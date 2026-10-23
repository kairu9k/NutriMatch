<template>
  <!-- Client onboarding (strict, 2026-10-10): the route guard sends a client
       here until the required steps are done (date of birth + sex, a food
       allergies answer, and a screening). Every step saves as you go; the
       page resumes at the first unfinished step. -->
  <div class="onb-page">
    <header class="onb-header">
      <div class="brand">
        <img src="/resources/nutrimatchlogo.png" alt="" class="brand-logo" />
        <span class="brand-text">Nutri<span class="brand-gold">Match</span></span>
      </div>
      <button class="link-btn" type="button" @click="signOut">Sign out</button>
    </header>

    <main class="onb-main">
      <ol class="onb-steps" aria-label="Setup steps">
        <li v-for="(s, i) in STEPS" :key="s.key" class="onb-step" :class="{ active: i === stepIndex, done: i < stepIndex }">
          <span class="onb-dot">{{ i < stepIndex ? '✓' : i + 1 }}</span>
          <span class="onb-step-label">{{ s.label }}</span>
        </li>
      </ol>

      <p v-if="loadError" class="form-error">{{ loadError }}</p>
      <div v-else-if="isLoading" class="card"><p class="muted">Loading…</p></div>

      <!-- 1 · WELCOME -->
      <section v-else-if="step === 'welcome'" class="card">
        <p class="eyebrow">Welcome sa NutriMatch 💚</p>
        <h1 class="title">Hi {{ auth.user?.first_name }}, sobrang saya namin na nandito ka!</h1>
        <p class="lead">
          Ang pag-aalaga sa kinakain mo ay isa sa pinakamagandang regalo mo sa sarili mo — at hindi mo kailangang gawin ito mag-isa.
          Mga 3 minutes lang ito, at gagamitin ito ng RND mo para paghandaan ang first consultation mo.
        </p>
        <ol class="journey">
          <li><span class="j-num">1</span><div><strong>Kilalanin ka namin</strong><p>Ang basic details at health background mo — kasama ang food allergies, kung meron.</p></div></li>
          <li><span class="j-num">2</span><div><strong>Mabilis na health screening</strong><p>Height, weight, at activity mo, para ma-estimate ang BMI at daily calorie needs mo.</p></div></li>
          <li><span class="j-num">3</span><div><strong>Hanapin ang RND mo at mag-book</strong><p>Pumili ng licensed Registered Nutritionist-Dietitian, magbayad bago ang session, then mag-consult sa video call o in person.</p></div></li>
        </ol>
        <p class="privacy">
          <ShieldCheck :size="15" /> Safe ang health information mo — sa RND mo lang ito ise-share, ayon sa Data Privacy Act of 2012 (RA 10173).
        </p>
        <div class="actions">
          <button class="nm-btn-dark" type="button" @click="go('about')">Tara, simulan na natin <ArrowRight :size="15" /></button>
        </div>
      </section>

      <!-- 2 · ABOUT YOU -->
      <section v-else-if="step === 'about'" class="card">
        <p class="eyebrow">Step 2 of 4</p>
        <h1 class="title">About you</h1>
        <p class="lead">We use your age and sex to calculate your calorie needs accurately.</p>
        <div class="grid-2">
          <div class="field">
            <label for="ob-dob">Date of birth <span class="req">Required</span></label>
            <input id="ob-dob" v-model="about.dob" type="date" :max="latestBirthDate" min="1900-01-01" :class="{ invalid: aboutErrors.dob }" />
            <p v-if="aboutErrors.dob" class="field-error">{{ aboutErrors.dob }}</p>
          </div>
          <div class="field">
            <label for="ob-sex">Sex <span class="req">Required</span></label>
            <select class="nm-select block" id="ob-sex" v-model="about.sex" :class="{ invalid: aboutErrors.sex }">
              <option value="" disabled>Select</option>
              <option value="female">Female</option>
              <option value="male">Male</option>
            </select>
            <p v-if="aboutErrors.sex" class="field-error">{{ aboutErrors.sex }}</p>
            <p v-else class="hint">Biological sex — it changes how calories are calculated.</p>
          </div>
          <div class="field">
            <label for="ob-lang">Preferred language</label>
            <select class="nm-select block" id="ob-lang" v-model="about.language">
              <option value="">Select</option>
              <option v-for="l in LANGUAGE_OPTIONS" :key="l.code" :value="l.code">{{ l.label }}</option>
            </select>
          </div>
          <div class="field">
            <label for="ob-phone">Mobile number <span class="opt">Optional</span></label>
            <PhoneInput id="ob-phone" v-model="about.phone" label="mobile number" :error="aboutErrors.phone" />
          </div>
        </div>
        <p v-if="saveError" class="form-error">{{ saveError }}</p>
        <div class="actions">
          <button class="nm-btn-soft" type="button" @click="go('welcome')">Back</button>
          <button class="nm-btn-dark" type="button" :disabled="isSaving" @click="saveAbout">{{ isSaving ? 'Saving…' : 'Continue' }} <ArrowRight :size="15" /></button>
        </div>
      </section>

      <!-- 3 · HEALTH BACKGROUND -->
      <section v-else-if="step === 'health'" class="card">
        <p class="eyebrow">Step 3 of 4</p>
        <h1 class="title">Your health background</h1>
        <p class="lead">Your RND reads this before your consultation and plans your meals around it.</p>

        <div class="field">
          <label for="ob-condition">Primary health condition</label>
          <select class="nm-select block" id="ob-condition" v-model="health.condition">
            <option value="">None / not sure</option>
            <option v-for="c in CONDITION_OPTIONS" :key="c" :value="c">{{ c }}</option>
            <option value="__other">Other</option>
          </select>
          <input v-if="health.condition === '__other'" v-model="health.conditionOther" type="text" maxlength="100" placeholder="Please specify, e.g. High cholesterol" class="mt-8" />
        </div>

        <fieldset class="field">
          <legend>Food allergies <span class="req">Required</span></legend>
          <div class="radio-row" role="radiogroup">
            <label class="radio-card" :class="{ checked: health.hasAllergies === false }">
              <input v-model="health.hasAllergies" type="radio" :value="false" /> I have no food allergies
            </label>
            <label class="radio-card" :class="{ checked: health.hasAllergies === true }">
              <input v-model="health.hasAllergies" type="radio" :value="true" /> I have food allergies
            </label>
          </div>
          <template v-if="health.hasAllergies">
            <div class="chips">
              <button v-for="a in ALLERGY_OPTIONS" :key="a" type="button" class="chip" :class="{ on: health.allergies.includes(a) }" :aria-pressed="health.allergies.includes(a)" @click="toggle(health.allergies, a)">{{ a }}</button>
              <button v-for="a in customAllergies" :key="a" type="button" class="chip on" :aria-pressed="true" @click="toggle(health.allergies, a)">{{ a }} ✕</button>
            </div>
            <div class="add-row">
              <input v-model="newAllergy" type="text" maxlength="60" placeholder="Other allergy, e.g. Mango" @keydown.enter.prevent="addAllergy()" />
              <button class="nm-btn-soft nm-btn-sm" type="button" :disabled="!newAllergy.trim()" @click="addAllergy()">Add</button>
            </div>
          </template>
          <p v-if="healthErrors.allergies" class="field-error">{{ healthErrors.allergies }}</p>
        </fieldset>

        <fieldset class="field">
          <legend>Dietary restrictions <span class="opt">Optional</span></legend>
          <div class="chips">
            <button v-for="d in DIET_OPTIONS" :key="d" type="button" class="chip" :class="{ on: health.diet.includes(d) }" :aria-pressed="health.diet.includes(d)" @click="toggle(health.diet, d)">{{ d }}</button>
            <button v-for="d in customDiet" :key="d" type="button" class="chip on" :aria-pressed="true" @click="toggle(health.diet, d)">{{ d }} ✕</button>
          </div>
          <div class="add-row">
            <input v-model="newDiet" type="text" maxlength="60" placeholder="Other restriction, e.g. No spicy food" @keydown.enter.prevent="addDiet()" />
            <button class="nm-btn-soft nm-btn-sm" type="button" :disabled="!newDiet.trim()" @click="addDiet()">Add</button>
          </div>
        </fieldset>

        <div class="grid-2">
          <div class="field">
            <label for="ob-religion">Religion <span class="opt">Optional</span></label>
            <select class="nm-select block" id="ob-religion" v-model="health.religion">
              <option value="">Prefer not to say</option>
              <option v-for="r in RELIGION_OPTIONS" :key="r" :value="r">{{ r }}</option>
            </select>
            <p class="hint">Only so meal plans respect any food practices.</p>
          </div>
        </div>

        <fieldset class="field">
          <legend>Your goals <span class="opt">Optional</span></legend>
          <div class="chips">
            <button v-for="g in GOAL_OPTIONS" :key="g" type="button" class="chip" :class="{ on: health.goals.includes(g) }" :aria-pressed="health.goals.includes(g)" @click="toggle(health.goals, g)">{{ g }}</button>
            <button v-for="g in customGoals" :key="g" type="button" class="chip on" :aria-pressed="true" @click="toggle(health.goals, g)">{{ g }} ✕</button>
          </div>
          <div class="add-row">
            <input v-model="newGoal" type="text" maxlength="60" placeholder="Other goal, e.g. Improve energy" @keydown.enter.prevent="addGoal()" />
            <button class="nm-btn-soft nm-btn-sm" type="button" :disabled="!newGoal.trim()" @click="addGoal()">Add</button>
          </div>
        </fieldset>

        <p v-if="saveError" class="form-error">{{ saveError }}</p>
        <div class="actions">
          <button class="nm-btn-soft" type="button" @click="go('about')">Back</button>
          <button class="nm-btn-dark" type="button" :disabled="isSaving" @click="saveHealth">{{ isSaving ? 'Saving…' : 'Continue' }} <ArrowRight :size="15" /></button>
        </div>
      </section>

      <!-- 4 · SCREENING -->
      <section v-else-if="step === 'screening'" class="card">
        <p class="eyebrow">Step 4 of 4</p>
        <template v-if="screeningDone && !redoScreening">
          <h1 class="title">Your screening is on file</h1>
          <p class="lead">Recorded {{ screeningDate }}. It's your starting point and can't be changed. New readings go in the Progress Tracker.</p>
          <div class="actions">
            <button class="nm-btn-soft" type="button" @click="redoScreening = true">View it</button>
            <button class="nm-btn-dark" type="button" :disabled="isFinishing" @click="finish">{{ isFinishing ? 'Finishing…' : 'Finish setup' }} <ArrowRight :size="15" /></button>
          </div>
        </template>
        <template v-else>
          <PreConsultationScreening embedded @completed="onScreened" />
          <div v-if="screeningDone" class="actions">
            <button class="nm-btn-soft" type="button" @click="go('health')">Back</button>
            <button class="nm-btn-dark" type="button" :disabled="isFinishing" @click="finish">{{ isFinishing ? 'Finishing…' : 'Finish setup' }} <ArrowRight :size="15" /></button>
          </div>
          <div v-else class="actions">
            <button class="nm-btn-soft" type="button" @click="go('health')">Back</button>
          </div>
        </template>
        <p v-if="finishError" class="form-error">{{ finishError }}</p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ArrowRight, ShieldCheck } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'
import { phoneError } from '~/utils/phone'

const auth = useAuthStore()
const { get, patch, post } = useApi()

const STEPS = [
  { key: 'welcome', label: 'Welcome' },
  { key: 'about', label: 'About you' },
  { key: 'health', label: 'Health background' },
  { key: 'screening', label: 'Screening' },
]
const step = ref('welcome')
const stepIndex = computed(() => STEPS.findIndex(s => s.key === step.value))
function go(key) {
  saveError.value = ''
  step.value = key
  window.scrollTo({ top: 0 })
}

// Same lists as sign-up / Profile Settings.
const CONDITION_OPTIONS = ['Hypertension', 'Type 2 Diabetes', 'Obesity Management', 'Renal Nutrition']
const LANGUAGE_OPTIONS = [
  { code: 'tl', label: 'Filipino (Tagalog)' },
  { code: 'ceb', label: 'Bisaya (Cebuano)' },
  { code: 'ilo', label: 'Ilocano' },
  { code: 'en', label: 'English' },
]
const ALLERGY_OPTIONS = ['Shrimp / shellfish', 'Fish', 'Peanuts', 'Tree nuts', 'Eggs', 'Milk', 'Soy', 'Wheat / gluten']
const DIET_OPTIONS = ['Halal', 'No pork', 'No beef', 'Vegetarian', 'Vegan', 'Pescatarian', 'Low sodium', 'Lactose-free']
const RELIGION_OPTIONS = ['Roman Catholic', 'Christian', 'Islam', 'Iglesia ni Cristo', 'Seventh-day Adventist', 'Other']
const GOAL_OPTIONS = ['Lose weight', 'Gain weight', 'Control blood sugar', 'Lower blood pressure', 'Lower cholesterol', 'Build muscle', 'Eat healthier']

const isLoading = ref(true)
const loadError = ref('')
const isSaving = ref(false)
const saveError = ref('')

const about = reactive({ dob: '', sex: '', language: '', phone: '' })
const aboutErrors = reactive({ dob: '', sex: '', phone: '' })
const health = reactive({ condition: '', conditionOther: '', hasAllergies: null, allergies: [], diet: [], religion: '', goals: [] })
const healthErrors = reactive({ allergies: '' })
const newAllergy = ref('')
const newDiet = ref('')
const newGoal = ref('')
const otherConditions = ref([])
const customAllergies = computed(() => health.allergies.filter(a => !ALLERGY_OPTIONS.includes(a)))
const customDiet = computed(() => health.diet.filter(d => !DIET_OPTIONS.includes(d)))
const customGoals = computed(() => health.goals.filter(g => !GOAL_OPTIONS.includes(g)))

function toggle(list, value) {
  const i = list.indexOf(value)
  if (i >= 0) list.splice(i, 1)
  else list.push(value)
}
function addCustom(list, value) {
  const v = value.trim()
  if (v && !list.some(x => x.toLowerCase() === v.toLowerCase())) list.push(v)
}
// Refs are auto-unwrapped in the template, so use one function per field
// and read/clear the ref's .value here in the script.
function addAllergy() { addCustom(health.allergies, newAllergy.value); newAllergy.value = '' }
function addDiet() { addCustom(health.diet, newDiet.value); newDiet.value = '' }
function addGoal() { addCustom(health.goals, newGoal.value); newGoal.value = '' }

// Clients must be 18+ (accounts/validators.py).
const latestBirthDate = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 18)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

const screeningDone = ref(false)
const screeningDate = ref('')
const redoScreening = ref(false)

function firstError(data, ...keys) {
  for (const k of keys) {
    const v = data?.[k]
    if (v) return Array.isArray(v) ? v[0] : v
  }
  return ''
}

async function saveAbout() {
  saveError.value = ''
  aboutErrors.dob = !about.dob ? 'Enter your date of birth.' : about.dob > latestBirthDate.value ? 'You must be at least 18 years old.' : ''
  aboutErrors.sex = about.sex ? '' : 'Choose one — it changes how your calories are calculated.'
  aboutErrors.phone = phoneError(about.phone)
  if (aboutErrors.dob || aboutErrors.sex || aboutErrors.phone) return
  isSaving.value = true
  try {
    await patch('/client/profile/', { date_of_birth: about.dob, sex: about.sex, language_code: about.language || null })
    if (about.phone !== (auth.user?.phone || '')) {
      await patch('/auth/me/', { phone: about.phone || null })
    }
    go('health')
  } catch (error) {
    aboutErrors.dob = firstError(error?.data, 'date_of_birth')
    aboutErrors.phone = firstError(error?.data, 'phone')
    saveError.value = aboutErrors.dob || aboutErrors.phone ? '' : firstError(error?.data, 'detail', 'sex') || 'Could not save. Please try again.'
  } finally {
    isSaving.value = false
  }
}

async function saveHealth() {
  saveError.value = ''
  healthErrors.allergies = ''
  // Auto-add anything typed but not yet added with the "Add" button.
  if (health.hasAllergies) addAllergy()
  addDiet()
  addGoal()
  if (health.hasAllergies === null) {
    healthErrors.allergies = 'Please answer this — your RND needs to know before planning meals.'
    return
  }
  if (health.hasAllergies && !health.allergies.length) {
    healthErrors.allergies = 'Choose or add at least one allergy, or pick "I have no food allergies".'
    return
  }
  const primary = health.condition === '__other' ? health.conditionOther.trim() : health.condition
  if (health.condition === '__other' && !primary) {
    saveError.value = 'Please type your condition, or pick one from the list.'
    return
  }
  isSaving.value = true
  try {
    await patch('/client/profile/', {
      medical_conditions: primary ? [primary, ...otherConditions.value] : otherConditions.value,
      allergies: health.hasAllergies ? health.allergies : [],
      dietary_restrictions: health.diet,
      religion: health.religion,
      health_goals: health.goals,
    })
    go('screening')
  } catch (error) {
    saveError.value = firstError(error?.data, 'detail', 'allergies', 'dietary_restrictions', 'health_goals', 'medical_conditions') || 'Could not save. Please try again.'
  } finally {
    isSaving.value = false
  }
}

function onScreened() {
  screeningDone.value = true
  // Keep the form (now showing its results) on screen rather than swapping
  // to the "on file" view — the client should see their BMI/TDEE first.
  redoScreening.value = true
}

const isFinishing = ref(false)
const finishError = ref('')
async function finish() {
  isFinishing.value = true
  finishError.value = ''
  try {
    await post('/auth/me/onboarding/complete/')
    await auth.fetchMe()
    await navigateTo('/client-dashboard')  // the welcome pop-up opens there
  } catch (error) {
    finishError.value = error?.data?.detail || 'Could not finish setup. Please try again.'
  } finally {
    isFinishing.value = false
  }
}

function signOut() {
  auth.logout()
  navigateTo('/login')
}

onMounted(async () => {
  try {
    const [status, profile, latest] = await Promise.all([
      get('/auth/me/onboarding/'),
      get('/client/profile/'),
      get('/client/screening/latest/').catch(() => null),
    ])
    if (status.complete) {
      await auth.fetchMe()
      return navigateTo('/client-dashboard')
    }
    about.dob = profile.date_of_birth || ''
    about.sex = profile.sex || ''
    about.language = profile.language_code || ''
    about.phone = profile.user?.phone || ''
    const hp = profile.health_profile || {}
    const conditions = hp.medical_conditions || []
    otherConditions.value = conditions.slice(1)
    if (conditions[0]) {
      if (CONDITION_OPTIONS.includes(conditions[0])) health.condition = conditions[0]
      else { health.condition = '__other'; health.conditionOther = conditions[0] }
    }
    if (Array.isArray(hp.allergies)) {
      health.hasAllergies = hp.allergies.length > 0
      health.allergies = [...hp.allergies]
    }
    health.diet = [...(hp.dietary_restrictions || [])]
    health.goals = [...(hp.health_goals || [])]
    health.religion = hp.religion || ''
    if (latest) {
      screeningDone.value = true
      screeningDate.value = new Date(latest.created_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    }
    // Resume at the screening once the health step is answered; otherwise
    // start at Welcome (a new client already has DOB/sex from sign-up, so
    // "About you" alone doesn't mean they've started — it's pre-filled).
    const done = Object.fromEntries(status.steps.map(s => [s.key, s.done]))
    if (done.about && done.health) step.value = 'screening'
  } catch {
    loadError.value = 'Could not load your account. Please refresh the page.'
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
* { box-sizing: border-box; }
.onb-page { min-height: 100vh; background: #f7f8f6; font-family: 'Inter', sans-serif; color: #1a3a1a; }
.onb-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; background: #004D3A; }
.brand { display: flex; align-items: center; gap: 10px; }
.brand-logo { width: 30px; height: 30px; object-fit: contain; }
.brand-text { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.1rem; color: #fff; }
.brand-gold { color: #D4A017; }
.link-btn { display: inline-flex; align-items: center; min-height: 32px; padding: 0 12px; border-radius: 8px; background: rgba(255, 255, 255, 0.14); border: none; color: #fff; font-size: 0.8rem; font-weight: 600; cursor: pointer; font-family: inherit; }
.link-btn:hover { background: rgba(255, 255, 255, 0.24); }
.link-btn:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }

.onb-main { max-width: 720px; margin: 0 auto; padding: 28px 16px 60px; }
.onb-steps { list-style: none; padding: 0; margin: 0 0 20px; display: flex; gap: 55px; }
.onb-step { flex: 1; display: flex; align-items: center; gap: 8px; font-size: 0.88rem; color: #8a9a8a; font-weight: 600; min-width: 0; }
.onb-dot { width: 26px; height: 26px; border-radius: 50%; border: 2px solid #d5dad5; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; flex-shrink: 0; background: #fff; }
.onb-step.active { color: #1a3a1a; }
.onb-step.active .onb-dot { border-color: #1a3a1a; background: #1a3a1a; color: #fff; }
.onb-step.done .onb-dot { border-color: #D4A017; background: #D4A017; color: #1a3a1a; }
.onb-step-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.card { background: #fff; border: 1px solid #eceeec; border-radius: 16px; padding: 28px; }
.eyebrow { font-size: 1.1rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #b8860b; margin: 0 0 6px; }
.title { font-family: 'Playfair Display', serif; font-size: 1.8rem; margin: 0 0 8px; line-height: 1.25; }
.lead { font-size: 1.1rem; color: #4a5a4a; margin: 0 0 22px; line-height: 1.55; }
.muted { color: #8a9a8a; font-size: 0.88rem; margin: 0; }

.journey { list-style: none; padding: 0; margin: 0 0 20px; display: flex; flex-direction: column; gap: 14px; }
.journey li { display: flex; gap: 14px; align-items: flex-start; }
.journey strong { font-size: 1.2rem; }
.journey p { margin: 3px 0 0; font-size: 0.84rem; color: #6a7a6a; line-height: 1.5; }
.j-num { width: 30px; height: 30px; border-radius: 50%; background: #eef3ec; color: #1e4a26; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.privacy { display: flex; gap: 8px; align-items: flex-start; font-size: 1.0rem; color: #3a6b4a; background: #f0f9f4; border-radius: 10px; padding: 10px 14px; margin: 0 0 4px; line-height: 1.5; }
.privacy svg { flex-shrink: 0; margin-top: 2px; }

.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px 20px; }
.field { display: flex; flex-direction: column; gap: 6px; margin: 0 0 18px; min-width: 0; border: none; padding: 0; }
.field label, .field legend { font-size: 0.84rem; font-weight: 600; color: #1a3a1a; padding: 0; margin-bottom: 2px; }
.req { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: #c0392b; background: #fbeaea; border-radius: 4px; padding: 1px 6px; margin-left: 6px; vertical-align: middle; }
.opt { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: #6a7a6a; background: #eef1ee; border-radius: 4px; padding: 1px 6px; margin-left: 6px; vertical-align: middle; }
.field select { width: 100%; min-height: 44px; font-size: 0.9rem; }
.field input { width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 13px; font-size: 0.9rem; font-family: inherit; color: #1a3a1a; background: #fff; }
.field input:focus { outline: none; border-color: #1a3a1a; }
.field .invalid { border-color: #c0392b; }
.mt-8 { margin-top: 8px; }
.hint { font-size: 0.76rem; color: #8a9a8a; margin: 0; }
.field-error { font-size: 0.78rem; color: #c0392b; margin: 0; }
.form-error { background: #fdecec; border: 1px solid #f3b8b8; color: #a12525; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 12px 0 0; }

.radio-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.field .radio-card { display: flex; align-items: center; gap: 10px; border: 1.5px solid #d5dad5; border-radius: 10px; padding: 12px 14px; margin: 0; font-size: 0.86rem; font-weight: 600; cursor: pointer; background: #fff; }
.radio-card input { width: auto; accent-color: #1a3a1a; margin: 0; }
.radio-card.checked { border-color: #1a3a1a; background: #f0f5f0; }
.chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.chip { border: 1.5px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 999px; padding: 7px 13px; font-size: 0.8rem; font-weight: 600; cursor: pointer; font-family: inherit; }
.chip:hover { border-color: #9aaa9a; }
.chip.on { border-color: #1a3a1a; background: #1a3a1a; color: #fff; }
.add-row { display: flex; gap: 8px; margin-top: 8px; }
.add-row input { flex: 1; }

.actions { display: flex; justify-content: space-between; gap: 10px; margin-top: 22px; }
.actions > :only-child { margin-left: auto; }
.btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 6px; background: #163a1c; color: #fff; border: none; border-radius: 8px; padding: 11px 20px; font-size: 0.88rem; font-weight: 600; cursor: pointer; font-family: inherit; }
.btn-dark:hover:not(:disabled) { background: #0f2a14; }
.btn-dark:disabled { opacity: 0.55; cursor: not-allowed; }
.outline-btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: none; background: #e3efe7; color: #0a4a37; border-radius: 8px; padding: 11px 18px; font-size: 0.86rem; font-weight: 600; cursor: pointer; font-family: inherit; }
.outline-btn:hover:not(:disabled) { background: #d3e7da; }
.outline-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.outline-btn.small { padding: 9px 14px; font-size: 0.8rem; }

@media (max-width: 640px) {
  .card { padding: 20px 16px; }
  .title { font-size: 1.35rem; }
  .grid-2, .radio-row { grid-template-columns: 1fr; }
  .onb-step-label { display: none; }
  .onb-step.active { flex: 2; }
  .onb-step.active .onb-step-label { display: inline; overflow: visible; }
  .actions { flex-direction: column-reverse; }
  .actions > * { width: 100%; }
}
</style>