<template>
  <div class="messages-page" :class="{ 'show-chat': mobileChatOpen }">
    <!-- CONVERSATION LIST -->
    <div class="conv-pane">
      <div class="conv-pane-header">
        <h2 class="conv-title">Conversations</h2>
        <p class="privacy-line"><Lock :size="12" aria-hidden="true" /> Private, protected under RA 10173</p>
      </div>

      <div class="search-row">
        <div class="search-wrap">
          <Search :size="16" class="search-icon" />
          <input v-model="searchQuery" type="text" class="search-input" placeholder="Search by name" aria-label="Search conversations" />
        </div>
      </div>

      <div v-if="loadingConversations" class="conv-empty">
        <p class="empty-title">Loading…</p>
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
          <p class="privacy-note"><Lock :size="12" aria-hidden="true" /> Only you and {{ activeConversation.firstName }} can read this conversation. It's kept private under the Data Privacy Act of 2012 (RA 10173).</p>
          <p v-if="loadingMessages" class="chat-note">Loading messages…</p>
          <p v-else-if="!activeMessages.length" class="chat-note">No messages yet. Say hello to {{ activeConversation.firstName }}.</p>

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
          <button class="send-btn" type="button" aria-label="Send message" @click="sendMessage">
            <Send :size="16" />
          </button>
        </div>
      </template>

      <div v-else class="chat-empty">
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
* { box-sizing: border-box; }

.messages-page {
  font-family: 'Inter', sans-serif;
  display: grid; grid-template-columns: 320px 1fr;
  /* One row that fills the box, and panes that may shrink into it — without
     these a long chat or patient list grows past the box and gets clipped,
     so neither the messages nor the list can scroll. */
  grid-template-rows: minmax(0, 1fr);
  height: calc(100vh - 140px); min-height: 560px;
  background: #fff; border-radius: 12px; border: 1px solid #d9e3dc; overflow: hidden;
  box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09);
}

/* CONVERSATION LIST */
.conv-pane { border-right: 1px solid #d9e3dc; display: flex; flex-direction: column; min-width: 0; min-height: 0; background: #fbfcfa; }
.conv-pane-header { padding: 18px 16px 12px; }
.conv-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0; }
.privacy-line { display: flex; align-items: center; gap: 5px; margin: 3px 0 0; font-size: 0.74rem; color: #5a7a66; }
.privacy-note { display: flex; align-items: flex-start; justify-content: center; gap: 6px; max-width: 460px; margin: 14px auto 4px; padding: 8px 12px; border-radius: 10px; background: #f2f6f3; font-size: 0.76rem; line-height: 1.45; color: #4a6a56; text-align: center; }
.privacy-note svg { flex-shrink: 0; margin-top: 2px; }

.search-row { padding: 0 16px 14px; border-bottom: 1px solid #d9e3dc; }
.search-wrap { position: relative; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #8a9a8a; }
.search-input {
  width: 100%; border: 1px solid #d9e3dc; border-radius: 8px; padding: 9px 12px 9px 36px; background: #fff;
  font-size: 0.85rem; font-family: inherit; color: #1a3a1a;
}
.search-input:focus { outline: none; border-color: #3f9a6b; box-shadow: 0 0 0 3px rgba(63, 154, 107, 0.15); }

.conv-list { flex: 1; min-height: 0; overflow-y: auto; }
.conv-item {
  position: relative; width: 100%; display: flex; align-items: flex-start; gap: 12px; text-align: left;
  padding: 13px 16px; border: none; border-bottom: 1px solid #eef1ee; background: none; cursor: pointer; font-family: inherit;
}
.conv-item:hover { background: #f4f7f4; }
.conv-item:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.conv-item.active { background: #fff; }
.conv-item.active::before { content: ''; position: absolute; left: 0; top: 10px; bottom: 10px; width: 3px; border-radius: 0 3px 3px 0; background: #1f8f5c; }
.conv-avatar, .chat-avatar {
  width: 38px; height: 38px; border-radius: 50%; flex-shrink: 0; object-fit: cover;
  background: #e3efe7; color: #1e4a26; display: flex; align-items: center; justify-content: center;
  font-size: 0.78rem; font-weight: 700;
}
.conv-body { flex: 1; min-width: 0; }
.conv-top { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.conv-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.conv-tag { margin-left: 6px; font-size: 0.68rem; font-weight: 600; color: #5a6a5a; background: #eceeec; border-radius: 6px; padding: 1px 6px; vertical-align: 1px; }
.conv-tag.waiting { color: #1f6f46; background: #fff; border: 1px dashed #3f9a6b; }
.conv-time { font-size: 0.72rem; color: #8a9a8a; flex-shrink: 0; font-variant-numeric: tabular-nums; }
.conv-bottom { display: flex; align-items: center; gap: 8px; }
.conv-preview { flex: 1; min-width: 0; font-size: 0.8rem; color: #7a8a7a; margin: 3px 0 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.conv-preview.unread { color: #1a3a1a; font-weight: 600; }
.conv-unread { flex-shrink: 0; margin-top: 3px; }
.conv-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 30px; text-align: center; }

/* CHAT PANEL */
.chat-pane { display: flex; flex-direction: column; background: #fff; min-width: 0; min-height: 0; }
.chat-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 22px; border-bottom: 1px solid #d9e3dc; }
.chat-who { display: flex; align-items: center; gap: 12px; min-width: 0; }
.chat-who-text { min-width: 0; }
.back-btn { display: none; }
.chat-name { font-size: 0.95rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.chat-sub { font-size: 0.78rem; color: #7a8a7a; margin: 1px 0 0; }
.online-status { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: 600; color: #1f8f5c; white-space: nowrap; }
.online-status.status-offline { color: #8a9a8a; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #1f8f5c; }
.status-offline .status-dot { background: #c9d2cb; }

.chat-body { flex: 1; min-height: 0; overflow-y: auto; padding: 8px 28px 20px; }
.chat-note { text-align: center; font-size: 0.84rem; color: #7a8a7a; margin: 28px 0; }
/* the day sits on a hairline, like a page break in a chart */
.day-label { display: flex; align-items: center; gap: 12px; margin: 18px 0 14px; font-size: 0.76rem; font-weight: 600; color: #6a7a6a; }
.day-label::before, .day-label::after { content: ''; flex: 1; border-top: 1px solid #d9e3dc; }

.msg-block { display: flex; flex-direction: column; margin-top: 12px; max-width: 62%; }
.msg-block.cont { margin-top: 3px; }
.msg-block-them { align-items: flex-start; }
.msg-block-me { align-items: flex-end; margin-left: auto; }
.msg-bubble { padding: 10px 14px; border-radius: 14px; font-size: 0.88rem; line-height: 1.5; white-space: pre-wrap; overflow-wrap: anywhere; }
.bubble-them { background: #f2f6f3; color: #1a2a1a; border: 1px solid #e3ebe5; }
.bubble-me { background: #0a4a37; color: #fff; }
/* back-to-back bubbles from one person share a flatter inner corner */
.msg-block-them.cont .bubble-them { border-top-left-radius: 5px; }
.msg-block-me.cont .bubble-me { border-top-right-radius: 5px; }
.msg-time { font-size: 0.7rem; color: #8a9a8a; margin-top: 4px; font-variant-numeric: tabular-nums; }

.chat-error { padding: 6px 22px 0; font-size: 0.8rem; color: #a12525; margin: 0; }
.chat-ended { margin: 0; padding: 14px 84px 14px 22px; background: #fafbfa; border-top: 1px solid #d9e3dc; font-size: 0.82rem; color: #5a6a5a; }
.chat-ended.waiting { background: #fff; border-top: 1.5px dashed #3f9a6b; color: #1f4a30; }

/* Right padding leaves room for the floating Help & Support button
   (SupportWidget, bottom right), which otherwise covers Send. */
.chat-input-row { display: flex; align-items: center; gap: 10px; padding: 14px 84px 14px 22px; border-top: 1px solid #d9e3dc; }
.chat-input {
  flex: 1; min-width: 0; border: 1px solid #d9e3dc; border-radius: 22px; padding: 11px 16px;
  font-size: 0.88rem; font-family: inherit; color: #1a3a1a; background: #fff;
}
.chat-input:focus { outline: none; border-color: #3f9a6b; box-shadow: 0 0 0 3px rgba(63, 154, 107, 0.15); }
.send-btn {
  width: 40px; height: 40px; border-radius: 50%; border: none; background: #0a4a37; color: #fff;
  display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0;
}
.send-btn:hover { background: #00382a; }
.send-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.chat-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 24px; }
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.84rem; color: #7a8a7a; margin: 0; }

/* TABLET / PHONE — under the layout's 900px breakpoint the page scrolls as a
   whole, so size the chat to the screen minus the two top bars + padding. */
@media (max-width: 900px) {
  .messages-page { grid-template-columns: 260px minmax(0, 1fr); height: calc(100dvh - 160px); min-height: 420px; }
}

/* PHONE — one pane at a time */
@media (max-width: 767px) {
  .messages-page { grid-template-columns: minmax(0, 1fr); }
  .conv-pane { border-right: none; min-height: 0; }
  .chat-pane { display: none; min-height: 0; }
  .show-chat .conv-pane { display: none; }
  .show-chat .chat-pane { display: flex; }

  .back-btn {
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    width: 32px; height: 32px; margin-left: -6px; border: none; border-radius: 8px;
    background: none; color: #1a3a1a; cursor: pointer;
  }
  .back-btn:active { background: #f0f2ef; }
  .chat-header { padding: 10px 14px; gap: 10px; }
  .chat-who { gap: 10px; }
  .chat-avatar { width: 34px; height: 34px; }
  .chat-name { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .online-status { font-size: 0.76rem; }

  .chat-body { padding: 6px 14px 16px; }
  .msg-block { max-width: 85%; }
  .msg-bubble { padding: 9px 12px; }

  .chat-error { padding: 6px 14px 0; }
  .chat-ended { padding: 12px 76px 12px 14px; }
  .chat-input-row { padding: 10px 76px 10px 12px; gap: 8px; }
  /* 16px stops iOS Safari from zooming in when the input is focused */
  .chat-input, .search-input { font-size: 16px; }
}
</style>
