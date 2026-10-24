<template>
  <div class="nm-page admin-dash">
    <p v-if="error" class="nm-error">{{ error }} <button type="button" class="nm-panel-link" @click="load()">Try again</button></p>

    <!-- BANNER: greeting and summary (nm-hero in portal.css, one column here) -->
    <section class="nm-hero greet-only">
      <div class="nm-hero-greet">
        <p class="nm-hero-date">{{ longToday }}</p>
        <h1 class="nm-hero-title">Good {{ partOfDay }}, {{ auth.user?.first_name }}</h1>
        <p class="nm-hero-sub">{{ summaryLine }}</p>
        <p class="updated">
          <span>{{ updatedText }}</span>
          <button type="button" class="refresh" :disabled="refreshing" aria-label="Refresh the dashboard" @click="load()">
            <RefreshCw :size="14" :class="{ spin: refreshing }" aria-hidden="true" /> Refresh
          </button>
        </p>
      </div>
    </section>

    <!-- NEEDS ATTENTION: the shared strip; its pop-up lists the admin's own to-do,
         then what to keep an eye on (the app or the RND handles those) -->
    <NeedsAttention v-if="dash" :count="dash.attention.length" :urgent="attnUrgent" :titles="attnTitles">
      <h3 class="attn-h">Your to-do</h3>
      <p v-if="!todoItems.length" class="attn-none">Nothing to do right now.</p>
      <ul v-else class="attn-list">
        <li v-for="a in todoItems" :key="a.key" class="attn todo-item">
          <CircleDot :size="16" class="attn-icon" aria-hidden="true" />
          <span class="attn-main"><strong>{{ a.title }}</strong><small>{{ a.detail }}</small>
            <small v-if="a.people.length" class="attn-people">{{ peopleText(a.people) }}</small></span>
          <NuxtLink :to="a.link" class="nm-btn-dark nm-btn-sm">{{ ACTIONS[a.key] || 'Open' }}</NuxtLink>
        </li>
      </ul>
      <h3 class="attn-h">Keep an eye on</h3>
      <p class="attn-sub">For your information. The app or the RND handles these.</p>
      <p v-if="!watchItems.length" class="attn-none">Nothing to watch right now.</p>
      <ul v-else class="attn-list">
        <li v-for="a in watchItems" :key="a.key" class="attn watch">
          <Info :size="16" class="attn-icon" aria-hidden="true" />
          <span class="attn-main"><strong>{{ a.title }}</strong><small>{{ a.detail }}</small>
            <small v-if="a.people.length" class="attn-people">{{ peopleText(a.people) }}</small></span>
          <NuxtLink :to="a.link" class="nm-panel-link">View</NuxtLink>
        </li>
      </ul>
    </NeedsAttention>

    <div v-if="dash" class="nm-grid">
      <!-- MONTH VS LAST MONTH -->
      <section class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">This month vs last month</h2>
            <p class="nm-panel-sub">{{ dash.compare.label }}, the same number of days</p>
          </div>
        </div>
        <div v-for="m in dash.compare.metrics" :key="m.key" class="cmp">
          <span class="cmp-label">{{ METRIC_LABEL[m.key] }}</span>
          <span class="cmp-now">{{ money(m) ? peso(m.now) : m.now }}</span>
          <ChangeBadge :now="m.now" :before="m.before" :pct="m.change_pct" :money="money(m)" />
          <span class="cmp-before">was {{ money(m) ? peso(m.before) : m.before }}</span>
        </div>
      </section>

      <!-- AT A GLANCE: nine figures, 3 x 3, each a link -->
      <section class="nm-panel today-panel" aria-label="At a glance">
        <div class="figs nine">
          <NuxtLink v-for="t in todayFigures" :key="t.label" :to="t.link" class="fig" :class="t.tone">
            <strong>{{ t.value }}</strong><span>{{ t.label }}</span>
          </NuxtLink>
        </div>
      </section>
    </div>

    <!-- OVERVIEW: clients, RNDs, platform. Three divided columns. -->
    <section v-if="ov" class="nm-panel overview" aria-label="Overview">
      <div class="ov-col">
        <div class="ov-head"><h2 class="nm-panel-title">Clients</h2><NuxtLink to="/users?tab=clients" class="nm-panel-link">All clients</NuxtLink></div>
        <dl class="ov-figs">
          <div><dt>In active care</dt><dd>{{ ov.clients.in_care }}</dd></div>
          <div><dt>New this month</dt><dd>{{ ov.clients.new_this_month }}</dd></div>
          <div><dt>Finished onboarding</dt><dd>{{ pct(ov.clients.onboarded_pct) }}</dd></div>
        </dl>
        <p class="ov-trend-label">New clients per month</p>
        <Sparkline :points="ov.clients.trend" label="New clients per month" />
      </div>
      <div class="ov-col">
        <div class="ov-head"><h2 class="nm-panel-title">RNDs</h2><NuxtLink to="/users?tab=rnds" class="nm-panel-link">All RNDs</NuxtLink></div>
        <dl class="ov-figs">
          <div><dt>Consulted in 30 days</dt><dd>{{ ov.rnds.active_30_days }} <small>of {{ ov.rnds.approved }} approved</small></dd></div>
          <div><dt>Clients can book</dt><dd>{{ ov.rnds.bookable }}</dd></div>
          <div><dt>Calendar booked, next 7 days</dt><dd>{{ pct(ov.rnds.calendar_filled_pct) }}</dd></div>
        </dl>
        <p class="ov-trend-label">RNDs who consulted, per month</p>
        <Sparkline :points="ov.rnds.trend" label="RNDs who consulted, per month" />
      </div>
      <div class="ov-col">
        <div class="ov-head"><h2 class="nm-panel-title">Platform</h2><NuxtLink to="/platform-reports" class="nm-panel-link">Reports</NuxtLink></div>
        <dl class="ov-figs">
          <div><dt>Consultations this month</dt><dd>{{ ov.platform.consultations_this_month }}</dd></div>
          <div><dt>Payments this month</dt><dd>{{ peso(ov.platform.payments_this_month) }}</dd></div>
          <div><dt>Cancelled, last 30 days</dt><dd>{{ pct(ov.platform.cancelled_pct_30_days) }}</dd></div>
        </dl>
        <p class="ov-trend-label">Payments per month</p>
        <Sparkline :points="ov.platform.trend" label="Payments per month" :format="v => peso(v)" />
      </div>
    </section>

    <div v-if="dash">
      <!-- RECENT ADMIN ACTIVITY: click a row for the details -->
      <section class="nm-panel">
        <div class="nm-panel-head act-head">
          <h2 class="nm-panel-title">Recent admin activity</h2>
          <NuxtLink to="/audit-logs?scope=admin" class="nm-btn-soft nm-btn-sm">View all</NuxtLink>
        </div>
        <p v-if="!activity.length" class="act-empty">Nothing yet. Approvals, account changes, refunds and payouts show up here.</p>
        <!-- same rows as the client dashboard's Recent activity; gold dot = in the last 24 hours -->
        <button v-for="a in activity" :key="a.id" type="button" class="act-row" @click="openLog = a">
          <span class="act-dot" :class="{ fresh: now - new Date(a.created_at) < DAY_MS }" aria-hidden="true"></span>
          <span class="act-text">
            <span class="act-title">{{ auditLabel(a.action) }}</span>
            <span class="act-time">{{ a.user ? `${a.user.first_name} ${a.user.last_name}` : 'System' }}, {{ timeAgo(a.created_at) }}</span>
          </span>
        </button>
      </section>
    </div>

    <!-- ACTIVITY DETAILS (pop-up, only when a row is clicked) -->
    <div v-if="openLog" class="nm-modal-overlay" @click.self="openLog = null">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="log-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="openLog = null"><X :size="18" aria-hidden="true" /></button>
        <h2 id="log-title" class="nm-modal-title">{{ auditLabel(openLog.action) }}</h2>
        <dl class="log-facts">
          <div><dt>By</dt><dd>{{ openLog.user ? `${openLog.user.first_name} ${openLog.user.last_name}` : 'System' }}</dd></div>
          <div><dt>When</dt><dd>{{ dateTime(openLog.created_at) }}</dd></div>
          <div v-if="openLog.table_name"><dt>Record</dt><dd>{{ recordName(openLog) }}</dd></div>
          <div v-if="openLog.ip_address"><dt>IP address</dt><dd>{{ openLog.ip_address }}</dd></div>
        </dl>
        <template v-if="changes(openLog).length">
          <h3 class="log-h">What changed</h3>
          <ul class="log-changes">
            <li v-for="c in changes(openLog)" :key="c.field"><strong>{{ c.field }}</strong>: <template v-if="c.from !== undefined">from {{ c.from }} to </template>{{ c.to }}</li>
          </ul>
        </template>
        <div class="nm-modal-actions">
          <NuxtLink to="/audit-logs?scope=admin" class="nm-btn-soft">Open audit logs</NuxtLink>
          <button type="button" class="nm-btn-dark" @click="openLog = null">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { phHour } from '~/utils/phTime'
import { CircleDot, Info, RefreshCw, X } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

const { get } = useApi()
const auth = useAuthStore()

const error = ref('')
const stats = ref({ support_open: 0 })
// GET /api/admin/dashboard/ (core/admin_dashboard.py): today, attention, compare, overview.
const dash = ref(null)
const ov = computed(() => dash.value?.overview || null)
const activity = ref([])
const openLog = ref(null)

const METRIC_LABEL = { consultations: 'Consultations completed', payments: 'Payments received', commission: 'Commission', new_clients: 'New clients' }
const money = m => m.key === 'payments' || m.key === 'commission'
const pct = v => (v == null ? '—' : `${v}%`)

const todayFigures = computed(() => {
  const t = dash.value?.today || {}
  return [
    { label: 'Consultations today', value: t.today ?? 0, link: '/admin-appointments' },
    { label: 'Next 7 days', value: t.next_7_days ?? 0, link: '/admin-appointments' },
    { label: 'Waiting for the RND', value: t.requests ?? 0, link: '/admin-appointments', tone: t.requests ? 'gold' : '' },
    { label: 'Unpaid, starting within 24 hours', value: t.unpaid_soon ?? 0, link: '/admin-appointments', tone: t.unpaid_soon ? 'red' : '' },
    { label: 'Support requests waiting', value: stats.value.support_open ?? 0, link: '/admin-support', tone: stats.value.support_open ? 'gold' : '' },
    { label: 'Completed in 7 days', value: t.completed_7_days ?? 0, link: '/admin-appointments' },
    { label: 'Cancelled in 7 days', value: t.cancelled_7_days ?? 0, link: '/admin-appointments' },
    { label: 'RND applications', value: stats.value.pending_verif ?? 0, link: '/rnd-verification', tone: stats.value.pending_verif ? 'gold' : '' },
    { label: 'Refunds to send', value: stats.value.refunds_pending ?? 0, link: '/billing-commission?tab=refunds', tone: stats.value.refunds_pending ? 'gold' : '' },
  ]
})
// The admin's own jobs (the rest is information: the app or the RND acts on it).
const TODO_KEYS = ['applications', 'support', 'refunds', 'payouts_due']
const ACTIONS = { applications: 'Review', support: 'Reply', refunds: 'Send refunds', payouts_due: 'Release' }
const todoItems = computed(() => (dash.value?.attention || []).filter(a => TODO_KEYS.includes(a.key)))
const watchItems = computed(() => (dash.value?.attention || []).filter(a => !TODO_KEYS.includes(a.key)))
// critical first (the API sorts them); the admin's jobs get their action name
const attnUrgent = computed(() => (dash.value?.attention || []).some(a => a.level === 'critical'))
const attnTitles = computed(() => (dash.value?.attention || []).map(a => a.title))
const peopleText = people => people.slice(0, 4).map(p => p.name).join(', ') + (people.length > 4 ? `, and ${people.length - 4} more` : '')
const todoOpen = computed(() => todoItems.value.length)
const summaryLine = computed(() => {
  if (!dash.value) return 'Loading today…'
  const n = todoOpen.value
  return n ? `${n} thing${n === 1 ? '' : 's'} to do today.` : "You're all caught up."
})

const longToday = new Date().toLocaleDateString('en-PH', { weekday: 'long', month: 'long', day: 'numeric' })
const partOfDay = (() => {
  const h = phHour()
  return h < 12 ? 'morning' : h < 18 ? 'afternoon' : 'evening'
})()

// "Invoice INV-0099", "users #12"
function recordName(log) {
  if (log.table_name === 'invoices' && log.record_id) return `Invoice INV-${String(log.record_id).padStart(4, '0')}`
  return `${log.table_name.replace(/_/g, ' ')}${log.record_id ? ` #${log.record_id}` : ''}`
}

// "What changed" lines from an audit row's old and new values.
function changes(log) {
  const oldV = log.old_values || {}
  const newV = log.new_values || {}
  const fmt = v => (v == null || v === '' ? 'empty' : typeof v === 'object' ? JSON.stringify(v) : String(v))
  return [...new Set([...Object.keys(oldV), ...Object.keys(newV)])].map(k => ({
    field: k.replace(/_/g, ' '),
    from: k in oldV ? fmt(oldV[k]) : undefined,
    to: fmt(newV[k]),
  }))
}

/* ---------- loading, and keeping it current ---------- */
// Admins have no live connection, so the page reloads itself every minute while
// it's open and visible, and when you come back to the tab.
const REFRESH_MS = 60 * 1000
const refreshing = ref(false)
const loadedAt = ref(null)
const now = ref(Date.now())
async function load() {
  refreshing.value = true
  try {
    const [s, logs, d] = await Promise.all([
      get('/admin/platform-stats/'),
      get('/admin/audit-logs/', { query: { scope: 'admin', page_size: 6 } }), get('/admin/dashboard/'),
    ])
    stats.value = s
    dash.value = d
    activity.value = (Array.isArray(logs) ? logs : logs?.results || []).slice(0, 6)
    error.value = ''
    loadedAt.value = Date.now()
  } catch {
    error.value = 'Could not load the dashboard.'
  } finally {
    refreshing.value = false
  }
}
const DAY_MS = 24 * 60 * 60 * 1000
// "19 min ago", "15 hrs ago", "3 days ago", then the date (as on the client dashboard)
function timeAgo(iso) {
  const mins = Math.round((now.value - new Date(iso)) / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs} hr${hrs === 1 ? '' : 's'} ago`
  const days = Math.round(hrs / 24)
  if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`
  return shortDate(iso)
}
const updatedText = computed(() => {
  if (!loadedAt.value) return ''
  const mins = Math.floor((now.value - loadedAt.value) / 60000)
  return mins < 1 ? 'Updated just now' : `Updated ${mins} min ago`
})
let timer = null
let clock = null
function onKey(e) {
  if (e.key !== 'Escape') return
  if (openLog.value) openLog.value = null
}
function onVisible() {
  if (document.visibilityState === 'visible' && (!loadedAt.value || Date.now() - loadedAt.value > REFRESH_MS)) load()
}
onMounted(() => {
  load()
  timer = setInterval(() => { if (document.visibilityState === 'visible') load() }, REFRESH_MS)
  clock = setInterval(() => { now.value = Date.now() }, 15000)
  document.addEventListener('visibilitychange', onVisible)
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  clearInterval(timer)
  clearInterval(clock)
  document.removeEventListener('visibilitychange', onVisible)
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
/* one 20px gap between every section */
.admin-dash { display: flex; flex-direction: column; gap: 20px; }
.admin-dash > * { margin-top: 0; margin-bottom: 0; }
.updated { display: flex; align-items: center; gap: 10px; margin: 2px 0 0; font-size: 0.8rem; color: #cfe0d5; }
.refresh {
  display: inline-flex; align-items: center; gap: 5px; min-height: 30px; padding: 0 10px; border: none; border-radius: 8px;
  background: rgba(255, 255, 255, 0.14); color: #fff; font-family: inherit; font-size: 0.78rem; font-weight: 600; cursor: pointer;
}
.refresh:hover:not(:disabled) { background: rgba(255, 255, 255, 0.22); }
.refresh:focus-visible { outline: 2px solid #f3d27a; outline-offset: 2px; }
@media (prefers-reduced-motion: no-preference) { .spin { animation: spin 0.8s linear infinite; } }
@keyframes spin { to { transform: rotate(360deg); } }
.attn-list { list-style: none; margin: 0; padding: 0; }
.attn { display: flex; align-items: flex-start; gap: 10px; padding: 12px 0; border-top: 1px solid #d9e3dc; }
.attn:first-child { border-top: none; padding-top: 0; }
.attn-icon { flex-shrink: 0; margin-top: 2px; }
.attn.todo-item .attn-icon { color: #a37a0b; }
.attn.watch .attn-icon { color: #6a7a6a; }
.attn-h { font-size: 0.92rem; font-weight: 700; margin: 4px 0 8px; }
.attn-h + .attn-list, .attn-sub + .attn-list { margin-bottom: 18px; }
.attn-sub { font-size: 0.8rem; color: #6a7a6a; margin: -4px 0 10px; }
.attn-none { margin: 0 0 18px; font-size: 0.84rem; color: #6a7a6a; }
.attn-main { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.attn-main strong { font-size: 0.86rem; color: #1a3a1a; }
.attn-main small { font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; }
.attn-people { color: #4a5a4a !important; }
/* Today in the banner's white card */
.nm-hero.greet-only { grid-template-columns: minmax(0, 1fr); }
/* the nine figures fill the panel beside the month comparison */
.nm-grid { align-items: stretch; }
.today-panel { padding: 0; overflow: hidden; display: flex; }
.today-panel .figs { flex: 1; border-top: none; grid-auto-rows: 1fr; }
.today-panel .fig { justify-content: center; padding: 14px 16px; }
.today-panel .fig strong { font-size: 1.6rem; }

/* figures: one divided panel */
.figs { display: grid; border-top: 1px solid #d9e3dc; }
/* 3 x 3, split by lines */
.figs.nine { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.figs.nine .fig:nth-child(3n + 1) { border-left: none; }
.figs.nine .fig:nth-child(n + 4) { border-top: 1px solid #d9e3dc; }
.fig { display: flex; flex-direction: column; gap: 2px; padding: 10px 14px; text-decoration: none; color: #1a3a1a; min-width: 0; border-left: 1px solid #d9e3dc; }
.fig:first-child { border-left: none; }
.fig:hover { background: #f7faf8; }
.fig:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.fig strong { font-family: 'Playfair Display', serif; font-size: 1.3rem; line-height: 1.15; font-variant-numeric: lining-nums tabular-nums; }
.fig span { font-size: 0.74rem; color: #4a5a4a; line-height: 1.3; }
.fig.red strong { color: #a12525; }
.fig.gold strong { color: #a37a0b; }

/* overview: three divided columns */
.overview { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); padding: 0; overflow: visible; }
.ov-col { padding: 18px 20px 16px; min-width: 0; border-left: 1px solid #d9e3dc; }
.ov-col:first-child { border-left: none; }
.ov-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
.ov-figs { margin: 0 0 14px; }
.ov-figs > div { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding: 7px 0; border-top: 1px solid #edf2ee; }
.ov-figs > div:first-child { border-top: none; }
.ov-figs dt { font-size: 0.82rem; color: #4a5a4a; }
.ov-figs dd { margin: 0; font-weight: 700; font-size: 0.98rem; color: #1a3a1a; white-space: nowrap; font-variant-numeric: tabular-nums; }
.ov-figs dd small { font-weight: 500; font-size: 0.74rem; color: #6a7a6a; }
.ov-trend-label { margin: 0 0 4px; font-size: 0.76rem; color: #6a7a6a; }

/* month vs last month: up is green, a drop is plain grey (not a warning) */
.cmp { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; grid-template-areas: "label now delta" "label before before"; gap: 0 12px; align-items: center; padding: 9px 0; border-bottom: 1px solid #edf2ee; }
.cmp:last-child { border-bottom: none; }
.cmp-label { grid-area: label; font-size: 0.84rem; color: #4a5a4a; }
.cmp-now { grid-area: now; font-weight: 700; font-size: 0.95rem; text-align: right; font-variant-numeric: tabular-nums; }
.cmp-before { grid-area: before; font-size: 0.74rem; color: #6a7a6a; text-align: right; }

/* activity rows open the details pop-up */
.act-head { margin-bottom: 14px; padding-bottom: 14px; border-bottom: 1px solid #d9e3dc; }
.act-empty { margin: 0; font-size: 0.85rem; color: #6a7a6a; line-height: 1.5; }
.act-row { display: flex; align-items: flex-start; gap: 10px; width: 100%; padding: 10px 0; border: none; border-top: 1px solid #d9e3dc; background: none; text-align: left; font-family: inherit; cursor: pointer; color: inherit; }
.act-row:first-of-type { border-top: none; padding-top: 0; }
.act-row:hover .act-title { text-decoration: underline; }
.act-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; border-radius: 6px; }
.act-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; margin-top: 6px; background: #c5d0c5; }
.act-dot.fresh { background: #D4A017; }
.act-text { display: flex; flex-direction: column; min-width: 0; }
.act-title { font-size: 0.83rem; font-weight: 600; color: #1a3a1a; overflow-wrap: anywhere; }
.act-time { font-size: 0.76rem; color: #6a7a6a; margin-top: 2px; }
.log-facts { margin: 0; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; }
.log-facts > div { display: flex; justify-content: space-between; gap: 12px; padding: 9px 14px; font-size: 0.86rem; }
.log-facts > div + div { border-top: 1px solid #d9e3dc; }
.log-facts dt { color: #6a7a6a; }
.log-facts dd { margin: 0; font-weight: 600; text-align: right; overflow-wrap: anywhere; }
.log-h { font-size: 0.88rem; font-weight: 700; margin: 16px 0 6px; }
.log-changes { margin: 0; padding-left: 18px; font-size: 0.84rem; color: #4a5a4a; line-height: 1.6; overflow-wrap: anywhere; }

@media (max-width: 1100px) {
  .overview { grid-template-columns: minmax(0, 1fr); }
  .ov-col { border-left: none; border-top: 1px solid #d9e3dc; }
  .ov-col:first-child { border-top: none; }
}
@media (max-width: 560px) {
  .fig { padding: 12px 12px; }
  .fig strong { font-size: 1.3rem; }
  .attn { flex-wrap: wrap; }
  .attn .nm-panel-link { margin-left: 26px; }
}
</style>
