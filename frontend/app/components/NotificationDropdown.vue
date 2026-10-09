<script setup>
const { get, patch } = useApi()

const open = ref(false)
const notifications = ref([])
const isLoading = ref(true)

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

async function loadNotifications() {
  isLoading.value = true
  try {
    notifications.value = await get('/notifications/')
  } catch {
    notifications.value = []
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

async function markRead(n) {
  if (n.is_read) return
  n.is_read = true
  try {
    await patch(`/notifications/${n.id}/read/`)
  } catch {
    n.is_read = false
  }
}

// "Meal log update" notifications carry the log itself (RND only) —
// clicking one opens it with the photo and what was planned.
const openMealLog = ref(null)
function openNotification(n) {
  markRead(n)
  if (n.meal_log) {
    openMealLog.value = n.meal_log
    close()
  }
}
const STATUS_CLASS = {
  followed: 'bg-emerald-50 text-emerald-700',
  partially_followed: 'bg-amber-50 text-amber-700',
  not_followed: 'bg-red-50 text-red-600',
}

onMounted(loadNotifications)
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

        <div v-if="isLoading" class="px-5 py-8 text-center text-sm text-forest/40">Loading…</div>

        <div v-else-if="!notifications.length" class="px-5 py-8 text-center text-sm text-forest/40">
          No notifications yet.
        </div>

        <TransitionGroup v-else name="list" tag="div" class="max-h-80 overflow-y-auto scrollbar-thin relative">
          <div
            v-for="n in notifications"
            :key="n.id"
            class="flex items-start gap-3 px-5 py-3 hover:bg-cream-soft transition-colors border-b border-forest/5 last:border-0"
            :class="n.meal_log ? 'cursor-pointer' : ''"
            @click="openNotification(n)"
          >
            <!-- meal log: photo thumbnail -->
            <img v-if="n.meal_log?.photo_url" :src="n.meal_log.photo_url" alt="" class="w-12 h-12 rounded-lg object-cover border border-forest/10 shrink-0" />
            <div v-else-if="n.meal_log" class="w-12 h-12 rounded-lg bg-cream-soft border border-forest/10 shrink-0 flex items-center justify-center text-[10px] text-forest/40">No photo</div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-forest-dark font-medium">{{ n.subject }}</p>
              <p class="text-xs text-forest/60">{{ n.content }}</p>
              <p v-if="n.meal_log" class="mt-1 flex items-center gap-2">
                <span class="text-[11px] font-semibold rounded-full px-2 py-0.5" :class="STATUS_CLASS[n.meal_log.status]">{{ n.meal_log.status_label }}</span>
                <span class="text-[11px] font-semibold text-emerald-700">View log →</span>
              </p>
              <p class="text-xs text-forest/50 mt-0.5">{{ timeAgo(n.created_at) }}</p>
            </div>
            <span v-if="!n.is_read" class="w-2 h-2 rounded-full bg-emerald-700 mt-1.5 shrink-0"></span>
          </div>
        </TransitionGroup>
      </div>
    </Transition>

    <MealLogPopup v-if="openMealLog" :meal-log-id="openMealLog.id" :initial="openMealLog" @close="openMealLog = null" />
  </div>
</template>
