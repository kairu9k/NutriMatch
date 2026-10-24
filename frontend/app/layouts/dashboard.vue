<template>
  <div class="dashboard-layout">
    <!-- MOBILE TOPBAR -->
    <div class="mobile-topbar">
      <button class="menu-btn" type="button" aria-label="Toggle menu" @click="isSidebarOpen = !isSidebarOpen">
        <Menu :size="22" />
      </button>
      <NuxtLink :to="dashboardPath" class="mobile-brand home-link" aria-label="NutriMatch — go to dashboard" @click="goHome">
        <img src="/resources/nutrimatchlogo.png" alt="" class="logo-mark" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </NuxtLink>
    </div>

    <!-- MOBILE OVERLAY -->
    <div v-if="isSidebarOpen" class="sidebar-overlay" @click="isSidebarOpen = false"></div>

    <!-- SIDEBAR — collapsed by default, expands on hover (desktop) or via
         the mobile menu button. Width transition + hidden overflow keeps
         labels from wrapping mid-animation. -->
    <aside
      class="sidebar"
      :class="{ collapsed: !expanded, 'sidebar-open': isSidebarOpen }"
      @mouseenter="isCollapsed = false"
      @mouseleave="collapseSidebar"
    >
      <div class="sidebar-top">
        <NuxtLink :to="dashboardPath" class="sidebar-brand home-link" aria-label="NutriMatch, go to dashboard" @click="goHome">
          <img src="/resources/nutrimatchlogo.png" alt="" class="logo-mark" />
          <span v-if="expanded" class="brand-words">
            <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
            <span class="brand-tagline">Clinical Nutrition System</span>
            <!-- which portal you're in -->
            <span v-if="portalLabel" class="portal-line">{{ portalLabel }}</span>
          </span>
        </NuxtLink>
      </div>

      <!-- NAV + ACCOUNT FOOTER — gated on auth.hydrated: auth.user only exists
           client-side (JWT lives in localStorage, unreadable during SSR), so
           rendering this before hydration completes sends the server a guess
           that's wrong for every RND/admin. Vue's hydration-mismatch repair
           then patches some nodes (labels) but not others (icons, hrefs),
           producing a genuinely broken mixed render rather than a clean one. -->
      <template v-if="auth.hydrated">
        <nav class="sidebar-nav">
          <div v-for="(group, gi) in navGroups" :key="gi" class="nav-group">
            <p v-if="group.label && expanded" class="nav-group-label">{{ group.label }}</p>
            <NuxtLink
              v-for="item in group.items"
              :key="item.label"
              :to="item.to"
              class="nav-item"
              :class="{ active: isActive(item) }"
              :aria-current="isActive(item) ? 'page' : null"
              :aria-label="!expanded ? item.label : null"
              :title="!expanded ? item.label : null"
              @click="isSidebarOpen = false"
            >
              <component :is="item.icon" class="nav-icon" :size="18" />
              <span v-if="expanded" class="nav-label">{{ item.label }}</span>
              <span v-if="item.badge && expanded" class="nav-badge">{{ item.badge }}</span>
              <span v-else-if="item.badge && !expanded" class="nav-badge-dot"></span>
            </NuxtLink>
          </div>
        </nav>

        <div class="sidebar-account">
          <button class="account-trigger" type="button" :aria-expanded="showAccountMenu" aria-label="Account menu" @click.stop="showAccountMenu = !showAccountMenu" :title="!expanded ? displayName : null">
            <img v-if="auth.user?.profile_photo" :src="auth.user.profile_photo" alt="" class="account-avatar account-avatar-img" />
            <div v-else class="account-avatar">{{ userInitials }}</div>
            <div v-if="expanded" class="account-info">
              <p class="account-name">{{ fullName }}</p>
              <p class="account-role">{{ isRnd ? (auth.rndProfile?.specialization || 'RND') : roleLabel }}</p>
            </div>
            <component v-if="expanded" :is="showAccountMenu ? ChevronUp : ChevronDown" class="account-chevron" :size="15" />
          </button>

          <div v-if="showAccountMenu" class="account-menu" :class="{ 'account-menu-collapsed': !expanded }">
            <NuxtLink v-if="auth.user?.role !== 'admin'" to="/profile-settings" class="account-menu-item" @click="showAccountMenu = false">
              <UserCog :size="15" /> <span v-if="expanded">Profile settings</span>
            </NuxtLink>
            <template v-else>
              <NuxtLink to="/admin-profile" class="account-menu-item" @click="showAccountMenu = false">
                <UserCog :size="15" /> <span v-if="expanded">My profile</span>
              </NuxtLink>
              <NuxtLink to="/system-settings" class="account-menu-item" @click="showAccountMenu = false">
                <Settings :size="15" /> <span v-if="expanded">System settings</span>
              </NuxtLink>
            </template>
            <button v-if="welcomeRole" class="account-menu-item" type="button" @click="openWelcome">
              <Sparkles :size="15" /> <span v-if="expanded">How NutriMatch works</span>
            </button>
            <button class="account-menu-item logout" type="button" @click="handleLogout">
              <LogOut :size="15" /> <span v-if="expanded">Sign out</span>
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

        <!-- Admins have no messages, and their to-dos live in the sidebar badges
             and the dashboard's Needs attention list (user's call, 2026-10-12). -->
        <div v-if="auth.user?.role !== 'admin'" class="topbar-actions">
          <button class="icon-btn" type="button" :aria-label="unreadMessages.total ? `Messages, ${unreadMessages.total} unread` : 'Messages'" @click="navigateTo('/messages')">
            <MessageSquare :size="20" />
            <!-- Same yellow dot as the bell (NotificationDropdown.vue). -->
            <span v-if="unreadMessages.total" class="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-gold border-2 border-cream animate-pop"></span>
          </button>
          <NotificationDropdown v-if="auth.hydrated" />
        </div>
      </header>

      <!-- SCROLLABLE CONTENT -->
      <main class="content">
        <slot />
      </main>
    </div>

    <SupportWidget v-if="auth.user && auth.user.role !== 'admin'" />
    <WelcomeModal :open="welcomeOpen" :role="welcomeRole || 'client'" :first-name="auth.user?.first_name || ''" @close="closeWelcome" />
  </div>
</template>

<script setup>
import {
  LayoutDashboard, Users, CalendarCheck, LineChart, Target,
  Search as SearchIcon, FileText, MessageSquare,
  UserCog, LogOut, ChevronDown, ChevronUp, Menu, Receipt, TrendingUp, Sparkles,
  ShieldCheck, Wallet, ScrollText, BarChart3, Settings, Headset, FlaskConical
} from 'lucide-vue-next'

const route = useRoute()
const auth = useAuthStore()
const { get } = useApi()
const isSidebarOpen = ref(false)
const isCollapsed = ref(true)
// Labels render only when expanded: on desktop that's while hovering; the
// mobile drawer (opened with the menu button) is always expanded — a phone
// has no hover, so it used to slide open as a wide icon-only rail.
const expanded = computed(() => isSidebarOpen.value || !isCollapsed.value)
// Leaving the desktop sidebar collapses it back to the icon rail — close the
// account menu too, or it's left squeezed into the rail as bare icons.
function collapseSidebar() {
  isCollapsed.value = true
  showAccountMenu.value = false
}
const showAccountMenu = ref(false)

const todayLabel = computed(() => new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }))

// Close the mobile sidebar automatically on route change (e.g. browser back/forward).
watch(() => route.path, () => { isSidebarOpen.value = false })
// The page behind the open phone menu doesn't scroll:
// plugins/modal-scroll-lock.client.ts (.sidebar-overlay).

// Page title comes from each page's definePageMeta({ title: '...' })
const pageTitle = computed(() => route.meta.title || 'Dashboard')

const isRnd = computed(() => auth.user?.role === 'rnd')

// The logo (sidebar + phone top bar) goes to the user's own dashboard — same
// rule as the sign-in redirect (middleware/auth.global.ts).
const dashboardPath = computed(() => ({ rnd: '/rnd-dashboard', admin: '/admin-dashboard' })[auth.user?.role] || '/client-dashboard')
function goHome() {
  isSidebarOpen.value = false
  if (route.path === dashboardPath.value) window.scrollTo({ top: 0, behavior: 'smooth' })
}
const roleLabel = computed(() => (auth.user?.role === 'client' ? 'Client' : 'Admin'))
const portalLabel = computed(() => ({ rnd: 'RND PORTAL', client: 'CLIENT PORTAL', admin: 'ADMIN PORTAL' })[auth.user?.role] || '')
const fullName = computed(() => (auth.user ? `${auth.user.first_name} ${auth.user.last_name}`.trim() : ''))
const isActive = item => route.path === item.to || (item.to !== '/' && route.path.startsWith(item.to + '/'))

const displayName = computed(() => {
  if (!auth.user) return ''
  const name = `${auth.user.first_name} ${auth.user.last_name}`.trim()
  return isRnd.value ? `RND ${name}` : name
})

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

// Real pending-confirmation appointment count, loaded once on mount. New
// clients book directly, so this also covers first-time bookings.
const pendingAppointments = ref(0)
// Client: lab tests their RND requested that are still waiting for an upload.
const openLabRequests = ref(0)

async function loadBadgeCounts() {
  if (auth.user?.role === 'client') {
    try {
      openLabRequests.value = (await get('/client/labs/')).requests.filter(r => r.status === 'open').length
    } catch {
      openLabRequests.value = 0
    }
    return
  }
  if (!isRnd.value) return
  try {
    const appointments = await get('/rnd/appointments/')
    pendingAppointments.value = appointments.filter(a => a.status === 'pending').length
  } catch {
    pendingAppointments.value = 0
  }
}


watch(() => auth.hydrated, (hydrated) => { if (hydrated) loadBadgeCounts() }, { immediate: true })

// Unread chat on the Messages icon (chat isn't in the bell): on load, on
// every page change, when the tab comes back, live when someone messages
// (ws/notifications/), and every 30 s only while the live connection is down.
const { unread: unreadMessages, refresh: refreshUnreadMessages } = useUnreadMessages()
const hasChat = () => auth.user && auth.user.role !== 'admin'
watch(() => [auth.hydrated, route.path], ([hydrated]) => { if (hydrated && hasChat()) refreshUnreadMessages() }, { immediate: true })

// Live updates for clients and RNDs (admins have no bell or Messages icon).
const live = useLiveUpdates()
watch(() => [auth.hydrated, auth.user?.id, auth.user?.role], ([hydrated]) => {
  if (hydrated && hasChat()) live.start()
  else live.stop()
}, { immediate: true })
live.onLive('message', () => { refreshUnreadMessages(); sound.play() })
// a short chime for new notifications and messages (off switch in Profile Settings → Notifications)
const sound = useNotificationSound()
live.onLive('notification', () => sound.play())
live.onLive('reconnect', () => { if (hasChat()) refreshUnreadMessages() })

let unreadTimer = null
function refreshWhenVisible() { if (hasChat() && document.visibilityState === 'visible') refreshUnreadMessages() }
onMounted(() => {
  unreadTimer = setInterval(() => { if (!live.connected.value) refreshWhenVisible() }, 30000)
  document.addEventListener('visibilitychange', refreshWhenVisible)
})
onUnmounted(() => {
  clearInterval(unreadTimer)
  document.removeEventListener('visibilitychange', refreshWhenVisible)
})
// Uploading clears a request, so refresh the client's badge when they move between pages.
watch(() => route.path, () => { if (auth.user?.role === 'client') loadBadgeCounts() })

// Main nav split into MAIN / CLINICAL / RESOURCES groups. Availability/
// Earnings/Reviews live as tabs inside Profile Settings rather than
// separate nav destinations — see RNDProfileSettings.vue's rndTabs.
// Notifications moved to the topbar bell (real unread badge, not a nav
// link) instead of a dedicated page.
const rndNavGroups = computed(() => [
  {
    label: null,
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', to: '/rnd-dashboard' },
      { icon: Users, label: 'My Patients', to: '/my-patients' },
      { icon: CalendarCheck, label: 'Appointments', to: '/appointments', badge: pendingAppointments.value || null },
    ],
  },
  {
    label: 'Clinical',
    items: [
      { icon: LineChart, label: 'NCP Records', to: '/ncp-records' },
      { icon: Target, label: 'Meal Plans', to: '/meal-planning' },
      { icon: SearchIcon, label: 'Food Exchange Search', to: '/food-exchange-search' },
    ],
  },
  {
    label: 'Business',
    items: [
      { icon: FileText, label: 'Resources', to: '/resource-upload' },
      { icon: Wallet, label: 'Earnings', to: '/earnings' },
    ],
  },
])

// Client-facing pages are still being built out (Phase 6) — only pages already
// verified to work for a client role are linked here, see vault/TODO.md.
// Grouping/order ported from feature/client's sidebar design.
const clientNavGroups = computed(() => [
  {
    label: null,
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', to: '/client-dashboard' },
    ],
  },
  {
    label: 'Health',
    items: [
      { icon: CalendarCheck, label: 'Appointments', to: '/appointments' },
      { icon: Target, label: 'My Meal Plan', to: '/meal-plan-view' },
      { icon: TrendingUp, label: 'Progress Tracker', to: '/progress-tracker' },
      { icon: FlaskConical, label: 'Lab Results', to: '/lab-results', badge: openLabRequests.value || null },
    ],
  },
  {
    label: 'Care team',
    items: [
      { icon: SearchIcon, label: 'Find an RND', to: '/find-rnd' },
    ],
  },
  {
    label: 'Library & billing',
    items: [
      { icon: FileText, label: 'Resources', to: '/resource-library' },
      { icon: Receipt, label: 'Billing & Invoice', to: '/invoices-billing' },
    ],
  },
])

// Admin menu — same layout and design as the client/RND portals.
const adminCounts = ref({ pending: 0, payouts: 0, refunds: 0, staleRequests: 0, support: 0 })
async function loadAdminCounts() {
  if (auth.user?.role !== 'admin') return
  try {
    const stats = await get('/admin/platform-stats/')
    adminCounts.value = {
      pending: stats.pending_verif || 0,
      payouts: stats.payouts_due_count || 0,
      refunds: stats.refunds_pending || 0,
      staleRequests: stats.appointments?.stale_requests || 0,
      support: stats.support_open || 0,
    }
  } catch {
    // badges are optional
  }
}
watch(() => [auth.hydrated, route.path], ([hydrated]) => { if (hydrated) loadAdminCounts() }, { immediate: true })
// The sidebar badges (RND booking requests, the client's lab requests, the
// admin's to-do counts) also keep up while you stay on one page.
useAutoRefresh(() => auth.hydrated && Promise.all([loadBadgeCounts(), loadAdminCounts()]))
const adminNavGroups = computed(() => [
  { label: null, items: [{ icon: LayoutDashboard, label: 'Dashboard', to: '/admin-dashboard' }] },
  {
    label: 'People',
    items: [
      { icon: ShieldCheck, label: 'RND Applications', to: '/rnd-verification', badge: adminCounts.value.pending || null },
      { icon: Users, label: 'Users', to: '/users' },
      { icon: CalendarCheck, label: 'Appointments', to: '/admin-appointments', badge: adminCounts.value.staleRequests || null },
      { icon: Headset, label: 'Support', to: '/admin-support', badge: adminCounts.value.support || null },
    ],
  },
  {
    label: 'Money',
    items: [
      { icon: Receipt, label: 'Billing & Commission', to: '/billing-commission', badge: adminCounts.value.refunds || null },
      { icon: Wallet, label: 'Payouts', to: '/payouts', badge: adminCounts.value.payouts || null },
    ],
  },
  {
    label: 'System',
    items: [
      { icon: ScrollText, label: 'Audit Logs', to: '/audit-logs' },
      { icon: BarChart3, label: 'Platform Reports', to: '/platform-reports' },
    ],
  },
])

const navGroups = computed(() => (auth.user?.role === 'admin' ? adminNavGroups.value : isRnd.value ? rndNavGroups.value : clientNavGroups.value))

/* ---------- One-time welcome (WelcomeModal.vue) ---------- */
// Shown once per account (User.welcome_seen_at), the first time a client or
// RND reaches the app; reopened from the account menu. A session saved
// before the field existed is refreshed once so it gets the welcome too.
const welcomeOpen = ref(false)
const welcomeRole = computed(() => (['client', 'rnd'].includes(auth.user?.role) ? auth.user.role : null))
const { post: postApi } = useApi()
function maybeShowWelcome() {
  const user = auth.user
  if (!welcomeRole.value || !user) return
  if (route.path === '/onboarding') return
  if (Object.prototype.hasOwnProperty.call(user, 'welcome_seen_at') && !user.welcome_seen_at) welcomeOpen.value = true
}
function openWelcome() {
  showAccountMenu.value = false
  isSidebarOpen.value = false
  welcomeOpen.value = true
}
async function closeWelcome() {
  welcomeOpen.value = false
  if (auth.user && !auth.user.welcome_seen_at) {
    try {
      auth.user = await postApi('/auth/me/welcome-seen/')
      auth.persist()
    } catch {
      // Not critical — it will just show again next time.
    }
  }
}
watch(() => auth.hydrated, async (hydrated) => {
  if (!hydrated || !auth.user) return
  if (!Object.prototype.hasOwnProperty.call(auth.user, 'welcome_seen_at')) {
    await auth.fetchMe().catch(() => null)
  }
  maybeShowWelcome()
}, { immediate: true })

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

/* One scrollbar: the page itself scrolls (like on phones); the sidebar and
   top bar are sticky. An inner scrolling <main> let absolutely positioned
   bits (e.g. charts' hidden tables) escape and stretch the page. */
.dashboard-layout {
  display: flex;
  min-height: 100vh;
  font-family: 'Inter', sans-serif;
  background: #f7f8f6;
}

/* SIDEBAR — collapsed to an icon rail by default, expands on hover.
   Flex column so the account footer stays pinned to the bottom of the
   viewport, independent of the nav's own scroll region. */
.sidebar {
  width: 76px; flex-shrink: 0; background: #004D3A; color: #fff;
  padding: 16px 14px 16px; height: 100vh; position: sticky; top: 0; z-index: 40;
  display: flex; flex-direction: column; overflow-y: auto; overflow-x: hidden;
  transition: width 0.2s ease, padding 0.2s ease;
  scrollbar-width: none; -ms-overflow-style: none;
}
.sidebar::-webkit-scrollbar { display: none; }
.sidebar:not(.collapsed) { width: 260px; padding: 16px 22px 16px; }

/* a hairline separates the logo from the pages (same line as above the account) */
.sidebar-top { margin-bottom: 22px; padding-bottom: 18px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); flex-shrink: 0; position: relative; }
.sidebar-brand { display: flex; align-items: center; gap: 12px; min-height: 40px; padding: 0 4px; }
.brand-words { display: flex; flex-direction: column; min-width: 0; line-height: 1.15; }
.brand-tagline { font-size: 0.74rem; font-weight: 500; color: #8fae9f; white-space: nowrap; margin-top: 2px; letter-spacing: 0.01em; }
.portal-line { margin-top: 5px; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.06em; color: #e2c25e; white-space: nowrap; }
.home-link { color: inherit; text-decoration: none; cursor: pointer; border-radius: 8px; }
.home-link:focus-visible { outline: 2px solid #D4A017; outline-offset: 3px; }
.sidebar.collapsed .sidebar-brand { justify-content: center; padding: 0; }
.logo-mark { width: 60px; height: 60px; flex-shrink: 0; object-fit: contain; }
.sidebar.collapsed .logo-mark { width: 42px; height: 42px; }
.logo-text { font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: 700; white-space: nowrap; letter-spacing: 0.005em; }
.logo-match { color: #D4A017; }

/* Nav sizes to its own content and scrolls only if it overflows. Groups are
   separated by space, with a quiet label when expanded. */
.sidebar-nav { flex: 1; overflow-y: auto; overflow-x: hidden; min-height: 0; scrollbar-width: none; -ms-overflow-style: none; }
.sidebar-nav::-webkit-scrollbar { display: none; }
/* The nav reaches the sidebar's edges (its own overflow would clip the
   active bar otherwise), with the padding given back inside. */
.sidebar-nav { margin: 0 -22px; padding: 0 22px; }
.sidebar.collapsed .sidebar-nav { margin: 0 -14px; padding: 0 14px; }
.nav-group { display: flex; flex-direction: column; gap: 6px; }
.nav-group + .nav-group { margin-top: 32px; }
.sidebar.collapsed .nav-group + .nav-group { margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); }
.nav-group-label { font-size: 0.72rem; font-weight: 500; color: #7f9f8f; margin: 0 0 4px; padding: 0 12px; white-space: nowrap; }

.nav-item {
  display: flex; align-items: center; gap: 12px; height: 42px; padding: 0 12px; border-radius: 8px;
  color: #b3c7bb; font-size: 0.9rem; font-weight: 500; cursor: pointer;
  position: relative; text-decoration: none; white-space: nowrap;
  transition: background-color 0.12s, color 0.12s;
}
.sidebar.collapsed .nav-item { justify-content: center; padding: 0; gap: 0; }
.nav-item:hover { background: rgba(255,255,255,0.06); color: #fff; }
.nav-item:focus-visible { outline: 2px solid #D4A017; outline-offset: -2px; }
.nav-item.active { background: rgba(255,255,255,0.1); color: #fff; font-weight: 600; }
/* The one accent: a gold bar on the sidebar's own edge, same place collapsed or open. */
.nav-item.active::before {
  content: ''; position: absolute; top: 10px; bottom: 10px; width: 3px; border-radius: 0 3px 3px 0;
  background: #D4A017; left: -22px;
}
.sidebar.collapsed .nav-item.active::before { left: -14px; }
.nav-icon { flex-shrink: 0; color: #8fae9f; transition: color 0.12s; }
.nav-item:hover .nav-icon { color: #dbe8df; }
.nav-item.active .nav-icon { color: #D4A017; }
.nav-label { flex: 1; overflow: hidden; text-overflow: ellipsis; }
.nav-badge {
  min-width: 20px; height: 20px; padding: 0 6px; border-radius: 10px; flex-shrink: 0;
  display: inline-flex; align-items: center; justify-content: center;
  background: #D4A017; color: #1a3a1a; font-size: 0.7rem; font-weight: 700; font-variant-numeric: tabular-nums;
}
.nav-badge-dot { position: absolute; top: 8px; right: 14px; width: 7px; height: 7px; border-radius: 50%; background: #D4A017; box-shadow: 0 0 0 2px #004D3A; }

/* ACCOUNT SECTION */
.sidebar-account { flex-shrink: 0; position: relative; margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); }
.account-trigger {
  display: flex; align-items: center; gap: 10px; width: 100%;
  background: none; border: none; cursor: pointer; padding: 8px 6px; border-radius: 8px; font-family: inherit;
}
.sidebar.collapsed .account-trigger { justify-content: center; padding: 8px 0; }
.account-trigger:hover { background: rgba(255,255,255,0.06); }
.account-trigger:focus-visible { outline: 2px solid #D4A017; outline-offset: -2px; }
.account-avatar {
  width: 34px; height: 34px; border-radius: 50%; background: #D4A017; color: #1a3a1a;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.8rem; flex-shrink: 0;
}
.account-avatar-img { object-fit: cover; background: #00382a; }
.account-info { flex: 1; min-width: 0; text-align: left; white-space: nowrap; }
.account-name { font-size: 0.86rem; font-weight: 600; color: #fff; margin: 0; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
.account-role { font-size: 0.74rem; color: #8fae9f; margin: 0; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
.account-chevron { color: #8fae9f; flex-shrink: 0; }

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
.main-column { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.topbar {
  position: sticky; top: 0; z-index: 10; background: #fff; border-bottom: 1px solid #a8d5b5;
  padding: 10px 32px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
}
.topbar h1 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a3a1a; margin: 0; }
.topbar-date { font-size: 0.8rem; color: #8a9a8a; }
.topbar-actions { display: flex; align-items: center; gap: 12px; }
.icon-btn {
  width: 40px; height: 40px; border-radius: 8px; border: 1px solid rgba(0,77,58,0.15);
  background: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #004D3A;
  position: relative; transition: background-color 0.12s;
}
.icon-btn:hover { background: rgba(0,77,58,0.05); }
.icon-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.content { flex: 1; padding: 24px 40px 96px; } /* bottom room so the help button never covers a page's last button */

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
    width: 260px !important; padding: 16px 22px 16px !important;
    /* dvh = the visible screen (100vh also counts the area behind a phone's
       address bar, which hid the account section at the bottom). */
    height: 100vh; height: 100dvh;
    z-index: 40;
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
  }
  .sidebar.sidebar-open { transform: translateX(0); box-shadow: 4px 0 24px rgba(0,0,0,0.2); }
  /* One scroll area on phones: the whole menu scrolls, not a list inside it. */
  .sidebar-nav { flex: none; overflow: visible; }
  /* Account stays at the bottom of the drawer, like on desktop (it still
     scrolls with the menu when the screen is too short). */
  .sidebar-account { margin-top: auto; }

  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.4);
    z-index: 35;
  }

  .main-column { height: auto; overflow: visible; }
  .content { padding: 20px 16px 88px; }
}
</style>
