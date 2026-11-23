<template>
  <!-- ADMIN LOG IN (/admin/login): blurred plate photo as the page, one white card -->
  <div v-if="isAdminMode" class="nm-admin">
    <img class="nm-admin-bg" :src="plateImg" alt="" aria-hidden="true" />
    <div class="nm-admin-shade" aria-hidden="true"></div>

    <NuxtLink to="/" class="nm-brand nm-admin-brand" aria-label="NutriMatch home">
      <img src="/resources/nutrimatchlogo.png" alt="" class="nm-brand-logo" />
      <span class="nm-brand-text">Nutri<span>Match</span></span>
    </NuxtLink>

    <div class="nm-box nm-admin-box">
      <NuxtLink to="/" class="nm-back nm-admin-back"><ArrowLeft :size="15" aria-hidden="true" /> Back to home</NuxtLink>
      <h1 class="nm-title">Admin log in</h1>
      <p class="nm-subtitle">For the NutriMatch team. Clients and RNDs log in on the main page.</p>

      <form class="nm-form" @submit.prevent="handleAdminLogin">
        <div class="nm-field">
          <label for="admin-email">Email address</label>
          <div class="nm-input">
            <User class="nm-input-icon" aria-hidden="true" />
            <input id="admin-email" v-model="adminForm.email" type="email" autocomplete="username" placeholder="you@nutrimatch.ph" required />
          </div>
        </div>

        <div class="nm-field">
          <label for="admin-password">Password</label>
          <div class="nm-input">
            <Lock class="nm-input-icon" aria-hidden="true" />
            <input
              id="admin-password"
              v-model="adminForm.password"
              :type="showAdminPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="Your password"
              required
            />
            <button type="button" class="nm-eye" :aria-label="showAdminPassword ? 'Hide password' : 'Show password'" @click="showAdminPassword = !showAdminPassword">
              <EyeOff v-if="showAdminPassword" :size="18" aria-hidden="true" /><Eye v-else :size="18" aria-hidden="true" />
            </button>
          </div>
        </div>

        <div v-if="deactivated && isAdminMode" class="nm-error nm-deactivated" role="alert">
          <p class="nm-deactivated-title">Your account has been deactivated</p>
          <p>The NutriMatch admin deactivated this account, so you can't sign in right now. If you think this is a mistake, email us to request a review.</p>
          <a :href="deactivatedMailto" class="nm-deactivated-link">{{ deactivated }}</a>
        </div>
        <p v-else-if="errorMessage && isAdminMode" class="nm-error" role="alert">{{ errorMessage }}</p>
        <p v-if="loginNote && !errorMessage && !deactivated" class="nm-note">{{ loginNote }}</p>

        <button type="submit" class="nm-submit" :disabled="isSubmitting" :aria-busy="isSubmitting">
          <span v-if="isSubmitting" class="nm-spin" aria-hidden="true"></span>
          {{ isSubmitting ? 'Logging in…' : 'Log in' }}
        </button>
      </form>
    </div>
  </div>

  <!-- CLIENT / RND LOG IN -->
  <div v-else class="nm-auth">
    <!-- LEFT: photo -->
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
          <span class="nm-eyebrow"><span class="nm-eyebrow-line" aria-hidden="true"></span>WELCOME BACK</span>
          <h1 class="nm-hero">Your health journey <em>continues</em> here.</h1>
          <p class="nm-desc">Your dashboard, meal plans and consultation records, right where you left them.</p>
          <span class="nm-rule" aria-hidden="true"></span>
        </div>
      </div>
    </aside>

    <!-- RIGHT: form -->
    <main class="nm-right">
      <div class="nm-dots nm-dots-top" aria-hidden="true"></div>
      <div class="nm-dots nm-dots-bottom" aria-hidden="true"></div>
      <div class="nm-right-top">
        <NuxtLink to="/" class="nm-back"><ArrowLeft :size="15" aria-hidden="true" /> Back to home</NuxtLink>
      </div>

      <!-- phone / tablet only: the photo panel is hidden, so the brand shows here -->
      <NuxtLink to="/" class="nm-mobile-brand" aria-label="NutriMatch home">
        <img src="/resources/nutrimatchlogo.png" alt="" class="nm-mobile-logo" />
        <span class="nm-mobile-text">Nutri<span>Match</span></span>
      </NuxtLink>

      <div class="nm-box-wrap">
        <div class="nm-box">
          <header class="nm-head">
            <h2 class="nm-title">Log in</h2>
            <p class="nm-subtitle">Use the email and password you signed up with.</p>
          </header>

          <form class="nm-form" @submit.prevent="handleLogin">
            <div class="nm-field">
              <label for="login-email">Email address</label>
              <div class="nm-input">
                <User class="nm-input-icon" aria-hidden="true" />
                <input id="login-email" v-model="form.email" type="email" autocomplete="username" placeholder="you@example.com" required />
              </div>
            </div>

            <div class="nm-field">
              <label for="login-password">Password</label>
              <div class="nm-input">
                <Lock class="nm-input-icon" aria-hidden="true" />
                <input
                  id="login-password"
                  v-model="form.password"
                  :type="showPassword ? 'text' : 'password'"
                  autocomplete="current-password"
                  placeholder="Your password"
                  required
                />
                <button type="button" class="nm-eye" :aria-label="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword">
                  <EyeOff v-if="showPassword" :size="18" aria-hidden="true" /><Eye v-else :size="18" aria-hidden="true" />
                </button>
              </div>
            </div>

            <div class="nm-options">
              <label class="nm-remember">
                <input v-model="form.rememberMe" type="checkbox" />
                Remember me
              </label>
              <NuxtLink to="/forgot-password" class="nm-link">Forgot password?</NuxtLink>
            </div>

            <div v-if="deactivated && !isAdminMode" class="nm-error nm-deactivated" role="alert">
              <p class="nm-deactivated-title">Your account has been deactivated</p>
              <p>The NutriMatch admin deactivated this account, so you can't sign in right now. If you think this is a mistake, email us to request a review.</p>
              <a :href="deactivatedMailto" class="nm-deactivated-link">{{ deactivated }}</a>
            </div>
            <p v-else-if="errorMessage && !isAdminMode" class="nm-error" role="alert">{{ errorMessage }}</p>
            <p v-if="loginNote && !errorMessage && !deactivated" class="nm-note">{{ loginNote }}</p>

            <button type="submit" class="nm-submit" :disabled="isSubmitting" :aria-busy="isSubmitting">
              <span v-if="isSubmitting" class="nm-spin" aria-hidden="true"></span>
              {{ isSubmitting ? 'Logging in…' : 'Log in' }}
            </button>
          </form>

          <p class="nm-signup">
            New to NutriMatch? <NuxtLink to="/register" class="nm-link">Create an account</NuxtLink>
          </p>
        </div>
      </div>

      <p class="nm-foot">© 2026 NutriMatch</p>
    </main>
  </div>
</template>

<script setup>
import { ArrowLeft, Eye, EyeOff, Lock, User } from 'lucide-vue-next'
const auth = useAuthStore()

// UI only: the plate photo (public/landing/login-plate.webp)
const plateImg = '/landing/login-plate.webp'
// UI only: Go / Grow / Glow labels placed on the plate photo
const platePins = [
  { tag: 'GO', label: 'Whole grains', share: '¼', x: '34%', y: '22%', side: 'to-right' },
  { tag: 'GROW', label: 'Protein', share: '¼', x: '63%', y: '35%', side: 'to-right' },
  { tag: 'GLOW', label: 'Vegetables', share: '½', x: '80%', y: '57%', side: 'to-left' },
]

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
// Sent here because the session ended (composables/useApi.ts)
// or after a password reset (ForgotPassword.vue)
const loginNote = useRoute().query.expired === '1' ? 'Your session ended. Please sign in again.'
  : useRoute().query.reset === '1' ? 'Your password was changed. Sign in with your new password.' : ''
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

<style scoped>
/* =========================================================
   NutriMatch log in: brand #063C2A / #EFBF04 / white
   Fonts: Playfair Display (headings), DM Sans (body)
   ========================================================= */
.nm-auth,
.nm-admin {
  font-family: 'DM Sans', Arial, sans-serif;
  color: #14261E;
  -webkit-font-smoothing: antialiased;
}

/* ---------- page layout ---------- */
.nm-auth {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(0, 1fr);
  min-height: 100vh;
  min-height: 100dvh;
  background: #FFFFFF;
}

/* ---------- LEFT: photo ---------- */
.nm-left {
  position: sticky;
  top: 0;
  align-self: start;
  height: 100vh;
  height: 100dvh;
  min-height: 640px;
  overflow: hidden;
  background: #063C2A;
  color: #FFFFFF;
}
/* the photo sits in a square so the labels stay on the food */
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
    rgba(4, 41, 29, 0) 40%,
    rgba(4, 41, 29, 0.55) 56%,
    rgba(4, 41, 29, 0.88) 72%,
    rgba(4, 41, 29, 0.97) 100%);
}
.nm-left-vignette {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, rgba(4, 41, 29, 0.40) 0%, rgba(4, 41, 29, 0) 55%),
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

.nm-left-inner {
  position: relative;
  height: 100%;
  box-sizing: border-box;
  padding: 28px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

/* brand */
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

/* welcome text */
.nm-welcome {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: 480px;
  margin: 0 0 64px 32px;
}
.nm-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 3px;
  color: #EFBF04;
  margin-bottom: 14px;
}
.nm-eyebrow-line {
  width: 36px;
  height: 2px;
  border-radius: 2px;
  background: #EFBF04;
}
.nm-rule {
  display: block;
  width: 100%;
  max-width: 420px;
  height: 1px;
  margin-top: 10px;
  background: linear-gradient(90deg, rgba(239, 191, 4, 0.7), rgba(239, 191, 4, 0));
}
.nm-hero {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-style: italic;
  font-size: clamp(34px, 3.6vw, 50px);
  line-height: 1.08;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #FFFFFF;
  text-shadow: 0 2px 18px rgba(0, 0, 0, 0.45);
}
/* guard against global h1 / em styles from other pages */
.nm-auth .nm-hero {
  display: block;
  width: auto;
  max-width: 100%;
  padding: 0;
  border: none;
  border-radius: 0;
  background: none;
  box-shadow: none;
  text-align: left;
}
.nm-hero em {
  display: inline;
  margin: 0;
  padding: 0;
  border: none;
  border-radius: 0;
  background: none;
  box-shadow: none;
  font-style: italic;
  color: #EFBF04;
}
.nm-desc {
  margin: 0;
  font-size: 16px;
  line-height: 1.65;
  color: rgba(255, 255, 255, 0.92);
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.5);
}

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
.nm-right > * { position: relative; z-index: 1; }
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
.nm-back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 14px 0 10px;
  border-radius: 999px;
  background: #F1F6F2;
  color: #063C2A;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: background-color .15s;
}
.nm-back:hover { background: #E5EFE8; }

.nm-mobile-brand { display: none; }
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
  padding: 56px 52px 44px;
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.03),
    0 0 12px rgba(0, 0, 0, 0.08),
    0 0 32px rgba(0, 0, 0, 0.10),
    0 8px 40px rgba(0, 0, 0, 0.12);
}
.nm-head {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 36px;
}
.nm-title {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 44px;
  line-height: 1.05;
  font-weight: 700;
  color: #10231B;
}
.nm-subtitle {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: #55665D;
}

/* form */
.nm-form {
  display: flex;
  flex-direction: column;
  gap: 22px;
  margin: 0;
}
.nm-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.nm-field label {
  font-size: 13px;
  font-weight: 600;
  color: #22362C;
}
.nm-input {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 56px;
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
.nm-input-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: #7A8F84;
}
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
.nm-input input:-webkit-autofill,
.nm-input input:-webkit-autofill:hover,
.nm-input input:-webkit-autofill:focus {
  -webkit-text-fill-color: #14261E;
  -webkit-box-shadow: 0 0 0 1000px #F7FAF8 inset;
  transition: background-color 9999s ease-out 0s;
}
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
  transition: background-color .15s, color .15s;
}
.nm-eye:hover { background: #EEF3EF; color: #063C2A; }

.nm-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.nm-remember {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: #3E5046;
  cursor: pointer;
  min-height: 24px;
}
.nm-remember input {
  width: 18px;
  height: 18px;
  margin: 0;
  accent-color: #063C2A;
  cursor: pointer;
}
.nm-link {
  font-size: 14px;
  font-weight: 700;
  color: #063C2A;
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-thickness: 1.5px;
  text-decoration-color: rgba(196, 145, 2, .7);
}
.nm-link:hover { text-decoration-color: #063C2A; }

/* messages */
.nm-error {
  margin: 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: #FEF3F2;
  border: 1px solid #FECDCA;
  color: #B42318;
  font-size: 14px;
  line-height: 1.5;
}
.nm-note {
  margin: 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: #FFF8E1;
  border: 1px solid #F5DE8A;
  color: #6B5200;
  font-size: 14px;
  line-height: 1.5;
}
.nm-deactivated p { margin: 0 0 6px; line-height: 1.5; }
.nm-deactivated-title { font-weight: 700; }
.nm-deactivated-link {
  font-weight: 700;
  color: inherit;
  text-decoration: underline;
  word-break: break-all;
}

/* submit */
.nm-submit {
  margin-top: 8px;
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
.nm-submit:hover:not(:disabled) {
  background: #0A4F38;
  box-shadow: 0 16px 28px -14px rgba(6, 60, 42, .9);
}
.nm-submit:active:not(:disabled) { transform: scale(.99); }
.nm-submit:disabled { opacity: .85; cursor: progress; }
.nm-spin {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2.5px solid rgba(239, 191, 4, 0.3);
  border-top-color: #EFBF04;
  animation: nm-spin .8s linear infinite;
}
@keyframes nm-spin { to { transform: rotate(360deg); } }

.nm-signup {
  margin: 30px 0 0;
  text-align: center;
  font-size: 14px;
  color: #55665D;
}
.nm-foot {
  margin: 0;
  font-size: 12px;
  color: #7A8F84;
}

/* focus ring */
.nm-auth a:focus-visible,
.nm-auth button:focus-visible,
.nm-auth input[type=checkbox]:focus-visible,
.nm-admin a:focus-visible,
.nm-admin button:focus-visible {
  outline: 3px solid #EFBF04;
  outline-offset: 2px;
}

/* ---------- ADMIN ---------- */
.nm-admin {
  position: relative;
  overflow: hidden;
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 32px 16px;
  box-sizing: border-box;
  background: #063C2A;
}
.nm-admin-bg {
  position: absolute;
  inset: -40px;
  width: calc(100% + 80px);
  height: calc(100% + 80px);
  object-fit: cover;
  filter: blur(18px) saturate(1.1);
}
.nm-admin-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(3, 30, 21, 0.82), rgba(3, 30, 21, 0.9));
}
.nm-admin-brand,
.nm-admin-box { position: relative; z-index: 1; }
.nm-admin-brand { align-self: center; }
.nm-admin-back { margin-bottom: 28px; }
.nm-admin-box .nm-title { font-size: 34px; margin-bottom: 8px; }
.nm-admin-box .nm-subtitle { margin-bottom: 28px; }

/* ---------- tablet + phone: only the log in rectangle ---------- */
@media (max-width: 960px) {
  .nm-auth { grid-template-columns: 1fr; }
  .nm-left { display: none; }
  .nm-right > .nm-dots { display: none; }
  .nm-right {
    min-height: 100vh;
    min-height: 100dvh;
    padding: 24px;
  }
  .nm-mobile-brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    align-self: center;
    order: 1;
    margin-top: 12px;
    text-decoration: none;
  }
  .nm-right-top {
    order: 2;
    display: flex;
    justify-content: flex-start;
    margin-top: 40px;
  }
  .nm-box-wrap { order: 3; }
  .nm-foot { order: 4; }
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
    letter-spacing: 0.2px;
    color: #063C2A;
  }
  .nm-mobile-text span { color: #C49102; }
  .nm-box-wrap { align-items: flex-start; padding: 28px 0 32px; }
  .nm-box { padding: 40px 36px 32px; }
  .nm-foot { text-align: center; }
}

@media (max-width: 600px) {
  .nm-right { padding: 16px 16px 20px; }
  .nm-mobile-brand { margin-top: 8px; }
  .nm-mobile-text { font-size: 26px; }
  .nm-box-wrap { padding: 24px 0; }
  .nm-box { padding: 30px 20px 24px; border-radius: 14px; }
  .nm-title { font-size: 34px; }
  .nm-admin-box .nm-title { font-size: 28px; }
  .nm-head { margin-bottom: 28px; }
  .nm-form { gap: 18px; }
  .nm-input { height: 54px; }
  .nm-input input { font-size: 16px; } /* stops iPhone zoom on tap */
  .nm-submit { height: 54px; }
}

@media (max-width: 360px) {
  .nm-box { padding: 24px 16px 20px; }
  .nm-title { font-size: 30px; }
}

@media (prefers-reduced-motion: reduce) {
  .nm-spin { animation: none; }
  .nm-dot::after { animation: none; opacity: 0; }
  .nm-tag { animation: none; }
}

/* bigger log-in card */
.nm-box { max-width: 620px !important; padding: 64px 60px 52px !important; border-radius: 24px; }
.nm-box h1, .nm-box .nm-title { font-size: 52px; }
.nm-box input { min-height: 60px; font-size: 16px; }
@media (max-width: 960px) { .nm-box { padding: 44px 32px 36px !important; } }
@media (max-width: 600px) { .nm-box { padding: 32px 22px 28px !important; } .nm-box h1, .nm-box .nm-title { font-size: 38px; } }
</style>