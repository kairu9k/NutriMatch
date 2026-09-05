<template>
  <div class="ncp-page">
    <!-- BREADCRUMB -->
    <p class="breadcrumb">
      <NuxtLink to="/my-patients">My Patients</NuxtLink> /
      <span>{{ patientName }}</span> /
      <span>NCP Record</span>
    </p>

    <div class="ncp-header">
      <div>
        <h1 class="ncp-title">Nutrition Care Process</h1>
        <p class="ncp-sub">
          Patient: {{ patientName }} · Encounter Date: {{ encounterDate }}
          <span class="draft-pill">Draft</span>
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

    <!-- CARD -->
    <div class="ncp-card">
      <!-- PHASE 1: ASSESSMENT -->
      <div v-if="currentStep === 0">
        <span class="phase-eyebrow">— PHASE 1 — NUTRITIONAL ASSESSMENT</span>

        <div class="field-grid-4">
          <div>
            <label class="field-label">Weight (kg)</label>
            <input v-model="assessment.weight" type="text" class="field-input" />
          </div>
          <div>
            <label class="field-label">Height (cm)</label>
            <input v-model="assessment.height" type="text" class="field-input" />
          </div>
          <div>
            <label class="field-label">Blood Pressure</label>
            <input v-model="assessment.bloodPressure" type="text" class="field-input" />
          </div>
          <div>
            <label class="field-label">Blood Glucose (mg/dL)</label>
            <input v-model="assessment.bloodGlucose" type="text" class="field-input" />
          </div>
        </div>

        <div class="field-grid-2">
          <div>
            <label class="field-label">HbA1c (%) <span class="optional">(optional)</span></label>
            <input v-model="assessment.hba1c" type="text" class="field-input" />
          </div>
          <div>
            <label class="field-label">Computed BMI</label>
            <div class="computed-box">{{ computedBmi }}</div>
          </div>
        </div>

        <label class="field-label">Lab Notes <span class="optional">(optional)</span></label>
        <textarea v-model="assessment.labNotes" class="field-textarea" rows="2"></textarea>

        <label class="field-label">Assessment Notes</label>
        <textarea v-model="assessment.notes" class="field-textarea" rows="4"></textarea>

        <div class="ncp-actions">
          <button class="save-draft-btn" @click="saveDraft"><Save :size="14" /> Save as Draft</button>
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
        <input v-model="diagnosis.problem" type="text" class="field-input" />

        <label class="field-label">Etiology (E) — "related to..."</label>
        <textarea v-model="diagnosis.etiology" class="field-textarea" rows="2"></textarea>

        <label class="field-label">Signs / Symptoms (S) — "as evidenced by..."</label>
        <textarea v-model="diagnosis.signs" class="field-textarea" rows="2"></textarea>

        <span class="preview-label">PREVIEW</span>
        <div class="pes-preview">
          <strong>{{ diagnosis.problem || '…' }}</strong> related to <strong>{{ diagnosis.etiology || '…' }}</strong>
          as evidenced by <strong>{{ diagnosis.signs || '…' }}</strong>.
        </div>

        <div class="ncp-actions">
          <button class="back-btn" @click="prevStep"><ArrowLeft :size="14" /> Back</button>
          <div class="actions-right">
            <button class="save-draft-btn" @click="saveDraft"><Save :size="14" /> Save as Draft</button>
            <button class="continue-btn" @click="nextStep">Continue to Intervention <ArrowRight :size="15" /></button>
          </div>
        </div>
      </div>

      <!-- PHASE 3: INTERVENTION -->
      <div v-if="currentStep === 2">
        <span class="phase-eyebrow">— PHASE 3 — INTERVENTION</span>

        <label class="field-label">Diet Prescription</label>
        <textarea v-model="intervention.dietPrescription" class="field-textarea" rows="3"></textarea>

        <span class="phase-eyebrow small-eyebrow">— MACRONUTRIENT TARGETS</span>
        <div class="field-grid-4">
          <div>
            <label class="field-label">Target kcal</label>
            <input v-model="intervention.kcal" type="text" class="field-input" />
          </div>
          <div>
            <label class="field-label">Protein (g)</label>
            <input v-model="intervention.protein" type="text" class="field-input" />
          </div>
          <div>
            <label class="field-label">Carbohydrate (g)</label>
            <input v-model="intervention.carbs" type="text" class="field-input" />
          </div>
          <div>
            <label class="field-label">Fat (g)</label>
            <input v-model="intervention.fat" type="text" class="field-input" />
          </div>
        </div>

        <label class="field-label">Intervention Notes</label>
        <textarea v-model="intervention.notes" class="field-textarea" rows="4"></textarea>

        <div class="linked-plan-banner">
          <Paperclip :size="15" class="info-icon" />
          Linked meal plan: <strong>{{ intervention.linkedPlan }}</strong> —
          <a href="#" class="linked-plan-link" @click.prevent="navigateTo('/meal-planning')">Edit in Meal Plan Builder →</a>
        </div>

        <div class="ncp-actions">
          <button class="back-btn" @click="prevStep"><ArrowLeft :size="14" /> Back</button>
          <div class="actions-right">
            <button class="save-draft-btn" @click="saveDraft"><Save :size="14" /> Save as Draft</button>
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
            :key="g"
            class="goal-status-btn"
            :class="{ active: monitoring.goalStatus === g }"
            @click="monitoring.goalStatus = g"
          >
            {{ g }}
          </button>
        </div>

        <label class="field-label">Monitoring Notes</label>
        <textarea v-model="monitoring.notes" class="field-textarea" rows="5"></textarea>

        <div class="ncp-actions">
          <button class="back-btn" @click="prevStep"><ArrowLeft :size="14" /> Back</button>
          <button class="save-draft-btn" @click="saveDraft"><Save :size="14" /> Save as Draft</button>
        </div>
      </div>
    </div>

    <!-- FINALIZE PANEL (only visible on last step) -->
    <div v-if="currentStep === 3" class="finalize-panel">
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

      <button class="finalize-btn" :disabled="!allChecksPassed" @click="finalizeRecord">Finalize NCP Record</button>
    </div>
  </div>
</template>

<script setup>
import { Check, Save, ArrowRight, ArrowLeft, Info, Paperclip, Lock } from 'lucide-vue-next'



definePageMeta({ layout: 'dashboard', title: 'NCP Record' })

const route = useRoute()
const patientName = computed(() => route.query.patient || 'Juan Dela Cruz')
const encounterDate = 'June 15, 2026'

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

/* ---------- PHASE 1: ASSESSMENT ---------- */
const assessment = ref({
  weight: '',
  height: '',
  bloodPressure: '',
  bloodGlucose: '',
  hba1c: '',
  labNotes: '',
  notes: ''
})

const computedBmi = computed(() => {
  const w = parseFloat(assessment.value.weight)
  const hCm = parseFloat(assessment.value.height)
  if (!w || !hCm) return '—'
  const hM = hCm / 100
  const bmi = w / (hM * hM)
  let category = 'Normal'
  if (bmi < 18.5) category = 'Underweight'
  else if (bmi >= 25 && bmi < 30) category = 'Overweight'
  else if (bmi >= 30) category = 'Obese'
  return `${bmi.toFixed(1)} — ${category}`
})

/* ---------- PHASE 2: DIAGNOSIS ---------- */
const diagnosis = ref({
  problem: 'Inadequate carbohydrate intake management',
  etiology: 'poor dietary knowledge regarding diabetic exchange portions and inconsistent meal timing',
  signs: 'elevated fasting blood glucose (126 mg/dL), HbA1c of 6.8%, and irregular meal pattern reported in 24-hour recall'
})

/* ---------- PHASE 3: INTERVENTION ---------- */
const intervention = ref({
  dietPrescription: '1,800 kcal diabetic exchange diet, low glycemic index focus, consistent carbohydrate distribution across 3 meals + 2 snacks. FNRI Food Exchange List-based meal planning.',
  kcal: '1800',
  protein: '90',
  carbs: '225',
  fat: '60',
  notes: 'Educated patient on FNRI Food Exchange List portion sizes using visual food models. Discussed strategies to avoid skipping breakfast. Set a behavioral goal of logging meals daily via food diary for the next 2 weeks. Linked patient to "Managing Carb Cravings" resource article.',
  linkedPlan: 'Diabetic-Friendly Plan (1,800 kcal)'
})

/* ---------- PHASE 4: MONITORING ---------- */
const goalOptions = ['Met', 'Partially Met', 'Not Met', 'Ongoing']

const monitoring = ref({
  goalStatus: 'Partially Met',
  notes: 'Patient has reduced fasting glucose from 126 to 112 mg/dL over 4 weeks, indicating partial progress toward glycemic goals. Food diary adherence improved to 5/7 days. Breakfast skipping has decreased but not fully resolved. Recommend continued reinforcement of meal timing at next follow-up (Jul 4, 2026) and re-check of HbA1c in 3 months.'
})

/* ---------- FINALIZE CHECKLIST ---------- */
const checklist = computed(() => [
  { label: 'Weight & Height recorded', done: !!assessment.value.weight && !!assessment.value.height },
  { label: 'PES Problem documented', done: !!diagnosis.value.problem },
  { label: 'Diet Prescription set', done: !!intervention.value.dietPrescription }
])

const allChecksPassed = computed(() => checklist.value.every(c => c.done))

/* ---------- ACTIONS ---------- */
function saveDraft() {
  // Wire this up to your real save-draft API call (PATCH /api/ncp-records/:id)
  console.log('Saving draft', { assessment: assessment.value, diagnosis: diagnosis.value, intervention: intervention.value, monitoring: monitoring.value })
}

function finalizeRecord() {
  if (!allChecksPassed.value) return
  // Wire this up to your real finalize API call — this should be immutable per RA 10173 once saved
  console.log('Finalizing NCP record')
  navigateTo(`/ncp-records?patient=${patientName.value}&finalized=true`)
}
</script>

<style scoped>
* { box-sizing: border-box; }

.ncp-page { font-family: 'Inter', sans-serif; }

.breadcrumb { font-size: 0.82rem; color: #9aaa9a; margin: 0 0 10px; }
.breadcrumb a { color: #9aaa9a; text-decoration: none; }
.breadcrumb span:last-child { color: #6a7a6a; }

.ncp-header { margin-bottom: 20px; }
.ncp-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.ncp-sub { font-size: 0.86rem; color: #6a7a6a; display: flex; align-items: center; gap: 10px; }
.draft-pill { background: #faead0; color: #b8860b; font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }

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

/* ACTIONS */
.ncp-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 24px; }
.actions-right { display: flex; align-items: center; gap: 14px; }
.save-draft-btn, .back-btn {
  display: flex; align-items: center; gap: 6px; background: none; border: none;
  color: #4a5a4a; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
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