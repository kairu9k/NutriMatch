<template>
  <div class="nm-page">
    <!-- HERO -->
    <section class="ap-hero">
      <img class="ap-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="ap-hero-fade" aria-hidden="true"></span>
      <div class="ap-hero-txt">
        <p class="ap-eyebrow"><span aria-hidden="true"></span>Appointments</p>
        <h2 class="ap-title">Your consultations</h2>
        <p class="nm-page-sub">Your consultations, sorted by what needs you. All times are Philippine time.</p>
        <NuxtLink to="/profile-settings?tab=availability" class="ap-avail"><CalendarClock :size="16" /> Availability</NuxtLink>
      </div>
    </section>

    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <div v-if="loading" class="nm-panel ap-loading"><span class="ap-spin" aria-hidden="true"></span><p class="nm-muted">Loading appointments…</p></div>

    <template v-else-if="board">
      <div v-if="patientFilter" class="nm-note plain-note filter-note">
        Showing only <strong>{{ patientFilterName }}</strong>.
        <NuxtLink to="/appointments" class="nm-panel-link">Show everyone</NuxtLink>
      </div>

      <div class="nm-toolbar">
        <div class="nm-tabs ap-tabs" role="tablist" aria-label="Appointment lists">
          <button v-for="t in TABS" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" role="tab"
                  :aria-selected="tab === t.key" @click="setTab(t.key)">
            <component :is="TAB_ICONS[t.key]" :size="15" class="tab-ic" aria-hidden="true" />
            {{ t.label }}<span v-if="t.key !== 'history'" class="nm-count">{{ list(t.key).length + (t.key === 'upcoming' ? list('rescheduling').length : 0) }}</span>
          </button>
        </div>
        <label v-if="tab === 'history'" class="nm-search ap-search">
          <Search :size="16" />
          <input v-model="search" type="search" placeholder="Search by patient" aria-label="Search history" />
        </label>
      </div>

      <div class="nm-panel appt-list">
        <!-- ============ REQUESTS ============ -->
        <template v-if="tab === 'requests'">
          <p class="tab-intro">Check each request and their screening before you confirm. Confirming sends them an invoice to pay before the consultation.</p>
          <div v-if="!list('requests').length" class="nm-empty"><Inbox :size="26" /><p>No booking requests right now.</p></div>
          <article v-for="a in list('requests')" :key="a.id" class="row tone-gold">
            <DateBlock :at="a.scheduled_at" tone="gold" />
            <div class="row-main">
              <p class="who">
                <NuxtLink :to="`/client-detail/${a.relationship_id}`" class="name-link">{{ a.client.name }}</NuxtLink>
                <span class="nm-pill" :class="a.returning ? 'green' : 'muted'">{{ a.returning ? 'Returning patient' : 'New patient' }}</span>
              </p>
              <p class="nm-row-sub">{{ timeRange(a) }}, {{ a.type_label.toLowerCase() }}, {{ a.duration_minutes }} min</p>
              <p v-if="confirmClosed(a)" class="flag critical"><OctagonAlert :size="13" /> Too late to confirm: requests must be confirmed 30 minutes before the start. Decline it so they can book again.</p>
              <p v-else-if="a.starts_in_hours < 24" class="flag warning"><AlertTriangle :size="13" /> Confirm by {{ clock(a.confirm_by) }}{{ sameDay(a) ? '' : `, ${longDay(a.confirm_by)}` }}, 30 minutes before the start.</p>
              <div class="chips">
                <template v-if="a.screening.submitted">
                  <span v-if="a.screening.nrs_score != null" class="chip" :class="{ risk: a.screening.nrs_score >= 3 }">NRS-2002 {{ a.screening.nrs_score }}{{ a.screening.nrs_risk ? `, ${a.screening.nrs_risk.toLowerCase()}` : '' }}</span>
                  <span v-if="a.screening.bmi_category" class="chip">BMI {{ a.screening.bmi?.toFixed(1) }}, {{ a.screening.bmi_category }}</span>
                  <span v-for="c in a.screening.conditions" :key="c" class="chip">{{ c }}</span>
                  <span v-if="a.screening.allergies.length" class="chip allergy">Allergy: {{ a.screening.allergies.join(', ') }}</span>
                </template>
                <span v-else class="chip risk">No screening yet, so it can't be confirmed</span>
              </div>
              <p v-if="a.notes" class="client-note">{{ a.notes }}</p>
            </div>
            <div class="row-actions">
              <button v-if="!confirmClosed(a)" type="button" class="nm-btn-dark nm-btn-sm" @click="openReview(a)">Review &amp; confirm</button>
              <button type="button" class="nm-btn-danger solid nm-btn-sm row-cancel" @click="openReason(a, 'decline')"><X :size="14" /> Decline</button>
            </div>
          </article>
        </template>

        <!-- ============ UPCOMING ============ -->
        <template v-else-if="tab === 'upcoming'">
          <section v-if="list('rescheduling').length" class="day">
            <p class="day-label"><span class="day-ico gold"><CalendarClock :size="15" /></span>Rescheduling<span class="day-count">{{ list('rescheduling').length }}</span></p>
            <article v-for="a in list('rescheduling')" :key="a.id" class="row tone-gold">
              <DateBlock :at="a.scheduled_at" tone="gold" />
              <div class="row-main">
                <p class="who">
                  <NuxtLink :to="`/client-detail/${a.relationship_id}`" class="name-link">{{ a.client.name }}</NuxtLink>
                  <span class="nm-pill gold">{{ a.reschedule?.turn === 'rnd' ? 'Your answer needed' : 'Waiting for the patient' }}</span>
                  <span v-if="a.payment?.status === 'paid'" class="nm-pill green">Paid</span>
                  <span v-else class="nm-pill muted">Not paid yet</span>
                </p>
                <p class="nm-row-sub">Booked for {{ timeRange(a) }}, {{ a.type_label.toLowerCase() }}</p>
                <RescheduleAnswer :appointment="a" role="rnd" :other-name="a.client.name" @changed="load" @cancel="openReason(a, 'cancel', 'refund')" />
              </div>
            </article>
          </section>
          <div v-if="!list('upcoming').length && !list('rescheduling').length" class="nm-empty"><CalendarDays :size="26" /><p>No confirmed consultations coming up.</p></div>
          <section v-for="g in upcomingByDay" :key="g.key" class="day">
            <p class="day-label"><span class="day-ico"><CalendarDays :size="15" /></span>{{ g.label }}<small v-if="['Today', 'Tomorrow'].includes(g.label)" class="day-date">{{ dayDate(g.items[0].scheduled_at) }}</small><span class="day-count">{{ g.items.length }} consultation{{ g.items.length === 1 ? '' : 's' }}</span></p>
            <article v-for="a in g.items" :key="a.id" class="row tone-green">
              <span class="time"><b>{{ timeParts(a.scheduled_at)[0] }}</b><i>{{ timeParts(a.scheduled_at)[1] }}</i><small>{{ a.duration_minutes }} min</small></span>
              <img v-if="a.client.profile_photo" :src="a.client.profile_photo" alt="" class="ap-av photo" />
              <span v-else class="ap-av" aria-hidden="true">{{ initialsOf(a.client.name) }}</span>
              <div class="row-main">
                <p class="who">
                  <NuxtLink :to="`/client-detail/${a.relationship_id}`" class="name-link">{{ a.client.name }}</NuxtLink>
                  <span v-if="a.payment?.status === 'paid'" class="nm-pill green">Paid</span>
                  <span v-else class="nm-pill muted">Not paid yet</span>
                </p>
                <p class="nm-row-sub with-icon">
                  <span class="type-chip" :class="a.type"><component :is="TYPE_ICONS[a.type]" :size="13" /> {{ a.type_label }}</span>
                  <i class="dot" aria-hidden="true"></i> {{ clock(a.scheduled_at) }} – {{ clock(a.ends_at) }}
                </p>
                <p v-if="a.type === 'in_person'" class="nm-row-sub addr with-icon">
                  <MapPin :size="13" class="ti" /> {{ a.clinic_address || 'No clinic address set. Add it in Profile Settings.' }}
                </p>
                <p v-if="a.payment?.status !== 'paid'" class="nm-row-sub">They pay before it starts. If it's still unpaid at {{ clock(a.pay_by || a.scheduled_at) }}, 15 minutes before, it's cancelled automatically.</p>
              </div>
              <div class="row-actions">
                <template v-if="inWindow(a)">
                  <NuxtLink v-if="a.type === 'video'" :to="`/consultation-room/${a.id}`" class="nm-btn-dark nm-btn-sm"><Video :size="14" /> Join</NuxtLink>
                  <NuxtLink v-else :to="`/consultation-room/${a.id}`" class="nm-btn-dark nm-btn-sm"><Users :size="14" /> Open room</NuxtLink>
                </template>
                <span v-else class="opens"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg> Opens {{ clock(a.join_opens_at) }}</span>
                <button v-if="canMove(a)" type="button" class="nm-btn-soft nm-btn-sm" @click="rescheduling = a"><CalendarDays :size="14" /> Reschedule</button>
                <button type="button" class="nm-btn-danger solid nm-btn-sm row-cancel" @click="openReason(a, 'cancel')"><X :size="14" /> Cancel</button>
              </div>
            </article>
          </section>
        </template>

        <!-- ============ TO COMPLETE ============ -->
        <template v-else-if="tab === 'to_complete'">
          <p class="tab-intro">Video consultations close by themselves when the room closes, from the call's attendance record: completed, a no-show, or refunded. So only in-person consultations wait here. Nothing records an in-person visit, so you mark it complete or a no-show. NutriMatch is told if one stays open for 3 days.</p>
          <p v-if="justCompleted" class="done-note">
            <CheckCircle2 :size="15" /> {{ justCompleted.client.first_name }}'s consultation is complete. Next:
            <NuxtLink :to="`/client-detail/${justCompleted.relationship_id}?tab=ncp`" class="nm-panel-link">Finish the NCP record</NuxtLink>
          </p>
          <div v-if="!list('to_complete').length" class="nm-empty"><CheckCircle2 :size="26" /><p>Nothing to close. You're all caught up.</p></div>
          <article v-for="a in list('to_complete')" :key="a.id" class="row tone-amber">
            <DateBlock :at="a.scheduled_at" tone="muted" />
            <div class="row-main">
              <p class="who"><NuxtLink :to="`/client-detail/${a.relationship_id}`" class="name-link">{{ a.client.name }}</NuxtLink></p>
              <p class="nm-row-sub">{{ timeRange(a) }}, {{ a.type_label.toLowerCase() }}, ended {{ ago(a.ends_at) }}</p>
              <p v-if="a.type === 'video'" class="nm-row-sub">This video consultation closes by itself from the call's attendance record.</p>
            </div>
            <div class="row-actions">
              <button v-if="a.payment && a.payment.status !== 'paid'" type="button" class="nm-btn-outline nm-btn-sm" disabled title="Can't complete an unpaid consultation">Waiting for payment</button>
              <template v-else-if="a.type !== 'video'">
                <NuxtLink :to="`/consultation-room/${a.id}`" class="nm-btn-soft nm-btn-sm">Open room</NuxtLink>
                <button type="button" class="nm-btn-dark nm-btn-sm" @click="completeTarget = a">Mark complete</button>
              </template>
            </div>
          </article>
        </template>

        <!-- ============ HISTORY ============ -->
        <template v-else>
          <div v-if="!history.length" class="nm-empty"><History :size="26" /><p>{{ search ? 'No consultations match that name.' : 'No past consultations yet.' }}</p></div>
          <article v-for="a in pagedHistory" :key="a.id" class="row past" :class="'tone-' + (a.status === 'completed' ? 'green' : a.status === 'no_show' ? 'red' : 'grey')">
            <DateBlock :at="a.scheduled_at" tone="muted" />
            <div class="row-main">
              <p class="who">
                <NuxtLink :to="`/client-detail/${a.relationship_id}`" class="name-link">{{ a.client.name }}</NuxtLink>
                <span class="nm-pill" :class="a.status === 'completed' ? 'green' : a.status === 'no_show' ? 'red' : 'muted'">{{ a.status === 'completed' ? 'Completed' : a.status === 'no_show' ? 'No-show' : 'Cancelled' }}</span>
                <span v-if="a.dispute?.opened_at && !a.dispute.resolved_at" class="nm-pill gold">Disputed, payment on hold</span>
                <span v-if="a.payment && ['refund_pending', 'refunded'].includes(a.payment.status)" class="nm-pill red">{{ a.payment.status === 'refunded' ? 'Refunded' : 'Refund pending' }}</span>
              </p>
              <p class="nm-row-sub">{{ timeRange(a) }}, {{ a.type_label.toLowerCase() }}{{ a.payment?.status === 'paid' ? `, ${peso(a.payment.amount)}` : '' }}</p>
              <p v-if="['cancelled', 'no_show'].includes(a.status) && a.cancellation_reason" class="nm-row-sub">{{ a.status === 'no_show' ? 'Your note' : 'Reason' }}: {{ a.cancellation_reason }}</p>
              <p v-if="a.attendance && a.attendance.state !== 'none' && a.status !== 'pending'" class="nm-row-sub">{{ a.attendance.line }}</p>
              <p v-if="a.dispute?.outcome" class="nm-row-sub">Dispute {{ a.dispute.outcome === 'refunded' ? 'approved, payment refunded' : 'not approved, the payment stays yours' }}. {{ a.dispute.note }}</p>
            </div>
            <div v-if="a.status === 'completed'" class="row-actions">
              <button type="button" class="nm-btn-outline nm-btn-sm" @click="summaryId = a.id"><FileText :size="14" /> Summary</button>
            </div>
          </article>
          <ListPager v-model:page="historyPage" :pages="historyPages" />
        </template>
      </div>
    </template>

    <!-- REVIEW & CONFIRM (full screening) -->
    <div v-if="review" class="nm-modal-overlay" @click.self="review = null">
      <div class="nm-modal wide review-modal" role="dialog" aria-modal="true" aria-labelledby="review-title">
        <header class="bm-head">
          <img class="bm-plate" :src="plateImg" alt="" aria-hidden="true" />
          <span class="bm-fade" aria-hidden="true"></span>
          <img v-if="review.appt.client.profile_photo" :src="review.appt.client.profile_photo" alt="" class="bm-av photo" />
          <span v-else class="bm-av" aria-hidden="true">{{ initialsOf(review.appt.client.name) }}</span>
          <div class="bm-head-txt">
            <p class="bm-kind">{{ review.appt.returning ? 'Booking request, returning patient' : 'New booking request' }}</p>
            <h2 id="review-title" class="nm-modal-title">{{ review.appt.client.name }}</h2>
            <p v-if="review.data" class="bm-sub">{{ review.data.client.age ?? '—' }} y/o, {{ SEX[review.data.client.sex] || '—' }}</p>
          </div>
          <button type="button" class="nm-modal-x bm-x" aria-label="Close" @click="review = null"><X :size="18" /></button>
        </header>

        <div class="bm-body">
          <p class="nm-modal-text bm-when">
            <span><CalendarDays :size="16" /> {{ whenDay(review.appt.scheduled_at) }}</span>
            <span><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg> {{ clock(review.appt.scheduled_at) }}</span>
            <span><component :is="TYPE_ICONS[review.appt.type]" :size="16" /> {{ review.appt.type_label }}</span>
            <span><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2h12M6 22h12M7 2v4l5 6-5 6v4M17 2v4l-5 6 5 6v4" /></svg> {{ review.appt.duration_minutes }} min</span>
          </p>
          <p v-if="review.loading" class="nm-muted bm-state"><span class="bm-spin" aria-hidden="true"></span> Loading screening…</p>
          <p v-else-if="review.error" class="nm-error">{{ review.error }}</p>
          <template v-else-if="review.data">
            <section class="bm-sec">
              <h3 class="section-k"><span class="bm-sico"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg></span>Patient profile</h3>
              <dl class="facts br-list">
              <div class="br-row"><dt><span class="br-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z" /></svg></span>Conditions</dt><dd><template v-if="review.data.client.medical_conditions?.length"><i v-for="x in review.data.client.medical_conditions" :key="x" class="bc blue">{{ x }}</i></template><span v-else class="br-none">None</span></dd></div>
              <div class="br-row" :class="{ warn: review.data.client.allergies?.length }"><dt><span class="br-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l10 18H2z" /><path d="M12 10v4M12 17h.01" /></svg></span>Food allergies</dt><dd><template v-if="review.data.client.allergies?.length"><i v-for="x in review.data.client.allergies" :key="x" class="bc red">{{ x }}</i></template><span v-else class="br-none">None</span></dd></div>
              <div class="br-row"><dt><span class="br-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 20A7 7 0 0 1 4 13c0-6 7-10 16-10 0 9-4 16-10 16" /><path d="M4 21c4-6 8-9 12-11" /></svg></span>Diet</dt><dd><template v-if="review.data.client.dietary_restrictions?.length"><i v-for="x in review.data.client.dietary_restrictions" :key="x" class="bc green">{{ x }}</i></template><span v-else class="br-none">None</span></dd></div>
              <div class="br-row"><dt><span class="br-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg></span>Goals</dt><dd><template v-if="review.data.client.health_goals?.length"><i v-for="x in review.data.client.health_goals" :key="x" class="bc gold">{{ x }}</i></template><span v-else class="br-none">None</span></dd></div>
              </dl>
              <p v-if="review.data.appointment.notes" class="client-note"><span class="cn-k"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg> Note from {{ review.appt.client.first_name }}</span>{{ review.data.appointment.notes }}</p>
            </section>
            <template v-if="review.data.screening">
              <section class="bm-sec">
                <h3 class="section-k"><span class="bm-sico"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4h6v3H9zM9 12h6M9 16h4" /></svg></span>Screening<em>Submitted {{ shortDate(review.data.screening.created_at) }}</em></h3>
                <div class="results">
                  <div><small>BMI</small><strong>{{ review.data.screening.bmi != null ? Number(review.data.screening.bmi).toFixed(1) : '—' }}</strong><i v-if="review.data.screening.bmi_category" class="rs-pill" :class="bmiTone(review.data.screening.bmi_category)">{{ review.data.screening.bmi_category }}</i></div>
                  <div><small>BMR</small><strong>{{ whole(review.data.screening.bmr_kcal) }}</strong><span>kcal/day</span></div>
                  <div><small>TER</small><strong>{{ whole(review.data.screening.tdee_kcal) }}</strong><span>kcal/day</span></div>
                  <div :class="{ risk: (review.data.screening.nrs_score ?? 0) >= 3 }"><small>NRS-2002</small><strong>{{ review.data.screening.nrs_score ?? '—' }}</strong><i v-if="RISK[review.data.screening.nrs_risk]" class="rs-pill" :class="(review.data.screening.nrs_score ?? 0) >= 3 ? 'bad' : 'ok'">{{ RISK[review.data.screening.nrs_risk] }}</i></div>
                </div>
                <dl class="facts br-list">
              <div class="br-row"><dt><span class="br-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17L17 3l4 4L7 21z" /><path d="M7 13l2 2M10 10l2 2M13 7l2 2" /></svg></span>Height and weight</dt><dd><b>{{ Number(review.data.screening.height_cm) }} cm</b><i class="br-dot" aria-hidden="true"></i><b>{{ Number(review.data.screening.weight_kg) }} kg</b></dd></div>
              <div class="br-row"><dt><span class="br-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="13" cy="4" r="2" /><path d="M7 21l3-6 3 2v4M6 12l3-3 4 1 3 3 3 1" /></svg></span>Activity</dt><dd><b>{{ ACTIVITY[review.data.screening.activity_level] || '—' }}</b></dd></div>
              <div class="br-row"><dt><span class="br-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h4l3-8 4 16 3-8h4" /></svg></span>Symptoms</dt><dd><template v-if="symptomList(review.data.screening.symptoms).length"><i v-for="x in symptomList(review.data.screening.symptoms)" :key="x" class="bc muted">{{ x }}</i></template><span v-else class="br-none">None reported</span></dd></div>
                </dl>
              </section>
              <p class="nm-hint bm-note"><span class="bm-note-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg></span><span>Confirming sends {{ review.appt.client.first_name }} an invoice for your fee. If it's still unpaid 15 minutes before the start, the booking is cancelled and the slot opens again.</span></p>
            </template>
            <p v-else class="nm-note todo-note bm-todo"><AlertTriangle :size="16" /> They haven't submitted a pre-consultation screening yet, so this booking can't be confirmed.</p>
            <p v-if="review.actionError" class="nm-field-error">{{ review.actionError }}</p>
          </template>
        </div>
        <div v-if="review.data && !review.loading && !review.error" class="nm-modal-actions bm-foot">
          <button type="button" class="nm-btn-danger solid bm-decline" @click="openReason(review.appt, 'decline')"><X :size="15" /> Decline</button>
          <button type="button" class="nm-btn-dark bm-confirm" :disabled="busy || !review.data.screening" @click="confirmBooking"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg> {{ busy ? 'Confirming…' : 'Confirm booking' }}</button>
        </div>
      </div>
    </div>

    <!-- RESCHEDULE: offer a later time (2026-11-23: paid or not), the same pop-up as the client's -->
    <RescheduleModal
      v-if="rescheduling" role="rnd" :appointment-id="rescheduling.id" :other-first-name="rescheduling.client.first_name"
      :paid="rescheduling.payment?.status === 'paid'" :late="movingLate" :type-label="rescheduling.type_label"
      :booked-label="longWhen(rescheduling.scheduled_at)"
      @close="rescheduling = null" @done="onOffered"
    />

    <!-- DECLINE / CANCEL WITH A REASON -->
    <div v-if="reason" class="nm-modal-overlay" @click.self="reason = null">
      <form class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="reason-title" @submit.prevent="submitReason">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="reason = null"><X :size="18" aria-hidden="true" /></button>
        <template v-if="reason.done">
          <h2 id="reason-title" class="nm-modal-title">Consultation cancelled</h2>
          <p class="nm-modal-text">{{ reason.appt.client.name }} was told and gets a full refund if they paid. Last-minute cancels are noted for NutriMatch.</p>
          <p class="nm-modal-text">Away for a while? Block time off so no new bookings land while you're out.</p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-soft" @click="reason = null">Close</button>
            <NuxtLink to="/availability" class="nm-btn-dark">Block time off</NuxtLink>
          </div>
        </template>
        <template v-else>
        <h2 id="reason-title" class="nm-modal-title">{{ reason.kind === 'decline' ? 'Decline this request?' : 'Cancel this consultation?' }}</h2>
        <p class="nm-modal-text">
          {{ reason.appt.client.name }}, {{ longWhen(reason.appt.scheduled_at) }}.
          <template v-if="reason.kind === 'decline'">They're notified with your reason and can book another time.</template>
          <template v-else-if="reason.appt.payment?.status === 'paid'">They already paid, so their invoice goes to <strong>refund pending</strong> and the NutriMatch admin refunds them.</template>
          <template v-else>Their unpaid invoice is voided and they're notified with your reason.</template>
        </p>
        <template v-if="reason.late">
          <p class="nm-note plain-note">It starts in under 30 minutes, so this counts as a last-minute cancel even if you move it. Pick why; you don't have to give details.</p>
          <label class="nm-label" for="reason-cat">Why you can't make it</label>
          <select id="reason-cat" v-model="reason.category" class="nm-select block">
            <option value="" disabled>Choose a reason</option>
            <option value="emergency">Emergency (family or health)</option>
            <option value="technical">Technical problem</option>
            <option value="other">Other</option>
          </select>
        </template>
        <label class="nm-label" for="reason-text">{{ reason.late && reason.category !== 'other' ? 'Note to the client (optional)' : 'Reason (sent to the client)' }}</label>
        <textarea id="reason-text" v-model="reason.text" class="nm-input" rows="3" maxlength="500"
                  :placeholder="reason.kind === 'decline' ? 'e.g. I\'m fully booked that day. Please choose another time.' : 'e.g. Please book again any day next week.'"></textarea>
        <p v-if="reason.error" class="nm-field-error">{{ reason.error }}</p>
        <p v-else-if="!reason.late || reason.category === 'other'" class="nm-hint">At least 10 characters.</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="reason = null">Keep it</button>
          <button type="submit" class="nm-btn-danger solid" :disabled="busy || !reasonReady">
            {{ busy ? 'Saving…' : reason.kind === 'decline' ? 'Decline request' : 'Cancel consultation' }}
          </button>
        </div>
        </template>
      </form>
    </div>

    <!-- MARK COMPLETE -->
    <div v-if="completeTarget" class="nm-modal-overlay" @click.self="completeTarget = null">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="complete-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="completeTarget = null"><X :size="18" aria-hidden="true" /></button>
        <h2 id="complete-title" class="nm-modal-title">Mark this consultation complete?</h2>
        <p class="nm-modal-text">
          {{ completeTarget.client.name }}, {{ longWhen(completeTarget.scheduled_at) }}.
          <template v-if="completeTarget.payment">They paid {{ peso(completeTarget.payment.amount) }}. Your share posts 3 days after today.</template>
          <template v-else>This was booked before pay-first, so completing sends them an invoice.</template>
          This can't be undone.
        </p>
        <p v-if="completeError" class="nm-field-error">{{ completeError }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="completeTarget = null">Not yet</button>
          <button type="button" class="nm-btn-dark" :disabled="busy" @click="completeNow">{{ busy ? 'Completing…' : 'Mark complete' }}</button>
        </div>
      </div>
    </div>
    <ConsultationSummaryModal v-if="summaryId" :appointment-id="summaryId" role="rnd" @close="summaryId = null" />
  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
const toast = useToast() // the app's toast (2026-11-03)
import {
  AlertTriangle, CalendarClock, CalendarDays, CheckCircle2, FileText, History, Inbox, MapPin, MessageSquare, OctagonAlert, Search, Users, Video, X,
} from 'lucide-vue-next'

const { get, patch, post } = useApi()
const route = useRoute()
const router = useRouter()
const now = useNow()

const board = ref(null)
const loading = ref(true)
const error = ref('')
const busy = ref(false)
const search = ref('')

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    board.value = await get('/rnd/appointments/board/')
  } catch {
    if (!quiet) error.value = 'Could not load your appointments.'
  } finally {
    loading.value = false
  }
}
// a new booking request, a payment or a cancellation shows without a reload
useAutoRefresh(() => load({ quiet: true }))

/* ---------- tabs + ?relationship= filter (from a patient chart) ---------- */
const TABS = [
  { key: 'requests', label: 'Requests' },
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'to_complete', label: 'To complete' },
  { key: 'history', label: 'History' },
]
const tab = ref(TABS.some(t => t.key === route.query.tab) ? route.query.tab : null)
function setTab(k) {
  tab.value = k
  router.replace({ query: { ...route.query, tab: k } })
}
// A notification can switch the tab while this page is already open.
watch(() => route.query.tab, (t) => {
  if (TABS.some(x => x.key === t) && t !== tab.value) { tab.value = t; load({ quiet: true }) }
})
onMounted(async () => {
  await load()
  if (!tab.value && board.value) tab.value = board.value.requests.length ? 'requests' : board.value.to_complete.length && !board.value.upcoming.length ? 'to_complete' : 'upcoming'
})
const patientFilter = computed(() => route.query.relationship ? String(route.query.relationship) : null)
const patientFilterName = computed(() => {
  for (const k of ['requests', 'upcoming', 'to_complete', 'history']) {
    const hit = board.value?.[k].find(a => String(a.relationship_id) === patientFilter.value)
    if (hit) return hit.client.name
  }
  return 'this patient'
})
function list(k) {
  const rows = board.value?.[k] || []
  return patientFilter.value ? rows.filter(a => String(a.relationship_id) === patientFilter.value) : rows
}
const history = computed(() => {
  const q = search.value.trim().toLowerCase()
  return list('history').filter(a => !q || a.client.name.toLowerCase().includes(q))
})
const { page: historyPage, pages: historyPages, paged: pagedHistory } = usePager(history, { resetOn: () => [search.value, patientFilter.value] })

/* ---------- time (PH) ---------- */
const PH = { timeZone: 'Asia/Manila' }
const phDate = v => new Date(v).toLocaleDateString('en-CA', PH)
const clock = v => new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
const longWhen = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
function dayLabel(v) {
  const d = phDate(v)
  if (d === phDate(now.value)) return 'Today'
  if (d === phDate(now.value + 86400000)) return 'Tomorrow'
  return new Date(v).toLocaleDateString('en-PH', { ...PH, weekday: 'long', month: 'long', day: 'numeric' })
}
const timeRange = a => `${new Date(a.scheduled_at).toLocaleDateString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric' })}, ${clock(a.scheduled_at)}–${clock(a.ends_at)}`
function hoursText(h) {
  if (h < 1) return `${Math.max(1, Math.round(h * 60))} minutes`
  return `${Math.round(h)} hour${Math.round(h) === 1 ? '' : 's'}`
}
function ago(v) {
  const mins = Math.round((now.value - new Date(v).getTime()) / 60000)
  if (mins < 60) return `${mins} min ago`
  if (mins < 1440) return `${Math.round(mins / 60)} h ago`
  return `${Math.round(mins / 1440)} day${Math.round(mins / 1440) === 1 ? '' : 's'} ago`
}
const inWindow = a => now.value >= new Date(a.join_opens_at).getTime() && now.value <= new Date(a.join_closes_at).getTime()
const upcomingByDay = computed(() => {
  const groups = []
  for (const a of list('upcoming')) {
    const key = phDate(a.scheduled_at)
    let g = groups.find(x => x.key === key)
    if (!g) groups.push(g = { key, label: dayLabel(a.scheduled_at), items: [] })
    g.items.push(a)
  }
  return groups
})

const TYPE_ICONS = { video: Video, chat: MessageSquare, in_person: Users }
const SEX = { male: 'Male', female: 'Female' }
const RISK = { no_risk: 'No risk', at_risk: 'At risk', high_risk: 'High risk' }
const ACTIVITY = { sedentary: 'Sedentary', lightly_active: 'Lightly active', moderately_active: 'Moderately active', very_active: 'Very active', extra_active: 'Extra active' }
const listText = l => (l?.length ? l.join(', ') : 'None')
const whole = v => (v == null ? '—' : Math.round(Number(v)).toLocaleString('en-PH'))

const DateBlock = defineComponent({
  props: { at: String, tone: String },
  setup(props) {
    return () => h('span', { class: ['date-block', props.tone] }, [
      h('span', { class: 'db-day' }, new Date(props.at).toLocaleDateString('en-PH', { ...PH, day: 'numeric' })),
      h('span', { class: 'db-mon' }, new Date(props.at).toLocaleDateString('en-PH', { ...PH, month: 'short' })),
    ])
  },
})

/* ---------- review & confirm ---------- */
const review = ref(null)
async function openReview(a) {
  review.value = { appt: a, loading: true, data: null, error: '', actionError: '' }
  try {
    review.value.data = await get(`/rnd/appointments/${a.id}/screening/`)
  } catch (e) {
    review.value.error = apiError(e, 'Could not load the screening.')
  } finally {
    review.value.loading = false
  }
}
async function confirmBooking() {
  busy.value = true
  review.value.actionError = ''
  try {
    await patch(`/rnd/appointments/${review.value.appt.id}/confirm/`)
    toast.success(`Booking confirmed. ${review.value.appt.client.first_name} was sent the invoice.`)
    review.value = null
    await load()
  } catch (e) {
    review.value.actionError = apiError(e, 'Could not confirm this booking.')
  } finally {
    busy.value = false
  }
}

/* ---------- decline / cancel ---------- */
const reason = ref(null)
function openReason(a, kind) {
  review.value = null
  const isRescheduling = a.status === 'rescheduling'
  // A confirmed consultation in its last 30 minutes (or started): a last-minute cancel.
  // (Being rescheduled: that was settled when the new time was offered.)
  const late = kind === 'cancel' && !isRescheduling && now.value >= new Date(a.scheduled_at).getTime() - 30 * 60000
  reason.value = { appt: a, kind, text: '', error: '', late, category: '', done: false }
}
/* ---------- reschedule (2026-11-23): the shared pop-up, RescheduleModal.vue ---------- */
const rescheduling = ref(null)
// a confirmed consultation that hasn't started, paid or not
const canMove = a => a.status === 'confirmed' && now.value < new Date(a.scheduled_at).getTime()
// in its last 30 minutes a move still counts as a last-minute cancel, so the pop-up asks why
const movingLate = computed(() => !!rescheduling.value && now.value >= new Date(rescheduling.value.scheduled_at).getTime() - 30 * 60000)
async function onOffered() {
  rescheduling.value = null
  await load()
}
const reasonReady = computed(() => {
  const r = reason.value
  if (!r) return false
  if (r.late) return !!r.category && (r.category !== 'other' || r.text.trim().length >= 10)
  return r.text.trim().length >= 10
})
function confirmClosed(a) {
  return a.time_passed || (a.confirm_by && now.value >= new Date(a.confirm_by).getTime())
}
function sameDay(a) {
  return new Date(a.confirm_by).toDateString() === new Date(now.value).toDateString()
}
function longDay(iso) {
  return new Date(iso).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}
async function submitReason() {
  busy.value = true
  reason.value.error = ''
  try {
    const r = reason.value
    await patch(`/rnd/appointments/${r.appt.id}/cancel/`, { reason: r.text.trim(), category: r.late ? r.category : undefined })
    if (r.late) r.done = true
    else {
      toast.success(`${r.kind === 'decline' ? 'Booking declined' : 'Consultation cancelled'}. ${r.appt.client.first_name} was told why.`)
      reason.value = null
    }
    await load()
  } catch (e) {
    reason.value.error = apiError(e, 'Could not save this.')
  } finally {
    busy.value = false
  }
}

/* ---------- mark complete ---------- */
const summaryId = ref(null)
const completeTarget = ref(null)
const completeError = ref('')
const justCompleted = ref(null)
async function completeNow() {
  busy.value = true
  completeError.value = ''
  try {
    await patch(`/rnd/appointments/${completeTarget.value.id}/complete/`)
    justCompleted.value = completeTarget.value
    completeTarget.value = null
    await load()
  } catch (e) {
    completeError.value = apiError(e, 'Could not complete this consultation.')
  } finally {
    busy.value = false
  }
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const HERO_TABS = ['requests', 'upcoming', 'to_complete']
const TAB_ICONS = { requests: Inbox, upcoming: CalendarDays, to_complete: CheckCircle2, history: History }
// same numbers as the tab counts
const tabCount = k => list(k).length + (k === 'upcoming' ? list('rescheduling').length : 0)
// "8:00 AM" → ["8:00", "AM"] for the time block
const timeParts = v => { const s = clock(v); const i = s.lastIndexOf(' '); return i > 0 ? [s.slice(0, i), s.slice(i + 1)] : [s, ''] }
// "Saturday, Nov 21" beside Today / Tomorrow
const dayDate = v => new Date(v).toLocaleDateString('en-PH', { ...PH, weekday: 'long', month: 'short', day: 'numeric' })
const initialsOf = name => { const w = String(name || '?').split(' ').filter(Boolean); return (w.length > 1 ? w[0][0] + w[w.length - 1][0] : (w[0] || '?')[0]).toUpperCase() }
// review modal: "Sat, Nov 21"
const whenDay = v => new Date(v).toLocaleDateString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric' })
// BMI category → pill colour
const bmiTone = c => (/normal/i.test(c || '') ? 'ok' : /obese/i.test(c || '') ? 'bad' : 'warn')
// "Always thirsty, Blurred vision" → chips
const symptomList = s => String(s || '').split(',').map(x => x.trim()).filter(Boolean)
</script>
<style scoped>
.nm-page { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); }
.ic { flex-shrink: 0; }

/* ---------- hero ---------- */
.ap-hero {
  position: relative; overflow: hidden; display: flex; align-items: flex-end; justify-content: space-between; gap: 18px 24px; flex-wrap: wrap;
  margin-bottom: 18px; padding: 26px 30px; border-radius: 24px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.ap-hero-plate { position: absolute; right: -70px; top: 50%; width: 340px; height: 340px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); opacity: 0.85; pointer-events: none; }
.ap-hero-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 48%, rgba(0, 77, 58, 0.8) 72%, rgba(0, 77, 58, 0.3) 100%); }
.ap-hero-txt { position: relative; z-index: 1; flex: 1 1 320px; min-width: 0; }
.ap-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.ap-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.ap-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.ap-hero .nm-page-sub { margin: 0 0 16px; font-size: 14.5px; line-height: 1.5; color: rgba(255, 255, 255, 0.85); }
.ap-avail { display: inline-flex; align-items: center; gap: 8px; height: 42px; padding: 0 18px; border-radius: 12px; background: #efbf04; color: #004d3a; font-size: 13.5px; font-weight: 800; text-decoration: none; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); transition: background 0.15s, transform 0.15s; }
.ap-avail:hover { background: #f5cb1c; transform: translateY(-1px); }
.ap-avail:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
.ap-figs { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(3, auto); gap: 8px; }
.ap-fig {
  display: flex; flex-direction: column; align-items: flex-start; min-width: 112px; padding: 10px 14px; border-radius: 14px; cursor: pointer; text-align: left;
  background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.18); color: #fff; font-family: inherit; backdrop-filter: blur(6px); transition: background 0.15s, transform 0.15s;
}
.ap-fig:hover { background: rgba(255, 255, 255, 0.18); transform: translateY(-1px); }
.ap-fig:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }
.ap-fig small { font-size: 11px; font-weight: 700; color: rgba(255, 255, 255, 0.75); white-space: nowrap; }
.ap-fig strong { font-family: 'Playfair Display', serif; font-size: 26px; line-height: 1.2; font-variant-numeric: lining-nums; }
.ap-fig.on { background: #fff; border-color: #fff; color: #004d3a; }
.ap-fig.on small { color: #6b7d73; }

.ap-loading { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px 20px; border-radius: 22px; box-shadow: var(--sh); }
.ap-loading .nm-muted { margin: 0; }
.ap-spin { width: 22px; height: 22px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: ap-spin 0.8s linear infinite; }
@keyframes ap-spin { to { transform: rotate(360deg); } }
.filter-note { margin-bottom: 14px; border-radius: 14px; }

/* ---------- tabs + search ---------- */
.ap-tabs { display: inline-flex; gap: 4px; padding: 5px; border-radius: 999px; background: #fff; border: none; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05), 0 8px 20px -14px rgba(0, 77, 58, 0.4); max-width: 100%; overflow-x: auto; scrollbar-width: none; }
.ap-tabs::-webkit-scrollbar { display: none; }
.ap-tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 38px; padding: 0 14px; margin: 0; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 700; color: #4a5a52; cursor: pointer; white-space: nowrap; }
.ap-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; color: #004d3a; }
.ap-tabs .tab-ic { color: #8a9a91; }
.ap-tabs .nm-count { min-width: 20px; height: 20px; padding: 0 6px; margin-left: 2px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 800; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; }
.ap-tabs .nm-tab.active { background: #004d3a; color: #fff; box-shadow: 0 8px 16px -10px rgba(0, 77, 58, 0.9); }
.ap-tabs .nm-tab.active .tab-ic { color: #efbf04; }
.ap-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }
.ap-tabs .nm-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.ap-search { position: relative; display: flex; align-items: center; gap: 10px; flex: 0 1 320px; height: 46px; padding: 0 16px; margin: 0; border-radius: 999px; background: #fff; border: 1.5px solid #d3dfd8; color: #8a9a91; box-sizing: border-box; }
.ap-search:focus-within { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.ap-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.ap-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }

/* ---------- list ---------- */
.appt-list { padding: 8px 0; border: none; border-radius: 24px; overflow: hidden; box-shadow: var(--sh); }
.tab-intro { margin: 8px 24px 6px; padding: 11px 14px; border-radius: 14px; background: #f1f6f2; border-left: 3px solid #1f9d55; font-size: 13px; line-height: 1.5; color: #2c4a3c; }
.row { position: relative; display: flex; gap: 18px; align-items: center; padding: 18px 24px 18px 28px; border-top: 1px solid #f0f3f1; transition: background 0.15s; }
.row:first-of-type, .tab-intro + .row, .day-label + .row { border-top: none; }
.row:hover { background: #fafcfb; }
.row::before { content: ''; position: absolute; left: 0; top: 18px; bottom: 18px; width: 4px; border-radius: 0 4px 4px 0; background: #1f9d55; }
.row.tone-gold::before { background: #efbf04; }
.row.tone-amber::before { background: #e0a100; }
.row.tone-red::before { background: #c0392b; }
.row.tone-grey::before { background: #c9d3cd; }
.row.past { opacity: 1; }
.row-main { flex: 1; min-width: 0; }
.row-actions { flex-shrink: 0; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.who { display: flex; align-items: center; gap: 6px 10px; flex-wrap: wrap; margin: 0 0 4px; }
.name-link { font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; letter-spacing: 0.01em; color: #0e3a2c; text-decoration: none; }
.name-link:hover { color: #004d3a; text-decoration: underline; text-underline-offset: 3px; }
.who .nm-pill { padding: 3px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 800; }
.who .nm-pill.green { background: #e3f4ea; color: #1f7a4d; }
.who .nm-pill.gold { background: #fff4d6; color: #8a6500; }
.who .nm-pill.red { background: #fdecea; color: #b42318; }
.who .nm-pill.muted { background: #eef2ef; color: #6b7d73; }
.row .nm-row-sub { margin: 6px 0 0; font-size: 13px; line-height: 1.5; color: #6b7d73; }
.ti { color: #8a9a91; flex-shrink: 0; }
.with-icon { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 8px; }
.with-icon .dot { width: 3px; height: 3px; border-radius: 50%; background: #b5c3ba; }
.type-chip { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px; background: #eef1fa; font-size: 12px; font-weight: 800; color: #3b5ba5; }
.type-chip.in_person { background: #fbf3d2; color: #9a7300; }
.type-chip.chat { background: #e3efe7; color: #004d3a; }
.addr { overflow-wrap: anywhere; }
.flag { display: inline-flex; align-items: center; gap: 6px; margin: 8px 0 0; padding: 6px 12px; border-radius: 12px; font-size: 12.5px; font-weight: 700; line-height: 1.4; }
.flag svg { flex-shrink: 0; }
.flag.critical { background: #fdecea; color: #b42318; }
.flag.warning { background: #fff4d6; color: #8a6500; }
.chips { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.chip { padding: 3px 10px; border-radius: 999px; background: #f3f7f4; font-size: 12px; font-weight: 700; color: #3e5046; }
.chip.allergy, .chip.risk { background: #fef3f2; color: #b42318; }
.client-note { margin: 10px 0 0; padding: 8px 12px; border-radius: 0 12px 12px 0; border-left: 3px solid #efbf04; background: #fffbea; font-size: 13px; color: #4a5a52; overflow-wrap: anywhere; }

/* day groups */
.day + .day { margin-top: 0; }
.day-label { display: flex; align-items: center; gap: 10px; margin: 0; padding: 12px 24px; background: #f7faf8; border-top: 1px solid #eef2ef; border-bottom: 1px solid #eef2ef; font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; color: #0e3a2c; }
.appt-list > .day:first-child .day-label, .appt-list > template + .day .day-label { border-top: none; }
.day-ico { width: 30px; height: 30px; border-radius: 10px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.day-ico.gold { background: #fbf3d2; color: #9a7300; }
.day-date { font-family: 'DM Sans', sans-serif; font-size: 13px; font-weight: 500; color: #6b7d73; }
.day-count { margin-left: auto; padding: 4px 11px; border-radius: 999px; background: #e3efe7; font-family: 'DM Sans', sans-serif; font-size: 12px; font-weight: 800; color: #004d3a; }

/* time block (upcoming) */
.time {
  flex-shrink: 0; width: 72px; height: 76px; border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; white-space: nowrap;
  background: linear-gradient(160deg, #035a45, #004d3a); color: #fff; border-bottom: 3px solid #efbf04; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.85);
}
.time b { font-family: 'Playfair Display', serif; font-size: 21px; line-height: 1.1; font-variant-numeric: lining-nums; }
.time i { font-style: normal; font-size: 10.5px; font-weight: 800; color: #efbf04; }
.time small { margin-top: 2px; font-size: 10.5px; font-weight: 500; color: rgba(255, 255, 255, 0.7); }
.ap-av.photo { object-fit: cover; box-sizing: border-box; }
.ap-av { flex-shrink: 0; width: 48px; height: 48px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-family: 'Playfair Display', serif; font-size: 16px; font-weight: 700; border: 2px solid #fff; box-shadow: 0 0 0 2.5px #1f9d55; }

/* date block (requests, to complete, history) */
:deep(.date-block) {
  flex-shrink: 0; width: 64px; height: 70px; border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: linear-gradient(160deg, #035a45, #004d3a); border-bottom: 3px solid #efbf04; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.85);
}
:deep(.db-day) { order: 2; font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 700; line-height: 1.1; color: #fff; font-variant-numeric: lining-nums; }
:deep(.db-mon) { order: 1; font-size: 10.5px; font-weight: 800; color: #efbf04; }
:deep(.date-block.gold) { background: #fff4d6; border-bottom-color: #e7c65a; box-shadow: none; }
:deep(.date-block.gold .db-day) { color: #8a6500; }
:deep(.date-block.gold .db-mon) { color: #9a7300; }
:deep(.date-block.muted) { background: #f1f4f2; border-bottom-color: #d3dfd8; box-shadow: none; }
:deep(.date-block.muted .db-day) { color: #3e5046; }
:deep(.date-block.muted .db-mon) { color: #6b7d73; }

/* row buttons */
.opens { display: inline-flex; align-items: center; gap: 6px; height: 40px; padding: 0 14px; border-radius: 12px; background: #fff8e6; border: 1px solid #f3e2a0; font-size: 13px; font-weight: 800; color: #8a6500; white-space: nowrap; }
.row-actions .nm-btn-dark, .row-actions .nm-btn-soft, .row-actions .nm-btn-outline, .row-actions .row-cancel {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; min-height: 40px; padding: 0 16px; border-radius: 12px; font-size: 13.5px; font-weight: 800; white-space: nowrap; text-decoration: none;
}
.row-actions .nm-btn-dark { background: #004d3a; border: 1px solid #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.row-actions .nm-btn-dark:hover { background: #00382a; }
.row-actions .nm-btn-soft, .row-actions .nm-btn-outline { background: #f1f6f2; border: 1px solid #dce8e0; color: #004d3a; }
.row-actions .row-cancel { background: #fef3f2; border: 1px solid #f6cfcb; color: #b42318; box-shadow: none; }
.row-actions .row-cancel:hover { background: #fde4e1; }
.done-note { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 4px 24px 10px; padding: 11px 14px; border-radius: 14px; background: #e3f4ea; font-size: 13.5px; font-weight: 700; color: #1f5c45; }

/* empty states */
.appt-list :deep(.nm-empty) { display: flex; flex-direction: column; align-items: center; gap: 10px; margin: 16px 24px; padding: 36px 20px; border-radius: 18px; border: 1.5px dashed #cfddd4; text-align: center; color: #004d3a; }
.appt-list :deep(.nm-empty p) { margin: 0; font-size: 14px; font-weight: 700; color: #4a5a52; }
.appt-list :deep(.nm-empty svg) { width: 52px; height: 52px; padding: 13px; border-radius: 16px; background: #e3efe7; box-sizing: border-box; }

/* ---------- modals ---------- */
.nm-modal.wide { max-width: 620px; }
.choices { display: grid; gap: 10px; margin: 4px 0 8px; }
.choice { display: flex; flex-direction: column; gap: 4px; padding: 14px 16px; border-radius: 14px; border: 1.5px solid #dce8e0; background: #fff; font-family: inherit; text-align: left; color: #0e3a2c; cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.choice strong { font-size: 14.5px; }
.choice span { font-size: 13px; line-height: 1.45; color: #6b7d73; }
.choice:hover { border-color: #004d3a; background: #f7faf8; }
.choice:focus-visible { outline: 2px solid #004d3a; outline-offset: 2px; }
.gap { height: 14px; }
.review-modal { position: relative; }
.facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 0 0 12px; }
.facts div { padding: 10px 12px; border-radius: 12px; background: #f7faf8; }
.facts dt { margin: 0; font-size: 11px; font-weight: 800; color: #8a9a91; }
.facts dd { margin: 2px 0 0; font-size: 13.5px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.facts dd.warn { color: #b42318; }
.section-k { margin: 16px 0 8px; font-size: 14px; font-weight: 800; color: #0e3a2c; }
.results { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-bottom: 12px; }
.results div { display: flex; flex-direction: column; min-width: 0; padding: 12px; border-radius: 14px; background: linear-gradient(160deg, #f1f8f4, #fff); border: 1px solid #dcede3; }
.results div.risk { background: #fef3f2; border-color: #f6cfcb; }
.results strong { font-family: 'Playfair Display', serif; font-size: 22px; color: #004d3a; font-variant-numeric: lining-nums tabular-nums; }
.results div.risk strong { color: #b42318; }
.results span { font-size: 11.5px; color: #6b7d73; }

/* ---------- review & confirm modal ---------- */
.nm-modal.review-modal { position: relative; display: flex; flex-direction: column; width: min(640px, 100%); max-width: 640px; max-height: calc(100vh - 48px); padding: 0; border-radius: 24px; overflow: hidden; background: #fff; box-shadow: 0 40px 90px -30px rgba(0, 0, 0, 0.55); }
.bm-head {
  position: relative; overflow: hidden; flex-shrink: 0; display: flex; align-items: center; gap: 14px; padding: 24px 26px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 55%, #004635 100%);
}
.bm-head > *:not(.bm-plate):not(.bm-fade) { position: relative; z-index: 1; }
.bm-plate { position: absolute; right: -40px; top: 50%; width: 220px; height: 220px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.bm-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 50%, rgba(0, 77, 58, 0.85) 68%, rgba(0, 77, 58, 0.65) 100%); }
.bm-av { flex-shrink: 0; width: 56px; height: 56px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; border: 3px solid rgba(255, 255, 255, 0.9); box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.14); }
.bm-av.photo { object-fit: cover; }
.bm-head-txt { flex: 1; min-width: 0; }
.bm-kind { display: flex; align-items: center; gap: 8px; margin: 0 0 4px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.bm-kind::before { content: ''; flex-shrink: 0; width: 7px; height: 7px; border-radius: 50%; background: #efbf04; box-shadow: 0 0 0 4px rgba(239, 191, 4, 0.22); }
.review-modal .bm-head .nm-modal-title { margin: 0; padding: 0; font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; line-height: 1.2; letter-spacing: 0.015em; color: #fff; overflow-wrap: anywhere; }
.bm-sub { margin: 3px 0 0; font-size: 14px; color: rgba(255, 255, 255, 0.85); }
.review-modal .nm-modal-x.bm-x { position: relative; inset: auto; flex-shrink: 0; align-self: flex-start; width: 38px; height: 38px; margin: 0; border-radius: 11px; border: 1px solid rgba(255, 255, 255, 0.3); background: rgba(0, 56, 42, 0.55); color: #fff; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; backdrop-filter: blur(6px); }
.review-modal .nm-modal-x.bm-x:hover { background: rgba(0, 56, 42, 0.8); }
.bm-body { flex: 1; min-height: 0; overflow-y: auto; padding: 20px 26px 22px; }
.review-modal .bm-when { display: flex; flex-wrap: wrap; gap: 8px; margin: 0; padding: 12px; border-radius: 16px; background: #f1f8f4; border: 1px solid #dcebe1; }
.bm-when span { display: inline-flex; align-items: center; gap: 7px; padding: 7px 12px; border-radius: 11px; background: #fff; font-size: 13.5px; font-weight: 700; color: #0e3a2c; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); }
.bm-when svg { color: #1f7a4d; flex-shrink: 0; }
.bm-state { display: flex; align-items: center; justify-content: center; gap: 10px; margin: 20px 0 0; padding: 26px; border-radius: 16px; background: #f7faf8; font-weight: 600; }
.bm-spin { width: 20px; height: 20px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: ap-spin 0.8s linear infinite; }
.bm-sec { margin-top: 20px; }
.review-modal .section-k { display: flex; align-items: center; gap: 10px; margin: 0 0 12px; font-size: 15px; font-weight: 800; color: #0e3a2c; }
.bm-sico { flex-shrink: 0; width: 28px; height: 28px; border-radius: 9px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.section-k em { margin-left: auto; padding: 4px 10px; border-radius: 999px; background: #f3f6f4; font-style: normal; font-size: 12px; font-weight: 600; color: #6b7d73; }
.facts.br-list { display: block; margin: 0; border-radius: 16px; border: 1px solid #e6eee9; overflow: hidden; }
.facts.br-list .br-row { display: grid; grid-template-columns: 170px minmax(0, 1fr); gap: 12px; align-items: center; padding: 12px 16px; border-radius: 0; background: #fff; border-bottom: 1px solid #eef2ef; }
.facts.br-list .br-row:last-child { border-bottom: none; }
.facts.br-list dt { display: flex; align-items: center; gap: 10px; margin: 0; font-size: 13.5px; font-weight: 500; letter-spacing: 0; text-transform: none; color: #4a5a52; }
.br-ico { flex-shrink: 0; width: 30px; height: 30px; border-radius: 10px; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.facts.br-list dd { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin: 0; font-size: 14.5px; font-weight: 400; color: #0e3a2c; }
.facts.br-list dd b { font-weight: 700; }
.br-dot { width: 4px; height: 4px; margin: 0 4px; border-radius: 50%; background: #b5c3ba; }
.br-none { font-size: 13.5px; color: #8a9a91; }
.facts.br-list .br-row.warn { background: #fff7f6; }
.facts.br-list .br-row.warn dt { color: #8c1d2c; font-weight: 600; }
.br-row.warn .br-ico { background: #fdecea; color: #b42318; }
.bc { display: inline-flex; align-items: center; padding: 5px 11px; border-radius: 999px; font-style: normal; font-size: 13px; font-weight: 700; line-height: 1.3; }
.bc.green { background: #e3f4ea; color: #1f5c45; }
.bc.blue { background: #eef1fa; color: #2e4a86; }
.bc.red { background: #fdecea; color: #b42318; box-shadow: inset 0 0 0 1px #f6c9c3; }
.bc.gold { background: #fff4d6; color: #8a6500; }
.bc.muted { background: #f3f6f4; color: #3e5046; font-weight: 600; }
.review-modal .client-note { margin: 12px 0 0; border-radius: 0 14px 14px 0; padding: 10px 14px; }
.cn-k { display: flex; align-items: center; gap: 6px; margin-bottom: 3px; font-size: 12px; font-weight: 800; color: #8a6500; }
.review-modal .results { gap: 10px; margin: 0 0 12px; }
.review-modal .results div { align-items: flex-start; gap: 2px; padding: 14px; border-radius: 16px; border-color: #dcebe1; }
.results small { font-size: 12px; font-weight: 700; color: #6b7d73; }
.review-modal .results strong { font-size: 26px; font-weight: 700; line-height: 1.15; }
.review-modal .results span { font-size: 12.5px; }
.rs-pill { padding: 2px 9px; border-radius: 999px; font-style: normal; font-size: 11.5px; font-weight: 800; }
.rs-pill.ok { background: #e3f4ea; color: #1f7a4d; }
.rs-pill.warn { background: #fff4d6; color: #8a6500; }
.rs-pill.bad { background: #fdecea; color: #b42318; }
.review-modal .bm-note { display: flex; gap: 10px; margin: 20px 0 0; padding: 12px 14px; border-radius: 14px; background: #fffbea; border: 1px solid #f3e2a0; font-size: 13px; line-height: 1.55; color: #6b5a1e; }
.bm-note-ico { flex-shrink: 0; margin-top: 1px; color: #c49102; }
.review-modal .bm-todo { display: flex; gap: 10px; align-items: flex-start; margin: 20px 0 0; border-radius: 14px; }
.review-modal .bm-todo svg { flex-shrink: 0; margin-top: 2px; }
.review-modal .nm-field-error { margin: 12px 0 0; }
.review-modal .bm-foot { flex-shrink: 0; display: flex; justify-content: flex-end; gap: 10px; margin: 0; padding: 14px 26px; border-top: 1px solid #eef2ef; background: #f7faf8; }
.bm-foot .bm-decline, .bm-foot .bm-confirm { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 44px; padding: 0 20px; border-radius: 12px; font-family: inherit; font-size: 14px; font-weight: 800; cursor: pointer; }
.bm-foot .bm-decline { background: #fff; border: 1px solid #f2c4be; color: #b42318; box-shadow: none; }
.bm-foot .bm-decline:hover { background: #fdecea; }
.bm-foot .bm-confirm { background: #004d3a; border: 1px solid #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.bm-foot .bm-confirm:hover:not(:disabled) { background: #00382a; }
.bm-foot .bm-confirm:disabled { opacity: 0.55; cursor: not-allowed; box-shadow: none; }
.bm-foot button:focus-visible, .bm-x:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }
@media (max-width: 760px) {
  .nm-modal.review-modal { max-height: calc(100dvh - 24px); border-radius: 22px; }
  .bm-head { padding: 18px; gap: 12px; }
  .bm-av { width: 46px; height: 46px; font-size: 16px; }
  .review-modal .bm-head .nm-modal-title { font-size: 22px; }
  .bm-plate { width: 160px; height: 160px; right: -50px; }
  .bm-body { padding: 16px 18px; }
  .facts.br-list .br-row { grid-template-columns: minmax(0, 1fr); gap: 8px; }
  .review-modal .bm-foot { padding: 12px 18px 16px; }
  .bm-foot > button { flex: 1; }
}

/* ---------- responsive ---------- */
@media (max-width: 960px) {
  .ap-hero { padding: 20px 18px; border-radius: 22px; }
  .ap-title { font-size: 24px; }
  .ap-hero-plate { width: 220px; height: 220px; right: -80px; top: 40px; transform: none; opacity: 0.5; }
  .ap-figs { flex-basis: 100%; grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .ap-fig { min-width: 0; }
  .ap-tabs { display: flex; border-radius: 16px; }
  .ap-search { flex: 1 1 100%; }
  .appt-list { padding: 0; overflow: visible; background: transparent; box-shadow: none; }
  .tab-intro, .done-note { margin: 0 0 12px; }
  .appt-list :deep(.nm-empty) { margin: 0; background: #fff; }
  .day-label { padding: 6px 2px 10px; background: transparent; border: none; }
  .day + .day { margin-top: 8px; }
  .row { flex-wrap: wrap; align-items: flex-start; gap: 14px; padding: 16px; border: none; border-radius: 20px; background: #fff; box-shadow: var(--sh); }
  .row + .row { margin-top: 12px; }
  .row:hover { background: #fff; }
  .ap-av { display: none; }
  .row-main { flex-basis: calc(100% - 90px); }
  .row-actions { width: 100%; justify-content: stretch; }
  .row-actions > * { flex: 1; }
}
@media (max-width: 760px) {
  .nm-page { padding-bottom: 110px; }
  .results { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 420px) {
  .facts { grid-template-columns: minmax(0, 1fr); }
  .time { width: 62px; height: 66px; }
  :deep(.date-block) { width: 56px; height: 62px; }
}

/* booking request modal: wider */
.nm-modal-overlay .nm-modal.wide.review-modal { width: min(860px, calc(100vw - 32px)) !important; max-width: none !important; }
</style>