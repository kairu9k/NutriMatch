<template>
  <div class="meal-plan-page">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="plan">
      <!-- your allergies first, always open -->
      <div v-if="myAllergies.length" class="allergy-panel" role="note">
        <AlertTriangle :size="18" aria-hidden="true" />
        <p><strong>Your food allergies: {{ myAllergies.join(', ') }}.</strong> A food in your plan that may contain one is marked in red. Don't eat it, and message your RND.</p>
      </div>

      <!-- PLAN CARD: name, the targets as a bento, and the RND's notes in the same card -->
      <section class="plan-card">
        <div class="plan-head">
          <h3 class="plan-name">{{ planName }}</h3>
          <p class="plan-sub">{{ conditionLabel }}, from your RND</p>
        </div>
        <div class="plan-grid" :class="{ 'no-notes': !(plan.notes || plan.allergies_restrictions) }">
          <div class="bento">
            <div class="bento-main">
              <span class="bento-label">Calories a day</span>
              <span class="bento-big">{{ plan.target_kcal ? Math.round(plan.target_kcal).toLocaleString() : '—' }}</span>
              <span class="bento-unit">kcal</span>
            </div>
            <div class="bento-rows">
              <div class="bento-row"><span>Carbs</span><strong class="gold">{{ plan.target_carb_g ? `${Math.round(plan.target_carb_g)} g` : '—' }}</strong></div>
              <div class="bento-row"><span>Protein</span><strong class="green">{{ plan.target_protein_g ? `${Math.round(plan.target_protein_g)} g` : '—' }}</strong></div>
              <div class="bento-row"><span>Fat</span><strong class="brown">{{ plan.target_fat_g ? `${Math.round(plan.target_fat_g)} g` : '—' }}</strong></div>
            </div>
          </div>
          <div v-if="plan.notes || plan.allergies_restrictions" class="plan-notes">
            <p class="notes-title">Notes from your RND</p>
            <p v-if="plan.allergies_restrictions" class="notes-text"><strong>Allergies and restrictions:</strong> {{ plan.allergies_restrictions }}</p>
            <p v-if="plan.notes" class="notes-text">{{ plan.notes }}</p>
          </div>
        </div>
        <!-- Any other targets the RND added (fiber, sodium, ...) -->
        <div v-if="otherTargets.length" class="other-targets">
          <span class="other-targets-label">Other targets:</span>
          <span v-for="t in otherTargets" :key="t.label" class="other-target-chip">{{ t.label }}: {{ t.value }}{{ t.unit ? ` ${t.unit}` : '' }}</span>
        </div>
      </section>

      <!-- TODAY: every meal in one list; tap one to open it and log it -->
      <section v-if="todaysMeals.length" class="day">
        <div class="day-head">
          <h3 class="day-title">Today, {{ todayLabel }}</h3>
          <span class="day-progress" :aria-label="`${loggedCount} of ${todaysMeals.length} meals logged`">
            <span class="pips" aria-hidden="true"><span v-for="(m, i) in todaysMeals" :key="m.id" class="pip" :class="{ on: logFor(m.id) }" /></span>
            {{ loggedCount }} of {{ todaysMeals.length }} logged
          </span>
        </div>

        <div v-for="(meal, i) in todaysMeals" :key="meal.id" class="meal" :class="{ open: activeMealIndex === i }">
          <button type="button" class="meal-row" :aria-expanded="activeMealIndex === i" @click="toggleMeal(i)">
            <span class="meal-time">{{ meal.scheduled_time ? formatClock(meal.scheduled_time) : '' }}</span>
            <span class="meal-main">
              <span class="meal-name">{{ mealTimeLabel(meal.meal_time) }}<span v-if="mealHasAllergen(meal)" class="allergy-tag"><AlertTriangle :size="12" aria-hidden="true" /> Allergy</span></span>
              <span class="meal-foods">{{ foodLine(meal) }}</span>
            </span>
            <span class="meal-state" :class="mealState(meal).cls"><span class="dot" aria-hidden="true" />{{ mealState(meal).label }}</span>
            <ChevronDown :size="16" class="chev" aria-hidden="true" />
          </button>

          <div v-if="activeMealIndex === i" class="meal-open">
            <div class="meal-col">
              <p class="col-title">Planned <span class="exchange-summary">{{ exchangeSummary(meal) }}</span></p>
              <ul v-if="meal.food_items.length" class="food-list">
                <li v-for="item in meal.food_items" :key="item.id" class="food" :class="{ allergen: foodAllergies(item).length }">
                  <span class="food-name">{{ item.food_name }}</span>
                  <span class="food-note">{{ item.household_measure || item.notes || `${item.exchanges} exchange` }}</span>
                  <span v-for="w in foodAllergies(item)" :key="w" class="allergy-tag"><AlertTriangle :size="12" aria-hidden="true" /> {{ w }}</span>
                </li>
              </ul>
              <p v-else class="no-items-note">No specific foods listed for this meal yet.</p>
              <p v-if="meal.meal_notes" class="meal-note-text"><strong>Note:</strong> {{ meal.meal_notes }}</p>
            </div>

            <div class="meal-col log-col">
              <p class="col-title">What you ate</p>
              <p v-if="activeLog?.time_logged" class="logged-at">Logged at {{ formatClock(activeLog.time_logged) }}<template v-if="activeLog.status">, rated by your RND</template></p>

              <input :ref="(el) => { if (el) photoInput = el }" type="file" accept="image/*" class="dropzone-input" @change="onPhotoSelected" />
              <div v-if="photoPreview" class="photo-preview">
                <button type="button" class="photo-thumb" aria-label="View the photo full size" @click="viewerOpen = true">
                  <img :src="photoPreview" :alt="logForm.photoFile ? 'Selected photo of what you ate' : 'Photo you logged for this meal'" />
                </button>
                <div class="photo-meta">
                  <span class="photo-name">{{ logForm.photoFile ? logForm.photoName : 'Saved photo' }}</span>
                  <span v-if="logForm.photoFile" class="photo-sub">Not saved yet. Press Save to send it.</span>
                  <div class="photo-actions">
                    <button type="button" class="photo-btn" @click="photoInput?.click()">Change photo</button>
                    <button v-if="logForm.photoFile" type="button" class="photo-btn remove" @click="removePhoto"><X :size="13" aria-hidden="true" /> Remove</button>
                  </div>
                </div>
              </div>
              <button v-else type="button" class="dropzone-inline" @click="photoInput?.click()">
                <UploadCloud :size="20" class="dropzone-icon" aria-hidden="true" />
                <span class="dropzone-text">Upload a photo of what you ate</span>
              </button>
              <p v-if="photoError" class="form-error inline">{{ photoError }}</p>

              <div class="field notes-field">
                <label for="meal-log-note">Note</label>
                <textarea id="meal-log-note" data-allow-emoji v-model="logForm.reasonNotes" rows="3" maxlength="1000"
                          placeholder="What did you eat? e.g. Had half the rice and added a banana."></textarea>
              </div>
              <p class="log-hint">Add a photo, a note or both. Your RND rates how closely it followed your plan.</p>
              <p v-if="logError" class="form-error inline">{{ logError }}</p>
              <button v-if="canSaveLog" class="save-log-btn" :disabled="isSavingLog" @click="saveMealLog">
                <Save :size="15" aria-hidden="true" /> {{ isSavingLog ? 'Saving…' : 'Save' }}
              </button>
            </div>
          </div>
        </div>

        <Teleport to="body">
          <div v-if="viewerOpen && photoPreview" class="photo-viewer" role="dialog" aria-modal="true" aria-label="Photo of what you ate" @click.self="viewerOpen = false">
            <button type="button" class="viewer-close" aria-label="Close" @click="viewerOpen = false"><X :size="20" /></button>
            <img :src="photoPreview" alt="Photo of what you ate, full size" />
          </div>
        </Teleport>
      </section>
      <div v-else class="empty-note-card">Your plan has no meals scheduled for today ({{ todayLabel }}).</div>

      <div class="info-note">
        <Info :size="16" aria-hidden="true" />
        <p>Portions follow the FNRI Food Exchange Lists. Your RND may change them at a follow-up consultation, and sees every meal you log.</p>
      </div>
    </template>

    <div v-else class="empty-state">
      <div class="empty-icon"><ClipboardList :size="28" /></div>
      <p class="empty-title">No meal plan yet</p>
      <p class="empty-desc">Your RND makes your meal plan after your consultation. It shows here, meal by meal.</p>
    </div>

    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle2 :size="16" /> {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { phIso, phWeekday } from '~/utils/phTime'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { Info, ClipboardList, Sunrise, Coffee, Sun, Moon, UploadCloud, Save, CheckCircle2, X, AlertTriangle, ChevronDown } from 'lucide-vue-next'
import { allergyWarnings } from '~/utils/foodWarnings'

definePageMeta({ layout: 'dashboard', title: 'My Meal Plan' })

const { get, post } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const plans = ref([])
const activeMealIndex = ref(0)
// Philippine date on the server's clock (the server decides the log day anyway).
const now = new Date()
const todayIso = phIso(now)
const todayDow = phWeekday(now)
const todayLabel = now.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })

// Only the plan the RND has sent (drafts never reach the client; archived
// plans have been replaced).
const plan = computed(() => plans.value.find(p => p.status === 'active') || null)

const CONDITION_LABELS = {
  diabetes: 'Diabetes mellitus', hypertension: 'Hypertension', renal: 'Renal condition',
  weight_loss: 'Weight loss', weight_gain: 'Weight gain', general: 'General',
}
const conditionLabel = computed(() => CONDITION_LABELS[plan.value?.condition] || plan.value?.condition)

const MEAL_ORDER = ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner', 'bedtime_snack']
const MEAL_LABELS = {
  breakfast: 'Breakfast', am_snack: 'Morning snack', lunch: 'Lunch',
  pm_snack: 'Afternoon snack', dinner: 'Dinner', bedtime_snack: 'Bedtime snack',
}
const MEAL_ICONS = { breakfast: Sunrise, am_snack: Coffee, lunch: Sun, pm_snack: Coffee, dinner: Moon, bedtime_snack: Moon }

function pillClass(log) {
  if (!log) return 'pill-muted'
  return { followed: 'pill-green', partially_followed: 'pill-gold', not_followed: 'pill-red' }[log.status] || 'pill-gold'
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
  const map = { rice_exchanges: 'rice', meat_exchanges: 'meat', vegetable_exchanges: 'vegetable', fruit_exchanges: 'fruit', milk_exchanges: 'milk', fat_exchanges: 'fat', sugar_exchanges: 'sugar' }
  for (const [field, label] of Object.entries(map)) {
    const value = Number(meal[field])
    if (value > 0) parts.push(`${value} ${label}`)
  }
  return parts.join(', ') || 'No exchanges set'
}

// Plans are per weekday; meals with no day (older plans) apply every day.
// Plan targets other than the three macros shown in the boxes above.
const MACRO_LABELS = ['protein', 'proteins', 'carb', 'carbs', 'carbohydrate', 'carbohydrates', 'fat', 'fats', 'total fat']
const otherTargets = computed(() =>
  (plan.value?.nutrient_targets || []).filter(t => t.value && !MACRO_LABELS.includes(t.label.toLowerCase()))
)

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

const logForm = reactive({ reasonNotes: '', photoFile: null, photoName: '' })
// Save shows once there's something new: a photo, or a note different from the saved one.
const canSaveLog = computed(() => !!logForm.photoFile
  || (logForm.reasonNotes.trim() && logForm.reasonNotes.trim() !== (activeLog.value?.reason_notes || '').trim()))

function resetLogForm() {
  const existing = activeLog.value
  logForm.reasonNotes = existing?.reason_notes || ''
  removePhoto()
  viewerOpen.value = false
}
watch(activeMealIndex, resetLogForm)
watch(todaysLogs, resetLogForm)

// Photo preview: a temporary in-browser link to the chosen file (released
// when it's changed, removed, saved or the meal changes), else today's saved photo.
const photoInput = ref(null)
const selectedUrl = ref('')
const photoError = ref('')
const viewerOpen = ref(false)
const photoPreview = computed(() => selectedUrl.value || activeLog.value?.photo_url || '')

function onPhotoSelected(e) {
  const file = e.target.files?.[0]
  e.target.value = '' // so picking the same file again still counts as a change
  if (!file) return
  if (!file.type.startsWith('image/')) {
    photoError.value = 'Please choose a photo (JPG, PNG or WEBP).'
    return
  }
  photoError.value = ''
  if (selectedUrl.value) URL.revokeObjectURL(selectedUrl.value)
  selectedUrl.value = URL.createObjectURL(file)
  logForm.photoFile = file
  logForm.photoName = file.name
}
function removePhoto() {
  if (selectedUrl.value) URL.revokeObjectURL(selectedUrl.value)
  selectedUrl.value = ''
  photoError.value = ''
  logForm.photoFile = null
  logForm.photoName = ''
}
function onViewerKey(e) { if (e.key === 'Escape') viewerOpen.value = false }
onMounted(() => document.addEventListener('keydown', onViewerKey))
onUnmounted(() => {
  document.removeEventListener('keydown', onViewerKey)
  if (selectedUrl.value) URL.revokeObjectURL(selectedUrl.value)
})

// The client's own recorded allergies: shown in red, and on every food that
// may match (same word list the RND's editor uses, utils/foodWarnings.js).
const myAllergies = ref([])
function foodAllergies(item) {
  return allergyWarnings(item.food_name, myAllergies.value)
}

// Older generated plans were named "… plan — 1,600 kcal": show it with a comma.
const planName = computed(() => (plan.value?.name || '').replace(' — ', ', '))
const loggedCount = computed(() => todaysMeals.value.filter(m => logFor(m.id)).length)
function foodLine(meal) {
  const names = (meal.food_items || []).map(f => f.food_name.split(' (')[0])
  if (!names.length) return 'No foods listed'
  return names.length > 4 ? `${names.slice(0, 4).join(', ')}, +${names.length - 4} more` : names.join(', ')
}
function mealHasAllergen(meal) {
  return (meal.food_items || []).some(f => foodAllergies(f).length)
}
function mealState(meal) {
  const log = logFor(meal.id)
  if (!log) return { cls: 'none', label: 'Not logged' }
  return {
    followed: { cls: 'green', label: 'Followed' },
    partially_followed: { cls: 'gold', label: 'Partly followed' },
    not_followed: { cls: 'red', label: 'Not followed' },
  }[log.status] || { cls: 'gold', label: 'Waiting for your RND' }
}
// One meal open at a time; tap it again to close.
function toggleMeal(i) {
  activeMealIndex.value = activeMealIndex.value === i ? -1 : i
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
  if (!activeMeal.value || !canSaveLog.value) return
  isSavingLog.value = true
  logError.value = ''
  try {
    const form = new FormData()
    form.append('log_date', todayIso)
    form.append('reason_notes', logForm.reasonNotes.trim())
    if (logForm.photoFile) form.append('photo', logForm.photoFile)

    const saved = await post(`/client/meals/${activeMeal.value.id}/log/`, form)
    const idx = todaysLogs.value.findIndex(l => l.meal_plan_meal === activeMeal.value.id)
    if (idx >= 0) todaysLogs.value.splice(idx, 1, saved)
    else todaysLogs.value.push(saved)
    resetLogForm() // show the saved photo/note (the watcher only sees a new list)

    fireToast(`${mealTimeLabel(activeMeal.value.meal_time)} log saved and sent to your RND.`)
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
    const [mealPlans, logs, profile] = await Promise.all([
      get('/client/meal-plans/'),
      get(`/client/meal-logs/?date=${todayIso}`),
      get('/client/profile/').catch(() => null),
    ])
    plans.value = mealPlans
    todaysLogs.value = logs
    myAllergies.value = profile?.health_profile?.allergies || []
    // open the first meal not logged yet (else the first one)
    const firstOpen = todaysMeals.value.findIndex(m => !logFor(m.id))
    activeMealIndex.value = firstOpen >= 0 ? firstOpen : 0
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
.placeholder-text { font-size: 0.85rem; color: #6a7a6a; }

.status-pill { font-size: 0.76rem; font-weight: 700; padding: 5px 14px; border-radius: 14px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-muted { background: #eef2ef; color: #4a5a4a; }
.pill-gold { background: #fbf3dc; color: #a07a10; }
.pill-red { background: #fbe1de; color: #c0483a; }
.status-col { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; text-align: right; }
.logged-at { font-size: 0.76rem; color: #6a7a6a; }
.log-hint { font-size: 0.78rem; color: #6a7a6a; margin: 8px 0 0; line-height: 1.5; }

/* YOUR ALLERGIES: always red, always first */
.allergy-panel { display: flex; gap: 10px; align-items: flex-start; background: #fdf1ef; border: 1.5px solid #c0392b; border-radius: 12px; padding: 14px 18px; margin-bottom: 18px; color: #8a1f14; }
.allergy-panel svg { flex-shrink: 0; margin-top: 2px; color: #c0392b; }
.allergy-panel p { margin: 0; font-size: 0.88rem; line-height: 1.5; }

.card-shadow, .plan-card, .day { background: #fff; border: 1px solid #d9e3dc; border-radius: 16px; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }

/* PLAN CARD: name, bento targets, RND notes */
.plan-card { padding: 20px 22px; margin-bottom: 18px; }
.plan-head { margin-bottom: 14px; }
.plan-name { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0 0 3px; }
.plan-sub { font-size: 0.86rem; color: #6a7a6a; margin: 0; }
.plan-grid { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 14px; }
.plan-grid.no-notes { grid-template-columns: minmax(0, 1fr); }
.bento { display: grid; grid-template-columns: minmax(130px, 0.9fr) minmax(0, 1fr); border: 1px solid #d9e3dc; border-radius: 14px; overflow: hidden; }
.bento-main { display: flex; flex-direction: column; justify-content: center; padding: 16px 18px; color: #fff; background: linear-gradient(135deg, #00382a 0%, #005a42 100%); }
.bento-label { font-size: 0.82rem; font-weight: 600; color: #e2c25e; }
.bento-big { font-family: 'Playfair Display', serif; font-size: 2.4rem; font-weight: 700; line-height: 1.05; margin-top: 4px; font-variant-numeric: lining-nums; }
.bento-unit { font-size: 0.82rem; color: rgba(255, 255, 255, 0.75); }
.bento-rows { display: flex; flex-direction: column; }
.bento-row { flex: 1; display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 16px; border-top: 1px solid #d9e3dc; font-size: 0.86rem; font-weight: 600; color: #4a5a4a; }
.bento-row:first-child { border-top: none; }
.bento-row strong { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; font-variant-numeric: lining-nums; }
.bento-row strong.gold { color: #D4A017; }
.bento-row strong.green { color: #1f8f5c; }
.bento-row strong.brown { color: #b8860b; }
.plan-notes { background: #fdf6e3; border-left: 3px solid #D4A017; border-radius: 12px; padding: 14px 16px; min-width: 0; max-height: 220px; overflow-y: auto; }
.notes-title { font-weight: 700; color: #b8860b; font-size: 0.88rem; margin: 0 0 6px; }
.notes-text { font-size: 0.86rem; color: #5a5240; line-height: 1.55; margin: 0 0 6px; overflow-wrap: anywhere; }
.notes-text:last-child { margin-bottom: 0; }
.other-targets { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 14px 0 0; }
.other-targets-label { font-size: 0.82rem; font-weight: 600; color: #4a5a4a; }
.other-target-chip { font-size: 0.8rem; color: #1a3a1a; background: #f2f6f3; border: 1px solid #d9e3dc; border-radius: 14px; padding: 4px 12px; }

/* TODAY: one list, one meal open */
.day { overflow: hidden; margin-bottom: 18px; }
.day-head { display: flex; align-items: center; justify-content: space-between; gap: 8px 16px; flex-wrap: wrap; padding: 16px 22px; border-bottom: 1px solid #d9e3dc; }
.day-title { font-family: 'Playfair Display', serif; font-size: 1.08rem; color: #1a3a1a; margin: 0; }
.day-progress { display: inline-flex; align-items: center; gap: 8px; font-size: 0.84rem; font-weight: 600; color: #1f6f46; }
.pips { display: inline-flex; gap: 4px; }
.pip { width: 9px; height: 9px; border-radius: 50%; border: 1.5px solid #9ec4ad; }
.pip.on { background: #1f8f5c; border-color: #1f8f5c; }

.meal + .meal { border-top: 1px solid #d9e3dc; }
.meal-row {
  display: grid; grid-template-columns: 76px minmax(0, 1fr) auto 18px; align-items: center; gap: 14px;
  width: 100%; padding: 14px 22px; border: none; background: #fff; text-align: left; font-family: inherit; cursor: pointer;
}
.meal-row:hover { background: #f7faf8; }
.meal-row:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.meal.open .meal-row { background: #f2f7f3; }
.meal-time { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; font-variant-numeric: tabular-nums; }
.meal-main { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.meal-name { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; font-size: 0.95rem; font-weight: 700; color: #1a3a1a; }
.meal-foods { font-size: 0.8rem; color: #6a7a6a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meal-state { display: inline-flex; align-items: center; gap: 7px; font-size: 0.8rem; font-weight: 600; color: #6a7a6a; white-space: nowrap; }
.meal-state .dot { width: 9px; height: 9px; border-radius: 50%; border: 1.5px solid #a9b8ad; }
.meal-state.green { color: #1f6f46; }
.meal-state.green .dot { background: #1f8f5c; border-color: #1f8f5c; }
.meal-state.gold { color: #8a6400; }
.meal-state.gold .dot { background: #D4A017; border-color: #D4A017; }
.meal-state.red { color: #a12525; }
.meal-state.red .dot { background: #c0392b; border-color: #c0392b; }
.chev { color: #6a7a6a; transition: transform 0.15s ease; }
.meal.open .chev { transform: rotate(180deg); }

.meal-open { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px; padding: 6px 22px 20px 112px; background: #f2f7f3; }
.meal-col { min-width: 0; }
.col-title { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 8px 0 8px; }
.exchange-summary { font-size: 0.78rem; font-weight: 500; color: #6a7a6a; margin-left: 6px; }
.logged-at { font-size: 0.78rem; color: #6a7a6a; margin: -4px 0 8px; }
.log-hint { font-size: 0.78rem; color: #6a7a6a; margin: 8px 0 0; line-height: 1.5; }

.food-list { list-style: none; margin: 0; padding: 0; background: #fff; border: 1px solid #d9e3dc; border-radius: 10px; overflow: hidden; }
.food { display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px 8px; padding: 9px 12px; }
.food + .food { border-top: 1px solid #d9e3dc; }
/* a food that may contain one of the client's allergens */
.food.allergen { background: #fdf1ef; box-shadow: inset 3px 0 0 #c0392b; }
.allergy-tag { display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; font-weight: 700; color: #fff; background: #c0392b; border-radius: 999px; padding: 2px 8px; }
.food-name { font-size: 0.88rem; color: #1a3a1a; font-weight: 600; }
.food-note { color: #6a7a6a; font-size: 0.8rem; }
.no-items-note { font-size: 0.83rem; color: #6a7a6a; margin: 0; }
.meal-note-text { font-size: 0.85rem; color: #4a5a4a; margin: 12px 0 0; line-height: 1.5; }
.meal-note-text strong { color: #1a3a1a; }

.dropzone-inline {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  background: #fff; border: 1.5px dashed #3f9a6b; border-radius: 10px;
  min-height: 76px; padding: 16px; cursor: pointer; margin-bottom: 14px; text-align: center;
  width: 100%; font-family: inherit;
}
.dropzone-inline:hover { border-color: #1a5a2a; }
.dropzone-inline:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.dropzone-input { display: none; }

.photo-preview {
  display: flex; align-items: center; gap: 14px; margin-bottom: 14px;
  background: #f7f9f7; border: 1px solid #dfe7df; border-radius: 10px; padding: 10px;
}
.photo-thumb {
  flex-shrink: 0; width: 112px; height: 112px; padding: 0; border: none; border-radius: 8px;
  overflow: hidden; cursor: zoom-in; background: #e8ede8;
}
.photo-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.photo-thumb:focus-visible { outline: 2px solid #D4A017; outline-offset: 2px; }
.photo-meta { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.photo-name { font-size: 0.85rem; font-weight: 600; color: #1a3a1a; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.photo-sub { font-size: 0.76rem; color: #8a6d10; }
.photo-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.photo-btn {
  display: inline-flex; align-items: center; gap: 4px; padding: 6px 12px; border-radius: 7px;
  border: 1px solid #c9d6c9; background: #fff; color: #1a3a1a; font-size: 0.78rem; font-weight: 600;
  font-family: inherit; cursor: pointer;
}
.photo-btn:hover { border-color: #1a5a2a; }
.photo-btn.remove { color: #b03a2e; }
.photo-btn.remove:hover { border-color: #b03a2e; }

.photo-viewer {
  position: fixed; inset: 0; z-index: 1000; background: rgba(10, 20, 12, 0.82);
  display: flex; align-items: center; justify-content: center; padding: 24px;
}
.photo-viewer img { max-width: min(92vw, 1000px); max-height: 86vh; border-radius: 10px; object-fit: contain; background: #fff; }
.viewer-close {
  position: absolute; top: 16px; right: 16px; width: 40px; height: 40px; border-radius: 50%;
  border: none; background: rgba(255, 255, 255, 0.92); color: #1a3a1a; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.dropzone-icon { color: #1a5a2a; flex-shrink: 0; }
.dropzone-text { font-size: 0.85rem; color: #4a5a4a; }
.field label { display: block; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; margin-bottom: 6px; }

.notes-field { margin-top: 14px; }
.notes-field textarea {
  background: #fff; width: 100%; border: 1px solid #d9e3dc; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #1a3a1a; resize: vertical;
}
.notes-field textarea:focus { outline: none; border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.15); }

.save-log-btn {
  display: inline-flex; align-items: center; gap: 7px; background: #0a4a37; color: #fff; border: none; font-family: inherit;
  border-radius: 8px; padding: 10px 18px; font-weight: 600; font-size: 0.85rem; cursor: pointer; margin-top: 16px;
}
.save-log-btn:hover { background: #00382a; }
.save-log-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.empty-note-card {
  background: #fff; border-radius: 12px; border: 1px solid #d9e3dc; padding: 24px; text-align: center;
  font-size: 0.85rem; color: #6a7a6a; margin-bottom: 20px;
}

.info-note {
  display: flex; gap: 10px; align-items: flex-start;
  background: #eef3ec; color: #1e4a26; border-radius: 10px; padding: 14px 16px;
}
.info-note p { font-size: 0.83rem; color: #4a5a4a; margin: 0; line-height: 1.6; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #d9e3dc;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #6a7a6a; margin: 0; }

/* TOAST */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

@media (max-width: 800px) {
  .plan-grid { grid-template-columns: minmax(0, 1fr); }
  .meal-open { grid-template-columns: minmax(0, 1fr); padding: 6px 16px 18px; gap: 8px; }
}
@media (max-width: 560px) {
  .plan-card { padding: 16px; }
  .bento-big { font-size: 2rem; }
  .day-head { padding: 14px 16px; }
  .meal-row { grid-template-columns: minmax(0, 1fr) 18px; grid-template-areas: "time chev" "main chev" "state chev"; gap: 2px 10px; padding: 12px 16px; }
  .meal-time { grid-area: time; font-size: 0.8rem; color: #4a5a4a; }
  .meal-main { grid-area: main; }
  .meal-state { grid-area: state; margin-top: 4px; }
  .chev { grid-area: chev; }
}
@media (prefers-reduced-motion: reduce) { .chev { transition: none; } }
</style>
