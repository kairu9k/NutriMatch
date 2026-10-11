<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <p v-if="loading" class="nm-muted">Loading your earnings…</p>

    <template v-else-if="e">
      <!-- next payout -->
      <div class="nm-banner">
        <span class="nm-banner-badge">NEXT PAYOUT · {{ longDate(e.next_payout_date).toUpperCase() }}</span>
        <h1 class="nm-banner-title">{{ peso(e.posted) }} ready to be paid out</h1>
        <p class="nm-banner-sub">
          <template v-if="!e.payout_account">Add your GCash or bank details below so NutriMatch can send it — your balance is kept safe until then.</template>
          <template v-else-if="!e.eligible">Payouts need at least {{ peso(e.minimum_payout) }} posted. Smaller balances carry over to the next 5th.</template>
          <template v-else>It goes to your {{ accountText }} on the 5th.</template>
          A paid consultation stays <strong>Pending</strong> for {{ e.hold_days }} days after it's completed, then it's <strong>Posted</strong>.
        </p>
        <div class="nm-todo">
          <span class="nm-todo-item"><Wallet :size="14" /> {{ e.payout_account ? accountText : 'No payout details yet' }}</span>
          <a href="#payout-details" class="nm-todo-item">{{ e.payout_account ? 'Change' : 'Add payout details' }}</a>
        </div>
      </div>

      <div class="nm-stat-grid">
        <div class="nm-stat-card">
          <div class="nm-stat-icon gold"><Hourglass :size="17" /></div>
          <p class="nm-stat-value">{{ peso(e.pending) }}</p>
          <p class="nm-stat-label">Pending</p>
          <p class="nm-stat-note">Paid, on the {{ e.hold_days }}-day hold</p>
        </div>
        <div class="nm-stat-card">
          <div class="nm-stat-icon"><Wallet :size="17" /></div>
          <p class="nm-stat-value">{{ peso(e.posted) }}</p>
          <p class="nm-stat-label">Posted</p>
          <p class="nm-stat-note">For the {{ shortDate(e.next_payout_date) }} payout</p>
        </div>
        <div class="nm-stat-card">
          <div class="nm-stat-icon"><Landmark :size="17" /></div>
          <p class="nm-stat-value">{{ peso(e.paid_out) }}</p>
          <p class="nm-stat-label">Paid out</p>
          <p class="nm-stat-note">All time · {{ e.payouts.length }} payout{{ e.payouts.length === 1 ? '' : 's' }}</p>
        </div>
        <div class="nm-stat-card">
          <div class="nm-stat-icon gold"><TrendingUp :size="17" /></div>
          <p class="nm-stat-value">{{ peso(e.this_month.share) }}</p>
          <p class="nm-stat-label">Earned this month</p>
          <p class="nm-stat-note">From {{ peso(e.this_month.gross) }} in consultation fees</p>
        </div>
      </div>

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
            <p class="nm-panel-sub">What each consultation earns you: the fee, minus the platform commission frozen when the booking was confirmed.</p>
          </div>
        </div>
        <div v-if="!filtered.length" class="nm-empty"><Receipt :size="28" /><p>{{ e.statement.length ? 'Nothing here.' : 'No invoices yet — they appear when you confirm a booking.' }}</p></div>
        <div v-else class="nm-table-wrap">
          <table class="nm-table stack">
            <thead>
              <tr><th>Invoice</th><th>Patient</th><th class="nm-num">Fee</th><th class="nm-num">Commission</th><th class="nm-num">Your share</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr v-for="r in filtered" :key="r.invoice_id" class="clickable" @click="row = r">
                <td data-label="Invoice"><strong>INV-{{ pad(r.invoice_id) }}</strong></td>
                <td data-label="Patient">{{ r.client_name }}<span class="nm-row-sub" style="display: block">{{ r.consultation_type }} · {{ r.consultation_at ? shortDate(r.consultation_at) : '—' }}</span></td>
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
      </div>

      <div class="nm-grid-even lower">
        <!-- payouts -->
        <div class="nm-panel">
          <h2 class="nm-panel-title">Payouts</h2>
          <p class="nm-panel-sub">Sent on the 5th of each month.</p>
          <div v-if="!e.payouts.length" class="nm-empty"><Landmark :size="28" /><p>No payouts yet — your first one comes on a payout day once {{ peso(e.minimum_payout) }} is posted.</p></div>
          <button v-for="p in e.payouts" :key="p.id" type="button" class="payout-row" @click="openPayout(p)">
            <span class="nm-stat-icon" style="margin: 0"><Landmark :size="16" /></span>
            <span class="payout-main">
              <span class="nm-row-title">{{ peso(p.amount) }} · {{ p.invoice_count }} consultation{{ p.invoice_count === 1 ? '' : 's' }}</span>
              <span class="nm-row-sub">{{ shortDate(p.released_at) }} · {{ p.method === 'gcash' ? 'GCash' : (p.bank_name || 'Bank') }} •••• {{ String(p.account_number).slice(-4) }} · Ref {{ p.reference }}</span>
            </span>
            <ChevronRight :size="16" class="chev" />
          </button>
        </div>

        <!-- trend -->
        <div class="nm-panel">
          <h2 class="nm-panel-title">Your share, last 6 months</h2>
          <p class="nm-panel-sub">By the month the client paid.</p>
          <div class="chart">
            <div v-for="m in trend" :key="m.key" class="bar-col">
              <span class="bar-val">{{ m.amount ? peso0(m.amount) : '' }}</span>
              <span class="bar" :style="{ height: `${Math.max(2, (m.amount / maxTrend) * 100)}%` }" />
              <span class="bar-label">{{ m.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- payout details -->
      <div id="payout-details" class="nm-panel payout-details">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">Payout details</h2>
            <p class="nm-panel-sub">Where NutriMatch sends your earnings. Only the NutriMatch admin sees these.</p>
          </div>
          <button v-if="account && !editing" class="nm-btn-outline nm-btn-sm" @click="startEdit"><Pencil :size="13" /> Change</button>
        </div>
        <dl v-if="account && !editing" class="nm-dl">
          <div><dt>Method</dt><dd>{{ account.method === 'gcash' ? 'GCash' : 'Bank transfer' }}</dd></div>
          <div v-if="account.method === 'bank'"><dt>Bank</dt><dd>{{ account.bank_name }}</dd></div>
          <div><dt>Account name</dt><dd>{{ account.account_name }}</dd></div>
          <div><dt>{{ account.method === 'gcash' ? 'GCash number' : 'Account number' }}</dt><dd>{{ account.account_number }}</dd></div>
        </dl>
        <div v-else class="pd-form">
          <div class="pd-methods">
            <label class="pd-method" :class="{ on: form.method === 'gcash' }"><input v-model="form.method" type="radio" value="gcash" /> GCash</label>
            <label class="pd-method" :class="{ on: form.method === 'bank' }"><input v-model="form.method" type="radio" value="bank" /> Bank transfer</label>
          </div>
          <div class="pd-grid">
            <div v-if="form.method === 'bank'">
              <label class="nm-label" for="pd-bank">Bank</label>
              <input id="pd-bank" v-model="form.bank_name" class="nm-input" maxlength="100" placeholder="e.g. BDO, BPI, Landbank" />
              <p v-if="formErrors.bank_name" class="nm-field-error">{{ formErrors.bank_name }}</p>
            </div>
            <div>
              <label class="nm-label" for="pd-name">Account name</label>
              <input id="pd-name" v-model="form.account_name" class="nm-input" maxlength="150" placeholder="Name on the account" />
              <p v-if="formErrors.account_name" class="nm-field-error">{{ formErrors.account_name }}</p>
            </div>
            <div>
              <label class="nm-label" for="pd-number">{{ form.method === 'gcash' ? 'GCash number' : 'Account number' }}</label>
              <input id="pd-number" v-model="form.account_number" class="nm-input" inputmode="numeric" maxlength="30" :placeholder="form.method === 'gcash' ? '09XX XXX XXXX' : '6–20 digits'" />
              <p v-if="formErrors.account_number" class="nm-field-error">{{ formErrors.account_number }}</p>
            </div>
          </div>
          <p v-if="formErrors.detail" class="nm-field-error">{{ formErrors.detail }}</p>
          <div class="nm-modal-actions">
            <button v-if="account" class="nm-btn-outline" @click="editing = false">Cancel</button>
            <button class="nm-btn-dark" :disabled="saving" @click="saveAccount">{{ saving ? 'Saving…' : 'Save payout details' }}</button>
          </div>
        </div>
      </div>
    </template>

    <!-- consultation detail -->
    <div v-if="row" class="nm-modal-overlay" @click.self="row = null">
      <div class="nm-modal">
        <div class="md-head">
          <div>
            <p class="nm-section-title" style="margin: 0 0 4px">Invoice</p>
            <h3 class="nm-modal-title" style="margin: 0">INV-{{ pad(row.invoice_id) }}</h3>
          </div>
          <span class="nm-pill" :class="STATE[row.state]?.pill || 'muted'">{{ STATE[row.state]?.label }}</span>
          <button class="close-btn" aria-label="Close" @click="row = null"><X :size="18" /></button>
        </div>
        <dl class="nm-dl" style="margin-top: 14px">
          <div><dt>Patient</dt><dd>{{ row.client_name }}</dd></div>
          <div><dt>Consultation</dt><dd>{{ row.consultation_type }} · {{ row.consultation_at ? when(row.consultation_at) : '—' }}</dd></div>
          <div><dt>Issued</dt><dd>{{ when(row.issued_at) }}</dd></div>
          <div><dt>Client paid</dt><dd :class="{ muted: !row.paid_at }">{{ row.paid_at ? `${when(row.paid_at)}${row.payment_method ? ' · ' + row.payment_method : ''}` : 'Not yet' }}</dd></div>
          <div v-if="row.payout"><dt>Paid out</dt><dd>{{ shortDate(row.payout.released_at) }} · Ref {{ row.payout.reference }}</dd></div>
          <div v-else-if="row.posts_on"><dt>Posts on</dt><dd>{{ when(row.posts_on) }}</dd></div>
        </dl>
        <div class="breakdown">
          <p><span>Consultation fee</span><span>{{ peso(row.amount) }}</span></p>
          <p><span>Platform commission ({{ Number(row.commission_pct) }}%)</span><span>− {{ peso(row.commission) }}</span></p>
          <p class="total"><span>Your share</span><span>{{ peso(row.share) }}</span></p>
        </div>
        <p class="nm-hint">{{ stateExplain(row) }}</p>
      </div>
    </div>

    <!-- payout detail -->
    <div v-if="payout" class="nm-modal-overlay" @click.self="payout = null">
      <div class="nm-modal wide-modal">
        <div class="md-head">
          <div>
            <p class="nm-section-title" style="margin: 0 0 4px">Payout</p>
            <h3 class="nm-modal-title" style="margin: 0">{{ peso(payout.amount) }} · {{ shortDate(payout.released_at) }}</h3>
          </div>
          <button class="close-btn" aria-label="Close" @click="payout = null"><X :size="18" /></button>
        </div>
        <dl class="nm-dl" style="margin-top: 14px">
          <div><dt>Sent to</dt><dd>{{ payout.method === 'gcash' ? 'GCash' : (payout.bank_name || 'Bank') }} · {{ payout.account_name }} · {{ payout.account_number }}</dd></div>
          <div><dt>Reference</dt><dd>{{ payout.reference }}</dd></div>
        </dl>
        <p class="nm-section-title">Consultations in this payout</p>
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
  CheckCircle2, ChevronRight, Hourglass, Landmark, Mail, Pencil, Printer, Receipt, Search, TrendingUp, Wallet, X,
} from 'lucide-vue-next'

const { get, put, post } = useApi()

const STATE = {
  awaiting_payment: { label: 'Awaiting payment', pill: 'gold' },
  pending: { label: 'Pending', pill: 'gold' },
  posted: { label: 'Posted', pill: 'green' },
  paid_out: { label: 'Paid out', pill: 'blue' },
  refund_pending: { label: 'Being refunded', pill: 'red' },
  refunded: { label: 'Refunded', pill: 'muted' },
  voided: { label: 'Voided', pill: 'muted' },
}
const TABS = [
  { key: 'all', label: 'All' },
  { key: 'awaiting_payment', label: 'Awaiting payment' },
  { key: 'pending', label: 'Pending' },
  { key: 'posted', label: 'Posted' },
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

async function load() {
  error.value = ''
  try {
    const [earnings, acc] = await Promise.all([get('/rnd/earnings/'), get('/rnd/payout-account/').catch(() => null)])
    e.value = earnings
    account.value = acc && acc.method ? acc : null
    editing.value = !account.value
  } catch {
    error.value = 'Could not load your earnings.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const accountText = computed(() => {
  const a = e.value?.payout_account
  if (!a) return ''
  return `${a.method === 'gcash' ? 'GCash' : (a.bank_name || 'bank account')} •••• ${a.account_number_last4}`
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
const countsAsEarning = r => ['pending', 'posted', 'paid_out'].includes(r.state)

function stateDetail(r) {
  if (r.state === 'awaiting_payment') return 'Client pays before the consultation'
  if (r.state === 'pending') return r.posts_on ? `Posts ${shortDate(r.posts_on)}` : 'Posts 3 days after it\'s completed'
  if (r.state === 'posted') return `For the ${shortDate(e.value.next_payout_date)} payout`
  if (r.state === 'paid_out') return r.payout ? `Paid ${shortDate(r.payout.released_at)}` : ''
  if (r.state === 'refund_pending') return 'Cancelled after paying'
  return ''
}
function stateExplain(r) {
  return {
    awaiting_payment: 'The client hasn\'t paid yet. If it\'s still unpaid at the start time, the consultation is cancelled automatically.',
    pending: `Paid. It stays pending until ${e.value.hold_days} days after you mark the consultation complete, in case the client reports a problem.`,
    posted: `Cleared — it's included in the next payout on ${longDate(e.value.next_payout_date)}.`,
    paid_out: 'Sent to your payout account.',
    refund_pending: 'The consultation was cancelled after the client paid, so the client is being refunded. It doesn\'t count toward your earnings.',
    refunded: 'The client was refunded. It doesn\'t count toward your earnings.',
    voided: 'The consultation was cancelled before it was paid — nothing to pay out.',
  }[r.state] || ''
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
  const method = p.method === 'gcash' ? 'GCash' : (p.bank_name || 'Bank transfer')
  const ok = printDocument({
    title: 'Payout statement',
    number: `Payout #${p.id} · ${shortDate(p.released_at)}`,
    rows: [['Paid to', p.account_name], ['Sent via', `${method} · ${p.account_number}`], ['Reference', p.reference], ['Payout date', shortDate(p.payout_date)]],
    table: [['Invoice', 'Patient', 'Consultation', 'Fee', 'Your share'],
      ...p.invoices.map(i => [`INV-${pad(i.invoice_id)}`, i.client_name, i.consultation_at ? shortDate(i.consultation_at) : '—', peso(i.amount), peso(i.share)])],
    total: ['Total paid out', peso(p.amount)],
  })
  if (!ok) flash('Allow pop-ups for this site to print the statement.')
}

/* payout details (same rules as the API: GCash 09XXXXXXXXX, bank 6–20 digits) */
const account = ref(null)
const editing = ref(false)
const saving = ref(false)
const form = reactive({ method: 'gcash', account_name: '', account_number: '', bank_name: '' })
const formErrors = reactive({})
function startEdit() {
  Object.assign(form, { method: 'gcash', account_name: '', account_number: '', bank_name: '' }, account.value || {})
  for (const k of Object.keys(formErrors)) delete formErrors[k]
  editing.value = true
}
async function saveAccount() {
  for (const k of Object.keys(formErrors)) delete formErrors[k]
  if (!form.account_name.trim()) formErrors.account_name = 'Enter the name on the account.'
  if (!form.account_number.trim()) formErrors.account_number = form.method === 'gcash' ? 'Enter your GCash number.' : 'Enter your account number.'
  if (form.method === 'bank' && !form.bank_name.trim()) formErrors.bank_name = 'Enter your bank.'
  if (Object.keys(formErrors).length) return
  saving.value = true
  try {
    account.value = await put('/rnd/payout-account/', {
      method: form.method, account_name: form.account_name.trim(), account_number: form.account_number.trim(),
      bank_name: form.method === 'bank' ? form.bank_name.trim() : '',
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
.nm-banner-sub strong { color: #fff; }
.nm-todo-item { gap: 8px; }
.lower { margin-top: 20px; }
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
.payout-details { margin-top: 20px; scroll-margin-top: 80px; }
.pd-methods { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.pd-method { display: inline-flex; align-items: center; gap: 8px; border: 1px solid #d5dad5; border-radius: 10px; padding: 9px 14px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.pd-method.on { border-color: #1f8f5c; background: #f2f9f4; }
.pd-method input { accent-color: #163a1c; }
.pd-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.md-head { display: flex; align-items: flex-start; gap: 12px; }
.md-head > div { flex: 1; }
.close-btn { background: none; border: none; color: #8a9a8a; cursor: pointer; padding: 4px; }
.breakdown { margin-top: 16px; border: 1px solid #eceeec; border-radius: 10px; padding: 4px 14px; }
.breakdown p { display: flex; justify-content: space-between; margin: 0; padding: 9px 0; font-size: 0.86rem; color: #4a5a4a; }
.breakdown p + p { border-top: 1px solid #f0f2f0; }
.breakdown .total { font-weight: 700; color: #1a3a1a; font-size: 0.95rem; }
.wide-modal { max-width: 640px; }
@media (max-width: 640px) {
  .pd-grid { grid-template-columns: minmax(0, 1fr); }
  .chart { gap: 4px; }
  .bar-val { display: none; }
}
</style>
