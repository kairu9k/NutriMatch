<template>
  <div class="nm-page prof">
    <!-- hero: cover + who you are -->
    <section class="ps-hero">
      <div class="ps-cover">
        <img class="ps-cover-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="ps-cover-fade" aria-hidden="true"></span>
        <p class="ps-cover-k"><span aria-hidden="true"></span>My profile</p>
      </div>
      <div class="ps-id">
        <img v-if="auth.user?.profile_photo" :src="auth.user.profile_photo" class="ps-avatar" alt="" />
        <span v-else class="ps-avatar" aria-hidden="true">{{ myInitials }}</span>
        <div class="ps-id-main">
          <h1 class="ps-name">{{ myName }}</h1>
          <div class="ps-chips">
            <span class="ps-chip role"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /></svg>Admin</span>
            <span v-if="auth.user?.email" class="ps-chip"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg>{{ auth.user.email }}</span>
            <span class="ps-chip"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>Signs in with email</span>
          </div>
        </div>
      </div>
    </section>

    <div class="ps-layout">
      <div class="ps-main">
        <section id="ap-details" class="nm-panel ps-card">
          <div class="nm-panel-head ps-card-head">
            <span class="ps-card-ico green" aria-hidden="true"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 12a4 4 0 1 0 0-8a4 4 0 0 0 0 8z" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg></span>
            <div>
              <h2 class="nm-panel-title">Your details</h2>
              <p class="nm-panel-sub">Shown in the audit log and on support replies other admins see.</p>
            </div>
          </div>
          <form class="grid" @submit.prevent="saveDetails">
            <label class="field"><span class="nm-label">First name</span>
              <span class="inp"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 12a4 4 0 1 0 0-8a4 4 0 0 0 0 8z" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg><input v-model="details.first_name" class="nm-input" maxlength="150" /></span>
              <small v-if="detailErrors.first_name" class="nm-field-error">{{ detailErrors.first_name }}</small></label>
            <label class="field"><span class="nm-label">Last name</span>
              <span class="inp"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 12a4 4 0 1 0 0-8a4 4 0 0 0 0 8z" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg><input v-model="details.last_name" class="nm-input" maxlength="150" /></span>
              <small v-if="detailErrors.last_name" class="nm-field-error">{{ detailErrors.last_name }}</small></label>
            <label class="field"><span class="nm-label">Email</span>
              <span class="inp locked"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg><input :value="auth.user?.email" class="nm-input" disabled /><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg></span></label>
            <div class="field"><label for="ap-phone" class="nm-label">Mobile number</label>
              <PhoneInput id="ap-phone" v-model="details.phone" label="mobile number" :error="detailErrors.phone" /></div>
            <p class="ps-lock"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg><span>Your email is your sign-in. To change it, ask another admin to use <b>Edit details</b> on your account in Users.</span></p>
            <div class="actions">
              <p v-if="detailErrors.detail" class="nm-error">{{ detailErrors.detail }}</p>
              <button type="submit" class="nm-btn-dark" :disabled="savingDetails || !detailsChanged"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>{{ savingDetails ? 'Saving…' : 'Save details' }}</button>
            </div>
          </form>
        </section>

        <section id="ap-password" class="nm-panel ps-card">
          <div class="nm-panel-head ps-card-head">
            <span class="ps-card-ico gold" aria-hidden="true"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 15a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M10.8 12.2L20 3M17 6l3 3M15 8l2 2" /></svg></span>
            <div>
              <h2 class="nm-panel-title">Change password</h2>
              <p class="nm-panel-sub">You'll get an email confirming the change. Forgot it? Sign out and use Forgot password instead.</p>
            </div>
          </div>
          <form class="pw" @submit.prevent="changePassword">
            <label class="field"><span class="nm-label">Current password</span>
              <span class="inp"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg><input v-model="pw.current" :type="showPw ? 'text' : 'password'" class="nm-input" autocomplete="current-password" /></span>
              <small v-if="pwErrors.current_password" class="nm-field-error">{{ pwErrors.current_password }}</small></label>
            <label class="field"><span class="nm-label">New password</span>
              <span class="inp"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 15a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M10.8 12.2L20 3M17 6l3 3M15 8l2 2" /></svg><input v-model="pw.next" :type="showPw ? 'text' : 'password'" class="nm-input" autocomplete="new-password" /></span>
              <small v-if="pwErrors.new_password" class="nm-field-error">{{ pwErrors.new_password }}</small></label>
            <ul class="rules" aria-label="Password rules">
              <li v-for="r in rules" :key="r.label" :class="{ ok: r.ok }"><Check v-if="r.ok" :size="12" /><span v-else class="dot" />{{ r.label }}</li>
            </ul>
            <label class="field"><span class="nm-label">Confirm new password</span>
              <span class="inp"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 15a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M10.8 12.2L20 3M17 6l3 3M15 8l2 2" /></svg><input v-model="pw.confirm" :type="showPw ? 'text' : 'password'" class="nm-input" autocomplete="new-password" /></span>
              <small v-if="pw.confirm && pw.confirm !== pw.next" class="nm-field-error">The passwords don't match.</small></label>
            <label class="show"><input v-model="showPw" type="checkbox" /><span class="sw" aria-hidden="true"><i></i></span> Show passwords</label>
            <p v-if="pwErrors.detail" class="nm-error">{{ pwErrors.detail }}</p>
            <div class="actions">
              <button type="submit" class="nm-btn-dark" :disabled="savingPw || !canChange"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 15a4 4 0 1 0 8 0a4 4 0 1 0 -8 0" /><path d="M10.8 12.2L20 3M17 6l3 3M15 8l2 2" /></svg>{{ savingPw ? 'Changing…' : 'Change password' }}</button>
            </div>
          </form>
        </section>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
// The signed-in admin's own profile: name/phone (PATCH /api/auth/me/) and
// password (POST /api/auth/me/password/, accounts/admin_accounts.py).
import { Check, CheckCircle2 } from 'lucide-vue-next'

const auth = useAuthStore()
const { patch, post } = useApi()
const toast = useToast() // the app's toast (2026-11-03)
function flash(msg, opts) {
  toast.success(msg, opts)
}
function fieldErrors(e) {
  const d = e?.data || {}
  const out = Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]))
  return Object.keys(out).length ? out : { detail: apiError(e) }
}

/* ---------- details ---------- */
const details = reactive({ first_name: '', last_name: '', phone: '' })
const detailErrors = ref({})
const savingDetails = ref(false)
const original = computed(() => ({ first_name: auth.user?.first_name || '', last_name: auth.user?.last_name || '', phone: auth.user?.phone || '' }))
watch(original, o => Object.assign(details, o), { immediate: true })
const detailsChanged = computed(() => Object.keys(original.value).some(k => (details[k] || '').trim() !== original.value[k]))
async function saveDetails() {
  detailErrors.value = {}
  const phoneMsg = phoneError(details.phone)
  if (phoneMsg) { detailErrors.value = { phone: phoneMsg }; return }
  savingDetails.value = true
  try {
    await patch('/auth/me/', { first_name: details.first_name.trim(), last_name: details.last_name.trim(), phone: details.phone || null })
    await auth.fetchMe()
    flash('Details saved.')
  } catch (e) {
    detailErrors.value = fieldErrors(e)
  } finally {
    savingDetails.value = false
  }
}

/* ---------- password (rules mirror PasswordComplexityValidator) ---------- */
const pw = reactive({ current: '', next: '', confirm: '' })
const pwErrors = ref({})
const savingPw = ref(false)
const showPw = ref(false)
const rules = computed(() => [
  { label: 'At least 8 characters', ok: pw.next.length >= 8 },
  { label: 'An uppercase letter', ok: /[A-Z]/.test(pw.next) },
  { label: 'A lowercase letter', ok: /[a-z]/.test(pw.next) },
  { label: 'A number', ok: /\d/.test(pw.next) },
  { label: 'A special character', ok: /[^A-Za-z0-9]/.test(pw.next) },
])
const canChange = computed(() => pw.current && rules.value.every(r => r.ok) && pw.next === pw.confirm)
async function changePassword() {
  pwErrors.value = {}
  savingPw.value = true
  try {
    await post('/auth/me/password/', { current_password: pw.current, new_password: pw.next })
    Object.assign(pw, { current: '', next: '', confirm: '' })
    flash('Password changed. We emailed you a confirmation.')
  } catch (e) {
    pwErrors.value = fieldErrors(e)
  } finally {
    savingPw.value = false
  }
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const myName = computed(() => `${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim() || 'My profile')
const myInitials = computed(() => `${(auth.user?.first_name || '?')[0]}${(auth.user?.last_name || '')[0] || ''}`.toUpperCase())
</script>

<style scoped>
.prof { --sh: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); display: flex; flex-direction: column; gap: 22px; font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; display: inline-block; }

/* ---------- hero ---------- */
.ps-hero { border-radius: 24px; box-shadow: var(--sh); }
.ps-cover { position: relative; overflow: hidden; height: 150px; border-radius: 24px 24px 0 0; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); }
.ps-cover-plate { position: absolute; right: -60px; top: 50%; width: 380px; height: 380px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.55; pointer-events: none; }
.ps-cover-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004d3a 0%, #004d3a 45%, rgba(0, 77, 58, 0.7) 65%, rgba(0, 70, 52, 0.1) 100%); }
.ps-cover-k { position: relative; z-index: 1; display: flex; align-items: center; gap: 10px; margin: 0; padding: 26px 34px; font-size: 12.5px; font-weight: 800; color: #efbf04; }
.ps-cover-k span { width: 26px; height: 2px; border-radius: 2px; background: #efbf04; }
.ps-id { position: relative; display: flex; flex-wrap: wrap; align-items: flex-end; gap: 24px; padding: 0 34px 26px; border: 1px solid #e4ebe6; border-top: none; border-radius: 0 0 24px 24px; background: #fff; }
.ps-avatar { flex-shrink: 0; width: 124px; height: 124px; margin-top: -58px; border-radius: 50%; object-fit: cover; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f5cb1f, #c49102); color: #004d3a; font-family: 'Playfair Display', Georgia, serif; font-size: 40px; font-weight: 700; border: 6px solid #fff; box-shadow: 0 18px 34px -18px rgba(0, 0, 0, 0.5); box-sizing: border-box; }
.ps-id-main { flex: 1; min-width: 0; padding-top: 16px; }
.ps-name { margin: 0 0 10px; font-family: 'Playfair Display', Georgia, serif; font-size: 30px; font-weight: 700; line-height: 1.2; color: #0e3a2c; }
.ps-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.ps-chip { display: inline-flex; align-items: center; gap: 7px; height: 32px; padding: 0 12px; border-radius: 999px; background: #f3f6f4; font-size: 13px; font-weight: 600; color: #3e5046; overflow-wrap: anywhere; }
.ps-chip .ic { color: #1f7a4d; }
.ps-chip.role { background: #fbf3d2; color: #8a6400; }
.ps-chip.role .ic { color: #9a7300; }

/* ---------- layout ---------- */
.ps-layout { display: block; }
.ps-main { display: grid; grid-template-columns: minmax(0, 1.3fr) minmax(0, 1fr); gap: 20px; align-items: stretch; min-width: 0; }
.ps-card { display: flex; flex-direction: column; }
.ps-card form { flex: 1; }
.pw .actions { margin-top: auto; }
.ps-card { margin: 0; padding: 24px 26px; border: 1px solid #e4ebe6; border-radius: 22px; background: #fff; box-shadow: var(--sh); scroll-margin-top: 96px; }
.ps-card-head { display: flex; align-items: center; gap: 14px; margin: 0 0 20px; padding: 0; border: none; }
.ps-card-head > div { flex: 1; min-width: 0; }
.ps-card-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; }
.ps-card-ico.green { background: #e3efe7; color: #004d3a; }
.ps-card-ico.gold { background: #fbf3d2; color: #9a7300; }
.ps-card-head .nm-panel-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-weight: 700; color: #0e3a2c; }
.ps-card-head .nm-panel-sub { margin: 4px 0 0; font-size: 13.5px; line-height: 1.5; color: #6b7d73; }

/* ---------- fields ---------- */
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; align-content: start; }
.pw { display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 7px; min-width: 0; }
.field .nm-label { margin: 0; font-size: 13px; font-weight: 700; color: #22362c; }
.inp { display: flex; align-items: center; gap: 10px; height: 48px; padding: 0 14px; border: 1.5px solid #c9d8cf; border-radius: 14px; background: #fff; color: #8a9a91; box-sizing: border-box; transition: border-color 0.15s, box-shadow 0.15s; }
.inp:focus-within { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); color: #1f7a4d; }
.inp input.nm-input { flex: 1; min-width: 0; height: 100%; min-height: 0; margin: 0; padding: 0 !important; border: none !important; border-radius: 0; background: transparent !important; box-shadow: none !important; outline: none; font-family: inherit; font-size: 14.5px; color: #14261e; }
.inp.locked { border-color: #e3ebe6; background: #f3f6f4; }
.inp.locked input.nm-input { color: #6b7d73; cursor: not-allowed; }
.field :deep(input), .field :deep(select) { min-height: 48px; border-radius: 14px; }
.ps-lock { grid-column: 1 / -1; display: flex; align-items: flex-start; gap: 10px; margin: 0; padding: 12px 14px; border-radius: 14px; background: #eef1fa; font-size: 13px; line-height: 1.5; color: #2e4a86; }
.ps-lock .ic { margin-top: 2px; }
.actions { grid-column: 1 / -1; display: flex; justify-content: flex-end; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 4px; padding-top: 16px; border-top: 1px solid #eef2ef; }
.pw .actions { justify-content: flex-end; }
.actions .nm-error { flex: 1; margin: 0; }
.prof .nm-btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 46px; padding: 0 22px; border: none; border-radius: 12px; background: #004d3a; color: #fff; font-family: inherit; font-size: 14px; font-weight: 800; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); cursor: pointer; }
.prof .nm-btn-dark .ic { color: #efbf04; }
.prof .nm-btn-dark:disabled { opacity: 0.45; box-shadow: none; cursor: not-allowed; }

/* password rules: chips that turn green */
.rules { display: flex; flex-wrap: wrap; gap: 6px; margin: -4px 0 0; padding: 0; list-style: none; }
.rules li { display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px; border-radius: 999px; background: #f3f6f4; font-size: 12.5px; font-weight: 600; color: #6b7d73; transition: background 0.15s, color 0.15s; }
.rules li.ok { background: #e3f4ea; color: #1f7a4d; }
.rules .dot { width: 6px; height: 6px; margin: 0 3px; border: 1.5px solid #a9b6ae; border-radius: 50%; }

/* show passwords: a switch */
.show { position: relative; display: inline-flex; align-items: center; gap: 10px; align-self: flex-start; font-size: 13.5px; font-weight: 600; color: #22362c; cursor: pointer; }
.show input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.sw { position: relative; width: 40px; height: 22px; border-radius: 999px; background: #c9d8cf; transition: background 0.15s; }
.sw i { position: absolute; left: 3px; top: 3px; width: 16px; height: 16px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2); transition: transform 0.15s; }
.show input:checked + .sw { background: #004d3a; }
.show input:checked + .sw i { transform: translateX(18px); background: #efbf04; }
.show input:focus-visible + .sw { outline: 2px solid #1f8f5c; outline-offset: 2px; }

@media (max-width: 1100px) {
  .ps-main { grid-template-columns: minmax(0, 1fr); }
    }
@media (max-width: 760px) {
  .prof { padding-bottom: 110px; }
  .ps-cover { height: 110px; border-radius: 22px 22px 0 0; }
  .ps-cover-plate { width: 200px; height: 200px; right: -50px; }
  .ps-cover-k { padding: 20px 18px; }
  .ps-id { flex-direction: column; align-items: center; gap: 12px; padding: 0 18px 20px; border-radius: 0 0 22px 22px; text-align: center; }
  .ps-avatar { width: 104px; height: 104px; margin-top: -52px; font-size: 32px; border-width: 5px; }
  .ps-id-main { padding-top: 0; }
  .ps-name { font-size: 24px; }
  .ps-chips { justify-content: center; }
  .ps-card { padding: 20px 18px; }
  .grid { grid-template-columns: minmax(0, 1fr); }
  .actions .nm-btn-dark { width: 100%; }
}
</style>