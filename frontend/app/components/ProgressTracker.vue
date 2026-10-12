<template>
  <div class="tracker-page">
    <div class="page-header">
      <div>
        <p class="page-sub">Your health journey — readings from your RND and the ones you log at home.</p>
      </div>
      <div class="header-actions">
        <select v-if="records.length" v-model="selectedRange" class="nm-select" aria-label="Date range">
          <option v-for="r in ranges" :key="r.label" :value="r.label">{{ r.label }}</option>
        </select>
        <button v-if="records.length" type="button" class="nm-btn-outline nm-btn-sm" @click="printReport"><Printer :size="14" /> Print / PDF</button>
        <button type="button" class="nm-btn-dark nm-btn-sm" @click="openLog"><Plus :size="14" /> Log a reading</button>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="printError" class="form-error">{{ printError }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-if="!isLoading && records.length">
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
        <!-- MEAL-PLAN ADHERENCE (weekly, from the client's meal logs) -->
        <div v-if="adherence.length" class="chart-card">
          <div class="adh-head">
            <div>
              <h3 class="chart-title flush">How well I followed my meal plan</h3>
              <p class="adh-sub">Share of planned meals followed each week (partly followed counts half) · goal 80%</p>
            </div>
            <div v-if="thisWeek?.pct != null" class="adh-now"><strong>{{ thisWeek.pct }}%</strong><span>this week</span></div>
          </div>
          <svg class="adh-svg" viewBox="0 0 400 140" role="img" :aria-label="`Weekly meal-plan adherence, this week ${thisWeek?.pct ?? 'no data'} percent`">
            <line x1="0" :y1="adhY(80)" x2="400" :y2="adhY(80)" class="adh-goal" />
            <text x="398" :y="adhY(80) - 4" text-anchor="end" class="adh-goal-label">80% goal</text>
            <line x1="0" :y1="adhY(0)" x2="400" :y2="adhY(0)" class="adh-base" />
            <g v-for="(w, i) in adherence" :key="w.end">
              <rect :x="adhX(i)" :y="adhY(w.pct ?? 0)" :width="adhBarW" :height="Math.max(0, adhY(0) - adhY(w.pct ?? 0))"
                    :rx="w.pct ? 4 : 0" class="adh-bar" :class="{ empty: w.pct == null }">
                <title>{{ weekLabel(w) }}: {{ w.pct != null ? `${w.pct}% (${w.logged} of ${w.planned} meals logged)` : 'no meals planned' }}</title>
              </rect>
              <rect v-if="w.pct" :x="adhX(i)" :y="adhY(0) - 4" :width="adhBarW" height="4" class="adh-bar" />
              <text v-if="i === adherence.length - 1 && w.pct != null" :x="adhX(i) + adhBarW / 2" :y="adhY(w.pct) - 5" text-anchor="middle" class="adh-val">{{ w.pct }}%</text>
              <text :x="adhX(i) + adhBarW / 2" y="136" text-anchor="middle" class="adh-x">{{ shortDay(w.end) }}</text>
            </g>
          </svg>
        </div>
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
        <div v-if="hba1cSeries.length > 1" class="chart-card">
          <h3 class="chart-title">HbA1c (%)</h3>
          <TrendLine :points="hba1cSeries" color="#2f6fa8" />
        </div>
      </div>

      <div class="surface">
        <h3 class="surface-title">Record History</h3>
        <div class="table-wrap">
          <table class="record-table">
            <thead>
              <tr><th>Date</th><th>By</th><th>Weight</th><th>BMI</th><th>BP</th><th>Glucose</th><th>Adherence</th><th>HbA1c</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="rec in filteredRecords" :key="rec.id">
                <td>{{ formatDate(rec.record_date) }}<span v-if="rec.client_notes" class="rec-note">{{ rec.client_notes }}</span></td>
                <td><span class="src" :class="rec.source">{{ rec.source === 'client' ? 'You' : 'RND' }}</span></td>
                <td>{{ rec.weight_kg ? `${rec.weight_kg} kg` : '—' }}</td>
                <td>{{ rec.bmi ?? '—' }}</td>
                <td>{{ rec.blood_pressure || '—' }}</td>
                <td>{{ rec.blood_glucose ? `${rec.blood_glucose} mg/dL` : '—' }}</td>
                <td>{{ rec.adherence_pct !== null ? `${rec.adherence_pct}%` : '—' }}</td>
                <td>{{ rec.hba1c ? `${rec.hba1c}%` : "—" }}</td>
                <td><button v-if="rec.source === 'client'" type="button" class="rec-x" aria-label="Delete this reading" @click="removeReading(rec)"><X :size="13" /></button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-icon"><LineChart :size="28" /></div>
      <p class="empty-title">No progress recorded yet</p>
      <p class="empty-desc">Your RND records your weight, blood pressure and other vitals at each consultation. You can also log your own readings at home with "Log a reading".</p>
    </div>

    <!-- LOG A READING (self-reported, POST /api/client/progress/) -->
    <div v-if="logOpen" class="nm-modal-overlay" @click.self="logOpen = false">
      <form class="nm-modal log-modal" @submit.prevent="saveReading">
        <h3 class="nm-modal-title">Log a reading</h3>
        <p class="nm-modal-text">From your scale, BP monitor or glucometer at home. It's marked "self-reported", and your RND sees it on your chart.</p>
        <div class="log-grid">
          <label class="log-field"><span>Date</span><input v-model="log.record_date" type="date" class="nm-input" :max="todayIso" /></label>
          <label class="log-field"><span>Weight (kg)</span><input v-model="log.weight_kg" type="number" step="0.1" min="25" max="300" class="nm-input" placeholder="e.g. 68.5" /></label>
          <div class="log-field"><span>Blood pressure (mmHg)</span>
            <div class="bp-pair">
              <input v-model="log.sys" type="number" min="60" max="260" class="nm-input" placeholder="120" aria-label="Systolic" />
              <span>/</span>
              <input v-model="log.dia" type="number" min="30" max="160" class="nm-input" placeholder="80" aria-label="Diastolic" />
            </div>
          </div>
          <label class="log-field"><span>Fasting glucose (mg/dL)</span><input v-model="log.blood_glucose" type="number" step="1" min="20" max="600" class="nm-input" placeholder="e.g. 110" /></label>
          <label class="log-field"><span>HbA1c (%)</span><input v-model="log.hba1c" type="number" step="0.1" min="3" max="20" class="nm-input" placeholder="e.g. 6.8" /></label>
          <label class="log-field wide"><span>Note <em>(optional)</em></span><input v-model="log.client_notes" class="nm-input" maxlength="500" placeholder="e.g. Morning, before breakfast" /></label>
        </div>
        <p v-if="logError" class="form-error" style="margin: 10px 0 0">{{ logError }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="logOpen = false">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="logSaving">{{ logSaving ? 'Saving…' : 'Save reading' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { Gauge, Activity, HeartPulse, Droplet, LineChart, Plus, Printer, X } from 'lucide-vue-next'
import { printDocument } from '~/utils/printDoc'

definePageMeta({ layout: 'dashboard', title: 'Progress Tracker' })

const { get, post, del } = useApi()

/* ---------- weekly meal-plan adherence (GET /api/client/adherence/) ---------- */
const adherence = ref([])
const thisWeek = computed(() => adherence.value[adherence.value.length - 1] || null)
async function loadAdherence() {
  try {
    const weeks = (await get('/client/adherence/')).weeks
    const first = weeks.findIndex(w => w.planned)
    adherence.value = first === -1 ? [] : weeks.slice(first)
  } catch { adherence.value = [] }
}
const ADH_TOP = 12
const ADH_BOTTOM = 120
const adhY = pct => ADH_BOTTOM - (Math.min(100, Math.max(0, pct)) / 100) * (ADH_BOTTOM - ADH_TOP)
const adhBarW = computed(() => Math.min(28, 400 / Math.max(1, adherence.value.length) - 16))
const adhX = i => (400 / adherence.value.length) * i + (400 / adherence.value.length - adhBarW.value) / 2
const shortDay = iso => new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { month: 'short', day: 'numeric' })
const weekLabel = w => `${shortDay(w.start)} – ${shortDay(w.end)}`

/* ---------- log a reading (self-reported) ---------- */
const todayIso = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' })
const logOpen = ref(false)
const logSaving = ref(false)
const logError = ref('')
const log = reactive({})
function openLog() {
  Object.assign(log, { record_date: todayIso, weight_kg: '', sys: '', dia: '', blood_glucose: '', hba1c: '', client_notes: '' })
  logError.value = ''
  logOpen.value = true
}
async function saveReading() {
  logError.value = ''
  const sys = String(log.sys ?? '').trim()
  const dia = String(log.dia ?? '').trim()
  if ((sys && !dia) || (!sys && dia)) { logError.value = 'Enter both blood pressure numbers, e.g. 120 / 80.'; return }
  const body = { record_date: log.record_date, client_notes: log.client_notes.trim() || null }
  for (const k of ['weight_kg', 'blood_glucose', 'hba1c']) if (String(log[k] ?? '').trim() !== '') body[k] = log[k]
  if (sys) body.blood_pressure = `${sys}/${dia}`
  logSaving.value = true
  try {
    await post('/client/progress/', body)
    logOpen.value = false
    await loadRecords()
  } catch (e) {
    const d = e?.data || {}
    const first = Object.values(d).flat()[0]
    logError.value = typeof first === 'string' ? first : 'Could not save this reading.'
  } finally {
    logSaving.value = false
  }
}
async function removeReading(rec) {
  try {
    await del(`/client/progress/${rec.id}/`)
    records.value = records.value.filter(r => r.id !== rec.id)
  } catch { errorMessage.value = 'Could not delete that reading.' }
}

/* ---------- printable progress report ---------- */
const printError = ref('')
function printReport() {
  printError.value = ''
  const l = latest.value
  const fmt = (v, unit) => (v != null && v !== '' ? `${v}${unit}` : '—')
  const change = (d, unit, dp = 1) => (d == null ? '—' : `${d <= 0 ? '' : '+'}${d.toFixed(dp)}${unit}`)
  const rows = [
    ['Latest weight', fmt(l.weight_kg, ' kg')], ['Weight change', change(weightDelta.value, ' kg')],
    ['Latest BMI', fmt(l.bmi, '')], ['BMI change', change(bmiDelta.value, '')],
    ['Blood pressure', fmt(l.blood_pressure, ' mmHg')], ['Fasting glucose', fmt(l.blood_glucose, ' mg/dL')],
    ['HbA1c', fmt(l.hba1c, '%')],
  ]
  const weeks = adherence.value.filter(w => w.pct != null)
  if (weeks.length) {
    rows.push(['Meal-plan adherence (this week)', fmt(thisWeek.value?.pct, '%')])
    rows.push([`Average over ${weeks.length} week${weeks.length === 1 ? '' : 's'}`, `${Math.round(weeks.reduce((s, w) => s + w.pct, 0) / weeks.length)}%`])
  }
  const ok = printDocument({
    title: 'Progress report', number: selectedRange.value,
    sections: [{ heading: 'Summary', rows }],
    table: [['Date', 'By', 'Weight', 'BMI', 'BP', 'Glucose', 'HbA1c'],
      ...filteredRecords.value.map(r => [formatDate(r.record_date), r.source === 'client' ? 'Self-reported' : 'RND',
        fmt(r.weight_kg, ' kg'), fmt(r.bmi, ''), fmt(r.blood_pressure, ''), fmt(r.blood_glucose, ' mg/dL'), fmt(r.hba1c, '%')])],
    note: '"Self-reported" readings were logged at home by the patient; "RND" readings were recorded by their Registered Nutritionist-Dietitian.',
  })
  if (!ok) printError.value = 'Allow pop-ups for this site to print your report.'
}

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
const hba1cSeries = computed(() => seriesFor('hba1c'))

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

onMounted(() => { loadRecords(); loadAdherence() })
</script>

<style scoped>
* { box-sizing: border-box; }

.tracker-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
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
.record-table td { padding: 12px; border-bottom: 1px solid #f4f5f2; color: #4a5a4a; white-space: nowrap; }
.record-table tr:last-child td { border-bottom: none; }

.header-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

/* Weekly adherence bars — one series, brand green; goal line dashed. */
.adh-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 8px; }
.chart-title.flush { margin: 0; }
.adh-sub { font-size: 0.74rem; color: #8a9a8a; margin: 3px 0 0; }
.adh-now { text-align: right; flex-shrink: 0; }
.adh-now strong { display: block; font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a3a1a; }
.adh-now span { font-size: 0.72rem; color: #8a9a8a; }
.adh-svg { width: 100%; height: 150px; display: block; overflow: visible; }
.adh-bar { fill: #1f8f5c; }
.adh-bar.empty { fill: none; }
.adh-bar:hover { fill: #17734a; }
.adh-goal { stroke: #b8860b; stroke-width: 1; stroke-dasharray: 4 4; }
.adh-goal-label { font-size: 9px; fill: #8a6a1a; font-family: 'Inter', sans-serif; }
.adh-base { stroke: #dfe5df; stroke-width: 1; }
.adh-val { font-size: 10px; font-weight: 700; fill: #1a3a1a; font-family: 'Inter', sans-serif; }
.adh-x { font-size: 9px; fill: #8a9a8a; font-family: 'Inter', sans-serif; }

/* Record history: who logged it */
.src { font-size: 0.68rem; font-weight: 700; padding: 2px 8px; border-radius: 10px; background: #eceeec; color: #5a6a5a; }
.src.client { background: #eef1f8; color: #34508a; }
.rec-note { display: block; font-size: 0.72rem; color: #8a9a8a; white-space: normal; max-width: 220px; }
.rec-x { border: none; background: none; color: #9aaa9a; cursor: pointer; padding: 2px; display: flex; }
.rec-x:hover { color: #c0392b; }

/* Log a reading */
.log-modal { max-width: 520px; }
.log-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.log-field { display: flex; flex-direction: column; gap: 4px; font-size: 0.78rem; font-weight: 600; color: #1a3a1a; min-width: 0; }
.log-field em { font-style: normal; font-weight: 400; color: #8a9a8a; }
.log-field .nm-input { min-height: 42px; }
.log-field.wide { grid-column: 1 / -1; }
.bp-pair { display: flex; align-items: center; gap: 6px; }
.bp-pair .nm-input { flex: 1; min-width: 0; }
@media (max-width: 560px) {
  .log-grid { grid-template-columns: minmax(0, 1fr); }
  .header-actions { width: 100%; }
  .header-actions > * { flex: 1; }
}

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
