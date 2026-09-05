<script setup>
import { Menu } from 'lucide-vue-next'

const route = useRoute()
const isSidebarOpen = ref(false)

watch(() => route.path, () => { isSidebarOpen.value = false })

const pageMeta = computed(() => {
  const map = {
    '/admin-dashboard': { title: 'Dashboard', subtitle: '' },
    '/rnd-verification': { title: 'RND Verification', subtitle: 'Review PRC credentials and manage practitioner status' },
    '/client-management': { title: 'Client Management', subtitle: 'Monitor client accounts and resolve flags' },
    '/billing-commission': { title: 'Billing & Commission', subtitle: 'Platform revenue, payouts, and commission settings' },
    '/audit-logs': { title: 'Audit Logs', subtitle: 'RA 10173-compliant activity trail' },
    '/platform-reports': { title: 'Platform Reports', subtitle: 'Performance analytics and custom exports' },
    '/system-settings': { title: 'System Setting', subtitle: 'Platform configuration and compliance controls' }
  }
  return map[route.path] || { title: 'Dashboard', subtitle: '' }
})

const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
</script>

<template>
  <div class="flex flex-col lg:flex-row min-h-screen lg:h-screen lg:overflow-hidden bg-cream text-forest-dark">
    <div
      v-if="isSidebarOpen"
      class="fixed inset-0 bg-black/40 z-30 lg:hidden"
      @click="isSidebarOpen = false"
    ></div>

    <AdminSidebar :open="isSidebarOpen" @close="isSidebarOpen = false" />

    <div class="flex-1 min-w-0 lg:h-screen lg:overflow-y-auto">
      <header class="flex items-center justify-between px-4 lg:px-8 py-4 lg:py-5 sticky top-0 z-20 bg-cream/95 backdrop-blur-sm">
        <div class="flex items-center gap-3 min-w-0">
          <button
            type="button"
            class="lg:hidden shrink-0 text-forest-dark"
            aria-label="Toggle menu"
            @click="isSidebarOpen = !isSidebarOpen"
          >
            <Menu :size="22" />
          </button>
          <div class="min-w-0">
            <h1 class="font-display text-xl lg:text-2xl text-forest-dark truncate">{{ pageMeta.title }}</h1>
            <p class="text-sm text-forest/50 hidden sm:block">{{ pageMeta.subtitle || today }}</p>
          </div>
        </div>
        <div class="flex items-center gap-3 shrink-0">
          <NotificationDropdown />
          <ProfileDropdown />
        </div>
      </header>
      <main class="px-4 lg:px-8 pb-10">
        <slot />
      </main>
    </div>
  </div>
</template>