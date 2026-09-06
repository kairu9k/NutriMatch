<template>
  <div class="meal-plan-page">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="plan">
      <div class="page-header">
        <div>
          <h1 class="page-title">{{ plan.name }}</h1>
          <p class="page-sub">{{ conditionLabel }} · Prescribed by your RND</p>
        </div>
        <span class="status-pill" :class="plan.status === 'active' ? 'success' : 'neutral'">{{ plan.status === 'active' ? 'Active' : 'Archived' }}</span>
      </div>

      <div class="surface target-card">
        <div class="target-row">
          <div>
            <p class="eyebrow">DAILY TARGET</p>
            <p class="target-kcal">{{ plan.target_kcal ? Math.round(plan.target_kcal) : '—' }} <span class="kcal-unit">kcal</span></p>
          </div>
          <div class="condition-block">
            <p class="condition-label">Condition</p>
            <span class="status-pill info">{{ conditionLabel }}</span>
          </div>
        </div>

        <p class="eyebrow">FNRI FOOD EXCHANGE TOTALS (PER DAY)</p>
        <div class="exchange-grid">
          <div class="exchange-chip"><div class="ex-num">{{ plan.total_rice }}</div><div class="ex-label">Rice</div></div>
          <div class="exchange-chip"><div class="ex-num">{{ plan.total_meat }}</div><div class="ex-label">Meat</div></div>
          <div class="exchange-chip"><div class="ex-num">{{ plan.total_vegetable }}</div><div class="ex-label">Vegetable</div></div>
          <div class="exchange-chip"><div class="ex-num">{{ plan.total_fruit }}</div><div class="ex-label">Fruit</div></div>
          <div class="exchange-chip"><div class="ex-num">{{ plan.total_milk }}</div><div class="ex-label">Milk</div></div>
          <div class="exchange-chip"><div class="ex-num">{{ plan.total_fat }}</div><div class="ex-label">Fat</div></div>
        </div>
      </div>

      <div v-if="plan.meals.length" class="meal-list">
        <div v-for="meal in orderedMeals(plan.meals)" :key="meal.id" class="meal-block">
          <div class="meal-block-header">
            <span class="meal-name">
              <component :is="mealIcon(meal.meal_time)" :size="16" class="meal-icon" />
              {{ mealTimeLabel(meal.meal_time) }}
            </span>
            <span class="status-pill neutral">{{ exchangeSummary(meal) }}</span>
          </div>
          <div v-if="meal.food_items.length" class="food-item-list">
            <div v-for="item in meal.food_items" :key="item.id" class="food-item-row">
              <span>{{ item.food_name }}</span>
              <span class="food-note">{{ item.notes || `${item.exchanges} Exchange` }}</span>
            </div>
          </div>
          <p v-else class="no-items-note">No specific foods listed for this meal yet.</p>
        </div>
      </div>
      <div v-else class="empty-note-card">No meals have been added to this plan yet.</div>

      <div class="info-note">
        <Info :size="16" />
        <p>Exchange amounts are based on the FNRI Food Exchange Lists. Your RND may adjust portions during follow-up consultations based on your progress.</p>
      </div>
    </template>

    <div v-else class="empty-state">
      <div class="empty-icon"><ClipboardList :size="28" /></div>
      <p class="empty-title">No meal plan yet</p>
      <p class="empty-desc">Your RND will create a personalized meal plan for you as part of your care journey.</p>
    </div>
  </div>
</template>

<script setup>
import { Info, ClipboardList, Sunrise, Coffee, Sun, Moon } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'My Meal Plan' })

const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const plans = ref([])

const plan = computed(() => plans.value.find(p => p.status === 'active') || plans.value[0] || null)

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

async function loadMealPlans() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    plans.value = await get('/client/meal-plans/')
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

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.status-pill { font-size: 0.76rem; font-weight: 700; padding: 5px 14px; border-radius: 14px; white-space: nowrap; }
.status-pill.success { background: #e6efe0; color: #3a6b3a; }
.status-pill.info { background: #e3edf7; color: #2f6fa8; }
.status-pill.neutral { background: #eceeec; color: #7a8a7a; }

.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; }
.target-card { padding: 22px; margin-bottom: 20px; }
.target-row { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; margin-bottom: 18px; }
.eyebrow { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; color: #8a9a8a; margin: 0 0 8px; }
.target-kcal { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.kcal-unit { font-size: 0.9rem; font-weight: 400; color: #9aaa9a; }
.condition-block { text-align: right; }
.condition-label { font-size: 0.82rem; color: #6a7a6a; margin: 0 0 6px; }

.exchange-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(90px, 1fr)); gap: 10px; }
.exchange-chip { background: #f9f9f5; border-radius: 8px; padding: 14px; text-align: center; }
.ex-num { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #1a3a1a; }
.ex-label { font-size: 0.68rem; color: #9aaa9a; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 2px; }

.meal-list { display: flex; flex-direction: column; gap: 14px; margin-bottom: 20px; }
.meal-block { background: #fff; border-radius: 12px; border: 1px solid #eceeec; overflow: hidden; }
.meal-block-header {
  background: #eef3ec; padding: 13px 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
}
.meal-name { font-weight: 700; color: #1a3a1a; font-size: 0.92rem; display: flex; align-items: center; gap: 8px; }
.meal-icon { color: #D4A017; }

.food-item-list { padding: 0; }
.food-item-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 11px 20px; border-bottom: 1px solid #f4f4ec; font-size: 0.86rem; color: #2a3a2a;
}
.food-item-row:last-child { border-bottom: none; }
.food-note { color: #9aaa9a; font-size: 0.8rem; }
.no-items-note { padding: 16px 20px; font-size: 0.83rem; color: #9aaa9a; margin: 0; }

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
</style>
