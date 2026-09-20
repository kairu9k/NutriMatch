<template>
  <div class="dashboard-layout">
    <!-- MOBILE TOPBAR -->
    <div class="mobile-topbar">
      <button class="menu-btn" type="button" aria-label="Toggle menu" @click="isSidebarOpen = !isSidebarOpen">
        <Menu :size="22" />
      </button>
      <div class="mobile-brand">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch" class="logo-mark" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </div>
    </div>

    <!-- MOBILE OVERLAY -->
    <div v-if="isSidebarOpen" class="sidebar-overlay" @click="isSidebarOpen = false"></div>

    <!-- SIDEBAR — collapsed by default, expands on hover (desktop) or via
         the mobile menu button. Width transition + hidden overflow keeps
         labels from wrapping mid-animation. -->
    <aside
      class="sidebar"
      :class="{ collapsed: isCollapsed, 'sidebar-open': isSidebarOpen }"
      @mouseenter="isCollapsed = false"
      @mouseleave="isCollapsed = true"
    >
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <img src="/resources/nutrimatchlogo.png" alt="NutriMatch" class="logo-mark" />
          <span v-if="!isCollapsed" class="logo-text">Nutri<span class="logo-match">Match</span></span>
        </div>
        <span v-if="!isCollapsed" class="brand-tagline">Clinical Nutrition System</span>
        <div v-if="!isCollapsed" class="portal-badge"><span class="portal-dot"></span>{{ portalLabel }}</div>
        <div v-if="!isCollapsed" class="sidebar-divider"></div>
      </div>

      <!-- NAV + ACCOUNT FOOTER — gated on auth.hydrated: auth.user only exists
           client-side (JWT lives in localStorage, unreadable during SSR), so
           rendering this before hydration completes sends the server a guess
           that's wrong for every RND/admin. Vue's hydration-mismatch repair
           then patches some nodes (labels) but not others (icons, hrefs),
           producing a genuinely broken mixed render rather than a clean one. -->
      <template v-if="auth.hydrated">
        <nav class="sidebar-nav">
          <template v-for="group in navGroups" :key="group.label">
            <p v-if="!isCollapsed" class="nav-group-label">{{ group.label }}</p>
            <NuxtLink
              v-for="item in group.items"
              :key="item.label"
              :to="item.to"
              class="nav-item"
              :class="{ active: route.path === item.to }"
              :title="isCollapsed ? item.label : null"
              @click="isSidebarOpen = false"
            >
              <component :is="item.icon" class="nav-icon" :size="17" />
              <span v-if="!isCollapsed" class="nav-label">{{ item.label }}</span>
              <span v-if="item.badge && !isCollapsed" class="nav-badge">{{ item.badge }}</span>
              <span v-else-if="item.badge && isCollapsed" class="nav-badge-dot"></span>
            </NuxtLink>
          </template>
        </nav>

        <div class="sidebar-account">
          <button class="account-trigger" type="button" @click.stop="showAccountMenu = !showAccountMenu" :title="isCollapsed ? displayName : null">
            <div class="account-avatar">{{ userInitials }}</div>
            <div v-if="!isCollapsed" class="account-info">
              <p class="account-name">{{ displayName }}</p>
              <p class="account-role">{{ isRnd ? 'RND' : roleLabel }}</p>
            </div>
            <component v-if="!isCollapsed" :is="showAccountMenu ? ChevronUp : ChevronDown" class="account-chevron" :size="15" />
          </button>

          <div v-if="showAccountMenu" class="account-menu" :class="{ 'account-menu-collapsed': isCollapsed }">
            <NuxtLink to="/profile-settings" class="account-menu-item" @click="showAccountMenu = false">
              <UserCog :size="15" /> <span v-if="!isCollapsed">Profile Settings</span>
            </NuxtLink>
            <button class="account-menu-item logout" type="button" @click="handleLogout">
              <LogOut :size="15" /> <span v-if="!isCollapsed">Sign Out</span>
            </button>
          </div>
        </div>
      </template>
    </aside>

    <!-- MAIN COLUMN -->
    <div class="main-column">
      <!-- STICKY TOP HEADER -->
      <header class="topbar">
        <div>
          <h1>{{ pageTitle }}</h1>
          <span class="topbar-date">{{ todayLabel }}</span>
        </div>

        <div class="topbar-actions">
          <button class="icon-btn" type="button" aria-label="Messages" @click="navigateTo('/messages')"><MessageSquare :size="17" /></button>
          <NotificationDropdown v-if="auth.hydrated" />
        </div>
      </header>

      <!-- SCROLLABLE CONTENT -->
      <main class="content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import {
  LayoutDashboard, Users, CalendarCheck, LineChart, Target,
  Search as SearchIcon, FileText, MessageCircle, MessageSquare,
  Star, UserCog, LogOut, ChevronDown, ChevronUp, Menu, Receipt, TrendingUp
} from 'lucide-vue-next'

const route = useRoute()
const auth = useAuthStore()
const { get } = useApi()
const isSidebarOpen = ref(false)
const isCollapsed = ref(true)
const showAccountMenu = ref(false)

const todayLabel = computed(() => new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }))

// Close the mobile sidebar automatically on route change (e.g. browser back/forward).
watch(() => route.path, () => { isSidebarOpen.value = false })

// Page title comes from each page's definePageMeta({ title: '...' })
const pageTitle = computed(() => route.meta.title || 'Dashboard')

const isRnd = computed(() => auth.user?.role === 'rnd')
const roleLabel = computed(() => (auth.user?.role === 'client' ? 'Client' : 'Admin'))
const portalLabel = computed(() => (isRnd.value ? 'RND Portal' : roleLabel.value + ' Portal'))

const displayName = computed(() => {
  if (!auth.user) return ''
  const name = `${auth.user.first_name} ${auth.user.last_name}`.trim()
  return isRnd.value ? `RND ${name}` : name
})

const rndProfile = computed(() => ({
  specialty: auth.rndProfile?.specialization || 'Specialist',
  prc: auth.rndProfile?.prc_license_number || '—'
}))

const userInitials = computed(() =>
  displayName.value
    .replace(/^RND\s*/i, '')
    .split(' ')
    .filter(Boolean)
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
)

// Real pending-count badges — pending relationship requests and
// pending-confirmation appointments — loaded once on mount.
const pendingPatientRequests = ref(0)
const pendingAppointments = ref(0)

async function loadBadgeCounts() {
  if (!isRnd.value) return
  try {
    const [requests, appointments] = await Promise.all([
      get('/rnd/relationship-requests/').catch(() => []),
      get('/rnd/appointments/').catch(() => []),
    ])
    pendingPatientRequests.value = requests.length
    pendingAppointments.value = appointments.filter(a => a.status === 'pending').length
  } catch {
    pendingPatientRequests.value = 0
    pendingAppointments.value = 0
  }
}

watch(() => auth.hydrated, (hydrated) => { if (hydrated) loadBadgeCounts() }, { immediate: true })

// Main nav split into MAIN / CLINICAL / RESOURCES groups. Availability/
// Earnings/Reviews live as tabs inside Profile Settings rather than
// separate nav destinations — see ProfileSettings.vue's rndTabs.
// Notifications moved to the topbar bell (real unread badge, not a nav
// link) instead of a dedicated page.
const rndNavGroups = computed(() => [
  {
    label: 'MAIN',
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', to: '/rnd-dashboard' },
      { icon: Users, label: 'My Patients', to: '/my-patients', badge: pendingPatientRequests.value || null },
      { icon: CalendarCheck, label: 'Appointments', to: '/appointments', badge: pendingAppointments.value || null },
    ],
  },
  {
    label: 'CLINICAL',
    items: [
      { icon: LineChart, label: 'NCP Records', to: '/ncp-records' },
      { icon: Target, label: 'Meal Plans', to: '/meal-planning' },
      { icon: SearchIcon, label: 'Food Exchange Search', to: '/food-exchange-search' },
    ],
  },
  {
    label: 'RESOURCES',
    items: [
      { icon: FileText, label: 'Resources', to: '/resource-upload' },
    ],
  },
])

// Client-facing pages are still being built out (Phase 6) — only pages already
// verified to work for a client role are linked here, see vault/TODO.md.
const clientNavGroups = computed(() => [
  {
    label: 'MAIN',
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', to: '/client-dashboard' },
      { icon: SearchIcon, label: 'Find an RND', to: '/find-rnd' },
      { icon: CalendarCheck, label: 'Appointments', to: '/appointments' },
    ],
  },
  {
    label: 'CLINICAL',
    items: [
      { icon: Target, label: 'My Meal Plan', to: '/meal-plan-view' },
      { icon: TrendingUp, label: 'Progress Tracker', to: '/progress-tracker' },
    ],
  },
  {
    label: 'RESOURCES',
    items: [
      { icon: FileText, label: 'Resources', to: '/resource-library' },
      { icon: MessageCircle, label: 'Messages', to: '/messages' },
      { icon: Receipt, label: 'Billing', to: '/invoices-billing' },
      { icon: Star, label: 'Reviews', to: '/reviews' },
    ],
  },
])

const navGroups = computed(() => (isRnd.value ? rndNavGroups.value : clientNavGroups.value))

function handleLogout() {
  auth.logout()
  navigateTo('/login')
}

function handleClickOutside() {
  showAccountMenu.value = false
}
onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600;700&display=swap');

* { box-sizing: border-box; }

.dashboard-layout {
  display: flex;
  height: 100vh;
  font-family: 'Inter', sans-serif;
  background: #f7f8f6;
}

/* SIDEBAR — collapsed to an icon rail by default, expands on hover.
   Flex column so the account footer stays pinned to the bottom of the
   viewport, independent of the nav's own scroll region. */
.sidebar {
  width: 76px; flex-shrink: 0; background: #004D3A; color: #fff;
  padding: 14px 14px 28px; height: 100vh; position: sticky; top: 0; z-index: 40;
  display: flex; flex-direction: column; overflow-y: auto; overflow-x: hidden;
  transition: width 0.2s ease, padding 0.2s ease;
  scrollbar-width: none; -ms-overflow-style: none;
}
.sidebar::-webkit-scrollbar { display: none; }
.sidebar:not(.collapsed) { width: 260px; padding: 14px 22px 28px; }

.sidebar-top { margin-bottom: 18px; flex-shrink: 0; position: relative; }
.sidebar-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.sidebar.collapsed .sidebar-brand { justify-content: center; margin-bottom: 16px; }
.logo-mark { width: 40px; height: 40px; flex-shrink: 0; object-fit: contain; }
.sidebar.collapsed .logo-mark { width: 32px; height: 32px; }
.logo-text { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; white-space: nowrap; }
.logo-match { color: #D4A017; }
.brand-tagline { display: block; font-size: 0.55rem; letter-spacing: 0.16em; color: #8fae9f; text-transform: uppercase; margin: 0 0 16px; font-weight: 600; white-space: nowrap; }
.portal-badge {
  display: inline-flex; align-items: center; gap: 5px;
  background: rgba(0,0,0,0.18); color: #D4A017;
  border: 1px solid #D4A017;
  font-size: 0.6rem; font-weight: 700; letter-spacing: 0.05em;
  padding: 5px 15px; border-radius: 20px; text-transform: uppercase;
  white-space: nowrap;
}
.portal-dot { width: 5px; height: 5px; border-radius: 50%; background: #D4A017; flex-shrink: 0; }
.sidebar-divider { border-bottom: 1px solid rgba(255,255,255,0.15); margin-top: 22px; }

/* Nav sizes to its own content and scrolls only if it overflows. */
.sidebar-nav { flex: 1; overflow-y: auto; overflow-x: hidden; min-height: 0; scrollbar-width: none; -ms-overflow-style: none; }
.sidebar-nav::-webkit-scrollbar { display: none; }
.nav-group-label { font-size: 0.65rem; letter-spacing: 0.12em; color: #5a7a5a; margin: 24px 0 10px; padding-left: 12px; white-space: nowrap; }
.nav-group-label:first-child { margin-top: 6px; }
.nav-item {
  display: flex; align-items: center; gap: 11px; padding: 10px; border-radius: 8px;
  color: #9fb5a3; font-size: 0.85rem; font-weight: 500; cursor: pointer; transition: background 0.15s;
  position: relative; text-decoration: none;
  width: 100%; background: none; border: none; text-align: left; font-family: inherit;
  white-space: nowrap; overflow: hidden; margin-bottom: 8px;
}
.sidebar.collapsed .nav-item { justify-content: center; padding: 8px 0; gap: 0; }
.nav-item:hover { background: rgba(255,255,255,0.05); }
.nav-item.active {
  background: #3a5a3a; color: #fff; font-weight: 700;
  border-left: 3px solid #D4A017; padding-left: 7px;
}
.sidebar.collapsed .nav-item.active { padding-left: 0; border-left: none; border-radius: 8px; }
.nav-item.active .nav-icon { color: #D4A017; }
.nav-icon { flex-shrink: 0; }
.nav-label { flex: 1; }
.nav-badge { background: #D4A017; color: #1a3a1a; font-size: 0.68rem; font-weight: 700; padding: 1px 7px; border-radius: 10px; flex-shrink: 0; }
.nav-badge-dot { position: absolute; top: 8px; right: 14px; width: 7px; height: 7px; border-radius: 50%; background: #D4A017; }

/* ACCOUNT SECTION */
.sidebar-account { flex-shrink: 0; position: relative; margin-top: 12px; padding-top: 14px; border-top: 1px solid rgba(255,255,255,0.08); }
.account-trigger {
  display: flex; align-items: center; gap: 10px; width: 100%;
  background: none; border: none; cursor: pointer; padding: 6px 4px; border-radius: 8px;
}
.sidebar.collapsed .account-trigger { justify-content: center; padding: 6px 0; }
.account-trigger:hover { background: rgba(255,255,255,0.05); }
.account-avatar {
  width: 36px; height: 36px; border-radius: 50%; background: #D4A017; color: #1a3a1a;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; flex-shrink: 0;
}
.account-info { flex: 1; text-align: left; white-space: nowrap; overflow: hidden; }
.account-name { font-size: 0.86rem; font-weight: 700; color: #fff; margin: 0; overflow: hidden; text-overflow: ellipsis; }
.account-role { font-size: 0.72rem; color: #9ab89a; margin: 0; }
.account-chevron { color: #9ab89a; flex-shrink: 0; }

.account-menu {
  position: absolute; bottom: calc(100% + 6px); left: 0; right: 0;
  background: #00382a; border: 1px solid rgba(255,255,255,0.1); border-radius: 10px;
  padding: 6px; box-shadow: 0 8px 24px rgba(0,0,0,0.3); z-index: 20;
}
.account-menu-collapsed { left: 0; right: auto; width: 180px; }
.account-menu-item {
  display: flex; align-items: center; gap: 8px; padding: 9px 10px; border-radius: 6px;
  color: #dbe8db; font-size: 0.83rem; text-decoration: none; cursor: pointer;
  width: 100%; background: none; border: none; text-align: left; font-family: inherit;
}
.account-menu-item:hover { background: rgba(255,255,255,0.06); }
.account-menu-item.logout { color: #e08a8a; }

/* MAIN COLUMN */
.main-column { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

.topbar {
  position: sticky; top: 0; z-index: 10; background: #fff; border-bottom: 1px solid #a8d5b5;
  padding: 10px 32px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
}
.topbar h1 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a3a1a; margin: 0; }
.topbar-date { font-size: 0.8rem; color: #8a9a8a; }
.topbar-actions { display: flex; align-items: center; gap: 12px; }
.icon-btn {
  width: 36px; height: 36px; border-radius: 8px; border: 1px solid #e5e8e5;
  background: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #4a5a4a;
  position: relative;
}

.content { flex: 1; overflow-y: auto; padding: 24px 100px 100px; }

/* MOBILE TOPBAR — hidden on desktop, shown only under the breakpoint below */
.mobile-topbar { display: none; }

.sidebar-overlay {
  display: none;
}

@media (max-width: 900px) {
  .mobile-topbar {
    display: flex;
    align-items: center;
    gap: 12px;
    background: #004D3A;
    color: #fff;
    padding: 14px 20px;
    position: sticky;
    top: 0;
    z-index: 30;
  }
  .menu-btn {
    background: none; border: none; color: #fff; cursor: pointer;
    display: flex; align-items: center; justify-content: center; padding: 4px;
  }
  .mobile-brand { display: flex; align-items: center; gap: 8px; font-size: 1rem; font-weight: 700; }
  .mobile-brand .logo-mark { width: 22px; height: 22px; }

  .dashboard-layout { flex-direction: column; height: auto; min-height: 100vh; }

  /* Mobile sidebar drops the hover-collapse behavior entirely — it's
     either fully open (slid in) or fully hidden, always at full width. */
  .sidebar {
    position: fixed;
    top: 0; left: 0;
    width: 260px !important; padding: 14px 22px 28px !important;
    height: 100vh;
    z-index: 40;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    box-shadow: 4px 0 24px rgba(0,0,0,0.2);
  }
  .sidebar.sidebar-open { transform: translateX(0); }
  .sidebar.collapsed .sidebar-brand,
  .sidebar.collapsed .nav-item,
  .sidebar.collapsed .account-trigger { justify-content: flex-start; }
  .sidebar.collapsed .logo-text,
  .sidebar.collapsed .brand-tagline,
  .sidebar.collapsed .portal-badge,
  .sidebar.collapsed .sidebar-divider,
  .sidebar.collapsed .nav-label,
  .sidebar.collapsed .nav-group-label,
  .sidebar.collapsed .account-info { display: block; }
  .sidebar.collapsed .nav-item.active { padding-left: 7px; border-left: 3px solid #D4A017; }

  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.4);
    z-index: 35;
  }

  .main-column { height: auto; overflow: visible; }
  .content { padding: 20px 16px 60px; }
}
</style>
