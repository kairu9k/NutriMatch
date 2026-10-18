<template>
  <!-- Same layout as the RND Profile Settings (RNDProfileSettings.vue): page
       header, tab list on the left, one panel on the right. -->
  <div class="profile-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Profile Settings</h1>
        <p class="page-sub">Manage your personal details, health profile, and account preferences.</p>
      </div>
      <span class="role-pill"><User :size="14" /> Patient</span>
    </div>

    <p v-if="loadError" class="form-error">{{ loadError }}</p>

    <div class="profile-layout">
      <!-- TABS -->
      <div class="tab-card">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          type="button"
          @click="activeTab = tab.key"
        >
          <component :is="tab.icon" :size="17" />
          {{ tab.label }}
        </button>
      </div>

      <!-- PANEL -->
      <div class="panel-card">
        <!-- ============ PERSONAL INFO ============ -->
        <!-- Read-only until "Edit Profile"; Save/Cancel replace it while editing. -->
        <template v-if="activeTab === 'personal'">
          <ProfileIdentityHeader :name="displayName" :subtitle="identitySubtitle" @photo-changed="fireToast">
            <template #actions>
              <button v-if="!isEditing" class="btn-dark" type="button" :disabled="!profileLoaded" @click="startEdit">
                <Pencil :size="15" /> Edit Profile
              </button>
              <template v-else>
                <button class="outline-btn" type="button" :disabled="isSaving" @click="cancelEdit">Cancel</button>
                <button class="btn-dark" type="button" :disabled="isSaving" @click="saveProfile">
                  <Check :size="15" /> {{ isSaving ? 'Saving…' : 'Save Changes' }}
                </button>
              </template>
            </template>
          </ProfileIdentityHeader>

          <!-- READ-ONLY VIEW -->
          <dl v-if="!isEditing" class="info-grid">
            <div class="info-item"><dt>First Name</dt><dd>{{ form.firstName || '—' }}</dd></div>
            <div class="info-item"><dt>Last Name</dt><dd>{{ form.lastName || '—' }}</dd></div>
            <div class="info-item"><dt>Email Address</dt><dd>{{ auth.user?.email || '—' }}</dd></div>
            <div class="info-item"><dt>Mobile Number</dt><dd :class="{ muted: !form.phone }">{{ formatPhone(form.phone) || 'Not provided' }}</dd></div>
            <div class="info-item"><dt>Date of Birth</dt><dd :class="{ muted: !form.dateOfBirth }">{{ dobLabel || 'Not provided' }}</dd></div>
            <div class="info-item"><dt>Sex</dt><dd :class="{ muted: !form.sex }">{{ sexLabel || 'Not provided' }}</dd></div>
            <div class="info-item"><dt>Preferred Language</dt><dd :class="{ muted: !form.languageCode }">{{ languageLabel || 'Not provided' }}</dd></div>
            <div class="info-item"><dt>Primary Health Condition</dt><dd :class="{ muted: !conditionLabel }">{{ conditionLabel || 'None / not sure' }}</dd></div>
            <div class="info-item"><dt>Food Allergies</dt><dd :class="{ muted: !background.allergiesList.length }">{{ background.allergiesAnswered ? (background.allergiesList.join(', ') || 'None') : 'Not answered yet' }}</dd></div>
            <div class="info-item"><dt>Dietary Restrictions</dt><dd :class="{ muted: !background.dietList.length }">{{ background.dietList.join(', ') || 'None' }}</dd></div>
            <div class="info-item"><dt>Religion</dt><dd :class="{ muted: !background.religion }">{{ background.religion || 'Not provided' }}</dd></div>
          </dl>

          <!-- EDIT FORM -->
          <template v-else>
            <div class="form-grid">
              <div class="field">
                <label class="field-label" for="pi-first">First Name</label>
                <input id="pi-first" v-model="form.firstName" type="text" class="field-input" :class="{ invalid: fieldErrors.firstName }" maxlength="150" />
                <p v-if="fieldErrors.firstName" class="field-error">{{ fieldErrors.firstName }}</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-last">Last Name</label>
                <input id="pi-last" v-model="form.lastName" type="text" class="field-input" :class="{ invalid: fieldErrors.lastName }" maxlength="150" />
                <p v-if="fieldErrors.lastName" class="field-error">{{ fieldErrors.lastName }}</p>
              </div>
              <div class="field">
                <label class="field-label">Email Address</label>
                <input :value="auth.user?.email" type="email" class="field-input" disabled />
                <p class="field-hint">Email can't be changed here.</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-phone">Mobile Number</label>
                <PhoneInput id="pi-phone" v-model="form.phone" label="mobile number" :error="fieldErrors.phone" />
              </div>
              <div class="field">
                <label class="field-label" for="pi-dob">Date of Birth</label>
                <input id="pi-dob" v-model="form.dateOfBirth" type="date" class="field-input" :class="{ invalid: fieldErrors.dateOfBirth }" :max="latestBirthDate" min="1900-01-01" />
                <p v-if="fieldErrors.dateOfBirth" class="field-error">{{ fieldErrors.dateOfBirth }}</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-sex">Sex</label>
                <select id="pi-sex" v-model="form.sex" class="nm-select block">
                  <option value="">Prefer not to say</option>
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                </select>
              </div>
              <div class="field">
                <label class="field-label" for="pi-lang">Preferred Language</label>
                <select id="pi-lang" v-model="form.languageCode" class="nm-select block">
                  <option value="">Select</option>
                  <option v-for="l in languageOptions" :key="l.code" :value="l.code">{{ l.label }}</option>
                </select>
              </div>
              <div class="field">
                <label class="field-label" for="pi-condition">Primary Health Condition</label>
                <select id="pi-condition" v-model="conditionChoice" class="nm-select block">
                  <option value="">None / not sure</option>
                  <option v-for="c in CONDITION_OPTIONS" :key="c" :value="c">{{ c }}</option>
                  <option value="__other">Other</option>
                </select>
                <p class="field-hint">Your RND sees this on your patient record.</p>
              </div>
              <div v-if="conditionChoice === '__other'" class="field">
                <label class="field-label" for="pi-condition-other">Please specify</label>
                <input id="pi-condition-other" v-model="conditionOther" type="text" maxlength="100" class="field-input" :class="{ invalid: fieldErrors.condition }" placeholder="e.g. High cholesterol" />
                <p v-if="fieldErrors.condition" class="field-error">{{ fieldErrors.condition }}</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-allergies">Food Allergies</label>
                <input id="pi-allergies" v-model="background.allergiesText" type="text" maxlength="300" class="field-input" placeholder="e.g. Shrimp, Peanuts — leave empty if none" />
                <p class="field-hint">Separate with commas. Your RND plans your meals around these.</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-diet">Dietary Restrictions</label>
                <input id="pi-diet" v-model="background.dietText" type="text" maxlength="300" class="field-input" placeholder="e.g. Halal, Low sodium" />
                <p class="field-hint">Separate with commas.</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-religion">Religion</label>
                <select id="pi-religion" v-model="background.religion" class="nm-select block">
                  <option value="">Prefer not to say</option>
                  <option v-for="r in RELIGION_OPTIONS" :key="r" :value="r">{{ r }}</option>
                </select>
              </div>
            </div>
          </template>

          <p v-if="saveError" class="profile-error">{{ saveError }}</p>
        </template>

        <!-- ============ HEALTH PROFILE ============ -->
        <template v-else-if="activeTab === 'health'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Health Profile</h3>
              <p class="tab-panel-sub">Your screening on file — the starting point your progress is measured from.</p>
            </div>
            <button class="outline-btn" type="button" @click="screeningOpen = true">View Screening</button>
          </div>

          <div v-if="screening" class="stat-grid-3">
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Scale :size="17" /></div>
              <p class="mini-stat-value">{{ screening.bmi }}</p>
              <p class="mini-stat-label">BMI · {{ screening.bmi_category }}</p>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Flame :size="17" /></div>
              <p class="mini-stat-value">{{ screening.tdee_kcal ? Math.round(screening.tdee_kcal) : '—' }} <span class="mini-stat-unit">kcal</span></p>
              <p class="mini-stat-label">Daily Target (TDEE)</p>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Activity :size="17" /></div>
              <p class="mini-stat-value">{{ screening.nrs_score ?? '—' }}</p>
              <p class="mini-stat-label">NRS-2002 · {{ nrsLabel(screening.nrs_risk) }}</p>
            </div>
          </div>
          <p v-else class="empty-note">No screening on file yet.</p>

          <p class="field-hint health-note">
            Your primary health condition is under
            <button class="link-btn" type="button" @click="activeTab = 'personal'">Personal Info</button>.
          </p>
        </template>

        <!-- ============ CARE TEAM ============ -->
        <template v-else-if="activeTab === 'care'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Care Team</h3>
              <p class="tab-panel-sub">The RND currently handling your nutrition care.</p>
            </div>
          </div>

          <div v-if="careRnd" class="setting-row">
            <div class="rnd-row">
              <div class="rnd-avatar">{{ careRndInitials }}</div>
              <div>
                <NuxtLink :to="`/rnd-profile-view/${careRnd.user.id}`" class="rnd-name">RND {{ careRnd.user.first_name }} {{ careRnd.user.last_name }}</NuxtLink>
                <p class="rnd-specialty">{{ careRnd.specialization || 'General Practice' }}</p>
                <p v-if="careRnd.review_count" class="rnd-rating">★ {{ Number(careRnd.average_rating).toFixed(1) }} ({{ careRnd.review_count }} review{{ careRnd.review_count === 1 ? '' : 's' }})</p>
              </div>
            </div>
            <button class="outline-btn" type="button" @click="navigateTo('/messages')">Send a Message</button>
          </div>
          <div v-else class="setting-row">
            <div>
              <p class="setting-label">No RND yet</p>
              <p class="setting-detail">You're not connected with an RND yet.</p>
            </div>
            <button class="outline-btn" type="button" @click="navigateTo('/find-rnd')">Find an RND</button>
          </div>
        </template>

        <!-- ============ SECURITY ============ -->
        <template v-else-if="activeTab === 'security'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Security</h3>
              <p class="tab-panel-sub">Keep your account safe.</p>
            </div>
          </div>
          <div class="setting-row">
            <div>
              <p class="setting-label">Password</p>
              <p class="setting-detail">We'll email you a 6-digit code to set a new password.</p>
            </div>
            <button class="outline-btn" type="button" @click="navigateTo('/forgot-password')">Change Password</button>
          </div>
          <div class="setting-row">
            <div>
              <p class="setting-label">Sign Out</p>
              <p class="setting-detail">Sign out of NutriMatch on this device.</p>
            </div>
            <button class="danger-outline-btn" type="button" @click="handleLogout">Sign Out</button>
          </div>
        </template>

        <!-- ============ NOTIFICATIONS ============ -->
        <template v-else-if="activeTab === 'notifications'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Notifications &amp; reminders</h3>
              <p class="tab-panel-sub">NutriMatch reminds you automatically. You always get them in the app — choose which ones, and whether to get emails too.</p>
            </div>
          </div>

          <p v-if="reminderError" class="form-error">{{ reminderError }}</p>
          <p v-if="!reminderPrefs" class="placeholder-text">Loading…</p>
          <template v-else>
            <div v-for="opt in REMINDER_OPTIONS" :key="opt.key" class="setting-row">
              <div>
                <p class="setting-label">{{ opt.label }}</p>
                <p class="setting-detail">{{ opt.detail }}</p>
              </div>
              <label class="toggle">
                <input :checked="reminderPrefs[opt.key]" type="checkbox" @change="savePref(opt.key, $event.target.checked)" />
                <span class="toggle-track"><span class="toggle-thumb"></span></span>
              </label>
            </div>
            <div class="setting-row">
              <div>
                <p class="setting-label">Also send reminders by email</p>
                <p class="setting-detail">To {{ auth.user?.email }}. Off by default — in-app notifications are always on.</p>
              </div>
              <label class="toggle">
                <input :checked="reminderPrefs.email" type="checkbox" @change="savePref('email', $event.target.checked)" />
                <span class="toggle-track"><span class="toggle-thumb"></span></span>
              </label>
            </div>
            <div class="setting-row">
              <div>
                <p class="setting-label">Also send reminders by text (SMS)</p>
                <p v-if="reminderPrefs.sms_number" class="setting-detail">To {{ reminderPrefs.sms_number }}. Consultation, payment and task reminders only — short texts with no health details.</p>
                <p v-else-if="auth.user?.phone" class="setting-detail">SMS reminders are only available for Philippine mobile numbers (+63). Yours is {{ formatPhone(auth.user.phone) }}.</p>
                <p v-else class="setting-detail">Add your mobile number (e.g. 0917 123 4567) in Personal Info first.</p>
              </div>
              <label class="toggle">
                <input :checked="reminderPrefs.sms" :disabled="!reminderPrefs.sms_number && !reminderPrefs.sms" type="checkbox" @change="savePref('sms', $event.target.checked)" />
                <span class="toggle-track"><span class="toggle-thumb"></span></span>
              </label>
            </div>

            <div class="rnd-reminders">
              <p class="setting-label" style="margin-bottom: 4px">Set by your RND</p>
              <p class="setting-detail" style="margin-bottom: 12px">Medication and habit reminders your RND set for you. Mute one if you don't need it.</p>
              <p v-if="!rndReminders.length" class="placeholder-text">Your RND hasn't set any reminders for you.</p>
              <div v-for="r in rndReminders" :key="r.id" class="rnd-reminder" :class="{ muted: r.is_muted }">
                <span class="rr-icon"><component :is="r.type === 'medication' ? Pill : AlarmClock" :size="16" /></span>
                <div class="rr-main">
                  <p class="rr-title">{{ r.title }}</p>
                  <p class="rr-sub">{{ r.repeat_label }} at {{ clock(r.time_of_day) }}<template v-if="r.repeat === 'once'"> · {{ dayLabel(r.next_at) }}</template> · from RND {{ r.created_by_name }}</p>
                  <p v-if="r.message" class="rr-msg">{{ r.message }}</p>
                </div>
                <label class="toggle" :title="r.is_muted ? 'Muted' : 'On'">
                  <input :checked="!r.is_muted" type="checkbox" @change="setMuted(r, !$event.target.checked)" />
                  <span class="toggle-track"><span class="toggle-thumb"></span></span>
                </label>
              </div>
            </div>
          </template>
        </template>

        <!-- ============ PRIVACY & DATA ============ -->
        <template v-else-if="activeTab === 'privacy'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Privacy &amp; Data</h3>
              <p class="tab-panel-sub">How your information is handled.</p>
            </div>
          </div>
          <div class="setting-row">
            <div>
              <p class="setting-label">Data sharing</p>
              <p class="setting-detail">Your health data is only shared with your assigned RND under RA 10173 (Data Privacy Act of 2012).</p>
            </div>
            <!-- TODO: no data-export endpoint exists yet. -->
            <button class="outline-btn" type="button" disabled title="Coming soon">Download My Data</button>
          </div>
        </template>

        <!-- ============ HISTORY ============ -->
        <template v-else-if="activeTab === 'history'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Your Activity</h3>
              <p class="tab-panel-sub">Every screening, appointment, and meal log on your account.</p>
            </div>
            <button class="outline-btn print-btn" type="button" @click="printHistory"><Printer :size="14" /> Print</button>
          </div>

          <div class="filter-tabs">
            <button v-for="f in historyFilters" :key="f.key" class="filter-tab" :class="{ active: historyFilter === f.key }" type="button" @click="historyFilter = f.key">{{ f.label }}</button>
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
        </template>
      </div>
    </div>

    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle2 :size="16" /> {{ toastMessage }}
      </div>
    </Transition>
    <ScreeningModal v-if="screeningOpen" @close="screeningOpen = false" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  User, HeartPulse, Shield, Bell, FileText, History as HistoryIcon, CheckCircle2,
  Printer, ClipboardList, ShieldCheck, CalendarCheck, UtensilsCrossed,
  Stethoscope, Scale, Flame, Activity, Pencil, Check, AlarmClock, Pill,
} from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'
import { formatPhone, phoneError } from '~/utils/phone'

const auth = useAuthStore()
const { get, patch, put } = useApi()

const tabs = [
  { key: 'personal', label: 'Personal Info', icon: User },
  { key: 'health', label: 'Health Profile', icon: HeartPulse },
  { key: 'care', label: 'Care Team', icon: Stethoscope },
  { key: 'security', label: 'Security', icon: Shield },
  { key: 'notifications', label: 'Notifications', icon: Bell },
  { key: 'privacy', label: 'Privacy & Data', icon: FileText },
  { key: 'history', label: 'History', icon: HistoryIcon },
]
// ?tab=health etc. opens a tab directly, like the RND settings page.
const route = useRoute()
const screeningOpen = ref(false) // View Screening pop-up
const activeTab = ref(tabs.some(t => t.key === route.query.tab) ? route.query.tab : 'personal')

const languageOptions = [
  { code: 'tl', label: 'Filipino (Tagalog)' },
  { code: 'ceb', label: 'Bisaya (Cebuano)' },
  { code: 'ilo', label: 'Ilocano' },
  { code: 'en', label: 'English' },
]

const loadError = ref('')
const displayName = computed(() => `${auth.user?.first_name || ''} ${auth.user?.last_name || ''}`.trim())
const initials = computed(() => `${auth.user?.first_name?.[0] || ''}${auth.user?.last_name?.[0] || ''}`.toUpperCase())
const identitySubtitle = computed(() =>
  [auth.user?.email, memberSince.value && `Member since ${memberSince.value}`].filter(Boolean).join(' · ')
)
const memberSince = computed(() =>
  auth.user?.created_at ? new Date(auth.user.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : ''
)

/* ---------- Personal info (read-only until Edit Profile) ---------- */
const form = reactive({ firstName: '', lastName: '', phone: '', dateOfBirth: '', sex: '', languageCode: '' })
const isSaving = ref(false)
const saveError = ref('')
const isEditing = ref(false)
const profileLoaded = ref(false)
// Last profile from the API — Cancel restores the form from it.
const lastProfile = ref(null)
const fieldErrors = reactive({ firstName: '', lastName: '', phone: '', dateOfBirth: '', condition: '' })

// Same rules the API enforces (accounts/validators.py): clients are 18+.
const MIN_CLIENT_AGE = 18
const latestBirthDate = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - MIN_CLIENT_AGE)
  return d.toISOString().slice(0, 10)
})
const NAME_RE = /^[A-Za-zÀ-ÖØ-öø-ÿÑñ]+(?:[ '.-][A-Za-zÀ-ÖØ-öø-ÿÑñ]+)*\.?$/

const sexLabel = computed(() => ({ female: 'Female', male: 'Male' }[form.sex] || ''))
const languageLabel = computed(() => languageOptions.find(l => l.code === form.languageCode)?.label || '')
const dobLabel = computed(() => {
  if (!form.dateOfBirth) return ''
  const d = new Date(`${form.dateOfBirth}T00:00:00`)
  const now = new Date()
  let age = now.getFullYear() - d.getFullYear()
  if (now.getMonth() < d.getMonth() || (now.getMonth() === d.getMonth() && now.getDate() < d.getDate())) age--
  return `${d.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })} (${age} years old)`
})
const conditionLabel = computed(() =>
  conditionChoice.value === '__other' ? conditionOther.value.trim() : conditionChoice.value
)

function clearFieldErrors() {
  Object.keys(fieldErrors).forEach(k => { fieldErrors[k] = '' })
}
function startEdit() {
  saveError.value = ''
  clearFieldErrors()
  isEditing.value = true
}
function cancelEdit() {
  if (lastProfile.value) {
    fillForm(lastProfile.value)
    fillCondition(lastProfile.value)
  }
  saveError.value = ''
  clearFieldErrors()
  isEditing.value = false
}

function fillForm(profile) {
  form.firstName = profile.user.first_name || ''
  form.lastName = profile.user.last_name || ''
  form.phone = profile.user.phone || ''
  form.dateOfBirth = profile.date_of_birth || ''
  form.sex = profile.sex || ''
  form.languageCode = profile.language_code || ''
}

function validatePersonal() {
  clearFieldErrors()
  form.firstName = form.firstName.trim()
  form.lastName = form.lastName.trim()
  if (!form.firstName) fieldErrors.firstName = 'Enter your first name.'
  else if (!NAME_RE.test(form.firstName)) fieldErrors.firstName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  if (!form.lastName) fieldErrors.lastName = 'Enter your last name.'
  else if (!NAME_RE.test(form.lastName)) fieldErrors.lastName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  fieldErrors.phone = phoneError(form.phone)
  if (!form.dateOfBirth) fieldErrors.dateOfBirth = 'Enter your date of birth.'
  else if (form.dateOfBirth > latestBirthDate.value) fieldErrors.dateOfBirth = `You must be at least ${MIN_CLIENT_AGE} years old.`
  else if (form.dateOfBirth < '1900-01-01') fieldErrors.dateOfBirth = 'Enter a valid date of birth.'
  if (conditionChoice.value === '__other' && !conditionOther.value.trim()) fieldErrors.condition = 'Please type your condition, or pick one from the list.'
  return !Object.values(fieldErrors).some(Boolean)
}

// One Save for everything on the tab, including the primary condition.
async function saveProfile() {
  saveError.value = ''
  if (!validatePersonal()) return
  isSaving.value = true
  const primary = conditionChoice.value === '__other' ? conditionOther.value.trim() : conditionChoice.value
  try {
    const [, profile] = await Promise.all([
      patch('/auth/me/', { first_name: form.firstName, last_name: form.lastName, phone: form.phone || null }),
      patch('/client/profile/', {
        date_of_birth: form.dateOfBirth || null,
        sex: form.sex || null,
        language_code: form.languageCode || null,
        medical_conditions: primary ? [primary, ...otherConditions.value] : otherConditions.value,
        // Health background (also asked during onboarding). An empty allergy
        // list means "no food allergies".
        allergies: splitList(background.allergiesText),
        dietary_restrictions: splitList(background.dietText),
        religion: background.religion,
      }),
    ])
    await auth.fetchMe()
    loadReminders() // the SMS setting shows the (new) number
    // The API capitalizes names; show exactly what was saved.
    const saved = await get('/client/profile/').catch(() => profile)
    lastProfile.value = saved
    fillForm(saved)
    fillCondition(saved)
    isEditing.value = false
    fireToast()
  } catch (error) {
    const data = error?.data || {}
    const first = (v) => (Array.isArray(v) ? v[0] : v) || ''
    fieldErrors.firstName = first(data.first_name)
    fieldErrors.lastName = first(data.last_name)
    fieldErrors.phone = first(data.phone)
    fieldErrors.dateOfBirth = first(data.date_of_birth)
    const shown = fieldErrors.firstName || fieldErrors.lastName || fieldErrors.phone || fieldErrors.dateOfBirth
    saveError.value = shown ? '' : data.detail || Object.values(data).flat()[0] || 'Could not save your changes. Please try again.'
  } finally {
    isSaving.value = false
  }
}

const toastVisible = ref(false)
const toastMessage = ref('Profile updated!')
let toastTimer = null
function fireToast(message = 'Profile updated!') {
  toastMessage.value = message
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

/* ---------- Health background (allergies / diet / religion) ---------- */
const RELIGION_OPTIONS = ['Roman Catholic', 'Christian', 'Islam', 'Iglesia ni Cristo', 'Seventh-day Adventist', 'Other']
const background = reactive({ allergiesAnswered: false, allergiesList: [], dietList: [], religion: '', allergiesText: '', dietText: '' })
function splitList(text) {
  const seen = new Set()
  return text.split(',').map(x => x.trim()).filter(x => x && !seen.has(x.toLowerCase()) && seen.add(x.toLowerCase()))
}
function fillBackground(profile) {
  const hp = profile.health_profile || {}
  background.allergiesAnswered = Array.isArray(hp.allergies)
  background.allergiesList = [...(hp.allergies || [])]
  background.dietList = [...(hp.dietary_restrictions || [])]
  background.religion = hp.religion || ''
  background.allergiesText = background.allergiesList.join(', ')
  background.dietText = background.dietList.join(', ')
}

function fillCondition(profile) {
  fillBackground(profile)
  const conditions = profile.health_profile?.medical_conditions || []
  const primary = conditions[0] || ''
  otherConditions.value = conditions.slice(1)
  conditionOther.value = ''
  if (!primary) {
    conditionChoice.value = ''
  } else if (CONDITION_OPTIONS.includes(primary)) {
    conditionChoice.value = primary
  } else {
    conditionChoice.value = '__other'
    conditionOther.value = primary
  }
}

function nrsLabel(risk) {
  return { no_risk: 'No Risk', at_risk: 'At Risk', high_risk: 'High Risk' }[risk] || ''
}

// TODO: mock/local only — no notification-preference field on User/ClientProfile.
/* ---------- NOTIFICATIONS & REMINDERS ---------- */
const REMINDER_OPTIONS = [
  { key: 'appointments', label: 'Consultation reminders', detail: '24 hours and 1 hour before each confirmed consultation.' },
  { key: 'payments', label: 'Payment reminders', detail: "If a consultation is still unpaid the day before — unpaid ones are cancelled at the start time." },
  { key: 'meal_logging', label: 'Meal logging reminders', detail: "At each meal time in your meal plan, if you haven't logged that meal yet." },
  { key: 'rnd_reminders', label: 'Reminders from your RND', detail: 'Medication and habit reminders your RND sets for you.' },
]
const reminderPrefs = ref(null)
const rndReminders = ref([])
const reminderError = ref('')
async function loadReminders() {
  try {
    const [prefs, list] = await Promise.all([get('/client/reminder-settings/'), get('/client/reminders/')])
    reminderPrefs.value = prefs
    rndReminders.value = list
  } catch {
    reminderError.value = 'Could not load your reminder settings. Please refresh.'
  }
}
async function savePref(key, value) {
  const before = reminderPrefs.value[key]
  reminderPrefs.value[key] = value
  reminderError.value = ''
  try {
    reminderPrefs.value = await put('/client/reminder-settings/', { [key]: value })
    fireReminderToast(value ? 'Turned on.' : 'Turned off.')
  } catch (error) {
    reminderPrefs.value[key] = before
    reminderError.value = error?.data?.[key]?.[0] || 'Could not save. Please try again.'
  }
}
async function setMuted(r, muted) {
  try {
    Object.assign(r, await patch(`/client/reminders/${r.id}/`, { is_muted: muted }))
    fireReminderToast(muted ? 'Reminder muted.' : 'Reminder turned back on.')
  } catch {
    reminderError.value = 'Could not update this reminder. Please try again.'
  }
}
function clock(hhmm) {
  const [h, m] = String(hhmm || '00:00').split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}
function dayLabel(iso) {
  return iso ? new Date(iso).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'short', month: 'short', day: 'numeric' }) : ''
}
function fireReminderToast(text) {
  fireToast(text)
}
onMounted(loadReminders)

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
        detail: `${LOG_STATUS[l.status] || 'Waiting for your RND to rate it'} · ${l.log_date}${l.reason_notes ? ` · ${l.reason_notes}` : ''}`,
      })),
    ].sort((x, y) => new Date(y.at) - new Date(x.at))
    historyLoaded = true
  } finally {
    isLoadingHistory.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'history' && !historyLoaded) loadHistory()
}, { immediate: true })

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
    lastProfile.value = profile
    fillForm(profile)
    fillCondition(profile)
    profileLoaded.value = true
    screening.value = latestScreening
    const active = relationships.find(r => r.status === 'active')
    if (active) careRnd.value = await get(`/client/rnds/${active.rnd.id}/`).catch(() => null)
  } catch {
    loadError.value = 'Could not load your profile. Please try again later.'
  }
})
</script>

<style scoped>
/* Mirrors RNDProfileSettings.vue — keep the two in step. */
* { box-sizing: border-box; }

.profile-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.role-pill {
  display: inline-flex; align-items: center; gap: 6px;
  background: #e6efe0; color: #3a6b3a; font-size: 0.78rem; font-weight: 700;
  padding: 7px 14px; border-radius: 20px; white-space: nowrap;
}

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

/* LAYOUT */
.profile-layout { display: grid; grid-template-columns: 280px 1fr; gap: 20px; align-items: start; }

.tab-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 10px; display: flex; flex-direction: column; gap: 2px;
}
.tab-item {
  display: flex; align-items: center; gap: 10px; text-align: left;
  border: none; background: none; border-radius: 8px; padding: 12px 14px;
  font-size: 0.88rem; font-weight: 600; color: #4a5a4a; cursor: pointer; font-family: inherit;
  white-space: nowrap;
}
.tab-item:hover { background: #f7f9f7; }
.tab-item.active { background: #eef3ec; color: #1a3a1a; }

.panel-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 28px; min-width: 0;
}


/* Same as the "Create Meal Plan" button (MealPlanning.vue .btn-primary). */
.btn-dark {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  background: #163a1c; color: #fff; border: none;
  padding: 9px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
  white-space: nowrap; font-family: inherit;
}
.btn-dark:hover:not(:disabled) { background: #0f2a14; }
.btn-dark:disabled { opacity: 0.5; cursor: not-allowed; }

/* READ-ONLY PERSONAL INFO */
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; margin: 0; }
.info-item { padding: 14px 0; border-top: 1px solid #f0f2f0; min-width: 0; }
.info-item:nth-child(-n + 2) { border-top: none; padding-top: 0; }
.info-item dt { font-size: 0.76rem; font-weight: 600; color: #8a9a8a; margin: 0 0 4px; }
.info-item dd { font-size: 0.92rem; font-weight: 500; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.info-item dd.muted { color: #aab5aa; font-weight: 400; }
.field-error { font-size: 0.76rem; color: #c0392b; margin: 4px 0 0; }
.field-input.invalid { border-color: #c0392b; }
.health-note { margin-top: 18px; }
.link-btn { background: none; border: none; padding: 0; color: #1a3a1a; font-weight: 700; text-decoration: underline; cursor: pointer; font: inherit; }

/* FORM */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 24px; margin-bottom: 24px; }
.field { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; margin: 0 0 8px; }
.field-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 12px 14px;
  font-size: 0.88rem; color: #2a2a2a; font-family: inherit; background: #fff;
}
.field-input:focus { outline: none; border-color: #D4A017; }
.field-input:disabled { background: #f4f5f3; color: #8a9a8a; }
.field select { min-height: 47px; font-size: 0.88rem; }
.field-hint { font-size: 0.76rem; color: #9aaa9a; margin: 6px 0 0; }
.section-hint { margin: -8px 0 16px; }
.profile-error { font-size: 0.82rem; color: #a12525; margin: 0 0 12px; }

.save-btn {
  display: flex; align-items: center; gap: 6px;
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 12px 22px; font-weight: 700; font-size: 0.88rem; cursor: pointer; white-space: nowrap; font-family: inherit;
}
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.outline-btn {
  display: inline-flex; align-items: center; gap: 6px; flex-shrink: 0;
  border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px;
  padding: 10px 16px; font-weight: 600; font-size: 0.84rem; cursor: pointer; white-space: nowrap; font-family: inherit;
}
.outline-btn:hover:not(:disabled) { background: #f7f9f7; }
.outline-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.danger-outline-btn {
  flex-shrink: 0; border: 1px solid #c0392b; background: #fff; color: #c0392b; border-radius: 8px;
  padding: 10px 16px; font-weight: 700; font-size: 0.84rem; cursor: pointer; white-space: nowrap; font-family: inherit;
}
.danger-outline-btn:hover { background: #fdecec; }

/* SHARED TAB PANEL HEADER */
.tab-panel-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; gap: 16px; }
.tab-panel-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0 0 4px; }
.tab-panel-sub { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
.sub-panel { border-top: 1px solid #f0f2f0; padding-top: 20px; margin-top: 24px; }
.sub-panel-title { font-family: 'Playfair Display', serif; font-size: 1rem; color: #1a3a1a; margin: 0 0 16px; }
.empty-note { font-size: 0.85rem; color: #9aaa9a; text-align: center; padding: 30px 0; margin: 0; }

/* HEALTH STATS */
.stat-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.mini-stat-card { background: #fafbfa; border-radius: 10px; padding: 16px 18px; border: 1px solid #f0f2f0; }
.mini-stat-icon {
  width: 30px; height: 30px; border-radius: 8px; background: #eef1ee;
  display: flex; align-items: center; justify-content: center; color: #4a5a4a; margin-bottom: 10px;
}
.mini-stat-value { font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.mini-stat-unit { font-family: 'Inter', sans-serif; font-size: 0.72rem; font-weight: 500; color: #9aaa9a; }
.mini-stat-label { font-size: 0.75rem; color: #8a9a8a; margin: 3px 0 0; }

/* SETTING ROWS (security, notifications, privacy, care team) */
.rnd-reminders { margin-top: 22px; padding-top: 18px; border-top: 1px solid #f0f2f0; }
.rnd-reminder { display: flex; align-items: flex-start; gap: 12px; padding: 12px 14px; border: 1px solid #eceeec; border-radius: 12px; margin-bottom: 8px; }
.rnd-reminder.muted { opacity: 0.6; }
.rr-icon { width: 32px; height: 32px; border-radius: 9px; background: #fdf1d6; color: #b8860b; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.rr-main { flex: 1; min-width: 0; }
.rr-title { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.rr-sub { font-size: 0.76rem; color: #8a9a8a; margin: 2px 0 0; }
.rr-msg { font-size: 0.8rem; color: #4a5a4a; margin: 6px 0 0; line-height: 1.45; overflow-wrap: anywhere; }
.setting-row {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 16px 18px; margin-bottom: 12px;
}
.setting-label { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.setting-detail { font-size: 0.8rem; color: #8a9a8a; margin: 3px 0 0; line-height: 1.5; }

.toggle { position: relative; display: inline-block; cursor: pointer; flex-shrink: 0; }
.toggle input { display: none; }
.toggle-track { display: block; width: 40px; height: 22px; background: #e5e8e5; border-radius: 999px; position: relative; transition: background 0.2s; }
.toggle input:checked + .toggle-track { background: #1f8f5c; }
.toggle-thumb { position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; background: #fff; border-radius: 50%; transition: transform 0.2s; }
.toggle input:checked + .toggle-track .toggle-thumb { transform: translateX(18px); }

/* CARE TEAM */
.rnd-row { display: flex; align-items: center; gap: 14px; min-width: 0; }
.rnd-avatar { width: 48px; height: 48px; border-radius: 50%; background: #00382a; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.rnd-name { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0; text-decoration: none; }
.rnd-name:hover { text-decoration: underline; }
.rnd-specialty { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; }
.rnd-rating { font-size: 0.78rem; color: #b8860b; font-weight: 600; margin: 2px 0 0; }

/* HISTORY */
.filter-tabs { display: inline-flex; gap: 4px; background: #f4f5f3; border-radius: 999px; padding: 3px; margin-bottom: 14px; flex-wrap: wrap; }
.filter-tab { border: none; background: none; padding: 6px 12px; border-radius: 999px; font-size: 0.76rem; font-weight: 600; color: #6a7a6a; cursor: pointer; font-family: inherit; }
.filter-tab.active { background: #14301a; color: #fff; }
.entry-row { display: flex; align-items: center; gap: 14px; padding: 13px 0; border-top: 1px solid #f0f2f0; }
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

/* TOAST */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

/* MOBILE — tabs become a sideways-scrolling strip above the panel. */
@media (max-width: 900px) {
  .profile-layout { grid-template-columns: 1fr; }
  .tab-card { flex-direction: row; overflow-x: auto; scrollbar-width: none; }
  .tab-card::-webkit-scrollbar { display: none; }
  .tab-item { flex-shrink: 0; padding: 10px 12px; }
}
@media (max-width: 640px) {
  .page-header { flex-direction: column; gap: 10px; }
  .page-title { font-size: 1.4rem; }
  .panel-card { padding: 20px 16px; }
  .form-grid, .stat-grid-3, .info-grid { grid-template-columns: 1fr; }
  .info-item:nth-child(2) { border-top: 1px solid #f0f2f0; padding-top: 14px; }
  .tab-panel-header, .setting-row { flex-direction: column; align-items: stretch; }
  .outline-btn, .danger-outline-btn, .save-btn { justify-content: center; }
  .entry-row { flex-wrap: wrap; }
  .entry-time { width: 100%; padding-left: 48px; }
}

@media print {
  .page-header, .tab-card, .print-btn, .filter-tabs { display: none !important; }
  .profile-layout { grid-template-columns: 1fr; }
  .panel-card { border: none; padding: 0; }
}
</style>
