<template>
  <div class="dashboard-layout">
    <!-- MOBILE TOPBAR -->
    <div class="mobile-topbar">
      <button class="menu-btn" type="button" aria-label="Toggle menu" @click="isSidebarOpen = !isSidebarOpen">
        <Menu :size="22" />
      </button>
      <div class="mobile-brand">
        <Leaf class="logo-icon" :size="18" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </div>
    </div>

    <!-- MOBILE OVERLAY -->
    <div v-if="isSidebarOpen" class="sidebar-overlay" @click="isSidebarOpen = false"></div>

    <!-- SIDEBAR -->
    <aside class="sidebar" :class="{ 'sidebar-open': isSidebarOpen }">
      <div class="sidebar-brand">
        <Leaf class="logo-icon" :size="20" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </div>

      <!-- NAV + ACCOUNT FOOTER — gated on auth.hydrated: auth.user only exists
           client-side (JWT lives in localStorage, unreadable during SSR), so
           rendering this before hydration completes sends the server a guess
           that's wrong for every RND/admin. Vue's hydration-mismatch repair
           then patches some nodes (labels) but not others (icons, hrefs),
           producing a genuinely broken mixed render rather than a clean one.
           Structured as a flex column so the account footer (profile +
           settings) stays pinned to the bottom of the viewport, independent
           of the main nav's own scroll region — same pattern as Claude's
           own sidebar. -->
      <template v-if="auth.hydrated">
        <nav class="sidebar-nav">
          <NuxtLink
            v-for="item in mainNav"
            :key="item.label"
            :to="item.to"
            class="nav-item"
            :class="{ active: route.path === item.to }"
            @click="isSidebarOpen = false"
          >
            <component :is="item.icon" class="nav-icon" :size="17" />
            <span class="nav-label">{{ item.label }}</span>
            <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
          </NuxtLink>
        </nav>

        <NuxtLink to="/profile-settings" class="account-footer" @click="isSidebarOpen = false">
          <div class="profile-avatar">{{ userInitials }}</div>
          <div class="account-footer-text">
            <p class="profile-name">{{ displayName }}</p>
            <p v-if="isRnd" class="profile-specialty">{{ rndProfile.specialty }}</p>
            <p v-else class="profile-specialty">{{ roleLabel }}</p>
          </div>
          <UserCog class="account-footer-icon" :size="16" />
        </NuxtLink>
      </template>
    </aside>

    <!-- MAIN COLUMN -->
    <div class="main-column">
      <!-- STICKY TOP HEADER — page title left, real notification bell right.
           Search/messages/avatar buttons dropped: the earlier version had
           no click handlers or backing state at all, just markup. -->
      <header class="topbar">
        <div>
          <h1>{{ pageTitle }}</h1>
        </div>
        <div class="topbar-actions">
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
  Leaf, LayoutDashboard, Users, CalendarCheck, LineChart, Target,
  Search as SearchIcon, FileText, MessageCircle,
  Star, UserCog, Menu, Receipt, TrendingUp
} from 'lucide-vue-next'

const route = useRoute()
const auth = useAuthStore()
const isSidebarOpen = ref(false)

// Close the mobile sidebar automatically on route change (e.g. browser back/forward).
watch(() => route.path, () => { isSidebarOpen.value = false })

// Page title comes from each page's definePageMeta({ title: '...' })
const pageTitle = computed(() => route.meta.title || 'Dashboard')

const isRnd = computed(() => auth.user?.role === 'rnd')
const roleLabel = computed(() => (auth.user?.role === 'client' ? 'Client' : 'Admin'))

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

// Main nav = daily working tools only. Availability/Earnings/Resources/
// Reviews are checked periodically, not opened as part of routine
// clinical work, so they live in Account/Settings instead — see
// vault/TODO.md for the reasoning behind this split. Food Exchange
// Search stays in Main since it's referenced live during meal-plan
// building and patient counseling, not a one-time config screen.
const rndMainNav = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/rnd-dashboard' },
  { icon: Users, label: 'My Patients', to: '/my-patients' },
  { icon: CalendarCheck, label: 'Appointments', to: '/appointments' },
  { icon: LineChart, label: 'NCP Records', to: '/ncp-records' },
  { icon: Target, label: 'Meal Plans', to: '/meal-planning' },
  { icon: SearchIcon, label: 'Food Exchange Search', to: '/food-exchange-search' },
  { icon: MessageCircle, label: 'Messages', to: '/messages' },
]

// Availability/Earnings/Resources/Reviews now live as tabs inside
// Profile Settings rather than separate nav destinations — see
// ProfileSettings.vue's rndTabs. Notifications moved to the topbar bell
// (real unread badge, not a nav link) instead of a dedicated page.
// Profile Settings itself is reached via the pinned account-footer link
// at the bottom of the sidebar, not a nav array entry — see template.

// Client-facing pages are still being built out (Phase 6) — only pages already
// verified to work for a client role are linked here, see vault/TODO.md.
const clientMainNav = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/client-dashboard' },
  { icon: SearchIcon, label: 'Find an RND', to: '/find-rnd' },
  { icon: CalendarCheck, label: 'Appointments', to: '/appointments' },
  { icon: Target, label: 'My Meal Plan', to: '/meal-plan-view' },
  { icon: TrendingUp, label: 'Progress Tracker', to: '/progress-tracker' },
  { icon: FileText, label: 'Resources', to: '/resource-library' },
  { icon: MessageCircle, label: 'Messages', to: '/messages' },
  { icon: Receipt, label: 'Billing', to: '/invoices-billing' },
  { icon: Star, label: 'Reviews', to: '/reviews' }
]

const mainNav = computed(() => (isRnd.value ? rndMainNav : clientMainNav))
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

/* SIDEBAR — flex column so the account footer stays pinned to the
   bottom of the viewport, independent of the nav's own scroll region. */
.sidebar {
  width: 240px; flex-shrink: 0; background: #14301a; color: #fff;
  padding: 24px 20px; height: 100vh; position: sticky; top: 0;
  display: flex; flex-direction: column; overflow: hidden;
}
.sidebar-brand { display: flex; align-items: center; gap: 8px; font-size: 1.15rem; font-weight: 700; margin-bottom: 20px; flex-shrink: 0; }
.logo-icon { color: #D4A017; flex-shrink: 0; }
.logo-match { color: #D4A017; }

.sidebar-nav { flex: 1; overflow-y: auto; min-height: 0; }

/* ACCOUNT FOOTER — pinned to the bottom via flex, links straight to
   Profile Settings (Log Out now lives on that page, not here). */
.account-footer {
  display: flex; align-items: center; gap: 10px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(212,160,23,0.25);
  border-radius: 12px;
  padding: 12px 14px;
  margin-top: 12px;
  flex-shrink: 0;
  text-decoration: none;
  transition: background 0.15s;
}
.account-footer:hover { background: rgba(255,255,255,0.08); }
.account-footer-text { flex: 1; min-width: 0; }
.account-footer-icon { color: #9ab89a; flex-shrink: 0; }
.profile-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: #D4A017; color: #1a3a1a;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.85rem;
  flex-shrink: 0;
}
.profile-name { font-size: 0.86rem; font-weight: 700; color: #fff; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile-specialty { font-size: 0.72rem; color: #9ab89a; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.nav-group-label { font-size: 0.65rem; letter-spacing: 0.1em; color: #5a7a5a; margin: 20px 0 8px; padding-left: 10px; }
.nav-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 10px; border-radius: 8px;
  color: #c8d8c8; font-size: 0.88rem; font-weight: 500; cursor: pointer; transition: background 0.15s;
  position: relative; text-decoration: none;
  width: 100%; background: none; border: none; text-align: left; font-family: inherit;
}
.nav-item:hover { background: rgba(255,255,255,0.05); }
.nav-item.active { background: #D4A017; color: #1a3a1a; font-weight: 700; }
.nav-item.active .nav-icon { color: #1a3a1a; }
.nav-icon { flex-shrink: 0; }
.nav-label { flex: 1; }
.nav-badge { background: #D4A017; color: #1a3a1a; font-size: 0.68rem; font-weight: 700; padding: 1px 7px; border-radius: 10px; }

/* MAIN COLUMN */
.main-column { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

.topbar {
  position: sticky; top: 0; z-index: 10; background: #fff; border-bottom: 1px solid #eceeec;
  padding: 18px 32px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
}
.topbar h1 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a3a1a; margin: 0; }
.topbar-date { font-size: 0.8rem; color: #8a9a8a; }
.topbar-actions { display: flex; align-items: center; gap: 12px; }
.search-box { display: flex; align-items: center; gap: 8px; background: #f4f6f4; border-radius: 8px; padding: 8px 14px; width: 260px; }
.search-box input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }
.icon-btn {
  width: 36px; height: 36px; border-radius: 8px; border: 1px solid #e5e8e5;
  background: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #4a5a4a;
}
.avatar-btn { border-radius: 50%; }

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
    background: #14301a;
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

  .dashboard-layout { flex-direction: column; height: auto; min-height: 100vh; }

  .sidebar {
    position: fixed;
    top: 0; left: 0;
    height: 100vh;
    z-index: 40;
    transform: translateX(-100%);
    transition: transform 0.2s ease;
    box-shadow: 4px 0 24px rgba(0,0,0,0.2);
  }
  .sidebar.sidebar-open { transform: translateX(0); }

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