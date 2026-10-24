<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-toolbar">
      <div class="nm-tabs">
        <button v-for="t in tabs" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" @click="tab = t.key">
          {{ t.label }} <span class="nm-count">{{ countOf(t.key) }}</span>
        </button>
      </div>
      <div class="nm-search">
        <Search :size="15" />
        <input v-model="search" type="search" placeholder="Search name, email or PRC no." />
      </div>
    </div>

    <p v-if="!loading && tab === 'pending' && unfinishedCount" class="nm-note plain-note unfinished-note">{{ unfinishedNote }}</p>
    <p v-if="loading" class="nm-muted">Loading applications…</p>

    <!-- TO REVIEW: short list + review panel -->
    <template v-else-if="tab === 'pending'">
      <div v-if="!filtered.length" class="nm-panel nm-empty">
        <ShieldCheck :size="28" />
        <p>{{ search ? 'No applications match your search.' : 'No applications waiting for review.' }}</p>
      </div>

      <div v-else class="review-layout">
        <!-- list -->
        <div class="nm-panel queue">
          <p class="queue-hint">Oldest first</p>
          <button
            v-for="r in filtered"
            :key="r.id"
            class="queue-item"
            :class="{ active: selected?.id === r.id }"
            @click="select(r.id)"
          >
            <img v-if="r.profile_photo" :src="r.profile_photo" class="nm-avatar" alt="" />
            <span v-else class="nm-avatar">{{ userInitials(r.first_name, r.last_name) }}</span>
            <span class="queue-main">
              <span class="queue-name">{{ r.first_name }} {{ r.last_name }}</span>
              <span class="queue-sub">{{ r.specialization }}</span>
            </span>
            <span class="queue-end">
              <span class="queue-date">{{ shortDate(r.submitted_at) }}</span>
              <span class="queue-email" :class="r.email_verified_at ? 'ok' : 'no'">
                <component :is="r.email_verified_at ? MailCheck : MailX" :size="12" />
                {{ r.email_verified_at ? 'Email verified' : 'Email not verified' }}
              </span>
            </span>
            <ChevronRight :size="16" class="queue-chevron" />
          </button>
        </div>

        <!-- review panel (a full-screen sheet on phones) -->
        <div v-if="selected" ref="reviewWrap" class="review-wrap">
          <div ref="reviewPanel" class="nm-panel review">
            <button class="back-btn" @click="selectedId = null"><ArrowLeft :size="15" /> All applications</button>

            <div class="review-head">
              <img v-if="selected.profile_photo" :src="selected.profile_photo" class="nm-avatar lg" alt="" />
              <span v-else class="nm-avatar lg">{{ userInitials(selected.first_name, selected.last_name) }}</span>
              <div style="min-width: 0; flex: 1">
                <h2 class="nm-panel-title review-name">{{ selected.first_name }} {{ selected.last_name }}</h2>
                <p class="nm-panel-sub">{{ selected.specialization }} · Applied {{ shortDate(selected.submitted_at) }}</p>
              </div>
              <span class="nm-pill gold">Under review</span>
            </div>

            <p v-if="!selected.email_verified_at" class="nm-note" style="margin: 16px 0 0">
              Waiting for the applicant to verify their email — you can approve once they have.
            </p>

            <p v-if="incomplete.length" class="nm-error" style="margin: 16px 0 0">
              This application is incomplete: {{ incomplete.join(', ') }}. Approve it only if that's fine — they won't appear in Find an RND until it's added.
            </p>

            <!-- the license first: it's the main thing to check -->
            <p class="nm-section-title">PRC license</p>
            <div class="license-row">
              <a v-if="selected.prc_license_image_url" :href="selected.prc_license_image_url" target="_blank" rel="noopener" class="license" title="Open full size">
                <img :src="selected.prc_license_image_url" alt="PRC license photo" />
                <span><Maximize2 :size="13" /> Open full size</span>
              </a>
              <div v-else class="license license-missing">No license photo on file</div>
              <dl class="nm-dl license-facts">
                <div><dt>PRC license no.</dt><dd class="mono">{{ selected.prc_license_number || '—' }}</dd></div>
                <div><dt>Name on application</dt><dd>{{ selected.first_name }} {{ selected.last_name }}</dd></div>
                <div><dt>Date of birth</dt><dd>{{ shortDate(selected.date_of_birth) }}<template v-if="selected.date_of_birth"> ({{ ageFrom(selected.date_of_birth) }} yrs)</template></dd></div>
                <div><dt>Email</dt><dd>{{ selected.email }}</dd></div>
                <div><dt>Mobile</dt><dd>{{ formatPhone(selected.phone) || '—' }}</dd></div>
              </dl>
            </div>

            <p class="nm-section-title">Practice</p>
            <dl class="nm-dl">
              <div><dt>Fee</dt><dd>{{ peso(selected.consultation_fee) }}</dd></div>
              <div><dt>Formats</dt><dd>{{ (selected.consultation_modes || []).map(m => MODE_LABELS[m] || m).join(', ') || '—' }}</dd></div>
              <div v-if="(selected.consultation_modes || []).includes('in_person')"><dt>Clinic address</dt><dd :class="{ muted: !selected.clinic_address }">{{ selected.clinic_address || 'Not given' }}</dd></div>
              <div><dt>Languages</dt><dd>{{ (selected.languages || []).join(', ') || '—' }}</dd></div>
              <div>
                <dt>Weekly hours</dt>
                <dd>
                  <span v-if="!hours.length" class="nm-muted">Added after approval</span>
                  <span v-for="line in hours" :key="line" class="hours-line">{{ line }}</span>
                </dd>
              </div>
            </dl>
            <p class="nm-section-title">Professional bio</p>
            <p class="bio">{{ selected.bio || '—' }}</p>

            <!-- reviewer checklist (a reminder; not saved) -->
            <div class="checklist">
              <p class="checklist-title">Before approving</p>
              <label v-for="c in CHECKS" :key="c.key" class="check">
                <input v-model="checks[c.key]" type="checkbox" />
                <span>{{ c.label }}</span>
              </label>
              <a href="https://verification.prc.gov.ph/" target="_blank" rel="noopener" class="nm-panel-link prc-link">
                Open PRC license verification <ExternalLink :size="12" />
              </a>
            </div>

            <div class="review-actions">
              <span class="review-pos">{{ position }} of {{ filtered.length }}</span>
              <button class="nm-btn-danger" :disabled="busy" @click="openReject"><X :size="14" /> Reject</button>
              <button class="nm-btn-dark" :disabled="busy || !canApprove" :title="approveHint" @click="approve">
                <Check :size="14" /> {{ busy ? 'Approving…' : filtered.length > 1 ? 'Approve → next' : 'Approve' }}
              </button>
            </div>
            <p v-if="approveHint" class="nm-hint" style="text-align: right">{{ approveHint }}</p>
          </div>
        </div>
        <div v-else class="nm-panel review-placeholder">
          <ShieldCheck :size="28" />
          <p>Select an application to review it.</p>
        </div>
      </div>
    </template>

    <!-- APPROVED / REJECTED / DEACTIVATED -->
    <div v-else class="nm-panel">
      <div v-if="!filtered.length" class="nm-empty">
        <ShieldCheck :size="28" />
        <p>{{ search ? 'No RNDs match your search.' : `No ${tabs.find(t => t.key === tab).label.toLowerCase()} RNDs.` }}</p>
      </div>
      <div v-else class="nm-table-wrap">
        <table class="nm-table stack">
          <thead>
            <tr>
              <th>RND</th>
              <th>PRC no.</th>
              <th v-if="tab === 'approved'">Approved</th>
              <th v-if="tab === 'approved'" class="nm-num">Patients</th>
              <th v-if="tab === 'approved'">Rating</th>
              <th v-if="tab === 'rejected'">Reason sent</th>
              <th v-if="tab === 'inactive'">Was</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in filtered" :key="r.id" class="clickable" @click="navigateTo(`/users/${r.id}`)">
              <td>
                <div style="display: flex; align-items: center; gap: 10px; min-width: 0">
                  <img v-if="r.profile_photo" :src="r.profile_photo" class="nm-avatar" alt="" />
                  <span v-else class="nm-avatar">{{ userInitials(r.first_name, r.last_name) }}</span>
                  <div style="min-width: 0">
                    <p class="nm-row-title">{{ r.first_name }} {{ r.last_name }}</p>
                    <p class="nm-row-sub">{{ r.specialization }}</p>
                  </div>
                </div>
              </td>
              <td data-label="PRC no." class="mono">{{ r.prc_license_number || '—' }}</td>
              <td v-if="tab === 'approved'" data-label="Approved">{{ shortDate(r.verified_at) }}</td>
              <td v-if="tab === 'approved'" data-label="Patients" class="nm-num">{{ r.patients }}</td>
              <td v-if="tab === 'approved'" data-label="Rating">{{ r.average_rating ? `★ ${r.average_rating}` : '—' }}</td>
              <td v-if="tab === 'rejected'" data-label="Reason sent">
                <span class="reason">{{ r.rejection_reason || '—' }}</span>
                <span class="nm-row-sub" style="display: block">{{ shortDate(r.reviewed_at) }} · can re-apply with the same email</span>
              </td>
              <td v-if="tab === 'inactive'" data-label="Was">{{ r.is_verified ? 'Approved RND' : 'Applicant' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- reject modal -->
    <div v-if="rejecting" class="nm-modal-overlay" @click.self="busy ? null : (rejecting = false)">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="reject-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="busy ? null : (rejecting = false)"><X :size="18" aria-hidden="true" /></button>
        <h3 id="reject-title" class="nm-modal-title">Reject {{ selected.first_name }} {{ selected.last_name }}'s application?</h3>
        <p class="nm-modal-text">We'll email them this reason. They can fix it and apply again with the same email.</p>
        <div class="reason-chips">
          <button v-for="q in QUICK_REASONS" :key="q" type="button" class="reason-chip" @click="rejectReason = q">{{ q }}</button>
        </div>
        <label class="nm-label" for="reject-reason">Reason</label>
        <textarea id="reject-reason" v-model="rejectReason" class="nm-input" rows="4" maxlength="1000"
          placeholder="e.g. The PRC license photo is blurry — please upload a clearer photo of the front of your ID." />
        <p v-if="rejectError" class="nm-field-error">{{ rejectError }}</p>
        <p v-else class="nm-hint">At least 10 characters — the applicant will see this.</p>
        <div class="nm-modal-actions">
          <button class="nm-btn-outline" :disabled="busy" @click="rejecting = false">Cancel</button>
          <button class="nm-btn-danger solid" :disabled="busy" @click="confirmReject">
            {{ busy ? 'Sending…' : 'Reject & email applicant' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import {
  ArrowLeft, Check, CheckCircle2, ChevronRight, ExternalLink, MailCheck, MailX, Maximize2, Search, ShieldCheck, X,
} from 'lucide-vue-next'
import { formatPhone } from '~/utils/phone'

const { get, patch } = useApi()
const route = useRoute()

const tabs = [
  { key: 'pending', label: 'To review' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
  { key: 'inactive', label: 'Deactivated' },
]
const CHECKS = [
  { key: 'name', label: 'The name matches the PRC license' },
  { key: 'number', label: 'The PRC license number is valid on the PRC website' },
  { key: 'photo', label: 'The license photo is clear and not expired' },
]
const QUICK_REASONS = [
  'The PRC license photo is blurry — please upload a clearer photo of the front of your license.',
  "The name on your application doesn't match the name on your PRC license.",
  "We couldn't verify your PRC license number on the PRC website — please check it and apply again.",
  'Your PRC license appears to be expired — please renew it and apply again.',
]

const loading = ref(true)
const error = ref('')
const rnds = ref([])
const search = ref('')
const tab = ref('pending')
const busy = ref(false)
const toast = ref('')
const selectedId = ref(null)
const checks = reactive({ name: false, number: false, photo: false })

// review_status comes from the RND's application (pending → approved /
// rejected); a deactivated account is listed separately.
// An applicant who never confirmed their email is an unfinished sign-up: it
// can't be approved, and signing up again replaces it, so it isn't listed.
function statusOf(r) {
  if (!r.is_active) return 'inactive'
  if (r.review_status === 'rejected') return 'rejected'
  if (r.is_verified) return 'approved'
  return r.email_verified_at ? 'pending' : 'unfinished'
}
const unfinishedCount = computed(() => countOf('unfinished'))
const unfinishedNote = computed(() => (unfinishedCount.value === 1
  ? "1 sign-up hasn't confirmed its email yet, so it isn't listed. It shows here once confirmed."
  : `${unfinishedCount.value} sign-ups haven't confirmed their email yet, so they aren't listed. They show here once confirmed.`))
const countOf = key => rnds.value.filter(r => statusOf(r) === key).length

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return rnds.value
    .filter(r => statusOf(r) === tab.value)
    .filter(r => !q || `${r.first_name} ${r.last_name} ${r.email} ${r.prc_license_number || ''}`.toLowerCase().includes(q))
    .sort((a, b) => (tab.value === 'pending' ? new Date(a.submitted_at) - new Date(b.submitted_at) : 0))
})

const selected = computed(() => (tab.value === 'pending' ? filtered.value.find(r => r.id === selectedId.value) : null) || null)
const position = computed(() => filtered.value.findIndex(r => r.id === selectedId.value) + 1)
const hours = computed(() => availabilityLines(selected.value?.availability))
// Applications from before the 5-step form (2026-10-10) may lack these.
const incomplete = computed(() => {
  const r = selected.value
  if (!r) return []
  const missing = []
  if (!r.prc_license_image_url) missing.push('no PRC license photo')
  if (!r.prc_license_number) missing.push('no PRC license number')
  if (Number(r.consultation_fee || 0) < 100) missing.push('no consultation fee')
  if (!(r.bio || '').trim()) missing.push('no bio')
  return missing
})
const allChecked = computed(() => CHECKS.every(c => checks[c.key]))
const canApprove = computed(() => !!selected.value?.email_verified_at && allChecked.value)
const approveHint = computed(() => {
  if (!selected.value) return ''
  if (!selected.value.email_verified_at) return 'Waiting for the applicant to verify their email.'
  if (!allChecked.value) return 'Tick the checklist to approve.'
  return ''
})

function isWide() {
  return import.meta.client && window.matchMedia('(min-width: 1000px)').matches
}

const reviewWrap = ref(null)
const reviewPanel = ref(null)
function select(id) {
  selectedId.value = id
  for (const c of CHECKS) checks[c.key] = false
  // start each application at the top (the sheet on phones, the page on desktop)
  nextTick(() => {
    if (reviewWrap.value) reviewWrap.value.scrollTop = 0
    if (isWide() && reviewPanel.value && reviewPanel.value.getBoundingClientRect().top < 0) {
      reviewPanel.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  })
}

// Keep ?open=<id> in the address so a link opens one application.
watch(selectedId, (id) => {
  const query = { ...route.query }
  if (id) query.open = String(id)
  else delete query.open
  navigateTo({ query }, { replace: true })
})

async function loadRnds({ quiet = false } = {}) {
  try {
    rnds.value = await get('/admin/rnds/')
  } catch {
    if (!quiet) error.value = 'Could not load RND applications. Please refresh the page.'
  } finally {
    loading.value = false
  }
}
// new applications show without a reload (the open one stays open)
useAutoRefresh(() => loadRnds({ quiet: true }))

onMounted(async () => {
  await loadRnds()
  const wanted = Number(route.query.open)
  if (wanted && rnds.value.some(r => r.id === wanted && statusOf(r) === 'pending')) select(wanted)
  else if (isWide() && filtered.value.length) select(filtered.value[0].id)
})

// On desktop there's always an application open while the list has any.
watch(filtered, (list) => {
  if (tab.value !== 'pending') return
  if (selectedId.value && !list.some(r => r.id === selectedId.value)) selectedId.value = null
  if (!selectedId.value && isWide() && list.length) select(list[0].id)
})

function flash(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3000)
}

// After a decision, open the application that was below it (or the first).
function goNext(doneId) {
  const list = filtered.value
  const idx = list.findIndex(r => r.id === doneId)
  const rest = list.filter(r => r.id !== doneId)
  const next = rest[Math.min(idx, rest.length - 1)]
  return () => (next ? select(next.id) : (selectedId.value = null))
}

async function approve() {
  const r = selected.value
  if (!r || !canApprove.value) return
  busy.value = true
  error.value = ''
  const next = goNext(r.id)
  try {
    await patch(`/admin/users/${r.id}/verify-rnd/`)
    Object.assign(r, { is_verified: true, review_status: 'approved', verified_at: new Date().toISOString() })
    next()
    flash(`${r.first_name} is approved — we emailed them.`)
  } catch (e) {
    error.value = apiError(e, 'Could not approve this RND. Please try again.')
  } finally {
    busy.value = false
  }
}

// Reject = decline the application with a reason; the applicant is emailed
// the reason and can apply again with the same email.
const rejecting = ref(false)
const rejectReason = ref('')
const rejectError = ref('')
function openReject() {
  rejectReason.value = ''
  rejectError.value = ''
  rejecting.value = true
}
async function confirmReject() {
  const r = selected.value
  if (rejectReason.value.trim().length < 10) {
    rejectError.value = 'Explain why in at least 10 characters — the applicant will see this.'
    return
  }
  busy.value = true
  rejectError.value = ''
  const next = goNext(r.id)
  try {
    await patch(`/admin/users/${r.id}/reject-rnd/`, { reason: rejectReason.value.trim() })
    Object.assign(r, { review_status: 'rejected', rejection_reason: rejectReason.value.trim(), reviewed_at: new Date().toISOString() })
    rejecting.value = false
    next()
    flash('Application rejected — the reason was emailed.')
  } catch (e) {
    rejectError.value = apiError(e, 'Could not reject this application. Please try again.')
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.unfinished-note { margin: 0 0 14px; }
.review-layout { display: grid; grid-template-columns: minmax(280px, 360px) 1fr; gap: 20px; align-items: start; }

/* queue */
.queue { padding: 10px; position: sticky; top: 16px; }
.queue-hint { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #9aaa9a; margin: 6px 10px 8px; }
.queue-item {
  display: flex; align-items: center; gap: 10px; width: 100%; text-align: left; background: none; border: 1px solid transparent;
  border-radius: 10px; padding: 10px; cursor: pointer; font-family: inherit; color: inherit;
}
.queue-item + .queue-item { margin-top: 2px; }
.queue-item:hover { background: #f7f9f7; }
.queue-item.active { background: #eef3ec; border-color: #d3e2d6; }
.queue-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.queue-name { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-sub { font-size: 0.75rem; color: #8a9a8a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-end { display: flex; flex-direction: column; align-items: flex-end; gap: 3px; flex-shrink: 0; }
.queue-date { font-size: 0.72rem; color: #8a9a8a; }
.queue-email { display: inline-flex; align-items: center; gap: 3px; font-size: 0.66rem; font-weight: 600; }
.queue-email.ok { color: #1f8f5c; }
.queue-email.no { color: #b8860b; }
.queue-chevron { color: #c5d0c5; flex-shrink: 0; display: none; }

/* review panel */
.review-head { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.review-name { font-size: 1.25rem; }
.back-btn { display: none; align-items: center; gap: 6px; background: none; border: none; color: #1f8f5c; font-weight: 600; font-size: 0.84rem; padding: 0; margin-bottom: 14px; cursor: pointer; font-family: inherit; }
.license-row { display: grid; grid-template-columns: 1.1fr 1fr; gap: 18px; align-items: start; }
.license { display: block; border: 1px solid #eceeec; border-radius: 10px; overflow: hidden; text-decoration: none; }
.license img { display: block; width: 100%; max-height: 300px; object-fit: contain; background: #f7f9f7; }
.license span { display: flex; align-items: center; gap: 6px; padding: 9px 12px; font-size: 0.78rem; font-weight: 600; color: #1f8f5c; border-top: 1px solid #eceeec; }
.license-missing { padding: 40px 16px; text-align: center; color: #a12525; background: #fdecec; font-size: 0.84rem; font-weight: 600; }
.license-facts { grid-template-columns: 1fr; }
.license-facts > div:nth-child(2) { border-top: 1px solid #f0f2f0; padding-top: 11px; }
.hours-line { display: block; font-size: 0.85rem; }
.bio { font-size: 0.86rem; color: #4a5a4a; line-height: 1.6; margin: 0; white-space: pre-line; }
.mono { font-variant-numeric: tabular-nums; letter-spacing: 0.02em; }
.reason { font-size: 0.84rem; color: #2a3a2a; }

.checklist { margin-top: 20px; background: #fafbfa; border: 1px solid #eceeec; border-radius: 12px; padding: 14px 16px; }
.checklist-title { font-size: 0.8rem; font-weight: 700; color: #1a3a1a; margin: 0 0 8px; }
.check { display: flex; align-items: flex-start; gap: 10px; font-size: 0.85rem; color: #2a3a2a; padding: 5px 0; cursor: pointer; }
.check input { width: 16px; height: 16px; margin-top: 2px; accent-color: #163a1c; flex-shrink: 0; }
.prc-link { display: inline-flex; align-items: center; gap: 4px; margin-top: 6px; }

.review-actions { display: flex; align-items: center; justify-content: flex-end; gap: 10px; margin-top: 18px; padding-top: 16px; border-top: 1px solid #f0f2f0; }
.review-pos { margin-right: auto; font-size: 0.78rem; color: #8a9a8a; }
.review-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: #9aaa9a; min-height: 300px; font-size: 0.86rem; }
.review-placeholder p { margin: 0; }

.reason-chips { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.reason-chip { text-align: left; background: #f7f9f7; border: 1px solid #e3e8e3; border-radius: 8px; padding: 8px 10px; font-size: 0.78rem; color: #2a3a2a; cursor: pointer; font-family: inherit; line-height: 1.4; }
.reason-chip:hover { border-color: #1a3a1a; }

/* below 1000px: just the list; an application opens as a full-screen sheet */
@media (max-width: 999px) {
  .review-layout { grid-template-columns: 1fr; }
  .queue { position: static; }
  .queue-chevron { display: block; }
  .queue-item.active { background: none; border-color: transparent; }
  .review-placeholder { display: none; }
  .review-wrap { position: fixed; inset: 0; z-index: 250; background: #f4f5f3; overflow-y: auto; padding: 16px; }
  .review { min-height: 100%; }
  .back-btn { display: inline-flex; }
}
@media (max-width: 640px) {
  .license-row { grid-template-columns: 1fr; }
  .review-actions { flex-wrap: wrap; }
  .review-pos { width: 100%; text-align: center; margin: 0 0 4px; }
  .review-actions > button { flex: 1; }
}
</style>
