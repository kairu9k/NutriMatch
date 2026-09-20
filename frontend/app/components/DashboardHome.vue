<template>
  <div class="rnd-dashboard">
    <!-- WELCOME BANNER -->
    <section class="welcome-banner">
      <div class="banner-blob banner-blob-1"></div>
      <div class="banner-blob banner-blob-2"></div>

      <div class="banner-content">
        <span class="banner-badge"><span class="banner-badge-dot"></span> WELCOME BACK</span>
        <h2 class="banner-title">Good Day, {{ rndName }}.</h2>
        <p class="banner-sub">
          <strong>{{ todaysAppointments.length }} consultations</strong> today ·
          <strong>{{ draftRecords.length }} NCP records</strong> awaiting finalization ·
          <strong>{{ patientRequests.length }} new patient requests</strong>
        </p>
        <div class="banner-actions">
          <NuxtLink to="/appointments" class="banner-btn">View Today's Schedule</NuxtLink>
        </div>
      </div>
    </section>

    <!-- STAT CARDS -->
    <section class="stat-grid">
      <div class="stat-card">
        <div class="stat-top">
          <div class="stat-icon"><Users :size="17" /></div>
        </div>
        <p class="stat-value">{{ activeRelationships.length }}</p>
        <p class="stat-label">Active Patients</p>
        <p class="stat-delta neutral">{{ activeRelationships.length ? 'Active caseload' : 'No patients yet' }}</p>
      </div>
      <div class="stat-card">
        <div class="stat-top">
          <div class="stat-icon icon-gold"><CalendarCheck :size="17" /></div>
        </div>
        <p class="stat-value">{{ todaysAppointments.length }}</p>
        <p class="stat-label">Today's Sessions</p>
        <p v-if="todaysAppointments.length" class="stat-delta neutral">🕐 Next at {{ formatTime(todaysAppointments[0].scheduled_at) }}</p>
        <p v-else class="stat-delta neutral">Nothing scheduled</p>
      </div>
      <div class="stat-card">
        <div class="stat-top">
          <div class="stat-icon"><Trophy :size="17" /></div>
        </div>
        <!-- No goal/adherence-tracking model in the schema yet. -->
        <p class="stat-value">—%</p>
        <p class="stat-label">Avg. Goal Achievement</p>
        <p class="stat-delta neutral">No data yet</p>
      </div>
      <div class="stat-card">
        <div class="stat-top">
          <div class="stat-icon icon-gold"><Landmark :size="17" /></div>
        </div>
        <p class="stat-value">₱{{ earningsThisMonth.net.toLocaleString() }}</p>
        <p class="stat-label">Earnings (This Month)</p>
        <p class="stat-delta neutral">{{ earningsThisMonth.count }} billable session{{ earningsThisMonth.count === 1 ? '' : 's' }}</p>
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
          <h3 class="panel-title">Draft NCP Records</h3>
          <div v-if="draftRecords.length" class="draft-list">
            <div v-for="d in draftRecords" :key="d.id" class="draft-item">
              <div class="draft-avatar" :style="{ background: colorForId(d.relationship_id) }">{{ initialsFor(d.client_name) }}</div>
              <div class="draft-info">
                <p class="draft-name">{{ d.client_name }}</p>
                <p class="draft-detail">Draft — last updated {{ formatDate(d.updated_at) }}</p>
              </div>
              <button class="resume-btn" @click="navigateTo(`/ncp-records?relationship=${d.relationship_id}`)">Resume</button>
            </div>
          </div>
          <p v-else class="empty-text">No drafts in progress.</p>
        </div>

        <div class="panel">
          <div class="panel-header-row">
            <h3 class="panel-title">Patient Adherence — Weekly</h3>
            <NuxtLink to="/my-patients" class="panel-link">View Report →</NuxtLink>
          </div>
          <!-- No adherence-tracking model in the schema yet — placeholder chart. -->
          <div class="bar-chart">
            <div class="bar-col" v-for="d in weeklyAdherence" :key="d.day">
              <div class="bar-wrap">
                <span class="bar-tooltip">{{ d.value }}%</span>
                <div class="bar" :class="d.variant" :style="{ height: d.value + '%' }"></div>
              </div>
              <span class="bar-label">{{ d.day }}</span>
            </div>
          </div>
        </div>

        <div class="panel">
          <h3 class="panel-title">Clinical Alerts</h3>
          <!-- No clinical-alert model in the schema yet — placeholder rows. -->
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
          <!-- No outcomes-aggregation endpoint yet — placeholder figures. -->
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
          <div v-if="todaysAppointments.length" class="schedule-list">
            <div v-for="a in todaysAppointments" :key="a.id" class="schedule-item">
              <p class="schedule-time">{{ formatTime(a.scheduled_at) }}</p>
              <p class="schedule-name">{{ a.relationship.client.first_name }} {{ a.relationship.client.last_name }}</p>
              <p class="schedule-detail">{{ a.type.replace('_', ' ') }} · {{ statusLabel(a.status) }}</p>
            </div>
          </div>
          <p v-else class="empty-text">No appointments today.</p>
        </div>

        <div class="panel">
          <h3 class="panel-title">New Patient Requests</h3>
          <div v-if="patientRequests.length" class="request-list">
            <div v-for="r in patientRequests" :key="r.id" class="request-item">
              <div class="request-avatar">{{ initialsFor(`${r.client.first_name} ${r.client.last_name}`) }}</div>
              <div class="request-info">
                <p class="request-name">{{ r.client.first_name }} {{ r.client.last_name }}</p>
                <p class="request-time">Requested {{ formatDate(r.created_at) }}</p>
              </div>
              <button class="accept-btn" :disabled="busyRequestId === r.id" @click="acceptRequest(r)">Accept</button>
            </div>
          </div>
          <p v-else class="empty-text">No pending requests.</p>
        </div>

        <div class="panel">
          <h3 class="panel-title">Earnings Summary</h3>
          <div class="earnings-row">
            <span class="earnings-label">This month (net)</span>
            <span class="earnings-amount">₱{{ earningsThisMonth.net.toLocaleString() }}</span>
          </div>
          <NuxtLink to="/earnings" class="view-earnings-btn">View Earnings Report</NuxtLink>
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
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="discharged">Discharged</option>
        </select>
      </div>

      <div v-if="filteredPatients.length" class="patient-table-wrap">
        <table class="patient-table">
          <thead>
            <tr>
              <th>PATIENT</th><th>CONDITION</th><th>STATUS</th><th>LAST VISIT</th><th>NCP STATUS</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in filteredPatients" :key="p.id">
              <td class="patient-cell">
                <div class="patient-avatar" :style="{ background: colorForId(p.client.id) }">{{ initialsFor(`${p.client.first_name} ${p.client.last_name}`) }}</div>
                <span class="patient-name">{{ p.client.first_name }} {{ p.client.last_name }}</span>
              </td>
              <td>{{ p.condition || '—' }}</td>
              <td><span class="status-pill" :class="{ 'pending-pill': p.status === 'pending' }">{{ p.status }}</span></td>
              <td>{{ p.last_visit ? formatDate(p.last_visit) : '—' }}</td>
              <td>{{ p.ncp_status || '—' }}</td>
              <td>
                <button class="chart-btn" @click="navigateTo(`/client-detail/${p.id}`)">Chart</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty-text">No patients match your search.</p>

      <button v-if="allPatients.length" class="view-all-btn" @click="navigateTo('/my-patients')">
        View All {{ allPatients.length }} Patients →
      </button>
    </section>

    <!-- ============ APPOINTMENTS TAB ============ -->
    <section v-if="activeTab === 'Appointments'" class="appointments-panel">
      <div v-if="allAppointments.length">
        <div v-for="appt in allAppointments" :key="appt.id" class="appt-card">
          <div class="appt-date">
            <span class="appt-day">{{ formatDay(appt.scheduled_at) }}</span>
            <span class="appt-month">{{ formatMonth(appt.scheduled_at) }}</span>
          </div>
          <div class="appt-avatar" :style="{ background: colorForId(appt.relationship.client.id) }">{{ initialsFor(`${appt.relationship.client.first_name} ${appt.relationship.client.last_name}`) }}</div>
          <div class="appt-info">
            <p class="appt-name">
              {{ appt.relationship.client.first_name }} {{ appt.relationship.client.last_name }}
              <span class="appt-status-pill" :class="appt.status === 'confirmed' ? 'confirmed' : 'awaiting'">{{ statusLabel(appt.status) }}</span>
            </p>
            <p class="appt-detail">{{ formatTime(appt.scheduled_at) }} · {{ appt.type.replace('_', ' ') }}</p>
          </div>
          <div class="appt-action">
            <NuxtLink v-if="appt.status === 'confirmed' && appt.video_session_url" :to="`/consultation-room/${appt.id}`" class="start-session-btn">Join Call</NuxtLink>
            <span v-else class="appt-note">{{ statusLabel(appt.status) }}</span>
          </div>
        </div>
      </div>
      <p v-else class="empty-text">No appointments yet.</p>

      <button v-if="allAppointments.length" class="view-all-btn" @click="navigateTo('/appointments')">View All Appointments →</button>
    </section>

    <!-- ============ NCP DOCUMENTATION TAB ============ -->
    <section v-if="activeTab === 'NCP Documentation'" class="ncp-panel">
      <div class="dash-grid">
        <div class="panel">
          <h3 class="panel-title">Draft NCP Records</h3>
          <div v-if="draftRecords.length" class="draft-list">
            <div v-for="d in draftRecords" :key="d.id" class="draft-item">
              <div class="draft-avatar" :style="{ background: colorForId(d.relationship_id) }">{{ initialsFor(d.client_name) }}</div>
              <div class="draft-info">
                <p class="draft-name">{{ d.client_name }}</p>
                <p class="draft-detail">Draft — last updated {{ formatDate(d.updated_at) }}</p>
              </div>
              <button class="resume-btn" @click="navigateTo(`/ncp-records?relationship=${d.relationship_id}`)">Resume</button>
            </div>
          </div>
          <p v-else class="empty-text">No drafts in progress.</p>
        </div>

        <div class="panel">
          <h3 class="panel-title">Start New NCP Record</h3>
          <label class="field-label">Select Patient</label>
          <select v-model="selectedRelationshipForNcp" class="field-select">
            <option value="">Select active patient...</option>
            <option v-for="p in activeRelationships" :key="p.id" :value="p.id">{{ p.client.first_name }} {{ p.client.last_name }}</option>
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
        <h3 class="panel-title">Your Patients</h3>
        <!-- No "active meal plans" list endpoint yet — links out to each
             patient's own meal plan via the real Meal Plans page instead. -->
        <div v-if="activeRelationships.length" class="mealplan-list">
          <div v-for="p in activeRelationships" :key="p.id" class="mealplan-item">
            <div class="mealplan-avatar" :style="{ background: colorForId(p.client.id) }">{{ initialsFor(`${p.client.first_name} ${p.client.last_name}`) }}</div>
            <div class="mealplan-info">
              <p class="mealplan-name">{{ p.client.first_name }} {{ p.client.last_name }}</p>
              <p class="mealplan-detail">{{ p.condition || 'No condition on file' }}</p>
            </div>
            <button class="edit-btn" @click="navigateTo(`/meal-planning?relationship=${p.id}`)">Open</button>
          </div>
        </div>
        <p v-else class="empty-text">No active patients yet.</p>
      </div>

      <div class="panel food-exchange-panel">
        <h3 class="panel-title">FNRI Food Exchange Search</h3>
        <p class="food-exchange-desc">
          Search the FNRI Food Exchange List (4th Ed.) to build evidence-based meal plans.
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
        <button class="upload-btn" @click="navigateTo('/resource-upload')"><Plus :size="15" /> Upload Resource</button>
      </div>
      <p class="empty-text">Manage and upload patient-facing resources from the full Resources page.</p>
      <button class="view-all-btn" @click="navigateTo('/resource-upload')">Open Resources Library →</button>
    </section>

    <!-- ============ EARNINGS & BILLING TAB ============ -->
    <section v-if="activeTab === 'Earnings & Billing'" class="earnings-panel">
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-top">
            <div class="stat-icon"><Eye :size="17" /></div>
          </div>
          <p class="stat-value">₱{{ earningsThisMonth.gross.toLocaleString() }}</p>
          <p class="stat-label">Gross This Month</p>
        </div>
        <div class="stat-card">
          <div class="stat-top">
            <div class="stat-icon"><Percent :size="17" /></div>
          </div>
          <p class="stat-value">₱{{ earningsThisMonth.commission.toLocaleString() }}</p>
          <p class="stat-label">Commission</p>
        </div>
        <div class="stat-card">
          <div class="stat-top">
            <div class="stat-icon"><Wallet :size="17" /></div>
          </div>
          <p class="stat-value">₱{{ earningsThisMonth.net.toLocaleString() }}</p>
          <p class="stat-label">Net Earnings</p>
        </div>
        <div class="stat-card">
          <div class="stat-top">
            <div class="stat-icon icon-gold"><Hourglass :size="17" /></div>
          </div>
          <p class="stat-value">₱{{ pendingInvoiceTotal.toLocaleString() }}</p>
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
              <td class="invoice-id">INV-{{ String(inv.id).padStart(4, '0') }}</td>
              <td>{{ inv.client_name }}</td>
              <td>{{ formatDate(inv.created_at) }}</td>
              <td>₱{{ Number(inv.amount).toFixed(2) }}</td>
              <td class="muted">₱{{ Number(inv.commission_amt).toFixed(2) }}</td>
              <td class="invoice-net">₱{{ Number(inv.net).toFixed(2) }}</td>
              <td><span class="status-pill" :class="{ 'pending-pill': inv.status !== 'paid' }">{{ inv.status === 'paid' ? 'Paid' : 'Pending' }}</span></td>
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
        <p class="empty-text">Edit your specialization, fees, and availability from the full Profile Settings page.</p>
        <button class="save-btn" @click="navigateTo('/profile-settings')">Open Profile Settings →</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  Users, CalendarCheck, Landmark, Trophy,
  LayoutGrid, UserCircle2, CalendarDays, FileBarChart2,
  Compass, BookOpen, CreditCard, Settings as SettingsIcon,
  Search, Info, Plus, Eye, Percent, Wallet, Hourglass,
} from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Dashboard' })

const { get, patch } = useApi()
const auth = useAuthStore()

const rndName = computed(() => auth.user ? `${auth.user.first_name} ${auth.user.last_name}` : 'RND')

const activeTab = ref('Overview')
const tabs = [
  { label: 'Overview', icon: LayoutGrid },
  { label: 'Patient Panel', icon: UserCircle2 },
  { label: 'Appointments', icon: CalendarDays },
  { label: 'NCP Documentation', icon: FileBarChart2 },
  { label: 'Meal Planning', icon: Compass },
  { label: 'Resources Library', icon: BookOpen },
  { label: 'Earnings & Billing', icon: CreditCard },
  { label: 'Settings', icon: SettingsIcon },
]

const AVATAR_COLORS = ['#1e4a26', '#3a6b3a', '#D4A017', '#6a8a6a', '#8a6a3a']
function colorForId(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}
function initialsFor(name) {
  const parts = name.trim().split(' ')
  return `${parts[0]?.[0] || ''}${parts[1]?.[0] || ''}`.toUpperCase()
}
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}
function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
function formatDay(iso) {
  return new Date(iso).toLocaleDateString('en-US', { day: 'numeric' })
}
function formatMonth(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short' }).toUpperCase()
}
function statusLabel(status) {
  return { pending: 'Pending Confirmation', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }[status] || status
}

const activeRelationships = ref([])
const rawAppointments = ref([])
const draftRecords = ref([])
const patientRequests = ref([])
const invoices = ref([])
const allPatients = ref([])
const busyRequestId = ref(null)

// TODO: wire to a real weekly adherence endpoint once one exists.
const weeklyAdherence = ref([
  { day: 'Mon', value: 55, variant: 'bar-mint' },
  { day: 'Tue', value: 78, variant: 'bar-gold' },
  { day: 'Wed', value: 42, variant: 'bar-mint' },
  { day: 'Thu', value: 90, variant: 'bar-mint' },
  { day: 'Fri', value: 68, variant: 'bar-gold' },
  { day: 'Sat', value: 95, variant: 'bar-mint' },
  { day: 'Sun', value: 65, variant: 'bar-gold' },
])
// TODO: wire to a real clinical-alerts source once one exists.
const clinicalAlerts = ref([])
// TODO: wire to a real outcomes-aggregation endpoint once one exists.
const healthOutcomes = ref([])

const todaysAppointments = computed(() => {
  const now = new Date()
  const todayKey = now.toDateString()
  return rawAppointments.value
    .filter(a => new Date(a.scheduled_at).toDateString() === todayKey)
    .filter(a => a.status === 'pending' || a.status === 'confirmed')
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
})

const allAppointments = computed(() =>
  [...rawAppointments.value].sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
)

const earningsThisMonth = computed(() => {
  const now = new Date()
  const monthInvoices = invoices.value.filter(inv => {
    const d = new Date(inv.created_at)
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth()
  })
  const paid = monthInvoices.filter(inv => inv.status === 'paid')
  return {
    gross: monthInvoices.reduce((sum, inv) => sum + Number(inv.amount), 0),
    commission: monthInvoices.reduce((sum, inv) => sum + Number(inv.commission_amt), 0),
    net: paid.reduce((sum, inv) => sum + Number(inv.net), 0),
    count: paid.length,
  }
})

const pendingInvoiceTotal = computed(() =>
  invoices.value.filter(inv => inv.status !== 'paid').reduce((sum, inv) => sum + Number(inv.amount), 0)
)

/* ---------- PATIENT PANEL FILTERS ---------- */
const patientSearch = ref('')
const statusFilter = ref('All Status')

const filteredPatients = computed(() => {
  return allPatients.value.filter(p => {
    const name = `${p.client.first_name} ${p.client.last_name}`.toLowerCase()
    const matchesSearch = name.includes(patientSearch.value.toLowerCase())
    const matchesStatus = statusFilter.value === 'All Status' || p.status === statusFilter.value
    return matchesSearch && matchesStatus
  })
})

/* ---------- ACTIONS ---------- */
async function acceptRequest(request) {
  busyRequestId.value = request.id
  try {
    await patch(`/rnd/relationships/${request.id}/accept/`)
    patientRequests.value = patientRequests.value.filter(r => r.id !== request.id)
    activeRelationships.value.push(request)
  } finally {
    busyRequestId.value = null
  }
}

const selectedRelationshipForNcp = ref('')
function beginNcpAssessment() {
  if (!selectedRelationshipForNcp.value) return
  navigateTo(`/ncp-records?relationship=${selectedRelationshipForNcp.value}`)
}

async function loadDashboard() {
  const [relationships, appointments, drafts, requests, rndInvoices, patients] = await Promise.all([
    get('/rnd/relationships/active/').catch(() => []),
    get('/rnd/appointments/').catch(() => []),
    get('/rnd/ncp/drafts/').catch(() => []),
    get('/rnd/relationship-requests/').catch(() => []),
    get('/rnd/invoices/').catch(() => []),
    get('/rnd/patients/').catch(() => []),
  ])
  activeRelationships.value = relationships
  rawAppointments.value = appointments
  draftRecords.value = drafts
  patientRequests.value = requests
  invoices.value = rndInvoices
  allPatients.value = patients
}

onMounted(loadDashboard)
</script>

<style scoped>
* { box-sizing: border-box; }

.rnd-dashboard { font-family: 'Inter', sans-serif; }

.empty-text { font-size: 0.85rem; color: #9aaa9a; padding: 12px 0; }

/* WELCOME BANNER */
.welcome-banner {
  position: relative;
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%);
  border-radius: 16px; padding: 32px 36px; overflow: hidden;
  margin: 0 0 24px; color: #fff;
  width: 100%;
}
.banner-blob { position: absolute; border-radius: 50%; background: rgba(255,255,255,0.05); }
.banner-blob-1 { width: 260px; height: 260px; top: -90px; right: 40px; }
.banner-blob-2 { width: 160px; height: 160px; bottom: -70px; right: -20px; background: rgba(255,255,255,0.04); }

.banner-content { position: relative; z-index: 1; }
.banner-badge {
  display: inline-flex; align-items: center; gap: 7px;
  background: rgba(0,0,0,0.2); color: #D4A017;
  font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
  padding: 5px 14px; border-radius: 20px; margin-bottom: 14px;
}
.banner-badge-dot { width: 5px; height: 5px; border-radius: 50%; background: #D4A017; }
.banner-title { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.7rem; margin: 0 0 8px; color: #fff; }
.banner-sub { font-size: 0.85rem; color: #cfe0d5; margin: 0 0 20px; max-width: 620px; line-height: 1.5; }
.banner-sub strong { color: #f0c419; font-weight: 700; }
.banner-actions { display: flex; gap: 10px; }
.banner-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 11px 20px; font-weight: 700; font-size: 0.85rem; cursor: pointer;
  text-decoration: none; display: inline-block;
}

/* STAT CARDS */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 14px; padding: 20px; border: 1px solid #eceeec; }
.stat-top { margin-bottom: 12px; }
.stat-icon { width: 34px; height: 34px; border-radius: 9px; background: #eef3ec; display: flex; align-items: center; justify-content: center; color: #1e4a26; }
.stat-icon.icon-gold { background: #fdf1d6; color: #b8860b; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stat-label { font-size: 0.8rem; color: #6a7a6a; margin: 4px 0 8px; }
.stat-delta { font-size: 0.75rem; margin: 0; }
.stat-delta.neutral { color: #8a9a8a; }

/* TABS */
.dash-tabs { display: flex; gap: 24px; border-bottom: 1px solid #e5e8e5; margin-bottom: 20px; overflow-x: auto; }
.tab-item { display: flex; align-items: center; gap: 6px; background: none; border: none; cursor: pointer; padding: 10px 2px; font-size: 0.85rem; font-weight: 600; color: #8a9a8a; white-space: nowrap; border-bottom: 2px solid transparent; }
.tab-item.active { color: #1a3a1a; border-bottom-color: #D4A017; }
.tab-item:hover:not(.active) { color: #4a5a4a; }

/* GRID */
.dash-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; align-items: start; }
.dash-col { display: flex; flex-direction: column; gap: 20px; }
.panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }
.panel-header-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.panel-header-row .panel-title { margin: 0; }
.panel-link { font-size: 0.78rem; color: #1f8f5c; font-weight: 600; text-decoration: none; }

/* BAR CHART */
.bar-chart { display: flex; align-items: flex-end; gap: 12px; height: 170px; }
.bar-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; gap: 8px; }
.bar-wrap { position: relative; width: 100%; height: 100%; display: flex; align-items: flex-end; }
.bar {
  width: 100%; border-radius: 6px 6px 0 0;
  transition: height 0.2s ease, filter 0.15s ease, transform 0.15s ease;
  cursor: pointer;
}
.bar:hover { background: #14301a; transform: scaleY(1.02); transform-origin: bottom; }
.bar-mint { background: #cfe3da; }
.bar-gold { background: #f1cf6b; }
.bar-gold:hover { background: #f0c419; }
.bar-label { font-size: 0.72rem; color: #9aaa9a; }

.bar-tooltip {
  position: absolute; bottom: calc(100% + 8px); left: 50%; transform: translateX(-50%);
  background: #14301a; color: #fff; font-size: 0.72rem; font-weight: 700;
  padding: 4px 9px; border-radius: 6px; white-space: nowrap;
  opacity: 0; pointer-events: none; transition: opacity 0.15s ease, bottom 0.15s ease;
}
.bar-tooltip::after {
  content: ''; position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
  border: 5px solid transparent; border-top-color: #14301a;
}
.bar-wrap:hover .bar-tooltip { opacity: 1; bottom: calc(100% + 12px); }

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
.outcome-value.green { color: #1f8f5c; }
.outcome-value.blue { color: #2a5a8a; }
.outcome-value.gold { color: #b8860b; }
.outcome-label { font-size: 0.72rem; color: #8a9a8a; margin: 4px 0 0; }

/* SCHEDULE */
.schedule-list { display: flex; flex-direction: column; gap: 10px; }
.schedule-item { background: #f7f9f7; border-left: 3px solid #D4A017; border-radius: 8px; padding: 12px 14px; }
.schedule-time { font-size: 0.72rem; font-weight: 700; color: #b8860b; margin: 0 0 2px; }
.schedule-name { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0 0 2px; }
.schedule-detail { font-size: 0.76rem; color: #6a7a6a; margin: 0; text-transform: capitalize; }

/* REQUESTS */
.request-list { display: flex; flex-direction: column; gap: 12px; }
.request-item { display: flex; align-items: center; gap: 12px; }
.request-avatar { width: 36px; height: 36px; border-radius: 50%; background: #00382a; color: #D4A017; display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700; flex-shrink: 0; }
.request-info { flex: 1; }
.request-name { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.request-time { font-size: 0.74rem; color: #8a9a8a; margin: 0; }
.accept-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 8px 16px; font-size: 0.78rem; font-weight: 700; cursor: pointer; }
.accept-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* EARNINGS SUMMARY */
.earnings-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 16px; }
.earnings-label { font-size: 0.85rem; color: #6a7a6a; }
.earnings-amount { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #1a3a1a; }
.view-earnings-btn {
  display: block; width: 100%; text-align: center; background: #fff; border: 1px solid #1a3a1a; color: #1a3a1a;
  border-radius: 8px; padding: 10px; font-weight: 700; font-size: 0.85rem; cursor: pointer; text-decoration: none; box-sizing: border-box;
}

/* NCP DRAFTS */
.draft-list { display: flex; flex-direction: column; gap: 12px; }
.draft-item { display: flex; align-items: center; gap: 12px; }
.draft-avatar { width: 32px; height: 32px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; }
.draft-info { flex: 1; }
.draft-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.draft-detail { font-size: 0.76rem; color: #6a7a6a; margin: 0; }
.resume-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 6px; padding: 6px 16px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }

/* PATIENT PANEL */
.patient-panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px; }
.panel-toolbar { display: flex; gap: 12px; margin-bottom: 20px; }
.search-box-wide { flex: 1; display: flex; align-items: center; gap: 8px; background: #f4f6f4; border-radius: 8px; padding: 10px 14px; }
.search-box-wide input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }
.status-select { border: 1px solid #dde3dd; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; color: #4a5a4a; background: #fff; cursor: pointer; }

.patient-table-wrap { overflow-x: auto; }
.patient-table { width: 100%; border-collapse: collapse; }
.patient-table th { text-align: left; font-size: 0.7rem; letter-spacing: 0.05em; color: #9aaa9a; font-weight: 700; padding: 0 12px 12px; border-bottom: 1px solid #eceeec; }
.patient-table td { padding: 16px 12px; border-bottom: 1px solid #f2f4f2; font-size: 0.86rem; color: #2a2a2a; }
.patient-cell { display: flex; align-items: center; gap: 10px; }
.patient-avatar, .draft-avatar, .mealplan-avatar, .appt-avatar { width: 32px; height: 32px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; }
.patient-name { font-weight: 700; color: #1a3a1a; }
.status-pill { background: #e3f3ea; color: #1f8f5c; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; text-transform: capitalize; }
.status-pill.pending-pill { background: #faead0; color: #b8860b; }
.chart-btn { border: 1px solid #d5dad5; background: #fff; color: #2a2a2a; border-radius: 6px; padding: 6px 16px; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.view-all-btn { margin-top: 16px; border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 10px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }

/* APPOINTMENTS */
.appointments-panel { display: flex; flex-direction: column; gap: 16px; }
.appt-card { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 20px 22px; display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
.appt-date { width: 52px; height: 52px; border-radius: 8px; background: #eef3ec; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; }
.appt-day { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #1a3a1a; line-height: 1; }
.appt-month { font-size: 0.62rem; letter-spacing: 0.05em; color: #6a7a6a; margin-top: 2px; }
.appt-info { flex: 1; }
.appt-name { display: flex; align-items: center; gap: 10px; font-size: 0.95rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.appt-status-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.appt-status-pill.confirmed { background: #e3f3ea; color: #1f8f5c; }
.appt-status-pill.awaiting { background: #faead0; color: #b8860b; }
.appt-detail { font-size: 0.8rem; color: #6a7a6a; margin: 0; text-transform: capitalize; }
.start-session-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; white-space: nowrap; text-decoration: none; display: inline-block; }
.appt-note { font-size: 0.78rem; color: #9aaa9a; white-space: nowrap; }

/* NCP DOCUMENTATION */
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
.resources-panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px; }
.resources-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.upload-btn { display: flex; align-items: center; gap: 6px; background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 9px 16px; font-weight: 700; font-size: 0.82rem; cursor: pointer; }

/* EARNINGS & BILLING */
.earnings-panel { display: flex; flex-direction: column; gap: 20px; }
.invoice-table-wrap { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px; }
.invoice-id { font-weight: 700; color: #1a3a1a; }
.invoice-net { font-weight: 700; color: #1a3a1a; }
.muted { color: #9aaa9a; }

/* SETTINGS */
.settings-eyebrow { display: block; font-size: 0.7rem; letter-spacing: 0.1em; color: #D4A017; font-weight: 700; margin-bottom: 14px; }
.save-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 11px 20px; font-weight: 700; font-size: 0.85rem; cursor: pointer; margin-top: 8px; }

@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-grid { grid-template-columns: 1fr; }
  .outcomes-grid { grid-template-columns: repeat(2, 1fr); }
  .appt-card { flex-wrap: wrap; }
}
</style>
