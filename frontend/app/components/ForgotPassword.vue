<template>
  <div class="login-page">
    <!-- LEFT PANEL -->
    <aside class="left-panel">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>

      <div class="brand">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="logo-icon" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </div>

      <div class="left-content">
        <span class="eyebrow">ACCOUNT RECOVERY</span>
        <h1>Let's get you<br />back <em class="highlight">in.</em></h1>
        <p class="left-desc">We'll email a one-time code to verify it's really you before resetting your password.</p>
      </div>

      <ul class="trust-badges">
        <li><span class="dot"></span> RA 10173 Data Privacy compliant</li>
        <li><span class="dot"></span> Codes expire after 15 minutes</li>
      </ul>
    </aside>

    <!-- RIGHT PANEL -->
    <main class="right-panel">
      <button class="back-link" @click="navigateTo('/login')">← Back to log in</button>

      <div class="form-wrap">
        <!-- STEP 1: REQUEST CODE -->
        <template v-if="step === 'request'">
          <h2>Forgot Your Password?</h2>
          <p class="subtitle">Enter the email associated with your account and we'll send you a reset code.</p>

          <form class="login-form" @submit.prevent="handleRequest">
            <div class="field">
              <label>Email Address</label>
              <div class="input-icon-wrap">
                <span class="input-icon">👤</span>
                <input v-model="email" type="email" placeholder="you@example.com" required />
              </div>
            </div>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

            <button type="submit" class="btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? 'Sending…' : 'Send Reset Code' }}
            </button>
          </form>
        </template>

        <!-- STEP 2: ENTER CODE + NEW PASSWORD -->
        <template v-else-if="step === 'confirm'">
          <div class="sent-icon">✉️</div>
          <h2>Check Your Inbox</h2>
          <p class="subtitle">
            We've sent a 6-digit code to <strong>{{ email }}</strong>. Enter it below along with your new password.
          </p>

          <form class="login-form" @submit.prevent="handleConfirm">
            <div class="field">
              <label>Reset Code</label>
              <input v-model="code" type="text" inputmode="numeric" maxlength="6" placeholder="123456" class="code-input" required />
            </div>

            <div class="field">
              <label>New Password</label>
              <div class="input-icon-wrap">
                <span class="input-icon">🔒</span>
                <input
                  v-model="newPassword"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="Enter a new password"
                  required
                />
                <button type="button" class="toggle-visibility" @click="showPassword = !showPassword">
                  {{ showPassword ? 'HIDE' : 'SHOW' }}
                </button>
              </div>
              <span class="field-hint">Min. 8 characters.</span>
            </div>

            <div class="field">
              <label>Confirm New Password</label>
              <input v-model="confirmPassword" :type="showPassword ? 'text' : 'password'" placeholder="Re-enter your new password" required />
            </div>

            <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
            <p v-if="successMessage" class="form-success">{{ successMessage }}</p>

            <button type="submit" class="btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? 'Resetting…' : 'Reset Password' }}
            </button>
          </form>

          <p class="signup-link">
            Didn't get the code? <a href="#" @click.prevent="step = 'request'">Try a different email</a>
          </p>
        </template>
      </div>
    </main>
  </div>
</template>

<script setup>
const auth = useAuthStore()

const step = ref('request')
const email = ref('')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const isSubmitting = ref(false)

async function handleRequest() {
  errorMessage.value = ''
  isSubmitting.value = true
  try {
    await auth.requestPasswordReset(email.value)
    step.value = 'confirm'
  } catch {
    errorMessage.value = 'Something went wrong. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

async function handleConfirm() {
  errorMessage.value = ''
  successMessage.value = ''

  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'Passwords do not match.'
    return
  }

  isSubmitting.value = true
  try {
    await auth.confirmPasswordReset(email.value, code.value, newPassword.value)
    successMessage.value = 'Password reset! Redirecting to log in…'
    setTimeout(() => navigateTo('/login'), 1500)
  } catch (error) {
    errorMessage.value = error?.data?.detail || error?.data?.new_password?.[0] || 'Invalid or expired code.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600;700&display=swap');

.login-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  font-family: 'Inter', sans-serif;
}

/* LEFT PANEL */
.left-panel {
  background: linear-gradient(180deg, #053B2A 0%, #053B2A 100%);
  position: relative;
  overflow: hidden;
  padding: 48px 64px;
  color: #fff;
  display: flex;
  flex-direction: column;
}

.circle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle at 35% 30%, #2E5E42, #053D2B, #162E22 100%);
  box-shadow: #053B2A 0px 10px 80px 100px;
  pointer-events: none;
}
.circle-1 { width: 420px; height: 420px; top: -150px; right: -120px; }
.circle-2 { width: 360px; height: 360px; bottom: 50px; right: -170px; }
.circle-3 { width: 480px; height: 480px; bottom: -190px; left: -130px; }

.brand { display: flex; align-items: center; gap: 10px; font-size: 1.3rem; font-weight: 700; position: relative; z-index: 1; font-family: 'Playfair Display', serif; }
.logo-icon { width: 50px; height: 50px; object-fit: contain; }
.logo-match { color: #D4A017; }

.left-content { margin-top: 140px; position: relative; z-index: 1; }

.eyebrow { font-size: 0.75rem; letter-spacing: 0.14em; color: #a8c4a8; font-weight: 600; }

.left-content h1 {
  font-family: 'Playfair Display', serif;
  font-style: italic;
  font-weight: 900;
  font-size: clamp(2.8rem, 4vw, 3.2rem);
  letter-spacing: 0.04em;
  line-height: 1.15;
  margin: 18px 0 24px;
}
.highlight { color: #D4A017; }

.left-desc { font-size: 0.92rem; color: #a8c4a8; line-height: 1.6; max-width: 380px; }

.trust-badges {
  position: relative;
  z-index: 1;
  list-style: none;
  margin-top: auto;
  padding-top: 32px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.trust-badges li { display: flex; align-items: center; gap: 10px; font-size: 0.82rem; color: #cfe0cf; }
.trust-badges .dot { width: 6px; height: 6px; border-radius: 50%; background: #D4A017; flex-shrink: 0; }

/* RIGHT PANEL */
.right-panel { background: #fff; padding: 90px 90px; display: flex; flex-direction: column; }

.back-link { background: none; border: none; cursor: pointer; color: #6a8a6a; font-size: 0.9rem; align-self: flex-start; }

.form-wrap { max-width: 480px; margin: 40px auto 0; width: 100%; }

.sent-icon { font-size: 2rem; margin-bottom: 8px; }

.form-wrap h2 {
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: 2rem;
  color: #1a3a1a;
  margin-bottom: 8px;
}

.subtitle { color: #8a9a8a; font-size: 0.9rem; margin-bottom: 32px; line-height: 1.5; }
.subtitle strong { color: #1a3a1a; }

.login-form { display: flex; flex-direction: column; gap: 18px; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field label {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #1a3a1a;
  text-transform: uppercase;
}
.field input {
  padding: 12px 14px;
  border: 1px solid #dde3dd;
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  background: #f7f9f7;
  color: #1a3a1a;
}
.field input:focus { outline: none; border-color: #1a3a1a; background: #fff; }
.field-hint { font-size: 0.76rem; color: #9aaa9a; }

.code-input { letter-spacing: 0.3em; font-size: 1.2rem; text-align: center; font-weight: 700; }

.input-icon-wrap { position: relative; display: flex; align-items: center; }
.input-icon-wrap input { flex: 1; padding-left: 38px; padding-right: 60px; }
.input-icon { position: absolute; left: 12px; font-size: 0.9rem; color: #9aa8a0; pointer-events: none; }
.toggle-visibility {
  position: absolute; right: 12px;
  background: none; border: none; cursor: pointer;
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em;
  color: #6a8a6a;
}

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
  transition: background 0.2s;
}
.btn-primary:hover { background: #14300f; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.signup-link { text-align: center; margin-top: 24px; font-size: 0.88rem; color: #8a9a8a; }
.signup-link a { color: #1a3a1a; font-weight: 600; text-decoration: none; }

.form-error {
  background: #fdecec;
  border: 1px solid #f3b8b8;
  color: #a12525;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.85rem;
  margin: -4px 0 0;
}
.form-success {
  background: #e6f4e6;
  border: 1px solid #b8ddb8;
  color: #1a5a2a;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.85rem;
  margin: -4px 0 0;
}

@media (max-width: 900px) {
  .login-page { grid-template-columns: 1fr; }
  .left-panel { padding: 32px; min-height: 240px; }
  .left-content { margin-top: 32px; }
  .right-panel { padding: 32px; }
  .form-wrap { margin-top: 32px; }
  .trust-badges { margin-top: 24px; }
}
</style>
