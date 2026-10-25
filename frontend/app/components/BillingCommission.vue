<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- THE MONEY AT A GLANCE: one divided panel -->
    <div class="nm-panel glance">
      <div class="fig">
        <strong>{{ peso(totals.gross) }}</strong>
        <span class="fig-label">Collected from clients</span>
        <span class="fig-note">{{ paid.length }} paid consultation{{ paid.length === 1 ? '' : 's' }}, all time</span>
      </div>
      <div class="fig">
        <strong>{{ peso(totals.commission) }}</strong>
        <span class="fig-label">Platform commission</span>
        <span class="fig-note">Current rate {{ currentRate }}%</span>
      </div>
      <div class="fig">
        <strong>{{ peso(totals.net) }}</strong>
        <span class="fig-label">RNDs' share</span>
        <NuxtLink to="/payouts" class="nm-btn-soft nm-btn-sm fig-btn">Manage payouts</NuxtLink>
      </div>
      <button type="button" class="fig" @click="tab = 'refunds'">
        <strong :class="{ warn: refundsDue.length }">{{ refundsDue.length }}</strong>
        <span class="fig-label">Refunds to send</span>
        <span class="fig-note" :class="{ warn: refundsDue.length }">{{ refundsDue.length ? `${peso(refundsDueTotal)} owed to clients` : 'None right now' }}</span>
      </button>
    </div>

    <div class="nm-toolbar">
      <div class="nm-tabs">
        <button type="button" class="nm-tab" :class="{ active: tab === 'invoices' }" @click="tab = 'invoices'">Invoices <span class="nm-count">{{ invoices.length }}</span></button>
        <button type="button" class="nm-tab" :class="{ active: tab === 'refunds' }" @click="tab = 'refunds'">Refunds <span class="nm-count">{{ refundsDue.length }}</span></button>
        <button type="button" class="nm-tab" :class="{ active: tab === 'commission' }" @click="tab = 'commission'">Commission</button>
      </div>
      <div v-if="tab === 'invoices'" class="bill-tools">
        <select v-model="statusFilter" class="nm-select" aria-label="Filter by status">
          <option value="">Any status</option>
          <option v-for="(label, key) in STATUS_LABELS" :key="key" :value="key">{{ label }}</option>
        </select>
        <div class="nm-search">
          <Search :size="15" aria-hidden="true" />
          <input v-model="search" type="search" placeholder="Search client, RND or INV no." />
        </div>
      </div>
    </div>

    <!-- INVOICES: a ledger, money lined up on the right -->
    <div v-if="tab === 'invoices'" class="nm-panel">
      <div class="nm-panel-head">
        <div>
          <h2 class="nm-panel-title">Invoices</h2>
          <p class="nm-panel-sub">Issued when an RND confirms a booking. Clients pay before the consultation.</p>
        </div>
        <span class="nm-muted ledger-count">{{ filteredInvoices.length }} invoice{{ filteredInvoices.length === 1 ? '' : 's' }}</span>
      </div>
      <p v-if="loading" class="nm-muted">Loading invoices…</p>
      <div v-else-if="!filteredInvoices.length" class="nm-empty">
        <Receipt :size="28" aria-hidden="true" />
        <p>{{ invoices.length ? 'No invoices match these filters.' : 'No invoices yet.' }}</p>
      </div>
      <div v-else class="nm-table-wrap ledger-scroll">
        <table class="nm-table stack ledger">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Client and RND</th>
              <th>Paid with</th>
              <th class="nm-num">Fee</th>
              <th class="nm-num">Commission</th>
              <th class="nm-num">RND's share</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="inv in pagedInvoices" :key="inv.id" class="clickable" tabindex="0"
              :aria-label="`View ${invNo(inv)} details`" @click="openInvoice(inv)" @keydown.enter="openInvoice(inv)"
            >
              <td data-label="Invoice">
                <strong class="mono">{{ invNo(inv) }}</strong>
                <span class="cell-sub">{{ shortDate(inv.created_at) }}</span>
              </td>
              <td data-label="Client and RND">
                {{ inv.client_name }}
                <span class="cell-sub">with RND {{ inv.rnd_name }}</span>
              </td>
              <td data-label="Paid with">{{ inv.payment_method ? (METHOD_LABELS[inv.payment_method] || inv.payment_method) : '—' }}</td>
              <td data-label="Fee" class="nm-num mono">{{ peso(inv.amount) }}</td>
              <td data-label="Commission" class="nm-num mono">{{ peso(inv.commission_amt) }} <span class="pct">{{ Number(inv.commission_pct) }}%</span></td>
              <td data-label="RND's share" class="nm-num mono">{{ peso(inv.net) }}</td>
              <td data-label="Status"><span class="nm-pill" :class="STATUS_PILLS[inv.status] || 'muted'">{{ STATUS_LABELS[inv.status] || inv.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <ListPager v-model:page="page" :pages="pages" />
    </div>

    <!-- REFUNDS -->
    <div v-else-if="tab === 'refunds'" class="nm-panel">
      <div class="nm-panel-head">
        <div>
          <h2 class="nm-panel-title">Refunds to send</h2>
          <p class="nm-panel-sub">These consultations were paid, then cancelled. Send each one back. The client is notified once it's refunded.</p>
        </div>
      </div>
      <p v-if="refundError" class="nm-error">{{ refundError }}</p>
      <div v-if="!refundsDue.length" class="nm-empty">
        <CheckCircle2 :size="28" aria-hidden="true" />
        <p>No refunds waiting.</p>
      </div>
      <div v-for="inv in refundsDue" :key="inv.id" class="refund">
        <div class="refund-amount">
          <strong class="mono">{{ peso(inv.amount) }}</strong>
          <span>{{ inv.payment_method ? (METHOD_LABELS[inv.payment_method] || inv.payment_method) : 'Not through PayMongo' }}</span>
        </div>
        <div class="refund-main">
          <p class="nm-row-title">Back to {{ inv.client_name }}</p>
          <p class="nm-row-sub">
            <button type="button" class="nm-text-link mono" @click="openInvoice(inv)">{{ invNo(inv) }}</button>, consultation with RND {{ inv.rnd_name }}<template v-if="inv.paid_at">, paid {{ shortDate(inv.paid_at) }}</template>
          </p>
          <p v-if="refundNotes[inv.id]" class="refund-state" :class="refundNotes[inv.id].tone">{{ refundNotes[inv.id].text }}</p>
          <p v-if="!inv.paymongo_payment_id" class="refund-state">Not paid through PayMongo. Return the money another way, then mark it refunded.</p>
        </div>
        <div class="refund-actions">
          <button v-if="inv.paymongo_payment_id" type="button" class="nm-btn-dark" @click="askRefund(inv)">Refund through PayMongo</button>
          <template v-else>
            <input v-model="refundRefs[inv.id]" class="nm-input" maxlength="100" placeholder="Refund reference (optional)" aria-label="Refund reference" />
            <button type="button" class="nm-btn-dark" :disabled="refundBusy === inv.id" @click="markRefunded(inv)">
              {{ refundBusy === inv.id ? 'Saving…' : 'Mark as refunded' }}
            </button>
          </template>
        </div>
      </div>
    </div>

    <!-- COMMISSION -->
    <div v-else class="nm-panel commission">
      <div class="com-form">
        <h2 class="nm-panel-title">Platform commission</h2>
        <p class="nm-panel-sub">NutriMatch's share of each consultation fee. The RND receives the rest.</p>
        <label class="nm-label" for="commission" style="margin-top: 18px">Commission rate (%)</label>
        <div class="com-row">
          <input id="commission" v-model="commissionRate" class="nm-input" type="number" min="0" max="50" step="0.01" :disabled="!settingsLoaded" />
          <button type="button" class="nm-btn-dark" :disabled="saving || !settingsLoaded || commissionRate === currentRate" @click="saveCommission">
            {{ saving ? 'Saving…' : 'Save rate' }}
          </button>
        </div>
        <p v-if="commissionError" class="nm-field-error">{{ commissionError }}</p>
        <p v-else class="nm-hint">Between 0% and 50%.</p>
      </div>

      <!-- the split of one consultation, live as the rate changes -->
      <div class="split">
        <p class="split-title">On a {{ peso(800) }} consultation</p>
        <template v-if="split">
          <div class="split-bar" role="img" :aria-label="`NutriMatch keeps ${peso(split.cut)}, the RND gets ${peso(split.rest)}`">
            <span class="split-ours" :style="{ width: `${split.pct}%` }"></span>
          </div>
          <div class="split-legend">
            <span><i class="key ours"></i> NutriMatch keeps <strong class="mono">{{ peso(split.cut) }}</strong></span>
            <span><i class="key theirs"></i> The RND gets <strong class="mono">{{ peso(split.rest) }}</strong></span>
          </div>
        </template>
        <p v-else class="nm-hint">Enter a rate between 0% and 50% to see the split.</p>
        <p class="nm-note plain-note split-note">
          Each invoice keeps the rate it was issued with. A new rate only applies to bookings confirmed after you save it, so RNDs' earnings on existing invoices never change.
          Every change is recorded in the audit log with the old and new rate.
        </p>
      </div>
    </div>

    <!-- INVOICE DETAIL + RECEIPT -->
    <div v-if="selected" class="nm-modal-overlay" @click.self="closeInvoice">
      <div class="nm-modal detail" role="dialog" aria-modal="true" aria-labelledby="inv-title">
        <div class="detail-head nm-modal-head">
          <div>
            <h3 id="inv-title" class="nm-modal-title mono" style="margin: 0">{{ invNo(selected) }}</h3>
            <p class="nm-panel-sub">Issued {{ dateTime(selected.created_at) }}</p>
          </div>
          <div class="head-right">
            <span class="nm-pill" :class="STATUS_PILLS[selected.status] || 'muted'">{{ STATUS_LABELS[selected.status] || selected.status }}</span>
            <button type="button" class="nm-modal-x" aria-label="Close" @click="closeInvoice"><X :size="18" aria-hidden="true" /></button>
          </div>
        </div>

        <p v-if="detailError" class="nm-error" style="margin-top: 14px">{{ detailError }}</p>
        <p v-else-if="!detail" class="nm-muted" style="margin-top: 14px">Loading invoice…</p>

        <template v-else>
          <h4 class="nm-section-title">Consultation</h4>
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
                <dd>{{ dateTime(detail.appointment.scheduled_at) }}<span class="sub">{{ detail.appointment.duration_minutes || 60 }} min, {{ (MODE_LABELS[detail.appointment.type] || detail.appointment.type).toLowerCase() }}</span></dd>
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

          <h4 class="nm-section-title">Amount</h4>
          <div class="lines">
            <div class="line"><span>Consultation fee</span><span>{{ peso(detail.amount) }}</span></div>
            <div class="line"><span>Platform commission ({{ Number(detail.commission_pct) }}%)</span><span>− {{ peso(detail.commission_amt) }}</span></div>
            <div class="line total"><span>RND's share</span><span>{{ peso(detail.net) }}</span></div>
            <p class="nm-hint">{{ detail.payout ? 'Paid out to the RND in a monthly payout.' : 'Not paid out to the RND yet.' }}</p>
          </div>

          <h4 class="nm-section-title">Payment receipt</h4>
          <div v-if="payment" class="receipt">
            <div class="receipt-top">
              <CheckCircle2 :size="20" aria-hidden="true" />
              <div>
                <p class="receipt-amount">{{ peso(payment.receipt.amount || payment.amount) }}</p>
                <p class="nm-hint" style="margin: 0">Paid by {{ payment.receipt.payer_name || detail.client.name }}, {{ dateTime(payment.receipt.paid_at || detail.paid_at || payment.processed_at) }}</p>
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
            <Receipt :size="24" aria-hidden="true" />
            <p>{{ selected.status === 'unpaid' ? 'The client hasn\'t paid this invoice yet.' : 'No payment was made on this invoice.' }}</p>
          </div>

          <div v-if="payment?.receipt?.payment_id" class="pm-box">
            <div class="pm-head">
              <h4 class="nm-section-title" style="margin: 0">In PayMongo</h4>
              <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="pmLoading" @click="checkPayMongo">{{ pmLoading ? 'Checking…' : 'Check with PayMongo' }}</button>
            </div>
            <p v-if="pmError" class="nm-error" style="margin: 8px 0 0">{{ pmError }}</p>
            <template v-else-if="pm">
              <p class="pm-line">
                Payment <span class="mono">{{ pm.payment_id }}</span>:
                <strong>{{ pm.refunded ? 'Refunded' : pm.in_progress ? 'Refund in progress' : 'Paid' }}</strong>
                <span v-if="pm.livemode === false" class="nm-pill gold" style="margin-left: 6px">Test mode</span>
              </p>
              <p v-if="!pm.refunds.length" class="nm-hint" style="margin: 4px 0 0">No refund sent to PayMongo yet.</p>
              <div v-for="r in pm.refunds" :key="r.id" class="line">
                <span><span class="mono">{{ r.id }}</span><span class="sub">{{ dateTime(unix(r.refunded_at || r.created_at)) }}</span></span>
                <span>{{ peso(r.amount) }} <span class="nm-pill" :class="PM_REFUND_PILLS[r.status] || 'muted'">{{ PM_REFUND_LABELS[r.status] || r.status }}</span></span>
              </div>
              <p v-if="pm.refunds.some(r => r.status === 'failed') && pm.source_type === 'qrph' && pm.livemode === false" class="nm-hint" style="margin: 6px 0 0">
                PayMongo's test mode can't complete QR Ph refunds. GCash, Maya and card refunds work in test mode.
              </p>
            </template>
          </div>

          <template v-if="refunds.length">
            <h4 class="nm-section-title">Refunds</h4>
            <div v-for="r in refunds" :key="r.id" class="line">
              <span>Refunded {{ dateTime(r.processed_at || r.created_at) }}<span v-if="r.reference" class="sub mono">Ref {{ r.reference }}</span></span>
              <span>{{ peso(r.amount) }}</span>
            </div>
          </template>
        </template>

        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="closeInvoice">Close</button>
          <button v-if="selected.status === 'refund_pending' && selected.paymongo_payment_id" type="button" class="nm-btn-dark" @click="askRefund(selected)">Refund through PayMongo</button>
        </div>
      </div>
    </div>

    <!-- REFUND CONFIRMATION: money leaves for good, so the button waits 3 seconds -->
    <div v-if="refundConfirm" class="nm-modal-overlay" style="z-index: 310" @click.self="refundBusy ? null : closeRefund()">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="refund-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="refundBusy ? null : closeRefund()"><X :size="18" aria-hidden="true" /></button>
        <h3 id="refund-title" class="nm-modal-title">Send {{ peso(refundConfirm.amount) }} back to {{ refundConfirm.client_name }}?</h3>
        <p class="nm-modal-text">
          PayMongo returns the full amount of {{ invNo(refundConfirm) }}<template v-if="refundConfirm.payment_method"> to the client's {{ METHOD_LABELS[refundConfirm.payment_method] || refundConfirm.payment_method }}</template>.
          It can't be undone. The invoice turns Refunded once PayMongo confirms, and the client is notified.
        </p>
        <p v-if="refundConfirmError" class="nm-field-error">{{ refundConfirmError }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" :disabled="!!refundBusy" @click="closeRefund">Not now</button>
          <button type="button" class="nm-btn-dark" :disabled="!!refundBusy || lockLeft > 0" @click="refundViaPayMongo(refundConfirm)">
            {{ refundBusy ? 'Sending to PayMongo…' : lockLeft > 0 ? `Send refund (${lockLeft})` : 'Send refund' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { CheckCircle2, Receipt, Search, X } from 'lucide-vue-next'

const { get, patch, post } = useApi()
const route = useRoute()

const METHOD_LABELS = { card: 'Card', gcash: 'GCash', maya: 'Maya', qrph: 'QR Ph', bank_transfer: 'Bank transfer', cash: 'Cash', other: 'Other' }
// cancelled = voided (appointment cancelled / not paid in time).
const STATUS_LABELS = { unpaid: 'Awaiting payment', paid: 'Paid', refund_pending: 'Refund pending', refunded: 'Refunded', cancelled: 'Voided' }
// gold = someone still has to act (client pays, admin refunds); grey = settled
const STATUS_PILLS = { unpaid: 'gold', paid: 'green', refund_pending: 'gold', refunded: 'muted', cancelled: 'muted' }

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

async function loadInvoices({ quiet = false } = {}) {
  try {
    invoices.value = await get('/admin/invoices/')
  } catch {
    if (!quiet) error.value = 'Could not load billing data. Refresh the page to try again.'
  } finally {
    loading.value = false
  }
}
// payments and refunds show without a reload (the settings form is left alone)
useAutoRefresh(() => loadInvoices({ quiet: true }))

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
const { page, pages, paged: pagedInvoices } = usePager(filteredInvoices, { perPage: 20, resetOn: () => [search.value, statusFilter.value] })

/* invoice detail overlay: details + the client's payment receipt */
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
  try {
    const d = await get(`/admin/invoices/${inv.id}/`)
    if (selected.value?.id === inv.id) detail.value = d
    if (inv.paymongo_payment_id) checkPayMongo()
  } catch (e) {
    if (selected.value?.id === inv.id) detailError.value = apiError(e, 'Could not load this invoice. Try again.')
  }
}
function closeInvoice() { selected.value = null }
function onKey(e) {
  if (e.key !== 'Escape') return
  if (refundConfirm.value) { if (!refundBusy.value) closeRefund() } else if (selected.value) closeInvoice()
}

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
    if (selected.value?.id === inv.id) pmError.value = apiError(e, 'Could not reach PayMongo. Try again.')
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
const refundsDueTotal = computed(() => refundsDue.value.reduce((s, i) => s + Number(i.amount), 0))
const refundRefs = reactive({})
const refundBusy = ref(null)
const refundError = ref('')
const refundNotes = reactive({})
const refundConfirm = ref(null)
const refundConfirmError = ref('')
const lockLeft = ref(0)
let lockTimer
function askRefund(inv) {
  refundConfirm.value = inv
  refundConfirmError.value = ''
  lockLeft.value = 3
  clearInterval(lockTimer)
  lockTimer = setInterval(() => {
    lockLeft.value -= 1
    if (lockLeft.value <= 0) clearInterval(lockTimer)
  }, 1000)
}
function closeRefund() {
  clearInterval(lockTimer)
  refundConfirm.value = null
}

async function refundViaPayMongo(inv) {
  refundBusy.value = inv.id
  refundConfirmError.value = ''
  try {
    const res = await post(`/admin/invoices/${inv.id}/refund/`)
    closeRefund()
    const last = res.refunds?.[res.refunds.length - 1]
    if (res.invoice_status === 'refunded') {
      flash(`${invNo(inv)} refunded through PayMongo${last ? ` (${last.id})` : ''}. ${inv.client_name} was notified.`)
    } else if (last?.status === 'failed') {
      refundNotes[inv.id] = { tone: 'bad', text: `PayMongo refused it: refund ${last.id} failed.${res.source_type === 'qrph' && res.livemode === false ? ' Test mode can\'t complete QR Ph refunds.' : ''}` }
    } else {
      refundNotes[inv.id] = { tone: 'wait', text: `Sent to PayMongo (${last?.id || 'refund'}). It turns Refunded once PayMongo confirms.` }
    }
    if (selected.value?.id === inv.id) pm.value = res
    await afterStatusChange(inv)
  } catch (e) {
    refundConfirmError.value = apiError(e, 'Could not send the refund to PayMongo. Try again.')
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
    flash(`${invNo(inv)} marked as refunded. ${inv.client_name} was notified.`)
  } catch (e) {
    refundError.value = apiError(e, 'Could not update this refund. Try again.')
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
const split = computed(() => {
  if (commissionRate.value === '' || commissionRate.value === null) return null
  const pct = Number(commissionRate.value)
  if (Number.isNaN(pct) || pct < 0 || pct > 50) return null
  const cut = Math.round(800 * pct) / 100
  return { pct, cut, rest: 800 - cut }
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
    flash(`Saved. New bookings use ${currentRate.value}% commission.`)
  } catch (e) {
    commissionError.value = apiError(e, 'Could not save. Try again.')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadInvoices()
  loadSettings()
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  clearInterval(lockTimer)
})
</script>

<style scoped>
.mono { font-variant-numeric: tabular-nums; }

/* at a glance: one divided panel */
.glance { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); padding: 0; margin-bottom: 20px; overflow: hidden; }
.fig {
  display: flex; flex-direction: column; align-items: flex-start; gap: 2px; padding: 16px 18px; text-align: left; min-width: 0;
  background: #fff; border: 0; border-left: 1px solid #d9e3dc; font-family: inherit; color: #1a3a1a;
}
.fig:first-child { border-left: none; }
button.fig { cursor: pointer; }
button.fig:hover { background: #f7faf8; }
.fig:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.fig strong { font-family: 'Playfair Display', serif; font-size: 1.5rem; line-height: 1.2; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.fig strong.warn { color: #b8860b; }
.fig-label { font-size: 0.82rem; font-weight: 600; color: #4a5a4a; }
.fig-note { font-size: 0.75rem; color: #8a9a8a; line-height: 1.4; }
.fig-note.warn { color: #b8860b; font-weight: 600; }
.fig-btn { margin-top: 6px; }

.bill-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.bill-tools .nm-select { width: auto; min-width: 160px; }

/* the ledger */
.ledger-count { font-size: 0.8rem; }
/* the invoice list scrolls inside its panel; the column names stay on top */
@media (min-width: 641px) {
  .ledger-scroll { max-height: max(320px, min(560px, calc(100vh - 330px))); overflow-y: auto; overscroll-behavior: contain; scrollbar-width: thin; scrollbar-color: #c5d6ca transparent; }
  .ledger-scroll thead th { position: sticky; top: 0; z-index: 1; background: #fff; padding-top: 2px; box-shadow: 0 1px 0 #d9e3dc; }
}
.cell-sub { display: block; font-size: 0.76rem; color: #8a9a8a; margin-top: 2px; }
.pct { font-size: 0.74rem; color: #8a9a8a; margin-left: 2px; }

/* refunds: amount on the left like a cheque stub */
.refund { display: flex; align-items: center; gap: 16px; padding: 14px 0; border-top: 1px solid #edf1ee; flex-wrap: wrap; }
.refund:first-of-type { border-top: none; }
.refund-amount { display: flex; flex-direction: column; min-width: 120px; padding-right: 16px; border-right: 1px solid #d9e3dc; }
.refund-amount strong { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; }
.refund-amount span { font-size: 0.76rem; color: #6a7a6a; }
.refund-main { flex: 1; min-width: 220px; }
.refund-main .nm-text-link { background: none; border: 0; padding: 0; font: inherit; cursor: pointer; }
.refund-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.refund-actions .nm-input { width: 220px; max-width: 100%; }
.refund-state { margin: 6px 0 0; font-size: 0.8rem; color: #6a7a6a; }
.refund-state.bad { color: #a12525; }
.refund-state.wait { color: #8a6a10; }

/* commission: the form beside a live split of one consultation */
.commission { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr); gap: 28px; }
.com-row { display: flex; gap: 10px; align-items: center; }
.com-row .nm-input { max-width: 140px; }
.split { border-left: 1px solid #d9e3dc; padding-left: 28px; }
.split-title { margin: 0 0 12px; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.split-bar { height: 14px; border-radius: 999px; background: #9fcfb3; overflow: hidden; }
.split-ours { display: block; height: 100%; background: #0a4a37; border-radius: 999px 0 0 999px; transition: width 0.2s ease; }
.split-legend { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-top: 10px; font-size: 0.82rem; color: #4a5a4a; }
.key { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 4px; vertical-align: -1px; }
.key.ours { background: #0a4a37; }
.key.theirs { background: #9fcfb3; }
.split-note { margin: 18px 0 0; }
@media (prefers-reduced-motion: reduce) { .split-ours { transition: none; } }

/* invoice pop-up */
.detail { max-width: 560px; }
.detail-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.detail-head .nm-modal-x { position: static; float: none; margin: 0; }
.head-right { display: flex; align-items: center; gap: 8px; }
.detail .nm-section-title { font-family: inherit; }
.sub { display: block; font-size: 0.76rem; font-weight: 400; color: #8a9a8a; margin-top: 2px; }
.lines { border: 1px solid #d9e3dc; border-radius: 10px; padding: 4px 14px 10px; }
.line { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; font-size: 0.86rem; color: #2a3a2a; }
.line + .line { border-top: 1px solid #edf1ee; }
.line > span:last-child { font-variant-numeric: tabular-nums; white-space: nowrap; }
.line.total { font-weight: 700; color: #1a3a1a; }
.receipt { border: 1px dashed #c7d6ca; background: #fafcfa; border-radius: 10px; padding: 14px; }
.receipt-top { display: flex; align-items: center; gap: 10px; color: #1f8f5c; padding-bottom: 12px; border-bottom: 1px dashed #d8e2da; }
.receipt-amount { font-size: 1.15rem; font-weight: 700; color: #1a3a1a; margin: 0; font-variant-numeric: tabular-nums; }
.test-pill { margin-left: auto; }
.receipt-rows { margin: 0; }
.receipt-rows > div { display: flex; justify-content: space-between; gap: 16px; padding: 7px 0; font-size: 0.83rem; }
.receipt-rows > div + div { border-top: 1px solid #edf1ee; }
.receipt-rows dt { color: #8a9a8a; font-weight: 500; flex-shrink: 0; }
.receipt-rows dd { margin: 0; color: #1a3a1a; text-align: right; overflow-wrap: anywhere; }
.pm-box { margin-top: 16px; padding: 12px 14px; border: 1px solid #d9e3dc; border-radius: 12px; background: #f7faf8; }
.pm-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.pm-line { margin: 10px 0 0; font-size: 0.84rem; color: #2a3a2a; overflow-wrap: anywhere; }
.pm-box .line .sub { display: block; font-size: 0.74rem; color: #8a9a8a; }

@media (max-width: 900px) {
  .glance { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fig:nth-child(3) { border-left: none; }
  .fig:nth-child(n + 3) { border-top: 1px solid #d9e3dc; }
  .commission { grid-template-columns: minmax(0, 1fr); }
  .split { border-left: none; padding-left: 0; border-top: 1px solid #d9e3dc; padding-top: 20px; }
}
@media (max-width: 640px) {
  .bill-tools { width: 100%; }
  .bill-tools .nm-search { flex: 1 1 100%; order: -1; max-width: none; }
  .bill-tools .nm-select { flex: 1; }
  .fig { padding: 12px 14px; }
  .fig strong { font-size: 1.2rem; }
  .detail .nm-dl { grid-template-columns: 1fr; }
  .detail .nm-dl > div:nth-child(2) { border-top: 1px solid #edf1ee; padding-top: 11px; }
  .refund-amount { border-right: none; padding-right: 0; }
  .refund-actions { width: 100%; }
  .refund-actions > * { flex: 1; }
}
</style>
