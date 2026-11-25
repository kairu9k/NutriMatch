<template>
  <div class="dashboard-layout" :class="{ 'is-client': ['client', 'admin', 'rnd'].includes(auth.user?.role), 'is-admin': auth.user?.role === 'admin' }">
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
      @mouseleave="pinned || collapseSidebar()"
    >
      <div class="sidebar-top">
        <NuxtLink :to="dashboardPath" class="sidebar-brand home-link" aria-label="NutriMatch, go to dashboard" @click="goHome">
          <img src="/resources/nutrimatchlogo.png" alt="" class="logo-mark" />
          <span v-if="expanded" class="brand-words">
            <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
            <span class="brand-tagline">Clinical Nutrition System</span>
          </span>
        </NuxtLink>
        <!-- keep the menu open (UI only: it otherwise opens on hover) -->
        <button v-if="expanded && !isSidebarOpen" type="button" class="pin-btn" :aria-label="pinned ? 'Collapse the menu' : 'Keep the menu open'" :title="pinned ? 'Collapse' : 'Keep open'" @click.stop="pinned = !pinned; !pinned && collapseSidebar()">
          <component :is="pinned ? ChevronsLeft : ChevronsRight" :size="16" />
        </button>
        <!-- which portal you're in -->
        <span v-if="portalLabel && expanded" class="portal-line"><span class="portal-dot" aria-hidden="true"></span>{{ portalLabel }}</span>
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
              <component :is="item.icon" class="nav-icon" :size="19" />
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
              <UserCog :size="15" /> <span>Profile settings</span>
            </NuxtLink>
            <template v-else>
              <NuxtLink to="/admin-profile" class="account-menu-item" @click="showAccountMenu = false">
                <UserCog :size="15" /> <span>My profile</span>
              </NuxtLink>
              <NuxtLink to="/system-settings" class="account-menu-item" @click="showAccountMenu = false">
                <Settings :size="15" /> <span>System settings</span>
              </NuxtLink>
            </template>
            <button v-if="welcomeRole" class="account-menu-item" type="button" @click="openWelcome">
              <Sparkles :size="15" /> <span>How NutriMatch works</span>
            </button>
            <span class="account-menu-sep" aria-hidden="true"></span>
            <button class="account-menu-item logout" type="button" @click="handleLogout">
              <LogOut :size="15" /> <span>Sign out</span>
            </button>
          </div>
        </div>
      </template>
    </aside>

    <!-- MAIN COLUMN -->
    <div class="main-column">
      <!-- STICKY TOP HEADER -->
      <header class="topbar">
        <div class="topbar-left">
          <!-- the rail only shows the logo, so the name sits here while it's collapsed -->
          <template v-if="!expanded">
            <span class="topbar-brand">
              <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
              <span class="topbar-tagline">Clinical Nutrition System</span>
            </span>
            <span class="topbar-sep" aria-hidden="true"></span>
          </template>
          <!-- phone: your photo opens your profile (the menu is in the bottom tabs) -->
          <NuxtLink v-if="auth.hydrated && ['client', 'admin', 'rnd'].includes(auth.user?.role)" :to="auth.user?.role === 'admin' ? '/admin-profile' : '/profile-settings'" class="topbar-me" aria-label="My profile">
            <img v-if="auth.user?.profile_photo" :src="auth.user.profile_photo" alt="" />
            <span v-else>{{ userInitials }}</span>
          </NuxtLink>
          <div class="topbar-title" :class="{ 'is-hidden': expanded && !isSidebarOpen }">
            <h1>
              <template v-if="['client', 'admin', 'rnd'].includes(auth.user?.role) && route.path === dashboardPath"><span class="title-desk">{{ pageTitle }}</span><span class="title-phone">Hi {{ auth.user?.first_name }} <span aria-hidden="true">👋</span></span></template>
              <template v-else>{{ pageTitle }}</template>
            </h1>
            <span class="topbar-date">{{ todayLabel }}</span>
          </div>
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
      <main class="content" :class="{ 'has-tabs': ['client', 'admin', 'rnd'].includes(auth.user?.role) }">
        <slot />
      </main>
    </div>

    <!-- PHONE: client bottom tabs (the same pages as the sidebar; Account opens the menu) -->
    <nav v-if="auth.hydrated && auth.user?.role === 'client'" class="mobile-tabs" aria-label="Main">
      <NuxtLink v-for="t in [
        { label: 'Home', to: '/client-dashboard', icon: LayoutDashboard },
        { label: 'Bookings', to: '/appointments', icon: CalendarCheck },
        { label: 'Meal plan', to: '/meal-plan-view', icon: Target },
        { label: 'Progress', to: '/progress-tracker', icon: TrendingUp },
      ]" :key="t.to" :to="t.to" class="mobile-tab" :class="{ active: isActive(t) }" :aria-current="isActive(t) ? 'page' : null">
        <span class="mobile-tab-icon"><component :is="t.icon" :size="20" /></span>
        <span>{{ t.label }}</span>
      </NuxtLink>
      <button type="button" class="mobile-tab" :class="{ active: isSidebarOpen }" @click="isSidebarOpen = !isSidebarOpen">
        <span class="mobile-tab-icon"><UserCog :size="20" /></span>
        <span>Account</span>
      </button>
    </nav>

    <!-- PHONE: RND bottom tabs (the everyday RND pages; Menu opens the sidebar for the rest) -->
    <nav v-if="auth.hydrated && auth.user?.role === 'rnd'" class="mobile-tabs" aria-label="Main">
      <NuxtLink v-for="t in [
        { label: 'Home', to: '/rnd-dashboard', icon: LayoutDashboard },
        { label: 'Patients', to: '/my-patients', icon: Users },
        { label: 'Bookings', to: '/appointments', icon: CalendarCheck, badge: pendingAppointments },
        { label: 'Meal plans', to: '/meal-planning', icon: Target },
      ]" :key="t.to" :to="t.to" class="mobile-tab" :class="{ active: isActive(t) }" :aria-current="isActive(t) ? 'page' : null">
        <span class="mobile-tab-icon"><component :is="t.icon" :size="20" /><i v-if="t.badge" class="mobile-tab-dot" aria-hidden="true"></i></span>
        <span>{{ t.label }}</span>
      </NuxtLink>
      <button type="button" class="mobile-tab" :class="{ active: isSidebarOpen }" @click="isSidebarOpen = !isSidebarOpen">
        <span class="mobile-tab-icon"><Menu :size="20" /></span>
        <span>Menu</span>
      </button>
    </nav>

    <!-- PHONE: admin bottom tabs (the busiest admin pages; Menu opens the sidebar for the rest) -->
    <nav v-if="auth.hydrated && auth.user?.role === 'admin'" class="mobile-tabs" aria-label="Main">
      <NuxtLink v-for="t in [
        { label: 'Home', to: '/admin-dashboard', icon: LayoutDashboard },
        { label: 'Users', to: '/users', icon: Users },
        { label: 'Bookings', to: '/admin-appointments', icon: CalendarCheck, badge: adminCounts.staleRequests },
        { label: 'Support', to: '/admin-support', icon: Headset, badge: adminCounts.support },
      ]" :key="t.to" :to="t.to" class="mobile-tab" :class="{ active: isActive(t) }" :aria-current="isActive(t) ? 'page' : null">
        <span class="mobile-tab-icon"><component :is="t.icon" :size="20" /><i v-if="t.badge" class="mobile-tab-dot" aria-hidden="true"></i></span>
        <span>{{ t.label }}</span>
      </NuxtLink>
      <button type="button" class="mobile-tab" :class="{ active: isSidebarOpen }" @click="isSidebarOpen = !isSidebarOpen">
        <span class="mobile-tab-icon"><Menu :size="20" /></span>
        <span>Menu</span>
      </button>
    </nav>

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

/* ---------- UI only ---------- */
import { ChevronsLeft, ChevronsRight } from 'lucide-vue-next'
// the collapse button: pinned keeps the menu open after the mouse leaves
const pinned = ref(false)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800&display=swap');

* { box-sizing: border-box; }

/* One scrollbar: the page itself scrolls (like on phones); the sidebar and
   top bar are sticky. An inner scrolling <main> let absolutely positioned
   bits (e.g. charts' hidden tables) escape and stretch the page.
   The page colour is also the colour of the active sidebar tab, so the tab
   looks like it opens into the page. */
.dashboard-layout {
  --nm-green: #004D3A;
  --nm-page: #F5F7F5;
  --nm-gold: #EFBF04;
  display: flex;
  min-height: 100vh;
  font-family: 'DM Sans', 'Inter', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  background: var(--nm-page);
}

/* ---------- SIDEBAR: icon rail by default, opens on hover ---------- */
.sidebar {
  width: 84px; flex-shrink: 0; background: var(--nm-green); color: #fff;
  padding: 18px 16px 16px; height: 100vh; position: sticky; top: 0; z-index: 40;
  display: flex; flex-direction: column; overflow-y: auto; overflow-x: hidden;
  transition: width 0.2s ease, padding 0.2s ease;
  scrollbar-width: none; -ms-overflow-style: none;
}
.sidebar::-webkit-scrollbar { display: none; }
.sidebar:not(.collapsed) { width: 272px; padding: 18px 16px 16px 20px; }

/* brand */
.sidebar-top { position: relative; flex-shrink: 0; display: flex; flex-direction: column; gap: 14px; padding-bottom: 18px; border-bottom: 1px solid rgba(255, 255, 255, 0.12); }
.sidebar-brand { display: flex; align-items: center; gap: 10px; min-height: 52px; }
.brand-words { display: flex; flex-direction: column; min-width: 0; line-height: 1.15; }
.brand-tagline { margin-top: 3px; font-size: 12px; font-weight: 600; color: rgba(255, 255, 255, 0.62); white-space: nowrap; }
.home-link { color: inherit; text-decoration: none; cursor: pointer; border-radius: 10px; }
.home-link:focus-visible { outline: 2px solid var(--nm-gold); outline-offset: 3px; }
.sidebar.collapsed .sidebar-brand { justify-content: center; }
.logo-mark { width: 50px; height: 60px; flex-shrink: 0; object-fit: contain; filter: brightness(1.35) saturate(1.2); }
.sidebar.collapsed .logo-mark { width: 40px; height: 48px; }
.logo-text { font-family: 'Playfair Display', Georgia, serif; font-size: 23px; font-weight: 700; white-space: nowrap; color: #fff; }
.logo-match { color: var(--nm-gold); }
.pin-btn {
  position: absolute; top: 12px; right: -2px;
  width: 30px; height: 30px; border-radius: 10px; border: none; cursor: pointer;
  background: rgba(255, 255, 255, 0.1); color: #fff;
  display: inline-flex; align-items: center; justify-content: center;
  transition: background-color 0.15s;
}
.pin-btn:hover { background: rgba(255, 255, 255, 0.2); }
.pin-btn:focus-visible { outline: 2px solid var(--nm-gold); outline-offset: 2px; }
.portal-line {
  align-self: flex-start; display: inline-flex; align-items: center; gap: 8px;
  height: 26px; padding: 0 12px; border-radius: 999px;
  background: rgba(239, 191, 4, 0.14); border: 1px solid rgba(239, 191, 4, 0.35);
  font-size: 11px; font-weight: 800; letter-spacing: 1.4px; color: var(--nm-gold); white-space: nowrap;
}
.portal-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--nm-gold); }

/* nav: runs to the sidebar's right edge so the active tab can join the page */
.sidebar-nav {
  flex: 1; min-height: 0; overflow-y: auto; overflow-x: hidden;
  margin: 0 -16px 0 0; padding: 40px 0 26px 0;
  scrollbar-width: none; -ms-overflow-style: none;
}
.sidebar-nav::-webkit-scrollbar { display: none; }
.nav-group { display: flex; flex-direction: column; gap: 12px; }
.nav-group + .nav-group { margin-top: 26px; }
.sidebar.collapsed .nav-group + .nav-group { margin-top: 10px; padding-top: 10px; }
.sidebar.collapsed .nav-group + .nav-group::before {
  content: ''; display: block; height: 1px; margin: -10px 16px 10px 0; background: rgba(255, 255, 255, 0.1);
}
.nav-group-label { margin: 0 0 2px; padding: 0 12px; font-size: 11px; font-weight: 800; color: rgba(255, 255, 255, 0.45); white-space: nowrap; }

.nav-item {
  display: flex; align-items: center; gap: 12px; height: 46px; padding: 0 14px; margin-right: 16px; border-radius: 14px;
  color: rgba(255, 255, 255, 0.78); font-size: 14.5px; font-weight: 600; cursor: pointer;
  position: relative; text-decoration: none; white-space: nowrap;
  transition: background-color 0.15s, color 0.15s;
}
.sidebar.collapsed .nav-item { justify-content: center; padding: 0; gap: 0; }
.nav-item:hover { background: rgba(255, 255, 255, 0.08); color: #fff; }
.nav-item:focus-visible { outline: 2px solid var(--nm-gold); outline-offset: -2px; }
.nav-icon { flex-shrink: 0; color: rgba(255, 255, 255, 0.7); transition: color 0.15s; }
.nav-item:hover .nav-icon { color: #fff; }
.nav-label { flex: 1; overflow: hidden; text-overflow: ellipsis; }

/* active: a curved tab that opens into the page */
.nav-item.active {
  z-index: 1; margin-right: 0; padding-right: 30px; border-radius: 24px 0 0 24px;
  background: var(--nm-page); color: var(--nm-green); font-weight: 700;
}
.sidebar.collapsed .nav-item.active { padding-right: 16px; }
.nav-item.active .nav-icon { color: var(--nm-green); }
.nav-item.active::before,
.nav-item.active::after {
  content: ''; position: absolute; right: 0; width: 22px; height: 22px; background: transparent; pointer-events: none;
}
.nav-item.active::before { top: -22px; border-bottom-right-radius: 22px; box-shadow: 8px 8px 0 8px var(--nm-page); }
.nav-item.active::after { bottom: -22px; border-top-right-radius: 22px; box-shadow: 8px -8px 0 8px var(--nm-page); }

.nav-badge {
  min-width: 20px; height: 20px; padding: 0 6px; border-radius: 10px; flex-shrink: 0;
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--nm-gold); color: #10231B; font-size: 11px; font-weight: 800; font-variant-numeric: tabular-nums;
}
.nav-badge-dot { position: absolute; top: 9px; right: 14px; width: 8px; height: 8px; border-radius: 50%; background: var(--nm-gold); box-shadow: 0 0 0 2px var(--nm-green); }
.nav-item.active .nav-badge-dot { box-shadow: 0 0 0 2px var(--nm-page); }

/* account: a plain row under a thin line */
.sidebar-account { flex-shrink: 0; position: relative; padding-top: 14px; border-top: 1px solid rgba(255, 255, 255, 0.12); }
.account-trigger {
  display: flex; align-items: center; gap: 10px; width: 100%;
  background: none; border: none; cursor: pointer; padding: 6px 4px; border-radius: 12px; font-family: inherit;
  transition: background-color 0.15s;
}
.sidebar.collapsed .account-trigger { justify-content: center; padding: 6px 0; }
.account-trigger:hover { background: rgba(255, 255, 255, 0.08); }
.account-trigger:focus-visible { outline: 2px solid var(--nm-gold); outline-offset: -2px; }
.account-avatar {
  width: 40px; height: 40px; border-radius: 50%; background: var(--nm-gold); color: var(--nm-green);
  display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; flex-shrink: 0;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.2);
}
.account-avatar-img { object-fit: cover; background: #00382a; }
.account-info { flex: 1; min-width: 0; text-align: left; white-space: nowrap; }
.account-name { margin: 0; font-size: 14px; font-weight: 700; color: #fff; overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
.account-role { margin: 0; font-size: 12px; color: rgba(255, 255, 255, 0.62); overflow: hidden; text-overflow: ellipsis; line-height: 1.3; }
.account-chevron { color: rgba(255, 255, 255, 0.62); flex-shrink: 0; }

.account-menu {
  position: absolute; bottom: calc(100% + 8px); left: 0; right: 0; z-index: 20;
  padding: 6px; border-radius: 14px; background: #FFFFFF;
  box-shadow: 0 0 0 1px rgba(16, 35, 27, 0.06), 0 18px 40px -12px rgba(0, 0, 0, 0.45);
}
.account-menu-collapsed { left: 0; right: auto; width: 210px; }
.account-menu-item {
  display: flex; align-items: center; gap: 10px; width: 100%; height: 40px; padding: 0 12px; border-radius: 10px;
  background: none; border: none; text-align: left; font-family: inherit;
  color: #22362C; font-size: 13.5px; font-weight: 600; text-decoration: none; cursor: pointer; white-space: nowrap;
}
.account-menu-item svg { color: #5D7065; }
.account-menu-item:hover { background: #F1F6F2; }
.account-menu-sep { display: block; height: 1px; margin: 4px 6px; background: #EEF2EF; }
.account-menu-item.logout,
.account-menu-item.logout svg { color: #B42318; }
.account-menu-item.logout:hover { background: #FEF3F2; }

/* ---------- MAIN COLUMN ---------- */
.main-column { flex: 1; display: flex; flex-direction: column; min-width: 0; }

.topbar {
  position: sticky; top: 0; z-index: 10; flex-shrink: 0;
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  min-height: 76px; padding: 12px 36px;
  background: #FFFFFF; border-bottom: 1px solid #CFDAD3;
  box-shadow: 0 6px 18px -14px rgba(16, 35, 27, 0.35);
}
.topbar-left { display: flex; align-items: center; gap: 18px; min-width: 0; }
.topbar-brand { display: flex; flex-direction: column; line-height: 1.1; }
.topbar-brand .logo-text { font-size: 21px; color: var(--nm-green); }
.topbar-brand .logo-match { color: #C49102; }
.topbar-tagline { margin-top: 3px; font-size: 11.5px; font-weight: 600; color: #6B7D73; white-space: nowrap; }
.topbar-sep { width: 2px; height: 38px; border-radius: 2px; background: #B8C9BE; }
.topbar-title { display: flex; flex-direction: column; min-width: 0; }
/* the open sidebar already names the page, so the header title steps aside */
.topbar-title.is-hidden { display: none; }
.topbar h1 { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-weight: 700; line-height: 1.2; color: #10231B; }
.topbar-date { font-size: 12.5px; color: #6B7D73; }
.topbar-actions { display: flex; align-items: center; gap: 10px; }
.icon-btn {
  position: relative; width: 42px; height: 42px; border-radius: 12px; border: 1px solid #DCE5DF;
  background: #FFFFFF; cursor: pointer; display: flex; align-items: center; justify-content: center; color: var(--nm-green);
  transition: background-color 0.15s, border-color 0.15s;
}
.icon-btn:hover { background: #F1F6F2; border-color: #B8C9BE; }
.icon-btn:focus-visible { outline: 2px solid var(--nm-gold); outline-offset: 2px; }

.content { flex: 1; padding: 28px 36px 96px; } /* bottom room so the help button never covers a page's last button */

/* ---------- PHONE ---------- */
.mobile-topbar { display: none; }
.mobile-tabs { display: none; }
.sidebar-overlay { display: none; }

@media (max-width: 900px) {
  .mobile-topbar {
    display: flex; align-items: center; gap: 10px;
    position: sticky; top: 0; z-index: 30;
    padding: 12px 16px; background: var(--nm-green); color: #fff;
    box-shadow: 0 8px 20px -14px rgba(0, 0, 0, 0.5);
  }
  .menu-btn {
    width: 40px; height: 40px; border-radius: 12px; background: rgba(255, 255, 255, 0.1); border: none; color: #fff; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
  }
  .mobile-brand { display: flex; align-items: center; gap: 8px; }
  .mobile-brand .logo-mark { width: 26px; height: 32px; }
  .mobile-brand .logo-text { font-size: 20px; }

  .dashboard-layout { flex-direction: column; height: auto; min-height: 100vh; }
  .topbar { position: static; min-height: 0; padding: 18px 16px 4px; background: transparent; border: none; box-shadow: none; }
  .topbar-brand, .topbar-sep { display: none; }
  .topbar h1 { font-size: 24px; }

  /* the menu slides in from the left, always fully open */
  .sidebar {
    position: fixed; top: 0; left: 0;
    width: 280px !important; padding: 18px 16px 16px 20px !important;
    /* dvh = the visible screen (100vh also counts the area behind a phone's
       address bar, which hid the account section at the bottom). */
    height: 100vh; height: 100dvh;
    z-index: 40;
    overscroll-behavior: contain;
    -webkit-overflow-scrolling: touch;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
  }
  .sidebar.sidebar-open { transform: translateX(0); box-shadow: 8px 0 30px rgba(0, 0, 0, 0.25); }
  /* One scroll area on phones: the whole menu scrolls, not a list inside it. */
  .sidebar-nav { flex: none; overflow: visible; }
  /* in the drawer the active page is a soft pill, not a tab into the page */
  .nav-item.active { margin-right: 16px; padding-right: 14px; border-radius: 14px; }
  .nav-item.active::before,
  .nav-item.active::after { display: none; }
  .sidebar-account { margin-top: auto; }

  .sidebar-overlay { display: block; position: fixed; inset: 0; z-index: 35; background: rgba(4, 30, 21, 0.45); }

  .main-column { height: auto; overflow: visible; }
  .content { padding: 12px 16px 88px; }
  .content.has-tabs { padding-bottom: 120px; }

  /* client: app-style tabs along the bottom */
  .mobile-tabs {
    position: fixed; left: 12px; right: 12px; bottom: 12px; z-index: 30;
    display: grid; grid-template-columns: repeat(5, 1fr); gap: 2px;
    padding: 8px 6px; border-radius: 22px;
    background: #FFFFFF; box-shadow: 0 0 0 1px rgba(16, 35, 27, 0.06), 0 18px 40px -16px rgba(16, 35, 27, 0.45);
    padding-bottom: calc(8px + env(safe-area-inset-bottom, 0px));
  }
  .mobile-tab {
    display: flex; flex-direction: column; align-items: center; gap: 3px;
    padding: 0; border: none; background: none; font-family: inherit; cursor: pointer;
    color: #7A8F84; font-size: 11px; font-weight: 600; text-decoration: none;
  }
  .mobile-tab-icon { width: 48px; height: 30px; border-radius: 999px; display: inline-flex; align-items: center; justify-content: center; transition: background-color 0.15s; }
  .mobile-tab.active { color: var(--nm-green); font-weight: 800; }
  .mobile-tab.active .mobile-tab-icon { background: #E3EFE7; }
}

.topbar-me { display: none; }
.title-phone { display: none; }
@media (max-width: 900px) {
  /* clients get app-style navigation: the bottom tabs + this header */
  .is-client .mobile-topbar { display: none; }
  .is-client .topbar {
    position: sticky; top: 0; z-index: 20;
    padding: 14px 16px 10px;
    /* solid, no blur: a blur here would trap the bell's pop-up inside the header */
    background: #F5F7F5;
  }
  .is-client .topbar-left { gap: 12px; }
  .is-client .topbar-me {
    flex-shrink: 0; width: 46px; height: 46px; padding: 0; border: none; border-radius: 50%; cursor: pointer;
    background: var(--nm-gold); color: var(--nm-green); font-family: inherit; font-size: 15px; font-weight: 800;
    display: inline-flex; align-items: center; justify-content: center; overflow: hidden;
    box-shadow: 0 0 0 3px #FFFFFF, 0 6px 14px -6px rgba(0, 0, 0, 0.3);
  }
  .is-client .topbar-me img { width: 100%; height: 100%; object-fit: cover; }
  .is-client .topbar-me { text-decoration: none; }
  .is-client .topbar-me:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
  .is-client .topbar-title { flex-direction: column; }
  .is-client .topbar-date { font-size: 12.5px; }
  .is-client .topbar h1 { font-size: 21px; }
  .is-client .title-desk { display: none; }
  .is-client .title-phone { display: inline; }
  .mobile-tab-icon { position: relative; }
  .mobile-tab-dot { position: absolute; top: 2px; right: 6px; width: 9px; height: 9px; border-radius: 50%; background: #efbf04; border: 2px solid #fff; }
  .is-admin .topbar-left { flex: 1; }
  .is-client .icon-btn { width: 44px; height: 44px; border-radius: 50%; }
}

/* hide the "keep open" pin button; the menu still opens on hover */
.pin-btn { display: none !important; }
</style>