<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <p v-if="loading" class="nm-muted">Loading your earnings…</p>

    <template v-else-if="e">
      <!-- statement: next payout, then where the money is (it moves on hold, cleared, paid out) -->
      <section class="nm-panel statement">
        <div class="st-head">
          <div>
            <h1 class="st-title">Next payout {{ longDate(e.next_payout_date) }}</h1>
            <p class="st-sub">
              <template v-if="!e.payout_account">Add your GCash or bank details so NutriMatch can send your earnings. Your balance is kept until then.</template>
              <template v-else-if="!e.eligible">Payouts start at {{ peso(e.minimum_payout) }} cleared. Smaller balances carry over to the next 5th.</template>
              <template v-else>{{ peso(e.payable) }} cleared by {{ shortDate(e.run_date) }} goes to your {{ accountText }}.</template>
            </p>
          </div>
          <button v-if="!e.payout_account" type="button" class="nm-btn-gold" @click="startEdit">Add payout details</button>
          <p v-else class="st-account">{{ accountText }} <button type="button" class="nm-btn-gold nm-btn-sm" @click="startEdit">Change</button></p>
        </div>

        <div class="st-figures">
          <div class="st-flow">
            <div class="fig">
              <p class="fig-label">On hold</p>
              <p class="fig-value">{{ peso(e.pending) }}</p>
              <p class="fig-note">Clears {{ e.hold_days }} days after the consultation</p>
            </div>
            <ChevronRight :size="18" class="fig-arrow" aria-hidden="true" />
            <div class="fig">
              <p class="fig-label">Cleared</p>
              <p class="fig-value">{{ peso(e.posted) }}</p>
              <p class="fig-note">Paid out on {{ shortDate(e.next_payout_date) }}</p>
            </div>
            <ChevronRight :size="18" class="fig-arrow" aria-hidden="true" />
            <div class="fig">
              <p class="fig-label">Paid out</p>
              <p class="fig-value">{{ peso(e.paid_out) }}</p>
              <p class="fig-note">{{ e.payouts.length }} payout{{ e.payouts.length === 1 ? '' : 's' }} so far</p>
            </div>
          </div>
          <div class="fig fig-month">
            <p class="fig-label">Earned this month</p>
            <p class="fig-value">{{ peso(e.this_month.share) }}</p>
            <p class="fig-note">From {{ peso(e.this_month.gross) }} in fees</p>
          </div>
        </div>
      </section>

      <!-- consultations -->
      <div class="nm-toolbar">
        <div class="nm-tabs">
          <button v-for="t in TABS" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" @click="tab = t.key">
            {{ t.label }}<span v-if="countOf(t.key)" class="nm-count"> {{ countOf(t.key) }}</span>
          </button>
        </div>
        <div class="nm-search">
          <Search :size="15" />
          <input v-model="search" type="search" placeholder="Search patient or invoice no." />
        </div>
      </div>

      <div class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">Consultations</h2>
            <p class="nm-panel-sub">The fee minus the platform commission, fixed when you confirmed the booking</p>
          </div>
        </div>
        <p v-if="filtered.length" class="result-count">
          {{ filtered.length }} consultation{{ filtered.length === 1 ? '' : 's' }}<template v-if="rowPages > 1">, showing {{ (rowPage - 1) * ROWS_PER_PAGE + 1 }}–{{ Math.min(rowPage * ROWS_PER_PAGE, filtered.length) }}</template>
        </p>
        <p v-if="!filtered.length" class="empty-line">{{ e.statement.length ? 'No consultations in this view.' : 'No invoices yet. One is issued each time you confirm a booking.' }}</p>
        <div v-else class="nm-table-wrap">
          <table class="nm-table stack">
            <thead>
              <tr><th>Invoice</th><th>Patient</th><th class="nm-num">Fee</th><th class="nm-num">Commission</th><th class="nm-num">Your share</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr v-for="r in pagedRows" :key="r.invoice_id" class="clickable" @click="row = r">
                <td data-label="Invoice"><strong>INV-{{ pad(r.invoice_id) }}</strong></td>
                <td data-label="Patient">{{ r.client_name }}<span class="nm-row-sub" style="display: block">{{ r.consultation_type }}, {{ r.consultation_at ? shortDate(r.consultation_at) : 'no date' }}</span></td>
                <td data-label="Fee" class="nm-num">{{ peso(r.amount) }}</td>
                <td data-label="Commission" class="nm-num">− {{ peso(r.commission) }} <span class="nm-muted">({{ Number(r.commission_pct) }}%)</span></td>
                <td data-label="Your share" class="nm-num"><strong>{{ countsAsEarning(r) ? peso(r.share) : '—' }}</strong></td>
                <td data-label="Status">
                  <span class="nm-pill" :class="STATE[r.state]?.pill || 'muted'">{{ STATE[r.state]?.label || r.state }}</span>
                  <span class="nm-row-sub" style="display: block">{{ stateDetail(r) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- same pager as Food Exchange Search: centred, the count sits above the table -->
        <div v-if="rowPages > 1" class="pager">
          <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="rowPage === 1" @click="rowPage--">Previous</button>
          <span class="pager-num">Page {{ rowPage }} of {{ rowPages }}</span>
          <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="rowPage === rowPages" @click="rowPage++">Next</button>
        </div>
      </div>

      <div class="nm-grid-even lower">
        <!-- payouts -->
        <div class="nm-panel">
          <h2 class="nm-panel-title">Payouts</h2>
          <p class="nm-panel-sub">Sent on the 5th of each month<template v-if="e.payouts.length">, {{ e.payouts.length }} so far</template></p>
          <p v-if="!e.payouts.length" class="empty-line">No payouts yet. The first one is sent on the 5th once {{ peso(e.minimum_payout) }} has cleared.</p>
          <button v-for="p in pagedPayouts" :key="p.id" type="button" class="payout-row" @click="openPayout(p)">
            <span class="payout-main">
              <span class="nm-row-title">{{ peso(p.amount) }} for {{ p.invoice_count }} consultation{{ p.invoice_count === 1 ? '' : 's' }}</span>
              <span class="nm-row-sub">{{ shortDate(p.released_at) }}, to {{ payoutVia(p.method, p.bank_name) }} •••• {{ String(p.account_number).slice(-4) }}, ref. {{ p.reference }}</span>
            </span>
            <ChevronRight :size="16" class="chev" />
          </button>
          <div v-if="payoutPages > 1" class="pager">
            <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="payoutPage === 1" @click="payoutPage--">Newer</button>
            <span class="pager-num">Page {{ payoutPage }} of {{ payoutPages }}</span>
            <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="payoutPage === payoutPages" @click="payoutPage++">Older</button>
          </div>
        </div>

        <!-- trend -->
        <div class="nm-panel">
          <h2 class="nm-panel-title">Your share, last 6 months</h2>
          <p class="nm-panel-sub">By the month the client paid</p>
          <div class="chart">
            <div v-for="m in trend" :key="m.key" class="bar-col">
              <span class="bar-val">{{ m.amount ? peso0(m.amount) : '' }}</span>
              <span class="bar" :style="{ height: `${Math.max(2, (m.amount / maxTrend) * 100)}%` }" />
              <span class="bar-label">{{ m.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- payout details (opened from the statement's Add / Change) -->
    <div v-if="editing" class="nm-modal-overlay" @click.self="saving ? null : (editing = false)">
      <form class="nm-modal pd-modal" role="dialog" aria-modal="true" aria-labelledby="pd-title" novalidate @submit.prevent="saveAccount">
        <button type="button" class="nm-modal-x" aria-label="Close" :disabled="saving" @click="editing = false"><X :size="18" /></button>
        <h3 id="pd-title" class="nm-modal-title">{{ account ? 'Change payout details' : 'Add payout details' }}</h3>
        <p class="nm-modal-text">Where NutriMatch sends your earnings on the 5th. Only NutriMatch admins can see these.</p>
        <div class="pd-methods" role="radiogroup" aria-label="Send my earnings by">
          <label class="pd-method" :class="{ on: form.kind === 'ewallet' }"><input v-model="form.kind" type="radio" value="ewallet" /> E-wallet</label>
          <label class="pd-method" :class="{ on: form.kind === 'bank' }"><input v-model="form.kind" type="radio" value="bank" /> Bank transfer</label>
        </div>
        <div class="pd-fields">
          <div v-if="form.kind === 'ewallet'">
            <label class="nm-label" for="pd-wallet">E-wallet</label>
            <select id="pd-wallet" v-model="form.wallet" class="nm-select block">
              <option v-for="w in WALLETS" :key="w.value" :value="w.value">{{ w.label }}</option>
            </select>
          </div>
          <div v-else>
            <label class="nm-label" for="pd-bank">Bank</label>
            <select id="pd-bank" v-model="form.bankChoice" class="nm-select block" :class="{ invalid: formErrors.bank_name }">
              <option value="" disabled>Choose your bank</option>
              <option v-for="b in BANKS" :key="b" :value="b">{{ b }}</option>
              <option value="__other">Other bank</option>
            </select>
            <input v-if="form.bankChoice === '__other'" v-model="form.otherBank" class="nm-input pd-other" maxlength="100" placeholder="Name of your bank" aria-label="Name of your bank" />
            <p v-if="formErrors.bank_name" class="nm-field-error">{{ formErrors.bank_name }}</p>
          </div>
          <div>
            <label class="nm-label" for="pd-name">Account name</label>
            <input id="pd-name" v-model="form.account_name" class="nm-input" maxlength="150" placeholder="Name on the account" />
            <p v-if="formErrors.account_name" class="nm-field-error">{{ formErrors.account_name }}</p>
          </div>
          <div>
            <label class="nm-label" for="pd-number">{{ numberLabel }}</label>
            <input id="pd-number" :value="form.account_number" class="nm-input" :class="{ invalid: numberMessage }" inputmode="numeric" autocomplete="off"
                   :maxlength="numberMax" :placeholder="isMobileWallet(formMethod) ? '09171234567' : 'Digits only'"
                   :aria-invalid="!!numberMessage" aria-describedby="pd-number-help" @input="onNumberInput" @blur="numberTouched = true" />
            <p v-if="numberMessage" id="pd-number-help" class="nm-field-error">{{ numberMessage }}</p>
            <p v-else id="pd-number-help" class="nm-hint pd-count">{{ isMobileWallet(formMethod) ? `${form.account_number.length} of 11 digits` : '6 to 20 digits' }}</p>
          </div>
        </div>
        <p v-if="formErrors.detail" class="nm-field-error">{{ formErrors.detail }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" :disabled="saving" @click="editing = false">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="saving">{{ saving ? 'Saving…' : 'Save payout details' }}</button>
        </div>
      </form>
    </div>

    <!-- invoice detail -->
    <div v-if="row" class="nm-modal-overlay" @click.self="row = null">
      <div class="nm-modal inv" role="dialog" aria-modal="true" :aria-label="`Invoice INV-${pad(row.invoice_id)}`">
        <div class="inv-head nm-modal-head">
          <div class="inv-who">
            <h3 class="inv-title">{{ row.client_name }}</h3>
            <p class="inv-sub">INV-{{ pad(row.invoice_id) }}, {{ row.consultation_type.toLowerCase() }} consultation{{ row.consultation_at ? ` on ${when(row.consultation_at)}` : '' }}</p>
          </div>
          <span class="nm-pill" :class="STATE[row.state]?.pill || 'muted'">{{ STATE[row.state]?.label }}</span>
          <button class="close-btn" aria-label="Close" @click="row = null"><X :size="18" /></button>
        </div>

        <div class="inv-money">
          <p><span>Consultation fee</span><span>{{ peso(row.amount) }}</span></p>
          <p><span>Platform commission, {{ Number(row.commission_pct) }}%</span><span>− {{ peso(row.commission) }}</span></p>
          <p class="inv-total">
            <span>{{ countsAsEarning(row) ? 'Your share' : row.state === 'awaiting_payment' ? 'Your share once paid' : 'Your share' }}</span>
            <span :class="{ void: ['refund_pending', 'refunded', 'voided'].includes(row.state) }">{{ peso(row.share) }}</span>
          </p>
        </div>

        <ol class="inv-steps">
          <li v-for="st in invoiceSteps(row)" :key="st.label" :class="st.state">
            <span class="dot" aria-hidden="true" />
            <span class="st-text"><strong>{{ st.label }}</strong><span>{{ st.when }}</span></span>
          </li>
        </ol>

        <p class="inv-note">{{ stateExplain(row) }}</p>
      </div>
    </div>

    <!-- payout detail -->
    <div v-if="payout" class="nm-modal-overlay" @click.self="payout = null">
      <div class="nm-modal wide-modal" role="dialog" aria-modal="true" aria-label="Payout">
        <div class="md-head nm-modal-head">
          <div>
            <h3 class="inv-title">Payout of {{ peso(payout.amount) }}</h3>
            <p class="inv-sub">Sent {{ shortDate(payout.released_at) }}</p>
          </div>
          <button class="close-btn" aria-label="Close" @click="payout = null"><X :size="18" /></button>
        </div>
        <dl class="nm-dl" style="margin-top: 14px">
          <div><dt>Sent to</dt><dd>{{ payoutVia(payout.method, payout.bank_name) }}, {{ payout.account_name }}, {{ payout.account_number }}</dd></div>
          <div><dt>Reference</dt><dd>{{ payout.reference }}</dd></div>
        </dl>
        <h4 class="sub-title">Consultations in this payout</h4>
        <p v-if="!payout.invoices" class="nm-muted">Loading…</p>
        <div v-else class="nm-table-wrap">
          <table class="nm-table">
            <thead><tr><th>Invoice</th><th>Patient</th><th class="nm-num">Fee</th><th class="nm-num">Your share</th></tr></thead>
            <tbody>
              <tr v-for="i in payout.invoices" :key="i.invoice_id">
                <td>INV-{{ pad(i.invoice_id) }}</td>
                <td>{{ i.client_name }}<span class="nm-row-sub" style="display: block">{{ i.consultation_at ? shortDate(i.consultation_at) : '' }}</span></td>
                <td class="nm-num">{{ peso(i.amount) }}</td>
                <td class="nm-num"><strong>{{ peso(i.share) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="nm-modal-actions">
          <button class="nm-btn-outline" :disabled="resending" @click="resendPayout(payout)"><Mail :size="14" /> {{ resending ? 'Sending…' : 'Resend payout email' }}</button>
          <button class="nm-btn-dark" :disabled="!payout.invoices" @click="printStatement(payout)"><Printer :size="14" /> Download / print statement</button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import {
  CheckCircle2, ChevronRight, Mail, Printer, Search, X,
} from 'lucide-vue-next'
import { BANKS, WALLETS, isMobileWallet, payoutVia } from '~/utils/payout'

const { get, put, post } = useApi()
const route = useRoute()

const STATE = {
  awaiting_payment: { label: 'Awaiting payment', pill: 'gold' },
  pending: { label: 'On hold', pill: 'gold' },
  posted: { label: 'Cleared', pill: 'green' },
  paid_out: { label: 'Paid out', pill: 'blue' },
  refund_pending: { label: 'Being refunded', pill: 'red' },
  refunded: { label: 'Refunded', pill: 'muted' },
  voided: { label: 'Voided', pill: 'muted' },
}
const TABS = [
  { key: 'all', label: 'All' },
  { key: 'awaiting_payment', label: 'Awaiting payment' },
  { key: 'pending', label: 'On hold' },
  { key: 'posted', label: 'Cleared' },
  { key: 'paid_out', label: 'Paid out' },
  { key: 'other', label: 'Refunded / voided' },
]

const e = ref(null)
const loading = ref(true)
const error = ref('')
const tab = ref('all')
const search = ref('')
const row = ref(null)
const payout = ref(null)
const toast = ref('')
const resending = ref(false)

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    const [earnings, acc] = await Promise.all([get('/rnd/earnings/'), get('/rnd/payout-account/').catch(() => null)])
    e.value = earnings
    account.value = acc && acc.method ? acc : null
    // the dashboard's "Add payout details" link opens the pop-up (/earnings?payout=1)
    if (route.query.payout && !quiet) startEdit()
  } catch {
    if (!quiet) error.value = 'Could not load your earnings.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
// a payment, a posted balance or a payout shows without a reload
useAutoRefresh(() => load({ quiet: true }))

const accountText = computed(() => {
  const a = e.value?.payout_account
  if (!a) return ''
  return `${payoutVia(a.method, a.bank_name)} •••• ${a.account_number_last4}`
})

function inTab(r, key) {
  if (key === 'all') return true
  if (key === 'other') return ['refund_pending', 'refunded', 'voided'].includes(r.state)
  return r.state === key
}
const countOf = key => (e.value?.statement || []).filter(r => inTab(r, key)).length
const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return (e.value?.statement || []).filter(r => inTab(r, tab.value) && (!q || `INV-${pad(r.invoice_id)} ${r.client_name}`.toLowerCase().includes(q)))
})
// 5 consultations / 5 payouts per page; back to page 1 when the filter changes.
const ROWS_PER_PAGE = 5
const PAYOUTS_PER_PAGE = 5
const rowPage = ref(1)
const rowPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / ROWS_PER_PAGE)))
const pagedRows = computed(() => filtered.value.slice((rowPage.value - 1) * ROWS_PER_PAGE, rowPage.value * ROWS_PER_PAGE))
watch([tab, search], () => { rowPage.value = 1 })
watch(rowPages, (n) => { if (rowPage.value > n) rowPage.value = n })
const payoutPage = ref(1)
const payoutPages = computed(() => Math.max(1, Math.ceil((e.value?.payouts.length || 0) / PAYOUTS_PER_PAGE)))
const pagedPayouts = computed(() => (e.value?.payouts || []).slice((payoutPage.value - 1) * PAYOUTS_PER_PAGE, payoutPage.value * PAYOUTS_PER_PAGE))

const countsAsEarning = r => ['pending', 'posted', 'paid_out'].includes(r.state)

function stateDetail(r) {
  if (r.state === 'awaiting_payment') return 'Client pays before the consultation'
  if (r.state === 'pending') return r.posts_on ? `Clears ${shortDate(r.posts_on)}` : 'Clears 3 days after it\'s completed'
  if (r.state === 'posted') return `For the ${shortDate(r.payable ? e.value.run_date : e.value.next_payout_date)} payout`
  if (r.state === 'paid_out') return r.payout ? `Paid ${shortDate(r.payout.released_at)}` : ''
  if (r.state === 'refund_pending') return 'Cancelled after paying'
  return ''
}
function stateExplain(r) {
  return {
    awaiting_payment: 'The client hasn\'t paid yet. If it\'s still unpaid at the start time, the consultation is cancelled automatically.',
    pending: `Paid. It stays on hold until ${e.value.hold_days} days after you mark the consultation complete, in case the client reports a problem.`,
    posted: r.payable
      ? `Cleared by ${longDate(e.value.run_date)}, so it's in that payout. NutriMatch sends it to your payout account.`
      : `Cleared after ${longDate(e.value.run_date)}, so it's in the next payout on ${longDate(e.value.next_payout_date)}. Payouts are never sent early.`,
    paid_out: 'Sent to your payout account.',
    refund_pending: 'The consultation was cancelled after the client paid, so the client is being refunded. It doesn\'t count toward your earnings.',
    refunded: 'The client was refunded. It doesn\'t count toward your earnings.',
    voided: 'The consultation was cancelled before it was paid, so there is nothing to pay out.',
  }[r.state] || ''
}

// The invoice's steps in order (pop-up): done, next (the one waiting) or later.
// A cancelled consultation ends at its cancellation instead.
function invoiceSteps(r) {
  const cancelled = ['refund_pending', 'refunded', 'voided'].includes(r.state)
  const steps = [{ label: 'Invoice issued', when: when(r.issued_at), done: true }]
  if (r.paid_at || !cancelled) {
    steps.push({ label: 'Client paid', when: r.paid_at ? `${when(r.paid_at)}${r.payment_method ? `, ${r.payment_method}` : ''}` : 'Due before the consultation starts', done: !!r.paid_at })
  }
  if (cancelled) {
    steps.push({ label: r.state === 'voided' ? 'Cancelled before payment' : r.state === 'refunded' ? 'Refunded to the client' : 'Being refunded to the client', when: r.state === 'refund_pending' ? 'NutriMatch handles the refund' : '', done: r.state !== 'refund_pending' })
  } else {
    const posted = ['posted', 'paid_out'].includes(r.state)
    steps.push({ label: 'Cleared', when: r.posts_on ? when(r.posts_on) : `${e.value.hold_days} days after the consultation is completed`, done: posted })
    steps.push({ label: 'Paid out', when: r.payout ? `${shortDate(r.payout.released_at)}, ref. ${r.payout.reference}` : `On a payout day (the 5th)`, done: r.state === 'paid_out' })
  }
  const next = steps.findIndex(x => !x.done)
  return steps.map((x, i) => ({ ...x, state: x.done ? 'done' : i === next ? 'next' : 'later' }))
}

// last 6 months of your share, by the month the client paid
const trend = computed(() => {
  const out = []
  const d = new Date()
  for (let i = 5; i >= 0; i--) {
    const m = new Date(d.getFullYear(), d.getMonth() - i, 1)
    const key = `${m.getFullYear()}-${m.getMonth()}`
    const amount = (e.value?.statement || []).filter((r) => {
      if (!r.paid_at || !countsAsEarning(r)) return false
      const p = new Date(r.paid_at)
      return p.getFullYear() === m.getFullYear() && p.getMonth() === m.getMonth()
    }).reduce((n, r) => n + Number(r.share), 0)
    out.push({ key, label: m.toLocaleDateString('en-PH', { month: 'short' }), amount })
  }
  return out
})
const maxTrend = computed(() => Math.max(1, ...trend.value.map(m => m.amount)))

async function openPayout(p) {
  payout.value = { ...p, invoices: null }
  try {
    payout.value = await get(`/rnd/payouts/${p.id}/`)
  } catch {
    payout.value = { ...p, invoices: [] }
  }
}
async function resendPayout(p) {
  resending.value = true
  try {
    flash((await post(`/rnd/payouts/${p.id}/resend/`)).detail)
  } catch (err) {
    flash(apiError(err, 'Could not send the email. Please try again.'))
  } finally {
    resending.value = false
  }
}
function printStatement(p) {
  const method = payoutVia(p.method, p.bank_name)
  const ok = printDocument({
    title: 'Payout statement',
    number: `Payout #${p.id}, ${shortDate(p.released_at)}`,
    rows: [['Paid to', p.account_name], ['Sent via', `${method}, ${p.account_number}`], ['Reference', p.reference], ['Payout date', shortDate(p.payout_date)]],
    table: [['Invoice', 'Patient', 'Consultation', 'Fee', 'Your share'],
      ...p.invoices.map(i => [`INV-${pad(i.invoice_id)}`, i.client_name, i.consultation_at ? shortDate(i.consultation_at) : '—', peso(i.amount), peso(i.share)])],
    total: ['Total paid out', peso(p.amount)],
  })
  if (!ok) flash('Allow pop-ups for this site to print the statement.')
}

/* payout details: an e-wallet (GCash, Maya, GoTyme, MariBank) or a bank from
   the list / typed in. Same rules as the API: GCash and Maya 09XXXXXXXXX,
   everything else 6–20 digits. */
const account = ref(null)
const editing = ref(false)
const saving = ref(false)
const form = reactive({ kind: 'ewallet', wallet: 'gcash', bankChoice: '', otherBank: '', account_name: '', account_number: '' })
const formErrors = reactive({})
const formMethod = computed(() => (form.kind === 'bank' ? 'bank' : form.wallet))
const formBank = computed(() => (form.bankChoice === '__other' ? form.otherBank.trim() : form.bankChoice))
// account number: digits only, capped per method, checked while typing
const numberTouched = ref(false)
const numberMax = computed(() => (isMobileWallet(formMethod.value) ? 11 : 20))
function onNumberInput(ev) {
  const digits = ev.target.value.replace(/\D/g, '').slice(0, numberMax.value)
  form.account_number = digits
  if (ev.target.value !== digits) ev.target.value = digits
  delete formErrors.account_number
}
watch(numberMax, (max) => { form.account_number = form.account_number.slice(0, max) })
const numberError = computed(() => {
  const v = form.account_number
  const name = payoutVia(formMethod.value)
  if (isMobileWallet(formMethod.value)) {
    if (v.length >= 2 && !v.startsWith('09')) return `${name} numbers start with 09.`
    if (numberTouched.value && v.length !== 11) return v ? `Enter the 11-digit ${name} number, e.g. 09171234567.` : `Enter your ${name} number.`
  } else if (numberTouched.value && v.length < 6) {
    return v ? 'Account numbers are 6 to 20 digits.' : 'Enter your account number.'
  }
  return ''
})
const numberMessage = computed(() => formErrors.account_number || numberError.value)
const numberLabel = computed(() => (isMobileWallet(formMethod.value) ? `${payoutVia(formMethod.value)} number` : 'Account number'))
function startEdit() {
  const a = account.value
  const isBank = a?.method === 'bank'
  Object.assign(form, {
    kind: isBank ? 'bank' : 'ewallet',
    wallet: !a || isBank ? 'gcash' : a.method,
    bankChoice: isBank ? (BANKS.includes(a.bank_name) ? a.bank_name : '__other') : '',
    otherBank: isBank && !BANKS.includes(a.bank_name) ? a.bank_name || '' : '',
    account_name: a?.account_name || '',
    account_number: a?.account_number || '',
  })
  numberTouched.value = false
  for (const k of Object.keys(formErrors)) delete formErrors[k]
  editing.value = true
}
async function saveAccount() {
  for (const k of Object.keys(formErrors)) delete formErrors[k]
  if (!form.account_name.trim()) formErrors.account_name = 'Enter the name on the account.'
  numberTouched.value = true
  if (numberError.value) formErrors.account_number = numberError.value
  if (form.kind === 'bank' && !formBank.value) formErrors.bank_name = form.bankChoice === '__other' ? 'Type the name of your bank.' : 'Choose your bank.'
  if (Object.keys(formErrors).length) return
  saving.value = true
  try {
    account.value = await put('/rnd/payout-account/', {
      method: formMethod.value, account_name: form.account_name.trim(), account_number: form.account_number.trim(),
      bank_name: form.kind === 'bank' ? formBank.value : '',
    })
    editing.value = false
    e.value = await get('/rnd/earnings/')
    flash('Payout details saved.')
  } catch (err) {
    const data = err?.data || {}
    for (const k of ['account_name', 'account_number', 'bank_name']) if (data[k]) formErrors[k] = Array.isArray(data[k]) ? data[k][0] : data[k]
    if (!Object.keys(formErrors).length) formErrors.detail = apiError(err, 'Could not save. Please try again.')
  } finally {
    saving.value = false
  }
}

function flash(text) {
  toast.value = text
  setTimeout(() => { toast.value = '' }, 3500)
}
const pad = n => String(n).padStart(4, '0')
const peso0 = v => `₱${Number(v || 0).toLocaleString('en-PH', { maximumFractionDigits: 0 })}`
const PH = { timeZone: 'Asia/Manila' }
function when(v) {
  return v ? new Date(v).toLocaleString('en-PH', { ...PH, month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }) : '—'
}
function longDate(v) {
  if (!v) return ''
  const d = /^\d{4}-\d{2}-\d{2}$/.test(v) ? new Date(`${v}T00:00:00`) : new Date(v)
  return d.toLocaleDateString('en-PH', { weekday: 'long', month: 'long', day: 'numeric' })
}
</script>

<style scoped>
/* STATEMENT: the page's one feature. Money figures in the display serif, digits aligned. */
.statement {
  padding: 0; overflow: hidden; margin-bottom: 24px;
  /* same dark-green shadow as the patient chart header, all around */
  box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
}
.st-head { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 22px 24px 20px; }
.st-title { font-family: 'Playfair Display', serif; font-size: 1.3rem; color: #1a3a1a; margin: 0 0 6px; }
/* the header is the dashboard's green banner (same gradient as .nm-hero); the figures below stay light */
.statement .st-head { background: linear-gradient(135deg, #00382a 0%, #005a42 100%); }
.statement .st-title { color: #fff; }
.statement .st-sub { color: #cfe0d5; }
.statement .st-account { color: rgba(255, 255, 255, 0.85); }
.statement .st-figures { border-top: none; }
.st-sub { font-size: 0.88rem; color: #4a5a4a; line-height: 1.55; margin: 0; max-width: 62ch; }
.st-head .nm-btn-gold { flex-shrink: 0; text-decoration: none; }
.st-account { flex-shrink: 0; display: flex; align-items: center; gap: 12px; font-size: 0.86rem; color: #4a5a4a; margin: 0; }
.st-figures { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 1fr); border-top: 1px solid #eef1ee; background: #fbfcfa; }
.st-flow { display: flex; align-items: stretch; }
.st-flow .fig { flex: 1; }
.fig { padding: 18px 24px 20px; min-width: 0; }
.fig-month { border-left: 1px solid #d9e3dc; }
/* visible dividers between On hold, Cleared and Paid out; the arrow sits on the line */
.st-flow .fig + .fig-arrow + .fig { border-left: 1px solid #d9e3dc; }
.fig-arrow { flex-shrink: 0; align-self: center; color: #8fa996; margin: 0 -11px; position: relative; z-index: 1; background: #fbfcfa; border-radius: 50%; box-sizing: content-box; padding: 2px; }
.fig-label { font-size: 0.8rem; font-weight: 600; color: #4a5a4a; margin: 0 0 6px; }
.fig-value { font-family: 'Playfair Display', serif; font-size: 1.55rem; font-weight: 700; color: #1a3a1a; margin: 0; font-variant-numeric: tabular-nums lining-nums; white-space: nowrap; }
.fig-note { font-size: 0.76rem; color: #7a8a7a; margin: 4px 0 0; }
.pager { display: flex; justify-content: center; align-items: center; gap: 12px; margin-top: 18px; }
.pager-num { font-size: 0.84rem; color: #4a5a4a; font-variant-numeric: tabular-nums; white-space: nowrap; }
.result-count { font-size: 0.84rem; color: #5a6a5a; margin: 6px 0 10px; }
.lower .pager { margin-top: auto; padding-top: 14px; }
.empty-line { font-size: 0.86rem; color: #6a7a6a; margin: 14px 0 4px; }
.lower { margin-top: 20px; align-items: stretch; }
/* Payouts sits beside the taller chart: same height, so no gap under it */
.lower > .nm-panel { display: flex; flex-direction: column; }
.payout-row { display: flex; align-items: center; gap: 12px; width: 100%; text-align: left; background: none; border: none; border-top: 1px solid #f0f2f0; padding: 12px 0; cursor: pointer; font-family: inherit; color: inherit; }
.payout-row:first-of-type { margin-top: 12px; }
.payout-row:hover .nm-row-title { color: #1f8f5c; }
.payout-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.chev { color: #c5d0c5; flex-shrink: 0; }
.chart { display: flex; align-items: flex-end; gap: 10px; height: 180px; margin-top: 18px; }
.bar-col { flex: 1; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; gap: 4px; min-width: 0; }
.bar { width: 70%; background: #1f8f5c; border-radius: 5px 5px 0 0; }
.bar-val { font-size: 0.66rem; color: #6a7a6a; white-space: nowrap; }
.bar-label { font-size: 0.74rem; color: #8a9a8a; }
.pd-modal { position: relative; max-width: 460px; }
.pd-fields { display: flex; flex-direction: column; gap: 12px; }
.pd-other { margin-top: 8px; }
.pd-count { margin: 4px 0 0; font-variant-numeric: tabular-nums; }
.pd-methods { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.pd-method { display: inline-flex; align-items: center; gap: 8px; border: 1px solid #d5dad5; border-radius: 10px; padding: 9px 14px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.pd-method.on { border-color: #1f8f5c; background: #f2f9f4; }
.pd-method input { accent-color: #163a1c; }
/* saved payout details */

/* invoice pop-up */
.inv { max-width: 460px; }
.inv-head { display: flex; align-items: flex-start; gap: 12px; }
.inv-who { flex: 1; min-width: 0; }
.inv-title { font-family: 'Playfair Display', serif; font-size: 1.35rem; font-weight: 700; line-height: 1.2; color: #1a3a1a; margin: 0 0 4px; }
.inv-sub { font-size: 0.82rem; color: #6a7a6a; margin: 0; line-height: 1.45; }
.inv-head .nm-pill { margin-top: 4px; flex-shrink: 0; }
.inv-money { margin-top: 18px; padding: 4px 0; border-top: 1px solid #eef1ee; border-bottom: 1px solid #eef1ee; }
.inv-money p { display: flex; justify-content: space-between; gap: 12px; margin: 0; padding: 8px 0; font-size: 0.88rem; color: #4a5a4a; font-variant-numeric: tabular-nums; }
.inv-total { font-weight: 700; color: #1a3a1a !important; font-size: 1rem !important; }
.inv-total span:last-child { font-family: 'Playfair Display', serif; font-size: 1.2rem; }
.inv-total .void { text-decoration: line-through; color: #9aaa9a; }
.inv-steps { list-style: none; margin: 18px 0 0; padding: 0; }
.inv-steps li { position: relative; display: flex; gap: 12px; padding-bottom: 14px; }
.inv-steps li:last-child { padding-bottom: 0; }
.inv-steps li:not(:last-child)::after { content: ''; position: absolute; left: 5px; top: 14px; bottom: 0; width: 2px; background: #e3e9e4; }
.inv-steps li.done:not(:last-child)::after { background: #1f8f5c; }
.inv-steps .dot { width: 12px; height: 12px; border-radius: 50%; margin-top: 3px; flex-shrink: 0; border: 2px solid #c9d4cb; background: #fff; position: relative; z-index: 1; }
.inv-steps .done .dot { background: #1f8f5c; border-color: #1f8f5c; }
.inv-steps .next .dot { border-color: #D4A017; box-shadow: 0 0 0 3px rgba(212,160,23,0.18); }
.st-text { display: flex; flex-direction: column; gap: 1px; font-size: 0.82rem; color: #6a7a6a; }
.st-text strong { font-size: 0.88rem; font-weight: 600; color: #1a3a1a; }
.later .st-text strong { color: #7a8a7a; font-weight: 500; }
.inv-note { font-size: 0.82rem; color: #5a6a5a; line-height: 1.5; margin: 18px 0 0; padding-top: 14px; border-top: 1px solid #eef1ee; }
.md-head { display: flex; align-items: flex-start; gap: 12px; }
.md-head > div { flex: 1; }
.close-btn { background: none; border: none; color: #8a9a8a; cursor: pointer; padding: 4px; }
.breakdown { margin-top: 16px; border: 1px solid #eceeec; border-radius: 10px; padding: 4px 14px; }
.breakdown p { display: flex; justify-content: space-between; margin: 0; padding: 9px 0; font-size: 0.86rem; color: #4a5a4a; }
.breakdown p + p { border-top: 1px solid #f0f2f0; }
.breakdown .total { font-weight: 700; color: #1a3a1a; font-size: 0.95rem; }
.wide-modal { max-width: 640px; }
.sub-title { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 18px 0 8px; }
@media (max-width: 900px) {
  .st-figures { grid-template-columns: minmax(0, 1fr); }
  .fig-month { border-left: none; border-top: 1px solid #d9e3dc; }
}
@media (max-width: 640px) {
  .st-head { flex-direction: column; padding: 18px 16px; }
  .st-head .nm-btn-gold { align-self: stretch; justify-content: center; }
  /* 2 x 2 on phones; the order still reads on hold, cleared, paid out */
  .st-figures { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .st-flow { display: contents; }
  .fig-arrow { display: none; }
  .fig { padding: 14px 16px; }
  /* lines follow the 2 x 2 grid: one between the columns, one between the rows */
  .st-flow .fig + .fig-arrow + .fig:nth-of-type(3) { border-left: none; border-top: 1px solid #d9e3dc; }
  .fig-month { border-left: 1px solid #d9e3dc; border-top: 1px solid #d9e3dc; }
  .fig-value { font-size: 1.2rem; }
  .st-head { align-items: stretch; }
  .chart { gap: 4px; }
  .bar-val { display: none; }
}
</style>
