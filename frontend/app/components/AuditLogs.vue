<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <p class="nm-note plain-note sealed">
      <Lock :size="15" aria-hidden="true" />
      <span><strong>Nothing here can be edited or deleted.</strong> It's the record of who did what and when, which RA 10173 requires.</span>
    </p>

    <!-- one toolbar: search, event, quick dates, admin only, export -->
    <div class="nm-panel filters">
      <div class="filter-row">
        <div class="nm-search">
          <Search :size="15" aria-hidden="true" />
          <input v-model="search" type="search" placeholder="Search person, event or IP" />
        </div>
        <select v-model="action" class="nm-select" aria-label="Filter by event">
          <option value="">All events</option>
          <option v-for="a in actionOptions" :key="a.key" :value="a.key">{{ a.label }} ({{ a.count }})</option>
        </select>
        <button type="button" class="nm-btn-soft" :disabled="exporting || !count" @click="exportCsv">
          <Download :size="14" aria-hidden="true" /> {{ exporting ? 'Preparing…' : 'Export CSV' }}
        </button>
      </div>
      <div class="filter-row">
        <div class="nm-tabs quick-ranges" role="group" aria-label="Date range">
          <button v-for="r in RANGES" :key="r.label" type="button" class="nm-tab" :class="{ active: activeRange === r.label }" @click="setRange(r)">{{ r.label }}</button>
        </div>
        <label class="date-field">From <input v-model="dateFrom" type="date" class="nm-input" :max="dateTo || today" /></label>
        <label class="date-field">To <input v-model="dateTo" type="date" class="nm-input" :min="dateFrom" :max="today" /></label>
        <label class="admin-only"><input v-model="adminOnly" type="checkbox" /> Admin actions only</label>
      </div>
    </div>

    <!-- THE JOURNAL: grouped by Philippine day, newest first -->
    <div ref="listTop" class="nm-panel journal">
      <div class="journal-head">
        <span class="nm-muted">{{ loading ? 'Loading…' : `${count.toLocaleString()} event${count === 1 ? '' : 's'}` }}</span>
        <button v-if="hasFilters" type="button" class="nm-btn-soft nm-btn-sm" @click="clearFilters">Clear filters</button>
      </div>
      <p v-if="loading && !logs.length" class="nm-muted">Loading audit log…</p>
      <div v-else-if="!logs.length" class="nm-empty">
        <ScrollText :size="28" aria-hidden="true" />
        <p>{{ hasFilters ? 'No events match these filters.' : 'No events recorded yet.' }}</p>
      </div>
      <section v-for="d in days" :key="d.key" class="day">
        <h3 class="day-title"><span>{{ d.label }}</span><span class="day-count">{{ d.items.length }}</span></h3>
        <button v-for="log in d.items" :key="log.id" type="button" class="entry" :class="toneOf(log.action)" @click="selected = log">
          <span class="entry-time">{{ timeText(log.created_at) }}</span>
          <span class="entry-mark" aria-hidden="true"><component :is="iconOf(log.action)" :size="15" /></span>
          <span class="entry-main">
            <span class="entry-title">{{ auditLabel(log.action) }}</span>
            <span class="entry-who">
              {{ actorName(log) }}<template v-if="log.user">, {{ ROLE_LABELS[log.user.role] || log.user.role }}</template><template v-if="targetOf(log)">, on {{ targetOf(log) }}</template>
            </span>
            <span v-if="changeLines(log).length" class="entry-change">{{ changeLines(log).join(', ') }}</span>
          </span>
          <ChevronRight :size="16" class="entry-go" aria-hidden="true" />
        </button>
      </section>
      <ListPager :page="page" :pages="pageCount" @update:page="goTo" />
    </div>

    <!-- ONE EVENT: everything that was stored, as evidence -->
    <div v-if="selected" class="nm-modal-overlay" @click.self="selected = null">
      <div class="nm-modal event" role="dialog" aria-modal="true" aria-labelledby="event-title">
        <div class="event-head nm-modal-head">
          <span class="event-mark" :class="toneOf(selected.action)"><component :is="iconOf(selected.action)" :size="18" aria-hidden="true" /></span>
          <div style="flex: 1; min-width: 0">
            <h3 id="event-title" class="nm-modal-title">{{ auditLabel(selected.action) }}</h3>
            <p class="nm-panel-sub">{{ dateTime(selected.created_at) }}, event #{{ selected.id }}</p>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="selected = null"><X :size="18" aria-hidden="true" /></button>
        </div>

        <dl class="nm-dl facts">
          <div>
            <dt>Done by</dt>
            <dd>
              <NuxtLink v-if="selected.user" :to="`/users/${selected.user.id}`" class="nm-text-link">{{ actorName(selected) }}</NuxtLink>
              <template v-else>System (automatic)</template>
              <span v-if="selected.user" class="sub">{{ ROLE_LABELS[selected.user.role] || selected.user.role }}, {{ selected.user.email }}</span>
            </dd>
          </div>
          <div>
            <dt>Record</dt>
            <dd>
              <NuxtLink v-if="selected.table_name === 'users' && selected.record_id" :to="`/users/${selected.record_id}`" class="nm-text-link">{{ targetOf(selected) }}</NuxtLink>
              <template v-else>{{ targetOf(selected) || '—' }}</template>
            </dd>
          </div>
          <div><dt>IP address</dt><dd class="mono">{{ selected.ip_address || '—' }}</dd></div>
          <div><dt>Event code</dt><dd class="mono">{{ selected.action }}</dd></div>
          <div v-if="selected.user_agent" class="wide"><dt>Browser</dt><dd class="sub-dd">{{ selected.user_agent }}</dd></div>
        </dl>

        <h4 class="event-section">What was recorded</h4>
        <p v-if="!fieldRows(selected).length" class="nm-muted">No values were stored with this event.</p>
        <div v-else class="nm-table-wrap">
          <table class="nm-table diff">
            <thead><tr><th>Field</th><th v-if="hasBefore(selected)">Before</th><th>{{ hasBefore(selected) ? 'After' : 'Value' }}</th></tr></thead>
            <tbody>
              <tr v-for="f in fieldRows(selected)" :key="f.key">
                <td class="diff-key">{{ f.label }}</td>
                <td v-if="hasBefore(selected)" class="diff-old">{{ f.before }}</td>
                <td class="diff-new">{{ f.after }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-dark" @click="selected = null">Done</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Ban, ChevronRight, Coins, Download, Eye, FileCheck2, KeyRound, Lock, LogIn, ScrollText, Search, Settings, ShieldCheck, Wallet, X,
} from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

const { get } = useApi()

const ROLE_LABELS = { client: 'Client', rnd: 'RND', admin: 'Admin' }
const TABLE_LABELS = { users: 'Account', rnd_profiles: 'RND profile', invoices: 'Invoice', system_settings: 'Setting', payouts: 'Payout', rnd_payout_accounts: 'Payout details', appointments: 'Appointment', audit_logs: 'Audit log' }

// Filtering and paging happen on the server (core/audit.py), PAGE_SIZE a page.
const route = useRoute()
const config = useRuntimeConfig()
const auth = useAuthStore()

const loading = ref(true)
const PAGE_SIZE = 20
const page = ref(1)
const listTop = ref(null)
const exporting = ref(false)
const error = ref('')
const logs = ref([])
const count = ref(0)
const actionCounts = ref([])
const selected = ref(null)

const search = ref('')
const action = ref(typeof route.query.action === 'string' ? route.query.action : '')
const dateFrom = ref('')
const dateTo = ref('')
const adminOnly = ref(route.query.scope === 'admin')

const PH = { timeZone: 'Asia/Manila' }
const ph = d => new Date(d).toLocaleDateString('en-CA', PH) // YYYY-MM-DD
const today = ph(new Date())
const RANGES = [
  { label: 'Any time', days: null },
  { label: 'Today', days: 0 },
  { label: '7 days', days: 6 },
  { label: '30 days', days: 29 },
]
const activeRange = computed(() => {
  if (!dateFrom.value && !dateTo.value) return 'Any time'
  if (!dateFrom.value || dateTo.value !== today) return ''
  return RANGES.find(r => r.days !== null && ph(Date.now() - r.days * 86400000) === dateFrom.value)?.label || ''
})
function setRange(r) {
  if (r.days === null) {
    dateFrom.value = ''
    dateTo.value = ''
    return
  }
  dateFrom.value = ph(Date.now() - r.days * 86400000)
  dateTo.value = today
}
const hasFilters = computed(() => !!(search.value.trim() || action.value || dateFrom.value || dateTo.value || adminOnly.value))
function clearFilters() {
  search.value = ''
  action.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  adminOnly.value = false
}

function params(pageNo) {
  const q = { page: pageNo, page_size: PAGE_SIZE }
  if (search.value.trim()) q.search = search.value.trim()
  if (action.value) q.action = action.value
  if (dateFrom.value) q.date_from = dateFrom.value
  if (dateTo.value) q.date_to = dateTo.value
  if (adminOnly.value) q.scope = 'admin'
  return q
}

const pageCount = computed(() => Math.max(1, Math.ceil(count.value / PAGE_SIZE)))

let requestId = 0
async function load(pageNo = 1, { quiet = false } = {}) {
  const id = ++requestId
  if (!quiet) {
    loading.value = true
    error.value = ''
  }
  try {
    const r = await get('/admin/audit-logs/', { query: params(pageNo) })
    if (id !== requestId) return // a newer filter change won
    logs.value = r.results
    count.value = r.count
    page.value = pageNo
  } catch {
    if (id === requestId && !quiet) error.value = 'Could not load the audit log. Refresh the page to try again.'
  } finally {
    if (id === requestId) loading.value = false
  }
}
// new entries show on the page the admin is on
useAutoRefresh(() => load(page.value, { quiet: true }))

async function goTo(n) {
  if (n < 1 || n > pageCount.value || n === page.value) return
  await load(n)
  listTop.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// Any filter change starts again at page 1.
let searchTimer
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => load(1), 350)
})
watch([action, dateFrom, dateTo, adminOnly], () => load(1))

onMounted(async () => {
  load(1)
  try {
    actionCounts.value = await get('/admin/audit-logs/actions/')
  } catch {
    actionCounts.value = []
  }
})

const actionOptions = computed(() => actionCounts.value
  .map(r => ({ key: r.action, count: r.count, label: auditLabel(r.action) }))
  .sort((a, b) => a.label.localeCompare(b.label)))

// The CSV needs the sign-in token, so it's fetched and saved as a file here.
async function exportCsv() {
  exporting.value = true
  error.value = ''
  try {
    const { page: _, ...q } = params(1)
    const download = () => $fetch('/admin/audit-logs/export/', {
      baseURL: config.public.apiBase,
      query: q,
      responseType: 'blob',
      headers: { Authorization: `Bearer ${auth.accessToken}` },
    })
    let blob
    try {
      blob = await download()
    } catch (e) {
      // expired sign-in: refresh once, like useApi does
      if (e?.response?.status !== 401 || !(await auth.refreshAccessToken())) throw e
      blob = await download()
    }
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `nutrimatch-audit-log-${today}.csv`
    a.click()
    URL.revokeObjectURL(url)
    load(1) // the export itself is now in the log
  } catch {
    error.value = 'Could not export the audit log. Try again.'
  } finally {
    exporting.value = false
  }
}

/* display */
// rows come newest first from the server; neighbours that share a PH day go together
const days = computed(() => {
  const out = []
  const t = ph(Date.now())
  const y = ph(Date.now() - 86400000)
  for (const log of logs.value) {
    const key = ph(log.created_at)
    const last = out[out.length - 1]
    if (last && last.key === key) { last.items.push(log); continue }
    const long = new Date(log.created_at).toLocaleDateString('en-PH', { ...PH, weekday: 'long', month: 'long', day: 'numeric' })
    const md = new Date(log.created_at).toLocaleDateString('en-PH', { ...PH, month: 'long', day: 'numeric' })
    out.push({ key, label: key === t ? `Today, ${md}` : key === y ? `Yesterday, ${md}` : long, items: [log] })
  }
  return out
})
const timeText = v => new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
const actorName = log => (log.user ? `${log.user.first_name} ${log.user.last_name}`.trim() : 'System')

function targetOf(log) {
  if (!log.table_name) return ''
  const label = TABLE_LABELS[log.table_name] || log.table_name.replace(/_/g, ' ')
  if (!log.record_id) return label
  if (log.table_name === 'invoices') return `${label} INV-${String(log.record_id).padStart(4, '0')}`
  if (log.table_name === 'payouts') return `${label} PO-${String(log.record_id).padStart(4, '0')}`
  return `${label} #${log.record_id}`
}

const fmt = v => (v == null || v === '' ? '—' : typeof v === 'object' ? JSON.stringify(v) : String(v))
const fieldLabel = k => { const t = k.replace(/_/g, ' '); return t.charAt(0).toUpperCase() + t.slice(1) }
// a short summary on the row: the first two fields, "before to after"
function changeLines(log) {
  const oldV = log.old_values || {}
  const newV = log.new_values || {}
  const keys = [...new Set([...Object.keys(oldV), ...Object.keys(newV)])]
  return keys.slice(0, 2).map(k => (k in oldV
    ? `${fieldLabel(k).toLowerCase()} ${fmt(oldV[k])} to ${fmt(newV[k])}`
    : `${fieldLabel(k).toLowerCase()} ${fmt(newV[k])}`))
}
const hasBefore = log => !!(log.old_values && Object.keys(log.old_values).length)
function fieldRows(log) {
  const oldV = log.old_values || {}
  const newV = log.new_values || {}
  return [...new Set([...Object.keys(oldV), ...Object.keys(newV)])]
    .map(k => ({ key: k, label: fieldLabel(k), before: k in oldV ? fmt(oldV[k]) : '—', after: k in newV ? fmt(newV[k]) : '—' }))
}

function iconOf(a) {
  if (a.startsWith('payout')) return Wallet
  if (a.startsWith('invoice')) return Coins
  if (a.startsWith('rnd.')) return ShieldCheck
  if (a.startsWith('setting')) return Settings
  if (a === 'client.record_viewed' || a === 'lab_result.viewed') return Eye
  if (a.startsWith('login')) return LogIn
  if (a.includes('password')) return KeyRound
  if (a === 'user.deactivated' || a === 'user.removed') return Ban
  return FileCheck2
}
// red = something taken away or refused; gold = sensitive data read or a
// setting changed; green = money; grey-green = everything else
function toneOf(a) {
  if (['user.deactivated', 'user.removed', 'rnd.rejected', 'login.failed'].includes(a)) return 'tone-red'
  if (['client.record_viewed', 'lab_result.viewed'].includes(a) || a.startsWith('setting')) return 'tone-gold'
  if (a.startsWith('payout') || a.startsWith('invoice')) return 'tone-green'
  return 'tone-plain'
}
</script>

<style scoped>
.mono { font-variant-numeric: tabular-nums; }
.sealed { display: flex; gap: 10px; align-items: flex-start; }
.sealed svg { flex-shrink: 0; margin-top: 2px; color: #0a4a37; }

/* toolbar */
.filters { margin-bottom: 16px; display: flex; flex-direction: column; gap: 12px; }
.filter-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.filter-row .nm-search { max-width: none; flex: 1; min-width: 220px; }
.filter-row .nm-select { width: auto; min-width: 200px; }
.date-field { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: 600; color: #4a5a4a; }
.date-field .nm-input { width: auto; padding: 8px 10px; }
.admin-only { display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; color: #2a3a2a; cursor: pointer; margin-left: auto; }
.admin-only input { accent-color: #0a4a37; }

/* journal */
.journal-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding-bottom: 12px; border-bottom: 1px solid #d9e3dc; font-size: 0.82rem; }
.day-title { display: flex; align-items: baseline; gap: 8px; margin: 18px 0 4px; font-family: inherit; font-size: 0.86rem; font-weight: 700; color: #0a4a37; }
.day-count { font-size: 0.74rem; font-weight: 600; color: #8a9a8a; }
.entry {
  display: grid; grid-template-columns: 70px 30px minmax(0, 1fr) 16px; gap: 12px; align-items: start; width: 100%;
  padding: 11px 8px; margin: 0; border: 0; border-top: 1px solid #edf1ee; background: none; text-align: left;
  font-family: inherit; color: inherit; cursor: pointer;
}
.day-title + .entry { border-top-color: transparent; }
.entry:hover { background: #f7faf8; }
.entry:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.entry-time { font-size: 0.8rem; font-weight: 600; color: #4a5a4a; padding-top: 6px; font-variant-numeric: tabular-nums; white-space: nowrap; }
.entry-mark { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.entry-main { display: flex; flex-direction: column; gap: 2px; min-width: 0; padding-top: 2px; }
.entry-title { font-size: 0.87rem; font-weight: 700; color: #1a3a1a; }
.entry-who { font-size: 0.78rem; color: #6a7a6a; overflow-wrap: anywhere; }
.entry-change { font-size: 0.76rem; color: #8a9a8a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.entry-go { color: #9aaa9a; margin-top: 7px; }
.tone-plain .entry-mark, .event-mark.tone-plain { background: #eef3ef; color: #4a6a55; }
.tone-green .entry-mark, .event-mark.tone-green { background: #e3f3ea; color: #1f8f5c; }
.tone-gold .entry-mark, .event-mark.tone-gold { background: #fdf1d6; color: #b8860b; }
.tone-red .entry-mark, .event-mark.tone-red { background: #fdecec; color: #a12525; }

/* event pop-up */
.event { max-width: 600px; }
.event-head { display: flex; gap: 12px; align-items: flex-start; }
.event-head .nm-modal-x { position: static; float: none; margin: 0; }
.event-mark { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.facts .wide { grid-column: 1 / -1; }
.sub { display: block; font-size: 0.76rem; font-weight: 400; color: #8a9a8a; margin-top: 2px; overflow-wrap: anywhere; }
.sub-dd { font-size: 0.78rem !important; font-weight: 400 !important; color: #6a7a6a !important; }
.event-section { margin: 18px 0 8px; font-family: inherit; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.diff td { vertical-align: top; overflow-wrap: anywhere; font-size: 0.82rem; }
.diff-key { font-weight: 600; color: #4a5a4a; white-space: nowrap; }
.diff-old { color: #8a9a8a; text-decoration: line-through; text-decoration-color: #c9a0a0; }
.diff-new { color: #1a3a1a; font-weight: 600; }

@media (max-width: 640px) {
  .filter-row .nm-search, .filter-row .nm-select { flex: 1 1 100%; min-width: 0; }
  .filter-row .nm-btn-soft { flex: 1; }
  .quick-ranges { width: 100%; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-radius: 12px; }
  .quick-ranges .nm-tab { justify-content: center; padding: 7px 4px; }
  .date-field { flex: 1 1 100%; }
  .date-field .nm-input { flex: 1; min-width: 0; }
  .admin-only { margin-left: 0; width: 100%; }
  .entry { grid-template-columns: 30px minmax(0, 1fr); row-gap: 2px; }
  .entry-time { grid-column: 2; grid-row: 2; padding-top: 0; font-weight: 500; color: #8a9a8a; }
  .entry-mark { grid-row: 1 / span 2; grid-column: 1; }
  .entry-main { grid-column: 2; grid-row: 1; }
  .entry-go { display: none; }
  .entry-change { white-space: normal; }
  .diff-key { white-space: normal; }
}
</style>
