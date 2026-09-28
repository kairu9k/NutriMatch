<template>
  <div class="tracker-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Progress Tracker</h1>
        <p class="page-sub">Your health journey over time, as recorded by your RND.</p>
      </div>
      <div v-if="records.length" class="range-dropdown" ref="rangeDropdownEl">
        <button class="range-trigger" @click="rangeDropdownOpen = !rangeDropdownOpen">
          {{ selectedRange }} <ChevronDown :size="14" :class="{ open: rangeDropdownOpen }" />
        </button>
        <div v-if="rangeDropdownOpen" class="range-menu">
          <button v-for="r in ranges" :key="r.label" class="range-item" :class="{ active: selectedRange === r.label }" @click="selectedRange = r.label; rangeDropdownOpen = false">{{ r.label }}</button>
        </div>
      </div>
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
          <div class="stat-icon"><Activity :size="18" /></div>
          <div class="stat-number">{{ latest.bmi ?? '—' }}</div>
          <div class="stat-label">Latest BMI</div>
          <div v-if="bmiDelta !== null" class="stat-delta" :class="bmiDelta <= 0 ? 'down' : 'up'">
            {{ bmiDelta <= 0 ? '↓' : '↑' }} {{ Math.abs(bmiDelta).toFixed(1) }} since start
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
          <div v-if="glucoseDelta !== null" class="stat-delta" :class="glucoseDelta <= 0 ? 'down' : 'up'">
            {{ glucoseDelta <= 0 ? '↓' : '↑' }} {{ Math.abs(glucoseDelta).toFixed(0) }} mg/dL {{ glucoseDelta <= 0 ? 'improved' : '' }}
          </div>
        </div>
      </div>

      <div class="chart-grid">
        <div v-if="weightSeries.length > 1" class="chart-card">
          <h3 class="chart-title">Weight Trend (kg)</h3>
          <TrendLine :points="weightSeries" color="#1a3a1a" />
        </div>
        <div v-if="bmiSeries.length > 1" class="chart-card">
          <h3 class="chart-title gold">BMI Trend</h3>
          <TrendLine :points="bmiSeries" color="#D4A017" />
        </div>
        <div v-if="systolicSeries.length > 1" class="chart-card">
          <h3 class="chart-title">Blood Pressure (mmHg)</h3>
          <svg viewBox="0 0 400 120" class="bp-svg" preserveAspectRatio="none">
            <path :d="bpLinePath(systolicSeries)" stroke="#1a3a1a" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
            <circle v-for="(p, i) in bpCoords(systolicSeries)" :key="'s'+i" :cx="p.x" :cy="p.y" r="3.5" fill="#1a3a1a" />
            <path :d="bpLinePath(diastolicSeries)" stroke="#D4A017" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
            <circle v-for="(p, i) in bpCoords(diastolicSeries)" :key="'d'+i" :cx="p.x" :cy="p.y" r="3.5" fill="#D4A017" />
          </svg>
          <div class="bp-labels">
            <span v-for="p in systolicSeries" :key="p.label">{{ p.label }}</span>
          </div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background:#1a3a1a"></span> Systolic</span>
            <span class="legend-item"><span class="legend-dot" style="background:#D4A017"></span> Diastolic</span>
          </div>
        </div>
        <div v-if="glucoseSeries.length > 1" class="chart-card">
          <h3 class="chart-title red">Fasting Blood Glucose (mg/dL)</h3>
          <TrendLine :points="glucoseSeries" color="#c0392b" />
        </div>
      </div>

      <div class="surface">
        <h3 class="surface-title">Record History</h3>
        <div class="table-wrap">
          <table class="record-table">
            <thead>
              <tr><th>Date</th><th>Weight</th><th>BMI</th><th>BP</th><th>Glucose</th><th>Adherence</th><th>Notes</th></tr>
            </thead>
            <tbody>
              <tr v-for="rec in filteredRecords" :key="rec.id">
                <td>{{ formatDate(rec.record_date) }}</td>
                <td>{{ rec.weight_kg ? `${rec.weight_kg} kg` : '—' }}</td>
                <td>{{ rec.bmi ?? '—' }}</td>
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
import { Gauge, Activity, HeartPulse, Droplet, LineChart, ChevronDown } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Progress Tracker' })

const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const records = ref([])

/* ---------- Date range filter ---------- */
const ranges = [
  { label: 'Last 3 Months', months: 3 },
  { label: 'Last 6 Months', months: 6 },
  { label: 'Last Year', months: 12 },
]
const selectedRange = ref('Last 6 Months')
const rangeDropdownOpen = ref(false)
const rangeDropdownEl = ref(null)
function handleClickOutside(e) {
  if (rangeDropdownEl.value && !rangeDropdownEl.value.contains(e.target)) rangeDropdownOpen.value = false
}
onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))

const filteredRecords = computed(() => {
  const months = ranges.find(r => r.label === selectedRange.value)?.months || 6
  const cutoff = new Date()
  cutoff.setMonth(cutoff.getMonth() - months)
  return records.value.filter(r => new Date(r.record_date) >= cutoff)
})

const sortedAsc = computed(() => [...filteredRecords.value].reverse())
const latest = computed(() => filteredRecords.value[0] || {})

function deltaFor(field) {
  const withField = sortedAsc.value.filter(r => r[field] != null)
  if (withField.length < 2) return null
  return Number(withField.at(-1)[field]) - Number(withField[0][field])
}
const weightDelta = computed(() => deltaFor('weight_kg'))
const bmiDelta = computed(() => deltaFor('bmi'))
const glucoseDelta = computed(() => deltaFor('blood_glucose'))

function seriesFor(field) {
  return sortedAsc.value
    .filter(r => r[field] != null)
    .map(r => ({ label: formatShortDate(r.record_date), value: Number(r[field]) }))
}
const weightSeries = computed(() => seriesFor('weight_kg'))
const bmiSeries = computed(() => seriesFor('bmi'))
const glucoseSeries = computed(() => seriesFor('blood_glucose'))

/* Blood pressure is stored as a single "120/80" string — split for the
   dual-line chart, display data only, not a clinical calculation. */
function bpPart(record, index) {
  if (!record.blood_pressure || !record.blood_pressure.includes('/')) return null
  const part = Number(record.blood_pressure.split('/')[index])
  return Number.isFinite(part) ? part : null
}
const systolicSeries = computed(() =>
  sortedAsc.value
    .filter(r => bpPart(r, 0) != null)
    .map(r => ({ label: formatShortDate(r.record_date), value: bpPart(r, 0) }))
)
const diastolicSeries = computed(() =>
  sortedAsc.value
    .filter(r => bpPart(r, 1) != null)
    .map(r => ({ label: formatShortDate(r.record_date), value: bpPart(r, 1) }))
)

function bpCoords(series) {
  const width = 400, height = 120, padding = 12
  const allValues = [...systolicSeries.value, ...diastolicSeries.value].map(p => p.value)
  const min = Math.min(...allValues)
  const max = Math.max(...allValues)
  const range = (max - min) || 1
  const n = series.length
  return series.map((p, i) => ({
    x: n === 1 ? width / 2 : padding + (i / (n - 1)) * (width - padding * 2),
    y: height - padding - ((p.value - min) / range) * (height - padding * 2),
  }))
}
function bpLinePath(series) {
  const coords = bpCoords(series)
  return coords.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.x},${c.y}`).join(' ')
}

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

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.range-dropdown { position: relative; }
.range-trigger { display: inline-flex; align-items: center; gap: 6px; border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 9px 14px; font-size: 0.83rem; font-weight: 600; cursor: pointer; }
.range-trigger svg.open { transform: rotate(180deg); }
.range-menu { position: absolute; top: calc(100% + 6px); right: 0; z-index: 20; min-width: 160px; background: #fff; border: 1px solid #eceeec; border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,0.1); padding: 6px; }
.range-item { display: block; width: 100%; text-align: left; border: none; background: none; padding: 9px 12px; border-radius: 8px; font-size: 0.83rem; font-weight: 600; color: #4a5a4a; cursor: pointer; }
.range-item:hover { background: #f7f9f7; }
.range-item.active { background: #eef3ee; color: #14301a; }

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
.chart-title.gold { color: #b8860b; }
.chart-title.red { color: #c0392b; }

.bp-svg { width: 100%; height: 120px; display: block; overflow: visible; }
.bp-labels { display: flex; justify-content: space-between; font-size: 0.68rem; color: #9aaa9a; margin-top: 6px; }
.chart-legend { display: flex; gap: 12px; margin-top: 10px; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.74rem; color: #6a7a6a; font-weight: 500; }
.legend-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }

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
