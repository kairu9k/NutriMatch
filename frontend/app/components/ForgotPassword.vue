<template>
  <div class="auth-page">
    <aside class="left-panel">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>

      <NuxtLink to="/" class="brand home-link" aria-label="NutriMatch home">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="logo-icon" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </NuxtLink>

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

    <main class="right-panel">
      <div class="form-wrap">
        <NuxtLink to="/login" class="back-link top-back"><ArrowLeft :size="14" aria-hidden="true" /> Back to sign in</NuxtLink>
        <!-- 1. ask for a code -->
        <template v-if="step === 'request'">
          <h2>Forgot your password?</h2>
          <p class="subtitle">Enter the email on your account and we'll send you a 6-digit code.</p>

          <form class="auth-form" @submit.prevent="handleRequest">
            <div class="field">
              <label for="fp-email">Email address</label>
              <div class="input-icon-wrap">
                <User class="input-icon" aria-hidden="true" />
                <input id="fp-email" v-model="email" type="email" autocomplete="username" placeholder="you@example.com" required />
              </div>
            </div>

            <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>

            <button type="submit" class="btn-primary" :disabled="isSubmitting">
              {{ isSubmitting ? 'Sending…' : 'Send code' }}
            </button>
          </form>
        </template>

        <!-- 2. the code + a new password -->
        <template v-else-if="step === 'confirm'">
          <div class="sent-icon"><Mail :size="24" aria-hidden="true" /></div>
          <h2>Check your inbox</h2>
          <p class="subtitle">
            We sent a 6-digit code to <strong>{{ email }}</strong>. Enter it with your new password.
          </p>

          <form class="auth-form" @submit.prevent="handleConfirm">
            <div class="field">
              <label for="fp-code">Code</label>
              <input id="fp-code" v-model="code" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" placeholder="123456" class="code-input" required />
            </div>

            <div class="field">
              <label for="fp-new">New password</label>
              <div class="input-icon-wrap">
                <Lock class="input-icon" aria-hidden="true" />
                <input
                  id="fp-new"
                  v-model="newPassword"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  placeholder="Choose a new password"
                  required
                />
                <button type="button" class="toggle-visibility" :aria-label="showPassword ? 'Hide passwords' : 'Show passwords'" @click="showPassword = !showPassword">
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
              <label for="fp-confirm">Type it again</label>
              <input id="fp-confirm" v-model="confirmPassword" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" placeholder="The same new password" required />
              <span v-if="confirmPassword && confirmPassword !== newPassword" class="field-error">The two passwords don't match.</span>
            </div>

            <p v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</p>
            <p v-if="successMessage" class="form-success" role="status">{{ successMessage }}</p>

            <button type="submit" class="btn-primary" :disabled="isSubmitting || !passwordOk">
              {{ isSubmitting ? 'Saving…' : 'Change password' }}
            </button>
          </form>

          <p class="signup-link">
            Didn't get it? Check spam, or <a href="#" @click.prevent="step = 'request'">use a different email</a>.
          </p>
        </template>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ArrowLeft, Check, Circle, Eye, EyeOff, Lock, Mail, User } from 'lucide-vue-next'
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

// Same rules as sign-up (the API checks them too: PasswordComplexityValidator).
const passwordRules = computed(() => [
  { label: 'At least 8 characters', ok: newPassword.value.length >= 8 },
  { label: 'One uppercase letter', ok: /[A-Z]/.test(newPassword.value) },
  { label: 'One lowercase letter', ok: /[a-z]/.test(newPassword.value) },
  { label: 'One number', ok: /\d/.test(newPassword.value) },
  { label: 'One special character (e.g. ! @ # $)', ok: /[^A-Za-z0-9\s]/.test(newPassword.value) },
])
const passwordOk = computed(() => passwordRules.value.every(r => r.ok))

async function handleRequest() {
  errorMessage.value = ''
  isSubmitting.value = true
  try {
    await auth.requestPasswordReset(email.value)
    step.value = 'confirm'
  } catch {
    errorMessage.value = 'We couldn\'t send the code. Check your connection and try again.'
  } finally {
    isSubmitting.value = false
  }
}

async function handleConfirm() {
  errorMessage.value = ''
  successMessage.value = ''

  if (!passwordOk.value) {
    errorMessage.value = 'Your new password needs everything on the list.'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'The two passwords don\'t match.'
    return
  }

  isSubmitting.value = true
  try {
    await auth.confirmPasswordReset(email.value, code.value, newPassword.value)
    successMessage.value = 'Password changed. Taking you to sign in…'
    setTimeout(() => navigateTo('/login'), 1500)
  } catch (error) {
    errorMessage.value = error?.data?.detail || error?.data?.new_password?.[0] || 'That code is wrong or has expired. Ask for a new one.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped src="~/assets/css/auth.css"></style>

<style scoped>
/* the original background picture: soft circles on #053B2A */
.left-panel { background: #053B2A; }
.circle { background: radial-gradient(circle at 35% 30%, #2E5E42, #053D2B, #162E22 100%); box-shadow: #053B2A 0px 10px 80px 100px; }
.circle-1 { width: 420px; height: 420px; top: -150px; right: -120px; }
.circle-2 { width: 360px; height: 360px; bottom: 50px; right: -170px; }
.circle-3 { width: 480px; height: 480px; bottom: -190px; left: -130px; }

.auth-form { display: flex; flex-direction: column; gap: 18px; }
/* the original headline here was a little smaller */
.left-content h1 { font-size: clamp(2.8rem, 4vw, 3.2rem); }
.field-error { font-size: 0.78rem; color: #c0392b; }
.top-back { margin-bottom: 18px; }
</style>
