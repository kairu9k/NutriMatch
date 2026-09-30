<template>
  <div class="messages-page">
    <!-- CONVERSATION LIST -->
    <div class="conv-pane">
      <div class="conv-pane-header">
        <h2 class="conv-title">Conversations</h2>
        <span class="compliance-badge"><Lock :size="11" /> RA 10173</span>
      </div>

      <div class="search-row">
        <div class="search-wrap">
          <Search :size="16" class="search-icon" />
          <input v-model="searchQuery" type="text" class="search-input" placeholder="Search conversations..." />
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
          @click="selectConversation(conv.id)"
        >
          <div class="conv-avatar-wrap">
            <div class="conv-avatar" :style="{ background: conv.avatarColor }">{{ conv.initials }}</div>
          </div>
          <div class="conv-body">
            <div class="conv-top">
              <span class="conv-name">{{ conv.name }}</span>
              <span class="conv-time">{{ conv.lastMessageAt }}</span>
            </div>
            <p class="conv-preview">{{ conv.lastMessage }}</p>
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
            <div class="chat-avatar" :style="{ background: activeConversation.avatarColor }">{{ activeConversation.initials }}</div>
            <div>
              <p class="chat-name">{{ activeConversation.name }}</p>
              <p class="chat-sub">RA 10173-compliant</p>
            </div>
          </div>
          <div class="chat-header-right">
            <span class="online-status" :class="{ 'status-offline': !isConnected }"><span class="status-dot" /> {{ isConnected ? 'Live' : 'Connecting…' }}</span>
          </div>
        </div>

        <div class="chat-body" ref="chatBodyEl">
          <div v-if="loadingMessages" class="date-divider"><span>Loading…</span></div>
          <div v-else-if="!activeMessages.length" class="date-divider"><span>No messages yet — say hello</span></div>

          <div
            v-for="msg in activeMessages"
            :key="msg.id"
            class="msg-block"
            :class="msg.sender.id === authStore.user?.id ? 'msg-block-me' : 'msg-block-them'"
          >
            <span class="msg-sender">{{ msg.sender.id === authStore.user?.id ? 'You' : activeConversation.name }}</span>
            <div class="msg-bubble" :class="msg.sender.id === authStore.user?.id ? 'bubble-me' : 'bubble-them'">
              {{ msg.message }}
            </div>
            <span class="msg-time">{{ formatTime(msg.created_at) }}</span>
          </div>
        </div>

        <p v-if="sendError" class="chat-error">{{ sendError }}</p>
        <div class="chat-input-row">
          <input
            v-model="draft"
            type="text"
            class="chat-input"
            placeholder="Type a message..."
            @keyup.enter="sendMessage"
          />
          <button class="send-btn" type="button" aria-label="Send message" @click="sendMessage">
            <Send :size="16" />
          </button>
        </div>
      </template>

      <div v-else class="chat-empty">
        <div class="empty-icon"><MessageCircle :size="28" /></div>
        <p class="empty-title">Select a conversation</p>
        <p class="empty-desc">Choose a conversation on the left to start chatting.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { Search, Send, MessageCircle, Lock } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'dashboard', title: 'Messages' })

const { get } = useApi()
const authStore = useAuthStore()
const route = useRoute()
const config = useRuntimeConfig()

const AVATAR_COLORS = ['#1a3a1a', '#D4A017', '#3a6b3a', '#8a5a2a', '#5a3a8a']
function colorFor(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}
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
    const preview = lastMessageByRelationship.value[rel.id]
    return {
      id: rel.id,
      name: `${other.first_name} ${other.last_name}`,
      initials: initialsFor(other.first_name, other.last_name),
      avatarColor: colorFor(other.id),
      lastMessage: preview ? preview.message : 'No messages yet',
      lastMessageAt: preview ? formatTime(preview.created_at) : '',
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

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
}

async function loadConversations() {
  loadingConversations.value = true
  try {
    const isRnd = authStore.user?.role === 'rnd'
    const path = isRnd ? '/rnd/relationships/active/' : '/client/relationships/'
    relationships.value = await get(path)
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
    if (activeConversationId.value === relationshipId) await scrollToBottom()
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
    if (activeConversationId.value === relationshipId) scrollToBottom()
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

function sendMessage() {
  const text = draft.value.trim()
  if (!text || !activeConversationId.value) return

  if (!socket || socket.readyState !== WebSocket.OPEN) {
    sendError.value = 'Not connected — reconnecting…'
    return
  }

  sendError.value = ''
  socket.send(JSON.stringify({ message: text }))
  draft.value = ''
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
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onUnmounted(() => {
  disconnectSocket()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style scoped>
* { box-sizing: border-box; }

.messages-page {
  font-family: 'Inter', sans-serif;
  display: grid; grid-template-columns: 320px 1fr;
  height: calc(100vh - 140px); min-height: 560px;
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; overflow: hidden;
}

/* CONVERSATION LIST */
.conv-pane { border-right: 1px solid #eceeec; display: flex; flex-direction: column; }

.conv-pane-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 16px 14px; }
.conv-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0; }
.compliance-badge {
  display: flex; align-items: center; gap: 4px; background: #f0f2ef; color: #6a7a6a;
  font-size: 0.68rem; font-weight: 700; padding: 4px 9px; border-radius: 12px; white-space: nowrap;
}

.search-row { display: flex; align-items: center; gap: 8px; padding: 0 16px 16px; }
.search-wrap { position: relative; flex: 1; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #9aaa9a; }
.search-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px 10px 36px;
  font-size: 0.85rem; font-family: inherit; color: #2a2a2a;
}
.search-input:focus { outline: none; border-color: #D4A017; }

.conv-list { flex: 1; overflow-y: auto; }
.conv-item {
  width: 100%; display: flex; align-items: flex-start; gap: 12px; text-align: left;
  padding: 14px 16px; border: none; border-bottom: 1px solid #f3f4f0; background: #fff; cursor: pointer;
  border-left: 3px solid transparent;
}
.conv-item.active { background: #f4f2e9; border-left-color: #D4A017; }
.conv-avatar-wrap { position: relative; flex-shrink: 0; }
.conv-avatar {
  width: 36px; height: 36px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700;
}
.conv-body { flex: 1; min-width: 0; }
.conv-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.conv-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.conv-time { font-size: 0.72rem; color: #9aaa9a; flex-shrink: 0; }
.conv-preview {
  font-size: 0.8rem; color: #8a9a8a; margin: 3px 0 0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.conv-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 30px; text-align: center; }

/* CHAT PANEL */
.chat-pane { display: flex; flex-direction: column; background: #fff; }

.chat-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 22px; background: #fff; border-bottom: 1px solid #eceeec;
}
.chat-who { display: flex; align-items: center; gap: 12px; }
.chat-avatar {
  width: 38px; height: 38px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700;
}
.chat-name { font-size: 0.94rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.chat-sub { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; }
.chat-header-right { display: flex; align-items: center; gap: 14px; }
.online-status { display: flex; align-items: center; gap: 6px; font-size: 0.82rem; font-weight: 600; color: #2e9e52; }
.online-status.status-offline { color: #9aaa9a; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #2e9e52; }
.status-offline .status-dot { background: #d5dad5; }

.chat-body { flex: 1; overflow-y: auto; padding: 24px 28px; background: #fff; }
.date-divider { text-align: center; margin-bottom: 20px; }
.date-divider span {
  font-size: 0.72rem; letter-spacing: 0.06em; color: #9aaa9a; text-transform: uppercase;
}

.msg-block { display: flex; flex-direction: column; margin-bottom: 20px; max-width: 60%; }
.msg-block-them { align-items: flex-start; }
.msg-block-me { align-items: flex-end; margin-left: auto; }
.msg-sender { font-size: 0.78rem; font-weight: 700; color: #4a5a4a; margin-bottom: 5px; }

.msg-bubble { padding: 12px 16px; border-radius: 12px; font-size: 0.86rem; line-height: 1.5; }
.bubble-them { background: #f4f6f4; color: #2a2a2a; }
.bubble-me { background: #14301a; color: #fff; }
.msg-time { font-size: 0.72rem; color: #9aaa9a; margin-top: 5px; }

.chat-error { padding: 6px 22px 0; font-size: 0.78rem; color: #b3261e; background: #fff; margin: 0; }

.chat-input-row {
  display: flex; align-items: center; gap: 10px; padding: 16px 22px;
  background: #fff; border-top: 1px solid #eceeec;
}
.chat-input {
  flex: 1; border: 1px solid #d5dad5; border-radius: 20px; padding: 11px 16px;
  font-size: 0.86rem; font-family: inherit; color: #2a2a2a;
}
.chat-input:focus { outline: none; border-color: #D4A017; }
.chat-input:disabled { background: #f4f2e9; }
.send-btn {
  width: 38px; height: 38px; border-radius: 50%; border: none; background: #14301a; color: #fff;
  display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0;
}
.send-btn:disabled { opacity: 0.5; cursor: default; }

.chat-empty {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.84rem; color: #8a9a8a; margin: 0; }
</style>
