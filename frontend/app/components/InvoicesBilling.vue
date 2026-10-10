<template>
  <div class="billing-page">
    <div class="page-header">
      <!-- <h1 class="page-title">Billing &amp; Invoices</h1> -->
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
                <span v-else-if="inv.status === 'paid'" class="paid-note">Paid {{ formatDate(inv.paid_at) }}{{ inv.payment_method ? ` · via ${PAYMENT_METHOD_LABELS[inv.payment_method] || inv.payment_method}` : '' }}</span>
                <span v-else-if="inv.status === 'refund_pending'" class="muted-note">Appointment cancelled — refund being processed</span>
                <span v-else-if="inv.status === 'refunded'" class="muted-note">Refunded</span>
                <span v-else-if="inv.status === 'cancelled'" class="muted-note">Appointment cancelled — nothing to pay</span>
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
      <p class="empty-desc">An invoice appears here when your RND confirms a booking. Pay it before the consultation to start it.</p>
    </div>
  </div>
</template>

<script setup>
import { AlertCircle, CheckCircle2, Receipt } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Billing' })

const { get, post } = useApi()
const PAYMENT_METHOD_LABELS = { card: 'Card', gcash: 'GCash', maya: 'Maya', qrph: 'QR Ph', bank_transfer: 'Bank Transfer', cash: 'Cash', other: 'Other' }

const isLoading = ref(true)
const errorMessage = ref('')
const invoices = ref([])

const unpaidInvoices = computed(() => invoices.value.filter(i => i.status === 'unpaid'))
const unpaidCount = computed(() => unpaidInvoices.value.length)
const unpaidTotal = computed(() => unpaidInvoices.value.reduce((sum, i) => sum + Number(i.amount), 0))

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// cancelled = voided (its appointment was cancelled or not paid in time);
// refund_pending = a paid appointment was cancelled and is being refunded.
function statusLabel(status) {
  return { unpaid: 'Unpaid', paid: 'Paid', cancelled: 'Voided', refund_pending: 'Refund pending', refunded: 'Refunded' }[status] || status
}
function statusClass(status) {
  return { unpaid: 'warning', paid: 'success', cancelled: 'neutral', refund_pending: 'warning', refunded: 'neutral' }[status] || ''
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

const paidNotice = ref('')

// Returning to this tab after paying in the PayMongo checkout re-checks.
function onVisible() {
  if (document.visibilityState === 'visible' && unpaidCount.value) loadInvoices({ quiet: true })
}

const { pay, payingId, payError } = usePayInvoice()
watch(payError, (msg) => { if (msg) errorMessage.value = msg })

function payInvoice(invoice) {
  errorMessage.value = ''
  pay(invoice.id, {
    onPaid(latest) {
      invoices.value = latest
      paidNotice.value = `Payment received — INV-${String(invoice.id).padStart(4, '0')} is now paid.`
    },
    onClosed() {
      loadInvoices({ quiet: true })
    },
  })
}

onMounted(() => {
  loadInvoices()
  document.addEventListener('visibilitychange', onVisible)
})
onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVisible)
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
