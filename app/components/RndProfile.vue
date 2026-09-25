<template>
  <div class="rnd-profile-page">
    <div v-if="!rnd" class="not-found">
      <p>We couldn't find that RND profile.</p>
      <NuxtLink to="/find-rnd" class="outline-btn">← Back to Find an RND</NuxtLink>
    </div>

    <template v-else>
      <!-- HEADER BANNER -->
      <div class="profile-banner">
        <div class="banner-blob"></div>
        <div class="banner-left">
          <div class="banner-avatar" :style="{ background: rnd.avatarColor, color: rnd.avatarTextColor || '#fff' }">{{ rnd.initials }}</div>
          <div>
            <p class="banner-name">{{ rnd.name }} <BadgeCheck :size="16" class="verified-icon" /></p>
            <p class="banner-specialty">{{ rnd.specialty }} · PRC License #{{ rnd.license }}</p>
            <div class="banner-chips">
              <span class="chip chip-gold">★ {{ rnd.rating }} ({{ rnd.reviews.length }} reviews)</span>
              <span class="chip">{{ rnd.languages.join(' · ') }}</span>
              <span class="chip"><component :is="modeIcon(rnd.consultMode)" :size="12" /> {{ rnd.consultMode }} Available</span>
            </div>
          </div>
        </div>
        <div class="banner-fee">
          <p class="fee-amount">₱{{ rnd.fee }}</p>
          <p class="fee-unit">per session</p>
        </div>
      </div>

      <div class="profile-grid">
        <div class="profile-col">
          <!-- ABOUT -->
          <div class="panel">
            <h3 class="panel-title">About</h3>
            <p class="about-text">{{ rnd.bio }}</p>
            <div class="stats-row">
              <div class="stat-box">
                <p class="stat-value">{{ rnd.yearsExperience }}+</p>
                <p class="stat-label">Years Experience</p>
              </div>
              <div class="stat-box">
                <p class="stat-value">{{ rnd.patientsHelped }}+</p>
                <p class="stat-label">Patients Helped</p>
              </div>
              <div class="stat-box">
                <p class="stat-value">{{ rnd.rating }}</p>
                <p class="stat-label">Average Rating</p>
              </div>
              <div class="stat-box">
                <p class="stat-value">{{ rnd.responseRate }}%</p>
                <p class="stat-label">Response Rate</p>
              </div>
            </div>
          </div>

          <!-- AVAILABILITY -->
          <div class="panel">
            <h3 class="panel-title">Weekly Availability</h3>
            <div class="avail-grid">
              <div v-for="d in rnd.availability" :key="d.day" class="avail-box" :class="{ muted: d.hours === '—' }">
                <p class="avail-day">{{ d.day }}</p>
                <p class="avail-hours">{{ d.hours }}</p>
              </div>
            </div>
          </div>

          <!-- REVIEWS -->
          <div class="panel">
            <div class="panel-header-row">
              <h3 class="panel-title">Patient Reviews</h3>
              <span class="chip chip-gold">★ {{ rnd.rating }} average</span>
            </div>
            <div class="review-row" v-for="r in rnd.reviews" :key="r.name">
              <div class="review-top">
                <span class="review-name">{{ r.name }}</span>
                <span class="review-stars">{{ '★'.repeat(r.stars) }}{{ '☆'.repeat(5 - r.stars) }}</span>
              </div>
              <p class="review-text">"{{ r.text }}"</p>
            </div>
          </div>
        </div>

        <div class="profile-col-side">
          <div class="panel cta-panel">
            <h3 class="panel-title">Start Your Care Journey</h3>
            <p class="cta-text">Send a relationship request to {{ rnd.name }}. Once accepted, you can book your first appointment.</p>
            <button class="primary-btn full-width" @click="openBookingModal">Book Appointment</button>
            <div class="info-banner">
              <Info :size="15" class="info-icon" />
              Pre-consultation screening is required before your first appointment can be confirmed.
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- BOOK APPOINTMENT MODAL -->
    <div v-if="bookingModalOpen" class="modal-overlay" @click.self="closeBookingModal">
      <div class="booking-modal-box">
        <button class="modal-close-btn booking-close" @click="closeBookingModal"><X :size="18" /></button>

        <div class="booking-grid">
          <!-- LEFT: BOOKING FLOW -->
          <div class="booking-left">
            <h2 class="booking-title">Book Your First <em>Consultation</em></h2>
            <p class="booking-sub">You matched with {{ rnd.name }} based on your specialty and screening. Pick a time that works and they'll confirm within 24 hours.</p>
            <span class="verified-chip"><BadgeCheck :size="13" /> PRC Lic. #{{ rnd.license }} · Verified by NutriMatch admin</span>

            <div class="rnd-mini-row">
              <div class="rnd-mini-avatar" :style="{ background: rnd.avatarColor, color: rnd.avatarTextColor || '#fff' }">{{ rnd.initials }}</div>
              <div class="rnd-mini-info">
                <p class="rnd-mini-name">{{ rnd.name }}</p>
                <p class="rnd-mini-sub">{{ rnd.specialty }} · ★ {{ rnd.rating }} ({{ rnd.reviews.length }} reviews)</p>
              </div>
              <NuxtLink to="/find-rnd" class="outline-btn small">Choose a different RND</NuxtLink>
            </div>

            <div class="booking-section">
              <h4 class="section-h">Session Format</h4>
              <p class="section-sub">How would you like to meet for your first consultation?</p>
              <div class="format-row">
                <button
                  v-for="f in formats" :key="f.key"
                  class="format-card" :class="{ active: consultType === f.key }"
                  @click="consultType = f.key"
                >
                  <component :is="f.icon" :size="17" />
                  <span class="format-name">{{ f.label }}</span>
                  <span class="format-desc">{{ f.desc }}</span>
                </button>
              </div>
            </div>

            <div class="booking-section">
              <h4 class="section-h">Pick a Date</h4>
              <p class="section-sub">{{ rnd.name }}'s available slots for the next two weeks.</p>

              <div class="calendar-head">
                <span class="calendar-month">{{ viewMonthLabel }}</span>
                <div class="calendar-nav">
                  <button @click="shiftMonth(-1)"><ChevronLeft :size="15" /></button>
                  <button @click="shiftMonth(1)"><ChevronRight :size="15" /></button>
                </div>
              </div>
              <div class="calendar-grid">
                <span v-for="d in dayHeaders" :key="d" class="calendar-day-header">{{ d }}</span>
                <button
                  v-for="(cell, i) in calendarCells" :key="i"
                  class="calendar-cell"
                  :class="{ 'out-month': !cell.inMonth, available: cell.available, selected: cell.iso === selectedDateISO, disabled: !cell.available }"
                  :disabled="!cell.available"
                  @click="selectDate(cell)"
                >{{ cell.day }}</button>
              </div>

              <div v-if="selectedDateISO" class="time-slot-row">
                <button
                  v-for="slot in timeSlots" :key="slot.value"
                  class="time-slot-btn" :class="{ selected: selectedTime === slot.value }"
                  @click="selectedTime = slot.value"
                >{{ slot.label }}</button>
                <p v-if="!timeSlots.length" class="availability-note availability-warn">No time slots available this day.</p>
              </div>
            </div>

            <div class="booking-section">
              <h4 class="section-h">Anything {{ rnd.name.replace('RND ', 'RND ') }} should know beforehand?</h4>
              <p class="section-sub">Optional — shared with your RND ahead of the session.</p>
              <textarea v-model="reasonText" rows="3" placeholder="e.g. Diabetes management, weight loss consultation..."></textarea>
            </div>

            <button class="confirm-btn" :disabled="!canSendBooking" @click="sendBookingRequest">
              <BadgeCheck :size="15" /> Confirm Booking
            </button>
          </div>
        </div>
      </div>    </div>

    <!-- SUCCESS TOAST -->
    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle :size="16" /> Consultation request sent! Waiting for RND confirmation.
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { BadgeCheck, Video, MessageCircle, Users, Info, X, CheckCircle, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { useAppointments } from '~/composables/useAppointments'

const route = useRoute()

// TODO: local mock data — move into the shared mock db (db.rnds) once the
// client-facing RND directory data model is defined; this duplicates the
// summary list in components/FindRnd.vue with full profile detail added.
const rnds = [
  {
    name: 'RND Ivy Hope Alba', initials: 'IA', avatarColor: '#1e4a26', license: '0012345',
    specialty: 'Diabetes & Renal Nutrition Specialist', rating: 4.9, fee: 800,
    languages: ['Cebuano', 'English'], consultMode: 'Video',
    bio: 'RND Ivy Hope Alba has over a decade of clinical experience in hospital-based dietetics, specializing in diabetic and renal Medical Nutrition Therapy. She combines structured NRS-2002 screening with FNRI Food Exchange List meal planning to deliver evidence-based, culturally appropriate care for Filipino patients managing chronic conditions.',
    yearsExperience: 10, patientsHelped: 180, responseRate: 98,
    availability: [
      { day: 'Mon', hours: '9–5', start: 9, end: 17 }, { day: 'Tue', hours: '9–5', start: 9, end: 17 }, { day: 'Wed', hours: '—' },
      { day: 'Thu', hours: '1–6', start: 13, end: 18 }, { day: 'Fri', hours: '9–5', start: 9, end: 17 }, { day: 'Sat', hours: '9–12', start: 9, end: 12 }, { day: 'Sun', hours: '—' }
    ],
    reviews: [
      { name: 'Julia N.', stars: 5, text: 'Helped me find an RND who speaks Cebuano and truly understands my diabetes. I feel heard for the first time.' },
      { name: 'Roberto M.', stars: 5, text: 'Very thorough during my initial screening. Explained my NRS score and BMI in terms I could actually understand.' },
      { name: 'Anna L.', stars: 4, text: 'Great meal plan, very practical for everyday Filipino cooking. Wish video sessions ran a bit longer.' }
    ]
  },
  {
    name: 'RND Marco Reyes', initials: 'MR', avatarColor: '#D4A017', avatarTextColor: '#1a3a1a', license: '0018210',
    specialty: 'Hypertension & Cardiac Care Specialist', rating: 4.8, fee: 650,
    languages: ['Tagalog', 'English'], consultMode: 'Chat',
    bio: 'RND Marco Reyes focuses on DASH-aligned meal planning for hypertensive and post-cardiac patients, working closely with cardiology referrals to design sustainable, heart-healthy Filipino diets.',
    yearsExperience: 7, patientsHelped: 120, responseRate: 95,
    availability: [
      { day: 'Mon', hours: '1–6', start: 13, end: 18 }, { day: 'Tue', hours: '—' }, { day: 'Wed', hours: '9–5', start: 9, end: 17 },
      { day: 'Thu', hours: '9–5', start: 9, end: 17 }, { day: 'Fri', hours: '1–6', start: 13, end: 18 }, { day: 'Sat', hours: '—' }, { day: 'Sun', hours: '—' }
    ],
    reviews: [
      { name: 'Mika S.', stars: 5, text: 'Explained my DASH diet plan very clearly. Blood pressure has improved a lot.' },
      { name: 'Dennis F.', stars: 4, text: 'Responsive over chat, good for a busy schedule.' }
    ]
  },
  {
    name: 'RND Camille Tan', initials: 'CT', avatarColor: '#7aa87a', license: '0021044',
    specialty: 'Weight Management Specialist', rating: 4.7, fee: 700,
    languages: ['Ilocano', 'English'], consultMode: 'In-Person',
    bio: 'RND Camille Tan uses a behavior-based weight management approach combining FNRI food exchanges with habit coaching, helping patients build lasting routines rather than short-term diets.',
    yearsExperience: 6, patientsHelped: 95, responseRate: 92,
    availability: [
      { day: 'Mon', hours: '9–5', start: 9, end: 17 }, { day: 'Tue', hours: '9–5', start: 9, end: 17 }, { day: 'Wed', hours: '9–5', start: 9, end: 17 },
      { day: 'Thu', hours: '—' }, { day: 'Fri', hours: '9–5', start: 9, end: 17 }, { day: 'Sat', hours: '9–12', start: 9, end: 12 }, { day: 'Sun', hours: '—' }
    ],
    reviews: [
      { name: 'Grace P.', stars: 5, text: 'Practical habit-based tips instead of just a strict diet. Lost 6kg in 3 months.' },
      { name: 'Elmer V.', stars: 4, text: 'In-person sessions were worth it — very hands-on.' }
    ]
  },
  {
    name: 'RND Dexter Paz', initials: 'DP', avatarColor: '#3a6b3a', license: '0009981',
    specialty: 'Pediatric Nutrition Specialist', rating: 5.0, fee: 750,
    languages: ['Tagalog', 'Cebuano'], consultMode: 'Video',
    bio: 'RND Dexter Paz supports growth monitoring and dietary diversity scoring for children under 12, working with parents to build balanced, kid-friendly Filipino meal plans.',
    yearsExperience: 5, patientsHelped: 60, responseRate: 99,
    availability: [
      { day: 'Mon', hours: '9–5', start: 9, end: 17 }, { day: 'Tue', hours: '—' }, { day: 'Wed', hours: '9–5', start: 9, end: 17 },
      { day: 'Thu', hours: '9–5', start: 9, end: 17 }, { day: 'Fri', hours: '—' }, { day: 'Sat', hours: '9–12', start: 9, end: 12 }, { day: 'Sun', hours: '—' }
    ],
    reviews: [
      { name: 'Cherry A.', stars: 5, text: 'My son finally eats his vegetables! Great with kids.' },
      { name: 'Noel D.', stars: 5, text: 'Very patient explaining growth charts to first-time parents like us.' }
    ]
  },
  {
    name: 'RND Lara Mendoza', initials: 'LM', avatarColor: '#f0dca8', avatarTextColor: '#1a3a1a', license: '0033217',
    specialty: 'General Practice', rating: 4.6, fee: 600,
    languages: ['English'], consultMode: 'Chat',
    bio: 'RND Lara Mendoza runs a generalist MNT practice with a strong track record across diverse dietary conditions, a good starting point for patients who are not yet sure which specialty they need.',
    yearsExperience: 8, patientsHelped: 210, responseRate: 90,
    availability: [
      { day: 'Mon', hours: '9–5', start: 9, end: 17 }, { day: 'Tue', hours: '9–5', start: 9, end: 17 }, { day: 'Wed', hours: '9–5', start: 9, end: 17 },
      { day: 'Thu', hours: '9–5', start: 9, end: 17 }, { day: 'Fri', hours: '9–5', start: 9, end: 17 }, { day: 'Sat', hours: '—' }, { day: 'Sun', hours: '—' }
    ],
    reviews: [
      { name: 'Wilfred T.', stars: 5, text: 'Great generalist, pointed me to the right specialist eventually.' },
      { name: 'Sheila R.', stars: 4, text: 'Good communication, a bit slow to reply on weekends.' }
    ]
  },
  {
    name: 'RND Rico Santos', initials: 'RS', avatarColor: '#00382a', license: '0027764',
    specialty: 'Renal Nutrition Specialist', rating: 4.9, fee: 900,
    languages: ['Tagalog', 'English'], consultMode: 'In-Person',
    bio: 'RND Rico Santos is a dialysis-stage renal diet specialist working closely with nephrology referrals to manage fluid, potassium, and phosphorus intake for patients with advanced kidney disease.',
    yearsExperience: 11, patientsHelped: 140, responseRate: 97,
    availability: [
      { day: 'Mon', hours: '1–6', start: 13, end: 18 }, { day: 'Tue', hours: '1–6', start: 13, end: 18 }, { day: 'Wed', hours: '—' },
      { day: 'Thu', hours: '1–6', start: 13, end: 18 }, { day: 'Fri', hours: '1–6', start: 13, end: 18 }, { day: 'Sat', hours: '9–12', start: 9, end: 12 }, { day: 'Sun', hours: '—' }
    ],
    reviews: [
      { name: 'Perla M.', stars: 5, text: 'Very knowledgeable about dialysis diets, coordinated well with my nephrologist.' },
      { name: 'Boyet L.', stars: 5, text: 'Explained potassium and phosphorus limits clearly with real food examples.' }
    ]
  }
]

const rnd = computed(() => rnds.find(r => r.name === route.query.rnd) || null)

/* ---------- BOOK APPOINTMENT MODAL ---------- */
const bookingModalOpen = ref(false)
const formats = [
  { key: 'Video', label: 'Video Call', desc: 'Face-to-face, from home', icon: Video },
  { key: 'Chat', label: 'Chat', desc: 'Text-based, at your pace', icon: MessageCircle },
  { key: 'In-Person', label: 'In-Person', desc: 'Visit the clinic', icon: Users }
]
const consultType = ref('Video')
const selectedDateISO = ref('')
const selectedTime = ref('')
const reasonText = ref('')

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const todayISO = new Date().toISOString().split('T')[0]

/* ---------- CALENDAR ---------- */
const dayHeaders = DAY_NAMES
const viewMonth = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1))
const viewMonthLabel = computed(() => viewMonth.value.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }))

function shiftMonth(delta) {
  viewMonth.value = new Date(viewMonth.value.getFullYear(), viewMonth.value.getMonth() + delta, 1)
}
function toISO(d) {
  return d.toISOString().split('T')[0]
}
function isDayAvailable(date) {
  if (!rnd.value) return false
  const iso = toISO(date)
  if (iso < todayISO) return false
  const dayName = DAY_NAMES[date.getDay()]
  const info = rnd.value.availability.find(a => a.day === dayName)
  return !!(info && info.hours !== '—')
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
      available: d.getMonth() === month && isDayAvailable(d)
    })
  }
  return cells
})

function selectDate(cell) {
  if (!cell.available) return
  selectedDateISO.value = cell.iso
  selectedTime.value = ''
}

const selectedDayName = computed(() => {
  if (!selectedDateISO.value) return ''
  const d = new Date(selectedDateISO.value + 'T00:00:00')
  return DAY_NAMES[d.getDay()]
})
const dayAvailability = computed(() => {
  if (!rnd.value || !selectedDayName.value) return null
  return rnd.value.availability.find(a => a.day === selectedDayName.value) || null
})
const timeSlots = computed(() => {
  if (!dayAvailability.value || dayAvailability.value.hours === '—') return []
  const slots = []
  for (let h = dayAvailability.value.start; h < dayAvailability.value.end; h++) {
    const period = h >= 12 ? 'PM' : 'AM'
    const hour12 = h % 12 === 0 ? 12 : h % 12
    slots.push({ value: `${String(h).padStart(2, '0')}:00`, label: `${hour12}:00 ${period}` })
  }
  return slots
})

function openBookingModal() {
  consultType.value = 'Video'
  selectedDateISO.value = ''
  selectedTime.value = ''
  reasonText.value = ''
  viewMonth.value = new Date(new Date().getFullYear(), new Date().getMonth(), 1)
  bookingModalOpen.value = true
}
function closeBookingModal() {
  bookingModalOpen.value = false
}

/* ---------- SUCCESS TOAST ---------- */
const toastVisible = ref(false)
let toastTimer = null
function showToast() {
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 4000)
}

const { addAppointment } = useAppointments()

const canSendBooking = computed(() =>
  selectedDateISO.value !== '' && selectedTime.value !== ''
)

function sendBookingRequest() {
  if (!canSendBooking.value) return
  // TODO: wire up to a real send-appointment-request + payment API call
  addAppointment({
    rndName: rnd.value?.name,
    consultType: consultType.value,
    preferredDateTime: `${selectedDateISO.value}T${selectedTime.value}`,
    reason: reasonText.value
  })
  closeBookingModal()
  showToast()
}

function modeIcon(mode) {
  if (mode === 'Video') return Video
  if (mode === 'Chat') return MessageCircle
  return Users
}
</script>

<style scoped>
* { box-sizing: border-box; }
.rnd-profile-page { font-family: 'Inter', sans-serif; }

.not-found { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 40px; text-align: center; color: #6a7a6a; }
.not-found p { margin: 0 0 14px; }

/* BANNER */
.profile-banner {
  position: relative; overflow: hidden;
  background: linear-gradient(140deg, #00382a 0%, #005a42 100%);
  border-radius: 16px; padding: 40px 35px; margin-bottom: 20px; color: #fff;
  display: flex; align-items: center; justify-content: space-between; gap:50px; flex-wrap: wrap;
}
.banner-blob { position: absolute; width: 220px; height: 220px; border-radius: 50%; background: rgba(255,255,255,0.05); top: -70px; right: -50px; z-index: 0; }
.banner-left { display: flex; align-items: center; gap: 18px; position: relative; z-index: 1; }
.banner-avatar { width: 64px; height: 64px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.3rem; flex-shrink: 0; }
.banner-name { display: flex; align-items: center; gap: 7px; font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; margin: 0; }
.verified-icon { color: #D4A017; }
.banner-specialty { font-size: 0.87rem; color: #cfe0d5; margin: 4px 0 10px; }
.banner-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { display: inline-flex; align-items: center; gap: 4px; font-size: 0.75rem; font-weight: 600; background: rgba(255,255,255,0.1); color: #fff; padding: 4px 12px; border-radius: 999px; }
.chip-gold { background: #fdf1d6; color: #b8860b; }
.banner-fee { text-align: right; position: relative; z-index: 1; }
.fee-amount { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 700; margin: 0; }
.fee-unit { font-size: 0.78rem; color: #cfe0d5; margin: 2px 0 0; }

/* GRID */
.profile-grid { display: grid; grid-template-columns: 1.6fr 1fr; gap: 20px; align-items: start; }
.profile-col { display: flex; flex-direction: column; gap: 16px; }
.profile-col-side { position: sticky; top: 90px; }

.panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px 24px; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 14px; }
.panel-header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.panel-header-row .panel-title { margin: 0; }

.about-text { font-size: 0.9rem; color: #4a5a4a; line-height: 1.65; margin: 0 0 20px; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; text-align: center; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stat-label { font-size: 0.74rem; color: #9aaa9a; margin: 3px 0 0; }

.avail-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; }
.avail-box { background: #f7f9f7; border-radius: 8px; padding: 10px 6px; text-align: center; }
.avail-box.muted { background: #f2f3f1; opacity: 0.6; }
.avail-day { font-size: 0.75rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.avail-hours { font-size: 0.75rem; color: #6a7a6a; margin: 3px 0 0; }
.avail-box.muted .avail-day, .avail-box.muted .avail-hours { color: #9aaa9a; }

.review-row { padding: 14px 0; border-top: 1px solid #f0f2f0; }
.review-row:first-of-type { border-top: none; padding-top: 0; }
.review-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 5px; }
.review-name { font-weight: 700; color: #1a3a1a; font-size: 0.87rem; }
.review-stars { color: #D4A017; font-size: 0.85rem; letter-spacing: 1px; }
.review-text { font-size: 0.86rem; color: #6a7a6a; line-height: 1.5; margin: 0; }

/* CTA PANEL */
.cta-text { font-size: 0.86rem; color: #6a7a6a; line-height: 1.55; margin: 0 0 18px; }
.primary-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 12px; font-weight: 700; font-size: 0.9rem; cursor: pointer; margin-bottom: 10px; }
.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.availability-note { font-size: 0.8rem; color: #6a7a6a; margin: 4px 0 18px; }
.availability-note.availability-warn { color: #c0392b; background: #fbe5e2; border-radius: 8px; padding: 10px 12px; margin: 4px 0 18px; }
.outline-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 12px; font-weight: 600; font-size: 0.9rem; cursor: pointer; margin-bottom: 16px; text-decoration: none; display: block; text-align: center; }
.full-width { width: 100%; }

.info-banner { display: flex; align-items: flex-start; gap: 8px; background: #eef1f6; border-radius: 8px; padding: 12px 14px; font-size: 0.8rem; color: #3a4a5a; line-height: 1.5; }
.info-icon { color: #2a5a8a; flex-shrink: 0; margin-top: 1px; }

/* BOOK APPOINTMENT MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(20,30,20,0.55); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 20px; }
.booking-modal-box { position: relative; background: #fff; border-radius: 18px; width: 100%; max-width: 720px; max-height: 92vh; overflow-y: auto; }
.booking-close {
  position: sticky; top: 14px; float: right; margin-right: 14px; z-index: 5; background: #fff; border: 1px solid #eceeec;
  border-radius: 50%; width: 32px; height: 32px;
}
.modal-close-btn { border: none; background: none; color: #6a7a6a; cursor: pointer; display: flex; align-items: center; justify-content: center; }

.booking-grid { display: block; }
.booking-left { padding: 30px 32px 34px; }
.booking-title { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1a3a1a; margin: 0 0 8px; }
.booking-title em { color: #D4A017; font-style: italic; }
.booking-sub { font-size: 0.87rem; color: #6a7a6a; line-height: 1.55; margin: 0 0 16px; max-width: 480px; }
.verified-chip {
  display: inline-flex; align-items: center; gap: 6px; background: #e3f3ea; color: #1f8f5c; font-size: 0.76rem; font-weight: 700;
  padding: 6px 14px; border-radius: 999px; margin-bottom: 20px;
}

.rnd-mini-row { display: flex; align-items: center; gap: 14px; border: 1px solid #eceeec; border-radius: 12px; padding: 14px 16px; margin-bottom: 22px; flex-wrap: wrap; }
.rnd-mini-avatar { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; flex-shrink: 0; }
.rnd-mini-info { flex: 1; min-width: 160px; }
.rnd-mini-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.rnd-mini-sub { font-size: 0.78rem; color: #9aaa9a; margin: 2px 0 0; }

.booking-section { margin-bottom: 26px; }
.section-h { font-family: 'Playfair Display', serif; font-size: 1rem; color: #1a3a1a; margin: 0 0 4px; }
.section-sub { font-size: 0.8rem; color: #9aaa9a; margin: 0 0 14px; }

.format-row { display: flex; gap: 10px; flex-wrap: wrap; }
.format-card {
  flex: 1; min-width: 150px; display: flex; flex-direction: column; align-items: flex-start; gap: 4px;
  border: 1.5px solid #d5dad5; background: #fff; border-radius: 12px; padding: 14px 16px; cursor: pointer; text-align: left;
  color: #4a5a4a;
}
.format-card.active { border-color: #1f8f5c; background: #f0f9f4; color: #1a3a1a; }
.format-name { font-size: 0.87rem; font-weight: 700; }
.format-desc { font-size: 0.75rem; color: #9aaa9a; }

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

.booking-section textarea {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 13px; font-size: 0.85rem; font-family: inherit; color: #2a2a2a; resize: vertical;
}

/* CONFIRM BUTTON */
.confirm-btn {
  width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; background: #14301a; color: #fff;
  border: none; border-radius: 10px; padding: 14px; font-weight: 700; font-size: 0.9rem; cursor: pointer; margin-top: 6px;
}
.confirm-btn:hover:not(:disabled) { background: #1c421f; }
.confirm-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* TOAST */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

@media (max-width: 1000px) {
  .profile-grid { grid-template-columns: 1fr; }
  .profile-col-side { position: static; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .avail-grid { grid-template-columns: repeat(4, 1fr); }
}
</style>