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
              <small>{{ clock(appt.scheduled_at) }}–{{ clock(endsAt) }} · {{ typeLabel }}</small>
            </span>
          </span>
        </template>
      </div>
      <div class="bar-right">
        <span v-if="appt && appt.status === 'confirmed'" class="timer" :class="timerTone">{{ timerText }}</span>
        <button v-if="isRnd && appt?.status === 'confirmed' && windowState !== 'early'" type="button" class="end-btn" @click="openEnd">
          <PhoneOff :size="15" /> End &amp; mark complete
        </button>
        <button type="button" class="exit-btn" @click="exitRoom"><ArrowLeft :size="15" /> Exit</button>
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
          <button type="button" class="link" @click="summaryOpen = true">View the summary →</button>
          <button type="button" class="link" @click="exitRoom">Back →</button>
        </div>
        <div v-else-if="appt.status !== 'confirmed'" class="state-card">
          <VideoOff :size="28" /><p>This consultation {{ appt.status === 'cancelled' ? 'was cancelled' : 'isn\'t confirmed yet' }}.</p>
          <button type="button" class="link" @click="exitRoom">Back →</button>
        </div>
        <!-- Pay first: the API only sends the client the room link once it's paid. -->
        <div v-else-if="!isRnd && appt.payment?.status === 'unpaid'" class="state-card">
          <VideoOff :size="28" />
          <p>Your consultation opens once it's paid. Pay {{ peso(appt.payment.amount) }} before {{ clock(appt.scheduled_at) }} to join.</p>
          <NuxtLink to="/appointments" class="link">Go to My Appointments to pay →</NuxtLink>
        </div>
        <div v-else-if="windowState === 'early'" class="state-card">
          <Clock :size="28" />
          <p class="big">Opens in {{ untilOpen }}</p>
          <p>The room opens {{ clock(appt.join_opens_at) }}, 15 minutes before the start. This page opens it automatically.</p>
        </div>
        <div v-else-if="windowState === 'closed'" class="state-card">
          <VideoOff :size="28" /><p>This consultation's room has closed.</p>
          <button v-if="isRnd" type="button" class="link" @click="openEnd">Mark it complete →</button>
        </div>
        <div v-else-if="!appt.video_session_url" class="state-card"><VideoOff :size="28" /><p>No video room has been set up for this consultation.</p></div>
        <iframe v-else :src="appt.video_session_url" class="video" title="Video consultation" allow="camera; microphone; fullscreen; display-capture; autoplay" />
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
              <div><span>Adherence · 7d</span><strong>{{ p.adherence?.pct != null ? `${p.adherence.pct}%` : '—' }}</strong><small>{{ p.adherence ? `${p.adherence.logged} of ${p.adherence.planned} logged` : 'no active plan' }}</small></div>
              <div :class="{ risk: (s.screening?.nrs_score ?? 0) >= 3 }"><span>NRS-2002</span><strong>{{ s.screening?.nrs_score ?? '—' }}</strong><small>{{ s.screening?.nrs_risk || '' }}</small></div>
            </div>
            <dl class="facts">
              <div><dt>Age · sex</dt><dd>{{ [p.client.age != null ? `${p.client.age} y/o` : null, SEX[p.client.sex]].filter(Boolean).join(' · ') || '—' }}</dd></div>
              <div><dt>Conditions</dt><dd>{{ list(s.health.conditions) }}</dd></div>
              <div><dt>Diet</dt><dd>{{ list(s.health.dietary_restrictions) }}</dd></div>
              <div v-if="s.health.religion"><dt>Religion</dt><dd>{{ s.health.religion }}</dd></div>
              <div><dt>Goals</dt><dd>{{ list(s.health.health_goals) }}</dd></div>
              <div v-if="s.screening"><dt>BMR · TDEE</dt><dd>{{ whole(s.screening.bmr_kcal) }} · {{ whole(s.screening.tdee_kcal) }} kcal</dd></div>
            </dl>
            <section class="block">
              <h3>Current care plan</h3>
              <template v-if="s.care_plan">
                <p v-if="s.care_plan.pes_problem" class="txt"><strong>{{ s.care_plan.pes_problem }}</strong><template v-if="s.care_plan.pes_etiology"> related to {{ s.care_plan.pes_etiology }}</template>.</p>
                <p v-if="s.care_plan.diet_prescription" class="txt">{{ s.care_plan.diet_prescription }}</p>
                <p v-if="s.care_plan.target_kcal" class="muted">Target {{ whole(s.care_plan.target_kcal) }} kcal/day{{ s.care_plan.target_carb_g ? ` · ${whole(s.care_plan.target_carb_g)} g carbs · ${whole(s.care_plan.target_protein_g)} g protein · ${whole(s.care_plan.target_fat_g)} g fat` : '' }}</p>
              </template>
              <p v-else class="muted">No finalized NCP record yet.</p>
            </section>
            <section v-if="s.recent_logs.length" class="block">
              <h3>Recent meal logs</h3>
              <div v-for="(l, i) in s.recent_logs.slice(0, 6)" :key="i" class="log">
                <span class="log-dot" :class="l.status" aria-hidden="true" />
                <span class="log-main">{{ shortDate(l.date) }} · {{ l.meal }} — {{ LOG[l.status] }}<small v-if="l.note">“{{ l.note }}”</small></span>
              </div>
            </section>
            <NuxtLink :to="`/client-detail/${appt.relationship.id}`" target="_blank" class="link small">Open full chart in a new tab ↗</NuxtLink>
          </template>

          <!-- NCP (the same form as the chart, inline) -->
          <div v-show="tab === 'ncp'" class="ncp-wrap">
            <NcpRecordModal v-if="ncpMounted" ref="ncpForm" inline :relationship-id="appt.relationship.id" :patient-name="other.name"
                            :appointment-id="appt.id" @changed="refreshSummary" />
          </div>

          <!-- PROGRESS -->
          <template v-if="s && tab === 'progress'">
            <form class="prog" @submit.prevent="saveProgress">
              <p class="muted">Measured during this consultation — saved to {{ p.client.first_name }}'s progress for {{ shortDate(todayIso) }}. BMI is worked out from their screening height.</p>
              <div class="prog-grid">
                <label><span>Weight (kg)</span><input v-model="pf.weight_kg" type="number" step="0.1" class="nm-input" :class="{ bad: pfErr.weight_kg }" /><em v-if="pfErr.weight_kg">{{ pfErr.weight_kg }}</em></label>
                <label><span>Blood pressure</span><input v-model="pf.blood_pressure" type="text" inputmode="numeric" placeholder="120/80" class="nm-input" /></label>
                <label><span>Fasting glucose (mg/dL)</span><input v-model="pf.blood_glucose" type="number" class="nm-input" :class="{ bad: pfErr.blood_glucose }" /><em v-if="pfErr.blood_glucose">{{ pfErr.blood_glucose }}</em></label>
                <label><span>HbA1c (%)</span><input v-model="pf.hba1c" type="number" step="0.1" class="nm-input" :class="{ bad: pfErr.hba1c }" /><em v-if="pfErr.hba1c">{{ pfErr.hba1c }}</em></label>
              </div>
              <label class="full"><span><Lock :size="12" /> Private note (only you see this)</span><textarea v-model="pf.rnd_notes" rows="2" maxlength="2000" class="nm-input" /></label>
              <p v-if="pfError" class="nm-field-error">{{ pfError }}</p>
              <p v-if="pfSaved" class="ok"><CheckCircle2 :size="14" /> Saved — {{ p.client.first_name }} can see it on their Progress page.</p>
              <button type="submit" class="nm-btn-dark" :disabled="pfSaving || Object.keys(pfErr).length > 0">{{ pfSaving ? 'Saving…' : 'Save progress' }}</button>
            </form>
            <section v-if="s.progress.length" class="block">
              <h3>Earlier records</h3>
              <div v-for="r in s.progress.slice(0, 4)" :key="r.id" class="log">
                <span class="log-main">{{ shortDate(r.record_date) }} · {{ r.weight_kg != null ? `${fmt1(r.weight_kg)} kg` : '—' }}{{ r.blood_pressure ? ` · BP ${r.blood_pressure}` : '' }}{{ r.blood_glucose != null ? ` · FBS ${r.blood_glucose}` : '' }}</span>
              </div>
            </section>
          </template>
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
            <p v-if="info.meal_plan.target_kcal" class="muted">{{ whole(info.meal_plan.target_kcal) }} kcal a day{{ info.meal_plan.target_carb_g ? ` · ${whole(info.meal_plan.target_carb_g)} g carbs · ${whole(info.meal_plan.target_protein_g)} g protein · ${whole(info.meal_plan.target_fat_g)} g fat` : '' }}</p>
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

    <!-- END & MARK COMPLETE -->
    <div v-if="endOpen" class="overlay" @click.self="!ending && (endOpen = false)">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="end-title">
        <template v-if="!wrap">
          <h2 id="end-title" class="nm-modal-title">End and mark this consultation complete?</h2>
          <p class="nm-modal-text">
            {{ other.name }} · {{ clock(appt.scheduled_at) }}–{{ clock(endsAt) }}.
            <template v-if="appt.payment?.status === 'paid'">Your share posts 3 days after today. This can't be undone.</template>
          </p>
          <p v-if="appt.payment && appt.payment.status !== 'paid'" class="nm-field-error">It hasn't been paid, so it can't be completed.</p>
          <p v-if="ncpDirty" class="warn"><AlertTriangle :size="14" /> Your NCP form has unsaved changes — they'll be saved as a draft first.</p>
          <p v-if="endError" class="nm-field-error">{{ endError }}</p>
          <div class="nm-modal-actions">
            <button type="button" class="nm-btn-outline" :disabled="ending" @click="endOpen = false">Not yet</button>
            <button type="button" class="nm-btn-dark" :disabled="ending || (appt.payment && appt.payment.status !== 'paid')" @click="completeNow">{{ ending ? 'Completing…' : 'Mark complete' }}</button>
          </div>
        </template>
        <template v-else>
          <h2 id="end-title" class="nm-modal-title"><CheckCircle2 :size="18" class="ok-icon" /> Consultation complete</h2>
          <p class="nm-modal-text">{{ wrap.todo.length ? 'Before you move on:' : 'Everything for this visit is done.' }}</p>
          <ul v-if="wrap.todo.length" class="todo">
            <li v-for="t in wrap.todo" :key="t.text"><NuxtLink :to="t.link" class="nm-panel-link">{{ t.text }} →</NuxtLink></li>
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
    <ConsultationSummaryModal v-if="summaryOpen && appt" :appointment-id="appt.id" :role="isRnd ? 'rnd' : 'client'" @close="summaryOpen = false" />
  </div>
</template>

<script setup>
// The consultation room. RND: video + a work panel (Patient · NCP · Progress)
// and "End & mark complete" with a wrap-up of what's left. Client: video +
// their RND, the consultation time and their meal-plan targets — never NCP
// drafts or the RND's notes. Pay-first and the join window are enforced by the
// API (the client gets the room link only when it's paid and inside the window).
import {
  AlertTriangle, ArrowLeft, CheckCircle2, ClipboardList, Clock, LineChart, Lock, PhoneOff, User, VideoOff,
} from 'lucide-vue-next'
import { rangeError } from '~/utils/ncp'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { get, patch, post } = useApi()
const now = useNow(15000)
const isRnd = computed(() => auth.user?.role === 'rnd')
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
  return { name: u ? `${u.first_name} ${u.last_name}` : '', photo: u?.profile_photo || null }
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
// The client gets the room link only inside the window — fetch it when it opens.
let refetched = false
watch(windowState, (state, prev) => {
  if (prev === 'early' && state === 'open' && !refetched) { refetched = true; loadAppointment() }
})

/* ---------- RND panel ---------- */
const RND_TABS = [
  { key: 'patient', label: 'Patient', icon: User },
  { key: 'ncp', label: 'NCP', icon: ClipboardList },
  { key: 'progress', label: 'Progress', icon: LineChart },
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

/* ---------- quick progress ---------- */
const blankPf = () => ({ weight_kg: '', blood_pressure: '', blood_glucose: '', hba1c: '', rnd_notes: '' })
const pf = ref(blankPf())
const pfSaving = ref(false)
const pfError = ref('')
const pfSaved = ref(false)
const pfErr = computed(() => {
  const e = {}
  for (const f of ['weight_kg', 'blood_glucose', 'hba1c']) { const x = rangeError(f, pf.value[f]); if (x) e[f] = x }
  return e
})
async function saveProgress() {
  pfError.value = ''
  pfSaved.value = false
  const body = { relationship: appt.value.relationship.id, record_date: todayIso }
  for (const k of Object.keys(pf.value)) { const v = String(pf.value[k] ?? '').trim(); if (v) body[k] = v }
  if (!['weight_kg', 'blood_pressure', 'blood_glucose', 'hba1c'].some(k => body[k])) { pfError.value = 'Enter at least one measurement.'; return }
  pfSaving.value = true
  try {
    await post(`/rnd/relationships/${appt.value.relationship.id}/progress/`, body)
    pf.value = blankPf()
    pfSaved.value = true
    progressSavedHere.value = true
    await refreshSummary()
  } catch (e) {
    pfError.value = apiError(e, 'Could not save this record.')
  } finally {
    pfSaving.value = false
  }
}
const progressSavedHere = ref(false)

/* ---------- end & mark complete ---------- */
const summaryOpen = ref(false)
const endOpen = ref(false)
const ending = ref(false)
const endError = ref('')
const wrap = ref(null)
function openEnd() {
  endError.value = ''
  wrap.value = null
  endOpen.value = true
}
async function completeNow() {
  ending.value = true
  endError.value = ''
  try {
    if (ncpDirty.value && ncpForm.value?.saveDraft) await ncpForm.value.saveDraft()
    await patch(`/rnd/appointments/${apptId}/complete/`)
    await loadAppointment()
    await refreshSummary()
    const rel = appt.value.relationship.id
    const todo = []
    if (s.value?.ncp_draft_id) todo.push({ text: 'Finish and finalize the NCP record', link: `/client-detail/${rel}?tab=ncp&open=draft` })
    else if (!s.value?.care_plan || s.value.care_plan.encounter_date < todayIso) todo.push({ text: 'Write an NCP record for this visit', link: `/client-detail/${rel}?tab=ncp` })
    if (!(progressSavedHere.value || s.value?.progress[0]?.record_date === todayIso)) todo.push({ text: 'Record today\'s progress', link: `/client-detail/${rel}?tab=progress` })
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
function exitRoom() {
  if (ncpDirty.value) { leaveAsk.value = true; return }
  leave()
}
function leave() {
  leaveAsk.value = false
  endOpen.value = false
  if (window.history.length > 1) router.back()
  else navigateTo('/appointments')
}
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
.bar-avatar { width: 32px; height: 32px; border-radius: 50%; background: #D4A017; color: #1a3a1a; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0; object-fit: cover; }
.who-text { display: flex; flex-direction: column; min-width: 0; }
.who-text strong { font-size: 0.88rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.who-text small { font-size: 0.72rem; color: #a9c2b0; }
.timer { font-size: 0.78rem; font-weight: 700; padding: 5px 10px; border-radius: 999px; background: rgba(255, 255, 255, 0.1); font-variant-numeric: tabular-nums; white-space: nowrap; }
.timer.soon { background: #D4A017; color: #1a3a1a; }
.timer.over { background: #c0392b; }
.end-btn, .exit-btn { display: inline-flex; align-items: center; gap: 6px; border-radius: 999px; padding: 7px 14px; font-family: inherit; font-size: 0.8rem; font-weight: 700; cursor: pointer; white-space: nowrap; }
.end-btn { background: #c0392b; color: #fff; border: none; }
.end-btn:hover { background: #a93226; }
.exit-btn { background: rgba(255, 255, 255, 0.1); color: #fff; border: 1px solid rgba(255, 255, 255, 0.2); }

.body { flex: 1; display: flex; min-height: 0; }
.stage { flex: 1; display: flex; align-items: center; justify-content: center; min-width: 0; min-height: 0; }
.video { width: 100%; height: 100%; border: none; }
.state-card { display: flex; flex-direction: column; align-items: center; gap: 10px; max-width: 340px; text-align: center; color: #a9c2b0; font-size: 0.88rem; padding: 20px; }
.state-card p { margin: 0; line-height: 1.5; }
.state-card .big { font-size: 1.4rem; font-weight: 700; color: #fff; }
.state-card.err { color: #f3b8b8; }
.link { background: none; border: none; padding: 0; font-family: inherit; color: #D4A017; font-weight: 700; font-size: 0.85rem; text-decoration: none; cursor: pointer; }
.panel .link { color: #1f6f46; }
.link.small { font-size: 0.78rem; display: inline-block; margin-top: 12px; }

.panel { width: 340px; background: #f9faf8; display: flex; flex-direction: column; flex-shrink: 0; min-height: 0; border-radius: 14px 0 0 0; overflow: hidden; }
.body.rnd .panel { width: 460px; }
.tabs { display: flex; gap: 4px; padding: 10px 12px; border-bottom: 1px solid #eceeec; background: #fff; }
.tab { flex: 1; display: inline-flex; align-items: center; justify-content: center; gap: 6px; border: none; background: none; padding: 8px; border-radius: 999px; font-family: inherit; font-size: 0.8rem; font-weight: 600; color: #6a7a6a; cursor: pointer; }
.tab.on { background: #14301a; color: #fff; }
.panel-body { flex: 1; overflow-y: auto; padding: 16px; min-height: 0; }
.ncp-wrap { height: 100%; margin: -16px; }
.ncp-wrap :deep(.ncp.is-inline) { border: none; border-radius: 0; }
.muted { font-size: 0.8rem; color: #7a8a7a; margin: 0; line-height: 1.5; }
.muted.small { margin-top: 14px; }

.allergy { display: flex; align-items: center; gap: 6px; background: #fdf1d6; color: #8a5a00; border-radius: 8px; padding: 8px 10px; font-size: 0.82rem; font-weight: 700; margin: 0 0 10px; }
.note { background: #fff; border: 1px solid #eceeec; border-radius: 8px; padding: 8px 10px; font-size: 0.82rem; font-style: italic; margin: 0 0 12px; display: flex; flex-direction: column; gap: 2px; }
.note small { font-style: normal; color: #8a9a8a; font-size: 0.7rem; }
.stats { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-bottom: 12px; }
.stats div { background: #fff; border: 1px solid #eceeec; border-radius: 10px; padding: 9px 10px; display: flex; flex-direction: column; min-width: 0; }
.stats div.risk { border-color: #f3c9c9; background: #fff8f8; }
.stats span { font-size: 0.66rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #8a9a8a; }
.stats strong { font-size: 1.05rem; font-variant-numeric: tabular-nums; }
.stats small { font-size: 0.7rem; color: #8a9a8a; }
.facts { margin: 0 0 4px; }
.facts div { display: flex; justify-content: space-between; gap: 10px; padding: 6px 0; border-top: 1px solid #eef1ee; }
.facts div:first-child { border-top: none; }
.facts dt { font-size: 0.74rem; color: #8a9a8a; margin: 0; }
.facts dd { margin: 0; font-size: 0.8rem; font-weight: 600; text-align: right; overflow-wrap: anywhere; }
.block { margin-top: 14px; padding-top: 12px; border-top: 1px solid #eceeec; }
.block h3 { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #6a7a6a; margin: 0 0 6px; }
.txt { font-size: 0.82rem; line-height: 1.5; margin: 0 0 4px; }
.log { display: flex; gap: 8px; align-items: baseline; padding: 4px 0; font-size: 0.78rem; }
.log-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; background: #b0bab0; }
.log-dot.followed { background: #1f8f5c; }
.log-dot.partially_followed { background: #D4A017; }
.log-dot.not_followed { background: #c0392b; }
.log-main small { display: block; color: #7a8a7a; font-style: italic; }

.prog { display: flex; flex-direction: column; gap: 10px; }
.prog-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.prog label { display: flex; flex-direction: column; gap: 4px; font-size: 0.76rem; font-weight: 600; }
.prog label span { display: inline-flex; align-items: center; gap: 4px; }
.prog em { font-style: normal; color: #c0392b; font-size: 0.7rem; }
.nm-input.bad { border-color: #e0a3a3; background: #fffafa; }
.ok { display: flex; align-items: center; gap: 6px; color: #1f6f46; font-size: 0.8rem; font-weight: 600; margin: 0; }

.client .rnd-card { display: flex; gap: 12px; align-items: center; margin-bottom: 14px; }
.rnd-photo { width: 52px; height: 52px; border-radius: 50%; background: #D4A017; color: #1a3a1a; display: flex; align-items: center; justify-content: center; font-weight: 700; object-fit: cover; flex-shrink: 0; }
.rnd-name { font-family: 'Playfair Display', serif; font-weight: 700; margin: 0; }
.check { margin: 0; padding-left: 18px; font-size: 0.8rem; line-height: 1.7; color: #3a4a3a; }

.overlay { position: fixed; inset: 0; background: rgba(5, 15, 10, 0.55); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 300; }
.warn { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; color: #8a5a00; background: #fdf6e3; border-radius: 8px; padding: 8px 10px; margin: 0 0 10px; }
.todo { margin: 0 0 6px; padding-left: 18px; line-height: 1.9; }
.ok-icon { color: #1f8f5c; vertical-align: -3px; }

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
