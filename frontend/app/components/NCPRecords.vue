<template>
  <div class="ncp-page">
    <div v-if="loadError" class="form-error">{{ loadError }}</div>
    <p v-else-if="isLoading" class="empty-note">Loading…</p>

    <!-- ================= CROSS-PATIENT LIST (no ?relationship= in context) ================= -->
    <template v-else-if="!relationshipId">
      <div class="toolbar">
        <div class="search-box-wide">
          <Search :size="16" class="search-icon" />
          <input v-model="search" type="text" placeholder="Search by name or ID....." />
        </div>
        <select v-model="statusFilter" class="filter-select">
          <option value="All Status">All Status</option>
          <option>Complete</option>
          <option>In Progress</option>
        </select>
      </div>

      <div class="history-section">
        <h3 class="history-title">NCP Records</h3>
        <div class="table-wrap">
          <table class="history-table">
            <thead>
              <tr>
                <th>PATIENT</th>
                <th>PHASE</th>
                <th>DATE</th>
                <th>STATUS</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="h in filteredAllRecords" :key="h.id" class="clickable-row" @click="navigateTo(`/ncp-records?relationship=${h.relationship_id}`)">
                <td class="patient-cell">
                  <div class="history-avatar">{{ h.initials }}</div>
                  <div>
                    <p class="history-name">{{ h.client_name }}</p>
                  </div>
                </td>
                <td>{{ h.phaseLabel }}</td>
                <td>{{ formatHistoryDate(h.updated_at) }}</td>
                <td><span class="status-pill" :class="historyStatusClass(h.displayStatus)">{{ h.displayStatus }}</span></td>
              </tr>
            </tbody>
          </table>
          <p v-if="!filteredAllRecords.length" class="empty-note table-empty">No NCP records match your filters yet.</p>
        </div>
      </div>
    </template>

    <!-- ================= SINGLE-PATIENT OVERVIEW ================= -->
    <template v-else>
      <div>
        <!-- TOOLBAR -->
        <div class="toolbar">
          <div class="search-box-wide">
            <Search :size="16" class="search-icon" />
            <input v-model="search" type="text" placeholder="Search by name or ID....." />
          </div>
          <select v-model="statusFilter" class="filter-select">
            <option value="All Status">All Status</option>
            <option>Complete</option>
            <option>In Progress</option>
            <option>Pending</option>
          </select>
          <select v-model="phaseFilter" class="filter-select">
            <option value="All NCP Phases">All NCP Phases</option>
            <option v-for="s in steps" :key="s.label" :value="s.label">{{ s.label }}</option>
          </select>
          <button class="new-record-btn" @click="openRecordModal(0)">
            <Plus :size="15" /> New NCP Record
          </button>
        </div>

        <!-- PATIENT HEADER -->
        <div class="record-header">
          <div class="record-header-left">
            <h2 class="record-patient-name">{{ patientName }}</h2>
            <span class="tag" :class="record?.status === 'completed' ? 'tag-active' : 'tag-dark'">{{ record?.status === 'completed' ? 'Finalized Record' : 'Draft Record' }}</span>
          </div>
          <p class="record-meta">Encounter Date: {{ encounterDate }}</p>
        </div>

        <!-- PHASE SUMMARY CARDS -->
        <div class="phase-cards">
          <div
            v-for="(step, index) in steps"
            :key="step.label"
            class="phase-card"
            :class="phaseCardClass(index)"
            @click="openRecordModal(index)"
          >
            <div class="phase-card-number" :class="phaseNumberClass(index)">
              <Check v-if="phaseStatus(index) === 'Complete'" :size="15" />
              <span v-else>{{ index + 1 }}</span>
            </div>
            <div class="phase-card-body">
              <p class="phase-card-title">{{ step.fullLabel }}</p>
              <p class="phase-card-desc">{{ phaseSummary(index) }}</p>
            </div>
            <span class="phase-status-pill" :class="phaseStatusClass(index)">{{ phaseStatus(index) }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- ================= NEW / CONTINUE NCP RECORD MODAL ================= -->
    <div v-if="showNewRecordModal" class="modal-overlay" @click.self="closeNewRecordModal">
      <div class="modal-box">
        <div class="modal-header">
          <div>
            <h2 class="modal-title">Nutrition Care Process</h2>
            <p class="modal-sub">Complete all 4 NCP phases</p>
          </div>
          <div class="modal-patient-chip">
            <span class="modal-patient-avatar">{{ newRecordInitials }}</span>
            {{ patientName }}
          </div>
        </div>

        <!-- TABS -->
        <div class="modal-tabs">
          <button
            v-for="(step, index) in steps"
            :key="step.label"
            class="modal-tab"
            :class="{ active: newRecordTab === index }"
            @click="newRecordTab = index"
          >
            {{ index + 1 }}. {{ step.label }}
          </button>
        </div>

        <p v-if="saveError" class="form-error">{{ saveError }}</p>
        <p v-if="isFinalized" class="info-banner finalized-banner">
          <Lock :size="15" class="info-icon" /> This record is finalized and can no longer be edited.
        </p>

        <!-- TAB 1: ASSESSMENT -->
        <div v-if="newRecordTab === 0" class="modal-body">
          <span class="modal-eyebrow">PHASE 1 — NUTRITIONAL ASSESSMENT</span>

          <div class="modal-field-grid-3">
            <div>
              <label class="field-label">Height (cm)</label>
              <input v-model="assessment.height_cm" type="number" step="0.1" class="field-input" :disabled="isFinalized" />
            </div>
            <div>
              <label class="field-label">Weight (kg)</label>
              <input v-model="assessment.weight_kg" type="number" step="0.1" class="field-input" :disabled="isFinalized" />
            </div>
            <div>
              <label class="field-label">HbA1c (%) <span class="optional">(optional)</span></label>
              <input v-model="assessment.hba1c" type="number" step="0.1" class="field-input" :disabled="isFinalized" />
            </div>
          </div>

          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">Blood Pressure</label>
              <input v-model="assessment.blood_pressure" type="text" class="field-input" placeholder="e.g. 120/80" :disabled="isFinalized" />
            </div>
            <div>
              <label class="field-label">Blood Glucose (mg/dL)</label>
              <input v-model="assessment.blood_glucose" type="number" step="0.1" class="field-input" :disabled="isFinalized" />
            </div>
          </div>

          <label class="field-label">Lab Notes <span class="optional">(optional)</span></label>
          <textarea v-model="assessment.lab_notes" class="field-textarea" rows="2" placeholder="Clinical observations..." :disabled="isFinalized"></textarea>

          <label class="field-label">Assessment Notes</label>
          <textarea v-model="assessment.assessment_notes" class="field-textarea" rows="2" :disabled="isFinalized"></textarea>

          <div class="extra-section">
            <div class="extra-header">
              <span class="field-label extra-title">Additional Measurements <span class="optional">(optional)</span></span>
              <button v-if="!isFinalized" type="button" class="extra-add-btn" @click="addExtra(assessment.extra)"><Plus :size="14" /> Add Field</button>
            </div>
            <p v-if="!assessment.extra.length" class="extra-empty">Add any measurement not listed above, e.g. waist circumference, cholesterol, creatinine.</p>
            <div v-for="(row, idx) in assessment.extra" :key="idx" class="extra-row">
              <input v-model="row.label" type="text" class="field-input" list="assessment-extra-labels" placeholder="Measurement" maxlength="100" :disabled="isFinalized" @change="fillUnit(row, ASSESSMENT_SUGGESTIONS)" />
              <input v-model="row.value" type="text" class="field-input" placeholder="Value" maxlength="500" :disabled="isFinalized" />
              <input v-model="row.unit" type="text" class="field-input extra-unit" placeholder="Unit" maxlength="30" :disabled="isFinalized" />
              <button v-if="!isFinalized" type="button" class="extra-remove-btn" title="Remove" @click="assessment.extra.splice(idx, 1)"><X :size="14" /></button>
            </div>
            <datalist id="assessment-extra-labels">
              <option v-for="s in ASSESSMENT_SUGGESTIONS" :key="s.label" :value="s.label" />
            </datalist>
          </div>

          <div class="auto-results-box">
            <span class="auto-results-label">COMPUTED · WHO ASIA-PACIFIC BMI</span>
            <div class="auto-results-grid single">
              <div class="auto-result-item">
                <p class="auto-result-value">{{ record?.bmi ?? '—' }}</p>
                <p class="auto-result-label">BMI (from saved record)</p>
              </div>
            </div>
          </div>

          <button class="modal-continue-btn" :disabled="isSaving || isFinalized" @click="saveAndContinue(1)">{{ isSaving ? 'Saving…' : 'Save and Continue to Diagnosis' }}</button>
        </div>

        <!-- TAB 2: DIAGNOSIS -->
        <div v-if="newRecordTab === 1" class="modal-body">
          <span class="modal-eyebrow">PHASE 2 — NUTRITION DIAGNOSIS (PES STATEMENT)</span>

          <label class="field-label">Problem (P)</label>
          <input v-model="diagnosis.pes_problem" type="text" class="field-input" :disabled="isFinalized" />

          <label class="field-label">Etiology / Related to (E)</label>
          <textarea v-model="diagnosis.pes_etiology" class="field-textarea" rows="2" placeholder="e.g High intake of refined carbohydrates..." :disabled="isFinalized"></textarea>

          <label class="field-label">Signs &amp; Symptoms (S)</label>
          <textarea v-model="diagnosis.pes_signs" class="field-textarea" rows="2" placeholder="e.g as evidenced by..." :disabled="isFinalized"></textarea>

          <div class="pes-generated-box">
            <span class="pes-generated-label">AUTO-GENERATED PES STATEMENT</span>
            <p class="pes-generated-text">
              {{ diagnosis.pes_problem || '…' }}<span v-if="diagnosis.pes_etiology"> related to {{ diagnosis.pes_etiology }}</span><span v-if="diagnosis.pes_signs"> as evidenced by {{ diagnosis.pes_signs }}</span>.
            </p>
          </div>

          <div class="modal-actions">
            <button class="modal-back-btn" @click="newRecordTab = 0">Back</button>
            <button class="modal-continue-btn" :disabled="isSaving || isFinalized" @click="saveAndContinue(2)">{{ isSaving ? 'Saving…' : 'Save and Continue to Intervention' }}</button>
          </div>
        </div>

        <!-- TAB 3: INTERVENTION -->
        <div v-if="newRecordTab === 2" class="modal-body">
          <span class="modal-eyebrow">PHASE 3 — NUTRITION INTERVENTION</span>

          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">Target kcal/day</label>
              <input v-model="intervention.target_kcal" type="number" step="1" class="field-input" :disabled="isFinalized" />
            </div>
            <div>
              <label class="field-label">Target Protein (g)</label>
              <input v-model="intervention.target_protein_g" type="number" step="1" class="field-input" :disabled="isFinalized" />
            </div>
          </div>

          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">Target Carbs (g)</label>
              <input v-model="intervention.target_carb_g" type="number" step="1" class="field-input" :disabled="isFinalized" />
            </div>
            <div>
              <label class="field-label">Target Fat (g)</label>
              <input v-model="intervention.target_fat_g" type="number" step="1" class="field-input" :disabled="isFinalized" />
            </div>
          </div>

          <label class="field-label">Diet Prescription Notes</label>
          <textarea v-model="intervention.diet_prescription" class="field-textarea" rows="3" placeholder="e.g. Low-GI, high-fiber Filipino diet. Reduce rice to 1/2 cup per meal. Include ampalaya, sayote, kangkong daily......." :disabled="isFinalized"></textarea>

          <label class="field-label">Intervention Notes <span class="optional">(optional)</span></label>
          <textarea v-model="intervention.intervention_notes" class="field-textarea" rows="2" :disabled="isFinalized"></textarea>

          <div class="extra-section">
            <div class="extra-header">
              <span class="field-label extra-title">Additional Intervention Items <span class="optional">(optional)</span></span>
              <button v-if="!isFinalized" type="button" class="extra-add-btn" @click="addExtra(intervention.extra)"><Plus :size="14" /> Add Field</button>
            </div>
            <p v-if="!intervention.extra.length" class="extra-empty">Add any prescription item not listed above, e.g. fluid or sodium limits, supplements, activity goals.</p>
            <div v-for="(row, idx) in intervention.extra" :key="idx" class="extra-row">
              <input v-model="row.label" type="text" class="field-input" list="intervention-extra-labels" placeholder="Item" maxlength="100" :disabled="isFinalized" @change="fillUnit(row, INTERVENTION_SUGGESTIONS)" />
              <input v-model="row.value" type="text" class="field-input" placeholder="Value / details" maxlength="500" :disabled="isFinalized" />
              <input v-model="row.unit" type="text" class="field-input extra-unit" placeholder="Unit" maxlength="30" :disabled="isFinalized" />
              <button v-if="!isFinalized" type="button" class="extra-remove-btn" title="Remove" @click="intervention.extra.splice(idx, 1)"><X :size="14" /></button>
            </div>
            <datalist id="intervention-extra-labels">
              <option v-for="s in INTERVENTION_SUGGESTIONS" :key="s.label" :value="s.label" />
            </datalist>
          </div>

          <div class="linked-plan-banner">
            <Paperclip :size="15" class="info-icon" />
            Meal plans for this patient are managed separately —
            <a href="#" class="linked-plan-link" @click.prevent="navigateTo(`/meal-planning?relationship=${relationshipId}`)">Open Meal Plan Builder →</a>
          </div>

          <div class="modal-actions">
            <button class="modal-back-btn" @click="newRecordTab = 1">Back</button>
            <button class="modal-continue-btn" :disabled="isSaving || isFinalized" @click="saveAndContinue(3)">{{ isSaving ? 'Saving…' : 'Save and Continue to Monitoring' }}</button>
          </div>
        </div>

        <!-- TAB 4: MONITORING -->
        <div v-if="newRecordTab === 3" class="modal-body">
          <span class="modal-eyebrow">PHASE 4 — MONITORING &amp; EVALUATION</span>

          <label class="field-label">Goal Status</label>
          <div class="goal-status-grid">
            <button
              v-for="g in goalOptions"
              :key="g.value"
              class="goal-status-btn"
              :class="{ active: monitoring.goal_status === g.value }"
              :disabled="isFinalized"
              @click="monitoring.goal_status = g.value"
            >
              {{ g.label }}
            </button>
          </div>

          <label class="field-label">Monitoring Notes</label>
          <textarea v-model="monitoring.monitoring_notes" class="field-textarea" rows="4" placeholder="Observations on patient progress, clinical response, next steps........" :disabled="isFinalized"></textarea>

          <div class="modal-actions">
            <button class="modal-back-btn" @click="newRecordTab = 2">Back</button>
            <button class="modal-continue-btn" :disabled="isSaving || isFinalized" @click="saveDraft">{{ isSaving ? 'Saving…' : 'Save as Draft' }}</button>
          </div>

          <!-- FINALIZE PANEL -->
          <div v-if="!isFinalized" class="finalize-panel">
            <div class="finalize-header">
              <Lock :size="18" class="finalize-icon" />
              <div>
                <p class="finalize-title">Finalize This Record</p>
                <p class="finalize-desc">
                  Once finalized, this NCP record becomes permanent and cannot be edited. All four phases must have required fields completed before finalizing.
                </p>
              </div>
            </div>

            <div class="checklist">
              <span v-for="c in checklist" :key="c.label" class="check-pill" :class="{ 'check-done': c.done }">
                <Check :size="12" /> {{ c.label }}
              </span>
            </div>

            <button class="finalize-btn" :disabled="!allChecksPassed || isSaving" @click="finalizeRecordFromModal">Finalize NCP Record</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Check, Paperclip, Lock, Search, Plus, X } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'NCP Record' })

const route = useRoute()
const { get, post, patch } = useApi()

// Reactive, not a plain const — clicking a row in the cross-patient list
// navigates here via navigateTo() with only the query string changing,
// which reuses this same component instance (no full remount), so this
// must update on its own rather than being captured once at setup.
const relationshipId = computed(() => route.query.relationship)
const record = ref(null)
const patientName = ref('this patient')
const isLoading = ref(true)
const isSaving = ref(false)
const loadError = ref('')
const saveError = ref('')

// ---- DESIGN PORTED FROM feature/landing-julia (2026-09-21), then the old
// 4-phase step-tracker "edit mode" was dropped in favor of the New/Continue
// NCP Record modal below (2026-09-24) — the modal is now the only way to
// create or edit a record, wired to the same real /rnd/ncp/... endpoints
// the old wizard used.
const encounterDate = computed(() =>
  record.value?.encounter_date
    ? new Date(record.value.encounter_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
)
const isFinalized = computed(() => record.value?.status === 'completed')

const steps = [
  { label: 'Assessment', fullLabel: 'Nutrition Assessment' },
  { label: 'Diagnosis', fullLabel: 'Nutrition Diagnosis' },
  { label: 'Intervention', fullLabel: 'Nutrition Intervention' },
  { label: 'Monitoring', fullLabel: 'Nutrition Monitoring & Evaluation' }
]

/* ---------- OVERVIEW: TOOLBAR STATE ---------- */
const search = ref('')
const statusFilter = ref('All Status')
const phaseFilter = ref('All NCP Phases')

/* ---------- OVERVIEW: PHASE STATUS DERIVATION ---------- */
// Derived from the record's own saved fields (not a "current step" cursor,
// since editing now happens in the modal, not a linear wizard). A phase is
// Complete once its required field(s) are filled in, In Progress once
// something in an earlier phase exists but this one is still empty and no
// later phase has data either, otherwise Pending. Finalized records read
// every phase as Complete.
const phaseHasData = [
  () => !!(assessment.value.weight_kg && assessment.value.height_cm),
  () => !!diagnosis.value.pes_problem,
  () => !!intervention.value.diet_prescription,
  () => !!monitoring.value.goal_status,
]
function phaseStatus(index) {
  if (isFinalized.value) return 'Complete'
  if (phaseHasData[index]()) return 'Complete'
  const firstIncomplete = phaseHasData.findIndex(has => !has())
  if (index === firstIncomplete) return 'In Progress'
  return 'Pending'
}
function phaseStatusClass(index) {
  const status = phaseStatus(index)
  if (status === 'Complete') return 'status-complete'
  if (status === 'In Progress') return 'status-progress'
  return 'status-pending'
}
function phaseCardClass(index) {
  const status = phaseStatus(index)
  if (status === 'Complete') return 'card-complete'
  if (status === 'In Progress') return 'card-progress'
  return 'card-pending'
}
function phaseNumberClass(index) {
  const status = phaseStatus(index)
  if (status === 'Complete') return 'number-complete'
  if (status === 'In Progress') return 'number-progress'
  return 'number-pending'
}

// Summary line per phase, built from the real record fields (main's schema,
// not the branch's mock field names).
function phaseSummary(index) {
  if (index === 0) {
    const a = assessment.value
    const extra = extrasText(a.extra)
    if (!a.weight_kg && !a.height_cm && !a.assessment_notes && !extra) return 'No assessment data yet.'
    return `Wt ${a.weight_kg || '—'}kg, Ht ${a.height_cm || '—'}cm, BP ${a.blood_pressure || '—'}, Glucose ${a.blood_glucose || '—'} mg/dL.${extra ? ` ${extra}.` : ''} ${a.assessment_notes || ''}`.trim()
  }
  if (index === 1) {
    const d = diagnosis.value
    if (!d.pes_problem) return 'No diagnosis documented yet.'
    return `${d.pes_problem} related to ${d.pes_etiology || '…'} as evidenced by ${d.pes_signs || '…'}.`
  }
  if (index === 2) {
    const i = intervention.value
    const extra = extrasText(i.extra)
    if (!i.diet_prescription && !extra) return 'No intervention plan yet.'
    return `${i.diet_prescription || ''} Targets: ${i.target_kcal || '—'} kcal, ${i.target_protein_g || '—'}g protein, ${i.target_carb_g || '—'}g carbs, ${i.target_fat_g || '—'}g fat.${extra ? ` ${extra}.` : ''}`.trim()
  }
  const m = monitoring.value
  if (!m.monitoring_notes) return 'Not started yet.'
  return `Goal status: ${m.goal_status || '—'}. ${m.monitoring_notes}`
}

const assessment = ref({ weight_kg: '', height_cm: '', blood_pressure: '', blood_glucose: '', hba1c: '', lab_notes: '', assessment_notes: '', extra: [] })
const diagnosis = ref({ pes_problem: '', pes_etiology: '', pes_signs: '' })
const intervention = ref({ diet_prescription: '', target_kcal: '', target_protein_g: '', target_carb_g: '', target_fat_g: '', intervention_notes: '', extra: [] })

// Suggestions for the "+ Add Field" rows — the RND can also type any label.
// Picking one pre-fills its usual unit.
const ASSESSMENT_SUGGESTIONS = [
  { label: 'Waist circumference', unit: 'cm' },
  { label: 'Hip circumference', unit: 'cm' },
  { label: 'Mid-upper arm circumference (MUAC)', unit: 'cm' },
  { label: 'Body fat', unit: '%' },
  { label: 'Total cholesterol', unit: 'mg/dL' },
  { label: 'LDL cholesterol', unit: 'mg/dL' },
  { label: 'HDL cholesterol', unit: 'mg/dL' },
  { label: 'Triglycerides', unit: 'mg/dL' },
  { label: 'Serum creatinine', unit: 'mg/dL' },
  { label: 'eGFR', unit: 'mL/min/1.73m²' },
  { label: 'Serum potassium', unit: 'mmol/L' },
  { label: 'Serum sodium', unit: 'mmol/L' },
  { label: 'Serum albumin', unit: 'g/dL' },
  { label: 'Hemoglobin', unit: 'g/dL' },
  { label: 'Uric acid', unit: 'mg/dL' },
]
const INTERVENTION_SUGGESTIONS = [
  { label: 'Fluid restriction', unit: 'L/day' },
  { label: 'Sodium limit', unit: 'mg/day' },
  { label: 'Potassium limit', unit: 'mg/day' },
  { label: 'Phosphorus limit', unit: 'mg/day' },
  { label: 'Fiber goal', unit: 'g/day' },
  { label: 'Water intake goal', unit: 'glasses/day' },
  { label: 'Meal frequency', unit: 'meals/day' },
  { label: 'Supplement', unit: '' },
  { label: 'Physical activity', unit: 'min/day' },
  { label: 'Nutrition education topic', unit: '' },
]
function localIsoDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function addExtra(list) {
  list.push({ label: '', value: '', unit: '' })
}
function fillUnit(row, suggestions) {
  const match = suggestions.find(s => s.label.toLowerCase() === row.label.trim().toLowerCase())
  if (match && !row.unit) row.unit = match.unit
}
function extrasText(list) {
  return (list || [])
    .filter(r => r.label && r.value)
    .map(r => `${r.label}: ${r.value}${r.unit ? ` ${r.unit}` : ''}`)
    .join(', ')
}
const goalOptions = [
  { value: 'met', label: 'Met' },
  { value: 'partially_met', label: 'Partially Met' },
  { value: 'not_met', label: 'Not Met' },
  { value: 'ongoing', label: 'Ongoing' },
]
const monitoring = ref({ goal_status: '', monitoring_notes: '' })

const computedBmi = computed(() => {
  const w = parseFloat(assessment.value.weight_kg)
  const hCm = parseFloat(assessment.value.height_cm)
  if (!w || !hCm) return '—'
  const hM = hCm / 100
  const bmi = w / (hM * hM)
  let category = 'Normal'
  if (bmi < 18.5) category = 'Underweight'
  else if (bmi >= 23 && bmi < 25) category = 'Overweight (At Risk)'
  else if (bmi >= 25) category = 'Obese'
  return `${bmi.toFixed(1)} — ${category}`
})

function hydrateFromRecord(r) {
  assessment.value = {
    weight_kg: r.weight_kg ?? '', height_cm: r.height_cm ?? '', blood_pressure: r.blood_pressure ?? '',
    blood_glucose: r.blood_glucose ?? '', hba1c: r.hba1c ?? '', lab_notes: r.lab_notes ?? '', assessment_notes: r.assessment_notes ?? '',
    extra: (r.assessment_extra || []).map(row => ({ ...row })),
  }
  diagnosis.value = { pes_problem: r.pes_problem ?? '', pes_etiology: r.pes_etiology ?? '', pes_signs: r.pes_signs ?? '' }
  intervention.value = {
    diet_prescription: r.diet_prescription ?? '', target_kcal: r.target_kcal ?? '', target_protein_g: r.target_protein_g ?? '',
    target_carb_g: r.target_carb_g ?? '', target_fat_g: r.target_fat_g ?? '', intervention_notes: r.intervention_notes ?? '',
    extra: (r.intervention_extra || []).map(row => ({ ...row })),
  }
  monitoring.value = { goal_status: r.goal_status ?? '', monitoring_notes: r.monitoring_notes ?? '' }
}

function buildPayload() {
  const num = (v) => (v === '' || v === null || v === undefined ? null : v)
  return {
    weight_kg: num(assessment.value.weight_kg), height_cm: num(assessment.value.height_cm),
    blood_pressure: assessment.value.blood_pressure || null, blood_glucose: num(assessment.value.blood_glucose),
    hba1c: num(assessment.value.hba1c), lab_notes: assessment.value.lab_notes || null,
    assessment_notes: assessment.value.assessment_notes || null,
    assessment_extra: assessment.value.extra.filter(r => r.label.trim()),
    pes_problem: diagnosis.value.pes_problem || null, pes_etiology: diagnosis.value.pes_etiology || null,
    pes_signs: diagnosis.value.pes_signs || null,
    diet_prescription: intervention.value.diet_prescription || null, target_kcal: num(intervention.value.target_kcal),
    target_protein_g: num(intervention.value.target_protein_g), target_carb_g: num(intervention.value.target_carb_g),
    target_fat_g: num(intervention.value.target_fat_g), intervention_notes: intervention.value.intervention_notes || null,
    intervention_extra: intervention.value.extra.filter(r => r.label.trim()),
    monitoring_notes: monitoring.value.monitoring_notes || null, goal_status: monitoring.value.goal_status || null,
  }
}

const checklist = computed(() => [
  { label: 'Weight & Height recorded', done: !!assessment.value.weight_kg && !!assessment.value.height_cm },
  { label: 'PES Problem documented', done: !!diagnosis.value.pes_problem },
  { label: 'Diet Prescription set', done: !!intervention.value.diet_prescription },
])
const allChecksPassed = computed(() => checklist.value.every(c => c.done))

async function loadRecord() {
  isLoading.value = true
  loadError.value = ''
  try {
    const [profile, records] = await Promise.all([
      get(`/rnd/relationships/${relationshipId.value}/client-profile/`),
      get(`/rnd/relationships/${relationshipId.value}/ncp/`),
    ])
    patientName.value = `${profile.user.first_name} ${profile.user.last_name}`
    if (records.length) {
      // Prefer an in-progress draft over an older finalized record — a
      // relationship can end up with more than one NcpRecord (e.g. a new
      // draft started after a prior one was finalized), and records are
      // ordered by encounter_date, which ties don't reliably break in
      // draft's favor. Without this, "Resume" from the dashboard could
      // land on a locked, finalized record instead of the actual draft.
      record.value = records.find(r => r.status === 'draft') || records[0]
      hydrateFromRecord(record.value)
    }
  } catch {
    loadError.value = 'Could not load this patient\'s NCP record. Please go back and try again.'
  } finally {
    isLoading.value = false
  }
}

async function saveDraft() {
  isSaving.value = true
  saveError.value = ''
  try {
    const payload = buildPayload()
    if (record.value) {
      record.value = await patch(`/rnd/ncp/${record.value.id}/`, payload)
    } else {
      record.value = await post(`/rnd/relationships/${relationshipId.value}/ncp/`, {
        relationship: Number(relationshipId.value),
        // Local (PHT) date — toISOString() would give yesterday before 8 AM.
        encounter_date: localIsoDate(new Date()),
        ...payload,
      })
    }
  } catch {
    saveError.value = 'Could not save this record. Please try again.'
  } finally {
    isSaving.value = false
  }
}

async function finalizeRecord() {
  if (!allChecksPassed.value || !record.value) return
  isSaving.value = true
  saveError.value = ''
  try {
    await saveDraft()
    record.value = await patch(`/rnd/ncp/${record.value.id}/finalize/`)
  } catch {
    saveError.value = 'Could not finalize this record. Please try again.'
  } finally {
    isSaving.value = false
  }
}
async function finalizeRecordFromModal() {
  await finalizeRecord()
  if (!saveError.value) showNewRecordModal.value = false
}

/* ---------- NEW / CONTINUE NCP RECORD MODAL ---------- */
const showNewRecordModal = ref(false)
const newRecordTab = ref(0)

const newRecordInitials = computed(() =>
  (patientName.value || '')
    .split(' ')
    .map(n => n[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
)

function openRecordModal(index = 0) {
  newRecordTab.value = index
  saveError.value = ''
  showNewRecordModal.value = true
}
function closeNewRecordModal() {
  showNewRecordModal.value = false
}
async function saveAndContinue(nextTab) {
  await saveDraft()
  if (!saveError.value) newRecordTab.value = nextTab
}

/* ---------- CROSS-PATIENT LIST (shown when no ?relationship= is in
   context — e.g. the sidebar/a bookmark, not a specific patient's chart).
   Reuses RndNcpDraftListView with ?status=all so this and the dashboard's
   "resume a draft" panel share one endpoint instead of two near-duplicates. ---------- */
const allRecords = ref([])

const phaseOrder = ['Assessment', 'Diagnosis', 'Intervention', 'Monitoring']
function phaseLabelFor(r) {
  if (r.status === 'completed') return 'Monitoring'
  const hasData = [
    !!(r.weight_kg && r.height_cm),
    !!r.pes_problem,
    !!r.diet_prescription,
    !!r.goal_status,
  ]
  const firstIncomplete = hasData.findIndex(has => !has)
  return phaseOrder[firstIncomplete === -1 ? phaseOrder.length - 1 : firstIncomplete]
}
function initialsFor(name) {
  return (name || '').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}
function formatHistoryDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
function historyStatusClass(status) {
  if (status === 'Completed') return 'pill-green'
  if (status === 'In Progress') return 'pill-gold'
  return 'pill-muted'
}

const decoratedAllRecords = computed(() =>
  allRecords.value.map(r => ({
    ...r,
    initials: initialsFor(r.client_name),
    phaseLabel: phaseLabelFor(r),
    displayStatus: r.status === 'completed' ? 'Completed' : 'In Progress',
  }))
)
const filteredAllRecords = computed(() => {
  const q = search.value.trim().toLowerCase()
  return decoratedAllRecords.value.filter(r => {
    const matchesSearch = !q || r.client_name.toLowerCase().includes(q)
    const matchesStatus = statusFilter.value === 'All Status'
      || (statusFilter.value === 'Complete' && r.displayStatus === 'Completed')
      || (statusFilter.value === 'In Progress' && r.displayStatus === 'In Progress')
    return matchesSearch && matchesStatus
  })
})

async function loadAllRecords() {
  isLoading.value = true
  loadError.value = ''
  try {
    allRecords.value = await get('/rnd/ncp/drafts/?status=all')
  } catch {
    loadError.value = 'Could not load your NCP records. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

watch(relationshipId, (id) => {
  if (!id) {
    loadAllRecords()
    return
  }
  // Reset previous patient's state before loading the new one — this
  // component instance is reused across a row-click navigation (query
  // string change only, no remount), so stale data would otherwise flash.
  record.value = null
  patientName.value = 'this patient'
  hydrateFromRecord({})
  showNewRecordModal.value = false
  loadRecord()
}, { immediate: true })
</script>

<style scoped>
* { box-sizing: border-box; }

.ncp-page { font-family: 'Inter', sans-serif; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.empty-note { font-size: 0.85rem; color: #9aaa9a; }

/* ============ OVERVIEW ============ */
.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.search-box-wide {
  flex: 1; min-width: 220px; display: flex; align-items: center; gap: 10px; background: #fff;
  border: 1.0px solid #a8b3a8; border-radius: 10px; padding: 11px 16px;
}
.search-box-wide input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; color: #4a5a4a; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }
.filter-select { border: 1px solid #e5e8e5; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; color: #4a5a4a; background: #fff; cursor: pointer; }
.new-record-btn {
  display: flex; align-items: center; gap: 6px; background: #14301a; color: #fff; border: none;
  border-radius: 8px; padding: 11px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; white-space: nowrap;
}

.record-header { margin-bottom: 16px; }
.record-header-left { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.record-patient-name { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0; }
.tag { font-size: 0.7rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.tag-active { background: #e3f3ea; color: #1f8f5c; }
.tag-dark { background: #14301a; color: #fff; }
.record-meta { font-size: 0.78rem; color: #9aaa9a; margin: 0; }

/* PHASE CARDS */
.phase-cards { display: flex; flex-direction: column; gap: 14px; margin-bottom: 28px; }
.phase-card {
  display: flex; align-items: flex-start; gap: 16px; background: #fff; border-radius: 10px;
  border: 1px solid #eceeec; border-left-width: 4px; padding: 18px 20px; cursor: pointer;
  transition: box-shadow 0.15s ease;
}
.phase-card:hover { box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.card-complete { border-left-color: #1f8f5c; }
.card-progress { border-left-color: #D4A017; }
.card-pending { border-left-color: #d5dad5; }

.phase-card-number {
  width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.82rem; flex-shrink: 0; margin-top: 2px;
}
.number-complete { background: #1f8f5c; color: #fff; }
.number-progress { background: #D4A017; color: #1a3a1a; }
.number-pending { background: #eceeec; color: #9aaa9a; }

.phase-card-body { flex: 1; }
.phase-card-title { font-weight: 700; color: #1a3a1a; font-size: 0.95rem; margin: 0 0 4px; }
.phase-card-desc { font-size: 0.82rem; color: #6a7a6a; margin: 0; line-height: 1.5; }

.phase-status-pill { font-size: 0.72rem; font-weight: 700; padding: 4px 12px; border-radius: 14px; white-space: nowrap; flex-shrink: 0; margin-top: 2px; }
.status-complete { background: #e3f3ea; color: #1f8f5c; }
.status-progress { background: #fdf1d6; color: #b8860b; }
.status-pending { background: #eceeec; color: #9aaa9a; }

/* HISTORY */
.history-section { margin-top: 8px; }
.history-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 14px; }
.table-wrap { background: #fff; border-radius: 14px; border: 1px solid #eceeec; overflow-x: auto; }
.history-table { width: 100%; border-collapse: collapse; }
.history-table th { text-align: left; font-size: 0.7rem; letter-spacing: 0.05em; color: #9aaa9a; font-weight: 700; padding: 14px 16px 10px; border-bottom: 1px solid #eceeec; }
.history-table td { padding: 14px 16px; border-bottom: 1px solid #f2f4f2; font-size: 0.86rem; color: #2a2a2a; }
.history-table tr:last-child td { border-bottom: none; }
.clickable-row { cursor: pointer; transition: background 0.1s ease; }
.clickable-row:hover { background: #f7f9f7; }
.patient-cell { display: flex; align-items: center; gap: 10px; }
.history-avatar { width: 30px; height: 30px; border-radius: 50%; background: #eceeec; color: #4a5a4a; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; flex-shrink: 0; }
.history-name { font-weight: 700; color: #1a3a1a; margin: 0; }
.history-id { font-size: 0.7rem; color: #9aaa9a; margin: 0; }
.status-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-gold { background: #fdf1d6; color: #b8860b; }
.pill-muted { background: #eceeec; color: #8a9a8a; }
.table-empty { padding: 40px 16px; text-align: center; }

/* ============ SHARED FIELD/BANNER STYLES (used inside the modal) ============ */
.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #2a2a2a; margin: 0 0 6px; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input, .field-textarea {
  width: 100%; border: 1px solid #e5e8e5; border-radius: 8px; padding: 11px 14px;
  font-size: 0.86rem; color: #2a2a2a; background: #fff; font-family: inherit; margin-bottom: 4px;
}
.field-input:disabled, .field-textarea:disabled { background: #f4f6f4; color: #6a7a6a; }
.field-textarea { resize: vertical; margin-bottom: 18px; }

.extra-section { border-top: 1px dashed #e5e8e5; padding-top: 14px; margin-bottom: 18px; }
.extra-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.extra-title { margin: 0; }
.extra-add-btn {
  display: inline-flex; align-items: center; gap: 4px; border: 1px solid #1f8f5c; color: #1f8f5c;
  background: #fff; border-radius: 8px; padding: 6px 12px; font-size: 0.8rem; font-weight: 600; cursor: pointer;
}
.extra-add-btn:hover { background: #e3f3ea; }
.extra-empty { font-size: 0.78rem; color: #9aaa9a; margin: 0; }
.extra-row { display: grid; grid-template-columns: 1.3fr 1fr 0.6fr auto; gap: 8px; align-items: center; margin-bottom: 6px; }
.extra-row .field-input { margin-bottom: 0; }
.extra-remove-btn {
  display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px;
  border: 1px solid #f0d6d6; border-radius: 8px; background: #fff; color: #c0392b; cursor: pointer;
}
.extra-remove-btn:hover { background: #fbeaea; }
@media (max-width: 600px) {
  .extra-row { grid-template-columns: 1fr 1fr; }
}

.info-banner {
  display: flex; align-items: center; gap: 8px; background: #eef1f6; border-radius: 8px;
  padding: 12px 16px; font-size: 0.82rem; color: #3a4a5a; margin-bottom: 20px;
}
.info-icon { color: #2a5a8a; flex-shrink: 0; }
.finalized-banner { background: #fdf8ee; color: #8a6a1a; }
.finalized-banner .info-icon { color: #b8860b; }

.linked-plan-banner {
  display: flex; align-items: center; gap: 8px; background: #eef1f6; border-radius: 8px;
  padding: 12px 16px; font-size: 0.82rem; color: #3a4a5a; margin: 4px 0 4px;
}
.linked-plan-link { color: #2a5a8a; font-weight: 600; text-decoration: underline; }

.goal-status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.goal-status-btn {
  border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 8px;
  padding: 12px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.goal-status-btn.active { border-color: #D4A017; color: #b8860b; background: #fdf8ee; font-weight: 700; }
.goal-status-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* ACTIONS */
/* FINALIZE PANEL */
.finalize-panel {
  background: #fdf8ee; border: 1px solid #f0dca8; border-radius: 12px; padding: 24px 28px; margin-top: 20px;
}
.finalize-header { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 16px; }
.finalize-icon { color: #b8860b; flex-shrink: 0; margin-top: 2px; }
.finalize-title { font-size: 1rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.finalize-desc { font-size: 0.84rem; color: #6a7a6a; margin: 0; line-height: 1.5; }

.checklist { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
.check-pill {
  display: flex; align-items: center; gap: 6px; background: #eceeec; color: #9aaa9a;
  font-size: 0.78rem; font-weight: 600; padding: 5px 12px; border-radius: 14px;
}
.check-pill.check-done { background: #e6efe0; color: #3a6b3a; }

.finalize-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 13px 24px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}
.finalize-btn:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 1024px) {
  .goal-status-grid { grid-template-columns: repeat(2, 1fr); }
}

/* ============ NEW / CONTINUE NCP RECORD MODAL ============ */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(20,30,20,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100; padding: 20px;
}
.modal-box {
  background: #fff; border-radius: 16px; width: 100%; max-width: 560px;
  max-height: 90vh; overflow-y: auto; padding: 28px;
}
.modal-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 18px; }
.modal-title { font-family: 'Playfair Display', serif; font-size: 1.3rem; color: #1a3a1a; margin: 0 0 4px; }
.modal-sub { font-size: 0.82rem; color: #8a9a8a; margin: 0; }
.modal-patient-chip {
  display: flex; align-items: center; gap: 8px; border: 1px solid #e5e8e5; border-radius: 20px;
  padding: 6px 14px 6px 6px; font-size: 0.82rem; font-weight: 700; color: #1a3a1a; white-space: nowrap;
}
.modal-patient-avatar {
  width: 26px; height: 26px; border-radius: 50%; background: #14301a; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; flex-shrink: 0;
}

.modal-tabs { display: flex; gap: 4px; border-bottom: 1px solid #eceeec; margin-bottom: 20px; overflow-x: auto; }
.modal-tab {
  border: none; background: none; padding: 10px 4px; margin-right: 20px; font-size: 0.82rem; font-weight: 600;
  color: #9aaa9a; cursor: pointer; border-bottom: 2px solid transparent; white-space: nowrap;
}
.modal-tab.active { color: #1f8f5c; border-bottom-color: #1f8f5c; font-weight: 700; }

.modal-body { display: flex; flex-direction: column; }
.modal-eyebrow { font-size: 0.68rem; letter-spacing: 0.08em; color: #b8860b; font-weight: 700; margin-bottom: 16px; }
.modal-field-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 16px; }
.modal-field-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin-bottom: 16px; }

.auto-results-box { background: #f4f8f5; border: 1px solid #dbe8dd; border-radius: 10px; padding: 16px; margin: 12px 0 20px; }
.auto-results-label { display: block; font-size: 0.66rem; letter-spacing: 0.06em; color: #6a8a70; font-weight: 700; margin-bottom: 12px; }
.auto-results-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.auto-results-grid.single { grid-template-columns: 1fr; max-width: 200px; }
.auto-result-item { background: #fff; border-radius: 8px; padding: 10px; text-align: center; }
.auto-result-value { font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.auto-result-label { font-size: 0.68rem; color: #9aaa9a; margin: 4px 0 0; }

.pes-generated-box { background: #fdf1d6; border: 1px solid #f0dca8; border-radius: 10px; padding: 14px 16px; margin: 16px 0 20px; }
.pes-generated-label { display: block; font-size: 0.66rem; letter-spacing: 0.06em; color: #b8860b; font-weight: 700; margin-bottom: 6px; }
.pes-generated-text { font-size: 0.85rem; color: #8a6a1a; font-style: italic; margin: 0; }

.modal-actions { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 4px; }
.modal-back-btn {
  border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 8px;
  padding: 11px 20px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.modal-continue-btn {
  flex: 1; background: #14301a; color: #fff; border: none; border-radius: 8px;
  padding: 12px 20px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}
</style>
