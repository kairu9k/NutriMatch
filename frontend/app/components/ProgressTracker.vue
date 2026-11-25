<template>
  <div class="tracker-page">
    <!-- HERO: title + range and print -->
    <section class="pt-hero">
      <img class="pt-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="pt-hero-fade" aria-hidden="true"></span>
      <div class="pt-hero-text">
        <p class="pt-eyebrow"><span aria-hidden="true"></span>Progress tracker</p>
        <h2 class="pt-title">Your progress, <em>step by step.</em></h2>
        <p class="page-sub">The readings your RND records at each consultation, and how closely you followed your meal plan.</p>
      </div>
      <div v-if="records.length" class="header-actions">
        <label class="pt-select">
          <svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>
          <select v-model="selectedRange" class="nm-select" aria-label="Date range">
            <option v-for="r in ranges" :key="r.label" :value="r.label">{{ r.label }}</option>
          </select>
          <svg class="ic pt-caret" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
        </label>
        <button type="button" class="pt-print" @click="printReport"><Printer :size="17" aria-hidden="true" /> Print or save as PDF</button>
      </div>
    </section>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="printError" class="form-error">{{ printError }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-if="!isLoading && records.length">
      <!-- latest readings -->
      <div class="stat-grid">
        <div class="stat-card" style="--c: #004D3A; --bg: #E3EFE7">
          <div class="stat-top">
            <span class="stat-label">Weight</span>
            <span class="stat-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 21h14a1 1 0 0 0 1-1l-1.5-13a1 1 0 0 0-1-1h-11a1 1 0 0 0-1 1L4 20a1 1 0 0 0 1 1z" /><path d="M12 6V3M9.5 12a2.5 2.5 0 0 1 5 0M12 12l1.5-2" /></svg></span>
          </div>
          <div class="stat-number" :class="{ none: !latest.weight_kg }">{{ latest.weight_kg ? num(latest.weight_kg) : '—' }}<span class="unit">kg</span></div>
          <div v-if="weightDelta !== null" class="stat-delta" :class="weightDelta <= 0 ? 'down' : 'up'">{{ changeText(weightDelta, ' kg', 1) }}</div>
          <div v-else class="stat-delta muted"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ latest.weight_kg ? lastOn : 'No reading yet' }}</div>
        </div>
        <div class="stat-card" style="--c: #9A7300; --bg: #FBF3D2">
          <div class="stat-top">
            <span class="stat-label">BMI</span>
            <span class="stat-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="4.5" r="2" /><path d="M8 22l1-8-3-1 2-6h8l2 6-3 1 1 8" /></svg></span>
          </div>
          <div class="stat-number" :class="{ none: latest.bmi == null }">{{ latest.bmi != null ? num(latest.bmi) : '—' }}</div>
          <div v-if="bmiDelta !== null" class="stat-delta" :class="bmiDelta <= 0 ? 'down' : 'up'">{{ changeText(bmiDelta, '', 1) }}</div>
          <div v-else class="stat-delta muted"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ latest.bmi != null ? lastOn : 'No reading yet' }}</div>
        </div>
        <div class="stat-card" style="--c: #B4384A; --bg: #FDECEC">
          <div class="stat-top">
            <span class="stat-label">Blood pressure</span>
            <span class="stat-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7.5-4.6-9.2-9.3C1.7 7.4 3.8 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.2 0 5.3 2.9 4.2 6.2C19.5 15.4 12 20 12 20z" /><path d="M3.5 12h4l2-3 3 6 2-3h6" /></svg></span>
          </div>
          <div class="stat-number" :class="{ none: !latest.blood_pressure }">{{ latest.blood_pressure || '—' }}<span class="unit">mmHg</span></div>
          <div class="stat-delta muted"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ latest.blood_pressure ? lastOn : 'No reading yet' }}</div>
        </div>
        <div class="stat-card" style="--c: #3B5BA5; --bg: #EEF1FA">
          <div class="stat-top">
            <span class="stat-label">Fasting glucose</span>
            <span class="stat-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3s7 7 7 12a7 7 0 0 1-14 0c0-5 7-12 7-12z" /><path d="M9 15a3 3 0 0 0 3 3" /></svg></span>
          </div>
          <div class="stat-number" :class="{ none: !latest.blood_glucose }">{{ latest.blood_glucose ? `${num(latest.blood_glucose)}` : '—' }}<span class="unit">mg/dL</span></div>
          <div v-if="glucoseDelta !== null" class="stat-delta" :class="glucoseDelta <= 0 ? 'down' : 'up'">{{ changeText(glucoseDelta, ' mg/dL', 0) }}</div>
          <div v-else class="stat-delta muted"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ latest.blood_glucose ? lastOn : 'No reading yet' }}</div>
        </div>
      </div>

      <!-- MEAL-PLAN ADHERENCE (weekly, from the client's meal logs) -->
      <div v-if="adherence.length" class="adh-card">
        <div class="adh-side">
          <p class="pt-k"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg>MEAL PLAN FOLLOW-THROUGH</p>
          <h3 class="chart-title flush">How closely you followed your meal plan</h3>
          <p class="adh-sub">Planned meals followed each week, as rated by your RND. Partly followed counts half.</p>
          <div class="adh-ring-row">
            <div class="adh-ring" :style="{ '--p': thisWeek?.pct ?? 0 }">
              <span><strong>{{ thisWeek?.pct != null ? `${thisWeek.pct}%` : '—' }}</strong><small>this week</small></span>
            </div>
            <div class="adh-goal-box">
              <p><span class="adh-goal-dash" aria-hidden="true"></span>Goal <strong>80%</strong></p>
              <p class="adh-sub">Keep logging your meals so your RND can rate them.</p>
            </div>
          </div>
        </div>
        <div class="adh-chart" role="img" :aria-label="`Weekly meal-plan adherence, this week ${thisWeek?.pct ?? 'no data'} percent`">
          <div class="adh-area" :style="{ '--n': adherence.length }">
            <span class="adh-goal-line" aria-hidden="true"><em>80% goal</em></span>
            <div v-for="w in adherence" :key="w.end" class="adh-col" :title="`${weekLabel(w)}: ${w.pct != null ? `${w.pct}% (${w.logged} of ${w.planned} meals logged)` : 'no meals planned'}`">
              <span class="adh-val">{{ w.pct != null ? `${w.pct}%` : '—' }}</span>
              <div class="adh-track">
                <span v-if="w.pct != null" class="adh-bar" :style="{ height: `${Math.min(100, Math.max(0, w.pct))}%` }"></span>
                <span v-else class="adh-none">No rating yet</span>
              </div>
              <span class="adh-x" :class="{ now: w === thisWeek }">{{ shortDay(w.end) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="weightSeries.length > 1 || bmiSeries.length > 1 || systolicSeries.length > 1 || glucoseSeries.length > 1 || hba1cSeries.length > 1" class="chart-grid">
        <div v-if="weightSeries.length > 1" class="chart-card">
          <h3 class="chart-title">Weight (kg)</h3>
          <TrendLine :points="weightSeries" color="#004D3A" />
        </div>
        <div v-if="bmiSeries.length > 1" class="chart-card">
          <h3 class="chart-title">BMI</h3>
          <TrendLine :points="bmiSeries" color="#C49102" />
        </div>
        <div v-if="systolicSeries.length > 1" class="chart-card">
          <h3 class="chart-title">Blood pressure (mmHg)</h3>
          <svg viewBox="0 0 400 120" class="bp-svg" preserveAspectRatio="none">
            <path :d="bpLinePath(systolicSeries)" stroke="#004D3A" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
            <circle v-for="(p, i) in bpCoords(systolicSeries)" :key="'s'+i" :cx="p.x" :cy="p.y" r="3.5" fill="#004D3A" />
            <path :d="bpLinePath(diastolicSeries)" stroke="#C49102" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
            <circle v-for="(p, i) in bpCoords(diastolicSeries)" :key="'d'+i" :cx="p.x" :cy="p.y" r="3.5" fill="#C49102" />
          </svg>
          <div class="bp-labels">
            <span v-for="p in systolicSeries" :key="p.label">{{ p.label }}</span>
          </div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background:#004D3A"></span> Systolic</span>
            <span class="legend-item"><span class="legend-dot" style="background:#C49102"></span> Diastolic</span>
          </div>
        </div>
        <div v-if="glucoseSeries.length > 1" class="chart-card">
          <h3 class="chart-title">Fasting blood glucose (mg/dL)</h3>
          <TrendLine :points="glucoseSeries" color="#c0392b" />
        </div>
        <div v-if="hba1cSeries.length > 1" class="chart-card">
          <h3 class="chart-title">HbA1c (%)</h3>
          <TrendLine :points="hba1cSeries" color="#2f6fa8" />
        </div>
      </div>

      <div class="surface">
        <header class="surface-head">
          <div>
            <p class="pt-k"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01" /></svg>HISTORY</p>
            <h3 class="surface-title">All readings</h3>
          </div>
          <span class="pt-count">{{ filteredRecords.length }} reading{{ filteredRecords.length === 1 ? '' : 's' }}</span>
        </header>
        <div class="table-wrap">
          <table class="record-table">
            <thead>
              <tr><th>Date</th><th>By</th><th>Weight</th><th>BMI</th><th>BP</th><th>Glucose</th><th>Adherence</th><th>HbA1c</th><th></th></tr>
            </thead>
            <tbody>
              <tr v-for="rec in filteredRecords" :key="rec.id">
                <td><span class="rec-date"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>{{ formatDate(rec.record_date) }}</span><span v-if="rec.client_notes" class="rec-note">{{ rec.client_notes }}</span></td>
                <td><span class="src" :class="rec.source">{{ rec.source === 'client' ? 'You' : 'RND' }}</span></td>
                <td :class="{ dash: !rec.weight_kg }">{{ rec.weight_kg ? `${num(rec.weight_kg)} kg` : '—' }}</td>
                <td :class="{ dash: rec.bmi == null }">{{ rec.bmi != null ? num(rec.bmi) : '—' }}</td>
                <td :class="{ dash: !rec.blood_pressure }">{{ rec.blood_pressure || '—' }}</td>
                <td :class="{ dash: !rec.blood_glucose }">{{ rec.blood_glucose ? `${num(rec.blood_glucose)} mg/dL` : '—' }}</td>
                <td :class="{ dash: rec.adherence_pct === null }">{{ rec.adherence_pct !== null ? `${rec.adherence_pct}%` : '—' }}</td>
                <td :class="{ dash: !rec.hba1c }">{{ rec.hba1c ? `${num(rec.hba1c)}%` : '—' }}</td>
                <td><button v-if="rec.source === 'client'" type="button" class="rec-x" aria-label="Delete this reading" :disabled="removing === rec.id" @click="removeReading(rec)"><X :size="13" /></button></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- PHONE: each reading as a card -->
        <ul class="rec-cards">
          <li v-for="rec in filteredRecords" :key="rec.id" class="rec-card">
            <div class="rec-card-top">
              <span class="rec-date"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>{{ formatDate(rec.record_date) }}</span>
              <span class="rec-card-right">
                <span class="src" :class="rec.source">{{ rec.source === 'client' ? 'You' : 'RND' }}</span>
                <button v-if="rec.source === 'client'" type="button" class="rec-x" aria-label="Delete this reading" :disabled="removing === rec.id" @click="removeReading(rec)"><X :size="14" /></button>
              </span>
            </div>
            <p v-if="rec.client_notes" class="rec-note">{{ rec.client_notes }}</p>
            <dl class="rec-grid">
              <div><dt>Weight</dt><dd>{{ rec.weight_kg ? `${num(rec.weight_kg)} kg` : '—' }}</dd></div>
              <div><dt>BMI</dt><dd>{{ rec.bmi != null ? num(rec.bmi) : '—' }}</dd></div>
              <div><dt>BP</dt><dd>{{ rec.blood_pressure || '—' }}</dd></div>
              <div><dt>Glucose</dt><dd>{{ rec.blood_glucose ? `${num(rec.blood_glucose)}` : '—' }}</dd></div>
              <div><dt>Adherence</dt><dd>{{ rec.adherence_pct !== null ? `${rec.adherence_pct}%` : '—' }}</dd></div>
              <div><dt>HbA1c</dt><dd>{{ rec.hba1c ? `${num(rec.hba1c)}%` : '—' }}</dd></div>
            </dl>
          </li>
        </ul>
      </div>
    </template>

    <div v-else-if="!isLoading" class="empty-state">
      <div class="empty-icon"><LineChart :size="28" /></div>
      <p class="empty-title">No progress recorded yet</p>
      <p class="empty-desc">Your RND records your weight, blood pressure and other vitals at each consultation.</p>
    </div>
  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
const toast = useToast() // the app's toast (2026-11-03)
import { LineChart, Printer, X } from 'lucide-vue-next'
import { printDocument } from '~/utils/printDoc'

definePageMeta({ layout: 'dashboard', title: 'Progress Tracker' })

const { get, del } = useApi()

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

/* ---------- older self-reported readings (logging was removed 2026-10-16) ---------- */
const removing = ref(null)
async function removeReading(rec) {
  if (removing.value) return
  removing.value = rec.id
  try {
    await del(`/client/progress/${rec.id}/`)
    records.value = records.value.filter(r => r.id !== rec.id)
  } catch { toast.error('Could not delete that reading. Please try again.') } finally { removing.value = null }
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
    foot: 'Confidential health information. Handle according to the Data Privacy Act of 2012 (RA 10173). Generated by NutriMatch.',
  })
  if (!ok) printError.value = 'Allow pop-ups for this site to print your report.'
}

const isLoading = ref(true)
const errorMessage = ref('')
const records = ref([])

/* ---------- Date range filter ---------- */
const ranges = [
  { label: 'Last 3 months', months: 3 },
  { label: 'Last 6 months', months: 6 },
  { label: 'Last year', months: 12 },
]
const selectedRange = ref('Last 6 months')

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
// 64.90 -> 64.9, 106.00 -> 106 (the API sends two decimals)
const num = v => String(Number(v))
// "Down 3.1 kg since Aug 1" / "Up 2 mg/dL since Aug 1"
function changeText(d, unit, dp) {
  const first = sortedAsc.value[0]
  const since = first ? ` since ${formatShortDate(first.record_date)}` : ''
  if (Math.abs(d) < 0.05) return `No change${since}`
  return `${d < 0 ? 'Down' : 'Up'} ${Math.abs(d).toFixed(dp)}${unit}${since}`
}
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

async function loadRecords({ quiet = false } = {}) {
  if (!quiet) {
    isLoading.value = true
    errorMessage.value = ''
  }
  try {
    records.value = await get('/client/progress/')
  } catch {
    if (!quiet) errorMessage.value = 'Could not load your progress history. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(() => { loadRecords(); loadAdherence() })
useAutoRefresh(() => Promise.all([loadRecords({ quiet: true }), loadAdherence()]))

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// "Latest Oct 25" under a reading with no change to show yet
const lastOn = computed(() => (latest.value.record_date ? `Latest ${formatShortDate(latest.value.record_date)}` : ''))
</script>

<style scoped>
/* =========================================================
   Progress Tracker: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings, numbers), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.tracker-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; gap: 18px; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }

/* ---------- HERO ---------- */
.pt-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px 28px;
  flex-wrap: wrap;
  padding: 32px 34px;
  border-radius: 24px;
  color: #FFFFFF;
  background:
    radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%),
    linear-gradient(115deg, #035A45 0%, #004D3A 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -24px rgba(0, 77, 58, 0.55);
}
.pt-hero-plate { position: absolute; right: -70px; top: 50%; width: 400px; height: 400px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.55; pointer-events: none; }
.pt-hero-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004D3A 0%, #004D3A 45%, rgba(0, 77, 58, 0.75) 62%, rgba(0, 70, 52, 0.15) 100%); pointer-events: none; }
.pt-hero-text { position: relative; z-index: 1; max-width: 560px; }
.pt-eyebrow { margin: 0; display: flex; align-items: center; gap: 10px; font-size: 12.5px; font-weight: 800; color: #EFBF04; }
.pt-eyebrow span { width: 26px; height: 2px; border-radius: 2px; background: #EFBF04; }
.pt-title { margin: 10px 0; font-family: 'Playfair Display', Georgia, serif; font-size: 40px; font-weight: 700; line-height: 1.12; color: #FFFFFF; }
.pt-title em { font-style: italic; color: #EFBF04; }
.page-sub { margin: 0; font-size: 15.0px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }
.header-actions { position: relative; z-index: 1; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.pt-select { display: inline-flex; align-items: center; gap: 10px; height: 46px; padding: 0 16px; border-radius: 12px; background: #FFFFFF; color: #004D3A; cursor: pointer; box-shadow: 0 10px 20px -14px rgba(0, 0, 0, 0.5); }
.pt-select .nm-select { min-width: 0; height: auto; padding: 0 4px 0 0; border: none; outline: none; background: transparent; box-shadow: none; color: #10231B; font-family: inherit; font-size: 14px; font-weight: 700; -webkit-appearance: none; appearance: none; cursor: pointer; }
.pt-caret { pointer-events: none; color: #6B7D73; }
.pt-print { display: inline-flex; align-items: center; justify-content: center; gap: 9px; height: 46px; padding: 0 20px; border: none; border-radius: 12px; background: #EFBF04; color: #004D3A; font-family: inherit; font-size: 14px; font-weight: 800; white-space: nowrap; cursor: pointer; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); transition: background-color .15s; }
.pt-print:hover { background: #F5CB1F; }
.pt-print:focus-visible,
.pt-select:focus-within { outline: 3px solid rgba(239, 191, 4, 0.6); outline-offset: 2px; }

.form-error { margin: 0; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 14px; }
.placeholder-text { font-size: 14px; color: #6B7D73; }

/* ---------- LATEST READINGS ---------- */
.stat-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.stat-card {
  position: relative;
  overflow: hidden;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 20px 22px 20px;
  border-radius: 20px;
  background: #FFFFFF;
  border: 1px solid #E4EBE6;
  box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3);
}
.stat-card::after { content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 4px; background: var(--c); opacity: .85; }
.stat-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.stat-label { font-size: 14px; font-weight: 700; color: #3E5046; }
.stat-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; background: var(--bg); color: var(--c); }
.stat-number { margin: 10px 0 12px; display: flex; align-items: baseline; gap: 6px; font-family: 'Playfair Display', Georgia, serif; font-size: 38px; font-weight: 700; line-height: 1; color: #0E3A2C; font-variant-numeric: lining-nums; }
.stat-number .unit { font-family: 'DM Sans', Arial, sans-serif; font-size: 14px; font-weight: 600; color: #6B7D73; }
.stat-number.none { color: #B5C2BA; }
.stat-delta { margin-top: auto; align-self: flex-start; display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.stat-delta.down { background: #EAF4EE; color: #1F6F46; }
.stat-delta.up { background: #FBF3D2; color: #8A6400; }
.stat-delta.muted { background: #F3F6F4; color: #4A5A52; font-weight: 600; }

/* ---------- ADHERENCE ---------- */
.pt-k { margin: 0; display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 800; color: #C49102; }
.adh-card {
  display: grid;
  grid-template-columns: minmax(0, .9fr) minmax(0, 1.4fr);
  gap: 28px;
  padding: 26px 28px;
  border-radius: 20px;
  background: #FFFFFF;
  border: 1px solid #E4EBE6;
  box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3);
}
.chart-title { margin: 0 0 14px; font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: #0E3A2C; }
.chart-title.flush { margin: 6px 0 0; font-size: 22px; }
.adh-sub { margin: 6px 0 0; font-size: 13.5px; line-height: 1.55; color: #6B7D73; }
.adh-ring-row { display: flex; align-items: center; gap: 20px; margin-top: 22px; }
.adh-ring { flex-shrink: 0; width: 122px; height: 122px; border-radius: 50%; display: grid; place-items: center; background: conic-gradient(#004D3A calc(var(--p) * 1%), #E3EFE7 0); }
.adh-ring span { width: 96px; height: 96px; border-radius: 50%; background: #FFFFFF; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.adh-ring strong { font-family: 'Playfair Display', Georgia, serif; font-size: 30px; line-height: 1; color: #0E3A2C; }
.adh-ring small { margin-top: 4px; font-size: 12px; color: #6B7D73; }
.adh-goal-box p { margin: 0; }
.adh-goal-box p:first-child { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #3E5046; }
.adh-goal-box strong { color: #9A7300; }
.adh-goal-dash { width: 22px; border-top: 2px dashed #EFBF04; }

.adh-chart { min-width: 0; padding: 16px 18px 10px; border-radius: 18px; background: #F6FAF7; }
.adh-area { position: relative; height: 250px; display: flex; gap: 14px; padding-top: 26px; }
/* the 80% line: 80% up the bar area (bars sit between the value label and the date) */
.adh-goal-line { position: absolute; left: 0; right: 0; bottom: calc(33px + (100% - 85px) * .8); border-top: 2px dashed #EFBF04; z-index: 1; pointer-events: none; }
.adh-goal-line em { position: absolute; right: 0; top: -24px; padding: 2px 8px; border-radius: 999px; background: #FDF6DA; font-style: normal; font-size: 11.5px; font-weight: 700; color: #9A7300; }
.adh-col { flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 8px; }
.adh-val { height: 18px; font-size: 13px; font-weight: 700; color: #0E3A2C; }
.adh-track { position: relative; width: 100%; max-width: 64px; flex: 1; display: flex; align-items: flex-end; justify-content: center; }
.adh-bar { width: 100%; min-height: 6px; border-radius: 12px 12px 4px 4px; background: linear-gradient(180deg, #1F9D55, #004D3A); transition: height .4s ease; }
.adh-none { position: absolute; left: 0; right: 0; bottom: 0; height: 40%; display: flex; align-items: center; justify-content: center; padding: 0 4px; border: 1.5px dashed #CFDDD4; border-radius: 12px 12px 4px 4px; text-align: center; font-size: 11px; line-height: 1.3; color: #8AA196; }
.adh-x { height: 25px; display: inline-flex; align-items: center; padding: 0 10px; border-radius: 999px; font-size: 12.5px; font-weight: 600; color: #6B7D73; white-space: nowrap; }
.adh-x.now { background: #004D3A; color: #FFFFFF; }

/* ---------- TREND CHARTS ---------- */
.chart-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }
.chart-card { min-width: 0; padding: 22px 24px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.chart-card.wide { grid-column: 1 / -1; }
.bp-svg { width: 100%; height: 120px; display: block; overflow: visible; }
.bp-labels { display: flex; justify-content: space-between; margin-top: 6px; font-size: 12px; color: #6B7D73; }
.chart-legend { display: flex; gap: 14px; margin-top: 10px; }
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 600; color: #3E5046; }
.legend-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }

/* ---------- ALL READINGS ---------- */
.surface { padding: 24px 26px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.surface-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.surface-title { margin: 6px 0 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #0E3A2C; }
.pt-count { padding: 6px 12px; border-radius: 999px; background: #EAF4EE; color: #004D3A; font-size: 13px; font-weight: 700; white-space: nowrap; }
.table-wrap { overflow-x: auto; border: 1px solid #E7EDE9; border-radius: 16px; }
.record-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.record-table th { padding: 13px 18px; text-align: left; font-size: 12px; font-weight: 800; color: #4A5A52; background: #F3F8F5; white-space: nowrap; }
.record-table td { padding: 16px 18px; border-top: 1px solid #EEF2EF; color: #0E3A2C; font-weight: 600; white-space: nowrap; font-variant-numeric: tabular-nums; }
.record-table td.dash { color: #B5C2BA; font-weight: 500; }
.record-table tbody tr:hover td { background: #FAFCFA; }
.rec-date { display: inline-flex; align-items: center; gap: 8px; font-weight: 700; color: #0E3A2C; }
.rec-date .ic { color: #1F7A4D; }
.src { display: inline-flex; align-items: center; height: 24px; padding: 0 10px; border-radius: 999px; background: #E3EFE7; color: #004D3A; font-size: 12px; font-weight: 800; }
.src.client { background: #F2F6F3; color: #4A5A52; }
.rec-note { display: block; margin-top: 4px; max-width: 240px; font-size: 12px; font-weight: 500; color: #6B7D73; white-space: normal; }
.rec-x { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; padding: 0; border: none; border-radius: 50%; background: none; color: #9AAA9A; cursor: pointer; }
.rec-x:hover:not(:disabled) { background: #FDECEC; color: #C0392B; }
.rec-x:disabled { opacity: .4; cursor: default; }
.rec-cards { display: none; }

/* ---------- EMPTY ---------- */
.empty-state { padding: 60px 20px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; text-align: center; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.empty-icon { width: 60px; height: 60px; margin: 0 auto 16px; border-radius: 18px; background: #EEF4F0; color: #004D3A; display: flex; align-items: center; justify-content: center; }
.empty-title { margin: 0 0 6px; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #0E3A2C; }
.empty-desc { max-width: 400px; margin: 0 auto; font-size: 14px; line-height: 1.55; color: #6B7D73; }

/* ---------- SMALLER SCREENS ---------- */
@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .adh-card { grid-template-columns: 1fr; }
}
@media (max-width: 960px) {
  .tracker-page { gap: 14px; padding-bottom: 96px; }
  .pt-hero { padding: 22px 18px 20px; border-radius: 22px; }
  .pt-hero-plate { width: 170px; height: 170px; right: -50px; top: 18px; transform: none; opacity: .9; }
  .pt-hero-fade { background: linear-gradient(90deg, #004D3A 40%, rgba(0, 77, 58, 0.5) 75%, rgba(0, 77, 58, 0.2)); }
  .pt-hero-text { max-width: 72%; }
  .pt-title { font-size: 28px; }
  .page-sub { font-size: 13.5px; }
  .header-actions { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .pt-select { height: 44px; padding: 0 10px; gap: 6px; }
  .pt-select .nm-select { width: 100%; font-size: 13px; }
  .pt-print { height: 44px; padding: 0 10px; font-size: 13px; }
  .stat-grid { gap: 10px; }
  .stat-card { padding: 14px 14px 16px; border-radius: 18px; }
  .stat-ico { width: 32px; height: 32px; border-radius: 11px; }
  .stat-ico .ic { width: 17px; height: 17px; }
  .stat-label { font-size: 12.5px; }
  .stat-number { margin: 12px 0 10px; font-size: 26px; flex-wrap: wrap; }
  .stat-number .unit { font-size: 12px; }
  .stat-delta { padding: 3px 8px; font-size: 11px; }
  .stat-delta .ic { display: none; }
  .adh-card { padding: 18px 16px; gap: 18px; border-radius: 18px; }
  .chart-title.flush { font-size: 19px; }
  .adh-ring { width: 96px; height: 96px; }
  .adh-ring span { width: 76px; height: 76px; }
  .adh-ring strong { font-size: 24px; }
  .adh-chart { padding: 12px 10px 8px; overflow-x: auto; }
  .adh-area { height: 200px; gap: 8px; min-width: calc(var(--n, 4) * 56px); }
  .adh-x { padding: 0 7px; font-size: 11px; }
  .chart-grid { grid-template-columns: minmax(0, 1fr); }
  .chart-card { padding: 18px 16px; border-radius: 18px; }
  .surface { padding: 18px 16px; border-radius: 18px; }
  .surface-title { font-size: 19px; }
  .table-wrap { display: none; }
  .rec-cards { display: flex; flex-direction: column; gap: 10px; margin: 0; padding: 0; list-style: none; }
  .rec-card { padding: 14px; border-radius: 16px; border: 1px solid #E7EDE9; background: #FAFCFA; }
  .rec-card-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
  .rec-card-right { display: inline-flex; align-items: center; gap: 4px; }
  .rec-card .rec-note { margin: -4px 0 10px; max-width: none; }
  .rec-grid { margin: 0; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
  .rec-grid div { min-width: 0; padding: 10px; border-radius: 12px; background: #FFFFFF; border: 1px solid #EEF2EF; }
  .rec-grid dt { font-size: 11.5px; color: #6B7D73; }
  .rec-grid dd { margin: 2px 0 0; font-size: 15px; font-weight: 800; color: #0E3A2C; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
}
@media (max-width: 380px) {
  .header-actions { grid-template-columns: 1fr; }
  .rec-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (prefers-reduced-motion: reduce) {
  .adh-bar { transition: none; }
}

/* no coloured line under the four cards */
.stat-card::after { display: none !important; }
</style>