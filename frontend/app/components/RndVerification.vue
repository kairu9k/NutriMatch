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
          <p class="queue-hint">{{ filtered.length }} waiting, oldest first</p>
          <button
            v-for="r in pagedList"
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
            <span class="queue-wait" :class="{ long: waitDays(r) > 3 }" :title="`Applied ${shortDate(r.submitted_at)}`">{{ waitText(r) }}</span>
            <ChevronRight :size="16" class="queue-chevron" />
          </button>
          <ListPager v-model:page="page" :pages="pages" />
        </div>

        <!-- REVIEW: a verification desk (2026-10-25). The decision bar stays at the
             top; the checklist sits beside the license photo, each tick next to the
             value it checks; then a preview of what clients will see once approved,
             with anything missing marked in gold. A full-screen sheet on phones. -->
        <div v-if="selected" ref="reviewWrap" class="review-wrap">
          <div ref="reviewPanel" class="nm-panel review">
            <button type="button" class="nm-btn-soft nm-btn-sm back-btn" @click="selectedId = null"><ArrowLeft :size="15" /> All applications</button>

            <div class="decide">
              <div class="decide-who">
                <img v-if="selected.profile_photo" :src="selected.profile_photo" class="nm-avatar lg" alt="" />
                <span v-else class="nm-avatar lg">{{ userInitials(selected.first_name, selected.last_name) }}</span>
                <div class="decide-name">
                  <h2 class="nm-panel-title">{{ selected.first_name }} {{ selected.last_name }}</h2>
                  <p class="nm-panel-sub">{{ selected.specialization }}, applied {{ shortDate(selected.submitted_at) }}</p>
                </div>
              </div>
              <div class="decide-actions">
                <span class="review-pos">{{ position }} of {{ filtered.length }}</span>
                <button type="button" class="nm-btn-danger solid" :disabled="busy" @click="openReject"><X :size="14" /> Reject</button>
                <button type="button" class="nm-btn-dark" :disabled="busy || !canApprove" @click="approve">
                  <Check :size="14" /> {{ busy ? 'Approving…' : filtered.length > 1 ? 'Approve and open next' : 'Approve' }}
                </button>
              </div>
              <p v-if="approveHint" class="decide-hint">{{ approveHint }}</p>
            </div>

            <p v-if="!selected.email_verified_at" class="nm-note plain-note review-note">
              Waiting for the applicant to confirm their email. You can approve once they have.
            </p>

            <!-- 1. the license, with the checks beside it -->
            <h3 class="desk-title">Check the license</h3>
            <div class="desk">
              <a v-if="selected.prc_license_image_url" :href="selected.prc_license_image_url" target="_blank" rel="noopener" class="license" title="Open full size">
                <img :src="selected.prc_license_image_url" alt="PRC license photo" />
                <span><Maximize2 :size="13" aria-hidden="true" /> Open full size</span>
              </a>
              <div v-else class="license license-missing">No license photo on file. The license can't be checked.</div>

              <div class="checks">
                <label class="check-row" :class="{ done: checks.name }">
                  <input v-model="checks.name" type="checkbox" />
                  <span class="check-text">
                    <span>The name matches the license</span>
                    <strong>{{ selected.first_name }} {{ selected.last_name }}</strong>
                  </span>
                </label>
                <label class="check-row" :class="{ done: checks.number }">
                  <input v-model="checks.number" type="checkbox" />
                  <span class="check-text">
                    <span>The license number is valid on the PRC website</span>
                    <strong class="mono">{{ selected.prc_license_number || 'No number given' }}</strong>
                    <a href="https://verification.prc.gov.ph/" target="_blank" rel="noopener" class="nm-panel-link prc-link" @click.stop>
                      Check on the PRC website <ExternalLink :size="12" aria-hidden="true" />
                    </a>
                  </span>
                </label>
                <label class="check-row" :class="{ done: checks.photo }">
                  <input v-model="checks.photo" type="checkbox" />
                  <span class="check-text">
                    <span>The photo is clear and the license isn't expired</span>
                    <small>Look for the expiry date on the photo.</small>
                  </span>
                </label>
              </div>
            </div>

            <!-- 2. what approving publishes -->
            <h3 class="desk-title">What clients will see once approved</h3>
            <article class="preview">
              <div class="pv-head">
                <img v-if="selected.profile_photo" :src="selected.profile_photo" class="nm-avatar lg" alt="" />
                <span v-else class="nm-avatar lg">{{ userInitials(selected.first_name, selected.last_name) }}</span>
                <div class="pv-id">
                  <p class="pv-name">{{ selected.first_name }} {{ selected.last_name }} <BadgeCheck :size="15" class="pv-verified" aria-hidden="true" /></p>
                  <p class="pv-spec">{{ selected.specialization || 'General and clinical nutrition' }}</p>
                  <p class="pv-fee">
                    <template v-if="Number(selected.consultation_fee) >= 100">{{ peso(selected.consultation_fee) }} per consultation</template>
                    <span v-else class="gap">{{ peso(selected.consultation_fee || 0) }}, below the ₱100 minimum</span>
                  </p>
                </div>
              </div>
              <p v-if="(selected.bio || '').trim()" class="pv-bio">{{ selected.bio }}</p>
              <p v-else class="gap">No bio yet</p>
              <div class="pv-chips">
                <span v-for="l in selected.languages || []" :key="l" class="chip">{{ String(l).replace(/ \(.*\)/, '') }}</span>
                <span v-if="!(selected.languages || []).length" class="gap">No languages yet</span>
              </div>
              <div class="pv-formats">
                <span v-for="m in selected.consultation_modes || []" :key="m" class="format"><component :is="MODE_ICONS[m] || Video" :size="13" aria-hidden="true" /> {{ MODE_LABELS[m] || m }}</span>
              </div>
              <p v-if="(selected.consultation_modes || []).includes('in_person')" class="pv-where">
                <MapPin :size="13" aria-hidden="true" />
                <span v-if="selected.clinic_address">{{ selected.clinic_address }}</span>
                <span v-else class="gap">No clinic address, so in-person can't be booked</span>
              </p>
              <div class="pv-hours">
                <CalendarClock :size="14" aria-hidden="true" />
                <span v-if="hours.length" class="pv-hours-list"><span v-for="h in hours" :key="h">{{ h }}</span></span>
                <span v-else>Weekly hours are added after approval</span>
              </div>
            </article>

            <!-- 3. contact details, for the admin only -->
            <h3 class="desk-title">Contact</h3>
            <dl class="contact">
              <div><dt>Email</dt><dd>{{ selected.email }}</dd></div>
              <div><dt>Mobile</dt><dd>{{ formatPhone(selected.phone) || 'None given' }}</dd></div>
              <div><dt>Date of birth</dt><dd>{{ selected.date_of_birth ? `${shortDate(selected.date_of_birth)} (${ageFrom(selected.date_of_birth)})` : 'None given' }}</dd></div>
            </dl>
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
            <tr v-for="r in pagedList" :key="r.id" class="clickable" @click="navigateTo(`/users/${r.id}`)">
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
                <span class="nm-row-sub" style="display: block">{{ shortDate(r.reviewed_at) }}, can apply again with the same email</span>
              </td>
              <td v-if="tab === 'inactive'" data-label="Was">{{ r.is_verified ? 'Approved RND' : 'Applicant' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <ListPager v-model:page="page" :pages="pages" />
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
          placeholder="For example: the PRC license photo is blurry. Please upload a clearer photo of the front of your license." />
        <p v-if="rejectError" class="nm-field-error">{{ rejectError }}</p>
        <p v-else class="nm-hint">At least 10 characters. The applicant will see this.</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" :disabled="busy" @click="rejecting = false">Keep reviewing</button>
          <button type="button" class="nm-btn-danger solid" :disabled="busy" @click="confirmReject">
            {{ busy ? 'Sending…' : 'Reject and email the applicant' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import {
  ArrowLeft, BadgeCheck, CalendarClock, Check, CheckCircle2, ChevronRight, ExternalLink, MapPin, Maximize2, Search, ShieldCheck,
  UserRound, Video, X,
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
  'The PRC license photo is blurry. Please upload a clearer photo of the front of your license.',
  "The name on your application doesn't match the name on your PRC license.",
  "We couldn't verify your PRC license number on the PRC website. Please check it and apply again.",
  'Your PRC license appears to be expired. Please renew it and apply again.',
]

const MODE_ICONS = { video: Video, in_person: UserRound }

// How long an application has waited; gold after 3 days.
const waitDays = r => Math.max(0, Math.floor((Date.now() - new Date(r.submitted_at)) / 86400000))
const waitText = (r) => {
  const d = waitDays(r)
  return d === 0 ? 'Today' : `${d} day${d === 1 ? '' : 's'}`
}

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

// 20 per page: the queue on To review, the table on the other tabs
const { page, pages, paged: pagedList } = usePager(filtered, { resetOn: () => [tab.value, search.value] })

const selected = computed(() => (tab.value === 'pending' ? filtered.value.find(r => r.id === selectedId.value) : null) || null)
const position = computed(() => filtered.value.findIndex(r => r.id === selectedId.value) + 1)
const hours = computed(() => availabilityLines(selected.value?.availability))
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
  // the queue shows the page the open application is on
  const at = filtered.value.findIndex(r => r.id === id)
  if (at >= 0) page.value = Math.floor(at / 20) + 1
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
    flash(`${r.first_name} is approved. We emailed them.`)
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
    rejectError.value = 'Explain why in at least 10 characters. The applicant will see this.'
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
    flash('Application rejected. We emailed them the reason.')
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
.queue { padding: 10px; position: sticky; top: 92px; }
.queue-hint { font-size: 0.78rem; color: #6a7a6a; margin: 6px 10px 8px; }
.queue :deep(.nm-pager) { margin: 8px 0 0; padding: 10px 0 2px; }
.queue-item {
  display: flex; align-items: center; gap: 10px; width: 100%; text-align: left; background: none; border: 1px solid transparent;
  border-radius: 10px; padding: 10px; cursor: pointer; font-family: inherit; color: inherit;
}
.queue-item + .queue-item { margin-top: 2px; }
.queue-item:hover { background: #f7f9f7; }
.queue-item.active { background: #eef3ec; border-color: #d9e3dc; }
.queue-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.queue-name { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-sub { font-size: 0.75rem; color: #8a9a8a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
/* how long it has waited; gold after 3 days */
.queue-wait { flex-shrink: 0; font-size: 0.74rem; font-weight: 600; color: #4a5a4a; background: #f2f6f3; border-radius: 999px; padding: 2px 9px; }
.queue-wait.long { background: #fdf3dc; color: #7a560f; }
.queue-chevron { color: #c5d0c5; flex-shrink: 0; display: none; }

/* review panel: the decision bar sticks under the top bar while you scroll */
.review { padding-top: 0; }
.decide {
  position: sticky; top: 75px; z-index: 3; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px 16px;
  margin: 0 -22px; padding: 18px 22px 16px; background: #fff; border-bottom: 1px solid #d9e3dc; border-radius: 14px 14px 0 0;
}
.decide-who { display: flex; align-items: center; gap: 14px; min-width: 0; }
.decide-name { min-width: 0; }
.decide-name .nm-panel-title { font-size: 1.25rem; }
.decide-actions { display: flex; align-items: center; gap: 10px; }
.review-pos { font-size: 0.78rem; color: #6a7a6a; margin-right: 4px; white-space: nowrap; }
.decide-hint { flex-basis: 100%; margin: -4px 0 0; text-align: right; font-size: 0.78rem; color: #6a7a6a; }
.back-btn { display: none; align-items: center; gap: 6px; margin: 16px 0 0; }
.review-note { margin: 16px 0 0; }
.desk-title { font-family: inherit; font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 22px 0 10px; }

/* 1. license + checks side by side */
.desk { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr); gap: 18px; align-items: start; }
.license { display: block; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; text-decoration: none; background: #f7faf8; }
.license img { display: block; width: 100%; max-height: 340px; object-fit: contain; }
.license span { display: flex; align-items: center; gap: 6px; padding: 9px 12px; font-size: 0.78rem; font-weight: 600; color: #0a4a37; border-top: 1px solid #d9e3dc; background: #fff; }
.license:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.license-missing { padding: 48px 16px; text-align: center; color: #a12525; background: #fdecec; border-color: #f3b8b8; font-size: 0.84rem; font-weight: 600; }
.checks { display: flex; flex-direction: column; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; }
.check-row { display: flex; align-items: flex-start; gap: 12px; padding: 14px 16px; cursor: pointer; background: #fff; }
.check-row + .check-row { border-top: 1px solid #d9e3dc; }
.check-row:hover { background: #f7faf8; }
.check-row.done { background: #f2f8f4; }
.check-row input { width: 18px; height: 18px; margin-top: 1px; accent-color: #0a4a37; flex-shrink: 0; cursor: pointer; }
.check-text { display: flex; flex-direction: column; gap: 3px; min-width: 0; font-size: 0.82rem; color: #4a5a4a; }
.check-text strong { font-size: 0.98rem; color: #1a3a1a; overflow-wrap: anywhere; }
.check-text small { font-size: 0.76rem; color: #6a7a6a; }
.prc-link { align-self: flex-start; display: inline-flex; align-items: center; gap: 4px; margin-top: 4px; }
.mono { font-variant-numeric: tabular-nums; letter-spacing: 0.02em; }

/* 2. the client-facing card, as on Find an RND; gaps in gold */
.preview { display: flex; flex-direction: column; gap: 10px; border: 1px solid #d9e3dc; border-radius: 14px; padding: 18px; background: #fff; overflow-wrap: anywhere; }
.pv-head { display: flex; gap: 14px; align-items: flex-start; }
.pv-id { min-width: 0; }
.pv-name { font-family: 'Playfair Display', serif; font-size: 1.12rem; font-weight: 700; color: #1a3a1a; margin: 0; display: flex; align-items: center; gap: 6px; }
.pv-verified { color: #1f8f5c; }
.pv-spec { font-size: 0.82rem; color: #4a5a4a; margin: 3px 0 0; }
.pv-fee { font-size: 0.84rem; font-weight: 600; color: #1a3a1a; margin: 4px 0 0; }
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
/* something clients would miss: a gold notice, not an error */
.gap { display: inline-block; font-size: 0.78rem; font-weight: 600; color: #7a560f; background: #fdf3dc; border-radius: 6px; padding: 2px 8px; margin: 0; align-self: flex-start; }

/* 3. contact */
.contact { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); margin: 0; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; }
.contact > div { padding: 12px 14px; min-width: 0; }
.contact > div + div { border-left: 1px solid #d9e3dc; }
.contact dt { font-size: 0.74rem; color: #6a7a6a; }
.contact dd { margin: 3px 0 0; font-size: 0.85rem; color: #1a3a1a; overflow-wrap: anywhere; }
.reason { font-size: 0.84rem; color: #2a3a2a; }

.review-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: #6a7a6a; min-height: 300px; font-size: 0.86rem; }
.review-placeholder p { margin: 0; }

.reason-chips { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
/* quick reasons: a tap fills the box (light green, like other secondary choices) */
.reason-chip { text-align: left; background: #f7faf8; border: 1px solid #d9e3dc; border-radius: 8px; padding: 8px 10px; font-size: 0.78rem; color: #1a3a1a; cursor: pointer; font-family: inherit; line-height: 1.4; }
.reason-chip:hover { background: #e3efe7; border-color: #3f9a6b; }
.reason-chip:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

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
  .decide { top: -16px; }
}
@media (max-width: 640px) {
  .desk { grid-template-columns: 1fr; }
  .decide-actions { width: 100%; flex-wrap: wrap; }
  .decide-actions > button { flex: 1; }
  .review-pos { width: 100%; }
  .decide-hint { text-align: left; }
  .contact { grid-template-columns: 1fr; }
  .contact > div + div { border-left: none; border-top: 1px solid #d9e3dc; }
}
</style>
