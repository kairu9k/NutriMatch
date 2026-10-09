<template>
  <div class="appointments-page">
    <!-- ============ RND VIEW (unchanged from before) ============ -->
    <template v-if="isRnd">
      <div class="page-header">
        <div>
          <h1 class="page-title">Appointments</h1>
          <p class="page-sub">Manage your upcoming and past consultations.</p>
        </div>
      </div>

      <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

      <div v-if="appointments.length" class="filter-tabs">
        <button
          v-for="f in filters"
          :key="f.label"
          class="filter-tab"
          :class="{ active: activeFilter === f.label }"
          @click="activeFilter = f.label"
        >
          {{ f.label }}
        </button>
      </div>

      <div v-if="isLoading" class="empty-state">
        <p class="empty-title">Loading appointments…</p>
      </div>

      <div v-else-if="appointments.length" class="appt-list">
        <div
          v-if="filteredAppointments.length"
          v-for="appt in filteredAppointments"
          :key="appt.id"
          class="appt-card"
          :class="{ 'appt-completed': appt.status === 'completed' }"
        >
          <div class="appt-date" :class="{ 'date-muted': appt.status === 'completed' }">
            <span class="appt-day">{{ appt.day }}</span>
            <span class="appt-month">{{ appt.month }}</span>
          </div>
          <div class="appt-avatar" :style="{ background: appt.avatarColor }">{{ appt.initials }}</div>
          <div class="appt-info">
            <p class="appt-name">
              {{ appt.otherPartyName }}
              <span class="appt-status-pill" :class="statusPillClass(appt.status)">{{ statusLabel(appt.status) }}</span>
            </p>
            <p class="appt-detail">{{ appt.detail }}</p>
          </div>
          <div class="appt-action">
            <span v-if="actionError[appt.id]" class="appt-note">{{ actionError[appt.id] }}</span>
            <!-- Pending bookings are accepted/declined from the screening popup,
                 so the RND reviews the client's screening before deciding. -->
            <button v-if="appt.status === 'pending'" class="confirm-btn" @click="openScreening(appt)">View Screening</button>
            <button v-else-if="appt.status !== 'cancelled'" class="chart-btn" @click="openScreening(appt)">View Screening</button>
            <NuxtLink v-if="appt.status === 'confirmed' && appt.hasVideoRoom" :to="`/consultation-room/${appt.id}`" class="join-btn">Join Call</NuxtLink>
            <button v-if="appt.status === 'confirmed'" class="start-session-btn" :disabled="busyId === appt.id" @click="completeTarget = appt">Mark Completed</button>
            <button v-if="appt.status === 'confirmed'" class="decline-btn" :disabled="busyId === appt.id" @click="cancelAppointment(appt)">Cancel</button>
            <button v-if="appt.status === 'confirmed' || appt.status === 'completed'" class="chart-btn" @click="navigateTo(`/client-detail/${appt.relationshipId}`)">
              {{ appt.status === 'completed' ? 'View NCP Record' : 'View Chart' }}
            </button>
          </div>
        </div>
        <p v-if="!filteredAppointments.length" class="empty-text">No appointments match this filter.</p>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon"><CalendarDays :size="28" /></div>
        <p class="empty-title">No appointments yet</p>
        <p class="empty-desc">Once patients book sessions with you, they'll show up here.</p>
      </div>

      <!-- MARK COMPLETED CONFIRMATION -->
      <div v-if="completeTarget" class="scr-overlay" @click.self="completeTarget = null">
        <div class="scr-box scr-box-small">
          <div class="scr-header">
            <div>
              <h2 class="scr-title">Mark consultation complete?</h2>
              <p class="scr-sub">{{ completeTarget.otherPartyName }} · {{ completeTarget.detail }}</p>
            </div>
          </div>
          <p class="scr-banner">
            <AlertTriangle :size="15" class="scr-banner-icon" />
            This sends {{ completeTarget.otherPartyName }} an invoice for your consultation fee. It can't be undone.
          </p>
          <p v-if="actionError[completeTarget.id]" class="form-error">{{ actionError[completeTarget.id] }}</p>
          <div class="scr-actions">
            <button class="scr-decline-btn scr-neutral-btn" :disabled="busyId === completeTarget.id" @click="completeTarget = null">Not yet</button>
            <button class="scr-accept-btn" :disabled="busyId === completeTarget.id" @click="confirmComplete">
              {{ busyId === completeTarget.id ? 'Completing…' : 'Mark Completed' }}
            </button>
          </div>
        </div>
      </div>

      <!-- PRE-CONSULTATION SCREENING POPUP (same look as the NCP record modal) -->
      <div v-if="screeningTarget" class="scr-overlay" @click.self="closeScreening">
        <div class="scr-box">
          <div class="scr-header">
            <div>
              <h2 class="scr-title">Pre-Consultation Screening</h2>
              <p class="scr-sub">{{ screeningTarget.detail }}</p>
            </div>
            <div class="scr-patient-chip">
              <span class="scr-patient-avatar">{{ screeningTarget.initials }}</span>
              {{ screeningTarget.otherPartyName }}
            </div>
          </div>

          <p v-if="screeningLoading" class="scr-muted">Loading screening…</p>
          <p v-else-if="screeningError" class="form-error">{{ screeningError }}</p>

          <template v-else-if="screeningData">
            <div class="scr-body">
              <span class="scr-eyebrow">CLIENT DETAILS</span>
              <div class="scr-grid-3">
                <div>
                  <label class="scr-label">Age</label>
                  <input class="scr-input" :value="screeningData.client.age ?? '—'" disabled />
                </div>
                <div>
                  <label class="scr-label">Sex</label>
                  <input class="scr-input" :value="capitalize(screeningData.client.sex) || '—'" disabled />
                </div>
                <div>
                  <label class="scr-label">Consultation</label>
                  <input class="scr-input" :value="capitalize(screeningData.appointment.type.replace('_', ' '))" disabled />
                </div>
              </div>
              <div class="scr-grid-2">
                <div>
                  <label class="scr-label">Medical Conditions</label>
                  <input class="scr-input" :value="listText(screeningData.client.medical_conditions)" disabled />
                </div>
                <div>
                  <label class="scr-label">Allergies</label>
                  <input class="scr-input" :value="listText(screeningData.client.allergies)" disabled />
                </div>
              </div>
              <label class="scr-label">Notes for the RND</label>
              <textarea class="scr-textarea" rows="2" :value="screeningData.appointment.notes || 'No notes added.'" disabled></textarea>

              <template v-if="screeningData.screening">
                <span class="scr-eyebrow">SCREENING — SUBMITTED {{ formatDate(screeningData.screening.created_at) }}</span>
                <div class="scr-grid-3">
                  <div>
                    <label class="scr-label">Height (cm)</label>
                    <input class="scr-input" :value="screeningData.screening.height_cm" disabled />
                  </div>
                  <div>
                    <label class="scr-label">Weight (kg)</label>
                    <input class="scr-input" :value="screeningData.screening.weight_kg" disabled />
                  </div>
                  <div>
                    <label class="scr-label">Activity Level</label>
                    <input class="scr-input" :value="activityLabel(screeningData.screening.activity_level)" disabled />
                  </div>
                </div>
                <label class="scr-label">Current Symptoms</label>
                <textarea class="scr-textarea" rows="2" :value="screeningData.screening.symptoms || 'None reported.'" disabled></textarea>

                <div class="scr-results-box">
                  <span class="scr-results-label">COMPUTED · MIFFLIN-ST JEOR · WHO ASIA-PACIFIC · NRS-2002</span>
                  <div class="scr-results-grid">
                    <div class="scr-result-item">
                      <p class="scr-result-value">{{ screeningData.screening.bmi ?? '—' }}</p>
                      <p class="scr-result-label">BMI · {{ screeningData.screening.bmi_category || '—' }}</p>
                    </div>
                    <div class="scr-result-item">
                      <p class="scr-result-value">{{ wholeNumber(screeningData.screening.bmr_kcal) }}</p>
                      <p class="scr-result-label">BMR kcal/day</p>
                    </div>
                    <div class="scr-result-item">
                      <p class="scr-result-value">{{ wholeNumber(screeningData.screening.tdee_kcal) }}</p>
                      <p class="scr-result-label">TDEE kcal/day</p>
                    </div>
                    <div class="scr-result-item">
                      <p class="scr-result-value">{{ screeningData.screening.nrs_score ?? '—' }}</p>
                      <p class="scr-result-label">NRS-2002 · {{ riskLabel(screeningData.screening.nrs_risk) }}</p>
                    </div>
                  </div>
                </div>
              </template>
              <p v-else class="scr-banner">
                <AlertTriangle :size="15" class="scr-banner-icon" />
                This client hasn't submitted a pre-consultation screening yet, so the booking can't be accepted.
              </p>
            </div>

            <p v-if="actionError[screeningTarget.id]" class="form-error">{{ actionError[screeningTarget.id] }}</p>

            <div v-if="screeningTarget.status === 'pending'" class="scr-actions">
              <button class="scr-decline-btn" :disabled="busyId === screeningTarget.id" @click="decideBooking('decline')">Decline</button>
              <button
                class="scr-accept-btn"
                :disabled="busyId === screeningTarget.id || !screeningData.screening"
                @click="decideBooking('accept')"
              >
                {{ busyId === screeningTarget.id ? 'Saving…' : 'Accept Booking' }}
              </button>
            </div>
            <div v-else class="scr-actions">
              <button class="scr-accept-btn" @click="closeScreening">Close</button>
            </div>
          </template>
        </div>
      </div>
    </template>

    <!-- ============ CLIENT VIEW ============ -->
    <template v-else>
      <div class="page-header">
        <div>
          <h1 class="page-title">My Appointments</h1>
          <p class="page-count">{{ filteredAppointments.length }} {{ filteredAppointments.length === 1 ? 'appointment' : 'appointments' }}</p>
        </div>
        <NuxtLink to="/find-rnd" class="primary-btn"><Plus :size="15" /> Book New Appointment</NuxtLink>
      </div>

      <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

      <div v-if="appointments.length" class="filter-tabs pill-tabs">
        <button v-for="f in filters" :key="f.label" class="filter-tab" :class="{ active: activeFilter === f.label }" @click="activeFilter = f.label">
          {{ f.shortLabel || f.label }}
        </button>
      </div>

      <div v-if="isLoading" class="empty-state">
        <p class="empty-title">Loading appointments…</p>
      </div>

      <div v-else class="appt-list">
        <div v-if="!appointments.length" class="empty-state">
          <CalendarX :size="28" class="empty-icon" />
          <p class="empty-title">No appointments yet</p>
          <p class="empty-sub">Once you book a session with an RND, it'll show up here.</p>
          <NuxtLink to="/find-rnd" class="primary-btn" style="margin-top: 12px;">Book Appointment</NuxtLink>
        </div>
        <div v-else-if="!filteredAppointments.length" class="empty-state">
          <CalendarX :size="28" class="empty-icon" />
          <p class="empty-title">No {{ activeFilter === 'All' ? '' : activeFilter.toLowerCase() + ' ' }}appointments</p>
        </div>

        <div v-for="appt in filteredAppointments" :key="appt.id" class="appt-card" :class="[statusAccent(appt.status), { dimmed: appt.status === 'cancelled' }]">
          <div class="appt-date-block" :class="dateBlockClass(appt.status)">
            <span class="d-num">{{ appt.day }}</span>
            <span class="d-mon">{{ appt.month }}</span>
          </div>

          <div class="appt-info">
            <div class="appt-info-row">
              <span class="appt-rnd">{{ appt.otherPartyName }}</span>
              <span class="status-pill" :class="pillClass(appt.status)">{{ statusLabel(appt.status) }}</span>
            </div>
            <p class="appt-meta"><CalendarDays :size="13" /> {{ appt.dateLabel }} <span class="dot">·</span> <Clock :size="13" /> {{ appt.timeLabel }}</p>
            <p v-if="actionError[appt.id]" class="appt-note">{{ actionError[appt.id] }}</p>
          </div>

          <div class="modality-icon" :class="dateBlockClass(appt.status)">
            <component :is="appt.type === 'video' ? Video : MessageCircle" :size="16" />
          </div>

          <div class="appt-actions">
            <NuxtLink v-if="appt.status === 'confirmed' && appt.hasVideoRoom" :to="`/consultation-room/${appt.id}`" class="primary-btn small"><Video :size="14" /> Join Video Call</NuxtLink>
            <button v-if="appt.status === 'pending'" class="outline-btn small" disabled><Hourglass :size="13" /> Awaiting Confirmation</button>
            <NuxtLink v-if="appt.status === 'completed'" to="/invoices-billing" class="outline-btn small"><Receipt :size="13" /> View Invoice</NuxtLink>
            <button v-if="appt.status === 'completed' && !appt.hasReview" class="outline-btn small" :disabled="busyId === appt.id" @click="openReviewModal(appt)"><Star :size="13" /> Leave Review</button>
            <NuxtLink v-if="appt.status === 'cancelled'" to="/find-rnd" class="outline-btn small"><RotateCcw :size="13" /> Book Again</NuxtLink>
            <button v-if="appt.status === 'confirmed' || appt.status === 'pending'" class="ghost-btn small" :disabled="busyId === appt.id" @click="openCancelModal(appt)">Cancel</button>
          </div>
        </div>
      </div>

      <!-- CANCEL MODAL -->
      <div v-if="cancelTarget" class="modal-overlay" @click.self="closeCancelModal">
        <div class="modal-box">
          <div class="modal-title-row">
            <AlertTriangle :size="18" class="modal-warn-icon" />
            <h3 class="modal-title">Cancel Appointment?</h3>
          </div>
          <label class="field-label">Reason for cancellation <span class="optional">(optional)</span></label>
          <textarea v-model="cancelReason" rows="2" placeholder="Let your RND know why..."></textarea>
          <p v-if="cancelError" class="form-error">{{ cancelError }}</p>
          <div class="modal-actions">
            <button class="ghost-btn" :disabled="isCancelling" @click="closeCancelModal">Keep Appointment</button>
            <button class="danger-outline-btn" :disabled="isCancelling" @click="confirmCancel">{{ isCancelling ? 'Cancelling…' : 'Confirm Cancellation' }}</button>
          </div>
        </div>
      </div>

      <!-- REVIEW MODAL -->
      <div v-if="reviewTarget" class="modal-overlay" @click.self="closeReviewModal">
        <div class="modal-box">
          <h3 class="modal-title">Rate Your Consultation</h3>
          <div class="star-row">
            <Star
              v-for="n in 5" :key="n" :size="26"
              :fill="n <= reviewStars ? '#D4A017' : 'none'"
              :stroke="n <= reviewStars ? '#D4A017' : '#c8c8c8'"
              @click="reviewStars = n"
              style="cursor: pointer;"
            />
          </div>
          <textarea v-model="reviewText" rows="3" placeholder="Share your experience..."></textarea>
          <p v-if="reviewError" class="form-error">{{ reviewError }}</p>
          <div class="modal-actions">
            <button class="ghost-btn" :disabled="isSubmittingReview" @click="closeReviewModal">Cancel</button>
            <button class="primary-btn" :disabled="isSubmittingReview" @click="submitReview">{{ isSubmittingReview ? 'Submitting…' : 'Submit Review' }}</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  CalendarDays, Plus, Video, MessageCircle, AlertTriangle, Star, Clock, CalendarX, Hourglass, Receipt, RotateCcw,
} from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Appointments' })

const auth = useAuthStore()
const { get, patch, post } = useApi()

const isRnd = computed(() => auth.user?.role === 'rnd')

const activeFilter = ref('All')
const isLoading = ref(true)
const errorMessage = ref('')
const busyId = ref(null)
const actionError = reactive({})

const filters = [
  { label: 'All' },
  { label: 'Pending Confirmation', shortLabel: 'Pending' },
  { label: 'Confirmed' },
  { label: 'Completed' },
  { label: 'Cancelled' },
]

const AVATAR_COLORS = ['#1e4a26', '#3a6b3a', '#D4A017', '#6a8a6a', '#8a6a3a']

function colorForId(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}

function initialsFor(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
}

const rawAppointments = ref([])
const reviewedAppointmentIds = ref(new Set())

const appointments = computed(() => rawAppointments.value.map((appt) => {
  const otherParty = isRnd.value ? appt.relationship.client : appt.relationship.rnd
  const scheduled = new Date(appt.scheduled_at)
  return {
    id: appt.id,
    relationshipId: appt.relationship.id,
    rndId: appt.relationship.rnd.id,
    status: appt.status,
    otherPartyName: `${isRnd.value ? '' : 'RND '}${otherParty.first_name} ${otherParty.last_name}`,
    initials: initialsFor(otherParty),
    avatarColor: colorForId(otherParty.id),
    day: scheduled.toLocaleDateString('en-US', { day: 'numeric' }),
    month: scheduled.toLocaleDateString('en-US', { month: 'short' }).toUpperCase(),
    detail: `${scheduled.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })} · ${scheduled.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })} · ${appt.type.replace('_', ' ')}`,
    dateLabel: scheduled.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }),
    timeLabel: appt.status === 'cancelled'
      ? `Cancelled${appt.cancellation_reason ? ': ' + appt.cancellation_reason : ''}`
      : scheduled.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' }),
    type: appt.type,
    hasVideoRoom: Boolean(appt.video_session_url),
    hasReview: reviewedAppointmentIds.value.has(appt.id),
  }
}))

const filteredAppointments = computed(() => {
  if (activeFilter.value === 'All') return appointments.value
  if (activeFilter.value === 'Pending Confirmation') {
    return appointments.value.filter(a => a.status === 'pending')
  }
  const map = { Confirmed: 'confirmed', Completed: 'completed', Cancelled: 'cancelled' }
  return appointments.value.filter(a => a.status === map[activeFilter.value])
})

function statusLabel(status) {
  return { pending: 'Pending Confirmation', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }[status] || status
}
function statusPillClass(status) {
  return { pending: 'pending', confirmed: 'confirmed', completed: 'completed', cancelled: 'awaiting' }[status] || ''
}
function pillClass(status) {
  return { confirmed: 'pill-green', pending: 'pill-gold', completed: 'pill-muted', cancelled: 'pill-red' }[status] || 'pill-muted'
}
function statusAccent(status) {
  return { confirmed: 'accent-green', pending: 'accent-gold', completed: 'accent-muted', cancelled: 'accent-red' }[status] || 'accent-muted'
}
function dateBlockClass(status) {
  return { confirmed: 'tint-green', pending: 'tint-gold', completed: 'tint-muted', cancelled: 'tint-muted' }[status] || 'tint-muted'
}

async function loadAppointments() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const path = isRnd.value ? '/rnd/appointments/' : '/client/appointments/'
    rawAppointments.value = await get(path)
    if (!isRnd.value) {
      const myReviews = await get('/client/reviews/').catch(() => [])
      reviewedAppointmentIds.value = new Set(myReviews.map(r => r.appointment))
    }
  } catch {
    errorMessage.value = 'Could not load appointments. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

async function runTransition(appt, path) {
  busyId.value = appt.id
  delete actionError[appt.id]
  try {
    await patch(path)
    await loadAppointments()
    return true
  } catch (error) {
    actionError[appt.id] = error?.data?.detail || 'Action failed. Please try again.'
    return false
  } finally {
    busyId.value = null
  }
}

// Completing creates the client's invoice and can't be undone, so it goes
// through a confirmation popup first.
const completeTarget = ref(null)
async function confirmComplete() {
  const appt = completeTarget.value
  if (await runTransition(appt, `/rnd/appointments/${appt.id}/complete/`)) completeTarget.value = null
}

function cancelAppointment(appt) {
  runTransition(appt, `/rnd/appointments/${appt.id}/cancel/`)
}

/* ---------- RND: SCREENING POPUP (accept / decline a booking) ---------- */
const screeningTarget = ref(null)
const screeningData = ref(null)
const screeningLoading = ref(false)
const screeningError = ref('')

async function openScreening(appt) {
  screeningTarget.value = appt
  screeningData.value = null
  screeningError.value = ''
  delete actionError[appt.id]
  screeningLoading.value = true
  try {
    screeningData.value = await get(`/rnd/appointments/${appt.id}/screening/`)
  } catch (error) {
    screeningError.value = error?.data?.detail || 'Could not load the screening. Please try again.'
  } finally {
    screeningLoading.value = false
  }
}
function closeScreening() {
  screeningTarget.value = null
}
async function decideBooking(decision) {
  const appt = screeningTarget.value
  const path = decision === 'accept'
    ? `/rnd/appointments/${appt.id}/confirm/`
    : `/rnd/appointments/${appt.id}/cancel/`
  if (await runTransition(appt, path)) closeScreening()
}

const ACTIVITY_LABELS = {
  sedentary: 'Sedentary', lightly_active: 'Lightly Active', moderately_active: 'Moderately Active',
  very_active: 'Very Active', extra_active: 'Extra Active',
}
const RISK_LABELS = { no_risk: 'No Risk', at_risk: 'At Risk', high_risk: 'High Risk' }
function activityLabel(value) { return ACTIVITY_LABELS[value] || '—' }
function riskLabel(value) { return RISK_LABELS[value] || '—' }
function capitalize(value) { return value ? value.charAt(0).toUpperCase() + value.slice(1) : '' }
function listText(list) { return list?.length ? list.join(', ') : 'None' }
function wholeNumber(value) { return value == null ? '—' : Math.round(Number(value)).toLocaleString('en-US') }
function formatDate(value) {
  return new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase()
}

/* ---------- CLIENT: CANCEL MODAL ---------- */
const cancelTarget = ref(null)
const cancelReason = ref('')
const isCancelling = ref(false)
const cancelError = ref('')
function openCancelModal(appt) { cancelTarget.value = appt; cancelReason.value = ''; cancelError.value = '' }
function closeCancelModal() { cancelTarget.value = null }
async function confirmCancel() {
  if (!cancelTarget.value) return
  isCancelling.value = true
  cancelError.value = ''
  try {
    await patch(`/client/appointments/${cancelTarget.value.id}/cancel/`, { reason: cancelReason.value || undefined })
    closeCancelModal()
    await loadAppointments()
  } catch (error) {
    cancelError.value = error?.data?.detail || 'Could not cancel this appointment. Please try again.'
  } finally {
    isCancelling.value = false
  }
}

/* ---------- CLIENT: REVIEW MODAL ---------- */
const reviewTarget = ref(null)
const reviewStars = ref(5)
const reviewText = ref('')
const isSubmittingReview = ref(false)
const reviewError = ref('')
function openReviewModal(appt) { reviewTarget.value = appt; reviewStars.value = 5; reviewText.value = ''; reviewError.value = '' }
function closeReviewModal() { reviewTarget.value = null }
async function submitReview() {
  if (!reviewTarget.value) return
  isSubmittingReview.value = true
  reviewError.value = ''
  try {
    await post('/client/reviews/', {
      appointment: reviewTarget.value.id,
      rnd: reviewTarget.value.rndId,
      rating: reviewStars.value,
      comment: reviewText.value || undefined,
    })
    closeReviewModal()
    await loadAppointments()
  } catch (error) {
    reviewError.value = error?.data?.non_field_errors?.[0] || error?.data?.detail || 'Could not submit your review. Please try again.'
  } finally {
    isSubmittingReview.value = false
  }
}

onMounted(loadAppointments)
</script>

<style scoped>
* { box-sizing: border-box; }

.appointments-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }
.page-count { font-size: 0.85rem; color: #9aaa9a; margin: 0; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}

/* FILTER TABS (RND: rounded rect tabs; client: pill tabs) */
.filter-tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.filter-tab {
  border: 1px solid #e5e8e5; background: #fff; color: #4a5a4a;
  border-radius: 20px; padding: 9px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.filter-tab.active { background: #14301a; color: #fff; border-color: #14301a; }
.filter-tabs.pill-tabs {
  background: #fff; padding: 5px; border-radius: 999px; border: 1px solid #eceeec;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03); width: fit-content; gap: 4px;
}
.pill-tabs .filter-tab { border: none; padding: 8px 18px; }
.pill-tabs .filter-tab:hover:not(.active) { background: #f7f9f7; color: #4a5a4a; }

/* APPOINTMENT LIST (RND card style) */
.appt-list { display: flex; flex-direction: column; gap: 16px; }
.appt-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px 22px;
  display: flex; align-items: center; gap: 16px;
}
.appt-card.appt-completed { opacity: 0.7; }

.appt-date {
  width: 52px; height: 52px; border-radius: 8px; background: #eef3ec;
  display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0;
}
.appt-date.date-muted { background: #eceeec; }
.appt-day { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #1a3a1a; line-height: 1; }
.appt-month { font-size: 0.62rem; letter-spacing: 0.05em; color: #6a7a6a; margin-top: 2px; }

.appt-avatar {
  width: 32px; height: 32px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;
}

.appt-info { flex: 1; min-width: 200px; }
.appt-name { display: flex; align-items: center; gap: 10px; font-size: 0.95rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.appt-status-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.appt-status-pill.confirmed { background: #e6efe0; color: #3a6b3a; }
.appt-status-pill.awaiting { background: #eceeec; color: #7a8a7a; }
.appt-status-pill.pending { background: #faead0; color: #b8860b; }
.appt-status-pill.completed { background: #eceeec; color: #7a8a7a; }
.appt-detail { font-size: 0.8rem; color: #6a7a6a; margin: 0; }

.appt-action { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.appt-note { font-size: 0.82rem; color: #a12525; background: #fdecec; padding: 10px 16px; border-radius: 8px; max-width: 320px; text-align: right; }

.start-session-btn, .confirm-btn, .join-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 10px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; white-space: nowrap;
  text-decoration: none; display: inline-block;
}
.start-session-btn:disabled, .confirm-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.decline-btn {
  background: none; border: none; color: #8a9a8a; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.decline-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.chart-btn {
  border: 1px solid #d5dad5; background: #fff; color: #2a2a2a;
  border-radius: 8px; padding: 10px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; white-space: nowrap;
}

/* CLIENT: accent-bordered card style */
.appt-card.accent-green, .appt-card.accent-gold, .appt-card.accent-red, .appt-card.accent-muted {
  border-left-width: 4px; flex-wrap: wrap;
  box-shadow: 0 1px 2px rgba(0,0,0,0.03); transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.appt-card:hover { box-shadow: 0 6px 18px rgba(0,0,0,0.06); }
.appt-card.dimmed { opacity: 0.7; }
.appt-card.accent-green { border-left-color: #1f8f5c; }
.appt-card.accent-green:hover { border-color: #1f8f5c; }
.appt-card.accent-gold { border-left-color: #D4A017; }
.appt-card.accent-gold:hover { border-color: #D4A017; }
.appt-card.accent-red { border-left-color: #e3a49a; }
.appt-card.accent-muted { border-left-color: #d5dad5; }

.appt-date-block { width: 60px; height: 60px; border-radius: 10px; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; }
.tint-green { background: #e3f3ea; }
.tint-green .d-num { color: #1f8f5c; }
.tint-gold { background: #fdf1d6; }
.tint-gold .d-num { color: #b8860b; }
.tint-muted { background: #f2f3f1; }
.tint-muted .d-num { color: #9aaa9a; }
.appt-date-block .d-num { font-weight: 700; font-size: 1.25rem; line-height: 1; }
.appt-date-block .d-mon { font-size: 0.65rem; color: #9aaa9a; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px; }

.appt-info-row { display: flex; align-items: center; gap: 8px; }
.appt-rnd { font-weight: 700; color: #1a3a1a; font-size: 0.94rem; }
.appt-meta { display: flex; align-items: center; gap: 5px; font-size: 0.8rem; color: #9aaa9a; margin: 5px 0 0; }
.appt-meta .dot { margin: 0 1px; }

.modality-icon { width: 34px; height: 34px; border-radius: 50%; color: #1a3a1a; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.modality-icon.tint-green { color: #1f8f5c; }
.modality-icon.tint-gold { color: #b8860b; }
.modality-icon.tint-muted { color: #9aaa9a; }

.appt-actions { display: flex; gap: 8px; flex-wrap: wrap; }

.status-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-gold { background: #fdf1d6; color: #b8860b; }
.pill-muted { background: #eceeec; color: #8a9a8a; }
.pill-red { background: #fbe5e2; color: #c0392b; }

.primary-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 10px 16px; font-weight: 700; font-size: 0.85rem; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; text-decoration: none; }
.primary-btn.small { padding: 8px 14px; font-size: 0.8rem; }
.outline-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 10px 16px; font-weight: 600; font-size: 0.85rem; cursor: pointer; text-decoration: none; display: inline-flex; align-items: center; gap: 6px; }
.outline-btn.small { padding: 8px 14px; font-size: 0.8rem; }
.outline-btn:hover:not(:disabled) { background: #f7f9f7; }
.outline-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.ghost-btn { background: none; border: none; color: #8a9a8a; font-weight: 600; font-size: 0.85rem; cursor: pointer; padding: 10px 12px; }
.ghost-btn:hover:not(:disabled) { color: #c0392b; }
.ghost-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.ghost-btn.small { padding: 8px 10px; font-size: 0.8rem; }
.danger-outline-btn { border: 1px solid #c0392b; background: #fff; color: #c0392b; border-radius: 8px; padding: 10px 16px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }
.danger-outline-btn:disabled { opacity: 0.55; cursor: not-allowed; }

/* MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(20,30,20,0.45); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 16px; }
.modal-box { background: #fff; border-radius: 14px; padding: 26px; width: 100%; max-width: 420px; }
.modal-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 14px; }
.modal-warn-icon { color: #c0392b; }
.modal-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 14px; }
.modal-title-row .modal-title { margin: 0; }
.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #4a5a4a; margin-bottom: 8px; }
.optional { font-weight: 400; color: #9aaa9a; }
.modal-box textarea { width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; resize: vertical; margin-bottom: 16px; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
.star-row { display: flex; gap: 6px; justify-content: center; margin-bottom: 16px; }

/* EMPTY STATE */
.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; text-transform: capitalize; }
.empty-desc, .empty-sub { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
.empty-text { font-size: 0.85rem; color: #9aaa9a; padding: 20px; text-align: center; }

@media (max-width: 640px) {
  .appt-card.accent-green, .appt-card.accent-gold, .appt-card.accent-red, .appt-card.accent-muted { flex-direction: column; align-items: flex-start; }
  .appt-actions { width: 100%; }
}
/* ============ RND SCREENING POPUP — mirrors the NCP record modal (NCPRecords.vue) ============ */
.scr-overlay {
  position: fixed; inset: 0; background: rgba(20,30,20,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100; padding: 20px;
}
.scr-box {
  background: #fff; border-radius: 16px; width: 100%; max-width: 560px;
  max-height: 90vh; overflow-y: auto; padding: 28px;
}
.scr-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 18px; padding-bottom: 16px; border-bottom: 1px solid #eceeec; }
.scr-title { font-family: 'Playfair Display', serif; font-size: 1.3rem; color: #1a3a1a; margin: 0 0 4px; }
.scr-sub { font-size: 0.82rem; color: #8a9a8a; margin: 0; text-transform: capitalize; }
.scr-patient-chip {
  display: flex; align-items: center; gap: 8px; border: 1px solid #e5e8e5; border-radius: 20px;
  padding: 6px 14px 6px 6px; font-size: 0.82rem; font-weight: 700; color: #1a3a1a; white-space: nowrap;
}
.scr-patient-avatar {
  width: 26px; height: 26px; border-radius: 50%; background: #14301a; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; flex-shrink: 0;
}
.scr-muted { font-size: 0.85rem; color: #8a9a8a; }
.scr-body { display: flex; flex-direction: column; }
.scr-eyebrow { font-size: 0.68rem; letter-spacing: 0.08em; color: #b8860b; font-weight: 700; margin: 4px 0 16px; }
.scr-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 16px; }
.scr-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin-bottom: 16px; }
.scr-label { display: block; font-size: 0.82rem; font-weight: 600; color: #2a2a2a; margin: 0 0 6px; }
.scr-input, .scr-textarea {
  width: 100%; border: 1px solid #e5e8e5; border-radius: 8px; padding: 11px 14px; font-family: inherit;
  font-size: 0.86rem; background: #f4f6f4; color: #4a5a4a; margin-bottom: 4px;
}
.scr-textarea { resize: none; margin-bottom: 18px; }
.scr-results-box { background: #f4f8f5; border: 1px solid #dbe8dd; border-radius: 10px; padding: 16px; margin: 0 0 20px; }
.scr-results-label { display: block; font-size: 0.66rem; letter-spacing: 0.06em; color: #6a8a70; font-weight: 700; margin-bottom: 12px; }
.scr-results-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.scr-result-item { background: #fff; border-radius: 8px; padding: 10px; text-align: center; }
.scr-result-value { font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.scr-result-label { font-size: 0.68rem; color: #9aaa9a; margin: 4px 0 0; }
.scr-banner {
  display: flex; align-items: center; gap: 8px; background: #fdf8ee; color: #8a6a1a; border-radius: 8px;
  padding: 12px 16px; font-size: 0.82rem; margin: 0 0 20px;
}
.scr-banner-icon { color: #b8860b; flex-shrink: 0; }
.scr-actions { display: flex; align-items: center; gap: 12px; margin-top: 4px; }
.scr-decline-btn {
  border: 1px solid #f0d6d6; background: #fff; color: #c0392b; border-radius: 8px;
  padding: 11px 20px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.scr-decline-btn:hover:not(:disabled) { background: #fbeaea; }
.scr-accept-btn {
  flex: 1; background: #14301a; color: #fff; border: none; border-radius: 8px;
  padding: 12px 20px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}
.scr-box-small { max-width: 460px; }
.scr-neutral-btn { border-color: #d5dad5; color: #4a5a4a; }
.scr-neutral-btn:hover:not(:disabled) { background: #f4f6f4; }
.scr-accept-btn:disabled, .scr-decline-btn:disabled { opacity: 0.55; cursor: not-allowed; }
@media (max-width: 640px) {
  .scr-grid-3, .scr-grid-2 { grid-template-columns: 1fr; }
  .scr-results-grid { grid-template-columns: repeat(2, 1fr); }
  .scr-header { flex-direction: column; }
}
</style>
