<template>
  <div class="ncp-page">
    <div v-if="loadError" class="form-error">{{ loadError }}</div>
    <p v-else-if="isLoading" class="empty-note">Loading…</p>

    <template v-else>
      <!-- ================= OVERVIEW MODE ================= -->
      <div v-if="viewMode === 'overview'">
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
          <button class="new-record-btn" @click="openNewRecordModal">
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
            @click="openPhase(index)"
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

        <!-- NCP HISTORY -->
        <div class="history-section">
          <h3 class="history-title">NCP History</h3>
          <div class="table-wrap">
            <table class="history-table">
              <thead>
                <tr>
                  <th>PATIENT</th>
                  <th>PHASE</th>
                  <th>DIETITIAN</th>
                  <th>DATE</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                <!-- No cross-patient NCP history endpoint yet — placeholder rows, ported as-is from the design source. -->
                <tr v-for="h in ncpHistory" :key="h.id">
                  <td class="patient-cell">
                    <div class="history-avatar">{{ h.initials }}</div>
                    <div>
                      <p class="history-name">{{ h.name }}</p>
                      <p class="history-id">#{{ h.id }}</p>
                    </div>
                  </td>
                  <td>{{ h.phase }}</td>
                  <td>{{ h.dietitian }}</td>
                  <td>{{ h.date }}</td>
                  <td><span class="status-pill" :class="historyStatusClass(h.status)">{{ h.status }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ================= EDIT MODE (4-phase wizard) ================= -->
      <div v-else>
        <!-- BREADCRUMB -->
        <p class="breadcrumb">
          <a href="#" @click.prevent="viewMode = 'overview'">NCP Records</a> /
          <span>{{ patientName }}</span> /
          <span>NCP Record</span>
        </p>

        <div class="ncp-header">
          <div>
            <h1 class="ncp-title">Nutrition Care Process</h1>
            <p class="ncp-sub">
              Patient: {{ patientName }} · Encounter Date: {{ encounterDate }}
              <span v-if="record" class="draft-pill" :class="{ 'completed-pill': record.status === 'completed' }">
                {{ record.status === 'completed' ? 'Finalized' : 'Draft' }}
              </span>
            </p>
          </div>
        </div>

        <!-- STEP TRACKER -->
        <div class="step-tracker">
          <template v-for="(step, index) in steps" :key="step.label">
            <div class="step-node">
              <div class="step-circle" :class="stepCircleClass(index)">
                <Check v-if="index < currentStep" :size="14" />
                <span v-else>{{ index + 1 }}</span>
              </div>
              <span class="step-label" :class="{ 'label-active': index === currentStep }">{{ step.label }}</span>
            </div>
            <div v-if="index < steps.length - 1" class="step-line" :class="{ 'line-done': index < currentStep }"></div>
          </template>
        </div>

        <p v-if="saveError" class="form-error">{{ saveError }}</p>
        <p v-if="isFinalized" class="info-banner finalized-banner">
          <Lock :size="15" class="info-icon" /> This record is finalized and can no longer be edited.
        </p>

        <!-- CARD -->
        <div class="ncp-card">
          <!-- PHASE 1: ASSESSMENT -->
          <div v-if="currentStep === 0">
            <span class="phase-eyebrow">— PHASE 1 — NUTRITIONAL ASSESSMENT</span>

            <div class="field-grid-4">
              <div>
                <label class="field-label">Weight (kg)</label>
                <input v-model="assessment.weight_kg" type="number" step="0.1" class="field-input" :disabled="isFinalized" />
              </div>
              <div>
                <label class="field-label">Height (cm)</label>
                <input v-model="assessment.height_cm" type="number" step="0.1" class="field-input" :disabled="isFinalized" />
              </div>
              <div>
                <label class="field-label">Blood Pressure</label>
                <input v-model="assessment.blood_pressure" type="text" class="field-input" placeholder="e.g. 120/80" :disabled="isFinalized" />
              </div>
              <div>
                <label class="field-label">Blood Glucose (mg/dL)</label>
                <input v-model="assessment.blood_glucose" type="number" step="0.1" class="field-input" :disabled="isFinalized" />
              </div>
            </div>

            <div class="field-grid-2">
              <div>
                <label class="field-label">HbA1c (%) <span class="optional">(optional)</span></label>
                <input v-model="assessment.hba1c" type="number" step="0.1" class="field-input" :disabled="isFinalized" />
              </div>
              <div>
                <label class="field-label">Computed BMI</label>
                <div class="computed-box">{{ computedBmi }}</div>
              </div>
            </div>

            <label class="field-label">Lab Notes <span class="optional">(optional)</span></label>
            <textarea v-model="assessment.lab_notes" class="field-textarea" rows="2" :disabled="isFinalized"></textarea>

            <label class="field-label">Assessment Notes</label>
            <textarea v-model="assessment.assessment_notes" class="field-textarea" rows="4" :disabled="isFinalized"></textarea>

            <div class="ncp-actions">
              <button class="save-draft-btn" :disabled="isSaving || isFinalized" @click="saveDraft"><Save :size="14" /> {{ isSaving ? 'Saving…' : 'Save as Draft' }}</button>
              <button class="continue-btn" @click="nextStep">Continue to Diagnosis <ArrowRight :size="15" /></button>
            </div>
          </div>

          <!-- PHASE 2: DIAGNOSIS (PES) -->
          <div v-if="currentStep === 1">
            <span class="phase-eyebrow">— PHASE 2 — NUTRITION DIAGNOSIS (PES STATEMENT)</span>

            <div class="info-banner">
              <Info :size="15" class="info-icon" />
              A PES statement follows the format: <strong>Problem</strong> related to <strong>Etiology</strong> as evidenced by <strong>Signs/Symptoms</strong>.
            </div>

            <label class="field-label">Problem (P)</label>
            <input v-model="diagnosis.pes_problem" type="text" class="field-input" :disabled="isFinalized" />

            <label class="field-label">Etiology (E) — "related to..."</label>
            <textarea v-model="diagnosis.pes_etiology" class="field-textarea" rows="2" :disabled="isFinalized"></textarea>

            <label class="field-label">Signs / Symptoms (S) — "as evidenced by..."</label>
            <textarea v-model="diagnosis.pes_signs" class="field-textarea" rows="2" :disabled="isFinalized"></textarea>

            <span class="preview-label">PREVIEW</span>
            <div class="pes-preview">
              <strong>{{ diagnosis.pes_problem || '…' }}</strong> related to <strong>{{ diagnosis.pes_etiology || '…' }}</strong>
              as evidenced by <strong>{{ diagnosis.pes_signs || '…' }}</strong>.
            </div>

            <div class="ncp-actions">
              <button class="back-btn" @click="prevStep"><ArrowLeft :size="14" /> Back</button>
              <div class="actions-right">
                <button class="save-draft-btn" :disabled="isSaving || isFinalized" @click="saveDraft"><Save :size="14" /> {{ isSaving ? 'Saving…' : 'Save as Draft' }}</button>
                <button class="continue-btn" @click="nextStep">Continue to Intervention <ArrowRight :size="15" /></button>
              </div>
            </div>
          </div>

          <!-- PHASE 3: INTERVENTION -->
          <div v-if="currentStep === 2">
            <span class="phase-eyebrow">— PHASE 3 — INTERVENTION</span>

            <label class="field-label">Diet Prescription</label>
            <textarea v-model="intervention.diet_prescription" class="field-textarea" rows="3" :disabled="isFinalized"></textarea>

            <span class="phase-eyebrow small-eyebrow">— MACRONUTRIENT TARGETS</span>
            <div class="field-grid-4">
              <div>
                <label class="field-label">Target kcal</label>
                <input v-model="intervention.target_kcal" type="number" step="1" class="field-input" :disabled="isFinalized" />
              </div>
              <div>
                <label class="field-label">Protein (g)</label>
                <input v-model="intervention.target_protein_g" type="number" step="1" class="field-input" :disabled="isFinalized" />
              </div>
              <div>
                <label class="field-label">Carbohydrate (g)</label>
                <input v-model="intervention.target_carb_g" type="number" step="1" class="field-input" :disabled="isFinalized" />
              </div>
              <div>
                <label class="field-label">Fat (g)</label>
                <input v-model="intervention.target_fat_g" type="number" step="1" class="field-input" :disabled="isFinalized" />
              </div>
            </div>

            <label class="field-label">Intervention Notes</label>
            <textarea v-model="intervention.intervention_notes" class="field-textarea" rows="4" :disabled="isFinalized"></textarea>

            <div class="linked-plan-banner">
              <Paperclip :size="15" class="info-icon" />
              Meal plans for this patient are managed separately —
              <a href="#" class="linked-plan-link" @click.prevent="navigateTo(`/meal-planning?relationship=${relationshipId}`)">Open Meal Plan Builder →</a>
            </div>

            <div class="ncp-actions">
              <button class="back-btn" @click="prevStep"><ArrowLeft :size="14" /> Back</button>
              <div class="actions-right">
                <button class="save-draft-btn" :disabled="isSaving || isFinalized" @click="saveDraft"><Save :size="14" /> {{ isSaving ? 'Saving…' : 'Save as Draft' }}</button>
                <button class="continue-btn" @click="nextStep">Continue to Monitoring <ArrowRight :size="15" /></button>
              </div>
            </div>
          </div>

          <!-- PHASE 4: MONITORING -->
          <div v-if="currentStep === 3">
            <span class="phase-eyebrow">— PHASE 4 — MONITORING &amp; EVALUATION</span>

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
            <textarea v-model="monitoring.monitoring_notes" class="field-textarea" rows="5" :disabled="isFinalized"></textarea>

            <div class="ncp-actions">
              <button class="back-btn" @click="prevStep"><ArrowLeft :size="14" /> Back</button>
              <button class="save-draft-btn" :disabled="isSaving || isFinalized" @click="saveDraft"><Save :size="14" /> {{ isSaving ? 'Saving…' : 'Save as Draft' }}</button>
            </div>
          </div>
        </div>

        <!-- FINALIZE PANEL (only visible on last step) -->
        <div v-if="currentStep === 3 && !isFinalized" class="finalize-panel">
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

          <button class="finalize-btn" :disabled="!allChecksPassed || isSaving" @click="finalizeRecord">Finalize NCP Record</button>
        </div>
      </div>
    </template>

    <!-- ================= NEW NCP RECORD MODAL ================= -->
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

        <!-- TAB 1: ASSESSMENT -->
        <div v-if="newRecordTab === 0" class="modal-body">
          <span class="modal-eyebrow">PHASE 1 — NUTRITIONAL ASSESSMENT</span>

          <div class="modal-field-grid-3">
            <div>
              <label class="field-label">Height (cm)</label>
              <input v-model="newAssessment.height" type="text" class="field-input" />
            </div>
            <div>
              <label class="field-label">Weight (kg)</label>
              <input v-model="newAssessment.weight" type="text" class="field-input" />
            </div>
            <div>
              <label class="field-label">Age</label>
              <input v-model="newAssessment.age" type="text" class="field-input" />
            </div>
          </div>

          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">Blood Pressure</label>
              <input v-model="newAssessment.bloodPressure" type="text" class="field-input" placeholder="e.g. 120/80 mmHg" />
            </div>
            <div>
              <label class="field-label">Blood Glucose (mg/dL)</label>
              <input v-model="newAssessment.bloodGlucose" type="text" class="field-input" />
            </div>
          </div>

          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">HbA1c (%)</label>
              <input v-model="newAssessment.hba1c" type="text" class="field-input" />
            </div>
            <div>
              <label class="field-label">eGFR (mL/min)</label>
              <input v-model="newAssessment.egfr" type="text" class="field-input" />
            </div>
          </div>

          <label class="field-label">Assessment Notes</label>
          <textarea v-model="newAssessment.notes" class="field-textarea" rows="2" placeholder="Clinical observations..."></textarea>

          <div class="auto-results-box">
            <span class="auto-results-label">AUTO-COMPUTED RESULTS · MIFFLIN-ST JEOR · WHO ASIA-PACIFIC</span>
            <div class="auto-results-grid">
              <div class="auto-result-item">
                <p class="auto-result-value">{{ newComputed.bmi }}</p>
                <p class="auto-result-sub">{{ newComputed.bmiCategory }}</p>
                <p class="auto-result-label">BMI</p>
              </div>
              <div class="auto-result-item">
                <p class="auto-result-value">{{ newComputed.bmr }}</p>
                <p class="auto-result-sub">kcal/day</p>
                <p class="auto-result-label">BMR</p>
              </div>
              <div class="auto-result-item">
                <p class="auto-result-value">{{ newComputed.tdee }}</p>
                <p class="auto-result-sub">kcal/day</p>
                <p class="auto-result-label">TDEE</p>
              </div>
              <div class="auto-result-item">
                <!-- TODO: NRS-2002 requires full clinical scoring criteria (weight loss %, intake reduction, disease severity) not yet captured here -->
                <p class="auto-result-value">{{ newComputed.nrs }}</p>
                <p class="auto-result-sub nrs-sub">{{ newComputed.nrsCategory }}</p>
                <p class="auto-result-label">NRS-2002</p>
              </div>
            </div>
          </div>

          <button class="modal-continue-btn" @click="newRecordTab = 1">Save and Continue to Diagnosis</button>
        </div>

        <!-- TAB 2: DIAGNOSIS -->
        <div v-if="newRecordTab === 1" class="modal-body">
          <span class="modal-eyebrow">PHASE 2 — NUTRITION DIAGNOSIS (PES STATEMENT)</span>

          <label class="field-label">Problem (P)</label>
          <input v-model="newDiagnosis.problem" type="text" class="field-input" />

          <label class="field-label">Etiology / Related to (E)</label>
          <textarea v-model="newDiagnosis.etiology" class="field-textarea" rows="2" placeholder="e.g High intake of refined carbohydrates..."></textarea>

          <label class="field-label">Signs &amp; Symptoms (S)</label>
          <textarea v-model="newDiagnosis.signs" class="field-textarea" rows="2" placeholder="e.g as evidenced by..."></textarea>

          <div class="pes-generated-box">
            <span class="pes-generated-label">AUTO-GENERATED PES STATEMENT</span>
            <p class="pes-generated-text">
              {{ newDiagnosis.problem || '…' }}<span v-if="newDiagnosis.etiology"> related to {{ newDiagnosis.etiology }}</span><span v-if="newDiagnosis.signs"> as evidenced by {{ newDiagnosis.signs }}</span>.
            </p>
          </div>

          <div class="modal-actions">
            <button class="modal-back-btn" @click="newRecordTab = 0">Back</button>
            <button class="modal-continue-btn" @click="newRecordTab = 2">Save and Continue to Intervention</button>
          </div>
        </div>

        <!-- TAB 3: INTERVENTION -->
        <div v-if="newRecordTab === 2" class="modal-body">
          <span class="modal-eyebrow">PHASE 3 — NUTRITION INTERVENTION</span>

          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">Target kcal/day</label>
              <input v-model="newIntervention.kcal" type="text" class="field-input" />
            </div>
            <div>
              <label class="field-label">Condition</label>
              <input v-model="newIntervention.condition" type="text" class="field-input" />
            </div>
          </div>

          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">Target Protein (g)</label>
              <input v-model="newIntervention.protein" type="text" class="field-input" />
            </div>
            <div>
              <label class="field-label">Target Carbs (g)</label>
              <input v-model="newIntervention.carbs" type="text" class="field-input" />
            </div>
          </div>

          <label class="field-label">Diet Prescription Notes</label>
          <textarea v-model="newIntervention.notes" class="field-textarea" rows="3" placeholder="e.g. Low-GI, high-fiber Filipino diet. Reduce rice to 1/2 cup per meal. Include amplaya, sayote, kangkong daily......."></textarea>

          <div class="modal-actions">
            <button class="modal-back-btn" @click="newRecordTab = 1">Back</button>
            <button class="modal-continue-btn" @click="newRecordTab = 3">Save and Continue to Intervention</button>
          </div>
        </div>

        <!-- TAB 4: MONITORING -->
        <div v-if="newRecordTab === 3" class="modal-body">
          <span class="modal-eyebrow">PHASE 4 — MONITORING &amp; EVALUATION</span>

          <label class="field-label">Goal Status</label>
          <input v-model="newMonitoring.goalStatus" type="text" class="field-input" />

          <label class="field-label">Next Follow-up Date</label>
          <input v-model="newMonitoring.followUpDate" type="date" class="field-input" />

          <label class="field-label">Monitoring Notes</label>
          <textarea v-model="newMonitoring.notes" class="field-textarea" rows="4" placeholder="Observations on patient progress, clinical response, next steps........"></textarea>

          <div class="modal-actions">
            <button class="modal-back-btn" @click="newRecordTab = 2">Back</button>
            <button class="modal-continue-btn" @click="submitNewRecord">Submit NCP Record</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Check, Save, ArrowRight, ArrowLeft, Info, Paperclip, Lock, Search, Plus } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'NCP Record' })

const route = useRoute()
const { get, post, patch } = useApi()

const relationshipId = route.query.relationship
const record = ref(null)
const patientName = ref('this patient')
const isLoading = ref(true)
const isSaving = ref(false)
const loadError = ref('')
const saveError = ref('')

// ---- DESIGN PORTED FROM feature/landing-julia (2026-09-21). The Overview
// mode (phase cards + history table) and "New NCP Record" modal are new —
// the modal is still fully mock/local-only, including its own client-side
// BMI/BMR/TDEE/NRS-2002 calculations (with known placeholder issues: male-only
// Mifflin-St Jeor coefficients, a fixed 1.375 activity factor, no real NRS-2002
// score). Main's real, verified calculation engine lives in
// backend clinical/services.py and is NOT used by this modal yet — wiring
// the modal to real data/endpoints is a deliberate later pass, not done here.
const viewMode = ref('overview') // 'overview' | 'edit'

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

const currentStep = ref(0)

/* ---------- OVERVIEW: TOOLBAR STATE ---------- */
const search = ref('')
const statusFilter = ref('All Status')
const phaseFilter = ref('All NCP Phases')

function openPhase(index) {
  currentStep.value = index
  viewMode.value = 'edit'
}

function stepCircleClass(index) {
  if (index < currentStep.value) return 'circle-done'
  if (index === currentStep.value) return 'circle-active'
  return 'circle-upcoming'
}
function nextStep() {
  if (currentStep.value < steps.length - 1) currentStep.value++
}
function prevStep() {
  if (currentStep.value > 0) currentStep.value--
}

/* ---------- OVERVIEW: PHASE STATUS DERIVATION ---------- */
// A phase before the current step is Complete, the current step is In
// Progress (unless finalized), later phases are Pending. Once the record
// is finalized, every phase reads as Complete.
function phaseStatus(index) {
  if (isFinalized.value) return 'Complete'
  if (index < currentStep.value) return 'Complete'
  if (index === currentStep.value) return 'In Progress'
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
    if (!a.weight_kg && !a.height_cm && !a.assessment_notes) return 'No assessment data yet.'
    return `Wt ${a.weight_kg || '—'}kg, Ht ${a.height_cm || '—'}cm, BP ${a.blood_pressure || '—'}, Glucose ${a.blood_glucose || '—'} mg/dL. ${a.assessment_notes || ''}`.trim()
  }
  if (index === 1) {
    const d = diagnosis.value
    if (!d.pes_problem) return 'No diagnosis documented yet.'
    return `${d.pes_problem} related to ${d.pes_etiology || '…'} as evidenced by ${d.pes_signs || '…'}.`
  }
  if (index === 2) {
    const i = intervention.value
    if (!i.diet_prescription) return 'No intervention plan yet.'
    return `${i.diet_prescription} Targets: ${i.target_kcal || '—'} kcal, ${i.target_protein_g || '—'}g protein, ${i.target_carb_g || '—'}g carbs, ${i.target_fat_g || '—'}g fat.`
  }
  const m = monitoring.value
  if (!m.monitoring_notes) return 'Not started yet.'
  return `Goal status: ${m.goal_status || '—'}. ${m.monitoring_notes}`
}

const assessment = ref({ weight_kg: '', height_cm: '', blood_pressure: '', blood_glucose: '', hba1c: '', lab_notes: '', assessment_notes: '' })
const diagnosis = ref({ pes_problem: '', pes_etiology: '', pes_signs: '' })
const intervention = ref({ diet_prescription: '', target_kcal: '', target_protein_g: '', target_carb_g: '', target_fat_g: '', intervention_notes: '' })
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
  }
  diagnosis.value = { pes_problem: r.pes_problem ?? '', pes_etiology: r.pes_etiology ?? '', pes_signs: r.pes_signs ?? '' }
  intervention.value = {
    diet_prescription: r.diet_prescription ?? '', target_kcal: r.target_kcal ?? '', target_protein_g: r.target_protein_g ?? '',
    target_carb_g: r.target_carb_g ?? '', target_fat_g: r.target_fat_g ?? '', intervention_notes: r.intervention_notes ?? '',
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
    pes_problem: diagnosis.value.pes_problem || null, pes_etiology: diagnosis.value.pes_etiology || null,
    pes_signs: diagnosis.value.pes_signs || null,
    diet_prescription: intervention.value.diet_prescription || null, target_kcal: num(intervention.value.target_kcal),
    target_protein_g: num(intervention.value.target_protein_g), target_carb_g: num(intervention.value.target_carb_g),
    target_fat_g: num(intervention.value.target_fat_g), intervention_notes: intervention.value.intervention_notes || null,
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
      get(`/rnd/relationships/${relationshipId}/client-profile/`),
      get(`/rnd/relationships/${relationshipId}/ncp/`),
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
      record.value = await post(`/rnd/relationships/${relationshipId}/ncp/`, {
        relationship: Number(relationshipId),
        encounter_date: new Date().toISOString().slice(0, 10),
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
    viewMode.value = 'overview'
  } catch {
    saveError.value = 'Could not finalize this record. Please try again.'
  } finally {
    isSaving.value = false
  }
}

/* ---------- NEW NCP RECORD MODAL (mock/local only — see note above) ---------- */
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

function openNewRecordModal() {
  newRecordTab.value = 0
  showNewRecordModal.value = true
}
function closeNewRecordModal() {
  showNewRecordModal.value = false
}

const newAssessment = ref({
  height: '', weight: '', age: '', bloodPressure: '', bloodGlucose: '', hba1c: '', egfr: '', notes: ''
})
const newDiagnosis = ref({ problem: '', etiology: '', signs: '' })
const newIntervention = ref({ kcal: '', condition: '', protein: '', carbs: '', notes: '' })
const newMonitoring = ref({ goalStatus: '', followUpDate: '', notes: '' })

// TODO: gender isn't captured in this modal yet — Mifflin-St Jeor needs it.
// Defaulting to male coefficients until a gender field/patient record is wired in.
// This whole block is a placeholder — main's verified engine lives in
// backend clinical/services.py and isn't called from here yet.
const newComputed = computed(() => {
  const w = parseFloat(newAssessment.value.weight)
  const hCm = parseFloat(newAssessment.value.height)
  const age = parseFloat(newAssessment.value.age)

  if (!w || !hCm) {
    return { bmi: '—', bmiCategory: '', bmr: '—', tdee: '—', nrs: '—', nrsCategory: '' }
  }

  const hM = hCm / 100
  const bmiVal = w / (hM * hM)
  let bmiCategory = 'Normal'
  if (bmiVal < 18.5) bmiCategory = 'Underweight'
  else if (bmiVal >= 25 && bmiVal < 30) bmiCategory = 'Overweight'
  else if (bmiVal >= 30) bmiCategory = 'Obese'

  let bmr = '—'
  let tdee = '—'
  if (age) {
    const bmrVal = 10 * w + 6.25 * hCm - 5 * age + 5
    bmr = Math.round(bmrVal)
    tdee = Math.round(bmrVal * 1.375) // TODO: replace 1.375 placeholder activity factor with real patient activity level
  }

  // TODO: NRS-2002 is a full clinical screening tool (weight-loss %, intake
  // reduction, disease severity). This is a placeholder, not a real score.
  const nrs = '—'
  const nrsCategory = ''

  return { bmi: bmiVal.toFixed(1), bmiCategory, bmr, tdee, nrs, nrsCategory }
})

function submitNewRecord() {
  // Wire this up to your real create-NCP-record API call
  console.log('Submitting new NCP record', {
    assessment: newAssessment.value,
    diagnosis: newDiagnosis.value,
    intervention: newIntervention.value,
    monitoring: newMonitoring.value
  })
  showNewRecordModal.value = false
}

/* ---------- NCP HISTORY (overview table) — no cross-patient history
   endpoint yet, ported as static placeholder rows from the design source ---------- */
const ncpHistory = ref([
  { id: 'PT-001', name: 'Ivy Hope Alba', initials: 'IA', phase: 'Monitoring', dietitian: 'Merian Felizarta, RND', date: 'May 13', status: 'Completed' },
  { id: 'PT-002', name: 'Julia Niel Bulalaque', initials: 'JB', phase: 'Intervention', dietitian: 'Nika Espantaleon, RND', date: 'May 12', status: 'Pending Review' },
  { id: 'PT-003', name: 'Kent Leabres', initials: 'KL', phase: 'Monitoring', dietitian: 'Nika Espantaleon, RND', date: 'May 12', status: 'Completed' },
  { id: 'PT-04', name: 'King Piolo Chui', initials: 'KP', phase: 'Diagnosis', dietitian: 'Nika Espantaleon, RND', date: 'May 12', status: 'Pending Review' }
])
function historyStatusClass(status) {
  if (status === 'Completed') return 'pill-green'
  if (status === 'Pending Review') return 'pill-gold'
  return 'pill-muted'
}

onMounted(() => {
  if (!relationshipId) {
    loadError.value = 'No patient selected. Go back to My Patients and choose a patient chart.'
    isLoading.value = false
    return
  }
  loadRecord()
})
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
.patient-cell { display: flex; align-items: center; gap: 10px; }
.history-avatar { width: 30px; height: 30px; border-radius: 50%; background: #eceeec; color: #4a5a4a; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; flex-shrink: 0; }
.history-name { font-weight: 700; color: #1a3a1a; margin: 0; }
.history-id { font-size: 0.7rem; color: #9aaa9a; margin: 0; }
.status-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-gold { background: #fdf1d6; color: #b8860b; }
.pill-muted { background: #eceeec; color: #8a9a8a; }

/* ============ EDIT MODE (4-phase wizard) ============ */
.breadcrumb { font-size: 0.82rem; color: #9aaa9a; margin: 0 0 10px; }
.breadcrumb a { color: #9aaa9a; text-decoration: none; cursor: pointer; }
.breadcrumb span:last-child { color: #6a7a6a; }

.ncp-header { margin-bottom: 20px; }
.ncp-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.ncp-sub { font-size: 0.86rem; color: #6a7a6a; display: flex; align-items: center; gap: 10px; }
.draft-pill { background: #faead0; color: #b8860b; font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.draft-pill.completed-pill { background: #e6efe0; color: #3a6b3a; }

/* STEP TRACKER */
.step-tracker { display: flex; align-items: center; margin-bottom: 24px; }
.step-node { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.step-circle {
  width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.85rem; flex-shrink: 0;
}
.step-circle.circle-active { background: #D4A017; color: #1a3a1a; }
.step-circle.circle-done { background: #1e4a26; color: #fff; }
.step-circle.circle-upcoming { background: #fff; color: #9aaa9a; border: 1px solid #d5dad5; }
.step-label { font-size: 0.8rem; color: #9aaa9a; font-weight: 600; }
.step-label.label-active { color: #1a3a1a; font-weight: 700; }
.step-line { flex: 1; height: 2px; background: #e5e8e5; margin: 0 12px; margin-bottom: 26px; }
.step-line.line-done { background: #1e4a26; }

/* CARD */
.ncp-card { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 28px 32px; }

.phase-eyebrow { display: block; font-size: 0.72rem; letter-spacing: 0.1em; color: #D4A017; font-weight: 700; margin-bottom: 18px; }
.small-eyebrow { margin-top: 20px; }

.field-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 18px; }
.field-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 18px; }

.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #2a2a2a; margin: 0 0 6px; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input, .field-textarea {
  width: 100%; border: 1px solid #e5e8e5; border-radius: 8px; padding: 11px 14px;
  font-size: 0.86rem; color: #2a2a2a; background: #fff; font-family: inherit; margin-bottom: 4px;
}
.field-input:disabled, .field-textarea:disabled { background: #f4f6f4; color: #6a7a6a; }
.field-textarea { resize: vertical; margin-bottom: 18px; }
.computed-box {
  background: #f4f6f4; border: 1px solid #e5e8e5; border-radius: 8px; padding: 11px 14px;
  font-size: 0.86rem; color: #2a2a2a; font-weight: 600;
}

.info-banner {
  display: flex; align-items: center; gap: 8px; background: #eef1f6; border-radius: 8px;
  padding: 12px 16px; font-size: 0.82rem; color: #3a4a5a; margin-bottom: 20px;
}
.info-icon { color: #2a5a8a; flex-shrink: 0; }
.finalized-banner { background: #fdf8ee; color: #8a6a1a; }
.finalized-banner .info-icon { color: #b8860b; }

.preview-label { display: block; font-size: 0.68rem; letter-spacing: 0.08em; color: #D4A017; font-weight: 700; margin: 4px 0 8px; }
.pes-preview { background: #eef3ec; border-radius: 8px; padding: 16px; font-size: 0.9rem; color: #1a3a1a; line-height: 1.6; margin-bottom: 4px; }

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
.ncp-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 24px; }
.actions-right { display: flex; align-items: center; gap: 14px; }
.save-draft-btn, .back-btn {
  display: flex; align-items: center; gap: 6px; background: none; border: none;
  color: #4a5a4a; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.save-draft-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.continue-btn {
  display: flex; align-items: center; gap: 8px; background: #D4A017; color: #1a3a1a; border: none;
  border-radius: 8px; padding: 12px 22px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}

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
  .field-grid-4, .goal-status-grid { grid-template-columns: repeat(2, 1fr); }
}

/* ============ NEW NCP RECORD MODAL ============ */
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
.auto-result-item { background: #fff; border-radius: 8px; padding: 10px; text-align: center; }
.auto-result-value { font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.auto-result-sub { font-size: 0.68rem; color: #b8860b; font-weight: 600; margin: 2px 0 4px; }
.auto-result-sub.nrs-sub { color: #9aaa9a; }
.auto-result-label { font-size: 0.68rem; color: #9aaa9a; margin: 0; }

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
