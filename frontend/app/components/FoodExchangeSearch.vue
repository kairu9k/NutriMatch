<template>
  <div class="search-page">
    <div class="page-header">
      <p class="page-sub">{{ source === 'usda' ? 'Search USDA FoodData Central for foods the FNRI list doesn\'t have. Values are per 100 g.' : 'Search the FNRI Food Exchange List to build evidence-based meal plans.' }}</p>
    </div>

    <div class="source-tabs" role="tablist" aria-label="Food source">
      <button type="button" role="tab" class="source-tab" :class="{ on: source === 'fnri' }" :aria-selected="source === 'fnri'" @click="source = 'fnri'"><span class="long">FNRI Food Exchange List</span><span class="short">FNRI</span></button>
      <button type="button" role="tab" class="source-tab" :class="{ on: source === 'usda' }" :aria-selected="source === 'usda'" @click="source = 'usda'"><span class="long">USDA FoodData Central</span><span class="short">USDA</span></button>
    </div>

    <div class="search-wrap">
      <Search :size="16" class="search-icon" />
      <input v-model="search" type="text" class="search-input" :placeholder="source === 'usda' ? 'Search USDA foods (e.g. oatmeal, salmon, quinoa)...' : 'Search foods (e.g. banana, bangus)...'" />
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <!-- USDA -->
    <template v-if="source === 'usda'">
      <p v-if="usdaError" class="form-error">{{ usdaError }}</p>
      <p v-else-if="usdaLoading" class="placeholder-text">Searching USDA…</p>
      <p v-else-if="search.trim().length < 2" class="placeholder-text">Type at least 2 letters to search.</p>
      <p v-else-if="!usdaResults.length" class="empty-text">No USDA foods match "{{ search.trim() }}".</p>
      <div v-else class="item-grid">
        <div v-for="f in usdaResults" :key="f.fdc_id" class="item-card">
          <div class="item-top">
            <span class="category-pill usda-pill">USDA · {{ f.data_type }}</span>
          </div>
          <h3 class="item-name">{{ f.name }}</h3>
          <p class="item-measure">Per 100 g · FDC #{{ f.fdc_id }}</p>
          <div class="macro-row">
            <div><span>kcal</span><strong>{{ fmt(f.per_100g.kcal) }}</strong></div>
            <div><span>Carbs</span><strong>{{ fmt(f.per_100g.carbs_g) }} g</strong></div>
            <div><span>Protein</span><strong>{{ fmt(f.per_100g.protein_g) }} g</strong></div>
            <div><span>Fat</span><strong>{{ fmt(f.per_100g.fat_g) }} g</strong></div>
          </div>
          <p class="item-notes">{{ minerals(f.per_100g) }}</p>
        </div>
      </div>
    </template>

    <template v-else>
    <div v-if="categories.length" class="filter-row">
      <div class="category-select-wrap">
        <select v-model="categorySelectValue" class="nm-select category-select">
          <option value="all">All Categories</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
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
    </template>
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

// <select class="nm-select"> values are always strings — this bridges the "all"/numeric-id
// option values to activeCategory (null or a real category id) so
// filteredItems keeps comparing against item.category.id correctly.
const categorySelectValue = computed({
  get: () => (activeCategory.value === null ? 'all' : String(activeCategory.value)),
  set: (val) => { activeCategory.value = val === 'all' ? null : Number(val) },
})

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

/* ---------- USDA FoodData Central (GET /api/usda/foods/?q=) ---------- */
const source = ref('fnri')
const usdaResults = ref([])
const usdaLoading = ref(false)
const usdaError = ref('')
let usdaTimer = null
let usdaSeq = 0
watch([search, source], () => {
  clearTimeout(usdaTimer)
  if (source.value !== 'usda') return
  const term = search.value.trim()
  usdaError.value = ''
  if (term.length < 2) { usdaResults.value = []; return }
  usdaTimer = setTimeout(async () => {
    const mine = ++usdaSeq
    usdaLoading.value = true
    try {
      const data = await get(`/usda/foods/?q=${encodeURIComponent(term)}`)
      if (mine === usdaSeq) usdaResults.value = data.results
    } catch (e) {
      if (mine === usdaSeq) { usdaResults.value = []; usdaError.value = e?.data?.detail || 'USDA search is unavailable right now.' }
    } finally {
      if (mine === usdaSeq) usdaLoading.value = false
    }
  }, 400)
})
function fmt(v) { return v == null ? '—' : Math.round(v * 10) / 10 }
function minerals(p) {
  const parts = [
    p.fiber_g != null && `Fiber ${fmt(p.fiber_g)} g`, p.sodium_mg != null && `Sodium ${fmt(p.sodium_mg)} mg`,
    p.potassium_mg != null && `Potassium ${fmt(p.potassium_mg)} mg`, p.phosphorus_mg != null && `Phosphorus ${fmt(p.phosphorus_mg)} mg`,
  ].filter(Boolean)
  return parts.join(' · ')
}
</script>

<style scoped>
* { box-sizing: border-box; }

.search-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 40px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.search-wrap { position: relative; margin-bottom: 30px; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: #9aaa9a; }
.search-input {
  width: 100%; max-width: 480px; border: 1px solid #d5dad5; border-radius: 10px; padding: 11px 16px 11px 38px;
  font-size: 0.85rem; font-family: inherit; color: #2a2a2a;
}
.search-input:focus { outline: none; border-color: #D4A017; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.source-tabs { display: inline-flex; gap: 4px; background: #eef1ee; border-radius: 10px; padding: 4px; margin-bottom: 16px; max-width: 100%; }
.source-tab { border: none; background: none; font-family: inherit; font-size: 0.82rem; font-weight: 600; color: #5a6a5a; padding: 8px 14px; border-radius: 8px; cursor: pointer; }
.source-tab.on { background: #fff; color: #1a3a1a; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08); }
.usda-pill { background: #eef1f8; color: #34508a; }
.source-tab .short { display: none; }
.macro-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; background: #f7f9f7; border-radius: 10px; padding: 8px 10px; }
.macro-row span { display: block; font-size: 0.64rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #8a9a8a; }
.macro-row strong { font-size: 0.86rem; color: #1a3a1a; }

.filter-row { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.category-select-wrap { position: relative; }
.category-select { min-width: 200px; }

.safety-group { display: flex; gap: 14px; flex-wrap: wrap; }
.safety-toggle {
  display: flex; align-items: center; gap: 6px; font-size: 0.82rem; color: #4a5a4a;
  cursor: pointer; user-select: none;
}
.safety-toggle input { cursor: pointer; }
.safety-toggle.active { color: #1a3a1a; font-weight: 700; }

.item-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }
.item-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 18px 20px;
  display: flex; flex-direction: column;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.item-card:hover {
  border-color: #1f8f5c;
  box-shadow: 0 4px 14px rgba(31,143,92,0.1);
}
.item-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.category-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.free-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; background: #e6efe0; color: #3a6b3a; }

.item-name { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0 0 2px; overflow-wrap: anywhere; }
.item-local { font-size: 0.85rem; color: #8a9a8a; font-style: italic; margin: 0 0 8px; }
.item-measure { font-size: 0.85rem; color: #4a5a4a; margin: 0 0 12px; }

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

@media (max-width: 1400px) { .item-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 900px) { .item-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } .page-header { flex-direction: column; } }
@media (max-width: 560px) {
  .item-grid { grid-template-columns: minmax(0, 1fr); gap: 12px; }
  .page-header { margin-bottom: 20px; }
  .filter-row { align-items: stretch; }
  .category-select-wrap, .category-select { width: 100%; min-width: 0; }
  .item-card { padding: 16px; }
  .source-tabs { display: flex; }
  .source-tab { flex: 1; padding: 8px 6px; }
  .source-tab .long { display: none; }
  .source-tab .short { display: inline; }
}
</style>
