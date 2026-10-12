<template>
  <div class="nm-page">
    <NuxtLink to="/users" class="nm-panel-link back-link"><ArrowLeft :size="14" /> All users</NuxtLink>

    <p v-if="error" class="nm-error">{{ error }}</p>
    <p v-if="loading" class="nm-muted">Loading account…</p>

    <template v-else-if="data">
      <!-- identity + actions -->
      <div class="nm-panel identity">
        <div class="identity-main">
          <img v-if="u.profile_photo" :src="u.profile_photo" class="nm-avatar lg" alt="" />
          <span v-else class="nm-avatar lg">{{ userInitials(u.first_name, u.last_name) }}</span>
          <div style="min-width: 0">
            <h1 class="nm-page-title" style="margin: 0">{{ u.first_name }} {{ u.last_name }}</h1>
            <p class="nm-page-sub">{{ u.email }}<span v-if="u.phone"> · {{ u.phone }}</span></p>
            <div class="pill-row">
              <span class="nm-pill blue">{{ roleLabel }}</span>
              <span class="nm-pill" :class="account.is_active ? 'green' : 'red'">{{ account.is_active ? 'Active' : 'Deactivated' }}</span>
              <span v-if="rnd" class="nm-pill" :class="reviewPill">{{ reviewLabel }}</span>
            </div>
          </div>
        </div>
        <div v-if="!isSelf" class="identity-actions">
          <button class="nm-btn-outline" :disabled="busy" @click="openEdit"><Pencil :size="14" /> Edit details</button>
          <button class="nm-btn-outline" :disabled="busy" @click="sendReset"><KeyRound :size="14" /> Send password reset</button>
          <button v-if="account.is_active" class="nm-btn-danger" :disabled="busy" @click="openDeactivate"><Ban :size="14" /> Deactivate</button>
          <button v-else class="nm-btn-dark" :disabled="busy" @click="reactivate"><RotateCcw :size="14" /> Reactivate</button>
        </div>
      </div>

      <p v-if="client" class="nm-note">
        This page shows health information. Your view was recorded in the audit log (RA 10173).
      </p>

      <div class="nm-grid">
        <div class="nm-col">
          <!-- CLIENT -->
          <template v-if="client">
            <div class="nm-panel">
              <h2 class="nm-panel-title">Personal details</h2>
              <dl class="nm-dl" style="margin-top: 14px">
                <div><dt>Date of birth</dt><dd :class="{ muted: !client.profile.date_of_birth }">{{ dobText(client.profile.date_of_birth) }}</dd></div>
                <div><dt>Sex</dt><dd :class="{ muted: !client.profile.sex }">{{ cap(client.profile.sex) || 'Not given' }}</dd></div>
                <div><dt>Address</dt><dd :class="{ muted: !client.profile.address }">{{ client.profile.address || 'Not given' }}</dd></div>
                <div><dt>Emergency contact</dt><dd :class="{ muted: !client.profile.emergency_contact }">{{ emergencyText }}</dd></div>
              </dl>
            </div>

            <div class="nm-panel">
              <h2 class="nm-panel-title">Health background</h2>
              <dl class="nm-dl" style="margin-top: 14px">
                <div><dt>Conditions</dt><dd :class="{ muted: !listText(client.health.medical_conditions) }">{{ listText(client.health.medical_conditions) || 'None listed' }}</dd></div>
                <div><dt>Allergies</dt><dd :class="{ muted: !listText(client.health.allergies) }">{{ allergyText }}</dd></div>
                <div><dt>Dietary restrictions</dt><dd :class="{ muted: !listText(client.health.dietary_restrictions) }">{{ listText(client.health.dietary_restrictions) || 'None listed' }}</dd></div>
                <div><dt>Religion</dt><dd :class="{ muted: !client.health.religion }">{{ client.health.religion || 'Not given' }}</dd></div>
                <div><dt>Health goals</dt><dd :class="{ muted: !listText(client.health.health_goals) }">{{ listText(client.health.health_goals) || 'None listed' }}</dd></div>
              </dl>
            </div>

            <div class="nm-panel">
              <div class="nm-panel-head">
                <div>
                  <h2 class="nm-panel-title">Latest screening</h2>
                  <p class="nm-panel-sub">{{ client.screening_count }} screening{{ client.screening_count === 1 ? '' : 's' }} in total</p>
                </div>
              </div>
              <div v-if="!s" class="nm-empty"><p>No pre-consultation screening yet.</p></div>
              <dl v-else class="nm-dl">
                <div><dt>Taken</dt><dd>{{ dateTime(s.created_at) }}</dd></div>
                <div><dt>Height / weight</dt><dd>{{ num(s.height_cm) }} cm · {{ num(s.weight_kg) }} kg</dd></div>
                <div><dt>BMI</dt><dd>{{ num(s.bmi) }} <span v-if="s.bmi_category" class="nm-muted">({{ cap(s.bmi_category) }})</span></dd></div>
                <div><dt>TDEE</dt><dd>{{ s.tdee_kcal ? `${Math.round(s.tdee_kcal)} kcal/day` : '—' }}</dd></div>
                <div><dt>NRS-2002</dt><dd>{{ s.nrs_score ?? '—' }} <span v-if="s.nrs_risk" class="nm-muted">({{ cap(s.nrs_risk) }})</span></dd></div>
              </dl>
            </div>
          </template>

          <!-- RND -->
          <template v-if="rnd">
            <div v-if="rnd.profile.review_status === 'rejected' && rnd.profile.rejection_reason" class="nm-error">
              Rejected: {{ rnd.profile.rejection_reason }}
            </div>
            <div class="nm-panel">
              <div class="nm-panel-head">
                <h2 class="nm-panel-title">Credentials</h2>
                <NuxtLink v-if="rnd.profile.review_status === 'pending'" to="/rnd-verification" class="nm-panel-link">Review application →</NuxtLink>
              </div>
              <dl class="nm-dl">
                <div><dt>PRC license no.</dt><dd :class="{ muted: !rnd.profile.prc_license_number }">{{ rnd.profile.prc_license_number || 'Not given' }}</dd></div>
                <div><dt>Specialization</dt><dd>{{ rnd.profile.specialization || '—' }}</dd></div>
                <div><dt>Date of birth</dt><dd :class="{ muted: !rnd.profile.date_of_birth }">{{ dobText(rnd.profile.date_of_birth) }}</dd></div>
                <div><dt>Verified</dt><dd :class="{ muted: !rnd.profile.verified_at }">{{ rnd.profile.verified_at ? shortDate(rnd.profile.verified_at) : 'Not yet' }}</dd></div>
              </dl>
              <a v-if="rnd.profile.prc_license_image_url" :href="rnd.profile.prc_license_image_url" target="_blank" rel="noopener" class="license">
                <img :src="rnd.profile.prc_license_image_url" alt="PRC license photo" />
                <span><FileImage :size="14" /> Open PRC license photo</span>
              </a>
              <p v-else class="nm-muted" style="margin-top: 12px">No PRC license photo on file.</p>
            </div>

            <div class="nm-panel">
              <h2 class="nm-panel-title">Practice</h2>
              <p v-if="rnd.profile.bio" class="bio">{{ rnd.profile.bio }}</p>
              <dl class="nm-dl" style="margin-top: 14px">
                <div><dt>Consultation fee</dt><dd>{{ rnd.profile.consultation_fee ? peso(rnd.profile.consultation_fee) : '—' }}</dd></div>
                <div><dt>Modes</dt><dd>{{ (rnd.profile.consultation_modes || []).map(m => MODE_LABELS[m] || m).join(', ') || '—' }}</dd></div>
                <div><dt>Languages</dt><dd>{{ rnd.languages.join(', ') || '—' }}</dd></div>
                <div><dt>New clients</dt><dd>{{ rnd.profile.available_for_new_clients ? 'Accepting' : 'Not accepting' }}</dd></div>
                <div v-if="(rnd.profile.consultation_modes || []).includes('in_person')"><dt>Clinic address</dt><dd :class="{ muted: !rnd.profile.clinic_address }">{{ rnd.profile.clinic_address || 'Not added yet' }}</dd></div>
              </dl>
              <p class="nm-section-title">Weekly hours</p>
              <p v-if="!hours.length" class="nm-muted">No availability set.</p>
              <p v-for="line in hours" :key="line" class="hours-line">{{ line }}</p>
              <p v-if="requiredMissing.length" class="nm-note" style="margin: 14px 0 0">
                Clients can't book this RND yet. Still to do: {{ requiredMissing.map(m => m.label.toLowerCase()).join('; ') }}.
              </p>
            </div>
          </template>
        </div>

        <div class="nm-col">
          <!-- client activity -->
          <div v-if="client" class="nm-panel">
            <div class="nm-panel-head" style="margin-bottom: 0">
              <h2 class="nm-panel-title">Activity</h2>
              <NuxtLink :to="`/admin-appointments?view=all&client=${u.id}`" class="nm-panel-link">Appointments →</NuxtLink>
            </div>
            <dl class="nm-dl" style="margin-top: 14px">
              <div><dt>Appointments</dt><dd>{{ countText(client.appointments) }}</dd></div>
              <div><dt>Total paid</dt><dd>{{ peso(client.invoices.paid_total) }}</dd></div>
            </dl>
            <p class="nm-section-title">RNDs</p>
            <p v-if="!client.rnds.length" class="nm-muted">Hasn't booked an RND yet.</p>
            <div v-for="r in client.rnds" :key="r.rnd_id" class="nm-row">
              <div class="nm-row-main">
                <NuxtLink :to="`/users/${r.rnd_id}`" class="nm-row-title link">{{ r.name }}</NuxtLink>
              </div>
              <span class="nm-pill" :class="r.status === 'active' ? 'green' : 'muted'">{{ cap(r.status) }}</span>
            </div>
          </div>

          <!-- RND money -->
          <template v-if="rnd">
            <div class="nm-panel">
              <div class="nm-panel-head">
                <div>
                  <h2 class="nm-panel-title">Earnings</h2>
                  <p class="nm-panel-sub">Next payout {{ shortDate(rnd.earnings.next_payout_date) }}</p>
                </div>
                <NuxtLink to="/payouts" class="nm-panel-link">Payouts →</NuxtLink>
              </div>
              <dl class="nm-dl">
                <div><dt>Pending</dt><dd>{{ peso(rnd.earnings.pending) }}</dd></div>
                <div><dt>Posted (ready)</dt><dd>{{ peso(rnd.earnings.posted) }}</dd></div>
                <div><dt>Paid out</dt><dd>{{ peso(rnd.earnings.paid_out) }}</dd></div>
                <div><dt>Payouts made</dt><dd>{{ rnd.payouts }}</dd></div>
              </dl>
            </div>

            <div class="nm-panel">
              <h2 class="nm-panel-title">Payout details</h2>
              <p v-if="!rnd.payout_account" class="nm-note" style="margin: 14px 0 0">
                No GCash or bank details yet — their balance is held until they add them.
              </p>
              <dl v-else class="nm-dl" style="margin-top: 14px">
                <div><dt>Method</dt><dd>{{ rnd.payout_account.method_label }}</dd></div>
                <div v-if="rnd.payout_account.bank_name"><dt>Bank</dt><dd>{{ rnd.payout_account.bank_name }}</dd></div>
                <div><dt>Account name</dt><dd>{{ rnd.payout_account.account_name }}</dd></div>
                <div><dt>Account number</dt><dd class="mono">{{ rnd.payout_account.account_number }}</dd></div>
                <div><dt>Last updated</dt><dd>{{ shortDate(rnd.payout_account.updated_at) }}</dd></div>
              </dl>
            </div>

            <div class="nm-panel">
              <div class="nm-panel-head" style="margin-bottom: 0">
                <h2 class="nm-panel-title">Practice activity</h2>
                <NuxtLink :to="`/admin-appointments?view=all&rnd=${u.id}`" class="nm-panel-link">Appointments →</NuxtLink>
              </div>
              <dl class="nm-dl" style="margin-top: 14px">
                <div><dt>Active patients</dt><dd>{{ rnd.patients }}</dd></div>
                <div><dt>Rating</dt><dd>{{ rnd.rating.average ? `${rnd.rating.average} ★ (${rnd.rating.count})` : 'No reviews yet' }}</dd></div>
                <div><dt>Appointments</dt><dd>{{ countText(rnd.appointments) }}</dd></div>
              </dl>
            </div>
          </template>

          <!-- account -->
          <div class="nm-panel">
            <h2 class="nm-panel-title">Account</h2>
            <dl class="nm-dl" style="margin-top: 14px">
              <div><dt>Joined</dt><dd>{{ shortDate(u.created_at) }}</dd></div>
              <div><dt>Last sign-in</dt><dd :class="{ muted: !account.last_login }">{{ account.last_login ? dateTime(account.last_login) : 'Never' }}</dd></div>
              <div><dt>Email verified</dt><dd :class="{ muted: !account.email_verified_at }">{{ account.email_verified_at ? shortDate(account.email_verified_at) : 'Not verified' }}</dd></div>
              <div><dt>Terms accepted</dt><dd :class="{ muted: !account.terms_accepted_at }">{{ account.terms_accepted_at ? shortDate(account.terms_accepted_at) : '—' }}</dd></div>
              <div><dt>Data-privacy consent</dt><dd :class="{ muted: !account.data_consent_at }">{{ account.data_consent_at ? shortDate(account.data_consent_at) : '—' }}</dd></div>
              <div v-if="u.role !== 'admin'"><dt>Onboarding</dt><dd :class="{ muted: !account.onboarding_completed_at }">{{ account.onboarding_completed_at ? shortDate(account.onboarding_completed_at) : 'Not finished' }}</dd></div>
            </dl>
            <p class="nm-hint" style="margin-top: 12px">Passwords are stored encrypted (hashed) and can't be viewed by anyone — use “Send password reset” instead.</p>
          </div>

          <div class="nm-panel">
            <h2 class="nm-panel-title">Admin history</h2>
            <p v-if="!data.recent_activity.length" class="nm-muted" style="margin-top: 12px">Nothing recorded yet.</p>
            <div v-else style="margin-top: 12px">
              <div v-for="(a, i) in data.recent_activity" :key="i" class="nm-row">
                <div class="nm-row-main">
                  <p class="nm-row-title">{{ auditLabel(a.action) }}</p>
                  <p class="nm-row-sub">{{ dateTime(a.created_at) }}<span v-if="a.by"> · by {{ a.by }}</span></p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- deactivate -->
    <div v-if="showDeactivate" class="nm-modal-overlay" @click.self="showDeactivate = false">
      <div class="nm-modal">
        <h3 class="nm-modal-title">Deactivate {{ u.first_name }}'s account?</h3>
        <p class="nm-modal-text">
          They'll be signed out and won't be able to sign in. We'll email them the reason below. You can reactivate the account any time.
        </p>
        <label class="nm-label" for="deactivate-reason">Reason</label>
        <textarea id="deactivate-reason" v-model="reason" class="nm-input" rows="4" maxlength="1000"
          placeholder="e.g. Repeated no-shows and abusive messages to an RND." />
        <p v-if="reasonError" class="nm-field-error">{{ reasonError }}</p>
        <p v-else class="nm-hint">At least 10 characters — the user will see this.</p>
        <div class="nm-modal-actions">
          <button class="nm-btn-outline" @click="showDeactivate = false">Cancel</button>
          <button class="nm-btn-danger solid" :disabled="busy" @click="deactivate">{{ busy ? 'Deactivating…' : 'Deactivate account' }}</button>
        </div>
      </div>
    </div>

    <!-- edit details -->
    <div v-if="showEdit" class="nm-modal-overlay" @click.self="showEdit = false">
      <form class="nm-modal edit-modal" @submit.prevent="saveEdit">
        <h3 class="nm-modal-title">Edit {{ u.first_name }}'s details</h3>
        <p class="nm-modal-text">For correcting mistakes. The change is saved in the audit log and the user is emailed what changed{{ editForm.email !== u.email ? ' (at both the old and new email)' : '' }}.</p>
        <div class="edit-grid">
          <label class="edit-field"><span class="nm-label">First name</span>
            <input v-model="editForm.first_name" class="nm-input" maxlength="150" :class="{ invalid: editErrors.first_name }" />
            <small v-if="editErrors.first_name" class="nm-field-error">{{ editErrors.first_name }}</small></label>
          <label class="edit-field"><span class="nm-label">Last name</span>
            <input v-model="editForm.last_name" class="nm-input" maxlength="150" :class="{ invalid: editErrors.last_name }" />
            <small v-if="editErrors.last_name" class="nm-field-error">{{ editErrors.last_name }}</small></label>
          <label class="edit-field"><span class="nm-label">Email</span>
            <input v-model="editForm.email" type="email" class="nm-input" maxlength="254" :class="{ invalid: editErrors.email }" />
            <small v-if="editErrors.email" class="nm-field-error">{{ editErrors.email }}</small></label>
          <label class="edit-field"><span class="nm-label">Phone</span>
            <input v-model="editForm.phone" type="tel" class="nm-input" maxlength="20" placeholder="0917 123 4567" :class="{ invalid: editErrors.phone }" />
            <small v-if="editErrors.phone" class="nm-field-error">{{ editErrors.phone }}</small></label>
          <template v-if="rnd">
            <label class="edit-field"><span class="nm-label">PRC license no.</span>
              <input v-model="editForm.prc_license_number" class="nm-input" inputmode="numeric" maxlength="7" placeholder="7 digits" :class="{ invalid: editErrors.prc_license_number }" />
              <small v-if="editErrors.prc_license_number" class="nm-field-error">{{ editErrors.prc_license_number }}</small></label>
            <label class="edit-field"><span class="nm-label">Specialization</span>
              <select v-model="editForm.specialization" class="nm-select block" :class="{ invalid: editErrors.specialization }">
                <option v-for="sp in specializations" :key="sp" :value="sp">{{ sp }}</option>
              </select>
              <small v-if="editErrors.specialization" class="nm-field-error">{{ editErrors.specialization }}</small></label>
          </template>
        </div>
        <label class="nm-label" for="edit-reason">Reason for the change</label>
        <textarea id="edit-reason" v-model="editForm.reason" class="nm-input" rows="2" maxlength="500" placeholder="e.g. User emailed support: their last name was misspelled at sign-up." />
        <p v-if="editErrors.reason" class="nm-field-error">{{ editErrors.reason }}</p>
        <p v-else class="nm-hint">At least 10 characters — saved in the audit log and included in the email.</p>
        <p v-if="editErrors.detail" class="nm-error" style="margin-top: 10px">{{ editErrors.detail }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="showEdit = false">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="busy || !editChanged">{{ busy ? 'Saving…' : 'Save changes' }}</button>
        </div>
      </form>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { ArrowLeft, Ban, CheckCircle2, FileImage, KeyRound, Pencil, RotateCcw } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

const route = useRoute()
const auth = useAuthStore()
const { get, post, patch } = useApi()

const data = ref(null)
const loading = ref(true)
const error = ref('')
const busy = ref(false)
const toast = ref('')
const showDeactivate = ref(false)
const reason = ref('')
const reasonError = ref('')

const u = computed(() => data.value?.user || {})
const account = computed(() => data.value?.account || {})
const client = computed(() => data.value?.client)
const rnd = computed(() => data.value?.rnd)
const s = computed(() => client.value?.latest_screening)
const isSelf = computed(() => u.value.id === auth.user?.id)
const roleLabel = computed(() => ({ client: 'Client', rnd: 'RND', admin: 'Admin' }[u.value.role] || u.value.role))
const reviewLabel = computed(() => ({ pending: 'Application under review', approved: 'Approved', rejected: 'Rejected' }[rnd.value?.profile.review_status] || ''))
const reviewPill = computed(() => ({ pending: 'gold', approved: 'green', rejected: 'red' }[rnd.value?.profile.review_status] || 'muted'))
const hours = computed(() => availabilityLines(rnd.value?.availability))
const requiredMissing = computed(() => (rnd.value?.missing_setup || []).filter(m => !m.optional))
const emergencyText = computed(() => {
  const p = client.value?.profile
  if (!p?.emergency_contact) return 'Not given'
  return p.emergency_phone ? `${p.emergency_contact} · ${p.emergency_phone}` : p.emergency_contact
})
const allergyText = computed(() => {
  const a = client.value?.health.allergies
  if (a == null) return 'Not answered yet'
  return listText(a) || 'No known allergies'
})

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await get(`/admin/users/${route.params.id}/overview/`)
    useHead({ title: `${data.value.user.first_name} ${data.value.user.last_name} · NutriMatch Admin` })
  } catch (e) {
    error.value = e?.response?.status === 404 ? 'This account doesn\'t exist.' : 'Could not load this account. Please refresh.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

function flash(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3000)
}

/* ---------- edit details (PATCH /api/admin/users/<id>/edit/, accounts/admin_edit.py) ---------- */
const EDIT_FIELDS = ['first_name', 'last_name', 'email', 'phone', 'prc_license_number', 'specialization']
const showEdit = ref(false)
const editForm = reactive({ reason: '' })
const editErrors = ref({})
const specializations = ref([])
const editBefore = computed(() => ({
  first_name: u.value.first_name || '', last_name: u.value.last_name || '', email: u.value.email || '', phone: u.value.phone || '',
  ...(rnd.value ? { prc_license_number: rnd.value.profile.prc_license_number || '', specialization: rnd.value.profile.specialization || '' } : {}),
}))
const editChanged = computed(() => Object.keys(editBefore.value).some(k => String(editForm[k] ?? '').trim() !== editBefore.value[k]))
async function openEdit() {
  Object.assign(editForm, editBefore.value, { reason: '' })
  editErrors.value = {}
  showEdit.value = true
  if (rnd.value && !specializations.value.length) {
    try { specializations.value = (await get('/client/rnds/options/')).specializations || [] } catch { /* keep the current value only */ }
    if (editForm.specialization && !specializations.value.includes(editForm.specialization)) specializations.value.unshift(editForm.specialization)
  }
}
async function saveEdit() {
  editErrors.value = {}
  if (editForm.reason.trim().length < 10) {
    editErrors.value = { reason: 'Explain the change in at least 10 characters.' }
    return
  }
  const body = { reason: editForm.reason.trim() }
  for (const k of EDIT_FIELDS) {
    if (k in editBefore.value && String(editForm[k] ?? '').trim() !== editBefore.value[k]) body[k] = String(editForm[k] ?? '').trim()
  }
  busy.value = true
  try {
    await patch(`/admin/users/${u.value.id}/edit/`, body)
    showEdit.value = false
    await load()
    flash('Details updated — the user was emailed.')
  } catch (e) {
    const d = e?.data || {}
    editErrors.value = Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]))
    if (!Object.keys(editErrors.value).length) editErrors.value = { detail: apiError(e) }
  } finally {
    busy.value = false
  }
}

function openDeactivate() {
  reason.value = ''
  reasonError.value = ''
  showDeactivate.value = true
}

async function deactivate() {
  reasonError.value = ''
  if (reason.value.trim().length < 10) {
    reasonError.value = 'Explain why in at least 10 characters — the user will see this.'
    return
  }
  busy.value = true
  try {
    await post(`/admin/users/${u.value.id}/deactivate/`, { reason: reason.value.trim() })
    showDeactivate.value = false
    await load()
    flash('Account deactivated — the user was emailed.')
  } catch (e) {
    reasonError.value = apiError(e)
  } finally {
    busy.value = false
  }
}

async function reactivate() {
  busy.value = true
  error.value = ''
  try {
    await post(`/admin/users/${u.value.id}/reactivate/`)
    await load()
    flash('Account reactivated — the user was emailed.')
  } catch (e) {
    error.value = apiError(e)
  } finally {
    busy.value = false
  }
}

async function sendReset() {
  busy.value = true
  error.value = ''
  try {
    await post(`/admin/users/${u.value.id}/send-password-reset/`)
    await load()
    flash(`Password reset code sent to ${u.value.email}.`)
  } catch (e) {
    error.value = apiError(e)
  } finally {
    busy.value = false
  }
}

function cap(v) {
  if (!v) return ''
  const t = String(v).replace(/_/g, ' ')
  return t.charAt(0).toUpperCase() + t.slice(1)
}
function listText(v) {
  return Array.isArray(v) ? v.filter(Boolean).join(', ') : (v || '')
}
function num(v) {
  return v == null ? '—' : Number(v).toLocaleString('en-PH', { maximumFractionDigits: 1 })
}
function dobText(dob) {
  return dob ? `${shortDate(dob)} (${ageFrom(dob)} yrs)` : 'Not given'
}
function countText(counts) {
  const entries = Object.entries(counts || {})
  if (!entries.length) return 'None yet'
  return entries.map(([k, n]) => `${n} ${cap(k).toLowerCase()}`).join(' · ')
}
</script>

<style scoped>
.back-link { display: inline-flex; align-items: center; gap: 6px; margin-bottom: 16px; }
.identity { display: flex; align-items: center; justify-content: space-between; gap: 18px; flex-wrap: wrap; margin-bottom: 20px; }
.identity-main { display: flex; align-items: center; gap: 16px; min-width: 0; }
.identity-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.pill-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.license { display: block; margin-top: 16px; border: 1px solid #eceeec; border-radius: 10px; overflow: hidden; text-decoration: none; }
.license img { display: block; width: 100%; max-height: 260px; object-fit: contain; background: #f7f9f7; }
.license span { display: flex; align-items: center; gap: 6px; padding: 10px 12px; font-size: 0.8rem; font-weight: 600; color: #1f8f5c; border-top: 1px solid #eceeec; }
.bio { font-size: 0.86rem; color: #4a5a4a; line-height: 1.6; margin: 12px 0 0; white-space: pre-line; }
.hours-line { font-size: 0.85rem; color: #2a3a2a; margin: 0 0 4px; }
.mono { font-variant-numeric: tabular-nums; letter-spacing: 0.02em; }
.link { text-decoration: none; }
.link:hover { text-decoration: underline; }
@media (max-width: 640px) {
  .identity-main { align-items: flex-start; }
  .identity-actions { width: 100%; }
  .identity-actions > * { flex: 1; }
}
.edit-modal { max-width: 560px; }
.edit-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.edit-field { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.edit-field .nm-label { margin: 0; }
.edit-field input.nm-input { min-height: 42px; }
.edit-field .nm-input.invalid { border-color: #e0a3a3; background: #fffafa; }
@media (max-width: 560px) { .edit-grid { grid-template-columns: minmax(0, 1fr); } }
</style>
