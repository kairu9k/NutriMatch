<template>
  <div class="room-shell">
    <div class="call-top">
      <div class="brand">Nutri<span class="gold">Match</span></div>
      <p v-if="appointment" class="appt-label">
        {{ isRnd ? `${appointment.relationship.client.first_name} ${appointment.relationship.client.last_name}` : `RND ${appointment.relationship.rnd.first_name} ${appointment.relationship.rnd.last_name}` }}
      </p>
      <NuxtLink to="/appointments" class="exit-btn"><ArrowLeft :size="15" /> Exit</NuxtLink>
    </div>

    <div class="call-body">
      <div class="video-col">
        <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
        <div v-if="isLoading" class="placeholder-text">Loading…</div>
        <div v-else-if="!appointment" class="placeholder-text">Appointment not found.</div>
        <div v-else-if="!appointment.video_session_url" class="no-room">
          <VideoOff :size="28" />
          <p>No video room has been set up for this appointment yet.</p>
        </div>
        <iframe
          v-else
          :src="appointment.video_session_url"
          class="video-frame"
          allow="camera; microphone; fullscreen; display-capture; autoplay"
        />
      </div>

      <div class="side-panel">
        <h3 class="side-title">Pre-Consultation Screening</h3>
        <div v-if="isLoadingScreening" class="placeholder-text small">Loading…</div>
        <template v-else-if="screening">
          <div class="screening-row"><span>BMI</span><span>{{ screening.bmi }} <span class="badge-pill" :class="bmiBadgeClass">{{ screening.bmi_category }}</span></span></div>
          <div class="screening-row"><span>NRS-2002</span><span>{{ screening.nrs_score ?? '—' }}</span></div>
          <div class="screening-row"><span>TDEE</span><span>{{ screening.tdee_kcal ? Math.round(screening.tdee_kcal) + ' kcal' : '—' }}</span></div>
        </template>
        <p v-else class="empty-note">No screening linked to this appointment.</p>

        <NuxtLink v-if="isRnd && appointment" :to="`/ncp-records?relationship=${appointment.relationship.id}`" class="outline-btn">
          Open NCP Record
        </NuxtLink>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowLeft, VideoOff } from 'lucide-vue-next'

const route = useRoute()
const auth = useAuthStore()
const { get } = useApi()

const isRnd = computed(() => auth.user?.role === 'rnd')

const isLoading = ref(true)
const isLoadingScreening = ref(true)
const errorMessage = ref('')
const appointment = ref(null)
const screening = ref(null)

const bmiBadgeClass = computed(() => {
  const cat = (screening.value?.bmi_category || '').toLowerCase()
  if (cat.includes('normal')) return 'badge-success'
  if (cat.includes('underweight')) return 'badge-info'
  return 'badge-warning'
})

async function loadAppointment() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const path = isRnd.value ? `/rnd/appointments/${route.params.id}/` : `/client/appointments/${route.params.id}/`
    appointment.value = await get(path)
  } catch {
    errorMessage.value = 'Could not load this appointment.'
  } finally {
    isLoading.value = false
  }
}

async function loadScreening() {
  isLoadingScreening.value = true
  try {
    screening.value = await get(`/client/screening/${route.params.id}/`)
  } catch {
    screening.value = null
  } finally {
    isLoadingScreening.value = false
  }
}

onMounted(() => {
  loadAppointment()
  loadScreening()
})
</script>

<style scoped>
* { box-sizing: border-box; }

.room-shell {
  height: 100vh; display: flex; flex-direction: column;
  background: #0D1F18; font-family: 'Inter', sans-serif;
}

.call-top {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 22px; color: #fff; flex-shrink: 0;
}
.brand { font-weight: 700; font-family: 'Playfair Display', serif; }
.gold { color: #D4A017; }
.appt-label { font-size: 0.85rem; color: #c9d9c9; margin: 0; }
.exit-btn {
  display: flex; align-items: center; gap: 6px; text-decoration: none;
  background: rgba(255,255,255,0.1); color: #fff; padding: 7px 14px;
  border-radius: 20px; font-size: 0.8rem; font-weight: 600;
}

.call-body { flex: 1; display: flex; min-height: 0; }
.video-col { flex: 1; position: relative; display: flex; align-items: center; justify-content: center; padding: 0 0 0 0; }
.video-frame { width: 100%; height: 100%; border: none; }

.placeholder-text { color: #9ab09a; font-size: 0.9rem; }
.placeholder-text.small { font-size: 0.82rem; }
.form-error { color: #f3b8b8; font-size: 0.85rem; }

.no-room {
  display: flex; flex-direction: column; align-items: center; gap: 12px;
  color: #9ab09a; font-size: 0.88rem; text-align: center; max-width: 320px;
}

.side-panel {
  width: 300px; background: #f9f9f5; padding: 20px; flex-shrink: 0;
  display: flex; flex-direction: column; gap: 12px; overflow-y: auto;
}
.side-title { font-family: 'Playfair Display', serif; font-size: 1rem; color: #1a3a1a; margin: 0; }

.screening-row {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 0.85rem; padding: 9px 0; border-bottom: 1px solid #eceeec;
}
.screening-row span:first-child { color: #6a7a6a; }
.screening-row span:last-child { font-weight: 600; color: #1a3a1a; display: flex; align-items: center; gap: 6px; }

.badge-pill { font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: 10px; }
.badge-success { background: #e6efe0; color: #3a6b3a; }
.badge-warning { background: #faead0; color: #b8860b; }
.badge-info { background: #e3edf7; color: #2f6fa8; }

.empty-note { font-size: 0.83rem; color: #9aaa9a; margin: 0; }

.outline-btn {
  display: block; text-align: center; text-decoration: none; border: 1px solid #d5dad5;
  background: #fff; color: #1a3a1a; border-radius: 8px; padding: 10px;
  font-size: 0.83rem; font-weight: 600; margin-top: auto;
}

@media (max-width: 900px) {
  .side-panel { display: none; }
}
</style>
