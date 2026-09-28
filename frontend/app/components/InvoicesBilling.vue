<template>
  <div class="billing-page">
    <div class="page-header">
      <h1 class="page-title">Billing &amp; Invoices</h1>
      <p class="page-sub">View and pay for your consultations.</p>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="paidNotice" class="paid-notice"><CheckCircle2 :size="16" /> {{ paidNotice }}</p>

    <div v-if="unpaidTotal > 0" class="unpaid-alert">
      <AlertCircle :size="18" />
      <span>You have <strong>{{ unpaidCount }} unpaid invoice{{ unpaidCount === 1 ? '' : 's' }}</strong> totaling ₱{{ unpaidTotal.toFixed(2) }}. Please settle {{ unpaidCount === 1 ? 'it' : 'them' }} to keep your upcoming appointments confirmed.</span>
    </div>

    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="invoices.length">
      <div class="table-wrap">
        <table class="invoice-table">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>RND</th>
              <th>Date</th>
              <th>Amount</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="inv in invoices" :key="inv.id">
              <td class="invoice-id">INV-{{ String(inv.id).padStart(4, '0') }}</td>
              <td>{{ inv.appointment ? `RND ${inv.appointment.relationship.rnd.first_name} ${inv.appointment.relationship.rnd.last_name}` : '—' }}</td>
              <td>{{ formatDate(inv.created_at) }}</td>
              <td class="amount">₱{{ Number(inv.amount).toFixed(2) }}</td>
              <td><span class="status-pill" :class="statusClass(inv.status)">{{ statusLabel(inv.status) }}</span></td>
              <td class="action-cell">
                <button
                  v-if="inv.status === 'unpaid'"
                  class="pay-btn"
                  type="button"
                  :disabled="payingId === inv.id"
                  @click="payInvoice(inv)"
                >
                  {{ payingId === inv.id ? 'Loading…' : 'Pay Now' }}
                </button>
                <span v-else-if="inv.status === 'paid'" class="paid-note">Paid {{ formatDate(inv.paid_at) }}</span>
                <span v-else class="muted-note">—</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-else class="empty-state">
      <div class="empty-icon"><Receipt :size="28" /></div>
      <p class="empty-title">No invoices yet</p>
      <p class="empty-desc">Invoices appear here after a consultation is marked completed by your RND.</p>
    </div>
  </div>
</template>

<script setup>
import { AlertCircle, CheckCircle2, Receipt } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Billing' })

const { get, post } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const invoices = ref([])
const payingId = ref(null)

const unpaidInvoices = computed(() => invoices.value.filter(i => i.status === 'unpaid'))
const unpaidCount = computed(() => unpaidInvoices.value.length)
const unpaidTotal = computed(() => unpaidInvoices.value.reduce((sum, i) => sum + Number(i.amount), 0))

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function statusLabel(status) {
  return { unpaid: 'Unpaid', paid: 'Paid', cancelled: 'Cancelled', refunded: 'Refunded' }[status] || status
}
function statusClass(status) {
  return { unpaid: 'warning', paid: 'success', cancelled: 'danger', refunded: 'neutral' }[status] || ''
}

// Checks unpaid PayMongo invoices directly with PayMongo first, so a payment
// still shows as paid even if its webhook never reached us. Best-effort:
// the invoice list still loads if the check fails.
async function loadInvoices({ quiet = false } = {}) {
  if (!quiet) isLoading.value = true
  errorMessage.value = ''
  try {
    await post('/client/invoices/sync/').catch(() => null)
    invoices.value = await get('/client/invoices/')
  } catch {
    errorMessage.value = 'Could not load your invoices. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

// While the PayMongo checkout popup is open, ask PayMongo (via our sync
// endpoint) whether this invoice is paid every few seconds. Payment Links
// can't redirect after payment, so once it's paid we close the popup
// ourselves — allowed because this page opened it. Also stops if the client
// closes the popup, or after 30 minutes (the QR code's lifetime).
const CHECK_EVERY_MS = 4000
const MAX_WATCH_MS = 30 * 60 * 1000
let checkoutWatch = null

function stopWatchingCheckout() {
  if (checkoutWatch) clearInterval(checkoutWatch)
  checkoutWatch = null
}

function watchCheckout(popup, invoiceId) {
  stopWatchingCheckout()
  const startedAt = Date.now()
  let checking = false
  checkoutWatch = setInterval(async () => {
    if (popup.closed || Date.now() - startedAt > MAX_WATCH_MS) {
      stopWatchingCheckout()
      loadInvoices({ quiet: true })
      return
    }
    if (checking) return
    checking = true
    try {
      // Check the invoice's actual status, not just whether this sync call
      // flipped it — the webhook may have marked it paid first.
      await post('/client/invoices/sync/').catch(() => null)
      const latest = await get('/client/invoices/')
      if (latest.find(i => i.id === invoiceId)?.status === 'paid') {
        stopWatchingCheckout()
        popup.close()
        invoices.value = latest
        paidNotice.value = `Payment received — INV-${String(invoiceId).padStart(4, '0')} is now paid.`
      }
    } catch {
      // Transient — try again on the next tick.
    } finally {
      checking = false
    }
  }, CHECK_EVERY_MS)
}

const paidNotice = ref('')

// Returning to this tab after paying in the PayMongo checkout re-checks.
function onVisible() {
  if (document.visibilityState === 'visible' && unpaidCount.value) loadInvoices({ quiet: true })
}

async function payInvoice(invoice) {
  payingId.value = invoice.id
  errorMessage.value = ''

  // Popups must be opened synchronously within the click handler or browsers
  // block them — open a blank window first, then redirect it once the
  // payment link comes back from the API.
  const width = 480
  const height = 720
  const left = window.screenX + (window.outerWidth - width) / 2
  const top = window.screenY + (window.outerHeight - height) / 2
  const popup = window.open(
    '',
    'paymongo-checkout',
    `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
  )

  try {
    const result = await post(`/client/invoices/${invoice.id}/pay/`)
    if (result.payment_url) {
      if (popup) {
        popup.location.href = result.payment_url
        watchCheckout(popup, invoice.id)
      } else {
        window.location.href = result.payment_url
      }
    } else if (popup) {
      popup.close()
    }
  } catch (error) {
    errorMessage.value = error?.data?.detail || 'Could not start payment. Please try again.'
    if (popup) popup.close()
  } finally {
    payingId.value = null
  }
}

onMounted(() => {
  loadInvoices()
  document.addEventListener('visibilitychange', onVisible)
})
onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVisible)
  stopWatchingCheckout()
})
</script>

<style scoped>
* { box-sizing: border-box; }

.billing-page { font-family: 'Inter', sans-serif; }

.page-header { margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.paid-notice {
  display: flex; align-items: center; gap: 8px;
  background: #e3f3ea; border: 1px solid #b8dcc6; color: #1f8f5c;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; font-weight: 600; margin: 0 0 16px;
}
.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}

.unpaid-alert {
  display: flex; align-items: flex-start; gap: 10px;
  background: #faead0; color: #8a6a1a; border-radius: 10px; padding: 14px 16px;
  font-size: 0.86rem; margin-bottom: 20px;
}
.unpaid-alert strong { color: #6a4a00; }

.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.table-wrap { background: #fff; border-radius: 12px; border: 1px solid #eceeec; overflow: hidden; overflow-x: auto; }
.invoice-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
.invoice-table th {
  text-align: left; font-size: 0.72rem; letter-spacing: 0.04em; color: #8a9a8a;
  padding: 14px 18px; border-bottom: 1px solid #eceeec; font-weight: 700;
}
.invoice-table td { padding: 14px 18px; border-bottom: 1px solid #f4f5f2; color: #4a5a4a; }
.invoice-table tr:last-child td { border-bottom: none; }
.invoice-id { font-weight: 700; color: #1a3a1a; }
.amount { font-weight: 700; color: #1a3a1a; }

.status-pill {
  font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap;
}
.status-pill.warning { background: #faead0; color: #b8860b; }
.status-pill.success { background: #e6efe0; color: #3a6b3a; }
.status-pill.danger { background: #fdecec; color: #a12525; }
.status-pill.neutral { background: #eceeec; color: #7a8a7a; }

.action-cell { text-align: right; }
.pay-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 8px 16px; font-weight: 700; font-size: 0.82rem; cursor: pointer; white-space: nowrap;
}
.pay-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.paid-note, .muted-note { font-size: 0.78rem; color: #9aaa9a; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
</style>
