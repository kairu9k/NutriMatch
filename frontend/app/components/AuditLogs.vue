
<template>
  <div class="nm-page au">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- hero -->
    <section class="ah">
      <img class="ah-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="ah-fade" aria-hidden="true"></span>
      <div class="ah-txt">
        <p class="ah-eyebrow"><span></span>Audit logs</p>
        <h1 class="ah-title">Who did what, and when</h1>
        <p class="ah-sub">Every sign-in, booking, payment and change, from people and from the system.</p>
        <p class="nm-note plain-note sealed">
          <Lock :size="15" aria-hidden="true" />
          <span><strong>Nothing here can be edited or deleted.</strong> It's the record of who did what and when, which RA 10173 requires.</span>
        </p>
      </div>
    </section>

    <!-- one toolbar: search, event, quick dates, admin only, export -->
    <div class="nm-panel filters">
      <div class="filter-row">
        <div class="nm-search f-search">
          <Search :size="17" aria-hidden="true" />
          <input v-model="search" type="search" placeholder="Search person, event or IP" />
        </div>
        <label class="f-sel">
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h18l-7 8v6l-4 2v-8z" /></svg>
          <select v-model="action" class="nm-select" aria-label="Filter by event">
            <option value="">All events</option>
            <option v-for="a in actionOptions" :key="a.key" :value="a.key">{{ a.label }} ({{ a.count }})</option>
          </select>
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
        </label>
        <button type="button" class="nm-btn-dark f-exp" :disabled="exporting || !count" @click="exportCsv">
          <Download :size="15" aria-hidden="true" /> {{ exporting ? 'Preparing…' : 'Export CSV' }}
        </button>
      </div>
      <div class="filter-row">
        <div class="nm-tabs quick-ranges" role="group" aria-label="Date range">
          <button v-for="r in RANGES" :key="r.label" type="button" class="nm-tab" :class="{ active: activeRange === r.label }" @click="setRange(r)">{{ r.label }}</button>
        </div>
        <div class="dates">
          <label class="date-field"><small>From</small> <DateField v-model="dateFrom" :max="dateTo || today" compact clearable hint="Pick the first day." placeholder="Any date" aria-label="From" /></label>
          <span class="dash" aria-hidden="true"></span>
          <label class="date-field"><small>To</small> <DateField v-model="dateTo" :min="dateFrom" :max="today" compact clearable hint="Pick the last day." placeholder="Any date" aria-label="To" /></label>
        </div>
        <label class="admin-only"><input v-model="adminOnly" type="checkbox" /><span class="sw" aria-hidden="true"><i></i></span> Admin actions only</label>
      </div>
    </div>

    <!-- THE JOURNAL: grouped by Philippine day, newest first -->
    <div ref="listTop" class="nm-panel journal">
      <div class="journal-head">
        <div>
          <h2 class="j-title">Activity</h2>
          <p class="j-sub">Newest first. Click an event to see every detail.</p>
        </div>
        <div class="j-right">
          <button v-if="hasFilters" type="button" class="nm-btn-soft nm-btn-sm" @click="clearFilters"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" /></svg>Clear filters</button>
          <span class="j-count">{{ loading ? 'Loading…' : `${count.toLocaleString()} event${count === 1 ? '' : 's'}` }}</span>
        </div>
      </div>
      <p v-if="loading && !logs.length" class="nm-muted j-pad">Loading audit log…</p>
      <div v-else-if="!logs.length" class="nm-empty j-pad">
        <span class="e-ico"><ScrollText :size="28" aria-hidden="true" /></span>
        <p>{{ hasFilters ? 'No events match these filters.' : 'No events recorded yet.' }}</p>
      </div>
      <div ref="scroller" class="journal-scroll">
        <section v-for="d in days" :key="d.key" class="day">
          <h3 class="day-title"><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg>{{ d.label }}</span><span class="day-count">{{ d.items.length }}</span></h3>
          <div class="evs">
            <button v-for="log in d.items" :key="log.id" type="button" class="entry" :class="toneOf(log.action)" @click="selected = log">
              <span class="entry-time">{{ timeText(log.created_at) }}</span>
              <span class="entry-mark" aria-hidden="true"><component :is="iconOf(log.action)" :size="16" /></span>
              <span class="entry-main">
                <span class="entry-title">{{ auditLabel(log.action) }}</span>
                <span class="entry-meta">
                  <span class="entry-who" :class="log.user ? `r-${log.user.role}` : 'r-sys'">
                    <template v-if="log.user"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><path d="M8 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /></svg></template><template v-else><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="8" width="14" height="11" rx="3" /><path d="M12 4v4M9 13h.01M15 13h.01" /></svg></template>{{ actorName(log) }}<template v-if="log.user">, {{ ROLE_LABELS[log.user.role] || log.user.role }}</template>
                  </span>
                  <template v-if="targetOf(log)"><span class="meta-sep" aria-hidden="true">on</span><span class="entry-tgt"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" /><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" /></svg>{{ targetOf(log) }}</span></template>
                </span>
                <span v-if="changeLines(log).length" class="entry-change">
                  <span v-for="(c, i) in changeLines(log)" :key="i" class="kv">{{ c }}</span>
                </span>
              </span>
              <ChevronRight :size="16" class="entry-go" aria-hidden="true" />
            </button>
          </div>
        </section>
      </div>
      <div class="j-pager"><ListPager :page="page" :pages="pageCount" @update:page="goTo" /></div>
    </div>

    <!-- ONE EVENT: everything that was stored, as evidence -->
    <div v-if="selected" class="nm-modal-overlay" @click.self="selected = null">
      <div class="nm-modal event au-ev" role="dialog" aria-modal="true" aria-labelledby="event-title">
        <div class="event-head nm-modal-head">
          <img class="em-plate" :src="plateImg" alt="" aria-hidden="true" />
          <span class="em-fade" aria-hidden="true"></span>
          <span class="event-mark" :class="toneOf(selected.action)"><component :is="iconOf(selected.action)" :size="22" aria-hidden="true" /></span>
          <div class="em-ht">
            <p class="em-kind">Event #{{ selected.id }}</p>
            <h3 id="event-title" class="nm-modal-title">{{ auditLabel(selected.action) }}</h3>
            <p class="nm-panel-sub em-sub"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 7v5l3 2" /></svg>{{ dateTime(selected.created_at) }}, event #{{ selected.id }}</p>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="selected = null"><X :size="18" aria-hidden="true" /></button>
        </div>

        <div class="em-body">
          <dl class="nm-dl facts">
            <div>
              <dt><span class="f-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><path d="M8 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /></svg></span>Done by</dt>
              <dd>
                <NuxtLink v-if="selected.user" :to="`/users/${selected.user.id}`" class="nm-text-link">{{ actorName(selected) }}</NuxtLink>
                <template v-else>System (automatic)</template>
                <span v-if="selected.user" class="sub">{{ ROLE_LABELS[selected.user.role] || selected.user.role }}, {{ selected.user.email }}</span>
              </dd>
            </div>
            <div>
              <dt><span class="f-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" /><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" /></svg></span>Record</dt>
              <dd>
                <NuxtLink v-if="selected.table_name === 'users' && selected.record_id" :to="`/users/${selected.record_id}`" class="nm-text-link">{{ targetOf(selected) }}</NuxtLink>
                <template v-else>{{ targetOf(selected) || '—' }}</template>
              </dd>
            </div>
            <div><dt><span class="f-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></svg></span>IP address</dt><dd :class="selected.ip_address ? 'mono' : 'muted'">{{ selected.ip_address || (selected.user ? 'Not recorded (older entry)' : 'None, done automatically') }}</dd></div>
            <div><dt><span class="f-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18" /></svg></span>Event code</dt><dd class="mono code">{{ selected.action }}</dd></div>
            <div v-if="selected.user_agent" class="wide"><dt><span class="f-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="13" rx="2" /><path d="M8 21h8M12 17v4" /></svg></span>Browser</dt><dd class="sub-dd">{{ selected.user_agent }}</dd></div>
          </dl>

          <h4 class="event-section"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>What was recorded</h4>
          <p v-if="!fieldRows(selected).length" class="nm-muted em-none">No values were stored with this event.</p>
          <div v-else class="nm-table-wrap diff-wrap">
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
        </div>

        <div class="nm-modal-actions em-foot">
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
const TABLE_LABELS = { meal_logs: 'Meal log', users: 'Account', rnd_profiles: 'RND profile', invoices: 'Invoice', system_settings: 'Setting', payouts: 'Payout', rnd_payout_accounts: 'Payout details', appointments: 'Appointment', audit_logs: 'Audit log' }

// Filtering and paging happen on the server (core/audit.py), PAGE_SIZE a page.
const route = useRoute()
const config = useRuntimeConfig()
const auth = useAuthStore()

const loading = ref(true)
const PAGE_SIZE = 20
const page = ref(1)
const listTop = ref(null)
const scroller = ref(null)
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
  scroller.value?.scrollTo({ top: 0 })
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
</script>

<style scoped>
.au { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.mono { font-variant-numeric: tabular-nums; }
.ic { flex-shrink: 0; display: inline-block; }

/* ---------- hero ---------- */
.ah { position: relative; overflow: hidden; margin-bottom: 18px; padding: 26px 30px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.ah-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.ah-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 52%, rgba(0, 77, 58, 0.85) 72%, rgba(0, 77, 58, 0.6) 100%); }
.ah-txt { position: relative; z-index: 1; max-width: 700px; }
.ah-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.ah-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.ah-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; color: #fff; }
.ah-sub { margin: 0; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }
.sealed { display: inline-flex; align-items: center; gap: 9px; margin: 16px 0 0; padding: 9px 14px; border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 12px; background: rgba(255, 255, 255, 0.1); font-size: 13px; line-height: 1.45; color: rgba(255, 255, 255, 0.88); }
.sealed svg { flex-shrink: 0; color: #efbf04; }
.sealed strong { color: #fff; }

/* ---------- toolbar ---------- */
.filters { display: flex; flex-direction: column; gap: 12px; margin-bottom: 18px; padding: 16px; border: none; border-radius: 22px; background: #fff; box-shadow: var(--sh); }
.filter-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.f-search { position: relative; flex: 1; min-width: 240px; max-width: none; display: flex; align-items: center; gap: 10px; height: 46px; margin: 0; padding: 0 16px; border: 1.5px solid #dce8e0; border-radius: 999px; background: #f7faf8; color: #8a9a91; box-sizing: border-box; }
.f-search:focus-within { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); background: #fff; }
.f-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.f-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; box-shadow: none !important; font-family: inherit; font-size: 14px; color: #14261e; }
.f-sel { display: flex; align-items: center; gap: 10px; min-width: 220px; height: 46px; padding: 0 16px; border: 1.5px solid #dce8e0; border-radius: 999px; background: #f7faf8; color: #1f7a4d; box-sizing: border-box; cursor: pointer; }
.f-sel:focus-within { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.f-sel .nm-select { flex: 1; width: auto; min-width: 0; height: 100%; padding: 0 !important; border: none !important; background: transparent !important; box-shadow: none !important; outline: none; appearance: none; -webkit-appearance: none; font-family: inherit; font-size: 14px; font-weight: 600; color: #14261e; cursor: pointer; }
.au .nm-btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 44px; padding: 0 18px; border: none; border-radius: 12px; background: #004d3a; color: #fff; font-family: inherit; font-size: 13.5px; font-weight: 800; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); cursor: pointer; }
.au .nm-btn-dark svg { color: #efbf04; }
.au .nm-btn-dark:disabled { opacity: 0.45; box-shadow: none; cursor: not-allowed; }
.f-exp { height: 46px !important; border-radius: 999px !important; }
.au .nm-btn-soft { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; border: 1px solid #dce8e0; border-radius: 999px; background: #fff; color: #004d3a; font-family: inherit; font-size: 12.5px; font-weight: 800; cursor: pointer; }
.quick-ranges { display: inline-flex; gap: 4px; margin: 0; padding: 5px; border: none; border-radius: 999px; background: #f1f6f2; }
.quick-ranges .nm-tab { display: inline-flex; align-items: center; height: 34px; margin: 0; padding: 0 14px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.quick-ranges .nm-tab:hover:not(.active) { background: #e3efe7; }
.quick-ranges .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.dates { display: flex; align-items: center; gap: 6px; }
.date-field { display: inline-flex; align-items: center; gap: 8px; padding: 4px 4px 4px 12px; border: 1.5px solid #dce8e0; border-radius: 12px; background: #fff; }
.date-field small { font-size: 11px; font-weight: 800; color: #8a9a91; }
.date-field :deep(.df-trigger) { border: none !important; box-shadow: none !important; background: transparent !important; }
.dash { width: 10px; height: 2px; border-radius: 2px; background: #c9d8cf; }
.admin-only { position: relative; display: inline-flex; align-items: center; gap: 10px; margin-left: auto; font-size: 13.5px; font-weight: 600; color: #22362c; cursor: pointer; }
.admin-only input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.sw { position: relative; width: 40px; height: 22px; border-radius: 999px; background: #c9d8cf; transition: background 0.15s; }
.sw i { position: absolute; left: 3px; top: 3px; width: 16px; height: 16px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2); transition: transform 0.15s; }
.admin-only input:checked + .sw { background: #004d3a; }
.admin-only input:checked + .sw i { transform: translateX(18px); background: #efbf04; }
.admin-only input:focus-visible + .sw { outline: 2px solid #1f8f5c; outline-offset: 2px; }

/* ---------- journal ---------- */
.journal { padding: 0; border: none; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: hidden; }
.journal-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 22px 26px 12px; border: none; }
.j-title { margin: 0 0 3px; font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; color: #0e3a2c; }
.j-sub { margin: 0; font-size: 13px; color: #6b7d73; }
.j-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }
.j-count { padding: 5px 12px; border-radius: 999px; background: #e3efe7; font-size: 12.5px; font-weight: 800; color: #004d3a; white-space: nowrap; }
.j-pad { padding: 10px 26px 26px; }
.au :deep(.nm-empty) { display: flex; flex-direction: column; align-items: center; gap: 10px; text-align: center; }
.au :deep(.nm-empty p) { margin: 0; font-size: 14px; font-weight: 600; color: #4a5a52; }
.e-ico { width: 56px; height: 56px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.journal-scroll { padding: 0 26px 8px; }
.day-title { display: flex; align-items: center; gap: 8px; margin: 14px 0 6px; padding: 8px 12px; border-radius: 12px; background: #f1f6f2; font-family: inherit; font-size: 13.5px; font-weight: 800; color: #004d3a; }
.day-title > span:first-child { display: inline-flex; align-items: center; gap: 8px; }
.day-title .ic { color: #1f7a4d; }
.day-count { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: #004d3a; color: #efbf04; font-size: 11px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.evs { position: relative; }
.evs::before { content: ''; position: absolute; left: 116px; top: 14px; bottom: 14px; width: 2px; border-radius: 2px; background: #e3ebe6; }
.entry { position: relative; display: grid; grid-template-columns: 76px 34px minmax(0, 1fr) 20px; align-items: center; column-gap: 14px; width: 100%; margin: 0; padding: 11px 10px; border: 0; border-radius: 12px; background: none; font-family: inherit; text-align: left; color: inherit; cursor: pointer; }
.entry:hover { background: #f7faf8; }
.entry:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.entry-time { padding-top: 0; font-size: 12.5px; font-weight: 700; color: #8a9a91; text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.entry-mark { position: relative; z-index: 1; width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 0 0 4px #fff; }
.entry:hover .entry-mark { box-shadow: 0 0 0 4px #f7faf8; }
.entry-main { display: flex; flex-direction: column; gap: 5px; min-width: 0; padding-top: 2px; }
.entry-title { font-size: 14.5px; font-weight: 800; color: #0e3a2c; }
.entry-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; font-size: 12.5px; color: #6b7d73; }
.entry-who { display: inline-flex; align-items: center; gap: 5px; font-weight: 700; color: #22362c; }
.entry-who .ic { width: 20px; height: 20px; padding: 4px; border-radius: 50%; box-sizing: border-box; }
.entry-who.r-sys .ic { background: #eef2ef; color: #6b7d73; }
.entry-who.r-client .ic { background: #fff4d6; color: #8a6500; }
.entry-who.r-rnd .ic { background: #e3f4ea; color: #1f7a4d; }
.entry-who.r-admin .ic { background: #e3efe7; color: #004d3a; }
.meta-sep { color: #a9b6ae; }
.entry-tgt { display: inline-flex; align-items: center; gap: 4px; font-weight: 700; color: #1f7a4d; }
.entry-tgt .ic { color: #8a9a91; }
.entry-change { display: flex; flex-wrap: wrap; gap: 6px; }
.kv { max-width: 100%; padding: 4px 10px; border: 1px solid #eef2ef; border-radius: 8px; background: #f7faf8; font-size: 12.5px; color: #4a5a52; overflow-wrap: anywhere; }
.entry-go { color: #c9d3cd; }
.entry:hover .entry-go { color: #1f7a4d; }
.entry + .entry::after { content: ''; position: absolute; left: 148px; right: 10px; top: 0; height: 1px; background: #eef2ef; }
.tone-plain .entry-mark, .event-mark.tone-plain { background: #eef3ef; color: #4a6a55; }
.tone-green .entry-mark, .event-mark.tone-green { background: #e3f4ea; color: #1f7a4d; }
.tone-gold .entry-mark, .event-mark.tone-gold { background: #fff4d6; color: #8a6500; }
.tone-red .entry-mark, .event-mark.tone-red { background: #fde2df; color: #b42318; }
.j-pager { margin-top: 10px; padding: 0 26px; border-top: 1px solid #eef2ef; background: #f7faf8; }
.j-pager :deep(.nm-pager) { margin: 0; padding: 14px 0; }

@media (max-width: 760px) {
  .au { padding-bottom: 110px; }
  .ah { padding: 20px 18px; border-radius: 22px; }
  .ah-title { font-size: 24px; }
  .ah-plate { width: 180px; height: 180px; right: -60px; top: 20px; transform: none; }
  .ah-txt { max-width: 88%; }
}
@media (max-width: 640px) {
  .f-search, .f-sel { flex: 1 1 100%; min-width: 0; }
  .f-exp { flex: 1; }
  .quick-ranges { width: 100%; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border-radius: 14px; }
  .quick-ranges .nm-tab { justify-content: center; padding: 0 4px; }
  .dates { width: 100%; }
  .date-field { flex: 1; min-width: 0; }
  .date-field :deep(.df-trigger) { flex: 1; min-width: 0; }
  .admin-only { margin-left: 0; width: 100%; }
  .journal-head { flex-wrap: wrap; padding: 18px 16px 10px; }
  .journal-scroll { padding: 0 12px 8px; }
  .j-pad { padding: 10px 16px 20px; }
  .j-pager { padding: 0 16px; }
  .evs::before { left: 25px; }
  .entry { grid-template-columns: 36px minmax(0, 1fr); row-gap: 4px; padding: 10px 6px; }
  .entry-mark { align-self: start; }
  .entry-time { grid-column: 2; grid-row: 1; padding: 0; text-align: left; font-size: 12px; font-weight: 600; color: #8a9a91; }
  .entry-mark { grid-column: 1; grid-row: 1 / span 2; }
  .entry-main { grid-column: 2; grid-row: 2; padding-top: 0; }
  .entry + .entry::after { left: 54px; }
  .entry-go { display: none; }
  .diff-key { white-space: normal; }
}
</style>

<style>
/* the event pop-up, unscoped so the app's global modal styles can't override it */
.nm-modal-overlay .nm-modal.au-ev { display: flex; flex-direction: column; width: min(760px, calc(100vw - 32px)) !important; max-width: 760px !important; min-width: 0 !important; height: auto !important; max-height: calc(100vh - 48px) !important; margin: auto !important; padding: 0 !important; border-radius: 24px; overflow: hidden !important; }
.nm-modal.au-ev .event-head { position: relative !important; top: auto !important; overflow: hidden; flex-shrink: 0; display: flex; align-items: center; gap: 16px; margin: 0 !important; padding: 24px 28px !important; min-height: 0 !important; border: none !important; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 55%, #004635 100%); }
.nm-modal.au-ev .event-head > *:not(.em-plate):not(.em-fade) { position: relative; z-index: 1; }
.nm-modal.au-ev .em-plate { position: absolute; right: -60px; top: 50%; width: 220px; height: 220px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.nm-modal.au-ev .em-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 55%, rgba(0, 77, 58, 0.88) 75%, rgba(0, 77, 58, 0.7) 100%); }
.nm-modal.au-ev .event-head .event-mark { flex-shrink: 0; width: 56px; height: 56px; border-radius: 16px; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 24px -10px rgba(0, 0, 0, 0.4); }
.nm-modal.au-ev .event-head .event-mark.tone-plain { background: #fff; color: #004d3a; }
.nm-modal.au-ev .em-ht { flex: 1; min-width: 0; }
.nm-modal.au-ev .em-kind { margin: 0 0 2px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.nm-modal.au-ev .em-ht .nm-modal-title { margin: 0 !important; padding: 0 !important; font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 700; line-height: 1.25; color: #fff !important; }
.nm-modal.au-ev .em-sub { display: flex; align-items: center; gap: 6px; margin: 4px 0 0 !important; font-size: 13px; color: rgba(255, 255, 255, 0.82) !important; }
.nm-modal.au-ev .event-head .nm-modal-x { position: static !important; inset: auto !important; float: none !important; flex-shrink: 0; width: 38px !important; height: 38px !important; margin: 0 !important; padding: 0 !important; border: 1px solid rgba(255, 255, 255, 0.25) !important; border-radius: 12px !important; background: rgba(0, 0, 0, 0.22) !important; color: #fff !important; opacity: 1 !important; display: inline-flex !important; align-items: center; justify-content: center; cursor: pointer; }
.nm-modal.au-ev .em-body { flex: 1 1 auto; min-height: 0 !important; overflow-y: auto !important; overscroll-behavior: contain; padding: 24px 28px 28px; }
.nm-modal.au-ev .facts { display: grid !important; grid-template-columns: 1fr 1fr !important; gap: 12px !important; margin: 0; }
.nm-modal.au-ev .facts > div { display: flex; flex-direction: column; gap: 6px; min-width: 0; margin: 0 !important; padding: 14px 16px !important; border: 1.5px solid #e3ebe6 !important; border-radius: 16px; background: #f7faf8; }
.nm-modal.au-ev .facts .wide { grid-column: 1 / -1; }
.nm-modal.au-ev .facts dt { display: flex; align-items: center; gap: 8px; margin: 0; font-size: 12px; font-weight: 700; color: #6b7d73; }
.nm-modal.au-ev .f-ico { width: 28px; height: 28px; border-radius: 9px; background: #fff; color: #004d3a; box-shadow: 0 0 0 1px #e3ebe6; display: inline-flex; align-items: center; justify-content: center; }
.nm-modal.au-ev .facts dd { margin: 0; font-size: 14.5px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.nm-modal.au-ev .facts dd.muted { font-weight: 500; color: #8a9a91; }
.nm-modal.au-ev .facts .nm-text-link { color: #1f7a4d; font-weight: 800; }
.nm-modal.au-ev .code { align-self: flex-start; padding: 3px 8px; border-radius: 8px; background: #fff; font-family: ui-monospace, Menlo, monospace; font-size: 13px; color: #004d3a; box-shadow: 0 0 0 1px #e3ebe6; }
.nm-modal.au-ev .sub { display: block; margin-top: 2px; font-size: 12.5px; font-weight: 400; color: #8a9a91; overflow-wrap: anywhere; }
.nm-modal.au-ev .sub-dd { font-size: 12.5px !important; font-weight: 400 !important; color: #6b7d73 !important; font-family: ui-monospace, Menlo, monospace; }
.nm-modal.au-ev .event-section { display: flex; align-items: center; gap: 8px; margin: 24px 0 12px; font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: #0e3a2c; }
.nm-modal.au-ev .event-section .ic { color: #1f7a4d; }
.nm-modal.au-ev .em-none { padding: 14px 16px; border: 1.5px dashed #c9d8cf; border-radius: 16px; }
.nm-modal.au-ev .diff-wrap { margin: 0; border: 1.5px solid #c9d8cf; border-radius: 18px; overflow: hidden; }
.nm-modal.au-ev .diff { width: 100%; border-collapse: collapse; }
.nm-modal.au-ev .diff thead th { padding: 12px 16px; background: #004d3a; border: none; text-align: left; font-size: 12.5px; font-weight: 700; color: #fff; text-transform: none; letter-spacing: 0; }
.nm-modal.au-ev .diff td { padding: 12px 16px; border-top: 1px solid #eef2ef; vertical-align: top; overflow-wrap: anywhere; font-size: 13.5px; }
.nm-modal.au-ev .diff tbody tr:first-child td { border-top: none; }
.nm-modal.au-ev .diff-key { font-weight: 700; color: #4a5a52; white-space: nowrap; }
.nm-modal.au-ev .diff-old { color: #8a9a91; text-decoration: line-through; text-decoration-color: #e3a5a0; background: #fef7f6; }
.nm-modal.au-ev .diff-new { color: #0e3a2c; font-weight: 700; background: #f5faf7; }
.nm-modal.au-ev .em-foot { flex-shrink: 0; display: flex; justify-content: flex-end; gap: 10px; margin: 0; padding: 14px 28px; border-top: 1px solid #eef2ef; background: #f7faf8; }
.nm-modal.au-ev { background: #fff !important; }
.nm-modal.au-ev .ic { flex-shrink: 0; display: inline-block; }
.nm-modal.au-ev .event-head { background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 55%, #004635 100%) !important; }
.nm-modal.au-ev .event-mark.tone-plain { background: #fff !important; color: #004d3a !important; }
.nm-modal.au-ev .event-mark.tone-green { background: #e3f4ea !important; color: #1f7a4d !important; }
.nm-modal.au-ev .event-mark.tone-gold { background: #fff4d6 !important; color: #8a6500 !important; }
.nm-modal.au-ev .event-mark.tone-red { background: #fde2df !important; color: #b42318 !important; }
@media (max-width: 760px) {
  .nm-modal-overlay .nm-modal.au-ev { width: calc(100vw - 24px) !important; max-height: calc(100dvh - 24px) !important; border-radius: 22px !important; }
  .nm-modal.au-ev .event-head { padding: 18px !important; }
  .nm-modal.au-ev .event-head .event-mark { width: 46px !important; height: 46px !important; }
  .nm-modal.au-ev .em-ht .nm-modal-title { font-size: 20px !important; }
  .nm-modal.au-ev .em-body { padding: 18px !important; }
  .nm-modal.au-ev .facts { grid-template-columns: 1fr !important; }
  .nm-modal.au-ev .em-foot { padding: 12px 18px !important; }
  .nm-modal.au-ev .em-foot > * { flex: 1; }
}
</style>