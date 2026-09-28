<template>
  <div class="profile-page">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="isLoading" class="placeholder-text">Loading…</p>

    <template v-else-if="rnd">
      <p class="breadcrumb"><NuxtLink to="/find-rnd">Find an RND</NuxtLink> / RND {{ rnd.user.first_name }} {{ rnd.user.last_name }}</p>

      <div class="profile-banner">
        <div class="big-avatar" :style="{ background: colorForId(rnd.user.id) }">{{ initialsFor(rnd.user) }}</div>
        <div class="banner-info">
          <h1 class="banner-name">RND {{ rnd.user.first_name }} {{ rnd.user.last_name }} <BadgeCheck :size="18" class="verified-icon" /></h1>
          <p class="banner-specialty">{{ rnd.specialization || 'General Practice' }}<template v-if="rnd.prc_license_number"> · PRC License #{{ rnd.prc_license_number }}</template></p>
          <div class="banner-chips">
            <span v-if="rnd.average_rating" class="chip chip-gold">★ {{ rnd.average_rating.toFixed(1) }} ({{ rnd.review_count }} review{{ rnd.review_count === 1 ? '' : 's' }})</span>
            <span v-if="rnd.languages.length" class="chip"><Languages :size="13" /> {{ rnd.languages.map(l => l.language_name).join(' · ') }}</span>
            <span v-for="f in offeredFormats" :key="f.key" class="chip"><component :is="f.icon" :size="12" /> {{ f.short }} Available</span>
          </div>
        </div>
        <div class="banner-fee">
          <div class="fee-amount">₱{{ formatFee(rnd.consultation_fee) }}</div>
          <div class="fee-unit">per session</div>
        </div>
      </div>

      <div class="content-grid">
        <div class="main-col">
          <div class="surface">
            <h3 class="surface-title">About</h3>
            <p class="bio-text">{{ rnd.bio || 'This RND has not added a bio yet.' }}</p>
          </div>

          <div class="surface">
            <h3 class="surface-title">Weekly Availability</h3>
            <div v-if="isLoadingAvailability" class="placeholder-text">Loading…</div>
            <div v-else-if="availabilityByDay.some(d => d.slots.length)" class="avail-grid">
              <div v-for="d in availabilityWeekMonFirst" :key="d.day" class="avail-box" :class="{ muted: !d.slots.length }">
                <p class="avail-day">{{ d.short }}</p>
                <p class="avail-hours">{{ d.slots.length ? d.slots.map(s => compactHours(s.start_time, s.end_time)).join(', ') : '—' }}</p>
              </div>
            </div>
            <p v-else class="empty-note">This RND hasn't set their availability yet.</p>
          </div>

          <div class="surface">
            <div class="reviews-header">
              <h3 class="surface-title">Patient Reviews</h3>
              <span v-if="rnd.average_rating" class="chip chip-gold">★ {{ rnd.average_rating.toFixed(1) }} average</span>
            </div>
            <div v-if="isLoadingReviews" class="placeholder-text">Loading reviews…</div>
            <div v-else-if="reviews.length" class="review-list">
              <div v-for="review in reviews" :key="review.id" class="review-row">
                <div class="review-top">
                  <span class="review-name">{{ review.client_name }}</span>
                  <span class="review-stars">{{ '★'.repeat(review.rating) }}{{ '☆'.repeat(5 - review.rating) }}</span>
                </div>
                <p v-if="review.comment" class="review-comment">"{{ review.comment }}"</p>
              </div>
            </div>
            <p v-else class="empty-note">No reviews yet.</p>
          </div>
        </div>

        <div class="sidebar-col">
          <div class="surface sticky-card">
            <h3 class="surface-title">Start Your Care Journey</h3>
            <p class="sidebar-desc">
              Book a session with RND {{ rnd.user.first_name }} {{ rnd.user.last_name }}. They'll confirm your appointment, and your care plan starts from there.
            </p>

            <button class="primary-btn" type="button" :disabled="!offeredFormats.length" @click="openBookingModal">Book Appointment</button>

            <div class="info-note">
              <Info :size="15" />
              <span>Pre-consultation screening is required before your first appointment can be confirmed.</span>
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
          <p class="booking-sub">Pick a session format and a time that works — RND {{ rnd.user.first_name }} {{ rnd.user.last_name }} will confirm within 24 hours.</p>

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
          </div>

          <div class="booking-section">
            <h4 class="section-h">Pick a Date</h4>
            <p class="section-sub">Based on RND {{ rnd.user.first_name }}'s weekly availability.</p>

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
                :class="{ 'out-month': !cell.inMonth, available: cell.available, selected: cell.iso === selectedDateISO, disabled: !cell.available }"
                :disabled="!cell.available"
                @click="selectDate(cell)"
              >{{ cell.day }}</button>
            </div>

            <div v-if="selectedDateISO" class="time-slot-row">
              <button
                v-for="slot in timeSlots" :key="slot.value"
                type="button"
                class="time-slot-btn" :class="{ selected: selectedTime === slot.value }"
                @click="selectedTime = slot.value"
              >{{ slot.label }}</button>
              <p v-if="!timeSlots.length" class="availability-warn">No time slots available this day.</p>
            </div>
          </div>

          <div class="booking-section">
            <h4 class="section-h">Notes for your RND <span class="optional">(optional)</span></h4>
            <textarea v-model="bookingNotes" rows="3" placeholder="Anything you'd like your RND to know before the session..."></textarea>
          </div>

          <p v-if="bookingError" class="form-error">{{ bookingError }}</p>

          <button class="confirm-btn" type="button" :disabled="!canConfirmBooking || isBooking" @click="confirmBooking">
            <BadgeCheck :size="15" /> {{ isBooking ? 'Booking…' : 'Confirm Booking' }}
          </button>
          <p v-if="bookingHint" class="booking-hint">{{ bookingHint }}</p>
          <p class="submit-note">You'll be asked to pay after your RND confirms the appointment.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { BadgeCheck, Languages, Info, X, ChevronLeft, ChevronRight, Video, MessageSquare, MapPin } from 'lucide-vue-next'

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

const AVATAR_COLORS = ['#1e4a26', '#3a6b3a', '#D4A017', '#6a8a6a', '#8a6a3a']
function colorForId(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}
function initialsFor(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
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

onMounted(() => {
  loadProfile()
  loadReviews()
  loadAvailability()
})

/* ---------- BOOK APPOINTMENT MODAL ---------- */
const bookingModalOpen = ref(false)
const formats = [
  { key: 'video', label: 'Video Call', short: 'Video', icon: Video },
  { key: 'chat', label: 'Chat', short: 'Chat', icon: MessageSquare },
  { key: 'in_person', label: 'In-Person', short: 'In-Person', icon: MapPin },
]
const offeredFormats = computed(() => formats.filter(f => rnd.value?.consultation_modes?.includes(f.key)))
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
  return slotsForDate(iso).length > 0
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
    })
  }
  return cells
})

function selectDate(cell) {
  if (!cell.available) return
  selectedDateISO.value = cell.iso
  selectedTime.value = ''
}

// Bookings are 60 minutes, so slots start at the RND's real start time and
// step hourly while a full session still fits before their end time (e.g.
// 1:30 PM–7:00 PM → 1:30 … 5:30 PM). Times already past today are skipped.
const SESSION_MINUTES = 60
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
    for (let start = toMinutes(s.start_time); start + SESSION_MINUTES <= end; start += SESSION_MINUTES) {
      if (isToday && start <= nowMinutes) continue
      const h = Math.floor(start / 60)
      const m = start % 60
      const value = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
      if (seen.has(value)) continue
      seen.add(value)
      slots.push({ value, label: `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}` })
    }
  }
  return slots.sort((a, b) => a.value.localeCompare(b.value))
}

const bookingHint = computed(() => {
  if (!selectedDateISO.value) return 'Pick a date to see available times.'
  if (!selectedTime.value) return 'Pick a time to continue.'
  return ''
})

const canConfirmBooking = computed(() => selectedDateISO.value !== '' && selectedTime.value !== '')

function openBookingModal() {
  bookingType.value = offeredFormats.value[0]?.key || 'video'
  selectedDateISO.value = ''
  selectedTime.value = ''
  bookingNotes.value = ''
  bookingError.value = ''
  viewMonth.value = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
  bookingModalOpen.value = true
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
    bookingError.value = data.detail || data.non_field_errors?.[0] || data.type?.[0] || data.rnd_id?.[0]
      || 'Could not book this appointment. Please try again.'
  } finally {
    isBooking.value = false
  }
}
</script>

<style scoped>
* { box-sizing: border-box; }

.profile-page { font-family: 'Inter', sans-serif; }

.breadcrumb { font-size: 0.8rem; color: #8a9a8a; margin: 0 0 14px; }
.breadcrumb :deep(a) { color: #3a6b3a; text-decoration: none; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.profile-banner {
  background: #14301a; border-radius: 14px; padding: 28px 32px; color: #fff;
  display: flex; align-items: center; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;
}
.big-avatar {
  width: 76px; height: 76px; border-radius: 50%; color: #fff; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.4rem;
}
.banner-info { flex: 1; min-width: 200px; }
.banner-name { font-family: 'Playfair Display', serif; font-size: 1.4rem; margin: 0; display: flex; align-items: center; gap: 8px; }
.verified-icon { color: #D4A017; }
.banner-specialty { font-size: 0.85rem; color: #c9d9c9; margin: 6px 0 10px; }
.banner-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip {
  font-size: 0.74rem; font-weight: 600; padding: 4px 11px; border-radius: 20px;
  background: rgba(255,255,255,0.12); color: #fff; display: inline-flex; align-items: center; gap: 5px;
}
.chip-gold { background: #D4A017; color: #1a3a1a; }
.banner-fee { text-align: right; }
.fee-amount { font-size: 1.4rem; font-weight: 700; }
.fee-unit { font-size: 0.72rem; color: #a9c0a9; }

.content-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; align-items: start; }
@media (max-width: 900px) { .content-grid { grid-template-columns: 1fr; } }

.main-col { display: flex; flex-direction: column; gap: 16px; }
.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px 22px; }
.surface-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 12px; }

.bio-text { font-size: 0.87rem; color: #4a5a4a; line-height: 1.6; margin: 0; }

.avail-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }
.avail-box { background: #f7f9f7; border-radius: 8px; padding: 10px 6px; text-align: center; }
.avail-box.muted { background: #f2f3f1; opacity: 0.6; }
.avail-day { font-size: 0.75rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.avail-hours { font-size: 0.75rem; color: #6a7a6a; margin: 3px 0 0; }
.avail-box.muted .avail-day, .avail-box.muted .avail-hours { color: #9aaa9a; }

@media (max-width: 640px) {
  .avail-grid { grid-template-columns: repeat(4, 1fr); }
}

.reviews-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.review-list { margin-top: 8px; }
.review-row { padding: 14px 0; border-bottom: 1px solid #f0f0e6; }
.review-row:last-child { border-bottom: none; }
.review-top { display: flex; justify-content: space-between; margin-bottom: 4px; }
.review-name { font-weight: 700; font-size: 0.87rem; color: #1a3a1a; }
.review-stars { color: #D4A017; font-size: 0.8rem; }
.review-comment { font-size: 0.85rem; color: #6a7a6a; margin: 0; }
.empty-note { font-size: 0.85rem; color: #9aaa9a; margin: 0; }

.sidebar-col { position: sticky; top: 20px; }
.sticky-card { display: flex; flex-direction: column; }
.sidebar-desc { font-size: 0.84rem; color: #6a7a6a; margin: 0 0 16px; line-height: 1.5; }

.primary-btn {
  display: block; width: 100%; text-align: center; text-decoration: none; border: none;
  background: #D4A017; color: #1a3a1a; border-radius: 8px; padding: 12px;
  font-weight: 700; font-size: 0.88rem; cursor: pointer; margin-bottom: 10px;
}
.primary-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.info-note {
  display: flex; align-items: flex-start; gap: 8px; margin-top: 16px;
  background: #e3edf7; color: #2f6fa8; border-radius: 8px; padding: 10px 12px; font-size: 0.78rem;
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

.time-slot-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px; }
.time-slot-btn { border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 8px; padding: 10px 16px; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
.time-slot-btn.selected { background: #14301a; border-color: #14301a; color: #fff; }
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
