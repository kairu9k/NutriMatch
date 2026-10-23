<template>
  <div class="nm-page">
    <div class="head">
      <p class="nm-page-sub">Your consultations, sorted by what needs you. All times are Philippine time.</p>
      <NuxtLink to="/profile-settings?tab=availability" class="nm-panel-link"><CalendarClock :size="14" /> Availability</NuxtLink>
    </div>

    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <div v-if="loading" class="nm-panel"><p class="nm-muted">Loading appointments…</p></div>

    <template v-else-if="board">
      <div v-if="patientFilter" class="nm-note filter-note">
        Showing only <strong>{{ patientFilterName }}</strong>.
        <NuxtLink to="/appointments" class="nm-panel-link">Show everyone</NuxtLink>
      </div>

      <div class="nm-toolbar">
        <div class="nm-tabs" role="tablist" aria-label="Appointment lists">
          <button v-for="t in TABS" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" role="tab"
                  :aria-selected="tab === t.key" @click="setTab(t.key)">
            {{ t.label }}<span v-if="t.key !== 'history'" class="nm-count">{{ list(t.key).length }}</span>
          </button>
        </div>
        <label v-if="tab === 'history'" class="nm-search">
          <Search :size="16" />
          <input v-model="search" type="search" placeholder="Search by patient" aria-label="Search history" />
        </label>
      </div>

      <div class="nm-panel appt-list">
        <!-- ============ REQUESTS ============ -->
        <template v-if="tab === 'requests'">
          <p class="tab-intro">Check each request and their screening before you confirm. Confirming sends them an invoice to pay before the consultation.</p>
          <div v-if="!list('requests').length" class="nm-empty"><Inbox :size="26" /><p>No booking requests right now.</p></div>
          <article v-for="a in list('requests')" :key="a.id" class="row">
            <DateBlock :at="a.scheduled_at" tone="gold" />
            <div class="row-main">
              <p class="who">
                <NuxtLink :to="`/client-detail/${a.relationship_id}`" class="name-link">{{ a.client.name }}</NuxtLink>
                <span class="nm-pill" :class="a.returning ? 'blue' : 'muted'">{{ a.returning ? 'Returning patient' : 'New patient' }}</span>
              </p>
              <p class="nm-row-sub">{{ timeRange(a) }}, {{ a.type_label.toLowerCase() }}, {{ a.duration_minutes }} min</p>
              <p v-if="a.time_passed" class="flag critical"><OctagonAlert :size="13" /> The requested time has passed. Decline it so they can book again.</p>
              <p v-else-if="a.starts_in_hours < 24" class="flag warning"><AlertTriangle :size="13" /> Starts in {{ hoursText(a.starts_in_hours) }}. Answer soon.</p>
              <div class="chips">
                <template v-if="a.screening.submitted">
                  <span v-if="a.screening.nrs_score != null" class="chip" :class="{ risk: a.screening.nrs_score >= 3 }">NRS-2002 {{ a.screening.nrs_score }}{{ a.screening.nrs_risk ? `, ${a.screening.nrs_risk.toLowerCase()}` : '' }}</span>
                  <span v-if="a.screening.bmi_category" class="chip">BMI {{ a.screening.bmi?.toFixed(1) }}, {{ a.screening.bmi_category }}</span>
                  <span v-for="c in a.screening.conditions" :key="c" class="chip">{{ c }}</span>
                  <span v-if="a.screening.allergies.length" class="chip allergy">Allergy: {{ a.screening.allergies.join(', ') }}</span>
                </template>
                <span v-else class="chip risk">No screening yet, so it can't be confirmed</span>
              </div>
              <p v-if="a.notes" class="client-note">{{ a.notes }}</p>
            </div>
            <div class="row-actions">
              <button v-if="!a.time_passed" type="button" class="nm-btn-dark nm-btn-sm" @click="openReview(a)">Review &amp; confirm</button>
              <button type="button" class="nm-btn-outline nm-btn-sm" @click="openReason(a, 'decline')">Decline</button>
            </div>
          </article>
        </template>

        <!-- ============ UPCOMING ============ -->
        <template v-else-if="tab === 'upcoming'">
          <div v-if="!list('upcoming').length" class="nm-empty"><CalendarDays :size="26" /><p>No confirmed consultations coming up.</p></div>
          <section v-for="g in upcomingByDay" :key="g.key" class="day">
            <p class="day-label">{{ g.label }}</p>
            <article v-for="a in g.items" :key="a.id" class="row">
              <span class="time">{{ clock(a.scheduled_at) }}<small>{{ a.duration_minutes }} min</small></span>
              <div class="row-main">
                <p class="who">
                  <NuxtLink :to="`/client-detail/${a.relationship_id}`" class="name-link">{{ a.client.name }}</NuxtLink>
                  <span v-if="a.payment?.status === 'paid'" class="nm-pill green">Paid</span>
                  <span v-else class="nm-pill muted">Not paid yet</span>
                </p>
                <p class="nm-row-sub with-icon">
                  <component :is="TYPE_ICONS[a.type]" :size="13" class="ti" /> {{ a.type_label }}, until {{ clock(a.ends_at) }}
                </p>
                <p v-if="a.type === 'in_person'" class="nm-row-sub addr with-icon">
                  <MapPin :size="13" class="ti" /> {{ a.clinic_address || 'No clinic address set. Add it in Profile Settings.' }}
                </p>
                <p v-if="a.payment?.status !== 'paid'" class="nm-row-sub">They pay before it starts. If it's still unpaid at {{ clock(a.scheduled_at) }}, it's cancelled automatically.</p>
              </div>
              <div class="row-actions">
                <template v-if="inWindow(a)">
                  <NuxtLink v-if="a.type === 'video'" :to="`/consultation-room/${a.id}`" class="nm-btn-dark nm-btn-sm"><Video :size="14" /> Join</NuxtLink>
                </template>
                <span v-else-if="a.type !== 'in_person'" class="opens">Opens {{ clock(a.join_opens_at) }}</span>
                <button type="button" class="nm-btn-outline nm-btn-sm" @click="openReason(a, 'cancel')">Cancel</button>
              </div>
            </article>
          </section>
        </template>

        <!-- ============ TO COMPLETE ============ -->
        <template v-else-if="tab === 'to_complete'">
          <p class="tab-intro">These consultations have ended. Mark each one complete so it's closed, and your share starts its 3-day hold before payout.</p>
          <p v-if="justCompleted" class="done-note">
            <CheckCircle2 :size="15" /> {{ justCompleted.client.first_name }}'s consultation is complete. Next:
            <NuxtLink :to="`/client-detail/${justCompleted.relationship_id}?tab=ncp`" class="nm-panel-link">Finish the NCP record</NuxtLink>
          </p>
          <div v-if="!list('to_complete').length" class="nm-empty"><CheckCircle2 :size="26" /><p>Nothing to close — all caught up.</p></div>
          <article v-for="a in list('to_complete')" :key="a.id" class="row">
            <DateBlock :at="a.scheduled_at" tone="muted" />
            <div class="row-main">
              <p class="who"><NuxtLink :to="`/client-detail/${a.relationship_id}`" class="name-link">{{ a.client.name }}</NuxtLink></p>
              <p class="nm-row-sub">{{ timeRange(a) }}, {{ a.type_label.toLowerCase() }}, ended {{ ago(a.ends_at) }}</p>
            </div>
            <div class="row-actions">
              <button v-if="a.payment && a.payment.status !== 'paid'" type="button" class="nm-btn-outline nm-btn-sm" disabled title="Can't complete an unpaid consultation">Waiting for payment</button>
              <button v-else type="button" class="nm-btn-dark nm-btn-sm" @click="completeTarget = a">Mark complete</button>
            </div>
          </article>
        </template>

        <!-- ============ HISTORY ============ -->
        <template v-else>
          <div v-if="!history.length" class="nm-empty"><History :size="26" /><p>{{ search ? 'No consultations match that name.' : 'No past consultations yet.' }}</p></div>
          <article v-for="a in history" :key="a.id" class="row past">
            <DateBlock :at="a.scheduled_at" tone="muted" />
            <div class="row-main">
              <p class="who">
                <NuxtLink :to="`/client-detail/${a.relationship_id}`" class="name-link">{{ a.client.name }}</NuxtLink>
                <span class="nm-pill" :class="a.status === 'completed' ? 'green' : 'muted'">{{ a.status === 'completed' ? 'Completed' : 'Cancelled' }}</span>
                <span v-if="a.payment && ['refund_pending', 'refunded'].includes(a.payment.status)" class="nm-pill red">{{ a.payment.status === 'refunded' ? 'Refunded' : 'Refund pending' }}</span>
              </p>
              <p class="nm-row-sub">{{ timeRange(a) }}, {{ a.type_label.toLowerCase() }}{{ a.payment?.status === 'paid' ? `, ${peso(a.payment.amount)}` : '' }}</p>
              <p v-if="a.status === 'cancelled' && a.cancellation_reason" class="nm-row-sub">Reason: {{ a.cancellation_reason }}</p>
            </div>
            <div v-if="a.status === 'completed'" class="row-actions">
              <button type="button" class="nm-btn-outline nm-btn-sm" @click="summaryId = a.id"><FileText :size="14" /> Summary</button>
            </div>
          </article>
        </template>
      </div>
    </template>

    <!-- REVIEW & CONFIRM (full screening) -->
    <div v-if="review" class="nm-modal-overlay" @click.self="review = null">
      <div class="nm-modal wide review-modal" role="dialog" aria-modal="true" aria-labelledby="review-title">
        <button type="button" class="modal-x" aria-label="Close" @click="review = null"><X :size="18" /></button>
        <h2 id="review-title" class="nm-modal-title">{{ review.appt.client.name }}</h2>
        <p class="nm-modal-text">{{ longWhen(review.appt.scheduled_at) }}, {{ review.appt.type_label.toLowerCase() }}, {{ review.appt.duration_minutes }} min</p>
        <p v-if="review.loading" class="nm-muted">Loading screening…</p>
        <p v-else-if="review.error" class="nm-error">{{ review.error }}</p>
        <template v-else-if="review.data">
          <dl class="facts">
            <div><dt>Age and sex</dt><dd>{{ review.data.client.age ?? '—' }}, {{ SEX[review.data.client.sex] || '—' }}</dd></div>
            <div><dt>Conditions</dt><dd>{{ listText(review.data.client.medical_conditions) }}</dd></div>
            <div><dt>Food allergies</dt><dd :class="{ warn: review.data.client.allergies?.length }">{{ listText(review.data.client.allergies) }}</dd></div>
            <div><dt>Diet</dt><dd>{{ listText(review.data.client.dietary_restrictions) }}</dd></div>
            <div><dt>Goals</dt><dd>{{ listText(review.data.client.health_goals) }}</dd></div>
          </dl>
          <p v-if="review.data.appointment.notes" class="client-note">{{ review.data.appointment.notes }}</p>
          <template v-if="review.data.screening">
            <p class="section-k">Screening, submitted {{ shortDate(review.data.screening.created_at) }}</p>
            <div class="results">
              <div><strong>{{ review.data.screening.bmi ?? '—' }}</strong><span>BMI, {{ review.data.screening.bmi_category || '—' }}</span></div>
              <div><strong>{{ whole(review.data.screening.bmr_kcal) }}</strong><span>BMR kcal/day</span></div>
              <div><strong>{{ whole(review.data.screening.tdee_kcal) }}</strong><span>TDEE kcal/day</span></div>
              <div :class="{ risk: (review.data.screening.nrs_score ?? 0) >= 3 }"><strong>{{ review.data.screening.nrs_score ?? '—' }}</strong><span>NRS-2002, {{ RISK[review.data.screening.nrs_risk] || '—' }}</span></div>
            </div>
            <dl class="facts">
              <div><dt>Height and weight</dt><dd>{{ review.data.screening.height_cm }} cm, {{ review.data.screening.weight_kg }} kg</dd></div>
              <div><dt>Activity</dt><dd>{{ ACTIVITY[review.data.screening.activity_level] || '—' }}</dd></div>
              <div><dt>Symptoms</dt><dd>{{ review.data.screening.symptoms || 'None reported' }}</dd></div>
            </dl>
            <p class="nm-hint">Confirming sends {{ review.appt.client.first_name }} an invoice for your fee. If it's still unpaid at the start time, the booking is cancelled and the slot opens again.</p>
          </template>
          <p v-else class="nm-note">They haven't submitted a pre-consultation screening yet, so this booking can't be confirmed.</p>
          <p v-if="review.actionError" class="nm-field-error">{{ review.actionError }}</p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" @click="openReason(review.appt, 'decline')">Decline</button>
            <button type="button" class="nm-btn-dark" :disabled="busy || !review.data.screening" @click="confirmBooking">{{ busy ? 'Confirming…' : 'Confirm booking' }}</button>
          </div>
        </template>
      </div>
    </div>

    <!-- DECLINE / CANCEL WITH A REASON -->
    <div v-if="reason" class="nm-modal-overlay" @click.self="reason = null">
      <form class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="reason-title" @submit.prevent="submitReason">
        <h2 id="reason-title" class="nm-modal-title">{{ reason.kind === 'decline' ? 'Decline this request?' : 'Cancel this consultation?' }}</h2>
        <p class="nm-modal-text">
          {{ reason.appt.client.name }}, {{ longWhen(reason.appt.scheduled_at) }}.
          <template v-if="reason.kind === 'decline'">They're notified with your reason and can book another time.</template>
          <template v-else-if="reason.appt.payment?.status === 'paid'">They already paid, so their invoice goes to <strong>refund pending</strong> and the NutriMatch admin refunds them.</template>
          <template v-else>Their unpaid invoice is voided and they're notified with your reason.</template>
        </p>
        <label class="nm-label" for="reason-text">Reason (sent to the client)</label>
        <textarea id="reason-text" v-model="reason.text" class="nm-input" rows="3" maxlength="500"
                  :placeholder="reason.kind === 'decline' ? 'e.g. I\'m fully booked that day. Please choose another time.' : 'e.g. I have a family emergency. Please book again any day next week.'"></textarea>
        <p v-if="reason.error" class="nm-field-error">{{ reason.error }}</p>
        <p v-else class="nm-hint">At least 10 characters.</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="reason = null">Keep it</button>
          <button type="submit" class="nm-btn-danger solid" :disabled="busy || reason.text.trim().length < 10">
            {{ busy ? 'Saving…' : reason.kind === 'decline' ? 'Decline request' : 'Cancel consultation' }}
          </button>
        </div>
      </form>
    </div>

    <!-- MARK COMPLETE -->
    <div v-if="completeTarget" class="nm-modal-overlay" @click.self="completeTarget = null">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="complete-title">
        <h2 id="complete-title" class="nm-modal-title">Mark this consultation complete?</h2>
        <p class="nm-modal-text">
          {{ completeTarget.client.name }}, {{ longWhen(completeTarget.scheduled_at) }}.
          <template v-if="completeTarget.payment">They paid {{ peso(completeTarget.payment.amount) }}. Your share posts 3 days after today.</template>
          <template v-else>This was booked before pay-first, so completing sends them an invoice.</template>
          This can't be undone.
        </p>
        <p v-if="completeError" class="nm-field-error">{{ completeError }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="completeTarget = null">Not yet</button>
          <button type="button" class="nm-btn-dark" :disabled="busy" @click="completeNow">{{ busy ? 'Completing…' : 'Mark complete' }}</button>
        </div>
      </div>
    </div>
    <ConsultationSummaryModal v-if="summaryId" :appointment-id="summaryId" role="rnd" @close="summaryId = null" />
  </div>
</template>

<script setup>
import {
  AlertTriangle, CalendarClock, CalendarDays, CheckCircle2, FileText, History, Inbox, MapPin, MessageSquare, OctagonAlert, Search, Users, Video, X,
} from 'lucide-vue-next'

const { get, patch } = useApi()
const route = useRoute()
const router = useRouter()
const now = useNow()

const board = ref(null)
const loading = ref(true)
const error = ref('')
const busy = ref(false)
const search = ref('')

async function load() {
  error.value = ''
  try {
    board.value = await get('/rnd/appointments/board/')
  } catch {
    error.value = 'Could not load your appointments.'
  } finally {
    loading.value = false
  }
}

/* ---------- tabs + ?relationship= filter (from a patient chart) ---------- */
const TABS = [
  { key: 'requests', label: 'Requests' },
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'to_complete', label: 'To complete' },
  { key: 'history', label: 'History' },
]
const tab = ref(TABS.some(t => t.key === route.query.tab) ? route.query.tab : null)
function setTab(k) {
  tab.value = k
  router.replace({ query: { ...route.query, tab: k } })
}
onMounted(async () => {
  await load()
  if (!tab.value && board.value) tab.value = board.value.requests.length ? 'requests' : board.value.to_complete.length && !board.value.upcoming.length ? 'to_complete' : 'upcoming'
})
const patientFilter = computed(() => route.query.relationship ? String(route.query.relationship) : null)
const patientFilterName = computed(() => {
  for (const k of ['requests', 'upcoming', 'to_complete', 'history']) {
    const hit = board.value?.[k].find(a => String(a.relationship_id) === patientFilter.value)
    if (hit) return hit.client.name
  }
  return 'this patient'
})
function list(k) {
  const rows = board.value?.[k] || []
  return patientFilter.value ? rows.filter(a => String(a.relationship_id) === patientFilter.value) : rows
}
const history = computed(() => {
  const q = search.value.trim().toLowerCase()
  return list('history').filter(a => !q || a.client.name.toLowerCase().includes(q))
})

/* ---------- time (PH) ---------- */
const PH = { timeZone: 'Asia/Manila' }
const phDate = v => new Date(v).toLocaleDateString('en-CA', PH)
const clock = v => new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
const longWhen = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
function dayLabel(v) {
  const d = phDate(v)
  if (d === phDate(now.value)) return 'Today'
  if (d === phDate(now.value + 86400000)) return 'Tomorrow'
  return new Date(v).toLocaleDateString('en-PH', { ...PH, weekday: 'long', month: 'long', day: 'numeric' })
}
const timeRange = a => `${new Date(a.scheduled_at).toLocaleDateString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric' })}, ${clock(a.scheduled_at)}–${clock(a.ends_at)}`
function hoursText(h) {
  if (h < 1) return `${Math.max(1, Math.round(h * 60))} minutes`
  return `${Math.round(h)} hour${Math.round(h) === 1 ? '' : 's'}`
}
function ago(v) {
  const mins = Math.round((now.value - new Date(v).getTime()) / 60000)
  if (mins < 60) return `${mins} min ago`
  if (mins < 1440) return `${Math.round(mins / 60)} h ago`
  return `${Math.round(mins / 1440)} day${Math.round(mins / 1440) === 1 ? '' : 's'} ago`
}
const inWindow = a => now.value >= new Date(a.join_opens_at).getTime() && now.value <= new Date(a.join_closes_at).getTime()
const upcomingByDay = computed(() => {
  const groups = []
  for (const a of list('upcoming')) {
    const key = phDate(a.scheduled_at)
    let g = groups.find(x => x.key === key)
    if (!g) groups.push(g = { key, label: dayLabel(a.scheduled_at), items: [] })
    g.items.push(a)
  }
  return groups
})

const TYPE_ICONS = { video: Video, chat: MessageSquare, in_person: Users }
const SEX = { male: 'Male', female: 'Female' }
const RISK = { no_risk: 'No risk', at_risk: 'At risk', high_risk: 'High risk' }
const ACTIVITY = { sedentary: 'Sedentary', lightly_active: 'Lightly active', moderately_active: 'Moderately active', very_active: 'Very active', extra_active: 'Extra active' }
const listText = l => (l?.length ? l.join(', ') : 'None')
const whole = v => (v == null ? '—' : Math.round(Number(v)).toLocaleString('en-PH'))

const DateBlock = defineComponent({
  props: { at: String, tone: String },
  setup(props) {
    return () => h('span', { class: ['date-block', props.tone] }, [
      h('span', { class: 'db-day' }, new Date(props.at).toLocaleDateString('en-PH', { ...PH, day: 'numeric' })),
      h('span', { class: 'db-mon' }, new Date(props.at).toLocaleDateString('en-PH', { ...PH, month: 'short' })),
    ])
  },
})

/* ---------- review & confirm ---------- */
const review = ref(null)
async function openReview(a) {
  review.value = { appt: a, loading: true, data: null, error: '', actionError: '' }
  try {
    review.value.data = await get(`/rnd/appointments/${a.id}/screening/`)
  } catch (e) {
    review.value.error = apiError(e, 'Could not load the screening.')
  } finally {
    review.value.loading = false
  }
}
async function confirmBooking() {
  busy.value = true
  review.value.actionError = ''
  try {
    await patch(`/rnd/appointments/${review.value.appt.id}/confirm/`)
    review.value = null
    await load()
  } catch (e) {
    review.value.actionError = apiError(e, 'Could not confirm this booking.')
  } finally {
    busy.value = false
  }
}

/* ---------- decline / cancel ---------- */
const reason = ref(null)
function openReason(a, kind) {
  review.value = null
  reason.value = { appt: a, kind, text: '', error: '' }
}
async function submitReason() {
  busy.value = true
  reason.value.error = ''
  try {
    await patch(`/rnd/appointments/${reason.value.appt.id}/cancel/`, { reason: reason.value.text.trim() })
    reason.value = null
    await load()
  } catch (e) {
    reason.value.error = apiError(e, 'Could not save this.')
  } finally {
    busy.value = false
  }
}

/* ---------- mark complete ---------- */
const summaryId = ref(null)
const completeTarget = ref(null)
const completeError = ref('')
const justCompleted = ref(null)
async function completeNow() {
  busy.value = true
  completeError.value = ''
  try {
    await patch(`/rnd/appointments/${completeTarget.value.id}/complete/`)
    justCompleted.value = completeTarget.value
    completeTarget.value = null
    await load()
  } catch (e) {
    completeError.value = apiError(e, 'Could not complete this consultation.')
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; flex-wrap: wrap; margin: 0 0 14px; }
.nm-page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }
.head .nm-panel-link { display: inline-flex; align-items: center; gap: 5px; }

.appt-list { box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.filter-note { margin-bottom: 14px; }

.tab-intro { font-size: 0.82rem; color: #6a7a6a; margin: 0 0 6px; }
.row { display: flex; gap: 14px; align-items: flex-start; padding: 14px 0; border-top: 1px solid #f0f2f0; }
.row:first-of-type, .tab-intro + .row, .day-label + .row { border-top: none; }
.row.past { opacity: 0.9; }
.row-main { flex: 1; min-width: 0; }
.row-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.who { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 0 0 2px; font-weight: 700; color: #1a3a1a; font-size: 0.92rem; }
.name-link { color: inherit; text-decoration: none; }
.name-link:hover { text-decoration: underline; }
.ti { color: #8a9a8a; flex-shrink: 0; }
.with-icon { display: flex; align-items: center; gap: 5px; }
.addr { overflow-wrap: anywhere; }
.flag { display: flex; align-items: center; gap: 5px; margin: 6px 0 0; font-size: 0.78rem; font-weight: 600; }
.flag.critical { color: #a12525; }
.flag.warning { color: #9a6a00; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.chip { font-size: 0.72rem; font-weight: 600; padding: 3px 9px; border-radius: 10px; background: #f2f5f2; color: #3a4a3a; }
.chip.allergy { background: #fdecec; color: #a12525; }
.chip.risk { background: #fdecec; color: #a12525; }
.client-note { margin: 8px 0 0; padding-left: 10px; border-left: 2px solid #e3e9e4; font-size: 0.82rem; color: #4a5a4a; overflow-wrap: anywhere; }

.day + .day { margin-top: 10px; }
.day-label { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0 0 2px; }
.time { width: 76px; white-space: nowrap; flex-shrink: 0; font-weight: 700; color: #1a3a1a; font-size: 0.9rem; font-variant-numeric: tabular-nums; display: flex; flex-direction: column; }
.time small { font-weight: 500; font-size: 0.72rem; color: #8a9a8a; }
.opens { font-size: 0.78rem; color: #6a7a6a; }
.done-note { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; font-size: 0.84rem; color: #1f6f46; font-weight: 600; margin: 4px 0 10px; }

:deep(.date-block) { width: 46px; height: 50px; border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; background: #eef3ec; }
:deep(.date-block.gold) { background: #fdf1d6; }
:deep(.date-block.muted) { background: #f4f5f4; }
:deep(.db-day) { font-size: 1.05rem; font-weight: 700; color: #1a3a1a; line-height: 1; }
:deep(.db-mon) { font-size: 0.72rem; font-weight: 600; color: #6a7a6a; }

/* modals */
.nm-modal.wide { max-width: 620px; }
.review-modal { position: relative; }
.review-modal .nm-modal-title { padding-right: 36px; }
.modal-x { position: absolute; top: 14px; right: 14px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: none; background: none; border-radius: 8px; color: #6a7a6a; cursor: pointer; }
.modal-x:hover { background: #f2f5f2; color: #1a3a1a; }
.modal-x:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 16px; margin: 0 0 12px; }
.facts dt { font-size: 0.72rem; color: #8a9a8a; margin: 0; }
.facts dd { margin: 0; font-size: 0.85rem; font-weight: 600; color: #1a3a1a; overflow-wrap: anywhere; }
.facts dd.warn { color: #a12525; }
.section-k { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 16px 0 8px; }
.results { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-bottom: 12px; }
.results div { background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 10px; display: flex; flex-direction: column; min-width: 0; }
.results div.risk { background: #fdecec; border-color: #f3c9c9; }
.results strong { font-size: 1.05rem; color: #1a3a1a; font-variant-numeric: tabular-nums; }
.results span { font-size: 0.7rem; color: #6a7a6a; }

@media (max-width: 760px) {
  .row { flex-wrap: wrap; }
  .row-actions { width: 100%; justify-content: flex-start; padding-left: 60px; }
  .results { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 420px) {
  .facts { grid-template-columns: minmax(0, 1fr); }
  .row-actions { padding-left: 0; }
}
</style>
