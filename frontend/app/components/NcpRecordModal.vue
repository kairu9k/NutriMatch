<template>
  <div class="modal-overlay" @click.self="close">
    <div class="modal-box">
      <div class="modal-header">
        <div>
          <h2 class="modal-title">Nutrition Care Process</h2>
          <p class="modal-sub">{{ subtitle }}</p>
        </div>
        <div class="modal-patient-chip">
          <span class="modal-patient-avatar">{{ initials }}</span>
          {{ patientName }}
        </div>
      </div>

      <p v-if="isLoading" class="empty-note">Loading…</p>
      <p v-else-if="loadError" class="form-error">{{ loadError }}</p>

      <template v-else>
        <!-- TABS — a check marks a tab whose required fields are all filled -->
        <div class="modal-tabs">
          <button
            v-for="(step, index) in steps"
            :key="step"
            class="modal-tab"
            :class="{ active: tab === index }"
            @click="tab = index"
          >
            <Check v-if="!isReadOnly && tabComplete(index)" :size="13" class="tab-check" />
            {{ index + 1 }}. {{ step }}
          </button>
        </div>

        <p v-if="isFinalized" class="info-banner finalized-banner">
          <Lock :size="15" class="info-icon" />
          Finalized {{ formatDateTime(record.updated_at) }} — this record can no longer be edited.
        </p>
        <p v-else-if="isReadOnly" class="info-banner">
          <Lock :size="15" class="info-icon" /> Viewing an unfinished record (read-only).
        </p>
        <p v-if="saveError" class="form-error">{{ saveError }}</p>

        <!-- TAB 1: ASSESSMENT -->
        <div v-if="tab === 0" class="modal-body">
          <span class="modal-eyebrow">PHASE 1 — NUTRITIONAL ASSESSMENT</span>

          <div class="modal-field-grid-3">
            <div>
              <label class="field-label">Height (cm)</label>
              <input v-model="assessment.height_cm" type="number" min="0" step="0.1" class="field-input" :disabled="isReadOnly" />
            </div>
            <div>
              <label class="field-label">Weight (kg)</label>
              <input v-model="assessment.weight_kg" type="number" min="0" step="0.1" class="field-input" :disabled="isReadOnly" />
            </div>
            <div>
              <label class="field-label">HbA1c (%) <span class="optional">(optional)</span></label>
              <input v-model="assessment.hba1c" type="number" min="0" step="0.1" class="field-input" :disabled="isReadOnly" />
            </div>
          </div>

          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">Blood Pressure (mmHg)</label>
              <div class="bp-row">
                <input v-model="assessment.bp_systolic" type="number" min="0" max="300" step="1" class="field-input" placeholder="120" aria-label="Systolic" :disabled="isReadOnly" />
                <span class="bp-slash">/</span>
                <input v-model="assessment.bp_diastolic" type="number" min="0" max="200" step="1" class="field-input" placeholder="80" aria-label="Diastolic" :disabled="isReadOnly" />
              </div>
            </div>
            <div>
              <label class="field-label">Blood Glucose (mg/dL)</label>
              <input v-model="assessment.blood_glucose" type="number" min="0" step="0.1" class="field-input" :disabled="isReadOnly" />
            </div>
          </div>

          <label class="field-label">Lab Notes <span class="optional">(optional)</span></label>
          <textarea v-model="assessment.lab_notes" class="field-textarea" rows="2" placeholder="Clinical observations..." :disabled="isReadOnly"></textarea>

          <label class="field-label">Assessment Notes</label>
          <textarea v-model="assessment.assessment_notes" class="field-textarea" rows="2" :disabled="isReadOnly"></textarea>

          <div class="extra-section">
            <div class="extra-header">
              <span class="field-label extra-title">Additional Measured Variables <span class="optional">(optional)</span></span>
              <button v-if="!isReadOnly" type="button" class="extra-add-btn" @click="addExtra(assessment.extra)"><Plus :size="14" /> Add Field</button>
            </div>
            <p v-if="!assessment.extra.length" class="extra-empty">
              {{ isReadOnly ? 'None recorded.' : 'Add any measured variable not listed above, e.g. waist circumference, cholesterol, creatinine.' }}
            </p>
            <div v-for="(row, idx) in assessment.extra" :key="idx" class="extra-row">
              <input v-model="row.label" type="text" class="field-input" placeholder="Measured Variable" maxlength="100" :disabled="isReadOnly" />
              <input v-model="row.value" type="text" class="field-input" placeholder="Value" maxlength="500" :disabled="isReadOnly" />
              <input v-model="row.unit" type="text" class="field-input extra-unit" placeholder="Unit" maxlength="30" :disabled="isReadOnly" />
              <button v-if="!isReadOnly" type="button" class="extra-remove-btn" title="Remove" @click="assessment.extra.splice(idx, 1)"><X :size="14" /></button>
            </div>
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
        </div>

        <!-- TAB 2: DIAGNOSIS -->
        <div v-if="tab === 1" class="modal-body">
          <span class="modal-eyebrow">PHASE 2 — NUTRITION DIAGNOSIS (PES STATEMENT)</span>

          <label class="field-label">Problem (P)</label>
          <input v-model="diagnosis.pes_problem" type="text" class="field-input field-spaced" :disabled="isReadOnly" />

          <label class="field-label">Etiology / Related to (E)</label>
          <textarea v-model="diagnosis.pes_etiology" class="field-textarea" rows="2" placeholder="e.g High intake of refined carbohydrates..." :disabled="isReadOnly"></textarea>

          <label class="field-label">Signs &amp; Symptoms (S)</label>
          <textarea v-model="diagnosis.pes_signs" class="field-textarea" rows="2" placeholder="e.g as evidenced by..." :disabled="isReadOnly"></textarea>

          <div class="pes-generated-box">
            <span class="pes-generated-label">AUTO-GENERATED PES STATEMENT</span>
            <p class="pes-generated-text">
              {{ diagnosis.pes_problem || '…' }}<span v-if="diagnosis.pes_etiology"> related to {{ diagnosis.pes_etiology }}</span><span v-if="diagnosis.pes_signs"> as evidenced by {{ diagnosis.pes_signs }}</span>.
            </p>
          </div>
        </div>

        <!-- TAB 3: INTERVENTION -->
        <div v-if="tab === 2" class="modal-body">
          <span class="modal-eyebrow">PHASE 3 — NUTRITION INTERVENTION</span>

          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">Target kcal/day</label>
              <input v-model="intervention.target_kcal" type="number" min="0" step="1" class="field-input" :disabled="isReadOnly" />
            </div>
            <div>
              <label class="field-label">Target Protein (g)</label>
              <input v-model="intervention.target_protein_g" type="number" min="0" step="1" class="field-input" :disabled="isReadOnly" />
            </div>
          </div>
          <div class="modal-field-grid-2">
            <div>
              <label class="field-label">Target Carbs (g)</label>
              <input v-model="intervention.target_carb_g" type="number" min="0" step="1" class="field-input" :disabled="isReadOnly" />
            </div>
            <div>
              <label class="field-label">Target Fat (g)</label>
              <input v-model="intervention.target_fat_g" type="number" min="0" step="1" class="field-input" :disabled="isReadOnly" />
            </div>
          </div>

          <label class="field-label">Diet Prescription Notes</label>
          <textarea v-model="intervention.diet_prescription" class="field-textarea" rows="3" placeholder="e.g. Low-GI, high-fiber Filipino diet. Reduce rice to 1/2 cup per meal. Include ampalaya, sayote, kangkong daily......." :disabled="isReadOnly"></textarea>

          <label class="field-label">Intervention Notes <span class="optional">(optional)</span></label>
          <textarea v-model="intervention.intervention_notes" class="field-textarea" rows="2" :disabled="isReadOnly"></textarea>

          <div class="extra-section">
            <div class="extra-header">
              <span class="field-label extra-title">Additional Measured Variables <span class="optional">(optional)</span></span>
              <button v-if="!isReadOnly" type="button" class="extra-add-btn" @click="addExtra(intervention.extra)"><Plus :size="14" /> Add Field</button>
            </div>
            <p v-if="!intervention.extra.length" class="extra-empty">
              {{ isReadOnly ? 'None recorded.' : 'Add any measured variable not listed above, e.g. fluid or sodium limits, fiber goal, physical activity.' }}
            </p>
            <div v-for="(row, idx) in intervention.extra" :key="idx" class="extra-row">
              <input v-model="row.label" type="text" class="field-input" placeholder="Measured Variable" maxlength="100" :disabled="isReadOnly" />
              <input v-model="row.value" type="text" class="field-input" placeholder="Value" maxlength="500" :disabled="isReadOnly" />
              <input v-model="row.unit" type="text" class="field-input extra-unit" placeholder="Unit" maxlength="30" :disabled="isReadOnly" />
              <button v-if="!isReadOnly" type="button" class="extra-remove-btn" title="Remove" @click="intervention.extra.splice(idx, 1)"><X :size="14" /></button>
            </div>
          </div>

          <div class="linked-plan-banner">
            <Paperclip :size="15" class="info-icon" />
            Meal plans for this patient are managed separately —
            <a href="#" class="linked-plan-link" @click.prevent="navigateTo(`/meal-planning?relationship=${relationshipId}`)">Open Meal Plan Builder →</a>
          </div>
        </div>

        <!-- TAB 4: MONITORING (follow-up records only) -->
        <div v-if="tab === 3" class="modal-body">
          <span class="modal-eyebrow">PHASE 4 — MONITORING &amp; EVALUATION</span>
          <p class="phase-hint">Evaluates the goals set in this client's previous NCP record.</p>

          <label class="field-label">Goal Status</label>
          <div class="goal-status-grid">
            <button
              v-for="g in goalOptions"
              :key="g.value"
              type="button"
              class="goal-status-btn"
              :class="{ active: monitoring.goal_status === g.value }"
              :disabled="isReadOnly"
              @click="monitoring.goal_status = g.value"
            >
              {{ g.label }}
            </button>
          </div>

          <label class="field-label">Monitoring Notes</label>
          <textarea v-model="monitoring.monitoring_notes" class="field-textarea" rows="4" placeholder="Observations on patient progress, clinical response, next steps........" :disabled="isReadOnly"></textarea>
        </div>

        <!-- STATUS: autosave / auto-finalize -->
        <div v-if="!isReadOnly" class="autosave-panel" :class="{ ready: allComplete }">
          <template v-if="allComplete">
            <p class="autosave-title">
              <Check :size="15" /> All required fields are filled
            </p>
            <p class="autosave-desc">
              {{ isFinalizing ? 'Finalizing…' : `This record will be finalized in ${finalizeCountdown}s. Keep typing to add more — it waits until you stop.` }}
            </p>
          </template>
          <template v-else>
            <p class="autosave-desc">
              Each tab saves automatically once all its required fields are filled; the record finalizes on its own when every tab is complete.
            </p>
            <p class="autosave-missing">Still needed: {{ missingSummary }}</p>
          </template>
          <p v-if="lastSavedAt" class="autosave-saved">{{ isSaving ? 'Saving…' : `Saved ${lastSavedAt}` }}</p>
        </div>

        <div class="modal-actions">
          <button class="modal-back-btn" :disabled="tab === 0" @click="tab--">Back</button>
          <button v-if="tab < steps.length - 1" class="modal-continue-btn" @click="tab++">Next: {{ steps[tab + 1] }}</button>
          <button v-else-if="isReadOnly && record && record.status === 'draft' && canContinue" class="modal-continue-btn" @click="emit('continue')">Continue Record</button>
          <button v-else class="modal-continue-btn" @click="close">Close</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
// The NCP record form, shared by the NCP Records page (cross-patient list)
// and Client Detail's "NCP Records" tab.
//  - edit mode: resumes the client's unfinished record, or starts a new one.
//    An initial record has Assessment → Diagnosis → Intervention; a
//    follow-up (client already has a finalized record) adds Monitoring.
//    There is no Save button: a tab autosaves once its required fields are
//    all filled, and the record finalizes itself a few seconds after every
//    tab is complete and the RND stops typing.
//  - view mode: one record, read-only.
// Required = every field not labelled "(optional)". The API enforces the
// clinical minimum on finalize (clinical/views.py NcpRecordFinalizeView).
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Check, Lock, Paperclip, Plus, X } from 'lucide-vue-next'

const props = defineProps({
  relationshipId: { type: [String, Number], required: true },
  patientName: { type: String, default: '' },
  mode: { type: String, default: 'edit' }, // 'edit' | 'view'
  recordId: { type: [String, Number], default: null }, // view mode
  canContinue: { type: Boolean, default: true }, // view mode: offer "Continue Record" on a draft
})
const emit = defineEmits(['close', 'changed', 'continue'])

const { get, post, patch } = useApi()

const AUTOSAVE_DELAY_MS = 1200
const FINALIZE_DELAY_S = 10

const isLoading = ref(true)
const loadError = ref('')
const saveError = ref('')
const record = ref(null)
const isFollowUp = ref(false)
const tab = ref(0)

const isFinalized = computed(() => record.value?.status === 'completed')
const isReadOnly = computed(() => props.mode === 'view' || isFinalized.value)
// Monitoring belongs to follow-ups. A read-only record that has monitoring
// data anyway (older initial records) still shows it rather than hiding it.
const showMonitoring = computed(() =>
  isFollowUp.value || (isReadOnly.value && !!(record.value?.goal_status || record.value?.monitoring_notes))
)
const steps = computed(() => {
  const base = ['Assessment', 'Diagnosis', 'Intervention']
  return showMonitoring.value ? [...base, 'Monitoring'] : base
})
const subtitle = computed(() => {
  const kind = isFollowUp.value ? 'Follow-up record' : 'Initial record'
  if (record.value?.created_at) return `${kind} · created ${formatDateTime(record.value.created_at)}`
  return `${kind} · ${isFollowUp.value ? 'Assessment to Monitoring' : 'Assessment to Intervention'}`
})
const initials = computed(() => (props.patientName || '').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase())

/* ---------- form state ---------- */
const assessment = ref({})
const diagnosis = ref({})
const intervention = ref({})
const monitoring = ref({})
const goalOptions = [
  { value: 'met', label: 'Met' },
  { value: 'partially_met', label: 'Partially Met' },
  { value: 'not_met', label: 'Not Met' },
  { value: 'ongoing', label: 'Ongoing' },
]

function hydrate(r = {}) {
  assessment.value = {
    weight_kg: r.weight_kg ?? '', height_cm: r.height_cm ?? '',
    bp_systolic: (r.blood_pressure || '').split('/')[0] || '', bp_diastolic: (r.blood_pressure || '').split('/')[1] || '',
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
hydrate()

// Stored as "systolic/diastolic" text; the form keeps two number boxes.
function bloodPressureText(a) {
  const sys = String(a.bp_systolic ?? '').trim()
  const dia = String(a.bp_diastolic ?? '').trim()
  return sys || dia ? `${sys}/${dia}` : ''
}
function addExtra(list) {
  list.push({ label: '', value: '', unit: '' })
}

function buildPayload() {
  const num = (v) => (v === '' || v === null || v === undefined ? null : v)
  const a = assessment.value, d = diagnosis.value, i = intervention.value, m = monitoring.value
  return {
    weight_kg: num(a.weight_kg), height_cm: num(a.height_cm),
    blood_pressure: bloodPressureText(a) || null, blood_glucose: num(a.blood_glucose),
    hba1c: num(a.hba1c), lab_notes: a.lab_notes || null, assessment_notes: a.assessment_notes || null,
    assessment_extra: a.extra.filter(r => r.label.trim()),
    pes_problem: d.pes_problem || null, pes_etiology: d.pes_etiology || null, pes_signs: d.pes_signs || null,
    diet_prescription: i.diet_prescription || null, target_kcal: num(i.target_kcal),
    target_protein_g: num(i.target_protein_g), target_carb_g: num(i.target_carb_g),
    target_fat_g: num(i.target_fat_g), intervention_notes: i.intervention_notes || null,
    intervention_extra: i.extra.filter(r => r.label.trim()),
    monitoring_notes: m.monitoring_notes || null, goal_status: m.goal_status || null,
  }
}

/* ---------- required fields ---------- */
const REQUIRED = [
  [['assessment', 'height_cm', 'Height'], ['assessment', 'weight_kg', 'Weight'], ['assessment', 'bp_systolic', 'Blood pressure'],
    ['assessment', 'bp_diastolic', 'Blood pressure'], ['assessment', 'blood_glucose', 'Blood glucose'], ['assessment', 'assessment_notes', 'Assessment notes']],
  [['diagnosis', 'pes_problem', 'Problem'], ['diagnosis', 'pes_etiology', 'Etiology'], ['diagnosis', 'pes_signs', 'Signs & symptoms']],
  [['intervention', 'target_kcal', 'Target kcal'], ['intervention', 'target_protein_g', 'Target protein'], ['intervention', 'target_carb_g', 'Target carbs'],
    ['intervention', 'target_fat_g', 'Target fat'], ['intervention', 'diet_prescription', 'Diet prescription']],
  [['monitoring', 'goal_status', 'Goal status'], ['monitoring', 'monitoring_notes', 'Monitoring notes']],
]
const sections = { assessment, diagnosis, intervention, monitoring }
const filled = (v) => String(v ?? '').trim() !== ''
function missingIn(index) {
  return REQUIRED[index].filter(([section, field]) => !filled(sections[section].value[field])).map(([, , label]) => label)
}
function tabComplete(index) {
  return missingIn(index).length === 0
}
const allComplete = computed(() => steps.value.every((_, i) => tabComplete(i)))
const missingSummary = computed(() =>
  steps.value
    .map((step, i) => ({ step, missing: [...new Set(missingIn(i))] }))
    .filter(s => s.missing.length)
    .map(s => `${s.step} (${s.missing.join(', ')})`)
    .join(' · ')
)

/* ---------- autosave + auto-finalize ---------- */
const isSaving = ref(false)
const isFinalizing = ref(false)
const lastSavedAt = ref('')
const finalizeCountdown = ref(FINALIZE_DELAY_S)
let saveTimer = null
let finalizeTimer = null
let countdownTimer = null
let saveQueue = Promise.resolve()
// The form as last loaded/saved — the change watcher ignores anything that
// matches it, so loading a record into the form isn't mistaken for an edit.
let savedSnapshot = ''
const snapshot = () => JSON.stringify([assessment.value, diagnosis.value, intervention.value, monitoring.value])

function clearTimers() {
  clearTimeout(saveTimer)
  clearTimeout(finalizeTimer)
  clearInterval(countdownTimer)
  saveTimer = null
}

// Saves are queued so an autosave and the final save never overlap (the
// first one creates the record; later ones must PATCH it).
function save() {
  saveQueue = saveQueue.then(async () => {
    if (isReadOnly.value) return
    isSaving.value = true
    saveError.value = ''
    try {
      const payload = buildPayload()
      const sent = snapshot()
      if (record.value) {
        record.value = await patch(`/rnd/ncp/${record.value.id}/`, payload)
      } else {
        record.value = await post(`/rnd/relationships/${props.relationshipId}/ncp/`, {
          relationship: Number(props.relationshipId),
          encounter_date: localIsoDate(new Date()),
          ...payload,
        })
      }
      savedSnapshot = sent
      lastSavedAt.value = new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
      emit('changed')
    } catch (error) {
      saveError.value = apiError(error, 'Could not save this record. Please try again.')
      throw error
    } finally {
      isSaving.value = false
    }
  })
  return saveQueue.catch(() => {})
}

async function finalize() {
  isFinalizing.value = true
  try {
    await save()
    if (saveError.value || !record.value) return
    record.value = await patch(`/rnd/ncp/${record.value.id}/finalize/`)
    emit('changed')
  } catch (error) {
    saveError.value = apiError(error, 'Could not finalize this record. Please try again.')
  } finally {
    isFinalizing.value = false
  }
}

function scheduleFinalize() {
  finalizeCountdown.value = FINALIZE_DELAY_S
  countdownTimer = setInterval(() => {
    finalizeCountdown.value = Math.max(0, finalizeCountdown.value - 1)
  }, 1000)
  finalizeTimer = setTimeout(() => {
    clearInterval(countdownTimer)
    finalize()
  }, FINALIZE_DELAY_S * 1000)
}

watch([assessment, diagnosis, intervention, monitoring], () => {
  if (isReadOnly.value || isLoading.value || snapshot() === savedSnapshot) return
  clearTimers()
  if (allComplete.value) {
    scheduleFinalize()
  } else if (tabComplete(tab.value)) {
    saveTimer = setTimeout(() => { saveTimer = null; save() }, AUTOSAVE_DELAY_MS)
  }
}, { deep: true })

/* ---------- load ---------- */
async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const records = await get(`/rnd/relationships/${props.relationshipId}/ncp/`)
    if (props.mode === 'view') {
      record.value = records.find(r => String(r.id) === String(props.recordId)) || null
      if (!record.value) throw new Error('not found')
      isFollowUp.value = !!record.value.is_follow_up
    } else {
      record.value = records.find(r => r.status === 'draft') || null
      isFollowUp.value = record.value ? record.value.is_follow_up : records.some(r => r.status === 'completed')
      // Resume on the first tab that still needs something.
      if (record.value) {
        hydrate(record.value)
        const firstIncomplete = steps.value.findIndex((_, i) => !tabComplete(i))
        tab.value = firstIncomplete === -1 ? 0 : firstIncomplete
      }
    }
    if (props.mode === 'view') hydrate(record.value)
    savedSnapshot = snapshot()
    // An unfinished record that already has everything filled (e.g. saved
    // before auto-finalize existed) finalizes like any other complete one.
    if (props.mode === 'edit' && record.value && allComplete.value) scheduleFinalize()
  } catch {
    loadError.value = 'Could not load this NCP record. Please try again.'
  } finally {
    isLoading.value = false
  }
}
onMounted(load)

async function close() {
  const pendingChanges = !isReadOnly.value && !isFinalizing.value && snapshot() !== savedSnapshot
  clearTimers()
  // Everything filled → finalize now rather than dropping the countdown.
  // A complete tab waiting on its autosave is saved first. An incomplete
  // tab's changes aren't kept (it was never valid to save).
  if (pendingChanges && allComplete.value) await finalize()
  else if (pendingChanges && tabComplete(tab.value)) await save()
  emit('close')
}
onBeforeUnmount(clearTimers)

/* ---------- helpers ---------- */
function localIsoDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
function formatDateTime(iso) {
  return iso ? new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }) : ''
}
function apiError(error, fallback) {
  const data = error?.data || {}
  if (data.detail) return data.detail
  const first = Object.entries(data).find(([, v]) => Array.isArray(v) && typeof v[0] === 'string')
  return first ? `${first[0].replace(/_/g, ' ')}: ${first[1][0]}` : fallback
}
</script>

<style scoped>
* { box-sizing: border-box; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.empty-note { font-size: 0.85rem; color: #9aaa9a; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(20,30,20,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100; padding: 20px;
}
.modal-box {
  background: #fff; border-radius: 16px; width: 100%; max-width: 560px;
  max-height: 90vh; overflow-y: auto; padding: 28px; font-family: 'Inter', sans-serif;
}
.modal-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 18px; }
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
  display: inline-flex; align-items: center; gap: 4px;
  border: none; background: none; padding: 10px 2px; margin-right: 12px; font-size: 0.8rem; font-weight: 600;
  color: #9aaa9a; cursor: pointer; border-bottom: 2px solid transparent; white-space: nowrap;
}
.modal-tab.active { color: #1f8f5c; border-bottom-color: #1f8f5c; font-weight: 700; }
.tab-check { color: #1f8f5c; }

.modal-body { display: flex; flex-direction: column; }
.modal-eyebrow { font-size: 0.68rem; letter-spacing: 0.08em; color: #b8860b; font-weight: 700; margin-bottom: 16px; }
.phase-hint { font-size: 0.8rem; color: #8a9a8a; margin: -8px 0 16px; }
.modal-field-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 16px; }
.modal-field-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin-bottom: 16px; }

.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #2a2a2a; margin: 0 0 6px; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input, .field-textarea {
  width: 100%; border: 1px solid #e5e8e5; border-radius: 8px; padding: 11px 14px;
  font-size: 0.86rem; color: #2a2a2a; background: #fff; font-family: inherit; margin-bottom: 4px;
}
.field-spaced { margin-bottom: 16px; }
.field-input:disabled, .field-textarea:disabled { background: #f4f6f4; color: #6a7a6a; }
.field-textarea { resize: vertical; margin-bottom: 18px; }
.bp-row { display: flex; align-items: center; gap: 8px; }
.bp-row .field-input { margin-bottom: 0; }
.bp-slash { font-size: 1.1rem; color: #8a9a8a; font-weight: 600; }

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

.info-banner {
  display: flex; align-items: center; gap: 8px; background: #eef1f6; border-radius: 8px;
  padding: 12px 16px; font-size: 0.82rem; color: #3a4a5a; margin: 0 0 20px;
}
.info-icon { color: #2a5a8a; flex-shrink: 0; }
.finalized-banner { background: #fdf8ee; color: #8a6a1a; }
.finalized-banner .info-icon { color: #b8860b; }

.linked-plan-banner {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap; background: #eef1f6; border-radius: 8px;
  padding: 12px 16px; font-size: 0.82rem; color: #3a4a5a; margin: 4px 0 16px;
}
.linked-plan-link { color: #2a5a8a; font-weight: 600; text-decoration: underline; }

.auto-results-box { background: #f4f8f5; border: 1px solid #dbe8dd; border-radius: 10px; padding: 16px; margin: 12px 0 20px; }
.auto-results-label { display: block; font-size: 0.66rem; letter-spacing: 0.06em; color: #6a8a70; font-weight: 700; margin-bottom: 12px; }
.auto-results-grid.single { display: grid; grid-template-columns: 1fr; max-width: 200px; }
.auto-result-item { background: #fff; border-radius: 8px; padding: 10px; text-align: center; }
.auto-result-value { font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.auto-result-label { font-size: 0.68rem; color: #9aaa9a; margin: 4px 0 0; }

.pes-generated-box { background: #fdf1d6; border: 1px solid #f0dca8; border-radius: 10px; padding: 14px 16px; margin: 0 0 20px; }
.pes-generated-label { display: block; font-size: 0.66rem; letter-spacing: 0.06em; color: #b8860b; font-weight: 700; margin-bottom: 6px; }
.pes-generated-text { font-size: 0.85rem; color: #8a6a1a; font-style: italic; margin: 0; }

.goal-status-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.goal-status-btn {
  border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 8px;
  padding: 12px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.goal-status-btn.active { border-color: #D4A017; color: #b8860b; background: #fdf8ee; font-weight: 700; }
.goal-status-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.autosave-panel { background: #f7f8f7; border: 1px solid #eceeec; border-radius: 10px; padding: 12px 16px; margin: 4px 0 16px; }
.autosave-panel.ready { background: #e9f5ee; border-color: #c4e3d0; }
.autosave-title { display: flex; align-items: center; gap: 6px; font-size: 0.84rem; font-weight: 700; color: #1f8f5c; margin: 0 0 4px; }
.autosave-desc { font-size: 0.8rem; color: #5a6a5a; margin: 0; line-height: 1.5; }
.autosave-missing { font-size: 0.78rem; color: #b8860b; margin: 6px 0 0; line-height: 1.5; }
.autosave-saved { font-size: 0.74rem; color: #8a9a8a; margin: 6px 0 0; }

.modal-actions { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 4px; }
.modal-back-btn {
  border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 8px;
  padding: 11px 20px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.modal-back-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.modal-continue-btn {
  flex: 1; background: #14301a; color: #fff; border: none; border-radius: 8px;
  padding: 12px 20px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}

@media (max-width: 600px) {
  .extra-row { grid-template-columns: 1fr 1fr; }
  .modal-field-grid-3, .modal-field-grid-2 { grid-template-columns: 1fr; }
  .goal-status-grid { grid-template-columns: repeat(2, 1fr); }
  .modal-header { flex-direction: column; }
}
</style>
