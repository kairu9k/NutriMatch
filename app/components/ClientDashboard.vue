<template>
  <div class="client-dashboard">
    <!-- WELCOME BANNER -->
    <section class="welcome-banner">
      <div class="banner-blob"></div>
      <div class="banner-content">
        <span class="banner-badge"><span class="banner-badge-dot"></span> {{ todayLabel }}</span>
        <h1 class="banner-title">Hi {{ client.firstName }}, Week {{ client.programWeek }} of your nutrition program.</h1>
        <p class="banner-sub">
          Next consultation with {{ client.rnd.name }} on {{ client.nextConsultDay }}.
          Your BMI is in the <strong>{{ bmiCategoryDisplay }}</strong> range.
        </p>
        <div class="banner-actions">
          <button class="banner-btn" @click="navigateTo('/appointments')">View Appointment</button>
        </div>
      </div>
    </section>

    <!-- STAT CARDS -->
    <section class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon"><Activity :size="17" /></div>
        <p class="stat-value">{{ bmiDisplay }}</p>
        <p class="stat-label">Current BMI</p>
        <span class="status-pill" :class="hasLatestScreening ? 'pill-green' : 'pill-muted'">{{ bmiCategoryDisplay }}</span>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-gold"><Flame :size="17" /></div>
        <p class="stat-value">{{ tdeeDisplay }} <span v-if="hasLatestScreening" class="unit">kcal</span></p>
        <p class="stat-label">Daily Target (TDEE)</p>
        <p class="stat-note">Protein {{ macros.protein }}g · Carbs {{ macros.carbs }}g · Fat {{ macros.fat }}g</p>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><ClipboardCheck :size="17" /></div>
        <p class="stat-value">{{ nrsDisplay }} <span v-if="hasLatestScreening" class="unit">/ 3</span></p>
        <p class="stat-label">NRS-2002 Score</p>
        <span class="status-pill" :class="hasLatestScreening ? 'pill-gold' : 'pill-muted'">{{ hasLatestScreening ? 'At Risk — Monitored' : 'Pending screening' }}</span>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><CalendarDays :size="17" /></div>
        <p class="stat-value">{{ nextAppointment.dateShort }}</p>
        <p class="stat-label">Next Appointment</p>
        <p class="stat-note">{{ nextAppointment.time }} · {{ nextAppointment.detail }}</p>
      </div>
    </section>

    <!-- TABS -->
    <nav class="dash-tabs">
      <button v-for="tab in tabs" :key="tab.key" class="tab-item" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
        <component :is="tab.icon" :size="15" /> {{ tab.label }}
      </button>
    </nav>

    <!-- ============ OVERVIEW ============ -->
    <section v-if="activeTab === 'overview'" class="dash-grid">
      <div class="dash-col">
        <div class="panel">
          <div class="panel-header-row">
            <h3 class="panel-title">Weight Progress (kg)</h3>
            <span class="status-pill pill-green">↓ {{ weightLostTotal }} kg total</span>
          </div>
          <div class="weight-chart">
            <svg viewBox="0 0 460 110" width="100%" style="overflow: visible;">
              <defs><linearGradient id="wGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1a3a1a" stop-opacity=".12" /><stop offset="100%" stop-color="#1a3a1a" stop-opacity="0" /></linearGradient></defs>
              <g transform="translate(20,8)">
                <polyline :points="chartPoints" stroke="#1a3a1a" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
                <polygon :points="chartFillPoints" fill="url(#wGrad)" />
                <circle v-for="(p, i) in weightHistory" :key="i" :cx="p.x" :cy="p.y" :r="i === weightHistory.length - 1 ? 4 : 3.5" :fill="i === weightHistory.length - 1 ? '#D4A017' : '#1a3a1a'" />
                <text v-for="(p, i) in weightHistory" :key="'l' + i" :x="p.x - (i === weightHistory.length - 1 ? 10 : 4)" y="104" font-size="9" :fill="i === weightHistory.length - 1 ? '#D4A017' : '#8aaa8a'" :font-weight="i === weightHistory.length - 1 ? 700 : 400" font-family="Inter, sans-serif">{{ p.month }}</text>
              </g>
            </svg>
          </div>
        </div>

        <div class="panel">
          <h3 class="panel-title">Clinical Alerts</h3>
          <div class="alert-list">
            <div v-for="alert in clinicalAlerts" :key="alert.title" class="alert-item" :class="alert.level">
              <component :is="alert.level === 'level-warning' ? AlertTriangle : CheckCircle" :size="16" class="alert-icon" />
              <div class="alert-text">
                <p class="alert-name">{{ alert.title }}</p>
                <p class="alert-detail">{{ alert.detail }}</p>
              </div>
              <NuxtLink v-if="alert.actionLabel" to="/messages" class="alert-action">{{ alert.actionLabel }} →</NuxtLink>
            </div>
          </div>
        </div>

        <div class="panel">
          <h3 class="panel-title">Today's Macronutrient Targets</h3>
          <div class="macro-grid">
            <div class="macro-item">
              <p class="macro-value">{{ macros.carbs }}g</p>
              <p class="macro-label">Carbohydrates</p>
              <div class="macro-track"><div class="macro-fill fill-green" :style="{ width: macros.carbsPct + '%' }"></div></div>
            </div>
            <div class="macro-item">
              <p class="macro-value gold">{{ macros.protein }}g</p>
              <p class="macro-label">Protein</p>
              <div class="macro-track"><div class="macro-fill fill-gold" :style="{ width: macros.proteinPct + '%' }"></div></div>
            </div>
            <div class="macro-item">
              <p class="macro-value">{{ macros.fat }}g</p>
              <p class="macro-label">Fat</p>
              <div class="macro-track"><div class="macro-fill fill-green" :style="{ width: macros.fatPct + '%' }"></div></div>
            </div>
          </div>
        </div>
      </div>

      <div class="dash-col">
        <div class="panel" v-if="recentActivity.length">
          <div class="panel-header-row">
            <h3 class="panel-title">Recent Activity</h3>
            <NuxtLink to="/history" class="view-all-link">View All →</NuxtLink>
          </div>
          <div class="activity-row" v-for="entry in recentActivity" :key="entry.id">
            <span class="activity-dot" :class="activityDotClass(entry.type)"></span>
            <div>
              <p class="activity-title">{{ entry.title }}</p>
              <p class="activity-time">{{ entry.timestamp }}</p>
            </div>
          </div>
        </div>

        <div class="panel">
          <h3 class="panel-title">Latest Screening</h3>
          <template v-if="hasLatestScreening">
            <p class="screening-summary-text">
              Recorded {{ screening.lastRecordedDate }} — BMI {{ screening.bmi }} ({{ screening.bmiCategory }}), NRS-2002 {{ screening.nrs }}.
            </p>
            <button class="outline-btn full-width" @click="navigateTo('/pre-consultation-screening')">Update Screening</button>
          </template>
          <template v-else>
            <p class="screening-summary-text">No screening on file yet — this is recorded ahead of your first consultation.</p>
            <button class="outline-btn full-width" @click="navigateTo('/pre-consultation-screening')">Complete Screening</button>
          </template>
        </div>

        <div class="panel">
          <h3 class="panel-title">Your RND</h3>
          <div class="rnd-row">
            <div class="rnd-avatar">{{ client.rnd.initials }}</div>
            <div>
              <p class="rnd-name">{{ client.rnd.name }}</p>
              <p class="rnd-specialty">{{ client.rnd.specialty }}</p>
              <p class="rnd-rating">★ {{ client.rnd.rating }} ({{ client.rnd.reviews }} reviews)</p>
            </div>
          </div>
          <button class="outline-btn full-width" @click="navigateTo('/messages')">Send a Message</button>
        </div>

        <div class="panel">
          <h3 class="panel-title">Today's Reminders</h3>
          <div class="reminder-list">
            <div v-for="r in todaysReminders" :key="r.label" class="reminder-item">
              <component :is="r.icon" :size="16" :style="{ color: r.color }" />
              <span class="reminder-label">{{ r.label }}</span>
            </div>
          </div>
        </div>

        <div class="panel">
          <h3 class="panel-title">Upload Lab Results</h3>
          <label class="dropzone">
            <input type="file" class="dropzone-input" @change="onLabFileSelected" />
            <UploadCloud :size="24" class="dropzone-icon" />
            <span class="dropzone-text"><template v-if="labFileName">{{ labFileName }}</template><template v-else>Drag files here or <strong>browse</strong></template></span>
            <span class="dropzone-hint">PDF · JPG · PNG — max 5MB</span>
          </label>
        </div>
      </div>
    </section>

    <!-- ============ HEALTH SCREENING ============ -->
    <section v-if="activeTab === 'screening'" class="dash-grid-single">
      <div class="panel" v-if="hasLatestScreening">
        <span class="section-eyebrow">PRE-CONSULTATION SCREENING RECORD</span>
        <div class="screening-stats">
          <div class="screening-stat">
            <p class="screening-value">{{ screening.bmi }}</p>
            <p class="screening-label">BMI</p>
            <span class="status-pill pill-green">{{ screening.bmiCategory }}</span>
          </div>
          <div class="screening-stat">
            <p class="screening-value">{{ screening.bmr.toLocaleString() }}</p>
            <p class="screening-label">BMR (kcal)</p>
          </div>
          <div class="screening-stat">
            <p class="screening-value">{{ screening.tdee.toLocaleString() }}</p>
            <p class="screening-label">TDEE (kcal)</p>
          </div>
          <div class="screening-stat">
            <p class="screening-value">{{ screening.nrs }}</p>
            <p class="screening-label">NRS-2002 Score</p>
            <span class="status-pill" :class="screening.nrs >= 2 ? 'pill-gold' : 'pill-muted'">{{ screening.nrs >= 2 ? 'At Risk' : 'Low Risk' }}</span>
          </div>
        </div>
        <div class="info-banner">
          <Info :size="15" class="info-icon" />
          Your RND uses these values to personalize your care plan.
          <NuxtLink to="/pre-consultation-screening" class="info-link">Update Screening →</NuxtLink>
        </div>
      </div>
      <div class="panel" v-else>
        <span class="section-eyebrow">PRE-CONSULTATION SCREENING RECORD</span>
        <p class="screening-summary-text">No screening on file yet — this is recorded ahead of your first consultation.</p>
        <NuxtLink to="/pre-consultation-screening" class="outline-btn full-width" style="display: inline-block; text-align: center; text-decoration: none;">Complete Screening</NuxtLink>
      </div>

      <div class="panel table-panel" v-if="screeningHistory.length">
        <h3 class="panel-title">Screening History</h3>
        <table class="data-table">
          <thead>
            <tr><th>DATE</th><th>WEIGHT</th><th>HEIGHT</th><th>BMI</th><th>NRS SCORE</th><th>TDEE</th></tr>
          </thead>
          <tbody>
            <tr v-for="(row, i) in screeningHistory" :key="i">
              <td>{{ row.lastRecordedDate }}</td>
              <td>{{ row.weight }} kg</td>
              <td>{{ row.height }} cm</td>
              <td>{{ row.bmi }}</td>
              <td><span class="status-pill" :class="row.nrs >= 2 ? 'pill-gold' : 'pill-muted'">{{ row.nrs }}</span></td>
              <td>{{ row.tdee.toLocaleString() }} kcal</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- ============ MY TASKS ============ -->
    <section v-if="activeTab === 'tasks'" class="dash-grid-single">
      <div class="panel">
        <div class="panel-header-row">
          <h3 class="panel-title">Tasks Assigned by {{ client.rnd.name }}</h3>
          <span class="status-pill pill-gold">{{ pendingTaskCount }} pending</span>
        </div>
        <div class="task-list">
          <label v-for="task in tasks" :key="task.label" class="task-row">
            <input type="checkbox" v-model="task.done" />
            <div class="task-info">
              <p class="task-label">{{ task.label }}</p>
              <p class="task-detail">{{ task.schedule }}</p>
            </div>
            <span class="status-pill" :class="task.done ? 'pill-green' : 'pill-gold'">{{ task.done ? 'Done today' : 'Pending' }}</span>
          </label>
        </div>
      </div>
    </section>

    <!-- ============ LOG PROGRESS ============ -->
    <section v-if="activeTab === 'logging'" class="dash-grid">
      <div class="dash-col">
        <div class="panel">
          <span class="section-eyebrow">24-HOUR FOOD RECALL</span>
          <div class="form-row-3">
            <div class="field">
              <label>Meal Slot</label>
              <select v-model="foodLog.slot"><option v-for="s in mealSlots" :key="s">{{ s }}</option></select>
            </div>
            <div class="field">
              <label>Date</label>
              <input v-model="foodLog.date" type="date" />
            </div>
            <div class="field">
              <label>Time</label>
              <input v-model="foodLog.time" type="time" />
            </div>
          </div>
          <label class="field-label">What did you eat?</label>
          <textarea v-model="foodLog.notes" rows="3" placeholder="e.g. 1 cup brown rice, 1 piece grilled tilapia, 1 cup sautéed kangkong..."></textarea>
          <button class="primary-btn" @click="saveFoodLog">Save Food Log</button>
        </div>

        <div class="panel">
          <span class="section-eyebrow">TODAY'S LOG</span>
          <div class="log-list">
            <div v-for="entry in todaysLog" :key="entry.label" class="log-row">
              <span class="log-label">{{ entry.label }}</span>
              <span class="log-detail">{{ entry.detail }}</span>
              <span class="status-pill" :class="entry.logged ? 'pill-green' : 'pill-gold'">{{ entry.logged ? 'Logged' : 'Pending' }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="dash-col">
        <div class="panel">
          <span class="section-eyebrow">VITALS ENTRY</span>
          <label class="field-label">Weight (kg)</label>
          <input v-model.number="vitals.weight" type="number" class="full-input" />
          <label class="field-label">Blood Pressure (mmHg)</label>
          <input v-model="vitals.bp" type="text" class="full-input" placeholder="120/80" />
          <label class="field-label">Fasting Blood Glucose (mg/dL)</label>
          <input v-model.number="vitals.glucose" type="number" class="full-input" />
          <button class="primary-btn full-width" @click="saveVitals">Save Vitals</button>
        </div>

        <div class="panel">
          <span class="section-eyebrow">NOTES FOR RND</span>
          <textarea v-model="notesForRnd" rows="3" placeholder="Anything you'd like your RND to know..."></textarea>
          <button class="outline-btn full-width" @click="sendNotesToRnd">Send to {{ client.rnd.name }}</button>
        </div>
      </div>
    </section>

    <!-- ============ CONSULTATION SUMMARIES ============ -->
    <section v-if="activeTab === 'summaries'" class="dash-grid-single">
      <div v-for="s in consultationSummaries" :key="s.title" class="panel summary-card">
        <div class="panel-header-row">
          <div>
            <p class="summary-title">{{ s.title }}</p>
            <p class="summary-meta">{{ s.date }} · {{ s.mode }} · {{ client.rnd.name }}</p>
          </div>
          <span class="status-pill pill-muted">Completed</span>
        </div>
        <p class="summary-notes"><strong>Key Notes:</strong> {{ s.notes }}</p>
        <button v-if="s.hasFullRecord" class="outline-btn" @click="navigateTo('/ncp-records')">View Full NCP Record</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import {
  Activity, Flame, ClipboardCheck, CalendarDays, LayoutGrid, ShieldCheck, CheckSquare,
  PlusCircle, BookOpen, Receipt, AlertTriangle, CheckCircle,
  Info, Search, UploadCloud, Hourglass, CalendarCheck, Droplet, HeartPulse,
  BookCheck, PlayCircle, Download, ArrowRight, FileText
} from 'lucide-vue-next'

import { useClientScreening } from '~/composables/useClientScreening'
import { useClientHistory } from '~/composables/useClientHistory'

definePageMeta({ layout: 'client', title: 'Dashboard' })

// TODO: this whole file uses local mock data — there's no client-facing
// section in mockDatabase.js yet. Move this into the shared mock db (e.g.
// db.clientProfile, db.clientTasks, etc.) once the client-side data model
// is defined, following the same pattern as the RND-side db.patients /
// db.appointments / etc. Screening data specifically now comes from
// useClientScreening() so it stays in sync with the screening form.

// TODO: hardcoded to match the rest of the app's mock "today" date — wire
// this to a real date source once available.
const todayLabel = 'FRIDAY, MAY 15, 2026'

const client = ref({
  firstName: 'Juan',
  programWeek: 6,
  nextConsultDay: 'Friday',
  rnd: { name: 'RND Ivy Hope Alba', initials: 'IA', specialty: 'Diabetes · Renal Nutrition', rating: 4.9, reviews: 38 }
})

// Shared with pre-consultation-screening.vue — submitting that form updates
// these here too, no reload needed.
const { hasLatestScreening, screening, screeningHistory } = useClientScreening()

// Shared with the History page — shows the 3 most recent saved activities
// (screenings, appointments, meal logs) right on the dashboard.
const { historyLog } = useClientHistory()
const recentActivity = computed(() => historyLog.value.slice(0, 3))
function activityDotClass(type) {
  return { screening: 'dot-blue', appointment: 'dot-gold', mealLog: 'dot-green' }[type] || 'dot-green'
}

// Screening-derived stats are null until a screening is submitted, so every
// place that displays them falls back to '—' rather than crashing on
// null.toLocaleString() etc.
const bmiDisplay = computed(() => hasLatestScreening.value ? screening.value.bmi : '—')
const bmiCategoryDisplay = computed(() => hasLatestScreening.value ? screening.value.bmiCategory : 'Not yet screened')
const bmrDisplay = computed(() => hasLatestScreening.value ? screening.value.bmr.toLocaleString() : '—')
const tdeeDisplay = computed(() => hasLatestScreening.value ? screening.value.tdee.toLocaleString() : '—')
const nrsDisplay = computed(() => hasLatestScreening.value ? screening.value.nrs : '—')

const macros = ref({ carbs: 225, carbsPct: 68, protein: 75, proteinPct: 80, fat: 55, fatPct: 50 })

const nextAppointment = ref({ dateShort: 'Jul 4', time: '2:00 PM', detail: 'Video follow-up #3' })

const tabs = [
  { key: 'overview', label: 'Overview', icon: LayoutGrid },
  { key: 'screening', label: 'Health Screening', icon: ShieldCheck },
  { key: 'tasks', label: 'My Tasks', icon: CheckSquare },
  { key: 'logging', label: 'Log Progress', icon: PlusCircle },
  { key: 'summaries', label: 'Consultation Summaries', icon: FileText }
]
const activeTab = ref('overview')

/* ---------- OVERVIEW ---------- */
const weightHistoryRaw = [
  { month: 'Feb', weight: 72.3 }, { month: 'Mar', weight: 71.5 }, { month: 'Apr', weight: 70.5 },
  { month: 'May', weight: 69.0 }, { month: 'Jun', weight: 68.6 }, { month: 'Jul', weight: 68.2 }
]
const weightLostTotal = (weightHistoryRaw[0].weight - weightHistoryRaw[weightHistoryRaw.length - 1].weight).toFixed(1)

const weightHistory = computed(() => {
  const minW = Math.min(...weightHistoryRaw.map(w => w.weight))
  const maxW = Math.max(...weightHistoryRaw.map(w => w.weight))
  const range = maxW - minW || 1
  return weightHistoryRaw.map((w, i) => ({
    month: w.month,
    x: (i / (weightHistoryRaw.length - 1)) * 400,
    y: 80 - ((w.weight - minW) / range) * 56
  }))
})
const chartPoints = computed(() => weightHistory.value.map(p => `${p.x},${p.y}`).join(' '))
const chartFillPoints = computed(() => chartPoints.value + ` 400,90 0,90`)

const clinicalAlerts = ref([
  { title: 'Fasting blood glucose slightly elevated', detail: 'Latest: 112 mg/dL (target <100). Your RND has noted this.', level: 'level-warning', actionLabel: 'Message RND' },
  { title: 'BMI within normal range', detail: '23.4 — consistently Normal for 3 months.', level: 'level-success', actionLabel: null }
])

const todaysReminders = ref([
  { label: 'Hydration (8 glasses — 2L)', icon: Droplet, color: '#2a5a8a' },
  { label: 'Check fasting blood sugar', icon: HeartPulse, color: '#c0392b' },
  { label: "Log today's meals", icon: BookCheck, color: '#1a3a1a' }
])

const labFileName = ref('')
function onLabFileSelected(e) {
  const file = e.target.files?.[0]
  if (file) labFileName.value = file.name
}

/* ---------- MY TASKS ---------- */
const tasks = ref([
  { label: 'Log all meals using the FNRI exchange guide', schedule: 'Daily — ongoing', done: true },
  { label: 'Hydration — 8 glasses of water daily', schedule: 'Daily', done: true },
  { label: 'Check and record fasting blood sugar', schedule: 'Daily — before breakfast', done: false },
  { label: 'Light walk — 30 minutes, 3x per week', schedule: 'Mon / Wed / Fri', done: false },
  { label: 'Read: Managing Carb Cravings (resource article)', schedule: 'One time', done: false }
])
const pendingTaskCount = computed(() => tasks.value.filter(t => !t.done).length)

/* ---------- LOG PROGRESS ---------- */
const mealSlots = ['Breakfast', 'AM Snack', 'Lunch', 'PM Snack', 'Dinner']
const foodLog = ref({ slot: 'Lunch', date: '2026-05-15', time: '12:30', notes: '' })
function saveFoodLog() {
  // TODO: wire up to a real save-food-log API call
  console.log('Saving food log', foodLog.value)
}

const todaysLog = ref([
  { label: 'Breakfast — 7:00 AM', detail: 'Brown rice, fried egg, kangkong', logged: true },
  { label: 'AM Snack — 10:00 AM', detail: 'Banana Saba, low-fat milk', logged: true },
  { label: 'Lunch — pending', detail: '—', logged: false }
])

const vitals = ref({ weight: 68.2, bp: '', glucose: 112 })
function saveVitals() {
  // TODO: wire up to a real save-vitals API call
  console.log('Saving vitals', vitals.value)
}

const notesForRnd = ref('')
function sendNotesToRnd() {
  // TODO: wire up to a real send-note API call
  console.log('Sending note to RND', notesForRnd.value)
  notesForRnd.value = ''
}

/* ---------- CONSULTATION SUMMARIES ---------- */
const consultationSummaries = ref([
  {
    title: 'Follow-up Consultation #2', date: 'June 15, 2026 · 2:00 PM', mode: 'Video',
    notes: 'Fasting blood glucose reduced from 126 to 112 mg/dL. Food diary adherence improved to 5/7 days. Breakfast skipping decreased. RND lowered rice exchanges at dinner by 0.5.',
    hasFullRecord: true
  },
  {
    title: 'Initial Assessment', date: 'May 20, 2026 · 10:00 AM', mode: 'In-Person',
    notes: 'Baseline: HbA1c 6.8%, BMI 23.7 (Normal). PES: Inadequate carb intake management r/t poor dietary knowledge. Started 1,800 kcal diabetic FNRI exchange plan.',
    hasFullRecord: false
  }
])

/* ---------- RESOURCES ---------- */
const resourceSearch = ref('')
const resources = ref([
  { title: 'FNRI Food Exchange List Guide', type: 'PDF', meta: '2 days ago' },
  { title: 'Reading Nutrition Labels', type: 'Video', meta: '6 min' },
  { title: 'Managing Carb Cravings', type: 'Article', meta: '4 min read' }
])
const filteredResources = computed(() =>
  resources.value.filter(r => r.title.toLowerCase().includes(resourceSearch.value.toLowerCase()))
)
function resourceIcon(type) {
  if (type === 'PDF') return FileText
  if (type === 'Video') return PlayCircle
  return ArrowRight
}
</script>

<style scoped>
* { box-sizing: border-box; }

.client-dashboard { font-family: 'Inter', sans-serif; }
.unit { font-size: 0.85rem; font-weight: 400; }

/* WELCOME BANNER */
.welcome-banner {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%);
  border-radius: 16px; padding: 28px 32px; margin-bottom: 20px; color: #fff;
}
.banner-blob { position: absolute; width: 220px; height: 220px; border-radius: 50%; background: rgba(255,255,255,0.05); top: -70px; right: -50px; z-index: 0; }
.banner-content { position: relative; z-index: 1; }
.banner-badge { display: inline-flex; align-items: center; gap: 7px; background: rgba(255,255,255,0.15); border: none; color: #fff; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; padding: 5px 14px; border-radius: 20px; margin-bottom: 14px; }
.banner-badge-dot { width: 5px; height: 5px; border-radius: 50%; background: #D4A017; }
.banner-title { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.5rem; margin: 0 0 8px; color: #fff; }
.banner-sub { font-size: 0.85rem; color: #cfe0d5; margin: 0 0 18px; max-width: 600px; line-height: 1.5; }
.banner-sub strong { color: #fff; }
.banner-actions { display: flex; gap: 10px; }
.banner-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 11px 20px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }

/* STAT CARDS */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 14px; padding: 18px 20px; border: 1px solid #CBD5E1; }
.stat-icon { width: 34px; height: 34px; border-radius: 9px; background: #eef3ec; display: flex; align-items: center; justify-content: center; color: #1e4a26; margin-bottom: 12px; }
.stat-icon.icon-gold { background: #fdf1d6; color: #b8860b; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stat-label { font-size: 0.8rem; color: #6a7a6a; margin: 4px 0 8px; }
.stat-note { font-size: 0.72rem; color: #9aaa9a; margin: 0; }
.stat-note.warn { color: #c0392b; font-weight: 600; }

/* TABS */
.dash-tabs { display: flex; gap: 24px; border-bottom: 1px solid #e5e8e5; margin-bottom: 20px; overflow-x: auto; }
.tab-item { display: flex; align-items: center; gap: 6px; background: none; border: none; cursor: pointer; padding: 10px 2px; font-size: 0.85rem; font-weight: 600; color: #8a9a8a; white-space: nowrap; border-bottom: 2px solid transparent; }
.tab-item.active { color: #1a3a1a; border-bottom-color: #D4A017; }

/* GRID */
.dash-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; align-items: start; }
.dash-grid-single { display: flex; flex-direction: column; gap: 16px; }
.dash-col { display: flex; flex-direction: column; gap: 20px; }
.panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }
.panel-header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.panel-header-row .panel-title { margin: 0; }
.section-eyebrow { display: block; font-size: 0.72rem; letter-spacing: 0.08em; color: #D4A017; font-weight: 700; margin-bottom: 16px; }

/* PILLS */
.status-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-gold { background: #fdf1d6; color: #b8860b; }
.pill-muted { background: #eceeec; color: #8a9a8a; }
.pill-blue { background: #e3ecf7; color: #2a5a8a; }

/* WEIGHT CHART */
.weight-chart { padding: 4px 0; }

/* ALERTS */
.alert-list { display: flex; flex-direction: column; gap: 10px; }
.alert-item { display: flex; align-items: flex-start; gap: 10px; padding: 14px 16px; border-radius: 10px; }
.alert-item.level-warning { background: #faf1de; }
.alert-item.level-success { background: #e6efe0; }
.alert-icon { flex-shrink: 0; margin-top: 1px; color: #b8860b; }
.level-success .alert-icon { color: #3a6b3a; }
.alert-text { flex: 1; }
.alert-name { font-weight: 700; font-size: 0.87rem; color: #2a2a2a; margin: 0 0 3px; }
.alert-detail { font-size: 0.78rem; color: #6a6a6a; margin: 0; }
.alert-action { font-size: 0.78rem; font-weight: 700; color: #b8860b; text-decoration: none; white-space: nowrap; }

/* MACROS */
.macro-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; text-align: center; }
.macro-value { font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.macro-value.gold { color: #b8860b; }
.macro-label { font-size: 0.72rem; color: #8a9a8a; margin: 2px 0 8px; }
.macro-track { height: 6px; background: #eceeec; border-radius: 3px; overflow: hidden; }
.macro-fill { height: 100%; border-radius: 3px; }
.fill-green { background: #1f8f5c; }
.fill-gold { background: #D4A017; }

/* LATEST SCREENING */
.screening-summary-text { font-size: 0.85rem; color: #6a7a6a; margin: 0 0 16px; line-height: 1.5; }

/* RECENT ACTIVITY */
.view-all-link { font-size: 0.78rem; font-weight: 700; color: #b8860b; text-decoration: none; white-space: nowrap; }
.activity-row { display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-top: 1px solid #f0f2f0; }
.activity-row:first-of-type { border-top: none; padding-top: 0; }
.activity-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; margin-top: 6px; display: inline-block; }
.activity-dot.dot-blue { background: #2a5a8a; }
.activity-dot.dot-gold { background: #D4A017; }
.activity-dot.dot-green { background: #1f8f5c; }
.activity-title { font-size: 0.83rem; font-weight: 600; color: #1a3a1a; margin: 0; }
.activity-time { font-size: 0.72rem; color: #9aaa9a; margin: 2px 0 0; }

/* RND CARD */
.rnd-row { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.rnd-avatar { width: 52px; height: 52px; border-radius: 50%; background: #00382a; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.rnd-name { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.rnd-specialty { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; }
.rnd-rating { font-size: 0.78rem; color: #b8860b; font-weight: 600; margin: 2px 0 0; }

/* REMINDERS (overview mini) */
.reminder-list { display: flex; flex-direction: column; gap: 10px; }
.reminder-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 8px; border-left: 3px solid #D4A017; background: #f7f9f7; }
.reminder-label { font-size: 0.85rem; font-weight: 600; color: #2a2a2a; }

/* DROPZONE */
.dropzone { display: flex; flex-direction: column; align-items: center; gap: 6px; background: #eef3ee; border: 1.5px dashed #b8c8b8; border-radius: 10px; padding: 24px 16px; cursor: pointer; text-align: center; }
.dropzone-input { display: none; }
.dropzone-icon { color: #1a5a2a; }
.dropzone-text { font-size: 0.84rem; color: #4a5a4a; }
.dropzone-text strong { color: #1a5a2a; text-decoration: underline; }
.dropzone-hint { font-size: 0.72rem; color: #9aaa9a; }

/* BUTTONS */
.primary-btn { background: #14301a; color: #fff; border: none; border-radius: 8px; padding: 11px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }
.primary-btn.small { display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; font-size: 0.8rem; }
.outline-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 11px 18px; font-weight: 600; font-size: 0.85rem; cursor: pointer; }
.outline-btn.small { padding: 7px 12px; font-size: 0.8rem; display: inline-flex; align-items: center; justify-content: center; }
.full-width { width: 100%; }

/* TABLES */
.table-panel { padding: 0; overflow: hidden; }
.table-panel .panel-title { padding: 22px 22px 0; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th { text-align: left; font-size: 0.7rem; letter-spacing: 0.05em; color: #9aaa9a; font-weight: 700; padding: 16px 16px 10px; }
.data-table td { padding: 12px 16px; border-top: 1px solid #f2f4f2; font-size: 0.85rem; color: #2a2a2a; }
.invoice-id { font-weight: 700; color: #1a3a1a; }
.invoice-amount { font-weight: 700; }

/* INFO BANNER */
.info-banner { display: flex; align-items: center; gap: 8px; background: #eef1f6; border-radius: 8px; padding: 12px 16px; font-size: 0.82rem; color: #3a4a5a; }
.info-icon { color: #2a5a8a; flex-shrink: 0; }
.info-link { color: #2a5a8a; font-weight: 600; text-decoration: none; }

/* SCREENING STATS */
.screening-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; text-align: center; margin-bottom: 20px; }
.screening-value { font-family: 'Playfair Display', serif; font-size: 1.7rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.screening-label { font-size: 0.75rem; color: #8a9a8a; margin: 2px 0 6px; }

/* TASKS */
.task-list { display: flex; flex-direction: column; }
.task-row { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #f0f2f0; cursor: pointer; }
.task-row:last-child { border-bottom: none; }
.task-row input { width: 17px; height: 17px; accent-color: #14301a; cursor: pointer; }
.task-info { flex: 1; }
.task-label { font-size: 0.87rem; font-weight: 600; color: #1a3a1a; margin: 0; }
.task-detail { font-size: 0.76rem; color: #9aaa9a; margin: 2px 0 0; }

/* LOG PROGRESS FORM */
.form-row-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label, .field-label { font-size: 0.78rem; font-weight: 600; color: #4a5a4a; }
.field-label { display: block; margin: 0 0 8px; }
.field input, .field select, textarea, .full-input {
  border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #2a2a2a; width: 100%;
}
textarea { resize: vertical; margin-bottom: 16px; }
.full-input { margin-bottom: 16px; }

.log-list { display: flex; flex-direction: column; }
.log-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 11px 0; border-bottom: 1px solid #f0f2f0; font-size: 0.85rem; }
.log-row:last-child { border-bottom: none; }
.log-label { font-weight: 600; color: #1a3a1a; }
.log-detail { color: #8a9a8a; flex: 1; text-align: right; margin-right: 8px; }

/* SUMMARIES */
.summary-title { font-weight: 700; color: #1a3a1a; margin: 0; }
.summary-meta { font-size: 0.78rem; color: #9aaa9a; margin: 3px 0 0; }
.summary-notes { font-size: 0.85rem; color: #4a5a4a; line-height: 1.55; margin: 14px 0 16px; }
.summary-notes strong { color: #1a3a1a; }

/* RESOURCES */
.search-wrap { position: relative; margin-bottom: 18px; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: #9aaa9a; }
.search-wrap input { width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 14px 11px 38px; font-size: 0.85rem; font-family: inherit; }
.resource-list { display: flex; flex-direction: column; gap: 10px; }
.resource-row { display: flex; align-items: center; gap: 14px; padding: 12px; background: #fafbfa; border-radius: 10px; }
.resource-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.resource-icon.icon-pdf { background: rgba(192,57,43,.1); color: #c0392b; }
.resource-icon.icon-video { background: rgba(47,111,168,.1); color: #2f6fa8; }
.resource-icon.icon-article { background: #eef3ec; color: #1e4a26; }
.resource-info { flex: 1; }
.resource-title { font-size: 0.88rem; font-weight: 600; color: #1a3a1a; margin: 0; }
.resource-meta { font-size: 0.76rem; color: #9aaa9a; margin: 2px 0 0; }

/* REMINDERS FULL */
.reminder-full-list { display: flex; flex-direction: column; gap: 10px; }
.reminder-full-item { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border-radius: 10px; border-left: 3px solid #D4A017; background: #f7f9f7; }
.reminder-full-icon { color: #b8860b; flex-shrink: 0; }
.reminder-full-info { flex: 1; }
.reminder-full-label { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.reminder-full-schedule { font-size: 0.76rem; color: #9aaa9a; margin: 2px 0 0; }

@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-grid { grid-template-columns: 1fr; }
  .form-row-3, .macro-grid, .screening-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>