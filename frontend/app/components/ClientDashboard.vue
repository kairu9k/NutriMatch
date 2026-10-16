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
        <div class="nm-upnext">
          <template v-if="upNext">
            <div class="nm-upnext-top">
              <span class="nm-upnext-label">Up next · {{ upNext.when }}</span>
              <span class="nm-upnext-pay" :class="{ unpaid: upNext.pill !== 'Paid' }">{{ upNext.pill }}</span>
            </div>
            <div class="nm-upnext-row">
              <div class="nm-upnext-who">
                <img v-if="upNext.photo" :src="upNext.photo" alt="" class="nm-upnext-avatar" />
                <span v-else class="nm-upnext-avatar">{{ upNext.initials }}</span>
                <div class="nm-upnext-name-wrap">
                  <p class="nm-upnext-name">RND {{ upNext.name }}</p>
                  <p class="nm-upnext-format">{{ upNext.format }}</p>
                </div>
              </div>
              <div class="nm-upnext-actions">
                <NuxtLink :to="nextStep.to" class="nm-hero-btn primary">
                  <Video v-if="/Join/.test(nextStep.action)" :size="16" />{{ nextStep.action }}
                </NuxtLink>
                <NuxtLink v-if="nextStep.to !== '/appointments'" to="/appointments" class="nm-hero-btn">View appointment</NuxtLink>
              </div>
            </div>
          </template>
          <template v-else>
            <p class="nm-upnext-label">{{ nextStep.eyebrow }}</p>
            <p class="nm-upnext-empty">{{ nextStep.short }}</p>
            <div class="nm-upnext-actions"><NuxtLink :to="nextStep.to" class="nm-hero-btn primary">{{ nextStep.action }}</NuxtLink></div>
          </template>
        </div>
      </section>

      <!-- UNPAID INVOICE -->
      <NuxtLink v-if="unpaidInvoices.length" to="/invoices-billing" class="notice-row">
        <div class="stat-icon icon-gold"><Receipt :size="17" /></div>
        <span class="notice-text">
          You have {{ unpaidInvoices.length === 1 ? 'an unpaid invoice' : `${unpaidInvoices.length} unpaid invoices` }}
          — <strong>₱{{ unpaidTotal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}</strong>
        </span>
        <span class="panel-link">Pay now →</span>
      </NuxtLink>

      <!-- HEALTH SNAPSHOT -->
      <section class="stat-grid">
        <div class="stat-card">
          <div class="stat-top"><div class="stat-icon"><Activity :size="17" /></div></div>
          <p class="stat-value">{{ screening ? Number(screening.bmi).toFixed(1) : '—' }}</p>
          <p class="stat-label">Current BMI</p>
          <p class="stat-delta" :class="screening ? bmiTone : 'neutral'">{{ screening?.bmi_category ?? 'Not yet screened' }}</p>
        </div>
        <div class="stat-card">
          <div class="stat-top"><div class="stat-icon icon-gold"><Flame :size="17" /></div></div>
          <p class="stat-value">
            {{ calorieTarget.value ? calorieTarget.value.toLocaleString() : '—' }}
            <span v-if="calorieTarget.value" class="unit">kcal</span>
          </p>
          <p class="stat-label">{{ calorieTarget.label }}</p>
          <p class="stat-delta neutral">{{ calorieTarget.note }}</p>
        </div>
        <div class="stat-card">
          <div class="stat-top"><div class="stat-icon"><ClipboardCheck :size="17" /></div></div>
          <p class="stat-value">{{ screening?.nrs_score ?? '—' }}</p>
          <p class="stat-label">NRS-2002 Score</p>
          <p class="stat-delta" :class="screening ? nrsTone : 'neutral'">{{ screening ? nrsRiskLabel : 'Pending screening' }}</p>
        </div>
        <div class="stat-card">
          <div class="stat-top"><div class="stat-icon"><CalendarDays :size="17" /></div></div>
          <p class="stat-value">{{ nextAppointment ? formatShortDate(nextAppointment.scheduled_at) : '—' }}</p>
          <p class="stat-label">Next Appointment</p>
          <p v-if="nextAppointment" class="stat-delta" :class="nextAppointment.status === 'pending' ? 'warn' : 'neutral'">
            {{ formatTime(nextAppointment.scheduled_at) }} · {{ APPT_TYPES[nextAppointment.type] || nextAppointment.type }}{{ nextAppointment.status === 'pending' ? ' · awaiting confirmation' : '' }}
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
                <h3 class="panel-title flush">Today's Meal Plan</h3>
                <p v-if="activePlan" class="panel-sub">{{ weekdayLabel }} · {{ activePlan.name || 'Your meal plan' }}</p>
              </div>
              <NuxtLink v-if="activePlan" to="/meal-plan-view" class="panel-link">Log meals →</NuxtLink>
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
                      <template v-if="meal.scheduled_time">{{ formatClock(meal.scheduled_time) }} · </template>
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
              <h3 class="panel-title flush">Weight Progress (kg)</h3>
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
            <p v-else class="empty-note">No weight history yet — this starts from your screening and fills in as you or your RND record your progress.</p>
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
                  {{ careRnd.specialization || 'Registered Nutritionist-Dietitian' }}<template v-if="careRnd.reviewCount"> · ★ {{ careRnd.rating }}</template>
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
              <button type="button" class="panel-link as-btn" @click="addOpen = !addOpen"><Plus :size="13" /> Add a task</button>
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

            <template v-for="(item, i) in todayItems" :key="item.id ? `t${item.id}` : i">
              <label v-if="item.kind === 'task'" class="today-row task" :class="{ done: item.done }">
                <input type="checkbox" class="task-check" :checked="item.done" @change="toggleTask(item, $event.target.checked)" />
                <span class="today-main">
                  <span class="today-title">{{ item.title }}</span>
                  <span class="today-detail">{{ item.detail }}</span>
                </span>
                <span class="today-time">{{ phClock(item.at) }}</span>
                <button v-if="item.own" type="button" class="task-x" aria-label="Delete task" @click.prevent="removeTask(item)"><X :size="13" /></button>
              </label>
              <NuxtLink v-else :to="item.link" class="today-row" :class="{ done: item.done }">
                <span v-if="item.kind === 'meal'" class="task-check meal" :class="{ on: item.done }" aria-hidden="true"><Check v-if="item.done" :size="12" /></span>
                <span v-else class="today-icon" :class="'k-' + item.kind"><component :is="TODAY_ICONS[item.kind]" :size="15" /></span>
                <span class="today-main">
                  <span class="today-title">{{ item.title }}</span>
                  <span v-if="item.detail" class="today-detail">{{ item.detail }}</span>
                </span>
                <span class="today-time">{{ phClock(item.at) }}</span>
              </NuxtLink>
            </template>
            <p v-if="todayLoaded && !todayItems.length" class="empty-note">No tasks for today. Tasks from your RND, meals to log and your own tasks show up here.</p>
          </div>

          <!-- RECENT ACTIVITY (real notifications) -->
          <div class="panel">
            <div class="panel-header-row">
              <h3 class="panel-title flush">Recent Activity</h3>
              <NuxtLink v-if="notifications.length" to="/notifications" class="panel-link">View all →</NuxtLink>
            </div>
            <div v-for="n in recentActivity" :key="n.id" class="activity-row">
              <span class="activity-dot" :class="{ unread: !n.is_read }"></span>
              <div class="activity-text">
                <p class="activity-title">{{ n.subject }}</p>
                <p class="activity-time">{{ timeAgo(n.created_at) }}</p>
              </div>
            </div>
            <p v-if="!recentActivity.length" class="empty-note">Nothing yet — updates about your bookings, meal plans and payments show up here.</p>
          </div>

          <!-- LATEST SCREENING -->
          <div class="panel">
            <h3 class="panel-title">Your Screening</h3>
            <template v-if="screening">
              <p class="screening-summary-text">
                Recorded {{ formatLongDate(screening.created_at) }} · {{ Number(screening.height_cm) }} cm · {{ Number(screening.weight_kg) }} kg
              </p>
              <button type="button" class="block-btn" @click="screeningOpen = true">View Screening</button>
            </template>
            <template v-else>
              <p class="screening-summary-text">Your RND needs this before your first consultation. It takes about a minute.</p>
              <NuxtLink to="/pre-consultation-screening" class="block-btn">Complete Screening</NuxtLink>
            </template>
          </div>
        </div>
      </section>
    </template>

    <ScreeningModal v-if="screeningOpen" @close="screeningOpen = false" />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  Activity, Flame, ClipboardCheck, CalendarDays, Receipt, UtensilsCrossed, Sunrise, Sun, Moon, Coffee, AlarmClock, CalendarCheck, Check, Plus, X, MessageSquare, UserRound, Video,
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

const APPT_TYPES = { video: 'Video', chat: 'Chat', in_person: 'In-person' }
const MEAL_ORDER = ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner', 'bedtime_snack']
const MEAL_LABELS = { breakfast: 'Breakfast', am_snack: 'AM Snack', lunch: 'Lunch', pm_snack: 'PM Snack', dinner: 'Dinner', bedtime_snack: 'Bedtime Snack' }
const MEAL_ICONS = { breakfast: Sunrise, am_snack: Coffee, lunch: Sun, pm_snack: Coffee, dinner: Moon, bedtime_snack: Moon }
const LOG_LABELS = { followed: 'Followed', partially_followed: 'Partly followed', not_followed: 'Not followed' }

// Local dates — toISOString() is UTC and would give yesterday before 8 AM in PHT.
const now = new Date()
function localIso(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
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
const unpaidTotal = computed(() => unpaidInvoices.value.reduce((sum, i) => sum + Number(i.amount), 0))

/* ---------- Banner "Up next" card: the next consultation, if any ---------- */
const longToday = new Date().toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' })
const upNext = computed(() => {
  const a = nextAppointment.value
  if (!a) return null
  const rnd = a.relationship?.rnd || {}
  const name = `${rnd.first_name || ''} ${rnd.last_name || ''}`.trim()
  const sameDay = new Date(a.scheduled_at).toDateString() === new Date().toDateString()
  const day = sameDay ? '' : `${new Date(a.scheduled_at).toLocaleDateString('en-PH', { weekday: 'short', month: 'short', day: 'numeric' })}, `
  return {
    when: `${day}${formatTime(a.scheduled_at)}`,
    pill: a.status === 'pending' ? 'Waiting to confirm' : a.payment?.status === 'paid' ? 'Paid' : 'Not paid yet',
    name,
    initials: `${rnd.first_name?.[0] || ''}${rnd.last_name?.[0] || ''}`.toUpperCase(),
    photo: rnd.profile_photo || (careRnd.value?.id === rnd.id ? careRnd.value.photo : ''),
    format: `${APPT_TYPES[a.type] || ''} consultation`.trim(),
  }
})

/* ---------- Next step (banner) ---------- */
const nextStep = computed(() => {
  const appt = nextAppointment.value
  const rndName = careRnd.value ? `RND ${careRnd.value.name}` : 'your RND'
  if (!screening.value) {
    return {
      eyebrow: 'YOUR NEXT STEP',
      text: 'Complete your health screening. It takes about a minute and gives your RND your BMI, calorie needs and nutrition risk before you meet.',
      short: 'Your health screening — about a minute.',
      action: 'Start Screening', to: '/pre-consultation-screening',
    }
  }
  // Pay before the consultation (unpaid ones are cancelled at the start time).
  if (appt?.status === 'confirmed' && appt.payment?.status === 'unpaid') {
    const amount = Number(appt.payment.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })
    return {
      eyebrow: 'PAYMENT DUE',
      text: `${rndName} confirmed your ${formatLongDate(appt.scheduled_at)} ${formatTime(appt.scheduled_at)} consultation. Pay ₱${amount} before then to start it — unpaid bookings are cancelled at the start time.`,
      action: `Pay ₱${amount}`, to: '/appointments',
    }
  }
  if (appt?.status === 'confirmed') {
    const when = `${formatLongDate(appt.scheduled_at)} at ${formatTime(appt.scheduled_at)}`
    // The API only sends the room link inside the join window (15 min early).
    const canJoin = (appt.type === 'video' && appt.video_session_url)
      || (appt.type === 'chat' && appt.payment?.status === 'paid' && Date.now() >= new Date(appt.join_opens_at) && Date.now() <= new Date(appt.join_closes_at))
    return {
      eyebrow: 'UPCOMING CONSULTATION',
      text: `${APPT_TYPES[appt.type] || ''} consultation with ${rndName} on ${when}.`,
      action: canJoin ? (appt.type === 'chat' ? 'Join Chat' : 'Join Video Call') : 'View Appointment',
      to: canJoin ? `/consultation-room/${appt.id}` : '/appointments',
    }
  }
  if (appt?.status === 'pending') {
    return {
      eyebrow: 'WAITING FOR CONFIRMATION',
      text: `Your ${formatLongDate(appt.scheduled_at)} ${formatTime(appt.scheduled_at)} booking is waiting for ${rndName} to confirm. We'll notify you as soon as they do.`,
      action: 'View Booking', to: '/appointments',
    }
  }
  // A booking request whose time passed before the RND confirmed it.
  if (!activeRelationship.value && expiredRequest.value) {
    const rnd = expiredRequest.value.relationship?.rnd
    return {
      eyebrow: 'BOOKING NOT CONFIRMED',
      text: `Your ${formatLongDate(expiredRequest.value.scheduled_at)} booking request${rnd ? ` with RND ${rnd.first_name} ${rnd.last_name}` : ''} wasn't confirmed before its time passed. Pick a new time, or choose another RND.`,
      short: 'Your last booking request expired. Pick a new time.',
      action: 'Book a New Time', to: rnd ? `/rnd-profile-view/${rnd.id}?book=1` : '/find-rnd',
    }
  }
  if (activeRelationship.value) {
    return {
      eyebrow: 'STAY ON TRACK',
      text: activePlan.value
        ? `You don't have an upcoming consultation with ${rndName}. Keep logging your meals, and book a follow-up when you're ready.`
        : `You don't have an upcoming consultation with ${rndName}. Book one to continue your care.`,
      short: `No consultation booked with ${rndName}.`,
      action: 'Book a Consultation', to: `/rnd-profile-view/${activeRelationship.value.rnd.id}?book=1`,
    }
  }
  return {
    eyebrow: 'YOUR NEXT STEP',
    text: 'Your screening is done. Find a licensed RND who fits your needs and book your first consultation.',
    short: 'Find an RND and book your first consultation.',
    action: 'Find an RND', to: '/find-rnd',
  }
})

/* ---------- Screening badges ---------- */
const nrsRiskLabel = computed(() => ({ no_risk: 'No Risk', at_risk: 'At Risk', high_risk: 'High Risk' }[screening.value?.nrs_risk] || ''))
const nrsTone = computed(() => ({ no_risk: 'good', at_risk: 'warn', high_risk: 'bad' }[screening.value?.nrs_risk] || 'neutral'))
const bmiTone = computed(() => ((screening.value?.bmi_category || '').toLowerCase().includes('normal') ? 'good' : 'warn'))

/* ---------- Meal plan ---------- */
// Only the plan the RND has sent (drafts never reach the client).
const activePlan = computed(() => mealPlans.value.find(p => p.status === 'active') || null)

// The RND's target when there's a plan; otherwise the screening's estimate.
const calorieTarget = computed(() => {
  if (activePlan.value?.target_kcal) {
    return { value: Math.round(Number(activePlan.value.target_kcal)), label: 'Daily Calorie Target', note: 'Set by your RND in your meal plan' }
  }
  if (screening.value?.tdee_kcal) {
    return { value: Math.round(Number(screening.value.tdee_kcal)), label: 'Estimated Daily Needs (TDEE)', note: 'Your RND will set your actual target' }
  }
  return { value: null, label: 'Daily Calorie Target', note: 'Complete your screening first' }
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
    const [appts, rels, latestScreening, progress, plans, logs, invs, notes] = await Promise.all([
      get('/client/appointments/'),
      get('/client/relationships/'),
      get('/client/screening/latest/').catch(() => null),
      get('/client/progress/').catch(() => []),
      get('/client/meal-plans/').catch(() => []),
      get('/client/meal-logs/').catch(() => []),
      get('/client/invoices/').catch(() => []),
      get('/notifications/').catch(() => []),
    ])
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
const checkable = computed(() => todayItems.value.filter(i => i.kind === 'task' || i.kind === 'meal'))
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
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }
.empty-note { font-size: 0.85rem; color: #9aaa9a; margin: 0; line-height: 1.5; }
.empty-note.spaced { margin-bottom: 16px; }

/* UNPAID INVOICE ROW */
.notice-row {
  display: flex; align-items: center; gap: 14px; background: #fff; border: 1px solid #eceeec;
  border-radius: 14px; padding: 14px 20px; margin: -8px 0 20px; text-decoration: none; color: #4a5a4a;
}
.notice-row .stat-icon { flex-shrink: 0; }
.notice-text { flex: 1; font-size: 0.85rem; }
.notice-text strong { color: #1a3a1a; }

/* STAT CARDS */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 14px; padding: 20px; border: 1px solid #eceeec; min-width: 0; }
.stat-top { margin-bottom: 12px; }
.stat-icon { width: 34px; height: 34px; border-radius: 9px; background: #eef3ec; display: flex; align-items: center; justify-content: center; color: #1e4a26; }
.stat-icon.icon-gold { background: #fdf1d6; color: #b8860b; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stat-label { font-size: 0.8rem; color: #6a7a6a; margin: 4px 0 8px; }
.stat-delta { font-size: 0.75rem; margin: 0; line-height: 1.4; }
.stat-delta.neutral { color: #8a9a8a; }
.stat-delta.good { color: #1f8f5c; font-weight: 600; }
.stat-delta.warn { color: #b8860b; font-weight: 600; }
.stat-delta.bad { color: #c0392b; font-weight: 600; }

/* GRID + PANELS */
.dash-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 20px; align-items: start; }
.dash-col { display: flex; flex-direction: column; gap: 20px; min-width: 0; }
.panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px; }
.today-row { display: flex; align-items: center; gap: 10px; padding: 10px 0; border-top: 1px solid #f0f2f0; text-decoration: none; color: inherit; }
.panel-header-row + .today-row { margin-top: 12px; border-top: none; }
.today-row.done { opacity: 0.55; }
.today-row.done .today-title { text-decoration: line-through; }
.today-icon { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #eef3ec; color: #1e4a26; }
.today-icon.k-reminder { background: #fdf1d6; color: #b8860b; }
.today-icon.k-appointment { background: #e3edf7; color: #2f6fa8; }
.today-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.today-title { font-size: 0.84rem; font-weight: 600; color: #1a3a1a; overflow-wrap: anywhere; }
.today-detail { font-size: 0.72rem; color: #8a9a8a; }
.today-time { font-size: 0.76rem; font-weight: 700; color: #4a5a4a; white-space: nowrap; }
.today-row.task { cursor: pointer; }
.task-check { width: 20px; height: 20px; margin: 0 5px; flex-shrink: 0; accent-color: #1f8f5c; cursor: pointer; }
.task-check.meal { display: inline-flex; align-items: center; justify-content: center; border: 2px solid #b9c4b9; border-radius: 5px; color: #fff; box-sizing: border-box; }
.task-check.meal.on { background: #1f8f5c; border-color: #1f8f5c; }
.task-x { border: none; background: none; color: #9aaa9a; cursor: pointer; padding: 2px; display: flex; }
.task-x:hover { color: #c0392b; }
.as-btn { background: none; border: none; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 3px; padding: 0; }
.add-task { display: flex; flex-direction: column; gap: 8px; background: #f7f9f7; border: 1px solid #eceeec; border-radius: 10px; padding: 10px; margin-bottom: 8px; }
.add-task .nm-input { min-height: 40px; }
.add-task-row { display: flex; gap: 8px; }
.add-task-row .nm-input { flex: 1; min-width: 0; }
.add-task-row .nm-select { flex: 1; min-width: 0; }
.add-error { font-size: 0.74rem; color: #a12525; margin: 0; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }
.panel-title.flush { margin: 0; }
.panel-sub { font-size: 0.78rem; color: #8a9a8a; margin: 3px 0 0; }
.panel-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 18px; }
.panel-link { font-size: 0.78rem; color: #1f8f5c; font-weight: 600; text-decoration: none; white-space: nowrap; }
.panel-link:hover { text-decoration: underline; }
.panel-meta { font-size: 0.78rem; color: #6a7a6a; font-weight: 600; white-space: nowrap; }

/* PILLS (meal log status only) */
.status-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-gold { background: #fdf1d6; color: #b8860b; }
.pill-muted { background: #eceeec; color: #8a9a8a; }
.badge-danger { background: #fdecec; color: #a12525; }

/* BUTTON — the RND dashboard's outlined block button */
.block-btn {
  display: block; width: 100%; text-align: center; background: #fff; border: 1px solid #1a3a1a; color: #1a3a1a;
  border-radius: 8px; padding: 10px; font-weight: 700; font-size: 0.85rem; font-family: inherit; cursor: pointer; text-decoration: none;
}
.block-btn:hover { background: #f7f9f7; }
.btn-row { display: flex; gap: 10px; }

/* TODAY'S MEAL PLAN */
.macro-strip {
  display: flex; flex-wrap: wrap; gap: 6px 16px; align-items: baseline;
  background: #f7f9f7; border-radius: 10px; padding: 10px 14px; margin-bottom: 14px; font-size: 0.82rem; color: #4a5a4a;
}
.macro-strip strong { color: #1a3a1a; }
.macro-source { font-size: 0.72rem; color: #9aaa9a; margin-left: auto; }
.meal-list { list-style: none; margin: 0; padding: 0; }
.meal-row { display: flex; align-items: center; gap: 12px; padding: 11px 0; border-top: 1px solid #f0f2f0; }
.meal-row:first-child { border-top: none; padding-top: 0; }
.meal-icon { width: 32px; height: 32px; border-radius: 9px; background: #eef3ec; color: #1e4a26; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.meal-info { flex: 1; min-width: 0; }
.meal-name { font-size: 0.87rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.meal-detail { font-size: 0.76rem; color: #8a9a8a; margin: 2px 0 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.adherence-row { display: grid; grid-template-columns: auto 1fr; gap: 18px; border-top: 1px solid #f0f2f0; margin-top: 12px; padding-top: 14px; }
.adherence-item { display: flex; align-items: baseline; gap: 8px; min-width: 0; }
.adherence-value { font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.adherence-label { font-size: 0.76rem; color: #8a9a8a; margin: 0; }
.empty-state { text-align: center; padding: 18px 10px; color: #9aaa9a; font-size: 0.85rem; }
.empty-state p { margin: 0; }
.empty-icon { color: #c5d0c5; margin-bottom: 8px; }
.empty-sub { font-size: 0.78rem; margin-top: 4px !important; line-height: 1.5; }

/* WEIGHT CHART */
.weight-chart { padding: 10px 0 4px; }

/* RND CARD */
.rnd-row { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.rnd-avatar { width: 52px; height: 52px; border-radius: 50%; background: #00382a; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.rnd-avatar-img { object-fit: cover; }
.rnd-text { min-width: 0; }
.rnd-name { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.rnd-specialty { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; }
.rnd-rating { font-size: 0.78rem; color: #b8860b; font-weight: 600; margin: 2px 0 0; }
.rnd-pending { font-size: 0.76rem; color: #b8860b; margin: 4px 0 0; }
/* Compact "Your RND" card at the top of the right column. */
.rnd-compact { display: flex; align-items: center; gap: 12px; padding: 14px 16px; }
.rnd-compact .rnd-avatar { width: 44px; height: 44px; font-size: 0.85rem; }
.rnd-compact .rnd-text { flex: 1; min-width: 0; }
.rnd-compact .rnd-name { overflow-wrap: anywhere; }
.rnd-eyebrow { font-size: 0.64rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #b8860b; margin: 0 0 1px; }
.rnd-actions { display: flex; gap: 6px; flex-shrink: 0; }
.icon-action { width: 36px; height: 36px; border-radius: 10px; border: 1px solid #dde3dd; display: flex; align-items: center; justify-content: center; color: #1a3a1a; text-decoration: none; }
.icon-action:hover { background: #f4f8f4; border-color: #b9d3be; }

/* LATEST SCREENING */
.screening-summary-text { font-size: 0.84rem; color: #6a7a6a; margin: 0 0 16px; line-height: 1.5; }

/* RECENT ACTIVITY */
.activity-row { display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-top: 1px solid #f0f2f0; }
.activity-row:first-of-type { border-top: none; padding-top: 0; }
.activity-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; margin-top: 6px; background: #c5d0c5; }
.activity-dot.unread { background: #D4A017; }
.activity-text { min-width: 0; }
.activity-title { font-size: 0.83rem; font-weight: 600; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.activity-time { font-size: 0.72rem; color: #9aaa9a; margin: 2px 0 0; }

@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dash-grid { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .stat-grid { gap: 12px; }
  .stat-card { padding: 16px; }
  .stat-value { font-size: 1.35rem; }
  .panel { padding: 18px 16px; }
  .adherence-row { grid-template-columns: 1fr; gap: 8px; }
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