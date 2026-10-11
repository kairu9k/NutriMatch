<template>
  <div class="screening-page" :class="{ embedded }">
    <div class="panel">
      <h1 class="screening-title">Pre-Consultation Nutritional Screening</h1>
      <p class="screening-sub">Your data auto-computes BMI, BMR, TDEE, and NRS-2002 risk score.</p>

      <div class="form-row-3">
        <div class="field">
          <label for="scr-height">Height (cm)</label>
          <input
            id="scr-height" v-model.number="form.height" type="number" inputmode="decimal"
            :min="LIMITS.height.min" :max="LIMITS.height.max" step="0.1" placeholder="e.g. 162"
            :class="{ invalid: shownError('height') }" @blur="touched.height = true"
          />
          <span v-if="shownError('height')" class="field-error">{{ shownError('height') }}</span>
          <span v-else class="field-hint">{{ LIMITS.height.min }}–{{ LIMITS.height.max }} cm</span>
        </div>
        <div class="field">
          <label for="scr-weight">Weight (kg)</label>
          <input
            id="scr-weight" v-model.number="form.weight" type="number" inputmode="decimal"
            :min="LIMITS.weight.min" :max="LIMITS.weight.max" step="0.1" placeholder="e.g. 72"
            :class="{ invalid: shownError('weight') }" @blur="touched.weight = true"
          />
          <span v-if="shownError('weight')" class="field-error">{{ shownError('weight') }}</span>
          <span v-else class="field-hint">{{ LIMITS.weight.min }}–{{ LIMITS.weight.max }} kg</span>
        </div>
        <div class="field">
          <label for="scr-age">Age</label>
          <!-- From the date of birth on file — not editable here (the API
               ignores a typed age when a DOB exists). Typed only as a
               fallback for older accounts without one. -->
          <input
            v-if="ageFromProfile" id="scr-age" :value="form.age" type="text" readonly
            class="readonly" aria-describedby="scr-age-note"
          />
          <input
            v-else id="scr-age" v-model.number="form.age" type="number" inputmode="numeric"
            :min="LIMITS.age.min" :max="LIMITS.age.max" step="1" placeholder="e.g. 34"
            :class="{ invalid: shownError('age') }" @blur="touched.age = true"
          />
          <span v-if="ageFromProfile" id="scr-age-note" class="field-hint">
            From your date of birth · <NuxtLink to="/profile-settings">change it in Profile Settings</NuxtLink>
          </span>
          <span v-else-if="shownError('age')" class="field-error">{{ shownError('age') }}</span>
          <span v-else class="field-hint">{{ LIMITS.age.min }}–{{ LIMITS.age.max }} years</span>
        </div>
      </div>

      <div class="form-row-2">
        <div class="field">
          <label for="scr-sex">Sex</label>
          <!-- Given at registration — read-only here, like Age. The dropdown
               is only for accounts that chose "Prefer not to say" (the
               BMR formula needs it); the API saves it to the profile. -->
          <template v-if="sexFromProfile">
            <input id="scr-sex" :value="sexLabel" type="text" readonly class="readonly" />
            <span class="field-hint">
              From your account · <NuxtLink to="/profile-settings">change it in Profile Settings</NuxtLink>
            </span>
          </template>
          <template v-else>
            <select class="nm-select block" id="scr-sex" v-model="form.sex">
              <option value="" disabled>Select sex</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
            </select>
            <span class="field-hint">Needed to compute your BMR. Saved to your profile.</span>
          </template>
        </div>
        <div class="field">
          <label>Activity Level</label>
          <select class="nm-select block" v-model="form.activityLevel">
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
          <p class="results-hint"><Info :size="13" /> Tap a result to see what it means.</p>
          <div class="results-grid" role="tablist" aria-label="Screening results">
            <button
              v-for="box in resultBoxes" :key="box.key"
              type="button" role="tab" class="result-box"
              :class="{ selected: openMetric === box.key }"
              :aria-selected="openMetric === box.key" :aria-controls="`explain-${box.key}`"
              @click="toggleMetric(box.key)"
            >
              <span class="result-info"><Info :size="13" /></span>
              <p class="result-label">{{ box.label }}</p>
              <p class="result-value">{{ box.value }}</p>
              <p v-if="box.tag" class="result-tag" :class="box.tagClass">{{ box.tag }}</p>
              <p v-else class="result-unit">{{ box.unit }}</p>
            </button>
          </div>

          <!-- Plain-language explanation of the selected result. Ranges match
               clinical/services.py (WHO Asia-Pacific BMI, NRS-2002 bands). -->
          <Transition name="explain-fade">
            <div v-if="explanation" :id="`explain-${openMetric}`" :key="openMetric" class="explain-card" role="tabpanel">
              <div class="explain-head">
                <div>
                  <p class="explain-title">{{ explanation.title }}</p>
                  <p class="explain-full">{{ explanation.fullName }}</p>
                </div>
                <button type="button" class="explain-close" aria-label="Close explanation" @click="openMetric = ''"><X :size="16" /></button>
              </div>
              <p class="explain-text">{{ explanation.what }}</p>
              <p class="explain-yours"><strong>Your result:</strong> {{ explanation.yours }}</p>

              <ul v-if="explanation.scale" class="explain-scale">
                <li v-for="row in explanation.scale" :key="row.label" :class="{ current: row.current }">
                  <span class="scale-label">{{ row.label }}</span>
                  <span class="scale-range">{{ row.range }}</span>
                  <span v-if="row.current" class="scale-you">You</span>
                </li>
              </ul>

              <p class="explain-note">{{ explanation.note }}</p>
            </div>
          </Transition>
        </div>

        <div v-if="!embedded" class="complete-banner">
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
import { CheckCircle2, ArrowRight, Info, X } from 'lucide-vue-next'

// `embedded`: used as the last step of client onboarding (ClientOnboarding.vue),
// which shows its own "finish" step instead of the Find-an-RND banner.
const props = defineProps({ embedded: { type: Boolean, default: false } })
const emit = defineEmits(['completed'])

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

// Realistic adult ranges — same limits the API enforces
// (clinical/serializers.py PreConsultationScreeningSerializer).
const LIMITS = {
  height: { min: 100, max: 250, unit: 'cm', label: 'Height' },
  weight: { min: 25, max: 300, unit: 'kg', label: 'Weight' },
  age: { min: 18, max: 120, unit: 'years', label: 'Age' },
}

const ageFromProfile = ref(false)
const sexFromProfile = ref(false)
const sexLabel = computed(() => ({ female: 'Female', male: 'Male' }[form.sex] || ''))
const touched = reactive({ height: false, weight: false, age: false })
const serverErrors = reactive({ height: '', weight: '', age: '' })

function rangeError(key) {
  const value = form[key]
  const { min, max, unit, label } = LIMITS[key]
  if (value === null || value === '') return `Enter your ${label.toLowerCase()}.`
  if (typeof value !== 'number' || Number.isNaN(value)) return 'Enter a number.'
  if (value < min || value > max) return `${label} must be between ${min} and ${max} ${unit}.`
  if (key === 'age' && !Number.isInteger(value)) return 'Enter your age in whole years.'
  if (key !== 'age' && Math.abs(Math.round(value * 10) - value * 10) > 1e-9) return 'Use at most 1 decimal place.'
  return ''
}
const fieldErrors = computed(() => ({
  height: rangeError('height'),
  weight: rangeError('weight'),
  age: ageFromProfile.value ? '' : rangeError('age'),
}))
// A field's error shows once the user has left it (so typing "1" on the way
// to "162" isn't flagged mid-entry), or straight away for a server error.
function shownError(key) {
  if (serverErrors[key]) return serverErrors[key]
  return touched[key] ? fieldErrors.value[key] : ''
}
watch(() => form.height, () => { serverErrors.height = '' })
watch(() => form.weight, () => { serverErrors.weight = '' })
watch(() => form.age, () => { serverErrors.age = '' })

const canCompute = computed(() =>
  !fieldErrors.value.height && !fieldErrors.value.weight && !fieldErrors.value.age
  && form.age > 0 && form.sex !== '' && form.activityLevel !== ''
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
      age: ageFromProfile.value ? undefined : form.age,
      sex: sexFromProfile.value ? undefined : form.sex,
      activity_level: form.activityLevel,
      reduced_intake: form.symptoms.poorAppetite,
      has_chronic_illness: form.symptoms.elevatedGlucose || form.symptoms.recentHospitalization,
      symptoms: checked.length ? checked.join(', ') : undefined,
    })
    emit('completed', result.value)
    toastVisible.value = !props.embedded
    clearTimeout(toastTimer)
    toastTimer = setTimeout(() => { toastVisible.value = false }, 4000)
  } catch (error) {
    const data = error?.data || {}
    const first = (v) => (Array.isArray(v) ? v[0] : v) || ''
    serverErrors.height = first(data.height_cm)
    serverErrors.weight = first(data.weight_kg)
    serverErrors.age = first(data.age)
    const fieldError = serverErrors.height || serverErrors.weight || serverErrors.age
    errorMessage.value = fieldError
      ? ''
      : data.detail || Object.values(data).flat()[0] || 'Could not save your screening. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

/* ---------- Result explanations (tap a result box) ---------- */
const openMetric = ref('')
function toggleMetric(key) {
  openMetric.value = openMetric.value === key ? '' : key
}
watch(result, () => { openMetric.value = '' })

const ACTIVITY_LABELS = Object.fromEntries(activityLevels.map(l => [l.value, l.label]))
const kcal = (v) => Math.round(Number(v)).toLocaleString()

const resultBoxes = computed(() => {
  const r = result.value
  if (!r) return []
  return [
    { key: 'bmi', label: 'BMI', value: Number(r.bmi).toFixed(1), tag: r.bmi_category, tagClass: bmiTagClass.value },
    { key: 'bmr', label: 'BMR', value: r.bmr_kcal ? Math.round(r.bmr_kcal) : '—', unit: 'kcal/day' },
    { key: 'tdee', label: 'TDEE', value: r.tdee_kcal ? Math.round(r.tdee_kcal) : '—', unit: 'kcal/day' },
    { key: 'nrs', label: 'NRS-2002', value: `Score: ${r.nrs_score ?? '—'}`, tag: nrsRiskLabel.value, tagClass: nrsTagClass.value },
  ]
})

// WHO Asia-Pacific cut-offs — same as classify_bmi_asia_pacific().
const BMI_SCALE = [
  { label: 'Underweight', range: 'below 18.5' },
  { label: 'Normal', range: '18.5 – 22.9' },
  { label: 'Overweight (At Risk)', range: '23 – 24.9' },
  { label: 'Obese I', range: '25 – 29.9' },
  { label: 'Obese II', range: '30 and above' },
]
// Same bands as calculate_nrs2002().
const NRS_SCALE = [
  { key: 'no_risk', label: 'No Risk', range: 'score 0 – 2' },
  { key: 'at_risk', label: 'At Risk', range: 'score 3 – 4' },
  { key: 'high_risk', label: 'High Risk', range: 'score 5 and above' },
]

const explanation = computed(() => {
  const r = result.value
  if (!r || !openMetric.value) return null
  const activity = ACTIVITY_LABELS[r.activity_level] || 'your activity level'
  if (openMetric.value === 'bmi') {
    return {
      title: 'BMI', fullName: 'Body Mass Index',
      what: 'A quick check of whether your weight is in a healthy range for your height. It is your weight (kg) divided by your height (m) squared.',
      yours: `${Number(r.bmi).toFixed(1)} — ${r.bmi_category}.`,
      scale: BMI_SCALE.map(row => ({ ...row, current: row.label === r.bmi_category })),
      note: 'NutriMatch uses the WHO Asia-Pacific ranges, which are set lower than the global ones because health risks start at a lower BMI for Asian adults. BMI doesn\'t tell muscle from fat, so your RND looks at it together with your other results.',
    }
  }
  if (openMetric.value === 'bmr') {
    return {
      title: 'BMR', fullName: 'Basal Metabolic Rate',
      what: 'The calories your body burns at complete rest just to stay alive — breathing, keeping your heart beating, and keeping you warm. It is worked out from your weight, height, age and sex (Mifflin-St Jeor equation).',
      yours: r.bmr_kcal
        ? `about ${kcal(r.bmr_kcal)} kcal a day, even if you rested all day.`
        : 'not computed — it needs your age and sex.',
      note: 'This isn\'t how much you should eat — it\'s the starting point for your TDEE.',
    }
  }
  if (openMetric.value === 'tdee') {
    return {
      title: 'TDEE', fullName: 'Total Daily Energy Expenditure',
      what: 'The total calories you burn in a day, including your daily activity. It is your BMR multiplied by an activity factor (Sedentary ×1.2 up to Extra Active ×1.9).',
      yours: r.tdee_kcal
        ? `about ${kcal(r.tdee_kcal)} kcal a day at ${activity}. Eating around this amount keeps your weight about the same.`
        : 'not computed — it needs your age and sex.',
      note: 'Your RND uses this to set your daily calorie target in your meal plan — please don\'t start cutting calories on your own based on it.',
    }
  }
  return {
    title: 'NRS-2002', fullName: 'Nutritional Risk Screening 2002',
    what: 'A standard hospital screening that checks your risk of malnutrition. It looks at your BMI, any weight lost since your last screening, a poor appetite, and health conditions like high blood sugar or a recent hospital stay.',
    yours: `a score of ${r.nrs_score ?? '—'} — ${nrsRiskLabel.value || 'not scored'}.`,
    scale: NRS_SCALE.map(row => ({ label: row.label, range: row.range, current: row.key === r.nrs_risk })),
    note: 'This is a screening, not a diagnosis. Your RND reviews it before your consultation and will talk you through anything that needs attention.',
  }
})

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
  if (profile?.date_of_birth) {
    form.age = ageFromDob(profile.date_of_birth)
    ageFromProfile.value = true
  }
  if (profile?.sex) {
    form.sex = profile.sex
    sexFromProfile.value = true
  }
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
.screening-page.embedded .panel { border: none; padding: 0; }

.panel { background: #fff; border-radius: 16px; border: 1px solid #eceeec; padding: 28px 30px; }
.screening-title { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #1a3a1a; margin: 0 0 6px; }
.screening-sub { font-size: 0.87rem; color: #9aaa9a; margin: 0 0 24px; }

.form-row-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 16px; }
.form-row-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.82rem; font-weight: 600; color: #6a7a6a; }
.field select { min-height: 44px; font-size: 0.9rem; }
.field input {
  border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 13px; font-size: 0.9rem; font-family: inherit; color: #1a3a1a; width: 100%; background: #fff;
}
.field input:focus { outline: none; border-color: #14301a; }
.field input.invalid { border-color: #c0392b; }
.field input.readonly { background: #f3f5f3; color: #4a5a4a; cursor: default; }
.field input.readonly:focus { border-color: #d5dad5; }
.field-error { font-size: 0.75rem; color: #c0392b; line-height: 1.35; }
.field-hint { font-size: 0.75rem; color: #9aaa9a; line-height: 1.35; }
.field-hint a { color: #1a3a1a; font-weight: 600; }

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
.results-hint { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; color: #3a6b4a; margin: -6px 0 12px; }
.results-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.result-box {
  position: relative; background: #fff; border-radius: 10px; padding: 14px; text-align: center;
  border: 2px solid transparent; cursor: pointer; font-family: inherit; width: 100%;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.result-box:hover { border-color: #b9dcc7; }
.result-box:focus-visible { outline: none; border-color: #1f8f5c; }
.result-box.selected { border-color: #1f8f5c; box-shadow: 0 4px 14px rgba(31, 143, 92, 0.15); }
.result-info { position: absolute; top: 8px; right: 8px; color: #9fc4ae; display: flex; }
.result-box.selected .result-info { color: #1f8f5c; }

.explain-card { background: #fff; border-radius: 10px; padding: 16px 18px; margin-top: 12px; border: 1px solid #cfe8da; }
.explain-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 8px; }
.explain-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.explain-full { font-size: 0.76rem; color: #8a9a8a; margin: 2px 0 0; }
.explain-close { background: none; border: none; color: #8a9a8a; cursor: pointer; padding: 2px; display: flex; }
.explain-close:hover { color: #1a3a1a; }
.explain-text { font-size: 0.86rem; color: #3a4a3a; line-height: 1.55; margin: 0 0 8px; }
.explain-yours { font-size: 0.86rem; color: #1a3a1a; line-height: 1.55; margin: 0 0 10px; background: #f0f9f4; border-radius: 8px; padding: 8px 12px; }
.explain-scale { list-style: none; padding: 0; margin: 0 0 10px; border: 1px solid #eceeec; border-radius: 8px; overflow: hidden; }
.explain-scale li { display: flex; align-items: center; gap: 10px; padding: 8px 12px; font-size: 0.82rem; border-top: 1px solid #f0f2f0; }
.explain-scale li:first-child { border-top: none; }
.explain-scale li.current { background: #e3f3ea; font-weight: 700; }
.scale-label { flex: 1; color: #1a3a1a; }
.scale-range { color: #6a7a6a; white-space: nowrap; }
.scale-you { background: #1f8f5c; color: #fff; font-size: 0.66rem; font-weight: 700; padding: 2px 8px; border-radius: 999px; }
.explain-note { font-size: 0.78rem; color: #6a7a6a; line-height: 1.5; margin: 0; }
.explain-fade-enter-active, .explain-fade-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.explain-fade-enter-from, .explain-fade-leave-to { opacity: 0; transform: translateY(-4px); }
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
  .panel { padding: 22px 18px; }
  .form-row-3, .results-grid { grid-template-columns: 1fr 1fr; }
  .form-row-2, .symptoms-grid { grid-template-columns: 1fr; }
}
@media (max-width: 420px) {
  .form-row-3 { grid-template-columns: 1fr; }
}
</style>
