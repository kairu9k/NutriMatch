<template>
  <div class="sup">
    <div class="nm-toolbar">
      <div class="nm-tabs" role="tablist">
        <button v-for="t in TABS" :key="t.key" type="button" role="tab" class="nm-tab" :class="{ active: status === t.key }" :aria-selected="status === t.key" @click="status = t.key">
          {{ t.label }}<span v-if="t.key !== 'all'" class="nm-count">{{ counts[t.key] ?? 0 }}</span>
        </button>
      </div>
      <div class="nm-search">
        <Search :size="15" aria-hidden="true" />
        <input v-model="search" type="search" placeholder="Search name, email, subject or SR-0001" aria-label="Search support requests" />
      </div>
    </div>
    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- SUPPORT DESK (2026-10-25): the queue and the open request each scroll on
         their own on desktop; on phones the request opens over the queue. -->
    <div ref="layout" class="desk" :class="{ 'has-open': !!selectedId }" :style="deskHeight ? { '--desk-h': `${deskHeight}px` } : null">
      <!-- QUEUE -->
      <section class="nm-panel queue">
        <p class="queue-head">{{ queueText }}</p>
        <p v-if="loading" class="nm-muted queue-empty">Loading…</p>
        <div v-else-if="!tickets.length" class="nm-empty queue-empty">
          <Inbox :size="28" aria-hidden="true" />
          <p>{{ emptyText }}</p>
        </div>
        <button v-for="t in pagedTickets" :key="t.id" type="button" class="q-row" :class="{ on: t.id === selectedId, unread: t.unread }" @click="select(t.id)">
          <img v-if="t.user.profile_photo" :src="t.user.profile_photo" class="nm-avatar sm" alt="" />
          <span v-else class="nm-avatar sm">{{ nameInitials(t.user.name) }}</span>
          <span class="q-main">
            <span class="q-top">
              <span class="q-name">{{ t.user.name }}<small>, {{ ROLE[t.user.role] }}</small></span>
              <span class="q-time" :class="{ long: waitingLong(t) }" :title="when(t.last_activity_at)">{{ ageText(t) }}</span>
            </span>
            <span class="q-subject"><span v-if="t.unread" class="dot" aria-label="New message"></span>{{ t.subject }}</span>
            <span v-if="t.last_message" class="q-preview">{{ t.last_message.from_support ? 'You: ' : '' }}{{ t.last_message.body }}</span>
            <span class="q-meta">
              <span>{{ t.reference }}, {{ t.category_label }}</span>
              <span v-if="status === 'all'" class="nm-pill" :class="STATUS_PILL[t.status]">{{ t.status_label }}</span>
            </span>
          </span>
        </button>
        <ListPager v-model:page="page" :pages="pages" />
      </section>

      <!-- THE REQUEST -->
      <section class="nm-panel thread">
        <div v-if="!selectedId" class="nm-empty thread-empty">
          <Headset :size="28" aria-hidden="true" />
          <p>Pick a request to read and reply.</p>
        </div>
        <p v-else-if="!ticket" class="nm-muted thread-empty">Loading…</p>
        <template v-else>
          <div class="t-head">
            <button type="button" class="nm-btn-soft nm-btn-sm back" @click="selectedId = null"><ArrowLeft :size="14" aria-hidden="true" /> All requests</button>
            <div class="t-title">
              <div class="t-name">
                <h2 class="nm-panel-title">{{ ticket.subject }}</h2>
                <p class="nm-panel-sub">{{ ticket.reference }}, {{ ticket.category_label }}, opened {{ when(ticket.created_at) }}</p>
              </div>
              <div class="t-actions">
                <span class="nm-pill" :class="STATUS_PILL[ticket.status]">{{ ticket.status_label }}</span>
                <button v-if="ticket.status !== 'closed'" type="button" class="nm-btn-soft nm-btn-sm" :disabled="busy" @click="act('close')">Close request</button>
                <button v-else type="button" class="nm-btn-soft nm-btn-sm" :disabled="busy" @click="act('reopen')">Reopen</button>
              </div>
            </div>
          </div>

          <!-- who asked, and what it's about -->
          <div class="who">
            <img v-if="ticket.user.profile_photo" :src="ticket.user.profile_photo" class="nm-avatar" alt="" />
            <span v-else class="nm-avatar">{{ nameInitials(ticket.user.name) }}</span>
            <div class="who-text">
              <strong>{{ ticket.user.name }}</strong>
              <span>{{ ROLE[ticket.user.role] }}, <a :href="`mailto:${ticket.user.email}`" class="nm-text-link">{{ ticket.user.email }}</a></span>
            </div>
            <NuxtLink :to="`/users/${ticket.user.id}`" class="nm-btn-soft nm-btn-sm">View user</NuxtLink>
          </div>
          <div v-if="ticket.appointment || ticket.invoice" class="refs">
            <span class="refs-label">About</span>
            <NuxtLink v-if="ticket.appointment" to="/admin-appointments?view=all" class="ref"><CalendarCheck :size="14" aria-hidden="true" /> {{ ticket.appointment.label }}</NuxtLink>
            <NuxtLink v-if="ticket.invoice" to="/billing-commission" class="ref"><Receipt :size="14" aria-hidden="true" /> {{ ticket.invoice.label }}</NuxtLink>
          </div>

          <!-- the conversation, split by day -->
          <div ref="box" class="msgs">
            <template v-for="g in messageDays" :key="g.key">
              <p class="msg-day"><span>{{ g.label }}</span></p>
              <div v-for="m in g.items" :key="m.id" class="msg" :class="{ support: m.from_support }">
                <p class="msg-who">{{ m.from_support ? `${m.sender_name} for NutriMatch Support` : m.sender_name }}, {{ timeOnly(m.created_at) }}</p>
                <p class="msg-body">{{ m.body }}</p>
              </div>
            </template>
          </div>

          <form class="reply" @submit.prevent="sendReply">
            <label class="sr-only" for="sup-reply">Reply</label>
            <textarea id="sup-reply" v-model="reply" data-allow-emoji class="nm-input" rows="3" maxlength="3000"
              :placeholder="`Reply to ${ticket.user.name.split(' ')[0]}`"></textarea>
            <div class="reply-foot">
              <p class="reply-hint">
                {{ ticket.status === 'closed' ? 'Replying reopens the request. ' : '' }}They see it from NutriMatch Support and get an email.
              </p>
              <button type="submit" class="nm-btn-dark" :disabled="busy || reply.trim().length < 2"><Send :size="14" aria-hidden="true" /> {{ busy ? 'Sending…' : 'Send reply' }}</button>
            </div>
            <p v-if="replyError" class="nm-field-error">{{ replyError }}</p>
          </form>
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
// waiting for us = gold (a to-do), waiting for them = green, done = grey
const STATUS_PILL = { open: 'gold', answered: 'green', closed: 'muted' }
const ROLE = { client: 'Client', rnd: 'RND' }
// an open request older than this gets a gold age
const LONG_WAIT_HOURS = 24

const status = ref('open')
const search = ref('')
const tickets = ref([])
const counts = ref({})
const loading = ref(true)
const error = ref('')
// Open requests: the one waiting longest first, like a queue at a counter
const sorted = computed(() => status.value === 'open'
  ? [...tickets.value].sort((a, b) => new Date(a.last_activity_at) - new Date(b.last_activity_at))
  : tickets.value)
const { page, pages, paged: pagedTickets } = usePager(sorted, { perPage: 20, resetOn: () => [status.value, search.value] })

const queueText = computed(() => {
  const n = tickets.value.length
  if (status.value === 'open') return n ? `${n} waiting for a reply, oldest first` : 'Nothing waiting for a reply'
  return `${n} request${n === 1 ? '' : 's'}`
})
const emptyText = computed(() => {
  if (search.value.trim()) return 'No requests match this search.'
  return { open: 'No requests waiting for a reply.', answered: 'No requests waiting for the user.', closed: 'No closed requests.' }[status.value] || 'No support requests yet.'
})

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    const q = new URLSearchParams({ status: status.value })
    if (search.value.trim()) q.set('search', search.value.trim())
    const data = await get(`/admin/support/tickets/?${q}`)
    tickets.value = data.results
    counts.value = data.counts
  } catch {
    if (!quiet) error.value = 'Could not load support requests. Refresh the page to try again.'
  } finally {
    loading.value = false
  }
}
// New requests and user replies show without a reload: the list, and the open
// thread (its typed reply is kept; a focused reply box pauses this anyway).
async function refreshAll() {
  await load({ quiet: true })
  if (!selectedId.value || busy.value) return
  const id = selectedId.value
  const fresh = await get(`/admin/support/tickets/${id}/`).catch(() => null)
  if (!fresh || selectedId.value !== id) return
  const grew = (fresh.messages?.length || 0) > (ticket.value?.messages?.length || 0)
  ticket.value = fresh
  if (grew) scroll()
}
useAutoRefresh(refreshAll)
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
    replyError.value = e?.data?.body?.[0] || e?.data?.detail || 'Could not send the reply. Try again.'
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
    replyError.value = 'Could not update this request. Try again.'
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

// Desktop: the queue and the request fill the rest of the screen and scroll on
// their own, so the page itself stays still (same as RND applications).
const layout = ref(null)
const deskHeight = ref(0)
const isWide = () => window.matchMedia('(min-width: 1000px)').matches
function measure() {
  if (!layout.value || !isWide()) { deskHeight.value = 0; return }
  const top = layout.value.getBoundingClientRect().top + window.scrollY
  deskHeight.value = Math.max(420, window.innerHeight - top - 24)
  nextTick(() => {
    const over = document.documentElement.scrollHeight - window.innerHeight
    if (over > 0) deskHeight.value = Math.max(420, deskHeight.value - over)
  })
}
onMounted(() => {
  nextTick(measure)
  window.addEventListener('resize', measure)
})
onBeforeUnmount(() => window.removeEventListener('resize', measure))

/* display */
const PH = { timeZone: 'Asia/Manila' }
function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}
function waitingLong(t) {
  return t.status === 'open' && Date.now() - new Date(t.last_activity_at) > LONG_WAIT_HOURS * 3600000
}
function ageText(t) {
  const s = Math.floor((Date.now() - new Date(t.last_activity_at)) / 1000)
  if (s < 60) return 'Just now'
  if (s < 3600) return `${Math.floor(s / 60)} min`
  if (s < 86400) return `${Math.floor(s / 3600)} h`
  const d = Math.floor(s / 86400)
  return `${d} day${d === 1 ? '' : 's'}`
}
function when(iso) {
  return new Date(iso).toLocaleString('en-PH', { ...PH, month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}
function timeOnly(iso) {
  return new Date(iso).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
}
const dayKey = v => new Date(v).toLocaleDateString('en-CA', PH)
const messageDays = computed(() => {
  const out = []
  const today = dayKey(Date.now())
  const yesterday = dayKey(Date.now() - 86400000)
  for (const m of ticket.value?.messages || []) {
    const key = dayKey(m.created_at)
    const last = out[out.length - 1]
    if (last && last.key === key) { last.items.push(m); continue }
    const label = key === today ? 'Today' : key === yesterday ? 'Yesterday'
      : new Date(m.created_at).toLocaleDateString('en-PH', { ...PH, weekday: 'long', month: 'long', day: 'numeric' })
    out.push({ key, label, items: [m] })
  }
  return out
})
</script>

<style scoped>
.desk { display: grid; grid-template-columns: minmax(280px, 380px) minmax(0, 1fr); gap: 16px; align-items: start; }

/* queue */
.queue { padding: 8px; }
.queue-head { margin: 6px 8px 8px; font-size: 0.78rem; font-weight: 600; color: #6a7a6a; }
.queue-empty { padding: 32px 10px; }
.q-row {
  display: flex; gap: 10px; align-items: flex-start; width: 100%; text-align: left; border: 0; background: none;
  border-radius: 10px; padding: 10px; cursor: pointer; font-family: inherit; border-left: 3px solid transparent;
}
.q-row + .q-row { margin-top: 2px; }
.q-row:hover { background: #f7faf8; }
.q-row.on { background: #eef5f0; border-left-color: #0a4a37; }
.q-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.nm-avatar.sm { width: 32px; height: 32px; font-size: 0.72rem; }
.q-main { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.q-top { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.q-name { font-size: 0.84rem; font-weight: 700; color: #1a3a1a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.q-name small { font-weight: 500; color: #8a9a8a; font-size: 0.76rem; }
.q-time { flex-shrink: 0; font-size: 0.72rem; font-weight: 600; color: #6a7a6a; background: #f2f6f3; border-radius: 999px; padding: 1px 8px; }
.q-time.long { background: #fdf3dc; color: #7a560f; }
.q-subject { font-size: 0.83rem; color: #2a3a2a; min-width: 0; overflow-wrap: anywhere; }
.q-row.unread .q-subject { font-weight: 700; color: #1a3a1a; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #D4A017; margin: 0 6px 1px 0; vertical-align: middle; }
.q-preview { font-size: 0.76rem; color: #8a9a8a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.q-meta { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-top: 2px; font-size: 0.72rem; color: #8a9a8a; }

/* the request */
.thread { padding-top: 0; display: flex; flex-direction: column; min-height: 460px; }
.thread-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 10px; }
.t-head {
  position: sticky; top: 0; z-index: 2; margin: 0 -22px; padding: 18px 22px 14px; background: #fff;
  border-bottom: 1px solid #d9e3dc; border-radius: 14px 14px 0 0;
}
.back { display: none; margin-bottom: 12px; }
.t-title { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.t-name { min-width: 0; flex: 1; }
.t-name .nm-panel-title { font-size: 1.2rem; overflow-wrap: anywhere; }
.t-actions { display: flex; align-items: center; gap: 10px; }
.who { display: flex; align-items: center; gap: 12px; padding: 14px 0; border-bottom: 1px solid #edf1ee; }
.who-text { display: flex; flex-direction: column; min-width: 0; flex: 1; font-size: 0.84rem; color: #1a3a1a; }
.who-text span { font-size: 0.78rem; color: #6a7a6a; overflow-wrap: anywhere; }
.refs { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; padding: 12px 0; border-bottom: 1px solid #edf1ee; }
.refs-label { font-size: 0.76rem; font-weight: 600; color: #6a7a6a; }
.ref {
  display: inline-flex; align-items: center; gap: 6px; font-size: 0.78rem; font-weight: 600; color: #0a4a37;
  background: #e3efe7; border-radius: 8px; padding: 6px 10px; text-decoration: none; overflow-wrap: anywhere;
}
.ref:hover { background: #d3e7da; }

.msgs { flex: 1; display: flex; flex-direction: column; gap: 10px; padding: 8px 2px 16px; }
.msg-day { display: flex; align-items: center; gap: 10px; margin: 10px 0 2px; font-size: 0.74rem; font-weight: 600; color: #8a9a8a; }
.msg-day::before, .msg-day::after { content: ''; flex: 1; height: 1px; background: #edf1ee; }
.msg { align-self: flex-start; max-width: 78%; background: #f4f6f4; border-radius: 14px 14px 14px 4px; padding: 10px 13px; }
.msg.support { align-self: flex-end; background: #e3efe7; border-radius: 14px 14px 4px 14px; }
.msg-who { font-size: 0.72rem; font-weight: 600; color: #6a7a6a; margin: 0 0 3px; }
.msg-body { font-size: 0.86rem; color: #1a3a1a; line-height: 1.55; margin: 0; white-space: pre-line; overflow-wrap: anywhere; }

.reply {
  position: sticky; bottom: 0; margin: 0 -22px -22px; padding: 14px 22px 18px; background: #f7faf8;
  border-top: 1px solid #d9e3dc; border-radius: 0 0 14px 14px;
}
.reply textarea { resize: vertical; background: #fff; }
.reply-foot { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 10px; flex-wrap: wrap; }
.reply-hint { margin: 0; font-size: 0.78rem; color: #6a7a6a; flex: 1; min-width: 200px; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

/* desktop: both sides scroll on their own */
@media (min-width: 1000px) {
  .queue, .thread {
    max-height: var(--desk-h, calc(100vh - 180px)); overflow-y: auto; overscroll-behavior: contain;
    scrollbar-width: thin; scrollbar-color: #c5d6ca transparent;
  }
  .thread { min-height: var(--desk-h, 460px); }
}
@media (max-width: 999px) {
  .desk { grid-template-columns: minmax(0, 1fr); }
  .desk.has-open .queue { display: none; }
  .desk:not(.has-open) .thread { display: none; }
  .back { display: inline-flex; }
  .msg { max-width: 92%; }
}
@media (max-width: 640px) {
  .nm-search { flex: 1 1 100%; max-width: none; }
  .t-head { margin: 0 -16px; padding: 16px 16px 12px; }
  .reply { margin: 0 -16px -18px; padding: 12px 16px 16px; }
  .who { flex-wrap: wrap; }
  .t-head, .reply { position: static; }
  .t-actions { width: 100%; }
  .t-actions .nm-pill { margin-right: auto; }
}
</style>
