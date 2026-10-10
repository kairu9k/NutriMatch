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
        <span class="nm-muted">{{ loading ? 'Loading…' : `${count.toLocaleString()} event${count === 1 ? '' : 's'}` }}<template v-if="hasFilters"> · <button class="nm-panel-link" @click="clearFilters">Clear filters</button></template></span>
        <button class="nm-btn-outline nm-btn-sm" :disabled="exporting || !count" @click="exportCsv">
          <Download :size="14" /> {{ exporting ? 'Preparing…' : 'Export CSV' }}
        </button>
      </div>
    </div>

    <div class="nm-panel">
      <p v-if="loading" class="nm-muted">Loading audit log…</p>
      <div v-else-if="!logs.length" class="nm-empty">
        <ScrollText :size="28" />
        <p>{{ hasFilters ? 'No events match these filters.' : 'No events recorded yet.' }}</p>
      </div>
      <template v-else>
        <div v-for="log in logs" :key="log.id" class="log-row">
          <div class="log-icon" :class="toneOf(log.action)"><component :is="iconOf(log.action)" :size="15" /></div>
          <div class="nm-row-main">
            <p class="nm-row-title">{{ auditLabel(log.action) }}</p>
            <p class="nm-row-sub">
              <template v-if="log.user">
                <NuxtLink :to="`/users/${log.user.id}`" class="who">{{ log.user.first_name }} {{ log.user.last_name }}</NuxtLink>
                <span class="nm-muted"> ({{ ROLE_LABELS[log.user.role] || log.user.role }})</span>
              </template>
              <template v-else>System</template>
              · {{ dateTime(log.created_at) }}<template v-if="log.ip_address"> · IP {{ log.ip_address }}</template>
            </p>
            <p v-if="targetOf(log)" class="nm-row-sub">
              <NuxtLink v-if="log.table_name === 'users' && log.record_id" :to="`/users/${log.record_id}`" class="who">{{ targetOf(log) }}</NuxtLink>
              <template v-else>{{ targetOf(log) }}</template>
            </p>
            <p v-for="line in changeLines(log)" :key="line" class="change">{{ line }}</p>
          </div>
        </div>
        <div v-if="nextPage" style="text-align: center; margin-top: 14px">
          <button class="nm-btn-outline" :disabled="loadingMore" @click="loadMore">
            {{ loadingMore ? 'Loading…' : `Load more (${(count - logs.length).toLocaleString()} left)` }}
          </button>
        </div>
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

// Filtering and paging happen on the server (core/audit.py), 50 at a time.
const route = useRoute()
const config = useRuntimeConfig()
const auth = useAuthStore()

const loading = ref(true)
const loadingMore = ref(false)
const exporting = ref(false)
const error = ref('')
const logs = ref([])
const count = ref(0)
const nextPage = ref(null)
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

function params(page) {
  const q = { page }
  if (search.value.trim()) q.search = search.value.trim()
  if (action.value) q.action = action.value
  if (dateFrom.value) q.date_from = dateFrom.value
  if (dateTo.value) q.date_to = dateTo.value
  if (adminOnly.value) q.scope = 'admin'
  return q
}

let requestId = 0
async function load() {
  const id = ++requestId
  loading.value = true
  error.value = ''
  try {
    const r = await get('/admin/audit-logs/', { query: params(1) })
    if (id !== requestId) return // a newer filter change won
    logs.value = r.results
    count.value = r.count
    nextPage.value = r.next ? 2 : null
  } catch {
    if (id === requestId) error.value = 'Could not load the audit log. Please refresh the page.'
  } finally {
    if (id === requestId) loading.value = false
  }
}

async function loadMore() {
  loadingMore.value = true
  try {
    const r = await get('/admin/audit-logs/', { query: params(nextPage.value) })
    logs.value.push(...r.results)
    nextPage.value = r.next ? nextPage.value + 1 : null
  } catch {
    error.value = 'Could not load more events. Please try again.'
  } finally {
    loadingMore.value = false
  }
}

let searchTimer
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 350)
})
watch([action, dateFrom, dateTo, adminOnly], load)

onMounted(async () => {
  load()
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
    load() // the export itself is now in the log
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
function toneOf(a) {
  if (['user.deactivated', 'user.removed', 'rnd.rejected', 'login.failed'].includes(a)) return 'red'
  if (a === 'client.record_viewed' || a.startsWith('setting')) return 'gold'
  return ''
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
.log-row { display: flex; gap: 12px; padding: 13px 0; border-top: 1px solid #f0f2f0; }
.log-row:first-child { border-top: none; padding-top: 0; }
.log-icon { width: 32px; height: 32px; border-radius: 9px; background: #eef3ec; color: #1e4a26; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.log-icon.red { background: #fdecec; color: #a12525; }
.log-icon.gold { background: #fdf1d6; color: #b8860b; }
.who { color: #1f8f5c; font-weight: 600; text-decoration: none; }
.who:hover { text-decoration: underline; }
.change { font-size: 0.76rem; color: #4a5a4a; background: #f7f9f7; border-radius: 6px; padding: 4px 8px; margin: 6px 0 0; overflow-wrap: anywhere; }
</style>
