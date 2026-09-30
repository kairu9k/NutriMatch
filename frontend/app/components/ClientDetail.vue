<template>
  <div class="detail-page">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="clientProfile">
      <p class="breadcrumb"><NuxtLink to="/my-patients">My Patients</NuxtLink> / {{ clientName }}</p>

      <div class="patient-banner">
        <div class="banner-left">
          <div class="big-avatar">{{ initials }}</div>
          <div class="banner-info">
            <h1 class="banner-name">{{ clientName }}</h1>
            <p class="banner-meta">{{ age !== null ? `${age} y/o ` : '' }}{{ sexLabel }}{{ conditions ? ' · ' + conditions : '' }}</p>
            <div class="banner-chips">
              <span class="chip chip-success">Active Relationship</span>
              <span v-if="allergies" class="chip">Allergy: {{ allergies }}</span>
            </div>
          </div>
        </div>
        <NuxtLink :to="`/messages?relationship=${relationshipId}`" class="message-btn">Message</NuxtLink>
      </div>

      <nav class="detail-tabs">
        <button
          v-for="tab in detailTabs"
          :key="tab"
          class="detail-tab"
          :class="{ active: activeTab === tab }"
          @click="activeTab = tab"
        >
          {{ tab }}
        </button>
      </nav>

      <div v-if="activeTab !== 'Overview'" class="surface">
        <p class="empty-note">{{ activeTab }} isn't broken out separately yet — use the links in Overview below.</p>
      </div>

      <div v-else class="content-grid">
        <div class="main-col">
          <div class="surface">
            <div class="surface-header">
              <h3 class="surface-title">Current NCP Record — Phase Progress</h3>
              <span v-if="latestNcp" class="status-pill" :class="latestNcp.status === 'completed' ? 'success' : 'warning'">
                {{ latestNcp.status === 'completed' ? 'Finalized' : `Draft (Phase ${currentPhaseNumber})` }}
              </span>
            </div>
            <div v-if="latestNcp" class="phase-grid">
              <div class="phase-card" :class="{ done: !!(latestNcp.pes_problem) }">
                <div class="phase-num"><Check v-if="latestNcp.weight_kg" :size="14" /><span v-else>1</span></div>
                <div class="phase-label">Assessment</div>
                <NuxtLink :to="`/ncp-records?relationship=${relationshipId}`" class="phase-action">{{ latestNcp.weight_kg ? 'View' : 'Continue' }}</NuxtLink>
              </div>
              <div class="phase-card" :class="{ done: !!latestNcp.pes_problem }">
                <div class="phase-num"><Check v-if="latestNcp.pes_problem" :size="14" /><span v-else>2</span></div>
                <div class="phase-label">Diagnosis</div>
                <NuxtLink :to="`/ncp-records?relationship=${relationshipId}`" class="phase-action">{{ latestNcp.pes_problem ? 'View' : 'Continue' }}</NuxtLink>
              </div>
              <div class="phase-card" :class="{ done: !!latestNcp.diet_prescription }">
                <div class="phase-num"><Check v-if="latestNcp.diet_prescription" :size="14" /><span v-else>3</span></div>
                <div class="phase-label">Intervention</div>
                <NuxtLink :to="`/ncp-records?relationship=${relationshipId}`" class="phase-action">{{ latestNcp.diet_prescription ? 'View' : 'Continue' }}</NuxtLink>
              </div>
              <div class="phase-card" :class="{ done: !!latestNcp.goal_status }">
                <div class="phase-num"><Check v-if="latestNcp.goal_status" :size="14" /><span v-else>4</span></div>
                <div class="phase-label">Monitoring</div>
                <NuxtLink :to="`/ncp-records?relationship=${relationshipId}`" class="phase-action">{{ latestNcp.goal_status ? 'View' : 'Continue' }}</NuxtLink>
              </div>
            </div>
            <p v-else class="empty-note">No NCP record started yet.</p>
          </div>

          <div class="surface">
            <h3 class="surface-title">Latest Vitals</h3>
            <div v-if="latestVitals" class="vitals-grid">
              <div class="vital-item"><div class="vital-num">{{ latestVitals.weight_kg ? `${latestVitals.weight_kg} kg` : '—' }}</div><div class="vital-label">Weight</div></div>
              <div class="vital-item"><div class="vital-num">{{ latestVitals.bmi || '—' }}</div><div class="vital-label">BMI</div></div>
              <div class="vital-item"><div class="vital-num">{{ latestVitals.blood_pressure || '—' }}</div><div class="vital-label">Blood Pressure</div></div>
              <div class="vital-item"><div class="vital-num">{{ latestVitals.blood_glucose ? `${latestVitals.blood_glucose} mg/dL` : '—' }}</div><div class="vital-label">Fasting Glucose</div></div>
            </div>
            <p v-else class="empty-note">No vitals recorded yet.</p>
          </div>

          <div v-if="latestNcp && latestNcp.pes_problem" class="surface">
            <h3 class="surface-title">Current PES Statement</h3>
            <div class="pes-box">
              <p><strong>Problem:</strong> {{ latestNcp.pes_problem }}</p>
              <p v-if="latestNcp.pes_etiology"><strong>Etiology:</strong> {{ latestNcp.pes_etiology }}</p>
              <p v-if="latestNcp.pes_signs"><strong>Signs:</strong> {{ latestNcp.pes_signs }}</p>
            </div>
          </div>
        </div>

        <div class="side-col">
          <div class="surface">
            <h3 class="surface-title">Health Profile</h3>
            <div class="info-row"><span>Conditions</span><span>{{ conditions || '—' }}</span></div>
            <div class="info-row"><span>Allergies</span><span>{{ allergies || '—' }}</span></div>
            <div class="info-row"><span>Dietary Restriction</span><span>{{ restrictions || '—' }}</span></div>
            <div class="info-row last"><span>Health Goal</span><span>{{ goals || '—' }}</span></div>
          </div>

          <div class="surface">
            <h3 class="surface-title">Next Appointment</h3>
            <template v-if="nextAppointment">
              <p class="appt-date">{{ formatFullDate(nextAppointment.scheduled_at) }}</p>
              <p class="appt-time">{{ formatTime(nextAppointment.scheduled_at) }} · {{ nextAppointment.type.replace('_', ' ') }}</p>
            </template>
            <p v-else class="empty-note">No upcoming appointment.</p>
            <NuxtLink to="/appointments" class="outline-btn small">Manage Appointment</NuxtLink>
          </div>

          <div class="surface">
            <h3 class="surface-title">Quick Actions</h3>
            <!-- Meal plans come out of the NCP Intervention phase (diet
                 prescription + targets), and only for active clients. -->
            <template v-if="relationshipStatus === 'active'">
              <NuxtLink v-if="interventionDone" :to="`/meal-planning?relationship=${relationshipId}&edit=1`" class="primary-btn small">
                {{ hasMealPlan ? 'Update Meal Plan' : 'Create Meal Plan' }}
              </NuxtLink>
              <template v-else>
                <button class="primary-btn small" type="button" disabled>{{ hasMealPlan ? 'Update Meal Plan' : 'Create Meal Plan' }}</button>
                <p class="action-hint">Complete the NCP Intervention (diet prescription and target calories) first.</p>
              </template>
            </template>
            <NuxtLink :to="`/ncp-records?relationship=${relationshipId}`" class="outline-btn small">Continue NCP Record</NuxtLink>
            <NuxtLink :to="`/messages?relationship=${relationshipId}`" class="outline-btn small">Send Message</NuxtLink>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Check } from 'lucide-vue-next'

const route = useRoute()
const { get } = useApi()

const relationshipId = route.params.relationshipId

const isLoading = ref(true)
const errorMessage = ref('')
const clientProfile = ref(null)
const ncpRecords = ref([])
const progressRecords = ref([])
const appointments = ref([])
const mealPlans = ref([])
const relationshipStatus = ref(null)

const hasMealPlan = computed(() => mealPlans.value.length > 0)
const interventionDone = computed(() => {
  const r = ncpRecords.value[0]
  return !!(r && (r.diet_prescription || r.target_kcal))
})

const detailTabs = ['Overview', 'NCP Records', 'Meal Plan', 'Progress History', 'Appointments']
const activeTab = ref('Overview')

const clientName = computed(() => {
  const u = clientProfile.value?.user
  return u ? `${u.first_name} ${u.last_name}` : ''
})
const initials = computed(() => {
  const u = clientProfile.value?.user
  return u ? `${u.first_name?.[0] || ''}${u.last_name?.[0] || ''}`.toUpperCase() : ''
})
const age = computed(() => {
  const dob = clientProfile.value?.date_of_birth
  if (!dob) return null
  const diff = Date.now() - new Date(dob).getTime()
  return Math.floor(diff / (365.25 * 24 * 60 * 60 * 1000))
})
const sexLabel = computed(() => {
  const sex = clientProfile.value?.sex
  return sex ? sex.charAt(0).toUpperCase() + sex.slice(1) : ''
})

const healthProfile = computed(() => clientProfile.value?.health_profile || {})
function joinList(list) {
  return Array.isArray(list) && list.length ? list.join(', ') : null
}
const conditions = computed(() => joinList(healthProfile.value.medical_conditions))
const allergies = computed(() => joinList(healthProfile.value.allergies))
const restrictions = computed(() => joinList(healthProfile.value.dietary_restrictions))
const goals = computed(() => joinList(healthProfile.value.health_goals))

const relationshipAppointments = computed(() =>
  appointments.value.filter(a => String(a.relationship.id) === String(relationshipId))
)
const nextAppointment = computed(() => {
  const upcoming = relationshipAppointments.value
    .filter(a => ['pending', 'confirmed'].includes(a.status) && new Date(a.scheduled_at) > new Date())
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
  return upcoming[0] || null
})

const latestNcp = computed(() => ncpRecords.value[0] || null)
// Whichever phase has no data filled in yet is the current one — a draft
// with only Assessment done is "Phase 2", one with Assessment+Diagnosis+
// Intervention is "Phase 4", etc.
const currentPhaseNumber = computed(() => {
  const r = latestNcp.value
  if (!r) return 1
  if (!r.weight_kg) return 1
  if (!r.pes_problem) return 2
  if (!r.diet_prescription) return 3
  return 4
})
const latestVitals = computed(() => {
  const withVitals = progressRecords.value.find(r => r.weight_kg || r.blood_pressure || r.blood_glucose)
  if (latestNcp.value && (latestNcp.value.weight_kg || latestNcp.value.blood_pressure)) {
    return { weight_kg: latestNcp.value.weight_kg, bmi: latestNcp.value.bmi, blood_pressure: latestNcp.value.blood_pressure, blood_glucose: latestNcp.value.blood_glucose }
  }
  return withVitals || null
})

function formatFullDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
}
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}

async function loadData() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [profile, ncp, progress, appts, plans, patients] = await Promise.all([
      get(`/rnd/relationships/${relationshipId}/client-profile/`),
      get(`/rnd/relationships/${relationshipId}/ncp/`),
      get(`/rnd/relationships/${relationshipId}/progress/`),
      get('/rnd/appointments/'),
      get(`/rnd/relationships/${relationshipId}/meal-plans/`).catch(() => []),
      get('/rnd/patients/').catch(() => []),
    ])
    clientProfile.value = profile
    ncpRecords.value = ncp
    progressRecords.value = progress
    appointments.value = appts
    mealPlans.value = plans
    relationshipStatus.value = patients.find(p => String(p.id) === String(relationshipId))?.status ?? null
  } catch {
    errorMessage.value = 'Could not load this patient. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
* { box-sizing: border-box; }

.detail-page { font-family: 'Inter', sans-serif; }

.breadcrumb { font-size: 0.8rem; color: #8a9a8a; margin: 0 0 14px; }
.breadcrumb :deep(a) { color: #3a6b3a; text-decoration: none; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.patient-banner {
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%);
  border-radius: 16px; padding: 28px 32px; color: #fff;
  display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;
}
.banner-left { display: flex; align-items: center; gap: 18px; }
.big-avatar {
  width: 64px; height: 64px; border-radius: 50%; background: #D4A017; color: #1a3a1a;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.3rem; flex-shrink: 0;
}
.banner-info { min-width: 200px; }
.banner-name { font-family: 'Playfair Display', serif; font-size: 1.4rem; margin: 0 0 4px; }
.banner-meta { font-size: 0.84rem; color: #c9d9c9; margin: 4px 0 8px; }
.banner-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { font-size: 0.74rem; font-weight: 600; padding: 4px 11px; border-radius: 20px; background: rgba(255,255,255,0.12); color: #fff; }
.chip-success { background: #e6efe0; color: #3a6b3a; }
.message-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 9px 18px; font-weight: 700; font-size: 0.85rem; text-decoration: none; white-space: nowrap;
}

.detail-tabs { display: flex; gap: 4px; background: #fff; border: 1px solid #eceeec; border-radius: 30px; padding: 4px; margin-bottom: 20px; width: fit-content; }
.detail-tab { border: none; background: none; padding: 10px 18px; border-radius: 24px; font-size: 0.85rem; font-weight: 600; color: #6a7a6a; cursor: pointer; }
.detail-tab.active { background: #14301a; color: #fff; }

.content-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; align-items: start; }
@media (max-width: 900px) { .content-grid { grid-template-columns: 1fr; } }
.main-col, .side-col { display: flex; flex-direction: column; gap: 16px; }

.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px 22px; }
.surface-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.surface-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 14px; }
.surface-header .surface-title { margin: 0; }

.status-pill { font-size: 0.72rem; font-weight: 700; padding: 4px 12px; border-radius: 14px; }
.status-pill.success { background: #e6efe0; color: #3a6b3a; }
.status-pill.warning { background: #faead0; color: #b8860b; }

.phase-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.phase-card { text-align: left; }
.phase-num {
  width: 34px; height: 34px; border-radius: 50%; background: #eceeec; color: #6a7a6a;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem;
  margin-bottom: 10px;
}
.phase-card.done .phase-num { background: #1f8f5c; color: #fff; }
.phase-label { font-weight: 700; color: #1a3a1a; font-size: 0.88rem; margin: 0 0 8px; }
.phase-action { border: none; background: none; color: #1f8f5c; font-size: 0.8rem; font-weight: 600; cursor: pointer; padding: 0; text-decoration: none; }

.vitals-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.vital-item { text-align: left; }
.vital-num { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.vital-label { font-size: 0.75rem; color: #8a9a8a; margin: 4px 0 0; }

.pes-box { background: #e3edf7; border-radius: 10px; padding: 16px; }
.pes-box p { font-size: 0.86rem; color: #2f6fa8; margin: 0 0 8px; line-height: 1.6; }
.pes-box p:last-child { margin-bottom: 0; }
.pes-box strong { color: #1a4a7a; }

.empty-note { font-size: 0.85rem; color: #9aaa9a; margin: 0 0 14px; }

.info-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f0f0e6; font-size: 0.85rem; }
.info-row.last { border-bottom: none; }
.info-row span:first-child { color: #6a7a6a; }
.info-row span:last-child { font-weight: 600; color: #1a3a1a; text-align: right; }

.appt-date { font-weight: 700; color: #1a3a1a; font-size: 0.92rem; margin: 0; }
.appt-time { font-size: 0.82rem; color: #8a9a8a; margin: 4px 0 14px; }

.outline-btn, .primary-btn {
  display: block; width: 100%; text-align: center; text-decoration: none; border: none;
  border-radius: 8px; font-weight: 700; box-sizing: border-box;
}
.outline-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; }
.primary-btn { background: #D4A017; color: #1a3a1a; }
.small { padding: 9px; font-size: 0.83rem; margin-bottom: 8px; }
.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.action-hint { font-size: 0.74rem; color: #b8860b; margin: -2px 0 10px; line-height: 1.4; }
.small:last-child { margin-bottom: 0; }
</style>
