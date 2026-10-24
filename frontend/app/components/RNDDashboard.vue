<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>

    <!-- BANNER (design A layout on the app's dark green, 2026-10-14; nm-hero in portal.css):
         greeting + today's summary on the left, the next consultation on the right. -->
    <section class="nm-hero">
      <div class="nm-hero-greet">
        <p class="nm-hero-date">{{ longToday }}</p>
        <h1 class="nm-hero-title">Good {{ partOfDay }}, {{ auth.user?.first_name }}</h1>
        <p v-if="d" class="nm-hero-sub">{{ summaryLine }}</p>
      </div>
      <div v-if="d" class="nm-upnext">
        <template v-if="d.next_up">
          <div class="nm-upnext-top">
            <span class="nm-upnext-label">Up next, {{ dayWord(d.next_up.scheduled_at) === 'Today' ? 'today' : dayWord(d.next_up.scheduled_at).replace(/^Tomorrow/, 'tomorrow') }} at {{ clock(d.next_up.scheduled_at) }}</span>
            <span class="nm-upnext-pay" :class="{ unpaid: d.next_up.payment !== 'paid' }">{{ d.next_up.payment === 'paid' ? 'Paid' : 'Not paid yet' }}</span>
          </div>
          <div class="nm-upnext-row">
            <div class="nm-upnext-who">
              <img v-if="d.next_up.client.profile_photo" :src="d.next_up.client.profile_photo" alt="" class="nm-upnext-avatar" />
              <span v-else class="nm-upnext-avatar">{{ nameInitials(d.next_up.client.name) }}</span>
              <div class="nm-upnext-name-wrap">
                <p class="nm-upnext-name">{{ d.next_up.client.name }}</p>
                <p class="nm-upnext-format">{{ d.next_up.type_label }} consultation</p>
              </div>
            </div>
            <div class="nm-upnext-actions">
              <NuxtLink v-if="canJoin(d.next_up)" :to="`/consultation-room/${d.next_up.id}`" class="nm-hero-btn primary"><Video :size="16" /> Join now</NuxtLink>
              <span v-else-if="d.next_up.type !== 'in_person'" class="nm-hero-btn primary waiting"><Video :size="16" /> Join opens {{ dayWord(d.next_up.join_opens_at) === 'Today' ? '' : `${dayWord(d.next_up.join_opens_at).split(',')[0].replace(/^Tomorrow/, 'tomorrow')} ` }}{{ clock(d.next_up.join_opens_at) }}</span>
              <NuxtLink :to="`/client-detail/${d.next_up.relationship_id}`" class="nm-hero-btn">Open patient</NuxtLink>
            </div>
          </div>
        </template>
        <template v-else>
          <p class="nm-upnext-label">Up next</p>
          <p class="nm-upnext-empty">No consultations coming up.</p>
          <div class="nm-upnext-actions"><NuxtLink to="/appointments" class="nm-hero-btn">View appointments</NuxtLink></div>
        </template>
      </div>
    </section>

    <!-- "Needs you": one panel, ranked: patient risks (red), then unfinished setup
         and records (dashed green mark), then the to-do chips -->
    <section v-if="d" class="nm-panel needs" aria-label="Needs you">
      <p v-if="allClear" class="all-clear"><CheckCircle2 :size="16" /> All caught up. Nothing is waiting on you.</p>
      <template v-else>
        <ul v-if="riskAlerts.length" class="needs-band">
          <li v-for="(a, i) in riskAlerts" :key="`risk-${i}`" class="needs-row risk" :style="{ '--i': i }">
            <component :is="ALERT_ICONS[a.level]" :size="16" class="needs-icon" aria-hidden="true" />
            <span class="needs-text"><strong>{{ a.client.name }}: {{ noDot(a.title) }}.</strong> {{ a.detail }}</span>
            <NuxtLink :to="a.link" class="nm-panel-link">{{ a.action }}</NuxtLink>
          </li>
        </ul>
        <ul v-if="hasUnfinished" class="needs-band">
          <li v-if="requiredMissing.length" class="needs-row unfinished">
            <span class="needs-text"><strong>Finish your profile so clients can book you.</strong> Still to do: {{ requiredMissing.map(m => m.label.toLowerCase()).join('; ') }}.</span>
            <NuxtLink :to="requiredMissing.length === 1 && requiredMissing[0].key === 'availability' ? '/profile-settings?tab=availability' : '/profile-settings'" class="nm-panel-link">Complete profile</NuxtLink>
          </li>
          <li v-if="needsClinicAddress" class="needs-row unfinished">
            <span class="needs-text"><strong>Add your clinic address.</strong> Clients can't book your in-person consultations until it's added.</span>
            <NuxtLink to="/profile-settings" class="nm-panel-link">Add address</NuxtLink>
          </li>
          <li v-if="!d.earnings.has_payout_account" class="needs-row unfinished">
            <span class="needs-text"><strong>Add your payout details.</strong> Earnings are sent every 5th to your e-wallet or bank<template v-if="Number(d.earnings.pending) + Number(d.earnings.posted) > 0">, and {{ peso(Number(d.earnings.pending) + Number(d.earnings.posted)) }} is waiting</template>.</span>
            <NuxtLink to="/earnings?payout=1" class="nm-panel-link">Add payout details</NuxtLink>
          </li>
          <li v-for="(a, i) in infoAlerts" :key="`info-${i}`" class="needs-row unfinished">
            <span class="needs-text"><strong>{{ a.client.name }}: {{ noDot(a.title) }}.</strong> {{ a.detail }}</span>
            <NuxtLink :to="a.link" class="nm-panel-link">{{ a.action }}</NuxtLink>
          </li>
        </ul>
        <p v-if="moreAlerts" class="needs-more">
          {{ moreAlerts }} more patient alert{{ moreAlerts === 1 ? '' : 's' }}.
          <NuxtLink to="/my-patients?filter=attention" class="nm-panel-link">See all in My Patients</NuxtLink>
        </p>
        <div v-if="todoItems.length" class="needs-chips">
          <NuxtLink v-for="(t, i) in todoItems" :key="t.key" :to="t.to" class="todo-item" :style="{ '--i': i }">
            <component :is="t.icon" :size="15" class="todo-icon" aria-hidden="true" />
            <span><strong>{{ t.count }}</strong> {{ t.label }}</span>
          </NuxtLink>
        </div>
      </template>
    </section>

    <div v-if="loading" class="nm-panel"><p class="nm-muted">Loading your dashboard…</p></div>

    <template v-else-if="d">
      <div class="nm-grid">
        <div class="nm-col">
          <!-- bento, same as Appointments: this week's consultations as the big green cell, two rows beside it; sits beside Booking requests -->
          <div class="nm-panel bento">
            <NuxtLink to="/appointments?tab=upcoming" class="bento-main">
              <span class="bento-label">Consultations this week</span>
              <strong class="bento-big">{{ d.stats.sessions_this_week }}</strong>
              <span class="bento-note">{{ todayCount }} today</span>
            </NuxtLink>
            <div class="bento-rows">
              <NuxtLink to="/my-patients" class="bento-row">
                <span>Active patients</span>
                <strong>{{ d.stats.active_patients }}</strong>
              </NuxtLink>
              <NuxtLink to="/meal-planning" class="bento-row">
                <span>Meal-plan adherence<small>{{ deltaText.toLowerCase() }}</small></span>
                <strong>{{ d.adherence.pct == null ? '—' : `${d.adherence.pct}%` }}</strong>
              </NuxtLink>
            </div>
          </div>
          <!-- schedule -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <div>
                <h2 class="nm-panel-title">Today &amp; the next 7 days</h2>
                <p class="nm-panel-sub">Confirmed consultations</p>
              </div>
              <NuxtLink to="/appointments" class="nm-panel-link">All appointments</NuxtLink>
            </div>
            <p v-if="!confirmedSchedule.length" class="nm-muted empty-line">Nothing confirmed for this week.</p>
            <div v-for="group in scheduleByDay" :key="group.key" class="day-group">
              <p class="day-label">{{ group.label }}</p>
              <div v-for="a in group.items" :key="a.id" class="sched-row">
                <span class="sched-time">{{ clock(a.scheduled_at) }}</span>
                <img v-if="a.client.profile_photo" :src="a.client.profile_photo" class="nm-avatar" alt="" />
                <span v-else class="nm-avatar">{{ nameInitials(a.client.name) }}</span>
                <span class="sched-main">
                  <NuxtLink :to="`/client-detail/${a.relationship_id}`" class="nm-row-title link">{{ a.client.name }}</NuxtLink>
                  <span class="nm-row-sub">{{ a.type_label }}, {{ a.duration_minutes }} min</span>
                </span>
                <span class="sched-end">
                  <span v-if="a.payment === 'paid'" class="nm-pill green">Paid</span>
                  <span v-else class="nm-pill muted">Not paid yet</span>
                  <NuxtLink v-if="canJoin(a)" :to="`/consultation-room/${a.id}`" class="nm-btn-dark nm-btn-sm"><Video :size="13" /> Join</NuxtLink>
                </span>
              </div>
            </div>
            <p v-if="d.requests.length" class="req-pointer">
              {{ d.requests.length }} booking request{{ d.requests.length === 1 ? ' is' : 's are' }} waiting for your answer, under Booking requests.
            </p>
          </div>

          <!-- adherence chart -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <div>
                <h2 class="nm-panel-title">Meal-plan adherence, last 7 days</h2>
                <p class="nm-panel-sub">Share of planned meals your patients followed. Partly followed counts as half, and an unlogged meal counts as missed.</p>
              </div>
              <div v-if="d.adherence.pct != null" class="chart-figure">
                <span class="cf-value">{{ d.adherence.pct }}%</span>
                <span class="cf-sub">{{ d.adherence.logged }} of {{ d.adherence.planned }} meals logged<template v-if="d.adherence.waiting">, {{ d.adherence.waiting }} waiting for your rating</template></span>
              </div>
            </div>
            <p v-if="!d.adherence.planned" class="nm-muted empty-line">No meal plans active yet. Adherence shows up once patients have a sent plan.</p>
            <div v-else class="chart" role="img" :aria-label="`Meal-plan adherence by day: ${chartSummary}`">
              <div class="chart-plot">
                <div v-for="t in [100, 50, 0]" :key="t" class="grid" :style="{ bottom: `${t}%` }"><span>{{ t }}%</span></div>
                <div class="goal" :style="{ bottom: `${d.adherence.goal}%` }"><span>Goal {{ d.adherence.goal }}%</span></div>
                <div class="cols">
                  <div v-for="(day, i) in d.adherence.days" :key="day.date" class="col" tabindex="0"
                       :aria-label="colLabel(day, i)" @mouseenter="hover = i" @mouseleave="hover = null" @focus="hover = i" @blur="hover = null">
                    <span v-if="day.followed_pct == null" class="no-data" title="No meals planned">–</span>
                    <span v-else class="bar" :class="{ today: i === 6 }" :style="{ height: `${Math.max(day.followed_pct, 1.5)}%` }" />
                    <div v-if="hover === i" class="tip" :class="{ left: i > 4 }">
                      <strong>{{ tipDay(day.date, i) }}</strong>
                      <span v-if="day.followed_pct == null">No meals planned</span>
                      <template v-else>
                        <span>{{ day.followed_pct }}% followed</span>
                        <span class="tip-muted">{{ day.logged }} of {{ day.planned }} meals logged{{ i === 6 ? ' so far' : '' }}</span>
                      </template>
                    </div>
                  </div>
                </div>
              </div>
              <div class="chart-x">
                <span v-for="(day, i) in d.adherence.days" :key="day.date" :class="{ today: i === 6 }">{{ i === 6 ? 'Today' : weekday(day.date) }}</span>
              </div>
              <table class="sr-only">
                <caption>Meal-plan adherence by day</caption>
                <thead><tr><th>Day</th><th>Followed</th><th>Meals logged</th></tr></thead>
                <tbody><tr v-for="day in d.adherence.days" :key="day.date"><td>{{ day.date }}</td><td>{{ day.followed_pct ?? 'none planned' }}</td><td>{{ day.logged }} / {{ day.planned }}</td></tr></tbody>
              </table>
            </div>
          </div>

        </div>

        <div class="nm-col">
          <!-- requests -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <div>
                <h2 class="nm-panel-title">Booking requests</h2>
                <p class="nm-panel-sub">Confirm before the time passes. The client pays after you confirm.</p>
              </div>
            </div>
            <p v-if="!d.requests.length" class="nm-muted">No requests waiting.</p>
            <div v-for="a in d.requests" :key="a.id" class="nm-row">
              <img v-if="a.client.profile_photo" :src="a.client.profile_photo" class="nm-avatar" alt="" />
              <span v-else class="nm-avatar">{{ nameInitials(a.client.name) }}</span>
              <div class="nm-row-main">
                <p class="nm-row-title">{{ a.client.name }}</p>
                <p class="nm-row-sub">{{ a.type_label }}, {{ dayWord(a.scheduled_at) }}, {{ clock(a.scheduled_at) }}</p>
                <p class="req-soon" :class="{ urgent: hoursUntil(a.scheduled_at) < SOON_HOURS }">{{ startsIn(a.scheduled_at) }}</p>
              </div>
              <NuxtLink to="/appointments?tab=requests" class="nm-btn-dark nm-btn-sm">Review</NuxtLink>
            </div>
          </div>

          <!-- earnings -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <h2 class="nm-panel-title">Earnings</h2>
              <NuxtLink to="/earnings" class="nm-panel-link">Open Earnings</NuxtLink>
            </div>
            <div class="money">
              <p class="sr-only">{{ ringLabel }}</p>
              <div class="earn-ring" :style="{ background: ringFill }" aria-hidden="true">
                <div class="earn-hole">
                  <span class="earn-total">{{ pesoShort(earnTotal) }}</span>
                  <span class="earn-caption">earned so far</span>
                </div>
              </div>
              <ul class="money-legend">
                <li v-for="x in earnSlices" :key="x.key">
                  <span class="swatch" :style="{ background: x.color }" />
                  <span class="m-label">{{ x.label }}</span>
                  <strong>{{ peso(x.value) }}</strong>
                </li>
              </ul>
            </div>
            <p class="nm-hint">
              Next payout {{ shortDate(d.earnings.next_payout_date) }}<template v-if="!d.earnings.eligible">. It needs {{ peso(d.earnings.minimum_payout) }} posted and your payout details</template>.
            </p>
          </div>

          <!-- reviews -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <h2 class="nm-panel-title">Latest reviews</h2>
              <NuxtLink v-if="d.rating?.count" to="/reviews" class="overall" :aria-label="`Average ${d.rating.average} out of 5 from ${d.rating.count} reviews. Open Reviews`">
                <span class="overall-star" aria-hidden="true">★</span>
                <strong>{{ d.rating.average.toFixed(1) }}</strong>
                <span>from {{ d.rating.count }} review{{ d.rating.count === 1 ? '' : 's' }}</span>
              </NuxtLink>
            </div>
            <p v-if="!d.reviews.length" class="nm-muted" style="margin-top: 10px">No reviews yet.</p>
            <div v-for="(r, i) in d.reviews" :key="i" class="review">
              <p class="stars">{{ '★'.repeat(r.rating) }}<span>{{ '★'.repeat(5 - r.rating) }}</span></p>
              <p v-if="r.comment" class="review-text">"{{ r.comment }}"</p>
              <p class="nm-row-sub">{{ r.client }}, {{ shortDate(r.created_at) }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import {
  AlertTriangle, CalendarDays, CheckCircle2, ClipboardList, FlaskConical, Info, MessageSquare,
  OctagonAlert, Target, Users, Utensils, Video, Wallet,
} from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'


const { get } = useApi()
const auth = useAuthStore()
const now = useNow()

const ALERT_ICONS = { critical: OctagonAlert, warning: AlertTriangle, info: Info }

const d = ref(null)
const loading = ref(true)
const error = ref('')
const hover = ref(null)
const setupMissing = ref([])

async function load() {
  error.value = ''
  try {
    d.value = await get('/rnd/dashboard/')
  } catch {
    error.value = 'Could not load your dashboard.'
  } finally {
    loading.value = false
  }
}
onMounted(async () => {
  load()
  try {
    setupMissing.value = (await get('/auth/me/onboarding/')).missing || []
  } catch {
    setupMissing.value = []
  }
})
// patient alerts (critical first, as the API sends them); only the first few up top
const MAX_ALERTS = 3
const shownAlerts = computed(() => (d.value?.alerts || []).slice(0, MAX_ALERTS))
const moreAlerts = computed(() => Math.max((d.value?.alerts || []).length - MAX_ALERTS, 0))
const noDot = t => String(t || '').replace(/[.\s]+$/, '')
const riskAlerts = computed(() => shownAlerts.value.filter(a => a.level !== 'info'))
const infoAlerts = computed(() => shownAlerts.value.filter(a => a.level === 'info'))
const hasUnfinished = computed(() => !!(requiredMissing.value.length || needsClinicAddress.value || !d.value?.earnings.has_payout_account || infoAlerts.value.length))
const allClear = computed(() => !riskAlerts.value.length && !hasUnfinished.value && !moreAlerts.value && !todoItems.value.length)
const requiredMissing = computed(() => setupMissing.value.filter(m => !m.optional))
const needsClinicAddress = computed(() => setupMissing.value.some(m => m.key === 'clinic_address'))

const PH = { timeZone: 'Asia/Manila' }
const phDate = v => new Date(v).toLocaleDateString('en-CA', PH)
const todayIso = phDate(new Date())
const partOfDay = (() => {
  const h = Number(new Date().toLocaleString('en-US', { ...PH, hour: 'numeric', hour12: false }))
  return h < 12 ? 'morning' : h < 18 ? 'afternoon' : 'evening'
})()

const todoItems = computed(() => {
  const t = d.value?.todo
  if (!t) return []
  return [
    { key: 'done', count: t.to_complete, label: `consultation${t.to_complete === 1 ? '' : 's'} to mark complete`, to: '/appointments?tab=to_complete', icon: ClipboardList },
    { key: 'ncp', count: t.ncp_drafts, label: `NCP draft${t.ncp_drafts === 1 ? '' : 's'} to finish`, to: '/ncp-records', icon: ClipboardList },
    { key: 'plan', count: t.need_meal_plan, label: `patient${t.need_meal_plan === 1 ? '' : 's'} ready for a meal plan`,
      to: t.need_meal_plan_first ? `/meal-planning?relationship=${t.need_meal_plan_first}` : '/meal-planning', icon: Target },
    { key: 'logs', count: t.meal_logs_to_review, label: `meal log${t.meal_logs_to_review === 1 ? '' : 's'} to rate`,
      to: t.meal_logs_to_review_first ? `/client-detail/${t.meal_logs_to_review_first}?tab=meal` : '/my-patients', icon: Utensils },
    { key: 'labs', count: t.lab_results_to_review, label: `lab result${t.lab_results_to_review === 1 ? '' : 's'} to review`,
      to: t.lab_results_to_review_first ? `/client-detail/${t.lab_results_to_review_first}?tab=labs` : '/my-patients', icon: FlaskConical },
    { key: 'msg', count: t.unread_messages, label: `unread message${t.unread_messages === 1 ? '' : 's'}`, to: '/messages', icon: MessageSquare },
  ].filter(i => i.count > 0)
})

const todayCount = computed(() => (d.value?.schedule || []).filter(a => phDate(a.scheduled_at) === todayIso).length)

/* ---------- banner ---------- */
const longToday = new Date().toLocaleDateString('en-PH', { ...PH, weekday: 'long', month: 'long', day: 'numeric' })
const todayConfirmed = computed(() => (d.value?.schedule || []).filter(a => a.status === 'confirmed' && phDate(a.scheduled_at) === todayIso))
function untilText(v) {
  const mins = Math.round((new Date(v) - now.value) / 60000)
  if (mins <= 0) return 'now'
  if (mins < 60) return `in ${mins} minute${mins === 1 ? '' : 's'}`
  const h = Math.round(mins / 60)
  return `in about ${h} hour${h === 1 ? '' : 's'}`
}
const summaryLine = computed(() => {
  const next = d.value?.next_up
  const n = todayConfirmed.value.length
  if (n) {
    const count = `You have ${n} consultation${n === 1 ? '' : 's'} today.`
    if (next && phDate(next.scheduled_at) === todayIso) {
      const started = new Date(next.scheduled_at) <= now.value
      return started ? `${count} Your consultation with ${next.client.first_name} is happening now.`
        : `${count} Your ${next.id === todayConfirmed.value[0]?.id ? 'first' : 'next'} one starts ${untilText(next.scheduled_at)}.`
    }
    return `${count} You're done with them for the day.`
  }
  if (next) return `No consultations today. Your next one is ${dayWord(next.scheduled_at, true).replace(/^Tomorrow/, 'tomorrow')} at ${clock(next.scheduled_at)}.`
  return 'No consultations coming up. Your schedule is clear.'
})
// The schedule shows only what's confirmed; requests live in Booking requests.
const confirmedSchedule = computed(() => (d.value?.schedule || []).filter(a => a.status === 'confirmed'))
const scheduleByDay = computed(() => {
  const groups = []
  for (const a of confirmedSchedule.value) {
    const key = phDate(a.scheduled_at)
    let g = groups.find(x => x.key === key)
    if (!g) groups.push(g = { key, label: dayWord(a.scheduled_at, true), items: [] })
    g.items.push(a)
  }
  return groups
})

const deltaText = computed(() => {
  const a = d.value?.adherence
  if (!a || a.pct == null) return 'Last 7 days'
  if (a.previous_pct == null) return 'Last 7 days'
  const diff = a.pct - a.previous_pct
  return diff === 0 ? 'Same as the week before' : `${diff > 0 ? '+' : '−'}${Math.abs(diff)} pts vs the week before`
})
/* earnings ring: pending, posted, paid out, light to dark green as the money moves */
const earnSlices = computed(() => {
  const e = d.value?.earnings || {}
  return [
    { key: 'pending', label: 'Pending', value: Number(e.pending) || 0, color: '#cfe6d8' },
    { key: 'posted', label: 'Posted', value: Number(e.posted) || 0, color: '#7cc09c' },
    { key: 'paid', label: 'Paid out', value: Number(e.paid_out) || 0, color: '#1f8f5c' },
  ]
})
const earnTotal = computed(() => earnSlices.value.reduce((n, x) => n + x.value, 0))
// the ring is a CSS conic gradient: each state takes its share of the circle
const ringFill = computed(() => {
  const total = earnTotal.value
  if (!total) return '#eef1ee'
  let at = 0
  const stops = earnSlices.value.filter(x => x.value > 0).map((x) => {
    const from = at
    at += (x.value / total) * 360
    return `${x.color} ${from}deg ${at}deg`
  })
  return `conic-gradient(${stops.join(', ')})`
})
const ringLabel = computed(() => `${peso(earnTotal.value)} earned so far: ${earnSlices.value.map(x => `${x.label} ${peso(x.value)}`).join(', ')}`)
function pesoShort(n) {
  if (n >= 1e6) return `₱${(n / 1e6).toFixed(1).replace(/\.0$/, '')}M`
  if (n >= 1e5) return `₱${Math.round(n / 1e3)}k`
  return `₱${Math.round(n).toLocaleString('en-PH')}`
}

function canJoin(a) {
  return a.status === 'confirmed' && a.type === 'video' && now.value >= new Date(a.join_opens_at) && now.value <= new Date(a.join_closes_at)
}
function clock(v) {
  return new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
}
// Booking requests: how soon each starts. Under SOON_HOURS it turns red,
// because an unconfirmed request lapses once its time passes.
const SOON_HOURS = 6
function hoursUntil(v) {
  return (new Date(v).getTime() - now.value) / 3600000
}
function startsIn(v) {
  const h = hoursUntil(v)
  if (h < 1) return `Starts in ${Math.max(1, Math.round(h * 60))} min`
  if (h < 24) return `Starts in ${Math.round(h)} hour${Math.round(h) === 1 ? '' : 's'}`
  const days = Math.round(h / 24)
  return `Starts in ${days} day${days === 1 ? '' : 's'}`
}
function dayWord(v, long = false) {
  const day = phDate(v)
  if (day === todayIso) return 'Today'
  if (day === phDate(Date.now() + 86400000)) return 'Tomorrow'
  return new Date(v).toLocaleDateString('en-PH', { ...PH, weekday: long ? 'long' : 'short', month: 'short', day: 'numeric' })
}
function weekday(iso) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { weekday: 'short' })
}
function tipDay(iso, i) {
  return i === 6 ? 'Today' : new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { weekday: 'long', month: 'short', day: 'numeric' })
}
function colLabel(day, i) {
  const name = tipDay(day.date, i)
  return day.followed_pct == null ? `${name}: no meals planned` : `${name}: ${day.followed_pct}% followed, ${day.logged} of ${day.planned} meals logged`
}
const chartSummary = computed(() => (d.value?.adherence.days || []).map((x, i) => `${i === 6 ? 'today' : weekday(x.date)} ${x.followed_pct ?? 'none'}`).join(', '))
function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}
</script>

<style scoped>

.all-clear { display: flex; align-items: center; gap: 8px; color: #1f6f46; font-size: 0.86rem; font-weight: 600; margin: 0; }

.day-group + .day-group { margin-top: 14px; }
.day-label { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.sched-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.sched-time { width: 66px; font-size: 0.84rem; font-weight: 700; color: #1a3a1a; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.sched-main { flex: 1; min-width: 140px; display: flex; flex-direction: column; }
.sched-end { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.link { text-decoration: none; }
.link:hover { text-decoration: underline; }

/* adherence chart — one series: one hue, today in the accent step, no legend */
.nm-panel-head > div:first-child { flex: 1 1 260px; min-width: 0; }
.chart-figure { text-align: right; flex-shrink: 0; white-space: nowrap; margin-left: auto; }
.cf-value { display: block; font-size: 1.6rem; font-weight: 700; color: #1a3a1a; line-height: 1.1; font-variant-numeric: tabular-nums; }
.cf-sub { font-size: 0.74rem; color: #8a9a8a; }
.chart { margin-top: 6px; }
.chart-plot { position: relative; height: 170px; margin: 10px 0 0 34px; }
.grid { position: absolute; left: 0; right: 0; border-top: 1px solid #eef1ee; }
.grid span { position: absolute; left: -34px; top: -8px; width: 28px; text-align: right; font-size: 0.68rem; color: #9aaa9a; font-variant-numeric: tabular-nums; }
.goal { position: absolute; left: 0; right: 0; border-top: 1px solid #8a9a8a; }
.goal span { position: absolute; right: 0; top: -17px; font-size: 0.68rem; font-weight: 600; color: #6a7a6a; background: #fff; padding: 0 4px; }
.cols { position: absolute; inset: 0; display: flex; }
.col { flex: 1; position: relative; display: flex; align-items: flex-end; justify-content: center; cursor: default; outline: none; }
.col:hover, .col:focus-visible { background: rgba(31, 143, 92, 0.05); border-radius: 6px; }
.bar { width: 24px; max-width: 60%; background: #a8d8bf; border-radius: 4px 4px 0 0; transition: background 0.15s; }
.bar.today { background: #1f8f5c; }
.col:hover .bar:not(.today), .col:focus-visible .bar:not(.today) { background: #7cc39f; }
.no-data { font-size: 0.8rem; color: #b0bab0; margin-bottom: 2px; }
.tip { position: absolute; bottom: calc(100% - 8px); left: 50%; transform: translateX(-50%); background: #1a3a1a; color: #fff; border-radius: 8px; padding: 8px 10px; font-size: 0.74rem; white-space: nowrap; display: flex; flex-direction: column; gap: 2px; z-index: 5; box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15); pointer-events: none; }
.tip.left { left: auto; right: 0; transform: none; }
.tip-muted { color: #b9cdbf; }
.chart-x { display: flex; margin-left: 34px; border-top: 1px solid #dfe5df; padding-top: 6px; }
.chart-x span { flex: 1; text-align: center; font-size: 0.72rem; color: #8a9a8a; }
.chart-x span.today { color: #1a3a1a; font-weight: 700; }
/* display: block — a <table> ignores width/height, so without it the hidden
   table keeps its full size and stretches the page below the layout. */
.sr-only { position: absolute; display: block; width: 1px; height: 1px; margin: -1px; padding: 0; border: 0; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

/* money / reviews */
/* bento (same as Appointments): green cell + three divided rows */
.bento { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.6fr); padding: 0; overflow: hidden; }
.bento a { color: inherit; text-decoration: none; }
.bento a:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.bento-main { display: flex; flex-direction: column; justify-content: center; gap: 0; padding: 14px 20px; background: linear-gradient(135deg, #00382a 0%, #005a42 100%); }
.bento .bento-main { color: #fff; }
.bento .bento-main:hover { background: linear-gradient(135deg, #00402f 0%, #00684c 100%); }
.bento .bento-main:focus-visible { outline: 2px solid #f3d27a; outline-offset: -3px; }
.bento-label { font-size: 0.84rem; font-weight: 600; color: #e2c25e; }
.bento-big { font-family: 'Playfair Display', serif; font-size: 2.2rem; font-weight: 700; line-height: 1.1; color: #fff; font-variant-numeric: tabular-nums lining-nums; }
.bento-note { font-size: 0.8rem; color: #cfe0d5; }
.bento-rows { display: flex; flex-direction: column; background: #fbfcfa; }
.bento-row { flex: 1; display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 7px 20px; font-size: 0.84rem; font-weight: 600; color: #3a4a3a; }
.bento-row:hover { background: #f4f7f4; }
.bento .bento-row + .bento-row { border-top: 1px solid #d9e3dc; }
.bento-row small { display: inline; font-size: 0.74rem; font-weight: 400; color: #7a8a7a; margin-left: 6px; }
.bento-row strong { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; font-variant-numeric: tabular-nums lining-nums; white-space: nowrap; }
.empty-line { margin: 12px 0 4px; }
/* "Needs you" panel */
.needs { padding: 0; overflow: hidden; margin-bottom: 20px; }
.needs .all-clear { padding: 14px 20px; }
.needs-band { list-style: none; margin: 0; padding: 0; }
.needs > * + * { border-top: 1px solid #d9e3dc; }
.needs-row { display: flex; align-items: center; gap: 12px; padding: 12px 20px; font-size: 0.86rem; color: #3a4a3a; line-height: 1.45; }
.needs-row + .needs-row { border-top: 1px solid #eef1ee; }
.needs-row strong { color: #1a3a1a; }
.needs-text { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.needs-row .nm-panel-link { flex-shrink: 0; white-space: nowrap; }
/* a patient risk: red, never quiet (patient safety) */
.needs-row.risk { background: #fdf3f2; }
.needs-row.risk strong { color: #a12525; }
.needs-icon { flex-shrink: 0; color: #c0392b; }
/* unfinished: the app's dashed green mark */
.needs-row.unfinished::before { content: ''; flex-shrink: 0; align-self: stretch; width: 0; border-left: 2px dashed #3f9a6b; margin: 2px 2px 2px 7px; }
.needs-more { display: flex; flex-wrap: wrap; gap: 8px; align-items: baseline; margin: 0; padding: 10px 20px; font-size: 0.82rem; color: #6a7a6a; }
.needs-chips { display: flex; flex-wrap: wrap; gap: 8px; padding: 12px 20px; background: #fbfcfa; }
.todo-item { display: inline-flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #d9e3dc; border-radius: 999px; padding: 6px 12px; text-decoration: none; color: #3a4a3a; font-size: 0.82rem; }
.todo-item:hover { border-color: #3f9a6b; color: #1a3a1a; }
.todo-item:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.todo-item strong { color: #1a3a1a; }
.todo-icon { color: #3f9a6b; }
/* one opening moment, about 3 seconds, then still: the panel drops in (no
   glow on the panel itself, only the items move): the red
   lines and dashed-green lines each glow three times, the chips pop in and glow */
@media (prefers-reduced-motion: no-preference) {
  .needs { animation: nm-drop 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
  .needs-row.risk { animation: nm-risk 1s ease-in-out 0.45s 3; }
  .needs-row.risk .needs-icon { animation: nm-shake 0.5s ease-in-out 0.6s 2; }
  .needs-row.unfinished::before { animation: nm-march 3s linear 0.45s 1; }
  .needs-row.unfinished { animation: nm-todo 1s ease-in-out 0.45s 3; }
  .needs-chips .todo-item { animation: nm-nudge 0.5s ease-out both, nm-chip-glow 1s ease-in-out 3; animation-delay: calc(0.6s + var(--i, 0) * 90ms), 0.45s; }
}
@keyframes nm-drop { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: none; } }
@keyframes nm-risk { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(192, 57, 43, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(192, 57, 43, 0.45), inset 0 0 18px rgba(192, 57, 43, 0.22); } }
@keyframes nm-todo { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(63, 154, 107, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(63, 154, 107, 0.45), inset 0 0 18px rgba(63, 154, 107, 0.2); } }
@keyframes nm-chip-glow { 0%, 100% { box-shadow: 0 0 0 0 rgba(63, 154, 107, 0); } 50% { box-shadow: 0 0 0 3px rgba(63, 154, 107, 0.25), 0 0 12px rgba(63, 154, 107, 0.35); } }
@keyframes nm-shake { 0%, 100% { transform: rotate(0); } 25% { transform: rotate(-12deg); } 75% { transform: rotate(12deg); } }
@keyframes nm-march { from { border-left-color: #3f9a6b; opacity: 1; } 25% { opacity: 0.35; } 50% { opacity: 1; } 75% { opacity: 0.35; } to { opacity: 1; } }
@keyframes nm-nudge { 0% { transform: translateY(4px); opacity: 0; } 60% { transform: translateY(-2px); opacity: 1; } 100% { transform: none; opacity: 1; } }
.req-pointer { margin: 12px 0 0; padding-top: 10px; border-top: 1px solid #f0f2f0; font-size: 0.82rem; color: #6a7a6a; }
/* the light card shadow on panels; the banner gets the stronger one */
.nm-page :deep(.nm-panel) { box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
@media (max-width: 640px) {
  .bento { grid-template-columns: minmax(0, 1fr); }
  .bento-main { padding: 12px 16px; }
  .bento-big { font-size: 1.9rem; }
  .bento-row { padding: 8px 16px; }
  .bento-row small { display: block; margin-left: 0; }
}
.money { display: grid; grid-template-columns: 108px minmax(0, 1fr); align-items: center; gap: 18px; margin-top: 14px; }
.earn-ring { width: 108px; height: 108px; border-radius: 50%; display: grid; place-items: center; }
.earn-hole { width: 88px; height: 88px; border-radius: 50%; background: #fff; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.earn-total { font-size: 0.95rem; font-weight: 700; color: #1a3a1a; font-variant-numeric: tabular-nums; line-height: 1.2; }
.earn-caption { font-size: 0.68rem; color: #8a9a8a; }
.money-legend { list-style: none; margin: 0; padding: 0; min-width: 0; }
.money-legend li { display: grid; grid-template-columns: 8px minmax(0, 1fr) auto; align-items: center; gap: 8px; padding: 6px 0; font-size: 0.84rem; color: #6a7a6a; }
.swatch { width: 8px; height: 8px; border-radius: 50%; }
.money-legend strong { color: #1a3a1a; font-weight: 600; font-variant-numeric: tabular-nums; }
.req-soon { font-size: 0.76rem; font-weight: 600; color: #1e4a26; margin: 2px 0 0; }
.req-soon.urgent { color: #c0392b; }
.overall { display: inline-flex; align-items: baseline; gap: 4px; font-size: 0.8rem; color: #4a5a4a; text-decoration: none; white-space: nowrap; }
.overall strong { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; }
.overall-star { color: #D4A017; }
.overall:hover span:last-child { text-decoration: underline; }
.overall:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; border-radius: 4px; }
.review { padding: 12px 0 0; margin-top: 12px; border-top: 1px solid #d9e3dc; }
.review:first-of-type { border-top: none; margin-top: 6px; }
.stars { margin: 0; color: #D4A017; letter-spacing: 1px; font-size: 0.86rem; }
.stars span { color: #e3e6e3; }
.review-text { font-size: 0.84rem; color: #3a4a3a; margin: 4px 0; line-height: 1.5; overflow-wrap: anywhere; }

@media (max-width: 640px) {
  .needs-row { flex-wrap: wrap; padding: 12px 16px; }
  .needs-row .needs-text { flex: 1 1 calc(100% - 40px); }
  .needs-row .nm-panel-link { margin-left: 28px; }
  .needs-row.unfinished .nm-panel-link { margin-left: 0; }
  .needs-chips, .needs-more { padding-left: 16px; padding-right: 16px; }
  .sched-end { width: 100%; padding-left: 78px; }
  .chart-figure { text-align: left; }
}

/* ===== BANNER "UP NEXT" CARD — frosted glass instead of white, gold primary button ===== */
.nm-upnext {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  color: #fff;
}

/* "Up next, tomorrow at 3:00 PM" label */
.nm-upnext-label { color: #f0c15b; }

/* Text inside the card */
.nm-upnext-empty,
.nm-upnext-name { color: #fff; }
.nm-upnext-format { color: rgba(255, 255, 255, 0.7); }

/* Patient avatar + payment pill */
.nm-upnext-avatar { background: rgba(255, 255, 255, 0.18); color: #fff; }
.nm-upnext-pay { background: rgba(255, 255, 255, 0.16); color: #fff; }
.nm-upnext-pay.unpaid { background: rgba(240, 193, 91, 0.2); color: #f0c15b; }

/* Buttons ("Open patient", "View appointments") */
.nm-upnext .nm-hero-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #fff;
}
.nm-upnext .nm-hero-btn:hover { background: rgba(255, 255, 255, 0.12); }

/* "Join now" — solid gold */
.nm-upnext .nm-hero-btn.primary {
  background: #f2b61f;
  border-color: #f2b61f;
  color: #0a4a37;
}
.nm-upnext .nm-hero-btn.primary:hover {
  background: #e0a410;
  border-color: #e0a410;
}

/* "Join opens Mon 2:45 PM" — not clickable yet, so softer gold outline */
.nm-upnext .nm-hero-btn.primary.waiting,
.nm-upnext .nm-hero-btn.primary.waiting:hover {
  background: rgba(242, 182, 31, 0.16);
  border-color: rgba(242, 182, 31, 0.5);
  color: #f0c15b;
  cursor: default;
}
</style>