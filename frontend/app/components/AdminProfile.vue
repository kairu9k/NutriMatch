<template>
  <div class="nm-page prof">
    <section class="nm-panel">
      <div class="nm-panel-head">
        <div>
          <h2 class="nm-panel-title">Your details</h2>
          <p class="nm-panel-sub">Shown in the audit log and on support replies other admins see. Your email is your sign-in — ask another admin to change it (Users → Edit details).</p>
        </div>
      </div>
      <form class="grid" @submit.prevent="saveDetails">
        <label class="field"><span class="nm-label">First name</span>
          <input v-model="details.first_name" class="nm-input" maxlength="150" />
          <small v-if="detailErrors.first_name" class="nm-field-error">{{ detailErrors.first_name }}</small></label>
        <label class="field"><span class="nm-label">Last name</span>
          <input v-model="details.last_name" class="nm-input" maxlength="150" />
          <small v-if="detailErrors.last_name" class="nm-field-error">{{ detailErrors.last_name }}</small></label>
        <label class="field"><span class="nm-label">Email</span>
          <input :value="auth.user?.email" class="nm-input" disabled /></label>
        <label class="field"><span class="nm-label">Phone</span>
          <input v-model="details.phone" type="tel" class="nm-input" maxlength="20" placeholder="0917 123 4567" />
          <small v-if="detailErrors.phone" class="nm-field-error">{{ detailErrors.phone }}</small></label>
        <div class="actions">
          <p v-if="detailErrors.detail" class="nm-error">{{ detailErrors.detail }}</p>
          <button type="submit" class="nm-btn-dark" :disabled="savingDetails || !detailsChanged">{{ savingDetails ? 'Saving…' : 'Save details' }}</button>
        </div>
      </form>
    </section>

    <section class="nm-panel">
      <div class="nm-panel-head">
        <div>
          <h2 class="nm-panel-title">Change password</h2>
          <p class="nm-panel-sub">You'll get an email confirming the change. Forgot it? Sign out and use Forgot password instead.</p>
        </div>
      </div>
      <form class="pw" @submit.prevent="changePassword">
        <label class="field"><span class="nm-label">Current password</span>
          <input v-model="pw.current" :type="showPw ? 'text' : 'password'" class="nm-input" autocomplete="current-password" />
          <small v-if="pwErrors.current_password" class="nm-field-error">{{ pwErrors.current_password }}</small></label>
        <label class="field"><span class="nm-label">New password</span>
          <input v-model="pw.next" :type="showPw ? 'text' : 'password'" class="nm-input" autocomplete="new-password" />
          <small v-if="pwErrors.new_password" class="nm-field-error">{{ pwErrors.new_password }}</small></label>
        <ul class="rules" aria-label="Password rules">
          <li v-for="r in rules" :key="r.label" :class="{ ok: r.ok }"><Check v-if="r.ok" :size="12" /><span v-else class="dot" />{{ r.label }}</li>
        </ul>
        <label class="field"><span class="nm-label">Confirm new password</span>
          <input v-model="pw.confirm" :type="showPw ? 'text' : 'password'" class="nm-input" autocomplete="new-password" />
          <small v-if="pw.confirm && pw.confirm !== pw.next" class="nm-field-error">The passwords don't match.</small></label>
        <label class="show"><input v-model="showPw" type="checkbox" /> Show passwords</label>
        <div class="actions">
          <button type="submit" class="nm-btn-dark" :disabled="savingPw || !canChange">{{ savingPw ? 'Changing…' : 'Change password' }}</button>
        </div>
      </form>
    </section>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
// The signed-in admin's own profile: name/phone (PATCH /api/auth/me/) and
// password (POST /api/auth/me/password/, accounts/admin_accounts.py).
import { Check, CheckCircle2 } from 'lucide-vue-next'

const auth = useAuthStore()
const { patch, post } = useApi()
const toast = ref('')
function flash(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3000)
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
  savingDetails.value = true
  try {
    await patch('/auth/me/', { first_name: details.first_name.trim(), last_name: details.last_name.trim(), phone: details.phone.trim() || null })
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
    flash('Password changed — we emailed you a confirmation.')
  } catch (e) {
    pwErrors.value = fieldErrors(e)
  } finally {
    savingPw.value = false
  }
}
</script>

<style scoped>
.prof { display: flex; flex-direction: column; gap: 16px; max-width: 760px; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.pw { display: flex; flex-direction: column; gap: 12px; max-width: 420px; }
.field { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.field .nm-label { margin: 0; }
.field input.nm-input { min-height: 42px; }
.field input:disabled { background: #f4f6f4; color: #6a7a6a; }
.actions { grid-column: 1 / -1; display: flex; justify-content: flex-end; align-items: center; gap: 12px; flex-wrap: wrap; }
.pw .actions { justify-content: flex-start; }
.actions .nm-error { margin: 0; flex: 1; }
.rules { list-style: none; padding: 0; margin: -4px 0 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px 12px; }
.rules li { display: flex; align-items: center; gap: 6px; font-size: 0.74rem; color: #8a9a8a; }
.rules li.ok { color: #1f8f5c; }
.rules .dot { width: 6px; height: 6px; border-radius: 50%; border: 1px solid #b0bab0; margin: 0 3px; }
.show { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; color: #4a5a4a; }
@media (max-width: 560px) {
  .grid, .rules { grid-template-columns: minmax(0, 1fr); }
  .actions .nm-btn-dark { width: 100%; justify-content: center; }
}
</style>
