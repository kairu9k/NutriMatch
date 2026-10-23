<template>
  <!-- Client home — one page, real data only. The "next step" banner follows
       where the client is in their journey (screen → find an RND → booking
       → consultation → meal plan). Sections with nothing to show explain
       what fills them, instead of showing placeholder data. -->
  <div class="client-dashboard">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-else-if="isLoading" class="placeholder-text">Loading…</p>

    <template v-else>
      <!-- BANNER (same design as the RND dashboard, nm-hero in portal.css):
           greeting + the next step on the left; the next consultation, or the
           next step when there isn't one, in the "Up next" card on the right. -->
      <section class="nm-hero">
        <div class="nm-hero-greet">
          <p class="nm-hero-date">{{ longToday }}</p>
          <h1 class="nm-hero-title">Hi {{ auth.user?.first_name }}, welcome back.</h1>
          <p class="nm-hero-sub">{{ nextStep.text }}</p>
        </div>
        <!-- UP NEXT: the time is the one big thing; the RND under a thin line;
             the status is a dot and a word. A button shows only when there's
             something to do right here (join, view a waiting booking). -->
        <div class="nm-upnext up">
          <template v-if="upNext">
            <div class="up-top">
              <span class="nm-upnext-label">Up next</span>
              <span class="up-status" :class="upNext.state"><span class="up-dot" aria-hidden="true" />{{ upNext.pill }}</span>
            </div>
            <!-- same shape as the empty card: text left, the one button centred on the right -->
            <div class="up-empty">
              <div class="up-empty-text">
                <p class="up-time">{{ upNext.time }}</p>
                <p class="up-when">{{ whenLine }}</p>
                <p class="up-with">With RND {{ upNext.name }}, {{ upNext.format.toLowerCase() }}</p>
              </div>
              <NuxtLink v-if="nextStep.action" :to="nextStep.to" class="nm-hero-btn primary up-empty-btn">
                <Video v-if="/Join/.test(nextStep.action)" :size="16" aria-hidden="true" />{{ nextStep.action }}
              </NuxtLink>
            </div>
          </template>
          <!-- nothing booked: headline on the left, the one button top right -->
          <template v-else>
            <div class="up-empty">
              <div class="up-empty-text">
                <span class="nm-upnext-label">{{ nextStep.eyebrow }}</span>
                <p class="up-time small">{{ emptyCard.headline }}</p>
                <p class="up-when">{{ emptyCard.sub }}</p>
              </div>
              <NuxtLink :to="nextStep.to" class="nm-hero-btn primary up-empty-btn">{{ nextStep.action }}</NuxtLink>
            </div>
          </template>
        </div>
      </section>

      <!-- NEEDS YOU: everything waiting on the client, same panel as the RND
           dashboard. Red = it goes wrong soon if left (payment due within a day,
           labs for a consultation within 2 days); dashed green = still to do. -->
      <section class="needs" aria-label="Needs you">
        <p v-if="!needsUrgent.length && !needsTodo.length" class="all-clear"><CheckCircle2 :size="16" aria-hidden="true" /> All caught up. Nothing is waiting on you.</p>
        <ul v-if="needsUrgent.length" class="needs-band">
          <li v-for="n in needsUrgent" :key="n.key" class="needs-row risk">
            <AlertTriangle :size="16" class="needs-icon" aria-hidden="true" />
            <span class="needs-text"><strong>{{ n.title }}</strong> {{ n.detail }}</span>
            <NuxtLink :to="n.to" class="needs-btn urgent">{{ n.action }}</NuxtLink>
          </li>
        </ul>
        <ul v-if="needsTodo.length" class="needs-band">
          <li v-for="n in needsTodo" :key="n.key" class="needs-row unfinished">
            <span class="needs-text"><strong>{{ n.title }}</strong> {{ n.detail }}</span>
            <NuxtLink :to="n.to" class="needs-btn">{{ n.action }}</NuxtLink>
          </li>
        </ul>
      </section>

      <!-- HEALTH SNAPSHOT -->
      <section class="stat-grid" aria-label="Your health at a glance">
        <div class="stat-card">
          <p class="stat-value">{{ screening ? Number(screening.bmi).toFixed(1) : '—' }}</p>
          <p class="stat-label">BMI</p>
          <p class="stat-delta" :class="screening ? bmiTone : 'neutral'">{{ screening?.bmi_category ?? 'Not yet screened' }}</p>
        </div>
        <div class="stat-card">
          <p class="stat-value">
            {{ calorieTarget.value ? calorieTarget.value.toLocaleString() : '—' }}
            <span v-if="calorieTarget.value" class="unit">kcal</span>
          </p>
          <p class="stat-label">{{ calorieTarget.label }}</p>
          <p class="stat-delta neutral">{{ calorieTarget.note }}</p>
        </div>
        <div class="stat-card">
          <p class="stat-value">{{ screening?.nrs_score ?? '—' }}</p>
          <p class="stat-label">NRS-2002 score</p>
          <p class="stat-delta" :class="screening ? nrsTone : 'neutral'">{{ screening ? nrsRiskLabel : 'Pending screening' }}</p>
        </div>
        <div class="stat-card">
          <p class="stat-value">{{ nextAppointment ? formatShortDate(nextAppointment.scheduled_at) : '—' }}</p>
          <p class="stat-label">Next consultation</p>
          <p v-if="nextAppointment" class="stat-delta" :class="nextAppointment.status === 'pending' ? 'warn' : 'neutral'">
            {{ formatTime(nextAppointment.scheduled_at) }}, {{ (APPT_TYPES[nextAppointment.type] || nextAppointment.type).toLowerCase() }}{{ nextAppointment.status === 'pending' ? ', waiting for your RND to confirm' : '' }}
          </p>
          <p v-else class="stat-delta neutral">Nothing booked yet</p>
        </div>
      </section>

      <section class="dash-grid">
        <div class="dash-col">
          <!-- TODAY'S MEAL PLAN -->
          <div class="panel">
            <div class="panel-header-row">
              <div>
                <h3 class="panel-title flush">Today's meal plan</h3>
                <p v-if="activePlan" class="panel-sub">{{ weekdayLabel }}, {{ activePlan.name || 'your meal plan' }}</p>
              </div>
              <NuxtLink v-if="activePlan" to="/meal-plan-view" class="nm-btn-soft nm-btn-sm">Log meals</NuxtLink>
            </div>

            <template v-if="activePlan">
              <div v-if="planMacros" class="macro-strip">
                <span><strong>{{ planMacros.kcal }}</strong> kcal</span>
                <span v-if="planMacros.carbs"><strong>{{ planMacros.carbs }}g</strong> carbs</span>
                <span v-if="planMacros.protein"><strong>{{ planMacros.protein }}g</strong> protein</span>
                <span v-if="planMacros.fat"><strong>{{ planMacros.fat }}g</strong> fat</span>
                <span class="macro-source">daily targets from your RND</span>
              </div>

              <ul v-if="todaysMeals.length" class="meal-list">
                <li v-for="meal in todaysMeals" :key="meal.id" class="meal-row">
                  <div class="meal-icon"><component :is="MEAL_ICONS[meal.meal_time] || Sun" :size="15" /></div>
                  <div class="meal-info">
                    <p class="meal-name">{{ MEAL_LABELS[meal.meal_time] || meal.meal_time }}</p>
                    <p class="meal-detail">
                      <template v-if="meal.scheduled_time">{{ formatClock(meal.scheduled_time) }}, </template>
                      {{ mealFoodsLabel(meal) }}
                    </p>
                  </div>
                  <span class="status-pill" :class="logPillClass(meal)">{{ logLabel(meal) }}</span>
                </li>
              </ul>
              <p v-else class="empty-note">No meals are scheduled for today in your plan.</p>

              <div class="adherence-row">
                <div class="adherence-item">
                  <p class="adherence-value">{{ todayLoggedCount }}/{{ todaysMeals.length }}</p>
                  <p class="adherence-label">meals logged today</p>
                </div>
                <div class="adherence-item">
                  <p class="adherence-value">{{ weekAdherence.logged ? `${weekAdherence.followedPct}%` : '—' }}</p>
                  <p class="adherence-label">
                    {{ weekAdherence.logged ? `followed in the last 7 days (${weekAdherence.followed} of ${weekAdherence.logged} meals your RND rated)` : 'no rated meals in the last 7 days' }}
                  </p>
                </div>
              </div>
            </template>
            <div v-else class="empty-state">
              <UtensilsCrossed :size="24" class="empty-icon" />
              <p>No meal plan yet.</p>
              <p class="empty-sub">Your RND prepares your meal plan after your consultation. It will show up here, meal by meal.</p>
            </div>
          </div>

          <!-- WEIGHT PROGRESS -->
          <div class="panel">
            <div class="panel-header-row">
              <h3 class="panel-title flush">Weight progress (kg)</h3>
              <span v-if="weightHistory.length > 1" class="panel-meta">{{ weightDeltaLabel }}</span>
            </div>
            <div v-if="weightHistory.length" class="weight-chart">
              <svg viewBox="0 0 460 110" width="100%" style="overflow: visible;" role="img" :aria-label="`Weight history, latest ${weightHistory[weightHistory.length - 1].weight} kg`">
                <defs><linearGradient id="wGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1a3a1a" stop-opacity=".12" /><stop offset="100%" stop-color="#1a3a1a" stop-opacity="0" /></linearGradient></defs>
                <g transform="translate(20,8)">
                  <polyline :points="chartPoints" stroke="#1a3a1a" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
                  <polygon :points="chartFillPoints" fill="url(#wGrad)" />
                  <circle v-for="(p, i) in chartCoords" :key="i" :cx="p.x" :cy="p.y" :r="i === chartCoords.length - 1 ? 4 : 3.5" :fill="i === chartCoords.length - 1 ? '#D4A017' : '#1a3a1a'" />
                  <text v-for="(p, i) in chartCoords" :key="'w' + i" :x="p.x" :y="p.y - 9" text-anchor="middle" font-size="9" fill="#4a5a4a" font-family="Inter, sans-serif">{{ p.weight }}</text>
                  <text v-for="(p, i) in chartCoords" :key="'l' + i" :x="p.x" y="104" text-anchor="middle" font-size="9" :fill="i === chartCoords.length - 1 ? '#D4A017' : '#8aaa8a'" :font-weight="i === chartCoords.length - 1 ? 700 : 400" font-family="Inter, sans-serif">{{ p.label }}</text>
                </g>
              </svg>
            </div>
            <p v-else class="empty-note">No weight history yet. It starts from your screening and fills in after each consultation.</p>
          </div>

          <!-- LATEST SCREENING -->
          <div class="panel">
            <h3 class="panel-title">Your screening</h3>
            <template v-if="screening">
              <p class="screening-summary-text">
                Recorded {{ formatLongDate(screening.created_at) }}, {{ Number(screening.height_cm) }} cm, {{ Number(screening.weight_kg) }} kg
              </p>
              <button type="button" class="nm-btn-soft block-wide" @click="screeningOpen = true">View screening</button>
            </template>
            <template v-else>
              <p class="screening-summary-text">Your RND needs this before your first consultation. It takes about a minute.</p>
              <NuxtLink to="/pre-consultation-screening" class="nm-btn-dark block-wide">Complete screening</NuxtLink>
            </template>
          </div>

        </div>


        <div class="dash-col">
          <!-- YOUR RND (compact, top of the column) -->
          <div class="panel rnd-compact">
            <template v-if="careRnd">
              <img v-if="careRnd.photo" :src="careRnd.photo" alt="" class="rnd-avatar rnd-avatar-img" />
              <div v-else class="rnd-avatar">{{ careRnd.initials }}</div>
              <div class="rnd-text">
                <p class="rnd-eyebrow">Your RND</p>
                <p class="rnd-name">RND {{ careRnd.name }}</p>
                <p class="rnd-specialty">
                  {{ careRnd.specialization || 'Registered Nutritionist-Dietitian' }}<template v-if="careRnd.reviewCount">, ★ {{ careRnd.rating }}</template>
                </p>
                <p v-if="careRnd.pending" class="rnd-pending">Waiting to confirm your first booking</p>
              </div>
              <div class="rnd-actions">
                <NuxtLink v-if="!careRnd.pending" to="/messages" class="icon-action" aria-label="Send a message" title="Send a message"><MessageSquare :size="16" /></NuxtLink>
                <NuxtLink :to="`/rnd-profile-view/${careRnd.id}`" class="icon-action" aria-label="View profile" title="View profile"><UserRound :size="16" /></NuxtLink>
              </div>
            </template>
            <template v-else>
              <div class="rnd-text">
                <p class="rnd-eyebrow">Your RND</p>
                <p class="rnd-specialty">You're not connected with an RND yet.</p>
              </div>
              <NuxtLink to="/find-rnd" class="nm-btn-dark nm-btn-sm">Find an RND</NuxtLink>
            </template>
          </div>

          <!-- MY TASKS (today) — tasks from the RND or the client are checkboxes;
               meals tick themselves once logged; consultations link out. -->
          <div class="panel">
            <div class="panel-header-row">
              <div>
                <h3 class="panel-title flush">My tasks</h3>
                <p v-if="taskCount" class="panel-sub">{{ doneCount }} of {{ taskCount }} done today</p>
              </div>
              <button type="button" class="nm-btn-soft nm-btn-sm" @click="addOpen = !addOpen"><Plus :size="13" aria-hidden="true" /> Add a task</button>
            </div>

            <form v-if="addOpen" class="add-task" @submit.prevent="addTask">
              <input v-model="newTask.title" class="nm-input" maxlength="120" placeholder="e.g. Walk for 20 minutes" aria-label="Task" />
              <div class="add-task-row">
                <input v-model="newTask.time" type="time" class="nm-input" aria-label="Time" />
                <select v-model="newTask.repeat" class="nm-select" aria-label="Repeat">
                  <option value="once">Today only</option>
                  <option value="daily">Every day</option>
                  <option value="weekdays">Weekdays</option>
                </select>
                <button type="submit" class="nm-btn-dark nm-btn-sm" :disabled="adding || newTask.title.trim().length < 3">{{ adding ? 'Adding…' : 'Add' }}</button>
              </div>
              <p v-if="addError" class="add-error">{{ addError }}</p>
            </form>

            <template v-for="(item, i) in todayItems" :key="item.id ? `${item.kind}${item.id}` : i">
              <label v-if="item.kind === 'task'" class="today-row task" :class="{ done: item.done }">
                <input type="checkbox" class="task-check" :checked="item.done" @change="toggleTask(item, $event.target.checked)" />
                <span class="today-main">
                  <span class="today-title">{{ item.title }}</span>
                  <span v-if="item.note" class="today-note">“{{ item.note }}”</span>
                  <span class="today-detail">{{ item.detail }}</span>
                </span>
                <span class="today-time">{{ phClock(item.at) }}</span>
                <button v-if="item.own" type="button" class="task-x" aria-label="Delete task" @click.prevent="removeTask(item)"><X :size="13" /></button>
              </label>
              <NuxtLink v-else :to="item.link" class="today-row" :class="{ done: item.done }">
                <span v-if="item.kind === 'meal' || item.kind === 'lab'" class="task-check meal" :class="{ on: item.done }" aria-hidden="true"><Check v-if="item.done" :size="12" /></span>
                <span v-else class="today-icon" :class="'k-' + item.kind"><component :is="TODAY_ICONS[item.kind]" :size="15" /></span>
                <span class="today-main">
                  <span class="today-title">{{ item.title }}</span>
                  <span v-if="item.detail" class="today-detail">{{ item.detail }}</span>
                </span>
                <span v-if="item.kind !== 'lab'" class="today-time">{{ phClock(item.at) }}</span>
              </NuxtLink>
            </template>
            <p v-if="todayLoaded && !todayItems.length" class="empty-note">No tasks for today. Tasks from your RND, meals to log and your own tasks show up here.</p>
          </div>

          <!-- UPLOAD LAB RESULTS (only once the client has an RND) -->
          <LabResultsCard @uploaded="loadToday" />

          <!-- RECENT ACTIVITY (real notifications) -->
          <div class="panel">
            <div class="panel-header-row">
              <h3 class="panel-title flush">Recent activity</h3>
              <NuxtLink v-if="notifications.length" to="/notifications" class="nm-btn-soft nm-btn-sm">View all</NuxtLink>
            </div>
            <div v-for="n in recentActivity" :key="n.id" class="activity-row">
              <span class="activity-dot" :class="{ unread: !n.is_read }"></span>
              <div class="activity-text">
                <p class="activity-title">{{ n.subject }}</p>
                <p class="activity-time">{{ timeAgo(n.created_at) }}</p>
              </div>
            </div>
            <p v-if="!recentActivity.length" class="empty-note">Nothing yet. Updates about your bookings, meal plans and payments show up here.</p>
          </div>

          
        </div>
      </section>
    </template>

    <ScreeningModal v-if="screeningOpen" @close="screeningOpen = false" />
  </div>
</template>

<script setup>
import { phIso } from '~/utils/phTime'
import { computed, onMounted, reactive, ref } from 'vue'
import {
  UtensilsCrossed, AlertTriangle, CheckCircle2, Sunrise, Sun, Moon, Coffee, AlarmClock, CalendarCheck, Check, Plus, X, MessageSquare, UserRound, Video,
} from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Dashboard' })

const auth = useAuthStore()
const { get, post, del } = useApi()

const isLoading = ref(true)
const screeningOpen = ref(false) // View Screening pop-up
const errorMessage = ref('')
const appointments = ref([])
const relationships = ref([])
const rndProfile = ref(null)
const screening = ref(null)
const mealPlans = ref([])
const mealLogs = ref([])
const invoices = ref([])
const notifications = ref([])
const labs = ref(null) // GET /client/labs/: open requests from the RND

const APPT_TYPES = { video: 'Video', chat: 'Chat', in_person: 'In person' }
const MEAL_ORDER = ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner', 'bedtime_snack']
const MEAL_LABELS = { breakfast: 'Breakfast', am_snack: 'Morning snack', lunch: 'Lunch', pm_snack: 'Afternoon snack', dinner: 'Dinner', bedtime_snack: 'Bedtime snack' }
const MEAL_ICONS = { breakfast: Sunrise, am_snack: Coffee, lunch: Sun, pm_snack: Coffee, dinner: Moon, bedtime_snack: Moon }
const LOG_LABELS = { followed: 'Followed', partially_followed: 'Partly followed', not_followed: 'Not followed' }

// Philippine dates on the server's clock.
const now = new Date()
const localIso = phIso
const todayIso = localIso(now)
const weekdayLabel = now.toLocaleDateString('en-US', { weekday: 'long' })

function formatShortDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
function formatLongDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
}
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}
function formatClock(t) {
  const [h, m] = t.split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}
function timeAgo(iso) {
  const mins = Math.round((Date.now() - new Date(iso)) / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs} hr${hrs === 1 ? '' : 's'} ago`
  const days = Math.round(hrs / 24)
  if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`
  return formatLongDate(iso)
}

/* ---------- Appointments & RND ---------- */
const activeRelationship = computed(() => relationships.value[0] || null)

// Upcoming = not cancelled/completed and not over yet (an in-progress call still counts).
const nextAppointment = computed(() => {
  const upcoming = appointments.value
    .filter(a => ['pending', 'confirmed'].includes(a.status))
    .filter(a => new Date(a.scheduled_at).getTime() + (a.duration_minutes || 60) * 60000 > Date.now())
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
  return upcoming[0] || null
})

// Most recent still-"pending" request whose time has already passed.
const expiredRequest = computed(() =>
  appointments.value
    .filter(a => a.status === 'pending' && new Date(a.scheduled_at) <= new Date())
    .sort((a, b) => new Date(b.scheduled_at) - new Date(a.scheduled_at))[0] || null
)

// The RND to show: the active care relationship, or the RND of a first
// booking that hasn't been confirmed yet.
const careRnd = computed(() => {
  const rnd = activeRelationship.value?.rnd || nextAppointment.value?.relationship?.rnd
  if (!rnd) return null
  const profile = rndProfile.value
  return {
    id: rnd.id,
    name: `${rnd.first_name} ${rnd.last_name}`,
    initials: `${rnd.first_name?.[0] || ''}${rnd.last_name?.[0] || ''}`.toUpperCase(),
    photo: profile?.user?.profile_photo || '',
    specialization: profile?.specialization || '',
    rating: profile?.average_rating ? Number(profile.average_rating).toFixed(1) : '',
    reviewCount: profile?.review_count || 0,
    pending: !activeRelationship.value,
  }
})

/* ---------- Billing ---------- */
const unpaidInvoices = computed(() => invoices.value.filter(i => i.status === 'unpaid'))

/* ---------- Needs you ---------- */
const HOUR = 3600000
const peso = v => `₱${Number(v).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
function whenShort(iso) {
  const d = new Date(iso)
  const day = d.toDateString() === new Date().toDateString() ? 'today'
    : d.toDateString() === new Date(Date.now() + 24 * HOUR).toDateString() ? 'tomorrow'
      : d.toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'short', month: 'short', day: 'numeric' })
  return `${day} at ${formatTime(iso)}`
}
const openLabRequests = computed(() => (labs.value?.requests || []).filter(r => r.status === 'open'))
function labsLeft(r) {
  const done = new Set(r.uploaded_tests || [])
  const names = r.test_names || []
  return (r.tests || []).length ? names.filter((_, i) => !done.has(r.tests[i])) : names
}
const needsUrgent = computed(() => {
  const out = []
  for (const inv of unpaidInvoices.value) {
    if (!inv.pay_by || new Date(inv.pay_by) - Date.now() > 24 * HOUR) continue
    out.push({
      key: `pay${inv.id}`, title: `Pay ${peso(inv.amount)} by ${whenShort(inv.pay_by)}.`,
      detail: "If it's still unpaid then, your consultation is cancelled.", action: 'Pay now', to: '/invoices-billing',
    })
  }
  for (const r of openLabRequests.value) {
    if (!r.needed_before || new Date(r.needed_before) - Date.now() > 48 * HOUR) continue
    out.push({
      key: `lab${r.id}`, title: `Lab results needed before your consultation ${whenShort(r.needed_before)}.`,
      detail: `Still to upload: ${labsLeft(r).join(', ')}.`, action: 'Upload', to: '/lab-results',
    })
  }
  return out
})
const needsTodo = computed(() => {
  const out = []
  const urgent = new Set(needsUrgent.value.map(n => n.key))
  if (!screening.value) {
    out.push({ key: 'screening', title: 'Complete your health screening.', detail: 'Your RND needs it before your first consultation. It takes about a minute.', action: 'Start screening', to: '/pre-consultation-screening' })
  }
  for (const inv of unpaidInvoices.value) {
    if (urgent.has(`pay${inv.id}`)) continue
    out.push({
      key: `pay${inv.id}`, title: `Pay ${peso(inv.amount)} for your consultation.`,
      detail: inv.pay_by ? `Pay before ${whenShort(inv.pay_by)}.` : 'Pay before it starts.', action: 'Pay', to: '/invoices-billing',
    })
  }
  for (const r of openLabRequests.value) {
    if (urgent.has(`lab${r.id}`)) continue
    out.push({
      key: `lab${r.id}`, title: `${r.requested_by ? `RND ${r.requested_by}` : 'Your RND'} asked for lab results.`,
      detail: `${labsLeft(r).join(', ')}${r.needed_before ? `, before ${whenShort(r.needed_before)}` : ''}.`, action: 'Upload', to: '/lab-results',
    })
  }
  if (!activeRelationship.value && expiredRequest.value && !nextAppointment.value) {
    const rnd = expiredRequest.value.relationship?.rnd
    out.push({
      key: 'expired', title: 'Your booking request wasn\'t confirmed in time.',
      detail: `The ${formatLongDate(expiredRequest.value.scheduled_at)} request${rnd ? ` with RND ${rnd.first_name} ${rnd.last_name}` : ''} has passed. Pick a new time.`,
      action: 'Book again', to: rnd ? `/rnd-profile-view/${rnd.id}?book=1` : '/find-rnd',
    })
  }
  return out
})

/* ---------- Banner "Up next" card: the next consultation, if any ---------- */
const longToday = new Date().toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' })
const upNext = computed(() => {
  const a = nextAppointment.value
  if (!a) return null
  const rnd = a.relationship?.rnd || {}
  const name = `${rnd.first_name || ''} ${rnd.last_name || ''}`.trim()
  const sameDay = new Date(a.scheduled_at).toDateString() === new Date().toDateString()
  const day = sameDay ? '' : `${new Date(a.scheduled_at).toLocaleDateString('en-PH', { weekday: 'short', month: 'short', day: 'numeric' })}, `
  const d = new Date(a.scheduled_at)
  const dayWord = sameDay ? 'Today'
    : d.toDateString() === new Date(Date.now() + 86400000).toDateString() ? 'Tomorrow'
      : d.toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'long', month: 'short', day: 'numeric' })
  const state = a.status === 'pending' ? 'waiting' : a.payment?.status === 'paid' ? 'paid' : 'unpaid'
  return {
    when: `${day}${formatTime(a.scheduled_at)}`,
    time: formatTime(a.scheduled_at),
    day: dayWord,
    startsAt: d.getTime(),
    state,
    pill: { waiting: 'Waiting for your RND', paid: 'Paid', unpaid: 'Not paid yet' }[state],
    name,
    initials: `${rnd.first_name?.[0] || ''}${rnd.last_name?.[0] || ''}`.toUpperCase(),
    photo: rnd.profile_photo || (careRnd.value?.id === rnd.id ? careRnd.value.photo : ''),
    format: `${APPT_TYPES[a.type] || ''} consultation, ${a.duration_minutes || 60} min`.trim(),
  }
})

// Under the time: a countdown only on the day itself ("Today, in 5 hours",
// "Starts in 12 min"); other days just say the day. Ticks every 30 s.
const tick = useNow()
const whenLine = computed(() => {
  const u = upNext.value
  if (!u) return ''
  const mins = Math.round((u.startsAt - tick.value) / 60000)
  if (mins <= 0) return 'Starting now'
  if (mins < 60) return `Starts in ${mins} min`
  if (u.day !== 'Today') return u.day
  const hrs = Math.round(mins / 60)
  return `Today, in ${hrs} hour${hrs === 1 ? '' : 's'}`
})

// The card when nothing is booked: one short headline, one line of context.
const lastVisit = computed(() => appointments.value
  .filter(a => a.status === 'completed')
  .sort((a, b) => new Date(b.scheduled_at) - new Date(a.scheduled_at))[0] || null)
const emptyCard = computed(() => {
  if (!screening.value) return { headline: 'Health screening', sub: 'About a minute. Your RND needs it before you meet.' }
  if (!activeRelationship.value && expiredRequest.value) return { headline: 'Booking expired', sub: 'Your last request passed before it was confirmed.' }
  if (activeRelationship.value) {
    const v = lastVisit.value
    if (!v) return { headline: 'Nothing booked', sub: 'Book your next consultation when you\'re ready.' }
    const days = Math.max(0, Math.round((Date.now() - new Date(v.scheduled_at)) / 86400000))
    const ago = days === 0 ? 'today' : days === 1 ? 'yesterday' : `${days} days ago`
    return { headline: 'Nothing booked', sub: `Your last consultation was ${formatShortDate(v.scheduled_at)}, ${ago}.` }
  }
  return { headline: 'Find your RND', sub: 'Pick a licensed RND and book your first consultation.' }
})

/* ---------- Next step (banner) ---------- */
const nextStep = computed(() => {
  const appt = nextAppointment.value
  const rndName = careRnd.value ? `RND ${careRnd.value.name}` : 'your RND'
  if (!screening.value) {
    return {
      eyebrow: 'Your next step',
      text: 'Complete your health screening. It takes about a minute and gives your RND your BMI, calorie needs and nutrition risk before you meet.',
      short: 'Your health screening. It takes about a minute.',
      action: 'Start screening', to: '/pre-consultation-screening',
    }
  }
  // Pay before the consultation (unpaid ones are cancelled at the start time).
  if (appt?.status === 'confirmed' && appt.payment?.status === 'unpaid') {
    const amount = Number(appt.payment.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })
    return {
      eyebrow: 'Payment due',
      text: `${rndName} confirmed your ${formatLongDate(appt.scheduled_at)} ${formatTime(appt.scheduled_at)} consultation. Pay ₱${amount} before then to start it. Unpaid bookings are cancelled at the start time.`,
      action: null, to: '/appointments', // no button here: paying lives in Needs you, the status pill says it
    }
  }
  if (appt?.status === 'confirmed') {
    const when = `${formatLongDate(appt.scheduled_at)} at ${formatTime(appt.scheduled_at)}`
    // The API only sends the room link inside the join window (15 min early).
    const canJoin = (appt.type === 'video' && appt.video_session_url)
      || (appt.type === 'chat' && appt.payment?.status === 'paid' && Date.now() >= new Date(appt.join_opens_at) && Date.now() <= new Date(appt.join_closes_at))
    return {
      eyebrow: 'Upcoming consultation',
      text: `${APPT_TYPES[appt.type] || ''} consultation with ${rndName} on ${when}.`,
      action: canJoin ? (appt.type === 'chat' ? 'Join chat' : 'Join video call') : 'View appointment',
      to: canJoin ? `/consultation-room/${appt.id}` : '/appointments',
    }
  }
  if (appt?.status === 'pending') {
    return {
      eyebrow: 'Waiting for your RND',
      text: `Your ${formatLongDate(appt.scheduled_at)} ${formatTime(appt.scheduled_at)} booking is waiting for ${rndName} to confirm. We'll notify you as soon as they do.`,
      action: 'View booking', to: '/appointments',
    }
  }
  // A booking request whose time passed before the RND confirmed it.
  if (!activeRelationship.value && expiredRequest.value) {
    const rnd = expiredRequest.value.relationship?.rnd
    return {
      eyebrow: 'Booking not confirmed',
      text: `Your ${formatLongDate(expiredRequest.value.scheduled_at)} booking request${rnd ? ` with RND ${rnd.first_name} ${rnd.last_name}` : ''} wasn't confirmed before its time passed. Pick a new time, or choose another RND.`,
      short: 'Your last booking request expired. Pick a new time.',
      action: 'Book a new time', to: rnd ? `/rnd-profile-view/${rnd.id}?book=1` : '/find-rnd',
    }
  }
  if (activeRelationship.value) {
    return {
      eyebrow: 'Stay on track',
      text: activePlan.value
        ? `You don't have an upcoming consultation with ${rndName}. Keep logging your meals, and book a follow-up when you're ready.`
        : `You don't have an upcoming consultation with ${rndName}. Book one to continue your care.`,
      short: `No consultation booked with ${rndName}.`,
      action: 'Book a consultation', to: `/rnd-profile-view/${activeRelationship.value.rnd.id}?book=1`,
    }
  }
  return {
    eyebrow: 'Your next step',
    text: 'Your screening is done. Find a licensed RND who fits your needs and book your first consultation.',
    short: 'Find an RND and book your first consultation.',
    action: 'Find an RND', to: '/find-rnd',
  }
})

/* ---------- Screening badges ---------- */
const nrsRiskLabel = computed(() => ({ no_risk: 'No risk', at_risk: 'At risk', high_risk: 'High risk' }[screening.value?.nrs_risk] || ''))
const nrsTone = computed(() => ({ no_risk: 'good', at_risk: 'warn', high_risk: 'bad' }[screening.value?.nrs_risk] || 'neutral'))
const bmiTone = computed(() => ((screening.value?.bmi_category || '').toLowerCase().includes('normal') ? 'good' : 'warn'))

/* ---------- Meal plan ---------- */
// Only the plan the RND has sent (drafts never reach the client).
const activePlan = computed(() => mealPlans.value.find(p => p.status === 'active') || null)

// The RND's target when there's a plan; otherwise the screening's estimate.
const calorieTarget = computed(() => {
  if (activePlan.value?.target_kcal) {
    return { value: Math.round(Number(activePlan.value.target_kcal)), label: 'Daily calorie target', note: 'Set by your RND in your meal plan' }
  }
  if (screening.value?.tdee_kcal) {
    return { value: Math.round(Number(screening.value.tdee_kcal)), label: 'Estimated daily needs (TDEE)', note: 'Your RND sets your actual target' }
  }
  return { value: null, label: 'Daily calorie target', note: 'Complete your screening first' }
})
const planMacros = computed(() => {
  const p = activePlan.value
  if (!p?.target_kcal) return null
  const g = (v) => (v ? Math.round(Number(v)) : null)
  return { kcal: Math.round(Number(p.target_kcal)).toLocaleString(), carbs: g(p.target_carb_g), protein: g(p.target_protein_g), fat: g(p.target_fat_g) }
})

// Plans are per weekday (Sunday = 0); meals with no day (older plans) apply every day.
const todaysMeals = computed(() =>
  (activePlan.value?.meals || [])
    .filter(m => m.day_of_week === now.getDay() || m.day_of_week === null)
    .sort((a, b) => MEAL_ORDER.indexOf(a.meal_time) - MEAL_ORDER.indexOf(b.meal_time))
)
function mealFoodsLabel(meal) {
  const names = (meal.food_items || []).map(f => f.food_name).filter(Boolean)
  if (!names.length) return 'No foods listed'
  return names.length > 3 ? `${names.slice(0, 3).join(', ')} +${names.length - 3} more` : names.join(', ')
}

const todaysLogsByMeal = computed(() => {
  const map = {}
  for (const log of mealLogs.value) if (log.log_date === todayIso) map[log.meal_plan_meal] = log
  return map
})
function logLabel(meal) {
  const log = todaysLogsByMeal.value[meal.id]
  return log ? LOG_LABELS[log.status] || 'Waiting for your RND to rate it' : 'Not logged'
}
function logPillClass(meal) {
  const status = todaysLogsByMeal.value[meal.id]?.status
  if (todaysLogsByMeal.value[meal.id] && !status) return 'pill-gold'
  return { followed: 'pill-green', partially_followed: 'pill-gold', not_followed: 'badge-danger' }[status] || 'pill-muted'
}
const todayLoggedCount = computed(() => todaysMeals.value.filter(m => todaysLogsByMeal.value[m.id]).length)

// Last 7 days including today, from the client's own meal logs.
const weekAdherence = computed(() => {
  const start = new Date(now)
  start.setDate(start.getDate() - 6)
  const startIso = localIso(start)
  // Only meals the RND has rated count; the rest are waiting for their rating.
  const logs = mealLogs.value.filter(l => l.log_date >= startIso && l.log_date <= todayIso && l.status)
  const followed = logs.filter(l => l.status === 'followed').length
  return { logged: logs.length, followed, followedPct: logs.length ? Math.round((followed / logs.length) * 100) : 0 }
})

/* ---------- Weight chart (oldest → newest) ----------
   Starts from the screening — the baseline the RND measures progress from —
   then the latest progress readings, so the change matches the RND's view. */
const weightHistory = ref([])
function toWeightHistory(records, baseline) {
  const points = records
    .filter(r => r.weight_kg != null)
    .slice(0, baseline ? 7 : 8)
    .reverse()
    .map(r => ({
      weight: Number(r.weight_kg),
      label: new Date(r.record_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    }))
  if (baseline?.weight_kg != null) points.unshift({ weight: Number(baseline.weight_kg), label: 'Screening' })
  return points
}
const weightDeltaLabel = computed(() => {
  if (weightHistory.value.length < 2) return ''
  const delta = weightHistory.value[weightHistory.value.length - 1].weight - weightHistory.value[0].weight
  if (Math.abs(delta) < 0.05) return 'No change'
  return `${delta < 0 ? '↓' : '↑'} ${Math.abs(delta).toFixed(1)} kg ${weightHistory.value[0].label === 'Screening' ? 'since your screening' : 'overall'}`
})
const chartCoords = computed(() => {
  if (!weightHistory.value.length) return []
  const weights = weightHistory.value.map(w => w.weight)
  const minW = Math.min(...weights)
  const maxW = Math.max(...weights)
  const range = maxW - minW || 1
  const n = weightHistory.value.length
  return weightHistory.value.map((w, i) => ({
    label: w.label,
    weight: w.weight,
    x: n > 1 ? (i / (n - 1)) * 400 : 200,
    y: 80 - ((w.weight - minW) / range) * 56,
  }))
})
const chartPoints = computed(() => chartCoords.value.map(p => `${p.x},${p.y}`).join(' '))
const chartFillPoints = computed(() => {
  const c = chartCoords.value
  if (!c.length) return ''
  return `${chartPoints.value} ${c[c.length - 1].x},90 ${c[0].x},90`
})

/* ---------- Recent activity ---------- */
const recentActivity = computed(() => notifications.value.slice(0, 5))

async function loadDashboard() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [appts, rels, latestScreening, progress, plans, logs, invs, notes, labData] = await Promise.all([
      get('/client/appointments/'),
      get('/client/relationships/'),
      get('/client/screening/latest/').catch(() => null),
      get('/client/progress/').catch(() => []),
      get('/client/meal-plans/').catch(() => []),
      get('/client/meal-logs/').catch(() => []),
      get('/client/invoices/').catch(() => []),
      get('/notifications/').catch(() => []),
      get('/client/labs/').catch(() => null),
    ])
    labs.value = labData
    appointments.value = appts
    relationships.value = rels
    screening.value = latestScreening
    weightHistory.value = toWeightHistory(progress, latestScreening)
    mealPlans.value = plans
    mealLogs.value = logs
    invoices.value = invs
    notifications.value = Array.isArray(notes) ? notes : notes?.results || []

    const rndId = careRnd.value?.id
    if (rndId) rndProfile.value = await get(`/client/rnds/${rndId}/`).catch(() => null)
  } catch {
    errorMessage.value = 'Could not load your dashboard. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadDashboard)

/* Coming up today — consultations, meals to log and RND reminders (also
   sends any reminder that's due right now). */
const TODAY_ICONS = { appointment: CalendarCheck, meal: UtensilsCrossed, reminder: AlarmClock }
const todayItems = ref([])
const todayLoaded = ref(false)
async function loadToday() {
  try {
    todayItems.value = await get('/client/today/')
  } catch {
    todayItems.value = []
  } finally {
    todayLoaded.value = true
  }
}
onMounted(loadToday)

// My tasks: tick off tasks (POST /client/reminders/<id>/check/), add your own.
const checkable = computed(() => todayItems.value.filter(i => ['task', 'meal', 'lab'].includes(i.kind)))
const taskCount = computed(() => checkable.value.length)
const doneCount = computed(() => checkable.value.filter(i => i.done).length)
async function toggleTask(item, done) {
  item.done = done
  try {
    item.done = (await post(`/client/reminders/${item.id}/check/`, { done })).done
  } catch {
    item.done = !done
  }
}
const addOpen = ref(false)
const adding = ref(false)
const addError = ref('')
function defaultTime() {
  const d = new Date(Date.now() + 30 * 60000)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
const newTask = reactive({ title: '', time: defaultTime(), repeat: 'once' })
async function addTask() {
  adding.value = true
  addError.value = ''
  try {
    const today = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' })
    await post('/client/reminders/', { title: newTask.title.trim(), date: today, time: newTask.time, repeat: newTask.repeat })
    Object.assign(newTask, { title: '', time: defaultTime(), repeat: 'once' })
    addOpen.value = false
    await loadToday()
  } catch (e) {
    const d = e?.data || {}
    addError.value = d.time?.[0] || d.title?.[0] || d.detail || 'Could not add the task.'
  } finally {
    adding.value = false
  }
}
async function removeTask(item) {
  try {
    await del(`/client/reminders/${item.id}/`)
    todayItems.value = todayItems.value.filter(i => i !== item)
  } catch { /* leave it */ }
}
function phClock(iso) {
  return new Date(iso).toLocaleTimeString('en-PH', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' })
}
</script>

<style scoped>
/* Same tokens as the RND dashboard (RNDDashboard.vue): banner, stat cards,
   panels, panel links and the outlined block button. */
* { box-sizing: border-box; }

.client-dashboard { font-family: 'Inter', sans-serif; }
.unit { font-size: 0.85rem; font-weight: 400; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #6a7a6a; }
.empty-note { font-size: 0.85rem; color: #6a7a6a; margin: 0; line-height: 1.5; }
.empty-note.spaced { margin-bottom: 16px; }

/* UNPAID INVOICE ROW */
/* NEEDS YOU (same panel as RNDDashboard.vue) */
.needs { background: #fff; border: 1px solid #d9e3dc; border-radius: 14px; overflow: hidden; margin: -4px 0 20px; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.needs > * + * { border-top: 1px solid #d9e3dc; }
.all-clear { display: flex; align-items: center; gap: 8px; margin: 0; padding: 14px 20px; font-size: 0.86rem; font-weight: 600; color: #1f6f46; }
.needs-band { list-style: none; margin: 0; padding: 0; }
.needs-row { display: flex; align-items: center; gap: 12px; padding: 12px 20px; font-size: 0.86rem; color: #3a4a3a; line-height: 1.45; }
.needs-row + .needs-row { border-top: 1px solid #eef1ee; }
.needs-row strong { color: #1a3a1a; }
.needs-text { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.needs-row.risk { background: #fdf3f2; }
.needs-row.risk strong { color: #a12525; }
.needs-icon { flex-shrink: 0; color: #c0392b; }
.needs-row.unfinished::before { content: ''; flex-shrink: 0; align-self: stretch; width: 0; border-left: 2px dashed #3f9a6b; margin: 2px 2px 2px 7px; }
/* every action here is the usual dark green; red only marks the warning (row + icon) */
.needs-btn { flex-shrink: 0; display: inline-flex; align-items: center; min-height: 32px; white-space: nowrap; font-size: 0.82rem; font-weight: 600; text-decoration: none; color: #fff; border: 1px solid #0a4a37; border-radius: 8px; padding: 0 14px; background: #0a4a37; }
.needs-btn:hover { background: #00382a; }
.needs-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
/* one opening moment, about 3 seconds: the panel drops in, then each red and
   dashed-green line glows three times (only the items, not the panel) */
@media (prefers-reduced-motion: no-preference) {
  .needs { animation: nm-drop 0.45s cubic-bezier(0.2, 0.8, 0.2, 1) both; }
  .needs-row.risk { animation: nm-risk 1s ease-in-out 0.45s 3; }
  .needs-row.risk .needs-icon { animation: nm-shake 0.5s ease-in-out 0.6s 2; }
  .needs-row.unfinished { animation: nm-todo 1s ease-in-out 0.45s 3; }
}
@keyframes nm-drop { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: none; } }
@keyframes nm-risk { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(192, 57, 43, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(192, 57, 43, 0.45), inset 0 0 18px rgba(192, 57, 43, 0.22); } }
@keyframes nm-todo { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(63, 154, 107, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(63, 154, 107, 0.45), inset 0 0 18px rgba(63, 154, 107, 0.2); } }
@keyframes nm-shake { 0%, 100% { transform: rotate(0); } 25% { transform: rotate(-12deg); } 75% { transform: rotate(12deg); } }
.notice-text { flex: 1; font-size: 0.85rem; }
.notice-text strong { color: #1a3a1a; }

/* STAT CARDS */
/* health figures: one divided panel, like the RND dashboard */
.stat-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); margin-bottom: 20px; background: #fff;
  border: 1px solid #d9e3dc; border-radius: 14px; overflow: hidden;
  box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09);
}
.stat-card { padding: 18px 20px; min-width: 0; border-left: 1px solid #d9e3dc; }
.stat-card:first-child { border-left: none; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: #1a3a1a; margin: 0; font-variant-numeric: lining-nums; }
.stat-label { font-size: 0.82rem; font-weight: 600; color: #4a5a4a; margin: 2px 0 6px; }
.stat-delta { font-size: 0.75rem; margin: 0; line-height: 1.4; }
.stat-delta.neutral { color: #6a7a6a; }
.stat-delta.good { color: #1f8f5c; font-weight: 600; }
.stat-delta.warn { color: #b8860b; font-weight: 600; }
.stat-delta.bad { color: #c0392b; font-weight: 600; }

/* GRID + PANELS */
.dash-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; align-items: start; }
.dash-col { display: flex; flex-direction: column; gap: 20px; min-width: 0; }
.panel { background: #fff; border-radius: 14px; border: 1px solid #d9e3dc; padding: 22px; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.today-row { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-top: 1px solid #d9e3dc; text-decoration: none; color: inherit; }
.panel-header-row + .today-row { margin-top: 12px; border-top: none; }
.today-row.done { opacity: 0.55; }
.today-row.done .today-title { text-decoration: line-through; }
.today-icon { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #eef3ec; color: #1e4a26; }
.today-icon.k-reminder { background: #fdf1d6; color: #b8860b; }
.today-icon.k-appointment { background: #e3efe7; color: #1e4a26; }
.today-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.today-title { font-size: 0.84rem; font-weight: 600; color: #1a3a1a; overflow-wrap: anywhere; }
.today-detail { font-size: 0.76rem; color: #6a7a6a; }
.today-time { font-size: 0.76rem; font-weight: 700; color: #4a5a4a; white-space: nowrap; }
.today-row.task { cursor: pointer; }
.task-check { width: 20px; height: 20px; margin: 0 5px; flex-shrink: 0; accent-color: #1f8f5c; cursor: pointer; }
.task-check.meal { display: inline-flex; align-items: center; justify-content: center; border: 2px solid #b9c4b9; border-radius: 5px; color: #fff; box-sizing: border-box; }
.task-check.meal.on { background: #1f8f5c; border-color: #1f8f5c; }
.today-note { display: block; font-size: 0.8rem; color: #3a4a3a; line-height: 1.45; white-space: pre-line; overflow-wrap: anywhere; }
.task-x { border: none; background: none; color: #9aaa9a; cursor: pointer; padding: 2px; display: flex; }
.task-x:hover { color: #c0392b; }
.as-btn { background: none; border: none; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 3px; padding: 0; }
.add-task { display: flex; flex-direction: column; gap: 8px; background: #f4f8f5; border: 1px solid #d9e3dc; border-radius: 10px; padding: 10px; margin-bottom: 8px; }
.add-task .nm-input { min-height: 40px; }
.add-task-row { display: flex; gap: 8px; }
.add-task-row .nm-input { flex: 1; min-width: 0; }
.add-task-row .nm-select { flex: 1; min-width: 0; }
.add-error { font-size: 0.74rem; color: #a12525; margin: 0; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }
.panel-title.flush { margin: 0; }
.panel-sub { font-size: 0.8rem; color: #6a7a6a; margin: 3px 0 0; }
.panel-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 18px; }
.panel-link { font-size: 0.8rem; color: #0a4a37; font-weight: 600; text-decoration: none; white-space: nowrap; }
.panel-link:hover { text-decoration: underline; }
.panel-meta { font-size: 0.78rem; color: #6a7a6a; font-weight: 600; white-space: nowrap; }

/* PILLS (meal log status only) */
.status-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-gold { background: #fdf1d6; color: #b8860b; }
.pill-muted { background: #eef2ef; color: #4a5a4a; }
.badge-danger { background: #fdecec; color: #a12525; }

/* BUTTON — the RND dashboard's outlined block button */
.block-btn {
  display: block; width: 100%; text-align: center; background: #fff; border: 1px solid #0a4a37; color: #0a4a37;
  border-radius: 8px; padding: 10px; font-weight: 600; font-size: 0.85rem; font-family: inherit; cursor: pointer; text-decoration: none;
}
.block-btn:hover { background: #f4f7f5; }
.block-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.btn-row { display: flex; gap: 10px; }
.block-wide { width: 100%; }

/* TODAY'S MEAL PLAN */
.macro-strip {
  display: flex; flex-wrap: wrap; gap: 6px 16px; align-items: baseline;
  background: #f4f8f5; border: 1px solid #d9e3dc; border-radius: 10px; padding: 10px 14px; margin-bottom: 14px; font-size: 0.82rem; color: #4a5a4a;
}
.macro-strip strong { color: #1a3a1a; }
.macro-source { font-size: 0.76rem; color: #6a7a6a; margin-left: auto; }
.meal-list { list-style: none; margin: 0; padding: 0; }
.meal-row { display: flex; align-items: center; gap: 12px; padding: 11px 0; border-top: 1px solid #d9e3dc; }
.meal-row:first-child { border-top: none; padding-top: 0; }
.meal-icon { width: 32px; height: 32px; border-radius: 9px; background: #eef3ec; color: #1e4a26; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.meal-info { flex: 1; min-width: 0; }
.meal-name { font-size: 0.87rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.meal-detail { font-size: 0.78rem; color: #6a7a6a; margin: 2px 0 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.adherence-row { display: grid; grid-template-columns: auto 1fr; gap: 18px; border-top: 1px solid #d9e3dc; margin-top: 12px; padding-top: 14px; }
.adherence-item { display: flex; align-items: baseline; gap: 8px; min-width: 0; }
.adherence-value { font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.adherence-label { font-size: 0.78rem; color: #6a7a6a; margin: 0; }
.empty-state { text-align: center; padding: 18px 10px; color: #6a7a6a; font-size: 0.85rem; }
.empty-state p { margin: 0; }
.empty-icon { color: #9ec4ad; margin-bottom: 8px; }
.empty-sub { font-size: 0.78rem; margin-top: 4px !important; line-height: 1.5; }

/* WEIGHT CHART */
.weight-chart { padding: 10px 0 4px; }

/* RND CARD */
.rnd-row { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.rnd-avatar { width: 52px; height: 52px; border-radius: 50%; background: #00382a; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.rnd-avatar-img { object-fit: cover; }
.rnd-text { min-width: 0; }
.rnd-name { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.rnd-specialty { font-size: 0.8rem; color: #6a7a6a; margin: 2px 0 0; }
.rnd-rating { font-size: 0.78rem; color: #b8860b; font-weight: 600; margin: 2px 0 0; }
.rnd-pending { font-size: 0.76rem; color: #b8860b; margin: 4px 0 0; }
/* Compact "Your RND" card at the top of the right column. */
.rnd-compact { display: flex; align-items: center; gap: 12px; padding: 14px 16px; }
.rnd-compact .rnd-avatar { width: 44px; height: 44px; font-size: 0.85rem; }
.rnd-compact .rnd-text { flex: 1; min-width: 0; }
.rnd-compact .rnd-name { overflow-wrap: anywhere; }
.rnd-eyebrow { font-size: 0.76rem; font-weight: 600; color: #4a5a4a; margin: 0 0 1px; }
.rnd-actions { display: flex; gap: 6px; flex-shrink: 0; }
.icon-action { width: 36px; height: 36px; border-radius: 10px; border: none; background: #e3efe7; display: flex; align-items: center; justify-content: center; color: #0a4a37; text-decoration: none; }
.icon-action:hover { background: #d3e7da; }
.icon-action:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

/* LATEST SCREENING */
.screening-summary-text { font-size: 0.84rem; color: #6a7a6a; margin: 0 0 16px; line-height: 1.5; }

/* RECENT ACTIVITY */
.activity-row { display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-top: 1px solid #d9e3dc; }
.activity-row:first-of-type { border-top: none; padding-top: 0; }
.activity-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; margin-top: 6px; background: #c5d0c5; }
.activity-dot.unread { background: #D4A017; }
.activity-text { min-width: 0; }
.activity-title { font-size: 0.83rem; font-weight: 600; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.activity-time { font-size: 0.76rem; color: #6a7a6a; margin: 2px 0 0; }

@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .stat-card:nth-child(3) { border-left: none; }
  .stat-card:nth-child(n+3) { border-top: 1px solid #d9e3dc; }
  .dash-grid { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .stat-card { padding: 14px 16px; }
  .stat-value { font-size: 1.35rem; }
  .panel { padding: 18px 16px; }
  .adherence-row { grid-template-columns: 1fr; gap: 8px; }
  .needs-row { flex-wrap: wrap; padding: 12px 16px; }
  .needs-text { flex-basis: calc(100% - 40px); }
  .needs-btn { margin-left: 28px; }
  .needs-row.unfinished .needs-btn { margin-left: 21px; }
  .macro-source { margin-left: 0; width: 100%; }
}

/* ===== BANNER "UP NEXT" CARD — frosted glass instead of white, gold primary button ===== */
.nm-upnext {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  color: #fff;
}

/* "YOUR NEXT STEP" / "Up next · time" label */
.nm-upnext-label { color: #f0c15b; }

/* Text inside the card (empty state + booked-consultation state) */
.nm-upnext-empty,
.nm-upnext-name { color: #fff; }
.nm-upnext-format { color: rgba(255, 255, 255, 0.7); }

/* RND avatar + payment pill (only shows when a consultation is booked) */
.nm-upnext-avatar { background: rgba(255, 255, 255, 0.18); color: #fff; }
.nm-upnext-pay { background: rgba(255, 255, 255, 0.16); color: #fff; }
.nm-upnext-pay.unpaid { background: rgba(240, 193, 91, 0.2); color: #f0c15b; }

/* UP NEXT card: the time is the big thing */
.up { gap: 0; }
.up-top { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.up-status { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 600; white-space: nowrap; }
.up-dot { width: 9px; height: 9px; border-radius: 50%; background: #fff; flex-shrink: 0; }
.up-status.unpaid { color: #f0c15b; }
.up-status.unpaid .up-dot { background: #f0c15b; box-shadow: 0 0 0 3px rgba(240, 193, 91, 0.22); }
.up-status.paid { color: #9be3bd; }
.up-status.paid .up-dot { background: #4ade80; }
.up-status.waiting { color: #fff; }
.up-time { font-family: 'Playfair Display', serif; font-size: 38px; font-weight: 700; line-height: 1.05; color: #fff; margin: 12px 0 2px; font-variant-numeric: lining-nums; }
.up-time.small { font-size: 28px; }
.up-when { font-size: 14px; color: rgba(255, 255, 255, 0.78); margin: 0; }
.up-with { font-size: 13px; color: rgba(255, 255, 255, 0.7); margin: 2px 0 0; overflow-wrap: anywhere; }
.up-who { display: flex; align-items: center; gap: 12px; min-width: 0; margin-top: 14px; padding-top: 14px; border-top: 1px solid rgba(255, 255, 255, 0.18); }
.up .nm-upnext-actions { margin-top: 14px; }
.up-empty { display: flex; align-items: center; justify-content: space-between; gap: 12px 16px; }
.up-empty-text { min-width: 0; }
.up-empty-btn { flex-shrink: 0; }
@media (max-width: 640px) {
  .up-time { font-size: 32px; }
  .up-time.small { font-size: 24px; }
  .up-empty { flex-direction: column; align-items: stretch; }
  .up-empty-btn { width: 100%; }
}

/* Buttons */
.nm-upnext .nm-hero-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: #fff;
}
.nm-upnext .nm-hero-btn:hover { background: rgba(255, 255, 255, 0.12); }

.nm-upnext .nm-hero-btn.primary {
  background: #f2b61f;
  border-color: #f2b61f;
  color: #0a4a37;
}
.nm-upnext .nm-hero-btn.primary:hover {
  background: #e0a410;
  border-color: #e0a410;
}
</style>