<script setup>
import { rnds, clients, adminProfile } from '~/mock/mockAdminDatabase'

const route = useRoute()
const profile = adminProfile

const pendingCount = computed(() => rnds.value.filter(r => r.status === 'pending').length)
const flaggedCount = computed(() => clients.value.filter(c => c.status === 'Flagged').length)

const nav = computed(() => [
  {
    section: 'OVERVIEW',
    items: [
      { label: 'Dashboard', to: '/admin-dashboard', icon: 'grid' }
    ]
  },
  {
    section: 'PLATFORM OPERATIONS',
    items: [
      { label: 'RND Verification', to: '/rnd-verification', icon: 'shield', badge: pendingCount.value },
      { label: 'Client Management', to: '/client-management', icon: 'users' },
      { label: 'Billing & Commission', to: '/billing-commission', icon: 'card' }
    ]
  },
  {
    section: 'GOVERNANCE',
    items: [
      { label: 'Audit Logs', to: '/audit-logs', icon: 'file' },
      { label: 'Platform Reports', to: '/platform-reports', icon: 'trending' },
      { label: 'System Settings', to: '/system-settings', icon: 'gear' }
    ]
  }
])

const isActive = (to) => route.path === to

async function handleSignOut() {
  localStorage.removeItem('nutrimatch_admin_session')
  await navigateTo('/login')
}
</script>

<template>
  <aside class="w-[230px] shrink-0 bg-forest text-cream/90 flex flex-col h-screen sticky top-0">
    <div class="px-5 pt-6 pb-5">
      <div class="flex items-center gap-2">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="w-7 h-7 object-contain shrink-0" />
        <span class="font-serif text-[19px] leading-none">
          <span class="text-cream">Nutri</span><span class="text-[#EFBF04]">Match</span>
        </span>
      </div>
      <p class="text-[9.5px] tracking-[0.18em] text-cream/40 mt-1.5">CLINICAL NUTRITION SYSTEM</p>
      <span class="inline-flex items-center gap-1.5 mt-3 text-[10.5px] font-semibold text-[#EFBF04] border border-[#EFBF04]/40 rounded-full px-2.5 py-1">
        <span class="w-1.5 h-1.5 rounded-full bg-[#EFBF04]"></span> ADMIN PORTAL
      </span>
    </div>

    <nav class="flex-1 overflow-y-auto scrollbar-thin px-3 pb-4">
      <div v-for="group in nav" :key="group.section" class="mb-6">
        <p class="text-[10px] tracking-[0.15em] text-cream/30 px-3 mb-2">{{ group.section }}</p>
        <NuxtLink
          v-for="item in group.items"
          :key="item.to"
          :to="item.to"
          class="group relative flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg text-[13.5px] mb-1 transition-all duration-200 ease-out"
          :class="isActive(item.to)
            ? 'bg-forest-light text-white font-medium'
            : 'text-cream/65 hover:bg-forest-light/60 hover:text-white hover:font-medium hover:translate-x-0.5 hover:shadow-sm'"
        >
        
          <span
            class="nav-indicator absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-gold-light transition-all duration-200"
            :class="isActive(item.to)
              ? 'opacity-100 scale-y-100'
              : 'opacity-0 scale-y-0 group-hover:opacity-60 group-hover:scale-y-100'"
          ></span>
          <span class="flex items-center gap-2.5">
            <NavIcon
              :name="item.icon"
              class="w-4 h-4 shrink-0 transition-transform duration-200 group-hover:scale-110"
              :class="isActive(item.to) ? 'text-gold-light' : 'group-hover:text-gold-light/90'"
            />
            {{ item.label }}
          </span>
          <span v-if="item.badge" class="bg-gold-light text-forest-dark text-[11px] font-bold rounded-full w-5 h-5 flex items-center justify-center animate-pop">
            {{ item.badge }}
          </span>
        </NuxtLink>
      </div>
    </nav>

    <div class="border-t border-white/10 px-4 py-3.5">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-full bg-gold-light text-forest-dark flex items-center justify-center text-xs font-bold shrink-0">
          {{ profile.footerName.split(' ').map(n => n[0]).slice(0,2).join('') }}
        </div>
        <div class="leading-tight min-w-0">
          <p class="text-[13.5px] text-white truncate">{{ profile.footerName }}</p>
          <p class="text-[11px] text-cream/40">{{ profile.footerRole }}</p>
        </div>
      </div>
      <button
        @click="handleSignOut"
        class="group flex items-center gap-2 text-[13px] text-cream/50 hover:text-white mt-3.5 transition-colors"
      >
        <NavIcon name="logout" class="w-4 h-4 transition-transform duration-200 group-hover:translate-x-0.5" /> Sign Out
      </button>
    </div>
  </aside>
</template>