<template>
  <div class="nm-page">
    <p class="crumb"><NuxtLink to="/my-patients">My Patients</NuxtLink> / {{ p?.client.name || 'Patient' }}</p>
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <div v-if="loading" class="nm-panel"><p class="nm-muted">Loading patient…</p></div>

    <template v-else-if="s">
      <!-- HEADER: who, status, the next step; Discharge lives in the More menu -->
      <section class="nm-panel patient-head">
        <div class="ph-top">
          <div class="ph-who">
            <img v-if="p.client.profile_photo" :src="p.client.profile_photo" class="ph-avatar" alt="" />
            <span v-else class="ph-avatar">{{ userInitials(p.client.first_name, p.client.last_name) }}</span>
            <div class="ph-info">
              <h1 class="ph-name">{{ p.client.name }}</h1>
              <p v-if="metaLine" class="ph-meta">{{ metaLine }}</p>
              <p class="ph-status">
                <span class="ph-pill" :class="p.status">{{ STATUS_LABEL[p.status] }}</span>
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
          <AlertTriangle :size="15" /> <span><strong>Food allergy:</strong> {{ s.health.allergies.join(', ') }}. Check every food in their plan against this.</span>
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
            <NuxtLink v-if="p.status === 'active'" :to="a.link" class="nm-btn-outline nm-btn-sm">{{ a.action }}</NuxtLink>
          </div>
        </div>

        <div class="nm-panel figures">
          <div class="fig">
            <p class="fig-label">Current weight</p>
            <p class="fig-value">{{ p.progress.latest_weight_kg != null ? `${fmt1(p.progress.latest_weight_kg)} kg` : '—' }}</p>
            <p class="fig-note">{{ figureSource(p.progress.weight_origin) || 'Not measured yet' }}</p>
            <p v-if="p.progress.weight_change_kg != null" class="fig-note">{{ signed(p.progress.weight_change_kg) }} kg since screening</p>
          </div>
          <div class="fig">
            <p class="fig-label">BMI</p>
            <p class="fig-value">{{ p.progress.bmi != null ? fmt1(p.progress.bmi) : '—' }}</p>
            <p class="fig-note">{{ p.progress.bmi_class ? `${p.progress.bmi_class}, Asia-Pacific` : 'Not measured yet' }}</p>
            <p v-if="p.progress.bmi_origin" class="fig-note">From the {{ figureSource(p.progress.bmi_origin) }} weight</p>
          </div>
          <div class="fig">
            <p class="fig-label">7-day meal-plan adherence</p>
            <p class="fig-value">{{ p.adherence?.pct != null ? `${p.adherence.pct}%` : '—' }}</p>
            <p class="fig-note">{{ p.adherence ? `${p.adherence.logged} of ${p.adherence.planned} meals logged` : 'No meal plan sent yet' }}</p>
          </div>
          <div class="fig" :class="{ risk: (s.screening?.nrs_score ?? 0) >= 3 }">
            <p class="fig-label">NRS-2002 score</p>
            <p class="fig-value">{{ s.screening?.nrs_score ?? '—' }}</p>
            <p class="fig-note">{{ s.screening ? (s.screening.nrs_risk || 'Not scored') : 'No screening yet' }}</p>
            <p v-if="s.screening" class="fig-note">{{ screeningSource(s.screening).replace(/^f/, 'F') }}</p>
          </div>
        </div>

        <div class="nm-grid">
          <div class="nm-col">
            <!-- care stage -->
            <div class="nm-panel">
              <h2 class="nm-panel-title">Care process</h2>
              <ol class="stepper">
                <li v-for="st in stageSteps" :key="st.label" :class="st.state">
                  <span class="dot"><Check v-if="st.state === 'done'" :size="13" /></span>
                  <span class="st-label">{{ st.label }}</span>
                  <span class="st-sub">{{ st.sub }}</span>
                </li>
              </ol>
            </div>

            <!-- current care plan -->
            <div class="nm-panel">
              <div class="nm-panel-head">
                <div>
                  <h2 class="nm-panel-title">Current diagnosis &amp; plan</h2>
                  <p class="nm-panel-sub">{{ s.care_plan ? `From the ${s.care_plan.is_follow_up ? 'follow-up' : 'initial'} NCP record of ${shortDate(s.care_plan.encounter_date)}` : 'From their latest finalized NCP record' }}</p>
                </div>
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
              <h2 class="nm-panel-title">Pre-consultation screening</h2>
              <p v-if="!s.screening" class="nm-muted" style="margin-top: 10px">They haven't submitted a screening yet.</p>
              <template v-else>
                <p class="nm-panel-sub">Submitted {{ shortDate(s.screening.date) }}</p>
                <dl class="facts">
                  <div><dt>Height</dt><dd>{{ fmt1(s.screening.height_cm) }} cm</dd></div>
                  <div><dt>Weight</dt><dd>{{ fmt1(s.screening.weight_kg) }} kg</dd></div>
                  <div><dt>BMI</dt><dd>{{ s.screening.bmi ? fmt1(s.screening.bmi) : '—' }}<small v-if="s.screening.bmi_category">, {{ s.screening.bmi_category }}</small></dd></div>
                  <div><dt>Activity</dt><dd>{{ s.screening.activity_level }}</dd></div>
                  <div><dt>BMR (Tannhauser)</dt><dd>{{ s.screening.bmr_kcal ? `${Math.round(s.screening.bmr_kcal).toLocaleString('en-PH')} kcal` : 'Not calculated' }}</dd></div>
                  <div><dt>TER</dt><dd>{{ s.screening.tdee_kcal ? `${Math.round(s.screening.tdee_kcal).toLocaleString('en-PH')} kcal` : 'Not calculated' }}</dd></div>
                  <div><dt>NRS-2002</dt><dd>{{ s.screening.nrs_score ?? '—' }}<small v-if="s.screening.nrs_risk">, {{ s.screening.nrs_risk.toLowerCase() }}</small></dd></div>
                </dl>
                <p v-if="s.screening.symptoms" class="symptoms"><span class="k">Symptoms and notes</span>{{ s.screening.symptoms }}</p>
              </template>
            </div>
          </div>

          <div class="nm-col">
            <!-- next appointment -->
            <div class="nm-panel">
              <div class="nm-panel-head">
                <h2 class="nm-panel-title">Next consultation</h2>
                <button type="button" class="nm-panel-link" @click="setTab('appointments')">All consultations</button>
              </div>
              <template v-if="nextAppt">
                <p class="big-when">{{ longWhen(nextAppt.scheduled_at) }}</p>
                <p class="nm-row-sub">{{ nextAppt.type_label }}, {{ nextAppt.duration_minutes }} min</p>
                <p class="pills">
                  <span v-if="nextAppt.status === 'pending'" class="nm-pill gold">Needs your confirmation</span>
                  <span v-else-if="nextAppt.payment === 'paid'" class="nm-pill green">Paid</span>
                  <span v-else class="nm-pill muted">Not paid yet</span>
                </p>
                <NuxtLink v-if="canJoin(nextAppt)" :to="`/consultation-room/${nextAppt.id}`" class="nm-btn-dark nm-btn-sm"><Video :size="14" /> Join</NuxtLink>
                <NuxtLink v-else-if="nextAppt.status === 'pending'" to="/appointments" class="nm-btn-dark nm-btn-sm">Review booking</NuxtLink>
              </template>
              <p v-else class="nm-muted">Nothing booked.{{ p.last_visit ? ` Last visit ${shortDate(p.last_visit)}.` : '' }}</p>
            </div>

            <!-- health profile -->
            <div class="nm-panel">
              <h2 class="nm-panel-title">Health profile</h2>
              <dl class="facts one">
                <div><dt>Conditions</dt><dd>{{ list(s.health.conditions) }}</dd></div>
                <div><dt>Food allergies</dt><dd :class="{ warn: s.health.allergies.length }">{{ s.health.allergies.length ? s.health.allergies.join(', ') : 'None reported' }}</dd></div>
                <div><dt>Diet</dt><dd>{{ list(s.health.dietary_restrictions) }}</dd></div>
                <div><dt>Religion</dt><dd>{{ s.health.religion || 'Not recorded' }}</dd></div>
                <div><dt>Goals</dt><dd>{{ list(s.health.health_goals) }}</dd></div>
              </dl>
            </div>

            <!-- latest progress -->
            <div class="nm-panel">
              <div class="nm-panel-head">
                <h2 class="nm-panel-title">Latest progress</h2>
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
                <h2 class="nm-panel-title">Lab results</h2>
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
      <div v-else-if="tab === 'ncp'" class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">NCP records</h2>
            <p class="nm-panel-sub">Assessment, diagnosis and intervention, plus monitoring on follow-ups. A finalized record can't be changed.</p>
          </div>
          <button v-if="p.status === 'active' && !openDraft && unwrittenVisit" class="nm-btn-dark nm-btn-sm" type="button" @click="openNcpForm(unwrittenVisit.id)">
            Write record for {{ shortDate(unwrittenVisit.scheduled_at) }} visit
          </button>
        </div>
        <!-- timeline, newest first: what each record says, so visits compare at a glance -->
        <ol v-if="ncpTimeline.length" class="ncp-tl">
          <li v-for="r in ncpTimeline" :key="r.id" class="tl-item" :class="{ draft: r.status !== 'completed' }">
            <span class="tl-dot" aria-hidden="true" />
            <div class="tl-body">
              <div class="tl-head">
                <p class="tl-kind" :class="{ follow: r.is_follow_up }">{{ r.kindLabel }}</p>
                <span class="nm-pill" :class="r.status === 'completed' ? 'green' : 'gold'">{{ r.status === 'completed' ? 'Finalized' : 'Draft' }}</span>
              </div>
              <p class="tl-date">{{ shortDate(r.encounter_date || r.created_at) }}<template v-if="r.status !== 'completed'">, last edited {{ dateTime(r.updated_at) }}</template></p>
              <p class="tl-dx"><span class="tl-k">Diagnosis</span>{{ r.pes_problem || 'Not written yet' }}<template v-if="r.pes_problem && r.pes_etiology">, related to {{ r.pes_etiology }}</template></p>
              <p class="tl-facts">
                <span><span class="tl-k">Weight</span>{{ r.weight_kg != null ? `${fmt1(r.weight_kg)} kg` : 'Not measured' }}<small v-if="r.weightChange != null" :class="{ down: r.weightChange < 0 }"> ({{ Math.abs(r.weightChange) < 0.05 ? 'no change' : `${signed(r.weightChange)} kg` }})</small></span>
                <span><span class="tl-k">TER</span>{{ r.target_kcal ? `${Math.round(r.target_kcal).toLocaleString('en-PH')} kcal` : 'Not set' }}</span>
                <span v-if="r.is_follow_up"><span class="tl-k">Goal</span>{{ GOAL_LABEL[r.goal_status] || 'Not rated' }}</span>
              </p>
              <p v-if="r.status !== 'completed' && r.missing.length" class="tl-missing"><strong>Still needed:</strong> {{ r.missing.join(', ') }}.</p>
              <div class="tl-actions">
                <!-- no Delete: a record comes from a consultation, so a draft is continued, never discarded -->
                <button type="button" class="nm-btn-outline nm-btn-sm" @click="viewNcpRecord(r)"><Eye :size="14" /> View record</button>
                <button v-if="r.status !== 'completed' && p.status === 'active'" type="button" class="nm-btn-dark nm-btn-sm" @click="openNcpForm()"><Pencil :size="14" /> Continue record</button>
              </div>
            </div>
          </li>
        </ol>
        <p v-else class="nm-muted">No NCP records yet.</p>
        <p v-if="p.status === 'active' && !openDraft && !unwrittenVisit" class="nm-muted">NCP records are written during the consultation, in the consultation room's NCP tab.</p>
      </div>

      <!-- ===================== MEAL PLAN ===================== -->
      <template v-else-if="tab === 'meal'">
        <div class="nm-panel">
          <div class="nm-panel-head">
            <div>
              <h2 class="nm-panel-title">{{ s.meal_plan ? s.meal_plan.name : 'Meal plan' }}</h2>
              <p class="nm-panel-sub" v-if="s.meal_plan">
                {{ s.meal_plan.status === 'active' ? `Sent ${shortDate(s.meal_plan.sent_at)}` : 'Draft, not sent to the patient yet' }},
                {{ s.meal_plan.meals_per_week }} meals a week
              </p>
            </div>
            <template v-if="p.status === 'active'">
              <NuxtLink v-if="mealPlanReady" :to="`/meal-planning?relationship=${relationshipId}&edit=1`" class="nm-btn-dark nm-btn-sm">
                {{ s.meal_plan ? (s.meal_plan.status === 'draft' ? 'Finish and send plan' : 'Update meal plan') : 'Create meal plan' }}
              </NuxtLink>
            </template>
          </div>
          <p v-if="p.status === 'active' && !mealPlanReady && !s.meal_plan" class="nm-note todo-note" style="margin: 0">Finish the NCP Intervention (diet prescription and target calories) before creating a meal plan.</p>
          <div v-if="s.meal_plan?.target_kcal" class="targets">
            <div><span>Calories</span><strong>{{ Math.round(s.meal_plan.target_kcal).toLocaleString('en-PH') }} kcal</strong></div>
            <div v-if="s.meal_plan.target_carb_g"><span>Carbs</span><strong>{{ Math.round(s.meal_plan.target_carb_g) }} g</strong></div>
            <div v-if="s.meal_plan.target_protein_g"><span>Protein</span><strong>{{ Math.round(s.meal_plan.target_protein_g) }} g</strong></div>
            <div v-if="s.meal_plan.target_fat_g"><span>Fat</span><strong>{{ Math.round(s.meal_plan.target_fat_g) }} g</strong></div>
          </div>
          <p v-else-if="!s.meal_plan && mealPlanReady" class="nm-muted">No meal plan yet.</p>
        </div>

        <div class="nm-panel">
          <div class="nm-panel-head">
            <div>
              <h2 class="nm-panel-title">Adherence, last 14 days</h2>
              <p class="nm-panel-sub">Share of planned meals followed each day, from your ratings. Partly followed counts as half, an unlogged meal counts as missed, and logs you haven't rated yet aren't counted.</p>
            </div>
          </div>
          <p v-if="!s.adherence_days.some(d => d.planned)" class="nm-muted">No meals were planned in the last 14 days.</p>
          <div v-else class="mini-chart" role="img" :aria-label="`Adherence by day: ${s.adherence_days.map(d => `${d.date} ${d.followed_pct ?? 'none planned'}`).join(', ')}`">
            <div class="mc-plot">
              <div v-for="t in [100, 50, 0]" :key="t" class="mc-grid" :style="{ bottom: `${t}%` }"><span>{{ t }}%</span></div>
              <div class="mc-goal" style="bottom: 80%"><span>Goal 80%</span></div>
              <div class="mc-cols">
                <div v-for="(d, i) in s.adherence_days" :key="d.date" class="mc-col" tabindex="0"
                     :aria-label="d.followed_pct == null ? `${dayName(d.date)}: no meals planned` : `${dayName(d.date)}: ${d.followed_pct}%, ${d.logged} of ${d.planned} logged`"
                     @mouseenter="hover = i" @mouseleave="hover = null" @focus="hover = i" @blur="hover = null">
                  <span v-if="d.followed_pct == null" class="mc-none">–</span>
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
              <span v-for="(d, i) in s.adherence_days" :key="d.date">{{ i % 2 === 1 || i === s.adherence_days.length - 1 ? shortDay(d.date, i === s.adherence_days.length - 1) : '' }}</span>
            </div>
          </div>
        </div>

        <div class="nm-panel">
          <h2 class="nm-panel-title">Recent meal logs</h2>
          <p class="nm-panel-sub">What {{ p.client.first_name }} ate, with their photo and note. {{ p.status === 'active' ? 'Rate each one. It counts toward adherence once rated.' : '' }}
            <strong v-if="toReview && p.status === 'active'" class="to-review">{{ toReview }} to review</strong></p>
          <div v-if="s.recent_logs.length" class="nm-table-wrap" style="margin-top: 10px">
            <table class="nm-table">
              <thead><tr><th>Date</th><th>Meal</th><th>Logged at</th><th>Their note</th><th>Your rating</th></tr></thead>
              <tbody>
                <tr v-for="l in s.recent_logs" :key="l.id">
                  <td>{{ shortDate(l.date) }}</td>
                  <td>{{ l.meal }}</td>
                  <td>{{ l.time_logged ? clockOf(l.time_logged) : 'Not recorded' }}</td>
                  <td class="note-cell">{{ l.note || 'No note' }}<a v-if="l.photo_url" :href="l.photo_url" target="_blank" rel="noopener" class="nm-panel-link photo-link">Photo</a></td>
                  <td>
                    <MealLogRating v-if="p.status === 'active'" :log-id="l.id" :status="l.status" compact
                                   :label="`${l.meal} on ${shortDate(l.date)}`" @rated="load" />
                    <span v-else class="nm-pill" :class="LOG_PILL[l.status] || 'muted'">{{ l.status_label }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="nm-muted" style="margin-top: 10px">No meals logged yet.</p>
        </div>
      </template>

      <!-- ===================== PROGRESS ===================== -->
      <template v-else-if="tab === 'progress'">
        <!-- every measurement at once (was one chart with a Weight / BMI / … switcher) -->
        <div class="nm-panel">
          <h2 class="nm-panel-title">Trends</h2>
          <p class="nm-panel-sub">From the screening, progress records and finalized NCP records.</p>
          <p v-if="!trends.shown.length" class="nm-muted" style="margin-top: 12px">No measurements yet. They appear here once an NCP record is finalized.</p>
          <div v-else class="trend-grid">
            <section v-for="t in trends.shown" :key="t.key" class="trend-card">
              <div class="tc-head">
                <h3 class="tc-title">{{ t.label }}</h3>
                <span class="tc-latest">{{ t.latest }}</span>
              </div>
              <p class="tc-sub">{{ t.sub }}</p>
              <TrendChart v-if="t.hasTrend" :series="t.series" :unit="t.unit" :decimals="t.decimals" :ref-lines="t.refLines" :title="`${t.label} trend`" />
              <p v-else class="tc-one">One reading so far. The trend line starts at the second.</p>
            </section>
          </div>
          <p v-if="trends.none.length" class="tc-none">No readings yet: {{ trends.none.join(', ') }}.</p>
        </div>

        <div class="nm-panel">
          <h2 class="nm-panel-title">All progress records</h2>
          <p class="nm-panel-sub">Saved automatically when you finalize an NCP record, with the measurements from that consultation.</p>
          <div v-if="s.progress.length" class="nm-table-wrap" style="margin-top: 10px">
            <table class="nm-table">
              <thead><tr><th>Date</th><th>Weight</th><th>BMI</th><th>Blood pressure</th><th>Glucose</th><th>HbA1c</th><th>Note</th></tr></thead>
              <tbody>
                <tr v-for="r in s.progress" :key="r.id">
                  <td class="nowrap">{{ shortDate(r.record_date) }}<span v-if="r.source === 'client'" class="nm-pill blue self-tag">Self-reported</span></td>
                  <td class="nowrap">{{ r.weight_kg != null ? `${fmt1(r.weight_kg)} kg` : '—' }}</td>
                  <td>{{ r.bmi != null ? fmt1(r.bmi) : '—' }}</td>
                  <td>{{ r.blood_pressure || '—' }}</td>
                  <td>{{ r.blood_glucose != null ? `${r.blood_glucose} mg/dL` : '—' }}</td>
                  <td>{{ r.hba1c != null ? `${r.hba1c}%` : '—' }}</td>
                  <td class="note-cell"><template v-if="r.source === 'client'">{{ r.client_notes ? `Patient: ${r.client_notes}` : '—' }}</template><template v-else>{{ r.rnd_notes || '—' }}</template></td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="nm-muted" style="margin-top: 10px">No progress records yet.</p>
        </div>
      </template>

      <!-- ===================== CONSULTATIONS ===================== -->
      <div v-else-if="tab === 'appointments'" class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">Consultations with {{ p.client.first_name }}</h2>
            <p class="nm-panel-sub">{{ p.consultations }} completed{{ consults.upcoming.length ? `, ${consults.upcoming.length} coming up` : '' }}</p>
          </div>
          <NuxtLink :to="`/appointments?relationship=${relationshipId}`" class="nm-panel-link">Open Appointments</NuxtLink>
        </div>
        <p v-if="!s.appointments.length" class="nm-muted">No consultations yet.</p>

        <!-- 1. coming up -->
        <section v-if="consults.upcoming.length" class="cs-sec">
          <h3 class="cs-title">Coming up</h3>
          <div v-for="a in consults.upcoming" :key="a.id" class="cs-card">
            <div class="appt-date">
              <span class="ad-day">{{ dayNum(a.scheduled_at) }}</span>
              <span class="ad-mon">{{ monthShort(a.scheduled_at) }}</span>
            </div>
            <div class="appt-main">
              <p class="nm-row-title">{{ longWhen(a.scheduled_at) }}</p>
              <p class="nm-row-sub">{{ a.type_label }}, {{ a.duration_minutes }} min{{ a.amount ? `, ${peso(a.amount)}` : '' }}</p>
            </div>
            <div class="appt-end">
              <span class="nm-pill" :class="APPT_PILL[a.status]">{{ a.status === 'pending' ? 'Needs your confirmation' : 'Confirmed' }}</span>
              <span v-if="a.payment" class="nm-pill" :class="a.payment === 'paid' ? 'green' : 'muted'">{{ PAY_LABEL[a.payment] || a.payment }}</span>
              <NuxtLink v-if="canJoin(a)" :to="`/consultation-room/${a.id}`" class="nm-btn-dark nm-btn-sm"><Video :size="13" /> Join</NuxtLink>
              <NuxtLink v-else-if="a.status === 'pending'" to="/appointments?tab=requests" class="nm-btn-dark nm-btn-sm">Review booking</NuxtLink>
            </div>
          </div>
        </section>

        <!-- 3. history, as a table -->
        <section v-if="consults.past.length" class="cs-sec">
          <h3 class="cs-title">Past consultations</h3>
          <div class="nm-table-wrap">
            <table class="nm-table stack cs-table">
              <thead><tr><th>Date</th><th>Format</th><th>Result</th><th>Payment</th><th>NCP record</th><th><span class="sr-only">Summary</span></th></tr></thead>
              <tbody>
                <tr v-for="a in pagedPast" :key="a.id">
                  <td data-label="Date"><strong>{{ shortDate(a.scheduled_at) }}</strong><span class="nm-row-sub cs-time">{{ timeOf(a.scheduled_at) }}</span></td>
                  <td data-label="Format">{{ a.type_label }}</td>
                  <td data-label="Result">
                    <span class="nm-pill" :class="a.status === 'confirmed' ? 'gold' : APPT_PILL[a.status]">{{ a.status === 'confirmed' ? 'Not marked complete' : APPT_LABEL[a.status] }}</span>
                    <span v-if="a.status === 'cancelled' && a.cancellation_reason" class="nm-row-sub cs-reason">{{ a.cancellation_reason }}</span>
                  </td>
                  <td data-label="Payment">{{ a.payment ? (PAY_LABEL[a.payment] || a.payment) : 'None' }}<template v-if="a.amount && a.payment === 'paid'">, {{ peso(a.amount) }}</template></td>
                  <td data-label="NCP record">
                    <span v-if="a.status !== 'completed' && !a.ncp_status" class="nm-muted">{{ a.status === 'confirmed' ? 'None yet' : 'Not needed' }}</span>
                    <span v-else-if="a.ncp_status === 'completed'" class="cs-ok"><Check :size="13" /> Finalized</span>
                    <span v-else-if="a.ncp_status === 'draft'" class="cs-draft">Draft</span>
                    <span v-else class="cs-none">None</span>
                  </td>
                  <td class="right">
                    <button v-if="a.status === 'completed'" type="button" class="nm-btn-outline nm-btn-sm" @click="summaryId = a.id"><FileText :size="13" /> Summary</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <ListPager v-model:page="pastPage" :pages="pastPages" />
        </section>
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
import {
  AlertTriangle, Check, CheckCircle2, Eye, FileText, Pencil, FlaskConical, Info, Lock, MessageSquare, MoreHorizontal, OctagonAlert, Video,
} from 'lucide-vue-next'
import { figureSource, screeningSource } from '~/utils/figureSource'

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
</script>

<style scoped>
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
</style>
