<template>
  <div class="client-profile-page">
    <p v-if="loadError" class="form-error">{{ loadError }}</p>

    <div class="profile-banner">
      <div class="banner-blob"></div>
      <div class="banner-left">
        <div class="banner-avatar">{{ initials }}</div>
        <div>
          <p class="banner-name">{{ displayName }}</p>
          <p class="banner-sub">{{ auth.user?.email }}</p>
          <div class="banner-chips">
            <span class="chip">Patient</span>
            <span v-if="memberSince" class="chip">Member since {{ memberSince }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-layout">
      <nav class="settings-nav">
        <button
          v-for="tab in tabs" :key="tab.key"
          class="settings-nav-item" :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <component :is="tab.icon" :size="16" />
          {{ tab.label }}
        </button>
      </nav>

      <div class="settings-main">
        <!-- PERSONAL INFO -->
        <div v-if="activeTab === 'personal'" class="panel">
          <h3 class="panel-title">Personal Information</h3>
          <div class="form-row-2">
            <div class="field">
              <label>First Name</label>
              <input v-model="form.firstName" type="text" />
            </div>
            <div class="field">
              <label>Last Name</label>
              <input v-model="form.lastName" type="text" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="field">
              <label>Email Address</label>
              <input :value="auth.user?.email" type="email" disabled />
              <span class="field-hint">Email can't be changed here.</span>
            </div>
            <div class="field">
              <label>Phone Number</label>
              <input v-model="form.phone" type="tel" placeholder="e.g. 0917 123 4567" />
            </div>
          </div>
          <div class="form-row-3">
            <div class="field">
              <label>Date of Birth</label>
              <input v-model="form.dateOfBirth" type="date" />
            </div>
            <div class="field">
              <label>Sex</label>
              <select v-model="form.sex">
                <option value="">Select</option>
                <option value="female">Female</option>
                <option value="male">Male</option>
              </select>
            </div>
            <div class="field">
              <label>Preferred Language</label>
              <select v-model="form.languageCode">
                <option value="">Select</option>
                <option v-for="l in languageOptions" :key="l.code" :value="l.code">{{ l.label }}</option>
              </select>
            </div>
          </div>
          <p v-if="saveError" class="form-error">{{ saveError }}</p>
          <button class="primary-btn" :disabled="isSaving" @click="saveProfile">{{ isSaving ? 'Saving…' : 'Save Changes' }}</button>
        </div>

        <!-- HEALTH PROFILE -->
        <div v-else-if="activeTab === 'health'" class="panel">
          <h3 class="panel-title">Health Profile</h3>
          <p class="tab-desc">Your latest screening results on file.</p>
          <div v-if="screening" class="health-grid">
            <div class="health-box"><p class="health-label">BMI</p><p class="health-value">{{ screening.bmi }}</p><p class="health-sub">{{ screening.bmi_category }}</p></div>
            <div class="health-box"><p class="health-label">TDEE</p><p class="health-value">{{ Math.round(screening.tdee_kcal) }} <span>kcal</span></p></div>
            <div class="health-box"><p class="health-label">NRS-2002</p><p class="health-value">{{ screening.nrs_score ?? '—' }}</p><p class="health-sub">{{ nrsLabel(screening.nrs_risk) }}</p></div>
          </div>
          <p v-else class="tab-desc">No screening on file yet.</p>
          <button class="outline-btn" @click="navigateTo('/pre-consultation-screening')">Update Screening</button>

          <div class="condition-section">
            <h4 class="section-title">Primary Health Condition</h4>
            <p class="tab-desc">Your RND sees this on your patient record so they can prepare for your care.</p>
            <div class="form-row-2">
              <div class="field">
                <label>Condition</label>
                <select v-model="conditionChoice">
                  <option value="">None / not sure</option>
                  <option v-for="c in CONDITION_OPTIONS" :key="c" :value="c">{{ c }}</option>
                  <option value="__other">Other</option>
                </select>
              </div>
              <div v-if="conditionChoice === '__other'" class="field">
                <label>Please specify</label>
                <input v-model="conditionOther" type="text" maxlength="100" placeholder="e.g. High cholesterol" />
              </div>
            </div>
            <p v-if="conditionError" class="form-error">{{ conditionError }}</p>
            <button class="primary-btn" :disabled="isSavingCondition" @click="saveCondition">{{ isSavingCondition ? 'Saving…' : 'Save Condition' }}</button>
          </div>
        </div>

        <!-- SECURITY -->
        <div v-else-if="activeTab === 'security'" class="panel">
          <h3 class="panel-title">Security</h3>
          <div class="account-row">
            <div>
              <p class="account-label">Password</p>
              <p class="account-detail">We'll email you a 6-digit code to set a new password.</p>
            </div>
            <button class="outline-btn small" @click="navigateTo('/forgot-password')">Change Password</button>
          </div>
        </div>

        <!-- NOTIFICATIONS -->
        <div v-else-if="activeTab === 'notifications'" class="panel">
          <h3 class="panel-title">Notifications</h3>
          <!-- TODO: mock/local only — no notification-preference field or endpoint exists yet. -->
          <div class="account-row">
            <div>
              <p class="account-label">Appointment, meal plan, and reminder alerts</p>
              <p class="account-detail">Receive push and email notifications</p>
            </div>
            <label class="toggle">
              <input v-model="notificationsEnabled" type="checkbox" />
              <span class="toggle-track"><span class="toggle-thumb"></span></span>
            </label>
          </div>
        </div>

        <!-- PRIVACY & DATA -->
        <div v-else-if="activeTab === 'privacy'" class="panel">
          <h3 class="panel-title">Privacy &amp; Data</h3>
          <p class="tab-desc">Your health data is only shared with your assigned RND under RA 10173 (Data Privacy Act of 2012).</p>
          <!-- TODO: no data-export endpoint exists yet. -->
          <button class="outline-btn" disabled title="Coming soon">Download My Data</button>
        </div>

        <!-- HISTORY -->
        <div v-else-if="activeTab === 'history'" class="panel">
          <div class="panel-header-row">
            <div>
              <h3 class="panel-title flush">Your Activity</h3>
              <p class="panel-sub">Every screening, appointment, and meal log on your account.</p>
            </div>
            <div class="header-actions">
              <div class="filter-tabs">
                <button v-for="f in historyFilters" :key="f.key" class="filter-tab" :class="{ active: historyFilter === f.key }" @click="historyFilter = f.key">{{ f.label }}</button>
              </div>
              <button class="outline-btn small print-btn" @click="printHistory"><Printer :size="14" /> Print</button>
            </div>
          </div>

          <p v-if="isLoadingHistory" class="placeholder-text">Loading…</p>
          <div v-else-if="!filteredHistory.length" class="empty-state">
            <ClipboardList :size="26" class="empty-icon" />
            <p>Nothing saved yet.</p>
            <p class="empty-sub">Complete a screening, book an appointment, or log a meal — it'll show up here.</p>
          </div>
          <div v-for="entry in filteredHistory" v-else :key="entry.key" class="entry-row">
            <div class="entry-icon" :class="entry.iconClass"><component :is="entry.icon" :size="16" /></div>
            <div class="entry-info">
              <p class="entry-title">{{ entry.title }}</p>
              <p class="entry-detail">{{ entry.detail }}</p>
            </div>
            <span class="entry-time">{{ formatTimestamp(entry.at) }}</span>
          </div>
        </div>
      </div>

      <!-- SIDE -->
      <div class="settings-side">
        <div class="panel">
          <h3 class="panel-title">Care Team</h3>
          <template v-if="careRnd">
            <div class="rnd-row">
              <div class="rnd-avatar">{{ careRndInitials }}</div>
              <div>
                <NuxtLink :to="`/rnd-profile-view/${careRnd.user.id}`" class="rnd-name">RND {{ careRnd.user.first_name }} {{ careRnd.user.last_name }}</NuxtLink>
                <p class="rnd-specialty">{{ careRnd.specialization || 'General Practice' }}</p>
                <p v-if="careRnd.review_count" class="rnd-rating">★ {{ Number(careRnd.average_rating).toFixed(1) }} ({{ careRnd.review_count }} review{{ careRnd.review_count === 1 ? '' : 's' }})</p>
              </div>
            </div>
            <button class="outline-btn full-width" @click="navigateTo('/messages')">Send a Message</button>
          </template>
          <template v-else>
            <p class="tab-desc">You're not connected with an RND yet.</p>
            <button class="outline-btn full-width" @click="navigateTo('/find-rnd')">Find an RND</button>
          </template>
        </div>

        <div class="panel danger-panel">
          <h3 class="panel-title">Sign Out</h3>
          <p class="danger-text">Sign out of NutriMatch on this device.</p>
          <button class="danger-outline-btn full-width" @click="handleLogout">Sign Out</button>
        </div>
      </div>
    </div>

    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle2 :size="16" /> Profile updated!
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  User, HeartPulse, Shield, Bell, FileText, History as HistoryIcon, CheckCircle2,
  Printer, ClipboardList, ShieldCheck, CalendarCheck, UtensilsCrossed,
} from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

const auth = useAuthStore()
const { get, patch } = useApi()

const tabs = [
  { key: 'personal', label: 'Personal Info', icon: User },
  { key: 'health', label: 'Health Profile', icon: HeartPulse },
  { key: 'security', label: 'Security', icon: Shield },
  { key: 'notifications', label: 'Notifications', icon: Bell },
  { key: 'privacy', label: 'Privacy & Data', icon: FileText },
  { key: 'history', label: 'History', icon: HistoryIcon },
]
const activeTab = ref('personal')

const languageOptions = [
  { code: 'tl', label: 'Filipino (Tagalog)' },
  { code: 'ceb', label: 'Bisaya (Cebuano)' },
  { code: 'ilo', label: 'Ilocano' },
  { code: 'en', label: 'English' },
]

const loadError = ref('')
const displayName = computed(() => `${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim())
const initials = computed(() => `${auth.user?.first_name?.[0] || ''}${auth.user?.last_name?.[0] || ''}`.toUpperCase())
const memberSince = computed(() =>
  auth.user?.created_at ? new Date(auth.user.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : ''
)

/* ---------- Personal info ---------- */
const form = reactive({ firstName: '', lastName: '', phone: '', dateOfBirth: '', sex: '', languageCode: '' })
const isSaving = ref(false)
const saveError = ref('')

function fillForm(profile) {
  form.firstName = profile.user.first_name || ''
  form.lastName = profile.user.last_name || ''
  form.phone = profile.user.phone || ''
  form.dateOfBirth = profile.date_of_birth || ''
  form.sex = profile.sex || ''
  form.languageCode = profile.language_code || ''
}

async function saveProfile() {
  isSaving.value = true
  saveError.value = ''
  try {
    await Promise.all([
      patch('/auth/me/', { first_name: form.firstName, last_name: form.lastName, phone: form.phone || null }),
      patch('/client/profile/', {
        date_of_birth: form.dateOfBirth || null,
        sex: form.sex || null,
        language_code: form.languageCode || null,
      }),
    ])
    await auth.fetchMe()
    fireToast()
  } catch (error) {
    const data = error?.data || {}
    saveError.value = data.detail || Object.values(data).flat()[0] || 'Could not save your changes. Please try again.'
  } finally {
    isSaving.value = false
  }
}

const toastVisible = ref(false)
let toastTimer = null
function fireToast() {
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 3500)
}

/* ---------- Health profile ---------- */
const screening = ref(null)

// Same choices as the sign-up form's "Primary Health Concern".
const CONDITION_OPTIONS = ['Hypertension', 'Type 2 Diabetes', 'Obesity Management', 'Renal Nutrition']
const conditionChoice = ref('')
const conditionOther = ref('')
// medical_conditions[0] is the primary condition; anything after it is kept.
const otherConditions = ref([])
const isSavingCondition = ref(false)
const conditionError = ref('')

function fillCondition(profile) {
  const conditions = profile.health_profile?.medical_conditions || []
  const primary = conditions[0] || ''
  otherConditions.value = conditions.slice(1)
  if (!primary) {
    conditionChoice.value = ''
  } else if (CONDITION_OPTIONS.includes(primary)) {
    conditionChoice.value = primary
  } else {
    conditionChoice.value = '__other'
    conditionOther.value = primary
  }
}

async function saveCondition() {
  conditionError.value = ''
  let primary = conditionChoice.value
  if (primary === '__other') {
    primary = conditionOther.value.trim()
    if (!primary) {
      conditionError.value = 'Please type your condition, or pick one from the list.'
      return
    }
  }
  isSavingCondition.value = true
  try {
    const profile = await patch('/client/profile/', {
      medical_conditions: primary ? [primary, ...otherConditions.value] : otherConditions.value,
    })
    fillCondition(profile)
    fireToast()
  } catch (error) {
    const data = error?.data || {}
    conditionError.value = data.detail || Object.values(data).flat()[0] || 'Could not save your condition. Please try again.'
  } finally {
    isSavingCondition.value = false
  }
}
function nrsLabel(risk) {
  return { no_risk: 'No Risk', at_risk: 'At Risk', high_risk: 'High Risk' }[risk] || ''
}

// TODO: mock/local only — no notification-preference field on User/ClientProfile.
const notificationsEnabled = ref(true)

/* ---------- Care team ---------- */
const careRnd = ref(null)
const careRndInitials = computed(() =>
  careRnd.value ? `${careRnd.value.user.first_name?.[0] || ''}${careRnd.value.user.last_name?.[0] || ''}`.toUpperCase() : ''
)

/* ---------- History (real screenings, appointments, meal logs) ---------- */
const historyFilters = [
  { key: 'all', label: 'All' },
  { key: 'screening', label: 'Screenings' },
  { key: 'appointment', label: 'Appointments' },
  { key: 'mealLog', label: 'Meal Logs' },
]
const historyFilter = ref('all')
const historyEntries = ref([])
const isLoadingHistory = ref(false)
let historyLoaded = false

const APPT_TYPE = { video: 'Video', chat: 'Chat', in_person: 'In-Person' }
const APPT_STATUS = { pending: 'Pending', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }
const MEAL_LABELS = { breakfast: 'Breakfast', am_snack: 'AM Snack', lunch: 'Lunch', pm_snack: 'PM Snack', dinner: 'Dinner', bedtime_snack: 'Bedtime Snack' }
const LOG_STATUS = { followed: 'Followed Plan', partially_followed: 'Partially Followed', not_followed: 'Did Not Follow' }

async function loadHistory() {
  isLoadingHistory.value = true
  try {
    const [screenings, appointments, mealLogs, mealPlans] = await Promise.all([
      get('/client/screening/').catch(() => []),
      get('/client/appointments/').catch(() => []),
      get('/client/meal-logs/').catch(() => []),
      get('/client/meal-plans/').catch(() => []),
    ])
    // meal_plan_meal is just an id on MealLog — resolve its meal_time from the plans.
    const mealTimeById = {}
    for (const p of mealPlans) for (const m of p.meals) mealTimeById[m.id] = m.meal_time

    historyEntries.value = [
      ...screenings.map(s => ({
        key: `s${s.id}`, type: 'screening', at: s.created_at, icon: ShieldCheck, iconClass: 'icon-blue',
        title: 'Health screening completed',
        detail: `BMI ${s.bmi} (${s.bmi_category}) · NRS-2002 ${s.nrs_score ?? '—'}`,
      })),
      ...appointments.map(a => ({
        key: `a${a.id}`, type: 'appointment', at: a.created_at, icon: CalendarCheck, iconClass: 'icon-gold',
        title: `${APPT_TYPE[a.type] || a.type} appointment with RND ${a.relationship.rnd.first_name} ${a.relationship.rnd.last_name}`,
        detail: `${APPT_STATUS[a.status] || a.status} · scheduled ${formatTimestamp(a.scheduled_at)}`,
      })),
      ...mealLogs.map(l => ({
        key: `m${l.id}`, type: 'mealLog', at: l.updated_at, icon: UtensilsCrossed, iconClass: 'icon-green',
        title: `${MEAL_LABELS[mealTimeById[l.meal_plan_meal]] || 'Meal'} logged`,
        detail: `${LOG_STATUS[l.status] || l.status} · ${l.log_date}${l.reason_notes ? ` · ${l.reason_notes}` : ''}`,
      })),
    ].sort((x, y) => new Date(y.at) - new Date(x.at))
    historyLoaded = true
  } finally {
    isLoadingHistory.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'history' && !historyLoaded) loadHistory()
})

const filteredHistory = computed(() =>
  historyFilter.value === 'all' ? historyEntries.value : historyEntries.value.filter(e => e.type === historyFilter.value)
)

function formatTimestamp(iso) {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}
function printHistory() {
  window.print()
}

function handleLogout() {
  auth.logout()
  navigateTo('/login')
}

onMounted(async () => {
  try {
    const [profile, latestScreening, relationships] = await Promise.all([
      get('/client/profile/'),
      get('/client/screening/latest/').catch(() => null),
      get('/client/relationships/').catch(() => []),
    ])
    fillForm(profile)
    fillCondition(profile)
    screening.value = latestScreening
    const active = relationships.find(r => r.status === 'active')
    if (active) careRnd.value = await get(`/client/rnds/${active.rnd.id}/`).catch(() => null)
  } catch {
    loadError.value = 'Could not load your profile. Please try again later.'
  }
})
</script>

<style scoped>
* { box-sizing: border-box; }
.client-profile-page { font-family: 'Inter', sans-serif; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

/* BANNER */
.profile-banner {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%);
  border-radius: 16px; padding: 28px 32px; margin-bottom: 20px; color: #fff;
}
.banner-blob { position: absolute; width: 220px; height: 220px; border-radius: 50%; background: rgba(255,255,255,0.05); top: -70px; right: -50px; z-index: 0; }
.banner-left { display: flex; align-items: center; gap: 18px; position: relative; z-index: 1; }
.banner-avatar { width: 64px; height: 64px; border-radius: 50%; background: #D4A017; color: #1a3a1a; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.3rem; flex-shrink: 0; }
.banner-name { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; margin: 0; }
.banner-sub { font-size: 0.87rem; color: #cfe0d5; margin: 4px 0 10px; }
.banner-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { font-size: 0.75rem; font-weight: 600; background: rgba(255,255,255,0.1); color: #fff; padding: 4px 12px; border-radius: 999px; }

/* LAYOUT */
.settings-layout { display: grid; grid-template-columns: 210px 1.6fr 1fr; gap: 20px; align-items: start; }
.settings-nav { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 10px; display: flex; flex-direction: column; gap: 2px; }
.settings-nav-item {
  display: flex; align-items: center; gap: 10px; border: none; background: none; text-align: left;
  padding: 11px 12px; border-radius: 10px; font-size: 0.85rem; font-weight: 600; color: #6a7a6a; cursor: pointer;
}
.settings-nav-item:hover { background: #f7f9f7; }
.settings-nav-item.active { background: #eef3ee; color: #1a3a1a; }
.settings-main, .settings-side { display: flex; flex-direction: column; gap: 16px; min-width: 0; }

.panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px 24px; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }
.panel-title.flush { margin: 0; }
.panel-sub { font-size: 0.82rem; color: #9aaa9a; margin: 4px 0 0; }
.tab-desc { font-size: 0.85rem; color: #6a7a6a; margin: 0 0 16px; line-height: 1.5; }

.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.form-row-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 18px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.8rem; font-weight: 600; color: #4a5a4a; }
.field input, .field select {
  border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px; font-size: 0.87rem; font-family: inherit; color: #1a3a1a; width: 100%; background: #fff;
}
.field input:disabled { background: #f4f5f3; color: #8a9a8a; }
.field input:focus, .field select:focus { outline: none; border-color: #D4A017; }
.field-hint { font-size: 0.72rem; color: #9aaa9a; }

.health-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 18px; }
.health-box { background: #f7f9f7; border-radius: 10px; padding: 14px; text-align: center; }
.health-label { font-size: 0.72rem; color: #9aaa9a; font-weight: 700; margin: 0 0 4px; }
.health-value { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.health-value span { font-size: 0.7rem; font-weight: 400; color: #9aaa9a; }
.health-sub { font-size: 0.72rem; color: #6a7a6a; margin: 4px 0 0; }
.condition-section { border-top: 1px solid #eceeec; margin-top: 22px; padding-top: 20px; }
.section-title { font-family: 'Playfair Display', serif; font-size: 0.98rem; color: #1a3a1a; margin: 0 0 4px; }

.primary-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 11px 20px; font-weight: 700; font-size: 0.87rem; cursor: pointer; }
.primary-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.outline-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 10px 16px; font-weight: 600; font-size: 0.85rem; cursor: pointer; }
.outline-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.outline-btn.small { padding: 8px 14px; font-size: 0.8rem; }
.outline-btn.full-width { width: 100%; }
.danger-outline-btn { border: 1px solid #c0392b; background: #fff; color: #c0392b; border-radius: 8px; padding: 10px 16px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }
.danger-outline-btn.full-width { width: 100%; }

.account-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.account-label { font-size: 0.87rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.account-detail { font-size: 0.78rem; color: #9aaa9a; margin: 2px 0 0; }

.toggle { position: relative; display: inline-block; cursor: pointer; flex-shrink: 0; }
.toggle input { display: none; }
.toggle-track { display: block; width: 40px; height: 22px; background: #e5e8e5; border-radius: 999px; position: relative; transition: background 0.2s; }
.toggle input:checked + .toggle-track { background: #1f8f5c; }
.toggle-thumb { position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; background: #fff; border-radius: 50%; transition: transform 0.2s; }
.toggle input:checked + .toggle-track .toggle-thumb { transform: translateX(18px); }

/* HISTORY */
.panel-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; flex-wrap: wrap; }
.header-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.filter-tabs { display: flex; gap: 4px; background: #f4f5f3; border-radius: 999px; padding: 3px; }
.filter-tab { border: none; background: none; padding: 6px 12px; border-radius: 999px; font-size: 0.76rem; font-weight: 600; color: #6a7a6a; cursor: pointer; }
.filter-tab.active { background: #14301a; color: #fff; }
.print-btn { display: inline-flex; align-items: center; gap: 6px; }
.entry-row { display: flex; align-items: center; gap: 14px; padding: 13px 0; border-top: 1px solid #f0f2f0; }
.entry-row:first-of-type { border-top: none; }
.entry-icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.icon-blue { background: #e3ecf7; color: #2a5a8a; }
.icon-gold { background: #fdf1d6; color: #b8860b; }
.icon-green { background: #e3f3ea; color: #1f8f5c; }
.entry-info { flex: 1; min-width: 0; }
.entry-title { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.entry-detail { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; }
.entry-time { font-size: 0.74rem; color: #9aaa9a; white-space: nowrap; }
.empty-state { padding: 30px; text-align: center; color: #9aaa9a; font-size: 0.85rem; }
.empty-state p { margin: 0; }
.empty-icon { color: #d5dad5; margin-bottom: 8px; }
.empty-sub { font-size: 0.78rem; margin-top: 4px !important; }

/* CARE TEAM */
.rnd-row { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.rnd-avatar { width: 48px; height: 48px; border-radius: 50%; background: #00382a; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.rnd-name { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0; text-decoration: none; }
.rnd-name:hover { text-decoration: underline; }
.rnd-specialty { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; }
.rnd-rating { font-size: 0.78rem; color: #b8860b; font-weight: 600; margin: 2px 0 0; }

.danger-panel { border-color: #f5d5cf; }
.danger-text { font-size: 0.83rem; color: #6a7a6a; margin: 0 0 14px; }

/* TOAST */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

@media (max-width: 1100px) {
  .settings-layout { grid-template-columns: 1fr; }
  .settings-nav { flex-direction: row; overflow-x: auto; }
}
@media (max-width: 640px) {
  .form-row-2, .form-row-3, .health-grid { grid-template-columns: 1fr; }
}

@media print {
  .profile-banner, .settings-nav, .settings-side, .header-actions { display: none !important; }
  .settings-layout { grid-template-columns: 1fr; }
}
</style>
