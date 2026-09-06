<script setup>
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const open = ref(false)
const close = () => { open.value = false }

const initials = computed(() => {
  const u = auth.user
  if (!u) return '?'
  return `${u.first_name?.[0] || ''}${u.last_name?.[0] || ''}`.toUpperCase()
})

async function handleSignOut() {
  auth.logout()
  await navigateTo('/login')
}
</script>

<template>
  <div class="relative" v-click-outside="close">
    <button
      class="btn-press w-9 h-9 rounded-lg border border-forest/15 flex items-center justify-center hover:bg-forest/5 hover:scale-105"
      @click="open = !open"
    >
      <NavIcon name="user" class="w-4 h-4 text-forest" />
    </button>

    <Transition name="dropdown">
      <div
        v-if="open"
        class="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-2xl border border-forest/10 z-50 overflow-hidden origin-top-right"
      >
        <div class="flex items-center gap-3 px-4 py-4 border-b border-forest/10">
          <div class="w-9 h-9 rounded-full bg-forest text-white flex items-center justify-center text-xs font-bold shrink-0">
            {{ initials }}
          </div>
          <div>
            <p class="text-sm font-semibold text-forest-dark leading-tight">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</p>
            <p class="text-xs text-forest/60 leading-tight">System Administrator</p>
            <p class="text-[11px] text-forest/40">{{ auth.user?.email }}</p>
          </div>
        </div>
        <NuxtLink to="/system-settings" class="flex items-center gap-2 px-4 py-3 text-sm text-forest-dark hover:bg-cream-soft transition-colors" @click="close">
          <NavIcon name="gear" class="w-4 h-4" /> Settings
        </NuxtLink>
        <button class="flex items-center gap-2 px-4 py-3 text-sm text-red-600 hover:bg-red-50 transition-colors w-full text-left" @click="handleSignOut">
          <NavIcon name="logout" class="w-4 h-4" /> Sign Out
        </button>
      </div>
    </Transition>
  </div>
</template>
