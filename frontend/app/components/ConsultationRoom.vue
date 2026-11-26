<template>
  <div class="room">
    <!-- TOP BAR -->
    <header class="bar">
      <div class="bar-left">
        <span class="brand">Nutri<span class="gold">Match</span></span>
        <template v-if="appt">
          <span class="sep" aria-hidden="true" />
          <span class="who">
            <img v-if="other.photo" :src="other.photo" class="bar-avatar" alt="" />
            <span v-else class="bar-avatar">{{ initials(other.name) }}</span>
            <span class="who-text">
              <strong>{{ other.name }}</strong>
              <small>{{ clock(appt.scheduled_at) }}–{{ clock(endsAt) }}, {{ typeLabel.toLowerCase() }}</small>
            </span>
          </span>
        </template>
      </div>
      <div class="bar-right">
        <span v-if="appt && appt.status === 'confirmed'" class="timer" :class="timerTone"><Clock :size="14" aria-hidden="true" /> {{ timerText }}</span>
        <!-- RND: once the consultation can start, the only way out is Finish
             (mark complete / leave for now / no-show) — no plain Exit. -->
        <button v-if="mustFinish && !callShowsEnd && windowState !== 'closed'" type="button" class="end-btn" @click="openEnd">
          <CheckCircle2 :size="15" /> Finish consultation
        </button>
        <button v-else-if="!mustFinish" type="button" class="exit-btn" @click="inLiveCall ? (callLeaveAsk = true) : exitRoom()">
          <template v-if="!isRnd && appt?.status === 'confirmed' && windowState === 'open'"><PhoneOff :size="15" /> Leave call</template>
          <template v-else><ArrowLeft :size="15" /> Leave</template>
        </button>
      </div>
    </header>

    <div class="body" :class="{ rnd: isRnd }">
      <!-- VIDEO -->
      <main class="stage">
        <p v-if="error" class="state-card err">{{ error }}</p>
        <div v-else-if="loading" class="state-card"><p>Loading…</p></div>
        <div v-else-if="!appt" class="state-card"><VideoOff :size="28" /><p>Consultation not found.</p></div>
        <div v-else-if="appt.status === 'completed' && !isRnd" class="state-card done">
          <span class="done-mark"><CheckCircle2 :size="30" aria-hidden="true" /></span>
          <p class="big">Your consultation is finished</p>
          <p>Thank you for your time, {{ auth.user?.first_name }}. Your consultation with {{ other.firstName }} is complete.</p>
          <p>Your summary is ready. Any updates to your meal plan and care plan show up in NutriMatch once {{ other.firstName }} sends them.</p>
          <div class="done-actions">
            <button type="button" class="link" @click="summaryOpen = true">View the summary</button>
            <button type="button" class="link quiet" @click="exitRoom">Back to My Appointments</button>
          </div>
        </div>
        <div v-else-if="appt.status === 'completed'" class="state-card">
          <CheckCircle2 :size="28" /><p>This consultation is complete.</p>
          <button type="button" class="link" @click="summaryOpen = true">View the summary</button>
          <button type="button" class="link quiet" @click="exitRoom">Leave the room</button>
        </div>
        <div v-else-if="appt.status !== 'confirmed'" class="state-card">
          <VideoOff :size="28" /><p>This consultation {{ appt.status === 'cancelled' ? 'was cancelled' : appt.status === 'no_show' ? 'was marked as a no-show' : appt.status === 'rescheduling' ? 'is being moved to a new time. Answer it in Appointments' : 'isn\'t confirmed yet' }}.</p>
          <p v-if="!isRnd && appt.payment?.status === 'refund_pending'">Your {{ peso(appt.payment.amount) }} payment is refunded in full within 5–7 business days.</p>
          <button type="button" class="link quiet" @click="exitRoom">Leave the room</button>
        </div>
        <!-- Pay first: the API only sends the client the room link once it's paid. -->
        <div v-else-if="!isRnd && appt.payment?.status === 'unpaid'" class="state-card">
          <VideoOff :size="28" />
          <p>Your consultation opens once it's paid. Pay {{ peso(appt.payment.amount) }} before {{ clock(appt.scheduled_at) }} to join.</p>
          <NuxtLink to="/appointments" class="link">Pay in My Appointments</NuxtLink>
        </div>
        <div v-else-if="windowState === 'early'" class="state-card">
          <Clock :size="28" />
          <p class="big">Opens in {{ untilOpen }}</p>
          <p>The room opens {{ clock(appt.join_opens_at) }}{{ demoMode ? '' : ', 15 minutes before the start' }}. This page opens it automatically.</p>
        </div>
        <div v-else-if="windowState === 'closed'" class="state-card">
          <VideoOff :size="28" /><p>The consultation time is over, so the room has closed.</p>
          <button v-if="isRnd" type="button" class="link" @click="openEnd">Finish this consultation</button>
        </div>
        <div v-else-if="appt.type === 'in_person'" class="state-card"><Clock :size="28" /><p>This is an in-person consultation. Meet {{ isRnd ? 'your patient' : 'your RND' }} at the clinic{{ isRnd ? ' and use the panel for your notes' : '' }}.</p></div>
        <!-- NutriMatch's own video call (WebRTC, 2026-10-26): browser to browser,
             encrypted, not recorded. The RND's End opens Finish consultation. -->
        <VideoCall v-else :appointment-id="appt.id" :other-name="other.name" :other-photo="other.photo" :is-rnd="isRnd" class="video" @hangup="onHangUp" @peer-joined="onPeerJoined" @peer-left="recheckAppointment" @time-up="onTimeUp" />
        <!-- The RND never joined: 15 minutes after the start the client can report it (full refund). -->
        <div v-if="rndAbsentReady" class="absent-note" role="status">
          <p><strong>{{ appt.attendance?.rnd_joined_at ? `${other.firstName} left the call.` : `${other.firstName} hasn't joined yet.` }}</strong> If they don't come back, you can report it and get a full refund.</p>
          <button type="button" class="nm-btn-danger solid nm-btn-sm" @click="absentAsk = true; absentError = ''">Report that {{ other.firstName }} didn't show up</button>
        </div>
        <!-- Notes over the top of the call (never over the camera views at the bottom): the RND waiting for a client
             who hasn't joined (when a no-show can be marked, 15 minutes after the start), and the no-overtime wrap-up. -->
        <div class="top-notes">
        <div v-if="rndWaiting" class="wrap-note wait-note" role="status">
          <UserX :size="16" class="wn-ic" aria-hidden="true" />
          <p v-if="noShowOpen && closeOpts.no_show"><strong>{{ other.firstName }} hasn't joined.</strong> You've waited long enough. You can mark a no-show now, or keep waiting.</p>
          <p v-else-if="noShowOpen"><strong>{{ other.firstName }} hasn't joined.</strong> Stay in the call {{ Math.max(1, 5 - (appt.attendance?.rnd_minutes ?? 0)) === 1 ? '1 more minute' : `${Math.max(1, 5 - (appt.attendance?.rnd_minutes ?? 0))} more minutes` }}, then you can mark a no-show.</p>
          <p v-else><strong>Waiting for {{ other.firstName }}.</strong> You can mark a no-show from {{ clock(noShowFrom) }}, 15 minutes after the start ({{ dur(noShowFrom - now) }} to go).</p>
          <button v-if="noShowOpen && closeOpts.no_show" type="button" class="nm-btn-danger solid nm-btn-sm" @click="startNoShow">Mark a no-show</button>
        </div>
        <!-- No overtime (2026-11-16): 15 and 5 minutes before the scheduled end, both people are told to wrap up. -->
        <div v-if="wrapShown && windowState === 'open'" class="wrap-note" role="status" aria-live="polite">
          <Clock :size="16" aria-hidden="true" />
          <p v-if="wrapShown === 15"><strong>{{ minsLeftText }} left.</strong> Time to wrap up. The call ends at {{ clock(endsAt) }}.</p>
          <p v-else><strong>{{ minsLeftText }} left.</strong> The call ends at {{ clock(endsAt) }} and the room closes.</p>
        </div>
        </div>
        <!-- pop-ups over the call (outside the v-if chain above) -->
        <div v-if="callPops.length" class="call-pops" aria-live="polite">
          <div v-for="pop in callPops" :key="pop.id" class="call-pop">
            <span class="call-pop-icon"><FlaskConical :size="16" aria-hidden="true" /></span>
            <div class="call-pop-main">
              <p class="call-pop-title">{{ pop.title }}</p>
              <p class="call-pop-text">{{ pop.text }}</p>
              <div class="call-pop-actions">
                <button type="button" class="call-pop-btn" @click="actOnPop(pop)">{{ pop.actionLabel }}</button>
                <button type="button" class="call-pop-btn soft" @click="dismissPop(pop)">Later</button>
              </div>
            </div>
            <button type="button" class="call-pop-x" aria-label="Dismiss" @click="dismissPop(pop)"><X :size="15" aria-hidden="true" /></button>
          </div>
        </div>
      </main>

      <!-- RND WORK PANEL -->
      <aside v-if="isRnd && appt" class="panel" :class="{ wide: tab === 'ncp' }">
        <nav class="tabs" role="tablist" aria-label="Consultation tools">
          <button v-for="t in RND_TABS" :key="t.key" type="button" role="tab" class="tab" :class="{ on: tab === t.key }" :aria-selected="tab === t.key"
                  :disabled="callEnded && t.key === 'ncp'" @click="tab = t.key">
            <component :is="t.icon" :size="14" /> {{ t.label }}
          </button>
        </nav>
        <p v-if="callEnded" class="ended-note">The video call has ended, so requesting lab tests and writing the NCP record are locked here. Continue from the patient's chart.</p>

        <div class="panel-body">
          <p v-if="!s" class="muted">Loading patient…</p>

          <!-- PATIENT -->
          <template v-else-if="tab === 'patient'">
            <div class="pt-who">
              <img v-if="other.photo" :src="other.photo" class="pt-av" alt="" />
              <span v-else class="pt-av">{{ initials(other.name) }}</span>
              <div class="pt-id"><strong>{{ other.name }}</strong><small v-if="ptSub">{{ ptSub }}</small></div>
            </div>
            <p v-if="s.health.allergies.length" class="allergy"><AlertTriangle :size="14" /> Allergy: {{ s.health.allergies.join(', ') }}</p>
            <p v-if="appt.notes" class="note">“{{ appt.notes }}”<small>Their note when booking</small></p>
            <!-- the four figures; clicking one turns the panel over to explain it
                 (what it is, the formula with this patient's numbers, how to read it) -->
            <p class="pt-sec">At a glance</p>
            <div class="flip" :class="{ flipped: !!statInfo }">
              <div class="stats face" :aria-hidden="!!statInfo" :inert="!!statInfo || undefined">
                <button type="button" class="tile" @click="statInfo = 'weight'">
                  <span class="pt-fi green" aria-hidden="true"><Scale :size="17" /></span><span class="pt-tx">
                  <span>Weight</span><strong>{{ p.progress.latest_weight_kg != null ? `${fmt1(p.progress.latest_weight_kg)} kg` : '—' }}</strong>
                  <small>{{ figureSource(p.progress.weight_origin) || 'not measured yet' }}</small>
                  <small v-if="p.progress.weight_change_kg != null">{{ signed(p.progress.weight_change_kg) }} kg since screening</small></span>
                </button>
                <button type="button" class="tile" @click="statInfo = 'bmi'">
                  <span class="pt-fi gold" aria-hidden="true"><PersonStanding :size="17" /></span><span class="pt-tx">
                  <span>BMI</span><strong>{{ p.progress.bmi != null ? fmt1(p.progress.bmi) : '—' }}</strong>
                  <small>{{ p.progress.bmi_class || '' }}</small>
                  <small v-if="p.progress.bmi_origin">from the weight on {{ figureSource(p.progress.bmi_origin) }}</small></span>
                </button>
                <button type="button" class="tile" @click="statInfo = 'adherence'">
                  <span class="pt-fi blue" aria-hidden="true"><Target :size="17" /></span><span class="pt-tx">
                  <span>Adherence, 7 days</span><strong>{{ p.adherence?.pct != null ? `${p.adherence.pct}%` : '—' }}</strong>
                  <small>{{ p.adherence ? `${p.adherence.logged} of ${p.adherence.planned} logged` : 'no active plan' }}</small></span>
                </button>
                <button type="button" class="tile" :class="{ risk: (s.screening?.nrs_score ?? 0) >= 3 }" @click="statInfo = 'nrs'">
                  <span class="pt-fi green" aria-hidden="true"><ShieldCheck :size="17" /></span><span class="pt-tx">
                  <span>NRS-2002</span><strong>{{ s.screening?.nrs_score ?? '—' }}</strong>
                  <small>{{ s.screening?.nrs_risk || '' }}</small>
                  <small v-if="s.screening">{{ screeningSource(s.screening) }}</small></span>
                </button>
                <p class="flip-hint"><Info :size="13" aria-hidden="true" /> Tap a figure to see what it means.</p>
              </div>

              <section class="info face back" :aria-hidden="!statInfo" :inert="!statInfo || undefined" aria-live="polite">
                <template v-if="statInfo === 'weight'">
                  <h4>Weight</h4>
                  <p>The latest weight on record: <strong>{{ p.progress.latest_weight_kg != null ? `${fmt1(p.progress.latest_weight_kg)} kg` : 'none yet' }}</strong><template v-if="p.progress.weight_origin">, {{ figureSource(p.progress.weight_origin) }}</template>.</p>
                  <p class="formula">Change = latest weight − screening weight<template v-if="p.progress.weight_change_kg != null && s.screening?.weight_kg != null"><br>{{ fmt1(p.progress.latest_weight_kg) }} − {{ fmt1(s.screening.weight_kg) }} = <strong>{{ signed(p.progress.weight_change_kg) }} kg</strong></template></p>
                  <p class="muted">"At consultation" means you measured it and it came from a finalized NCP record. "Self-reported" means {{ p.client.first_name }} typed it in, so check it. A change of 2 kg or more within 14 days is flagged as an alert.</p>
                </template>
                <template v-else-if="statInfo === 'bmi'">
                  <h4>BMI (body mass index)</h4>
                  <p class="formula">BMI = weight (kg) ÷ height (m)²<template v-if="bmiCalc"><br>{{ bmiCalc }}</template></p>
                  <p class="muted">WHO Asia-Pacific cut-offs (lower than the global ones, for Asian adults):</p>
                  <ul class="bands">
                    <li v-for="b in BMI_BANDS" :key="b.label" :class="{ on: p.progress.bmi_class === b.label }"><span>{{ b.label }}</span><span>{{ b.range }}</span></li>
                  </ul>
                </template>
                <template v-else-if="statInfo === 'adherence'">
                  <h4>Meal-plan adherence, last 7 days</h4>
                  <p class="formula">Adherence = score ÷ counted meals × 100<template v-if="p.adherence?.pct != null"><br>{{ p.adherence.logged }} of {{ p.adherence.planned }} planned meals logged, scored <strong>{{ p.adherence.pct }}%</strong></template></p>
                  <ul class="bands">
                    <li><span>Followed</span><span>1 point</span></li>
                    <li><span>Partly followed</span><span>½ point</span></li>
                    <li><span>Not followed, or not logged</span><span>0</span></li>
                    <li><span>Logged, waiting for your rating</span><span>not counted</span></li>
                  </ul>
                  <p class="muted">The goal is 80%. Under 50% is flagged as an alert. Meals count from the day the plan was first sent.</p>
                </template>
                <template v-else-if="statInfo === 'nrs'">
                  <h4>NRS-2002 (nutritional risk screening)</h4>
                  <p class="formula">Score = nutritional status (0–3) + severity of disease (0–3)</p>
                  <ul class="bands">
                    <li><span>BMI under 18.5</span><span>3</span></li>
                    <li><span>Weight loss of 5% or more</span><span>2</span></li>
                    <li><span>Eating less than usual</span><span>1</span></li>
                  </ul>
                  <ul class="bands">
                    <li :class="{ on: (s.screening?.nrs_score ?? -1) >= 0 && s.screening.nrs_score < 3 }"><span>No risk</span><span>0–2</span></li>
                    <li :class="{ on: s.screening?.nrs_score >= 3 && s.screening.nrs_score < 5 }"><span>At risk</span><span>3–4</span></li>
                    <li :class="{ on: s.screening?.nrs_score >= 5 }"><span>High risk</span><span>5 or more</span></li>
                  </ul>
                  <p class="muted">{{ p.client.first_name }} scored {{ s.screening?.nrs_score ?? '—' }} {{ screeningSource(s.screening) }}, from their own answers. It isn't recalculated afterwards, so reassess if their weight or intake has changed.</p>
                </template>
                <button type="button" class="link small soft" @click="statInfo = null"><ArrowLeft :size="13" aria-hidden="true" /> Back to the figures</button>
              </section>
            </div>
            <p class="pt-sec">Details</p>
            <dl class="facts pt-facts">
              <div><dt><HeartPulse :size="15" aria-hidden="true" /> Conditions</dt><dd>{{ list(s.health.conditions) }}</dd></div>
              <div><dt><Leaf :size="15" aria-hidden="true" /> Diet</dt><dd>{{ list(s.health.dietary_restrictions) }}</dd></div>
              <div v-if="s.health.religion"><dt><Church :size="15" aria-hidden="true" /> Religion</dt><dd>{{ s.health.religion }}</dd></div>
              <div><dt><Flag :size="15" aria-hidden="true" /> Goals</dt><dd>{{ list(s.health.health_goals) }}</dd></div>
              <div v-if="s.screening"><dt><Flame :size="15" aria-hidden="true" /> BMR and TER</dt><dd>{{ whole(s.screening.bmr_kcal) }} and {{ whole(s.screening.tdee_kcal) }} kcal</dd></div>
            </dl>
            <section class="block">
              <h3>Current care plan</h3>
              <template v-if="s.care_plan">
                <p v-if="s.care_plan.pes_problem" class="txt"><strong>{{ s.care_plan.pes_problem }}</strong><template v-if="s.care_plan.pes_etiology"> related to {{ s.care_plan.pes_etiology }}</template>.</p>
                <p v-if="s.care_plan.diet_prescription" class="txt">{{ s.care_plan.diet_prescription }}</p>
                <p v-if="s.care_plan.target_kcal" class="muted">TER {{ whole(s.care_plan.target_kcal) }} kcal/day{{ s.care_plan.target_carb_g ? `, ${whole(s.care_plan.target_carb_g)} g carbs, ${whole(s.care_plan.target_protein_g)} g protein, ${whole(s.care_plan.target_fat_g)} g fat` : '' }}</p>
              </template>
              <p v-else class="muted pt-empty">No finalized NCP record yet.</p>
            </section>
            <section v-if="s.recent_logs.length" class="block">
              <h3>Recent meal logs</h3>
              <div v-for="(l, i) in s.recent_logs.slice(0, 6)" :key="i" class="log">
                <span class="log-dot" :class="l.status" aria-hidden="true" />
                <span class="log-main">{{ shortDate(l.date) }}, {{ l.meal }}: {{ LOG[l.status] || 'not rated yet' }}<small v-if="l.note">“{{ l.note }}”</small></span>
              </div>
            </section>
            <section class="block">
              <div class="block-head">
                <h3>Lab results</h3>
                <button type="button" class="link small" :disabled="labsLoading || callEnded" @click="openLabRequest"><FlaskConical :size="13" aria-hidden="true" /> Request lab tests</button>
              </div>
              <p v-if="!s.labs || (!s.labs.total_results && !s.labs.open.length)" class="muted pt-empty">None yet.</p>
              <p v-if="labsSent" class="ok">
                <CheckCircle2 :size="14" aria-hidden="true" />
                <template v-if="windowState === 'open'">Sent. {{ p.client.first_name }} can upload them now, during the call, or later from the Lab results page.</template>
                <template v-else>Sent. {{ p.client.first_name }} can upload them from the Lab results page.</template>
              </p>
              <p v-if="labsError" class="nm-field-error">{{ labsError }}</p>
              <div v-for="r in s.labs?.recent || []" :key="r.id" class="lab-row">
                <span class="lab-main">
                  {{ r.test_names.join(', ') }}, taken {{ shortDate(r.taken_on) }}<template v-if="r.fasted === 'no'">, not fasting</template>
                  <small v-if="!r.reviewed_at && !r.declined_at" class="lab-new">New</small>
                </span>
                <button type="button" class="link small soft" @click="viewLab(r)">View</button>
              </div>
              <p v-for="r in s.labs?.open || []" :key="`q${r.id}`" class="muted">Requested: {{ r.test_names.join(', ') }}, not uploaded yet</p>
            </section>
            <NuxtLink :to="`/client-detail/${appt.relationship.id}`" target="_blank" class="link small soft chart-link"><ExternalLink :size="13" aria-hidden="true" /> Open the full chart in a new tab</NuxtLink>
          </template>

          <!-- NCP (the same form as the chart, inline) -->
          <div v-show="tab === 'ncp'" class="ncp-wrap">
            <NcpRecordModal v-if="ncpMounted" ref="ncpForm" inline :relationship-id="appt.relationship.id" :patient-name="other.name"
                            :appointment-id="appt.id" @changed="refreshSummary" />
          </div>

        </div>
      </aside>

      <!-- CLIENT PANEL -->
      <aside v-else-if="appt" class="panel client">
        <div class="panel-body">
          <div class="rnd-card">
            <img v-if="info?.rnd.profile_photo" :src="info.rnd.profile_photo" class="rnd-photo" alt="" />
            <span v-else class="rnd-photo">{{ initials(info?.rnd.name || other.name) }}</span>
            <div>
              <p class="rnd-name">{{ info?.rnd.name || other.name }}, RND</p>
              <p class="muted">{{ info?.rnd.specialization || 'Registered Nutritionist-Dietitian' }}</p>
            </div>
          </div>
          <dl class="facts">
            <div><dt>Consultation</dt><dd>{{ longWhen(appt.scheduled_at) }}</dd></div>
            <div><dt>Length</dt><dd>{{ appt.duration_minutes || 60 }} minutes</dd></div>
          </dl>
          <section v-if="info?.meal_plan" class="block">
            <h3>Your current meal plan</h3>
            <p class="txt"><strong>{{ info.meal_plan.name }}</strong></p>
            <p v-if="info.meal_plan.target_kcal" class="muted">{{ whole(info.meal_plan.target_kcal) }} kcal a day{{ info.meal_plan.target_carb_g ? `, ${whole(info.meal_plan.target_carb_g)} g carbs, ${whole(info.meal_plan.target_protein_g)} g protein, ${whole(info.meal_plan.target_fat_g)} g fat` : '' }}</p>
          </section>
          <!-- lab results: upload mid-call; the RND sees them straight away -->
          <!-- only while the consultation is still on: a cancelled or finished one has no call to prepare for -->
          <section v-if="labs && appt.status === 'confirmed'" class="block">
            <h3>Lab results</h3>
            <p v-for="r in openLabRequests" :key="r.id" class="lab-ask">
              <FlaskConical :size="13" aria-hidden="true" /> {{ info?.rnd.first_name || 'Your RND' }} asked for: {{ r.test_names.join(', ') }}
            </p>
            <p v-if="!openLabRequests.length" class="muted">Have lab results with you? Upload them so {{ info?.rnd.first_name || 'your RND' }} can see them during the call.</p>
            <label class="link small upload">
              <Upload :size="13" aria-hidden="true" /> Upload lab results
              <input ref="labInput" type="file" :accept="LAB_ACCEPT" multiple class="sr-only" @change="onPickLabs" />
            </label>
            <p v-if="labPickError" class="nm-field-error">{{ labPickError }}</p>
            <p v-if="labsUploaded" class="ok"><CheckCircle2 :size="14" aria-hidden="true" /> Uploaded. {{ info?.rnd.first_name || 'Your RND' }} can open it now.</p>
          </section>

          <section v-if="appt.status === 'confirmed'" class="block">
            <h3>Before your call</h3>
            <ul class="check">
              <li>Allow your camera and microphone when the browser asks.</li>
              <li>Find a quiet, well-lit spot.</li>
              <li>Have your recent meal logs and any lab results ready.</li>
              <li>Write down questions you want to ask.</li>
            </ul>
          </section>
          <p v-if="appt.status === 'confirmed'" class="muted small">Having trouble joining? Message {{ info?.rnd.first_name || 'your RND' }} from Messages.</p>
        </div>
      </aside>
    </div>

    <!-- FINISH CONSULTATION -->
    <div v-if="endOpen" class="overlay" @click.self="!ending && closeEnd()">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="end-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="!ending && closeEnd()"><X :size="18" aria-hidden="true" /></button>
        <template v-if="noShowDone">
          <h2 id="end-title" class="nm-modal-title">Marked as a no-show</h2>
          <p class="nm-modal-text">
            {{ other.firstName }} was told. There's no refund, and your share posts in 3 days unless they dispute it and NutriMatch approves the dispute.
          </p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-dark" @click="leave">Done</button>
          </div>
        </template>
        <template v-else-if="callFailedDone">
          <h2 id="end-title" class="nm-modal-title">Ended as a call that didn't work</h2>
          <p class="nm-modal-text">
            {{ other.firstName }} was told and can book a new time.
            <template v-if="appt.payment?.status === 'refund_pending'">Their {{ peso(appt.payment.amount) }} payment is refunded in full.</template>
          </p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-dark" @click="leave">Done</button>
          </div>
        </template>
        <template v-else-if="endMode === 'noshow'">
          <h2 id="end-title" class="nm-modal-title">{{ other.firstName }} didn't show up?</h2>
          <p class="nm-modal-text">
            It's marked as a no-show and {{ other.firstName }} sees your note. There's no refund: you're paid for it like a completed consultation.
            {{ other.firstName }} can dispute it within 3 days, and NutriMatch decides with the call's attendance record.
          </p>
          <label class="ns-label" for="ns-reason">What happened</label>
          <textarea id="ns-reason" v-model="noShowReason" rows="3" maxlength="500" class="nm-input ns-text"
                    placeholder="e.g. I waited 15 minutes in the room and messaged you, but you didn't join." />
          <p class="ns-hint" :class="{ bad: noShowReason.trim().length > 0 && noShowReason.trim().length < 10 }">At least 10 characters.</p>
          <p v-if="ncpDirty" class="unsaved"><PenLine :size="14" aria-hidden="true" /> Your NCP form has unsaved changes. They'll be saved as a draft first.</p>
          <p v-if="endError" class="nm-field-error">{{ endError }}</p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" :disabled="ending" @click="endMode = 'choose'; endError = ''">Back</button>
            <button type="button" class="nm-btn-danger" :disabled="ending || noShowReason.trim().length < 10" @click="markNoShow">{{ ending ? 'Saving…' : 'Mark as no-show' }}</button>
          </div>
        </template>
        <template v-else-if="endMode === 'callfailed'">
          <h2 id="end-title" class="nm-modal-title">The video call didn't work?</h2>
          <p class="nm-modal-text">
            The consultation is cancelled and {{ other.firstName }} gets a full refund, so there's no payout for this one. They can book a new time.
          </p>
          <label class="ns-label" for="cf-note">What went wrong (optional)</label>
          <textarea id="cf-note" v-model="callFailedNote" rows="2" maxlength="300" class="nm-input ns-text"
                    placeholder="e.g. We could not hear each other." />
          <p v-if="endError" class="nm-field-error">{{ endError }}</p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" :disabled="ending" @click="endMode = 'choose'; endError = ''">Back</button>
            <button type="button" class="nm-btn-danger" :disabled="ending" @click="markCallFailed">{{ ending ? 'Ending…' : 'End and refund' }}</button>
          </div>
        </template>
        <template v-else-if="!wrap">
          <h2 id="end-title" class="nm-modal-title">Finish this consultation?</h2>
          <p class="nm-modal-text">{{ other.name }}, {{ clock(appt.scheduled_at) }}–{{ clock(endsAt) }}</p>
          <p v-if="appt.payment && appt.payment.status !== 'paid'" class="nm-field-error">It hasn't been paid, so it can't be completed.</p>
          <p v-if="ncpDirty" class="unsaved"><PenLine :size="14" aria-hidden="true" /> Your NCP form has unsaved changes. They'll be saved as a draft first.</p>
          <p v-if="endError" class="nm-field-error">{{ endError }}</p>
          <div class="finish-choices">
            <p v-if="closeHint" class="ns-hint">{{ closeHint }}</p>
            <button v-if="closeOpts.complete" type="button" class="choice main" :disabled="ending || (appt.payment && appt.payment.status !== 'paid')" @click="completeNow">
              <CheckCircle2 :size="18" />
              <span><strong>{{ ending ? 'Completing…' : 'It\'s done, mark it complete' }}</strong>
                <small>Your share posts 3 days after today. This can't be undone.</small></span>
            </button>
            <button v-if="started && closeOpts.no_show" type="button" class="choice" :disabled="ending" @click="endMode = 'noshow'; endError = ''">
              <UserX :size="18" />
              <span><strong>{{ other.firstName }} didn't show up</strong>
                <small>Mark as a no-show. No refund, and you're paid for it.</small></span>
            </button>
            <button v-if="appt.type === 'video'" type="button" class="choice" :disabled="ending" @click="endMode = 'callfailed'; endError = ''">
              <PhoneOff :size="18" />
              <span><strong>The video call didn't work</strong>
                <small>Cancel it. {{ other.firstName }} gets a full refund and can book again.</small></span>
            </button>
            <button type="button" class="choice" :disabled="ending" @click="leaveForNow">
              <LogOut :size="18" />
              <span><strong>Leave for now, I'll come back</strong>
                <small>It stays in To complete. {{ appt.type === 'video' ? 'It closes by itself when the room closes, from the call record.' : 'Your payment for it starts only once you mark it complete.' }}</small></span>
            </button>
          </div>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" :disabled="ending" @click="closeEnd">Stay in the room</button>
          </div>
        </template>
        <template v-else>
          <h2 id="end-title" class="nm-modal-title"><CheckCircle2 :size="18" class="ok-icon" /> Consultation complete</h2>
          <p class="nm-modal-text">{{ wrap.todo.length ? 'Before you move on:' : 'Everything for this visit is done.' }}</p>
          <ul v-if="wrap.todo.length" class="todo">
            <li v-for="t in wrap.todo" :key="t.text"><NuxtLink :to="t.link" class="nm-panel-link">{{ t.text }}</NuxtLink></li>
          </ul>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" @click="summaryOpen = true">View summary</button>
            <NuxtLink :to="`/client-detail/${appt.relationship.id}`" class="nm-btn-outline">Open patient chart</NuxtLink>
            <button type="button" class="nm-btn-dark" @click="leave">Done</button>
          </div>
        </template>
      </div>
    </div>

    <!-- LEAVE WITH UNSAVED NCP -->
    <!-- client leaving a live call: ask first, so a stray tap doesn't drop them out -->
    <div v-if="callLeaveAsk" class="overlay" @click.self="stayInCall">
      <div class="nm-modal" role="alertdialog" aria-modal="true" aria-labelledby="call-leave-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="stayInCall"><X :size="18" aria-hidden="true" /></button>
        <h2 id="call-leave-title" class="nm-modal-title">Leave the call?</h2>
        <p class="nm-modal-text">
          {{ other.firstName || 'Your RND' }} stays in the call. You can join again from My Appointments until {{ clock(appt.join_closes_at) }}.
        </p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="stayInCall">Stay</button>
          <button type="button" class="nm-btn-danger solid" @click="callLeaveAsk = false; leave()"><PhoneOff :size="15" aria-hidden="true" /> Leave call</button>
        </div>
      </div>
    </div>

    <div v-if="absentAsk" class="overlay" @click.self="!absentBusy && (absentAsk = false)">
      <div class="nm-modal" role="alertdialog" aria-modal="true" aria-labelledby="absent-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="!absentBusy && (absentAsk = false)"><X :size="18" aria-hidden="true" /></button>
        <h2 id="absent-title" class="nm-modal-title">Report that {{ other.firstName }} didn't show up?</h2>
        <p class="nm-modal-text">
          NutriMatch's call record shows you joined and {{ other.firstName }} {{ appt.attendance?.rnd_joined_at ? 'was in the call for less than 5 minutes' : 'never joined' }}. The consultation is cancelled
          and your {{ peso(appt.payment?.amount) }} payment is refunded in full within 5–7 business days. You can book again any time.
        </p>
        <p v-if="absentError" class="nm-field-error">{{ absentError }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" :disabled="absentBusy" @click="absentAsk = false">Keep waiting</button>
          <button type="button" class="nm-btn-danger solid" :disabled="absentBusy" @click="reportAbsent">{{ absentBusy ? 'Reporting…' : 'Report and get a refund' }}</button>
        </div>
      </div>
    </div>

    <div v-if="leaveAsk" class="overlay" @click.self="leaveAsk = false">
      <div class="nm-modal" role="alertdialog" aria-labelledby="leave-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="leaveAsk = false"><X :size="18" aria-hidden="true" /></button>
        <h2 id="leave-title" class="nm-modal-title">Your NCP form has unsaved changes</h2>
        <p class="nm-modal-text">Save them as a draft before leaving the room?</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="leaveAsk = false">Stay</button>
          <button type="button" class="nm-btn-danger solid" @click="leave">Leave without saving</button>
          <button type="button" class="nm-btn-dark" @click="tab = 'ncp'; leaveAsk = false">Go to the NCP form</button>
        </div>
      </div>
    </div>
    <LabUploadModal
      v-if="pickedLabs.length" :tests="labs.tests" :requests="openLabRequests" :initial-files="pickedLabs"
      @close="pickedLabs = []" @uploaded="onLabsUploaded"
    />
    <RequestLabsModal v-if="labRequest" :relationship-id="appt.relationship.id" :patient-name="other.firstName" :tests="labRequest.tests"
                      :next-consultation="labRequest.next_consultation" @close="labRequest = null" @sent="onLabsSent" />
    <ConsultationSummaryModal v-if="summaryOpen && appt" :appointment-id="appt.id" :role="isRnd ? 'rnd' : 'client'" @close="summaryOpen = false" />
      <LabFileModal
      v-if="viewing" :path="viewing.path" :title="viewing.title" :sub="viewing.sub" :file-name="viewing.fileName" :review-path="viewing.reviewPath"
      @close="viewing = null" @opened="onViewed" @reviewed="onReviewed"
    />
  </div>
</template>

<script setup>
const demoMode = useDemoMode() // scheduling/demo.py: demo times
// The consultation room. RND: video + a work panel (Patient · NCP)
// and "End & mark complete" with a wrap-up of what's left. Client: video +
// their RND, the consultation time and their meal-plan targets — never NCP
// drafts or the RND's notes. Pay-first and the join window are enforced by the
// API (the client gets the room link only when it's paid and inside the window).
import { AlertTriangle, ArrowLeft, CheckCircle2, ClipboardList, Clock, ExternalLink, FlaskConical, LogOut, PenLine, PhoneOff, Upload, User, UserX, VideoOff, X } from 'lucide-vue-next'
import { figureSource, screeningSource } from '~/utils/figureSource'
import { LAB_ACCEPT, labDate, splitLabFiles } from '~/utils/labs'
// UI only: icons for the redesigned patient panel
import { Church, Flag, Flame, HeartPulse, Info, Leaf, PersonStanding, Scale, ShieldCheck, Target } from 'lucide-vue-next'

const route = useRoute()
const auth = useAuthStore()
const { get, patch, post } = useApi()
const now = useNow(15000)
const isRnd = computed(() => auth.user?.role === 'rnd')
const apptId = route.params.id

const appt = ref(null)
const s = ref(null) // RND: patient summary
const info = ref(null) // client: room info
const loading = ref(true)
const error = ref('')
const p = computed(() => s.value?.patient)

// Quietly re-read the consultation; a client whose RND just finished it gets
// the finish screen (the call closes because the room leaves the call state).
async function recheckAppointment() {
  if (isRnd.value) return
  try { await loadAppointment() } catch { /* keep what is shown */ }
}
// the other person just joined: re-read attendance for both sides (waiting and absent notes)
function onPeerJoined() {
  loadAppointment().catch(() => {})
}
async function loadAppointment() {
  appt.value = await get(isRnd.value ? `/rnd/appointments/${apptId}/` : `/client/appointments/${apptId}/`)
}
async function refreshSummary() {
  if (!isRnd.value || !appt.value) return
  s.value = await get(`/rnd/relationships/${appt.value.relationship.id}/summary/`).catch(() => s.value)
}
// Opening a lab file (in a pop-up) marks it reviewed, so refresh the "New" tags after.
const viewing = ref(null)
function viewLab(r) {
  const open = !r.reviewed_at && !r.declined_at
  viewing.value = { path: `/rnd/lab-results/${r.id}/file/`, title: (r.test_names || []).join(', ') || 'Lab result', sub: r.taken_on ? `Taken ${labDate(r.taken_on)}` : '', fileName: r.file_name,
                    reviewPath: open ? `/rnd/lab-results/${r.id}/review/` : '' }
}
function onViewed() {}
function onReviewed() { refreshSummary() }
onMounted(async () => {
  try {
    await loadAppointment()
    if (isRnd.value) await refreshSummary()
    else {
      info.value = await get(`/client/appointments/${apptId}/room-info/`).catch(() => null)
      loadLabs()
    }
  } catch {
    error.value = 'Could not load this consultation.'
  } finally {
    loading.value = false
  }
  // "Close it" in To complete opens the room with the finish choices ready
  if (route.query.finish && isRnd.value && appt.value?.status === 'confirmed') openEnd()
})

/* ---------- client: lab results during the call ---------- */
const labs = ref(null) // GET /client/labs/: tests, requests, results
const pickedLabs = ref([])
const labPickError = ref('')
const labsUploaded = ref(false)
const openLabRequests = computed(() => (labs.value?.requests || []).filter(r => r.status === 'open'))
async function loadLabs() {
  try { labs.value = await get('/client/labs/') } catch { labs.value = null }
}
async function onPickLabs(e) {
  const files = Array.from(e.target.files || [])
  e.target.value = ''
  labsUploaded.value = false
  const { ok, error } = await splitLabFiles(files)
  labPickError.value = error
  if (ok.length) pickedLabs.value = ok
}
async function onLabsUploaded() {
  pickedLabs.value = []
  labsUploaded.value = true
  await loadLabs()
}
// The RND's patient panel picks up new lab results (and other changes) without a reload.
useAutoRefresh(() => (isRnd.value ? refreshSummary() : loadLabs()))

/* ---------- pop-ups over the call: lab tests asked for and sent ---------- */
// The room has no dashboard layout, so it starts the live connection itself;
// the two lab notifications then appear over the call the moment they happen.
const live = useLiveUpdates()
onMounted(() => live.start())
const callPops = ref([])
const labInput = ref(null)
let popSeq = 0
function showPop(pop) {
  callPops.value = [...callPops.value, { id: ++popSeq, ...pop }].slice(-3)
}
function dismissPop(pop) {
  callPops.value = callPops.value.filter(x => x.id !== pop.id)
}
async function actOnPop(pop) {
  dismissPop(pop)
  if (pop.action === 'upload') {
    labInput.value?.click()
  } else if (pop.action === 'view') {
    tab.value = 'patient'
    await refreshSummary()
    const r = (s.value?.labs?.recent || []).find(x => x.id === pop.resultId)
    if (r) viewLab(r)
  }
}
live.onLive('notification', ({ notification: n } = {}) => {
  if (!n || !appt.value) return
  // this consultation changed (finished, cancelled): show its new state
  if (n.notifiable_type === 'appointment' && n.notifiable_id === appt.value.id) recheckAppointment()
  // client: their RND asked for tests (not the "cancelled" notice of the same type)
  if (!isRnd.value && n.notifiable_type === 'lab_request' && n.subject === 'Your RND requested lab tests') {
    loadLabs()
    showPop({ title: `${other.value.firstName || 'Your RND'} requested lab tests`, text: n.content, action: 'upload', actionLabel: 'Upload now' })
  }
  // RND: the patient sent results
  if (isRnd.value && n.notifiable_type === 'lab_result' && n.subject === 'Lab results uploaded') {
    refreshSummary()
    showPop({ title: `${other.value.firstName || 'Your patient'} sent lab results`, text: n.content, action: 'view', actionLabel: 'View', resultId: n.notifiable_id })
  }
})

/* ---------- people / time ---------- */
const other = computed(() => {
  const u = isRnd.value ? appt.value?.relationship.client : appt.value?.relationship.rnd
  return { name: u ? `${u.first_name} ${u.last_name}` : '', firstName: u?.first_name || '', photo: u?.profile_photo || null }
})
const TYPES = { video: 'Video', chat: 'Chat', in_person: 'In person' }
const typeLabel = computed(() => TYPES[appt.value?.type] || '')
const endsAt = computed(() => new Date(new Date(appt.value.scheduled_at).getTime() + (appt.value.duration_minutes || 60) * 60000))
const PH = { timeZone: 'Asia/Manila' }
const clock = v => new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
const longWhen = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
const todayIso = new Date().toLocaleDateString('en-CA', PH)
function dur(ms) {
  const m = Math.max(0, Math.round(ms / 60000))
  return m >= 60 ? `${Math.floor(m / 60)} h ${m % 60} min` : `${m} min`
}
const windowState = computed(() => {
  const a = appt.value
  if (!a?.join_opens_at) return 'open'
  if (now.value < new Date(a.join_opens_at).getTime()) return 'early'
  if (now.value > new Date(a.join_closes_at).getTime()) return 'closed'
  return 'open'
})
const untilOpen = computed(() => dur(new Date(appt.value.join_opens_at).getTime() - now.value))
const timerText = computed(() => {
  const start = new Date(appt.value.scheduled_at).getTime()
  const end = endsAt.value.getTime()
  if (now.value < start) return `Starts in ${dur(start - now.value)}`
  if (now.value <= end) return end - now.value <= 5 * 60000 ? `Ends in ${dur(end - now.value)}` : `${dur(end - now.value)} left`
  return 'Ended'
})
const timerTone = computed(() => {
  const end = endsAt.value.getTime()
  if (now.value > end) return 'over'
  return end - now.value <= 15 * 60000 && now.value >= new Date(appt.value.scheduled_at).getTime() ? 'soon' : ''
})
const started = computed(() => !!appt.value && now.value >= new Date(appt.value.scheduled_at).getTime())
// 15 and 5 minutes before the scheduled end: a note over the call for ~25 s each
const wrapLevel = computed(() => {
  const a = appt.value
  if (!a || a.status !== 'confirmed' || a.type !== 'video' || !started.value) return 0
  const left = (endsAt.value.getTime() - now.value) / 60000
  return left <= 0 ? 0 : left <= 5 ? 5 : left <= 15 ? 15 : 0
})
const wrapShown = ref(0)
// the real time left (joining with 10 minutes to go says 10, not 15)
const minsLeftText = computed(() => {
  // rounded like the top timer (dur), so the note and the timer never disagree
  const m = Math.max(1, Math.round((endsAt.value.getTime() - now.value) / 60000))
  return `${m} minute${m === 1 ? '' : 's'}`
})
let wrapTimer = null
watch(wrapLevel, (level, before) => {
  if (!level || level === before) return
  wrapShown.value = level
  clearTimeout(wrapTimer)
  wrapTimer = setTimeout(() => { wrapShown.value = 0 }, 25000)
}, { immediate: true })
onBeforeUnmount(() => clearTimeout(wrapTimer))
// The server ended the call at the scheduled end and closed the consultation if the call record decides it.
function onTimeUp() {
  wrapShown.value = 0
  setTimeout(async () => {
    try { await loadAppointment() } catch { /* keep what is shown */ }
    if (isRnd.value) refreshSummary()
  }, 1500)
}
// The RND can't just walk out of a consultation that could have started: they
// finish it (mark complete, leave for now, or no-show).
const mustFinish = computed(() => isRnd.value && appt.value?.status === 'confirmed' && windowState.value !== 'early')
// While the video call is up its End button opens the same finish choices, so the top bar doesn't repeat it
// (an in-person consultation has no End button, so it keeps "Finish consultation"; a closed room shows the
// same button in the middle of the screen, so the top bar doesn't repeat it).
// The video call is over (the room closes at the scheduled end): the work panel's actions are locked,
// so nothing gets added to a consultation after the call (2026-11-16). Reading the patient's info still works.
const callEnded = computed(() => isRnd.value && appt.value?.type === 'video' && windowState.value === 'closed')
watch(callEnded, (ended) => { if (ended && tab.value === 'ncp') tab.value = 'patient' })
const callShowsEnd = computed(() => isRnd.value && appt.value?.type === 'video' && appt.value?.status === 'confirmed' && windowState.value === 'open')
// The client gets the room link only inside the window — fetch it when it opens.
let refetched = false
watch(windowState, (state, prev) => {
  if (prev === 'early' && state === 'open' && !refetched) { refetched = true; loadAppointment() }
})

/* ---------- RND panel ---------- */
const RND_TABS = [
  { key: 'patient', label: 'Patient', icon: User },
  { key: 'ncp', label: 'NCP', icon: ClipboardList },
]
const tab = ref('patient')
const ncpForm = ref(null)
const ncpMounted = ref(false)
watch(tab, (t) => { if (t === 'ncp') ncpMounted.value = true }) // load the form the first time it's opened
const ncpDirty = computed(() => !!ncpForm.value?.dirty)

const SEX = { male: 'Male', female: 'Female' }
const LOG = { followed: 'followed', partially_followed: 'partly followed', not_followed: 'not followed' }
const list = l => (l?.length ? l.join(', ') : '—')
const whole = v => (v == null ? '—' : Math.round(Number(v)).toLocaleString('en-PH'))
// the figure whose explanation is showing on the back of the panel
const statInfo = ref(null)
const BMI_BANDS = [
  { label: 'Underweight', range: 'under 18.5' }, { label: 'Normal', range: '18.5–22.9' }, { label: 'Overweight (At Risk)', range: '23–24.9' },
  { label: 'Obese I', range: '25–29.9' }, { label: 'Obese II', range: '30 or more' },
]
const bmiCalc = computed(() => {
  const w = Number(p.value?.progress?.latest_weight_kg)
  const h = Number(s.value?.screening?.height_cm) / 100
  if (!w || !h) return ''
  return `${w.toFixed(1)} ÷ ${h.toFixed(2)}² = ${(w / (h * h)).toFixed(1)}`
})
const fmt1 = v => Number(v).toFixed(1)
const signed = v => `${Number(v) > 0 ? '+' : Number(v) < 0 ? '−' : ''}${Math.abs(Number(v)).toFixed(1)}`
const initials = n => String(n || '').split(' ').filter(Boolean).map(x => x[0]).slice(0, 2).join('').toUpperCase()

/* ---------- lab tests (same pop-up as the chart) ---------- */
// Measurements are typed once, in the NCP Assessment; finalizing it saves
// them to the patient's progress (no separate Progress tab, 2026-10-23).
const labRequest = ref(null) // { tests, next_consultation } while the pop-up is open
const labsLoading = ref(false)
const labsError = ref('')
const labsSent = ref(false)
async function openLabRequest() {
  labsError.value = ''
  labsSent.value = false
  labsLoading.value = true
  try {
    const d = await get(`/rnd/relationships/${appt.value.relationship.id}/labs/`)
    if (!d.can_request) labsError.value = 'Lab tests can be requested for active patients only.'
    else labRequest.value = { tests: d.tests, next_consultation: d.next_consultation }
  } catch (e) {
    labsError.value = apiError(e, 'Could not open the lab request.')
  } finally {
    labsLoading.value = false
  }
}
function onLabsSent() {
  labRequest.value = null
  labsSent.value = true
  refreshSummary()
}

/* ---------- end & mark complete ---------- */
const summaryOpen = ref(false)
const endOpen = ref(false)
const ending = ref(false)
const endError = ref('')
const wrap = ref(null)
const endMode = ref('choose') // choose | noshow
const noShowReason = ref('')
const noShowDone = ref(false)
const callFailedNote = ref('')
const callFailedDone = ref(false)
// From the call's attendance record (the server refuses a no-show too).
const clientJoined = computed(() => !!appt.value?.attendance?.client_joined_at)
// What the call record allows (scheduling/closing.py): a video consultation completes by itself
// when both were together for 5 minutes; a no-show needs the RND to have waited.
const closeOpts = computed(() => appt.value?.close_options || { complete: true, no_show: true, refund: true })
// A no-show opens 15 minutes after the start (NO_SHOW_AFTER_MINUTES), so the client has time to arrive.
const noShowFrom = computed(() => (appt.value?.no_show_opens_at ? new Date(appt.value.no_show_opens_at).getTime() : 0))
const noShowOpen = computed(() => !!noShowFrom.value && now.value >= noShowFrom.value)
// one sentence saying why a choice is missing
const closeHint = computed(() => {
  const a = appt.value
  if (!a) return ''
  const name = other.value.firstName || 'the patient'
  const early = !!noShowFrom.value && !noShowOpen.value
  if (a.type !== 'video') return early ? `A no-show can be marked from ${clock(noShowFrom.value)}, 15 minutes after the start, so ${name} has time to arrive.` : ''
  if (closeOpts.value.complete) return ''
  if (closeOpts.value.no_show) return `${name} never joined, so it can’t be marked complete. You can mark a no-show or end it with a refund.`
  if (!a.attendance?.client_joined_at && early) return `${name} hasn’t joined yet. You can mark a no-show from ${clock(noShowFrom.value)}, 15 minutes after the start.`
  if ((a.attendance?.rnd_minutes ?? 0) < 5) return 'You weren’t in the video call for 5 minutes, so it can only be refunded.'
  return `You and ${name} weren’t in the call together for 5 minutes, so it can only be refunded.`
})
// the RND is on this page waiting for a client who hasn't joined (the note's own refresh tells them when they've waited enough)
const rndWaiting = computed(() => isRnd.value && appt.value?.status === 'confirmed' && appt.value?.type === 'video'
  && started.value && windowState.value === 'open' && !appt.value?.attendance?.client_joined_at)
// the answer to "can I mark it yet?" changes with the clock: re-read it when the wait is over, and each minute while waiting
watch(noShowOpen, (open) => { if (open && isRnd.value) loadAppointment().catch(() => {}) })
let waitTimer = null
onMounted(() => {
  waitTimer = setInterval(() => { if (rndWaiting.value) loadAppointment().catch(() => {}) }, 30000)
})
onBeforeUnmount(() => clearInterval(waitTimer))
function startNoShow() {
  openEnd()
  endMode.value = 'noshow'
}
function openEnd() {
  endError.value = ''
  wrap.value = null
  endMode.value = 'choose'
  endOpen.value = true
  loadAppointment().catch(() => {}) // fresh attendance: did the client join?
}
function closeEnd() {
  endOpen.value = false
  pendingTo = null
}
async function saveNcpIfDirty() {
  if (ncpDirty.value && ncpForm.value?.saveDraft) await ncpForm.value.saveDraft()
}
// "I'll come back": keep unsaved NCP work as a draft, then go.
async function leaveForNow() {
  ending.value = true
  endError.value = ''
  try {
    await saveNcpIfDirty()
    leave()
  } catch (e) {
    endError.value = apiError(e, 'Could not save your NCP draft.')
  } finally {
    ending.value = false
  }
}
async function markNoShow() {
  ending.value = true
  endError.value = ''
  try {
    await saveNcpIfDirty()
    await post(`/rnd/appointments/${apptId}/no-show/`, { note: noShowReason.value.trim() })
    await loadAppointment()
    noShowDone.value = true
  } catch (e) {
    endError.value = apiError(e, 'Could not mark this as a no-show.')
    loadAppointment().catch(() => {})
  } finally {
    ending.value = false
  }
}
async function markCallFailed() {
  ending.value = true
  endError.value = ''
  try {
    await saveNcpIfDirty()
    await post(`/rnd/appointments/${apptId}/call-failed/`, { note: callFailedNote.value.trim() })
    await loadAppointment()
    callFailedDone.value = true
  } catch (e) {
    endError.value = apiError(e, 'Could not end this consultation.')
  } finally {
    ending.value = false
  }
}
async function completeNow() {
  ending.value = true
  endError.value = ''
  try {
    await saveNcpIfDirty()
    await patch(`/rnd/appointments/${apptId}/complete/`)
    await loadAppointment()
    await refreshSummary()
    const rel = appt.value.relationship.id
    const todo = []
    if (s.value?.ncp_draft_id) todo.push({ text: 'Finish and finalize the NCP record', link: `/client-detail/${rel}?tab=ncp&open=draft` })
    else if (!s.value?.care_plan || s.value.care_plan.encounter_date < todayIso) todo.push({ text: 'Write an NCP record for this visit', link: `/client-detail/${rel}?tab=ncp` })
    const mp = s.value?.patient.meal_plan
    if (mp?.ready && (!mp.plan || mp.plan.status === 'draft' || mp.outdated)) {
      todo.push({ text: !mp.plan ? 'Create a meal plan' : mp.plan.status === 'draft' ? 'Send the meal plan' : 'Update the meal plan', link: `/meal-planning?relationship=${rel}` })
    }
    wrap.value = { todo }
  } catch (e) {
    endError.value = apiError(e, 'Could not complete this consultation.')
  } finally {
    ending.value = false
  }
}

/* ---------- leaving ---------- */
const leaveAsk = ref(false)
// the client in a live video call: leaving asks first (Stay / Leave call)
const callLeaveAsk = ref(false)

/* ---------- client: the RND didn't come ---------- */
const RND_ABSENT_AFTER_MS = 15 * 60 * 1000 // RND_ABSENT_AFTER_MINUTES
const rndAbsentReady = computed(() => !isRnd.value && appt.value?.status === 'confirmed' && appt.value?.type === 'video'
  && appt.value?.payment?.status === 'paid' && !appt.value?.attendance?.rnd_in_call
  && (appt.value?.attendance?.rnd_minutes ?? 0) < 5 // RND_MIN_PRESENT_MINUTES: a brief join doesn't count
  && now.value >= new Date(appt.value.scheduled_at).getTime() + RND_ABSENT_AFTER_MS)
const absentAsk = ref(false)
const absentBusy = ref(false)
const absentError = ref('')
async function reportAbsent() {
  absentBusy.value = true
  absentError.value = ''
  try {
    await post(`/client/appointments/${apptId}/rnd-absent/`)
    absentAsk.value = false
    await loadAppointment()
  } catch (e) {
    absentError.value = apiError(e, 'Could not report it.')
    loadAppointment().catch(() => {})
  } finally {
    absentBusy.value = false
  }
}
// While the client waits past the start, re-read attendance each minute (did the RND join?).
let absentTimer = null
onMounted(() => {
  if (isRnd.value) return
  absentTimer = setInterval(() => {
    const a = appt.value
    if (a?.status === 'confirmed' && a.type === 'video' && (a.attendance?.rnd_minutes ?? 0) < 5
        && Date.now() >= new Date(a.scheduled_at).getTime()) recheckAppointment()
  }, 60000)
})
onBeforeUnmount(() => clearInterval(absentTimer))
const inLiveCall = computed(() => !isRnd.value && appt.value?.type === 'video' && appt.value?.status === 'confirmed'
  && windowState.value === 'open' && appt.value?.payment?.status === 'paid')
function stayInCall() {
  callLeaveAsk.value = false
  pendingTo = null
}
let leaving = false // set once the RND chose how to leave, so the guard lets it through
let pendingTo = null // where a blocked navigation (Back, a link) was going
function exitRoom() {
  if (mustFinish.value) { openEnd(); return }
  if (ncpDirty.value) { leaveAsk.value = true; return }
  leave()
}
function leave() {
  leaveAsk.value = false
  endOpen.value = false
  leaving = true
  const to = pendingTo
  pendingTo = null
  // Back to the app page we came from (or My Appointments).
  navigateTo(to || window.history.state?.back || '/appointments')
}
// Browser Back, the sidebar or any link: ask the same Finish question first.
onBeforeRouteLeave((to) => {
  if (leaving) return true
  if (mustFinish.value) { pendingTo = to.fullPath; openEnd(); return false }
  if (ncpDirty.value) { pendingTo = to.fullPath; leaveAsk.value = true; return false }
  if (inLiveCall.value) { pendingTo = to.fullPath; callLeaveAsk.value = true; return false }
  return true
})
// Closing or reloading the tab: the browser's own "Leave site?" prompt.
function onBeforeUnload(e) {
  if (!leaving && (mustFinish.value || ncpDirty.value)) { e.preventDefault(); e.returnValue = '' }
}
onMounted(() => window.addEventListener('beforeunload', onBeforeUnload))
onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload))

/* ---------- video (WebRTC, components/VideoCall.vue) ---------- */
// The RND's End asks how to finish (complete, no-show, come back later) and
// the call stays open meanwhile; the client's Leave just leaves the room.
function onHangUp() {
  if (mustFinish.value) openEnd()
  else if (inLiveCall.value) callLeaveAsk.value = true
  else exitRoom()
}

/* ---------- UI only: patient panel header line ---------- */
const ptSub = computed(() => {
  const c = p.value?.client
  if (!c) return ''
  return [c.age != null ? `${c.age} y/o` : null, SEX[c.sex], ...(s.value?.health?.conditions || [])].filter(Boolean).join(', ')
})
</script>

<style scoped>
* { box-sizing: border-box; }
.lab-ask { display: flex; gap: 6px; align-items: flex-start; margin: 0 0 6px; font-size: 0.82rem; color: #7a560f; font-weight: 600; }
.lab-ask svg { flex-shrink: 0; margin-top: 2px; }
.upload { margin-top: 8px; cursor: pointer; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.stage { position: relative; }
.top-notes { position: absolute; top: 14px; left: 50%; transform: translateX(-50%); z-index: 6; display: flex; flex-direction: column; align-items: center; gap: 8px; width: max-content; max-width: calc(100% - 28px); }
.wrap-note { display: flex; align-items: center; gap: 10px; max-width: 100%;
  background: #fdf1d6; color: #5c4400; border: 1px solid #e7c874; border-radius: 12px; padding: 10px 14px; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22); }
.wrap-note p { margin: 0; font-size: 0.88rem; }
.wait-note { background: #fff; color: #1a3a1a; border-color: #d9e3dc; flex-wrap: wrap; }
.wait-note p { flex: 1 1 200px; }
.ended-note { margin: 0; padding: 10px 16px; font-size: 0.82rem; color: #6a7a6a; background: #f2f5f2; border-bottom: 1px solid #d9e3dc; }
.tab:disabled, .panel .link:disabled { opacity: 0.45; cursor: not-allowed; }
.absent-note { position: absolute; left: 14px; right: 14px; bottom: 96px; z-index: 5; display: flex; align-items: center; gap: 10px 14px; flex-wrap: wrap;
  padding: 12px 14px; border-radius: 12px; background: #fff; border: 1px solid #f1c9c9; box-shadow: 0 0 2px rgba(0,77,58,.08), 0 0 24px rgba(0,77,58,.22); }
.absent-note p { margin: 0; flex: 1 1 240px; font-size: 0.86rem; color: #1a3a1a; }
.call-pops { position: absolute; top: 14px; right: 14px; z-index: 5; display: flex; flex-direction: column; gap: 8px; width: min(340px, calc(100% - 28px)); }
.call-pop {
  position: relative; display: flex; gap: 10px; padding: 12px 34px 12px 12px; border-radius: 12px; background: #fff; color: #1a3a1a;
  box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 0, 0, 0.35);
}
@media (prefers-reduced-motion: no-preference) {
  .call-pop { animation: pop-in 0.25s ease-out; }
  @keyframes pop-in { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: none; } }
}
.call-pop-icon { width: 32px; height: 32px; border-radius: 9px; background: #e3efe7; color: #0a4a37; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.call-pop-main { min-width: 0; }
.call-pop-title { margin: 0; font-size: 0.88rem; font-weight: 700; }
.call-pop-text { margin: 2px 0 0; font-size: 0.8rem; color: #4a5a4a; line-height: 1.45; overflow-wrap: anywhere; }
.call-pop-actions { display: flex; gap: 8px; margin-top: 8px; }
.call-pop-btn { min-height: 32px; padding: 0 12px; border-radius: 8px; border: none; cursor: pointer; font-family: inherit; font-size: 0.8rem; font-weight: 700; background: #0a4a37; color: #fff; }
.call-pop-btn:hover { background: #00382a; }
.call-pop-btn.soft { background: #e3efe7; color: #0a4a37; }
.call-pop-btn.soft:hover { background: #d3e7da; }
.call-pop-x { position: absolute; top: 6px; right: 6px; width: 26px; height: 26px; border: none; background: none; color: #6a7a6a; cursor: pointer; border-radius: 6px; display: flex; align-items: center; justify-content: center; }
.state-card.done { max-width: 420px; gap: 8px; }
.done-mark { width: 56px; height: 56px; border-radius: 50%; background: rgba(159, 207, 179, 0.18); color: #9fcfb3; display: flex; align-items: center; justify-content: center; margin-bottom: 4px; }
.done-actions { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-top: 8px; }
.room { height: 100vh; height: 100dvh; display: flex; flex-direction: column; background: #0d1f18; font-family: 'Inter', sans-serif; color: #1a3a1a; }

.bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 18px; color: #fff; flex-shrink: 0; flex-wrap: wrap; }
.bar-left, .bar-right { display: flex; align-items: center; gap: 12px; min-width: 0; }
.brand { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.05rem; }
.gold { color: #D4A017; }
.sep { width: 1px; height: 26px; background: rgba(255, 255, 255, 0.18); }
.who { display: flex; align-items: center; gap: 10px; min-width: 0; }
.bar-avatar { width: 32px; height: 32px; border-radius: 50%; background: #e3efe7; color: #1e4a26; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; object-fit: cover; }
.who-text { display: flex; flex-direction: column; min-width: 0; }
.who-text strong { font-size: 0.88rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.who-text small { font-size: 0.72rem; color: #a9c2b0; }
.timer { display: inline-flex; align-items: center; min-height: 34px; font-size: 0.8rem; font-weight: 700; padding: 0 14px; border-radius: 999px; background: rgba(255, 255, 255, 0.1); font-variant-numeric: tabular-nums; white-space: nowrap; }
.timer.soon { background: #D4A017; color: #1a3a1a; }
.timer.over { background: #c0392b; }
.end-btn, .exit-btn { display: inline-flex; align-items: center; gap: 6px; min-height: 34px; border-radius: 999px; padding: 7px 14px; font-family: inherit; font-size: 0.8rem; font-weight: 700; cursor: pointer; white-space: nowrap; }
.end-btn { background: #D4A017; color: #1a3a1a; border: none; }
.end-btn:hover { background: #e2b02a; }
.exit-btn { background: rgba(255, 255, 255, 0.1); color: #fff; border: 1px solid rgba(255, 255, 255, 0.2); }

.body { flex: 1; display: flex; min-height: 0; }
.stage { flex: 1; display: flex; align-items: center; justify-content: center; min-width: 0; min-height: 0; }
.video { width: 100%; height: 100%; border: none; }
.state-card { display: flex; flex-direction: column; align-items: center; gap: 10px; max-width: 340px; text-align: center; color: #a9c2b0; font-size: 0.88rem; padding: 20px; }
.state-card p { margin: 0; line-height: 1.5; }
.state-card .big { font-size: 1.4rem; font-weight: 700; color: #fff; }
.state-card.err { color: #f3b8b8; }
.link {
  display: inline-flex; align-items: center; justify-content: center; gap: 5px; min-height: 36px; padding: 0 16px; border-radius: 8px;
  background: #D4A017; color: #1a3a1a; border: none; font-family: inherit; font-weight: 700; font-size: 0.85rem; line-height: 1.2;
  text-decoration: none; white-space: nowrap; cursor: pointer;
}
.link:hover:not(:disabled) { background: #e0ae22; }
.link:disabled { opacity: 0.5; cursor: not-allowed; }
.link:focus-visible { outline: 2px solid #e2c25e; outline-offset: 2px; }
.link.quiet { background: rgba(255, 255, 255, 0.12); color: #e6efe9; font-weight: 600; }
.link.quiet:hover { background: rgba(255, 255, 255, 0.2); }
.chart-link { display: inline-flex; align-items: center; gap: 5px; }
.panel .link { background: #e3efe7; color: #0a4a37; font-weight: 600; }
.panel .link:hover:not(:disabled) { background: #d3e7da; }
.panel .link:focus-visible { outline-color: #1f8f5c; }
.link.small { font-size: 0.78rem; min-height: 32px; padding: 0 12px; margin-top: 12px; }
/* in the light side panel: dark green action, light green secondary (gold is only for the dark room) */
.link.small { background: #0a4a37; color: #fff; }
.link.small:hover:not(:disabled) { background: #00382a; }
.link.small.soft { background: #e3efe7; color: #0a4a37; }
.link.small.soft:hover:not(:disabled) { background: #d3e7da; }
.link.small:focus-visible { outline-color: #1f8f5c; }
.lab-row { display: flex; align-items: baseline; gap: 8px; padding: 4px 0; font-size: 0.78rem; }
.lab-main { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.lab-row .link.small { margin-top: 0; }
.lab-new { margin-left: 6px; font-size: 0.68rem; font-weight: 700; color: #1f6f46; background: #e3f3ea; border-radius: 8px; padding: 1px 6px; }

.panel { width: 340px; background: #f9faf8; display: flex; flex-direction: column; flex-shrink: 0; min-height: 0; border-radius: 14px 0 0 0; overflow: hidden; }
.body.rnd .panel { width: 460px; }
.tabs { display: flex; gap: 4px; padding: 10px 12px; border-bottom: 1px solid #d9e3dc; background: #fff; }
.tab { flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: none; background: none; padding: 8px; border-radius: 999px; font-family: inherit; font-size: 0.8rem; font-weight: 600; color: #6a7a6a; cursor: pointer; }
.tab.on { background: #0a4a37; color: #fff; }
.tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.panel-body { flex: 1; overflow-y: auto; padding: 16px; min-height: 0; }
.ncp-wrap { height: 100%; margin: -16px; }
.ncp-wrap :deep(.ncp.is-inline) { border: none; border-radius: 0; }
.muted { font-size: 0.8rem; color: #7a8a7a; margin: 0; line-height: 1.5; }
.muted.small { margin-top: 14px; }

.allergy { display: flex; align-items: center; gap: 6px; background: #fdecec; color: #a12525; border-radius: 8px; padding: 8px 10px; font-size: 0.82rem; font-weight: 700; margin: 0 0 10px; }
.note { background: #fff; border: 1px solid #d9e3dc; border-radius: 8px; padding: 8px 10px; font-size: 0.82rem; font-style: italic; margin: 0 0 12px; display: flex; flex-direction: column; gap: 2px; }
.note small { font-style: normal; color: #8a9a8a; font-size: 0.7rem; }
.stats { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); margin-bottom: 12px; background: #fff; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden;
  box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.stats .tile {
  padding: 10px 12px; display: flex; flex-direction: column; align-items: flex-start; min-width: 0; text-align: left;
  border: 0; background: #fff; font-family: inherit; color: #1a3a1a; cursor: pointer;
}
.stats .tile:hover { background: #f7faf8; }
.stats .tile:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.stats .tile:nth-child(even) { border-left: 1px solid #d9e3dc; }
.stats .tile:nth-child(n+3) { border-top: 1px solid #d9e3dc; }
.stats .tile.risk { background: #fdf3f2; }
.stats .tile.risk strong, .stats .tile.risk small { color: #a12525; }
.flip-hint { grid-column: 1 / -1; margin: 0; padding: 6px 12px; border-top: 1px solid #d9e3dc; font-size: 0.7rem; color: #8a9a8a; background: #f7faf8; }
/* both faces share one grid cell, so the panel is as tall as the longer one */
.flip { display: grid; margin-bottom: 12px; perspective: 1200px; }
.flip > .face { grid-area: 1 / 1; backface-visibility: hidden; -webkit-backface-visibility: hidden; }
.flip > .stats { margin-bottom: 0; }
.flip > .back { transform: rotateY(180deg); }
.flip.flipped > .stats { transform: rotateY(-180deg); }
.flip.flipped > .back { transform: rotateY(0deg); }
@media (prefers-reduced-motion: no-preference) {
  .flip > .face { transition: transform 0.45s ease; }
}
.info {
  background: #fff; border: 1px solid #d9e3dc; border-radius: 12px; padding: 12px 14px; font-size: 0.8rem; color: #2a3a2a; line-height: 1.5;
  box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09);
}
.info h4 { margin: 0 0 6px; font-family: inherit; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.info p { margin: 0 0 8px; }
.info .formula { background: #f2f7f3; border-radius: 8px; padding: 8px 10px; font-variant-numeric: tabular-nums; }
.info .bands { list-style: none; margin: 0 0 8px; padding: 0; border: 1px solid #d9e3dc; border-radius: 8px; overflow: hidden; }
.info .bands li { display: flex; justify-content: space-between; gap: 10px; padding: 5px 10px; font-size: 0.76rem; }
.info .bands li + li { border-top: 1px solid #edf1ee; }
.info .bands li.on { background: #e3efe7; font-weight: 700; color: #0a4a37; }
.info .link.small { margin-top: 4px; }
.stats span { font-size: 0.74rem; font-weight: 600; color: #4a5a4a; }
.stats strong { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-variant-numeric: tabular-nums lining-nums; }
.stats small { font-size: 0.7rem; color: #8a9a8a; }
.facts { margin: 0 0 4px; }
.facts div { display: flex; justify-content: space-between; gap: 10px; padding: 6px 0; border-top: 1px solid #d9e3dc; }
.facts div:first-child { border-top: none; }
.facts dt { font-size: 0.74rem; color: #8a9a8a; margin: 0; }
.facts dd { margin: 0; font-size: 0.8rem; font-weight: 600; text-align: right; overflow-wrap: anywhere; }
.block { margin-top: 14px; padding-top: 12px; border-top: 1px solid #d9e3dc; }
.block-head { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.block-head .link.small { margin-top: 0; display: inline-flex; align-items: center; gap: 4px; }
.block h3 { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0 0 6px; }
.txt { font-size: 0.82rem; line-height: 1.5; margin: 0 0 4px; }
.log { display: flex; gap: 8px; align-items: baseline; padding: 4px 0; font-size: 0.78rem; }
.log-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; background: #b0bab0; }
.log-dot.followed { background: #1f8f5c; }
.log-dot.partially_followed { background: #D4A017; }
.log-dot.not_followed { background: #c0392b; }
.log-main small { display: block; color: #7a8a7a; font-style: italic; }

.ok { display: flex; align-items: center; gap: 6px; color: #1f6f46; font-size: 0.8rem; font-weight: 600; margin: 0; }

.client .rnd-card { display: flex; gap: 12px; align-items: center; margin-bottom: 14px; }
.rnd-photo { width: 52px; height: 52px; border-radius: 50%; background: #e3efe7; color: #1e4a26; display: flex; align-items: center; justify-content: center; font-weight: 700; object-fit: cover; flex-shrink: 0; }
.rnd-name { font-family: 'Playfair Display', serif; font-weight: 700; margin: 0; }
.check { margin: 0; padding-left: 18px; font-size: 0.8rem; line-height: 1.7; color: #3a4a3a; }

.overlay { position: fixed; inset: 0; background: rgba(20, 30, 20, 0.55); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 300; }
.unsaved { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #1f4a30; background: #fff; border: 1.5px dashed #3f9a6b; border-radius: 10px; padding: 9px 12px; margin: 0 0 12px; }
.unsaved svg { flex-shrink: 0; color: #3f9a6b; }
.todo { list-style: none; margin: 0 0 8px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.todo li { border: 1.5px dashed #3f9a6b; border-radius: 10px; padding: 9px 12px; }
.todo .nm-panel-link { white-space: normal; text-align: left; padding: 6px 12px; }
.ok-icon { color: #1f8f5c; vertical-align: -3px; }
.finish-choices { display: flex; flex-direction: column; gap: 8px; margin: 4px 0 6px; }
.choice { display: flex; align-items: flex-start; gap: 12px; width: 100%; text-align: left; background: #fff; border: 1px solid #d9e3dc; border-radius: 12px; padding: 12px 14px; font-family: inherit; color: #1a3a1a; cursor: pointer; }
.choice:hover:not(:disabled) { border-color: #1f6f46; background: #f6faf7; }
.choice:disabled { opacity: 0.55; cursor: not-allowed; }
.choice svg { flex-shrink: 0; margin-top: 1px; color: #5a6a5a; }
.choice span { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.choice strong { font-size: 0.9rem; }
.choice small { font-size: 0.76rem; color: #6a7a6a; line-height: 1.4; }
.choice.main { background: linear-gradient(135deg, #00382a 0%, #005a42 100%); border-color: #00382a; color: #fff; }
.choice.main svg { color: #e2c25e; }
.choice:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.choice.main small { color: #c4d6c9; }
.choice.main:hover:not(:disabled) { background: linear-gradient(135deg, #00402f 0%, #00684c 100%); border-color: #00402f; }
.ns-label { display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px; }
.ns-text { width: 100%; resize: vertical; }
.ns-hint { font-size: 0.72rem; color: #8a9a8a; margin: 4px 0 10px; }
.ns-hint.bad { color: #c0392b; }

@media (max-width: 1100px) { .body.rnd .panel { width: 400px; } }
@media (max-width: 860px) {
  .room { height: auto; min-height: 100vh; }
  .body, .body.rnd { flex-direction: column; }
  .stage { height: 52vh; flex: none; }
  .panel, .body.rnd .panel { width: 100%; border-radius: 14px 14px 0 0; min-height: 60vh; }
  .ncp-wrap { height: auto; }
  .who-text small { display: none; }
  .bar-right { width: 100%; justify-content: flex-end; flex-wrap: wrap; }
}

/* ===== UI refresh (2026-11-23): room + side panel, matches the canvas ===== */
.room { background: #0B1F18; font-family: 'DM Sans', 'Inter', sans-serif; }
.bar { min-height: 64px; padding: 10px 20px; background: #081A14; }
.brand { font-size: 1.25rem; }
.gold { color: #EFBF04; }
.sep { height: 28px; background: rgba(255, 255, 255, 0.15); }
.bar-avatar { width: 36px; height: 36px; }
.who-text strong { font-size: 0.92rem; }
.timer { gap: 6px; min-height: 36px; font-weight: 800; }
.timer.soon, .end-btn { background: #EFBF04; color: #004D3A; }
.end-btn { min-height: 36px; font-weight: 800; }
.end-btn:hover { background: #f5cb22; }
.exit-btn { min-height: 36px; }
.stage { background: radial-gradient(80% 70% at 50% 45%, #12352A, #0B1F18 70%); }
.state-card { max-width: 380px; color: #A9C9B9; font-size: 0.9rem; }
.state-card > svg { width: 64px; height: 64px; padding: 16px; border-radius: 50%; color: #EFBF04; background: rgba(239, 191, 4, 0.12); box-shadow: 0 0 0 8px rgba(239, 191, 4, 0.06); }
.state-card .big { font-family: 'Playfair Display', serif; font-size: 1.6rem; }
.link { border-radius: 12px; min-height: 42px; padding: 0 20px; background: #EFBF04; color: #004D3A; font-weight: 800; }
.link:hover:not(:disabled) { background: #f5cb22; }

/* waiting for the patient: gold glass note over the call */
.wait-note { background: rgba(239, 191, 4, 0.14); border: 1px solid rgba(239, 191, 4, 0.35); color: #F6E3A0; border-radius: 14px; padding: 10px 16px; backdrop-filter: blur(6px); box-shadow: none; }
.wait-note p { color: #F6E3A0; }
.wait-note strong { color: #fff; }
.wn-ic { flex-shrink: 0; color: #EFBF04; }

/* side panel */
.panel { background: #F7FAF8; border-radius: 22px 0 0 0; }
.body.rnd .panel.wide { width: min(820px, 62vw); }
.tabs { margin: 12px; padding: 4px; gap: 4px; border: none; border-radius: 14px; background: #E8EFEB; }
.tab { height: 40px; border-radius: 10px; font-size: 0.86rem; font-weight: 700; color: #4A5A52; }
.tab.on { background: #fff; color: #004D3A; font-weight: 800; box-shadow: 0 2px 8px -2px rgba(16, 35, 27, 0.25); }
.ended-note { margin: 0 12px 4px; border: none; border-radius: 10px; }
.panel-body { padding: 4px 18px 18px; }
.ncp-wrap { margin: -4px -18px -18px; }

.pt-who { display: flex; align-items: center; gap: 12px; padding: 6px 0 14px; }
.pt-av { width: 46px; height: 46px; border-radius: 50%; object-fit: cover; flex-shrink: 0; display: flex; align-items: center; justify-content: center; background: #e3efe7; color: #004D3A; font-weight: 800; box-shadow: 0 0 0 2px #EFBF04; }
.pt-id { min-width: 0; display: flex; flex-direction: column; }
.pt-id strong { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #0E3A2C; line-height: 1.2; }
.pt-id small { font-size: 0.8rem; color: #4A5A52; }
.allergy { border-radius: 12px; padding: 10px 12px; font-size: 0.85rem; background: #FDECEC; color: #B4384A; }
.note { border-radius: 12px; }
.pt-sec, .block h3 { margin: 18px 0 10px; font-size: 0.72rem; font-weight: 800; color: #6B7D73; }
.block-head h3 { margin: 0; }

/* figures: round icons, no boxes */
.stats { background: none; border: none; box-shadow: none; overflow: visible; gap: 10px 12px; }
.stats .tile { flex-direction: row; gap: 10px; padding: 10px; border-radius: 14px; background: none; }
.stats .tile:hover { background: #fff; }
.stats .tile:nth-child(even), .stats .tile:nth-child(n+3) { border: none; }
.stats .tile.risk { background: #FDF3F2; }
.stats .tile > .pt-fi { width: 38px; height: 38px; flex-shrink: 0; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0; }
.pt-fi.green { background: #DDEFE4; color: #1F7A4D; }
.pt-fi.gold { background: #FBF3D2; color: #9A7300; }
.pt-fi.blue { background: #DFF0FB; color: #1F6FA8; }
.stats .tile > .pt-tx { display: flex; flex-direction: column; align-items: flex-start; min-width: 0; font-size: inherit; font-weight: inherit; color: inherit; }
.stats .pt-tx > span { font-size: 0.75rem; font-weight: 500; color: #6B7D73; }
.stats .pt-tx > strong { font-size: 1.4rem; line-height: 1.15; color: #0E3A2C; }
.stats .pt-tx > small { font-size: 0.72rem; color: #6B7D73; }
.flip-hint { display: flex; align-items: center; gap: 6px; padding: 4px 2px 0; border: none; background: none; font-size: 0.72rem; color: #8A9A91; }
.info { border-radius: 14px; }

/* details: icon rows */
.pt-facts div { padding: 9px 0; border-top-color: #E8EFEB; }
.pt-facts dt { display: inline-flex; align-items: center; gap: 8px; font-size: 0.8rem; color: #6B7D73; }
.pt-facts dt svg { flex-shrink: 0; color: #1F7A4D; }
.pt-facts dd { font-size: 0.82rem; font-weight: 700; }

.block { margin-top: 6px; padding-top: 6px; border-top-color: #E1EAE4; }
.pt-empty { padding: 12px; border-radius: 12px; border: 1.5px dashed #D3DED7; color: #8A9A91; text-align: center; }
.link.small { min-height: 32px; border-radius: 10px; background: #004D3A; font-weight: 800; }
.link.small svg { color: #EFBF04; }
.link.small.soft { background: #E3EFE7; color: #004D3A; }
.link.small.soft svg { color: inherit; }
.chart-link { display: flex; width: 100%; min-height: 42px; margin-top: 18px; border-radius: 12px; font-size: 0.85rem; }

/* client panel: same look */
.client .rnd-card { padding: 6px 0 4px; }
.rnd-photo { box-shadow: 0 0 0 2px #EFBF04; }
.rnd-name { font-size: 1.1rem; color: #0E3A2C; }

@media (max-width: 1100px) { .body.rnd .panel.wide { width: min(640px, 60vw); } }
@media (max-width: 860px) {
  .bar { padding: 10px 14px; }
  .panel, .body.rnd .panel, .body.rnd .panel.wide { width: 100%; border-radius: 22px 22px 0 0; }
}
</style>