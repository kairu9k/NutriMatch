<template>
  <div class="rnd-dashboard">
    <!-- WELCOME BANNER -->
    <section class="welcome-banner">
      <div class="banner-text">
        <span class="banner-eyebrow">— WELCOME BACK</span>
        <h2 class="banner-title">Good Day, {{ rnd?.name || 'RND' }}.</h2>
        <p class="banner-sub">
          {{ appointments.length }} consultations today · {{ draftRecords.length }} NCP records awaiting finalization · {{ patientRequests.length }} new patient requests
        </p>
      </div>
      <button class="banner-btn">View Today's Schedule</button>
    </section>

    <!-- STAT CARDS -->
    <section class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon"><Users :size="18" /></div>
        <p class="stat-value">{{ patients.length }}</p>
        <p class="stat-label">Active Patients</p>
        <p v-if="patients.length" class="stat-delta up">↑ 3 new this month</p>
        <p v-else class="stat-delta neutral">No patients yet</p>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><CalendarCheck :size="18" /></div>
        <p class="stat-value">{{ todaysSchedule.length }}</p>
        <p class="stat-label">Today's Sessions</p>
        <p v-if="todaysSchedule.length" class="stat-delta neutral">🕐 Next at {{ todaysSchedule[0].time }}</p>
        <p v-else class="stat-delta neutral">Nothing scheduled</p>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><Trophy :size="18" /></div>
        <p class="stat-value">{{ earningsSummary.goalAchievement || '—' }}%</p>
        <p class="stat-label">Avg. Goal Achievement</p>
        <p class="stat-delta neutral">No data yet</p>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><Landmark :size="18" /></div>
        <p class="stat-value">₱{{ earningsSummary.thisMonthNet.toLocaleString() }}</p>
        <p class="stat-label">Earnings (This Month)</p>
        <p class="stat-delta neutral">{{ earningsSummary.billableSessionsThisMonth }} billable sessions</p>
      </div>
    </section>

    <!-- TABS -->
    <nav class="dash-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.label"
        class="tab-item"
        :class="{ active: activeTab === tab.label }"
        @click="activeTab = tab.label"
      >
        <component :is="tab.icon" :size="15" />
        {{ tab.label }}
      </button>
    </nav>

    <!-- ============ OVERVIEW TAB ============ -->
    <section v-if="activeTab === 'Overview'" class="dash-grid">
      <div class="dash-col">
        <div class="panel">
          <h3 class="panel-title">Clinical Alerts</h3>
          <div v-if="clinicalAlerts.length" class="alert-list">
            <div v-for="alert in clinicalAlerts" :key="alert.name" class="alert-item" :class="alert.level">
              <div class="alert-text">
                <p class="alert-name">{{ alert.name }} — {{ alert.issue }}</p>
                <p class="alert-detail">{{ alert.detail }}</p>
              </div>
              <NuxtLink :to="alert.link" class="alert-action">{{ alert.actionLabel }} →</NuxtLink>
            </div>
          </div>
          <p v-else class="empty-text">No clinical alerts right now.</p>
        </div>

        <div class="panel">
          <h3 class="panel-title">Patient Health Outcomes (Avg. Progress)</h3>
          <div v-if="healthOutcomes.length" class="outcomes-grid">
            <div v-for="o in healthOutcomes" :key="o.label" class="outcome-item">
              <p class="outcome-value" :class="o.color">{{ o.value }}</p>
              <p class="outcome-label">{{ o.label }}</p>
            </div>
          </div>
          <p v-else class="empty-text">Not enough data yet.</p>
        </div>
      </div>

      <div class="dash-col">
        <div class="panel">
          <h3 class="panel-title">Today's Schedule</h3>
          <div v-if="todaysSchedule.length" class="schedule-list">
            <div v-for="s in todaysSchedule" :key="s.name" class="schedule-item">
              <p class="schedule-time">{{ s.time }}</p>
              <p class="schedule-name">{{ s.name }}</p>
              <p class="schedule-detail">{{ s.detail }}</p>
            </div>
          </div>
          <p v-else class="empty-text">No appointments today.</p>
        </div>

        <div class="panel">
          <h3 class="panel-title">New Patient Requests</h3>
          <div v-if="patientRequests.length" class="request-list">
            <div v-for="r in patientRequests" :key="r.name" class="request-item">
              <div class="request-avatar">{{ r.initials }}</div>
              <div class="request-info">
                <p class="request-name">{{ r.name }}</p>
                <p class="request-time">{{ r.requestedAt }}</p>
              </div>
              <button class="accept-btn" @click="acceptRequest(r)">Accept</button>
            </div>
          </div>
          <p v-else class="empty-text">No pending requests.</p>
        </div>

        <div class="panel">
          <h3 class="panel-title">Earnings Summary</h3>
          <div class="earnings-row">
            <span class="earnings-label">This month (net)</span>
            <span class="earnings-amount">₱{{ earningsSummary.thisMonthNet.toLocaleString() }}</span>
          </div>
          <div class="earnings-bar">
            <div class="earnings-fill" :style="{ width: earningsProgress + '%' }"></div>
          </div>
          <button class="view-earnings-btn" @click="navigateTo('/earnings')">View Earnings Report</button>
        </div>
      </div>
    </section>

    <!-- ============ PATIENT PANEL TAB ============ -->
    <section v-if="activeTab === 'Patient Panel'" class="patient-panel">
      <div class="panel-toolbar">
        <div class="search-box-wide">
          <Search :size="16" class="search-icon" />
          <input v-model="patientSearch" type="text" placeholder="Search patients..." />
        </div>
        <select v-model="statusFilter" class="status-select">
          <option value="All Status">All Status</option>
          <option value="Active">Active</option>
          <option value="Inactive">Inactive</option>
        </select>
      </div>

      <div v-if="filteredPatients.length" class="patient-table-wrap">
        <table class="patient-table">
          <thead>
            <tr>
              <th>PATIENT</th><th>CONDITION</th><th>STATUS</th><th>LAST VISIT</th><th>NCP PHASE</th><th>CLINICAL ALERT</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in filteredPatients" :key="p.name" :class="{ 'row-alert': p.alert }">
              <td class="patient-cell">
                <div class="patient-avatar" :style="{ background: p.avatarColor }">{{ p.initials }}</div>
                <span class="patient-name">{{ p.name }}</span>
              </td>
              <td>{{ p.condition }}</td>
              <td><span class="status-pill">{{ p.status }}</span></td>
              <td>{{ p.lastVisit || '—' }}</td>
              <td>{{ p.ncpPhase }}</td>
              <td>
                <span v-if="p.alert" class="alert-pill" :class="p.alertLevel">{{ p.alert }}</span>
                <span v-else class="no-alert">—</span>
              </td>
              <td>
                <button class="chart-btn" :class="{ 'review-btn': p.alert }" @click="navigateTo(`/ncp-records?patient=${p.name}`)">
                  {{ p.alert ? 'Review' : 'Chart' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty-text">No patients match your search.</p>

      <button v-if="patients.length" class="view-all-btn" @click="navigateTo('/my-patients')">
        View All {{ patients.length }} Patients →
      </button>
    </section>

    <!-- ============ APPOINTMENTS TAB ============ -->
    <section v-if="activeTab === 'Appointments'" class="appointments-panel">
      <div v-if="appointments.length">
        <div v-for="appt in appointments" :key="appt.name + appt.detail" class="appt-card">
          <div class="appt-date">
            <span class="appt-day">{{ appt.day }}</span>
            <span class="appt-month">{{ appt.month }}</span>
          </div>
          <div class="appt-avatar" :style="{ background: appt.avatarColor }">{{ appt.initials }}</div>
          <div class="appt-info">
            <p class="appt-name">
              {{ appt.name }}
              <span class="appt-status-pill" :class="appt.statusClass">{{ appt.statusLabel }}</span>
            </p>
            <p class="appt-detail">{{ appt.detail }}</p>
          </div>
          <div class="appt-action">
            <button v-if="appt.canStart" class="start-session-btn" @click="startSession(appt)">Start Session</button>
            <span v-else-if="appt.note" class="appt-note">{{ appt.note }}</span>
          </div>
        </div>
      </div>
      <p v-else class="empty-text">No appointments yet.</p>

      <button v-if="appointments.length" class="view-all-btn" @click="navigateTo('/appointments')">View All Appointments →</button>
    </section>

    <!-- ============ NCP DOCUMENTATION TAB ============ -->
    <section v-if="activeTab === 'NCP Documentation'" class="ncp-panel">
      <div class="dash-grid">
        <div class="panel">
          <h3 class="panel-title">Draft NCP Records</h3>
          <div v-if="draftRecords.length" class="draft-list">
            <div v-for="d in draftRecords" :key="d.name" class="draft-item">
              <div class="draft-avatar" :style="{ background: d.avatarColor }">{{ d.initials }}</div>
              <div class="draft-info">
                <p class="draft-name">{{ d.name }}</p>
                <p class="draft-detail">{{ d.phase }} — {{ d.status }}</p>
              </div>
              <button class="resume-btn" @click="navigateTo(`/ncp-records?patient=${d.name}`)">Resume</button>
            </div>
          </div>
          <p v-else class="empty-text">No drafts in progress.</p>
        </div>

        <div class="panel">
          <h3 class="panel-title">Start New NCP Record</h3>
          <label class="field-label">Select Patient</label>
          <select v-model="selectedPatientForNcp" class="field-select">
            <option value="">Select active patient...</option>
            <option v-for="p in patients" :key="p.name" :value="p.name">{{ p.name }}</option>
          </select>
          <button class="begin-assessment-btn" @click="beginNcpAssessment">Begin NCP Assessment →</button>
        </div>
      </div>

      <div class="ncp-footnote">
        <Info :size="15" class="footnote-icon" />
        4-phase Nutrition Care Process: <strong>Assessment → PES Diagnosis → Intervention → Monitoring &amp; Evaluation.</strong>
        Finalized records are immutable per RA 10173.
      </div>
    </section>

    <!-- ============ MEAL PLANNING TAB ============ -->
    <section v-if="activeTab === 'Meal Planning'" class="dash-grid">
      <div class="panel">
        <h3 class="panel-title">Active Meal Plans</h3>
        <div v-if="mealPlans.length" class="mealplan-list">
          <div v-for="m in mealPlans" :key="m.name" class="mealplan-item">
            <div class="mealplan-avatar" :style="{ background: m.avatarColor }">{{ m.initials }}</div>
            <div class="mealplan-info">
              <p class="mealplan-name">{{ m.name }}</p>
              <p class="mealplan-detail">{{ m.diet }} · {{ m.kcal }} kcal · {{ m.status }}</p>
            </div>
            <button class="edit-btn" @click="navigateTo(`/meal-planning?patient=${m.name}`)">Edit</button>
          </div>
        </div>
        <p v-else class="empty-text">No active meal plans.</p>
      </div>

      <div class="panel food-exchange-panel">
        <h3 class="panel-title">FNRI Food Exchange Search</h3>
        <p class="food-exchange-desc">
          Search the 550-item FNRI Food Exchange List (4th Ed.) and USDA FoodData Central to build evidence-based meal plans.
        </p>
        <button class="open-search-btn" @click="navigateTo('/food-exchange-search')">
          <Search :size="15" /> Open Food Exchange Search →
        </button>
      </div>
    </section>

    <!-- ============ RESOURCES LIBRARY TAB ============ -->
    <section v-if="activeTab === 'Resources Library'" class="resources-panel">
      <div class="resources-header">
        <h3 class="panel-title">Your Resources Library</h3>
        <button class="upload-btn" @click="uploadResource"><Plus :size="15" /> Upload Resource</button>
      </div>

      <div v-if="resources.length" class="resource-list">
        <div v-for="r in resources" :key="r.title" class="resource-item">
          <div class="resource-icon" :class="`icon-${r.iconType}`">
            <component :is="resourceIcon(r.iconType)" :size="18" />
          </div>
          <div class="resource-info">
            <p class="resource-title">{{ r.title }}</p>
            <p class="resource-detail">{{ r.detail }}</p>
          </div>
          <span class="status-pill">{{ r.status }}</span>
        </div>
      </div>
      <p v-else class="empty-text">No resources uploaded yet.</p>

      <button v-if="resources.length" class="view-all-btn" @click="navigateTo('/resource-library')">Manage All Resources →</button>
    </section>

    <!-- ============ EARNINGS & BILLING TAB ============ -->
    <section v-if="activeTab === 'Earnings & Billing'" class="earnings-panel">
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-icon"><Eye :size="18" /></div>
          <p class="stat-value">₱{{ earningsSummary.gross.toLocaleString() }}</p>
          <p class="stat-label">Gross This Month</p>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><Percent :size="18" /></div>
          <p class="stat-value">₱{{ earningsSummary.commission.toLocaleString() }}</p>
          <p class="stat-label">Commission (10%)</p>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><Wallet :size="18" /></div>
          <p class="stat-value">₱{{ earningsSummary.net.toLocaleString() }}</p>
          <p class="stat-label">Net Earnings</p>
        </div>
        <div class="stat-card">
          <div class="stat-icon pending-icon"><Hourglass :size="18" /></div>
          <p class="stat-value">₱{{ earningsSummary.pending.toLocaleString() }}</p>
          <p class="stat-label">Pending</p>
        </div>
      </div>

      <div v-if="invoices.length" class="patient-table-wrap invoice-table-wrap">
        <table class="patient-table">
          <thead>
            <tr><th>INVOICE</th><th>PATIENT</th><th>DATE</th><th>GROSS</th><th>COMMISSION</th><th>NET</th><th>STATUS</th></tr>
          </thead>
          <tbody>
            <tr v-for="inv in invoices" :key="inv.id">
              <td class="invoice-id">{{ inv.id }}</td>
              <td>{{ inv.patient }}</td>
              <td>{{ inv.date }}</td>
              <td>₱{{ inv.gross }}</td>
              <td class="muted">₱{{ inv.commission }}</td>
              <td class="invoice-net">₱{{ inv.net }}</td>
              <td><span class="status-pill" :class="{ 'pending-pill': inv.status === 'Pending' }">{{ inv.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty-text">No invoices yet.</p>

      <button v-if="invoices.length" class="view-all-btn" @click="navigateTo('/earnings')">Full Earnings Report →</button>
    </section>

    <!-- ============ SETTINGS TAB ============ -->
    <section v-if="activeTab === 'Settings'" class="dash-grid">
      <div class="panel">
        <span class="settings-eyebrow">— PUBLIC PROFILE</span>

        <label class="field-label">Specialization</label>
        <input v-model="settings.specialization" type="text" class="field-input" />

        <label class="field-label">Consultation Fee (₱)</label>
        <input v-model="settings.fee" type="text" class="field-input" />

        <div class="toggle-row">
          <span class="field-label toggle-label">Accepting new clients</span>
          <label class="switch">
            <input type="checkbox" v-model="settings.acceptingClients" />
            <span class="slider"></span>
          </label>
        </div>

        <button class="save-btn" @click="saveSettings">Save Changes</button>
      </div>

      <div class="panel">
        <span class="settings-eyebrow">— NOTIFICATIONS</span>

        <div class="toggle-row" v-for="n in notifications" :key="n.key">
          <span class="field-label toggle-label">{{ n.label }}</span>
          <label class="switch">
            <input type="checkbox" v-model="n.enabled" />
            <span class="slider"></span>
          </label>
        </div>

        <button class="view-earnings-btn" @click="navigateTo('/profile-settings')">Full Profile Settings →</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import {
  Users, CalendarCheck, Trophy, Landmark,
  LayoutGrid, UserCircle2, CalendarDays, FileBarChart2,
  Compass, BookOpen, CreditCard, Settings as SettingsIcon,
  Search, Info, Plus, FileText, PlayCircle, FileEdit,
  Eye, Percent, Wallet, Hourglass
} from 'lucide-vue-next'

// ---- ALL DATA COMES FROM THE MOCK "DATABASE" — nothing hardcoded here ----
import { db } from '~/mock/mockDatabase'

definePageMeta({ layout: 'dashboard', title: 'Dashboard' })

const rnd = db.getCurrentUser('rnd')



const activeTab = ref('Overview')

const tabs = [
  { label: 'Overview', icon: LayoutGrid },
  { label: 'Patient Panel', icon: UserCircle2 },
  { label: 'Appointments', icon: CalendarDays },
  { label: 'NCP Documentation', icon: FileBarChart2 },
  { label: 'Meal Planning', icon: Compass },
  { label: 'Resources Library', icon: BookOpen },
  { label: 'Earnings & Billing', icon: CreditCard },
  { label: 'Settings', icon: SettingsIcon }
]

// Pulled straight from the mock db — swap these lines for real API calls later
const patients = ref(db.patients)
const patientRequests = ref(db.patientRequests)
const appointments = ref(db.appointments)
const todaysSchedule = ref(db.todaysSchedule)
const draftRecords = ref(db.draftRecords)
const healthOutcomes = ref(db.healthOutcomes)
const clinicalAlerts = ref(db.clinicalAlerts)
const mealPlans = ref(db.mealPlans)
const resources = ref(db.resources)
const earningsSummary = ref(db.earningsSummary)
const invoices = ref(db.invoices)
const settings = ref({ ...db.rndSettings })
const notifications = ref(db.notificationPrefs.map(n => ({ ...n })))

/* ---------- PATIENT PANEL FILTERS ---------- */
const patientSearch = ref('')
const statusFilter = ref('All Status')

const filteredPatients = computed(() => {
  return patients.value.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(patientSearch.value.toLowerCase())
    const matchesStatus = statusFilter.value === 'All Status' || p.status === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

/* ---------- ACTIONS ---------- */
function acceptRequest(request) {
  patientRequests.value = patientRequests.value.filter(r => r.name !== request.name)
}

function startSession(appt) {
  navigateTo(`/appointments?start=${appt.name}`)
}

const selectedPatientForNcp = ref('')
function beginNcpAssessment() {
  if (!selectedPatientForNcp.value) return
  navigateTo(`/ncp-records?new=true&patient=${selectedPatientForNcp.value}`)
}

function uploadResource() {
  navigateTo('/resource-library?upload=true')
}

function resourceIcon(type) {
  if (type === 'pdf') return FileText
  if (type === 'video') return PlayCircle
  return FileEdit
}

function saveSettings() {
  // Wire this up to your real API call to persist settings
  console.log('Saving settings', settings.value)
}

const earningsProgress = computed(() =>
  Math.min(100, (earningsSummary.value.thisMonthNet / (earningsSummary.value.monthlyGoal || 1)) * 100)
)
</script>

<style scoped>
* { box-sizing: border-box; }

.rnd-dashboard { font-family: 'Inter', sans-serif; }

.empty-text { font-size: 0.85rem; color: #9aaa9a; padding: 12px 0; }

/* WELCOME BANNER */
.welcome-banner {
  background: linear-gradient(135deg, #14301a, #1e4a26);
  border-radius: 16px; padding: 32px 36px; display: flex; align-items: center;
  justify-content: space-between; margin-bottom: 24px; color: #fff;
}
.banner-eyebrow { font-size: 0.7rem; letter-spacing: 0.1em; color: #D4A017; font-weight: 700; }
.banner-title { font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.7rem; margin: 8px 0 6px; color: #fff; }
.banner-sub { font-size: 0.85rem; color: #b8ccb8; margin: 0; }
.banner-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 24px; padding: 12px 24px; font-weight: 700; font-size: 0.88rem; cursor: pointer; flex-shrink: 0; }

/* STAT CARDS */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid #eceeec; }
.stat-icon { width: 36px; height: 36px; border-radius: 8px; background: #eef3ec; display: flex; align-items: center; justify-content: center; color: #1e4a26; margin-bottom: 12px; }
.stat-icon.pending-icon { background: #faf1de; color: #b8860b; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stat-label { font-size: 0.8rem; color: #6a7a6a; margin: 4px 0 8px; }
.stat-delta { font-size: 0.75rem; margin: 0; }
.stat-delta.up { color: #2e7d32; }
.stat-delta.neutral { color: #8a9a8a; }

/* TABS */
.dash-tabs { display: flex; gap: 24px; border-bottom: 1px solid #e5e8e5; margin-bottom: 20px; overflow-x: auto; }
.tab-item { display: flex; align-items: center; gap: 6px; background: none; border: none; cursor: pointer; padding: 10px 2px; font-size: 0.85rem; font-weight: 600; color: #8a9a8a; white-space: nowrap; border-bottom: 2px solid transparent; }
.tab-item.active { color: #1a3a1a; border-bottom-color: #D4A017; }

/* GRID */
.dash-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; align-items: start; }
.dash-col { display: flex; flex-direction: column; gap: 20px; }
.panel { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 22px; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }

/* ALERTS */
.alert-list { display: flex; flex-direction: column; gap: 10px; }
.alert-item { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px; border-radius: 10px; }
.alert-item.level-danger { background: #fbe9e9; }
.alert-item.level-warning { background: #faf1de; }
.alert-name { font-weight: 700; font-size: 0.88rem; color: #2a2a2a; margin: 0 0 4px; }
.alert-detail { font-size: 0.78rem; color: #6a6a6a; margin: 0; }
.alert-action { font-size: 0.8rem; font-weight: 700; color: #1a3a1a; text-decoration: underline; white-space: nowrap; }

/* OUTCOMES */
.outcomes-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.outcome-item { text-align: left; }
.outcome-value { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; margin: 0; }
.outcome-value.olive { color: #6b7a3a; }
.outcome-value.green { color: #2e7d32; }
.outcome-value.blue { color: #2a5a8a; }
.outcome-value.gold { color: #b8860b; }
.outcome-label { font-size: 0.72rem; color: #8a9a8a; margin: 4px 0 0; }

/* SCHEDULE */
.schedule-list { display: flex; flex-direction: column; gap: 10px; }
.schedule-item { background: #eef3ec; border-left: 3px solid #D4A017; border-radius: 8px; padding: 12px 14px; }
.schedule-time { font-size: 0.72rem; font-weight: 700; color: #b8860b; margin: 0 0 2px; }
.schedule-name { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0 0 2px; }
.schedule-detail { font-size: 0.76rem; color: #6a7a6a; margin: 0; }

/* REQUESTS */
.request-list { display: flex; flex-direction: column; gap: 12px; }
.request-item { display: flex; align-items: center; gap: 12px; }
.request-avatar { width: 36px; height: 36px; border-radius: 50%; background: #1e4a26; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700; flex-shrink: 0; }
.request-info { flex: 1; }
.request-name { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.request-time { font-size: 0.74rem; color: #8a9a8a; margin: 0; }
.accept-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 8px 16px; font-size: 0.78rem; font-weight: 700; cursor: pointer; }

/* EARNINGS SUMMARY */
.earnings-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
.earnings-label { font-size: 0.85rem; color: #6a7a6a; }
.earnings-amount { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #1a3a1a; }
.earnings-bar { height: 8px; background: #eceeec; border-radius: 4px; overflow: hidden; margin-bottom: 16px; }
.earnings-fill { height: 100%; background: #D4A017; border-radius: 4px; }
.view-earnings-btn { width: 100%; background: #fff; border: 1px solid #1a3a1a; color: #1a3a1a; border-radius: 8px; padding: 10px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }

/* PATIENT PANEL */
.patient-panel { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 22px; }
.panel-toolbar { display: flex; gap: 12px; margin-bottom: 20px; }
.search-box-wide { flex: 1; display: flex; align-items: center; gap: 8px; background: #f4f6f4; border-radius: 8px; padding: 10px 14px; }
.search-box-wide input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }
.status-select { border: 1px solid #e5e8e5; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; color: #4a5a4a; background: #fff; cursor: pointer; }

.patient-table-wrap { overflow-x: auto; }
.patient-table { width: 100%; border-collapse: collapse; }
.patient-table th { text-align: left; font-size: 0.7rem; letter-spacing: 0.05em; color: #9aaa9a; font-weight: 700; padding: 0 12px 12px; border-bottom: 1px solid #eceeec; }
.patient-table td { padding: 16px 12px; border-bottom: 1px solid #f2f4f2; font-size: 0.86rem; color: #2a2a2a; }
.patient-table tr.row-alert { background: #fdf2f2; }
.patient-cell { display: flex; align-items: center; gap: 10px; }
.patient-avatar, .draft-avatar, .mealplan-avatar, .appt-avatar { width: 32px; height: 32px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; }
.patient-name { font-weight: 700; color: #1a3a1a; }
.status-pill { background: #e6efe0; color: #3a6b3a; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.status-pill.pending-pill { background: #faead0; color: #b8860b; }
.alert-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.alert-pill.danger { background: #f9d6d0; color: #c0392b; }
.alert-pill.warning { background: #faead0; color: #b8860b; }
.no-alert { color: #b0b8b0; }
.chart-btn { border: 1px solid #d5dad5; background: #fff; color: #2a2a2a; border-radius: 6px; padding: 6px 16px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.chart-btn.review-btn { border-color: #c0392b; color: #c0392b; }
.view-all-btn { margin-top: 16px; border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 10px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }

/* APPOINTMENTS */
.appointments-panel { display: flex; flex-direction: column; gap: 16px; }
.appt-card { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px 22px; display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.appt-date { width: 52px; height: 52px; border-radius: 8px; background: #eef3ec; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; }
.appt-day { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #1a3a1a; line-height: 1; }
.appt-month { font-size: 0.62rem; letter-spacing: 0.05em; color: #6a7a6a; margin-top: 2px; }
.appt-info { flex: 1; }
.appt-name { display: flex; align-items: center; gap: 10px; font-size: 0.95rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.appt-status-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.appt-status-pill.confirmed { background: #e6efe0; color: #3a6b3a; }
.appt-status-pill.awaiting { background: #faead0; color: #b8860b; }
.appt-detail { font-size: 0.8rem; color: #6a7a6a; margin: 0; }
.start-session-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; white-space: nowrap; }
.appt-note { font-size: 0.78rem; color: #9aaa9a; white-space: nowrap; }

/* NCP DOCUMENTATION */
.draft-list { display: flex; flex-direction: column; gap: 12px; }
.draft-item { display: flex; align-items: center; gap: 12px; }
.draft-info { flex: 1; }
.draft-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.draft-detail { font-size: 0.76rem; color: #6a7a6a; margin: 0; }
.resume-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 6px; padding: 6px 16px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.field-label { display: block; font-size: 0.8rem; font-weight: 600; color: #4a5a4a; margin: 14px 0 6px; }
.field-select, .field-input { width: 100%; border: 1px solid #e5e8e5; border-radius: 8px; padding: 12px 14px; font-size: 0.85rem; color: #2a2a2a; background: #fff; margin-bottom: 6px; }
.begin-assessment-btn { width: 100%; background: #D4A017; color: #1a3a1a; border: none; border-radius: 24px; padding: 13px; font-weight: 700; font-size: 0.88rem; cursor: pointer; margin-top: 14px; }
.ncp-footnote { display: flex; align-items: center; gap: 8px; background: #eef1ee; border-radius: 8px; padding: 12px 16px; font-size: 0.8rem; color: #4a5a4a; margin-top: 20px; }
.footnote-icon { color: #2a5a8a; flex-shrink: 0; }

/* MEAL PLANNING */
.mealplan-list { display: flex; flex-direction: column; gap: 12px; }
.mealplan-item { display: flex; align-items: center; gap: 12px; }
.mealplan-info { flex: 1; }
.mealplan-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.mealplan-detail { font-size: 0.76rem; color: #6a7a6a; margin: 0; }
.edit-btn { border: 1px solid #d5dad5; background: #fff; color: #2a2a2a; border-radius: 6px; padding: 6px 16px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.food-exchange-desc { font-size: 0.85rem; color: #6a7a6a; line-height: 1.5; margin: 0 0 18px; }
.open-search-btn { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; background: #D4A017; color: #1a3a1a; border: none; border-radius: 24px; padding: 13px; font-weight: 700; font-size: 0.88rem; cursor: pointer; }

/* RESOURCES LIBRARY */
.resources-panel { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 22px; }
.resources-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.upload-btn { display: flex; align-items: center; gap: 6px; background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 9px 16px; font-weight: 700; font-size: 0.82rem; cursor: pointer; }
.resource-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 18px; }
.resource-item { display: flex; align-items: center; gap: 14px; padding: 14px 0; border-bottom: 1px solid #f2f4f2; }
.resource-icon { width: 38px; height: 38px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.resource-icon.icon-pdf { background: #fbe4e0; color: #c0392b; }
.resource-icon.icon-video { background: #dde7f7; color: #2a5a8a; }
.resource-icon.icon-article { background: #eef3ec; color: #1e4a26; }
.resource-info { flex: 1; }
.resource-title { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.resource-detail { font-size: 0.76rem; color: #8a9a8a; margin: 0; }

/* EARNINGS & BILLING */
.earnings-panel { display: flex; flex-direction: column; gap: 20px; }
.invoice-table-wrap { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 22px; }
.invoice-id { font-weight: 700; color: #1a3a1a; }
.invoice-net { font-weight: 700; color: #1a3a1a; }
.muted { color: #9aaa9a; }

/* SETTINGS */
.settings-eyebrow { display: block; font-size: 0.7rem; letter-spacing: 0.1em; color: #D4A017; font-weight: 700; margin-bottom: 14px; }
.toggle-row { display: flex; align-items: center; justify-content: space-between; margin: 16px 0; }
.toggle-label { margin: 0; }
.switch { position: relative; display: inline-block; width: 40px; height: 22px; flex-shrink: 0; }
.switch input { opacity: 0; width: 0; height: 0; }
.slider { position: absolute; cursor: pointer; inset: 0; background: #d5dad5; border-radius: 22px; transition: 0.2s; }
.slider::before { content: ""; position: absolute; height: 16px; width: 16px; left: 3px; bottom: 3px; background: #fff; border-radius: 50%; transition: 0.2s; }
.switch input:checked + .slider { background: #1e4a26; }
.switch input:checked + .slider::before { transform: translateX(18px); }
.save-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 11px 20px; font-weight: 700; font-size: 0.85rem; cursor: pointer; margin-top: 8px; }

@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-grid { grid-template-columns: 1fr; }
  .appt-card { flex-wrap: wrap; }
}
</style>