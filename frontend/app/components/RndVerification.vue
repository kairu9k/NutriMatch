<template>
  <div class="nm-page">
    <section class="ra-hero">
      <img class="ra-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="ra-fade" aria-hidden="true"></span>
      <div class="ra-hero-txt">
        <p class="ra-eyebrow"><span aria-hidden="true"></span>RND applications</p>
        <h2 class="ra-title">Review new RNDs</h2>
        <p class="ra-sub">Check each license and selfie before an RND can be booked by clients. Oldest first.</p>
      </div>
    </section>

    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-toolbar ra-toolbar">
      <div class="nm-tabs ra-tabs">
        <button v-for="t in tabs" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" @click="tab = t.key">
          <svg v-if="t.key === 'pending'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg><svg v-else-if="t.key === 'approved'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg><svg v-else-if="t.key === 'rejected'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg><svg v-else class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M5.6 5.6l12.8 12.8" /></svg>
          {{ t.label }} <span class="nm-count">{{ countOf(t.key) }}</span>
        </button>
      </div>
      <div class="nm-search ra-search">
        <Search :size="17" />
        <input v-model="search" type="search" placeholder="Search name, email or PRC no." />
      </div>
    </div>

    <p v-if="!loading && tab === 'pending' && unfinishedCount" class="nm-note plain-note unfinished-note"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg> {{ unfinishedNote }}</p>
    <p v-if="loading" class="nm-muted ra-loading"><span class="ra-spin" aria-hidden="true"></span> Loading applications…</p>

    <!-- TO REVIEW: short list + review panel -->
    <template v-else-if="tab === 'pending'">
      <div v-if="!filtered.length" class="nm-panel nm-empty">
        <ShieldCheck :size="28" />
        <p>{{ search ? 'No applications match your search.' : 'No applications waiting for review.' }}</p>
      </div>

      <div v-else ref="layout" class="review-layout" :style="deskHeight ? { '--desk-h': `${deskHeight}px` } : null">
        <!-- list -->
        <div class="nm-panel queue">
          <p class="queue-hint"><strong>Waiting</strong><i>{{ filtered.length }}</i><small>Oldest first</small></p>
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
            <span class="queue-wait" :class="{ long: waitDays(r) > 3 }" :title="`Applied ${shortDate(r.submitted_at)}`"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg> {{ waitText(r) }}</span>
            <ChevronRight :size="16" class="queue-chevron" />
          </button>
          <ListPager v-model:page="page" :pages="pages" />
        </div>

        <!-- REVIEW: a verification desk (2026-10-25). The decision bar stays at the
             top; the checklist sits beside the license photo, each tick next to the
             value it checks; then a preview of what clients will see once approved,
             with anything missing marked in gold. A full-screen sheet on phones. -->
        <div v-if="selected" ref="reviewWrap" class="review-wrap">
          <div class="nm-panel review">
            <button type="button" class="nm-btn-soft nm-btn-sm back-btn" @click="selectedId = null"><ArrowLeft :size="15" /> All applications</button>

            <div class="decide">
              <div class="decide-who">
                <img v-if="selected.profile_photo" :src="selected.profile_photo" class="nm-avatar lg" alt="" />
                <span v-else class="nm-avatar lg">{{ userInitials(selected.first_name, selected.last_name) }}</span>
                <div class="decide-name">
                  <h2 class="nm-panel-title">{{ selected.first_name }} {{ selected.last_name }}</h2>
                  <p class="nm-panel-sub"><span class="spec-chip">{{ selected.specialization }}</span><i class="dot" aria-hidden="true"></i>Applied {{ shortDate(selected.submitted_at) }}</p>
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
              <div class="progress" aria-hidden="true">
                <span class="pg-txt"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" /></svg> Tick all {{ checkTotal }} checks to approve</span>
                <span class="pg-bar"><i :style="{ width: `${(checkedCount / checkTotal) * 100}%` }"></i></span>
                <b>{{ checkedCount }} of {{ checkTotal }}</b>
              </div>
            </div>

            <p v-if="!selected.email_verified_at" class="nm-note plain-note review-note">
              Waiting for the applicant to confirm their email. You can approve once they have.
            </p>

            <!-- 1. the license, with the checks beside it -->
            <h3 class="desk-title">Check the identity</h3>
            <div class="desk">
              <div class="photos">
                <div class="photo-cell">
                  <p class="photo-label"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2" /><circle cx="8" cy="12" r="2.5" /><path d="M13 10h5M13 14h3" /></svg> PRC license</p>
                  <button v-if="selected.prc_license_image_url" type="button" class="license" aria-haspopup="dialog" @click="zoom = 'license'">
                    <img :src="selected.prc_license_image_url" alt="PRC license photo" />
                    <span><Maximize2 :size="13" aria-hidden="true" /> View full size</span>
                  </button>
                  <div v-else class="license license-missing">No license photo on file. The license can't be checked.</div>
                </div>
                <div class="photo-cell">
                  <p class="photo-label"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" /><circle cx="12" cy="13" r="4" /></svg> Selfie with the license</p>
                  <button v-if="selected.prc_selfie_image_url" type="button" class="license" aria-haspopup="dialog" @click="zoom = 'selfie'">
                    <img :src="selected.prc_selfie_image_url" alt="Selfie holding the PRC license" />
                    <span><Maximize2 :size="13" aria-hidden="true" /> View full size</span>
                  </button>
                  <div v-else class="license license-none">No selfie on file. This application was sent before selfies were asked for.</div>
                </div>
              </div>

              <div class="checks">
                <label class="check-row" :class="{ done: checks.name }">
                  <input v-model="checks.name" type="checkbox" /><span class="ck-box" aria-hidden="true"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></span>
                  <span class="check-text">
                    <span>The name matches the license</span>
                    <strong>{{ selected.first_name }} {{ selected.last_name }}</strong>
                  </span>
                </label>
                <label class="check-row" :class="{ done: checks.number }">
                  <input v-model="checks.number" type="checkbox" /><span class="ck-box" aria-hidden="true"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></span>
                  <span class="check-text">
                    <span>The license number is valid on the PRC website</span>
                    <strong class="mono">{{ selected.prc_license_number || 'No number given' }}</strong>
                    <a href="https://verification.prc.gov.ph/" target="_blank" rel="noopener" class="nm-panel-link prc-link" @click.stop>
                      Check on the PRC website <ExternalLink :size="12" aria-hidden="true" />
                    </a>
                  </span>
                </label>
                <label v-if="selected.prc_selfie_image_url" class="check-row" :class="{ done: checks.face }">
                  <input v-model="checks.face" type="checkbox" /><span class="ck-box" aria-hidden="true"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></span>
                  <span class="check-text">
                    <span>The face in the selfie matches the license photo</span>
                    <small>The ID in the selfie is the same license, with the same name.</small>
                  </span>
                </label>
                <label class="check-row" :class="{ done: checks.photo }">
                  <input v-model="checks.photo" type="checkbox" /><span class="ck-box" aria-hidden="true"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></span>
                  <span class="check-text">
                    <span>The photo is clear and the license isn't expired</span>
                    <small>Look for the expiry date on the photo.</small>
                  </span>
                </label>
              </div>
            </div>

            <!-- 2. the profile: applicants since 2026-11-16 set it up after approval, in the RND onboarding -->
            <p v-if="!hasProfileInfo" class="nm-note plain-note desk-note">
              <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg> <span>Their profile, fee, formats and weekly hours are set after approval, when they first sign in. Clients can't find them until then.</span>
            </p>
            <template v-else>
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
            </template>

            <!-- 3. contact details, for the admin only -->
            <h3 class="desk-title">Contact</h3>
            <dl class="contact">
              <div><span class="cc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M22 6l-10 7L2 6" /></svg></span><dt>Email</dt><dd>{{ selected.email }}</dd></div>
              <div><span class="cc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.5 2.7.6a2 2 0 0 1 1.7 2z" /></svg></span><dt>Mobile</dt><dd>{{ formatPhone(selected.phone) || 'None given' }}</dd></div>
              <div><span class="cc-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-8a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8" /><path d="M4 16s.5-1 2-1 2.5 2 4 2 2.5-2 4-2 2.5 2 4 2 2-1 2-1" /><path d="M2 21h20M7 8v3M12 8v3M17 8v3" /></svg></span><dt>Date of birth</dt><dd>{{ selected.date_of_birth ? `${shortDate(selected.date_of_birth)} (${ageFrom(selected.date_of_birth)})` : 'None given' }}</dd></div>
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

    <!-- LICENSE PHOTO, full size (the client Resources preview pop-up) -->
    <div v-if="zoom && zoomUrl" class="nm-modal-overlay" @click.self="zoom = null">
      <div class="nm-modal license-modal" role="dialog" aria-modal="true" aria-labelledby="license-title">
        <div class="lm-head nm-modal-head">
          <span class="lm-icon"><IdCard :size="18" aria-hidden="true" /></span>
          <div style="flex: 1; min-width: 0">
            <h3 id="license-title" class="nm-modal-title" style="margin: 0">{{ zoom === 'selfie' ? 'Selfie with the license' : 'PRC license' }}, {{ selected.first_name }} {{ selected.last_name }}</h3>
            <p class="nm-panel-sub">License no. {{ selected.prc_license_number || 'not given' }}</p>
          </div>
          <button type="button" class="nm-modal-x" aria-label="Close" @click="zoom = null"><X :size="18" aria-hidden="true" /></button>
        </div>
        <div class="lm-photo"><img :src="zoomUrl" :alt="zoom === 'selfie' ? 'Selfie holding the PRC license, full size' : 'PRC license photo, full size'" /></div>
        <div class="nm-modal-actions">
          <a :href="zoomUrl" target="_blank" rel="noopener noreferrer" class="nm-btn-soft"><ExternalLink :size="14" aria-hidden="true" /> Open in new tab</a>
          <button type="button" class="nm-btn-dark" @click="zoom = null">Done</button>
        </div>
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

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import {
  ArrowLeft, BadgeCheck, CalendarClock, Check, CheckCircle2, ChevronRight, ExternalLink, IdCard, MapPin, Maximize2, Search, ShieldCheck,
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
  { key: 'face', label: 'The face in the selfie matches the license photo' },
  { key: 'photo', label: 'The license photo is clear and not expired' },
]
const QUICK_REASONS = [
  'The PRC license photo is blurry. Please upload a clearer photo of the front of your license.',
  "The name on your application doesn't match the name on your PRC license.",
  "We couldn't match your selfie with your PRC license. Please upload a clear selfie holding your license next to your face.",
  "We couldn't verify your PRC license number on the PRC website. Please check it and apply again.",
  'Your PRC license appears to be expired. Please renew it and apply again.',
]

const MODE_ICONS = { video: Video, in_person: UserRound }
const zoom = ref(null) // 'license' | 'selfie' while a photo is open full size

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
const toast = useToast() // the app's toast (2026-11-03)
const selectedId = ref(null)
const checks = reactive({ name: false, number: false, face: false, photo: false })
// an application from before the onboarding already holds a fee, languages or a bio
const hasProfileInfo = computed(() => Number(selected.value?.consultation_fee) >= 100 || !!(selected.value?.bio || '').trim() || (selected.value?.languages || []).length > 0)
const zoomUrl = computed(() => (zoom.value === 'selfie' ? selected.value?.prc_selfie_image_url : selected.value?.prc_license_image_url) || '')

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
// applications sent before selfies were asked for have none, so that check doesn't apply
const allChecked = computed(() => CHECKS.every(c => checks[c.key] || (c.key === 'face' && !selected.value?.prc_selfie_image_url)))
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
function select(id) {
  selectedId.value = id
  // the queue shows the page the open application is on
  const at = filtered.value.findIndex(r => r.id === id)
  if (at >= 0) page.value = Math.floor(at / 20) + 1
  for (const c of CHECKS) checks[c.key] = false
  // start each application at the top (the sheet on phones, the page on desktop)
  nextTick(() => {
    if (reviewWrap.value) reviewWrap.value.scrollTop = 0
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

// Desktop: the queue and the review panel fill the rest of the screen and
// scroll on their own, so the page itself stays still.
const layout = ref(null)
const deskHeight = ref(0)
function measure() {
  if (!layout.value || !isWide()) { deskHeight.value = 0; return }
  const top = layout.value.getBoundingClientRect().top + window.scrollY
  deskHeight.value = Math.max(360, window.innerHeight - top - 24)
  // take off whatever still makes the page scroll (the page's bottom padding)
  nextTick(() => {
    const over = document.documentElement.scrollHeight - window.innerHeight
    if (over > 0) deskHeight.value = Math.max(360, deskHeight.value - over)
  })
}
watch(layout, () => nextTick(measure))
onMounted(() => window.addEventListener('resize', measure))
onBeforeUnmount(() => window.removeEventListener('resize', measure))

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

function flash(msg, opts) {
  toast.success(msg, opts)
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
    toast.error(apiError(e, 'Could not approve this RND. Please try again.'))
  } finally {
    busy.value = false
  }
}

// Reject = decline the application with a reason; the applicant is emailed
// the reason and can apply again with the same email.
const rejecting = ref(false)
const rejectReason = ref('')
const rejectError = ref('')
// clear the error once the reason is long enough (a quick reason fills it in)
watch(rejectReason, (v) => { if (rejectError.value && v.trim().length >= 10) rejectError.value = '' })
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// the progress bar under the decision bar (the selfie check only counts when there is a selfie)
const checkTotal = computed(() => CHECKS.filter(c => c.key !== 'face' || selected.value?.prc_selfie_image_url).length)
const checkedCount = computed(() => CHECKS.filter(c => checks[c.key] && (c.key !== 'face' || selected.value?.prc_selfie_image_url)).length)
</script>
<style scoped>
.nm-page { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; display: inline-block; }

/* ---------- hero ---------- */
.ra-hero { position: relative; overflow: hidden; margin-bottom: 18px; padding: 26px 30px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.ra-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.ra-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 52%, rgba(0, 77, 58, 0.85) 72%, rgba(0, 77, 58, 0.6) 100%); }
.ra-hero-txt { position: relative; z-index: 1; max-width: 620px; }
.ra-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.ra-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.ra-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.ra-sub { margin: 0; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }

/* ---------- tabs + search ---------- */
.ra-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin: 0 0 12px; }
.ra-tabs { display: inline-flex; gap: 4px; max-width: 100%; padding: 5px; border: none; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); overflow-x: auto; scrollbar-width: none; }
.ra-tabs::-webkit-scrollbar { display: none; }
.ra-tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 36px; margin: 0; padding: 0 15px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.ra-tabs .nm-tab .ic { color: #8a9a91; }
.ra-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; }
.ra-tabs .nm-count { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 700; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.ra-tabs .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.ra-tabs .nm-tab.active .ic { color: #efbf04; }
.ra-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }
.ra-tabs .nm-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.ra-search { position: relative; display: flex; align-items: center; gap: 10px; flex: 0 1 320px; height: 46px; margin: 0; padding: 0 16px; border: none; border-radius: 999px; background: #fff; color: #8a9a91; box-sizing: border-box; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); }
.ra-search:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.ra-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.ra-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }
.unfinished-note { display: flex; align-items: center; gap: 8px; margin: 0 0 18px; padding: 10px 14px; border: none; border-radius: 14px; background: #eef1fa; font-size: 13px; color: #2e4a86; }
.ra-loading { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 40px 20px; border-radius: 22px; background: #fff; box-shadow: var(--sh); font-weight: 600; }
.ra-spin { width: 20px; height: 20px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: ra-spin 0.8s linear infinite; }
@keyframes ra-spin { to { transform: rotate(360deg); } }
.nm-panel.nm-empty, .review-placeholder { border: none; border-radius: 24px; box-shadow: var(--sh); }

.review-layout { display: grid; grid-template-columns: minmax(280px, 320px) 1fr; gap: 18px; align-items: start; }

/* ---------- queue ---------- */
.queue { position: sticky; top: 92px; padding: 8px; border: none; border-radius: 22px; box-shadow: var(--sh); }
.queue-hint { display: flex; align-items: center; gap: 8px; margin: 0; padding: 10px 10px 12px; }
.queue-hint strong { font-family: 'Playfair Display', serif; font-size: 18px; color: #0e3a2c; }
.queue-hint i { min-width: 22px; height: 22px; padding: 0 7px; border-radius: 999px; background: #efbf04; color: #004d3a; font-style: normal; font-size: 12px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.queue-hint small { margin-left: auto; font-size: 12px; color: #8a9a91; }
.queue :deep(.nm-pager) { margin: 8px 0 0; padding: 10px 0 2px; }
.queue-item { display: flex; align-items: center; gap: 12px; width: 100%; padding: 12px; border: 1.5px solid transparent; border-radius: 16px; background: none; font-family: inherit; color: inherit; text-align: left; cursor: pointer; transition: background 0.15s; }
.queue-item + .queue-item { margin-top: 4px; }
.queue-item:hover { background: #f7faf8; }
.queue-item.active { border-color: #1f9d55; background: #f1f8f4; box-shadow: 0 0 0 3px rgba(31, 157, 85, 0.1); }
.queue-item:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.queue-item .nm-avatar { flex-shrink: 0; width: 42px; height: 42px; border-radius: 50%; object-fit: cover; box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-size: 13.5px; font-weight: 800; border: 2px solid #fff; box-shadow: 0 0 0 2.5px #efbf04; }
.queue-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.queue-name { font-size: 14.5px; font-weight: 700; color: #0e3a2c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-sub { font-size: 12.5px; color: #6b7d73; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-wait { flex-shrink: 0; display: inline-flex; align-items: center; gap: 4px; padding: 3px 9px; border-radius: 999px; background: #f3f6f4; font-size: 11.5px; font-weight: 800; color: #4a5a52; white-space: nowrap; }
.queue-wait.long, .queue-item.active .queue-wait { background: #fff4d6; color: #8a6500; }
.queue-chevron { flex-shrink: 0; display: none; color: #9dc3ae; }

/* ---------- review panel ---------- */
/* desktop: no scroll inside the card; the page scrolls and the queue stays in view */
@media (min-width: 1000px) {
  .review-wrap { max-height: none !important; overflow: visible; border-radius: 24px; box-shadow: var(--sh); }
  .queue { position: sticky; top: 92px; max-height: none; overflow: visible; }
  .decide { position: static; }
}
.review { padding: 0 26px 26px; border: none; border-radius: 24px; counter-reset: desk; }
.decide {
  position: sticky; top: 0; z-index: 3; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px 16px;
  margin: 0 -26px; padding: 20px 26px 14px; background: #f1f8f4; border-bottom: 1px solid #e3efe7; border-radius: 24px 24px 0 0;
}
.decide-who { display: flex; align-items: center; gap: 16px; min-width: 0; }
.decide-who .nm-avatar.lg { flex-shrink: 0; width: 60px; height: 60px; border-radius: 50%; object-fit: cover; box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-family: 'Playfair Display', serif; font-size: 21px; font-weight: 700; border: 3px solid #fff; box-shadow: 0 0 0 2.5px #efbf04, 0 10px 20px -12px rgba(0, 77, 58, 0.6); }
.decide-name { min-width: 0; }
.decide-name .nm-panel-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; color: #0e3a2c; }
.decide-name .nm-panel-sub { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 0; font-size: 13.5px; color: #6b7d73; }
.spec-chip { padding: 3px 10px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px #dce8e0; font-size: 12.5px; font-weight: 700; color: #1f5c45; }
.decide-name .dot { width: 4px; height: 4px; border-radius: 50%; background: #b5c3ba; }
.decide-actions { display: flex; align-items: center; gap: 10px; }
.review-pos { margin-right: 2px; font-size: 12.5px; font-weight: 600; color: #8a9a91; white-space: nowrap; }
.decide-actions > button { display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 42px; padding: 0 18px; border-radius: 12px; font-family: inherit; font-size: 14px; font-weight: 800; cursor: pointer; }
.decide-actions .nm-btn-danger { background: #fff; border: 1px solid #f2c4be; color: #b42318; box-shadow: none; }
.decide-actions .nm-btn-danger:hover:not(:disabled) { background: #fdecea; }
.decide-actions .nm-btn-dark { background: #004d3a; border: 1px solid #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.decide-actions .nm-btn-dark:hover:not(:disabled) { background: #00382a; }
.decide-actions .nm-btn-dark:disabled { opacity: 0.45; cursor: not-allowed; box-shadow: none; }
.decide-hint { display: none; }
.progress { flex-basis: 100%; display: flex; align-items: center; gap: 12px; padding-top: 12px; border-top: 1px solid #e3efe7; font-size: 13px; color: #4a5a52; }
.pg-txt { display: inline-flex; align-items: center; gap: 7px; font-weight: 600; white-space: nowrap; }
.pg-txt .ic { color: #1f7a4d; }
.pg-bar { flex: 1; height: 6px; border-radius: 999px; background: #dfeae3; overflow: hidden; }
.pg-bar i { display: block; height: 100%; border-radius: 999px; background: #1f9d55; transition: width 0.25s; }
.progress b { font-size: 12.5px; color: #0e3a2c; white-space: nowrap; }
.back-btn { display: none; align-items: center; gap: 6px; margin: 16px 0 0; }
.review-note { margin: 16px 0 0; border-radius: 14px; }
.desk-title { display: flex; align-items: center; gap: 9px; margin: 24px 0 14px; font-family: inherit; font-size: 15px; font-weight: 800; color: #0e3a2c; }
.desk-title::before { counter-increment: desk; content: counter(desk); width: 24px; height: 24px; border-radius: 8px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; font-size: 12.5px; }

/* 1. license + checks */
.desk { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1.15fr); gap: 14px; align-items: start; }
@media (max-width: 1200px) and (min-width: 1000px) { .desk { grid-template-columns: 1fr; } }
.photos { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; align-items: start; }
.photo-cell { min-width: 0; border: 1.5px solid #c9d8cf; border-radius: 18px; background: #fff; overflow: hidden; }
.photo-label { display: flex; align-items: center; gap: 7px; margin: 0; padding: 11px 14px; border-bottom: 1px solid #eef2ef; font-size: 13px; font-weight: 800; color: #0e3a2c; }
.photo-label .ic { color: #1f7a4d; }
.license { display: block; width: 100%; padding: 0; border: none; border-radius: 0; overflow: hidden; background: #f1f4f2; font-family: inherit; text-align: left; text-decoration: none; cursor: zoom-in; }
.license:hover img { opacity: 0.92; }
.license img, .photos .license img { display: block; width: 100%; height: 210px; max-height: none; object-fit: cover; background: #f1f4f2; }
.license span { display: flex; align-items: center; justify-content: center; gap: 7px; height: 42px; padding: 0 12px; border-top: 1px solid #eef2ef; background: #f7faf8; font-size: 13px; font-weight: 800; color: #004d3a; }
.license:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.photos .license-missing, .photos .license-none { min-height: 262px; display: flex; align-items: center; justify-content: center; cursor: default; }
.license-none { padding: 36px 16px; text-align: center; background: #f7faf8; color: #4a5a52; font-size: 13px; }
.license-missing { padding: 48px 16px; text-align: center; background: #fdecea; color: #b42318; font-size: 13px; font-weight: 700; }
.checks { display: flex; flex-direction: column; border: 1.5px solid #c9d8cf; border-radius: 18px; overflow: hidden; background: #fff; }
.check-row { position: relative; display: flex; align-items: flex-start; gap: 12px; padding: 14px 16px; cursor: pointer; background: #fff; transition: background 0.15s; }
.check-row + .check-row { border-top: 1px solid #eef2ef; }
.check-row:hover { background: #fafcfb; }
.check-row.done { background: #f1f8f4; }
.check-row input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.ck-box { flex-shrink: 0; width: 22px; height: 22px; margin-top: 1px; border-radius: 7px; border: 2px solid #9dc3ae; background: #fff; color: transparent; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; transition: background 0.15s, border-color 0.15s; }
.check-row.done .ck-box { background: #1f9d55; border-color: #1f9d55; color: #fff; }
.check-row input:focus-visible + .ck-box { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.check-text { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; min-width: 0; font-size: 14px; font-weight: 600; color: #22362c; }
.check-text strong { font-size: 17px; font-weight: 800; color: #0e3a2c; overflow-wrap: anywhere; }
.check-text small { font-size: 12.5px; font-weight: 400; color: #6b7d73; }
.prc-link { display: inline-flex; align-items: center; gap: 6px; margin-top: 2px; padding: 6px 12px; border-radius: 10px; background: #004d3a; color: #fff !important; font-size: 12.5px; font-weight: 800; text-decoration: none; }
.prc-link:hover { background: #00382a; }
.mono { font-variant-numeric: tabular-nums; letter-spacing: 0.06em; }
.desk-note { display: flex; align-items: flex-start; gap: 10px; margin: 18px 0 0; padding: 12px 14px; border: 1px solid #f3e2a0; border-radius: 14px; background: #fffbea; font-size: 13px; line-height: 1.55; color: #6b5a1e; }
.desk-note .ic { margin-top: 1px; color: #c49102; }

/* 2. the client-facing card */
.preview { display: flex; flex-direction: column; gap: 10px; padding: 18px; border: 1.5px solid #c9d8cf; border-radius: 18px; background: #fff; overflow-wrap: anywhere; }
.pv-head { display: flex; gap: 14px; align-items: flex-start; }
.pv-head .nm-avatar.lg { flex-shrink: 0; width: 54px; height: 54px; border-radius: 50%; object-fit: cover; display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-weight: 800; border: 2px solid #fff; box-shadow: 0 0 0 2.5px #1f9d55; box-sizing: border-box; }
.pv-id { min-width: 0; }
.pv-name { display: flex; align-items: center; gap: 6px; margin: 0; font-family: 'Playfair Display', serif; font-size: 19px; font-weight: 700; color: #0e3a2c; }
.pv-verified { color: #1f9d55; }
.pv-spec { margin: 3px 0 0; font-size: 13px; color: #4a5a52; }
.pv-fee { margin: 4px 0 0; font-size: 13.5px; font-weight: 700; color: #0e3a2c; }
.pv-bio { margin: 0; font-size: 13.5px; line-height: 1.55; color: #4a5a52; white-space: pre-line; }
.pv-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { padding: 3px 10px; border-radius: 999px; background: #e3f4ea; font-size: 12.5px; font-weight: 700; color: #1f5c45; }
.pv-formats { display: flex; flex-wrap: wrap; gap: 8px; }
.format { display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px; border-radius: 999px; background: #eef1fa; font-size: 12.5px; font-weight: 700; color: #2e4a86; }
.pv-where { display: flex; align-items: flex-start; gap: 6px; margin: 0; font-size: 13px; line-height: 1.4; color: #4a5a52; }
.pv-where svg { flex-shrink: 0; margin-top: 2px; color: #1f7a4d; }
.pv-hours { display: flex; align-items: flex-start; gap: 8px; padding: 10px 12px; border-radius: 12px; background: #f1f8f4; color: #1f5c45; font-size: 13px; line-height: 1.45; }
.pv-hours svg { flex-shrink: 0; margin-top: 1px; }
.pv-hours-list { display: flex; flex-direction: column; gap: 2px; }
.gap { display: inline-block; align-self: flex-start; margin: 0; padding: 3px 9px; border-radius: 8px; background: #fff4d6; font-size: 12.5px; font-weight: 700; color: #8a6500; }

/* 3. contact */
.contact { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 0; border: none; }
.contact > div { display: grid; grid-template-columns: 38px minmax(0, 1fr); grid-template-rows: auto auto; column-gap: 12px; align-items: center; min-width: 0; padding: 14px; border: 1.5px solid #c9d8cf !important; border-radius: 16px; }
.cc-ico { grid-row: 1 / 3; width: 38px; height: 38px; border-radius: 12px; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.contact dt { font-size: 12px; color: #8a9a91; }
.contact dd { margin: 0; font-size: 14px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }

/* approved / rejected / deactivated table */
.nm-page > .nm-panel { border: none; border-radius: 24px; box-shadow: var(--sh); }
.reason { font-size: 13.5px; color: #22362c; }
.review-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; min-height: 300px; font-size: 14px; color: #6b7d73; }
.review-placeholder p { margin: 0; }
.review-placeholder svg { width: 56px; height: 56px; padding: 14px; border-radius: 18px; background: #e3efe7; color: #004d3a; box-sizing: border-box; }

/* full-size photo pop-up */
.license-modal { max-width: 900px; }
.lm-head { display: flex; gap: 12px; align-items: flex-start; }
.lm-icon { flex-shrink: 0; width: 40px; height: 40px; border-radius: 12px; background: #004d3a; color: #efbf04; display: flex; align-items: center; justify-content: center; }
.lm-photo { margin-top: 16px; border: 1px solid #e3ebe6; border-radius: 16px; overflow: auto; background: #f7faf8; display: flex; justify-content: center; }
.lm-photo img { display: block; max-width: 100%; max-height: 70vh; object-fit: contain; }

/* reject pop-up */
.reason-chips { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.reason-chip { padding: 10px 12px; border: 1.5px solid #dce8e0; border-radius: 12px; background: #fff; font-family: inherit; font-size: 13px; line-height: 1.4; color: #0e3a2c; text-align: left; cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.reason-chip:hover { border-color: #1f9d55; background: #f1f8f4; }
.reason-chip:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

/* below 1000px: the list; an application opens as a full-screen sheet */
@media (max-width: 999px) {
  .ra-hero { padding: 20px 18px; border-radius: 22px; }
  .ra-title { font-size: 24px; }
  .ra-plate { width: 180px; height: 180px; right: -60px; top: 20px; transform: none; }
  .ra-hero-txt { max-width: 70%; }
  .ra-search { flex: 1 1 100%; }
  .ra-tabs { display: flex; width: 100%; border-radius: 16px; }
  .review-layout { grid-template-columns: 1fr; }
  .queue { position: static; max-height: none; }
  .queue-chevron { display: block; }
  .queue-item.active { background: none; border-color: transparent; box-shadow: none; }
  .review-placeholder { display: none; }
  .review-wrap { position: fixed; inset: 0; z-index: 250; padding: 16px; background: #f4f5f3; overflow-y: auto; }
  .review { min-height: 100%; padding: 0 16px 20px; }
  .back-btn { display: inline-flex; }
  .decide { top: -16px; margin: 0 -16px; padding: 16px 16px 12px; }
  .desk { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .nm-page { padding-bottom: 110px; }
}
@media (max-width: 640px) {
  .license-modal { max-width: none; height: 100%; max-height: none; border-radius: 0; display: flex; flex-direction: column; }
  .lm-photo { flex: 1; align-items: center; }
  .photos { grid-template-columns: 1fr; }
  .decide-who .nm-avatar.lg { width: 50px; height: 50px; font-size: 17px; }
  .decide-name .nm-panel-title { font-size: 21px; }
  .decide-actions { width: 100%; flex-wrap: wrap; }
  .decide-actions > button { flex: 1; }
  .review-pos { width: 100%; }
  .progress { flex-wrap: wrap; }
  .pg-bar { flex-basis: 100%; order: 3; }
  .contact { grid-template-columns: 1fr; }
}
</style>