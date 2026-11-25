<template>
  <div class="sup">
    <section class="sp-hero">
      <img class="sp-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="sp-fade" aria-hidden="true"></span>
      <div class="sp-hero-txt">
        <p class="sp-eyebrow"><span aria-hidden="true"></span>Support</p>
        <h2 class="sp-title">Help requests</h2>
        <p class="sp-sub">Questions from clients and RNDs. Oldest first, so no one waits too long.</p>
      </div>
    </section>

    <div class="nm-toolbar sp-toolbar">
      <div class="nm-tabs sp-tabs" role="tablist">
        <button v-for="t in TABS" :key="t.key" type="button" role="tab" class="nm-tab" :class="{ active: status === t.key }" :aria-selected="status === t.key" @click="status = t.key">
          <svg v-if="t.key === 'open'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.5 5.1L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.5-6.9A2 2 0 0 0 16.8 4H7.2a2 2 0 0 0-1.7 1.1z" /></svg><svg v-else-if="t.key === 'answered'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 17l-5-5 5-5" /><path d="M20 18v-2a4 4 0 0 0-4-4H4" /></svg><svg v-else-if="t.key === 'closed'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M8.5 12.5l2.5 2.5 4.5-5" /></svg><svg v-else class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>
          {{ t.label }}<span v-if="t.key !== 'all'" class="nm-count">{{ counts[t.key] ?? 0 }}</span>
        </button>
      </div>
      <div class="nm-search sp-search">
        <Search :size="17" aria-hidden="true" />
        <input v-model="search" type="search" placeholder="Search name, email, subject or SR-0001" aria-label="Search support requests" />
      </div>
    </div>
    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- SUPPORT DESK (2026-10-25): the queue and the open request each scroll on
         their own on desktop; on phones the request opens over the queue. -->
    <div ref="layout" class="desk" :class="{ 'has-open': !!selectedId }" :style="deskHeight ? { '--desk-h': `${deskHeight}px` } : null">
      <!-- QUEUE -->
      <section class="nm-panel queue">
        <p class="queue-head"><strong>{{ status === 'open' ? 'Waiting' : TABS.find(x => x.key === status).label }}</strong><i>{{ tickets.length }}</i><small>{{ status === 'open' ? 'Oldest first' : '' }}</small><span class="sr-only">{{ queueText }}</span></p>
        <p v-if="loading" class="nm-muted queue-empty">Loading…</p>
        <div v-else-if="!tickets.length" class="nm-empty queue-empty">
          <span class="e-ico"><Inbox :size="26" aria-hidden="true" /></span>
          <p>{{ emptyText }}</p>
        </div>
        <button v-for="t in pagedTickets" :key="t.id" type="button" class="q-row" :class="{ on: t.id === selectedId, unread: t.unread }" @click="select(t.id)">
          <img v-if="t.user.profile_photo" :src="t.user.profile_photo" class="nm-avatar sm" alt="" />
          <span v-else class="nm-avatar sm">{{ nameInitials(t.user.name) }}</span>
          <span class="q-main">
            <span class="q-top">
              <span class="q-name">{{ t.user.name }}</span>
              <span class="q-time" :class="{ long: waitingLong(t) }" :title="when(t.last_activity_at)">{{ ageText(t) }}</span>
            </span>
            <span class="q-subject"><span v-if="t.unread" class="dot" aria-label="New message"></span>{{ t.subject }}</span>
            <span v-if="t.last_message" class="q-preview">{{ t.last_message.from_support ? 'You: ' : '' }}{{ t.last_message.body }}</span>
            <span class="q-meta">
              <span class="q-tags"><i class="role" :class="t.user.role">{{ ROLE[t.user.role] }}</i><i>{{ t.reference }}</i><i>{{ t.category_label }}</i></span>
              <span v-if="status === 'all'" class="nm-pill" :class="STATUS_PILL[t.status]">{{ t.status_label }}</span>
            </span>
          </span>
        </button>
        <ListPager v-model:page="page" :pages="pages" />
      </section>

      <!-- THE REQUEST -->
      <section class="nm-panel thread">
        <div v-if="!selectedId" class="nm-empty thread-empty">
          <span class="e-ico"><Headset :size="26" aria-hidden="true" /></span>
          <p>Pick a request to read and reply.</p>
        </div>
        <p v-else-if="!ticket" class="nm-muted thread-empty">Loading…</p>
        <template v-else>
          <div class="t-head">
            <button type="button" class="nm-btn-soft nm-btn-sm back" @click="selectedId = null"><ArrowLeft :size="14" aria-hidden="true" /> All requests</button>
            <div class="t-title">
              <div class="t-name">
                <p class="nm-panel-sub t-ids"><i class="sr">{{ ticket.reference }}</i><i class="cat"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z" /><circle cx="7.5" cy="7.5" r="1.5" /></svg> {{ ticket.category_label }}</i><span><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg> Opened {{ when(ticket.created_at) }}</span></p>
                <h2 class="nm-panel-title">{{ ticket.subject }}</h2>
              </div>
              <div class="t-actions">
                <span class="nm-pill" :class="STATUS_PILL[ticket.status]">{{ ticket.status_label }}</span>
                <button v-if="ticket.status !== 'closed'" type="button" class="nm-btn-soft nm-btn-sm" :disabled="busy" @click="act('close')"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg> Close request</button>
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
              <span><i class="role" :class="ticket.user.role">{{ ROLE[ticket.user.role] }}</i><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M22 6l-10 7L2 6" /></svg> <a :href="`mailto:${ticket.user.email}`" class="nm-text-link">{{ ticket.user.email }}</a></span>
            </div>
            <NuxtLink :to="`/users/${ticket.user.id}`" class="nm-btn-soft nm-btn-sm"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg> View user <svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
          </div>
          <div v-if="ticket.appointment || ticket.invoice" class="refs">
            <span class="refs-label">About</span>
            <NuxtLink v-if="ticket.appointment" to="/admin-appointments?view=all" class="ref"><CalendarCheck :size="14" aria-hidden="true" /> {{ ticket.appointment.label }}</NuxtLink>
            <NuxtLink v-if="ticket.invoice" to="/billing-commission" class="ref"><Receipt :size="14" aria-hidden="true" /> {{ ticket.invoice.label }}</NuxtLink>
          </div>

          <!-- a dispute (a no-show, or an in-person visit marked complete): decide it here (the RND's payment waits) -->
          <div v-if="ticket.dispute" class="dispute" :class="{ decided: ticket.dispute.resolved_at }">
            <p class="dispute-title"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l10 18H2z" /><path d="M12 10v4M12 17h.01" /></svg> Consultation dispute</p>
            <p class="dispute-line"><strong>Attendance:</strong> {{ ticket.dispute.attendance }}</p>
            <template v-if="ticket.dispute.resolved_at">
              <p class="dispute-line"><strong>Decided:</strong> {{ ticket.dispute.outcome === 'refunded' ? 'refund approved' : 'rejected, the RND keeps the payment' }}. {{ ticket.dispute.note }}</p>
            </template>
            <template v-else>
              <p class="dispute-line">The RND's payment is on hold until you decide. Both people see your note.</p>
              <label class="nm-label" for="dispute-note">Your decision note</label>
              <textarea id="dispute-note" v-model="decisionNote" class="nm-input" rows="2" maxlength="1000"
                        placeholder="e.g. The call record shows the client joined at 3:01 PM."></textarea>
              <p v-if="decisionError" class="nm-field-error">{{ decisionError }}</p>
              <div class="dispute-actions">
                <button type="button" class="nm-btn-soft" :disabled="busy || decisionNote.trim().length < 10" @click="decide('reject')">Reject dispute</button>
                <button type="button" class="nm-btn-dark" :disabled="busy || decisionNote.trim().length < 10" @click="decide('refund')">Approve and refund</button>
              </div>
              <p class="reply-hint">Approving sends it to Refunds in Billing and commission, where you refund it through PayMongo.</p>
            </template>
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
            <div class="rb">
            <textarea id="sup-reply" v-model="reply" data-allow-emoji class="nm-input" rows="3" maxlength="3000"
              :placeholder="`Reply to ${ticket.user.name.split(' ')[0]}…`"></textarea>
            <div class="reply-foot">
              <p class="reply-hint"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M22 6l-10 7L2 6" /></svg>
                
                {{ ticket.status === 'closed' ? 'Replying reopens the request. ' : '' }}They see it from NutriMatch Support and get an email.
              </p>
              <button type="submit" class="nm-btn-dark" :disabled="busy || reply.trim().length < 2"><Send :size="15" aria-hidden="true" /> {{ busy ? 'Sending…' : 'Send reply' }}</button>
            </div>
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
const decisionNote = ref('')
const decisionError = ref('')
async function decide(decision) {
  busy.value = true
  decisionError.value = ''
  try {
    await post(`/admin/appointments/${ticket.value.dispute.appointment_id}/dispute/`, { decision, note: decisionNote.value.trim() })
    decisionNote.value = ''
    await select(ticket.value.id)
    load()
  } catch (e) {
    decisionError.value = e?.data?.note?.[0] || e?.data?.detail || 'Could not save the decision. Try again.'
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
</script>
<style scoped>
.sup { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; display: inline-block; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

/* ---------- hero ---------- */
.sp-hero { position: relative; overflow: hidden; margin-bottom: 18px; padding: 26px 30px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.sp-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.sp-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 52%, rgba(0, 77, 58, 0.85) 72%, rgba(0, 77, 58, 0.6) 100%); }
.sp-hero-txt { position: relative; z-index: 1; max-width: 620px; }
.sp-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.sp-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.sp-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.sp-sub { margin: 0; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }

/* ---------- tabs + search ---------- */
.sp-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin: 0 0 16px; }
.sp-tabs { display: inline-flex; gap: 4px; max-width: 100%; padding: 5px; border: none; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); overflow-x: auto; scrollbar-width: none; }
.sp-tabs::-webkit-scrollbar { display: none; }
.sp-tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 36px; margin: 0; padding: 0 15px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.sp-tabs .nm-tab .ic { color: #8a9a91; }
.sp-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; }
.sp-tabs .nm-count { min-width: 20px; height: 20px; margin-left: 2px; padding: 0 6px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 700; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.sp-tabs .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.sp-tabs .nm-tab.active .ic { color: #efbf04; }
.sp-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }
.sp-tabs .nm-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.sp-search { position: relative; display: flex; align-items: center; gap: 10px; flex: 0 1 340px; height: 46px; margin: 0; padding: 0 16px; border: none; border-radius: 999px; background: #fff; color: #8a9a91; box-sizing: border-box; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); }
.sp-search:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.sp-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.sp-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }

.desk { display: grid; grid-template-columns: minmax(280px, 340px) minmax(0, 1fr); gap: 18px; align-items: start; }

/* ---------- queue ---------- */
.queue { position: sticky; top: 92px; padding: 8px; border: none; border-radius: 22px; box-shadow: var(--sh); }
.queue-head { display: flex; align-items: center; gap: 8px; margin: 0; padding: 10px 10px 12px; }
.queue-head strong { font-family: 'Playfair Display', serif; font-size: 18px; color: #0e3a2c; }
.queue-head i { min-width: 22px; height: 22px; padding: 0 7px; border-radius: 999px; background: #efbf04; color: #004d3a; font-style: normal; font-size: 12px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.queue-head small { margin-left: auto; font-size: 12px; color: #8a9a91; }
.queue-empty { padding: 28px 10px; }
.sup :deep(.nm-empty) { display: flex; flex-direction: column; align-items: center; gap: 10px; text-align: center; }
.sup :deep(.nm-empty p) { margin: 0; font-size: 14px; font-weight: 600; color: #4a5a52; }
.e-ico { width: 56px; height: 56px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.q-row { display: flex; gap: 12px; align-items: flex-start; width: 100%; padding: 12px; border: 1.5px solid transparent; border-radius: 16px; background: none; font-family: inherit; text-align: left; cursor: pointer; transition: background 0.15s; }
.q-row + .q-row { margin-top: 4px; }
.q-row:hover { background: #f7faf8; }
.q-row.on { border-color: #1f9d55; background: #f1f8f4; box-shadow: 0 0 0 3px rgba(31, 157, 85, 0.1); }
.q-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.nm-avatar.sm { flex-shrink: 0; width: 42px; height: 42px; border-radius: 50%; object-fit: cover; box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; background: #e3efe7; color: #004d3a; font-size: 13px; font-weight: 800; border: 2px solid #fff; box-shadow: 0 0 0 2px #efbf04; }
.q-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.q-top { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.q-name { min-width: 0; font-size: 14.5px; font-weight: 700; color: #0e3a2c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.q-time { flex-shrink: 0; padding: 2px 8px; border-radius: 999px; background: #f3f6f4; font-size: 11px; font-weight: 800; color: #4a5a52; }
.q-time.long, .q-row.on .q-time { background: #fff4d6; color: #8a6500; }
.q-subject { font-size: 14px; color: #22362c; overflow-wrap: anywhere; }
.q-row.unread .q-subject { font-weight: 800; color: #0e3a2c; }
.dot { display: inline-block; width: 8px; height: 8px; margin: 0 6px 1px 0; border-radius: 50%; background: #efbf04; vertical-align: middle; }
.q-preview { font-size: 12.5px; color: #6b7d73; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.q-meta { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-top: 6px; }
.q-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.q-tags i { padding: 2px 8px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px #dce8e0; font-style: normal; font-size: 11px; font-weight: 700; color: #4a5a52; }
.role { padding: 2px 8px; border-radius: 999px; font-style: normal; font-size: 10.5px; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase; background: #fff4d6 !important; box-shadow: none !important; color: #8a6500 !important; }
.role.rnd { background: #e3f4ea !important; color: #1f7a4d !important; }
.q-meta .nm-pill, .t-actions .nm-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.q-meta .nm-pill::before, .t-actions .nm-pill::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.nm-pill.gold { background: #fff4d6; color: #8a6500; }
.nm-pill.green { background: #e3f4ea; color: #1f7a4d; }
.nm-pill.muted { background: #f3f6f4; color: #6b7d73; }
.queue :deep(.nm-pager) { margin: 8px 0 0; padding: 10px 0 2px; }

/* ---------- the request ---------- */
.thread { display: flex; flex-direction: column; min-height: 560px; padding: 0; border: none; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: clip; }
.thread-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 10px; }
.t-head { position: static; margin: 0; padding: 20px 26px; background: #f1f8f4; border-bottom: 1px solid #e3efe7; border-radius: 24px 24px 0 0; }
.back { display: none; margin-bottom: 12px; }
.t-title { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.t-name { flex: 1; min-width: 0; }
.t-ids { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 0 0 6px; font-size: 12.5px; color: #6b7d73; }
.t-ids i { display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; border-radius: 999px; font-style: normal; font-size: 12px; font-weight: 800; }
.t-ids .sr { background: #004d3a; color: #efbf04; letter-spacing: 0.04em; }
.t-ids .cat { background: #eef1fa; color: #2e4a86; }
.t-ids span { display: inline-flex; align-items: center; gap: 5px; }
.t-ids span .ic { color: #1f7a4d; }
.t-name .nm-panel-title { margin: 0; font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.t-actions { display: flex; align-items: center; gap: 10px; }
.t-actions .nm-btn-soft { display: inline-flex; align-items: center; gap: 7px; height: 40px; padding: 0 16px; border: 1px solid #dce8e0; border-radius: 12px; background: #fff; color: #004d3a; font-size: 13.5px; font-weight: 800; }
.who { display: flex; align-items: center; gap: 14px; margin: 16px 26px 0; padding: 14px 16px; border: 1.5px solid #e3ebe6; border-radius: 16px; }
.who .nm-avatar { flex-shrink: 0; width: 46px; height: 46px; border-radius: 50%; object-fit: cover; box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; background: #e3efe7; color: #004d3a; font-weight: 800; border: 2px solid #fff; box-shadow: 0 0 0 2px #efbf04; }
.who-text { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.who-text strong { font-size: 15px; color: #0e3a2c; }
.who-text span { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; font-size: 13px; color: #6b7d73; overflow-wrap: anywhere; }
.who-text span .ic { color: #1f7a4d; }
.who-text .nm-text-link { font-weight: 600; color: #1f7a4d; }
.who > .nm-btn-soft { display: inline-flex; align-items: center; gap: 7px; height: 38px; padding: 0 14px; border: 1px solid #dce8e0; border-radius: 11px; background: #f1f6f2; color: #004d3a; font-size: 13px; font-weight: 800; text-decoration: none; }
.refs { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 12px 26px 0; }
.refs-label { font-size: 12.5px; font-weight: 700; color: #8a9a91; }
.ref { display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 10px; background: #e3efe7; font-size: 13px; font-weight: 700; color: #004d3a; text-decoration: none; overflow-wrap: anywhere; }
.ref:hover { background: #d3e7da; }
.dispute { margin: 14px 26px 0; padding: 14px 16px; border: 1px solid #f6cfcb; border-radius: 16px; background: #fef3f2; }
.dispute.decided { border-color: #e3ebe6; background: #f7faf8; }
.dispute-title { display: flex; align-items: center; gap: 8px; margin: 0 0 8px; font-size: 14.5px; font-weight: 800; color: #8c1d2c; }
.dispute-title .ic { color: #b42318; }
.dispute.decided .dispute-title { color: #0e3a2c; }
.dispute.decided .dispute-title .ic { color: #1f7a4d; }
.dispute-line { margin: 0 0 8px; font-size: 13.5px; color: #3e5046; }
.dispute .nm-input { border: 1.5px solid #c9d8cf; border-radius: 12px; background: #fff; }
.dispute-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; margin-top: 10px; }
.dispute-actions > button { height: 40px; padding: 0 16px; border-radius: 12px; font-weight: 800; }

.msgs { flex: 1; display: flex; flex-direction: column; gap: 12px; padding: 18px 26px; }
.msg-day { display: flex; align-items: center; gap: 12px; margin: 6px 0 4px; font-size: 12px; font-weight: 800; color: #4a5a52; }
.msg-day::before, .msg-day::after { content: ''; flex: 1; height: 1px; background: #e3ebe6; }
.msg-day span { padding: 3px 12px; border-radius: 999px; background: #f1f6f2; }
.msg { align-self: flex-start; max-width: 72%; padding: 12px 16px; border: 1px solid #e3ebe6; border-radius: 4px 18px 18px 18px; background: #f1f6f2; }
.msg.support { align-self: flex-end; border-color: #004d3a; border-radius: 18px 4px 18px 18px; background: #004d3a; }
.msg-who { margin: 0 0 4px; font-size: 12px; font-weight: 700; color: #6b7d73; }
.msg.support .msg-who { color: #efbf04; }
.msg-body { margin: 0; font-size: 14.5px; line-height: 1.55; color: #0e3a2c; white-space: pre-line; overflow-wrap: anywhere; }
.msg.support .msg-body { color: #fff; }

.reply { position: sticky; bottom: 0; margin: 0; padding: 16px 26px 20px; border-top: 1px solid #eef2ef; border-radius: 0 0 24px 24px; background: #f7faf8; }
.rb { border: 1.5px solid #c9d8cf; border-radius: 18px; background: #fff; overflow: hidden; }
.rb:focus-within { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.reply textarea { display: block; width: 100%; box-sizing: border-box; padding: 14px 16px; border: none !important; border-radius: 0; background: #fff; box-shadow: none !important; outline: none; resize: vertical; font-family: inherit; font-size: 14.5px; color: #14261e; }
.reply-foot { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin: 0; padding: 10px 10px 10px 16px; border-top: 1px solid #eef2ef; }
.reply-hint { display: flex; align-items: center; gap: 7px; flex: 1; min-width: 200px; margin: 0; font-size: 12.5px; color: #6b7d73; }
.reply-hint .ic { color: #1f7a4d; }
.reply-foot .nm-btn-dark { display: inline-flex; align-items: center; gap: 7px; height: 40px; padding: 0 18px; border: none; border-radius: 12px; background: #004d3a; color: #fff; font-size: 13.5px; font-weight: 800; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.reply-foot .nm-btn-dark:disabled { opacity: 0.45; box-shadow: none; cursor: not-allowed; }
.reply .nm-field-error { margin: 8px 0 0; }

/* phones: the request opens over the queue */
@media (max-width: 999px) {
  .sp-hero { padding: 20px 18px; border-radius: 22px; }
  .sp-title { font-size: 24px; }
  .sp-plate { width: 180px; height: 180px; right: -60px; top: 20px; transform: none; }
  .sp-hero-txt { max-width: 72%; }
  .sp-tabs { display: flex; width: 100%; border-radius: 16px; }
  .sp-search { flex: 1 1 100%; }
  .desk { grid-template-columns: minmax(0, 1fr); }
  .queue { position: static; }
  .desk.has-open .queue { display: none; }
  .desk:not(.has-open) .thread { display: none; }
  .back { display: inline-flex; }
  .msg { max-width: 92%; }
}
@media (max-width: 760px) {
  .sup { padding-bottom: 110px; }
}
@media (max-width: 640px) {
  .t-head { padding: 16px; }
  .t-name .nm-panel-title { font-size: 21px; }
  .who { margin: 12px 16px 0; flex-wrap: wrap; }
  .who > .nm-btn-soft { width: 100%; justify-content: center; }
  .refs, .dispute { margin-left: 16px; margin-right: 16px; }
  .msgs { padding: 16px; }
  .reply { position: static; padding: 12px 16px 16px; }
  .reply-foot .nm-btn-dark { width: 100%; justify-content: center; }
  .t-actions { width: 100%; }
  .t-actions .nm-pill { margin-right: auto; }
}
</style>