<template>
  <div class="tracker-page">
    <div class="page-header">
      <h1 class="page-title">Progress Tracker</h1>
      <p class="page-sub">Your health journey over time, as recorded by your RND.</p>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="records.length">
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-icon"><Gauge :size="18" /></div>
          <div class="stat-number">{{ latest.weight_kg ? `${latest.weight_kg} kg` : '—' }}</div>
          <div class="stat-label">Latest Weight</div>
          <div v-if="weightDelta !== null" class="stat-delta" :class="weightDelta <= 0 ? 'down' : 'up'">
            {{ weightDelta <= 0 ? '↓' : '↑' }} {{ Math.abs(weightDelta).toFixed(1) }} kg total
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><HeartPulse :size="18" /></div>
          <div class="stat-number">{{ latest.blood_pressure || '—' }}</div>
          <div class="stat-label">Blood Pressure</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><Droplet :size="18" /></div>
          <div class="stat-number">{{ latest.blood_glucose ? `${latest.blood_glucose} mg/dL` : '—' }}</div>
          <div class="stat-label">Fasting Glucose</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon"><ClipboardCheck :size="18" /></div>
          <div class="stat-number">{{ latest.adherence_pct !== null ? `${latest.adherence_pct}%` : '—' }}</div>
          <div class="stat-label">Adherence</div>
        </div>
      </div>

      <div class="chart-grid">
        <div v-if="weightSeries.length > 1" class="chart-card">
          <h3 class="chart-title">Weight Trend (kg)</h3>
          <TrendLine :points="weightSeries" color="#1a3a1a" />
        </div>
        <div v-if="glucoseSeries.length > 1" class="chart-card">
          <h3 class="chart-title">Fasting Blood Glucose (mg/dL)</h3>
          <TrendLine :points="glucoseSeries" color="#c0392b" />
        </div>
      </div>

      <div class="surface">
        <h3 class="surface-title">Record History</h3>
        <div class="table-wrap">
          <table class="record-table">
            <thead>
              <tr><th>Date</th><th>Weight</th><th>BP</th><th>Glucose</th><th>Adherence</th><th>Notes</th></tr>
            </thead>
            <tbody>
              <tr v-for="rec in records" :key="rec.id">
                <td>{{ formatDate(rec.record_date) }}</td>
                <td>{{ rec.weight_kg ? `${rec.weight_kg} kg` : '—' }}</td>
                <td>{{ rec.blood_pressure || '—' }}</td>
                <td>{{ rec.blood_glucose ? `${rec.blood_glucose} mg/dL` : '—' }}</td>
                <td>{{ rec.adherence_pct !== null ? `${rec.adherence_pct}%` : '—' }}</td>
                <td class="notes-cell">{{ rec.rnd_notes || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">
      <div class="empty-icon"><LineChart :size="28" /></div>
      <p class="empty-title">No progress recorded yet</p>
      <p class="empty-desc">Your RND will log your weight, blood pressure, and other vitals here as you progress through your care plan.</p>
    </div>
  </div>
</template>

<script setup>
import { Gauge, HeartPulse, Droplet, ClipboardCheck, LineChart } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Progress Tracker' })

const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const records = ref([])

const sortedAsc = computed(() => [...records.value].reverse())
const latest = computed(() => records.value[0] || {})

const weightDelta = computed(() => {
  const withWeight = sortedAsc.value.filter(r => r.weight_kg != null)
  if (withWeight.length < 2) return null
  return Number(withWeight.at(-1).weight_kg) - Number(withWeight[0].weight_kg)
})

function seriesFor(field) {
  return sortedAsc.value
    .filter(r => r[field] != null)
    .map(r => ({ label: formatShortDate(r.record_date), value: Number(r[field]) }))
}
const weightSeries = computed(() => seriesFor('weight_kg'))
const glucoseSeries = computed(() => seriesFor('blood_glucose'))

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
function formatShortDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

async function loadRecords() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    records.value = await get('/client/progress/')
  } catch {
    errorMessage.value = 'Could not load your progress history. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadRecords)
</script>

<style scoped>
* { box-sizing: border-box; }

.tracker-page { font-family: 'Inter', sans-serif; }

.page-header { margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.stat-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 14px; margin-bottom: 20px;
}
.stat-card { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 18px; }
.stat-icon {
  width: 34px; height: 34px; border-radius: 8px; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin-bottom: 10px;
}
.stat-number { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #1a3a1a; }
.stat-label { font-size: 0.76rem; color: #8a9a8a; margin-top: 2px; }
.stat-delta { font-size: 0.74rem; margin-top: 4px; font-weight: 600; }
.stat-delta.down { color: #3a6b3a; }
.stat-delta.up { color: #b8860b; }

.chart-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-bottom: 20px; }
.chart-card { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px; }
.chart-title { font-family: 'Playfair Display', serif; font-size: 1rem; color: #1a3a1a; margin: 0 0 14px; }

.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px; }
.surface-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 14px; }

.table-wrap { overflow-x: auto; }
.record-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.record-table th {
  text-align: left; font-size: 0.7rem; letter-spacing: 0.04em; color: #8a9a8a;
  padding: 10px 12px; border-bottom: 1px solid #eceeec; font-weight: 700; text-transform: uppercase;
}
.record-table td { padding: 12px; border-bottom: 1px solid #f4f5f2; color: #4a5a4a; }
.record-table tr:last-child td { border-bottom: none; }
.notes-cell { color: #8a9a8a; font-style: italic; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; max-width: 400px; margin-left: auto; margin-right: auto; }
</style>
