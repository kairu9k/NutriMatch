<template>
  <!-- Client "My Appointments" (Appointments.vue renders this for clients;
       the RND view lives in Appointments.vue). Styled with the same tokens
       as the client dashboard / Profile Settings. -->
  <div class="appointments-page">
    <!-- BANNER: what's coming and what's done -->
    <section class="ap-banner">
      <img class="ap-banner-plate" src="/landing/login-plate.webp" alt="" aria-hidden="true" />
      <div class="ap-banner-text">
        <p class="ap-eyebrow"><span aria-hidden="true"></span>Your consultations</p>
        <h2 class="ap-title">Every visit, <em>in one place.</em></h2>
        <p class="page-sub">Your upcoming consultations and past visits.</p>
        <NuxtLink :to="bookLink" class="ap-btn-gold"><CalendarPlus :size="17" aria-hidden="true" /> Book a consultation</NuxtLink>
      </div>
      <div v-if="!isLoading && !errorMessage" class="ap-banner-stats">
        <div><strong>{{ upcoming.length }}</strong><span>Upcoming</span></div>
        <div><strong>{{ historyCounts.completed }}</strong><span>Completed</span></div>
        <div :class="{ red: historyCounts.cancelled }"><strong>{{ historyCounts.cancelled }}</strong><span>Cancelled</span></div>
      </div>
    </section>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="isLoading" class="placeholder-text"><span class="ap-spin" aria-hidden="true"></span>Loading appointments…</p>

    <template v-else-if="!errorMessage">
      <!-- ============ UPCOMING ============ -->
      <section class="section">
        <div class="section-head"><h2 class="section-title">Upcoming <span class="count">{{ upcoming.length }}</span></h2></div>
        
        <div v-if="!upcoming.length" class="panel up-empty">
          <span class="up-empty-glow" aria-hidden="true"></span>
          <div class="up-empty-row">
            <span class="up-empty-icon" aria-hidden="true"><CalendarDays :size="30" :stroke-width="1.7" /><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 8v8M8 12h8" /></svg></span></span>
            <div class="up-empty-text">
              <p class="up-empty-title">No upcoming consultations.</p>
              <p class="empty-sub">{{ activeRnd ? `Book a follow-up with RND ${activeRnd.first_name} ${activeRnd.last_name} when you're ready.` : 'Find an RND and book your first consultation.' }}</p>
            </div>
            <NuxtLink :to="bookLink" class="ap-btn-gold">{{ activeRnd ? 'Book a consultation' : 'Find an RND' }}<svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
          </div>
          <div v-if="!activeRnd" class="ap-steps">
            <div class="ap-step"><span>1</span><div><strong>Find your RND</strong><p>Pick a licensed RND who fits your needs.</p></div></div>
            <div class="ap-step"><span>2</span><div><strong>Choose a time</strong><p>Video call or in person, when it suits you.</p></div></div>
            <div class="ap-step"><span>3</span><div><strong>Pay and confirm</strong><p>Pay before the session to lock it in.</p></div></div>
          </div>
        </div>

        <article v-for="appt in upcoming" :key="appt.id" class="panel up-card">
          <div class="up-head">
            <span class="ap-date" aria-hidden="true"><span>{{ appt.month }}</span><strong>{{ appt.day }}</strong></span>
            <div class="up-when-block">
              <p class="up-day">{{ appt.dayLabel }}</p>
              <p class="up-time">{{ appt.startClock }} <span class="up-to">to {{ appt.endClock }}</span></p>
            </div>
            <span class="dot-status" :class="appt.tone"><span class="dot" aria-hidden="true" />{{ appt.statusLabel }}<template v-if="appt.phase === 'confirmed' && appt.payment?.status === 'paid'">, paid</template></span>
          </div>
          <p class="up-with">
            <component :is="appt.typeIcon" :size="15" aria-hidden="true" /> {{ appt.typeLabel }} with
            <NuxtLink :to="`/rnd-profile-view/${appt.rnd.id}`" class="up-rnd">RND {{ appt.rnd.name }}</NuxtLink>
          </p>
          <p v-if="appt.clinic_address" class="up-where">
            <span>{{ appt.clinic_address }}</span>
            <a :href="`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(appt.clinic_address)}`" target="_blank" rel="noopener" class="nm-text-link">Open in Google Maps</a>
          </p>
          <p v-if="appt.notes" class="appt-notes"><span>Your notes:</span> {{ appt.notes }}</p>
          <p v-if="appt.hint" class="appt-hint" :class="{ 'hint-due': appt.phase === 'payment_due' }">{{ appt.hint }}</p>
          <RescheduleAnswer v-if="appt.phase === 'rescheduling' || (appt.status === 'pending' && appt.reschedule?.waiting)" :appointment="appt" role="client" :other-name="appt.rnd.name" @changed="load" />

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
            <button v-if="appt.canMove" class="nm-btn-soft" type="button" @click="startMove(appt)">
              <CalendarDays :size="14" aria-hidden="true" /> Reschedule
            </button>
            <button v-if="appt.canCancel" class="nm-btn-danger solid cancel-btn" type="button" :disabled="busyId === appt.id" @click="openCancel(appt)">
              {{ appt.status === 'pending' ? 'Cancel request' : 'Cancel' }}
            </button>
          </div>
          <p v-if="appt.cancelNote" class="cancel-closed">{{ appt.cancelNote }}</p>
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
          <span class="empty-icon"><ClipboardList :size="24" /></span>
          <p>No past appointments yet.</p>
        </div>
        <div v-else class="panel history-panel">
          <p v-if="!filteredHistory.length" class="empty-note">{{ historyFilters.find(f => f.key === historyFilter).empty }}</p>
          <template v-for="g in historyGroups" :key="g.label">
            <h3 class="month-head">{{ g.label }}</h3>
            <div v-for="appt in g.items" :key="appt.id" class="h-row" :class="`is-${appt.phase}`">
              <p class="h-date" :aria-label="appt.shortDate"><span>{{ appt.month }}</span><strong>{{ appt.day }}</strong></p>
              <div class="h-main">
                <p class="h-title"><component :is="appt.typeIcon" :size="17" class="h-type" aria-hidden="true" />{{ appt.typeLabel }}, {{ appt.startClock }}</p>
                <p class="h-sub h-rnd"><span class="h-ini" aria-hidden="true">{{ appt.rnd.initials }}</span>RND {{ appt.rnd.name }}</p>
                <p v-if="appt.status === 'cancelled' && appt.cancellationReason" class="h-sub">Reason: {{ appt.cancellationReason }}</p>
                <p v-if="appt.attendanceLine" class="h-sub">{{ appt.attendanceLine }}</p>
                <template v-if="appt.status === 'no_show'">
                  <p class="h-sub">Your RND marked this as not attended, so it isn't refunded.<template v-if="appt.cancellationReason"> Their note: {{ appt.cancellationReason }}</template></p>
                  <p v-if="appt.dispute?.outcome === 'refunded'" class="refund-note">Your dispute was approved. {{ appt.dispute.note }}</p>
                  <p v-else-if="appt.dispute?.outcome === 'rejected'" class="h-sub">Your dispute wasn't approved. {{ appt.dispute.note }}</p>
                  <p v-else-if="appt.dispute?.opened_at" class="h-sub">You disputed this. NutriMatch is reviewing it and will reply in Help &amp; Support.</p>
                  <p v-else-if="appt.dispute?.can_open" class="h-sub">Think this is wrong? Use Help &amp; Support (bottom right), Dispute a consultation, until {{ appt.disputeUntil }}.</p>
                </template>
                <!-- an in-person visit marked complete: nothing records it, so the client can say it didn't happen -->
                <template v-else-if="appt.status === 'completed' && appt.dispute">
                  <p v-if="appt.dispute.outcome === 'refunded'" class="refund-note">Your dispute was approved. {{ appt.dispute.note }}</p>
                  <p v-else-if="appt.dispute.outcome === 'rejected'" class="h-sub">Your dispute wasn't approved. {{ appt.dispute.note }}</p>
                  <p v-else-if="appt.dispute.opened_at" class="h-sub">You disputed this. NutriMatch is reviewing it and will reply in Help &amp; Support.</p>
                  <p v-else-if="appt.dispute.can_open" class="h-sub">Didn’t take place? Use Help &amp; Support (bottom right), Dispute a consultation, until {{ appt.disputeUntil }}.</p>
                </template>
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

    <!-- RESCHEDULE (2026-11-23, the adviser): paid or not; only the RND confirms it.
         A request still waiting for the RND just changes its time. Later times only. -->
    <RescheduleModal
      v-if="moving" role="client" :appointment-id="moving.id" :other-first-name="moving.rnd.firstName"
      :status="moving.status" :paid="moving.payment?.status === 'paid'" :type-label="moving.typeLabel"
      :booked-label="`${moving.dayLabel}, ${moving.startClock}`"
      @close="moving = null" @done="onMoved"
    />

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

    <ConsultationSummaryModal v-if="summaryId" :appointment-id="summaryId" role="client" @close="summaryId = null" />
  </div>
</template>

<script setup>
const demoMode = useDemoMode() // scheduling/demo.py: demo times
import { useSupportPanel } from '~/composables/useSupportPanel'
import { useToast } from '~/composables/useToast'
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
function cancelRules(a, phase, payment, nowMs, start, payBy, cancelBy) {
  if (a.status === 'pending') return { canCancel: phase === 'pending', cancelNote: '' }
  if (a.status !== 'confirmed' || nowMs >= start.getTime()) return { canCancel: false, cancelNote: '' }
  if (payment?.status === 'unpaid') {
    return { canCancel: nowMs < payBy.getTime(), cancelNote: nowMs < payBy.getTime() ? 'Not paid yet, so you can cancel at no cost.' : '' }
  }
  if (nowMs < cancelBy.getTime()) {
    return { canCancel: true, cancelNote: `You can cancel until ${clock(cancelBy)}, 30 minutes before the start. If you don't attend, there's no refund.` }
  }
  return { canCancel: false, cancelNote: 'Cancelling closed 30 minutes before the start. If you can\'t make it, message your RND. If you don\'t attend, there\'s no refund.' }
}
// Only who joined the video call and for how long (nothing from the call is kept).
function attendanceText(at) {
  if (at.state === 'both') return `Video call: you and your RND were in it together for ${at.together_minutes} min.`
  if (at.state === 'client_only') return 'Video call: you joined, your RND didn\'t.'
  if (at.state === 'rnd_only') return 'Video call: your RND joined, you didn\'t.'
  return ''
}

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
  const payBy = a.pay_by ? new Date(a.pay_by) : start
  const cancelBy = a.cancel_by ? new Date(a.cancel_by) : start
  const confirmBy = a.confirm_by ? new Date(a.confirm_by) : start
  let phase = a.status
  if (a.status === 'pending' && nowMs >= confirmBy.getTime()) phase = 'expired'
  if (a.status === 'confirmed' && isOver) phase = 'ended'
  if (a.status === 'confirmed' && !isOver && payment?.status === 'unpaid') phase = 'payment_due'

  const STATUS = {
    pending: ['Waiting for your RND', 'pill-gold'],
    rescheduling: ['Rescheduling', 'pill-gold'],
    payment_due: ['Payment due', 'pill-gold'],
    confirmed: ['Confirmed', 'pill-green'],
    completed: ['Completed', 'pill-muted'],
    cancelled: ['Cancelled', 'pill-red'],
    no_show: ['No-show', 'pill-red'],
    expired: ['Not confirmed', 'pill-muted'],
    ended: ['Ended', 'pill-muted'],
  }
  const [statusLabel, statusClass] = STATUS[phase] || [a.status, 'pill-muted']

  let hint = ''
  if (phase === 'pending') hint = `Waiting for RND ${rndUser.first_name} to confirm (by ${clock(confirmBy)}). You'll be asked to pay once they do.`
  else if (phase === 'payment_due') hint = `Pay ₱${money(payment.amount)} by ${payBy.toLocaleDateString('en-US', { month: 'long', day: 'numeric' })}, ${clock(payBy)}${demoMode.value ? '' : ', 15 minutes before the start'}. If it isn't paid by then, the booking is cancelled and the slot is released.`
  else if (phase === 'confirmed' && a.type === 'video' && nowMs < opensAt) hint = `Your video room opens ${formatJoinTime(opensAt, nowMs)}${demoMode.value ? '' : ', 15 minutes before the start'}.`
  else if (phase === 'confirmed' && a.type === 'video') hint = 'Your video room is open. You can join now.'
  else if (phase === 'confirmed' && a.type === 'in_person') hint = a.clinic_address
    ? 'Arrive a few minutes early, and bring any lab results and a list of the medicines you take.'
    : 'Message your RND if you need the clinic address or directions.'
  else if (phase === 'expired') hint = 'Your RND didn\'t confirm this request in time.'
  else if (phase === 'ended') hint = 'Your RND will mark this consultation complete.'

  return {
    id: a.id,
    status: a.status,
    clinic_address: a.clinic_address,
    phase,
    relationshipId: a.relationship.id,
    start,
    scheduled_at: a.scheduled_at,
    // ask for a later time: a request still waiting for the RND, or a confirmed booking
    // (paid or not), until 2 hours before it (REQUEST_CUTOFF_MINUTES in scheduling/reschedule.py;
    // 30 minutes in demo mode, scheduling/demo.py reschedule_cutoff_minutes)
    canMove: ['pending', 'payment_due', 'confirmed'].includes(phase) && start.getTime() - nowMs > (demoMode.value ? 30 : 120) * 60000,
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
    // NutriMatch's own video call (WebRTC) needs no room link: a confirmed,
    // paid consultation inside its window can be joined (the call checks too)
    canJoinVideo: phase === 'confirmed' && a.type === 'video' && inWindow,
    opensLater: phase === 'confirmed' && a.type === 'video' && nowMs < opensAt,
    opensLabel: formatJoinTime(opensAt, nowMs),
    canMessage: relActive,
    // Time rules (the API refuses too): a request can be withdrawn until the RND
    // confirms; unpaid, until the pay-by time; paid, until 30 minutes before the start.
    ...cancelRules(a, phase, payment, nowMs, start, payBy, cancelBy),
    attendanceLine: ['completed', 'no_show', 'cancelled'].includes(a.status) && a.attendance && a.attendance.state !== 'none'
      ? attendanceText(a.attendance) : '',
    dispute: a.dispute,
    disputeUntil: a.dispute?.open_until ? new Date(a.dispute.open_until).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) : '',
    review: reviewByAppt.value[a.id] || null,
    payment,
    reschedule: a.reschedule,
  }
}))

const upcoming = computed(() =>
  appointments.value.filter(a => ['pending', 'payment_due', 'confirmed', 'rescheduling'].includes(a.phase)).sort((x, y) => x.start - y.start)
)
const history = computed(() =>
  appointments.value.filter(a => !['pending', 'payment_due', 'confirmed', 'rescheduling'].includes(a.phase)).sort((x, y) => y.start - x.start)
)

const historyFilters = [
  { key: 'all', label: 'All', empty: 'No past appointments.' },
  { key: 'completed', label: 'Completed', empty: 'No completed consultations yet.' },
  { key: 'cancelled', label: 'Cancelled', empty: 'No cancelled appointments.' },
  { key: 'no_show', label: 'No-show', empty: 'No missed consultations.' },
  { key: 'expired', label: 'Not confirmed', empty: 'No expired booking requests.' },
]
const historyFilter = ref('all')
const historyCounts = computed(() => ({
  completed: history.value.filter(a => a.phase === 'completed').length,
  cancelled: history.value.filter(a => a.phase === 'cancelled').length,
  no_show: history.value.filter(a => a.phase === 'no_show').length,
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
    // Ask the payment provider about unpaid invoices first, so a just-made payment shows.
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
// confirmations, cancellations and expired requests show without a reload;
// not while a payment is open
useAutoRefresh(load, { paused: () => !!payingId.value })

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
watch(payError, (msg) => { if (msg) toast.error(msg, { id: 'pay' }) })
// Coming back to this tab after paying re-checks.
function onVisible() {
  if (document.visibilityState === 'visible' && upcoming.value.some(a => a.phase === 'payment_due')) load()
}
onMounted(() => document.addEventListener('visibilitychange', onVisible))
onBeforeUnmount(() => document.removeEventListener('visibilitychange', onVisible))

const toast = useToast() // the app's toast (2026-11-03)
function showToast(message, opts) {
  toast.success(message, opts)
}

/* ---------- Cancel ---------- */
const busyId = ref(null)

/* ---------- Reschedule (2026-11-23): the shared pop-up, RescheduleModal.vue ---------- */
const moving = ref(null)
function startMove(appt) {
  moving.value = appt
}
async function onMoved() {
  moving.value = null
  await load()
}
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

/* ---------- Disputes (2026-11-16) ---------- */
// The Help & Support panel is the one place to dispute ("Dispute a consultation");
// the server holds the RND's payout there (scheduling/no_shows.py open_dispute).
// The page shows "You disputed this" as soon as the panel sends it.
const { sent: disputeSent } = useSupportPanel()
watch(disputeSent, () => load())

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
/* =========================================================
   Client "My Appointments": brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.appointments-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; gap: 22px; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }

/* ---------- BANNER ---------- */
.ap-banner {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 28px 30px;
  border-radius: 24px;
  color: #FFFFFF;
  background:
    radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0) 45%),
    linear-gradient(115deg, #035A45 0%, #004D3A 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -14px rgba(0, 77, 58, 0.55);
}
.ap-banner-plate {
  position: absolute;
  right: -70px;
  top: 50%;
  width: 300px;
  height: 300px;
  transform: translateY(-50%);
  object-fit: cover;
  border-radius: 50%;
  opacity: 0.22;
  pointer-events: none;
}
.ap-banner-text,
.ap-banner-stats { position: relative; z-index: 1; }
.ap-banner-text { max-width: 460px; }
.ap-eyebrow { margin: 0; display: flex; align-items: center; gap: 12px; font-size: 12.5px; font-weight: 800; color: #EFBF04; }
.ap-eyebrow span { width: 28px; height: 2px; border-radius: 2px; background: #EFBF04; }
.ap-title { margin: 10px 0 8px; font-family: 'Playfair Display', Georgia, serif; font-size: 30px; line-height: 1.15; font-weight: 700; color: #FFFFFF; }
.ap-title em { font-style: italic; color: #EFBF04; background: none; padding: 0; }
.page-sub { margin: 0 0 18px; font-size: 15.0px; line-height: 1.6; color: rgba(255, 255, 255, 0.85); }
.ap-banner-stats { flex-shrink: 0; display: grid; grid-template-columns: repeat(3, 120px); gap: 10px; }
.ap-banner-stats > div {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.09);
  border: 1px solid rgba(255, 255, 255, 0.16);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
}
.ap-banner-stats strong { display: block; font-family: 'Playfair Display', Georgia, serif; font-size: 28px; font-weight: 700; line-height: 1; color: #FFFFFF; }
.ap-banner-stats span { display: block; margin-top: 4px; font-size: 12.5px; font-weight: 600; color: rgba(255, 255, 255, 0.78); }
.ap-banner-stats .red strong { color: #FFB4AB; }

/* gold button (banner, empty card) */
.ap-btn-gold {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 46px;
  padding: 0 20px;
  border-radius: 12px;
  background: #EFBF04;
  color: #004D3A;
  font-size: 14.5px;
  font-weight: 800;
  text-decoration: none;
  white-space: nowrap;
  box-shadow: 0 10px 20px -10px rgba(196, 145, 2, 0.9);
  transition: background-color .15s, transform .15s;
}
.ap-btn-gold:hover { background: #F5CB1F; transform: translateY(-1px); }

/* ---------- messages ---------- */
.form-error { margin: 0; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 14px; }
.placeholder-text { margin: 0; display: flex; align-items: center; gap: 10px; font-size: 14px; color: #6B7D73; }
.ap-spin { width: 20px; height: 20px; border-radius: 50%; border: 2.5px solid #DCE5DF; border-top-color: #004D3A; animation: ap-spin .8s linear infinite; }
@keyframes ap-spin { to { transform: rotate(360deg); } }
.empty-note { margin: 0; padding: 18px 0; font-size: 14px; text-align: center; color: #6B7D73; }
.inline-error { margin: 10px 0 0; font-size: 13px; font-weight: 600; color: #B42318; }
.cancel-closed { margin: 10px 0 0; font-size: 13px; line-height: 1.5; color: #5D7065; }

/* ---------- sections ---------- */
.section { margin: 0; }
.section-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin: 4px 2px 12px; }
.section-title { margin: 0; display: flex; align-items: center; gap: 10px; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #10231B; }
.count { min-width: 24px; height: 24px; padding: 0 8px; border-radius: 999px; background: #E3EFE7; color: #004D3A; font-family: 'DM Sans', Arial, sans-serif; font-size: 12px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }

.panel {
  background: #FFFFFF;
  border: 1px solid #E1E7E3;
  border-radius: 20px;
  padding: 22px 24px;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.02),
    0 2px 6px rgba(0, 0, 0, 0.06),
    0 12px 28px -6px rgba(0, 0, 0, 0.12),
    0 24px 48px -18px rgba(0, 77, 58, 0.22);
}

/* ---------- buttons on this page ---------- */
.appointments-page .nm-btn-dark,
.appointments-page .nm-btn-soft,
.appointments-page .nm-btn-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  height: 44px;
  padding: 0 18px;
  border: none;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color .15s;
}
.appointments-page .nm-btn-sm { height: 36px; padding: 0 14px; font-size: 13px; }
.appointments-page .nm-btn-dark { background: #004D3A; color: #FFFFFF; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.appointments-page .nm-btn-dark:hover:not(:disabled) { background: #0A5C46; }
.appointments-page .nm-btn-soft { background: #F1F6F2; color: #004D3A; }
.appointments-page .nm-btn-soft:hover:not(:disabled) { background: #E3EFE7; }
.appointments-page .nm-btn-danger.solid { background: #FEF3F2; color: #B42318; }
.appointments-page .nm-btn-danger.solid:hover:not(:disabled) { background: #B42318; color: #FFFFFF; }
.appointments-page button:disabled { opacity: .55; cursor: not-allowed; box-shadow: none; }
.appointments-page button:focus-visible,
.appointments-page a:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }

/* ---------- empty states ---------- */
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 32px 20px; text-align: center; font-size: 14.5px; font-weight: 600; color: #3E5046; }
.empty-state p { margin: 0; }
.empty-icon { width: 52px; height: 52px; border-radius: 16px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.empty-sub { margin: 0; font-size: 14px; font-weight: 400; line-height: 1.6; color: #5D7065; }

.up-empty { position: relative; overflow: hidden; padding: 28px 30px; }
.up-empty-glow { position: absolute; right: -40px; top: -40px; width: 200px; height: 200px; border-radius: 50%; background: radial-gradient(circle, rgba(239, 191, 4, 0.14), rgba(239, 191, 4, 0) 70%); pointer-events: none; }
.up-empty-row { position: relative; display: flex; align-items: center; gap: 24px; flex-wrap: wrap; }
.up-empty-icon {
  position: relative;
  flex-shrink: 0;
  width: 72px;
  height: 72px;
  border-radius: 22px;
  background: #EEF4F0;
  color: #004D3A;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 22px -14px rgba(0, 77, 58, 0.5);
}
.up-empty-icon > span { position: absolute; right: -6px; bottom: -6px; width: 26px; height: 26px; border-radius: 50%; background: #EFBF04; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 0 0 3px #FFFFFF; }
.up-empty-text { flex: 1; min-width: 220px; }
.up-empty-title { margin: 0 0 4px; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-weight: 700; color: #10231B; }
.up-empty .ap-btn-gold { flex-shrink: 0; }
.ap-steps { position: relative; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 22px; padding-top: 20px; border-top: 1px dashed #DCE5DF; }
.ap-step { display: flex; gap: 12px; align-items: flex-start; }
.ap-step > span { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; background: #EFBF04; color: #004D3A; font-size: 13px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }
.ap-step strong { display: block; font-size: 14px; color: #10231B; }
.ap-step p { margin: 2px 0 0; font-size: 12.5px; line-height: 1.5; color: #5D7065; }

/* ---------- UPCOMING CARD ---------- */
.up-card { margin-bottom: 14px; }
.up-card:last-child { margin-bottom: 0; }
.up-head { display: flex; align-items: center; gap: 16px; }
.up-when-block { flex: 1; min-width: 0; }
.ap-date {
  flex-shrink: 0;
  width: 60px;
  height: 64px;
  border-radius: 16px;
  background: #004D3A;
  color: #FFFFFF;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  box-shadow: 0 10px 18px -12px rgba(0, 77, 58, 0.8);
}
.ap-date span { font-size: 10.5px; font-weight: 800; color: #EFBF04; }
.ap-date strong { font-family: 'Playfair Display', Georgia, serif; font-size: 24px; line-height: 1; }
.up-day { margin: 0; font-size: 12.5px; font-weight: 800; color: #C49102; }
.up-time { margin: 2px 0 0; font-family: 'Playfair Display', Georgia, serif; font-size: 28px; font-weight: 700; line-height: 1.1; color: #10231B; font-variant-numeric: lining-nums; }
.up-to { font-family: 'DM Sans', Arial, sans-serif; font-size: 14px; font-weight: 600; color: #6B7D73; }
.up-with { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 14px 0 0; padding: 10px 14px; border-radius: 12px; background: #F7FAF8; font-size: 14px; color: #22362C; }
.up-with svg { color: #004D3A; }
.up-rnd { font-weight: 700; color: #004D3A; text-decoration: none; }
.up-rnd:hover { text-decoration: underline; text-underline-offset: 3px; }
.appt-notes { margin: 12px 0 0; padding: 8px 12px; border-left: 3px solid #EFBF04; border-radius: 0 10px 10px 0; background: #FBF8EC; font-size: 13.5px; line-height: 1.5; color: #3E5046; overflow-wrap: anywhere; }
.appt-notes span { font-weight: 700; color: #7A5A00; }
.up-where { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 12px; margin: 10px 0 0; font-size: 14px; color: #1a3a1a; font-weight: 600; }
.up-where a { font-size: 13px; }
.appt-hint { margin: 12px 0 0; font-size: 13.5px; line-height: 1.55; color: #4A5A52; }
/* payment still to make */
.appt-hint.hint-due { padding: 12px 14px; border-radius: 12px; background: #FBF6E4; border: 1.5px dashed #E2C35A; color: #4A3E10; font-weight: 600; }
.appt-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-top: 18px; padding-top: 16px; border-top: 1px solid #EEF2EF; }
.cancel-btn { margin-left: auto; }

/* status: a dot and a word, as a pill */
.dot-status { display: inline-flex; align-items: center; gap: 7px; height: 28px; padding: 0 12px; border-radius: 999px; background: #F1F4F2; font-size: 12.5px; font-weight: 700; color: #4A5A52; white-space: nowrap; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #A9B8AD; flex-shrink: 0; }
.dot-status.gold { background: #FBF6E4; color: #7A5A00; }
.dot-status.gold .dot { background: #EFBF04; }
.dot-status.green { background: #EAF4EE; color: #1F7A4C; }
.dot-status.green .dot { background: #1F9D55; }
.dot-status.red { background: #FEF3F2; color: #B42318; }
.dot-status.red .dot { background: #D92D20; }

/* ---------- HISTORY ---------- */
.filter-tabs { display: inline-flex; gap: 4px; padding: 4px; border-radius: 999px; background: #FFFFFF; border: 1px solid #E1E7E3; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05); max-width: 100%; overflow-x: auto; scrollbar-width: none; }
.filter-tabs::-webkit-scrollbar { display: none; }
.filter-tab { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border: none; border-radius: 999px; background: none; font-family: inherit; font-size: 13px; font-weight: 700; color: #3E5046; white-space: nowrap; cursor: pointer; transition: background-color .15s, color .15s; }
.filter-tab:hover { background: #F1F6F2; }
.filter-tab.active { background: #004D3A; color: #FFFFFF; }
.tab-count { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: #EEF4F0; color: #004D3A; font-size: 11px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }
.filter-tab.active .tab-count { background: #EFBF04; color: #004D3A; }
.history-panel { padding: 8px 22px 12px; }
.month-head { margin: 0; padding: 14px 0 10px; border-bottom: 1px solid #EEF2EF; font-size: 12px; font-weight: 800; color: #C49102; }
.h-row {
  position: relative;
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) auto;
  align-items: start;
  gap: 4px 16px;
  padding: 16px 4px;
  border-radius: 14px;
  transition: background-color .15s;
}
.h-row + .h-row { border-top: 1px solid #EEF2EF; border-radius: 0; }
.h-row:hover { background: #F7FAF8; }
.h-row.is-cancelled::before,
.h-row.is-no_show::before { content: ''; position: absolute; left: -22px; top: 14px; bottom: 14px; width: 4px; border-radius: 0 4px 4px 0; background: #D92D20; }
.h-row.is-completed::before { content: ''; position: absolute; left: -22px; top: 14px; bottom: 14px; width: 4px; border-radius: 0 4px 4px 0; background: #1F9D55; }
.h-date {
  margin: 0;
  width: 56px;
  height: 60px;
  border-radius: 14px;
  background: #004D3A;
  color: #FFFFFF;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  box-shadow: 0 10px 18px -12px rgba(0, 77, 58, 0.8);
}
.h-row.is-cancelled .h-date,
.h-row.is-no_show .h-date,
.h-row.is-expired .h-date { background: #F1F4F2; color: #3E5046; box-shadow: none; }
.h-date span { font-size: 10.5px; font-weight: 800; color: #EFBF04; }
.h-row.is-cancelled .h-date span,
.h-row.is-no_show .h-date span,
.h-row.is-expired .h-date span { color: #7A8F84; }
.h-date strong { font-family: 'Playfair Display', Georgia, serif; font-size: 22px; line-height: 1; }
.h-main { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.h-title { margin: 0; display: inline-flex; align-items: center; gap: 8px; font-size: 15.5px; font-weight: 700; color: #10231B; }
.h-type { color: #004D3A; }
.h-sub { margin: 0; font-size: 13.5px; line-height: 1.5; color: #5D7065; overflow-wrap: anywhere; }
.h-rnd { display: inline-flex; align-items: center; gap: 8px; }
.h-ini { flex-shrink: 0; width: 24px; height: 24px; border-radius: 50%; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; font-size: 10.5px; font-weight: 800; }
.h-links { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 0; }
.text-link { background: none; border: none; padding: 0; font: inherit; font-size: 13px; font-weight: 700; color: #004D3A; cursor: pointer; text-decoration: underline; text-underline-offset: 2px; }
.h-side { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
.h-money { font-size: 13px; font-weight: 600; color: #4A5A52; white-space: nowrap; }
.h-money.link { color: #004D3A; font-weight: 700; text-decoration: underline; text-underline-offset: 3px; }
.review-stars { display: inline-flex; align-items: center; gap: 2px; }
.refund-note { margin: 6px 0 0; padding: 10px 12px; border-radius: 12px; background: #F7FAF8; border: 1px solid #E3EAE5; color: #3E5046; font-size: 13px; line-height: 1.5; }

/* ---------- MODALS ---------- */
.appointments-page .nm-modal-overlay { background: rgba(4, 30, 21, 0.55); -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px); }
.appointments-page .nm-modal { position: relative; border-radius: 22px; padding: 30px 30px 24px; box-shadow: 0 30px 70px -20px rgba(0, 0, 0, 0.5); font-family: 'DM Sans', Arial, sans-serif; }
.appointments-page .nm-modal-title { margin: 0 40px 8px 0; font-family: 'Playfair Display', Georgia, serif; font-size: 24px; font-weight: 700; color: #10231B; }
.appointments-page .nm-modal-x { position: absolute; top: 16px; right: 16px; width: 36px; height: 36px; border: none; border-radius: 50%; background: #F1F6F2; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; }
.appointments-page .nm-modal-x:hover { background: #E3EFE7; }
.appointments-page .nm-modal-actions { display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap; margin-top: 20px; padding-top: 16px; border-top: 1px solid #EEF2EF; }
.modal-text { margin: 0 0 16px; font-size: 14.5px; line-height: 1.6; color: #4A5A52; }
.modal-note { margin: -6px 0 16px; padding: 12px 14px; border-radius: 12px; background: #F7FAF8; border: 1px solid #E3EAE5; font-size: 13.5px; line-height: 1.55; color: #3E5046; }
.field-label { display: block; margin: 0 0 6px; font-size: 13px; font-weight: 700; color: #22362C; }
.optional { font-weight: 500; color: #7A8F84; }
.field-input { width: 100%; padding: 12px 14px; border-radius: 14px; border: 1.5px solid #DCE5DF; background: #F7FAF8; font-family: inherit; font-size: 14.5px; color: #14261E; resize: vertical; }
.field-input:focus { outline: none; border-color: #004D3A; background: #FFFFFF; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.char-count { margin: 4px 0 0; font-size: 12px; text-align: right; color: #7A8F84; }
.star-row { display: flex; align-items: center; gap: 4px; margin: 0 0 18px; padding: 12px 14px; border-radius: 14px; background: #FBF8EC; }
.star-btn { display: flex; padding: 2px; border: none; border-radius: 8px; background: none; cursor: pointer; transition: transform .15s; }
.star-btn:hover { transform: scale(1.1); }
.star-label { margin-left: 10px; font-size: 14px; font-weight: 700; color: #7A5A00; }

/* ---------- smaller screens ---------- */
@media (max-width: 1100px) {
  .ap-banner { flex-wrap: wrap; }
  .ap-banner-stats { grid-template-columns: repeat(3, minmax(0, 1fr)); width: 100%; }
  .ap-steps { grid-template-columns: 1fr; }
}

/* phone: same layout as the approved mobile design */
@media (max-width: 640px) {
  .appointments-page { gap: 16px; }
  .ap-banner { padding: 20px 18px 18px; border-radius: 22px; gap: 16px; }
  .ap-banner-plate { width: 200px; height: 200px; right: -70px; top: 40px; transform: none; }
  .ap-title { font-size: 25px; }
  .page-sub { margin-bottom: 14px; font-size: 13.5px; }
  .ap-banner .ap-btn-gold { width: 100%; }
  .ap-banner-stats { gap: 8px; }
  .ap-banner-stats > div { padding: 10px 12px; border-radius: 14px; }
  .ap-banner-stats strong { font-size: 22px; }
  .ap-banner-stats span { font-size: 11.5px; }

  .section-title { font-size: 20px; }
  .panel { padding: 18px 16px; border-radius: 18px; }

  /* empty upcoming: icon + text, button full width, steps as three small tiles */
  .up-empty { padding: 20px 16px; }
  .up-empty-row { gap: 14px; }
  .up-empty-icon { width: 56px; height: 56px; border-radius: 18px; }
  .up-empty-text { min-width: 0; flex: 1 1 calc(100% - 80px); }
  .up-empty-title { font-size: 18px; }
  .up-empty .ap-btn-gold { width: 100%; }
  .ap-steps { grid-template-columns: repeat(3, 1fr); gap: 6px; margin: 16px 0 0; padding: 12px 8px; border-radius: 14px; background: #F7FAF8; border: 1px dashed #DCE5DF; }
  .ap-step { flex-direction: column; align-items: center; gap: 6px; text-align: center; }
  .ap-step > span { width: 24px; height: 24px; font-size: 11.5px; }
  .ap-step strong { font-size: 11.5px; line-height: 1.3; }
  .ap-step p { display: none; }

  /* upcoming card */
  .up-head { flex-wrap: wrap; gap: 12px; }
  .ap-date { width: 52px; height: 56px; border-radius: 14px; }
  .ap-date strong { font-size: 21px; }
  .up-time { font-size: 23px; }
  .up-head .dot-status { order: 3; }
  .appt-actions { gap: 8px; }
  .appt-actions > .nm-btn-dark,
  .appt-actions > .nm-btn-soft { flex: 1; }
  .cancel-btn { margin-left: 0; width: 100%; }

  /* history: chips scroll; compact rows */
  .section-head { flex-direction: column; align-items: stretch; }
  .filter-tabs { display: flex; width: 100%; }
  .history-panel { padding: 4px 14px 8px; }
  .h-row { grid-template-columns: 48px minmax(0, 1fr); gap: 4px 12px; padding: 14px 2px; }
  .h-row.is-cancelled::before,
  .h-row.is-no_show::before,
  .h-row.is-completed::before { left: -14px; }
  .h-date { width: 48px; height: 52px; border-radius: 12px; }
  .h-date strong { font-size: 19px; }
  .h-title { font-size: 14.5px; }
  .h-side { grid-column: 2; align-items: flex-start; flex-direction: row; flex-wrap: wrap; }

  .appointments-page .nm-modal { padding: 24px 18px 18px; border-radius: 20px; }
  .appointments-page .nm-modal-actions > * { flex: 1; }
  .field-input { font-size: 16px; } /* stops iPhone zoom on tap */
}
@media (prefers-reduced-motion: reduce) {
  .ap-spin { animation: none; }
}
</style>