<template>
  <div class="nm-page">
    <NuxtLink :to="backTo" class="nm-panel-link back-link"><ArrowLeft :size="14" /> {{ backLabel }}</NuxtLink>

    <p v-if="error" class="nm-error">{{ error }}</p>
    <p v-if="loading" class="nm-muted">Loading account…</p>

    <template v-else-if="data">
      <!-- ACCOUNT FILE (2026-10-25): who they are and the account's state at the
           top, real information below, anything missing in one grey line. -->
      <section class="nm-panel file-head">
        <div class="fh-top">
          <div class="identity-main">
            <img v-if="u.profile_photo" :src="u.profile_photo" class="nm-avatar lg" alt="" />
            <span v-else class="nm-avatar lg">{{ userInitials(u.first_name, u.last_name) }}</span>
            <div style="min-width: 0">
              <h1 class="nm-page-title" style="margin: 0">{{ u.first_name }} {{ u.last_name }}</h1>
              <p class="nm-page-sub">{{ u.email }}<template v-if="u.phone">, {{ formatPhone(u.phone) }}</template></p>
              <div class="pill-row">
                <span class="nm-pill muted">{{ roleLabel }}</span>
                <span class="nm-pill" :class="account.is_active ? 'green' : 'muted'">{{ account.is_active ? 'Active' : 'Deactivated' }}</span>
                <span v-if="rnd" class="nm-pill" :class="reviewPill">{{ reviewLabel }}</span>
              </div>
            </div>
          </div>
          <div v-if="!isSelf" class="identity-actions">
            <button type="button" class="nm-btn-soft" :disabled="busy" @click="openEdit"><Pencil :size="14" aria-hidden="true" /> Edit details</button>
            <button type="button" class="nm-btn-soft" :disabled="busy" @click="sendReset"><KeyRound :size="14" aria-hidden="true" /> Send password reset</button>
            <button v-if="account.is_active" type="button" class="nm-btn-danger solid" :disabled="busy" @click="openDeactivate"><Ban :size="14" aria-hidden="true" /> Deactivate</button>
            <button v-else type="button" class="nm-btn-dark" :disabled="busy" @click="reactivate"><RotateCcw :size="14" aria-hidden="true" /> Reactivate</button>
          </div>
        </div>
        <!-- the account at a glance (gold = something not done yet) -->
        <dl class="fh-strip">
          <div v-for="c in stripCells" :key="c.label" :class="{ warn: c.warn }">
            <dt>{{ c.label }}</dt><dd>{{ c.value }}</dd>
          </div>
        </dl>
        <p v-if="client" class="fh-audit"><ShieldCheck :size="14" aria-hidden="true" /> Health information. Your view was recorded in the audit log (RA 10173).</p>
      </section>

      <!-- CLIENT -->
      <div v-if="client" class="file-grid">
        <div class="file-col">
          <section class="nm-panel">
            <div class="nm-panel-head">
              <h2 class="nm-panel-title">Care</h2>
              <NuxtLink :to="`/admin-appointments?view=all&client=${u.id}`" class="nm-panel-link">Appointments</NuxtLink>
            </div>
            <p class="care-rnds">
              <template v-if="client.rnds.length">
                <span class="label">RND</span>
                <span v-for="r in client.rnds" :key="r.rnd_id" class="care-rnd">
                  <NuxtLink :to="`/users/${r.rnd_id}`" class="nm-text-link">{{ r.name }}</NuxtLink>
                  <span class="nm-pill" :class="r.status === 'active' ? 'green' : 'muted'">{{ cap(r.status) }}</span>
                </span>
              </template>
              <span v-else class="nm-muted">Hasn't booked an RND yet.</span>
            </p>
            <div class="figs four">
              <div><strong>{{ appt(client, 'pending') + appt(client, 'confirmed') }}</strong><span>Upcoming or waiting</span></div>
              <div><strong>{{ appt(client, 'completed') }}</strong><span>Completed</span></div>
              <div><strong>{{ appt(client, 'cancelled') }}</strong><span>Cancelled</span></div>
              <div><strong>{{ peso(client.invoices.paid_total) }}</strong><span>Total paid</span></div>
            </div>
          </section>

          <section class="nm-panel">
            <h2 class="nm-panel-title">Health</h2>
            <dl class="facts">
              <div v-if="listText(client.health.medical_conditions)"><dt>Conditions</dt><dd>{{ listText(client.health.medical_conditions) }}</dd></div>
              <!-- allergies are never quiet (patient safety) -->
              <div>
                <dt>Allergies</dt>
                <dd>
                  <span v-if="client.health.allergies == null" class="gap">Not answered yet</span>
                  <span v-else-if="!listText(client.health.allergies)">No known allergies</span>
                  <span v-else class="allergy-list"><span v-for="a in client.health.allergies" :key="a" class="allergy">{{ a }}</span></span>
                </dd>
              </div>
              <div v-if="listText(client.health.dietary_restrictions)"><dt>Diet</dt><dd>{{ listText(client.health.dietary_restrictions) }}</dd></div>
              <div v-if="listText(client.health.health_goals)"><dt>Goals</dt><dd>{{ listText(client.health.health_goals) }}</dd></div>
              <div v-if="client.health.religion"><dt>Religion</dt><dd>{{ client.health.religion }}</dd></div>
            </dl>
          </section>

          <section class="nm-panel">
            <h2 class="nm-panel-title">Latest screening</h2>
            <p class="nm-panel-sub">{{ s ? `Taken ${shortDate(s.created_at)}, ${client.screening_count} in total` : 'No pre-consultation screening yet.' }}</p>
            <div v-if="s" class="figs four" style="margin-top: 14px">
              <div><strong>{{ num(s.bmi) }}</strong><span>BMI<template v-if="s.bmi_category">, {{ s.bmi_category }}</template></span></div>
              <div :class="{ risk: Number(s.nrs_score) >= 3 }"><strong>{{ s.nrs_score ?? '—' }}</strong><span>NRS-2002<template v-if="s.nrs_risk">, {{ cap(s.nrs_risk).toLowerCase() }}</template></span></div>
              <div><strong>{{ num(s.weight_kg) }} kg</strong><span>{{ num(s.height_cm) }} cm tall</span></div>
              <div><strong>{{ s.tdee_kcal ? Math.round(s.tdee_kcal).toLocaleString('en-PH') : '—' }}</strong><span>kcal a day (TDEE)</span></div>
            </div>
          </section>
        </div>

        <div class="file-col">
          <section class="nm-panel">
            <h2 class="nm-panel-title">Personal</h2>
            <dl class="facts">
              <div v-if="client.profile.date_of_birth"><dt>Born</dt><dd>{{ dobText(client.profile.date_of_birth) }}</dd></div>
              <div v-if="client.profile.sex"><dt>Sex</dt><dd>{{ cap(client.profile.sex) }}</dd></div>
              <div v-if="client.profile.address"><dt>Address</dt><dd>{{ client.profile.address }}</dd></div>
              <div v-if="client.profile.emergency_contact"><dt>Emergency contact</dt><dd>{{ emergencyText }}</dd></div>
            </dl>
            <p v-if="personalMissing.length === 4" class="nm-muted" style="margin: 12px 0 0">Nothing filled in yet.</p>
          </section>
          <section class="nm-panel">
            <h2 class="nm-panel-title">Admin history</h2>
            <p v-if="!data.recent_activity.length" class="nm-muted" style="margin: 12px 0 0">Nothing recorded yet.</p>
            <ol v-else class="history">
              <li v-for="(a, i) in data.recent_activity" :key="i">
                <span class="h-title">{{ auditLabel(a.action) }}</span>
                <span class="h-time">{{ dateTime(a.created_at) }}<template v-if="a.by">, by {{ a.by }}</template></span>
              </li>
            </ol>
          </section>
        </div>
      </div>

      <!-- RND -->
      <template v-if="rnd">
        <section class="nm-panel figs-panel">
          <div class="figs six">
            <div><strong>{{ rnd.patients }}</strong><span>Active patients</span></div>
            <div><strong>{{ appt(rnd, 'completed') }}</strong><span>Consultations done</span></div>
            <div><strong>{{ rnd.rating.average ? `${rnd.rating.average} ★` : '—' }}</strong><span>{{ rnd.rating.count ? `${rnd.rating.count} review${rnd.rating.count === 1 ? '' : 's'}` : 'No reviews yet' }}</span></div>
            <div><strong>{{ peso(rnd.earnings.pending) }}</strong><span>Pending</span></div>
            <div><strong>{{ peso(rnd.earnings.posted) }}</strong><span>Posted, ready to pay</span></div>
            <div><strong>{{ peso(rnd.earnings.paid_out) }}</strong><span>Paid out, {{ rnd.payouts }} payout{{ rnd.payouts === 1 ? '' : 's' }}</span></div>
          </div>
        </section>

        <div class="file-grid">
          <div class="file-col">
            <p v-if="rnd.profile.review_status === 'rejected' && rnd.profile.rejection_reason" class="nm-note plain-note" style="margin: 0">
              <strong>Application rejected.</strong> Reason sent: {{ rnd.profile.rejection_reason }}
            </p>
            <section class="nm-panel">
              <div class="nm-panel-head">
                <h2 class="nm-panel-title">Credentials</h2>
                <NuxtLink v-if="rnd.profile.review_status === 'pending'" :to="`/rnd-verification?open=${u.id}`" class="nm-panel-link">Review application</NuxtLink>
              </div>
              <div class="cred">
                <button v-if="rnd.profile.prc_license_image_url" type="button" class="license" aria-haspopup="dialog" @click="licenseOpen = true">
                  <img :src="rnd.profile.prc_license_image_url" alt="PRC license photo" />
                  <span><Maximize2 :size="13" aria-hidden="true" /> View full size</span>
                </button>
                <div v-else class="license license-missing">No license photo on file</div>
                <dl class="facts">
                  <div><dt>PRC license no.</dt><dd class="mono">{{ rnd.profile.prc_license_number || 'Not given' }}</dd></div>
                  <div><dt>Specialization</dt><dd>{{ rnd.profile.specialization || 'Not given' }}</dd></div>
                  <div><dt>Born</dt><dd>{{ dobText(rnd.profile.date_of_birth) }}</dd></div>
                  <div><dt>Approved</dt><dd>{{ rnd.profile.verified_at ? shortDate(rnd.profile.verified_at) : 'Not yet' }}</dd></div>
                </dl>
              </div>
            </section>

            <!-- the Find an RND card, as clients see it (gaps in gold) -->
            <section class="nm-panel">
              <h2 class="nm-panel-title">What clients see</h2>
              <p v-if="requiredMissing.length" class="nm-panel-sub">Clients can't book them yet. Still to do: {{ requiredMissing.map(m => m.label.toLowerCase()).join('; ') }}.</p>
              <article class="preview">
                <p class="pv-fee">
                  <template v-if="Number(rnd.profile.consultation_fee) >= 100">{{ peso(rnd.profile.consultation_fee) }} per consultation</template>
                  <span v-else class="gap">{{ peso(rnd.profile.consultation_fee || 0) }}, below the ₱100 minimum</span>
                  <span class="nm-pill" :class="rnd.profile.available_for_new_clients ? 'green' : 'muted'">{{ rnd.profile.available_for_new_clients ? 'Taking new clients' : 'Not taking new clients' }}</span>
                </p>
                <p v-if="(rnd.profile.bio || '').trim()" class="pv-bio">{{ rnd.profile.bio }}</p>
                <span v-else class="gap">No bio yet</span>
                <div class="pv-chips">
                  <span v-for="l in rnd.languages" :key="l" class="chip">{{ String(l).replace(/ \(.*\)/, '') }}</span>
                  <span v-if="!rnd.languages.length" class="gap">No languages yet</span>
                </div>
                <div class="pv-formats">
                  <span v-for="m in rnd.profile.consultation_modes || []" :key="m" class="format"><component :is="MODE_ICONS[m] || Video" :size="13" aria-hidden="true" /> {{ MODE_LABELS[m] || m }}</span>
                </div>
                <p v-if="(rnd.profile.consultation_modes || []).includes('in_person')" class="pv-where">
                  <MapPin :size="13" aria-hidden="true" />
                  <span v-if="rnd.profile.clinic_address">{{ rnd.profile.clinic_address }}</span>
                  <span v-else class="gap">No clinic address, so in-person can't be booked</span>
                </p>
                <div class="pv-hours">
                  <CalendarClock :size="14" aria-hidden="true" />
                  <span v-if="hours.length" class="pv-hours-list"><span v-for="h in hours" :key="h">{{ h }}</span></span>
                  <span v-else>{{ rnd.profile.review_status === 'approved' ? 'No weekly hours set yet' : 'Weekly hours are added after approval' }}</span>
                </div>
              </article>
            </section>
          </div>

          <div class="file-col">
            <section class="nm-panel">
              <div class="nm-panel-head">
                <div>
                  <h2 class="nm-panel-title">Payout details</h2>
                  <p class="nm-panel-sub">Next payout {{ shortDate(rnd.earnings.next_payout_date) }}</p>
                </div>
                <NuxtLink to="/payouts" class="nm-panel-link">Payouts</NuxtLink>
              </div>
              <p v-if="!rnd.payout_account" class="nm-note" style="margin: 0">No GCash or bank details yet. Their balance is held until they add them.</p>
              <dl v-else class="facts">
                <div><dt>Method</dt><dd>{{ rnd.payout_account.method_label }}<template v-if="rnd.payout_account.bank_name">, {{ rnd.payout_account.bank_name }}</template></dd></div>
                <div><dt>Account</dt><dd>{{ rnd.payout_account.account_name }}, <span class="mono">{{ rnd.payout_account.account_number }}</span></dd></div>
                <div><dt>Last updated</dt><dd>{{ shortDate(rnd.payout_account.updated_at) }}</dd></div>
              </dl>
            </section>
            <section class="nm-panel">
              <div class="nm-panel-head">
                <h2 class="nm-panel-title">Admin history</h2>
                <NuxtLink :to="`/admin-appointments?view=all&rnd=${u.id}`" class="nm-panel-link">Appointments</NuxtLink>
              </div>
              <p v-if="!data.recent_activity.length" class="nm-muted" style="margin: 0">Nothing recorded yet.</p>
              <ol v-else class="history">
                <li v-for="(a, i) in data.recent_activity" :key="i">
                  <span class="h-title">{{ auditLabel(a.action) }}</span>
                  <span class="h-time">{{ dateTime(a.created_at) }}<template v-if="a.by">, by {{ a.by }}</template></span>
                </li>
              </ol>
            </section>
          </div>
        </div>
      </template>

      <!-- ADMIN: the header and the history -->
      <section v-if="!client && !rnd" class="nm-panel">
        <h2 class="nm-panel-title">Admin history</h2>
        <p v-if="!data.recent_activity.length" class="nm-muted" style="margin: 12px 0 0">Nothing recorded yet.</p>
        <ol v-else class="history">
          <li v-for="(a, i) in data.recent_activity" :key="i">
            <span class="h-title">{{ auditLabel(a.action) }}</span>
            <span class="h-time">{{ dateTime(a.created_at) }}<template v-if="a.by">, by {{ a.by }}</template></span>
          </li>
        </ol>
      </section>
    </template>

    <!-- deactivate -->
    <div v-if="showDeactivate" class="nm-modal-overlay" @click.self="showDeactivate = false">
      <div class="nm-modal">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="showDeactivate = false"><X :size="18" aria-hidden="true" /></button>
        <h3 class="nm-modal-title">Deactivate {{ u.first_name }}'s account?</h3>
        <p class="nm-modal-text">
          They'll be signed out and won't be able to sign in. We'll email them the reason below. You can reactivate the account any time.
        </p>
        <p v-if="rnd" class="nm-note" style="margin: 0 0 12px">
          <strong>Their patients are let go right away:</strong> every upcoming consultation is cancelled (paid ones go to the Refunds tab in Billing and Commission)
          and their care ends, so the clients can choose another RND. Reactivating doesn't bring these back.
        </p>
        <label class="nm-label" for="deactivate-reason">Reason</label>
        <textarea id="deactivate-reason" v-model="reason" class="nm-input" rows="4" maxlength="1000"
          placeholder="For example: repeated no-shows and abusive messages to an RND." />
        <p v-if="reasonError" class="nm-field-error">{{ reasonError }}</p>
        <p v-else class="nm-hint">At least 10 characters. The user will see this.</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="showDeactivate = false">Keep account</button>
          <button class="nm-btn-danger solid" :disabled="busy" @click="deactivate">{{ busy ? 'Deactivating…' : 'Deactivate account' }}</button>
        </div>
      </div>
    </div>

    <!-- edit details -->
    <div v-if="showEdit" class="nm-modal-overlay" @click.self="showEdit = false">
      <form class="nm-modal edit-modal" @submit.prevent="saveEdit">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="showEdit = false"><X :size="18" aria-hidden="true" /></button>
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
          <div class="edit-field"><label for="edit-phone" class="nm-label">Mobile number</label>
            <PhoneInput id="edit-phone" v-model="editForm.phone" label="mobile number" :rnd="!!rnd" :error="editErrors.phone" /></div>
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
        <textarea id="edit-reason" v-model="editForm.reason" class="nm-input" rows="2" maxlength="500" placeholder="For example: the user emailed support because their last name was misspelled at sign-up." />
        <p v-if="editErrors.reason" class="nm-field-error">{{ editErrors.reason }}</p>
        <p v-else class="nm-hint">At least 10 characters. It's saved in the audit log and included in the email.</p>
        <p v-if="editErrors.detail" class="nm-error" style="margin-top: 10px">{{ editErrors.detail }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="showEdit = false">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="busy || !editChanged">{{ busy ? 'Saving…' : 'Save changes' }}</button>
        </div>
      </form>
    </div>

    <!-- LICENSE PHOTO, full size (same pop-up as RND Applications) -->
    <div v-if="licenseOpen && rnd?.profile.prc_license_image_url" class="nm-modal-overlay" @click.self="licenseOpen = false">
      <div class="nm-modal license-modal" role="dialog" aria-modal="true" aria-labelledby="license-title">
        <div class="lm-head nm-modal-head">
          <span class="lm-icon"><IdCard :size="18" aria-hidden="true" /></span>
          <div style="flex: 1; min-width: 0">
            <h3 id="license-title" class="nm-modal-title" style="margin: 0">PRC license, {{ u.first_name }} {{ u.last_name }}</h3>
            <p class="nm-panel-sub">License no. {{ rnd.profile.prc_license_number || 'not given' }}</p>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="licenseOpen = false"><X :size="18" aria-hidden="true" /></button>
        </div>
        <div class="lm-photo"><img :src="rnd.profile.prc_license_image_url" alt="PRC license photo, full size" /></div>
        <div class="nm-modal-actions">
          <a :href="rnd.profile.prc_license_image_url" target="_blank" rel="noopener noreferrer" class="nm-btn-soft"><ExternalLink :size="14" aria-hidden="true" /> Open in new tab</a>
          <button type="button" class="nm-btn-dark" @click="licenseOpen = false">Done</button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import {
  ArrowLeft, Ban, CalendarClock, CheckCircle2, ExternalLink, IdCard, KeyRound, MapPin, Maximize2, Pencil, RotateCcw, ShieldCheck,
  UserRound, Video, X,
} from 'lucide-vue-next'
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
const licenseOpen = ref(false)
const MODE_ICONS = { video: Video, in_person: UserRound }

const u = computed(() => data.value?.user || {})
const account = computed(() => data.value?.account || {})
const client = computed(() => data.value?.client)
const rnd = computed(() => data.value?.rnd)
const s = computed(() => client.value?.latest_screening)
const isSelf = computed(() => u.value.id === auth.user?.id)
const roleLabel = computed(() => ({ client: 'Client', rnd: 'RND', admin: 'Admin' }[u.value.role] || u.value.role))
// Back to the list tab this user is on (Users keeps the tab in ?tab=)
const backTo = computed(() => ({ path: '/users', query: { tab: { client: 'clients', rnd: 'rnds', admin: 'admins' }[u.value.role] || 'clients' } }))
const backLabel = computed(() => ({ client: 'All clients', rnd: 'All RNDs', admin: 'All admins' }[u.value.role] || 'All users'))
const reviewLabel = computed(() => ({ pending: 'Application under review', approved: 'Approved', rejected: 'Rejected' }[rnd.value?.profile.review_status] || ''))
const reviewPill = computed(() => ({ pending: 'gold', approved: 'green', rejected: 'muted' }[rnd.value?.profile.review_status] || 'muted'))
const hours = computed(() => availabilityLines(rnd.value?.availability))
const requiredMissing = computed(() => (rnd.value?.missing_setup || []).filter(m => !m.optional))
const emergencyText = computed(() => {
  const p = client.value?.profile
  if (!p?.emergency_contact) return 'Not given'
  return p.emergency_phone ? `${p.emergency_contact}, ${formatPhone(p.emergency_phone) || p.emergency_phone}` : p.emergency_contact
})
// appointment counts by status ({ completed: 3, ... })
const appt = (who, k) => who?.appointments?.[k] || 0
// The strip under the name: the account at a glance; gold = not done yet.
const stripCells = computed(() => {
  const a = account.value
  const cells = [
    { label: 'Joined', value: shortDate(u.value.created_at) },
    { label: 'Last sign-in', value: a.last_login ? dateTime(a.last_login) : 'Never' },
    { label: 'Email', value: a.email_verified_at ? `Confirmed ${shortDate(a.email_verified_at)}` : 'Not confirmed', warn: !a.email_verified_at },
  ]
  if (client.value) cells.push({ label: 'Onboarding', value: a.onboarding_completed_at ? `Finished ${shortDate(a.onboarding_completed_at)}` : 'Not finished', warn: !a.onboarding_completed_at })
  if (rnd.value) cells.push({ label: 'Application', value: reviewLabel.value || 'Not sent', warn: rnd.value.profile.review_status === 'pending' })
  if (u.value.role !== 'admin') {
    const both = a.terms_accepted_at && a.data_consent_at
    cells.push({ label: 'Consent (RA 10173)', value: both ? `Given ${shortDate(a.data_consent_at)}` : 'Missing', warn: !both })
  }
  return cells
})
// empty fields are simply left out; this only tells when nothing is filled in
const personalMissing = computed(() => {
  const p = client.value?.profile || {}
  return [['date of birth', p.date_of_birth], ['sex', p.sex], ['address', p.address], ['emergency contact', p.emergency_contact]]
    .filter(([, v]) => !v).map(([k]) => k)
})

const allergyText = computed(() => {
  const a = client.value?.health.allergies
  if (a == null) return 'Not answered yet'
  return listText(a) || 'No known allergies'
})

async function load({ quiet = false } = {}) {
  if (!quiet) {
    loading.value = true
    error.value = ''
  }
  try {
    data.value = await get(`/admin/users/${route.params.id}/overview/`)
    useHead({ title: `${data.value.user.first_name} ${data.value.user.last_name} · NutriMatch Admin` })
  } catch (e) {
    if (!quiet) error.value = e?.response?.status === 404 ? 'This account doesn\'t exist.' : 'Could not load this account. Please refresh.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
// Refreshes every 5 minutes, but never a client's record: each load of it
// writes a "record viewed" audit row (RA 10173), which must mean a person
// looked, not a timer.
useAutoRefresh(() => load({ quiet: true }), { interval: 300000, paused: () => !data.value || data.value.user?.role === 'client' })

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
  const phoneMsg = editForm.phone === editBefore.value.phone ? ''
    : rnd.value && !editForm.phone ? 'RNDs must have a mobile number. Enter a Philippine mobile, for example +63 917 123 4567.'
    : (rnd.value ? rndPhoneError : phoneError)(editForm.phone)
  if (phoneMsg) {
    editErrors.value = { phone: phoneMsg }
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
    flash('Details updated. We emailed the user.')
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
    reasonError.value = 'Explain why in at least 10 characters. The user will see this.'
    return
  }
  busy.value = true
  try {
    const res = await post(`/admin/users/${u.value.id}/deactivate/`, { reason: reason.value.trim() })
    showDeactivate.value = false
    await load()
    const n = res?.consultations_cancelled || 0, m = res?.care_ended || 0
    flash('Account deactivated. We emailed the user.'
      + (n ? ` ${n} consultation${n === 1 ? '' : 's'} cancelled.` : '')
      + (m ? ` Care ended for ${m} client${m === 1 ? '' : 's'}.` : ''))
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
    flash('Account reactivated. We emailed the user.')
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
  return entries.map(([k, n]) => `${n} ${cap(k).toLowerCase()}`).join(', ')
}
</script>

<style scoped>
.back-link { display: inline-flex; align-items: center; gap: 6px; margin-bottom: 16px; }

/* header: identity + actions, then the account strip */
.file-head { padding: 0; overflow: hidden; margin-bottom: 20px; }
.fh-top { display: flex; align-items: center; justify-content: space-between; gap: 18px; flex-wrap: wrap; padding: 22px 22px 18px; }
.identity-main { display: flex; align-items: center; gap: 16px; min-width: 0; }
.identity-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.pill-row { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.fh-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); margin: 0; border-top: 1px solid #d9e3dc; }
.fh-strip > div { padding: 12px 18px; min-width: 0; border-left: 1px solid #d9e3dc; }
.fh-strip > div:first-child { border-left: none; }
.fh-strip dt { font-size: 0.74rem; color: #6a7a6a; }
.fh-strip dd { margin: 3px 0 0; font-size: 0.88rem; font-weight: 600; color: #1a3a1a; overflow-wrap: anywhere; }
.fh-strip .warn dd { color: #7a560f; }
.fh-audit { display: flex; align-items: center; gap: 8px; margin: 0; padding: 9px 18px; border-top: 1px solid #d9e3dc; background: #f7faf8; font-size: 0.78rem; color: #4a5a4a; }
.fh-audit svg { color: #0a4a37; flex-shrink: 0; }

/* body */
.file-grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 20px; align-items: start; }
.file-col { display: flex; flex-direction: column; gap: 20px; min-width: 0; }
.figs-panel { padding: 0; overflow: hidden; margin-bottom: 20px; }

/* divided figures, as on the dashboards */
.figs { display: grid; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; }
.figs-panel .figs { border: none; border-radius: 0; }
.figs.four { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.figs.six { grid-template-columns: repeat(6, minmax(0, 1fr)); }
.figs > div { display: flex; flex-direction: column; gap: 2px; padding: 12px 14px; min-width: 0; border-left: 1px solid #d9e3dc; }
.figs > div:first-child { border-left: none; }
.figs strong { font-family: 'Playfair Display', serif; font-size: 1.25rem; color: #1a3a1a; line-height: 1.2; font-variant-numeric: lining-nums tabular-nums; overflow-wrap: anywhere; }
.figs span { font-size: 0.74rem; color: #4a5a4a; line-height: 1.3; }
.figs .risk strong { color: #a12525; }

/* facts: label above value, only what's filled in */
.facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 18px; margin: 12px 0 0; }
.facts > div { padding: 9px 0; border-top: 1px solid #edf2ee; min-width: 0; }
.facts > div:nth-child(-n + 2) { border-top: none; }
.facts dt { font-size: 0.74rem; color: #6a7a6a; }
.facts dd { margin: 3px 0 0; font-size: 0.88rem; color: #1a3a1a; overflow-wrap: anywhere; }
.care-rnds { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 14px; margin: 0 0 14px; font-size: 0.88rem; }
.care-rnds .label { font-size: 0.74rem; color: #6a7a6a; }
.care-rnd { display: inline-flex; align-items: center; gap: 6px; }
/* allergies: red, never quiet */
.allergy-list { display: flex; flex-wrap: wrap; gap: 6px; }
.allergy { font-size: 0.78rem; font-weight: 700; color: #a12525; background: #fdecec; border: 1px solid #f3b8b8; border-radius: 999px; padding: 2px 10px; }
.gap { display: inline-block; font-size: 0.78rem; font-weight: 600; color: #7a560f; background: #fdf3dc; border-radius: 6px; padding: 2px 8px; align-self: flex-start; }

/* admin history: a short timeline */
.history { list-style: none; margin: 12px 0 0; padding: 0; }
.history li { position: relative; display: flex; flex-direction: column; gap: 2px; padding: 0 0 14px 18px; }
.history li::before { content: ''; position: absolute; left: 3px; top: 6px; width: 7px; height: 7px; border-radius: 50%; background: #3f9a6b; }
.history li::after { content: ''; position: absolute; left: 6px; top: 16px; bottom: 2px; width: 1px; background: #d9e3dc; }
.history li:last-child { padding-bottom: 0; }
.history li:last-child::after { display: none; }
.h-title { font-size: 0.84rem; font-weight: 600; color: #1a3a1a; }
.h-time { font-size: 0.76rem; color: #6a7a6a; }

/* RND credentials + the client-facing card */
.cred { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; align-items: start; }
.cred .facts { grid-template-columns: 1fr; margin: 0; }
.cred .facts > div:nth-child(2) { border-top: 1px solid #edf2ee; }
.license { display: block; width: 100%; padding: 0; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; background: #f7faf8; cursor: zoom-in; font-family: inherit; text-align: left; }
.license:hover img { opacity: 0.92; }
.license:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.license img { display: block; width: 100%; max-height: 220px; object-fit: contain; }
.license span { display: flex; align-items: center; gap: 6px; padding: 9px 12px; font-size: 0.78rem; font-weight: 600; color: #0a4a37; border-top: 1px solid #d9e3dc; background: #fff; }
.license-missing { padding: 40px 14px; text-align: center; color: #a12525; background: #fdecec; border-color: #f3b8b8; font-size: 0.82rem; font-weight: 600; cursor: default; }
.preview { display: flex; flex-direction: column; gap: 10px; margin-top: 14px; border: 1px solid #d9e3dc; border-radius: 12px; padding: 16px; overflow-wrap: anywhere; }
.pv-fee { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; font-size: 0.88rem; font-weight: 600; color: #1a3a1a; margin: 0; }
.pv-bio { font-size: 0.85rem; color: #4a5a4a; line-height: 1.55; margin: 0; white-space: pre-line; }
.pv-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { font-size: 0.76rem; font-weight: 600; background: #f2f6f3; border: 1px solid #d9e3dc; color: #4a5a4a; border-radius: 12px; padding: 2px 10px; }
.pv-formats { display: flex; flex-wrap: wrap; gap: 12px; }
.format { display: inline-flex; align-items: center; gap: 5px; font-size: 0.8rem; color: #1a3a1a; font-weight: 500; }
.format svg { color: #3f9a6b; }
.pv-where { display: flex; align-items: flex-start; gap: 6px; font-size: 0.8rem; color: #4a5a4a; margin: 0; line-height: 1.4; }
.pv-where svg { flex-shrink: 0; margin-top: 2px; }
.pv-hours { display: flex; align-items: flex-start; gap: 8px; background: #e3efe7; color: #1e4a26; border-radius: 8px; padding: 9px 12px; font-size: 0.8rem; line-height: 1.45; }
.pv-hours svg { flex-shrink: 0; margin-top: 1px; }
.pv-hours-list { display: flex; flex-direction: column; gap: 2px; }
.mono { font-variant-numeric: tabular-nums; letter-spacing: 0.02em; }

/* license pop-up */
.license-modal { max-width: 900px; }
.lm-head { display: flex; gap: 12px; align-items: flex-start; }
.lm-icon { width: 36px; height: 36px; border-radius: 9px; background: #e3efe7; color: #0a4a37; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.lm-photo { margin-top: 16px; border: 1px solid #d9e3dc; border-radius: 12px; overflow: auto; background: #f7faf8; display: flex; justify-content: center; }
.lm-photo img { display: block; max-width: 100%; max-height: 70vh; object-fit: contain; }

/* edit pop-up */
.edit-modal { max-width: 560px; }
.edit-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin-bottom: 14px; }
.edit-field { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.edit-field .nm-label { margin: 0; }
.edit-field input.nm-input { min-height: 42px; }
.edit-field .nm-input.invalid { border-color: #e0a3a3; background: #fffafa; }

@media (max-width: 1100px) {
  .figs.six { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .figs.six > div:nth-child(4) { border-left: none; }
  .figs.six > div:nth-child(n + 4) { border-top: 1px solid #d9e3dc; }
}
@media (max-width: 900px) {
  .file-grid { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 640px) {
  .fh-top { padding: 18px 16px 14px; }
  .identity-main { align-items: flex-start; }
  .identity-actions { width: 100%; }
  .identity-actions > * { flex: 1; }
  .fh-strip { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fh-strip > div { border-left: none; border-top: 1px solid #d9e3dc; }
  .fh-strip > div:nth-child(even) { border-left: 1px solid #d9e3dc; }
  .fh-strip > div:nth-child(-n + 2) { border-top: none; }
  .figs.four, .figs.six { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .figs.four > div:nth-child(odd), .figs.six > div:nth-child(odd) { border-left: none; }
  .figs.four > div:nth-child(n + 3), .figs.six > div:nth-child(n + 3) { border-top: 1px solid #d9e3dc; }
  .facts { grid-template-columns: minmax(0, 1fr); }
  .facts > div:nth-child(2) { border-top: 1px solid #edf2ee; }
  .cred { grid-template-columns: minmax(0, 1fr); }
  .license-modal { max-width: none; height: 100%; max-height: none; border-radius: 0; display: flex; flex-direction: column; }
  .lm-photo { flex: 1; align-items: center; }
}
@media (max-width: 560px) { .edit-grid { grid-template-columns: minmax(0, 1fr); } }
</style>
