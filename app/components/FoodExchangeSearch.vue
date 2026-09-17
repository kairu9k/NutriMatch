<template>
  <div class="fx-page">
    <div class="page-header">
      <div>
        <p class="page-sub">Search the FNRI Food Exchange List to build evidence-based meal plans.</p>
      </div>
    </div>

    <div class="search-wrap">
      <Search :size="16" class="search-icon" />
      <input v-model="search" type="text" class="search-input" placeholder="Search foods (e.g. banana, bangus)..." />
    </div>

    <!-- CATEGORY FILTER PILLS -->
    <div class="category-row">
      <button
        v-for="cat in categories"
        :key="cat"
        class="category-pill"
        :class="{ active: activeCategory === cat }"
        @click="activeCategory = cat"
      >
        {{ cat || 'All' }}
      </button>
    </div>

    <!-- SAFETY FILTERS -->
    <!-- TODO: these flags are placeholder data, not verified clinical guidance.
         Replace with real FNRI Food Exchange List 4th Ed. safety data, reviewed
         by a licensed RND, before relying on this for actual patient meal plans. -->
    <div class="safety-row">
      <label class="safety-check">
        <input type="checkbox" v-model="diabetesSafe" /> Diabetes-safe
      </label>
      <label class="safety-check">
        <input type="checkbox" v-model="hypertensionSafe" /> Hypertension-safe
      </label>
      <label class="safety-check">
        <input type="checkbox" v-model="renalSafe" /> Renal-safe
      </label>
    </div>

    <!-- FOOD CARD GRID -->
    <div v-if="filteredFoods.length" class="food-grid">
      <div v-for="food in filteredFoods" :key="food.id" class="food-card">
        <div class="food-tags-top">
          <span class="tag category-tag" :class="'cat-' + slug(food.category)">{{ food.category }}</span>
          <span v-if="food.freeFood" class="tag free-food-tag">Free Food</span>
        </div>
        <p class="food-name">{{ food.name }}</p>
        <p class="food-local-name">{{ food.localName }}</p>
        <p class="food-portion">{{ food.portion }} · {{ food.weight }}</p>
        <span v-if="food.nutritionTag" class="tag nutrition-tag" :class="'nut-' + slug(food.nutritionTag)">{{ food.nutritionTag }}</span>
      </div>
    </div>
    <div v-else class="empty-state">
      <SearchX :size="28" class="empty-icon" />
      <p class="empty-title">No foods match your filters</p>
      <p class="empty-desc">Try a different search term or category.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Search, SearchX } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Food Exchange Search' })

const categories = [
  '', 'Vegetable', 'Fruit', 'Milk (Whole)', 'Milk (Low Fat)', 'Milk (Non-fat/Skim)',
  'Rice A (Low Protein)', 'Rice B (Medium Protein)', 'Rice C (High Protein)',
  'Meat (Low Fat)', 'Meat (Medium Fat)', 'Meat (High Fat)', 'Fat', 'Sugar'
]

const activeCategory = ref('')
const search = ref('')
const diabetesSafe = ref(false)
const hypertensionSafe = ref(false)
const renalSafe = ref(false)

// TODO: this is a small placeholder dataset for UI purposes only — replace with
// the real FNRI Food Exchange List 4th Ed., 2020 (all ~550 items), including
// verified nutrition tags and diabetes/hypertension/renal safety flags.
const foods = ref([
  { id: 1, category: 'Vegetable', name: 'Kangkong (Swamp cabbage), leaves', localName: 'Kangkong, dahon', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: true, nutritionTag: 'High Fiber', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 2, category: 'Vegetable', name: 'Ampalaya (Bittermelon/gourd), leaves', localName: 'Ampalaya, dahon', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: true, nutritionTag: 'High Fiber', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 3, category: 'Vegetable', name: 'Sitaw (String/yard long bean), pod', localName: 'Sitaw, bunga', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: false, nutritionTag: 'High Fiber', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 4, category: 'Vegetable', name: 'Kalabasa (Squash), fruit', localName: 'Kalabasa, bunga', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: false, nutritionTag: 'High Potassium', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 5, category: 'Vegetable', name: 'Talong (Eggplant)', localName: 'Talong', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: true, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 6, category: 'Vegetable', name: 'Pechay (Pechay), leaves', localName: 'Pechay, dahon', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: false, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 7, category: 'Vegetable', name: 'Carrot', localName: 'Carrot', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: false, nutritionTag: 'High Potassium', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 8, category: 'Vegetable', name: 'Broccoli', localName: 'Broccoli', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: false, nutritionTag: 'High Fiber', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 9, category: 'Vegetable', name: 'Tomato, canned', localName: 'Kamatis, de lata', portion: '3/4 cup', weight: '110.00g', freeFood: false, nutritionTag: 'High Sodium', diabetesSafe: true, hypertensionSafe: false, renalSafe: false },
  { id: 10, category: 'Vegetable', name: 'Mushroom, fresh', localName: 'Kabuti, sariwa', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: false, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 11, category: 'Vegetable', name: 'Malunggay (Horseradish tree), leaves', localName: 'Malunggay, dahon', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: false, nutritionTag: 'High Fiber', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 12, category: 'Vegetable', name: 'Toge (Mung bean sprout)', localName: 'Toge', portion: '1/2 cup raw or cooked', weight: '45.00g', freeFood: true, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 13, category: 'Fruit', name: 'Saging, lakatan (Banana, lakatan)', localName: 'Saging, lakatan', portion: '1/2 pc of 14 x 3.5 cm', weight: '40.00g', freeFood: false, nutritionTag: 'High Potassium', diabetesSafe: false, hypertensionSafe: true, renalSafe: false },
  { id: 14, category: 'Fruit', name: 'Saging, saba (Banana, saba)', localName: 'Saging, saba', portion: '1/2 pc of 12 x 4.5 cm', weight: '40.00g', freeFood: false, nutritionTag: 'High Potassium', diabetesSafe: false, hypertensionSafe: true, renalSafe: false },
  { id: 15, category: 'Fruit', name: 'Papaya, ripe', localName: 'Papaya, hinog', portion: '3/4 cup or 1 slice', weight: '90.00g', freeFood: false, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 16, category: 'Fruit', name: 'Mangga, kalabaw, ripe', localName: 'Mangga, kalabaw', portion: '1/2 cup, sliced', weight: '80.00g', freeFood: false, nutritionTag: '', diabetesSafe: false, hypertensionSafe: true, renalSafe: true },
  { id: 17, category: 'Fruit', name: 'Dalandan (Orange)', localName: 'Dalandan', portion: '1 pc, small', weight: '130.00g', freeFood: false, nutritionTag: 'High Potassium', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 18, category: 'Fruit', name: 'Pakwan (Watermelon)', localName: 'Pakwan', portion: '1 cup, cubed', weight: '160.00g', freeFood: false, nutritionTag: 'High Potassium', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 19, category: 'Fruit', name: 'Pinya (Pineapple)', localName: 'Pinya', portion: '3/4 cup, diced', weight: '120.00g', freeFood: false, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 20, category: 'Fruit', name: 'Suha (Pomelo)', localName: 'Suha', portion: '3/4 cup, sections', weight: '150.00g', freeFood: false, nutritionTag: 'High Potassium', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 21, category: 'Rice A (Low Protein)', name: 'Rice, cooked', localName: 'Kanin', portion: '1/3 cup', weight: '60.00g', freeFood: false, nutritionTag: '', diabetesSafe: false, hypertensionSafe: true, renalSafe: true },
  { id: 22, category: 'Rice B (Medium Protein)', name: 'Corn, boiled', localName: 'Mais, nilaga', portion: '1/2 cup', weight: '85.00g', freeFood: false, nutritionTag: '', diabetesSafe: false, hypertensionSafe: true, renalSafe: true },
  { id: 23, category: 'Meat (Low Fat)', name: 'Fish, bangus, grilled', localName: 'Bangus, inihaw', portion: '1 piece, small', weight: '35.00g', freeFood: false, nutritionTag: 'High Sodium', diabetesSafe: true, hypertensionSafe: false, renalSafe: false },
  { id: 24, category: 'Meat (Medium Fat)', name: 'Chicken, breast, skinless', localName: 'Manok, dibdib', portion: '1 piece, small', weight: '35.00g', freeFood: false, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 25, category: 'Meat (High Fat)', name: 'Pork, belly, roasted', localName: 'Baboy, liempo', portion: '1 piece, small', weight: '35.00g', freeFood: false, nutritionTag: 'High Sodium', diabetesSafe: true, hypertensionSafe: false, renalSafe: false },
  { id: 26, category: 'Milk (Whole)', name: 'Milk, whole, fresh', localName: 'Gatas, buo', portion: '1 cup', weight: '240.00ml', freeFood: false, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 27, category: 'Milk (Low Fat)', name: 'Milk, low fat', localName: 'Gatas, mababa ang taba', portion: '1 cup', weight: '240.00ml', freeFood: false, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 28, category: 'Milk (Non-fat/Skim)', name: 'Milk, non-fat/skim', localName: 'Gatas, walang taba', portion: '1 cup', weight: '240.00ml', freeFood: false, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: false },
  { id: 29, category: 'Fat', name: 'Cooking oil', localName: 'Mantika', portion: '1 tsp', weight: '5.00ml', freeFood: false, nutritionTag: '', diabetesSafe: true, hypertensionSafe: true, renalSafe: true },
  { id: 30, category: 'Sugar', name: 'White sugar', localName: 'Asukal, puti', portion: '1 tsp', weight: '5.00g', freeFood: false, nutritionTag: '', diabetesSafe: false, hypertensionSafe: true, renalSafe: true }
])

const filteredFoods = computed(() => {
  return foods.value.filter(f => {
    const matchesCategory = !activeCategory.value || f.category === activeCategory.value
    const matchesSearch = !search.value.trim() ||
      f.name.toLowerCase().includes(search.value.toLowerCase()) ||
      f.localName.toLowerCase().includes(search.value.toLowerCase())
    const matchesDiabetes = !diabetesSafe.value || f.diabetesSafe
    const matchesHypertension = !hypertensionSafe.value || f.hypertensionSafe
    const matchesRenal = !renalSafe.value || f.renalSafe
    return matchesCategory && matchesSearch && matchesDiabetes && matchesHypertension && matchesRenal
  })
})

function slug(text) {
  return (text || '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
}
</script>

<style scoped>
* { box-sizing: border-box; }

.fx-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 40px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.9rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.search-wrap { position: relative; margin-bottom: 30px; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: #9aaa9a; }
.search-input {
  width: 100%; max-width: 480px; border: 1px solid #d5dad5; border-radius: 10px; padding: 11px 16px 11px 38px;
  font-size: 0.85rem; font-family: inherit; color: #2a2a2a;
}
.search-input:focus { outline: none; border-color: #D4A017; }

/* CATEGORY PILLS */
.category-row { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 18px; }
.category-pill {
  border: 1px solid #e0e5e0; background: #fff; color: #4a5a4a;
  padding: 9px 16px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; cursor: pointer; white-space: nowrap;
}
.category-pill.active { background: #163a1c; color: #fff; border-color: #163a1c; }

/* SAFETY CHECKBOXES */
.safety-row { display: flex; gap: 24px; margin-bottom: 28px; }
.safety-check { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: #3a4a3a; cursor: pointer; }
.safety-check input { width: 16px; height: 16px; accent-color: #163a1c; cursor: pointer; }

/* FOOD GRID */
.food-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }
.food-card {
  background: #fff; border-radius: 14px; border: 1.5px solid #eceeec; padding: 20px;
  display: flex; flex-direction: column; gap: 7px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.food-card:hover {
  border-color: #1f8f5c;
  box-shadow: 0 4px 14px rgba(31,143,92,0.1);
}
.food-tags-top { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 6px; }
.tag { font-size: 0.66rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.category-tag { background: #e6f4e6; color: #2e7d32; }
.category-tag.cat-fruit { background: #fdeadf; color: #d9683f; }
.category-tag.cat-fat { background: #eef0ee; color: #6a7a6a; }
.category-tag.cat-sugar { background: #fbe1de; color: #c0483a; }
.category-tag.cat-rice-a-low-protein,
.category-tag.cat-rice-b-medium-protein,
.category-tag.cat-rice-c-high-protein { background: #fdf1d6; color: #b8860b; }
.category-tag.cat-meat-low-fat,
.category-tag.cat-meat-medium-fat,
.category-tag.cat-meat-high-fat { background: #fbe1de; color: #c0483a; }
.category-tag.cat-milk-whole,
.category-tag.cat-milk-low-fat,
.category-tag.cat-milk-non-fat-skim { background: #e3edfc; color: #3b6fd6; }
.free-food-tag { background: #eef0ee; color: #4a5a4a; }

.food-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0; line-height: 1.3; }
.food-local-name { font-size: 0.78rem; color: #8a9a8a; font-style: italic; margin: 0; }
.food-portion { font-size: 0.78rem; color: #4a5a4a; margin: 4px 0 6px; }

.nutrition-tag { align-self: flex-start; background: #fdf1d6; color: #b8860b; }
.nutrition-tag.nut-high-sodium { background: #fbe1de; color: #c0483a; }
.nutrition-tag.nut-high-potassium { background: #e3edfc; color: #3b6fd6; }
.nutrition-tag.nut-high-fiber { background: #e6f4e6; color: #2e7d32; }

/* EMPTY STATE */
.empty-state { text-align: center; padding: 60px 24px; background: #fff; border-radius: 14px; border: 1px solid #eceeec; }
.empty-icon { color: #c8d0c8; margin-bottom: 12px; }
.empty-title { font-size: 0.95rem; font-weight: 700; color: #4a5a4a; margin: 0 0 6px; }
.empty-desc { font-size: 0.82rem; color: #9aaa9a; margin: 0; }

@media (max-width: 1400px) { .food-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px) { .food-grid { grid-template-columns: repeat(2, 1fr); } .page-header { flex-direction: column; } .search-input { width: 100%; } }
</style>