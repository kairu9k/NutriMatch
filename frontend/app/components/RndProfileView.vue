<template>
  <div class="profile-page nm-page">
    <p v-if="errorMessage" class="nm-error">{{ errorMessage }}</p>

    <div v-if="isLoading" class="loading-hero"><span class="sk sk-avatar" /><span style="flex: 1"><span class="sk sk-line w40" /><span class="sk sk-line w60" /></span></div>

    <template v-else-if="rnd">
      <p class="breadcrumb"><NuxtLink to="/find-rnd">Find an RND</NuxtLink> / {{ fullName }}</p>

      <!-- hero -->
      <section class="hero">
        <img v-if="rnd.user.profile_photo" :src="rnd.user.profile_photo" class="hero-avatar" alt="" />
        <span v-else class="hero-avatar initials">{{ userInitials(rnd.user.first_name, rnd.user.last_name) }}</span>
        <div class="hero-main">
          <span class="hero-badge"><ShieldCheck :size="13" /> PRC-verified<template v-if="rnd.verified_at"> since {{ monthYear(rnd.verified_at) }}</template></span>
          <h1 class="hero-name">{{ fullName }}</h1>
          <p class="hero-spec">{{ rnd.specialization || 'General / Clinical Nutrition' }}<template v-if="rnd.prc_license_number"> · PRC License No. {{ rnd.prc_license_number }}</template></p>
          <div class="hero-stats">
            <span v-if="rnd.review_count"><Star :size="14" class="gold" /> <strong>{{ rnd.average_rating.toFixed(1) }}</strong> ({{ rnd.review_count }} review{{ rnd.review_count === 1 ? '' : 's' }})</span>
            <span v-else><Star :size="14" /> No reviews yet</span>
            <span><CalendarCheck :size="14" /> <strong>{{ rnd.consultations_completed }}</strong> consultation{{ rnd.consultations_completed === 1 ? '' : 's' }} done</span>
            <span><Users :size="14" /> <strong>{{ rnd.active_patients }}</strong> active patient{{ rnd.active_patients === 1 ? '' : 's' }}</span>
            <span><Clock :size="14" /> On NutriMatch since {{ monthYear(rnd.member_since) }}</span>
          </div>
          <div class="hero-chips">
            <span v-for="l in rnd.languages" :key="l.code" class="hero-chip"><Languages :size="12" /> {{ l.language_name }}</span>
            <span v-for="f in offeredFormats" :key="f.key" class="hero-chip"><component :is="f.icon" :size="12" /> {{ f.short }}</span>
          </div>
        </div>
        <div class="hero-fee">
          <p class="fee-amount">₱{{ formatFee(rnd.consultation_fee) }}</p>
          <p class="fee-unit">per {{ SESSION_MINUTES }}-minute session</p>
        </div>
      </section>

      <div class="nm-grid">
        <div class="nm-col">
          <div class="nm-panel">
            <h2 class="nm-panel-title">About {{ rnd.user.first_name }}</h2>
            <p class="bio-text">{{ rnd.bio || 'This RND has not added a bio yet.' }}</p>
          </div>

          <div class="nm-panel">
            <h2 class="nm-panel-title">How your care works</h2>
            <p class="nm-panel-sub">NutriMatch follows the Nutrition Care Process used by RNDs.</p>
            <ol class="steps">
              <li v-for="(st, i) in CARE_STEPS" :key="st.title">
                <span class="step-num">{{ i + 1 }}</span>
                <span><strong>{{ st.title }}</strong><span class="step-text">{{ st.text }}</span></span>
              </li>
            </ol>
          </div>

          <div class="nm-panel">
            <h2 class="nm-panel-title">Where &amp; how you'll meet</h2>
            <div v-for="f in offeredFormats" :key="f.key" class="nm-row how-row">
              <span class="nm-stat-icon" style="margin: 0"><component :is="f.icon" :size="16" /></span>
              <div class="nm-row-main">
                <p class="nm-row-title">{{ f.label }}</p>
                <p class="nm-row-sub">{{ f.how }}</p>
                <template v-if="f.key === 'in_person'">
                  <p class="address"><MapPin :size="13" /> {{ rnd.clinic_address }}</p>
                  <a :href="mapUrl" target="_blank" rel="noopener" class="nm-panel-link map-link">Open in Google Maps <ExternalLink :size="11" /></a>
                </template>
              </div>
            </div>
            <p v-if="inPersonWithoutAddress" class="nm-note" style="margin: 12px 0 0">
              {{ rnd.user.first_name }} hasn't added a clinic address yet, so in-person consultations can't be booked for now.
            </p>
          </div>

          <div class="nm-panel">
            <h2 class="nm-panel-title">Weekly hours</h2>
            <p class="nm-panel-sub">Philippine time</p>
            <div v-if="isLoadingAvailability" class="nm-muted" style="margin-top: 12px">Loading…</div>
            <div v-else-if="availabilityByDay.some(d => d.slots.length)" class="avail-grid">
              <div v-for="d in availabilityWeekMonFirst" :key="d.day" class="avail-box" :class="{ muted: !d.slots.length }">
                <p class="avail-day">{{ d.short }}</p>
                <p class="avail-hours">{{ d.slots.length ? d.slots.map(s => compactHours(s.start_time, s.end_time)).join(', ') : '—' }}</p>
              </div>
            </div>
            <p v-else class="nm-muted" style="margin-top: 12px">This RND hasn't set their hours yet.</p>
          </div>

          <div class="nm-panel">
            <h2 class="nm-panel-title">Patient reviews</h2>
            <div v-if="rnd.review_count" class="rating-summary">
              <div class="rating-big">
                <p class="rating-num">{{ rnd.average_rating.toFixed(1) }}</p>
                <p class="rating-stars">{{ starText(Math.round(rnd.average_rating)) }}</p>
                <p class="nm-muted">{{ rnd.review_count }} review{{ rnd.review_count === 1 ? '' : 's' }}</p>
              </div>
              <div class="bars">
                <div v-for="star in [5, 4, 3, 2, 1]" :key="star" class="bar-row">
                  <span>{{ star }}★</span>
                  <span class="bar"><span :style="{ width: `${barPct(star)}%` }" /></span>
                  <span class="bar-n">{{ rnd.rating_breakdown?.[star] || 0 }}</span>
                </div>
              </div>
            </div>
            <div v-if="isLoadingReviews" class="nm-muted" style="margin-top: 12px">Loading reviews…</div>
            <div v-else-if="reviews.length">
              <div v-for="review in reviews" :key="review.id" class="nm-row review-row">
                <div class="nm-row-main">
                  <p class="review-top"><span class="nm-row-title">{{ review.client_name }}</span><span class="rating-stars small">{{ starText(review.rating) }}</span></p>
                  <p v-if="review.comment" class="review-comment">"{{ review.comment }}"</p>
                  <p class="nm-row-sub">{{ shortDate(review.created_at) }}</p>
                </div>
              </div>
            </div>
            <p v-else class="nm-muted" style="margin-top: 12px">No reviews yet — be one of {{ rnd.user.first_name }}'s first patients.</p>
          </div>
        </div>

        <!-- booking card -->
        <div class="nm-col side">
          <div class="nm-panel book-card">
            <template v-if="rnd.is_my_rnd">
              <span class="nm-pill green">Your RND</span>
              <p class="book-text">You're already seeing {{ rnd.user.first_name }}. Your appointments and messages are in one place.</p>
              <div class="book-links">
                <NuxtLink to="/appointments" class="nm-btn-outline">My appointments</NuxtLink>
                <NuxtLink to="/messages" class="nm-btn-outline">Messages</NuxtLink>
              </div>
              <div class="divider" />
            </template>

            <p class="book-fee">₱{{ formatFee(rnd.consultation_fee) }} <span>/ {{ SESSION_MINUTES }}-min session</span></p>
            <!-- One RND at a time: booking someone else waits until the current RND discharges them. -->
            <div v-if="rnd.booking_blocked_by" class="one-rnd">
              <p v-if="rnd.booking_blocked_by.status === 'active'">
                You're under <strong>RND {{ rnd.booking_blocked_by.name }}</strong>'s care. You can book a different RND once RND {{ rnd.booking_blocked_by.name }} discharges you.
              </p>
              <p v-else>
                You have a booking waiting for <strong>RND {{ rnd.booking_blocked_by.name }}</strong>. Cancel it first if you'd like a different RND.
              </p>
              <NuxtLink :to="`/rnd-profile-view/${rnd.booking_blocked_by.rnd_id}`" class="nm-panel-link">Go to RND {{ rnd.booking_blocked_by.name }} →</NuxtLink>
            </div>
            <template v-else>
            <p class="nm-section-title" style="margin-top: 14px">Next open times</p>
            <div v-if="rnd.next_open_slots.length" class="slot-grid">
              <button v-for="slot in rnd.next_open_slots" :key="slot" type="button" class="slot" @click="bookSlot(slot)">
                <span class="slot-day">{{ slotDay(slot) }}</span>
                <span class="slot-time">{{ slotTime(slot) }}</span>
              </button>
            </div>
            <p v-else class="nm-muted">No open times in the next 4 weeks.</p>

            <button class="nm-btn-dark book-btn" type="button" :disabled="!offeredFormats.length || !rnd.next_open_slots.length" @click="openBookingModal()">
              <CalendarPlus :size="15" /> {{ rnd.next_open_slots.length ? 'See all times & book' : 'No times available' }}
            </button>
            </template>

            <ul class="policy">
              <li><CreditCard :size="13" /> Pay after {{ rnd.user.first_name }} confirms — before the session starts.</li>
              <li><RotateCcw :size="13" /> Cancel before it starts and a paid session is refunded.</li>
              <li><Clock :size="13" /> Your booking is a request until {{ rnd.user.first_name }} confirms it.</li>
            </ul>

            <!-- Only for clients who haven't screened yet — the RND can't
                 confirm a first appointment without it. -->
            <div v-if="hasScreening === false" class="info-note">
              <Info :size="15" />
              <span>
                Pre-consultation screening is required before your first appointment can be confirmed.
                <NuxtLink to="/pre-consultation-screening" class="info-note-link">Complete it now →</NuxtLink>
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- BOOK APPOINTMENT MODAL -->
    <div v-if="bookingModalOpen" class="modal-overlay" @click.self="closeBookingModal">
      <div class="booking-modal-box">
        <button class="modal-close-btn booking-close" @click="closeBookingModal"><X :size="18" /></button>

        <div class="booking-left">
          <h2 class="booking-title">Book Your <em>Consultation</em></h2>
          <p class="booking-sub">Pick a session format and a time that works — {{ fullName }} will confirm your booking.</p>

          <div class="booking-section">
            <h4 class="section-h">Session Format</h4>
            <div class="format-row">
              <button
                v-for="f in offeredFormats" :key="f.key"
                class="format-card" :class="{ active: bookingType === f.key }"
                type="button"
                @click="bookingType = f.key"
              >
                <component :is="f.icon" :size="17" />
                <span class="format-name">{{ f.label }}</span>
              </button>
            </div>
            <p v-if="bookingType === 'in_person'" class="address booking-address"><MapPin :size="13" /> {{ rnd.clinic_address }}</p>
          </div>

          <div class="booking-section">
            <h4 class="section-h">Pick a Date</h4>
            <p class="section-sub">Based on {{ rnd.user.first_name }}'s weekly hours.</p>

            <div class="calendar-head">
              <span class="calendar-month">{{ viewMonthLabel }}</span>
              <div class="calendar-nav">
                <button type="button" @click="shiftMonth(-1)"><ChevronLeft :size="15" /></button>
                <button type="button" @click="shiftMonth(1)"><ChevronRight :size="15" /></button>
              </div>
            </div>
            <div class="calendar-grid">
              <span v-for="d in dayHeaders" :key="d" class="calendar-day-header">{{ d }}</span>
              <button
                v-for="(cell, i) in calendarCells" :key="i"
                type="button"
                class="calendar-cell"
                :class="{ 'out-month': !cell.inMonth, available: cell.available, selected: cell.iso === selectedDateISO, disabled: !cell.available, 'day-off': cell.dayOff }"
                :disabled="!cell.available"
                :title="cell.dayOff ? 'Day off' : undefined"
                :aria-label="cell.dayOff ? `${cell.day}, day off` : undefined"
                @click="selectDate(cell)"
              >{{ cell.day }}</button>
            </div>
            <p v-if="calendarCells.some(c => c.dayOff)" class="day-off-key"><span class="day-off-swatch" /> Day off — {{ rnd.user.first_name }} isn't taking consultations that day.</p>

            <div v-if="selectedDateISO" class="time-slot-row">
              <button
                v-for="slot in timeSlots" :key="slot.value"
                type="button"
                class="time-slot-btn" :class="{ selected: selectedTime === slot.value, taken: slot.taken }"
                :disabled="slot.taken"
                :title="slot.taken ? (slot.off ? `${rnd.user.first_name} isn't available at this time` : 'Already booked by another client') : undefined"
                @click="selectedTime = slot.value"
              >{{ slot.label }}<span v-if="slot.taken" class="taken-tag">{{ slot.off ? 'Unavailable' : 'Booked' }}</span></button>
              <p v-if="!timeSlots.length" class="availability-warn">No time slots available this day.</p>
              <p v-else-if="timeSlots.every(s => s.taken)" class="availability-warn">No open times left this day — pick another date.</p>
            </div>
          </div>

          <div class="booking-section">
            <h4 class="section-h">Notes for your RND <span class="optional">(optional)</span></h4>
            <textarea v-model="bookingNotes" data-allow-emoji rows="3" placeholder="Anything you'd like your RND to know before the session..."></textarea>
          </div>

          <p v-if="bookingError" class="form-error">{{ bookingError }}</p>

          <button class="confirm-btn" type="button" :disabled="!canConfirmBooking || isBooking" @click="confirmBooking">
            <BadgeCheck :size="15" /> {{ isBooking ? 'Booking…' : 'Confirm Booking' }}
          </button>
          <p v-if="bookingHint" class="booking-hint">{{ bookingHint }}</p>
          <p class="submit-note">Once {{ rnd.user.first_name }} confirms, you'll get an invoice — pay it before the session starts to join.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  BadgeCheck, CalendarCheck, CalendarPlus, ChevronLeft, ChevronRight, Clock, CreditCard, ExternalLink, Info, Languages,
  MapPin, MessageSquare, RotateCcw, ShieldCheck, Star, Users, Video, X,
} from 'lucide-vue-next'

const route = useRoute()
const { get, post } = useApi()

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

const isLoading = ref(true)
const isLoadingReviews = ref(true)
const isLoadingAvailability = ref(true)
const errorMessage = ref('')
const rnd = ref(null)
const reviews = ref([])
const availability = ref([])

const availabilityByDay = computed(() =>
  DAY_NAMES.map((day, dayIndex) => ({
    day,
    slots: availability.value
      .filter(s => s.day_of_week === dayIndex)
      .sort((a, b) => a.start_time.localeCompare(b.start_time)),
  }))
)

// Reference design's Weekly Availability grid runs Mon→Sun, not
// availabilityByDay's Sun-first order (DAY_NAMES/day_of_week both key off
// JS's Sunday=0 convention, which is right for the calendar grid but wrong
// for this display) — reorder without touching the underlying data shape.
const DAY_SHORT = { Sunday: 'Sun', Monday: 'Mon', Tuesday: 'Tue', Wednesday: 'Wed', Thursday: 'Thu', Friday: 'Fri', Saturday: 'Sat' }
const availabilityWeekMonFirst = computed(() => {
  const days = availabilityByDay.value
  return [...days.slice(1), days[0]].map(d => ({ ...d, short: DAY_SHORT[d.day] }))
})

// Short form for the small grid boxes, e.g. "9–5", "1:30–7" (keeps minutes).
function shortTime(t) {
  const [h, m] = t.split(':').map(Number)
  return `${h % 12 || 12}${m ? `:${String(m).padStart(2, '0')}` : ''}`
}
function compactHours(start, end) {
  return `${shortTime(start)}–${shortTime(end)}`
}
function formatFee(fee) {
  return Number(fee).toLocaleString('en-PH', { maximumFractionDigits: 2 })
}

const fullName = computed(() => (rnd.value ? `${rnd.value.user.first_name} ${rnd.value.user.last_name}` : ''))
const mapUrl = computed(() => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(rnd.value?.clinic_address || '')}`)
const CARE_STEPS = [
  { title: 'Health screening', text: 'A short form about your height, weight and health so your RND comes prepared.' },
  { title: 'First consultation', text: 'Your RND assesses your diet and health and agrees on goals with you.' },
  { title: 'Your meal plan', text: 'A weekly plan built from Filipino foods, which you can follow and log in the app.' },
  { title: 'Follow-ups', text: 'Regular check-ins to track your progress and adjust the plan.' },
]
const PH = { timeZone: 'Asia/Manila' }
function monthYear(v) {
  return v ? new Date(v).toLocaleDateString('en-PH', { ...PH, month: 'short', year: 'numeric' }) : ''
}
function slotDay(iso) {
  const day = new Date(iso).toLocaleDateString('en-CA', PH)
  if (day === new Date().toLocaleDateString('en-CA', PH)) return 'Today'
  if (day === new Date(Date.now() + 86400000).toLocaleDateString('en-CA', PH)) return 'Tomorrow'
  return new Date(iso).toLocaleDateString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric' })
}
function slotTime(iso) {
  return new Date(iso).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
}
function starText(n) {
  return '★'.repeat(n) + '☆'.repeat(5 - n)
}
function barPct(star) {
  const n = rnd.value?.rating_breakdown?.[star] || 0
  return rnd.value?.review_count ? Math.round((n / rnd.value.review_count) * 100) : 0
}

async function loadProfile() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    rnd.value = await get(`/client/rnds/${route.params.id}/`)
  } catch {
    errorMessage.value = 'Could not load this RND profile. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

async function loadReviews() {
  isLoadingReviews.value = true
  try {
    reviews.value = await get(`/client/rnds/${route.params.id}/reviews/`)
  } catch {
    reviews.value = []
  } finally {
    isLoadingReviews.value = false
  }
}

async function loadAvailability() {
  isLoadingAvailability.value = true
  try {
    availability.value = await get(`/client/rnds/${route.params.id}/availability/`)
  } catch {
    availability.value = []
  } finally {
    isLoadingAvailability.value = false
  }
}

// null until known, so the note doesn't flash for clients who have screened.
const hasScreening = ref(null)
async function loadScreeningStatus() {
  try {
    await get('/client/screening/latest/')
    hasScreening.value = true
  } catch (error) {
    hasScreening.value = (error?.response?.status ?? error?.status) === 404 ? false : null
  }
}

onMounted(async () => {
  loadReviews()
  loadAvailability()
  loadScreeningStatus()
  await loadProfile()
  // ?book=1 (e.g. the client dashboard's "Book a Consultation") opens the
  // booking modal straight away.
  if (route.query.book === '1' && offeredFormats.value.length && !rnd.value?.booking_blocked_by) openBookingModal()
})

/* ---------- BOOK APPOINTMENT MODAL ---------- */
const bookingModalOpen = ref(false)
const formats = [
  { key: 'video', label: 'Video call', short: 'Video', icon: Video, how: 'Right in your browser — no app to install. The Join button appears in My Appointments 15 minutes before the start, once you\'ve paid.' },
  { key: 'chat', label: 'Chat consultation', short: 'Chat', icon: MessageSquare, how: 'A live text session in NutriMatch Messages at your booked time.' },
  { key: 'in_person', label: 'In-person', short: 'In-person', icon: MapPin, how: 'Visit the clinic at your booked time.' },
]
// In-person needs a clinic address on file (the API refuses it otherwise).
const offeredFormats = computed(() => formats.filter(f => rnd.value?.consultation_modes?.includes(f.key)
  && (f.key !== 'in_person' || rnd.value?.clinic_address)))
const inPersonWithoutAddress = computed(() => rnd.value?.consultation_modes?.includes('in_person') && !rnd.value?.clinic_address)
const bookingType = ref('video')
const selectedDateISO = ref('')
const selectedTime = ref('')
const bookingNotes = ref('')
const isBooking = ref(false)
const bookingError = ref('')

const CAL_DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const dayHeaders = CAL_DAY_NAMES

// Local-calendar-date formatting — Date#toISOString() converts to UTC first,
// which shifts a local midnight back a day in any UTC+ timezone (e.g. PHT,
// UTC+8) and silently mis-gates "today" and every calendar cell by one day.
function toISO(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
const todayISO = toISO(new Date())

const viewMonth = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1))
const viewMonthLabel = computed(() => viewMonth.value.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }))
function shiftMonth(delta) {
  viewMonth.value = new Date(viewMonth.value.getFullYear(), viewMonth.value.getMonth() + delta, 1)
}

// Gated by the RND's real RndAvailabilitySchedule rows (already loaded via
// loadAvailability), not mock data — a day is bookable only if it has at
// least one is_available slot.
function scheduleForDate(date) {
  return availability.value.filter(s => s.day_of_week === date.getDay())
}
// A day is only highlighted if it still has at least one bookable time —
// otherwise picking it would show no times and Confirm could never enable
// (e.g. today after the RND's last slot, or hours shorter than a session).
function isDayAvailable(date) {
  const iso = toISO(date)
  if (iso < todayISO) return false
  return slotsForDate(iso).some(s => !s.taken)
}
const calendarCells = computed(() => {
  const year = viewMonth.value.getFullYear()
  const month = viewMonth.value.getMonth()
  const firstOfMonth = new Date(year, month, 1)
  const startOffset = firstOfMonth.getDay()
  const gridStart = new Date(year, month, 1 - startOffset)
  const cells = []
  for (let i = 0; i < 42; i++) {
    const d = new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + i)
    cells.push({
      day: d.getDate(),
      iso: toISO(d),
      inMonth: d.getMonth() === month,
      available: d.getMonth() === month && isDayAvailable(d),
      dayOff: d.getMonth() === month && toISO(d) >= todayISO && isDayOff(d),
    })
  }
  return cells
})

function selectDate(cell) {
  if (!cell.available) return
  selectedDateISO.value = cell.iso
  selectedTime.value = ''
}

// Bookings are 60 minutes. Start times step every hour from the RND's start
// time while a full session still fits before their end time (e.g.
// 1:30 PM–7:00 PM → 1:30, 2:30 … 5:30 PM) — same grid the server enforces
// (scheduling/serializers.py SLOT_STEP_MINUTES). Today, a time must be at
// least MIN_LEAD_MINUTES away.
const SESSION_MINUTES = 60
const SLOT_STEP_MINUTES = 60
const MIN_LEAD_MINUTES = 10
const timeSlots = computed(() => (selectedDateISO.value ? slotsForDate(selectedDateISO.value) : []))

function slotsForDate(iso) {
  const date = new Date(iso + 'T00:00:00')
  const isToday = iso === todayISO
  const now = new Date()
  const nowMinutes = now.getHours() * 60 + now.getMinutes()
  const toMinutes = (t) => { const [h, m] = t.split(':').map(Number); return h * 60 + m }
  const seen = new Set()
  const slots = []
  for (const s of scheduleForDate(date)) {
    const end = toMinutes(s.end_time)
    for (let start = toMinutes(s.start_time); start + SESSION_MINUTES <= end; start += SLOT_STEP_MINUTES) {
      if (isToday && start < nowMinutes + MIN_LEAD_MINUTES) continue
      const h = Math.floor(start / 60)
      const m = start % 60
      const value = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
      if (seen.has(value)) continue
      seen.add(value)
      // Times already booked, or blocked off by the RND, stay visible but can't be picked.
      const taken = isSlotTaken(iso, start)
      slots.push({ value, label: `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`, taken: !!taken, off: taken === 'time_off' })
    }
  }
  return slots.sort((a, b) => a.value.localeCompare(b.value))
}

const bookingHint = computed(() => {
  if (!selectedDateISO.value) return 'Pick a date to see available times.'
  if (!selectedTime.value) return 'Pick a time to continue.'
  return ''
})

const canConfirmBooking = computed(() => selectedDateISO.value !== '' && selectedTime.value !== ''
  && !timeSlots.value.find(s => s.value === selectedTime.value)?.taken)
// A time picked (e.g. from "Next available") that turns out to be booked is cleared.
watch(timeSlots, (slots) => {
  if (selectedTime.value && slots.find(s => s.value === selectedTime.value)?.taken) selectedTime.value = ''
})

// Times this RND is already booked or has blocked off (start/end/kind only), so they aren't offered.
const bookedSlots = ref([])
async function loadBookedSlots() {
  try {
    const rows = await get(`/client/rnds/${route.params.id}/booked-slots/`)
    bookedSlots.value = rows.map(r => ({ start: new Date(r.start).getTime(), end: new Date(r.end).getTime(), kind: r.kind || 'booked' }))
  } catch {
    bookedSlots.value = []
  }
}
function slotHits(iso, minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  const start = new Date(`${iso}T${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`).getTime()
  const end = start + SESSION_MINUTES * 60000
  return bookedSlots.value.filter(b => b.start < end && start < b.end)
}
// 'booked' (another booking), 'time_off' (the RND blocked it) or null (open).
function isSlotTaken(iso, minutes) {
  const hits = slotHits(iso, minutes)
  if (!hits.length) return null
  return hits.some(b => b.kind === 'booked') ? 'booked' : 'time_off'
}
// A day the RND blocked off entirely: every start time falls in their time off
// (whatever was already booked that day).
function isDayOff(d) {
  if (!bookedSlots.value.some(b => b.kind === 'time_off')) return false
  const iso = toISO(d)
  const toMinutes = (t) => { const [h, m] = t.split(':').map(Number); return h * 60 + m }
  const starts = scheduleForDate(d).flatMap(s => {
    const out = []
    for (let t = toMinutes(s.start_time); t + SESSION_MINUTES <= toMinutes(s.end_time); t += SLOT_STEP_MINUTES) out.push(t)
    return out
  })
  return starts.length > 0 && starts.every(t => slotHits(iso, t).some(b => b.kind === 'time_off'))
}

function openBookingModal(slotIso = null) {
  loadBookedSlots()
  bookingType.value = offeredFormats.value[0]?.key || 'video'
  selectedDateISO.value = ''
  selectedTime.value = ''
  bookingNotes.value = ''
  bookingError.value = ''
  viewMonth.value = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
  if (slotIso) {
    // The calendar works in the browser's local time, like the slot list.
    const d = new Date(slotIso)
    selectedDateISO.value = toISO(d)
    selectedTime.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    viewMonth.value = new Date(d.getFullYear(), d.getMonth(), 1)
  }
  bookingModalOpen.value = true
}
function bookSlot(iso) {
  openBookingModal(iso)
}
function closeBookingModal() {
  bookingModalOpen.value = false
}

async function confirmBooking() {
  if (!canConfirmBooking.value) return
  isBooking.value = true
  bookingError.value = ''
  try {
    await post('/client/appointments/', {
      rnd_id: rnd.value.user.id,
      scheduled_at: new Date(`${selectedDateISO.value}T${selectedTime.value}`).toISOString(),
      type: bookingType.value,
      duration_minutes: SESSION_MINUTES,
      notes: bookingNotes.value || undefined,
    })
    closeBookingModal()
    await navigateTo('/appointments')
  } catch (error) {
    const data = error?.data || {}
    bookingError.value = data.detail || data.non_field_errors?.[0] || data.scheduled_at?.[0] || data.type?.[0]
      || data.duration_minutes?.[0] || data.rnd_id?.[0] || 'Could not book this appointment. Please try again.'
    // The slot may have just been taken — refresh what's open.
    if (data.scheduled_at) {
      selectedTime.value = ''
      await loadBookedSlots()
    }
  } finally {
    isBooking.value = false
  }
}
</script>

<style scoped>
* { box-sizing: border-box; }

.profile-page { font-family: 'Inter', sans-serif; }
.breadcrumb { font-size: 0.8rem; color: #8a9a8a; margin: 0 0 14px; }
.breadcrumb :deep(a) { color: #1f8f5c; text-decoration: none; font-weight: 600; }

.hero {
  position: relative; overflow: hidden; display: flex; gap: 24px; align-items: center; flex-wrap: wrap;
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%); color: #fff; border-radius: 16px; padding: 28px 30px; margin-bottom: 20px;
}
.hero::after { content: ''; position: absolute; width: 260px; height: 260px; border-radius: 50%; background: rgba(255, 255, 255, 0.05); top: -100px; right: -40px; }
.hero > * { position: relative; z-index: 1; }
.hero-avatar { width: 104px; height: 104px; border-radius: 50%; object-fit: cover; border: 3px solid rgba(255, 255, 255, 0.25); flex-shrink: 0; }
.hero-avatar.initials { display: flex; align-items: center; justify-content: center; background: #D4A017; color: #1a3a1a; font-weight: 700; font-size: 1.8rem; }
.hero-main { flex: 1; min-width: 240px; }
.hero-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(0, 0, 0, 0.22); color: #D4A017; font-size: 0.72rem; font-weight: 700; padding: 5px 12px; border-radius: 20px; }
.hero-name { font-family: 'Playfair Display', serif; font-size: 1.8rem; margin: 10px 0 4px; color: #fff; }
.hero-spec { font-size: 0.88rem; color: #cfe0d5; margin: 0; }
.hero-stats { display: flex; flex-wrap: wrap; gap: 8px 18px; margin: 14px 0 0; font-size: 0.82rem; color: #e3eee7; }
.hero-stats span { display: inline-flex; align-items: center; gap: 6px; }
.hero-stats strong { color: #fff; }
.gold { color: #D4A017; fill: #D4A017; }
.hero-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; }
.hero-chip { display: inline-flex; align-items: center; gap: 5px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.16); border-radius: 14px; padding: 4px 11px; font-size: 0.74rem; }
.hero-fee { text-align: right; }
.fee-amount { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 700; margin: 0; }
.fee-unit { font-size: 0.76rem; color: #a9c0a9; margin: 2px 0 0; }

.bio-text { font-size: 0.88rem; color: #4a5a4a; line-height: 1.7; margin: 12px 0 0; white-space: pre-line; }
.steps { list-style: none; padding: 0; margin: 14px 0 0; display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.steps li { display: flex; gap: 12px; align-items: flex-start; font-size: 0.85rem; color: #1a3a1a; }
.step-num { width: 28px; height: 28px; border-radius: 50%; background: #eef3ec; color: #1e4a26; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 0.82rem; }
.step-text { display: block; color: #6a7a6a; font-size: 0.8rem; line-height: 1.5; margin-top: 2px; }
.how-row { align-items: flex-start; }
.address { display: flex; align-items: flex-start; gap: 6px; font-size: 0.82rem; color: #2a3a2a; margin: 8px 0 4px; line-height: 1.45; }
.address svg { flex-shrink: 0; margin-top: 2px; color: #1f8f5c; }
.map-link { display: inline-flex; align-items: center; gap: 4px; }
.booking-address { background: #f7f9f7; border-radius: 8px; padding: 10px 12px; margin-top: 10px; }

.avail-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 14px; }
.avail-box { background: #eef6f0; border-radius: 8px; padding: 10px 6px; text-align: center; }
.avail-box.muted { background: #f7f9f7; }
.avail-box.muted .avail-day, .avail-box.muted .avail-hours { color: #b0bab0; }
.avail-day { font-size: 0.75rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.avail-hours { font-size: 0.74rem; color: #1f6f46; margin: 3px 0 0; }

.rating-summary { display: flex; gap: 24px; align-items: center; margin: 14px 0 6px; flex-wrap: wrap; }
.rating-big { text-align: center; min-width: 110px; }
.rating-num { font-family: 'Playfair Display', serif; font-size: 2.2rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.rating-stars { color: #D4A017; letter-spacing: 1px; margin: 0; }
.rating-stars.small { font-size: 0.8rem; }
.bars { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: grid; grid-template-columns: 28px 1fr 24px; gap: 10px; align-items: center; font-size: 0.76rem; color: #6a7a6a; }
.bar { height: 8px; background: #f0f2f0; border-radius: 4px; overflow: hidden; }
.bar span { display: block; height: 100%; background: #D4A017; border-radius: 4px; }
.bar-n { text-align: right; }
.review-row { display: block; }
.review-top { display: flex; justify-content: space-between; gap: 10px; margin: 0 0 4px; }
.review-comment { font-size: 0.86rem; color: #3a4a3a; margin: 0 0 4px; line-height: 1.55; }

.side { position: sticky; top: 16px; }
.book-card { display: flex; flex-direction: column; }
.book-text { font-size: 0.84rem; color: #4a5a4a; line-height: 1.5; margin: 10px 0 12px; }
.book-links { display: flex; gap: 8px; }
.book-links > * { flex: 1; }
.divider { border-top: 1px solid #f0f2f0; margin: 18px 0 4px; }
.book-fee { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1a3a1a; margin: 6px 0 0; }
.book-fee span { font-family: 'Inter', sans-serif; font-size: 0.78rem; font-weight: 500; color: #8a9a8a; }
.slot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.slot { display: flex; flex-direction: column; align-items: flex-start; gap: 1px; border: 1px solid #d3e2d6; background: #f7fbf8; border-radius: 10px; padding: 9px 12px; cursor: pointer; font-family: inherit; text-align: left; }
.slot:hover { border-color: #1f8f5c; background: #eef6f0; }
.slot-day { font-size: 0.72rem; color: #6a7a6a; font-weight: 600; }
.slot-time { font-size: 0.88rem; color: #1a3a1a; font-weight: 700; }
.book-btn { width: 100%; margin-top: 14px; padding: 12px 16px; }
.policy { list-style: none; padding: 0; margin: 16px 0 0; display: flex; flex-direction: column; gap: 8px; }
.policy li { display: flex; gap: 8px; align-items: flex-start; font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; }
.policy svg { flex-shrink: 0; margin-top: 2px; color: #1f8f5c; }
.info-note-link { color: #2a5a8a; font-weight: 700; text-decoration: underline; white-space: nowrap; }
.info-note { display: flex; gap: 8px; align-items: flex-start; background: #eaf2fb; color: #2a5a8a; border-radius: 10px; padding: 11px 12px; font-size: 0.8rem; line-height: 1.5; margin-top: 16px; }

.loading-hero { display: flex; gap: 20px; align-items: center; background: #fff; border: 1px solid #eceeec; border-radius: 16px; padding: 28px; }
.sk { display: block; background: linear-gradient(90deg, #f0f2f0 25%, #e6eae6 50%, #f0f2f0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 6px; }
.sk-avatar { width: 96px; height: 96px; border-radius: 50%; flex-shrink: 0; }
.sk-line { height: 14px; margin: 8px 0; }
.w60 { width: 60%; } .w40 { width: 40%; }
@keyframes shimmer { to { background-position: -200% 0; } }

@media (max-width: 1100px) {
  .side { position: static; }
}
@media (max-width: 640px) {
  .hero { padding: 22px 18px; gap: 16px; }
  .hero-avatar { width: 76px; height: 76px; }
  .hero-name { font-size: 1.4rem; }
  .hero-fee { text-align: left; width: 100%; }
  .steps { grid-template-columns: 1fr; }
  .avail-grid { grid-template-columns: repeat(4, 1fr); }
}

/* BOOK APPOINTMENT MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(20,30,20,0.55); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 20px; }
.booking-modal-box { position: relative; background: #fff; border-radius: 18px; width: 100%; max-width: 640px; max-height: 92vh; overflow-y: auto; }
.booking-close {
  position: sticky; top: 14px; float: right; margin-right: 14px; z-index: 5; background: #fff; border: 1px solid #eceeec;
  border-radius: 50%; width: 32px; height: 32px;
}
.modal-close-btn { border: none; background: none; color: #6a7a6a; cursor: pointer; display: flex; align-items: center; justify-content: center; }

.booking-left { padding: 30px 32px 34px; }
.booking-title { font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: 700; color: #1a3a1a; margin: 0 0 8px; }
.booking-title em { color: #D4A017; font-style: italic; }
.booking-sub { font-size: 0.87rem; color: #6a7a6a; line-height: 1.55; margin: 0 0 22px; }

.booking-section { margin-bottom: 24px; }
.section-h { font-family: 'Playfair Display', serif; font-size: 0.98rem; color: #1a3a1a; margin: 0 0 4px; }
.section-h .optional { font-family: 'Inter', sans-serif; font-weight: 400; color: #9aaa9a; font-size: 0.82rem; }
.section-sub { font-size: 0.8rem; color: #9aaa9a; margin: 0 0 14px; }

.format-row { display: flex; gap: 10px; flex-wrap: wrap; }
.format-card {
  flex: 1; min-width: 110px; display: flex; flex-direction: column; align-items: center; gap: 6px;
  border: 1.5px solid #d5dad5; background: #fff; border-radius: 12px; padding: 14px 10px; cursor: pointer;
  color: #4a5a4a;
}
.format-card.active { border-color: #1f8f5c; background: #f0f9f4; color: #1a3a1a; }
.format-name { font-size: 0.82rem; font-weight: 700; }

.calendar-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.calendar-month { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.calendar-nav { display: flex; gap: 5px; }
.calendar-nav button { width: 26px; height: 26px; border-radius: 6px; border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }
.calendar-day-header { text-align: center; font-size: 0.68rem; font-weight: 700; color: #9aaa9a; padding-bottom: 4px; }
.calendar-cell {
  aspect-ratio: 1.6 / 1; border: none; border-radius: 7px; background: transparent; color: #c5cdc5; font-size: 0.8rem; cursor: default;
}
.calendar-cell.out-month { visibility: hidden; }
.calendar-cell.available { background: #d9ecdf; color: #1a3a1a; cursor: pointer; font-weight: 600; }
.calendar-cell.available:hover { background: #c3e0cc; }
.calendar-cell.selected { background: #14301a; color: #fff; }
.calendar-cell.disabled:not(.out-month) { color: #d5dad5; }
.calendar-cell.day-off { background: repeating-linear-gradient(135deg, #f1f3f1, #f1f3f1 4px, #e6e9e6 4px, #e6e9e6 8px); color: #9aaa9a; text-decoration: line-through; }
.day-off-key { display: flex; align-items: center; gap: 8px; font-size: 0.76rem; color: #6a7a6a; margin: 8px 0 0; }
.day-off-swatch { width: 14px; height: 14px; border-radius: 4px; flex-shrink: 0; background: repeating-linear-gradient(135deg, #f1f3f1, #f1f3f1 3px, #e6e9e6 3px, #e6e9e6 6px); border: 1px solid #dde3dd; }

.time-slot-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
.time-slot-btn { border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 8px; padding: 10px 16px; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
.time-slot-btn.selected { background: #14301a; border-color: #14301a; color: #fff; }
.one-rnd { background: #fff8e8; border: 1px solid #f1dca3; border-radius: 10px; padding: 12px 14px; margin-top: 14px; font-size: 0.84rem; color: #5a4a1a; line-height: 1.5; }
.one-rnd p { margin: 0 0 6px; }
.time-slot-btn.taken { background: #f3f4f3; border-style: dashed; color: #9aaa9a; text-decoration: line-through; cursor: not-allowed; display: inline-flex; align-items: center; gap: 6px; }
.taken-tag { font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; text-decoration: none; display: inline-block; background: #e6e9e6; color: #6a7a6a; border-radius: 6px; padding: 1px 5px; }
.availability-warn { font-size: 0.8rem; color: #c0392b; background: #fbe5e2; border-radius: 8px; padding: 10px 12px; margin: 4px 0 0; width: 100%; }

.booking-section textarea {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 13px; font-size: 0.85rem; font-family: inherit; color: #2a2a2a; resize: vertical;
}

.confirm-btn {
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; background: #14301a; color: #fff;
  border: none; border-radius: 10px; padding: 14px; font-weight: 700; font-size: 0.9rem; cursor: pointer; margin-top: 6px;
}
.confirm-btn:hover:not(:disabled) { background: #1c421f; }
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.booking-hint { text-align: center; font-size: 0.8rem; font-weight: 600; color: #b8860b; margin: 10px 0 0; }
.submit-note { text-align: center; font-size: 0.76rem; color: #9aaa9a; margin: 10px 0 0; }
</style>
