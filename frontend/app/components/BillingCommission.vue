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
            <tr
              v-for="inv in filteredInvoices" :key="inv.id" class="clickable" tabindex="0"
              :aria-label="`View ${invNo(inv)} details`" @click="openInvoice(inv)" @keydown.enter="openInvoice(inv)"
            >
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
          <p class="nm-panel-sub">These consultations were paid, then cancelled. Refund each one through PayMongo — it turns Refunded only once PayMongo confirms the money went back, and the client is notified.</p>
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
        <div v-if="inv.paymongo_payment_id" class="refund-actions">
          <p v-if="refundNotes[inv.id]" class="refund-state" :class="refundNotes[inv.id].tone">{{ refundNotes[inv.id].text }}</p>
          <template v-if="refundConfirm === inv.id">
            <span class="nm-hint">Send {{ peso(inv.amount) }} back to {{ inv.client_name }}?</span>
            <button class="nm-btn-dark" :disabled="refundBusy === inv.id" @click="refundViaPayMongo(inv)">
              {{ refundBusy === inv.id ? 'Sending to PayMongo…' : 'Yes, refund' }}
            </button>
            <button class="nm-btn-outline" :disabled="refundBusy === inv.id" @click="refundConfirm = null">Cancel</button>
          </template>
          <button v-else class="nm-btn-dark" @click="refundConfirm = inv.id">Refund through PayMongo</button>
        </div>
        <div v-else class="refund-actions">
          <p class="refund-state muted">Not paid through PayMongo — return the money another way, then mark it refunded.</p>
          <input v-model="refundRefs[inv.id]" class="nm-input" maxlength="100" placeholder="Refund reference (optional)" />
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

    <!-- INVOICE DETAIL + RECEIPT -->
    <div v-if="selected" class="nm-modal-overlay" @click.self="closeInvoice">
      <div class="nm-modal detail" role="dialog" aria-modal="true" :aria-label="`${invNo(selected)} details`">
        <div class="detail-head nm-modal-head">
          <div>
            <p class="nm-section-title" style="margin: 0 0 4px">Invoice</p>
            <h3 class="nm-modal-title mono" style="margin: 0">{{ invNo(selected) }}</h3>
            <p class="nm-panel-sub">Issued {{ dateTime(selected.created_at) }}</p>
          </div>
          <div class="head-right">
            <span class="nm-pill" :class="STATUS_PILLS[selected.status] || 'muted'">{{ STATUS_LABELS[selected.status] || selected.status }}</span>
            <button class="close-btn" aria-label="Close" @click="closeInvoice"><X :size="18" /></button>
          </div>
        </div>

        <p v-if="detailError" class="nm-error" style="margin-top: 14px">{{ detailError }}</p>
        <p v-else-if="!detail" class="nm-muted" style="margin-top: 14px">Loading invoice…</p>

        <template v-else>
          <p class="nm-section-title">Consultation</p>
          <dl class="nm-dl">
            <div>
              <dt>Client</dt>
              <dd>{{ detail.client.name }}<span class="sub">{{ detail.client.email }}</span></dd>
            </div>
            <div>
              <dt>RND</dt>
              <dd>{{ detail.rnd.name }}<span class="sub">{{ detail.rnd.email }}</span></dd>
            </div>
            <template v-if="detail.appointment">
              <div>
                <dt>Scheduled</dt>
                <dd>{{ dateTime(detail.appointment.scheduled_at) }}<span class="sub">{{ detail.appointment.duration_minutes || 60 }} min · {{ MODE_LABELS[detail.appointment.type] || detail.appointment.type }}</span></dd>
              </div>
              <div>
                <dt>Appointment</dt>
                <dd>{{ APPT_LABELS[detail.appointment.status] || detail.appointment.status }}<span v-if="detail.appointment.cancellation_reason" class="sub">{{ detail.appointment.cancellation_reason }}</span></dd>
              </div>
            </template>
            <div v-else>
              <dt>Appointment</dt>
              <dd class="muted">No longer linked</dd>
            </div>
          </dl>

          <p class="nm-section-title">Amount</p>
          <div class="lines">
            <div class="line"><span>Consultation fee</span><span>{{ peso(detail.amount) }}</span></div>
            <div class="line"><span>Platform commission ({{ Number(detail.commission_pct) }}%)</span><span>− {{ peso(detail.commission_amt) }}</span></div>
            <div class="line total"><span>RND's share</span><span>{{ peso(detail.net) }}</span></div>
            <p class="nm-hint">{{ detail.payout ? 'Paid out to the RND in a monthly payout.' : 'Not paid out to the RND yet.' }}</p>
          </div>

          <p class="nm-section-title">Payment receipt</p>
          <div v-if="payment" class="receipt">
            <div class="receipt-top">
              <CheckCircle2 :size="20" />
              <div>
                <p class="receipt-amount">{{ peso(payment.receipt.amount || payment.amount) }}</p>
                <p class="nm-hint" style="margin: 0">Paid by {{ payment.receipt.payer_name || detail.client.name }} · {{ dateTime(payment.receipt.paid_at || detail.paid_at || payment.processed_at) }}</p>
              </div>
              <span v-if="payment.receipt.livemode === false" class="nm-pill gold test-pill">Test mode</span>
            </div>
            <dl class="receipt-rows">
              <div><dt>Payment method</dt><dd>{{ methodText }}</dd></div>
              <div v-if="payment.receipt.payment_id"><dt>PayMongo payment ID</dt><dd class="mono">{{ payment.receipt.payment_id }}</dd></div>
              <div v-if="detail.gateway_reference_id"><dt>Reference no.</dt><dd class="mono">{{ detail.gateway_reference_id }}</dd></div>
              <div v-if="payment.receipt.payer_email"><dt>Payer email</dt><dd>{{ payment.receipt.payer_email }}</dd></div>
              <div v-if="payment.receipt.payer_phone"><dt>Payer phone</dt><dd>{{ payment.receipt.payer_phone }}</dd></div>
              <div v-if="payment.receipt.description"><dt>Description</dt><dd>{{ payment.receipt.description }}</dd></div>
              <div v-if="payment.receipt.fee"><dt>PayMongo fee</dt><dd>− {{ peso(payment.receipt.fee) }}</dd></div>
              <div v-if="payment.receipt.net_amount"><dt>Received by NutriMatch</dt><dd><strong>{{ peso(payment.receipt.net_amount) }}</strong></dd></div>
              <div><dt>Recorded via</dt><dd>{{ SOURCE_LABELS[payment.source] || payment.source || '—' }}</dd></div>
            </dl>
            <p v-if="!payment.receipt.payment_id" class="nm-hint" style="margin-top: 10px">
              The gateway's receipt details weren't stored for this payment{{ payment.source === 'seed_demo' ? ' (demo data)' : '' }}, so only NutriMatch's record is shown.
            </p>
          </div>
          <div v-else class="nm-empty" style="padding: 14px 12px">
            <Receipt :size="24" />
            <p>{{ selected.status === 'unpaid' ? 'The client hasn\'t paid this invoice yet.' : 'No payment was made on this invoice.' }}</p>
          </div>

          <div v-if="payment?.receipt?.payment_id" class="pm-box">
            <div class="pm-head">
              <p class="nm-section-title" style="margin: 0">In PayMongo</p>
              <button class="nm-btn-outline nm-btn-sm" :disabled="pmLoading" @click="checkPayMongo">{{ pmLoading ? 'Checking…' : 'Check with PayMongo' }}</button>
            </div>
            <p v-if="pmError" class="nm-error" style="margin: 8px 0 0">{{ pmError }}</p>
            <template v-else-if="pm">
              <p class="pm-line">
                Payment <span class="mono">{{ pm.payment_id }}</span> ·
                <strong>{{ pm.refunded ? 'Refunded' : pm.in_progress ? 'Refund in progress' : 'Paid' }}</strong>
                <span v-if="pm.livemode === false" class="nm-pill gold" style="margin-left: 6px">Test mode</span>
              </p>
              <p v-if="!pm.refunds.length" class="nm-hint" style="margin: 4px 0 0">No refund sent to PayMongo yet.</p>
              <div v-for="r in pm.refunds" :key="r.id" class="line">
                <span><span class="mono">{{ r.id }}</span><span class="sub">{{ dateTime(unix(r.refunded_at || r.created_at)) }}</span></span>
                <span>{{ peso(r.amount) }} <span class="nm-pill" :class="PM_REFUND_PILLS[r.status] || 'muted'">{{ PM_REFUND_LABELS[r.status] || r.status }}</span></span>
              </div>
              <p v-if="pm.refunds.some(r => r.status === 'failed') && pm.source_type === 'qrph' && pm.livemode === false" class="nm-hint" style="margin: 6px 0 0">
                PayMongo's test mode can't complete QR Ph refunds — GCash, Maya and card refunds work in test mode.
              </p>
            </template>
            <div v-if="selected.status === 'refund_pending'" class="refund-actions" style="margin-top: 10px">
              <template v-if="refundConfirm === selected.id">
                <span class="nm-hint">Send {{ peso(selected.amount) }} back to {{ selected.client_name }}?</span>
                <button class="nm-btn-dark" :disabled="refundBusy === selected.id" @click="refundViaPayMongo(selected)">{{ refundBusy === selected.id ? 'Sending to PayMongo…' : 'Yes, refund' }}</button>
                <button class="nm-btn-outline" :disabled="refundBusy === selected.id" @click="refundConfirm = null">Cancel</button>
              </template>
              <button v-else class="nm-btn-dark" @click="refundConfirm = selected.id">Refund through PayMongo</button>
            </div>
          </div>

          <template v-if="refunds.length">
            <p class="nm-section-title">Refunds</p>
            <div v-for="r in refunds" :key="r.id" class="line">
              <span>Refunded {{ dateTime(r.processed_at || r.created_at) }}<span v-if="r.reference" class="sub mono">Ref {{ r.reference }}</span></span>
              <span>{{ peso(r.amount) }}</span>
            </div>
          </template>
        </template>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { Banknote, CheckCircle2, Coins, Receipt, RotateCcw, Search, Wallet, X } from 'lucide-vue-next'

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

/* invoice detail overlay — details + the client's payment receipt */
const APPT_LABELS = { pending: 'Awaiting RND confirmation', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }
const SOURCE_LABELS = { webhook: 'PayMongo notification', status_check: 'PayMongo status check', seed_demo: 'Demo data', admin: 'Admin', paymongo: 'PayMongo' }
const selected = ref(null)
const detail = ref(null)
const detailError = ref('')

async function openInvoice(inv) {
  selected.value = inv
  detail.value = null
  detailError.value = ''
  pm.value = null
  pmError.value = ''
  refundConfirm.value = null
  try {
    const d = await get(`/admin/invoices/${inv.id}/`)
    if (selected.value?.id === inv.id) detail.value = d
    if (inv.paymongo_payment_id) checkPayMongo()
  } catch (e) {
    if (selected.value?.id === inv.id) detailError.value = apiError(e, 'Could not load this invoice. Please try again.')
  }
}
function closeInvoice() { selected.value = null }
function onKey(e) { if (e.key === 'Escape' && selected.value) closeInvoice() }

// The successful payment (newest, in case of a re-payment).
const payment = computed(() => [...(detail.value?.transactions || [])].reverse()
  .find(t => t.transaction_type === 'payment' && t.status === 'success') || null)
const refunds = computed(() => (detail.value?.transactions || []).filter(t => t.transaction_type === 'refund'))
const methodText = computed(() => {
  const r = payment.value?.receipt || {}
  if (r.card_last4) return `${r.card_brand ? r.card_brand.charAt(0).toUpperCase() + r.card_brand.slice(1) : 'Card'} •••• ${r.card_last4}`
  const m = detail.value?.payment_method
  return m ? (METHOD_LABELS[m] || m) : (r.source_type || '—')
})

/* What PayMongo says about the payment and its refunds (2026-10-19): an
   invoice paid through PayMongo is refunded through PayMongo and only turns
   Refunded once PayMongo reports the refund succeeded. */
const PM_REFUND_LABELS = { succeeded: 'Succeeded', failed: 'Failed', pending: 'Processing', processing: 'Processing', refunding: 'Waiting for the client to claim it' }
const PM_REFUND_PILLS = { succeeded: 'green', failed: 'red', pending: 'gold', processing: 'gold', refunding: 'gold' }
const pm = ref(null)
const pmError = ref('')
const pmLoading = ref(false)
const unix = t => (typeof t === 'number' ? new Date(t * 1000).toISOString() : t)

async function checkPayMongo() {
  const inv = selected.value
  if (!inv) return
  pmLoading.value = true
  pmError.value = ''
  try {
    const res = await get(`/admin/invoices/${inv.id}/paymongo/`)
    if (selected.value?.id !== inv.id) return
    pm.value = res
    if (res.invoice_status && res.invoice_status !== inv.status) await afterStatusChange(inv)
  } catch (e) {
    if (selected.value?.id === inv.id) pmError.value = apiError(e, 'Could not reach PayMongo. Please try again.')
  } finally {
    pmLoading.value = false
  }
}

async function afterStatusChange(inv) {
  await loadInvoices()
  const fresh = invoices.value.find(i => i.id === inv.id)
  if (fresh && selected.value?.id === inv.id) {
    selected.value = fresh
    detail.value = await get(`/admin/invoices/${inv.id}/`).catch(() => detail.value)
  }
}

/* refunds */
const refundsDue = computed(() => invoices.value.filter(i => i.status === 'refund_pending'))
const refundRefs = reactive({})
const refundBusy = ref(null)
const refundError = ref('')
const refundConfirm = ref(null)
const refundNotes = reactive({})

async function refundViaPayMongo(inv) {
  refundBusy.value = inv.id
  refundError.value = ''
  try {
    const res = await post(`/admin/invoices/${inv.id}/refund/`)
    refundConfirm.value = null
    const last = res.refunds?.[res.refunds.length - 1]
    if (res.invoice_status === 'refunded') {
      flash(`${invNo(inv)} refunded through PayMongo${last ? ' (' + last.id + ')' : ''} — ${inv.client_name} was notified.`)
    } else if (last?.status === 'failed') {
      refundNotes[inv.id] = { tone: 'bad', text: `PayMongo refused it: refund ${last.id} failed.${res.source_type === 'qrph' && res.livemode === false ? ' Test mode can\'t complete QR Ph refunds.' : ''}` }
    } else {
      refundNotes[inv.id] = { tone: 'wait', text: `Sent to PayMongo (${last?.id || 'refund'}) — it turns Refunded once PayMongo confirms.` }
    }
    if (selected.value?.id === inv.id) pm.value = res
    await afterStatusChange(inv)
  } catch (e) {
    const msg = apiError(e, 'Could not send the refund to PayMongo. Please try again.')
    if (selected.value?.id === inv.id) pmError.value = msg
    else refundError.value = msg
  } finally {
    refundBusy.value = null
  }
}
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
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.mono { font-variant-numeric: tabular-nums; }
.refund-row { flex-wrap: wrap; }
.detail { max-width: 560px; }
.detail-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.head-right { display: flex; align-items: center; gap: 6px; }
.close-btn { background: none; border: none; color: #8a9a8a; cursor: pointer; padding: 4px; }
.sub { display: block; font-size: 0.76rem; font-weight: 400; color: #8a9a8a; margin-top: 2px; }
.lines { border: 1px solid #eceeec; border-radius: 10px; padding: 4px 14px 10px; }
.line { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; font-size: 0.86rem; color: #2a3a2a; }
.line + .line { border-top: 1px solid #f0f2f0; }
.line > span:last-child { font-variant-numeric: tabular-nums; white-space: nowrap; }
.line.total { font-weight: 700; color: #1a3a1a; }
.receipt { border: 1px dashed #c7d6ca; background: #fafcfa; border-radius: 10px; padding: 14px; }
.receipt-top { display: flex; align-items: center; gap: 10px; color: #2e7d32; padding-bottom: 12px; border-bottom: 1px dashed #d8e2da; }
.receipt-amount { font-size: 1.15rem; font-weight: 700; color: #1a3a1a; margin: 0; font-variant-numeric: tabular-nums; }
.test-pill { margin-left: auto; }
.receipt-rows { margin: 0; }
.receipt-rows > div { display: flex; justify-content: space-between; gap: 16px; padding: 7px 0; font-size: 0.83rem; }
.receipt-rows > div + div { border-top: 1px solid #eef1ee; }
.receipt-rows dt { color: #8a9a8a; font-weight: 500; flex-shrink: 0; }
.receipt-rows dd { margin: 0; color: #1a3a1a; text-align: right; overflow-wrap: anywhere; }
@media (max-width: 640px) {
  .detail .nm-dl { grid-template-columns: 1fr; }
  .detail .nm-dl > div:nth-child(2) { border-top: 1px solid #f0f2f0; padding-top: 11px; }
}
.refund-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.refund-actions .nm-input { width: 240px; max-width: 100%; }
.refund-state { flex-basis: 100%; margin: 0; font-size: 0.8rem; color: #4a5a4a; }
.refund-state.bad { color: #a12525; }
.refund-state.wait { color: #8a6a10; }
.refund-state.muted { color: #8a9a8a; }
.pm-box { margin-top: 16px; padding: 12px 14px; border: 1px solid #eceeec; border-radius: 12px; background: #fafbfa; }
.pm-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.pm-line { margin: 10px 0 0; font-size: 0.84rem; color: #2a3a2a; overflow-wrap: anywhere; }
.pm-box .line .sub { display: block; font-size: 0.74rem; color: #8a9a8a; }
@media (max-width: 640px) {
  .refund-actions { width: 100%; }
  .refund-actions > * { width: 100% !important; }
}
</style>
