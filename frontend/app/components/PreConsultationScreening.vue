<template>
  <div class="screening-page">
    <div class="panel">
      <h1 class="screening-title">Pre-Consultation Nutritional Screening</h1>
      <p class="screening-sub">Your data auto-computes BMI, BMR, TDEE, and NRS-2002 risk score.</p>

      <div class="form-row-3">
        <div class="field">
          <label>Height (cm)</label>
          <input v-model.number="form.height" type="number" min="50" max="250" step="0.1" placeholder="e.g. 162" />
        </div>
        <div class="field">
          <label>Weight (kg)</label>
          <input v-model.number="form.weight" type="number" min="20" max="300" step="0.1" placeholder="e.g. 72" />
        </div>
        <div class="field">
          <label>Age</label>
          <input v-model.number="form.age" type="number" min="1" max="120" placeholder="e.g. 34" />
        </div>
      </div>

      <div class="form-row-2">
        <div class="field">
          <label>Sex</label>
          <select v-model="form.sex">
            <option value="" disabled>Select sex</option>
            <option value="female">Female</option>
            <option value="male">Male</option>
          </select>
        </div>
        <div class="field">
          <label>Activity Level</label>
          <select v-model="form.activityLevel">
            <option value="" disabled>Select activity level</option>
            <option v-for="level in activityLevels" :key="level.value" :value="level.value">{{ level.label }}</option>
          </select>
        </div>
      </div>

      <label class="symptoms-label">Current Symptoms (select all that apply)</label>
      <div class="symptoms-grid">
        <label v-for="s in symptomOptions" :key="s.key" class="checkbox-row">
          <input v-model="form.symptoms[s.key]" type="checkbox" />
          {{ s.label }}
        </label>
      </div>

      <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

      <button class="compute-btn" :disabled="!canCompute || isSubmitting" @click="handleCompute">
        {{ isSubmitting ? 'Computing…' : 'Compute My Health Metrics' }}
      </button>

      <template v-if="result">
        <div class="results-panel">
          <span class="results-eyebrow">Auto-Computed Results (Mifflin-St Jeor · WHO Asia-Pacific)</span>
          <div class="results-grid">
            <div class="result-box">
              <p class="result-label">BMI</p>
              <p class="result-value">{{ Number(result.bmi).toFixed(1) }}</p>
              <p class="result-tag" :class="bmiTagClass">{{ result.bmi_category }}</p>
            </div>
            <div class="result-box">
              <p class="result-label">BMR</p>
              <p class="result-value">{{ result.bmr_kcal ? Math.round(result.bmr_kcal) : '—' }}</p>
              <p class="result-unit">kcal/day</p>
            </div>
            <div class="result-box">
              <p class="result-label">TDEE</p>
              <p class="result-value">{{ result.tdee_kcal ? Math.round(result.tdee_kcal) : '—' }}</p>
              <p class="result-unit">kcal/day</p>
            </div>
            <div class="result-box">
              <p class="result-label">NRS-2002</p>
              <p class="result-value">Score: {{ result.nrs_score ?? '—' }}</p>
              <p class="result-tag" :class="nrsTagClass">{{ nrsRiskLabel }}</p>
            </div>
          </div>
        </div>

        <div class="complete-banner">
          <p class="complete-title"><CheckCircle2 :size="16" /> Screening Complete</p>
          <p class="complete-text">This summary has been shared with your RND, who will review it before your consultation.</p>
          <p class="complete-text">{{ hasActiveRnd ? 'You can head to Appointments to book your next consultation.' : 'You can now proceed to find your RND and book a consultation.' }}</p>
          <NuxtLink v-if="hasActiveRnd" to="/appointments" class="find-rnd-btn">Go to Appointments <ArrowRight :size="15" /></NuxtLink>
          <NuxtLink v-else to="/find-rnd" class="find-rnd-btn">Find an RND <ArrowRight :size="15" /></NuxtLink>
        </div>
      </template>
    </div>

    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle2 :size="16" /> Screening computed and saved!
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { CheckCircle2, ArrowRight } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Pre-Consultation Screening' })

const { get, post } = useApi()

// Values match clinical.PreConsultationScreening.ActivityLevel.
const activityLevels = [
  { value: 'sedentary', label: 'Sedentary' },
  { value: 'lightly_active', label: 'Lightly Active' },
  { value: 'moderately_active', label: 'Moderately Active' },
  { value: 'very_active', label: 'Very Active' },
  { value: 'extra_active', label: 'Extra Active' },
]

const symptomOptions = [
  { key: 'weightLoss', label: 'Unintended weight loss' },
  { key: 'poorAppetite', label: 'Poor appetite' },
  { key: 'elevatedGlucose', label: 'Elevated blood glucose' },
  { key: 'recentHospitalization', label: 'Recent hospitalization' },
]

const form = reactive({
  height: null,
  weight: null,
  age: null,
  sex: '',
  activityLevel: '',
  symptoms: { weightLoss: false, poorAppetite: false, elevatedGlucose: false, recentHospitalization: false },
})

const canCompute = computed(() =>
  form.height > 0 && form.weight > 0 && form.age > 0 && form.sex !== '' && form.activityLevel !== ''
)

const isSubmitting = ref(false)
const errorMessage = ref('')
const result = ref(null)
const hasActiveRnd = ref(false)

const toastVisible = ref(false)
let toastTimer = null

function ageFromDob(dob) {
  const d = new Date(`${dob}T00:00:00`)
  const now = new Date()
  let age = now.getFullYear() - d.getFullYear()
  if (now.getMonth() < d.getMonth() || (now.getMonth() === d.getMonth() && now.getDate() < d.getDate())) age--
  return age
}

// All calculations happen server-side (clinical/services.py). The symptom
// boxes map onto the backend's NRS-2002 inputs: poor appetite -> reduced
// intake; elevated glucose / recent hospitalization -> disease severity.
// Weight loss is derived by the backend from screening history, so that box
// is recorded in `symptoms` for the RND but doesn't change the score.
async function handleCompute() {
  if (!canCompute.value) return
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    const checked = symptomOptions.filter(s => form.symptoms[s.key]).map(s => s.label)
    result.value = await post('/client/screening/', {
      height_cm: form.height,
      weight_kg: form.weight,
      age: form.age,
      sex: form.sex,
      activity_level: form.activityLevel,
      reduced_intake: form.symptoms.poorAppetite,
      has_chronic_illness: form.symptoms.elevatedGlucose || form.symptoms.recentHospitalization,
      symptoms: checked.length ? checked.join(', ') : undefined,
    })
    toastVisible.value = true
    clearTimeout(toastTimer)
    toastTimer = setTimeout(() => { toastVisible.value = false }, 4000)
  } catch (error) {
    const data = error?.data || {}
    errorMessage.value = data.detail || Object.values(data).flat()[0] || 'Could not save your screening. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

const bmiTagClass = computed(() => {
  const cat = (result.value?.bmi_category || '').toLowerCase()
  if (cat.includes('normal')) return 'tag-green'
  if (cat.includes('underweight')) return 'tag-blue'
  return 'tag-gold'
})
const nrsRiskLabel = computed(() => ({ no_risk: 'No Risk', at_risk: 'At Risk', high_risk: 'High Risk' }[result.value?.nrs_risk] || ''))
const nrsTagClass = computed(() => ({ no_risk: 'tag-green', at_risk: 'tag-gold', high_risk: 'tag-red' }[result.value?.nrs_risk] || ''))

onMounted(async () => {
  // Pre-fill from the profile and the last screening so a repeat screening
  // only needs the new weight.
  const [profile, latest, relationships] = await Promise.all([
    get('/client/profile/').catch(() => null),
    get('/client/screening/latest/').catch(() => null),
    get('/client/relationships/').catch(() => []),
  ])
  if (profile?.date_of_birth) form.age = ageFromDob(profile.date_of_birth)
  if (profile?.sex) form.sex = profile.sex
  if (latest) {
    form.height = Number(latest.height_cm)
    form.activityLevel = latest.activity_level
  }
  hasActiveRnd.value = relationships.length > 0
})
</script>

<style scoped>
* { box-sizing: border-box; }
.screening-page { font-family: 'Inter', sans-serif; max-width: 760px; margin: 0 auto; }

.panel { background: #fff; border-radius: 16px; border: 1px solid #eceeec; padding: 28px 30px; }
.screening-title { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #1a3a1a; margin: 0 0 6px; }
.screening-sub { font-size: 0.87rem; color: #9aaa9a; margin: 0 0 24px; }

.form-row-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px; }
.form-row-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.82rem; font-weight: 600; color: #6a7a6a; }
.field input, .field select {
  border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 13px; font-size: 0.9rem; font-family: inherit; color: #1a3a1a; width: 100%; background: #fff;
}
.field input:focus, .field select:focus { outline: none; border-color: #14301a; }

.symptoms-label { display: block; font-size: 0.82rem; font-weight: 600; color: #6a7a6a; margin-bottom: 12px; }
.symptoms-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 24px; }
.checkbox-row { display: flex; align-items: center; gap: 10px; background: #f7f9f7; border-radius: 8px; padding: 12px 14px; font-size: 0.87rem; color: #2a2a2a; cursor: pointer; }
.checkbox-row input { width: 17px; height: 17px; accent-color: #14301a; cursor: pointer; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}

.compute-btn { width: 100%; background: #14301a; color: #fff; border: none; border-radius: 999px; padding: 15px; font-weight: 700; font-size: 0.94rem; cursor: pointer; }
.compute-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.results-panel { background: #e3f3ea; border-radius: 12px; padding: 20px 22px; margin-top: 22px; }
.results-eyebrow { display: block; font-size: 0.72rem; letter-spacing: 0.06em; text-transform: uppercase; font-weight: 700; color: #1f8f5c; margin-bottom: 14px; }
.results-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.result-box { background: #fff; border-radius: 10px; padding: 14px; text-align: center; }
.result-label { font-size: 0.72rem; color: #9aaa9a; font-weight: 600; margin: 0 0 4px; }
.result-value { font-family: 'Playfair Display', serif; font-size: 1.15rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.result-unit { font-size: 0.72rem; color: #9aaa9a; margin: 3px 0 0; }
.result-tag { font-size: 0.76rem; font-weight: 700; margin: 4px 0 0; }
.tag-green { color: #1f8f5c; }
.tag-gold { color: #b8860b; }
.tag-blue { color: #2a5a8a; }
.tag-red { color: #c0392b; }

.complete-banner { background: #e3f3ea; border-radius: 12px; padding: 16px 20px; margin-top: 14px; }
.complete-title { display: flex; align-items: center; gap: 7px; font-weight: 700; color: #1f8f5c; font-size: 0.9rem; margin: 0 0 5px; }
.complete-text { font-size: 0.84rem; color: #3a6b4a; line-height: 1.5; margin: 0; }
.complete-text + .complete-text { margin-top: 6px; }
.find-rnd-btn {
  display: inline-flex; align-items: center; gap: 6px; background: #14301a; color: #fff; text-decoration: none;
  padding: 10px 18px; border-radius: 8px; font-weight: 700; font-size: 0.85rem; margin-top: 14px;
}

.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 999px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

@media (max-width: 640px) {
  .form-row-3, .form-row-2, .symptoms-grid, .results-grid { grid-template-columns: 1fr 1fr; }
}
</style>
