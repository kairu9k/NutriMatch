<template>
  <!-- Client onboarding (strict, 2026-10-10): the route guard sends a client
       here until the required steps are done (date of birth + sex, a food
       allergies answer, and a screening). Every step saves as you go; the
       page resumes at the first unfinished step. -->
  <div class="nm-onb">
    <!-- LEFT: plate photo + the steps (desktop only, stays put) -->
    <aside class="nm-left">
      <div class="nm-stage">
        <img class="nm-left-photo" :src="plateImg" alt="A balanced plate: half vegetables, a quarter whole grains and a quarter protein" />
      </div>
      <div class="nm-left-shade" aria-hidden="true"></div>
      <div class="nm-left-vignette" aria-hidden="true"></div>
      <div class="nm-frame" aria-hidden="true"></div>
      <!-- Go / Grow / Glow labels sit above the dark fade so they stay clear -->
      <div class="nm-stage nm-stage-top">
        <div class="nm-pins">
          <div v-for="pin in platePins" :key="pin.tag" class="nm-pin" :class="pin.side" :style="{ left: pin.x, top: pin.y }">
            <span class="nm-dot" aria-hidden="true"></span>
            <span class="nm-pin-line" aria-hidden="true"></span>
            <span class="nm-tag">
              <span class="nm-tag-key">{{ pin.tag }}</span>
              {{ pin.label }}
              <span class="nm-tag-share">{{ pin.share }}</span>
            </span>
          </div>
        </div>
      </div>

      <div class="nm-left-inner">
        <div class="nm-brand">
          <img src="/resources/nutrimatchlogo.png" alt="" class="nm-brand-logo" />
          <span class="nm-brand-text">Nutri<span>Match</span></span>
        </div>

        <div class="nm-welcome">
          <span class="nm-eyebrow"><span class="nm-eyebrow-line" aria-hidden="true"></span>WELCOME</span>
          <p class="nm-hero">Let's get your <em>plate</em> ready.</p>

          <p class="nm-welcome-sub">A few quick questions so your RND can plan meals that fit your body and the food you love.</p>
        </div>
      </div>
    </aside>

    <!-- RIGHT: the form (scrolls on its own on desktop) -->
    <main ref="rightPane" class="nm-right">
      <div class="nm-mobile-brand">
        <img src="/resources/nutrimatchlogo.png" alt="" class="nm-mobile-logo" />
        <span class="nm-mobile-text">Nutri<span>Match</span></span>
      </div>

      <div class="nm-right-top">
        <button class="nm-back" type="button" @click="signOut"><LogOut :size="15" aria-hidden="true" />Sign out</button>
      </div>

      <div class="nm-box-wrap">
        <div class="nm-box" :class="{ 'is-wide': step === 'health' || step === 'screening' }">
          <!-- steps: the first thing the client sees -->
          <nav class="ob-stepper" aria-label="Setup steps">
            <p class="ob-stepper-top">STEP {{ stepIndex + 1 }} OF {{ STEPS.length }}</p>
            <ol>
              <li v-for="(s, i) in STEPS" :key="s.key" :class="{ active: i === stepIndex, done: i < stepIndex, reached: i <= stepIndex }">
                <span class="ob-sdot">{{ i < stepIndex ? '✓' : i + 1 }}</span>
                <span class="ob-slab">{{ s.label }}</span>
              </li>
            </ol>
          </nav>

          <p v-if="loadError" class="form-error">{{ loadError }}</p>
          <div v-else-if="isLoading" class="ob-loading"><span class="ob-spin" aria-hidden="true"></span><p class="muted">Loading…</p></div>

          <!-- 1. Welcome -->
          <section v-else-if="step === 'welcome'">
            <h1 class="nm-title">Hi {{ auth.user?.first_name }}, we're so glad you're <em>here!</em></h1>
            <p class="ob-lead">
              Taking care of what you eat is one of the best gifts you can give yourself, and you don't have to do it alone.
              Your RND will use this to prepare for your first consultation.
            </p>
            <span class="ob-time"><Clock :size="15" aria-hidden="true" />Takes about 3 minutes</span>

            <ol class="ob-journey">
              <li v-for="(j, i) in journey" :key="j.title" class="ob-item">
                <span class="ob-item-icon" aria-hidden="true"><component :is="j.icon" :size="22" :stroke-width="1.9" /><span class="ob-item-num">{{ i + 1 }}</span></span>
                <span class="ob-item-text"><strong>{{ j.title }}</strong><span>{{ j.text }}</span></span>
              </li>
            </ol>

            <div class="ob-privacy">
              <span class="ob-privacy-icon" aria-hidden="true"><ShieldCheck :size="15" /></span>
              <p>Your health information is safe. It is shared only with your RND, under the Data Privacy Act of 2012 (RA 10173).</p>
            </div>

            <button class="ob-btn ob-btn-block" type="button" @click="go('about')">Let's get started<ArrowRight :size="18" aria-hidden="true" /></button>
          </section>

          <!-- 2. About you -->
          <section v-else-if="step === 'about'">
            <div class="nm-head">
              <h1 class="nm-title">About you</h1>
              <p class="ob-sub">We use your age and sex to calculate your calorie needs accurately.</p>
            </div>

            <div class="ob-grid">
              <div class="ob-field">
                <label for="ob-dob">Date of birth</label>
                <div class="ob-wrap" :class="{ locked: knownDob }">
                  <DateField id="ob-dob" v-model="about.dob" :max="latestBirthDate" min="1900-01-01" year-select :disabled="knownDob" :invalid="!!aboutErrors.dob" placeholder="Select date" />
                </div>
                <p v-if="aboutErrors.dob" class="field-error">{{ aboutErrors.dob }}</p>
                <p v-else-if="knownDob" class="hint">From your sign-up. You can change it later in Profile Settings.</p>
              </div>
              <div class="ob-field">
                <label for="ob-sex">Sex</label>
                <select id="ob-sex" v-model="about.sex" class="ob-control" :disabled="knownSex" :class="{ invalid: aboutErrors.sex }">
                  <option value="" disabled>Select</option>
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
                <p v-if="aboutErrors.sex" class="field-error">{{ aboutErrors.sex }}</p>
                <p v-else-if="knownSex" class="hint">From your sign-up. You can change it later in Profile Settings.</p>
                <p v-else class="hint">Biological sex. It changes how calories are calculated.</p>
              </div>
              <div class="ob-field">
                <label for="ob-lang">Preferred language</label>
                <select id="ob-lang" v-model="about.language" class="ob-control">
                  <option value="">Select</option>
                  <option v-for="l in LANGUAGE_OPTIONS" :key="l.code" :value="l.code">{{ l.label }}</option>
                </select>
              </div>
              <div class="ob-field">
                <label for="ob-phone">Mobile number <span class="opt">Optional</span></label>
                <div class="ob-wrap">
                  <PhoneInput id="ob-phone" v-model="about.phone" label="mobile number" :error="aboutErrors.phone" />
                </div>
              </div>
            </div>

            <p v-if="saveError" class="form-error">{{ saveError }}</p>
            <div class="ob-actions">
              <button class="ob-btn-back" type="button" @click="go('welcome')"><ArrowLeft :size="16" aria-hidden="true" />Back</button>
              <button class="ob-btn" type="button" :disabled="isSaving" @click="saveAbout">
                <span v-if="isSaving" class="ob-spin light" aria-hidden="true"></span>{{ isSaving ? 'Saving…' : 'Continue' }}<ArrowRight v-if="!isSaving" :size="18" aria-hidden="true" />
              </button>
            </div>
          </section>

          <!-- 3. Health background -->
          <section v-else-if="step === 'health'">
            <div class="nm-head">
              <h1 class="nm-title">Your health background</h1>
              <p class="ob-sub">Your RND reads this before your consultation and plans your meals around it.</p>
            </div>

            <div class="ob-field">
              <label for="ob-condition">Primary health condition</label>
              <select id="ob-condition" v-model="health.condition" class="ob-control">
                <option value="">None / not sure</option>
                <option v-for="c in CONDITION_OPTIONS" :key="c" :value="c">{{ c }}</option>
                <option value="__other">Other</option>
              </select>
              <input v-if="health.condition === '__other'" v-model="health.conditionOther" type="text" maxlength="100" placeholder="Please specify, e.g. High cholesterol" class="ob-control" />
            </div>

            <fieldset class="ob-field">
              <legend>Food allergies <span class="req">Required</span></legend>
              <div class="ob-radio-row" role="radiogroup">
                <label class="ob-radio" :class="{ checked: health.hasAllergies === false }">
                  <input v-model="health.hasAllergies" type="radio" :value="false" /><span class="ob-radio-dot" aria-hidden="true"></span>I have no food allergies
                </label>
                <label class="ob-radio" :class="{ checked: health.hasAllergies === true }">
                  <input v-model="health.hasAllergies" type="radio" :value="true" /><span class="ob-radio-dot" aria-hidden="true"></span>I have food allergies
                </label>
              </div>
              <template v-if="health.hasAllergies">
                <div class="ob-chips">
                  <button v-for="a in ALLERGY_OPTIONS" :key="a" type="button" class="ob-chip allergy" :class="{ on: health.allergies.includes(a) }" :aria-pressed="health.allergies.includes(a)" @click="toggle(health.allergies, a)"><span class="ob-tick" aria-hidden="true"><Check :size="11" :stroke-width="3.4" /></span>{{ a }}</button>
                  <button v-for="a in customAllergies" :key="a" type="button" class="ob-chip allergy on" :aria-pressed="true" @click="toggle(health.allergies, a)">{{ a }}<X :size="13" aria-hidden="true" /></button>
                </div>
                <div class="ob-add">
                  <input v-model="newAllergy" type="text" maxlength="60" class="ob-control" placeholder="Other allergy, e.g. Mango" @keydown.enter.prevent="addAllergy()" />
                  <button class="ob-btn-soft" type="button" :disabled="!newAllergy.trim()" @click="addAllergy()"><Plus :size="15" aria-hidden="true" />Add</button>
                </div>
              </template>
              <p v-if="healthErrors.allergies" class="field-error">{{ healthErrors.allergies }}</p>
            </fieldset>

            <fieldset class="ob-field">
              <legend>Dietary restrictions <span class="opt">Optional</span></legend>
              <div class="ob-chips">
                <button v-for="d in DIET_OPTIONS" :key="d" type="button" class="ob-chip" :class="{ on: health.diet.includes(d) }" :aria-pressed="health.diet.includes(d)" @click="toggle(health.diet, d)"><span class="ob-tick" aria-hidden="true"><Check :size="11" :stroke-width="3.4" /></span>{{ d }}</button>
                <button v-for="d in customDiet" :key="d" type="button" class="ob-chip on" :aria-pressed="true" @click="toggle(health.diet, d)">{{ d }}<X :size="13" aria-hidden="true" /></button>
              </div>
              <div class="ob-add">
                <input v-model="newDiet" type="text" maxlength="60" class="ob-control" placeholder="Other restriction, e.g. No spicy food" @keydown.enter.prevent="addDiet()" />
                <button class="ob-btn-soft" type="button" :disabled="!newDiet.trim()" @click="addDiet()"><Plus :size="15" aria-hidden="true" />Add</button>
              </div>
            </fieldset>

            <div class="ob-grid">
              <div class="ob-field">
                <label for="ob-religion">Religion <span class="opt">Optional</span></label>
                <select id="ob-religion" v-model="health.religion" class="ob-control">
                  <option value="">Prefer not to say</option>
                  <option v-for="r in RELIGION_OPTIONS" :key="r" :value="r">{{ r }}</option>
                </select>
                <p class="hint">Only so meal plans respect any food practices.</p>
              </div>
            </div>

            <fieldset class="ob-field">
              <legend>Your goals <span class="opt">Optional</span></legend>
              <div class="ob-chips">
                <button v-for="g in GOAL_OPTIONS" :key="g" type="button" class="ob-chip" :class="{ on: health.goals.includes(g) }" :aria-pressed="health.goals.includes(g)" @click="toggle(health.goals, g)"><span class="ob-tick" aria-hidden="true"><Check :size="11" :stroke-width="3.4" /></span>{{ g }}</button>
                <button v-for="g in customGoals" :key="g" type="button" class="ob-chip on" :aria-pressed="true" @click="toggle(health.goals, g)">{{ g }}<X :size="13" aria-hidden="true" /></button>
              </div>
              <div class="ob-add">
                <input v-model="newGoal" type="text" maxlength="60" class="ob-control" placeholder="Other goal, e.g. Improve energy" @keydown.enter.prevent="addGoal()" />
                <button class="ob-btn-soft" type="button" :disabled="!newGoal.trim()" @click="addGoal()"><Plus :size="15" aria-hidden="true" />Add</button>
              </div>
            </fieldset>

            <p v-if="saveError" class="form-error">{{ saveError }}</p>
            <div class="ob-actions">
              <button class="ob-btn-back" type="button" @click="go('about')"><ArrowLeft :size="16" aria-hidden="true" />Back</button>
              <button class="ob-btn" type="button" :disabled="isSaving" @click="saveHealth">
                <span v-if="isSaving" class="ob-spin light" aria-hidden="true"></span>{{ isSaving ? 'Saving…' : 'Continue' }}<ArrowRight v-if="!isSaving" :size="18" aria-hidden="true" />
              </button>
            </div>
          </section>

          <!-- 4. Screening -->
          <section v-else-if="step === 'screening'">
            <template v-if="screeningDone && !redoScreening">
              <div class="ob-done-icon" aria-hidden="true"><ClipboardCheck :size="28" /></div>
              <h1 class="nm-title">Your screening is on file</h1>
              <p class="ob-sub">Recorded {{ screeningDate }}. It's your starting point and can't be changed. New readings go in the Progress Tracker.</p>
              <label class="ob-confirm">
                <input v-model="infoConfirmed" type="checkbox" :disabled="isFinishing" />
                <span>I confirm that all the information I entered here is correct and complete to the best of my knowledge.</span>
              </label>
              <div class="ob-actions">
                <button class="ob-btn-back" type="button" @click="redoScreening = true">View it</button>
                <button class="ob-btn" type="button" :disabled="isFinishing || !infoConfirmed" @click="finish">
                  <span v-if="isFinishing" class="ob-spin light" aria-hidden="true"></span>{{ isFinishing ? 'Finishing…' : 'Finish setup' }}<Check v-if="!isFinishing" :size="18" aria-hidden="true" />
                </button>
              </div>
            </template>
            <template v-else>
              <div class="ob-screening">
                <PreConsultationScreening embedded :draft="screeningDraft" @keep-draft="keepScreeningDraft" @worked-out="answers => pendingScreening = answers" @changed="pendingScreening = null" />
              </div>
              <p v-if="pendingScreening" class="ob-note"><Info :size="16" aria-hidden="true" />Nothing is saved yet. Check your results, then finish setup. Your screening can't be changed after that.</p>
              <label v-if="screeningDone || pendingScreening" class="ob-confirm">
                <input v-model="infoConfirmed" type="checkbox" :disabled="isFinishing" />
                <span>I confirm that all the information I entered here is correct and complete to the best of my knowledge.</span>
              </label>
              <div v-if="screeningDone || pendingScreening" class="ob-actions">
                <button class="ob-btn-back" type="button" @click="go('health')"><ArrowLeft :size="16" aria-hidden="true" />Back</button>
                <button class="ob-btn" type="button" :disabled="isFinishing || !infoConfirmed" @click="finish">
                  <span v-if="isFinishing" class="ob-spin light" aria-hidden="true"></span>{{ isFinishing ? 'Finishing…' : 'Finish setup' }}<Check v-if="!isFinishing" :size="18" aria-hidden="true" />
                </button>
              </div>
              <div v-else class="ob-actions">
                <button class="ob-btn-back" type="button" @click="go('health')"><ArrowLeft :size="16" aria-hidden="true" />Back</button>
              </div>
            </template>
            <p v-if="finishError" class="form-error">{{ finishError }}</p>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>


<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ShieldCheck } from 'lucide-vue-next'
import { Activity, ArrowLeft, ArrowRight, CalendarCheck, Check, ClipboardCheck, Clock, Info, LogOut, Plus, UserRound, X } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'
import { phoneError } from '~/utils/phone'

const auth = useAuthStore()
const { get, patch, post } = useApi()

const STEPS = [
  { key: 'welcome', label: 'Welcome' },
  { key: 'about', label: 'About you' },
  { key: 'health', label: 'Your health' },
  { key: 'screening', label: 'Screening' },
]
const step = ref('welcome')
// Read-only in About you when sign-up already gave them (2026-11-09, user's call).
// Still asked if one is missing: the calorie calculation needs both.
const knownDob = ref(false)
const knownSex = ref(false)
const stepIndex = computed(() => STEPS.findIndex(s => s.key === step.value))
function go(key) {
  saveError.value = ''
  step.value = key
  window.scrollTo({ top: 0 })
}

// Same lists as sign-up / Profile Settings.
// same spelling as sign-up (RegisterFlow.vue); matched ignoring case so older
// "Renal Nutrition"-style values still land on their option
const CONDITION_OPTIONS = ['Hypertension', 'Type 2 Diabetes', 'Obesity management', 'Renal nutrition']
const conditionOption = v => CONDITION_OPTIONS.find(c => c.toLowerCase() === String(v || '').trim().toLowerCase())
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
// clear the allergy error as soon as it's answered (it used to stay until Continue)
watch(() => [health.hasAllergies, health.allergies.length], ([has, n]) => {
  if (has === false || (has && n)) healthErrors.allergies = ''
})
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
  aboutErrors.sex = about.sex ? '' : 'Choose one. It changes how your calories are calculated.'
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
    healthErrors.allergies = 'Please answer this. Your RND needs to know before planning meals.'
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

// What "Work out my results" calculated, saved only by Finish setup.
const pendingScreening = ref(null)
// Answers typed on the Screening step, kept while the client visits other steps.
const screeningDraft = ref(null)
function keepScreeningDraft(answers) {
  screeningDraft.value = answers
  pendingScreening.value = null // results are worked out again on return
}

const isFinishing = ref(false)
const finishError = ref('')
// The client states their answers are correct before setup can finish.
const infoConfirmed = ref(false)
async function finish() {
  if (!infoConfirmed.value) return
  isFinishing.value = true
  finishError.value = ''
  try {
    await post('/auth/me/onboarding/complete/', pendingScreening.value ? { screening: pendingScreening.value } : undefined)
    await auth.fetchMe()
    await navigateTo('/client-dashboard')  // the welcome pop-up opens there
  } catch (error) {
    finishError.value = firstError(error?.data, 'detail', 'height_cm', 'weight_kg', 'age', 'sex') || 'Could not finish setup. Please try again.'
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
    knownDob.value = !!about.dob
    knownSex.value = !!about.sex
    about.language = profile.language_code || ''
    about.phone = profile.user?.phone || ''
    const hp = profile.health_profile || {}
    const conditions = hp.medical_conditions || []
    otherConditions.value = conditions.slice(1)
    if (conditions[0]) {
      if (conditionOption(conditions[0])) health.condition = conditionOption(conditions[0])
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

/* ---------- UI only (no data or API changes) ---------- */
const plateImg = '/landing/login-plate.webp'
const platePins = [
  { tag: 'GO', label: 'Whole grains', share: '¼', x: '34%', y: '22%', side: 'to-right' },
  { tag: 'GROW', label: 'Protein', share: '¼', x: '63%', y: '35%', side: 'to-right' },
  { tag: 'GLOW', label: 'Vegetables', share: '½', x: '80%', y: '53%', side: 'to-left' },
]
const journey = [
  { icon: UserRound, title: 'Getting to know you', text: 'Your basic details and health background, including any food allergies.' },
  { icon: Activity, title: 'A quick health screening', text: 'Your height, weight and activity, to estimate your BMI and daily calorie needs.' },
  { icon: CalendarCheck, title: 'Find your RND and book', text: 'Choose a licensed Registered Nutritionist-Dietitian, pay before the session, then consult by video call or in person.' },
]
// the form side scrolls on its own on desktop: start each step at its top
const rightPane = ref(null)
watch(step, () => nextTick(() => {
  if (rightPane.value) rightPane.value.scrollTop = 0
}))
</script>

<style scoped>
/* =========================================================
   NutriMatch onboarding: brand #063C2A / #EFBF04 / white
   Fonts: Playfair Display (headings), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.nm-onb {
  font-family: 'DM Sans', Arial, sans-serif;
  color: #14261E;
  -webkit-font-smoothing: antialiased;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  min-height: 100vh;
  min-height: 100dvh;
  background: #FFFFFF;
}

/* ---------- LEFT: photo ---------- */
.nm-left {
  position: relative;
  overflow: hidden;
  background: #063C2A;
  color: #FFFFFF;
  min-height: 640px;
}
.nm-stage {
  position: absolute;
  top: 0;
  left: 50%;
  height: 100%;
  aspect-ratio: 1 / 1;
  min-width: 100%;
  transform: translateX(-50%);
}
.nm-stage-top { pointer-events: none; }
.nm-left-photo {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.nm-left-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg,
    rgba(4, 41, 29, 0.72) 0%,
    rgba(4, 41, 29, 0.18) 18%,
    rgba(4, 41, 29, 0) 30%,
    rgba(4, 41, 29, 0) 38%,
    rgba(4, 41, 29, 0.62) 52%,
    rgba(4, 41, 29, 0.92) 64%,
    rgba(4, 41, 29, 0.98) 100%);
}
.nm-left-vignette {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(4, 41, 29, 0.55) 0%, rgba(4, 41, 29, 0) 60%),
    radial-gradient(120% 90% at 50% 40%, rgba(0, 0, 0, 0) 55%, rgba(0, 0, 0, 0.28) 100%);
}
.nm-frame {
  position: absolute;
  inset: 16px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 4px;
  pointer-events: none;
}

/* Go / Grow / Glow labels */
.nm-pin { position: absolute; width: 0; height: 0; }
.nm-dot {
  position: absolute;
  left: -7px;
  top: -7px;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #EFBF04;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.95), 0 4px 10px rgba(0, 0, 0, 0.45);
}
.nm-dot::after {
  content: "";
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 2px solid rgba(239, 191, 4, 0.9);
  animation: nm-pulse 2.4s ease-out infinite;
}
.nm-pin:nth-child(2) .nm-dot::after { animation-delay: .8s; }
.nm-pin:nth-child(3) .nm-dot::after { animation-delay: 1.6s; }
@keyframes nm-pulse {
  0% { transform: scale(1); opacity: .9; }
  100% { transform: scale(2.8); opacity: 0; }
}
.nm-pin-line {
  position: absolute;
  top: 0;
  width: 40px;
  height: 1px;
  background: linear-gradient(90deg, rgba(239, 191, 4, 0.95), rgba(239, 191, 4, 0.55));
}
.nm-tag {
  position: absolute;
  top: 0;
  display: inline-flex;
  align-items: center;
  gap: 9px;
  white-space: nowrap;
  height: 36px;
  padding: 0 14px 0 6px;
  border-radius: 999px;
  background: rgba(4, 41, 29, 0.62);
  border: 1px solid rgba(239, 191, 4, 0.45);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  box-shadow: 0 10px 24px -12px rgba(0, 0, 0, 0.6);
  font-size: 13px;
  font-weight: 600;
  color: #FFFFFF;
  transform: translateY(-50%);
  animation: nm-tag-in .6s cubic-bezier(.2, .7, .2, 1) both;
}
.nm-pin.to-right .nm-pin-line { left: 7px; }
.nm-pin.to-right .nm-tag { left: 46px; --nm-from: 8px; }
.nm-pin.to-left .nm-pin-line { right: 7px; }
.nm-pin.to-left .nm-tag { right: 46px; --nm-from: -8px; }
.nm-pin:nth-child(1) .nm-tag { animation-delay: .3s; }
.nm-pin:nth-child(2) .nm-tag { animation-delay: .5s; }
.nm-pin:nth-child(3) .nm-tag { animation-delay: .7s; }
@keyframes nm-tag-in {
  from { opacity: 0; transform: translateY(-50%) translateX(var(--nm-from, 8px)); }
  to { opacity: 1; transform: translateY(-50%); }
}
.nm-tag-key {
  height: 24px;
  padding: 0 9px;
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  background: #EFBF04;
  color: #063C2A;
  font-size: 10.5px;
  font-weight: 800;
  letter-spacing: 1.4px;
}
.nm-tag-share {
  font-family: 'DM Sans', Arial, sans-serif;
  font-size: 15px;
  font-weight: 700;
  color: #EFBF04;
}

/* brand + welcome */
.nm-left-inner {
  position: relative;
  z-index: 1;
  height: 100%;
  box-sizing: border-box;
  padding: 28px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.nm-brand {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  align-self: flex-start;
}
.nm-brand-logo {
  width: 40px;
  height: 50px;
  object-fit: contain;
  filter: brightness(1.45) saturate(1.3) drop-shadow(0 2px 6px rgba(0, 0, 0, 0.6));
}
.nm-brand-text {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 28px;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: 0.2px;
  text-shadow: 0 2px 10px rgba(0, 0, 0, 0.55);
}
.nm-brand-text span { color: #F5C915; }
.nm-welcome {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 480px;
  margin: 0 0 130px 20px;
}
.nm-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 3px;
  color: #EFBF04;
}
.nm-eyebrow-line {
  width: 36px;
  height: 2px;
  border-radius: 2px;
  background: #EFBF04;
}
.nm-onb .nm-hero {
  display: block;
  margin: 0;
  padding: 0;
  background: none;
  border: none;
  box-shadow: none;
  font-family: 'Playfair Display', Georgia, serif;
  font-style: italic;
  font-size: clamp(34px, 3.6vw, 50px);
  line-height: 1.08;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #FFFFFF;
  text-shadow: 0 2px 18px rgba(0, 0, 0, 0.45);
}
.nm-hero em {
  display: inline;
  margin: 0;
  padding: 0;
  background: none;
  font-style: italic;
  color: #EFBF04;
}

/* the steps */
.nm-steps {
  position: relative;
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.55);
}
.nm-steps::before {
  content: "";
  position: absolute;
  left: 17px;
  top: 30px;
  bottom: 30px;
  width: 2px;
  background: linear-gradient(180deg, rgba(239, 191, 4, 0.8), rgba(255, 255, 255, 0.18));
}
.nm-step {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px 0;
}
.nm-step-dot {
  position: relative;
  z-index: 1;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 50%;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  text-shadow: none;
  background: rgba(4, 41, 29, 0.75);
  color: rgba(255, 255, 255, 0.85);
  border: 1.5px solid rgba(255, 255, 255, 0.35);
}
.nm-step.active .nm-step-dot {
  background: #EFBF04;
  color: #063C2A;
  border: none;
  box-shadow: 0 0 0 5px rgba(239, 191, 4, 0.22);
}
.nm-step.done .nm-step-dot {
  background: #FFFFFF;
  color: #063C2A;
  border: 2px solid #EFBF04;
}
.nm-step-text { display: flex; flex-direction: column; gap: 2px; }
.nm-step-kick {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.6);
}
.nm-step-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.78);
}
.nm-step.active .nm-step-kick,
.nm-step.done .nm-step-kick { color: #EFBF04; }
.nm-step.active .nm-step-title,
.nm-step.done .nm-step-title { color: #FFFFFF; }

/* ---------- RIGHT: form ---------- */
.nm-right {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 32px clamp(28px, 4.5vw, 64px) 28px;
  min-width: 0;
  background: #FFFFFF;
}
.nm-right > * { position: relative; z-index: 1; flex-shrink: 0; }
.nm-right > .nm-dots {
  position: absolute;
  z-index: 0;
  background-size: 14px 14px;
  pointer-events: none;
}
.nm-dots-top {
  top: 72px;
  right: 40px;
  width: 140px;
  height: 100px;
  background-image: radial-gradient(rgba(6, 60, 42, 0.22) 1.2px, transparent 1.4px);
}
.nm-dots-bottom {
  bottom: 70px;
  left: 36px;
  width: 120px;
  height: 90px;
  background-image: radial-gradient(rgba(196, 145, 2, 0.35) 1.2px, transparent 1.4px);
}
.nm-mobile-brand { display: none; }
.nm-right-top { min-height: 38px; }
.nm-back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 14px 0 10px;
  border: none;
  border-radius: 999px;
  background: #F1F6F2;
  color: #063C2A;
  text-decoration: none;
  font-family: inherit;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color .15s;
}
.nm-back:hover { background: #E5EFE8; }
.nm-back:disabled { opacity: .5; cursor: not-allowed; }

.nm-box-wrap {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 14px 0 40px;
}
.nm-box {
  width: 100%;
  max-width: 640px;
  transition: max-width .25s ease;
}
.nm-box.is-wide { max-width: 820px; }

/* progress + headings */
.nm-progress {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.nm-progress-text {
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1.4px;
  color: #C49102;
}
.nm-progress-bars { display: flex; gap: 6px; }
.nm-progress-bars span {
  width: 34px;
  height: 5px;
  border-radius: 99px;
  background: #E3EAE5;
}
.nm-progress-bars span.on { background: #063C2A; }
.nm-head {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 26px;
}
.nm-onb .nm-title {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 40px;
  line-height: 1.1;
  font-weight: 700;
  color: #10231B;
}

/* the plate panel heading is a <p> here (the form keeps the page's one <h1>) */
.nm-onb .nm-hero { margin: 0; }


/* left: subtitle under the heading */
.nm-welcome-sub {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.82);
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.5);
}

/* the steps, top of the form */
.ob-stepper { margin: 0 0 34px; padding: 18px 20px 16px; border-radius: 18px; background: #F3F7F4; }
.ob-stepper-top { margin: 0 0 14px; font-size: 12.5px; font-weight: 800; letter-spacing: 1.6px; color: #C49102; }
.ob-stepper ol { list-style: none; margin: 0; padding: 0; display: flex; }
.ob-stepper li { position: relative; flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center; }
.ob-stepper li:not(:first-child)::before {
  content: "";
  position: absolute;
  top: 17px;
  right: calc(50% + 22px);
  left: calc(-50% + 22px);
  height: 3px;
  border-radius: 3px;
  background: #DCE5DF;
}
.ob-stepper li.reached:not(:first-child)::before { background: #063C2A; }
.ob-sdot {
  position: relative;
  z-index: 1;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 800;
  background: #FFFFFF;
  color: #8A9A91;
  border: 2px solid #D3DCD6;
  transition: all .2s;
}
.ob-stepper li.done .ob-sdot { background: #EFBF04; color: #063C2A; border-color: #EFBF04; }
.ob-stepper li.active .ob-sdot { background: #063C2A; color: #FFFFFF; border-color: #063C2A; box-shadow: 0 0 0 5px rgba(6, 60, 42, 0.14); }
.ob-slab { font-size: 13px; font-weight: 700; line-height: 1.25; color: #8A9A91; }
.ob-stepper li.done .ob-slab { color: #3E5046; }
.ob-stepper li.active .ob-slab { color: #063C2A; }

/* ---------- form side: shared bits ---------- */
.nm-onb .nm-title em { font-style: italic; color: #C49102; background: none; padding: 0; }
.ob-sub,
.ob-lead { margin: 0; font-size: 15px; line-height: 1.6; color: #55665D; }
.ob-lead { margin-top: 14px; font-size: 15.5px; line-height: 1.65; color: #4A5A52; }
.muted { margin: 0; font-size: 14px; color: #7A8F84; }
.hint { margin: 0; font-size: 12.5px; line-height: 1.55; color: #6B7D73; }
.field-error { margin: 0; font-size: 12.5px; font-weight: 600; color: #B42318; }
.form-error {
  margin: 16px 0 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: #FEF3F2;
  border: 1px solid #FECDCA;
  color: #B42318;
  font-size: 13.5px;
  line-height: 1.5;
}
.ob-loading { display: flex; align-items: center; gap: 12px; padding: 24px 0; }

/* welcome */
.ob-time {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  height: 32px;
  padding: 0 12px;
  border-radius: 999px;
  background: #FBF6E4;
  border: 1px solid #F1E2A6;
  color: #6B5200;
  font-size: 13px;
  font-weight: 700;
}
.ob-journey { list-style: none; margin: 24px 0 0; padding: 0; display: flex; flex-direction: column; gap: 18px; }
.ob-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 4px 0;
}
.ob-item-icon {
  position: relative;
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: #EEF4F0;
  color: #063C2A;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.ob-item-num {
  position: absolute;
  top: -7px;
  right: -7px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #EFBF04;
  color: #063C2A;
  font-size: 11.5px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 3px #FFFFFF;
}
.ob-item-text { display: flex; flex-direction: column; gap: 4px; padding-top: 2px; }
.ob-item-text strong { font-size: 16px; color: #10231B; }
.ob-item-text span { font-size: 13.5px; line-height: 1.55; color: #5D7065; }
.ob-privacy {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  margin-top: 22px;
  padding: 16px 0 0;
  border-top: 1px solid #EEF2EF;
}
.ob-privacy p { margin: 0; font-size: 14px; line-height: 1.6; color: #1F3A2C; }
.ob-privacy-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #063C2A;
  color: #EFBF04;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* fields */
.ob-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 18px; align-items: start; }
.ob-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
  margin: 0 0 22px;
  padding: 0;
  border: none;
}
.ob-field > label,
.ob-field > legend { padding: 0; margin-bottom: 8px; font-size: 13px; font-weight: 600; color: #22362C; }
.ob-field > label { margin-bottom: 0; }
.req { margin-left: 6px; font-size: 11px; font-weight: 700; letter-spacing: .4px; color: #B42318; }
.opt { margin-left: 6px; font-size: 11.5px; font-weight: 600; color: #7A8F84; }
.ob-control {
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 16px;
  border-radius: 14px;
  border: 1.5px solid #DCE5DF;
  background: #F7FAF8;
  font-family: inherit;
  font-size: 15px;
  color: #14261E;
  outline: none;
  transition: border-color .15s, box-shadow .15s, background-color .15s;
}
select.ob-control {
  -webkit-appearance: none;
  appearance: none;
  padding-right: 44px;
  cursor: pointer;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%235D7065' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
}
.ob-control::placeholder { color: #9AA9A1; }
.ob-control:hover:not(:disabled) { border-color: #9FBCAC; }
.ob-control:focus { border-color: #063C2A; background-color: #FFFFFF; box-shadow: 0 0 0 4px rgba(6, 60, 42, 0.10); }
.ob-control:disabled { border-style: dashed; background-color: #F1F4F2; color: #4A5A52; cursor: not-allowed; opacity: 1; }
.ob-control.invalid { border-color: #D92D20; }
/* DateField / PhoneInput are shared components: only soften their edges */
.ob-wrap :deep(input),
.ob-wrap :deep(button),
.ob-wrap :deep(select) { font-family: inherit; }
.ob-wrap :deep(input) { min-height: 48px; border-radius: 12px; }
.ob-wrap.locked { opacity: .9; }

/* allergy radio cards */
.ob-radio-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.ob-radio {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 0 16px;
  border-radius: 14px;
  border: 1.5px solid #DCE5DF;
  background: #FFFFFF;
  font-size: 14.5px;
  font-weight: 600;
  color: #22362C;
  cursor: pointer;
  transition: border-color .15s, background-color .15s;
}
.ob-radio:hover { border-color: #9FBCAC; }
.ob-radio input { position: absolute; opacity: 0; pointer-events: none; }
.ob-radio-dot {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #B8C9BE;
  box-sizing: border-box;
  transition: all .15s;
}
.ob-radio.checked { border-color: #063C2A; background: #F1F6F2; color: #063C2A; }
.ob-radio.checked .ob-radio-dot { border: 6px solid #063C2A; }
.ob-radio:focus-within { box-shadow: 0 0 0 4px rgba(6, 60, 42, 0.10); }

/* chips */
.ob-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.ob-chips + .ob-add,
.ob-radio-row + .ob-chips { margin-top: 12px; }
.ob-chip {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 14px 0 10px;
  border-radius: 999px;
  border: 1.5px solid #DCE5DF;
  background: #FFFFFF;
  color: #3E5046;
  font-family: inherit;
  font-size: 13.5px;
  font-weight: 600;
  cursor: pointer;
  user-select: none;
  transition: background-color .15s, border-color .15s, color .15s;
}
.ob-chip:hover { border-color: #9FBCAC; }
.ob-tick {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1.5px solid #C9D6CE;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: transparent;
}
.ob-chip.on { background: #063C2A; border-color: #063C2A; color: #FFFFFF; }
.ob-chip.on .ob-tick { background: #EFBF04; border-color: #EFBF04; color: #063C2A; }
/* a ticked allergy is a real warning: red, never quiet */
.ob-chip.allergy.on { background: #B42318; border-color: #B42318; }
.ob-chip.allergy.on .ob-tick { background: #FFFFFF; border-color: #FFFFFF; color: #B42318; }
.ob-chip:not(:has(.ob-tick)) { padding-left: 14px; }
.ob-add { display: flex; gap: 8px; margin-top: 12px; }
.ob-add .ob-control { flex: 1; min-width: 0; height: 48px; font-size: 14.5px; }

/* buttons */
.ob-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 28px;
  padding-top: 22px;
  border-top: 1px solid #EEF2EF;
}
.ob-actions > :only-child { margin-right: auto; }
.ob-btn {
  height: 52px;
  padding: 0 26px;
  border: none;
  border-radius: 14px;
  background: #063C2A;
  color: #FFFFFF;
  font-family: inherit;
  font-size: 15.5px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  box-shadow: 0 12px 24px -14px rgba(6, 60, 42, 0.85);
  transition: background-color .15s, transform .15s;
}
.ob-btn:hover:not(:disabled) { background: #0A4F38; }
.ob-btn:active:not(:disabled) { transform: scale(.99); }
.ob-btn:disabled { opacity: .5; cursor: not-allowed; box-shadow: none; }
.ob-btn-block { width: 100%; height: 58px; margin-top: 26px; font-size: 16px; }
.ob-btn-back,
.ob-btn-soft {
  border: none;
  background: #F1F6F2;
  color: #063C2A;
  font-family: inherit;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background-color .15s;
}
.ob-btn-back { height: 46px; padding: 0 18px 0 14px; border-radius: 999px; font-size: 14px; }
.ob-btn-soft { flex-shrink: 0; height: 48px; padding: 0 16px; border-radius: 14px; font-size: 14px; }
.ob-btn-back:hover,
.ob-btn-soft:hover:not(:disabled) { background: #E5EFE8; }
.ob-btn-soft:disabled { opacity: .5; cursor: not-allowed; }
.ob-spin {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2.5px solid #DCE5DF;
  border-top-color: #063C2A;
  animation: ob-spin .8s linear infinite;
}
.ob-spin.light { width: 18px; height: 18px; border-color: rgba(255, 255, 255, 0.35); border-top-color: #FFFFFF; }
@keyframes ob-spin { to { transform: rotate(360deg); } }

/* screening step */
.ob-done-icon {
  width: 56px;
  height: 56px;
  margin-bottom: 16px;
  border-radius: 18px;
  background: #EEF4F0;
  color: #063C2A;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 1.5px #D3E5DA;
}
.ob-done-icon + .nm-title { margin-bottom: 10px; }
.ob-note {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  margin: 18px 0 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: #FBF6E4;
  border: 1px solid #F1E2A6;
  color: #6B5200;
  font-size: 13.5px;
  line-height: 1.5;
}
.ob-note svg { flex-shrink: 0; margin-top: 1px; }
.ob-confirm {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin: 18px 0 0;
  padding: 14px 16px;
  border-radius: 14px;
  border: 1.5px solid #DCE5DF;
  background: #F7FAF8;
  font-size: 14px;
  line-height: 1.55;
  color: #1F3A2C;
  cursor: pointer;
  transition: border-color .15s, background-color .15s;
}
.ob-confirm:hover { border-color: #9FBCAC; }
.ob-confirm:has(input:checked) { border-color: #063C2A; background: #F1F6F2; }
.ob-confirm input { margin-top: 2px; width: 18px; height: 18px; accent-color: #063C2A; flex-shrink: 0; cursor: pointer; }

.nm-onb button:focus-visible,
.nm-onb input[type="checkbox"]:focus-visible { outline: 3px solid #EFBF04; outline-offset: 2px; }

/* ---------- desktop: the photo stays put, only the form side scrolls ---------- */
@media (min-width: 961px) {
  .nm-onb { height: 100vh; height: 100dvh; min-height: 0; overflow: hidden; }
  .nm-left { height: 100vh; height: 100dvh; }
  .nm-right {
    height: 100vh;
    height: 100dvh;
    overflow-x: hidden;
    overflow-y: auto;
    overscroll-behavior: contain;
  }
}

/* ---------- tablet + phone: only the form ---------- */
@media (max-width: 960px) {
  .nm-onb { grid-template-columns: 1fr; }
  .nm-left { display: none; }
  .nm-right > .nm-dots { display: none; }
  .nm-right { min-height: 100vh; min-height: 100dvh; padding: 24px; }
  .nm-mobile-brand {
    order: 1;
    display: inline-flex;
    align-items: center;
    align-self: center;
    gap: 10px;
    margin-top: 12px;
  }
  .nm-mobile-logo {
    width: 38px;
    height: 46px;
    object-fit: contain;
    filter: drop-shadow(0 4px 8px rgba(6, 60, 42, 0.18));
  }
  .nm-mobile-text {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 28px;
    font-weight: 700;
    color: #063C2A;
  }
  .nm-mobile-text span { color: #C49102; }
  .nm-right-top { order: 2; margin-top: 28px; }
  .nm-box-wrap { order: 3; align-items: flex-start; padding: 20px 0 32px; }
}

@media (max-width: 640px) {
  .nm-right { padding: 16px 16px 20px; }
  .nm-mobile-brand { margin-top: 8px; }
  .nm-mobile-text { font-size: 26px; }
  .nm-box-wrap { padding: 16px 0 24px; }
  .nm-onb .nm-title { font-size: 30px; }
  .ob-grid,
  .ob-radio-row { grid-template-columns: minmax(0, 1fr); }
  .ob-control,
  .ob-add .ob-control { font-size: 16px; } /* stops iPhone zoom on tap */
  .ob-item { gap: 14px; }
  .ob-item-icon { width: 42px; height: 42px; border-radius: 12px; }
  .ob-actions { flex-direction: column-reverse; align-items: stretch; }
  .ob-actions > * { width: 100%; justify-content: center; }
  .ob-stepper { margin-bottom: 26px; padding: 14px 12px 12px; border-radius: 16px; }
  .ob-slab { font-size: 11.5px; }
  .ob-sdot { width: 32px; height: 32px; font-size: 13px; }
  .ob-stepper li:not(:first-child)::before { top: 15px; right: calc(50% + 20px); left: calc(-50% + 20px); }
}

@media (prefers-reduced-motion: reduce) {
  .nm-dot::after { animation: none; opacity: 0; }
  .nm-tag { animation: none; }
  .ob-spin { animation: none; }
  .ob-item:hover { transform: none; }
}
</style>