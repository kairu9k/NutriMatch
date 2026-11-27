<template>
  <div class="nm-page">
    <p class="crumb"><NuxtLink to="/my-patients">My Patients</NuxtLink> / {{ p?.client.name || 'Patient' }}</p>
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <div v-if="loading" class="nm-panel"><p class="nm-muted">Loading patient…</p></div>

    <template v-else-if="s">
      <!-- HEADER: who, status, the next step; Discharge lives in the More menu -->
      <section class="nm-panel patient-head">
        <img class="ph-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="ph-fade" aria-hidden="true"></span>
        <div class="ph-top">
          <div class="ph-who">
            <img v-if="p.client.profile_photo" :src="p.client.profile_photo" class="ph-avatar" alt="" />
            <span v-else class="ph-avatar">{{ userInitials(p.client.first_name, p.client.last_name) }}</span>
            <div class="ph-info">
              <h1 class="ph-name">{{ p.client.name }}</h1>
              <p v-if="metaLine" class="ph-meta"><template v-for="(m, i) in metaParts" :key="i"><i v-if="i" aria-hidden="true"></i>{{ m }}</template></p>
              <p class="ph-status">
                <span class="ph-pill" :class="p.status"><b aria-hidden="true"></b>{{ STATUS_LABEL[p.status] }}</span>
                <span v-if="p.started_at && p.status !== 'pending'" class="ph-since">Patient since {{ shortDate(p.started_at) }}</span>
              </p>
            </div>
          </div>
          <div class="ph-actions">
            <NuxtLink v-if="p.status === 'active' && p.stage.next_step.key !== 'open'" :to="p.stage.next_step.link" class="nm-btn-gold">{{ p.stage.next_step.label }}</NuxtLink>
            <NuxtLink :to="`/messages?relationship=${relationshipId}`" class="nm-btn-outline ph-btn">
              <MessageSquare :size="15" /> {{ p.status === 'discharged' ? 'Message history' : 'Message' }}
              <span v-if="p.unread_messages" class="ph-badge">{{ p.unread_messages }}</span>
            </NuxtLink>
            <button v-if="p.status === 'active'" type="button" class="nm-btn-outline ph-btn" @click="requestLabs"><FlaskConical :size="15" /> Request lab tests</button>
            <div v-if="p.status === 'active'" class="more-wrap">
              <button type="button" class="more-btn" aria-label="More actions" aria-haspopup="menu" :aria-expanded="moreOpen" @click.stop="moreOpen = !moreOpen">
                <MoreHorizontal :size="18" />
              </button>
              <div v-if="moreOpen" class="more-menu" role="menu" @click.stop>
                <button type="button" role="menuitem" class="more-item danger" @click="moreOpen = false; showDischarge = true">Discharge patient…</button>
              </div>
            </div>
          </div>
        </div>
        <!-- allergies stay in the header so they're never missed (patient safety) -->
        <p v-if="s.health.allergies.length" class="ph-allergy" role="note">
          <span class="ph-allergy-ico"><AlertTriangle :size="14" /></span><span><strong>Food allergy:</strong> {{ s.health.allergies.join(', ') }}. Check every food in their plan against this.</span>
        </p>
      </section>

      <!-- The client asked to end care (Profile Settings -> Care Team): close it
           properly with a note, or it ends on its own on the date shown. -->
      <section v-if="p.status === 'active' && s.discharge_request" class="nm-note dr-banner" role="status">
        <div>
          <strong>{{ p.client.first_name }} asked to end their care</strong> on {{ shortDate(s.discharge_request.requested_at) }}.
          Reason: {{ s.discharge_request.reason_label }}.<template v-if="s.discharge_request.note"> "{{ s.discharge_request.note }}"</template>
          Discharge them with a closing note by <strong>{{ shortDate(s.discharge_request.ends_at) }}</strong>. After that, it ends automatically.
        </div>
        <button type="button" class="nm-btn-dark" @click="showDischarge = true">Discharge now</button>
      </section>

      <section v-if="p.status === 'discharged'" class="nm-note plain-note">
        <strong>Discharged{{ p.ended_at ? ` on ${shortDate(p.ended_at)}` : '' }}.</strong>
        This record is read-only.<template v-if="p.discharge_reason"> Reason: "{{ p.discharge_reason }}"</template>
        If {{ p.client.first_name }} books you again, it reopens when you confirm the booking.
      </section>
      <section v-else-if="p.status === 'pending'" class="nm-note todo-note">
        <strong>New booking.</strong> {{ p.client.first_name }} becomes your patient once you confirm their booking.
        <NuxtLink to="/appointments?tab=requests" class="nm-panel-link">Review booking</NuxtLink>
      </section>

      <nav class="nm-tabs tabs" role="tablist" aria-label="Patient sections">
        <button v-for="t in TABS" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" role="tab"
                :aria-selected="tab === t.key" @click="setTab(t.key)">
          {{ t.label }}<span v-if="t.count != null" class="nm-count">{{ t.count }}</span>
        </button>
      </nav>

      <!-- ===================== OVERVIEW ===================== -->
      <template v-if="tab === 'overview'">
        <div v-if="p.alerts.length" class="nm-panel attention">
          <div v-for="(a, i) in p.alerts" :key="i" class="alert" :class="a.level">
            <span class="alert-icon"><component :is="ALERT_ICONS[a.level]" :size="15" /></span>
            <p class="alert-title">{{ a.title }}</p>
            <NuxtLink v-if="p.status === 'active' && a.action === 'Open patient'" :to="`/messages?relationship=${relationshipId}`" class="nm-btn-outline nm-btn-sm">Message</NuxtLink>
            <NuxtLink v-else-if="p.status === 'active'" :to="a.link" class="nm-btn-outline nm-btn-sm">{{ a.action }}</NuxtLink>
          </div>
        </div>

        <div class="figures">
          <div class="fig" style="--c: #004D3A">
            <p class="fig-top"><span class="fig-label">Current weight</span><span class="fig-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 21h14a1 1 0 0 0 1-1l-1.5-13a1 1 0 0 0-1-1h-11a1 1 0 0 0-1 1L4 20a1 1 0 0 0 1 1z" /><path d="M12 6V3M9.5 12a2.5 2.5 0 0 1 5 0M12 12l1.5-2" /></svg></span></p>
            <p class="fig-value">{{ p.progress.latest_weight_kg != null ? `${fmt1(p.progress.latest_weight_kg)} kg` : '—' }}</p>
            <p class="fig-note">{{ figureSource(p.progress.weight_origin) || 'Not measured yet' }}</p>
            <p v-if="p.progress.weight_change_kg != null" class="fig-note">{{ signed(p.progress.weight_change_kg) }} kg since screening</p>
          </div>
          <div class="fig" style="--c: #9A7300">
            <p class="fig-top"><span class="fig-label">BMI</span><span class="fig-ico" style="background: #FBF3D2; color: #9A7300"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="4.5" r="2" /><path d="M8 22l1-8-3-1 2-6h8l2 6-3 1 1 8" /></svg></span></p>
            <p class="fig-value">{{ p.progress.bmi != null ? fmt1(p.progress.bmi) : '—' }}</p>
            <p class="fig-note">{{ p.progress.bmi_class ? `${p.progress.bmi_class}, Asia-Pacific` : 'Not measured yet' }}</p>
            <p v-if="p.progress.bmi_origin" class="fig-note">From the weight on {{ figureSource(p.progress.bmi_origin) }}</p>
          </div>
          <div class="fig" style="--c: #3B5BA5">
            <p class="fig-top"><span class="fig-label">7-day meal-plan adherence</span><span class="fig-ico" style="background: #EEF1FA; color: #3B5BA5"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg></span></p>
            <p class="fig-value">{{ p.adherence?.pct != null ? `${p.adherence.pct}%` : '—' }}</p>
            <p class="fig-note">{{ p.adherence ? `${p.adherence.logged} of ${p.adherence.planned} meals logged` : 'No meal plan sent yet' }}</p>
          </div>
          <div class="fig" :class="{ risk: (s.screening?.nrs_score ?? 0) >= 3 }" :style="{ '--c': (s.screening?.nrs_score ?? 0) >= 3 ? '#B42318' : '#1F7A4D' }">
            <p class="fig-top"><span class="fig-label">NRS-2002 score</span><span class="fig-ico" style="background: #EAF4EE; color: #1F7A4D"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg></span></p>
            <p class="fig-value">{{ s.screening?.nrs_score ?? '—' }}</p>
            <p class="fig-note">{{ s.screening ? (s.screening.nrs_risk || 'Not scored') : 'No screening yet' }}</p>
            <p v-if="s.screening" class="fig-note">{{ screeningSource(s.screening).replace(/^f/, 'F') }}</p>
          </div>
        </div>

        <div class="nm-grid">
          <div class="nm-col">
            <!-- care stage -->
            <div class="nm-panel">
              <div class="pc-head"><span class="pc-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 2l4 4-4 4" /><path d="M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4" /><path d="M21 13v2a3 3 0 0 1-3 3H3" /></svg></span><div><h2 class="nm-panel-title">Care process</h2><p class="nm-panel-sub">Nutrition Care Process for this patient</p></div></div>
              <ol class="stepper">
                <li v-for="(st, i) in stageSteps" :key="st.label" :class="[st.state, { next: i === nextStepIndex }]">
                  <span class="dot">
                    <Check v-if="st.state === 'done'" :size="16" :stroke-width="3" />
                    <svg v-else class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="STEP_ICONS[i]" />
                  </span>
                  <span class="st-label">{{ st.label }}</span>
                  <span class="st-sub">{{ st.sub }}</span>
                  <span v-if="i === nextStepIndex" class="st-next">{{ st.state === 'current' ? 'In progress' : 'Up next' }}</span>
                </li>
              </ol>
            </div>

            <!-- current care plan -->
            <div class="nm-panel">
              <div class="nm-panel-head">
                <div class="pc-head"><span class="pc-ico" style="background: #FBF3D2; color: #9A7300"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6M9 17.5h3" /></svg></span><div>
                  <h2 class="nm-panel-title">Current diagnosis &amp; plan</h2>
                  <p class="nm-panel-sub">{{ s.care_plan ? `From the ${s.care_plan.is_follow_up ? 'follow-up' : 'initial'} NCP record of ${shortDate(s.care_plan.encounter_date)}` : 'From their latest finalized NCP record' }}</p>
                </div></div>
                <button v-if="ncpRecords.length" type="button" class="nm-panel-link" @click="setTab('ncp')">NCP records</button>
              </div>
              <p v-if="!s.care_plan" class="nm-muted">No finalized NCP record yet.{{ s.ncp_draft_id ? ' A draft is in progress.' : '' }}</p>
              <template v-else>
                <div v-if="s.care_plan.pes_problem" class="pes">
                  <p class="k">PES statement</p>
                  <p><strong>{{ s.care_plan.pes_problem }}</strong><template v-if="s.care_plan.pes_etiology"> related to {{ s.care_plan.pes_etiology }}</template><template v-if="s.care_plan.pes_signs">, as evidenced by {{ s.care_plan.pes_signs }}</template>.</p>
                </div>
                <div v-if="s.care_plan.diet_prescription" class="pes">
                  <p class="k">Diet prescription</p>
                  <p>{{ s.care_plan.diet_prescription }}</p>
                </div>
                <div v-if="s.care_plan.target_kcal" class="targets">
                  <div><span>Calories</span><strong>{{ Math.round(s.care_plan.target_kcal).toLocaleString('en-PH') }} kcal</strong></div>
                  <div v-if="s.care_plan.target_carb_g"><span>Carbs</span><strong>{{ Math.round(s.care_plan.target_carb_g) }} g</strong></div>
                  <div v-if="s.care_plan.target_protein_g"><span>Protein</span><strong>{{ Math.round(s.care_plan.target_protein_g) }} g</strong></div>
                  <div v-if="s.care_plan.target_fat_g"><span>Fat</span><strong>{{ Math.round(s.care_plan.target_fat_g) }} g</strong></div>
                </div>
                <p v-if="s.care_plan.target_kcal" class="targets-note">Daily targets</p>
                <p v-if="s.care_plan.goal_status" class="nm-hint">Goal status at last follow-up: <strong>{{ s.care_plan.goal_status }}</strong></p>
              </template>
            </div>

            <!-- screening -->
            <div class="nm-panel">
              <div class="pc-head"><span class="pc-ico" style="background: #FDECEC; color: #B4384A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7.5-4.6-9.2-9.3C1.7 7.4 3.8 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.2 0 5.3 2.9 4.2 6.2C19.5 15.4 12 20 12 20z" /></svg></span><div>
                <h2 class="nm-panel-title">Pre-consultation screening</h2>
                <p v-if="s.screening" class="nm-panel-sub">Submitted {{ shortDate(s.screening.date) }}</p>
              </div></div>
              <p v-if="!s.screening" class="nm-muted" style="margin-top: 10px">They haven't submitted a screening yet.</p>
              <template v-else>
                <dl class="facts sc-tiles">
                  <div><span class="sc-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17L17 3l4 4L7 21z" /><path d="M7 13l2 2M10 10l2 2M13 7l2 2" /></svg></span><span><dt>Height</dt><dd>{{ fmt1(s.screening.height_cm) }} cm</dd></span></div>
                  <div><span class="sc-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 21h14a1 1 0 0 0 1-1l-1.5-13a1 1 0 0 0-1-1h-11a1 1 0 0 0-1 1L4 20a1 1 0 0 0 1 1z" /><path d="M12 6V3M9.5 12a2.5 2.5 0 0 1 5 0M12 12l1.5-2" /></svg></span><span><dt>Weight</dt><dd>{{ fmt1(s.screening.weight_kg) }} kg</dd></span></div>
                  <div><span class="sc-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="4.5" r="2" /><path d="M8 22l1-8-3-1 2-6h8l2 6-3 1 1 8" /></svg></span><span><dt>BMI</dt><dd>{{ s.screening.bmi ? fmt1(s.screening.bmi) : '—' }}<small v-if="s.screening.bmi_category">, {{ s.screening.bmi_category }}</small><small v-if="isShortStature(s.screening.height_cm)" class="short-note">{{ BMI_SHORT_STATURE_NOTE }}</small></dd></span></div>
                  <div><span class="sc-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="14" cy="4" r="2" /><path d="M6 22l3-7 3 2v6M10 9l4-2 2 4 3 1M9 15l-3-1 2-5 3-1" /></svg></span><span><dt>Activity</dt><dd>{{ s.screening.activity_level }}</dd></span></div>
                  <div><span class="sc-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2c1 3 4 5 4 9a4 4 0 0 1-8 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 0-8z" /><path d="M8 18a4 4 0 0 0 8 0" /></svg></span><span><dt>BMR (BMI method)</dt><dd>{{ s.screening.bmr_kcal ? `${Math.round(s.screening.bmr_kcal).toLocaleString('en-PH')} kcal` : 'Not calculated' }}</dd></span></div>
                  <div><span class="sc-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2c1 3 4 5 4 9a4 4 0 0 1-8 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 0-8z" /><path d="M8 18a4 4 0 0 0 8 0" /></svg></span><span><dt>TER</dt><dd>{{ s.screening.tdee_kcal ? `${Math.round(s.screening.tdee_kcal).toLocaleString('en-PH')} kcal` : 'Not calculated' }}</dd></span></div>
                  <div><span class="sc-ico"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg></span><span><dt>NRS-2002</dt><dd>{{ s.screening.nrs_score ?? '—' }}<small v-if="s.screening.nrs_risk"> {{ s.screening.nrs_risk.toLowerCase() }}</small></dd></span></div>
                </dl>
                <div v-if="s.screening.symptoms" class="sc-sym">
                  <p class="sc-sym-k">Symptoms and notes</p>
                  <div class="sc-tags"><span v-for="(x, i) in symptomList" :key="i" class="sc-tag">{{ x }}</span></div>
                </div>
              </template>
            </div>
          </div>

          <div class="nm-col">
            <!-- next appointment -->
            <div class="nm-panel">
              <div class="nm-panel-head">
                <div class="pc-head"><span class="pc-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span><h2 class="nm-panel-title">Next consultation</h2></div>
                <button type="button" class="nm-panel-link" @click="setTab('appointments')">All consultations</button>
              </div>
              <template v-if="nextAppt">
                <div class="next-body">
                <div class="next-date"><small>{{ monthShort(nextAppt.scheduled_at) }}</small><strong>{{ dayNum(nextAppt.scheduled_at) }}</strong></div>
                <div class="next-main">
                <p class="big-when">{{ longWhen(nextAppt.scheduled_at) }}</p>
                <p class="nm-row-sub">{{ nextAppt.type_label }}, {{ nextAppt.duration_minutes }} min</p>
                <p class="pills">
                  <span v-if="nextAppt.status === 'pending'" class="nm-pill gold">Needs your confirmation</span>
                  <span v-else-if="nextAppt.payment === 'paid'" class="nm-pill green">Paid</span>
                  <span v-else class="nm-pill muted">Not paid yet</span>
                </p>
                <NuxtLink v-if="canJoin(nextAppt)" :to="`/consultation-room/${nextAppt.id}`" class="nm-btn-dark nm-btn-sm"><Video :size="14" /> Join</NuxtLink>
                <NuxtLink v-else-if="canVisit(nextAppt)" :to="`/consultation-room/${nextAppt.id}`" class="nm-btn-dark nm-btn-sm">Start visit</NuxtLink>
                <NuxtLink v-else-if="nextAppt.status === 'pending'" to="/appointments" class="nm-btn-dark nm-btn-sm">Review booking</NuxtLink>
                </div>
                </div>
              </template>
              <p v-else class="nm-muted">Nothing booked.{{ p.last_visit ? ` Last visit ${shortDate(p.last_visit)}.` : '' }}</p>
            </div>

            <!-- health profile -->
            <div class="nm-panel">
              <div class="pc-head"><span class="pc-ico" style="background: #FDECEC; color: #B4384A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7.5-4.6-9.2-9.3C1.7 7.4 3.8 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.2 0 5.3 2.9 4.2 6.2C19.5 15.4 12 20 12 20z" /></svg></span><h2 class="nm-panel-title">Health profile</h2></div>
              <dl class="hp">
                <div class="hp-row"><dt><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h4l3-8 4 16 3-8h4" /></svg>Conditions</dt><dd><span v-for="c in s.health.conditions" :key="c" class="hp-tag green">{{ c }}</span><span v-if="!s.health.conditions?.length" class="hp-none">Not recorded</span></dd></div>
                <div class="hp-row"><dt><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg>Food allergies</dt><dd><span v-for="a in s.health.allergies" :key="a" class="hp-tag red">{{ a }}</span><span v-if="!s.health.allergies.length" class="hp-none">None reported</span></dd></div>
                <div class="hp-row"><dt><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 20A7 7 0 0 1 4 13c0-6 7-9 16-9 0 9-3 16-9 16z" /><path d="M4 20c4-4 7-6 11-8" /></svg>Diet</dt><dd><span v-for="d in s.health.dietary_restrictions" :key="d" class="hp-tag gold">{{ d }}</span><span v-if="!s.health.dietary_restrictions?.length" class="hp-none">Not recorded</span></dd></div>
                <div class="hp-row"><dt><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2v6M9 5h6" /><path d="M5 22V12l7-4 7 4v10" /><path d="M10 22v-4a2 2 0 0 1 4 0v4" /></svg>Religion</dt><dd><strong>{{ s.health.religion || 'Not recorded' }}</strong></dd></div>
                <div class="hp-row"><dt><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21V4M4 4h12l-2 4 2 4H4" /></svg>Goals</dt><dd><strong>{{ list(s.health.health_goals) }}</strong></dd></div>
              </dl>
            </div>

            <!-- latest progress -->
            <div class="nm-panel">
              <div class="nm-panel-head">
                <div class="pc-head"><span class="pc-ico" style="background: #EEF1FA; color: #3B5BA5"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8" /><path d="M14 7h7v7" /></svg></span><h2 class="nm-panel-title">Latest progress</h2></div>
                <button type="button" class="nm-panel-link" @click="setTab('progress')">All progress</button>
              </div>
              <template v-if="s.progress.length">
                <p class="nm-row-sub">{{ shortDate(s.progress[0].record_date) }}</p>
                <dl class="facts">
                  <div><dt>Weight</dt><dd>{{ s.progress[0].weight_kg != null ? `${fmt1(s.progress[0].weight_kg)} kg` : '—' }}</dd></div>
                  <div><dt>BP</dt><dd>{{ s.progress[0].blood_pressure || '—' }}</dd></div>
                  <div><dt>Glucose</dt><dd>{{ s.progress[0].blood_glucose != null ? `${s.progress[0].blood_glucose} mg/dL` : '—' }}</dd></div>
                  <div><dt>HbA1c</dt><dd>{{ s.progress[0].hba1c != null ? `${s.progress[0].hba1c}%` : '—' }}</dd></div>
                </dl>
                <p v-if="s.progress[0].rnd_notes" class="private-note"><Lock :size="12" /> {{ s.progress[0].rnd_notes }}</p>
              </template>
              <p v-else class="nm-muted">No progress recorded yet.</p>
            </div>

            <!-- lab results -->
            <div class="nm-panel">
              <div class="nm-panel-head">
                <div class="pc-head"><span class="pc-ico" style="background: #FBF3D2; color: #9A7300"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3" /></svg></span><h2 class="nm-panel-title">Lab results</h2></div>
                <button type="button" class="nm-panel-link" @click="setTab('labs')">{{ s.labs.total_results ? 'View results' : (p.status === 'active' ? 'Request tests' : 'Open') }}</button>
              </div>
              <p v-if="s.labs.new_results" class="labs-new"><FlaskConical :size="14" /> {{ s.labs.new_results }} new lab result{{ s.labs.new_results === 1 ? '' : 's' }} to review</p>
              <p v-for="r in s.labs.open" :key="r.id" class="nm-row-sub">Requested {{ r.test_names.join(', ') }}. Waiting for the patient to upload.</p>
              <p v-if="!s.labs.total_results && !s.labs.open.length" class="nm-muted">No lab results yet.</p>
              <p v-else-if="s.labs.total_results && !s.labs.new_results" class="nm-muted">{{ s.labs.total_results }} result{{ s.labs.total_results === 1 ? '' : 's' }}, all reviewed.</p>
            </div>
          </div>
        </div>
      </template>

      <!-- ===================== LAB RESULTS ===================== -->
      <RndLabsTab
        v-else-if="tab === 'labs'" ref="labsTab" :relationship-id="relationshipId" :patient-first-name="p.client.first_name"
        :can-edit="p.status === 'active'" :open-request="labsAutoOpen" @changed="refresh" @auto-opened="labsAutoOpen = false"
      />

      <!-- ===================== NCP RECORDS ===================== -->
      <div v-else-if="tab === 'ncp'" class="nm-panel ncp-panel">
        <div class="nm-panel-head">
          <div class="pc-head"><span class="pc-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6M9 17.5h3" /></svg></span><div>
            <h2 class="nm-panel-title">NCP records <span v-if="ncpTimeline.length" class="ncp-count">{{ ncpTimeline.length }}</span></h2>
            <p class="nm-panel-sub">Assessment, diagnosis and intervention, plus monitoring on follow-ups. A finalized record can't be changed.</p>
          </div></div>
          <button v-if="p.status === 'active' && !openDraft && unwrittenVisit" class="nm-btn-dark nm-btn-sm ncp-write" type="button" @click="openNcpForm(unwrittenVisit.id)">
            <Pencil :size="14" /> Write record for {{ shortDate(unwrittenVisit.scheduled_at) }} visit
          </button>
        </div>
        <!-- timeline, newest first: what each record says, so visits compare at a glance -->
        <ol v-if="ncpTimeline.length" class="nr-list">
          <li v-for="r in ncpTimeline" :key="r.id" class="nr" :class="{ draft: r.status !== 'completed' }">
            <div class="nr-date" aria-hidden="true">
              <small>{{ dateParts(r.encounter_date || r.created_at).m }}</small>
              <strong>{{ dateParts(r.encounter_date || r.created_at).d }}</strong>
              <small>{{ dateParts(r.encounter_date || r.created_at).y }}</small>
            </div>
            <div class="nr-main">
              <div class="nr-top">
                <h4>{{ r.kindLabel }}</h4>
                <span class="nr-status" :class="r.status === 'completed' ? 'ok' : 'draft'">
                  <Lock v-if="r.status === 'completed'" :size="12" />
                  <Pencil v-else :size="12" />
                  {{ r.status === 'completed' ? 'Finalized' : 'Draft' }}
                </span>
                <span class="nr-edited">{{ shortDate(r.encounter_date || r.created_at) }}<template v-if="r.status !== 'completed'">, last edited {{ dateTime(r.updated_at) }}</template></span>
              </div>
              <p class="nr-dx">
                <span class="nr-p" aria-hidden="true">P</span>
                <span v-if="r.pes_problem" class="nr-dx-t" :title="`${r.pes_problem}${r.pes_etiology ? ` related to ${r.pes_etiology}` : ''}`"><b>{{ r.pes_problem }}</b><template v-if="r.pes_etiology"> related to {{ r.pes_etiology }}</template></span>
                <span v-else class="nr-dx-t none">Diagnosis not written yet</span>
              </p>
              <div class="nr-chips">
                <span class="nr-chip"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M8 9a4 4 0 0 1 8 0" /><path d="M12 9l1.5-2" /></svg><b>{{ r.weight_kg != null ? `${fmt1(r.weight_kg)} kg` : 'Not measured' }}</b><em v-if="r.weightChange != null" :class="{ down: r.weightChange < 0, up: r.weightChange > 0 }">{{ Math.abs(r.weightChange) < 0.05 ? 'no change' : `${signed(r.weightChange)} kg` }}</em></span>
                <span class="nr-chip"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22a7 7 0 0 0 7-7c0-4-3-6-4-9-1 2-2 3-4 3 0-2-1-4-2-6-1 4-4 7-4 12a7 7 0 0 0 7 7z" /></svg><template v-if="r.target_kcal"><b>{{ Math.round(r.target_kcal).toLocaleString('en-PH') }}</b> kcal/day</template><template v-else>TER not set</template></span>
                <span v-if="r.is_follow_up" class="nr-chip"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg>Goal <b>{{ GOAL_LABEL[r.goal_status] || 'Not rated' }}</b></span>
              </div>
              <p v-if="r.status !== 'completed' && r.missing.length" class="nr-miss"><AlertTriangle :size="13" /> Still needed: {{ r.missing.join(', ') }}</p>
            </div>
            <div class="nr-acts">
              <!-- no Delete: a record comes from a consultation, so a draft is continued, never discarded -->
              <button type="button" class="nr-btn" :class="r.status === 'completed' ? 'dark' : 'soft'" @click="viewNcpRecord(r)"><Eye :size="15" /> {{ r.status === 'completed' ? 'View record' : 'View' }}<template v-if="r.status === 'completed'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></template></button>
              <button v-if="r.status !== 'completed' && p.status === 'active'" type="button" class="nr-btn gold" @click="openNcpForm()"><Pencil :size="15" /> Continue record<svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></button>
            </div>
          </li>
        </ol>
        <div v-else class="ncp-empty">
          <span class="pc-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6M9 17.5h3" /></svg></span>
          <p>No NCP records yet.</p>
        </div>
        <p v-if="p.status === 'active' && !openDraft && !unwrittenVisit" class="ncp-hint"><Info :size="15" /> NCP records are written during the consultation, in the consultation room's NCP tab.</p>
      </div>

      <!-- ===================== MEAL PLAN ===================== -->
      <template v-else-if="tab === 'meal'">
        <div class="mpx-grid"><div class="mpx-left">
        <div class="nm-panel mpx-plan">
          <div class="nm-panel-head mpx-head">
            <span class="mpx-ico"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M17 3c-2 0-3 2-3 5s1 4 3 4v9" /></svg></span>
            <div>
              <div class="mpx-row">
                <h2 class="nm-panel-title">{{ s.meal_plan ? s.meal_plan.name : 'Meal plan' }}</h2>
                <span v-if="s.meal_plan" class="mpx-pill" :class="s.meal_plan.status">{{ { active: 'Active', draft: 'Draft', archived: 'Ended' }[s.meal_plan.status] || s.meal_plan.status }}</span>
              </div>
              <p class="nm-panel-sub mpx-meta" v-if="s.meal_plan">
                <span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>{{ s.meal_plan.status === 'active' ? `Sent ${shortDate(s.meal_plan.sent_at)}` : s.meal_plan.status === 'archived' ? `Their last plan, sent ${shortDate(s.meal_plan.sent_at)}. It ended with their care` : 'Draft, not sent to the patient yet' }}</span>
                <span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12a8 8 0 0 1 14-5.3L20 9M20 4v5h-5M20 12a8 8 0 0 1-14 5.3L4 15M4 20v-5h5" /></svg>{{ s.meal_plan.meals_per_week }} meals a week</span>
              </p>
            </div>
            <template v-if="p.status === 'active'">
              <NuxtLink v-if="mealPlanReady" :to="`/meal-planning?relationship=${relationshipId}&edit=1`" class="nm-btn-dark nm-btn-sm mpx-upd">
                <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg>{{ s.meal_plan ? (s.meal_plan.status === 'draft' ? 'Finish and send plan' : 'Update meal plan') : 'Create meal plan' }}
              </NuxtLink>
            </template>
          </div>
          <p v-if="p.status === 'active' && !mealPlanReady && !s.meal_plan" class="nm-note todo-note" style="margin: 0">Finish the NCP Intervention (diet prescription and target calories) before creating a meal plan.</p>
          <template v-if="s.meal_plan?.target_kcal">
            <p class="mpx-key"><span class="mpx-key-t">Color key:</span><span><i class="k" />Calories</span><span><i class="c" />Carbs</span><span><i class="p" />Protein</span><span><i class="f" />Fat</span></p>
            <div class="targets mpx-macros">
              <div class="mt-k"><span class="mx-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3c3 4 6 6 6 10a6 6 0 0 1-12 0c0-3 2-5 3-7 1 2 2 3 3 3 0-2-1-4 0-6z" /></svg></span><p><span>Calories</span><strong>{{ Math.round(s.meal_plan.target_kcal).toLocaleString('en-PH') }}<em>kcal</em></strong><small>Daily target</small></p></div>
              <div v-if="s.meal_plan.target_carb_g" class="mt-c"><span class="mx-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21V9M12 9c-3 0-4-3-4-5 2 0 4 1 4 5zM12 9c3 0 4-3 4-5-2 0-4 1-4 5zM12 14c-3 0-4-3-4-5 2 0 4 1 4 5zM12 14c3 0 4-3 4-5-2 0-4 1-4 5z" /></svg></span><p><span>Carbs</span><strong>{{ Math.round(s.meal_plan.target_carb_g) }}<em>g</em></strong><small v-if="macroPct.c">{{ macroPct.c }}% of calories</small></p></div>
              <div v-if="s.meal_plan.target_protein_g" class="mt-p"><span class="mx-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3c-4 0-7 6-7 10a7 7 0 0 0 14 0c0-4-3-10-7-10z" /></svg></span><p><span>Protein</span><strong>{{ Math.round(s.meal_plan.target_protein_g) }}<em>g</em></strong><small v-if="macroPct.p">{{ macroPct.p }}% of calories</small></p></div>
              <div v-if="s.meal_plan.target_fat_g" class="mt-f"><span class="mx-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" /></svg></span><p><span>Fat</span><strong>{{ Math.round(s.meal_plan.target_fat_g) }}<em>g</em></strong><small v-if="macroPct.f">{{ macroPct.f }}% of calories</small></p></div>
            </div>
          </template>
          <p v-else-if="!s.meal_plan && p.status !== 'active'" class="nm-muted">No meal plan was sent during their care.</p>
          <p v-else-if="!s.meal_plan && mealPlanReady" class="nm-muted">No meal plan yet.</p>
        </div>

        <div class="nm-panel mpx-adh">
          <div class="mpx-adh-sum">
            <p class="mpx-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8M15 7h6v6" /></svg>Adherence</p>
            <h2 class="nm-panel-title">Last 14 days</h2>
            <div class="mpx-big"><b>{{ adhSummary.avg == null ? '—' : `${adhSummary.avg}%` }}</b><span>{{ adhSummary.avg == null ? 'No rated days yet' : 'average on rated days' }}</span></div>
            <ul class="mpx-facts">
              <li><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg><span>Goal</span><b>80%</b></li>
              <li><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg><span>Days rated</span><b>{{ adhSummary.rated }} of {{ s.adherence_days.length }}</b></li>
              <li><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg><span>Meals logged</span><b>{{ adhSummary.logged }}</b></li>
            </ul>
            <p class="mpx-note"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg><span>Share of planned meals followed each day, from your ratings. Partly followed counts as half, an unlogged meal counts as missed, and logs you haven't rated yet aren't counted.</span></p>
          </div>
          <div class="mpx-adh-chart">
          <p v-if="!s.adherence_days.some(d => d.planned)" class="nm-muted mpx-empty">No meals were planned in the last 14 days.</p>
          <div v-else class="mini-chart" role="img" :aria-label="`Adherence by day: ${s.adherence_days.map(d => `${d.date} ${d.followed_pct ?? 'none planned'}`).join(', ')}`">
            <div class="mc-plot">
              <div v-for="t in [100, 50, 0]" :key="t" class="mc-grid" :style="{ bottom: `${t}%` }"><span>{{ t }}%</span></div>
              <div class="mc-goal" style="bottom: 80%"><span>Goal 80%</span></div>
              <div class="mc-cols">
                <div v-for="(d, i) in s.adherence_days" :key="d.date" class="mc-col" tabindex="0"
                     :aria-label="d.followed_pct == null ? `${dayName(d.date)}: no meals planned` : `${dayName(d.date)}: ${d.followed_pct}%, ${d.logged} of ${d.planned} logged`"
                     @mouseenter="hover = i" @mouseleave="hover = null" @focus="hover = i" @blur="hover = null">
                  <span class="mc-track" aria-hidden="true" />
                  <span v-if="d.followed_pct == null" class="mc-none" />
                  <span v-else class="mc-bar" :class="{ today: i === s.adherence_days.length - 1 }" :style="{ height: `${Math.max(d.followed_pct, 1.5)}%` }" />
                  <div v-if="hover === i" class="tip" :class="{ left: i > 9, right: i < 3 }">
                    <strong>{{ dayName(d.date) }}</strong>
                    <span v-if="d.followed_pct == null">{{ d.waiting ? `${d.waiting} log${d.waiting === 1 ? '' : 's'} waiting for your rating` : 'No meals planned' }}</span>
                    <template v-else><span>{{ d.followed_pct }}% followed</span><span class="tip-muted">{{ d.logged }} of {{ d.planned }} meals logged</span><span v-if="d.waiting" class="tip-muted">{{ d.waiting }} waiting for your rating</span></template>
                  </div>
                </div>
              </div>
            </div>
            <div class="mc-x">
              <span v-for="(d, i) in s.adherence_days" :key="d.date">{{ i === s.adherence_days.length - 1 ? 'Today' : new Date(`${d.date}T00:00:00`).getDate() }}</span>
            </div>
            <p class="mpx-leg"><span><i class="g" />Followed share</span><span><i class="n" />No rated meals</span></p>
          </div>
          </div>
        </div>

        </div>
        <div class="nm-panel mpx-logs">
          <div class="mpx-logs-head">
            <div>
              <p class="mpx-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg>Meal logs</p>
              <h2 class="nm-panel-title">What {{ p.client.first_name }} ate</h2>
              <p class="nm-panel-sub">With their photo and note. {{ p.status === 'active' ? 'Rate each one. It counts toward adherence once rated.' : '' }}</p>
            </div>
            <div class="mpx-logs-side">
              <button v-if="s.recent_logs.length" type="button" class="mpx-seeall" @click="showAllLogs = true">See all<svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></button>
              <strong v-if="toReview && p.status === 'active'" class="to-review">{{ toReview }} to review</strong>
            </div>
          </div>
          <div v-if="s.recent_logs.length" class="mpx-list">
            <article v-for="l in visibleLogs" :id="`meal-log-${l.id}`" :key="l.id" class="mpx-log" :class="{ 'row-flash': flashLog === l.id, todo: !l.status && p.status === 'active' }">
              <div class="lg-date"><b>{{ new Date(l.date + 'T00:00:00').getDate() }}</b><small>{{ new Date(l.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short' }) }}</small></div>
              <button v-if="l.photo_url" type="button" class="lg-pic" :aria-label="`Open photo of ${l.meal} on ${shortDate(l.date)}`" @click="photoLog = l"><img :src="l.photo_url" :alt="`${l.meal} photo`" loading="lazy" /><span><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg>Tap to enlarge</span></button>
              <span v-else class="lg-pic lg-nopic"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg>No photo</span>
              <div class="lg-main">
                <p class="lg-meal"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M17 3c-2 0-3 2-3 5s1 4 3 4v9" /></svg>{{ l.meal }}<span><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg><em class="lg-day">{{ shortDate(l.date) }}, </em>{{ l.time_logged ? clockOf(l.time_logged) : 'Not recorded' }}</span></p>
                <p class="lg-note" :class="{ empty: !l.note }">{{ l.note || 'No note' }}</p>
              </div>
              
              <div class="lg-rate">
                <small>Your rating</small>
                <MealLogRating v-if="p.status === 'active'" :log-id="l.id" :status="l.status" compact
                               :label="`${l.meal} on ${shortDate(l.date)}`" @rated="load" />
                <span v-else class="nm-pill" :class="LOG_PILL[l.status] || 'muted'">{{ l.status_label }}</span>
              </div>
            </article>
            <MealPhotoModal v-if="photoLog && !showAllLogs" :url="photoLog.photo_url" :title="`${photoLog.meal}, ${shortDate(photoLog.date)}`" :note="photoLog.note || ''" @close="photoLog = null" />
          </div>
          <p v-else class="nm-muted mpx-none">No meals logged yet.</p>
        </div>
        </div>
        <!-- ALL MEAL LOGS: a full-screen view (no new page) -->
        <Teleport to="body">
          <div v-if="showAllLogs" class="mlx" role="dialog" aria-modal="true" aria-labelledby="mlx-title">
            <header class="mlx-bar">
              <button type="button" class="mlx-back" @click="showAllLogs = false"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 12H5M11 6l-6 6 6 6" /></svg>Back to chart</button>
              <div class="mlx-t">
                <p class="mlx-k"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg>Meal logs</p>
                <h2 id="mlx-title">What {{ p.client.first_name }} ate</h2>
                <p>{{ s.recent_logs.length }} meal log{{ s.recent_logs.length === 1 ? '' : 's' }}<template v-if="toReview && p.status === 'active'">, <b>{{ toReview }} to review</b></template></p>
              </div>
              <div class="mlx-filter" role="tablist" aria-label="Show">
                <button v-for="f in LOG_FILTERS" :key="f.key" type="button" role="tab" :aria-selected="logFilter === f.key" :class="{ on: logFilter === f.key }" @click="logFilter = f.key">{{ f.label }}</button>
              </div>
            </header>
            <div class="mlx-body">
              <p v-if="!filteredLogs.length" class="mlx-empty">No meal logs here.</p>
              <div v-else class="mlx-grid">
                <article v-for="l in filteredLogs" :id="`meal-log-${l.id}`" :key="l.id" class="mlx-card" :class="{ todo: !l.status && p.status === 'active', 'row-flash': flashLog === l.id }">
                  <button v-if="l.photo_url" type="button" class="mlx-pic" :aria-label="`Open photo of ${l.meal} on ${shortDate(l.date)}`" @click="photoLog = l"><img :src="l.photo_url" :alt="`${l.meal} photo`" loading="lazy" /><span><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg>Tap to enlarge</span></button>
                  <div v-else class="mlx-pic none"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg>No photo</div>
                  <div class="mlx-info">
                    <p class="lg-meal"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3v8M5 3v5a2 2 0 0 0 4 0V3M7 11v10M17 3c-2 0-3 2-3 5s1 4 3 4v9" /></svg>{{ l.meal }}</p>
                    <p class="mlx-when"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ shortDate(l.date) }}, {{ l.time_logged ? clockOf(l.time_logged) : 'Not recorded' }}</p>
                    <p class="lg-note" :class="{ empty: !l.note }">{{ l.note || 'No note' }}</p>
                  </div>
                  <div class="lg-rate">
                    <small>Your rating</small>
                    <MealLogRating v-if="p.status === 'active'" :log-id="l.id" :status="l.status" compact
                                   :label="`${l.meal} on ${shortDate(l.date)}`" @rated="load" />
                    <span v-else class="nm-pill" :class="LOG_PILL[l.status] || 'muted'">{{ l.status_label }}</span>
                  </div>
                </article>
              </div>
            </div>
            <MealPhotoModal v-if="photoLog" :url="photoLog.photo_url" :title="`${photoLog.meal}, ${shortDate(photoLog.date)}`" :note="photoLog.note || ''" @close="photoLog = null" />
          </div>
        </Teleport>
      </template>

      <!-- ===================== PROGRESS ===================== -->
      <template v-else-if="tab === 'progress'">
        <!-- every measurement at once (was one chart with a Weight / BMI / … switcher) -->
        <div class="nm-panel pgx">
          <div class="pgx-h"><div>
            <p class="pgx-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8M15 7h6v6" /></svg>Trends</p>
            <h2 class="nm-panel-title">How the numbers are moving</h2>
            <p class="nm-panel-sub">From the screening, progress records and finalized NCP records.</p>
          </div></div>
          <p v-if="!trends.shown.length" class="nm-muted pgx-empty">No measurements yet. They appear here once an NCP record is finalized.</p>
          <div v-else class="trend-grid pgx-grid">
            <section v-for="t in trends.shown" :key="t.key" class="trend-card pgx-card">
              <div class="tc-head pgx-ch">
                <span class="pgx-ico sm" :class="PG_TONE[t.key]"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="PG_ICON[t.key] || PG_ICON.weight" /></span>
                <div class="pgx-ct">
                  <h3 class="tc-title">{{ t.label }}</h3>
                  <p class="tc-sub">{{ t.sub }}</p>
                </div>
                <div class="pgx-cv">
                  <span class="tc-latest">{{ t.latest }}</span>
                  <span class="pgx-chg" :class="t.hasTrend ? 'flat' : 'flat'">{{ t.hasTrend ? `${trendPoints(t)} readings` : '1 reading' }}</span>
                </div>
              </div>
              <TrendChart v-if="t.hasTrend" :series="t.series" :unit="t.unit" :decimals="t.decimals" :ref-lines="t.refLines" :title="`${t.label} trend`" />
              <div v-else class="pgx-one">
                <svg viewBox="0 0 600 70" preserveAspectRatio="none" width="100%" height="70" aria-hidden="true"><line x1="20" x2="580" y1="35" y2="35" class="dash" /><circle cx="60" cy="35" r="7" class="pt" /></svg>
                <p><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8M15 7h6v6" /></svg>The trend line starts at the second reading.</p>
              </div>
            </section>
          </div>
          <div v-if="trends.none.length" class="pgx-none">
            <span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg>No readings yet:</span>
            <i v-for="n in trends.none" :key="n">{{ n.charAt(0).toUpperCase() + n.slice(1) }}</i>
          </div>
        </div>

        <div class="nm-panel pgx">
          <div class="pgx-h">
            <div>
              <p class="pgx-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>Records</p>
              <h2 class="nm-panel-title">All progress records</h2>
              <p class="nm-panel-sub">Saved automatically when you finalize an NCP record, with the measurements from that consultation.</p>
            </div>
            <span v-if="s.progress.length" class="pgx-count">{{ s.progress.length }} record{{ s.progress.length === 1 ? '' : 's' }}</span>
          </div>
          <div v-if="s.progress.length" class="pgx-list">
            <article v-for="r in s.progress" :key="r.id" class="pgx-rec">
              <div class="pgx-date"><b>{{ dateParts(r.record_date).d }}</b><small>{{ dateParts(r.record_date).m }}</small><em>{{ dateParts(r.record_date).y }}</em></div>
              <ul class="pgx-vals">
                <li :class="{ no: r.weight_kg == null }"><small><i class="w" />Weight</small><b>{{ r.weight_kg != null ? fmt1(r.weight_kg) : '—' }}<em v-if="r.weight_kg != null">kg</em></b></li>
                <li :class="{ no: r.bmi == null }"><small><i class="bm" />BMI</small><b>{{ r.bmi != null ? fmt1(r.bmi) : '—' }}</b></li>
                <li :class="{ no: !r.blood_pressure }"><small><i class="bp" />Blood pressure</small><b>{{ r.blood_pressure || '—' }}</b></li>
                <li :class="{ no: r.blood_glucose == null }"><small><i class="gl" />Glucose</small><b>{{ r.blood_glucose != null ? r.blood_glucose : '—' }}<em v-if="r.blood_glucose != null">mg/dL</em></b></li>
                <li :class="{ no: r.hba1c == null }"><small><i class="hb" />HbA1c</small><b>{{ r.hba1c != null ? `${r.hba1c}%` : '—' }}</b></li>
              </ul>
              <div class="pgx-side">
                <span class="pgx-src" :class="{ self: r.source === 'client' }"><template v-if="r.source === 'client'"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg>Self-reported</template><template v-else><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5" /></svg>Progress record</template></span>
                <p class="pgx-note">Note: <template v-if="r.source === 'client'"><em v-if="!r.client_notes">None</em><template v-else>Patient: {{ r.client_notes }}</template></template><template v-else><em v-if="!r.rnd_notes">None</em><template v-else>{{ r.rnd_notes }}</template></template></p>
              </div>
            </article>
          </div>
          <p v-else class="nm-muted pgx-empty">No progress records yet.</p>
        </div>
      </template>

      <!-- ===================== CONSULTATIONS ===================== -->
      <div v-else-if="tab === 'appointments'" class="csx">
        <!-- 1. coming up, grouped by day -->
        <div class="nm-panel csx-card">
          <div class="csx-h">
            <div>
              <p class="csx-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>Coming up</p>
              <h2 class="nm-panel-title">Consultations with {{ p.client.first_name }}</h2>
              <p class="nm-panel-sub">{{ p.consultations }} completed{{ consults.upcoming.length ? `, ${consults.upcoming.length} coming up` : '' }}</p>
            </div>
            <NuxtLink :to="`/appointments?relationship=${relationshipId}`" class="csx-open">Open Appointments<svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
          </div>
          <p v-if="!consults.upcoming.length" class="nm-muted csx-empty">Nothing booked{{ s.appointments.length ? '' : ' yet' }}.</p>
          <section v-for="(g, gi) in byDay(consults.upcoming)" :key="g.key" class="csx-g">
            <h4><b>{{ g.label }}</b><span>{{ g.date }}</span><em v-if="gi === 0" class="csx-next">Next</em></h4>
            <div class="csx-l">
              <article v-for="(a, ai) in g.items" :key="a.id" class="csx-e" :class="{ nx: gi === 0 && ai === 0 }">
                <span class="csx-i" :class="gi === 0 && ai === 0 ? 'gold' : 'blue'"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="14" height="12" rx="2" /><path d="M22 8l-6 4 6 4z" /></svg></span>
                <div class="csx-t">
                  <b>{{ a.type_label }} consultation</b>
                  <small>{{ timeOf(a.scheduled_at) }}, {{ a.duration_minutes }} min<template v-if="a.amount">, {{ peso(a.amount) }}</template></small>
                </div>
                <div class="csx-s">
                  <span class="csx-pl" :class="a.status === 'pending' ? 'gold' : 'blue'"><template v-if="a.status !== 'pending'"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></template>{{ a.status === 'pending' ? 'Needs your confirmation' : 'Confirmed' }}</span>
                  <span v-if="a.payment" class="csx-pl" :class="a.payment === 'paid' ? 'green' : 'muted'">{{ PAY_LABEL[a.payment] || a.payment }}</span>
                  <NuxtLink v-if="canJoin(a)" :to="`/consultation-room/${a.id}`" class="nm-btn-dark nm-btn-sm"><Video :size="13" /> Join</NuxtLink>
                  <NuxtLink v-else-if="canVisit(a)" :to="`/consultation-room/${a.id}`" class="nm-btn-dark nm-btn-sm">Start visit</NuxtLink>
                  <NuxtLink v-else-if="a.status === 'pending'" to="/appointments?tab=requests" class="nm-btn-dark nm-btn-sm">Review booking</NuxtLink>
                </div>
              </article>
            </div>
          </section>
        </div>

        <!-- 2. history, grouped by day -->
        <div v-if="consults.past.length" class="nm-panel csx-card">
          <div class="csx-h">
            <div>
              <p class="csx-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5M12 7v5l3 2" /></svg>History</p>
              <h2 class="nm-panel-title">Past consultations</h2>
            </div>
            <span class="csx-count">{{ consults.past.length }} consultation{{ consults.past.length === 1 ? '' : 's' }}</span>
          </div>
          <section v-for="g in byDay(pagedPast)" :key="g.key" class="csx-g">
            <h4><b>{{ g.label }}</b><span>{{ g.date }}</span></h4>
            <div class="csx-l">
              <article v-for="a in g.items" :key="a.id" class="csx-e">
                <span class="csx-i" :class="{ completed: 'green', cancelled: 'red' }[a.status] || 'gold'">
                  <template v-if="a.status === 'completed'"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></template>
                  <template v-else-if="a.status === 'cancelled'"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg></template>
                  <template v-else><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg></template>
                </span>
                <div class="csx-t">
                  <b>{{ a.type_label }} consultation {{ a.status === 'confirmed' ? 'not marked complete' : (APPT_LABEL[a.status] || a.status).toLowerCase() }}</b>
                  <small>{{ timeOf(a.scheduled_at) }}<template v-if="a.status === 'cancelled' && a.cancellation_reason">, {{ a.cancellation_reason }}</template></small>
                </div>
                <div class="csx-s col">
                  <div class="csx-row">
                    <span class="csx-pl" :class="a.payment === 'paid' ? 'green' : a.payment ? 'gold' : 'muted'">{{ a.payment ? (PAY_LABEL[a.payment] || a.payment) : 'No payment' }}<template v-if="a.amount && a.payment === 'paid'">, {{ peso(a.amount) }}</template></span>
                    <button v-if="a.status === 'completed'" type="button" class="nm-btn-outline nm-btn-sm csx-sum" @click="summaryId = a.id"><FileText :size="13" /> Summary</button>
                  </div>
                  <span v-if="a.ncp_status === 'completed'" class="csx-ncp ok"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>NCP finalized</span>
                  <span v-else-if="a.ncp_status === 'draft'" class="csx-ncp draft">NCP draft</span>
                  <span v-else-if="a.status === 'completed'" class="csx-ncp none">No NCP record</span>
                  <span v-else class="csx-ncp mute">{{ a.status === 'confirmed' ? 'No NCP yet' : 'No NCP needed' }}</span>
                </div>
              </article>
            </div>
          </section>
          <ListPager v-model:page="pastPage" :pages="pastPages" />
        </div>
      </div>

      <!-- ===================== REMINDERS ===================== -->
      <div v-else-if="tab === 'reminders'" class="nm-panel">
        <RndClientReminders :relationship-id="relationshipId" :client-name="p.client.name" :can-edit="p.status === 'active'" />
      </div>
    </template>

    <NcpRecordModal
      v-if="ncpModal"
      :key="`${ncpModal.mode}-${ncpModal.recordId}`"
      :relationship-id="relationshipId"
      :patient-name="p?.client.name || ''"
      :mode="ncpModal.mode"
      :record-id="ncpModal.recordId"
      :appointment-id="ncpModal.appointmentId"
      :can-continue="p?.status === 'active'"
      @close="ncpModal = null"
      @changed="refresh"
      @continue="ncpModal = { mode: 'edit', recordId: null }"
    />
    <DischargeModal
      v-if="showDischarge" :relationship-id="relationshipId" :patient-name="p?.client.name"
      :initial-reason="s?.discharge_request ? `Care ended at ${p.client.first_name}'s request (${s.discharge_request.reason_label}). ` : ''"
      @close="showDischarge = false" @discharged="onDischarged"
    />
    <ConsultationSummaryModal v-if="summaryId" :appointment-id="summaryId" role="rnd" @close="summaryId = null" />
  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
const toast = useToast() // the app's toast (2026-11-03)
import {
  AlertTriangle, Check, CheckCircle2, Eye, FileText, Pencil, FlaskConical, Info, Lock, MessageSquare, MoreHorizontal, OctagonAlert, Video,
} from 'lucide-vue-next'
import { figureSource, screeningSource } from '~/utils/figureSource'
import { BMI_SHORT_STATURE_NOTE, isShortStature } from '~/utils/ncp'

const route = useRoute()
const router = useRouter()
const { get } = useApi()
const now = useNow()
const relationshipId = route.params.relationshipId

const s = ref(null)
const ncpRecords = ref([])
const loading = ref(true)
const error = ref('')
const hover = ref(null)
const p = computed(() => s.value?.patient)

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    const [summary, ncp] = await Promise.all([
      get(`/rnd/relationships/${relationshipId}/summary/`),
      get(`/rnd/relationships/${relationshipId}/ncp/`).catch(() => []),
    ])
    s.value = summary
    ncpRecords.value = ncp
  } catch {
    if (!quiet) error.value = 'Could not load this patient.'
  } finally {
    loading.value = false
  }
}
const refresh = load
// meal logs, lab uploads, payments and discharge requests show without a
// reload; the NCP form and other pop-ups pause it while open
useAutoRefresh(() => load({ quiet: true }))
onMounted(async () => {
  await load()
  if (route.query.log) showLog(Number(route.query.log))
  // "Continue in chart" (NCP Records page) lands here with ?open=draft.
  if (route.query.open === 'draft' && s.value?.patient.status === 'active') {
    tab.value = 'ncp'
    openNcpForm()
    const { open, ...rest } = route.query
    router.replace({ query: rest })
  }
})

/* ---------- tabs (?tab= deep links from other pages) ---------- */
const TAB_KEYS = ['overview', 'ncp', 'meal', 'progress', 'labs', 'appointments', 'reminders']
const tab = ref(TAB_KEYS.includes(route.query.tab) ? route.query.tab : 'overview')
function setTab(k) {
  tab.value = k
  router.replace({ query: { ...route.query, tab: k === 'overview' ? undefined : k } })
}
// A notification can open this chart while it's already showing
// (?tab=meal&log=<id> for "Meal log to review"): follow the URL, and bring
// that meal log into view with a short highlight.
const flashLog = ref(null)
const photoLog = ref(null) // the meal log whose photo is open
async function showLog(id) {
  if (!id) return
  await nextTick()
  const row = document.getElementById(`meal-log-${id}`)
  if (row) {
    row.scrollIntoView({ block: 'center', behavior: 'smooth' })
    flashLog.value = id
    setTimeout(() => { if (flashLog.value === id) flashLog.value = null }, 3000)
  }
  const { log, ...rest } = route.query
  router.replace({ query: rest })
}
watch(() => [route.query.tab, route.query.log], async ([t, log]) => {
  const next = TAB_KEYS.includes(t) ? t : 'overview'
  if (next !== tab.value) tab.value = next
  if (log) {
    await load({ quiet: true })
    showLog(Number(log))
  }
})
const TABS = computed(() => [
  { key: 'overview', label: 'Overview' },
  { key: 'ncp', label: 'NCP records', count: ncpRecords.value.length || null },
  { key: 'meal', label: 'Meal plan' },
  { key: 'progress', label: 'Progress', count: s.value?.progress.length || null },
  { key: 'labs', label: 'Lab results', count: s.value?.labs.new_results || null },
  { key: 'appointments', label: 'Consultations', count: s.value?.appointments.length || null },
  { key: 'reminders', label: 'Tasks & reminders' },
])

/* ---------- lab tests: the header button opens the request pop-up on the Lab results tab ---------- */
const labsTab = ref(null)
const labsAutoOpen = ref(false)
function requestLabs() {
  if (tab.value === 'labs' && labsTab.value) return labsTab.value.openRequestForm()
  labsAutoOpen.value = true
  setTab('labs')
}

/* ---------- labels ---------- */
const STATUS_LABEL = { active: 'Active patient', pending: 'New booking', discharged: 'Discharged' }
const ALERT_ICONS = { critical: OctagonAlert, warning: AlertTriangle, info: Info }
const APPT_LABEL = { pending: 'To confirm', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }
const APPT_PILL = { pending: 'gold', confirmed: 'blue', completed: 'green', cancelled: 'muted' }
const PAY_LABEL = { paid: 'Paid', unpaid: 'Not paid yet', refund_pending: 'Refund pending', refunded: 'Refunded', cancelled: 'Voided' }
const LOG_PILL = { followed: 'green', partially_followed: 'gold', not_followed: 'red' }
const SEX = { male: 'Male', female: 'Female' }

const metaLine = computed(() => {
  const c = p.value.client
  return [c.age != null ? `${c.age} y/o` : null, SEX[c.sex], s.value.health.conditions.join(', ') || null].filter(Boolean).join(', ')
})
const list = arr => (arr && arr.length ? arr.join(', ') : 'Not recorded')

// header "More" menu (Discharge): closes on an outside click or Escape
const moreOpen = ref(false)
function closeMore(e) { if (e.type === 'click' || e.key === 'Escape') moreOpen.value = false }
onMounted(() => { document.addEventListener('click', closeMore); document.addEventListener('keydown', closeMore) })
onUnmounted(() => { document.removeEventListener('click', closeMore); document.removeEventListener('keydown', closeMore) })
const fmt1 = v => Number(v).toFixed(1)
const signed = v => `${Number(v) > 0 ? '+' : Number(v) < 0 ? '−' : ''}${Math.abs(Number(v)).toFixed(1)}`

/* ---------- care stage ---------- */
const stageSteps = computed(() => {
  const st = p.value.stage
  return [
    { label: 'Screening', state: st.screening ? 'done' : 'todo', sub: s.value.screening ? shortDate(s.value.screening.date) : 'Not submitted' },
    { label: 'NCP', state: st.ncp === 'done' ? 'done' : st.ncp_draft ? 'current' : 'todo',
      sub: st.ncp === 'done' ? `${st.ncp_count} finalized` : st.ncp_draft ? 'Draft in progress' : 'Not started' },
    { label: 'Meal plan', state: st.meal_plan === 'active' ? 'done' : st.meal_plan === 'draft' ? 'current' : 'todo',
      sub: { active: 'Sent', draft: 'Not sent yet', none: 'None yet' }[st.meal_plan] },
    { label: 'Follow-up', state: st.follow_up ? 'done' : (st.ncp === 'done' && st.ncp_draft) ? 'current' : 'todo',
      sub: st.follow_up ? 'Done' : (st.ncp === 'done' && st.ncp_draft) ? 'In progress' : 'Not yet' },
  ]
})
const toReview = computed(() => (s.value?.recent_logs || []).filter(l => !l.status).length)
const mealPlanReady = computed(() => ncpRecords.value.some(r => r.diet_prescription || r.target_kcal))

/* ---------- appointments ---------- */
const nextAppt = computed(() => [...(s.value?.appointments || [])].filter(a => a.upcoming).sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))[0] || null)
// Consultations tab: coming up / ended but still open / history
const consults = computed(() => {
  const all = s.value?.appointments || []
  return {
    upcoming: all.filter(a => a.upcoming).reverse(), // soonest first
    // ended but not marked complete yet: listed with the past ones (Appointments → To complete is where it's done)
    past: all.filter(a => !a.upcoming),
  }
})
const pastConsults = computed(() => consults.value.past)
const { page: pastPage, pages: pastPages, paged: pagedPast } = usePager(pastConsults, { perPage: 10 })
// appointment start time, Philippine time, e.g. 10:00 AM
const timeOf = v => new Date(v).toLocaleTimeString('en-PH', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' })
// an in-person visit opens from the start of its day and stays open until the RND finishes it
function canVisit(a) {
  return a.status === 'confirmed' && a.type === 'in_person' && now.value >= new Date(a.join_opens_at)
}
function canJoin(a) {
  return a.status === 'confirmed' && a.type === 'video' && now.value >= new Date(a.join_opens_at) && now.value <= new Date(a.join_closes_at)
}
const PH = { timeZone: 'Asia/Manila' }
const longWhen = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
const dayNum = v => new Date(v).toLocaleDateString('en-PH', { ...PH, day: 'numeric' })
const monthShort = v => new Date(v).toLocaleDateString('en-PH', { ...PH, month: 'short' })
const dayName = iso => new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { weekday: 'short', month: 'short', day: 'numeric' })
const shortDay = (iso, today) => (today ? 'Today' : new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { month: 'short', day: 'numeric' }))
function clockOf(t) {
  const [h, m] = t.split(':').map(Number)
  return `${((h + 11) % 12) + 1}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}

/* ---------- NCP (shared NcpRecordModal) ---------- */
const ncpModal = ref(null)
const openDraft = computed(() => ncpRecords.value.find(r => r.status === 'draft') || null)
function openNcpForm(appointmentId = null) { ncpModal.value = { mode: 'edit', recordId: null, appointmentId } }
// The latest completed consultation that has no NCP record yet (the RND didn't write it in the room).
const unwrittenVisit = computed(() => {
  const last = (s.value?.appointments || []).find(a => a.status === 'completed') // newest first
  return last && !last.has_ncp ? last : null
})
function viewNcpRecord(r) { ncpModal.value = { mode: 'view', recordId: r.id } }
const GOAL_LABEL = { met: 'Met', partially_met: 'Partially met', not_met: 'Not met', ongoing: 'Ongoing' }
// What finalizing still needs (same list as NcpRecord.finalize_missing()).
function ncpMissing(r) {
  return [
    !r.weight_kg && 'weight', !r.height_cm && 'height', !r.pes_problem && 'PES problem', !r.pes_etiology && 'etiology',
    !r.pes_signs && 'signs and symptoms', !r.diet_prescription && 'diet prescription', !r.target_kcal && 'TER',
    r.is_follow_up && !r.goal_status && 'goal status',
  ].filter(Boolean)
}
// Oldest first to number the follow-ups and get the weight change since the
// previous record, then newest first for the timeline (drafts on top).
const ncpTimeline = computed(() => {
  const asc = [...ncpRecords.value].sort((a, b) => String(a.created_at).localeCompare(String(b.created_at)))
  let n = 0
  let prevWeight = null
  const out = asc.map((r) => {
    const kindLabel = r.is_follow_up ? `Follow-up #${++n}` : 'Initial record'
    const w = r.weight_kg != null ? Number(r.weight_kg) : null
    const weightChange = w != null && prevWeight != null ? w - prevWeight : null
    if (w != null && r.status === 'completed') prevWeight = w
    return { ...r, kindLabel, weightChange, missing: ncpMissing(r) }
  })
  return out.reverse().sort((a, b) => (a.status === 'completed') - (b.status === 'completed'))
})

/* ---------- discharge ---------- */
const summaryId = ref(null) // consultation summary pop-up
const showDischarge = ref(false)
function onDischarged() {
  showDischarge.value = false
  toast.success('Patient discharged. We emailed them.')
  load()
}

/* ---------- trends: one chart, switch the measurement ---------- */
// Points come from the screening (weight/BMI), progress records and finalized
// NCP records (their assessment + lipid "other measurements"). One point per
// date per line — a progress record wins over an NCP record on the same day.
const METRICS = [
  { key: 'weight', label: 'Weight', unit: 'kg', decimals: 1 },
  { key: 'bmi', label: 'BMI', unit: '', decimals: 1, refLines: [{ value: 23, label: 'Normal < 23' }] },
  { key: 'bp', label: 'Blood pressure', unit: 'mmHg', decimals: 0, refLines: [{ value: 140, label: '140' }] },
  { key: 'glucose', label: 'Glucose', unit: 'mg/dL', decimals: 0, refLines: [{ value: 100, label: 'Fasting 100' }] },
  { key: 'hba1c', label: 'HbA1c', unit: '%', decimals: 1, refLines: [{ value: 6.5, label: '6.5%' }] },
  { key: 'lipids', label: 'Lipids', unit: 'mg/dL', decimals: 0 },
]
const LIPIDS = [['total', 'Total cholesterol', /total cholesterol|^cholesterol/i], ['ldl', 'LDL', /\bldl\b/i], ['hdl', 'HDL', /\bhdl\b/i], ['tg', 'Triglycerides', /triglyceride/i]]
const metricSeries = computed(() => {
  const out = { weight: [{ key: 'w', label: 'Weight', pts: {} }], bmi: [{ key: 'b', label: 'BMI', pts: {} }],
    bp: [{ key: 'sys', label: 'Systolic', pts: {} }, { key: 'dia', label: 'Diastolic', pts: {} }],
    glucose: [{ key: 'g', label: 'Fasting glucose', pts: {} }], hba1c: [{ key: 'a', label: 'HbA1c', pts: {} }],
    lipids: LIPIDS.map(([key, label]) => ({ key, label, pts: {} })) }
  const put = (m, i, date, v, note, override = true) => {
    if (v == null || v === '' || Number.isNaN(Number(v))) return
    if (!override && out[m][i].pts[date]) return
    out[m][i].pts[date] = { date, value: Number(v), note }
  }
  const add = (r, date, note, override) => {
    put('weight', 0, date, r.weight_kg, note, override)
    put('bmi', 0, date, r.bmi, note, override)
    if (r.blood_pressure) {
      const [sys, dia] = String(r.blood_pressure).split('/')
      put('bp', 0, date, sys, note, override)
      put('bp', 1, date, dia, note, override)
    }
    put('glucose', 0, date, r.blood_glucose, note, override)
    put('hba1c', 0, date, r.hba1c, note, override)
  }
  if (s.value?.screening) {
    const sc = s.value.screening
    add({ weight_kg: sc.weight_kg, bmi: sc.bmi }, sc.date.slice(0, 10), 'screening', false)
  }
  for (const r of ncpRecords.value.filter(r => r.status === 'completed')) {
    add(r, r.encounter_date, 'NCP record', false)
    for (const e of r.assessment_extra || []) {
      const i = LIPIDS.findIndex(([, , re]) => re.test(e.label))
      if (i >= 0) put('lipids', i, r.encounter_date, e.value, 'NCP record')
    }
  }
  for (const r of s.value?.progress || []) add(r, r.record_date, 'progress record', true)
  const result = {}
  for (const [k, lines] of Object.entries(out)) {
    result[k] = lines.map(l => ({ key: l.key, label: l.label, points: Object.values(l.pts).sort((a, b) => a.date.localeCompare(b.date)) }))
  }
  return result
})
// Every measurement with at least one reading gets a card; the rest are listed
// by name. Change is first to latest reading of the main line.
const trends = computed(() => {
  const shown = []
  const none = []
  for (const def of METRICS) {
    const series = metricSeries.value[def.key].filter(l => l.points.length)
    if (!series.length) { none.push(def.label === 'BMI' || def.label === 'HbA1c' ? def.label : def.label.toLowerCase()); continue }
    const main = series[0].points
    const last = main[main.length - 1]
    const fmtV = v => `${Number(v).toFixed(def.decimals)}${def.unit ? ` ${def.unit}` : ''}`
    const latest = def.key === 'bp' && series[1]?.points.length
      ? `${last.value}/${series[1].points[series[1].points.length - 1].value} mmHg`
      : series.length > 1 ? `${series.length} values` : fmtV(last.value)
    let sub = `${shortDate(last.date)}, from the ${last.note}`
    if (main.length >= 2) {
      const ch = last.value - main[0].value
      const sign = ch > 0 ? '+' : ch < 0 ? '−' : ''
      sub = `${sign}${Math.abs(ch).toFixed(def.decimals)}${def.unit ? ` ${def.unit}` : ''}${series.length > 1 ? ` ${series[0].label.toLowerCase()}` : ''} since ${shortDate(main[0].date)}`
    }
    shown.push({ key: def.key, label: def.label, unit: def.unit, decimals: def.decimals, refLines: def.refLines || [],
      series, latest, sub, hasTrend: series.some(l => l.points.length >= 2) })
  }
  return { shown, none }
})

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// the header's meta line as separate pieces (age, sex, conditions) for dot separators
const metaParts = computed(() => (metaLine.value ? metaLine.value.split(', ') : []))
// care process: an icon per step, and which step comes next (the first one not done)
const STEP_ICONS = [
  '<rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6M9 17.5h3" />',
  '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" />',
  '<path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" />',
  '<path d="M17 2l4 4-4 4" /><path d="M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4" /><path d="M21 13v2a3 3 0 0 1-3 3H3" />',
]
// screening symptoms as tags (the text is comma-separated)
const symptomList = computed(() => String(s.value?.screening?.symptoms || '').split(',').map(x => x.trim()).filter(Boolean))
// NCP timeline: a calendar-style date block (month, day, year)
function dateParts(d) {
  const dt = d ? new Date(d) : null
  if (!dt || Number.isNaN(dt.getTime())) return { m: '', d: '—', y: '' }
  return { m: dt.toLocaleDateString('en-PH', { month: 'short' }).toUpperCase(), d: dt.getDate(), y: dt.getFullYear() }
}
const nextStepIndex = computed(() => (p.value ? stageSteps.value.findIndex(st => st.state !== 'done') : -1))

// meal plan tab: share of calories per macro, and the 14-day summary
const macroPct = computed(() => {
  const m = s.value?.meal_plan
  const kcal = Number(m?.target_kcal) || 0
  const share = (g, perGram) => (kcal && Number(g) ? Math.round((Number(g) * perGram / kcal) * 100) : 0)
  return { c: share(m?.target_carb_g, 4), p: share(m?.target_protein_g, 4), f: share(m?.target_fat_g, 9) }
})
const adhSummary = computed(() => {
  const days = s.value?.adherence_days || []
  const rated = days.filter(d => d.followed_pct != null)
  return {
    avg: rated.length ? Math.round(rated.reduce((t, d) => t + d.followed_pct, 0) / rated.length) : null,
    rated: rated.length,
    logged: days.reduce((t, d) => t + (d.logged || 0), 0),
  }
})
// meal logs: the first three on the tab; "See all" opens a full-screen list
const LOGS_FIRST = 3
const showAllLogs = ref(false)
const visibleLogs = computed(() => (s.value?.recent_logs || []).slice(0, LOGS_FIRST))
const LOG_FILTERS = [{ key: 'all', label: 'All' }, { key: 'todo', label: 'To review' }, { key: 'rated', label: 'Rated' }]
const logFilter = ref('all')
const filteredLogs = computed(() => {
  const logs = s.value?.recent_logs || []
  if (logFilter.value === 'todo') return logs.filter(l => !l.status)
  if (logFilter.value === 'rated') return logs.filter(l => l.status)
  return logs
})
// a link to a log further down the list (?log=) opens the full view so it can be shown
watch([() => route.query.log, () => s.value], ([log]) => {
  if (!log) return
  const i = (s.value?.recent_logs || []).findIndex(l => l.id === Number(log))
  if (i >= LOGS_FIRST) { logFilter.value = 'all'; showAllLogs.value = true }
}, { immediate: true })
// full view: Escape closes it (the photo first, if open); the page behind doesn't scroll
function onLogsKey(e) {
  if (e.key !== 'Escape' || !showAllLogs.value) return
  if (photoLog.value) return
  showAllLogs.value = false
}
onMounted(() => document.addEventListener('keydown', onLogsKey))
onUnmounted(() => { document.removeEventListener('keydown', onLogsKey); document.body.style.overflow = '' })
watch(showAllLogs, (open) => { document.body.style.overflow = open ? 'hidden' : '' })
// progress tab: an icon and colour per measurement, and the four main numbers
const PG_ICON = {
  weight: '<path d="M5 21h14a1 1 0 0 0 1-1l-1.5-13a1 1 0 0 0-1-1h-11a1 1 0 0 0-1 1L4 20a1 1 0 0 0 1 1z" /><path d="M12 6V3M9.5 12a2.5 2.5 0 0 1 5 0M12 12l1.5-2" />',
  bmi: '<circle cx="12" cy="4.5" r="2" /><path d="M8 22l1-8-3-1 2-6h8l2 6-3 1 1 8" />',
  bp: '<path d="M12 20s-7.5-4.6-9.2-9.3C1.7 7.4 3.8 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.2 0 5.3 2.9 4.2 6.2C19.5 15.4 12 20 12 20z" />',
  glucose: '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" />',
  hba1c: '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3" />',
  lipids: '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3" />',
}
const PG_TONE = { weight: 'g', bmi: 'y', bp: 'r', glucose: 'b', hba1c: 'v', lipids: 'v' }
const trendPoints = t => t.series[0]?.points.length || 0
const pgSummary = computed(() => ['weight', 'bmi', 'bp', 'glucose'].map((key) => {
  const def = METRICS.find(m => m.key === key)
  const t = trends.value.shown.find(x => x.key === key)
  if (!t) return { key, label: def.label, value: '' }
  const pts = t.series[0].points
  let pill = ''
  let pillTone = 'flat'
  if (key === 'bmi' && p.value?.progress?.bmi_class) { pill = p.value.progress.bmi_class; pillTone = 'ok' }
  else if (pts.length >= 2 && key !== 'bp') {
    const ch = pts[pts.length - 1].value - pts[0].value
    pill = Math.abs(ch) < 0.05 ? 'No change' : `${ch > 0 ? '+' : '−'}${Math.abs(ch).toFixed(def.decimals)}${def.unit ? ` ${def.unit}` : ''}`
  } else pill = shortDate(pts[pts.length - 1].date)
  return { key, label: def.label, value: t.latest, pill, pillTone }
}))
// consultations tab: list grouped by day (Philippine date), newest/soonest order kept
function byDay(list) {
  const groups = []
  for (const a of list || []) {
    const key = new Date(a.scheduled_at).toLocaleDateString('en-CA', PH)
    let g = groups.find(x => x.key === key)
    if (!g) {
      g = {
        key,
        label: new Date(a.scheduled_at).toLocaleDateString('en-US', { ...PH, weekday: 'long' }),
        date: new Date(a.scheduled_at).toLocaleDateString('en-US', { ...PH, month: 'short', day: 'numeric', year: 'numeric' }),
        items: [],
      }
      groups.push(g)
    }
    g.items.push(a)
  }
  return groups
}
</script>

<style scoped>
.row-flash td { background: #e3efe7; }
@media (prefers-reduced-motion: no-preference) {
  .row-flash td { transition: background 0.6s ease; }
}
.crumb { font-size: 0.8rem; color: #8a9a8a; margin: 0 0 12px; }
.crumb a { color: #1f6f46; text-decoration: none; font-weight: 600; }

/* header */
.patient-head {
  padding: 20px 22px; margin-bottom: 16px;
  /* the same dark-green shadow, spread evenly around the whole card */
  box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
}
.ph-top { display: flex; justify-content: space-between; align-items: center; gap: 18px; flex-wrap: wrap; }
.ph-who { display: flex; gap: 16px; align-items: center; min-width: 0; }
.ph-avatar { width: 56px; height: 56px; border-radius: 50%; background: #004D3A; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem; flex-shrink: 0; object-fit: cover; }
.ph-info { min-width: 0; }
.ph-name { font-family: 'Playfair Display', serif; font-size: 1.5rem; color: #1a3a1a; margin: 0 0 2px; line-height: 1.2; }
.ph-meta { font-size: 0.88rem; color: #4a5a4a; margin: 0 0 6px; }
.ph-status { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 0; }
.ph-pill { font-size: 0.74rem; font-weight: 600; padding: 2px 9px; border-radius: 10px; background: #eceeec; color: #5a6a5a; }
.ph-pill.active { background: #e2f2e7; color: #1f6f46; }
.ph-pill.pending { background: #fdf1d6; color: #8a6a1a; }
.ph-since { font-size: 0.8rem; color: #7a8a7a; }
.ph-actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.ph-btn { position: relative; display: inline-flex; align-items: center; gap: 6px; }
.ph-badge { min-width: 18px; height: 18px; padding: 0 5px; border-radius: 9px; background: #D4A017; color: #1a3a1a; font-size: 0.68rem; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }
.more-wrap { position: relative; }
.more-btn { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 8px; background: #e3efe7; color: #0a4a37; cursor: pointer; }
.more-btn:hover { background: #d3e7da; }
.more-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.more-menu { position: absolute; right: 0; top: calc(100% + 6px); min-width: 200px; background: #fff; border: 1px solid #e3e8e3; border-radius: 10px; box-shadow: 0 8px 24px rgba(20, 40, 20, 0.12); padding: 6px; z-index: 30; }
.more-item { display: block; width: 100%; text-align: left; background: none; border: none; border-radius: 6px; padding: 9px 10px; font-family: inherit; font-size: 0.86rem; cursor: pointer; color: #1a3a1a; }
.more-item:hover, .more-item:focus-visible { background: #f6f8f6; outline: none; }
.more-item.danger { color: #b23b2e; }
.more-item.danger:hover { background: #fdf0ee; }
.ph-allergy { display: flex; width: fit-content; max-width: 100%; align-items: flex-start; gap: 8px; margin: 16px 0 0; padding: 10px 12px; border-radius: 8px; background: #fdecec; color: #8f2a20; font-size: 0.86rem; line-height: 1.45; }
.ph-allergy svg { flex-shrink: 0; margin-top: 2px; }

/* every panel on the chart (tabs included, also inside child components like
   the Lab results tab): the light card shadow; the header keeps the stronger one */
.nm-page :deep(.nm-panel) { box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.nm-page .patient-head { box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22); }

/* header = the dashboard's green banner (same gradient as .nm-hero), for one
   look across the RND's main pages */
.nm-page .patient-head { background: linear-gradient(135deg, #00382a 0%, #005a42 100%); border: none; color: #fff; }
.patient-head .ph-avatar { background: #D4A017; color: #1a3a1a; }
.patient-head .ph-name { color: #fff; }
.patient-head .ph-meta { color: #cfe0d5; }
.patient-head .ph-since { color: rgba(255, 255, 255, 0.7); }
.patient-head .ph-pill { background: rgba(255, 255, 255, 0.14); color: #fff; }
.patient-head .ph-pill.active { background: rgba(191, 232, 207, 0.18); color: #bfe8cf; }
.patient-head .ph-pill.pending { background: rgba(212, 160, 23, 0.22); color: #f3d27a; }
.patient-head .ph-btn, .patient-head .more-btn {
  background: rgba(255, 255, 255, 0.14); border: none; color: #fff;
}
.patient-head .ph-btn:hover, .patient-head .more-btn:hover { background: rgba(255, 255, 255, 0.22); }
.patient-head .ph-btn:focus-visible, .patient-head .more-btn:focus-visible { outline: 2px solid #f3d27a; outline-offset: 2px; }
/* allergy stays solid red on the green: the most visible thing in the header */
.patient-head .ph-allergy { background: #fdecec; color: #8f2a20; }

/* overview figures: one panel (same treatment as Earnings, NCP Records, Appointments) */
.figures { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); padding: 0; overflow: hidden; margin-bottom: 16px; }
.fig { border-left: 1px solid #eef1ee; padding: 16px 20px; min-width: 0; }
.fig:first-child { border-left: none; }
.fig-label { font-size: 0.8rem; font-weight: 600; color: #4a5a4a; margin: 0 0 4px; }
.fig-value { font-family: 'Playfair Display', serif; font-size: 1.55rem; font-weight: 700; line-height: 1.15; color: #1a3a1a; margin: 0; font-variant-numeric: tabular-nums lining-nums; }
.fig-note { font-size: 0.76rem; color: #7a8a7a; margin: 4px 0 0; }
.fig.risk .fig-value { color: #b23b2e; }

.tabs { margin: 0 0 18px; }
.nm-page > .nm-panel { margin-bottom: 16px; }
.right { text-align: right; }

.attention { padding: 6px 18px; margin-bottom: 16px; }
.alert { display: flex; gap: 12px; align-items: center; padding: 10px 0; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.alert:first-child { border-top: none; }
.alert-icon { width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #e3edf7; color: #2f6fa8; }
.alert.critical .alert-icon { background: #fdecec; color: #a12525; }
.alert.warning .alert-icon { background: #fdf1d6; color: #b8860b; }
.alert-title { flex: 1; min-width: 160px; margin: 0; font-size: 0.86rem; font-weight: 600; color: #1a3a1a; }

.stepper { list-style: none; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; padding: 0; margin: 16px 0 0; }
.stepper li { position: relative; display: flex; flex-direction: column; gap: 2px; padding-top: 30px; }
.stepper li::before { content: ''; position: absolute; top: 11px; left: 26px; right: -8px; height: 2px; background: #e3e8e3; }
.stepper li:last-child::before { display: none; }
.stepper li.done::before { background: #1f8f5c; }
.dot { position: absolute; top: 0; left: 0; width: 24px; height: 24px; border-radius: 50%; border: 2px solid #d5dad5; background: #fff; display: flex; align-items: center; justify-content: center; color: #fff; }
.stepper li.done .dot { background: #1f8f5c; border-color: #1f8f5c; }
.stepper li.current .dot { border-color: #D4A017; background: #fdf1d6; }
.st-label { font-size: 0.84rem; font-weight: 700; color: #1a3a1a; }
.st-sub { font-size: 0.74rem; color: #8a9a8a; }

.pes { margin-top: 12px; }
.pes p { margin: 0; font-size: 0.86rem; color: #2a3a2a; line-height: 1.55; }
.k { display: block; font-size: 0.78rem; font-weight: 600; color: #4a5a4a; margin: 0 0 3px; }
.targets { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 14px; border: 1px solid #eef1ee; border-radius: 10px; background: #fbfcfa; }
.targets div { padding: 10px 12px; display: flex; flex-direction: column; gap: 2px; border-left: 1px solid #eef1ee; }
.targets div:first-child { border-left: none; }
.targets strong { font-size: 0.98rem; color: #1a3a1a; font-variant-numeric: tabular-nums; }
.targets span { font-size: 0.74rem; color: #7a8a7a; }
.targets-note { font-size: 0.74rem; color: #8a9a8a; margin: 6px 0 0; }

.facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 16px; margin: 12px 0 0; }
.facts.one { grid-template-columns: minmax(0, 1fr); gap: 0; }
.facts.one div { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-top: 1px solid #f0f2f0; }
.facts.one div:first-child { border-top: none; }
.facts dt { font-size: 0.74rem; color: #8a9a8a; margin: 0; }
.facts dd { margin: 0; font-size: 0.86rem; font-weight: 600; color: #1a3a1a; overflow-wrap: anywhere; }
.facts.one dd { text-align: right; }
.facts dd small { font-weight: 500; color: #6a7a6a; }
.facts dd small.short-note { display: block; margin-top: 3px; color: #8a5a10; line-height: 1.4; }
.facts dd.warn { color: #a12525; }
.symptoms { margin: 12px 0 0; font-size: 0.84rem; color: #3a4a3a; line-height: 1.5; }
.big-when { font-size: 0.96rem; font-weight: 700; color: #1a3a1a; margin: 6px 0 2px; }
.pills { margin: 8px 0 10px; }
.labs-new { display: flex; align-items: center; gap: 6px; font-size: 0.84rem; font-weight: 700; color: #8a5a00; margin: 0 0 6px; }
.private-note { display: flex; gap: 6px; align-items: baseline; margin: 10px 0 0; font-size: 0.8rem; color: #5a6a5a; background: #fafbfa; border-radius: 8px; padding: 8px 10px; }
.note-cell { max-width: 260px; color: #5a6a5a; overflow-wrap: anywhere; }
.photo-link { margin-left: 8px; white-space: nowrap; }
.to-review { color: #a07a10; margin-left: 4px; }

/* mini adherence chart */
.mini-chart { margin-top: 4px; }
.mc-plot { position: relative; height: 140px; margin-left: 34px; }
.mc-grid { position: absolute; left: 0; right: 0; border-top: 1px solid #eef1ee; }
.mc-grid span { position: absolute; left: -34px; top: -8px; width: 28px; text-align: right; font-size: 0.68rem; color: #9aaa9a; }
.mc-goal { position: absolute; left: 0; right: 0; border-top: 1px solid #8a9a8a; }
.mc-goal span { position: absolute; right: 0; top: -17px; font-size: 0.68rem; font-weight: 600; color: #6a7a6a; background: #fff; padding: 0 4px; }
.mc-cols { position: absolute; inset: 0; display: flex; gap: 2px; }
.mc-col { flex: 1; position: relative; display: flex; align-items: flex-end; justify-content: center; outline: none; }
.mc-col:hover, .mc-col:focus-visible { background: rgba(31, 143, 92, 0.05); border-radius: 4px; }
.mc-bar { width: 18px; max-width: 70%; background: #a8d8bf; border-radius: 4px 4px 0 0; }
.mc-bar.today { background: #1f8f5c; }
.mc-none { font-size: 0.8rem; color: #b0bab0; }
.mc-x { display: flex; gap: 2px; margin-left: 34px; border-top: 1px solid #dfe5df; padding-top: 6px; }
.mc-x span { flex: 1; text-align: center; font-size: 0.68rem; color: #8a9a8a; white-space: nowrap; }
.tip { position: absolute; bottom: calc(100% - 8px); left: 50%; transform: translateX(-50%); background: #1a3a1a; color: #fff; border-radius: 8px; padding: 7px 10px; font-size: 0.74rem; white-space: nowrap; display: flex; flex-direction: column; gap: 2px; z-index: 5; pointer-events: none; box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15); }
.tip.left { left: auto; right: 0; transform: none; }
.tip.right { left: 0; transform: none; }
.tip-muted { color: #b9cdbf; }

/* weight chart */
.nm-panel-head > div:first-child { flex: 1 1 240px; min-width: 0; }

/* progress form */

/* consultations */
.appt-row { display: flex; gap: 14px; align-items: center; padding: 12px 0; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.appt-row:first-of-type { border-top: none; }
.appt-row.past { opacity: 0.85; }
.appt-date { width: 48px; height: 52px; border-radius: 10px; background: #eef3ec; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; }
.appt-row.past .appt-date { background: #f4f5f4; }
.ad-day { font-size: 1.1rem; font-weight: 700; color: #1a3a1a; line-height: 1; }
.ad-mon { font-size: 0.72rem; font-weight: 600; color: #6a7a6a; }
.appt-main { flex: 1; min-width: 180px; }
.appt-end { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }

@media (max-width: 900px) {
  .figures { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fig:nth-child(3) { border-left: none; }
  .fig:nth-child(n+3) { border-top: 1px solid #eef1ee; }
}
@media (max-width: 640px) {
  .stepper { grid-template-columns: repeat(2, minmax(0, 1fr)); row-gap: 14px; }
  .stepper li:nth-child(2)::before { display: none; }
  .targets { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .facts { grid-template-columns: minmax(0, 1fr); }
  .patient-head { padding: 16px; }
  .ph-actions { width: 100%; }
  .ph-actions > .nm-btn-gold { flex: 1 1 100%; justify-content: center; text-align: center; }
  .ph-actions > .ph-btn { flex: 1 1 0; min-width: 0; justify-content: center; white-space: nowrap; }
  .fig { padding: 12px 16px; }
  .fig-value { font-size: 1.25rem; }
  .targets div:nth-child(3) { border-left: none; }
  .targets div:nth-child(n+3) { border-top: 1px solid #eef1ee; }
    .mc-bar { width: 10px; }
  .mc-x span { font-size: 0.6rem; }
}
.nowrap { white-space: nowrap; }
/* consultations tab */
.cs-sec { margin-top: 18px; }
.cs-sec:first-of-type { margin-top: 10px; }
.cs-title { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0 0 8px; }
.cs-card { display: flex; align-items: center; gap: 14px; padding: 12px 14px; border: 1px solid #eef1ee; border-radius: 10px; margin-bottom: 8px; flex-wrap: wrap; }
.cs-time { display: block; }
.cs-reason { display: block; margin-top: 4px; max-width: 32ch; white-space: normal; }
.cs-ok { display: inline-flex; align-items: center; gap: 4px; color: #1f7a4d; font-weight: 600; }
.cs-none { color: #a07400; font-weight: 600; }
.cs-draft { color: #1f6f46; font-weight: 600; border: 1.5px dashed #3f9a6b; border-radius: 10px; padding: 1px 8px; font-size: 0.8rem; }
.cs-table td { vertical-align: top; }
/* NCP records timeline */
.ncp-tl { list-style: none; margin: 16px 0 0; padding: 0; }
.tl-item { position: relative; display: flex; gap: 14px; padding-bottom: 18px; }
.tl-item:last-child { padding-bottom: 0; }
.tl-item:not(:last-child)::after { content: ''; position: absolute; left: 6px; top: 18px; bottom: 0; width: 2px; background: #e3e9e4; }
.tl-dot { width: 14px; height: 14px; border-radius: 50%; margin-top: 3px; flex-shrink: 0; background: #1f8f5c; position: relative; z-index: 1; box-shadow: 0 0 0 3px #fff; }
.tl-item.draft .tl-dot { background: #fff; border: 2px solid #3f9a6b; }
.tl-body { flex: 1; min-width: 0; }
/* unfinished, not a problem: a white card with a dashed green border */
.tl-item.draft .tl-body { background: #fff; border: 1.5px dashed #3f9a6b; border-radius: 10px; padding: 12px 14px; margin-top: -4px; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.tl-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.tl-kind { font-size: 0.95rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.tl-kind.follow { color: #a07400; }
.tl-date { font-size: 0.8rem; color: #7a8a7a; margin: 2px 0 8px; }
.tl-k { display: inline-block; min-width: 72px; font-size: 0.78rem; font-weight: 600; color: #6a7a6a; }
.tl-dx { font-size: 0.88rem; color: #1a3a1a; margin: 0 0 6px; overflow-wrap: anywhere; }
.tl-facts { display: flex; flex-wrap: wrap; gap: 6px 24px; font-size: 0.86rem; color: #1a3a1a; margin: 0; font-variant-numeric: tabular-nums; }
.tl-facts .tl-k { min-width: 0; margin-right: 8px; }
.tl-facts small { color: #7a8a7a; }
.tl-facts small.down { color: #1f7a4d; }
.tl-missing { font-size: 0.84rem; color: #3a4a3a; margin: 8px 0 0; }
.tl-missing strong { color: #1a3a1a; }
.tl-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
/* progress trends: one card per measurement */
.trend-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-top: 14px; }
.trend-card { border: 1px solid #eef1ee; border-radius: 10px; padding: 14px 16px 10px; min-width: 0; background: #fff; }
.tc-head { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.tc-title { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.tc-latest { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #1a3a1a; font-variant-numeric: tabular-nums lining-nums; white-space: nowrap; }
.tc-sub { font-size: 0.78rem; color: #7a8a7a; margin: 2px 0 8px; }
.tc-one { font-size: 0.82rem; color: #8a9a8a; margin: 12px 0 6px; }
.tc-none { font-size: 0.8rem; color: #8a9a8a; margin: 14px 0 0; }
@media (max-width: 900px) { .trend-grid { grid-template-columns: minmax(0, 1fr); } }
.self-tag { margin-left: 6px; font-size: 0.62rem; }

.dr-banner { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; background: #fdf8e8; border-color: #f0e2b0; }

/* =========================================================
   REFINED LOOK (UI only): brand #004D3A / #EFBF04 / white,
   Playfair Display headings, DM Sans body, the client
   dashboard's card shadow
   ========================================================= */
.nm-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }
.crumb { display: flex; align-items: center; gap: 6px; margin: 0 0 14px; font-size: 13.5px; color: #6B7D73; }
.crumb a { color: #004D3A; font-weight: 700; }

/* every card: the client dashboard shadow */
.nm-page :deep(.nm-panel) {
  border-radius: 20px;
  border: 1px solid #E1E7E3;
  padding: 22px 24px;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22);
}
.nm-page :deep(.nm-panel-title) { font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #0E3A2C; margin: 0; }
.nm-page :deep(.nm-panel-sub) { font-size: 13px; color: #6B7D73; margin: 3px 0 0; }
.nm-page :deep(.nm-panel-link) { display: inline-flex; align-items: center; height: 34px; padding: 0 12px; border-radius: 10px; background: #F1F6F2; border: 1px solid #DCE8E0; color: #004D3A; font-size: 13px; font-weight: 700; text-decoration: none; white-space: nowrap; cursor: pointer; }
.nm-page :deep(.nm-panel-link:hover) { background: #E3EFE7; }

/* ---------- HEADER ---------- */
.nm-page .patient-head {
  position: relative;
  overflow: hidden;
  padding: 24px 28px;
  margin-bottom: 18px;
  border: none;
  border-radius: 24px;
  color: #FFFFFF;
  background:
    radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%),
    linear-gradient(115deg, #035A45 0%, #004D3A 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.ph-plate { position: absolute; right: -60px; bottom: -140px; width: 360px; height: 360px; object-fit: cover; border-radius: 50%; opacity: 0.3; pointer-events: none; }
.ph-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004D3A 0%, #004D3A 55%, rgba(0, 77, 58, 0.6) 80%, rgba(0, 77, 58, 0.3) 100%); pointer-events: none; }
.ph-top,
.patient-head .ph-allergy { position: relative; z-index: 1; }
.ph-who { gap: 18px; }
.patient-head .ph-avatar { width: 76px; height: 76px; font-family: 'Playfair Display', Georgia, serif; font-size: 26px; background: linear-gradient(135deg, #F5CB1F, #C49102); color: #004D3A; border: 3px solid #FFFFFF; box-shadow: 0 14px 26px -14px rgba(0, 0, 0, 0.55); }
.patient-head .ph-name { margin: 0 0 4px; font-size: 32px; font-weight: 700; line-height: 1.1; color: #FFFFFF; }
.patient-head .ph-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin: 0; font-size: 15px; font-weight: 500; color: rgba(255, 255, 255, 0.88); }
.ph-meta i { width: 4px; height: 4px; border-radius: 50%; background: rgba(255, 255, 255, 0.45); }
.ph-status { margin-top: 10px; gap: 12px; }
.patient-head .ph-pill { display: inline-flex; align-items: center; gap: 7px; padding: 0; background: none; font-size: 13px; font-weight: 700; color: #FFFFFF; }
.ph-pill b { width: 8px; height: 8px; border-radius: 50%; background: rgba(255, 255, 255, 0.6); }
.patient-head .ph-pill.active { background: none; color: #EFBF04; }
.ph-pill.active b { background: #EFBF04; box-shadow: 0 0 0 4px rgba(239, 191, 4, 0.22); }
.patient-head .ph-pill.pending { background: none; color: #F3D27A; }
.ph-pill.pending b { background: #F3D27A; }
.patient-head .ph-since { padding-left: 12px; border-left: 1px solid rgba(255, 255, 255, 0.25); font-size: 13px; color: rgba(255, 255, 255, 0.7); }
.ph-actions { position: relative; z-index: 2; gap: 8px; }
.patient-head :deep(.nm-btn-gold) { display: inline-flex; align-items: center; height: 44px; padding: 0 18px; border-radius: 12px; background: #EFBF04; color: #004D3A; font-weight: 800; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
.patient-head .ph-btn { height: 44px; padding: 0 16px; border-radius: 12px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.22); font-weight: 800; }
.patient-head .more-btn { width: 44px; height: 44px; border-radius: 12px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.22); }
.ph-badge { background: #EFBF04; color: #004D3A; }
.more-menu { border-radius: 14px; padding: 6px; box-shadow: 0 18px 40px -16px rgba(0, 0, 0, 0.35); }
.more-item { border-radius: 10px; font-size: 14px; font-weight: 600; }
.patient-head .ph-allergy { align-items: center; gap: 10px; margin: 16px 0 0; padding: 6px 16px 6px 6px; border-radius: 999px; background: rgba(255, 255, 255, 0.96); color: #7A1C12; font-size: 13px; line-height: 1.35; box-shadow: 0 8px 18px -12px rgba(0, 0, 0, 0.45); }
.ph-allergy-ico { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; background: #B42318; color: #FFFFFF; display: inline-flex; align-items: center; justify-content: center; }
.ph-allergy strong { color: #B42318; }

/* notes under the header */
.nm-page :deep(.nm-note) { border-radius: 16px; padding: 14px 18px; font-size: 14px; }
.dr-banner { background: #FFFAEB; border: 1px solid #F1DE97; }

/* ---------- TABS ---------- */
.nm-page .tabs { display: flex; gap: 4px; width: fit-content; max-width: 100%; margin: 0 0 18px; padding: 5px; overflow-x: auto; border-radius: 999px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 6px 16px -12px rgba(16, 35, 27, 0.3); scrollbar-width: none; }
.nm-page .tabs::-webkit-scrollbar { display: none; }
.nm-page .tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 40px; padding: 0 18px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 14px; font-weight: 700; color: #3E5046; white-space: nowrap; cursor: pointer; }
.nm-page .tabs .nm-tab:hover:not(.active) { color: #004D3A; background: #F3F6F4; }
.nm-page .tabs .nm-tab.active { background: #004D3A; color: #FFFFFF; }
.nm-page .tabs .nm-count { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: #EEF4F0; color: #004D3A; font-size: 11.5px; display: inline-flex; align-items: center; justify-content: center; }
.nm-page .tabs .nm-tab.active .nm-count { background: rgba(255, 255, 255, 0.18); color: #FFFFFF; }

/* ---------- ALERTS ---------- */
.attention { padding: 8px 18px !important; }
.alert-icon { width: 34px; height: 34px; border-radius: 11px; }
.alert-title { font-size: 14px; }

/* ---------- FIGURES: four cards ---------- */
.figures { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-bottom: 18px; padding: 0; overflow: visible; }
.fig { position: relative; overflow: hidden; min-width: 0; padding: 20px 22px 18px; border: 1px solid #E1E7E3; border-left: 1px solid #E1E7E3; border-radius: 20px; background: #FFFFFF; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); }
.fig:first-child { border-left: 1px solid #E1E7E3; }
.fig::after { content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 4px; background: var(--c, #004D3A); opacity: .85; }
.fig-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 0 0 8px; }
.fig-label { font-size: 13.5px; font-weight: 700; color: #3E5046; margin: 0; }
.fig-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; }
.fig-value { font-size: 36px; line-height: 1; color: #0E3A2C; margin: 0 0 8px; }
.fig-note { font-size: 12px; color: #6B7D73; margin: 2px 0 0; }
.fig.risk .fig-value { color: #B42318; }

/* ---------- PANEL HEADS ---------- */
.pc-head { display: flex; align-items: center; gap: 14px; min-width: 0; }
.pc-head > div { min-width: 0; }
.pc-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 13px; display: inline-flex; align-items: center; justify-content: center; }
.nm-page :deep(.nm-panel-head) { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.nm-col > .nm-panel > .pc-head { margin-bottom: 16px; }

/* empty lines inside cards: a soft dashed box */
.nm-col > .nm-panel > .nm-muted { margin: 4px 0 0 !important; padding: 14px 16px; border-radius: 14px; border: 1.5px dashed #CFDDD4; background: #F8FBF9; font-size: 13.5px; color: #4A5A52; }

/* ---------- CARE PROCESS ---------- */
.stepper { gap: 10px; margin: 6px 0 0; }
.stepper li { align-items: center; text-align: center; padding-top: 56px; gap: 3px; }
.stepper li::before { top: 22px; left: calc(50% + 26px); right: calc(-50% + 26px); height: 3px; border-radius: 3px; background: #E3EBE6; }
.stepper li.done::before { background: #1F9D55; }
.dot { top: 0; left: 50%; width: 46px; height: 46px; margin-left: -23px; border: 2px solid #DCE5DF; color: #8A9A91; }
.stepper li.done .dot { background: #1F9D55; border-color: #1F9D55; color: #FFFFFF; box-shadow: 0 0 0 5px rgba(31, 157, 85, 0.15); }
.stepper li.current .dot { border-color: #EFBF04; background: #FFFAEB; box-shadow: 0 0 0 5px rgba(239, 191, 4, 0.18); }
.stepper li.current .dot::after { content: ''; width: 10px; height: 10px; border-radius: 50%; background: #EFBF04; }
.st-label { font-size: 14px; color: #0E3A2C; }
.st-sub { font-size: 12px; color: #6B7D73; }

/* ---------- PLAN / TARGETS ---------- */
.pes { margin-top: 12px; padding: 12px 14px; border-radius: 14px; background: #F7FAF8; }
.pes p { font-size: 14px; color: #22362C; }
.k { font-size: 12px; font-weight: 800; color: #9A7300; }
.targets { gap: 8px; border: none; background: none; }
.targets div { border: 1px solid #EDF2EE !important; border-radius: 14px; background: #F7FAF8; padding: 12px 14px; }
.targets strong { font-family: 'Playfair Display', Georgia, serif; font-size: 20px; color: #0E3A2C; }

/* ---------- FACTS (screening, progress) ---------- */
.facts:not(.one) { gap: 10px; margin-top: 4px; }
.facts:not(.one) > div { padding: 12px 14px; border-radius: 14px; background: #F7FAF8; border: 1px solid #EDF2EE; }
.facts dt { font-size: 12px; font-weight: 600; color: #6B7D73; }
.facts dd { margin-top: 2px; font-size: 15px; font-weight: 700; color: #0E3A2C; }
.facts dd small { font-size: 12px; color: #1F7A4C; }
.symptoms { margin-top: 14px; padding: 12px 14px; border-radius: 14px; background: #FEF5F4; font-size: 14px; color: #7A1C12; }
.symptoms .k { color: #B42318; }

/* health profile rows */
.facts.one > div { align-items: center; padding: 12px 0; border-top: 1px solid #F0F3F1; }
.facts.one dt { font-size: 13px; }
.facts.one dd { font-size: 14px; }
.facts dd.warn { display: inline-block; padding: 3px 12px; border-radius: 999px; background: #FDECEC; color: #B42318; }

/* next consultation */
.next-body { display: flex; align-items: flex-start; gap: 16px; }
.next-date { flex-shrink: 0; width: 70px; padding: 8px 0 10px; border-radius: 16px; background: #004D3A; color: #FFFFFF; display: flex; flex-direction: column; align-items: center; box-shadow: 0 12px 22px -14px rgba(0, 77, 58, 0.9); }
.next-date small { font-size: 11px; font-weight: 800; color: #EFBF04; }
.next-date strong { font-family: 'Playfair Display', Georgia, serif; font-size: 30px; line-height: 1.1; }
.next-main { flex: 1; min-width: 0; }
.big-when { margin: 0 0 2px; font-size: 16px; font-weight: 800; color: #0E3A2C; }
.pills { margin: 10px 0 10px; }

/* pills + buttons used on this page */
.nm-page :deep(.nm-pill) { display: inline-flex; align-items: center; height: 26px; padding: 0 12px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.nm-page :deep(.nm-btn-dark) { border-radius: 12px; }
.nm-page :deep(.nm-btn-outline) { border-radius: 12px; }

.labs-new { padding: 10px 12px; border-radius: 12px; background: #FFFAEB; color: #8A6400; }
.private-note { border-radius: 12px; background: #F7FAF8; }

/* other tabs: softer tables + timeline */
.nm-page :deep(.nm-table-wrap) { border: 1px solid #E7EDE9; border-radius: 16px; overflow: auto; }
.nm-page :deep(.nm-table th) { background: #F3F8F5; font-size: 12px; font-weight: 800; color: #4A5A52; }
.tl-dot { width: 16px; height: 16px; background: #1F9D55; }
.tl-item:not(:last-child)::after { left: 7px; }
.tl-body { padding: 14px 16px; border-radius: 16px; background: #F7FAF8; border: 1px solid #EDF2EE; }
.tl-item.draft .tl-body { background: #FFFFFF; border-radius: 16px; }
.trend-card { border-radius: 16px; border-color: #E7EDE9; background: #FBFCFB; }
.cs-card { border-radius: 16px; border-color: #E7EDE9; background: #F7FAF8; }
.appt-date { border-radius: 14px; background: #004D3A; }
.ad-day { color: #FFFFFF; font-family: 'Playfair Display', Georgia, serif; }
.ad-mon { color: #EFBF04; }
.mc-goal { border-top: 2px dashed #EFBF04; }
.mc-goal span { color: #9A7300; background: #FDF6DA; border-radius: 999px; padding: 1px 8px; }
.mc-bar { border-radius: 6px 6px 2px 2px; }
.mc-bar.today { background: linear-gradient(180deg, #1F9D55, #004D3A); }

/* ---------- SMALLER SCREENS ---------- */
@media (max-width: 1100px) {
  .figures { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fig:nth-child(n + 3) { border-top: 1px solid #E1E7E3; }
}
@media (max-width: 900px) {
  .nm-page { padding-bottom: 96px; }
}
@media (max-width: 640px) {
  .nm-page .patient-head { padding: 18px 16px; border-radius: 22px; }
  .ph-plate { display: none; }
  .ph-who { align-items: flex-start; gap: 12px; }
  .patient-head .ph-avatar { width: 60px; height: 60px; font-size: 21px; }
  .patient-head .ph-name { font-size: 24px; }
  .patient-head .ph-meta { font-size: 13.5px; gap: 8px; }
  .patient-head .ph-btn,
  .patient-head :deep(.nm-btn-gold) { height: 42px; }
  .patient-head .ph-allergy { border-radius: 16px; align-items: flex-start; padding: 8px 12px 8px 8px; font-size: 12.5px; }
  .figures { gap: 10px; }
  .fig { padding: 14px 14px 16px; border-radius: 16px; }
  .fig-ico { width: 32px; height: 32px; border-radius: 11px; }
  .fig-ico .ic { width: 16px; height: 16px; }
  .fig-label { font-size: 12px; }
  .fig-value { font-size: 26px; }
  .nm-page :deep(.nm-panel) { padding: 16px; border-radius: 18px; }
  .nm-page :deep(.nm-panel-title) { font-size: 18px; }
  .pc-ico { width: 38px; height: 38px; }
  .stepper { grid-template-columns: 1fr; row-gap: 0; }
  .stepper li { flex-direction: row; flex-wrap: wrap; align-items: center; text-align: left; gap: 2px 12px; min-height: 58px; padding: 6px 0 6px 60px; }
  .stepper li::before { display: block !important; top: 46px; bottom: -12px; left: 22px; right: auto; width: 3px; height: auto; }
  .stepper li:last-child::before { display: none !important; }
  .dot { top: 6px; left: 0; margin-left: 0; }
  .st-sub { flex-basis: 100%; }
  .next-date { width: 60px; }
  .next-date strong { font-size: 24px; }
  .facts.one > div { flex-direction: column; align-items: flex-start; gap: 4px; }
  .facts.one dd { text-align: left; }
}

/* care process, as on the canvas */
.stepper li.next:not(.done) .dot,
.stepper li.current .dot { border-color: #EFBF04; background: #FFFAEB; color: #9A7300; box-shadow: 0 0 0 5px rgba(239, 191, 4, 0.18); }
.stepper li.current .dot::after { display: none; }
.dot { color: #8A9A91; }
.st-next { margin-top: 6px; padding: 2px 10px; border-radius: 999px; background: #FBF3D2; color: #8A6400; font-size: 11px; font-weight: 800; }
.stepper li { padding-top: 58px; }

/* health profile: icon + tags per row */
.hp { margin: 0; display: flex; flex-direction: column; }
.hp-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 0; border-top: 1px solid #F0F3F1; }
.hp-row:first-child { border-top: none; padding-top: 2px; }
.hp-row dt { flex-shrink: 0; display: inline-flex; align-items: center; gap: 10px; margin: 0; font-size: 13.5px; font-weight: 600; color: #6B7D73; }
.hp-row dt .ic { color: #1F7A4D; }
.hp-row dd { margin: 0; min-width: 0; display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px; text-align: right; }
.hp-row dd strong { font-size: 14px; font-weight: 800; color: #0E3A2C; overflow-wrap: anywhere; }
.hp-tag { display: inline-flex; align-items: center; height: 30px; padding: 0 12px; border-radius: 999px; font-size: 13px; font-weight: 700; }
.hp-tag.green { background: #E3EFE7; color: #004D3A; }
.hp-tag.red { background: #FDECEC; color: #B42318; }
.hp-tag.gold { background: #FBF3D2; color: #8A6400; }
.hp-none { font-size: 13.5px; color: #8A9A91; }
@media (max-width: 640px) {
  .st-next { margin-top: 0; }
  .stepper li { padding-top: 6px; }
  .hp-row { flex-direction: column; align-items: flex-start; gap: 6px; }
  .hp-row dd { justify-content: flex-start; text-align: left; }
}

/* screening tiles, as on the canvas */
.facts.sc-tiles { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-top: 4px; }
.sc-tiles > div { display: flex; align-items: center; gap: 12px; min-width: 0; padding: 12px 14px !important; }
.sc-tiles > div > span:last-child { min-width: 0; }
.sc-ico { flex-shrink: 0; width: 38px; height: 38px; border-radius: 12px; background: #FFFFFF; color: #1F5C45; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px -6px rgba(16, 35, 27, 0.3); }
.sc-tiles dd small { margin-left: 2px; font-size: 12px; font-weight: 700; color: #1F7A4C; }
.sc-tiles dd small.short-note { display: block; margin: 3px 0 0; font-weight: 500; color: #8A5A10; }
.sc-sym { margin-top: 16px; }
.sc-sym-k { margin: 0 0 8px; font-size: 12px; font-weight: 800; color: #4A5A52; }
.sc-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.sc-tag { display: inline-flex; align-items: center; min-height: 30px; padding: 4px 12px; border-radius: 999px; background: #FDECEC; color: #B42318; font-size: 13px; font-weight: 700; }

/* ---------- PHONE + TABLET: same pattern as the client pages ---------- */
@media (max-width: 1100px) {
  .nm-page :deep(.nm-grid) { display: grid; grid-template-columns: minmax(0, 1fr); gap: 16px; }
  .facts.sc-tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 900px) {
  .nm-page { padding-bottom: 110px; }
  .ph-top { flex-direction: column; align-items: stretch; gap: 16px; }
  .ph-actions { display: grid; grid-template-columns: 1fr 1fr; width: 100%; }
  .ph-actions > :deep(.nm-btn-gold) { grid-column: 1 / -1; justify-content: center; }
  .ph-actions > .ph-btn { justify-content: center; }
  .ph-actions .more-wrap { position: absolute; top: -66px; right: 0; }
  .nm-page .tabs { width: 100%; border-radius: 16px; }
  .nm-page :deep(.nm-col) { gap: 16px; }
}
@media (max-width: 640px) {
  .ph-actions .more-wrap { top: -64px; }
  .ph-actions .more-btn { width: 38px; height: 38px; }
  .facts.sc-tiles { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 8px; }
  .sc-tiles > div { padding: 10px !important; gap: 10px; }
  .sc-ico { width: 32px; height: 32px; }
  .sc-tiles dd { font-size: 14px; }
  .nm-page .tabs .nm-tab { height: 38px; padding: 0 14px; font-size: 13px; }
  .next-body { gap: 12px; }
}
@media (max-width: 380px) {
  .facts.sc-tiles { grid-template-columns: minmax(0, 1fr); }
}

/* ---------- NCP records tab (UI only): one compact row per record ---------- */
.ncp-count { display: inline-flex; align-items: center; justify-content: center; min-width: 22px; height: 22px; margin-left: 8px; padding: 0 7px; border-radius: 999px; background: #E3EFE7; font-family: 'DM Sans', sans-serif; font-size: 12px; font-weight: 800; color: #004D3A; vertical-align: 4px; }
.ncp-write { display: inline-flex; align-items: center; gap: 6px; }
.nr-list { list-style: none; margin: 20px 0 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
.nr { position: relative; display: flex; align-items: center; gap: 18px; padding: 14px 18px 14px 14px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E8EFEA; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03), 0 12px 26px -18px rgba(0, 77, 58, 0.45); transition: transform 0.15s, box-shadow 0.15s; }
.nr:hover { transform: translateY(-1px); box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03), 0 18px 34px -18px rgba(0, 77, 58, 0.55); }
.nr::before { content: ''; position: absolute; left: 0; top: 18px; bottom: 18px; width: 4px; border-radius: 0 4px 4px 0; background: #1F9D55; }
.nr.draft { background: #FFFDF6; border: 1.5px dashed #E7C65A; box-shadow: none; }
.nr.draft::before { background: #EFBF04; }
.nr-date { flex-shrink: 0; width: 66px; height: 72px; margin-left: 6px; border-radius: 16px; background: linear-gradient(160deg, #035A45, #004D3A); color: #FFFFFF; display: flex; flex-direction: column; align-items: center; justify-content: center; border-bottom: 3px solid #EFBF04; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.85); }
.nr-date small { font-size: 10.5px; font-weight: 800; color: rgba(255, 255, 255, 0.75); }
.nr-date small:first-child { color: #EFBF04; }
.nr-date strong { font-family: 'Playfair Display', serif; font-size: 25px; line-height: 1.1; font-variant-numeric: lining-nums tabular-nums; }
.nr.draft .nr-date { background: #FFF4D6; color: #8A6500; border-bottom-color: #E7C65A; box-shadow: none; }
.nr.draft .nr-date small, .nr.draft .nr-date small:first-child { color: #9A7300; }
.nr-main { flex: 1; min-width: 0; }
.nr-top { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 10px; }
.nr-top h4 { margin: 0; font-family: 'Playfair Display', serif; font-size: 18px; font-weight: 700; letter-spacing: 0.01em; font-variant-numeric: lining-nums; color: #0E3A2C; }
.nr-status { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 800; }
.nr-status.ok { background: #E3F4EA; color: #1F7A4D; }
.nr-status.draft { background: #FFF4D6; color: #8A6500; }
.nr-edited { font-size: 12px; color: #8A9A91; }
.nr-dx { display: flex; align-items: center; gap: 8px; min-width: 0; margin: 6px 0 0; font-size: 13.5px; color: #4A5A52; }
.nr-dx-t { min-width: 0; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.nr-dx-t b { color: #0E3A2C; }
.nr-dx-t.none { color: #8A9A91; font-style: italic; }
.nr-p { flex-shrink: 0; width: 20px; height: 20px; border-radius: 6px; background: #E3EFE7; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; font-family: 'Playfair Display', serif; font-size: 12px; font-weight: 700; }
.nr-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }
.nr-chip { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 10px; border-radius: 999px; background: #F3F7F4; font-size: 12.5px; color: #4A5A52; font-variant-numeric: tabular-nums; }
.nr-chip svg { color: #1F7A4D; }
.nr-chip b { color: #0E3A2C; }
.nr-chip em { margin-left: 2px; padding: 1px 7px; border-radius: 999px; background: #FFFFFF; font-style: normal; font-size: 11px; font-weight: 800; color: #6B7D73; }
.nr-chip em.down { color: #1F7A4D; }
.nr-chip em.up { color: #8A6500; }
.nr.draft .nr-chip { background: #FFFFFF; border: 1px solid #F0E3B5; }
.nr-miss { display: flex; align-items: center; gap: 6px; margin: 8px 0 0; font-size: 12.5px; font-weight: 700; color: #8A6500; }
.nr-acts { flex-shrink: 0; display: flex; align-items: center; gap: 8px; }
.nr-btn { display: inline-flex; align-items: center; gap: 7px; height: 42px; padding: 0 16px; border-radius: 12px; border: 1px solid transparent; font-family: inherit; font-size: 13.5px; font-weight: 800; white-space: nowrap; cursor: pointer; transition: transform 0.15s, background 0.15s; }
.nr-btn:hover { transform: translateY(-1px); }
.nr-btn:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
.nr-btn.dark { background: #004D3A; color: #FFFFFF; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.nr-btn.dark:hover { background: #00382A; }
.nr-btn.soft { background: #FFFFFF; border-color: #DCE8E0; color: #004D3A; }
.nr-btn.soft:hover { background: #F1F6F2; }
.nr-btn.gold { background: #EFBF04; color: #004D3A; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
.nr-btn.gold:hover { background: #F5CB1C; }
.ncp-empty { display: flex; flex-direction: column; align-items: center; gap: 10px; margin-top: 18px; padding: 36px 20px; border-radius: 18px; border: 1.5px dashed #CFDDD4; text-align: center; }
.ncp-empty p { margin: 0; font-size: 14px; font-weight: 700; color: #4A5A52; }
.ncp-hint { display: flex; align-items: center; gap: 10px; margin: 18px 0 0; padding: 12px 14px; border-radius: 14px; background: #F1F6F2; border-left: 3px solid #1F9D55; font-size: 13px; color: #2C4A3C; }
.ncp-hint svg { flex-shrink: 0; color: #004D3A; }
@media (max-width: 760px) {
  .ncp-panel .nm-panel-head { flex-wrap: wrap; }
  .ncp-write { width: 100%; justify-content: center; }
  .nr { flex-wrap: wrap; align-items: flex-start; gap: 12px; padding: 14px; }
  .nr-date { width: 56px; height: 62px; margin-left: 4px; }
  .nr-date strong { font-size: 21px; }
  .nr-main { flex-basis: calc(100% - 80px); }
  .nr-dx { align-items: flex-start; }
  .nr-p { display: none; }
  .nr-dx-t { white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
  .nr-acts { width: 100%; }
  .nr-btn { flex: 1; justify-content: center; }
}

/* =========================================================
   Meal plan tab
   ========================================================= */
.mpx-k { display: flex; align-items: center; gap: 8px; margin: 0 0 4px; font-size: 12px; font-weight: 800; color: #9a7300; }
.mpx-head { align-items: center; gap: 16px; }
.mpx-head > div { flex: 1 1 240px; min-width: 0; }
.mpx-ico { flex-shrink: 0; width: 52px; height: 52px; border-radius: 16px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.mpx-row { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
.mpx-plan .nm-panel-title { font-size: 26px; }
.mpx-pill { display: inline-flex; align-items: center; height: 28px; padding: 0 12px; border-radius: 999px; font-size: 13px; font-weight: 800; background: #f3f6f4; color: #4a5a52; }
.mpx-pill.active { background: #e3f4ea; color: #1f7a4d; }
.mpx-pill.draft { background: #fbf3d2; color: #8a6400; }
.mpx-meta { display: flex; flex-wrap: wrap; gap: 6px 18px; margin-top: 6px; font-size: 14px; color: #4a5a52; }
.mpx-meta span { display: inline-flex; align-items: center; gap: 6px; }
.mpx-meta .ic { color: #1f7a4d; }
.mpx-upd { display: inline-flex; align-items: center; gap: 8px; height: 44px !important; padding: 0 20px !important; border-radius: 12px !important; font-size: 14px !important; }
.mpx-upd .ic { color: #efbf04; }
.targets.mpx-macros { gap: 12px; margin-top: 20px; border: none; border-radius: 0; background: none; }
.mpx-macros > div { flex-direction: row; align-items: center; gap: 14px; padding: 16px 18px; border: 1.5px solid #e6eee9; border-bottom-width: 4px; border-left: 1.5px solid #e6eee9; border-radius: 16px; background: #f7faf8; }
.mpx-macros > div:first-child { border-left: 1.5px solid #e6eee9; }
.mx-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 13px; background: #fff; display: inline-flex; align-items: center; justify-content: center; }
.mpx-macros p { margin: 0; min-width: 0; display: flex; flex-direction: column; }
.mpx-macros p > span { font-size: 13px; font-weight: 700; color: #4a5a52; }
.mpx-macros strong { font-family: 'Playfair Display', Georgia, serif; font-size: 28px; line-height: 1.15; color: #0e3a2c; }
.mpx-macros strong em { margin-left: 4px; font-family: 'DM Sans', sans-serif; font-style: normal; font-size: 14px; font-weight: 700; color: #4a5a52; }
.mpx-macros small { font-size: 12.5px; color: #4a5a52; }
.mpx-macros .k { border-bottom-color: #efbf04 !important; } .mpx-macros .k .mx-ico { color: #9a7300; }
.mpx-macros .c { border-bottom-color: #1f7a4d !important; } .mpx-macros .c .mx-ico { color: #1f7a4d; }
.mpx-macros .p { border-bottom-color: #3b5ba5 !important; } .mpx-macros .p .mx-ico { color: #3b5ba5; }
.mpx-macros .f { border-bottom-color: #c0483a !important; } .mpx-macros .f .mx-ico { color: #c0483a; }
.mpx-split { display: flex; gap: 3px; height: 10px; margin-top: 18px; border-radius: 999px; overflow: hidden; }
.mpx-split .c, .mpx-split-k i.c { background: #1f7a4d; }
.mpx-split .p, .mpx-split-k i.p { background: #3b5ba5; }
.mpx-split .f, .mpx-split-k i.f { background: #c0483a; }
.mpx-split-k { display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 10px 0 0; font-size: 13px; font-weight: 700; color: #3e5046; }
.mpx-split-k span { display: inline-flex; align-items: center; gap: 6px; }
.mpx-split-k i { width: 10px; height: 10px; border-radius: 3px; }

/* adherence: summary | chart */
.nm-panel.mpx-adh { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 28px; }
.mpx-adh .nm-panel-title { font-size: 22px; }
.mpx-big { display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px 10px; margin: 14px 0; }
.mpx-big b { font-family: 'Playfair Display', Georgia, serif; font-size: 52px; line-height: 1; color: #004d3a; }
.mpx-big span { font-size: 13.5px; color: #4a5a52; }
.mpx-facts { list-style: none; margin: 0; padding: 0; }
.mpx-facts li { display: flex; align-items: center; gap: 10px; padding: 9px 0; border-top: 1.5px solid #eef2ef; font-size: 14px; color: #3e5046; }
.mpx-facts li .ic { color: #1f7a4d; }
.mpx-facts li b { margin-left: auto; color: #0e3a2c; }
.mpx-note { display: flex; gap: 8px; margin: 12px 0 0; font-size: 12.5px; line-height: 1.5; color: #4a5a52; }
.mpx-note .ic { margin-top: 1px; color: #3b5ba5; }
.mpx-adh-chart { min-width: 0; padding-left: 28px; border-left: 1.5px solid #eef2ef; display: flex; flex-direction: column; justify-content: center; }
.mpx-empty { margin: 0; padding: 40px 0; text-align: center; }
.mpx-adh .mc-plot { height: 240px; margin-left: 40px; }
.mpx-adh .mc-grid { border-top-color: #eef2ef; }
.mpx-adh .mc-grid span { left: -40px; width: 32px; font-size: 11.5px; font-weight: 700; color: #8a9a91; }
.mpx-adh .mc-goal { z-index: 2; border-top: 2px dashed #efbf04; }
.mpx-adh .mc-goal span { top: -12px; padding: 2px 8px; border-radius: 999px; background: #fbf3d2; color: #8a6400; font-size: 11.5px; font-weight: 800; }
.mpx-adh .mc-cols { gap: 8px; }
.mpx-adh .mc-col { border-radius: 10px; }
.mpx-adh .mc-track { position: absolute; left: 50%; bottom: 0; top: 0; width: 100%; max-width: 34px; transform: translateX(-50%); border-radius: 10px; background: #f3f6f4; }
.mpx-adh .mc-bar { position: relative; z-index: 1; width: 100%; max-width: 34px; border-radius: 10px; background: linear-gradient(180deg, #2e9a62, #1f7a4d); }
.mpx-adh .mc-bar.today { background: linear-gradient(180deg, #035a45, #004d3a); }
.mpx-adh .mc-none { position: relative; z-index: 1; width: 6px; height: 6px; margin-bottom: 8px; border-radius: 50%; background: #c6d3cb; }
.mpx-adh .mc-x { margin-left: 40px; gap: 8px; border-top: none; }
.mpx-adh .mc-x span { font-size: 12px; font-weight: 700; color: #4a5a52; }
.mpx-leg { display: flex; gap: 18px; margin: 12px 0 0 40px; font-size: 12.5px; font-weight: 700; color: #3e5046; }
.mpx-leg span { display: inline-flex; align-items: center; gap: 6px; }
.mpx-leg i { width: 10px; height: 10px; border-radius: 3px; background: #1f7a4d; }
.mpx-leg i.n { border-radius: 50%; background: #c6d3cb; }
.mpx-adh .tip { z-index: 6; }

/* meal logs as cards */
.mpx-logs-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.mpx-logs .nm-panel-title { font-size: 22px; }
.mpx-logs .to-review { flex-shrink: 0; margin: 0; padding: 5px 12px; border-radius: 999px; background: #fbf3d2; color: #8a6400; font-size: 13px; }
.mpx-list { display: flex; flex-direction: column; gap: 10px; }
.mpx-log { display: grid; grid-template-columns: 60px minmax(0, 1fr) auto auto; align-items: center; gap: 18px; padding: 16px 18px; border: 1.5px solid #e1eae4; border-radius: 18px; background: #fff; transition: background-color 0.6s; }
.mpx-log.todo { border-color: #efd98a; background: #fffdf5; }
.mpx-log.row-flash { background: #e3efe7; }
.lg-date { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 60px; height: 60px; border-radius: 16px; background: #004d3a; color: #fff; }
.lg-date b { font-family: 'Playfair Display', Georgia, serif; font-size: 24px; line-height: 1; }
.lg-date small { font-size: 12px; font-weight: 700; color: #efbf04; }
.lg-main { min-width: 0; }
.lg-meal { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 0; font-size: 16px; font-weight: 800; color: #0e3a2c; }
.lg-meal > .ic { color: #9a7300; }
.lg-meal span { display: inline-flex; align-items: center; gap: 4px; font-size: 13.5px; font-weight: 600; color: #4a5a52; }
.lg-note { margin: 4px 0 0; font-size: 14px; color: #22362c; overflow-wrap: anywhere; }
.lg-note.empty { font-style: italic; color: #6b7d73; }
.lg-photo { display: inline-flex; align-items: center; gap: 8px; height: 40px; padding: 0 16px; border: 1.5px solid #c9d8cf; border-radius: 12px; background: #fff; color: #004d3a; font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; white-space: nowrap; }
.lg-photo:hover { border-color: #004d3a; background: #f1f8f4; }
.lg-rate small { display: block; margin-bottom: 6px; font-size: 11.5px; font-weight: 800; color: #8a6400; }
.mpx-none { margin: 0; padding: 30px; border: 1.5px dashed #c6d9cd; border-radius: 16px; text-align: center; }

@media (max-width: 1100px) {
  .targets.mpx-macros { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .nm-panel.mpx-adh { grid-template-columns: minmax(0, 1fr); }
  .mpx-adh-chart { padding: 18px 0 0; border-left: none; border-top: 1.5px solid #eef2ef; }
  .mpx-log { grid-template-columns: 60px minmax(0, 1fr); }
  .lg-photo, .lg-rate { grid-column: 1 / -1; }
  .lg-photo { justify-self: start; }
}
@media (max-width: 640px) {
  .targets.mpx-macros { grid-template-columns: minmax(0, 1fr); }
  .mpx-upd { width: 100%; justify-content: center; }
  .mpx-adh .mc-plot { height: 180px; margin-left: 34px; }
  .mpx-adh .mc-grid span { left: -34px; }
  .mpx-adh .mc-cols, .mpx-adh .mc-x { gap: 3px; }
  .mpx-adh .mc-x { margin-left: 34px; }
  .mpx-adh .mc-x span { font-size: 10px; }
  .mpx-leg { margin-left: 0; }
  .mpx-log { padding: 14px; gap: 12px; }
}

/* meal photo shown right on the log */
.mpx-log { grid-template-columns: 60px 150px minmax(0, 1fr) auto; }
.lg-pic { position: relative; display: block; width: 150px; height: 110px; padding: 0; border: none; border-radius: 14px; overflow: hidden; background: #e3ebe6; cursor: zoom-in; }
.lg-pic img { display: block; width: 100%; height: 100%; object-fit: cover; }
.lg-pic span { position: absolute; left: 6px; bottom: 6px; display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 999px; background: rgba(0, 0, 0, 0.55); color: #fff; font-size: 11px; font-weight: 700; }
.lg-pic:focus-visible { outline: 2px solid #004d3a; outline-offset: 2px; }
.lg-nopic { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; border: 1.5px dashed #c6d3cb; background: #f7faf8; color: #8a9a91; font-size: 12px; font-weight: 700; cursor: default; }
@media (max-width: 1100px) {
  .mpx-log { grid-template-columns: 60px minmax(0, 1fr); }
  .lg-pic { grid-column: 1 / -1; width: 100%; height: 180px; }
  .lg-nopic { height: 70px; }
}

/* color key for the macro tiles' bottom lines */
.mpx-key { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 16px; margin: 20px 0 0; font-size: 13px; font-weight: 700; color: #3e5046; }
.mpx-key span { display: inline-flex; align-items: center; gap: 6px; }
.mpx-key-t { font-weight: 600; color: #6b7d73; }
.mpx-key i { width: 18px; height: 5px; border-radius: 3px; }
.mpx-key i.k { background: #efbf04; } .mpx-key i.c { background: #1f7a4d; } .mpx-key i.p { background: #3b5ba5; } .mpx-key i.f { background: #c0483a; }
.mpx-key + .targets.mpx-macros { margin-top: 12px; }





/* chart + rating: match the canvas */
.mpx-adh .mc-track { background: #e4ece7; }
.mpx-adh .mc-col:hover .mc-track, .mpx-adh .mc-col:focus-visible .mc-track { background: #d6e3db; }
.mpx-adh .mc-col:hover, .mpx-adh .mc-col:focus-visible { background: transparent; }
.mpx-adh .mc-none { background: #a9bbb1; }
.mpx-adh .mc-bar { min-height: 6px; }
.mpx-adh .mc-x span { font-size: 13px; color: #22362c; }
.mpx-adh .mc-grid span { color: #4a5a52; }
/* rating buttons (from MealLogRating): green / gold / red */
.lg-rate :deep(button) { display: inline-flex; align-items: center; gap: 6px; height: 38px; padding: 0 14px; border-radius: 999px; border: 1.5px solid #c9d8cf; background: #fff; font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; transition: background-color 0.15s, color 0.15s; }
.lg-rate :deep(button:nth-of-type(1)) { border-color: #a9d3ba; color: #1f7a4d; }
.lg-rate :deep(button:nth-of-type(2)) { border-color: #efd98a; color: #8a6400; }
.lg-rate :deep(button:nth-of-type(3)) { border-color: #ebc2be; color: #b4384a; }
.lg-rate :deep(button:nth-of-type(1):hover), .lg-rate :deep(button:nth-of-type(1)[aria-pressed="true"]), .lg-rate :deep(button:nth-of-type(1).active), .lg-rate :deep(button:nth-of-type(1).on) { background: #1f7a4d; border-color: #1f7a4d; color: #fff; }
.lg-rate :deep(button:nth-of-type(2):hover), .lg-rate :deep(button:nth-of-type(2)[aria-pressed="true"]), .lg-rate :deep(button:nth-of-type(2).active), .lg-rate :deep(button:nth-of-type(2).on) { background: #efbf04; border-color: #efbf04; color: #004d3a; }
.lg-rate :deep(button:nth-of-type(3):hover), .lg-rate :deep(button:nth-of-type(3)[aria-pressed="true"]), .lg-rate :deep(button:nth-of-type(3).active), .lg-rate :deep(button:nth-of-type(3).on) { background: #b4384a; border-color: #b4384a; color: #fff; }
.lg-rate :deep(button:disabled) { opacity: 0.6; cursor: default; }
@media (max-width: 640px) { .mpx-adh .mc-x span { font-size: 10.5px; } }

/* macro tiles: boxes with a colour line (class names kept clear of .k) */
.mpx-macros .mt-k { border-bottom-color: #efbf04 !important; } .mpx-macros .mt-k .mx-ico { color: #9a7300; }
.mpx-macros .mt-c { border-bottom-color: #1f7a4d !important; } .mpx-macros .mt-c .mx-ico { color: #1f7a4d; }
.mpx-macros .mt-p { border-bottom-color: #3b5ba5 !important; } .mpx-macros .mt-p .mx-ico { color: #3b5ba5; }
.mpx-macros .mt-f { border-bottom-color: #c0483a !important; } .mpx-macros .mt-f .mx-ico { color: #c0483a; }
.mpx-macros p > span, .mpx-macros strong em, .mpx-macros small { text-transform: none; letter-spacing: 0; }
.mpx-macros p > span { color: #4a5a52; font-size: 13px; font-weight: 700; }
.mpx-log.todo .lg-rate small::after { content: ', needs your rating'; text-transform: none; letter-spacing: 0; font-weight: 700; color: #9a7300; }

/* macro targets: no boxes (the card around them stays); colour on the icon */
.targets.mpx-macros { gap: 0; }
.targets.mpx-macros > div { padding: 4px 24px; border: none !important; border-left: 1.5px solid #eef2ef !important; border-radius: 0; background: none; }
.targets.mpx-macros > div:first-child { padding-left: 0; border-left: none !important; }
.mpx-macros .mx-ico { width: 46px; height: 46px; border-radius: 50%; }
.mpx-macros .mt-k .mx-ico { background: #fbf3d2; color: #9a7300; }
.mpx-macros .mt-c .mx-ico { background: #ddefe4; color: #1f7a4d; }
.mpx-macros .mt-p .mx-ico { background: #e6ecf8; color: #3b5ba5; }
.mpx-macros .mt-f .mx-ico { background: #fbe6e3; color: #c0483a; }
.mpx-key i { width: 10px; height: 10px; border-radius: 50%; }
@media (max-width: 1100px) {
  .targets.mpx-macros { row-gap: 16px; }
  .targets.mpx-macros > div:nth-child(odd) { padding-left: 0; border-left: none !important; }
}
@media (max-width: 640px) {
  .targets.mpx-macros > div { padding-left: 0; border-left: none !important; }
}

/* meal plan tab: plan + adherence on the left, meal logs on the right (photo seen right away) */
.mpx-grid { display: grid; grid-template-columns: minmax(0, 1fr) 400px; gap: 18px; align-items: start; }
.mpx-left { min-width: 0; display: flex; flex-direction: column; gap: 18px; }
.mpx-left > .nm-panel, .mpx-grid > .nm-panel { margin: 0 !important; }
.nm-page .nm-panel.mpx-logs { position: sticky; top: 16px; }
.mpx-logs .mpx-logs-head { flex-wrap: wrap; }
.nm-panel.mpx-adh { grid-template-columns: 240px minmax(0, 1fr); }
.mpx-logs .mpx-log { grid-template-columns: 52px minmax(0, 1fr); gap: 12px 14px; padding: 14px; }
.mpx-logs .lg-pic { grid-column: 1 / -1; order: -1; width: 100%; height: 140px; }
.mpx-logs .lg-nopic { height: 70px; }
.mpx-logs .lg-date { width: 52px; height: 52px; border-radius: 14px; }
.mpx-logs .lg-date b { font-size: 21px; }
.mpx-logs .lg-rate { grid-column: 1 / -1; }
@media (max-width: 1200px) {
  .mpx-grid { grid-template-columns: minmax(0, 1fr); }
  .nm-page .nm-panel.mpx-logs { position: static; }
}

/* right column: photo as a small square, like a profile picture */
.lg-day { font-style: normal; display: none; }
.mpx-logs .mpx-log { grid-template-columns: 76px minmax(0, 1fr); align-items: center; gap: 12px 14px; }
.mpx-logs .lg-date { display: none; }
.mpx-logs .lg-day { display: inline; }
.mpx-logs .lg-pic { grid-column: auto; order: 0; width: 76px; height: 76px; border-radius: 16px; box-shadow: 0 8px 18px -12px rgba(16, 35, 27, 0.5); }
.mpx-logs .lg-pic span { left: auto; right: 5px; bottom: 5px; width: 24px; height: 24px; padding: 0; justify-content: center; font-size: 0; }
.mpx-logs .lg-pic span .ic { width: 13px; height: 13px; }
.mpx-logs .lg-nopic { width: 76px; height: 76px; font-size: 10.5px; }
.mpx-logs .lg-meal { font-size: 15.5px; }
.mpx-logs .lg-meal span { flex-basis: 100%; }

/* See all (top right of Meal logs) */
.mpx-logs-side { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; flex-shrink: 0; }
.mpx-seeall { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 14px; border: 1.5px solid #c9d8cf; border-radius: 999px; background: #fff; color: #004d3a; font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; white-space: nowrap; }
.mpx-seeall:hover { background: #f1f8f4; border-color: #004d3a; }
.mpx-seeall .ic { color: #9a7300; }

/* ALL MEAL LOGS: full-screen view */
.mlx { position: fixed; inset: 0; z-index: 60; display: flex; flex-direction: column; background: #f4f7f5; font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261e; }
.mlx-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 14px 24px; padding: 18px 32px; background: linear-gradient(115deg, #035a45 0%, #004d3a 55%, #00402f 100%); color: #fff; box-shadow: 0 10px 24px -18px rgba(0, 0, 0, 0.6); }
.mlx-back { display: inline-flex; align-items: center; gap: 8px; height: 42px; padding: 0 16px; border: 1px solid rgba(255, 255, 255, 0.25); border-radius: 12px; background: rgba(255, 255, 255, 0.1); color: #fff; font-family: inherit; font-size: 14px; font-weight: 800; cursor: pointer; }
.mlx-back:hover { background: rgba(255, 255, 255, 0.2); }
.mlx-back .ic { color: #efbf04; }
.mlx-t { flex: 1; min-width: 200px; }
.mlx-k { display: flex; align-items: center; gap: 7px; margin: 0; font-size: 12px; font-weight: 800; color: #efbf04; }
.mlx-t h2 { margin: 2px 0; font-family: 'Playfair Display', Georgia, serif; font-size: 26px; font-weight: 700; color: #fff; }
.mlx-t > p:last-child { margin: 0; font-size: 13.5px; color: rgba(255, 255, 255, 0.8); }
.mlx-t b { color: #efbf04; }
.mlx-filter { display: flex; gap: 4px; padding: 4px; border-radius: 999px; background: rgba(0, 0, 0, 0.2); }
.mlx-filter button { height: 36px; padding: 0 16px; border: none; border-radius: 999px; background: transparent; color: rgba(255, 255, 255, 0.85); font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; }
.mlx-filter button.on { background: #efbf04; color: #004d3a; }
.mlx-body { flex: 1; overflow-y: auto; padding: 24px 32px 40px; }
.mlx-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.mlx-card { display: flex; flex-direction: column; gap: 12px; padding: 12px; border: 1.5px solid #e1eae4; border-radius: 18px; background: #fff; transition: background-color 0.6s; }
.mlx-card.todo { border-color: #efd98a; background: #fffdf5; }
.mlx-card.row-flash { background: #e3efe7; }
.mlx-pic { position: relative; display: block; width: 100%; aspect-ratio: 4 / 3; padding: 0; border: none; border-radius: 14px; overflow: hidden; background: #e3ebe6; cursor: zoom-in; }
.mlx-pic img { display: block; width: 100%; height: 100%; object-fit: cover; }
.mlx-pic span { position: absolute; left: 8px; bottom: 8px; display: inline-flex; align-items: center; gap: 5px; padding: 4px 9px; border-radius: 999px; background: rgba(0, 0, 0, 0.55); color: #fff; font-size: 11.5px; font-weight: 700; }
.mlx-pic.none { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 6px; border: 1.5px dashed #c6d3cb; background: #f7faf8; color: #8a9a91; font-size: 13px; font-weight: 700; cursor: default; }
.mlx-info { padding: 0 4px; }
.mlx-card .lg-meal { font-size: 16px; }
.mlx-when { display: flex; align-items: center; gap: 6px; margin: 4px 0 0; font-size: 13px; font-weight: 600; color: #4a5a52; }
.mlx-card .lg-rate { padding: 0 4px 4px; }
.mlx-card.todo .lg-rate small::after { content: ', needs your rating'; text-transform: none; letter-spacing: 0; font-weight: 700; color: #9a7300; }
.mlx-empty { margin: 40px auto; max-width: 420px; padding: 30px; border: 1.5px dashed #c6d9cd; border-radius: 16px; text-align: center; color: #4a5a52; }
@media (max-width: 760px) {
  .mlx-bar { padding: 14px 16px; }
  .mlx-t h2 { font-size: 22px; }
  .mlx-filter { width: 100%; }
  .mlx-filter button { flex: 1; }
  .mlx-body { padding: 16px 16px 110px; }
  .mlx-grid { grid-template-columns: minmax(0, 1fr); }
}

/* =========================================================
   Progress tab
   ========================================================= */
.pgx-sum { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin: 0 0 22px; padding: 4px 0 22px; border-bottom: 1.5px solid #e3ebe6; }
.pgx-fig { display: flex; align-items: center; gap: 14px; min-width: 0; padding: 6px 24px; border-left: 1.5px solid #e3ebe6; }
.pgx-fig:first-child { padding-left: 4px; border-left: none; }
.pgx-fig.none { opacity: 0.75; }
.pgx-fig > div { min-width: 0; }
.pgx-fig small { display: block; font-size: 13px; font-weight: 700; color: #4a5a52; }
.pgx-fig b { display: block; font-family: 'Playfair Display', Georgia, serif; font-size: 28px; line-height: 1.15; color: #0e3a2c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.pgx-fig.none b { color: #9aa8a0; }
.pgx-ico { flex-shrink: 0; width: 48px; height: 48px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; }
.pgx-ico.sm { width: 42px; height: 42px; }
.pgx-ico.g { background: #ddefe4; color: #1f7a4d; } .pgx-ico.y { background: #fbf3d2; color: #9a7300; }
.pgx-ico.r { background: #fbe6e3; color: #c0483a; } .pgx-ico.b { background: #e6ecf8; color: #3b5ba5; } .pgx-ico.v { background: #eee8f7; color: #6a4ba0; }
.pgx-chg { display: inline-flex; align-items: center; margin-top: 4px; padding: 2px 9px; border-radius: 999px; font-size: 12px; font-weight: 800; background: #eef2ef; color: #3e5046; white-space: nowrap; }
.pgx-chg.ok { background: #e3f4ea; color: #1f7a4d; }
.pgx-chg.muted { padding: 0; background: none; color: #8a9a91; font-weight: 600; }
.pgx-h { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.pgx-k { display: flex; align-items: center; gap: 8px; margin: 0 0 4px; font-size: 12px; font-weight: 800; color: #9a7300; }
.pgx .nm-panel-title { font-size: 22px; }
.pgx-count { flex-shrink: 0; display: inline-flex; align-items: center; height: 28px; padding: 0 12px; border-radius: 999px; background: #e3efe7; color: #004d3a; font-size: 13px; font-weight: 800; }
.trend-grid.pgx-grid { grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; margin-top: 0; }
.trend-card.pgx-card { padding: 18px 20px 14px; border: 1.5px solid #e6eee9; border-radius: 18px; background: #f7faf8; }
.pgx-ch { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.pgx-ct { flex: 1; min-width: 0; }
.pgx-card .tc-title { font-family: 'DM Sans', sans-serif; font-size: 16px; font-weight: 800; color: #0e3a2c; }
.pgx-card .tc-sub { margin: 2px 0 0; font-size: 13px; color: #4a5a52; }
.pgx-cv { display: flex; flex-direction: column; align-items: flex-end; text-align: right; }
.pgx-card .tc-latest { font-size: 24px; color: #0e3a2c; }
.pgx-one { padding: 4px 0 2px; }
.pgx-one .dash { stroke: #c6d3cb; stroke-width: 2; stroke-dasharray: 4 7; }
.pgx-one .pt { fill: #1f7a4d; stroke: #fff; stroke-width: 3; }
.pgx-one p { display: flex; align-items: center; gap: 6px; margin: 4px 0 0; font-size: 13px; font-weight: 600; color: #4a5a52; }
.pgx-one p .ic { color: #9a7300; }
.pgx-none { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 16px; font-size: 13.5px; color: #4a5a52; }
.pgx-none > span { display: inline-flex; align-items: center; gap: 6px; font-weight: 700; }
.pgx-none > span .ic { color: #3b5ba5; }
.pgx-none i { display: inline-flex; align-items: center; height: 30px; padding: 0 12px; border: 1.5px dashed #c6d3cb; border-radius: 999px; font-style: normal; font-weight: 700; color: #4a5a52; }
.pgx-empty { margin: 0; padding: 24px; border: 1.5px dashed #c6d9cd; border-radius: 16px; text-align: center; }
.pgx-list { display: flex; flex-direction: column; }
.pgx-rec { display: grid; grid-template-columns: 64px minmax(0, 1fr) auto; align-items: center; gap: 20px; padding: 16px 0; border-bottom: 1.5px solid #eef2ef; }
.pgx-rec:first-child { border-top: 1.5px solid #eef2ef; }
.pgx-date { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 64px; height: 68px; border-radius: 16px; background: #004d3a; color: #fff; }
.pgx-date b { font-family: 'Playfair Display', Georgia, serif; font-size: 24px; line-height: 1; }
.pgx-date small { font-size: 11px; font-weight: 800; color: #efbf04; }
.pgx-date em { font-style: normal; font-size: 10.5px; color: rgba(255, 255, 255, 0.75); }
.pgx-vals { display: flex; flex-wrap: wrap; align-items: center; row-gap: 10px; margin: 0; padding: 0; list-style: none; }
.pgx-vals li { display: flex; flex-direction: column; padding: 0 22px; border-left: 1.5px solid #eef2ef; }
.pgx-vals li:first-child { padding-left: 0; border-left: none; }
.pgx-vals small { display: flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 700; color: #4a5a52; }
.pgx-vals small i { width: 8px; height: 8px; border-radius: 50%; }
.pgx-vals i.w { background: #1f7a4d; } .pgx-vals i.bm { background: #efbf04; } .pgx-vals i.bp { background: #c0483a; } .pgx-vals i.gl { background: #3b5ba5; } .pgx-vals i.hb { background: #6a4ba0; }
.pgx-vals b { font-size: 18px; font-weight: 800; color: #0e3a2c; white-space: nowrap; }
.pgx-vals b em { margin-left: 3px; font-style: normal; font-size: 12.5px; font-weight: 700; color: #4a5a52; }
.pgx-vals li.no b { color: #b5c2ba; font-weight: 600; }
.pgx-side { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; max-width: 280px; text-align: right; }
.pgx-src { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 12px; border-radius: 999px; background: #e3efe7; color: #1f7a4d; font-size: 12.5px; font-weight: 800; white-space: nowrap; }
.pgx-src.self { background: #e6ecf8; color: #3b5ba5; }
.pgx-note { margin: 0; font-size: 13px; color: #4a5a52; overflow-wrap: anywhere; }
.pgx-note em { color: #8a9a91; }
@media (max-width: 1100px) {
  .pgx-sum { grid-template-columns: repeat(2, minmax(0, 1fr)); row-gap: 14px; }
  .pgx-fig:nth-child(3) { padding-left: 4px; border-left: none; }
}
@media (max-width: 640px) {
  .pgx-fig { padding: 6px 10px; gap: 10px; }
  .pgx-ico { width: 38px; height: 38px; }
  .pgx-fig b { font-size: 22px; }
  .trend-grid.pgx-grid { grid-template-columns: minmax(0, 1fr); }
  .pgx-rec { grid-template-columns: 56px minmax(0, 1fr); gap: 14px; }
  .pgx-date { width: 56px; height: 60px; }
  .pgx-vals li { padding: 0 14px; }
  .pgx-vals li:nth-child(4) { padding-left: 0; border-left: none; }
  .pgx-side { grid-column: 1 / -1; flex-direction: row; align-items: center; justify-content: space-between; max-width: none; text-align: left; }
}

/* =========================================================
   Consultations tab: day-grouped timelines
   ========================================================= */
.csx { display: flex; flex-direction: column; gap: 18px; }
.nm-page .csx > .nm-panel { margin: 0; }
.csx-h { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 16px; }
.csx-k { display: flex; align-items: center; gap: 8px; margin: 0 0 4px; font-size: 12px; font-weight: 800; color: #9a7300; }
.csx .nm-panel-title { font-size: 22px; }
.csx-open { flex-shrink: 0; display: inline-flex; align-items: center; gap: 8px; height: 42px; padding: 0 18px; border-radius: 12px; background: #004d3a; color: #fff; font-size: 14px; font-weight: 800; text-decoration: none; }
.csx-open .ic { color: #efbf04; }
.csx-open:hover { background: #035a45; }
.csx-count { flex-shrink: 0; display: inline-flex; align-items: center; height: 28px; padding: 0 12px; border-radius: 999px; background: #e3efe7; color: #004d3a; font-size: 13px; font-weight: 800; }
.csx-empty { margin: 0; padding: 22px; border: 1.5px dashed #c6d9cd; border-radius: 16px; text-align: center; }
.csx-g { margin-bottom: 16px; }
.csx-g:last-of-type { margin-bottom: 0; }
.csx-g h4 { display: flex; align-items: baseline; gap: 10px; margin: 0 0 8px; }
.csx-g h4 b { font-family: 'Playfair Display', Georgia, serif; font-size: 19px; color: #0e3a2c; }
.csx-g h4 span { font-size: 13.5px; font-weight: 600; color: #4a5a52; }
.csx-next { padding: 3px 10px; border-radius: 999px; background: #efbf04; color: #004d3a; font-style: normal; font-size: 12px; font-weight: 800; align-self: center; }
.csx-l { position: relative; display: flex; flex-direction: column; gap: 6px; }
.csx-l::before { content: ''; position: absolute; left: 21px; top: 24px; bottom: 24px; width: 2px; background: #d3e0d8; }
.csx-e { position: relative; display: grid; grid-template-columns: 44px minmax(0, 1fr) auto; align-items: center; gap: 16px; padding: 12px 14px 12px 0; border-radius: 16px; }
.csx-e:hover { background: #f7faf8; }
.csx-e.nx { margin-left: -10px; padding-left: 10px; background: #f1f8f4; }
.csx-i { position: relative; z-index: 1; width: 44px; height: 44px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; border: 3px solid #fff; }
.csx-i.gold { background: #efbf04; color: #004d3a; }
.csx-i.blue { background: #e6ecf8; color: #3b5ba5; }
.csx-i.green { background: #ddefe4; color: #1f7a4d; }
.csx-i.red { background: #fbe6e3; color: #b4384a; }
.csx-t { min-width: 0; }
.csx-t b { display: block; font-size: 15.5px; font-weight: 800; color: #0e3a2c; }
.csx-t small { display: block; margin-top: 3px; font-size: 13.5px; line-height: 1.45; color: #4a5a52; overflow-wrap: anywhere; }
.csx-s { display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 6px; }
.csx-s.col { flex-direction: column; align-items: flex-end; }
.csx-row { display: flex; align-items: center; gap: 6px; }
.csx-pl { display: inline-flex; align-items: center; gap: 5px; height: 28px; padding: 0 11px; border-radius: 999px; font-size: 12.5px; font-weight: 800; white-space: nowrap; }
.csx-pl.blue { background: #e6ecf8; color: #3b5ba5; }
.csx-pl.green { background: #e3f4ea; color: #1f7a4d; }
.csx-pl.gold { background: #fbf3d2; color: #8a6400; }
.csx-pl.muted { background: #eef2ef; color: #6b7d73; }
.csx-ncp { display: inline-flex; align-items: center; gap: 5px; font-size: 13px; font-weight: 800; }
.csx-ncp.ok { color: #1f7a4d; }
.csx-ncp.draft { padding: 1px 9px; border: 1.5px dashed #3f9a6b; border-radius: 999px; color: #1f6f46; }
.csx-ncp.none { color: #a07400; }
.csx-ncp.mute { color: #8a9a91; font-weight: 600; }
.csx-sum { display: inline-flex; align-items: center; gap: 5px; }
@media (max-width: 760px) {
  .csx-h { flex-direction: column; }
  .csx-open { width: 100%; justify-content: center; }
  .csx-e { grid-template-columns: 44px minmax(0, 1fr); }
  .csx-s, .csx-s.col { grid-column: 2; align-items: flex-start; justify-content: flex-start; }
}
</style>