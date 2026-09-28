<template>
  <div class="client-dashboard">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-else-if="isLoading" class="placeholder-text">Loading…</p>

    <template v-else>
      <!-- WELCOME BANNER -->
      <section class="welcome-banner">
        <div class="banner-blob"></div>
        <div class="banner-content">
          <span class="banner-badge"><span class="banner-badge-dot"></span> {{ todayLabel }}</span>
          <h1 class="banner-title">Hi {{ auth.user?.first_name }}, welcome back.</h1>
          <p class="banner-sub">{{ welcomeSubtext }}</p>
          <div class="banner-actions">
            <button v-if="upcomingAppointment" class="banner-btn" @click="navigateTo('/appointments')">View Appointment</button>
            <button v-else class="banner-btn" @click="navigateTo('/find-rnd')">Find an RND</button>
          </div>
        </div>
      </section>

      <!-- STAT CARDS -->
      <section class="stat-grid">
        <div class="stat-card">
          <div class="stat-icon"><Activity :size="17" /></div>
          <p class="stat-value">{{ screening?.bmi ?? '—' }}</p>
          <p class="stat-label">Current BMI</p>
          <span class="status-pill" :class="screening ? bmiBadgeClass : 'pill-muted'">{{ screening?.bmi_category ?? 'Not yet screened' }}</span>
        </div>
        <div class="stat-card">
          <div class="stat-icon icon-gold"><Flame :size="17" /></div>
          <p class="stat-value">{{ screening?.tdee_kcal ? Math.round(screening.tdee_kcal) : '—' }} <span v-if="screening?.tdee_kcal" class="unit">kcal</span></p>
          <p class="stat-label">Daily Target (TDEE)</p>
          <p class="stat-note">Protein {{ macros.protein }}g · Carbs {{ macros.carbs }}g · Fat {{ macros.fat }}g</p>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><ClipboardCheck :size="17" /></div>
          <p class="stat-value">{{ screening?.nrs_score ?? '—' }}</p>
          <p class="stat-label">NRS-2002 Score</p>
          <span class="status-pill" :class="screening ? nrsBadgeClass : 'pill-muted'">{{ screening ? nrsRiskLabel : 'Pending screening' }}</span>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><CalendarDays :size="17" /></div>
          <p class="stat-value">{{ upcomingAppointment ? formatShortDate(upcomingAppointment.scheduled_at) : '—' }}</p>
          <p class="stat-label">Next Appointment</p>
          <p v-if="upcomingAppointment" class="stat-note">{{ formatTime(upcomingAppointment.scheduled_at) }} · {{ upcomingAppointment.type.replace('_', ' ') }}</p>
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
              <span v-if="weightHistory.length > 1" class="status-pill pill-green">{{ weightDeltaLabel }}</span>
            </div>
            <div v-if="weightHistory.length" class="weight-chart">
              <svg viewBox="0 0 460 110" width="100%" style="overflow: visible;">
                <defs><linearGradient id="wGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1a3a1a" stop-opacity=".12" /><stop offset="100%" stop-color="#1a3a1a" stop-opacity="0" /></linearGradient></defs>
                <g transform="translate(20,8)">
                  <polyline :points="chartPoints" stroke="#1a3a1a" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
                  <polygon :points="chartFillPoints" fill="url(#wGrad)" />
                  <circle v-for="(p, i) in chartCoords" :key="i" :cx="p.x" :cy="p.y" :r="i === chartCoords.length - 1 ? 4 : 3.5" :fill="i === chartCoords.length - 1 ? '#D4A017' : '#1a3a1a'" />
                  <text v-for="(p, i) in chartCoords" :key="'l' + i" :x="p.x - (i === chartCoords.length - 1 ? 10 : 4)" y="104" font-size="9" :fill="i === chartCoords.length - 1 ? '#D4A017' : '#8aaa8a'" :font-weight="i === chartCoords.length - 1 ? 700 : 400" font-family="Inter, sans-serif">{{ p.label }}</text>
                </g>
              </svg>
            </div>
            <p v-else class="empty-note">No weight history yet — this fills in as your RND logs progress at each consultation.</p>
          </div>

          <div class="panel">
            <h3 class="panel-title">Clinical Alerts</h3>
            <!-- TODO: no clinical-alerts endpoint yet — derive real ones from
                 screening/progress data once that's available server-side. -->
            <p v-if="!clinicalAlerts.length" class="empty-note">No alerts right now.</p>
            <div v-else class="alert-list">
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
            <div v-if="screening?.tdee_kcal" class="macro-grid">
              <div class="macro-item">
                <p class="macro-value">{{ macros.carbs }}g</p>
                <p class="macro-label">Carbohydrates</p>
                <div class="macro-track"><div class="macro-fill fill-green" style="width: 100%"></div></div>
              </div>
              <div class="macro-item">
                <p class="macro-value gold">{{ macros.protein }}g</p>
                <p class="macro-label">Protein</p>
                <div class="macro-track"><div class="macro-fill fill-gold" style="width: 100%"></div></div>
              </div>
              <div class="macro-item">
                <p class="macro-value">{{ macros.fat }}g</p>
                <p class="macro-label">Fat</p>
                <div class="macro-track"><div class="macro-fill fill-green" style="width: 100%"></div></div>
              </div>
            </div>
            <p v-else class="empty-note">Complete your screening to see daily targets.</p>
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
            <template v-if="screening">
              <p class="screening-summary-text">
                Recorded {{ formatShortDate(screening.created_at) }} — BMI {{ screening.bmi }} ({{ screening.bmi_category }}), NRS-2002 {{ screening.nrs_score }}.
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
            <div v-if="activeRelationship" class="rnd-row">
              <div class="rnd-avatar" :style="{ background: colorForId(activeRelationship.rnd.id) }">{{ initialsFor(activeRelationship.rnd) }}</div>
              <div>
                <p class="rnd-name">RND {{ activeRelationship.rnd.first_name }} {{ activeRelationship.rnd.last_name }}</p>
                <p v-if="rndProfile?.specialization" class="rnd-specialty">{{ rndProfile.specialization }}</p>
                <p v-if="rndProfile?.average_rating" class="rnd-rating">★ {{ Number(rndProfile.average_rating).toFixed(1) }} ({{ rndProfile.review_count }} reviews)</p>
              </div>
            </div>
            <p v-else class="empty-note">No active RND yet.</p>
            <button class="outline-btn full-width" @click="navigateTo(activeRelationship ? '/messages' : '/find-rnd')">
              {{ activeRelationship ? 'Send a Message' : 'Find an RND' }}
            </button>
          </div>

          <div class="panel">
            <h3 class="panel-title">Today's Reminders</h3>
            <!-- TODO: mock/local only — Reminder has a DB model but no
                 serializer/view/endpoint yet. -->
            <div v-if="!todaysReminders.length" class="empty-note">No reminders set.</div>
            <div v-else class="reminder-list">
              <div v-for="r in todaysReminders" :key="r.label" class="reminder-item">
                <component :is="r.icon" :size="16" :style="{ color: r.color }" />
                <span class="reminder-label">{{ r.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ============ HEALTH SCREENING ============ -->
      <section v-if="activeTab === 'screening'" class="dash-grid-single">
        <div class="panel" v-if="screening">
          <span class="section-eyebrow">PRE-CONSULTATION SCREENING RECORD</span>
          <div class="screening-stats">
            <div class="screening-stat">
              <p class="screening-value">{{ screening.bmi }}</p>
              <p class="screening-label">BMI</p>
              <span class="status-pill" :class="bmiBadgeClass">{{ screening.bmi_category }}</span>
            </div>
            <div class="screening-stat">
              <p class="screening-value">{{ screening.bmr_kcal ? Math.round(screening.bmr_kcal).toLocaleString() : '—' }}</p>
              <p class="screening-label">BMR (kcal)</p>
            </div>
            <div class="screening-stat">
              <p class="screening-value">{{ screening.tdee_kcal ? Math.round(screening.tdee_kcal).toLocaleString() : '—' }}</p>
              <p class="screening-label">TDEE (kcal)</p>
            </div>
            <div class="screening-stat">
              <p class="screening-value">{{ screening.nrs_score ?? '—' }}</p>
              <p class="screening-label">NRS-2002 Score</p>
              <span v-if="screening.nrs_risk" class="status-pill" :class="nrsBadgeClass">{{ nrsRiskLabel }}</span>
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

        <!-- TODO: no screening-history list endpoint yet (only /client/screening/latest/
             and a per-appointment detail exist) — wire this up once one is added. -->
      </section>

      <!-- ============ MY TASKS ============ -->
      <section v-if="activeTab === 'tasks'" class="dash-grid-single">
        <!-- TODO: mock/local only — no assigned-tasks concept/endpoint on the backend yet. -->
        <div class="panel">
          <div class="panel-header-row">
            <h3 class="panel-title">Tasks Assigned{{ activeRelationship ? ` by RND ${activeRelationship.rnd.first_name} ${activeRelationship.rnd.last_name}` : '' }}</h3>
            <span class="status-pill pill-gold">{{ pendingTaskCount }} pending</span>
          </div>
          <p v-if="!tasks.length" class="empty-note">No tasks assigned yet.</p>
          <div v-else class="task-list">
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
            <span class="section-eyebrow">ACTUAL FOOD INTAKE</span>
            <p class="empty-note">Meal-by-meal adherence logging (with photo, time, and status per meal) now lives on the <NuxtLink to="/meal-plan-view" class="inline-link">My Meal Plan</NuxtLink> page, next to what your RND actually prescribed for each meal.</p>
          </div>
        </div>

        <div class="dash-col">
          <div class="panel">
            <!-- TODO: mock/local only — no vitals-log endpoint yet. -->
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
            <button class="outline-btn full-width" @click="sendNotesToRnd">Send Notes</button>
          </div>
        </div>
      </section>

      <!-- ============ CONSULTATION SUMMARIES ============ -->
      <section v-if="activeTab === 'summaries'" class="dash-grid-single">
        <!-- TODO: mock/local only — no consultation-summary endpoint yet;
             real NCP records exist (clinical/models.py NcpRecord) but aren't
             surfaced to the client role. -->
        <p v-if="!consultationSummaries.length" class="empty-note">No consultation summaries yet.</p>
        <div v-for="s in consultationSummaries" :key="s.title" class="panel summary-card">
          <div class="panel-header-row">
            <div>
              <p class="summary-title">{{ s.title }}</p>
              <p class="summary-meta">{{ s.date }} · {{ s.mode }}</p>
            </div>
            <span class="status-pill pill-muted">Completed</span>
          </div>
          <p class="summary-notes"><strong>Key Notes:</strong> {{ s.notes }}</p>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  Activity, Flame, ClipboardCheck, CalendarDays, LayoutGrid, ShieldCheck, CheckSquare,
  PlusCircle, FileText, AlertTriangle, CheckCircle, Info, Droplet, HeartPulse, BookCheck,
} from 'lucide-vue-next'
import { useClientHistory } from '~/composables/useClientHistory'

definePageMeta({ layout: 'dashboard', title: 'Dashboard' })

const auth = useAuthStore()
const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const appointments = ref([])
const relationships = ref([])
const rndProfile = ref(null)
const screening = ref(null)

const AVATAR_COLORS = ['#1e4a26', '#3a6b3a', '#D4A017', '#6a8a6a', '#8a6a3a']
function colorForId(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}
function initialsFor(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
}

const todayLabel = computed(() => new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).toUpperCase())

const activeRelationship = computed(() => relationships.value[0] || null)

const upcomingAppointment = computed(() => {
  const upcoming = appointments.value
    .filter(a => ['pending', 'confirmed'].includes(a.status) && new Date(a.scheduled_at) > new Date())
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
  return upcoming[0] || null
})

const welcomeSubtext = computed(() => {
  if (upcomingAppointment.value && activeRelationship.value) {
    return `Next consultation with RND ${activeRelationship.value.rnd.first_name} ${activeRelationship.value.rnd.last_name} on ${formatShortDate(upcomingAppointment.value.scheduled_at)}. Your BMI is in the ${screening.value?.bmi_category ?? 'not yet screened'} range.`
  }
  if (activeRelationship.value) {
    return `You're working with RND ${activeRelationship.value.rnd.first_name} ${activeRelationship.value.rnd.last_name}.`
  }
  return "You haven't connected with an RND yet."
})

const nrsRiskLabel = computed(() => ({ no_risk: 'No Risk', at_risk: 'At Risk', high_risk: 'High Risk' }[screening.value?.nrs_risk] || screening.value?.nrs_risk))
const nrsBadgeClass = computed(() => ({ no_risk: 'badge-success', at_risk: 'badge-warning', high_risk: 'badge-danger' }[screening.value?.nrs_risk] || ''))
const bmiBadgeClass = computed(() => {
  const cat = (screening.value?.bmi_category || '').toLowerCase()
  if (cat.includes('normal')) return 'badge-success'
  if (cat.includes('underweight')) return 'badge-info'
  return 'badge-warning'
})

function formatShortDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}

// TODO: TDEE-based macro split is a placeholder ratio (40/30/30-ish),
// not a real RND-assigned macro plan — no such field/endpoint exists yet.
const macros = computed(() => {
  const tdee = screening.value?.tdee_kcal
  if (!tdee) return { carbs: '—', protein: '—', fat: '—' }
  return {
    carbs: Math.round((tdee * 0.5) / 4),
    protein: Math.round((tdee * 0.2) / 4),
    fat: Math.round((tdee * 0.3) / 9),
  }
})

const tabs = [
  { key: 'overview', label: 'Overview', icon: LayoutGrid },
  { key: 'screening', label: 'Health Screening', icon: ShieldCheck },
  { key: 'tasks', label: 'My Tasks', icon: CheckSquare },
  { key: 'logging', label: 'Log Progress', icon: PlusCircle },
  { key: 'summaries', label: 'Consultation Summaries', icon: FileText },
]
const activeTab = ref('overview')

/* ---------- OVERVIEW: weight chart ---------- */
// TODO: no weight-history endpoint yet — ProgressRecord exists on the
// backend (clinical/models.py) but isn't surfaced here. Empty until wired.
const weightHistory = ref([])
const weightDeltaLabel = computed(() => {
  if (weightHistory.value.length < 2) return ''
  const delta = weightHistory.value[0].weight - weightHistory.value[weightHistory.value.length - 1].weight
  return `${delta >= 0 ? '↓' : '↑'} ${Math.abs(delta).toFixed(1)} kg total`
})
const chartCoords = computed(() => {
  if (!weightHistory.value.length) return []
  const weights = weightHistory.value.map(w => w.weight)
  const minW = Math.min(...weights)
  const maxW = Math.max(...weights)
  const range = maxW - minW || 1
  return weightHistory.value.map((w, i) => ({
    label: w.label,
    x: weightHistory.value.length > 1 ? (i / (weightHistory.value.length - 1)) * 400 : 0,
    y: 80 - ((w.weight - minW) / range) * 56,
  }))
})
const chartPoints = computed(() => chartCoords.value.map(p => `${p.x},${p.y}`).join(' '))
const chartFillPoints = computed(() => chartPoints.value + ` 400,90 0,90`)

// TODO: mock/local only — no clinical-alerts endpoint yet.
const clinicalAlerts = ref([])

/* ---------- Recent activity (shared with the History page) ---------- */
const { historyLog } = useClientHistory()
const recentActivity = computed(() => historyLog.value.slice(0, 3))
function activityDotClass(type) {
  return { screening: 'dot-blue', appointment: 'dot-gold', mealLog: 'dot-green' }[type] || 'dot-green'
}

// TODO: mock/local only — Reminder has a DB model but no endpoint yet.
const todaysReminders = ref([
  { label: 'Hydration (8 glasses — 2L)', icon: Droplet, color: '#2a5a8a' },
  { label: 'Check fasting blood sugar', icon: HeartPulse, color: '#c0392b' },
  { label: "Log today's meals", icon: BookCheck, color: '#1a3a1a' },
])

/* ---------- My Tasks (mock/local only) ---------- */
const tasks = ref([])
const pendingTaskCount = computed(() => tasks.value.filter(t => !t.done).length)

/* ---------- Log Progress (mock/local only) ---------- */
const vitals = ref({ weight: null, bp: '', glucose: null })
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

/* ---------- Consultation Summaries (mock/local only) ---------- */
const consultationSummaries = ref([])

async function loadDashboard() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [appts, rels, latestScreening] = await Promise.all([
      get('/client/appointments/'),
      get('/client/relationships/'),
      get('/client/screening/latest/').catch(() => null),
    ])
    appointments.value = appts
    relationships.value = rels
    screening.value = latestScreening

    if (rels[0]) {
      rndProfile.value = await get(`/client/rnds/${rels[0].rnd.id}/`).catch(() => null)
    }
  } catch {
    errorMessage.value = 'Could not load your dashboard. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadDashboard)
</script>

<style scoped>
* { box-sizing: border-box; }

.client-dashboard { font-family: 'Inter', sans-serif; }
.unit { font-size: 0.85rem; font-weight: 400; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }
.empty-note { font-size: 0.85rem; color: #9aaa9a; margin: 0; }
.inline-link { color: #1a5a2a; font-weight: 600; text-decoration: underline; }

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
.badge-success { background: #e6efe0; color: #3a6b3a; }
.badge-warning { background: #faead0; color: #b8860b; }
.badge-info { background: #e3edf7; color: #2f6fa8; }
.badge-danger { background: #fdecec; color: #a12525; }

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
.rnd-avatar { width: 52px; height: 52px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.rnd-name { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.rnd-specialty { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; }
.rnd-rating { font-size: 0.78rem; color: #b8860b; font-weight: 600; margin: 2px 0 0; }

/* REMINDERS (overview mini) */
.reminder-list { display: flex; flex-direction: column; gap: 10px; }
.reminder-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-radius: 8px; border-left: 3px solid #D4A017; background: #f7f9f7; }
.reminder-label { font-size: 0.85rem; font-weight: 600; color: #2a2a2a; }

/* BUTTONS */
.primary-btn { background: #14301a; color: #fff; border: none; border-radius: 8px; padding: 11px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }
.outline-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 11px 18px; font-weight: 600; font-size: 0.85rem; cursor: pointer; }
.full-width { width: 100%; }

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
.summary-notes { font-size: 0.85rem; color: #4a5a4a; line-height: 1.55; margin: 14px 0 0; }
.summary-notes strong { color: #1a3a1a; }

@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-grid { grid-template-columns: 1fr; }
  .form-row-3, .macro-grid, .screening-stats { grid-template-columns: repeat(2, 1fr); }
}
</style>
