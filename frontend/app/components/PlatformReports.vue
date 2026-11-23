<template>
  <div class="nm-page reports">
    <section class="rh">
      <img class="rh-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="rh-fade" aria-hidden="true"></span>
      <div class="rh-txt">
        <p class="rh-eyebrow"><span></span>Platform reports</p>
        <h1 class="rh-title">How NutriMatch is doing</h1>
        <p v-if="r" class="rh-period"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg>{{ r.period.label }}, {{ dateRange }}</p>
      </div>
      <div class="exports">
        <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="!r" @click="downloadCsv"><Download :size="15" aria-hidden="true" /> CSV</button>
        <button type="button" class="nm-btn-dark nm-btn-sm" :disabled="!r" @click="print"><Printer :size="15" aria-hidden="true" /> Print / PDF</button>
      </div>
    </section>

    <div class="toolbar">
      <div class="period">
        <label class="p-sel">
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg><small>Period</small>
          <select v-model="period" class="nm-select" aria-label="Report period">
            <option v-for="p in PERIODS" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
          <svg class="ic p-chev" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
        </label>
        <template v-if="period === 'custom'">
          <DateField v-model="from" :max="to || todayIso" compact hint="Pick the first day." placeholder="Start date" aria-label="From" />
          <span class="to">to</span>
          <DateField v-model="to" :min="from" :max="todayIso" compact hint="Pick the last day." placeholder="End date" aria-label="To" />
        </template>
      </div>
    </div>
    <p v-if="printError" class="nm-error">{{ printError }}</p>
    <p v-if="error" class="nm-error">{{ error }}</p>
    <p v-if="loading && !r" class="nm-muted">Loading…</p>

    <template v-if="r">
      <div class="tab-row">
        <div class="nm-tabs" role="tablist" aria-label="Report sections">
          <button v-for="t in TABS" :key="t.key" type="button" role="tab" class="nm-tab" :class="{ active: tab === t.key }" :aria-selected="tab === t.key" @click="setTab(t.key)"><template v-if="t.key === 'overview'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /></svg></template><template v-else-if="t.key === 'clients'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><path d="M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" /></svg></template><template v-else-if="t.key === 'rnds'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /><path d="M9 12l2 2 4-4" /></svg></template><template v-else-if="t.key === 'consultations'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="14" height="12" rx="2" /><path d="M22 8l-6 4 6 4z" /></svg></template><template v-else><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg></template>{{ t.label }}</button>
        </div>
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
        <div v-if="r.monthly.length" class="two">
          <section class="nm-panel ch">
            <h2 class="nm-panel-title ch-title"><span class="ch-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="14" height="12" rx="2" /><path d="M22 8l-6 4 6 4z" /></svg></span>Consultations per month</h2>
            <p class="nm-panel-sub chart-sub">Completed and cancelled</p>
            <BarChart :rows="monthRows(m => ({ completed: m.completed, cancelled: m.cancelled }))" :series="CONSULT_SERIES" label="Consultations per month" />
          </section>
          <section class="nm-panel ch">
            <h2 class="nm-panel-title ch-title"><span class="ch-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg></span>Money per month</h2>
            <p class="nm-panel-sub chart-sub">Payments kept, split into the RNDs' share and the platform commission</p>
            <BarChart :rows="monthRows(m => ({ rnd_share: m.rnd_share, commission: m.commission }))" :series="MONEY_SERIES" label="Money per month" :format="v => peso(v)" />
          </section>
        </div>
        <p v-else class="nm-note plain-note chart-note"><span class="n-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18" /><path d="M7 15v3M12 10v8M17 6v12" /></svg></span><span><b>No chart yet</b>No months with activity in this period yet.</span></p>
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
        <section v-if="r.monthly.length" class="nm-panel ch">
          <h2 class="nm-panel-title ch-title"><span class="ch-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><path d="M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" /></svg></span>New clients per month</h2>
          <BarChart :rows="monthRows(m => ({ new_clients: m.new_clients }))" :series="[{ key: 'new_clients', label: 'New clients' }]" label="New clients per month" />
        </section>
        <p v-else class="nm-note plain-note chart-note"><span class="n-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18" /><path d="M7 15v3M12 10v8M17 6v12" /></svg></span><span><b>No chart yet</b>No months with activity in this period yet.</span></p>
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
        <section v-if="r.monthly.length" class="nm-panel ch">
          <h2 class="nm-panel-title ch-title"><span class="ch-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /><path d="M9 12l2 2 4-4" /></svg></span>Applications per month</h2>
          <BarChart :rows="monthRows(m => ({ applications: m.applications }))" :series="[{ key: 'applications', label: 'Applications' }]" label="RND applications per month" />
        </section>
        <p v-else class="nm-note plain-note chart-note"><span class="n-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18" /><path d="M7 15v3M12 10v8M17 6v12" /></svg></span><span><b>No chart yet</b>No months with activity in this period yet.</span></p>
        <section class="nm-panel ch">
          <div class="nm-panel-head">
            <div>
              <h2 class="nm-panel-title ch-title"><span class="ch-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z" /><path d="M9 12l2 2 4-4" /></svg></span>Each RND</h2>
              <p class="nm-panel-sub">Approved RNDs in this period. The rating is overall.</p>
            </div>
          </div>
          <div v-if="!r.rnds.length" class="nm-empty"><span class="e-ico"><BarChart3 :size="28" aria-hidden="true" /></span><p>No approved RNDs yet.</p></div>
          <div v-else class="nm-table-wrap">
            <table class="nm-table stack r-table">
              <thead>
                <tr><th>RND</th><th class="nm-num">Consultations</th><th class="nm-num">Received</th><th class="nm-num">Commission</th><th class="nm-num">RND share</th><th>Rating</th><th style="width: 140px">Share of consultations</th></tr>
              </thead>
              <tbody>
                <tr v-for="x in pagedRnds" :key="x.id" class="clickable" tabindex="0" @click="navigateTo(`/users/${x.id}`)" @keydown.enter="navigateTo(`/users/${x.id}`)">
                  <td><span class="r-who"><span class="r-av" aria-hidden="true">{{ initialsOf(x.name) }}</span><span><p class="nm-row-title">{{ x.name }}</p><p class="nm-row-sub">{{ x.specialization || '—' }}</p></span></span></td>
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
          <ListPager v-model:page="rndPage" :pages="rndPages" />
        </section>
      </template>

      <!-- CONSULTATIONS -->
      <template v-else-if="tab === 'consultations'">
        <section class="nm-panel figs-panel" aria-label="Consultations">
          <dl class="figs">
            <div class="fig"><dt>Completed</dt><dd>{{ r.consultations.completed }}</dd><p>{{ formatSplit }}</p></div>
            <div class="fig"><dt>Cancelled</dt><dd>{{ r.consultations.cancelled }}</dd><p>{{ pct(cancelledPct) }} of those due</p></div>
            <div class="fig"><dt>No-shows</dt><dd>{{ r.consultations.cancelled_reasons.no_show }}</dd><p>the client didn't come</p></div>
            <div class="fig"><dt>Not paid in time</dt><dd>{{ r.consultations.cancelled_reasons.not_paid }}</dd><p>cancelled 15 minutes before the start</p></div>
            <div class="fig"><dt>Cancelled for other reasons</dt><dd>{{ r.consultations.cancelled_reasons.other }}</dd><p>by the client, the RND or NutriMatch</p></div>
          </dl>
        </section>
        <section v-if="r.monthly.length" class="nm-panel ch">
          <h2 class="nm-panel-title ch-title"><span class="ch-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="14" height="12" rx="2" /><path d="M22 8l-6 4 6 4z" /></svg></span>Consultations per month</h2>
          <p class="nm-panel-sub chart-sub">Completed and cancelled</p>
          <BarChart :rows="monthRows(m => ({ completed: m.completed, cancelled: m.cancelled }))" :series="CONSULT_SERIES" label="Consultations per month" />
        </section>
        <p v-else class="nm-note plain-note chart-note"><span class="n-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18" /><path d="M7 15v3M12 10v8M17 6v12" /></svg></span><span><b>No chart yet</b>No months with activity in this period yet.</span></p>
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
        <section v-if="r.monthly.length" class="nm-panel ch">
          <h2 class="nm-panel-title ch-title"><span class="ch-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg></span>Money per month</h2>
          <p class="nm-panel-sub chart-sub">Payments kept, split into the RNDs' share and the platform commission</p>
          <BarChart :rows="monthRows(m => ({ rnd_share: m.rnd_share, commission: m.commission }))" :series="MONEY_SERIES" label="Money per month" :format="v => peso(v)" />
        </section>
        <section v-if="r.monthly.length" class="nm-panel ch">
          <h2 class="nm-panel-title ch-title"><span class="ch-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18M9 10v10" /></svg></span>By month</h2>
          <div class="nm-table-wrap">
            <table class="nm-table r-table m-table">
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
// all time first (user's call, 2026-10-26); a narrower period is one pick away
const period = ref('all')
const todayIso = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' })
const from = ref('')
const to = ref('')
const r = ref(null)
const loading = ref(true)
const error = ref('')
const printError = ref('')

async function load({ quiet = false } = {}) {
  if (period.value === 'custom' && !(from.value && to.value)) return
  if (!quiet) {
    loading.value = true
    error.value = ''
  }
  try {
    const q = period.value === 'custom' ? { from: from.value, to: to.value } : { period: period.value }
    r.value = await get('/admin/reports/', { query: q })
  } catch {
    if (!quiet) error.value = 'Could not load the report. Try again.'
  } finally {
    loading.value = false
  }
}
// a heavier request, so every 5 minutes rather than every minute
useAutoRefresh(() => load({ quiet: true }), { interval: 300000 })
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
// Each RND: 20 a page; a new period starts at page 1
const rndList = computed(() => r.value?.rnds || [])
const { page: rndPage, pages: rndPages, paged: pagedRnds } = usePager(rndList, { perPage: 20, resetOn: () => [period.value, from.value, to.value] })

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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const initialsOf = name => { const w = String(name || '?').split(' ').filter(Boolean); return (w.length > 1 ? w[0][0] + w[w.length - 1][0] : (w[0] || '?')[0]).toUpperCase() }
</script>

<style scoped>
.reports { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); display: flex; flex-direction: column; gap: 16px; font-family: 'DM Sans', sans-serif; color: #22362c; }
.reports > * { margin: 0; }
.ic { flex-shrink: 0; display: inline-block; }

/* ---------- hero ---------- */
.rh { position: relative; overflow: hidden; display: flex; align-items: center; gap: 20px; padding: 18px 26px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.rh > *:not(.rh-plate):not(.rh-fade) { position: relative; z-index: 1; }
.rh-plate { position: absolute; right: -50px; top: 50%; width: 220px; height: 220px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.rh-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 55%, rgba(0, 77, 58, 0.88) 75%, rgba(0, 77, 58, 0.65) 100%); }
.rh-txt { flex: 1; min-width: 0; }
.rh-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 6px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.rh-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.rh-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 700; line-height: 1.2; color: #fff; }
.rh-period { display: inline-flex; align-items: center; gap: 7px; margin: 0; padding: 5px 12px; border-radius: 999px; background: rgba(255, 255, 255, 0.12); font-size: 13px; font-weight: 600; color: rgba(255, 255, 255, 0.92); }
.rh-period .ic { color: #efbf04; }
.exports { display: flex; gap: 10px; margin-right: 140px; }
.exports .nm-btn-soft, .exports .nm-btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 44px; padding: 0 18px; border-radius: 12px; font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; }
.exports .nm-btn-soft { border: 1px solid rgba(255, 255, 255, 0.3); background: rgba(255, 255, 255, 0.1); color: #fff; }
.exports .nm-btn-dark { border: none; background: #efbf04; color: #004d3a; box-shadow: 0 10px 20px -12px rgba(0, 0, 0, 0.6); }
.exports button:disabled { opacity: 0.5; cursor: not-allowed; }

/* ---------- toolbar ---------- */
.toolbar { display: flex; justify-content: flex-start; align-items: center; gap: 12px; flex-wrap: wrap; }
.period { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.p-sel { display: flex; align-items: center; gap: 10px; min-width: 230px; height: 46px; padding: 0 16px; border-radius: 999px; background: #fff; color: #1f7a4d; box-sizing: border-box; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); cursor: pointer; }
.p-sel:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.p-sel small { font-size: 11px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a91; }
.p-sel .nm-select { flex: 1; width: auto; min-width: 0; height: 100%; padding: 0 !important; border: none !important; background: transparent !important; box-shadow: none !important; outline: none; appearance: none; -webkit-appearance: none; font-family: inherit; font-size: 14px; font-weight: 700; color: #14261e; cursor: pointer; }
.period :deep(.df-trigger) { min-height: 46px; border-radius: 12px; }
.to { font-size: 13px; font-weight: 700; color: #6b7d73; }
.tab-row { display: flex; align-items: center; justify-content: space-between; gap: 10px 16px; flex-wrap: wrap; }
.tab-row .nm-tabs { display: inline-flex; gap: 4px; max-width: 100%; margin: 0; padding: 5px; border: none; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); overflow-x: auto; scrollbar-width: none; }
.tab-row .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 36px; margin: 0; padding: 0 15px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.tab-row .nm-tab .ic { color: #8a9a91; }
.tab-row .nm-tab:hover:not(.active) { background: #f1f6f2; }
.tab-row .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.tab-row .nm-tab.active .ic { color: #efbf04; }

/* ---------- figures: one clean strip ---------- */
.figs-panel { padding: 0; border: 1.5px solid #c9d8cf; border-radius: 20px; background: #fff; box-shadow: 0 10px 24px -18px rgba(0, 77, 58, 0.35); overflow: hidden; }
.figs { display: flex; flex-wrap: wrap; margin: 0; }
.fig { flex: 1 1 180px; display: flex; flex-direction: column; gap: 6px; min-width: 0; padding: 16px 18px; box-shadow: -1px 0 0 #eef2ef, 0 -1px 0 #eef2ef; }
.fig dt { order: 0; display: flex; align-items: center; gap: 8px; font-size: 12.5px; font-weight: 700; color: #4a5a52; line-height: 1.3; }
.fig dt::before { content: ''; flex-shrink: 0; width: 8px; height: 8px; border-radius: 3px; background: #1f9d55; }
.fig:nth-child(6n + 2) dt::before, .fig:nth-child(6n + 3) dt::before { background: #efbf04; }
.fig:nth-child(6n + 4) dt::before { background: #3b5ba5; }
.fig:nth-child(6n + 6) dt::before { background: #a9b6ae; }
.fig dd { order: 1; margin: 0; font-family: 'DM Sans', sans-serif; font-size: 26px; font-weight: 800; letter-spacing: -0.01em; line-height: 1.1; color: #0e3a2c; font-variant-numeric: lining-nums tabular-nums; overflow-wrap: anywhere; }
.fig p { order: 2; margin: 0; font-size: 12.5px; font-weight: 600; color: #6b7d73; line-height: 1.35; }
.fig.warn { background: #fffbea; }
.fig.warn dd { color: #8a6500; }
.fig.warn dt::before { background: #efbf04; }

/* ---------- chart + table panels ---------- */
.two { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.ch { padding: 22px 24px; border: none; border-radius: 22px; background: #fff; box-shadow: var(--sh); }
.ch-title { display: flex; align-items: center; gap: 12px; margin: 0; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.ch-ico { flex-shrink: 0; width: 40px; height: 40px; border-radius: 12px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.chart-sub { margin: 4px 0 16px 52px; font-size: 13px; color: #6b7d73; }
.ch > .ch-title + :not(.chart-sub) { margin-top: 16px; }
.ch .nm-panel-head { margin-bottom: 14px; }
.ch .nm-panel-head .nm-panel-sub { margin: 4px 0 0 52px; font-size: 13px; color: #6b7d73; }
.chart-note { display: flex; align-items: center; gap: 14px; padding: 16px 20px; border: 1.5px dashed #b9c8e6; border-radius: 18px; background: #f5f7fd; font-size: 13px; color: #4a5f8c; }
.chart-note b { display: block; font-size: 14.5px; color: #1e3560; }
.n-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; background: #fff; color: #2e4a86; box-shadow: 0 0 0 1px #dde4f4; display: inline-flex; align-items: center; justify-content: center; }
.reports :deep(.nm-empty) { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 24px 10px; text-align: center; }
.e-ico { width: 56px; height: 56px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.ch .nm-table-wrap { margin: 0 -24px; border: none; border-radius: 0; overflow-x: auto; }
.r-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.r-table thead th { padding: 13px 14px; background: #004d3a; border: none; text-align: left !important; font-size: 12.5px; font-weight: 700; color: #fff; text-transform: none; letter-spacing: 0; white-space: nowrap; }
.r-table th:first-child, .r-table td:first-child { padding-left: 24px; }
.r-table th:last-child, .r-table td:last-child { padding-right: 24px; }
.r-table tbody td { padding: 14px; border-bottom: 1px solid #eef2ef; text-align: left !important; vertical-align: middle; color: #22362c; }
.r-table tbody tr:last-child td { border-bottom: none; }
.r-table tbody tr.clickable { cursor: pointer; }
.r-table tbody tr.clickable:hover td { background: #f7faf8; }
.r-table tbody tr:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.r-who { display: flex; align-items: center; gap: 12px; }
.r-av { flex-shrink: 0; width: 38px; height: 38px; border-radius: 50%; background: #e3efe7; color: #004d3a; font-size: 12.5px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; border: 2px solid #fff; box-shadow: 0 0 0 2px #efbf04; }
.r-table .nm-row-title { margin: 0; font-size: 14.5px; font-weight: 800; color: #0e3a2c; }
.r-table .nm-row-sub { margin: 2px 0 0; font-size: 12.5px; color: #8a9a91; }
.m-table tbody td:first-child { font-weight: 800; color: #0e3a2c; }
.bar { height: 8px; margin-bottom: 4px; border-radius: 999px; background: #e3efe7; overflow: hidden; }
.bar span { display: block; height: 100%; border-radius: 999px; background: linear-gradient(90deg, #1f9d55, #efbf04); }

@media (max-width: 900px) { .two { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 760px) {
  .reports { padding-bottom: 110px; }
  .rh { flex-direction: column; align-items: stretch; padding: 20px 18px; border-radius: 22px; }
  .rh-plate { width: 160px; height: 160px; right: -50px; top: 20px; transform: none; }
  .exports { margin: 0; }
  .exports button { flex: 1; }
  .ch { padding: 18px; }
  .ch .nm-table-wrap { margin: 0 -18px; }
  .chart-sub, .ch .nm-panel-head .nm-panel-sub { margin-left: 0; }
}
@media (max-width: 640px) {
  .fig { flex-basis: 140px; padding: 14px 16px; }
  .fig dd { font-size: 22px; }
  .bar { display: inline-block; width: 120px; vertical-align: middle; margin: 0 6px 0 0; }
  .toolbar, .period { align-items: stretch; }
  .period { width: 100%; }
  .p-sel { width: 100%; }
  .period :deep(.df-trigger) { flex: 1; min-width: 0; width: auto; }
  .tab-row .nm-tabs { display: flex; width: 100%; border-radius: 16px; }
  .r-table thead { display: none; }
}
</style>