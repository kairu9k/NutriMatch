<template>
  <div class="nm-page">
    <p class="crumb"><NuxtLink to="/my-patients">My Patients</NuxtLink> / {{ p?.client.name || 'Patient' }}</p>
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <div v-if="loading" class="nm-panel"><p class="nm-muted">Loading patient…</p></div>

    <template v-else-if="s">
      <!-- BANNER -->
      <section class="nm-banner patient-banner">
        <div class="pb-left">
          <img v-if="p.client.profile_photo" :src="p.client.profile_photo" class="pb-avatar" alt="" />
          <span v-else class="pb-avatar">{{ userInitials(p.client.first_name, p.client.last_name) }}</span>
          <div class="pb-info">
            <h1 class="nm-banner-title">{{ p.client.name }}</h1>
            <p class="nm-banner-sub">{{ metaLine }}</p>
            <div class="pb-chips">
              <span class="pb-chip" :class="p.status">{{ STATUS_LABEL[p.status] }}</span>
              <span v-if="s.health.allergies.length" class="pb-chip allergy">Allergy: {{ s.health.allergies.join(', ') }}</span>
              <span v-if="p.started_at && p.status !== 'pending'" class="pb-chip">Patient since {{ shortDate(p.started_at) }}</span>
            </div>
          </div>
        </div>
        <div class="pb-actions">
          <NuxtLink v-if="p.status === 'active' && p.stage.next_step.key !== 'open'" :to="p.stage.next_step.link" class="nm-btn-gold">{{ p.stage.next_step.label }}</NuxtLink>
          <NuxtLink :to="`/messages?relationship=${relationshipId}`" class="pb-btn">
            <MessageSquare :size="15" /> {{ p.status === 'discharged' ? 'Message history' : 'Message' }}
            <span v-if="p.unread_messages" class="pb-badge">{{ p.unread_messages }}</span>
          </NuxtLink>
          <button v-if="p.status === 'active'" type="button" class="pb-btn" @click="showDischarge = true">Discharge</button>
        </div>
      </section>

      <section v-if="p.status === 'discharged'" class="nm-note">
        <strong>Discharged{{ p.ended_at ? ` on ${shortDate(p.ended_at)}` : '' }}.</strong>
        This record is read-only.<template v-if="p.discharge_reason"> Reason: “{{ p.discharge_reason }}”</template>
        If {{ p.client.first_name }} books you again, it reopens when you confirm the booking.
      </section>
      <section v-else-if="p.status === 'pending'" class="nm-note">
        <strong>New booking.</strong> {{ p.client.first_name }} becomes your patient once you confirm their booking.
        <NuxtLink to="/appointments" class="nm-panel-link">Review booking →</NuxtLink>
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

        <div class="nm-stat-grid">
          <div class="nm-stat-card">
            <div class="nm-stat-icon"><Scale :size="17" /></div>
            <p class="nm-stat-value">{{ p.progress.latest_weight_kg != null ? `${fmt1(p.progress.latest_weight_kg)} kg` : '—' }}</p>
            <p class="nm-stat-label">Current weight</p>
            <p class="nm-stat-note">{{ p.progress.weight_change_kg != null ? `${signed(p.progress.weight_change_kg)} kg since screening` : 'From their screening' }}</p>
          </div>
          <div class="nm-stat-card">
            <div class="nm-stat-icon"><Activity :size="17" /></div>
            <p class="nm-stat-value">{{ p.progress.bmi != null ? fmt1(p.progress.bmi) : '—' }}</p>
            <p class="nm-stat-label">BMI</p>
            <p class="nm-stat-note">{{ p.progress.bmi_class ? `${p.progress.bmi_class} (Asia-Pacific)` : 'No measurement yet' }}</p>
          </div>
          <div class="nm-stat-card">
            <div class="nm-stat-icon gold"><Utensils :size="17" /></div>
            <p class="nm-stat-value">{{ p.adherence?.pct != null ? `${p.adherence.pct}%` : '—' }}</p>
            <p class="nm-stat-label">Meal-plan adherence · 7 days</p>
            <p class="nm-stat-note">{{ p.adherence ? `${p.adherence.logged} of ${p.adherence.planned} meals logged` : 'No active meal plan' }}</p>
          </div>
          <div class="nm-stat-card">
            <div class="nm-stat-icon" :class="{ gold: (s.screening?.nrs_score ?? 0) >= 3 }"><ShieldAlert :size="17" /></div>
            <p class="nm-stat-value">{{ s.screening?.nrs_score ?? '—' }}</p>
            <p class="nm-stat-label">NRS-2002 score</p>
            <p class="nm-stat-note" :class="{ warn: (s.screening?.nrs_score ?? 0) >= 3 }">{{ s.screening ? (s.screening.nrs_risk || 'Not scored') : 'No screening yet' }}</p>
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
                <button v-if="ncpRecords.length" type="button" class="nm-panel-link" @click="setTab('ncp')">NCP records →</button>
              </div>
              <p v-if="!s.care_plan" class="nm-muted">No finalized NCP record yet{{ s.ncp_draft_id ? ' — a draft is in progress' : '' }}.</p>
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
                  <div><strong>{{ Math.round(s.care_plan.target_kcal) }}</strong><span>kcal / day</span></div>
                  <div v-if="s.care_plan.target_carb_g"><strong>{{ Math.round(s.care_plan.target_carb_g) }} g</strong><span>carbs</span></div>
                  <div v-if="s.care_plan.target_protein_g"><strong>{{ Math.round(s.care_plan.target_protein_g) }} g</strong><span>protein</span></div>
                  <div v-if="s.care_plan.target_fat_g"><strong>{{ Math.round(s.care_plan.target_fat_g) }} g</strong><span>fat</span></div>
                </div>
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
                  <div><dt>BMI</dt><dd>{{ s.screening.bmi ? fmt1(s.screening.bmi) : '—' }}<small v-if="s.screening.bmi_category"> · {{ s.screening.bmi_category }}</small></dd></div>
                  <div><dt>Activity</dt><dd>{{ s.screening.activity_level }}</dd></div>
                  <div><dt>BMR (Mifflin-St Jeor)</dt><dd>{{ s.screening.bmr_kcal ? `${Math.round(s.screening.bmr_kcal)} kcal` : '—' }}</dd></div>
                  <div><dt>TDEE</dt><dd>{{ s.screening.tdee_kcal ? `${Math.round(s.screening.tdee_kcal)} kcal` : '—' }}</dd></div>
                  <div><dt>NRS-2002</dt><dd>{{ s.screening.nrs_score ?? '—' }}<small v-if="s.screening.nrs_risk"> · {{ s.screening.nrs_risk }}</small></dd></div>
                </dl>
                <p v-if="s.screening.symptoms" class="symptoms"><span class="k">Symptoms / notes</span>{{ s.screening.symptoms }}</p>
              </template>
            </div>
          </div>

          <div class="nm-col">
            <!-- next appointment -->
            <div class="nm-panel">
              <div class="nm-panel-head">
                <h2 class="nm-panel-title">Next consultation</h2>
                <button type="button" class="nm-panel-link" @click="setTab('appointments')">All →</button>
              </div>
              <template v-if="nextAppt">
                <p class="big-when">{{ longWhen(nextAppt.scheduled_at) }}</p>
                <p class="nm-row-sub">{{ nextAppt.type_label }} · {{ nextAppt.duration_minutes }} min</p>
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
                <div><dt>Religion</dt><dd>{{ s.health.religion || '—' }}</dd></div>
                <div><dt>Goals</dt><dd>{{ list(s.health.health_goals) }}</dd></div>
              </dl>
            </div>

            <!-- latest progress -->
            <div class="nm-panel">
              <div class="nm-panel-head">
                <h2 class="nm-panel-title">Latest progress</h2>
                <button type="button" class="nm-panel-link" @click="setTab('progress')">{{ p.status === 'active' ? 'Record →' : 'All →' }}</button>
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
          </div>
        </div>
      </template>

      <!-- ===================== NCP RECORDS ===================== -->
      <div v-else-if="tab === 'ncp'" class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">NCP records</h2>
            <p class="nm-panel-sub">Assessment → Diagnosis → Intervention, plus Monitoring on follow-ups. Finalized records can't be changed.</p>
          </div>
          <button v-if="p.status === 'active'" class="nm-btn-dark nm-btn-sm" type="button" @click="openNcpForm">
            {{ openDraft ? 'Continue record' : 'New NCP record' }}
          </button>
        </div>
        <div v-if="ncpRecords.length" class="nm-table-wrap">
          <table class="nm-table">
            <thead><tr><th>Created</th><th>Record</th><th>Phase</th><th>Status</th><th class="right">Actions</th></tr></thead>
            <tbody>
              <tr v-for="r in ncpRecords" :key="r.id">
                <td>{{ dateTime(r.created_at) }}</td>
                <td>{{ r.is_follow_up ? 'Follow-up' : 'Initial' }}</td>
                <td>{{ ncpPhaseLabel(r) }}</td>
                <td><span class="nm-pill" :class="r.status === 'completed' ? 'green' : 'gold'">{{ r.status === 'completed' ? 'Finalized' : 'In progress' }}</span></td>
                <td class="right">
                  <NcpRowActions :record="r" :patient-name="p.client.name" :editable="p.status === 'active'"
                                 @view="viewNcpRecord(r)" @edit="openNcpForm" @deleted="refresh" />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-else class="nm-muted">No NCP records yet.{{ p.status === 'active' ? ' Start the first one with "New NCP record".' : '' }}</p>
      </div>

      <!-- ===================== MEAL PLAN ===================== -->
      <template v-else-if="tab === 'meal'">
        <div class="nm-panel">
          <div class="nm-panel-head">
            <div>
              <h2 class="nm-panel-title">{{ s.meal_plan ? s.meal_plan.name : 'Meal plan' }}</h2>
              <p class="nm-panel-sub" v-if="s.meal_plan">
                {{ s.meal_plan.status === 'active' ? `Sent ${shortDate(s.meal_plan.sent_at)}` : 'Draft — not sent to the patient yet' }}
                · {{ s.meal_plan.meals_per_week }} meals a week
              </p>
            </div>
            <template v-if="p.status === 'active'">
              <NuxtLink v-if="mealPlanReady" :to="`/meal-planning?relationship=${relationshipId}&edit=1`" class="nm-btn-dark nm-btn-sm">
                {{ s.meal_plan ? (s.meal_plan.status === 'draft' ? 'Finish & send plan' : 'Update meal plan') : 'Create meal plan' }}
              </NuxtLink>
            </template>
          </div>
          <p v-if="p.status === 'active' && !mealPlanReady && !s.meal_plan" class="nm-note" style="margin: 0">Finish the NCP Intervention (diet prescription and target calories) before creating a meal plan.</p>
          <div v-if="s.meal_plan?.target_kcal" class="targets">
            <div><strong>{{ Math.round(s.meal_plan.target_kcal) }}</strong><span>kcal / day</span></div>
            <div v-if="s.meal_plan.target_carb_g"><strong>{{ Math.round(s.meal_plan.target_carb_g) }} g</strong><span>carbs</span></div>
            <div v-if="s.meal_plan.target_protein_g"><strong>{{ Math.round(s.meal_plan.target_protein_g) }} g</strong><span>protein</span></div>
            <div v-if="s.meal_plan.target_fat_g"><strong>{{ Math.round(s.meal_plan.target_fat_g) }} g</strong><span>fat</span></div>
          </div>
          <p v-else-if="!s.meal_plan && mealPlanReady" class="nm-muted">No meal plan yet.</p>
        </div>

        <div class="nm-panel">
          <div class="nm-panel-head">
            <div>
              <h2 class="nm-panel-title">Adherence, last 14 days</h2>
              <p class="nm-panel-sub">Share of planned meals followed each day (partly followed counts half; unlogged counts as missed).</p>
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
                    <span v-if="d.followed_pct == null">No meals planned</span>
                    <template v-else><span>{{ d.followed_pct }}% followed</span><span class="tip-muted">{{ d.logged }} of {{ d.planned }} meals logged</span></template>
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
          <p class="nm-panel-sub">What {{ p.client.first_name }} reported against the plan.</p>
          <div v-if="s.recent_logs.length" class="nm-table-wrap" style="margin-top: 10px">
            <table class="nm-table">
              <thead><tr><th>Date</th><th>Meal</th><th>Status</th><th>Logged at</th><th>Their note</th></tr></thead>
              <tbody>
                <tr v-for="(l, i) in s.recent_logs" :key="i">
                  <td>{{ shortDate(l.date) }}</td>
                  <td>{{ l.meal }}</td>
                  <td><span class="nm-pill" :class="LOG_PILL[l.status]">{{ LOG_LABEL[l.status] }}</span></td>
                  <td>{{ l.time_logged ? clockOf(l.time_logged) : '—' }}</td>
                  <td class="note-cell">{{ l.note || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else class="nm-muted" style="margin-top: 10px">No meals logged yet.</p>
        </div>
      </template>

      <!-- ===================== PROGRESS ===================== -->
      <template v-else-if="tab === 'progress'">
        <div v-if="p.status === 'active'" class="nm-panel">
          <div class="nm-panel-head">
            <div>
              <h2 class="nm-panel-title">Record progress</h2>
              <p class="nm-panel-sub">Measured or checked during a consultation. BMI is worked out from their screening height.</p>
            </div>
            <button v-if="!formOpen" type="button" class="nm-btn-dark nm-btn-sm" @click="openForm"><Plus :size="14" /> Record progress</button>
          </div>
          <form v-if="formOpen" class="progress-form" @submit.prevent="saveProgress">
            <div class="pf-grid">
              <label><span class="nm-label">Date</span><input v-model="form.record_date" type="date" class="nm-input" :max="todayIso" required /></label>
              <label><span class="nm-label">Weight (kg)</span><input v-model="form.weight_kg" type="number" step="0.1" min="25" max="300" class="nm-input" placeholder="e.g. 68.5" /></label>
              <label><span class="nm-label">Blood pressure</span><input v-model="form.blood_pressure" type="text" inputmode="numeric" class="nm-input" placeholder="120/80" /></label>
              <label><span class="nm-label">Fasting glucose (mg/dL)</span><input v-model="form.blood_glucose" type="number" step="1" min="20" max="600" class="nm-input" placeholder="e.g. 110" /></label>
              <label><span class="nm-label">HbA1c (%)</span><input v-model="form.hba1c" type="number" step="0.1" min="3" max="20" class="nm-input" placeholder="e.g. 6.5" /></label>
            </div>
            <label class="pf-note">
              <span class="nm-label"><Lock :size="12" /> Private note <span class="nm-muted">(only you see this)</span></span>
              <textarea v-model="form.rnd_notes" class="nm-input" rows="2" maxlength="2000" placeholder="Observations for your own record"></textarea>
            </label>
            <p v-if="formError" class="nm-field-error">{{ formError }}</p>
            <div class="nm-modal-actions">
              <button type="button" class="nm-btn-outline" @click="formOpen = false">Cancel</button>
              <button type="submit" class="nm-btn-dark" :disabled="saving">{{ saving ? 'Saving…' : 'Save record' }}</button>
            </div>
          </form>
          <p v-if="savedNote" class="saved">
            <CheckCircle2 :size="15" /> Saved. {{ p.client.first_name }} can see the new numbers on their Progress page.
            <NuxtLink :to="`/messages?relationship=${relationshipId}`" class="nm-panel-link">Message {{ p.client.first_name }} →</NuxtLink>
          </p>
        </div>

        <div class="nm-panel">
          <div class="nm-panel-head">
            <div>
              <h2 class="nm-panel-title">Trends</h2>
              <p class="nm-panel-sub">From the screening, progress records and finalized NCP records.</p>
            </div>
            <div v-if="trend && trend.change != null" class="chart-figure">
              <span class="cf-value">{{ trend.change > 0 ? '+' : trend.change < 0 ? '−' : '' }}{{ Math.abs(trend.change).toFixed(trend.decimals) }} {{ trend.unit }}</span>
              <span class="cf-sub">{{ trend.changeLabel }}</span>
            </div>
          </div>
          <div class="nm-tabs metric-tabs" role="tablist" aria-label="Measurement">
            <button v-for="mt in METRICS" :key="mt.key" type="button" role="tab" class="nm-tab" :class="{ active: metric === mt.key }"
                    :aria-selected="metric === mt.key" :disabled="!metricSeries[mt.key].some(x => x.points.length)" @click="metric = mt.key">
              {{ mt.label }}
            </button>
          </div>
          <p v-if="!trend" class="nm-muted">The trend shows once there are two readings of {{ METRICS.find(x => x.key === metric).label.toLowerCase() }}.</p>
          <TrendChart v-else :series="trend.series" :unit="trend.unit" :decimals="trend.decimals" :ref-lines="trend.refLines" :title="trend.title" />
        </div>

        <div class="nm-panel">
          <h2 class="nm-panel-title">All progress records</h2>
          <div v-if="s.progress.length" class="nm-table-wrap" style="margin-top: 10px">
            <table class="nm-table">
              <thead><tr><th>Date</th><th>Weight</th><th>BMI</th><th>BP</th><th>Glucose</th><th>HbA1c</th><th>Private note</th></tr></thead>
              <tbody>
                <tr v-for="r in s.progress" :key="r.id">
                  <td class="nowrap">{{ shortDate(r.record_date) }}</td>
                  <td class="nowrap">{{ r.weight_kg != null ? `${fmt1(r.weight_kg)} kg` : '—' }}</td>
                  <td>{{ r.bmi != null ? fmt1(r.bmi) : '—' }}</td>
                  <td>{{ r.blood_pressure || '—' }}</td>
                  <td>{{ r.blood_glucose != null ? `${r.blood_glucose} mg/dL` : '—' }}</td>
                  <td>{{ r.hba1c != null ? `${r.hba1c}%` : '—' }}</td>
                  <td class="note-cell">{{ r.rnd_notes || '—' }}</td>
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
            <p class="nm-panel-sub">{{ p.consultations }} completed</p>
          </div>
          <NuxtLink to="/appointments" class="nm-panel-link">Appointments →</NuxtLink>
        </div>
        <p v-if="!s.appointments.length" class="nm-muted">No consultations yet.</p>
        <div v-for="a in s.appointments" :key="a.id" class="appt-row" :class="{ past: !a.upcoming }">
          <div class="appt-date">
            <span class="ad-day">{{ dayNum(a.scheduled_at) }}</span>
            <span class="ad-mon">{{ monthShort(a.scheduled_at) }}</span>
          </div>
          <div class="appt-main">
            <p class="nm-row-title">{{ longWhen(a.scheduled_at) }}</p>
            <p class="nm-row-sub">{{ a.type_label }} · {{ a.duration_minutes }} min{{ a.amount ? ` · ${peso(a.amount)}` : '' }}</p>
            <p v-if="a.status === 'cancelled' && a.cancellation_reason" class="nm-row-sub">Cancelled: {{ a.cancellation_reason }}</p>
          </div>
          <div class="appt-end">
            <span class="nm-pill" :class="APPT_PILL[a.status]">{{ APPT_LABEL[a.status] }}</span>
            <span v-if="a.payment && a.status !== 'cancelled'" class="nm-pill" :class="a.payment === 'paid' ? 'green' : a.payment === 'unpaid' ? 'muted' : 'red'">{{ PAY_LABEL[a.payment] || a.payment }}</span>
            <NuxtLink v-if="canJoin(a)" :to="`/consultation-room/${a.id}`" class="nm-btn-dark nm-btn-sm"><Video :size="13" /> Join</NuxtLink>
            <button v-if="a.status === 'completed'" type="button" class="nm-btn-outline nm-btn-sm" @click="summaryId = a.id"><FileText :size="13" /> Summary</button>
          </div>
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
      :can-continue="p?.status === 'active'"
      @close="ncpModal = null"
      @changed="refresh"
      @continue="ncpModal = { mode: 'edit', recordId: null }"
    />
    <DischargeModal
      v-if="showDischarge" :relationship-id="relationshipId" :patient-name="p?.client.name"
      @close="showDischarge = false" @discharged="onDischarged"
    />
    <ConsultationSummaryModal v-if="summaryId" :appointment-id="summaryId" role="rnd" @close="summaryId = null" />
  </div>
</template>

<script setup>
import {
  Activity, AlertTriangle, Check, CheckCircle2, FileText, Info, Lock, MessageSquare, OctagonAlert, Plus, Scale, ShieldAlert, Utensils, Video,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { get, post } = useApi()
const now = useNow()
const relationshipId = route.params.relationshipId

const s = ref(null)
const ncpRecords = ref([])
const loading = ref(true)
const error = ref('')
const hover = ref(null)
const p = computed(() => s.value?.patient)

async function load() {
  error.value = ''
  try {
    const [summary, ncp] = await Promise.all([
      get(`/rnd/relationships/${relationshipId}/summary/`),
      get(`/rnd/relationships/${relationshipId}/ncp/`).catch(() => []),
    ])
    s.value = summary
    ncpRecords.value = ncp
  } catch {
    error.value = 'Could not load this patient.'
  } finally {
    loading.value = false
  }
}
const refresh = load
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
const TAB_KEYS = ['overview', 'ncp', 'meal', 'progress', 'appointments', 'reminders']
const tab = ref(TAB_KEYS.includes(route.query.tab) ? route.query.tab : 'overview')
function setTab(k) {
  tab.value = k
  router.replace({ query: { ...route.query, tab: k === 'overview' ? undefined : k } })
}
const TABS = computed(() => [
  { key: 'overview', label: 'Overview' },
  { key: 'ncp', label: 'NCP Records', count: ncpRecords.value.length || null },
  { key: 'meal', label: 'Meal Plan' },
  { key: 'progress', label: 'Progress', count: s.value?.progress.length || null },
  { key: 'appointments', label: 'Consultations', count: s.value?.appointments.length || null },
  { key: 'reminders', label: 'Tasks & reminders' },
])

/* ---------- labels ---------- */
const STATUS_LABEL = { active: 'Active patient', pending: 'New booking', discharged: 'Discharged' }
const ALERT_ICONS = { critical: OctagonAlert, warning: AlertTriangle, info: Info }
const APPT_LABEL = { pending: 'To confirm', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }
const APPT_PILL = { pending: 'gold', confirmed: 'blue', completed: 'green', cancelled: 'muted' }
const PAY_LABEL = { paid: 'Paid', unpaid: 'Not paid yet', refund_pending: 'Refund pending', refunded: 'Refunded', cancelled: 'Voided' }
const LOG_LABEL = { followed: 'Followed', partially_followed: 'Partly followed', not_followed: 'Not followed' }
const LOG_PILL = { followed: 'green', partially_followed: 'gold', not_followed: 'red' }
const SEX = { male: 'Male', female: 'Female' }

const metaLine = computed(() => {
  const c = p.value.client
  return [c.age != null ? `${c.age} y/o` : null, SEX[c.sex], s.value.health.conditions.join(', ') || null].filter(Boolean).join(' · ')
})
const list = arr => (arr && arr.length ? arr.join(', ') : '—')
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
const mealPlanReady = computed(() => ncpRecords.value.some(r => r.diet_prescription || r.target_kcal))

/* ---------- appointments ---------- */
const nextAppt = computed(() => [...(s.value?.appointments || [])].filter(a => a.upcoming).sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))[0] || null)
function canJoin(a) {
  return a.status === 'confirmed' && ['video', 'chat'].includes(a.type) && now.value >= new Date(a.join_opens_at) && now.value <= new Date(a.join_closes_at)
}
const PH = { timeZone: 'Asia/Manila' }
const longWhen = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
const dayNum = v => new Date(v).toLocaleDateString('en-PH', { ...PH, day: 'numeric' })
const monthShort = v => new Date(v).toLocaleDateString('en-PH', { ...PH, month: 'short' }).toUpperCase()
const dayName = iso => new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { weekday: 'short', month: 'short', day: 'numeric' })
const shortDay = (iso, today) => (today ? 'Today' : new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { month: 'short', day: 'numeric' }))
function clockOf(t) {
  const [h, m] = t.split(':').map(Number)
  return `${((h + 11) % 12) + 1}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}

/* ---------- NCP (shared NcpRecordModal) ---------- */
const ncpModal = ref(null)
const openDraft = computed(() => ncpRecords.value.find(r => r.status === 'draft') || null)
function openNcpForm() { ncpModal.value = { mode: 'edit', recordId: null } }
function viewNcpRecord(r) { ncpModal.value = { mode: 'view', recordId: r.id } }
function ncpPhaseLabel(r) {
  if (r.status === 'completed') return r.is_follow_up ? 'Monitoring' : 'Intervention'
  if (!(r.weight_kg && r.height_cm)) return 'Assessment'
  if (!r.pes_problem) return 'Diagnosis'
  if (!r.diet_prescription) return 'Intervention'
  return r.is_follow_up ? 'Monitoring' : 'Intervention'
}

/* ---------- discharge ---------- */
const summaryId = ref(null) // consultation summary pop-up
const showDischarge = ref(false)
function onDischarged() {
  showDischarge.value = false
  load()
}

/* ---------- record progress ---------- */
const todayIso = new Date().toLocaleDateString('en-CA', PH)
const formOpen = ref(false)
const saving = ref(false)
const formError = ref('')
const savedNote = ref(false)
const blank = () => ({ record_date: todayIso, weight_kg: '', blood_pressure: '', blood_glucose: '', hba1c: '', rnd_notes: '' })
const form = ref(blank())
function openForm() {
  form.value = blank()
  formError.value = ''
  savedNote.value = false
  formOpen.value = true
}
async function saveProgress() {
  formError.value = ''
  const f = form.value
  const body = { relationship: Number(relationshipId), record_date: f.record_date }
  for (const k of ['weight_kg', 'blood_pressure', 'blood_glucose', 'hba1c', 'rnd_notes']) {
    const v = String(f[k] ?? '').trim()
    if (v) body[k] = v
  }
  if (!['weight_kg', 'blood_pressure', 'blood_glucose', 'hba1c'].some(k => body[k])) {
    formError.value = 'Enter at least one measurement.'
    return
  }
  saving.value = true
  try {
    await post(`/rnd/relationships/${relationshipId}/progress/`, body)
    formOpen.value = false
    savedNote.value = true
    await load()
  } catch (e) {
    formError.value = apiError(e, 'Could not save this record.')
  } finally {
    saving.value = false
  }
}

/* ---------- trends: one chart, switch the measurement ---------- */
// Points come from the screening (weight/BMI), progress records and finalized
// NCP records (their assessment + lipid "other measurements"). One point per
// date per line — a progress record wins over an NCP record on the same day.
const METRICS = [
  { key: 'weight', label: 'Weight', unit: 'kg', decimals: 1 },
  { key: 'bmi', label: 'BMI', unit: '', decimals: 1, refLines: [{ value: 23, label: 'Normal < 23' }] },
  { key: 'bp', label: 'Blood pressure', unit: 'mmHg', decimals: 0, refLines: [{ value: 130, label: '130' }] },
  { key: 'glucose', label: 'Glucose', unit: 'mg/dL', decimals: 0, refLines: [{ value: 100, label: 'Fasting 100' }] },
  { key: 'hba1c', label: 'HbA1c', unit: '%', decimals: 1, refLines: [{ value: 6.5, label: '6.5%' }] },
  { key: 'lipids', label: 'Lipids', unit: 'mg/dL', decimals: 0 },
]
const LIPIDS = [['total', 'Total cholesterol', /total cholesterol|^cholesterol/i], ['ldl', 'LDL', /\bldl\b/i], ['hdl', 'HDL', /\bhdl\b/i], ['tg', 'Triglycerides', /triglyceride/i]]
const metric = ref('weight')
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
const trend = computed(() => {
  const def = METRICS.find(m => m.key === metric.value)
  const series = metricSeries.value[metric.value].filter(l => l.points.length)
  if (!series.length || !series.some(l => l.points.length >= 2)) return null
  const main = series[0].points
  const change = main.length >= 2 ? main[main.length - 1].value - main[0].value : null
  return {
    series, unit: def.unit, decimals: def.decimals, refLines: def.refLines || [], title: `${def.label} trend`,
    change, changeLabel: `${series.length > 1 ? `${series[0].label.toLowerCase()} ` : ''}since ${shortDate(main[0].date)}`,
  }
})
// open on the first measurement that has a trend
watch(metricSeries, (ms) => {
  if (!ms[metric.value].some(l => l.points.length >= 2)) {
    const first = METRICS.find(m => ms[m.key].some(l => l.points.length >= 2))
    if (first) metric.value = first.key
  }
}, { immediate: true })
</script>

<style scoped>
.crumb { font-size: 0.8rem; color: #8a9a8a; margin: 0 0 12px; }
.crumb a { color: #1f6f46; text-decoration: none; font-weight: 600; }

.patient-banner { display: flex; justify-content: space-between; align-items: center; gap: 18px; flex-wrap: wrap; }
.pb-left { display: flex; gap: 16px; align-items: center; min-width: 0; }
.pb-avatar { width: 64px; height: 64px; border-radius: 50%; background: #D4A017; color: #1a3a1a; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.25rem; flex-shrink: 0; object-fit: cover; }
.pb-info { min-width: 0; }
.pb-info .nm-banner-title { margin-bottom: 2px; }
.pb-info .nm-banner-sub { margin: 0 0 8px; }
.pb-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.pb-chip { font-size: 0.72rem; font-weight: 600; padding: 3px 10px; border-radius: 12px; background: rgba(255, 255, 255, 0.14); color: #fff; }
.pb-chip.active { background: #d8f0e0; color: #1f6f46; }
.pb-chip.pending { background: #fdf1d6; color: #8a6a1a; }
.pb-chip.discharged { background: #eceeec; color: #5a6a5a; }
.pb-chip.allergy { background: #fdf1d6; color: #8a5a00; }
.pb-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.pb-btn { position: relative; display: inline-flex; align-items: center; gap: 6px; background: transparent; color: #fff; border: 1px solid rgba(255, 255, 255, 0.45); border-radius: 8px; padding: 8px 14px; font-weight: 600; font-size: 0.84rem; cursor: pointer; text-decoration: none; font-family: inherit; }
.pb-btn:hover { background: rgba(255, 255, 255, 0.1); }
.pb-badge { min-width: 18px; height: 18px; padding: 0 5px; border-radius: 9px; background: #D4A017; color: #1a3a1a; font-size: 0.68rem; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; }

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
.k { display: block; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; margin: 0 0 3px; }
.targets { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 14px; }
.targets div { background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 10px; display: flex; flex-direction: column; }
.targets strong { font-size: 1rem; color: #1a3a1a; font-variant-numeric: tabular-nums; }
.targets span { font-size: 0.72rem; color: #8a9a8a; }

.facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 16px; margin: 12px 0 0; }
.facts.one { grid-template-columns: minmax(0, 1fr); gap: 0; }
.facts.one div { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-top: 1px solid #f0f2f0; }
.facts.one div:first-child { border-top: none; }
.facts dt { font-size: 0.74rem; color: #8a9a8a; margin: 0; }
.facts dd { margin: 0; font-size: 0.86rem; font-weight: 600; color: #1a3a1a; overflow-wrap: anywhere; }
.facts.one dd { text-align: right; }
.facts dd small { font-weight: 500; color: #6a7a6a; }
.facts dd.warn { color: #8a5a00; }
.symptoms { margin: 12px 0 0; font-size: 0.84rem; color: #3a4a3a; line-height: 1.5; }
.big-when { font-size: 0.96rem; font-weight: 700; color: #1a3a1a; margin: 6px 0 2px; }
.pills { margin: 8px 0 10px; }
.private-note { display: flex; gap: 6px; align-items: baseline; margin: 10px 0 0; font-size: 0.8rem; color: #5a6a5a; background: #fafbfa; border-radius: 8px; padding: 8px 10px; }
.note-cell { max-width: 260px; color: #5a6a5a; overflow-wrap: anywhere; }

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
.chart-figure { text-align: right; flex-shrink: 0; margin-left: auto; }
.cf-value { display: block; font-size: 1.4rem; font-weight: 700; color: #1a3a1a; line-height: 1.1; font-variant-numeric: tabular-nums; }
.cf-sub { font-size: 0.74rem; color: #8a9a8a; }
.nm-panel-head > div:first-child { flex: 1 1 240px; min-width: 0; }
.metric-tabs { margin: 0 0 14px; }
.metric-tabs .nm-tab:disabled { opacity: 0.4; cursor: not-allowed; }

/* progress form */
.progress-form { margin-top: 4px; }
.pf-grid { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; }
.pf-note { display: block; margin-top: 12px; }
.pf-note .nm-label { display: flex; align-items: center; gap: 5px; }
.saved { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 10px 0 0; font-size: 0.84rem; color: #1f6f46; font-weight: 600; }

/* consultations */
.appt-row { display: flex; gap: 14px; align-items: center; padding: 12px 0; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.appt-row:first-of-type { border-top: none; }
.appt-row.past { opacity: 0.85; }
.appt-date { width: 48px; height: 52px; border-radius: 10px; background: #eef3ec; display: flex; flex-direction: column; align-items: center; justify-content: center; flex-shrink: 0; }
.appt-row.past .appt-date { background: #f4f5f4; }
.ad-day { font-size: 1.1rem; font-weight: 700; color: #1a3a1a; line-height: 1; }
.ad-mon { font-size: 0.62rem; font-weight: 700; color: #6a7a6a; letter-spacing: 0.06em; }
.appt-main { flex: 1; min-width: 180px; }
.appt-end { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }

@media (max-width: 900px) {
  .pf-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .pf-grid label:first-child { grid-column: 1 / -1; }
}
@media (max-width: 640px) {
  .stepper { grid-template-columns: repeat(2, minmax(0, 1fr)); row-gap: 14px; }
  .stepper li:nth-child(2)::before { display: none; }
  .targets { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .facts { grid-template-columns: minmax(0, 1fr); }
  .pb-actions { width: 100%; }
  .chart-figure { text-align: left; margin-left: 0; }
  .mc-bar { width: 10px; }
  .mc-x span { font-size: 0.6rem; }
}
.nowrap { white-space: nowrap; }
</style>
