<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-grid">
      <div class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">Platform configuration</h2>
            <p class="nm-panel-sub">Values used across NutriMatch. Every change is recorded in the audit log.</p>
          </div>
        </div>
        <p v-if="loading" class="nm-muted">Loading settings…</p>
        <div v-else-if="!settings.length" class="nm-empty"><p>No settings configured yet.</p></div>
        <div v-for="s in settings" :key="s.key" class="setting">
          <label class="nm-label" :for="`setting-${s.key}`">{{ META[s.key]?.label || s.key.replace(/_/g, ' ') }}</label>
          <p v-if="META[s.key]?.help || s.description" class="nm-hint" style="margin: 0 0 8px">{{ META[s.key]?.help || s.description }}</p>
          <div class="setting-row">
            <input :id="`setting-${s.key}`" v-model="drafts[s.key]" class="nm-input" :type="META[s.key]?.type || 'text'"
              v-bind="META[s.key]?.attrs || {}" />
            <button class="nm-btn-dark" :disabled="savingKey === s.key || drafts[s.key] === s.value" @click="save(s)">
              {{ savingKey === s.key ? 'Saving…' : 'Save' }}
            </button>
          </div>
          <p v-if="errors[s.key]" class="nm-field-error">{{ errors[s.key] }}</p>
          <p class="nm-hint">
            Last changed {{ dateTime(s.updated_at) }}<template v-if="s.updated_by"> by {{ s.updated_by.first_name }} {{ s.updated_by.last_name }}</template>
          </p>
        </div>
      </div>

      <div class="nm-col">
        <div class="nm-panel">
          <h2 class="nm-panel-title">Signed in as</h2>
          <div class="nm-row" style="margin-top: 14px">
            <span class="nm-avatar">{{ userInitials(auth.user?.first_name, auth.user?.last_name) }}</span>
            <div class="nm-row-main">
              <p class="nm-row-title">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</p>
              <p class="nm-row-sub">{{ auth.user?.email }}</p>
            </div>
            <span class="nm-pill green">Admin</span>
          </div>
        </div>

        <div class="nm-panel">
          <h2 class="nm-panel-title">Privacy & compliance</h2>
          <p class="nm-panel-sub">Republic Act No. 10173, the Data Privacy Act</p>
          <div v-for="c in COMPLIANCE" :key="c.title" class="nm-row" style="margin-top: 6px">
            <div class="nm-stat-icon" style="margin: 0"><component :is="c.icon" :size="16" /></div>
            <div class="nm-row-main">
              <p class="nm-row-title">{{ c.title }}</p>
              <p class="nm-row-sub">{{ c.text }}</p>
            </div>
            <span class="nm-pill green">{{ c.state }}</span>
          </div>
          <p class="nm-hint" style="margin-top: 14px">
            Formal NPC registration, end-to-end encryption, automated data-retention schedules and granular consent
            revocation are out of scope for this capstone.
          </p>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
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
const toast = ref('')

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
    toast.value = `${META[s.key]?.label || s.key} saved.`
    setTimeout(() => { toast.value = '' }, 2500)
  } catch (e) {
    errors[s.key] = apiError(e, 'Could not save. Please try again.')
  } finally {
    savingKey.value = null
  }
}
</script>

<style scoped>
.setting { padding: 16px 0; border-top: 1px solid #f0f2f0; }
.setting:first-of-type { border-top: none; padding-top: 0; }
.setting-row { display: flex; gap: 8px; }
.setting-row .nm-input { flex: 1; min-width: 0; }
</style>
