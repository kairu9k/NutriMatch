<template>
  <div class="nm-page admin-dash">
    <p v-if="error" class="nm-error">{{ error }} <button type="button" class="nm-panel-link" @click="load()">Try again</button></p>

    <!-- BANNER: greeting and summary on the left, the platform's day on the right
         (nm-hero in portal.css; AdminDayTimeline.vue) -->
    <section class="nm-hero admin-hero">
      <img class="ah-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="ah-fade" aria-hidden="true"></span>
      <div class="nm-hero-greet">
        <p class="nm-hero-date"><span class="ah-line" aria-hidden="true"></span><span class="d-only">{{ longToday }}</span><span class="m-only-i">Admin dashboard</span></p>
        <h1 class="nm-hero-title">Good {{ partOfDay }}, {{ auth.user?.first_name }}</h1>
        <div class="ah-meta">
          <p class="nm-hero-sub">{{ summaryLine }}</p>
          <p class="updated">{{ updatedText }}</p>
        </div>
      </div>
      <div v-if="dash?.schedule" class="ah-sched">
        <p class="ah-sk"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg> Today's schedule</p>
        <AdminDayTimeline :rows="dash.schedule.today" :next="dash.schedule.next" :now="now" />
      </div>
    </section>

    <!-- NEEDS ATTENTION: the shared strip; its pop-up lists the admin's own to-do,
         then what to keep an eye on (the app or the RND handles those) -->
    <NeedsAttention v-if="dash" :groups="attnGroups" />

    <!-- QUICK ACCESS (phones only, like the client dashboard) -->
    <section class="qa" aria-label="Quick access">
      <h2 class="m-h">Quick access</h2>
      <div class="qa-grid">
          <NuxtLink to="/rnd-verification" class="qa-it"><span class="qa-ico gold"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2l2.4 3.2 4-.6.6 4L22 11l-3 2.6.6 4-4-.6L12 20l-2.4-3.2-4 .6-.6-4L2 11l3-2.4-.6-4 4 .6z" /><path d="M9 11l2 2 4-4" /></svg></span><small>Applications</small></NuxtLink>
          <NuxtLink to="/billing-commission?tab=refunds" class="qa-it"><span class="qa-ico gold"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg></span><small>Refunds</small></NuxtLink>
          <NuxtLink to="/users?tab=clients" class="qa-it"><span class="qa-ico "><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z" /></svg></span><small>Clients</small></NuxtLink>
          <NuxtLink to="/users?tab=rnds" class="qa-it"><span class="qa-ico "><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3v6a5 5 0 0 0 10 0V3" /><path d="M10 14v2a5 5 0 0 0 10 0v-2" /><path d="M18 12a2 2 0 1 0 4 0a2 2 0 1 0-4 0" /></svg></span><small>RNDs</small></NuxtLink>
          <NuxtLink to="/admin-appointments" class="qa-it"><span class="qa-ico "><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" /><path d="M16 3v4M8 3v4M3 10h18" /></svg></span><small>Appointments</small></NuxtLink>
          <NuxtLink to="/admin-support" class="qa-it"><span class="qa-ico "><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 18v-6a9 9 0 0 1 18 0v6" /><path d="M21 19a2 2 0 0 1-2 2h-1v-6h3zM3 19a2 2 0 0 0 2 2h1v-6H3z" /></svg></span><small>Support</small></NuxtLink>
          <NuxtLink to="/billing-commission" class="qa-it"><span class="qa-ico gold"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" /><path d="M2 10h20" /></svg></span><small>Payments</small></NuxtLink>
          <NuxtLink to="/platform-reports" class="qa-it"><span class="qa-ico dark"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18" /><path d="M7 15l4-4 3 3 5-6" /></svg></span><small>Reports</small></NuxtLink>
      </div>
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
        <div class="cmp-key" aria-hidden="true"><i class="now"></i>This month<i class="before"></i>Last month</div>
        <div v-for="m in dash.compare.metrics" :key="m.key" class="cmp">
          <span class="cmp-ico" aria-hidden="true"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path v-for="(d, i) in METRIC_ICON[m.key] || []" :key="i" :d="d" /></svg></span>
          <span class="cmp-label">{{ METRIC_LABEL[m.key] }}<span class="cmp-bars" aria-hidden="true"><i class="now" :style="{ width: barPct(m, 'now') }"></i><i class="before" :style="{ width: barPct(m, 'before') }"></i></span></span>
          <span class="cmp-now">{{ money(m) ? peso(m.now) : m.now }}</span>
          <ChangeBadge class="cmp-badge" :now="m.now" :before="m.before" :pct="m.change_pct" />
          <span class="cmp-chg" :class="deltaTone(m)">{{ deltaTone(m) === 'same' ? 'No change' : `${deltaTone(m) === 'up' ? '+' : '−'}${money(m) ? peso(Math.abs(m.now - m.before)) : Math.abs(m.now - m.before)}` }}</span>
          <span class="cmp-before">was {{ money(m) ? peso(m.before) : m.before }}</span>
        </div>
      </section>

      <!-- AT A GLANCE: nine figures, 3 x 3, each a link -->
      <section class="nm-panel today-panel" aria-label="At a glance">
        <h2 class="m-h m-only">At a glance</h2>
        <div v-for="g in figGroups" :key="g.title" class="fig-group">
          <p class="fig-k" :class="{ hot: g.hot }">{{ g.title }}</p>
          <div class="figs nine">
            <NuxtLink v-for="t in g.items" :key="t.label" :to="t.link" class="fig" :class="[t.tone, figTone(t)]">
              <span class="fig-ico" aria-hidden="true"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path v-for="(d, i) in FIG_ICON[t.label] || []" :key="i" :d="d" /></svg></span>
              <strong>{{ t.value }}</strong><span>{{ t.label }}</span>
            </NuxtLink>
          </div>
        </div>
      </section>
    </div>

    <!-- OVERVIEW: clients, RNDs, platform. Three divided columns. -->
    <h2 v-if="ov" class="m-h m-only">Overview</h2>
    <section v-if="ov" class="nm-panel overview" aria-label="Overview">
      <div class="ov-col">
        <div class="ov-head"><span class="ov-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z" /></svg></span><h2 class="nm-panel-title">Clients</h2><NuxtLink to="/users?tab=clients" class="nm-panel-link">All clients <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink></div>
        <p class="ov-big"><strong>{{ ov.clients.new_this_month }}</strong><small>new clients this month</small></p>
        <dl class="ov-figs">
          <div><dt>In active care</dt><dd>{{ ov.clients.in_care }}</dd></div>
          <div><dt>New this month</dt><dd>{{ ov.clients.new_this_month }}</dd></div>
          <div><dt>Finished onboarding</dt><dd>{{ pct(ov.clients.onboarded_pct) }}</dd></div>
        </dl>
        <div class="ov-sp">
          <p class="ov-trend-label">New clients per month</p>
          <Sparkline :points="ov.clients.trend" label="New clients per month" />
        </div>
      </div>
      <div class="ov-col">
        <div class="ov-head"><span class="ov-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3v6a5 5 0 0 0 10 0V3" /><path d="M10 14v2a5 5 0 0 0 10 0v-2" /><circle cx="20" cy="12" r="2" /></svg></span><h2 class="nm-panel-title">RNDs</h2><NuxtLink to="/users?tab=rnds" class="nm-panel-link">All RNDs <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink></div>
        <p class="ov-big"><strong>{{ ov.rnds.bookable }}</strong><small>approved RNDs clients can book</small></p>
        <dl class="ov-figs">
          <div><dt>Consulted in 30 days</dt><dd>{{ ov.rnds.active_30_days }} <small>of {{ ov.rnds.approved }} approved</small></dd></div>
          <div><dt>Clients can book</dt><dd>{{ ov.rnds.bookable }}</dd></div>
          <div><dt>Calendar booked, next 7 days</dt><dd>{{ pct(ov.rnds.calendar_filled_pct) }}</dd></div>
        </dl>
        <div class="ov-sp">
          <p class="ov-trend-label">RNDs who consulted, per month</p>
          <Sparkline :points="ov.rnds.trend" label="RNDs who consulted, per month" />
        </div>
      </div>
      <div class="ov-col">
        <div class="ov-head"><span class="ov-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18" /><path d="M7 15l4-4 3 3 5-6" /></svg></span><h2 class="nm-panel-title">Platform</h2><NuxtLink to="/platform-reports" class="nm-panel-link">Reports <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink></div>
        <p class="ov-big"><strong>{{ peso(ov.platform.payments_this_month) }}</strong><small>payments this month</small></p>
        <dl class="ov-figs">
          <div><dt>Consultations this month</dt><dd>{{ ov.platform.consultations_this_month }}</dd></div>
          <div><dt>Payments this month</dt><dd>{{ peso(ov.platform.payments_this_month) }}</dd></div>
          <div><dt>Cancelled, last 30 days</dt><dd>{{ pct(ov.platform.cancelled_pct_30_days) }}</dd></div>
        </dl>
        <div class="ov-sp">
          <p class="ov-trend-label">Payments per month</p>
          <Sparkline :points="ov.platform.trend" label="Payments per month" :format="v => peso(v)" />
        </div>
      </div>
    </section>

    <div v-if="dash">
      <!-- RECENT ADMIN ACTIVITY: click a row for the details -->
      <section class="nm-panel">
        <div class="nm-panel-head act-head">
          <h2 class="nm-panel-title"><span class="ov-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l3 2" /></svg></span>Recent admin activity</h2>
          <NuxtLink to="/audit-logs?scope=admin" class="nm-btn-soft nm-btn-sm">View all <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
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
import { X } from 'lucide-vue-next'
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
// the pop-up's two sections (NeedsAttention.vue draws them)
const attnItem = (a, tone, action) => ({
  key: a.key, title: a.title, detail: a.detail, extra: a.people.length ? peopleText(a.people) : '', to: a.link, action, tone,
  critical: a.level === 'critical',
})
const attnGroups = computed(() => [
  { title: 'Your to-do', empty: 'Nothing to do right now.', always: true,
    items: todoItems.value.map(a => attnItem(a, 'todo', ACTIONS[a.key] || 'Open')) },
  { title: 'Keep an eye on', sub: 'For your information. The app or the RND handles these.', empty: 'Nothing to watch right now.', always: true,
    items: watchItems.value.map(a => attnItem(a, 'info', 'View')) },
])
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
const loadedAt = ref(null)
const now = ref(Date.now())
async function load() {
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// small line icons (SVG path data) for the month rows and the nine figures
const METRIC_ICON = {
  consultations: ['M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0', 'M8.5 12.5l2.5 2.5 4.5-5'],
  payments: ['M7 21V3h6a5 5 0 0 1 0 10H7', 'M4 7h16M4 10h16'],
  commission: ['M19 5L5 19', 'M4.0 6.5a2.5 2.5 0 1 0 5.0 0a2.5 2.5 0 1 0 -5.0 0', 'M15.0 17.5a2.5 2.5 0 1 0 5.0 0a2.5 2.5 0 1 0 -5.0 0'],
  new_clients: ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M5 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0', 'M19 8v6M22 11h-6'],
}
const FIG_ICON = {
  'Consultations today': ['M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z', 'M16 3v4M8 3v4M3 10h18'],
  'Next 7 days': ['M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0', 'M12 7v5l3 2'],
  'Waiting for the RND': ['M6 2h12M6 22h12M7 2v4l5 6-5 6v4M17 2v4l-5 6 5 6v4'],
  'Unpaid, starting within 24 hours': ['M4 5h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z', 'M2 10h20'],
  'Support requests waiting': ['M3 18v-6a9 9 0 0 1 18 0v6', 'M21 19a2 2 0 0 1-2 2h-1v-6h3zM3 19a2 2 0 0 0 2 2h1v-6H3z'],
  'Completed in 7 days': ['M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0', 'M8.5 12.5l2.5 2.5 4.5-5'],
  'Cancelled in 7 days': ['M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0', 'M15 9l-6 6M9 9l6 6'],
  'RND applications': ['M12 2l2.4 3.2 4-.6.6 4L22 11l-3 2.6.6 4-4-.6L12 20l-2.4-3.2-4 .6-.6-4L2 11l3-2.4-.6-4 4 .6z', 'M9 11l2 2 4-4'],
  'Refunds to send': ['M3 12a9 9 0 1 0 3-6.7L3 8', 'M3 3v5h5'],
}
// the same nine figures, in three labelled rows: what needs the admin first
const FIG_ROWS = [
  { title: 'Needs you', hot: true, labels: ['Cancelled in 7 days', 'RND applications', 'Refunds to send'] },
  { title: 'Consultations', labels: ['Consultations today', 'Next 7 days', 'Waiting for the RND'] },
  { title: 'Keep an eye on', labels: ['Unpaid, starting within 24 hours', 'Support requests waiting', 'Completed in 7 days'] },
]
const figGroups = computed(() => FIG_ROWS.map(g => ({ ...g, items: g.labels.map(l => todayFigures.value.find(t => t.label === l)).filter(Boolean) })))
// month row: up, down or the same as last month
const deltaTone = m => { const d = (Number(m.now) || 0) - (Number(m.before) || 0); return d > 0 ? 'up' : d < 0 ? 'down' : 'same' }
// cancellations show red on the dashboard design
const figTone = t => (t.label === 'Cancelled in 7 days' && t.value && !t.tone ? 'red' : '')
// width of a month bar: this month and last month against the bigger of the two
function barPct(m, side) {
  const a = Number(m.now) || 0
  const b = Number(m.before) || 0
  const top = Math.max(a, b)
  return top ? `${Math.round(((side === 'now' ? a : b) / top) * 100)}%` : '0%'
}
</script>
<style scoped>
.admin-dash { font-family: 'DM Sans', sans-serif; color: #22362c; --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); display: flex; flex-direction: column; gap: 20px; }
.admin-dash > * { margin-top: 0; margin-bottom: 0; }
.ic { flex-shrink: 0; display: inline-block; }
.qa, .m-only, .m-only-i { display: none; }

/* ---------- hero ---------- */
.nm-hero.admin-hero {
  position: relative; overflow: hidden; grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.2fr); gap: 36px; align-items: center; padding: 28px 30px; border-radius: 24px;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.admin-hero > *:not(.ah-plate):not(.ah-fade) { position: relative; z-index: 1; }
.ah-plate { position: absolute; right: -90px; top: 50%; width: 340px; height: 340px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.ah-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 55%, rgba(0, 77, 58, 0.9) 75%, rgba(0, 77, 58, 0.72) 100%); }
.admin-hero .nm-hero-date { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.ah-line { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.admin-hero .nm-hero-title { margin: 0 0 10px; font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.ah-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 10px; }
.admin-hero .nm-hero-sub { margin: 0; padding: 4px 11px; border-radius: 999px; background: #efbf04; color: #004d3a; font-size: 12.5px; font-weight: 800; }
.updated { display: flex; align-items: center; gap: 10px; margin: 0; font-size: 14px; color: rgba(255, 255, 255, 0.8); }
.updated:not(:empty)::before { content: ''; width: 4px; height: 4px; border-radius: 50%; background: rgba(255, 255, 255, 0.5); }
/* today's schedule: a glass card on the right */
.ah-sched { min-width: 0; padding: 18px 20px; border-radius: 18px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.14); backdrop-filter: blur(6px); }
.ah-sk { display: flex; align-items: center; gap: 8px; margin: 0 0 12px; font-size: 13px; font-weight: 700; color: #fff; }
.ah-sk .ic { color: #efbf04; }
@media (max-width: 900px) { .nm-hero.admin-hero { grid-template-columns: minmax(0, 1fr); gap: 22px; } }

/* ---------- month vs last month ---------- */
.nm-grid { align-items: stretch; }
.nm-grid > .nm-panel { border: none; border-radius: 24px; box-shadow: var(--sh); }
.nm-grid > .nm-panel:first-child { display: flex; flex-direction: column; padding: 24px 26px 12px; }
.nm-grid .nm-panel-title { margin: 0 0 4px; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.nm-grid .nm-panel-sub { margin: 0; font-size: 13px; color: #6b7d73; }
.cmp-key { display: flex; align-items: center; gap: 6px; margin: 10px 0 4px; font-size: 12px; color: #6b7d73; }
.cmp-key i { width: 10px; height: 10px; border-radius: 3px; }
.cmp-key i + i, .cmp-key i:nth-of-type(2) { margin-left: 8px; }
.cmp-key i.now, .cmp-bars i.now { background: #1f9d55; }
.cmp-key i.before, .cmp-bars i.before { background: #c9d8cf; }
.cmp {
  flex: 1; display: grid; grid-template-columns: 36px minmax(0, 1fr) auto 124px; grid-template-areas: "ico label now chg" "ico label before chg";
  gap: 0 14px; align-items: center; padding: 14px 0; border-bottom: 1px solid #f0f3f1;
}
.cmp:last-child { border-bottom: none; }
.cmp-ico { grid-area: ico; width: 36px; height: 36px; border-radius: 11px; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.cmp-label { grid-area: label; display: flex; flex-direction: column; gap: 7px; min-width: 0; font-size: 14.5px; color: #22362c; }
.cmp-bars { display: flex; flex-direction: column; gap: 3px; max-width: 220px; padding: 2px 0; }
.cmp-bars i { display: block; min-width: 0; height: 5px; border-radius: 999px; }
.cmp-bars i[style*='width: 0%'] { width: 100% !important; background: #eef2ef; }
.cmp-now { grid-area: now; font-size: 17px; font-weight: 800; color: #0e3a2c; text-align: right; font-variant-numeric: tabular-nums; }
.cmp-badge { display: none !important; }
.cmp-chg { grid-area: chg; justify-self: end; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 800; white-space: nowrap; }
.cmp-chg.up { background: #e3f4ea; color: #1f7a4d; }
.cmp-chg.down { background: #f3f6f4; color: #4a5a52; }
.cmp-chg.same { background: #f3f6f4; color: #8a9a91; font-weight: 600; }
.cmp-before { grid-area: before; font-size: 12px; color: #8a9a91; text-align: right; }

/* ---------- at a glance: nine figures in three labelled rows ---------- */
.today-panel { display: flex; flex-direction: column; gap: 14px; padding: 20px; overflow: visible; }
.fig-k { display: flex; align-items: center; gap: 8px; margin: 0 0 8px; font-size: 12px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #8a9a91; }
.fig-k.hot { color: #8a6500; }
.fig-k.hot::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: #efbf04; box-shadow: 0 0 0 3px #fff4d6; }
.figs.nine { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; border: none; }
.fig {
  display: flex; flex-direction: column; align-items: flex-start; gap: 2px; min-width: 0; padding: 14px; border: 1.5px solid #c9d8cf !important; border-radius: 16px;
  background: #fff; color: #0e3a2c; text-decoration: none; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04); transition: transform 0.15s, box-shadow 0.15s;
}
.fig:hover { background: #fff; transform: translateY(-1px); box-shadow: 0 12px 22px -16px rgba(0, 77, 58, 0.5); }
.fig:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.fig-ico { width: 30px; height: 30px; margin-bottom: 6px; border-radius: 9px; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.fig strong { font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 700; line-height: 1.1; color: #0e3a2c; font-variant-numeric: lining-nums tabular-nums; }
.fig > span:last-child { font-size: 12.5px; line-height: 1.35; color: #6b7d73; }
.fig.gold { background: #fff8e1; border-color: #e7c65a !important; }
.fig.gold .fig-ico { background: #efbf04; color: #004d3a; }
.fig.gold strong { color: #8a6500; }
.fig.red { background: #fef3f2; border-color: #eba79f !important; }
.fig.red .fig-ico { background: #fde4e1; color: #b42318; }
.fig.red strong { color: #b42318; }

/* ---------- overview: three cards ---------- */
.overview { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; padding: 0; border: none; background: none; box-shadow: none; overflow: visible; }
.ov-col { display: flex; flex-direction: column; min-width: 0; padding: 0 24px 20px; border: none !important; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: hidden; }
.ov-head { display: flex; align-items: center; gap: 10px; margin: 0 -24px 14px; padding: 16px 24px; background: #f1f8f4; border-bottom: 1px solid #e3efe7; }
.ov-ico { flex-shrink: 0; width: 34px; height: 34px; border-radius: 11px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.ov-head .nm-panel-title { flex: 1; margin: 0; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.ov-head .nm-panel-link { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; border: 1px solid #dce8e0; border-radius: 10px; background: #fff; color: #004d3a; font-size: 12.5px; font-weight: 800; text-decoration: none; white-space: nowrap; }
.ov-head .nm-panel-link:hover { background: #f1f6f2; }
.ov-big { display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px; margin: 0; }
.ov-big strong { font-family: 'Playfair Display', serif; font-size: 34px; font-weight: 700; line-height: 1.1; color: #004d3a; font-variant-numeric: lining-nums; }
.ov-big small { font-size: 13px; color: #6b7d73; }
.ov-sp { order: 0; margin: 12px 0 8px; padding: 12px 14px 10px; border-radius: 14px; background: #f7faf8; }
.ov-trend-label { margin: 0 0 6px; font-size: 12.5px; font-weight: 600; color: #4a5a52; }
.ov-figs { order: 1; margin: 0; }
.ov-figs > div { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; padding: 11px 0; border-top: 1px solid #f0f3f1; }
.ov-figs dt { font-size: 14px; color: #22362c; }
.ov-figs dd { margin: 0; font-size: 15px; font-weight: 800; color: #0e3a2c; white-space: nowrap; font-variant-numeric: tabular-nums; }
.ov-figs dd small { font-size: 12.5px; font-weight: 500; color: #8a9a91; }
.ov-col > .ov-sp { order: 1; }
.ov-col > .ov-figs { order: 2; }

/* ---------- recent admin activity ---------- */
.admin-dash > div > .nm-panel { padding: 22px 24px; border: none; border-radius: 24px; box-shadow: var(--sh); }
.act-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; padding-bottom: 14px; border-bottom: 1px solid #f0f3f1; }
.act-head .nm-panel-title { display: flex; align-items: center; gap: 10px; margin: 0; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.act-head .nm-btn-soft { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; border-radius: 10px; font-weight: 800; }
.act-empty { margin: 0; padding: 18px; border-radius: 14px; background: #f7faf8; font-size: 13.5px; line-height: 1.5; color: #6b7d73; }
.act-row { display: flex; align-items: center; gap: 12px; width: 100%; padding: 12px 8px; border: none; border-top: 1px solid #f0f3f1; border-radius: 0; background: none; text-align: left; font-family: inherit; color: inherit; cursor: pointer; transition: background 0.15s; }
.act-row:first-of-type { border-top: none; }
.act-row:hover { background: #fafcfb; }
.act-row:hover .act-title { color: #1f7a4d; }
.act-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; border-radius: 10px; }
.act-dot { flex-shrink: 0; width: 8px; height: 8px; margin: 0 4px; border-radius: 50%; background: #c9d3cd; box-shadow: 0 0 0 3px #f1f4f2; }
.act-dot.fresh { background: #efbf04; box-shadow: 0 0 0 3px #fff4d6; }
.act-text { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.act-title { font-size: 14px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.act-time { margin: 0; font-size: 12.5px; color: #6b7d73; }

/* activity pop-up */
.log-facts { margin: 0; border: 1px solid #e3ebe6; border-radius: 14px; overflow: hidden; }
.log-facts > div { display: flex; justify-content: space-between; gap: 12px; padding: 10px 14px; font-size: 13.5px; }
.log-facts > div + div { border-top: 1px solid #eef2ef; }
.log-facts dt { color: #6b7d73; }
.log-facts dd { margin: 0; font-weight: 700; color: #0e3a2c; text-align: right; overflow-wrap: anywhere; }
.log-h { margin: 16px 0 6px; font-size: 14px; font-weight: 800; color: #0e3a2c; }
.log-changes { margin: 0; padding: 10px 14px 10px 30px; border-radius: 12px; background: #f7faf8; font-size: 13.5px; line-height: 1.6; color: #4a5a52; overflow-wrap: anywhere; }

/* ---------- tablets ---------- */
@media (max-width: 1100px) {
  .overview { grid-template-columns: minmax(0, 1fr); }
}

/* ---------- phones: same style as the client dashboard ---------- */
@media (max-width: 760px) {
  .admin-dash { gap: 14px; padding-bottom: 110px; }
  .d-only { display: none; }
  .m-only { display: block; }
  .m-only-i { display: inline; }
  .m-h { margin: 8px 2px 0; font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; color: #10231b; }
  .nm-hero.admin-hero { padding: 22px 20px 20px; }
  .ah-plate { width: 190px; height: 190px; right: -50px; top: -30px; transform: none; }
  .ah-fade { background: linear-gradient(90deg, #004d3a 0%, #004d3a 42%, rgba(0, 77, 58, 0.55) 72%, rgba(0, 77, 58, 0.1) 100%); }
  .nm-hero-greet { max-width: 66%; }
  .admin-hero .nm-hero-date { font-size: 10.5px; letter-spacing: 1.8px; }
  .ah-line { display: none; }
  .admin-hero .nm-hero-title { font-size: 26px; }
  .updated { font-size: 12.5px; }
  .updated:not(:empty)::before { display: none; }
  .qa { display: block; }
  .qa .m-h { margin-bottom: 12px; }
  .qa-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px 8px; }
  .qa-it { display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center; text-decoration: none; }
  .qa-ico { width: 52px; height: 52px; border-radius: 16px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 6px 14px -10px rgba(0, 77, 58, 0.6); }
  .qa-ico.gold { background: #fff4d6; color: #8a6500; }
  .qa-ico.dark { background: #004d3a; color: #efbf04; }
  .qa-it small { font-size: 12px; font-weight: 600; line-height: 1.25; color: #22362c; }
  .nm-grid > .nm-panel { border-radius: 20px; }
  .nm-grid > .nm-panel:first-child { padding: 18px 16px 6px; }
  .cmp { grid-template-columns: 36px minmax(0, 1fr) auto; grid-template-areas: "ico label now" "ico label before" "ico chg chg"; }
  .cmp-chg { justify-self: start; margin-top: 6px; }
  .ah-sched { padding: 12px 14px; border-radius: 16px; background: rgba(0, 40, 30, 0.5); }
  .cmp-bars { max-width: none; }
  .today-panel { padding: 0; gap: 12px; background: none; box-shadow: none !important; }
  .today-panel .m-h { margin-bottom: 0; }
  .fig-k { margin: 0 2px 8px; }
  .figs.nine { gap: 8px; }
  .fig { padding: 12px 10px; border-radius: 16px; box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.08); }
  .fig-ico { width: 26px; height: 26px; margin-bottom: 4px; }
  .fig strong { font-size: 24px; }
  .fig > span:last-child { font-size: 11.5px; }
  .overview { gap: 14px; }
  .ov-col { padding: 0 16px 16px; border-radius: 20px; }
  .ov-head { margin: 0 -16px 12px; padding: 14px 16px; }
  .admin-dash > div > .nm-panel { padding: 18px 16px; border-radius: 20px; }
}
</style>