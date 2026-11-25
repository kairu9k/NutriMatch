<template>
  <div class="nm-reg">
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
        <NuxtLink to="/" class="nm-brand" aria-label="NutriMatch home">
          <img src="/resources/nutrimatchlogo.png" alt="" class="nm-brand-logo" />
          <span class="nm-brand-text">Nutri<span>Match</span></span>
        </NuxtLink>

        <div class="nm-welcome">
          <span class="nm-eyebrow"><span class="nm-eyebrow-line" aria-hidden="true"></span>CREATE ACCOUNT</span>
          <h1 class="nm-hero">Join your <em>nutrition</em> journey today.</h1>

          <ol class="nm-steps" aria-label="Sign-up steps">
            <li
              v-for="(step, index) in steps"
              :key="step.label"
              class="nm-step"
              :class="{ active: stageIndex === index, done: stageIndex > index }"
            >
              <span class="nm-step-dot">
                <span v-if="stageIndex > index">✓</span>
                <span v-else>{{ index + 1 }}</span>
              </span>
              <span class="nm-step-text">
                <span class="nm-step-kick">STEP {{ String(index + 1).padStart(2, '0') }}</span>
                <span class="nm-step-title">{{ step.label }}</span>
              </span>
            </li>
          </ol>
        </div>
      </div>
    </aside>

    <!-- RIGHT: the form (scrolls on its own on desktop) -->
    <main ref="rightPane" class="nm-right">
      <div class="nm-dots nm-dots-top" aria-hidden="true"></div>
      <div class="nm-dots nm-dots-bottom" aria-hidden="true"></div>

      <!-- phone / tablet only: the photo panel is hidden, so the brand shows here -->
      <NuxtLink to="/" class="nm-mobile-brand" aria-label="NutriMatch home">
        <img src="/resources/nutrimatchlogo.png" alt="" class="nm-mobile-logo" />
        <span class="nm-mobile-text">Nutri<span>Match</span></span>
      </NuxtLink>

      <!-- one back button, always here at the top: to log in, or to the step before -->
      <div class="nm-right-top">
        <template v-if="topBack">
          <NuxtLink v-if="topBack.to" :to="topBack.to" class="nm-back"><ArrowLeft :size="15" aria-hidden="true" /> {{ uiLabel(topBack.label) }}</NuxtLink>
          <button v-else type="button" class="nm-back" :disabled="isSubmitting" @click="goBack(topBack.step)"><ArrowLeft :size="15" aria-hidden="true" /> {{ uiLabel(topBack.label) }}</button>
        </template>
      </div>

      <div class="nm-box-wrap">
        <div class="nm-box" :class="{ 'is-wide': currentStep === 2 }">

          <!-- progress (steps 1 to 3) -->
          <div v-if="currentStep <= 3" class="nm-progress">
            <span class="nm-progress-text">Step {{ currentStep }} of {{ steps.length }}</span>
            <span class="nm-progress-bars" aria-hidden="true">
              <span v-for="n in steps.length" :key="n" :class="{ on: n <= currentStep }"></span>
            </span>
          </div>

          <!-- STEP 1: CHOOSE ROLE -->
          <div v-if="currentStep === 1">
            <header class="nm-head">
              <h2 class="nm-title">How will you use NutriMatch?</h2>
              <p class="nm-subtitle">Step 1 of {{ steps.length }}.</p>
            </header>

            <div class="nm-roles" role="radiogroup" aria-label="Account type">
              <button
                v-for="role in roles"
                :key="role.value"
                type="button"
                class="nm-role"
                role="radio"
                :aria-checked="selectedRole === role.value"
                :class="{ selected: selectedRole === role.value }"
                @click="selectedRole = role.value"
              >
                <span class="nm-role-radio" aria-hidden="true"><Check :size="12" :stroke-width="3.4" /></span>
                <span class="nm-role-icon" v-html="role.icon"></span>
                <span class="nm-role-name">{{ role.label }}</span>
                <span class="nm-role-desc">{{ role.desc }}</span>
              </button>
            </div>

            <Transition name="fade-slide">
              <div v-if="roleInfo" class="nm-note" role="status">
                <span class="nm-note-icon" aria-hidden="true">i</span>
                <p>{{ roleInfo }}</p>
              </div>
            </Transition>

            <button type="button" class="nm-submit" :disabled="!selectedRole" @click="currentStep = 2">
              Continue <ArrowRight :size="18" aria-hidden="true" />
            </button>
          </div>

          <!-- STEP 2: YOUR DETAILS -->
          <div v-else-if="currentStep === 2">
            <header class="nm-head">
              <h2 class="nm-title">{{ selectedRole === 'rnd' ? 'Account and license' : 'Your details' }}</h2>
              <p class="nm-subtitle">Step 2 of {{ steps.length }}. {{ selectedRole === 'rnd' ? 'How you log in, and your PRC license.' : 'How you log in, and a little about you.' }}</p>
            </header>

            <form class="nm-form" novalidate @submit.prevent="goToConfirm">
              <!-- PERSONAL DETAILS -->
              <section class="nm-section">
                <div class="nm-section-head"><span>Personal details</span></div>
                <div class="nm-grid">
                  <div class="nm-field">
                    <label for="reg-first">First name</label>
                    <input id="reg-first" v-model="form.firstName" class="nm-control" type="text" placeholder="e.g. Juan" maxlength="100" :class="{ invalid: firstNameError }" required />
                    <span v-if="firstNameError" class="nm-error-text">{{ firstNameError }}</span>
                  </div>
                  <div class="nm-field">
                    <label for="reg-last">Last name</label>
                    <input id="reg-last" v-model="form.lastName" class="nm-control" type="text" placeholder="e.g. Dela Cruz" maxlength="100" :class="{ invalid: lastNameError }" required />
                    <span v-if="lastNameError" class="nm-error-text">{{ lastNameError }}</span>
                  </div>

                  <div class="nm-field">
                    <label>Date of birth</label>
                    <DateField v-model="form.dob" :max="latestBirthDate" min="1900-01-01" year-select :invalid="!!dobError" placeholder="Select date" aria-label="Date of birth" />
                    <span v-if="dobError" class="nm-error-text">{{ dobError }}</span>
                  </div>

                  <!-- client: gender + main health concern -->
                  <template v-if="selectedRole === 'patient'">
                    <div class="nm-field">
                      <label for="reg-gender">Gender</label>
                      <select id="reg-gender" v-model="form.gender" class="nm-select block nm-control" required>
                        <option disabled value="">Select</option>
                        <option>Female</option>
                        <option>Male</option>
                        <option>Prefer not to say</option>
                      </select>
                    </div>
                    <div class="nm-field nm-span">
                      <label>Health conditions</label>
                      <span class="nm-hint">Tick every one that applies.</span>
                      <ConditionPicker v-model="form.healthConcerns" v-model:none="form.noCondition" v-model:error="conditionError" />
                    </div>
                  </template>

                  <!-- RND: mobile number -->
                  <template v-else-if="selectedRole === 'rnd'">
                    <div class="nm-field">
                      <label for="reg-phone">Mobile number <span class="nm-required">Required</span></label>
                      <PhoneInput id="reg-phone" v-model="form.phone" label="mobile number" rnd />
                    </div>
                    <span class="nm-hint nm-span">A Philippine mobile number, so our admin team can reach you. Not shown to clients.</span>
                  </template>
                </div>
              </section>

              <!-- ACCOUNT -->
              <section class="nm-section">
                <div class="nm-section-head"><span>Account</span></div>
                <div class="nm-grid">
                  <div class="nm-field nm-span">
                    <label for="reg-email">Email address</label>
                    <div class="nm-input" :class="{ invalid: emailError }">
                      <Mail class="nm-input-icon" aria-hidden="true" />
                      <input id="reg-email" v-model.trim="form.email" type="email" placeholder="you@example.com" required />
                    </div>
                    <span v-if="emailError" class="nm-error-text">{{ emailError }}</span>
                  </div>

                  <div class="nm-field">
                    <label for="reg-pass">Password</label>
                    <div class="nm-input">
                      <Lock class="nm-input-icon" aria-hidden="true" />
                      <input
                        id="reg-pass"
                        v-model="form.password"
                        :type="showPassword ? 'text' : 'password'"
                        placeholder="Choose a password"
                        minlength="8"
                        required
                      />
                      <button type="button" class="nm-eye" :aria-label="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword">
                        <EyeOff v-if="showPassword" :size="18" aria-hidden="true" /><Eye v-else :size="18" aria-hidden="true" />
                      </button>
                    </div>
                  </div>

                  <div class="nm-field">
                    <label for="reg-pass2">Type the password again</label>
                    <div class="nm-input" :class="{ invalid: form.confirmPassword && !passwordsMatch }">
                      <Lock class="nm-input-icon" aria-hidden="true" />
                      <input
                        id="reg-pass2"
                        v-model="form.confirmPassword"
                        :type="showConfirmPassword ? 'text' : 'password'"
                        placeholder="Repeat your password"
                        required
                      />
                      <button type="button" class="nm-eye" :aria-label="showConfirmPassword ? 'Hide password' : 'Show password'" @click="showConfirmPassword = !showConfirmPassword">
                        <EyeOff v-if="showConfirmPassword" :size="18" aria-hidden="true" /><Eye v-else :size="18" aria-hidden="true" />
                      </button>
                    </div>
                    <span v-if="form.confirmPassword && !passwordsMatch" class="nm-error-text">The two passwords don't match.</span>
                  </div>

                  <ul class="nm-rules nm-span" aria-label="Password requirements">
                    <li v-for="rule in passwordRules" :key="rule.label" :class="{ ok: rule.ok }">
                      <Check v-if="rule.ok" :size="12" :stroke-width="3" aria-hidden="true" /><span v-else class="nm-rule-dot" aria-hidden="true"></span>
                      {{ rule.label }}
                    </li>
                  </ul>
                </div>
              </section>

              <!-- RND: PRC LICENSE + PRACTICE -->
              <template v-if="selectedRole === 'rnd'">
                <section class="nm-section">
                  <div class="nm-section-head"><span>PRC license</span></div>
                  <div class="nm-grid">
                    <div class="nm-field nm-span">
                      <label for="reg-prc">PRC license number <span class="nm-required">Required</span></label>
                      <input
                        id="reg-prc"
                        v-model="form.prcNumber"
                        class="nm-control"
                        type="text"
                        inputmode="numeric"
                        maxlength="7"
                        placeholder="e.g. 0123456"
                        :class="{ invalid: prcNumberError }"
                      />
                      <span v-if="prcNumberError" class="nm-error-text">{{ prcNumberError }}</span>
                      <span v-else class="nm-hint">The 7-digit number on your PRC ID.</span>
                    </div>

                    <div class="nm-field">
                      <label>PRC license photo <span class="nm-required">Required</span></label>
                      <label class="nm-upload" :class="{ 'has-file': licensePreview }">
                        <input ref="licenseInput" type="file" accept="image/jpeg,image/png,image/webp" class="nm-file" @change="onLicenseSelected" />
                        <img v-if="licensePreview" :src="licensePreview" alt="PRC license preview" class="nm-upload-preview" />
                        <span v-else class="nm-upload-empty">
                          <span class="nm-upload-icon" aria-hidden="true"><Upload :size="22" /></span>
                          <strong>Upload a clear photo of your PRC ID</strong>
                          JPG, PNG or WEBP, up to 10 MB
                        </span>
                      </label>
                      <div v-if="form.prcLicenseImage" class="nm-file-row">
                        <span class="nm-file-name">{{ form.prcLicenseImage.name }}. Click the photo to change it.</span>
                        <button type="button" class="nm-remove" @click="removeLicense">Remove</button>
                      </div>
                      <span class="nm-hint">Only our admin team sees this photo, to verify your license.</span>
                    </div>

                    <div class="nm-field">
                      <label>Selfie with your PRC license <span class="nm-required">Required</span></label>
                      <label class="nm-upload" :class="{ 'has-file': selfiePreview }">
                        <input ref="selfieInput" type="file" accept="image/jpeg,image/png,image/webp" class="nm-file" @change="onSelfieSelected" />
                        <img v-if="selfiePreview" :src="selfiePreview" alt="Selfie preview" class="nm-upload-preview" />
                        <span v-else class="nm-upload-empty">
                          <span class="nm-upload-icon" aria-hidden="true"><Upload :size="22" /></span>
                          <strong>Upload a selfie holding your PRC ID</strong>
                          JPG, PNG or WEBP, up to 10 MB
                        </span>
                      </label>
                      <label class="nm-camera">
                        <input type="file" accept="image/*" capture="user" class="nm-file" @change="onSelfieSelected" />
                        <Camera :size="16" aria-hidden="true" /> Take a selfie now
                      </label>
                      <div v-if="form.prcSelfieImage" class="nm-file-row">
                        <span class="nm-file-name">{{ form.prcSelfieImage.name }}. Click the photo to change it.</span>
                        <button type="button" class="nm-remove" @click="removeSelfie">Remove</button>
                      </div>
                      <span class="nm-hint">Only our admin team sees this photo, to confirm your identity.</span>
                    </div>

                    <p class="nm-hint nm-span nm-hint-box">Selfie: hold your PRC ID next to your face so we can see it's really you. Your face and the whole ID are in the photo, the name on the ID is readable, and no sunglasses, mask or cap.</p>
                  </div>
                </section>

                <section class="nm-section">
                  <div class="nm-section-head"><span>Practice</span></div>
                  <div class="nm-field">
                    <label>Specializations <span class="nm-required">Required</span></label>
                    <SpecializationPicker v-model="form.specializations" v-model:error="specError" />
                  </div>
                </section>
              </template>

              <p v-if="errorMessage" class="nm-alert" role="alert">{{ errorMessage }}</p>

              <button type="submit" class="nm-submit" :disabled="!detailsValid || checkingEmail">
                {{ checkingEmail ? 'Checking…' : 'Continue' }} <ArrowRight v-if="!checkingEmail" :size="18" aria-hidden="true" />
              </button>
            </form>
          </div>

          <!-- RND: APPLICATION UNDER REVIEW (stage 7, after verifying the email) -->
          <div v-else-if="currentStep === 7" class="nm-center">
            <span class="nm-big-icon gold" aria-hidden="true"><ClipboardCheck :size="28" /></span>
            <h2 class="nm-title">Application sent</h2>
            <p class="nm-subtitle">
              Thank you, {{ form.firstName }}. Your email is confirmed and your application is with our admin team.
            </p>
            <ol class="nm-next-steps">
              <li><span class="nm-num">1</span><span><strong>We review your PRC license.</strong> It usually takes 1 to 2 business days.</span></li>
              <li><span class="nm-num">2</span><span><strong>We email you at {{ form.email }}</strong> once your account is approved, or if we need anything fixed.</span></li>
              <li><span class="nm-num">3</span><span><strong>Then you can log in.</strong> You'll set up your profile, fee and weekly hours, and clients can find and book you.</span></li>
            </ol>
            <p class="nm-small">You can't log in until your application is approved.</p>
            <button type="button" class="nm-submit" @click="navigateTo('/')">Back to home</button>
          </div>

          <!-- STEP 3: CONFIRM -->
          <div v-else-if="currentStep === 3">
            <header class="nm-head">
              <h2 class="nm-title">{{ selectedRole === 'rnd' ? 'Review and submit' : 'Review and create' }}</h2>
              <p class="nm-subtitle">Step {{ steps.length }} of {{ steps.length }}. Make sure everything is right before you send it.</p>
            </header>

            <div class="nm-summary">
              <div class="nm-row"><span>Signing up as</span><strong><span class="nm-role-pill">{{ selectedRole === 'rnd' ? 'RND' : 'Client' }}</span></strong></div>
              <div class="nm-row"><span>Name</span><strong>{{ form.firstName }} {{ form.lastName }}</strong></div>
              <div class="nm-row"><span>Email</span><strong class="no-capitalize">{{ form.email }}</strong></div>
              <template v-if="selectedRole === 'patient'">
                <div class="nm-row"><span>Date of birth</span><strong>{{ form.dob }}</strong></div>
                <div class="nm-row"><span>Gender</span><strong>{{ form.gender }}</strong></div>
                <div class="nm-row"><span>Health conditions</span><strong>{{ form.healthConcerns.length ? form.healthConcerns.join(', ') : 'None / not sure' }}</strong></div>
              </template>
              <template v-else-if="selectedRole === 'rnd'">
                <div class="nm-row"><span>Date of birth</span><strong>{{ form.dob }}</strong></div>
                <div class="nm-row"><span>Mobile number</span><strong>{{ formatPhone(form.phone) }}</strong></div>
                <div class="nm-row"><span>PRC license number</span><strong>{{ form.prcNumber }}</strong></div>
                <div class="nm-row"><span>PRC license photo</span><img v-if="licensePreview" :src="licensePreview" alt="PRC license" class="nm-thumb" /></div>
                <div class="nm-row"><span>Selfie with your PRC license</span><img v-if="selfiePreview" :src="selfiePreview" alt="Selfie with your PRC license" class="nm-thumb" /></div>
                <div class="nm-row">
                  <span>Specializations</span>
                  <strong class="nm-spec-list">
                    <span v-for="spec in pickedSpecs" :key="spec" class="nm-spec">{{ spec }}</span>
                    <template v-if="!pickedSpecs.length">—</template>
                  </strong>
                </div>
              </template>
            </div>

            <div v-if="selectedRole === 'rnd'" class="nm-note">
              <span class="nm-note-icon" aria-hidden="true">i</span>
              <p>
                Our admin team reviews your PRC license before your account is activated. It usually takes 1 to 2 business days.
                Once it's approved, you finish setting up your profile, fee and weekly hours when you first log in.
              </p>
            </div>

            <!-- Informed consent (RA 10173) — two boxes the person ticks
                 themselves (consent must be their own act, never pre-ticked), and
                 the health-data consent stays separate from the Terms because
                 health information is sensitive personal information. Both stay
                 locked until the Terms and the Privacy Policy were opened.
                 Recorded on the account and in the audit log by the API. -->
            <div class="nm-consent">
              <p v-if="!termsViewed" class="nm-lock-note">
                <Lock :size="16" aria-hidden="true" />
                <span>
                  Open the <a href="/terms" @click.prevent="openLegal('terms')">Terms and Conditions</a> and the
                  <a href="/privacy-policy" @click.prevent="openLegal('privacy')">Privacy Policy</a> first to tick these boxes.
                </span>
              </p>
              <label class="nm-consent-item" :class="{ 'is-locked': !termsViewed }">
                <input v-model="consent.terms" type="checkbox" :disabled="isSubmitting || !termsViewed" />
                <span>
                  I have read and agree to the
                  <a href="/terms" @click.prevent="openLegal('terms')">Terms and Conditions</a> and
                  <a href="/privacy-policy" @click.prevent="openLegal('privacy')">Privacy Policy</a>.
                </span>
              </label>
              <label class="nm-consent-item" :class="{ 'is-locked': !termsViewed }">
                <input v-model="consent.data" type="checkbox" :disabled="isSubmitting || !termsViewed" />
                <span>
                  I consent to NutriMatch collecting and processing my personal and health information
                  {{ selectedRole === 'rnd' ? '(including my PRC license photo and selfie, for verification)' : '(including my screening and nutrition records)' }}
                  to provide nutrition care services, as described in the Privacy Policy, in accordance with
                  Republic Act No. 10173 (Data Privacy Act of 2012).
                </span>
              </label>
            </div>

            <!-- Terms / Privacy pop-up: opens by itself on this step and when a link
                 is clicked. Showing both tabs unlocks and ticks the checkbox. -->
            <div v-if="legalOpen" class="nm-legal-overlay" @click.self="legalOpen = false">
              <div class="nm-legal" role="dialog" aria-modal="true" aria-label="Terms and Conditions and Privacy Policy">
                <div class="nm-legal-head">
                  <div class="nm-legal-tabs">
                    <button type="button" class="nm-legal-tab" :class="{ active: legalTab === 'terms' }" @click="openLegal('terms')">Terms and Conditions</button>
                    <button type="button" class="nm-legal-tab" :class="{ active: legalTab === 'privacy' }" @click="openLegal('privacy')">Privacy Policy</button>
                  </div>
                  <button type="button" class="nm-legal-close" aria-label="Close" @click="legalOpen = false"><X :size="18" aria-hidden="true" /></button>
                </div>
                <iframe class="nm-legal-frame" :class="{ ready: legalReady }" :src="legalTab === 'terms' ? '/terms' : '/privacy-policy'" :title="legalTab === 'terms' ? 'Terms and Conditions' : 'Privacy Policy'" @load="trimLegalFrame"></iframe>
                <div class="nm-legal-foot">
                  <!-- Terms first, then Next leads to the Privacy Policy, which closes. -->
                  <template v-if="legalTab === 'terms'">
                    <p class="nm-legal-hint"><span class="nm-legal-dot"></span>Read the Terms, then the Privacy Policy.</p>
                    <button type="button" class="nm-legal-btn" @click="openLegal('privacy')">Next: Privacy Policy</button>
                  </template>
                  <template v-else>
                    <p class="nm-legal-hint"><span class="nm-legal-dot" :class="{ ok: termsViewed }"></span>{{ termsViewed ? 'You can now tick the consent boxes.' : 'Open the Terms tab too to continue.' }}</p>
                    <button type="button" class="nm-legal-btn" @click="legalOpen = false">{{ termsViewed ? 'Done' : 'Close' }}</button>
                  </template>
                </div>
              </div>
            </div>

            <p v-if="errorMessage" class="nm-alert" role="alert">{{ errorMessage }}</p>

            <button type="button" class="nm-submit" :disabled="isSubmitting || !consentGiven" :aria-busy="isSubmitting" @click="submitRegistration">
              <span v-if="isSubmitting" class="nm-spin" aria-hidden="true"></span>
              {{ isSubmitting ? (selectedRole === 'rnd' ? 'Submitting…' : 'Creating account…') : (selectedRole === 'rnd' ? 'Submit application' : 'Create account') }}
            </button>
          </div>

          <!-- STEP 4: VERIFY EMAIL -->
          <div v-else-if="currentStep === 4">
            <div class="nm-center">
              <span class="nm-big-icon" aria-hidden="true"><Mail :size="28" /></span>
              <h2 class="nm-title">Check your inbox</h2>
              <p class="nm-subtitle">
                We sent a 6-digit code to <strong>{{ form.email }}</strong>. Enter it to confirm your email.
                It can take a minute, so check your spam or junk folder too.
              </p>
            </div>

            <form class="nm-form nm-form-tight" @submit.prevent="submitVerification">
              <div class="nm-field">
                <label for="reg-code">Code</label>
                <input id="reg-code" v-model="verificationCode" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="123456" class="nm-code" required />
              </div>

              <p v-if="errorMessage" class="nm-alert" role="alert">{{ errorMessage }}</p>
              <p v-if="resendMessage" class="nm-success" role="status">{{ resendMessage }}</p>

              <button type="submit" class="nm-submit" :disabled="isSubmitting || isResending" :aria-busy="isSubmitting">
                <span v-if="isSubmitting" class="nm-spin" aria-hidden="true"></span>
                {{ isSubmitting ? 'Verifying…' : 'Confirm email' }}
              </button>
            </form>

            <p class="nm-foot-link">
              Didn't get it?
              <span v-if="resendIn > 0" class="nm-resend-wait">Resend code in {{ resendIn }}s</span>
              <a v-else href="#" :class="{ 'link-disabled': isSubmitting || isResending }" :aria-disabled="isSubmitting || isResending" @click.prevent="!isSubmitting && !isResending && resendCode()">{{ isResending ? 'Sending…' : 'Resend code' }}</a>,
              or <a href="#" :class="{ 'link-disabled': isSubmitting }" :aria-disabled="isSubmitting" @click.prevent="!isSubmitting && changeEmail()">change your email</a>.
            </p>
          </div>

          <p v-if="[1, 2].includes(currentStep)" class="nm-foot-link">
            Already have an account? <a href="#" :class="{ 'link-disabled': isSubmitting }" :aria-disabled="isSubmitting" @click.prevent="!isSubmitting && navigateTo('/login')">Log in</a>
          </p>
        </div>
      </div>

      <p class="nm-copy">© 2026 NutriMatch</p>
    </main>
  </div>
</template>

<script setup>
import { phIso } from '~/utils/phTime'
import { shrinkImage } from '~/utils/shrinkImage'
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
  healthConcerns: [],
  noCondition: false,
  prcLicenseImage: null,
  prcNumber: '',
  phone: '',
  specializations: [],   // up to 3, one may be typed
  prcSelfieImage: null,
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

const MAX_LICENSE_BYTES = 10 * 1024 * 1024
const licensePreview = ref('')

// Checks and shrinks a picked image (license or selfie); null when refused.
async function acceptPhoto(picked, what) {
  errorMessage.value = ''
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(picked.type)) {
    errorMessage.value = `Upload a JPG, PNG, or WEBP ${what}. iPhone HEIC photos: take a screenshot of it, or set the camera to "Most compatible".`
    return null
  }
  if (picked.size > MAX_LICENSE_BYTES) {
    errorMessage.value = `That photo is ${(picked.size / 1024 / 1024).toFixed(1)} MB. The ${what} must be 10 MB or smaller.`
    return null
  }
  // shrink it before it's sent, so the upload is quick on a phone connection
  return await shrinkImage(picked)
}
async function onLicenseSelected(e) {
  const picked = e.target.files?.[0]
  if (!picked) return
  const file = await acceptPhoto(picked, 'photo of your PRC license')
  if (!file) return
  if (licensePreview.value) URL.revokeObjectURL(licensePreview.value)
  form.prcLicenseImage = file
  licensePreview.value = URL.createObjectURL(file)
}

const selfiePreview = ref('')
const selfieInput = ref(null)
async function onSelfieSelected(e) {
  const picked = e.target.files?.[0]
  if (!picked) return
  const file = await acceptPhoto(picked, 'selfie holding your PRC license')
  e.target.value = ''
  if (!file) return
  if (selfiePreview.value) URL.revokeObjectURL(selfiePreview.value)
  form.prcSelfieImage = file
  selfiePreview.value = URL.createObjectURL(file)
}
function removeSelfie() {
  if (selfiePreview.value) URL.revokeObjectURL(selfiePreview.value)
  selfiePreview.value = ''
  form.prcSelfieImage = null
  if (selfieInput.value) selfieInput.value.value = ''
}
onBeforeUnmount(() => {
  if (licensePreview.value) URL.revokeObjectURL(licensePreview.value)
  if (selfiePreview.value) URL.revokeObjectURL(selfiePreview.value)
})
const licenseInput = ref(null)
function removeLicense() {
  if (licensePreview.value) URL.revokeObjectURL(licensePreview.value)
  licensePreview.value = ''
  form.prcLicenseImage = null
  // so picking the same file again still fires @change
  if (licenseInput.value) licenseInput.value.value = ''
}

// Up to 3 specializations, one may be typed: SpecializationPicker.vue holds the
// rules (same as profiles/specializations.py). specError is why they aren't valid yet.
const specError = ref('')
// Client conditions (several allowed, 2026-11-23): ConditionPicker.vue. Answered = at
// least one picked, or None / not sure ticked, and any typed one is valid.
const conditionError = ref('')
const conditionsAnswered = computed(() => (form.healthConcerns.length > 0 || form.noCondition) && !conditionError.value)
const pickedSpecs = computed(() => form.specializations)

// Digits only, max 7 — applied after v-model stores the keystroke (an
// @input handler runs before v-model and would write back the old value).
watch(() => form.prcNumber, v => {
  const digits = v.replace(/\D/g, '').slice(0, 7)
  if (digits !== v) form.prcNumber = digits
})
// Set by the "already registered" check on Continue; editing the number clears it.
const takenPrc = ref('')
const prcNumberError = computed(() => {
  if (form.prcNumber && !/^\d{7}$/.test(form.prcNumber)) return 'Enter all 7 digits of your PRC license number.'
  if (takenPrc.value && form.prcNumber === takenPrc.value) return 'This PRC license number is already registered.'
  return ''
})
watch(() => form.prcNumber, v => {
  if (takenPrc.value && v !== takenPrc.value && errorMessage.value.includes('already registered')) errorMessage.value = ''
})

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
  if (selectedRole.value === 'patient') return !!(form.dob && !dobError.value && form.gender && conditionsAnswered.value)
  if (selectedRole.value === 'rnd') {
    return !!(form.prcLicenseImage && form.dob && !dobError.value
      && /^\d{7}$/.test(form.prcNumber) && !prcNumberError.value && form.prcSelfieImage
      && pickedSpecs.value.length >= 1 && !specError.value && !rndPhoneError(form.phone))
  }
  return false
})

// The back button at the top of each step (none once the account is made).
const topBack = computed(() => {
  const rnd = selectedRole.value === 'rnd'
  switch (currentStep.value) {
    case 1:
    case 2: return { label: 'Back to sign in', to: '/login' }
    case 3: return { label: rnd ? 'Back to account and license' : 'Back to your details', step: 2 }
    default: return null
  }
})
function goBack(step) {
  errorMessage.value = ''
  currentStep.value = step
}

// The first thing on the details step that still needs fixing, in words.
const detailsProblem = computed(() => {
  if (!form.firstName.trim() || firstNameError.value) return 'your first name'
  if (!form.lastName.trim() || lastNameError.value) return 'your last name'
  if (!form.email || emailError.value) return 'your email address'
  if (!passwordRules.value.every(r => r.ok)) return 'your password'
  if (!form.confirmPassword || !passwordsMatch.value) return 'the password typed again'
  if (!form.dob || dobError.value) return 'your date of birth'
  if (selectedRole.value === 'patient') return !form.gender ? 'your gender' : !conditionsAnswered.value ? 'your health conditions' : ''
  if (rndPhoneError(form.phone)) return 'your mobile number'
  if (!/^\d{7}$/.test(form.prcNumber)) return 'your PRC license number'
  if (!form.prcLicenseImage) return 'your PRC license photo'
  if (!form.prcSelfieImage) return 'your selfie with your PRC license'
  if (!pickedSpecs.value.length || specError.value) return 'your specializations'
  return ''
})

async function goToConfirm() {
  if (!detailsValid.value) {
    // On a later step the details aren't on screen: take them back there.
    if (currentStep.value !== 2) currentStep.value = 2
    errorMessage.value = `Please check ${detailsProblem.value || 'the highlighted fields'} first.`
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
      // An RND's PRC number is checked the same way (a verified or approved RND owns it).
      if (selectedRole.value === 'rnd') {
        const prc = await auth.checkRegistrationPrc(form.prcNumber, form.email)
        if (!prc.available) {
          takenPrc.value = form.prcNumber
          errorMessage.value = prc.detail || 'This PRC license number is already registered.'
          return
        }
      }
    } catch {
      // Can't reach the check — carry on; registration itself still refuses a taken email or PRC number.
    } finally {
      checkingEmail.value = false
    }
  }
  if (selectedRole.value === 'rnd' && !form.prcLicenseImage) {
    errorMessage.value = 'Please upload a photo of your PRC license.'
    return
  }
  errorMessage.value = ''
  currentStep.value = 3
}

const genderToSex = { Male: 'male', Female: 'female' }

// RNDs apply with what approval needs (account, PRC license, selfie,
// specializations); their profile, fee, hours and payout come after approval, in
// the RND onboarding (2026-11-16). Stage numbers: 1 role, 2 details, 3 confirm,
// 4 verify email, 7 under review.
const steps = computed(() => (selectedRole.value === 'rnd'
  ? [{ label: 'Choose a role' }, { label: 'Account and license' }, { label: 'Review and submit' }]
  : [{ label: 'Choose a role' }, { label: 'Your details' }, { label: 'Review and create' }]))
const STAGE_ORDER = { patient: [1, 2, 3], rnd: [1, 2, 3] }
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
        prc_selfie_image: form.prcSelfieImage,
        phone: form.phone,
        date_of_birth: form.dob,
        specializations: JSON.stringify(pickedSpecs.value),
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
        health_concerns: form.noCondition ? [] : form.healthConcerns,
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
    const FIELDS = ['email', 'first_name', 'last_name', 'password', 'phone', 'date_of_birth', 'prc_license_number', 'prc_license_image', 'prc_selfie_image', 'specializations',
      'accept_terms', 'data_privacy_consent']
    const failed = FIELDS.find(f => data?.[f]?.[0])
    const code = error?.statusCode || error?.status || error?.response?.status
    // no answer at all: the upload never finished (slow or dropped connection)
    const fallback = !error?.response && !data
        ? "Your application didn't finish sending. Your internet connection may have dropped or been too slow. Check it and press Submit again."
      : code === 413
        ? 'The photos are too large to send. Choose a smaller license photo or selfie and try again.'
        : code >= 500
          ? 'Something went wrong on our side while saving your application. Wait a minute and press Submit again.'
          : 'Registration failed. Please check your details and try again.'
    errorMessage.value = (failed && data[failed][0]) || data?.detail || fallback
    // Send them back to the step that has the problem.
    if (selectedRole.value === 'rnd' && failed) {
      if (!['accept_terms', 'data_privacy_consent'].includes(failed)) currentStep.value = 2
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

// ---------------------------------------------------------------------------
// UI only (design): nothing below talks to the API or changes the sign-up flow.
// ---------------------------------------------------------------------------
import { ArrowRight, Camera, Upload } from 'lucide-vue-next'

// the plate photo on the left (public/landing/login-plate.webp)
const plateImg = '/landing/login-plate.webp'
// Go / Grow / Glow labels placed on the plate photo
const platePins = [
  { tag: 'GO', label: 'Whole grains', share: '¼', x: '34%', y: '22%', side: 'to-right' },
  { tag: 'GROW', label: 'Protein', share: '¼', x: '63%', y: '35%', side: 'to-right' },
  { tag: 'GLOW', label: 'Vegetables', share: '½', x: '80%', y: '53%', side: 'to-left' },
]
// wording only: "sign in" reads "log in" on the buttons, like the log in page
const uiLabel = text => (text || '').replace('sign in', 'log in')
// the form side scrolls on its own on desktop: start each step at its top
const rightPane = ref(null)
watch(currentStep, () => nextTick(() => {
  if (rightPane.value) rightPane.value.scrollTop = 0
  if (typeof window !== 'undefined') window.scrollTo(0, 0)
}))
</script>

<style scoped>
/* =========================================================
   NutriMatch create account: brand #063C2A / #EFBF04 / white
   Fonts: Playfair Display (headings), DM Sans (body)
   ========================================================= */
.nm-reg {
  font-family: 'DM Sans', Arial, sans-serif;
  color: #14261E;
  -webkit-font-smoothing: antialiased;
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(0, 1fr);
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
  margin: 0 0 40px 32px;
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
.nm-reg .nm-hero {
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
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}
.nm-box {
  width: 100%;
  max-width: 520px;
  box-sizing: border-box;
  padding: 48px 52px 40px;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.03),
    0 0 12px rgba(0, 0, 0, 0.08),
    0 0 32px rgba(0, 0, 0, 0.10),
    0 8px 40px rgba(0, 0, 0, 0.12);
  transition: max-width .25s ease;
}
.nm-box.is-wide { max-width: 760px; }

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
.nm-reg .nm-title {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 40px;
  line-height: 1.1;
  font-weight: 700;
  color: #10231B;
}
.nm-subtitle {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: #55665D;
}
.nm-subtitle strong { color: #10231B; }

/* role cards */
.nm-roles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}
.nm-role {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  padding: 22px 18px 20px;
  border-radius: 16px;
  border: 1.5px solid #DCE5DF;
  background: #FFFFFF;
  text-align: left;
  font-family: inherit;
  color: #10231B;
  cursor: pointer;
  transition: border-color .15s, background-color .15s, box-shadow .15s, transform .15s;
}
.nm-role:hover { border-color: #9FBCAC; transform: translateY(-2px); }
.nm-role.selected {
  border: 2px solid #063C2A;
  background: #F3F8F4;
  box-shadow: 0 10px 24px -14px rgba(6, 60, 42, 0.5);
}
.nm-role-radio {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #FFFFFF;
  border: 2px solid #C9D6CE;
  color: transparent;
}
.nm-role.selected .nm-role-radio {
  background: #063C2A;
  border-color: #063C2A;
  color: #FFFFFF;
}
.nm-role-icon {
  width: 48px;
  height: 48px;
  margin-bottom: 6px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #EEF4F0;
  color: #063C2A;
}
.nm-role.selected .nm-role-icon { background: #063C2A; color: #EFBF04; }
.nm-role-name { font-size: 16px; font-weight: 700; }
.nm-role-desc { font-size: 13.5px; line-height: 1.5; color: #5D7065; }

/* gold info note */
.nm-note {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-top: 16px;
  padding: 14px 16px;
  border-radius: 14px;
  background: #FBF6E4;
  border: 1px solid #F1E2A6;
}
.nm-note p { margin: 0; font-size: 14px; line-height: 1.6; color: #4A4020; }
.nm-note-icon {
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #EFBF04;
  color: #063C2A;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: Georgia, serif;
  font-weight: 700;
  font-style: italic;
  font-size: 15px;
}
.fade-slide-enter-active, .fade-slide-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.fade-slide-enter-from, .fade-slide-leave-to { opacity: 0; transform: translateY(-6px); }

/* form */
.nm-form { display: flex; flex-direction: column; gap: 22px; margin: 0; }
.nm-form-tight { gap: 16px; }
.nm-section { display: flex; flex-direction: column; gap: 14px; }
.nm-section-head {
  display: flex;
  align-items: center;
  gap: 10px;
}
.nm-section-head span {
  font-size: 12px;
  font-weight: 800;
  color: #C49102;
}
.nm-section-head::after {
  content: "";
  flex: 1;
  height: 1px;
  background: #E8EDEA;
}
.nm-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px 18px;
  align-items: start;
}
.nm-span { grid-column: 1 / -1; }
.nm-field { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.nm-field > label {
  font-size: 13px;
  font-weight: 600;
  color: #22362C;
}
.nm-required {
  margin-left: 6px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .4px;
  color: #B42318;
}
.nm-hint { font-size: 12.5px; line-height: 1.55; color: #6B7D73; }
.nm-hint-box {
  margin: 0;
  padding: 10px 14px;
  border-radius: 12px;
  background: #F3F6F4;
}
.nm-error-text { font-size: 12.5px; line-height: 1.5; color: #B42318; }

/* plain inputs + selects */
.nm-control {
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 16px;
  border-radius: 14px;
  border: 1.5px solid #DCE5DF;
  background-color: #F7FAF8;
  font-family: inherit;
  font-size: 15px;
  color: #14261E;
  outline: none;
  transition: border-color .15s, box-shadow .15s, background-color .15s;
}
select.nm-control { cursor: pointer; }
.nm-control::placeholder { color: #9AA9A1; }
.nm-control:hover { border-color: #B8C9BE; }
.nm-control:focus {
  border-color: #063C2A;
  background-color: #FFFFFF;
  box-shadow: 0 0 0 4px rgba(6, 60, 42, .10);
}
.nm-control.invalid { border-color: #E2A39B; background-color: #FFF8F7; }

/* inputs with an icon */
.nm-input {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 52px;
  padding: 0 7px 0 16px;
  border-radius: 14px;
  border: 1.5px solid #DCE5DF;
  background: #F7FAF8;
  transition: border-color .15s, box-shadow .15s, background-color .15s;
}
.nm-input:hover { border-color: #B8C9BE; }
.nm-input:focus-within {
  border-color: #063C2A;
  background: #FFFFFF;
  box-shadow: 0 0 0 4px rgba(6, 60, 42, .10);
}
.nm-input.invalid { border-color: #E2A39B; background: #FFF8F7; }
.nm-input-icon { width: 18px; height: 18px; flex-shrink: 0; color: #7A8F84; }
.nm-input input {
  flex: 1;
  min-width: 0;
  height: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 15px;
  color: #14261E;
}
.nm-input input::placeholder { color: #9AA9A1; }
.nm-eye {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #5D7065;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.nm-eye:hover { background: #EEF3EF; color: #063C2A; }
.nm-control:-webkit-autofill,
.nm-input input:-webkit-autofill {
  -webkit-text-fill-color: #14261E;
  -webkit-box-shadow: 0 0 0 1000px #F7FAF8 inset;
  transition: background-color 9999s ease-out 0s;
}

/* password rules as small pills */
.nm-rules {
  list-style: none;
  margin: 2px 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.nm-rules li {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #F3F5F4;
  color: #6B7D73;
  font-size: 12px;
  font-weight: 500;
}
.nm-rules li.ok { background: #EAF4EE; color: #0A5A3C; font-weight: 600; }
.nm-rule-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  border: 1.5px solid #A9B8AF;
}

/* uploads */
.nm-file { display: none; }
.nm-upload {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 150px;
  padding: 14px;
  box-sizing: border-box;
  overflow: hidden;
  border-radius: 14px;
  border: 1.5px dashed #B8C9BE;
  background: #F7FAF8;
  cursor: pointer;
  transition: border-color .15s, background-color .15s;
}
.nm-upload:hover { border-color: #9FBCAC; background: #F1F6F2; }
.nm-upload.has-file { border-style: solid; border-color: #DCE5DF; background: #FFFFFF; }
.nm-upload-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  text-align: center;
  font-size: 12.5px;
  color: #6B7D73;
}
.nm-upload-empty strong { font-size: 14px; color: #10231B; }
.nm-upload-icon {
  width: 46px;
  height: 46px;
  margin-bottom: 2px;
  border-radius: 14px;
  background: #FFFFFF;
  color: #063C2A;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px -6px rgba(6, 60, 42, 0.3);
}
.nm-upload-preview { max-height: 160px; max-width: 100%; border-radius: 10px; object-fit: contain; }
.nm-file-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}
.nm-file-name { font-size: 12.5px; color: #4A5A4A; overflow-wrap: anywhere; }
.nm-remove {
  display: inline-flex;
  align-items: center;
  height: 32px;
  padding: 0 12px;
  border: none;
  border-radius: 999px;
  background: #FEF3F2;
  color: #B42318;
  font-family: inherit;
  font-size: 12.5px;
  font-weight: 700;
  cursor: pointer;
}
.nm-remove:hover { background: #FEE4E2; }
/* the camera button only where a camera is the usual way to add a photo */
.nm-camera {
  display: none;
  align-self: flex-start;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  background: #F1F6F2;
  color: #063C2A;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}
@media (pointer: coarse) { .nm-camera { display: inline-flex; } }

/* messages */
.nm-alert {
  margin: 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: #FEF3F2;
  border: 1px solid #FECDCA;
  color: #B42318;
  font-size: 14px;
  line-height: 1.5;
}
.nm-success {
  margin: 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: #EAF4EE;
  border: 1px solid #BFE0CC;
  color: #0A5A3C;
  font-size: 14px;
  line-height: 1.5;
}

/* main button */
.nm-submit {
  width: 100%;
  margin-top: 22px;
  height: 58px;
  border: none;
  border-radius: 14px;
  background: #063C2A;
  color: #FFFFFF;
  font-family: inherit;
  font-size: 16px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  box-shadow: 0 12px 24px -14px rgba(6, 60, 42, 0.85);
  transition: background-color .15s, box-shadow .15s, transform .15s;
}
.nm-form .nm-submit { margin-top: 4px; }
.nm-submit:hover:not(:disabled) { background: #0A4F38; }
.nm-submit:active:not(:disabled) { transform: scale(.99); }
.nm-submit:disabled {
  background: #DCE5DF;
  color: #7A8F84;
  box-shadow: none;
  cursor: not-allowed;
}
.nm-submit[aria-busy="true"]:disabled { background: #063C2A; color: #FFFFFF; opacity: .85; cursor: progress; }
.nm-spin {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 2.5px solid rgba(239, 191, 4, 0.3);
  border-top-color: #EFBF04;
  animation: nm-spin .8s linear infinite;
}
@keyframes nm-spin { to { transform: rotate(360deg); } }

/* links under the box */
.nm-foot-link {
  margin: 26px 0 0;
  text-align: center;
  font-size: 14px;
  line-height: 1.6;
  color: #55665D;
}
.nm-foot-link a,
.nm-consent a,
.nm-lock-note a {
  font-weight: 700;
  color: #063C2A;
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1.5px;
  text-decoration-color: rgba(196, 145, 2, .7);
}
.nm-resend-wait { font-weight: 700; color: #C49102; font-variant-numeric: tabular-nums; }
.link-disabled { opacity: 0.45; pointer-events: none; cursor: not-allowed; }
.nm-copy {
  margin: 0;
  font-size: 12px;
  color: #7A8F84;
}

/* review summary */
.nm-summary {
  border: 1px solid #E3EAE5;
  border-radius: 16px;
  overflow: hidden;
  background: #FFFFFF;
}
.nm-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 48px;
  padding: 10px 18px;
  box-sizing: border-box;
}
.nm-row + .nm-row { border-top: 1px solid #EEF2EF; }
.nm-row > span { font-size: 14px; color: #6B7D73; flex-shrink: 0; }
.nm-row > strong { font-size: 14.5px; font-weight: 700; color: #10231B; text-align: right; overflow-wrap: anywhere; }
.nm-role-pill {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  background: #063C2A;
  color: #EFBF04;
  font-size: 12.5px;
  font-weight: 800;
  letter-spacing: .4px;
}
.nm-thumb { height: 52px; border-radius: 10px; object-fit: cover; border: 1px solid #DCE5DF; }
.nm-spec-list { display: inline-flex; flex-wrap: wrap; justify-content: flex-end; gap: 6px; }
.nm-spec {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #EAF4EE;
  color: #0A5A3C;
  font-size: 12.5px;
  font-weight: 700;
}

/* consent (RA 10173) */
.nm-consent {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 16px;
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid #E3EAE5;
  background: #FFFFFF;
}
.nm-lock-note {
  margin: 0;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  background: #F3F6F4;
  font-size: 13px;
  line-height: 1.55;
  color: #3E5046;
}
.nm-lock-note svg { flex-shrink: 0; margin-top: 2px; color: #5D7065; }
.nm-consent-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 13.5px;
  line-height: 1.6;
  color: #3E5046;
  cursor: pointer;
}
.nm-consent-item input {
  width: 20px;
  height: 20px;
  margin: 2px 0 0;
  flex-shrink: 0;
  accent-color: #063C2A;
  cursor: pointer;
}
.nm-consent-item.is-locked { cursor: default; opacity: .6; }
.nm-consent-item input:disabled { cursor: not-allowed; }

/* Terms / Privacy pop-up */
.nm-legal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(4, 30, 21, 0.55);
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
}
.nm-legal {
  width: 100%;
  max-width: 1000px;
  height: 92vh;
  height: 92dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 20px;
  background: #FFFFFF;
  box-shadow: 0 30px 80px -20px rgba(0, 0, 0, 0.45);
  animation: nm-pop .3s cubic-bezier(.2, .7, .2, 1);
}
@keyframes nm-pop {
  from { opacity: 0; transform: translateY(12px) scale(.98); }
  to { opacity: 1; transform: none; }
}
.nm-legal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px 14px 20px;
  border-bottom: 1px solid #EEF2EF;
}
.nm-legal-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 4px;
  border-radius: 999px;
  background: #F1F6F2;
}
.nm-legal-tab {
  height: 36px;
  padding: 0 16px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: #063C2A;
  font-family: inherit;
  font-size: 13.5px;
  font-weight: 700;
  cursor: pointer;
}
.nm-legal-tab.active {
  background: #063C2A;
  color: #FFFFFF;
  box-shadow: 0 6px 14px -8px rgba(6, 60, 42, 0.8);
}
.nm-legal-close {
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 999px;
  background: #F1F6F2;
  color: #3E5046;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.nm-legal-close:hover { background: #E5EFE8; color: #063C2A; }
.nm-legal-frame {
  flex: 1;
  width: 100%;
  border: none;
  background: #FFFFFF;
  opacity: 0;
  transition: opacity 0.15s ease;
}
.nm-legal-frame.ready { opacity: 1; }
.nm-legal-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 14px 20px;
  border-top: 1px solid #EEF2EF;
  background: #FFFFFF;
}
.nm-legal-hint {
  margin: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  color: #3E5046;
}
.nm-legal-dot { width: 8px; height: 8px; border-radius: 50%; background: #EFBF04; }
.nm-legal-dot.ok { background: #1F9D55; }
.nm-legal-btn {
  height: 46px;
  padding: 0 20px;
  border: none;
  border-radius: 12px;
  background: #063C2A;
  color: #FFFFFF;
  font-family: inherit;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
}
.nm-legal-btn:hover { background: #0A4F38; }

/* check inbox + application sent */
.nm-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  margin-bottom: 24px;
}
.nm-big-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: #063C2A;
  color: #EFBF04;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 14px 28px -14px rgba(6, 60, 42, 0.8);
}
.nm-big-icon.gold {
  background: #EFBF04;
  color: #063C2A;
  box-shadow: 0 14px 28px -14px rgba(196, 145, 2, 0.8);
}
.nm-center .nm-title { font-size: 38px; margin-top: 6px; }
.nm-code {
  width: 100%;
  height: 64px;
  box-sizing: border-box;
  padding: 0 16px;
  border-radius: 14px;
  border: 1.5px solid #DCE5DF;
  background: #F7FAF8;
  font-family: inherit;
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  color: #10231B;
  outline: none;
}
.nm-code::placeholder { color: #C3CEC8; }
.nm-code:focus {
  border-color: #063C2A;
  background: #FFFFFF;
  box-shadow: 0 0 0 4px rgba(6, 60, 42, .10);
}
.nm-next-steps {
  list-style: none;
  margin: 0;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-radius: 16px;
  border: 1px solid #E3EAE5;
  text-align: left;
}
.nm-next-steps li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 14px;
  line-height: 1.6;
  color: #3E5046;
}
.nm-next-steps strong { color: #10231B; }
.nm-num {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #EFBF04;
  color: #063C2A;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 800;
}
.nm-small { margin: 14px 0 0; text-align: center; font-size: 13px; color: #6B7D73; }

/* focus ring */
.nm-reg a:focus-visible,
.nm-reg button:focus-visible,
.nm-reg input[type=checkbox]:focus-visible {
  outline: 3px solid #EFBF04;
  outline-offset: 2px;
}

/* ---------- desktop: the photo stays put, only the form side scrolls ---------- */
@media (min-width: 961px) {
  .nm-reg { height: 100vh; height: 100dvh; min-height: 0; overflow: hidden; }
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
  .nm-reg { grid-template-columns: 1fr; }
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
    text-decoration: none;
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
  .nm-right-top { order: 2; margin-top: 40px; min-height: 0; }
  .nm-box-wrap { order: 3; align-items: flex-start; padding: 28px 0 32px; }
  .nm-copy { order: 4; text-align: center; }
  .nm-box { padding: 40px 36px 32px; }
}

@media (max-width: 640px) {
  .nm-right { padding: 16px 16px 20px; }
  .nm-mobile-brand { margin-top: 8px; }
  .nm-mobile-text { font-size: 26px; }
  .nm-box-wrap { padding: 24px 0; }
  .nm-box { padding: 28px 20px 24px; border-radius: 14px; }
  .nm-reg .nm-title { font-size: 30px; }
  .nm-center .nm-title { font-size: 30px; }
  .nm-roles,
  .nm-grid { grid-template-columns: minmax(0, 1fr); }
  .nm-control,
  .nm-input input { font-size: 16px; } /* stops iPhone zoom on tap */
  .nm-code { font-size: 24px; }
  .nm-row { flex-wrap: wrap; }
  .nm-legal-overlay { padding: 0; }
  .nm-legal { max-width: none; height: 100vh; height: 100dvh; border-radius: 0; }
  .nm-legal-foot .nm-legal-btn { width: 100%; }
}

@media (prefers-reduced-motion: reduce) {
  .nm-dot::after { animation: none; opacity: 0; }
  .nm-tag,
  .nm-legal { animation: none; }
  .nm-spin { animation: none; }
  .fade-slide-enter-active, .fade-slide-leave-active { transition: none; }
}
</style>