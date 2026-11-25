<template>
  <!-- RND onboarding (2026-11-16, panel feedback): sign-up only asks what approval
       needs; after an admin approves, the RND sets up their profile, consultation
       fee and formats, weekly hours and payout here. The route guard sends an
       approved RND who hasn't finished to this page. Nothing is saved until
       Finish setup: one request saves it all (POST /auth/me/onboarding/complete/).
       Layout: same as the client onboarding (plate photo left, steps + form right). -->
  <div class="nm-onb">
    <!-- LEFT: plate photo (desktop only, stays put) -->
    <aside class="nm-left">
      <div class="nm-stage">
        <img class="nm-left-photo" :src="plateImg" alt="A balanced plate: half vegetables, a quarter whole grains and a quarter protein" />
      </div>
      <div class="nm-left-shade" aria-hidden="true"></div>
      <div class="nm-left-vignette" aria-hidden="true"></div>
      <div class="nm-frame" aria-hidden="true"></div>
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
          <span class="nm-eyebrow"><span class="nm-eyebrow-line" aria-hidden="true"></span>WELCOME, RND</span>
          <p class="nm-hero">Let's set up your <em>practice.</em></p>
          <p class="nm-welcome-sub">A few details so clients can find you, see your fee and book a time that works for you.</p>
        </div>
      </div>
    </aside>

    <!-- RIGHT: the form -->
    <main ref="rightPane" class="nm-right">
      <div class="nm-mobile-brand">
        <img src="/resources/nutrimatchlogo.png" alt="" class="nm-mobile-logo" />
        <span class="nm-mobile-text">Nutri<span>Match</span></span>
      </div>

      <div class="nm-right-top">
        <button class="nm-back" type="button" @click="signOut"><LogOut :size="15" aria-hidden="true" />Sign out</button>
      </div>

      <div class="nm-box-wrap">
        <div class="nm-box" :class="{ 'is-wide': step === 'hours' || step === 'payout' }">
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
            <h1 class="nm-title">You're approved{{ firstName ? `, ${firstName}` : '' }}. <em>Welcome!</em></h1>
            <p class="ob-lead">Our team checked your PRC license. A few more things and clients can find and book you.</p>
            <span class="ob-time"><Clock :size="15" aria-hidden="true" />Takes about 5 minutes</span>
            <ol class="ob-journey">
              <li v-for="(j, i) in rndJourney" :key="j.title" class="ob-item">
                <span class="ob-item-icon" aria-hidden="true"><component :is="j.icon" :size="22" :stroke-width="1.9" /><span class="ob-item-num">{{ i + 1 }}</span></span>
                <span class="ob-item-text"><strong>{{ j.title }}</strong><span>{{ j.text }}</span></span>
              </li>
            </ol>
            <div class="ob-privacy">
              <span class="ob-privacy-icon" aria-hidden="true"><ShieldCheck :size="15" /></span>
              <p>Nothing is shown to clients until you finish. You can change all of this later in Profile Settings.</p>
            </div>
            <button class="ob-btn ob-btn-block" type="button" @click="go('profile')">Let's get started<ArrowRight :size="18" aria-hidden="true" /></button>
          </section>

          <!-- 2. Your profile -->
          <section v-else-if="step === 'profile'">
            <div class="nm-head">
              <h1 class="nm-title">Your profile</h1>
              <p class="ob-sub">What clients see before they book you.</p>
            </div>

            <div class="ob-field">
              <label>Profile photo <span class="opt">Optional</span></label>
              <div class="photo-row">
                <img v-if="photoPreview" :src="photoPreview" alt="Profile photo preview" class="photo-preview" />
                <div v-else class="photo-placeholder">{{ initials }}</div>
                <div class="photo-actions">
                  <label class="ob-btn-back photo-btn">
                    <input type="file" accept="image/jpeg,image/png,image/webp" class="file-input" @change="onPhotoSelected" />
                    <Camera :size="15" aria-hidden="true" />{{ photo ? 'Change photo' : 'Upload photo' }}
                  </label>
                  <button v-if="photo" type="button" class="ob-btn-back photo-remove" @click="removePhoto">Remove</button>
                  <span class="hint">A clear, friendly headshot. JPG, PNG or WEBP, up to 2 MB.</span>
                </div>
              </div>
            </div>

            <div class="ob-field">
              <label for="onb-bio">Bio <span class="opt">Optional</span></label>
              <textarea id="onb-bio" v-model="profile.bio" data-allow-emoji rows="5" maxlength="1000" class="ob-control bio-input" :class="{ invalid: bioError }"
                placeholder="e.g. Registered Nutritionist-Dietitian with 6 years of hospital experience, helping adults manage diabetes and lose weight through practical Filipino meals."></textarea>
              <div class="bio-meta">
                <span v-if="bioError" class="field-error">{{ bioError }}</span>
                <span v-else class="hint">You can add it later in Profile Settings. It helps clients choose you. If you write one now, at least 50 characters.</span>
                <span class="char-count">{{ profile.bio.trim().length }}/1000</span>
              </div>
            </div>

            <div class="ob-field">
              <label id="onb-lang">Languages you consult in <span class="req">Required</span></label>
              <div class="ob-chips" role="group" aria-labelledby="onb-lang">
                <label v-for="lang in LANGUAGES" :key="lang.code" class="ob-chip choice" :class="{ on: profile.languages.includes(lang.code) }">
                  <input v-model="profile.languages" type="checkbox" :value="lang.code" />
                  <span class="ob-tick" aria-hidden="true"><Check :size="12" :stroke-width="3" /></span>{{ lang.name }}
                </label>
              </div>
              <span v-if="errors.languages" class="field-error">{{ errors.languages }}</span>
            </div>

            <div class="ob-actions">
              <button class="ob-btn-back" type="button" @click="go('welcome')"><ArrowLeft :size="16" aria-hidden="true" />Back</button>
              <button class="ob-btn" type="button" @click="next('profile', 'consult')">Continue<ArrowRight :size="18" aria-hidden="true" /></button>
            </div>
          </section>

          <!-- 3. Consultations -->
          <section v-else-if="step === 'consult'">
            <div class="nm-head">
              <h1 class="nm-title">Your consultations</h1>
              <p class="ob-sub">Your fee and how you consult.</p>
            </div>

            <div class="ob-field">
              <label for="onb-fee">Consultation fee <span class="req">Required</span></label>
              <div class="fee-wrap">
                <span class="fee-prefix">₱</span>
                <input id="onb-fee" v-model.number="profile.fee" type="number" inputmode="numeric" min="100" step="50" placeholder="e.g. 800" class="ob-control" :class="{ invalid: feeError || errors.consultation_fee }" />
                <span class="fee-suffix">per session</span>
              </div>
              <span v-if="feeError || errors.consultation_fee" class="field-error">{{ feeError || errors.consultation_fee }}</span>
              <span v-else class="hint">At least ₱100. Clients pay this before each consultation.</span>
            </div>

            <div class="ob-field">
              <label id="onb-modes">Consultation formats <span class="req">Required</span></label>
              <div class="ob-chips" role="group" aria-labelledby="onb-modes">
                <label v-for="(label, key) in MODE_LABELS" :key="key" class="ob-chip choice" :class="{ on: profile.modes.includes(key) }">
                  <input v-model="profile.modes" type="checkbox" :value="key" />
                  <span class="ob-tick" aria-hidden="true"><Check :size="12" :stroke-width="3" /></span>{{ label }}
                </label>
              </div>
              <span v-if="errors.consultation_modes" class="field-error">{{ errors.consultation_modes }}</span>
            </div>

            <div v-if="profile.modes.includes('in_person')" class="ob-field">
              <label for="onb-clinic">Clinic address <span class="req">Required</span></label>
              <input id="onb-clinic" v-model="profile.clinicAddress" type="text" maxlength="255" class="ob-control" :class="{ invalid: addressError || errors.clinic_address }"
                placeholder="e.g. 2F Bajada Medical Bldg, J.P. Laurel Ave, Bajada, Davao City" />
              <span v-if="addressError || errors.clinic_address" class="field-error">{{ addressError || errors.clinic_address }}</span>
              <span v-else class="hint">Where clients go for in-person consultations. It's shown on your profile.</span>
            </div>

            <div class="ob-actions">
              <button class="ob-btn-back" type="button" @click="go('profile')"><ArrowLeft :size="16" aria-hidden="true" />Back</button>
              <button class="ob-btn" type="button" @click="next('consult', 'hours')">Continue<ArrowRight :size="18" aria-hidden="true" /></button>
            </div>
          </section>

          <!-- 4. Weekly hours -->
          <section v-else-if="step === 'hours'">
            <div class="nm-head hours-head">
              <div>
                <h1 class="nm-title">Your weekly hours</h1>
                <p class="ob-sub">When clients can book you. You can change these any time in Profile Settings, and block days off.</p>
              </div>
              <button class="ob-btn-back" type="button" @click="availabilityRef?.openWeekForm()"><Plus :size="15" aria-hidden="true" />Add hours for all week</button>
            </div>
            <Availability ref="availabilityRef" embedded hide-time-off />
            <span v-if="errors.availability" class="field-error hours-error">{{ errors.availability }}</span>
            <div class="ob-actions">
              <button class="ob-btn-back" type="button" @click="go('consult')"><ArrowLeft :size="16" aria-hidden="true" />Back</button>
              <button class="ob-btn" type="button" @click="next('hours', 'payout')">Continue<ArrowRight :size="18" aria-hidden="true" /></button>
            </div>
          </section>

          <!-- 5. Payout -->
          <section v-else-if="step === 'payout'">
            <div class="nm-head">
              <h1 class="nm-title">Your payout details <span class="po-opt">Optional</span></h1>
              <p class="ob-sub">Where NutriMatch sends your earnings on the 5th of each month. You can add this later in Earnings, but we can't pay you until it's there.</p>
            </div>
            <div class="po-facts">
              <span><CalendarClock :size="15" aria-hidden="true" />Paid every 5th of the month</span>
              <span><ShieldCheck :size="15" aria-hidden="true" />Only NutriMatch admins can see these</span>
            </div>
            <div class="po-card">
              <PayoutDetailsFields ref="payoutFields" :account="existingPayout" />
            </div>
            <label class="confirm-item">
              <input v-model="infoConfirmed" type="checkbox" :disabled="isFinishing" />
              <span>I confirm that all the information I entered here is correct and complete to the best of my knowledge.</span>
            </label>
            <p class="hint skip-note">Leave the payout details empty to add them later.</p>
            <p v-if="finishError" class="form-error">{{ finishError }}</p>
            <div class="ob-actions">
              <button class="ob-btn-back" type="button" :disabled="isFinishing" @click="go('hours')"><ArrowLeft :size="16" aria-hidden="true" />Back</button>
              <button class="ob-btn" type="button" :disabled="isFinishing || !infoConfirmed" @click="finish">
                <span v-if="isFinishing" class="ob-spin light" aria-hidden="true"></span>{{ isFinishing ? 'Finishing…' : 'Finish setup' }}<Check v-if="!isFinishing" :size="18" aria-hidden="true" />
              </button>
            </div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useAuthStore } from '~/stores/auth'
import { useToast } from '~/composables/useToast'
import { addressProblem, bioProblem, feeProblem, LANGUAGES, MODE_LABELS } from '~/utils/rndSetup'
import { ArrowLeft, ArrowRight, CalendarClock, Camera, Check, Clock, LogOut, Plus, ShieldCheck, UserRound, Video, Wallet } from 'lucide-vue-next'

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

/* ---------- UI only (same look as the client onboarding; no data or API changes) ---------- */
const plateImg = '/landing/login-plate.webp'
const platePins = [
  { tag: 'GO', label: 'Whole grains', share: '¼', x: '34%', y: '22%', side: 'to-right' },
  { tag: 'GROW', label: 'Protein', share: '¼', x: '63%', y: '35%', side: 'to-right' },
  { tag: 'GLOW', label: 'Vegetables', share: '½', x: '80%', y: '53%', side: 'to-left' },
]
const rndJourney = [
  { icon: UserRound, title: 'Your profile', text: 'A photo, a short bio and the languages you consult in.' },
  { icon: Video, title: 'Your consultations', text: 'Your fee and how you consult.' },
  { icon: CalendarClock, title: 'Your weekly hours', text: 'When clients can book you.' },
  { icon: Wallet, title: 'Your payout details', text: 'Where we send your earnings. You can add this later.' },
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

/* ===== RND-only bits on top of the shared onboarding look ===== */
.ob-chip.choice { position: relative; }
.ob-chip.choice input { position: absolute; opacity: 0; width: 1px; height: 1px; pointer-events: none; }
.ob-chip.choice:focus-within { outline: 2px solid #1F8F5C; outline-offset: 2px; }
.photo-row { display: flex; align-items: center; gap: 16px; }
.photo-preview, .photo-placeholder { width: 76px; height: 76px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 0 3px #FFFFFF, 0 0 0 5px #EFBF04; }
.photo-preview { object-fit: cover; }
.photo-placeholder { background: #063C2A; color: #EFBF04; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 800; }
.photo-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.photo-actions .hint { flex-basis: 100%; }
.photo-btn { cursor: pointer; }
.photo-remove { color: #B42318; }
.file-input { display: none; }
.bio-input { min-height: 120px; height: auto; padding-top: 12px; padding-bottom: 12px; line-height: 1.55; resize: vertical; }
.bio-meta { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; }
.char-count { font-size: 12px; color: #6B7D73; white-space: nowrap; font-variant-numeric: tabular-nums; }
.fee-wrap { display: flex; align-items: center; gap: 10px; max-width: 360px; }
.fee-wrap .ob-control { flex: 1; min-width: 0; }
.fee-prefix { font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #063C2A; }
.fee-suffix { font-size: 13.5px; color: #55665D; white-space: nowrap; }
.hours-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.hours-head .ob-btn-back { flex-shrink: 0; }
.hours-error { display: block; margin-top: 10px; }
.confirm-item { display: flex; align-items: flex-start; gap: 10px; margin: 22px 0 0; padding: 14px 16px; border-radius: 14px; background: #F4F8F5; font-size: 13.5px; color: #22362C; line-height: 1.55; cursor: pointer; }
.confirm-item input { margin-top: 3px; width: 17px; height: 17px; accent-color: #063C2A; flex-shrink: 0; cursor: pointer; }
.skip-note { margin: 10px 0 0; }
@media (max-width: 640px) {
  .hours-head { flex-direction: column; }
  .hours-head .ob-btn-back { width: 100%; justify-content: center; }
  .photo-row { align-items: flex-start; }
  .fee-wrap { max-width: none; }
}

/* ===== Weekly hours, onboarding only: days as rows (the dashboard Availability page keeps its own design) ===== */
.nm-box :deep(.av-sum) { margin: 18px 0 0 !important; }
.nm-box :deep(.av-sum span) { height: 36px !important; padding: 0 14px !important; background: #E3EFE7 !important; font-size: 13.5px !important; color: #22362C !important; }
.nm-box :deep(.day-list) { display: flex !important; flex-direction: column !important; gap: 0 !important; margin-top: 18px !important; border: 1.5px solid #E1EAE4 !important; border-radius: 18px !important; overflow: hidden !important; background: #FFFFFF !important; }
.nm-box :deep(.day-row), .nm-box :deep(.day-row:first-child) { display: grid !important; grid-template-columns: 150px minmax(0, 1fr) auto !important; align-items: center !important; gap: 14px !important; padding: 14px 16px !important; border: none !important; border-top: 1px solid #EEF2EF !important; border-radius: 0 !important; background: #FFFFFF !important; box-shadow: none !important; }
.nm-box :deep(.day-row:first-child) { border-top: none !important; }
.nm-box :deep(.day-row.empty) { background: #FAFCFB !important; }
.nm-box :deep(.day-row.today) { background: #FFFFFF !important; }
.nm-box :deep(.day-head) { display: flex !important; align-items: center !important; gap: 10px !important; padding: 0 !important; border: none !important; }
/* the switch is only a picture of open / closed (no extra logic) */
.nm-box :deep(.day-head)::before { content: ''; width: 38px; height: 22px; flex-shrink: 0; border-radius: 999px; background: #1F7A4D radial-gradient(circle at 27px 11px, #FFFFFF 7.5px, transparent 8.5px); }
.nm-box :deep(.day-row.empty .day-head)::before { background: #D3DED7 radial-gradient(circle at 11px 11px, #FFFFFF 7.5px, transparent 8.5px); }
.nm-box :deep(.day-name) { font-size: 15.5px !important; font-weight: 800 !important; color: #0E3A2C !important; }
.nm-box :deep(.day-row.empty:not(.today) .day-name) { color: #0E3A2C !important; }
.nm-box :deep(.day-head small) { display: none !important; }
.nm-box :deep(.today-tag) { padding: 2px 8px !important; font-size: 11px !important; }
.nm-box :deep(.day-content) { display: flex !important; flex-direction: row !important; flex-wrap: wrap !important; align-items: center !important; gap: 8px !important; }
.nm-box :deep(.slot-pill) { display: inline-flex !important; flex-direction: row !important; align-items: center !important; gap: 4px !important; width: auto !important; height: 34px !important; padding: 0 32px 0 12px !important; border: none !important; border-radius: 999px !important; background: #E3EFE7 !important; color: #063C2A !important; font-size: 13px !important; font-weight: 800 !important; box-shadow: none !important; }
.nm-box :deep(.slot-pill .sp-from), .nm-box :deep(.slot-pill .sp-to) { font-size: 13px !important; font-weight: 800 !important; color: #063C2A !important; }
.nm-box :deep(.slot-pill .pill-icon-btn) { top: 6px !important; right: 6px !important; width: 22px !important; height: 22px !important; background: #FFFFFF !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; }
.nm-box :deep(.empty-note-inline) { padding: 0 !important; text-align: left !important; font-size: 13.5px !important; font-weight: 600 !important; color: #8A9A91 !important; }
.nm-box :deep(.day-preview) { flex-basis: 100% !important; margin: 2px 0 0 !important; font-size: 12px !important; color: #6B7D73 !important; }
.nm-box :deep(.slot-edit-form) { flex-direction: row !important; flex-wrap: wrap !important; align-items: center !important; width: 100% !important; padding: 8px 10px !important; border-radius: 12px !important; }
.nm-box :deep(.slot-edit-form .time-input) { width: auto !important; flex: 1 1 120px !important; }
.nm-box :deep(.slot-edit-form .form-btn) { width: auto !important; }
.nm-box :deep(.day-action-link.day-add) { display: inline-flex !important; align-items: center !important; gap: 6px !important; height: 34px !important; padding: 0 12px !important; border: 1.5px dashed #B9CFC1 !important; border-radius: 999px !important; background: #FFFFFF !important; color: #063C2A !important; font-size: 12.5px !important; font-weight: 800 !important; white-space: nowrap; }
.nm-box :deep(.day-row:not(.empty) .day-action-link.day-add) { border-style: solid !important; }
@media (max-width: 640px) {
  .nm-box :deep(.day-row), .nm-box :deep(.day-row:first-child) { grid-template-columns: 1fr auto !important; gap: 10px !important; }
  .nm-box :deep(.day-content) { grid-column: 1 / -1 !important; grid-row: 2 !important; }
}

/* ===== Payout step (onboarding only) ===== */
.po-opt { display: inline-block; vertical-align: middle; margin-left: 8px; padding: 4px 10px; border-radius: 999px; background: #EEF4F0; color: #55665D; font-family: 'DM Sans', sans-serif; font-size: 12px; font-weight: 800; font-style: normal; letter-spacing: 0.3px; }
.po-facts { display: flex; flex-wrap: wrap; gap: 8px; margin: 18px 0 0; }
.po-facts span { display: inline-flex; align-items: center; gap: 7px; height: 34px; padding: 0 13px; border-radius: 999px; background: #E3EFE7; color: #22362C; font-size: 13px; font-weight: 600; }
.po-facts svg { color: #1F7A4D; }
.po-card { margin-top: 18px; padding: 22px; border-radius: 20px; border: 1.5px solid #E1EAE4; background: #FAFCFB; }
/* method: two big tiles */
.po-card :deep(div:has(> label > input[type="radio"])) { display: grid !important; grid-template-columns: 1fr 1fr; gap: 10px; }
.po-card :deep(label:has(input[type="radio"])) { position: relative; display: flex !important; align-items: center; gap: 12px; min-height: 64px; padding: 0 16px 0 62px; border: 1.5px solid #DCE5DF !important; border-radius: 16px !important; background: #FFFFFF !important; font-size: 15px; font-weight: 800; color: #22362C; cursor: pointer; }
.po-card :deep(label:has(input[type="radio"]))::before { content: ''; position: absolute; left: 14px; top: 50%; width: 36px; height: 36px; margin-top: -18px; border-radius: 50%; background: #EEF4F0 center / 18px no-repeat url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23004D3A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='6' width='18' height='13' rx='3'/%3E%3Cpath d='M3 10h18M16 15h2'/%3E%3C/svg%3E"); }
.po-card :deep(label:has(input[type="radio"]) ~ label:has(input[type="radio"]))::before { background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23004D3A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 10 12 4l9 6M5 10v8M9 10v8M15 10v8M19 10v8M3 20h18'/%3E%3C/svg%3E"); }
.po-card :deep(label:has(input[type="radio"]:checked)) { border-color: #063C2A !important; background: #F1F8F4 !important; color: #063C2A; box-shadow: 0 0 0 4px rgba(6, 60, 42, 0.08); }
.po-card :deep(label:has(input[type="radio"]:checked))::before { background-color: #FBF3D2; }
.po-card :deep(input[type="radio"]) { position: absolute; right: 16px; top: 50%; margin: -9px 0 0 !important; width: 18px; height: 18px; accent-color: #063C2A; }
/* fields: same look as the other onboarding fields */
.po-card :deep(label:not(:has(input[type="radio"]))) { display: block; margin: 18px 0 8px; font-size: 13px; font-weight: 600; color: #22362C; }
.po-card :deep(input:not([type="radio"]):not([type="checkbox"])),
.po-card :deep(select) { width: 100%; height: 52px; min-height: 52px; padding: 0 16px; border: 1.5px solid #DCE5DF !important; border-radius: 14px !important; background-color: #FFFFFF; font-family: inherit; font-size: 15px; color: #0E3A2C; box-sizing: border-box; }
.po-card :deep(input:not([type="radio"]):not([type="checkbox"]):focus),
.po-card :deep(select:focus) { outline: none; border-color: #063C2A !important; box-shadow: 0 0 0 4px rgba(6, 60, 42, 0.10) !important; }
.po-card :deep(small), .po-card :deep(.hint) { font-size: 12px; color: #6B7D73; }
@media (max-width: 640px) {
  .po-card { padding: 16px; }
  .po-card :deep(div:has(> label > input[type="radio"])) { grid-template-columns: 1fr; }
}
</style>