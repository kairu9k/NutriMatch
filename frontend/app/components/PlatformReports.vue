<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-stat-grid">
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><CalendarCheck :size="17" /></div>
        <p class="nm-stat-value">{{ stats.total_consultations }}</p>
        <p class="nm-stat-label">Consultations completed</p>
        <p class="nm-stat-note">All time</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon gold"><Banknote :size="17" /></div>
        <p class="nm-stat-value">{{ peso(stats.gross_revenue) }}</p>
        <p class="nm-stat-label">Payments this month</p>
        <p class="nm-stat-note">{{ peso(stats.commissions) }} commission</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><Stethoscope :size="17" /></div>
        <p class="nm-stat-value">{{ stats.active_rnds }}</p>
        <p class="nm-stat-label">Active RNDs</p>
        <p class="nm-stat-note">{{ stats.pending_verif }} waiting for review</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><Users :size="17" /></div>
        <p class="nm-stat-value">{{ stats.clients }}</p>
        <p class="nm-stat-label">Active clients</p>
        <p class="nm-stat-note" :class="{ good: stats.new_registrations }">{{ stats.new_registrations }} new accounts in 30 days</p>
      </div>
    </div>

    <div class="nm-panel">
      <div class="nm-panel-head">
        <div>
          <h2 class="nm-panel-title">RND performance</h2>
          <p class="nm-panel-sub">Approved RNDs by completed consultations</p>
        </div>
      </div>
      <p v-if="loading" class="nm-muted">Loading…</p>
      <div v-else-if="!rnds.length" class="nm-empty">
        <BarChart3 :size="28" />
        <p>No approved RNDs yet.</p>
      </div>
      <div v-else class="nm-table-wrap">
        <table class="nm-table stack">
          <thead>
            <tr>
              <th>RND</th>
              <th class="nm-num">Active patients</th>
              <th class="nm-num">Consultations</th>
              <th class="nm-num">Revenue</th>
              <th>Rating</th>
              <th style="width: 22%">Share of consultations</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rnds" :key="r.id" class="clickable" @click="navigateTo(`/users/${r.id}`)">
              <td>
                <div style="display: flex; align-items: center; gap: 10px; min-width: 0">
                  <img v-if="r.profile_photo" :src="r.profile_photo" class="nm-avatar" alt="" />
                  <span v-else class="nm-avatar">{{ userInitials(r.first_name, r.last_name) }}</span>
                  <div style="min-width: 0">
                    <p class="nm-row-title">{{ r.first_name }} {{ r.last_name }}</p>
                    <p class="nm-row-sub">{{ r.specialization }}</p>
                  </div>
                </div>
              </td>
              <td data-label="Patients" class="nm-num">{{ r.patients }}</td>
              <td data-label="Consultations" class="nm-num">{{ r.consultations }}</td>
              <td data-label="Revenue" class="nm-num">{{ peso(r.revenue) }}</td>
              <td data-label="Rating">{{ r.average_rating ? `★ ${r.average_rating}` : '—' }}</td>
              <td data-label="Share">
                <div class="bar"><span :style="{ width: `${share(r)}%` }" /></div>
                <span class="nm-row-sub">{{ share(r) }}%</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Banknote, BarChart3, CalendarCheck, Stethoscope, Users } from 'lucide-vue-next'

const { get } = useApi()

const loading = ref(true)
const error = ref('')
const stats = ref({ active_rnds: 0, clients: 0, new_registrations: 0, total_consultations: 0, gross_revenue: 0, commissions: 0, pending_verif: 0 })
const rnds = ref([])

onMounted(async () => {
  try {
    const [s, list] = await Promise.all([get('/admin/platform-stats/'), get('/admin/rnds/')])
    stats.value = s
    rnds.value = list.filter(r => r.is_verified).sort((a, b) => b.consultations - a.consultations)
  } catch {
    error.value = 'Could not load report data. Please refresh the page.'
  } finally {
    loading.value = false
  }
})

const totalConsults = computed(() => rnds.value.reduce((s, r) => s + (r.consultations || 0), 0))
function share(r) {
  return totalConsults.value ? Math.round((r.consultations / totalConsults.value) * 100) : 0
}
</script>

<style scoped>
.bar { height: 6px; background: #eef3ec; border-radius: 4px; overflow: hidden; margin-bottom: 3px; }
.bar span { display: block; height: 100%; background: #1f8f5c; border-radius: 4px; }
@media (max-width: 640px) {
  .bar { display: inline-block; width: 120px; vertical-align: middle; margin: 0 6px 0 0; }
}
</style>
