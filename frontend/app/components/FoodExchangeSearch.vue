<template>
  <div class="search-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Food Exchange Search</h1>
        <p class="page-sub">Search the FNRI Food Exchange List to build evidence-based meal plans.</p>
      </div>
      <div class="search-box">
        <Search :size="16" class="search-icon" />
        <input v-model="search" type="text" placeholder="Search foods (e.g. banana, bangus)..." />
      </div>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div v-if="categories.length" class="filter-row">
      <div class="chip-group">
        <button class="filter-chip" :class="{ active: activeCategory === null }" @click="activeCategory = null">All</button>
        <button
          v-for="c in categories"
          :key="c.id"
          class="filter-chip"
          :class="{ active: activeCategory === c.id }"
          :style="activeCategory === c.id ? { background: c.color, borderColor: c.color } : {}"
          @click="activeCategory = c.id"
        >
          {{ c.name }}
        </button>
      </div>

      <div class="safety-group">
        <label v-for="f in safetyFilters" :key="f.key" class="safety-toggle" :class="{ active: safety[f.key] }">
          <input type="checkbox" v-model="safety[f.key]" />
          {{ f.label }}
        </label>
      </div>
    </div>

    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="items.length">
      <div v-if="filteredItems.length" class="item-grid">
        <div v-for="item in filteredItems" :key="item.id" class="item-card">
          <div class="item-top">
            <span class="category-pill" :style="{ background: item.category.color + '22', color: item.category.color }">
              {{ item.category.name }}
            </span>
            <span v-if="item.is_free_food" class="free-pill">Free Food</span>
          </div>
          <h3 class="item-name">{{ item.name }}</h3>
          <p v-if="item.local_name" class="item-local">{{ item.local_name }}</p>
          <p class="item-measure">{{ item.household_measure || '—' }}<span v-if="item.ep_grams"> · {{ item.ep_grams }}g</span></p>

          <div class="flag-row">
            <span v-if="!item.ok_for_diabetes" class="flag-pill warn">Not for Diabetes</span>
            <span v-if="!item.ok_for_hypertension" class="flag-pill warn">Not for Hypertension</span>
            <span v-if="!item.ok_for_renal" class="flag-pill warn">Not for Renal</span>
            <span v-if="item.is_high_sodium" class="flag-pill neutral">High Sodium</span>
            <span v-if="item.is_high_potassium" class="flag-pill neutral">High Potassium</span>
            <span v-if="item.is_high_fiber" class="flag-pill good">High Fiber</span>
            <span v-if="item.is_low_gi" class="flag-pill good">Low GI</span>
          </div>

          <p v-if="item.notes" class="item-notes">{{ item.notes }}</p>
        </div>
      </div>
      <p v-else class="empty-text">No foods match your search and filters.</p>
    </template>

    <div v-else class="empty-state">
      <div class="empty-icon"><SearchX :size="28" /></div>
      <p class="empty-title">No food exchange data yet</p>
      <p class="empty-desc">Ask an admin to run the seed data command to load the FNRI Food Exchange List.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Search, SearchX } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Food Exchange Search' })

const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const categories = ref([])
const items = ref([])
const search = ref('')
const activeCategory = ref(null)

const safetyFilters = [
  { key: 'ok_for_diabetes', label: 'Diabetes-safe' },
  { key: 'ok_for_hypertension', label: 'Hypertension-safe' },
  { key: 'ok_for_renal', label: 'Renal-safe' },
]
const safety = reactive({ ok_for_diabetes: false, ok_for_hypertension: false, ok_for_renal: false })

const filteredItems = computed(() => {
  const q = search.value.trim().toLowerCase()
  return items.value.filter((item) => {
    if (activeCategory.value !== null && item.category.id !== activeCategory.value) return false
    if (q && !item.name.toLowerCase().includes(q) && !(item.local_name || '').toLowerCase().includes(q)) return false
    if (safety.ok_for_diabetes && !item.ok_for_diabetes) return false
    if (safety.ok_for_hypertension && !item.ok_for_hypertension) return false
    if (safety.ok_for_renal && !item.ok_for_renal) return false
    return true
  })
})

async function loadData() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [cats, foods] = await Promise.all([
      get('/food-exchange/categories/'),
      get('/food-exchange/items/'),
    ])
    categories.value = cats
    items.value = foods
  } catch {
    errorMessage.value = 'Could not load food exchange data. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
* { box-sizing: border-box; }

.search-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.search-box {
  display: flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #e5e8e5;
  border-radius: 8px; padding: 10px 14px; width: 300px; flex-shrink: 0;
}
.search-box input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.filter-row { display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px; }
.chip-group { display: flex; gap: 8px; flex-wrap: wrap; }
.filter-chip {
  padding: 8px 16px; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
  background: #fff; border: 1px solid #eceeec; color: #6a7a6a; cursor: pointer;
}
.filter-chip.active { color: #fff; }

.safety-group { display: flex; gap: 14px; flex-wrap: wrap; }
.safety-toggle {
  display: flex; align-items: center; gap: 6px; font-size: 0.82rem; color: #4a5a4a;
  cursor: pointer; user-select: none;
}
.safety-toggle input { cursor: pointer; }
.safety-toggle.active { color: #1a3a1a; font-weight: 700; }

.item-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.item-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 18px 20px;
  display: flex; flex-direction: column;
}
.item-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.category-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.free-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; background: #e6efe0; color: #3a6b3a; }

.item-name { font-family: 'Playfair Display', serif; font-size: 0.95rem; color: #1a3a1a; margin: 0 0 2px; }
.item-local { font-size: 0.8rem; color: #8a9a8a; font-style: italic; margin: 0 0 8px; }
.item-measure { font-size: 0.82rem; color: #4a5a4a; margin: 0 0 12px; }

.flag-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }
.flag-pill { font-size: 0.68rem; font-weight: 600; padding: 3px 9px; border-radius: 10px; }
.flag-pill.warn { background: #fbe1de; color: #c0483a; }
.flag-pill.neutral { background: #eceeec; color: #6a7a6a; }
.flag-pill.good { background: #e6efe0; color: #3a6b3a; }

.item-notes { font-size: 0.78rem; color: #9aaa9a; margin: 8px 0 0; line-height: 1.4; }

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
.empty-text { font-size: 0.85rem; color: #9aaa9a; padding: 20px; text-align: center; }
</style>
