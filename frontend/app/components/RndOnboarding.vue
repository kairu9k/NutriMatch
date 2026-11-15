<template>
  <!-- RND onboarding (2026-11-16, panel feedback): sign-up only asks what approval
       needs; after an admin approves, the RND sets up their profile, consultation
       fee and formats, weekly hours and payout here. The route guard sends an
       approved RND who hasn't finished to this page. Nothing is saved until
       Finish setup: one request saves it all (POST /auth/me/onboarding/complete/). -->
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

      <!-- 1. Welcome -->
      <section v-else-if="step === 'welcome'" class="card">
        <h1 class="title">You're approved{{ firstName ? `, ${firstName}` : '' }}</h1>
        <p class="lead">Our team checked your PRC license. A few more things and clients can find and book you.</p>
        <ol class="journey">
          <li><span class="j-num">1</span><div><strong>Your profile</strong><p>A photo, a short bio and the languages you consult in.</p></div></li>
          <li><span class="j-num">2</span><div><strong>Your consultations</strong><p>Your fee and how you consult.</p></div></li>
          <li><span class="j-num">3</span><div><strong>Your weekly hours</strong><p>When clients can book you.</p></div></li>
          <li><span class="j-num">4</span><div><strong>Your payout details</strong><p>Where we send your earnings. You can add this later.</p></div></li>
        </ol>
        <div class="actions"><button class="nm-btn-dark" type="button" @click="go('profile')">Get started</button></div>
      </section>

      <!-- 2. Your profile -->
      <section v-else-if="step === 'profile'" class="card">
        <h1 class="title">Your profile</h1>
        <p class="lead">What clients see before they book you.</p>

        <div class="field">
          <label>Profile photo <span class="optional-tag">Optional</span></label>
          <div class="photo-row">
            <img v-if="photoPreview" :src="photoPreview" alt="Profile photo preview" class="photo-preview" />
            <div v-else class="photo-placeholder">{{ initials }}</div>
            <div class="photo-actions">
              <label class="nm-btn-soft nm-btn-sm photo-btn">
                <input type="file" accept="image/jpeg,image/png,image/webp" class="file-input" @change="onPhotoSelected" />
                {{ photo ? 'Change photo' : 'Upload photo' }}
              </label>
              <button v-if="photo" type="button" class="nm-btn-danger solid nm-btn-sm" @click="removePhoto">Remove</button>
              <span class="hint">A clear, friendly headshot. JPG, PNG or WEBP, up to 2 MB.</span>
            </div>
          </div>
        </div>

        <div class="field">
          <label for="onb-bio">Bio <span class="optional-tag">Optional</span></label>
          <textarea id="onb-bio" v-model="profile.bio" data-allow-emoji rows="5" maxlength="1000" class="bio-input" :class="{ invalid: bioError }"
            placeholder="e.g. Registered Nutritionist-Dietitian with 6 years of hospital experience, helping adults manage diabetes and lose weight through practical Filipino meals."></textarea>
          <div class="bio-meta">
            <span v-if="bioError" class="field-error">{{ bioError }}</span>
            <span v-else class="hint">You can add it later in Profile Settings. It helps clients choose you. If you write one now, at least 50 characters.</span>
            <span class="char-count">{{ profile.bio.trim().length }}/1000</span>
          </div>
        </div>

        <div class="field">
          <label id="onb-lang">Languages you consult in <span class="required-tag">Required</span></label>
          <div class="chip-grid" role="group" aria-labelledby="onb-lang">
            <label v-for="lang in LANGUAGES" :key="lang.code" class="choice-chip" :class="{ checked: profile.languages.includes(lang.code) }">
              <input v-model="profile.languages" type="checkbox" :value="lang.code" />
              {{ lang.name }}
            </label>
          </div>
          <span v-if="errors.languages" class="field-error">{{ errors.languages }}</span>
        </div>

        <div class="actions">
          <button class="nm-btn-soft" type="button" @click="go('welcome')">Back</button>
          <button class="nm-btn-dark" type="button" @click="next('profile', 'consult')">Continue</button>
        </div>
      </section>

      <!-- 3. Consultations -->
      <section v-else-if="step === 'consult'" class="card">
        <h1 class="title">Your consultations</h1>
        <p class="lead">Your fee and how you consult.</p>

        <div class="field">
          <label for="onb-fee">Consultation fee <span class="required-tag">Required</span></label>
          <div class="fee-wrap">
            <span class="fee-prefix">₱</span>
            <input id="onb-fee" v-model.number="profile.fee" type="number" inputmode="numeric" min="100" step="50" placeholder="e.g. 800" :class="{ invalid: feeError || errors.consultation_fee }" />
            <span class="fee-suffix">per session</span>
          </div>
          <span v-if="feeError || errors.consultation_fee" class="field-error">{{ feeError || errors.consultation_fee }}</span>
          <span v-else class="hint">At least ₱100. Clients pay this before each consultation.</span>
        </div>

        <div class="field">
          <label id="onb-modes">Consultation formats <span class="required-tag">Required</span></label>
          <div class="chip-grid" role="group" aria-labelledby="onb-modes">
            <label v-for="(label, key) in MODE_LABELS" :key="key" class="choice-chip" :class="{ checked: profile.modes.includes(key) }">
              <input v-model="profile.modes" type="checkbox" :value="key" />
              {{ label }}
            </label>
          </div>
          <span v-if="errors.consultation_modes" class="field-error">{{ errors.consultation_modes }}</span>
        </div>

        <div v-if="profile.modes.includes('in_person')" class="field">
          <label for="onb-clinic">Clinic address <span class="required-tag">Required</span></label>
          <input id="onb-clinic" v-model="profile.clinicAddress" type="text" maxlength="255" :class="{ invalid: addressError || errors.clinic_address }"
            placeholder="e.g. 2F Bajada Medical Bldg, J.P. Laurel Ave, Bajada, Davao City" />
          <span v-if="addressError || errors.clinic_address" class="field-error">{{ addressError || errors.clinic_address }}</span>
          <span v-else class="hint">Where clients go for in-person consultations. It's shown on your profile.</span>
        </div>

        <div class="actions">
          <button class="nm-btn-soft" type="button" @click="go('profile')">Back</button>
          <button class="nm-btn-dark" type="button" @click="next('consult', 'hours')">Continue</button>
        </div>
      </section>

      <!-- 4. Weekly hours -->
      <section v-else-if="step === 'hours'" class="card">
        <h1 class="title">Your weekly hours</h1>
        <p class="lead">When clients can book you. You can change these any time in Profile Settings, and block days off.</p>
        <div class="hours-tools">
          <button class="nm-btn-soft nm-btn-sm" type="button" @click="availabilityRef?.openWeekForm()">Add hours for all week</button>
        </div>
        <Availability ref="availabilityRef" embedded hide-time-off />
        <span v-if="errors.availability" class="field-error hours-error">{{ errors.availability }}</span>
        <div class="actions">
          <button class="nm-btn-soft" type="button" @click="go('consult')">Back</button>
          <button class="nm-btn-dark" type="button" @click="next('hours', 'payout')">Continue</button>
        </div>
      </section>

      <!-- 5. Payout -->
      <section v-else-if="step === 'payout'" class="card">
        <h1 class="title">Your payout details</h1>
        <p class="lead">Where NutriMatch sends your earnings on the 5th of each month. Only NutriMatch admins can see these. You can add this later in Earnings, but we can't pay you until it's there.</p>
        <PayoutDetailsFields ref="payoutFields" :account="existingPayout" />
        <label class="confirm-item">
          <input v-model="infoConfirmed" type="checkbox" :disabled="isFinishing" />
          <span>I confirm that all the information I entered here is correct and complete to the best of my knowledge.</span>
        </label>
        <div class="actions">
          <button class="nm-btn-soft" type="button" :disabled="isFinishing" @click="go('hours')">Back</button>
          <button class="nm-btn-dark" type="button" :disabled="isFinishing || !infoConfirmed" @click="finish">{{ isFinishing ? 'Finishing…' : 'Finish setup' }}</button>
        </div>
        <p class="hint skip-note">Leave the payout details empty to add them later.</p>
        <p v-if="finishError" class="form-error">{{ finishError }}</p>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useToast } from '~/composables/useToast'
import { addressProblem, bioProblem, feeProblem, LANGUAGES, MODE_LABELS } from '~/utils/rndSetup'

const auth = useAuthStore()
const { get, post } = useApi()
const toast = useToast()

const STEPS = [
  { key: 'welcome', label: 'Welcome' },
  { key: 'profile', label: 'Your profile' },
  { key: 'consult', label: 'Consultations' },
  { key: 'hours', label: 'Weekly hours' },
  { key: 'payout', label: 'Payout' },
]
const step = ref('welcome')
const stepIndex = computed(() => STEPS.findIndex(s => s.key === step.value))
const isLoading = ref(true)
const loadError = ref('')
const firstName = computed(() => auth.user?.first_name || '')
const initials = computed(() => `${auth.user?.first_name?.[0] || ''}${auth.user?.last_name?.[0] || ''}`)

// The profile answers are kept here until Finish setup (the weekly hours are saved as they're added). Whatever the
// application already held (an applicant from before this change) is filled in.
const profile = reactive({ bio: '', languages: [], fee: '', modes: ['video'], clinicAddress: '' })
const availabilityRef = ref(null) // the same weekly hours editor as Profile Settings; it saves each change as it's made
const existingPayout = ref(null)
const payoutFields = ref(null)
const errors = reactive({})
const infoConfirmed = ref(false)

const bioError = computed(() => bioProblem(profile.bio))
const feeError = computed(() => feeProblem(profile.fee))
const addressError = computed(() => (profile.clinicAddress.trim() ? addressProblem(profile.modes, profile.clinicAddress) : ''))

// photo: optional, sent after the setup is saved
const MAX_PHOTO_BYTES = 2 * 1024 * 1024
const photo = ref(null)
const photoPreview = ref('')
function onPhotoSelected(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    toast.problem('Use a JPG, PNG, or WEBP image for your profile photo.', { id: 'rnd-onb-photo' })
    return
  }
  if (file.size > MAX_PHOTO_BYTES) {
    toast.problem('The profile photo must be 2 MB or smaller.', { id: 'rnd-onb-photo' })
    return
  }
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photo.value = file
  photoPreview.value = URL.createObjectURL(file)
}
function removePhoto() {
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photo.value = null
  photoPreview.value = ''
}
onBeforeUnmount(() => { if (photoPreview.value) URL.revokeObjectURL(photoPreview.value) })

// a field's error goes away once the answer changes
watch(profile, () => { for (const k of Object.keys(errors)) delete errors[k] }, { deep: true })

function go(key) {
  for (const k of Object.keys(errors)) delete errors[k]
  step.value = key
  nextTick(() => window.scrollTo({ top: 0 }))
}

// What each step needs before Continue (the same rules the API applies at Finish).
function stepProblem(key) {
  if (key === 'profile') {
    if (!profile.languages.length) return { languages: 'Choose at least one language.' }
    if (bioError.value) return { bio: bioError.value }
  }
  if (key === 'consult') {
    if (profile.fee === '' || profile.fee === null) return { consultation_fee: 'Set your consultation fee.' }
    if (feeError.value) return { consultation_fee: feeError.value }
    if (!profile.modes.length) return { consultation_modes: 'Offer at least one consultation format.' }
    const address = addressProblem(profile.modes, profile.clinicAddress)
    if (address) return { clinic_address: address }
  }
  if (key === 'hours' && !availabilityRef.value?.hasHours) return { availability: 'Add at least one block of weekly hours. Clients can only book inside them.' }
  return null
}
function next(from, to) {
  const problem = stepProblem(from)
  for (const k of Object.keys(errors)) delete errors[k]
  if (problem) {
    Object.assign(errors, problem)
    toast.problem('Please check the highlighted field.', { id: 'rnd-onb' })
    return
  }
  go(to)
}

const isFinishing = ref(false)
const finishError = ref('')
// which step shows each error the API can return
const FIELD_STEP = { languages: 'profile', bio: 'profile', consultation_fee: 'consult', consultation_modes: 'consult', clinic_address: 'consult', availability: 'hours' }
const first = v => (Array.isArray(v) ? v[0] : v)

async function finish() {
  if (!infoConfirmed.value) return
  finishError.value = ''
  // payout is optional: empty means "add later"; typed, it has to be right
  const fields = payoutFields.value
  const withPayout = fields && !fields.isEmpty()
  if (withPayout && !fields.validate()) return
  isFinishing.value = true
  try {
    await post('/auth/me/onboarding/complete/', {
      profile: {
        bio: profile.bio.trim(),
        languages: profile.languages,
        consultation_fee: Number(profile.fee).toFixed(2),
        consultation_modes: profile.modes,
        clinic_address: profile.modes.includes('in_person') ? profile.clinicAddress.trim() : '',
      },
      ...(withPayout ? { payout: fields.payload() } : {}),
    })
    if (photo.value) {
      // the setup is saved; a photo that fails can be added in Profile Settings
      try {
        const body = new FormData()
        body.append('photo', photo.value)
        await post('/auth/me/photo/', body)
      } catch {
        toast.problem('Your setup is saved, but the photo did not upload. Add it in Profile Settings.', { id: 'rnd-onb-photo' })
      }
    }
    await auth.fetchMe()
    await navigateTo('/rnd-dashboard') // the welcome pop-up opens there
  } catch (error) {
    const data = error?.data || {}
    if (data.payout) {
      fields?.setErrors(data.payout)
      finishError.value = 'Check your payout details, or leave them empty to add later.'
    } else {
      const key = Object.keys(FIELD_STEP).find(k => data[k])
      if (key) {
        Object.assign(errors, { [key]: first(data[key]) })
        step.value = FIELD_STEP[key]
        toast.problem(first(data[key]), { id: 'rnd-onb' })
      } else {
        finishError.value = data.detail || 'Could not finish setup. Please try again.'
      }
    }
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
    const [status, mine, payout] = await Promise.all([
      get('/auth/me/onboarding/'),
      get('/rnd/profile/'),
      get('/rnd/payout-account/').catch(() => null),
    ])
    if (status.complete) {
      await auth.fetchMe()
      return navigateTo('/rnd-dashboard')
    }
    profile.bio = mine.bio || ''
    profile.languages = (mine.languages || []).map(l => l.language_code).filter(Boolean)
    profile.fee = Number(mine.consultation_fee) >= 100 ? Number(mine.consultation_fee) : ''
    profile.modes = mine.consultation_modes?.length ? [...mine.consultation_modes] : ['video']
    profile.clinicAddress = mine.clinic_address || ''
    existingPayout.value = payout && payout.method ? payout : null
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
.onb-steps { list-style: none; padding: 0; margin: 0 0 20px; display: flex; gap: 12px; }
.onb-step { flex: 1; display: flex; align-items: center; gap: 8px; font-size: 0.88rem; color: #8a9a8a; font-weight: 600; min-width: 0; }
.onb-dot { width: 26px; height: 26px; border-radius: 50%; border: 2px solid #d5dad5; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; flex-shrink: 0; background: #fff; }
.onb-step.active { color: #1a3a1a; }
.onb-step.active .onb-dot { border-color: #1a3a1a; background: #1a3a1a; color: #fff; }
.onb-step.done .onb-dot { border-color: #D4A017; background: #D4A017; color: #1a3a1a; }
.onb-step-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.card { background: #fff; border: 1px solid #d9e3dc; border-radius: 16px; padding: 28px; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.title { font-family: 'Playfair Display', serif; font-size: 1.8rem; margin: 0 0 8px; line-height: 1.25; }
.lead { font-size: 1rem; color: #4a5a4a; margin: 0 0 22px; line-height: 1.55; }
.muted { color: #8a9a8a; font-size: 0.88rem; margin: 0; }
.hint { font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; }
.skip-note { margin: 12px 0 0; }

.journey { list-style: none; padding: 0; margin: 0 0 20px; display: flex; flex-direction: column; gap: 14px; }
.journey li { display: flex; gap: 14px; align-items: flex-start; }
.journey strong { font-size: 1.05rem; }
.journey p { margin: 3px 0 0; font-size: 0.84rem; color: #6a7a6a; line-height: 1.5; }
.j-num { width: 30px; height: 30px; border-radius: 50%; background: #eef3ec; color: #1e4a26; font-weight: 700; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }

.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 20px; }
.field > label { font-size: 0.85rem; font-weight: 600; color: #1a3a1a; }
.field input[type='text'], .field input[type='number'], .bio-input { width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 13px; font-size: 0.9rem; font-family: inherit; color: #1a3a1a; background: #fff; }
.field input:focus, .bio-input:focus { outline: none; border-color: #1a3a1a; }
.field .invalid { border-color: #c0392b; }
.bio-input { resize: vertical; min-height: 110px; line-height: 1.5; }
.bio-meta { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.char-count { font-size: 0.76rem; color: #6a7a6a; white-space: nowrap; font-variant-numeric: tabular-nums; }
.required-tag { color: #a12525; font-size: 0.74rem; font-weight: 600; margin-left: 4px; }
.optional-tag { color: #6a7a6a; font-size: 0.74rem; font-weight: 600; margin-left: 4px; }
.field-error { font-size: 0.78rem; color: #c0392b; }
.hours-error { display: block; margin-top: 10px; }
.hours-tools { display: flex; justify-content: flex-end; margin: -6px 0 12px; }
.form-error { background: #fdecec; border: 1px solid #f3b8b8; color: #a12525; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 12px 0 0; }

.photo-row { display: flex; align-items: center; gap: 14px; }
.photo-preview, .photo-placeholder { width: 64px; height: 64px; border-radius: 50%; flex-shrink: 0; }
.photo-preview { object-fit: cover; }
.photo-placeholder { background: #0a4a37; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; }
.photo-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.photo-actions .hint { flex-basis: 100%; }
.photo-btn { cursor: pointer; }
.file-input { display: none; }

.chip-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.choice-chip { display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 0 13px; border: 1.5px solid #d9e3dc; border-radius: 999px; background: #fff; color: #4a5a4a; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
.choice-chip input { width: 16px; height: 16px; flex-shrink: 0; accent-color: #0a4a37; margin: 0; }
.choice-chip.checked { border-color: #0a4a37; background: #e3efe7; color: #0a4a37; }

.fee-wrap { display: flex; align-items: center; gap: 8px; max-width: 320px; }
.fee-wrap input { flex: 1; min-width: 0; }
.fee-prefix, .fee-suffix { font-size: 0.88rem; color: #4a5a4a; white-space: nowrap; }

.confirm-item { display: flex; align-items: flex-start; gap: 10px; margin: 20px 0 0; font-size: 0.86rem; color: #1a3a1a; line-height: 1.5; cursor: pointer; }
.confirm-item input { margin-top: 3px; width: 16px; height: 16px; accent-color: #0a4a37; flex-shrink: 0; cursor: pointer; }

.actions { display: flex; justify-content: space-between; gap: 10px; margin-top: 22px; }
.actions > :only-child { margin-left: auto; }

@media (max-width: 640px) {
  .card { padding: 20px; }
  .onb-step-label { display: none; }
  .onb-step.active .onb-step-label { display: inline; }
  .title { font-size: 1.5rem; }
  .actions { flex-direction: column-reverse; }
  .actions > * { width: 100%; }
}
</style>
