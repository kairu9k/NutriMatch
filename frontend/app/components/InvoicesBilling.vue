<template>
  <div class="nm-page">
    <p class="nm-page-sub intro">Pay for your consultations and keep your receipts. Each invoice appears when your RND confirms a booking.</p>
    <p v-if="error" class="nm-error">{{ error }}</p>
    <p v-if="paidNotice" class="nm-success"><CheckCircle2 :size="15" /> {{ paidNotice }}</p>

    <!-- figures: one divided panel -->
    <div class="figs">
      <div class="fig">
        <p class="fig-label">Due now</p>
        <p class="fig-value">{{ peso(dueTotal) }}</p>
        <p class="fig-note" :class="{ warn: due.length }">{{ due.length ? `${due.length} invoice${due.length === 1 ? '' : 's'} to pay` : 'Nothing to pay' }}</p>
      </div>
      <div class="fig">
        <p class="fig-label">Paid in {{ thisYear }}</p>
        <p class="fig-value">{{ peso(paidThisYear) }}</p>
        <p class="fig-note">{{ paidCount }} consultation{{ paidCount === 1 ? '' : 's' }}</p>
      </div>
      <div class="fig">
        <p class="fig-label">Refunds in progress</p>
        <p class="fig-value">{{ peso(refundTotal) }}</p>
        <p class="fig-note">{{ refunding.length ? `Within ${REFUND_WINDOW}` : 'None' }}</p>
      </div>
      <div class="fig">
        <p class="fig-label">Next payment deadline</p>
        <p class="fig-value">{{ nextDeadline ? shortDate(nextDeadline) : '—' }}</p>
        <p class="fig-note">{{ nextDeadline ? phTime(nextDeadline) : 'No upcoming payments' }}</p>
      </div>
    </div>

    <!-- due -->
    <div v-if="due.length" class="nm-panel due-panel">
      <h2 class="nm-panel-title">Pay before your consultation</h2>
      <p class="nm-panel-sub">Unpaid consultations are cancelled automatically at their start time.</p>
      <div v-for="inv in due" :key="inv.id" class="due-row">
        <img v-if="inv.consultation.rnd.profile_photo" :src="inv.consultation.rnd.profile_photo" class="nm-avatar" alt="" />
        <span v-else class="nm-avatar">{{ nameInitials(inv.consultation.rnd.name) }}</span>
        <div class="due-main">
          <p class="nm-row-title">{{ inv.consultation.type_label }} with RND {{ inv.consultation.rnd.name }}</p>
          <p class="nm-row-sub">{{ invNo(inv) }}, {{ when(inv.consultation.scheduled_at) }}</p>
          <p class="deadline"><AlarmClock :size="13" aria-hidden="true" /> Pay by {{ when(inv.pay_by) }} <span class="left">({{ timeLeft(inv.pay_by) }})</span></p>
        </div>
        <div class="due-end">
          <p class="due-amount">{{ peso(inv.amount) }}</p>
          <button class="nm-btn-dark" :disabled="payingId === inv.id" @click="payInvoice(inv)">
            <CreditCard :size="15" /> {{ payingId === inv.id ? 'Opening…' : 'Pay now' }}
          </button>
          <p class="methods">GCash, Maya, card or QR Ph</p>
        </div>
      </div>
    </div>

    <!-- history -->
    <div class="nm-toolbar history-bar">
      <div class="nm-tabs">
        <button v-for="t in TABS" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" @click="tab = t.key">
          {{ t.label }}<span v-if="countOf(t.key)" class="nm-count"> {{ countOf(t.key) }}</span>
        </button>
      </div>
      <div class="nm-search">
        <Search :size="15" aria-hidden="true" />
        <input v-model="search" type="search" placeholder="Search by RND or invoice number" aria-label="Search invoices" />
      </div>
    </div>

    <div class="nm-panel">
      <p v-if="loading" class="nm-muted">Loading your invoices…</p>
      <div v-else-if="!invoices.length" class="nm-empty">
        <Receipt :size="28" />
        <p>No invoices yet.</p>
        <p class="nm-hint" style="margin-top: 4px">An invoice appears when your RND confirms a booking. Pay it before the consultation to join.</p>
      </div>
      <div v-else-if="!filtered.length" class="nm-empty"><p>No invoices match.</p></div>
      <div v-else class="nm-table-wrap">
        <table class="nm-table stack">
          <thead>
            <tr><th>Invoice</th><th>Consultation</th><th class="nm-num">Amount</th><th>Status</th><th></th></tr>
          </thead>
          <tbody>
            <tr v-for="inv in filtered" :key="inv.id" class="clickable" @click="open(inv)">
              <td data-label="Invoice"><strong>{{ invNo(inv) }}</strong><span class="nm-row-sub" style="display: block">Issued {{ shortDate(inv.created_at) }}</span></td>
              <td data-label="Consultation">
                {{ inv.consultation.type_label || 'Consultation' }} with RND {{ inv.consultation.rnd.name }}
                <span v-if="inv.consultation.scheduled_at" class="nm-row-sub" style="display: block">{{ when(inv.consultation.scheduled_at) }}</span>
              </td>
              <td data-label="Amount" class="nm-num">{{ peso(inv.amount) }}</td>
              <td data-label="Status">
                <span class="nm-pill" :class="STATUS[inv.status]?.pill">{{ STATUS[inv.status]?.label || inv.status }}</span>
                <span class="nm-row-sub" style="display: block">{{ statusDetail(inv) }}</span>
              </td>
              <td class="nm-num">
                <button v-if="inv.status === 'unpaid' && inv.pay_by" class="nm-btn-dark nm-btn-sm" :disabled="payingId === inv.id" @click.stop="payInvoice(inv)">Pay</button>
                <button v-else-if="inv.receipt" class="nm-btn-soft nm-btn-sm" @click.stop="open(inv)"><FileText :size="13" /> Receipt</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- receipt / details -->
    <div v-if="current" class="nm-modal-overlay" @click.self="current = null">
      <div class="nm-modal receipt-modal" role="dialog" aria-modal="true">
        <div class="rm-head">
          <div>
            <p class="nm-section-title" style="margin: 0 0 4px">{{ current.receipt ? 'Receipt' : 'Invoice' }}</p>
            <h3 class="nm-modal-title" style="margin: 0">{{ invNo(current) }}</h3>
          </div>
          <span class="nm-pill" :class="STATUS[current.status]?.pill">{{ STATUS[current.status]?.label }}</span>
          <button class="close-btn" aria-label="Close" @click="current = null"><X :size="18" /></button>
        </div>

        <dl class="nm-dl rm-dl">
          <div><dt>RND</dt><dd>{{ current.consultation.rnd.name }}</dd></div>
          <div><dt>Consultation</dt><dd>{{ current.consultation.type_label || '—' }}<template v-if="current.consultation.duration_minutes">, {{ current.consultation.duration_minutes }} min</template></dd></div>
          <div><dt>Scheduled</dt><dd>{{ current.consultation.scheduled_at ? when(current.consultation.scheduled_at) : '—' }}</dd></div>
          <div><dt>Issued</dt><dd>{{ when(current.created_at) }}</dd></div>
          <template v-if="current.receipt">
            <div><dt>Paid on</dt><dd>{{ when(current.receipt.paid_at) }}</dd></div>
            <div><dt>Paid via</dt><dd>{{ paidVia(current) }}</dd></div>
            <div v-if="current.receipt.reference" class="wide"><dt>Payment reference</dt><dd class="mono">{{ current.receipt.reference }}</dd></div>
          </template>
          <div v-else-if="current.pay_by" class="wide"><dt>Pay by</dt><dd>{{ when(current.pay_by) }}</dd></div>
        </dl>

        <!-- refund progress -->
        <div v-if="current.refund" class="refund">
          <p class="nm-section-title" style="margin: 0 0 10px">Refund</p>
          <ol class="steps">
            <li class="on"><span /> Paid, {{ shortDate(current.receipt?.paid_at) }}</li>
            <li class="on"><span /> Consultation cancelled<template v-if="current.refund.cancelled_at">, {{ shortDate(current.refund.cancelled_at) }}</template></li>
            <li :class="{ on: true, now: current.refund.status === 'refund_pending' }"><span /> Refund in progress</li>
            <li :class="{ on: current.refund.status === 'refunded' }"><span /> Refunded<template v-if="current.refund.refunded_at">, {{ shortDate(current.refund.refunded_at) }}</template></li>
          </ol>
          <p v-if="current.refund.status === 'refund_pending'" class="nm-hint">{{ refundMessage(Number(current.amount).toLocaleString('en-PH', { minimumFractionDigits: 2 }), current.payment_method) }}</p>
        </div>
        <p v-if="current.consultation.cancellation_reason && current.status !== 'paid'" class="nm-note plain-note" style="margin: 14px 0 0">{{ current.consultation.cancellation_reason }}</p>

        <div class="rm-total"><span>{{ current.receipt ? 'Total paid' : 'Amount' }}</span><strong>{{ peso(current.amount) }}</strong></div>

        <div class="nm-modal-actions">
          <template v-if="current.receipt">
            <button class="nm-btn-soft" :disabled="resending" @click="resend(current)"><Mail :size="14" /> {{ resending ? 'Sending…' : 'Resend receipt' }}</button>
            <button class="nm-btn-dark" @click="printReceipt(current)"><Printer :size="14" aria-hidden="true" /> Download or print</button>
          </template>
          <button v-else-if="current.status === 'unpaid' && current.pay_by" class="nm-btn-dark" :disabled="payingId === current.id" @click="payInvoice(current)"><CreditCard :size="14" /> Pay now</button>
        </div>
        <p v-if="current.receipt" class="nm-hint" style="text-align: right">The receipt was emailed to you when you paid. Resend it if you can't find it.</p>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import {
  AlarmClock, CheckCircle2, CreditCard, FileText, Mail, Printer, Receipt, Search, X,
} from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'dashboard', title: 'Billing' })

const { get, post } = useApi()
const { pay, payingId, payError } = usePayInvoice()
const now = useNow()

const STATUS = {
  unpaid: { label: 'Awaiting payment', pill: 'gold' },
  paid: { label: 'Paid', pill: 'green' },
  refund_pending: { label: 'Refund in progress', pill: 'red' },
  refunded: { label: 'Refunded', pill: 'blue' },
  cancelled: { label: 'Voided', pill: 'muted' },
}
const TABS = [
  { key: 'all', label: 'All' },
  { key: 'paid', label: 'Paid' },
  { key: 'refunds', label: 'Refunds' },
  { key: 'voided', label: 'Voided' },
]

const invoices = ref([])
const loading = ref(true)
const error = ref('')
const paidNotice = ref('')
const tab = ref('all')
const search = ref('')
const current = ref(null)
const resending = ref(false)
const toast = ref('')

async function load({ quiet = false } = {}) {
  if (!quiet) loading.value = true
  error.value = ''
  try {
    await post('/client/invoices/sync/').catch(() => null) // catches payments whose webhook was missed
    invoices.value = await get('/client/invoices/')
  } catch {
    error.value = 'Could not load your invoices. Please refresh the page.'
  } finally {
    loading.value = false
  }
}
function onVisible() {
  if (document.visibilityState === 'visible' && due.value.length) load({ quiet: true })
}
onMounted(() => {
  load()
  document.addEventListener('visibilitychange', onVisible)
})
onBeforeUnmount(() => document.removeEventListener('visibilitychange', onVisible))
watch(payError, (msg) => { if (msg) error.value = msg })

const due = computed(() => invoices.value.filter(i => i.status === 'unpaid' && i.pay_by)
  .sort((a, b) => new Date(a.pay_by) - new Date(b.pay_by)))
const dueTotal = computed(() => due.value.reduce((n, i) => n + Number(i.amount), 0))
const thisYear = new Date().getFullYear()
const paidList = computed(() => invoices.value.filter(i => i.status === 'paid'))
const paidCount = computed(() => paidList.value.filter(i => new Date(i.paid_at).getFullYear() === thisYear).length)
const paidThisYear = computed(() => paidList.value.filter(i => new Date(i.paid_at).getFullYear() === thisYear).reduce((n, i) => n + Number(i.amount), 0))
const refunding = computed(() => invoices.value.filter(i => i.status === 'refund_pending'))
const refundTotal = computed(() => refunding.value.reduce((n, i) => n + Number(i.amount), 0))
const nextDeadline = computed(() => due.value[0]?.pay_by || null)

function inTab(i, key) {
  if (key === 'paid') return i.status === 'paid'
  if (key === 'refunds') return ['refund_pending', 'refunded'].includes(i.status)
  if (key === 'voided') return i.status === 'cancelled'
  return true
}
const countOf = key => invoices.value.filter(i => inTab(i, key)).length
const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return invoices.value.filter(i => inTab(i, tab.value) && (!q || `${invNo(i)} ${i.consultation.rnd.name}`.toLowerCase().includes(q)))
})

function payInvoice(inv) {
  error.value = ''
  paidNotice.value = ''
  pay(inv.id, {
    onPaid(latest) {
      invoices.value = latest
      current.value = null
      paidNotice.value = `Payment received. ${invNo(inv)} is paid, and your receipt is on its way to your email.`
      load({ quiet: true })
    },
    onClosed() { load({ quiet: true }) },
  })
}
function open(inv) {
  current.value = inv
}
async function resend(inv) {
  resending.value = true
  try {
    const r = await post(`/client/invoices/${inv.id}/resend-receipt/`)
    flash(r.detail)
  } catch (e) {
    flash(apiError(e, 'Could not send the receipt. Please try again.'))
  } finally {
    resending.value = false
  }
}
function flash(text) {
  toast.value = text
  setTimeout(() => { toast.value = '' }, 3500)
}
function printReceipt(inv) {
  const ok = printDocument({
    title: 'Official receipt',
    number: invNo(inv),
    rows: [
      ['Billed to', `${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim() || '—'],
      ['RND', inv.consultation.rnd.name],
      ['Consultation', `${inv.consultation.type_label || 'Consultation'}${inv.consultation.scheduled_at ? ', ' + when(inv.consultation.scheduled_at) : ''}`],
      ['Paid on', when(inv.receipt.paid_at)],
      ['Paid via', paidVia(inv)],
      ...(inv.receipt.reference ? [['Payment reference', inv.receipt.reference]] : []),
      ['Status', STATUS[inv.status]?.label || inv.status],
    ],
    total: ['Total paid', peso(inv.amount)],
    note: inv.refund ? 'This consultation was cancelled and the payment is being refunded (or has been).' : 'Thank you for choosing NutriMatch.',
  })
  if (!ok) flash('Allow pop-ups for this site to print the receipt.')
}

const auth = useAuthStore()
const invNo = i => `INV-${String(i.id).padStart(4, '0')}`
const PH = { timeZone: 'Asia/Manila' }
function when(v) {
  return v ? new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—'
}
function phTime(v) {
  return new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
}
function timeLeft(v) {
  const ms = new Date(v) - now.value
  if (ms <= 0) return 'now'
  const h = Math.floor(ms / 3600000)
  if (h >= 48) return `${Math.floor(h / 24)} days left`
  if (h >= 1) return `${h} hour${h === 1 ? '' : 's'} left`
  return `${Math.max(1, Math.floor(ms / 60000))} minutes left`
}
function paidVia(inv) {
  const r = inv.receipt || {}
  if (r.card_last4) return `${(r.card_brand || 'Card').replace(/^./, c => c.toUpperCase())} •••• ${r.card_last4}`
  return r.method || 'PayMongo'
}
function statusDetail(inv) {
  if (inv.status === 'unpaid') return inv.pay_by ? `Pay by ${shortDate(inv.pay_by)}` : ''
  if (inv.status === 'paid') return `${shortDate(inv.paid_at)}${inv.payment_method_label ? ', ' + inv.payment_method_label : ''}`
  if (inv.status === 'refunded') return inv.refund?.refunded_at ? `Refunded ${shortDate(inv.refund.refunded_at)}` : ''
  if (inv.status === 'refund_pending') return 'Consultation cancelled'
  if (inv.status === 'cancelled') return 'Nothing to pay'
  return ''
}
function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}
</script>

<style scoped>
.intro { margin: 0 0 16px; }
.nm-success { display: flex; align-items: center; gap: 8px; }
/* figures: one divided panel */
.figs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-bottom: 18px; background: #fff; border: 1px solid #d9e3dc; border-radius: 14px; overflow: hidden; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.fig { padding: 16px 20px; border-left: 1px solid #d9e3dc; min-width: 0; }
.fig:first-child { border-left: none; }
.fig-label { font-size: 0.82rem; font-weight: 600; color: #4a5a4a; margin: 0; }
.fig-value { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1a3a1a; margin: 2px 0 0; font-variant-numeric: lining-nums; }
.fig-note { font-size: 0.78rem; color: #6a7a6a; margin: 2px 0 0; }
.fig-note.warn { color: #8a6400; font-weight: 600; }
/* payments still to make: the app's dashed green for "to do" */
.due-panel { margin-bottom: 20px; border: 1.5px dashed #3f9a6b; background: #fff; }
.due-row { display: flex; gap: 14px; align-items: center; padding: 16px 0 0; margin-top: 14px; border-top: 1px solid #d9e3dc; flex-wrap: wrap; }
.due-main { flex: 1; min-width: 220px; }
.deadline { display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: 600; color: #a0700b; margin: 6px 0 0; }
.left { font-weight: 500; color: #b8860b; }
.due-end { text-align: right; }
.due-amount { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #1a3a1a; margin: 0 0 6px; }
.methods { font-size: 0.76rem; color: #6a7a6a; margin: 5px 0 0; }
.history-bar { margin-top: 4px; }
.receipt-modal { max-width: 520px; }
.rm-head { display: flex; align-items: flex-start; gap: 12px; }
.rm-head > div { flex: 1; }
.close-btn { background: none; border: none; color: #6a7a6a; cursor: pointer; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background: #f2f5f2; }
.rm-dl { margin-top: 16px; }
.rm-dl .wide { grid-column: 1 / -1; }
.mono { font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.refund { margin-top: 16px; background: #f7faf8; border: 1px solid #d9e3dc; border-radius: 12px; padding: 14px 16px; }
.steps { list-style: none; margin: 0 0 6px; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.steps li { display: flex; align-items: center; gap: 10px; font-size: 0.84rem; color: #6a7a6a; }
.steps li span { width: 10px; height: 10px; border-radius: 50%; background: #d9e3dc; flex-shrink: 0; }
.steps li.on { color: #1a3a1a; }
.steps li.on span { background: #1f8f5c; }
.steps li.now span { background: #D4A017; box-shadow: 0 0 0 4px rgba(212, 160, 23, 0.2); }
.rm-total { display: flex; justify-content: space-between; align-items: center; background: #f2f7f3; border: 1px solid #d9e3dc; border-radius: 10px; padding: 12px 16px; margin-top: 16px; font-size: 0.88rem; }
.rm-total strong { font-family: 'Playfair Display', serif; font-size: 1.35rem; color: #1a3a1a; }
@media (max-width: 760px) {
  .figs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fig:nth-child(3) { border-left: none; }
  .fig:nth-child(n+3) { border-top: 1px solid #d9e3dc; }
}
@media (max-width: 640px) {
  .fig { padding: 14px 16px; }
  .fig-value { font-size: 1.3rem; }
  .due-end { text-align: left; width: 100%; }
  .due-end .nm-btn-dark { width: 100%; }
}
</style>
