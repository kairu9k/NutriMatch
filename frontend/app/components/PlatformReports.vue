<template>
  <div class="nm-page reports">
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
        <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="!r" @click="downloadCsv"><Download :size="14" aria-hidden="true" /> CSV</button>
        <button type="button" class="nm-btn-dark nm-btn-sm" :disabled="!r" @click="print"><Printer :size="14" aria-hidden="true" /> Print / PDF</button>
      </div>
    </div>
    <p v-if="printError" class="nm-error">{{ printError }}</p>
    <p v-if="error" class="nm-error">{{ error }}</p>
    <p v-if="loading && !r" class="nm-muted">Loading…</p>

    <template v-if="r">
      <div class="tab-row">
        <div class="nm-tabs" role="tablist" aria-label="Report sections">
          <button v-for="t in TABS" :key="t.key" type="button" role="tab" class="nm-tab" :class="{ active: tab === t.key }" :aria-selected="tab === t.key" @click="setTab(t.key)">{{ t.label }}</button>
        </div>
        <p class="nm-panel-sub period-label">{{ r.period.label }}, {{ dateRange }}</p>
      </div>

      <!-- OVERVIEW -->
      <template v-if="tab === 'overview'">
        <section class="nm-panel figs-panel" aria-label="Summary">
          <dl class="figs">
            <div class="fig"><dt>Consultations completed</dt><dd>{{ r.consultations.completed }}</dd><p>{{ r.consultations.cancelled }} cancelled</p></div>
            <div class="fig"><dt>Payments received</dt><dd>{{ peso(r.money.gross) }}</dd><p>{{ r.money.payments }} payment{{ r.money.payments === 1 ? '' : 's' }}</p></div>
            <div class="fig"><dt>Platform commission</dt><dd>{{ peso(r.money.commission) }}</dd><p>{{ peso(r.money.rnd_share) }} to RNDs</p></div>
            <div class="fig"><dt>New clients</dt><dd>{{ r.clients.new }}</dd><p>{{ r.clients.in_care_now }} in active care now</p></div>
            <div class="fig"><dt>RNDs consulting</dt><dd>{{ r.rnd_stats.active }}</dd><p>of {{ r.rnd_stats.approved_now }} approved</p></div>
            <div class="fig"><dt>Support requests</dt><dd>{{ r.people.support_requests }}</dd><p>opened in this period</p></div>
          </dl>
        </section>
        <div v-if="hasMonths" class="two">
          <section class="nm-panel">
            <h2 class="nm-panel-title">Consultations per month</h2>
            <p class="nm-panel-sub chart-sub">Completed and cancelled</p>
            <BarChart :rows="monthRows(m => ({ completed: m.completed, cancelled: m.cancelled }))" :series="CONSULT_SERIES" label="Consultations per month" />
          </section>
          <section class="nm-panel">
            <h2 class="nm-panel-title">Money per month</h2>
            <p class="nm-panel-sub chart-sub">Payments kept, split into the RNDs' share and the platform commission</p>
            <BarChart :rows="monthRows(m => ({ rnd_share: m.rnd_share, commission: m.commission }))" :series="MONEY_SERIES" label="Money per month" :format="v => peso(v)" />
          </section>
        </div>
        <p v-else class="nm-note plain-note">Pick a period longer than a month to see month-by-month charts.</p>
      </template>

      <!-- CLIENTS -->
      <template v-else-if="tab === 'clients'">
        <section class="nm-panel figs-panel" aria-label="Clients">
          <dl class="figs">
            <div class="fig"><dt>New sign-ups</dt><dd>{{ r.clients.new }}</dd><p>{{ r.clients.onboarded_of_new }} finished onboarding</p></div>
            <div class="fig"><dt>In active care</dt><dd>{{ r.clients.in_care_now }}</dd><p>right now</p></div>
            <div class="fig"><dt>Waiting for a first consultation</dt><dd>{{ r.clients.waiting_now }}</dd><p>booked, not yet confirmed or seen</p></div>
            <div class="fig"><dt>Clients seen</dt><dd>{{ r.clients.consulted }}</dd><p>had a consultation in this period</p></div>
            <div class="fig"><dt>Came back</dt><dd>{{ pct(r.clients.repeat_pct) }}</dd><p>of those seen have had 2 or more consultations</p></div>
            <div class="fig"><dt>Days to a first consultation</dt><dd>{{ days(r.clients.days_to_first_median) }}</dd><p>median, from sign-up</p></div>
            <div class="fig"><dt>Discharged</dt><dd>{{ r.clients.discharged }}</dd><p>care ended in this period</p></div>
          </dl>
        </section>
        <section v-if="hasMonths" class="nm-panel">
          <h2 class="nm-panel-title">New clients per month</h2>
          <BarChart :rows="monthRows(m => ({ new_clients: m.new_clients }))" :series="[{ key: 'new_clients', label: 'New clients' }]" label="New clients per month" />
        </section>
        <p v-else class="nm-note plain-note">Pick a period longer than a month to see month-by-month charts.</p>
      </template>

      <!-- RNDS -->
      <template v-else-if="tab === 'rnds'">
        <section class="nm-panel figs-panel" aria-label="RNDs">
          <dl class="figs">
            <div class="fig"><dt>Applications</dt><dd>{{ r.rnd_stats.applications }}</dd><p>with a confirmed email</p></div>
            <div class="fig"><dt>Approved</dt><dd>{{ r.rnd_stats.approved }}</dd><p>{{ r.rnd_stats.rejected }} rejected</p></div>
            <div class="fig"><dt>Days to review</dt><dd>{{ days(r.rnd_stats.days_to_review_median) }}</dd><p>median, from applying</p></div>
            <div class="fig"><dt>Consulting</dt><dd>{{ r.rnd_stats.active }}</dd><p>of {{ r.rnd_stats.approved_now }} approved RNDs</p></div>
            <div class="fig"><dt>Taking new clients</dt><dd>{{ r.rnd_stats.taking_new_clients }}</dd><p>right now</p></div>
            <div class="fig"><dt>Patients per RND</dt><dd>{{ r.rnd_stats.patients_per_rnd ?? '—' }}</dd><p>in active care, on average</p></div>
            <div class="fig"><dt>Average rating</dt><dd>{{ r.rnd_stats.rating ? `${r.rnd_stats.rating} ★` : '—' }}</dd><p>{{ r.rnd_stats.reviews }} review{{ r.rnd_stats.reviews === 1 ? '' : 's' }} in this period</p></div>
          </dl>
        </section>
        <section v-if="hasMonths" class="nm-panel">
          <h2 class="nm-panel-title">Applications per month</h2>
          <BarChart :rows="monthRows(m => ({ applications: m.applications }))" :series="[{ key: 'applications', label: 'Applications' }]" label="RND applications per month" />
        </section>
        <section class="nm-panel">
          <div class="nm-panel-head">
            <div>
              <h2 class="nm-panel-title">Each RND</h2>
              <p class="nm-panel-sub">Approved RNDs in this period. The rating is overall.</p>
            </div>
          </div>
          <div v-if="!r.rnds.length" class="nm-empty"><BarChart3 :size="28" aria-hidden="true" /><p>No approved RNDs yet.</p></div>
          <div v-else class="nm-table-wrap">
            <table class="nm-table stack">
              <thead>
                <tr><th>RND</th><th class="nm-num">Consultations</th><th class="nm-num">Received</th><th class="nm-num">Commission</th><th class="nm-num">RND share</th><th>Rating</th><th style="width: 140px">Share of consultations</th></tr>
              </thead>
              <tbody>
                <tr v-for="x in r.rnds" :key="x.id" class="clickable" @click="navigateTo(`/users/${x.id}`)">
                  <td><p class="nm-row-title">{{ x.name }}</p><p class="nm-row-sub">{{ x.specialization || '—' }}</p></td>
                  <td data-label="Consultations" class="nm-num">{{ x.consultations }}</td>
                  <td data-label="Received" class="nm-num">{{ peso(x.gross) }}</td>
                  <td data-label="Commission" class="nm-num">{{ peso(x.commission) }}</td>
                  <td data-label="RND share" class="nm-num">{{ peso(x.rnd_share) }}</td>
                  <td data-label="Rating">{{ x.rating ? `${x.rating} ★ (${x.reviews})` : '—' }}</td>
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

      <!-- CONSULTATIONS -->
      <template v-else-if="tab === 'consultations'">
        <section class="nm-panel figs-panel" aria-label="Consultations">
          <dl class="figs">
            <div class="fig"><dt>Completed</dt><dd>{{ r.consultations.completed }}</dd><p>{{ formatSplit }}</p></div>
            <div class="fig"><dt>Cancelled</dt><dd>{{ r.consultations.cancelled }}</dd><p>{{ pct(cancelledPct) }} of those due</p></div>
            <div class="fig"><dt>No-shows</dt><dd>{{ r.consultations.cancelled_reasons.no_show }}</dd><p>the client didn't come</p></div>
            <div class="fig"><dt>Not paid in time</dt><dd>{{ r.consultations.cancelled_reasons.not_paid }}</dd><p>cancelled at the start time</p></div>
            <div class="fig"><dt>Cancelled for other reasons</dt><dd>{{ r.consultations.cancelled_reasons.other }}</dd><p>by the client, the RND or NutriMatch</p></div>
          </dl>
        </section>
        <section v-if="hasMonths" class="nm-panel">
          <h2 class="nm-panel-title">Consultations per month</h2>
          <p class="nm-panel-sub chart-sub">Completed and cancelled</p>
          <BarChart :rows="monthRows(m => ({ completed: m.completed, cancelled: m.cancelled }))" :series="CONSULT_SERIES" label="Consultations per month" />
        </section>
        <p v-else class="nm-note plain-note">Pick a period longer than a month to see month-by-month charts.</p>
      </template>

      <!-- MONEY -->
      <template v-else-if="tab === 'money'">
        <section class="nm-panel figs-panel" aria-label="Money">
          <dl class="figs">
            <div class="fig"><dt>Payments received</dt><dd>{{ peso(r.money.gross) }}</dd><p>{{ r.money.payments }} payment{{ r.money.payments === 1 ? '' : 's' }}</p></div>
            <div class="fig"><dt>Platform commission</dt><dd>{{ peso(r.money.commission) }}</dd><p>{{ r.money.take_rate_pct == null ? 'no payments kept yet' : `${r.money.take_rate_pct}% of payments kept` }}</p></div>
            <div class="fig"><dt>RNDs' share</dt><dd>{{ peso(r.money.rnd_share) }}</dd><p>earned by RNDs</p></div>
            <div class="fig"><dt>Payouts sent</dt><dd>{{ peso(r.money.payouts_sent.amount) }}</dd><p>{{ r.money.payouts_sent.count }} payout{{ r.money.payouts_sent.count === 1 ? '' : 's' }}</p></div>
            <div class="fig"><dt>Refunded</dt><dd>{{ peso(r.money.refunded.amount) }}</dd><p>{{ r.money.refunded.count }} refund{{ r.money.refunded.count === 1 ? '' : 's' }}</p></div>
            <div class="fig" :class="{ warn: r.money.refund_pending.count }"><dt>Waiting for a refund</dt><dd>{{ peso(r.money.refund_pending.amount) }}</dd><p>{{ r.money.refund_pending.count }} to send</p></div>
          </dl>
        </section>
        <section v-if="hasMonths" class="nm-panel">
          <h2 class="nm-panel-title">Money per month</h2>
          <p class="nm-panel-sub chart-sub">Payments kept, split into the RNDs' share and the platform commission</p>
          <BarChart :rows="monthRows(m => ({ rnd_share: m.rnd_share, commission: m.commission }))" :series="MONEY_SERIES" label="Money per month" :format="v => peso(v)" />
        </section>
        <section v-if="r.monthly.length" class="nm-panel">
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
      </template>
    </template>
  </div>
</template>

<script setup>
// Platform report for a chosen period (GET /api/admin/reports/, core/reports.py),
// printable (utils/printDoc.js) and downloadable as CSV.
import { BarChart3, Download, Printer } from 'lucide-vue-next'
import { printDocument } from '~/utils/printDoc'

const { get } = useApi()
const route = useRoute()
const router = useRouter()

// Tabs (?tab=), one per part of the platform (2026-10-24 plan)
const TABS = [
  { key: 'overview', label: 'Overview' }, { key: 'clients', label: 'Clients' }, { key: 'rnds', label: 'RNDs' },
  { key: 'consultations', label: 'Consultations' }, { key: 'money', label: 'Money' },
]
const tab = ref(TABS.some(t => t.key === route.query.tab) ? route.query.tab : 'overview')
function setTab(key) {
  tab.value = key
  router.replace({ query: { ...route.query, tab: key === 'overview' ? undefined : key } })
}
// fixed order, so a colour always means the same series: green first, gold second
const CONSULT_SERIES = [{ key: 'completed', label: 'Completed' }, { key: 'cancelled', label: 'Cancelled' }]
const MONEY_SERIES = [{ key: 'rnd_share', label: "RNDs' share" }, { key: 'commission', label: 'Commission' }]
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
const dateRange = computed(() => (r.value ? (r.value.period.key === 'all' ? 'everything so far' : `${fmtDate(r.value.period.from)} to ${fmtDate(r.value.period.to)}`) : ''))
const monthLabel = m => new Date(`${m}-01T00:00:00`).toLocaleDateString('en-PH', { month: 'long', year: 'numeric' })
const monthShort = m => new Date(`${m}-01T00:00:00`).toLocaleDateString('en-PH', { month: 'short' })
const hasMonths = computed(() => (r.value?.monthly || []).length > 1)
const monthRows = pick => (r.value?.monthly || []).map(m => ({ label: monthLabel(m.month), short: monthShort(m.month), values: pick(m) }))
const pct = v => (v == null ? '—' : `${v}%`)
const days = v => (v == null ? '—' : `${v} day${v === 1 ? '' : 's'}`)
const cancelledPct = computed(() => {
  const c = r.value?.consultations
  const due = c ? c.completed + c.cancelled : 0
  return due ? Math.round(c.cancelled / due * 100) : null
})
const formatSplit = computed(() => Object.entries(r.value?.consultations.by_format || {}).map(([f, n]) => `${n} ${f.toLowerCase()}`).join(', ') || 'none yet')
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
      ['Refunded', `${x.money.refunded.count}, ${peso(x.money.refunded.amount)}`],
      ['Waiting for refund', `${x.money.refund_pending.count}, ${peso(x.money.refund_pending.amount)}`],
      ['Payouts sent', `${x.money.payouts_sent.count}, ${peso(x.money.payouts_sent.amount)}`],
      ['Support requests', String(x.people.support_requests)],
    ] },
    { heading: 'Clients', rows: [
      ['New sign-ups', `${x.clients.new} (${x.clients.onboarded_of_new} finished onboarding)`],
      ['In active care now', String(x.clients.in_care_now)],
      ['Clients seen', String(x.clients.consulted)],
      ['Came back (2+ consultations)', pct(x.clients.repeat_pct)],
      ['Days to a first consultation (median)', days(x.clients.days_to_first_median)],
      ['Discharged', String(x.clients.discharged)],
    ] },
    { heading: 'RNDs', rows: [
      ['Applications', String(x.rnd_stats.applications)],
      ['Approved / rejected', `${x.rnd_stats.approved} / ${x.rnd_stats.rejected}`],
      ['Days to review (median)', days(x.rnd_stats.days_to_review_median)],
      ['Consulting', `${x.rnd_stats.active} of ${x.rnd_stats.approved_now}`],
      ['Patients per RND', String(x.rnd_stats.patients_per_rnd ?? '—')],
      ['Average rating', x.rnd_stats.rating ? `${x.rnd_stats.rating} (${x.rnd_stats.reviews} reviews)` : '—'],
    ] },
  ]
  if (x.monthly.length > 1) {
    sections.push({ heading: 'By month', rows: x.monthly.map(m => [monthLabel(m.month), `${m.completed} completed, ${m.cancelled} cancelled, ${peso(m.gross)} received, ${peso(m.commission)} commission`]) })
  }
  const ok = printDocument({
    title: 'Platform report', number: `${x.period.label}, ${dateRange.value}`, sections,
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
    ['Payouts sent', x.money.payouts_sent.count], ['Payouts sent (PHP)', x.money.payouts_sent.amount], ['Take rate (%)', x.money.take_rate_pct ?? ''],
    ['New clients', x.clients.new], ['Finished onboarding (of new)', x.clients.onboarded_of_new], ['In active care now', x.clients.in_care_now],
    ['Clients seen', x.clients.consulted], ['Came back (%)', x.clients.repeat_pct ?? ''], ['Days to first consultation (median)', x.clients.days_to_first_median ?? ''],
    ['Discharged', x.clients.discharged], ['RND applications', x.rnd_stats.applications], ['RNDs approved', x.rnd_stats.approved],
    ['RNDs rejected', x.rnd_stats.rejected], ['Days to review (median)', x.rnd_stats.days_to_review_median ?? ''], ['RNDs consulting', x.rnd_stats.active],
    ['No-shows', x.consultations.cancelled_reasons.no_show], ['Not paid in time', x.consultations.cancelled_reasons.not_paid],
    ['Support requests', x.people.support_requests],
    [],
    ['Month', 'Completed', 'Cancelled', 'Payments', 'Received (PHP)', 'Commission (PHP)', 'RND share (PHP)', 'New clients', 'RND applications'],
    ...x.monthly.map(m => [m.month, m.completed, m.cancelled, m.payments, m.gross, m.commission, m.rnd_share, m.new_clients, m.applications]),
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
.reports { display: flex; flex-direction: column; gap: 16px; }
.reports > * { margin: 0; }
.toolbar { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.period { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.period .nm-select { min-width: 180px; }
.date { width: 160px; min-height: 42px; }
.to { font-size: 0.82rem; color: #6a7a6a; }
.exports { display: flex; gap: 8px; }
.tab-row { display: flex; align-items: center; justify-content: space-between; gap: 10px 16px; flex-wrap: wrap; }
.period-label { margin: 0; }
.chart-sub { margin: 2px 0 14px; }
.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }

/* figures: one divided panel, three across */
.figs-panel { padding: 0; overflow: hidden; }
.figs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 0; }
.fig { display: flex; flex-direction: column; gap: 2px; padding: 16px 20px; min-width: 0; border-left: 1px solid #d9e3dc; border-top: 1px solid #d9e3dc; }
.fig:nth-child(3n + 1) { border-left: none; }
.fig:nth-child(-n + 3) { border-top: none; }
.fig dt { order: 1; font-size: 0.82rem; color: #4a5a4a; }
.fig dd { order: 0; margin: 0; font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1a3a1a; font-variant-numeric: lining-nums tabular-nums; }
.fig p { order: 2; margin: 0; font-size: 0.76rem; color: #6a7a6a; line-height: 1.4; }
.fig.warn dd { color: #a37a0b; }

.bar { height: 6px; background: #e3efe7; border-radius: 4px; overflow: hidden; margin-bottom: 3px; }
.bar span { display: block; height: 100%; background: #278f60; border-radius: 4px; }
@media (max-width: 900px) { .two { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 640px) {
  .figs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fig { padding: 14px 16px; border-left: 1px solid #d9e3dc; border-top: 1px solid #d9e3dc; }
  .fig:nth-child(odd) { border-left: none; }
  .fig:nth-child(-n + 2) { border-top: none; }
  .fig:nth-child(3) { border-top: 1px solid #d9e3dc; }
  .fig dd { font-size: 1.3rem; }
  .bar { display: inline-block; width: 120px; vertical-align: middle; margin: 0 6px 0 0; }
  .toolbar, .period { align-items: stretch; }
  .period { width: 100%; }
  .period .nm-select, .date { flex: 1; min-width: 0; width: auto; }
  .exports { width: 100%; }
  .exports button { flex: 1; justify-content: center; }
  .nm-tabs { overflow-x: auto; flex-wrap: nowrap; }
}
</style>
