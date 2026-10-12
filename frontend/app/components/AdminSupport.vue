<template>
  <div class="sup">
    <div class="toolbar">
      <div class="nm-tabs" role="tablist">
        <button v-for="t in TABS" :key="t.key" type="button" role="tab" class="nm-tab" :class="{ active: status === t.key }" :aria-selected="status === t.key" @click="status = t.key">
          {{ t.label }}<span v-if="t.key !== 'all'" class="nm-count">{{ counts[t.key] ?? 0 }}</span>
        </button>
      </div>
      <div class="nm-search">
        <Search :size="15" />
        <input v-model="search" type="search" placeholder="Search name, email, subject or SR-0001" aria-label="Search support requests" />
      </div>
    </div>
    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="layout" :class="{ 'has-open': !!selectedId }">
      <!-- LIST -->
      <section class="nm-panel list">
        <p v-if="loading" class="nm-muted">Loading…</p>
        <div v-else-if="!tickets.length" class="empty">
          <Inbox :size="28" />
          <p>{{ status === 'open' ? 'No requests waiting for a reply.' : 'No requests here.' }}</p>
        </div>
        <button v-for="t in tickets" :key="t.id" type="button" class="row" :class="{ on: t.id === selectedId, unread: t.unread }" @click="select(t.id)">
          <span class="row-top">
            <span class="row-user">{{ t.user.name }} <small>{{ ROLE[t.user.role] }}</small></span>
            <span class="row-time">{{ ago(t.last_activity_at) }}</span>
          </span>
          <span class="row-subject"><span v-if="t.unread" class="dot" aria-label="Unread"></span>{{ t.subject }}</span>
          <span class="row-meta">
            <span>{{ t.reference }} · {{ t.category_label }}</span>
            <span class="nm-pill" :class="STATUS_PILL[t.status]">{{ t.status_label }}</span>
          </span>
        </button>
      </section>

      <!-- THREAD -->
      <section class="nm-panel thread-panel">
        <div v-if="!selectedId" class="empty">
          <Headset :size="28" />
          <p>Pick a request to read and reply.</p>
        </div>
        <p v-else-if="!ticket" class="nm-muted">Loading…</p>
        <template v-else>
          <button type="button" class="nm-panel-link back" @click="selectedId = null"><ArrowLeft :size="14" /> All requests</button>
          <div class="t-head">
            <div>
              <h2 class="nm-panel-title">{{ ticket.subject }}</h2>
              <p class="nm-panel-sub">{{ ticket.reference }} · {{ ticket.category_label }} · opened {{ when(ticket.created_at) }}</p>
            </div>
            <span class="nm-pill" :class="STATUS_PILL[ticket.status]">{{ ticket.status_label }}</span>
          </div>

          <div class="who">
            <div>
              <strong>{{ ticket.user.name }}</strong> <span class="nm-pill muted">{{ ROLE[ticket.user.role] }}</span>
              <p><a :href="`mailto:${ticket.user.email}`">{{ ticket.user.email }}</a></p>
            </div>
            <NuxtLink :to="`/users/${ticket.user.id}`" class="nm-btn-outline nm-btn-sm">View user</NuxtLink>
          </div>
          <div v-if="ticket.appointment || ticket.invoice" class="refs">
            <NuxtLink v-if="ticket.appointment" to="/admin-appointments" class="ref"><CalendarCheck :size="14" /> {{ ticket.appointment.label }}</NuxtLink>
            <NuxtLink v-if="ticket.invoice" to="/billing-commission" class="ref"><Receipt :size="14" /> {{ ticket.invoice.label }}</NuxtLink>
          </div>

          <div ref="box" class="msgs">
            <div v-for="m in ticket.messages" :key="m.id" class="msg" :class="{ support: m.from_support }">
              <p class="msg-who">{{ m.from_support ? `${m.sender_name} (Support)` : m.sender_name }} · {{ when(m.created_at) }}</p>
              <p class="msg-body">{{ m.body }}</p>
            </div>
          </div>

          <form class="reply" @submit.prevent="sendReply">
            <textarea v-model="reply" class="nm-input" rows="3" maxlength="3000" placeholder="Write a reply — the user is notified and emailed. They see it from &quot;NutriMatch Support&quot;." aria-label="Reply"></textarea>
            <div class="reply-actions">
              <button v-if="ticket.status !== 'closed'" type="button" class="nm-btn-outline nm-btn-sm" :disabled="busy" @click="act('close')">Close request</button>
              <button v-else type="button" class="nm-btn-outline nm-btn-sm" :disabled="busy" @click="act('reopen')">Reopen</button>
              <button type="submit" class="nm-btn-dark nm-btn-sm" :disabled="busy || reply.trim().length < 2"><Send :size="13" /> {{ busy ? 'Sending…' : 'Send reply' }}</button>
            </div>
          </form>
          <p v-if="replyError" class="nm-error">{{ replyError }}</p>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup>
// Admin Support page: every Help & Support request from clients and RNDs
// (communication/support.py). Open = waiting for us, Answered = waiting for
// the user. ?ticket=<id> opens one (notification / email links).
import { ArrowLeft, CalendarCheck, Headset, Inbox, Receipt, Search, Send } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { get, post } = useApi()

const TABS = [{ key: 'open', label: 'Open' }, { key: 'answered', label: 'Answered' }, { key: 'closed', label: 'Closed' }, { key: 'all', label: 'All' }]
const STATUS_PILL = { open: 'gold', answered: 'green', closed: 'muted' }
const ROLE = { client: 'Client', rnd: 'RND' }

const status = ref('open')
const search = ref('')
const tickets = ref([])
const counts = ref({})
const loading = ref(true)
const error = ref('')

async function load() {
  error.value = ''
  try {
    const q = new URLSearchParams({ status: status.value })
    if (search.value.trim()) q.set('search', search.value.trim())
    const data = await get(`/admin/support/tickets/?${q}`)
    tickets.value = data.results
    counts.value = data.counts
  } catch {
    error.value = 'Could not load support requests.'
  } finally {
    loading.value = false
  }
}
let t = null
watch(search, () => { clearTimeout(t); t = setTimeout(load, 300) })
watch(status, load)
onMounted(load)

const selectedId = ref(null)
const ticket = ref(null)
const reply = ref('')
const busy = ref(false)
const replyError = ref('')
const box = ref(null)
async function select(id) {
  selectedId.value = Number(id)
  ticket.value = null
  reply.value = ''
  replyError.value = ''
  try {
    ticket.value = await get(`/admin/support/tickets/${id}/`)
    const row = tickets.value.find(x => x.id === Number(id))
    if (row) row.unread = false
    scroll()
  } catch {
    replyError.value = 'Could not open this request.'
  }
}
async function sendReply() {
  busy.value = true
  replyError.value = ''
  try {
    ticket.value = await post(`/admin/support/tickets/${ticket.value.id}/messages/`, { body: reply.value.trim() })
    reply.value = ''
    scroll()
    load()
  } catch (e) {
    replyError.value = e?.data?.body?.[0] || e?.data?.detail || 'Could not send the reply.'
  } finally {
    busy.value = false
  }
}
async function act(kind) {
  busy.value = true
  try {
    ticket.value = await post(`/admin/support/tickets/${ticket.value.id}/${kind}/`)
    load()
  } catch {
    replyError.value = 'Could not update this request.'
  } finally {
    busy.value = false
  }
}
function scroll() { nextTick(() => { if (box.value) box.value.scrollTop = box.value.scrollHeight }) }

watch(() => route.query.ticket, (id) => {
  if (!id) return
  status.value = 'all'
  select(id)
  const { ticket: _, ...rest } = route.query
  router.replace({ query: rest })
}, { immediate: true })

function ago(iso) {
  const s = Math.floor((Date.now() - new Date(iso)) / 1000)
  for (const [label, secs] of [['d', 86400], ['h', 3600], ['m', 60]]) {
    const v = Math.floor(s / secs)
    if (v >= 1) return `${v}${label} ago`
  }
  return 'just now'
}
function when(iso) {
  return new Date(iso).toLocaleString('en-PH', { timeZone: 'Asia/Manila', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}
</script>

<style scoped>
.toolbar { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.layout { display: grid; grid-template-columns: minmax(280px, 380px) minmax(0, 1fr); gap: 16px; align-items: start; }
.list { padding: 10px; max-height: calc(100vh - 220px); overflow-y: auto; }
.empty { display: flex; flex-direction: column; align-items: center; gap: 8px; color: #8a9a8a; padding: 40px 10px; text-align: center; font-size: 0.85rem; }
.empty p { margin: 0; }
.row { display: flex; flex-direction: column; gap: 4px; width: 100%; text-align: left; border: 1px solid transparent; background: none; border-radius: 10px; padding: 10px 12px; cursor: pointer; font-family: inherit; }
.row + .row { margin-top: 2px; }
.row:hover { background: #f7f9f7; }
.row.on { background: #eef4ee; border-color: #cfe0d2; }
.row-top { display: flex; justify-content: space-between; gap: 8px; }
.row-user { font-size: 0.82rem; font-weight: 600; color: #1a3a1a; }
.row-user small { font-weight: 500; color: #8a9a8a; margin-left: 4px; }
.row-time { font-size: 0.7rem; color: #9aaa9a; white-space: nowrap; }
.row-subject { font-size: 0.82rem; color: #2a3a2a; display: flex; align-items: center; gap: 6px; overflow-wrap: anywhere; }
.row.unread .row-subject { font-weight: 700; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #e04b3c; flex-shrink: 0; }
.row-meta { display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 0.7rem; color: #8a9a8a; }

.thread-panel { min-height: 420px; }
.back { display: none; align-items: center; gap: 4px; margin-bottom: 10px; }
.t-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 12px; }
.t-head .nm-panel-title { overflow-wrap: anywhere; }
.who { display: flex; justify-content: space-between; align-items: center; gap: 10px; background: #f7f9f7; border-radius: 10px; padding: 10px 12px; margin-bottom: 10px; font-size: 0.84rem; }
.who p { margin: 3px 0 0; font-size: 0.78rem; }
.who a { color: #1f8f5c; }
.refs { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.ref { display: inline-flex; align-items: center; gap: 5px; font-size: 0.76rem; color: #34508a; background: #eef1f8; border-radius: 8px; padding: 5px 9px; text-decoration: none; }
.msgs { display: flex; flex-direction: column; gap: 10px; max-height: 420px; overflow-y: auto; padding: 4px 2px 10px; }
.msg { align-self: flex-start; max-width: 80%; background: #f4f6f4; border-radius: 12px 12px 12px 4px; padding: 9px 12px; }
.msg.support { align-self: flex-end; background: #e6f0e8; border-radius: 12px 12px 4px 12px; }
.msg-who { font-size: 0.68rem; font-weight: 700; color: #6a7a6a; margin: 0 0 3px; }
.msg-body { font-size: 0.85rem; color: #1a3a1a; line-height: 1.55; margin: 0; white-space: pre-line; overflow-wrap: anywhere; }
.reply { border-top: 1px solid #eceeec; padding-top: 12px; }
.reply textarea { resize: vertical; }
.reply-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 8px; flex-wrap: wrap; }

@media (max-width: 900px) {
  .layout { grid-template-columns: minmax(0, 1fr); }
  .layout.has-open .list { display: none; }
  .layout:not(.has-open) .thread-panel { display: none; }
  .back { display: inline-flex; }
  .list { max-height: none; }
  .msg { max-width: 92%; }
}
@media (max-width: 560px) {
  .toolbar { flex-direction: column; align-items: stretch; }
  .nm-search { max-width: none; }
  .who { flex-direction: column; align-items: flex-start; }
}
</style>
