<template>
  <div class="room">
    <!-- TOP BAR -->
    <header class="bar">
      <div class="bar-left">
        <span class="brand">Nutri<span class="gold">Match</span></span>
        <template v-if="appt">
          <span class="sep" aria-hidden="true" />
          <span class="who">
            <img v-if="other.photo" :src="other.photo" class="bar-avatar" alt="" />
            <span v-else class="bar-avatar">{{ initials(other.name) }}</span>
            <span class="who-text">
              <strong>{{ other.name }}</strong>
              <small>{{ clock(appt.scheduled_at) }}–{{ clock(endsAt) }}, {{ typeLabel.toLowerCase() }}</small>
            </span>
          </span>
        </template>
      </div>
      <div class="bar-right">
        <span v-if="appt && appt.status === 'confirmed'" class="timer" :class="timerTone">{{ timerText }}</span>
        <!-- RND: once the consultation can start, the only way out is Finish
             (mark complete / leave for now / no-show) — no plain Exit. -->
        <button v-if="mustFinish" type="button" class="end-btn" @click="openEnd">
          <CheckCircle2 :size="15" /> Finish consultation
        </button>
        <button v-else type="button" class="exit-btn" @click="exitRoom">
          <template v-if="!isRnd && appt?.status === 'confirmed' && windowState === 'open'"><PhoneOff :size="15" /> Leave call</template>
          <template v-else><ArrowLeft :size="15" /> Leave</template>
        </button>
      </div>
    </header>

    <div class="body" :class="{ rnd: isRnd }">
      <!-- VIDEO -->
      <main class="stage">
        <p v-if="error" class="state-card err">{{ error }}</p>
        <div v-else-if="loading" class="state-card"><p>Loading…</p></div>
        <div v-else-if="!appt" class="state-card"><VideoOff :size="28" /><p>Consultation not found.</p></div>
        <div v-else-if="appt.status === 'completed'" class="state-card">
          <CheckCircle2 :size="28" /><p>This consultation is complete.</p>
          <button type="button" class="link" @click="summaryOpen = true">View the summary</button>
          <button type="button" class="link quiet" @click="exitRoom">Leave the room</button>
        </div>
        <div v-else-if="appt.status !== 'confirmed'" class="state-card">
          <VideoOff :size="28" /><p>This consultation {{ appt.status === 'cancelled' ? 'was cancelled' : 'isn\'t confirmed yet' }}.</p>
          <button type="button" class="link quiet" @click="exitRoom">Leave the room</button>
        </div>
        <!-- Pay first: the API only sends the client the room link once it's paid. -->
        <div v-else-if="!isRnd && appt.payment?.status === 'unpaid'" class="state-card">
          <VideoOff :size="28" />
          <p>Your consultation opens once it's paid. Pay {{ peso(appt.payment.amount) }} before {{ clock(appt.scheduled_at) }} to join.</p>
          <NuxtLink to="/appointments" class="link">Pay in My Appointments</NuxtLink>
        </div>
        <div v-else-if="windowState === 'early'" class="state-card">
          <Clock :size="28" />
          <p class="big">Opens in {{ untilOpen }}</p>
          <p>The room opens {{ clock(appt.join_opens_at) }}, 15 minutes before the start. This page opens it automatically.</p>
        </div>
        <div v-else-if="windowState === 'closed'" class="state-card">
          <VideoOff :size="28" /><p>This consultation's room has closed.</p>
          <button v-if="isRnd" type="button" class="link" @click="openEnd">Finish this consultation</button>
        </div>
        <div v-else-if="appt.type === 'in_person'" class="state-card"><Clock :size="28" /><p>This is an in-person consultation. Meet {{ isRnd ? 'your patient' : 'your RND' }} at the clinic{{ isRnd ? ' and use the panel for your notes' : '' }}.</p></div>
        <div v-else-if="!appt.video_session_url" class="state-card"><VideoOff :size="28" /><p>No video room has been set up for this consultation.</p></div>
        <!-- Jitsi's embed script, so hanging up can open Finish; the plain
             frame is the fallback if the script can't load. -->
        <iframe v-else-if="jitsiFailed" :src="videoSrc" class="video" title="Video consultation" allow="camera; microphone; fullscreen; display-capture; autoplay" />
        <div v-else ref="videoHost" class="video" />
      </main>

      <!-- RND WORK PANEL -->
      <aside v-if="isRnd && appt" class="panel">
        <nav class="tabs" role="tablist" aria-label="Consultation tools">
          <button v-for="t in RND_TABS" :key="t.key" type="button" role="tab" class="tab" :class="{ on: tab === t.key }" :aria-selected="tab === t.key" @click="tab = t.key">
            <component :is="t.icon" :size="14" /> {{ t.label }}
          </button>
        </nav>

        <div class="panel-body">
          <p v-if="!s" class="muted">Loading patient…</p>

          <!-- PATIENT -->
          <template v-else-if="tab === 'patient'">
            <p v-if="s.health.allergies.length" class="allergy"><AlertTriangle :size="14" /> Allergy: {{ s.health.allergies.join(', ') }}</p>
            <p v-if="appt.notes" class="note">“{{ appt.notes }}”<small>Their note when booking</small></p>
            <div class="stats">
              <div><span>Weight</span><strong>{{ p.progress.latest_weight_kg != null ? `${fmt1(p.progress.latest_weight_kg)} kg` : '—' }}</strong><small>{{ p.progress.weight_change_kg != null ? `${signed(p.progress.weight_change_kg)} kg since screening` : 'from screening' }}</small></div>
              <div><span>BMI</span><strong>{{ p.progress.bmi != null ? fmt1(p.progress.bmi) : '—' }}</strong><small>{{ p.progress.bmi_class || '' }}</small></div>
              <div><span>Adherence, 7 days</span><strong>{{ p.adherence?.pct != null ? `${p.adherence.pct}%` : '—' }}</strong><small>{{ p.adherence ? `${p.adherence.logged} of ${p.adherence.planned} logged` : 'no active plan' }}</small></div>
              <div :class="{ risk: (s.screening?.nrs_score ?? 0) >= 3 }"><span>NRS-2002</span><strong>{{ s.screening?.nrs_score ?? '—' }}</strong><small>{{ s.screening?.nrs_risk || '' }}</small></div>
            </div>
            <dl class="facts">
              <div><dt>Age and sex</dt><dd>{{ [p.client.age != null ? `${p.client.age} y/o` : null, SEX[p.client.sex]].filter(Boolean).join(', ') || '—' }}</dd></div>
              <div><dt>Conditions</dt><dd>{{ list(s.health.conditions) }}</dd></div>
              <div><dt>Diet</dt><dd>{{ list(s.health.dietary_restrictions) }}</dd></div>
              <div v-if="s.health.religion"><dt>Religion</dt><dd>{{ s.health.religion }}</dd></div>
              <div><dt>Goals</dt><dd>{{ list(s.health.health_goals) }}</dd></div>
              <div v-if="s.screening"><dt>BMR and TDEE</dt><dd>{{ whole(s.screening.bmr_kcal) }} and {{ whole(s.screening.tdee_kcal) }} kcal</dd></div>
            </dl>
            <section class="block">
              <h3>Current care plan</h3>
              <template v-if="s.care_plan">
                <p v-if="s.care_plan.pes_problem" class="txt"><strong>{{ s.care_plan.pes_problem }}</strong><template v-if="s.care_plan.pes_etiology"> related to {{ s.care_plan.pes_etiology }}</template>.</p>
                <p v-if="s.care_plan.diet_prescription" class="txt">{{ s.care_plan.diet_prescription }}</p>
                <p v-if="s.care_plan.target_kcal" class="muted">Target {{ whole(s.care_plan.target_kcal) }} kcal/day{{ s.care_plan.target_carb_g ? `, ${whole(s.care_plan.target_carb_g)} g carbs, ${whole(s.care_plan.target_protein_g)} g protein, ${whole(s.care_plan.target_fat_g)} g fat` : '' }}</p>
              </template>
              <p v-else class="muted">No finalized NCP record yet.</p>
            </section>
            <section v-if="s.recent_logs.length" class="block">
              <h3>Recent meal logs</h3>
              <div v-for="(l, i) in s.recent_logs.slice(0, 6)" :key="i" class="log">
                <span class="log-dot" :class="l.status" aria-hidden="true" />
                <span class="log-main">{{ shortDate(l.date) }}, {{ l.meal }}: {{ LOG[l.status] || 'not rated yet' }}<small v-if="l.note">“{{ l.note }}”</small></span>
              </div>
            </section>
            <section class="block">
              <div class="block-head">
                <h3>Lab results</h3>
                <button type="button" class="link small" :disabled="labsLoading" @click="openLabRequest"><FlaskConical :size="13" /> Request lab tests</button>
              </div>
              <p v-if="!s.labs || (!s.labs.total_results && !s.labs.open.length)" class="muted">None yet.</p>
              <p v-if="labsSent" class="ok"><CheckCircle2 :size="14" /> Sent. {{ p.client.first_name }} is asked to upload them before your next consultation.</p>
              <p v-if="labsError" class="nm-field-error">{{ labsError }}</p>
              <div v-for="r in s.labs?.recent || []" :key="r.id" class="lab-row">
                <span class="lab-main">
                  {{ r.test_names.join(', ') }}, taken {{ shortDate(r.taken_on) }}<template v-if="r.fasted === 'no'">, not fasting</template>
                  <small v-if="!r.reviewed_at" class="lab-new">New</small>
                </span>
                <button type="button" class="link small" @click="viewLab(r)">View</button>
              </div>
              <p v-for="r in s.labs?.open || []" :key="`q${r.id}`" class="muted">Requested: {{ r.test_names.join(', ') }}, not uploaded yet</p>
            </section>
            <NuxtLink :to="`/client-detail/${appt.relationship.id}`" target="_blank" class="link small chart-link"><ExternalLink :size="13" aria-hidden="true" /> Open the full chart in a new tab</NuxtLink>
          </template>

          <!-- NCP (the same form as the chart, inline) -->
          <div v-show="tab === 'ncp'" class="ncp-wrap">
            <NcpRecordModal v-if="ncpMounted" ref="ncpForm" inline :relationship-id="appt.relationship.id" :patient-name="other.name"
                            :appointment-id="appt.id" @changed="refreshSummary" />
          </div>

        </div>
      </aside>

      <!-- CLIENT PANEL -->
      <aside v-else-if="appt" class="panel client">
        <div class="panel-body">
          <div class="rnd-card">
            <img v-if="info?.rnd.profile_photo" :src="info.rnd.profile_photo" class="rnd-photo" alt="" />
            <span v-else class="rnd-photo">{{ initials(info?.rnd.name || other.name) }}</span>
            <div>
              <p class="rnd-name">{{ info?.rnd.name || other.name }}, RND</p>
              <p class="muted">{{ info?.rnd.specialization || 'Registered Nutritionist-Dietitian' }}</p>
            </div>
          </div>
          <dl class="facts">
            <div><dt>Consultation</dt><dd>{{ longWhen(appt.scheduled_at) }}</dd></div>
            <div><dt>Length</dt><dd>{{ appt.duration_minutes || 60 }} minutes</dd></div>
          </dl>
          <section v-if="info?.meal_plan" class="block">
            <h3>Your current meal plan</h3>
            <p class="txt"><strong>{{ info.meal_plan.name }}</strong></p>
            <p v-if="info.meal_plan.target_kcal" class="muted">{{ whole(info.meal_plan.target_kcal) }} kcal a day{{ info.meal_plan.target_carb_g ? `, ${whole(info.meal_plan.target_carb_g)} g carbs, ${whole(info.meal_plan.target_protein_g)} g protein, ${whole(info.meal_plan.target_fat_g)} g fat` : '' }}</p>
          </section>
          <section class="block">
            <h3>Before your call</h3>
            <ul class="check">
              <li>Allow your camera and microphone when the browser asks.</li>
              <li>Find a quiet, well-lit spot.</li>
              <li>Have your recent meal logs and any lab results ready.</li>
              <li>Write down questions you want to ask.</li>
            </ul>
          </section>
          <p class="muted small">Having trouble joining? Message {{ info?.rnd.first_name || 'your RND' }} from Messages.</p>
        </div>
      </aside>
    </div>

    <!-- FINISH CONSULTATION -->
    <div v-if="endOpen" class="overlay" @click.self="!ending && closeEnd()">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="end-title">
        <template v-if="noShowDone">
          <h2 id="end-title" class="nm-modal-title">Marked as a no-show</h2>
          <p class="nm-modal-text">
            The consultation was cancelled and {{ other.firstName }} was told why.
            <template v-if="appt.payment?.status === 'refund_pending'">Their {{ peso(appt.payment.amount) }} payment goes back to them within 5–7 business days.</template>
          </p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-dark" @click="leave">Done</button>
          </div>
        </template>
        <template v-else-if="endMode === 'noshow'">
          <h2 id="end-title" class="nm-modal-title">{{ other.firstName }} didn't show up?</h2>
          <p class="nm-modal-text">
            The consultation is cancelled and {{ other.firstName }} sees your reason.
            <template v-if="appt.payment?.status === 'paid'">Their {{ peso(appt.payment.amount) }} payment is refunded, so there's no payout for this one.</template>
          </p>
          <label class="ns-label" for="ns-reason">What happened</label>
          <textarea id="ns-reason" v-model="noShowReason" rows="3" maxlength="500" class="nm-input ns-text"
                    placeholder="e.g. I waited 15 minutes in the room and messaged you, but you didn't join." />
          <p class="ns-hint" :class="{ bad: noShowReason.trim().length > 0 && noShowReason.trim().length < 10 }">At least 10 characters.</p>
          <p v-if="ncpDirty" class="unsaved"><PenLine :size="14" aria-hidden="true" /> Your NCP form has unsaved changes. They'll be saved as a draft first.</p>
          <p v-if="endError" class="nm-field-error">{{ endError }}</p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" :disabled="ending" @click="endMode = 'choose'; endError = ''">Back</button>
            <button type="button" class="nm-btn-danger" :disabled="ending || noShowReason.trim().length < 10" @click="markNoShow">{{ ending ? 'Cancelling…' : 'Cancel as no-show' }}</button>
          </div>
        </template>
        <template v-else-if="!wrap">
          <h2 id="end-title" class="nm-modal-title">Finish this consultation?</h2>
          <p class="nm-modal-text">{{ other.name }}, {{ clock(appt.scheduled_at) }}–{{ clock(endsAt) }}</p>
          <p v-if="appt.payment && appt.payment.status !== 'paid'" class="nm-field-error">It hasn't been paid, so it can't be completed.</p>
          <p v-if="ncpDirty" class="unsaved"><PenLine :size="14" aria-hidden="true" /> Your NCP form has unsaved changes. They'll be saved as a draft first.</p>
          <p v-if="endError" class="nm-field-error">{{ endError }}</p>
          <div class="finish-choices">
            <button type="button" class="choice main" :disabled="ending || (appt.payment && appt.payment.status !== 'paid')" @click="completeNow">
              <CheckCircle2 :size="18" />
              <span><strong>{{ ending ? 'Completing…' : 'It\'s done, mark it complete' }}</strong>
                <small>Your share posts 3 days after today. This can't be undone.</small></span>
            </button>
            <button v-if="started" type="button" class="choice" :disabled="ending" @click="endMode = 'noshow'; endError = ''">
              <UserX :size="18" />
              <span><strong>{{ other.firstName }} didn't show up</strong>
                <small>Cancel with a reason. Their payment is refunded.</small></span>
            </button>
            <button type="button" class="choice" :disabled="ending" @click="leaveForNow">
              <LogOut :size="18" />
              <span><strong>Leave for now, I'll come back</strong>
                <small>It stays in To complete. Your payment for it starts only once you mark it complete.</small></span>
            </button>
          </div>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" :disabled="ending" @click="closeEnd">Stay in the room</button>
          </div>
        </template>
        <template v-else>
          <h2 id="end-title" class="nm-modal-title"><CheckCircle2 :size="18" class="ok-icon" /> Consultation complete</h2>
          <p class="nm-modal-text">{{ wrap.todo.length ? 'Before you move on:' : 'Everything for this visit is done.' }}</p>
          <ul v-if="wrap.todo.length" class="todo">
            <li v-for="t in wrap.todo" :key="t.text"><NuxtLink :to="t.link" class="nm-panel-link">{{ t.text }}</NuxtLink></li>
          </ul>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" @click="summaryOpen = true">View summary</button>
            <NuxtLink :to="`/client-detail/${appt.relationship.id}`" class="nm-btn-outline">Open patient chart</NuxtLink>
            <button type="button" class="nm-btn-dark" @click="leave">Done</button>
          </div>
        </template>
      </div>
    </div>

    <!-- LEAVE WITH UNSAVED NCP -->
    <div v-if="leaveAsk" class="overlay" @click.self="leaveAsk = false">
      <div class="nm-modal" role="alertdialog" aria-labelledby="leave-title">
        <h2 id="leave-title" class="nm-modal-title">Your NCP form has unsaved changes</h2>
        <p class="nm-modal-text">Save them as a draft before leaving the room?</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="leaveAsk = false">Stay</button>
          <button type="button" class="nm-btn-danger" @click="leave">Leave without saving</button>
          <button type="button" class="nm-btn-dark" @click="tab = 'ncp'; leaveAsk = false">Go to the NCP form</button>
        </div>
      </div>
    </div>
    <RequestLabsModal v-if="labRequest" :relationship-id="appt.relationship.id" :patient-name="other.firstName" :tests="labRequest.tests"
                      :next-consultation="labRequest.next_consultation" @close="labRequest = null" @sent="onLabsSent" />
    <ConsultationSummaryModal v-if="summaryOpen && appt" :appointment-id="appt.id" :role="isRnd ? 'rnd' : 'client'" @close="summaryOpen = false" />
  </div>
</template>

<script setup>
// The consultation room. RND: video + a work panel (Patient · NCP)
// and "End & mark complete" with a wrap-up of what's left. Client: video +
// their RND, the consultation time and their meal-plan targets — never NCP
// drafts or the RND's notes. Pay-first and the join window are enforced by the
// API (the client gets the room link only when it's paid and inside the window).
import { AlertTriangle, ArrowLeft, CheckCircle2, ClipboardList, Clock, ExternalLink, FlaskConical, LogOut, PenLine, PhoneOff, User, UserX, VideoOff } from 'lucide-vue-next'
import { openLabFile } from '~/utils/labs'

const route = useRoute()
const auth = useAuthStore()
const { get, patch } = useApi()
const now = useNow(15000)
const isRnd = computed(() => auth.user?.role === 'rnd')
// Jitsi otherwise shows whatever name was last typed in this browser; pass the
// signed-in person's name ("RND" added for the dietitian) in its URL config.
const videoSrc = computed(() => {
  const u = auth.user
  const name = u ? `${u.first_name} ${u.last_name}`.trim() + (isRnd.value ? ', RND' : '') : ''
  return name ? `${appt.value.video_session_url}#userInfo.displayName=${encodeURIComponent(JSON.stringify(name))}` : appt.value.video_session_url
})
const apptId = route.params.id

const appt = ref(null)
const s = ref(null) // RND: patient summary
const info = ref(null) // client: room info
const loading = ref(true)
const error = ref('')
const p = computed(() => s.value?.patient)

async function loadAppointment() {
  appt.value = await get(isRnd.value ? `/rnd/appointments/${apptId}/` : `/client/appointments/${apptId}/`)
}
async function refreshSummary() {
  if (!isRnd.value || !appt.value) return
  s.value = await get(`/rnd/relationships/${appt.value.relationship.id}/summary/`).catch(() => s.value)
}
// Opening a lab file marks it reviewed, so refresh the "New" tags after.
async function viewLab(r) {
  if ((await openLabFile(get, `/rnd/lab-results/${r.id}/file/`)) && !r.reviewed_at) refreshSummary()
}
onMounted(async () => {
  try {
    await loadAppointment()
    if (isRnd.value) await refreshSummary()
    else info.value = await get(`/client/appointments/${apptId}/room-info/`).catch(() => null)
  } catch {
    error.value = 'Could not load this consultation.'
  } finally {
    loading.value = false
  }
})

/* ---------- people / time ---------- */
const other = computed(() => {
  const u = isRnd.value ? appt.value?.relationship.client : appt.value?.relationship.rnd
  return { name: u ? `${u.first_name} ${u.last_name}` : '', firstName: u?.first_name || '', photo: u?.profile_photo || null }
})
const TYPES = { video: 'Video', chat: 'Chat', in_person: 'In person' }
const typeLabel = computed(() => TYPES[appt.value?.type] || '')
const endsAt = computed(() => new Date(new Date(appt.value.scheduled_at).getTime() + (appt.value.duration_minutes || 60) * 60000))
const PH = { timeZone: 'Asia/Manila' }
const clock = v => new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
const longWhen = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
const todayIso = new Date().toLocaleDateString('en-CA', PH)
function dur(ms) {
  const m = Math.max(0, Math.round(ms / 60000))
  return m >= 60 ? `${Math.floor(m / 60)} h ${m % 60} min` : `${m} min`
}
const windowState = computed(() => {
  const a = appt.value
  if (!a?.join_opens_at) return 'open'
  if (now.value < new Date(a.join_opens_at).getTime()) return 'early'
  if (now.value > new Date(a.join_closes_at).getTime()) return 'closed'
  return 'open'
})
const untilOpen = computed(() => dur(new Date(appt.value.join_opens_at).getTime() - now.value))
const timerText = computed(() => {
  const start = new Date(appt.value.scheduled_at).getTime()
  const end = endsAt.value.getTime()
  if (now.value < start) return `Starts in ${dur(start - now.value)}`
  if (now.value <= end) return end - now.value <= 5 * 60000 ? `Ends in ${dur(end - now.value)}` : `${dur(end - now.value)} left`
  return `Overtime ${dur(now.value - end)}`
})
const timerTone = computed(() => {
  const end = endsAt.value.getTime()
  if (now.value > end) return 'over'
  return end - now.value <= 5 * 60000 && now.value >= new Date(appt.value.scheduled_at).getTime() ? 'soon' : ''
})
const started = computed(() => !!appt.value && now.value >= new Date(appt.value.scheduled_at).getTime())
// The RND can't just walk out of a consultation that could have started: they
// finish it (mark complete, leave for now, or no-show).
const mustFinish = computed(() => isRnd.value && appt.value?.status === 'confirmed' && windowState.value !== 'early')
// The client gets the room link only inside the window — fetch it when it opens.
let refetched = false
watch(windowState, (state, prev) => {
  if (prev === 'early' && state === 'open' && !refetched) { refetched = true; loadAppointment() }
})

/* ---------- RND panel ---------- */
const RND_TABS = [
  { key: 'patient', label: 'Patient', icon: User },
  { key: 'ncp', label: 'NCP', icon: ClipboardList },
]
const tab = ref('patient')
const ncpForm = ref(null)
const ncpMounted = ref(false)
watch(tab, (t) => { if (t === 'ncp') ncpMounted.value = true }) // load the form the first time it's opened
const ncpDirty = computed(() => !!ncpForm.value?.dirty)

const SEX = { male: 'Male', female: 'Female' }
const LOG = { followed: 'followed', partially_followed: 'partly followed', not_followed: 'not followed' }
const list = l => (l?.length ? l.join(', ') : '—')
const whole = v => (v == null ? '—' : Math.round(Number(v)).toLocaleString('en-PH'))
const fmt1 = v => Number(v).toFixed(1)
const signed = v => `${Number(v) > 0 ? '+' : Number(v) < 0 ? '−' : ''}${Math.abs(Number(v)).toFixed(1)}`
const initials = n => String(n || '').split(' ').filter(Boolean).map(x => x[0]).slice(0, 2).join('').toUpperCase()

/* ---------- lab tests (same pop-up as the chart) ---------- */
// Measurements are typed once, in the NCP Assessment; finalizing it saves
// them to the patient's progress (no separate Progress tab, 2026-10-23).
const labRequest = ref(null) // { tests, next_consultation } while the pop-up is open
const labsLoading = ref(false)
const labsError = ref('')
const labsSent = ref(false)
async function openLabRequest() {
  labsError.value = ''
  labsSent.value = false
  labsLoading.value = true
  try {
    const d = await get(`/rnd/relationships/${appt.value.relationship.id}/labs/`)
    if (!d.can_request) labsError.value = 'Lab tests can be requested for active patients only.'
    else labRequest.value = { tests: d.tests, next_consultation: d.next_consultation }
  } catch (e) {
    labsError.value = apiError(e, 'Could not open the lab request.')
  } finally {
    labsLoading.value = false
  }
}
function onLabsSent() {
  labRequest.value = null
  labsSent.value = true
  refreshSummary()
}

/* ---------- end & mark complete ---------- */
const summaryOpen = ref(false)
const endOpen = ref(false)
const ending = ref(false)
const endError = ref('')
const wrap = ref(null)
const endMode = ref('choose') // choose | noshow
const noShowReason = ref('')
const noShowDone = ref(false)
function openEnd() {
  endError.value = ''
  wrap.value = null
  endMode.value = 'choose'
  endOpen.value = true
}
function closeEnd() {
  endOpen.value = false
  pendingTo = null
}
async function saveNcpIfDirty() {
  if (ncpDirty.value && ncpForm.value?.saveDraft) await ncpForm.value.saveDraft()
}
// "I'll come back": keep unsaved NCP work as a draft, then go.
async function leaveForNow() {
  ending.value = true
  endError.value = ''
  try {
    await saveNcpIfDirty()
    leave()
  } catch (e) {
    endError.value = apiError(e, 'Could not save your NCP draft.')
  } finally {
    ending.value = false
  }
}
async function markNoShow() {
  ending.value = true
  endError.value = ''
  try {
    await saveNcpIfDirty()
    await patch(`/rnd/appointments/${apptId}/cancel/`, { reason: `No-show: ${noShowReason.value.trim()}` })
    await loadAppointment()
    noShowDone.value = true
  } catch (e) {
    endError.value = apiError(e, 'Could not cancel this consultation.')
  } finally {
    ending.value = false
  }
}
async function completeNow() {
  ending.value = true
  endError.value = ''
  try {
    await saveNcpIfDirty()
    await patch(`/rnd/appointments/${apptId}/complete/`)
    await loadAppointment()
    await refreshSummary()
    const rel = appt.value.relationship.id
    const todo = []
    if (s.value?.ncp_draft_id) todo.push({ text: 'Finish and finalize the NCP record', link: `/client-detail/${rel}?tab=ncp&open=draft` })
    else if (!s.value?.care_plan || s.value.care_plan.encounter_date < todayIso) todo.push({ text: 'Write an NCP record for this visit', link: `/client-detail/${rel}?tab=ncp` })
    const mp = s.value?.patient.meal_plan
    if (mp?.ready && (!mp.plan || mp.plan.status === 'draft' || mp.outdated)) {
      todo.push({ text: !mp.plan ? 'Create a meal plan' : mp.plan.status === 'draft' ? 'Send the meal plan' : 'Update the meal plan', link: `/meal-planning?relationship=${rel}` })
    }
    wrap.value = { todo }
  } catch (e) {
    endError.value = apiError(e, 'Could not complete this consultation.')
  } finally {
    ending.value = false
  }
}

/* ---------- leaving ---------- */
const leaveAsk = ref(false)
let leaving = false // set once the RND chose how to leave, so the guard lets it through
let pendingTo = null // where a blocked navigation (Back, a link) was going
function exitRoom() {
  if (mustFinish.value) { openEnd(); return }
  if (ncpDirty.value) { leaveAsk.value = true; return }
  leave()
}
function leave() {
  leaveAsk.value = false
  endOpen.value = false
  leaving = true
  const to = pendingTo
  pendingTo = null
  // Not router.back(): the Jitsi frame adds its own history entries, so "back"
  // can just step inside the frame. Use the app page we came from instead.
  navigateTo(to || window.history.state?.back || '/appointments')
}
// Browser Back, the sidebar or any link: ask the same Finish question first.
onBeforeRouteLeave((to) => {
  if (leaving) return true
  if (mustFinish.value) { pendingTo = to.fullPath; openEnd(); return false }
  if (ncpDirty.value) { pendingTo = to.fullPath; leaveAsk.value = true; return false }
  return true
})
// Closing or reloading the tab: the browser's own "Leave site?" prompt.
function onBeforeUnload(e) {
  if (!leaving && (mustFinish.value || ncpDirty.value)) { e.preventDefault(); e.returnValue = '' }
}
onMounted(() => window.addEventListener('beforeunload', onBeforeUnload))
onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload))

/* ---------- video (Jitsi embed script) ---------- */
// Jitsi's external API lets the room notice the RND pressing Jitsi's own red
// hang-up button — that opens Finish. If the script can't load, the plain
// frame is used and the Finish button still works.
const videoHost = ref(null)
const jitsiFailed = ref(false)
let jitsi = null
function loadJitsiScript(origin) {
  if (window.JitsiMeetExternalAPI) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const tag = document.createElement('script')
    tag.src = `${origin}/external_api.js`
    tag.async = true
    tag.onload = resolve
    tag.onerror = reject
    document.head.appendChild(tag)
  })
}
async function mountJitsi(host) {
  if (jitsi || !host || !appt.value?.video_session_url) return
  try {
    const url = new URL(appt.value.video_session_url)
    await loadJitsiScript(url.origin)
    if (!videoHost.value) return // the room changed state while loading
    const u = auth.user
    jitsi = new window.JitsiMeetExternalAPI(url.host, {
      roomName: url.pathname.replace(/^\//, ''),
      parentNode: host,
      configOverwrite: {
        disableDeepLinking: true, // phones stay in the browser, no "get the app" page
        // RND only — the client's hang-up works as normal.
        ...(isRnd.value ? { buttonsWithNotifyClick: [{ key: 'hangup', preventExecution: true }] } : {}),
      },
      width: '100%',
      height: '100%',
      userInfo: u ? { displayName: `${u.first_name} ${u.last_name}`.trim() + (isRnd.value ? ', RND' : '') } : undefined,
    })
    // Hanging up: Jitsi tells us instead of hanging up itself (hangup is in
    // buttonsWithNotifyClick), so we leave by disposing, put a fresh join screen
    // back (no Jitsi end page) and ask the RND to finish. readyToClose covers
    // a hang-up that still reaches Jitsi's end page.
    const hungUp = () => {
      disposeJitsi()
      if (videoHost.value) mountJitsi(videoHost.value)
      if (mustFinish.value && !endOpen.value) openEnd()
    }
    jitsi.addListener('toolbarButtonClicked', (e) => { if (e?.key === 'hangup') hungUp() })
    jitsi.addListener('readyToClose', hungUp)
  } catch {
    jitsiFailed.value = true
  }
}
function disposeJitsi() {
  if (jitsi) { jitsi.dispose(); jitsi = null }
}
watch(videoHost, (host) => { if (host) mountJitsi(host); else disposeJitsi() })
onBeforeUnmount(disposeJitsi)
</script>

<style scoped>
* { box-sizing: border-box; }
.room { height: 100vh; height: 100dvh; display: flex; flex-direction: column; background: #0d1f18; font-family: 'Inter', sans-serif; color: #1a3a1a; }

.bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 18px; color: #fff; flex-shrink: 0; flex-wrap: wrap; }
.bar-left, .bar-right { display: flex; align-items: center; gap: 12px; min-width: 0; }
.brand { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.05rem; }
.gold { color: #D4A017; }
.sep { width: 1px; height: 26px; background: rgba(255, 255, 255, 0.18); }
.who { display: flex; align-items: center; gap: 10px; min-width: 0; }
.bar-avatar { width: 32px; height: 32px; border-radius: 50%; background: #e3efe7; color: #1e4a26; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; object-fit: cover; }
.who-text { display: flex; flex-direction: column; min-width: 0; }
.who-text strong { font-size: 0.88rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.who-text small { font-size: 0.72rem; color: #a9c2b0; }
.timer { font-size: 0.78rem; font-weight: 700; padding: 5px 10px; border-radius: 999px; background: rgba(255, 255, 255, 0.1); font-variant-numeric: tabular-nums; white-space: nowrap; }
.timer.soon { background: #D4A017; color: #1a3a1a; }
.timer.over { background: #c0392b; }
.end-btn, .exit-btn { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 7px 14px; font-family: inherit; font-size: 0.8rem; font-weight: 700; cursor: pointer; white-space: nowrap; }
.end-btn { background: #D4A017; color: #1a3a1a; border: none; }
.end-btn:hover { background: #e2b02a; }
.exit-btn { background: rgba(255, 255, 255, 0.1); color: #fff; border: 1px solid rgba(255, 255, 255, 0.2); }

.body { flex: 1; display: flex; min-height: 0; }
.stage { flex: 1; display: flex; align-items: center; justify-content: center; min-width: 0; min-height: 0; }
.video { width: 100%; height: 100%; border: none; }
.state-card { display: flex; flex-direction: column; align-items: center; gap: 10px; max-width: 340px; text-align: center; color: #a9c2b0; font-size: 0.88rem; padding: 20px; }
.state-card p { margin: 0; line-height: 1.5; }
.state-card .big { font-size: 1.4rem; font-weight: 700; color: #fff; }
.state-card.err { color: #f3b8b8; }
.link { background: none; border: none; padding: 0; font-family: inherit; color: #e2c25e; font-weight: 700; font-size: 0.85rem; text-decoration: none; cursor: pointer; }
.link:hover { text-decoration: underline; }
.link:focus-visible { outline: 2px solid #e2c25e; outline-offset: 3px; border-radius: 4px; }
.link.quiet { color: #a9c2b0; font-weight: 600; }
.chart-link { display: inline-flex; align-items: center; gap: 5px; }
.panel .link { color: #1f6f46; }
.link.small { font-size: 0.78rem; display: inline-block; margin-top: 12px; }
.lab-row { display: flex; align-items: baseline; gap: 8px; padding: 4px 0; font-size: 0.78rem; }
.lab-main { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.lab-row .link.small { margin-top: 0; }
.lab-new { margin-left: 6px; font-size: 0.68rem; font-weight: 700; color: #1f6f46; background: #e3f3ea; border-radius: 8px; padding: 1px 6px; }

.panel { width: 340px; background: #f9faf8; display: flex; flex-direction: column; flex-shrink: 0; min-height: 0; border-radius: 14px 0 0 0; overflow: hidden; }
.body.rnd .panel { width: 460px; }
.tabs { display: flex; gap: 4px; padding: 10px 12px; border-bottom: 1px solid #d9e3dc; background: #fff; }
.tab { flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: none; background: none; padding: 8px; border-radius: 999px; font-family: inherit; font-size: 0.8rem; font-weight: 600; color: #6a7a6a; cursor: pointer; }
.tab.on { background: #0a4a37; color: #fff; }
.tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.panel-body { flex: 1; overflow-y: auto; padding: 16px; min-height: 0; }
.ncp-wrap { height: 100%; margin: -16px; }
.ncp-wrap :deep(.ncp.is-inline) { border: none; border-radius: 0; }
.muted { font-size: 0.8rem; color: #7a8a7a; margin: 0; line-height: 1.5; }
.muted.small { margin-top: 14px; }

.allergy { display: flex; align-items: center; gap: 6px; background: #fdecec; color: #a12525; border-radius: 8px; padding: 8px 10px; font-size: 0.82rem; font-weight: 700; margin: 0 0 10px; }
.note { background: #fff; border: 1px solid #d9e3dc; border-radius: 8px; padding: 8px 10px; font-size: 0.82rem; font-style: italic; margin: 0 0 12px; display: flex; flex-direction: column; gap: 2px; }
.note small { font-style: normal; color: #8a9a8a; font-size: 0.7rem; }
.stats { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); margin-bottom: 12px; background: #fff; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden;
  box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.stats div { padding: 10px 12px; display: flex; flex-direction: column; min-width: 0; }
.stats div:nth-child(even) { border-left: 1px solid #d9e3dc; }
.stats div:nth-child(n+3) { border-top: 1px solid #d9e3dc; }
.stats div.risk { background: #fdf3f2; }
.stats div.risk strong, .stats div.risk small { color: #a12525; }
.stats span { font-size: 0.74rem; font-weight: 600; color: #4a5a4a; }
.stats strong { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-variant-numeric: tabular-nums lining-nums; }
.stats small { font-size: 0.7rem; color: #8a9a8a; }
.facts { margin: 0 0 4px; }
.facts div { display: flex; justify-content: space-between; gap: 10px; padding: 6px 0; border-top: 1px solid #d9e3dc; }
.facts div:first-child { border-top: none; }
.facts dt { font-size: 0.74rem; color: #8a9a8a; margin: 0; }
.facts dd { margin: 0; font-size: 0.8rem; font-weight: 600; text-align: right; overflow-wrap: anywhere; }
.block { margin-top: 14px; padding-top: 12px; border-top: 1px solid #d9e3dc; }
.block-head { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.block-head .link.small { margin-top: 0; display: inline-flex; align-items: center; gap: 4px; }
.block h3 { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0 0 6px; }
.txt { font-size: 0.82rem; line-height: 1.5; margin: 0 0 4px; }
.log { display: flex; gap: 8px; align-items: baseline; padding: 4px 0; font-size: 0.78rem; }
.log-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; background: #b0bab0; }
.log-dot.followed { background: #1f8f5c; }
.log-dot.partially_followed { background: #D4A017; }
.log-dot.not_followed { background: #c0392b; }
.log-main small { display: block; color: #7a8a7a; font-style: italic; }

.ok { display: flex; align-items: center; gap: 6px; color: #1f6f46; font-size: 0.8rem; font-weight: 600; margin: 0; }

.client .rnd-card { display: flex; gap: 12px; align-items: center; margin-bottom: 14px; }
.rnd-photo { width: 52px; height: 52px; border-radius: 50%; background: #e3efe7; color: #1e4a26; display: flex; align-items: center; justify-content: center; font-weight: 700; object-fit: cover; flex-shrink: 0; }
.rnd-name { font-family: 'Playfair Display', serif; font-weight: 700; margin: 0; }
.check { margin: 0; padding-left: 18px; font-size: 0.8rem; line-height: 1.7; color: #3a4a3a; }

.overlay { position: fixed; inset: 0; background: rgba(5, 15, 10, 0.55); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 300; }
.unsaved { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #1f4a30; background: #fff; border: 1.5px dashed #3f9a6b; border-radius: 10px; padding: 9px 12px; margin: 0 0 12px; }
.unsaved svg { flex-shrink: 0; color: #3f9a6b; }
.todo { list-style: none; margin: 0 0 8px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.todo li { border: 1.5px dashed #3f9a6b; border-radius: 10px; padding: 9px 12px; }
.todo .nm-panel-link { font-size: 0.86rem; white-space: normal; }
.ok-icon { color: #1f8f5c; vertical-align: -3px; }
.finish-choices { display: flex; flex-direction: column; gap: 8px; margin: 4px 0 6px; }
.choice { display: flex; align-items: flex-start; gap: 12px; width: 100%; text-align: left; background: #fff; border: 1px solid #d9e3dc; border-radius: 12px; padding: 12px 14px; font-family: inherit; color: #1a3a1a; cursor: pointer; }
.choice:hover:not(:disabled) { border-color: #1f6f46; background: #f6faf7; }
.choice:disabled { opacity: 0.55; cursor: not-allowed; }
.choice svg { flex-shrink: 0; margin-top: 1px; color: #5a6a5a; }
.choice span { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.choice strong { font-size: 0.9rem; }
.choice small { font-size: 0.76rem; color: #6a7a6a; line-height: 1.4; }
.choice.main { background: linear-gradient(135deg, #00382a 0%, #005a42 100%); border-color: #00382a; color: #fff; }
.choice.main svg { color: #e2c25e; }
.choice:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.choice.main small { color: #c4d6c9; }
.choice.main:hover:not(:disabled) { background: linear-gradient(135deg, #00402f 0%, #00684c 100%); border-color: #00402f; }
.ns-label { display: block; font-size: 0.8rem; font-weight: 600; margin-bottom: 4px; }
.ns-text { width: 100%; resize: vertical; }
.ns-hint { font-size: 0.72rem; color: #8a9a8a; margin: 4px 0 10px; }
.ns-hint.bad { color: #c0392b; }

@media (max-width: 1100px) { .body.rnd .panel { width: 400px; } }
@media (max-width: 860px) {
  .room { height: auto; min-height: 100vh; }
  .body, .body.rnd { flex-direction: column; }
  .stage { height: 52vh; flex: none; }
  .panel, .body.rnd .panel { width: 100%; border-radius: 14px 14px 0 0; min-height: 60vh; }
  .ncp-wrap { height: auto; }
  .who-text small { display: none; }
  .bar-right { width: 100%; justify-content: flex-end; flex-wrap: wrap; }
}
</style>
