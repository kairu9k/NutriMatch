<template>
  <div class="nm-page admin-dash">
    <p v-if="error" class="nm-error">{{ error }} <button type="button" class="nm-panel-link" @click="load()">Try again</button></p>

    <!-- BANNER: greeting + summary on the left, the most urgent thing on the right
         (same banner as the RND dashboard, nm-hero in portal.css) -->
    <section class="nm-hero">
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
      <div class="nm-upnext today-card" aria-label="At a glance">
        <div v-if="dash" class="figs nine">
          <NuxtLink v-for="t in todayFigures" :key="t.label" :to="t.link" class="fig" :class="t.tone">
            <strong>{{ t.value }}</strong><span>{{ t.label }}</span>
          </NuxtLink>
        </div>
        <p v-else class="nm-upnext-empty">Loading…</p>
      </div>
    </section>

    <!-- NEEDS ATTENTION: same strip as the client dashboard's "Pay now" row.
         Red = critical, dashed green = the admin's own to-do, grey = for information. -->
    <section v-if="dash" class="needs" aria-label="Needs attention">
      <p v-if="!dash.attention.length" class="all-clear"><CheckCircle2 :size="16" aria-hidden="true" /> All caught up. Nothing needs you right now.</p>
      <ul v-else class="needs-band">
        <li v-for="a in attnRows" :key="a.key" class="needs-row" :class="a.tone">
          <AlertTriangle v-if="a.tone === 'risk'" :size="16" class="needs-icon" aria-hidden="true" />
          <Info v-else-if="a.tone === 'watch'" :size="16" class="needs-icon info" aria-hidden="true" />
          <span class="needs-text"><strong>{{ a.title }}.</strong> {{ a.text }}</span>
          <NuxtLink :to="a.link" :class="a.tone === 'watch' ? 'nm-btn-soft nm-btn-sm' : 'nm-btn-dark nm-btn-sm'">{{ a.action }}</NuxtLink>
        </li>
      </ul>
    </section>

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
          <span class="cmp-delta" :class="m.change_pct == null ? 'flat' : m.change_pct > 0 ? 'up' : 'flat'">
            <template v-if="m.change_pct == null">{{ m.now ? 'New' : 'No change' }}</template>
            <template v-else><component :is="m.change_pct >= 0 ? TrendingUp : TrendingDown" :size="13" aria-hidden="true" /> {{ m.change_pct > 0 ? '+' : '' }}{{ m.change_pct }}%</template>
          </span>
          <span class="cmp-before">was {{ money(m) ? peso(m.before) : m.before }}</span>
        </div>
      </section>

      <!-- RND APPLICATIONS -->
      <section class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">RND applications</h2>
            <p class="nm-panel-sub">Check each PRC license before approving</p>
          </div>
          <NuxtLink to="/rnd-verification" class="nm-panel-link">View all</NuxtLink>
        </div>
        <div v-if="!pendingRnds.length" class="nm-empty"><ShieldCheck :size="26" aria-hidden="true" /><p>No applications waiting.</p></div>
        <div v-for="r in pendingRnds.slice(0, 5)" :key="r.id" class="nm-row">
          <img v-if="r.profile_photo" :src="r.profile_photo" class="nm-avatar" alt="" />
          <span v-else class="nm-avatar">{{ userInitials(r.first_name, r.last_name) }}</span>
          <div class="nm-row-main">
            <p class="nm-row-title">{{ r.first_name }} {{ r.last_name }}</p>
            <p class="nm-row-sub">{{ [r.specialization, r.prc_license_number && `PRC ${r.prc_license_number}`, `sent ${shortDate(r.submitted_at)}`].filter(Boolean).join(', ') }}</p>
          </div>
          <div class="nm-row-end">
            <span v-if="!r.email_verified_at" class="nm-pill muted">Email not confirmed</span>
            <NuxtLink :to="`/rnd-verification?open=${r.id}`" class="nm-btn-dark nm-btn-sm">Review</NuxtLink>
          </div>
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
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">Recent admin activity</h2>
            <p class="nm-panel-sub">Approvals, account changes, refunds, payouts and settings</p>
          </div>
          <NuxtLink to="/audit-logs?scope=admin" class="nm-panel-link">Audit logs</NuxtLink>
        </div>
        <div v-if="!activity.length" class="nm-empty"><p>Nothing recorded yet.</p></div>
        <button v-for="a in activity" :key="a.id" type="button" class="act-row" @click="openLog = a">
          <span class="nm-row-main">
            <span class="nm-row-title">{{ auditLabel(a.action) }}</span>
            <span class="nm-row-sub">{{ a.user ? `${a.user.first_name} ${a.user.last_name}` : 'System' }}, {{ dateTime(a.created_at) }}</span>
          </span>
          <ChevronRight :size="15" class="act-go" aria-hidden="true" />
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
import { AlertTriangle, CheckCircle2, ChevronRight, Info, RefreshCw, ShieldCheck, TrendingDown, TrendingUp, X } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

const { get } = useApi()
const auth = useAuthStore()

const error = ref('')
const stats = ref({ support_open: 0 })
const pendingRnds = ref([])
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
const attnRows = computed(() => (dash.value?.attention || []).map(a => ({
  ...a,
  title: a.title.replace(/\.$/, ''),
  text: a.people.length ? `${a.detail} ${peopleText(a.people)}.` : a.detail,
  tone: a.level === 'critical' ? 'risk' : TODO_KEYS.includes(a.key) ? 'unfinished' : 'watch',
  action: ACTIONS[a.key] || (TODO_KEYS.includes(a.key) || a.level === 'critical' ? 'Open' : 'View'),
})))
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
    const [s, rnds, logs, d] = await Promise.all([
      get('/admin/platform-stats/'), get('/admin/rnds/'),
      get('/admin/audit-logs/', { query: { scope: 'admin', page_size: 6 } }), get('/admin/dashboard/'),
    ])
    stats.value = s
    dash.value = d
    // unfinished sign-ups (email not confirmed) stay hidden: they can't be approved yet
    pendingRnds.value = rnds.filter(r => r.is_active && r.review_status === 'pending' && r.email_verified_at)
      .sort((a, b) => new Date(a.submitted_at) - new Date(b.submitted_at))
    activity.value = (Array.isArray(logs) ? logs : logs?.results || []).slice(0, 6)
    error.value = ''
    loadedAt.value = Date.now()
  } catch {
    error.value = 'Could not load the dashboard.'
  } finally {
    refreshing.value = false
  }
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
/* Today in the banner's white card */
.today-card { padding: 0; gap: 0; overflow: hidden; }
.today-card .figs { border-top: none; }

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

/* needs attention: same strip as ClientDashboard.vue's "Needs you" */
.needs { background: #fff; border: 1px solid #d9e3dc; border-radius: 14px; overflow: hidden; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.all-clear { display: flex; align-items: center; gap: 8px; margin: 0; padding: 14px 20px; font-size: 0.86rem; font-weight: 600; color: #1f6f46; }
.needs-band { list-style: none; margin: 0; padding: 0; }
.needs-row { display: flex; align-items: center; gap: 12px; padding: 12px 20px; font-size: 0.86rem; color: #3a4a3a; line-height: 1.45; }
.needs-row + .needs-row { border-top: 1px solid #eef1ee; }
.needs-row strong { color: #1a3a1a; }
.needs-text { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.needs-row.risk { background: #fdf3f2; }
.needs-row.risk strong { color: #a12525; }
.needs-icon { flex-shrink: 0; color: #c0392b; }
.needs-icon.info { color: #6a7a6a; }
.needs-row.unfinished::before { content: ''; flex-shrink: 0; align-self: stretch; width: 0; border-left: 2px dashed #3f9a6b; margin: 2px 2px 2px 7px; }
.needs-row .nm-btn-dark, .needs-row .nm-btn-soft { flex-shrink: 0; white-space: nowrap; }
/* one opening moment: the strip drops in, red and dashed rows glow three times */
@media (prefers-reduced-motion: no-preference) {
  .needs { animation: nm-drop 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
  .needs-row.risk { animation: nm-risk 1s ease-in-out 0.45s 3; }
  .needs-row.risk .needs-icon { animation: nm-shake 0.5s ease-in-out 0.6s 2; }
  .needs-row.unfinished { animation: nm-todo 1s ease-in-out 0.45s 3; }
}
@keyframes nm-drop { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: none; } }
@keyframes nm-risk { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(192, 57, 43, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(192, 57, 43, 0.45), inset 0 0 18px rgba(192, 57, 43, 0.22); } }
@keyframes nm-todo { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(63, 154, 107, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(63, 154, 107, 0.45), inset 0 0 18px rgba(63, 154, 107, 0.2); } }
@keyframes nm-shake { 0%, 100% { transform: none; } 25% { transform: rotate(-12deg); } 75% { transform: rotate(12deg); } }

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
.cmp-delta { grid-area: delta; display: inline-flex; align-items: center; gap: 3px; font-size: 0.74rem; font-weight: 700; border-radius: 10px; padding: 2px 8px; justify-self: end; }
.cmp-delta.up { background: #e3efe7; color: #0a4a37; }
.cmp-delta.flat { background: #eef1ee; color: #4a5a4a; }
.cmp-before { grid-area: before; font-size: 0.74rem; color: #6a7a6a; text-align: right; }

/* activity rows open the details pop-up */
.act-row { display: flex; align-items: center; gap: 10px; width: 100%; padding: 10px 0; border: none; border-top: 1px solid #edf2ee; background: none; text-align: left; font-family: inherit; cursor: pointer; color: inherit; }
.act-row:first-of-type { border-top: none; }
.act-row:hover .nm-row-title { color: #0a4a37; text-decoration: underline; }
.act-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; border-radius: 6px; }
.act-row .nm-row-main { display: flex; flex-direction: column; }
.act-go { color: #6a7a6a; flex-shrink: 0; }
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
  .needs-row { flex-wrap: wrap; padding: 12px 16px; }
  .needs-text { flex-basis: calc(100% - 40px); }
  .needs-row .nm-btn-dark, .needs-row .nm-btn-soft { margin-left: 28px; }
  .needs-row.unfinished .nm-btn-dark { margin-left: 21px; }
}
</style>
