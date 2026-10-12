<template>
  <div class="nm-page">
    <div class="toolbar">
      <div class="period">
        <select v-model="period" class="nm-select" aria-label="Report period">
          <option v-for="p in PERIODS" :key="p.value" :value="p.value">{{ p.label }}</option>
        </select>
        <template v-if="period === 'custom'">
          <input v-model="from" type="date" class="nm-input date" aria-label="From" />
          <span class="to">to</span>
          <input v-model="to" type="date" class="nm-input date" aria-label="To" />
        </template>
      </div>
      <div class="exports">
        <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="!r" @click="downloadCsv"><Download :size="14" /> CSV</button>
        <button type="button" class="nm-btn-dark nm-btn-sm" :disabled="!r" @click="print"><Printer :size="14" /> Print / PDF</button>
      </div>
    </div>
    <p v-if="printError" class="nm-error">{{ printError }}</p>
    <p v-if="error" class="nm-error">{{ error }}</p>
    <p v-if="loading && !r" class="nm-muted">Loading…</p>

    <template v-if="r">
      <p class="nm-panel-sub period-label">{{ r.period.label }} · {{ dateRange }}</p>
      <div class="nm-stat-grid">
        <div class="nm-stat-card">
          <div class="nm-stat-icon"><CalendarCheck :size="17" /></div>
          <p class="nm-stat-value">{{ r.consultations.completed }}</p>
          <p class="nm-stat-label">Consultations completed</p>
          <p class="nm-stat-note">{{ r.consultations.cancelled }} cancelled</p>
        </div>
        <div class="nm-stat-card">
          <div class="nm-stat-icon gold"><Banknote :size="17" /></div>
          <p class="nm-stat-value">{{ peso(r.money.gross) }}</p>
          <p class="nm-stat-label">Payments received</p>
          <p class="nm-stat-note">{{ r.money.payments }} payment{{ r.money.payments === 1 ? '' : 's' }}</p>
        </div>
        <div class="nm-stat-card">
          <div class="nm-stat-icon"><Percent :size="17" /></div>
          <p class="nm-stat-value">{{ peso(r.money.commission) }}</p>
          <p class="nm-stat-label">Platform commission</p>
          <p class="nm-stat-note">{{ peso(r.money.rnd_share) }} to RNDs</p>
        </div>
        <div class="nm-stat-card">
          <div class="nm-stat-icon"><Users :size="17" /></div>
          <p class="nm-stat-value">{{ r.people.new_clients }}</p>
          <p class="nm-stat-label">New clients</p>
          <p class="nm-stat-note">{{ r.people.rnds_approved }} RND{{ r.people.rnds_approved === 1 ? '' : 's' }} approved</p>
        </div>
      </div>

      <div class="two">
        <section class="nm-panel">
          <h2 class="nm-panel-title">Money</h2>
          <dl class="facts">
            <div><dt>Payments received</dt><dd>{{ peso(r.money.gross) }}</dd></div>
            <div><dt>Platform commission</dt><dd>{{ peso(r.money.commission) }}</dd></div>
            <div><dt>RNDs' share</dt><dd>{{ peso(r.money.rnd_share) }}</dd></div>
            <div><dt>Refunded</dt><dd>{{ r.money.refunded.count }} · {{ peso(r.money.refunded.amount) }}</dd></div>
            <div><dt>Waiting for refund</dt><dd :class="{ warn: r.money.refund_pending.count }">{{ r.money.refund_pending.count }} · {{ peso(r.money.refund_pending.amount) }}</dd></div>
          </dl>
        </section>
        <section class="nm-panel">
          <h2 class="nm-panel-title">Activity</h2>
          <dl class="facts">
            <div><dt>Completed consultations</dt><dd>{{ r.consultations.completed }}</dd></div>
            <div v-for="(n, f) in r.consultations.by_format" :key="f"><dt class="sub">· {{ f }}</dt><dd>{{ n }}</dd></div>
            <div><dt>Cancelled consultations</dt><dd>{{ r.consultations.cancelled }}</dd></div>
            <div><dt>Support requests</dt><dd>{{ r.people.support_requests }}</dd></div>
          </dl>
        </section>
      </div>

      <section v-if="r.monthly.length > 1" class="nm-panel">
        <h2 class="nm-panel-title">By month</h2>
        <div class="nm-table-wrap">
          <table class="nm-table">
            <thead><tr><th>Month</th><th class="nm-num">Completed</th><th class="nm-num">Cancelled</th><th class="nm-num">Payments</th><th class="nm-num">Received</th><th class="nm-num">Commission</th></tr></thead>
            <tbody>
              <tr v-for="m in r.monthly" :key="m.month">
                <td>{{ monthLabel(m.month) }}</td><td class="nm-num">{{ m.completed }}</td><td class="nm-num">{{ m.cancelled }}</td>
                <td class="nm-num">{{ m.payments }}</td><td class="nm-num">{{ peso(m.gross) }}</td><td class="nm-num">{{ peso(m.commission) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">RND performance</h2>
            <p class="nm-panel-sub">Approved RNDs in this period · rating is overall</p>
          </div>
        </div>
        <div v-if="!r.rnds.length" class="nm-empty"><BarChart3 :size="28" /><p>No approved RNDs yet.</p></div>
        <div v-else class="nm-table-wrap">
          <table class="nm-table stack">
            <thead>
              <tr><th>RND</th><th class="nm-num">Consultations</th><th class="nm-num">Received</th><th class="nm-num">Commission</th><th class="nm-num">RND share</th><th>Rating</th><th style="width: 18%">Share of consultations</th></tr>
            </thead>
            <tbody>
              <tr v-for="x in r.rnds" :key="x.id" class="clickable" @click="navigateTo(`/users/${x.id}`)">
                <td><p class="nm-row-title">{{ x.name }}</p><p class="nm-row-sub">{{ x.specialization || '—' }}</p></td>
                <td data-label="Consultations" class="nm-num">{{ x.consultations }}</td>
                <td data-label="Received" class="nm-num">{{ peso(x.gross) }}</td>
                <td data-label="Commission" class="nm-num">{{ peso(x.commission) }}</td>
                <td data-label="RND share" class="nm-num">{{ peso(x.rnd_share) }}</td>
                <td data-label="Rating">{{ x.rating ? `★ ${x.rating} (${x.reviews})` : '—' }}</td>
                <td data-label="Share">
                  <div class="bar"><span :style="{ width: `${share(x)}%` }" /></div>
                  <span class="nm-row-sub">{{ share(x) }}%</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
// Platform report for a chosen period (GET /api/admin/reports/, core/reports.py),
// printable (utils/printDoc.js) and downloadable as CSV.
import { Banknote, BarChart3, CalendarCheck, Download, Percent, Printer, Users } from 'lucide-vue-next'
import { printDocument } from '~/utils/printDoc'

const { get } = useApi()
const PERIODS = [
  { value: 'this_month', label: 'This month' }, { value: 'last_month', label: 'Last month' },
  { value: 'last_3_months', label: 'Last 3 months' }, { value: 'this_year', label: 'This year' },
  { value: 'all', label: 'All time' }, { value: 'custom', label: 'Custom dates…' },
]
const period = ref('this_month')
const from = ref('')
const to = ref('')
const r = ref(null)
const loading = ref(true)
const error = ref('')
const printError = ref('')

async function load() {
  if (period.value === 'custom' && !(from.value && to.value)) return
  loading.value = true
  error.value = ''
  try {
    const q = period.value === 'custom' ? { from: from.value, to: to.value } : { period: period.value }
    r.value = await get('/admin/reports/', { query: q })
  } catch {
    error.value = 'Could not load the report. Please try again.'
  } finally {
    loading.value = false
  }
}
watch([period, from, to], load)
onMounted(load)

const fmtDate = d => new Date(`${d}T00:00:00`).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
const dateRange = computed(() => (r.value ? (r.value.period.key === 'all' ? 'everything so far' : `${fmtDate(r.value.period.from)} – ${fmtDate(r.value.period.to)}`) : ''))
const monthLabel = m => new Date(`${m}-01T00:00:00`).toLocaleDateString('en-PH', { month: 'long', year: 'numeric' })
const totalConsults = computed(() => (r.value?.rnds || []).reduce((s, x) => s + x.consultations, 0))
const share = x => (totalConsults.value ? Math.round(x.consultations / totalConsults.value * 100) : 0)

function print() {
  printError.value = ''
  const x = r.value
  const sections = [
    { heading: 'Summary', rows: [
      ['Consultations completed', String(x.consultations.completed)],
      ...Object.entries(x.consultations.by_format).map(([f, n]) => [`  ${f}`, String(n)]),
      ['Consultations cancelled', String(x.consultations.cancelled)],
      ['Payments received', `${peso(x.money.gross)} (${x.money.payments})`],
      ['Platform commission', peso(x.money.commission)],
      ["RNDs' share", peso(x.money.rnd_share)],
      ['Refunded', `${x.money.refunded.count} · ${peso(x.money.refunded.amount)}`],
      ['Waiting for refund', `${x.money.refund_pending.count} · ${peso(x.money.refund_pending.amount)}`],
      ['New clients', String(x.people.new_clients)],
      ['RNDs approved', String(x.people.rnds_approved)],
      ['Support requests', String(x.people.support_requests)],
    ] },
  ]
  if (x.monthly.length > 1) {
    sections.push({ heading: 'By month', rows: x.monthly.map(m => [monthLabel(m.month), `${m.completed} completed · ${m.cancelled} cancelled · ${peso(m.gross)} received · ${peso(m.commission)} commission`]) })
  }
  const ok = printDocument({
    title: 'Platform report', number: `${x.period.label} · ${dateRange.value}`, sections,
    table: [['RND', 'Consultations', 'Received', 'Commission', 'RND share', 'Rating'],
      ...x.rnds.map(z => [z.name, String(z.consultations), peso(z.gross), peso(z.commission), peso(z.rnd_share), z.rating ? `${z.rating} (${z.reviews})` : '—'])],
    note: `Generated ${new Date(x.generated_at).toLocaleString('en-PH', { timeZone: 'Asia/Manila' })}. Payments are counted by the date they were received; commission is the rate frozen on each invoice.`,
  })
  if (!ok) printError.value = 'Allow pop-ups for this site to print the report.'
}

function downloadCsv() {
  const x = r.value
  const cell = v => `"${String(v ?? '').replace(/"/g, '""')}"`
  const lines = [
    ['NutriMatch platform report', x.period.label, x.period.from, x.period.to],
    [],
    ['Metric', 'Value'],
    ['Consultations completed', x.consultations.completed], ['Consultations cancelled', x.consultations.cancelled],
    ...Object.entries(x.consultations.by_format).map(([f, n]) => [`Completed - ${f}`, n]),
    ['Payments', x.money.payments], ['Payments received (PHP)', x.money.gross], ['Platform commission (PHP)', x.money.commission],
    ["RNDs' share (PHP)", x.money.rnd_share], ['Refunded (PHP)', x.money.refunded.amount], ['Waiting for refund (PHP)', x.money.refund_pending.amount],
    ['New clients', x.people.new_clients], ['RNDs approved', x.people.rnds_approved], ['Support requests', x.people.support_requests],
    [],
    ['Month', 'Completed', 'Cancelled', 'Payments', 'Received (PHP)', 'Commission (PHP)'],
    ...x.monthly.map(m => [m.month, m.completed, m.cancelled, m.payments, m.gross, m.commission]),
    [],
    ['RND', 'Specialization', 'Consultations', 'Payments', 'Received (PHP)', 'Commission (PHP)', 'RND share (PHP)', 'Rating', 'Reviews'],
    ...x.rnds.map(z => [z.name, z.specialization, z.consultations, z.payments, z.gross, z.commission, z.rnd_share, z.rating ?? '', z.reviews]),
  ]
  const csv = '﻿' + lines.map(row => row.map(cell).join(',')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const a = document.createElement('a')
  a.href = url
  a.download = `nutrimatch-report-${x.period.from}-to-${x.period.to}.csv`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>

<style scoped>
.toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
.period { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.period .nm-select { min-width: 180px; }
.date { width: 160px; min-height: 42px; }
.to { font-size: 0.82rem; color: #6a7a6a; }
.exports { display: flex; gap: 8px; }
.period-label { margin: 0 0 14px; }
.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin: 16px 0; }
.nm-panel + .nm-panel { margin-top: 16px; }
.two .nm-panel { margin-top: 0; }
.facts { margin: 12px 0 0; }
.facts div { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-bottom: 1px solid #f0f2f0; font-size: 0.85rem; }
.facts dt { color: #5a6a5a; }
.facts dt.sub { padding-left: 12px; color: #8a9a8a; }
.facts dd { margin: 0; font-weight: 600; color: #1a3a1a; text-align: right; }
.facts dd.warn { color: #a16207; }
.bar { height: 6px; background: #eef3ec; border-radius: 4px; overflow: hidden; margin-bottom: 3px; }
.bar span { display: block; height: 100%; background: #1f8f5c; border-radius: 4px; }
@media (max-width: 760px) { .two { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 640px) {
  .bar { display: inline-block; width: 120px; vertical-align: middle; margin: 0 6px 0 0; }
  .toolbar, .period { align-items: stretch; }
  .period { width: 100%; }
  .period .nm-select, .date { flex: 1; min-width: 0; width: auto; }
  .exports { width: 100%; }
  .exports button { flex: 1; justify-content: center; }
}
</style>
