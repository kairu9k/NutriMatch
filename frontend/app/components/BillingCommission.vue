<template>
  <div class="nm-page bl">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- hero -->
    <section class="bh">
      <img class="bh-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="bh-fade" aria-hidden="true"></span>
      <div class="bh-txt">
        <p class="bh-eyebrow"><span></span>Billing &amp; commission</p>
        <h1 class="bh-title">Every peso, accounted for</h1>
        <p class="bh-sub">What clients paid, what the platform keeps, and what each RND is owed.</p>
      </div>
    </section>

    <!-- THE MONEY AT A GLANCE -->
    <div class="glance">
      <div class="fig">
        <span class="fig-ico"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg></span>
        <span class="fig-label">Collected from clients</span>
        <strong>{{ peso(totals.gross) }}</strong>
        <span class="fig-note">{{ paid.length }} paid consultation{{ paid.length === 1 ? '' : 's' }}, all time</span>
      </div>
      <div class="fig">
        <span class="fig-ico"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 5L5 19" /><path d="M4 6.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /><path d="M15 17.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg></span>
        <span class="fig-label">Platform commission</span>
        <strong>{{ peso(totals.commission) }}</strong>
        <span class="fig-note">Current rate <b>{{ currentRate }}%</b></span>
      </div>
      <div class="fig">
        <span class="fig-ico"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3" /><path d="M21 9h-6a3 3 0 0 0 0 6h6z" /></svg></span>
        <span class="fig-label">RNDs' share</span>
        <strong>{{ peso(totals.net) }}</strong>
        <NuxtLink to="/payouts" class="fig-btn">Manage payouts<svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
      </div>
      <button type="button" class="fig" :class="{ warn: refundsDue.length }" @click="tab = 'refunds'">
        <span class="fig-ico"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg></span>
        <span class="fig-label">Refunds to send</span>
        <strong :class="{ warn: refundsDue.length }">{{ refundsDue.length }}</strong>
        <span class="fig-note" :class="{ warn: refundsDue.length }"><template v-if="refundsDue.length"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 9v4M12 17h.01" /><path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /></svg></template>{{ refundsDue.length ? `${peso(refundsDueTotal)} owed to clients` : 'None right now' }}</span>
      </button>
    </div>

    <div class="bt-bar">
      <div class="nm-tabs bt-tabs">
        <button type="button" class="nm-tab" :class="{ active: tab === 'invoices' }" @click="tab = 'invoices'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>Invoices <span class="nm-count">{{ invoices.length }}</span></button>
        <button type="button" class="nm-tab" :class="{ active: tab === 'refunds' }" @click="tab = 'refunds'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg>Refunds <span class="nm-count">{{ refundsDue.length }}</span></button>
        <button type="button" class="nm-tab" :class="{ active: tab === 'commission' }" @click="tab = 'commission'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 5L5 19" /><path d="M4 6.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /><path d="M15 17.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg>Commission</button>
      </div>
      <div v-if="tab === 'invoices'" class="bill-tools">
        <label class="bt-sel">
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h18l-7 8v6l-4 2v-8z" /></svg>
          <select v-model="statusFilter" class="nm-select" aria-label="Filter by status">
            <option value="">Any status</option>
            <option v-for="(label, key) in STATUS_LABELS" :key="key" :value="key">{{ label }}</option>
          </select>
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
        </label>
        <div class="nm-search bt-search">
          <Search :size="17" aria-hidden="true" />
          <input v-model="search" type="search" placeholder="Search client, RND or INV no." />
        </div>
      </div>
    </div>

    <!-- INVOICES -->
    <div v-if="tab === 'invoices'" class="nm-panel bc">
      <div class="nm-panel-head bc-head">
        <div>
          <h2 class="nm-panel-title">Invoices</h2>
          <p class="nm-panel-sub">Issued when an RND confirms a booking. Clients pay before the consultation.</p>
        </div>
        <span class="ledger-count">{{ filteredInvoices.length }} invoice{{ filteredInvoices.length === 1 ? '' : 's' }}</span>
      </div>
      <p v-if="loading" class="nm-muted bc-pad">Loading invoices…</p>
      <div v-else-if="!filteredInvoices.length" class="nm-empty bc-pad">
        <span class="e-ico"><Receipt :size="28" aria-hidden="true" /></span>
        <p>{{ invoices.length ? 'No invoices match these filters.' : 'No invoices yet.' }}</p>
      </div>
      <div v-else class="nm-table-wrap ledger-scroll">
        <table class="nm-table stack ledger">
          <thead>
            <tr>
              <th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>Invoice</th>
              <th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><path d="M8 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /></svg>Client and RND</th>
              <th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /></svg>Paid with</th>
              <th class="nm-num"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z" /><path d="M7.5 6v.01" /></svg>Fee</th>
              <th class="nm-num"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 5L5 19" /><path d="M4 6.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /><path d="M15 17.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg>Commission</th>
              <th class="nm-num"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3" /><path d="M21 9h-6a3 3 0 0 0 0 6h6z" /></svg>RND's share</th>
              <th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 22V4a1 1 0 0 1 1-1h12l-2 4 2 4H5" /></svg>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="inv in pagedInvoices" :key="inv.id" class="clickable" :class="`tone-${STATUS_PILLS[inv.status] || 'muted'}`" tabindex="0"
              :aria-label="`View ${invNo(inv)} details`" @click="openInvoice(inv)" @keydown.enter="openInvoice(inv)"
            >
              <td data-label="Invoice">
                <strong class="mono inv-chip"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>{{ invNo(inv) }}</strong>
                <span class="cell-sub">{{ shortDate(inv.created_at) }}</span>
              </td>
              <td data-label="Client and RND">
                <span class="pt">
                  <span class="pt-av" aria-hidden="true">{{ initialsOf(inv.client_name) }}</span>
                  <span class="pt-txt"><b>{{ inv.client_name }}</b><span class="cell-sub">with RND <em>{{ inv.rnd_name }}</em></span></span>
                </span>
              </td>
              <td data-label="Paid with"><span v-if="inv.payment_method" class="pay-chip"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /></svg>{{ METHOD_LABELS[inv.payment_method] || inv.payment_method }}</span><span v-else class="nm-muted">—</span></td>
              <td data-label="Fee" class="nm-num mono">{{ peso(inv.amount) }}</td>
              <td data-label="Commission" class="nm-num mono">{{ peso(inv.commission_amt) }} <span class="pct">{{ Number(inv.commission_pct) }}%</span></td>
              <td data-label="RND's share" class="nm-num mono share">{{ peso(inv.net) }}</td>
              <td data-label="Status"><span class="nm-pill" :class="STATUS_PILLS[inv.status] || 'muted'">{{ STATUS_LABELS[inv.status] || inv.status }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="bc-pager"><ListPager v-model:page="page" :pages="pages" /></div>
    </div>

    <!-- REFUNDS -->
    <div v-else-if="tab === 'refunds'" class="nm-panel bc">
      <div class="nm-panel-head bc-head">
        <div>
          <h2 class="nm-panel-title">Refunds to send</h2>
          <p class="nm-panel-sub">These consultations were paid, then cancelled. Send each one back. The client is notified once it's refunded.</p>
        </div>
      </div>
      <div class="bc-pad rf-list">
        <p v-if="refundError" class="nm-error">{{ refundError }}</p>
        <div v-if="!refundsDue.length" class="nm-empty">
          <span class="e-ico"><CheckCircle2 :size="28" aria-hidden="true" /></span>
          <p>No refunds waiting.</p>
        </div>
        <div v-for="inv in refundsDue" :key="inv.id" class="refund">
          <div class="refund-amount">
            <span class="ra-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg></span>
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
            <button v-if="inv.paymongo_payment_id" type="button" class="nm-btn-dark" @click="askRefund(inv)"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg>Refund through PayMongo</button>
            <template v-else>
              <input v-model="refundRefs[inv.id]" class="nm-input" maxlength="100" placeholder="Refund reference (optional)" aria-label="Refund reference" />
              <button type="button" class="nm-btn-dark" :disabled="refundBusy === inv.id" @click="markRefunded(inv)">
                {{ refundBusy === inv.id ? 'Saving…' : 'Mark as refunded' }}
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- COMMISSION -->
    <div v-else class="nm-panel bc commission">
      <div class="com-form">
        <span class="com-ico"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 5L5 19" /><path d="M4 6.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /><path d="M15 17.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg></span>
        <h2 class="nm-panel-title">Platform commission</h2>
        <p class="nm-panel-sub">NutriMatch's share of each consultation fee. The RND receives the rest.</p>
        <label class="nm-label" for="commission" style="margin-top: 18px">Commission rate (%)</label>
        <div class="com-row">
          <div class="com-input">
            <input id="commission" v-model="commissionRate" class="nm-input" type="number" min="0" max="50" step="0.01" :disabled="!settingsLoaded" />
            <span aria-hidden="true">%</span>
          </div>
          <button type="button" class="nm-btn-dark" :disabled="saving || !settingsLoaded || commissionRate === currentRate" @click="saveCommission">
            {{ saving ? 'Saving…' : 'Save rate' }}
          </button>
        </div>
        <p v-if="commissionError" class="nm-field-error">{{ commissionError }}</p>
        <p v-else class="nm-hint">Between 0% and 50%.</p>
      </div>

      <!-- the split of one consultation, live as the rate changes -->
      <div class="split">
        <p class="split-title"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg>On a {{ peso(800) }} consultation</p>
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
          <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 11v5M12 8h.01" /></svg><span>Each invoice keeps the rate it was issued with. A new rate only applies to bookings confirmed after you save it, so RNDs' earnings on existing invoices never change.
          Every change is recorded in the audit log with the old and new rate.</span>
        </p>
      </div>
    </div>

    <!-- INVOICE DETAIL + RECEIPT -->
    <div v-if="selected" class="nm-modal-overlay" @click.self="closeInvoice">
      <div class="nm-modal detail" role="dialog" aria-modal="true" aria-labelledby="inv-title">
        <div class="detail-head nm-modal-head">
          <img class="im-plate" :src="plateImg" alt="" aria-hidden="true" />
          <span class="im-fade" aria-hidden="true"></span>
          <span class="im-doc" aria-hidden="true"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg></span>
          <div class="im-ht">
            <p class="im-kind">Invoice</p>
            <h3 id="inv-title" class="nm-modal-title mono" style="margin: 0">{{ invNo(selected) }}</h3>
            <p class="nm-panel-sub im-meta"><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 7v5l3 2" /></svg>Issued {{ dateTime(selected.created_at) }}</span><span class="im-amtchip">{{ peso(selected.amount) }}</span></p>
          </div>
          <div class="head-right">
            <span class="nm-pill" :class="STATUS_PILLS[selected.status] || 'muted'">{{ STATUS_LABELS[selected.status] || selected.status }}</span>
            <button type="button" class="nm-modal-x" aria-label="Close" @click="closeInvoice"><X :size="18" aria-hidden="true" /></button>
          </div>
        </div>

        <div class="im-body">
          <p v-if="detailError" class="nm-error">{{ detailError }}</p>
          <p v-else-if="!detail" class="nm-muted">Loading invoice…</p>

          <template v-else>
            <h4 class="nm-section-title im-h"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg>Consultation</h4>
            <div class="im-people">
              <div class="pc">
                <span class="pc-av" aria-hidden="true">{{ initialsOf(detail.client.name) }}</span>
                <span class="pc-t"><i class="role client">Client</i><b>{{ detail.client.name }}</b><small><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M22 6l-10 7L2 6" /></svg>{{ detail.client.email }}</small></span>
              </div>
              <div class="pc">
                <span class="pc-av" aria-hidden="true">{{ initialsOf(detail.rnd.name) }}</span>
                <span class="pc-t"><i class="role rnd">RND</i><b>{{ detail.rnd.name }}</b><small><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M22 6l-10 7L2 6" /></svg>{{ detail.rnd.email }}</small></span>
              </div>
            </div>
            <template v-if="detail.appointment">
              <div class="im-tiles">
                <div><span class="t-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg></span><small>Scheduled</small><b>{{ dateTime(detail.appointment.scheduled_at) }}</b></div>
                <div><span class="t-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="14" height="12" rx="2" /><path d="M22 8l-6 4 6 4z" /></svg></span><small>Session</small><b>{{ detail.appointment.duration_minutes || 60 }} min, {{ (MODE_LABELS[detail.appointment.type] || detail.appointment.type).toLowerCase() }}</b></div>
                <div :class="apptTone(detail.appointment.status)"><span class="t-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 22V4a1 1 0 0 1 1-1h12l-2 4 2 4H5" /></svg></span><small>Appointment</small><b>{{ APPT_LABELS[detail.appointment.status] || detail.appointment.status }}</b></div>
              </div>
              <p v-if="detail.appointment.cancellation_reason" class="im-note"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 11v5M12 8h.01" /></svg><span>{{ detail.appointment.cancellation_reason }}</span></p>
            </template>
            <div v-else class="im-tiles one">
              <div class="muted"><span class="t-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 22V4a1 1 0 0 1 1-1h12l-2 4 2 4H5" /></svg></span><small>Appointment</small><b>No longer linked</b></div>
            </div>

            <h4 class="nm-section-title im-h"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg>Amount</h4>
            <div class="lines">
              <div class="line"><span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>Consultation fee</span><span>{{ peso(detail.amount) }}</span></div>
              <div class="line"><span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 5L5 19" /><path d="M4 6.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /><path d="M15 17.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg>Platform commission <em class="pct-chip">{{ Number(detail.commission_pct) }}%</em></span><span class="neg">− {{ peso(detail.commission_amt) }}</span></div>
              <div class="split-mini" aria-hidden="true">
                <span class="sm-rnd" :style="{ width: `${100 - Number(detail.commission_pct)}%` }">RND {{ 100 - Number(detail.commission_pct) }}%</span>
                <span class="sm-plat" :style="{ width: `${Number(detail.commission_pct)}%` }">{{ Number(detail.commission_pct) }}%</span>
              </div>
              <div class="line total"><span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3" /><path d="M21 9h-6a3 3 0 0 0 0 6h6z" /></svg>RND's share</span><span>{{ peso(detail.net) }}</span></div>
              <p class="nm-hint lines-foot"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 7v5l3 2" /></svg>{{ detail.payout ? 'Paid out to the RND in a monthly payout.' : 'Not paid out to the RND yet.' }}</p>
            </div>

            <h4 class="nm-section-title im-h"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3v18l2-1.5L9 21l2-1.5L13 21l2-1.5L17 21l2-1.5V3l-2 1.5L15 3l-2 1.5L11 3 9 4.5 7 3z" /><path d="M9 9h6M9 13h6" /></svg>Payment receipt</h4>
            <div v-if="payment" class="receipt">
              <div class="receipt-top">
                <span class="rc-ok"><CheckCircle2 :size="22" aria-hidden="true" /></span>
                <div>
                  <p class="receipt-amount">{{ peso(payment.receipt.amount || payment.amount) }}</p>
                  <p class="nm-hint" style="margin: 0">Paid by {{ payment.receipt.payer_name || detail.client.name }} · {{ dateTime(payment.receipt.paid_at || detail.paid_at || payment.processed_at) }}</p>
                </div>
                <span v-if="payment.receipt.livemode === false" class="nm-pill gold test-pill">Test mode</span>
              </div>
              <dl class="receipt-rows">
                <div><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /></svg>Payment method</dt><dd>{{ methodText }}</dd></div>
                <div v-if="payment.receipt.payment_id"><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18" /></svg>PayMongo payment ID</dt><dd class="mono code">{{ payment.receipt.payment_id }}</dd></div>
                <div v-if="detail.gateway_reference_id"><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18" /></svg>Reference no.</dt><dd class="mono code">{{ detail.gateway_reference_id }}</dd></div>
                <div v-if="payment.receipt.payer_email"><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M22 6l-10 7L2 6" /></svg>Payer email</dt><dd>{{ payment.receipt.payer_email }}</dd></div>
                <div v-if="payment.receipt.payer_phone"><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2" /><path d="M11 18h2" /></svg>Payer phone</dt><dd>{{ payment.receipt.payer_phone }}</dd></div>
                <div v-if="payment.receipt.description"><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>Description</dt><dd>{{ payment.receipt.description }}</dd></div>
                <div v-if="payment.receipt.fee"><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 5L5 19" /><path d="M4 6.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /><path d="M15 17.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg>PayMongo fee</dt><dd>− {{ peso(payment.receipt.fee) }}</dd></div>
                <div v-if="payment.receipt.net_amount"><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg>Received by NutriMatch</dt><dd><strong>{{ peso(payment.receipt.net_amount) }}</strong></dd></div>
                <div><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" /><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" /></svg>Recorded via</dt><dd>{{ SOURCE_LABELS[payment.source] || payment.source || '—' }}</dd></div>
              </dl>
              <p v-if="!payment.receipt.payment_id" class="nm-hint receipt-hint">
                The gateway's receipt details weren't stored for this payment{{ payment.source === 'seed_demo' ? ' (demo data)' : '' }}, so only NutriMatch's record is shown.
              </p>
            </div>
            <div v-else class="nm-empty receipt-empty">
              <span class="e-ico"><Receipt :size="24" aria-hidden="true" /></span>
              <p>{{ selected.status === 'unpaid' ? 'The client hasn\'t paid this invoice yet.' : 'No payment was made on this invoice.' }}</p>
            </div>

            <div v-if="payment?.receipt?.payment_id" class="pm-box">
              <div class="pm-head">
                <span class="pm-ico" aria-hidden="true"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1" /><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1" /></svg></span>
                <h4 class="nm-section-title" style="margin: 0">In PayMongo</h4>
                <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="pmLoading" @click="checkPayMongo"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 0 1-15.5 6.2L3 16" /><path d="M3 12a9 9 0 0 1 15.5-6.2L21 8" /><path d="M21 3v5h-5M3 21v-5h5" /></svg>{{ pmLoading ? 'Checking…' : 'Check with PayMongo' }}</button>
              </div>
              <p v-if="pmError" class="nm-error" style="margin: 8px 0 0">{{ pmError }}</p>
              <template v-else-if="pm">
                <p class="pm-line">
                  Payment <span class="mono code">{{ pm.payment_id }}</span>
                  <strong class="pm-state" :class="pm.refunded ? 'muted' : pm.in_progress ? 'gold' : 'green'">{{ pm.refunded ? 'Refunded' : pm.in_progress ? 'Refund in progress' : 'Paid' }}</strong>
                  <span v-if="pm.livemode === false" class="nm-pill gold" style="margin-left: 6px">Test mode</span>
                </p>
                <p v-if="!pm.refunds.length" class="nm-hint pm-none"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 11v5M12 8h.01" /></svg>No refund sent to PayMongo yet.</p>
                <div v-for="r in pm.refunds" :key="r.id" class="line pm-refund">
                  <span><span class="mono">{{ r.id }}</span><span class="sub">{{ dateTime(unix(r.refunded_at || r.created_at)) }}</span></span>
                  <span>{{ peso(r.amount) }} <span class="nm-pill" :class="PM_REFUND_PILLS[r.status] || 'muted'">{{ PM_REFUND_LABELS[r.status] || r.status }}</span></span>
                </div>
                <p v-if="pm.refunds.some(r => r.status === 'failed') && pm.source_type === 'qrph' && pm.livemode === false" class="nm-hint" style="margin: 6px 0 0">
                  PayMongo's test mode can't complete QR Ph refunds. GCash, Maya and card refunds work in test mode.
                </p>
              </template>
            </div>

            <template v-if="refunds.length">
              <h4 class="nm-section-title im-h"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg>Refunds</h4>
              <div class="lines">
                <div v-for="r in refunds" :key="r.id" class="line">
                  <span class="col">Refunded {{ dateTime(r.processed_at || r.created_at) }}<span v-if="r.reference" class="sub mono">Ref {{ r.reference }}</span></span>
                  <span>{{ peso(r.amount) }}</span>
                </div>
              </div>
            </template>
          </template>
        </div>

        <div class="nm-modal-actions im-foot">
          <button type="button" class="nm-btn-soft" @click="closeInvoice">Close</button>
          <button v-if="selected.status === 'refund_pending' && selected.paymongo_payment_id" type="button" class="nm-btn-dark" @click="askRefund(selected)"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg>Refund through PayMongo</button>
        </div>
      </div>
    </div>

    <!-- REFUND CONFIRMATION: money leaves for good, so the button waits 3 seconds -->
    <div v-if="refundConfirm" class="nm-modal-overlay" style="z-index: 310" @click.self="refundBusy ? null : closeRefund()">
      <div class="nm-modal rc-modal" role="dialog" aria-modal="true" aria-labelledby="refund-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="refundBusy ? null : closeRefund()"><X :size="18" aria-hidden="true" /></button>
        <span class="rcm-ico" aria-hidden="true"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg></span>
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

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
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
const toast = useToast() // the app's toast (2026-11-03)

function flash(msg, opts) {
  toast.success(msg, opts)
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const initialsOf = name => { const w = String(name || '?').split(' ').filter(Boolean); return (w.length > 1 ? w[0][0] + w[w.length - 1][0] : (w[0] || '?')[0]).toUpperCase() }
const apptTone = s => (s === 'cancelled' ? 'bad' : s === 'completed' ? 'good' : '')
</script>

<style scoped>
.bl { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.mono { font-variant-numeric: tabular-nums; }
.ic { flex-shrink: 0; display: inline-block; }

/* ---------- hero ---------- */
.bh { position: relative; overflow: hidden; margin-bottom: 26px; padding: 26px 30px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.bh-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.bh-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 52%, rgba(0, 77, 58, 0.85) 72%, rgba(0, 77, 58, 0.6) 100%); }
.bh-txt { position: relative; z-index: 1; max-width: 620px; }
.bh-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.bh-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.bh-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; color: #fff; }
.bh-sub { margin: 0; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }

/* ---------- at a glance ---------- */
.glance { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-bottom: 24px; }
.fig { position: relative; display: flex; flex-direction: column; align-items: flex-start; gap: 4px; min-width: 0; padding: 20px 22px; border: 1.5px solid #c9d8cf; border-radius: 20px; background: #fff; box-shadow: 0 10px 24px -18px rgba(0, 77, 58, 0.35); font-family: inherit; text-align: left; color: #0e3a2c; }
button.fig { cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
button.fig:hover { transform: translateY(-2px); box-shadow: 0 16px 30px -18px rgba(0, 77, 58, 0.45); }
.fig:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.fig-ico { width: 42px; height: 42px; margin-bottom: 10px; border-radius: 13px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.fig-label { font-size: 13px; font-weight: 700; color: #4a5a52; }
.fig strong { font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.15; color: #0e3a2c; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.fig-note { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; line-height: 1.4; color: #6b7d73; }
.fig-note b { color: #004d3a; }
.fig-btn { display: inline-flex; align-items: center; gap: 6px; height: 32px; margin-top: 2px; padding: 0 12px; border-radius: 10px; background: #004d3a; color: #fff; font-size: 12.5px; font-weight: 800; text-decoration: none; }
.fig-btn .ic { color: #efbf04; }
.fig.warn { border-color: #efbf04; background: linear-gradient(180deg, #fffbea 0%, #fff 70%); }
.fig.warn .fig-ico { background: #efbf04; color: #004d3a; }
.fig strong.warn { color: #8a6500; }
.fig-note.warn { font-weight: 800; color: #8a6500; }

/* ---------- tabs + tools ---------- */
.bt-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.bt-tabs { display: inline-flex; gap: 4px; max-width: 100%; margin: 0; padding: 5px; border: none; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); overflow-x: auto; scrollbar-width: none; }
.bt-tabs::-webkit-scrollbar { display: none; }
.bt-tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 36px; margin: 0; padding: 0 15px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.bt-tabs .nm-tab .ic { color: #8a9a91; }
.bt-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; }
.bt-tabs .nm-count { min-width: 20px; height: 20px; margin-left: 2px; padding: 0 6px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 700; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.bt-tabs .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.bt-tabs .nm-tab.active .ic { color: #efbf04; }
.bt-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }
.bill-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.bt-sel, .bt-search { position: relative; display: flex; align-items: center; gap: 10px; height: 46px; margin: 0; padding: 0 16px; border: none; border-radius: 999px; background: #fff; color: #1f7a4d; box-sizing: border-box; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); }
.bt-sel:focus-within, .bt-search:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.bt-sel { min-width: 180px; cursor: pointer; }
.bt-sel .nm-select { flex: 1; width: auto; min-width: 0; height: 100%; padding: 0 !important; border: none !important; background: transparent !important; box-shadow: none !important; outline: none; appearance: none; -webkit-appearance: none; font-family: inherit; font-size: 14px; font-weight: 600; color: #14261e; cursor: pointer; }
.bt-search { width: 320px; max-width: 100%; color: #8a9a91; }
.bt-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.bt-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; box-shadow: none !important; font-family: inherit; font-size: 14px; color: #14261e; }

/* ---------- panel ---------- */
.bc { padding: 0; border: none; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: hidden; }
.bc-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin: 0; padding: 24px 30px 20px; }
.bc-head .nm-panel-title { margin: 0 0 4px; font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; color: #0e3a2c; }
.bc-head .nm-panel-sub { margin: 0; font-size: 13.5px; color: #6b7d73; }
.ledger-count { flex-shrink: 0; padding: 5px 12px; border-radius: 999px; background: #e3efe7; font-size: 12.5px; font-weight: 800; color: #004d3a; white-space: nowrap; }
.bc-pad { padding: 0 30px 26px; }
.bl :deep(.nm-empty) { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 26px 10px; text-align: center; }
.bl :deep(.nm-empty p) { margin: 0; font-size: 14px; font-weight: 600; color: #4a5a52; }
.e-ico { width: 56px; height: 56px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.bc-pager { padding: 0 30px; }
.bc-pager :deep(.nm-pager) { margin: 0; padding: 14px 0 18px; }

/* ---------- ledger ---------- */
.ledger-scroll { margin: 0; border: none; border-radius: 0; overflow-x: auto; }
.ledger { width: 100% !important; min-width: 980px; table-layout: fixed; border-collapse: collapse; font-size: 14px; }
.ledger th:nth-child(1) { width: 12%; }
.ledger th:nth-child(2) { width: 23%; }
.ledger th:nth-child(3) { width: 11%; }
.ledger th:nth-child(4) { width: 11%; }
.ledger th:nth-child(5) { width: 13%; }
.ledger th:nth-child(6) { width: 12%; }
.ledger th:nth-child(7) { width: 18%; }
.ledger thead th { position: static; padding: 14px 14px; background: #004d3a; border: none; box-shadow: none; text-align: left; font-size: 12.5px; font-weight: 700; color: #fff; white-space: nowrap; text-transform: none; letter-spacing: 0; }
.ledger thead th .ic { margin-right: 7px; vertical-align: -2px; color: #efbf04; }
.ledger th.nm-num, .ledger td.nm-num, .ledger thead th { text-align: left !important; }
.ledger th:first-child, .ledger td:first-child { padding-left: 30px; }
.ledger th:last-child, .ledger td:last-child { padding-right: 30px; }
.ledger tbody td { position: relative; padding: 16px 14px; border-bottom: 1px solid #eef2ef; vertical-align: middle; color: #22362c; }
.ledger tbody tr:last-child td { border-bottom: none; }
.ledger tbody tr.clickable { cursor: pointer; }
.ledger tbody tr.clickable:hover td { background: #f7faf8; }
.ledger tbody tr:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
@media (min-width: 641px) {
  .ledger tbody td:first-child::before { content: ''; position: absolute; left: 0; top: 14px; bottom: 14px; width: 4px; border-radius: 0 4px 4px 0; background: #c9d3cd; }
  .ledger tbody tr.tone-gold td:first-child::before { background: #efbf04; }
  .ledger tbody tr.tone-green td:first-child::before { background: #1f9d55; }
}
.inv-chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 9px; background: #f1f6f2; font-size: 13px; font-weight: 800; color: #004d3a; }
.inv-chip .ic { color: #1f7a4d; }
.cell-sub { display: block; margin-top: 5px; font-size: 12.5px; color: #8a9a91; }
.cell-sub em { font-style: normal; font-weight: 700; color: #1f7a4d; }
.pt { display: flex; align-items: center; gap: 12px; min-width: 0; }
.pt-av { flex-shrink: 0; width: 38px; height: 38px; border-radius: 50%; background: #e3efe7; color: #004d3a; font-size: 12.5px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; border: 2px solid #fff; box-shadow: 0 0 0 2px #efbf04; }
.pt-txt { min-width: 0; }
.pt-txt b { display: block; font-size: 14.5px; color: #0e3a2c; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pt-txt .cell-sub { margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pay-chip { display: inline-flex; align-items: center; gap: 6px; padding: 5px 11px; border-radius: 999px; border: 1px solid #dce8e0; font-size: 12.5px; font-weight: 700; color: #22362c; white-space: nowrap; }
.pay-chip .ic { color: #1f7a4d; }
.pct { margin-left: 6px; padding: 2px 7px; border-radius: 999px; background: #eef1fa; font-size: 11px; font-weight: 800; color: #2e4a86; }
.share { font-weight: 800; color: #004d3a !important; }
.bl :deep(.nm-pill) { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; font-size: 12px; font-weight: 800; white-space: nowrap; }
.bl :deep(.nm-pill)::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.bl :deep(.nm-pill.gold) { background: #fff4d6; color: #8a6500; }
.bl :deep(.nm-pill.green) { background: #e3f4ea; color: #1f7a4d; }
.bl :deep(.nm-pill.red) { background: #fde2df; color: #b42318; }
.bl :deep(.nm-pill.muted) { background: #f3f6f4; color: #6b7d73; }

/* ---------- refunds ---------- */
.rf-list { display: flex; flex-direction: column; gap: 12px; }
.refund { display: flex; align-items: center; gap: 18px; flex-wrap: wrap; padding: 16px 18px; border: 1.5px solid #c9d8cf; border-left: 4px solid #efbf04; border-radius: 18px; background: #fff; }
.refund-amount { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; min-width: 140px; padding-right: 18px; border-right: 1px dashed #c9d8cf; }
.ra-ico { width: 32px; height: 32px; margin-bottom: 4px; border-radius: 10px; background: #fff4d6; color: #8a6500; display: inline-flex; align-items: center; justify-content: center; }
.refund-amount strong { font-family: 'Playfair Display', serif; font-size: 22px; color: #0e3a2c; }
.refund-amount span { font-size: 12.5px; color: #6b7d73; }
.refund-main { flex: 1; min-width: 220px; }
.refund-main .nm-row-title { margin: 0 0 4px; font-size: 15px; font-weight: 800; color: #0e3a2c; }
.refund-main .nm-row-sub { margin: 0; font-size: 13px; color: #6b7d73; }
.refund-main .nm-text-link { padding: 0; border: 0; background: none; font: inherit; font-weight: 800; color: #1f7a4d; cursor: pointer; }
.refund-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.refund-actions .nm-input { width: 220px; max-width: 100%; height: 42px; border: 1.5px solid #c9d8cf; border-radius: 12px; }
.refund-state { margin: 8px 0 0; padding: 7px 11px; border-radius: 10px; background: #f3f6f4; font-size: 12.5px; color: #4a5a52; }
.refund-state.bad { background: #fef3f2; color: #a12525; }
.refund-state.wait { background: #fff8e1; color: #8a6500; }

/* buttons in this page */
.bl .nm-btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 42px; padding: 0 18px; border: none; border-radius: 12px; background: #004d3a; color: #fff; font-family: inherit; font-size: 13.5px; font-weight: 800; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); cursor: pointer; }
.bl .nm-btn-dark .ic { color: #efbf04; }
.bl .nm-btn-dark:disabled { opacity: 0.45; box-shadow: none; cursor: not-allowed; }
.bl .nm-btn-soft { display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 42px; padding: 0 18px; border: 1px solid #dce8e0; border-radius: 12px; background: #fff; color: #004d3a; font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; }
.bl .nm-btn-soft.nm-btn-sm { height: 38px; padding: 0 14px; font-size: 13px; }
.bl .nm-btn-soft .ic { color: #1f7a4d; }

/* ---------- commission ---------- */
.commission { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr); gap: 0; }
.com-form { padding: 28px 30px; }
.com-ico { width: 48px; height: 48px; margin-bottom: 14px; border-radius: 15px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.com-form .nm-panel-title { margin: 0 0 4px; font-family: 'Playfair Display', serif; font-size: 22px; color: #0e3a2c; }
.com-form .nm-panel-sub { margin: 0; font-size: 13.5px; color: #6b7d73; }
.com-form .nm-label { display: block; margin-bottom: 8px; font-size: 13px; font-weight: 700; color: #22362c; }
.com-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.com-input { position: relative; width: 150px; }
.com-input .nm-input { width: 100%; max-width: none; height: 46px; padding: 0 34px 0 16px; border: 1.5px solid #c9d8cf; border-radius: 14px; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; box-sizing: border-box; }
.com-input .nm-input:focus { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); outline: none; }
.com-input span { position: absolute; right: 14px; top: 50%; transform: translateY(-50%); font-weight: 800; color: #8a9a91; pointer-events: none; }
.com-row .nm-btn-dark { height: 46px; }
.split { padding: 28px 30px; border-left: 1px solid #eef2ef; background: #f7faf8; }
.split-title { display: flex; align-items: center; gap: 8px; margin: 0 0 14px; font-size: 15px; font-weight: 800; color: #0e3a2c; }
.split-title .ic { color: #1f7a4d; }
.split-bar { height: 18px; border-radius: 999px; background: #9fcfb3; overflow: hidden; }
.split-ours { display: block; height: 100%; background: #004d3a; border-radius: 999px 0 0 999px; transition: width 0.2s ease; }
.split-legend { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-top: 12px; font-size: 13px; color: #4a5a52; }
.split-legend strong { color: #0e3a2c; }
.key { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 4px; vertical-align: -1px; }
.key.ours { background: #004d3a; }
.key.theirs { background: #9fcfb3; }
.split-note { display: flex; gap: 10px; margin: 20px 0 0; padding: 12px 14px; border-radius: 14px; background: #eef1fa; font-size: 13px; line-height: 1.55; color: #2e4a86; }
.split-note .ic { margin-top: 1px; }
@media (prefers-reduced-motion: reduce) { .split-ours { transition: none; } }

/* ---------- invoice pop-up ---------- */
.nm-modal-overlay .nm-modal.detail { display: flex; flex-direction: column; width: min(920px, calc(100vw - 32px)) !important; max-width: 920px !important; min-width: 0 !important; height: auto !important; max-height: calc(100vh - 48px) !important; margin: auto !important; padding: 0 !important; border-radius: 24px; overflow: hidden !important; }
.detail-head { position: relative; overflow: hidden; flex-shrink: 0; display: flex; align-items: center; gap: 16px; margin: 0; padding: 22px 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 55%, #004635 100%); border: none; }
.detail-head > *:not(.im-plate):not(.im-fade) { position: relative; z-index: 1; }
.im-plate { position: absolute; right: -60px; top: 50%; width: 220px; height: 220px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.im-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 55%, rgba(0, 77, 58, 0.88) 75%, rgba(0, 77, 58, 0.7) 100%); }
.im-doc { flex-shrink: 0; width: 56px; height: 60px; border-radius: 14px; background: #fff; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 24px -10px rgba(0, 0, 0, 0.4); }
.im-ht { flex: 1; min-width: 0; }
.im-kind { margin: 0 0 2px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.2px; text-transform: uppercase; color: #efbf04; }
.im-ht .nm-modal-title { font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; letter-spacing: 0.02em; color: #fff; }
.im-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin: 4px 0 0; font-size: 13px; color: rgba(255, 255, 255, 0.82) !important; }
.im-meta > span { display: inline-flex; align-items: center; gap: 6px; }
.im-amtchip { padding: 2px 10px; border-radius: 999px; background: rgba(255, 255, 255, 0.16); font-weight: 800; color: #fff; }
.head-right { display: flex; align-items: center; gap: 10px; }
.detail-head :deep(.nm-pill.gold) { background: #efbf04; color: #004d3a; }
.detail-head :deep(.nm-pill.green) { background: #e3f4ea; color: #1f7a4d; }
.detail-head :deep(.nm-pill.muted) { background: rgba(255, 255, 255, 0.18); color: #fff; }
.nm-modal.detail .detail-head { position: relative !important; top: auto !important; margin: 0 !important; padding: 24px 28px !important; min-height: 0 !important; height: auto !important; align-items: center !important; border: none !important; }
.nm-modal.detail .detail-head .nm-modal-x { position: static !important; inset: auto !important; top: auto !important; right: auto !important; float: none !important; flex-shrink: 0; width: 38px !important; height: 38px !important; margin: 0 !important; padding: 0 !important; border: 1px solid rgba(255, 255, 255, 0.25) !important; border-radius: 12px !important; background: rgba(0, 0, 0, 0.22) !important; color: #fff !important; opacity: 1 !important; display: inline-flex !important; align-items: center; justify-content: center; cursor: pointer; }
.nm-modal.detail .detail-head .nm-modal-x:hover { background: rgba(0, 0, 0, 0.35) !important; }
.nm-modal.detail .im-ht .nm-modal-title { margin: 0 !important; padding: 0 !important; line-height: 1.2; color: #fff !important; }
.nm-modal.detail .im-kind { line-height: 1.3; }
.im-body { flex: 1 1 auto; min-height: 0 !important; max-height: none !important; overflow-y: auto !important; overscroll-behavior: contain; -webkit-overflow-scrolling: touch; padding: 24px 28px 28px; }
.im-h { display: flex; align-items: center; gap: 8px; margin: 24px 0 12px; font-family: 'Playfair Display', serif !important; font-size: 18px; font-weight: 700; color: #0e3a2c; }
.im-h:first-child { margin-top: 0; }
.im-h .ic { color: #1f7a4d; }
.im-people { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.pc { display: flex; align-items: center; gap: 12px; min-width: 0; padding: 14px; border: 1.5px solid #c9d8cf; border-radius: 16px; }
.pc-av { flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%; background: #e3efe7; color: #004d3a; font-size: 13px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; border: 2px solid #fff; box-shadow: 0 0 0 2px #efbf04; }
.pc-t { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
.pc-t b { font-size: 15px; color: #0e3a2c; }
.pc-t small { display: flex; align-items: center; gap: 5px; max-width: 100%; font-size: 12.5px; color: #6b7d73; overflow-wrap: anywhere; }
.role { padding: 2px 8px; border-radius: 999px; font-style: normal; font-size: 10.5px; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase; }
.role.client { background: #fff4d6; color: #8a6500; }
.role.rnd { background: #e3f4ea; color: #1f7a4d; }
.im-tiles { display: grid; grid-template-columns: 1.3fr 1fr 1fr; gap: 12px; margin-top: 12px; }
.im-tiles.one { grid-template-columns: 1fr; }
.im-tiles > div { display: grid; grid-template-columns: 38px 1fr; column-gap: 12px; row-gap: 1px; align-items: center; padding: 12px 14px; border: 1px solid #e3ebe6; border-radius: 16px; background: #f7faf8; }
.t-ico { grid-row: span 2; width: 38px; height: 38px; border-radius: 12px; background: #fff; color: #004d3a; box-shadow: 0 0 0 1px #e3ebe6; display: inline-flex; align-items: center; justify-content: center; }
.im-tiles small { font-size: 12px; font-weight: 700; color: #6b7d73; }
.im-tiles b { font-size: 14.5px; color: #0e3a2c; }
.im-tiles .bad { background: #fef3f2; border-color: #f6cfcb; }
.im-tiles .bad .t-ico { color: #b42318; box-shadow: 0 0 0 1px #f6cfcb; }
.im-tiles .bad b { color: #8c1d2c; }
.im-tiles .good { background: #f1f8f4; border-color: #cfe6d7; }
.im-tiles .good b { color: #1f7a4d; }
.im-tiles .muted b { color: #6b7d73; }
.im-note { display: flex; gap: 10px; margin: 12px 0 0; padding: 12px 14px; border-radius: 14px; background: #eef1fa; font-size: 13.5px; line-height: 1.5; color: #2e4a86; }
.im-note .ic { margin-top: 1px; }
.lines { padding: 0; border: 1.5px solid #c9d8cf; border-radius: 18px; overflow: hidden; }
.line { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 14px 18px; font-size: 14.5px; color: #22362c; }
.line + .line { border-top: 1px solid #eef2ef; }
.line > span:first-child { display: inline-flex; align-items: center; gap: 9px; }
.line > span:first-child > .ic { color: #1f7a4d; }
.line > span.col { display: block; }
.line > span:last-child { font-weight: 700; color: #0e3a2c; font-variant-numeric: tabular-nums; white-space: nowrap; }
.line .neg { color: #b42318 !important; }
.pct-chip { padding: 2px 7px; border-radius: 999px; background: #eef1fa; font-style: normal; font-size: 11px; font-weight: 800; color: #2e4a86; }
.split-mini { display: flex; height: 26px; margin: 4px 18px 14px; border-radius: 999px; overflow: hidden; font-size: 11.5px; font-weight: 800; }
.split-mini span { display: flex; align-items: center; min-width: 0; padding: 0 12px; white-space: nowrap; overflow: hidden; }
.sm-rnd { background: #e3f4ea; color: #1f7a4d; }
.sm-plat { justify-content: center; padding: 0 !important; background: #eef1fa; color: #2e4a86; }
.line.total { border-top: none; background: #004d3a; color: #fff; font-weight: 800; }
.line.total > span:first-child > .ic { color: #efbf04; }
.line.total > span:last-child { font-family: 'Playfair Display', serif; font-size: 20px; color: #efbf04; }
.lines-foot { display: flex; align-items: center; gap: 6px; margin: 0; padding: 10px 18px; background: #f7faf8; font-size: 12.5px; color: #6b7d73; }
.receipt { padding: 0; border: 1.5px solid #c9d8cf; border-radius: 18px; background: #fff; overflow: hidden; }
.receipt-top { display: flex; align-items: center; gap: 14px; padding: 16px 18px; background: #f1f8f4; border-bottom: 1px dashed #c9d8cf; }
.rc-ok { flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%; background: #1f9d55; color: #fff; display: inline-flex; align-items: center; justify-content: center; }
.receipt-top > div { flex: 1; min-width: 0; }
.receipt-amount { margin: 0; font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 700; color: #0e3a2c; font-variant-numeric: tabular-nums; }
.receipt-top .nm-hint { font-size: 12.5px; color: #6b7d73; }
.test-pill { margin-left: auto; }
.receipt-rows { display: grid; grid-template-columns: 1fr 1fr; gap: 1px; margin: 0; background: #eef2ef; }
.receipt-rows > div { display: flex; flex-direction: column; gap: 4px; min-width: 0; padding: 13px 18px; background: #fff; }
.receipt-rows > div:last-child:nth-child(odd) { grid-column: 1 / -1; }
.receipt-rows dt { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 700; color: #6b7d73; }
.receipt-rows dt .ic { color: #1f7a4d; }
.receipt-rows dd { margin: 0; font-size: 14px; color: #0e3a2c; overflow-wrap: anywhere; }
.code { align-self: flex-start; max-width: 100%; padding: 3px 8px; border-radius: 8px; background: #f1f6f2; font-family: ui-monospace, Menlo, monospace; font-size: 12.5px; color: #004d3a; overflow-wrap: anywhere; }
.receipt-hint { margin: 0; padding: 12px 18px; border-top: 1px solid #eef2ef; background: #f7faf8; font-size: 12.5px; }
.receipt-empty { border: 1.5px dashed #c9d8cf; border-radius: 18px; }
.pm-box { margin-top: 14px; padding: 16px 18px; border: 1.5px solid #c9d8cf; border-radius: 18px; background: linear-gradient(90deg, #f1f8f4 0%, #fff 60%); }
.pm-head { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.pm-ico { flex-shrink: 0; width: 40px; height: 40px; border-radius: 13px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.pm-head .nm-section-title { flex: 1; font-family: 'Playfair Display', serif; font-size: 17px; color: #0e3a2c; }
.pm-line { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 12px 0 0; font-size: 13.5px; color: #4a5a52; }
.pm-state { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.pm-state.green { background: #e3f4ea; color: #1f7a4d; }
.pm-state.gold { background: #fff4d6; color: #8a6500; }
.pm-state.muted { background: #f3f6f4; color: #6b7d73; }
.pm-none { display: flex; align-items: center; gap: 6px; margin: 8px 0 0; font-size: 12.5px; font-weight: 600; color: #8a6500; }
.pm-refund { margin-top: 10px; padding: 10px 12px; border: 1px solid #eef2ef; border-radius: 12px; background: #fff; }
.sub { display: block; margin-top: 2px; font-size: 12px; font-weight: 400; color: #8a9a91; }
.im-foot { flex-shrink: 0; display: flex; justify-content: flex-end; gap: 10px; margin: 0; padding: 14px 28px; border-top: 1px solid #eef2ef; background: #f7faf8; }

/* refund confirm */
.rc-modal { border-radius: 24px; }
.rcm-ico { width: 52px; height: 52px; margin-bottom: 14px; border-radius: 16px; background: #fff4d6; color: #8a6500; display: inline-flex; align-items: center; justify-content: center; }
.rc-modal .nm-modal-title { font-family: 'Playfair Display', serif; font-size: 22px; color: #0e3a2c; }

@media (max-width: 999px) {
  .glance { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
  .fig { padding: 16px; }
  .fig strong { font-size: 24px; }
  .commission { grid-template-columns: minmax(0, 1fr); }
  .split { border-left: none; border-top: 1px solid #eef2ef; }
}
@media (max-width: 760px) {
  .bl { padding-bottom: 110px; }
  .bh { padding: 20px 18px; border-radius: 22px; }
  .bh-title { font-size: 24px; }
  .bh-plate { width: 180px; height: 180px; right: -60px; top: 20px; transform: none; }
  .bh-txt { max-width: 72%; }
  .bt-tabs { display: flex; width: 100%; border-radius: 16px; }
  .bill-tools { width: 100%; }
  .bt-search { flex: 1 1 100%; width: 100%; order: -1; }
  .bt-sel { flex: 1; }
  .nm-modal-overlay .nm-modal.detail { width: calc(100vw - 24px) !important; max-height: calc(100dvh - 24px) !important; border-radius: 22px; }
  .detail-head { flex-wrap: wrap; padding: 18px; }
  .im-ht .nm-modal-title { font-size: 22px; }
  .im-doc { width: 48px; height: 52px; }
  .head-right { width: 100%; justify-content: space-between; }
  .im-body { padding: 18px; }
  .im-people, .receipt-rows { grid-template-columns: 1fr; }
  .receipt-rows > div:last-child:nth-child(odd) { grid-column: auto; }
  .im-tiles { grid-template-columns: 1fr 1fr; }
  .im-tiles > div:last-child { grid-column: 1 / -1; }
  .im-foot { padding: 12px 18px; }
  .im-foot > button { flex: 1; }
}
@media (max-width: 640px) {
  .bc-head { padding: 18px; }
  .bc-pad { padding: 0 18px 18px; }
  .bc-pager { padding: 0 18px; }
  .ledger { min-width: 0; table-layout: auto; }
  .ledger thead { display: none; }
  .ledger tbody tr { border-left: 4px solid #c9d3cd; }
  .ledger tbody tr.tone-gold { border-left-color: #efbf04; }
  .ledger tbody tr.tone-green { border-left-color: #1f9d55; }
  .ledger tbody td, .ledger td:first-child, .ledger td:last-child { padding-left: 16px; padding-right: 16px; }
  .refund-amount { border-right: none; padding-right: 0; }
  .refund-actions { width: 100%; }
  .refund-actions > * { flex: 1; }
  .com-form, .split { padding: 20px 18px; }
}
</style>