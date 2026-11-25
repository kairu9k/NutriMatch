<template>
  <div class="meal-plan-page">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text"><span class="mp-spin" aria-hidden="true"></span>Loading…</div>

    <template v-else-if="plan">
      <!-- BANNER: the plan, who made it, download, today's progress -->
      <section class="mp-hero">
        <img class="mp-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
        <span class="mp-hero-fade" aria-hidden="true"></span>
        <div class="mp-hero-text">
          <p class="mp-eyebrow"><span aria-hidden="true"></span>MY MEAL PLAN</p>
          <h3 class="plan-name">{{ planName }}</h3>
          <p class="plan-sub"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 20A7 7 0 0 1 4 13c0-6 7-9 16-9 0 9-3 16-9 16z" /><path d="M4 20c4-4 7-6 11-8" /></svg>{{ conditionLabel }}, from your RND</p>
          <div class="mp-hero-actions">
            <button type="button" class="mp-btn-gold" @click="downloadPlan"><Download :size="17" aria-hidden="true" /> Download / print</button>
            <span v-if="todaysMeals.length" class="mp-glass"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>{{ loggedCount }} of {{ todaysMeals.length }} meals logged today</span>
          </div>
        </div>
      </section>
      <p v-if="printBlocked" class="form-error inline">Your browser blocked the print window. Allow pop-ups for NutriMatch, then try again.</p>

      <!-- TARGETS: calories, the three macros, the RND's notes -->
      <section class="mp-targets" :class="{ 'no-notes': !(plan.notes || plan.allergies_restrictions) }">
        <div class="mp-card mp-cal">
          <p class="mp-k">CALORIES A DAY</p>
          <div class="mp-ring" :style="{ '--p': `${ringPct}%` }" aria-hidden="true">
            <span><strong>{{ plan.target_kcal ? Math.round(plan.target_kcal).toLocaleString() : '—' }}</strong><small>kcal</small></span>
          </div>
          <p class="mp-cal-note">Your daily target, set by your RND.<template v-if="todaysMeals.length"> The ring fills as you log today's meals.</template></p>
        </div>
        <div class="mp-card mp-macros">
          <p class="mp-k dark">DAILY TARGETS</p>
          <div v-for="m in macroRows" :key="m.key" class="mp-macro" :class="m.key">
            <div class="mp-macro-top"><span>{{ m.label }}</span><strong>{{ m.grams ? Math.round(m.grams) : '—' }}<small v-if="m.grams"> g</small></strong></div>
            <div class="mp-bar"><span :style="{ width: `${m.pct}%` }"></span></div>
            <p>{{ m.pct ? `${m.pct}% of calories` : 'Not set' }}</p>
          </div>
        </div>
        <div v-if="plan.notes || plan.allergies_restrictions" class="mp-card plan-notes">
          <p class="mp-k gold"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg>NOTES FROM YOUR RND</p>
          <p v-if="plan.allergies_restrictions" class="mp-allergy"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /><path d="M12 9v4M12 17h.01" /></svg><span><strong>Allergies and restrictions:</strong> {{ plan.allergies_restrictions }}</span></p>
          <p v-if="plan.notes" class="notes-text">{{ plan.notes }}</p>
        </div>
      </section>
      <!-- Any other targets the RND added (fiber, sodium, ...) -->
      <div v-if="otherTargets.length" class="other-targets">
        <span class="other-targets-label">Other targets</span>
        <span v-for="t in otherTargets" :key="t.label" class="other-target-chip">{{ t.label }}: <strong>{{ t.value }}{{ t.unit ? ` ${t.unit}` : '' }}</strong></span>
      </div>

      <template v-if="todaysMeals.length">
        <div class="mp-day-head">
          <div>
            <p class="mp-k dark">TODAY</p>
            <p class="today-label">{{ todayLabel }}</p>
          </div>
          <span class="mp-legend"><i class="ok"></i>Logged <i></i>Not yet</span>
        </div>
        <div class="meal-tabs" role="tablist" aria-label="Meals today">
          <button
            v-for="(meal, i) in todaysMeals" :key="meal.id" type="button" role="tab"
            class="meal-tab" :class="{ active: activeMealIndex === i }" :aria-selected="activeMealIndex === i"
            @click="activeMealIndex = i"
          >
            <span class="meal-tab-ico"><component :is="mealIcon(meal.meal_time)" :size="17" /></span>
            <span class="meal-tab-txt">
              <strong>{{ mealTimeLabel(meal.meal_time) }}</strong>
              <small v-if="meal.scheduled_time">{{ formatClock(meal.scheduled_time) }}</small>
            </span>
            <span v-if="logFor(meal.id)" class="tab-status-dot" :class="logFor(meal.id).status === 'followed' ? 'dot-green' : 'dot-gold'" :title="logFor(meal.id).status_label"></span>
          </button>
        </div>

        <div class="meal-card">
          <div class="meal-header">
            <span class="meal-ico"><component :is="mealIcon(activeMeal.meal_time)" :size="22" /></span>
            <div class="meal-head-txt">
              <h3 class="meal-name">{{ mealTimeLabel(activeMeal.meal_time) }}</h3>
              <p v-if="activeMeal.scheduled_time" class="meal-scheduled"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>Planned for {{ formatClock(activeMeal.scheduled_time) }}</p>
            </div>
            <!-- The client logs what they ate; the RND rates it. -->
            <div class="status-col">
              <span class="status-pill" :class="pillClass(activeLog)">
                <i aria-hidden="true"></i>{{ !activeLog ? 'Not logged yet' : activeLog.status ? activeLog.status_label : 'Waiting for your RND to rate it' }}
              </span>
              <span v-if="activeLog?.time_logged" class="logged-at">Logged at {{ formatClock(activeLog.time_logged) }}<template v-if="activeLog.status">, rated by your RND</template></span>
            </div>
          </div>

          <div class="meal-body">
            <div class="meal-col">
              <div class="col-head"><span class="col-eyebrow">Planned meal</span><span class="mp-k">FNRI EXCHANGES</span></div>
              <div class="exchange-summary">
                <span v-for="part in exchangeSummary(activeMeal).split(', ')" :key="part" class="ex-chip">{{ part }}</span>
              </div>
              <div v-if="activeMeal.food_items.length" class="food-item-list">
                <div v-for="(item, fi) in activeMeal.food_items" :key="item.id" class="planned-item" :class="[{ allergen: foodAllergies(item).length }, `t${fi % 5}`]">
                  <span class="planned-dot"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 8c-4-3-9 0-8 6 1 5 5 8 8 6 3 2 7-1 8-6 1-6-4-9-8-6z" /><path d="M12 8c0-3 1-5 3-6" /></svg></span>
                  <div class="planned-text">
                    <span class="food-name">{{ item.food_name }}</span>
                    <span class="food-note">{{ item.household_measure || item.notes || `${item.exchanges} exchange` }}</span>
                    <span v-for="w in foodAllergies(item)" :key="w" class="allergy-tag" :title="`${w}. Don't eat this, and message your RND.`"><AlertTriangle :size="12" aria-hidden="true" /> {{ w }}</span>
                  </div>
                  <span v-if="item.kcal" class="food-kcal">{{ Math.round(Number(item.kcal)) }} kcal</span>
                </div>
              </div>
              <p v-else class="no-items-note">No specific foods listed for this meal yet.</p>
              <p v-if="activeMeal.meal_notes" class="meal-note-text"><strong>Note:</strong> {{ activeMeal.meal_notes }}</p>
            </div>

            <div class="meal-col log-col">
              <div class="col-head"><span class="col-eyebrow">What you ate</span><span class="mp-k">YOUR LOG</span></div>

              <!-- rated by the RND: final, shown read-only -->
              <template v-if="isRated">
                <div v-if="activeLog.photo_url" class="photo-preview">
                  <button type="button" class="photo-thumb" aria-label="View the photo full size" @click="viewerOpen = true">
                    <img :src="activeLog.photo_url" alt="Photo you logged for this meal" />
                  </button>
                </div>
                <p v-if="activeLog.reason_notes" class="rated-note">{{ activeLog.reason_notes }}</p>
                <p class="rated-lock"><Lock :size="14" aria-hidden="true" /> Your RND rated this meal, so it can't be changed. Message your RND if something's wrong.</p>
              </template>
              <template v-else>
              <input ref="photoInput" type="file" accept="image/*" class="dropzone-input" @change="onPhotoSelected" />
              <!-- The chosen photo (not uploaded until Save) or the one already
                   saved today, shown as a picture; tap it to see it full size. -->
              <div v-if="photoPreview" class="photo-preview">
                <button type="button" class="photo-thumb" aria-label="View the photo full size" @click="viewerOpen = true">
                  <img :src="photoPreview" :alt="logForm.photoFile ? 'Selected photo of what you ate' : 'Photo you logged for this meal'" />
                </button>
                <div class="photo-meta">
                  <span class="photo-name">{{ logForm.photoFile ? logForm.photoName : 'Saved photo' }}</span>
                  <span v-if="logForm.photoFile" class="photo-sub">Not saved yet. Press Save to send it.</span>
                  <div class="photo-actions">
                    <button type="button" class="nm-btn-soft nm-btn-sm" @click="photoInput?.click()">Change photo</button>
                    <button type="button" class="nm-btn-danger solid nm-btn-sm" @click="removePhoto"><X :size="13" aria-hidden="true" /> Remove</button>
                  </div>
                </div>
              </div>
              <button v-else type="button" class="dropzone-inline" @click="photoInput?.click()">
                <span class="dropzone-icon"><UploadCloud :size="22" /></span>
                <span class="dropzone-text"><strong>Upload a photo of what you ate</strong><small>JPG, PNG or WEBP. On a phone, you can take one now.</small></span>
                <span class="dropzone-btn"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8a2 2 0 0 1 2-2h2l2-2h6l2 2h2a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><circle cx="12" cy="13" r="3.5" /></svg>Choose photo</span>
              </button>
              <p v-if="logForm.removeSaved" class="photo-sub">Your saved photo will be removed when you press Save.</p>
              <p v-if="photoError" class="form-error inline">{{ photoError }}</p>

              <Teleport to="body">
                <div v-if="viewerOpen && photoPreview" class="photo-viewer" role="dialog" aria-modal="true" aria-label="Photo of what you ate" @click.self="viewerOpen = false">
                  <button type="button" class="viewer-close" aria-label="Close" @click="viewerOpen = false"><X :size="20" /></button>
                  <img :src="photoPreview" alt="Photo of what you ate, full size" />
                </div>
              </Teleport>

              <div class="field notes-field">
                <label for="meal-log-note">Note</label>
                <textarea id="meal-log-note" data-allow-emoji v-model="logForm.reasonNotes" rows="3" maxlength="1000"
                          placeholder="What did you eat? e.g. Had half the rice and added a banana."></textarea>
              </div>
              <p class="log-hint"><Info :size="14" aria-hidden="true" /> Add a photo, a note or both. The time is saved for you, and your RND rates how closely it followed your plan.</p>

              <p v-if="logError" class="form-error inline">{{ logError }}</p>

              <button v-if="canSaveLog" class="save-log-btn" :disabled="isSavingLog" @click="saveMealLog">
                <Save :size="16" /> {{ isSavingLog ? 'Saving…' : 'Save my log' }}
              </button>
              </template>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="empty-note-card">
        <span class="empty-note-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>
        Your plan has no meals scheduled for today ({{ todayLabel }}).
      </div>

      <div class="info-note">
        <Info :size="16" aria-hidden="true" />
        <p>Portions follow the FNRI Food Exchange Lists. Your RND may change them at a follow-up consultation, and sees every meal you log.</p>
      </div>
    </template>

    <!-- NO PLAN YET -->
    <div v-else class="empty-state">
      <span class="empty-glow" aria-hidden="true"></span>
      <div class="empty-icon" aria-hidden="true"><span><svg class="ic" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3v8M5 3v4a2 2 0 0 0 4 0V3M7 11v10M17 21V3c-2 0-4 2-4 6s2 5 4 5" /></svg></span></div>
      <p class="mp-k dark center">MY MEAL PLAN</p>
      <p class="empty-title">No meal plan <em>yet.</em></p>
      <p class="empty-desc">Your RND makes your meal plan after your consultation. It shows here, meal by meal.</p>
      <div class="empty-chips"><span class="c-veg">½ Vegetables</span><span class="c-grain">¼ Whole grains</span><span class="c-prot">¼ Protein</span></div>
      <div class="empty-steps">
        <div><span>1</span><strong>Book a consultation</strong><p>Meet your RND by video call or in person.</p></div>
        <div><span>2</span><strong>Your RND plans it</strong><p>A plan for your calories, health and the food you like.</p></div>
        <div><span>3</span><strong>Log your meals</strong><p>Snap a photo of each meal. Your RND checks how it went.</p></div>
      </div>
      <div class="empty-actions">
        <NuxtLink to="/appointments" class="mp-btn-gold"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>My appointments</NuxtLink>
        <NuxtLink to="/resource-library" class="nm-btn-soft">Browse resources<svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import { phIso, phWeekday } from '~/utils/phTime'
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { Info, ClipboardList, Sunrise, Coffee, Sun, Moon, UploadCloud, Save, CheckCircle2, X, AlertTriangle, Lock, Download } from 'lucide-vue-next'
import { printDocument } from '~/utils/printDoc'
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

/* ---------- download / print the whole week (browser print to PDF) ---------- */
const WEEK = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
const printBlocked = ref(false)
function downloadPlan() {
  const p = plan.value
  if (!p) return
  const g = v => (v ? `${Math.round(Number(v))} g` : '—')
  const rows = [
    ['Plan', planName.value],
    ['For', conditionLabel.value || '—'],
    // allergies near the top: never quiet (patient safety)
    ['Allergies', p.allergies_restrictions || (myAllergies.value.length ? myAllergies.value.join(', ') : 'None recorded')],
    ['Calories a day', p.target_kcal ? `${Math.round(p.target_kcal).toLocaleString()} kcal` : '—'],
    ['Carbs, protein, fat', `${g(p.target_carb_g)}, ${g(p.target_protein_g)}, ${g(p.target_fat_g)}`],
  ]
  if (otherTargets.value.length) rows.push(['Other targets', otherTargets.value.map(t => `${t.label}: ${t.value}${t.unit ? ` ${t.unit}` : ''}`).join(', ')])
  const table = [['Day', 'Meal', 'Food', 'Portion', 'kcal']]
  const meals = p.meals || []
  const everyDay = meals.every(m => m.day_of_week === null) // older plans: the same meals every day
  const dayList = everyDay ? [null] : WEEK.map((_, i) => i)
  for (const d of dayList) {
    let first = true
    for (const meal of orderedMeals(meals.filter(m => m.day_of_week === d || m.day_of_week === null))) {
      const mealName = `${mealTimeLabel(meal.meal_time)}${meal.scheduled_time ? `, ${formatClock(meal.scheduled_time)}` : ''}`
      const foods = meal.food_items?.length ? meal.food_items : [{ food_name: 'No foods set' }]
      foods.forEach((item, i) => {
        table.push([
          first ? (d === null ? 'Every day' : WEEK[d]) : '',
          i === 0 ? mealName : '',
          item.food_name || '',
          item.household_measure || (item.exchanges ? `${Number(item.exchanges)} exchange` : ''),
          item.kcal ? String(Math.round(Number(item.kcal))) : '',
        ])
        first = false
      })
      if (meal.meal_notes) table.push(['', '', `Note: ${meal.meal_notes}`, '', ''])
    }
  }
  const sections = []
  if (p.notes) sections.push({ heading: 'Instructions from your RND', text: p.notes })
  printBlocked.value = !printDocument({
    title: 'Meal plan',
    number: planName.value,
    rows,
    table,
    sections,
    note: 'Follow the portions your RND set. Message your RND in NutriMatch before changing foods or amounts.',
    foot: 'Generated by NutriMatch for your own use. Your health information is protected under the Data Privacy Act of 2012 (RA 10173).',
  })
}

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
// rated by the RND (Followed / Partly / Not followed): final for the client
const isRated = computed(() => Boolean(activeLog.value?.status))

const logForm = reactive({ reasonNotes: '', photoFile: null, photoName: '', removeSaved: false })
// Save shows once there's something new: a photo, a removed photo, or a changed note.
const canSaveLog = computed(() => !!logForm.photoFile || logForm.removeSaved
  || (logForm.reasonNotes.trim() && logForm.reasonNotes.trim() !== (activeLog.value?.reason_notes || '').trim()))

function resetLogForm() {
  const existing = activeLog.value
  logForm.reasonNotes = existing?.reason_notes || ''
  removePhoto()
  logForm.removeSaved = false
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
const photoPreview = computed(() => selectedUrl.value || (logForm.removeSaved ? '' : activeLog.value?.photo_url) || '')

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
  logForm.removeSaved = false
}
// Remove: drops a photo chosen but not saved; with none chosen, marks the
// saved photo to be removed on Save (remove_photo=true).
function removePhoto() {
  if (!logForm.photoFile && activeLog.value?.photo_url) logForm.removeSaved = true
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
const completionPct = computed(() => {
  const meals = todaysMeals.value
  if (!meals.length) return 0
  const followed = meals.filter(m => logFor(m.id)?.status === 'followed').length
  return Math.round((followed / meals.length) * 100)
})

/* ---------- SAVE + NOTIFY RND ---------- */
const isSavingLog = ref(false)
const logError = ref('')
const toast = useToast() // the app's toast (2026-11-03)
function fireToast(msg, opts) {
  toast.success(msg, opts)
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
    else if (logForm.removeSaved) form.append('remove_photo', 'true')

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

async function loadMealPlans({ quiet = false } = {}) {
  if (!quiet) {
    isLoading.value = true
    errorMessage.value = ''
  }
  try {
    const [mealPlans, logs, profile] = await Promise.all([
      get('/client/meal-plans/'),
      get(`/client/meal-logs/?date=${todayIso}`),
      get('/client/profile/').catch(() => null),
    ])
    plans.value = mealPlans
    todaysLogs.value = logs
    myAllergies.value = profile?.health_profile?.allergies || []
    if (quiet) return // a background refresh keeps the meal the client is on
    // start on the first meal not logged yet (else the first one)
    const firstOpen = todaysMeals.value.findIndex(m => !logFor(m.id))
    activeMealIndex.value = firstOpen >= 0 ? firstOpen : 0
    resetLogForm()
  } catch {
    if (!quiet) errorMessage.value = 'Could not load your meal plan. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadMealPlans)
// new plan, plan updates and the RND's ratings show without a reload; waits
// while a log is being written (a chosen photo or an edited note)
useAutoRefresh(() => loadMealPlans({ quiet: true }), {
  paused: () => isSavingLog.value || !!logForm.photoFile || logForm.removeSaved ||
    logForm.reasonNotes !== (activeLog.value?.reason_notes || ''),
})

/* ---------- UI only (no data or API changes) ---------- */
const plateImg = '/landing/login-plate.webp'
// meals logged today, for the banner and the calorie ring
const loggedCount = computed(() => todaysMeals.value.filter(m => logFor(m.id)).length)
const ringPct = computed(() => (todaysMeals.value.length ? Math.round((loggedCount.value / todaysMeals.value.length) * 100) : 100))
// each macro's share of the day's calories (4 kcal per g carbs and protein, 9 per g fat)
const macroRows = computed(() => {
  const p = plan.value || {}
  const kcal = Number(p.target_kcal) || 0
  const share = (g, per) => (kcal && g ? Math.min(100, Math.round((Number(g) * per / kcal) * 100)) : 0)
  return [
    { key: 'carb', label: 'Carbs', grams: p.target_carb_g, pct: share(p.target_carb_g, 4) },
    { key: 'protein', label: 'Protein', grams: p.target_protein_g, pct: share(p.target_protein_g, 4) },
    { key: 'fat', label: 'Fat', grams: p.target_fat_g, pct: share(p.target_fat_g, 9) },
  ]
})
</script>

<style scoped>
/* =========================================================
   My Meal Plan: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings, numbers), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.meal-plan-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; gap: 20px; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }

.form-error { margin: 0; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 14px; }
.form-error.inline { margin: 12px 0 0; }
.placeholder-text { display: flex; align-items: center; gap: 10px; font-size: 14px; color: #6B7D73; }
.mp-spin { width: 20px; height: 20px; border-radius: 50%; border: 2.5px solid #DCE5DF; border-top-color: #004D3A; animation: mp-spin .8s linear infinite; }
@keyframes mp-spin { to { transform: rotate(360deg); } }
.mp-k { margin: 0; display: flex; align-items: center; gap: 6px; font-size: 11.5px; font-weight: 800; letter-spacing: 1.4px; color: #7A8F84; }
.mp-k.dark { color: #C49102; }
.mp-k.gold { color: #9A7300; }
.mp-k.center { justify-content: center; }
.mp-card {
  background: #FFFFFF;
  border: 1px solid #E1E7E3;
  border-radius: 20px;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.02),
    0 2px 6px rgba(0, 0, 0, 0.06),
    0 12px 28px -6px rgba(0, 0, 0, 0.12),
    0 24px 48px -18px rgba(0, 77, 58, 0.22);
}

/* ---------- BANNER ---------- */
.mp-hero {
  position: relative;
  overflow: hidden;
  padding: 30px 32px;
  border-radius: 24px;
  color: #FFFFFF;
  background:
    radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%),
    linear-gradient(115deg, #035A45 0%, #004D3A 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -14px rgba(0, 77, 58, 0.55);
}
.mp-hero-plate { position: absolute; right: -80px; top: 50%; width: 440px; height: 440px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.6; pointer-events: none; }
.mp-hero-fade { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(0, 70, 52, 0) 48%, rgba(0, 68, 51, 0.8) 66%, rgba(0, 64, 47, 0.2) 100%); pointer-events: none; }
.mp-hero-text { position: relative; z-index: 1; max-width: 620px; }
.mp-eyebrow { margin: 0; display: flex; align-items: center; gap: 12px; font-size: 12.5px; font-weight: 800; letter-spacing: 2px; color: #EFBF04; }
.mp-eyebrow span { width: 28px; height: 2px; border-radius: 2px; background: #EFBF04; }
.plan-name { margin: 10px 0 10px; font-family: 'Playfair Display', Georgia, serif; font-size: 32px; line-height: 1.15; font-weight: 700; color: #FFFFFF; }
.plan-sub { margin: 0; display: inline-flex; align-items: center; gap: 8px; font-size: 15px; color: rgba(255, 255, 255, 0.85); }
.plan-sub .ic { color: #6EE7A8; }
.mp-hero-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 18px; }
.mp-btn-gold {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  padding: 0 18px;
  border: none;
  border-radius: 12px;
  background: #EFBF04;
  color: #004D3A;
  font-family: inherit;
  font-size: 14px;
  font-weight: 800;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9);
  transition: background-color .15s, transform .15s;
}
.mp-btn-gold:hover { background: #F5CB1F; transform: translateY(-1px); }
.mp-glass { display: inline-flex; align-items: center; gap: 8px; height: 44px; padding: 0 16px; border-radius: 12px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.18); -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px); font-size: 13.5px; font-weight: 700; }
.mp-glass .ic { color: #6EE7A8; }

/* ---------- TARGETS ---------- */
.mp-targets { display: grid; grid-template-columns: 240px minmax(0, 1fr) minmax(0, 1.1fr); gap: 18px; align-items: stretch; }
.mp-targets.no-notes { grid-template-columns: 240px minmax(0, 1fr); }
.mp-cal { padding: 20px; display: flex; flex-direction: column; align-items: center; text-align: center; background: linear-gradient(160deg, #035A45, #004D3A); border: none; color: #FFFFFF; }
.mp-cal .mp-k { align-self: flex-start; color: #EFBF04; }
.mp-ring { --p: 0%; margin: 14px 0 10px; width: 132px; height: 132px; border-radius: 50%; background: conic-gradient(#EFBF04 0 var(--p), rgba(255, 255, 255, 0.14) var(--p) 100%); display: flex; align-items: center; justify-content: center; }
.mp-ring span { width: 108px; height: 108px; border-radius: 50%; background: #004D3A; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.mp-ring strong { font-family: 'Playfair Display', Georgia, serif; font-size: 30px; line-height: 1; }
.mp-ring small { font-size: 12px; color: rgba(255, 255, 255, 0.75); }
.mp-cal-note { margin: 0; font-size: 12.5px; line-height: 1.5; color: rgba(255, 255, 255, 0.78); }
.mp-macros { padding: 20px 22px; display: flex; flex-direction: column; gap: 14px; }
.mp-macro-top { display: flex; align-items: baseline; justify-content: space-between; }
.mp-macro-top span { font-size: 14px; font-weight: 700; color: #22362C; }
.mp-macro-top strong { font-family: 'Playfair Display', Georgia, serif; font-size: 22px; }
.mp-macro-top small { font-family: 'DM Sans', Arial, sans-serif; font-size: 13px; font-weight: 700; }
.mp-bar { height: 8px; margin-top: 6px; border-radius: 99px; overflow: hidden; }
.mp-bar span { display: block; height: 100%; border-radius: 99px; transition: width .4s; }
.mp-macro p { margin: 4px 0 0; font-size: 12px; color: #6B7D73; }
.mp-macro.carb strong { color: #9A7300; } .mp-macro.carb .mp-bar { background: #FBF3D2; } .mp-macro.carb .mp-bar span { background: #C49102; }
.mp-macro.protein strong { color: #004D3A; } .mp-macro.protein .mp-bar { background: #E3EFE7; } .mp-macro.protein .mp-bar span { background: #004D3A; }
.mp-macro.fat strong { color: #8A4B2A; } .mp-macro.fat .mp-bar { background: #F6E7DC; } .mp-macro.fat .mp-bar span { background: #B4683F; }
.plan-notes { min-width: 0; max-height: 300px; overflow-y: auto; padding: 20px 22px; background: linear-gradient(160deg, #FFFBEE, #FBF6E4); border-color: #F1E2A6; }
.mp-allergy { margin: 12px 0 0; display: flex; gap: 8px; padding: 10px 12px; border-radius: 12px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 13.5px; line-height: 1.5; }
.mp-allergy .ic { margin-top: 2px; }
.notes-text { margin: 12px 0 0; font-size: 14px; line-height: 1.65; color: #3E3410; overflow-wrap: anywhere; white-space: pre-line; }
.other-targets { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: -6px; }
.other-targets-label { font-size: 11.5px; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase; color: #7A8F84; }
.other-target-chip { height: 30px; padding: 0 12px; display: inline-flex; align-items: center; gap: 4px; border-radius: 999px; background: #FFFFFF; border: 1px solid #E1E7E3; font-size: 13px; color: #3E5046; }
.other-target-chip strong { color: #004D3A; }

/* ---------- TODAY + MEAL TABS ---------- */
.mp-day-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; margin: 4px 2px -6px; }
.today-label { margin: 2px 0 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #10231B; }
.mp-legend { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: #6B7D73; }
.mp-legend i { width: 8px; height: 8px; margin-left: 8px; border-radius: 50%; background: #D3DCD6; }
.mp-legend i.ok { margin-left: 0; background: #1F9D55; }
.meal-tabs { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
.meal-tab {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border: 1.5px solid #E1E7E3;
  border-radius: 16px;
  background: #FFFFFF;
  color: #10231B;
  font-family: inherit;
  text-align: left;
  cursor: pointer;
  transition: background-color .15s, border-color .15s, box-shadow .15s;
}
.meal-tab:hover:not(.active) { border-color: #B8C9BE; }
.meal-tab:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.meal-tab.active { background: #004D3A; border-color: #004D3A; color: #FFFFFF; box-shadow: 0 12px 22px -14px rgba(0, 77, 58, 0.9); }
.meal-tab-ico { flex-shrink: 0; width: 38px; height: 38px; border-radius: 12px; background: #F1F6F2; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.meal-tab.active .meal-tab-ico { background: rgba(255, 255, 255, 0.14); color: #EFBF04; }
.meal-tab-txt { display: flex; flex-direction: column; min-width: 0; }
.meal-tab-txt strong { font-size: 14px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.meal-tab-txt small { font-size: 12px; opacity: .75; }
.tab-status-dot { position: absolute; top: 10px; right: 10px; width: 8px; height: 8px; border-radius: 50%; }
.dot-green { background-color: #1F9D55; }
.dot-gold { background-color: #EFBF04; }

/* ---------- MEAL CARD ---------- */
.meal-card { overflow: hidden; background: #FFFFFF; border: 1px solid #E1E7E3; border-radius: 20px; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); }
.meal-header { display: flex; align-items: center; gap: 14px; padding: 18px 24px; background: #F7FAF8; border-bottom: 1px solid #EEF2EF; }
.meal-ico { flex-shrink: 0; width: 48px; height: 48px; border-radius: 14px; background: #004D3A; color: #EFBF04; display: inline-flex; align-items: center; justify-content: center; }
.meal-head-txt { flex: 1; min-width: 0; }
.meal-name { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #10231B; }
.meal-scheduled { margin: 2px 0 0; display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: #5D7065; }
.status-col { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; text-align: right; }
.status-pill { display: inline-flex; align-items: center; gap: 7px; height: 30px; padding: 0 12px; border-radius: 999px; font-size: 12.5px; font-weight: 800; white-space: nowrap; }
.status-pill i { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
.pill-green { background: #EAF4EE; color: #1F7A4C; }
.pill-muted { background: #FBF6E4; color: #7A5A00; }
.pill-gold { background: #FBF6E4; color: #7A5A00; }
.pill-red { background: #FEF3F2; color: #B42318; }
.logged-at { font-size: 12px; color: #6B7D73; }

.meal-body { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
.meal-col { min-width: 0; padding: 22px 24px; }
.log-col { display: flex; flex-direction: column; border-left: 1px solid #EEF2EF; }
.col-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 12px; }
.col-eyebrow { font-size: 16px; font-weight: 800; color: #10231B; }
.exchange-summary { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.ex-chip { height: 26px; padding: 0 10px; display: inline-flex; align-items: center; border-radius: 999px; background: #F1F4F2; color: #3E5046; font-size: 12px; font-weight: 700; }

.food-item-list { display: flex; flex-direction: column; gap: 8px; }
.planned-item { display: flex; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 14px; border: 1px solid #E8EDEA; background: #FFFFFF; transition: border-color .15s; }
.planned-item:hover { border-color: #B8C9BE; }
.planned-dot { flex-shrink: 0; width: 38px; height: 38px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; background: #EEF4F0; color: #004D3A; }
.planned-item.t1 .planned-dot { background: #FBF6E4; color: #9A7300; }
.planned-item.t2 .planned-dot { background: #F8ECE4; color: #8A4B2A; }
.planned-item.t3 .planned-dot { background: #FDEDEF; color: #B4384A; }
.planned-item.t4 .planned-dot { background: #EEF1FA; color: #3B5BA5; }
/* a food that may contain one of the client's allergens: red, never quiet */
.planned-item.allergen { background: #FEF3F2; border: 1.5px solid #D92D20; }
.planned-item.allergen .planned-dot { background: #D92D20; color: #FFFFFF; }
.planned-text { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: flex-start; }
.food-name { font-size: 14px; font-weight: 700; color: #10231B; }
.food-note { font-size: 12.5px; color: #6B7D73; }
.food-kcal { flex-shrink: 0; height: 24px; padding: 0 9px; display: inline-flex; align-items: center; border-radius: 999px; background: #F1F4F2; font-size: 11.5px; font-weight: 800; color: #3E5046; }
.allergy-tag { display: inline-flex; align-items: center; gap: 4px; margin-top: 4px; padding: 2px 8px; border-radius: 999px; background: #D92D20; color: #FFFFFF; font-size: 11.5px; font-weight: 800; }
.no-items-note { margin: 0; padding: 14px; border-radius: 12px; background: #F7FAF8; font-size: 13.5px; color: #6B7D73; }
.meal-note-text { margin: 14px 0 0; padding: 10px 12px; border-left: 3px solid #EFBF04; border-radius: 0 10px 10px 0; background: #FBF8EC; font-size: 13.5px; line-height: 1.5; color: #3E5046; }
.meal-note-text strong { color: #7A5A00; }

/* log side */
.dropzone-input { display: none; }
.dropzone-inline {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 22px 16px;
  border: 1.5px dashed #9FC7AF;
  border-radius: 16px;
  background: #F7FBF8;
  font-family: inherit;
  text-align: center;
  cursor: pointer;
  transition: border-color .15s, background-color .15s;
}
.dropzone-inline:hover { border-color: #004D3A; background: #F1F6F2; }
.dropzone-inline:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.dropzone-icon { width: 48px; height: 48px; border-radius: 14px; background: #FFFFFF; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 8px 16px -10px rgba(0, 77, 58, 0.6); }
.dropzone-text { display: flex; flex-direction: column; gap: 2px; }
.dropzone-text strong { font-size: 14.5px; color: #10231B; }
.dropzone-text small { font-size: 12.5px; color: #6B7D73; }
.dropzone-btn { margin-top: 6px; height: 36px; padding: 0 14px; display: inline-flex; align-items: center; gap: 6px; border-radius: 10px; background: #F1F6F2; color: #004D3A; font-size: 13px; font-weight: 700; }

.photo-preview { display: flex; flex-direction: column; gap: 10px; margin-bottom: 4px; }
.photo-thumb { display: block; width: 100%; aspect-ratio: 16 / 9; padding: 0; border: 1px solid #E1E7E3; border-radius: 16px; overflow: hidden; cursor: zoom-in; background: #EEF2EF; }
.photo-thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.photo-meta { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.photo-name { font-size: 14px; font-weight: 700; color: #10231B; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.photo-sub { margin: 0; font-size: 12.5px; color: #7A5A00; }
.photo-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.meal-plan-page .nm-btn-soft,
.meal-plan-page .nm-btn-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 40px;
  padding: 0 16px;
  border: none;
  border-radius: 12px;
  font-family: inherit;
  font-size: 13.5px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color .15s;
}
.meal-plan-page .nm-btn-sm { height: 36px; padding: 0 14px; font-size: 13px; }
.meal-plan-page .nm-btn-soft { background: #F1F6F2; color: #004D3A; }
.meal-plan-page .nm-btn-soft:hover { background: #E3EFE7; }
.meal-plan-page .nm-btn-danger.solid { background: #FEF3F2; color: #B42318; }
.meal-plan-page .nm-btn-danger.solid:hover { background: #B42318; color: #FFFFFF; }

.photo-viewer { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 24px; background: rgba(4, 20, 14, 0.85); }
.photo-viewer img { max-width: min(92vw, 1000px); max-height: 86vh; border-radius: 16px; object-fit: contain; background: #FFFFFF; }
.viewer-close { position: absolute; top: 16px; right: 16px; width: 44px; height: 44px; border: none; border-radius: 50%; background: rgba(255, 255, 255, 0.14); color: #FFFFFF; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.viewer-close:hover { background: rgba(255, 255, 255, 0.24); }

.field label { display: block; margin-bottom: 6px; font-size: 13px; font-weight: 700; color: #22362C; }
.notes-field { margin-top: 16px; }
.notes-field textarea { width: 100%; padding: 12px 14px; border: 1.5px solid #DCE5DF; border-radius: 14px; background: #F7FAF8; font-family: inherit; font-size: 14px; color: #14261E; resize: vertical; }
.notes-field textarea:focus { outline: none; border-color: #004D3A; background: #FFFFFF; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.log-hint { margin: 10px 0 0; display: flex; gap: 8px; font-size: 12.5px; line-height: 1.5; color: #5D7065; }
.log-hint svg { flex-shrink: 0; margin-top: 2px; color: #7A8F84; }
.rated-note { margin: 10px 0; padding: 12px 14px; border-radius: 14px; background: #F7FAF8; border: 1px solid #E3EAE5; font-size: 14px; line-height: 1.55; color: #10231B; white-space: pre-line; overflow-wrap: anywhere; }
.rated-lock { margin: 0; display: flex; gap: 8px; align-items: flex-start; padding: 12px 14px; border-radius: 14px; background: #EAF4EE; font-size: 13px; line-height: 1.5; color: #1F3A2C; }
.rated-lock svg { flex-shrink: 0; margin-top: 2px; color: #004D3A; }
.save-log-btn {
  align-self: flex-end;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 48px;
  margin-top: 16px;
  padding: 0 22px;
  border: none;
  border-radius: 12px;
  background: #004D3A;
  color: #FFFFFF;
  font-family: inherit;
  font-size: 14.5px;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 12px 22px -12px rgba(0, 77, 58, 0.85);
  transition: background-color .15s;
}
.save-log-btn:hover:not(:disabled) { background: #0A5C46; }
.save-log-btn:disabled { opacity: .6; cursor: not-allowed; }

.empty-note-card { display: flex; align-items: center; gap: 12px; padding: 18px 20px; border-radius: 18px; background: #FFFFFF; border: 1px solid #E1E7E3; font-size: 14px; color: #3E5046; }
.empty-note-icon { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.info-note { display: flex; gap: 10px; align-items: center; padding: 14px 18px; border-radius: 14px; background: #EEF4F0; color: #004D3A; }
.info-note svg { flex-shrink: 0; }
.info-note p { margin: 0; font-size: 13.5px; line-height: 1.55; color: #3E5046; }

/* ---------- NO PLAN YET ---------- */
.empty-state {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 44px 32px 36px;
  border-radius: 20px;
  background: #FFFFFF;
  border: 1px solid #E1E7E3;
  text-align: center;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22);
}
.empty-glow { position: absolute; left: 50%; top: -120px; width: 520px; height: 320px; transform: translateX(-50%); border-radius: 50%; background: radial-gradient(circle, rgba(239, 191, 4, 0.16), rgba(239, 191, 4, 0) 70%); pointer-events: none; }
.empty-icon { position: relative; width: 150px; height: 150px; margin-bottom: 22px; border-radius: 50%; background: conic-gradient(#DDEBE2 0 50%, #F6E7B4 50% 75%, #F0D9C8 75% 100%); box-shadow: inset 0 0 0 12px #FFFFFF, 0 0 0 1px #E6ECE8, 0 20px 40px -22px rgba(0, 77, 58, 0.6); }
.empty-icon span { position: absolute; inset: 40px; border-radius: 50%; background: #FFFFFF; display: flex; align-items: center; justify-content: center; color: #004D3A; }
.empty-title { position: relative; margin: 8px 0 8px; font-family: 'Playfair Display', Georgia, serif; font-size: 32px; font-weight: 700; color: #10231B; }
.empty-title em { font-style: italic; color: #C49102; }
.empty-desc { position: relative; margin: 0; max-width: 520px; font-size: 15px; line-height: 1.65; color: #5D7065; }
.empty-chips { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; margin-top: 16px; }
.empty-chips span { height: 28px; padding: 0 12px; display: inline-flex; align-items: center; border-radius: 999px; font-size: 12.5px; font-weight: 700; }
.c-veg { background: #EAF4EE; color: #004D3A; }
.c-grain { background: #FBF6E4; color: #7A5A00; }
.c-prot { background: #F8ECE4; color: #8A4B2A; }
.empty-steps { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; width: 100%; max-width: 820px; margin-top: 28px; padding-top: 24px; border-top: 1px dashed #DCE5DF; text-align: left; }
.empty-steps div { display: grid; grid-template-columns: 30px 1fr; column-gap: 12px; }
.empty-steps span { grid-row: 1 / span 2; width: 30px; height: 30px; border-radius: 50%; background: #EFBF04; color: #004D3A; font-size: 13px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }
.empty-steps strong { font-size: 14.5px; color: #10231B; }
.empty-steps p { margin: 2px 0 0; font-size: 13px; line-height: 1.5; color: #5D7065; }
.empty-actions { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; margin-top: 26px; }
.empty-actions .nm-btn-soft { height: 44px; }

/* ---------- smaller screens ---------- */
@media (max-width: 1200px) {
  .mp-targets { grid-template-columns: 220px minmax(0, 1fr); }
  .plan-notes { grid-column: 1 / -1; }
}

/* phone + tablet: the approved mobile design */
@media (max-width: 960px) {
  .meal-plan-page { gap: 16px; }

  .mp-hero { min-height: 236px; padding: 20px 18px 18px; border-radius: 22px; }
  .mp-hero-plate { width: 176px; height: 176px; right: -44px; top: 22px; transform: none; opacity: 1; box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.08); }
  .mp-hero-fade { display: none; }
  .mp-hero-text { max-width: none; }
  .mp-eyebrow,
  .plan-name,
  .plan-sub { max-width: 64%; }
  .mp-eyebrow { font-size: 11px; gap: 8px; }
  .mp-eyebrow span { width: 18px; }
  .plan-name { margin: 8px 0 8px; font-size: 22px; line-height: 1.2; }
  .plan-sub { font-size: 12.5px; align-items: flex-start; }
  .mp-hero-actions { flex-wrap: nowrap; margin-top: 16px; }
  .mp-btn-gold { height: 42px; padding: 0 14px; font-size: 13.5px; border-radius: 999px; }
  .mp-glass { height: 42px; padding: 0 12px; border-radius: 999px; font-size: 12px; white-space: nowrap; }

  .mp-targets,
  .mp-targets.no-notes { grid-template-columns: 1fr; gap: 10px; }
  .mp-cal { flex-direction: row; align-items: center; gap: 16px; padding: 14px 16px; text-align: left; }
  .mp-cal .mp-k { display: none; }
  .mp-ring { flex-shrink: 0; width: 88px; height: 88px; margin: 0; }
  .mp-ring span { width: 72px; height: 72px; }
  .mp-ring strong { font-size: 20px; }
  .mp-ring small { font-size: 11px; }
  .mp-cal-note { font-size: 13px; }
  .mp-cal-note::before { content: 'Calories a day'; display: block; margin-bottom: 2px; font-family: 'Playfair Display', Georgia, serif; font-size: 18px; font-weight: 700; color: #FFFFFF; }
  .mp-macros { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; padding: 12px; }
  .mp-macros > .mp-k { grid-column: 1 / -1; margin-bottom: 2px; }
  .mp-macro { padding: 10px; border-radius: 14px; background: #F7FAF8; }
  .mp-macro-top { flex-direction: column; align-items: flex-start; gap: 2px; }
  .mp-macro-top span { font-size: 12px; color: #5D7065; }
  .mp-macro-top strong { font-size: 20px; }
  .mp-macro p { margin-top: 6px; font-size: 11px; }
  .plan-notes { max-height: none; padding: 14px 16px; }
  .notes-text { font-size: 13.5px; }

  .mp-day-head { margin: 6px 2px -4px; }
  .today-label { font-size: 20px; }
  .mp-legend { display: none; }
  .meal-tabs { display: flex; gap: 8px; overflow-x: auto; scrollbar-width: none; margin: 0 -16px; padding: 2px 16px 6px; }
  .meal-tabs::-webkit-scrollbar { display: none; }
  .meal-tab { flex: 0 0 auto; gap: 8px; padding: 8px 14px 8px 8px; border-radius: 999px; }
  .meal-tab-ico { width: 32px; height: 32px; border-radius: 50%; }
  .meal-tab-txt strong { font-size: 13px; }
  .meal-tab-txt small { font-size: 11px; }
  .tab-status-dot { top: 4px; right: 6px; }

  .meal-card { border-radius: 20px; }
  .meal-header { flex-wrap: wrap; gap: 12px; padding: 14px 16px; }
  .meal-ico { width: 44px; height: 44px; }
  .meal-name { font-size: 20px; }
  .status-col { order: 3; width: 100%; align-items: stretch; text-align: center; }
  .status-pill { justify-content: center; }
  .meal-body { grid-template-columns: 1fr; }
  .meal-col { padding: 16px; }
  .col-head .mp-k { display: none; }
  .exchange-summary { flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; margin: 0 -16px 12px; padding: 0 16px; }
  .exchange-summary::-webkit-scrollbar { display: none; }
  .ex-chip { flex-shrink: 0; }
  .planned-item { padding: 10px; gap: 10px; }
  .planned-dot { width: 36px; height: 36px; }
  .food-name { font-size: 13.5px; }
  .log-col { border-left: none; border-top: 8px solid #F5F7F5; }
  .dropzone-inline { flex-direction: row; align-items: center; gap: 12px; padding: 14px; text-align: left; }
  .dropzone-icon { flex-shrink: 0; width: 44px; height: 44px; }
  .dropzone-text { flex: 1; }
  .dropzone-text strong { font-size: 13.5px; }
  .dropzone-text small { display: none; }
  .dropzone-btn { margin: 0; }
  .notes-field textarea { font-size: 16px; } /* stops iPhone zoom on tap */
  .log-hint { font-size: 12px; }
  .save-log-btn { position: sticky; bottom: 96px; z-index: 5; width: 100%; align-self: stretch; height: 52px; border-radius: 999px; box-shadow: 0 14px 28px -12px rgba(0, 77, 58, 0.7); }
  .info-note { align-items: flex-start; padding: 12px 14px; }
  .info-note p { font-size: 12.5px; }

  .empty-state { padding: 28px 18px 22px; }
  .empty-icon { width: 120px; height: 120px; }
  .empty-icon span { inset: 32px; }
  .empty-title { font-size: 26px; }
  .empty-desc { font-size: 14px; }
  .empty-steps { grid-template-columns: 1fr; gap: 12px; margin-top: 20px; padding: 14px; border: 1px dashed #DCE5DF; border-radius: 16px; background: #F7FAF8; }
  .empty-actions { width: 100%; flex-direction: column; }
  .empty-actions > * { width: 100%; }
}
@media (max-width: 380px) {
  .mp-glass { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  .mp-spin { animation: none; }
}
</style>