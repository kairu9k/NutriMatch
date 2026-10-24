<template>
  <!-- ADMIN SIGN IN (/admin/login): the green banner as the page, one white card -->
  <div v-if="isAdminMode" class="admin-login-page">
    <div class="admin-page-circle admin-circle-1"></div>
    <div class="admin-page-circle admin-circle-2"></div>
    <div class="admin-page-circle admin-circle-3"></div>
    <NuxtLink to="/" class="brand home-link admin-page-brand" aria-label="NutriMatch home">
      <img src="/resources/nutrimatchlogo.png" alt="" class="logo-icon" />
      <span>Nutri<span class="logo-match">Match</span></span>
    </NuxtLink>

    <div class="admin-card">
      <h1>Admin sign in</h1>
      <p class="admin-subtitle">For the NutriMatch team. Clients and RNDs sign in on the main page.</p>

      <form class="auth-form" @submit.prevent="handleAdminLogin">
        <div class="field">
          <label for="admin-email">Email address</label>
          <div class="input-icon-wrap">
            <User class="input-icon" aria-hidden="true" />
            <input id="admin-email" v-model="adminForm.email" type="email" autocomplete="username" placeholder="you@nutrimatch.ph" required />
          </div>
        </div>

        <div class="field">
          <label for="admin-password">Password</label>
          <div class="input-icon-wrap">
            <Lock class="input-icon" aria-hidden="true" />
            <input
              id="admin-password"
              v-model="adminForm.password"
              :type="showAdminPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="Your password"
              required
            />
            <button type="button" class="toggle-visibility" :aria-label="showAdminPassword ? 'Hide password' : 'Show password'" @click="showAdminPassword = !showAdminPassword">
              <EyeOff v-if="showAdminPassword" :size="17" aria-hidden="true" /><Eye v-else :size="17" aria-hidden="true" />
            </button>
          </div>
        </div>

        <div v-if="deactivated && isAdminMode" class="form-error deactivated-box" role="alert">
          <p class="deactivated-title">Your account has been deactivated</p>
          <p>The NutriMatch admin deactivated this account, so you can't sign in right now. If you think this is a mistake, email us to request a review.</p>
          <a :href="deactivatedMailto" class="deactivated-link">{{ deactivated }}</a>
        </div>
        <p v-else-if="errorMessage && isAdminMode" class="form-error" role="alert">{{ errorMessage }}</p>

        <button type="submit" class="btn-primary" :disabled="isSubmitting">
          {{ isSubmitting ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>
    </div>

    <NuxtLink to="/login" class="back-link on-green"><ArrowLeft :size="14" aria-hidden="true" /> Client and RND sign in</NuxtLink>
  </div>

  <!-- CLIENT / RND SIGN IN -->
  <div v-else class="auth-page">
    <aside class="left-panel">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
      <div class="circle circle-4"></div>
      <div class="circle circle-5"></div>

      <NuxtLink to="/" class="brand home-link" aria-label="NutriMatch home">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="logo-icon" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </NuxtLink>

      <div class="left-content">
        <span class="eyebrow">WELCOME BACK !</span>
        <h1>
          Your health<br />
          journey <em class="highlight">continues</em><br />
          here.
        </h1>
        <p class="left-desc">Access your dashboard, meal plans, and consultation records securely.</p>
      </div>

      <ul class="trust-badges">
        <li><span class="dot"></span> RA 10173 Data Privacy compliant</li>
        <li><span class="dot"></span> PRC-verified RNDs only</li>
      </ul>
    </aside>

    <main class="right-panel">
      <div class="form-wrap">
        <h2>Sign in</h2>
        <p class="subtitle">Use the email and password you signed up with.</p>

        <form class="auth-form" @submit.prevent="handleLogin">
          <div class="field">
            <label for="login-email">Email address</label>
            <div class="input-icon-wrap">
              <User class="input-icon" aria-hidden="true" />
              <input id="login-email" v-model="form.email" type="email" autocomplete="username" placeholder="you@example.com" required />
            </div>
          </div>

          <div class="field">
            <label for="login-password">Password</label>
            <div class="input-icon-wrap">
              <Lock class="input-icon" aria-hidden="true" />
              <input
                id="login-password"
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="Your password"
                required
              />
              <button type="button" class="toggle-visibility" :aria-label="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword">
                <EyeOff v-if="showPassword" :size="17" aria-hidden="true" /><Eye v-else :size="17" aria-hidden="true" />
              </button>
            </div>
          </div>

          <div class="form-options">
            <label class="remember-me">
              <input v-model="form.rememberMe" type="checkbox" />
              Remember me
            </label>
            <NuxtLink to="/forgot-password" class="forgot-link">Forgot password?</NuxtLink>
          </div>

          <div v-if="deactivated && !isAdminMode" class="form-error deactivated-box" role="alert">
            <p class="deactivated-title">Your account has been deactivated</p>
            <p>The NutriMatch admin deactivated this account, so you can't sign in right now. If you think this is a mistake, email us to request a review.</p>
            <a :href="deactivatedMailto" class="deactivated-link">{{ deactivated }}</a>
          </div>
          <p v-else-if="errorMessage && !isAdminMode" class="form-error" role="alert">{{ errorMessage }}</p>

          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            {{ isSubmitting ? 'Signing in…' : 'Sign in' }}
          </button>
          <NuxtLink to="/" class="back-link home-back"><ArrowLeft :size="14" aria-hidden="true" /> Back to home</NuxtLink>
        </form>

        <p class="signup-link">
          New to NutriMatch? <NuxtLink to="/register">Create an account</NuxtLink>
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ArrowLeft, Eye, EyeOff, Lock, User } from 'lucide-vue-next'
const auth = useAuthStore()

// Admins sign in on their own route (/admin/login → pages/admin/login.vue
// passes `admin`); /login is for clients and RNDs only.
const props = defineProps({ admin: { type: Boolean, default: false } })
const isAdminMode = computed(() => props.admin)

const showPassword = ref(false)
const form = reactive({
  email: '',
  password: '',
  rememberMe: true,
})

const showAdminPassword = ref(false)
const adminForm = reactive({
  email: '',
  password: '',
})

const errorMessage = ref('')
// Deactivated by an admin: the API returns the support email to appeal to.
const deactivated = ref('')
const deactivatedMailto = computed(() => {
  const subject = encodeURIComponent('Request to review my deactivated NutriMatch account')
  const body = encodeURIComponent(`Hi NutriMatch team,\n\nMy account (${form.email || adminForm.email}) was deactivated. I'd like to request a review.\n\nThank you.`)
  return `mailto:${deactivated.value}?subject=${subject}&body=${body}`
})
function showLoginError(error) {
  const data = error?.data || {}
  deactivated.value = data.code === 'account_deactivated' ? (data.support_email || '') : ''
  errorMessage.value = data.detail || 'Incorrect email or password.'
}
const isSubmitting = ref(false)

const roleRedirect = {
  client: '/client-dashboard',
  rnd: '/rnd-dashboard',
  admin: '/admin-dashboard',
}

async function handleLogin() {
  errorMessage.value = ''
  deactivated.value = ''
  isSubmitting.value = true
  try {
    const user = await auth.login(form.email, form.password, form.rememberMe)
    if (user.role === 'admin') {
      auth.logout()
      errorMessage.value = 'Admin accounts sign in on the admin sign-in page.'
      return
    }
    navigateTo(roleRedirect[user.role] || '/')
  } catch (error) {
    showLoginError(error)
  } finally {
    isSubmitting.value = false
  }
}

async function handleAdminLogin() {
  errorMessage.value = ''
  deactivated.value = ''
  isSubmitting.value = true
  try {
    const user = await auth.login(adminForm.email, adminForm.password)
    if (user.role !== 'admin') {
      auth.logout()
      errorMessage.value = 'This account is not an admin account.'
      return
    }
    navigateTo('/admin-dashboard')
  } catch (error) {
    showLoginError(error)
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
.circle-4 { width: 260px; height: 260px; bottom: 50%; left: 8%; }
.circle-5 { width: 180px; height: 180px; top: 40%; right: 12%; }

.auth-form { display: flex; flex-direction: column; gap: 18px; }
/* Remember me on the left, Forgot password? on the right */
.form-options { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-top: -4px; }
.remember-me { display: flex; align-items: center; gap: 8px; font-size: 0.86rem; color: #4a5a4a; cursor: pointer; }
.remember-me input { width: 16px; height: 16px; accent-color: #0a4a37; cursor: pointer; }
.home-back { align-self: center; }
.forgot-link { font-size: 0.82rem; font-weight: 600; color: #0a4a37; text-decoration: underline; text-underline-offset: 2px; }
.deactivated-box p { margin: 0 0 6px; line-height: 1.5; }
.deactivated-title { font-weight: 700; }
.deactivated-link { font-weight: 700; color: inherit; text-decoration: underline; word-break: break-all; }

/* ADMIN */
.admin-login-page {
  min-height: 100vh; min-height: 100dvh; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 22px;
  padding: 32px 16px; background: #0d2818; font-family: 'Inter', sans-serif; color: #1a3a1a; position: relative; overflow: hidden;
}
/* the original background picture */
.admin-page-circle { position: absolute; border-radius: 50%; background: radial-gradient(circle at 45% 40%, #0d2818, #053D2B, #0d2818 100%); box-shadow: #0d2818 10px 20px 10px 100px; pointer-events: none; }
.admin-circle-1 { width: 420px; height: 420px; top: -140px; right: -100px; }
.admin-circle-2 { width: 380px; height: 380px; bottom: -220px; right: 8%; }
.admin-circle-3 { width: 460px; height: 460px; bottom: -260px; left: -140px; }
.admin-login-page > :not(.admin-page-circle) { position: relative; z-index: 2; }
.admin-page-brand { color: #fff; }
.admin-card { width: 100%; max-width: 440px; background: #fff; border-radius: 18px; padding: 32px; box-shadow: 0 20px 50px rgba(0, 20, 12, 0.35); }
.admin-card h1 { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.6rem; line-height: 1.2; margin: 0 0 6px; }
.admin-subtitle { font-size: 0.9rem; color: #4a5a4a; line-height: 1.5; margin: 0 0 24px; }
/* the way back sits on the green: see-through white */
.back-link.on-green { align-self: center; background: rgba(255, 255, 255, 0.14); color: #fff; }
.back-link.on-green:hover { background: rgba(255, 255, 255, 0.22); }
.back-link.on-green:focus-visible { outline-color: #f3d27a; }
@media (max-width: 480px) {
  .admin-card { padding: 24px 20px; }
}
</style>
