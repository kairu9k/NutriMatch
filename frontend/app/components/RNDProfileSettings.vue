<template>
  <div class="profile-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Profile Settings</h1>
        <p class="page-sub">Manage your professional profile, credentials, and preferences.</p>
      </div>
      <span v-if="personalInfo.prcVerified" class="verified-pill">
        <BadgeCheck :size="14" />
        PRC Verified
      </span>
    </div>

    <div class="profile-layout">
      <!-- TABS -->
      <div ref="tabCard" class="tab-card">
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
        <!-- ============ PROFESSIONAL PROFILE ============ -->
        <!-- Same pattern as the client's Personal Info tab: read-only until
             "Edit Profile"; Cancel/Save replace it while editing. -->
        <template v-if="activeTab === 'professional'">
          <ProfileIdentityHeader :name="identityName" :subtitle="identitySubtitle" @photo-changed="fireToast">
            <template #actions>
              <button v-if="!isEditing" class="btn-dark" type="button" :disabled="!profileLoaded" @click="startEdit">
                <Pencil :size="15" /> Edit Profile
              </button>
              <template v-else>
                <button class="outline-btn" type="button" :disabled="isSavingProfile" @click="cancelEdit">Cancel</button>
                <button class="btn-dark" type="button" :disabled="isSavingProfile" @click="saveChanges">
                  <Check :size="15" /> {{ isSavingProfile ? 'Saving…' : 'Save Changes' }}
                </button>
              </template>
            </template>
          </ProfileIdentityHeader>

          <!-- READ-ONLY VIEW -->
          <template v-if="!isEditing">
            <dl class="info-grid">
              <div class="info-item"><dt>First Name</dt><dd>{{ personalInfo.firstName || '—' }}</dd></div>
              <div class="info-item"><dt>Last Name</dt><dd>{{ personalInfo.lastName || '—' }}</dd></div>
              <div class="info-item"><dt>Email Address</dt><dd>{{ personalInfo.email || '—' }}</dd></div>
              <div class="info-item"><dt>Mobile Number</dt><dd :class="{ muted: !personalInfo.phone }">{{ formatPhone(personalInfo.phone) || 'Not provided' }}</dd></div>
            </dl>
          </template>

          <!-- EDIT FORM -->
          <div v-else class="form-grid">
            <div class="field">
              <label class="field-label" for="rp-first">First Name</label>
              <input id="rp-first" v-model="personalInfo.firstName" type="text" class="field-input" :class="{ invalid: fieldErrors.firstName }" maxlength="150" />
              <p v-if="fieldErrors.firstName" class="field-error">{{ fieldErrors.firstName }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="rp-last">Last Name</label>
              <input id="rp-last" v-model="personalInfo.lastName" type="text" class="field-input" :class="{ invalid: fieldErrors.lastName }" maxlength="150" />
              <p v-if="fieldErrors.lastName" class="field-error">{{ fieldErrors.lastName }}</p>
            </div>
            <div class="field">
              <label class="field-label">Email Address</label>
              <input :value="personalInfo.email" type="email" class="field-input" disabled />
              <p class="field-hint">Email can't be changed here.</p>
            </div>
            <div class="field">
              <label class="field-label" for="rp-phone">Mobile Number</label>
              <PhoneInput id="rp-phone" v-model="personalInfo.phone" label="mobile number" rnd :error="fieldErrors.phone" />
              <p v-if="!fieldErrors.phone" class="field-hint">Required — a Philippine mobile number. Not shown to clients.</p>
            </div>
          </div>

          <!-- PRC LICENSE — always read-only: set at registration, checked by the admin -->
          <div class="prc-section">
            <div class="prc-header">
              <span class="field-label prc-title"><Lock :size="13" /> PRC License</span>
              <span class="prc-status" :class="personalInfo.prcVerified ? 'prc-verified' : 'prc-pending'">
                {{ personalInfo.prcVerified ? 'Verified' : 'Pending admin verification' }}
              </span>
            </div>
            <dl class="info-grid">
              <div class="info-item"><dt>PRC License Number</dt><dd :class="{ muted: !personalInfo.prcNumber }">{{ personalInfo.prcNumber || 'Not provided' }}</dd></div>
              <div class="info-item"><dt>Verified On</dt><dd :class="{ muted: !personalInfo.prcVerifiedOn }">{{ personalInfo.prcVerifiedOn || 'Not yet verified' }}</dd></div>
              <div class="info-item"><dt>Specialization</dt><dd :class="{ muted: !personalInfo.specialization }">{{ personalInfo.specialization || 'Not set' }}</dd></div>
            </dl>
            <a v-if="personalInfo.prcPhotoUrl" :href="personalInfo.prcPhotoUrl" target="_blank" rel="noopener" class="prc-photo-link">
              <FileImage :size="15" /> View license photo
            </a>
            <p class="field-hint">Your PRC details and specialization can't be edited here. To update them, contact the NutriMatch admin.</p>
          </div>

          <div class="newclients-row">
            <div>
              <p class="newclients-label">Taking new clients</p>
              <p class="field-hint">{{ personalInfo.acceptingNewClients
                ? 'New clients can find and book you. Turn it off when your schedule is full.'
                : 'Hidden from new clients on Find an RND — your current patients can still book you.' }}</p>
            </div>
            <label class="toggle">
              <input type="checkbox" :checked="personalInfo.acceptingNewClients" :disabled="savingNewClients" aria-label="Taking new clients" @change="toggleNewClients($event.target.checked)" />
              <span class="toggle-track"><span class="toggle-thumb" /></span>
            </label>
          </div>

          <!-- READ-ONLY: bio / fee / formats -->
          <dl v-if="!isEditing" class="info-stack">
            <div class="info-item">
              <dt>Professional Bio</dt>
              <dd :class="{ muted: !personalInfo.bio }" class="bio-text">{{ personalInfo.bio || 'Not provided' }}</dd>
            </div>
            <div class="info-item">
              <dt>Consultation Fee</dt>
              <dd :class="{ muted: personalInfo.consultationFee === '' }">
                {{ personalInfo.consultationFee === '' ? 'Not set' : `₱${Number(personalInfo.consultationFee).toLocaleString()} per session` }}
              </dd>
            </div>
            <div class="info-item">
              <dt>Consultation Formats</dt>
              <dd>
                <span v-if="!personalInfo.consultationModes.length" class="muted">None offered</span>
                <span v-for="m in MODE_OPTIONS.filter(o => personalInfo.consultationModes.includes(o.value))" :key="m.value" class="mode-chip">
                  <component :is="m.icon" :size="14" /> {{ m.label }}
                </span>
              </dd>
            </div>
            <div v-if="personalInfo.consultationModes.includes('in_person')" class="info-item">
              <dt>Clinic Address</dt>
              <dd :class="{ muted: !personalInfo.clinicAddress }">
                {{ personalInfo.clinicAddress || 'Not added yet — clients can\'t book in-person consultations until you add it.' }}
              </dd>
            </div>
          </dl>

          <template v-else>
            <div class="field field-bio">
              <div class="bio-label-row">
                <label class="field-label" for="rp-bio">Professional Bio</label>
                <span class="bio-count" :class="{ 'bio-count-warn': personalInfo.bio.length > 500 }">{{ personalInfo.bio.length }}/500</span>
              </div>
              <textarea
                id="rp-bio"
                v-model="personalInfo.bio"
                maxlength="500"
                rows="4"
                class="field-input bio-textarea"
                placeholder="Tell patients about your background, specialization, and approach to nutrition care..."
              ></textarea>
              <p class="field-hint">Shown on your public profile when patients search for an RND.</p>
            </div>

            <div class="field field-bio fee-field">
              <label class="field-label" for="rp-fee">Consultation Fee</label>
              <div class="fee-input-wrap">
                <span class="fee-prefix">₱</span>
                <input id="rp-fee" v-model="personalInfo.consultationFee" type="number" min="100" step="50" class="field-input fee-input" placeholder="e.g. 750" />
                <span class="fee-suffix">per session</span>
              </div>
              <p class="field-hint">At least ₱100. Shown to patients on Find an RND and your profile. Changes apply to future invoices only.</p>
            </div>

            <div class="field field-bio">
              <label class="field-label">Consultation Formats</label>
              <div class="mode-options">
                <label v-for="m in MODE_OPTIONS" :key="m.value" class="mode-option" :class="{ checked: personalInfo.consultationModes.includes(m.value) }">
                  <input v-model="personalInfo.consultationModes" type="checkbox" :value="m.value" />
                  <component :is="m.icon" :size="15" /> {{ m.label }}
                </label>
              </div>
              <p class="field-hint">Patients can only book the formats you offer.</p>
            </div>

            <div v-if="personalInfo.consultationModes.includes('in_person')" class="field field-bio">
              <label class="field-label" for="rp-address">Clinic Address</label>
              <input id="rp-address" v-model="personalInfo.clinicAddress" type="text" class="field-input" :class="{ invalid: fieldErrors.clinicAddress }"
                maxlength="255" placeholder="e.g. 2F Bajada Medical Bldg, J.P. Laurel Ave, Bajada, Davao City" />
              <p v-if="fieldErrors.clinicAddress" class="field-error">{{ fieldErrors.clinicAddress }}</p>
              <p v-else class="field-hint">Where clients go for in-person consultations — shown on your profile.</p>
            </div>
          </template>

          <p v-if="profileError" class="profile-error">{{ profileError }}</p>
        </template>

        <!-- ============ EARNINGS ============ -->
        <!-- ============ AVAILABILITY ============ -->
        <template v-else-if="activeTab === 'availability'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Availability</h3>
              <p class="tab-panel-sub">Set the hours clients can book consultations with you.</p>
            </div>
          </div>

          <!-- Real, saved schedule (RndAvailabilitySchedule) — the same one
               clients see on your profile and in the booking calendar. -->
          <Availability embedded />
        </template>

        <!-- ============ LANGUAGES ============ -->
        <template v-else-if="activeTab === 'languages'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Languages</h3>
              <p class="tab-panel-sub">Languages you can communicate with patients in.</p>
            </div>
          </div>

          <div v-if="languages.length" class="language-list">
            <span v-for="lang in languages" :key="lang.id" class="language-pill">
              {{ lang.name }}
              <button class="pill-icon-btn" type="button" @click="removeLanguage(lang)"><X :size="13" /></button>
            </span>
          </div>
          <p v-else class="empty-note">No languages added yet.</p>

          <div class="language-add-row">
            <select v-model="newLanguage" class="nm-select language-select">
              <option value="">Add a language...</option>
              <option v-for="opt in availableLanguageOptions" :key="opt.code" :value="opt.code">{{ opt.name }}</option>
            </select>
            <button class="save-btn" type="button" :disabled="!newLanguage" @click="addLanguage">Add</button>
          </div>
          <p v-if="languageError" class="profile-error">{{ languageError }}</p>
        </template>

        <!-- ============ SECURITY ============ -->
        <!-- Change password right here (POST /api/auth/me/password/): current
             password + a new one with the sign-up rules; a confirmation email
             goes out. Sign out lives in the account menu. -->
        <template v-else-if="activeTab === 'security'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Security</h3>
              <p class="tab-panel-sub">Keep your account safe.</p>
            </div>
          </div>
          <form class="pw-form" novalidate @submit.prevent="changePassword">
            <p class="pw-title">Change password</p>
            <div class="field">
              <label class="field-label" for="rpw-current">Current password</label>
              <input id="rpw-current" v-model="pw.current" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pwErrors.current_password }" autocomplete="current-password" />
              <p v-if="pwErrors.current_password" class="field-error">{{ pwErrors.current_password }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="rpw-new">New password</label>
              <input id="rpw-new" v-model="pw.next" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pwErrors.new_password }" autocomplete="new-password" />
              <p v-if="pwErrors.new_password" class="field-error">{{ pwErrors.new_password }}</p>
              <ul class="pw-rules" aria-label="Password rules">
                <li v-for="r in pwRules" :key="r.label" :class="{ ok: r.ok }"><Check v-if="r.ok" :size="12" /><span v-else class="pw-dot" />{{ r.label }}</li>
              </ul>
            </div>
            <div class="field">
              <label class="field-label" for="rpw-confirm">Confirm new password</label>
              <input id="rpw-confirm" v-model="pw.confirm" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pw.confirm && pw.confirm !== pw.next }" autocomplete="new-password" />
              <p v-if="pw.confirm && pw.confirm !== pw.next" class="field-error">The passwords don't match.</p>
            </div>
            <label class="pw-show"><input v-model="showPw" type="checkbox" /> Show passwords</label>
            <p v-if="pwErrors.detail" class="profile-error">{{ pwErrors.detail }}</p>
            <div class="pw-actions">
              <button type="submit" class="save-btn" :disabled="savingPw || !canChangePw">{{ savingPw ? 'Changing…' : 'Change Password' }}</button>
              <NuxtLink to="/forgot-password" class="pw-forgot">Forgot your current password?</NuxtLink>
            </div>
            <p class="field-hint">We'll email you to confirm the change.</p>
          </form>
        </template>

        <!-- ============ HISTORY (GET /api/rnd/activity/, scheduling/rnd_activity.py) ============ -->
        <template v-else-if="activeTab === 'history'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Your Activity</h3>
              <p class="tab-panel-sub">Your consultations, NCP records, meal plans, patients, reviews and payouts.</p>
            </div>
            <button class="outline-btn print-btn" type="button" @click="printHistory"><Printer :size="14" /> Print</button>
          </div>

          <div class="filter-tabs">
            <button v-for="f in HISTORY_FILTERS" :key="f.key" class="filter-tab" :class="{ active: historyFilter === f.key }" type="button" @click="historyFilter = f.key">{{ f.label }}</button>
          </div>

          <p v-if="historyError" class="profile-error">{{ historyError }}</p>
          <p v-if="isLoadingHistory" class="placeholder-text">Loading…</p>
          <div v-else-if="!filteredHistory.length" class="empty-state">
            <ClipboardList :size="26" class="empty-icon" />
            <p>Nothing here yet.</p>
            <p class="empty-sub">Your consultations, records and meal plans show up here as you work with patients.</p>
          </div>
          <template v-else>
            <NuxtLink v-for="entry in filteredHistory" :key="entry.key" :to="entry.link" class="entry-row">
              <div class="entry-icon" :class="HISTORY_KINDS[entry.type]?.cls"><component :is="HISTORY_KINDS[entry.type]?.icon || ClipboardList" :size="16" /></div>
              <div class="entry-info">
                <p class="entry-title">{{ entry.title }}</p>
                <p v-if="entry.detail" class="entry-detail">{{ entry.detail }}</p>
              </div>
              <span class="entry-time">{{ formatTimestamp(entry.at) }}</span>
            </NuxtLink>
          </template>
        </template>

        <!-- ============ OTHER TABS (still placeholder) ============ -->
        <template v-else>
          <p class="placeholder-text">{{ activeTabLabel }} settings go here.</p>
        </template>
      </div>
    </div>

    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle2 :size="16" /> {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import {
  Briefcase, BadgeCheck,
  CalendarClock, X, Languages, Shield, History, Printer, ClipboardList,
  CalendarCheck, FileText, UtensilsCrossed, UserRound, Star, Wallet,
  Video, Users, Lock, FileImage, Pencil, Check, CheckCircle2
} from 'lucide-vue-next'
import { formatPhone, rndPhoneError } from '~/utils/phone'

const { get, patch, post, put } = useApi()

definePageMeta({ layout: 'dashboard', title: 'Profile Settings' })

const tabs = [
  { key: 'professional', label: 'Professional Profile', icon: Briefcase },
  { key: 'availability', label: 'Availability', icon: CalendarClock },
  { key: 'languages', label: 'Languages', icon: Languages },
  { key: 'security', label: 'Security', icon: Shield },
  { key: 'history', label: 'History', icon: History },
]

const route = useRoute()
const validTabKeys = tabs.map(t => t.key)

// Earnings moved to its own page (sidebar → Earnings).
if (route.query.tab === 'earnings') navigateTo('/earnings', { replace: true })
// Reviews live on their own page (sidebar → Reviews, real data).
if (route.query.tab === 'reviews') navigateTo('/reviews', { replace: true })
const activeTab = ref(validTabKeys.includes(route.query.tab) ? route.query.tab : 'professional')
const activeTabLabel = computed(() => tabs.find(t => t.key === activeTab.value)?.label)

/* ---------- PROFESSIONAL PROFILE ---------- */
const auth = useAuthStore()

const MODE_OPTIONS = [
  { value: 'video', label: 'Video', icon: Video },
  { value: 'in_person', label: 'In-Person', icon: Users },
]

const personalInfo = ref({
  firstName: '', lastName: '', email: '', phone: '', bio: '', consultationFee: '',
  consultationModes: [], clinicAddress: '', initials: '', avatarColor: '#D4A017',
  prcVerified: false, prcNumber: '', prcVerifiedOn: '', prcPhotoUrl: '',
  specialization: '', acceptingNewClients: true,
})
const isSavingProfile = ref(false)
const profileError = ref('')
const isEditing = ref(false)
const profileLoaded = ref(false)
// Last loaded profile — Cancel restores the form from it.
const lastLoaded = ref(null)
const fieldErrors = reactive({ firstName: '', lastName: '', phone: '', clinicAddress: '' })

const identityName = computed(() => `RND ${personalInfo.value.firstName} ${personalInfo.value.lastName}`.trim())
const identitySubtitle = computed(() => {
  const since = auth.user?.created_at
    ? new Date(auth.user.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
    : ''
  return [personalInfo.value.email, since && `Member since ${since}`].filter(Boolean).join(' · ')
})

function startEdit() {
  profileError.value = ''
  fieldErrors.firstName = fieldErrors.lastName = ''
  isEditing.value = true
}
function cancelEdit() {
  if (lastLoaded.value) applyProfile(lastLoaded.value.user, lastLoaded.value.rndProfile)
  profileError.value = ''
  fieldErrors.firstName = fieldErrors.lastName = ''
  isEditing.value = false
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

function applyProfile(user, rndProfile) {
  lastLoaded.value = { user, rndProfile }
  setLanguagesFrom(rndProfile)
  personalInfo.value.firstName = user.first_name || ''
  personalInfo.value.lastName = user.last_name || ''
  personalInfo.value.email = user.email || ''
  personalInfo.value.phone = user.phone || ''
  personalInfo.value.bio = rndProfile.bio || ''
  personalInfo.value.consultationFee = rndProfile.consultation_fee != null ? Number(rndProfile.consultation_fee) : ''
  personalInfo.value.consultationModes = [...(rndProfile.consultation_modes || [])]
  personalInfo.value.clinicAddress = rndProfile.clinic_address || ''
  personalInfo.value.specialization = rndProfile.specialization || ''
  personalInfo.value.acceptingNewClients = rndProfile.available_for_new_clients !== false
  // PRC — read-only. The photo link is signed and short-lived (it's a
  // private upload), so it's refreshed every time the profile loads.
  personalInfo.value.prcVerified = Boolean(rndProfile.is_verified)
  personalInfo.value.prcNumber = rndProfile.prc_license_number || ''
  personalInfo.value.prcVerifiedOn = rndProfile.verified_at
    ? new Date(rndProfile.verified_at).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
    : ''
  personalInfo.value.prcPhotoUrl = rndProfile.prc_license_image_url || ''
  personalInfo.value.initials = `${personalInfo.value.firstName[0] ?? ''}${personalInfo.value.lastName[0] ?? ''}`.toUpperCase()
}

async function loadProfessionalProfile() {
  try {
    const rndProfile = await get('/rnd/profile/')
    applyProfile(rndProfile.user, rndProfile)
    profileLoaded.value = true
  } catch {
    profileError.value = 'Could not load your profile. Please try again later.'
  }
}
onMounted(loadProfessionalProfile)

// Real RndLanguage rows (profiles/models.py LANGUAGES). Adding/removing
// saves straight away (PATCH /rnd/profile/ {languages: [codes]}); at least
// one language must stay.
const LANGUAGE_OPTIONS = [
  { code: 'en', name: 'English' },
  { code: 'tl', name: 'Filipino (Tagalog)' },
  { code: 'ceb', name: 'Bisaya (Cebuano)' },
  { code: 'ilo', name: 'Ilocano' },
  { code: 'hil', name: 'Hiligaynon (Ilonggo)' },
  { code: 'war', name: 'Waray' },
  { code: 'pam', name: 'Kapampangan' },
  { code: 'bcl', name: 'Bicolano' },
]
const languages = ref([])
const newLanguage = ref('')
const languageError = ref('')
const availableLanguageOptions = computed(() => LANGUAGE_OPTIONS.filter(o => !languages.value.some(l => l.code === o.code)))
function setLanguagesFrom(rndProfile) {
  languages.value = (rndProfile.languages || []).map(l => ({ id: l.language_code, code: l.language_code, name: l.language_name }))
}
async function saveLanguages(codes) {
  languageError.value = ''
  try {
    const profile = await patch('/rnd/profile/', { languages: codes })
    setLanguagesFrom(profile)
  } catch (error) {
    languageError.value = error?.data?.languages?.[0] || error?.data?.detail || 'Could not save your languages. Please try again.'
  }
}
function addLanguage() {
  if (!newLanguage.value) return
  saveLanguages([...languages.value.map(l => l.code), newLanguage.value])
  newLanguage.value = ''
}
function removeLanguage(lang) {
  if (languages.value.length === 1) {
    languageError.value = 'Keep at least one language — clients filter RNDs by language.'
    return
  }
  saveLanguages(languages.value.filter(l => l.code !== lang.code).map(l => l.code))
}

const NAME_RE = /^[A-Za-zÀ-ÖØ-öø-ÿÑñ]+(?:[ '.-][A-Za-zÀ-ÖØ-öø-ÿÑñ]+)*\.?$/

async function saveChanges() {
  profileError.value = ''
  fieldErrors.firstName = fieldErrors.lastName = fieldErrors.phone = fieldErrors.clinicAddress = ''
  personalInfo.value.firstName = personalInfo.value.firstName.trim()
  personalInfo.value.lastName = personalInfo.value.lastName.trim()
  if (!personalInfo.value.firstName) fieldErrors.firstName = 'Enter your first name.'
  else if (!NAME_RE.test(personalInfo.value.firstName)) fieldErrors.firstName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  if (!personalInfo.value.lastName) fieldErrors.lastName = 'Enter your last name.'
  else if (!NAME_RE.test(personalInfo.value.lastName)) fieldErrors.lastName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  fieldErrors.phone = rndPhoneError(personalInfo.value.phone)
  if (fieldErrors.firstName || fieldErrors.lastName || fieldErrors.phone) return
  if (!personalInfo.value.consultationModes.length) {
    profileError.value = 'Offer at least one consultation format.'
    return
  }
  const address = (personalInfo.value.clinicAddress || '').trim()
  if (personalInfo.value.consultationModes.includes('in_person')) {
    if (!address) fieldErrors.clinicAddress = 'Add your clinic address — clients need to know where to go.'
    else if (address.length < 10) fieldErrors.clinicAddress = 'Enter the full address — building, street, barangay and city.'
    if (fieldErrors.clinicAddress) return
  }
  const fee = personalInfo.value.consultationFee
  if (fee === '' || fee === null || Number(fee) < 100) {
    profileError.value = 'The consultation fee must be at least ₱100.'
    return
  }
  isSavingProfile.value = true
  try {
    const [user, rndProfile] = await Promise.all([
      patch('/auth/me/', {
        first_name: personalInfo.value.firstName,
        last_name: personalInfo.value.lastName,
        phone: personalInfo.value.phone || null,
      }),
      patch('/rnd/profile/', {
        bio: personalInfo.value.bio,
        consultation_fee: Number(fee).toFixed(2),
        consultation_modes: personalInfo.value.consultationModes,
        clinic_address: personalInfo.value.consultationModes.includes('in_person') ? address : (address || null),
      }),
    ])
    applyProfile(user, rndProfile)
    await auth.fetchMe()
    isEditing.value = false
    fireToast()
  } catch (error) {
    const data = error?.data || {}
    const first = (v) => (Array.isArray(v) ? v[0] : v) || ''
    fieldErrors.firstName = first(data.first_name)
    fieldErrors.lastName = first(data.last_name)
    fieldErrors.phone = first(data.phone)
    fieldErrors.clinicAddress = first(data.clinic_address)
    profileError.value = fieldErrors.firstName || fieldErrors.lastName || fieldErrors.phone || fieldErrors.clinicAddress
      ? ''
      : data.detail || Object.values(data).flat()[0] || 'Could not save your changes. Please try again.'
  } finally {
    isSavingProfile.value = false
  }
}

/* ---------- HISTORY ---------- */
const HISTORY_KINDS = {
  consultation: { icon: CalendarCheck, cls: 'icon-gold' },
  ncp: { icon: FileText, cls: 'icon-blue' },
  meal_plan: { icon: UtensilsCrossed, cls: 'icon-green' },
  patient: { icon: UserRound, cls: 'icon-blue' },
  review: { icon: Star, cls: 'icon-gold' },
  payout: { icon: Wallet, cls: 'icon-green' },
}
const HISTORY_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'consultation', label: 'Consultations' },
  { key: 'ncp', label: 'NCP Records' },
  { key: 'meal_plan', label: 'Meal Plans' },
  { key: 'patient', label: 'Patients' },
  { key: 'review', label: 'Reviews' },
  { key: 'payout', label: 'Payouts' },
]
const historyEntries = ref([])
const historyFilter = ref('all')
const isLoadingHistory = ref(false)
const historyError = ref('')
let historyLoaded = false
const filteredHistory = computed(() =>
  historyFilter.value === 'all' ? historyEntries.value : historyEntries.value.filter(e => e.type === historyFilter.value))
async function loadHistory() {
  isLoadingHistory.value = true
  historyError.value = ''
  try {
    historyEntries.value = await get('/rnd/activity/')
    historyLoaded = true
  } catch {
    historyError.value = 'Could not load your activity. Please try again.'
  } finally {
    isLoadingHistory.value = false
  }
}
watch(activeTab, (tab) => { if (tab === 'history' && !historyLoaded) loadHistory() }, { immediate: true })
function formatTimestamp(iso) {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}
function printHistory() {
  window.print()
}

/* ---------- TAKING NEW CLIENTS (saves straight away) ---------- */
// Off = hidden from new clients on Find an RND and new bookings are refused;
// current patients can still book.
const savingNewClients = ref(false)
async function toggleNewClients(value) {
  const before = personalInfo.value.acceptingNewClients
  personalInfo.value.acceptingNewClients = value
  savingNewClients.value = true
  try {
    await patch('/rnd/profile/', { available_for_new_clients: value })
    fireToast(value ? 'You\'re taking new clients again.' : 'New clients can no longer book you.')
  } catch {
    personalInfo.value.acceptingNewClients = before
    fireToast('Could not save. Please try again.')
  } finally {
    savingNewClients.value = false
  }
}

/* ---------- SECURITY: change password (rules mirror PasswordComplexityValidator) ---------- */
const pw = reactive({ current: '', next: '', confirm: '' })
const pwErrors = ref({})
const savingPw = ref(false)
const showPw = ref(false)
const pwRules = computed(() => [
  { label: 'At least 8 characters', ok: pw.next.length >= 8 },
  { label: 'An uppercase letter', ok: /[A-Z]/.test(pw.next) },
  { label: 'A lowercase letter', ok: /[a-z]/.test(pw.next) },
  { label: 'A number', ok: /\d/.test(pw.next) },
  { label: 'A special character', ok: /[^A-Za-z0-9]/.test(pw.next) },
])
const canChangePw = computed(() => pw.current && pwRules.value.every(r => r.ok) && pw.next === pw.confirm)
async function changePassword() {
  pwErrors.value = {}
  if (!canChangePw.value) return
  savingPw.value = true
  try {
    await post('/auth/me/password/', { current_password: pw.current, new_password: pw.next })
    Object.assign(pw, { current: '', next: '', confirm: '' })
    showPw.value = false
    fireToast('Password changed — we emailed you a confirmation.')
  } catch (e) {
    const d = e?.data || {}
    const out = Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]))
    pwErrors.value = Object.keys(out).length ? out : { detail: 'Could not change your password. Please try again.' }
  } finally {
    savingPw.value = false
  }
}

/* ---------- phones: keep the selected tab in view in the sideways strip ---------- */
const tabCard = ref(null)
function showActiveTab() {
  nextTick(() => {
    const strip = tabCard.value
    const btn = strip?.querySelector('.tab-item.active')
    if (!strip || !btn || strip.scrollWidth <= strip.clientWidth) return
    strip.scrollLeft = Math.min(Math.max(0, btn.offsetLeft - (strip.clientWidth - btn.offsetWidth) / 2), strip.scrollWidth - strip.clientWidth)
  })
}
watch(activeTab, showActiveTab)
onMounted(showActiveTab)

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

/* Buttons + read-only view — same as ClientProfileSettings.vue. */
.btn-dark {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  background: #163a1c; color: #fff; border: none;
  padding: 9px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
  white-space: nowrap; font-family: inherit;
}
.btn-dark:hover:not(:disabled) { background: #0f2a14; }
.btn-dark:disabled { opacity: 0.5; cursor: not-allowed; }
.outline-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex-shrink: 0;
  border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px;
  padding: 9px 16px; font-weight: 600; font-size: 0.82rem; cursor: pointer; white-space: nowrap; font-family: inherit;
}
.outline-btn:hover:not(:disabled) { background: #f7f9f7; }
.outline-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 24px; margin: 0 0 24px; }
.info-stack { margin: 0 0 8px; }
.info-item { padding: 14px 0; border-top: 1px solid #f0f2f0; min-width: 0; }
.info-grid .info-item:nth-child(-n + 2), .info-stack .info-item:first-child { border-top: none; padding-top: 0; }
.info-item dt { font-size: 0.76rem; font-weight: 600; color: #8a9a8a; margin: 0 0 4px; }
.info-item dd { font-size: 0.92rem; font-weight: 500; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.info-item dd.muted, .info-item .muted { color: #aab5aa; font-weight: 400; }
.bio-text { white-space: pre-line; line-height: 1.55; font-weight: 400 !important; }
.mode-chip {
  display: inline-flex; align-items: center; gap: 6px; margin: 2px 8px 2px 0;
  background: #f0f9f4; border: 1px solid #cfe8da; color: #1a3a1a; border-radius: 999px;
  padding: 5px 12px; font-size: 0.8rem; font-weight: 600;
}
.field-error { font-size: 0.76rem; color: #c0392b; margin: 4px 0 0; }
.field-input.invalid { border-color: #c0392b; }
.prc-section .info-grid { margin-bottom: 12px; }

.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

/* FORM */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 24px; margin-bottom: 24px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; margin: 0 0 8px; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 12px 14px;
  font-size: 0.88rem; color: #2a2a2a; font-family: inherit;
}
.field-input:focus { outline: none; border-color: #D4A017; }

.field-bio { margin-bottom: 24px; }
.bio-label-row { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 8px; }
.bio-label-row .field-label { margin: 0; }
.bio-count { font-size: 0.74rem; color: #9aaa9a; }
.bio-count-warn { color: #c0483a; font-weight: 600; }
.bio-textarea { resize: vertical; min-height: 90px; line-height: 1.55; font-family: inherit; }
.field-hint { font-size: 0.76rem; color: #9aaa9a; margin: 6px 0 0; }
.field-input:disabled { background: #f4f5f3; color: #8a9a8a; }

.prc-section { border: 1px solid #e5e8e5; border-radius: 12px; padding: 18px 20px; margin-bottom: 24px; background: #fafbfa; }
.prc-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.prc-title { display: inline-flex; align-items: center; gap: 6px; margin: 0; }
.prc-status { font-size: 0.74rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.prc-verified { background: #e3f3ea; color: #1f8f5c; }
.prc-pending { background: #fdf1d6; color: #b8860b; }
.prc-section .form-grid { margin-bottom: 12px; }
.prc-photo-link {
  display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; font-weight: 600;
  color: #1f8f5c; text-decoration: none; border: 1px solid #1f8f5c; border-radius: 8px; padding: 7px 12px;
}
.prc-photo-link:hover { background: #e3f3ea; }
.fee-input-wrap { display: flex; align-items: center; gap: 8px; max-width: 320px; margin-top: 8px; }
.fee-prefix { font-weight: 700; color: #1a3a1a; }
.fee-input { flex: 1; min-width: 0; }
.fee-suffix { font-size: 0.8rem; color: #9aaa9a; white-space: nowrap; }
.mode-options { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
.mode-option {
  display: inline-flex; align-items: center; gap: 7px; border: 1.5px solid #d5dad5; border-radius: 10px;
  padding: 9px 14px; font-size: 0.84rem; font-weight: 600; color: #4a5a4a; cursor: pointer; background: #fff;
}
.mode-option input { accent-color: #1f8f5c; margin: 0; }
.mode-option.checked { border-color: #1f8f5c; background: #f0f9f4; color: #1a3a1a; }
.profile-error { font-size: 0.82rem; color: #a12525; margin: 0 0 12px; }
.profile-saved { font-size: 0.82rem; color: #1f8f5c; font-weight: 600; margin: 0 0 12px; }

.save-btn {
  display: flex; align-items: center; gap: 6px;
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 12px 22px; font-weight: 700; font-size: 0.88rem; cursor: pointer; white-space: nowrap;
}
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* LANGUAGES (nested inside Professional Profile) */
.language-list { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.language-pill { display: flex; align-items: center; gap: 6px; background: #e6f4e6; color: #1a5a2a; font-size: 0.8rem; font-weight: 600; padding: 6px 10px 6px 14px; border-radius: 20px; }
.language-add-row { display: flex; gap: 10px; align-items: center; }
.language-select { max-width: 260px; cursor: pointer; }

.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }
.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}

/* SHARED TAB PANEL HEADER */
.tab-panel-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; gap: 16px; }
.tab-panel-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0 0 4px; }
.tab-panel-sub { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
.empty-note { font-size: 0.85rem; color: #9aaa9a; text-align: center; padding: 30px 0; }

.mini-stat-icon {
  width: 30px; height: 30px; border-radius: 8px; background: #eef1ee;
  display: flex; align-items: center; justify-content: center; color: #4a5a4a; margin-bottom: 10px;
}




/* AVAILABILITY TAB */
.day-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px; }
.day-row { background: #fafbfa; border-radius: 10px; border: 1px solid #f0f2f0; padding: 14px 18px; display: flex; align-items: center; gap: 16px; }
.day-row-blocked { background: #fafafa; }
.day-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; width: 100px; flex-shrink: 0; }
.day-name-blocked { color: #9aaa9a; font-weight: 600; }
.day-content { flex: 1; display: flex; flex-wrap: wrap; gap: 8px; }
.slot-pill { display: flex; align-items: center; gap: 6px; background: #e6f4e6; color: #1a5a2a; font-size: 0.8rem; font-weight: 600; padding: 6px 10px 6px 14px; border-radius: 20px; }
.pill-icon-btn { background: none; border: none; color: #4a8a5a; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 2px; }
.pill-icon-btn:hover { color: #1a5a2a; }
.blocked-pill { background: #fbe1de; color: #c0483a; font-size: 0.78rem; font-weight: 700; padding: 6px 14px; border-radius: 20px; }
.day-action-link { background: none; border: none; color: #1a6a2a; font-size: 0.8rem; font-weight: 600; cursor: pointer; white-space: nowrap; flex-shrink: 0; }
.day-row-blocked .day-action-link { color: #9aaa9a; }
.day-action-link:hover { text-decoration: underline; }

.block-panel { background: #eef3ee; border-radius: 10px; padding: 20px; border-top: none; margin-top: 20px; }
.block-header { display: flex; gap: 12px; margin-bottom: 18px; }
.block-icon { color: #1a3a1a; flex-shrink: 0; margin-top: 2px; }
.block-desc { font-size: 0.8rem; color: #6a7a6a; line-height: 1.5; margin: 0; max-width: 640px; }
.block-form { display: grid; grid-template-columns: 1fr 1fr 1.4fr auto; gap: 12px; align-items: end; margin-bottom: 14px; }
.field-wide { grid-column: auto; }
.block-btn { padding: 12px 20px; }
.blocked-list { display: flex; flex-direction: column; gap: 8px; }
.blocked-item { display: flex; align-items: center; gap: 12px; background: #fff; border-radius: 8px; padding: 10px 14px; font-size: 0.8rem; }
.blocked-dates { font-weight: 700; color: #1a3a1a; }
.blocked-reason { color: #7a8a7a; flex: 1; }
.remove-block-btn { background: none; border: none; color: #9aaa9a; cursor: pointer; display: flex; }
.remove-block-btn:hover { color: #c0483a; }

@media (max-width: 1100px) {
  .block-form { grid-template-columns: 1fr; }
}

/* MOBILE — same as the client settings page (ClientProfileSettings.vue):
   tabs become a sideways-scrolling strip above the panel. */
@media (max-width: 900px) {
  .profile-layout { grid-template-columns: 1fr; }
  .tab-card { position: relative; flex-direction: row; overflow-x: auto; scrollbar-width: none; }
  .tab-card::-webkit-scrollbar { display: none; }
  .tab-item { flex-shrink: 0; padding: 10px 12px; white-space: nowrap; }
  .panel-card { min-width: 0; }
}
@media (max-width: 640px) {
  .page-header { flex-direction: column; gap: 10px; }
  .page-title { font-size: 1.4rem; }
  .panel-card { padding: 20px 16px; }
  .form-grid, .info-grid { grid-template-columns: 1fr; }
  .info-grid .info-item:nth-child(2) { border-top: 1px solid #f0f2f0; padding-top: 14px; }
  .tab-panel-header { flex-direction: column; }
  .language-add-row { flex-wrap: wrap; }
}

/* Taking new clients */
.newclients-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; margin: 16px 0 20px; padding: 14px 16px; border: 1px solid #e5e8e5; border-radius: 12px; background: #fff; }
.newclients-row .field-hint { margin: 2px 0 0; }
.newclients-label { margin: 0; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.toggle { position: relative; flex-shrink: 0; width: 42px; height: 24px; cursor: pointer; }
.toggle input { position: absolute; opacity: 0; width: 100%; height: 100%; margin: 0; cursor: pointer; }
.toggle-track { position: absolute; inset: 0; border-radius: 999px; background: #d5dad5; transition: background 0.2s; }
.toggle-thumb { position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2); transition: transform 0.2s; }
.toggle input:checked + .toggle-track { background: #1f8f5c; }
.toggle input:checked + .toggle-track .toggle-thumb { transform: translateX(18px); }
.toggle input:focus-visible + .toggle-track { box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.25); }
.toggle input:disabled + .toggle-track { opacity: 0.6; }

/* Security — change password */
.pw-form { display: flex; flex-direction: column; gap: 14px; max-width: 440px; }
.pw-title { margin: 0; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.pw-rules { list-style: none; padding: 0; margin: 4px 0 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px 12px; }
.pw-rules li { display: flex; align-items: center; gap: 6px; font-size: 0.74rem; color: #8a9a8a; }
.pw-rules li.ok { color: #1f8f5c; }
.pw-dot { width: 6px; height: 6px; border-radius: 50%; border: 1px solid #b0bab0; margin: 0 3px; }
.pw-show { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #4a5a4a; cursor: pointer; }
.pw-actions { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.pw-forgot { font-size: 0.82rem; color: #1a3a1a; font-weight: 600; text-decoration: underline; }
@media (max-width: 480px) { .pw-rules { grid-template-columns: 1fr; } }

/* History — mirrors ClientProfileSettings.vue */
.filter-tabs { display: inline-flex; gap: 4px; background: #f4f5f3; border-radius: 999px; padding: 3px; margin-bottom: 14px; flex-wrap: wrap; }
.filter-tab { border: none; background: none; padding: 6px 12px; border-radius: 999px; font-size: 0.76rem; font-weight: 600; color: #6a7a6a; cursor: pointer; font-family: inherit; }
.filter-tab.active { background: #14301a; color: #fff; }
.entry-row { display: flex; align-items: center; gap: 14px; padding: 13px 0; border-top: 1px solid #f0f2f0; text-decoration: none; color: inherit; }
.entry-row:hover .entry-title { text-decoration: underline; }
.entry-icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.icon-blue { background: #e3ecf7; color: #2a5a8a; }
.icon-gold { background: #fdf1d6; color: #b8860b; }
.icon-green { background: #e3f3ea; color: #1f8f5c; }
.entry-info { flex: 1; min-width: 0; }
.entry-title { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.entry-detail { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; overflow-wrap: anywhere; }
.entry-time { font-size: 0.74rem; color: #9aaa9a; white-space: nowrap; }
.empty-state { padding: 30px; text-align: center; color: #9aaa9a; font-size: 0.85rem; }
.empty-state p { margin: 0; }
.empty-icon { color: #d5dad5; margin-bottom: 8px; }
.empty-sub { font-size: 0.78rem; margin-top: 4px !important; }
.print-btn { display: inline-flex; align-items: center; gap: 6px; }
@media (max-width: 640px) {
  .entry-row { flex-wrap: wrap; }
  .entry-time { width: 100%; padding-left: 48px; }
}
@media print {
  .page-header, .tab-card, .print-btn, .filter-tabs { display: none !important; }
  .profile-layout { grid-template-columns: 1fr; }
}
</style>
