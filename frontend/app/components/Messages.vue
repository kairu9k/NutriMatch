<template>
  <div class="messages-page">
    <!-- CONVERSATION LIST -->
    <div class="conv-pane">
      <div class="search-wrap">
        <Search :size="16" class="search-icon" />
        <input v-model="searchQuery" type="text" class="search-input" placeholder="Search messages..." />
      </div>

      <div v-if="filteredConversations.length" class="conv-list">
        <button
          v-for="conv in filteredConversations"
          :key="conv.id"
          class="conv-item"
          :class="{ active: activeConversationId === conv.id }"
          @click="activeConversationId = conv.id"
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
        <p class="empty-desc">Messages with your RND will show up here.</p>
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
              <p v-if="activeConversation.online" class="chat-status">
                <span class="status-dot" /> Active now
              </p>
            </div>
          </div>
          <button class="video-btn" type="button" aria-label="Start video call">
            <Video :size="18" />
          </button>
        </div>

        <div class="chat-body">
          <div class="date-divider"><span>Today</span></div>

          <div
            v-for="msg in activeMessages"
            :key="msg.id"
            class="msg-row"
            :class="msg.sender === 'me' ? 'msg-row-me' : 'msg-row-them'"
          >
            <div class="msg-bubble" :class="msg.sender === 'me' ? 'bubble-me' : 'bubble-them'">
              {{ msg.text }}
            </div>
            <span class="msg-time">{{ msg.time }}</span>
          </div>
        </div>

        <div class="chat-input-row">
          <input
            v-model="draft"
            type="text"
            class="chat-input"
            placeholder="Type your message..."
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
import { computed, ref } from 'vue'
import { Search, Video, Send, MessageCircle } from 'lucide-vue-next'
import { db } from '~/mock/mockDatabase'

definePageMeta({ layout: 'dashboard', title: 'Messages' })

const searchQuery = ref('')
const draft = ref('')

const conversations = ref(db.conversations)
const messagesByConversation = ref(db.messagesByConversation)

const activeConversationId = ref(conversations.value[0]?.id ?? null)

const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) return conversations.value
  const q = searchQuery.value.toLowerCase()
  return conversations.value.filter(c => c.name.toLowerCase().includes(q))
})

const activeConversation = computed(() =>
  conversations.value.find(c => c.id === activeConversationId.value) ?? null
)

const activeMessages = computed(() =>
  activeConversationId.value ? (messagesByConversation.value[activeConversationId.value] ?? []) : []
)

function sendMessage() {
  const text = draft.value.trim()
  if (!text || !activeConversationId.value) return

  // Wire this up to your real send-message API call
  const thread = messagesByConversation.value[activeConversationId.value] ?? []
  thread.push({
    id: `msg-${Date.now()}`,
    sender: 'me',
    text,
    time: new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
  })
  messagesByConversation.value[activeConversationId.value] = thread
  draft.value = ''
}
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
.chat-status { display: flex; align-items: center; gap: 5px; font-size: 0.78rem; color: #3a6b3a; margin: 2px 0 0; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #3a6b3a; }

.video-btn {
  width: 36px; height: 36px; border-radius: 50%; border: none; background: #D4A017; color: #1a3a1a;
  display: flex; align-items: center; justify-content: center; cursor: pointer;
}

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

.chat-input-row {
  display: flex; align-items: center; gap: 10px; padding: 16px 22px;
  background: #fff; border-top: 1px solid #eceeec;
}
.chat-input {
  flex: 1; border: 1px solid #d5dad5; border-radius: 20px; padding: 11px 16px;
  font-size: 0.86rem; font-family: inherit; color: #2a2a2a;
}
.chat-input:focus { outline: none; border-color: #D4A017; }
.send-btn {
  width: 38px; height: 38px; border-radius: 50%; border: none; background: #1a3a1a; color: #fff;
  display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0;
}

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