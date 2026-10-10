<template>
  <div class="register-page">
    <!-- LEFT PANEL -->
    <aside class="left-panel">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>

      <div class="brand">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="logo-img" />
        <span class="logo-text" style="font-family: 'DM Serif Display', serif; font-weight: 700; font-size: medium;">Nutri<span class="logo-match">Match</span></span>
      </div>

      <div class="left-content">
        <span class="eyebrow">CREATE ACCOUNT</span>
        <h1>
          Join your<br />
          <em class="highlight">nutrition</em><br />
          journey today.
        </h1>

        <div class="steps">
          <div
            v-for="(step, index) in steps"
            :key="step.label"
            class="step"
            :class="{ active: stageIndex === index, done: stageIndex > index }"
          >
            <span class="step-number">
              <span v-if="stageIndex > index">✓</span>
              <span v-else>{{ index + 1 }}</span>
            </span>
            <div class="step-text">
              <span class="step-label">STEP {{ String(index + 1).padStart(2, '0') }}</span>
              <span class="step-title">{{ step.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- RIGHT PANEL -->
    <main class="right-panel">
      <div class="form-wrap">
        <!-- STEP 1: CHOOSE ROLE -->
        <div v-if="currentStep === 1">
          <h2>Choose Your Role</h2>
          <p class="subtitle">Step 1 of {{ steps.length }} — Tell us how you'll use NutriMatch</p>

          <div class="role-grid">
            <button
              v-for="role in roles"
              :key="role.value"
              class="role-card"
              :class="{ selected: selectedRole === role.value }"
              @click="selectedRole = role.value"
            >
              <span class="role-icon" v-html="role.icon"></span>
              <span class="role-name">{{ role.label }}</span>
              <span class="role-desc">{{ role.desc }}</span>
            </button>
          </div>

          <Transition name="fade-slide">
            <div v-if="roleInfo" class="role-info-box">
              <p>{{ roleInfo }}</p>
            </div>
          </Transition>

          <button class="btn-primary" :disabled="!selectedRole" @click="currentStep = 2">
            Continue →
          </button>
        </div>

        <!-- STEP 2: YOUR DETAILS -->
        <div v-else-if="currentStep === 2">
          <h2>{{ selectedRole === 'rnd' ? 'Account & License' : 'Your Details' }}</h2>
          <p class="subtitle">Step 2 of {{ steps.length }} — {{ selectedRole === 'rnd' ? 'Your account and PRC credentials' : 'Enter your personal information' }}</p>

          <form class="details-form" novalidate @submit.prevent="goToConfirm">
            <div class="field-row">
              <div class="field">
                <label>First Name</label>
                <input v-model="form.firstName" type="text" placeholder="e.g. Juan" maxlength="100" :class="{ invalid: firstNameError }" required />
                <span v-if="firstNameError" class="field-error">{{ firstNameError }}</span>
              </div>
              <div class="field">
                <label>Last Name</label>
                <input v-model="form.lastName" type="text" placeholder="e.g. Dela Cruz" maxlength="100" :class="{ invalid: lastNameError }" required />
                <span v-if="lastNameError" class="field-error">{{ lastNameError }}</span>
              </div>
            </div>

            <div class="field">
              <label>Email Address</label>
              <div class="input-icon-wrap">
                <User class="input-icon" aria-hidden="true" />
                <input v-model.trim="form.email" type="email" placeholder="you@example.com" :class="{ invalid: emailError }" required />
              </div>
              <span v-if="emailError" class="field-error">{{ emailError }}</span>
            </div>

            <div class="field">
              <label>Password</label>
              <div class="input-icon-wrap">
                <Lock class="input-icon" aria-hidden="true" />
                <input
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Min. 8 characters"
                  minlength="8"
                  required
                />
                <button type="button" class="toggle-visibility" @click="showPassword = !showPassword">
                  {{ showPassword ? 'HIDE' : 'SHOW' }}
                </button>
              </div>
              <ul class="pw-rules" aria-label="Password requirements">
                <li v-for="rule in passwordRules" :key="rule.label" :class="{ ok: rule.ok }">
                  <span class="pw-rule-mark">{{ rule.ok ? '✓' : '○' }}</span> {{ rule.label }}
                </li>
              </ul>
            </div>

            <div class="field">
              <label>Confirm Password</label>
              <div class="input-icon-wrap">
                <Lock class="input-icon" aria-hidden="true" />
                <input
                  v-model="form.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="Repeat your password"
                  required
                />
                <button type="button" class="toggle-visibility" @click="showConfirmPassword = !showConfirmPassword">
                  {{ showConfirmPassword ? 'HIDE' : 'SHOW' }}
                </button>
              </div>
              <span v-if="form.confirmPassword && !passwordsMatch" class="field-error">Passwords do not match.</span>
            </div>

            <template v-if="selectedRole === 'patient'">
              <div class="field-row">
                <div class="field">
                  <label>Date of Birth</label>
                  <input v-model="form.dob" type="date" :max="latestBirthDate" min="1900-01-01" :class="{ invalid: dobError }" required />
                  <span v-if="dobError" class="field-error">{{ dobError }}</span>
                </div>
                <div class="field">
                  <label>Gender</label>
                  <select v-model="form.gender" required>
                    <option disabled value="">Select</option>
                    <option>Female</option>
                    <option>Male</option>
                    <option>Prefer not to say</option>
                  </select>
                </div>
              </div>

              <div class="field">
                <label>Primary Health Concern</label>
                <select v-model="form.healthConcern" required>
                  <option disabled value="">Select</option>
                  <option>Hypertension</option>
                  <option>Type 2 Diabetes</option>
                  <option>Obesity Management</option>
                  <option>Renal Nutrition</option>
                  <option>Other</option>
                </select>
              </div>
            </template>

            <template v-else-if="selectedRole === 'rnd'">
              <div class="field">
                <label>Date of Birth</label>
                <input v-model="form.dob" type="date" :max="latestBirthDate" min="1900-01-01" :class="{ invalid: dobError }" required />
                <span v-if="dobError" class="field-error">{{ dobError }}</span>
              </div>
              <div class="field">
                <label>PRC License Number <span class="required-tag">Required</span></label>
                <input
                  v-model="form.prcNumber"
                  type="text"
                  inputmode="numeric"
                  maxlength="7"
                  placeholder="e.g. 0123456"
                  :class="{ invalid: prcNumberError }"
                />
                <span v-if="prcNumberError" class="field-error">{{ prcNumberError }}</span>
                <span v-else class="license-hint">The 7-digit number on your PRC ID.</span>
              </div>
              <div class="field">
                <label>PRC License Photo <span class="required-tag">Required</span></label>
                <label class="license-upload" :class="{ 'has-file': licensePreview }">
                  <input ref="licenseInput" type="file" accept="image/jpeg,image/png,image/webp" class="license-input" @change="onLicenseSelected" />
                  <img v-if="licensePreview" :src="licensePreview" alt="PRC license preview" class="license-preview" />
                  <span v-else class="license-placeholder">
                    <strong>Upload a clear photo of your PRC ID</strong>
                    JPG, PNG, or WEBP · up to 5 MB
                  </span>
                </label>
                <div v-if="form.prcLicenseImage" class="license-file-row">
                  <span class="license-filename">{{ form.prcLicenseImage.name }} · click the photo to change</span>
                  <button type="button" class="license-remove" @click="removeLicense">Remove</button>
                </div>
                <span class="license-hint">Only our admin team sees this photo, to verify your license.</span>
              </div>
              <div class="field">
                <label>Specialization <span class="required-tag">Required</span></label>
                <select v-model="form.specialization" required>
                  <option disabled value="">Select</option>
                  <option v-for="sp in SPECIALIZATIONS" :key="sp" :value="sp">{{ sp }}</option>
                </select>
              </div>
            </template>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

            <div class="form-nav">
              <button type="button" class="btn-back" @click="currentStep = 1">← Back</button>
              <button type="submit" class="btn-primary" :disabled="!detailsValid">Continue →</button>
            </div>
          </form>
        </div>

        <!-- RND STEP 3: PROFESSIONAL PROFILE (stage 5) -->
        <div v-else-if="currentStep === 5">
          <h2>Professional Profile</h2>
          <p class="subtitle">Step 3 of {{ steps.length }} — What clients see before booking</p>

          <form class="details-form" novalidate @submit.prevent="goToConsultation">
            <div class="field">
              <label>Profile Photo <span class="optional-tag">Optional</span></label>
              <div class="photo-row">
                <img v-if="photoPreview" :src="photoPreview" alt="Profile photo preview" class="photo-preview" />
                <div v-else class="photo-placeholder">{{ (form.firstName[0] || '') + (form.lastName[0] || '') }}</div>
                <div class="photo-actions">
                  <label class="photo-btn">
                    <input ref="photoInput" type="file" accept="image/jpeg,image/png,image/webp" class="license-input" @change="onPhotoSelected" />
                    {{ form.profilePhoto ? 'Change photo' : 'Upload photo' }}
                  </label>
                  <button v-if="form.profilePhoto" type="button" class="license-remove" @click="removePhoto">Remove</button>
                  <span class="license-hint">A clear, friendly headshot. JPG, PNG or WEBP · max 2 MB.</span>
                </div>
              </div>
            </div>

            <div class="field">
              <label>Professional Bio <span class="required-tag">Required</span></label>
              <textarea
                v-model="form.bio" rows="5" maxlength="1000" class="bio-input" :class="{ invalid: bioError }"
                placeholder="e.g. Registered Nutritionist-Dietitian with 6 years of hospital experience, helping adults manage diabetes and lose weight through practical Filipino meals."
              ></textarea>
              <div class="bio-meta">
                <span v-if="bioError" class="field-error">{{ bioError }}</span>
                <span v-else class="license-hint">At least 50 characters. Shown on your public profile.</span>
                <span class="char-count" :class="{ short: form.bio.trim().length < 50 }">{{ form.bio.trim().length }}/1000</span>
              </div>
            </div>

            <div class="field">
              <label>Languages You Consult In <span class="required-tag">Required</span></label>
              <div class="chip-grid">
                <label v-for="lang in LANGUAGES" :key="lang.code" class="choice-chip" :class="{ checked: form.languages.includes(lang.code) }">
                  <input v-model="form.languages" type="checkbox" :value="lang.code" />
                  {{ lang.name }}
                </label>
              </div>
            </div>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
            <div class="form-nav">
              <button type="button" class="btn-back" @click="currentStep = 2">← Back</button>
              <button type="submit" class="btn-primary" :disabled="!profileValid">Continue →</button>
            </div>
          </form>
        </div>

        <!-- RND STEP 4: CONSULTATION SETUP (stage 6) -->
        <div v-else-if="currentStep === 6">
          <h2>Consultation Setup</h2>
          <p class="subtitle">Step 4 of {{ steps.length }} — Your fee, formats and weekly hours</p>

          <form class="details-form" novalidate @submit.prevent="goToConfirm">
            <div class="field">
              <label>Consultation Fee <span class="required-tag">Required</span></label>
              <div class="fee-wrap">
                <span class="fee-prefix">₱</span>
                <input v-model.number="form.fee" type="number" inputmode="numeric" min="100" step="50" placeholder="e.g. 800" :class="{ invalid: feeError }" />
                <span class="fee-suffix">per session</span>
              </div>
              <span v-if="feeError" class="field-error">{{ feeError }}</span>
              <span v-else class="license-hint">At least ₱100. Clients pay this before each consultation.</span>
            </div>

            <div class="field">
              <label>Consultation Formats <span class="required-tag">Required</span></label>
              <div class="chip-grid">
                <label v-for="(label, key) in MODE_LABELS" :key="key" class="choice-chip" :class="{ checked: form.modes.includes(key) }">
                  <input v-model="form.modes" type="checkbox" :value="key" />
                  {{ label }}
                </label>
              </div>
            </div>

            <div class="field">
              <label>Weekly Availability <span class="required-tag">Required</span></label>
              <span class="license-hint">Clients can only book within these hours. Each block must be at least 1 hour.</span>
              <div class="avail-list">
                <div v-for="day in DAYS" :key="day.value" class="avail-day" :class="{ off: !dayBlocks(day.value).length }">
                  <div class="avail-day-head">
                    <span class="avail-day-name">{{ day.label }}</span>
                    <button v-if="!dayBlocks(day.value).length" type="button" class="avail-add" @click="addBlock(day.value)">+ Add hours</button>
                    <span v-else class="avail-on">Available</span>
                  </div>
                  <div v-for="block in dayBlocks(day.value)" :key="block.id" class="avail-block">
                    <select v-model="block.start" :aria-label="`${day.label} start time`">
                      <option v-for="t in TIME_OPTIONS" :key="t.value" :value="t.value">{{ t.label }}</option>
                    </select>
                    <span class="avail-to">to</span>
                    <select v-model="block.end" :aria-label="`${day.label} end time`">
                      <option v-for="t in TIME_OPTIONS" :key="t.value" :value="t.value">{{ t.label }}</option>
                    </select>
                    <button type="button" class="avail-remove" :aria-label="`Remove ${day.label} block`" @click="removeBlock(block.id)">✕</button>
                  </div>
                  <button v-if="dayBlocks(day.value).length" type="button" class="avail-add small" @click="addBlock(day.value)">+ Add another block</button>
                </div>
              </div>
              <span v-if="availabilityError && availability.length" class="field-error">{{ availabilityError }}</span>
            </div>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
            <div class="form-nav">
              <button type="button" class="btn-back" @click="currentStep = 5">← Back</button>
              <button type="submit" class="btn-primary" :disabled="!consultationValid">Continue →</button>
            </div>
          </form>
        </div>

        <!-- RND: APPLICATION UNDER REVIEW (stage 7, after verifying the email) -->
        <div v-else-if="currentStep === 7" class="review-stage">
          <div class="review-icon"><ClipboardCheck :size="28" aria-hidden="true" /></div>
          <h2>Application Submitted</h2>
          <p class="subtitle">
            Thank you, {{ form.firstName }}! Your email is confirmed and your application is now with our admin team.
          </p>
          <ol class="review-steps">
            <li><strong>We review your PRC license and profile</strong> — usually within 1–2 business days.</li>
            <li><strong>We email you at {{ form.email }}</strong> once your account is approved (or if we need anything fixed).</li>
            <li><strong>Then you can sign in</strong> — clients will find your profile and book within your available hours.</li>
          </ol>
          <p class="review-small">You won't be able to sign in until your application is approved.</p>
          <button type="button" class="btn-primary" @click="navigateTo('/')">Back to Homepage</button>
        </div>

        <!-- STEP 3: CONFIRM -->
        <div v-else-if="currentStep === 3">
          <h2>{{ selectedRole === 'rnd' ? 'Review Your Application' : 'Confirm Your Details' }}</h2>
          <p class="subtitle">Step {{ steps.length }} of {{ steps.length }} — Review before submitting</p>

          <div class="confirm-summary">
            <div class="confirm-row"><span>Role</span><strong>{{ selectedRole === 'rnd' ? 'RND' : 'Patient' }}</strong></div>
            <div class="confirm-row"><span>Name</span><strong>{{ form.firstName }} {{ form.lastName }}</strong></div>
            <div class="confirm-row"><span>Email</span><strong class="no-capitalize">{{ form.email }}</strong></div>
            <template v-if="selectedRole === 'patient'">
              <div class="confirm-row"><span>Date of Birth</span><strong>{{ form.dob }}</strong></div>
              <div class="confirm-row"><span>Gender</span><strong>{{ form.gender }}</strong></div>
              <div class="confirm-row"><span>Primary Health Concern</span><strong>{{ form.healthConcern }}</strong></div>
            </template>
            <template v-else-if="selectedRole === 'rnd'">
              <div class="confirm-row"><span>Date of Birth</span><strong>{{ form.dob }}</strong></div>
              <div class="confirm-row"><span>PRC License Number</span><strong>{{ form.prcNumber }}</strong></div>
              <div class="confirm-row"><span>PRC License Photo</span><img v-if="licensePreview" :src="licensePreview" alt="PRC license" class="confirm-license" /></div>
              <div class="confirm-row"><span>Specialization</span><strong>{{ form.specialization || '—' }}</strong></div>
              <div class="confirm-row"><span>Languages</span><strong>{{ form.languages.map(languageName).join(', ') }}</strong></div>
              <div class="confirm-row"><span>Consultation Fee</span><strong>₱{{ Number(form.fee).toLocaleString() }} per session</strong></div>
              <div class="confirm-row"><span>Formats</span><strong>{{ form.modes.map(m => MODE_LABELS[m]).join(', ') }}</strong></div>
              <div class="confirm-row confirm-block"><span>Weekly Availability</span>
                <ul class="confirm-hours">
                  <li v-for="line in availabilitySummary" :key="line">{{ line }}</li>
                </ul>
              </div>
              <div class="confirm-row confirm-block"><span>Bio</span><p class="confirm-bio">{{ form.bio.trim() }}</p></div>
              <div v-if="photoPreview" class="confirm-row"><span>Profile Photo</span><img :src="photoPreview" alt="Profile photo" class="confirm-photo" /></div>
            </template>
          </div>
          <p v-if="selectedRole === 'rnd'" class="review-note">
            Our admin team reviews your PRC license and profile before your account is activated — usually within 1–2 business days.
            You'll be able to sign in once it's approved.
          </p>

          <!-- Informed consent (RA 10173) — both required; recorded on the
               account and in the audit log by the API. -->
          <div class="consent-box">
            <label class="consent-item">
              <input v-model="consent.terms" type="checkbox" :disabled="isSubmitting" />
              <span>
                I have read and agree to the
                <a href="/terms" target="_blank" rel="noopener">Terms and Conditions</a> and
                <a href="/privacy-policy" target="_blank" rel="noopener">Privacy Policy</a>.
              </span>
            </label>
            <label class="consent-item">
              <input v-model="consent.data" type="checkbox" :disabled="isSubmitting" />
              <span>
                I consent to NutriMatch collecting and processing my personal and health information
                {{ selectedRole === 'rnd' ? '(including my PRC license photo, for verification)' : '(including my screening and nutrition records)' }}
                to provide nutrition care services, as described in the Privacy Policy, in accordance with
                Republic Act No. 10173 (Data Privacy Act of 2012).
              </span>
            </label>
          </div>

          <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

          <div class="form-nav">
            <button type="button" class="btn-back" :disabled="isSubmitting" @click="currentStep = selectedRole === 'rnd' ? 6 : 2">← Back</button>
            <button class="btn-primary" :disabled="isSubmitting || !consentGiven" :aria-busy="isSubmitting" @click="submitRegistration">
              <span v-if="isSubmitting" class="btn-spinner" aria-hidden="true"></span>
              {{ isSubmitting ? (selectedRole === 'rnd' ? 'Submitting…' : 'Creating account…') : (selectedRole === 'rnd' ? 'Submit Application →' : 'Create Account →') }}
            </button>
          </div>
        </div>

        <!-- STEP 4: VERIFY EMAIL -->
        <div v-else-if="currentStep === 4">
          <div class="sent-icon"><Mail :size="26" aria-hidden="true" /></div>
          <h2>Verify Your Email</h2>
          <p class="subtitle">
            We've sent a 6-digit code to <strong>{{ form.email }}</strong>. Enter it below to activate your account.
          </p>

          <form class="details-form" @submit.prevent="submitVerification">
            <div class="field">
              <label>Verification Code</label>
              <input v-model="verificationCode" type="text" inputmode="numeric" maxlength="6" placeholder="123456" class="code-input" required />
            </div>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
            <p v-if="resendMessage" class="form-success">{{ resendMessage }}</p>

            <button type="submit" class="btn-primary" :disabled="isSubmitting || isResending" :aria-busy="isSubmitting">
              <span v-if="isSubmitting" class="btn-spinner" aria-hidden="true"></span>
              {{ isSubmitting ? 'Verifying…' : 'Verify & Continue →' }}
            </button>
          </form>

          <p class="signin-link">
            Didn't get the code?
            <a href="#" :class="{ 'link-disabled': isSubmitting || isResending }" :aria-disabled="isSubmitting || isResending" @click.prevent="!isSubmitting && !isResending && resendCode()">{{ isResending ? 'Sending…' : 'Resend code' }}</a>
          </p>
        </div>

        <p v-if="![4, 7].includes(currentStep)" class="signin-link">
          Already have an account? <a href="#" :class="{ 'link-disabled': isSubmitting }" :aria-disabled="isSubmitting" @click.prevent="!isSubmitting && navigateTo('/login')">Sign in →</a>
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ClipboardCheck, Lock, Mail, User } from 'lucide-vue-next'
const auth = useAuthStore()

const currentStep = ref(1)
const selectedRole = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const errorMessage = ref('')
const isSubmitting = ref(false)
const verificationCode = ref('')
const isResending = ref(false)
const resendMessage = ref('')

const form = reactive({
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  confirmPassword: '',
  dob: '',
  gender: '',
  healthConcern: '',
  prcLicenseImage: null,
  prcNumber: '',
  specialization: '',
  // RND application (onboarding): reviewed by the admin before sign-in.
  profilePhoto: null,
  bio: '',
  languages: [],
  fee: '',
  modes: ['video'],
})

// Both consent checkboxes on the Confirm step must be ticked to register.
const consent = reactive({ terms: false, data: false })
const consentGiven = computed(() => consent.terms && consent.data)

const MAX_LICENSE_BYTES = 5 * 1024 * 1024
const licensePreview = ref('')

function onLicenseSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  errorMessage.value = ''
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    errorMessage.value = 'Upload a JPG, PNG, or WEBP photo of your PRC license.'
    return
  }
  if (file.size > MAX_LICENSE_BYTES) {
    errorMessage.value = 'The license photo must be 5 MB or smaller.'
    return
  }
  if (licensePreview.value) URL.revokeObjectURL(licensePreview.value)
  form.prcLicenseImage = file
  licensePreview.value = URL.createObjectURL(file)
}
onBeforeUnmount(() => {
  if (licensePreview.value) URL.revokeObjectURL(licensePreview.value)
})
const licenseInput = ref(null)
function removeLicense() {
  if (licensePreview.value) URL.revokeObjectURL(licensePreview.value)
  licensePreview.value = ''
  form.prcLicenseImage = null
  // so picking the same file again still fires @change
  if (licenseInput.value) licenseInput.value.value = ''
}

// Same list the API accepts (profiles/models.py RND_SPECIALIZATIONS); each
// contains the keyword the "Find an RND" filter searches for.
const SPECIALIZATIONS = [
  'Diabetes Management',
  'Weight Management',
  'Renal Nutrition',
  'Hypertension & Cardiac Care',
  'Pediatric Nutrition',
  'Sports Nutrition',
  'General / Clinical Nutrition',
]
// Digits only, max 7 — applied after v-model stores the keystroke (an
// @input handler runs before v-model and would write back the old value).
watch(() => form.prcNumber, v => {
  const digits = v.replace(/\D/g, '').slice(0, 7)
  if (digits !== v) form.prcNumber = digits
})
const prcNumberError = computed(() =>
  form.prcNumber && !/^\d{7}$/.test(form.prcNumber) ? 'Enter all 7 digits of your PRC license number.' : ''
)

/* ---------- Step 2 validation (the API enforces the same rules) ---------- */
// Letters in any language plus spaces, hyphens, apostrophes and periods
// ("Dela Cruz", "O'Neil", "Ma. Theresa") — no numbers or other symbols.
const NAME_RE = /^\p{L}+(?:[ .'\-]+\p{L}+)*\.?$/u
function nameError(value) {
  const v = value.trim()
  if (!v) return ''
  return NAME_RE.test(v) ? '' : 'Letters only — no numbers or symbols.'
}
const firstNameError = computed(() => nameError(form.firstName))
const lastNameError = computed(() => nameError(form.lastName))

// Capitalize the first letter of each word as it's typed ("juan dela cruz"
// → "Juan Dela Cruz", "o'neil" → "O'Neil"); the rest is left as typed. The
// API normalizes the same way.
function capitalizeWords(value) {
  return value.replace(/(^|[\s\-'.])(\p{L})/gu, (_, sep, ch) => sep + ch.toUpperCase())
}
watch(() => form.firstName, v => { const c = capitalizeWords(v); if (c !== v) form.firstName = c })
watch(() => form.lastName, v => { const c = capitalizeWords(v); if (c !== v) form.lastName = c })

// Shown under the field as soon as something's typed, like "Passwords do
// not match" — instead of the browser's own "Please include an '@'" popup.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/
const emailError = computed(() =>
  form.email && !EMAIL_RE.test(form.email) ? 'Enter a valid email address (e.g. juan@example.com).' : ''
)

const passwordRules = computed(() => [
  { label: 'At least 8 characters', ok: form.password.length >= 8 },
  { label: 'One uppercase letter', ok: /[A-Z]/.test(form.password) },
  { label: 'One lowercase letter', ok: /[a-z]/.test(form.password) },
  { label: 'One number', ok: /\d/.test(form.password) },
  { label: 'One special character (e.g. ! @ # $)', ok: /[^A-Za-z0-9\s]/.test(form.password) },
])
const passwordsMatch = computed(() => form.password === form.confirmPassword)

// Local date (not toISOString, which is UTC and a day behind before 8 AM PHT).
const todayIso = (() => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})()
// Minimum ages — the API enforces the same numbers (accounts/validators.py):
// clients 18 (a minor's health data needs a guardian's consent, RA 10173),
// RNDs 21 (4-year nutrition degree + PRC board exam).
const MIN_AGE = { patient: 18, rnd: 21 }
const minAge = computed(() => MIN_AGE[selectedRole.value] || 18)
// The latest birth date that's old enough, for the date picker's max.
const latestBirthDate = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - minAge.value)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})
const dobError = computed(() => {
  if (!form.dob) return ''
  if (form.dob > todayIso) return "Date of birth can't be in the future."
  if (form.dob < '1900-01-01') return 'Enter a valid date of birth.'
  if (form.dob > latestBirthDate.value) {
    return selectedRole.value === 'rnd'
      ? `RNDs must be at least ${minAge.value} years old to register.`
      : `You must be at least ${minAge.value} years old to create an account.`
  }
  return ''
})

const detailsValid = computed(() => {
  const common = form.firstName.trim() && form.lastName.trim() && !firstNameError.value && !lastNameError.value
    && form.email && !emailError.value && passwordRules.value.every(r => r.ok) && form.confirmPassword && passwordsMatch.value
  if (!common) return false
  if (selectedRole.value === 'patient') return !!(form.dob && !dobError.value && form.gender && form.healthConcern)
  if (selectedRole.value === 'rnd') {
    return !!(form.prcLicenseImage && form.dob && !dobError.value
      && /^\d{7}$/.test(form.prcNumber) && form.specialization)
  }
  return false
})

function goToConfirm() {
  if (!detailsValid.value) {
    errorMessage.value = 'Please fix the highlighted fields first.'
    return
  }
  if (selectedRole.value === 'rnd' && !form.prcLicenseImage) {
    errorMessage.value = 'Please upload a photo of your PRC license.'
    return
  }
  if (selectedRole.value === 'rnd' && currentStep.value === 2) {
    errorMessage.value = ''
    currentStep.value = 5
    return
  }
  if (selectedRole.value === 'rnd' && !consultationValid.value) {
    errorMessage.value = 'Please fix the highlighted fields first.'
    return
  }
  errorMessage.value = ''
  currentStep.value = 3
}

/* ---------- RND application: profile + consultation setup ---------- */
// Same lists/rules the API enforces (profiles/models.py LANGUAGES,
// MIN_CONSULTATION_FEE; accounts/serializers.py RegisterRndSerializer).
const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'tl', name: 'Filipino (Tagalog)' },
  { code: 'ceb', name: 'Bisaya (Cebuano)' },
  { code: 'ilo', name: 'Ilocano' },
  { code: 'hil', name: 'Hiligaynon (Ilonggo)' },
  { code: 'war', name: 'Waray' },
  { code: 'pam', name: 'Kapampangan' },
  { code: 'bcl', name: 'Bicolano' },
]
const languageName = (code) => LANGUAGES.find(l => l.code === code)?.name || code
const MODE_LABELS = { video: 'Video call', chat: 'Chat', in_person: 'In-person' }
const MIN_FEE = 100
const DAYS = [
  { value: 1, label: 'Monday' }, { value: 2, label: 'Tuesday' }, { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' }, { value: 5, label: 'Friday' }, { value: 6, label: 'Saturday' }, { value: 0, label: 'Sunday' },
]
// 6:00 AM – 10:00 PM in 30-minute steps.
const TIME_OPTIONS = Array.from({ length: 33 }, (_, i) => {
  const minutes = 6 * 60 + i * 30
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return { value: `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`, label: `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}` }
})
const timeLabel = (v) => TIME_OPTIONS.find(t => t.value === v)?.label || v

const availability = ref([])
let blockSeq = 0
const dayBlocks = (day) => availability.value.filter(b => b.day === day)
function addBlock(day) {
  const existing = dayBlocks(day)
  const start = existing.length ? existing[existing.length - 1].end : '09:00'
  const startIdx = Math.max(0, TIME_OPTIONS.findIndex(t => t.value === start))
  const end = TIME_OPTIONS[Math.min(startIdx + 6, TIME_OPTIONS.length - 1)].value
  availability.value.push({ id: ++blockSeq, day, start, end })
}
function removeBlock(id) {
  availability.value = availability.value.filter(b => b.id !== id)
}
const toMin = (t) => { const [h, m] = t.split(':').map(Number); return h * 60 + m }
const availabilityError = computed(() => {
  if (!availability.value.length) return 'Add at least one block of hours.'
  for (const b of availability.value) {
    if (toMin(b.end) - toMin(b.start) < 60) return `${DAYS.find(d => d.value === b.day).label}: each block must be at least 1 hour.`
  }
  for (const day of DAYS) {
    const blocks = dayBlocks(day.value).slice().sort((a, b) => toMin(a.start) - toMin(b.start))
    for (let i = 1; i < blocks.length; i++) {
      if (toMin(blocks[i].start) < toMin(blocks[i - 1].end)) return `${day.label}: two blocks overlap.`
    }
  }
  return ''
})
const availabilitySummary = computed(() =>
  DAYS.filter(d => dayBlocks(d.value).length).map(d =>
    `${d.label}: ${dayBlocks(d.value).slice().sort((a, b) => toMin(a.start) - toMin(b.start)).map(b => `${timeLabel(b.start)} – ${timeLabel(b.end)}`).join(', ')}`
  )
)

const bioError = computed(() => {
  const len = form.bio.trim().length
  return len > 0 && len < 50 ? `Write at least 50 characters (${50 - len} more).` : ''
})
const feeError = computed(() => {
  if (form.fee === '' || form.fee === null) return ''
  if (!Number.isFinite(Number(form.fee)) || Number(form.fee) < MIN_FEE) return `The fee must be at least ₱${MIN_FEE}.`
  if (Number(form.fee) > 100000) return 'Enter a realistic fee.'
  return ''
})
const profileValid = computed(() => form.bio.trim().length >= 50 && form.languages.length > 0)
const consultationValid = computed(() =>
  Number(form.fee) >= MIN_FEE && !feeError.value && form.modes.length > 0 && !availabilityError.value
)
function goToConsultation() {
  if (!profileValid.value) {
    errorMessage.value = form.languages.length ? 'Your bio needs at least 50 characters.' : 'Choose at least one language.'
    return
  }
  errorMessage.value = ''
  currentStep.value = 6
}

const MAX_PHOTO_BYTES = 2 * 1024 * 1024
const photoPreview = ref('')
const photoInput = ref(null)
function onPhotoSelected(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  errorMessage.value = ''
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    errorMessage.value = 'Use a JPG, PNG, or WEBP image for your profile photo.'
    return
  }
  if (file.size > MAX_PHOTO_BYTES) {
    errorMessage.value = 'The profile photo must be 2 MB or smaller.'
    return
  }
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  form.profilePhoto = file
  photoPreview.value = URL.createObjectURL(file)
}
function removePhoto() {
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photoPreview.value = ''
  form.profilePhoto = null
}
onBeforeUnmount(() => { if (photoPreview.value) URL.revokeObjectURL(photoPreview.value) })

const genderToSex = { Male: 'male', Female: 'female' }

// RNDs fill in a full application (reviewed by an admin before they can sign
// in); clients keep the short form. Stage numbers: 1 role, 2 details,
// 5 profile, 6 consultation, 3 confirm, 4 verify email, 7 under review.
const steps = computed(() => (selectedRole.value === 'rnd'
  ? [{ label: 'Choose Role' }, { label: 'Account & License' }, { label: 'Profile' }, { label: 'Consultation' }, { label: 'Review & Submit' }]
  : [{ label: 'Choose Role' }, { label: 'Your Details' }, { label: 'Confirm' }]))
const STAGE_ORDER = { patient: [1, 2, 3], rnd: [1, 2, 5, 6, 3] }
const stageIndex = computed(() => {
  if ([4, 7].includes(currentStep.value)) return steps.value.length // all done
  const order = STAGE_ORDER[selectedRole.value] || STAGE_ORDER.patient
  return Math.max(0, order.indexOf(currentStep.value))
})

// Line-style SVG icons to match the Figma design (person / stethoscope / shield)
const icons = {
  patient: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg>`,
  rnd: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M6 3v7a4 4 0 0 0 8 0V3"/><path d="M10 3v3M14 3v3"/><circle cx="18" cy="16" r="2.5"/><path d="M18 13.5V11"/></svg>`,
  admin: `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z"/></svg>`
}

const roles = [
  { value: 'patient', icon: icons.patient, label: 'Patient', desc: 'Find an RND' },
  { value: 'rnd', icon: icons.rnd, label: 'RND', desc: 'Offer care' }
]

// Info box text nga mo show the role grid, matching the Figma copy per role
const roleInfoText = {
  patient: "You'll be matched with PRC-verified nutritionist–dietitians based on your health goals and preferences. No verification needed to get started.",
  rnd: "RND accounts require PRC license verification by our admin team — usually within 1–2 business days — before your profile goes live to clients."
}

const roleInfo = computed(() => roleInfoText[selectedRole.value] || '')

async function submitRegistration() {
  errorMessage.value = ''

  if (form.password !== form.confirmPassword) {
    errorMessage.value = 'Passwords do not match.'
    return
  }

  isSubmitting.value = true
  try {
    if (selectedRole.value === 'rnd') {
      await auth.registerRnd({
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
        prc_license_number: form.prcNumber,
        prc_license_image: form.prcLicenseImage,
        date_of_birth: form.dob,
        specialization: form.specialization,
        bio: form.bio.trim(),
        consultation_fee: Number(form.fee).toFixed(2),
        // List fields travel as JSON strings in the multipart form.
        consultation_modes: JSON.stringify(form.modes),
        languages: JSON.stringify(form.languages),
        availability: JSON.stringify(availability.value.map(b => ({ day_of_week: b.day, start_time: b.start, end_time: b.end }))),
        profile_photo: form.profilePhoto || undefined,
        accept_terms: consent.terms,
        data_privacy_consent: consent.data,
      })
    } else {
      await auth.registerClient({
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
        date_of_birth: form.dob,
        sex: genderToSex[form.gender],
        primary_health_concern: form.healthConcern,
        accept_terms: consent.terms,
        data_privacy_consent: consent.data,
      })
    }

    // Registration sends a verification code and leaves the account
    // unverified — login is refused until it's confirmed, so move to the
    // code-entry step instead of logging in right away.
    currentStep.value = 4
  } catch (error) {
    const data = error?.data
    const FIELDS = ['email', 'first_name', 'last_name', 'password', 'date_of_birth', 'prc_license_number', 'prc_license_image', 'specialization',
      'bio', 'languages', 'profile_photo', 'consultation_fee', 'consultation_modes', 'availability', 'accept_terms', 'data_privacy_consent']
    const failed = FIELDS.find(f => data?.[f]?.[0])
    errorMessage.value = (failed && data[failed][0]) || data?.detail || 'Registration failed. Please check your details and try again.'
    // Send them back to the step that has the problem.
    if (selectedRole.value === 'rnd' && failed) {
      if (['bio', 'languages', 'profile_photo'].includes(failed)) currentStep.value = 5
      else if (['consultation_fee', 'consultation_modes', 'availability'].includes(failed)) currentStep.value = 6
      else if (!['accept_terms', 'data_privacy_consent'].includes(failed)) currentStep.value = 2
    }
  } finally {
    isSubmitting.value = false
  }
}

async function submitVerification() {
  errorMessage.value = ''
  isSubmitting.value = true
  try {
    await auth.verifyEmail(form.email, verificationCode.value)
    // RND accounts can't sign in until an admin approves the application.
    if (selectedRole.value === 'rnd') {
      currentStep.value = 7
      return
    }
    const user = await auth.login(form.email, form.password)
    if (user.role === 'rnd') {
      navigateTo('/rnd-dashboard')
    } else {
      navigateTo('/client-dashboard')
    }
  } catch (error) {
    errorMessage.value = error?.data?.detail || 'Invalid or expired code.'
  } finally {
    isSubmitting.value = false
  }
}

async function resendCode() {
  errorMessage.value = ''
  resendMessage.value = ''
  isResending.value = true
  try {
    await auth.resendVerificationCode(form.email)
    resendMessage.value = 'A new code has been sent.'
  } catch {
    errorMessage.value = 'Something went wrong. Please try again.'
  } finally {
    isResending.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600;700&display=swap');

.register-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  font-family: 'Inter', sans-serif;
}

/* LEFT PANEL */
.left-panel {
  background: linear-gradient(160deg, #0b3022 0%, #063c2a 60%, #052a1d 100%);
  position: relative;
  overflow: hidden;
  padding: 48px 64px;
  color: #fff;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle at 32% 28%, rgba(255,255,255,0.16), rgba(255,255,255,0.04) 55%, rgba(255,255,255,0) 75%);
}
.circle-1 { width: 400px; height: 400px; top: -150px; right: -100px; }
.circle-2 { width: 350px; height: 350px; bottom: 100px; right: -150px; }
.circle-3 { width: 450px; height: 450px; bottom: -250px; left: -150px; }

.brand { display: flex; align-items: center; gap: 10px; font-size: 1.2rem; font-weight: 700; position: relative; z-index: 1; }
.logo-img { width: 32px; height: 32px; object-fit: contain; flex-shrink: 0; }
.logo-match { color: #D4A017; }

.left-content { margin-top: 120px; position: relative; z-index: 1; }

.eyebrow { font-size: 0.75rem; letter-spacing: 0.1em; color: #a8c4a8; }

.left-content h1 {
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: clamp(2rem, 4vw, 2.75rem);
  line-height: 1.2;
  margin: 16px 0 56px;
}
.highlight { color: #D4A017; font-style: italic; }

.steps { display: flex; flex-direction: column; }

.step {
  display: flex;
  gap: 16px;
  padding-bottom: 32px;
  position: relative;
}
.step:not(:last-child)::after {
  content: '';
  position: absolute;
  left: 15px;
  top: 32px;
  width: 1px;
  height: calc(100% - 32px);
  background: rgba(255,255,255,0.2);
}

.step-number {
  width: 32px; height: 32px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: rgba(255,255,255,0.1);
  color: #a8c4a8;
  font-size: 0.85rem;
  font-weight: 600;
  flex-shrink: 0;
}
.step.active .step-number { background: #fff; color: #1a3a1a; }
.step.done .step-number { background: #D4A017; color: #1a3a1a; }

.step-text { display: flex; flex-direction: column; }
.step-label { font-size: 0.7rem; letter-spacing: 0.08em; color: #7aaa7a; }
.step-title { font-weight: 600; color: #d8e8d8; }
.step.active .step-title { color: #fff; }
.step.done .step-title { color: #D4A017; }

/* RIGHT PANEL */
.right-panel {
  background: #fff;
  padding: 48px 80px;
  display: flex;
  flex-direction: column;
}

.form-wrap { max-width: 480px; margin: 40px auto 0; width: 100%; }

.form-wrap h2 {
  font-family: 'Playfair Display', serif;
  font-size: 2rem;
  color: #1a3a1a;
  margin-bottom: 8px;
}

.subtitle { color: #8a9a8a; font-size: 0.9rem; margin-bottom: 32px; }

/* ROLE CARDS */
.role-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 20px; }

.role-card {
  border: 1.5px solid #e0e5e0;
  border-radius: 12px;
  padding: 28px 16px;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s ease;
}
.role-card:hover { border-color: #1a3a1a; transform: translateY(-1px); }
.role-card.selected {
  border-color: #1a3a1a;
  background: #f6f9f6;
  box-shadow: 0 0 0 1px #1a3a1a;
}

.role-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6a8a6a;
  margin-bottom: 6px;
  transition: color 0.15s ease;
}
.role-card.selected .role-icon,
.role-card:hover .role-icon { color: #1a3a1a; }

.role-name { font-weight: 700; color: #1a3a1a; }
.role-desc { font-size: 0.78rem; color: #8a9a8a; }

/* ROLE INFO BOX — mirrors the Figma hint box under the role grid */
.role-info-box {
  border-left: 3px solid #1a3a1a;
  background: #f6f5ef;
  border-radius: 6px;
  padding: 14px 18px;
  margin-bottom: 20px;
}
.role-info-box p {
  font-size: 0.85rem;
  line-height: 1.5;
  color: #4a5a4a;
  margin: 0;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* FORM FIELDS */
.details-form { display: flex; flex-direction: column; gap: 18px; margin-bottom: 12px; }
.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #1a3a1a;
  text-transform: uppercase;
}
.field input,
.field select {
  padding: 12px 14px;
  border: 1px solid #dde3dd;
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  background: #fff;
  color: #1a3a1a;
}
.field input:focus,
.field select:focus { outline: none; border-color: #1a3a1a; }

.license-upload {
  display: flex; align-items: center; justify-content: center; min-height: 120px;
  border: 1.5px dashed #b8c8b8; border-radius: 10px; background: #f7f9f7;
  cursor: pointer; overflow: hidden; padding: 10px; text-transform: none; letter-spacing: normal;
}
.license-upload:hover { border-color: #1a3a1a; }
.license-upload.has-file { border-style: solid; background: #fff; }
.license-input { display: none; }
.license-placeholder { display: flex; flex-direction: column; align-items: center; gap: 4px; font-size: 0.8rem; color: #8a9a8a; text-align: center; font-weight: 400; }
.license-placeholder strong { color: #1a3a1a; font-size: 0.86rem; }
.license-preview { max-height: 160px; max-width: 100%; border-radius: 6px; object-fit: contain; }
.license-filename { font-size: 0.75rem; color: #4a5a4a; }
.license-file-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.license-remove {
  border: 1px solid #f0d6d6; background: #fff; color: #c0392b; border-radius: 6px;
  padding: 4px 10px; font-size: 0.74rem; font-weight: 600; cursor: pointer;
}
.license-remove:hover { background: #fbeaea; }
.required-tag {
  font-size: 0.62rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  color: #c0392b; background: #fbeaea; border-radius: 4px; padding: 1px 6px; margin-left: 6px; vertical-align: middle;
}
.license-hint { font-size: 0.72rem; color: #9aaa9a; }
.confirm-license { height: 56px; border-radius: 6px; object-fit: cover; }

.input-icon-wrap { position: relative; display: flex; align-items: center; }
.input-icon-wrap input { flex: 1; padding-left: 38px; padding-right: 60px; }
.input-icon {
  position: absolute; left: 13px; top: 50%; transform: translateY(-50%);
  width: 16px; height: 16px; color: #9aa8a0;
  pointer-events: none;
}
.toggle-visibility {
  position: absolute; right: 12px;
  background: none; border: none; cursor: pointer;
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em;
  color: #6a8a6a;
}

/* CONFIRM STEP */
.confirm-summary {
  border: 1px solid #e0e5e0;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.confirm-row { display: flex; justify-content: space-between; gap: 16px; font-size: 0.9rem; }
.confirm-row span { color: #8a9a8a; flex-shrink: 0; }
.confirm-row strong { color: #1a3a1a; text-transform: capitalize; text-align: right; }
.confirm-row strong.no-capitalize { text-transform: none; }

/* BUTTONS */
.form-nav { display: flex; gap: 12px; margin-top: 4px; }

.btn-primary {
  width: 100%;
  background: #1a3a1a;
  color: #fff;
  border: none;
  padding: 16px;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 4px;
}
.btn-primary:hover:not(:disabled) { background: #14300f; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { display: inline-flex; align-items: center; justify-content: center; gap: 8px; }
.btn-back:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-spinner {
  width: 15px; height: 15px; border-radius: 50%; border: 2px solid rgba(255,255,255,0.35); border-top-color: #fff;
  animation: btn-spin 0.7s linear infinite; flex-shrink: 0;
}
@keyframes btn-spin { to { transform: rotate(360deg); } }
.link-disabled { opacity: 0.45; pointer-events: none; cursor: not-allowed; }

.optional-tag { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; color: #6a7a6a; background: #eef1ee; border-radius: 4px; padding: 1px 6px; margin-left: 6px; vertical-align: middle; }
.photo-row { display: flex; align-items: center; gap: 14px; }
.photo-preview, .photo-placeholder { width: 64px; height: 64px; border-radius: 50%; flex-shrink: 0; }
.photo-preview { object-fit: cover; }
.photo-placeholder { background: #D4A017; color: #1a3a1a; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem; }
.photo-actions { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; }
.field .photo-btn, .photo-btn { position: relative; border: 1px solid #d5dad5; border-radius: 8px; padding: 7px 14px; font-size: 0.8rem; font-weight: 600; color: #1a3a1a; cursor: pointer; background: #fff; text-transform: none; letter-spacing: normal; }
.photo-btn:hover { background: #f7f9f7; }
.bio-input { width: 100%; border: 1px solid #d5dad5; border-radius: 10px; padding: 12px 14px; font-size: 0.88rem; font-family: inherit; line-height: 1.5; resize: vertical; box-sizing: border-box; }
.bio-input:focus { outline: none; border-color: #1a3a1a; }
.bio-input.invalid { border-color: #c0392b; }
.bio-meta { display: flex; justify-content: space-between; gap: 10px; }
.char-count { font-size: 0.72rem; color: #8a9a8a; white-space: nowrap; }
.char-count.short { color: #b8860b; }
.chip-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.field .choice-chip, .choice-chip { display: inline-flex; align-items: center; gap: 6px; border: 1.5px solid #d5dad5; border-radius: 999px; padding: 7px 13px; font-size: 0.8rem; font-weight: 600; color: #4a5a4a; cursor: pointer; background: #fff; text-transform: none; letter-spacing: normal; }
.choice-chip input { accent-color: #1a3a1a; margin: 0; }
.choice-chip.checked { border-color: #1a3a1a; background: #f0f5f0; color: #1a3a1a; }
.fee-wrap { display: flex; align-items: center; gap: 8px; max-width: 280px; }
.fee-wrap input { flex: 1; min-width: 0; }
.fee-prefix { font-weight: 700; color: #1a3a1a; }
.fee-suffix { font-size: 0.8rem; color: #8a9a8a; white-space: nowrap; }
.avail-list { display: flex; flex-direction: column; gap: 8px; margin-top: 6px; }
.avail-day { border: 1px solid #e5e8e5; border-radius: 10px; padding: 10px 12px; background: #fff; }
.avail-day.off { background: #fafbfa; }
.avail-day-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.avail-day-name { font-size: 0.85rem; font-weight: 700; color: #1a3a1a; }
.avail-on { font-size: 0.7rem; font-weight: 700; color: #1f8f5c; }
.avail-add { background: none; border: none; color: #1f8f5c; font-weight: 700; font-size: 0.78rem; cursor: pointer; padding: 2px 0; font-family: inherit; }
.avail-add.small { margin-top: 6px; }
.avail-block { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
.avail-block select { flex: 1; min-width: 0; padding: 8px 10px; border: 1px solid #d5dad5; border-radius: 8px; font-size: 0.82rem; font-family: inherit; background: #fff; }
.avail-to { font-size: 0.78rem; color: #8a9a8a; }
.avail-remove { background: none; border: none; color: #9aaa9a; cursor: pointer; font-size: 0.9rem; padding: 4px 6px; }
.avail-remove:hover { color: #c0392b; }
.confirm-block { flex-direction: column; align-items: flex-start !important; gap: 4px; }
.confirm-hours { margin: 0; padding-left: 18px; font-size: 0.84rem; color: #1a3a1a; font-weight: 600; }
.confirm-bio { margin: 0; font-size: 0.84rem; color: #1a3a1a; line-height: 1.5; white-space: pre-line; }
.confirm-photo { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; }
.review-note { font-size: 0.8rem; color: #6a5a2a; background: #fdf8ec; border-left: 3px solid #D4A017; border-radius: 6px; padding: 10px 14px; margin: 14px 0 0; line-height: 1.5; }
.review-stage { text-align: left; }
.review-icon { width: 56px; height: 56px; border-radius: 50%; background: #e3f3ea; color: #1f8f5c; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
.review-steps { margin: 18px 0 14px; padding-left: 20px; display: flex; flex-direction: column; gap: 10px; font-size: 0.88rem; color: #4a5a4a; line-height: 1.5; }
.review-steps strong { color: #1a3a1a; }
.review-small { font-size: 0.8rem; color: #8a9a8a; margin: 0 0 18px; }
.consent-box { display: flex; flex-direction: column; gap: 12px; margin: 18px 0 6px; padding: 14px 16px; border: 1px solid #e5e8e5; border-radius: 10px; background: #fafbfa; }
.consent-item { display: flex; align-items: flex-start; gap: 10px; font-size: 0.8rem; color: #4a5a4a; line-height: 1.5; cursor: pointer; text-transform: none; letter-spacing: normal; font-weight: 400; }
.consent-item input { margin-top: 3px; width: 16px; height: 16px; accent-color: #1a3a1a; flex-shrink: 0; cursor: pointer; }
.consent-item a { color: #1a3a1a; font-weight: 700; text-decoration: underline; }
.field-error { display: block; font-size: 0.74rem; color: #c0392b; margin-top: 5px; }
input.invalid, select.invalid { border-color: #e2a39b !important; background: #fff8f7; }
.pw-rules { list-style: none; padding: 0; margin: 8px 0 0; display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; }
.pw-rules li { font-size: 0.74rem; color: #8a9a8a; display: flex; align-items: center; gap: 6px; }
.pw-rules li.ok { color: #1f8f5c; font-weight: 600; }
.pw-rule-mark { width: 12px; text-align: center; }
@media (max-width: 480px) { .pw-rules { grid-template-columns: 1fr; } }
.form-nav .btn-primary { flex: 1; margin-top: 0; }

.btn-back {
  flex: 0 0 auto;
  background: #fff;
  border: 1px solid #dde3dd;
  color: #1a3a1a;
  padding: 16px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}
.btn-back:hover { background: #f4f6f4; }

.signin-link { text-align: center; margin-top: 20px; font-size: 0.88rem; color: #8a9a8a; }
.signin-link a { color: #1a3a1a; font-weight: 600; text-decoration: none; }

.form-error {
  background: #fdecec;
  border: 1px solid #f3b8b8;
  color: #a12525;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.85rem;
  margin: 4px 0 0;
}

.form-success {
  background: #e6f4e6;
  border: 1px solid #b8ddb8;
  color: #1a5a2a;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.85rem;
  margin: 4px 0 0;
}

.sent-icon {
  width: 52px; height: 52px; border-radius: 50%; background: #f1f3f1; color: #9aa8a0;
  display: flex; align-items: center; justify-content: center; margin-bottom: 12px;
}

.code-input { letter-spacing: 0.3em; font-size: 1.2rem; text-align: center; font-weight: 700; }

/* Phones/tablets: the green hero (headline + step list) would stack above
   the form and push it off-screen, so it shrinks to a slim branded bar and
   the form comes first — the form already says "Step 2 of 3". */
@media (max-width: 900px) {
  .register-page { grid-template-columns: 1fr; min-height: 100vh; min-height: 100dvh; grid-template-rows: auto 1fr; }
  .left-panel { padding: 16px 20px; min-height: 0; }
  .left-content, .circle { display: none; }
  .right-panel { padding: 24px 20px 32px; }
  .form-wrap { margin-top: 8px; }
  .role-grid { grid-template-columns: 1fr; }
  .field-row { grid-template-columns: 1fr; }
}
</style>