<template>
  <div class="profile-page nm-page">
    <p v-if="errorMessage" class="nm-error">{{ errorMessage }}</p>

    <div v-if="isLoading" class="loading-hero"><span class="sk sk-avatar" /><span style="flex: 1"><span class="sk sk-line w40" /><span class="sk sk-line w60" /></span></div>

    <template v-else-if="rnd">
      <p class="breadcrumb"><NuxtLink to="/find-rnd">Find an RND</NuxtLink> / {{ fullName }}</p>

      <!-- hero: who they are and what it costs on top, the four figures in one divided strip below -->
      <section class="hero">
        <div class="hero-top">
          <img v-if="rnd.user.profile_photo" :src="rnd.user.profile_photo" class="hero-avatar" alt="" />
          <span v-else class="hero-avatar initials">{{ userInitials(rnd.user.first_name, rnd.user.last_name) }}</span>
          <div class="hero-main">
            <h1 class="hero-name">
              {{ fullName }}
              <span class="verified" :title="verifiedTitle" tabindex="0" :aria-label="verifiedTitle"><BadgeCheck :size="20" aria-hidden="true" /></span>
            </h1>
            <p class="hero-spec">{{ rnd.specialization || 'General and clinical nutrition' }}</p>
            <p v-if="rnd.languages?.length" class="hero-line" :title="languageNames.join(', ')"><Languages :size="14" aria-hidden="true" /> {{ languagesText }}</p>
            <p v-if="offeredFormats.length" class="hero-line"><component :is="offeredFormats[0].icon" :size="14" aria-hidden="true" /> {{ formatsText }}</p>
          </div>
          <div class="hero-fee">
            <p class="fee-amount">₱{{ formatFee(rnd.consultation_fee) }}</p>
            <p class="fee-unit">per {{ SESSION_MINUTES }}-minute session</p>
            <button v-if="!rnd.booking_blocked_by && offeredFormats.length && rnd.next_open_slots.length" type="button" class="hero-book" @click="openBookingModal()">
              <CalendarPlus :size="15" aria-hidden="true" /> Book
            </button>
          </div>
        </div>
        <dl class="hero-figs">
          <div class="hfig">
            <dt>{{ rnd.review_count ? `${rnd.review_count} review${rnd.review_count === 1 ? '' : 's'}` : 'No reviews yet' }}</dt>
            <dd><Star v-if="rnd.review_count" :size="16" class="gold" aria-hidden="true" />{{ rnd.review_count ? rnd.average_rating.toFixed(1) : '—' }}</dd>
          </div>
          <div class="hfig">
            <dt>consultation{{ rnd.consultations_completed === 1 ? '' : 's' }} done</dt>
            <dd>{{ rnd.consultations_completed }}</dd>
          </div>
          <div class="hfig">
            <dt>active patient{{ rnd.active_patients === 1 ? '' : 's' }}</dt>
            <dd>{{ rnd.active_patients }}</dd>
          </div>
          <div class="hfig">
            <dt>on NutriMatch since</dt>
            <dd>{{ monthYear(rnd.member_since) }}</dd>
          </div>
        </dl>
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
            <h2 class="nm-panel-title">Where and how you'll meet</h2>
            <div v-for="f in offeredFormats" :key="f.key" class="nm-row how-row">
              <span class="nm-stat-icon" style="margin: 0"><component :is="f.icon" :size="16" /></span>
              <div class="nm-row-main">
                <p class="nm-row-title">{{ f.label }}</p>
                <p class="nm-row-sub">{{ f.how }}</p>
                <template v-if="f.key === 'in_person'">
                  <p class="address"><MapPin :size="13" /> {{ rnd.clinic_address }}</p>
                  <a :href="mapUrl" target="_blank" rel="noopener" class="nm-btn-soft nm-btn-sm map-link">Open in Google Maps <ExternalLink :size="12" aria-hidden="true" /></a>
                </template>
              </div>
            </div>
            <p v-if="inPersonWithoutAddress" class="nm-note plain-note" style="margin: 12px 0 0">
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
            <p v-else class="nm-muted" style="margin-top: 12px">No reviews yet. You could be one of {{ rnd.user.first_name }}'s first patients.</p>
          </div>
        </div>

        <!-- booking card -->
        <div class="nm-col side">
          <div class="nm-panel book-card">
            <template v-if="rnd.is_my_rnd">
              <span class="nm-pill green">Your RND</span>
              <p class="book-text">You're already seeing {{ rnd.user.first_name }}. Your appointments and messages are in one place.</p>
              <div class="book-links">
                <NuxtLink to="/appointments" class="nm-btn-soft">My appointments</NuxtLink>
                <NuxtLink to="/messages" class="nm-btn-soft">Messages</NuxtLink>
              </div>
              <div class="divider" />
            </template>

            <p class="book-fee">₱{{ formatFee(rnd.consultation_fee) }} <span>/ {{ SESSION_MINUTES }}-min session</span></p>
            <!-- One RND at a time: booking someone else waits until the current RND discharges them. -->
            <div v-if="rnd.booking_blocked_by" class="one-rnd">
              <p v-if="rnd.booking_blocked_by.status === 'active'">
                You're under <strong>RND {{ rnd.booking_blocked_by.name }}</strong>'s care. You can book a different RND once RND {{ rnd.booking_blocked_by.name }} discharges you. To switch, ask to end your care in Profile Settings, Care team.
              </p>
              <p v-else>
                You have a booking waiting for <strong>RND {{ rnd.booking_blocked_by.name }}</strong>. Cancel it first if you'd like a different RND.
              </p>
              <NuxtLink :to="`/rnd-profile-view/${rnd.booking_blocked_by.rnd_id}`" class="nm-btn-soft nm-btn-sm">Go to RND {{ rnd.booking_blocked_by.name }}</NuxtLink>
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
              <CalendarPlus :size="15" aria-hidden="true" /> {{ rnd.next_open_slots.length ? 'See all times and book' : 'No times available' }}
            </button>
            </template>

            <ul class="policy">
              <li><Clock :size="13" aria-hidden="true" /> Your booking is a request until {{ rnd.user.first_name }} confirms it.</li>
              <li><CreditCard :size="13" aria-hidden="true" /> Pay after {{ rnd.user.first_name }} confirms, before the session starts.</li>
              <li><RotateCcw :size="13" aria-hidden="true" /> Cancel before it starts and a paid session is refunded.</li>
            </ul>

            <!-- Only for clients who haven't screened yet — the RND can't
                 confirm a first appointment without it. -->
            <div v-if="hasScreening === false" class="info-note">
              <p>Complete your health screening first. Your RND needs it before they can confirm your first consultation.</p>
              <NuxtLink to="/pre-consultation-screening" class="nm-btn-dark nm-btn-sm">Start screening</NuxtLink>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- BOOK APPOINTMENT MODAL: header, a scrolling body (format, open days,
         times, notes) and a footer that always shows what's picked + Send. -->
    <div v-if="bookingModalOpen" class="modal-overlay" @click.self="closeBookingModal">
      <div class="booking-modal-box" role="dialog" aria-modal="true" aria-labelledby="bk-title">
        <header class="bk-head">
          <div class="bk-head-text">
            <h2 id="bk-title" class="booking-title">Book a consultation with {{ rnd.user.first_name }}</h2>
            <p class="booking-sub">{{ rnd.user.first_name }} confirms your request, then you pay before it starts. Times are Philippine time.</p>
          </div>
          <button class="bk-x" type="button" aria-label="Close" @click="closeBookingModal"><X :size="18" /></button>
        </header>

        <div class="bk-body">
          <div class="bk-format">
            <div class="seg" role="radiogroup" aria-label="Format">
              <button
                v-for="f in offeredFormats" :key="f.key"
                type="button" role="radio" :aria-checked="bookingType === f.key"
                class="seg-btn" :class="{ active: bookingType === f.key }"
                @click="bookingType = f.key"
              ><component :is="f.icon" :size="15" aria-hidden="true" /> {{ f.label }}</button>
            </div>
            <p class="bk-fee"><strong>₱{{ formatFee(rnd.consultation_fee) }}</strong>, {{ SESSION_MINUTES }} minutes</p>
          </div>
          <p v-if="bookingType === 'in_person'" class="address booking-address"><MapPin :size="13" aria-hidden="true" /> {{ rnd.clinic_address }}</p>

          <section class="bk-section" aria-labelledby="bk-day-h">
            <div class="bk-row-head">
              <h3 id="bk-day-h" class="section-h">{{ viewMonthLabel }}</h3>
              <div class="strip-nav">
                <button type="button" aria-label="Previous month" :disabled="!canGoBack" @click="shiftMonth(-1)"><ChevronLeft :size="15" /></button>
                <button type="button" aria-label="Next month" @click="shiftMonth(1)"><ChevronRight :size="15" /></button>
              </div>
            </div>
            <div class="cal">
              <span v-for="d in dayHeaders" :key="d" class="cal-wd" aria-hidden="true">{{ d }}</span>
              <template v-for="cell in calendarCells" :key="cell.iso">
                <span v-if="!cell.inMonth" class="cal-cell out" aria-hidden="true" />
                <button
                  v-else type="button" class="cal-cell"
                  :class="{ open: cell.open, selected: cell.iso === selectedDateISO, today: cell.iso === todayISO, off: cell.dayOff, full: cell.full }"
                  :disabled="!cell.open" :aria-pressed="cell.iso === selectedDateISO" :aria-label="cell.aria"
                  @click="pickDay(cell.iso)"
                >
                  <span class="cal-num">{{ cell.day }}</span>
                  <span v-if="cell.open" class="cal-note">{{ cell.open }} open</span>
                  <span v-else-if="cell.dayOff" class="cal-note">Day off</span>
                  <span v-else-if="cell.full" class="cal-note">Full</span>
                </button>
              </template>
            </div>
            <p v-if="!calendarCells.some(c => c.open)" class="nm-note plain-note cal-empty">No open times in {{ viewMonthLabel }}. Try the next month.</p>
          </section>

          <section v-if="selectedDateISO" class="bk-section" aria-labelledby="bk-time-h">
            <h3 id="bk-time-h" class="section-h">{{ selectedDayLabel }}</h3>
            <div v-for="g in timeGroups" :key="g.label" class="tg">
              <span class="tg-label">{{ g.label }}</span>
              <div class="tg-times">
                <template v-for="item in g.items" :key="item.value">
                  <span v-if="item.away" class="t-away">Away {{ item.label }}</span>
                  <span v-else-if="item.taken" class="t-booked" title="Already booked by another client">{{ item.label }}, booked</span>
                  <button
                    v-else type="button" class="t-btn" :class="{ selected: selectedTime === item.value }"
                    :aria-pressed="selectedTime === item.value" @click="selectedTime = item.value"
                  >{{ item.label }}</button>
                </template>
              </div>
            </div>
          </section>

          <section class="bk-section">
            <label for="bk-notes" class="section-h">Notes for your RND <span class="optional">(optional)</span></label>
            <textarea id="bk-notes" v-model="bookingNotes" data-allow-emoji rows="2" placeholder="Anything you'd like your RND to know before the session"></textarea>
          </section>
        </div>

        <footer class="bk-foot">
          <div class="bk-summary" aria-live="polite">
            <p v-if="bookingSummary" class="bk-pick">{{ bookingSummary }}</p>
            <p v-else class="bk-pick muted">{{ bookingHint }}</p>
            <p v-if="bookingError" class="form-error" role="alert">{{ bookingError }}</p>
            <p v-else class="bk-after">You get an invoice once {{ rnd.user.first_name }} confirms.</p>
          </div>
          <button class="nm-btn-dark bk-send" type="button" :disabled="!canConfirmBooking || isBooking" @click="confirmBooking">
            {{ isBooking ? 'Sending…' : 'Send booking request' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  BadgeCheck, CalendarPlus, ChevronLeft, ChevronRight, Clock, CreditCard, ExternalLink, Languages,
  MapPin, RotateCcw, Star, Video, X,
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
// Hero sentences: languages ("Speaks English, Filipino, Bisaya and 3 more"),
// formats + city ("Video call or in person, Davao City"), PRC details on the check.
const languageNames = computed(() => (rnd.value?.languages || []).map(l => l.language_name.replace(/ \(.*\)/, '')))
const languagesText = computed(() => {
  const n = languageNames.value
  if (n.length <= 3) return `Speaks ${n.length > 1 ? `${n.slice(0, -1).join(', ')} and ${n.at(-1)}` : n[0]}`
  return `Speaks ${n.slice(0, 3).join(', ')} and ${n.length - 3} more`
})
const formatsText = computed(() => {
  const labels = offeredFormats.value.map((f, i) => (i ? f.label.toLowerCase() : f.label))
  const city = offeredFormats.value.some(f => f.key === 'in_person') ? (rnd.value?.clinic_address || '').split(',').pop().trim() : ''
  return `${labels.join(' or ')}${city ? `, ${city}` : ''}`
})
const verifiedTitle = computed(() => {
  const r = rnd.value
  if (!r) return ''
  return `PRC verified${r.verified_at ? ` since ${monthYear(r.verified_at)}` : ''}${r.prc_license_number ? `, license no. ${r.prc_license_number}` : ''}`
})
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
  { key: 'video', label: 'Video call', short: 'Video call', icon: Video, how: 'Right in your browser, no app to install. The Join button appears in My Appointments 15 minutes before the start, once you\'ve paid.' },
  { key: 'in_person', label: 'In person', short: 'In person', icon: MapPin, how: 'Visit the clinic at your booked time.' },
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

// Local-calendar-date formatting — Date#toISOString() converts to UTC first,
// which shifts a local midnight back a day in any UTC+ timezone (e.g. PHT,
// UTC+8) and silently mis-gates "today" by one day.
function toISO(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
const todayISO = toISO(new Date())

// Gated by the RND's real RndAvailabilitySchedule rows (already loaded via
// loadAvailability), not mock data — a day is bookable only if it has at
// least one is_available slot.
function scheduleForDate(date) {
  return availability.value.filter(s => s.day_of_week === date.getDay())
}
// A day is only highlighted if it still has at least one bookable time —
// otherwise picking it would show no times and Confirm could never enable
// (e.g. today after the RND's last slot, or hours shorter than a session).
// The month calendar. A day is green with its count while it still has an open
// time; past days and days without hours are faint; a day the RND blocked off
// is striped "Day off", a day with every time taken says "Full".
const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const viewMonth = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1))
const viewMonthLabel = computed(() => viewMonth.value.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }))
const canGoBack = computed(() => {
  const now = new Date()
  return viewMonth.value > new Date(now.getFullYear(), now.getMonth(), 1)
})
function shiftMonth(delta) {
  viewMonth.value = new Date(viewMonth.value.getFullYear(), viewMonth.value.getMonth() + delta, 1)
}
const calendarCells = computed(() => {
  const year = viewMonth.value.getFullYear()
  const month = viewMonth.value.getMonth()
  const gridStart = new Date(year, month, 1 - new Date(year, month, 1).getDay())
  const weeks = Math.ceil((new Date(year, month, 1).getDay() + new Date(year, month + 1, 0).getDate()) / 7)
  const cells = []
  for (let i = 0; i < weeks * 7; i++) {
    const d = new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + i)
    const iso = toISO(d)
    const inMonth = d.getMonth() === month
    const future = iso >= todayISO
    const slots = inMonth && future ? slotsForDate(iso) : []
    const open = slots.filter(t => !t.taken).length
    const dayOff = !open && slots.length > 0 && slots.every(t => t.off)
    const full = !open && !dayOff && slots.length > 0
    const long = d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
    cells.push({
      iso, inMonth, open, dayOff, full, day: d.getDate(),
      aria: open ? `${long}, ${open} open` : dayOff ? `${long}, day off` : full ? `${long}, fully booked` : long,
    })
  }
  return cells
})
function pickDay(iso) {
  if (iso === selectedDateISO.value) return
  selectedDateISO.value = iso
  selectedTime.value = ''
}
// The first day with an open time, looking up to 60 days ahead.
function firstOpenDay() {
  const now = new Date()
  for (let i = 0; i < 60; i++) {
    const iso = toISO(new Date(now.getFullYear(), now.getMonth(), now.getDate() + i))
    if (slotsForDate(iso).some(t => !t.taken)) return iso
  }
  return ''
}
const selectedDayLabel = computed(() => (selectedDateISO.value
  ? new Date(selectedDateISO.value + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
  : ''))
// Times split into morning / afternoon / evening. Booked times stay visible
// (greyed); a run of blocked-off hours shows as one "Away 9:00 AM to 12:00 PM".
const timeGroups = computed(() => {
  const groups = [
    { label: 'Morning', test: h => h < 12, items: [] },
    { label: 'Afternoon', test: h => h >= 12 && h < 17, items: [] },
    { label: 'Evening', test: h => h >= 17, items: [] },
  ]
  // A run of blocked hours stays one item, filed under the part of day it starts in.
  let run = null
  for (const slot of timeSlots.value) {
    if (slot.off) {
      const endLabel = clockLabel(minutesOf(slot.value) + SESSION_MINUTES)
      if (run) { run.label = `${run.from} to ${endLabel}`; continue }
      run = { value: slot.value, away: true, from: slot.label, label: `${slot.label} to ${endLabel}` }
      groups.find(g => g.test(Number(slot.value.slice(0, 2)))).items.push(run)
    } else {
      run = null
      groups.find(g => g.test(Number(slot.value.slice(0, 2)))).items.push(slot)
    }
  }
  return groups.filter(g => g.items.length)
})
function minutesOf(t) { const [h, m] = t.split(':').map(Number); return h * 60 + m }
function clockLabel(min) {
  const h = Math.floor(min / 60) % 24
  const m = min % 60
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}
const bookingSummary = computed(() => {
  if (!selectedDateISO.value || !selectedTime.value) return ''
  const fmt = offeredFormats.value.find(f => f.key === bookingType.value)?.label || ''
  const day = new Date(selectedDateISO.value + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  return `${fmt}, ${day}, ${clockLabel(minutesOf(selectedTime.value))}`
})

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
  if (!selectedDateISO.value) return 'Pick a green day to see the open times.'
  if (!selectedTime.value) return 'Pick a time.'
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
async function openBookingModal(slotIso = null) {
  bookingType.value = offeredFormats.value[0]?.key || 'video'
  selectedDateISO.value = ''
  selectedTime.value = ''
  bookingNotes.value = ''
  bookingError.value = ''
  if (slotIso) {
    // The strip works in the browser's local time, like the slot list.
    const d = new Date(slotIso)
    selectedDateISO.value = toISO(d)
    selectedTime.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }
  bookingModalOpen.value = true
  await loadBookedSlots()
  // Nothing picked yet (or that day is now full): start on the first open day.
  if (!selectedDateISO.value || !slotsForDate(selectedDateISO.value).some(t => !t.taken)) {
    selectedDateISO.value = firstOpenDay()
    selectedTime.value = ''
  }
  const shown = selectedDateISO.value ? new Date(selectedDateISO.value + 'T00:00:00') : new Date()
  viewMonth.value = new Date(shown.getFullYear(), shown.getMonth(), 1)
}
function bookSlot(iso) {
  openBookingModal(iso)
}
function closeBookingModal() {
  bookingModalOpen.value = false
}
function onBookingKey(e) { if (e.key === 'Escape' && bookingModalOpen.value) closeBookingModal() }
onMounted(() => window.addEventListener('keydown', onBookingKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onBookingKey))

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
.breadcrumb { font-size: 0.82rem; color: #6a7a6a; margin: 0 0 14px; }
.breadcrumb :deep(a) { color: #0a4a37; text-decoration: none; font-weight: 600; }
.breadcrumb :deep(a:hover) { text-decoration: underline; }
.profile-page .nm-panel { border-color: #d9e3dc; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }

.hero {
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%); color: #fff; border-radius: 16px; margin-bottom: 20px; overflow: hidden;
  box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
}
.hero-top { display: flex; gap: 22px; align-items: center; padding: 26px 28px 22px; }
.hero-avatar { width: 96px; height: 96px; border-radius: 50%; object-fit: cover; border: 3px solid rgba(255, 255, 255, 0.25); flex-shrink: 0; }
.hero-avatar.initials { display: flex; align-items: center; justify-content: center; background: #D4A017; color: #1a3a1a; font-weight: 700; font-size: 1.7rem; }
.hero-main { flex: 1; min-width: 0; }
.hero-name { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; font-family: 'Playfair Display', serif; font-size: 1.8rem; line-height: 1.15; margin: 0 0 4px; color: #fff; }
.verified { display: inline-flex; color: #7fd7a8; cursor: help; border-radius: 50%; }
.verified:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
.hero-spec { font-size: 0.92rem; color: #e3eee7; margin: 0 0 10px; }
.hero-line { display: flex; align-items: center; gap: 7px; font-size: 0.86rem; color: #cfe0d5; margin: 4px 0 0; }
.hero-line svg { flex-shrink: 0; color: #9fd0b4; }
.gold { color: #D4A017; fill: #D4A017; }
.hero-fee { text-align: right; flex-shrink: 0; }
.fee-amount { font-family: 'Playfair Display', serif; font-size: 1.9rem; font-weight: 700; margin: 0; line-height: 1; }
.fee-unit { font-size: 0.78rem; color: #cfe0d5; margin: 4px 0 10px; }
.hero-book {
  display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-height: 40px; padding: 0 22px; border-radius: 10px;
  background: #f2b61f; border: none; color: #0a4a37; font-family: inherit; font-size: 0.88rem; font-weight: 700; cursor: pointer;
}
.hero-book:hover { background: #e0a410; }
.hero-book:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
/* the four figures: one divided strip along the bottom of the banner */
.hero-figs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 0; border-top: 1px solid rgba(255, 255, 255, 0.16); background: rgba(0, 0, 0, 0.12); }
.hfig { display: flex; flex-direction: column-reverse; padding: 12px 20px; border-left: 1px solid rgba(255, 255, 255, 0.16); min-width: 0; }
.hfig:first-child { border-left: none; }
.hfig dd { display: flex; align-items: center; gap: 5px; margin: 0; font-family: 'Playfair Display', serif; font-size: 1.35rem; font-weight: 700; color: #fff; font-variant-numeric: lining-nums; }
.hfig dt { font-size: 0.78rem; color: #cfe0d5; }

.bio-text { font-size: 0.88rem; color: #4a5a4a; line-height: 1.7; margin: 12px 0 0; white-space: pre-line; }
.steps { list-style: none; padding: 0; margin: 14px 0 0; display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.steps li { display: flex; gap: 12px; align-items: flex-start; font-size: 0.85rem; color: #1a3a1a; }
.step-num { width: 28px; height: 28px; border-radius: 50%; background: #e3efe7; color: #1e4a26; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; font-size: 0.82rem; }
.step-text { display: block; color: #6a7a6a; font-size: 0.8rem; line-height: 1.5; margin-top: 2px; }
.how-row { align-items: flex-start; }
.address { display: flex; align-items: flex-start; gap: 6px; font-size: 0.82rem; color: #2a3a2a; margin: 8px 0 4px; line-height: 1.45; }
.address svg { flex-shrink: 0; margin-top: 2px; color: #1f8f5c; }
.map-link { display: inline-flex; align-items: center; gap: 4px; }
.booking-address { background: #f2f6f3; border: 1px solid #d9e3dc; border-radius: 8px; padding: 10px 12px; margin-top: 10px; }

.avail-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 14px; }
.avail-box { background: #e3efe7; border-radius: 8px; padding: 10px 6px; text-align: center; }
.avail-box.muted { background: #f4f6f4; }
.avail-box.muted .avail-day, .avail-box.muted .avail-hours { color: #8a9a8a; }
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
.divider { border-top: 1px solid #d9e3dc; margin: 18px 0 4px; }
.book-fee { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1a3a1a; margin: 6px 0 0; }
.book-fee span { font-family: 'Inter', sans-serif; font-size: 0.8rem; font-weight: 500; color: #6a7a6a; }
.slot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.slot { display: flex; flex-direction: column; align-items: flex-start; gap: 1px; border: 1px solid #d9e3dc; background: #f7faf8; border-radius: 10px; padding: 9px 12px; cursor: pointer; font-family: inherit; text-align: left; }
.slot:hover { border-color: #1f8f5c; background: #e3efe7; }
.slot:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.slot-day { font-size: 0.72rem; color: #6a7a6a; font-weight: 600; }
.slot-time { font-size: 0.88rem; color: #1a3a1a; font-weight: 700; }
.book-btn { width: 100%; margin-top: 14px; }
.policy { list-style: none; padding: 0; margin: 16px 0 0; display: flex; flex-direction: column; gap: 8px; }
.policy li { display: flex; gap: 8px; align-items: flex-start; font-size: 0.8rem; color: #4a5a4a; line-height: 1.45; }
.policy svg { flex-shrink: 0; margin-top: 2px; color: #1f8f5c; }
/* screening still to do: dashed green */
.info-note { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; background: #fff; border: 1.5px dashed #3f9a6b; color: #1f4a30; border-radius: 10px; padding: 11px 12px; font-size: 0.82rem; line-height: 1.5; margin-top: 16px; }
.info-note p { margin: 0; }

.loading-hero { display: flex; gap: 20px; align-items: center; background: #fff; border: 1px solid #d9e3dc; border-radius: 16px; padding: 28px; }
.sk { display: block; background: linear-gradient(90deg, #f0f2f0 25%, #e6eae6 50%, #f0f2f0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 6px; }
.sk-avatar { width: 96px; height: 96px; border-radius: 50%; flex-shrink: 0; }
.sk-line { height: 14px; margin: 8px 0; }
.w60 { width: 60%; } .w40 { width: 40%; }
@keyframes shimmer { to { background-position: -200% 0; } }

@media (max-width: 1100px) {
  .side { position: static; }
}
@media (max-width: 640px) {
  .hero-top { flex-wrap: wrap; padding: 20px 18px 18px; gap: 14px; }
  .hero-avatar { width: 72px; height: 72px; }
  .hero-name { font-size: 1.4rem; }
  .hero-main { flex-basis: calc(100% - 90px); }
  .hero-fee { width: 100%; text-align: left; display: flex; align-items: center; gap: 4px 12px; flex-wrap: wrap; }
  .fee-unit { margin: 0; flex: 1; }
  .hero-book { width: 100%; }
  .hero-figs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hfig:nth-child(3) { border-left: none; }
  .hfig:nth-child(n+3) { border-top: 1px solid rgba(255, 255, 255, 0.16); }
  .hfig { padding: 10px 16px; }
  .steps { grid-template-columns: 1fr; }
  .avail-grid { grid-template-columns: repeat(4, 1fr); }
}

/* BOOK APPOINTMENT MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(20,30,20,0.55); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 20px; }
.booking-modal-box {
  position: relative; background: #fff; border-radius: 18px; width: 100%; max-width: 620px; max-height: 92vh; max-height: 92dvh;
  display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
}
.bk-head { display: flex; align-items: flex-start; gap: 12px; padding: 24px 26px 16px; border-bottom: 1px solid #d9e3dc; }
.bk-head-text { flex: 1; min-width: 0; }
.booking-title { font-family: 'Playfair Display', serif; font-size: 1.35rem; font-weight: 700; color: #1a3a1a; margin: 0 0 6px; line-height: 1.2; }
.booking-sub { font-size: 0.85rem; color: #4a5a4a; line-height: 1.5; margin: 0; }
.bk-x { border: none; background: #e3efe7; color: #0a4a37; cursor: pointer; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.bk-x:hover { background: #d3e6d9; }
.bk-x:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.bk-body { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 18px 26px 6px; }
.bk-section { margin-bottom: 22px; }
.section-h { display: block; font-family: 'Playfair Display', serif; font-size: 1rem; font-weight: 700; color: #1a3a1a; margin: 0 0 10px; }
.section-h .optional { font-family: 'Inter', sans-serif; font-weight: 400; color: #6a7a6a; font-size: 0.82rem; }

/* format: a two-option switch, the fee beside it */
.bk-format { display: flex; align-items: center; justify-content: space-between; gap: 10px 16px; flex-wrap: wrap; margin-bottom: 20px; }
.seg { display: inline-flex; background: #eef4f0; border: 1px solid #d9e3dc; border-radius: 10px; padding: 3px; gap: 3px; }
.seg-btn {
  display: inline-flex; align-items: center; gap: 7px; min-height: 34px; padding: 0 16px; border: none; border-radius: 8px; background: transparent;
  color: #4a5a4a; font-family: inherit; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.seg-btn:hover:not(.active) { color: #0a4a37; }
.seg-btn.active { background: #0a4a37; color: #fff; }
.seg-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.bk-fee { margin: 0; font-size: 0.86rem; color: #4a5a4a; }
.bk-fee strong { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin-right: 1px; }
.booking-address { margin: -10px 0 20px; }

/* the open-day strip */
.bk-row-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.bk-row-head .section-h { margin: 0 0 10px; }
.strip-nav { display: flex; gap: 5px; margin-bottom: 10px; }
.strip-nav button { width: 30px; height: 30px; border-radius: 8px; border: none; background: #e3efe7; color: #0a4a37; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.strip-nav button:hover { background: #d3e6d9; }
.strip-nav button:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.strip-nav button:disabled { opacity: 0.4; cursor: default; }
.cal { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 5px; }
.cal-wd { text-align: center; font-size: 0.76rem; font-weight: 600; color: #6a7a6a; padding-bottom: 2px; }
.cal-cell {
  min-height: 52px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
  border: 1px solid transparent; border-radius: 9px; background: transparent; color: #b5bfb5; font-family: inherit; padding: 4px 2px;
}
.cal-cell.out { border: none; }
.cal-num { font-size: 0.9rem; font-weight: 600; font-variant-numeric: lining-nums tabular-nums; }
.cal-note { font-size: 0.66rem; font-weight: 600; white-space: nowrap; }
.cal-cell.today .cal-num { text-decoration: underline; text-underline-offset: 3px; }
.cal-cell.open { background: #e3efe7; border-color: #cfe3d6; color: #1a3a1a; cursor: pointer; }
.cal-cell.open .cal-note { color: #1f6f46; }
.cal-cell.open:hover:not(.selected) { background: #d3e6d9; border-color: #3f9a6b; }
.cal-cell.selected { background: #0a4a37; border-color: #0a4a37; color: #fff; }
.cal-cell.selected .cal-note { color: #9fd0b4; }
.cal-cell:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.cal-cell.off { background: repeating-linear-gradient(135deg, #f3f5f3, #f3f5f3 4px, #e8ebe8 4px, #e8ebe8 8px); color: #8a9a8a; }
.cal-cell.full { background: #f3f5f3; color: #8a9a8a; }
.cal-empty { margin: 10px 0 0; }

/* times grouped by part of the day */
.tg { display: grid; grid-template-columns: 84px 1fr; gap: 8px 12px; align-items: start; padding: 10px 0; border-top: 1px solid #d9e3dc; }
.tg:first-of-type { border-top: none; padding-top: 0; }
.tg-label { font-size: 0.82rem; font-weight: 600; color: #4a5a4a; padding-top: 9px; }
.tg-times { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.t-btn {
  min-height: 36px; padding: 0 16px; border-radius: 8px; border: 1px solid #b9d4c2; background: #fff; color: #1a3a1a;
  font-family: inherit; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-variant-numeric: tabular-nums;
}
.t-btn:hover:not(.selected) { border-color: #3f9a6b; background: #f2f7f3; }
.t-btn.selected { background: #0a4a37; border-color: #0a4a37; color: #fff; }
.t-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.t-booked, .t-away { display: inline-flex; align-items: center; min-height: 36px; padding: 0 12px; border-radius: 8px; background: #f2f4f2; color: #8a9a8a; font-size: 0.82rem; }
.t-booked { text-decoration: line-through; text-decoration-color: #b5bfb5; }

.bk-section textarea {
  width: 100%; border: 1px solid #d9e3dc; border-radius: 8px; padding: 10px 13px; font-size: 0.85rem; font-family: inherit; color: #1a3a1a; resize: vertical;
}
.bk-section textarea:focus { outline: none; border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.15); }

/* the footer: what's picked, and Send */
.bk-foot { display: flex; align-items: center; gap: 12px 18px; padding: 14px 26px; border-top: 1px solid #d9e3dc; background: #f7faf8; }
.bk-summary { flex: 1; min-width: 0; }
.bk-pick { margin: 0; font-size: 0.92rem; font-weight: 700; color: #1a3a1a; }
.bk-pick.muted { font-weight: 600; color: #4a5a4a; }
.bk-after { margin: 2px 0 0; font-size: 0.78rem; color: #6a7a6a; }
.bk-foot .form-error { margin: 4px 0 0; font-size: 0.8rem; color: #a12525; }
.bk-send { flex-shrink: 0; min-height: 40px; padding: 0 20px; }

/* one RND at a time: plain information */
.one-rnd { background: #f4f6f4; border: 1px solid #d9e3dc; border-radius: 10px; padding: 12px 14px; margin-top: 14px; font-size: 0.84rem; color: #4a5a4a; line-height: 1.5; }
.one-rnd p { margin: 0 0 6px; }

@media (max-width: 640px) {
  .modal-overlay { padding: 0; align-items: stretch; }
  .booking-modal-box { max-width: none; max-height: none; height: 100%; border-radius: 0; }
  .bk-head { padding: 18px 16px 14px; }
  .bk-body { padding: 16px 16px 4px; }
  .bk-foot { flex-direction: column; align-items: stretch; padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); }
  .bk-send { width: 100%; }
  .seg { width: 100%; }
  .seg-btn { flex: 1; justify-content: center; }
  .cal { gap: 3px; }
  .cal-cell { min-height: 46px; }
  .cal-note { font-size: 0.6rem; }
  .tg { grid-template-columns: 1fr; gap: 6px; }
  .tg-label { padding-top: 0; }
}
</style>
