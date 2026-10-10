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
              <div class="info-item"><dt>Phone Number</dt><dd :class="{ muted: !personalInfo.phone }">{{ personalInfo.phone || 'Not provided' }}</dd></div>
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
              <label class="field-label" for="rp-phone">Phone Number</label>
              <input id="rp-phone" v-model="personalInfo.phone" type="tel" inputmode="tel" class="field-input" maxlength="20" placeholder="e.g. 0917 123 4567" />
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
            </dl>
            <a v-if="personalInfo.prcPhotoUrl" :href="personalInfo.prcPhotoUrl" target="_blank" rel="noopener" class="prc-photo-link">
              <FileImage :size="15" /> View license photo
            </a>
            <p class="field-hint">Your PRC details can't be edited here. To update them, contact the NutriMatch admin.</p>
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
          </template>

          <p v-if="profileError" class="profile-error">{{ profileError }}</p>
        </template>

        <!-- ============ EARNINGS ============ -->
        <template v-else-if="activeTab === 'earnings'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Earnings</h3>
              <p class="tab-panel-sub">Your share of each paid consultation, sent to you every 5th of the month.</p>
            </div>
          </div>

          <p v-if="earningsError" class="form-error">{{ earningsError }}</p>
          <p v-if="isLoadingEarnings" class="placeholder-text">Loading…</p>

          <template v-else-if="earnings">
          <p v-if="!earnings.has_payout_account" class="nm-note">
            <strong>Add your payout details below</strong> so we can send your earnings. Your balance is kept safe until you do.
          </p>

          <div class="stat-grid-4">
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Hourglass :size="17" /></div>
              <p class="mini-stat-value">{{ peso(earnings.pending) }}</p>
              <p class="mini-stat-label">Pending</p>
              <p class="mini-stat-note">Paid consultations on a {{ earnings.hold_days }}-day hold</p>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Wallet :size="17" /></div>
              <p class="mini-stat-value">{{ peso(earnings.posted) }}</p>
              <p class="mini-stat-label">Posted</p>
              <p class="mini-stat-note">Ready for your next payout</p>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Landmark :size="17" /></div>
              <p class="mini-stat-value">{{ peso(earnings.paid_out) }}</p>
              <p class="mini-stat-label">Paid out</p>
              <p class="mini-stat-note">All time</p>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><CalendarClock :size="17" /></div>
              <p class="mini-stat-value">{{ shortDate(earnings.next_payout_date) }}</p>
              <p class="mini-stat-label">Next payout</p>
              <p class="mini-stat-note" :class="{ warn: !earnings.eligible }">{{ nextPayoutNote }}</p>
            </div>
          </div>

          <p class="earnings-flow">
            <span class="nm-pill gold">Pending</span> a consultation is paid and completed →
            <span class="nm-pill green">Posted</span> after {{ earnings.hold_days }} days →
            <span class="nm-pill blue">Paid out</span> on the 5th, once your posted balance is at least {{ peso(earnings.minimum_payout) }} (smaller balances carry over).
          </p>

          <!-- PAYOUT DETAILS -->
          <div class="sub-panel">
            <div class="sub-panel-head">
              <h4 class="sub-panel-title" style="margin: 0">Payout details</h4>
              <button v-if="payoutAccount && !editingPayout" class="btn-outline-sm" @click="startPayoutEdit"><Pencil :size="13" /> Edit</button>
            </div>
            <dl v-if="payoutAccount && !editingPayout" class="info-grid">
              <div class="info-item"><dt>Method</dt><dd>{{ payoutAccount.method === 'gcash' ? 'GCash' : 'Bank transfer' }}</dd></div>
              <div v-if="payoutAccount.method === 'bank'" class="info-item"><dt>Bank</dt><dd>{{ payoutAccount.bank_name }}</dd></div>
              <div class="info-item"><dt>Account name</dt><dd>{{ payoutAccount.account_name }}</dd></div>
              <div class="info-item"><dt>{{ payoutAccount.method === 'gcash' ? 'GCash number' : 'Account number' }}</dt><dd>{{ payoutAccount.account_number }}</dd></div>
            </dl>
            <div v-else class="form-grid" style="margin-bottom: 0">
              <div class="field">
                <label class="field-label">Send my payouts to</label>
                <div class="mode-options">
                  <label class="mode-option" :class="{ checked: payoutForm.method === 'gcash' }">
                    <input v-model="payoutForm.method" type="radio" value="gcash" /> GCash
                  </label>
                  <label class="mode-option" :class="{ checked: payoutForm.method === 'bank' }">
                    <input v-model="payoutForm.method" type="radio" value="bank" /> Bank transfer
                  </label>
                </div>
              </div>
              <div v-if="payoutForm.method === 'bank'" class="field">
                <label class="field-label" for="po-bank">Bank</label>
                <input id="po-bank" v-model="payoutForm.bank_name" class="field-input" :class="{ invalid: payoutErrors.bank_name }" maxlength="100" placeholder="e.g. BDO, BPI, Landbank" />
                <p v-if="payoutErrors.bank_name" class="field-error">{{ payoutErrors.bank_name }}</p>
              </div>
              <div v-else class="field" />
              <div class="field">
                <label class="field-label" for="po-name">Account name</label>
                <input id="po-name" v-model="payoutForm.account_name" class="field-input" :class="{ invalid: payoutErrors.account_name }" maxlength="150" placeholder="Name on the account" />
                <p v-if="payoutErrors.account_name" class="field-error">{{ payoutErrors.account_name }}</p>
              </div>
              <div class="field">
                <label class="field-label" for="po-number">{{ payoutForm.method === 'gcash' ? 'GCash number' : 'Account number' }}</label>
                <input id="po-number" v-model="payoutForm.account_number" class="field-input" :class="{ invalid: payoutErrors.account_number }" inputmode="numeric" maxlength="30"
                  :placeholder="payoutForm.method === 'gcash' ? '09XX XXX XXXX' : '6–20 digits'" />
                <p v-if="payoutErrors.account_number" class="field-error">{{ payoutErrors.account_number }}</p>
                <p v-else class="field-hint">Only the NutriMatch admin sees this, to send your payouts.</p>
              </div>
            </div>
            <p v-if="payoutErrors.detail" class="profile-error">{{ payoutErrors.detail }}</p>
            <div v-if="!payoutAccount || editingPayout" class="payout-actions">
              <button v-if="payoutAccount" class="btn-outline-sm" @click="editingPayout = false">Cancel</button>
              <button class="btn-dark" :disabled="savingPayout" @click="savePayoutAccount">{{ savingPayout ? 'Saving…' : 'Save payout details' }}</button>
            </div>
            <p v-if="payoutSaved" class="field-hint" style="color: #1f8f5c">Payout details saved.</p>
          </div>

          <div class="sub-panel">
            <h4 class="sub-panel-title">Earnings trend (last 6 months)</h4>
            <div class="chart-wrap">
              <div class="chart-y-axis">
                <span v-for="tick in yTicks" :key="tick">{{ tick.toLocaleString() }}</span>
              </div>
              <div class="chart-bars">
                <div v-for="point in earningsTrend" :key="point.month" class="chart-col">
                  <div class="chart-bar" :style="{ height: barHeight(point.amount) + '%' }"></div>
                  <span class="chart-label">{{ point.month }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="sub-panel">
            <h4 class="sub-panel-title">Consultations</h4>
            <p v-if="!earnings.items.length" class="empty-note">No paid consultations yet.</p>
            <div v-else class="nm-table-wrap">
              <table class="nm-table stack">
                <thead>
                  <tr><th>Invoice</th><th>Patient</th><th>Consultation</th><th class="nm-num">Fee</th><th class="nm-num">Commission</th><th class="nm-num">Your share</th><th>Status</th></tr>
                </thead>
                <tbody>
                  <tr v-for="item in earnings.items" :key="item.invoice_id">
                    <td data-label="Invoice"><strong>INV-{{ String(item.invoice_id).padStart(4, '0') }}</strong></td>
                    <td data-label="Patient">{{ item.client_name }}</td>
                    <td data-label="Consultation">{{ shortDate(item.appointment_date) }}</td>
                    <td data-label="Fee" class="nm-num">{{ peso(item.amount) }}</td>
                    <td data-label="Commission" class="nm-num">{{ peso(item.commission) }}</td>
                    <td data-label="Your share" class="nm-num"><strong>{{ peso(item.share) }}</strong></td>
                    <td data-label="Status">
                      <span class="nm-pill" :class="STATE_PILLS[item.state]">{{ STATE_LABELS[item.state] || item.state }}</span>
                      <span v-if="item.state === 'pending'" class="state-note">{{ item.posts_on ? `Posts ${shortDate(item.posts_on)}` : 'After the consultation' }}</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="sub-panel">
            <h4 class="sub-panel-title">Payout history</h4>
            <p v-if="!earnings.payouts.length" class="empty-note">No payouts yet — your first one arrives on a payout day once your posted balance reaches {{ peso(earnings.minimum_payout) }}.</p>
            <div v-for="p in earnings.payouts" :key="p.id" class="nm-row">
              <div class="nm-row-main">
                <p class="nm-row-title">{{ peso(p.amount) }} · {{ p.invoice_count }} consultation{{ p.invoice_count === 1 ? '' : 's' }}</p>
                <p class="nm-row-sub">{{ dateTime(p.released_at) }} · {{ p.method === 'gcash' ? 'GCash' : (p.bank_name || 'Bank') }} {{ p.account_number }} · Ref {{ p.reference }}</p>
              </div>
              <span class="nm-pill blue">Paid out</span>
            </div>
          </div>
          </template>
        </template>

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
            <select v-model="newLanguage" class="field-input language-select">
              <option value="">Add a language...</option>
              <option v-for="opt in availableLanguageOptions" :key="opt.code" :value="opt.code">{{ opt.name }}</option>
            </select>
            <button class="save-btn" type="button" :disabled="!newLanguage" @click="addLanguage">Add</button>
          </div>
          <p v-if="languageError" class="profile-error">{{ languageError }}</p>
        </template>

        <!-- ============ REVIEWS ============ -->
        <template v-else-if="activeTab === 'reviews'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Reviews</h3>
              <p class="tab-panel-sub">See what your patients are saying about their care.</p>
            </div>
          </div>

          <div v-if="reviews.length" class="summary-row">
            <div class="score-card">
              <p class="score-number">{{ reviewsSummary.average.toFixed(1) }}</p>
              <div class="stars-row">
                <Star
                  v-for="n in 5" :key="n" :size="17"
                  :fill="n <= Math.round(reviewsSummary.average) ? '#D4A017' : 'none'"
                  :color="n <= Math.round(reviewsSummary.average) ? '#D4A017' : '#d5dad5'"
                  :stroke-width="1.5"
                />
              </div>
              <p class="score-caption">Based on {{ reviewsSummary.total }} reviews</p>
            </div>

            <div class="breakdown-card">
              <div v-for="row in ratingBreakdown" :key="row.stars" class="breakdown-row">
                <span class="breakdown-label">{{ row.stars }} star{{ row.stars !== 1 ? 's' : '' }}</span>
                <div class="breakdown-track">
                  <div class="breakdown-fill" :style="{ width: maxCount ? `${(row.count / maxCount) * 100}%` : '0%' }" />
                </div>
                <span class="breakdown-count">{{ row.count }}</span>
              </div>
            </div>
          </div>

          <div v-if="reviews.length" class="review-list">
            <div v-for="review in reviews" :key="review.id" class="review-card">
              <div class="review-top">
                <div class="review-who">
                  <div class="review-avatar" :style="{ background: review.avatarColor }">{{ review.initials }}</div>
                  <div>
                    <p class="review-name">{{ review.name }}</p>
                    <div class="stars-row stars-row-sm">
                      <Star
                        v-for="n in 5" :key="n" :size="13"
                        :fill="n <= review.rating ? '#D4A017' : 'none'"
                        :color="n <= review.rating ? '#D4A017' : '#d5dad5'"
                        :stroke-width="1.5"
                      />
                    </div>
                  </div>
                </div>
                <span class="review-time">{{ review.postedAt }}</span>
              </div>
              <p class="review-comment">"{{ review.comment }}"</p>
            </div>
          </div>
          <p v-else class="empty-note">No reviews yet.</p>
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
import { computed, onMounted, reactive, ref } from 'vue'
import {
  Briefcase, BadgeCheck,
  Landmark, Wallet, Hourglass,
  Star, CalendarClock, X, Languages,
  Video, MessageCircle, Users, Lock, FileImage, Pencil, Check, CheckCircle2
} from 'lucide-vue-next'
import { db } from '~/mock/mockDatabase'

const { get, patch, put } = useApi()

definePageMeta({ layout: 'dashboard', title: 'Profile Settings' })

const tabs = [
  { key: 'professional', label: 'Professional Profile', icon: Briefcase },
  { key: 'earnings', label: 'Earnings', icon: Wallet },
  { key: 'availability', label: 'Availability', icon: CalendarClock },
  { key: 'languages', label: 'Languages', icon: Languages },
  { key: 'reviews', label: 'Reviews', icon: Star },
]

const route = useRoute()
const validTabKeys = tabs.map(t => t.key)

const activeTab = ref(validTabKeys.includes(route.query.tab) ? route.query.tab : 'professional')
const activeTabLabel = computed(() => tabs.find(t => t.key === activeTab.value)?.label)

/* ---------- PROFESSIONAL PROFILE ---------- */
const auth = useAuthStore()

const MODE_OPTIONS = [
  { value: 'video', label: 'Video', icon: Video },
  { value: 'chat', label: 'Chat', icon: MessageCircle },
  { value: 'in_person', label: 'In-Person', icon: Users },
]

const personalInfo = ref({
  firstName: '', lastName: '', email: '', phone: '', bio: '', consultationFee: '',
  consultationModes: [], initials: '', avatarColor: db.personalInfo.avatarColor,
  prcVerified: false, prcNumber: '', prcVerifiedOn: '', prcPhotoUrl: '',
})
const isSavingProfile = ref(false)
const profileError = ref('')
const isEditing = ref(false)
const profileLoaded = ref(false)
// Last loaded profile — Cancel restores the form from it.
const lastLoaded = ref(null)
const fieldErrors = reactive({ firstName: '', lastName: '' })

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
  fieldErrors.firstName = fieldErrors.lastName = ''
  personalInfo.value.firstName = personalInfo.value.firstName.trim()
  personalInfo.value.lastName = personalInfo.value.lastName.trim()
  if (!personalInfo.value.firstName) fieldErrors.firstName = 'Enter your first name.'
  else if (!NAME_RE.test(personalInfo.value.firstName)) fieldErrors.firstName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  if (!personalInfo.value.lastName) fieldErrors.lastName = 'Enter your last name.'
  else if (!NAME_RE.test(personalInfo.value.lastName)) fieldErrors.lastName = 'Use letters only (spaces, hyphens and apostrophes are fine).'
  if (fieldErrors.firstName || fieldErrors.lastName) return
  if (!personalInfo.value.consultationModes.length) {
    profileError.value = 'Offer at least one consultation format.'
    return
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
        phone: (personalInfo.value.phone || '').trim() || null,
      }),
      patch('/rnd/profile/', {
        bio: personalInfo.value.bio,
        consultation_fee: Number(fee).toFixed(2),
        consultation_modes: personalInfo.value.consultationModes,
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
    profileError.value = fieldErrors.firstName || fieldErrors.lastName
      ? ''
      : data.detail || Object.values(data).flat()[0] || 'Could not save your changes. Please try again.'
  } finally {
    isSavingProfile.value = false
  }
}

/* ---------- EARNINGS ---------- */
// Pending (paid, on hold) → Posted → Paid out on the 5th (billing/payouts.py).
const STATE_LABELS = { pending: 'Pending', posted: 'Posted', paid_out: 'Paid out' }
const STATE_PILLS = { pending: 'gold', posted: 'green', paid_out: 'blue' }
const earnings = ref(null)
const rawInvoices = ref([])
const isLoadingEarnings = ref(true)
const earningsError = ref('')

async function loadEarnings() {
  isLoadingEarnings.value = true
  earningsError.value = ''
  try {
    const [e, inv, account] = await Promise.all([
      get('/rnd/earnings/'),
      get('/rnd/invoices/'),
      get('/rnd/payout-account/').catch(() => null),
    ])
    earnings.value = e
    rawInvoices.value = inv
    payoutAccount.value = account && account.method ? account : null
  } catch {
    earningsError.value = 'Could not load your earnings. Please try again later.'
  } finally {
    isLoadingEarnings.value = false
  }
}
onMounted(loadEarnings)

const nextPayoutNote = computed(() => {
  const e = earnings.value
  if (!e) return ''
  if (!e.has_payout_account) return 'Add payout details first'
  if (e.eligible) return `${peso(e.posted)} will be sent`
  return `Needs ${peso(e.minimum_payout)} posted — carries over`
})

/* payout details (GCash / bank) */
const payoutAccount = ref(null)
const editingPayout = ref(false)
const savingPayout = ref(false)
const payoutSaved = ref(false)
const payoutForm = reactive({ method: 'gcash', account_name: '', account_number: '', bank_name: '' })
const payoutErrors = reactive({})

function startPayoutEdit() {
  Object.assign(payoutForm, { method: 'gcash', account_name: '', account_number: '', bank_name: '' }, payoutAccount.value || {})
  for (const k of Object.keys(payoutErrors)) delete payoutErrors[k]
  editingPayout.value = true
}

async function savePayoutAccount() {
  for (const k of Object.keys(payoutErrors)) delete payoutErrors[k]
  payoutSaved.value = false
  if (!payoutForm.account_name.trim()) payoutErrors.account_name = 'Enter the name on the account.'
  if (!payoutForm.account_number.trim()) payoutErrors.account_number = payoutForm.method === 'gcash' ? 'Enter your GCash number.' : 'Enter your account number.'
  if (payoutForm.method === 'bank' && !payoutForm.bank_name.trim()) payoutErrors.bank_name = 'Enter your bank.'
  if (Object.keys(payoutErrors).length) return
  savingPayout.value = true
  try {
    payoutAccount.value = await put('/rnd/payout-account/', {
      method: payoutForm.method,
      account_name: payoutForm.account_name.trim(),
      account_number: payoutForm.account_number.trim(),
      bank_name: payoutForm.method === 'bank' ? payoutForm.bank_name.trim() : '',
    })
    editingPayout.value = false
    payoutSaved.value = true
    earnings.value = await get('/rnd/earnings/')
    setTimeout(() => { payoutSaved.value = false }, 3000)
  } catch (e) {
    const data = e?.data || {}
    for (const k of ['account_name', 'account_number', 'bank_name', 'method']) {
      if (data[k]) payoutErrors[k] = Array.isArray(data[k]) ? data[k][0] : data[k]
    }
    if (!Object.keys(payoutErrors).length) payoutErrors.detail = data.detail || 'Could not save your payout details. Please try again.'
  } finally {
    savingPayout.value = false
  }
}

const earningsTrend = computed(() => {
  const now = new Date()
  const months = []
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({ year: d.getFullYear(), month: d.getMonth(), label: d.toLocaleDateString('en-US', { month: 'short' }) })
  }
  return months.map(m => {
    const amount = rawInvoices.value
      .filter(inv => {
        if (inv.status !== 'paid') return false
        const d = new Date(inv.paid_at || inv.created_at)
        return d.getFullYear() === m.year && d.getMonth() === m.month
      })
      .reduce((sum, inv) => sum + Number(inv.net), 0)
    return { month: m.label, amount }
  })
})

const maxAmount = computed(() => Math.max(...earningsTrend.value.map(p => p.amount), 5000))
const yTicks = computed(() => {
  const step = Math.ceil(maxAmount.value / 5 / 1000) * 1000
  return [0, step, step * 2, step * 3, step * 4, step * 5].reverse()
})
function barHeight(amount) {
  const topTick = yTicks.value[0] || 5000
  return Math.min(100, Math.round((amount / topTick) * 100))
}

/* ---------- REVIEWS ---------- */
const reviewsSummary = ref(db.reviewsSummary)
const ratingBreakdown = ref(db.ratingBreakdown)
const reviews = ref(db.reviews)
const maxCount = computed(() => Math.max(0, ...ratingBreakdown.value.map(r => r.count)))

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
.sub-panel { border-top: 1px solid #f0f2f0; padding-top: 20px; margin-top: 20px; }
.sub-panel-title { font-family: 'Playfair Display', serif; font-size: 1rem; color: #1a3a1a; margin: 0 0 16px; }
.empty-note { font-size: 0.85rem; color: #9aaa9a; text-align: center; padding: 30px 0; }

/* EARNINGS TAB */
.period-select { position: relative; flex-shrink: 0; }
.period-select select {
  appearance: none; border: 1px solid #dde3dd; background: #fff;
  padding: 9px 32px 9px 14px; border-radius: 8px; font-size: 0.85rem; color: #1a3a1a; cursor: pointer;
}
.select-caret { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #9aaa9a; pointer-events: none; }

.stat-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.mini-stat-card { background: #fafbfa; border-radius: 10px; padding: 16px 18px; border: 1px solid #f0f2f0; }
.mini-stat-icon {
  width: 30px; height: 30px; border-radius: 8px; background: #eef1ee;
  display: flex; align-items: center; justify-content: center; color: #4a5a4a; margin-bottom: 10px;
}
.mini-stat-value { font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.mini-stat-label { font-size: 0.75rem; color: #8a9a8a; margin: 3px 0 0; }

.chart-wrap { display: flex; gap: 12px; }
.chart-y-axis { display: flex; flex-direction: column; justify-content: space-between; font-size: 0.7rem; color: #9aaa9a; padding-bottom: 24px; text-align: right; min-width: 44px; }
.chart-bars { flex: 1; display: flex; align-items: flex-end; gap: 16px; height: 200px; border-left: 1px solid #eceeec; padding-left: 16px; }
.chart-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.chart-bar { width: 60%; background: #163a1c; border-radius: 4px 4px 0 0; min-height: 2px; }
.chart-label { font-size: 0.76rem; color: #8a9a8a; margin-top: 8px; }

.invoice-table { width: 100%; border-collapse: collapse; }
.invoice-table th { text-align: left; font-size: 0.66rem; letter-spacing: 0.05em; color: #9aaa9a; padding-bottom: 12px; }
.invoice-table td { padding: 12px 10px 12px 0; border-top: 1px solid #f2f4f2; font-size: 0.83rem; color: #3a4a3a; }
.invoice-id { font-weight: 700; color: #1a3a1a; }
.invoice-date { color: #3b6fd6; }
.invoice-commission { color: #9aaa9a; }
.invoice-net { font-weight: 700; color: #1a3a1a; }
.status-pill { font-size: 0.7rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; }
.status-paid { background: #e6f4e6; color: #2e7d32; }
.status-pending { background: #fdf1d6; color: #b8860b; }

.mini-stat-note { font-size: 0.72rem; color: #9aaa9a; margin: 4px 0 0; line-height: 1.4; }
.mini-stat-note.warn { color: #b8860b; font-weight: 600; }
.earnings-flow { font-size: 0.8rem; color: #6a7a6a; line-height: 2; margin: 14px 0 0; }
.sub-panel-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.btn-outline-sm { display: inline-flex; align-items: center; gap: 6px; background: #fff; color: #1a3a1a; border: 1px solid #d5dad5; border-radius: 8px; padding: 7px 12px; font-size: 0.8rem; font-weight: 600; cursor: pointer; font-family: inherit; }
.btn-outline-sm:hover { background: #f7f9f7; }
.payout-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
.state-note { display: block; font-size: 0.7rem; color: #9aaa9a; margin-top: 3px; }

/* REVIEWS TAB */
.summary-row { display: grid; grid-template-columns: 220px 1fr; gap: 14px; margin-bottom: 20px; }
.score-card { background: #fafbfa; border-radius: 10px; border: 1px solid #f0f2f0; padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.score-number { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stars-row { display: flex; gap: 3px; margin-top: 6px; }
.stars-row-sm { margin-top: 2px; }
.score-caption { font-size: 0.78rem; color: #8a9a8a; margin: 8px 0 0; }
.breakdown-card { background: #fafbfa; border-radius: 10px; border: 1px solid #f0f2f0; padding: 18px 22px; display: flex; flex-direction: column; justify-content: center; gap: 9px; }
.breakdown-row { display: flex; align-items: center; gap: 10px; }
.breakdown-label { width: 46px; font-size: 0.78rem; color: #4a5a4a; }
.breakdown-track { flex: 1; height: 7px; border-radius: 999px; background: #eceeec; overflow: hidden; }
.breakdown-fill { height: 100%; background: #D4A017; border-radius: 999px; }
.breakdown-count { width: 20px; text-align: right; font-size: 0.78rem; color: #8a9a8a; }

.review-list { display: flex; flex-direction: column; gap: 14px; }
.review-card { background: #fafbfa; border-radius: 10px; border: 1px solid #f0f2f0; padding: 16px 20px; }
.review-top { display: flex; align-items: flex-start; justify-content: space-between; }
.review-who { display: flex; align-items: flex-start; gap: 12px; }
.review-avatar { width: 34px; height: 34px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; }
.review-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.review-time { font-size: 0.76rem; color: #9aaa9a; white-space: nowrap; }
.review-comment { font-size: 0.84rem; color: #4a5a4a; line-height: 1.55; margin: 10px 0 0 46px; }

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
  .stat-grid-4 { grid-template-columns: repeat(2, 1fr); }
  .summary-row { grid-template-columns: 1fr; }
  .block-form { grid-template-columns: 1fr; }
}

/* MOBILE — same as the client settings page (ClientProfileSettings.vue):
   tabs become a sideways-scrolling strip above the panel. */
@media (max-width: 900px) {
  .profile-layout { grid-template-columns: 1fr; }
  .tab-card { flex-direction: row; overflow-x: auto; scrollbar-width: none; }
  .tab-card::-webkit-scrollbar { display: none; }
  .tab-item { flex-shrink: 0; padding: 10px 12px; white-space: nowrap; }
  .panel-card { min-width: 0; }
  .sub-panel { overflow-x: auto; }
}
@media (max-width: 640px) {
  .page-header { flex-direction: column; gap: 10px; }
  .page-title { font-size: 1.4rem; }
  .panel-card { padding: 20px 16px; }
  .form-grid, .stat-grid-4, .info-grid { grid-template-columns: 1fr; }
  .info-grid .info-item:nth-child(2) { border-top: 1px solid #f0f2f0; padding-top: 14px; }
  .tab-panel-header { flex-direction: column; }
  .language-add-row { flex-wrap: wrap; }
}
</style>