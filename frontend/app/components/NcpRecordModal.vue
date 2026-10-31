<template>
  <div :class="inline ? 'ncp-inline' : 'nm-modal-overlay ncp-overlay'" @click.self="!inline && requestClose()">
    <div class="ncp" :class="{ 'is-inline': inline }" role="dialog" :aria-modal="!inline" aria-labelledby="ncp-title">
      <!-- HEADER -->
      <header class="ncp-head">
        <div class="ncp-title-wrap">
          <h2 id="ncp-title" class="ncp-title">Nutrition Care Process</h2>
          <p class="ncp-sub">{{ patientName }}, <strong class="ncp-kind" :class="{ follow: isFollowUp }">{{ isFollowUp ? 'follow-up record' : 'initial record' }}</strong>, {{ subtitle }}</p>
        </div>
        <div class="ncp-head-right">
          <span v-if="!isReadOnly" class="save-state" :class="saveStateClass">{{ saveStateText }}</span>
          <button v-if="!inline" type="button" class="icon-x" aria-label="Close" @click="requestClose"><X :size="18" /></button>
        </div>
      </header>

      <p v-if="isLoading" class="nm-muted pad">Loading…</p>
      <p v-else-if="loadError" class="nm-error pad">{{ loadError }}</p>

      <template v-else>
        <!-- STEPS -->
        <nav class="steps" aria-label="NCP steps">
          <button v-for="(st, i) in steps" :key="st" type="button" class="step" :class="[stepState(i), { active: tab === i, err: stepHasError(i) }]" @click="tab = i">
            <span class="step-dot"><Check v-if="stepState(i) === 'done'" :size="12" /><template v-else>{{ i + 1 }}</template></span>
            <span class="step-name">{{ st }}</span>
          </button>
        </nav>

        <div class="ncp-body">
          <div class="ncp-form">
            <p v-if="isFinalized" class="banner lock"><Lock :size="15" /> Finalized {{ dateTime(record.updated_at) }}. Part of the patient's permanent record.</p>
            <p v-else-if="isReadOnly" class="banner"><Lock :size="15" /> Viewing an unfinished record. It's read-only here.</p>
            <p v-if="saveError" class="nm-error">{{ saveError }}</p>

            <button v-if="!inline" type="button" class="strip-toggle" @click="stripOpen = !stripOpen">
              <Info :size="14" /> {{ stripOpen ? 'Hide' : 'Show' }} patient info
            </button>

            <!-- ASSESSMENT -->
            <section v-if="stepKey === 'assessment'">
              <header class="step-head"><h3 class="step-title">Nutrition assessment</h3><p class="step-desc">Where the patient is today: measurements, labs and how they eat.</p></header>
              <p v-if="prefilled && !isReadOnly" class="hint-box"><Info :size="14" /> Measurements are filled in from their latest records. Check them with the patient and update what changed.</p>
              <div class="grid g3">
                <Field label="Height (cm)" required :hint="srcHint('height_cm')" :error="errors.height_cm">
                  <input v-model="a.height_cm" type="number" :min="L.height_cm.min" :max="L.height_cm.max" step="0.1" class="nm-input" :disabled="isReadOnly" />
                </Field>
                <Field label="Weight (kg)" required :hint="srcHint('weight_kg')" :error="errors.weight_kg">
                  <input v-model="a.weight_kg" type="number" :min="L.weight_kg.min" :max="L.weight_kg.max" step="0.1" class="nm-input" :disabled="isReadOnly" />
                </Field>
                <div class="computed">
                  <span class="k">BMI, WHO Asia-Pacific</span>
                  <strong>{{ liveBmi ?? '—' }}</strong>
                  <span class="c-sub">{{ liveBmi ? bmiClass(liveBmi) : (errors.weight_kg || errors.height_cm) ? 'Check height and weight' : 'Enter height and weight' }}</span>
                </div>
              </div>
              <div class="grid g3">
                <Field label="Blood pressure (mmHg)" group :hint="srcHint('blood_pressure')" :error="errors.blood_pressure">
                  <div class="bp">
                    <input v-model="a.bp_systolic" type="number" :min="L.bp_systolic.min" :max="L.bp_systolic.max" class="nm-input" placeholder="120" aria-label="Systolic" :disabled="isReadOnly" />
                    <span>/</span>
                    <input v-model="a.bp_diastolic" type="number" :min="L.bp_diastolic.min" :max="L.bp_diastolic.max" class="nm-input" placeholder="80" aria-label="Diastolic" :disabled="isReadOnly" />
                  </div>
                  <p v-if="liveBp" class="m-cat" :class="liveBp.level" role="status" title="WHO / ESH grading">
                    <AlertTriangle v-if="liveBp.level !== 'ok'" :size="13" /> {{ liveBp.label }}
                  </p>
                </Field>
                <Field label="Fasting glucose (mg/dL)" info="Blood sugar after at least 8 hours without food." :hint="srcHint('blood_glucose')" :error="errors.blood_glucose">
                  <input v-model="a.blood_glucose" type="number" :min="L.blood_glucose.min" :max="L.blood_glucose.max" step="1" class="nm-input" :disabled="isReadOnly" />
                  <p v-if="liveGlucose" class="m-cat" :class="liveGlucose.level" role="status">
                    <AlertTriangle v-if="liveGlucose.level !== 'ok'" :size="13" /> {{ liveGlucose.label }}
                  </p>
                </Field>
                <Field label="HbA1c (%)" :info="'Average blood sugar over the past 2⁠–⁠3 months.' /* word joiners keep 2–3 on one line */" :hint="srcHint('hba1c')" :error="errors.hba1c">
                  <input v-model="a.hba1c" type="number" :min="L.hba1c.min" :max="L.hba1c.max" step="0.1" class="nm-input" :disabled="isReadOnly" />
                  <p v-if="liveHba1c" class="m-cat" :class="liveHba1c.level" role="status">
                    <AlertTriangle v-if="liveHba1c.level !== 'ok'" :size="13" /> {{ liveHba1c.label }}
                  </p>
                </Field>
              </div>
              <NcpExtraRows :rows="a.extra" :templates="MEASURE_TEMPLATES.assessment" :read-only="isReadOnly" empty="Add waist circumference, cholesterol, creatinine and more. Pick from the list or type your own." />
              <Field label="Lab notes">
                <textarea v-model="a.lab_notes" data-allow-emoji class="nm-input" :maxlength="TMAX.lab_notes" rows="2" placeholder="e.g. Lipid profile from Oct 2: LDL 160 mg/dL" :disabled="isReadOnly"></textarea>
                <p v-if="ctx.labs?.total_results && !isReadOnly" class="lab-link">
                  <FlaskConical :size="13" /> {{ ctx.labs.total_results }} lab result{{ ctx.labs.total_results === 1 ? '' : 's' }} uploaded<template v-if="ctx.labs.new_results"> ({{ ctx.labs.new_results }} new)</template>.
                  <NuxtLink :to="`/client-detail/${relationshipId}?tab=labs`" target="_blank">View them in a new tab</NuxtLink>
                </p>
              </Field>
              <Field label="Assessment notes">
                <textarea v-model="a.assessment_notes" data-allow-emoji class="nm-input" :maxlength="TMAX.assessment_notes" rows="3" placeholder="Appetite, eating pattern, activity, food access…" :disabled="isReadOnly"></textarea>
              </Field>
            </section>

            <!-- DIAGNOSIS -->
            <section v-else-if="stepKey === 'diagnosis'">
              <header class="step-head"><h3 class="step-title">Nutrition diagnosis</h3><p class="step-desc">Name the nutrition problem as a PES statement: the problem, its cause and the signs that show it.</p></header>
              <p v-if="carried && !isReadOnly" class="hint-box"><Info :size="14" /> Carried over from the {{ shortDate(ctx.previous.encounter_date) }} record. Edit what changed.</p>
              <Field label="Problem (P)" required group hint="Pick a standard nutrition diagnosis, or type your own.">
                <div class="combo" @keydown.down.prevent="move(1)" @keydown.up.prevent="move(-1)" @keydown.enter="pickActive" @keydown.esc="pesOpen = false">
                  <input v-model="d.pes_problem" type="text" class="nm-input" :maxlength="TMAX.pes_problem" :disabled="isReadOnly" placeholder="Search, e.g. carbohydrate" aria-label="PES problem"
                         role="combobox" :aria-expanded="pesOpen" aria-controls="pes-list" autocomplete="off"
                         @focus="pesOpen = true" @input="pesOpen = true; activeIdx = -1" @blur="closeSoon" />
                  <div v-if="pesOpen && !isReadOnly && pesMatches.length" id="pes-list" class="combo-list" role="listbox">
                    <template v-for="g in pesMatches" :key="g.group">
                      <p class="combo-group">{{ g.group }}</p>
                      <button v-for="t in g.terms" :key="t" type="button" role="option" class="combo-opt"
                              :class="{ on: flatMatches[activeIdx] === t }" :aria-selected="flatMatches[activeIdx] === t" @mousedown.prevent="pick(t)">{{ t }}</button>
                    </template>
                  </div>
                </div>
              </Field>
              <Field label="Etiology: related to (E)" required group hint="Pick a cause from the Etiology Matrix (Academy of Nutrition and Dietetics, 2020), or type your own. Add the patient's details after it.">
                <div class="combo" @keydown.down="etMove($event, 1)" @keydown.up="etMove($event, -1)" @keydown.enter="etPickActive" @keydown.esc="etOpen = false">
                  <textarea v-model="d.pes_etiology" class="nm-input" :maxlength="TMAX.pes_etiology" rows="2" placeholder="Search, e.g. knowledge, or type the cause" :disabled="isReadOnly" aria-label="PES etiology"
                            role="combobox" :aria-expanded="etOpen" aria-controls="et-list" autocomplete="off"
                            @focus="etOpen = true" @input="etOpen = true; etIdx = -1" @blur="etCloseSoon"></textarea>
                  <div v-if="etOpen && !isReadOnly && etGroups.length" id="et-list" class="combo-list" role="listbox">
                    <template v-for="g in etGroups" :key="g.key">
                      <p class="combo-group" :class="{ linked: g.linked }">{{ g.label }}</p>
                      <button v-for="e in g.items" :key="e.id" type="button" role="option" class="combo-opt"
                              :class="{ on: etFlat[etIdx]?.id === e.id }" :aria-selected="etFlat[etIdx]?.id === e.id" @mousedown.prevent="etPick(e.t)">
                        {{ e.t }}<span v-if="g.linked" class="combo-tag">{{ e.c }}</span>
                      </button>
                    </template>
                  </div>
                </div>
              </Field>
              <Field label="Signs and symptoms: as evidenced by (S)" required group hint="Pick signs from the Assessment Terminology (Academy of Nutrition and Dietetics, 2020), or type your own. Add the patient's value after each; separate signs with ;">
                <div class="combo" @keydown.down="sgMove($event, 1)" @keydown.up="sgMove($event, -1)" @keydown.enter="sgPickActive" @keydown.esc="sgOpen = false">
                  <textarea ref="signsBox" v-model="d.pes_signs" class="nm-input" :maxlength="TMAX.pes_signs" rows="3" placeholder="Search, e.g. edema, HbA1c, weight loss, or type the signs" :disabled="isReadOnly" aria-label="PES signs and symptoms"
                            role="combobox" :aria-expanded="sgOpen" aria-controls="sg-list" autocomplete="off"
                            @focus="sgOpen = true; sgTrackCaret()" @input="sgOpen = true; sgIdx = -1; sgTrackCaret()" @click="sgOpen = true; sgTrackCaret()"
                            @keyup.left.right.home.end="sgTrackCaret" @select="sgTrackCaret" @blur="sgCloseSoon"></textarea>
                  <div v-if="sgOpen && !isReadOnly && sgGroups.length" id="sg-list" class="combo-list" role="listbox">
                    <template v-for="g in sgGroups" :key="g.key">
                      <p class="combo-group">{{ g.label }}</p>
                      <button v-for="s in g.items" :key="s.c + s.t" type="button" role="option" class="combo-opt"
                              :class="{ on: sgFlat[sgIdx] === s }" :aria-selected="sgFlat[sgIdx] === s" @mousedown.prevent="sgPick(s.t)">{{ s.t }}</button>
                    </template>
                  </div>
                </div>
              </Field>
              <div class="pes-preview">
                <span class="k">PES statement</span>
                <p>{{ pesSentence }}</p>
              </div>
            </section>

            <!-- INTERVENTION -->
            <section v-else-if="stepKey === 'intervention'">
              <header class="step-head"><h3 class="step-title">Nutrition intervention</h3><p class="step-desc">What you prescribe: the energy and macro targets, and the diet itself.</p></header>
              <p v-if="carried && !isReadOnly" class="hint-box"><Info :size="14" /> Targets carried over from the {{ shortDate(ctx.previous.encounter_date) }} record. Adjust them as needed.</p>
              <!-- TER, Tannhauser's factorial method (utils/ncp.js terSteps) -->
              <div class="ter-box">
                <div class="ter-head">
                  <p class="ter-title">Total Energy Requirement, Tannhauser's method</p>
                  <label class="ter-act">
                    <span>Activity</span>
                    <select v-model="i.ter_activity" class="nm-select" :disabled="isReadOnly" aria-label="Physical activity level">
                      <option v-for="a2 in TER_ACTIVITY" :key="a2.value" :value="a2.value">{{ a2.label }} (+{{ a2.pct }}% of BMR)</option>
                    </select>
                  </label>
                </div>
                <!-- The result only; the working opens on request (user's call, 2026-11-01) -->
                <div v-if="terCalc" class="ter-result">
                  <p><strong>{{ whole(terCalc.ter) }} kcal/day</strong> <span class="c-sub">calculated TER</span></p>
                  <button type="button" class="ter-toggle" :aria-expanded="terShowSteps" aria-controls="ter-steps" @click="terShowSteps = !terShowSteps">
                    {{ terShowSteps ? 'Hide calculation' : 'Show calculation' }} <ChevronDown :size="14" :class="{ up: terShowSteps }" aria-hidden="true" />
                  </button>
                </div>
                <dl v-if="terCalc && terShowSteps" id="ter-steps" class="ter-steps">
                  <div><dt>DBW</dt><dd>({{ fmt(a.height_cm) }} − 100) − 10% = <strong>{{ fmt(terCalc.dbw, 1) }} kg</strong></dd></div>
                  <div><dt>BMR</dt><dd>{{ fmt(terCalc.dbw, 1) }} × {{ terCalc.perHour.toFixed(1) }} × 24 = <strong>{{ whole(terCalc.bmr) }} kcal</strong></dd></div>
                  <div><dt>Activity</dt><dd>{{ terCalc.act.label }}, {{ terCalc.act.pct }}% of BMR = <strong>{{ whole(terCalc.pa) }} kcal</strong></dd></div>
                  <div><dt>TEF</dt><dd>10% of (BMR + activity) = <strong>{{ whole(terCalc.tef) }} kcal</strong></dd></div>
                  <div class="ter-total"><dt>TER</dt><dd>{{ whole(terCalc.exact) }}, to the nearest 50 = <strong>{{ whole(terCalc.ter) }} kcal</strong></dd></div>
                </dl>
                <p v-if="!terCalc" class="c-sub">{{ ctx.patient?.sex ? 'Enter the height in Assessment to work out the TER.' : 'The patient\'s sex isn\'t on file, so the TER can\'t be worked out. Type it below.' }}</p>
              </div>
              <div class="ter-field">
                <Field label="TER (Total Energy Requirement), kcal/day" required :error="errors.target_kcal">
                  <input v-model="i.target_kcal" type="number" :min="L.target_kcal.min" :max="L.target_kcal.max" step="50" class="nm-input" :disabled="isReadOnly" />
                </Field>
              </div>
              <p v-if="!isReadOnly && terCalc && Number(i.target_kcal) !== terCalc.ter" class="macro-line">
                <span>This differs from the calculated TER of {{ whole(terCalc.ter) }} kcal.</span>
                <button type="button" class="nm-panel-link" @click="i.target_kcal = terCalc.ter">Use calculated TER</button>
              </p>
              <!-- Macro distribution: the RND sets the %, grams are TER × % ÷ kcal per gram, to the nearest 5 g -->
              <div class="macro-table" role="group" aria-label="Macronutrient distribution">
                <div class="mt-row mt-head"><span>Macronutrient</span><span>% of TER</span><span>Grams a day</span></div>
                <div v-for="m2 in MACROS" :key="m2.key" class="mt-row">
                  <span class="mt-name">{{ m2.label }} <small>{{ m2.per }} kcal/g</small></span>
                  <span><input v-model.number="i[`${m2.key}_pct`]" type="number" min="0" max="100" step="1" class="nm-input mt-pct" :disabled="isReadOnly" :aria-label="`${m2.label} percent of TER`" /> %</span>
                  <span class="mt-g">{{ i[`target_${m2.key}_g`] !== '' && i[`target_${m2.key}_g`] != null ? `${whole(i[`target_${m2.key}_g`])} g` : '—' }}</span>
                </div>
                <div class="mt-row mt-foot" :class="{ bad: errors.macro_pct }"><span>Total</span><span>{{ pctTotal }}%</span><span></span></div>
              </div>
              <p v-if="errors.macro_pct" class="mt-err" role="alert">{{ errors.macro_pct }}</p>
              <p v-else-if="!isReadOnly" class="c-sub">Starts at 55 / 20 / 25. Grams are TER × % ÷ 4 kcal/g (carbs, protein) or ÷ 9 kcal/g (fat), to the nearest 5 g.</p>
              <NcpExtraRows :rows="i.extra" :templates="MEASURE_TEMPLATES.intervention" :read-only="isReadOnly" empty="Add a sodium limit, fluid limit, fiber goal, activity and more. Pick from the list or type your own." />
              <Field label="Diet prescription" required group :hint="isReadOnly ? '' : 'The first lines are written from the TER, macros and other measurements above and update with them. Add the diet itself after them; you can edit everything.'">
                <textarea v-model="i.diet_prescription" class="nm-input" :maxlength="TMAX.diet_prescription" rows="4" placeholder="e.g. Low-GI Filipino diet. Brown rice, 1 cup max per meal; water instead of sweetened drinks." :disabled="isReadOnly"></textarea>
                <p v-if="!isReadOnly && rxBlock && rxCurrent !== rxBlock" class="macro-line rx-outdated">
                  <span>The TER and targets lines don't match what's set above.</span>
                  <button type="button" class="nm-panel-link" @click="updateRxLine">Update to current numbers</button>
                </p>
              </Field>
              <Field label="Intervention notes">
                <textarea v-model="i.intervention_notes" data-allow-emoji class="nm-input" :maxlength="TMAX.intervention_notes" rows="2" placeholder="Education given, goals agreed with the patient…" :disabled="isReadOnly"></textarea>
              </Field>
            </section>

            <!-- MONITORING (follow-ups) -->
            <section v-else-if="stepKey === 'monitoring'">
              <header class="step-head"><h3 class="step-title">Monitoring and evaluation</h3><p class="step-desc">How the patient did against the goals from their last record.</p></header>
              <div v-if="ctx.previous" class="prev-box">
                <span class="k">Goals from the {{ shortDate(ctx.previous.encounter_date) }} record</span>
                <p v-if="ctx.previous.pes_problem"><strong>{{ ctx.previous.pes_problem }}</strong><template v-if="ctx.previous.pes_etiology"> related to {{ ctx.previous.pes_etiology }}</template>.</p>
                <p v-if="ctx.previous.diet_prescription">{{ ctx.previous.diet_prescription }}</p>
                <p v-if="ctx.previous.target_kcal" class="c-sub">TER {{ whole(ctx.previous.target_kcal) }} kcal/day</p>
                <div class="since">
                  <div><span class="k">Weight since then</span><strong>{{ ctx.previous.weight_change_kg != null ? `${signed(ctx.previous.weight_change_kg)} kg` : 'Not measured' }}</strong></div>
                  <div><span class="k">7-day meal-plan adherence</span><strong>{{ ctx.adherence?.pct != null ? `${ctx.adherence.pct}%` : 'No meal plan yet' }}</strong></div>
                </div>
              </div>
              <Field label="Were those goals met?" required group>
                <div class="goals">
                  <button v-for="g in GOALS" :key="g.value" type="button" class="goal" :class="{ on: m.goal_status === g.value }" :disabled="isReadOnly" @click="m.goal_status = g.value">{{ g.label }}</button>
                </div>
              </Field>
              <Field label="Monitoring notes">
                <textarea v-model="m.monitoring_notes" data-allow-emoji class="nm-input" :maxlength="TMAX.monitoring_notes" rows="3" placeholder="Response to the plan, barriers, what to change next…" :disabled="isReadOnly"></textarea>
              </Field>
            </section>

            <!-- REVIEW -->
            <section v-else-if="stepKey === 'review'">
              <header class="step-head"><h3 class="step-title">{{ isReadOnly ? 'Summary' : 'Review and finalize' }}</h3><p class="step-desc">{{ isReadOnly ? 'The record as it was saved.' : 'Check the record before you finalize it. A finalized record can\'t be changed.' }}</p></header>
              <div v-if="!isReadOnly && missing.length" class="missing">
                <p><AlertTriangle :size="15" /> Still needed before you can finalize:</p>
                <ul><li v-for="x in missing" :key="x.label">{{ x.label }} <button type="button" class="nm-panel-link" @click="tab = x.step">Fix</button></li></ul>
              </div>
              <dl class="summary">
                <div><dt>Measurements</dt><dd>{{ measureLine }}</dd></div>
                <div v-if="assessExtraLine"><dt>Other measurements</dt><dd>{{ assessExtraLine }}</dd></div>
                <div><dt>Diagnosis</dt><dd :class="{ empty: !d.pes_problem }">{{ d.pes_problem ? pesSentence : 'Not filled in' }}</dd></div>
                <div><dt>Prescription</dt><dd :class="{ empty: !i.diet_prescription }">{{ i.diet_prescription || 'Not filled in' }}</dd></div>
                <div v-if="interventionExtraLine"><dt>Other targets</dt><dd>{{ interventionExtraLine }}</dd></div>
                <div v-if="showMonitoring"><dt>Goal status</dt><dd :class="{ empty: !m.goal_status }">{{ GOALS.find(g => g.value === m.goal_status)?.label || 'Not rated' }}</dd></div>
              </dl>
              <template v-if="isFinalized">
                <p class="done"><CheckCircle2 :size="16" /> This record is finalized.</p>
                <NuxtLink v-if="!inline" :to="`/meal-planning?relationship=${relationshipId}&edit=1`" class="nm-btn-dark nm-btn-sm" @click="emit('close')">Create or update the meal plan</NuxtLink>
              </template>
              <p v-else-if="!isReadOnly && !missing.length" class="nm-hint">Everything required is filled in. Finalizing makes this record permanent, so it can't be edited afterwards.</p>
            </section>
          </div>

          <!-- PATIENT STRIP -->
          <aside v-if="!inline || showStripInline" class="strip" :class="{ open: stripOpen }">
            <p class="strip-name">{{ ctx.patient?.name }}</p>
            <p class="c-sub">{{ [ctx.patient?.age != null ? `${ctx.patient.age} y/o` : null, SEX[ctx.patient?.sex]].filter(Boolean).join(', ') }}</p>
            <p v-if="ctx.patient?.allergies.length" class="allergy"><AlertTriangle :size="13" /> Allergy: {{ ctx.patient.allergies.join(', ') }}</p>
            <dl class="strip-facts">
              <div><dt>Conditions</dt><dd>{{ list(ctx.patient?.conditions) }}</dd></div>
              <div><dt>Diet</dt><dd>{{ list(ctx.patient?.dietary_restrictions) }}</dd></div>
              <div v-if="ctx.patient?.religion"><dt>Religion</dt><dd>{{ ctx.patient.religion }}</dd></div>
              <div><dt>Goals</dt><dd>{{ list(ctx.patient?.health_goals) }}</dd></div>
            </dl>
            <!-- the screening is the baseline progress is measured from, so it stands out -->
            <section v-if="ctx.screening" class="baseline" aria-label="Screening baseline">
              <p class="bl-title">Screening baseline</p>
              <p class="bl-sub">{{ shortDate(ctx.screening.date) }}. The starting point progress is measured from.</p>
              <dl class="bl-grid">
                <div><dt>BMI</dt><dd>{{ ctx.screening.bmi ?? '—' }}</dd><small>{{ ctx.screening.bmi_category }}</small></div>
                <div :class="{ risk: (ctx.screening.nrs_score ?? 0) >= 3 }"><dt>NRS-2002</dt><dd>{{ ctx.screening.nrs_score ?? '—' }}</dd><small>{{ ctx.screening.nrs_risk }}</small></div>
                <div><dt>TER</dt><dd>{{ whole(ctx.screening.tdee_kcal) }}</dd><small>kcal/day</small></div>
                <div><dt>BMR</dt><dd>{{ whole(ctx.screening.bmr_kcal) }}</dd><small>kcal/day</small></div>
              </dl>
              <p v-if="ctx.screening.symptoms" class="bl-sym"><strong>Symptoms:</strong> {{ ctx.screening.symptoms }}</p>
            </section>
            <template v-if="ctx.meal_plan">
              <p class="strip-k">Current meal plan</p>
              <p class="c-sub">{{ ctx.meal_plan.name }}{{ ctx.meal_plan.target_kcal ? `, ${whole(ctx.meal_plan.target_kcal)} kcal` : '' }}</p>
            </template>
            <template v-if="ctx.adherence">
              <p class="strip-k">7-day adherence</p>
              <p class="c-sub">{{ ctx.adherence.pct != null ? `${ctx.adherence.pct}%, ${ctx.adherence.logged} of ${ctx.adherence.planned} meals logged` : 'Nothing due yet' }}</p>
            </template>
          </aside>
        </div>

        <!-- FOOTER -->
        <footer class="ncp-foot">
          <p v-if="!isReadOnly && errorCount" class="foot-err" role="status"><AlertTriangle :size="14" /> Fix {{ errorCount }} highlighted field{{ errorCount === 1 ? '' : 's' }} before saving.</p>
          <button type="button" class="nm-btn-outline" :disabled="tab === 0" @click="tab--">Back</button>
          <div class="foot-right">
            <button v-if="!isReadOnly" type="button" class="nm-btn-outline" :disabled="saving || !dirty || errorCount > 0" @click="saveDraft">
              <Save :size="14" /> {{ saving ? 'Saving…' : 'Save draft' }}
            </button>
            <button v-if="tab < steps.length - 1" type="button" class="nm-btn-dark" @click="tab++">Next: {{ steps[tab + 1] }}</button>
            <button v-else-if="!isReadOnly" type="button" class="nm-btn-dark" :disabled="saving || missing.length > 0 || errorCount > 0" @click="confirmFinalize = true">Finalize record</button>
            <button v-else-if="isReadOnly && record?.status === 'draft' && canContinue" type="button" class="nm-btn-dark" @click="emit('continue')">Continue record</button>
            <button v-else-if="!inline" type="button" class="nm-btn-dark" @click="emit('close')">Close</button>
          </div>
        </footer>
      </template>

      <!-- CONFIRM: finalize -->
      <div v-if="confirmFinalize" class="inner-overlay" @click.self="confirmFinalize = false">
        <div class="nm-modal" role="alertdialog" aria-labelledby="fin-title">
          <button type="button" class="nm-modal-x" aria-label="Close" @click="confirmFinalize = false"><X :size="18" aria-hidden="true" /></button>
          <h3 id="fin-title" class="nm-modal-title">Finalize this NCP record?</h3>
          <p class="nm-modal-text">It becomes part of {{ patientName }}'s permanent record and can't be edited or deleted afterwards. Any changes are saved first.</p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" @click="confirmFinalize = false">Not yet</button>
            <button type="button" class="nm-btn-dark" :disabled="saving" @click="finalize">{{ saving ? 'Finalizing…' : 'Finalize record' }}</button>
          </div>
        </div>
      </div>

      <!-- CONFIRM: unsaved changes -->
      <div v-if="confirmLeave" class="inner-overlay" @click.self="confirmLeave = false">
        <div class="nm-modal" role="alertdialog" aria-labelledby="leave-title">
          <button type="button" class="nm-modal-x" aria-label="Close" @click="confirmLeave = false"><X :size="18" aria-hidden="true" /></button>
          <h3 id="leave-title" class="nm-modal-title">You have unsaved changes</h3>
          <p class="nm-modal-text">Save them as a draft so you can continue later?</p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" @click="confirmLeave = false">Keep editing</button>
            <button type="button" class="nm-btn-danger" @click="discardAndClose">Discard</button>
            <button type="button" class="nm-btn-dark" :disabled="saving" @click="saveAndClose">{{ saving ? 'Saving…' : 'Save draft' }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// The NCP record form — one longitudinal record across Assessment →
// Diagnosis → Intervention (→ Monitoring on follow-ups), then Review.
// Used by the NCP Records page, Client Detail and (inline) the consultation room.
//  - edit mode: resumes the patient's open draft, or starts a new one
//    pre-filled from their latest measurements (and, on a follow-up, the
//    previous record's PES and targets).
//  - view mode: one record, read-only.
// Nothing saves on its own: "Save draft" saves whatever is filled, and
// "Finalize record" (Review step, with a confirmation) locks it. Required
// fields mirror NcpRecord.finalize_missing() on the API.
import { AlertTriangle, Check, CheckCircle2, ChevronDown, FlaskConical, Info, Lock, Save, X } from 'lucide-vue-next'
import {
  DEFAULT_MACRO_PCT, KCAL_PER_G, MEASURE_TEMPLATES, NCP_LIMITS as L, NCP_TEXT_MAX as TMAX, PES_TERMS, TER_ACTIVITY, bmiClass, bmiOf, bpCategory, extraRowErrors,
  glucoseCategory, hba1cCategory, macroGrams, rangeError, terSteps,
} from '~/utils/ncp'
import { etiologyGroups } from '~/utils/ncpEtiology'
import { signGroups } from '~/utils/ncpSigns'

const props = defineProps({
  relationshipId: { type: [String, Number], required: true },
  patientName: { type: String, default: '' },
  mode: { type: String, default: 'edit' }, // 'edit' | 'view'
  recordId: { type: [String, Number], default: null }, // view mode
  canContinue: { type: Boolean, default: true }, // view mode: offer "Continue record" on a draft
  appointmentId: { type: [String, Number], default: null }, // link a new record to this consultation
  inline: { type: Boolean, default: false }, // render in place (consultation room) instead of a pop-up
  showStripInline: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'changed', 'continue'])
const { get, post, patch } = useApi()

/* ---------- small building blocks ---------- */
const Field = defineComponent({
  // `group`: the field holds several controls (BP pair, picker, buttons), so it
  // isn't a <label> — clicking its text mustn't press the first button.
  // `info`: a short explanation behind an ⓘ beside the label (hover, focus or tap).
  props: { label: String, required: Boolean, hint: String, group: Boolean, error: String, info: String },
  setup(p, { slots }) {
    // preventDefault: clicking the ⓘ inside a <label> mustn't focus the input.
    const infoTip = () => h('span', { class: 'info-tip', tabindex: 0, 'aria-label': `About ${p.label}: ${p.info}`, onClick: e => e.preventDefault() }, [
      h(Info, { size: 13, 'aria-hidden': 'true' }),
      h('span', { class: 'info-bubble', role: 'tooltip', 'aria-hidden': 'true' }, p.info),
    ])
    return () => h(p.group ? 'div' : 'label', { class: ['field', { invalid: !!p.error }], role: p.group ? 'group' : undefined, 'aria-label': p.group ? p.label : undefined }, [
      h('span', { class: 'field-label' }, [p.label, p.required ? h('span', { class: 'req', 'aria-hidden': 'true' }, ' *') : null, p.info ? infoTip() : null]),
      slots.default?.(),
      p.error ? h('span', { class: 'field-error', role: 'alert' }, p.error) : p.hint ? h('span', { class: 'field-hint' }, p.hint) : null,
    ])
  },
})
/* ---------- state ---------- */
const isLoading = ref(true)
const loadError = ref('')
const saveError = ref('')
const saving = ref(false)
const record = ref(null)
const ctx = ref({})
const isFollowUp = ref(false)
const tab = ref(0)
const stripOpen = ref(false)
const prefilled = ref(false)
const carried = ref(false)
const confirmFinalize = ref(false)
const confirmLeave = ref(false)
const lastSavedAt = ref('')

const a = ref({}); const d = ref({}); const i = ref({}); const m = ref({})
const isFinalized = computed(() => record.value?.status === 'completed')
const isReadOnly = computed(() => props.mode === 'view' || isFinalized.value)
const showMonitoring = computed(() => isFollowUp.value || (isReadOnly.value && !!(record.value?.goal_status || record.value?.monitoring_notes)))
const stepKeys = computed(() => ['assessment', 'diagnosis', 'intervention', ...(showMonitoring.value ? ['monitoring'] : []), 'review'])
const STEP_NAMES = { assessment: 'Assessment', diagnosis: 'Diagnosis', intervention: 'Intervention', monitoring: 'Monitoring', review: 'Review' }
const steps = computed(() => stepKeys.value.map(k => (k === 'review' && isReadOnly.value ? 'Summary' : STEP_NAMES[k])))
const stepKey = computed(() => stepKeys.value[tab.value])
const subtitle = computed(() => (record.value?.created_at ? `started ${dateTime(record.value.created_at)}` : 'new'))
const GOALS = [
  { value: 'met', label: 'Met' }, { value: 'partially_met', label: 'Partially met' },
  { value: 'not_met', label: 'Not met' }, { value: 'ongoing', label: 'Ongoing' },
]
const SEX = { male: 'Male', female: 'Female' }

function hydrate(r = {}) {
  const [sys, dia] = (r.blood_pressure || '').split('/')
  a.value = {
    height_cm: r.height_cm ?? '', weight_kg: r.weight_kg ?? '', bp_systolic: sys || '', bp_diastolic: dia || '',
    blood_glucose: r.blood_glucose ?? '', hba1c: r.hba1c ?? '', lab_notes: r.lab_notes ?? '', assessment_notes: r.assessment_notes ?? '',
    extra: (r.assessment_extra || []).map(x => ({ ...x })),
  }
  d.value = { pes_problem: r.pes_problem ?? '', pes_etiology: r.pes_etiology ?? '', pes_signs: r.pes_signs ?? '' }
  i.value = {
    target_kcal: r.target_kcal ?? '', target_carb_g: r.target_carb_g ?? '', target_protein_g: r.target_protein_g ?? '',
    target_fat_g: r.target_fat_g ?? '', diet_prescription: r.diet_prescription ?? '', intervention_notes: r.intervention_notes ?? '',
    ter_activity: r.ter_activity ?? '', ...splitOf(r),
    extra: (r.intervention_extra || []).map(x => ({ ...x })),
  }
  m.value = { goal_status: r.goal_status ?? '', monitoring_notes: r.monitoring_notes ?? '' }
}
// The record's macro split in %. Records from before the % were stored get it
// back from their grams (fat takes the remainder so it adds up to 100); with
// no grams either, the standard 55 / 20 / 25.
function splitOf(r) {
  if (r.carb_pct != null && r.protein_pct != null && r.fat_pct != null) return { carb_pct: r.carb_pct, protein_pct: r.protein_pct, fat_pct: r.fat_pct }
  const t = Number(r.target_kcal)
  const g = { carb: Number(r.target_carb_g), protein: Number(r.target_protein_g), fat: Number(r.target_fat_g) }
  if (t && g.carb && g.protein && g.fat) {
    const carb = Math.round(g.carb * KCAL_PER_G.carb / t * 100)
    const protein = Math.round(g.protein * KCAL_PER_G.protein / t * 100)
    return { carb_pct: carb, protein_pct: protein, fat_pct: 100 - carb - protein }
  }
  return { carb_pct: DEFAULT_MACRO_PCT.carb, protein_pct: DEFAULT_MACRO_PCT.protein, fat_pct: DEFAULT_MACRO_PCT.fat }
}
hydrate()

/* ---------- pre-fill (only fields that are still empty) ---------- */
const prefilledFields = ref([])
function prefillBlanks() {
  const pf = ctx.value.prefill || {}
  const blank = v => String(v ?? '').trim() === ''
  for (const f of ['height_cm', 'weight_kg', 'blood_glucose', 'hba1c']) {
    if (pf[f] && blank(a.value[f])) { a.value[f] = pf[f].value; prefilledFields.value.push(f) }
  }
  if (pf.blood_pressure && blank(a.value.bp_systolic) && blank(a.value.bp_diastolic)) {
    [a.value.bp_systolic, a.value.bp_diastolic] = String(pf.blood_pressure.value).split('/')
    prefilledFields.value.push('blood_pressure')
  }
  prefilled.value = prefilledFields.value.length > 0
  const prev = ctx.value.previous
  const blankPlan = blank(d.value.pes_problem) && blank(d.value.pes_etiology) && blank(i.value.target_kcal) && blank(i.value.diet_prescription)
  if (isFollowUp.value && prev && blankPlan) {
    d.value = { pes_problem: prev.pes_problem || '', pes_etiology: prev.pes_etiology || '', pes_signs: prev.pes_signs || '' }
    Object.assign(i.value, {
      target_kcal: prev.target_kcal ?? '', target_carb_g: prev.target_carb_g ?? '', target_protein_g: prev.target_protein_g ?? '',
      target_fat_g: prev.target_fat_g ?? '', diet_prescription: prev.diet_prescription || '',
      ter_activity: prev.ter_activity || '', ...splitOf(prev),
    })
    carried.value = true
  }
  // TER: the activity starts from the screening's answer; an empty TER is
  // filled with the calculated one, and the grams follow from the %.
  if (blank(i.value.ter_activity)) i.value.ter_activity = ctx.value.screening?.ter_activity || 'sedentary'
  if (blank(i.value.target_kcal) && terCalc.value) i.value.target_kcal = terCalc.value.ter
  applyGrams()
  initRxLine()
}
function srcHint(f) {
  const s = ctx.value.prefill?.[f]
  if (!s || isReadOnly.value || !prefilledFields.value.includes(f)) return ''
  return `From their ${s.source}, ${shortDate(s.date)}`
}

/* ---------- live clinical help ---------- */
// Only from in-range values — an impossible weight mustn't show a BMI.
// Only categorise a reading that passes the form's own checks.
const liveBp = computed(() => (errors.value.blood_pressure ? null : bpCategory(a.value.bp_systolic, a.value.bp_diastolic)))
const liveGlucose = computed(() => (errors.value.blood_glucose ? null : glucoseCategory(a.value.blood_glucose)))
const liveHba1c = computed(() => (errors.value.hba1c ? null : hba1cCategory(a.value.hba1c)))
const liveBmi = computed(() =>(rangeError('weight_kg', a.value.weight_kg) || rangeError('height_cm', a.value.height_cm) ? null : bmiOf(a.value.weight_kg, a.value.height_cm)))
/* ---------- TER and macro distribution (Tannhauser, utils/ncp.js) ---------- */
const MACROS = [
  { key: 'carb', label: 'Carbohydrate', per: KCAL_PER_G.carb },
  { key: 'protein', label: 'Protein', per: KCAL_PER_G.protein },
  { key: 'fat', label: 'Fat', per: KCAL_PER_G.fat },
]
const terCalc = computed(() => (rangeError('height_cm', a.value.height_cm) ? null : terSteps(a.value.height_cm, ctx.value.patient?.sex, i.value.ter_activity)))
const terShowSteps = ref(false)
const pctTotal = computed(() => MACROS.reduce((s, m2) => s + (Number(i.value[`${m2.key}_pct`]) || 0), 0))
// Grams are calculated only: TER × % ÷ kcal per gram, to the nearest 5 g.
// Left alone when they already match, so a saved draft doesn't turn "unsaved".
function applyGrams() {
  if (isReadOnly.value) return
  const ter = Number(i.value.target_kcal)
  const g = ter && !rangeError('target_kcal', ter)
    ? macroGrams(ter, { carb: i.value.carb_pct, protein: i.value.protein_pct, fat: i.value.fat_pct })
    : { carb: '', protein: '', fat: '' }
  for (const k of ['carb', 'protein', 'fat']) {
    const f = `target_${k}_g`
    const cur = i.value[f]
    const empty = cur === '' || cur == null
    const same = empty ? g[k] === '' : g[k] !== '' && Number(cur) === Number(g[k])
    if (!same) i.value[f] = g[k]
  }
}
watch(() => [i.value.target_kcal, i.value.carb_pct, i.value.protein_pct, i.value.fat_pct], applyGrams)
// The calculated TER follows height and activity while the RND hasn't typed their own.
watch(() => terCalc.value?.ter, (now, before) => {
  if (isReadOnly.value || !now) return
  if (String(i.value.target_kcal ?? '').trim() === '' || Number(i.value.target_kcal) === before) i.value.target_kcal = now
})
/* ---------- Diet prescription: the lines written from the Intervention (user's calls, 2026-11-01) ----------
   The prescription starts with up to two lines stating what's set above:
     TER 1,850 kcal/day: carbohydrate 255 g (55%), protein 95 g (20%), fat 50 g (25%).
     Other targets: Sodium 1500 mg/day, Water intake 2 L/day.
   (the second from the complete "Other measurements" rows). It's plain text
   the RND can edit. While those lines are still what we wrote, they follow
   the form; once the RND changes them, they're theirs, and "Update to
   current numbers" rewrites them. Saved as part of diet_prescription. */
const RX_LINE = /^TER [\d,]+ kcal\/day: carbohydrate /
const RX_OTHER = /^Other targets: /
// (Uses only what's defined above: the watch below reads it during setup.)
const rxBlock = computed(() => {
  const lines = []
  const ter = Number(i.value.target_kcal)
  const g = { carb: i.value.target_carb_g, protein: i.value.target_protein_g, fat: i.value.target_fat_g }
  if (ter && !rangeError('target_kcal', ter) && pctTotal.value === 100 && Object.values(g).every(v => v !== '' && v != null)) {
    const n = v => Math.round(Number(v)).toLocaleString('en-PH')
    const part = k => `${MACROS.find(m2 => m2.key === k).label.toLowerCase()} ${n(g[k])} g (${i.value[`${k}_pct`]}%)`
    lines.push(`TER ${n(ter)} kcal/day: ${part('carb')}, ${part('protein')}, ${part('fat')}.`)
  }
  const others = (i.value.extra || [])
    .filter(r => r.label?.trim() && String(r.value ?? '').trim() && !Object.keys(extraRowErrors(r)).length)
    .map(r => `${r.label.trim()} ${String(r.value).trim()}${r.unit?.trim() ? ` ${r.unit.trim()}` : ''}`)
  if (others.length) lines.push(`Other targets: ${others.join(', ')}.`)
  return lines.join('\n')
})
// How many of the prescription's first lines are written ones (0–2).
function rxAutoCount(lines) {
  let n = RX_LINE.test(lines[0] || '') ? 1 : 0
  if (RX_OTHER.test(lines[n] || '')) n++
  return n
}
const rxCurrent = computed(() => {
  const lines = (i.value.diet_prescription || '').split('\n')
  return lines.slice(0, rxAutoCount(lines)).join('\n')
})
let rxWritten = '' // the lines this form last wrote, so it knows they're still ours
function updateRxLine() {
  const lines = (i.value.diet_prescription || '').split('\n')
  const rest = lines.slice(rxAutoCount(lines)).join('\n')
  i.value.diet_prescription = [rxBlock.value, rest.trim() ? rest : ''].filter(Boolean).join('\n')
  rxWritten = rxBlock.value
}
// On opening a record that can be edited: put the lines at the top (or bring
// earlier ones up to date).
function initRxLine() {
  if (isReadOnly.value) return
  if (rxBlock.value && rxCurrent.value !== rxBlock.value) updateRxLine()
  else rxWritten = rxCurrent.value
}
watch(rxBlock, () => {
  if (isReadOnly.value) return
  if (!(i.value.diet_prescription || '').trim() || rxCurrent.value === rxWritten) updateRxLine()
})
const fmt = (v, dp = 0) => (v === '' || v == null ? '—' : Number(v).toLocaleString('en-PH', { maximumFractionDigits: dp }))
const pesSentence = computed(() => {
  if (!filled(d.value.pes_problem) && !filled(d.value.pes_etiology) && !filled(d.value.pes_signs)) return 'Fill in the problem, etiology and signs to build the statement.'
  // A sign just picked ends in a space (or "; ") left for its value; don't show that before the full stop.
  const signs = (d.value.pes_signs || '').replace(/[\s;,]+$/, '')
  return `${d.value.pes_problem || '…'}${d.value.pes_etiology ? ` related to ${d.value.pes_etiology}` : ''}${signs ? `, as evidenced by ${signs}` : ''}.`
})

/* ---------- PES picker ---------- */
const pesOpen = ref(false)
const activeIdx = ref(-1)
const pesMatches = computed(() => {
  const q = (d.value.pes_problem || '').trim().toLowerCase()
  return PES_TERMS.map(g => ({ group: g.group, terms: g.terms.filter(t => !q || t.toLowerCase().includes(q)) }))
    .filter(g => g.terms.length && !(g.terms.length === 1 && g.terms[0].toLowerCase() === q))
})
const flatMatches = computed(() => pesMatches.value.flatMap(g => g.terms))
function move(dir) {
  if (!pesOpen.value) { pesOpen.value = true; return }
  const n = flatMatches.value.length
  if (n) activeIdx.value = (activeIdx.value + dir + n) % n
}
function pick(t) {
  d.value.pes_problem = t
  pesOpen.value = false
  activeIdx.value = -1
}
function pickActive(e) {
  if (pesOpen.value && flatMatches.value[activeIdx.value]) { e.preventDefault(); pick(flatMatches.value[activeIdx.value]) }
}
function closeSoon() { setTimeout(() => { pesOpen.value = false }, 120) }

/* ---------- Etiology picker (Etiology Matrix, utils/ncpEtiology.js) ---------- */
// Same behaviour as the PES picker, on a textarea: the arrow keys only drive
// the list while it's open, and Enter only picks when an option is highlighted
// (otherwise it's a normal new line).
const etOpen = ref(false)
const etIdx = ref(-1)
const etGroups = computed(() => {
  const q = (d.value.pes_etiology || '').trim()
  const groups = etiologyGroups(q, d.value.pes_problem)
  const all = groups.flatMap(g => g.items)
  return all.length && all.every(e => e.t.toLowerCase() === q.toLowerCase()) ? [] : groups
})
const etFlat = computed(() => etGroups.value.flatMap(g => g.items))
function etMove(e, dir) {
  if (!etOpen.value || !etFlat.value.length) return
  e.preventDefault()
  const n = etFlat.value.length
  etIdx.value = (etIdx.value + dir + n) % n
}
function etPick(t) {
  d.value.pes_etiology = t
  etOpen.value = false
  etIdx.value = -1
}
function etPickActive(e) {
  if (etOpen.value && etFlat.value[etIdx.value]) { e.preventDefault(); etPick(etFlat.value[etIdx.value].t) }
}
function etCloseSoon() { setTimeout(() => { etOpen.value = false; etIdx.value = -1 }, 120) }

/* ---------- Signs picker (Assessment Terminology, utils/ncpSigns.js) ----------
   Same behaviour as the Etiology picker, but the box holds several signs
   separated by "; " and the RND types values and their own words between
   them. So it searches the words just before the cursor: from the last ";"
   (or line break) it tries the longest run of trailing words first, then
   fewer, and uses the first that matches a term — "…diet recall nausea"
   searches "nausea", "ankle ede" searches "ankle ede". Many terms contain
   commas ("Glucose, fasting"), so a comma never ends the search. Picking
   replaces just those words with the term, adds "; " before it if needed and
   leaves the cursor after it for the patient's value. */
const sgOpen = ref(false)
const sgIdx = ref(-1)
const signsBox = ref(null)
const sgCaret = ref(null)
function sgTrackCaret() { sgCaret.value = signsBox.value?.selectionStart ?? null }
const sgSearch = computed(() => {
  const text = d.value.pes_signs || ''
  const caret = sgCaret.value == null ? text.length : Math.min(sgCaret.value, text.length)
  const before = text.slice(0, caret)
  const segStart = Math.max(before.lastIndexOf(';'), before.lastIndexOf('\n')) + 1
  const segment = before.slice(segStart)
  // Nothing typed for this sign yet (empty box, or just after "; "): the whole list.
  if (!segment.trim()) return { start: caret, end: caret, groups: signGroups('') }
  // Cursor after a space: between words (e.g. just after a picked term, ready
  // for its value), so nothing to suggest until the next word is typed.
  if (/\s$/.test(segment)) return { start: caret, end: caret, groups: [] }
  // Where each word starts, longest run of words first.
  const starts = [...segment.matchAll(/(?:^|[\s,]+)(?=\S)/g)].map(m => m.index + m[0].length)
  for (const s of starts) {
    const q = segment.slice(s).trim()
    if (q.replace(/[^a-z0-9]/gi, '').length < 2) continue
    const groups = signGroups(q)
    if (groups.length) return { start: segStart + s, end: caret, groups }
  }
  return { start: caret, end: caret, groups: [] }
})
const sgGroups = computed(() => sgSearch.value.groups)
const sgFlat = computed(() => sgGroups.value.flatMap(g => g.items))
function sgMove(e, dir) {
  if (!sgOpen.value || !sgFlat.value.length) return
  e.preventDefault()
  const n = sgFlat.value.length
  sgIdx.value = (sgIdx.value + dir + n) % n
}
function sgPick(t) {
  const text = d.value.pes_signs || ''
  const { start, end } = sgSearch.value
  let head = text.slice(0, start).replace(/[\s,]+$/, '')
  if (head && !/[;\n]$/.test(head)) head += ';'
  head = head ? `${head} ` : ''
  const tail = text.slice(end).replace(/^\s+/, '')
  const inserted = `${head}${t}${tail.startsWith(';') ? '' : ' '}`
  d.value.pes_signs = `${inserted}${tail}`.slice(0, TMAX.pes_signs)
  sgOpen.value = false
  sgIdx.value = -1
  nextTick(() => {
    const el = signsBox.value
    if (!el) return
    el.focus()
    const at = Math.min(inserted.length, el.value.length)
    el.setSelectionRange(at, at)
    sgCaret.value = at
  })
}
function sgPickActive(e) {
  if (sgOpen.value && sgFlat.value[sgIdx.value]) { e.preventDefault(); sgPick(sgFlat.value[sgIdx.value].t) }
}
function sgCloseSoon() { setTimeout(() => { sgOpen.value = false; sgIdx.value = -1 }, 120) }

/* ---------- required fields (mirrors NcpRecord.finalize_missing) ---------- */
const filled = v => String(v ?? '').trim() !== ''
const missing = computed(() => {
  const idx = k => stepKeys.value.indexOf(k)
  const out = []
  if (!filled(a.value.height_cm) || !filled(a.value.weight_kg)) out.push({ label: 'Height and weight', step: idx('assessment') })
  if (!filled(d.value.pes_problem)) out.push({ label: 'PES problem', step: idx('diagnosis') })
  if (!filled(d.value.pes_etiology) || !filled(d.value.pes_signs)) out.push({ label: 'PES etiology and signs', step: idx('diagnosis') })
  if (!filled(i.value.target_kcal)) out.push({ label: 'TER', step: idx('intervention') })
  if (!filled(i.value.diet_prescription)) out.push({ label: 'Diet prescription', step: idx('intervention') })
  if (showMonitoring.value && !filled(m.value.goal_status)) out.push({ label: 'Goal status', step: idx('monitoring') })
  return out
})
/* ---------- limits: shown live, block Save draft / Finalize ---------- */
const errors = computed(() => {
  const e = {}
  for (const f of ['height_cm', 'weight_kg', 'blood_glucose', 'hba1c']) { const x = rangeError(f, a.value[f]); if (x) e[f] = x }
  for (const f of ['target_kcal', 'target_carb_g', 'target_protein_g', 'target_fat_g']) { const x = rangeError(f, i.value[f]); if (x) e[f] = x }
  const sys = String(a.value.bp_systolic ?? '').trim()
  const dia = String(a.value.bp_diastolic ?? '').trim()
  if (sys || dia) {
    const bp = !sys || !dia ? 'Enter both numbers, e.g. 120 / 80.'
      : rangeError('bp_systolic', sys) || rangeError('bp_diastolic', dia) || (Number(dia) >= Number(sys) ? 'The first number (systolic) must be higher.' : '')
    if (bp) e.blood_pressure = bp
  }
  const rowsBad = rows => rows.some(row => Object.keys(extraRowErrors(row)).length)
  if (rowsBad(a.value.extra)) e.assessment_extra = 'Fix the other measurements.'
  if (rowsBad(i.value.extra)) e.intervention_extra = 'Fix the other measurements.'
  const pcts = MACROS.map(m2 => i.value[`${m2.key}_pct`])
  if (pcts.some(p => p === '' || p == null || !Number.isInteger(Number(p)) || p < 0 || p > 100)) e.macro_pct = 'Each % must be a whole number from 0 to 100.'
  else if (pctTotal.value !== 100) e.macro_pct = `Carbs, protein and fat must add up to 100% (now ${pctTotal.value}%).`
  return e
})
const errorCount = computed(() => Object.keys(errors.value).length)
const ERROR_STEP = {
  height_cm: 'assessment', weight_kg: 'assessment', blood_pressure: 'assessment', blood_glucose: 'assessment', hba1c: 'assessment', assessment_extra: 'assessment',
  target_kcal: 'intervention', target_carb_g: 'intervention', target_protein_g: 'intervention', target_fat_g: 'intervention', intervention_extra: 'intervention',
  macro_pct: 'intervention',
}
function stepHasError(index) {
  return Object.keys(errors.value).some(k => ERROR_STEP[k] === stepKeys.value[index])
}

function stepState(index) {
  if (isReadOnly.value) return 'done'
  const k = stepKeys.value[index]
  if (k === 'review') return missing.value.length ? 'todo' : 'ready'
  const mine = missing.value.filter(x => x.step === index)
  const touched = {
    assessment: () => filled(a.value.height_cm) || filled(a.value.weight_kg) || filled(a.value.assessment_notes),
    diagnosis: () => filled(d.value.pes_problem) || filled(d.value.pes_etiology),
    intervention: () => filled(i.value.target_kcal) || filled(i.value.diet_prescription),
    monitoring: () => filled(m.value.goal_status) || filled(m.value.monitoring_notes),
  }[k]()
  return !mine.length ? 'done' : touched ? 'partial' : 'todo'
}

const measureLine = computed(() => [
  filled(a.value.weight_kg) ? `${a.value.weight_kg} kg` : null, filled(a.value.height_cm) ? `${a.value.height_cm} cm` : null,
  liveBmi.value ? `BMI ${liveBmi.value} (${bmiClass(liveBmi.value)})` : null,
  filled(a.value.bp_systolic) ? `BP ${a.value.bp_systolic}/${a.value.bp_diastolic}` : null,
  filled(a.value.blood_glucose) ? `FBS ${a.value.blood_glucose} mg/dL` : null, filled(a.value.hba1c) ? `HbA1c ${a.value.hba1c}%` : null,
].filter(Boolean).join(', ') || 'Not filled in')
// "+ Add Field" rows, e.g. "Sodium 1500 mg"; half-filled rows are left out.
const extraLine = rows => rows
  .filter(r => r.label?.trim() && filled(r.value))
  .map(r => `${r.label.trim()} ${r.value}${r.unit?.trim() ? ` ${r.unit.trim()}` : ''}`)
  .join(', ')
const assessExtraLine = computed(() => extraLine(a.value.extra))
const interventionExtraLine = computed(() => extraLine(i.value.extra))

/* ---------- save / finalize ---------- */
// A ref, so saving (which changes only this) re-evaluates `dirty`.
const savedSnapshot = ref('')
const snapshot = () => JSON.stringify([a.value, d.value, i.value, m.value])
const dirty = computed(() => !isReadOnly.value && snapshot() !== savedSnapshot.value)
const saveStateText = computed(() => (saving.value ? 'Saving…' : dirty.value ? 'Unsaved changes' : lastSavedAt.value ? `Saved ${lastSavedAt.value}` : record.value ? 'Draft' : 'Not saved yet'))
const saveStateClass = computed(() => (dirty.value ? 'dirty' : lastSavedAt.value ? 'ok' : ''))

function payload() {
  const num = v => (v === '' || v == null ? null : v)
  const sys = String(a.value.bp_systolic ?? '').trim()
  const dia = String(a.value.bp_diastolic ?? '').trim()
  return {
    weight_kg: num(a.value.weight_kg), height_cm: num(a.value.height_cm), blood_pressure: sys || dia ? `${sys}/${dia}` : null,
    blood_glucose: num(a.value.blood_glucose), hba1c: num(a.value.hba1c), lab_notes: a.value.lab_notes || null,
    assessment_notes: a.value.assessment_notes || null, assessment_extra: a.value.extra.filter(r => r.label.trim()),
    pes_problem: d.value.pes_problem || null, pes_etiology: d.value.pes_etiology || null, pes_signs: (d.value.pes_signs || '').replace(/[\s;,]+$/, '') || null,
    target_kcal: num(i.value.target_kcal), target_carb_g: num(i.value.target_carb_g), target_protein_g: num(i.value.target_protein_g),
    target_fat_g: num(i.value.target_fat_g), ter_activity: i.value.ter_activity || null,
    carb_pct: num(i.value.carb_pct), protein_pct: num(i.value.protein_pct), fat_pct: num(i.value.fat_pct),
    diet_prescription: i.value.diet_prescription || null,
    intervention_notes: i.value.intervention_notes || null, intervention_extra: i.value.extra.filter(r => r.label.trim()),
    goal_status: m.value.goal_status || null, monitoring_notes: m.value.monitoring_notes || null,
  }
}
async function saveDraft() {
  saving.value = true
  saveError.value = ''
  try {
    const sent = snapshot()
    if (record.value) {
      record.value = await patch(`/rnd/ncp/${record.value.id}/`, payload())
    } else {
      const appt = props.appointmentId || ctx.value.appointment_id
      record.value = await post(`/rnd/relationships/${props.relationshipId}/ncp/`, {
        relationship: Number(props.relationshipId),
        encounter_date: new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' }),
        ...(appt ? { appointment: Number(appt) } : {}),
        ...payload(),
      })
    }
    savedSnapshot.value = sent
    lastSavedAt.value = new Date().toLocaleTimeString('en-PH', { hour: 'numeric', minute: '2-digit' })
    emit('changed')
    return true
  } catch (e) {
    saveError.value = ncpError(e, 'Could not save this record.')
    return false
  } finally {
    saving.value = false
  }
}
async function finalize() {
  if (dirty.value || !record.value) {
    if (!(await saveDraft())) { confirmFinalize.value = false; return }
  }
  saving.value = true
  try {
    record.value = await patch(`/rnd/ncp/${record.value.id}/finalize/`)
    savedSnapshot.value = snapshot()
    confirmFinalize.value = false
    emit('changed')
  } catch (e) {
    saveError.value = ncpError(e, 'Could not finalize this record.')
    confirmFinalize.value = false
  } finally {
    saving.value = false
  }
}
function requestClose() {
  if (dirty.value) confirmLeave.value = true
  else emit('close')
}
async function saveAndClose() {
  if (errorCount.value) { confirmLeave.value = false; return }
  if (await saveDraft()) { confirmLeave.value = false; emit('close') }
  else confirmLeave.value = false
}
function discardAndClose() {
  confirmLeave.value = false
  emit('close')
}
function onBeforeUnload(e) { if (dirty.value) { e.preventDefault(); e.returnValue = '' } }
onMounted(() => window.addEventListener('beforeunload', onBeforeUnload))
onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload))
defineExpose({ dirty, requestClose, saveDraft })

/* ---------- load ---------- */
async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const [records, context] = await Promise.all([
      get(`/rnd/relationships/${props.relationshipId}/ncp/`),
      get(`/rnd/relationships/${props.relationshipId}/ncp/context/`).catch(() => ({})),
    ])
    ctx.value = context
    if (props.mode === 'view') {
      record.value = records.find(r => String(r.id) === String(props.recordId)) || null
      if (!record.value) throw new Error('not found')
      isFollowUp.value = !!record.value.is_follow_up
      hydrate(record.value)
    } else {
      record.value = records.find(r => r.status === 'draft') || null
      isFollowUp.value = record.value ? record.value.is_follow_up : !!context.is_follow_up
      if (record.value) {
        hydrate(record.value)
      }
      const before = snapshot()
      prefillBlanks()
      // A new record starts "unsaved" only if the RND changes something; a
      // resumed draft that just got pre-filled values offers to save them.
      savedSnapshot.value = record.value ? before : snapshot()
      // A new record starts at Assessment (pre-filled height/weight would
      // otherwise skip it); a resumed draft opens where something is missing.
      const first = missing.value[0]
      tab.value = !record.value ? 0 : (first ? first.step : stepKeys.value.length - 1)
    }
    if (props.mode === 'view') savedSnapshot.value = snapshot()
  } catch {
    loadError.value = 'Could not load this NCP record. Please try again.'
  } finally {
    isLoading.value = false
  }
}
onMounted(load)

/* ---------- helpers ---------- */
const list = l => (l?.length ? l.join(', ') : 'Not recorded')
const whole = v => (v == null || v === '' ? '—' : Math.round(Number(v)).toLocaleString('en-PH'))
const signed = v => `${Number(v) > 0 ? '+' : Number(v) < 0 ? '−' : ''}${Math.abs(Number(v)).toFixed(1)}`
function ncpError(e, fallback) {
  const data = e?.data || {}
  if (data.detail) return Array.isArray(data.detail) ? data.detail[0] : data.detail
  const first = Object.entries(data).find(([, v]) => Array.isArray(v) && typeof v[0] === 'string')
  return first ? `${first[0].replace(/_/g, ' ')}: ${first[1][0]}` : fallback
}
</script>

<style scoped>
.ncp-overlay { z-index: 200; }
.ncp { position: relative; background: #fff; border-radius: 18px; width: 100%; max-width: 960px; max-height: 86dvh; display: flex; flex-direction: column; font-family: 'Inter', sans-serif; color: #1a3a1a; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22); overflow: hidden; }
.ncp.is-inline { max-width: none; max-height: none; height: 100%; box-shadow: none; border: 1px solid #eceeec; }
.ncp-inline { height: 100%; }
/* In the consultation room's narrow panel the steps share one row: dot above
   the name, equal columns (4 steps, 5 on a follow-up) — no wrapping. */
.ncp.is-inline .steps { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); gap: 4px; overflow: visible; padding: 8px 10px; }
.ncp.is-inline .step { flex-direction: column; justify-content: center; gap: 4px; padding: 6px 2px; border-radius: 12px; font-size: 0.72rem; min-width: 0; }
.ncp.is-inline .step-name { max-width: 100%; overflow: hidden; text-overflow: ellipsis; }
.ncp.is-inline .g4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.ncp.is-inline .ncp-head, .ncp.is-inline .ncp-form, .ncp.is-inline .ncp-foot { padding-left: 16px; padding-right: 16px; }
.pad { padding: 20px 24px; }

.ncp-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 20px 24px 14px; border-bottom: 1px solid #d9e3dc; }
.ncp-title { font-family: 'Playfair Display', serif; font-size: 1.25rem; margin: 0; font-weight: 700; line-height: 1.2; }
.ncp-sub { font-size: 0.8rem; color: #8a9a8a; margin: 2px 0 0; }
.ncp-kind { font-weight: 700; color: #3d4a3d; }
.ncp-kind.follow { color: #b8860b; }
.ncp-head-right { display: flex; align-items: center; gap: 10px; }
.save-state { font-size: 0.74rem; font-weight: 600; color: #8a9a8a; white-space: nowrap; }
.save-state.dirty { color: #9a6a00; }
.save-state.ok { color: #1f6f46; }
.icon-x { border: none; background: none; color: #6a7a6a; cursor: pointer; border-radius: 6px; display: flex; }
.icon-x:hover { background: #f2f5f2; }

.steps { display: flex; gap: 4px; padding: 8px 24px; border-bottom: 1px solid #d9e3dc; overflow-x: auto; }
.step { display: inline-flex; align-items: center; gap: 6px; border: none; background: none; padding: 5px 11px 5px 5px; border-radius: 999px; font-family: inherit; font-size: 0.78rem; font-weight: 600; color: #6a7a6a; cursor: pointer; white-space: nowrap; }
.step:hover { background: #f7f9f7; }
.step.active { background: #0a4a37; color: #fff; }
.step-dot { width: 20px; height: 20px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; background: #eceeec; color: #6a7a6a; }
.step.done .step-dot { background: #1f8f5c; color: #fff; }
.step.partial .step-dot { background: #fdf1d6; color: #8a6a00; }
.step.ready .step-dot { background: #D4A017; color: #1a3a1a; }
.step.active .step-dot { box-shadow: 0 0 0 2px #0a4a37, 0 0 0 3px rgba(255, 255, 255, 0.6); }

.ncp-body { display: grid; grid-template-columns: minmax(0, 1fr) 280px; flex: 1; min-height: 0; }
.ncp.is-inline .ncp-body { grid-template-columns: minmax(0, 1fr); }
.ncp-form { padding: 18px 24px 24px; overflow-y: auto; min-width: 0; }
/* step heading: what the step is for (the step bar already numbers them) */
.step-head { margin: 0 0 16px; }
.step-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 700; color: #1a3a1a; margin: 0 0 2px; }
.step-desc { font-size: 0.84rem; color: #5a6a5a; margin: 0; line-height: 1.5; }
.summary dd.empty { color: #9aaa9a; font-weight: 500; }
.banner { display: flex; align-items: center; gap: 8px; background: #f4f6f4; border-radius: 8px; padding: 9px 12px; font-size: 0.82rem; color: #4a5a4a; margin: 0 0 14px; }
.banner.lock { background: #e3f3ea; color: #1f6f46; }
.hint-box { display: flex; gap: 8px; align-items: flex-start; background: #f3f8f4; border: 1px solid #dcebe0; border-radius: 8px; padding: 9px 12px; font-size: 0.8rem; color: #2f5f3f; margin: 0 0 14px; }
.strip-toggle { display: none; }

.grid { display: grid; column-gap: 12px; row-gap: 0; margin-bottom: 4px; } /* rows are spaced by each field's margin (they span 4 subgrid rows) */
.g3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.g4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
:deep(.field) { display: flex; flex-direction: column; gap: 5px; margin-bottom: 12px; min-width: 0; }
/* Fields side by side share label / input / hint rows, so the inputs line up
   even when one label wraps to two lines ("Blood pressure (mmHg)"). */
.grid > :deep(*) { grid-row: span 4; } /* label · control · category · hint */
.grid > :deep(.field) { display: grid; grid-template-rows: subgrid; row-gap: 0; align-content: start; }
.grid > :deep(.field > * + *) { margin-top: 5px; } /* spacing only where there's content, so empty rows add nothing */
.grid > :deep(.field > .field-label) { align-self: end; }
:deep(.field-label) { font-size: 0.8rem; font-weight: 600; color: #1a3a1a; position: relative; }
/* ⓘ beside a label; the bubble stays within the field's width so it never runs off the modal. */
:deep(.info-tip) { display: inline-flex; vertical-align: -2px; margin-left: 5px; color: #8a9a8a; cursor: help; border-radius: 50%; }
:deep(.info-tip:hover), :deep(.info-tip:focus-visible) { color: #00382a; outline: none; }
:deep(.info-tip:focus-visible) { box-shadow: 0 0 0 2px rgba(0, 56, 42, 0.25); }
:deep(.info-bubble) {
  position: absolute; left: 0; bottom: calc(100% + 6px); z-index: 30; width: max-content; max-width: 100%;
  background: #00382a; color: #fff; font-size: 0.74rem; font-weight: 500; line-height: 1.4;
  padding: 7px 10px; border-radius: 8px; box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
  opacity: 0; visibility: hidden; transition: opacity 0.12s; pointer-events: none;
}
:deep(.info-tip:hover .info-bubble), :deep(.info-tip:focus .info-bubble) { opacity: 1; visibility: visible; }
:deep(.req) { color: #c0392b; }
:deep(.field-hint) { font-size: 0.72rem; color: #8a9a8a; }
:deep(.field-error) { font-size: 0.72rem; color: #c0392b; font-weight: 600; }
:deep(.field.invalid .nm-input) { border-color: #e0a3a3; background: #fffafa; }
.step.err .step-dot { background: #fdecec; color: #a12525; }
.foot-err { flex-basis: 100%; display: flex; align-items: center; gap: 6px; margin: 0 0 4px; font-size: 0.78rem; font-weight: 600; color: #a12525; }
.bp { display: flex; align-items: center; gap: 6px; }
.bp input { min-width: 0; padding-left: 8px; padding-right: 8px; }
/* No up/down arrows on number boxes: in the narrow room panel they hid the
   value (128 showed as "12") and a stray click set an empty box to its min. */
input[type='number'] { appearance: textfield; -moz-appearance: textfield; }
input[type='number']::-webkit-outer-spin-button,
input[type='number']::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.bp span { color: #8a9a8a; }
.lab-link { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; margin: 6px 0 0; font-size: 0.76rem; color: #5a6a5a; }
.lab-link a { color: #a37a0b; font-weight: 700; text-decoration: none; }
.lab-link a:hover { text-decoration: underline; }
.m-cat { display: inline-flex; align-items: center; gap: 5px; margin: 6px 0 0; padding: 3px 9px; border-radius: 999px; font-size: 0.74rem; font-weight: 600; }
.m-cat.ok { background: #eaf5ee; color: #1f6b43; }
.m-cat.warn { background: #fdecec; color: #a12525; }
.m-cat.danger { background: #fdecea; color: #b42318; }
.computed { background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 8px 12px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 12px; }
.computed strong { font-size: 1.15rem; font-variant-numeric: tabular-nums; }
.k { font-size: 0.76rem; font-weight: 600; color: #6a7a6a; }
.c-sub { font-size: 0.74rem; color: #8a9a8a; margin: 0; }

.combo { position: relative; }
.combo-list { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; right: 0; max-height: 260px; overflow-y: auto; background: #fff; border: 1px solid #d5dad5; border-radius: 10px; box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12); padding: 6px; }
.combo-group { font-size: 0.74rem; font-weight: 600; color: #6a7a6a; margin: 6px 8px 2px; }
.combo-opt { display: block; width: 100%; text-align: left; border: none; background: none; padding: 7px 8px; border-radius: 6px; font-family: inherit; font-size: 0.84rem; color: #1a3a1a; cursor: pointer; }
.combo-opt:hover, .combo-opt.on { background: #eef3ec; }
.combo-group.linked { color: #1f6b43; }
.combo-tag { float: right; margin-left: 10px; font-size: 0.7rem; font-weight: 600; color: #8a9a8a; }
.pes-preview, .prev-box, .energy { background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 12px 14px; margin: 4px 0 14px; }
.pes-preview p, .prev-box p { margin: 4px 0 0; font-size: 0.86rem; line-height: 1.5; }
.energy { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px 16px; }
.energy div { display: flex; flex-direction: column; }
.energy strong { font-size: 1rem; }
.energy .c-sub { grid-column: 1 / -1; }
.ter-box { background: #fafbfa; border: 1px solid #d9e3dc; border-radius: 10px; padding: 12px 14px; margin: 4px 0 14px; }
.ter-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
.ter-title { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.ter-act { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; font-weight: 600; color: #4a5a4a; }
.ter-result { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.ter-result p { margin: 0; font-size: 0.86rem; color: #1a3a1a; }
.ter-result strong { font-size: 1.05rem; }
.ter-toggle {
  display: inline-flex; align-items: center; gap: 4px; border: none; background: #e3efe7; color: #0a4a37; border-radius: 8px;
  min-height: 32px; padding: 0 12px; font-family: inherit; font-size: 0.78rem; font-weight: 600; cursor: pointer;
}
.ter-toggle:hover { background: #d3e7da; }
.ter-toggle:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
@media (prefers-reduced-motion: no-preference) { .ter-toggle svg { transition: transform 0.15s; } }
.ter-toggle svg.up { transform: rotate(180deg); }
.ter-steps { margin: 10px 0 0; display: grid; gap: 4px; font-size: 0.82rem; color: #4a5a4a; }
.ter-steps div { display: grid; grid-template-columns: 70px 1fr; gap: 8px; }
.ter-steps dt { font-weight: 600; color: #1a3a1a; }
.ter-steps dd { margin: 0; }
.ter-steps strong { color: #1a3a1a; }
.ter-steps .ter-total { border-top: 1px solid #d9e3dc; padding-top: 6px; margin-top: 2px; }
.ter-field { max-width: 320px; }
.rx-outdated { margin: 8px 0 0; }
.macro-table { border: 1px solid #d9e3dc; border-radius: 10px; overflow: hidden; margin: 2px 0 6px; }
.mt-row { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 10px; align-items: center; padding: 8px 12px; border-top: 1px solid #d9e3dc; font-size: 0.84rem; color: #1a3a1a; }
.mt-row:first-child { border-top: none; }
.mt-head { background: #f7faf8; font-size: 0.74rem; font-weight: 600; color: #6a7a6a; }
.mt-name small { color: #8a9a8a; font-weight: 400; margin-left: 4px; }
.mt-pct { width: 72px; display: inline-block; }
.mt-g { font-weight: 700; }
.mt-foot { background: #f7faf8; font-weight: 700; }
.mt-foot.bad { color: #c0392b; }
.mt-err { font-size: 0.78rem; color: #c0392b; font-weight: 600; margin: 0 0 12px; }
.macro-line { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; font-size: 0.8rem; color: #4a5a4a; background: #f3f8f4; border-radius: 8px; padding: 8px 12px; margin: -2px 0 14px; }
.macro-line.warn { background: #fdf6e3; color: #7a5a00; }
.since { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 10px; }
.since div { display: flex; flex-direction: column; }
.goals { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.goal { border: 1px solid #d5dad5; background: #fff; border-radius: 8px; padding: 9px 6px; font-family: inherit; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; cursor: pointer; }
.goal.on { background: #14301a; border-color: #14301a; color: #fff; }


/* what finalizing still needs = unfinished work: white with a dashed green border, like an NCP draft */
.missing { background: #fff; border: 1.5px dashed #3f9a6b; border-radius: 10px; padding: 10px 14px; margin-bottom: 14px; font-size: 0.84rem; color: #2a3a2a; }
.missing p { display: flex; gap: 6px; align-items: center; margin: 0 0 4px; font-weight: 700; color: #1a3a1a; }
.missing ul { margin: 0; padding-left: 20px; line-height: 1.8; }
.summary { margin: 0 0 14px; }
.summary div { display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 12px; padding: 9px 0; border-top: 1px solid #f0f2f0; }
.summary div:first-child { border-top: none; }
.summary dt { font-size: 0.76rem; color: #8a9a8a; margin: 0; }
.summary dd { margin: 0; font-size: 0.86rem; line-height: 1.5; overflow-wrap: anywhere; }
.done { display: flex; align-items: center; gap: 6px; color: #1f6f46; font-weight: 600; font-size: 0.86rem; }

.strip { border-left: 1px solid #f0f2f0; background: #fbfcfb; padding: 18px 18px 24px; overflow-y: auto; }
.strip-name { font-weight: 700; margin: 0; font-size: 0.95rem; }
.allergy { display: flex; align-items: center; gap: 5px; margin: 8px 0 0; font-size: 0.78rem; font-weight: 600; color: #a12525; background: #fdecec; border-radius: 8px; padding: 6px 8px; }
.strip-k { font-size: 0.82rem; font-weight: 700; color: #1a3a1a; margin: 16px 0 6px; }
.strip-facts { margin: 10px 0 0; }
/* screening baseline card */
.baseline { margin: 16px 0 4px; padding: 12px 14px; border-radius: 10px; background: #f1f8f3; border: 1px solid #d6e8dc; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.bl-title { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.bl-sub { font-size: 0.74rem; color: #5a7a64; margin: 2px 0 10px; }
.bl-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px 12px; margin: 0; }
.bl-grid div { display: flex; flex-direction: column; min-width: 0; }
.bl-grid dt { font-size: 0.72rem; font-weight: 600; color: #4a6a54; margin: 0; }
.bl-grid dd { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #1a3a1a; margin: 0; line-height: 1.2; font-variant-numeric: tabular-nums lining-nums; }
.bl-grid small { font-size: 0.72rem; color: #5a7a64; }
.bl-grid .risk dd { color: #b23b2e; }
.bl-sym { font-size: 0.78rem; color: #3a4a3a; margin: 10px 0 0; overflow-wrap: anywhere; }
/* information boxes in the form: the light card shadow */
.computed, .energy, .pes-preview, .prev-box, .missing { box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.strip-facts div { padding: 5px 0; }
.strip-facts dt { font-size: 0.7rem; color: #8a9a8a; margin: 0; }
.strip-facts dd { margin: 0; font-size: 0.82rem; font-weight: 600; overflow-wrap: anywhere; }
.strip-facts dd small { font-weight: 500; color: #6a7a6a; }
.strip-facts dd.risk { color: #a12525; }

.ncp-foot { display: flex; justify-content: space-between; gap: 10px; padding: 12px 24px; border-top: 1px solid #d9e3dc; background: #f7faf8; flex-wrap: wrap; }
.foot-right { display: flex; gap: 8px; flex-wrap: wrap; }
.foot-right .nm-btn-outline { display: inline-flex; align-items: center; gap: 6px; }
.inner-overlay { position: absolute; inset: 0; background: rgba(20, 30, 20, 0.45); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 30; }

@media (max-width: 900px) {
  .ncp-body { grid-template-columns: minmax(0, 1fr); }
  .strip { display: none; border-left: none; border-bottom: 1px solid #f0f2f0; }
  .strip.open { display: block; grid-row: 1; }
  .strip-toggle { display: inline-flex; align-items: center; gap: 6px; border: 1px solid #d5dad5; background: #fff; border-radius: 8px; padding: 6px 10px; font-family: inherit; font-size: 0.78rem; font-weight: 600; color: #1a3a1a; cursor: pointer; margin: 0 0 12px; }
  .g4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .ncp-head, .steps, .ncp-form, .ncp-foot { padding-left: 16px; padding-right: 16px; }
  .ncp-head { padding-top: 18px; padding-bottom: 14px; }
  .ncp-title { font-size: 1.15rem; }
  .g3 { grid-template-columns: minmax(0, 1fr); }
  .goals { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .summary div { grid-template-columns: minmax(0, 1fr); gap: 2px; }
  .ncp-foot { flex-direction: column-reverse; }
  .foot-right { width: 100%; }
  .foot-right > * { flex: 1; justify-content: center; }
}
</style>
