<script setup>
const { get, patch } = useApi()

const open = ref(false)
const notifications = ref([])
const isLoading = ref(true)

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

async function loadNotifications({ quiet = false } = {}) {
  if (!quiet) isLoading.value = true
  try {
    notifications.value = await get('/notifications/')
  } catch {
    if (!quiet) notifications.value = []
  } finally {
    isLoading.value = false
  }
}

async function markAllRead() {
  try {
    await patch('/notifications/mark-all-read/')
    notifications.value = notifications.value.map(n => ({ ...n, is_read: true }))
  } catch {
    // leave state as-is on failure
  }
}

function timeAgo(iso) {
  const seconds = Math.floor((Date.now() - new Date(iso)) / 1000)
  const units = [['year', 31536000], ['month', 2592000], ['day', 86400], ['hour', 3600], ['minute', 60]]
  for (const [label, secs] of units) {
    const value = Math.floor(seconds / secs)
    if (value >= 1) return `${value} ${label}${value > 1 ? 's' : ''} ago`
  }
  return 'just now'
}

const close = () => { open.value = false }

// On phones the panel is pinned to the screen (full width minus a gutter)
// just below the bell, instead of hanging off the bell and running off the
// left edge — see .notif-panel below.
const bellEl = ref(null)
const panelTop = ref(64)
function toggle() {
  if (!open.value && bellEl.value) panelTop.value = Math.round(bellEl.value.getBoundingClientRect().bottom + 8)
  open.value = !open.value
}

async function markRead(n) {
  if (n.is_read) return
  n.is_read = true
  try {
    await patch(`/notifications/${n.id}/read/`)
  } catch {
    n.is_read = false
  }
}

// Clicking a notification opens its full detail (NotificationDetailModal).
// "Meal log update" notifications carry the log itself (RND only) — those
// open the log with the photo and what was planned instead.
const openMealLog = ref(null)
const openDetail = ref(null)
function openNotification(n) {
  markRead(n)
  if (n.meal_log) openMealLog.value = n.meal_log
  else openDetail.value = n
  close()
}
const STATUS_CLASS = {
  followed: 'bg-emerald-50 text-emerald-700',
  partially_followed: 'bg-amber-50 text-amber-700',
  not_followed: 'bg-red-50 text-red-600',
  null: 'bg-gray-100 text-gray-600',
}

onMounted(loadNotifications)

// New notifications arrive live (ws/notifications/); a reconnect re-syncs,
// and only while the live connection is down does the list refresh itself.
const live = useLiveUpdates()
live.onLive('notification', ({ notification }) => {
  if (!notifications.value.some(n => n.id === notification.id)) notifications.value = [notification, ...notifications.value]
})
live.onLive('reconnect', loadNotifications)
let fallbackTimer = null
onMounted(() => {
  fallbackTimer = setInterval(() => {
    if (!live.connected.value && document.visibilityState === 'visible') loadNotifications({ quiet: true })
  }, 30000)
})
onUnmounted(() => clearInterval(fallbackTimer))
</script>

<template>
  <div class="relative" v-click-outside="close">
    <button
      ref="bellEl"
      class="btn-press w-10 h-10 rounded-lg border border-forest/15 flex items-center justify-center relative hover:bg-forest/5"
      aria-label="Notifications"
      @click="toggle"
    >
      <NavIcon name="bell" class="w-5 h-5 text-forest transition-transform" :class="open ? 'rotate-12' : ''" />
      <span v-if="unreadCount" class="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-gold border-2 border-cream animate-pop"></span>
    </button>

    <Transition name="dropdown">
      <div
        v-if="open"
        class="notif-panel absolute right-0 mt-2 w-96 bg-white rounded-xl shadow-2xl border border-forest/10 z-50 overflow-hidden origin-top-right"
        :style="{ '--panel-top': `${panelTop}px` }"
      >
        <div class="flex items-center justify-between px-5 py-4 border-b border-forest/10">
          <p class="font-display text-lg text-forest whitespace-nowrap">
            Notifications <span class="text-sm font-sans bg-forest text-white rounded-full px-2 py-0.5 ml-1">{{ unreadCount }}</span>
          </p>
          <button class="text-xs text-forest/60 hover:text-forest transition-colors whitespace-nowrap" @click="markAllRead">Mark all read</button>
        </div>

        <div v-if="isLoading" class="px-5 py-8 text-center text-sm text-forest/40">Loading…</div>

        <div v-else-if="!notifications.length" class="px-5 py-8 text-center text-sm text-forest/50">
          No notifications yet. Updates about consultations, payments and your care show up here.
        </div>

        <TransitionGroup v-else name="list" tag="div" class="notif-list max-h-80 overflow-y-auto scrollbar-thin relative">
          <div
            v-for="n in notifications"
            :key="n.id"
            class="flex items-start gap-3 px-5 py-3 hover:bg-cream-soft transition-colors border-b border-forest/5 last:border-0 cursor-pointer"
            role="button" tabindex="0"
            @click="openNotification(n)" @keydown.enter="openNotification(n)"
          >
            <!-- meal log: photo thumbnail -->
            <img v-if="n.meal_log?.photo_url" :src="n.meal_log.photo_url" alt="" class="w-12 h-12 rounded-lg object-cover border border-forest/10 shrink-0" />
            <div v-else-if="n.meal_log" class="w-12 h-12 rounded-lg bg-cream-soft border border-forest/10 shrink-0 flex items-center justify-center text-[10px] text-forest/40">No photo</div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-forest-dark font-medium">{{ n.subject }}</p>
              <p class="text-xs text-forest/60">{{ n.content }}</p>
              <p v-if="n.meal_log" class="mt-1 flex items-center gap-2">
                <span class="text-[11px] font-semibold rounded-full px-2 py-0.5" :class="STATUS_CLASS[n.meal_log.status]">{{ n.meal_log.status_label }}</span>
                <span class="text-[11px] font-semibold text-emerald-700">View log</span>
              </p>
              <p class="text-xs text-forest/50 mt-0.5">{{ timeAgo(n.created_at) }}</p>
            </div>
            <span v-if="!n.is_read" class="w-2 h-2 rounded-full bg-emerald-700 mt-1.5 shrink-0"></span>
          </div>
        </TransitionGroup>
      </div>
    </Transition>

    <MealLogPopup v-if="openMealLog" :meal-log-id="openMealLog.id" :initial="openMealLog" @close="openMealLog = null" />
    <NotificationDetailModal v-if="openDetail" :notification="openDetail" @close="openDetail = null" />
  </div>
</template>

<style scoped>
/* the app's green-tinted shadow instead of a grey one */
.notif-panel { box-shadow: 0 0 2px rgba(0, 77, 58, 0.1), 0 12px 32px -8px rgba(0, 77, 58, 0.28); }
@media (max-width: 639px) {
  .notif-panel {
    position: fixed;
    top: var(--panel-top, 64px);
    left: 12px;
    right: 12px;
    width: auto;
    margin-top: 0;
    transform-origin: top center;
  }
  .notif-panel .notif-list { max-height: calc(100dvh - var(--panel-top, 64px) - 90px); }
}
</style>
