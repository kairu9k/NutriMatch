<template>
  <div class="ncp-page">
    <!-- BREADCRUMB -->
    <p class="breadcrumb">
      <NuxtLink to="/my-patients">My Patients</NuxtLink> /
      <span>{{ patientName }}</span> /
      <span>NCP Record</span>
    </p>

    <div v-if="loadError" class="form-error">{{ loadError }}</div>

    <template v-else>
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

      <p v-if="isLoading" class="empty-note">Loading…</p>

      <template v-else>
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
      </template>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Check, Save, ArrowRight, ArrowLeft, Info, Paperclip, Lock } from 'lucide-vue-next'

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

const encounterDate = computed(() =>
  record.value?.encounter_date
    ? new Date(record.value.encounter_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
)
const isFinalized = computed(() => record.value?.status === 'completed')

const steps = [
  { label: 'Assessment' },
  { label: 'Diagnosis' },
  { label: 'Intervention' },
  { label: 'Monitoring' }
]

const currentStep = ref(0)

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
      record.value = records[0]
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
  } catch {
    saveError.value = 'Could not finalize this record. Please try again.'
  } finally {
    isSaving.value = false
  }
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

.breadcrumb { font-size: 0.82rem; color: #9aaa9a; margin: 0 0 10px; }
.breadcrumb a { color: #9aaa9a; text-decoration: none; }
.breadcrumb span:last-child { color: #6a7a6a; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.empty-note { font-size: 0.85rem; color: #9aaa9a; }

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
</style>
