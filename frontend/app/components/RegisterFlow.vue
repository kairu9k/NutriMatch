<template>
  <div class="auth-page register-page">
    <!-- LEFT PANEL: the steps, a real sequence -->
    <aside class="left-panel">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>

      <NuxtLink to="/" class="brand home-link" aria-label="NutriMatch home">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="logo-icon" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </NuxtLink>

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
        <NuxtLink v-if="![4, 7].includes(currentStep)" to="/login" class="back-link top-back"><ArrowLeft :size="14" aria-hidden="true" /> Back to sign in</NuxtLink>
        <!-- STEP 1: CHOOSE ROLE -->
        <div v-if="currentStep === 1">
          <h2>How will you use NutriMatch?</h2>
          <p class="subtitle">Step 1 of {{ steps.length }}.</p>

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

          <button class="btn-primary" :disabled="!selectedRole" @click="currentStep = 2">Continue</button>
        </div>

        <!-- STEP 2: YOUR DETAILS -->
        <div v-else-if="currentStep === 2">
          <h2>{{ selectedRole === 'rnd' ? 'Account and license' : 'Your details' }}</h2>
          <p class="subtitle">Step 2 of {{ steps.length }}. {{ selectedRole === 'rnd' ? 'How you sign in, and your PRC license.' : 'How you sign in, and a little about you.' }}</p>

          <form class="details-form" novalidate @submit.prevent="goToConfirm">
            <div class="field-row">
              <div class="field">
                <label>First name</label>
                <input v-model="form.firstName" type="text" placeholder="e.g. Juan" maxlength="100" :class="{ invalid: firstNameError }" required />
                <span v-if="firstNameError" class="field-error">{{ firstNameError }}</span>
              </div>
              <div class="field">
                <label>Last name</label>
                <input v-model="form.lastName" type="text" placeholder="e.g. Dela Cruz" maxlength="100" :class="{ invalid: lastNameError }" required />
                <span v-if="lastNameError" class="field-error">{{ lastNameError }}</span>
              </div>
            </div>

            <div class="field">
              <label>Email address</label>
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
                  placeholder="Choose a password"
                  minlength="8"
                  required
                />
                <button type="button" class="toggle-visibility" :aria-label="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword">
                  <EyeOff v-if="showPassword" :size="17" aria-hidden="true" /><Eye v-else :size="17" aria-hidden="true" />
                </button>
              </div>
              <ul class="pw-rules" aria-label="Password requirements">
                <li v-for="rule in passwordRules" :key="rule.label" :class="{ ok: rule.ok }">
                  <Check v-if="rule.ok" :size="13" aria-hidden="true" /><Circle v-else :size="11" aria-hidden="true" /> {{ rule.label }}
                </li>
              </ul>
            </div>

            <div class="field">
              <label>Type the password again</label>
              <div class="input-icon-wrap">
                <Lock class="input-icon" aria-hidden="true" />
                <input
                  v-model="form.confirmPassword"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  placeholder="Repeat your password"
                  required
                />
                <button type="button" class="toggle-visibility" :aria-label="showConfirmPassword ? 'Hide password' : 'Show password'" @click="showConfirmPassword = !showConfirmPassword">
                  <EyeOff v-if="showConfirmPassword" :size="17" aria-hidden="true" /><Eye v-else :size="17" aria-hidden="true" />
                </button>
              </div>
              <span v-if="form.confirmPassword && !passwordsMatch" class="field-error">The two passwords don't match.</span>
            </div>

            <template v-if="selectedRole === 'patient'">
              <div class="field-row">
                <div class="field">
                  <label>Date of birth</label>
                  <input v-model="form.dob" type="date" :max="latestBirthDate" min="1900-01-01" :class="{ invalid: dobError }" required />
                  <span v-if="dobError" class="field-error">{{ dobError }}</span>
                </div>
                <div class="field">
                  <label>Gender</label>
                  <select class="nm-select block" v-model="form.gender" required>
                    <option disabled value="">Select</option>
                    <option>Female</option>
                    <option>Male</option>
                    <option>Prefer not to say</option>
                  </select>
                </div>
              </div>

              <div class="field">
                <label>Main health concern</label>
                <select class="nm-select block" v-model="form.healthConcern" required>
                  <option disabled value="">Select</option>
                  <option>Hypertension</option>
                  <option>Type 2 Diabetes</option>
                  <option>Obesity management</option>
                  <option>Renal nutrition</option>
                  <option>Other</option>
                </select>
              </div>
            </template>

            <template v-else-if="selectedRole === 'rnd'">
              <div class="field">
                <label for="reg-phone">Mobile number <span class="required-tag">Required</span></label>
                <PhoneInput id="reg-phone" v-model="form.phone" label="mobile number" rnd />
                <span class="license-hint">A Philippine mobile number, so our admin team can reach you. Not shown to clients.</span>
              </div>
              <div class="field">
                <label>Date of birth</label>
                <input v-model="form.dob" type="date" :max="latestBirthDate" min="1900-01-01" :class="{ invalid: dobError }" required />
                <span v-if="dobError" class="field-error">{{ dobError }}</span>
              </div>
              <div class="field">
                <label>PRC license number <span class="required-tag">Required</span></label>
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
                <label>PRC license photo <span class="required-tag">Required</span></label>
                <label class="license-upload" :class="{ 'has-file': licensePreview }">
                  <input ref="licenseInput" type="file" accept="image/jpeg,image/png,image/webp" class="license-input" @change="onLicenseSelected" />
                  <img v-if="licensePreview" :src="licensePreview" alt="PRC license preview" class="license-preview" />
                  <span v-else class="license-placeholder">
                    <strong>Upload a clear photo of your PRC ID</strong>
                    JPG, PNG or WEBP, up to 5 MB
                  </span>
                </label>
                <div v-if="form.prcLicenseImage" class="license-file-row">
                  <span class="license-filename">{{ form.prcLicenseImage.name }}. Click the photo to change it.</span>
                  <button type="button" class="license-remove" @click="removeLicense">Remove</button>
                </div>
                <span class="license-hint">Only our admin team sees this photo, to verify your license.</span>
              </div>
              <div class="field">
                <label>Specialization <span class="required-tag">Required</span></label>
                <select class="nm-select block" v-model="form.specialization" required>
                  <option disabled value="">Select</option>
                  <option v-for="sp in SPECIALIZATIONS" :key="sp" :value="sp">{{ sp }}</option>
                </select>
              </div>
            </template>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

            <div class="form-nav">
              <button type="submit" class="btn-primary" :disabled="!detailsValid || checkingEmail">{{ checkingEmail ? 'Checking…' : 'Continue' }}</button>
            </div>
          </form>
        </div>

        <!-- RND STEP 3: PROFESSIONAL PROFILE (stage 5) -->
        <div v-else-if="currentStep === 5">
          <h2>Your profile</h2>
          <p class="subtitle">Step 3 of {{ steps.length }}. What clients see before they book you.</p>

          <form class="details-form" novalidate @submit.prevent="goToConsultation">
            <div class="field">
              <label>Profile photo <span class="optional-tag">Optional</span></label>
              <div class="photo-row">
                <img v-if="photoPreview" :src="photoPreview" alt="Profile photo preview" class="photo-preview" />
                <div v-else class="photo-placeholder">{{ (form.firstName[0] || '') + (form.lastName[0] || '') }}</div>
                <div class="photo-actions">
                  <label class="photo-btn">
                    <input ref="photoInput" type="file" accept="image/jpeg,image/png,image/webp" class="license-input" @change="onPhotoSelected" />
                    {{ form.profilePhoto ? 'Change photo' : 'Upload photo' }}
                  </label>
                  <button v-if="form.profilePhoto" type="button" class="license-remove" @click="removePhoto">Remove</button>
                  <span class="license-hint">A clear, friendly headshot. JPG, PNG or WEBP, up to 2 MB.</span>
                </div>
              </div>
            </div>

            <div class="field">
              <label>Bio <span class="required-tag">Required</span></label>
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
              <label>Languages you consult in <span class="required-tag">Required</span></label>
              <div class="chip-grid">
                <label v-for="lang in LANGUAGES" :key="lang.code" class="choice-chip" :class="{ checked: form.languages.includes(lang.code) }">
                  <input v-model="form.languages" type="checkbox" :value="lang.code" />
                  {{ lang.name }}
                </label>
              </div>
            </div>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
            <div class="form-nav">
              <button type="submit" class="btn-primary" :disabled="!profileValid">Continue</button>
            </div>
          </form>
        </div>

        <!-- RND STEP 4: CONSULTATION SETUP (stage 6) -->
        <div v-else-if="currentStep === 6">
          <h2>Consultations</h2>
          <p class="subtitle">Step 4 of {{ steps.length }}. Your fee and how you consult.</p>

          <form class="details-form" novalidate @submit.prevent="goToConfirm">
            <div class="field">
              <label>Consultation fee <span class="required-tag">Required</span></label>
              <div class="fee-wrap">
                <span class="fee-prefix">₱</span>
                <input v-model.number="form.fee" type="number" inputmode="numeric" min="100" step="50" placeholder="e.g. 800" :class="{ invalid: feeError }" />
                <span class="fee-suffix">per session</span>
              </div>
              <span v-if="feeError" class="field-error">{{ feeError }}</span>
              <span v-else class="license-hint">At least ₱100. Clients pay this before each consultation.</span>
            </div>

            <div class="field">
              <label>Consultation formats <span class="required-tag">Required</span></label>
              <div class="chip-grid">
                <label v-for="(label, key) in MODE_LABELS" :key="key" class="choice-chip" :class="{ checked: form.modes.includes(key) }">
                  <input v-model="form.modes" type="checkbox" :value="key" />
                  {{ label }}
                </label>
              </div>
            </div>

            <div v-if="form.modes.includes('in_person')" class="field">
              <label for="reg-clinic">Clinic address <span class="required-tag">Required</span></label>
              <input id="reg-clinic" v-model="form.clinicAddress" type="text" maxlength="255"
                placeholder="e.g. 2F Bajada Medical Bldg, J.P. Laurel Ave, Bajada, Davao City" />
              <span v-if="clinicAddressError" class="field-error">{{ clinicAddressError }}</span>
              <span v-else class="license-hint">Where clients go for in-person consultations. It's shown on your profile.</span>
            </div>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
            <div class="form-nav">
              <button type="submit" class="btn-primary" :disabled="!consultationValid">Continue</button>
            </div>
          </form>
        </div>

        <!-- RND: APPLICATION UNDER REVIEW (stage 7, after verifying the email) -->
        <div v-else-if="currentStep === 7" class="review-stage">
          <div class="review-icon"><ClipboardCheck :size="28" aria-hidden="true" /></div>
          <h2>Application sent</h2>
          <p class="subtitle">
            Thank you, {{ form.firstName }}. Your email is confirmed and your application is with our admin team.
          </p>
          <ol class="review-steps">
            <li><strong>We review your PRC license and profile.</strong> It usually takes 1 to 2 business days.</li>
            <li><strong>We email you at {{ form.email }}</strong> once your account is approved, or if we need anything fixed.</li>
            <li><strong>Then you can sign in.</strong> Add your weekly hours in Profile Settings and clients can find and book you.</li>
          </ol>
          <p class="review-small">You can't sign in until your application is approved.</p>
          <button type="button" class="btn-primary" @click="navigateTo('/')">Back to home</button>
        </div>

        <!-- STEP 3: CONFIRM -->
        <div v-else-if="currentStep === 3">
          <h2>{{ selectedRole === 'rnd' ? 'Check your application' : 'Check your details' }}</h2>
          <p class="subtitle">Step {{ steps.length }} of {{ steps.length }}. Make sure everything is right before you send it.</p>

          <div class="confirm-summary">
            <div class="confirm-row"><span>Signing up as</span><strong>{{ selectedRole === 'rnd' ? 'RND' : 'Client' }}</strong></div>
            <div class="confirm-row"><span>Name</span><strong>{{ form.firstName }} {{ form.lastName }}</strong></div>
            <div class="confirm-row"><span>Email</span><strong class="no-capitalize">{{ form.email }}</strong></div>
            <template v-if="selectedRole === 'patient'">
              <div class="confirm-row"><span>Date of birth</span><strong>{{ form.dob }}</strong></div>
              <div class="confirm-row"><span>Gender</span><strong>{{ form.gender }}</strong></div>
              <div class="confirm-row"><span>Main health concern</span><strong>{{ form.healthConcern }}</strong></div>
            </template>
            <template v-else-if="selectedRole === 'rnd'">
              <div class="confirm-row"><span>Date of birth</span><strong>{{ form.dob }}</strong></div>
              <div class="confirm-row"><span>Mobile number</span><strong>{{ formatPhone(form.phone) }}</strong></div>
              <div class="confirm-row"><span>PRC license number</span><strong>{{ form.prcNumber }}</strong></div>
              <div class="confirm-row"><span>PRC license photo</span><img v-if="licensePreview" :src="licensePreview" alt="PRC license" class="confirm-license" /></div>
              <div class="confirm-row"><span>Specialization</span><strong>{{ form.specialization || '—' }}</strong></div>
              <div class="confirm-row"><span>Languages</span><strong>{{ form.languages.map(languageName).join(', ') }}</strong></div>
              <div class="confirm-row"><span>Consultation fee</span><strong>₱{{ Number(form.fee).toLocaleString() }} per session</strong></div>
              <div class="confirm-row"><span>Formats</span><strong>{{ form.modes.map(m => MODE_LABELS[m]).join(', ') }}</strong></div>
              <div v-if="form.modes.includes('in_person')" class="confirm-row"><span>Clinic address</span><strong>{{ form.clinicAddress.trim() }}</strong></div>
              <div class="confirm-row confirm-block"><span>Bio</span><p class="confirm-bio">{{ form.bio.trim() }}</p></div>
              <div v-if="photoPreview" class="confirm-row"><span>Profile photo</span><img :src="photoPreview" alt="Profile photo" class="confirm-photo" /></div>
            </template>
          </div>
          <p v-if="selectedRole === 'rnd'" class="review-note">
            Our admin team reviews your PRC license and profile before your account is activated. It usually takes 1 to 2 business days,
            and you can sign in once it's approved.
          </p>

          <!-- Informed consent (RA 10173) — two boxes the person ticks
               themselves (consent must be their own act, never pre-ticked), and
               the health-data consent stays separate from the Terms because
               health information is sensitive personal information. Both stay
               locked until the Terms and the Privacy Policy were opened.
               Recorded on the account and in the audit log by the API. -->
          <div class="consent-box">
            <p v-if="!termsViewed" class="consent-lock-note">
              Open the <a href="/terms" @click.prevent="openLegal('terms')">Terms and Conditions</a> and the
              <a href="/privacy-policy" @click.prevent="openLegal('privacy')">Privacy Policy</a> first to tick these boxes.
            </p>
            <label class="consent-item" :class="{ 'is-locked': !termsViewed }">
              <input v-model="consent.terms" type="checkbox" :disabled="isSubmitting || !termsViewed" />
              <span>
                I have read and agree to the
                <a href="/terms" @click.prevent="openLegal('terms')">Terms and Conditions</a> and
                <a href="/privacy-policy" @click.prevent="openLegal('privacy')">Privacy Policy</a>.
              </span>
            </label>
            <label class="consent-item" :class="{ 'is-locked': !termsViewed }">
              <input v-model="consent.data" type="checkbox" :disabled="isSubmitting || !termsViewed" />
              <span>
                I consent to NutriMatch collecting and processing my personal and health information
                {{ selectedRole === 'rnd' ? '(including my PRC license photo, for verification)' : '(including my screening and nutrition records)' }}
                to provide nutrition care services, as described in the Privacy Policy, in accordance with
                Republic Act No. 10173 (Data Privacy Act of 2012).
              </span>
            </label>
          </div>

          <!-- Terms / Privacy pop-up: opens by itself on this step and when a link
               is clicked. Showing both tabs unlocks and ticks the checkbox. -->
          <div v-if="legalOpen" class="legal-overlay" @click.self="legalOpen = false">
            <div class="legal-modal" role="dialog" aria-modal="true" aria-label="Terms and Conditions and Privacy Policy">
              <div class="legal-head">
                <div class="legal-tabs">
                  <button type="button" class="legal-tab" :class="{ active: legalTab === 'terms' }" @click="openLegal('terms')">Terms and Conditions</button>
                  <button type="button" class="legal-tab" :class="{ active: legalTab === 'privacy' }" @click="openLegal('privacy')">Privacy Policy</button>
                </div>
                <button type="button" class="legal-close" aria-label="Close" @click="legalOpen = false"><X :size="18" aria-hidden="true" /></button>
              </div>
              <iframe class="legal-frame" :class="{ ready: legalReady }" :src="legalTab === 'terms' ? '/terms' : '/privacy-policy'" :title="legalTab === 'terms' ? 'Terms and Conditions' : 'Privacy Policy'" @load="trimLegalFrame"></iframe>
              <div class="legal-foot">
                <!-- Terms first, then Next leads to the Privacy Policy, which closes. -->
                <template v-if="legalTab === 'terms'">
                  <p class="legal-hint">Read the Terms, then the Privacy Policy.</p>
                  <button type="button" class="btn-primary legal-done" @click="openLegal('privacy')">Next: Privacy Policy</button>
                </template>
                <template v-else>
                  <p class="legal-hint">{{ termsViewed ? 'You can now tick the consent boxes.' : 'Open the Terms tab too to continue.' }}</p>
                  <button type="button" class="btn-primary legal-done" @click="legalOpen = false">{{ termsViewed ? 'Done' : 'Close' }}</button>
                </template>
              </div>
            </div>
          </div>

          <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

          <div class="form-nav">
            <button class="btn-primary" :disabled="isSubmitting || !consentGiven" :aria-busy="isSubmitting" @click="submitRegistration">
              <span v-if="isSubmitting" class="btn-spinner" aria-hidden="true"></span>
              {{ isSubmitting ? (selectedRole === 'rnd' ? 'Submitting…' : 'Creating account…') : (selectedRole === 'rnd' ? 'Submit application' : 'Create account') }}
            </button>
          </div>
        </div>

        <!-- STEP 4: VERIFY EMAIL -->
        <div v-else-if="currentStep === 4">
          <div class="sent-icon"><Mail :size="26" aria-hidden="true" /></div>
          <h2>Check your inbox</h2>
          <p class="subtitle">
            We sent a 6-digit code to <strong>{{ form.email }}</strong>. Enter it to confirm your email.
          </p>

          <form class="details-form" @submit.prevent="submitVerification">
            <div class="field">
              <label>Code</label>
              <input v-model="verificationCode" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="123456" class="code-input" required />
            </div>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
            <p v-if="resendMessage" class="form-success">{{ resendMessage }}</p>

            <button type="submit" class="btn-primary" :disabled="isSubmitting || isResending" :aria-busy="isSubmitting">
              <span v-if="isSubmitting" class="btn-spinner" aria-hidden="true"></span>
              {{ isSubmitting ? 'Verifying…' : 'Confirm email' }}
            </button>
          </form>

          <p class="signin-link">
            Didn't get it?
            <span v-if="resendIn > 0" class="resend-wait">Resend code in {{ resendIn }}s</span>
            <a v-else href="#" :class="{ 'link-disabled': isSubmitting || isResending }" :aria-disabled="isSubmitting || isResending" @click.prevent="!isSubmitting && !isResending && resendCode()">{{ isResending ? 'Sending…' : 'Resend code' }}</a>,
            or <a href="#" :class="{ 'link-disabled': isSubmitting }" :aria-disabled="isSubmitting" @click.prevent="!isSubmitting && changeEmail()">change your email</a>.
          </p>
        </div>

        <p v-if="![4, 7].includes(currentStep)" class="signin-link">
          Already have an account? <a href="#" :class="{ 'link-disabled': isSubmitting }" :aria-disabled="isSubmitting" @click.prevent="!isSubmitting && navigateTo('/login')">Sign in</a>
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { phIso } from '~/utils/phTime'
import { ArrowLeft, Check, Circle, ClipboardCheck, Eye, EyeOff, Lock, Mail, User, X } from 'lucide-vue-next'
const auth = useAuthStore()

// Landing-page buttons link to /register?role=client|rnd: open that role's
// form directly (Back still returns to the role choice).
const ROLE_FROM_QUERY = { client: 'patient', patient: 'patient', rnd: 'rnd' }
const presetRole = ROLE_FROM_QUERY[useRoute().query.role] || ''
const currentStep = ref(presetRole ? 2 : 1)
const selectedRole = ref(presetRole)
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
  phone: '',
  specialization: '',
  // RND application (onboarding): reviewed by the admin before sign-in.
  profilePhoto: null,
  bio: '',
  languages: [],
  fee: '',
  modes: ['video'],
  clinicAddress: '',
})

// Both consent boxes on the Confirm step must be ticked by the person (RA
// 10173: consent is their own act — never ticked for them). They stay locked
// until both the Terms and the Privacy Policy were opened.
const consent = reactive({ terms: false, data: false })
const viewed = reactive({ terms: false, privacy: false })
const termsViewed = computed(() => viewed.terms && viewed.privacy)
// Terms / Privacy pop-up: opens on its own when the Confirm step shows, and
// when either link is clicked. Opening a tab counts as viewing it.
const legalOpen = ref(false)
const legalTab = ref('terms')
// The page stays hidden until the site navbar/footer inside it were removed,
// so Login / Get started never flash on screen.
const legalReady = ref(false)
function openLegal(tab) {
  if (!legalOpen.value || legalTab.value !== tab) legalReady.value = false
  legalTab.value = tab
  viewed[tab] = true
  legalOpen.value = true
}
watch(currentStep, v => { if (v === 3 && !consent.terms) openLegal('terms') })
// The /terms and /privacy-policy pages come with the site navbar (Login / Get
// started) and footer; hide them so the pop-up only shows the document.
function trimLegalFrame(e) {
  try {
    const doc = e.target.contentDocument
    if (!doc?.head) return
    const style = doc.createElement('style')
    style.textContent = 'nav, footer, header:has(nav), [class*="navbar" i] { display: none !important; } html, body { margin-top: 0 !important; }'
    doc.head.appendChild(style)
    // Give the page a moment to render its navbar so the rule above hides it
    // before the pop-up shows anything.
    setTimeout(() => { legalReady.value = true }, 250)
  } catch {
    legalReady.value = true // not readable: show the page as it is
  }
}
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
  return NAME_RE.test(v) ? '' : 'Letters only, no numbers or symbols.'
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
// Set by the "already exists" check on Continue; editing the email clears it.
const takenEmail = ref('')
const emailError = computed(() => {
  if (form.email && !EMAIL_RE.test(form.email)) return 'Enter a valid email address (e.g. juan@example.com).'
  if (takenEmail.value && form.email.toLowerCase() === takenEmail.value) return 'An account with this email already exists.'
  return ''
})
const checkingEmail = ref(false)
watch(() => form.email, v => {
  if (takenEmail.value && v.toLowerCase() !== takenEmail.value && errorMessage.value.includes('already exists')) errorMessage.value = ''
})

const passwordRules = computed(() => [
  { label: 'At least 8 characters', ok: form.password.length >= 8 },
  { label: 'One uppercase letter', ok: /[A-Z]/.test(form.password) },
  { label: 'One lowercase letter', ok: /[a-z]/.test(form.password) },
  { label: 'One number', ok: /\d/.test(form.password) },
  { label: 'One special character (e.g. ! @ # $)', ok: /[^A-Za-z0-9\s]/.test(form.password) },
])
const passwordsMatch = computed(() => form.password === form.confirmPassword)

// Philippine date on the server's clock.
const todayIso = phIso()
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
      && /^\d{7}$/.test(form.prcNumber) && form.specialization && !rndPhoneError(form.phone))
  }
  return false
})

async function goToConfirm() {
  if (!detailsValid.value) {
    errorMessage.value = 'Please fix the highlighted fields first.'
    return
  }
  // Same rule the API applies at submit (a verified account owns the email),
  // checked here so the form doesn't move on to Confirm with a taken email.
  if (currentStep.value === 2) {
    checkingEmail.value = true
    try {
      const res = await auth.checkRegistrationEmail(form.email)
      if (!res.available) {
        takenEmail.value = form.email.toLowerCase()
        errorMessage.value = res.detail || 'An account with this email already exists.'
        return
      }
    } catch {
      // Can't reach the check — carry on; registration itself still refuses a taken email.
    } finally {
      checkingEmail.value = false
    }
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
const MODE_LABELS = { video: 'Video call', in_person: 'In-person' }
const MIN_FEE = 100
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
// Only asked for (and required) when they offer in-person consultations.
const clinicAddressError = computed(() => {
  if (!form.modes.includes('in_person')) return ''
  const v = form.clinicAddress.trim()
  if (!v) return ''
  return v.length < 10 ? 'Enter the full address: building, street, barangay and city.' : ''
})
const clinicAddressOk = computed(() => !form.modes.includes('in_person') || (form.clinicAddress.trim().length >= 10))
const consultationValid = computed(() =>
  Number(form.fee) >= MIN_FEE && !feeError.value && form.modes.length > 0 && clinicAddressOk.value
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
  ? [{ label: 'Choose a role' }, { label: 'Account and license' }, { label: 'Profile' }, { label: 'Consultations' }, { label: 'Check and send' }]
  : [{ label: 'Choose a role' }, { label: 'Your details' }, { label: 'Check and create' }]))
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
  { value: 'patient', icon: icons.patient, label: 'I need nutrition care', desc: 'Sign up as a client' },
  { value: 'rnd', icon: icons.rnd, label: "I'm an RND", desc: 'Apply to consult' }
]

// The note under the role cards, one per role
const roleInfoText = {
  patient: "Find a PRC-verified nutritionist-dietitian who fits your health goals, and book them directly. No verification needed to get started.",
  rnd: "Our admin team checks your PRC license before your profile goes live to clients. It usually takes 1 to 2 business days."
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
        phone: form.phone,
        date_of_birth: form.dob,
        specialization: form.specialization,
        bio: form.bio.trim(),
        consultation_fee: Number(form.fee).toFixed(2),
        // List fields travel as JSON strings in the multipart form.
        consultation_modes: JSON.stringify(form.modes),
        clinic_address: form.modes.includes('in_person') ? form.clinicAddress.trim() : undefined,
        languages: JSON.stringify(form.languages),
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
    startResendTimer()
  } catch (error) {
    const data = error?.data
    const FIELDS = ['email', 'first_name', 'last_name', 'password', 'phone', 'date_of_birth', 'prc_license_number', 'prc_license_image', 'specialization',
      'bio', 'languages', 'profile_photo', 'consultation_fee', 'consultation_modes', 'clinic_address', 'accept_terms', 'data_privacy_consent']
    const failed = FIELDS.find(f => data?.[f]?.[0])
    errorMessage.value = (failed && data[failed][0]) || data?.detail || 'Registration failed. Please check your details and try again.'
    // Send them back to the step that has the problem.
    if (selectedRole.value === 'rnd' && failed) {
      if (['bio', 'languages', 'profile_photo'].includes(failed)) currentStep.value = 5
      else if (['consultation_fee', 'consultation_modes', 'clinic_address'].includes(failed)) currentStep.value = 6
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

// A new code can be asked for 30 seconds after the last one was sent
// (the API also allows at most 5 a minute).
const RESEND_SECONDS = 30
const resendIn = ref(0)
let resendTimer = null
function startResendTimer() {
  clearInterval(resendTimer)
  resendIn.value = RESEND_SECONDS
  resendTimer = setInterval(() => {
    resendIn.value -= 1
    if (resendIn.value <= 0) clearInterval(resendTimer)
  }, 1000)
}
onBeforeUnmount(() => clearInterval(resendTimer))

async function resendCode() {
  if (resendIn.value > 0) return
  errorMessage.value = ''
  resendMessage.value = ''
  isResending.value = true
  try {
    await auth.resendVerificationCode(form.email)
    resendMessage.value = `A new code is on its way to ${form.email}.`
    startResendTimer()
  } catch (error) {
    errorMessage.value = (error?.response?.status ?? error?.status) === 429
      ? 'Too many codes asked for. Wait a minute, then try again.'
      : "We couldn't send a new code. Check your connection and try again."
  } finally {
    isResending.value = false
  }
}

// Typed the wrong email: back to the details with everything still filled
// in. Sending the form again makes a new account for the right address; the
// unconfirmed one is cleaned up if anyone registers that address later.
function changeEmail() {
  clearInterval(resendTimer)
  resendIn.value = 0
  verificationCode.value = ''
  errorMessage.value = ''
  resendMessage.value = ''
  currentStep.value = 2
}
</script>

<style scoped src="~/assets/css/auth.css"></style>

<style scoped>
/* the original background picture: light circles on the dark green */
.left-panel { background: linear-gradient(160deg, #0b3022 0%, #063c2a 60%, #052a1d 100%); }
.circle { background: radial-gradient(circle at 32% 28%, rgba(255,255,255,0.16), rgba(255,255,255,0.04) 55%, rgba(255,255,255,0) 75%); }
.circle-1 { width: 400px; height: 400px; top: -150px; right: -100px; }
.circle-2 { width: 350px; height: 350px; bottom: 100px; right: -150px; }
.circle-3 { width: 450px; height: 450px; bottom: -250px; left: -150px; }

/* the original left panel of sign-up */
.left-panel { padding: 48px 64px; display: block; }
.left-content { margin-top: 120px; }
.eyebrow { letter-spacing: 0.1em; font-weight: 400; }
.left-content h1 { font-style: normal; font-weight: 700; font-size: clamp(2rem, 4vw, 2.75rem); letter-spacing: normal; line-height: 1.2; margin: 16px 0 56px; }
.highlight { font-style: italic; }
.step-text { display: flex; flex-direction: column; }
.step-label { font-size: 0.7rem; letter-spacing: 0.08em; color: #7aaa7a; }
@media (max-width: 900px) { .left-panel { padding: 16px 20px; } }
.step.done .step-title { color: #D4A017; }

/* LEFT: the steps (original) */
.steps { display: flex; flex-direction: column; }
.step { display: flex; gap: 16px; padding-bottom: 32px; position: relative; }
.step:not(:last-child)::after { content: ''; position: absolute; left: 15px; top: 32px; width: 1px; height: calc(100% - 32px); background: rgba(255, 255, 255, 0.2); }
.step-number {
  width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  background: rgba(255, 255, 255, 0.1); color: #a8c4a8; font-size: 0.85rem; font-weight: 600;
}
.step.active .step-number { background: #fff; color: #1a3a1a; }
.step.done .step-number { background: #D4A017; color: #1a3a1a; }
.step-title { font-weight: 600; color: #d8e8d8; }
.step.active .step-title { color: #fff; }

/* ROLE CARDS */
.role-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
.role-card {
  display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 24px 16px; text-align: center;
  border: 1.5px solid #d9e3dc; border-radius: 12px; background: #fff; cursor: pointer; font-family: inherit; color: #1a3a1a;
}
.role-card:hover { border-color: #1f8f5c; }
.role-card.selected { border-color: #0a4a37; background: #f2f9f4; box-shadow: 0 0 0 1px #0a4a37; }
.role-card:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.role-icon { display: flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: 50%; background: #e3efe7; color: #0a4a37; margin-bottom: 6px; }
.role-name { font-weight: 700; font-size: 0.95rem; }
.role-desc { font-size: 0.8rem; color: #6a7a6a; }
/* plain information: grey */
.role-info-box { background: #f4f6f4; border: 1px solid #d9e3dc; border-radius: 10px; padding: 12px 14px; margin-bottom: 18px; }
.role-info-box p { font-size: 0.85rem; line-height: 1.5; color: #4a5a4a; margin: 0; }
.fade-slide-enter-active, .fade-slide-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity: 0; transform: translateY(-6px); }
@media (prefers-reduced-motion: reduce) { .fade-slide-enter-active, .fade-slide-leave-active { transition: none; } }

/* FORM */
.details-form { display: flex; flex-direction: column; gap: 18px; margin-bottom: 12px; }
.field-row { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 18px; }
.field select { min-height: 46px; font-size: 0.95rem; }
.required-tag, .optional-tag { font-size: 0.78rem; font-weight: 500; margin-left: 6px; }
.required-tag { color: #a12525; }
.optional-tag { color: #6a7a6a; }
.field-error { display: block; font-size: 0.78rem; color: #c0392b; }
.field input.invalid, .field select.invalid, .bio-input.invalid { border-color: #e2a39b; background: #fff8f7; }
.license-hint { font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; }

.license-upload {
  display: flex; align-items: center; justify-content: center; min-height: 120px; padding: 10px; overflow: hidden; cursor: pointer;
  border: 1.5px dashed #3f9a6b; border-radius: 10px; background: #fff;
}
.license-upload:hover { background: #f7faf8; }
.license-upload.has-file { border: 1px solid #d9e3dc; }
.license-input { display: none; }
.license-placeholder { display: flex; flex-direction: column; align-items: center; gap: 4px; font-size: 0.8rem; color: #6a7a6a; text-align: center; }
.license-placeholder strong { color: #1a3a1a; font-size: 0.86rem; }
.license-preview { max-height: 160px; max-width: 100%; border-radius: 6px; object-fit: contain; }
.license-file-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.license-filename { font-size: 0.78rem; color: #4a5a4a; overflow-wrap: anywhere; }
.license-remove {
  display: inline-flex; align-items: center; min-height: 32px; padding: 0 12px; border: none; border-radius: 8px;
  background: #c0392b; color: #fff; font-family: inherit; font-size: 0.78rem; font-weight: 600; cursor: pointer;
}
.license-remove:hover { background: #a93226; }

.photo-row { display: flex; align-items: center; gap: 14px; }
.photo-preview, .photo-placeholder { width: 64px; height: 64px; border-radius: 50%; flex-shrink: 0; }
.photo-preview { object-fit: cover; }
.photo-placeholder { background: #0a4a37; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem; }
.photo-actions { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; }
.photo-btn {
  position: relative; display: inline-flex; align-items: center; min-height: 32px; padding: 0 12px; border-radius: 8px;
  background: #e3efe7; color: #0a4a37; font-size: 0.78rem; font-weight: 600; cursor: pointer;
}
.photo-btn:hover { background: #d3e7da; }
.bio-input {
  width: 100%; box-sizing: border-box; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 14px;
  font-size: 0.9rem; font-family: inherit; line-height: 1.5; color: #1a3a1a; resize: vertical;
}
.bio-input:focus { outline: none; border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.15); }
.bio-meta { display: flex; justify-content: space-between; gap: 10px; }
.char-count { font-size: 0.76rem; color: #6a7a6a; white-space: nowrap; font-variant-numeric: tabular-nums; }
.char-count.short { color: #a12525; }

/* toggle chips: languages, formats */
.chip-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.choice-chip {
  display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 0 13px; border: 1.5px solid #d9e3dc; border-radius: 999px;
  background: #fff; color: #4a5a4a; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.choice-chip input { accent-color: #0a4a37; margin: 0; }
.choice-chip.checked { border-color: #0a4a37; background: #e3efe7; color: #0a4a37; }
.fee-wrap { display: flex; align-items: center; gap: 8px; max-width: 280px; }
.fee-wrap input { flex: 1; min-width: 0; }
.fee-prefix { font-weight: 700; color: #1a3a1a; }
.fee-suffix { font-size: 0.82rem; color: #6a7a6a; white-space: nowrap; }

/* CHECK STEP: one divided summary */
.confirm-summary { border: 1px solid #d9e3dc; border-radius: 12px; margin-bottom: 20px; overflow: hidden; }
.confirm-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 11px 16px; font-size: 0.88rem; }
.confirm-row + .confirm-row { border-top: 1px solid #d9e3dc; }
.confirm-row span { color: #6a7a6a; flex-shrink: 0; }
.confirm-block { flex-direction: column; align-items: flex-start; gap: 4px; }
.confirm-bio { margin: 0; font-size: 0.86rem; color: #1a3a1a; line-height: 1.5; white-space: pre-line; overflow-wrap: anywhere; }
.confirm-license { height: 56px; border-radius: 6px; object-fit: cover; }
.confirm-photo { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; }
.review-note { font-size: 0.84rem; color: #4a5a4a; background: #f4f6f4; border: 1px solid #d9e3dc; border-radius: 10px; padding: 10px 14px; margin: 0 0 14px; line-height: 1.5; }

.review-stage { text-align: left; }
.review-icon { width: 56px; height: 56px; border-radius: 50%; background: #e3efe7; color: #0a4a37; display: flex; align-items: center; justify-content: center; margin-bottom: 16px; }
.review-steps { margin: 18px 0 14px; padding-left: 20px; display: flex; flex-direction: column; gap: 10px; font-size: 0.9rem; color: #4a5a4a; line-height: 1.5; }
.review-steps strong { color: #1a3a1a; }
.review-small { font-size: 0.84rem; color: #6a7a6a; margin: 0 0 18px; }

/* consent (RA 10173) */
.consent-box { display: flex; flex-direction: column; gap: 12px; margin: 0 0 6px; padding: 14px 16px; border: 1px solid #d9e3dc; border-radius: 12px; background: #fff; }
.consent-item { display: flex; align-items: flex-start; gap: 10px; font-size: 0.84rem; color: #4a5a4a; line-height: 1.5; cursor: pointer; }
.consent-item input { margin-top: 3px; width: 16px; height: 16px; accent-color: #0a4a37; flex-shrink: 0; cursor: pointer; }
.consent-item a, .consent-lock-note a { color: #0a4a37; font-weight: 600; text-decoration: underline; }
.consent-item.is-locked { cursor: default; }
.consent-item input:disabled { opacity: 0.5; cursor: not-allowed; }
/* something still to do: dashed green */
.consent-lock-note { margin: 0; font-size: 0.82rem; color: #1f4a30; border: 1.5px dashed #3f9a6b; border-radius: 8px; padding: 8px 12px; line-height: 1.5; }

/* Terms / Privacy pop-up, same frame as every pop-up */
.legal-overlay { position: fixed; inset: 0; background: rgba(20, 30, 20, 0.55); display: flex; align-items: center; justify-content: center; padding: 20px; z-index: 1000; }
.legal-modal {
  width: 100%; max-width: 1000px; height: 92vh; height: 92dvh; display: flex; flex-direction: column; overflow: hidden;
  background: #fff; border-radius: 18px; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
}
.legal-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 20px; border-bottom: 1px solid #d9e3dc; }
.legal-tabs { display: flex; flex-wrap: wrap; gap: 6px; }
.legal-tab {
  display: inline-flex; align-items: center; min-height: 36px; padding: 0 14px; border: none; border-radius: 8px;
  background: #e3efe7; color: #0a4a37; font-size: 0.82rem; font-weight: 600; font-family: inherit; cursor: pointer;
}
.legal-tab:hover { background: #d3e7da; }
.legal-tab.active { background: #0a4a37; color: #fff; }
.legal-close { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 8px; background: none; color: #6a7a6a; cursor: pointer; }
.legal-close:hover { background: #f2f5f2; color: #1a3a1a; }
.legal-frame { flex: 1; width: 100%; border: none; background: #fff; opacity: 0; transition: opacity 0.15s ease; }
.legal-frame.ready { opacity: 1; }
.legal-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; padding: 14px 20px; border-top: 1px solid #d9e3dc; background: #f7faf8; }
.legal-hint { margin: 0; font-size: 0.82rem; color: #4a5a4a; }
.btn-primary.legal-done { width: auto; min-height: 40px; }

/* BUTTON ROW */
.form-nav { display: flex; gap: 12px; margin-top: 4px; }
.form-nav .btn-primary { flex: 1; }
.btn-spinner { width: 15px; height: 15px; border-radius: 50%; border: 2px solid rgba(255, 255, 255, 0.35); border-top-color: #fff; animation: btn-spin 0.7s linear infinite; flex-shrink: 0; }
@keyframes btn-spin { to { transform: rotate(360deg); } }
.top-back { margin-bottom: 32px; }
.resend-wait { color: #a37a0b; font-weight: 600; font-variant-numeric: tabular-nums; }
.link-disabled { opacity: 0.45; pointer-events: none; cursor: not-allowed; }
.form-success { margin-top: 4px; }

@media (max-width: 900px) {
  .role-grid, .field-row { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 640px) {
  .legal-overlay { padding: 0; }
  .legal-modal { max-width: none; height: 100vh; height: 100dvh; border-radius: 0; }
  .legal-foot .btn-primary.legal-done { width: 100%; }
}
</style>
