<template>
  <div class="nm-page">
    <NuxtLink :to="backTo" class="nm-panel-link back-link"><ArrowLeft :size="15" /> {{ backLabel }}</NuxtLink>

    <p v-if="error" class="nm-error">{{ error }}</p>
    <p v-if="loading" class="nm-muted ud-loading"><span class="ud-spin" aria-hidden="true"></span> Loading account…</p>

    <template v-else-if="data">
      <!-- ACCOUNT FILE (2026-10-25): who they are and the account's state at the
           top, real information below, anything missing in one grey line. -->
      <section class="nm-panel file-head">
        <div class="fh-top">
          <img class="ud-plate" :src="plateImg" alt="" aria-hidden="true" />
          <span class="ud-fade" aria-hidden="true"></span>
          <div class="identity-main">
            <img v-if="u.profile_photo" :src="u.profile_photo" class="nm-avatar lg" alt="" />
            <span v-else class="nm-avatar lg">{{ userInitials(u.first_name, u.last_name) }}</span>
            <div style="min-width: 0">
              <p class="ud-eyebrow"><span aria-hidden="true"></span>{{ roleLabel }} account</p>
              <h1 class="nm-page-title" style="margin: 0">{{ u.first_name }} {{ u.last_name }}</h1>
              <p class="nm-page-sub"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M22 6l-10 7L2 6" /></svg> {{ u.email }}<template v-if="u.phone">, {{ formatPhone(u.phone) }}</template></p>
              <div class="pill-row">
                <span class="nm-pill muted">{{ roleLabel }}</span>
                <span class="nm-pill" :class="account.is_active ? 'green' : 'muted'">{{ account.is_active ? 'Active' : 'Deactivated' }}</span>
                <span v-if="rnd" class="nm-pill" :class="reviewPill">{{ reviewLabel }}</span>
              </div>
            </div>
          </div>
          <div v-if="!isSelf" class="identity-actions">
            <button type="button" class="nm-btn-soft" :disabled="busy" @click="openEdit"><Pencil :size="14" aria-hidden="true" /> Edit details</button>
            <button type="button" class="nm-btn-soft" :disabled="busy" @click="sendReset"><KeyRound :size="14" aria-hidden="true" /> Send password reset</button>
            <button v-if="account.is_active" type="button" class="nm-btn-danger solid" :disabled="busy" @click="openDeactivate"><Ban :size="14" aria-hidden="true" /> Deactivate</button>
            <button v-else type="button" class="nm-btn-dark" :disabled="busy" @click="reactivate"><RotateCcw :size="14" aria-hidden="true" /> Reactivate</button>
          </div>
        </div>
        <!-- the account at a glance (gold = something not done yet) -->
        <dl class="fh-strip">
          <div v-for="c in stripCells" :key="c.label" :class="{ warn: c.warn }">
            <span class="fh-ico" aria-hidden="true"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path v-for="(d, i) in (STRIP_ICON[c.label] || STRIP_ICON.Joined)" :key="i" :d="d" /></svg></span>
            <dt>{{ c.label }}</dt><dd>{{ c.value }}</dd>
          </div>
        </dl>
        <p v-if="client" class="fh-audit"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg> Health information. Your view was recorded in the audit log (RA 10173).</p>
      </section>

      <!-- CLIENT -->
      <div v-if="client" class="file-grid">
        <div class="file-col">
          <section class="nm-panel uc">
            <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z" /></svg></span><h2 class="nm-panel-title">Care</h2><NuxtLink :to="`/admin-appointments?view=all&client=${u.id}`" class="nm-panel-link">Appointments <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink></div>
            <p class="care-rnds">
              <template v-if="client.rnds.length">
                <span class="label">RND</span>
                <span v-for="r in client.rnds" :key="r.rnd_id" class="care-rnd">
                  <NuxtLink :to="`/users/${r.rnd_id}`" class="nm-text-link">{{ r.name }}</NuxtLink>
                  <span class="nm-pill" :class="r.status === 'active' ? 'green' : 'muted'">{{ cap(r.status) }}</span>
                </span>
              </template>
              <span v-else class="nm-muted care-empty"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg> Hasn't booked an RND yet.</span>
            </p>
            <div class="figs four">
              <div><i class="fig-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg></i><strong>{{ appt(client, 'pending') + appt(client, 'confirmed') }}</strong><span>Upcoming or waiting</span></div>
              <div><i class="fig-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M8.5 12.5l2.5 2.5 4.5-5" /></svg></i><strong>{{ appt(client, 'completed') }}</strong><span>Completed</span></div>
              <div><i class="fig-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M15 9l-6 6M9 9l6 6" /></svg></i><strong>{{ appt(client, 'cancelled') }}</strong><span>Cancelled</span></div>
              <div><i class="fig-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 21V3h6a5 5 0 0 1 0 10H7" /><path d="M4 7h16M4 10h16" /></svg></i><strong>{{ peso(client.invoices.paid_total) }}</strong><span>Total paid</span></div>
            </div>
          </section>

          <section class="nm-panel uc">
            <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h4l3-8 4 16 3-8h4" /></svg></span><h2 class="nm-panel-title">Health</h2></div>
            <dl class="facts">
              <div v-if="listText(client.health.medical_conditions)"><dt>Conditions</dt><dd><span class="chip blue">{{ listText(client.health.medical_conditions) }}</span></dd></div>
              <!-- allergies are never quiet (patient safety) -->
              <div>
                <dt>Allergies</dt>
                <dd>
                  <span v-if="client.health.allergies == null" class="gap">Not answered yet</span>
                  <span v-else-if="!listText(client.health.allergies)">No known allergies</span>
                  <span v-else class="allergy-list"><span v-for="a in client.health.allergies" :key="a" class="allergy">{{ a }}</span></span>
                </dd>
              </div>
              <div v-if="listText(client.health.dietary_restrictions)"><dt>Diet</dt><dd>{{ listText(client.health.dietary_restrictions) }}</dd></div>
              <div v-if="listText(client.health.health_goals)"><dt>Goals</dt><dd>{{ listText(client.health.health_goals) }}</dd></div>
              <div v-if="client.health.religion"><dt>Religion</dt><dd>{{ client.health.religion }}</dd></div>
            </dl>
          </section>

          <section class="nm-panel uc">
            <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4h6v3H9zM9 12h6M9 16h4" /></svg></span><h2 class="nm-panel-title">Latest screening</h2></div>
            <p v-if="!s" class="uc-none"><span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4h6v3H9zM9 12h6M9 16h4" /></svg></span>No pre-consultation screening yet.</p>
            <p v-else class="nm-panel-sub">{{ s ? `Taken ${shortDate(s.created_at)}, ${client.screening_count} in total` : 'No pre-consultation screening yet.' }}</p>
            <div v-if="s" class="figs four" style="margin-top: 14px">
              <div><strong>{{ num(s.bmi) }}</strong><span>BMI<template v-if="s.bmi_category">, {{ s.bmi_category }}</template></span></div>
              <div :class="{ risk: Number(s.nrs_score) >= 3 }"><strong>{{ s.nrs_score ?? '—' }}</strong><span>NRS-2002<template v-if="s.nrs_risk">, {{ cap(s.nrs_risk).toLowerCase() }}</template></span></div>
              <div><strong>{{ num(s.weight_kg) }} kg</strong><span>{{ num(s.height_cm) }} cm tall</span></div>
              <div><strong>{{ s.tdee_kcal ? Math.round(s.tdee_kcal).toLocaleString('en-PH') : '—' }}</strong><span>kcal a day (TER)</span></div>
            </div>
          </section>
        </div>

        <div class="file-col">
          <section class="nm-panel uc">
            <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg></span><h2 class="nm-panel-title">Personal</h2></div>
            <dl class="facts">
              <div v-if="client.profile.date_of_birth"><dt>Born</dt><dd>{{ dobText(client.profile.date_of_birth) }}</dd></div>
              <div v-if="client.profile.sex"><dt>Sex</dt><dd>{{ cap(client.profile.sex) }}</dd></div>
              <div v-if="client.profile.address"><dt>Address</dt><dd>{{ client.profile.address }}</dd></div>
              <div v-if="client.profile.emergency_contact"><dt>Emergency contact</dt><dd>{{ emergencyText }}</dd></div>
            </dl>
            <p v-if="personalMissing.length === 4" class="nm-muted" style="margin: 12px 0 0">Nothing filled in yet.</p>
          </section>
          <section class="nm-panel uc">
            <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l3 2" /></svg></span><h2 class="nm-panel-title">Admin history</h2><span v-if="data.recent_activity.length" class="uc-count">{{ data.recent_activity.length }} event{{ data.recent_activity.length === 1 ? '' : 's' }}</span></div>
            <p v-if="!data.recent_activity.length" class="nm-muted uc-empty-line">Nothing recorded yet.</p>
            <div v-else class="history-wrap">
              <template v-for="g in historyDays" :key="g.day">
                <p class="tl-day"><span>{{ g.day }}</span></p>
                <ol class="history">
                  <li v-for="(it, i) in g.items" :key="i" :class="{ fresh: it.fresh }">
                    <span class="h-dot" aria-hidden="true"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg></span>
                    <span class="h-card">
                      <span class="h-main">
                        <span class="h-title">{{ auditLabel(it.a.action) }}</span>
                        <span v-if="it.a.by" class="h-by"><i class="h-av">{{ initialsOf(it.a.by) }}</i>{{ it.a.by }}</span>
                      </span>
                      <span class="h-time" :title="dateTime(it.a.created_at)">{{ it.time }}</span>
                    </span>
                  </li>
                </ol>
              </template>
            </div>
          </section>
        </div>
      </div>

      <!-- RND -->
      <template v-if="rnd">
        <section class="nm-panel figs-panel">
          <div class="figs six">
            <div><strong>{{ rnd.patients }}</strong><span>Active patients</span></div>
            <div><strong>{{ appt(rnd, 'completed') }}</strong><span>Consultations done</span></div>
            <div><strong>{{ rnd.rating.average ? `${rnd.rating.average} ★` : '—' }}</strong><span>{{ rnd.rating.count ? `${rnd.rating.count} review${rnd.rating.count === 1 ? '' : 's'}` : 'No reviews yet' }}</span></div>
            <div><strong>{{ peso(rnd.earnings.pending) }}</strong><span>Pending</span></div>
            <div><strong>{{ peso(rnd.earnings.posted) }}</strong><span>Cleared, waiting for payout</span></div>
            <div><strong>{{ peso(rnd.earnings.paid_out) }}</strong><span>Paid out, {{ rnd.payouts }} payout{{ rnd.payouts === 1 ? '' : 's' }}</span></div>
          </div>
        </section>

        <div class="file-grid">
          <div class="file-col">
            <p v-if="rnd.profile.review_status === 'rejected' && rnd.profile.rejection_reason" class="nm-note plain-note" style="margin: 0">
              <strong>Application rejected.</strong> Reason sent: {{ rnd.profile.rejection_reason }}
            </p>
            <section class="nm-panel uc">
              <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2" /><circle cx="8" cy="12" r="2.5" /><path d="M13 10h5M13 14h3" /></svg></span><h2 class="nm-panel-title">Credentials</h2><NuxtLink v-if="rnd.profile.review_status === 'pending'" :to="`/rnd-verification?open=${u.id}`" class="nm-panel-link">Review application <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink></div>
              <div class="cred">
                <div class="photos">
                  <div>
                    <p class="photo-label">PRC license</p>
                    <button v-if="rnd.profile.prc_license_image_url" type="button" class="license" aria-haspopup="dialog" @click="zoom = 'license'">
                      <img :src="rnd.profile.prc_license_image_url" alt="PRC license photo" />
                      <span><Maximize2 :size="13" aria-hidden="true" /> View full size</span>
                    </button>
                    <div v-else class="license license-missing">No license photo on file</div>
                  </div>
                  <div>
                    <p class="photo-label">Selfie with the license</p>
                    <button v-if="rnd.profile.prc_selfie_image_url" type="button" class="license" aria-haspopup="dialog" @click="zoom = 'selfie'">
                      <img :src="rnd.profile.prc_selfie_image_url" alt="Selfie holding the PRC license" />
                      <span><Maximize2 :size="13" aria-hidden="true" /> View full size</span>
                    </button>
                    <div v-else class="license license-missing">No selfie on file</div>
                  </div>
                </div>
                <dl class="facts">
                  <div><dt>PRC license no.</dt><dd class="mono">{{ rnd.profile.prc_license_number || 'Not given' }}</dd></div>
                  <div><dt>Specialization</dt><dd>{{ rnd.profile.specialization || 'Not given' }}</dd></div>
                  <div><dt>Born</dt><dd>{{ dobText(rnd.profile.date_of_birth) }}</dd></div>
                  <div><dt>Approved</dt><dd>{{ rnd.profile.verified_at ? shortDate(rnd.profile.verified_at) : 'Not yet' }}</dd></div>
                </dl>
              </div>
            </section>

            <!-- the Find an RND card, as clients see it (gaps in gold) -->
            <section class="nm-panel uc">
              <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg></span><h2 class="nm-panel-title">What clients see</h2></div>
              <p v-if="requiredMissing.length" class="nm-panel-sub">Clients can't book them yet. Still to do: {{ requiredMissing.map(m => m.label.toLowerCase()).join('; ') }}.</p>
              <article class="preview">
                <p class="pv-fee">
                  <template v-if="Number(rnd.profile.consultation_fee) >= 100">{{ peso(rnd.profile.consultation_fee) }} per consultation</template>
                  <span v-else class="gap">{{ peso(rnd.profile.consultation_fee || 0) }}, below the ₱100 minimum</span>
                  <span class="nm-pill" :class="rnd.profile.available_for_new_clients ? 'green' : 'muted'">{{ rnd.profile.available_for_new_clients ? 'Taking new clients' : 'Not taking new clients' }}</span>
                </p>
                <p v-if="(rnd.profile.bio || '').trim()" class="pv-bio">{{ rnd.profile.bio }}</p>
                <span v-else class="gap">No bio yet</span>
                <div class="pv-chips">
                  <span v-for="l in rnd.languages" :key="l" class="chip">{{ String(l).replace(/ \(.*\)/, '') }}</span>
                  <span v-if="!rnd.languages.length" class="gap">No languages yet</span>
                </div>
                <div class="pv-formats">
                  <span v-for="m in rnd.profile.consultation_modes || []" :key="m" class="format"><component :is="MODE_ICONS[m] || Video" :size="13" aria-hidden="true" /> {{ MODE_LABELS[m] || m }}</span>
                </div>
                <p v-if="(rnd.profile.consultation_modes || []).includes('in_person')" class="pv-where">
                  <MapPin :size="13" aria-hidden="true" />
                  <span v-if="rnd.profile.clinic_address">{{ rnd.profile.clinic_address }}</span>
                  <span v-else class="gap">No clinic address, so in-person can't be booked</span>
                </p>
                <div class="pv-hours">
                  <CalendarClock :size="14" aria-hidden="true" />
                  <span v-if="hours.length" class="pv-hours-list"><span v-for="h in hours" :key="h">{{ h }}</span></span>
                  <span v-else>{{ rnd.profile.review_status === 'approved' ? 'No weekly hours set yet' : 'Weekly hours are added after approval' }}</span>
                </div>
              </article>
            </section>
          </div>

          <div class="file-col">
            <section class="nm-panel uc">
              <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3" /><path d="M21 9h-6a3 3 0 0 0 0 6h6z" /></svg></span><div class="uc-titles"><h2 class="nm-panel-title">Payout details</h2><p class="nm-panel-sub">Next payout {{ shortDate(rnd.earnings.next_payout_date) }}</p></div><NuxtLink to="/payouts" class="nm-panel-link">Payouts <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink></div>
              <p v-if="!rnd.payout_account" class="nm-note" style="margin: 0">No GCash or bank details yet. Their balance is held until they add them.</p>
              <dl v-else class="facts">
                <div><dt>Method</dt><dd>{{ rnd.payout_account.method_label }}<template v-if="rnd.payout_account.bank_name">, {{ rnd.payout_account.bank_name }}</template></dd></div>
                <div><dt>Account</dt><dd>{{ rnd.payout_account.account_name }}, <span class="mono">{{ rnd.payout_account.account_number }}</span></dd></div>
                <div><dt>Last updated</dt><dd>{{ shortDate(rnd.payout_account.updated_at) }}</dd></div>
              </dl>
            </section>
            <section class="nm-panel uc">
              <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l3 2" /></svg></span><h2 class="nm-panel-title">Admin history</h2><NuxtLink :to="`/admin-appointments?view=all&rnd=${u.id}`" class="nm-panel-link">Appointments <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink></div>
              <p v-if="!data.recent_activity.length" class="nm-muted uc-empty-line">Nothing recorded yet.</p>
              <div v-else class="history-wrap">
              <template v-for="g in historyDays" :key="g.day">
                <p class="tl-day"><span>{{ g.day }}</span></p>
                <ol class="history">
                  <li v-for="(it, i) in g.items" :key="i" :class="{ fresh: it.fresh }">
                    <span class="h-dot" aria-hidden="true"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg></span>
                    <span class="h-card">
                      <span class="h-main">
                        <span class="h-title">{{ auditLabel(it.a.action) }}</span>
                        <span v-if="it.a.by" class="h-by"><i class="h-av">{{ initialsOf(it.a.by) }}</i>{{ it.a.by }}</span>
                      </span>
                      <span class="h-time" :title="dateTime(it.a.created_at)">{{ it.time }}</span>
                    </span>
                  </li>
                </ol>
              </template>
            </div>
            </section>
          </div>
        </div>
      </template>

      <!-- ADMIN: the header and the history -->
      <section v-if="!client && !rnd" class="nm-panel uc">
        <div class="uc-head"><span class="uc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /><path d="M12 7v5l3 2" /></svg></span><h2 class="nm-panel-title">Admin history</h2></div>
        <p v-if="!data.recent_activity.length" class="nm-muted uc-empty-line">Nothing recorded yet.</p>
        <div v-else class="history-wrap">
              <template v-for="g in historyDays" :key="g.day">
                <p class="tl-day"><span>{{ g.day }}</span></p>
                <ol class="history">
                  <li v-for="(it, i) in g.items" :key="i" :class="{ fresh: it.fresh }">
                    <span class="h-dot" aria-hidden="true"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" /><circle cx="12" cy="12" r="3" /></svg></span>
                    <span class="h-card">
                      <span class="h-main">
                        <span class="h-title">{{ auditLabel(it.a.action) }}</span>
                        <span v-if="it.a.by" class="h-by"><i class="h-av">{{ initialsOf(it.a.by) }}</i>{{ it.a.by }}</span>
                      </span>
                      <span class="h-time" :title="dateTime(it.a.created_at)">{{ it.time }}</span>
                    </span>
                  </li>
                </ol>
              </template>
            </div>
      </section>
    </template>

    <!-- deactivate -->
    <div v-if="showDeactivate" class="nm-modal-overlay" @click.self="showDeactivate = false">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="deactivate-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="showDeactivate = false"><X :size="18" aria-hidden="true" /></button>
        <h3 id="deactivate-title" class="nm-modal-title">Deactivate {{ u.first_name }}'s account?</h3>
        <p class="nm-modal-text">
          They'll be signed out and won't be able to sign in. We'll email them the reason below. You can reactivate the account any time.
        </p>
        <p v-if="rnd" class="nm-note" style="margin: 0 0 12px">
          <strong>Their patients are let go right away:</strong> every upcoming consultation is cancelled (paid ones go to the Refunds tab in Billing and Commission)
          and their care ends, so the clients can choose another RND. Reactivating doesn't bring these back.
        </p>
        <label class="nm-label" for="deactivate-reason">Reason</label>
        <textarea id="deactivate-reason" v-model="reason" class="nm-input" rows="4" maxlength="1000"
          placeholder="For example: repeated no-shows and abusive messages to an RND." />
        <p v-if="reasonError" class="nm-field-error">{{ reasonError }}</p>
        <p v-else class="nm-hint">At least 10 characters. The user will see this.</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="showDeactivate = false">Keep account</button>
          <button class="nm-btn-danger solid" :disabled="busy" @click="deactivate">{{ busy ? 'Deactivating…' : 'Deactivate account' }}</button>
        </div>
      </div>
    </div>

    <!-- edit details -->
    <div v-if="showEdit" class="nm-modal-overlay" @click.self="showEdit = false">
      <form class="nm-modal edit-modal" role="dialog" aria-modal="true" aria-labelledby="edit-title" @submit.prevent="saveEdit">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="showEdit = false"><X :size="18" aria-hidden="true" /></button>
        <h3 id="edit-title" class="nm-modal-title">Edit {{ u.first_name }}'s details</h3>
        <p class="nm-modal-text">For correcting mistakes. The change is saved in the audit log and the user is emailed what changed{{ editForm.email !== u.email ? ' (at both the old and new email)' : '' }}.</p>
        <div class="edit-grid">
          <label class="edit-field"><span class="nm-label">First name</span>
            <input v-model="editForm.first_name" class="nm-input" maxlength="150" :class="{ invalid: editErrors.first_name }" />
            <small v-if="editErrors.first_name" class="nm-field-error">{{ editErrors.first_name }}</small></label>
          <label class="edit-field"><span class="nm-label">Last name</span>
            <input v-model="editForm.last_name" class="nm-input" maxlength="150" :class="{ invalid: editErrors.last_name }" />
            <small v-if="editErrors.last_name" class="nm-field-error">{{ editErrors.last_name }}</small></label>
          <label class="edit-field"><span class="nm-label">Email</span>
            <input v-model="editForm.email" type="email" class="nm-input" maxlength="254" :class="{ invalid: editErrors.email }" />
            <small v-if="editErrors.email" class="nm-field-error">{{ editErrors.email }}</small></label>
          <div class="edit-field"><label for="edit-phone" class="nm-label">Mobile number</label>
            <PhoneInput id="edit-phone" v-model="editForm.phone" label="mobile number" :rnd="!!rnd" :error="editErrors.phone" /></div>
          <template v-if="rnd">
            <label class="edit-field"><span class="nm-label">PRC license no.</span>
              <input v-model="editForm.prc_license_number" class="nm-input" inputmode="numeric" maxlength="7" placeholder="7 digits" :class="{ invalid: editErrors.prc_license_number }" />
              <small v-if="editErrors.prc_license_number" class="nm-field-error">{{ editErrors.prc_license_number }}</small></label>
            <div class="edit-field"><span class="nm-label">Specializations</span>
              <SpecializationPicker v-model="editSpecs" v-model:error="editSpecError" />
              <small v-if="editErrors.specialization" class="nm-field-error">{{ editErrors.specialization }}</small></div>
          </template>
        </div>
        <label class="nm-label" for="edit-reason">Reason for the change</label>
        <textarea id="edit-reason" v-model="editForm.reason" class="nm-input" rows="2" maxlength="500" placeholder="For example: the user emailed support because their last name was misspelled at sign-up." />
        <p v-if="editErrors.reason" class="nm-field-error">{{ editErrors.reason }}</p>
        <p v-else class="nm-hint">At least 10 characters. It's saved in the audit log and included in the email.</p>
        <p v-if="editErrors.detail" class="nm-error" style="margin-top: 10px">{{ editErrors.detail }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="showEdit = false">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="busy || !editChanged">{{ busy ? 'Saving…' : 'Save changes' }}</button>
        </div>
      </form>
    </div>

    <!-- LICENSE PHOTO, full size (same pop-up as RND Applications) -->
    <div v-if="zoom && zoomUrl" class="nm-modal-overlay" @click.self="zoom = null">
      <div class="nm-modal license-modal" role="dialog" aria-modal="true" aria-labelledby="license-title">
        <div class="lm-head nm-modal-head">
          <span class="lm-icon"><IdCard :size="18" aria-hidden="true" /></span>
          <div style="flex: 1; min-width: 0">
            <h3 id="license-title" class="nm-modal-title" style="margin: 0">{{ zoom === 'selfie' ? 'Selfie with the license' : 'PRC license' }}, {{ u.first_name }} {{ u.last_name }}</h3>
            <p class="nm-panel-sub">License no. {{ rnd.profile.prc_license_number || 'not given' }}</p>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="zoom = null"><X :size="18" aria-hidden="true" /></button>
        </div>
        <div class="lm-photo"><img :src="zoomUrl" :alt="zoom === 'selfie' ? 'Selfie holding the PRC license, full size' : 'PRC license photo, full size'" /></div>
        <div class="nm-modal-actions">
          <a :href="zoomUrl" target="_blank" rel="noopener noreferrer" class="nm-btn-soft"><ExternalLink :size="14" aria-hidden="true" /> Open in new tab</a>
          <button type="button" class="nm-btn-dark" @click="zoom = null">Done</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import {
  ArrowLeft, Ban, CalendarClock, CheckCircle2, ExternalLink, IdCard, KeyRound, MapPin, Maximize2, Pencil, RotateCcw, ShieldCheck,
  UserRound, Video, X,
} from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const { get, post, patch } = useApi()

const data = ref(null)
const loading = ref(true)
const error = ref('')
const busy = ref(false)
const toast = useToast() // the app's toast (2026-11-03)
const showDeactivate = ref(false)
const reason = ref('')
const reasonError = ref('')
const zoom = ref(null) // 'license' | 'selfie' while a photo is open full size
const zoomUrl = computed(() => (zoom.value === 'selfie' ? rnd.value?.profile.prc_selfie_image_url : rnd.value?.profile.prc_license_image_url) || '')
const MODE_ICONS = { video: Video, in_person: UserRound }

const u = computed(() => data.value?.user || {})
const account = computed(() => data.value?.account || {})
const client = computed(() => data.value?.client)
const rnd = computed(() => data.value?.rnd)
const s = computed(() => client.value?.latest_screening)
const isSelf = computed(() => u.value.id === auth.user?.id)
const roleLabel = computed(() => ({ client: 'Client', rnd: 'RND', admin: 'Admin' }[u.value.role] || u.value.role))
// Back to the list tab this user is on (Users keeps the tab in ?tab=)
const backTo = computed(() => ({ path: '/users', query: { tab: { client: 'clients', rnd: 'rnds', admin: 'admins' }[u.value.role] || 'clients' } }))
const backLabel = computed(() => ({ client: 'All clients', rnd: 'All RNDs', admin: 'All admins' }[u.value.role] || 'All users'))
const reviewLabel = computed(() => ({ pending: 'Application under review', approved: 'Approved', rejected: 'Rejected' }[rnd.value?.profile.review_status] || ''))
const reviewPill = computed(() => ({ pending: 'gold', approved: 'green', rejected: 'muted' }[rnd.value?.profile.review_status] || 'muted'))
const hours = computed(() => availabilityLines(rnd.value?.availability))
const requiredMissing = computed(() => (rnd.value?.missing_setup || []).filter(m => !m.optional))
const emergencyText = computed(() => {
  const p = client.value?.profile
  if (!p?.emergency_contact) return 'Not given'
  return p.emergency_phone ? `${p.emergency_contact}, ${formatPhone(p.emergency_phone) || p.emergency_phone}` : p.emergency_contact
})
// appointment counts by status ({ completed: 3, ... })
const appt = (who, k) => who?.appointments?.[k] || 0
// The strip under the name: the account at a glance; gold = not done yet.
const stripCells = computed(() => {
  const a = account.value
  const cells = [
    { label: 'Joined', value: shortDate(u.value.created_at) },
    { label: 'Last sign-in', value: a.last_login ? dateTime(a.last_login) : 'Never' },
    { label: 'Email', value: a.email_verified_at ? `Confirmed ${shortDate(a.email_verified_at)}` : 'Not confirmed', warn: !a.email_verified_at },
  ]
  if (client.value || (rnd.value && rnd.value.profile.review_status === 'approved')) cells.push({ label: rnd.value ? 'Setup' : 'Onboarding', value: a.onboarding_completed_at ? `Finished ${shortDate(a.onboarding_completed_at)}` : 'Not finished', warn: !a.onboarding_completed_at })
  if (rnd.value) cells.push({ label: 'Application', value: reviewLabel.value || 'Not sent', warn: rnd.value.profile.review_status === 'pending' })
  if (u.value.role !== 'admin') {
    const both = a.terms_accepted_at && a.data_consent_at
    cells.push({ label: 'Consent (RA 10173)', value: both ? `Given ${shortDate(a.data_consent_at)}` : 'Missing', warn: !both })
  }
  return cells
})
// empty fields are simply left out; this only tells when nothing is filled in
const personalMissing = computed(() => {
  const p = client.value?.profile || {}
  return [['date of birth', p.date_of_birth], ['sex', p.sex], ['address', p.address], ['emergency contact', p.emergency_contact]]
    .filter(([, v]) => !v).map(([k]) => k)
})

const allergyText = computed(() => {
  const a = client.value?.health.allergies
  if (a == null) return 'Not answered yet'
  return listText(a) || 'No known allergies'
})

// set in setup so the title goes away with the page (useHead after an await
// is outside the component and stuck on every later page)
useHead({ title: computed(() => data.value?.user ? `${data.value.user.first_name} ${data.value.user.last_name}, NutriMatch admin` : 'NutriMatch') })

async function load({ quiet = false } = {}) {
  if (!quiet) {
    loading.value = true
    error.value = ''
  }
  try {
    data.value = await get(`/admin/users/${route.params.id}/overview/`)
  } catch (e) {
    if (!quiet) error.value = e?.response?.status === 404 ? 'This account doesn\'t exist.' : 'Could not load this account. Please refresh.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
// Refreshes every 5 minutes, but never a client's record: each load of it
// writes a "record viewed" audit row (RA 10173), which must mean a person
// looked, not a timer.
useAutoRefresh(() => load({ quiet: true }), { interval: 300000, paused: () => !data.value || data.value.user?.role === 'client' })

function flash(msg, opts) {
  toast.success(msg, opts)
}

/* ---------- edit details (PATCH /api/admin/users/<id>/edit/, accounts/admin_edit.py) ---------- */
const EDIT_FIELDS = ['first_name', 'last_name', 'email', 'phone', 'prc_license_number', 'specialization']
const showEdit = ref(false)
const editForm = reactive({ reason: '' })
const editErrors = ref({})
// up to 3, one may be typed; the API stores them as one comma-joined text
const editSpecs = ref([])
const editSpecError = ref('')
watch(editSpecs, v => { editForm.specialization = v.join(', ') })
const editBefore = computed(() => ({
  first_name: u.value.first_name || '', last_name: u.value.last_name || '', email: u.value.email || '', phone: u.value.phone || '',
  ...(rnd.value ? { prc_license_number: rnd.value.profile.prc_license_number || '', specialization: rnd.value.profile.specialization || '' } : {}),
}))
const editChanged = computed(() => Object.keys(editBefore.value).some(k => String(editForm[k] ?? '').trim() !== editBefore.value[k]))
async function openEdit() {
  Object.assign(editForm, editBefore.value, { reason: '' })
  editSpecs.value = (editBefore.value.specialization || '').split(',').map(x => x.trim()).filter(Boolean)
  editErrors.value = {}
  showEdit.value = true
}
async function saveEdit() {
  editErrors.value = {}
  if (editForm.reason.trim().length < 10) {
    editErrors.value = { reason: 'Explain the change in at least 10 characters.' }
    return
  }
  const phoneMsg = editForm.phone === editBefore.value.phone ? ''
    : rnd.value && !editForm.phone ? 'RNDs must have a mobile number. Enter a Philippine mobile, for example +63 917 123 4567.'
    : (rnd.value ? rndPhoneError : phoneError)(editForm.phone)
  if (phoneMsg) {
    editErrors.value = { phone: phoneMsg }
    return
  }
  if (rnd.value && (editSpecError.value || !editSpecs.value.length)) {
    editErrors.value = { specialization: editSpecError.value || 'Pick at least one specialization.' }
    return
  }
  if (rnd.value) editForm.specialization = editSpecs.value.join(', ')
  const body = { reason: editForm.reason.trim() }
  for (const k of EDIT_FIELDS) {
    if (k in editBefore.value && String(editForm[k] ?? '').trim() !== editBefore.value[k]) body[k] = String(editForm[k] ?? '').trim()
  }
  busy.value = true
  try {
    await patch(`/admin/users/${u.value.id}/edit/`, body)
    showEdit.value = false
    await load()
    flash('Details updated. We emailed the user.')
  } catch (e) {
    const d = e?.data || {}
    editErrors.value = Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]))
    if (!Object.keys(editErrors.value).length) editErrors.value = { detail: apiError(e) }
  } finally {
    busy.value = false
  }
}

function openDeactivate() {
  reason.value = ''
  reasonError.value = ''
  showDeactivate.value = true
}

async function deactivate() {
  reasonError.value = ''
  if (reason.value.trim().length < 10) {
    reasonError.value = 'Explain why in at least 10 characters. The user will see this.'
    return
  }
  busy.value = true
  try {
    const res = await post(`/admin/users/${u.value.id}/deactivate/`, { reason: reason.value.trim() })
    showDeactivate.value = false
    await load()
    const n = res?.consultations_cancelled || 0, m = res?.care_ended || 0
    flash('Account deactivated. We emailed the user.'
      + (n ? ` ${n} consultation${n === 1 ? '' : 's'} cancelled.` : '')
      + (m ? ` Care ended for ${m} client${m === 1 ? '' : 's'}.` : ''))
  } catch (e) {
    reasonError.value = apiError(e)
  } finally {
    busy.value = false
  }
}

async function reactivate() {
  busy.value = true
  error.value = ''
  try {
    await post(`/admin/users/${u.value.id}/reactivate/`)
    await load()
    flash('Account reactivated. We emailed the user.')
  } catch (e) {
    toast.error(apiError(e, 'Could not reactivate this account. Please try again.'))
  } finally {
    busy.value = false
  }
}

async function sendReset() {
  busy.value = true
  error.value = ''
  try {
    await post(`/admin/users/${u.value.id}/send-password-reset/`)
    await load()
    flash(`Password reset code sent to ${u.value.email}.`)
  } catch (e) {
    toast.error(apiError(e, 'Could not send the reset code. Please try again.'))
  } finally {
    busy.value = false
  }
}

function cap(v) {
  if (!v) return ''
  const t = String(v).replace(/_/g, ' ')
  return t.charAt(0).toUpperCase() + t.slice(1)
}
function listText(v) {
  return Array.isArray(v) ? v.filter(Boolean).join(', ') : (v || '')
}
function num(v) {
  return v == null ? '—' : Number(v).toLocaleString('en-PH', { maximumFractionDigits: 1 })
}
function dobText(dob) {
  return dob ? `${shortDate(dob)} (${ageFrom(dob)} yrs)` : 'Not given'
}
function countText(counts) {
  const entries = Object.entries(counts || {})
  if (!entries.length) return 'None yet'
  return entries.map(([k, n]) => `${n} ${cap(k).toLowerCase()}`).join(', ')
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// icons for the strip under the header (SVG path data)
const STRIP_ICON = {
  Joined: ['M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z', 'M16 3v4M8 3v4M3 10h18'],
  'Last sign-in': ['M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4', 'M10 17l5-5-5-5M15 12H3'],
  Email: ['M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z', 'M22 6l-10 7L2 6'],
  Onboarding: ['M4 21V4M4 4h12l-2 4 2 4H4'],
  Setup: ['M4 21V4M4 4h12l-2 4 2 4H4'],
  Application: ['M12 2l2.4 3.2 4-.6.6 4L22 11l-3 2.6.6 4-4-.6L12 20l-2.4-3.2-4 .6-.6-4L2 11l3-2.4-.6-4 4 .6z', 'M9 11l2 2 4-4'],
  'Consent (RA 10173)': ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z', 'M9 12l2 2 4-4'],
}
// admin history grouped by day; the last 24 hours in gold
const historyDays = computed(() => {
  const out = []
  for (const a of data.value?.recent_activity || []) {
    const d = new Date(a.created_at)
    const day = d.toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
    let g = out.find(x => x.day === day)
    if (!g) out.push(g = { day, items: [] })
    g.items.push({ a, time: d.toLocaleTimeString('en-PH', { hour: 'numeric', minute: '2-digit' }), fresh: Date.now() - d.getTime() < 86400000 })
  }
  return out
})
const initialsOf = name => { const w = String(name || '?').split(' ').filter(Boolean); return (w.length > 1 ? w[0][0] + w[w.length - 1][0] : (w[0] || '?')[0]).toUpperCase() }
</script>
<style scoped>
.nm-page { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; display: inline-block; }
.back-link { display: inline-flex; align-items: center; gap: 7px; height: 36px; margin-bottom: 14px; padding: 0 14px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); font-size: 13px; font-weight: 800; color: #004d3a; text-decoration: none; }
.back-link:hover { background: #f1f6f2; }
.ud-loading { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 40px 20px; border-radius: 22px; background: #fff; box-shadow: var(--sh); font-weight: 600; }
.ud-spin { width: 20px; height: 20px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: ud-spin 0.8s linear infinite; }
@keyframes ud-spin { to { transform: rotate(360deg); } }

/* ---------- header: green identity, then the account strip ---------- */
.file-head { margin-bottom: 18px; padding: 0; border: none; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: hidden; }
.fh-top {
  position: relative; overflow: hidden; display: flex; align-items: center; justify-content: space-between; gap: 18px 24px; flex-wrap: wrap; padding: 26px 30px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%);
}
.fh-top > *:not(.ud-plate):not(.ud-fade) { position: relative; z-index: 1; }
.ud-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.ud-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 55%, rgba(0, 77, 58, 0.9) 74%, rgba(0, 77, 58, 0.72) 100%); }
.identity-main { display: flex; align-items: center; gap: 20px; min-width: 0; }
.identity-main .nm-avatar.lg { flex-shrink: 0; width: 84px; height: 84px; border-radius: 50%; object-fit: cover; box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; border: 3px solid rgba(255, 255, 255, 0.9); box-shadow: 0 0 0 5px rgba(255, 255, 255, 0.14); }
.ud-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 6px; font-size: 11px; font-weight: 800; color: #efbf04; }
.ud-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.fh-top .nm-page-title { font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 700; line-height: 1.15; letter-spacing: 0.01em; color: #fff; }
.fh-top .nm-page-sub { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; margin: 6px 0 0; font-size: 14px; color: rgba(255, 255, 255, 0.85); }
.fh-top .nm-page-sub .ic { color: #efbf04; }
.pill-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
.pill-row .nm-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.pill-row .nm-pill.muted { background: rgba(255, 255, 255, 0.14); border: 1px solid rgba(255, 255, 255, 0.2); color: #fff; }
.pill-row .nm-pill.green { background: #e3f4ea; color: #1f7a4d; }
.pill-row .nm-pill.green::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.pill-row .nm-pill.gold { background: #fff4d6; color: #8a6500; }
.identity-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-right: 110px; }
.identity-actions > button { display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 42px; padding: 0 16px; border-radius: 12px; font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; transition: background 0.15s; }
.identity-actions .nm-btn-soft { background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.25); color: #fff; backdrop-filter: blur(6px); }
.identity-actions .nm-btn-soft:hover:not(:disabled) { background: rgba(255, 255, 255, 0.18); }
.identity-actions .nm-btn-danger { background: #fff; border: 1px solid #fff; color: #b42318; box-shadow: none; }
.identity-actions .nm-btn-danger:hover:not(:disabled) { background: #fdecea; }
.identity-actions .nm-btn-dark { background: #efbf04; border: 1px solid #efbf04; color: #004d3a; }
.identity-actions > button:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
.identity-actions > button:disabled { opacity: 0.6; cursor: not-allowed; }
.fh-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); margin: 0; }
.fh-strip > div { display: grid; grid-template-columns: 36px minmax(0, 1fr); grid-template-rows: auto auto; column-gap: 12px; align-items: center; min-width: 0; padding: 16px 18px; border-left: 1px solid #eef2ef; }
.fh-strip > div:first-child { border-left: none; }
.fh-ico { grid-row: 1 / 3; width: 36px; height: 36px; border-radius: 11px; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.fh-strip dt { font-size: 12px; color: #8a9a91; }
.fh-strip dd { margin: 0; font-size: 14px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.fh-strip .warn .fh-ico { background: #fff4d6; color: #8a6500; }
.fh-strip .warn dd { color: #8a6500; }
.fh-audit { display: flex; align-items: center; gap: 8px; margin: 0; padding: 10px 18px; border-top: 1px solid #e3e8f5; background: #eef1fa; font-size: 13px; color: #2e4a86; }

/* ---------- body ---------- */
.file-grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 18px; align-items: start; }
.file-col { display: flex; flex-direction: column; gap: 18px; min-width: 0; }
.nm-panel.uc { padding: 20px 24px 22px; border: none; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: hidden; }
.uc-head { display: flex; align-items: center; gap: 10px; margin: -20px -24px 18px; padding: 16px 24px; background: #f1f8f4; border-bottom: 1px solid #e3efe7; }
.uc-ico { flex-shrink: 0; width: 34px; height: 34px; border-radius: 11px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.uc-head .nm-panel-title { flex: 1; margin: 0; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.uc-titles { flex: 1; min-width: 0; }
.uc-titles .nm-panel-sub { margin: 2px 0 0; font-size: 12.5px; color: #6b7d73; }
.uc-head .nm-panel-link { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; border: 1px solid #dce8e0; border-radius: 10px; background: #fff; color: #004d3a; font-size: 12.5px; font-weight: 800; text-decoration: none; white-space: nowrap; }
.uc-head .nm-panel-link:hover { background: #f1f6f2; }
.uc-count { padding: 4px 11px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px #dce8e0; font-size: 12px; font-weight: 700; color: #1f5c45; }
.uc-empty-line { margin: 0; padding: 14px; border-radius: 14px; background: #f7faf8; font-size: 13.5px; }
.uc .nm-panel-sub { margin: 0 0 4px; font-size: 13px; color: #6b7d73; }
.uc-none { display: flex; flex-direction: column; align-items: center; gap: 8px; margin: 0; padding: 22px 16px; border-radius: 16px; border: 1.5px dashed #cfddd4; text-align: center; font-size: 13.5px; font-weight: 600; color: #4a5a52; }
.uc-none span { width: 48px; height: 48px; border-radius: 14px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }

/* care */
.care-rnds { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 14px; margin: 0 0 14px; font-size: 14px; }
.care-rnds .label { font-size: 12px; color: #8a9a91; }
.care-rnd { display: inline-flex; align-items: center; gap: 6px; font-weight: 700; }
.care-empty { display: flex; align-items: center; gap: 8px; width: 100%; padding: 10px 12px; border-radius: 12px; background: #f7faf8; color: #4a5a52; }
.care-empty .ic { color: #1f7a4d; }

/* figures: small tiles */
.figs { display: grid; gap: 10px; }
.figs.four { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.figs.six { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.figs > div { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; min-width: 0; padding: 14px; border: 1.5px solid #c9d8cf; border-radius: 16px; background: #fff; }
.fig-ico { width: 28px; height: 28px; margin-bottom: 6px; border-radius: 9px; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.figs strong { font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 700; line-height: 1.15; color: #0e3a2c; font-variant-numeric: lining-nums tabular-nums; overflow-wrap: anywhere; }
.figs span { font-size: 12.5px; line-height: 1.3; color: #6b7d73; }
.figs .risk { background: #fef3f2; border-color: #eba79f; }
.figs .risk strong { color: #b42318; }
.figs-panel { margin-bottom: 18px; padding: 18px; border: none; border-radius: 24px; box-shadow: var(--sh); }

/* facts: small boxes */
.facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0; }
.facts > div { min-width: 0; padding: 12px 14px; border: 1.5px solid #e3ebe6; border-radius: 14px; }
.facts dt { margin-bottom: 4px; font-size: 12px; color: #8a9a91; }
.facts dd { margin: 0; font-size: 14.5px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.chip { display: inline-flex; padding: 4px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 700; background: #e3f4ea; color: #1f5c45; }
.chip.blue { background: #eef1fa; color: #2e4a86; }
.allergy-list { display: flex; flex-wrap: wrap; gap: 6px; }
.allergy { padding: 4px 11px; border-radius: 999px; border: 1px solid #f6c9c3; background: #fdecea; font-size: 12.5px; font-weight: 800; color: #b42318; }
.gap { display: inline-flex; align-self: flex-start; padding: 4px 11px; border-radius: 999px; background: #fff4d6; font-size: 12.5px; font-weight: 700; color: #8a6500; }

/* admin history: grouped by day, one card per event */
.history-wrap { position: relative; }
.tl-day { margin: 0 0 10px; padding-left: 50px; }
.tl-day:not(:first-child) { margin-top: 16px; }
.tl-day span { display: inline-flex; padding: 3px 10px; border-radius: 999px; background: #f1f6f2; font-size: 11.5px; font-weight: 800; color: #4a5a52; }
.history { position: relative; list-style: none; margin: 0; padding: 0; }
.history::before { content: ''; position: absolute; left: 17px; top: 18px; bottom: 18px; width: 2px; border-radius: 2px; background: #dce8e0; }
.history li { position: relative; display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.history li:last-child { margin-bottom: 0; }
.h-dot { position: relative; z-index: 1; flex-shrink: 0; width: 36px; height: 36px; border-radius: 50%; background: #e3f4ea; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 0 0 4px #fff; }
.history li.fresh .h-dot { background: #efbf04; color: #004d3a; }
.h-card { flex: 1; min-width: 0; display: flex; align-items: center; gap: 12px; padding: 10px 12px; border: 1.5px solid #e3ebe6; border-radius: 14px; background: #fff; }
.history li.fresh .h-card { background: #fffbea; border-color: #f3e2a0; }
.h-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.h-title { font-size: 14px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.h-by { display: flex; align-items: center; gap: 6px; margin-top: 4px; font-size: 12.5px; color: #6b7d73; }
.h-av { width: 20px; height: 20px; border-radius: 50%; background: #004d3a; color: #efbf04; font-style: normal; font-size: 9px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }
.h-time { flex-shrink: 0; padding: 4px 10px; border-radius: 999px; background: #f3f6f4; font-size: 12px; font-weight: 700; color: #4a5a52; white-space: nowrap; }
.history li.fresh .h-time { background: #fff; color: #8a6500; }

/* RND: credentials + the client-facing card */
.cred { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); gap: 14px; align-items: start; }
.photos { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.photos > div { min-width: 0; border: 1.5px solid #c9d8cf; border-radius: 16px; overflow: hidden; }
.photo-label { margin: 0; padding: 10px 12px; border-bottom: 1px solid #eef2ef; font-size: 13px; font-weight: 800; color: #0e3a2c; }
.license { display: block; width: 100%; padding: 0; border: none; border-radius: 0; overflow: hidden; background: #f1f4f2; font-family: inherit; text-align: left; cursor: zoom-in; }
.license:hover img { opacity: 0.92; }
.license:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.license img, .photos .license img { display: block; width: 100%; height: 190px; max-height: none; object-fit: cover; background: #f1f4f2; }
.license span { display: flex; align-items: center; justify-content: center; gap: 7px; height: 40px; border-top: 1px solid #eef2ef; background: #f7faf8; font-size: 13px; font-weight: 800; color: #004d3a; }
.license-missing, .photos .license-missing { min-height: 230px; display: flex; align-items: center; justify-content: center; padding: 30px 14px; background: #fdecea; color: #b42318; font-size: 13px; font-weight: 700; text-align: center; cursor: default; }
.cred .facts { grid-template-columns: 1fr; gap: 8px; }
.preview { display: flex; flex-direction: column; gap: 10px; margin-top: 14px; padding: 16px; border: 1.5px solid #c9d8cf; border-radius: 16px; overflow-wrap: anywhere; }
.pv-fee { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin: 0; font-size: 14px; font-weight: 700; color: #0e3a2c; }
.pv-fee .nm-pill { padding: 4px 11px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.pv-fee .nm-pill.green { background: #e3f4ea; color: #1f7a4d; }
.pv-fee .nm-pill.muted { background: #f3f6f4; color: #6b7d73; }
.pv-bio { margin: 0; font-size: 13.5px; line-height: 1.55; color: #4a5a52; white-space: pre-line; }
.pv-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.pv-formats { display: flex; flex-wrap: wrap; gap: 8px; }
.format { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px; background: #eef1fa; font-size: 12.5px; font-weight: 700; color: #2e4a86; }
.pv-where { display: flex; align-items: flex-start; gap: 6px; margin: 0; font-size: 13px; line-height: 1.4; color: #4a5a52; }
.pv-where svg { flex-shrink: 0; margin-top: 2px; color: #1f7a4d; }
.pv-hours { display: flex; align-items: flex-start; gap: 8px; padding: 10px 12px; border-radius: 12px; background: #f1f8f4; color: #1f5c45; font-size: 13px; line-height: 1.45; }
.pv-hours svg { flex-shrink: 0; margin-top: 1px; }
.pv-hours-list { display: flex; flex-direction: column; gap: 2px; }
.mono { font-variant-numeric: tabular-nums; letter-spacing: 0.04em; }
.file-col > .nm-note { border-radius: 14px; }

/* pop-ups */
.license-modal { max-width: 900px; }
.lm-head { display: flex; gap: 12px; align-items: flex-start; }
.lm-icon { flex-shrink: 0; width: 40px; height: 40px; border-radius: 12px; background: #004d3a; color: #efbf04; display: flex; align-items: center; justify-content: center; }
.lm-photo { margin-top: 16px; border: 1px solid #e3ebe6; border-radius: 16px; overflow: auto; background: #f7faf8; display: flex; justify-content: center; }
.lm-photo img { display: block; max-width: 100%; max-height: 70vh; object-fit: contain; }
.edit-modal { max-width: 560px; }
.edit-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.edit-field { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.edit-field .nm-label { margin: 0; font-size: 13px; font-weight: 700; color: #22362c; }
.edit-field .nm-input { border: 1.5px solid #c9d8cf; border-radius: 12px; }
.edit-field .nm-input:focus { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); outline: none; }
.edit-field input.nm-input { min-height: 44px; }
.edit-field .nm-input.invalid { border-color: #e0a3a3; background: #fffafa; }

@media (max-width: 1100px) {
  .figs.six { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (max-width: 960px) {
  .fh-top { padding: 20px 18px; }
  .ud-plate { width: 170px; height: 170px; right: -60px; top: 10px; transform: none; }
  .identity-main .nm-avatar.lg { width: 64px; height: 64px; font-size: 22px; }
  .fh-top .nm-page-title { font-size: 24px; }
  .identity-actions { width: 100%; margin-right: 0; }
  .identity-actions > button { flex: 1; padding: 0 10px; font-size: 12.5px; }
  .fh-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fh-strip > div { grid-template-columns: 30px minmax(0, 1fr); padding: 12px; border-left: none; border-top: 1px solid #eef2ef; }
  .fh-strip > div:nth-child(-n + 2) { border-top: none; }
  .fh-strip > div:nth-child(even) { border-left: 1px solid #eef2ef; }
  .fh-ico { width: 30px; height: 30px; }
  .fh-strip dd { font-size: 13px; }
  .file-grid { grid-template-columns: minmax(0, 1fr); }
  .nm-panel.uc { padding: 18px 16px 18px; }
  .uc-head { margin: -18px -16px 14px; padding: 14px 16px; }
}
@media (max-width: 760px) {
  .nm-page { padding-bottom: 110px; }
}
@media (max-width: 640px) {
  .identity-main { align-items: flex-start; }
  .figs.four, .figs.six { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .facts { grid-template-columns: minmax(0, 1fr); }
  .cred, .photos { grid-template-columns: minmax(0, 1fr); }
  .license-modal { max-width: none; height: 100%; max-height: none; border-radius: 0; display: flex; flex-direction: column; }
  .lm-photo { flex: 1; align-items: center; }
}
@media (max-width: 560px) { .edit-grid { grid-template-columns: minmax(0, 1fr); } }
</style>