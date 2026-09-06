<template>
  <!-- ADMIN PORTAL LOGIN VIEW -->
  <div v-if="isAdminMode" class="admin-login-page">
    <div class="admin-page-circle admin-circle-1"></div>
    <div class="admin-page-circle admin-circle-2"></div>
    <div class="admin-page-circle admin-circle-3"></div>

    <div class="admin-page-brand">
      <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="admin-page-logo-icon" />
      <span class="admin-page-logo-text">Nutri<span class="logo-match">Match</span></span>
    </div>

    <div class="admin-card">
      <div class="admin-brand">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="admin-logo-icon" />
        <span class="admin-logo-text">Nutri<span class="logo-match">Match</span></span>
      </div>
      <p class="admin-tagline">CLINICAL NUTRITION SYSTEM</p>

      <h1>Admin Portal Login</h1>
      <p class="admin-subtitle">Enter your credentials to continue</p>

      <form class="admin-form" @submit.prevent="handleAdminLogin">
        <div class="field">
          <label>Email</label>
          <input v-model="adminForm.email" type="email" placeholder="admin@nutrimatch.ph" required />
        </div>

        <div class="field">
          <label>Password</label>
          <div class="input-icon-wrap">
            <input
              v-model="adminForm.password"
              :type="showAdminPassword ? 'text' : 'password'"
              placeholder="Enter your password"
              required
            />
            <button type="button" class="toggle-visibility" @click="showAdminPassword = !showAdminPassword">
              {{ showAdminPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
        </div>

        <p v-if="errorMessage && isAdminMode" class="form-error">{{ errorMessage }}</p>

        <button type="submit" class="btn-signin" :disabled="isSubmitting">
          {{ isSubmitting ? 'Signing in…' : 'Sign In' }}
        </button>
      </form>

      <button type="button" class="back-to-user" @click="isAdminMode = false">
        ← Back to regular sign in
      </button>
    </div>
  </div>

  <!-- REGULAR LOGIN VIEW -->
  <div v-else class="login-page">
    <!-- LEFT PANEL -->
    <aside class="left-panel">
      <div class="circle circle-1"></div>
      <div class="circle circle-2"></div>
      <div class="circle circle-3"></div>
      <div class="circle circle-4"></div>
      <div class="circle circle-5"></div>

      <div class="brand">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="logo-icon" />
        <span class="logo-text">Nutri<span class="logo-match">Match</span></span>
      </div>

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

    <!-- RIGHT PANEL -->
    <main class="right-panel">
      <button class="back-link" @click="navigateTo('/')">
        ← Back to home
      </button>

      <div class="form-wrap">
        <h2>Sign in</h2>
        <p class="subtitle">Enter your credentials to access your NutriMatch account</p>

        <form class="login-form" @submit.prevent="handleLogin">
          <div class="field">
            <label>Email Address</label>
            <div class="input-icon-wrap">
              <span class="input-icon">👤</span>
              <input v-model="form.email" type="email" placeholder="blessedhope2003@email.com" required />
            </div>
          </div>

          <div class="field">
            <label>Password</label>
            <div class="input-icon-wrap">
              <span class="input-icon">🔒</span>
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="Enter your password"
                required
              />
              <button type="button" class="toggle-visibility" @click="showPassword = !showPassword">
                {{ showPassword ? 'HIDE' : 'SHOW' }}
              </button>
            </div>
          </div>

          <div class="form-options">
            <label class="remember-me">
              <input v-model="form.rememberMe" type="checkbox" />
              Remember me
            </label>
            <a href="#" class="forgot-link" @click.prevent="navigateTo('/forgot-password')">Forgot Password?</a>
          </div>

          <p v-if="errorMessage && !isAdminMode" class="form-error">{{ errorMessage }}</p>

          <button type="submit" class="btn-primary" :disabled="isSubmitting">
            {{ isSubmitting ? 'Signing in…' : 'Sign in' }}
          </button>

          <div class="divider"><span>or</span></div>

          <button type="button" class="btn-google" @click="handleGoogleLogin">
            <span class="google-icon">G</span> Sign in with Google
          </button>

          <button type="button" class="btn-admin" @click="isAdminMode = true">
            <span class="admin-icon">🛡</span> Sign in as Admin
          </button>
        </form>

        <p class="signup-link">
          Don't have an account? <a href="#" @click.prevent="navigateTo('/register')">Sign up free</a>
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
const auth = useAuthStore()

// isAdminMode toggles between the two views below — both live in this
// same component, so clicking "Sign in as Admin" just swaps what's
// rendered instead of navigating to a different route/app.
const isAdminMode = ref(false)

const showPassword = ref(false)
const form = reactive({
  email: '',
  password: '',
  rememberMe: false
})

const showAdminPassword = ref(false)
const adminForm = reactive({
  email: '',
  password: '',
})

const errorMessage = ref('')
const isSubmitting = ref(false)

const roleRedirect = {
  client: '/client-dashboard',
  rnd: '/rnd-dashboard',
  admin: '/admin-dashboard',
}

async function handleLogin() {
  errorMessage.value = ''
  isSubmitting.value = true
  try {
    const user = await auth.login(form.email, form.password)
    navigateTo(roleRedirect[user.role] || '/')
  } catch (error) {
    errorMessage.value = error?.data?.detail || 'Invalid email or password.'
  } finally {
    isSubmitting.value = false
  }
}

function handleGoogleLogin() {
  // TODO: connect to your Google OAuth flow here
  console.log('Google sign in clicked')
}

async function handleAdminLogin() {
  errorMessage.value = ''
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
    errorMessage.value = error?.data?.detail || 'Invalid email or password.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600;700&display=swap');

/* ===================== REGULAR LOGIN ===================== */
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
.circle-4 { width: 260px; height: 260px; bottom: 50%; left: 8%; }
.circle-5 { width: 180px; height: 180px; top: 40%; right: 12%; }

.brand { display: flex; align-items: center; gap: 10px; font-size: 1.3rem; font-weight: 700; position: relative; z-index: 1; font-family: 'Playfair Display', serif; }
.logo-icon { width: 50px; height: 50px; object-fit: contain; }
.logo-match { color: #D4A017; }

.left-content { margin-top: 140px; position: relative; z-index: 1; }

.eyebrow { font-size: 0.75rem; letter-spacing: 0.14em; color: #a8c4a8; font-weight: 600; }

.left-content h1 {
  font-family: 'Playfair Display', serif;
  font-style: italic;
  font-weight: 900;
  font-size: clamp(3.4rem, 4.6vw, 3.4rem);
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
.trust-badges li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.82rem;
  color: #cfe0cf;
}
.trust-badges .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #D4A017; flex-shrink: 0;
}

/* RIGHT PANEL */
.right-panel {
  background: #fff;
  padding: 90px 90px;
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
  font-weight: 700;
  font-size: 2.1rem;
  color: #1a3a1a;
  margin-bottom: 8px;
}

.subtitle { color: #8a9a8a; font-size: 0.9rem; margin-bottom: 32px; }

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

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
}
.remember-me { display: flex; align-items: center; gap: 8px; color: #4a5a4a; cursor: pointer; }
.remember-me input { width: 15px; height: 15px; cursor: pointer; }
.forgot-link { color: #1a3a1a; font-weight: 600; text-decoration: none; }
.forgot-link:hover { text-decoration: underline; }

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

.divider {
  display: flex;
  align-items: center;
  text-align: center;
  color: #a8b4a8;
  font-size: 0.8rem;
  margin: 4px 0;
}
.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid #e0e5e0;
}
.divider span { padding: 0 14px; }

.btn-google {
  width: 100%;
  background: #fff;
  border: 1px solid #dde3dd;
  color: #1a3a1a;
  padding: 14px;
  border-radius: 8px;
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: background 0.2s;
}
.btn-google:hover { background: #f7f8f7; }
.google-icon {
  font-weight: 700;
  color: #4285F4;
}

.btn-admin {
  width: 100%;
  background: #fff;
  border: 1px dashed #b9c7b9;
  color: #1a3a1a;
  padding: 14px;
  border-radius: 8px;
  font-size: 0.92rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 10px;
  transition: background 0.2s, border-color 0.2s;
}
.btn-admin:hover { background: #f7f8f7; border-color: #1a3a1a; }
.admin-icon { color: #6a8a6a; }

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

.btn-primary:disabled,
.btn-signin:disabled { opacity: 0.6; cursor: not-allowed; }

/* ===================== ADMIN PORTAL LOGIN ===================== */
.admin-login-page {
  min-height: 100vh;
  width: 100%;
  background: #0d2818;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Inter', sans-serif;
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.admin-page-circle {
  position: absolute;
  border-radius: 50%;
  background: radial-gradient(circle at 45% 40%, #0d2818, #053D2B, #0d2818 100%);
  box-shadow: #0d2818 10px 20px 10px 100px;
  pointer-events: none;
}
.admin-circle-1 { width: 420px; height: 420px; top: -140px; right: -100px; }
.admin-circle-2 { width: 380px; height: 380px; bottom: -220px; right: 8%; }
.admin-circle-3 { width: 460px; height: 460px; bottom: -260px; left: -140px; }

.admin-page-brand {
  position: absolute;
  top: 40px;
  left: 56px;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 15px;
}
.admin-page-logo-icon { width: 40px; height: 34px; object-fit: contain; }
.admin-page-logo-text {
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: 1.3rem;
  color: #ffffff;
}

.admin-card {
  position: relative;
  z-index: 2;
  background: #fdfdf8;
  border-radius: 30px;
  padding: 40px 48px 48px;
  width: 100%;
  max-width: 500px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
}

.admin-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 4px;
}

.admin-logo-icon { width: 26px; height: 26px; object-fit: contain; }

.admin-logo-text {
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: 1.3rem;
  color: #1a3a1a;
}

.admin-tagline {
  font-size: 0.62rem;
  letter-spacing: 0.18em;
  color: #9aab9a;
  margin-bottom: 28px;
}

.admin-card h1 {
  font-family: 'Playfair Display', serif;
  font-weight: 700;
  font-size: 1.5rem;
  color: #1a3a1a;
  margin-bottom: 6px;
}

.admin-subtitle {
  font-size: 0.85rem;
  color: #8a9a8a;
  margin-bottom: 28px;
}

.admin-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  text-align: left;
}

.btn-signin {
  width: 100%;
  background: #1a3a1a;
  color: #fff;
  border: none;
  padding: 14px;
  border-radius: 8px;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
  margin-top: 6px;
  transition: background 0.2s;
}
.btn-signin:hover { background: #14300f; }

.back-to-user {
  background: none;
  border: none;
  cursor: pointer;
  color: #8a9a8a;
  font-size: 0.8rem;
  margin-top: 20px;
}
.back-to-user:hover { color: #1a3a1a; }

@media (max-width: 900px) {
  .login-page { grid-template-columns: 1fr; }
  .left-panel { padding: 32px; min-height: 280px; }
  .left-content { margin-top: 32px; }
  .right-panel { padding: 32px; }
  .form-wrap { margin-top: 32px; }
  .trust-badges { margin-top: 24px; }
}

@media (max-width: 500px) {
  .admin-card { padding: 32px 28px 36px; }
}
</style>