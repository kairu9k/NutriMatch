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
        <span v-if="!isCollapsed" class="portal-badge"><span class="portal-dot"></span> Client Portal</span>
        <div v-if="!isCollapsed" class="sidebar-divider"></div>
      </div>

      <nav class="sidebar-nav">
        <div v-for="group in navGroups" :key="group.label" class="nav-group">
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
            <span v-if="!isCollapsed && item.badge" class="nav-badge">{{ item.badge }}</span>
          </NuxtLink>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div v-if="!isCollapsed" class="sidebar-divider"></div>
        <div class="profile-card" :class="{ collapsed: isCollapsed }">
          <div class="profile-avatar">{{ userInitials }}</div>
          <div v-if="!isCollapsed" class="profile-text">
            <span class="profile-name">{{ userName }}</span>
            <span class="profile-role">Patient</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- MAIN COLUMN -->
    <div class="main-column">
      <header class="topbar">
        <div>
          <h1>{{ pageTitle }}</h1>
          <span class="topbar-date">{{ pageSubtitle }}</span>
        </div>

        <div class="topbar-actions">
          <div class="notif-dropdown" ref="notifDropdownEl">
            <button class="icon-btn" @click="notifDropdownOpen = !notifDropdownOpen">
              <Bell :size="17" /><span v-if="notifications.length" class="icon-dot"></span>
            </button>
            <div v-if="notifDropdownOpen" class="notif-popover">
              <p class="notif-title">Notifications</p>
              <div v-for="n in notifications" :key="n.id" class="notif-item">
                <span class="notif-dot" :class="n.color"></span>
                <div>
                  <p class="notif-text">{{ n.text }}</p>
                  <p class="notif-time">{{ n.time }}</p>
                </div>
              </div>
            </div>
          </div>
          <button class="icon-btn" @click="navigateTo('/messages')"><MessageSquare :size="17" /></button>

          <div class="profile-dropdown" ref="profileDropdownEl">
            <button class="icon-btn avatar-btn" @click="profileDropdownOpen = !profileDropdownOpen"><User :size="17" /></button>
            <div v-if="profileDropdownOpen" class="profile-popover">
              <div class="popover-header">
                <div class="popover-avatar">{{ userInitials }}</div>
                <div>
                  <p class="popover-name">{{ userName }}</p>
                  <p class="popover-role">Patient</p>
                </div>
              </div>
              <div class="popover-divider"></div>
              <NuxtLink to="/client-profile-settings" class="popover-item" @click="profileDropdownOpen = false"><Settings :size="16" /> Settings</NuxtLink>
              <button class="popover-item popover-item-danger" @click="handleLogout"><LogOut :size="16" /> Sign Out</button>
            </div>
          </div>
        </div>
      </header>

      <main class="content">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import {
  LayoutDashboard, Search, CalendarCheck, ClipboardList, LineChart,
  FileText, MessageSquare, LogOut, Bell, User, Settings, AlarmClock, Receipt
} from 'lucide-vue-next'

const route = useRoute()
const todayLabel = 'Friday, May 15, 2026'
const isCollapsed = ref(true)

const pageTitle = computed(() => route.meta.title || 'Dashboard')
const pageSubtitle = computed(() => route.meta.subtitle || todayLabel)

// TODO: pull from the real client profile once that endpoint exists.
const userName = 'Juan Dela Cruz'
const userInitials = 'JD'

const navGroups = [
  {
    label: 'OVERVIEW',
    items: [
      { icon: LayoutDashboard, label: 'Dashboard', to: '/client-dashboard' }
    ]
  },
  {
    label: 'HEALTH',
    items: [
      { icon: CalendarCheck, label: 'Appointments', to: '/appointments' },
      { icon: ClipboardList, label: 'My Meal Plan', to: '/meal-plan-view' },
      { icon: LineChart, label: 'Progress Tracker', to: '/progress-tracker' }
    ]
  },
  {
    label: 'CLINICAL',
    items: [
      { icon: Search, label: 'Find an RND', to: '/find-rnd' }
    ]
  },
  {
    label: 'CONNECT',
    items: [
      { icon: FileText, label: 'Resources', to: '/resources-library' },
      { icon: AlarmClock, label: 'Reminders', to: '/reminders' },
      { icon: Receipt, label: 'Billing', to: '/invoices-billing' }
    ]
  }
]

const notifications = ref([
  { id: 1, text: 'RND Reyes approved your consultation request', time: '1 hr ago', color: 'dot-green' },
  { id: 2, text: 'Your meal plan has been updated', time: 'Today 9:30 AM', color: 'dot-gold' },
  { id: 3, text: 'Reminder: Log your meals for today', time: 'Today 8:00 AM', color: 'dot-blue' }
])
const notifDropdownOpen = ref(false)
const notifDropdownEl = ref(null)
function handleNotifClickOutside(e) {
  if (notifDropdownEl.value && !notifDropdownEl.value.contains(e.target)) notifDropdownOpen.value = false
}
onMounted(() => document.addEventListener('click', handleNotifClickOutside))
onUnmounted(() => document.removeEventListener('click', handleNotifClickOutside))

const profileDropdownOpen = ref(false)
const profileDropdownEl = ref(null)
function handleProfileClickOutside(e) {
  if (profileDropdownEl.value && !profileDropdownEl.value.contains(e.target)) profileDropdownOpen.value = false
}
onMounted(() => document.addEventListener('click', handleProfileClickOutside))
onUnmounted(() => document.removeEventListener('click', handleProfileClickOutside))

function handleLogout() {
  navigateTo('/login')
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600;700&display=swap');

* { box-sizing: border-box; }

.dashboard-layout { display: flex; height: 100vh; font-family: 'Inter', sans-serif; background: #f7f8f6; }

/* SIDEBAR */
.sidebar {
  width: 76px; flex-shrink: 0; background: #004D3A; color: #fff;
  padding: 14px 14px 16px; height: 100vh; overflow-y: auto; overflow-x: hidden;
  display: flex; flex-direction: column;
  position: sticky; top: 0; z-index: 40;
  transition: width 0.2s ease, padding 0.2s ease;
  scrollbar-width: none; -ms-overflow-style: none;
}
.sidebar::-webkit-scrollbar { display: none; }
.sidebar:not(.collapsed) { width: 250px; padding: 14px 20px 16px; }

.sidebar-top { margin-bottom: 20px; flex-shrink: 0; }
.sidebar-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.sidebar.collapsed .sidebar-brand { justify-content: center; }
.logo-mark { width: 40px; height: 40px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; }
.sidebar.collapsed .logo-mark { width: 45px; height: 40px; font-size: 1.1rem; }
.brand-text { display: flex; flex-direction: column; line-height: 1.2; white-space: nowrap; }
.logo-text { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #fff; }
.logo-match { color: #D4A017; }
.brand-tagline { display: block; font-size: 0.55rem; letter-spacing: 0.16em; color: #8fae9f; text-transform: uppercase; margin: 0 0 10px; font-weight: 600; white-space: nowrap; }
.portal-badge {
  display: inline-flex; align-items: center; gap: 6px; font-size: 0.65rem; font-weight: 700; letter-spacing: 0.06em;
  color: #D4A017; border: 1px solid rgba(212,160,23,0.5); border-radius: 999px; padding: 4px 10px; margin-bottom: 14px; white-space: nowrap;
}
.portal-dot { width: 5px; height: 5px; border-radius: 50%; background: #D4A017; flex-shrink: 0; }
.sidebar-divider { border-bottom: 1px solid rgba(255,255,255,0.15); margin-top: 8px; }

.sidebar-nav { flex: 1; overflow-y: auto; overflow-x: hidden; scrollbar-width: none; }
.sidebar-nav::-webkit-scrollbar { display: none; }
.nav-group { margin-bottom: 15px; }
.nav-group-label { font-size: 0.65rem; letter-spacing: 0.12em; color: #5a7a5a; margin: 16px 0 8px; padding-left: 12px; white-space: nowrap; }
.nav-group:first-child .nav-group-label { margin-top: 0; }
.nav-item {
  display: flex; align-items: center; gap: 11px; padding: 10px; border-radius: 8px;
  color: #9fb5a3; font-size: 0.82rem; font-weight: 500; cursor: pointer; transition: background 0.15s;
  text-decoration: none; width: 100%; background: none; border: none; text-align: left; font-family: inherit;
  white-space: nowrap; overflow: hidden; margin-bottom: 4px;
}
.sidebar.collapsed .nav-item { justify-content: center; padding: 13px 0; gap: 0; }
.nav-item:hover { background: rgba(255,255,255,0.05); }
.nav-item.active { background: #3a5a3a; color: #fff; font-weight: 700; border-left: 3px solid #D4A017; padding-left: 7px; }
.sidebar.collapsed .nav-item.active { padding-left: 0; border-left: none; border-radius: 8px; }
.nav-item.active .nav-icon { color: #D4A017; }
.nav-icon { flex-shrink: 0; }
.nav-label { flex: 1; }
.nav-badge {
  background: #D4A017; color: #1a3a1a; font-size: 0.65rem; font-weight: 800; border-radius: 999px;
  padding: 2px 7px; flex-shrink: 0;
}

/* FOOTER / PROFILE CARD */
.sidebar-footer { flex-shrink: 0; margin-top: 8px; }
.profile-card {
  display: flex; align-items: center; gap: 10px; padding: 10px; border-radius: 10px; margin: 10px 0 4px;
  text-decoration: none; background: rgba(255,255,255,0.05);
}
.profile-card.collapsed { justify-content: center; padding: 8px 0; margin: 8px 0 4px; }
.profile-avatar {
  width: 34px; height: 34px; border-radius: 8px; background: #D4A017; color: #1a3a1a; font-weight: 800; font-size: 0.8rem;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.profile-text { flex: 1; display: flex; flex-direction: column; line-height: 1.25; overflow: hidden; }
.profile-name { font-size: 0.82rem; font-weight: 700; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile-role { font-size: 0.7rem; color: #9fb5a3; }
.profile-chevron { color: #9fb5a3; flex-shrink: 0; }

/* MAIN COLUMN */
.main-column { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }

.topbar {
  position: sticky; top: 0; z-index: 10; background: #fff; border-bottom: 1px solid #eceeec;
  padding: 18px 32px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0;
}
.topbar h1 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a3a1a; margin: 0; }
.topbar-date { font-size: 0.8rem; color: #8a9a8a; }
.topbar-actions { display: flex; align-items: center; gap: 12px; }
.icon-btn {
  width: 36px; height: 36px; border-radius: 8px; border: 1px solid #e5e8e5;
  background: #fff; cursor: pointer; display: flex; align-items: center; justify-content: center; color: #4a5a4a;
  position: relative; text-decoration: none;
}
.avatar-btn { border-radius: 50%; }

.notif-dropdown { position: relative; }
.notif-popover {
  position: absolute; top: calc(100% + 10px); right: 0; z-index: 50; width: 300px;
  background: #fff; border-radius: 14px; box-shadow: 0 12px 32px rgba(0,0,0,0.14); padding: 16px;
}
.notif-title { font-family: 'Playfair Display', serif; font-size: 1rem; color: #1a3a1a; margin: 0 0 12px; }
.notif-item { display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-top: 1px solid #f2f4f2; }
.notif-item:first-of-type { border-top: none; padding-top: 0; }
.notif-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; margin-top: 5px; }
.notif-dot.dot-green { background: #1f8f5c; }
.notif-dot.dot-gold { background: #D4A017; }
.notif-dot.dot-blue { background: #2a5a8a; }
.notif-text { font-size: 0.85rem; color: #2a2a2a; margin: 0; line-height: 1.4; }
.notif-time { font-size: 0.74rem; color: #9aaa9a; margin: 3px 0 0; }

.profile-dropdown { position: relative; }
.profile-popover {
  position: absolute; top: calc(100% + 10px); right: 0; z-index: 50; width: 240px;
  background: #fff; border-radius: 14px; box-shadow: 0 12px 32px rgba(0,0,0,0.14); overflow: hidden;
}
.popover-header { display: flex; align-items: center; gap: 12px; padding: 16px; background: linear-gradient(135deg, #eef3ee 0%, #f7f9f7 100%); }
.popover-avatar { width: 42px; height: 42px; border-radius: 50%; background: #00382a; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem; flex-shrink: 0; }
.popover-name { font-weight: 700; color: #1a3a1a; font-size: 0.88rem; margin: 0; }
.popover-role { font-size: 0.76rem; color: #8a9a8a; margin: 2px 0 0; }
.popover-divider { border-top: 1px solid #eceeec; }
.popover-item {
  display: flex; align-items: center; gap: 10px; width: 100%; text-align: left; border: none; background: none;
  padding: 13px 16px; font-size: 0.85rem; font-weight: 600; color: #2a2a2a; cursor: pointer; text-decoration: none; font-family: inherit;
}
.popover-item:hover { background: #f7f9f7; }
.popover-item-danger { color: #c0392b; }
.icon-dot { position: absolute; top: 7px; right: 7px; width: 7px; height: 7px; border-radius: 50%; background: #D4A017; }

.content { flex: 1; overflow-y: auto; padding: 24px 60px 32px; }

@media print {
  .sidebar, .topbar { display: none; }
  .main-column { height: auto; overflow: visible; }
  .content { overflow: visible; padding: 0; }
}
</style>