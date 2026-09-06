<template>
  <div class="planning-page">
    <div class="top-controls">
      <div>
        <h1 class="page-title">Meal Plans</h1>
        <p class="page-sub">Create and manage FNRI exchange-based meal plans for your patients.</p>
      </div>
      <div class="patient-select">
        <select v-model="selectedRelationshipId">
          <option value="" disabled>Select a patient</option>
          <option v-for="rel in relationships" :key="rel.id" :value="rel.id">
            {{ rel.client.first_name }} {{ rel.client.last_name }}
          </option>
        </select>
        <ChevronDown :size="15" class="select-caret" />
      </div>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div v-if="isLoadingRelationships" class="placeholder-text">Loading…</div>

    <div v-else-if="!relationships.length" class="empty-state">
      <p class="empty-title">No active patients yet</p>
      <p class="empty-desc">Meal plans can only be created once you have an active relationship with a client.</p>
    </div>

    <template v-else-if="selectedRelationshipId">
      <div v-if="isLoadingPlan" class="placeholder-text">Loading plan…</div>

      <template v-else-if="!plan">
        <div class="surface create-plan-card">
          <h3 class="surface-title">No meal plan yet for {{ selectedClientName }}</h3>
          <div class="form-grid">
            <div class="field">
              <label>Plan Name</label>
              <input v-model="newPlan.name" type="text" placeholder="e.g. Diabetic-Friendly Plan" />
            </div>
            <div class="field">
              <label>Condition</label>
              <select v-model="newPlan.condition">
                <option value="diabetes">Diabetes</option>
                <option value="hypertension">Hypertension</option>
                <option value="renal">Renal</option>
                <option value="weight_loss">Weight Loss</option>
                <option value="weight_gain">Weight Gain</option>
                <option value="general">General</option>
              </select>
            </div>
            <div class="field">
              <label>Target Calories/day</label>
              <input v-model.number="newPlan.target_kcal" type="number" placeholder="1800" />
            </div>
          </div>
          <button class="btn-primary" type="button" :disabled="!newPlan.name || isSaving" @click="createPlan">
            {{ isSaving ? 'Creating…' : 'Create Meal Plan' }}
          </button>
        </div>
      </template>

      <template v-else>
        <div class="surface plan-header-card">
          <div class="plan-header-top">
            <div>
              <h3 class="plan-name">{{ plan.name }}</h3>
              <span class="badge badge-blue">{{ plan.target_kcal ? Math.round(plan.target_kcal) : '—' }} kcal/day</span>
              <span class="badge badge-gold">{{ conditionLabel(plan.condition) }}</span>
            </div>
            <span class="status-pill" :class="plan.status === 'active' ? 'success' : 'neutral'">{{ plan.status === 'active' ? 'Active' : 'Archived' }}</span>
          </div>

          <div class="exchange-totals">
            <div class="exchange-chip"><div class="ex-num">{{ computedTotal('rice_exchanges') }}</div><div class="ex-label">Rice</div></div>
            <div class="exchange-chip"><div class="ex-num">{{ computedTotal('meat_exchanges') }}</div><div class="ex-label">Meat</div></div>
            <div class="exchange-chip"><div class="ex-num">{{ computedTotal('vegetable_exchanges') }}</div><div class="ex-label">Vegetable</div></div>
            <div class="exchange-chip"><div class="ex-num">{{ computedTotal('fruit_exchanges') }}</div><div class="ex-label">Fruit</div></div>
            <div class="exchange-chip"><div class="ex-num">{{ computedTotal('milk_exchanges') }}</div><div class="ex-label">Milk</div></div>
            <div class="exchange-chip"><div class="ex-num">{{ computedTotal('fat_exchanges') }}</div><div class="ex-label">Fat</div></div>
          </div>
          <p class="totals-note">Totals are computed live from the meals below.</p>
        </div>

        <div class="meal-list">
          <div v-for="meal in orderedMeals" :key="meal.id" class="surface meal-card">
            <div class="meal-card-header">
              <span class="meal-name">
                <component :is="mealIcon(meal.meal_time)" :size="15" class="meal-icon" />
                {{ mealTimeLabel(meal.meal_time) }}
              </span>
              <button class="remove-meal-btn" type="button" :disabled="busy" @click="removeMeal(meal)"><X :size="14" /></button>
            </div>

            <div class="meal-exchange-inputs">
              <div v-for="field in exchangeFields" :key="field.key" class="exchange-field">
                <label>{{ field.label }}</label>
                <input
                  type="number" step="0.5" min="0"
                  :value="meal[field.key]"
                  @change="updateMealExchange(meal, field.key, $event.target.value)"
                />
              </div>
            </div>

            <div v-if="meal.food_items.length" class="food-item-list">
              <div v-for="item in meal.food_items" :key="item.id" class="food-item-row">
                <span class="food-name">{{ item.food_name }}</span>
                <span class="food-exchange">{{ item.exchanges }} exchange{{ Number(item.exchanges) === 1 ? '' : 's' }}{{ item.notes ? ' · ' + item.notes : '' }}</span>
                <button class="remove-item-btn" type="button" :disabled="busy" @click="removeFoodItem(item)"><X :size="12" /></button>
              </div>
            </div>
            <p v-else class="food-list-empty">No specific foods listed yet — this meal's exchange counts above are still what the client sees.</p>

            <div class="add-food-row">
              <input v-model="newFoodForm[meal.id].food_name" type="text" placeholder="Food name, e.g. 1 cup Brown Rice" />
              <input v-model.number="newFoodForm[meal.id].exchanges" type="number" step="0.5" placeholder="Exchanges" class="exchange-input" />
              <button class="add-food-btn" type="button" :disabled="!newFoodForm[meal.id].food_name || busy" @click="addFoodItem(meal)">
                <Plus :size="14" />
              </button>
            </div>
          </div>
        </div>

        <div class="add-meal-row">
          <select v-model="newMealTime" class="meal-time-select">
            <option v-for="t in availableMealTimes" :key="t" :value="t">{{ mealTimeLabel(t) }}</option>
          </select>
          <button class="btn-add-meal" type="button" :disabled="!availableMealTimes.length || busy" @click="addMeal">
            <Plus :size="14" /> Add Meal
          </button>
        </div>
      </template>
    </template>

    <div v-else class="empty-state">
      <p class="empty-title">Select a patient to view or create their meal plan</p>
    </div>
  </div>
</template>

<script setup>
import { ChevronDown, Plus, X, Sun, Coffee, Utensils, Apple, Moon } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Meal Plans' })

const { get, post, patch, del } = useApi()
const route = useRoute()

const relationships = ref([])
const isLoadingRelationships = ref(true)
const selectedRelationshipId = ref('')
const errorMessage = ref('')

const plan = ref(null)
const isLoadingPlan = ref(false)
const isSaving = ref(false)
const busy = ref(false)

const newPlan = reactive({ name: '', condition: 'general', target_kcal: null })
const newMealTime = ref('breakfast')
const newFoodForm = reactive({})

const MEAL_ORDER = ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner', 'bedtime_snack']
const MEAL_LABELS = {
  breakfast: 'Breakfast', am_snack: 'AM Snack', lunch: 'Lunch',
  pm_snack: 'PM Snack', dinner: 'Dinner', bedtime_snack: 'Bedtime Snack',
}
const MEAL_ICONS = { breakfast: Sun, am_snack: Coffee, lunch: Utensils, pm_snack: Apple, dinner: Moon, bedtime_snack: Moon }
const CONDITION_LABELS = {
  diabetes: 'Diabetes', hypertension: 'Hypertension', renal: 'Renal',
  weight_loss: 'Weight Loss', weight_gain: 'Weight Gain', general: 'General',
}
const exchangeFields = [
  { key: 'rice_exchanges', label: 'Rice' },
  { key: 'meat_exchanges', label: 'Meat' },
  { key: 'vegetable_exchanges', label: 'Veg' },
  { key: 'fruit_exchanges', label: 'Fruit' },
  { key: 'milk_exchanges', label: 'Milk' },
  { key: 'fat_exchanges', label: 'Fat' },
]

const selectedClientName = computed(() => {
  const rel = relationships.value.find(r => r.id === selectedRelationshipId.value)
  return rel ? `${rel.client.first_name} ${rel.client.last_name}` : ''
})

const orderedMeals = computed(() => {
  if (!plan.value) return []
  return [...plan.value.meals].sort((a, b) => MEAL_ORDER.indexOf(a.meal_time) - MEAL_ORDER.indexOf(b.meal_time))
})
const availableMealTimes = computed(() => {
  const used = new Set(plan.value?.meals.map(m => m.meal_time) || [])
  return MEAL_ORDER.filter(t => !used.has(t))
})
watch(availableMealTimes, (times) => {
  if (!times.includes(newMealTime.value)) newMealTime.value = times[0] || ''
}, { immediate: true })

function mealTimeLabel(t) { return MEAL_LABELS[t] || t }
function mealIcon(t) { return MEAL_ICONS[t] || Sun }
function conditionLabel(c) { return CONDITION_LABELS[c] || c }

function computedTotal(field) {
  if (!plan.value) return 0
  return plan.value.meals.reduce((sum, m) => sum + Number(m[field] || 0), 0)
}

function ensureFoodForm(mealId) {
  if (!newFoodForm[mealId]) {
    newFoodForm[mealId] = { food_name: '', exchanges: 1 }
  }
}

async function updateMealExchange(meal, field, rawValue) {
  const value = Math.max(0, Number(rawValue) || 0)
  const previous = meal[field]
  meal[field] = value
  try {
    await patch(`/rnd/meals/${meal.id}/`, { [field]: value })
  } catch {
    meal[field] = previous
    errorMessage.value = 'Could not update this exchange count. Please try again.'
  }
}

watch(() => plan.value?.meals, (meals) => {
  for (const meal of meals || []) ensureFoodForm(meal.id)
}, { immediate: true, deep: true })

async function loadRelationships() {
  isLoadingRelationships.value = true
  try {
    relationships.value = await get('/rnd/relationships/active/')
    const preselect = Number(route.query.relationship)
    if (preselect && relationships.value.some(r => r.id === preselect)) {
      selectedRelationshipId.value = preselect
    }
  } catch {
    errorMessage.value = 'Could not load your patients. Please try again later.'
  } finally {
    isLoadingRelationships.value = false
  }
}

async function loadPlan() {
  if (!selectedRelationshipId.value) return
  isLoadingPlan.value = true
  errorMessage.value = ''
  plan.value = null
  try {
    const plans = await get(`/rnd/relationships/${selectedRelationshipId.value}/meal-plans/`)
    plan.value = plans.find(p => p.status === 'active') || plans[0] || null
    newPlan.name = ''; newPlan.condition = 'general'; newPlan.target_kcal = null
  } catch {
    errorMessage.value = 'Could not load this patient\'s meal plan.'
  } finally {
    isLoadingPlan.value = false
  }
}
watch(selectedRelationshipId, loadPlan)

async function createPlan() {
  isSaving.value = true
  errorMessage.value = ''
  try {
    plan.value = await post(`/rnd/relationships/${selectedRelationshipId.value}/meal-plans/`, {
      relationship: selectedRelationshipId.value,
      name: newPlan.name,
      condition: newPlan.condition,
      target_kcal: newPlan.target_kcal || undefined,
    })
  } catch {
    errorMessage.value = 'Could not create this meal plan. Please try again.'
  } finally {
    isSaving.value = false
  }
}

async function addMeal() {
  busy.value = true
  errorMessage.value = ''
  try {
    const meal = await post(`/rnd/meal-plans/${plan.value.id}/meals/`, { meal_time: newMealTime.value })
    plan.value.meals.push({ ...meal, food_items: [] })
    ensureFoodForm(meal.id)
    if (availableMealTimes.value.length) newMealTime.value = availableMealTimes.value[0]
  } catch {
    errorMessage.value = 'Could not add this meal. Please try again.'
  } finally {
    busy.value = false
  }
}

async function removeMeal(meal) {
  busy.value = true
  try {
    await del(`/rnd/meals/${meal.id}/`)
    plan.value.meals = plan.value.meals.filter(m => m.id !== meal.id)
  } catch {
    errorMessage.value = 'Could not remove this meal. Please try again.'
  } finally {
    busy.value = false
  }
}

async function addFoodItem(meal) {
  const form = newFoodForm[meal.id]
  if (!form.food_name) return
  busy.value = true
  errorMessage.value = ''
  try {
    const item = await post(`/rnd/meals/${meal.id}/food-items/`, {
      food_name: form.food_name, exchanges: form.exchanges || 1,
    })
    meal.food_items.push(item)
    form.food_name = ''; form.exchanges = 1
  } catch {
    errorMessage.value = 'Could not add this food item. Please try again.'
  } finally {
    busy.value = false
  }
}

async function removeFoodItem(item) {
  busy.value = true
  try {
    await del(`/rnd/food-items/${item.id}/`)
    const meal = plan.value.meals.find(m => m.food_items.some(i => i.id === item.id))
    if (meal) meal.food_items = meal.food_items.filter(i => i.id !== item.id)
  } catch {
    errorMessage.value = 'Could not remove this food item. Please try again.'
  } finally {
    busy.value = false
  }
}

onMounted(loadRelationships)
</script>

<style scoped>
* { box-sizing: border-box; }

.planning-page { font-family: 'Inter', sans-serif; }

.top-controls { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.patient-select { position: relative; }
.patient-select select {
  appearance: none; border: 1px solid #d5dad5; background: #fff;
  padding: 10px 34px 10px 14px; border-radius: 8px; font-size: 0.85rem; color: #1a3a1a; cursor: pointer; min-width: 200px;
}
.select-caret { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #9aaa9a; pointer-events: none; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px 22px; margin-bottom: 16px; }
.surface-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }

.form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 14px; margin-bottom: 18px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; color: #4a5a4a; text-transform: uppercase; }
.field input, .field select {
  border: 1px solid #dde3dd; border-radius: 8px; padding: 9px 12px; font-size: 0.85rem; font-family: inherit; color: #1a3a1a;
}

.btn-primary {
  background: #163a1c; color: #fff; border: none; border-radius: 8px;
  padding: 10px 20px; font-weight: 700; font-size: 0.85rem; cursor: pointer;
}
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.plan-header-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; flex-wrap: wrap; gap: 10px; }
.plan-name { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0 0 8px; }
.badge { font-size: 0.72rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; margin-right: 6px; }
.badge-blue { background: #e3edfc; color: #3b6fd6; }
.badge-gold { background: #fdf1d6; color: #b8860b; }
.status-pill { font-size: 0.72rem; font-weight: 700; padding: 4px 12px; border-radius: 14px; }
.status-pill.success { background: #e6efe0; color: #3a6b3a; }
.status-pill.neutral { background: #eceeec; color: #7a8a7a; }

.exchange-totals { display: grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap: 10px; }
.exchange-chip { background: #f9f9f5; border-radius: 8px; padding: 12px; text-align: center; }
.ex-num { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #1a3a1a; }
.ex-label { font-size: 0.66rem; color: #9aaa9a; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 2px; }
.totals-note { font-size: 0.76rem; color: #9aaa9a; margin: 10px 0 0; }

.meal-card { padding: 0; overflow: hidden; }
.meal-card-header {
  display: flex; align-items: center; justify-content: space-between; gap: 10px; background: #eef3ec; padding: 12px 18px;
}
.meal-name { display: flex; align-items: center; gap: 7px; font-weight: 700; color: #1a3a1a; font-size: 0.88rem; }
.meal-icon { color: #D4A017; }
.meal-exchange-inputs {
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; padding: 14px 18px; border-bottom: 1px solid #f4f4ec;
}
.exchange-field { display: flex; flex-direction: column; gap: 4px; }
.exchange-field label { font-size: 0.66rem; font-weight: 700; color: #9aaa9a; text-transform: uppercase; letter-spacing: 0.03em; }
.exchange-field input {
  border: 1px solid #dde3dd; border-radius: 6px; padding: 6px 8px; font-size: 0.82rem; font-family: inherit; width: 100%;
}
.food-list-empty { padding: 12px 18px; font-size: 0.8rem; color: #9aaa9a; margin: 0; font-style: italic; }
.remove-meal-btn {
  width: 24px; height: 24px; border-radius: 6px; border: none; background: none; color: #a12525;
  display: flex; align-items: center; justify-content: center; cursor: pointer;
}
.remove-meal-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.food-item-list { padding: 4px 0; }
.food-item-row {
  display: flex; align-items: center; gap: 10px; padding: 9px 18px; border-bottom: 1px solid #f4f4ec; font-size: 0.85rem;
}
.food-item-row:last-child { border-bottom: none; }
.food-name { flex: 1; color: #2a3a2a; }
.food-exchange { color: #9aaa9a; font-size: 0.78rem; }
.remove-item-btn {
  width: 18px; height: 18px; border-radius: 4px; border: none; background: #fbe1de; color: #c0483a;
  display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0;
}
.remove-item-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.add-food-row { display: flex; gap: 8px; padding: 12px 18px; border-top: 1px solid #f4f4ec; }
.add-food-row input, .add-food-row select {
  border: 1px solid #dde3dd; border-radius: 6px; padding: 8px 10px; font-size: 0.82rem; font-family: inherit;
}
.add-food-row input[type="text"] { flex: 1; }
.exchange-input { width: 90px; }
.exchange-type-select { width: 120px; }
.add-food-btn {
  width: 34px; height: 34px; border-radius: 6px; border: none; background: #163a1c; color: #fff;
  display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0;
}
.add-food-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.add-meal-row { display: flex; gap: 10px; }
.meal-time-select {
  border: 1px solid #dde3dd; border-radius: 8px; padding: 9px 12px; font-size: 0.85rem; font-family: inherit; color: #1a3a1a;
}
.btn-add-meal {
  display: flex; align-items: center; gap: 6px;
  border: 1px dashed #cdd8cd; background: none; color: #1a6a2a;
  padding: 9px 16px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.btn-add-meal:disabled { opacity: 0.5; cursor: not-allowed; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 48px 20px; text-align: center;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
</style>
