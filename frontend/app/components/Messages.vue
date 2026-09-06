<template>
  <div class="messages-page">
    <!-- CONVERSATION LIST -->
    <div class="conv-pane">
      <div class="search-wrap">
        <Search :size="16" class="search-icon" />
        <input v-model="searchQuery" type="text" class="search-input" placeholder="Search messages..." />
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
          <div class="conv-avatar" :style="{ background: conv.avatarColor }">{{ conv.initials }}</div>
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
            </div>
          </div>
        </div>

        <div class="chat-body" ref="chatBodyEl">
          <div v-if="loadingMessages" class="date-divider"><span>Loading…</span></div>
          <div v-else-if="!activeMessages.length" class="date-divider"><span>No messages yet — say hello</span></div>

          <div
            v-for="msg in activeMessages"
            :key="msg.id"
            class="msg-row"
            :class="msg.sender.id === authStore.user?.id ? 'msg-row-me' : 'msg-row-them'"
          >
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
            placeholder="Type your message..."
            :disabled="sending"
            @keyup.enter="sendMessage"
          />
          <button class="send-btn" type="button" aria-label="Send message" :disabled="sending" @click="sendMessage">
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
import { Search, Send, MessageCircle } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'dashboard', title: 'Messages' })

const { get, post } = useApi()
const authStore = useAuthStore()

const AVATAR_COLORS = ['#1a3a1a', '#D4A017', '#3a6b3a', '#8a5a2a', '#5a3a8a']
function colorFor(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}
function initialsFor(first, last) {
  return `${(first || '?')[0] ?? ''}${(last || '')[0] ?? ''}`.toUpperCase()
}

const searchQuery = ref('')
const draft = ref('')
const sending = ref(false)
const sendError = ref('')
const loadingConversations = ref(true)
const loadingMessages = ref(false)

const relationships = ref([])
const activeConversationId = ref(null)
const messagesByRelationship = ref({})
const lastMessageByRelationship = ref({})
const chatBodyEl = ref(null)

let pollTimer = null

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
      selectConversation(relationships.value[0].id)
    }
  } finally {
    loadingConversations.value = false
  }
}

async function loadMessages(relationshipId, { silent = false } = {}) {
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

function selectConversation(id) {
  activeConversationId.value = id
  sendError.value = ''
  loadMessages(id)
}

async function scrollToBottom() {
  await nextTick()
  if (chatBodyEl.value) chatBodyEl.value.scrollTop = chatBodyEl.value.scrollHeight
}

async function sendMessage() {
  const text = draft.value.trim()
  if (!text || !activeConversationId.value || sending.value) return

  sending.value = true
  sendError.value = ''
  try {
    const message = await post(`/relationships/${activeConversationId.value}/messages/`, { message: text })
    const thread = messagesByRelationship.value[activeConversationId.value] ?? []
    thread.push(message)
    messagesByRelationship.value[activeConversationId.value] = thread
    lastMessageByRelationship.value[activeConversationId.value] = message
    draft.value = ''
    await scrollToBottom()
  } catch {
    sendError.value = 'Message failed to send. Please try again.'
  } finally {
    sending.value = false
  }
}

watch(activeConversationId, () => scrollToBottom())

onMounted(async () => {
  await loadConversations()
  pollTimer = setInterval(() => {
    if (activeConversationId.value) loadMessages(activeConversationId.value, { silent: true })
  }, 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
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

.search-wrap { position: relative; padding: 16px; border-bottom: 1px solid #eceeec; }
.search-icon { position: absolute; left: 28px; top: 50%; transform: translateY(-50%); color: #9aaa9a; }
.search-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px 10px 36px;
  font-size: 0.85rem; font-family: inherit; color: #2a2a2a;
}
.search-input:focus { outline: none; border-color: #D4A017; }

.conv-list { flex: 1; overflow-y: auto; }
.conv-item {
  width: 100%; display: flex; align-items: flex-start; gap: 12px; text-align: left;
  padding: 14px 16px; border: none; border-bottom: 1px solid #f3f4f0; background: #fff; cursor: pointer;
}
.conv-item.active { background: #f4f2e9; }
.conv-avatar {
  width: 36px; height: 36px; border-radius: 50%; color: #fff; flex-shrink: 0;
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
.chat-pane { display: flex; flex-direction: column; background: #f4f2e9; }

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

.chat-body { flex: 1; overflow-y: auto; padding: 24px 28px; }
.date-divider { text-align: center; margin-bottom: 20px; }
.date-divider span {
  font-size: 0.72rem; letter-spacing: 0.06em; color: #9aaa9a; text-transform: uppercase;
}

.msg-row { display: flex; flex-direction: column; margin-bottom: 18px; max-width: 60%; }
.msg-row-them { align-items: flex-start; }
.msg-row-me { align-items: flex-end; margin-left: auto; }

.msg-bubble { padding: 12px 16px; border-radius: 14px; font-size: 0.86rem; line-height: 1.5; }
.bubble-them { background: #fff; color: #2a2a2a; border-bottom-left-radius: 4px; }
.bubble-me { background: #1a3a1a; color: #fff; border-bottom-right-radius: 4px; }
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
  width: 38px; height: 38px; border-radius: 50%; border: none; background: #1a3a1a; color: #fff;
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
