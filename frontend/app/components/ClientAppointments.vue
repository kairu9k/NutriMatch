<template>
  <!-- Client "My Appointments" (Appointments.vue renders this for clients;
       the RND view lives in Appointments.vue). Styled with the same tokens
       as the client dashboard / Profile Settings. -->
  <div class="appointments-page">
    <div class="page-header">
      <div>
       
        <p class="page-sub">Your upcoming consultations and past visits.</p>
      </div>
      <NuxtLink :to="bookLink" class="nm-btn-dark"><CalendarPlus :size="15" aria-hidden="true" /> Book a consultation</NuxtLink>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="isLoading" class="placeholder-text">Loading appointments…</p>

    <template v-else-if="!errorMessage">
      <!-- ============ UPCOMING ============ -->
      <section class="section">
        <h2 class="section-title">Upcoming <span class="count">{{ upcoming.length }}</span></h2>

        <div v-if="!upcoming.length" class="panel empty-state">
          <CalendarDays :size="24" class="empty-icon" />
          <p>No upcoming consultations.</p>
          <p class="empty-sub">{{ activeRnd ? `Book a follow-up with RND ${activeRnd.first_name} ${activeRnd.last_name} when you're ready.` : 'Find an RND and book your first consultation.' }}</p>
          <NuxtLink :to="bookLink" class="nm-btn-soft">{{ activeRnd ? 'Book a consultation' : 'Find an RND' }}</NuxtLink>
        </div>

        <article v-for="appt in upcoming" :key="appt.id" class="panel up-card">
          <div class="up-head">
            <div>
              <p class="up-day">{{ appt.dayLabel }}</p>
              <p class="up-time">{{ appt.startClock }} <span class="up-to">to {{ appt.endClock }}</span></p>
            </div>
            <span class="dot-status" :class="appt.tone"><span class="dot" aria-hidden="true" />{{ appt.statusLabel }}<template v-if="appt.phase === 'confirmed' && appt.payment?.status === 'paid'">, paid</template></span>
          </div>
          <p class="up-with">
            <component :is="appt.typeIcon" :size="15" aria-hidden="true" /> {{ appt.typeLabel }} with
            <NuxtLink :to="`/rnd-profile-view/${appt.rnd.id}`" class="up-rnd">RND {{ appt.rnd.name }}</NuxtLink>
          </p>
          <p v-if="appt.notes" class="appt-notes"><span>Your notes:</span> {{ appt.notes }}</p>
          <p v-if="appt.hint" class="appt-hint" :class="{ 'hint-due': appt.phase === 'payment_due' }">{{ appt.hint }}</p>

          <div class="appt-actions">
            <button
              v-if="appt.phase === 'payment_due'" class="nm-btn-dark" type="button"
              :disabled="payingId === appt.payment.invoice_id" @click="payNow(appt)"
            >
              <CreditCard :size="14" aria-hidden="true" /> {{ payingId === appt.payment.invoice_id ? 'Opening checkout…' : `Pay ₱${money(appt.payment.amount)}` }}
            </button>
            <NuxtLink v-if="appt.canJoinVideo" :to="`/consultation-room/${appt.id}`" class="nm-btn-dark"><Video :size="14" aria-hidden="true" /> Join video call</NuxtLink>
            <!-- Join window: opens 15 min before the start (see join_opens_at). -->
            <button v-if="appt.opensLater" class="nm-btn-dark" type="button" disabled :title="`Opens ${appt.opensLabel}`">
              <Video :size="14" aria-hidden="true" /> Join opens {{ appt.opensLabel }}
            </button>
            <NuxtLink v-if="appt.canMessage" :to="`/messages?relationship=${appt.relationshipId}`" class="nm-btn-soft"><MessageSquare :size="14" aria-hidden="true" /> Message RND</NuxtLink>
            <button v-if="appt.canCancel" class="nm-btn-danger solid cancel-btn" type="button" :disabled="busyId === appt.id" @click="openCancel(appt)">
              {{ appt.status === 'pending' ? 'Cancel request' : 'Cancel' }}
            </button>
          </div>
          <p v-if="actionError[appt.id]" class="inline-error">{{ actionError[appt.id] }}</p>
        </article>
      </section>

      <!-- ============ HISTORY ============ -->
      <section class="section">
        <div class="section-head">
          <h2 class="section-title">History <span class="count">{{ history.length }}</span></h2>
          <div v-if="history.length" class="filter-tabs" role="tablist" aria-label="Filter history">
            <button
              v-for="f in historyFilters" :key="f.key" type="button" role="tab"
              class="filter-tab" :class="{ active: historyFilter === f.key }" :aria-selected="historyFilter === f.key"
              @click="historyFilter = f.key"
            >
              {{ f.label }}<span v-if="f.key !== 'all'" class="tab-count">{{ historyCounts[f.key] }}</span>
            </button>
          </div>
        </div>

        <div v-if="!history.length" class="panel empty-state">
          <ClipboardList :size="24" class="empty-icon" />
          <p>No past appointments yet.</p>
        </div>
        <div v-else class="panel history-panel">
          <p v-if="!filteredHistory.length" class="empty-note">{{ historyFilters.find(f => f.key === historyFilter).empty }}</p>
          <template v-for="g in historyGroups" :key="g.label">
            <h3 class="month-head">{{ g.label }}</h3>
            <div v-for="appt in g.items" :key="appt.id" class="h-row">
              <p class="h-date">{{ appt.shortDate }}</p>
              <div class="h-main">
                <p class="h-title">{{ appt.typeLabel }}, {{ appt.startClock }}</p>
                <p class="h-sub">RND {{ appt.rnd.name }}</p>
                <p v-if="appt.status === 'cancelled' && appt.cancellationReason" class="h-sub">Reason: {{ appt.cancellationReason }}</p>
                <p v-if="appt.hint" class="h-sub">{{ appt.hint }}</p>
                <p v-if="appt.payment?.status === 'refund_pending'" class="refund-note">{{ refundMessage(money(appt.payment.amount), appt.payment.method) }}</p>
                <p v-if="appt.status === 'completed'" class="h-links">
                  <button type="button" class="nm-btn-soft nm-btn-sm" @click="summaryId = appt.id">View summary</button>
                  <button v-if="!appt.review" type="button" class="nm-btn-soft nm-btn-sm" @click="openReview(appt)">Leave a review</button>
                </p>
              </div>
              <div class="h-side">
                <span class="dot-status" :class="appt.tone"><span class="dot" aria-hidden="true" />{{ appt.statusLabel }}</span>
                <span v-if="appt.review" class="review-stars" :aria-label="`You rated ${appt.review.rating} out of 5`">
                  <Star v-for="n in 5" :key="n" :size="13" :fill="n <= appt.review.rating ? '#D4A017' : 'none'" :color="n <= appt.review.rating ? '#D4A017' : '#d5dad5'" aria-hidden="true" />
                </span>
                <template v-else-if="appt.payment">
                  <span v-if="appt.payment.status === 'paid'" class="h-money">Paid ₱{{ money(appt.payment.amount) }}</span>
                  <NuxtLink v-else-if="appt.payment.status === 'unpaid'" to="/invoices-billing" class="h-money link">Unpaid ₱{{ money(appt.payment.amount) }}, pay now</NuxtLink>
                  <span v-else-if="appt.payment.status === 'refund_pending'" class="h-money">Refund pending ₱{{ money(appt.payment.amount) }}</span>
                  <span v-else-if="appt.payment.status === 'refunded'" class="h-money">Refunded ₱{{ money(appt.payment.amount) }}</span>
                </template>
              </div>
            </div>
          </template>
        </div>
      </section>
    </template>

    <!-- CANCEL MODAL -->
    <div v-if="cancelTarget" class="nm-modal-overlay" @click.self="closeCancel">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="cancel-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="closeCancel"><X :size="18" aria-hidden="true" /></button>
        <h3 id="cancel-title" class="nm-modal-title">{{ cancelTarget.status === 'pending' ? 'Cancel this booking request?' : 'Cancel this appointment?' }}</h3>
        <p class="modal-text">
          {{ cancelTarget.typeLabel }} consultation with RND {{ cancelTarget.rnd.name }} on {{ cancelTarget.longDate }}, {{ cancelTarget.timeRange }}.
          RND {{ cancelTarget.rnd.firstName }} will be notified.
        </p>
        <p v-if="cancelTarget.payment?.status === 'paid'" class="modal-note">
          You paid ₱{{ money(cancelTarget.payment.amount) }} for this consultation. {{ refundMessage(money(cancelTarget.payment.amount), cancelTarget.payment.method) }}
        </p>
        <p v-else-if="cancelTarget.payment?.status === 'unpaid'" class="modal-note">Its unpaid invoice is voided, so there's nothing to pay.</p>
        <label class="field-label" for="cancel-reason">Reason <span class="optional">(optional)</span></label>
        <textarea id="cancel-reason" v-model="cancelReason" rows="3" maxlength="500" class="field-input" placeholder="Let your RND know why…"></textarea>
        <p class="char-count">{{ cancelReason.length }}/500</p>
        <p v-if="cancelError" class="inline-error">{{ cancelError }}</p>
        <div class="nm-modal-actions">
          <button class="nm-btn-soft" type="button" :disabled="isCancelling" @click="closeCancel">Keep it</button>
          <button class="nm-btn-danger solid" type="button" :disabled="isCancelling" @click="confirmCancel">{{ isCancelling ? 'Cancelling…' : 'Yes, cancel' }}</button>
        </div>
      </div>
    </div>

    <!-- REVIEW MODAL -->
    <div v-if="reviewTarget" class="nm-modal-overlay" @click.self="closeReview">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="review-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="closeReview"><X :size="18" aria-hidden="true" /></button>
        <h3 id="review-title" class="nm-modal-title">Rate your consultation</h3>
        <p class="modal-text">With RND {{ reviewTarget.rnd.name }} on {{ reviewTarget.longDate }}.</p>
        <div class="star-row" role="radiogroup" aria-label="Rating">
          <button
            v-for="n in 5" :key="n" type="button" class="star-btn" role="radio"
            :aria-checked="reviewStars === n" :aria-label="`${n} star${n === 1 ? '' : 's'}`" @click="reviewStars = n"
          >
            <Star :size="28" :fill="n <= reviewStars ? '#D4A017' : 'none'" :color="n <= reviewStars ? '#D4A017' : '#c8c8c8'" />
          </button>
          <span class="star-label">{{ STAR_LABELS[reviewStars] }}</span>
        </div>
        <label class="field-label" for="review-text">Comment <span class="optional">(optional)</span></label>
        <textarea id="review-text" v-model="reviewText" rows="3" maxlength="1000" class="field-input" placeholder="How was your consultation?"></textarea>
        <p class="char-count">{{ reviewText.length }}/1000</p>
        <p v-if="reviewError" class="inline-error">{{ reviewError }}</p>
        <div class="nm-modal-actions">
          <button class="nm-btn-soft" type="button" :disabled="isSubmittingReview" @click="closeReview">Not now</button>
          <button class="nm-btn-dark" type="button" :disabled="isSubmittingReview || !reviewStars" @click="submitReview">{{ isSubmittingReview ? 'Posting…' : 'Post review' }}</button>
        </div>
      </div>
    </div>

    <Transition name="toast-fade">
      <div v-if="toast" class="toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
    </Transition>
    <ConsultationSummaryModal v-if="summaryId" :appointment-id="summaryId" role="client" @close="summaryId = null" />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import {
  CalendarPlus, CalendarDays, Video, MessageCircle, MessageSquare, MapPin, Star,
  CheckCircle2, ClipboardList, CreditCard, X,
} from 'lucide-vue-next'

const { get, patch, post } = useApi()
const now = useNow(30000) // join window ticks

const isLoading = ref(true)
const errorMessage = ref('')
const rawAppointments = ref([])
const relationships = ref([])
const reviews = ref([])
const rndProfiles = ref({}) // rnd user id -> /client/rnds/<id>/ payload

const TYPES = {
  video: { label: 'Video call', icon: Video },
  chat: { label: 'Chat', icon: MessageCircle },
  in_person: { label: 'In person', icon: MapPin },
}
const STAR_LABELS = { 1: 'Poor', 2: 'Fair', 3: 'Good', 4: 'Very good', 5: 'Excellent' }

function money(v) {
  return Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
function clock(d) {
  return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}

const activeRnd = computed(() => relationships.value[0]?.rnd || null)
const bookLink = computed(() => (activeRnd.value ? `/rnd-profile-view/${activeRnd.value.id}?book=1` : '/find-rnd'))

const reviewByAppt = computed(() => Object.fromEntries(reviews.value.map(r => [r.appointment, r])))
const activeRelIds = computed(() => new Set(relationships.value.map(r => r.id)))

const appointments = computed(() => rawAppointments.value.map((a) => {
  const start = new Date(a.scheduled_at)
  const end = new Date(start.getTime() + (a.duration_minutes || 60) * 60000)
  const nowMs = now.value
  const isOver = end.getTime() <= nowMs
  const opensAt = a.join_opens_at ? new Date(a.join_opens_at).getTime() : start.getTime()
  const closesAt = a.join_closes_at ? new Date(a.join_closes_at).getTime() : end.getTime()
  const inWindow = nowMs >= opensAt && nowMs <= closesAt
  const rndUser = a.relationship.rnd
  const profile = rndProfiles.value[rndUser.id]
  const type = TYPES[a.type] || { label: a.type, icon: CalendarDays }
  const relActive = activeRelIds.value.has(a.relationship.id)

  // "expired": a request whose time passed before the RND confirmed it;
  // "ended": confirmed, the time has passed, but the RND hasn't marked it complete.
  // Pay before the consultation: a confirmed appointment with an unpaid
  // invoice is "payment due" until it's paid (the API cancels it at the
  // start time if it's still unpaid). Older ones with no invoice are just "confirmed".
  const payment = a.payment || null
  let phase = a.status
  if (a.status === 'pending' && isOver) phase = 'expired'
  if (a.status === 'confirmed' && isOver) phase = 'ended'
  if (a.status === 'confirmed' && !isOver && payment?.status === 'unpaid') phase = 'payment_due'

  const STATUS = {
    pending: ['Waiting for your RND', 'pill-gold'],
    payment_due: ['Payment due', 'pill-gold'],
    confirmed: ['Confirmed', 'pill-green'],
    completed: ['Completed', 'pill-muted'],
    cancelled: ['Cancelled', 'pill-red'],
    expired: ['Not confirmed', 'pill-muted'],
    ended: ['Ended', 'pill-muted'],
  }
  const [statusLabel, statusClass] = STATUS[phase] || [a.status, 'pill-muted']

  let hint = ''
  if (phase === 'pending') hint = `Waiting for RND ${rndUser.first_name} to confirm. You'll be asked to pay once they do.`
  else if (phase === 'payment_due') hint = `Pay ₱${money(payment.amount)} before ${start.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}, ${clock(start)} to start your consultation. If it isn't paid by then, the booking is cancelled and the slot is released.`
  else if (phase === 'confirmed' && a.type === 'video' && nowMs < opensAt) hint = `Your video room opens ${formatJoinTime(opensAt, nowMs)}, 15 minutes before the start.`
  else if (phase === 'confirmed' && a.type === 'video') hint = a.video_session_url ? 'Your video room is open. You can join now.' : 'Your RND is setting up the video room.'
  else if (phase === 'confirmed' && a.type === 'in_person') hint = 'Message your RND if you need the clinic address or directions.'
  else if (phase === 'expired') hint = 'The time passed before your RND confirmed this request.'
  else if (phase === 'ended') hint = 'Your RND will mark this consultation complete.'

  return {
    id: a.id,
    status: a.status,
    phase,
    relationshipId: a.relationship.id,
    start,
    rnd: {
      id: rndUser.id,
      name: `${rndUser.first_name} ${rndUser.last_name}`,
      firstName: rndUser.first_name,
      initials: `${rndUser.first_name?.[0] || ''}${rndUser.last_name?.[0] || ''}`.toUpperCase(),
      photo: profile?.user?.profile_photo || '',
      specialization: profile?.specialization || '',
    },
    month: start.toLocaleDateString('en-US', { month: 'short' }),
    day: start.getDate(),
    year: start.getFullYear(),
    weekday: start.toLocaleDateString('en-US', { weekday: 'short' }),
    longDate: start.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }),
    timeRange: `${clock(start)} – ${clock(end)}`,
    startClock: clock(start),
    endClock: clock(end),
    dayLabel: start.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
    shortDate: start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    monthLabel: start.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
    tone: phase === 'completed' ? 'green' : { 'pill-gold': 'gold', 'pill-green': 'green', 'pill-red': 'red' }[statusClass] || 'grey',
    typeLabel: type.label,
    typeIcon: type.icon,
    notes: (a.notes || '').trim(),
    cancellationReason: (a.cancellation_reason || '').trim(),
    statusLabel,
    statusClass,
    hint,
    canJoinVideo: phase === 'confirmed' && a.type === 'video' && Boolean(a.video_session_url) && inWindow,
    opensLater: phase === 'confirmed' && a.type === 'video' && nowMs < opensAt,
    opensLabel: formatJoinTime(opensAt, nowMs),
    needsRoomRefresh: phase === 'confirmed' && a.type === 'video' && inWindow && !a.video_session_url,
    canMessage: relActive,
    // A confirmed consultation can't be cancelled once it has started (the API refuses too).
    canCancel: a.status === 'pending' || (a.status === 'confirmed' && nowMs < start.getTime()),
    review: reviewByAppt.value[a.id] || null,
    payment,
  }
}))

const upcoming = computed(() =>
  appointments.value.filter(a => ['pending', 'payment_due', 'confirmed'].includes(a.phase)).sort((x, y) => x.start - y.start)
)
const history = computed(() =>
  appointments.value.filter(a => !['pending', 'payment_due', 'confirmed'].includes(a.phase)).sort((x, y) => y.start - x.start)
)

const historyFilters = [
  { key: 'all', label: 'All', empty: 'No past appointments.' },
  { key: 'completed', label: 'Completed', empty: 'No completed consultations yet.' },
  { key: 'cancelled', label: 'Cancelled', empty: 'No cancelled appointments.' },
  { key: 'expired', label: 'Not confirmed', empty: 'No expired booking requests.' },
]
const historyFilter = ref('all')
const historyCounts = computed(() => ({
  completed: history.value.filter(a => a.phase === 'completed').length,
  cancelled: history.value.filter(a => a.phase === 'cancelled').length,
  expired: history.value.filter(a => a.phase === 'expired').length,
}))
const filteredHistory = computed(() =>
  historyFilter.value === 'all' ? history.value : history.value.filter(a => a.phase === historyFilter.value)
)
// History under month headings ("October 2026"), newest first.
const historyGroups = computed(() => {
  const groups = []
  for (const a of filteredHistory.value) {
    const last = groups[groups.length - 1]
    if (last && last.label === a.monthLabel) last.items.push(a)
    else groups.push({ label: a.monthLabel, items: [a] })
  }
  return groups
})

/* ---------- Load ---------- */
async function load() {
  errorMessage.value = ''
  try {
    // Ask PayMongo about unpaid invoices first, so a just-made payment shows.
    await post('/client/invoices/sync/').catch(() => null)
    const [appts, rels, revs] = await Promise.all([
      get('/client/appointments/'),
      get('/client/relationships/').catch(() => []),
      get('/client/reviews/').catch(() => []),
    ])
    rawAppointments.value = appts
    relationships.value = rels
    reviews.value = revs
    // Photo + specialization for each RND on the list (one request per RND).
    const ids = [...new Set(appts.map(a => a.relationship.rnd.id))].filter(id => !rndProfiles.value[id])
    const profiles = await Promise.all(ids.map(id => get(`/client/rnds/${id}/`).catch(() => null)))
    const next = { ...rndProfiles.value }
    ids.forEach((id, i) => { if (profiles[i]) next[id] = profiles[i] })
    rndProfiles.value = next
  } catch {
    errorMessage.value = 'Could not load your appointments. Please try again later.'
  } finally {
    isLoading.value = false
  }
}
onMounted(load)

/* ---------- Join window ---------- */
// Re-renders every 30s (`now`, declared at the top); when a paid video
// visit's window opens, reload once to fetch its room link (the API only
// sends it inside the window).
const refreshedFor = new Set()
watch(now, () => {
  const due = appointments.value.filter(a => a.needsRoomRefresh && !refreshedFor.has(a.id))
  if (!due.length) return
  due.forEach(a => refreshedFor.add(a.id))
  load()
})

/* ---------- Pay before the consultation ---------- */
const { pay, payingId, payError } = usePayInvoice()
function payNow(appt) {
  pay(appt.payment.invoice_id, {
    onPaid() {
      load()
      showToast('Payment received. Your consultation is all set.')
    },
    onClosed: load,
  })
}
watch(payError, (msg) => { if (msg) showToast(msg) })
// Coming back to this tab after paying re-checks.
function onVisible() {
  if (document.visibilityState === 'visible' && upcoming.value.some(a => a.phase === 'payment_due')) load()
}
onMounted(() => document.addEventListener('visibilitychange', onVisible))
onBeforeUnmount(() => document.removeEventListener('visibilitychange', onVisible))

const toast = ref('')
let toastTimer = null
function showToast(message) {
  toast.value = message
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 3500)
}

/* ---------- Cancel ---------- */
const busyId = ref(null)
const actionError = reactive({})
const cancelTarget = ref(null)
const cancelReason = ref('')
const isCancelling = ref(false)
const cancelError = ref('')
function openCancel(appt) {
  cancelTarget.value = appt
  cancelReason.value = ''
  cancelError.value = ''
}
function closeCancel() {
  if (!isCancelling.value) cancelTarget.value = null
}
async function confirmCancel() {
  const appt = cancelTarget.value
  if (!appt) return
  isCancelling.value = true
  cancelError.value = ''
  busyId.value = appt.id
  try {
    await patch(`/client/appointments/${appt.id}/cancel/`, { reason: cancelReason.value.trim() || undefined })
    cancelTarget.value = null
    await load()
    showToast(appt.status === 'pending' ? 'Booking request cancelled.' : 'Appointment cancelled.')
  } catch (error) {
    cancelError.value = error?.data?.detail || 'Could not cancel this appointment. Please try again.'
  } finally {
    isCancelling.value = false
    busyId.value = null
  }
}

/* ---------- Review ---------- */
const summaryId = ref(null) // consultation summary pop-up
const reviewTarget = ref(null)
const reviewStars = ref(5)
const reviewText = ref('')
const isSubmittingReview = ref(false)
const reviewError = ref('')
function openReview(appt) {
  reviewTarget.value = appt
  reviewStars.value = 5
  reviewText.value = ''
  reviewError.value = ''
}
function closeReview() {
  if (!isSubmittingReview.value) reviewTarget.value = null
}
async function submitReview() {
  const appt = reviewTarget.value
  if (!appt) return
  isSubmittingReview.value = true
  reviewError.value = ''
  try {
    await post('/client/reviews/', {
      appointment: appt.id,
      rnd: appt.rnd.id,
      rating: reviewStars.value,
      comment: reviewText.value.trim() || undefined,
    })
    reviewTarget.value = null
    await load()
    showToast('Thanks. Your review is posted.')
  } catch (error) {
    const data = error?.data || {}
    reviewError.value = data.appointment?.[0] || data.rating?.[0] || data.non_field_errors?.[0] || data.detail || 'Could not submit your review. Please try again.'
  } finally {
    isSubmittingReview.value = false
  }
}

function onKeydown(e) {
  if (e.key !== 'Escape') return
  if (cancelTarget.value) closeCancel()
  else if (reviewTarget.value) closeReview()
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
/* Same tokens as the client dashboard (ClientDashboard.vue) and Profile Settings. */
* { box-sizing: border-box; }
.appointments-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 24px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.form-error { background: #fdecec; border: 1px solid #f3b8b8; color: #a12525; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px; }
.placeholder-text { font-size: 0.85rem; color: #6a7a6a; }
.empty-note { font-size: 0.85rem; color: #6a7a6a; margin: 0; padding: 6px 0; }
.inline-error { font-size: 0.8rem; color: #a12525; margin: 8px 0 0; }

.section { margin-bottom: 28px; }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.section-head .section-title { margin: 0; }
.section-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0 0 14px; display: flex; align-items: center; gap: 8px; }
.count { font-family: 'Inter', sans-serif; font-size: 0.74rem; font-weight: 700; color: #1e4a26; background: #e3efe7; border-radius: 999px; padding: 2px 9px; }

.panel { background: #fff; border-radius: 14px; border: 1px solid #d9e3dc; padding: 22px; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }

/* BUTTONS */
.btn-dark {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex-shrink: 0;
  background: #0a4a37; color: #fff; border: none; text-decoration: none; font-family: inherit;
  padding: 9px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer; white-space: nowrap;
}
.btn-dark:hover:not(:disabled) { background: #00382a; }
.btn-dark:disabled { opacity: 0.5; cursor: not-allowed; }
.outline-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex-shrink: 0;
  border: 1px solid #d9e3dc; background: #fff; color: #0a4a37; border-radius: 8px; text-decoration: none; font-family: inherit;
  padding: 9px 16px; font-weight: 600; font-size: 0.82rem; cursor: pointer; white-space: nowrap;
}
.outline-btn:hover:not(:disabled) { background: #f4f7f5; }
.btn-dark:focus-visible, .outline-btn:focus-visible, .ghost-danger-btn:focus-visible, .danger-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.outline-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.outline-btn.small { padding: 7px 12px; font-size: 0.78rem; }
/* cancel: a solid red button, kept apart on the right */
.ghost-danger-btn { display: inline-flex; align-items: center; justify-content: center; background: #c0392b; border: 1px solid #c0392b; color: #fff; border-radius: 8px; font-weight: 600; font-size: 0.82rem; cursor: pointer; padding: 9px 16px; font-family: inherit; margin-left: auto; white-space: nowrap; }
.ghost-danger-btn:hover:not(:disabled) { background: #a12f23; border-color: #a12f23; }
.ghost-danger-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.danger-btn { background: #c0392b; color: #fff; border: none; border-radius: 8px; padding: 9px 16px; font-weight: 600; font-size: 0.82rem; cursor: pointer; font-family: inherit; }
.danger-btn:hover:not(:disabled) { background: #a93226; }
.danger-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* PILLS */
.status-pill { display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-gold { background: #fdf1d6; color: #b8860b; }
.pill-muted { background: #eef2ef; color: #4a5a4a; }
.pill-red { background: #fdecec; color: #a12525; }
.pill-link { text-decoration: none; }
.pill-link:hover { text-decoration: underline; }

/* EMPTY */
.empty-state { text-align: center; color: #6a7a6a; font-size: 0.86rem; padding: 28px 20px; }
.empty-state p { margin: 0; }
.empty-icon { display: block; margin: 0 auto 8px; color: #9ec4ad; }
.empty-sub { font-size: 0.8rem; margin: 4px 0 14px !important; line-height: 1.5; }

/* UPCOMING CARD: the date and time lead */
.up-card { margin-bottom: 14px; }
.up-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.up-day { font-size: 0.86rem; font-weight: 600; color: #4a5a4a; margin: 0; }
.up-time { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; line-height: 1.1; color: #1a3a1a; margin: 2px 0 0; font-variant-numeric: lining-nums; }
.up-to { font-family: 'Inter', sans-serif; font-size: 0.92rem; font-weight: 500; color: #6a7a6a; }
.up-with { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; font-size: 0.9rem; color: #1a3a1a; margin: 10px 0 0; }
.up-with svg { color: #3f9a6b; }
.up-rnd { font-weight: 700; color: #0a4a37; text-decoration: none; }
.up-rnd:hover { text-decoration: underline; }
.appt-notes { font-size: 0.82rem; color: #4a5a4a; margin: 10px 0 0; line-height: 1.5; overflow-wrap: anywhere; }
.appt-notes span { color: #6a7a6a; }
.appt-hint { font-size: 0.82rem; color: #4a5a4a; margin: 10px 0 0; line-height: 1.5; }
/* payment still to make: the app's dashed green for "to do" */
.appt-hint.hint-due { color: #1f4a30; background: #fff; border: 1.5px dashed #3f9a6b; border-radius: 10px; padding: 9px 12px; }
.modal-note { font-size: 0.82rem; color: #4a5a4a; background: #f4f6f4; border: 1px solid #d9e3dc; border-radius: 10px; padding: 9px 12px; margin: -6px 0 14px; line-height: 1.5; }
.appt-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-top: 16px; padding-top: 14px; border-top: 1px solid #d9e3dc; }
/* every button in the row the same height */
.cancel-btn { margin-left: auto; }

/* status: a dot and a word */
.dot-status { display: inline-flex; align-items: center; gap: 7px; font-size: 0.82rem; font-weight: 600; color: #4a5a4a; white-space: nowrap; }
.dot { width: 9px; height: 9px; border-radius: 50%; background: #a9b8ad; flex-shrink: 0; }
.dot-status.gold { color: #8a6400; }
.dot-status.gold .dot { background: #D4A017; }
.dot-status.green { color: #1f6f46; }
.dot-status.green .dot { background: #1f8f5c; }
.dot-status.red { color: #a12525; }
.dot-status.red .dot { background: #c0392b; }

/* HISTORY: month headings, quiet rows */
.filter-tabs { display: inline-flex; gap: 4px; background: #f2f6f3; border-radius: 999px; padding: 3px; flex-wrap: wrap; }
.filter-tab { border: none; background: none; padding: 6px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; color: #6a7a6a; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 6px; }
.filter-tab.active { background: #0a4a37; color: #fff; }
.filter-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.tab-count { font-size: 0.7rem; opacity: 0.75; }
.history-panel { padding: 6px 22px 10px; }
.month-head { font-size: 0.86rem; font-weight: 700; color: #4a5a4a; margin: 14px 0 4px; }
.h-row { display: grid; grid-template-columns: 64px minmax(0, 1fr) auto; gap: 4px 16px; padding: 12px 0; border-top: 1px solid #d9e3dc; }
.h-date { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.h-main { min-width: 0; }
.h-title { font-size: 0.9rem; font-weight: 600; color: #1a3a1a; margin: 0; }
.h-sub { font-size: 0.8rem; color: #6a7a6a; margin: 2px 0 0; line-height: 1.45; overflow-wrap: anywhere; }
.h-links { display: flex; flex-wrap: wrap; gap: 4px 16px; margin: 6px 0 0; }
.text-link { background: none; border: none; padding: 0; font: inherit; font-size: 0.82rem; font-weight: 600; color: #0a4a37; cursor: pointer; text-decoration: underline; text-underline-offset: 2px; }
.text-link:hover { color: #00382a; }
.text-link:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; border-radius: 3px; }
.h-side { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.h-money { font-size: 0.8rem; color: #4a5a4a; white-space: nowrap; }
.h-money.link { color: #0a4a37; font-weight: 600; text-decoration: underline; }
.review-stars { display: inline-flex; align-items: center; gap: 2px; }

/* MODALS */
.modal-text { font-size: 0.85rem; color: #4a5a4a; line-height: 1.55; margin: 0 0 16px; }
.field-label { display: block; font-size: 0.8rem; font-weight: 600; color: #1a3a1a; margin: 0 0 6px; }
.optional { font-weight: 400; color: #6a7a6a; }
.field-input { width: 100%; border: 1px solid #d9e3dc; border-radius: 8px; padding: 10px 12px; font-size: 0.86rem; font-family: inherit; color: #1a3a1a; resize: vertical; }
.field-input:focus { outline: none; border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.15); }
.char-count { font-size: 0.74rem; color: #6a7a6a; text-align: right; margin: 4px 0 0; }
.star-row { display: flex; align-items: center; gap: 2px; margin: 0 0 16px; }
.star-btn { background: none; border: none; padding: 2px; cursor: pointer; display: flex; border-radius: 6px; }
.star-btn:focus-visible { outline: 2px solid #D4A017; }
.star-label { font-size: 0.82rem; color: #6a7a6a; font-weight: 600; margin-left: 10px; }

/* TOAST */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 400;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22); white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

@media (max-width: 640px) {
  .page-header { flex-direction: column; }
  .page-header .nm-btn-dark { width: 100%; }
  .page-title { font-size: 1.4rem; }
  .panel { padding: 18px 16px; }
  .up-head { flex-direction: column-reverse; gap: 8px; }
  .up-time { font-size: 1.7rem; }
  .appt-actions > .nm-btn-dark, .appt-actions > .nm-btn-soft { flex: 1; }
  .cancel-btn { margin-left: 0; width: 100%; }
  .history-panel { padding: 4px 16px; }
  .h-row { grid-template-columns: minmax(0, 1fr) auto; }
  .h-main { grid-column: 1 / -1; grid-row: 2; }
  .h-side { grid-column: 2; grid-row: 1; }
  .toast { white-space: normal; max-width: calc(100% - 32px); }
}
.refund-note { margin: 6px 0 0; padding: 8px 10px; border-radius: 8px; background: #f4f6f4; border: 1px solid #d9e3dc; color: #4a5a4a; font-size: 0.8rem; line-height: 1.45; }
</style>
