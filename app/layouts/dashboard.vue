<template>
  <div class="dashboard-layout">
    <!-- SIDEBAR -->
    <aside
      class="sidebar"
      :class="{ collapsed: isCollapsed }"
      @mouseenter="isCollapsed = false"
      @mouseleave="isCollapsed = true"
    >
      <!-- BRAND -->
      <div class="sidebar-top">
        <div class="sidebar-brand">
          <img src="/resources/nutrimatchlogo.png" alt="NutriMatch" class="logo-mark" />
          <div v-if="!isCollapsed" class="brand-text">
            <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
          </div>
        </div>
        <span v-if="!isCollapsed" class="brand-tagline">Clinical Nutrition System</span>
        <div v-if="!isCollapsed" class="portal-badge"><span class="portal-dot"></span>RND Portal</div>
        <div v-if="!isCollapsed" class="sidebar-divider"></div>
      </div>

      <!-- NAV -->
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
          >
            <component :is="item.icon" class="nav-icon" :size="17" />
            <span v-if="!isCollapsed" class="nav-label">{{ item.label }}</span>
            <span v-if="item.badge && !isCollapsed" class="nav-badge">{{ item.badge }}</span>
            <span v-else-if="item.badge && isCollapsed" class="nav-badge-dot"></span>
          </NuxtLink>
        </template>
      </nav>

      <!-- BOTTOM ACCOUNT BLOCK -->
      <div class="sidebar-account">
        <button class="account-trigger" @click.stop="showAccountMenu = !showAccountMenu" :title="isCollapsed ? user.name : null">
          <div class="account-avatar">{{ userInitials }}</div>
          <div v-if="!isCollapsed" class="account-info">
            <p class="account-name">{{ user.name }}</p>
            <p class="account-role">RND</p>
          </div>
          <component v-if="!isCollapsed" :is="showAccountMenu ? ChevronUp : ChevronDown" class="account-chevron" :size="15" />
        </button>

        <div v-if="showAccountMenu" class="account-menu" :class="{ 'account-menu-collapsed': isCollapsed }">
          <NuxtLink to="/profile-settings" class="account-menu-item" @click="showAccountMenu = false">
            <UserCog :size="15" /> <span v-if="!isCollapsed">Profile Settings</span>
          </NuxtLink>
          <NuxtLink to="/languages" class="account-menu-item" @click="showAccountMenu = false">
            <Languages :size="15" /> <span v-if="!isCollapsed">Languages</span>
          </NuxtLink>
          <button class="account-menu-item logout" @click="handleLogout">
            <LogOut :size="15" /> <span v-if="!isCollapsed">Sign Out</span>
          </button>
        </div>
      </div>
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
          <div class="search-box">
            <SearchIcon class="search-icon" :size="15" />
            <input type="text" placeholder="Search patients, records..." />
          </div>

          <button class="icon-btn" @click="navigateTo('/messages')"><MessageSquare :size="17" /></button>

          <div class="icon-btn-wrap">
            <button class="icon-btn" @click.stop="toggleNotifications">
              <Bell :size="17" />
              <span v-if="notifications.length" class="icon-dot"></span>
            </button>
            <div v-if="showNotifications" class="dropdown-panel notif-panel">
              <div class="dropdown-header">
                <span>Notifications</span>
                <button class="mark-read" @click="notifications = []">Mark all read</button>
              </div>
              <div v-if="notifications.length === 0" class="notif-empty">You're all caught up.</div>
              <div v-for="n in notifications" :key="n.id" class="notif-item">
                <div class="notif-avatar">{{ n.initials }}</div>
                <div>
                  <p class="notif-text"><strong>{{ n.name }}</strong> {{ n.message }}</p>
                  <p class="notif-time">{{ n.time }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="icon-btn-wrap">
            <button class="icon-btn avatar-btn" @click.stop="toggleProfilePopover">
              <User :size="17" />
            </button>
            <div v-if="showProfilePopover" class="dropdown-panel profile-panel">
              <div class="profile-panel-avatar">{{ userInitials }}</div>
              <p class="profile-panel-name">{{ user.name }}, RND</p>
              <p class="profile-panel-role">Registered Nutritionist-Dietitian</p>
              <p class="profile-panel-license">License No. {{ user.prc }}-RND</p>
              <hr />
              <NuxtLink to="/profile-settings" class="profile-panel-item" @click="showProfilePopover = false">
                <SettingsIcon :size="15" /> Settings
              </NuxtLink>
              <button class="profile-panel-item logout" @click="handleLogout">
                <LogOut :size="15" /> Sign Out
              </button>
            </div>
          </div>
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
  Search as SearchIcon, CalendarDays, FileText,
  Wallet, Star, UserCog, Languages, LogOut, MessageSquare, Bell, User,
  ChevronDown, ChevronUp, Settings as SettingsIcon
} from 'lucide-vue-next'

const route = useRoute()
const todayLabel = 'Friday, May 15, 2026'
const isCollapsed = ref(true)

const pageTitle = computed(() => route.meta.title || 'Dashboard')

// Replace with real user data (e.g. from a store or auth composable)
const user = {
  name: 'Ivy Hope Alba',
  specialty: 'Diabetes & Renal Specialist',
  prc: '0012345'
}

const userInitials = computed(() =>
  user.name
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
)

// TODO: wire badge counts to real data (active patients, upcoming appointments, etc.)
// Earnings, Reviews, and Availability were moved into Profile Settings and
// removed from here per request.
const navGroups = [
  {
    label: 'MAIN',
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', to: '/rnd-dashboard' },
      { icon: Users, label: 'My Patients', to: '/my-patients', badge: 28 },
      { icon: CalendarCheck, label: 'Appointments', to: '/appointments', badge: 5 }
    ]
  },
  {
    label: 'CLINICAL',
    items: [
      { icon: LineChart, label: 'NCP Records', to: '/ncp-records' },
      { icon: Target, label: 'Meal Plans', to: '/meal-planning' },
      { icon: SearchIcon, label: 'Food Exchange Search', to: '/food-exchange-search' }
    ]
  },
  {
    label: 'RESOURCES',
    items: [
      { icon: FileText, label: 'Resources', to: '/resource-library' }
    ]
  }
]

const showAccountMenu = ref(false)
const showNotifications = ref(false)
const showProfilePopover = ref(false)

// TODO: replace with real notifications from your API/store
const notifications = ref([
  { id: 1, initials: 'MT', name: 'Maria Torres', message: 'sent you a message', time: '4 hours ago' },
  { id: 2, initials: 'EP', name: 'Edgar Pascual', message: 'requested a reschedule', time: 'Yesterday' }
])

function toggleNotifications() {
  showNotifications.value = !showNotifications.value
  showProfilePopover.value = false
}
function toggleProfilePopover() {
  showProfilePopover.value = !showProfilePopover.value
  showNotifications.value = false
}

function handleLogout() {
  navigateTo('/login')
}

function handleClickOutside() {
  showAccountMenu.value = false
  showNotifications.value = false
  showProfilePopover.value = false
}
onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600;700&family=DM+Sans:opsz,wght@9..40,400;9..40,700&display=swap');

* { box-sizing: border-box; }

.dashboard-layout {
  display: flex;
  height: 100vh;
  font-family: 'Inter', sans-serif;
  background: #f7f8f6;
}

/* SIDEBAR */
.sidebar {
  width: 76px; flex-shrink: 0; background: #004D3A; color: #fff;
  padding: 14px 14px 28px; height: 100vh; overflow-y: auto; overflow-x: hidden;
  display: flex; flex-direction: column;
  position: sticky; top: 0; z-index: 40;
  transition: width 0.2s ease, padding 0.2s ease;
  scrollbar-width: none; -ms-overflow-style: none;
}
.sidebar::-webkit-scrollbar { display: none; }
.sidebar:not(.collapsed) {
  width: 260px; padding: 14px 22px 28px;
}

/* BRAND */
.sidebar-top { margin-bottom: 18px; flex-shrink: 0; position: relative; }
.sidebar-brand { display: flex; flex-direction: row; align-items: center; gap: 12px; margin-bottom: 14px; }
.sidebar.collapsed .sidebar-brand { justify-content: center; margin-bottom: 16px; }
.logo-mark { width: 40px; height: 40px; flex-shrink: 0; object-fit: contain; }
.sidebar.collapsed .logo-mark { width: 32px; height: 32px; }
.brand-text { display: flex; flex-direction: column; line-height: 1.2; white-space: nowrap; }
.logo-text { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #fff; letter-spacing: 0; }
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

/* NAV */
.sidebar-nav {
  flex: 1; overflow-y: auto; overflow-x: hidden;
  scrollbar-width: none; -ms-overflow-style: none;
}
.sidebar-nav::-webkit-scrollbar { display: none; }
.nav-group-label { font-size: 0.65rem; letter-spacing: 0.12em; color: #5a7a5a; margin: 24px 0 10px; padding-left: 12px; white-space: nowrap; }
.nav-group-label:first-child { margin-top: 6px; }
.nav-item {
  display: flex; align-items: center; gap: 11px; padding: 10px 10px; border-radius: 8px;
  color: #9fb5a3; font-size: 0.82rem; font-weight: 500; cursor: pointer; transition: background 0.15s;
  position: relative; text-decoration: none;
  width: 100%; background: none; border: none; text-align: left; font-family: inherit;
  white-space: nowrap; overflow: hidden; margin-bottom: 8px;
}
.sidebar.collapsed .nav-item { justify-content: center; padding: 8px 0; gap: 0; }
.nav-item:hover { background: rgba(255,255,255,0.05); }
.nav-item.active {
  background: #3a5a3a;
  color: #fff;
  font-weight: 700;
  border-left: 3px solid #D4A017;
  padding-left: 7px;
}
.sidebar.collapsed .nav-item.active { padding-left: 0; border-left: none; border-radius: 8px; }
.nav-item.active .nav-icon { color: #D4A017; }
.nav-icon { flex-shrink: 0; }
.nav-label { flex: 1; }
.nav-badge { background: #D4A017; color: #1a3a1a; font-size: 0.68rem; font-weight: 700; padding: 1px 7px; border-radius: 10px; flex-shrink: 0; }
.nav-badge-dot { position: absolute; top: 8px; right: 14px; width: 7px; height: 7px; border-radius: 50%; background: #D4A017; }

/* BOTTOM ACCOUNT BLOCK */
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
.account-name { font-size: 0.85rem; font-weight: 700; color: #fff; margin: 0; }
.account-role { font-size: 0.7rem; color: #9ab89a; margin: 0; }
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
.search-box { display: flex; align-items: center; gap: 8px; background: #f4f6f4; border-radius: 8px; padding: 8px 14px; width: 260px; }
.search-box input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }
.icon-btn {
  width: 36px; height: 36px; border-radius: 8px; border: 1px solid #e5e8e5;
  background: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #4a5a4a;
  position: relative;
}
.avatar-btn { border-radius: 50%; }
.icon-btn-wrap { position: relative; }
.icon-dot { position: absolute; top: 7px; right: 7px; width: 7px; height: 7px; border-radius: 50%; background: #D4A017; }

/* DROPDOWNS */
.dropdown-panel {
  position: absolute; top: calc(100% + 10px); right: 0; width: 300px;
  background: #fff; border: 1px solid #eceeec; border-radius: 12px;
  box-shadow: 0 12px 32px rgba(0,0,0,0.12); z-index: 30; padding: 14px;
}
.dropdown-header { display: flex; align-items: center; justify-content: space-between; font-weight: 700; color: #1a3a1a; font-size: 0.9rem; margin-bottom: 10px; }
.mark-read { background: none; border: none; color: #D4A017; font-size: 0.75rem; font-weight: 600; cursor: pointer; }
.notif-empty { font-size: 0.82rem; color: #8a9a8a; padding: 10px 0; }
.notif-item { display: flex; gap: 10px; padding: 8px 0; border-top: 1px solid #f2f4f2; }
.notif-item:first-of-type { border-top: none; }
.notif-avatar { width: 28px; height: 28px; border-radius: 50%; background: #e8f0e8; color: #1a3a1a; font-size: 0.7rem; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.notif-text { font-size: 0.82rem; color: #3a4a3a; margin: 0; line-height: 1.3; }
.notif-time { font-size: 0.7rem; color: #9aaa9a; margin: 2px 0 0; }

.profile-panel { text-align: center; }
.profile-panel-avatar { width: 44px; height: 44px; border-radius: 50%; background: #004D3A; color: #D4A017; font-weight: 700; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; }
.profile-panel-name { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.profile-panel-role { font-size: 0.75rem; color: #6a7a6a; margin: 2px 0 0; }
.profile-panel-license { font-size: 0.7rem; color: #9aaa9a; margin: 2px 0 10px; }
.profile-panel hr { border: none; border-top: 1px solid #f0f2f0; margin: 10px 0; }
.profile-panel-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 6px; border-radius: 6px;
  color: #3a4a3a; font-size: 0.83rem; text-decoration: none; cursor: pointer;
  width: 100%; background: none; border: none; text-align: left; font-family: inherit;
}
.profile-panel-item:hover { background: #f4f6f4; }
.profile-panel-item.logout { color: #c85a5a; }

.content { flex: 1; overflow-y: auto; padding: 24px 40px 32px; }
</style>