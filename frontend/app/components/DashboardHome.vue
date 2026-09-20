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

    <!-- ============ OVERVIEW ============
         Note: the branch source this design is ported from defines a full
         tab bar (tabs/activeTab in the script, .dash-tabs/.tab-item CSS)
         but never actually renders it in the template — only this
         Overview content is ever reachable there. Reproduced as-is,
         including that gap, rather than fixing it, per explicit
         instruction to match the branch's real rendered behavior exactly. -->
    <section class="dash-grid">
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

  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Users, CalendarCheck, Landmark, Trophy } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Dashboard' })

const { get, patch } = useApi()
const auth = useAuthStore()

const rndName = computed(() => auth.user ? `${auth.user.first_name} ${auth.user.last_name}` : 'RND')

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
function statusLabel(status) {
  return { pending: 'Pending Confirmation', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }[status] || status
}

const activeRelationships = ref([])
const rawAppointments = ref([])
const draftRecords = ref([])
const patientRequests = ref([])
const invoices = ref([])
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

const earningsThisMonth = computed(() => {
  const now = new Date()
  const monthInvoices = invoices.value.filter(inv => {
    const d = new Date(inv.created_at)
    return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && inv.status === 'paid'
  })
  return {
    net: monthInvoices.reduce((sum, inv) => sum + Number(inv.net), 0),
    count: monthInvoices.length,
  }
})

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

async function loadDashboard() {
  const [relationships, appointments, drafts, requests, rndInvoices] = await Promise.all([
    get('/rnd/relationships/active/').catch(() => []),
    get('/rnd/appointments/').catch(() => []),
    get('/rnd/ncp/drafts/').catch(() => []),
    get('/rnd/relationship-requests/').catch(() => []),
    get('/rnd/invoices/').catch(() => []),
  ])
  activeRelationships.value = relationships
  rawAppointments.value = appointments
  draftRecords.value = drafts
  patientRequests.value = requests
  invoices.value = rndInvoices
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

@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-grid { grid-template-columns: 1fr; }
  .outcomes-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
