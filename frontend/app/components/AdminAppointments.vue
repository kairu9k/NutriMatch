<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- AT A GLANCE: one divided panel; each figure opens the list it counts -->
    <div class="nm-panel glance">
      <button type="button" class="fig" @click="jump('upcoming')">
        <strong>{{ summary.today ?? '—' }}</strong>
        <span class="fig-label">Consultations today</span>
        <span class="fig-note">{{ summary.next_7_days ?? 0 }} in the next 7 days</span>
      </button>
      <button type="button" class="fig" @click="jump('requests')">
        <strong>{{ summary.requests ?? '—' }}</strong>
        <span class="fig-label">Waiting for the RND</span>
        <span class="fig-note" :class="{ warn: summary.stale_requests }">
          {{ summary.stale_requests ? `${summary.stale_requests} waiting over ${summary.stale_request_hours} hours` : 'None waiting too long' }}
        </span>
      </button>
      <button type="button" class="fig" @click="jump('upcoming', 'unpaid')">
        <strong :class="{ warn: summary.unpaid_soon }">{{ summary.unpaid_soon ?? '—' }}</strong>
        <span class="fig-label">Unpaid, starting within 24 hours</span>
        <span class="fig-note">Cancelled on its own if still unpaid at the start</span>
      </button>
      <button type="button" class="fig" @click="jump('past')">
        <strong>{{ summary.completed_7_days ?? '—' }}</strong>
        <span class="fig-label">Completed in 7 days</span>
        <span class="fig-note">{{ summary.cancelled_7_days ?? 0 }} cancelled in 7 days</span>
      </button>
    </div>

    <div class="nm-toolbar">
      <div class="nm-tabs">
        <button v-for="t in VIEWS" :key="t.key" type="button" class="nm-tab" :class="{ active: view === t.key }" @click="view = t.key">
          {{ t.label }}<span v-if="t.count && summary[t.count]" class="nm-count"> {{ summary[t.count] }}</span>
        </button>
      </div>
      <div class="appt-tools">
        <select v-model="payment" class="nm-select" aria-label="Filter by payment">
          <option value="">Any payment</option>
          <option value="unpaid">Awaiting payment</option>
          <option value="paid">Paid</option>
          <option value="refund_pending">Refund pending</option>
          <option value="refunded">Refunded</option>
        </select>
        <div class="nm-search">
          <Search :size="15" aria-hidden="true" />
          <input v-model="search" type="search" placeholder="Search client, RND or appointment no." />
        </div>
      </div>
    </div>

    <p v-if="personFilter" class="nm-note plain-note person-filter">
      Showing only {{ personFilter.label }}.
      <button type="button" class="nm-btn-soft nm-btn-sm" @click="clearPerson">Show everyone</button>
    </p>

    <!-- THE AGENDA: grouped by Philippine day, time on the left -->
    <div ref="listTop" class="nm-panel agenda-panel">
      <div class="agenda-head">
        <div class="dates">
          <label class="date-field">From <input v-model="dateFrom" type="date" class="nm-input" /></label>
          <label class="date-field">To <input v-model="dateTo" type="date" class="nm-input" :min="dateFrom" /></label>
          <button v-if="dateFrom || dateTo" type="button" class="nm-btn-soft nm-btn-sm" @click="dateFrom = ''; dateTo = ''">Clear dates</button>
        </div>
        <span class="nm-muted count">{{ loading ? 'Loading…' : `${count} appointment${count === 1 ? '' : 's'}` }}</span>
      </div>

      <div v-if="!loading && !rows.length" class="nm-empty">
        <CalendarX :size="28" aria-hidden="true" />
        <p>{{ emptyText }}</p>
      </div>

      <section v-for="d in days" :key="d.key" class="day">
        <h3 class="day-title">
          <span>{{ d.label }}</span>
          <span class="day-count">{{ d.items.length }}</span>
        </h3>
        <button v-for="a in d.items" :key="a.id" type="button" class="appt" :class="{ attention: attentionOf(a) }" @click="selected = a">
          <span class="appt-time">
            <strong>{{ timeText(a.scheduled_at) }}</strong>
            <small>{{ a.duration_minutes || 60 }} min</small>
          </span>
          <span class="appt-people">
            <img v-if="a.client.profile_photo" :src="a.client.profile_photo" class="nm-avatar sm" alt="" />
            <span v-else class="nm-avatar sm">{{ nameInitials(a.client.name) }}</span>
            <span class="appt-names">
              <span class="appt-client">{{ a.client.name }}</span>
              <span class="appt-rnd">with RND {{ a.rnd.name }}</span>
            </span>
          </span>
          <span class="appt-format">
            <component :is="a.type === 'in_person' ? MapPin : Video" :size="14" aria-hidden="true" />
            {{ a.type === 'in_person' ? 'In person' : a.type === 'chat' ? 'Chat' : 'Video call' }}
          </span>
          <span class="appt-state">
            <span class="nm-pill" :class="statusOf(a).pill">{{ statusOf(a).label }}</span>
            <span v-if="a.payment" class="nm-pill" :class="PAY[a.payment.status]?.pill || 'muted'">{{ PAY[a.payment.status]?.label || a.payment.status }}</span>
            <span v-if="attentionOf(a)" class="appt-flag">{{ attentionOf(a) }}</span>
          </span>
          <ChevronRight :size="16" class="appt-go" aria-hidden="true" />
        </button>
      </section>

      <ListPager v-model:page="page" :pages="pages" />
    </div>

    <!-- DETAILS -->
    <div v-if="selected" class="nm-modal-overlay" @click.self="selected = null">
      <div class="nm-modal detail" role="dialog" aria-modal="true" aria-labelledby="appt-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="selected = null"><X :size="18" aria-hidden="true" /></button>
        <h3 id="appt-title" class="nm-modal-title">{{ dayText(selected.scheduled_at, true) }}</h3>
        <p class="detail-sub">
          {{ timeText(selected.scheduled_at) }}, {{ selected.duration_minutes || 60 }} min,
          {{ selected.type === 'in_person' ? 'in person' : selected.type === 'chat' ? 'chat' : 'video call' }}. Appointment #{{ selected.id }}
        </p>

        <div class="people">
          <NuxtLink v-for="p in [{ role: 'Client', ...selected.client }, { role: 'RND', ...selected.rnd }]" :key="p.role" :to="`/users/${p.id}`" class="person">
            <img v-if="p.profile_photo" :src="p.profile_photo" class="nm-avatar" alt="" />
            <span v-else class="nm-avatar">{{ nameInitials(p.name) }}</span>
            <span class="person-text">
              <span class="nm-row-title">{{ p.name }}</span>
              <span class="nm-row-sub">{{ p.role }}, {{ p.email }}</span>
            </span>
            <ChevronRight :size="15" class="person-go" aria-hidden="true" />
          </NuxtLink>
        </div>

        <!-- what has happened so far: a real sequence -->
        <ol class="track">
          <li v-for="s in steps" :key="s.key" :class="s.state">
            <span class="dot" aria-hidden="true"><Check v-if="s.state === 'done'" :size="11" /><X v-else-if="s.state === 'stopped'" :size="11" /></span>
            <span class="step-text">
              <strong>{{ s.label }}</strong>
              <span>{{ s.detail }}</span>
            </span>
          </li>
        </ol>

        <p v-if="selected.cancellation_reason" class="nm-note plain-note reason">{{ selected.cancellation_reason }}</p>

        <dl class="nm-dl facts">
          <div>
            <dt>Invoice</dt>
            <dd v-if="selected.payment">
              <NuxtLink to="/billing-commission" class="nm-text-link">INV-{{ String(selected.payment.invoice_id).padStart(4, '0') }}</NuxtLink>,
              {{ peso(selected.payment.amount) }}
            </dd>
            <dd v-else class="muted">{{ selected.status === 'pending' ? 'Issued when the RND confirms' : 'None' }}</dd>
          </div>
          <div>
            <dt>Payment</dt>
            <dd v-if="selected.payment">{{ PAY[selected.payment.status]?.label || selected.payment.status }}</dd>
            <dd v-else class="muted">None yet</dd>
          </div>
          <div v-if="selected.notes" class="wide"><dt>Client's note</dt><dd>{{ selected.notes }}</dd></div>
        </dl>

        <p v-if="startedOpen(selected)" class="nm-hint started">This consultation has started, so it can't be cancelled here. The RND closes it from the consultation room.</p>

        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="selected = null">Close</button>
          <button v-if="canCancel(selected)" type="button" class="nm-btn-danger solid" @click="openCancel"><Ban :size="14" aria-hidden="true" /> Cancel appointment</button>
        </div>
      </div>
    </div>

    <!-- CANCEL: a last resort, the button waits 3 seconds -->
    <div v-if="cancelling" class="nm-modal-overlay" style="z-index: 310" @click.self="busy ? null : closeCancel()">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="cancel-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="busy ? null : closeCancel()"><X :size="18" aria-hidden="true" /></button>
        <h3 id="cancel-title" class="nm-modal-title">Cancel this appointment?</h3>
        <p class="nm-modal-text">
          Only cancel when the client or the RND can't do it themselves, for example after a support request.
          {{ selected.client.name }} and RND {{ selected.rnd.name }} will both be notified with your reason.
        </p>
        <p v-if="selected.payment?.status === 'paid'" class="nm-note">
          <strong>The client paid {{ peso(selected.payment.amount) }}.</strong> It will be marked for refund and listed under Refunds in Billing and commission.
        </p>
        <p v-else-if="selected.payment?.status === 'unpaid'" class="nm-note plain-note">The unpaid invoice will be voided.</p>
        <label class="nm-label" for="cancel-reason">Reason</label>
        <textarea id="cancel-reason" v-model="reason" class="nm-input" rows="3" maxlength="500"
          placeholder="For example: the RND has a family emergency and can't attend." />
        <p v-if="cancelError" class="nm-field-error">{{ cancelError }}</p>
        <p v-else class="nm-hint">At least 10 characters. Both people will see this.</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" :disabled="busy" @click="closeCancel">Keep it</button>
          <button type="button" class="nm-btn-danger solid" :disabled="busy || lockLeft > 0" @click="confirmCancel">
            {{ busy ? 'Cancelling…' : lockLeft > 0 ? `Cancel appointment (${lockLeft})` : 'Cancel appointment' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { Ban, CalendarX, Check, CheckCircle2, ChevronRight, MapPin, Search, Video, X } from 'lucide-vue-next'

const { get, post } = useApi()
const route = useRoute()

const PER_PAGE = 20
const VIEWS = [
  { key: 'upcoming', label: 'Upcoming', count: 'upcoming' },
  { key: 'requests', label: 'Waiting for RND', count: 'requests' },
  { key: 'past', label: 'Past' },
  { key: 'cancelled', label: 'Cancelled' },
  { key: 'all', label: 'All' },
]
// states in green/grey, things an admin may need to act on in gold
const PAY = {
  unpaid: { label: 'Awaiting payment', pill: 'gold' },
  paid: { label: 'Paid', pill: 'green' },
  refund_pending: { label: 'Refund pending', pill: 'gold' },
  refunded: { label: 'Refunded', pill: 'muted' },
  cancelled: { label: 'Voided', pill: 'muted' },
}

const view = ref(VIEWS.some(v => v.key === route.query.view) ? route.query.view : 'upcoming')
const search = ref('')
const payment = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const person = ref({ client: route.query.client || '', rnd: route.query.rnd || '' })
const page = ref(1)

const summary = ref({})
const rows = ref([])
const count = ref(0)
const pages = computed(() => Math.max(1, Math.ceil(count.value / PER_PAGE)))
const loading = ref(true)
const error = ref('')
const toast = ref('')
const selected = ref(null)
const listTop = ref(null)

const personFilter = computed(() => {
  if (!person.value.client && !person.value.rnd) return null
  const first = rows.value[0]
  if (person.value.client) return { label: first ? `${first.client.name}'s appointments` : "this client's appointments" }
  return { label: first ? `RND ${first.rnd.name}'s appointments` : "this RND's appointments" }
})
function clearPerson() {
  person.value = { client: '', rnd: '' }
  navigateTo({ query: { view: view.value } }, { replace: true })
}
function jump(v, pay = '') {
  view.value = v
  payment.value = pay
}

const emptyText = computed(() => {
  if (search.value.trim() || payment.value || dateFrom.value || dateTo.value) return 'No appointments match these filters.'
  return {
    upcoming: 'No upcoming appointments.',
    requests: 'No booking requests waiting for an RND.',
    past: 'No past appointments.',
    cancelled: 'No cancelled appointments.',
  }[view.value] || 'No appointments yet.'
})

function params() {
  const q = { view: view.value, page: page.value, page_size: PER_PAGE }
  if (search.value.trim()) q.search = search.value.trim()
  if (payment.value) q.payment = payment.value
  if (dateFrom.value) q.date_from = dateFrom.value
  if (dateTo.value) q.date_to = dateTo.value
  if (person.value.client) q.client = person.value.client
  if (person.value.rnd) q.rnd = person.value.rnd
  return q
}

let requestId = 0
async function load({ quiet = false } = {}) {
  const id = ++requestId
  if (!quiet) {
    loading.value = true
    error.value = ''
  }
  try {
    const r = await get('/admin/appointments/', { query: params() })
    if (id !== requestId) return
    rows.value = r.results
    count.value = r.count
    // a quiet refresh can leave the page past the end (rows cancelled meanwhile)
    if (page.value > pages.value) page.value = pages.value
  } catch {
    if (id === requestId && !quiet) error.value = 'Could not load appointments. Refresh the page to try again.'
  } finally {
    if (id === requestId) loading.value = false
  }
}
async function loadSummary() {
  try {
    summary.value = await get('/admin/appointments/summary/')
  } catch {
    summary.value = {}
  }
}
useAutoRefresh(() => Promise.all([loadSummary(), load({ quiet: true })]))

let searchTimer
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value === 1 ? load() : (page.value = 1) }, 350)
})
// a new filter starts again at page 1 (the page watcher then loads)
watch([view, payment, dateFrom, dateTo, person], () => { page.value === 1 ? load() : (page.value = 1) }, { deep: true })
watch(page, () => {
  load()
  listTop.value?.scrollIntoView({ block: 'start', behavior: 'smooth' })
})
watch(view, v => navigateTo({ query: { ...route.query, view: v } }, { replace: true }))
onMounted(() => {
  load()
  loadSummary()
})

/* display */
const PH = { timeZone: 'Asia/Manila' }
const dayKey = v => new Date(v).toLocaleDateString('en-CA', PH)
function dayLabel(v) {
  const key = dayKey(v)
  const today = dayKey(Date.now())
  const md = new Date(v).toLocaleDateString('en-PH', { ...PH, month: 'long', day: 'numeric' })
  if (key === today) return `Today, ${md}`
  if (key === dayKey(Date.now() + 86400000)) return `Tomorrow, ${md}`
  if (key === dayKey(Date.now() - 86400000)) return `Yesterday, ${md}`
  return dayText(v, true, key.slice(0, 4) !== today.slice(0, 4))
}
// rows arrive sorted by the server; group neighbours that share a day
const days = computed(() => {
  const out = []
  for (const a of rows.value) {
    const key = dayKey(a.scheduled_at)
    const last = out[out.length - 1]
    if (last && last.key === key) last.items.push(a)
    else out.push({ key, label: dayLabel(a.scheduled_at), items: [a] })
  }
  return out
})

function statusOf(a) {
  const past = new Date(a.scheduled_at) < new Date()
  if (a.status === 'pending') return past ? { label: 'Expired', pill: 'muted' } : { label: 'Waiting for RND', pill: 'gold' }
  if (a.status === 'confirmed') {
    if (!past) return { label: 'Confirmed', pill: 'green' }
    const end = new Date(a.scheduled_at).getTime() + (a.duration_minutes || 60) * 60000
    return Date.now() < end ? { label: 'In progress', pill: 'green' } : { label: 'Not marked complete', pill: 'gold' }
  }
  if (a.status === 'completed') return { label: 'Completed', pill: 'muted' }
  return { label: 'Cancelled', pill: 'muted' }
}
// one short gold line when a row needs a look
function attentionOf(a) {
  const now = Date.now()
  const start = new Date(a.scheduled_at).getTime()
  if (a.status === 'pending' && start > now && now - new Date(a.created_at) > (summary.value.stale_request_hours || 24) * 3600000) {
    return `Waiting ${ageText(a.created_at)} for the RND`
  }
  if (a.status === 'confirmed' && a.payment?.status === 'unpaid' && start > now && start - now < 86400000) {
    return `Unpaid, starts in ${untilText(start - now)}`
  }
  return ''
}
function ageText(v) {
  const h = Math.floor((Date.now() - new Date(v)) / 3600000)
  return h >= 48 ? `${Math.floor(h / 24)} days` : `${h} hours`
}
function untilText(ms) {
  const m = Math.max(1, Math.round(ms / 60000))
  return m < 60 ? `${m} min` : `${Math.round(m / 60)} h`
}
function dayText(v, long = false, withYear = true) {
  return new Date(v).toLocaleDateString('en-PH', {
    ...PH, weekday: long ? 'long' : 'short', month: long ? 'long' : 'short', day: 'numeric', ...(withYear ? { year: 'numeric' } : {}),
  })
}
function timeText(v) {
  return new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
}
function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}
function canCancel(a) {
  return ['pending', 'confirmed'].includes(a.status) && new Date(a.scheduled_at) > new Date()
}
function startedOpen(a) {
  return a.status === 'confirmed' && new Date(a.scheduled_at) <= new Date()
}

// Booked, confirmed, paid, then completed or cancelled
const steps = computed(() => {
  const a = selected.value
  if (!a) return []
  const pay = a.payment
  const cancelled = a.status === 'cancelled'
  const out = [{ key: 'booked', label: 'Booked by the client', detail: dateTime(a.created_at), state: 'done' }]
  const confirmed = !!pay?.issued_at && a.status !== 'pending'
  out.push({
    key: 'confirmed', label: 'Confirmed by the RND',
    detail: confirmed ? dateTime(pay.issued_at) : cancelled ? 'Never confirmed' : 'Not yet',
    state: confirmed ? 'done' : cancelled ? 'stopped' : 'todo',
  })
  if (confirmed || !cancelled) {
    const paid = !!pay?.paid_at
    out.push({
      key: 'paid', label: 'Paid',
      detail: paid ? dateTime(pay.paid_at) : cancelled ? 'Never paid' : 'Due before the start',
      state: paid ? 'done' : cancelled ? 'stopped' : 'todo',
    })
  }
  if (cancelled) out.push({ key: 'end', label: 'Cancelled', detail: dateTime(a.updated_at), state: 'stopped' })
  else out.push({ key: 'end', label: 'Completed', detail: a.completed_at ? dateTime(a.completed_at) : 'Not yet', state: a.completed_at ? 'done' : 'todo' })
  return out
})

/* cancel */
const cancelling = ref(false)
const reason = ref('')
const cancelError = ref('')
const busy = ref(false)
const lockLeft = ref(0)
let lockTimer
function openCancel() {
  reason.value = ''
  cancelError.value = ''
  cancelling.value = true
  lockLeft.value = 3
  clearInterval(lockTimer)
  lockTimer = setInterval(() => {
    lockLeft.value -= 1
    if (lockLeft.value <= 0) clearInterval(lockTimer)
  }, 1000)
}
function closeCancel() {
  clearInterval(lockTimer)
  cancelling.value = false
}
onBeforeUnmount(() => clearInterval(lockTimer))
async function confirmCancel() {
  cancelError.value = ''
  if (reason.value.trim().length < 10) {
    cancelError.value = 'Explain why in at least 10 characters. Both people will see this.'
    return
  }
  busy.value = true
  try {
    const updated = await post(`/admin/appointments/${selected.value.id}/cancel/`, { reason: reason.value.trim() })
    closeCancel()
    selected.value = null
    toast.value = updated.payment?.status === 'refund_pending'
      ? 'Appointment cancelled. The payment is now under Refunds in Billing and commission.'
      : 'Appointment cancelled. Both people were notified.'
    setTimeout(() => { toast.value = '' }, 3500)
    load()
    loadSummary()
  } catch (e) {
    cancelError.value = apiError(e, 'Could not cancel this appointment. Try again.')
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
/* at a glance: one divided panel */
.glance { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); padding: 0; margin-bottom: 20px; overflow: hidden; }
.fig {
  display: flex; flex-direction: column; gap: 2px; padding: 16px 18px; text-align: left; min-width: 0;
  background: #fff; border: 0; border-left: 1px solid #d9e3dc; cursor: pointer; font-family: inherit; color: #1a3a1a;
}
.fig:first-child { border-left: none; }
.fig:hover { background: #f7faf8; }
.fig:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.fig strong { font-family: 'Playfair Display', serif; font-size: 1.6rem; line-height: 1.2; }
.fig strong.warn { color: #b8860b; }
.fig-label { font-size: 0.82rem; font-weight: 600; color: #4a5a4a; }
.fig-note { font-size: 0.75rem; color: #8a9a8a; line-height: 1.4; }
.fig-note.warn { color: #b8860b; font-weight: 600; }

.appt-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.appt-tools .nm-select { width: auto; min-width: 160px; }
.person-filter { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

/* the agenda */
.agenda-panel { scroll-margin-top: 16px; }
.agenda-head { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; justify-content: space-between; padding-bottom: 14px; border-bottom: 1px solid #d9e3dc; }
.dates { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.date-field { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: 600; color: #4a5a4a; }
.date-field .nm-input { width: auto; padding: 8px 10px; }

.day + .day { margin-top: 6px; }
.day-title {
  display: flex; align-items: baseline; gap: 8px; margin: 18px 0 4px; font-family: inherit;
  font-size: 0.86rem; font-weight: 700; color: #0a4a37;
}
.day-count { font-size: 0.74rem; font-weight: 600; color: #8a9a8a; }

.appt {
  display: grid; grid-template-columns: 84px minmax(0, 1.6fr) minmax(0, 0.8fr) minmax(0, 1.4fr) 16px;
  align-items: center; gap: 14px; width: 100%; padding: 12px 10px 12px 12px; margin: 0;
  background: #fff; border: 0; border-top: 1px solid #edf1ee; border-left: 3px solid transparent;
  text-align: left; cursor: pointer; font-family: inherit; color: #1a3a1a;
}
.day-title + .appt { border-top-color: transparent; }
.appt:hover { background: #f7faf8; }
.appt:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.appt.attention { border-left-color: #D4A017; }
.appt-time { display: flex; flex-direction: column; border-right: 1px solid #d9e3dc; padding-right: 12px; }
.appt-time strong { font-size: 0.92rem; font-variant-numeric: tabular-nums; white-space: nowrap; }
.appt-time small { font-size: 0.74rem; color: #8a9a8a; }
.appt-people { display: flex; align-items: center; gap: 10px; min-width: 0; }
.nm-avatar.sm { width: 32px; height: 32px; font-size: 0.72rem; }
.appt-names { display: flex; flex-direction: column; min-width: 0; }
.appt-client { font-size: 0.88rem; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.appt-rnd { font-size: 0.78rem; color: #6a7a6a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.appt-format { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; color: #4a5a4a; }
.appt-format svg { color: #3f9a6b; flex-shrink: 0; }
.appt-state { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.appt-flag { flex-basis: 100%; font-size: 0.72rem; font-weight: 600; color: #b8860b; }
.appt-go { color: #9aaa9a; }

/* details */
.detail { max-width: 560px; }
.detail-sub { margin: 4px 0 16px; font-size: 0.86rem; color: #6a7a6a; }
.people { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 18px; }
.person { display: flex; gap: 10px; align-items: center; border: 1px solid #d9e3dc; border-radius: 12px; padding: 10px 12px; text-decoration: none; min-width: 0; }
.person:hover { background: #f7faf8; }
.person-text { display: flex; flex-direction: column; min-width: 0; flex: 1; }
.person-go { color: #9aaa9a; flex-shrink: 0; }

.track { list-style: none; margin: 0 0 16px; padding: 0; }
.track li { position: relative; display: flex; gap: 12px; padding: 0 0 14px; }
.track li:last-child { padding-bottom: 0; }
.track li:not(:last-child)::before { content: ''; position: absolute; left: 9px; top: 20px; bottom: 0; width: 2px; background: #d9e3dc; }
.track li.done:not(:last-child)::before { background: #9fcfb3; }
.dot {
  width: 20px; height: 20px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center;
  border: 2px solid #c9d6cd; background: #fff; color: #fff;
}
.track li.done .dot { background: #1f8f5c; border-color: #1f8f5c; }
.track li.stopped .dot { background: #8a9a8a; border-color: #8a9a8a; }
.step-text { display: flex; flex-direction: column; gap: 1px; padding-top: 1px; }
.step-text strong { font-size: 0.86rem; color: #1a3a1a; }
.step-text span { font-size: 0.78rem; color: #6a7a6a; }
.track li.todo .step-text strong { color: #6a7a6a; font-weight: 600; }
.reason { margin-bottom: 16px; }
.facts .wide { grid-column: 1 / -1; }
.started { margin: 14px 0 0; }

@media (max-width: 900px) {
  .glance { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fig:nth-child(3) { border-left: none; }
  .fig:nth-child(n + 3) { border-top: 1px solid #d9e3dc; }
  .appt { grid-template-columns: 76px minmax(0, 1fr) 16px; row-gap: 8px; }
  .appt-format, .appt-state { grid-column: 2; }
  .appt-go { grid-column: 3; grid-row: 1; }
}
@media (max-width: 640px) {
  .appt-tools { width: 100%; }
  .appt-tools .nm-search { flex: 1 1 100%; order: -1; max-width: none; }
  .appt-tools .nm-select { flex: 1; }
  .dates { width: 100%; }
  .date-field { flex: 1; }
  .date-field .nm-input { flex: 1; min-width: 0; }
  .people { grid-template-columns: 1fr; }
  .fig { padding: 12px 14px; }
  .fig strong { font-size: 1.35rem; }
  .appt { grid-template-columns: 64px minmax(0, 1fr) 16px; gap: 10px; padding-left: 8px; }
  .appt-time { padding-right: 8px; }
}
</style>
