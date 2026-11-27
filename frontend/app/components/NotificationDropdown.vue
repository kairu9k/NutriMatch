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

// Clicking a notification goes straight to the page it's about (no pop-up,
// 2026-11-03, user's call — utils/notificationLink.js). With nowhere to go it
// is just marked read: the row already shows the full text.
const { opening, openNotification: goTo } = useOpenNotification()
async function openNotification(n) {
  markRead(n)
  if (await goTo(n)) close()
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
  // a new one can replace an older unread one on the server (a changed meal rating), so re-sync quietly
  loadNotifications({ quiet: true })
})
live.onLive('reconnect', loadNotifications)
let fallbackTimer = null
onMounted(() => {
  fallbackTimer = setInterval(() => {
    if (!live.connected.value && document.visibilityState === 'visible') loadNotifications({ quiet: true })
  }, 30000)
})
onUnmounted(() => clearInterval(fallbackTimer))

/* ---------- UI only ---------- */
// a small icon + colour for each kind of notification, read from its subject
const NOTIF_KINDS = [
  { test: /pay|invoice|refund|receipt/i, tone: 'gold', path: '<rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20M6 15h4" />' },
  { test: /resource|guide|shared/i, tone: 'blue', path: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z" /><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5" />' },
  { test: /message/i, tone: 'green', path: '<path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />' },
  { test: /lab|result/i, tone: 'red', path: '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3" />' },
  { test: /meal|plan|log/i, tone: 'green', path: '<path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" />' },
  { test: /consult|appointment|booking|session|today/i, tone: 'green', path: '<rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" />' },
]
const notifKind = n => NOTIF_KINDS.find(k => k.test.test(n.subject || '')) || { tone: 'muted', path: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" />' }
</script>

<template>
  <div class="relative" v-click-outside="close">
    <button
      ref="bellEl"
      class="nb-bell btn-press"
      :class="{ on: open }"
      aria-label="Notifications"
      @click="toggle"
    >
      <NavIcon name="bell" class="w-5 h-5 transition-transform" :class="open ? 'rotate-12' : ''" />
      <span v-if="unreadCount" class="nb-dot animate-pop"></span>
    </button>

    <Transition name="dropdown">
      <div
        v-if="open"
        class="notif-panel"
        :style="{ '--panel-top': `${panelTop}px` }"
      >
        <div class="nb-head">
          <span class="nb-head-ico"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" /></svg></span>
          <div class="nb-head-text">
            <p class="nb-title">Notifications</p>
            <p class="nb-sub">{{ unreadCount ? `${unreadCount} unread` : 'You\'re all caught up' }}</p>
          </div>
          <button v-if="unreadCount" type="button" class="nb-markall" @click="markAllRead">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12.5l4.5 4.5L15 8.5M10 16l1 1 9-9.5" /></svg>Mark all read
          </button>
        </div>

        <div v-if="isLoading" class="nb-empty"><p>Loading…</p></div>

        <div v-else-if="!notifications.length" class="nb-empty">
          <span class="nb-empty-ico"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" /></svg></span>
          <p class="nb-empty-title">No notifications yet</p>
          <p>Updates about consultations, payments and your care show up here.</p>
        </div>

        <TransitionGroup v-else name="list" tag="div" class="notif-list">
          <div
            v-for="n in notifications"
            :key="n.id"
            class="nb-item"
            :class="{ unread: !n.is_read }"
            role="link" tabindex="0" :aria-busy="opening === n.id"
            @click="openNotification(n)" @keydown.enter="openNotification(n)"
          >
            <!-- meal log: photo thumbnail -->
            <img v-if="n.meal_log?.photo_url" :src="n.meal_log.photo_url" alt="" class="nb-thumb" />
            <div v-else-if="n.meal_log" class="nb-thumb none">No photo</div>
            <span v-else class="nb-ico" :class="notifKind(n).tone"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="notifKind(n).path" /></span>
            <div class="nb-body">
              <p class="nb-subject">{{ n.subject }}</p>
              <p class="nb-content">{{ n.content }}</p>
              <p v-if="n.meal_log" class="nb-meal">
                <span class="nb-status" :class="STATUS_CLASS[n.meal_log.status]">{{ n.meal_log.status_label }}</span>
                <span class="nb-open">Open in chart</span>
              </p>
              <p class="nb-time"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ opening === n.id ? 'Opening…' : timeAgo(n.created_at) }}</p>
            </div>
            <span v-if="!n.is_read" class="nb-unread" aria-label="Unread"></span>
          </div>
        </TransitionGroup>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
/* bell */
.nb-bell { position: relative; width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 8px; border: 1px solid rgba(0, 77, 58, 0.15); background: transparent; color: #004D3A; cursor: pointer; transition: background-color .15s, border-color .15s; }
.nb-bell:hover,
.nb-bell.on { background: #F1F6F2; border-color: rgba(0, 77, 58, 0.3); }
.nb-bell:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.nb-dot { position: absolute; top: -4px; right: -4px; width: 14px; height: 14px; border-radius: 50%; background: #EFBF04; border: 2px solid #FFFFFF; }

/* panel */
.notif-panel {
  position: absolute;
  right: 0;
  z-index: 50;
  width: 400px;
  margin-top: 10px;
  overflow: hidden;
  border-radius: 20px;
  background: #FFFFFF;
  border: 1px solid #E4EBE6;
  box-shadow: 0 2px 6px rgba(16, 35, 27, 0.06), 0 30px 60px -24px rgba(16, 35, 27, 0.45);
  transform-origin: top right;
  font-family: 'DM Sans', Arial, sans-serif;
}
.nb-head { display: flex; align-items: center; gap: 12px; padding: 16px 18px; background: linear-gradient(120deg, #F0F7F2 0%, #FFFFFF 75%); border-bottom: 1px solid #EEF2EF; }
.nb-head-ico { flex-shrink: 0; width: 40px; height: 40px; border-radius: 12px; background: #004D3A; color: #EFBF04; display: inline-flex; align-items: center; justify-content: center; }
.nb-head-text { flex: 1; min-width: 0; }
.nb-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; line-height: 1.2; color: #0E3A2C; }
.nb-sub { margin: 2px 0 0; font-size: 12.5px; color: #6B7D73; }
.nb-markall { flex-shrink: 0; display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; border: 1px solid #DCE8E0; border-radius: 10px; background: #FFFFFF; color: #004D3A; font-family: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.nb-markall:hover { background: #F1F6F2; }

.notif-list { position: relative; max-height: 420px; overflow-y: auto; padding: 8px; scrollbar-width: thin; }
.nb-item { position: relative; display: flex; align-items: flex-start; gap: 12px; padding: 12px; border-radius: 14px; cursor: pointer; transition: background-color .15s; }
.nb-item + .nb-item { margin-top: 2px; }
.nb-item:hover { background: #F6FAF7; }
.nb-item:focus-visible { outline: 2px solid #EFBF04; outline-offset: -2px; }
.nb-item.unread { background: #FFFBEC; }
.nb-item.unread:hover { background: #FFF6D6; }
.nb-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 13px; display: inline-flex; align-items: center; justify-content: center; }
.nb-ico.green { background: #E3EFE7; color: #004D3A; }
.nb-ico.gold { background: #FBF3D2; color: #9A7300; }
.nb-ico.blue { background: #EEF1FA; color: #3B5BA5; }
.nb-ico.red { background: #FDECEC; color: #B42318; }
.nb-ico.muted { background: #F1F3F2; color: #4A5A52; }
.nb-thumb { flex-shrink: 0; width: 46px; height: 46px; border-radius: 12px; object-fit: cover; border: 1px solid #E4EBE6; }
.nb-thumb.none { display: flex; align-items: center; justify-content: center; background: #F6FAF7; font-size: 10px; color: #8A9A91; }
.nb-body { flex: 1; min-width: 0; }
.nb-subject { margin: 0; font-size: 14px; font-weight: 700; line-height: 1.35; color: #0E3A2C; }
.nb-item:not(.unread) .nb-subject { font-weight: 600; color: #22362C; }
.nb-content { margin: 3px 0 0; font-size: 13px; line-height: 1.45; color: #4A5A52; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.nb-meal { display: flex; align-items: center; gap: 8px; margin: 6px 0 0; }
.nb-status { padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.nb-open { font-size: 11.5px; font-weight: 700; color: #1F7A4D; }
.nb-time { display: flex; align-items: center; gap: 5px; margin: 6px 0 0; font-size: 12px; color: #8A9A91; }
.nb-unread { flex-shrink: 0; width: 9px; height: 9px; margin-top: 6px; border-radius: 50%; background: #EFBF04; box-shadow: 0 0 0 3px rgba(239, 191, 4, 0.2); }

.nb-empty { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 32px 24px; text-align: center; font-size: 13.5px; color: #6B7D73; }
.nb-empty p { margin: 0; }
.nb-empty-ico { width: 56px; height: 56px; margin-bottom: 8px; border-radius: 50%; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.nb-empty-title { font-family: 'Playfair Display', Georgia, serif; font-size: 17px; font-weight: 700; color: #0E3A2C; }

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
  .notif-panel .notif-list { max-height: calc(100dvh - var(--panel-top, 64px) - 100px); }
  .nb-head { padding: 14px; }
  .nb-markall { padding: 0 10px; }
}
</style>