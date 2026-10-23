<template>
  <div class="notifications-page">
    <div class="page-header">
      <div>
        <p class="page-sub">Updates about your consultations, payments and care.</p>
      </div>
      <button v-if="unreadCount > 0" class="mark-all-btn" type="button" :disabled="isMarkingAll" @click="markAllRead">
        {{ isMarkingAll ? 'Marking…' : 'Mark all as read' }}
      </button>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <div v-else-if="notifications.length" class="surface">
      <template v-for="g in groups" :key="g.label">
      <h2 class="day-label">{{ g.label }}</h2>
      <div
        v-for="n in g.items"
        :key="n.id"
        class="notif-item clickable"
        :class="{ unread: !n.is_read }"
        role="button" tabindex="0"
        @click="openNotification(n)" @keydown.enter="openNotification(n)"
      >
        <img v-if="n.meal_log?.photo_url" :src="n.meal_log.photo_url" alt="" class="notif-photo" />
        <div v-else class="notif-icon" :class="iconClass(n.notifiable_type)">
          <component :is="iconFor(n.notifiable_type)" :size="18" aria-hidden="true" />
        </div>
        <div class="notif-body">
          <p class="notif-subject"><span v-if="!n.is_read" class="unread-dot" aria-label="Unread" />{{ n.subject }}</p>
          <p v-if="n.content" class="notif-text">{{ n.content }}</p>
          <p v-if="n.meal_log" class="notif-log-row">
            <span class="notif-log-status" :class="`log-${n.meal_log.status}`">{{ n.meal_log.status_label }}</span>
            <span class="notif-log-link">View log</span>
          </p>
          <span class="notif-time" :title="new Date(n.created_at).toLocaleString('en-PH', { dateStyle: 'medium', timeStyle: 'short' })">{{ timeAgo(n.created_at) }}</span>
        </div>
      </div>
      </template>
    </div>

    <div v-else class="empty-state">
      <p class="empty-title">No notifications yet</p>
      <p class="empty-desc">Updates about your consultations, payments and care show up here.</p>
    </div>

    <MealLogPopup v-if="openMealLog" :meal-log-id="openMealLog.id" :initial="openMealLog" @close="openMealLog = null" />
    <NotificationDetailModal v-if="openDetail" :notification="openDetail" @close="openDetail = null" />
  </div>
</template>

<script setup>
import { AlarmClock, Bell, BookOpen, CalendarCheck, FlaskConical, Headset, HeartHandshake, MessageSquare, Receipt, Utensils, Wallet } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Notifications' })

const { get, patch } = useApi()

const isLoading = ref(true)
const isMarkingAll = ref(false)
const errorMessage = ref('')
const notifications = ref([])

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

// Same icons as the notification pop-up.
const ICONS = { appointment: CalendarCheck, invoice: Receipt, message: MessageSquare, meal_plan: Utensils, meal_log: Utensils, payout: Wallet, resource: BookOpen, reminder: AlarmClock, relationship: HeartHandshake, support: Headset, lab_request: FlaskConical, lab_result: FlaskConical }
function iconFor(type) {
  return ICONS[type] || Bell
}
// Green for everything; payments gold (a notice), so they stand out.
function iconClass(type) {
  return type === 'invoice' ? 'gold' : 'green'
}
// Grouped by Philippine day: Today, Yesterday, then the date.
const groups = computed(() => {
  const day = iso => new Date(iso).toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' })
  const today = day(new Date())
  const yesterday = day(new Date(Date.now() - 86400000))
  const out = []
  for (const n of notifications.value) {
    const d = day(n.created_at)
    const label = d === today ? 'Today' : d === yesterday ? 'Yesterday'
      : new Date(n.created_at).toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' })
    if (out.at(-1)?.label !== label) out.push({ label, items: [] })
    out.at(-1).items.push(n)
  }
  return out
})

function timeAgo(iso) {
  const seconds = Math.floor((Date.now() - new Date(iso)) / 1000)
  const units = [
    ['year', 31536000], ['month', 2592000], ['day', 86400],
    ['hour', 3600], ['minute', 60],
  ]
  for (const [label, secs] of units) {
    const value = Math.floor(seconds / secs)
    if (value >= 1) return `${value} ${label}${value > 1 ? 's' : ''} ago`
  }
  return 'just now'
}

async function loadNotifications() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    notifications.value = await get('/notifications/')
  } catch {
    errorMessage.value = 'Could not load your notifications. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

// Clicking a notification opens its full detail (NotificationDetailModal).
// "Meal log update" notifications carry the log itself (RND only) — those
// open the log with the photo and what was planned instead.
const openMealLog = ref(null)
const openDetail = ref(null)
function openNotification(n) {
  if (!n.is_read) markRead(n)
  if (n.meal_log) openMealLog.value = n.meal_log
  else openDetail.value = n
}

async function markRead(n) {
  try {
    await patch(`/notifications/${n.id}/read/`)
    n.is_read = true
  } catch {
    // non-critical, leave as unread on failure
  }
}

async function markAllRead() {
  isMarkingAll.value = true
  try {
    await patch('/notifications/mark-all-read/')
    notifications.value.forEach(n => { n.is_read = true })
  } catch {
    errorMessage.value = 'Could not mark notifications as read. Please try again.'
  } finally {
    isMarkingAll.value = false
  }
}

onMounted(loadNotifications)

// New ones appear live at the top (ws/notifications/); a reconnect re-syncs.
const live = useLiveUpdates()
live.onLive('notification', ({ notification }) => {
  if (!notifications.value.some(n => n.id === notification.id)) notifications.value = [notification, ...notifications.value]
})
live.onLive('reconnect', loadNotifications)
</script>

<style scoped>
* { box-sizing: border-box; }

.notifications-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.mark-all-btn {
  border: none; background: #e3efe7; color: #0a4a37; border-radius: 8px; font-family: inherit;
  padding: 0 16px; min-height: 36px; font-size: 0.82rem; font-weight: 600; cursor: pointer; white-space: nowrap;
}
.mark-all-btn:hover:not(:disabled) { background: #d3e7da; }
.mark-all-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.surface { background: #fff; border-radius: 12px; border: 1px solid #d9e3dc; overflow: hidden; }
.day-label { font-family: 'Inter', sans-serif; margin: 0; padding: 14px 20px 6px; font-size: 0.82rem; font-weight: 600; color: #4a5a4a; border-top: 1px solid #d9e3dc; }
.day-label:first-child { border-top: none; }
.unread-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #D4A017; margin-right: 8px; vertical-align: middle; }

.notif-item {
  display: flex; gap: 14px; padding: 12px 20px 14px; cursor: default;
}
.notif-item + .notif-item { border-top: 1px solid #edf2ee; }
.notif-item:hover { background: #f7faf8; }
.notif-item:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.notif-item:not(.unread) .notif-subject { font-weight: 600; color: #2a3a2a; }

.notif-icon {
  width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.notif-icon.green { background: #e3efe7; color: #0a4a37; }
.notif-icon.gold { background: #fbf3dc; color: #a37a0b; }

.notif-body { flex: 1; }
.notif-item.clickable { cursor: pointer; }
.notif-photo { width: 48px; height: 48px; border-radius: 10px; object-fit: cover; border: 1px solid #e5e8e5; flex-shrink: 0; }
.notif-log-row { display: flex; align-items: center; gap: 10px; margin: 2px 0 4px; }
.notif-log-status { font-size: 0.72rem; font-weight: 700; padding: 2px 10px; border-radius: 12px; }
.log-followed { background: #e3f3ea; color: #1f8f5c; }
.log-partially_followed { background: #fdf1d6; color: #b8860b; }
.log-null { background: #eceeec; color: #5a6a5a; }
.log-not_followed { background: #fbe1de; color: #c0483a; }
.notif-log-link { display: inline-flex; align-items: center; min-height: 28px; padding: 0 10px; border-radius: 8px; background: #e3efe7; font-size: 0.76rem; font-weight: 600; color: #0a4a37; }
.notif-subject { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0 0 2px; }
.notif-text { font-size: 0.86rem; color: #4a5a4a; margin: 0 0 4px; line-height: 1.5; }
.surface { box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.notif-time { font-size: 0.76rem; color: #6a7a6a; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #d9e3dc;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
</style>
