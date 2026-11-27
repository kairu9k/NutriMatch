<template>
  <div class="nm-page po">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- THE RUN SHEET: payout day, what's ready, and how money gets there -->
    <section class="ph run-day">
      <img class="ph-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="ph-fade" aria-hidden="true"></span>
      <div class="ph-txt">
        <p class="ph-eyebrow"><span></span>Payouts</p>
        <h2 class="run-day-title">{{ run ? dayTitle : 'Loading…' }}</h2>
        <p class="run-day-sub">{{ daySub }}</p>
      </div>
      <!-- the month between two payout days, with today on it -->
      <div v-if="cycle" class="cycle">
        <div class="cy-top">
          <span class="cy-ico"><CalendarClock :size="19" aria-hidden="true" /></span>
          <p class="cycle-left"><strong>{{ daysLeft === 0 ? 'Today' : daysLeft }}</strong>{{ daysLeft === 0 ? '' : ` day${daysLeft === 1 ? '' : 's'} to go` }}</p>
        </div>
        <div class="cycle-bar" role="img" :aria-label="`${cycle.pct}% of the way from ${cycle.from} to ${cycle.to}`">
          <span class="cycle-fill" :style="{ width: `${cycle.pct}%` }"></span>
          <span class="cycle-now" :style="{ left: `${cycle.pct}%` }"></span>
        </div>
        <div class="cycle-ends"><span>{{ cycle.from }}</span><span>{{ cycle.to }}</span></div>
      </div>
    </section>

    <!-- the money from left to right: on hold, then cleared and waiting, then ready on payday -->
    <ol class="pipe" aria-label="How an RND's share is paid">
      <li class="pp p1">
        <span class="pp-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 7v5l3 2" /></svg></span>
        <div>
          <span class="fig-label"><b>1</b>On hold</span>
          <strong>{{ peso(pendingTotal) }}</strong>
          <span class="fig-note">Clears {{ run?.hold_days ?? 3 }} days after the consultation</span>
          <span class="pp-how">For {{ run?.hold_days ?? 3 }} days after the consultation is completed, in case the client needs a refund.</span>
        </div>
      </li>
      <li class="pp p2">
        <span class="pp-ico"><CheckCircle2 :size="18" aria-hidden="true" /></span>
        <div>
          <span class="fig-label"><b>2</b>Cleared, waiting</span>
          <strong :class="{ warn: heldTotal > 0 }">{{ peso(heldTotal) }}</strong>
          <span class="fig-note" :class="{ warn: heldRows.length }">{{ heldRows.length ? `${heldRows.length} RND${heldRows.length === 1 ? '' : 's'}, see why below` : 'Nothing waiting' }}</span>
          <span class="pp-how">Now the RND's. It waits for payday, the {{ ordinal(payoutDay) }}, and needs {{ peso(run?.minimum_payout ?? 500) }} or more, otherwise it carries over.</span>
        </div>
      </li>
      <li class="pp p3">
        <span class="pp-ico"><Send :size="18" aria-hidden="true" /></span>
        <div>
          <span class="fig-label"><b>3</b>Ready to send</span>
          <strong>{{ peso(run?.due_total ?? 0) }}</strong>
          <span class="fig-note">{{ dueRows.length }} RND{{ dueRows.length === 1 ? '' : 's' }}</span>
          <span class="pp-how">On payday, send it by GCash or bank, then record the receipt's reference here.</span>
        </div>
      </li>
    </ol>

    <div class="nm-toolbar po-bar">
      <div class="nm-tabs po-tabs">
        <button type="button" class="nm-tab" :class="{ active: tab === 'run' }" @click="tab = 'run'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>This month <span class="nm-count">{{ rows.length }}</span></button>
        <button type="button" class="nm-tab" :class="{ active: tab === 'history' }" @click="tab = 'history'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5M12 8v4l3 2" /></svg>History <span class="nm-count">{{ history.length }}</span></button>
      </div>
    </div>

    <!-- THIS MONTH: who to pay now, then everything still on its way -->
    <template v-if="tab === 'run'">
      <p v-if="loading" class="nm-panel nm-muted po-loading">Loading balances…</p>
      <div v-else-if="!rows.length" class="nm-panel nm-empty po-card">
        <span class="e-ico"><Wallet :size="28" aria-hidden="true" /></span>
        <p>No RND has earnings yet.</p>
      </div>
      <template v-else>
        <!-- READY TO SEND -->
        <section class="now" aria-labelledby="col-ready">
          <header class="now-head">
            <span class="nw-ico"><Send :size="18" aria-hidden="true" /></span>
            <div>
              <h3 id="col-ready" class="col-title">Pay these now <span class="col-count">{{ readyCol.cards.length }}</span></h3>
              <p class="col-sub">{{ readyCol.sub }}</p>
            </div>
            <strong class="col-total mono">{{ peso(readyCol.total) }}</strong>
          </header>
          <div v-if="!readyCol.cards.length" class="col-empty">
            <p>{{ readyCol.empty }}</p>
            <button type="button" class="nm-btn-soft nm-btn-sm preview-btn" @click="openPreview">
              <Eye :size="14" aria-hidden="true" /> Preview the release pop-up
            </button>
          </div>
          <article v-for="c in readyCol.cards" :key="c.r.rnd_id" class="nw-row">
            <button type="button" class="nw-who" :aria-label="`See ${c.r.rnd_name}'s balance`" @click="openBalance(c.r)">
              <img v-if="c.r.profile_photo" :src="c.r.profile_photo" class="av" alt="" />
              <span v-else class="av">{{ nameInitials(c.r.rnd_name) }}</span>
              <span class="nw-name"><b>{{ c.r.rnd_name }}</b><span class="tag ok"><CheckCircle2 :size="12" aria-hidden="true" />{{ c.next }}</span></span>
            </button>
            <div class="nw-method">
              <span class="m-brand"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2" /><path d="M11 18h2" /></svg>{{ payoutVia(c.r.payout_account.method, c.r.payout_account.bank_name) }}</span>
              <div class="m-txt"><small>Account name</small><b>{{ c.r.payout_account.account_name }}</b></div>
              <div class="m-txt"><small>Number</small><b class="mono">{{ c.r.payout_account.account_number }}</b></div>
            </div>
            <div class="nw-amt"><strong class="mono">{{ peso(c.amount) }}</strong><small>to send</small></div>
            <button type="button" class="nm-btn-dark rel" @click="openRelease(c.r)"><Send :size="15" aria-hidden="true" /> Release {{ peso(c.r.payable) }}</button>
          </article>
        </section>

        <!-- ON HOLD + CLEARED, WAITING -->
        <section class="up" aria-labelledby="col-up">
          <header class="up-head-bar">
            <div>
              <h3 id="col-up" class="col-title">Coming up</h3>
              <p class="col-sub">Money still on hold or waiting for the {{ nextText }} payday.</p>
            </div>
            <div class="up-sums">
              <span class="sum gold"><i></i>{{ waitingCol.title }} <b class="mono">{{ peso(waitingCol.total) }}</b></span>
              <span class="sum gray"><i></i>{{ holdCol.title }} <b class="mono">{{ peso(holdCol.total) }}</b></span>
            </div>
          </header>
          <div v-if="!upCards.length" class="col-empty"><p>{{ waitingCol.empty }} {{ holdCol.empty }}</p></div>
          <template v-else>
            <div class="up-head" aria-hidden="true">
              <span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><path d="M8 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /></svg>RND</span><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 22V4a1 1 0 0 1 1-1h12l-2 4 2 4H5" /></svg>Stage</span><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 11v5M12 8h.01" /></svg>What happens next</span><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="20" height="12" rx="2" /><path d="M9.5 12a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg>Amount</span>
            </div>
            <button
              v-for="c in upCards" :key="`${c.stage}-${c.r.rnd_id}`" type="button" class="up-row" :class="`t-${c.stage}`"
              :aria-label="`See ${c.r.rnd_name}'s balance`" @click="openBalance(c.r)"
            >
              <span class="up-who">
                <img v-if="c.r.profile_photo" :src="c.r.profile_photo" class="av sm" alt="" />
                <span v-else class="av sm">{{ nameInitials(c.r.rnd_name) }}</span>
                <b>{{ c.r.rnd_name }}</b>
              </span>
              <span><span class="pill" :class="c.stage === 'waiting' ? 'gold' : 'muted'">{{ c.stage === 'waiting' ? 'Cleared' : 'On hold' }}</span></span>
              <span class="card-next" :class="c.tone">{{ c.next }}</span>
              <strong class="card-amount mono">{{ peso(c.amount) }}</strong>
              <ChevronRight :size="16" class="up-go" aria-hidden="true" />
            </button>
          </template>
        </section>
      </template>
    </template>

    <!-- HISTORY: grouped by payout month -->
    <div v-else class="nm-panel po-card hist">
      <div v-if="!history.length" class="nm-empty">
        <span class="e-ico"><Wallet :size="28" aria-hidden="true" /></span>
        <p>No payouts released yet.</p>
      </div>
      <section v-for="m in historyMonths" :key="m.key" class="month">
        <h3 class="month-title"><span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg>{{ m.label }}</span><span class="mono">{{ peso(m.total) }}</span></h3>
        <button v-for="p in m.items" :key="p.id" type="button" class="paid-row" :aria-label="`Open payout ${payoutNo(p)} to ${p.rnd_name}`" @click="openSlip(p)">
          <span class="paid-date"><b>{{ shortDate(p.released_at) }}</b><small class="mono">{{ payoutNo(p) }}</small></span>
          <span class="paid-who">
            <span class="paid-name">{{ p.rnd_name }}</span>
            <span class="nm-row-sub">{{ p.invoice_count }} consultation{{ p.invoice_count === 1 ? '' : 's' }}, sent to {{ methodText(p) }}</span>
          </span>
          <span class="paid-ref">
            <span class="mono ref-chip">{{ p.reference }}</span>
            <span class="nm-row-sub">{{ p.released_by_name ? `Recorded by ${p.released_by_name}` : '' }}</span>
          </span>
          <strong class="paid-amount mono">{{ peso(p.amount) }}</strong>
          <ChevronRight :size="16" class="paid-go" aria-hidden="true" />
        </button>
      </section>
      <ListPager v-model:page="page" :pages="pages" />
    </div>

    <!-- AN RND'S BALANCE (read only): every consultation not paid yet, by stage -->
    <div v-if="balance" class="nm-modal-overlay" @click.self="balance = null">
      <div class="nm-modal bal pm" role="dialog" aria-modal="true" aria-labelledby="bal-title">
        <div class="bal-head nm-modal-head pm-head">
          <img class="pm-plate" :src="plateImg" alt="" aria-hidden="true" />
          <span class="pm-fade" aria-hidden="true"></span>
          <img v-if="balance.row.profile_photo" :src="balance.row.profile_photo" class="av lg" alt="" />
          <span v-else class="av lg">{{ nameInitials(balance.row.rnd_name) }}</span>
          <div class="pm-ht">
            <p class="pm-kind">RND balance</p>
            <h3 id="bal-title" class="nm-modal-title">{{ balance.row.rnd_name }}</h3>
            <p class="nm-panel-sub pm-sub">Not paid yet: <b>{{ peso(Number(balance.row.pending) + Number(balance.row.posted)) }}</b></p>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="balance = null"><X :size="18" aria-hidden="true" /></button>
        </div>

        <div class="pm-body">
          <p v-if="!balance.row.payout_account" class="nm-note bal-note">
            <ShieldAlert :size="16" aria-hidden="true" />
            <span><strong>No GCash or bank details yet.</strong> Cleared money waits until {{ balance.row.rnd_name.split(' ')[0] }} adds them in Earnings.</span>
          </p>
          <p v-if="balanceError" class="nm-error">{{ balanceError }}</p>
          <p v-else-if="!balance.items" class="nm-muted">Loading…</p>
          <template v-else>
            <section v-for="g in balanceGroups" :key="g.key" class="bal-group" :class="g.key">
              <h4 class="bal-title">
                <span><i class="dot"></i>{{ g.title }}</span>
                <strong class="mono">{{ peso(g.total) }}</strong>
              </h4>
              <p class="bal-sub">{{ g.sub }}</p>
              <div v-for="i in g.items" :key="i.invoice_id" class="bal-line">
                <span class="bal-what">
                  <span>{{ i.client_name }}<template v-if="i.appointment_date">, {{ shortDate(i.appointment_date) }}</template></span>
                  <span class="nm-row-sub">INV-{{ String(i.invoice_id).padStart(4, '0') }}, fee {{ peso(i.amount) }} less {{ peso(i.commission) }} commission</span>
                </span>
                <span class="bal-right">
                  <strong class="mono">{{ peso(i.share) }}</strong>
                  <span class="bal-when">{{ g.when(i) }}</span>
                </span>
              </div>
            </section>
            <p v-if="!balanceGroups.length" class="nm-muted">Nothing waiting to be paid.</p>
          </template>
        </div>

        <div class="nm-modal-actions pm-foot">
          <NuxtLink :to="`/users/${balance.row.rnd_id}`" class="nm-btn-soft"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><path d="M8 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /></svg>View RND</NuxtLink>
          <button v-if="balance.row.eligible" type="button" class="nm-btn-dark" @click="releaseFromBalance"><Send :size="14" aria-hidden="true" /> Release {{ peso(balance.row.payable) }}</button>
          <button v-else type="button" class="nm-btn-dark" @click="balance = null">Done</button>
        </div>
      </div>
    </div>

    <!-- PAYOUT SLIP: what was paid, where it went, and the consultations it covered -->
    <div v-if="slip" class="nm-modal-overlay" @click.self="slip = null">
      <div class="nm-modal slip pm" role="dialog" aria-modal="true" aria-labelledby="slip-title">
        <div class="slip-head nm-modal-head pm-head">
          <img class="pm-plate" :src="plateImg" alt="" aria-hidden="true" />
          <span class="pm-fade" aria-hidden="true"></span>
          <span class="pm-doc" aria-hidden="true"><Wallet :size="22" /></span>
          <div class="pm-ht">
            <p class="pm-kind">Payout slip</p>
            <h3 id="slip-title" class="nm-modal-title mono">{{ payoutNo(slip) }}</h3>
            <p class="nm-panel-sub pm-sub">Recorded {{ dateTime(slip.released_at) }}{{ slip.released_by_name ? `, by ${slip.released_by_name}` : '' }}</p>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="slip = null"><X :size="18" aria-hidden="true" /></button>
        </div>

        <div class="pm-body">
          <div class="send">
            <div class="send-top">
              <span class="send-ok"><CheckCircle2 :size="22" aria-hidden="true" /></span>
              <div>
                <p class="send-amount mono">{{ peso(slip.amount) }}</p>
                <p class="send-for">to {{ slip.rnd_name }}, for the {{ longDay(slip.payout_date) }} payout</p>
              </div>
            </div>
            <dl class="send-rows">
              <div><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2" /><path d="M11 18h2" /></svg>Sent by</dt><dd>{{ payoutVia(slip.method, slip.bank_name) }}</dd></div>
              <div><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><path d="M8 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /></svg>Account name</dt><dd>{{ slip.account_name }}</dd></div>
              <div><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18" /></svg>Account number</dt><dd class="mono">{{ slip.account_number }}</dd></div>
              <div>
                <dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18" /></svg>Receipt reference</dt>
                <dd>
                  <span class="mono code">{{ slip.reference }}</span>
                  <button type="button" class="nm-btn-soft nm-btn-sm copy" @click="copy(slip.reference)">
                    <component :is="copied ? Check : Copy" :size="13" aria-hidden="true" /> {{ copied ? 'Copied' : 'Copy' }}
                  </button>
                </dd>
              </div>
            </dl>
          </div>
          <p v-if="slip.notes" class="nm-note plain-note slip-note">{{ slip.notes }}</p>

          <h4 class="slip-title"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>Consultations it covered</h4>
          <p v-if="!slip.invoices" class="nm-muted">Loading…</p>
          <p v-else-if="slipError" class="nm-error">{{ slipError }}</p>
          <div v-else class="slip-lines">
            <div v-for="i in slip.invoices" :key="i.invoice_id" class="slip-line">
              <span class="slip-what">
                <span>{{ i.client_name }}</span>
                <span class="nm-row-sub">INV-{{ String(i.invoice_id).padStart(4, '0') }}<template v-if="i.consultation_at">, {{ shortDate(i.consultation_at) }}</template>, fee {{ peso(i.amount) }} less {{ peso(i.commission) }} commission</span>
              </span>
              <strong class="mono">{{ peso(i.share) }}</strong>
            </div>
            <div class="slip-line total"><span>Total paid out</span><strong class="mono">{{ peso(slip.amount) }}</strong></div>
          </div>
        </div>

        <div class="nm-modal-actions pm-foot">
          <NuxtLink :to="`/users/${slip.rnd}`" class="nm-btn-soft"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><path d="M8 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /></svg>View RND</NuxtLink>
          <button type="button" class="nm-btn-soft" :disabled="!slip.invoices" @click="printSlip"><Printer :size="14" aria-hidden="true" /> Print</button>
          <button type="button" class="nm-btn-dark" @click="slip = null">Done</button>
        </div>
      </div>
    </div>

    <!-- RELEASE: send first, then record it -->
    <div v-if="releasing" class="nm-modal-overlay" @click.self="busy ? null : (releasing = null)">
      <div class="nm-modal release pm" role="dialog" aria-modal="true" aria-labelledby="release-title">
        <div class="nm-modal-head pm-head">
          <img class="pm-plate" :src="plateImg" alt="" aria-hidden="true" />
          <span class="pm-fade" aria-hidden="true"></span>
          <span class="pm-doc" aria-hidden="true"><Send :size="22" /></span>
          <div class="pm-ht">
            <p class="pm-kind">Release payout</p>
            <h3 id="release-title" class="nm-modal-title">Pay {{ releasing.rnd_name }}</h3>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="busy ? null : (releasing = null)"><X :size="18" aria-hidden="true" /></button>
        </div>

        <div class="pm-body">
          <p v-if="releasing.preview" class="preview-note">
            <Eye :size="15" aria-hidden="true" />
            <span><strong>Preview with sample data.</strong> This is what the admin sees on payday. Nothing can be sent or recorded from here.</span>
          </p>

          <div class="send">
            <div class="send-top">
              <span class="send-ok gold"><Send :size="20" aria-hidden="true" /></span>
              <div>
                <p class="send-amount mono">{{ peso(releasing.payable) }}</p>
                <p class="send-for">for {{ releasing.payable_count }} consultation{{ releasing.payable_count === 1 ? '' : 's' }} cleared by {{ runText }}</p>
              </div>
            </div>
            <dl class="send-rows">
              <div><dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2" width="12" height="20" rx="2" /><path d="M11 18h2" /></svg>Send by</dt><dd>{{ payoutVia(releasing.payout_account.method, releasing.payout_account.bank_name) }}</dd></div>
              <div>
                <dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><path d="M8 7a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /></svg>Account name</dt>
                <dd>{{ releasing.payout_account.account_name }}</dd>
              </div>
              <div>
                <dt><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9h16M4 15h16M10 3L8 21M16 3l-2 18" /></svg>Account number</dt>
                <dd>
                  <span class="mono code">{{ releasing.payout_account.account_number }}</span>
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
            <li><span class="st-n">1</span><span>Send {{ peso(releasing.payable) }} from the NutriMatch {{ payoutVia(releasing.payout_account.method, releasing.payout_account.bank_name) }} account.</span></li>
            <li><span class="st-n">2</span><span>Copy the reference number from the receipt into the box below. {{ releasing.rnd_name.split(' ')[0] }} gets an email and a notification.</span></li>
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
        </div>
        <div class="nm-modal-actions pm-foot">
          <button type="button" class="nm-btn-soft" :disabled="busy" @click="releasing = null">Not yet</button>
          <button type="button" class="nm-btn-dark" :disabled="busy || !canRecord || releasing.preview" @click="release">
            {{ busy ? 'Recording…' : lockLeft > 0 ? `Record as paid out (${lockLeft})` : 'Record as paid out' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import { payoutVia } from '~/utils/payout'
import { CalendarClock, Check, CheckCircle2, ChevronRight, Copy, Eye, Printer, Send, ShieldAlert, Wallet, X } from 'lucide-vue-next'

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
const toast = useToast() // the app's toast (2026-11-03)
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
const heldTotal = computed(() => rows.value.reduce((s, r) => s + Number(r.posted) - (r.eligible ? Number(r.payable) : 0), 0))
const pendingTotal = computed(() => rows.value.reduce((s, r) => s + Number(r.pending), 0))
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`
// one card per RND per stage, each with one line saying what happens next
const columns = computed(() => {
  const hold = rows.value.filter(r => Number(r.pending) > 0).map(r => ({
    r,
    amount: Number(r.pending),
    next: r.next_posts_on
      ? `${plural(r.pending_count, 'consultation')}, the first clears ${shortDate(r.next_posts_on)}`
      : `${plural(r.pending_count, 'consultation')}, not completed yet`,
    tone: '',
  }))
  const waiting = rows.value
    .map(r => ({ r, amount: Number(r.posted) - (r.eligible ? Number(r.payable) : 0) }))
    .filter(c => c.amount > 0)
    .map((c) => {
      const r = c.r
      if (!r.payout_account) return { ...c, next: 'Waits for the RND to add GCash or bank details', tone: 'gold' }
      if (r.eligible || Number(r.payable) === 0) return { ...c, next: `Paid on ${nextText.value}`, tone: '' }
      return { ...c, next: `Under ${peso(run.value?.minimum_payout ?? 500)}, adds to the ${nextText.value} payout`, tone: '' }
    })
  const ready = dueRows.value.map(r => ({
    r, amount: Number(r.payable), next: `${plural(r.payable_count, 'consultation')}, cleared by ${runText.value}`, tone: '',
  }))
  const total = list => list.reduce((s, c) => s + c.amount, 0)
  return [
    { key: 'hold', title: 'On hold', sub: 'Just finished. Wait 3 days in case of a refund.', empty: 'Nothing on hold.', cards: hold, total: total(hold) },
    { key: 'waiting', title: 'Cleared, waiting', sub: 'The RND\'s now. It waits for payday.', empty: 'Nothing waiting.', cards: waiting, total: total(waiting) },
    {
      key: 'ready', title: 'Ready to send', sub: `Cleared by ${runText.value}. Pay these now.`, cards: ready, total: total(ready),
      empty: run.value?.payout_day_reached && daysLeft.value !== 0 ? `Everyone from the ${runText.value} run is paid. Next payday is ${nextText.value}.` : `Nobody to pay until ${nextText.value}.`,
    },
  ]
})

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

// For demos when nobody is ready to pay: the real pop-up with a made-up RND,
// marked as a preview; its record button stays disabled.
function openPreview() {
  openRelease({
    preview: true, rnd_id: 0, rnd_name: 'Sample RND', payable: '720.00', payable_count: 1,
    payout_account: { method: 'gcash', account_name: 'Sample RND', account_number: '09171234567', bank_name: null, recently_changed: false },
  })
}
// Lists show the payout number masked (•••• 4567, billing.payouts.mask_account); the full
// number is fetched only here, where the admin types it to send the money (audit-logged).
async function openRelease(r) {
  releasing.value = { ...r, payout_account: { ...r.payout_account } }
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
  if (r.preview) return
  try {
    const full = await get(`/admin/payouts/account/${r.rnd_id}/`)
    if (releasing.value?.rnd_id === r.rnd_id) releasing.value.payout_account.account_number = full.account_number
  } catch (e) {
    releaseError.value = apiError(e)
  }
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
  if (releasing.value?.preview) return // sample data: never sent or recorded
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
    toast.success(`${peso(p.amount)} recorded as paid out to ${p.rnd_name}.`)
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
/* an RND's balance (read only, from the board) */
const balance = ref(null)
const balanceError = ref('')
async function openBalance(row) {
  balance.value = { row, items: null }
  balanceError.value = ''
  try {
    const d = await get(`/admin/payouts/rnd/${row.rnd_id}/`)
    if (balance.value?.row.rnd_id === row.rnd_id) balance.value = { row, items: d.items }
  } catch (e) {
    balanceError.value = apiError(e, 'Could not load this balance. Try again.')
  }
}
function releaseFromBalance() {
  const row = balance.value.row
  balance.value = null
  openRelease(row)
}
const balanceGroups = computed(() => {
  const items = balance.value?.items || []
  const sum = list => list.reduce((t, i) => t + Number(i.share), 0)
  const ready = items.filter(i => i.state === 'posted' && i.payable)
  const waiting = items.filter(i => i.state === 'posted' && !i.payable)
  const hold = items.filter(i => i.state === 'pending')
  return [
    { key: 'ready', title: 'Ready to send', sub: `Cleared by ${runText.value}, so it belongs to the payout that can be paid now.`, items: ready, total: sum(ready),
      when: i => `Cleared ${shortDate(i.cleared_on)}` },
    { key: 'waiting', title: 'Cleared, waiting', sub: `Cleared after ${runText.value}, so it waits for payday on ${nextText.value}. Payouts are never sent early.`, items: waiting, total: sum(waiting),
      when: i => `Cleared ${shortDate(i.cleared_on)}, paid ${nextText.value}` },
    { key: 'hold', title: 'On hold', sub: 'Within 3 days of the consultation, or not marked complete yet, in case the client needs a refund.', items: hold, total: sum(hold),
      when: i => (i.posts_on ? `Clears ${shortDate(i.posts_on)}` : 'Not completed yet') },
  ].filter(g => g.items.length)
})

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
    toast.problem('Allow pop-ups for this site to print the slip.')
  }
}

function methodText(p) {
  return `${payoutVia(p.method, p.bank_name)} ${p.account_number}`
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const holdCol = computed(() => columns.value.find(c => c.key === 'hold'))
const waitingCol = computed(() => columns.value.find(c => c.key === 'waiting'))
const readyCol = computed(() => columns.value.find(c => c.key === 'ready'))
// on hold and cleared-waiting cards in one list, cleared first
const upCards = computed(() => [
  ...waitingCol.value.cards.map(c => ({ ...c, stage: 'waiting' })),
  ...holdCol.value.cards.map(c => ({ ...c, stage: 'hold' })),
])
</script>

<style scoped>
.po { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.mono { font-variant-numeric: tabular-nums; }
.ic { flex-shrink: 0; display: inline-block; }

/* ---------- hero ---------- */
.ph { position: relative; overflow: hidden; display: flex; align-items: center; gap: 24px; margin-bottom: 22px; padding: 26px 30px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.ph > *:not(.ph-plate):not(.ph-fade) { position: relative; z-index: 1; }
.ph-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.ph-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 52%, rgba(0, 77, 58, 0.85) 72%, rgba(0, 77, 58, 0.6) 100%); }
.ph-txt { flex: 1; min-width: 0; max-width: 660px; }
.ph-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.ph-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.run-day-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; color: #fff; }
.run-day-sub { margin: 0; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }
.cycle { flex-shrink: 0; width: 300px; margin-left: auto; padding: 16px 18px; border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 18px; background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(8px); }
.cy-top { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.cy-ico { width: 40px; height: 40px; border-radius: 12px; background: #efbf04; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
.cycle-left { margin: 0; font-size: 13px; font-weight: 700; color: rgba(255, 255, 255, 0.85); }
.cycle-left strong { margin-right: 6px; font-family: 'Playfair Display', serif; font-size: 32px; line-height: 1; color: #efbf04; font-variant-numeric: tabular-nums; }
.cycle-bar { position: relative; height: 8px; border-radius: 999px; background: rgba(255, 255, 255, 0.18); }
.cycle-fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 999px; background: linear-gradient(90deg, #9fcfb3, #efbf04); }
.cycle-now { position: absolute; top: 50%; width: 16px; height: 16px; border-radius: 50%; background: #efbf04; border: 3px solid #004d3a; transform: translate(-50%, -50%); box-shadow: 0 0 0 3px rgba(239, 191, 4, 0.3); box-sizing: border-box; }
.cycle-ends { display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px; font-weight: 700; color: rgba(255, 255, 255, 0.75); }

/* ---------- pipeline ---------- */
.pipe { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 0 0 24px; padding: 0; list-style: none; border: 1.5px solid #c9d8cf; border-radius: 22px; background: #fff; overflow: hidden; box-shadow: 0 10px 24px -18px rgba(0, 77, 58, 0.35); }
.pp { position: relative; display: flex; gap: 14px; min-width: 0; padding: 20px 22px; }
.pp + .pp { border-left: 1px solid #eef2ef; }
.pp:not(:last-child)::after { content: ''; position: absolute; right: -12px; top: 50%; z-index: 2; width: 22px; height: 22px; border-radius: 50%; background: #fff url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%231F7A4D' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 6l6 6-6 6'/%3E%3C/svg%3E") center no-repeat; box-shadow: 0 0 0 1px #dce8e0; transform: translateY(-50%); }
.pp > div { min-width: 0; }
.pp-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; }
.fig-label { display: flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 700; color: #4a5a52; }
.fig-label b { width: 20px; height: 20px; border-radius: 50%; font-size: 11px; display: inline-flex; align-items: center; justify-content: center; }
.pp strong { display: block; margin: 3px 0 2px; font-family: 'Playfair Display', serif; font-size: 28px; line-height: 1.15; font-variant-numeric: tabular-nums; }
.fig-note { display: block; font-size: 12.5px; color: #6b7d73; }
.fig-note.warn { font-weight: 800; color: #8a6500; }
.pp-how { display: block; margin-top: 8px; padding-top: 8px; border-top: 1px dashed #dce8e0; font-size: 12px; line-height: 1.45; color: #8a9a91; }
.p1 .pp-ico { background: #f1f6f2; color: #6b7d73; }
.p1 .fig-label b { background: #e9eef0; color: #4a5a52; }
.p1 strong { color: #4a5a52; }
.p2 { background: linear-gradient(180deg, #fffbea, #fff); }
.p2 .pp-ico { background: #efbf04; color: #004d3a; }
.p2 .fig-label b { background: #efbf04; color: #004d3a; }
.p2 strong { color: #0e3a2c; }
.p2 strong.warn { color: #8a6500; }
.p3 .pp-ico { background: #004d3a; color: #efbf04; }
.p3 .fig-label b { background: #004d3a; color: #efbf04; }
.p3 strong { color: #004d3a; }

/* ---------- tabs ---------- */
.po-bar { margin: 0 0 16px; }
.po-tabs { display: inline-flex; gap: 4px; max-width: 100%; margin: 0; padding: 5px; border: none; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); overflow-x: auto; scrollbar-width: none; }
.po-tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 36px; margin: 0; padding: 0 15px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.po-tabs .nm-tab .ic { color: #8a9a91; }
.po-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; }
.po-tabs .nm-count { min-width: 20px; height: 20px; margin-left: 2px; padding: 0 6px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 700; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.po-tabs .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.po-tabs .nm-tab.active .ic { color: #efbf04; }
.po-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }

.po-card, .po-loading { border: none; border-radius: 22px; box-shadow: var(--sh); }
.po :deep(.nm-empty) { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 26px 10px; text-align: center; }
.po :deep(.nm-empty p) { margin: 0; font-size: 14px; font-weight: 600; color: #4a5a52; }
.e-ico { width: 56px; height: 56px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }

/* avatars */
.av { flex-shrink: 0; width: 46px; height: 46px; border-radius: 50%; object-fit: cover; background: #e3efe7; color: #004d3a; font-size: 13px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; border: 2px solid #fff; box-shadow: 0 0 0 2px #efbf04; box-sizing: border-box; }
.av.sm { width: 40px; height: 40px; font-size: 12.5px; }
.av.lg { width: 56px; height: 56px; font-size: 16px; }

/* ---------- pay these now ---------- */
.now { margin-bottom: 18px; border: 2px solid #004d3a; border-radius: 22px; background: #fff; overflow: hidden; box-shadow: var(--sh); }
.now-head, .up-head-bar { display: flex; align-items: center; gap: 14px; padding: 18px 24px; }
.now-head { background: #004d3a; color: #fff; }
.nw-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 13px; background: #efbf04; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.now-head > div, .up-head-bar > div:first-child { flex: 1; min-width: 0; }
.col-title { display: flex; align-items: center; gap: 8px; margin: 0 0 3px; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; }
.now-head .col-title { color: #fff; }
.up .col-title { color: #0e3a2c; }
.col-count { min-width: 22px; height: 22px; padding: 0 7px; border-radius: 999px; background: #efbf04; color: #004d3a; font-family: 'DM Sans', sans-serif; font-size: 12px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.col-sub { margin: 0; font-size: 13px; color: #6b7d73; }
.now-head .col-sub { color: rgba(255, 255, 255, 0.8); }
.col-total { font-family: 'Playfair Display', serif; font-size: 24px; color: #efbf04; white-space: nowrap; }
.col-empty { padding: 22px 24px; font-size: 14px; color: #6b7d73; }
.col-empty p { margin: 0; }
.preview-btn { margin-top: 12px; }
.nw-row { display: grid; grid-template-columns: minmax(220px, 1fr) auto auto auto; align-items: center; gap: 20px; padding: 20px 24px; background: linear-gradient(90deg, #fff 0%, #f7faf8 100%); }
.nw-row + .nw-row { border-top: 1px solid #eef2ef; }
.nw-who { display: flex; align-items: center; gap: 14px; min-width: 0; padding: 0; border: 0; background: none; font-family: inherit; text-align: left; color: inherit; cursor: pointer; }
.nw-who .av { width: 50px; height: 50px; }
.nw-who:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 4px; border-radius: 12px; }
.nw-name { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; min-width: 0; }
.nw-name b { font-size: 15.5px; color: #0e3a2c; }
.nw-who:hover .nw-name b { text-decoration: underline; text-underline-offset: 3px; }
.tag { display: inline-flex; align-items: center; gap: 5px; padding: 3px 9px; border-radius: 999px; background: #f1f6f2; font-size: 12px; font-weight: 600; color: #4a5a52; }
.tag.ok { background: #e3f4ea; color: #1f7a4d; }
.nw-method { display: flex; align-items: center; gap: 16px; padding: 8px; border: 1.5px solid #dce8e0; border-radius: 16px; background: #fff; }
.m-brand { display: inline-flex; align-items: center; gap: 6px; height: 40px; padding: 0 12px; border-radius: 11px; background: #e8f0fe; color: #1a56c9; font-size: 13px; font-weight: 800; white-space: nowrap; }
.m-txt { min-width: 0; }
.m-txt small { display: block; font-size: 11px; font-weight: 700; color: #8a9a91; }
.m-txt b { font-size: 13.5px; color: #0e3a2c; white-space: nowrap; }
.nw-amt { text-align: right; }
.nw-amt strong { display: block; font-family: 'Playfair Display', serif; font-size: 26px; line-height: 1.1; color: #004d3a; }
.nw-amt small { font-size: 12px; font-weight: 700; color: #8a9a91; }

/* ---------- coming up ---------- */
.up { border-radius: 22px; background: #fff; overflow: hidden; box-shadow: var(--sh); }
.up-sums { display: flex; gap: 8px; flex-wrap: wrap; }
.sum { display: inline-flex; align-items: center; gap: 7px; padding: 6px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 700; }
.sum i { width: 8px; height: 8px; border-radius: 50%; }
.sum.gold { background: #fff4d6; color: #8a6500; }
.sum.gold i { background: #efbf04; }
.sum.gray { background: #f3f6f4; color: #4a5a52; }
.sum.gray i { background: #a9b6ae; }
.up-head, .up-row { display: grid; grid-template-columns: minmax(200px, 1.3fr) 130px minmax(220px, 1.8fr) 130px 20px; align-items: center; column-gap: 16px; padding: 0 24px; }
.up-head { padding-top: 13px; padding-bottom: 13px; background: #004d3a; font-size: 12.5px; font-weight: 700; color: #fff; }
.up-head span { display: inline-flex; align-items: center; gap: 7px; }
.up-head .ic { color: #efbf04; }
.up-row { position: relative; width: 100%; padding-top: 14px; padding-bottom: 14px; border: 0; border-bottom: 1px solid #eef2ef; background: #fff; font-family: inherit; text-align: left; color: inherit; cursor: pointer; }
.up-row:last-child { border-bottom: none; }
.up-row:hover { background: #f7faf8; }
.up-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.up-row::before { content: ''; position: absolute; left: 0; top: 12px; bottom: 12px; width: 4px; border-radius: 0 4px 4px 0; background: #c9d3cd; }
.up-row.t-waiting::before { background: #efbf04; }
.up-who { display: flex; align-items: center; gap: 12px; min-width: 0; }
.up-who b { font-size: 14.5px; color: #0e3a2c; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.pill::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.pill.gold { background: #fff4d6; color: #8a6500; }
.pill.muted { background: #f3f6f4; color: #6b7d73; }
.card-next { font-size: 13px; color: #6b7d73; }
.card-next.gold { font-weight: 700; color: #8a6500; }
.card-amount { font-size: 15px; font-weight: 800; color: #0e3a2c; }
.t-waiting .card-amount { color: #8a6500; }
.t-hold .card-amount { color: #4a5a52; }
.up-go { color: #a9b6ae; }

/* buttons */
.po .nm-btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 42px; padding: 0 18px; border: none; border-radius: 12px; background: #004d3a; color: #fff; font-family: inherit; font-size: 13.5px; font-weight: 800; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); cursor: pointer; text-decoration: none; }
.po .nm-btn-dark svg { color: #efbf04; }
.po .nm-btn-dark:disabled { opacity: 0.45; box-shadow: none; cursor: not-allowed; }
.po .nm-btn-soft { display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 42px; padding: 0 18px; border: 1px solid #dce8e0; border-radius: 12px; background: #fff; color: #004d3a; font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; text-decoration: none; }
.po .nm-btn-soft.nm-btn-sm { height: 34px; padding: 0 12px; font-size: 12.5px; }
.po .nm-btn-soft svg { color: #1f7a4d; }
.po .nm-btn-soft:disabled { opacity: 0.5; cursor: not-allowed; }
.nw-row .rel { height: 50px; padding: 0 22px; border-radius: 14px; font-size: 14.5px; }

/* ---------- history ---------- */
.hist { padding: 22px 24px; }
.month + .month { margin-top: 22px; }
.month-title { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin: 0 0 6px; padding: 10px 14px; border-radius: 12px; background: #004d3a; font-family: inherit; font-size: 14px; font-weight: 800; color: #fff; }
.month-title > span:first-child { display: inline-flex; align-items: center; gap: 8px; }
.month-title .ic { color: #efbf04; }
.month-title .mono { font-family: 'Playfair Display', serif; font-size: 17px; color: #efbf04; }
.paid-row { display: grid; grid-template-columns: 110px minmax(0, 1.6fr) minmax(0, 1fr) auto 16px; gap: 14px; align-items: center; width: 100%; margin: 0; padding: 14px 12px; border: 0; border-bottom: 1px solid #eef2ef; border-radius: 0; background: none; text-align: left; font-family: inherit; color: inherit; cursor: pointer; }
.paid-row:last-child { border-bottom: none; }
.paid-row:hover { background: #f7faf8; }
.paid-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.paid-date { display: flex; flex-direction: column; gap: 2px; }
.paid-date b { font-size: 13.5px; color: #0e3a2c; }
.paid-date small { font-size: 11.5px; font-weight: 800; color: #1f7a4d; }
.paid-who, .paid-ref { display: flex; flex-direction: column; align-items: flex-start; gap: 3px; min-width: 0; font-size: 13.5px; }
.paid-name { font-size: 14.5px; font-weight: 800; color: #0e3a2c; }
.ref-chip { max-width: 100%; padding: 3px 8px; border-radius: 8px; background: #f1f6f2; font-family: ui-monospace, Menlo, monospace; font-size: 12.5px; color: #004d3a; overflow-wrap: anywhere; }
.paid-amount { font-size: 15px; color: #004d3a; text-align: right; }
.paid-go { color: #a9b6ae; }

/* ---------- pop-ups ---------- */
.nm-modal-overlay .nm-modal.pm { display: flex; flex-direction: column; width: min(760px, calc(100vw - 32px)) !important; max-width: 760px !important; min-width: 0 !important; height: auto !important; max-height: calc(100vh - 48px) !important; margin: auto !important; padding: 0 !important; border-radius: 24px; overflow: hidden !important; }
.nm-modal-overlay .nm-modal.release { width: min(680px, calc(100vw - 32px)) !important; max-width: 680px !important; }
.nm-modal.pm .pm-head { position: relative !important; top: auto !important; overflow: hidden; flex-shrink: 0; display: flex; align-items: center; gap: 16px; margin: 0 !important; padding: 24px 28px !important; min-height: 0 !important; border: none !important; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 55%, #004635 100%); }
.pm-head > *:not(.pm-plate):not(.pm-fade) { position: relative; z-index: 1; }
.pm-plate { position: absolute; right: -60px; top: 50%; width: 220px; height: 220px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.pm-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 55%, rgba(0, 77, 58, 0.88) 75%, rgba(0, 77, 58, 0.7) 100%); }
.pm-doc { flex-shrink: 0; width: 54px; height: 58px; border-radius: 14px; background: #fff; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 24px -10px rgba(0, 0, 0, 0.4); }
.pm-ht { flex: 1; min-width: 0; }
.pm-kind { margin: 0 0 2px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.nm-modal.pm .pm-ht .nm-modal-title { margin: 0 !important; padding: 0 !important; font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; line-height: 1.2; color: #fff !important; }
.pm-sub { margin: 4px 0 0 !important; font-size: 13px; color: rgba(255, 255, 255, 0.82) !important; }
.pm-sub b { color: #efbf04; }
.nm-modal.pm .pm-head .nm-modal-x { position: static !important; inset: auto !important; float: none !important; flex-shrink: 0; width: 38px !important; height: 38px !important; margin: 0 !important; padding: 0 !important; border: 1px solid rgba(255, 255, 255, 0.25) !important; border-radius: 12px !important; background: rgba(0, 0, 0, 0.22) !important; color: #fff !important; opacity: 1 !important; display: inline-flex !important; align-items: center; justify-content: center; cursor: pointer; }
.pm-body { flex: 1 1 auto; min-height: 0 !important; overflow-y: auto !important; overscroll-behavior: contain; padding: 24px 28px 28px; }
.nm-modal.pm .pm-foot { flex-shrink: 0; display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 10px; margin: 0; padding: 14px 28px; border-top: 1px solid #eef2ef; background: #f7faf8; }

/* balance */
.bal-note { display: flex; gap: 10px; margin: 0 0 16px; padding: 12px 14px; border-radius: 14px; background: #fff4d6; color: #8a6500; font-size: 13.5px; line-height: 1.5; }
.bal-note svg { flex-shrink: 0; margin-top: 2px; }
.bal-group { margin-top: 16px; border: 1.5px solid #c9d8cf; border-radius: 18px; overflow: hidden; }
.bal-group:first-of-type { margin-top: 0; }
.bal-title { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin: 0; padding: 14px 18px 4px; font-family: inherit; font-size: 15px; font-weight: 800; color: #0e3a2c; }
.bal-title > span { display: inline-flex; align-items: center; gap: 8px; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: #a9b6ae; }
.bal-group.ready { border-color: #004d3a; }
.bal-group.ready .dot { background: #004d3a; }
.bal-group.ready .bal-title strong { color: #004d3a; }
.bal-group.waiting { border-color: #efbf04; }
.bal-group.waiting .dot { background: #efbf04; }
.bal-group.waiting .bal-title strong { color: #8a6500; }
.bal-title strong { font-family: 'Playfair Display', serif; font-size: 19px; }
.bal-sub { margin: 0; padding: 0 18px 12px; font-size: 12.5px; color: #6b7d73; }
.bal-line { display: flex; justify-content: space-between; gap: 12px; padding: 12px 18px; border-top: 1px solid #eef2ef; font-size: 14px; }
.bal-what { display: flex; flex-direction: column; gap: 2px; min-width: 0; color: #0e3a2c; font-weight: 600; }
.bal-what .nm-row-sub { font-weight: 400; font-size: 12.5px; color: #8a9a91; }
.bal-right { display: flex; flex-direction: column; align-items: flex-end; flex-shrink: 0; }
.bal-right strong { color: #0e3a2c; }
.bal-when { font-size: 12px; color: #6b7d73; }

/* send box (slip + release) */
.send { border: 1.5px solid #c9d8cf; border-radius: 18px; background: #fff; overflow: hidden; }
.send-top { display: flex; align-items: center; gap: 14px; padding: 16px 18px; background: #f1f8f4; border-bottom: 1px dashed #c9d8cf; }
.send-ok { flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%; background: #1f9d55; color: #fff; display: inline-flex; align-items: center; justify-content: center; }
.send-ok.gold { background: #efbf04; color: #004d3a; }
.send-amount { margin: 0; font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 700; line-height: 1.1; color: #004d3a; }
.send-for { margin: 2px 0 0; font-size: 12.5px; color: #6b7d73; }
.send-rows { margin: 0; }
.send-rows > div { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 18px; border-top: 1px solid #eef2ef; font-size: 14px; }
.send-rows > div:first-child { border-top: none; }
.send-rows dt { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 700; color: #6b7d73; }
.send-rows dt .ic { color: #1f7a4d; }
.send-rows dd { display: flex; align-items: center; gap: 8px; margin: 0; font-weight: 700; color: #0e3a2c; text-align: right; overflow-wrap: anywhere; }
.code { padding: 3px 8px; border-radius: 8px; background: #f1f6f2; font-family: ui-monospace, Menlo, monospace; font-size: 13px; color: #004d3a; }
.copy { flex-shrink: 0; }
.slip-note { margin: 14px 0 0; padding: 12px 14px; border-radius: 14px; background: #eef1fa; color: #2e4a86; font-size: 13.5px; }
.slip-title { display: flex; align-items: center; gap: 8px; margin: 22px 0 12px; font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: #0e3a2c; }
.slip-title .ic { color: #1f7a4d; }
.slip-lines { border: 1.5px solid #c9d8cf; border-radius: 18px; overflow: hidden; }
.slip-line { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 18px; font-size: 14px; }
.slip-line + .slip-line { border-top: 1px solid #eef2ef; }
.slip-what { display: flex; flex-direction: column; gap: 2px; min-width: 0; font-weight: 600; color: #0e3a2c; }
.slip-what .nm-row-sub { font-weight: 400; font-size: 12.5px; color: #8a9a91; }
.slip-line.total { border-top: none; background: #004d3a; color: #fff; font-weight: 800; }
.slip-line.total strong { font-family: 'Playfair Display', serif; font-size: 20px; color: #efbf04; }

/* release */
.preview-note { display: flex; gap: 8px; align-items: flex-start; margin: 0 0 16px; padding: 12px 14px; border: 1px dashed #9aaa9a; border-radius: 14px; background: #f4f6f4; font-size: 13px; color: #4a5a52; line-height: 1.45; }
.preview-note svg { flex-shrink: 0; margin-top: 2px; }
.changed { display: flex; gap: 10px; align-items: flex-start; margin: 16px 0 0; padding: 14px 16px; border: 1px solid #f2c4c4; border-radius: 14px; background: #fdecec; color: #7a1f1f; font-size: 13.5px; line-height: 1.5; }
.changed svg { flex-shrink: 0; margin-top: 2px; color: #a12525; }
.changed p { margin: 0; }
.steps { display: grid; gap: 8px; margin: 18px 0 16px; padding: 0; list-style: none; }
.steps li { display: flex; gap: 12px; align-items: flex-start; padding: 12px 14px; border-radius: 14px; background: #f7faf8; font-size: 13.5px; line-height: 1.5; color: #22362c; }
.st-n { flex-shrink: 0; width: 24px; height: 24px; border-radius: 50%; background: #004d3a; color: #efbf04; font-size: 12px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }
.release .nm-label { display: block; margin-bottom: 6px; font-size: 13px; font-weight: 700; color: #22362c; }
.release .nm-input { width: 100%; box-sizing: border-box; border: 1.5px solid #c9d8cf; border-radius: 12px; }
.release .nm-input:focus { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); outline: none; }
.release .nm-hint { margin: 6px 0 0; font-size: 12.5px; color: #6b7d73; }
.confirm { display: flex; gap: 10px; align-items: flex-start; margin-top: 12px; padding: 12px 14px; border: 1.5px solid #dce8e0; border-radius: 14px; font-size: 13.5px; color: #0e3a2c; line-height: 1.45; cursor: pointer; }
.confirm:has(input:checked) { border-color: #1f9d55; background: #f1f8f4; }
.confirm input { margin-top: 3px; accent-color: #004d3a; flex-shrink: 0; }

@media (max-width: 1100px) {
  .nw-row { grid-template-columns: minmax(0, 1fr) auto; }
  .nw-method { grid-column: 1 / -1; grid-row: 2; }
  .nw-row .rel { grid-column: 1 / -1; }
}
@media (max-width: 900px) {
  .pipe { grid-template-columns: minmax(0, 1fr); }
  .pp + .pp { border-left: none; border-top: 1px solid #eef2ef; }
  .pp:not(:last-child)::after { right: auto; left: 50%; top: auto; bottom: -12px; transform: translateX(-50%) rotate(90deg); }
  .up-head { display: none; }
  .up-row { grid-template-columns: minmax(0, 1fr) auto; row-gap: 8px; padding: 14px 16px 14px 20px; }
  .up-row > span:nth-child(2) { grid-column: 1; grid-row: 2; }
  .up-row .card-next { grid-column: 1 / -1; }
  .up-row .card-amount { grid-column: 2; grid-row: 1; }
  .up-go { display: none; }
  .up-head-bar { flex-wrap: wrap; }
  .paid-row { grid-template-columns: minmax(0, 1fr) auto; row-gap: 6px; }
  .paid-go { display: none; }
  .paid-date { grid-column: 1 / -1; flex-direction: row; gap: 8px; }
  .paid-ref { grid-column: 1; }
  .paid-amount { grid-row: 2; grid-column: 2; }
}
@media (max-width: 760px) {
  .po { padding-bottom: 110px; }
  .ph { flex-direction: column; align-items: stretch; padding: 20px 18px; border-radius: 22px; }
  .run-day-title { font-size: 24px; }
  .ph-plate { width: 180px; height: 180px; right: -60px; top: 20px; transform: none; }
  .ph-txt { max-width: 80%; }
  .cycle { width: auto; margin: 0; }
  .po-tabs { display: flex; width: 100%; border-radius: 16px; }
  .now-head, .up-head-bar { padding: 16px; }
  .nw-row { padding: 16px; gap: 14px; }
  .nw-method { flex-wrap: wrap; }
  .hist { padding: 16px; }
  .nm-modal-overlay .nm-modal.pm { width: calc(100vw - 24px) !important; max-height: calc(100dvh - 24px) !important; border-radius: 22px; }
  .nm-modal.pm .pm-head { padding: 18px !important; }
  .nm-modal.pm .pm-ht .nm-modal-title { font-size: 22px; }
  .pm-doc { width: 46px; height: 50px; }
  .pm-body { padding: 18px; }
  .nm-modal.pm .pm-foot { padding: 12px 18px; }
  .nm-modal.pm .pm-foot > * { flex: 1; }
  .send-rows > div { flex-direction: column; align-items: flex-start; gap: 4px; }
  .send-rows dd { text-align: left; }
}
</style>