<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <p class="nm-note">
      <strong>Append-only by design.</strong> Audit entries are never edited or deleted — this is the accountability record
      required by RA 10173 (who did what, and when).
    </p>

    <div class="nm-panel filters">
      <div class="filter-row">
        <div class="nm-search">
          <Search :size="15" />
          <input v-model="search" type="search" placeholder="Search person, event or IP" />
        </div>
        <select v-model="action" class="nm-select" aria-label="Filter by event">
          <option value="">All events</option>
          <option v-for="a in actionOptions" :key="a.key" :value="a.key">{{ a.label }} ({{ a.count }})</option>
        </select>
      </div>
      <div class="filter-row">
        <label class="date-field">From <input v-model="dateFrom" type="date" class="nm-input" :max="dateTo || today" /></label>
        <label class="date-field">To <input v-model="dateTo" type="date" class="nm-input" :min="dateFrom" :max="today" /></label>
        <div class="quick-ranges">
          <button v-for="r in RANGES" :key="r.label" class="nm-tab" :class="{ active: activeRange === r.label }" @click="setRange(r.days)">{{ r.label }}</button>
        </div>
        <label class="admin-only"><input v-model="adminOnly" type="checkbox" /> Admin actions only</label>
      </div>
      <div class="filter-foot">
        <span class="nm-muted">{{ loading ? 'Loading…' : `${count.toLocaleString()} event${count === 1 ? '' : 's'}` }}<template v-if="hasFilters"> <button class="nm-panel-link" @click="clearFilters">Clear filters</button></template></span>
        <button class="nm-btn-outline nm-btn-sm" :disabled="exporting || !count" @click="exportCsv">
          <Download :size="14" /> {{ exporting ? 'Preparing…' : 'Export CSV' }}
        </button>
      </div>
    </div>

    <div ref="listTop" class="nm-panel">
      <p v-if="loading" class="nm-muted">Loading audit log…</p>
      <div v-else-if="!logs.length" class="nm-empty">
        <ScrollText :size="28" />
        <p>{{ hasFilters ? 'No events match these filters.' : 'No events recorded yet.' }}</p>
      </div>
      <template v-else>
        <!-- Same look as the History / Your Activity lists (Profile Settings). -->
        <div v-for="log in logs" :key="log.id" class="entry-row">
          <div class="entry-icon" :class="toneOf(log.action)"><component :is="iconOf(log.action)" :size="16" /></div>
          <div class="entry-info">
            <p class="entry-title">{{ auditLabel(log.action) }}</p>
            <p class="entry-detail">
              <template v-if="log.user">
                <NuxtLink :to="`/users/${log.user.id}`" class="who">{{ log.user.first_name }} {{ log.user.last_name }}</NuxtLink>
                ({{ ROLE_LABELS[log.user.role] || log.user.role }})
              </template>
              <template v-else>System</template>
              <template v-if="targetOf(log)"> ·
                <NuxtLink v-if="log.table_name === 'users' && log.record_id" :to="`/users/${log.record_id}`" class="who">{{ targetOf(log) }}</NuxtLink>
                <template v-else>{{ targetOf(log) }}</template>
              </template>
              <template v-if="log.ip_address"> · IP {{ log.ip_address }}</template>
            </p>
            <p v-for="line in changeLines(log)" :key="line" class="change">{{ line }}</p>
          </div>
          <span class="entry-time">{{ dateTime(log.created_at) }}</span>
        </div>

        <nav v-if="pageCount > 1" class="pager" aria-label="Audit log pages">
          <span class="nm-muted">Showing {{ ((page - 1) * PAGE_SIZE + 1).toLocaleString() }}–{{ Math.min(page * PAGE_SIZE, count).toLocaleString() }} of {{ count.toLocaleString() }} events</span>
          <div class="pager-btns">
            <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="page === 1" @click="goTo(page - 1)">Previous</button>
            <template v-for="(n, i) in pageNumbers" :key="i">
              <span v-if="n === '…'" class="pager-gap">…</span>
              <button v-else type="button" class="pager-num" :class="{ active: n === page }" :aria-current="n === page ? 'page' : undefined" @click="goTo(n)">{{ n }}</button>
            </template>
            <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="page === pageCount" @click="goTo(page + 1)">Next</button>
          </div>
        </nav>
      </template>
    </div>
  </div>
</template>

<script setup>
import { Ban, Coins, Download, Eye, FileCheck2, KeyRound, LogIn, ScrollText, Search, Settings, ShieldCheck, Wallet } from 'lucide-vue-next'
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

const search = ref('')
const action = ref(typeof route.query.action === 'string' ? route.query.action : '')
const dateFrom = ref('')
const dateTo = ref('')
const adminOnly = ref(route.query.scope === 'admin')

const ph = d => new Date(d).toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' }) // YYYY-MM-DD
const today = ph(new Date())
const RANGES = [
  { label: 'Today', days: 0 },
  { label: '7 days', days: 6 },
  { label: '30 days', days: 29 },
]
const activeRange = computed(() => {
  if (!dateFrom.value || dateTo.value !== today) return ''
  return RANGES.find(r => ph(Date.now() - r.days * 86400000) === dateFrom.value)?.label || ''
})
function setRange(days) {
  dateFrom.value = ph(Date.now() - days * 86400000)
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
// 1 … 4 5 [6] 7 8 … 20 — first, last, and two either side of the current page.
const pageNumbers = computed(() => {
  const last = pageCount.value
  const out = []
  for (let n = 1; n <= last; n++) {
    if (n === 1 || n === last || Math.abs(n - page.value) <= 2) out.push(n)
    else if (out[out.length - 1] !== '…') out.push('…')
  }
  return out
})

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
    if (id === requestId && !quiet) error.value = 'Could not load the audit log. Please refresh the page.'
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
    const { page, ...q } = params(1)
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
    error.value = 'Could not export the audit log. Please try again.'
  } finally {
    exporting.value = false
  }
}

function targetOf(log) {
  if (!log.table_name) return ''
  const label = TABLE_LABELS[log.table_name] || log.table_name.replace(/_/g, ' ')
  if (!log.record_id) return label
  return log.table_name === 'invoices' ? `${label} INV-${String(log.record_id).padStart(4, '0')}` : `${label} #${log.record_id}`
}

// Readable "field: old → new" lines from the stored values.
function changeLines(log) {
  const oldV = log.old_values || {}
  const newV = log.new_values || {}
  const keys = [...new Set([...Object.keys(oldV), ...Object.keys(newV)])]
  return keys.slice(0, 4).map((k) => {
    const label = k.replace(/_/g, ' ')
    const fmt = v => (v == null || v === '' ? '—' : typeof v === 'object' ? JSON.stringify(v) : String(v))
    return k in oldV ? `${label}: ${fmt(oldV[k])} → ${fmt(newV[k])}` : `${label}: ${fmt(newV[k])}`
  })
}

function iconOf(a) {
  if (a.startsWith('payout')) return Wallet
  if (a.startsWith('invoice')) return Coins
  if (a.startsWith('rnd.')) return ShieldCheck
  if (a.startsWith('setting')) return Settings
  if (a === 'client.record_viewed') return Eye
  if (a.startsWith('login')) return LogIn
  if (a.includes('password')) return KeyRound
  if (a === 'user.deactivated' || a === 'user.removed') return Ban
  return FileCheck2
}
// Tile colours as in the History lists: red = removals/rejections, gold =
// sensitive reads & settings, blue = accounts/records, green = money.
function toneOf(a) {
  if (['user.deactivated', 'user.removed', 'rnd.rejected', 'login.failed'].includes(a)) return 'icon-red'
  if (a === 'client.record_viewed' || a.startsWith('setting')) return 'icon-gold'
  if (a.startsWith('payout') || a.startsWith('invoice')) return 'icon-green'
  return 'icon-blue'
}
</script>

<style scoped>
.filters { margin-bottom: 16px; display: flex; flex-direction: column; gap: 12px; }
.filter-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.filter-row .nm-search { max-width: none; flex: 1; }
.date-field { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: 600; color: #4a5a4a; }
.date-field .nm-input { width: auto; padding: 8px 10px; }
.quick-ranges { display: inline-flex; gap: 4px; }
.quick-ranges .nm-tab { border: 1px solid #eceeec; }
.admin-only { display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; color: #2a3a2a; cursor: pointer; margin-left: auto; }
.admin-only input { accent-color: #163a1c; }
.filter-foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; border-top: 1px solid #f0f2f0; padding-top: 12px; }
@media (max-width: 640px) {
  .filter-row:first-child > * { flex: 1 1 100%; }
  .date-field { flex: 1; }
  .date-field .nm-input { flex: 1; min-width: 0; }
  .admin-only { margin-left: 0; }
}
/* Rows — same as the History / Your Activity lists */
.entry-row { display: flex; align-items: flex-start; gap: 14px; padding: 13px 0; border-top: 1px solid #f0f2f0; }
.entry-row:first-child { border-top: none; padding-top: 0; }
.entry-icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.icon-blue { background: #e3ecf7; color: #2a5a8a; }
.icon-gold { background: #fdf1d6; color: #b8860b; }
.icon-green { background: #e3f3ea; color: #1f8f5c; }
.icon-red { background: #fdecec; color: #a12525; }
.entry-info { flex: 1; min-width: 0; }
.entry-title { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.entry-detail { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; overflow-wrap: anywhere; }
.entry-time { font-size: 0.74rem; color: #9aaa9a; white-space: nowrap; padding-top: 2px; }
@media (max-width: 640px) {
  .entry-row { flex-wrap: wrap; }
  .entry-time { width: 100%; padding-left: 48px; }
}
/* Pages instead of "Load more" */
.pager { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 16px; padding-top: 14px; border-top: 1px solid #f0f2f0; font-size: 0.82rem; }
.pager-btns { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.pager-num { min-width: 34px; height: 34px; padding: 0 8px; border: 1px solid #d5dad5; border-radius: 8px; background: #fff; color: #1a3a1a; font: inherit; font-weight: 600; cursor: pointer; }
.pager-num:hover { border-color: #b9c4b9; }
.pager-num.active { background: #14301a; border-color: #14301a; color: #fff; }
.pager-gap { color: #9aaa9a; padding: 0 2px; }
.who { color: #1f8f5c; font-weight: 600; text-decoration: none; }
.who:hover { text-decoration: underline; }
.change { font-size: 0.76rem; color: #4a5a4a; background: #f7f9f7; border-radius: 6px; padding: 4px 8px; margin: 6px 0 0; overflow-wrap: anywhere; }
</style>
