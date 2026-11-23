<template>
  <div class="notifications-page">
    <section class="nx-hero">
      <img class="nx-plate" :src="NX_PLATE" alt="" aria-hidden="true" />
      <span class="nx-fade" aria-hidden="true"></span>
      <div class="nx-text">
        <p class="nx-eb"><span aria-hidden="true"></span>Notifications</p>
        <h1 class="nx-title">Stay on top of <em>your care.</em></h1>
        <p class="page-sub nx-sub">Updates about your consultations, payments, reminders and meal plan.</p>
      </div>
      <div class="nx-side">
        <p><b>{{ unreadCount }}</b> unread</p>
        <button v-if="unreadCount > 0" class="mark-all-btn nx-mark" type="button" :disabled="isMarkingAll" @click="markAllRead">
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>{{ isMarkingAll ? 'Marking…' : 'Mark all as read' }}
        </button>
      </div>
    </section>

    <div v-if="!isLoading && notifications.length" class="nx-pills" role="tablist" aria-label="Filter notifications">
      <button v-for="f in NX_FILTERS" :key="f.key" type="button" role="tab" :aria-selected="nxFilter === f.key" :class="{ on: nxFilter === f.key }" @click="nxFilter = f.key">
        {{ f.label }}<i v-if="nxCount(f.key)">{{ nxCount(f.key) }}</i>
      </button>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <div v-else-if="notifications.length" class="nx-list">
      <p v-if="!nxGroups.length" class="nx-none">Nothing here on this page. Try another filter.</p>
      <section v-for="g in nxGroups" :key="g.label" class="nx-day">
        <h2 class="day-label nx-dh"><b>{{ g.label }}</b><span v-if="g.sub">{{ g.sub }}</span><em v-if="g.unread">{{ g.unread }} new</em></h2>
        <div class="nx-items">
          <div
            v-for="n in g.items"
            :key="n.id"
            class="notif-item clickable nx-item"
            :class="{ unread: !n.is_read }"
            role="link" tabindex="0" :aria-busy="opening === n.id"
            @click="openNotification(n)" @keydown.enter="openNotification(n)"
          >
            <img v-if="n.meal_log?.photo_url" :src="n.meal_log.photo_url" alt="" class="notif-photo nx-ic" />
            <div v-else class="notif-icon nx-ic" :class="nxKind(n.notifiable_type).tone">
              <component :is="iconFor(n.notifiable_type)" :size="18" aria-hidden="true" />
            </div>
            <div class="notif-body">
              <p class="nx-top">
                <span class="nx-lab" :class="nxKind(n.notifiable_type).tone">{{ nxKind(n.notifiable_type).label }}</span>
                <span class="notif-time" :title="new Date(n.created_at).toLocaleString('en-PH', { dateStyle: 'medium', timeStyle: 'short' })">{{ opening === n.id ? 'Opening…' : timeAgo(n.created_at) }}</span>
              </p>
              <p class="notif-subject">{{ n.subject }}</p>
              <p v-if="n.content" class="notif-text">{{ n.content }}</p>
              <p v-if="n.meal_log" class="notif-log-row">
                <span class="notif-log-status" :class="`log-${n.meal_log.status}`">{{ n.meal_log.status_label }}</span>
                <span class="nx-act">Open in chart<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg></span>
              </p>
              <span v-else-if="nxKind(n.notifiable_type).action" class="nx-act">{{ nxKind(n.notifiable_type).action }}<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg></span>
            </div>
            <span v-if="!n.is_read" class="nx-dot" aria-label="Unread" />
          </div>
        </div>
      </section>
    </div>
    <div v-if="!isLoading && pageCount > 1" class="pager">
      <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="page === 1" @click="goPage(page - 1)">Previous</button>
      <span class="pager-num">Page {{ page }} of {{ pageCount }}</span>
      <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="page === pageCount" @click="goPage(page + 1)">Next</button>
    </div>

    <div v-else-if="!isLoading && !notifications.length" class="empty-state">
      <p class="empty-title">No notifications yet</p>
      <p class="empty-desc">Updates about your consultations, payments and care show up here.</p>
    </div>

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
// 20 a page from the server (?page=N); unread is counted over all of them.
const page = ref(1)
const total = ref(0)
const pageSize = ref(20)
const unreadTotal = ref(0)
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const unreadCount = computed(() => unreadTotal.value)

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
    const res = await get(`/notifications/?page=${page.value}`)
    notifications.value = res.results
    total.value = res.count
    pageSize.value = res.page_size
    unreadTotal.value = res.unread
    page.value = res.page
  } catch {
    errorMessage.value = 'Could not load your notifications. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

// Clicking a notification goes straight to the page it's about (no pop-up,
// 2026-11-03, user's call — utils/notificationLink.js). With nowhere to go it
// is just marked read: the row already shows the full text.
const { opening, openNotification: goTo } = useOpenNotification()
function openNotification(n) {
  if (!n.is_read) markRead(n)
  goTo(n)
}

function goPage(n) {
  page.value = n
  loadNotifications()
  window.scrollTo({ top: 0 })
}

async function markRead(n) {
  try {
    await patch(`/notifications/${n.id}/read/`)
    n.is_read = true
    unreadTotal.value = Math.max(0, unreadTotal.value - 1)
  } catch {
    // non-critical, leave as unread on failure
  }
}

async function markAllRead() {
  isMarkingAll.value = true
  try {
    await patch('/notifications/mark-all-read/')
    notifications.value.forEach(n => { n.is_read = true })
    unreadTotal.value = 0
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
  if (notifications.value.some(n => n.id === notification.id)) return
  total.value += 1
  if (!notification.is_read) unreadTotal.value += 1
  // only the first page shows the newest ones
  if (page.value === 1) notifications.value = [notification, ...notifications.value].slice(0, pageSize.value)
})
live.onLive('reconnect', loadNotifications)

// ---- UI helpers only: banner, filter pills, coloured kinds, day cards ----
const NX_PLATE = '/landing/login-plate.webp'
const NX_KINDS = {
  appointment: { key: 'appointment', label: 'Consultation', tone: 'gold', action: 'Open appointment' },
  reminder: { key: 'reminder', label: 'Reminder', tone: 'blue', action: '' },
  meal_plan: { key: 'meal', label: 'Meal plan', tone: 'orange', action: 'View meal plan' },
  meal_log: { key: 'meal', label: 'Meal log', tone: 'orange', action: '' },
  invoice: { key: 'payment', label: 'Payment', tone: 'green', action: 'View invoice' },
  payout: { key: 'payment', label: 'Payout', tone: 'green', action: '' },
  message: { key: 'other', label: 'Message', tone: 'green', action: 'Open messages' },
  lab_request: { key: 'other', label: 'Lab', tone: 'purple', action: '' },
  lab_result: { key: 'other', label: 'Lab', tone: 'purple', action: '' },
  resource: { key: 'other', label: 'Resource', tone: 'green', action: '' },
  relationship: { key: 'other', label: 'Care', tone: 'green', action: '' },
  support: { key: 'other', label: 'Support', tone: 'green', action: '' },
}
const NX_OTHER = { key: 'other', label: 'Update', tone: 'green', action: '' }
const nxKind = type => NX_KINDS[type] || NX_OTHER
const NX_FILTERS = [
  { key: 'all', label: 'All' }, { key: 'unread', label: 'Unread' }, { key: 'appointment', label: 'Consultations' },
  { key: 'reminder', label: 'Reminders' }, { key: 'meal', label: 'Meals' }, { key: 'payment', label: 'Payments' },
]
const nxFilter = ref('all')
const nxMatch = (n, f) => f === 'all' || (f === 'unread' ? !n.is_read : nxKind(n.notifiable_type).key === f)
const nxCount = f => notifications.value.filter(n => nxMatch(n, f)).length
const nxGroups = computed(() => {
  const keep = new Set(notifications.value.filter(n => nxMatch(n, nxFilter.value)).map(n => n.id))
  return groups.value
    .map((g) => {
      const items = g.items.filter(n => keep.has(n.id))
      const first = items[0]
      const sub = first && ['Today', 'Yesterday'].includes(g.label)
        ? new Date(first.created_at).toLocaleDateString('en-US', { timeZone: 'Asia/Manila', weekday: 'long', month: 'short', day: 'numeric' })
        : ''
      return { label: g.label, sub, items, unread: items.filter(n => !n.is_read).length }
    })
    .filter(g => g.items.length)
})
</script>

<style scoped>
* { box-sizing: border-box; }

.notifications-page { font-family: 'Inter', sans-serif; }
.pager { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 18px; }
.pager-num { font-size: 0.84rem; color: #4a5a4a; font-variant-numeric: tabular-nums; }

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

/* ===== Redesign: banner, filter pills, day cards with a timeline ===== */
.nx-hero { position: relative; display: flex; align-items: center; justify-content: space-between; gap: 24px; margin-bottom: 20px; padding: 30px 36px; border-radius: 26px; background: #004D3A; overflow: hidden; color: #FFFFFF; font-family: 'DM Sans', sans-serif; }
.nx-plate { position: absolute; right: -60px; top: 50%; width: 380px; height: 380px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.55; pointer-events: none; }
.nx-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004D3A 0%, #004D3A 50%, rgba(0, 77, 58, 0.4) 100%); pointer-events: none; }
.nx-text, .nx-side { position: relative; z-index: 1; }
.nx-eb { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 12.5px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; color: #EFBF04; }
.nx-eb span { width: 26px; height: 2px; background: #EFBF04; }
.nx-title { margin: 0 0 8px; font-family: 'Playfair Display', Georgia, serif; font-size: 34px; color: #FFFFFF; }
.nx-title em { color: #EFBF04; }
.page-sub.nx-sub { font-size: 14.5px; color: rgba(255, 255, 255, 0.85); }
.nx-side { display: flex; align-items: center; gap: 14px; padding: 8px 8px 8px 18px; border-radius: 999px; background: rgba(0, 0, 0, 0.2); border: 1px solid rgba(255, 255, 255, 0.15); }
.nx-side p { margin: 0; font-size: 14px; color: #CFE3D8; white-space: nowrap; }
.nx-side b { font-size: 18px; color: #EFBF04; }
.mark-all-btn.nx-mark { display: inline-flex; align-items: center; gap: 7px; height: 40px; min-height: 40px; padding: 0 16px; border-radius: 999px; background: #EFBF04; color: #004D3A; font-size: 13.5px; font-weight: 800; }
.mark-all-btn.nx-mark:hover:not(:disabled) { background: #F5CB1F; }
.nx-pills { display: inline-flex; flex-wrap: wrap; gap: 4px; margin: 0 0 16px; padding: 5px; border-radius: 999px; background: #FFFFFF; box-shadow: 0 8px 20px -14px rgba(0, 77, 58, 0.4); font-family: 'DM Sans', sans-serif; }
.nx-pills button { display: inline-flex; align-items: center; gap: 7px; height: 38px; padding: 0 14px; border: none; border-radius: 999px; background: none; font-family: inherit; font-size: 13.5px; font-weight: 700; color: #22362C; cursor: pointer; }
.nx-pills button i { font-style: normal; min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: #EEF2EF; font-size: 11.5px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }
.nx-pills button.on { background: #004D3A; color: #FFFFFF; }
.nx-pills button.on i { background: #EFBF04; color: #004D3A; }
.nx-pills button:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
.nx-list { display: flex; flex-direction: column; gap: 16px; font-family: 'DM Sans', sans-serif; }
.nx-none { margin: 0; padding: 30px; border-radius: 22px; background: #FFFFFF; border: 1.5px dashed #C6D9CD; text-align: center; color: #6B7D73; }
.nx-day { padding: 20px 24px; border-radius: 22px; background: #FFFFFF; border: 1.5px solid #E1EAE4; }
.day-label.nx-dh { display: flex; align-items: baseline; gap: 8px; margin: 0 0 6px; padding: 0; border: none; font-family: 'DM Sans', sans-serif; font-size: 14px; font-weight: 400; color: #6B7D73; }
.nx-dh b { font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: #0E3A2C; }
.nx-dh em { margin-left: auto; padding: 2px 10px; border-radius: 999px; background: #FBF3D2; color: #8A6400; font-style: normal; font-size: 12px; font-weight: 800; }
.nx-items { display: flex; flex-direction: column; }
.notif-item.nx-item { position: relative; display: grid; grid-template-columns: 44px minmax(0, 1fr) 14px; gap: 14px; align-items: start; padding: 14px 10px 14px 0; border: none !important; border-radius: 14px; }
.notif-item.nx-item:hover { background: #F7FAF8; }
.nx-item:not(:last-child)::after { content: ''; position: absolute; left: 21px; top: 60px; bottom: -14px; width: 2px; background: #E1EAE4; }
.nx-ic { position: relative; z-index: 1; width: 44px !important; height: 44px !important; border-radius: 50% !important; border: 3px solid #FFFFFF !important; box-sizing: border-box; }
.notif-icon.nx-ic.gold { background: #FBF3D2; color: #9A7300; }
.notif-icon.nx-ic.blue { background: #DFF0FB; color: #1F6FA8; }
.notif-icon.nx-ic.orange { background: #FDEBD9; color: #B8621B; }
.notif-icon.nx-ic.green { background: #DDEFE4; color: #1F7A4D; }
.notif-icon.nx-ic.purple { background: #ECE8F8; color: #5A4FA8; }
.nx-item .notif-body { min-width: 0; }
.nx-top { display: flex; align-items: center; gap: 8px; margin: 0; }
.nx-lab { padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 800; letter-spacing: 0.3px; }
.nx-lab.gold { background: #FBF3D2; color: #8A6400; }
.nx-lab.blue { background: #DFF0FB; color: #1F6FA8; }
.nx-lab.orange { background: #FDEBD9; color: #B8621B; }
.nx-lab.green { background: #E3F4EA; color: #1F7A4D; }
.nx-lab.purple { background: #ECE8F8; color: #5A4FA8; }
.nx-item .notif-time { font-size: 12px; color: #8A9A91; }
.nx-item .notif-subject { margin: 5px 0 2px; font-size: 15.5px; font-weight: 700; color: #22362C; }
.nx-item.unread .notif-subject { font-weight: 800; color: #0E3A2C; }
.nx-item .notif-text { margin: 0; max-width: 820px; font-size: 13.5px; line-height: 1.5; color: #4A5A52; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.nx-item .notif-log-row { margin: 8px 0 0; }
.nx-act { display: inline-flex; align-items: center; gap: 4px; margin-top: 8px; font-size: 13px; font-weight: 800; color: #004D3A; }
.nx-dot { margin-top: 8px; width: 10px; height: 10px; border-radius: 50%; background: #EFBF04; box-shadow: 0 0 0 3px rgba(239, 191, 4, 0.2); }
@media (max-width: 640px) {
  .nx-hero { flex-direction: column; align-items: stretch; padding: 22px 18px; }
  .nx-title { font-size: 26px; }
  .nx-plate { display: none; }
  .nx-side { justify-content: space-between; }
  .nx-pills { display: flex; flex-wrap: nowrap; overflow-x: auto; border-radius: 16px; }
  .nx-pills button { flex-shrink: 0; }
  .nx-day { padding: 16px 12px; }
  .notif-item.nx-item { grid-template-columns: 38px minmax(0, 1fr) 12px; gap: 10px; }
  .nx-ic { width: 38px !important; height: 38px !important; }
  .nx-item:not(:last-child)::after { left: 18px; top: 54px; }
}
</style>