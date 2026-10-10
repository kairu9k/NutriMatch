<template>
  <div class="notifications-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Notifications</h1>
        <p class="page-sub">Stay up to date on appointments, messages, and invoices.</p>
      </div>
      <button v-if="unreadCount > 0" class="mark-all-btn" type="button" :disabled="isMarkingAll" @click="markAllRead">
        {{ isMarkingAll ? 'Marking…' : 'Mark All as Read' }}
      </button>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <div v-else-if="notifications.length" class="surface">
      <div
        v-for="n in notifications"
        :key="n.id"
        class="notif-item clickable"
        :class="{ unread: !n.is_read }"
        role="button" tabindex="0"
        @click="openNotification(n)" @keydown.enter="openNotification(n)"
      >
        <img v-if="n.meal_log?.photo_url" :src="n.meal_log.photo_url" alt="" class="notif-photo" />
        <div v-else class="notif-icon" :class="iconClass(n.notifiable_type)">
          <component :is="iconFor(n.notifiable_type)" :size="18" />
        </div>
        <div class="notif-body">
          <p class="notif-text"><strong>{{ n.subject }}</strong> — {{ n.content }}</p>
          <p v-if="n.meal_log" class="notif-log-row">
            <span class="notif-log-status" :class="`log-${n.meal_log.status}`">{{ n.meal_log.status_label }}</span>
            <span class="notif-log-link">View log →</span>
          </p>
          <span class="notif-time">{{ timeAgo(n.created_at) }}</span>
        </div>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon"><Bell :size="28" /></div>
      <p class="empty-title">No notifications yet</p>
      <p class="empty-desc">You'll see updates here about appointments, messages, and invoices.</p>
    </div>

    <MealLogPopup v-if="openMealLog" :meal-log-id="openMealLog.id" :initial="openMealLog" @close="openMealLog = null" />
    <NotificationDetailModal v-if="openDetail" :notification="openDetail" @close="openDetail = null" />
  </div>
</template>

<script setup>
import { Bell, CalendarCheck, MessageSquare, Receipt, Utensils } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Notifications' })

const { get, patch } = useApi()

const isLoading = ref(true)
const isMarkingAll = ref(false)
const errorMessage = ref('')
const notifications = ref([])

const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

const ICONS = { appointment: CalendarCheck, message: MessageSquare, invoice: Receipt, meal_log: Utensils }
function iconFor(type) {
  return ICONS[type] || Bell
}
function iconClass(type) {
  return { appointment: 'gold', message: 'info', invoice: 'warning' }[type] || 'neutral'
}

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
</script>

<style scoped>
* { box-sizing: border-box; }

.notifications-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.mark-all-btn {
  border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px;
  padding: 9px 16px; font-size: 0.83rem; font-weight: 600; cursor: pointer; white-space: nowrap;
}
.mark-all-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; overflow: hidden; }

.notif-item {
  display: flex; gap: 14px; padding: 16px 20px; border-bottom: 1px solid #f0f0e6; cursor: default;
}
.notif-item:last-child { border-bottom: none; }
.notif-item.unread { background: #eef3ec; cursor: pointer; }

.notif-icon {
  width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.notif-icon.gold { background: rgba(212,160,23,0.16); color: #b8860b; }
.notif-icon.info { background: #e3edf7; color: #2f6fa8; }
.notif-icon.warning { background: #faead0; color: #b8860b; }
.notif-icon.neutral { background: #eceeec; color: #7a8a7a; }

.notif-body { flex: 1; }
.notif-item.clickable { cursor: pointer; }
.notif-photo { width: 48px; height: 48px; border-radius: 10px; object-fit: cover; border: 1px solid #e5e8e5; flex-shrink: 0; }
.notif-log-row { display: flex; align-items: center; gap: 10px; margin: 2px 0 4px; }
.notif-log-status { font-size: 0.72rem; font-weight: 700; padding: 2px 10px; border-radius: 12px; }
.log-followed { background: #e3f3ea; color: #1f8f5c; }
.log-partially_followed { background: #fdf1d6; color: #b8860b; }
.log-not_followed { background: #fbe1de; color: #c0483a; }
.notif-log-link { font-size: 0.76rem; font-weight: 700; color: #1f8f5c; }
.notif-text { font-size: 0.88rem; color: #2a3a2a; margin: 0 0 4px; line-height: 1.5; }
.notif-time { font-size: 0.74rem; color: #9aaa9a; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
</style>
