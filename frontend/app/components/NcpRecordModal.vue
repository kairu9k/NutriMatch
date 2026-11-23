<template>
  <div :class="inline ? 'ncp-inline' : 'nm-modal-overlay ncp-overlay'" @click.self="!inline && requestClose()">
    <div class="ncp" :class="{ 'is-inline': inline }" role="dialog" :aria-modal="!inline" aria-labelledby="ncp-title">
      <!-- HEADER -->
      <header class="ncp-head">
        <img v-if="!inline" class="ncp-head-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="ncp-head-fade" aria-hidden="true"></span>
        <div class="ncp-head-top">
          <span v-if="!inline" class="ncp-av" aria-hidden="true">{{ initials }}</span>
          <div id="ncp-title" class="ncp-title-wrap">
            <p class="ncp-eyebrow"><span aria-hidden="true"></span>Nutrition Care Process</p>
            <h2 class="ncp-title"><span class="ncp-kind" :class="{ follow: isFollowUp }">{{ isFollowUp ? 'Follow-up record' : 'Initial record' }}</span><em v-if="patientName"> · {{ patientName }}</em></h2>
            <p class="ncp-sub">
              <span>{{ subtitleText }}</span>
              <template v-if="isFinalized"><i aria-hidden="true"></i><span class="ncp-final"><Lock :size="12" /> Finalized {{ dateTime(record.updated_at) }}</span></template>
            </p>
          </div>
          <div class="ncp-head-right">
            <span v-if="!isReadOnly" class="save-state" :class="saveStateClass">{{ saveStateText }}</span>
            <button v-if="!inline" type="button" class="icon-x" aria-label="Close" @click="requestClose"><X :size="18" /></button>
          </div>
        </div>

        <!-- STEPS -->
        <nav v-if="!isLoading && !loadError" class="steps" aria-label="NCP steps">
          <template v-for="(st, i) in steps" :key="st">
            <button type="button" class="step" :class="[stepState(i), { active: tab === i, err: stepHasError(i) }]" :aria-current="tab === i ? 'step' : undefined" @click="tab = i">
              <span class="step-dot"><Check v-if="stepState(i) === 'done'" :size="14" /><template v-else>{{ i + 1 }}</template></span>
              <span class="step-txt"><span class="step-name">{{ st }}</span><small class="step-sub">{{ STEP_SUB[st] }}</small></span>
            </button>
            <span v-if="i < steps.length - 1" class="step-line" :class="{ done: stepState(i) === 'done' }" aria-hidden="true"></span>
          </template>
        </nav>
      </header>

      <div v-if="isLoading" class="ncp-loading pad"><span class="ncp-spin" aria-hidden="true"></span> Loading…</div>
      <p v-else-if="loadError" class="nm-error pad">{{ loadError }}</p>

      <template v-else>
        <div class="ncp-body">
          <div class="ncp-form">
            <p v-if="!isFinalized && isReadOnly" class="banner"><Lock :size="15" /> Viewing an unfinished record. It's read-only here.</p>
            <p v-if="saveError" class="nm-error">{{ saveError }}</p>

            <button v-if="!inline" type="button" class="strip-toggle" @click="stripOpen = !stripOpen">
              <Info :size="14" /> {{ stripOpen ? 'Hide' : 'Show' }} patient info
            </button>

            <!-- ASSESSMENT -->
            <section v-if="stepKey === 'assessment'" class="step-sec" :class="{ 'ms-locked': measuresLocked && !isReadOnly }">
              <header class="step-head"><span class="step-num" aria-hidden="true">{{ stepNum }}</span><div><h3 class="step-title">Nutrition assessment</h3><p class="step-desc">Where the patient is today: measurements, labs and how they eat.</p></div></header>
              <p v-if="prefilled && !isReadOnly" class="hint-box"><Info :size="14" /> Measurements are filled in from their latest records. Check them with the patient, then press Edit measurements to change what changed.</p>
              <!-- Measurements are locked until Edit (user's call, 2026-11-02): an accidental
                   change can't slip in, and every changed value shows what it was. -->
              <div class="card">
              <div class="card-head">
                <span class="card-ico ico-green"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17L17 3l4 4L7 21z" /><path d="M7 13l2 2M10 10l2 2M13 7l2 2" /></svg></span>
                <div class="card-head-txt"><p class="ms-title">Measurements</p><p class="card-sub">Body size, blood pressure and blood sugar</p></div>
                <div v-if="!isReadOnly" class="ms-bar">
                  <button v-if="measuresLocked" type="button" class="nm-btn-soft nm-btn-sm" @click="measuresLocked = false"><PenLine :size="14" aria-hidden="true" /> Edit measurements</button>
                  <template v-else-if="hasOriginals">
                    <button type="button" class="nm-btn-soft nm-btn-sm" @click="cancelMeasureEdits">{{ changedMeasures.length ? 'Cancel changes' : 'Cancel' }}</button>
                    <button type="button" class="nm-btn-dark nm-btn-sm" @click="measuresLocked = true"><Check :size="14" aria-hidden="true" /> Done</button>
                  </template>
                </div>
              </div>
              <div class="grid g3">
                <Field label="Height (cm)" required :hint="srcHint('height_cm')" :error="errors.height_cm">
                  <input v-model="a.height_cm" type="number" :min="L.height_cm.min" :max="L.height_cm.max" step="0.1" class="nm-input" :disabled="isReadOnly || measuresLocked" />
                  <p v-if="changed('height_cm')" class="was">Was {{ wasText('height_cm', 'cm') }}. <button type="button" class="nm-btn-soft nm-btn-sm" @click="putBack('height_cm')">Put back</button></p>
                </Field>
                <Field label="Weight (kg)" required :hint="srcHint('weight_kg')" :error="errors.weight_kg">
                  <input v-model="a.weight_kg" type="number" :min="L.weight_kg.min" :max="L.weight_kg.max" step="0.1" class="nm-input" :disabled="isReadOnly || measuresLocked" />
                  <p v-if="changed('weight_kg')" class="was">Was {{ wasText('weight_kg', 'kg') }}. <button type="button" class="nm-btn-soft nm-btn-sm" @click="putBack('weight_kg')">Put back</button></p>
                </Field>
                <div class="computed" :class="liveBmi ? 'bmi-' + bmiTone(liveBmi) : ''">
                  <div class="bmi-top"><span class="k">BMI, WHO Asia-Pacific</span><span v-if="liveBmi" class="bmi-chip">{{ bmiClass(liveBmi) }}</span></div>
                  <strong>{{ liveBmi != null ? liveBmi.toFixed(1) : '—' }}</strong>
                  <template v-if="liveBmi">
                    <div class="bmi-scale" aria-hidden="true"><span></span><span></span><span></span><span></span><i :style="{ left: bmiPos(liveBmi) + '%' }"></i></div>
                    <div class="bmi-lbl" aria-hidden="true"><span>&lt;18.5</span><span>18.5–22.9</span><span>23–24.9</span><span>≥25</span></div>
                  </template>
                  <span v-else class="c-sub">{{ (errors.weight_kg || errors.height_cm) ? 'Check height and weight' : 'Enter height and weight' }}</span>
                  <span v-if="liveBmi && isShortStature(a.height_cm)" class="c-sub">{{ BMI_SHORT_STATURE_NOTE }}</span>
                </div>
              </div>
              <div class="grid g3">
                <Field label="Blood pressure (mmHg)" group :hint="srcHint('blood_pressure')" :error="errors.blood_pressure">
                  <div class="bp">
                    <input v-model="a.bp_systolic" type="number" :min="L.bp_systolic.min" :max="L.bp_systolic.max" class="nm-input" placeholder="120" aria-label="Systolic" :disabled="isReadOnly || measuresLocked" />
                    <span>/</span>
                    <input v-model="a.bp_diastolic" type="number" :min="L.bp_diastolic.min" :max="L.bp_diastolic.max" class="nm-input" placeholder="80" aria-label="Diastolic" :disabled="isReadOnly || measuresLocked" />
                  </div>
                  <p v-if="changed('bp_systolic') || changed('bp_diastolic')" class="was">Was {{ bpWasText }}. <button type="button" class="nm-btn-soft nm-btn-sm" @click="putBack('bp_systolic'); putBack('bp_diastolic')">Put back</button></p>
                  <p v-if="liveBp" class="m-cat" :class="liveBp.level" role="status" title="WHO / ESH grading">
                    <AlertTriangle v-if="liveBp.level !== 'ok'" :size="13" /> {{ liveBp.label }}
                  </p>
                </Field>
                <Field label="Fasting glucose (mg/dL)" info="Blood sugar after at least 8 hours without food." :hint="srcHint('blood_glucose')" :error="errors.blood_glucose">
                  <input v-model="a.blood_glucose" type="number" :min="L.blood_glucose.min" :max="L.blood_glucose.max" step="1" class="nm-input" :disabled="isReadOnly || measuresLocked" />
                  <p v-if="changed('blood_glucose')" class="was">Was {{ wasText('blood_glucose', 'mg/dL') }}. <button type="button" class="nm-btn-soft nm-btn-sm" @click="putBack('blood_glucose')">Put back</button></p>
                  <p v-if="liveGlucose" class="m-cat" :class="liveGlucose.level" role="status">
                    <AlertTriangle v-if="liveGlucose.level !== 'ok'" :size="13" /> {{ liveGlucose.label }}
                  </p>
                </Field>
                <Field label="HbA1c (%)" :info="'Average blood sugar over the past 2⁠–⁠3 months.' /* word joiners keep 2–3 on one line */" :hint="srcHint('hba1c')" :error="errors.hba1c">
                  <input v-model="a.hba1c" type="number" :min="L.hba1c.min" :max="L.hba1c.max" step="0.1" class="nm-input" :disabled="isReadOnly || measuresLocked" />
                  <p v-if="changed('hba1c')" class="was">Was {{ wasText('hba1c', '%') }}. <button type="button" class="nm-btn-soft nm-btn-sm" @click="putBack('hba1c')">Put back</button></p>
                  <p v-if="liveHba1c" class="m-cat" :class="liveHba1c.level" role="status">
                    <AlertTriangle v-if="liveHba1c.level !== 'ok'" :size="13" /> {{ liveHba1c.label }}
                  </p>
                </Field>
              </div>
              </div>
              <div class="card">
              <div class="card-head">
                <span class="card-ico ico-red"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6M10 3v6L4.5 18.5A2 2 0 0 0 6.2 21.5h11.6a2 2 0 0 0 1.7-3L14 9V3" /><path d="M7 15h10" /></svg></span>
                <div class="card-head-txt"><p class="ms-title">Labs and notes</p><p class="card-sub">Other measurements, lab results and how they eat</p></div>
              </div>
              <NcpExtraRows :rows="a.extra" :templates="MEASURE_TEMPLATES.assessment" :read-only="isReadOnly" empty="Add waist circumference, cholesterol, creatinine and more. Pick from the list or type your own." />
              <Field label="Lab notes">
                <textarea v-model="a.lab_notes" data-allow-emoji class="nm-input" :maxlength="TMAX.lab_notes" rows="2" placeholder="e.g. Lipid profile from Oct 2: LDL 160 mg/dL" :disabled="isReadOnly"></textarea>
                <p v-if="ctx.labs?.total_results && !isReadOnly" class="lab-link">
                  <FlaskConical :size="13" /> {{ ctx.labs.total_results }} lab result{{ ctx.labs.total_results === 1 ? '' : 's' }} uploaded<template v-if="ctx.labs.new_results"> ({{ ctx.labs.new_results }} new)</template>.
                  <button type="button" class="nm-text-link" @click="showLabs = true">View lab results</button>
                </p>
              </Field>
              <Field label="Assessment notes">
                <textarea v-model="a.assessment_notes" data-allow-emoji class="nm-input" :maxlength="TMAX.assessment_notes" rows="3" placeholder="Appetite, eating pattern, activity, food access…" :disabled="isReadOnly"></textarea>
              </Field>
              </div>
            </section>

            <!-- DIAGNOSIS -->
            <section v-else-if="stepKey === 'diagnosis'" class="step-sec">
              <header class="step-head"><span class="step-num" aria-hidden="true">{{ stepNum }}</span><div><h3 class="step-title">Nutrition diagnosis</h3><p class="step-desc">Name the nutrition problem as a PES statement: the problem, its cause and the signs that show it.</p></div></header>
              <p v-if="carried && !isReadOnly" class="hint-box"><Info :size="14" /> Carried over from the {{ shortDate(ctx.previous.encounter_date) }} record. Edit what changed.</p>
              <div class="pes-card pes-p">
                <span class="pes-l" aria-hidden="true">P</span>
                <div class="pes-b">
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
                </div>
              </div>
              <div class="pes-card pes-e">
                <span class="pes-l" aria-hidden="true">E</span>
                <div class="pes-b">
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
                </div>
              </div>
              <div class="pes-card pes-s">
                <span class="pes-l" aria-hidden="true">S</span>
                <div class="pes-b">
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
                </div>
              </div>
              <div class="pes-preview">
                <div class="pes-preview-h"><span class="pes-preview-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3v6a4 4 0 0 0 8 0V3" /><path d="M10 13v3a5 5 0 0 0 10 0v-2" /><circle cx="20" cy="12" r="2" /></svg></span><span class="k">PES statement</span><small>How it reads in the record</small></div>
                <p>{{ pesSentence }}</p>
              </div>
            </section>

            <!-- INTERVENTION -->
            <section v-else-if="stepKey === 'intervention'" class="step-sec">
              <header class="step-head"><span class="step-num" aria-hidden="true">{{ stepNum }}</span><div><h3 class="step-title">Nutrition intervention</h3><p class="step-desc">What you prescribe: the energy and macro targets, and the diet itself.</p></div></header>
              <p v-if="carried && !isReadOnly" class="hint-box"><Info :size="14" /> Targets carried over from the {{ shortDate(ctx.previous.encounter_date) }} record. Adjust them as needed.</p>
              <!-- TER, Tannhauser's factorial method on a BMR from the BMI-method DBW (utils/ncp.js terSteps) -->
              <div class="ter-box card">
              <div class="card-head">
                <span class="card-ico ico-gold"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22a7 7 0 0 0 7-7c0-4-3-6-4-9-1 2-2 3-4 3 0-2-1-4-2-6-1 4-4 7-4 12a7 7 0 0 0 7 7z" /></svg></span>
                <div class="card-head-txt"><p class="ter-title">Total Energy Requirement</p><p class="card-sub">BMR by the BMI method</p></div>
              </div>
                <div class="ter-grid">
                  <!-- The result only; the working opens on request (user's call, 2026-11-01) -->
                  <div v-if="terCalc" class="ter-big">
                    <small>Calculated TER</small>
                    <strong>{{ whole(terCalc.ter) }}</strong>
                    <em>kcal/day</em>
                  </div>
                  <div class="ter-side">
                    <label class="ter-act">
                      <span>Activity</span>
                      <select v-model="i.ter_activity" class="nm-select" :disabled="isReadOnly" aria-label="Physical activity level">
                        <option v-for="a2 in TER_ACTIVITY" :key="a2.value" :value="a2.value">{{ a2.label }} (+{{ a2.pct }}% of BMR)</option>
                      </select>
                    </label>
                    <button v-if="terCalc" type="button" class="ter-toggle" :aria-expanded="terShowSteps" aria-controls="ter-steps" @click="terShowSteps = !terShowSteps">
                      {{ terShowSteps ? 'Hide calculation' : 'Show calculation' }} <ChevronDown :size="14" :class="{ up: terShowSteps }" aria-hidden="true" />
                    </button>
                  </div>
                </div>
                <dl v-if="terCalc && terShowSteps" id="ter-steps" class="ter-steps">
                  <div><dt>DBW</dt><dd>{{ terCalc.heightM.toFixed(2) }}² × 22 = <strong>{{ fmt(terCalc.dbw, 1) }} kg</strong></dd></div>
                  <div><dt>BMR</dt><dd>{{ fmt(terCalc.dbw, 1) }} × {{ terCalc.perHour.toFixed(1) }} × 24 = <strong>{{ whole(terCalc.bmr) }} kcal</strong></dd></div>
                  <div><dt>Activity</dt><dd>{{ terCalc.act.label }}, {{ terCalc.act.pct }}% of BMR = <strong>{{ whole(terCalc.pa) }} kcal</strong></dd></div>
                  <div><dt>TEF</dt><dd>10% of (BMR + activity) = <strong>{{ whole(terCalc.tef) }} kcal</strong></dd></div>
                  <div class="ter-total"><dt>TER</dt><dd>{{ whole(terCalc.exact) }}, to the nearest 50 = <strong>{{ whole(terCalc.ter) }} kcal</strong></dd></div>
                </dl>
                <p v-if="terCalc?.shortStature" class="nm-note plain-note">{{ SHORT_STATURE_NOTE }}</p>
                <p v-if="!terCalc" class="c-sub">{{ ctx.patient?.sex ? 'Enter the height in Assessment to work out the TER.' : 'The patient\'s sex isn\'t on file, so the TER can\'t be worked out. Type it below.' }}</p>
              </div>
              <div class="card">
              <div class="card-head">
                <span class="card-ico ico-green"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12A9 9 0 1 1 12 3v9z" /><path d="M15 3.5A9 9 0 0 1 20.5 9H15z" /></svg></span>
                <div class="card-head-txt"><p class="ms-title">Energy and macro targets</p><p class="card-sub">The TER to prescribe and how it splits</p></div>
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
              <!-- Minimize (user's call, 2026-11-02): one line with the split and grams; it opens by itself on an error -->
              <div class="mt-bar">
                <p class="mt-bar-title">Macronutrients <span>{{ macroSplitText }}</span></p>
                <button type="button" class="nm-btn-soft nm-btn-sm" :aria-expanded="macrosOpen" aria-controls="ncp-macro-table" @click="toggleMacros">
                  <ChevronDown :size="14" class="mt-chev" :class="{ up: macrosOpen }" aria-hidden="true" /> {{ macrosOpen ? 'Minimize' : 'Show' }}
                </button>
              </div>
                <div v-if="pctTotal > 0" class="mt-split" aria-hidden="true">
                  <span v-for="m2 in MACROS" :key="m2.key" :class="'sp-' + m2.key" :style="{ flexGrow: Number(i[`${m2.key}_pct`]) || 0 }">{{ Number(i[`${m2.key}_pct`]) ? `${i[`${m2.key}_pct`]}%` : '' }}</span>
                </div>
              <p v-if="!macrosOpen" class="mt-summary">{{ macroGramsText }}</p>
              <div v-show="macrosOpen" id="ncp-macro-table" class="macro-table" role="group" aria-label="Macronutrient distribution">
                <div class="mt-row mt-head"><span>Macronutrient</span><span>% of TER</span><span>Grams a day</span></div>
                <div v-for="m2 in MACROS" :key="m2.key" class="mt-row">
                  <span class="mt-name"><span class="mt-dot" :class="'sp-' + m2.key" aria-hidden="true"></span>{{ m2.label }} <small>{{ m2.per }} kcal/g</small></span>
                  <span><input v-model.number="i[`${m2.key}_pct`]" type="number" min="0" max="100" step="1" class="nm-input mt-pct" :disabled="isReadOnly" :aria-label="`${m2.label} percent of TER`" /> %</span>
                  <span class="mt-g">{{ i[`target_${m2.key}_g`] !== '' && i[`target_${m2.key}_g`] != null ? `${whole(i[`target_${m2.key}_g`])} g` : '—' }}</span>
                </div>
                <div class="mt-row mt-foot" :class="{ bad: errors.macro_pct }"><span>Total</span><span>{{ pctTotal }}%</span><span></span></div>
              </div>
              <p v-if="errors.macro_pct" class="mt-err" role="alert">{{ errors.macro_pct }}</p>
              <p v-else-if="!isReadOnly && macrosOpen" class="c-sub">Starts at 55 / 20 / 25. Grams are TER × % ÷ 4 kcal/g (carbs, protein) or ÷ 9 kcal/g (fat), to the nearest 5 g.</p>
              </div>
              <div class="card">
              <div class="card-head">
                <span class="card-ico ico-blue"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 21c0-9 6-15 15-16-1 9-7 15-15 16z" /><path d="M5 21l8-8" /></svg></span>
                <div class="card-head-txt"><p class="ms-title">Diet prescription</p><p class="card-sub">Other targets, the diet itself and notes</p></div>
              </div>
              <NcpExtraRows :rows="i.extra" :templates="MEASURE_TEMPLATES.intervention" title="Other targets" item="Target" :read-only="isReadOnly" empty="Add a sodium limit, fluid limit, fiber goal, activity and more. Pick from the list or type your own." />
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
              </div>
            </section>

            <!-- MONITORING (follow-ups) -->
            <section v-else-if="stepKey === 'monitoring'" class="step-sec">
              <header class="step-head"><span class="step-num" aria-hidden="true">{{ stepNum }}</span><div><h3 class="step-title">Monitoring and evaluation</h3><p class="step-desc">How the patient did against the goals from their last record.</p></div></header>
              <div v-if="ctx.previous" class="prev-box">
                <div class="prev-h"><span class="card-ico ico-gold"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg></span><span class="k">Goals from the {{ shortDate(ctx.previous.encounter_date) }} record</span></div>
                <p v-if="ctx.previous.pes_problem"><strong>{{ ctx.previous.pes_problem }}</strong><template v-if="ctx.previous.pes_etiology"> related to {{ ctx.previous.pes_etiology }}</template>.</p>
                <p v-if="ctx.previous.diet_prescription">{{ ctx.previous.diet_prescription }}</p>
                <p v-if="ctx.previous.target_kcal" class="c-sub">TER {{ whole(ctx.previous.target_kcal) }} kcal/day</p>
                <div class="since">
                  <div><span class="k">Weight since then</span><strong>{{ weightSince != null ? `${signed(weightSince)} kg` : 'Not measured' }}</strong></div>
                  <div><span class="k">7-day meal-plan adherence</span><strong>{{ ctx.adherence?.pct != null ? `${ctx.adherence.pct}%` : 'No meal plan yet' }}</strong></div>
                </div>
              </div>
              <div class="card">
              <Field label="Were those goals met?" required group>
                <div class="goals">
                  <button v-for="g in GOALS" :key="g.value" type="button" class="goal" :class="{ on: m.goal_status === g.value }" :disabled="isReadOnly" @click="m.goal_status = g.value">{{ g.label }}</button>
                </div>
              </Field>
              <Field label="Monitoring notes">
                <textarea v-model="m.monitoring_notes" data-allow-emoji class="nm-input" :maxlength="TMAX.monitoring_notes" rows="3" placeholder="Response to the plan, barriers, what to change next…" :disabled="isReadOnly"></textarea>
              </Field>
              </div>
            </section>

            <!-- REVIEW -->
            <section v-else-if="stepKey === 'review'" class="step-sec">
              <header class="step-head"><span class="step-num" aria-hidden="true">{{ stepNum }}</span><div><h3 class="step-title">{{ isReadOnly ? 'Summary' : 'Review and finalize' }}</h3><p class="step-desc">{{ isReadOnly ? 'The record as it was saved.' : 'Check the record before you finalize it. A finalized record can\'t be changed.' }}</p></div></header>
              <div v-if="!isReadOnly && missing.length" class="missing">
                <p><AlertTriangle :size="15" /> Still needed before you can finalize:</p>
                <ul><li v-for="x in missing" :key="x.label">{{ x.label }} <button type="button" class="nm-panel-link" @click="tab = x.step">Fix</button></li></ul>
              </div>
              <div v-if="isFinalized" class="done-card">
                <span class="done-ico"><CheckCircle2 :size="22" /></span>
                <div class="done-txt"><p class="done">This record is finalized.</p><p class="done-sub">Part of the patient's permanent record.</p></div>
                <NuxtLink v-if="!inline" :to="`/meal-planning?relationship=${relationshipId}&edit=1`" class="nm-btn-dark nm-btn-sm done-link" @click="emit('close')"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" /></svg> Create or update the meal plan</NuxtLink>
              </div>
              <p v-else-if="!isReadOnly && !missing.length" class="nm-hint ready-hint"><CheckCircle2 :size="16" /> Everything required is filled in. Finalizing makes this record permanent, so it can't be edited afterwards.</p>
              <dl class="summary">
                <div><dt><span class="sum-ico ico-green"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="3" /><path d="M8 9a4 4 0 0 1 8 0" /><path d="M12 9l1.5-2" /></svg></span>Measurements</dt><dd>{{ measureLine }}</dd></div>
                <div v-if="assessExtraLine"><dt><span class="sum-ico ico-red"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6M10 3v6L4.5 18.5A2 2 0 0 0 6.2 21.5h11.6a2 2 0 0 0 1.7-3L14 9V3" /><path d="M7 15h10" /></svg></span>Other measurements</dt><dd>{{ assessExtraLine }}</dd></div>
                <div><dt><span class="sum-ico ico-red"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 3v6a4 4 0 0 0 8 0V3" /><path d="M10 13v3a5 5 0 0 0 10 0v-2" /><circle cx="20" cy="12" r="2" /></svg></span>Diagnosis</dt><dd :class="{ empty: !d.pes_problem }">{{ d.pes_problem ? pesSentence : 'Not filled in' }}</dd></div>
                <div><dt><span class="sum-ico ico-gold"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22a7 7 0 0 0 7-7c0-4-3-6-4-9-1 2-2 3-4 3 0-2-1-4-2-6-1 4-4 7-4 12a7 7 0 0 0 7 7z" /></svg></span>Prescription</dt><dd :class="{ empty: !i.diet_prescription }">{{ i.diet_prescription || 'Not filled in' }}</dd></div>
                <div v-if="interventionExtraLine"><dt><span class="sum-ico ico-blue"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg></span>Other targets</dt><dd>{{ interventionExtraLine }}</dd></div>
                <div v-if="showMonitoring"><dt><span class="sum-ico ico-green"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8" /><path d="M14 7h7v7" /></svg></span>Goal status</dt><dd :class="{ empty: !m.goal_status }">{{ GOALS.find(g => g.value === m.goal_status)?.label || 'Not rated' }}</dd></div>
              </dl>
            </section>
          </div>

          <!-- PATIENT STRIP -->
          <aside v-if="!inline || showStripInline" class="strip" :class="{ open: stripOpen }">
            <div class="strip-pt">
              <span class="strip-av" aria-hidden="true">{{ initials }}</span>
              <div>
                <p class="strip-name">{{ ctx.patient?.name }}</p>
                <p class="c-sub">{{ [ctx.patient?.age != null ? `${ctx.patient.age} y/o` : null, SEX[ctx.patient?.sex]].filter(Boolean).join(', ') }}</p>
              </div>
            </div>
            <p v-if="ctx.patient?.allergies.length" class="allergy"><AlertTriangle :size="15" /> <span><b>Allergy:</b> {{ ctx.patient.allergies.join(', ') }}</span></p>
            <dl class="strip-facts">
              <div><dt><span class="fact-ico ico-red"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.8 5.6a5 5 0 0 0-7.1 0L12 7.3l-1.7-1.7a5 5 0 0 0-7.1 7.1L12 21.5l8.8-8.8a5 5 0 0 0 0-7.1z" /></svg></span>Conditions</dt><dd>{{ list(ctx.patient?.conditions) }}</dd></div>
              <div><dt><span class="fact-ico ico-green"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 21c0-9 6-15 15-16-1 9-7 15-15 16z" /><path d="M5 21l8-8" /></svg></span>Diet</dt><dd>{{ list(ctx.patient?.dietary_restrictions) }}</dd></div>
              <div v-if="ctx.patient?.religion"><dt><span class="fact-ico ico-purple"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v18M7 8h10" /></svg></span>Religion</dt><dd>{{ ctx.patient.religion }}</dd></div>
              <div><dt><span class="fact-ico ico-gold"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg></span>Goals</dt><dd>{{ list(ctx.patient?.health_goals) }}</dd></div>
            </dl>
            <!-- the screening is the baseline progress is measured from, so it stands out -->
            <section v-if="ctx.screening" class="baseline" aria-label="Screening baseline">
              <div class="bl-head">
                <span class="bl-ico"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6M9 17.5h3" /></svg></span>
                <div>
                  <p class="bl-title">Screening baseline</p>
                  <p class="bl-sub">{{ shortDate(ctx.screening.date) }}. The starting point progress is measured from.</p>
                </div>
              </div>
              <dl class="bl-grid">
                <div><dt>BMI</dt><dd>{{ ctx.screening.bmi != null ? Number(ctx.screening.bmi).toFixed(1) : '—' }}</dd><small>{{ ctx.screening.bmi_category }}</small></div>
                <div :class="{ risk: (ctx.screening.nrs_score ?? 0) >= 3 }"><dt>NRS-2002</dt><dd>{{ ctx.screening.nrs_score ?? '—' }}</dd><small>{{ ctx.screening.nrs_risk }}</small></div>
                <div><dt>TER</dt><dd>{{ whole(ctx.screening.tdee_kcal) }}</dd><small>kcal/day</small></div>
                <div><dt>BMR</dt><dd>{{ whole(ctx.screening.bmr_kcal) }}</dd><small>kcal/day</small></div>
              </dl>
              <p v-if="ctx.screening.bmr_note" class="bl-sym">{{ ctx.screening.bmr_note }}</p>
              <template v-if="ctx.screening.symptoms">
                <p class="bl-sym"><strong>Symptoms</strong></p>
                <div class="bl-tags"><em v-for="sym in symptomTags" :key="sym">{{ sym }}</em></div>
              </template>
            </section>
            <div v-if="ctx.meal_plan" class="strip-card gold">
              <span class="strip-card-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" /></svg></span>
              <div>
                <p class="strip-k">Current meal plan</p>
                <p class="c-sub">{{ ctx.meal_plan.name }}{{ ctx.meal_plan.target_kcal ? `, ${whole(ctx.meal_plan.target_kcal)} kcal` : '' }}</p>
              </div>
            </div>
            <div v-if="ctx.adherence" class="strip-card">
              <span class="strip-card-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8" /><path d="M14 7h7v7" /></svg></span>
              <div>
                <p class="strip-k">7-day adherence</p>
                <p class="c-sub">{{ ctx.adherence.pct != null ? `${ctx.adherence.pct}%, ${ctx.adherence.logged} of ${ctx.adherence.planned} meals logged` : 'Nothing due yet' }}</p>
              </div>
            </div>
          </aside>
        </div>

        <!-- FOOTER -->
        <footer class="ncp-foot">
          <p v-if="!isReadOnly && errorCount" class="foot-err" role="status"><AlertTriangle :size="14" /> Fix {{ errorCount }} highlighted field{{ errorCount === 1 ? '' : 's' }} before saving.</p>
          <button type="button" class="nm-btn-outline" :disabled="tab === 0" @click="tab--">Back</button>
          <div class="foot-mid" aria-hidden="true">
            <span v-if="isFinalized" class="foot-lock"><Lock :size="13" /> Part of the patient's permanent record</span>
            <span class="foot-step"><b>Step {{ tab + 1 }}</b> of {{ steps.length }}</span>
            <span class="foot-dots"><i v-for="(st, n) in steps" :key="st" :class="{ on: n === tab, done: n < tab }"></i></span>
          </div>
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

      <!-- LAB RESULTS: over the form, so nothing typed is lost (files open
           in their own pop-up from here, never a new tab) -->
      <div v-if="showLabs" class="inner-overlay" @click.self="showLabs = false">
        <div class="nm-modal labs-modal" role="dialog" aria-labelledby="labs-title">
          <button type="button" class="nm-modal-x" aria-label="Close" @click="showLabs = false"><X :size="18" aria-hidden="true" /></button>
          <h3 id="labs-title" class="nm-modal-title">Lab results</h3>
          <RndLabsTab :relationship-id="relationshipId" :patient-first-name="patientName.split(' ')[0]" />
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-soft" @click="showLabs = false">Back to the record</button>
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
</template><script setup>
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
import { AlertTriangle, Check, CheckCircle2, ChevronDown, FlaskConical, Info, Lock, PenLine, Save, X } from 'lucide-vue-next'
import {
  DEFAULT_MACRO_PCT, KCAL_PER_G, MEASURE_TEMPLATES, NCP_LIMITS as L, NCP_TEXT_MAX as TMAX, PES_TERMS, TER_ACTIVITY, bmiClass, bmiOf, bpCategory, extraRowErrors,
  glucoseCategory, hba1cCategory, macroGrams, rangeError, terSteps, SHORT_STATURE_NOTE, BMI_SHORT_STATURE_NOTE, isShortStature,
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
const showLabs = ref(false)
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

// "168.00" from the API reads as 168
const plainNum = v => (v == null || v === '' ? '' : Number(v))
function hydrate(r = {}) {
  const [sys, dia] = (r.blood_pressure || '').split('/')
  a.value = {
    height_cm: plainNum(r.height_cm), weight_kg: plainNum(r.weight_kg), bp_systolic: sys || '', bp_diastolic: dia || '',
    blood_glucose: plainNum(r.blood_glucose), hba1c: plainNum(r.hba1c), lab_notes: r.lab_notes ?? '', assessment_notes: r.assessment_notes ?? '',
    extra: (r.assessment_extra || []).map(x => ({ ...x })),
  }
  d.value = { pes_problem: r.pes_problem ?? '', pes_etiology: r.pes_etiology ?? '', pes_signs: r.pes_signs ?? '' }
  i.value = {
    target_kcal: r.target_kcal != null && r.target_kcal !== '' ? Number(r.target_kcal) : '', target_carb_g: r.target_carb_g ?? '', target_protein_g: r.target_protein_g ?? '',
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
    if (pf[f] && blank(a.value[f])) { a.value[f] = plainNum(pf[f].value); prefilledFields.value.push(f) }
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
/* ---------- measurements: locked until Edit, with the original values kept ---------- */
const MEASURE_KEYS = ['height_cm', 'weight_kg', 'bp_systolic', 'bp_diastolic', 'blood_glucose', 'hba1c']
const originals = ref({})
const measuresLocked = ref(false)
const hasOriginals = computed(() => MEASURE_KEYS.some(k => String(originals.value[k] ?? '').trim() !== ''))
// called once the form is filled (saved draft + pre-filled values)
function rememberMeasures() {
  originals.value = Object.fromEntries(MEASURE_KEYS.map(k => [k, a.value[k] ?? '']))
  measuresLocked.value = hasOriginals.value // nothing on file yet: type straight away
}
const sameValue = (x, y) => {
  const sx = String(x ?? '').trim(), sy = String(y ?? '').trim()
  return sx === sy || (sx !== '' && sy !== '' && Number(sx) === Number(sy))
}
function changed(k) {
  return hasOriginals.value && !isReadOnly.value && !sameValue(a.value[k], originals.value[k])
}
const changedMeasures = computed(() => MEASURE_KEYS.filter(changed))
function wasText(k, unit) {
  const v = String(originals.value[k] ?? '').trim()
  return v === '' ? 'empty' : `${Number(v)} ${unit}`
}
const bpWasText = computed(() => {
  const s = String(originals.value.bp_systolic ?? '').trim(), dd = String(originals.value.bp_diastolic ?? '').trim()
  return s || dd ? `${s || '?'}/${dd || '?'} mmHg` : 'empty'
})
function putBack(k) { a.value[k] = originals.value[k] ?? '' }
function cancelMeasureEdits() {
  MEASURE_KEYS.forEach(putBack)
  measuresLocked.value = true
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
// Change since the previous record, from the weight typed in this record (the
// server's value only knows the last saved weight).
const weightSince = computed(() => {
  const prev = ctx.value?.previous
  if (!prev) return null
  const w = Number(a.value.weight_kg)
  if (filled(a.value.weight_kg) && !rangeError('weight_kg', a.value.weight_kg) && prev.weight_kg != null) return Math.round((w - Number(prev.weight_kg)) * 10) / 10
  return prev.weight_change_kg
})
const liveBmi = computed(() =>(rangeError('weight_kg', a.value.weight_kg) || rangeError('height_cm', a.value.height_cm) ? null : bmiOf(a.value.weight_kg, a.value.height_cm)))
/* ---------- TER and macro distribution (utils/ncp.js) ---------- */
const MACROS = [
  { key: 'carb', label: 'Carbohydrate', per: KCAL_PER_G.carb },
  { key: 'protein', label: 'Protein', per: KCAL_PER_G.protein },
  { key: 'fat', label: 'Fat', per: KCAL_PER_G.fat },
]
const terCalc = computed(() => (rangeError('height_cm', a.value.height_cm) ? null : terSteps(a.value.height_cm, ctx.value.patient?.sex, i.value.ter_activity)))
const terShowSteps = ref(false)
const pctTotal = computed(() => MACROS.reduce((s, m2) => s + (Number(i.value[`${m2.key}_pct`]) || 0), 0))
// The macro table can be minimized to one line; the choice is remembered on this device.
const MACROS_KEY = 'nm-ncp-macros-open'
const macrosOpen = ref(true)
onMounted(() => { try { macrosOpen.value = localStorage.getItem(MACROS_KEY) !== '0' } catch { /* storage blocked */ } })
function toggleMacros() {
  macrosOpen.value = !macrosOpen.value
  try { localStorage.setItem(MACROS_KEY, macrosOpen.value ? '1' : '0') } catch { /* storage blocked */ }
}
const macroSplitText = computed(() => MACROS.map(m2 => i.value[`${m2.key}_pct`] || 0).join(' / '))
const macroGramsText = computed(() => {
  const gram = k => (i.value[`target_${k}_g`] !== '' && i.value[`target_${k}_g`] != null ? `${whole(i.value[`target_${k}_g`])} g` : '—')
  return `Carbohydrate ${gram('carb')}, protein ${gram('protein')}, fat ${gram('fat')} a day.`
})
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
// The TER box follows the calculated TER until the RND types their own. Compare
// with the last VALID calculated value: while a height is being typed ("1",
// "16", "165") it's briefly invalid and the TER blank, which used to make the
// box stop following (2026-11-02 test-run fix).
let lastTer = null
watch(() => terCalc.value?.ter, (now) => {
  if (!now) return
  const before = lastTer
  lastTer = now
  if (isReadOnly.value) return
  if (String(i.value.target_kcal ?? '').trim() === '' || Number(i.value.target_kcal) === before) i.value.target_kcal = now
}, { immediate: true })
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
  if (rowsBad(i.value.extra)) e.intervention_extra = 'Fix the other targets.'
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
  liveBmi.value ? `BMI ${liveBmi.value.toFixed(1)} (${bmiClass(liveBmi.value)})` : null,
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
      rememberMeasures()
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
// A split that doesn't add up to 100 opens the minimized macro table again.
watch(() => errors.value.macro_pct, (bad) => { if (bad) macrosOpen.value = true })
const whole = v => (v == null || v === '' ? '—' : Math.round(Number(v)).toLocaleString('en-PH'))
const signed = v => `${Number(v) > 0 ? '+' : Number(v) < 0 ? '−' : ''}${Math.abs(Number(v)).toFixed(1)}`
function ncpError(e, fallback) {
  const data = e?.data || {}
  if (data.detail) return Array.isArray(data.detail) ? data.detail[0] : data.detail
  const first = Object.entries(data).find(([, v]) => Array.isArray(v) && typeof v[0] === 'string')
  return first ? `${first[0].replace(/_/g, ' ')}: ${first[1][0]}` : fallback
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// first and last name, e.g. Ivy Hope Alba → IA
const initials = computed(() => {
  const w = (props.patientName || ctx.value.patient?.name || '?').split(' ').filter(Boolean)
  return (w.length > 1 ? w[0][0] + w[w.length - 1][0] : (w[0] || '?')[0]).toUpperCase()
})
const subtitleText = computed(() => subtitle.value.charAt(0).toUpperCase() + subtitle.value.slice(1))
const stepNum = computed(() => String(tab.value + 1).padStart(2, '0'))
// a short line under each step name in the step bar
const STEP_SUB = { Assessment: 'Measurements', Diagnosis: 'PES statement', Intervention: 'Energy and diet', Monitoring: 'Goals and progress', Review: 'Check and finalize', Summary: 'The saved record' }
// BMI marker on the WHO Asia-Pacific bar: four bands (<18.5, 18.5–22.9, 23–24.9, ≥25) drawn at fixed widths
function bmiPos(b) {
  const bands = [[12, 18.5, 0, 24], [18.5, 23, 24, 54], [23, 25, 54, 74], [25, 35, 74, 100]]
  const v = Math.min(35, Math.max(12, Number(b)))
  const [lo, hi, p0, p1] = bands.find(([, h]) => v < h) || bands[3]
  return Math.min(98, Math.max(2, p0 + ((v - lo) / (hi - lo)) * (p1 - p0)))
}
const bmiTone = b => (b < 18.5 ? 'low' : b < 23 ? 'ok' : b < 25 ? 'warn' : 'high')
// screening symptoms as tags (the text is comma-separated)
const symptomTags = computed(() => String(ctx.value.screening?.symptoms || '').split(',').map(x => x.trim()).filter(Boolean))
</script>
<style scoped>
/* ================= NCP RECORD (UI refresh: brand #004D3A / #EFBF04, DM Sans + Playfair) ================= */
.ncp-overlay { z-index: 200; backdrop-filter: blur(4px); }
.ncp {
  --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22);
  position: relative; display: flex; flex-direction: column; width: 100%; max-width: 1120px; max-height: 90dvh; overflow: hidden;
  background: #fff; border-radius: 26px; font-family: 'DM Sans', sans-serif; color: #22362c; box-shadow: 0 40px 90px -30px rgba(0, 0, 0, 0.5);
}
.ncp .ic { flex-shrink: 0; }
.ncp.is-inline { max-width: none; max-height: none; height: 100%; border-radius: 18px; box-shadow: none; border: 1px solid #e4ebe6; }
.ncp-inline { height: 100%; }
.pad { padding: 20px 26px; }
.ncp-loading { display: flex; align-items: center; gap: 10px; font-size: 14px; font-weight: 600; color: #6b7d73; }
.ncp-spin { width: 18px; height: 18px; border-radius: 50%; border: 2.5px solid #e3efe7; border-top-color: #004d3a; animation: ncp-spin 0.8s linear infinite; }
@keyframes ncp-spin { to { transform: rotate(360deg); } }

/* ---------- header (green, with the plate) ---------- */
.ncp-head {
  position: relative; overflow: hidden; flex-shrink: 0; display: flex; flex-direction: column; gap: 16px; padding: 22px 26px 0; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 55%, #004635 100%);
}
.ncp-head-plate { position: absolute; right: -30px; top: 50%; width: 260px; height: 260px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); opacity: 0.75; pointer-events: none; }
.ncp-head-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 50%, rgba(0, 77, 58, 0.75) 75%, rgba(0, 77, 58, 0.35) 100%); }
.ncp-head-top { position: relative; z-index: 1; display: flex; align-items: center; gap: 18px; padding: 4px 0 2px; }
.ncp-av {
  flex-shrink: 0; width: 56px; height: 56px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; letter-spacing: 0.06em;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.14);
}
.ncp-title-wrap { flex: 1; min-width: 0; }
.ncp-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; line-height: 1.3; text-transform: uppercase; color: #efbf04; }
.ncp-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.ncp-title { margin: 0 0 8px; font-family: 'Playfair Display', serif; font-size: 27px; font-weight: 700; line-height: 1.3; letter-spacing: 0.015em; word-spacing: 0.06em; font-stretch: normal; color: #fff; overflow-wrap: anywhere; }
.ncp-title em { margin-left: 4px; font-style: normal; font-weight: 600; color: rgba(255, 255, 255, 0.72); }
.ncp-kind.follow { color: #f5d466; }
.ncp-sub { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 12px; margin: 0; font-size: 14px; line-height: 1.5; letter-spacing: 0.01em; color: rgba(255, 255, 255, 0.88); }
.ncp-sub i { width: 4px; height: 4px; border-radius: 50%; background: rgba(255, 255, 255, 0.45); }
.ncp-final { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; letter-spacing: 0.02em; border-radius: 999px; background: rgba(110, 231, 168, 0.16); border: 1px solid rgba(110, 231, 168, 0.35); font-size: 12px; font-weight: 800; color: #6ee7a8; }
.ncp-head-right { align-self: flex-start; display: flex; align-items: center; gap: 10px; }
.save-state { padding: 5px 11px; border-radius: 999px; background: rgba(255, 255, 255, 0.12); font-size: 12px; font-weight: 700; color: rgba(255, 255, 255, 0.85); white-space: nowrap; }
.save-state.dirty { background: rgba(239, 191, 4, 0.2); color: #f5d466; }
.save-state.ok { background: rgba(110, 231, 168, 0.16); color: #6ee7a8; }
.icon-x {
  width: 40px; height: 40px; display: inline-flex; align-items: center; justify-content: center; border-radius: 12px; cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.3); background: rgba(0, 56, 42, 0.55); color: #fff; backdrop-filter: blur(6px);
}
.icon-x:hover { background: rgba(0, 56, 42, 0.8); }
.icon-x:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }

/* ---------- step bar (inside the header) ---------- */
.steps {
  position: relative; z-index: 1; display: flex; align-items: center; gap: 10px; margin: 0 -26px; padding: 12px 26px; overflow-x: auto; scrollbar-width: none;
  background: rgba(0, 40, 30, 0.35); border-top: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(8px);
}
.steps::-webkit-scrollbar { display: none; }
.step {
  flex-shrink: 0; display: inline-flex; align-items: center; gap: 10px; padding: 5px 14px 5px 5px; border: none; border-radius: 999px;
  background: transparent; font-family: inherit; text-align: left; color: #fff; cursor: pointer; white-space: nowrap; transition: background 0.15s;
}
.step:hover:not(.active) { background: rgba(255, 255, 255, 0.08); }
.step:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }
.step-dot {
  flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
  background: rgba(255, 255, 255, 0.12); color: rgba(255, 255, 255, 0.8); font-size: 13px; font-weight: 800;
}
.step.done .step-dot { background: rgba(110, 231, 168, 0.2); color: #6ee7a8; }
.step.partial .step-dot { background: rgba(239, 191, 4, 0.22); color: #f5d466; }
.step.ready .step-dot { background: #efbf04; color: #004d3a; }
.step.err .step-dot { background: #fdecec; color: #a12525; }
.step-txt { display: flex; flex-direction: column; }
.step-name { font-size: 13.5px; font-weight: 800; letter-spacing: 0.01em; }
.step-sub { font-size: 11.5px; color: rgba(255, 255, 255, 0.6); }
.step.active { background: #fff; box-shadow: 0 12px 24px -14px rgba(0, 0, 0, 0.6); }
.step.active .step-dot { background: #efbf04; color: #004d3a; }
.step.active.err .step-dot { background: #fdecec; color: #a12525; }
.step.active .step-name { color: #004d3a; }
.step.active .step-sub { color: #6b7d73; }
.step-line { flex: 1; min-width: 18px; height: 2px; border-radius: 2px; background: rgba(255, 255, 255, 0.16); }
.step-line.done { background: rgba(110, 231, 168, 0.4); }

/* ---------- body ---------- */
.ncp-body { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr) 320px; }
.ncp.is-inline .ncp-body { grid-template-columns: minmax(0, 1fr); }
.ncp-form {
  min-width: 0; overflow-y: auto; padding: 22px 26px 26px;
  background: radial-gradient(90% 60% at 100% 0%, rgba(239, 191, 4, 0.06), rgba(239, 191, 4, 0) 60%), #f4f8f6;
}
.step-sec { display: flex; flex-direction: column; gap: 16px; }
.step-sec > * { flex-shrink: 0; }
.step-head { display: flex; align-items: center; gap: 14px; margin: 0; }
.step-num {
  flex-shrink: 0; width: 48px; height: 48px; border-radius: 15px; display: inline-flex; align-items: center; justify-content: center;
  background: #fff; color: #004d3a; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; box-shadow: var(--sh); border-bottom: 3px solid #efbf04;
}
.step-title { margin: 0 0 4px; font-family: 'Playfair Display', serif; font-size: 23px; font-weight: 700; line-height: 1.3; letter-spacing: 0.015em; word-spacing: 0.06em; color: #0e3a2c; }
.step-desc { margin: 0; font-size: 13.5px; line-height: 1.5; color: #6b7d73; }
.banner { display: flex; align-items: center; gap: 8px; margin: 0 0 16px; padding: 10px 14px; border-radius: 14px; background: #fff; border: 1px solid #e4ebe6; font-size: 13px; font-weight: 600; color: #4a5a52; }
.hint-box { display: flex; gap: 8px; align-items: flex-start; margin: 0; padding: 11px 14px; border-radius: 14px; background: #fff; border: 1px solid #d6e8dc; border-left: 3px solid #1f9d55; font-size: 13px; line-height: 1.5; color: #2c4a3c; }
.hint-box svg { flex-shrink: 0; margin-top: 2px; color: #1f7a4d; }
.ncp-form > .nm-error { margin: 0 0 14px; }
.strip-toggle { display: none; }

/* cards */
.card { padding: 18px; border-radius: 20px; background: #fff; box-shadow: var(--sh); }
.card-head { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid #f0f3f1; }
.card-head-txt { flex: 1; min-width: 0; }
.card-ico, .sum-ico, .fact-ico { flex-shrink: 0; display: inline-flex; align-items: center; justify-content: center; }
.card-ico { width: 38px; height: 38px; border-radius: 12px; }
.ico-green { background: #e3efe7; color: #004d3a; }
.ico-gold { background: #fbf3d2; color: #9a7300; }
.ico-red { background: #fdedef; color: #b4384a; }
.ico-blue { background: #eef1fa; color: #3b5ba5; }
.ico-purple { background: #f1eef8; color: #5b4a9a; }
.ms-title, .ter-title { margin: 0; font-size: 15.5px; font-weight: 800; color: #0e3a2c; }
.card-sub { margin: 2px 0 0; font-size: 12.5px; color: #6b7d73; }
.ms-bar { display: flex; align-items: center; gap: 8px; margin: 0; }
.ms-locked .grid .nm-input:disabled { background: #f4f7f5; border-color: #d3dfd8; color: #22362c; cursor: not-allowed; }

/* ---------- fields ---------- */
.grid { display: grid; column-gap: 14px; row-gap: 0; margin-bottom: 4px; } /* rows are spaced by each field's margin (they span 4 subgrid rows) */
.g3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.g4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
:deep(.field) { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; min-width: 0; }
/* Fields side by side share label / input / hint rows, so the inputs line up
   even when one label wraps to two lines ("Blood pressure (mmHg)"). */
.grid > :deep(*) { grid-row: span 4; } /* label · control · category · hint */
.grid > :deep(.field) { display: grid; grid-template-rows: subgrid; row-gap: 0; align-content: start; }
.grid > :deep(.field > * + *) { margin-top: 6px; } /* spacing only where there's content, so empty rows add nothing */
.grid > :deep(.field > .field-label) { align-self: end; }
:deep(.field-label) { position: relative; font-size: 12px; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase; color: #6b7d73; }
:deep(.req) { color: #c0392b; }
:deep(.field-hint) { font-size: 12px; line-height: 1.45; color: #8a9a91; }
:deep(.field-error) { font-size: 12px; font-weight: 700; color: #c0392b; }
.ncp :deep(.nm-input), .ncp :deep(.nm-select) {
  min-height: 44px; border: 1.5px solid #c9d8cf; border-radius: 12px; background-color: #fff; font-family: inherit; font-size: 14.5px; font-weight: 600; color: #14261e;
  box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05);
  transition: border-color 0.15s, box-shadow 0.15s, background-color 0.15s;
}
.ncp :deep(.nm-input:hover:not(:disabled)), .ncp :deep(.nm-select:hover:not(:disabled)) { border-color: #9ec4ad; }
.ncp :deep(.nm-input:focus), .ncp :deep(.nm-select:focus) { outline: none; background-color: #fff; border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.ncp :deep(.nm-input:disabled), .ncp :deep(.nm-select:disabled) { background-color: #f4f7f5; border-color: #d3dfd8; border-style: solid; color: #22362c; -webkit-text-fill-color: #22362c; opacity: 1; box-shadow: none; }
.ncp :deep(textarea.nm-input) { line-height: 1.55; }
:deep(.field.invalid .nm-input) { border-color: #e0a3a3; background-color: #fffafa; }
/* ⓘ beside a label; the bubble stays within the field's width so it never runs off the modal. */
:deep(.info-tip) { display: inline-flex; vertical-align: -2px; margin-left: 5px; color: #8a9a91; cursor: help; border-radius: 50%; text-transform: none; letter-spacing: 0; }
:deep(.info-tip:hover), :deep(.info-tip:focus-visible) { color: #004d3a; outline: none; }
:deep(.info-tip:focus-visible) { box-shadow: 0 0 0 2px rgba(0, 56, 42, 0.25); }
:deep(.info-bubble) {
  position: absolute; left: 0; bottom: calc(100% + 6px); z-index: 30; width: max-content; max-width: 100%;
  background: #00382a; color: #fff; font-size: 12px; font-weight: 500; line-height: 1.4; text-transform: none; letter-spacing: 0;
  padding: 7px 10px; border-radius: 10px; box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
  opacity: 0; visibility: hidden; transition: opacity 0.12s; pointer-events: none;
}
:deep(.info-tip:hover .info-bubble), :deep(.info-tip:focus .info-bubble) { opacity: 1; visibility: visible; }
/* No up/down arrows on number boxes: in the narrow room panel they hid the
   value (128 showed as "12") and a stray click set an empty box to its min. */
input[type='number'] { appearance: textfield; -moz-appearance: textfield; }
input[type='number']::-webkit-outer-spin-button,
input[type='number']::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.bp { display: flex; align-items: center; gap: 6px; }
.bp input { min-width: 0; padding-left: 10px; padding-right: 10px; }
.bp span { font-weight: 700; color: #a3b1a9; }
.was { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin: 6px 0 0; padding: 6px 10px; border-radius: 10px; background: #fff8e6; font-size: 12.5px; color: #7a5a00; }
.m-cat { display: inline-flex; align-items: center; gap: 5px; align-self: flex-start; margin: 6px 0 0; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.m-cat.ok { background: #e3f4ea; color: #1f7a4d; }
.m-cat.warn { background: #fff4d6; color: #8a6500; }
.m-cat.danger { background: #fdecea; color: #b42318; }
.lab-link { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin: 8px 0 0; padding: 8px 12px; border-radius: 12px; background: #f7faf8; font-size: 12.5px; color: #4a5a52; }
.lab-link a { color: #a37a0b; font-weight: 700; text-decoration: none; }
.lab-link a:hover { text-decoration: underline; }
.k { font-size: 11.5px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; color: #6b7d73; }
.c-sub { margin: 0; font-size: 12.5px; color: #8a9a91; }

/* BMI */
.computed { display: flex; flex-direction: column; justify-content: center; margin-bottom: 14px; padding: 12px 14px; border-radius: 16px; background: linear-gradient(135deg, #f1f8f4, #fff); border: 1px solid #dcede3; }
.bmi-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.bmi-chip { padding: 3px 10px; border-radius: 999px; background: #e3f4ea; font-size: 12px; font-weight: 800; color: #1f7a4d; white-space: nowrap; }
.bmi-low .bmi-chip { background: #eef1fa; color: #3b5ba5; }
.bmi-warn .bmi-chip { background: #fff4d6; color: #8a6500; }
.bmi-high .bmi-chip { background: #fdecea; color: #b42318; }
.computed strong { font-family: 'Playfair Display', serif; font-size: 28px; line-height: 1.15; color: #004d3a; font-variant-numeric: tabular-nums; }
.bmi-scale { position: relative; display: grid; grid-template-columns: 1.2fr 1.5fr 1fr 1.3fr; gap: 3px; height: 7px; margin-top: 8px; }
.bmi-scale span { border-radius: 999px; }
.bmi-scale span:nth-child(1) { background: #9db4f0; }
.bmi-scale span:nth-child(2) { background: #1f9d55; }
.bmi-scale span:nth-child(3) { background: #efbf04; }
.bmi-scale span:nth-child(4) { background: #e07a5f; }
.bmi-scale i { position: absolute; top: -4px; width: 15px; height: 15px; margin-left: -7px; border-radius: 50%; background: #fff; border: 3px solid #004d3a; box-sizing: border-box; transition: left 0.3s; }
.bmi-lbl { display: grid; grid-template-columns: 1.2fr 1.5fr 1fr 1.3fr; gap: 3px; margin-top: 6px; font-size: 10px; color: #8a9a91; }

/* ---------- diagnosis ---------- */
.pes-card { display: flex; gap: 14px; padding: 16px; border-radius: 20px; background: #fff; box-shadow: var(--sh); border-left: 4px solid var(--c); }
.pes-p { --c: #004d3a; --bg: #e3efe7; }
.pes-e { --c: #9a7300; --bg: #fbf3d2; }
.pes-s { --c: #3b5ba5; --bg: #eef1fa; }
.pes-l { flex-shrink: 0; width: 42px; height: 42px; border-radius: 13px; display: inline-flex; align-items: center; justify-content: center; background: var(--bg); color: var(--c); font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; }
.pes-b { flex: 1; min-width: 0; }
.pes-b :deep(.field) { margin-bottom: 0; }
.combo { position: relative; }
.combo-list { position: absolute; z-index: 20; top: calc(100% + 6px); left: 0; right: 0; max-height: 280px; overflow-y: auto; padding: 6px; background: #fff; border: 1px solid #e4ebe6; border-radius: 14px; box-shadow: 0 18px 36px -12px rgba(16, 35, 27, 0.3); }
.combo-group { margin: 8px 8px 4px; font-size: 11px; font-weight: 800; letter-spacing: 0.6px; text-transform: uppercase; color: #6b7d73; }
.combo-group.linked { color: #1f7a4d; }
.combo-opt { display: block; width: 100%; padding: 8px 10px; border: none; border-radius: 10px; background: none; text-align: left; font-family: inherit; font-size: 13.5px; color: #0e3a2c; cursor: pointer; }
.combo-opt:hover, .combo-opt.on { background: #f1f6f2; }
.combo-tag { float: right; margin-left: 10px; font-size: 11px; font-weight: 700; color: #8a9a91; }
.pes-preview { margin: 0; padding: 18px; border-radius: 20px; background: linear-gradient(135deg, #004d3a, #035a45); color: #fff; box-shadow: 0 18px 36px -20px rgba(0, 77, 58, 0.8); }
.pes-preview-h { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.pes-preview-ico { width: 32px; height: 32px; border-radius: 10px; background: rgba(255, 255, 255, 0.12); color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.pes-preview .k { color: #fff; font-size: 13px; letter-spacing: 0.3px; }
.pes-preview-h small { margin-left: auto; font-size: 12px; color: rgba(255, 255, 255, 0.6); }
.pes-preview p { margin: 0; font-size: 15px; line-height: 1.7; color: rgba(255, 255, 255, 0.92); overflow-wrap: anywhere; }

/* ---------- intervention ---------- */
.ter-box .card-head { margin-bottom: 14px; }
.ter-grid { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 16px; align-items: center; }
.ter-big { display: flex; flex-direction: column; justify-content: center; min-width: 170px; padding: 16px 18px; border-radius: 18px; background: linear-gradient(135deg, #004d3a, #035a45); color: #fff; box-shadow: 0 14px 28px -18px rgba(0, 77, 58, 0.9); }
.ter-big small { font-size: 11px; font-weight: 800; letter-spacing: 0.6px; text-transform: uppercase; color: #efbf04; }
.ter-big strong { font-family: 'Playfair Display', serif; font-size: 36px; line-height: 1.1; }
.ter-big em { font-style: normal; font-size: 12.5px; color: rgba(255, 255, 255, 0.7); }
.ter-side { display: flex; flex-direction: column; align-items: flex-start; gap: 10px; min-width: 0; }
.ter-act { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.ter-act > span { font-size: 12px; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase; color: #6b7d73; }
.ter-act .nm-select { width: 100%; }
.ter-toggle { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 0 14px; border: 1px solid #dce8e0; border-radius: 999px; background: #f1f6f2; font-family: inherit; font-size: 12.5px; font-weight: 800; color: #004d3a; cursor: pointer; }
.ter-toggle:hover { background: #e3efe7; }
.ter-toggle:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
@media (prefers-reduced-motion: no-preference) { .ter-toggle svg { transition: transform 0.15s; } }
.ter-toggle svg.up { transform: rotate(180deg); }
.ter-steps { display: grid; gap: 6px; margin: 14px 0 0; padding: 12px 14px; border-radius: 14px; background: #f7faf8; font-size: 13px; color: #4a5a52; }
.ter-steps div { display: grid; grid-template-columns: 74px 1fr; gap: 8px; }
.ter-steps dt { font-weight: 800; color: #0e3a2c; }
.ter-steps dd { margin: 0; }
.ter-steps strong { color: #0e3a2c; }
.ter-steps .ter-total { margin-top: 2px; padding-top: 8px; border-top: 1px solid #e4ebe6; }
.ter-box .plain-note, .ter-box > .c-sub { margin: 12px 0 0; }
.ter-field { max-width: 320px; }
.macro-line { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; margin: -2px 0 14px; padding: 9px 12px; border-radius: 12px; background: #f1f6f2; font-size: 13px; color: #2c4a3c; }
.macro-line.warn, .rx-outdated { background: #fff8e6; color: #7a5a00; }
.rx-outdated { margin: 8px 0 0; }
.mt-bar { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 4px 0 10px; padding-top: 14px; border-top: 1px solid #f0f3f1; }
.mt-bar-title { margin: 0; font-size: 14.5px; font-weight: 800; color: #0e3a2c; }
.mt-bar-title span { margin-left: 8px; padding: 2px 9px; border-radius: 999px; background: #f3f6f4; font-size: 12px; font-weight: 700; color: #6b7d73; }
.mt-chev { transition: transform 0.15s ease; }
.mt-chev.up { transform: rotate(180deg); }
@media (prefers-reduced-motion: reduce) { .mt-chev { transition: none; } }
.mt-split { display: flex; gap: 3px; height: 28px; margin: 0 0 12px; border-radius: 10px; overflow: hidden; }
.mt-split span { flex-basis: 0; min-width: 0; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 800; color: #fff; transition: flex-grow 0.3s; }
.sp-carb { background: #c49102; }
.sp-protein { background: #1f9d55; }
.sp-fat { background: #3b5ba5; }
.mt-summary { margin: 0 0 12px; padding: 10px 14px; border-radius: 12px; background: #f7faf8; border: 1px solid #d3dfd8; font-size: 13.5px; color: #22362c; }
.macro-table { margin: 2px 0 8px; border: 1px solid #eef2ef; border-radius: 14px; overflow: hidden; }
.mt-row { display: grid; grid-template-columns: 1.4fr 1fr 1fr; gap: 10px; align-items: center; padding: 10px 14px; border-top: 1px solid #f3f6f4; font-size: 14px; color: #22362c; }
.mt-row:first-child { border-top: none; }
.mt-head { background: #f7faf8; font-size: 11px; font-weight: 800; letter-spacing: 0.8px; text-transform: uppercase; color: #6b7d73; }
.mt-name { display: inline-flex; align-items: center; gap: 8px; font-weight: 700; }
.mt-name small { font-weight: 500; color: #8a9a91; }
.mt-dot { width: 9px; height: 9px; border-radius: 3px; }
.mt-pct { width: 74px !important; display: inline-block; text-align: center; }
.mt-g { font-weight: 800; color: #0e3a2c; }
.mt-foot { background: #f7faf8; font-weight: 800; color: #1f5c45; }
.mt-foot.bad { color: #c0392b; }
.mt-err { margin: 0 0 12px; font-size: 13px; font-weight: 700; color: #c0392b; }

/* ---------- monitoring ---------- */
.prev-box { margin: 0; padding: 16px 18px; border-radius: 20px; background: #fff; box-shadow: var(--sh); border-left: 4px solid #efbf04; }
.prev-h { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.prev-box p { margin: 6px 0 0; font-size: 14px; line-height: 1.55; color: #3e5046; }
.prev-box strong { color: #0e3a2c; }
.since { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.since div { display: flex; flex-direction: column; gap: 2px; padding: 12px 14px; border-radius: 14px; background: #f7faf8; }
.since strong { font-family: 'Playfair Display', serif; font-size: 20px; color: #004d3a; }
.goals { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.goal { min-height: 44px; padding: 8px 6px; border: 1.5px solid #c9d8cf; border-radius: 12px; background: #fff; font-family: inherit; font-size: 13.5px; font-weight: 700; color: #22362c; cursor: pointer; transition: all 0.15s; }
.goal:hover:not(:disabled):not(.on) { border-color: #9ec4ad; }
.goal.on { background: #004d3a; border-color: #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.9); }
.goal:disabled:not(.on) { opacity: 0.6; cursor: default; }

/* ---------- review / summary ---------- */
.missing { margin: 0; padding: 14px 16px; border-radius: 18px; background: #fffdf5; border: 1.5px dashed #e7c65a; font-size: 13.5px; color: #3d3005; }
.missing p { display: flex; gap: 6px; align-items: center; margin: 0 0 6px; font-weight: 800; color: #8a6500; }
.missing ul { margin: 0; padding-left: 20px; line-height: 1.9; }
.done-card { position: relative; overflow: hidden; display: flex; align-items: center; flex-wrap: wrap; gap: 14px; padding: 16px 18px; border-radius: 20px; background: linear-gradient(135deg, #004d3a, #035a45); color: #fff; box-shadow: 0 18px 36px -20px rgba(0, 77, 58, 0.8); }
.done-card::after { content: ''; position: absolute; right: -40px; top: -40px; width: 160px; height: 160px; border-radius: 50%; background: radial-gradient(circle, rgba(239, 191, 4, 0.25), rgba(239, 191, 4, 0) 70%); pointer-events: none; }
.done-card > * { position: relative; z-index: 1; }
.done-ico { flex-shrink: 0; width: 46px; height: 46px; border-radius: 14px; background: #efbf04; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.done-txt { flex: 1; min-width: 180px; }
.done { margin: 0; font-size: 16px; font-weight: 800; color: #fff; }
.done-sub { margin: 2px 0 0; font-size: 13px; color: rgba(255, 255, 255, 0.75); }
.ncp .done-link { display: inline-flex; align-items: center; gap: 8px; min-height: 44px; padding: 0 18px; border-radius: 12px; background: #efbf04; border-color: #efbf04; color: #004d3a; font-size: 14px; font-weight: 800; text-decoration: none; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
.ncp .done-link:hover { background: #f5cb1c; }
.ready-hint { display: flex; align-items: flex-start; gap: 8px; margin: 0; padding: 12px 14px; border-radius: 14px; background: #e3f4ea; font-size: 13.5px; color: #1f5c45; }
.ready-hint svg { flex-shrink: 0; margin-top: 1px; }
.summary { display: flex; flex-direction: column; gap: 10px; margin: 0; }
.summary div { display: grid; grid-template-columns: 170px minmax(0, 1fr); gap: 14px; align-items: start; padding: 14px 16px; border-radius: 18px; background: #fff; box-shadow: var(--sh); }
.summary dt { display: flex; align-items: center; gap: 10px; margin: 0; font-size: 13.5px; font-weight: 800; color: #0e3a2c; }
.sum-ico { width: 32px; height: 32px; border-radius: 10px; }
.summary dd { margin: 0; padding-top: 6px; font-size: 14px; line-height: 1.6; color: #3e5046; white-space: pre-line; overflow-wrap: anywhere; }
.summary dd.empty { color: #8a9a91; font-style: italic; }

/* ---------- patient strip ---------- */
.strip { min-width: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; padding: 22px 20px 26px; background: #fbfcfb; border-left: 1px solid #eef2ef; }
.strip-pt { display: flex; align-items: center; gap: 12px; padding: 14px; border-radius: 18px; background: #fff; border: 1px solid #eef2ef; }
.ncp:not(.is-inline) .strip-pt { display: none; } /* the header already names the patient */
.strip-av { flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-family: 'Playfair Display', serif; font-size: 16px; font-weight: 700; }
.strip-name { margin: 0; font-size: 15px; font-weight: 800; color: #0e3a2c; }
.allergy { display: flex; align-items: flex-start; gap: 8px; margin: 0; padding: 10px 12px; border-radius: 12px; background: #fef3f2; border: 1px solid #f6cfcb; font-size: 13px; line-height: 1.4; color: #912018; }
.allergy svg { flex-shrink: 0; margin-top: 1px; color: #c0392b; }
.allergy b { font-weight: 800; }
.strip-facts { display: flex; flex-direction: column; gap: 12px; margin: 0; padding: 14px; border-radius: 18px; background: #fff; border: 1px solid #eef2ef; }
.strip-facts div { position: relative; min-height: 32px; padding-left: 44px; }
.fact-ico { position: absolute; left: 0; top: 0; width: 32px; height: 32px; border-radius: 10px; }
.strip-facts dt { margin: 0; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; color: #8a9a91; }
.strip-facts dd { margin: 2px 0 0; font-size: 13.5px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.strip-facts dd small { font-weight: 500; color: #6b7d73; }
.strip-facts dd.risk { color: #a12525; }
/* screening baseline card */
.baseline { margin: 0; padding: 14px; border-radius: 18px; background: linear-gradient(160deg, #f1f8f4, #fff); border: 1px solid #dcede3; }
.bl-head { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 12px; }
.bl-ico { flex-shrink: 0; width: 30px; height: 30px; border-radius: 9px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; }
.bl-title { margin: 0; font-size: 14px; font-weight: 800; color: #0e3a2c; }
.bl-sub { margin: 1px 0 0; font-size: 11.5px; line-height: 1.4; color: #6b7d73; }
.bl-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin: 0; }
.bl-grid div { display: flex; flex-direction: column; min-width: 0; padding: 10px 12px; border-radius: 12px; background: #fff; border: 1px solid #e6f0ea; }
.bl-grid dt { margin: 0; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; color: #6b7d73; }
.bl-grid dd { margin: 0; font-family: 'Playfair Display', serif; font-size: 21px; font-weight: 700; line-height: 1.2; color: #004d3a; font-variant-numeric: tabular-nums lining-nums; }
.bl-grid small { font-size: 11.5px; color: #6b7d73; }
.bl-grid .risk dd { color: #b23b2e; }
.bl-sym { margin: 10px 0 0; font-size: 12.5px; color: #3e5046; overflow-wrap: anywhere; }
.bl-sym strong { font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; color: #6b7d73; }
.bl-tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }
.bl-tags em { padding: 3px 9px; border-radius: 999px; background: #fff; border: 1px solid #e6f0ea; font-style: normal; font-size: 12px; font-weight: 700; color: #22362c; }
.strip-card { display: flex; align-items: center; gap: 10px; padding: 12px; border-radius: 14px; background: #f1f6f2; }
.strip-card.gold { background: #fbf3d2; }
.strip-card-ico { flex-shrink: 0; width: 32px; height: 32px; border-radius: 10px; background: #fff; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.strip-card.gold .strip-card-ico { color: #9a7300; }
.strip-k { margin: 0; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase; color: #6b7d73; }
.strip-card.gold .strip-k { color: #8a6500; }
.strip-card .c-sub { font-size: 13.5px; font-weight: 700; color: #0e3a2c; }

/* ---------- footer ---------- */
.ncp-foot { flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px 12px; padding: 14px 26px; border-top: 1px solid #eef2ef; background: #fff; }
.foot-err { flex-basis: 100%; display: flex; align-items: center; gap: 6px; margin: 0 0 2px; font-size: 13px; font-weight: 700; color: #a12525; }
.foot-mid { display: inline-flex; align-items: center; gap: 12px; font-size: 13px; color: #6b7d73; }
.foot-lock { display: inline-flex; align-items: center; gap: 6px; padding-right: 12px; border-right: 1px solid #e4ebe6; font-weight: 700; color: #1f7a4d; }
.foot-step b { color: #0e3a2c; }
.foot-dots { display: inline-flex; gap: 5px; }
.foot-dots i { width: 8px; height: 8px; border-radius: 999px; background: #dce5df; transition: width 0.2s; }
.foot-dots i.done { background: #1f9d55; }
.foot-dots i.on { width: 22px; background: #004d3a; }
.foot-right { display: flex; gap: 8px; flex-wrap: wrap; }
.ncp-foot .nm-btn-outline, .ncp-foot .nm-btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-height: 44px; padding: 0 20px; border-radius: 12px; font-size: 14px; font-weight: 800; }
.ncp-foot .nm-btn-outline { background: #f1f6f2; border: 1px solid #dce8e0; color: #004d3a; }
.ncp-foot .nm-btn-dark { box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.ncp-foot button:disabled { opacity: 0.45; cursor: not-allowed; box-shadow: none; }
.inner-overlay { position: absolute; inset: 0; z-index: 30; display: flex; align-items: center; justify-content: center; padding: 16px; background: rgba(8, 32, 24, 0.5); backdrop-filter: blur(3px); }
.labs-modal { max-width: 720px; }

/* ---------- consultation room (inline, narrow panel) ---------- */
/* The steps share one row: dot above the name, equal columns (4 steps, 5 on a follow-up) — no wrapping. */
.ncp.is-inline .ncp-head { padding: 16px 16px 0; gap: 12px; border-radius: 17px 17px 0 0; }
.ncp.is-inline .ncp-title { font-size: 20px; }
.ncp.is-inline .ncp-title em { display: none; }
.ncp.is-inline .steps { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); gap: 4px; overflow: visible; margin: 0 -16px; padding: 8px 10px; }
.ncp.is-inline .step { flex-direction: column; justify-content: center; gap: 4px; padding: 6px 2px; border-radius: 12px; min-width: 0; }
.ncp.is-inline .step-sub, .ncp.is-inline .step-line { display: none; }
.ncp.is-inline .step-dot { width: 26px; height: 26px; font-size: 12px; }
.ncp.is-inline .step-name { max-width: 100%; overflow: hidden; text-overflow: ellipsis; font-size: 12px; text-align: center; }
.ncp.is-inline .g4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.ncp.is-inline .ncp-form, .ncp.is-inline .ncp-foot { padding-left: 16px; padding-right: 16px; }
.ncp.is-inline .foot-mid { display: none; }

/* ---------- tablet ---------- */
@media (max-width: 900px) {
  .ncp-body { display: flex; flex-direction: column; overflow-y: auto; }
  .ncp-form { overflow: visible; }
  .strip { display: none; overflow: visible; border-left: none; border-bottom: 1px solid #eef2ef; }
  .strip.open { display: flex; order: -1; }
  .strip-toggle { display: inline-flex; align-items: center; gap: 6px; margin: 0 0 14px; padding: 0 14px; min-height: 36px; border: 1px solid #e4ebe6; border-radius: 999px; background: #fff; font-family: inherit; font-size: 12.5px; font-weight: 800; color: #004d3a; cursor: pointer; }
  .g4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .ter-grid { grid-template-columns: minmax(0, 1fr); }
  .foot-lock { display: none; }
}
/* A long pop-up goes full screen on phones, like the lab file pop-up. */
@media (max-width: 640px) {
  .ncp-overlay { padding: 0; }
  .ncp:not(.is-inline) { max-width: none; max-height: none; height: 100%; border-radius: 0; }
  .ncp:not(.is-inline) .ncp-foot { padding-bottom: calc(12px + env(safe-area-inset-bottom)); }
}
@media (max-width: 560px) {
  .ncp-head { padding: 16px 16px 0; gap: 12px; }
  .ncp-head-plate { width: 170px; height: 170px; right: -60px; opacity: 0.45; }
  .ncp-av { width: 44px; height: 44px; font-size: 16px; }
  .ncp-title { font-size: 21px; }
  .ncp-title em { display: none; }
  .save-state { display: none; }
  .steps { margin: 0 -16px; padding: 10px 16px; gap: 6px; }
  .step:not(.active) .step-txt { display: none; }
  .step:not(.active) { padding: 4px; }
  .step-sub { display: none; }
  .step-dot { width: 28px; height: 28px; }
  .step-line { min-width: 10px; }
  .ncp-form, .strip { padding-left: 16px; padding-right: 16px; }
  .ncp-form { padding-top: 16px; }
  .step-num { width: 40px; height: 40px; border-radius: 12px; font-size: 17px; }
  .step-title { font-size: 20px; }
  .card, .pes-card, .prev-box { padding: 14px; }
  .pes-card { flex-direction: column; gap: 10px; }
  .pes-l { width: 34px; height: 34px; font-size: 18px; }
  .g3 { grid-template-columns: minmax(0, 1fr); }
  .card-head { flex-wrap: wrap; }
  .ms-bar { width: 100%; }
  .ms-bar > * { flex: 1; justify-content: center; }
  .ter-field { max-width: none; }
  .mt-row { grid-template-columns: 1.3fr 1fr 0.8fr; padding: 10px; font-size: 13px; }
  .goals { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .since { grid-template-columns: minmax(0, 1fr); }
  .summary div { grid-template-columns: minmax(0, 1fr); gap: 4px; }
  .summary dd { padding-top: 0; }
  .done-card .done-link { width: 100%; justify-content: center; }
  .ncp-foot { padding: 12px 16px; }
  .foot-mid { display: none; }
  .ncp-foot { flex-wrap: nowrap; }
  .ncp-foot .foot-err { display: none; }
  .foot-right { flex: 1; justify-content: flex-end; }
  .foot-right > * { flex: 1; justify-content: center; padding: 0 12px; }
}
</style>