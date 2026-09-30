<template>
  <div class="meal-plan-page">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="plan">
      <div class="targets-card">
        <div class="targets-header">
          <div>
            <h3 class="targets-title">{{ plan.name }}</h3>
            <p class="targets-sub">{{ conditionLabel }} · Prescribed by your RND</p>
          </div>
          <span class="progress-pill">{{ completionPct }}% Followed Today</span>
        </div>
        <div class="targets-grid">
          <div class="target-box">
            <p class="target-label">Calories</p>
            <p class="target-value">{{ plan.target_kcal ? Math.round(plan.target_kcal).toLocaleString() : '—' }}</p>
          </div>
          <div class="target-box">
            <p class="target-label">Carbs</p>
            <p class="target-value gold">{{ plan.target_carb_g ? Math.round(plan.target_carb_g) + 'g' : '—' }}</p>
          </div>
          <div class="target-box">
            <p class="target-label">Protein</p>
            <p class="target-value green">{{ plan.target_protein_g ? Math.round(plan.target_protein_g) + 'g' : '—' }}</p>
          </div>
          <div class="target-box">
            <p class="target-label">Fat</p>
            <p class="target-value brown">{{ plan.target_fat_g ? Math.round(plan.target_fat_g) + 'g' : '—' }}</p>
          </div>
        </div>
      </div>

      <div v-if="plan.notes || plan.allergies_restrictions" class="notes-panel">
        <p class="notes-title">Your RND's Notes</p>
        <p v-if="plan.allergies_restrictions" class="notes-text"><strong>Allergies / Restrictions:</strong> {{ plan.allergies_restrictions }}</p>
        <p v-if="plan.notes" class="notes-text">{{ plan.notes }}</p>
      </div>

      <template v-if="todaysMeals.length">
        <p class="today-label">Today · {{ todayLabel }}</p>
        <div class="meal-tabs">
          <button
            v-for="(meal, i) in todaysMeals" :key="meal.id"
            class="meal-tab" :class="{ active: activeMealIndex === i }"
            @click="activeMealIndex = i"
          >
            <component :is="mealIcon(meal.meal_time)" :size="14" />
            {{ mealTimeLabel(meal.meal_time) }}
            <span v-if="logFor(meal.id)" class="tab-status-dot" :class="logFor(meal.id).status === 'followed' ? 'dot-green' : 'dot-gold'"></span>
          </button>
        </div>

        <div class="meal-card">
          <div class="meal-header">
            <div>
              <h3 class="meal-name">{{ mealTimeLabel(activeMeal.meal_time) }}</h3>
              <p v-if="activeMeal.scheduled_time" class="meal-scheduled">Scheduled Time: {{ formatClock(activeMeal.scheduled_time) }}</p>
            </div>
            <span class="status-pill" :class="activeLog?.status === 'followed' ? 'pill-green' : 'pill-muted'">
              {{ activeLog ? statusLabel(activeLog.status) : 'Not logged yet' }}
            </span>
          </div>

          <div class="meal-body">
            <div class="meal-col">
              <span class="col-eyebrow">Planned Meal</span>
              <span class="exchange-summary">{{ exchangeSummary(activeMeal) }}</span>
              <div v-if="activeMeal.food_items.length" class="food-item-list">
                <div v-for="item in activeMeal.food_items" :key="item.id" class="planned-item">
                  <span class="planned-dot"></span>
                  <div>
                    <span class="food-name">{{ item.food_name }}</span>
                    <span class="food-note">{{ item.household_measure || item.notes || `${item.exchanges} Exchange` }}</span>
                  </div>
                </div>
              </div>
              <p v-else class="no-items-note">No specific foods listed for this meal yet.</p>
              <p v-if="activeMeal.meal_notes" class="meal-note-text"><strong>Note:</strong> {{ activeMeal.meal_notes }}</p>
            </div>

            <div class="meal-col">
              <span class="col-eyebrow">Actual Food Intake</span>

              <label class="dropzone-inline">
                <input type="file" accept="image/*" class="dropzone-input" @change="onPhotoSelected" />
                <UploadCloud :size="20" class="dropzone-icon" />
                <span class="dropzone-text">
                  <template v-if="logForm.photoName">{{ logForm.photoName }}</template>
                  <template v-else-if="activeLog?.photo_url">Photo already logged for today — choose a file to replace it</template>
                  <template v-else>Upload a photo of what you ate</template>
                </span>
              </label>

              <div class="meal-log-row">
                <div class="field">
                  <label>Time Logged</label>
                  <div class="time-input-wrap">
                    <input v-model="logForm.timeLogged" type="time" />
                    <Clock :size="14" class="time-icon" />
                  </div>
                </div>
                <div class="field">
                  <label>Meal Status</label>
                  <select v-model="logForm.status">
                    <option value="">Select status</option>
                    <option v-for="s in mealStatusOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
                  </select>
                </div>
              </div>

              <div v-if="logForm.status === 'partially_followed' || logForm.status === 'not_followed'" class="field notes-field">
                <label>Reason / Notes</label>
                <textarea v-model="logForm.reasonNotes" rows="2" placeholder="e.g. Ran out of time, ate something else instead..."></textarea>
              </div>

              <p v-if="logError" class="form-error inline">{{ logError }}</p>

              <button v-if="logForm.status" class="save-log-btn" :disabled="isSavingLog" @click="saveMealLog">
                <Save :size="15" /> {{ isSavingLog ? 'Saving…' : 'Save' }}
              </button>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="empty-note-card">Your plan has no meals scheduled for today ({{ todayLabel }}).</div>

      <div class="info-note">
        <Info :size="16" />
        <p>Exchange amounts are based on the FNRI Food Exchange Lists. Your RND may adjust portions during follow-up consultations based on your progress. Your meal logs are sent directly to your RND.</p>
      </div>
    </template>

    <div v-else class="empty-state">
      <div class="empty-icon"><ClipboardList :size="28" /></div>
      <p class="empty-title">No meal plan yet</p>
      <p class="empty-desc">Your RND will create a personalized meal plan for you as part of your care journey.</p>
    </div>

    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle2 :size="16" /> {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Info, ClipboardList, Sunrise, Coffee, Sun, Moon, Clock, UploadCloud, Save, CheckCircle2 } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'My Meal Plan' })

const { get, post } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const plans = ref([])
const activeMealIndex = ref(0)
// Local date — toISOString() is UTC and gives yesterday before 8 AM in PHT.
const now = new Date()
const todayIso = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
const todayDow = now.getDay()
const todayLabel = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

// Only the plan the RND has sent (drafts never reach the client; archived
// plans have been replaced).
const plan = computed(() => plans.value.find(p => p.status === 'active') || null)

const CONDITION_LABELS = {
  diabetes: 'Diabetes Mellitus', hypertension: 'Hypertension', renal: 'Renal Condition',
  weight_loss: 'Weight Loss', weight_gain: 'Weight Gain', general: 'General',
}
const conditionLabel = computed(() => CONDITION_LABELS[plan.value?.condition] || plan.value?.condition)

const MEAL_ORDER = ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner', 'bedtime_snack']
const MEAL_LABELS = {
  breakfast: 'Breakfast', am_snack: 'AM Snack', lunch: 'Lunch',
  pm_snack: 'PM Snack', dinner: 'Dinner', bedtime_snack: 'Bedtime Snack',
}
const MEAL_ICONS = { breakfast: Sunrise, am_snack: Coffee, lunch: Sun, pm_snack: Coffee, dinner: Moon, bedtime_snack: Moon }

const mealStatusOptions = [
  { value: 'followed', label: 'Followed Plan' },
  { value: 'partially_followed', label: 'Partially Followed' },
  { value: 'not_followed', label: 'Did Not Follow' },
]
function statusLabel(value) {
  return mealStatusOptions.find(s => s.value === value)?.label || value
}

function orderedMeals(meals) {
  return [...meals].sort((a, b) => MEAL_ORDER.indexOf(a.meal_time) - MEAL_ORDER.indexOf(b.meal_time))
}
function mealTimeLabel(time) {
  return MEAL_LABELS[time] || time
}
function mealIcon(time) {
  return MEAL_ICONS[time] || Sun
}
function exchangeSummary(meal) {
  const parts = []
  const map = { rice_exchanges: 'Rice', meat_exchanges: 'Meat', vegetable_exchanges: 'Veg', fruit_exchanges: 'Fruit', milk_exchanges: 'Milk', fat_exchanges: 'Fat', sugar_exchanges: 'Sugar' }
  for (const [field, label] of Object.entries(map)) {
    const value = Number(meal[field])
    if (value > 0) parts.push(`${value} ${label}`)
  }
  return parts.join(' · ') || 'No exchanges set'
}

// Plans are per weekday; meals with no day (older plans) apply every day.
const todaysMeals = computed(() =>
  orderedMeals((plan.value?.meals || []).filter(m => m.day_of_week === todayDow || m.day_of_week === null))
)
const activeMeal = computed(() => todaysMeals.value[activeMealIndex.value] || null)

function formatClock(t) {
  const [h, m] = t.split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}

/* ---------- ADHERENCE LOGS (today's actual food intake) ---------- */
const todaysLogs = ref([]) // MealLog rows for today, keyed by meal_plan_meal id
function logFor(mealId) {
  return todaysLogs.value.find(l => l.meal_plan_meal === mealId) || null
}
const activeLog = computed(() => activeMeal.value ? logFor(activeMeal.value.id) : null)

const logForm = reactive({ status: '', timeLogged: '', reasonNotes: '', photoFile: null, photoName: '' })

function resetLogForm() {
  const existing = activeLog.value
  logForm.status = existing?.status || ''
  logForm.timeLogged = existing?.time_logged?.slice(0, 5) || ''
  logForm.reasonNotes = existing?.reason_notes || ''
  logForm.photoFile = null
  logForm.photoName = ''
}
watch(activeMealIndex, resetLogForm)
watch(todaysLogs, resetLogForm)

function onPhotoSelected(e) {
  const file = e.target.files?.[0]
  if (file) {
    logForm.photoFile = file
    logForm.photoName = file.name
  }
}

const completionPct = computed(() => {
  const meals = todaysMeals.value
  if (!meals.length) return 0
  const followed = meals.filter(m => logFor(m.id)?.status === 'followed').length
  return Math.round((followed / meals.length) * 100)
})

/* ---------- SAVE + NOTIFY RND ---------- */
const isSavingLog = ref(false)
const logError = ref('')
const toastVisible = ref(false)
const toastMessage = ref('')
let toastTimer = null
function fireToast(msg) {
  toastMessage.value = msg
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 4000)
}

async function saveMealLog() {
  if (!activeMeal.value || !logForm.status) return
  isSavingLog.value = true
  logError.value = ''
  try {
    const form = new FormData()
    form.append('log_date', todayIso)
    form.append('status', logForm.status)
    if (logForm.timeLogged) form.append('time_logged', logForm.timeLogged)
    if (logForm.reasonNotes) form.append('reason_notes', logForm.reasonNotes)
    if (logForm.photoFile) form.append('photo', logForm.photoFile)

    const saved = await post(`/client/meals/${activeMeal.value.id}/log/`, form)
    const idx = todaysLogs.value.findIndex(l => l.meal_plan_meal === activeMeal.value.id)
    if (idx >= 0) todaysLogs.value.splice(idx, 1, saved)
    else todaysLogs.value.push(saved)

    fireToast(`${mealTimeLabel(activeMeal.value.meal_time)} log saved & sent to your RND!`)
  } catch (error) {
    logError.value = error?.data?.detail || 'Could not save this log. Please try again.'
  } finally {
    isSavingLog.value = false
  }
}

async function loadMealPlans() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [mealPlans, logs] = await Promise.all([
      get('/client/meal-plans/'),
      get(`/client/meal-logs/?date=${todayIso}`),
    ])
    plans.value = mealPlans
    todaysLogs.value = logs
    resetLogForm()
  } catch {
    errorMessage.value = 'Could not load your meal plan. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadMealPlans)
</script>

<style scoped>
* { box-sizing: border-box; }
.meal-plan-page { font-family: 'Inter', sans-serif; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.form-error.inline { margin: 14px 0 0; }
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.status-pill { font-size: 0.76rem; font-weight: 700; padding: 5px 14px; border-radius: 14px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-muted { background: #eceeec; color: #7a8a7a; }

/* TARGETS CARD */
.targets-card { background: #fff; border: 1px solid #eceeec; border-radius: 16px; padding: 26px 28px; margin-bottom: 22px; }
.targets-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 22px; }
.targets-title { font-family: 'Playfair Display', serif; font-size: 1.25rem; color: #1a3a1a; margin: 0 0 5px; }
.targets-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }
.progress-pill { font-size: 0.82rem; font-weight: 700; background: #e3f3ea; color: #1f8f5c; padding: 6px 15px; border-radius: 999px; white-space: nowrap; }

.targets-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 22px; }
.target-box { background: #f7f9f7; border: 1px solid #eceeec; border-radius: 12px; padding: 18px; }
.target-label { font-size: 0.76rem; letter-spacing: 0.06em; text-transform: uppercase; color: #9aaa9a; font-weight: 700; margin: 0 0 8px; }
.target-value { font-family: 'Playfair Display', serif; font-size: 1.65rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.target-value.gold { color: #D4A017; }
.target-value.green { color: #1f8f5c; }
.target-value.brown { color: #b8860b; }

/* NOTES PANEL */
.notes-panel { background: #fdf1d6; border-left: 4px solid #D4A017; border-radius: 12px; padding: 20px 24px; margin-bottom: 22px; }
.notes-title { font-weight: 700; color: #b8860b; font-size: 0.92rem; letter-spacing: 0.03em; margin: 0 0 8px; }
.notes-text { font-size: 0.9rem; color: #5a5240; line-height: 1.6; margin: 0; }

/* MEAL TABS */
.meal-tabs { display: flex; gap: 6px; margin-bottom: 16px; flex-wrap: wrap; }
.meal-tab {
  display: inline-flex; align-items: center; gap: 7px; border: 1px solid #eceeec; background: #fff;
  padding: 10px 18px; border-radius: 999px; font-size: 0.85rem; font-weight: 600; color: #6a7a6a; cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.meal-tab:hover:not(.active) { background: #f7f9f7; }
.meal-tab.active { background: #14301a; border-color: #14301a; color: #fff; }
.tab-status-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.dot-green { background-color: #4ade80; }
.dot-gold { background-color: #D4A017; }

/* MEAL CARD */
.meal-card { background: #fff; border: 1px solid #eceeec; border-radius: 16px; overflow: hidden; margin-bottom: 20px; }
.meal-header { display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 18px 26px; background: #f2f7f3; }
.meal-name { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0; }
.meal-scheduled { font-size: 0.82rem; color: #9aaa9a; margin: 3px 0 0; }
.today-label { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.04em; color: #6a7a6a; text-transform: uppercase; margin: 0 0 10px; }

.meal-body { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; padding: 22px 26px; }
.meal-col { min-width: 0; }
.col-eyebrow { display: block; font-size: 0.76rem; letter-spacing: 0.06em; text-transform: uppercase; font-weight: 700; color: #1e4a26; margin-bottom: 12px; }
.exchange-summary { display: block; font-size: 0.76rem; color: #9aaa9a; margin: -8px 0 12px; }

.food-item-list { display: flex; flex-direction: column; gap: 10px; }
.planned-item { display: flex; align-items: center; gap: 12px; background: #f7f9f7; border: 1px solid #eceeec; border-radius: 10px; padding: 13px 16px; }
.planned-dot { width: 8px; height: 8px; border-radius: 50%; background: #D4A017; flex-shrink: 0; }
.food-name { font-size: 0.9rem; color: #2a3a2a; font-weight: 600; margin-right: 8px; }
.food-note { color: #9aaa9a; font-size: 0.78rem; }
.no-items-note { font-size: 0.83rem; color: #9aaa9a; margin: 0; }
.meal-note-text { font-size: 0.85rem; color: #4a5a4a; margin: 16px 0 0; line-height: 1.5; }
.meal-note-text strong { color: #1a3a1a; }

.dropzone-inline {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  background: #f7f9f7; border: 1.5px dashed #b8c8b8; border-radius: 10px;
  min-height: 76px; padding: 16px; cursor: pointer; margin-bottom: 14px; text-align: center;
}
.dropzone-input { display: none; }
.dropzone-icon { color: #1a5a2a; flex-shrink: 0; }
.dropzone-text { font-size: 0.85rem; color: #4a5a4a; }
.meal-log-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.field label { display: block; font-size: 0.76rem; letter-spacing: 0.05em; text-transform: uppercase; font-weight: 700; color: #9aaa9a; margin-bottom: 7px; }
.field select {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 12px; font-size: 0.86rem; font-family: inherit; color: #2a2a2a; background: #fff;
}
.time-input-wrap { position: relative; }
.time-input-wrap input { width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 32px 11px 12px; font-size: 0.86rem; font-family: inherit; color: #2a2a2a; }
.time-icon { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #9aaa9a; pointer-events: none; }

.notes-field { margin-top: 14px; }
.notes-field textarea {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #2a2a2a; resize: vertical;
}

.save-log-btn {
  display: inline-flex; align-items: center; gap: 7px; background: #14301a; color: #fff; border: none;
  border-radius: 8px; padding: 10px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; margin-top: 16px;
}
.save-log-btn:hover { background: #1c421f; }
.save-log-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.empty-note-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 24px; text-align: center;
  font-size: 0.85rem; color: #9aaa9a; margin-bottom: 20px;
}

.info-note {
  display: flex; gap: 10px; align-items: flex-start;
  background: #eef3ec; color: #1e4a26; border-radius: 10px; padding: 14px 16px;
}
.info-note p { font-size: 0.83rem; color: #4a5a4a; margin: 0; line-height: 1.6; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; }

/* TOAST */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

@media (max-width: 800px) {
  .targets-grid { grid-template-columns: repeat(2, 1fr); }
  .meal-body { grid-template-columns: 1fr; }
}
</style>
