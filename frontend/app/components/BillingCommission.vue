<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-stat-grid">
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><Banknote :size="17" /></div>
        <p class="nm-stat-value">{{ peso(totals.gross) }}</p>
        <p class="nm-stat-label">Collected from clients</p>
        <p class="nm-stat-note">{{ paid.length }} paid consultation{{ paid.length === 1 ? '' : 's' }}, all time</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon gold"><Coins :size="17" /></div>
        <p class="nm-stat-value">{{ peso(totals.commission) }}</p>
        <p class="nm-stat-label">Platform commission</p>
        <p class="nm-stat-note">Current rate {{ currentRate }}%</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><Wallet :size="17" /></div>
        <p class="nm-stat-value">{{ peso(totals.net) }}</p>
        <p class="nm-stat-label">RNDs' share</p>
        <NuxtLink to="/payouts" class="nm-stat-note good" style="text-decoration: none">Manage payouts →</NuxtLink>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon gold"><RotateCcw :size="17" /></div>
        <p class="nm-stat-value">{{ refundsDue.length }}</p>
        <p class="nm-stat-label">Refunds to send</p>
        <p class="nm-stat-note" :class="{ warn: refundsDue.length }">{{ refundsDue.length ? peso(refundsDue.reduce((s, i) => s + Number(i.amount), 0)) + ' owed to clients' : 'None right now' }}</p>
      </div>
    </div>

    <div class="nm-toolbar">
      <div class="nm-tabs">
        <button class="nm-tab" :class="{ active: tab === 'invoices' }" @click="tab = 'invoices'">Invoices <span class="nm-count">{{ invoices.length }}</span></button>
        <button class="nm-tab" :class="{ active: tab === 'refunds' }" @click="tab = 'refunds'">Refunds <span class="nm-count">{{ refundsDue.length }}</span></button>
        <button class="nm-tab" :class="{ active: tab === 'commission' }" @click="tab = 'commission'">Commission</button>
      </div>
      <template v-if="tab === 'invoices'">
        <div class="nm-search">
          <Search :size="15" />
          <input v-model="search" type="search" placeholder="Search client, RND or INV no." />
        </div>
      </template>
    </div>

    <!-- INVOICES -->
    <div v-if="tab === 'invoices'" class="nm-panel">
      <div class="nm-panel-head">
        <div>
          <h2 class="nm-panel-title">Invoice log</h2>
          <p class="nm-panel-sub">Issued when an RND confirms a booking. Clients pay before the consultation.</p>
        </div>
        <select v-model="statusFilter" class="nm-select" aria-label="Filter by status">
          <option value="">All statuses</option>
          <option v-for="(label, key) in STATUS_LABELS" :key="key" :value="key">{{ label }}</option>
        </select>
      </div>
      <p v-if="loading" class="nm-muted">Loading invoices…</p>
      <div v-else-if="!filteredInvoices.length" class="nm-empty">
        <Receipt :size="28" />
        <p>{{ invoices.length ? 'No invoices match these filters.' : 'No invoices yet.' }}</p>
      </div>
      <div v-else class="nm-table-wrap">
        <table class="nm-table stack">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Client → RND</th>
              <th>Issued</th>
              <th>Paid via</th>
              <th class="nm-num">Amount</th>
              <th class="nm-num">Commission</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="inv in filteredInvoices" :key="inv.id">
              <td data-label="Invoice" class="mono"><strong>{{ invNo(inv) }}</strong></td>
              <td data-label="Client → RND">{{ inv.client_name }} → {{ inv.rnd_name }}</td>
              <td data-label="Issued">{{ shortDate(inv.created_at) }}</td>
              <td data-label="Paid via">{{ inv.payment_method ? (METHOD_LABELS[inv.payment_method] || inv.payment_method) : '—' }}</td>
              <td data-label="Amount" class="nm-num">{{ peso(inv.amount) }}</td>
              <td data-label="Commission" class="nm-num">{{ peso(inv.commission_amt) }} <span class="nm-muted">({{ Number(inv.commission_pct) }}%)</span></td>
              <td data-label="Status"><span class="nm-pill" :class="STATUS_PILLS[inv.status] || 'muted'">{{ STATUS_LABELS[inv.status] || inv.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- REFUNDS -->
    <div v-else-if="tab === 'refunds'" class="nm-panel">
      <div class="nm-panel-head">
        <div>
          <h2 class="nm-panel-title">Refunds to send</h2>
          <p class="nm-panel-sub">These consultations were paid, then cancelled. Refund each one in the PayMongo dashboard, then mark it refunded here — the client is notified.</p>
        </div>
      </div>
      <p v-if="refundError" class="nm-error">{{ refundError }}</p>
      <div v-if="!refundsDue.length" class="nm-empty">
        <CheckCircle2 :size="28" />
        <p>No refunds waiting.</p>
      </div>
      <div v-for="inv in refundsDue" :key="inv.id" class="nm-row refund-row">
        <div class="nm-row-main">
          <p class="nm-row-title">{{ invNo(inv) }} · {{ inv.client_name }} → {{ inv.rnd_name }}</p>
          <p class="nm-row-sub">
            {{ peso(inv.amount) }}<template v-if="inv.payment_method"> · paid via {{ METHOD_LABELS[inv.payment_method] || inv.payment_method }}</template><template v-if="inv.paid_at"> on {{ shortDate(inv.paid_at) }}</template>
          </p>
        </div>
        <div class="refund-actions">
          <input v-model="refundRefs[inv.id]" class="nm-input" maxlength="100" placeholder="PayMongo refund ref (optional)" />
          <button class="nm-btn-dark" :disabled="refundBusy === inv.id" @click="markRefunded(inv)">
            {{ refundBusy === inv.id ? 'Saving…' : 'Mark as refunded' }}
          </button>
        </div>
      </div>
    </div>

    <!-- COMMISSION -->
    <div v-else class="nm-grid-even">
      <div class="nm-panel">
        <h2 class="nm-panel-title">Platform commission</h2>
        <p class="nm-panel-sub">NutriMatch's share of each consultation fee. The RND receives the rest.</p>
        <label class="nm-label" for="commission" style="margin-top: 18px">Commission rate (%)</label>
        <input id="commission" v-model="commissionRate" class="nm-input" type="number" min="0" max="50" step="0.01" :disabled="!settingsLoaded" style="max-width: 180px" />
        <p v-if="commissionError" class="nm-field-error">{{ commissionError }}</p>
        <p v-else class="nm-hint">Between 0% and 50%. Example: on a {{ peso(800) }} consultation, {{ commissionPreview }}.</p>
        <div style="margin-top: 16px">
          <button class="nm-btn-dark" :disabled="saving || !settingsLoaded || commissionRate === currentRate" @click="saveCommission">
            {{ saving ? 'Saving…' : 'Save rate' }}
          </button>
        </div>
      </div>
      <div class="nm-panel">
        <h2 class="nm-panel-title">How changes apply</h2>
        <p class="nm-modal-text" style="margin-top: 10px">
          Each invoice freezes the rate it was issued with. A new rate only applies to bookings confirmed after you save it —
          RNDs' earnings on existing invoices never change.
        </p>
        <p class="nm-modal-text" style="margin: 0">Every change is recorded in the audit log with the old and new rate.</p>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { Banknote, CheckCircle2, Coins, Receipt, RotateCcw, Search, Wallet } from 'lucide-vue-next'

const { get, patch, post } = useApi()
const route = useRoute()

const METHOD_LABELS = { card: 'Card', gcash: 'GCash', maya: 'Maya', qrph: 'QR Ph', bank_transfer: 'Bank transfer', cash: 'Cash', other: 'Other' }
// cancelled = voided (appointment cancelled / not paid in time).
const STATUS_LABELS = { unpaid: 'Awaiting payment', paid: 'Paid', refund_pending: 'Refund pending', refunded: 'Refunded', cancelled: 'Voided' }
const STATUS_PILLS = { unpaid: 'gold', paid: 'green', refund_pending: 'red', refunded: 'blue', cancelled: 'muted' }

const tab = ref(['invoices', 'refunds', 'commission'].includes(route.query.tab) ? route.query.tab : 'invoices')
watch(tab, t => navigateTo({ query: { ...route.query, tab: t } }, { replace: true }))

const loading = ref(true)
const error = ref('')
const invoices = ref([])
const search = ref('')
const statusFilter = ref('')
const toast = ref('')

function flash(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3500)
}

async function loadInvoices() {
  try {
    invoices.value = await get('/admin/invoices/')
  } catch {
    error.value = 'Could not load billing data. Please refresh the page.'
  } finally {
    loading.value = false
  }
}

const paid = computed(() => invoices.value.filter(i => i.status === 'paid'))
const totals = computed(() => paid.value.reduce((t, i) => ({
  gross: t.gross + Number(i.amount),
  commission: t.commission + Number(i.commission_amt),
  net: t.net + Number(i.net),
}), { gross: 0, commission: 0, net: 0 }))

const invNo = inv => `INV-${String(inv.id).padStart(4, '0')}`
const filteredInvoices = computed(() => {
  const q = search.value.trim().toLowerCase()
  return invoices.value.filter(i =>
    (!statusFilter.value || i.status === statusFilter.value)
    && (!q || `${invNo(i)} ${i.client_name} ${i.rnd_name}`.toLowerCase().includes(q)))
})

/* refunds — not automated: the admin refunds in PayMongo, then records it */
const refundsDue = computed(() => invoices.value.filter(i => i.status === 'refund_pending'))
const refundRefs = reactive({})
const refundBusy = ref(null)
const refundError = ref('')
async function markRefunded(inv) {
  refundBusy.value = inv.id
  refundError.value = ''
  try {
    await post(`/admin/invoices/${inv.id}/mark-refunded/`, { reference: (refundRefs[inv.id] || '').trim() || undefined })
    await loadInvoices()
    flash(`${invNo(inv)} marked as refunded — ${inv.client_name} was notified.`)
  } catch (e) {
    refundError.value = apiError(e, 'Could not update this refund. Please try again.')
  } finally {
    refundBusy.value = null
  }
}

/* commission */
const commissionRate = ref('')
const currentRate = ref('')
const settingsLoaded = ref(false)
const saving = ref(false)
const commissionError = ref('')
const commissionPreview = computed(() => {
  const pct = Number(commissionRate.value)
  if (Number.isNaN(pct) || pct < 0 || pct > 50) return 'enter a rate to see the split'
  const cut = 800 * pct / 100
  return `NutriMatch keeps ${peso(cut)} and the RND gets ${peso(800 - cut)}`
})

async function loadSettings() {
  try {
    const settings = await get('/admin/settings/')
    const s = settings.find(x => x.key === 'platform_commission_pct')
    currentRate.value = commissionRate.value = s ? String(Number(s.value)) : '10'
  } catch {
    currentRate.value = commissionRate.value = '10'
  } finally {
    settingsLoaded.value = true
  }
}

async function saveCommission() {
  commissionError.value = ''
  saving.value = true
  try {
    const updated = await patch('/admin/settings/platform_commission_pct/', { value: String(commissionRate.value) })
    currentRate.value = commissionRate.value = String(Number(updated.value))
    flash(`Saved — new bookings use ${currentRate.value}% commission.`)
  } catch (e) {
    commissionError.value = apiError(e, 'Could not save. Please try again.')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadInvoices()
  loadSettings()
})
</script>

<style scoped>
.mono { font-variant-numeric: tabular-nums; }
.refund-row { flex-wrap: wrap; }
.refund-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.refund-actions .nm-input { width: 240px; max-width: 100%; }
@media (max-width: 640px) {
  .refund-actions { width: 100%; }
  .refund-actions > * { width: 100% !important; }
}
</style>
