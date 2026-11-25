<template>
  <div class="messages-page" :class="{ 'show-chat': mobileChatOpen }">
    <!-- CONVERSATION LIST -->
    <div class="conv-pane">
      <div class="conv-pane-header">
        <div class="conv-title-row">
          <h2 class="conv-title">Conversations</h2>
          <span v-if="conversations.length" class="conv-count">{{ conversations.length }}</span>
        </div>
        <p class="privacy-line"><Lock :size="12" aria-hidden="true" /> Private, protected under RA 10173</p>
      </div>

      <div class="search-row">
        <div class="search-wrap">
          <Search :size="16" class="search-icon" />
          <input v-model="searchQuery" type="text" class="search-input" placeholder="Search by name" aria-label="Search conversations" />
        </div>
      </div>

      <div v-if="loadingConversations" class="conv-empty">
        <p class="empty-desc">Loading…</p>
      </div>

      <div v-else-if="filteredConversations.length" class="conv-list">
        <button
          v-for="conv in filteredConversations"
          :key="conv.id"
          class="conv-item"
          :class="{ active: activeConversationId === conv.id }"
          @click="openConversation(conv.id)"
        >
          <img v-if="conv.photo" :src="conv.photo" alt="" class="conv-avatar" />
          <span v-else class="conv-avatar">{{ conv.initials }}</span>
          <div class="conv-body">
            <div class="conv-top">
              <span class="conv-name">{{ conv.name }}<span v-if="conv.ended" class="conv-tag">Ended</span><span v-else-if="conv.waiting" class="conv-tag waiting">Waiting</span></span>
              <span class="conv-time">{{ conv.lastMessageAt }}</span>
            </div>
            <div class="conv-bottom">
              <p class="conv-preview" :class="{ unread: unreadFor(conv.id) }">{{ conv.lastMessage }}</p>
              <span v-if="unreadFor(conv.id)" class="conv-unread w-3 h-3 rounded-full bg-gold animate-pop" role="img" :aria-label="`${unreadFor(conv.id)} unread`"></span>
            </div>
          </div>
        </button>
      </div>

      <div v-else class="conv-empty">
        <span class="empty-ico"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg></span>
        <p class="empty-title">No conversations yet</p>
        <p class="empty-desc">
          {{ authStore.user?.role === 'rnd' ? 'Messages with your patients will show up here.' : 'Messages with your RND will show up here.' }}
        </p>
      </div>
    </div>

    <!-- CHAT PANEL -->
    <div class="chat-pane">
      <template v-if="activeConversation">
        <div class="chat-header">
          <div class="chat-who">
            <button class="back-btn" type="button" aria-label="Back to conversations" @click="mobileChatOpen = false">
              <ArrowLeft :size="18" />
            </button>
            <img v-if="activeConversation.photo" :src="activeConversation.photo" alt="" class="chat-avatar" />
            <span v-else class="chat-avatar">{{ activeConversation.initials }}</span>
            <div class="chat-who-text">
              <p class="chat-name">{{ activeConversation.name }}</p>
              <p class="chat-sub">{{ authStore.user?.role === 'rnd' ? 'Your patient' : 'Your RND' }}<template v-if="activeConversation.ended">, care ended</template></p>
            </div>
          </div>
          <div class="chat-header-right">
            <span class="online-status" :class="{ 'status-offline': !isConnected }" :title="isConnected ? 'New messages appear instantly' : 'Checking for new messages every few seconds'"><span class="status-dot" /> {{ isConnected ? 'Live' : 'Reconnecting' }}</span>
          </div>
        </div>

        <div class="chat-body" ref="chatBodyEl">
          <p v-if="loadingMessages" class="chat-note">Loading messages…</p>
          <div v-else-if="!activeMessages.length" class="chat-hello">
            <img v-if="activeConversation.photo" :src="activeConversation.photo" alt="" class="hello-avatar" />
            <span v-else class="hello-avatar">{{ activeConversation.initials }}</span>
            <p class="hello-title">Start your conversation</p>
            <p class="chat-note">No messages yet. Say hello to {{ activeConversation.firstName }}.</p>
            <p class="hello-lock"><Lock :size="12" aria-hidden="true" /> Only you and {{ activeConversation.firstName }} can read these messages.</p>
          </div>

          <!-- grouped by day; one sender's back-to-back messages sit together -->
          <section v-for="day in messageDays" :key="day.key" class="day">
            <p class="day-label"><span>{{ day.label }}</span></p>
            <div
              v-for="msg in day.items"
              :key="msg.id"
              class="msg-block"
              :class="[mine(msg) ? 'msg-block-me' : 'msg-block-them', { cont: msg.cont }]"
            >
              <div class="msg-bubble" :class="mine(msg) ? 'bubble-me' : 'bubble-them'">{{ msg.message }}</div>
              <span v-if="!msg.nextSame" class="msg-time">{{ formatTime(msg.created_at) }}</span>
            </div>
          </section>
        </div>

        <p v-if="sendError" class="chat-error">{{ sendError }}</p>
        <p v-if="activeConversation.ended" class="chat-ended">This care has ended, so the conversation is read-only. Book a new consultation to message again.</p>
        <p v-else-if="activeConversation.waiting" class="chat-ended waiting">{{ authStore.user?.role === 'rnd' ? `You can message ${activeConversation.firstName} once you confirm their booking.` : `You can message ${activeConversation.firstName} once they confirm your booking.` }}</p>
        <div v-else class="chat-input-row">
          <input
            v-model="draft"
            type="text"
            class="chat-input" data-allow-emoji
            :placeholder="`Message ${activeConversation.firstName}`"
            @keyup.enter="sendMessage"
          />
          <button class="send-btn" type="button" aria-label="Send message" :class="{ ready: draft.trim() }" @click="sendMessage">
            <Send :size="18" />
          </button>
        </div>
      </template>

      <div v-else class="chat-empty">
        <span class="empty-ico big"><svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /><path d="M8 9h8M8 13h5" /></svg></span>
        <p class="empty-title">No conversation open</p>
        <p class="empty-desc">Pick someone from the list to read and reply.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { ArrowLeft, Lock, Search, Send } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'dashboard', title: 'Messages' })

const { get, post } = useApi()
const authStore = useAuthStore()
const route = useRoute()
const config = useRuntimeConfig()

function initialsFor(first, last) {
  return `${(first || '?')[0] ?? ''}${(last || '')[0] ?? ''}`.toUpperCase()
}

const searchQuery = ref('')
const draft = ref('')
const sendError = ref('')
const loadingConversations = ref(true)
const loadingMessages = ref(false)
const isConnected = ref(false)

const relationships = ref([])
const activeConversationId = ref(null)
const messagesByRelationship = ref({})
const lastMessageByRelationship = ref({})
const chatBodyEl = ref(null)

let socket = null
let reconnectTimer = null

const conversations = computed(() => {
  const isRnd = authStore.user?.role === 'rnd'
  return relationships.value.map((rel) => {
    const other = isRnd ? rel.client : rel.rnd
    // The loaded thread once opened; before that, the latest from /messages/unread/.
    const preview = lastMessageByRelationship.value[rel.id] || unread.value.latest?.[rel.id]
    return {
      id: rel.id,
      name: `${other.first_name} ${other.last_name}`,
      ended: rel.status === 'discharged',
      waiting: rel.status === 'pending',
      firstName: other.first_name,
      initials: initialsFor(other.first_name, other.last_name),
      photo: other.profile_photo || '',
      lastMessage: preview ? preview.message : 'No messages yet',
      lastMessageAt: preview ? listTime(preview.created_at) : '',
      lastMessageTs: preview ? preview.created_at : rel.created_at,
    }
  }).sort((a, b) => new Date(b.lastMessageTs) - new Date(a.lastMessageTs))
})

const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) return conversations.value
  const q = searchQuery.value.toLowerCase()
  return conversations.value.filter(c => c.name.toLowerCase().includes(q))
})

const activeConversation = computed(() =>
  conversations.value.find(c => c.id === activeConversationId.value) ?? null
)

const activeMessages = computed(() =>
  activeConversationId.value ? (messagesByRelationship.value[activeConversationId.value] ?? []) : []
)

// Unread counts per conversation; whatever is open (and on screen) is read.
const { unread, refresh: refreshUnread, markRead } = useUnreadMessages()
const unreadFor = id => (id === activeConversationId.value ? 0 : unread.value.byRelationship[id] || 0)
function markActiveRead() {
  const id = activeConversationId.value
  if (id && document.visibilityState === 'visible') markRead(id)
}
const isFromOther = m => m?.sender?.id !== authStore.user?.id
const mine = m => m?.sender?.id === authStore.user?.id

// Philippine dates (the ph-time plugin makes toLocale* default to Asia/Manila)
const dayKey = iso => new Date(iso).toLocaleDateString('en-CA')
function dayName(iso) {
  const k = dayKey(iso)
  if (k === dayKey(Date.now())) return 'Today'
  if (k === dayKey(Date.now() - 86400000)) return 'Yesterday'
  return new Date(iso).toLocaleDateString('en-PH', { weekday: 'long', month: 'long', day: 'numeric' })
}
// the list shows the time for today's messages, else the day
function listTime(iso) {
  const d = dayName(iso)
  if (d === 'Today') return formatTime(iso)
  return d === 'Yesterday' ? d : new Date(iso).toLocaleDateString('en-PH', { month: 'short', day: 'numeric' })
}
const GROUP_MS = 5 * 60 * 1000 // same sender within 5 minutes = one group
const messageDays = computed(() => {
  const days = []
  const list = activeMessages.value
  list.forEach((m, i) => {
    const key = dayKey(m.created_at)
    let day = days[days.length - 1]
    if (!day || day.key !== key) days.push(day = { key, label: dayName(m.created_at), items: [] })
    const prev = list[i - 1]
    const next = list[i + 1]
    const same = (a, b) => a && b && a.sender.id === b.sender.id && dayKey(a.created_at) === dayKey(b.created_at)
      && Math.abs(new Date(b.created_at) - new Date(a.created_at)) < GROUP_MS
    day.items.push({ ...m, cont: same(prev, m), nextSame: same(m, next) })
  })
  return days
})

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

// Phones show one pane at a time: the list, or the open chat (with a back
// button). Desktop ignores this and shows both side by side.
const mobileChatOpen = ref(Boolean(route.query.relationship))
function openConversation(id) {
  mobileChatOpen.value = true
  if (id !== activeConversationId.value) selectConversation(id)
}

async function loadConversations() {
  loadingConversations.value = true
  try {
    const isRnd = authStore.user?.role === 'rnd'
    const path = isRnd ? '/rnd/relationships/active/' : '/client/relationships/'
    // Discharged care stays readable here (sending is closed).
    relationships.value = await get(path, { query: { include: 'ended' } })
    if (!activeConversationId.value && relationships.value.length) {
      // ?relationship=<id> (e.g. from a patient's chart) opens that
      // conversation; otherwise fall back to the first one.
      const requested = Number(route.query.relationship)
      const target = relationships.value.find(r => r.id === requested) ?? relationships.value[0]
      selectConversation(target.id)
    }
  } finally {
    loadingConversations.value = false
  }
}

async function loadMessageHistory(relationshipId, { silent = false } = {}) {
  if (!silent) loadingMessages.value = true
  try {
    const data = await get(`/relationships/${relationshipId}/messages/`)
    messagesByRelationship.value[relationshipId] = data
    if (data.length) {
      lastMessageByRelationship.value[relationshipId] = data[data.length - 1]
    }
    if (activeConversationId.value === relationshipId) {
      markActiveRead()
      await scrollToBottom()
    }
  } finally {
    if (!silent) loadingMessages.value = false
  }
}

function wsUrlFor(relationshipId) {
  // apiBase is e.g. http://localhost:8000/api — the WS route lives
  // outside /api, at the ASGI app's root (see backend communication/routing.py).
  const base = config.public.apiBase.replace(/\/api\/?$/, '')
  const wsBase = base.replace(/^http/, 'ws')
  return `${wsBase}/ws/relationships/${relationshipId}/messages/?token=${authStore.accessToken}`
}

function connectSocket(relationshipId, { isReconnect = false } = {}) {
  disconnectSocket()
  isConnected.value = false

  socket = new WebSocket(wsUrlFor(relationshipId))

  socket.onopen = () => {
    isConnected.value = true
    // A reconnect (network blip, idle Redis pubsub timeout, server
    // restart) has a real gap where messages could have been sent and
    // missed — the group broadcast only reaches connections that were
    // subscribed at that moment. Re-sync from REST to backfill anything
    // missed rather than silently dropping it until the next manual reload.
    if (isReconnect) loadMessageHistory(relationshipId, { silent: true })
  }

  socket.onmessage = (event) => {
    const message = JSON.parse(event.data)
    const thread = messagesByRelationship.value[relationshipId] ?? []
    // The consumer echoes the sender's own message back too (group
    // broadcast includes the sender) — skip re-appending if it's already
    // the last thing in the thread (covers the optimistic-append case).
    if (thread.length && thread[thread.length - 1].id === message.id) return
    thread.push(message)
    messagesByRelationship.value[relationshipId] = thread
    lastMessageByRelationship.value[relationshipId] = message
    if (activeConversationId.value === relationshipId) {
      if (isFromOther(message)) markActiveRead()
      scrollToBottom()
    }
  }

  socket.onclose = (event) => {
    isConnected.value = false
    // 4001 (unauthenticated) / 4003 (not part of this relationship) are
    // permanent — don't retry those. Anything else (network blip, server
    // restart) is worth a reconnect attempt.
    if (event.code !== 4001 && event.code !== 4003 && activeConversationId.value === relationshipId) {
      reconnectTimer = setTimeout(() => connectSocket(relationshipId, { isReconnect: true }), 3000)
    }
  }

  socket.onerror = () => {
    isConnected.value = false
  }
}

function disconnectSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  if (socket) {
    socket.onclose = null
    socket.close()
    socket = null
  }
}

async function selectConversation(id) {
  activeConversationId.value = id
  sendError.value = ''
  await loadMessageHistory(id)
  connectSocket(id)
}

async function scrollToBottom() {
  await nextTick()
  if (chatBodyEl.value) chatBodyEl.value.scrollTop = chatBodyEl.value.scrollHeight
}

// Append messages not already in the thread (socket echo, polling, own send).
function appendMessages(relationshipId, list) {
  const thread = messagesByRelationship.value[relationshipId] ?? []
  const ids = new Set(thread.map(m => m.id))
  const fresh = list.filter(m => !ids.has(m.id))
  if (!fresh.length) return
  thread.push(...fresh)
  messagesByRelationship.value[relationshipId] = thread
  lastMessageByRelationship.value[relationshipId] = thread[thread.length - 1]
  if (activeConversationId.value === relationshipId) {
    if (fresh.some(isFromOther)) markActiveRead()
    scrollToBottom()
  }
}

async function sendMessage() {
  const text = draft.value.trim()
  if (!text || !activeConversationId.value) return
  sendError.value = ''

  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ message: text }))
    draft.value = ''
    return
  }
  // No live connection (e.g. Redis isn't running): send over the normal API;
  // the other side picks it up by polling.
  const id = activeConversationId.value
  try {
    draft.value = ''
    appendMessages(id, [await post(`/relationships/${id}/messages/`, { message: text })])
  } catch (e) {
    draft.value = text
    sendError.value = e?.data?.detail || 'Could not send your message. Please try again.'
  }
}

// While the live connection is down, check for new messages every few seconds.
const POLL_MS = 4000
let pollTimer = null
async function pollNew() {
  const id = activeConversationId.value
  if (!id || (socket && socket.readyState === WebSocket.OPEN) || document.visibilityState !== 'visible') return
  const thread = messagesByRelationship.value[id] ?? []
  const lastId = thread.length ? thread[thread.length - 1].id : 0
  try {
    appendMessages(id, await get(`/relationships/${id}/messages/`, { query: { after: lastId } }))
  } catch { /* try again next tick */ }
}

watch(activeConversationId, () => scrollToBottom())

// Defense-in-depth for the same missed-message-on-reconnect gap: a
// backgrounded tab can have its WebSocket silently die (mobile browsers,
// laptop sleep) without onclose firing promptly. Re-syncing whenever the
// tab regains focus catches that even if the close event never arrives.
function handleVisibilityChange() {
  if (document.visibilityState === 'visible' && activeConversationId.value) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      connectSocket(activeConversationId.value, { isReconnect: true })
    } else {
      loadMessageHistory(activeConversationId.value, { silent: true })
    }
  }
}

onMounted(() => {
  loadConversations()
  refreshUnread()
  document.addEventListener('visibilitychange', handleVisibilityChange)
  pollTimer = setInterval(pollNew, POLL_MS)
})

onUnmounted(() => {
  clearInterval(pollTimer)
  disconnectSocket()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
/* =========================================================
   Messages: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }

.messages-page {
  font-family: 'DM Sans', 'Inter', Arial, sans-serif;
  display: grid;
  grid-template-columns: 340px 1fr;
  /* One row that fills the box, and panes that may shrink into it, so both
     the list and the messages scroll inside. */
  grid-template-rows: minmax(0, 1fr);
  height: calc(100vh - 140px);
  min-height: 560px;
  overflow: hidden;
  border-radius: 24px;
  background: #FFFFFF;
  border: 1px solid #E4EBE6;
  box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 18px 36px -22px rgba(16, 35, 27, 0.35);
}

/* ---------- CONVERSATION LIST ---------- */
.conv-pane { display: flex; flex-direction: column; min-width: 0; min-height: 0; background: #F7FAF8; border-right: 1px solid #E7EDE9; }
.conv-pane-header { padding: 22px 20px 14px; }
.conv-title-row { display: flex; align-items: center; gap: 10px; }
.conv-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #0E3A2C; }
.conv-count { min-width: 24px; height: 24px; padding: 0 8px; border-radius: 999px; background: #004D3A; color: #EFBF04; font-size: 12px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }
.privacy-line { display: inline-flex; align-items: center; gap: 6px; margin: 8px 0 0; padding: 4px 10px; border-radius: 999px; background: #E3EFE7; font-size: 12px; font-weight: 600; color: #1F5C45; }

.search-row { padding: 0 16px 14px; }
.search-wrap { position: relative; }
.search-icon { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: #6B7D73; }
.search-input { width: 100%; height: 46px; padding: 0 16px 0 44px; border: 1px solid #E1E9E4; border-radius: 999px; background: #FFFFFF; font-family: inherit; font-size: 14px; color: #14261E; transition: border-color .15s, box-shadow .15s; }
.search-input:focus { outline: none; border-color: #004D3A; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }

.conv-list { flex: 1; min-height: 0; overflow-y: auto; padding: 4px 10px 12px; }
.conv-item { position: relative; width: 100%; display: flex; align-items: center; gap: 12px; margin-bottom: 4px; padding: 12px; border: none; border-radius: 16px; background: none; font-family: inherit; text-align: left; cursor: pointer; transition: background-color .15s, box-shadow .15s; }
.conv-item:hover { background: #FFFFFF; }
.conv-item:focus-visible { outline: 2px solid #EFBF04; outline-offset: -2px; }
.conv-item.active { background: #FFFFFF; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 10px 22px -16px rgba(16, 35, 27, 0.4); }
.conv-item.active::before { content: ''; position: absolute; left: 0; top: 14px; bottom: 14px; width: 4px; border-radius: 0 4px 4px 0; background: #004D3A; }
.conv-avatar,
.chat-avatar { flex-shrink: 0; width: 46px; height: 46px; border-radius: 50%; object-fit: cover; background: linear-gradient(135deg, #E3EFE7, #CFE2D7); color: #004D3A; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; }
.conv-item.active .conv-avatar { background: #004D3A; color: #EFBF04; }
.conv-body { flex: 1; min-width: 0; }
.conv-top { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.conv-name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14.5px; font-weight: 700; color: #0E3A2C; }
.conv-tag { margin-left: 6px; padding: 2px 8px; border-radius: 999px; background: #EEF1EF; font-size: 11px; font-weight: 700; color: #4A5A52; vertical-align: 1px; }
.conv-tag.waiting { background: #FBF3D2; color: #8A6400; border: none; }
.conv-time { flex-shrink: 0; font-size: 11.5px; color: #8A9A91; font-variant-numeric: tabular-nums; }
.conv-bottom { display: flex; align-items: center; gap: 8px; }
.conv-preview { flex: 1; min-width: 0; margin: 3px 0 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 13px; color: #6B7D73; }
.conv-preview.unread { color: #0E3A2C; font-weight: 700; }
.conv-unread { flex-shrink: 0; margin-top: 3px; box-shadow: 0 0 0 3px rgba(239, 191, 4, 0.2); }
.conv-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; padding: 30px; text-align: center; }

/* ---------- CHAT PANEL ---------- */
.chat-pane { display: flex; flex-direction: column; min-width: 0; min-height: 0; background: #FFFFFF; }
.chat-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 24px; background: #FFFFFF; border-bottom: 1px solid #EEF2EF; }
.chat-who { display: flex; align-items: center; gap: 14px; min-width: 0; }
.chat-header .chat-avatar { width: 48px; height: 48px; background: #004D3A; color: #EFBF04; box-shadow: 0 0 0 3px #FFFFFF, 0 0 0 5px #E3EFE7; }
.chat-who-text { min-width: 0; }
.back-btn { display: none; }
.chat-name { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: #0E3A2C; }
.chat-sub { margin: 2px 0 0; font-size: 13px; color: #6B7D73; }
.online-status { display: inline-flex; align-items: center; gap: 7px; height: 30px; padding: 0 12px; border-radius: 999px; background: #EAF4EE; font-size: 12.5px; font-weight: 700; color: #1F7A4C; white-space: nowrap; }
.online-status.status-offline { background: #F1F3F2; color: #6B7D73; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #1F9D55; box-shadow: 0 0 0 3px rgba(31, 157, 85, 0.2); }
.status-offline .status-dot { background: #B5C2BA; box-shadow: none; }

.chat-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 32px 24px;
  background-color: #F6FAF7;
  background-image: radial-gradient(rgba(0, 77, 58, 0.06) 1px, transparent 1px);
  background-size: 18px 18px;
}
.chat-note { margin: 28px 0; text-align: center; font-size: 13.5px; color: #6B7D73; }
.chat-hello { display: flex; flex-direction: column; align-items: center; margin: 48px auto 0; max-width: 360px; padding: 28px 24px; border-radius: 22px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 14px 30px -22px rgba(16, 35, 27, 0.4); text-align: center; }
.hello-avatar { width: 72px; height: 72px; margin-bottom: 14px; border-radius: 50%; object-fit: cover; background: #004D3A; color: #EFBF04; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 800; box-shadow: 0 0 0 4px #FFFFFF, 0 0 0 6px #E3EFE7; }
.hello-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #0E3A2C; }
.chat-hello .chat-note { margin: 6px 0 14px; }
.hello-lock { display: inline-flex; align-items: center; gap: 6px; margin: 0; padding: 6px 12px; border-radius: 999px; background: #F3F6F4; font-size: 12px; color: #4A5A52; }

/* the day: a pill in the middle */
.day-label { display: flex; align-items: center; justify-content: center; margin: 22px 0 14px; }
.day-label span { padding: 5px 14px; border-radius: 999px; background: #FFFFFF; border: 1px solid #E4EBE6; font-size: 12px; font-weight: 700; color: #4A5A52; box-shadow: 0 4px 10px -8px rgba(16, 35, 27, 0.4); }

.msg-block { display: flex; flex-direction: column; max-width: 62%; margin-top: 14px; }
.msg-block.cont { margin-top: 4px; }
.msg-block-them { align-items: flex-start; }
.msg-block-me { align-items: flex-end; margin-left: auto; }
.msg-bubble { padding: 11px 16px; border-radius: 20px; font-size: 14.5px; line-height: 1.5; white-space: pre-wrap; overflow-wrap: anywhere; }
.bubble-them { background: #FFFFFF; color: #14261E; border: 1px solid #E4EBE6; border-bottom-left-radius: 6px; box-shadow: 0 4px 12px -10px rgba(16, 35, 27, 0.4); }
.bubble-me { background: linear-gradient(135deg, #0B6B47 0%, #004D3A 100%); color: #FFFFFF; border-bottom-right-radius: 6px; box-shadow: 0 8px 18px -12px rgba(0, 77, 58, 0.8); }
/* back-to-back bubbles from one person share a flatter corner */
.msg-block-them.cont .bubble-them { border-top-left-radius: 6px; }
.msg-block-me.cont .bubble-me { border-top-right-radius: 6px; }
.msg-time { margin-top: 5px; padding: 0 4px; font-size: 11.5px; color: #8A9A91; font-variant-numeric: tabular-nums; }

.chat-error { margin: 0; padding: 8px 24px 0; font-size: 13px; font-weight: 600; color: #B42318; }
.chat-ended { margin: 0; padding: 16px 90px 16px 24px; background: #F7FAF8; border-top: 1px solid #EEF2EF; font-size: 13.5px; color: #4A5A52; }
.chat-ended.waiting { background: #FFFAEB; border-top: 1px solid #F1DE97; color: #6A5410; }

/* Right padding leaves room for the floating Help & Support button
   (SupportWidget, bottom right), which otherwise covers Send. */
.chat-input-row { display: flex; align-items: center; gap: 10px; padding: 14px 90px 16px 24px; background: #FFFFFF; border-top: 1px solid #EEF2EF; }
.chat-input { flex: 1; min-width: 0; height: 50px; padding: 0 20px; border: 1px solid #E1E9E4; border-radius: 999px; background: #F6FAF7; font-family: inherit; font-size: 14.5px; color: #14261E; transition: border-color .15s, box-shadow .15s, background-color .15s; }
.chat-input:focus { outline: none; background: #FFFFFF; border-color: #004D3A; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.send-btn { flex-shrink: 0; width: 50px; height: 50px; border: none; border-radius: 50%; background: #C9D6CE; color: #FFFFFF; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background-color .15s, transform .15s, box-shadow .15s; }
.send-btn.ready { background: #004D3A; box-shadow: 0 10px 20px -10px rgba(0, 77, 58, 0.9); }
.send-btn.ready:hover { background: #0A5C46; transform: translateY(-1px); }
.send-btn:focus-visible { outline: 3px solid rgba(239, 191, 4, 0.6); outline-offset: 2px; }

.chat-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; padding: 24px; text-align: center; background-color: #F6FAF7; background-image: radial-gradient(rgba(0, 77, 58, 0.06) 1px, transparent 1px); background-size: 18px 18px; }
.empty-ico { width: 56px; height: 56px; margin-bottom: 8px; border-radius: 50%; background: #FFFFFF; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px -14px rgba(0, 77, 58, 0.6); }
.empty-ico.big { width: 72px; height: 72px; }
.empty-title { margin: 0 0 2px; font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: #0E3A2C; }
.empty-desc { margin: 0; font-size: 13.5px; color: #6B7D73; }

/* TABLET / PHONE: under the layout's 900px breakpoint the page scrolls as a
   whole, so size the chat to the screen minus the top bars + padding. */
@media (max-width: 900px) {
  .messages-page { grid-template-columns: 280px minmax(0, 1fr); height: calc(100dvh - 160px); min-height: 420px; border-radius: 20px; }
}

/* PHONE: one pane at a time */
@media (max-width: 767px) {
  .messages-page { grid-template-columns: minmax(0, 1fr); }
  .conv-pane { border-right: none; min-height: 0; }
  .chat-pane { display: none; min-height: 0; }
  .show-chat .conv-pane { display: none; }
  .show-chat .chat-pane { display: flex; }

  .back-btn { display: flex; align-items: center; justify-content: center; flex-shrink: 0; width: 36px; height: 36px; margin-left: -6px; border: none; border-radius: 50%; background: #F1F6F2; color: #004D3A; cursor: pointer; }
  .back-btn:active { background: #E3EFE7; }
  .chat-header { padding: 12px 14px; gap: 10px; }
  .chat-who { gap: 10px; }
  .chat-header .chat-avatar { width: 40px; height: 40px; }
  .chat-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 17px; }
  .online-status { height: 26px; padding: 0 10px; font-size: 11.5px; }

  .conv-pane-header { padding: 18px 16px 12px; }
  .chat-body { padding: 6px 14px 16px; }
  .chat-hello { margin-top: 28px; padding: 22px 18px; }
  .msg-block { max-width: 85%; }
  .msg-bubble { padding: 10px 14px; font-size: 14px; }

  .chat-error { padding: 6px 14px 0; }
  .chat-ended { padding: 12px 76px 12px 14px; }
  .chat-input-row { padding: 10px 76px 12px 12px; gap: 8px; }
  .chat-input { height: 46px; }
  .send-btn { width: 46px; height: 46px; }
  /* 16px stops iOS Safari from zooming in when the input is focused */
  .chat-input, .search-input { font-size: 16px; }
}
</style>