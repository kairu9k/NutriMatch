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
            :class="{ active: currentStep === index + 1, done: currentStep > index + 1 }"
          >
            <span class="step-number">
              <span v-if="currentStep > index + 1">✓</span>
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
      <button class="back-link" @click="navigateTo('/')">
        ← Back to home
      </button>

      <div class="form-wrap">
        <!-- STEP 1: CHOOSE ROLE -->
        <div v-if="currentStep === 1">
          <h2>Choose Your Role</h2>
          <p class="subtitle">Step 1 of 3 — Tell us how you'll use NutriMatch</p>

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
          <h2>Your Details</h2>
          <p class="subtitle">Step 2 of 3 — Enter your personal information</p>

          <form class="details-form" @submit.prevent="currentStep = 3">
            <div class="field-row">
              <div class="field">
                <label>First Name</label>
                <input v-model="form.firstName" type="text" placeholder="Julia Niel" required />
              </div>
              <div class="field">
                <label>Last Name</label>
                <input v-model="form.lastName" type="text" placeholder="Bulalaque" required />
              </div>
            </div>

            <div class="field">
              <label>Email Address</label>
              <div class="input-icon-wrap">
                <span class="input-icon">👤</span>
                <input v-model="form.email" type="email" placeholder="bulalaque@email.com" required />
              </div>
            </div>

            <div class="field">
              <label>Password</label>
              <div class="input-icon-wrap">
                <span class="input-icon">🔒</span>
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
            </div>

            <div class="field">
              <label>Confirm Password</label>
              <div class="input-icon-wrap">
                <span class="input-icon">🔒</span>
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
            </div>

            <template v-if="selectedRole === 'patient'">
              <div class="field-row">
                <div class="field">
                  <label>Date of Birth</label>
                  <input v-model="form.dob" type="date" required />
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
                <label>PRC License Number</label>
                <input v-model="form.prcLicenseNumber" type="text" placeholder="0012345" required />
              </div>
              <div class="field">
                <label>Specialization</label>
                <input v-model="form.specialization" type="text" placeholder="Diabetes Management" />
              </div>
            </template>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

            <div class="form-nav">
              <button type="button" class="btn-back" @click="currentStep = 1">← Back</button>
              <button type="submit" class="btn-primary">Continue →</button>
            </div>
          </form>
        </div>

        <!-- STEP 3: CONFIRM -->
        <div v-else-if="currentStep === 3">
          <h2>Confirm Your Details</h2>
          <p class="subtitle">Step 3 of 3 — Review before submitting</p>

          <div class="confirm-summary">
            <div class="confirm-row"><span>Role</span><strong>{{ selectedRole }}</strong></div>
            <div class="confirm-row"><span>Name</span><strong>{{ form.firstName }} {{ form.lastName }}</strong></div>
            <div class="confirm-row"><span>Email</span><strong>{{ form.email }}</strong></div>
            <template v-if="selectedRole === 'patient'">
              <div class="confirm-row"><span>Date of Birth</span><strong>{{ form.dob }}</strong></div>
              <div class="confirm-row"><span>Gender</span><strong>{{ form.gender }}</strong></div>
              <div class="confirm-row"><span>Primary Health Concern</span><strong>{{ form.healthConcern }}</strong></div>
            </template>
            <template v-else-if="selectedRole === 'rnd'">
              <div class="confirm-row"><span>PRC License Number</span><strong>{{ form.prcLicenseNumber }}</strong></div>
              <div class="confirm-row"><span>Specialization</span><strong>{{ form.specialization || '—' }}</strong></div>
            </template>
          </div>

          <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

          <div class="form-nav">
            <button type="button" class="btn-back" @click="currentStep = 2">← Back</button>
            <button class="btn-primary" :disabled="isSubmitting" @click="submitRegistration">
              {{ isSubmitting ? 'Creating account…' : 'Create Account →' }}
            </button>
          </div>
        </div>

        <p class="signin-link">
          Already have an account? <a href="#" @click.prevent="navigateTo('/login')">Sign in →</a>
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
const auth = useAuthStore()

const currentStep = ref(1)
const selectedRole = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const errorMessage = ref('')
const isSubmitting = ref(false)

const form = reactive({
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  confirmPassword: '',
  dob: '',
  gender: '',
  healthConcern: '',
  prcLicenseNumber: '',
  specialization: ''
})

const genderToSex = { Male: 'male', Female: 'female' }

const steps = [
  { label: 'Choose Role' },
  { label: 'Your Details' },
  { label: 'Confirm' }
]

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
        prc_license_number: form.prcLicenseNumber,
        specialization: form.specialization,
      })
    } else {
      await auth.registerClient({
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
        date_of_birth: form.dob || undefined,
        sex: genderToSex[form.gender],
        primary_health_concern: form.healthConcern,
      })
    }

    // Registration doesn't return tokens — log in right after so the user
    // lands signed in instead of being bounced back to the login page.
    const user = await auth.login(form.email, form.password)
    if (user.role === 'rnd') {
      navigateTo('/rnd-dashboard')
    } else {
      navigateTo('/appointments')
    }
  } catch (error) {
    const data = error?.data
    errorMessage.value = data?.email?.[0] || data?.prc_license_number?.[0] || data?.detail || 'Registration failed. Please check your details and try again.'
  } finally {
    isSubmitting.value = false
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

.back-link {
  background: none; border: none; cursor: pointer;
  color: #6a8a6a; font-size: 0.9rem; align-self: flex-start;
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

.input-icon-wrap { position: relative; display: flex; align-items: center; }
.input-icon-wrap input { flex: 1; padding-left: 38px; padding-right: 60px; }
.input-icon {
  position: absolute; left: 12px;
  font-size: 0.9rem; color: #9aa8a0;
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

@media (max-width: 900px) {
  .register-page { grid-template-columns: 1fr; }
  .left-panel { padding: 32px; min-height: 320px; }
  .left-content { margin-top: 32px; }
  .right-panel { padding: 32px; }
  .form-wrap { margin-top: 32px; }
  .role-grid { grid-template-columns: 1fr; }
  .field-row { grid-template-columns: 1fr; }
}
</style>