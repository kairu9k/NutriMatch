<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>

    <!-- BANNER: greeting + the next consultation -->
    <section class="nm-banner">
      <h1 class="nm-banner-title">Good {{ partOfDay }}, {{ auth.user?.first_name }}</h1>
      <template v-if="d?.next_up">
        <p class="nm-banner-sub">
          Next: <strong>{{ d.next_up.client.name }}</strong> · {{ d.next_up.type_label }} · {{ dayWord(d.next_up.scheduled_at) }} at {{ clock(d.next_up.scheduled_at) }}
          <span class="pay-chip" :class="d.next_up.payment === 'paid' ? 'paid' : 'unpaid'">{{ d.next_up.payment === 'paid' ? 'Paid' : 'Not paid yet' }}</span>
        </p>
        <div class="banner-actions">
          <NuxtLink v-if="canJoin(d.next_up)" :to="`/consultation-room/${d.next_up.id}`" class="nm-btn-gold"><Video :size="15" /> Join now</NuxtLink>
          <span v-else-if="d.next_up.type === 'video'" class="nm-todo-item done"><Clock :size="14" /> Join opens at {{ clock(d.next_up.join_opens_at) }}</span>
          <NuxtLink :to="`/client-detail/${d.next_up.relationship_id}`" class="nm-todo-item">Open patient</NuxtLink>
        </div>
      </template>
      <p v-else-if="d" class="nm-banner-sub">No consultations coming up. Your schedule is clear.</p>
    </section>

    <!-- setup reminders (kept from before) -->
    <section v-if="requiredMissing.length" class="nm-note setup">
      <strong>Finish your profile so clients can book you.</strong> Still to do: {{ requiredMissing.map(m => m.label.toLowerCase()).join('; ') }}.
      <NuxtLink :to="requiredMissing.length === 1 && requiredMissing[0].key === 'availability' ? '/profile-settings?tab=availability' : '/profile-settings'" class="nm-panel-link">Complete profile →</NuxtLink>
    </section>
    <section v-if="needsClinicAddress" class="nm-note setup">
      <strong>Add your clinic address.</strong> Clients can't book your in-person consultations until it's added.
      <NuxtLink to="/profile-settings" class="nm-panel-link">Add address →</NuxtLink>
    </section>
    <section v-if="d && !d.earnings.has_payout_account" class="nm-note setup">
      <strong>Add your payout details.</strong> Earnings are sent every 5th to your GCash or bank account<template v-if="Number(d.earnings.pending) + Number(d.earnings.posted) > 0"> — {{ peso(Number(d.earnings.pending) + Number(d.earnings.posted)) }} is waiting</template>.
      <NuxtLink to="/earnings#payout-details" class="nm-panel-link">Add payout details →</NuxtLink>
    </section>

    <!-- TO DO -->
    <section v-if="d" class="todo">
      <template v-if="todoItems.length">
        <NuxtLink v-for="t in todoItems" :key="t.key" :to="t.to" class="todo-item">
          <span class="todo-icon" :class="t.tone"><component :is="t.icon" :size="15" /></span>
          <span><strong>{{ t.count }}</strong> {{ t.label }}</span>
          <ChevronRight :size="14" class="todo-chev" />
        </NuxtLink>
      </template>
      <p v-else class="all-clear"><CheckCircle2 :size="16" /> All caught up — nothing waiting on you.</p>
    </section>

    <div v-if="loading" class="nm-panel"><p class="nm-muted">Loading your dashboard…</p></div>

    <template v-else-if="d">
      <div class="nm-stat-grid">
        <div class="nm-stat-card">
          <div class="nm-stat-icon"><Users :size="17" /></div>
          <p class="nm-stat-value">{{ d.stats.active_patients }}</p>
          <p class="nm-stat-label">Active patients</p>
          <NuxtLink to="/my-patients" class="nm-stat-note good" style="text-decoration: none">View patients →</NuxtLink>
        </div>
        <div class="nm-stat-card">
          <div class="nm-stat-icon"><CalendarCheck :size="17" /></div>
          <p class="nm-stat-value">{{ d.stats.sessions_this_week }}</p>
          <p class="nm-stat-label">Consultations this week</p>
          <p class="nm-stat-note">{{ todayCount }} today</p>
        </div>
        <div class="nm-stat-card">
          <div class="nm-stat-icon gold"><Utensils :size="17" /></div>
          <p class="nm-stat-value">{{ d.adherence.pct == null ? '—' : `${d.adherence.pct}%` }}</p>
          <p class="nm-stat-label">Meal-plan adherence</p>
          <p class="nm-stat-note" :class="deltaClass">{{ deltaText }}</p>
        </div>
        <div class="nm-stat-card">
          <div class="nm-stat-icon gold"><Wallet :size="17" /></div>
          <p class="nm-stat-value">{{ peso(d.earnings.posted) }}</p>
          <p class="nm-stat-label">Ready for the {{ shortDate(d.earnings.next_payout_date) }} payout</p>
          <p class="nm-stat-note">{{ peso(d.earnings.pending) }} still pending</p>
        </div>
      </div>

      <div class="nm-grid">
        <div class="nm-col">
          <!-- schedule -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <div>
                <h2 class="nm-panel-title">Today &amp; the next 7 days</h2>
                <p class="nm-panel-sub">Confirmed and requested consultations</p>
              </div>
              <NuxtLink to="/appointments" class="nm-panel-link">Appointments →</NuxtLink>
            </div>
            <div v-if="!d.schedule.length" class="nm-empty"><CalendarDays :size="26" /><p>Nothing scheduled this week.</p></div>
            <div v-for="group in scheduleByDay" :key="group.key" class="day-group">
              <p class="day-label">{{ group.label }}</p>
              <div v-for="a in group.items" :key="a.id" class="sched-row">
                <span class="sched-time">{{ clock(a.scheduled_at) }}</span>
                <img v-if="a.client.profile_photo" :src="a.client.profile_photo" class="nm-avatar" alt="" />
                <span v-else class="nm-avatar">{{ nameInitials(a.client.name) }}</span>
                <span class="sched-main">
                  <NuxtLink :to="`/client-detail/${a.relationship_id}`" class="nm-row-title link">{{ a.client.name }}</NuxtLink>
                  <span class="nm-row-sub">{{ a.type_label }} · {{ a.duration_minutes }} min</span>
                </span>
                <span class="sched-end">
                  <span v-if="a.status === 'pending'" class="nm-pill gold">Needs your confirmation</span>
                  <span v-else-if="a.payment === 'paid'" class="nm-pill green">Paid</span>
                  <span v-else class="nm-pill muted">Not paid yet</span>
                  <NuxtLink v-if="canJoin(a)" :to="`/consultation-room/${a.id}`" class="nm-btn-dark nm-btn-sm"><Video :size="13" /> Join</NuxtLink>
                </span>
              </div>
            </div>
          </div>

          <!-- adherence chart -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <div>
                <h2 class="nm-panel-title">Meal-plan adherence, last 7 days</h2>
                <p class="nm-panel-sub">Share of planned meals your patients followed (partly followed counts half; unlogged counts as missed).</p>
              </div>
              <div v-if="d.adherence.pct != null" class="chart-figure">
                <span class="cf-value">{{ d.adherence.pct }}%</span>
                <span class="cf-sub">{{ d.adherence.logged }} of {{ d.adherence.planned }} meals logged<template v-if="d.adherence.waiting"> · {{ d.adherence.waiting }} waiting for your rating</template></span>
              </div>
            </div>
            <div v-if="!d.adherence.planned" class="nm-empty"><Utensils :size="26" /><p>No meal plans active yet — adherence shows up once patients have a plan.</p></div>
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

          <!-- attention -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <div>
                <h2 class="nm-panel-title">Patients needing attention</h2>
                <p class="nm-panel-sub">Flagged from meal logs, screenings, progress records and NCP drafts.</p>
              </div>
            </div>
            <p v-if="!d.alerts.length" class="all-clear"><CheckCircle2 :size="16" /> No patients need attention right now.</p>
            <div v-for="(a, i) in d.alerts" :key="i" class="alert" :class="a.level">
              <span class="alert-icon"><component :is="ALERT_ICONS[a.level]" :size="15" /></span>
              <div class="alert-main">
                <p class="nm-row-title">{{ a.client.name }} — {{ a.title }}</p>
                <p class="nm-row-sub">{{ a.detail }}</p>
              </div>
              <NuxtLink :to="a.link" class="nm-btn-outline nm-btn-sm">{{ a.action }}</NuxtLink>
            </div>
          </div>
        </div>

        <div class="nm-col">
          <!-- requests -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <div>
                <h2 class="nm-panel-title">Booking requests</h2>
                <p class="nm-panel-sub">Confirm before the time passes — the client pays after you confirm.</p>
              </div>
            </div>
            <p v-if="!d.requests.length" class="nm-muted">No requests waiting.</p>
            <div v-for="a in d.requests" :key="a.id" class="nm-row">
              <img v-if="a.client.profile_photo" :src="a.client.profile_photo" class="nm-avatar" alt="" />
              <span v-else class="nm-avatar">{{ nameInitials(a.client.name) }}</span>
              <div class="nm-row-main">
                <p class="nm-row-title">{{ a.client.name }}</p>
                <p class="nm-row-sub">{{ a.type_label }} · {{ dayWord(a.scheduled_at) }}, {{ clock(a.scheduled_at) }}</p>
              </div>
              <NuxtLink to="/appointments" class="nm-btn-dark nm-btn-sm">Review</NuxtLink>
            </div>
          </div>

          <!-- outcomes -->
          <div class="nm-panel">
            <h2 class="nm-panel-title">Patient outcomes</h2>
            <p class="nm-panel-sub">From your active patients' progress records and NCP follow-ups.</p>
            <div class="outcomes">
              <div class="outcome">
                <span class="o-value">{{ d.outcomes.avg_weight_change_kg == null ? '—' : `${signed(d.outcomes.avg_weight_change_kg)} kg` }}</span>
                <span class="o-label">Average weight change</span>
                <span class="o-note">{{ d.outcomes.weight_patients ? `across ${d.outcomes.weight_patients} patient${d.outcomes.weight_patients === 1 ? '' : 's'}` : 'needs 2+ progress records' }}</span>
              </div>
              <div class="outcome">
                <span class="o-value">{{ d.outcomes.bmi_compared ? `${d.outcomes.bmi_improved} of ${d.outcomes.bmi_compared}` : '—' }}</span>
                <span class="o-label">Improved their BMI</span>
                <span class="o-note">since their screening</span>
              </div>
              <div class="outcome">
                <span class="o-value">{{ goalsTotal ? `${d.outcomes.goals.met} of ${goalsTotal}` : '—' }}</span>
                <span class="o-label">Follow-up goals met</span>
                <span class="o-note">{{ goalsTotal ? `${d.outcomes.goals.partially_met} partly · ${d.outcomes.goals.ongoing} ongoing` : 'from finalized follow-ups' }}</span>
              </div>
            </div>
          </div>

          <!-- earnings -->
          <div class="nm-panel">
            <div class="nm-panel-head">
              <h2 class="nm-panel-title">Earnings</h2>
              <NuxtLink to="/earnings" class="nm-panel-link">Earnings →</NuxtLink>
            </div>
            <div class="money">
              <p><span>Pending</span><strong>{{ peso(d.earnings.pending) }}</strong></p>
              <p><span>Posted</span><strong>{{ peso(d.earnings.posted) }}</strong></p>
              <p><span>Paid out</span><strong>{{ peso(d.earnings.paid_out) }}</strong></p>
            </div>
            <p class="nm-hint">
              Next payout {{ shortDate(d.earnings.next_payout_date) }}<template v-if="!d.earnings.eligible"> — needs {{ peso(d.earnings.minimum_payout) }} posted and payout details</template>.
            </p>
          </div>

          <!-- reviews -->
          <div class="nm-panel">
            <h2 class="nm-panel-title">Latest reviews</h2>
            <p v-if="!d.reviews.length" class="nm-muted" style="margin-top: 10px">No reviews yet.</p>
            <div v-for="(r, i) in d.reviews" :key="i" class="review">
              <p class="stars">{{ '★'.repeat(r.rating) }}<span>{{ '★'.repeat(5 - r.rating) }}</span></p>
              <p v-if="r.comment" class="review-text">"{{ r.comment }}"</p>
              <p class="nm-row-sub">{{ r.client }} · {{ shortDate(r.created_at) }}</p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import {
  AlertTriangle, CalendarCheck, CalendarDays, CheckCircle2, ChevronRight, ClipboardList, Clock, Info, MessageSquare,
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
    { key: 'req', count: t.requests, label: `booking request${t.requests === 1 ? '' : 's'} to confirm`, to: '/appointments', icon: CalendarCheck, tone: 'gold' },
    { key: 'done', count: t.to_complete, label: `consultation${t.to_complete === 1 ? '' : 's'} to mark complete`, to: '/appointments', icon: ClipboardList, tone: 'gold' },
    { key: 'ncp', count: t.ncp_drafts, label: `NCP draft${t.ncp_drafts === 1 ? '' : 's'} to finish`, to: '/ncp-records', icon: ClipboardList, tone: '' },
    { key: 'plan', count: t.need_meal_plan, label: `patient${t.need_meal_plan === 1 ? '' : 's'} ready for a meal plan`,
      to: t.need_meal_plan_first ? `/meal-planning?relationship=${t.need_meal_plan_first}` : '/meal-planning', icon: Target, tone: '' },
    { key: 'logs', count: t.meal_logs_to_review, label: `meal log${t.meal_logs_to_review === 1 ? '' : 's'} to rate`,
      to: t.meal_logs_to_review_first ? `/client-detail/${t.meal_logs_to_review_first}?tab=meal` : '/my-patients', icon: Utensils, tone: 'gold' },
    { key: 'msg', count: t.unread_messages, label: `unread message${t.unread_messages === 1 ? '' : 's'}`, to: '/messages', icon: MessageSquare, tone: '' },
  ].filter(i => i.count > 0)
})

const todayCount = computed(() => (d.value?.schedule || []).filter(a => phDate(a.scheduled_at) === todayIso).length)
const scheduleByDay = computed(() => {
  const groups = []
  for (const a of d.value?.schedule || []) {
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
const deltaClass = computed(() => {
  const a = d.value?.adherence
  if (!a || a.pct == null || a.previous_pct == null) return ''
  return a.pct > a.previous_pct ? 'good' : a.pct < a.previous_pct ? 'warn' : ''
})
const goalsTotal = computed(() => Object.values(d.value?.outcomes.goals || {}).reduce((n, x) => n + x, 0))

function canJoin(a) {
  return a.status === 'confirmed' && ['video', 'chat'].includes(a.type) && now.value >= new Date(a.join_opens_at) && now.value <= new Date(a.join_closes_at)
}
function clock(v) {
  return new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
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
const signed = v => `${Number(v) > 0 ? '+' : Number(v) < 0 ? '−' : ''}${Math.abs(Number(v)).toFixed(1)}`
function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}
</script>

<style scoped>
.nm-banner-sub strong { color: #fff; }
.pay-chip { display: inline-block; margin-left: 8px; font-size: 0.7rem; font-weight: 700; padding: 2px 9px; border-radius: 10px; vertical-align: 1px; }
.pay-chip.paid { background: rgba(255, 255, 255, 0.16); color: #d8f0e0; }
.pay-chip.unpaid { background: #D4A017; color: #1a3a1a; }
.banner-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.setup { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: baseline; }

.todo { display: flex; flex-wrap: wrap; gap: 10px; margin: 0 0 20px; }
.todo-item { display: inline-flex; align-items: center; gap: 10px; background: #fff; border: 1px solid #eceeec; border-radius: 12px; padding: 10px 14px; text-decoration: none; color: #1a3a1a; font-size: 0.84rem; }
.todo-item:hover { border-color: #c7d6ca; }
.todo-icon { width: 28px; height: 28px; border-radius: 8px; background: #eef3ec; color: #1e4a26; display: flex; align-items: center; justify-content: center; }
.todo-icon.gold { background: #fdf1d6; color: #b8860b; }
.todo-chev { color: #b0bab0; }
.all-clear { display: flex; align-items: center; gap: 8px; color: #1f6f46; font-size: 0.86rem; font-weight: 600; margin: 0; }

.day-group + .day-group { margin-top: 14px; }
.day-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #8a9a8a; margin: 0 0 4px; }
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

/* attention */
.alert { display: flex; gap: 12px; align-items: flex-start; padding: 12px 0; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.alert:first-of-type { border-top: none; }
.alert-icon { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #eef3ec; color: #1e4a26; }
.alert.critical .alert-icon { background: #fdecec; color: #a12525; }
.alert.warning .alert-icon { background: #fdf1d6; color: #b8860b; }
.alert-main { flex: 1; min-width: 180px; }

/* outcomes / money / reviews */
.outcomes { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 14px; }
.outcome { background: #fafbfa; border: 1px solid #f0f2f0; border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.o-value { font-size: 1.15rem; font-weight: 700; color: #1a3a1a; font-variant-numeric: tabular-nums; }
.o-label { font-size: 0.76rem; font-weight: 600; color: #4a5a4a; }
.o-note { font-size: 0.7rem; color: #9aaa9a; }
.money { margin-top: 10px; }
.money p { display: flex; justify-content: space-between; margin: 0; padding: 8px 0; border-top: 1px solid #f0f2f0; font-size: 0.86rem; color: #4a5a4a; }
.money p:first-child { border-top: none; }
.money strong { color: #1a3a1a; font-variant-numeric: tabular-nums; }
.review { padding: 12px 0 0; margin-top: 12px; border-top: 1px solid #f0f2f0; }
.review:first-of-type { border-top: none; margin-top: 6px; }
.stars { margin: 0; color: #D4A017; letter-spacing: 1px; font-size: 0.86rem; }
.stars span { color: #e3e6e3; }
.review-text { font-size: 0.84rem; color: #3a4a3a; margin: 4px 0; line-height: 1.5; overflow-wrap: anywhere; }

@media (max-width: 640px) {
  .outcomes { grid-template-columns: minmax(0, 1fr); }
  .todo-item { width: 100%; }
  .sched-end { width: 100%; padding-left: 78px; }
  .chart-figure { text-align: left; }
}
</style>
