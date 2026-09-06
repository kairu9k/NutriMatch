<script setup>
import { useAuthStore } from '~/stores/auth'

const { get, patch } = useApi()
const auth = useAuthStore()

const isLoading = ref(true)
const errorMessage = ref('')
const settings = ref([])
const drafts = reactive({})
const savingKey = ref(null)
const savedMsg = reactive({})

async function loadSettings() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    settings.value = await get('/admin/settings/')
    for (const s of settings.value) drafts[s.key] = s.value
  } catch {
    errorMessage.value = 'Could not load system settings. Please try again later.'
  } finally {
    isLoading.value = false
  }
}
onMounted(loadSettings)

async function saveSetting(key) {
  savingKey.value = key
  savedMsg[key] = ''
  try {
    const updated = await patch(`/admin/settings/${key}/`, { value: drafts[key] })
    const s = settings.value.find(s => s.key === key)
    if (s) { s.value = updated.value; s.updated_at = updated.updated_at }
    savedMsg[key] = 'Saved.'
  } catch {
    savedMsg[key] = 'Could not save.'
  } finally {
    savingKey.value = null
    setTimeout(() => { savedMsg[key] = '' }, 2500)
  }
}

function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}
</script>

<template>
  <div class="grid grid-cols-2 gap-6">
    <div class="space-y-6">
      <p v-if="errorMessage" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">{{ errorMessage }}</p>

      <div class="animate-in bg-white rounded-2xl p-6">
        <h3 class="font-display text-lg text-forest-dark mb-1">Signed In As</h3>
        <p class="text-xs text-forest/40 mb-4">Admin account changes are managed via profile settings, not here yet</p>
        <div class="flex items-center gap-3 bg-cream-soft rounded-xl p-4">
          <div class="w-10 h-10 rounded-full bg-gold text-forest-dark flex items-center justify-center font-bold">
            {{ `${auth.user?.first_name?.[0] || ''}${auth.user?.last_name?.[0] || ''}`.toUpperCase() }}
          </div>
          <div class="flex-1">
            <p class="font-semibold text-sm">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</p>
            <p class="text-xs text-forest/50">{{ auth.user?.email }} · System Admin</p>
          </div>
          <span class="text-xs font-semibold bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full">Full Access</span>
        </div>
      </div>

      <div class="animate-in stagger-1 bg-white rounded-2xl p-6">
        <h3 class="font-display text-lg text-forest-dark mb-1">Platform Configuration</h3>
        <p class="text-xs text-forest/40 mb-4">Values used across the platform (e.g. new-invoice commission on Billing & Commission)</p>

        <div v-if="isLoading" class="text-sm text-forest/50 py-6 text-center">Loading…</div>
        <div v-else-if="!settings.length" class="text-sm text-forest/50 py-6 text-center">No settings configured yet.</div>
        <div v-else v-for="s in settings" :key="s.key" class="py-3 border-b border-forest/5 last:border-0">
          <label class="text-xs text-forest/50 uppercase">{{ s.key.replace(/_/g, ' ') }}</label>
          <p v-if="s.description" class="text-xs text-forest/40 mb-1.5">{{ s.description }}</p>
          <div class="flex gap-2">
            <input v-model="drafts[s.key]" type="text" class="flex-1 border border-forest/15 rounded-lg px-3 py-2 text-sm bg-cream-soft transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />
            <button class="btn-press bg-forest text-white rounded-lg px-4 text-sm font-medium hover:bg-forest-light disabled:opacity-60" :disabled="savingKey === s.key" @click="saveSetting(s.key)">
              {{ savingKey === s.key ? 'Saving…' : 'Save' }}
            </button>
          </div>
          <p class="text-xs text-forest/35 mt-1">Last updated {{ fmtDate(s.updated_at) }}{{ s.updated_by ? ' by ' + s.updated_by.first_name + ' ' + s.updated_by.last_name : '' }}</p>
          <Transition name="dropdown">
            <p v-if="savedMsg[s.key]" class="text-xs text-emerald-700 mt-1">{{ savedMsg[s.key] }}</p>
          </Transition>
        </div>
      </div>
    </div>

    <div class="space-y-6">
      <div class="animate-in stagger-1 bg-white rounded-2xl p-6">
        <h3 class="font-display text-lg text-forest-dark">Privacy & Compliance</h3>
        <p class="text-xs text-forest/40 mb-4">Republic Act No. 10173</p>

        <div class="card-hover bg-emerald-50 rounded-lg px-4 py-3 flex justify-between items-center mb-2">
          <div><p class="text-sm font-medium">SSL/TLS Encryption</p><p class="text-xs text-forest/40">In transit, per platform requirement</p></div>
          <span class="text-xs font-semibold bg-emerald-600 text-white px-2.5 py-1 rounded-full">Active</span>
        </div>
        <div class="card-hover bg-emerald-50 rounded-lg px-4 py-3 flex justify-between items-center mb-2">
          <div><p class="text-sm font-medium">Role-Based Access Control</p><p class="text-xs text-forest/40">3 roles: Admin, RND, Client</p></div>
          <span class="text-xs font-semibold bg-emerald-600 text-white px-2.5 py-1 rounded-full">Enforced</span>
        </div>
        <div class="card-hover bg-emerald-50 rounded-lg px-4 py-3 flex justify-between items-center mb-4">
          <div><p class="text-sm font-medium">Audit Logging</p><p class="text-xs text-forest/40">Append-only, immutable by design</p></div>
          <span class="text-xs font-semibold bg-emerald-600 text-white px-2.5 py-1 rounded-full">Enabled</span>
        </div>

        <p class="text-xs text-forest/40">
          Formal NPC registration, end-to-end encryption, automated data-retention schedules, and granular consent
          revocation are explicitly out of scope per the capstone proposal.
        </p>
      </div>
    </div>
  </div>
</template>
