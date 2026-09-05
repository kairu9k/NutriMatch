<script setup>
const route = useRoute()

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
  <div class="flex h-screen overflow-hidden bg-cream text-forest-dark">
    <AdminSidebar />
    <div class="flex-1 min-w-0 h-screen overflow-y-auto">
      <header class="flex items-center justify-between px-8 py-5 sticky top-0 z-20 bg-cream/95 backdrop-blur-sm">
        <div>
          <h1 class="font-display text-2xl text-forest-dark">{{ pageMeta.title }}</h1>
          <p class="text-sm text-forest/50">{{ pageMeta.subtitle || today }}</p>
        </div>
        <div class="flex items-center gap-3">
          <NotificationDropdown />
          <ProfileDropdown />
        </div>
      </header>
      <main class="px-8 pb-10">
        <slot />
      </main>
    </div>
  </div>
</template>