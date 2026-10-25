<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- THE RUN SHEET: payout day, what's ready, and how money gets there -->
    <section class="nm-panel run-sheet">
      <div class="run-day">
        <CalendarClock :size="20" class="run-day-icon" aria-hidden="true" />
        <div>
          <h2 class="run-day-title">{{ run ? dayTitle : 'Loading…' }}</h2>
          <p class="run-day-sub">{{ daySub }}</p>
        </div>
        <!-- the month between two payout days, with today on it -->
        <div v-if="cycle" class="cycle">
          <p class="cycle-left"><strong>{{ daysLeft === 0 ? 'Today' : daysLeft }}</strong>{{ daysLeft === 0 ? '' : ` day${daysLeft === 1 ? '' : 's'} to go` }}</p>
          <div class="cycle-bar" role="img" :aria-label="`${cycle.pct}% of the way from ${cycle.from} to ${cycle.to}`">
            <span class="cycle-fill" :style="{ width: `${cycle.pct}%` }"></span>
            <span class="cycle-now" :style="{ left: `${cycle.pct}%` }"></span>
          </div>
          <div class="cycle-ends"><span>{{ cycle.from }}</span><span>{{ cycle.to }}</span></div>
        </div>
      </div>
      <div class="run-figs">
        <div class="fig">
          <strong>{{ peso(run?.due_total ?? 0) }}</strong>
          <span class="fig-label">Ready to send</span>
          <span class="fig-note">{{ dueRows.length }} RND{{ dueRows.length === 1 ? '' : 's' }}</span>
        </div>
        <div class="fig">
          <strong :class="{ warn: heldTotal > 0 }">{{ peso(heldTotal) }}</strong>
          <span class="fig-label">Cleared, waiting</span>
          <span class="fig-note" :class="{ warn: heldRows.length }">{{ heldRows.length ? `${heldRows.length} RND${heldRows.length === 1 ? '' : 's'}, see why below` : 'Nothing waiting' }}</span>
        </div>
        <div class="fig">
          <strong>{{ peso(pendingTotal) }}</strong>
          <span class="fig-label">On hold</span>
          <span class="fig-note">Clears {{ run?.hold_days ?? 3 }} days after the consultation</span>
        </div>
      </div>

      <!-- how a consultation's share moves: a real sequence -->
      <ol class="flow" aria-label="How an RND's share is paid">
        <li><strong>On hold</strong><span>until {{ run?.hold_days ?? 3 }} days after the consultation is completed, in case the client needs a refund</span></li>
        <li><strong>Cleared</strong><span>paid on the {{ ordinal(payoutDay) }} if it's {{ peso(run?.minimum_payout ?? 500) }} or more, otherwise it carries over</span></li>
        <li><strong>Paid out</strong><span>you send it by GCash or bank, then record the reference here</span></li>
      </ol>
    </section>

    <div class="nm-toolbar">
      <div class="nm-tabs">
        <button type="button" class="nm-tab" :class="{ active: tab === 'run' }" @click="tab = 'run'">This month <span class="nm-count">{{ rows.length }}</span></button>
        <button type="button" class="nm-tab" :class="{ active: tab === 'history' }" @click="tab = 'history'">History <span class="nm-count">{{ history.length }}</span></button>
      </div>
    </div>

    <!-- THIS MONTH: ready, waiting, then still on hold -->
    <template v-if="tab === 'run'">
      <p v-if="loading" class="nm-panel nm-muted">Loading balances…</p>
      <div v-else-if="!rows.length" class="nm-panel nm-empty">
        <Wallet :size="28" aria-hidden="true" />
        <p>No RND has earnings yet.</p>
      </div>
      <template v-else>
        <section v-for="g in groups" :key="g.key" class="nm-panel group">
          <div class="group-head">
            <h3 class="group-title">{{ g.title }} <span class="group-count">{{ g.rows.length }}</span></h3>
            <p class="group-sub">{{ g.sub }}</p>
          </div>
          <p v-if="!g.rows.length" class="nm-muted group-empty">{{ g.empty }}</p>
          <div v-for="r in g.rows" :key="r.rnd_id" class="payee" :class="g.key">
            <NuxtLink :to="`/users/${r.rnd_id}`" class="payee-who">
              <img v-if="r.profile_photo" :src="r.profile_photo" class="nm-avatar" alt="" />
              <span v-else class="nm-avatar">{{ nameInitials(r.rnd_name) }}</span>
              <span class="payee-name">
                <span class="nm-row-title">{{ r.rnd_name }}</span>
                <span class="nm-row-sub">{{ r.email }}</span>
              </span>
            </NuxtLink>

            <div class="payee-money">
              <strong class="mono">{{ peso(g.key === 'later' ? r.pending : g.key === 'ready' ? r.payable : r.posted) }}</strong>
              <span>{{ moneyLine(r, g.key) }}</span>
            </div>

            <div class="payee-to">
              <template v-if="r.payout_account">
                <span class="to-method">{{ payoutVia(r.payout_account.method, r.payout_account.bank_name) }}</span>
                <span class="to-line">{{ r.payout_account.account_name }}, <span class="mono">{{ r.payout_account.account_number }}</span></span>
              </template>
              <span v-else class="nm-pill gold no-details">No payout details yet, waits until added</span>
            </div>

            <div class="payee-act">
              <button v-if="r.eligible" type="button" class="nm-btn-dark nm-btn-sm" @click="openRelease(r)">Release {{ peso(r.payable) }}</button>
              <span v-else-if="g.key === 'held' && r.payout_account" class="held-why">{{ r.reason }}</span>
            </div>
          </div>
        </section>
      </template>
    </template>

    <!-- HISTORY: grouped by payout month -->
    <div v-else class="nm-panel">
      <div v-if="!history.length" class="nm-empty">
        <Wallet :size="28" aria-hidden="true" />
        <p>No payouts released yet.</p>
      </div>
      <section v-for="m in historyMonths" :key="m.key" class="month">
        <h3 class="month-title"><span>{{ m.label }}</span><span class="mono">{{ peso(m.total) }}</span></h3>
        <button v-for="p in m.items" :key="p.id" type="button" class="paid-row" :aria-label="`Open payout ${payoutNo(p)} to ${p.rnd_name}`" @click="openSlip(p)">
          <span class="paid-date">{{ shortDate(p.released_at) }}</span>
          <span class="paid-who">
            <span class="paid-name">{{ p.rnd_name }}</span>
            <span class="nm-row-sub">{{ p.invoice_count }} consultation{{ p.invoice_count === 1 ? '' : 's' }}, sent to {{ methodText(p) }}</span>
          </span>
          <span class="paid-ref">
            <span class="mono">{{ p.reference }}</span>
            <span class="nm-row-sub">{{ p.released_by_name ? `Recorded by ${p.released_by_name}` : '' }}</span>
          </span>
          <strong class="paid-amount mono">{{ peso(p.amount) }}</strong>
          <ChevronRight :size="16" class="paid-go" aria-hidden="true" />
        </button>
      </section>
      <ListPager v-model:page="page" :pages="pages" />
    </div>

    <!-- PAYOUT SLIP: what was paid, where it went, and the consultations it covered -->
    <div v-if="slip" class="nm-modal-overlay" @click.self="slip = null">
      <div class="nm-modal slip" role="dialog" aria-modal="true" aria-labelledby="slip-title">
        <div class="slip-head nm-modal-head">
          <div>
            <h3 id="slip-title" class="nm-modal-title mono">{{ payoutNo(slip) }}</h3>
            <p class="nm-panel-sub">Recorded {{ dateTime(slip.released_at) }}{{ slip.released_by_name ? `, by ${slip.released_by_name}` : '' }}</p>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="slip = null"><X :size="18" aria-hidden="true" /></button>
        </div>

        <div class="send">
          <p class="send-amount mono">{{ peso(slip.amount) }}</p>
          <p class="send-for">to {{ slip.rnd_name }}, for the {{ longDay(slip.payout_date) }} payout</p>
          <dl class="send-rows">
            <div><dt>Sent by</dt><dd>{{ payoutVia(slip.method, slip.bank_name) }}</dd></div>
            <div><dt>Account name</dt><dd>{{ slip.account_name }}</dd></div>
            <div><dt>Account number</dt><dd class="mono">{{ slip.account_number }}</dd></div>
            <div>
              <dt>Receipt reference</dt>
              <dd>
                <span class="mono">{{ slip.reference }}</span>
                <button type="button" class="nm-btn-soft nm-btn-sm copy" @click="copy(slip.reference)">
                  <component :is="copied ? Check : Copy" :size="13" aria-hidden="true" /> {{ copied ? 'Copied' : 'Copy' }}
                </button>
              </dd>
            </div>
          </dl>
        </div>
        <p v-if="slip.notes" class="nm-note plain-note slip-note">{{ slip.notes }}</p>

        <h4 class="slip-title">Consultations it covered</h4>
        <p v-if="!slip.invoices" class="nm-muted">Loading…</p>
        <p v-else-if="slipError" class="nm-error">{{ slipError }}</p>
        <template v-else>
          <div v-for="i in slip.invoices" :key="i.invoice_id" class="slip-line">
            <span class="slip-what">
              <span>{{ i.client_name }}</span>
              <span class="nm-row-sub">INV-{{ String(i.invoice_id).padStart(4, '0') }}<template v-if="i.consultation_at">, {{ shortDate(i.consultation_at) }}</template>, fee {{ peso(i.amount) }} less {{ peso(i.commission) }} commission</span>
            </span>
            <strong class="mono">{{ peso(i.share) }}</strong>
          </div>
          <div class="slip-line total"><span>Total paid out</span><strong class="mono">{{ peso(slip.amount) }}</strong></div>
        </template>

        <div class="nm-modal-actions">
          <NuxtLink :to="`/users/${slip.rnd}`" class="nm-btn-soft">View RND</NuxtLink>
          <button type="button" class="nm-btn-soft" :disabled="!slip.invoices" @click="printSlip"><Printer :size="14" aria-hidden="true" /> Print</button>
          <button type="button" class="nm-btn-dark" @click="slip = null">Done</button>
        </div>
      </div>
    </div>

    <!-- RELEASE: send first, then record it -->
    <div v-if="releasing" class="nm-modal-overlay" @click.self="busy ? null : (releasing = null)">
      <div class="nm-modal release" role="dialog" aria-modal="true" aria-labelledby="release-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="busy ? null : (releasing = null)"><X :size="18" aria-hidden="true" /></button>
        <h3 id="release-title" class="nm-modal-title">Pay {{ releasing.rnd_name }}</h3>

        <div class="send">
          <p class="send-amount mono">{{ peso(releasing.payable) }}</p>
          <p class="send-for">for {{ releasing.payable_count }} consultation{{ releasing.payable_count === 1 ? '' : 's' }} cleared by {{ runText }}</p>
          <dl class="send-rows">
            <div><dt>Send by</dt><dd>{{ payoutVia(releasing.payout_account.method, releasing.payout_account.bank_name) }}</dd></div>
            <div>
              <dt>Account name</dt>
              <dd>{{ releasing.payout_account.account_name }}</dd>
            </div>
            <div>
              <dt>Account number</dt>
              <dd>
                <span class="mono">{{ releasing.payout_account.account_number }}</span>
                <button type="button" class="nm-btn-soft nm-btn-sm copy" @click="copy(releasing.payout_account.account_number)">
                  <component :is="copied ? Check : Copy" :size="13" aria-hidden="true" /> {{ copied ? 'Copied' : 'Copy' }}
                </button>
              </dd>
            </div>
          </dl>
        </div>

        <!-- new or changed details: the classic payout fraud, so stop and check -->
        <div v-if="releasing.payout_account.recently_changed" class="changed" role="alert">
          <ShieldAlert :size="18" aria-hidden="true" />
          <p>
            <strong>These payout details {{ changedText }}.</strong>
            Before sending, confirm the number with {{ firstName }} on a channel you already trust (a call or Discord).
            If someone got into their account, they could have swapped the number.
          </p>
        </div>

        <ol class="steps">
          <li>Send {{ peso(releasing.payable) }} from the NutriMatch {{ payoutVia(releasing.payout_account.method, releasing.payout_account.bank_name) }} account.</li>
          <li>Copy the reference number from the receipt into the box below. {{ releasing.rnd_name.split(' ')[0] }} gets an email and a notification.</li>
        </ol>

        <label class="nm-label" for="payout-ref">Receipt reference number</label>
        <input id="payout-ref" v-model="reference" class="nm-input mono" maxlength="100" placeholder="For example: 1234 567 890123" aria-describedby="payout-ref-hint" />
        <p id="payout-ref-hint" class="nm-hint">
          <template v-if="['gcash', 'maya'].includes(releasing.payout_account.method)">After you send, {{ payoutVia(releasing.payout_account.method) }} shows a receipt with a "Ref. No." (about 13 digits). It proves the money went out.</template>
          <template v-else>After you send, the bank or app shows a reference or transaction number on the receipt. It proves the money went out.</template>
          Not the RND's account number.
        </p>
        <label class="nm-label" for="payout-notes" style="margin-top: 12px">Notes <span class="nm-muted">(optional)</span></label>
        <textarea id="payout-notes" v-model="notes" data-allow-emoji class="nm-input" rows="2" maxlength="500" />
        <label v-if="releasing.payout_account.recently_changed" class="confirm">
          <input v-model="detailsChecked" type="checkbox" />
          <span>I confirmed this {{ payoutVia(releasing.payout_account.method, releasing.payout_account.bank_name) }} number with {{ firstName }}.</span>
        </label>
        <label class="confirm">
          <input v-model="sentChecked" type="checkbox" />
          <span>I sent <strong>{{ peso(releasing.payable) }}</strong> to {{ payoutVia(releasing.payout_account.method, releasing.payout_account.bank_name) }} <span class="mono">{{ releasing.payout_account.account_number }}</span>. This can't be undone.</span>
        </label>
        <p v-if="releaseError" class="nm-field-error">{{ releaseError }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" :disabled="busy" @click="releasing = null">Not yet</button>
          <button type="button" class="nm-btn-dark" :disabled="busy || !canRecord" @click="release">
            {{ busy ? 'Recording…' : lockLeft > 0 ? `Record as paid out (${lockLeft})` : 'Record as paid out' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { payoutVia } from '~/utils/payout'
import { CalendarClock, Check, CheckCircle2, ChevronRight, Copy, Printer, ShieldAlert, Wallet, X } from 'lucide-vue-next'

const { get, post } = useApi()

const run = ref(null)
const history = ref([])
const loading = ref(true)
const error = ref('')
const tab = ref('run')
const releasing = ref(null)
const reference = ref('')
const notes = ref('')
const releaseError = ref('')
const busy = ref(false)
const toast = ref('')
const copied = ref(false)
const sentChecked = ref(false)
const detailsChecked = ref(false)
const lockLeft = ref(0)
let lockTimer
const firstName = computed(() => (releasing.value?.rnd_name || '').split(' ')[0])
const changedText = computed(() => {
  const at = releasing.value?.payout_account?.details_changed_at
  if (!at) return 'are new'
  const days = Math.floor((Date.now() - new Date(at)) / 86400000)
  return days < 1 ? 'were added or changed today' : `were added or changed ${days} day${days === 1 ? '' : 's'} ago`
})
// a payout can't be undone: tick what you did, and the button waits 3 seconds
const canRecord = computed(() => sentChecked.value && lockLeft.value <= 0
  && (!releasing.value?.payout_account?.recently_changed || detailsChecked.value))

const rows = computed(() => run.value?.rows || [])
const dueRows = computed(() => rows.value.filter(r => r.eligible))
const heldRows = computed(() => rows.value.filter(r => !r.eligible && Number(r.posted) > 0))
const laterRows = computed(() => rows.value.filter(r => !r.eligible && Number(r.posted) <= 0 && Number(r.pending) > 0))
const heldTotal = computed(() => rows.value.reduce((s, r) => s + Number(r.posted) - (r.eligible ? Number(r.payable) : 0), 0))
const pendingTotal = computed(() => rows.value.reduce((s, r) => s + Number(r.pending), 0))
const groups = computed(() => [
  { key: 'ready', title: 'Ready to release', sub: `Cleared by ${runText.value}, at least ${peso(run.value?.minimum_payout ?? 500)}, with payout details on file.`, empty: `Everyone from the ${runText.value} run is paid.`, rows: dueRows.value },
  { key: 'held', title: 'Waiting', sub: 'Cleared, but not paid in this run. Each says why.', empty: 'Nothing waiting.', rows: heldRows.value },
  { key: 'later', title: 'Still on hold', sub: 'Consultations inside the 3-day hold. Nothing to pay yet.', empty: 'Nothing on hold.', rows: laterRows.value },
].filter(g => g.key !== 'later' || g.rows.length))

const payoutDay = computed(() => run.value ? new Date(`${run.value.next_payout_date}T00:00:00+08:00`).getDate() : 5)
const daysLeft = computed(() => {
  if (!run.value) return null
  const today = new Date(new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' }))
  const day = new Date(run.value.next_payout_date)
  return Math.round((day - today) / 86400000)
})
const dayTitle = computed(() => {
  const d = new Date(`${run.value.next_payout_date}T00:00:00+08:00`).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' })
  return daysLeft.value === 0 ? `Payout day is today, ${d}` : `Next payout day: ${d}`
})
// the run that can be paid now: the last 5th (no early payouts, user's rule 2026-10-26)
const runText = computed(() => run.value
  ? new Date(`${run.value.run_date}T00:00:00+08:00`).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', month: 'short', day: 'numeric' })
  : '')
const nextText = computed(() => run.value
  ? new Date(`${run.value.next_payout_date}T00:00:00+08:00`).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', month: 'short', day: 'numeric' })
  : '')
const daySub = computed(() => {
  if (!run.value) return ''
  if (daysLeft.value === 0) return 'Pay everything cleared by today, then record each one.'
  const n = dueRows.value.length
  if (n) return `${n} RND${n === 1 ? '' : 's'} still to be paid from the ${runText.value} run. Money cleared after ${runText.value} is paid on ${nextText.value}.`
  return `Everyone from the ${runText.value} run is paid. Money cleared since then is paid on ${nextText.value}.`
})
// from the last payout day to the next one, and how far along today is
const cycle = computed(() => {
  if (!run.value) return null
  const next = new Date(`${run.value.next_payout_date}T00:00:00+08:00`)
  const prev = new Date(next)
  prev.setMonth(prev.getMonth() - 1)
  const fmt = d => d.toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', month: 'short', day: 'numeric' })
  const total = Math.round((next - prev) / 86400000)
  const pct = Math.min(100, Math.max(0, Math.round(((total - daysLeft.value) / total) * 100)))
  return { from: fmt(prev), to: fmt(next), pct }
})
function ordinal(n) {
  const end = n % 100 >= 11 && n % 100 <= 13 ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th')
  return `${n}${end}`
}
function moneyLine(r, key) {
  const posted = `${r.posted_count} consultation${r.posted_count === 1 ? '' : 's'} cleared`
  if (key === 'later') {
    const when = r.next_posts_on ? `, the first clears ${shortDate(r.next_posts_on)}` : ''
    return `${r.pending_count} on hold${when}`
  }
  if (key === 'ready') {
    const waits = Number(r.posted) - Number(r.payable)
    const line = `${r.payable_count} consultation${r.payable_count === 1 ? '' : 's'} cleared by ${runText.value}`
    return waits > 0 ? `${line}, ${peso(waits)} waits for ${nextText.value}` : line
  }
  return Number(r.pending) > 0 ? `${posted}, ${peso(r.pending)} still on hold` : posted
}

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    const [r, h] = await Promise.all([get('/admin/payouts/run/'), get('/admin/payouts/')])
    run.value = r
    history.value = Array.isArray(h) ? h : h?.results || []
  } catch {
    if (!quiet) error.value = 'Could not load payouts. Refresh the page to try again.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
useAutoRefresh(() => load({ quiet: true }))

// history: 20 payouts a page, shown under their month
const { page, pages, paged: pagedHistory } = usePager(history, { perPage: 20 })
const historyMonths = computed(() => {
  const out = []
  for (const p of pagedHistory.value) {
    const d = new Date(p.released_at)
    const key = d.toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' }).slice(0, 7)
    let m = out[out.length - 1]
    if (!m || m.key !== key) {
      m = { key, label: d.toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', month: 'long', year: 'numeric' }), total: 0, items: [] }
      out.push(m)
    }
    m.items.push(p)
    m.total += Number(p.amount)
  }
  return out
})

function openRelease(r) {
  releasing.value = r
  reference.value = ''
  notes.value = ''
  releaseError.value = ''
  copied.value = false
  sentChecked.value = false
  detailsChecked.value = false
  lockLeft.value = 3
  clearInterval(lockTimer)
  lockTimer = setInterval(() => {
    lockLeft.value -= 1
    if (lockLeft.value <= 0) clearInterval(lockTimer)
  }, 1000)
}
onBeforeUnmount(() => clearInterval(lockTimer))
async function copy(text) {
  try {
    await navigator.clipboard.writeText(text)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    copied.value = false
  }
}

async function release() {
  releaseError.value = ''
  if (!reference.value.trim()) {
    releaseError.value = 'Enter the GCash or bank reference number so the payment can be traced.'
    return
  }
  busy.value = true
  try {
    const p = await post(`/admin/payouts/release/${releasing.value.rnd_id}/`, {
      reference: reference.value.trim(),
      notes: notes.value.trim(),
      // the amount this pop-up showed; the API refuses if it changed meanwhile
      expected_amount: String(releasing.value.payable),
      details_confirmed: detailsChecked.value,
    })
    releasing.value = null
    await load()
    toast.value = `${peso(p.amount)} recorded as paid out to ${p.rnd_name}.`
    setTimeout(() => { toast.value = '' }, 3000)
  } catch (e) {
    releaseError.value = apiError(e)
  } finally {
    busy.value = false
  }
}

function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}
/* payout slip (History) */
const slip = ref(null)
const slipError = ref('')
const payoutNo = p => `PO-${String(p.id).padStart(4, '0')}`
const longDay = d => new Date(`${d}T00:00:00+08:00`).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', month: 'long', day: 'numeric', year: 'numeric' })
async function openSlip(p) {
  slip.value = { ...p, invoices: null }
  slipError.value = ''
  copied.value = false
  try {
    const d = await get(`/admin/payouts/${p.id}/`)
    if (slip.value?.id === p.id) slip.value = d
  } catch (e) {
    if (slip.value?.id === p.id) {
      slipError.value = apiError(e, 'Could not load this payout. Try again.')
      slip.value = { ...slip.value, invoices: [] }
    }
  }
}
function printSlip() {
  const p = slip.value
  const ok = printDocument({
    title: 'Payout slip',
    number: `${payoutNo(p)}, ${shortDate(p.released_at)}`,
    rows: [['Paid to', `${p.rnd_name} (${p.account_name})`], ['Sent by', `${payoutVia(p.method, p.bank_name)}, ${p.account_number}`],
      ['Receipt reference', p.reference], ['Payout day', longDay(p.payout_date)], ['Recorded by', p.released_by_name || 'NutriMatch']],
    table: [['Invoice', 'Client', 'Consultation', 'Fee', 'Commission', 'RND share'],
      ...p.invoices.map(i => [`INV-${String(i.invoice_id).padStart(4, '0')}`, i.client_name, i.consultation_at ? shortDate(i.consultation_at) : '—', peso(i.amount), peso(i.commission), peso(i.share)])],
    total: ['Total paid out', peso(p.amount)],
    note: p.notes || '',
  })
  if (!ok) {
    toast.value = 'Allow pop-ups for this site to print the slip.'
    setTimeout(() => { toast.value = '' }, 3000)
  }
}

function methodText(p) {
  return `${payoutVia(p.method, p.bank_name)} ${p.account_number}`
}
</script>

<style scoped>
.mono { font-variant-numeric: tabular-nums; }

/* run sheet */
.run-sheet { margin-bottom: 20px; padding: 0; overflow: hidden; }
/* the payout day: the green banner, like the dashboards */
.run-day {
  display: flex; gap: 12px; align-items: center; padding: 22px 24px 20px;
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%); color: #fff;
}
.run-day > div:nth-child(2) { flex: 1; min-width: 0; }
.cycle { width: 260px; flex-shrink: 0; }
.cycle-left { margin: 0 0 8px; text-align: right; font-size: 0.8rem; color: rgba(255, 255, 255, 0.78); }
.cycle-left strong { font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #D4A017; margin-right: 4px; font-variant-numeric: tabular-nums; }
.cycle-bar { position: relative; height: 8px; border-radius: 999px; background: rgba(255, 255, 255, 0.16); }
.cycle-fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 999px; background: rgba(255, 255, 255, 0.55); }
.cycle-now { position: absolute; top: 50%; width: 14px; height: 14px; margin-left: -7px; transform: translateY(-50%); border-radius: 50%; background: #D4A017; border: 2px solid #00382a; }
.cycle-ends { display: flex; justify-content: space-between; margin-top: 6px; font-size: 0.72rem; color: rgba(255, 255, 255, 0.7); }
.run-day-icon { color: #D4A017; margin-top: 3px; flex-shrink: 0; }
.run-day-title { margin: 0; font-family: 'Playfair Display', serif; font-size: 1.3rem; color: #fff; }
.run-day-sub { margin: 4px 0 0; font-size: 0.82rem; color: rgba(255, 255, 255, 0.78); }
.run-figs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border-bottom: 1px solid #d9e3dc; }
.fig { display: flex; flex-direction: column; gap: 2px; padding: 14px 22px; border-left: 1px solid #d9e3dc; min-width: 0; }
.fig:first-child { border-left: none; }
.fig strong { font-family: 'Playfair Display', serif; font-size: 1.45rem; color: #1a3a1a; font-variant-numeric: tabular-nums; }
.fig strong.warn { color: #b8860b; }
.fig-label { font-size: 0.82rem; font-weight: 600; color: #4a5a4a; }
.fig-note { font-size: 0.75rem; color: #8a9a8a; }
.fig-note.warn { color: #b8860b; font-weight: 600; }

.flow { list-style: none; margin: 0; padding: 14px 22px 16px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; background: #f7faf8; counter-reset: step; }
.flow li { position: relative; display: flex; flex-direction: column; gap: 2px; padding-left: 26px; font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; counter-increment: step; }
.flow li::before {
  content: counter(step); position: absolute; left: 0; top: 0; width: 18px; height: 18px; border-radius: 50%;
  background: #0a4a37; color: #fff; font-size: 0.68rem; font-weight: 700; display: flex; align-items: center; justify-content: center;
}
.flow strong { font-size: 0.84rem; color: #1a3a1a; }

/* groups of payees */
.group + .group { margin-top: 16px; }
.group-head { margin-bottom: 6px; }
.group-title { margin: 0; font-family: inherit; font-size: 0.95rem; font-weight: 700; color: #1a3a1a; display: flex; align-items: baseline; gap: 8px; }
.group-count { font-size: 0.76rem; font-weight: 600; color: #8a9a8a; }
.group-sub { margin: 2px 0 0; font-size: 0.8rem; color: #8a9a8a; }
.group-empty { margin: 10px 0 0; font-size: 0.84rem; }
.payee {
  display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr) minmax(0, 1.2fr) auto; align-items: center; gap: 16px;
  padding: 14px 0; border-top: 1px solid #edf1ee;
}
.group-head + .payee { border-top-color: transparent; }
.payee-who { display: flex; align-items: center; gap: 10px; min-width: 0; text-decoration: none; }
.payee-name { display: flex; flex-direction: column; min-width: 0; }
.payee-money { display: flex; flex-direction: column; min-width: 0; }
.payee-money strong { font-size: 1.05rem; color: #1a3a1a; }
.payee.held .payee-money strong { color: #b8860b; }
.payee.later .payee-money strong { color: #6a7a6a; }
.payee-money span { font-size: 0.76rem; color: #8a9a8a; }
.payee-to { display: flex; flex-direction: column; min-width: 0; }
.no-details { align-self: flex-start; white-space: normal; }
.to-method { font-size: 0.8rem; font-weight: 700; color: #1a3a1a; }
.to-line { font-size: 0.77rem; color: #6a7a6a; overflow-wrap: anywhere; }
.payee-act { text-align: right; }
.held-why { font-size: 0.78rem; font-weight: 600; color: #7a560f; }

/* history */
.month + .month { margin-top: 18px; }
.month-title {
  display: flex; justify-content: space-between; gap: 12px; margin: 0 0 4px; padding-bottom: 8px; border-bottom: 1px solid #d9e3dc;
  font-family: inherit; font-size: 0.88rem; font-weight: 700; color: #0a4a37;
}
.paid-row {
  display: grid; grid-template-columns: 90px minmax(0, 1.6fr) minmax(0, 1fr) auto 16px; gap: 14px; align-items: center; width: 100%;
  padding: 11px 8px; margin: 0; border: 0; border-top: 1px solid #edf1ee; background: none; text-align: left; font-family: inherit; cursor: pointer; color: inherit;
}
.paid-row:hover { background: #f7faf8; }
.paid-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.paid-name { font-weight: 700; color: #1a3a1a; }
.paid-go { color: #9aaa9a; }
/* payout slip */
.slip { max-width: 540px; }
.slip-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.slip-head .nm-modal-x { position: static; float: none; margin: 0; }
.slip-note { margin: 14px 0 0; }
.slip-title { margin: 18px 0 6px; font-family: inherit; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.slip-line { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 9px 0; border-top: 1px solid #edf1ee; font-size: 0.86rem; }
.slip-what { display: flex; flex-direction: column; min-width: 0; }
.slip-line.total { border-top: 1px solid #d9e3dc; font-weight: 700; }
.month-title + .paid-row { border-top: none; }
.paid-date { font-size: 0.8rem; color: #6a7a6a; }
.paid-who, .paid-ref { display: flex; flex-direction: column; min-width: 0; font-size: 0.86rem; }
.paid-ref .mono { color: #1a3a1a; overflow-wrap: anywhere; }
.paid-amount { font-size: 0.95rem; color: #1a3a1a; text-align: right; }

/* release pop-up */
.release { max-width: 500px; }
.send { border: 1px solid #d9e3dc; border-radius: 12px; padding: 16px 18px; background: #f7faf8; }
.send-amount { margin: 0; font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 700; color: #0a4a37; }
.send-for { margin: 0 0 10px; font-size: 0.8rem; color: #6a7a6a; }
.send-rows { margin: 0; }
.send-rows > div { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 8px 0; border-top: 1px solid #e3ebe5; font-size: 0.86rem; }
.send-rows dt { color: #6a7a6a; }
.send-rows dd { margin: 0; color: #1a3a1a; font-weight: 600; display: flex; align-items: center; gap: 8px; text-align: right; overflow-wrap: anywhere; }
.copy { flex-shrink: 0; }
.changed {
  display: flex; gap: 10px; align-items: flex-start; margin: 16px 0 0; padding: 12px 14px; border-radius: 10px;
  background: #fdecec; border: 1px solid #f2c4c4; color: #7a1f1f; font-size: 0.83rem; line-height: 1.5;
}
.changed svg { flex-shrink: 0; margin-top: 2px; color: #a12525; }
.changed p { margin: 0; }
.confirm {
  display: flex; gap: 10px; align-items: flex-start; margin-top: 12px; padding: 10px 12px; border: 1px solid #d9e3dc;
  border-radius: 10px; font-size: 0.84rem; color: #1a3a1a; line-height: 1.45; cursor: pointer;
}
.confirm input { margin-top: 3px; accent-color: #0a4a37; flex-shrink: 0; }
.steps { list-style: decimal; margin: 16px 0 14px; padding-left: 20px; font-size: 0.84rem; color: #4a5a4a; line-height: 1.55; }
.steps li + li { margin-top: 4px; }

@media (max-width: 900px) {
  .payee { grid-template-columns: minmax(0, 1fr) auto; row-gap: 8px; }
  .payee-who { grid-column: 1 / -1; }
  .payee-act { grid-column: 1 / -1; text-align: left; }
  .paid-row { grid-template-columns: minmax(0, 1fr) auto; row-gap: 4px; }
  .paid-go { display: none; }
  .paid-date { grid-column: 1 / -1; }
  .paid-ref { grid-column: 1; }
  .paid-amount { grid-row: 2; grid-column: 2; }
}
@media (max-width: 640px) {
  .run-day { padding: 16px; flex-wrap: wrap; }
  .cycle { width: 100%; }
  .cycle-left { text-align: left; }
  .run-figs { grid-template-columns: minmax(0, 1fr); }
  .fig { border-left: none; padding: 12px 16px; }
  .fig + .fig { border-top: 1px solid #d9e3dc; }
  .flow { grid-template-columns: minmax(0, 1fr); padding: 14px 16px; gap: 12px; }
  .payee-act .nm-btn-dark { width: 100%; }
}
</style>
