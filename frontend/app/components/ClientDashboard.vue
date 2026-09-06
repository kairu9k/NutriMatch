<template>
  <div class="dashboard-page">
    <div class="welcome-banner">
      <div>
        <p class="eyebrow">{{ greeting }}</p>
        <h1 class="welcome-title">Hi {{ auth.user?.first_name }}, welcome back.</h1>
        <p class="welcome-sub">{{ welcomeSubtext }}</p>
      </div>
      <NuxtLink v-if="upcomingAppointment" to="/appointments" class="banner-btn">View Appointment</NuxtLink>
      <NuxtLink v-else to="/find-rnd" class="banner-btn">Find an RND</NuxtLink>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else>
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-icon"><Activity :size="18" /></div>
          <div class="stat-number">{{ screening?.bmi ?? '—' }}</div>
          <div class="stat-label">Current BMI</div>
          <span v-if="screening?.bmi_category" class="badge-pill" :class="bmiBadgeClass">{{ screening.bmi_category }}</span>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><Flame :size="18" /></div>
          <div class="stat-number">{{ screening?.tdee_kcal ? Math.round(screening.tdee_kcal) : '—' }}<span v-if="screening?.tdee_kcal" class="stat-unit">kcal</span></div>
          <div class="stat-label">Daily Target (TDEE)</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><ClipboardList :size="18" /></div>
          <div class="stat-number">{{ screening?.nrs_score ?? '—' }}</div>
          <div class="stat-label">NRS-2002 Score</div>
          <span v-if="screening?.nrs_risk" class="badge-pill" :class="nrsBadgeClass">{{ nrsRiskLabel }}</span>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><CalendarClock :size="18" /></div>
          <div class="stat-number">{{ upcomingAppointment ? formatShortDate(upcomingAppointment.scheduled_at) : '—' }}</div>
          <div class="stat-label">Next Appointment</div>
          <div v-if="upcomingAppointment" class="stat-note">{{ formatTime(upcomingAppointment.scheduled_at) }} · {{ upcomingAppointment.type.replace('_', ' ') }}</div>
        </div>
      </div>

      <div class="content-grid">
        <div class="surface">
          <h3 class="surface-title">Your RND</h3>
          <div v-if="activeRelationship" class="rnd-row">
            <div class="rnd-avatar" :style="{ background: colorForId(activeRelationship.rnd.id) }">{{ initialsFor(activeRelationship.rnd) }}</div>
            <div>
              <p class="rnd-name">RND {{ activeRelationship.rnd.first_name }} {{ activeRelationship.rnd.last_name }}</p>
            </div>
          </div>
          <p v-else class="empty-note">No active RND yet.</p>
          <NuxtLink :to="activeRelationship ? '/messages' : '/find-rnd'" class="outline-btn">
            {{ activeRelationship ? 'Send a Message' : 'Find an RND' }}
          </NuxtLink>
        </div>

        <div class="surface">
          <h3 class="surface-title">Latest Screening</h3>
          <template v-if="screening">
            <div class="screening-row"><span>Weight</span><span>{{ screening.weight_kg }} kg</span></div>
            <div class="screening-row"><span>Height</span><span>{{ screening.height_cm }} cm</span></div>
            <div class="screening-row"><span>BMR</span><span>{{ screening.bmr_kcal ? Math.round(screening.bmr_kcal) + ' kcal' : '—' }}</span></div>
            <div class="screening-row"><span>Recorded</span><span>{{ formatShortDate(screening.created_at) }}</span></div>
          </template>
          <template v-else>
            <p class="empty-note">No screening on file yet — this is recorded ahead of your first consultation.</p>
            <NuxtLink to="/pre-consultation-screening" class="outline-btn">Complete Screening</NuxtLink>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Activity, Flame, ClipboardList, CalendarClock } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Dashboard' })

const auth = useAuthStore()
const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const appointments = ref([])
const relationships = ref([])
const screening = ref(null)

const AVATAR_COLORS = ['#1e4a26', '#3a6b3a', '#D4A017', '#6a8a6a', '#8a6a3a']
function colorForId(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}
function initialsFor(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
}

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'GOOD MORNING'
  if (hour < 18) return 'GOOD AFTERNOON'
  return 'GOOD EVENING'
})

const activeRelationship = computed(() => relationships.value[0] || null)

const upcomingAppointment = computed(() => {
  const upcoming = appointments.value
    .filter(a => ['pending', 'confirmed'].includes(a.status) && new Date(a.scheduled_at) > new Date())
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
  return upcoming[0] || null
})

const welcomeSubtext = computed(() => {
  if (upcomingAppointment.value && activeRelationship.value) {
    return `Next consultation with RND ${activeRelationship.value.rnd.first_name} ${activeRelationship.value.rnd.last_name} on ${formatShortDate(upcomingAppointment.value.scheduled_at)}.`
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

.dashboard-page { font-family: 'Inter', sans-serif; }

.welcome-banner {
  background: linear-gradient(120deg, #1a3a1a, #14301a);
  border-radius: 14px; padding: 26px 28px; color: #fff;
  display: flex; align-items: center; justify-content: space-between; gap: 20px;
  margin-bottom: 20px; flex-wrap: wrap;
}
.eyebrow { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; color: #D4A017; margin: 0 0 8px; }
.welcome-title { font-family: 'Playfair Display', serif; font-style: italic; font-size: 1.4rem; margin: 0; }
.welcome-sub { font-size: 0.85rem; color: #c9d9c9; margin: 8px 0 0; }
.banner-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 10px 20px; font-weight: 700; font-size: 0.85rem; text-decoration: none; white-space: nowrap;
}

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.stat-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px; margin-bottom: 20px;
}
.stat-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 18px;
}
.stat-icon {
  width: 34px; height: 34px; border-radius: 8px; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin-bottom: 10px;
}
.stat-number { font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: 700; color: #1a3a1a; }
.stat-unit { font-size: 0.75rem; font-weight: 400; color: #8a9a8a; margin-left: 4px; }
.stat-label { font-size: 0.76rem; color: #8a9a8a; margin-top: 2px; }
.stat-note { font-size: 0.74rem; color: #8a9a8a; margin-top: 4px; }

.badge-pill {
  display: inline-block; font-size: 0.68rem; font-weight: 700; padding: 2px 9px;
  border-radius: 12px; margin-top: 6px;
}
.badge-success { background: #e6efe0; color: #3a6b3a; }
.badge-warning { background: #faead0; color: #b8860b; }
.badge-danger { background: #fdecec; color: #a12525; }
.badge-info { background: #e3edf7; color: #2f6fa8; }

.content-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;
}
.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px; }
.surface-title { font-family: 'Playfair Display', serif; font-size: 1rem; color: #1a3a1a; margin: 0 0 14px; }

.rnd-row { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.rnd-avatar {
  width: 46px; height: 46px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; flex-shrink: 0;
}
.rnd-name { font-weight: 700; color: #1a3a1a; font-size: 0.9rem; margin: 0; }

.empty-note { font-size: 0.85rem; color: #9aaa9a; margin: 0 0 14px; }

.outline-btn {
  display: block; text-align: center; border: 1px solid #d5dad5; background: #fff;
  color: #1a3a1a; border-radius: 8px; padding: 10px; font-size: 0.85rem; font-weight: 600;
  text-decoration: none;
}

.screening-row {
  display: flex; justify-content: space-between; font-size: 0.85rem;
  padding: 9px 0; border-bottom: 1px solid #f0f0e6;
}
.screening-row:last-child { border-bottom: none; }
.screening-row span:first-child { color: #6a7a6a; }
.screening-row span:last-child { font-weight: 600; color: #1a3a1a; }
</style>
