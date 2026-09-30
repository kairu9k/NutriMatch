<template>
  <div class="meal-planning-page">
    <!-- TOP CONTROLS -->
    <div class="top-controls no-print">
      <div class="mode-toggle">
        <button class="mode-btn" :class="{ active: mode === 'view' }" :disabled="!patients.length" @click="mode = 'view'">
          <Eye :size="15" /> View Plans
        </button>
        <button class="mode-btn" :class="{ active: mode === 'create' }" :disabled="!patients.length" @click="openCreate">
          <Plus :size="15" /> {{ selectedPlan ? 'Edit Plan' : 'Create Plan' }}
        </button>
      </div>

      <div v-if="patients.length" class="patient-select">
        <select v-model="selectedRelId">
          <option v-for="p in patients" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <ChevronDown :size="15" class="select-caret" />
      </div>
    </div>

    <p v-if="errorMessage" class="form-error no-print">{{ errorMessage }}</p>
    <p v-if="notice" class="form-notice no-print"><CheckCircle2 :size="15" /> {{ notice }}</p>

    <p v-if="isLoading" class="macro-note">Loading…</p>

    <div v-else-if="!patients.length" class="empty-state">
      <p class="empty-title">No active patients yet</p>
      <p class="macro-note">Meal plans can be created once a client's first appointment is confirmed.</p>
    </div>

    <!-- ================= VIEW PLANS MODE ================= -->
    <div v-else-if="mode === 'view' && !selectedPlan" class="empty-state">
      <p class="empty-title">No meal plan yet for {{ selectedPatientName }}</p>
      <button class="btn-primary" @click="startNewPlan"><Plus :size="15" /> Create Meal Plan</button>
    </div>

    <div v-else-if="mode === 'view'" class="planning-layout">
      <div class="panel plan-panel print-area">
        <div class="plan-header">
          <div>
            <h3>Weekly Meal Plan — {{ selectedPatientName }}</h3>
            <p class="plan-subtitle">{{ planMeta.name }} · <span class="status-text">{{ statusLabel(selectedPlan.status) }}</span></p>
          </div>
          <div class="plan-badges">
            <span v-if="planMeta.kcalPerDay" class="badge badge-blue">{{ planMeta.kcalPerDay }} kcal/day</span>
            <span class="badge badge-gold">{{ conditionLabel(planMeta.condition) }}</span>
          </div>
        </div>

        <div class="day-tabs no-print">
          <button
            v-for="day in days"
            :key="day"
            class="day-tab"
            :class="{ active: activeDay === day }"
            @click="activeDay = day"
          >
            {{ day }}
          </button>
        </div>

        <!-- Screen: selected day. Print: the whole week. -->
        <div v-for="day in printDays" :key="day" class="print-day" :class="{ 'screen-hidden': day !== activeDay }">
          <h4 class="print-only print-day-title">{{ DAY_FULL[day] }}</h4>
          <div class="meal-list">
            <div class="meal-row" v-for="meal in mealsForDay(day)" :key="meal.type">
              <div class="meal-info">
                <div class="meal-label">
                  <component :is="meal.icon" :size="14" />
                  {{ meal.type }}<template v-if="meal.time"> · {{ formatTime(meal.time) }}</template>
                </div>
                <div class="meal-title">{{ meal.title }}</div>
                <div class="meal-breakdown">{{ meal.breakdown }}</div>
              </div>
              <div class="meal-kcal">{{ meal.kcal }} kcal</div>
            </div>
          </div>
        </div>

        <div v-if="instructions.allergies || instructions.notes" class="instructions-view">
          <p v-if="instructions.allergies"><strong>Allergies / Restrictions:</strong> {{ instructions.allergies }}</p>
          <p v-if="instructions.notes"><strong>RND Notes:</strong> {{ instructions.notes }}</p>
        </div>

        <div class="plan-actions no-print">
          <button class="btn-secondary" @click="printPlan"><Printer :size="15" /> Print Plan</button>
          <button class="btn-secondary" @click="mode = 'create'"><Pencil :size="15" /> Edit Plan</button>
          <button class="btn-primary" :disabled="isSending" @click="sendToPatient">
            <Send :size="15" /> {{ isSending ? 'Sending…' : selectedPlan.status === 'active' ? 'Resend to Patient' : 'Send to Patient' }}
          </button>
        </div>
      </div>

      <!-- RIGHT SIDEBAR -->
      <div class="side-column no-print">
        <div class="panel">
          <h4 class="side-title">Nutritional Summary</h4>
          <span class="side-subtitle">{{ DAY_FULL[activeDay] }}</span>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Total Calories</span><span>{{ nutrition.calories.value }} / {{ nutrition.calories.target ?? '—' }} kcal</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-green" :style="{ width: pct(nutrition.calories) + '%' }"></div></div>
          </div>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Carbohydrates</span><span>{{ nutrition.carbs.value }}g / {{ nutrition.carbs.target ?? '—' }}g</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-gold" :style="{ width: pct(nutrition.carbs) + '%' }"></div></div>
          </div>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Protein</span><span>{{ nutrition.protein.value }}g / {{ nutrition.protein.target ?? '—' }}g</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-green" :style="{ width: pct(nutrition.protein) + '%' }"></div></div>
          </div>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Fat</span><span>{{ nutrition.fat.value }}g / {{ nutrition.fat.target ?? '—' }}g</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-dark" :style="{ width: pct(nutrition.fat) + '%' }"></div></div>
          </div>
        </div>

        <div class="panel">
          <div class="side-header-row">
            <h4 class="side-title">Saved Plans</h4>
            <button class="link-btn" @click="startNewPlan"><Plus :size="13" /> New Plan</button>
          </div>
          <button
            v-for="p in plans"
            :key="p.id"
            class="saved-plan-card"
            :class="{ selected: p.id === selectedPlanId }"
            @click="selectPlan(p.id)"
          >
            <div>
              <div class="saved-plan-name">{{ p.name }}</div>
              <div class="saved-plan-meta">{{ conditionLabel(p.condition) }}<template v-if="p.target_kcal"> · {{ Math.round(p.target_kcal) }} kcal/day</template></div>
            </div>
            <span class="active-pill" :class="'pill-' + p.status">{{ p.status.toUpperCase() }}</span>
          </button>
        </div>

        <div class="panel">
          <h4 class="side-title">FNRI Exchange Lists</h4>
          <div class="exchange-tags">
            <span class="exchange-tag tag-rice">Rice/Bread</span>
            <span class="exchange-tag tag-veg">Vegetables</span>
            <span class="exchange-tag tag-fruit">Fruits</span>
            <span class="exchange-tag tag-meat">Meat/Fish</span>
            <span class="exchange-tag tag-milk">Milk</span>
            <span class="exchange-tag tag-fat">Fat</span>
          </div>
          <p class="exchange-note">Based on FNRI Food Exchange Lists 4th Ed., 2020</p>
        </div>
      </div>
    </div>

    <!-- ================= CREATE / EDIT PLAN MODE ================= -->
    <div v-else class="planning-layout">
      <div class="create-column">
        <!-- STEP 1: PLAN DETAILS -->
        <div class="panel">
          <h4 v-if="!selectedPlan" class="no-plan-title">No meal plan yet for {{ selectedPatientName }}</h4>
          <h4 v-else class="side-title">Plan Details</h4>
          <p v-if="!selectedPlan && ncpTargets" class="macro-note prefill-note">Targets pre-filled from this client's NCP Intervention — adjust if needed.</p>

          <div class="form-row-6">
            <div class="field">
              <label>Plan Name</label>
              <input v-model="planMeta.name" type="text" placeholder="e.g., Diabetic-Friendly Plan" />
            </div>
            <div class="field">
              <label>Condition</label>
              <select v-model="planMeta.condition">
                <option v-for="c in CONDITIONS" :key="c.value" :value="c.value">{{ c.label }}</option>
              </select>
            </div>
            <div class="field">
              <label>Target Calories/day</label>
              <input v-model.number="planMeta.kcalPerDay" type="number" min="0" placeholder="e.g., 1800" />
            </div>
            <div class="field">
              <label>Protein (g/day) <span class="optional">(optional)</span></label>
              <input v-model.number="targets.protein" type="number" min="0" placeholder="e.g., 90" />
            </div>
            <div class="field">
              <label>Carbohydrate (g/day) <span class="optional">(optional)</span></label>
              <input v-model.number="targets.carb" type="number" min="0" placeholder="e.g., 200" />
            </div>
            <div class="field">
              <label>Fat (g/day) <span class="optional">(optional)</span></label>
              <input v-model.number="targets.fat" type="number" min="0" placeholder="e.g., 55" />
            </div>
          </div>

          <button v-if="!selectedPlan" class="btn-primary" :disabled="!planMeta.name || !planMeta.kcalPerDay || isSaving" @click="createPlan">
            {{ isSaving ? 'Creating…' : 'Create Meal Plan' }}
          </button>
        </div>

        <!-- STEP 2: DAILY MEALS — only once the plan exists -->
        <template v-if="selectedPlan">
          <div class="day-tabs">
            <button
              v-for="day in days"
              :key="day"
              class="day-tab"
              :class="{ active: activeDay === day }"
              @click="activeDay = day"
            >
              {{ day }}
            </button>
          </div>

          <div class="panel meal-edit-panel" v-for="meal in currentDayMeals" :key="meal.type">
            <div class="meal-edit-header">
              <span class="meal-edit-label"><component :is="meal.icon" :size="14" /> {{ meal.type.toUpperCase() }}</span>
              <input v-model="weeklyPlan[activeDay][meal.type].time" type="time" class="meal-time-input" title="Meal time" />
            </div>

            <div class="food-table">
              <div class="food-table-head">
                <span></span>
                <span>FOOD ITEM</span>
                <span>PORTION</span>
                <span>KCAL</span>
                <span>CARB(G)</span>
                <span>PROT(G)</span>
                <span>FAT(G)</span>
              </div>
              <div class="food-table-row" v-for="(item, idx) in meal.items" :key="idx">
                <button class="remove-btn" title="Remove" @click="removeItem(meal, idx)"><X :size="12" /></button>
                <input
                  v-model="item.name"
                  type="text"
                  list="fnri-suggestions"
                  placeholder="Search FNRI or type a food"
                  @input="onFoodNameInput(item, $event.target.value)"
                  @change="applyFnriMatch(item, $event.target.value)"
                />
                <input v-model="item.portion" type="text" placeholder="e.g., ½ cup" />
                <input v-model.number="item.kcal" type="number" min="0" placeholder="0" />
                <input v-model.number="item.carb" type="number" min="0" placeholder="0" />
                <input v-model.number="item.prot" type="number" min="0" placeholder="0" />
                <input v-model.number="item.fat" type="number" min="0" placeholder="0" />
              </div>
            </div>

            <button class="btn-add-food" @click="addItem(meal)"><Plus :size="14" /> Add Food Item</button>
          </div>

          <datalist id="fnri-suggestions">
            <option v-for="f in fnriSuggestions" :key="f.id" :value="f.name">{{ f.category.name }} · {{ f.household_measure || '1 exchange' }}</option>
          </datalist>

          <div class="plan-actions create-actions">
            <button class="btn-secondary" @click="discardChanges">Cancel</button>
            <button class="btn-secondary" :disabled="isSaving" @click="savePlan()">{{ isSaving ? 'Saving…' : 'Save Plan' }}</button>
            <button class="btn-primary" :disabled="isSaving || isSending" @click="saveAndSend"><Send :size="15" /> Save &amp; Send to Patient</button>
          </div>
        </template>
      </div>

      <!-- RIGHT SIDEBAR (CREATE MODE) -->
      <div class="side-column">
        <div class="panel">
          <div class="side-header-row">
            <h4 class="side-title">Live Preview</h4>
            <span v-if="selectedPlan" class="preview-day">{{ DAY_FULL[activeDay] }}</span>
          </div>

          <p v-if="!planMeta.name && !planMeta.kcalPerDay" class="macro-note">
            Fill in the plan details to see a live preview here.
          </p>

          <template v-else>
            <div class="preview-summary">
              <p class="preview-summary-name">{{ planMeta.name || 'Untitled Plan' }}</p>
              <div class="plan-badges">
                <span v-if="planMeta.condition" class="badge badge-gold">{{ conditionLabel(planMeta.condition) }}</span>
                <span v-if="planMeta.kcalPerDay" class="badge badge-blue">{{ planMeta.kcalPerDay }} kcal/day</span>
              </div>
            </div>

            <div v-if="targets.protein || targets.carb || targets.fat" class="target-list">
              <div v-if="targets.protein" class="target-row"><span>Protein</span><span>{{ targets.protein }}g/day</span></div>
              <div v-if="targets.carb" class="target-row"><span>Carbohydrate</span><span>{{ targets.carb }}g/day</span></div>
              <div v-if="targets.fat" class="target-row"><span>Fat</span><span>{{ targets.fat }}g/day</span></div>
            </div>
          </template>

          <div v-if="selectedPlan && currentDayMeals.some(m => m.items.some(i => i.name))" class="preview-list">
            <div class="preview-item" v-for="meal in currentDayMeals.filter(m => m.items.some(i => i.name))" :key="meal.type" :class="'preview-' + meal.accent">
              <div class="preview-label"><component :is="meal.icon" :size="13" /> {{ meal.type }}</div>
              <div class="preview-food">{{ firstFoodSummary(meal) }}</div>
              <div class="preview-kcal">{{ mealTotal(meal, 'kcal') }} kcal</div>
            </div>
          </div>
          <p v-else-if="selectedPlan" class="macro-note">No meals added yet. Add food items per day to see the nutrition breakdown.</p>
        </div>

        <div v-if="selectedPlan" class="panel">
          <h4 class="side-title">Macro Tracker</h4>
          <div class="macro-row"><span>Calories</span><span class="macro-value">{{ dayTotal('kcal') }} kcal</span></div>
          <div class="macro-bar"><div class="macro-fill fill-dark" :style="{ width: macroPct('kcal') + '%' }"></div></div>

          <div class="macro-row"><span>Carbs (g)</span><span class="macro-value">{{ dayTotal('carb') }}g</span></div>
          <div class="macro-bar"><div class="macro-fill fill-gold" :style="{ width: macroPct('carb') + '%' }"></div></div>

          <div class="macro-row"><span>Protein (g)</span><span class="macro-value">{{ dayTotal('prot') }}g</span></div>
          <div class="macro-bar"><div class="macro-fill fill-green" :style="{ width: macroPct('prot') + '%' }"></div></div>

          <div class="macro-row"><span>Fat (g)</span><span class="macro-value">{{ dayTotal('fat') }}g</span></div>
          <div class="macro-bar"><div class="macro-fill fill-dark2" :style="{ width: macroPct('fat') + '%' }"></div></div>

          <p class="macro-note">Based on foods entered for the selected day</p>
        </div>

        <div v-if="selectedPlan" class="panel">
          <h4 class="side-title">Special Instructions</h4>
          <div class="field">
            <label>Allergies / Restrictions</label>
            <textarea v-model="instructions.allergies" rows="2" placeholder="e.g., No shellfish, low potassium"></textarea>
          </div>
          <div class="field">
            <label>RND Notes for Patient</label>
            <textarea v-model="instructions.notes" rows="3" placeholder="e.g., Please eat meals at regular times. Avoid skipping meals."></textarea>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {
  Eye, Plus, ChevronDown, Printer, Pencil, Send, X, CheckCircle2,
  Sun, Coffee, Utensils, Apple, Moon
} from 'lucide-vue-next'

const route = useRoute()
const { get, post, patch, put } = useApi()

// Matches nutrition.MealPlan.Condition.
const CONDITIONS = [
  { value: 'diabetes', label: 'Diabetes' },
  { value: 'hypertension', label: 'Hypertension' },
  { value: 'renal', label: 'Renal Disease' },
  { value: 'weight_loss', label: 'Weight Loss' },
  { value: 'weight_gain', label: 'Weight Gain' },
  { value: 'general', label: 'General' },
]
function conditionLabel(value) {
  return CONDITIONS.find(c => c.value === value)?.label || value
}
function statusLabel(status) {
  return { draft: 'Draft — not yet sent', active: 'Active — visible to patient', archived: 'Archived' }[status] || status
}

// Design order Mon→Sun; day_of_week uses Sunday=0 (same as availability).
const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const DAY_INDEX = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 }
const DAY_FULL = { Mon: 'Monday', Tue: 'Tuesday', Wed: 'Wednesday', Thu: 'Thursday', Fri: 'Friday', Sat: 'Saturday', Sun: 'Sunday' }
const activeDay = ref(days[(new Date().getDay() + 6) % 7])

// Design meal slots → nutrition.MealPlanMeal.MealTime.
const mealOrder = ['Breakfast', 'Morning Snack', 'Lunch', 'Afternoon Snack', 'Dinner']
const MEAL_TIME = { Breakfast: 'breakfast', 'Morning Snack': 'am_snack', Lunch: 'lunch', 'Afternoon Snack': 'pm_snack', Dinner: 'dinner' }
const MEAL_TYPE = Object.fromEntries(Object.entries(MEAL_TIME).map(([k, v]) => [v, k]))
const mealIcons = { Breakfast: Sun, 'Morning Snack': Coffee, Lunch: Utensils, 'Afternoon Snack': Apple, Dinner: Moon }
const mealAccents = { Breakfast: 'green', 'Morning Snack': 'gold', Lunch: 'blue', 'Afternoon Snack': 'gold', Dinner: 'blue' }

const mode = ref('view')
const isLoading = ref(true)
const isSaving = ref(false)
const isSending = ref(false)
const errorMessage = ref('')
const notice = ref('')
let noticeTimer = null
function flash(message) {
  notice.value = message
  clearTimeout(noticeTimer)
  noticeTimer = setTimeout(() => { notice.value = '' }, 4000)
}
function apiError(error, fallback) {
  const data = error?.data || {}
  return data.detail || Object.values(data).flat().find(v => typeof v === 'string') || fallback
}

/* ---------- Patients (the RND's active clients) ---------- */
const patients = ref([])
const selectedRelId = ref(null)
const selectedPatientName = computed(() => patients.value.find(p => p.id === selectedRelId.value)?.name || '')

/* ---------- Plans for the selected patient ---------- */
const plans = ref([])
const selectedPlanId = ref(null)
const selectedPlan = computed(() => plans.value.find(p => p.id === selectedPlanId.value) || null)
const ncpTargets = ref(null)

const planMeta = reactive({ name: '', condition: 'general', kcalPerDay: null })
const targets = reactive({ carb: null, protein: null, fat: null })
const instructions = reactive({ allergies: '', notes: '' })
const weeklyPlan = reactive(emptyWeek())

function emptyWeek() {
  const week = {}
  for (const day of days) {
    week[day] = {}
    for (const type of mealOrder) week[day][type] = { time: '', items: [] }
  }
  return week
}
function num(v) {
  return v === null || v === undefined || v === '' ? null : Number(v)
}

function fillFromPlan(plan) {
  planMeta.name = plan.name
  planMeta.condition = plan.condition
  planMeta.kcalPerDay = num(plan.target_kcal) === null ? null : Math.round(num(plan.target_kcal))
  targets.protein = num(plan.target_protein_g)
  targets.carb = num(plan.target_carb_g)
  targets.fat = num(plan.target_fat_g)
  instructions.allergies = plan.allergies_restrictions || ''
  instructions.notes = plan.notes || ''
  Object.assign(weeklyPlan, emptyWeek())
  for (const meal of plan.meals) {
    const type = MEAL_TYPE[meal.meal_time]
    const day = days.find(d => DAY_INDEX[d] === meal.day_of_week)
    if (!type || !day) continue
    weeklyPlan[day][type] = {
      time: meal.scheduled_time ? meal.scheduled_time.slice(0, 5) : '',
      items: meal.food_items.map(i => ({
        foodItemId: i.food_item,
        name: i.food_name,
        portion: i.household_measure || '',
        exchanges: num(i.exchanges),
        kcal: num(i.kcal),
        carb: num(i.carbs_g),
        prot: num(i.protein_g),
        fat: num(i.fat_g),
      })),
    }
  }
}

function resetForm() {
  Object.assign(planMeta, { name: '', condition: 'general', kcalPerDay: null })
  Object.assign(targets, { carb: null, protein: null, fat: null })
  Object.assign(instructions, { allergies: '', notes: '' })
  Object.assign(weeklyPlan, emptyWeek())
  // Pre-fill targets from the NCP Intervention phase when available.
  if (ncpTargets.value) {
    planMeta.kcalPerDay = ncpTargets.value.kcal
    targets.protein = ncpTargets.value.protein
    targets.carb = ncpTargets.value.carb
    targets.fat = ncpTargets.value.fat
  }
}

function selectPlan(id) {
  selectedPlanId.value = id
  const plan = selectedPlan.value
  if (plan) fillFromPlan(plan)
  mode.value = 'view'
}

function startNewPlan() {
  selectedPlanId.value = null
  resetForm()
  mode.value = 'create'
}

function openCreate() {
  if (selectedPlan.value) fillFromPlan(selectedPlan.value)
  else resetForm()
  mode.value = 'create'
}

function discardChanges() {
  if (selectedPlan.value) fillFromPlan(selectedPlan.value)
  mode.value = 'view'
}

async function loadPatients() {
  const rels = await get('/rnd/relationships/active/')
  patients.value = rels.map(r => ({ id: r.id, name: `${r.client.first_name} ${r.client.last_name}` }))
  const requested = Number(route.query.relationship)
  selectedRelId.value = patients.value.find(p => p.id === requested)?.id ?? patients.value[0]?.id ?? null
}

async function loadPatientPlans() {
  if (!selectedRelId.value) return
  errorMessage.value = ''
  const [planList, ncpList] = await Promise.all([
    get(`/rnd/relationships/${selectedRelId.value}/meal-plans/`),
    get(`/rnd/relationships/${selectedRelId.value}/ncp/`).catch(() => []),
  ])
  plans.value = planList
  const ncp = ncpList[0]
  ncpTargets.value = ncp && ncp.target_kcal
    ? { kcal: Math.round(num(ncp.target_kcal)), protein: num(ncp.target_protein_g), carb: num(ncp.target_carb_g), fat: num(ncp.target_fat_g) }
    : null

  const preferred = planList.find(p => p.status === 'active') || planList.find(p => p.status === 'draft') || planList[0]
  if (preferred) {
    selectPlan(preferred.id)
    if (route.query.edit) mode.value = 'create'
  } else {
    selectedPlanId.value = null
    resetForm()
    mode.value = route.query.edit ? 'create' : 'view'
  }
}

watch(selectedRelId, async (id, previous) => {
  if (!id || previous === undefined) return
  try {
    await loadPatientPlans()
  } catch {
    errorMessage.value = 'Could not load this patient\'s meal plans.'
  }
})

onMounted(async () => {
  try {
    await loadPatients()
    await loadPatientPlans()
  } catch {
    errorMessage.value = 'Could not load meal plans. Please try again later.'
  } finally {
    isLoading.value = false
  }
})

/* ---------- Create / save / send ---------- */
function planDetailsPayload() {
  return {
    name: planMeta.name.trim(),
    condition: planMeta.condition,
    target_kcal: planMeta.kcalPerDay ?? null,
    target_protein_g: targets.protein ?? null,
    target_carb_g: targets.carb ?? null,
    target_fat_g: targets.fat ?? null,
    allergies_restrictions: instructions.allergies || null,
    notes: instructions.notes || null,
  }
}

function weekPayload() {
  const meals = []
  for (const day of days) {
    for (const type of mealOrder) {
      const slot = weeklyPlan[day][type]
      meals.push({
        day_of_week: DAY_INDEX[day],
        meal_time: MEAL_TIME[type],
        scheduled_time: slot.time || null,
        items: slot.items
          .filter(i => i.name && i.name.trim())
          .map(i => ({
            food_item: i.foodItemId || null,
            food_name: i.name.trim(),
            household_measure: i.portion || null,
            exchanges: i.exchanges || 1,
            kcal: i.kcal ?? null,
            carbs_g: i.carb ?? null,
            protein_g: i.prot ?? null,
            fat_g: i.fat ?? null,
          })),
      })
    }
  }
  return { meals }
}

function replacePlan(updated) {
  const idx = plans.value.findIndex(p => p.id === updated.id)
  if (idx >= 0) plans.value.splice(idx, 1, updated)
  else plans.value.unshift(updated)
}

async function createPlan() {
  isSaving.value = true
  errorMessage.value = ''
  try {
    const created = await post(`/rnd/relationships/${selectedRelId.value}/meal-plans/`, {
      relationship: selectedRelId.value,
      ...planDetailsPayload(),
    })
    replacePlan(created)
    selectedPlanId.value = created.id
    flash('Plan created as a draft — add meals for each day, then send it to your patient.')
  } catch (error) {
    errorMessage.value = apiError(error, 'Could not create the plan.')
  } finally {
    isSaving.value = false
  }
}

async function savePlan({ quiet = false } = {}) {
  if (!selectedPlan.value) return false
  if (!planMeta.name.trim()) {
    errorMessage.value = 'Plan name is required.'
    return false
  }
  isSaving.value = true
  errorMessage.value = ''
  try {
    await patch(`/rnd/meal-plans/${selectedPlanId.value}/`, planDetailsPayload())
    const saved = await put(`/rnd/meal-plans/${selectedPlanId.value}/week/`, weekPayload())
    replacePlan(saved)
    fillFromPlan(saved)
    if (!quiet) flash('Plan saved.')
    return true
  } catch (error) {
    errorMessage.value = apiError(error, 'Could not save the plan.')
    return false
  } finally {
    isSaving.value = false
  }
}

async function sendToPatient() {
  isSending.value = true
  errorMessage.value = ''
  const wasActive = selectedPlan.value?.status === 'active'
  try {
    const sent = await post(`/rnd/meal-plans/${selectedPlanId.value}/send/`)
    // Sending archives any other active plan for this patient.
    plans.value = plans.value.map(p => (p.status === 'active' && p.id !== sent.id ? { ...p, status: 'archived' } : p))
    replacePlan(sent)
    flash(wasActive ? `Updated plan sent to ${selectedPatientName.value}.` : `Plan sent to ${selectedPatientName.value}.`)
    mode.value = 'view'
  } catch (error) {
    errorMessage.value = apiError(error, 'Could not send the plan.')
  } finally {
    isSending.value = false
  }
}

async function saveAndSend() {
  if (await savePlan({ quiet: true })) await sendToPatient()
}

function printPlan() {
  window.print()
}

/* ---------- FNRI food suggestions ---------- */
const fnriSuggestions = ref([])
let searchTimer = null
// The value comes from the event: this handler can run before v-model has
// copied the new text into item.name.
function onFoodNameInput(item, value) {
  // Typing clears any previous FNRI link until a suggestion is picked again.
  item.foodItemId = null
  const term = (value || '').trim()
  clearTimeout(searchTimer)
  if (term.length < 2) return
  searchTimer = setTimeout(async () => {
    try {
      fnriSuggestions.value = (await get(`/food-exchange/items/?search=${encodeURIComponent(term)}`)).slice(0, 12)
    } catch {
      fnriSuggestions.value = []
    }
  }, 250)
}
// Picking an FNRI item fills 1 exchange's household measure and macros from
// its FNRI category — the RND can still adjust the numbers.
async function applyFnriMatch(item, value) {
  const term = (value || '').trim()
  let match = fnriSuggestions.value.find(f => f.name.toLowerCase() === term.toLowerCase())
  // A name typed in full and tabbed out of can beat the debounced search —
  // look it up directly instead of silently leaving the row unfilled.
  if (!match && term.length >= 2) {
    clearTimeout(searchTimer)
    try {
      const results = await get(`/food-exchange/items/?search=${encodeURIComponent(term)}`)
      match = results.find(f => f.name.toLowerCase() === term.toLowerCase())
    } catch {
      return
    }
  }
  if (!match) return
  const cat = match.category
  item.name = match.name
  item.foodItemId = match.id
  item.exchanges = 1
  item.portion = match.household_measure || item.portion
  item.kcal = num(cat.kcal_per_exchange)
  item.carb = num(cat.carbs_g)
  item.prot = num(cat.protein_g)
  item.fat = num(cat.fat_g)
}

/* ---------- Meals, totals ---------- */
function mealsForDay(day) {
  return mealOrder.map(type => {
    const meal = weeklyPlan[day][type]
    const named = meal.items.filter(i => i.name)
    return {
      type,
      time: meal.time,
      items: meal.items,
      icon: mealIcons[type],
      accent: mealAccents[type],
      kcal: round(named.reduce((sum, i) => sum + (Number(i.kcal) || 0), 0)),
      title: named.map(i => `${i.name}${i.portion ? ` (${i.portion})` : ''}`).join(' + ') || 'No items added',
      breakdown: named.map(i => `${i.name}: ${i.kcal || 0}kcal | ${i.carb || 0}g carb | ${i.prot || 0}g prot | ${i.fat || 0}g fat`).join(' | ') || '—',
    }
  })
}
const currentDayMeals = computed(() => mealsForDay(activeDay.value))
// Print shows the whole week; the screen shows only the selected day.
const printDays = days

function round(n) {
  return Math.round(n * 10) / 10
}
function mealTotal(meal, field) {
  return round(meal.items.reduce((sum, i) => sum + (Number(i[field]) || 0), 0))
}
function dayTotal(field) {
  return round(currentDayMeals.value.reduce((sum, meal) => sum + mealTotal(meal, field), 0))
}
function macroPct(field) {
  const fieldTargets = { kcal: planMeta.kcalPerDay, carb: targets.carb, prot: targets.protein, fat: targets.fat }
  const target = fieldTargets[field]
  if (!target) return 0
  return Math.min(100, Math.round((dayTotal(field) / target) * 100))
}

const nutrition = computed(() => ({
  calories: { value: dayTotal('kcal'), target: planMeta.kcalPerDay },
  carbs: { value: dayTotal('carb'), target: targets.carb },
  protein: { value: dayTotal('prot'), target: targets.protein },
  fat: { value: dayTotal('fat'), target: targets.fat },
}))
function pct(n) {
  if (!n.target) return 0
  return Math.min(100, Math.round((n.value / n.target) * 100))
}

function addItem(meal) {
  weeklyPlan[activeDay.value][meal.type].items.push({ foodItemId: null, name: '', portion: '', exchanges: 1, kcal: null, carb: null, prot: null, fat: null })
}
function removeItem(meal, idx) {
  weeklyPlan[activeDay.value][meal.type].items.splice(idx, 1)
}
function firstFoodSummary(meal) {
  const named = meal.items.filter(i => i.name)
  return named.length ? `${named[0].name}${named.length > 1 ? ` (+${named.length - 1} more)` : ''}` : ''
}

function formatTime(t) {
  const [h, m] = t.split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}
</script>

<style scoped>
.top-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 28px; }

.mode-toggle { display: flex; gap: 10px; }
.mode-btn {
  display: flex; align-items: center; gap: 6px;
  border: 1px solid #dde3dd; background: #fff; color: #4a5a4a;
  padding: 9px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.mode-btn.active { background: #163a1c; color: #fff; border-color: #163a1c; }

.patient-select { position: relative; }
.patient-select select {
  appearance: none; border: 1px solid #dde3dd; background: #fff;
  padding: 9px 32px 9px 14px; border-radius: 8px; font-size: 0.85rem; color: #1a3a1a; cursor: pointer;
}
.select-caret { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #9aaa9a; pointer-events: none; }

.planning-layout { display: grid; grid-template-columns: 2.3fr 1fr; gap: 24px; align-items: start; }

.panel { background: #fff; border-radius: 12px; padding: 24px; border: 1px solid #eceeec; margin-bottom: 20px; }

/* VIEW MODE */
.plan-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.plan-header h3 { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0; }
.plan-badges { display: flex; gap: 8px; }
.badge { font-size: 0.72rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; }
.badge-blue { background: #e3edfc; color: #3b6fd6; }
.badge-gold { background: #fdf1d6; color: #b8860b; }

.day-tabs { display: flex; gap: 8px; margin-bottom: 24px; }
.day-tab {
  border: 1px solid #e0e5e0; background: #fff; color: #4a5a4a;
  padding: 8px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.day-tab.active { background: #163a1c; color: #fff; border-color: #163a1c; }

.meal-list { display: flex; flex-direction: column; }
.meal-row {
  display: flex; justify-content: space-between; align-items: flex-start;
  padding: 16px 0; border-bottom: 1px solid #f0f2f0;
}
.meal-row:first-child { padding-top: 0; }
.meal-row:last-child { border-bottom: none; }
.meal-info { flex: 1; }
.meal-label {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; color: #9aaa9a; text-transform: uppercase; margin-bottom: 6px;
}
.meal-title { font-size: 0.92rem; font-weight: 600; color: #1a3a1a; margin-bottom: 4px; }
.meal-breakdown { font-size: 0.75rem; color: #9aaa9a; }
.meal-kcal { font-size: 0.85rem; font-weight: 600; color: #3a4a3a; white-space: nowrap; margin-left: 16px; }

.plan-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; padding-top: 18px; border-top: 1px solid #f0f2f0; }
.btn-secondary {
  display: flex; align-items: center; gap: 6px;
  border: 1px solid #dde3dd; background: #fff; color: #3a4a3a;
  padding: 9px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.btn-primary {
  display: flex; align-items: center; gap: 6px;
  background: #163a1c; color: #fff; border: none;
  padding: 9px 16px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }

/* SIDE COLUMN (shared) */
.side-title { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0 0 6px; }
.side-subtitle { font-size: 0.75rem; color: #9aaa9a; }
.side-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.link-btn { display: flex; align-items: center; gap: 4px; background: none; border: none; color: #1a6a2a; font-size: 0.78rem; font-weight: 600; cursor: pointer; }

.nutrient-row { margin-top: 16px; }
.nutrient-top { display: flex; justify-content: space-between; font-size: 0.78rem; color: #4a5a4a; margin-bottom: 6px; }
.nutrient-bar { height: 6px; background: #eceeec; border-radius: 3px; overflow: hidden; }
.nutrient-fill { height: 100%; border-radius: 3px; }
.fill-green { background: #2e9e52; }
.fill-gold { background: #D4A017; }
.fill-dark { background: #163a1c; }
.fill-dark2 { background: #3a4a3a; }

.saved-plan-card {
  display: flex; justify-content: space-between; align-items: center;
  background: #eef5ee; border-radius: 10px; padding: 14px; margin-top: 6px;
}
.saved-plan-name { font-size: 0.85rem; font-weight: 700; color: #1a3a1a; }
.saved-plan-meta { font-size: 0.72rem; color: #7a8a7a; margin-top: 2px; }
.active-pill { background: #163a1c; color: #fff; font-size: 0.65rem; font-weight: 700; padding: 3px 9px; border-radius: 10px; }

.exchange-tags { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.exchange-tag { font-size: 0.72rem; font-weight: 600; padding: 4px 12px; border-radius: 20px; }
.tag-rice { background: #fdf1d6; color: #b8860b; }
.tag-veg { background: #e6f4e6; color: #2e7d32; }
.tag-fruit { background: #fdeadf; color: #d9683f; }
.tag-meat { background: #fbe1de; color: #c0483a; }
.tag-milk { background: #e3edfc; color: #3b6fd6; }
.tag-fat { background: #eef0ee; color: #6a7a6a; }
.exchange-note { font-size: 0.72rem; color: #9aaa9a; margin-top: 12px; }

/* CREATE MODE — STEP 1 (simplified plan details form) */
.no-plan-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }
.form-row-6 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px 24px; margin-bottom: 14px; }
.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.field label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; color: #4a5a4a; text-transform: uppercase; }
.optional { font-weight: 400; text-transform: none; color: #9aaa9a; }
.field input, .field select, .field textarea {
  border: 1px solid #dde3dd; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #1a3a1a;
}
.field textarea { resize: vertical; }

/* LIVE PREVIEW (create mode) */
.preview-summary { margin-bottom: 12px; }
.preview-summary-name { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0 0 8px; }
.target-list { margin-top: 12px; padding-top: 12px; border-top: 1px solid #f0f2f0; display: flex; flex-direction: column; gap: 6px; }
.target-row { display: flex; justify-content: space-between; font-size: 0.8rem; color: #4a5a4a; }

.meal-edit-panel { padding: 0; overflow: hidden; margin-bottom: 18px; }
.meal-edit-header {
  display: flex; justify-content: space-between; align-items: center;
  background: #eef5ee; padding: 16px 24px;
}
.meal-edit-label { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; font-weight: 700; color: #1a3a1a; letter-spacing: 0.03em; }
.meal-edit-time { font-size: 0.75rem; color: #7a8a7a; }

.food-table { padding: 20px 24px 4px; }
.food-table-head, .food-table-row {
  display: grid; grid-template-columns: 24px 2fr 1fr 0.8fr 0.9fr 0.9fr 0.8fr; gap: 12px; align-items: center;
}
.food-table-head { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.04em; color: #9aaa9a; padding-bottom: 10px; }
.food-table-head span:first-child { visibility: hidden; }
.food-table-row { margin-bottom: 12px; }
.food-table-row input {
  border: 1px solid #e0e5e0; border-radius: 6px; padding: 9px 10px; font-size: 0.82rem; font-family: inherit; width: 100%;
}
.remove-btn {
  width: 20px; height: 20px; border-radius: 5px; border: none;
  background: #fbe1de; color: #c0483a; display: flex; align-items: center; justify-content: center; cursor: pointer;
}

.btn-add-food {
  display: flex; align-items: center; gap: 6px; justify-content: center;
  width: calc(100% - 48px); margin: 6px 24px 22px;
  border: 1px dashed #cdd8cd; background: none; color: #1a6a2a;
  padding: 11px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.btn-add-food:hover { background: #f4f8f4; }

.preview-list { display: flex; flex-direction: column; gap: 10px; margin-top: 14px; }
.preview-item { border-left: 3px solid #ccc; background: #fafbfa; border-radius: 8px; padding: 12px 14px; }
.preview-green { border-left-color: #2e9e52; }
.preview-gold { border-left-color: #D4A017; }
.preview-blue { border-left-color: #3b6fd6; }
.preview-label { display: flex; align-items: center; gap: 5px; font-size: 0.72rem; font-weight: 700; color: #4a5a4a; margin-bottom: 3px; }
.preview-food { font-size: 0.8rem; color: #1a3a1a; margin-bottom: 3px; }
.preview-kcal { font-size: 0.72rem; color: #9aaa9a; }
.preview-day { font-size: 0.72rem; color: #9aaa9a; }

.macro-row { display: flex; justify-content: space-between; font-size: 0.82rem; color: #3a4a3a; margin-top: 18px; margin-bottom: 8px; }
.macro-value { font-weight: 600; }
.macro-bar { height: 6px; background: #eceeec; border-radius: 3px; overflow: hidden; }
.macro-fill { height: 100%; border-radius: 3px; }
.macro-note { font-size: 0.72rem; color: #9aaa9a; margin-top: 16px; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center; display: flex; flex-direction: column; align-items: center; gap: 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0; }

.mode-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.form-notice {
  display: flex; align-items: center; gap: 8px;
  background: #e3f3ea; border: 1px solid #b8dcc6; color: #1f8f5c;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; font-weight: 600; margin: 0 0 16px;
}
.plan-subtitle { font-size: 0.8rem; color: #7a8a7a; margin: 4px 0 0; }
.status-text { font-weight: 600; }
.prefill-note { margin: -8px 0 14px; }

button.saved-plan-card { width: 100%; border: 1.5px solid transparent; cursor: pointer; text-align: left; font-family: inherit; }
button.saved-plan-card:hover { border-color: #cfe0cf; }
button.saved-plan-card.selected { border-color: #163a1c; }
.active-pill.pill-draft { background: #fdf1d6; color: #b8860b; }
.active-pill.pill-archived { background: #eceeec; color: #7a8a7a; }

.instructions-view { margin-top: 16px; padding: 14px 16px; background: #fafbfa; border-radius: 8px; }
.instructions-view p { font-size: 0.8rem; color: #4a5a4a; margin: 0 0 6px; line-height: 1.5; }
.instructions-view p:last-child { margin: 0; }

.meal-time-input { border: 1px solid #d5dfd5; border-radius: 6px; padding: 5px 8px; font-size: 0.78rem; font-family: inherit; color: #1a3a1a; background: #fff; }
.create-actions { margin: 0 0 20px; padding: 0; border-top: none; }

.print-only { display: none; }
.screen-hidden { display: none; }

@media print {
  :global(body *) { visibility: hidden; }
  .print-area, .print-area * { visibility: visible; }
  .print-area { position: absolute; left: 0; top: 0; width: 100%; border: none; }
  .no-print { display: none !important; }
  .print-only { display: block; }
  .screen-hidden { display: block; }
  .print-day { break-inside: avoid; margin-bottom: 14px; }
  .print-day-title { font-size: 0.95rem; color: #1a3a1a; margin: 12px 0 6px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }
}

@media (max-width: 1150px) {
  .planning-layout { grid-template-columns: 1fr; }
  .form-row-6 { grid-template-columns: 1fr 1fr; }
  .food-table-head, .food-table-row { grid-template-columns: 20px 2fr 1fr 1fr 1fr; }
  .food-table-head span:nth-child(6), .food-table-row input:nth-child(6),
  .food-table-head span:nth-child(7), .food-table-row input:nth-child(7) { display: none; }
}
</style>
