<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-stat-grid">
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><CalendarDays :size="17" /></div>
        <p class="nm-stat-value">{{ summary.today ?? '—' }}</p>
        <p class="nm-stat-label">Consultations today</p>
        <p class="nm-stat-note">{{ summary.next_7_days ?? 0 }} in the next 7 days</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon gold"><Hourglass :size="17" /></div>
        <p class="nm-stat-value">{{ summary.requests ?? '—' }}</p>
        <p class="nm-stat-label">Waiting for the RND</p>
        <p class="nm-stat-note" :class="{ warn: summary.stale_requests }">
          {{ summary.stale_requests ? `${summary.stale_requests} waiting over ${summary.stale_request_hours} hours` : 'None waiting too long' }}
        </p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon gold"><CircleAlert :size="17" /></div>
        <p class="nm-stat-value">{{ summary.unpaid_soon ?? '—' }}</p>
        <p class="nm-stat-label">Unpaid, starting within 24h</p>
        <p class="nm-stat-note">Cancelled automatically if still unpaid at the start</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><CalendarCheck :size="17" /></div>
        <p class="nm-stat-value">{{ summary.completed_7_days ?? '—' }}</p>
        <p class="nm-stat-label">Completed in 7 days</p>
        <p class="nm-stat-note">{{ summary.cancelled_7_days ?? 0 }} cancelled in 7 days</p>
      </div>
    </div>

    <div class="nm-toolbar">
      <div class="nm-tabs">
        <button v-for="t in VIEWS" :key="t.key" class="nm-tab" :class="{ active: view === t.key }" @click="view = t.key">
          {{ t.label }}<span v-if="t.count && summary[t.count]" class="nm-count"> {{ summary[t.count] }}</span>
        </button>
      </div>
      <div class="nm-search">
        <Search :size="15" />
        <input v-model="search" type="search" placeholder="Search client, RND or appointment no." />
      </div>
    </div>

    <div v-if="personFilter" class="nm-note person-filter">
      Showing only {{ personFilter.label }}.
      <button class="nm-panel-link" @click="clearPerson">Show everyone</button>
    </div>

    <div class="nm-panel">
      <div class="filter-row">
        <select v-model="payment" class="nm-select" aria-label="Filter by payment">
          <option value="">Any payment</option>
          <option value="unpaid">Awaiting payment</option>
          <option value="paid">Paid</option>
          <option value="refund_pending">Refund pending</option>
          <option value="refunded">Refunded</option>
        </select>
        <label class="date-field">From <input v-model="dateFrom" type="date" class="nm-input" /></label>
        <label class="date-field">To <input v-model="dateTo" type="date" class="nm-input" :min="dateFrom" /></label>
        <span class="nm-muted count">{{ loading ? 'Loading…' : `${count} appointment${count === 1 ? '' : 's'}` }}</span>
      </div>

      <div v-if="!loading && !rows.length" class="nm-empty">
        <CalendarX :size="28" />
        <p>{{ emptyText }}</p>
      </div>
      <div v-else-if="rows.length" class="nm-table-wrap">
        <table class="nm-table stack">
          <thead>
            <tr>
              <th>When</th>
              <th>Client</th>
              <th>RND</th>
              <th>Status</th>
              <th>Payment</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in rows" :key="a.id" class="clickable" @click="selected = a">
              <td data-label="When">
                <strong>{{ dayText(a.scheduled_at) }}</strong>
                <span class="nm-row-sub" style="display: block">{{ timeText(a.scheduled_at) }} · {{ a.duration_minutes || 60 }} min · {{ a.type_label }}</span>
              </td>
              <td data-label="Client">{{ a.client.name }}</td>
              <td data-label="RND">{{ a.rnd.name }}</td>
              <td data-label="Status">
                <span class="nm-pill" :class="statusOf(a).pill">{{ statusOf(a).label }}</span>
                <span v-if="isStale(a)" class="stale">Waiting {{ ageText(a.created_at) }}</span>
              </td>
              <td data-label="Payment">
                <span v-if="a.payment" class="nm-pill" :class="PAY[a.payment.status]?.pill || 'muted'">{{ PAY[a.payment.status]?.label || a.payment.status }}</span>
                <span v-else class="nm-muted">{{ a.status === 'pending' && new Date(a.scheduled_at) > new Date() ? 'Invoice after confirm' : '—' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="nextPage" style="text-align: center; margin-top: 14px">
        <button class="nm-btn-outline" :disabled="loadingMore" @click="loadMore">{{ loadingMore ? 'Loading…' : `Load more (${count - rows.length} left)` }}</button>
      </div>
    </div>

    <!-- details -->
    <div v-if="selected" class="nm-modal-overlay" @click.self="selected = null">
      <div class="nm-modal detail">
        <div class="detail-head nm-modal-head">
          <div>
            <p class="nm-section-title" style="margin: 0 0 4px">Appointment #{{ selected.id }}</p>
            <h3 class="nm-modal-title" style="margin: 0">{{ dayText(selected.scheduled_at, true) }}</h3>
            <p class="nm-panel-sub">{{ timeText(selected.scheduled_at) }} · {{ selected.duration_minutes || 60 }} min · {{ selected.type_label }}</p>
          </div>
          <button class="close-btn" aria-label="Close" @click="selected = null"><X :size="18" /></button>
        </div>
        <div class="pill-row">
          <span class="nm-pill" :class="statusOf(selected).pill">{{ statusOf(selected).label }}</span>
          <span v-if="selected.payment" class="nm-pill" :class="PAY[selected.payment.status]?.pill || 'muted'">{{ PAY[selected.payment.status]?.label }}</span>
        </div>

        <div class="people">
          <NuxtLink v-for="p in [{ role: 'Client', ...selected.client }, { role: 'RND', ...selected.rnd }]" :key="p.role" :to="`/users/${p.id}`" class="person">
            <img v-if="p.profile_photo" :src="p.profile_photo" class="nm-avatar" alt="" />
            <span v-else class="nm-avatar">{{ nameInitials(p.name) }}</span>
            <span style="min-width: 0">
              <span class="nm-row-sub" style="display: block">{{ p.role }}</span>
              <span class="nm-row-title">{{ p.name }}</span>
              <span class="nm-row-sub" style="display: block">{{ p.email }}</span>
            </span>
          </NuxtLink>
        </div>

        <dl class="nm-dl">
          <div><dt>Booked</dt><dd>{{ dateTime(selected.created_at) }}</dd></div>
          <div>
            <dt>Invoice</dt>
            <dd v-if="selected.payment">
              <NuxtLink to="/billing-commission" class="nm-text-link">INV-{{ String(selected.payment.invoice_id).padStart(4, '0') }}</NuxtLink>
              · {{ peso(selected.payment.amount) }}
            </dd>
            <dd v-else class="muted">{{ selected.status === 'pending' ? 'Issued when the RND confirms' : 'None' }}</dd>
          </div>
          <div v-if="selected.payment?.paid_at"><dt>Paid</dt><dd>{{ dateTime(selected.payment.paid_at) }}</dd></div>
          <div v-if="selected.completed_at"><dt>Completed</dt><dd>{{ dateTime(selected.completed_at) }}</dd></div>
          <div v-if="selected.notes"><dt>Client's note</dt><dd>{{ selected.notes }}</dd></div>
          <div v-if="selected.cancellation_reason"><dt>Cancellation reason</dt><dd>{{ selected.cancellation_reason }}</dd></div>
        </dl>

        <div v-if="canCancel(selected)" class="nm-modal-actions">
          <button class="nm-btn-danger" @click="openCancel"><Ban :size="14" /> Cancel appointment</button>
        </div>
      </div>
    </div>

    <!-- cancel -->
    <div v-if="cancelling" class="nm-modal-overlay" style="z-index: 310" @click.self="busy ? null : (cancelling = false)">
      <div class="nm-modal">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="busy ? null : (cancelling = false)"><X :size="18" aria-hidden="true" /></button>
        <h3 class="nm-modal-title">Cancel this appointment?</h3>
        <p class="nm-modal-text">
          {{ selected.client.name }} and RND {{ selected.rnd.name }} will both be notified with your reason.
          <template v-if="selected.payment?.status === 'paid'"><br><strong>The client paid {{ peso(selected.payment.amount) }}</strong> — it will be marked for refund and show up in Billing → Refunds.</template>
          <template v-else-if="selected.payment?.status === 'unpaid'"><br>The unpaid invoice will be voided.</template>
        </p>
        <label class="nm-label" for="cancel-reason">Reason</label>
        <textarea id="cancel-reason" v-model="reason" class="nm-input" rows="3" maxlength="500"
          placeholder="e.g. The RND has a family emergency and can't attend." />
        <p v-if="cancelError" class="nm-field-error">{{ cancelError }}</p>
        <p v-else class="nm-hint">At least 10 characters — both people will see this.</p>
        <div class="nm-modal-actions">
          <button class="nm-btn-outline" :disabled="busy" @click="cancelling = false">Keep it</button>
          <button class="nm-btn-danger solid" :disabled="busy" @click="confirmCancel">{{ busy ? 'Cancelling…' : 'Cancel appointment' }}</button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import {
  Ban, CalendarCheck, CalendarDays, CalendarX, CheckCircle2, CircleAlert, Hourglass, Search, X,
} from 'lucide-vue-next'

const { get, post } = useApi()
const route = useRoute()

const VIEWS = [
  { key: 'upcoming', label: 'Upcoming', count: 'upcoming' },
  { key: 'requests', label: 'Waiting for RND', count: 'requests' },
  { key: 'past', label: 'Past' },
  { key: 'cancelled', label: 'Cancelled' },
  { key: 'all', label: 'All' },
]
const PAY = {
  unpaid: { label: 'Awaiting payment', pill: 'gold' },
  paid: { label: 'Paid', pill: 'green' },
  refund_pending: { label: 'Refund pending', pill: 'red' },
  refunded: { label: 'Refunded', pill: 'blue' },
  cancelled: { label: 'Voided', pill: 'muted' },
}

const view = ref(VIEWS.some(v => v.key === route.query.view) ? route.query.view : 'upcoming')
const search = ref('')
const payment = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const person = ref({ client: route.query.client || '', rnd: route.query.rnd || '' })

const summary = ref({})
const rows = ref([])
const count = ref(0)
const nextPage = ref(null)
const loading = ref(true)
const loadingMore = ref(false)
const error = ref('')
const toast = ref('')
const selected = ref(null)

const personFilter = computed(() => {
  if (!person.value.client && !person.value.rnd) return null
  const first = rows.value[0]
  if (person.value.client) return { label: first ? `${first.client.name}'s appointments` : "this client's appointments" }
  return { label: first ? `RND ${first.rnd.name}'s appointments` : "this RND's appointments" }
})
function clearPerson() {
  person.value = { client: '', rnd: '' }
  navigateTo({ query: {} }, { replace: true })
}

const emptyText = computed(() => ({
  upcoming: 'No upcoming appointments.',
  requests: 'No booking requests waiting for an RND.',
  past: 'No past appointments.',
  cancelled: 'No cancelled appointments.',
}[view.value] || 'No appointments match these filters.'))

function params(page) {
  const q = { view: view.value, page }
  if (search.value.trim()) q.search = search.value.trim()
  if (payment.value) q.payment = payment.value
  if (dateFrom.value) q.date_from = dateFrom.value
  if (dateTo.value) q.date_to = dateTo.value
  if (person.value.client) q.client = person.value.client
  if (person.value.rnd) q.rnd = person.value.rnd
  return q
}

let requestId = 0
async function load() {
  const id = ++requestId
  loading.value = true
  error.value = ''
  try {
    const r = await get('/admin/appointments/', { query: params(1) })
    if (id !== requestId) return
    rows.value = r.results
    count.value = r.count
    nextPage.value = r.next ? 2 : null
  } catch {
    if (id === requestId) error.value = 'Could not load appointments. Please refresh the page.'
  } finally {
    if (id === requestId) loading.value = false
  }
}
async function loadMore() {
  loadingMore.value = true
  try {
    const r = await get('/admin/appointments/', { query: params(nextPage.value) })
    rows.value.push(...r.results)
    nextPage.value = r.next ? nextPage.value + 1 : null
  } finally {
    loadingMore.value = false
  }
}
async function loadSummary() {
  try {
    summary.value = await get('/admin/appointments/summary/')
  } catch {
    summary.value = {}
  }
}

let searchTimer
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 350)
})
watch([view, payment, dateFrom, dateTo, person], load, { deep: true })
watch(view, v => navigateTo({ query: { ...route.query, view: v } }, { replace: true }))
onMounted(() => {
  load()
  loadSummary()
})

/* display */
function statusOf(a) {
  const past = new Date(a.scheduled_at) < new Date()
  if (a.status === 'pending') return past ? { label: 'Expired — RND never confirmed', pill: 'muted' } : { label: 'Waiting for RND', pill: 'gold' }
  if (a.status === 'confirmed') {
    return past ? { label: 'Not marked complete', pill: 'muted' } : { label: 'Confirmed', pill: 'green' }
  }
  if (a.status === 'completed') return { label: 'Completed', pill: 'blue' }
  return { label: 'Cancelled', pill: 'red' }
}
function isStale(a) {
  return a.status === 'pending' && new Date(a.scheduled_at) > new Date() && Date.now() - new Date(a.created_at) > (summary.value.stale_request_hours || 24) * 3600000
}
function ageText(v) {
  const h = Math.floor((Date.now() - new Date(v)) / 3600000)
  return h >= 48 ? `${Math.floor(h / 24)} days` : `${h} hours`
}
const PH = { timeZone: 'Asia/Manila' }
function dayText(v, long = false) {
  return new Date(v).toLocaleDateString('en-PH', { ...PH, weekday: long ? 'long' : 'short', month: long ? 'long' : 'short', day: 'numeric', year: 'numeric' })
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

/* cancel */
const cancelling = ref(false)
const reason = ref('')
const cancelError = ref('')
const busy = ref(false)
function openCancel() {
  reason.value = ''
  cancelError.value = ''
  cancelling.value = true
}
async function confirmCancel() {
  cancelError.value = ''
  if (reason.value.trim().length < 10) {
    cancelError.value = 'Explain why in at least 10 characters — both people will see this.'
    return
  }
  busy.value = true
  try {
    const updated = await post(`/admin/appointments/${selected.value.id}/cancel/`, { reason: reason.value.trim() })
    cancelling.value = false
    selected.value = null
    toast.value = updated.payment?.status === 'refund_pending'
      ? 'Appointment cancelled — the payment is now in Billing → Refunds.'
      : 'Appointment cancelled — both people were notified.'
    setTimeout(() => { toast.value = '' }, 3500)
    load()
    loadSummary()
  } catch (e) {
    cancelError.value = apiError(e, 'Could not cancel this appointment. Please try again.')
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.filter-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; margin-bottom: 14px; }
.date-field { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: 600; color: #4a5a4a; }
.date-field .nm-input { width: auto; padding: 8px 10px; }
.count { margin-left: auto; }
.stale { display: block; font-size: 0.7rem; color: #b8860b; font-weight: 600; margin-top: 3px; }
.person-filter { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.detail { max-width: 520px; }
.detail-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.close-btn { background: none; border: none; color: #8a9a8a; cursor: pointer; padding: 4px; }
.pill-row { display: flex; gap: 6px; flex-wrap: wrap; margin: 12px 0 16px; }
.people { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px; }
.person { display: flex; gap: 10px; align-items: center; border: 1px solid #eceeec; border-radius: 10px; padding: 10px; text-decoration: none; min-width: 0; }
.person:hover { border-color: #c7d6ca; background: #fafbfa; }
@media (max-width: 640px) {
  .people { grid-template-columns: 1fr; }
  .date-field { flex: 1; }
  .date-field .nm-input { flex: 1; min-width: 0; }
  .filter-row .nm-select { width: 100%; }
  .count { margin-left: 0; }
}
</style>
