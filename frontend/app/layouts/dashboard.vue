<template>
  <div class="dashboard-layout">
    <!-- SIDEBAR -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <Leaf class="logo-icon" :size="20" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </div>

      <!-- PROFILE CARD -->
      <div class="profile-card">
        <div class="profile-avatar">{{ userInitials }}</div>
        <p class="profile-name">{{ displayName }}</p>
        <p v-if="isRnd" class="profile-specialty">{{ rndProfile.specialty }}</p>
        <p v-if="isRnd" class="profile-prc">● PRC #{{ rndProfile.prc }} · {{ auth.rndProfile?.is_verified ? 'Verified' : 'Pending Verification' }}</p>
        <p v-else class="profile-specialty">{{ roleLabel }}</p>
      </div>

      <nav class="sidebar-nav">
        <NuxtLink
          v-for="item in mainNav"
          :key="item.label"
          :to="item.to"
          class="nav-item"
          :class="{ active: route.path === item.to }"
        >
          <component :is="item.icon" class="nav-icon" :size="17" />
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </NuxtLink>

        <p v-if="accountNav.length" class="nav-group-label">ACCOUNT</p>
        <NuxtLink
          v-for="item in accountNav"
          :key="item.label"
          :to="item.to"
          class="nav-item"
          :class="{ active: route.path === item.to }"
        >
          <component :is="item.icon" class="nav-icon" :size="17" />
          <span class="nav-label">{{ item.label }}</span>
        </NuxtLink>

        <button class="nav-item logout-item" @click="handleLogout">
          <LogOut class="nav-icon" :size="17" />
          <span class="nav-label">Log Out</span>
        </button>
      </nav>
    </aside>

    <!-- MAIN COLUMN -->
    <div class="main-column">
      <!-- STICKY TOP HEADER -->
      <!-- <header class="topbar">
        <div>
          <h1>{{ pageTitle }}</h1>
          <span class="topbar-date">{{ todayLabel }}</span>
        </div>
        <div class="topbar-actions">
          <div class="search-box">
            <Search class="search-icon" :size="15" />
            <input type="text" placeholder="Search patients, records..." />
          </div>
          <button class="icon-btn"><MessageSquare :size="17" /></button>
          <button class="icon-btn"><Bell :size="17" /></button>
          <button class="icon-btn avatar-btn"><User :size="17" /></button>
        </div>
      </header> -->

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
  Search as SearchIcon, CalendarDays, FileText, MessageCircle,
  Wallet, Star, UserCog, Languages, LogOut, MessageSquare, Bell, User
} from 'lucide-vue-next'

const route = useRoute()
const auth = useAuthStore()
const todayLabel = 'Friday, May 15, 2026'

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

const rndMainNav = [
  { icon: LayoutDashboard, label: 'Dashboard', to: '/rnd-dashboard' },
  { icon: Users, label: 'My Patients', to: '/my-patients' },
  { icon: CalendarCheck, label: 'Appointments', to: '/appointments' },
  { icon: LineChart, label: 'NCP Records', to: '/ncp-records' },
  { icon: Target, label: 'Meal Plans', to: '/meal-planning' },
  { icon: SearchIcon, label: 'Food Exchange Search', to: '/food-exchange-search' },
  { icon: CalendarDays, label: 'Availability', to: '/availability' },
  { icon: FileText, label: 'Resources', to: '/resource-library' },
  { icon: MessageCircle, label: 'Messages', to: '/messages' },
  { icon: Wallet, label: 'Earnings', to: '/earnings' },
  { icon: Star, label: 'Reviews', to: '/reviews' }
]

const rndAccountNav = [
  { icon: UserCog, label: 'Profile Settings', to: '/profile-settings' },
  { icon: Languages, label: 'Languages', to: '/languages' }
]

// Client-facing pages are still being built out (Phase 6) — only pages already
// verified to work for a client role are linked here, see vault/TODO.md.
const clientMainNav = [
  { icon: SearchIcon, label: 'Find an RND', to: '/find-rnd' },
  { icon: CalendarCheck, label: 'Appointments', to: '/appointments' },
  { icon: MessageCircle, label: 'Messages', to: '/messages' },
  { icon: Star, label: 'Reviews', to: '/reviews' }
]

const clientAccountNav = [
  { icon: UserCog, label: 'Profile Settings', to: '/profile-settings' }
]

const mainNav = computed(() => (isRnd.value ? rndMainNav : clientMainNav))
const accountNav = computed(() => (isRnd.value ? rndAccountNav : clientAccountNav))

function handleLogout() {
  auth.logout()
  navigateTo('/login')
}
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

/* SIDEBAR */
.sidebar {
  width: 240px; flex-shrink: 0; background: #14301a; color: #fff;
  padding: 24px 20px; height: 100vh; position: sticky; top: 0; overflow-y: auto;
}
.sidebar-brand { display: flex; align-items: center; gap: 8px; font-size: 1.15rem; font-weight: 700; margin-bottom: 20px; }
.logo-icon { color: #D4A017; flex-shrink: 0; }
.logo-match { color: #D4A017; }

/* PROFILE CARD */
.profile-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(212,160,23,0.25);
  border-radius: 12px;
  padding: 18px 16px;
  margin-bottom: 20px;
  text-align: left;
}
.profile-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: #D4A017; color: #1a3a1a;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.95rem;
  margin-bottom: 10px;
}
.profile-name { font-size: 0.92rem; font-weight: 700; color: #fff; margin: 0 0 2px; }
.profile-specialty { font-size: 0.75rem; color: #9ab89a; margin: 0 0 6px; }
.profile-prc { font-size: 0.68rem; color: #D4A017; font-weight: 600; margin: 0; }

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
.logout-item { margin-top: 4px; }

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
</style>