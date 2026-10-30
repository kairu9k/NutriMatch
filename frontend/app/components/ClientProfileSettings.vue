<template>
  <!-- Same layout as the RND Profile Settings (RNDProfileSettings.vue): page
       header, tab list on the left, one panel on the right. -->
  <div class="profile-page">
    <div class="page-header">
      <div>
        <p class="page-sub">Manage your personal details, health profile, and account preferences.</p>
      </div>
      <span class="role-pill"><User :size="14" /> Patient</span>
    </div>

    <p v-if="loadError" class="form-error">{{ loadError }}</p>

    <div class="profile-layout">
      <!-- TABS -->
      <div ref="tabCard" class="tab-card">
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
        <!-- Read-only until "Edit profile"; Cancel / Save changes sit at the bottom while editing. -->
        <template v-if="activeTab === 'personal'">
          <ProfileIdentityHeader :name="displayName" :subtitle="identitySubtitle" :editable="isEditing" @photo-changed="fireToast">
            <template #actions>
              <button v-if="!isEditing" class="nm-btn-dark" type="button" :disabled="!profileLoaded" @click="startEdit">
                <Pencil :size="15" aria-hidden="true" /> Edit profile
              </button>
            </template>
          </ProfileIdentityHeader>

          <!-- READ-ONLY VIEW -->
          <dl v-if="!isEditing" class="info-grid">
            <div class="info-item"><dt>First name</dt><dd>{{ form.firstName || '—' }}</dd></div>
            <div class="info-item"><dt>Last name</dt><dd>{{ form.lastName || '—' }}</dd></div>
            <div class="info-item"><dt>Email address</dt><dd>{{ auth.user?.email || '—' }}</dd></div>
            <div class="info-item"><dt>Mobile number</dt><dd :class="{ muted: !form.phone }">{{ formatPhone(form.phone) || 'Not provided' }}</dd></div>
            <div class="info-item"><dt>Date of birth</dt><dd :class="{ muted: !form.dateOfBirth }">{{ dobLabel || 'Not provided' }}</dd></div>
            <div class="info-item"><dt>Sex</dt><dd :class="{ muted: !form.sex }">{{ sexLabel || 'Not provided' }}</dd></div>
            <div class="info-item"><dt>Preferred language</dt><dd :class="{ muted: !form.languageCode }">{{ languageLabel || 'Not provided' }}</dd></div>
            <div class="info-item"><dt>Primary health condition</dt><dd :class="{ muted: !conditionLabel }">{{ conditionLabel || 'None / not sure' }}</dd></div>
            <div class="info-item"><dt>Food allergies</dt><dd :class="{ muted: !background.allergiesList.length }">{{ background.allergiesAnswered ? (background.allergiesList.join(', ') || 'None') : 'Not answered yet' }}</dd></div>
            <div class="info-item"><dt>Dietary restrictions</dt><dd :class="{ muted: !background.dietList.length }">{{ background.dietList.join(', ') || 'None' }}</dd></div>
            <div class="info-item"><dt>Religion</dt><dd :class="{ muted: !background.religion }">{{ background.religion || 'Not provided' }}</dd></div>
          </dl>

          <!-- EDIT FORM -->
          <template v-else>
            <div class="form-grid">
              <div class="field">
                <label class="field-label" for="pi-first">First name</label>
                <input id="pi-first" v-model="form.firstName" type="text" class="field-input" :class="{ invalid: fieldErrors.firstName }" maxlength="150" />
                <p v-if="fieldErrors.firstName" class="field-error">{{ fieldErrors.firstName }}</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-last">Last name</label>
                <input id="pi-last" v-model="form.lastName" type="text" class="field-input" :class="{ invalid: fieldErrors.lastName }" maxlength="150" />
                <p v-if="fieldErrors.lastName" class="field-error">{{ fieldErrors.lastName }}</p>
              </div>
              <div class="field">
                <label class="field-label">Email address</label>
                <input :value="auth.user?.email" type="email" class="field-input" disabled />
                <p class="field-hint">Email can't be changed here.</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-phone">Mobile number</label>
                <PhoneInput id="pi-phone" v-model="form.phone" label="mobile number" :error="fieldErrors.phone" />
              </div>
              <div class="field">
                <label class="field-label" for="pi-dob">Date of birth</label>
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
                <label class="field-label" for="pi-lang">Preferred language</label>
                <select id="pi-lang" v-model="form.languageCode" class="nm-select block">
                  <option value="">Select</option>
                  <option v-for="l in languageOptions" :key="l.code" :value="l.code">{{ l.label }}</option>
                </select>
              </div>
              <div class="field">
                <label class="field-label" for="pi-condition">Primary health condition</label>
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
                <label class="field-label" for="pi-allergies">Food allergies</label>
                <input id="pi-allergies" v-model="background.allergiesText" type="text" maxlength="300" class="field-input" placeholder="e.g. Shrimp, peanuts. Leave empty if none" />
                <p class="field-hint">Separate with commas. Your RND plans your meals around these.</p>
              </div>
              <div class="field">
                <label class="field-label" for="pi-diet">Dietary restrictions</label>
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
          <div v-if="isEditing" class="edit-foot">
            <button class="nm-btn-soft" type="button" :disabled="isSaving" @click="cancelEdit">Cancel</button>
            <button class="nm-btn-dark" type="button" :disabled="isSaving" @click="saveProfile">
              <Check :size="15" aria-hidden="true" /> {{ isSaving ? 'Saving…' : 'Save changes' }}
            </button>
          </div>
        </template>

        <!-- ============ HEALTH PROFILE ============ -->
        <template v-else-if="activeTab === 'health'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Health profile</h3>
              <p class="tab-panel-sub">Your screening on file. Your progress is measured from it.</p>
            </div>
            <button class="nm-btn-soft" type="button" @click="screeningOpen = true">View screening</button>
          </div>

          <dl v-if="screening" class="figs">
            <div class="fig">
              <dt>BMI, {{ screening.bmi_category }}</dt>
              <dd>{{ screening.bmi }}</dd>
            </div>
            <div class="fig">
              <dt>Energy needs a day (TDEE)</dt>
              <dd>{{ screening.tdee_kcal ? Math.round(screening.tdee_kcal).toLocaleString() : '—' }} <span class="fig-unit">kcal</span></dd>
            </div>
            <div class="fig" :class="{ risk: (screening.nrs_score ?? 0) >= 3 }">
              <dt>NRS-2002, {{ nrsLabel(screening.nrs_risk) }}</dt>
              <dd>{{ screening.nrs_score ?? '—' }}</dd>
            </div>
          </dl>
          <p v-else class="empty-note">No screening on file yet.</p>

          <p class="field-hint health-note">
            Your primary health condition is under
            <button class="nm-btn-soft nm-btn-sm" type="button" @click="activeTab = 'personal'">Personal info</button>.
          </p>
        </template>

        <!-- ============ CARE TEAM ============ -->
        <template v-else-if="activeTab === 'care'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Care team</h3>
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
            <button class="nm-btn-soft" type="button" @click="navigateTo('/messages')">Send a message</button>
          </div>

          <!-- Ending care (2026-10-19): one RND at a time, so the client can ask
               to end it; the RND has 3 days to discharge them, then it ends on
               its own (scheduling/discharge_requests.py). -->
          <template v-if="careRnd && careRel">
            <div v-if="careRel.discharge_request" class="dr-pending" role="status">
              <p class="dr-title">You asked to end your care</p>
              <p class="dr-text">
                Asked on {{ drDate(careRel.discharge_request.requested_at) }}: {{ careRel.discharge_request.reason_label }}.
                RND {{ careRnd.user.first_name }} can close your care with a final note until
                <strong>{{ drDate(careRel.discharge_request.ends_at) }}</strong>. After that it ends automatically and you can book any RND.
                Your records stay in your account.
              </p>
              <p v-if="drError" class="field-error">{{ drError }}</p>
              <button class="nm-btn-soft" type="button" :disabled="drBusy" @click="withdrawDischarge">{{ drBusy ? 'Saving…' : 'Keep my RND' }}</button>
            </div>
            <div v-else class="setting-row">
              <div>
                <p class="setting-label">End care with this RND</p>
                <p class="setting-detail">Want to switch RNDs or finished your care? Ask to end it. Your RND gets {{ DR_DAYS }} days to close it, then it ends automatically.</p>
              </div>
              <button class="nm-btn-soft" type="button" @click="openDischarge">Request discharge</button>
            </div>
          </template>
          <div v-else class="setting-row">
            <div>
              <p class="setting-label">No RND yet</p>
              <p class="setting-detail">You're not connected with an RND yet.</p>
            </div>
            <button class="nm-btn-soft" type="button" @click="navigateTo('/find-rnd')">Find an RND</button>
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
          <!-- Change password right here (POST /api/auth/me/password/): current
               password + a new one with the sign-up rules; a confirmation
               email goes out. Sign out lives in the account menu. -->
          <form class="pw-form" novalidate @submit.prevent="changePassword">
            <p class="setting-label">Change password</p>
            <div class="field">
              <label class="field-label" for="pw-current">Current password</label>
              <input id="pw-current" v-model="pw.current" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pwErrors.current_password }" autocomplete="current-password" />
              <p v-if="pwErrors.current_password" class="field-error">{{ pwErrors.current_password }}</p>
            </div>
            <div class="field">
              <label class="field-label" for="pw-new">New password</label>
              <input id="pw-new" v-model="pw.next" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pwErrors.new_password }" autocomplete="new-password" />
              <p v-if="pwErrors.new_password" class="field-error">{{ pwErrors.new_password }}</p>
              <ul class="pw-rules" aria-label="Password rules">
                <li v-for="r in pwRules" :key="r.label" :class="{ ok: r.ok }"><Check v-if="r.ok" :size="12" /><span v-else class="pw-dot" />{{ r.label }}</li>
              </ul>
            </div>
            <div class="field">
              <label class="field-label" for="pw-confirm">Confirm new password</label>
              <input id="pw-confirm" v-model="pw.confirm" :type="showPw ? 'text' : 'password'" class="field-input" :class="{ invalid: pw.confirm && pw.confirm !== pw.next }" autocomplete="new-password" />
              <p v-if="pw.confirm && pw.confirm !== pw.next" class="field-error">The passwords don't match.</p>
            </div>
            <label class="pw-show"><input v-model="showPw" type="checkbox" /> Show passwords</label>
            <p v-if="pwErrors.detail" class="profile-error">{{ pwErrors.detail }}</p>
            <div class="pw-actions">
              <button type="submit" class="nm-btn-dark" :disabled="savingPw || !canChangePw">{{ savingPw ? 'Changing…' : 'Change password' }}</button>
              <NuxtLink to="/forgot-password" class="pw-forgot">Forgot your current password?</NuxtLink>
            </div>
            <p class="setting-detail">We'll email you to confirm the change.</p>
          </form>
        </template>

        <!-- ============ NOTIFICATIONS ============ -->
        <template v-else-if="activeTab === 'notifications'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Notifications and reminders</h3>
              <p class="tab-panel-sub">NutriMatch reminds you automatically. You always get them in the app. Choose which ones, and whether to get emails too.</p>
            </div>
          </div>

          <p v-if="reminderError" class="form-error">{{ reminderError }}</p>
          <p v-if="!reminderPrefs" class="placeholder-text">Loading…</p>
          <template v-else>
            <NotificationSoundToggle />
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
                <p class="setting-detail">To {{ auth.user?.email }}. Off by default. In-app notifications are always on.</p>
              </div>
              <label class="toggle">
                <input :checked="reminderPrefs.email" type="checkbox" @change="savePref('email', $event.target.checked)" />
                <span class="toggle-track"><span class="toggle-thumb"></span></span>
              </label>
            </div>
            <div class="setting-row">
              <div>
                <p class="setting-label">Also send reminders by text (SMS)</p>
                <p v-if="reminderPrefs.sms_number" class="setting-detail">To {{ reminderPrefs.sms_number }}. Only the important ones: booking confirmed, payment due, your consultation starting in 1 hour, and a cancelled consultation. Short texts with no health details.</p>
                <p v-else-if="auth.user?.phone" class="setting-detail">SMS reminders are only available for Philippine mobile numbers (+63). Yours is {{ formatPhone(auth.user.phone) }}.</p>
                <p v-else class="setting-detail">Add your mobile number (e.g. 0917 123 4567) in Personal Info first.</p>
              </div>
              <label class="toggle">
                <input :checked="reminderPrefs.sms" :disabled="!reminderPrefs.sms_number && !reminderPrefs.sms" type="checkbox" @change="savePref('sms', $event.target.checked)" />
                <span class="toggle-track"><span class="toggle-thumb"></span></span>
              </label>
            </div>

          </template>
        </template>

        <!-- ============ PRIVACY & DATA ============ -->
        <template v-else-if="activeTab === 'privacy'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Privacy and data</h3>
              <p class="tab-panel-sub">How your information is handled.</p>
            </div>
          </div>
          <div class="setting-row">
            <div>
              <p class="setting-label">Data sharing</p>
              <p class="setting-detail">Your health data is only shared with your assigned RND under RA 10173 (Data Privacy Act of 2012).</p>
            </div>
            <!-- TODO: no data-export endpoint exists yet. -->
            <button class="nm-btn-soft" type="button" disabled title="Coming soon">Download my data</button>
          </div>
        </template>

        <!-- ============ HISTORY ============ -->
        <template v-else-if="activeTab === 'history'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Your activity</h3>
              <p class="tab-panel-sub">Every screening, appointment, and meal log on your account.</p>
            </div>
            <button class="nm-btn-soft print-btn" type="button" @click="printHistory"><Printer :size="14" /> Print</button>
          </div>

          <div class="filter-tabs">
            <button v-for="f in historyFilters" :key="f.key" class="filter-tab" :class="{ active: historyFilter === f.key }" type="button" @click="historyFilter = f.key">{{ f.label }}</button>
          </div>

          <p v-if="isLoadingHistory" class="placeholder-text">Loading…</p>
          <div v-else-if="!filteredHistory.length" class="empty-state">
            <ClipboardList :size="26" class="empty-icon" />
            <p>Nothing saved yet.</p>
            <p class="empty-sub">Complete a screening, book an appointment or log a meal, and it shows up here.</p>
          </div>
          <div v-for="entry in pagedHistory" v-else :key="entry.key" class="entry-row">
            <div class="entry-icon" :class="entry.iconClass"><component :is="entry.icon" :size="16" /></div>
            <div class="entry-info">
              <p class="entry-title">{{ entry.title }}</p>
              <p class="entry-detail">{{ entry.detail }}</p>
            </div>
            <span class="entry-time">{{ formatTimestamp(entry.at) }}</span>
          </div>
          <div v-if="!isLoadingHistory && historyPages > 1" class="pager">
            <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="historyPage === 1" @click="historyPage--">Previous</button>
            <span class="pager-num">Page {{ historyPage }} of {{ historyPages }}</span>
            <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="historyPage === historyPages" @click="historyPage++">Next</button>
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

    <div v-if="drOpen" class="nm-modal-overlay" @click.self="drOpen = false" @keydown.esc="drOpen = false">
      <div class="nm-modal dr-modal" role="dialog" aria-modal="true" aria-labelledby="dr-heading">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="drOpen = false"><X :size="18" aria-hidden="true" /></button>
        <h3 id="dr-heading" class="nm-modal-title">Request discharge</h3>
        <p class="dr-text">
          You're asking to end your care with <strong>RND {{ careRnd?.user.first_name }} {{ careRnd?.user.last_name }}</strong>.
          They'll be told right away and have <strong>{{ DR_DAYS }} days</strong> to close your care with a final note.
          If they don't, it ends automatically on <strong>{{ drDate(drEndsPreview) }}</strong>.
        </p>
        <ul class="dr-points">
          <li>Your consultations, meal plans and progress stay in your account (read-only).</li>
          <li>Your meal plan and RND reminders stop when your care ends.</li>
          <li>You can then book any RND, including RND {{ careRnd?.user.first_name }} again.</li>
        </ul>
        <div class="field">
          <label class="field-label" for="dr-reason">Why are you ending care?</label>
          <select id="dr-reason" v-model="dr.reason" class="nm-select block" :class="{ invalid: drFieldErrors.reason }">
            <option value="" disabled>Choose a reason</option>
            <option v-for="r in DR_REASONS" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
          <p v-if="drFieldErrors.reason" class="field-error">{{ drFieldErrors.reason }}</p>
        </div>
        <div class="field">
          <label class="field-label" for="dr-note">Anything to add? <span class="optional-tag">{{ dr.reason === 'other' ? 'Required' : 'Optional' }}</span></label>
          <textarea id="dr-note" v-model="dr.note" class="field-input" rows="3" maxlength="500" data-allow-emoji
            :class="{ invalid: drFieldErrors.note }" placeholder="Your RND will see this." />
          <p v-if="drFieldErrors.note" class="field-error">{{ drFieldErrors.note }}</p>
        </div>
        <p v-if="drError" class="field-error">{{ drError }}
          <NuxtLink v-if="/upcoming consultation/i.test(drError)" to="/appointments" class="nm-btn-soft nm-btn-sm dr-link">Open My Appointments</NuxtLink>
        </p>
        <div class="nm-modal-actions">
          <button class="nm-btn-soft" type="button" :disabled="drBusy" @click="drOpen = false">Keep my RND</button>
          <button class="nm-btn-dark" type="button" :disabled="drBusy || !dr.reason || (dr.reason === 'other' && !dr.note.trim())" @click="requestDischarge">
            {{ drBusy ? 'Sending…' : 'Request discharge' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { Bell, CalendarCheck, Check, CheckCircle2, ClipboardList, FileText, HeartPulse, History as HistoryIcon, Pencil, Printer, Shield, ShieldCheck, Stethoscope, User, UtensilsCrossed, X } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'
import { formatPhone, phoneError } from '~/utils/phone'

const auth = useAuthStore()
const { get, patch, post, put, del } = useApi()

const tabs = [
  { key: 'personal', label: 'Personal info', icon: User },
  { key: 'health', label: 'Health profile', icon: HeartPulse },
  { key: 'care', label: 'Care team', icon: Stethoscope },
  { key: 'security', label: 'Security', icon: Shield },
  { key: 'notifications', label: 'Notifications', icon: Bell },
  { key: 'privacy', label: 'Privacy and data', icon: FileText },
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
  [auth.user?.email, memberSince.value && `Member since ${memberSince.value}`].filter(Boolean).join(', ')
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
// same spelling as sign-up (RegisterFlow.vue); matched ignoring case so older
// "Renal Nutrition"-style values still land on their option
const CONDITION_OPTIONS = ['Hypertension', 'Type 2 Diabetes', 'Obesity management', 'Renal nutrition']
const conditionOption = v => CONDITION_OPTIONS.find(c => c.toLowerCase() === String(v || '').trim().toLowerCase())
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
  } else if (conditionOption(primary)) {
    conditionChoice.value = conditionOption(primary)
  } else {
    conditionChoice.value = '__other'
    conditionOther.value = primary
  }
}

function nrsLabel(risk) {
  return { no_risk: 'no risk', at_risk: 'at risk', high_risk: 'high risk' }[risk] || ''
}

// TODO: mock/local only — no notification-preference field on User/ClientProfile.
/* ---------- NOTIFICATIONS & REMINDERS ---------- */
const REMINDER_OPTIONS = [
  { key: 'appointments', label: 'Consultation reminders', detail: '24 hours and 1 hour before each confirmed consultation.' },
  { key: 'payments', label: 'Payment reminders', detail: "If a consultation is still unpaid the day before. Unpaid ones are cancelled at the start time." },
  { key: 'meal_logging', label: 'Meal logging reminders', detail: "At each meal time in your meal plan, if you haven't logged that meal yet." },
  { key: 'rnd_reminders', label: 'Reminders from your RND', detail: 'Medication and habit reminders your RND sets for you.' },
]
const reminderPrefs = ref(null)
const reminderError = ref('')
async function loadReminders() {
  try {
    reminderPrefs.value = await get('/client/reminder-settings/')
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
function fireReminderToast(text) {
  fireToast(text)
}
onMounted(loadReminders)

/* ---------- Care team ---------- */
const careRnd = ref(null)
const careRel = ref(null) // the active care relationship (id + any discharge request)

/* ---------- request discharge (Care Team) ---------- */
const DR_DAYS = 3 // scheduling/discharge_requests.py DISCHARGE_REQUEST_DAYS
const DR_REASONS = [
  { value: 'different_rnd', label: 'I want a different RND' },
  { value: 'goal_reached', label: 'I reached my goal' },
  { value: 'moved', label: "I'm moving or no longer available" },
  { value: 'schedule', label: "The schedule doesn't work for me" },
  { value: 'cost', label: 'Cost' },
  { value: 'other', label: 'Other' },
]
const drOpen = ref(false)
const drBusy = ref(false)
const drError = ref('')
const drFieldErrors = reactive({ reason: '', note: '' })
const dr = reactive({ reason: '', note: '' })
const drEndsPreview = computed(() => new Date(Date.now() + DR_DAYS * 86400000).toISOString())
const drDate = (iso) => new Date(iso).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
function openDischarge() {
  Object.assign(dr, { reason: '', note: '' })
  Object.assign(drFieldErrors, { reason: '', note: '' })
  drError.value = ''
  drOpen.value = true
}
async function requestDischarge() {
  drBusy.value = true
  drError.value = ''
  Object.assign(drFieldErrors, { reason: '', note: '' })
  try {
    const res = await post(`/client/relationships/${careRel.value.id}/discharge-request/`, { reason: dr.reason, note: dr.note.trim() })
    careRel.value = { ...careRel.value, discharge_request: res.discharge_request }
    drOpen.value = false
    fireToast(`Request sent. RND ${careRnd.value.user.first_name} has been told.`)
  } catch (e) {
    const d = e?.data || {}
    drFieldErrors.reason = Array.isArray(d.reason) ? d.reason[0] : ''
    drFieldErrors.note = Array.isArray(d.note) ? d.note[0] : ''
    drError.value = d.detail || (drFieldErrors.reason || drFieldErrors.note ? '' : 'Could not send your request. Please try again.')
  } finally {
    drBusy.value = false
  }
}
async function withdrawDischarge() {
  drBusy.value = true
  drError.value = ''
  try {
    await del(`/client/relationships/${careRel.value.id}/discharge-request/`)
    careRel.value = { ...careRel.value, discharge_request: null }
    fireToast(`You're continuing your care with RND ${careRnd.value.user.first_name}.`)
  } catch (e) {
    drError.value = e?.data?.detail || 'Could not cancel your request. Please try again.'
  } finally {
    drBusy.value = false
  }
}
const careRndInitials = computed(() =>
  careRnd.value ? `${careRnd.value.user.first_name?.[0] || ''}${careRnd.value.user.last_name?.[0] || ''}`.toUpperCase() : ''
)

/* ---------- History (real screenings, appointments, meal logs) ---------- */
const historyFilters = [
  { key: 'all', label: 'All' },
  { key: 'screening', label: 'Screenings' },
  { key: 'appointment', label: 'Appointments' },
  { key: 'mealLog', label: 'Meal logs' },
]
const historyFilter = ref('all')
const historyEntries = ref([])
const isLoadingHistory = ref(false)
let historyLoaded = false

const APPT_TYPE = { video: 'Video', chat: 'Chat', in_person: 'In person' }
const APPT_STATUS = { pending: 'Pending', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }
const MEAL_LABELS = { breakfast: 'Breakfast', am_snack: 'AM Snack', lunch: 'Lunch', pm_snack: 'PM Snack', dinner: 'Dinner', bedtime_snack: 'Bedtime Snack' }
const LOG_STATUS = { followed: 'Followed the plan', partially_followed: 'Partly followed', not_followed: 'Did not follow' }

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
        detail: `BMI ${s.bmi} (${s.bmi_category}), NRS-2002 ${s.nrs_score ?? '—'}`,
      })),
      ...appointments.map(a => ({
        key: `a${a.id}`, type: 'appointment', at: a.created_at, icon: CalendarCheck, iconClass: 'icon-gold',
        title: `${APPT_TYPE[a.type] || a.type} appointment with RND ${a.relationship.rnd.first_name} ${a.relationship.rnd.last_name}`,
        detail: `${APPT_STATUS[a.status] || a.status}, scheduled ${formatTimestamp(a.scheduled_at)}`,
      })),
      ...mealLogs.map(l => ({
        key: `m${l.id}`, type: 'mealLog', at: l.updated_at, icon: UtensilsCrossed, iconClass: 'icon-green',
        title: `${MEAL_LABELS[mealTimeById[l.meal_plan_meal]] || 'Meal'} logged`,
        detail: `${LOG_STATUS[l.status] || 'Waiting for your RND to rate it'}, ${drDate(`${l.log_date}T00:00:00`)}${l.reason_notes ? `, ${l.reason_notes}` : ''}`,
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

// Phones: the tabs are a sideways-scrolling strip — keep the selected one in
// view (centred), also when the page opens on ?tab=… .
const tabCard = ref(null)
function showActiveTab() {
  nextTick(() => {
    const strip = tabCard.value
    const btn = strip?.querySelector('.tab-item.active')
    if (!strip || !btn || strip.scrollWidth <= strip.clientWidth) return
    // Clamped: Chrome ignores a smooth scroll to a negative position (the first tab).
    const left = Math.min(Math.max(0, btn.offsetLeft - (strip.clientWidth - btn.offsetWidth) / 2), strip.scrollWidth - strip.clientWidth)
    strip.scrollLeft = left
  })
}
watch(activeTab, () => showActiveTab())
onMounted(showActiveTab)

const filteredHistory = computed(() =>
  historyFilter.value === 'all' ? historyEntries.value : historyEntries.value.filter(e => e.type === historyFilter.value)
)
// 20 a page (Print still prints the whole filtered list); a new filter starts at page 1.
const HISTORY_PER_PAGE = 20
const historyPage = ref(1)
const historyPages = computed(() => Math.max(1, Math.ceil(filteredHistory.value.length / HISTORY_PER_PAGE)))
const pagedHistory = computed(() => filteredHistory.value.slice((historyPage.value - 1) * HISTORY_PER_PAGE, historyPage.value * HISTORY_PER_PAGE))
watch(historyFilter, () => { historyPage.value = 1 })

function formatTimestamp(iso) {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}
function printHistory() {
  window.print()
}

/* ---------- change password (Security tab; rules mirror PasswordComplexityValidator) ---------- */
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
    fireToast('Password changed. We emailed you a confirmation.')
  } catch (e) {
    const d = e?.data || {}
    const out = Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]))
    pwErrors.value = Object.keys(out).length ? out : { detail: 'Could not change your password. Please try again.' }
  } finally {
    savingPw.value = false
  }
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
    careRel.value = active || null
    if (active) careRnd.value = await get(`/client/rnds/${active.rnd.id}/`).catch(() => null)
  } catch {
    loadError.value = 'Could not load your profile. Please try again later.'
  }
})
// Care team stays current (a discharge, a new RND) without a reload. Only that
// part refreshes: the profile form is never touched.
async function refreshCare() {
  const relationships = await get('/client/relationships/')
  const active = relationships.find(r => r.status === 'active')
  careRel.value = active || null
  if (active && careRnd.value?.id !== active.rnd.id) careRnd.value = await get(`/client/rnds/${active.rnd.id}/`).catch(() => null)
  if (!active) careRnd.value = null
}
useAutoRefresh(refreshCare)
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

/* SHARED TAB PANEL HEADER */
.tab-panel-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; gap: 16px; }
.tab-panel-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0 0 4px; }
.tab-panel-sub { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
.sub-panel { border-top: 1px solid #d9e3dc; padding-top: 20px; margin-top: 24px; }
.sub-panel-title { font-family: 'Playfair Display', serif; font-size: 1rem; color: #1a3a1a; margin: 0 0 16px; }
.empty-note { font-size: 0.85rem; color: #9aaa9a; text-align: center; padding: 30px 0; margin: 0; }

/* HEALTH FIGURES: one divided panel */
.figs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 0; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; }
.fig { display: flex; flex-direction: column-reverse; gap: 2px; padding: 14px 18px; border-left: 1px solid #d9e3dc; min-width: 0; }
.fig:first-child { border-left: none; }
.fig dt { font-size: 0.8rem; color: #4a5a4a; }
.fig dd { margin: 0; font-family: 'Playfair Display', serif; font-size: 1.35rem; font-weight: 700; color: #1a3a1a; font-variant-numeric: lining-nums; }
.fig-unit { font-family: 'Inter', sans-serif; font-size: 0.76rem; font-weight: 500; color: #6a7a6a; }
.fig.risk dd { color: #a12525; }
.pager { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 16px; }
.pager-num { font-size: 0.84rem; color: #4a5a4a; font-variant-numeric: tabular-nums; }
.edit-foot { display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap; margin-top: 22px; padding-top: 16px; border-top: 1px solid #d9e3dc; }

/* SETTING ROWS (security, notifications, privacy, care team) */
.setting-row {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  background: #fff; border: none; border-top: 1px solid #d9e3dc; border-radius: 0; padding: 16px 0; margin: 0;
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
.icon-blue { background: #e3efe7; color: #0a4a37; }
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
  .tab-card { position: relative; flex-direction: row; overflow-x: auto; scrollbar-width: none; }
  .tab-card::-webkit-scrollbar { display: none; }
  .tab-item { flex-shrink: 0; padding: 10px 12px; }
}
@media (max-width: 640px) {
  .page-header { flex-direction: column; gap: 10px; }
  .page-title { font-size: 1.4rem; }
  .panel-card { padding: 20px 16px; }
  .form-grid, .info-grid { grid-template-columns: 1fr; }
  .figs { grid-template-columns: 1fr; }
  .fig { border-left: none; }
  .fig + .fig { border-top: 1px solid #d9e3dc; }
  .edit-foot > * { flex: 1; justify-content: center; }
  .info-item:nth-child(2) { border-top: 1px solid #f0f2f0; padding-top: 14px; }
  .tab-panel-header, .setting-row { flex-direction: column; align-items: stretch; }
  .outline-btn, .save-btn { justify-content: center; }
  .entry-row { flex-wrap: wrap; }
  .entry-time { width: 100%; padding-left: 48px; }
}

@media print {
  .page-header, .tab-card, .print-btn, .filter-tabs { display: none !important; }
  .profile-layout { grid-template-columns: 1fr; }
  .panel-card { border: none; padding: 0; }
}

/* Security tab — change password */
.pw-form { display: flex; flex-direction: column; gap: 14px; max-width: 440px; }
.pw-form > .setting-label { margin: 0; }
.pw-rules { list-style: none; padding: 0; margin: 4px 0 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 3px 12px; }
.pw-rules li { display: flex; align-items: center; gap: 6px; font-size: 0.74rem; color: #8a9a8a; }
.pw-rules li.ok { color: #1f8f5c; }
.pw-dot { width: 6px; height: 6px; border-radius: 50%; border: 1px solid #b0bab0; margin: 0 3px; }
.pw-show { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #4a5a4a; cursor: pointer; }
.pw-actions { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.pw-forgot { font-size: 0.82rem; color: #1a3a1a; font-weight: 600; text-decoration: underline; }
@media (max-width: 480px) { .pw-rules { grid-template-columns: 1fr; } }

/* Request discharge (Care Team) */
.dr-pending { margin-top: 12px; padding: 14px 16px; border: 1px solid #f0e2b0; border-radius: 12px; background: #fdf8e8; display: flex; flex-direction: column; gap: 8px; align-items: flex-start; }
.dr-title { margin: 0; font-size: 0.9rem; font-weight: 700; color: #6a5410; }
.dr-text { margin: 0; font-size: 0.84rem; line-height: 1.55; color: #4a5a4a; }
.dr-modal { max-width: 480px; }
.dr-modal > * + * { margin-top: 14px; }
.dr-points { margin: 0; padding-left: 18px; font-size: 0.82rem; color: #4a5a4a; line-height: 1.6; }
.dr-link { margin-left: 6px; }
.optional-tag { font-weight: 500; color: #8a9a8a; margin-left: 4px; }
</style>
