<template>
  <div class="nm-page st">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- hero, with who is signed in -->
    <section class="sh">
      <img class="sh-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="sh-fade" aria-hidden="true"></span>
      <div class="sh-txt">
        <p class="sh-eyebrow"><span></span>System settings</p>
        <h1 class="sh-title">How NutriMatch runs</h1>
        <p class="sh-sub">Values used across the platform. Every change is recorded in the audit log.</p>
      </div>
      <div class="me">
        <span class="nm-avatar me-av">{{ userInitials(auth.user?.first_name, auth.user?.last_name) }}</span>
        <div class="me-t">
          <small>Signed in as</small>
          <p class="nm-row-title">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</p>
          <p class="nm-row-sub">{{ auth.user?.email }}</p>
        </div>
        <span class="me-role"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg>Admin</span>
      </div>
    </section>

    <div class="cols">
      <div class="nm-panel card">
        <div class="nm-panel-head c-head">
          <span class="c-ico dark" aria-hidden="true"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 15a3 3 0 1 0 0-6a3 3 0 0 0 0 6z" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" /></svg></span>
          <div>
            <h2 class="nm-panel-title">Platform configuration</h2>
            <p class="nm-panel-sub">Values used across NutriMatch. Every change is recorded in the audit log.</p>
          </div>
        </div>
        <p v-if="loading" class="nm-muted">Loading settings…</p>
        <div v-else-if="!settings.length" class="nm-empty"><p>No settings configured yet.</p></div>
        <div class="sets">
          <div v-for="s in settings" :key="s.key" class="setting">
            <span class="set-ico" :class="SET_TONE[s.key] || 'plain'" aria-hidden="true">
              <template v-if="s.key === 'platform_commission_pct'"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 5L5 19" /><path d="M4 6.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /><path d="M15 17.5a2.5 2.5 0 1 0 5 0a2.5 2.5 0 1 0 -5 0" /></svg></template>
              <template v-else-if="s.key === 'platform_name'"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7V4h16v3M9 20h6M12 4v16" /></svg></template>
              <template v-else-if="s.key === 'support_email'"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 7l9 6 9-6" /></svg></template>
              <template v-else><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6" /></svg></template>
            </span>
            <div class="set-main">
              <label class="nm-label" :for="`setting-${s.key}`">{{ META[s.key]?.label || s.key.replace(/_/g, ' ') }}</label>
              <p v-if="META[s.key]?.help || s.description" class="nm-hint set-help">{{ META[s.key]?.help || s.description }}</p>
              <div class="setting-row">
                <span class="inp">
                  <input :id="`setting-${s.key}`" v-model="drafts[s.key]" class="nm-input" :type="META[s.key]?.type || 'text'"
                    v-bind="META[s.key]?.attrs || {}" />
                  <span v-if="s.key === 'platform_commission_pct'" class="suf" aria-hidden="true">%</span>
                </span>
                <button class="nm-btn-dark" :disabled="savingKey === s.key || drafts[s.key] === s.value" @click="save(s)">
                  <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>{{ savingKey === s.key ? 'Saving…' : 'Save' }}
                </button>
              </div>
              <p v-if="errors[s.key]" class="nm-field-error">{{ errors[s.key] }}</p>
              <p class="nm-hint chg">
                <svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 7v5l3 2" /></svg><span>Last changed {{ dateTime(s.updated_at) }}<template v-if="s.updated_by"> by <b>{{ s.updated_by.first_name }} {{ s.updated_by.last_name }}</b></template></span>
              </p>
            </div>
          </div>
        </div>
      </div>

      <div class="nm-panel card">
        <div class="c-head">
          <span class="c-ico green" aria-hidden="true"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg></span>
          <div>
            <h2 class="nm-panel-title">Privacy & compliance</h2>
            <p class="nm-panel-sub">Republic Act No. 10173, the Data Privacy Act</p>
          </div>
        </div>
        <div class="prs">
          <div v-for="(c, i) in COMPLIANCE" :key="c.title" class="nm-row pr">
            <div class="nm-stat-icon pr-ico" :class="PR_TONES[i % PR_TONES.length]"><component :is="c.icon" :size="17" /></div>
            <div class="nm-row-main">
              <p class="nm-row-title">{{ c.title }}</p>
              <p class="nm-row-sub">{{ c.text }}</p>
            </div>
            <span class="nm-pill green">{{ c.state }}</span>
          </div>
        </div>
        <p class="nm-hint scope">
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 11v5M12 8h.01" /></svg><span>Formal NPC registration, end-to-end encryption, automated data-retention schedules and granular consent
          revocation are out of scope for this capstone.</span>
        </p>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import { CheckCircle2, FileCheck2, Lock, ScrollText, ShieldCheck } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

const { get, patch } = useApi()
const auth = useAuthStore()

const META = {
  platform_commission_pct: {
    label: 'Platform commission (%)',
    help: 'NutriMatch\'s share of each consultation fee, between 0% and 50%. Only applies to bookings confirmed after the change.',
    type: 'number',
    attrs: { min: 0, max: 50, step: 0.01 },
  },
  platform_name: { label: 'Platform name', help: 'Shown in emails and page titles.' },
  support_email: { label: 'Support email', help: 'Where users are told to write for help.', type: 'email' },
}
const COMPLIANCE = [
  { icon: Lock, title: 'Encryption in transit', text: 'HTTPS/TLS for every request', state: 'Active' },
  { icon: ShieldCheck, title: 'Role-based access', text: 'Admin, RND and client permissions', state: 'Enforced' },
  { icon: ScrollText, title: 'Audit logging', text: 'Append-only record of sensitive actions', state: 'Enabled' },
  { icon: FileCheck2, title: 'Informed consent', text: 'Terms and data-privacy consent at sign-up', state: 'Required' },
]

const loading = ref(true)
const error = ref('')
const settings = ref([])
const drafts = reactive({})
const errors = reactive({})
const savingKey = ref(null)
const toast = useToast() // the app's toast (2026-11-03)

onMounted(async () => {
  try {
    settings.value = await get('/admin/settings/')
    for (const s of settings.value) drafts[s.key] = s.value
  } catch {
    error.value = 'Could not load system settings. Please refresh the page.'
  } finally {
    loading.value = false
  }
})

async function save(s) {
  savingKey.value = s.key
  errors[s.key] = ''
  try {
    const updated = await patch(`/admin/settings/${s.key}/`, { value: String(drafts[s.key] ?? '') })
    Object.assign(s, updated)
    drafts[s.key] = updated.value
    toast.success(`${META[s.key]?.label || s.key} saved.`)
  } catch (e) {
    errors[s.key] = apiError(e, 'Could not save. Please try again.')
  } finally {
    savingKey.value = null
  }
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const SET_TONE = { platform_commission_pct: 'gold', platform_name: 'green', support_email: 'blue' }
const PR_TONES = ['green', 'blue', 'gold', 'plain']
</script>

<style scoped>
.st { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; display: inline-block; }

/* ---------- hero ---------- */
.sh { position: relative; overflow: hidden; display: flex; align-items: center; gap: 24px; margin-bottom: 20px; padding: 24px 30px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.sh > *:not(.sh-plate):not(.sh-fade) { position: relative; z-index: 1; }
.sh-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.sh-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 55%, rgba(0, 77, 58, 0.88) 75%, rgba(0, 77, 58, 0.65) 100%); }
.sh-txt { flex: 1; min-width: 0; }
.sh-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.sh-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.sh-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 700; line-height: 1.2; color: #fff; }
.sh-sub { margin: 0; font-size: 14px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }
.me { display: flex; align-items: center; gap: 12px; margin-right: 150px; padding: 12px 16px; border: 1px solid rgba(255, 255, 255, 0.18); border-radius: 18px; background: rgba(255, 255, 255, 0.1); backdrop-filter: blur(8px); }
.me-av { flex-shrink: 0; width: 46px !important; height: 46px !important; border-radius: 50%; background: linear-gradient(135deg, #f5cb1f, #c49102) !important; color: #004d3a !important; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; border: 2px solid rgba(255, 255, 255, 0.8); }
.me-t { min-width: 0; }
.me-t small { display: block; font-size: 11px; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; color: #efbf04; }
.me-t .nm-row-title { margin: 0; font-size: 15px; font-weight: 800; color: #fff; }
.me-t .nm-row-sub { margin: 0; font-size: 12.5px; color: rgba(255, 255, 255, 0.8); overflow-wrap: anywhere; }
.me-role { display: inline-flex; align-items: center; gap: 5px; margin-left: 8px; padding: 4px 10px; border-radius: 999px; background: #efbf04; color: #004d3a; font-size: 12px; font-weight: 800; }

/* ---------- cards ---------- */
.cols { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(0, 1fr); gap: 20px; align-items: start; }
.card { margin: 0; padding: 24px 26px; border: none; border-radius: 22px; background: #fff; box-shadow: var(--sh); }
.c-head { display: flex; align-items: center; gap: 14px; margin: 0 0 18px; padding: 0; border: none; }
.c-head > div { flex: 1; min-width: 0; }
.c-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; }
.c-ico.dark { background: #004d3a; color: #efbf04; }
.c-ico.green { background: #e3efe7; color: #004d3a; }
.c-head .nm-panel-title { margin: 0; font-family: 'Playfair Display', serif; font-size: 21px; font-weight: 700; color: #0e3a2c; }
.c-head .nm-panel-sub { margin: 3px 0 0; font-size: 13px; color: #6b7d73; }

/* settings */
.sets { display: flex; flex-direction: column; gap: 12px; }
.setting { display: flex; gap: 14px; padding: 16px 18px; border: 1.5px solid #e3ebe6; border-radius: 18px; background: #fbfcfb; transition: border-color 0.15s; }
.setting:hover, .setting:focus-within { border-color: #c9d8cf; }
.set-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 13px; display: inline-flex; align-items: center; justify-content: center; }
.gold { background: #fff4d6 !important; color: #8a6500 !important; }
.green { background: #e3f4ea !important; color: #1f7a4d !important; }
.blue { background: #eef1fa !important; color: #2e4a86 !important; }
.plain { background: #f1f6f2 !important; color: #4a5a52 !important; }
.set-main { flex: 1; min-width: 0; }
.set-main .nm-label { display: block; margin: 0; font-size: 15px; font-weight: 800; color: #0e3a2c; }
.set-help { margin: 3px 0 0 !important; font-size: 12.5px; line-height: 1.45; color: #6b7d73; }
.setting-row { display: flex; gap: 10px; margin-top: 12px; }
.inp { flex: 1; min-width: 0; display: flex; align-items: center; gap: 8px; height: 46px; padding: 0 14px; border: 1.5px solid #c9d8cf; border-radius: 13px; background: #fff; box-sizing: border-box; transition: border-color 0.15s, box-shadow 0.15s; }
.inp:focus-within { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.inp .nm-input { flex: 1; min-width: 0; height: 100%; margin: 0; padding: 0 !important; border: none !important; background: transparent !important; box-shadow: none !important; outline: none; font-family: inherit; font-size: 14.5px; font-weight: 600; color: #14261e; }
.suf { padding: 3px 9px; border-radius: 8px; background: #f1f6f2; font-size: 13px; font-weight: 800; color: #4a5a52; }
.st .nm-btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 46px; padding: 0 18px; border: none; border-radius: 13px; background: #004d3a; color: #fff; font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.st .nm-btn-dark .ic { color: #efbf04; }
.st .nm-btn-dark:disabled { opacity: 0.4; box-shadow: none; cursor: not-allowed; }
.set-main .nm-field-error { margin: 8px 0 0; }
.chg { display: inline-flex; align-items: center; gap: 6px; margin: 10px 0 0; padding: 3px 10px; border-radius: 999px; background: #f1f6f2; font-size: 12px; font-weight: 600; color: #6b7d73; }
.chg .ic { color: #1f7a4d; }
.chg b { color: #22362c; }

/* privacy */
.prs { display: flex; flex-direction: column; gap: 10px; }
.pr { display: flex; align-items: center; gap: 12px; margin: 0 !important; padding: 13px 14px; border: 1px solid #eef2ef; border-radius: 16px; background: #f7faf8; }
.pr-ico { flex-shrink: 0; width: 38px !important; height: 38px !important; margin: 0 !important; border-radius: 12px !important; display: inline-flex; align-items: center; justify-content: center; }
.pr .nm-row-main { flex: 1; min-width: 0; }
.pr .nm-row-title { margin: 0; font-size: 14px; font-weight: 800; color: #0e3a2c; }
.pr .nm-row-sub { margin: 1px 0 0; font-size: 12.5px; color: #6b7d73; }
.pr .nm-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; background: #e3f4ea; color: #1f7a4d; font-size: 12px; font-weight: 800; white-space: nowrap; }
.pr .nm-pill::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.scope { display: flex; gap: 10px; margin: 16px 0 0 !important; padding: 12px 14px; border: 1.5px dashed #c9d8cf; border-radius: 14px; font-size: 12.5px; line-height: 1.5; color: #6b7d73; }
.scope .ic { margin-top: 1px; color: #8a9a91; }

@media (max-width: 1100px) {
  .cols { grid-template-columns: minmax(0, 1fr); }
  .me { margin-right: 0; }
}
@media (max-width: 760px) {
  .st { padding-bottom: 110px; }
  .sh { flex-direction: column; align-items: stretch; padding: 20px 18px; border-radius: 22px; }
  .sh-title { font-size: 24px; }
  .sh-plate { width: 170px; height: 170px; right: -55px; top: 20px; transform: none; }
  .card { padding: 18px; }
  .setting { flex-direction: column; }
  .setting-row { flex-direction: column; }
  .st .nm-btn-dark { width: 100%; }
}
</style>  