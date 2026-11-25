<template>
  <div class="nm-page bl-page">
    <!-- HERO -->
    <section class="bl-hero">
      <img class="bl-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="bl-hero-fade" aria-hidden="true"></span>
      <div class="bl-hero-text">
        <p class="bl-eyebrow"><span aria-hidden="true"></span>Billing and invoices</p>
        <h2 class="bl-title">Your bills, <em>all in one place.</em></h2>
        <p class="nm-page-sub intro"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg>Pay for your consultations and keep your receipts. Each invoice appears when your RND confirms a booking.</p>
      </div>
    </section>

    <p v-if="error" class="nm-error">{{ error }}</p>
    <p v-if="paidNotice" class="nm-success"><CheckCircle2 :size="15" /> {{ paidNotice }}</p>

    <!-- figures -->
    <div class="figs">
      <div class="fig" style="--c: #004D3A; --bg: #E3EFE7">
        <div class="fig-top">
          <p class="fig-label">Due now</p>
          <span class="fig-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3" /><path d="M21 9h-6a3 3 0 0 0 0 6h6z" /><path d="M15 12h.01" /></svg></span>
        </div>
        <p class="fig-value">{{ peso(dueTotal) }}</p>
        <p class="fig-note" :class="{ warn: due.length }">{{ due.length ? `${due.length} invoice${due.length === 1 ? '' : 's'} to pay` : 'Nothing to pay' }}</p>
      </div>
      <div class="fig" style="--c: #9A7300; --bg: #FBF3D2">
        <div class="fig-top">
          <p class="fig-label">Paid in {{ thisYear }}</p>
          <span class="fig-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M8 12.5l2.5 2.5L16 9.5" /></svg></span>
        </div>
        <p class="fig-value">{{ peso(paidThisYear) }}</p>
        <p class="fig-note">{{ paidCount }} consultation{{ paidCount === 1 ? '' : 's' }}</p>
      </div>
      <div class="fig" style="--c: #3B5BA5; --bg: #EEF1FA">
        <div class="fig-top">
          <p class="fig-label">Refunds in progress</p>
          <span class="fig-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 8v4l3 2" /></svg></span>
        </div>
        <p class="fig-value">{{ peso(refundTotal) }}</p>
        <p class="fig-note">{{ refunding.length ? `Within ${REFUND_WINDOW}` : 'None' }}</p>
      </div>
      <div class="fig" :class="{ empty: !nextDeadline }" style="--c: #B4384A; --bg: #FDECEC">
        <div class="fig-top">
          <p class="fig-label">Next payment deadline</p>
          <span class="fig-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>
        </div>
        <p class="fig-value">{{ nextDeadline ? shortDate(nextDeadline) : '—' }}</p>
        <p class="fig-note">{{ nextDeadline ? phTime(nextDeadline) : 'No upcoming payments' }}</p>
      </div>
    </div>

    <!-- due -->
    <div v-if="due.length" class="due-panel">
      <div class="due-head">
        <span class="due-head-ico"><AlarmClock :size="20" aria-hidden="true" /></span>
        <div>
          <h2 class="due-title">Pay before your consultation</h2>
          <p class="due-sub">Unpaid consultations are cancelled automatically at their start time.</p>
        </div>
      </div>
      <div v-for="inv in due" :key="inv.id" class="due-row">
        <img v-if="inv.consultation.rnd.profile_photo" :src="inv.consultation.rnd.profile_photo" class="nm-avatar due-avatar" alt="" />
        <span v-else class="nm-avatar due-avatar">{{ nameInitials(inv.consultation.rnd.name) }}</span>
        <div class="due-main">
          <p class="due-what">{{ typeLabel(inv.consultation.type_label) }} with RND {{ inv.consultation.rnd.name }}</p>
          <p class="due-meta">{{ invNo(inv) }}, {{ when(inv.consultation.scheduled_at) }}</p>
          <p class="deadline"><AlarmClock :size="13" aria-hidden="true" /> Pay by {{ when(inv.pay_by) }} <span class="left">({{ timeLeft(inv.pay_by) }})</span></p>
        </div>
        <div class="due-end">
          <p class="due-amount">{{ peso(inv.amount) }}</p>
          <button class="bl-btn-dark" :disabled="payingId === inv.id" @click="payInvoice(inv)">
            <CreditCard :size="16" /> {{ payingId === inv.id ? 'Opening…' : 'Pay now' }}
          </button>
          <p class="methods">GCash, Maya, card or QR Ph</p>
        </div>
      </div>
    </div>

    <!-- history -->
    <div class="history-bar">
      <div class="bl-seg" role="tablist" aria-label="Invoices">
        <button v-for="t in TABS.filter(x => x.key === 'all' || countOf(x.key))" :key="t.key" type="button" class="bl-seg-btn" :class="{ active: tab === t.key }" @click="tab = t.key">
          {{ t.label }}<span v-if="countOf(t.key)" class="bl-seg-count">{{ countOf(t.key) }}</span>
        </button>
      </div>
      <label class="bl-search">
        <Search :size="18" aria-hidden="true" />
        <input v-model="search" type="search" placeholder="Search by RND or invoice number" aria-label="Search invoices" />
      </label>
    </div>

    <div class="bl-list">
      <p v-if="loading" class="bl-muted">Loading your invoices…</p>
      <div v-else-if="!invoices.length" class="bl-empty">
        <span class="bl-empty-ico"><Receipt :size="28" /></span>
        <p class="bl-empty-title">No invoices yet.</p>
        <p class="bl-muted">An invoice appears when your RND confirms a booking. Pay it before the consultation to join.</p>
      </div>
      <div v-else-if="!filtered.length" class="bl-empty"><p class="bl-empty-title">No invoices match.</p></div>
      <div v-else class="bl-table">
        <div class="bl-row bl-row-head" aria-hidden="true">
          <span>Invoice</span><span>Consultation</span><span class="r">Amount</span><span>Status</span><span></span>
        </div>
        <div v-for="inv in filtered" :key="inv.id" class="bl-row" role="button" tabindex="0" @click="open(inv)" @keydown.enter="open(inv)">
          <div class="bl-inv">
            <span class="bl-inv-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg></span>
            <span class="bl-stack"><strong>{{ invNo(inv) }}</strong><small>Issued {{ shortDate(inv.created_at) }}</small></span>
          </div>
          <div class="bl-con">
            <span class="bl-con-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>
            <span class="bl-stack">
              <strong>{{ typeLabel(inv.consultation.type_label) }} with RND {{ inv.consultation.rnd.name }}</strong>
              <small v-if="inv.consultation.scheduled_at">{{ when(inv.consultation.scheduled_at) }}</small>
            </span>
          </div>
          <div class="bl-amt">{{ peso(inv.amount) }}</div>
          <div class="bl-status">
            <span class="nm-pill bl-pill" :class="STATUS[inv.status]?.pill"><i aria-hidden="true"></i>{{ STATUS[inv.status]?.label || inv.status }}</span>
            <small>{{ statusDetail(inv) }}</small>
          </div>
          <div class="bl-act">
            <button v-if="inv.status === 'unpaid' && inv.pay_by" class="bl-btn-dark sm" :disabled="payingId === inv.id" @click.stop="payInvoice(inv)"><CreditCard :size="15" aria-hidden="true" /> Pay</button>
            <button v-else-if="inv.receipt" class="bl-btn-soft sm" @click.stop="open(inv)"><FileText :size="15" aria-hidden="true" /> Receipt</button>
          </div>
        </div>
      </div>
    </div>

    <!-- receipt / details -->
    <div v-if="current" class="nm-modal-overlay rm-overlay" @click.self="current = null">
      <div class="nm-modal receipt-modal" role="dialog" aria-modal="true" :aria-label="`${current.receipt ? 'Receipt' : 'Invoice'} ${invNo(current)}`">
        <button class="close-btn" aria-label="Close" @click="current = null"><X :size="18" /></button>

        <!-- top: what it is, and how much -->
        <div class="rm-top">
          <span class="rm-badge" :class="{ paid: current.receipt }">
            <svg v-if="current.receipt" class="ic" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
            <svg v-else class="ic" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3h14v18l-3-2-2 2-2-2-2 2-2-2-3 2z" /><path d="M9 8h6M9 12h6M9 16h3" /></svg>
          </span>
          <p class="rm-k">{{ current.receipt ? 'Receipt' : 'Invoice' }}, {{ invNo(current) }}</p>
          <p class="rm-amount">{{ peso(current.amount) }}</p>
          <p class="rm-amount-label">{{ current.receipt ? 'Total paid' : 'Amount' }}</p>
          <span class="nm-pill bl-pill" :class="STATUS[current.status]?.pill"><i aria-hidden="true"></i>{{ STATUS[current.status]?.label }}</span>
        </div>

        <!-- the paper edge -->
        <div class="rm-tear" aria-hidden="true"><span></span></div>

        <div class="rm-body">
          <dl class="rm-dl">
            <div><dt>RND</dt><dd>{{ current.consultation.rnd.name }}</dd></div>
            <div><dt>Consultation</dt><dd>{{ current.consultation.type_label ? typeLabel(current.consultation.type_label) : '—' }}<template v-if="current.consultation.duration_minutes">, {{ current.consultation.duration_minutes }} min</template></dd></div>
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
            <p class="rm-sec">Refund</p>
            <ol class="steps">
              <li class="on"><span /> Paid, {{ shortDate(current.receipt?.paid_at) }}</li>
              <li class="on"><span /> Consultation cancelled<template v-if="current.refund.cancelled_at">, {{ shortDate(current.refund.cancelled_at) }}</template></li>
              <li :class="{ on: true, now: current.refund.status === 'refund_pending' }"><span /> Refund in progress</li>
              <li :class="{ on: current.refund.status === 'refunded' }"><span /> Refunded<template v-if="current.refund.refunded_at">, {{ shortDate(current.refund.refunded_at) }}</template></li>
            </ol>
            <p v-if="current.refund.status === 'refund_pending'" class="rm-hint">{{ refundMessage(Number(current.amount).toLocaleString('en-PH', { minimumFractionDigits: 2 }), current.payment_method) }}</p>
          </div>
          <p v-if="current.consultation.cancellation_reason && current.status !== 'paid'" class="rm-note"><strong>Reason for cancelling:</strong> {{ current.consultation.cancellation_reason }}</p>

          <p v-if="current.receipt" class="rm-hint rm-mail"><Mail :size="14" aria-hidden="true" /> The receipt was emailed to you when you paid. Resend it if you can't find it.</p>
        </div>

        <div class="rm-actions">
          <template v-if="current.receipt">
            <button class="bl-btn-soft" :disabled="resending" @click="resend(current)"><Mail :size="15" /> {{ resending ? 'Sending…' : 'Resend receipt' }}</button>
            <button class="bl-btn-dark" @click="printReceipt(current)"><Printer :size="15" aria-hidden="true" /> Download or print</button>
          </template>
          <button v-else-if="current.status === 'unpaid' && current.pay_by" class="bl-btn-dark" :disabled="payingId === current.id" @click="payInvoice(current)"><CreditCard :size="15" /> Pay now</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
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
  refund_pending: { label: 'Refund in progress', pill: 'gold' },
  refunded: { label: 'Refunded', pill: 'muted' },
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
const toast = useToast() // the app's toast (2026-11-03)

async function load({ quiet = false } = {}) {
  if (!quiet) {
    loading.value = true
    error.value = ''
  }
  try {
    // The list first: asking PayMongo takes several seconds, and until the
    // list is in, the figures would read ₱0.00 and "Nothing to pay".
    invoices.value = await get('/client/invoices/')
  } catch {
    if (!quiet) error.value = 'Could not load your invoices. Please refresh the page.'
    return
  } finally {
    loading.value = false
  }
  // Then catch payments (and refunds) whose webhook was missed, and refresh.
  const synced = await post('/client/invoices/sync/').catch(() => null)
  if (synced?.updated) invoices.value = await get('/client/invoices/').catch(() => invoices.value)
}
function onVisible() {
  if (document.visibilityState === 'visible' && due.value.length) load({ quiet: true })
}
onMounted(() => {
  load()
  document.addEventListener('visibilitychange', onVisible)
})
onBeforeUnmount(() => document.removeEventListener('visibilitychange', onVisible))
useAutoRefresh(() => load({ quiet: true }), { paused: () => !!payingId.value })
watch(payError, (msg) => { if (msg) toast.error(msg, { id: 'pay' }) })

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
// The server sends "In Person"; the app writes it in sentence case.
const typeLabel = t => (t ? t.charAt(0) + t.slice(1).toLowerCase() : 'Consultation')
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
    toast.error(apiError(e, 'Could not send the receipt. Please try again.'), { id: 'receipt' })
  } finally {
    resending.value = false
  }
}
function flash(text, opts) {
  toast.success(text, opts)
}
function printReceipt(inv) {
  const ok = printDocument({
    title: 'Payment receipt',
    number: invNo(inv),
    rows: [
      ['Billed to', `${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim() || '—'],
      ['RND', inv.consultation.rnd.name],
      ['Consultation', `${typeLabel(inv.consultation.type_label)}${inv.consultation.scheduled_at ? ', ' + when(inv.consultation.scheduled_at) : ''}`],
      ['Paid on', when(inv.receipt.paid_at)],
      ['Paid via', paidVia(inv)],
      ...(inv.receipt.reference ? [['Payment reference', inv.receipt.reference]] : []),
      ['Status', STATUS[inv.status]?.label || inv.status],
    ],
    total: ['Total paid', peso(inv.amount)],
    note: inv.refund ? 'This consultation was cancelled and the payment is being refunded (or has been).' : 'Thank you for choosing NutriMatch.',
  })
  if (!ok) toast.problem('Allow pop-ups for this site to print the receipt.')
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
</script>

<style scoped>
/* =========================================================
   Billing: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings, money), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.bl-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; gap: 18px; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }
.bl-page .nm-error { margin: 0; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 14px; }
.nm-success { display: flex; align-items: center; gap: 8px; margin: 0; padding: 12px 16px; border-radius: 14px; background: #EAF4EE; border: 1px solid #CFE5D7; color: #1F6F46; font-size: 14px; font-weight: 600; }

/* ---------- HERO ---------- */
.bl-hero {
  position: relative;
  overflow: hidden;
  padding: 32px 34px;
  border-radius: 24px;
  color: #FFFFFF;
  background:
    radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%),
    linear-gradient(115deg, #035A45 0%, #004D3A 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -24px rgba(0, 77, 58, 0.55);
}
.bl-hero-plate { position: absolute; right: -70px; top: 50%; width: 400px; height: 400px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.55; pointer-events: none; }
.bl-hero-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004D3A 0%, #004D3A 45%, rgba(0, 77, 58, 0.75) 62%, rgba(0, 70, 52, 0.15) 100%); pointer-events: none; }
.bl-hero-text { position: relative; z-index: 1; max-width: 620px; }
.bl-eyebrow { margin: 0; display: flex; align-items: center; gap: 10px; font-size: 12.5px; font-weight: 800; color: #EFBF04; }
.bl-eyebrow span { width: 26px; height: 2px; border-radius: 2px; background: #EFBF04; }
.bl-title { margin: 10px 0 12px; font-family: 'Playfair Display', Georgia, serif; font-size: 40px; font-weight: 700; line-height: 1.12; color: #FFFFFF; }
.bl-title em { font-style: italic; color: #EFBF04; }
.bl-page .intro { margin: 0; display: flex; align-items: flex-start; gap: 8px; font-size: 15.0px; line-height: 1.55; color: rgba(255, 255, 255, 0.88); }
.intro .ic { margin-top: 5px; color: #8FD4A8; }

/* ---------- FIGURES ---------- */
.figs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.fig {
  position: relative;
  overflow: hidden;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 20px 22px 20px;
  border-radius: 20px;
  background: #FFFFFF;
  border: 1px solid #E4EBE6;
  box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3);
}
.fig::after { display: none; }
.fig-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.fig-label { margin: 0; font-size: 14px; font-weight: 700; color: #3E5046; }
.fig-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; background: var(--bg); color: var(--c); }
.fig-value { margin: 10px 0 12px; font-family: 'Playfair Display', Georgia, serif; font-size: 34px; font-weight: 700; line-height: 1; color: #0E3A2C; font-variant-numeric: lining-nums; }
.fig.empty .fig-value { color: #B5C2BA; }
.fig-note { margin: auto 0 0; align-self: flex-start; padding: 4px 10px; border-radius: 999px; background: #F3F6F4; font-size: 12px; font-weight: 600; color: #4A5A52; }
.fig-note.warn { background: #FBF3D2; color: #8A6400; font-weight: 700; }

/* ---------- DUE ---------- */
.due-panel { padding: 22px 24px; border-radius: 20px; background: linear-gradient(180deg, #FFFBEA 0%, #FFFFFF 70%); border: 1.5px solid #F1DE97; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(154, 115, 0, 0.35); }
.due-head { display: flex; align-items: flex-start; gap: 14px; }
.due-head-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; background: #EFBF04; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.due-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-weight: 700; color: #0E3A2C; }
.due-sub { margin: 4px 0 0; font-size: 13.5px; color: #6B5A1F; }
.due-row { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin-top: 16px; padding: 16px 18px; border-radius: 16px; background: #FFFFFF; border: 1px solid #F1E6BD; }
.due-avatar { flex-shrink: 0; width: 52px; height: 52px; border-radius: 50%; object-fit: cover; background: #E3EFE7; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; font-weight: 800; }
.due-main { flex: 1; min-width: 220px; }
.due-what { margin: 0; font-size: 15.5px; font-weight: 700; color: #0E3A2C; }
.due-meta { margin: 3px 0 0; font-size: 13px; color: #6B7D73; }
.deadline { display: inline-flex; align-items: center; gap: 6px; margin: 8px 0 0; padding: 4px 10px; border-radius: 999px; background: #FBF3D2; font-size: 12.5px; font-weight: 700; color: #8A6400; }
.left { font-weight: 500; color: #9A7300; }
.due-end { display: flex; flex-direction: column; align-items: flex-end; text-align: right; }
.due-amount { margin: 0 0 8px; font-family: 'Playfair Display', Georgia, serif; font-size: 26px; font-weight: 700; color: #0E3A2C; }
.methods { margin: 6px 0 0; font-size: 12px; color: #6B7D73; }

/* ---------- BUTTONS ---------- */
.bl-btn-dark,
.bl-btn-soft { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 46px; padding: 0 22px; border-radius: 12px; font-family: inherit; font-size: 14.5px; font-weight: 700; white-space: nowrap; cursor: pointer; transition: background-color .15s; }
.bl-btn-dark { border: none; background: #004D3A; color: #FFFFFF; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.bl-btn-dark:hover:not(:disabled) { background: #0A5C46; }
.bl-btn-soft { border: 1px solid #DCE8E0; background: #F1F6F2; color: #004D3A; }
.bl-btn-soft:hover:not(:disabled) { background: #E3EFE7; }
.bl-btn-dark:disabled,
.bl-btn-soft:disabled { opacity: .55; cursor: not-allowed; }
.bl-btn-dark.sm,
.bl-btn-soft.sm { height: 40px; padding: 0 20px; font-size: 13.5px; }
.bl-btn-dark:focus-visible,
.bl-btn-soft:focus-visible { outline: 3px solid rgba(239, 191, 4, 0.6); outline-offset: 2px; }

/* ---------- TABS + SEARCH ---------- */
.history-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-top: 4px; }
.bl-seg { display: inline-flex; gap: 4px; padding: 5px; border-radius: 999px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 6px 16px -12px rgba(16, 35, 27, 0.3); }
.bl-seg-btn { display: inline-flex; align-items: center; gap: 8px; height: 38px; padding: 0 18px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 14px; font-weight: 700; color: #3E5046; cursor: pointer; transition: background-color .15s, color .15s; }
.bl-seg-btn:hover:not(.active) { color: #004D3A; }
.bl-seg-count { min-width: 22px; height: 22px; padding: 0 6px; border-radius: 999px; background: #EEF4F0; color: #004D3A; font-size: 12px; display: inline-flex; align-items: center; justify-content: center; }
.bl-seg-btn.active { background: #004D3A; color: #FFFFFF; }
.bl-seg-btn.active .bl-seg-count { background: rgba(255, 255, 255, 0.18); color: #FFFFFF; }
.bl-seg-btn:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.bl-search { display: flex; align-items: center; gap: 10px; width: 380px; max-width: 100%; height: 48px; padding: 0 18px; border-radius: 10px; background: #FFFFFF; border: 1px solid #E4EBE6; color: #6B7D73; box-shadow: 0 6px 16px -12px rgba(16, 35, 27, 0.3); cursor: text; }
.bl-search:focus-within { border-color: #004D3A; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.bl-search input { flex: 1; min-width: 0; border: none; outline: none; background: transparent; font-family: inherit; font-size: 14px; color: #14261E; }

/* ---------- INVOICE LIST ---------- */
.bl-list { padding: 8px 10px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.bl-muted { margin: 0; padding: 14px; font-size: 14px; line-height: 1.55; color: #6B7D73; }
.bl-empty { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 40px 20px; text-align: center; }
.bl-empty .bl-muted { padding: 0; max-width: 420px; }
.bl-empty-ico { width: 60px; height: 60px; margin-bottom: 10px; border-radius: 18px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.bl-empty-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: #0E3A2C; }
.bl-row { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1.6fr) 120px minmax(0, 1fr) 130px; align-items: center; gap: 16px; padding: 18px; border-radius: 16px; transition: background-color .15s; }
.bl-row:not(.bl-row-head) { cursor: pointer; }
.bl-row:not(.bl-row-head):hover { background: #F6FAF7; }
.bl-row:not(.bl-row-head):focus-visible { outline: 2px solid #EFBF04; outline-offset: -2px; }
.bl-row + .bl-row:not(:nth-child(2)) { border-top: 1px solid #F0F3F1; border-radius: 0; }
.bl-row-head { height: 46px; padding: 0 18px; border-bottom: 1px solid #EEF2EF; border-radius: 0; font-size: 12px; font-weight: 800; color: #4A5A52; }
.bl-row-head .r,
.bl-amt { text-align: right; }
.bl-inv,
.bl-con { display: flex; align-items: center; gap: 14px; min-width: 0; }
.bl-stack { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.bl-inv-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.bl-inv strong { font-size: 15px; font-weight: 800; letter-spacing: .3px; color: #0E3A2C; }
.bl-con strong { font-size: 14.5px; font-weight: 600; color: #14261E; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.bl-inv small,
.bl-con small,
.bl-status small { font-size: 12.5px; color: #6B7D73; }
.bl-con-ico { flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%; background: #F3F6F4; color: #1F5C45; display: inline-flex; align-items: center; justify-content: center; }
.bl-amt { font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #0E3A2C; font-variant-numeric: lining-nums tabular-nums; }
.bl-status { display: flex; flex-direction: column; align-items: flex-start; gap: 5px; min-width: 0; }
.bl-pill { display: inline-flex; align-items: center; gap: 6px; height: 26px; padding: 0 12px; border-radius: 999px; font-size: 12.5px; font-weight: 800; white-space: nowrap; background: #F3F6F4; color: #4A5A52; }
.bl-pill i { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.bl-pill.green { background: #EAF4EE; color: #1F7A4C; }
.bl-pill.gold { background: #FBF3D2; color: #8A6400; }
.bl-pill.muted { background: #F1F3F2; color: #6B7D73; }
.bl-act { display: flex; justify-content: flex-end; }

/* ---------- RECEIPT MODAL: looks like a paper receipt ---------- */
.rm-overlay { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 24px; background: rgba(4, 30, 21, 0.55); -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px); }
.receipt-modal { position: relative; width: 100%; max-width: 460px; max-height: 92vh; max-height: 92dvh; display: flex; flex-direction: column; overflow: hidden; padding: 0 !important; border-radius: 26px !important; background: #FFFFFF; box-shadow: 0 40px 90px -30px rgba(0, 0, 0, 0.6); font-family: 'DM Sans', Arial, sans-serif; animation: rm-in .25s cubic-bezier(.2, .7, .2, 1); }
@keyframes rm-in { from { opacity: 0; transform: translateY(12px) scale(.98); } to { opacity: 1; transform: none; } }
.close-btn { position: absolute; top: 14px; right: 14px; z-index: 2; width: 36px; height: 36px; border: none; border-radius: 50%; background: #FFFFFF; color: #4A5A52; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px -6px rgba(16, 35, 27, 0.35); }
.close-btn:hover { color: #0E3A2C; background: #F3F6F4; }
.close-btn:focus-visible { outline: 2px solid #EFBF04; outline-offset: 1px; }

.rm-top { flex-shrink: 0; display: flex; flex-direction: column; align-items: center; padding: 30px 24px 22px; text-align: center; background: linear-gradient(180deg, #EAF4EE 0%, #F6FAF7 100%); }
.rm-badge { width: 60px; height: 60px; margin-bottom: 14px; border-radius: 50%; background: #FFFFFF; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 0 0 6px rgba(0, 77, 58, 0.06), 0 12px 24px -14px rgba(0, 77, 58, 0.6); }
.rm-badge.paid { background: #0B6B47; color: #FFFFFF; box-shadow: 0 0 0 6px rgba(31, 157, 85, 0.15), 0 12px 24px -12px rgba(0, 77, 58, 0.7); }
.rm-k { margin: 0; font-size: 12px; font-weight: 800; color: #4A5A52; }
.rm-amount { margin: 8px 0 0; font-family: 'Playfair Display', Georgia, serif; font-size: 42px; font-weight: 700; line-height: 1; color: #0E3A2C; font-variant-numeric: lining-nums; }
.rm-amount-label { margin: 6px 0 12px; font-size: 13px; color: #6B7D73; }

/* torn-paper edge between the top and the details */
.rm-tear { position: relative; flex-shrink: 0; height: 22px; background: #FFFFFF; }
.rm-tear::before,
.rm-tear::after { content: ''; position: absolute; top: 0; width: 22px; height: 22px; border-radius: 50%; background: rgba(4, 30, 21, 0.55); transform: translateY(-50%); }
.rm-tear::before { left: -11px; }
.rm-tear::after { right: -11px; }
.rm-tear span { position: absolute; left: 22px; right: 22px; top: 0; border-top: 2px dashed #DCE5DF; }

.rm-body { flex: 1; min-height: 0; overflow-y: auto; padding: 0 26px 6px; }
.rm-dl { margin: 0; display: flex; flex-direction: column; }
.rm-dl > div { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; padding: 11px 0; border-bottom: 1px solid #F0F3F1; }
.rm-dl > div:last-child { border-bottom: none; }
.rm-dl dt { flex-shrink: 0; font-size: 13.5px; color: #6B7D73; }
.rm-dl dd { margin: 0; min-width: 0; text-align: right; font-size: 14px; font-weight: 700; color: #0E3A2C; }
.rm-dl .wide { flex-direction: column; align-items: stretch; gap: 6px; }
.rm-dl .wide dd { text-align: left; }
.mono { padding: 8px 12px; border-radius: 10px; background: #F6FAF7; font-family: ui-monospace, 'SFMono-Regular', Menlo, Consolas, monospace; font-size: 12.5px !important; font-weight: 600 !important; letter-spacing: .2px; color: #3E5046 !important; overflow-wrap: anywhere; }
.rm-sec { margin: 0 0 10px; font-size: 12px; font-weight: 800; color: #3B5BA5; }
.refund { margin-top: 12px; padding: 14px 16px; border-radius: 14px; background: #F7F9FD; border: 1px solid #DCE3F2; }
.steps { list-style: none; margin: 0 0 6px; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.steps li { display: flex; align-items: center; gap: 10px; font-size: 13.5px; color: #6B7D73; }
.steps li span { flex-shrink: 0; width: 10px; height: 10px; border-radius: 50%; background: #D9E3DC; }
.steps li.on { color: #0E3A2C; }
.steps li.on span { background: #1F9D55; }
.steps li.now span { background: #EFBF04; box-shadow: 0 0 0 4px rgba(239, 191, 4, 0.2); }
.rm-hint { margin: 8px 0 0; font-size: 12.5px; line-height: 1.5; color: #6B7D73; }
.rm-mail { display: flex; align-items: flex-start; gap: 8px; margin: 14px 0 4px; padding: 10px 12px; border-radius: 12px; background: #F6FAF7; }
.rm-mail svg { flex-shrink: 0; margin-top: 2px; color: #1F7A4D; }
.rm-note { margin: 12px 0 0; padding: 12px 14px; border-radius: 12px; background: #F7FAF8; font-size: 13px; line-height: 1.5; color: #4A5A52; }
.rm-actions { flex-shrink: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 16px 26px 24px; }
.rm-actions > :only-child { grid-column: 1 / -1; }
.rm-actions:empty { display: none; }
.rm-actions .bl-btn-dark,
.rm-actions .bl-btn-soft { height: 48px; padding: 0 12px; }

/* ---------- SMALLER SCREENS ---------- */
@media (max-width: 1100px) {
  .figs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 960px) {
  .bl-page { gap: 14px; padding-bottom: 96px; }
  .bl-hero { padding: 22px 18px 20px; border-radius: 22px; }
  .bl-hero-plate { width: 170px; height: 170px; right: -50px; top: 18px; transform: none; opacity: .9; }
  .bl-hero-fade { background: linear-gradient(90deg, #004D3A 40%, rgba(0, 77, 58, 0.5) 75%, rgba(0, 77, 58, 0.2)); }
  .bl-hero-text { max-width: 74%; }
  .bl-title { font-size: 28px; }
  .bl-page .intro { font-size: 13px; }
  .intro .ic { display: none; }
  .figs { gap: 10px; }
  .fig { padding: 14px 14px 16px; border-radius: 18px; }
  .fig-ico { width: 32px; height: 32px; border-radius: 11px; }
  .fig-ico .ic { width: 17px; height: 17px; }
  .fig-label { font-size: 12.5px; }
  .fig-value { margin: 12px 0 10px; font-size: 24px; }
  .fig-note { padding: 3px 8px; font-size: 11px; }
  .due-panel { padding: 16px; border-radius: 18px; }
  .due-row { padding: 14px; gap: 12px; }
  .due-end { width: 100%; flex-direction: row; flex-wrap: wrap; align-items: center; justify-content: space-between; text-align: left; }
  .due-amount { margin: 0; font-size: 22px; }
  .due-end .bl-btn-dark { flex: 1; max-width: 200px; }
  .methods { flex-basis: 100%; }
  .history-bar { flex-direction: column; align-items: stretch; gap: 10px; }
  .bl-seg { align-self: flex-start; max-width: 100%; overflow-x: auto; }
  .bl-search { width: 100%; height: 46px; }
  .bl-list { padding: 6px; border-radius: 18px; }
  .bl-row-head { display: none; }
  .bl-row { grid-template-columns: minmax(0, 1fr) auto; grid-template-areas: "inv amt" "con con" "status act"; gap: 12px; padding: 14px; }
  .bl-row + .bl-row:not(:nth-child(2)) { border-top: 1px solid #EEF2EF; }
  .bl-inv { grid-area: inv; }
  .bl-amt { grid-area: amt; font-size: 19px; }
  .bl-con { grid-area: con; padding: 10px 12px; border-radius: 12px; background: #F6FAF7; }
  .bl-con strong { white-space: normal; }
  .bl-status { grid-area: status; }
  .bl-act { grid-area: act; align-self: end; }
}
@media (max-width: 640px) {
  .rm-overlay { padding: 0; align-items: flex-end; }
  .receipt-modal { max-width: none; max-height: 94dvh; border-radius: 26px 26px 0 0 !important; animation: none; }
  .rm-tear::before,
  .rm-tear::after { display: none; }
  .rm-top { padding: 26px 18px 18px; }
  .rm-amount { font-size: 36px; }
  .rm-body { padding: 0 18px 4px; }
  .rm-dl dt { font-size: 13px; }
  .rm-dl dd { font-size: 13.5px; }
  .rm-actions { padding: 14px 18px calc(16px + env(safe-area-inset-bottom)); }
}
</style>