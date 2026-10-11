<template>
  <div :class="inline ? 'ncp-inline' : 'nm-modal-overlay ncp-overlay'" @click.self="!inline && requestClose()">
    <div class="ncp" :class="{ 'is-inline': inline }" role="dialog" :aria-modal="!inline" aria-labelledby="ncp-title">
      <!-- HEADER -->
      <header class="ncp-head">
        <div class="ncp-title-wrap">
          <h2 id="ncp-title" class="ncp-title">Nutrition Care Process</h2>
          <p class="ncp-sub">{{ patientName }} · {{ subtitle }}</p>
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
            <p v-if="isFinalized" class="banner lock"><Lock :size="15" /> Finalized {{ dateTime(record.updated_at) }} — part of the patient's permanent record.</p>
            <p v-else-if="isReadOnly" class="banner"><Lock :size="15" /> Viewing an unfinished record (read-only).</p>
            <p v-if="saveError" class="nm-error">{{ saveError }}</p>

            <button v-if="!inline" type="button" class="strip-toggle" @click="stripOpen = !stripOpen">
              <Info :size="14" /> {{ stripOpen ? 'Hide' : 'Show' }} patient info
            </button>

            <!-- ASSESSMENT -->
            <section v-if="stepKey === 'assessment'">
              <p class="phase">Phase 1 · Nutrition assessment</p>
              <p v-if="prefilled && !isReadOnly" class="hint-box"><Sparkles :size="14" /> Measurements are pre-filled from their latest records — check them with the patient and update what changed.</p>
              <div class="grid g3">
                <Field label="Height (cm)" required :hint="srcHint('height_cm')" :error="errors.height_cm">
                  <input v-model="a.height_cm" type="number" :min="L.height_cm.min" :max="L.height_cm.max" step="0.1" class="nm-input" :disabled="isReadOnly" />
                </Field>
                <Field label="Weight (kg)" required :hint="srcHint('weight_kg')" :error="errors.weight_kg">
                  <input v-model="a.weight_kg" type="number" :min="L.weight_kg.min" :max="L.weight_kg.max" step="0.1" class="nm-input" :disabled="isReadOnly" />
                </Field>
                <div class="computed">
                  <span class="k">BMI · WHO Asia-Pacific</span>
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
                </Field>
                <Field label="Fasting glucose (mg/dL)" :hint="srcHint('blood_glucose')" :error="errors.blood_glucose">
                  <input v-model="a.blood_glucose" type="number" :min="L.blood_glucose.min" :max="L.blood_glucose.max" step="1" class="nm-input" :disabled="isReadOnly" />
                </Field>
                <Field label="HbA1c (%)" :hint="srcHint('hba1c')" :error="errors.hba1c">
                  <input v-model="a.hba1c" type="number" :min="L.hba1c.min" :max="L.hba1c.max" step="0.1" class="nm-input" :disabled="isReadOnly" />
                </Field>
              </div>
              <Field label="Lab notes">
                <textarea v-model="a.lab_notes" class="nm-input" :maxlength="TMAX.lab_notes" rows="2" placeholder="e.g. Lipid profile from Oct 2: LDL 160 mg/dL" :disabled="isReadOnly"></textarea>
              </Field>
              <Field label="Assessment notes">
                <textarea v-model="a.assessment_notes" class="nm-input" :maxlength="TMAX.assessment_notes" rows="3" placeholder="Diet history, 24-hour recall, appetite, activity…" :disabled="isReadOnly"></textarea>
              </Field>
              <NcpExtraRows :rows="a.extra" :templates="MEASURE_TEMPLATES.assessment" :read-only="isReadOnly" empty="Add waist circumference, cholesterol, creatinine… — pick from the list or type your own." />
            </section>

            <!-- DIAGNOSIS -->
            <section v-else-if="stepKey === 'diagnosis'">
              <p class="phase">Phase 2 · Nutrition diagnosis (PES statement)</p>
              <p v-if="carried && !isReadOnly" class="hint-box"><Sparkles :size="14" /> Carried over from the {{ shortDate(ctx.previous.encounter_date) }} record — edit what changed.</p>
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
              <Field label="Etiology — related to (E)" required>
                <textarea v-model="d.pes_etiology" class="nm-input" :maxlength="TMAX.pes_etiology" rows="2" placeholder="e.g. frequent large servings of white rice and sweetened drinks" :disabled="isReadOnly"></textarea>
              </Field>
              <Field label="Signs & symptoms — as evidenced by (S)" required>
                <textarea v-model="d.pes_signs" class="nm-input" :maxlength="TMAX.pes_signs" rows="2" placeholder="e.g. FBS 148 mg/dL, HbA1c 7.9%, diet recall of 4 cups rice/day" :disabled="isReadOnly"></textarea>
              </Field>
              <div class="pes-preview">
                <span class="k">PES statement</span>
                <p>{{ pesSentence }}</p>
              </div>
            </section>

            <!-- INTERVENTION -->
            <section v-else-if="stepKey === 'intervention'">
              <p class="phase">Phase 3 · Nutrition intervention</p>
              <p v-if="carried && !isReadOnly" class="hint-box"><Sparkles :size="14" /> Targets carried over from the {{ shortDate(ctx.previous.encounter_date) }} record — adjust as needed.</p>
              <div v-if="ctx.screening?.tdee_kcal" class="energy">
                <div><span class="k">BMR (Mifflin-St Jeor)</span><strong>{{ whole(ctx.screening.bmr_kcal) }} kcal</strong></div>
                <div><span class="k">TDEE · {{ ctx.screening.activity_level }}</span><strong>{{ whole(ctx.screening.tdee_kcal) }} kcal</strong></div>
                <p class="c-sub">From their screening of {{ shortDate(ctx.screening.date) }}.</p>
              </div>
              <div class="grid g4">
                <Field label="Target kcal / day" required :error="errors.target_kcal">
                  <input v-model="i.target_kcal" type="number" :min="L.target_kcal.min" :max="L.target_kcal.max" step="10" class="nm-input" :disabled="isReadOnly" />
                </Field>
                <Field label="Carbs (g)" :hint="macroHint('carb')" :error="errors.target_carb_g">
                  <input v-model="i.target_carb_g" type="number" :min="L.target_carb_g.min" :max="L.target_carb_g.max" step="1" class="nm-input" :disabled="isReadOnly" />
                </Field>
                <Field label="Protein (g)" :hint="macroHint('protein')" :error="errors.target_protein_g">
                  <input v-model="i.target_protein_g" type="number" :min="L.target_protein_g.min" :max="L.target_protein_g.max" step="1" class="nm-input" :disabled="isReadOnly" />
                </Field>
                <Field label="Fat (g)" :hint="macroHint('fat')" :error="errors.target_fat_g">
                  <input v-model="i.target_fat_g" type="number" :min="L.target_fat_g.min" :max="L.target_fat_g.max" step="1" class="nm-input" :disabled="isReadOnly" />
                </Field>
              </div>
              <div v-if="!isReadOnly || macroTotal" class="macro-line" :class="{ warn: macroOff }">
                <span v-if="macroTotal">Macros add up to <strong>{{ whole(macroTotal) }} kcal</strong><template v-if="Number(i.target_kcal)"> ({{ macroOff ? `${macroDiffPct}% off the target` : 'matches the target' }})</template>.</span>
                <span v-else>Add carbs, protein and fat in grams, or use a standard split.</span>
                <button v-if="!isReadOnly && Number(i.target_kcal)" type="button" class="nm-panel-link" @click="applySplit">Suggest 50 / 20 / 30 split</button>
              </div>
              <Field label="Diet prescription" required>
                <textarea v-model="i.diet_prescription" class="nm-input" :maxlength="TMAX.diet_prescription" rows="3" placeholder="e.g. 1500 kcal low-GI Filipino diet. Brown rice, 1 cup max per meal; water instead of sweetened drinks." :disabled="isReadOnly"></textarea>
              </Field>
              <Field label="Intervention notes">
                <textarea v-model="i.intervention_notes" class="nm-input" :maxlength="TMAX.intervention_notes" rows="2" placeholder="Education given, goals agreed with the patient…" :disabled="isReadOnly"></textarea>
              </Field>
              <NcpExtraRows :rows="i.extra" :templates="MEASURE_TEMPLATES.intervention" :read-only="isReadOnly" empty="Add a sodium limit, fluid limit, fiber goal, activity… — pick from the list or type your own." />
            </section>

            <!-- MONITORING (follow-ups) -->
            <section v-else-if="stepKey === 'monitoring'">
              <p class="phase">Phase 4 · Monitoring &amp; evaluation</p>
              <div v-if="ctx.previous" class="prev-box">
                <span class="k">Goals from the {{ shortDate(ctx.previous.encounter_date) }} record</span>
                <p v-if="ctx.previous.pes_problem"><strong>{{ ctx.previous.pes_problem }}</strong><template v-if="ctx.previous.pes_etiology"> related to {{ ctx.previous.pes_etiology }}</template>.</p>
                <p v-if="ctx.previous.diet_prescription">{{ ctx.previous.diet_prescription }}</p>
                <p v-if="ctx.previous.target_kcal" class="c-sub">Target {{ whole(ctx.previous.target_kcal) }} kcal/day</p>
                <div class="since">
                  <div><span class="k">Weight since then</span><strong>{{ ctx.previous.weight_change_kg != null ? `${signed(ctx.previous.weight_change_kg)} kg` : '—' }}</strong></div>
                  <div><span class="k">Meal-plan adherence · 7 days</span><strong>{{ ctx.adherence?.pct != null ? `${ctx.adherence.pct}%` : '—' }}</strong></div>
                </div>
              </div>
              <Field label="Were those goals met?" required group>
                <div class="goals">
                  <button v-for="g in GOALS" :key="g.value" type="button" class="goal" :class="{ on: m.goal_status === g.value }" :disabled="isReadOnly" @click="m.goal_status = g.value">{{ g.label }}</button>
                </div>
              </Field>
              <Field label="Monitoring notes">
                <textarea v-model="m.monitoring_notes" class="nm-input" :maxlength="TMAX.monitoring_notes" rows="3" placeholder="Response to the plan, barriers, what to change next…" :disabled="isReadOnly"></textarea>
              </Field>
            </section>

            <!-- REVIEW -->
            <section v-else-if="stepKey === 'review'">
              <p class="phase">{{ isReadOnly ? 'Summary' : 'Review & finalize' }}</p>
              <div v-if="!isReadOnly && missing.length" class="missing">
                <p><AlertTriangle :size="15" /> Still needed before you can finalize:</p>
                <ul><li v-for="x in missing" :key="x.label">{{ x.label }} <button type="button" class="nm-panel-link" @click="tab = x.step">Fix →</button></li></ul>
              </div>
              <dl class="summary">
                <div><dt>Measurements</dt><dd>{{ measureLine }}</dd></div>
                <div><dt>Diagnosis</dt><dd>{{ d.pes_problem ? pesSentence : '—' }}</dd></div>
                <div><dt>Prescription</dt><dd>{{ i.diet_prescription || '—' }}</dd></div>
                <div><dt>Targets</dt><dd>{{ targetLine }}</dd></div>
                <div v-if="showMonitoring"><dt>Goal status</dt><dd>{{ GOALS.find(g => g.value === m.goal_status)?.label || '—' }}</dd></div>
              </dl>
              <template v-if="isFinalized">
                <p class="done"><CheckCircle2 :size="16" /> This record is finalized.</p>
                <NuxtLink v-if="!inline" :to="`/meal-planning?relationship=${relationshipId}&edit=1`" class="nm-btn-dark nm-btn-sm" @click="emit('close')">Create / update meal plan →</NuxtLink>
              </template>
              <p v-else-if="!isReadOnly && !missing.length" class="nm-hint">Everything required is filled in. Finalizing makes this record permanent — it can't be edited afterwards.</p>
            </section>
          </div>

          <!-- PATIENT STRIP -->
          <aside v-if="!inline || showStripInline" class="strip" :class="{ open: stripOpen }">
            <p class="strip-name">{{ ctx.patient?.name }}</p>
            <p class="c-sub">{{ [ctx.patient?.age != null ? `${ctx.patient.age} y/o` : null, SEX[ctx.patient?.sex]].filter(Boolean).join(' · ') }}</p>
            <p v-if="ctx.patient?.allergies.length" class="allergy"><AlertTriangle :size="13" /> Allergy: {{ ctx.patient.allergies.join(', ') }}</p>
            <dl class="strip-facts">
              <div><dt>Conditions</dt><dd>{{ list(ctx.patient?.conditions) }}</dd></div>
              <div><dt>Diet</dt><dd>{{ list(ctx.patient?.dietary_restrictions) }}</dd></div>
              <div v-if="ctx.patient?.religion"><dt>Religion</dt><dd>{{ ctx.patient.religion }}</dd></div>
              <div><dt>Goals</dt><dd>{{ list(ctx.patient?.health_goals) }}</dd></div>
            </dl>
            <template v-if="ctx.screening">
              <p class="strip-k">Screening · {{ shortDate(ctx.screening.date) }}</p>
              <dl class="strip-facts">
                <div><dt>BMI</dt><dd>{{ ctx.screening.bmi ?? '—' }} <small>{{ ctx.screening.bmi_category }}</small></dd></div>
                <div><dt>NRS-2002</dt><dd :class="{ risk: (ctx.screening.nrs_score ?? 0) >= 3 }">{{ ctx.screening.nrs_score ?? '—' }} <small>{{ ctx.screening.nrs_risk }}</small></dd></div>
                <div><dt>TDEE</dt><dd>{{ whole(ctx.screening.tdee_kcal) }} kcal</dd></div>
                <div v-if="ctx.screening.symptoms"><dt>Symptoms</dt><dd>{{ ctx.screening.symptoms }}</dd></div>
              </dl>
            </template>
            <template v-if="ctx.meal_plan">
              <p class="strip-k">Current meal plan</p>
              <p class="c-sub">{{ ctx.meal_plan.name }}{{ ctx.meal_plan.target_kcal ? ` · ${whole(ctx.meal_plan.target_kcal)} kcal` : '' }}</p>
            </template>
            <template v-if="ctx.adherence">
              <p class="strip-k">Adherence · 7 days</p>
              <p class="c-sub">{{ ctx.adherence.pct != null ? `${ctx.adherence.pct}% · ${ctx.adherence.logged} of ${ctx.adherence.planned} meals logged` : 'Nothing due yet' }}</p>
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
            <button v-else-if="!isReadOnly" type="button" class="nm-btn-gold" :disabled="saving || missing.length > 0 || errorCount > 0" @click="confirmFinalize = true">Finalize record</button>
            <button v-else-if="isReadOnly && record?.status === 'draft' && canContinue" type="button" class="nm-btn-dark" @click="emit('continue')">Continue record</button>
            <button v-else-if="!inline" type="button" class="nm-btn-dark" @click="emit('close')">Close</button>
          </div>
        </footer>
      </template>

      <!-- CONFIRM: finalize -->
      <div v-if="confirmFinalize" class="inner-overlay" @click.self="confirmFinalize = false">
        <div class="nm-modal" role="alertdialog" aria-labelledby="fin-title">
          <h3 id="fin-title" class="nm-modal-title">Finalize this NCP record?</h3>
          <p class="nm-modal-text">It becomes part of {{ patientName }}'s permanent record and can't be edited or deleted afterwards. Any changes are saved first.</p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" @click="confirmFinalize = false">Not yet</button>
            <button type="button" class="nm-btn-gold" :disabled="saving" @click="finalize">{{ saving ? 'Finalizing…' : 'Finalize record' }}</button>
          </div>
        </div>
      </div>

      <!-- CONFIRM: unsaved changes -->
      <div v-if="confirmLeave" class="inner-overlay" @click.self="confirmLeave = false">
        <div class="nm-modal" role="alertdialog" aria-labelledby="leave-title">
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
import { AlertTriangle, Check, CheckCircle2, Info, Lock, Save, Sparkles, X } from 'lucide-vue-next'
import {
  KCAL_PER_G, MEASURE_TEMPLATES, NCP_LIMITS as L, NCP_TEXT_MAX as TMAX, PES_TERMS, bmiClass, bmiOf, extraRowErrors, macroKcal, rangeError, suggestMacros,
} from '~/utils/ncp'

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
  props: { label: String, required: Boolean, hint: String, group: Boolean, error: String },
  setup(p, { slots }) {
    return () => h(p.group ? 'div' : 'label', { class: ['field', { invalid: !!p.error }], role: p.group ? 'group' : undefined, 'aria-label': p.group ? p.label : undefined }, [
      h('span', { class: 'field-label' }, [p.label, p.required ? h('span', { class: 'req', 'aria-hidden': 'true' }, ' *') : null]),
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
const subtitle = computed(() => {
  const kind = isFollowUp.value ? 'Follow-up record' : 'Initial record'
  return record.value?.created_at ? `${kind} · started ${dateTime(record.value.created_at)}` : `${kind} · new`
})
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
    extra: (r.intervention_extra || []).map(x => ({ ...x })),
  }
  m.value = { goal_status: r.goal_status ?? '', monitoring_notes: r.monitoring_notes ?? '' }
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
    })
    carried.value = true
  }
}
function srcHint(f) {
  const s = ctx.value.prefill?.[f]
  if (!s || isReadOnly.value || !prefilledFields.value.includes(f)) return ''
  return `From their ${s.source}, ${shortDate(s.date)}`
}

/* ---------- live clinical help ---------- */
// Only from in-range values — an impossible weight mustn't show a BMI.
const liveBmi = computed(() => (rangeError('weight_kg', a.value.weight_kg) || rangeError('height_cm', a.value.height_cm) ? null : bmiOf(a.value.weight_kg, a.value.height_cm)))
const macroTotal = computed(() => macroKcal({ carb: i.value.target_carb_g, protein: i.value.target_protein_g, fat: i.value.target_fat_g }))
const macroDiffPct = computed(() => {
  const t = Number(i.value.target_kcal)
  return t && macroTotal.value ? Math.round(Math.abs(macroTotal.value - t) / t * 100) : 0
})
const macroOff = computed(() => macroDiffPct.value > 10)
function macroHint(k) {
  const g = Number(i.value[{ carb: 'target_carb_g', protein: 'target_protein_g', fat: 'target_fat_g' }[k]])
  const t = Number(i.value.target_kcal)
  return g && t ? `${Math.round(g * KCAL_PER_G[k] / t * 100)}% of kcal` : ''
}
function applySplit() {
  const s = suggestMacros(i.value.target_kcal)
  if (s) Object.assign(i.value, { target_carb_g: s.carb, target_protein_g: s.protein, target_fat_g: s.fat })
}
const pesSentence = computed(() => !filled(d.value.pes_problem) && !filled(d.value.pes_etiology) && !filled(d.value.pes_signs)
  ? 'Fill in the problem, etiology and signs to build the statement.'
  : `${d.value.pes_problem || '…'}${d.value.pes_etiology ? ` related to ${d.value.pes_etiology}` : ''}${d.value.pes_signs ? `, as evidenced by ${d.value.pes_signs}` : ''}.`)

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

/* ---------- required fields (mirrors NcpRecord.finalize_missing) ---------- */
const filled = v => String(v ?? '').trim() !== ''
const missing = computed(() => {
  const idx = k => stepKeys.value.indexOf(k)
  const out = []
  if (!filled(a.value.height_cm) || !filled(a.value.weight_kg)) out.push({ label: 'Height and weight', step: idx('assessment') })
  if (!filled(d.value.pes_problem)) out.push({ label: 'PES problem', step: idx('diagnosis') })
  if (!filled(d.value.pes_etiology) || !filled(d.value.pes_signs)) out.push({ label: 'PES etiology and signs', step: idx('diagnosis') })
  if (!filled(i.value.target_kcal)) out.push({ label: 'Target kcal', step: idx('intervention') })
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
  return e
})
const errorCount = computed(() => Object.keys(errors.value).length)
const ERROR_STEP = {
  height_cm: 'assessment', weight_kg: 'assessment', blood_pressure: 'assessment', blood_glucose: 'assessment', hba1c: 'assessment', assessment_extra: 'assessment',
  target_kcal: 'intervention', target_carb_g: 'intervention', target_protein_g: 'intervention', target_fat_g: 'intervention', intervention_extra: 'intervention',
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
].filter(Boolean).join(' · ') || '—')
const targetLine = computed(() => {
  const t = i.value
  if (!filled(t.target_kcal)) return '—'
  const macros = [filled(t.target_carb_g) ? `${t.target_carb_g} g carbs` : null, filled(t.target_protein_g) ? `${t.target_protein_g} g protein` : null, filled(t.target_fat_g) ? `${t.target_fat_g} g fat` : null].filter(Boolean)
  return `${whole(t.target_kcal)} kcal/day${macros.length ? ` · ${macros.join(', ')}` : ''}`
})

/* ---------- save / finalize ---------- */
let savedSnapshot = ''
const snapshot = () => JSON.stringify([a.value, d.value, i.value, m.value])
const dirty = computed(() => !isReadOnly.value && snapshot() !== savedSnapshot)
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
    pes_problem: d.value.pes_problem || null, pes_etiology: d.value.pes_etiology || null, pes_signs: d.value.pes_signs || null,
    target_kcal: num(i.value.target_kcal), target_carb_g: num(i.value.target_carb_g), target_protein_g: num(i.value.target_protein_g),
    target_fat_g: num(i.value.target_fat_g), diet_prescription: i.value.diet_prescription || null,
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
    savedSnapshot = sent
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
    savedSnapshot = snapshot()
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
defineExpose({ dirty, requestClose })

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
      savedSnapshot = record.value ? before : snapshot()
      const first = missing.value[0]
      tab.value = first ? first.step : (record.value ? stepKeys.value.length - 1 : 0)
    }
    if (props.mode === 'view') savedSnapshot = snapshot()
  } catch {
    loadError.value = 'Could not load this NCP record. Please try again.'
  } finally {
    isLoading.value = false
  }
}
onMounted(load)

/* ---------- helpers ---------- */
const list = l => (l?.length ? l.join(', ') : '—')
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
.ncp { position: relative; background: #fff; border-radius: 16px; width: 100%; max-width: 1080px; max-height: calc(100vh - 32px); display: flex; flex-direction: column; font-family: 'Inter', sans-serif; color: #1a3a1a; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2); overflow: hidden; }
.ncp.is-inline { max-width: none; max-height: none; height: 100%; box-shadow: none; border: 1px solid #eceeec; }
.ncp-inline { height: 100%; }
.pad { padding: 20px 24px; }

.ncp-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 18px 24px 12px; border-bottom: 1px solid #f0f2f0; }
.ncp-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; margin: 0; }
.ncp-sub { font-size: 0.8rem; color: #8a9a8a; margin: 2px 0 0; }
.ncp-head-right { display: flex; align-items: center; gap: 10px; }
.save-state { font-size: 0.74rem; font-weight: 600; color: #8a9a8a; white-space: nowrap; }
.save-state.dirty { color: #9a6a00; }
.save-state.ok { color: #1f6f46; }
.icon-x { border: none; background: none; color: #6a7a6a; cursor: pointer; padding: 4px; border-radius: 6px; display: flex; }
.icon-x:hover { background: #f2f5f2; }

.steps { display: flex; gap: 4px; padding: 10px 24px; border-bottom: 1px solid #f0f2f0; overflow-x: auto; }
.step { display: inline-flex; align-items: center; gap: 7px; border: none; background: none; padding: 7px 12px 7px 7px; border-radius: 999px; font-family: inherit; font-size: 0.8rem; font-weight: 600; color: #6a7a6a; cursor: pointer; white-space: nowrap; }
.step:hover { background: #f7f9f7; }
.step.active { background: #14301a; color: #fff; }
.step-dot { width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; background: #eceeec; color: #6a7a6a; }
.step.done .step-dot { background: #1f8f5c; color: #fff; }
.step.partial .step-dot { background: #fdf1d6; color: #8a6a00; }
.step.ready .step-dot { background: #D4A017; color: #1a3a1a; }
.step.active .step-dot { box-shadow: 0 0 0 2px #14301a, 0 0 0 3px rgba(255, 255, 255, 0.6); }

.ncp-body { display: grid; grid-template-columns: minmax(0, 1fr) 280px; flex: 1; min-height: 0; }
.ncp.is-inline .ncp-body { grid-template-columns: minmax(0, 1fr); }
.ncp-form { padding: 18px 24px 24px; overflow-y: auto; min-width: 0; }
.phase { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #b8860b; margin: 0 0 12px; }
.banner { display: flex; align-items: center; gap: 8px; background: #f4f6f4; border-radius: 8px; padding: 9px 12px; font-size: 0.82rem; color: #4a5a4a; margin: 0 0 14px; }
.banner.lock { background: #e3f3ea; color: #1f6f46; }
.hint-box { display: flex; gap: 8px; align-items: flex-start; background: #f3f8f4; border: 1px solid #dcebe0; border-radius: 8px; padding: 9px 12px; font-size: 0.8rem; color: #2f5f3f; margin: 0 0 14px; }
.strip-toggle { display: none; }

.grid { display: grid; gap: 12px; margin-bottom: 4px; }
.g3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.g4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
:deep(.field) { display: flex; flex-direction: column; gap: 5px; margin-bottom: 12px; min-width: 0; }
:deep(.field-label) { font-size: 0.8rem; font-weight: 600; color: #1a3a1a; }
:deep(.req) { color: #c0392b; }
:deep(.field-hint) { font-size: 0.72rem; color: #8a9a8a; }
:deep(.field-error) { font-size: 0.72rem; color: #c0392b; font-weight: 600; }
:deep(.field.invalid .nm-input) { border-color: #e0a3a3; background: #fffafa; }
.step.err .step-dot { background: #fdecec; color: #a12525; }
.foot-err { flex-basis: 100%; display: flex; align-items: center; gap: 6px; margin: 0 0 4px; font-size: 0.78rem; font-weight: 600; color: #a12525; }
.bp { display: flex; align-items: center; gap: 6px; }
.bp span { color: #8a9a8a; }
.computed { background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 8px 12px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 12px; }
.computed strong { font-size: 1.15rem; font-variant-numeric: tabular-nums; }
.k { font-size: 0.66rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; }
.c-sub { font-size: 0.74rem; color: #8a9a8a; margin: 0; }

.combo { position: relative; }
.combo-list { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; right: 0; max-height: 260px; overflow-y: auto; background: #fff; border: 1px solid #d5dad5; border-radius: 10px; box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12); padding: 6px; }
.combo-group { font-size: 0.64rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; margin: 6px 8px 2px; }
.combo-opt { display: block; width: 100%; text-align: left; border: none; background: none; padding: 7px 8px; border-radius: 6px; font-family: inherit; font-size: 0.84rem; color: #1a3a1a; cursor: pointer; }
.combo-opt:hover, .combo-opt.on { background: #eef3ec; }
.pes-preview, .prev-box, .energy { background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 12px 14px; margin: 4px 0 14px; }
.pes-preview p, .prev-box p { margin: 4px 0 0; font-size: 0.86rem; line-height: 1.5; }
.energy { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 16px; }
.energy div { display: flex; flex-direction: column; }
.energy strong { font-size: 1rem; }
.energy .c-sub { grid-column: 1 / -1; }
.macro-line { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; font-size: 0.8rem; color: #4a5a4a; background: #f3f8f4; border-radius: 8px; padding: 8px 12px; margin: -2px 0 14px; }
.macro-line.warn { background: #fdf6e3; color: #7a5a00; }
.since { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 10px; }
.since div { display: flex; flex-direction: column; }
.goals { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.goal { border: 1px solid #d5dad5; background: #fff; border-radius: 8px; padding: 9px 6px; font-family: inherit; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; cursor: pointer; }
.goal.on { background: #14301a; border-color: #14301a; color: #fff; }


.missing { background: #fdf6e3; border: 1px solid #f0dca0; border-radius: 10px; padding: 10px 14px; margin-bottom: 14px; font-size: 0.84rem; color: #7a5a00; }
.missing p { display: flex; gap: 6px; align-items: center; margin: 0 0 4px; font-weight: 600; }
.missing ul { margin: 0; padding-left: 20px; line-height: 1.8; }
.summary { margin: 0 0 14px; }
.summary div { display: grid; grid-template-columns: 120px minmax(0, 1fr); gap: 12px; padding: 9px 0; border-top: 1px solid #f0f2f0; }
.summary div:first-child { border-top: none; }
.summary dt { font-size: 0.76rem; color: #8a9a8a; margin: 0; }
.summary dd { margin: 0; font-size: 0.86rem; line-height: 1.5; overflow-wrap: anywhere; }
.done { display: flex; align-items: center; gap: 6px; color: #1f6f46; font-weight: 600; font-size: 0.86rem; }

.strip { border-left: 1px solid #f0f2f0; background: #fbfcfb; padding: 18px 18px 24px; overflow-y: auto; }
.strip-name { font-weight: 700; margin: 0; font-size: 0.95rem; }
.allergy { display: flex; align-items: center; gap: 5px; margin: 8px 0 0; font-size: 0.78rem; font-weight: 600; color: #8a5a00; background: #fdf1d6; border-radius: 8px; padding: 6px 8px; }
.strip-k { font-size: 0.64rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; margin: 16px 0 6px; }
.strip-facts { margin: 10px 0 0; }
.strip-facts div { padding: 5px 0; }
.strip-facts dt { font-size: 0.7rem; color: #8a9a8a; margin: 0; }
.strip-facts dd { margin: 0; font-size: 0.82rem; font-weight: 600; overflow-wrap: anywhere; }
.strip-facts dd small { font-weight: 500; color: #6a7a6a; }
.strip-facts dd.risk { color: #a12525; }

.ncp-foot { display: flex; justify-content: space-between; gap: 10px; padding: 12px 24px; border-top: 1px solid #f0f2f0; background: #fff; flex-wrap: wrap; }
.foot-right { display: flex; gap: 8px; flex-wrap: wrap; }
.foot-right .nm-btn-outline { display: inline-flex; align-items: center; gap: 6px; }
.inner-overlay { position: absolute; inset: 0; background: rgba(10, 25, 15, 0.35); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 30; }

@media (max-width: 900px) {
  .ncp-body { grid-template-columns: minmax(0, 1fr); }
  .strip { display: none; border-left: none; border-bottom: 1px solid #f0f2f0; }
  .strip.open { display: block; grid-row: 1; }
  .strip-toggle { display: inline-flex; align-items: center; gap: 6px; border: 1px solid #d5dad5; background: #fff; border-radius: 8px; padding: 6px 10px; font-family: inherit; font-size: 0.78rem; font-weight: 600; color: #1a3a1a; cursor: pointer; margin: 0 0 12px; }
  .g4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 560px) {
  .ncp-head, .steps, .ncp-form, .ncp-foot { padding-left: 16px; padding-right: 16px; }
  .g3 { grid-template-columns: minmax(0, 1fr); }
  .goals { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .summary div { grid-template-columns: minmax(0, 1fr); gap: 2px; }
  .ncp-foot { flex-direction: column-reverse; }
  .foot-right { width: 100%; }
  .foot-right > * { flex: 1; justify-content: center; }
}
</style>
