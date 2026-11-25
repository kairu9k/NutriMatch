<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <p v-if="loading" class="nm-muted er-loading"><span class="er-spin" aria-hidden="true"></span> Loading your earnings…</p>

    <template v-else-if="e">
      <!-- statement: next payout, then where the money is (it moves on hold, cleared, paid out) -->
      <section class="nm-panel statement">
        <img class="st-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="st-fade" aria-hidden="true"></span>
        <div class="st-head">
          <div class="st-txt">
            <p class="st-eyebrow"><span aria-hidden="true"></span>Earnings</p>
            <h1 class="st-title">Next payout {{ longDate(e.next_payout_date) }}</h1>
            <p class="st-sub">
              <template v-if="!e.payout_account">Add your GCash or bank details so NutriMatch can send your earnings. Your balance is kept until then.</template>
              <template v-else-if="!e.eligible">Payouts start at {{ peso(e.minimum_payout) }} cleared. Smaller balances carry over to the next 5th.</template>
              <template v-else>{{ peso(e.payable) }} cleared by {{ shortDate(e.run_date) }} goes to your {{ accountText }}.</template>
            </p>
          </div>
          <button v-if="!e.payout_account" type="button" class="nm-btn-gold" @click="startEdit">Add payout details</button>
          <p v-else class="st-account"><span class="st-acc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2" /><rect x="3" y="9" width="18" height="11" rx="2" /><path d="M16 14.5h2" /></svg></span><span class="st-acc-k">Paid to</span><strong class="st-acc-v">{{ accountText }}</strong><button type="button" class="st-acc-edit" @click="startEdit"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg>Change</button></p>
        </div>
      </section>

      <div class="st-figures st-below">
        <div class="st-flow">
          <div class="fig on">
            <span class="fig-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg></span>
            <p class="fig-label">On hold</p>
            <p class="fig-value">{{ peso(e.pending) }}</p>
            <p class="fig-note">Clears {{ e.hold_days }} days after the consultation</p>
          </div>
          <ChevronRight :size="18" class="fig-arrow" aria-hidden="true" />
          <div class="fig">
            <span class="fig-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M8.5 12.5l2.5 2.5 4.5-5" /></svg></span>
            <p class="fig-label">Cleared</p>
            <p class="fig-value">{{ peso(e.posted) }}</p>
            <p class="fig-note">Paid out on {{ shortDate(e.next_payout_date) }}</p>
          </div>
          <ChevronRight :size="18" class="fig-arrow" aria-hidden="true" />
          <div class="fig">
            <span class="fig-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4z" /></svg></span>
            <p class="fig-label">Paid out</p>
            <p class="fig-value">{{ peso(e.paid_out) }}</p>
            <p class="fig-note">{{ e.payouts.length }} payout{{ e.payouts.length === 1 ? '' : 's' }} so far</p>
          </div>
        </div>
        <div class="fig fig-month">
          <span class="fig-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8" /><path d="M14 7h7v7" /></svg></span>
          <p class="fig-label">Earned this month</p>
          <p class="fig-value">{{ peso(e.this_month.share) }}</p>
          <p class="fig-note">From {{ peso(e.this_month.gross) }} in fees</p>
        </div>
      </div>

      <!-- consultations -->
      <div class="nm-toolbar er-toolbar">
        <div class="nm-tabs er-tabs">
          <button v-for="t in TABS" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" @click="tab = t.key">
            {{ t.label }}<span v-if="countOf(t.key)" class="nm-count"> {{ countOf(t.key) }}</span>
          </button>
        </div>
        <div class="nm-search er-search">
          <Search :size="15" />
          <input v-model="search" type="search" placeholder="Search patient or invoice no." />
        </div>
      </div>

      <div class="nm-panel er-card">
        <div class="nm-panel-head er-head">
          <div>
            <h2 class="nm-panel-title">Consultations</h2>
            <p class="nm-panel-sub">The fee minus the platform commission, fixed when you confirmed the booking</p>
          </div>
          <p v-if="filtered.length" class="result-count">
            {{ filtered.length }} consultation{{ filtered.length === 1 ? '' : 's' }}<template v-if="rowPages > 1">, showing {{ (rowPage - 1) * ROWS_PER_PAGE + 1 }}–{{ Math.min(rowPage * ROWS_PER_PAGE, filtered.length) }}</template>
          </p>
        </div>
        <p v-if="!filtered.length" class="empty-line er-empty"><span class="er-empty-ico"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg></span>{{ e.statement.length ? 'No consultations in this view.' : 'No invoices yet. One is issued each time you confirm a booking.' }}</p>
        <div v-else class="nm-table-wrap er-wrap">
          <table class="nm-table stack er-table">
            <thead>
              <tr><th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg> Invoice</th><th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg> Patient</th><th class="nm-num"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z" /><circle cx="7.5" cy="7.5" r="1.5" /></svg> Fee</th><th class="nm-num"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 5L5 19" /><circle cx="6.5" cy="6.5" r="2.5" /><circle cx="17.5" cy="17.5" r="2.5" /></svg> Commission</th><th class="nm-num"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3" /><path d="M21 9h-6a3 3 0 0 0 0 6h6z" /></svg> Your share</th><th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21V4M4 4h12l-2 4 2 4H4" /></svg> Status</th></tr>
            </thead>
            <tbody>
              <tr v-for="r in pagedRows" :key="r.invoice_id" class="clickable" :class="'tone-' + rowTone(r.state)" @click="row = r">
                <td data-label="Invoice"><strong class="er-inv"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg>INV-{{ pad(r.invoice_id) }}</strong></td>
                <td data-label="Patient"><span class="er-pt"><span class="er-av" aria-hidden="true">{{ initialsOf(r.client_name) }}</span><span class="er-pt-txt"><b class="er-name">{{ r.client_name }}</b><span class="nm-row-sub er-meta" style="display: block"><svg v-if="/video/i.test(r.consultation_type || '')" class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="14" height="12" rx="2" /><path d="M16 10l6-3v10l-6-3z" /></svg><svg v-else-if="/chat/i.test(r.consultation_type || '')" class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg><svg v-else class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" /></svg> {{ r.consultation_type }}, {{ r.consultation_at ? shortDate(r.consultation_at) : 'no date' }}</span></span></span></td>
                <td data-label="Fee" class="nm-num er-fee">{{ peso(r.amount) }}</td>
                <td data-label="Commission" class="nm-num er-com">− {{ peso(r.commission) }} <span class="nm-muted er-pct">{{ Number(r.commission_pct) }}%</span></td>
                <td data-label="Your share" class="nm-num er-share"><strong :class="{ none: !countsAsEarning(r) }">{{ countsAsEarning(r) ? peso(r.share) : '—' }}</strong></td>
                <td data-label="Status" class="er-st">
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
        <div class="nm-panel er-card er-lower">
          <h2 class="nm-panel-title">Payouts</h2>
          <p class="nm-panel-sub">Sent on the 5th of each month<template v-if="e.payouts.length">, {{ e.payouts.length }} so far</template></p>
          <div v-if="!e.payouts.length" class="empty-line po-empty">
            <span class="po-ico"><svg class="ic" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg></span>
            <strong>No payouts yet</strong>
            <span class="po-txt">The first one is sent on the 5th once {{ peso(e.minimum_payout) }} has cleared.</span>
            <span v-if="e.next_payout_date" class="po-next"><span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg> Next payout</span><b>{{ shortDate(e.next_payout_date) }}</b></span>
          </div>
          <button v-for="p in pagedPayouts" :key="p.id" type="button" class="payout-row" @click="openPayout(p)">
            <span class="po-row-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 2L11 13" /><path d="M22 2l-7 20-4-9-9-4z" /></svg></span>
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
        <div class="nm-panel er-card er-lower">
          <h2 class="nm-panel-title">Your share, last 6 months</h2>
          <p class="nm-panel-sub">By the month the client paid</p>
          <div class="chart">
            <div v-for="m in trend" :key="m.key" class="bar-col" :class="{ on: m.amount }">
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
        <aside class="pd-aside" aria-hidden="true">
          <img class="pd-plate" :src="plateImg" alt="" />
          <span class="pd-aside-ico"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2" /><rect x="3" y="9" width="18" height="11" rx="2" /><path d="M16 14.5h2" /></svg></span>
          <p class="pd-aside-k">Your payouts</p>
          <ul>
            <li><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg><span>Sent every <b>5th of the month</b></span></li>
            <li><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M14.5 9.5c-.5-1-1.5-1.5-2.5-1.5-1.4 0-2.5.8-2.5 2s1.1 1.7 2.5 2 2.5.8 2.5 2-1.1 2-2.5 2c-1 0-2-.5-2.5-1.5M12 6.5V8M12 16v1.5" /></svg><span>Starts at <b>{{ e ? peso(e.minimum_payout) : 'the minimum' }}</b> cleared</span></li>
            <li><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg><span>Only <b>NutriMatch admins</b> can see these details</span></li>
          </ul>
        </aside>
        <div class="pd-main">
          <h3 id="pd-title" class="nm-modal-title">{{ account ? 'Change payout details' : 'Add payout details' }}</h3>
          <p class="nm-modal-text">Where NutriMatch sends your earnings on the 5th. Only NutriMatch admins can see these.</p>
          <PayoutDetailsFields ref="payoutFields" :account="account" />
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" :disabled="saving" @click="editing = false">Cancel</button>
            <button type="submit" class="nm-btn-dark" :disabled="saving"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg>{{ saving ? 'Saving…' : 'Save payout details' }}</button>
          </div>
        </div>
      </form>
    </div>

    <!-- invoice detail -->
    <div v-if="row" class="nm-modal-overlay" @click.self="row = null">
      <div class="nm-modal inv" role="dialog" aria-modal="true" :aria-label="`Invoice INV-${pad(row.invoice_id)}`">
        <div class="inv-head nm-modal-head">
          <span class="inv-av" aria-hidden="true">{{ (row.client_name || '?').split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() }}</span>
          <div class="inv-who">
            <h3 class="inv-title">{{ row.client_name }}</h3>
            <p class="inv-sub">INV-{{ pad(row.invoice_id) }}, {{ row.consultation_type.toLowerCase() }} consultation{{ row.consultation_at ? ` on ${when(row.consultation_at)}` : '' }}</p>
          </div>
          <span class="nm-pill" :class="STATE[row.state]?.pill || 'muted'">{{ STATE[row.state]?.label }}</span>
          <button class="close-btn" aria-label="Close" @click="row = null"><X :size="18" /></button>
        </div>

        <div class="inv-body">
        <section class="inv-col">
        <p class="inv-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2z" /><path d="M9 8h6M9 12h6" /></svg>Breakdown</p>
        <div class="inv-money">
          <p><span>Consultation fee</span><span>{{ peso(row.amount) }}</span></p>
          <p><span>Platform commission, {{ Number(row.commission_pct) }}%</span><span>− {{ peso(row.commission) }}</span></p>
          <p class="inv-total">
            <span>{{ countsAsEarning(row) ? 'Your share' : row.state === 'awaiting_payment' ? 'Your share once paid' : 'Your share' }}</span>
            <span :class="{ void: ['refund_pending', 'refunded', 'voided'].includes(row.state) }">{{ peso(row.share) }}</span>
          </p>
        </div>

  <p class="inv-note"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg><span>{{ stateExplain(row) }}</span></p>
        </section>
        <section class="inv-col">
        <p class="inv-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>Timeline</p>
        <ol class="inv-steps">
          <li v-for="st in invoiceSteps(row)" :key="st.label" :class="st.state">
            <span class="dot" aria-hidden="true" />
            <span class="st-text"><strong>{{ st.label }}</strong><span>{{ st.when }}</span></span>
          </li>
        </ol>

        </section>
        </div>

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

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import {
  CheckCircle2, ChevronRight, Mail, Printer, Search, X,
} from 'lucide-vue-next'
import { payoutVia } from '~/utils/payout'

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
const toast = useToast() // the app's toast (2026-11-03)
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
    awaiting_payment: 'The client hasn\'t paid yet. If it\'s still unpaid 15 minutes before the start, the consultation is cancelled automatically.',
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
    toast.error(apiError(err, 'Could not send the email. Please try again.'), { id: 'payout-email' })
  } finally {
    resending.value = false
  }
}
function printStatement(p) {
  const method = payoutVia(p.method, p.bank_name)
  const ok = printDocument({
    title: 'Payout statement',
    number: `Payout #${p.id}, sent ${shortDate(p.released_at)}`,
    rows: [['Paid to', p.account_name], ['Sent via', `${method}, ${p.account_number}`], ['Reference', p.reference], ['Payday it belongs to', shortDate(p.payout_date)]],
    table: [['Invoice', 'Patient', 'Consultation', 'Fee', 'Your share'],
      ...p.invoices.map(i => [`INV-${pad(i.invoice_id)}`, i.client_name, i.consultation_at ? shortDate(i.consultation_at) : '—', peso(i.amount), peso(i.share)])],
    total: ['Total paid out', peso(p.amount)],
  })
  if (!ok) toast.problem('Allow pop-ups for this site to print the statement.')
}

/* payout details: an e-wallet (GCash, Maya, GoTyme, MariBank) or a bank from
   the list / typed in. Same rules as the API: GCash and Maya 09XXXXXXXXX,
   everything else 6–20 digits. */
const account = ref(null)
const editing = ref(false)
const saving = ref(false)
const payoutFields = ref(null)
function startEdit() {
  editing.value = true // the form mounts fresh, filled from `account`
}
async function saveAccount() {
  const fields = payoutFields.value
  if (!fields.validate()) return
  saving.value = true
  try {
    account.value = await put('/rnd/payout-account/', fields.payload())
    editing.value = false
    e.value = await get('/rnd/earnings/')
    flash('Payout details saved.')
  } catch (err) {
    fields.setErrors(err?.data, apiError(err, 'Could not save. Please try again.'))
  } finally {
    saving.value = false
  }
}

function flash(text, opts) {
  toast.success(text, opts)
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// accent colour of a consultation row
const rowTone = s => ({ awaiting_payment: 'gold', pending: 'gold', posted: 'green', paid_out: 'blue', refund_pending: 'red' }[s] || 'muted')
const initialsOf = name => { const w = String(name || '?').split(' ').filter(Boolean); return (w.length > 1 ? w[0][0] + w[w.length - 1][0] : (w[0] || '?')[0]).toUpperCase() }
</script>
<style scoped>
.nm-page { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); }
.ic { flex-shrink: 0; }
.er-loading { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 40px 20px; border-radius: 22px; background: #fff; box-shadow: var(--sh); font-weight: 600; }
.er-spin { width: 20px; height: 20px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: er-spin 0.8s linear infinite; }
@keyframes er-spin { to { transform: rotate(360deg); } }

/* ---------- statement hero ---------- */
.nm-panel.statement {
  position: relative; overflow: hidden; margin-bottom: 20px; padding: 28px 30px 26px; border: none; border-radius: 24px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.statement > *:not(.st-plate):not(.st-fade) { position: relative; z-index: 1; }
.st-plate { position: absolute; right: -70px; top: -70px; width: 340px; height: 340px; object-fit: cover; border-radius: 50%; pointer-events: none; }
.st-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 50%, rgba(0, 77, 58, 0.9) 72%, rgba(0, 77, 58, 0.72) 100%); }
.st-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 18px 24px; flex-wrap: wrap; padding: 0; background: none; }
.st-txt { flex: 1 1 380px; min-width: 0; }
.st-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.st-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.st-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.st-sub { margin: 0; max-width: 62ch; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }
.st-head .nm-btn-gold { flex-shrink: 0; display: inline-flex; align-items: center; height: 42px; padding: 0 18px; border-radius: 12px; background: #efbf04; border: none; color: #004d3a; font-weight: 800; text-decoration: none; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
.st-account { flex-shrink: 0; display: flex; align-items: center; gap: 12px; margin: 0; padding: 10px 10px 10px 12px; border-radius: 16px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.16); backdrop-filter: blur(6px); font-size: 14.5px; font-weight: 700; letter-spacing: 0.02em; color: #fff; }
.st-acc-ico { width: 38px; height: 38px; border-radius: 12px; background: rgba(255, 255, 255, 0.14); color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.st-acc-txt { display: flex; flex-direction: column; }
.st-acc-txt small { font-size: 11.5px; font-weight: 500; letter-spacing: 0; color: rgba(255, 255, 255, 0.7); }
.st-account .nm-btn-gold { height: 38px; padding: 0 16px; border-radius: 11px; background: #efbf04; border: none; color: #004d3a; font-size: 13.5px; font-weight: 800; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
.st-head button:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }

.st-figures { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 1fr); gap: 12px; margin-top: 24px; border: none; background: none; }
.st-flow { display: flex; align-items: stretch; gap: 4px; }
.st-flow .fig { flex: 1; }
.fig { display: flex; flex-direction: column; gap: 2px; min-width: 0; padding: 16px 18px; border-radius: 18px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.14); }
.fig-ico { width: 32px; height: 32px; margin-bottom: 8px; border-radius: 10px; background: rgba(255, 255, 255, 0.12); color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.fig-label { margin: 0; font-size: 12.5px; font-weight: 600; color: rgba(255, 255, 255, 0.78); }
.fig-value { margin: 0; font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; letter-spacing: 0.01em; color: #fff; font-variant-numeric: tabular-nums lining-nums; white-space: nowrap; }
.fig-note { margin: 0; font-size: 12.5px; color: rgba(255, 255, 255, 0.7); }
.fig-arrow { flex-shrink: 0; align-self: center; width: 18px; color: rgba(255, 255, 255, 0.55); }
.fig-month { margin-left: 12px; }

/* ---------- tabs + search ---------- */
.er-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.er-tabs { display: inline-flex; gap: 4px; max-width: 100%; padding: 5px; border: none; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); overflow-x: auto; scrollbar-width: none; }
.er-tabs::-webkit-scrollbar { display: none; }
.er-tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 4px; height: 36px; margin: 0; padding: 0 15px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.er-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; }
.er-tabs .nm-count { min-width: 20px; height: 20px; margin-left: 3px; padding: 0 6px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 700; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.er-tabs .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.er-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }
.er-tabs .nm-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.er-search { position: relative; display: flex; align-items: center; gap: 10px; flex: 0 1 320px; height: 46px; margin: 0; padding: 0 16px; border: none; border-radius: 10px; background: #fff; color: #8a9a91; box-sizing: border-box; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); }
.er-search:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.er-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.er-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }

/* ---------- cards ---------- */
.nm-panel.er-card { padding: 0; border: none; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: hidden; }
.er-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin: 0; padding: 24px 32px 20px; }
.er-card .nm-panel-title { margin: 0 0 4px; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.er-card .nm-panel-sub { margin: 0; font-size: 13.5px; color: #6b7d73; }
.result-count { flex-shrink: 0; margin: 0; padding: 5px 12px; border-radius: 999px; background: #e3f4ea; font-size: 12.5px; font-weight: 700; color: #1f7a4d; white-space: nowrap; }
.er-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; margin: 0 32px 28px; padding: 32px 20px; border-radius: 18px; border: 1.5px dashed #cfddd4; text-align: center; font-size: 14px; font-weight: 600; color: #4a5a52; }
.er-empty-ico { width: 52px; height: 52px; border-radius: 16px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }

/* consultations table: every label lines up with its values (left) */
.er-wrap { margin: 0; border: none; border-radius: 0; overflow-x: auto; }
.er-table { width: 100% !important; min-width: 980px; table-layout: fixed; border-collapse: collapse; font-size: 14px; }
/* same column widths as the canvas: spread across the card, 32px between columns */
.er-table th:nth-child(1) { width: 13%; }
.er-table th:nth-child(2) { width: 24%; }
.er-table th:nth-child(3) { width: 12%; }
.er-table th:nth-child(4) { width: 16%; }
.er-table th:nth-child(5) { width: 15%; }
.er-table th:nth-child(6) { width: 20%; }
.er-table thead th { padding: 15px 16px; background: #eaf3ed; border-top: 1px solid #dcebe1; border-bottom: 1px solid #dcebe1; text-align: left; font-size: 13px; font-weight: 700; color: #1f5c45; white-space: nowrap; text-transform: none; letter-spacing: 0; }
.er-table thead th .ic { display: inline-block !important; margin-right: 6px; vertical-align: -2px; color: #1f7a4d; }
.er-table th.nm-num, .er-table td.nm-num, .er-table thead th { text-align: left !important; }
.er-table th:first-child, .er-table td:first-child { padding-left: 32px; }
.er-table th:last-child, .er-table td:last-child { padding-right: 32px; }
.er-table tbody td { position: relative; padding: 22px 16px; border-bottom: 1px solid #f0f3f1; vertical-align: middle; }
.er-table tbody tr:last-child td { border-bottom: none; }
.er-table tbody tr.clickable { cursor: pointer; transition: background 0.15s; }
.er-table tbody tr.clickable:hover td { background: #fafcfb; }
@media (min-width: 761px) {
  .er-table tbody td:first-child::before { content: ''; position: absolute; left: 0; top: 22px; bottom: 22px; width: 4px; border-radius: 0 4px 4px 0; background: #c9d3cd; }
  .tone-green td:first-child::before { background: #1f9d55 !important; }
  .tone-gold td:first-child::before { background: #efbf04 !important; }
  .tone-red td:first-child::before { background: #c0392b !important; }
  .tone-blue td:first-child::before { background: #3b5ba5 !important; }
}
.er-inv { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 9px; background: #f3f7f4; font-size: 13px; font-weight: 700; letter-spacing: 0.02em; color: #0e3a2c; white-space: nowrap; }
.er-inv .ic { color: #1f7a4d; }
.er-pt { display: flex; align-items: center; gap: 14px; min-width: 0; }
.er-av { flex-shrink: 0; width: 42px; height: 42px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-size: 13.5px; font-weight: 800; border: 2px solid #fff; box-shadow: 0 0 0 2.5px #c9d3cd; }
.tone-green .er-av { box-shadow: 0 0 0 2.5px #1f9d55; }
.tone-gold .er-av { box-shadow: 0 0 0 2.5px #efbf04; }
.tone-red .er-av { box-shadow: 0 0 0 2.5px #e7b4ae; }
.tone-blue .er-av { box-shadow: 0 0 0 2.5px #9fb2dd; }
.er-pt-txt { min-width: 0; }
.er-name { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14.5px; font-weight: 700; color: #0e3a2c; }
.er-meta { display: flex !important; align-items: center; gap: 6px; margin-top: 4px; font-size: 13px; color: #6b7d73; }
.er-meta .ic { color: #1f7a4d; }
.er-fee { font-weight: 600; color: #22362c; font-variant-numeric: tabular-nums; white-space: nowrap; }
.er-com { color: #6b7d73; font-variant-numeric: tabular-nums; white-space: nowrap; }
.er-pct { margin-left: 6px; padding: 2px 8px; border-radius: 999px; background: #f3f6f4; font-size: 11.5px; font-weight: 700; color: #6b7d73; }
.er-share strong { font-size: 15px; font-weight: 800; color: #1f7a4d; font-variant-numeric: tabular-nums; white-space: nowrap; }
.er-share strong.none { font-weight: 700; color: #b5c3ba; }
.er-table td.er-st { padding-left: 16px; }
.er-st .nm-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 700; }
.er-st .nm-pill::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.er-st .nm-row-sub { margin-top: 6px; font-size: 12.5px; color: #6b7d73; }
.nm-pill.gold { background: #fff4d6; color: #8a6500; }
.nm-pill.green { background: #e3f4ea; color: #1f7a4d; }
.nm-pill.blue { background: #eef1fa; color: #2e4a86; }
.nm-pill.red { background: #fdecea; color: #b42318; }
.nm-pill.muted { background: #f3f6f4; color: #6b7d73; }
.pager { display: flex; justify-content: center; align-items: center; gap: 12px; margin: 0; padding: 16px 32px 20px; border-top: 1px solid #f0f3f1; }
.pager-num { font-size: 13px; color: #4a5a52; font-variant-numeric: tabular-nums; white-space: nowrap; }
.pager .nm-btn-sm { border-radius: 10px; }

/* ---------- payouts + chart ---------- */
.lower { margin-top: 20px; align-items: stretch; gap: 20px; }
.lower > .nm-panel { display: flex; flex-direction: column; }
.er-lower { padding: 24px 32px 24px !important; }
.lower .pager { margin-top: auto; padding: 14px 0 0; border-top: none; }
.po-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin: 18px 0 0; padding: 28px 20px; border-radius: 18px; background: #f7faf8; border: 1px dashed #d5e3da; }
.po-ico { width: 58px; height: 58px; margin-bottom: 12px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.po-empty strong { font-size: 16px; color: #0e3a2c; }
.po-txt { margin: 4px 0 16px; max-width: 36ch; font-size: 13.5px; line-height: 1.5; color: #6b7d73; }
.po-next { display: inline-flex; align-items: center; gap: 10px; padding: 7px 7px 7px 14px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px #e3ece6; font-size: 13px; color: #4a5a52; }
.po-next > span { display: inline-flex; align-items: center; gap: 6px; }
.po-next .ic { color: #1f7a4d; }
.po-next b { padding: 4px 12px; border-radius: 999px; background: #004d3a; color: #fff; font-size: 12.5px; }
.payout-row { display: flex; align-items: center; gap: 12px; width: 100%; padding: 14px 4px; text-align: left; background: none; border: none; border-top: 1px solid #f0f3f1; border-radius: 0; cursor: pointer; font-family: inherit; color: inherit; transition: background 0.15s; }
.payout-row:first-of-type { margin-top: 14px; border-top: none; }
.payout-row:hover { background: #fafcfb; }
.payout-row:hover .nm-row-title { color: #1f7a4d; }
.payout-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.po-row-ico { flex-shrink: 0; width: 38px; height: 38px; border-radius: 12px; background: #e3f4ea; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.payout-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.payout-main .nm-row-title { font-size: 14.5px; font-weight: 700; color: #0e3a2c; }
.payout-main .nm-row-sub { font-size: 12.5px; color: #6b7d73; overflow-wrap: anywhere; }
.chev { flex-shrink: 0; width: 28px; height: 28px; padding: 6px; box-sizing: border-box; border-radius: 50%; background: #f1f6f2; color: #1f7a4d; }
.chart { display: flex; align-items: flex-end; gap: 14px; height: 220px; margin-top: 18px; padding: 20px 18px 14px; border-radius: 18px; box-sizing: border-box; background: repeating-linear-gradient(to top, #f1f5f2 0, #f1f5f2 1px, transparent 1px, transparent 46px), #fff; box-shadow: inset 0 0 0 1px #eef3ef; }
.bar-col { flex: 1; height: 100%; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; gap: 8px; min-width: 0; }
.bar { width: 100%; max-width: 56px; min-height: 4px; border-radius: 10px 10px 4px 4px; background: #e3ece6; }
.bar-col.on .bar { background: linear-gradient(180deg, #1f9d55, #004d3a); box-shadow: 0 12px 20px -12px rgba(0, 77, 58, 0.8); }
.bar-val { min-height: 16px; font-size: 12.5px; font-weight: 800; color: #004d3a; white-space: nowrap; }
.bar-label { font-size: 12.5px; color: #6b7d73; }
.bar-col.on .bar-label { font-weight: 700; color: #0e3a2c; }

/* ---------- pop-ups ---------- */
.pd-modal { position: relative; max-width: 460px; }
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
.inv-title, .md-head .inv-title { color: #0e3a2c; }
.inv-steps li.done:not(:last-child)::after, .inv-steps .done .dot { background: #1f9d55; border-color: #1f9d55; }
.close-btn { width: 36px; height: 36px; border-radius: 11px; border: 1px solid #e3ebe6; background: #fff; display: inline-flex; align-items: center; justify-content: center; }
.close-btn:hover { background: #f1f6f2; color: #004d3a; }

/* ---------- responsive ---------- */
@media (max-width: 960px) {
  .nm-panel.statement { padding: 22px 18px; border-radius: 22px; }
  .st-title { font-size: 23px; }
  .st-plate { width: 200px; height: 200px; right: -80px; top: -60px; }
  .st-account { width: 100%; box-sizing: border-box; }
  .st-acc-txt { flex: 1; }
  .st-head .nm-btn-gold { justify-content: center; }
  .st-figures { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .st-flow { display: contents; }
  .fig-arrow { display: none; }
  .fig-month { margin-left: 0; }
  .fig { padding: 14px; }
  .fig-value { font-size: 21px; }
  .fig-note { font-size: 11.5px; }
  .er-search { flex: 1 1 100%; }
  .er-tabs { display: flex; width: 100%; box-sizing: border-box; border-radius: 16px; }
  .er-head { padding: 18px 16px 12px; flex-wrap: wrap; }
  .er-empty { margin: 0 16px 20px; }
  .er-lower { padding: 18px 16px !important; }
  .chart { gap: 6px; padding: 16px 10px 12px; }
}
@media (max-width: 760px) {
  .nm-page { padding-bottom: 110px; }
  .er-table { min-width: 0; table-layout: auto; }
  .er-table thead { display: none; }
  .er-table tbody td, .er-table th:first-child, .er-table td:first-child, .er-table td:last-child { padding-left: 16px; padding-right: 16px; }
  .er-table tbody tr { border-left: 4px solid #c9d3cd; }
  .er-table tbody tr.tone-green { border-left-color: #1f9d55; }
  .er-table tbody tr.tone-gold { border-left-color: #efbf04; }
  .er-table tbody tr.tone-red { border-left-color: #c0392b; }
  .er-table tbody tr.tone-blue { border-left-color: #3b5ba5; }
  .bar-val { display: none; }
}

/* payout account: one pill, same spot (top right of the hero) */
.st-account { position: relative; z-index: 2; gap: 10px; padding: 6px; border-radius: 999px; background: rgba(0, 0, 0, 0.18); border: 1px solid rgba(255, 255, 255, 0.14); backdrop-filter: blur(6px); }
.st-acc-ico { width: 30px; height: 30px; border-radius: 50%; background: #efbf04; color: #004d3a; }
.st-acc-k { font-size: 13.5px; font-weight: 500; letter-spacing: 0; color: rgba(255, 255, 255, 0.75); white-space: nowrap; }
.st-acc-v { font-size: 14.5px; font-weight: 800; letter-spacing: 0.03em; color: #fff; white-space: nowrap; }
.st-acc-edit { display: inline-flex; align-items: center; gap: 6px; height: 30px; margin-left: 4px; padding: 0 12px; border: none; border-radius: 999px; background: rgba(255, 255, 255, 0.14); color: #fff; font-family: inherit; font-size: 13px; font-weight: 700; cursor: pointer; transition: background-color 0.15s; }
.st-acc-edit .ic { color: #efbf04; }
.st-acc-edit:hover { background: rgba(255, 255, 255, 0.24); }
.st-acc-edit:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }
@media (max-width: 760px) {
  .st-account { width: auto; max-width: 100%; flex-wrap: wrap; border-radius: 18px; }
  .st-acc-edit { margin-left: auto; }
}

/* =========================================================
   Payout details modal: green side panel + clear form
   ========================================================= */
.nm-modal-overlay .nm-modal.pd-modal { display: grid !important; grid-template-columns: 250px minmax(0, 1fr); width: min(760px, calc(100vw - 32px)) !important; max-width: none !important; max-height: calc(100vh - 48px) !important; padding: 0 !important; overflow: hidden !important; border-radius: 24px !important; }
.pd-aside { position: relative; display: flex; flex-direction: column; gap: 14px; padding: 30px 24px; background: radial-gradient(120% 90% at 0% 0%, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0) 55%), linear-gradient(160deg, #035a45, #004d3a 60%, #00402f); color: #fff; }
.pd-aside-ico { width: 52px; height: 52px; border-radius: 16px; background: #efbf04; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 12px 24px -12px rgba(0, 0, 0, 0.5); }
.pd-aside-k { margin: 4px 0 0; font-size: 12px; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; color: #efbf04; }
.pd-aside ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 14px; }
.pd-aside li { display: flex; gap: 10px; align-items: flex-start; font-size: 14px; line-height: 1.45; color: rgba(255, 255, 255, 0.85); }
.pd-aside li .ic { margin-top: 1px; color: #efbf04; }
.pd-aside li b { color: #fff; }
.pd-main { display: flex; flex-direction: column; min-width: 0; padding: 28px 30px 24px; overflow-y: auto; }
.pd-modal .nm-modal-x { top: 18px !important; right: 18px !important; z-index: 2; width: 36px !important; height: 36px !important; border-radius: 50% !important; background: #f1f6f2 !important; color: #22362c !important; }
.pd-modal .nm-modal-title { margin: 0 40px 6px 0 !important; font-family: 'Playfair Display', Georgia, serif; font-size: 24px !important; color: #0e3a2c !important; }
.pd-modal .nm-modal-text { margin: 0 0 20px !important; font-size: 14px !important; line-height: 1.5; color: #4a5a52 !important; }

/* the fields come from PayoutDetailsFields: styled from here */
.pd-modal :deep(label:not(:has(input[type="radio"]))) { font-size: 13.5px; font-weight: 700; color: #22362c; }
.pd-modal :deep(input:not([type="radio"]):not([type="checkbox"])),
.pd-modal :deep(select) { min-height: 48px; border: 1.5px solid #b9c9bf !important; border-radius: 12px !important; font-size: 15px; color: #0e3a2c; background-color: #fff; }
.pd-modal :deep(input:not([type="radio"]):not([type="checkbox"]):focus),
.pd-modal :deep(select:focus) { outline: none; border-color: #004d3a !important; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1) !important; }
.pd-modal :deep(label:has(input[type="radio"])) { min-height: 48px; padding: 0 16px; border: 1.5px solid #c9d8cf !important; border-radius: 14px !important; background: #fff !important; font-size: 14.5px; font-weight: 700; color: #22362c; cursor: pointer; }
.pd-modal :deep(label:has(input[type="radio"]:checked)) { border-color: #004d3a !important; background: #f1f8f4 !important; color: #004d3a; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.08); }
.pd-modal :deep(input[type="radio"]) { accent-color: #004d3a; width: 18px; height: 18px; }

.pd-modal .nm-modal-actions { margin-top: auto !important; padding-top: 20px !important; border-top: 1.5px solid #eef2ef; display: flex; justify-content: flex-end; gap: 10px; background: none !important; }
.pd-modal .nm-btn-outline { height: 46px; padding: 0 20px; border: 1.5px solid #c9d8cf; border-radius: 12px; background: #fff; color: #004d3a; font-weight: 800; }
.pd-modal .nm-btn-dark { display: inline-flex; align-items: center; gap: 8px; height: 46px; padding: 0 22px; border-radius: 12px; background: #004d3a; font-weight: 800; }
.pd-modal .nm-btn-dark .ic { color: #efbf04; }

@media (max-width: 720px) {
  .nm-modal-overlay .nm-modal.pd-modal { grid-template-columns: minmax(0, 1fr); overflow-y: auto !important; }
  .pd-aside { flex-direction: row; flex-wrap: wrap; align-items: center; gap: 10px 14px; padding: 18px 20px; }
  .pd-aside-ico { width: 40px; height: 40px; border-radius: 12px; }
  .pd-aside ul { flex-basis: 100%; gap: 8px; }
  .pd-aside li { font-size: 13px; }
  .pd-main { padding: 22px 18px 18px; overflow: visible; }
  .pd-modal .nm-modal-x { background: rgba(255, 255, 255, 0.16) !important; color: #fff !important; }
  .pd-modal .nm-modal-actions .nm-btn-outline, .pd-modal .nm-modal-actions .nm-btn-dark { flex: 1; justify-content: center; }
}

/* keep the X out of the grid; pin the two columns */
.pd-modal .nm-modal-x { position: absolute !important; }
.pd-aside { grid-column: 1; grid-row: 1; }
.pd-main { grid-column: 2; grid-row: 1; }
@media (max-width: 720px) {
  .pd-aside { grid-column: 1; grid-row: 1; }
  .pd-main { grid-column: 1; grid-row: 2; }
}

/* side panel: roomier list + plate at the bottom */
.pd-aside { overflow: hidden; gap: 16px; padding: 30px 22px; }
.pd-aside > *:not(.pd-plate) { position: relative; z-index: 1; }
.pd-aside-k { margin: 6px 0 2px; }
.pd-aside ul { gap: 10px; }
.pd-aside li { align-items: center; gap: 12px; padding: 10px 12px; border-radius: 14px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.1); font-size: 13.5px; }
.pd-aside li .ic { flex-shrink: 0; width: 32px; height: 32px; margin: 0; padding: 7px; border-radius: 10px; background: rgba(239, 191, 4, 0.16); box-sizing: border-box; }
.pd-plate { position: absolute; left: 50%; bottom: -120px; width: 260px; height: 260px; transform: translateX(-50%); border-radius: 50%; object-fit: cover; opacity: 0.45; pointer-events: none; -webkit-mask-image: linear-gradient(180deg, transparent 0%, #000 45%); mask-image: linear-gradient(180deg, transparent 0%, #000 45%); }
@media (max-width: 720px) {
  .pd-plate { display: none; }
  .pd-aside li { padding: 8px 10px; }
}

/* side panel list: timeline (round icons + line), no boxes */
.pd-aside ul { position: relative; gap: 22px; }
.pd-aside ul::before { content: ''; position: absolute; left: 17px; top: 20px; bottom: 20px; width: 2px; background: rgba(239, 191, 4, 0.35); }
.pd-aside li { position: relative; align-items: center; gap: 14px; padding: 0; border: none; border-radius: 0; background: none; font-size: 14px; }
.pd-aside li .ic { position: relative; z-index: 1; width: 36px; height: 36px; padding: 8px; border-radius: 50%; background: #0b5a44; border: 2px solid rgba(239, 191, 4, 0.55); color: #efbf04; }
@media (max-width: 720px) {
  .pd-aside ul { gap: 14px; }
  .pd-aside li { padding: 0; }
}

/* =========================================================
   Invoice detail modal: wider, breakdown | timeline
   ========================================================= */
.nm-modal-overlay .nm-modal.inv { width: min(760px, calc(100vw - 32px)) !important; max-width: none !important; max-height: calc(100vh - 48px) !important; padding: 0 !important; overflow-y: auto !important; border-radius: 24px !important; }
.inv .inv-head { position: relative; align-items: center; gap: 14px; margin: 0 !important; padding: 24px 28px !important; border-bottom: 1.5px solid #eef2ef; background: linear-gradient(180deg, #f4f8f5, #fff); }
.inv-av { flex-shrink: 0; width: 52px; height: 52px; border-radius: 50%; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; font-size: 17px; font-weight: 800; }
.inv .inv-title { margin: 0 0 3px; font-size: 24px; color: #0e3a2c; }
.inv .inv-sub { font-size: 14px; color: #4a5a52; }
.inv .inv-head .nm-pill { margin: 0; padding: 6px 12px; font-size: 13px; font-weight: 800; }
.inv-body { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 0; padding: 22px 28px 0; }
.inv-col { min-width: 0; }
.inv-col + .inv-col { padding-left: 28px; margin-left: 28px; border-left: 1.5px solid #eef2ef; }
.inv-body .inv-col:first-child { padding-right: 0; }
.inv-k { display: flex; align-items: center; gap: 8px; margin: 0 0 12px; font-size: 12px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; color: #9a7300; }
.inv .inv-money { margin: 0; padding: 6px 16px; border: 1.5px solid #e3ebe6; border-radius: 16px; background: #f7faf8; }
.inv .inv-money p { padding: 10px 0; font-size: 14.5px; color: #3e5046; }
.inv .inv-money p + p { border-top: 1px dashed #d3e0d8; }
.inv .inv-total { padding-top: 12px !important; font-size: 15.5px !important; color: #0e3a2c !important; }
.inv .inv-total span:last-child { font-size: 24px; color: #004d3a; }
.inv .inv-total .void { color: #9aa8a0; }
.inv .inv-steps { margin: 0; }
.inv .inv-steps li { gap: 14px; padding-bottom: 18px; }
.inv .inv-steps li:not(:last-child)::after { left: 7px; top: 18px; }
.inv .inv-steps .dot { width: 16px; height: 16px; margin-top: 2px; }
.inv .st-text { font-size: 13.5px; color: #4a5a52; }
.inv .st-text strong { font-size: 15px; font-weight: 700; color: #0e3a2c; }
.inv .inv-note { display: flex; gap: 10px; align-items: flex-start; margin: 22px 28px 26px; padding: 14px 16px; border: none; border-radius: 14px; background: #fbf8ec; font-size: 14px; line-height: 1.5; color: #5a4a10; }
.inv .inv-note .ic { margin-top: 1px; color: #9a7300; }
@media (max-width: 720px) {
  .inv .inv-head { flex-wrap: wrap; padding: 18px !important; }
  .inv-body { grid-template-columns: minmax(0, 1fr); padding: 18px 18px 0; gap: 22px; }
  .inv-col + .inv-col { padding: 0; margin: 0; border-left: none; }
  .inv .inv-note { margin: 18px; }
}

/* v2: no boxes, header never clipped, columns balanced */
.inv .inv-head { position: relative !important; top: auto !important; margin: 0 !important; padding: 26px 28px 22px !important; background: #fff; }
.inv .inv-money { padding: 0; border: none; border-radius: 0; background: none; }
.inv .inv-money p { padding: 12px 0; }
.inv .inv-money p + p { border-top: 1.5px solid #eef2ef; }
.inv .inv-total { margin-top: 4px; padding: 14px 16px !important; border-top: none !important; border-radius: 14px; background: #f1f8f4; align-items: center; }
.inv .inv-total span:last-child { font-size: 26px; }
.inv .inv-note { margin: 18px 0 0; padding: 0; border: none; border-radius: 0; background: none; font-size: 13.5px; color: #6b5a1c; }
.inv-body { padding: 22px 28px 28px; }
@media (max-width: 720px) { .inv-body { padding: 18px; } .inv .inv-note { margin: 16px 0 0; } }

/* ===== Figures: white cards on the green banner ===== */
.st-figures .fig { position: relative; z-index: 1; padding: 18px 20px; border: none; border-radius: 18px; background: #FFFFFF; box-shadow: 0 16px 32px -20px rgba(0, 0, 0, 0.55); }
.st-figures .fig-ico { width: 36px; height: 36px; border-radius: 50%; background: #E3EFE7; color: #004D3A; }
.st-flow .fig:nth-of-type(1) .fig-ico { background: #FBF3D2; color: #9A7300; }
.st-flow .fig:nth-of-type(2) .fig-ico { background: #E3F4EA; color: #1F7A4D; }
.st-flow .fig:nth-of-type(3) .fig-ico { background: #E6ECF8; color: #3B5BA5; }
.st-figures .fig-month .fig-ico { background: #004D3A; color: #EFBF04; }
.st-figures .fig-label { font-size: 13px; font-weight: 700; color: #3E5046; }
.st-figures .fig-value { color: #0E3A2C; }
.st-figures .fig-note { color: #6B7D73; }
.st-figures .fig-arrow { color: #EFBF04; }

/* ===== Figures moved under the banner ===== */
.st-figures.st-below { margin-top: 16px; }
.st-figures.st-below .fig { box-shadow: none; border: 1.5px solid #E1EAE4; }
.st-figures.st-below .fig-arrow { color: #9AAAA1; }

/* Paid to: under the text on the left, not top-right */
.statement .st-head { flex-direction: column; align-items: flex-start; flex-wrap: nowrap; gap: 18px; }
.statement .st-head .st-account, .statement .st-head .nm-btn-gold { align-self: flex-start; }
.statement .st-head .st-txt { flex: 0 0 auto; width: 100%; }

/* more room between the figure cards and the tabs */
.er-toolbar { margin-top: 28px !important; }
.er-toolbar .nm-search, .er-search, .er-search input { border-radius: 10px !important; }
</style>