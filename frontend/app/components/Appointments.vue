<template>
  <div class="appointments-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Appointments</h1>
        <p class="page-sub">{{ isRnd ? 'Manage your upcoming and past consultations.' : 'Your upcoming and past consultations.' }}</p>
      </div>
      <NuxtLink v-if="!isRnd" to="/book-appointment" class="book-btn">Book Appointment</NuxtLink>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <!-- FILTER TABS -->
    <div v-if="appointments.length" class="filter-tabs">
      <button
        v-for="f in filters"
        :key="f.label"
        class="filter-tab"
        :class="{ active: activeFilter === f.label }"
        @click="activeFilter = f.label"
      >
        {{ f.label }}
      </button>
    </div>

    <!-- LOADING STATE -->
    <div v-if="isLoading" class="empty-state">
      <p class="empty-title">Loading appointments…</p>
    </div>

    <!-- APPOINTMENT LIST -->
    <div v-else-if="appointments.length" class="appt-list">
      <div
        v-if="filteredAppointments.length"
        v-for="appt in filteredAppointments"
        :key="appt.id"
        class="appt-card"
        :class="{ 'appt-completed': appt.status === 'completed' }"
      >
        <div class="appt-date" :class="{ 'date-muted': appt.status === 'completed' }">
          <span class="appt-day">{{ appt.day }}</span>
          <span class="appt-month">{{ appt.month }}</span>
        </div>
        <div class="appt-avatar" :style="{ background: appt.avatarColor }">{{ appt.initials }}</div>
        <div class="appt-info">
          <p class="appt-name">
            {{ appt.otherPartyName }}
            <span class="appt-status-pill" :class="statusPillClass(appt.status)">{{ statusLabel(appt.status) }}</span>
          </p>
          <p class="appt-detail">{{ appt.detail }}</p>
        </div>
        <div class="appt-action">
          <span v-if="actionError[appt.id]" class="appt-note">{{ actionError[appt.id] }}</span>
          <template v-if="isRnd">
            <button v-if="appt.status === 'pending'" class="confirm-btn" :disabled="busyId === appt.id" @click="confirmAppointment(appt)">Confirm</button>
            <button v-if="appt.status === 'pending'" class="decline-btn" :disabled="busyId === appt.id" @click="cancelAppointment(appt)">Decline</button>
            <NuxtLink v-if="appt.status === 'confirmed' && appt.hasVideoRoom" :to="`/consultation-room/${appt.id}`" class="join-btn">Join Call</NuxtLink>
            <button v-if="appt.status === 'confirmed'" class="start-session-btn" :disabled="busyId === appt.id" @click="completeAppointment(appt)">Mark Completed</button>
            <button v-if="appt.status === 'confirmed'" class="decline-btn" :disabled="busyId === appt.id" @click="cancelAppointment(appt)">Cancel</button>
            <button v-if="appt.status === 'confirmed' || appt.status === 'completed'" class="chart-btn" @click="navigateTo(`/client-detail/${appt.relationshipId}`)">View Chart</button>
          </template>
          <template v-else>
            <NuxtLink v-if="appt.status === 'confirmed' && appt.hasVideoRoom" :to="`/consultation-room/${appt.id}`" class="join-btn">Join Call</NuxtLink>
            <button v-if="appt.status === 'pending' || appt.status === 'confirmed'" class="decline-btn" :disabled="busyId === appt.id" @click="cancelAppointment(appt)">Cancel</button>
          </template>
        </div>
      </div>
      <p v-if="!filteredAppointments.length" class="empty-text">No appointments match this filter.</p>
    </div>

    <!-- EMPTY STATE: no appointments at all -->
    <div v-else class="empty-state">
      <div class="empty-icon"><CalendarDays :size="28" /></div>
      <p class="empty-title">No appointments yet</p>
      <p class="empty-desc">{{ isRnd ? "Once patients book sessions with you, they'll show up here." : "Once you book a session with an RND, it'll show up here." }}</p>
      <NuxtLink v-if="!isRnd" to="/book-appointment" class="book-btn">Book Appointment</NuxtLink>
    </div>
  </div>
</template>

<script setup>
import { CalendarDays } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Appointments' })

const auth = useAuthStore()
const { get, patch } = useApi()

const isRnd = computed(() => auth.user?.role === 'rnd')

const activeFilter = ref('All')
const isLoading = ref(true)
const errorMessage = ref('')
const busyId = ref(null)
const actionError = reactive({})

const filters = [
  { label: 'All' },
  { label: 'Pending Confirmation' },
  { label: 'Confirmed' },
  { label: 'Completed' },
  { label: 'Cancelled' }
]

const AVATAR_COLORS = ['#1e4a26', '#3a6b3a', '#D4A017', '#6a8a6a', '#8a6a3a']

function colorForId(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}

function initialsFor(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
}

const rawAppointments = ref([])

const appointments = computed(() => rawAppointments.value.map((appt) => {
  const otherParty = isRnd.value ? appt.relationship.client : appt.relationship.rnd
  const scheduled = new Date(appt.scheduled_at)
  return {
    id: appt.id,
    relationshipId: appt.relationship.id,
    status: appt.status,
    otherPartyName: `${otherParty.first_name} ${otherParty.last_name}`,
    initials: initialsFor(otherParty),
    avatarColor: colorForId(otherParty.id),
    day: scheduled.toLocaleDateString('en-US', { day: 'numeric' }),
    month: scheduled.toLocaleDateString('en-US', { month: 'short' }).toUpperCase(),
    detail: `${scheduled.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })} · ${scheduled.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })} · ${appt.type.replace('_', ' ')}`,
    type: appt.type,
    hasVideoRoom: Boolean(appt.video_session_url),
  }
}))

const filteredAppointments = computed(() => {
  if (activeFilter.value === 'All') return appointments.value
  if (activeFilter.value === 'Pending Confirmation') {
    return appointments.value.filter(a => a.status === 'pending')
  }
  const map = { Confirmed: 'confirmed', Completed: 'completed', Cancelled: 'cancelled' }
  return appointments.value.filter(a => a.status === map[activeFilter.value])
})

function statusLabel(status) {
  return { pending: 'Pending Confirmation', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }[status] || status
}

function statusPillClass(status) {
  return { pending: 'pending', confirmed: 'confirmed', completed: 'completed', cancelled: 'awaiting' }[status] || ''
}

async function loadAppointments() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const path = isRnd.value ? '/rnd/appointments/' : '/client/appointments/'
    rawAppointments.value = await get(path)
  } catch {
    errorMessage.value = 'Could not load appointments. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

async function runTransition(appt, path) {
  busyId.value = appt.id
  delete actionError[appt.id]
  try {
    await patch(path)
    await loadAppointments()
  } catch (error) {
    actionError[appt.id] = error?.data?.detail || 'Action failed. Please try again.'
  } finally {
    busyId.value = null
  }
}

function confirmAppointment(appt) {
  runTransition(appt, `/rnd/appointments/${appt.id}/confirm/`)
}

function completeAppointment(appt) {
  runTransition(appt, `/rnd/appointments/${appt.id}/complete/`)
}

function cancelAppointment(appt) {
  const path = isRnd.value ? `/rnd/appointments/${appt.id}/cancel/` : `/client/appointments/${appt.id}/cancel/`
  runTransition(appt, path)
}

onMounted(loadAppointments)
</script>

<style scoped>
* { box-sizing: border-box; }

.appointments-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.form-error {
  background: #fdecec;
  border: 1px solid #f3b8b8;
  color: #a12525;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.85rem;
  margin: 0 0 16px;
}

/* FILTER TABS */
.filter-tabs { display: flex; gap: 10px; margin-bottom: 20px; }
.filter-tab {
  border: 1px solid #e5e8e5; background: #fff; color: #4a5a4a;
  border-radius: 20px; padding: 9px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.filter-tab.active { background: #14301a; color: #fff; border-color: #14301a; }

/* APPOINTMENT LIST */
.appt-list { display: flex; flex-direction: column; gap: 16px; }
.appt-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px 22px;
  display: flex; align-items: center; gap: 16px;
}
.appt-card.appt-completed { opacity: 0.7; }

.appt-date {
  width: 52px; height: 52px; border-radius: 8px; background: #eef3ec;
  display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0;
}
.appt-date.date-muted { background: #eceeec; }
.appt-day { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #1a3a1a; line-height: 1; }
.appt-month { font-size: 0.62rem; letter-spacing: 0.05em; color: #6a7a6a; margin-top: 2px; }

.appt-avatar {
  width: 32px; height: 32px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;
}

.appt-info { flex: 1; }
.appt-name { display: flex; align-items: center; gap: 10px; font-size: 0.95rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.appt-status-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.appt-status-pill.confirmed { background: #e6efe0; color: #3a6b3a; }
.appt-status-pill.awaiting { background: #eceeec; color: #7a8a7a; }
.appt-status-pill.pending { background: #faead0; color: #b8860b; }
.appt-status-pill.completed { background: #eceeec; color: #7a8a7a; }
.appt-detail { font-size: 0.8rem; color: #6a7a6a; margin: 0; }

.appt-action { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.appt-note { font-size: 0.82rem; color: #a12525; background: #fdecec; padding: 10px 16px; border-radius: 8px; max-width: 320px; text-align: right; }

.start-session-btn, .confirm-btn, .join-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 10px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; white-space: nowrap;
  text-decoration: none; display: inline-block;
}
.start-session-btn:disabled, .confirm-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.decline-btn {
  background: none; border: none; color: #8a9a8a; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.decline-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.chart-btn, .reschedule-btn {
  border: 1px solid #d5dad5; background: #fff; color: #2a2a2a;
  border-radius: 8px; padding: 10px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer; white-space: nowrap;
}

/* EMPTY STATE */
.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0 0 16px; }
.empty-text { font-size: 0.85rem; color: #9aaa9a; padding: 20px; text-align: center; }

.book-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 10px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer;
  white-space: nowrap; text-decoration: none; display: inline-block;
}
</style>
