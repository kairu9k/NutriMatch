<template>
  <div>
    <!-- TOP CONTROLS -->
    <div class="top-controls">
      <div class="mode-toggle">
        <button class="mode-btn" :class="{ active: mode === 'view' }" @click="mode = 'view'">
          <Eye :size="15" /> View Plans
        </button>
        <button class="mode-btn" :class="{ active: mode === 'create' }" @click="mode = 'create'">
          <Plus :size="15" /> Create Plan
        </button>
      </div>

      <div class="patient-select">
        <select v-model="selectedPatient">
          <option v-for="p in patients" :key="p" :value="p">{{ p }}</option>
        </select>
        <ChevronDown :size="15" class="select-caret" />
      </div>
    </div>

    <!-- ================= VIEW PLANS MODE ================= -->
    <div v-if="mode === 'view'" class="planning-layout">
      <div class="panel plan-panel">
        <div class="plan-header">
          <div>
            <h3>Weekly Meal Plan — {{ selectedPatient }}</h3>
          </div>
          <div class="plan-badges">
            <span class="badge badge-blue">{{ planMeta.kcalPerDay }} kcal/day</span>
            <span class="badge badge-gold">{{ planMeta.dietType }}</span>
          </div>
        </div>

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

        <div class="meal-list">
          <div class="meal-row" v-for="meal in currentDayMeals" :key="meal.type">
            <div class="meal-info">
              <div class="meal-label">
                <component :is="meal.icon" :size="14" />
                {{ meal.type }} · {{ meal.time }}
              </div>
              <div class="meal-title">{{ meal.title }}</div>
              <div class="meal-breakdown">{{ meal.breakdown }}</div>
            </div>
            <div class="meal-kcal">{{ meal.kcal }} kcal</div>
          </div>
        </div>

        <div class="plan-actions">
          <button class="btn-secondary"><Printer :size="15" /> Print Plan</button>
          <button class="btn-secondary" @click="mode = 'create'"><Pencil :size="15" /> Edit Plan</button>
          <button class="btn-primary"><Send :size="15" /> Send to Patient</button>
        </div>
      </div>

      <!-- RIGHT SIDEBAR -->
      <div class="side-column">
        <div class="panel">
          <h4 class="side-title">Nutritional Summary</h4>
          <span class="side-subtitle">Monday</span>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Total Calories</span><span>{{ nutrition.calories.value }} / {{ nutrition.calories.target }} kcal</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-green" :style="{ width: pct(nutrition.calories) + '%' }"></div></div>
          </div>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Carbohydrates</span><span>{{ nutrition.carbs.value }}g / {{ nutrition.carbs.target }}g</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-gold" :style="{ width: pct(nutrition.carbs) + '%' }"></div></div>
          </div>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Protein</span><span>{{ nutrition.protein.value }}g / {{ nutrition.protein.target }}g</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-green" :style="{ width: pct(nutrition.protein) + '%' }"></div></div>
          </div>
          <div class="nutrient-row">
            <div class="nutrient-top"><span>Fat</span><span>{{ nutrition.fat.value }}g / {{ nutrition.fat.target }}g</span></div>
            <div class="nutrient-bar"><div class="nutrient-fill fill-dark" :style="{ width: pct(nutrition.fat) + '%' }"></div></div>
          </div>
        </div>

        <div class="panel">
          <div class="side-header-row">
            <h4 class="side-title">Saved Plans</h4>
            <button class="link-btn"><Plus :size="13" /> New Plan</button>
          </div>
          <div class="saved-plan-card">
            <div>
              <div class="saved-plan-name">{{ planMeta.name }}</div>
              <div class="saved-plan-meta">{{ planMeta.dietType }} · {{ planMeta.kcalPerDay }} kcal/day</div>
            </div>
            <span class="active-pill">ACTIVE</span>
          </div>
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

    <!-- ================= CREATE PLAN MODE ================= -->
    <div v-else class="planning-layout">
      <div class="create-column">
        <div class="panel">
          <h4 class="side-title">Plan Details</h4>
          <div class="form-row">
            <div class="field">
              <label>Plan Name</label>
              <input v-model="planMeta.name" type="text" />
            </div>
            <div class="field">
              <label>Diet Type</label>
              <input v-model="planMeta.dietType" type="text" />
            </div>
            <div class="field">
              <label>Target Calories/day</label>
              <input v-model="planMeta.kcalPerDay" type="number" />
            </div>
          </div>
        </div>

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
            <span class="meal-edit-time">{{ meal.time }}</span>
          </div>

          <div class="food-table">
            <div class="food-table-head">
              <span>FOOD ITEM</span>
              <span>PORTION</span>
              <span>KCAL</span>
              <span>CARB(G)</span>
              <span>PROT(G)</span>
              <span>FAT(G)</span>
              <span></span>
            </div>
            <div class="food-table-row" v-for="(item, idx) in meal.items" :key="idx">
              <button class="remove-btn" @click="removeItem(meal, idx)"><X :size="12" /></button>
              <input v-model="item.name" type="text" placeholder="e.g., Brown rice" />
              <input v-model="item.portion" type="text" placeholder="e.g., ½ cup" />
              <input v-model.number="item.kcal" type="number" placeholder="0" />
              <input v-model.number="item.carb" type="number" placeholder="0" />
              <input v-model.number="item.prot" type="number" placeholder="0" />
              <input v-model.number="item.fat" type="number" placeholder="0" />
            </div>
          </div>

          <button class="btn-add-food" @click="addItem(meal)"><Plus :size="14" /> Add Food Item</button>
        </div>
      </div>

      <!-- RIGHT SIDEBAR (CREATE MODE) -->
      <div class="side-column">
        <div class="panel">
          <div class="side-header-row">
            <h4 class="side-title">Live Preview</h4>
            <span class="preview-day">{{ activeDay === 'Mon' ? 'Monday' : activeDay }}</span>
          </div>
          <div class="preview-list">
            <div class="preview-item" v-for="meal in currentDayMeals.filter(m => m.items.some(i => i.name))" :key="meal.type" :class="'preview-' + meal.accent">
              <div class="preview-label"><component :is="meal.icon" :size="13" /> {{ meal.type }}</div>
              <div class="preview-food">{{ firstFoodSummary(meal) }}</div>
              <div class="preview-kcal">{{ mealTotal(meal, 'kcal') }} kcal</div>
            </div>
          </div>
        </div>

        <div class="panel">
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

        <div class="panel">
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
  Eye, Plus, ChevronDown, Printer, Pencil, Send, X,
  Sun, Coffee, Utensils, Apple, Moon
} from 'lucide-vue-next'
import { db } from '~/mock/mockDatabase'

const mode = ref('view')

// Patient list + selection — pulled from the shared mock db
const patients = computed(() => db.patients.map(p => p.name))
const selectedPatient = ref(db.patients[0]?.name || '')

const selectedPatientId = computed(() => {
  const match = db.patients.find(p => p.name === selectedPatient.value)
  return match?.id || null
})

const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const activeDay = ref('Mon')
const mealOrder = ['Breakfast', 'Morning Snack', 'Lunch', 'Afternoon Snack', 'Dinner']
const mealIcons = { Breakfast: Sun, 'Morning Snack': Coffee, Lunch: Utensils, 'Afternoon Snack': Apple, Dinner: Moon }
const mealAccents = { Breakfast: 'green', 'Morning Snack': 'gold', Lunch: 'blue', 'Afternoon Snack': 'gold', Dinner: 'blue' }

function emptyWeek() {
  const week = {}
  for (const day of days) {
    week[day] = {}
    for (const type of mealOrder) week[day][type] = { time: '', items: [] }
  }
  return week
}

const planMeta = reactive({ name: '', dietType: '', kcalPerDay: 0 })
const targets = reactive({ carb: 0, protein: 0, fat: 0 })
const instructions = reactive({ allergies: '', notes: '' })
const weeklyPlan = reactive(emptyWeek())

// Load whichever patient's plan matches the current selection, deep-copied
// so edits here don't mutate the shared mock db directly.
function loadPlanForPatient() {
  const found = db.mealPlanDetails.find(m => m.patientId === selectedPatientId.value)

  if (!found) {
    planMeta.name = ''
    planMeta.dietType = ''
    planMeta.kcalPerDay = 0
    targets.carb = 0
    targets.protein = 0
    targets.fat = 0
    instructions.allergies = ''
    instructions.notes = ''
    Object.assign(weeklyPlan, emptyWeek())
    return
  }

  planMeta.name = found.planName
  planMeta.dietType = found.dietType
  planMeta.kcalPerDay = found.kcalTarget
  targets.carb = found.carbTarget
  targets.protein = found.proteinTarget
  targets.fat = found.fatTarget
  instructions.allergies = found.allergies
  instructions.notes = found.notes
  Object.assign(weeklyPlan, JSON.parse(JSON.stringify(found.week)))
}

loadPlanForPatient()
watch(selectedPatient, loadPlanForPatient)

// Nutritional Summary is now computed live from the active day's actual items
const nutrition = computed(() => {
  const dayTotals = { calories: 0, carb: 0, protein: 0, fat: 0 }
  for (const type of mealOrder) {
    for (const item of weeklyPlan[activeDay.value][type].items) {
      dayTotals.calories += Number(item.kcal) || 0
      dayTotals.carb += Number(item.carb) || 0
      dayTotals.protein += Number(item.prot) || 0
      dayTotals.fat += Number(item.fat) || 0
    }
  }
  return {
    calories: { value: dayTotals.calories, target: planMeta.kcalPerDay },
    carbs: { value: dayTotals.carb, target: targets.carb },
    protein: { value: dayTotals.protein, target: targets.protein },
    fat: { value: dayTotals.fat, target: targets.fat }
  }
})
function pct(n) {
  if (!n.target) return 0
  return Math.min(100, Math.round((n.value / n.target) * 100))
}

const currentDayMeals = computed(() => {
  return mealOrder.map(type => {
    const meal = weeklyPlan[activeDay.value][type]
    const totalKcal = meal.items.reduce((sum, i) => sum + (Number(i.kcal) || 0), 0)
    const summary = meal.items.filter(i => i.name).map(i => `${i.name} (${i.portion || '1'})`).join(' + ')
    const breakdown = meal.items.filter(i => i.name)
      .map(i => `${i.name}: ${i.kcal || 0}kcal | ${i.carb || 0}g carb | ${i.prot || 0}g prot | ${i.fat || 0}g fat`)
      .join(' | ')
    return {
      type,
      time: meal.time,
      items: meal.items,
      icon: mealIcons[type],
      accent: mealAccents[type],
      kcal: totalKcal,
      title: summary || 'No items added',
      breakdown: breakdown || '—'
    }
  })
})

function addItem(meal) {
  weeklyPlan[activeDay.value][meal.type].items.push({ name: '', portion: '', kcal: 0, carb: 0, prot: 0, fat: 0 })
}
function removeItem(meal, idx) {
  weeklyPlan[activeDay.value][meal.type].items.splice(idx, 1)
}

function firstFoodSummary(meal) {
  const first = meal.items.find(i => i.name)
  const count = meal.items.filter(i => i.name).length
  return first ? `${first.name}${count > 1 ? ` (${count})` : ''}` : ''
}
function mealTotal(meal, field) {
  return meal.items.reduce((sum, i) => sum + (Number(i[field]) || 0), 0)
}
function dayTotal(field) {
  return currentDayMeals.value.reduce((sum, meal) => sum + mealTotal(meal, field), 0)
}
function macroPct(field) {
  const fieldTargets = { kcal: planMeta.kcalPerDay, carb: targets.carb, prot: targets.protein, fat: targets.fat }
  const target = fieldTargets[field]
  if (!target) return 0
  return Math.min(100, Math.round((dayTotal(field) / target) * 100))
}
</script>

<style scoped>
.top-controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }

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

.planning-layout { display: grid; grid-template-columns: 2.3fr 1fr; gap: 20px; align-items: start; }

.panel { background: #fff; border-radius: 12px; padding: 22px; border: 1px solid #eceeec; margin-bottom: 16px; }

/* VIEW MODE */
.plan-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.plan-header h3 { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0; }
.plan-badges { display: flex; gap: 8px; }
.badge { font-size: 0.72rem; font-weight: 700; padding: 4px 12px; border-radius: 20px; }
.badge-blue { background: #e3edfc; color: #3b6fd6; }
.badge-gold { background: #fdf1d6; color: #b8860b; }

.day-tabs { display: flex; gap: 6px; margin-bottom: 20px; }
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

/* SIDE COLUMN (shared) */
.side-title { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
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

/* CREATE MODE */
.form-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 12px; }
.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.field label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; color: #4a5a4a; text-transform: uppercase; }
.field input, .field textarea {
  border: 1px solid #dde3dd; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #1a3a1a;
}
.field textarea { resize: vertical; }

.meal-edit-panel { padding: 0; overflow: hidden; }
.meal-edit-header {
  display: flex; justify-content: space-between; align-items: center;
  background: #eef5ee; padding: 14px 22px;
}
.meal-edit-label { display: flex; align-items: center; gap: 6px; font-size: 0.78rem; font-weight: 700; color: #1a3a1a; letter-spacing: 0.03em; }
.meal-edit-time { font-size: 0.75rem; color: #7a8a7a; }

.food-table { padding: 16px 22px 0; }
.food-table-head, .food-table-row {
  display: grid; grid-template-columns: 24px 2fr 1fr 0.8fr 0.9fr 0.9fr 0.8fr; gap: 10px; align-items: center;
}
.food-table-head { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.04em; color: #9aaa9a; padding-bottom: 8px; }
.food-table-head span:first-child { visibility: hidden; }
.food-table-row { margin-bottom: 8px; }
.food-table-row input {
  border: 1px solid #e0e5e0; border-radius: 6px; padding: 7px 9px; font-size: 0.82rem; font-family: inherit; width: 100%;
}
.remove-btn {
  width: 20px; height: 20px; border-radius: 5px; border: none;
  background: #fbe1de; color: #c0483a; display: flex; align-items: center; justify-content: center; cursor: pointer;
}

.btn-add-food {
  display: flex; align-items: center; gap: 6px; justify-content: center;
  width: calc(100% - 44px); margin: 4px 22px 18px;
  border: 1px dashed #cdd8cd; background: none; color: #1a6a2a;
  padding: 10px; border-radius: 8px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.btn-add-food:hover { background: #f4f8f4; }

.preview-list { display: flex; flex-direction: column; gap: 8px; }
.preview-item { border-left: 3px solid #ccc; background: #fafbfa; border-radius: 8px; padding: 10px 12px; }
.preview-green { border-left-color: #2e9e52; }
.preview-gold { border-left-color: #D4A017; }
.preview-blue { border-left-color: #3b6fd6; }
.preview-label { display: flex; align-items: center; gap: 5px; font-size: 0.72rem; font-weight: 700; color: #4a5a4a; margin-bottom: 3px; }
.preview-food { font-size: 0.8rem; color: #1a3a1a; margin-bottom: 3px; }
.preview-kcal { font-size: 0.72rem; color: #9aaa9a; }
.preview-day { font-size: 0.72rem; color: #9aaa9a; }

.macro-row { display: flex; justify-content: space-between; font-size: 0.82rem; color: #3a4a3a; margin-top: 14px; margin-bottom: 6px; }
.macro-value { font-weight: 600; }
.macro-bar { height: 6px; background: #eceeec; border-radius: 3px; overflow: hidden; }
.macro-fill { height: 100%; border-radius: 3px; }
.macro-note { font-size: 0.72rem; color: #9aaa9a; margin-top: 16px; }

@media (max-width: 1150px) {
  .planning-layout { grid-template-columns: 1fr; }
  .form-row { grid-template-columns: 1fr; }
  .food-table-head, .food-table-row { grid-template-columns: 20px 2fr 1fr 1fr 1fr; }
  .food-table-head span:nth-child(6), .food-table-row input:nth-child(6),
  .food-table-head span:nth-child(7), .food-table-row input:nth-child(7) { display: none; }
}
</style>