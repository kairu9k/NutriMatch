<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-banner">
      <span class="nm-banner-badge">MONTHLY PAYOUT RUN</span>
      <h1 class="nm-banner-title">Next payout: {{ run ? shortDate(run.next_payout_date) : '—' }}</h1>
      <p class="nm-banner-sub">
        RNDs are paid every 5th of the month. A paid consultation is <strong>Pending</strong> for {{ run?.hold_days ?? 3 }} days
        after it's completed, then <strong>Posted</strong>. Posted balances of {{ peso(run?.minimum_payout ?? 500) }} or more are paid out;
        smaller balances carry over to next month.
      </p>
      <div class="nm-todo">
        <span class="nm-todo-item"><strong>{{ dueRows.length }}</strong> RND{{ dueRows.length === 1 ? '' : 's' }} ready to pay</span>
        <span class="nm-todo-item"><strong>{{ peso(run?.due_total) }}</strong> to send</span>
        <span v-if="run && !run.payout_day_reached" class="nm-todo-item done">Payout day hasn't come yet this month</span>
      </div>
    </div>

    <div class="nm-toolbar">
      <div class="nm-tabs">
        <button class="nm-tab" :class="{ active: tab === 'run' }" @click="tab = 'run'">This month <span class="nm-count">{{ rows.length }}</span></button>
        <button class="nm-tab" :class="{ active: tab === 'history' }" @click="tab = 'history'">History <span class="nm-count">{{ history.length }}</span></button>
      </div>
    </div>

    <!-- RUN -->
    <div v-if="tab === 'run'" class="nm-panel">
      <p v-if="loading" class="nm-muted">Loading balances…</p>
      <div v-else-if="!rows.length" class="nm-empty">
        <Wallet :size="28" />
        <p>No RND has earnings yet.</p>
      </div>
      <div v-else class="nm-table-wrap">
        <table class="nm-table stack">
          <thead>
            <tr>
              <th>RND</th>
              <th class="nm-num">Pending</th>
              <th class="nm-num">Posted</th>
              <th class="nm-num">Paid out</th>
              <th>Send to</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in rows" :key="r.rnd_id">
              <td>
                <NuxtLink :to="`/users/${r.rnd_id}`" class="rnd-cell">
                  <img v-if="r.profile_photo" :src="r.profile_photo" class="nm-avatar" alt="" />
                  <span v-else class="nm-avatar">{{ nameInitials(r.rnd_name) }}</span>
                  <span style="min-width: 0">
                    <span class="nm-row-title">{{ r.rnd_name }}</span>
                    <span class="nm-row-sub" style="display: block">{{ r.email }}</span>
                  </span>
                </NuxtLink>
              </td>
              <td data-label="Pending" class="nm-num">{{ peso(r.pending) }}</td>
              <td data-label="Posted" class="nm-num"><strong>{{ peso(r.posted) }}</strong></td>
              <td data-label="Paid out" class="nm-num">{{ peso(r.paid_out) }}</td>
              <td data-label="Send to">
                <template v-if="r.payout_account">
                  <span class="acct-method">{{ payoutVia(r.payout_account.method, r.payout_account.bank_name) }}</span>
                  <span class="acct-line">{{ r.payout_account.account_name }} · {{ r.payout_account.account_number }}</span>
                </template>
                <span v-else class="nm-pill gold">No payout details</span>
              </td>
              <td class="nm-num">
                <button v-if="r.eligible" class="nm-btn-dark nm-btn-sm" @click="openRelease(r)">Release {{ peso(r.posted) }}</button>
                <span v-else-if="!r.payout_account" class="nm-muted">Held until added</span>
                <span v-else-if="Number(r.posted) > 0" class="nm-pill muted">{{ r.reason }}</span>
                <span v-else class="nm-pill muted">Nothing posted</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- HISTORY -->
    <div v-else class="nm-panel">
      <div v-if="!history.length" class="nm-empty">
        <Wallet :size="28" />
        <p>No payouts released yet.</p>
      </div>
      <div v-else class="nm-table-wrap">
        <table class="nm-table stack">
          <thead>
            <tr>
              <th>Released</th>
              <th>RND</th>
              <th class="nm-num">Amount</th>
              <th>Sent to</th>
              <th>Reference</th>
              <th>By</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in history" :key="p.id">
              <td data-label="Released">{{ dateTime(p.released_at) }}</td>
              <td data-label="RND"><NuxtLink :to="`/users/${p.rnd}`" class="nm-text-link">{{ p.rnd_name }}</NuxtLink></td>
              <td data-label="Amount" class="nm-num"><strong>{{ peso(p.amount) }}</strong> <span class="nm-muted">· {{ p.invoice_count }} consult{{ p.invoice_count === 1 ? '' : 's' }}</span></td>
              <td data-label="Sent to">{{ methodText(p) }}</td>
              <td data-label="Reference" class="mono">{{ p.reference }}</td>
              <td data-label="By">{{ p.released_by_name || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- release modal -->
    <div v-if="releasing" class="nm-modal-overlay" @click.self="releasing = null">
      <div class="nm-modal">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="releasing = null"><X :size="18" aria-hidden="true" /></button>
        <h3 class="nm-modal-title">Release {{ peso(releasing.posted) }} to {{ releasing.rnd_name }}</h3>
        <p class="nm-modal-text">
          First send the money yourself, then record it here. The RND gets an email and a notification.
        </p>
        <dl class="nm-dl send-box">
          <div><dt>Method</dt><dd>{{ payoutVia(releasing.payout_account.method, releasing.payout_account.bank_name) }}</dd></div>
          <div><dt>Amount</dt><dd>{{ peso(releasing.posted) }} ({{ releasing.posted_count }} consult{{ releasing.posted_count === 1 ? '' : 's' }})</dd></div>
          <div><dt>Account name</dt><dd>{{ releasing.payout_account.account_name }}</dd></div>
          <div><dt>Account number</dt><dd class="mono">{{ releasing.payout_account.account_number }}</dd></div>
        </dl>
        <label class="nm-label" for="payout-ref" style="margin-top: 16px">GCash / bank reference no.</label>
        <input id="payout-ref" v-model="reference" class="nm-input" maxlength="100" placeholder="e.g. 1234 567 890123" />
        <label class="nm-label" for="payout-notes" style="margin-top: 12px">Notes <span class="nm-muted">(optional)</span></label>
        <textarea id="payout-notes" data-allow-emoji v-model="notes" class="nm-input" rows="2" maxlength="500" />
        <p v-if="releaseError" class="nm-field-error">{{ releaseError }}</p>
        <div class="nm-modal-actions">
          <button class="nm-btn-outline" @click="releasing = null">Cancel</button>
          <button class="nm-btn-dark" :disabled="busy" @click="release">{{ busy ? 'Recording…' : 'Mark as paid out' }}</button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { payoutVia } from '~/utils/payout'
import { CheckCircle2, Wallet, X } from 'lucide-vue-next'

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

const rows = computed(() => run.value?.rows || [])
const dueRows = computed(() => rows.value.filter(r => r.eligible))

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    const [r, h] = await Promise.all([get('/admin/payouts/run/'), get('/admin/payouts/')])
    run.value = r
    history.value = Array.isArray(h) ? h : h?.results || []
  } catch {
    if (!quiet) error.value = 'Could not load payouts. Please refresh the page.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
useAutoRefresh(() => load({ quiet: true }))

function openRelease(r) {
  releasing.value = r
  reference.value = ''
  notes.value = ''
  releaseError.value = ''
}

async function release() {
  releaseError.value = ''
  if (!reference.value.trim()) {
    releaseError.value = 'Enter the GCash or bank reference number so the payment can be traced.'
    return
  }
  busy.value = true
  try {
    const p = await post(`/admin/payouts/release/${releasing.value.rnd_id}/`, { reference: reference.value.trim(), notes: notes.value.trim() })
    releasing.value = null
    await load()
    toast.value = `${peso(p.amount)} paid out to ${p.rnd_name}.`
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
function methodText(p) {
  const m = payoutVia(p.method, p.bank_name)
  return `${m} · ${p.account_number}`
}
</script>

<style scoped>
.rnd-cell { display: flex; align-items: center; gap: 10px; text-decoration: none; min-width: 0; }
.acct-method { display: block; font-size: 0.8rem; font-weight: 700; color: #1a3a1a; }
.acct-line { display: block; font-size: 0.77rem; color: #6a7a6a; font-variant-numeric: tabular-nums; }
.send-box { background: #f7f9f7; border-radius: 10px; padding: 12px 14px; }
.mono { font-variant-numeric: tabular-nums; letter-spacing: 0.02em; }
@media (max-width: 640px) {
  .nm-table.stack td.nm-num:last-child { padding-top: 8px; }
  .nm-table.stack td.nm-num:last-child .nm-btn-dark { width: 100%; }
}
</style>
