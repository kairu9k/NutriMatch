<template>
  <div class="rnd-dashboard">
    <!-- WELCOME BANNER -->
    <section class="welcome-banner">
      <div class="banner-text">
        <span class="banner-eyebrow">— WELCOME BACK</span>
        <h2 class="banner-title">Good Day, {{ rndName }}.</h2>
        <p class="banner-sub">
          {{ todaysAppointments.length }} consultation{{ todaysAppointments.length === 1 ? '' : 's' }} today ·
          {{ draftRecords.length }} NCP record{{ draftRecords.length === 1 ? '' : 's' }} awaiting finalization ·
          {{ patientRequests.length }} new patient request{{ patientRequests.length === 1 ? '' : 's' }}
        </p>
      </div>
      <NuxtLink to="/appointments" class="banner-btn">View Today's Schedule</NuxtLink>
    </section>

    <!-- STAT CARDS -->
    <section class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon"><Users :size="18" /></div>
        <p class="stat-value">{{ activeRelationships.length }}</p>
        <p class="stat-label">Active Patients</p>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><CalendarCheck :size="18" /></div>
        <p class="stat-value">{{ todaysAppointments.length }}</p>
        <p class="stat-label">Today's Sessions</p>
        <p v-if="todaysAppointments.length" class="stat-delta neutral">🕐 Next at {{ formatTime(todaysAppointments[0].scheduled_at) }}</p>
        <p v-else class="stat-delta neutral">Nothing scheduled</p>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><Landmark :size="18" /></div>
        <p class="stat-value">₱{{ earningsThisMonth.net.toLocaleString() }}</p>
        <p class="stat-label">Earnings (This Month)</p>
        <p class="stat-delta neutral">{{ earningsThisMonth.count }} billable session{{ earningsThisMonth.count === 1 ? '' : 's' }}</p>
      </div>
    </section>

    <!-- OVERVIEW -->
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
          <h3 class="panel-title">Earnings Summary</h3>
          <div class="earnings-row">
            <span class="earnings-label">This month (net)</span>
            <span class="earnings-amount">₱{{ earningsThisMonth.net.toLocaleString() }}</span>
          </div>
          <NuxtLink to="/earnings" class="view-earnings-btn">View Earnings Report</NuxtLink>
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
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Users, CalendarCheck, Landmark } from 'lucide-vue-next'

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

onMounted(loadDashboard)
</script>

<style scoped>
* { box-sizing: border-box; }

.rnd-dashboard { font-family: 'Inter', sans-serif; }

.empty-text { font-size: 0.85rem; color: #9aaa9a; padding: 12px 0; }

/* WELCOME BANNER */
.welcome-banner {
  background: linear-gradient(135deg, #14301a, #1e4a26);
  border-radius: 16px; padding: 32px 36px; display: flex; align-items: center;
  justify-content: space-between; margin-bottom: 24px; color: #fff; gap: 16px; flex-wrap: wrap;
}
.banner-eyebrow { font-size: 0.7rem; letter-spacing: 0.1em; color: #D4A017; font-weight: 700; }
.banner-title { font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.7rem; margin: 8px 0 6px; color: #fff; }
.banner-sub { font-size: 0.85rem; color: #b8ccb8; margin: 0; }
.banner-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 24px; padding: 12px 24px;
  font-weight: 700; font-size: 0.88rem; cursor: pointer; flex-shrink: 0; text-decoration: none; display: inline-block;
}

/* STAT CARDS */
.stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 12px; padding: 20px; border: 1px solid #eceeec; }
.stat-icon { width: 36px; height: 36px; border-radius: 8px; background: #eef3ec; display: flex; align-items: center; justify-content: center; color: #1e4a26; margin-bottom: 12px; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stat-label { font-size: 0.8rem; color: #6a7a6a; margin: 4px 0 8px; }
.stat-delta { font-size: 0.75rem; margin: 0; }
.stat-delta.neutral { color: #8a9a8a; }

/* GRID */
.dash-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
.dash-col { display: flex; flex-direction: column; gap: 20px; }
.panel { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 22px; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }

/* SCHEDULE */
.schedule-list { display: flex; flex-direction: column; gap: 10px; }
.schedule-item { background: #eef3ec; border-left: 3px solid #D4A017; border-radius: 8px; padding: 12px 14px; }
.schedule-time { font-size: 0.72rem; font-weight: 700; color: #b8860b; margin: 0 0 2px; }
.schedule-name { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0 0 2px; }
.schedule-detail { font-size: 0.76rem; color: #6a7a6a; margin: 0; text-transform: capitalize; }

/* REQUESTS */
.request-list { display: flex; flex-direction: column; gap: 12px; }
.request-item { display: flex; align-items: center; gap: 12px; }
.request-avatar { width: 36px; height: 36px; border-radius: 50%; background: #1e4a26; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700; flex-shrink: 0; }
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
}
</style>
