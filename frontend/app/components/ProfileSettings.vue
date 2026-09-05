<template>
  <div class="profile-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Profile Settings</h1>
        <p class="page-sub">{{ isRnd ? 'Manage your professional profile, credentials, and preferences.' : 'Manage your personal and health information.' }}</p>
      </div>
      <span v-if="isRnd && auth.rndProfile?.is_verified" class="verified-pill">
        <BadgeCheck :size="14" />
        PRC Verified
      </span>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="form-success">{{ successMessage }}</p>

    <div class="profile-layout">
      <!-- TABS -->
      <div class="tab-card">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <component :is="tab.icon" :size="17" />
          {{ tab.label }}
        </button>
      </div>

      <!-- PANEL -->
      <div class="panel-card">
        <p v-if="isLoading" class="placeholder-text">Loading…</p>

        <template v-else-if="activeTab === 'personal'">
          <div class="avatar-row">
            <div class="avatar-circle" :style="{ background: avatarColor }">
              {{ initials }}
            </div>
            <div>
              <p class="avatar-name">{{ displayName }}</p>
              <p class="avatar-hint">{{ auth.user?.email }}</p>
            </div>
          </div>

          <template v-if="!isRnd">
            <div class="form-grid">
              <div class="field">
                <label class="field-label">Address</label>
                <input v-model="clientForm.address" type="text" class="field-input" />
              </div>
              <div class="field">
                <label class="field-label">Emergency Contact Name</label>
                <input v-model="clientForm.emergency_contact" type="text" class="field-input" />
              </div>
              <div class="field">
                <label class="field-label">Emergency Contact Phone</label>
                <input v-model="clientForm.emergency_phone" type="tel" class="field-input" />
              </div>
            </div>

            <button class="save-btn" type="button" :disabled="isSaving" @click="saveClientProfile">
              {{ isSaving ? 'Saving…' : 'Save Changes' }}
            </button>
          </template>
          <p v-else class="placeholder-text">Name and email are managed by NutriMatch — contact support to update them.</p>
        </template>

        <template v-else-if="activeTab === 'health'">
          <div class="health-grid">
            <div class="health-field">
              <p class="field-label">Medical Conditions</p>
              <p class="health-value">{{ formatList(healthProfile?.medical_conditions) }}</p>
            </div>
            <div class="health-field">
              <p class="field-label">Allergies</p>
              <p class="health-value">{{ formatList(healthProfile?.allergies) }}</p>
            </div>
            <div class="health-field">
              <p class="field-label">Dietary Restrictions</p>
              <p class="health-value">{{ formatList(healthProfile?.dietary_restrictions) }}</p>
            </div>
            <div class="health-field">
              <p class="field-label">Health Goals</p>
              <p class="health-value">{{ formatList(healthProfile?.health_goals) }}</p>
            </div>
          </div>
          <p class="health-hint">Health information is captured during pre-consultation screening and updated by your RND — it can't be edited here.</p>
        </template>

        <template v-else>
          <p class="placeholder-text">{{ activeTabLabel }} settings go here.</p>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { User, Briefcase, Languages, Wallet, ShieldCheck, BadgeCheck, HeartPulse } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Profile Settings' })

const auth = useAuthStore()
const { get, patch } = useApi()

const isRnd = computed(() => auth.user?.role === 'rnd')

const rndTabs = [
  { key: 'personal', label: 'Personal Info', icon: User },
  { key: 'professional', label: 'Professional Profile', icon: Briefcase },
  { key: 'languages', label: 'Languages', icon: Languages },
  { key: 'fees', label: 'Fees & Payouts', icon: Wallet },
  { key: 'security', label: 'Security', icon: ShieldCheck }
]

const clientTabs = [
  { key: 'personal', label: 'Personal Info', icon: User },
  { key: 'health', label: 'Health Info', icon: HeartPulse },
  { key: 'security', label: 'Security', icon: ShieldCheck }
]

const tabs = computed(() => (isRnd.value ? rndTabs : clientTabs))
const activeTab = ref('personal')
const activeTabLabel = computed(() => tabs.value.find(t => t.key === activeTab.value)?.label)

const isLoading = ref(true)
const isSaving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const displayName = computed(() => auth.user ? `${auth.user.first_name} ${auth.user.last_name}` : '')
const initials = computed(() => `${auth.user?.first_name?.[0] || ''}${auth.user?.last_name?.[0] || ''}`.toUpperCase())
const avatarColor = computed(() => (isRnd.value ? '#D4A017' : '#1e4a26'))

const clientForm = reactive({
  address: '',
  emergency_contact: '',
  emergency_phone: ''
})

const healthProfile = ref(null)

function formatList(value) {
  if (!value || (Array.isArray(value) && !value.length)) return 'None recorded'
  return Array.isArray(value) ? value.join(', ') : value
}

async function loadProfile() {
  if (isRnd.value) {
    isLoading.value = false
    return
  }
  isLoading.value = true
  errorMessage.value = ''
  try {
    const profile = await get('/client/profile/')
    clientForm.address = profile.address || ''
    clientForm.emergency_contact = profile.emergency_contact || ''
    clientForm.emergency_phone = profile.emergency_phone || ''
    healthProfile.value = profile.health_profile
  } catch {
    errorMessage.value = 'Could not load your profile. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

async function saveClientProfile() {
  isSaving.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await patch('/client/profile/', { ...clientForm })
    successMessage.value = 'Profile updated.'
  } catch {
    errorMessage.value = 'Could not save changes. Please try again.'
  } finally {
    isSaving.value = false
  }
}

onMounted(loadProfile)
</script>

<style scoped>
* { box-sizing: border-box; }

.profile-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.verified-pill {
  display: inline-flex; align-items: center; gap: 6px;
  background: #e6efe0; color: #3a6b3a; font-size: 0.78rem; font-weight: 700;
  padding: 7px 14px; border-radius: 20px; white-space: nowrap;
}

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.form-success {
  background: #e6efe0; border: 1px solid #b8d5b8; color: #3a6b3a;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}

/* LAYOUT */
.profile-layout { display: grid; grid-template-columns: 280px 1fr; gap: 20px; align-items: start; }

.tab-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 10px; display: flex; flex-direction: column; gap: 2px;
}
.tab-item {
  display: flex; align-items: center; gap: 10px; text-align: left;
  border: none; background: none; border-radius: 8px; padding: 12px 14px;
  font-size: 0.88rem; font-weight: 600; color: #4a5a4a; cursor: pointer;
}
.tab-item.active { background: #eef3ec; color: #1a3a1a; }

.panel-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 28px;
}

/* AVATAR */
.avatar-row { display: flex; align-items: center; gap: 18px; margin-bottom: 26px; }
.avatar-circle {
  width: 56px; height: 56px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 1.05rem; font-weight: 700; flex-shrink: 0;
}
.avatar-name { font-size: 0.95rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.avatar-hint { font-size: 0.76rem; color: #9aaa9a; margin: 0; }

/* FORM */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 24px; margin-bottom: 24px; }
.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; margin: 0 0 8px; }
.field-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 12px 14px;
  font-size: 0.88rem; color: #2a2a2a; font-family: inherit;
}
.field-input:focus { outline: none; border-color: #D4A017; }

.save-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 12px 22px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}
.save-btn:disabled { opacity: 0.6; cursor: not-allowed; }

/* HEALTH INFO */
.health-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px 24px; margin-bottom: 16px; }
.health-value { font-size: 0.9rem; color: #2a2a2a; margin: 0; }
.health-hint { font-size: 0.8rem; color: #9aaa9a; margin: 0; }

.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }
</style>
