<template>
  <div class="cc">
    <header class="cc-head">
      <MessageSquare :size="16" />
      <span>Chat consultation with <strong>{{ otherName }}</strong></span>
      <span class="cc-state">Messages are saved to your conversation</span>
    </header>
    <div ref="body" class="cc-body" aria-live="polite">
      <p v-if="loading" class="cc-muted">Loading the conversation…</p>
      <p v-else-if="!messages.length" class="cc-muted">No messages yet — say hello to start the consultation.</p>
      <div v-for="m in messages" :key="m.id" class="cc-msg" :class="{ mine: senderId(m) === meId }">
        <p class="cc-text">{{ m.message }}</p>
        <span class="cc-time">{{ time(m.created_at) }}</span>
      </div>
    </div>
    <p v-if="error" class="cc-error">{{ error }}</p>
    <form class="cc-form" @submit.prevent="send">
      <textarea v-model="draft" rows="2" maxlength="5000" :placeholder="`Message ${otherName}…`" aria-label="Message"
                @keydown.enter.exact.prevent="send" />
      <button type="submit" :disabled="sending || !draft.trim()" aria-label="Send"><Send :size="17" /></button>
    </form>
  </div>
</template>

<script setup>
// The chat for a chat-type consultation, shown in ConsultationRoom.vue where
// the video would be. Uses the relationship's NutriMatch conversation
// (/api/relationships/<id>/messages/), so everything is kept in the patient's
// message history. Works without Redis: sends over the API and checks for
// new messages every few seconds.
import { MessageSquare, Send } from 'lucide-vue-next'

const props = defineProps({
  relationshipId: { type: [Number, String], required: true },
  otherName: { type: String, default: '' },
})
const auth = useAuthStore()
const { get, post } = useApi()
const meId = computed(() => auth.user?.id)

const messages = ref([])
const loading = ref(true)
const draft = ref('')
const sending = ref(false)
const error = ref('')
const body = ref(null)

const senderId = m => (typeof m.sender === 'object' ? m.sender?.id : m.sender) ?? m.sender_id
function scroll() { nextTick(() => { if (body.value) body.value.scrollTop = body.value.scrollHeight }) }
function add(list) {
  const ids = new Set(messages.value.map(m => m.id))
  const fresh = list.filter(m => !ids.has(m.id))
  if (fresh.length) { messages.value.push(...fresh); scroll() }
}

async function load() {
  try {
    messages.value = await get(`/relationships/${props.relationshipId}/messages/`)
    scroll()
  } catch {
    error.value = 'Could not load the conversation.'
  } finally {
    loading.value = false
  }
}
async function poll() {
  if (loading.value || document.visibilityState !== 'visible') return
  const lastId = messages.value.length ? messages.value[messages.value.length - 1].id : 0
  try { add(await get(`/relationships/${props.relationshipId}/messages/`, { query: { after: lastId } })) } catch { /* next tick */ }
}
async function send() {
  const text = draft.value.trim()
  if (!text || sending.value) return
  sending.value = true
  error.value = ''
  draft.value = ''
  try {
    add([await post(`/relationships/${props.relationshipId}/messages/`, { message: text })])
  } catch (e) {
    draft.value = text
    error.value = e?.data?.detail || 'Could not send. Please try again.'
  } finally {
    sending.value = false
  }
}

let timer = null
onMounted(() => { load(); timer = setInterval(poll, 3000) })
onBeforeUnmount(() => clearInterval(timer))

function time(iso) {
  return new Date(iso).toLocaleTimeString('en-PH', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' })
}
</script>

<style scoped>
.cc { display: flex; flex-direction: column; height: 100%; min-height: 0; background: #f4f6f4; }
.cc-head { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 10px; padding: 12px 16px; background: #fff; border-bottom: 1px solid #e3e8e3; font-size: 0.85rem; color: #1a3a1a; }
.cc-state { margin-left: auto; font-size: 0.72rem; color: #8a9a8a; }
.cc-body { flex: 1; min-height: 0; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.cc-muted { color: #8a9a8a; font-size: 0.85rem; text-align: center; margin: auto 0; }
.cc-msg { align-self: flex-start; max-width: 75%; background: #fff; border: 1px solid #e3e8e3; border-radius: 14px 14px 14px 4px; padding: 8px 12px; }
.cc-msg.mine { align-self: flex-end; background: #163a1c; border-color: #163a1c; color: #fff; border-radius: 14px 14px 4px 14px; }
.cc-text { margin: 0; font-size: 0.88rem; line-height: 1.5; white-space: pre-line; overflow-wrap: anywhere; }
.cc-time { display: block; font-size: 0.66rem; opacity: 0.65; margin-top: 3px; text-align: right; }
.cc-error { margin: 0; padding: 6px 16px; font-size: 0.8rem; color: #a12525; background: #fdecec; }
.cc-form { display: flex; gap: 8px; align-items: flex-end; padding: 10px 12px; background: #fff; border-top: 1px solid #e3e8e3; }
.cc-form textarea { flex: 1; resize: none; border: 1px solid #d5dad5; border-radius: 10px; padding: 10px 12px; font-family: inherit; font-size: 0.88rem; }
.cc-form textarea:focus { outline: none; border-color: #1a3a1a; }
.cc-form button { width: 44px; height: 44px; border: none; border-radius: 10px; background: #163a1c; color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; }
.cc-form button:disabled { opacity: 0.5; cursor: not-allowed; }
@media (max-width: 560px) { .cc-msg { max-width: 88%; } .cc-state { display: none; } }
</style>
