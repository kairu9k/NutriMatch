<script setup>
import { notifications } from '~/mock/mockAdminDatabase'

const open = ref(false)
const unreadCount = computed(() => notifications.value.filter(n => n.unread).length)

const markAllRead = () => {
  notifications.value = notifications.value.map(n => ({ ...n, unread: false }))
}

const close = () => { open.value = false }
</script>

<template>
  <div class="relative" v-click-outside="close">
    <button
      class="btn-press w-9 h-9 rounded-lg border border-forest/15 flex items-center justify-center relative hover:bg-forest/5 hover:scale-105"
      @click="open = !open"
    >
      <NavIcon name="bell" class="w-4 h-4 text-forest transition-transform" :class="open ? 'rotate-12' : ''" />
      <span v-if="unreadCount" class="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-gold border-2 border-cream animate-pop"></span>
    </button>

    <Transition name="dropdown">
      <div
        v-if="open"
        class="absolute right-0 mt-2 w-96 bg-white rounded-xl shadow-2xl border border-forest/10 z-50 overflow-hidden origin-top-right"
      >
        <div class="flex items-center justify-between px-5 py-4 border-b border-forest/10">
          <p class="font-display text-lg text-forest">
            Notifications <span class="text-sm font-sans bg-forest text-white rounded-full px-2 py-0.5 ml-1">{{ unreadCount }}</span>
          </p>
          <button class="text-xs text-forest/60 hover:text-forest transition-colors" @click="markAllRead">Mark all read</button>
        </div>
        <TransitionGroup name="list" tag="div" class="max-h-80 overflow-y-auto scrollbar-thin relative">
          <div
            v-for="n in notifications"
            :key="n.id"
            class="flex items-start gap-3 px-5 py-3 hover:bg-cream-soft transition-colors border-b border-forest/5 last:border-0"
          >
            <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0', n.color]">
              {{ n.initials }}
            </div>
            <div class="flex-1">
              <p class="text-sm text-forest-dark" v-html="n.text.replace(/^(\S+ \S+\.? ?\S*)/, '<b>$1</b>')"></p>
              <p class="text-xs text-forest/50 mt-0.5">{{ n.time }}</p>
            </div>
            <span v-if="n.unread" class="w-2 h-2 rounded-full bg-emerald-700 mt-1.5 shrink-0"></span>
          </div>
        </TransitionGroup>
        <div class="px-5 py-3 border-t border-forest/10">
          <button class="text-sm font-medium text-forest hover:underline">View all →</button>
        </div>
      </div>
    </Transition>
  </div>
</template>
