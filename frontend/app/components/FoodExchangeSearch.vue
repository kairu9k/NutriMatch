<template>
  <div class="search-page">
    <section class="fh page-header">
      <img class="fh-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="fh-fade" aria-hidden="true"></span>
      <div class="fh-txt">
        <p class="fh-eyebrow"><span></span>Food exchange search</p>
        <h1 class="fh-title">Find the right food</h1>
        <p class="page-sub">{{ source === 'usda' ? 'Search USDA FoodData Central for foods the FNRI list doesn\'t have. Values are per 100 g.' : 'Search the FNRI Food Exchange List to build evidence-based meal plans.' }}</p>
      </div>
    </section>

    <div class="source-tabs" role="tablist" aria-label="Food source">
      <button type="button" role="tab" class="source-tab" :class="{ on: source === 'fnri' }" :aria-selected="source === 'fnri'" @click="source = 'fnri'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z" /><path d="M4 19.5V21h16" /></svg><span class="long">FNRI Food Exchange List</span><span class="short">FNRI</span></button>
      <button type="button" role="tab" class="source-tab" :class="{ on: source === 'usda' }" :aria-selected="source === 'usda'" @click="source = 'usda'"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></svg><span class="long">USDA FoodData Central</span><span class="short">USDA</span></button>
    </div>

    <!-- search + filters in one card -->
    <section class="flt">
      <div class="flt-row">
        <div class="search-wrap">
          <Search :size="16" class="search-icon" />
          <input v-model="search" type="text" class="search-input" :placeholder="source === 'usda' ? 'Search USDA foods (e.g. oatmeal, salmon, quinoa)...' : 'Search foods (e.g. banana, bangus)...'" />
        </div>
        <label v-if="source !== 'usda' && categories.length" class="category-select-wrap">
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h18l-7 8v6l-4 2v-8z" /></svg>
          <select v-model="categorySelectValue" class="nm-select category-select" aria-label="Food group">
            <option value="all">All food groups</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
        </label>
      </div>
      <div v-if="source !== 'usda' && categories.length" class="filter-row">
        <span class="flt-k">Suits</span>
        <div class="safety-group">
          <label v-for="f in safetyFilters" :key="f.key" class="safety-toggle" :class="{ active: safety[f.key] }">
            <input type="checkbox" v-model="safety[f.key]" />
            <template v-if="f.key === 'ok_for_diabetes'"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" /></svg></template><template v-else-if="f.key === 'ok_for_hypertension'"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7.5-4.6-9.2-9.3C1.7 7.4 3.8 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.2 0 5.3 2.9 4.2 6.2C19.5 15.4 12 20 12 20z" /></svg></template><template v-else><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 16c-3-3-2-9 3-10s8 3 7 7-7 6-10 3z" /></svg></template>
            {{ f.label.replace('Suits ', '').replace(/^./, c => c.toUpperCase()) }}
          </label>
        </div>
      </div>
    </section>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <!-- USDA -->
    <template v-if="source === 'usda'">
      <p v-if="usdaError" class="form-error">{{ usdaError }}</p>
      <p v-else-if="usdaLoading" class="placeholder-text">Searching USDA…</p>
      <p v-else-if="usdaSearching && !usdaResults.length" class="empty-text">No USDA foods match "{{ search.trim() }}".</p>
      <template v-else-if="usdaShown.length">
        <p class="result-count">{{ usdaSearching ? `${usdaResults.length} USDA food${usdaResults.length === 1 ? '' : 's'} for "${search.trim()}"` : 'Common foods not on the FNRI list. Search for anything else.' }}</p>
        <div class="mkey" aria-label="Color key">
          <span class="mkey-k">Color key</span>
          <span class="mk k"><i></i>kcal</span><span class="mk c"><i></i>Carbs</span><span class="mk p"><i></i>Protein</span><span class="mk f"><i></i>Fat</span>
          <span class="mkey-note">Values per 100 g</span>
        </div>
        <div class="item-grid">
          <div v-for="f in usdaShown" :key="f.fdc_id" class="item-card">
            <div class="item-top">
              <span class="category-pill usda-pill"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></svg>USDA, {{ f.data_type }}</span>
            </div>
            <h3 class="item-name">{{ f.name }}</h3>
            <p class="item-measure"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v18M5 7h14M5 7l-3 7a3 3 0 0 0 6 0zM19 7l-3 7a3 3 0 0 0 6 0z" /></svg><span>Per 100 g, FDC {{ f.fdc_id }}</span></p>
            <div class="macro-row">
              <div class="k"><span>kcal</span><strong>{{ fmt(f.per_100g.kcal) }}</strong></div>
              <div class="c"><span>Carbs</span><strong>{{ fmt(f.per_100g.carbs_g) }} g</strong></div>
              <div class="p"><span>Protein</span><strong>{{ fmt(f.per_100g.protein_g) }} g</strong></div>
              <div class="f"><span>Fat</span><strong>{{ fmt(f.per_100g.fat_g) }} g</strong></div>
            </div>
            <p class="item-notes">{{ minerals(f.per_100g) }}</p>
          </div>
        </div>
      </template>
      <p v-else-if="usdaCommonLoading" class="placeholder-text">Loading common foods…</p>
      <p v-else class="placeholder-text">Type at least 2 letters to search.</p>
    </template>

    <template v-else>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="items.length">
      <p v-if="filteredItems.length" class="result-count">
        <b>{{ filteredItems.length === items.length ? `${items.length} foods` : `${filteredItems.length} of ${items.length} foods` }}</b><template v-if="pageCount > 1">, showing {{ (page - 1) * PER_PAGE + 1 }}–{{ Math.min(page * PER_PAGE, filteredItems.length) }}</template>
      </p>
      <div v-if="filteredItems.length" class="mkey" aria-label="Color key">
        <span class="mkey-k">Color key</span>
          <span class="mk k"><i></i>kcal</span><span class="mk c"><i></i>Carbs</span><span class="mk p"><i></i>Protein</span><span class="mk f"><i></i>Fat</span>
          <span class="mkey-note">Values per one exchange</span>
        </div>
      <div v-if="filteredItems.length" class="item-grid">
        <div v-for="item in pagedItems" :key="item.id" class="item-card">
          <div class="item-top">
            <span class="category-pill" :style="{ background: item.category.color + '22', color: item.category.color }">
              <i class="cat-dot" :style="{ background: item.category.color }" aria-hidden="true"></i>{{ item.category.name }}
            </span>
            <span v-if="item.is_free_food" class="free-pill"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg>Free food</span>
          </div>
          <h3 class="item-name">{{ item.name }}</h3>
          <p v-if="item.local_name" class="item-local">{{ item.local_name }}</p>
          <p class="item-measure"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v18M5 7h14M5 7l-3 7a3 3 0 0 0 6 0zM19 7l-3 7a3 3 0 0 0 6 0z" /></svg><span>{{ item.household_measure || 'No household measure' }}<b v-if="item.ep_grams"> {{ grams(item.ep_grams) }} g</b></span></p>
          <div class="macro-row" :title="`One ${item.category.name.toLowerCase()} exchange`">
            <div class="k"><span>kcal</span><strong>{{ fmt(item.category.kcal_per_exchange) }}</strong></div>
            <div class="c"><span>Carbs</span><strong>{{ fmt(item.category.carbs_g ?? 0) }} g</strong></div>
            <div class="p"><span>Protein</span><strong>{{ fmt(item.category.protein_g ?? 0) }} g</strong></div>
            <div class="f"><span>Fat</span><strong>{{ fmt(item.category.fat_g ?? 0) }} g</strong></div>
          </div>

          <div class="flag-row">
            <span v-if="!item.ok_for_diabetes" class="flag-pill warn">Not for diabetes</span>
            <span v-if="!item.ok_for_hypertension" class="flag-pill warn">Not for hypertension</span>
            <span v-if="!item.ok_for_renal" class="flag-pill warn">Not for kidney disease</span>
            <span v-if="item.is_high_sodium" class="flag-pill neutral">High sodium</span>
            <span v-if="item.is_high_potassium" class="flag-pill neutral">High potassium</span>
            <span v-if="item.is_high_fiber" class="flag-pill good">High fiber</span>
            <span v-if="item.is_low_gi" class="flag-pill good">Low GI</span>
          </div>

          <p v-if="item.notes" class="item-notes">{{ item.notes }}</p>
        </div>
      </div>
      <div v-if="pageCount > 1" class="pager">
        <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="page === 1" @click="goPage(page - 1)"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>Previous</button>
        <span class="pager-num">Page <b>{{ page }}</b> of {{ pageCount }}</span>
        <button type="button" class="nm-btn-outline nm-btn-sm next" :disabled="page === pageCount" @click="goPage(page + 1)">Next<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg></button>
      </div>
      <p v-if="!filteredItems.length" class="empty-text">No foods match your search and filters.</p>
      <p class="fine-print"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M12 11v5M12 8h.01" /></svg><span>Values are per exchange, from the FNRI Food Exchange List. "Suits" means FNRI lists it for that condition; check portions and the patient's other conditions.</span></p>
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

// FNRI marks a food as suitable for a condition; "safe" overclaimed that
// (portion and the patient's other conditions still matter).
const safetyFilters = [
  { key: 'ok_for_diabetes', label: 'Suits diabetes' },
  { key: 'ok_for_hypertension', label: 'Suits hypertension' },
  { key: 'ok_for_renal', label: 'Suits kidney disease' },
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

// 24 foods per page (a full 3-column grid); back to page 1 when the filters change.
const PER_PAGE = 24
const page = ref(1)
const pageCount = computed(() => Math.max(1, Math.ceil(filteredItems.value.length / PER_PAGE)))
const pagedItems = computed(() => filteredItems.value.slice((page.value - 1) * PER_PAGE, page.value * PER_PAGE))
watch([search, activeCategory, () => ({ ...safety })], () => { page.value = 1 }, { deep: true })
function goPage(n) {
  page.value = n
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

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
// Before a search the USDA tab shows common foods that aren't on the FNRI
// list (each lookup is cached on the server for 30 days).
// [search, preferred USDA name]: plain reference foods, not dishes like
// "almond butter" or "avocado dressing".
const USDA_COMMON = [
  ['oats rolled dry', 'Cereals, oats, regular and quick'], ['quinoa cooked', 'Quinoa, cooked'],
  ['salmon atlantic raw', 'Fish, salmon, Atlantic'], ['almonds raw', 'Nuts, almonds, whole, raw'],
  ['yogurt greek plain nonfat', 'Yogurt, Greek, plain, nonfat'], ['avocados raw', 'Avocados, raw'],
  ['tofu raw firm', 'Tofu, raw, firm'], ['chia seeds dried', 'Seeds, chia seeds, dried'],
  ['oil olive salad or cooking', 'Oil, olive, salad or cooking'], ['lentils cooked boiled', 'Lentils, mature seeds, cooked, boiled, without salt'],
]
const REFERENCE = ['Foundation', 'SR Legacy']
const pick = (list, name) => list.find(f => f.name.startsWith(name)) || list.find(f => REFERENCE.includes(f.data_type)) || list[0]
const usdaCommon = ref([])
const usdaCommonLoading = ref(false)
const usdaSearching = computed(() => search.value.trim().length >= 2)
const usdaShown = computed(() => (usdaSearching.value ? usdaResults.value : usdaCommon.value))
async function loadUsdaCommon() {
  if (usdaCommon.value.length || usdaCommonLoading.value) return
  usdaCommonLoading.value = true
  // Five at a time: ten parallel first-time lookups made USDA time some out.
  const found = []
  for (let i = 0; i < USDA_COMMON.length; i += 5) {
    found.push(...await Promise.all(USDA_COMMON.slice(i, i + 5).map(([q, name]) =>
      get(`/usda/foods/?q=${encodeURIComponent(q)}`).then(d => pick(d.results, name)).catch(() => null))))
  }
  usdaCommon.value = found.filter(Boolean)
  usdaCommonLoading.value = false
}
watch(source, (v) => { if (v === 'usda') loadUsdaCommon() })

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
function fmt(v) { return v == null ? '—' : Math.round(Number(v) * 10) / 10 }
// "45.00" -> "45", "12.50" -> "12.5"
function grams(v) { return String(Number(v)) }
function minerals(p) {
  const parts = [
    p.fiber_g != null && `Fiber ${fmt(p.fiber_g)} g`, p.sodium_mg != null && `Sodium ${fmt(p.sodium_mg)} mg`,
    p.potassium_mg != null && `Potassium ${fmt(p.potassium_mg)} mg`, p.phosphorus_mg != null && `Phosphorus ${fmt(p.phosphorus_mg)} mg`,
  ].filter(Boolean)
  return parts.join(', ')
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
</script>

<style scoped>
* { box-sizing: border-box; }
.search-page { font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; display: inline-block; }

/* ---------- hero ---------- */
.fh { position: relative; overflow: hidden; display: block; margin-bottom: 18px; padding: 24px 30px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.fh-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.fh-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 52%, rgba(0, 77, 58, 0.85) 72%, rgba(0, 77, 58, 0.6) 100%); }
.fh-txt { position: relative; z-index: 1; max-width: 660px; }
.fh-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.fh-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.fh-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 700; line-height: 1.2; color: #fff; }
.page-sub { margin: 0; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }

/* ---------- source tabs ---------- */
.source-tabs { display: inline-flex; gap: 4px; max-width: 100%; margin-bottom: 14px; padding: 5px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); }
.source-tab { display: inline-flex; align-items: center; gap: 7px; height: 36px; padding: 0 15px; border: none; border-radius: 999px; background: none; font-family: inherit; font-size: 13.5px; font-weight: 500; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.source-tab .ic { color: #8a9a91; }
.source-tab:hover:not(.on) { background: #f1f6f2; }
.source-tab.on { background: #004d3a; color: #fff; font-weight: 600; box-shadow: none; }
.source-tab.on .ic { color: #efbf04; }
.source-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.source-tab .short { display: none; }

/* ---------- search + filters ---------- */
.flt { display: flex; flex-direction: column; gap: 12px; margin-bottom: 18px; padding: 16px; border-radius: 20px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.05), 0 10px 24px -10px rgba(0, 0, 0, 0.12); }
.flt-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.search-wrap { position: relative; flex: 1; min-width: 240px; margin: 0; }
.search-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: #8a9a91; }
.search-input { width: 100%; max-width: none; height: 42px; padding: 0 14px 0 40px; border: 1px solid #d9e0dc; border-radius: 10px; background: #fff; font-family: inherit; font-size: 14px; color: #14261e; }
.search-input::placeholder { color: #8a9a91; }
.search-input:hover { border-color: #c2ccc6; }
.search-input:focus { outline: none; border-color: #004d3a; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.1); }
.category-select-wrap { position: relative; display: flex; align-items: center; gap: 10px; min-width: 220px; height: 42px; padding: 0 14px; border: 1px solid #d9e0dc; border-radius: 10px; background: #fff; color: #1f7a4d; cursor: pointer; }
.category-select-wrap:focus-within { border-color: #004d3a; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.1); }
.category-select { flex: 1; width: auto; min-width: 0 !important; height: 100%; padding: 0 !important; border: none !important; background: transparent !important; box-shadow: none !important; outline: none; appearance: none; -webkit-appearance: none; font-family: inherit; font-size: 14px; font-weight: 600; color: #14261e; cursor: pointer; }
.filter-row { display: flex; align-items: center; gap: 10px; margin: 0; flex-wrap: wrap; }
.flt-k { font-size: 12px; font-weight: 800; color: #8a9a91; }
.safety-group { display: flex; gap: 8px; flex-wrap: wrap; }
.safety-toggle { position: relative; display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 13px; border: 1px solid #d9e0dc; border-radius: 999px; background: #fff; font-size: 13px; font-weight: 600; color: #4a5a52; cursor: pointer; user-select: none; transition: background 0.15s, border-color 0.15s; }
.safety-toggle input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.safety-toggle .ic { color: #8a9a91; }
.safety-toggle:hover { border-color: #9ec4ad; }
.safety-toggle.active { border-color: #004d3a; background: #004d3a; color: #fff; font-weight: 700; }
.safety-toggle.active .ic { color: #efbf04; }
.safety-toggle:focus-within { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.form-error { margin: 0 0 16px; padding: 10px 14px; border: 1px solid #f3b8b8; border-radius: 12px; background: #fdecec; font-size: 13.5px; color: #a12525; }
.placeholder-text { font-size: 14px; color: #8a9a91; }
.result-count { margin: 0 0 12px; font-size: 13.5px; color: #6b7d73; }
.result-count b { color: #0e3a2c; }

/* ---------- cards ---------- */
.item-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.item-card { display: flex; flex-direction: column; padding: 18px 20px; border: 1.5px solid #e3ebe6; border-radius: 20px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.05), 0 10px 24px -10px rgba(0, 0, 0, 0.12); transition: transform 0.15s ease, border-color 0.15s ease; }
.item-card:hover { transform: translateY(-2px); border-color: #9ec4ad; }
.item-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 12px; }
.category-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.cat-dot { width: 7px; height: 7px; border-radius: 50%; }
.usda-pill { background: #eef1fa; color: #2e4a86; }
.free-pill { display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px; border-radius: 999px; background: #fff4d6; color: #8a6500; font-size: 12px; font-weight: 800; }
.item-name { margin: 0; font-family: 'Playfair Display', serif; font-size: 19px; line-height: 1.3; color: #0e3a2c; overflow-wrap: anywhere; }
.item-local { margin: 3px 0 0; font-size: 13px; font-style: italic; color: #8a9a91; }
.item-measure { display: inline-flex; align-items: center; gap: 7px; align-self: flex-start; margin: 12px 0 0; padding: 5px 11px; border-radius: 10px; background: #f7faf8; font-size: 13px; color: #4a5a52; }
.item-measure .ic { color: #1f7a4d; }
.item-measure b { color: #0e3a2c; }
.macro-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 14px 0 12px; padding: 0; background: none; }
.macro-row > div { position: relative; padding: 10px 10px 12px; border-radius: 12px; background: #f7faf8; overflow: hidden; }
.macro-row > div::after { content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 3px; }
.macro-row .k::after { background: #efbf04; }
.macro-row .c::after { background: #1f9d55; }
.macro-row .p::after { background: #3b5ba5; }
.macro-row .f::after { background: #c0392b; }
.macro-row span { display: block; font-size: 11px; font-weight: 700; color: #8a9a91; }
.macro-row strong { font-size: 16px; color: #0e3a2c; font-variant-numeric: tabular-nums; }
.flag-row { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 4px; padding-top: 12px; border-top: 1px dashed #e3ebe6; }
.flag-row:empty { display: none; }
.flag-pill { padding: 3px 9px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.flag-pill.warn { background: #fde2df; color: #b42318; }
.flag-pill.neutral { background: #f3f6f4; color: #4a5a52; }
.flag-pill.good { background: #e3f4ea; color: #1f7a4d; }
.item-notes { margin: 8px 0 0; font-size: 12.5px; line-height: 1.45; color: #8a9a91; }

/* ---------- pager + notes ---------- */
.pager { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 24px; }
.pager .nm-btn-outline { display: inline-flex; align-items: center; gap: 6px; height: 40px; padding: 0 16px; border: 1px solid #dce8e0; border-radius: 12px; background: #fff; font-family: inherit; font-size: 13.5px; font-weight: 800; color: #004d3a; cursor: pointer; }
.pager .nm-btn-outline.next { border: none; background: #004d3a; color: #fff; }
.pager .nm-btn-outline.next .ic { color: #efbf04; }
.pager .nm-btn-outline:disabled { opacity: 0.45; cursor: not-allowed; }
.pager-num { font-size: 13.5px; color: #6b7d73; font-variant-numeric: tabular-nums; }
.pager-num b { color: #0e3a2c; }
.fine-print { display: flex; gap: 10px; max-width: 90ch; margin: 22px 0 0; padding: 12px 14px; border: 1.5px dashed #c9d8cf; border-radius: 14px; font-size: 12.5px; line-height: 1.5; color: #6b7d73; }
.fine-print .ic { margin-top: 1px; color: #8a9a91; }
.empty-state { padding: 60px 20px; border: 1.5px dashed #c9d8cf; border-radius: 20px; background: #fff; text-align: center; }
.empty-icon { width: 56px; height: 56px; margin: 0 auto 16px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: flex; align-items: center; justify-content: center; }
.empty-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 19px; color: #0e3a2c; }
.empty-desc { margin: 0; font-size: 13.5px; color: #6b7d73; }
.empty-text { padding: 20px; font-size: 14px; color: #8a9a91; text-align: center; }

@media (max-width: 1200px) { .item-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 760px) {
  .search-page { padding-bottom: 110px; }
  .fh { padding: 20px 18px; border-radius: 22px; }
  .fh-title { font-size: 24px; }
  .fh-plate { width: 170px; height: 170px; right: -55px; top: 20px; transform: none; }
  .fh-txt { max-width: 80%; }
  .search-wrap, .category-select-wrap { flex: 1 1 100%; min-width: 0; }
  .item-grid { grid-template-columns: minmax(0, 1fr); gap: 12px; }
  .item-card { padding: 16px; }
  .source-tabs { display: flex; width: 100%; border-radius: 16px; }
  .source-tab { flex: 1; justify-content: center; padding: 0 6px; }
  .source-tab .long { display: none; }
  .source-tab .short { display: inline; }
}

/* color key for the macro tiles */
.mkey { display: flex; align-items: center; flex-wrap: wrap; gap: 8px 12px; margin: 0 0 14px; padding: 10px 14px; border-radius: 12px; background: #fff; box-shadow: 0 0 0 1px #eef2ef; }
.mkey-k { font-size: 11.5px; font-weight: 800; color: #8a9a91; }
.mk { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 700; color: #22362c; }
.mk i { width: 16px; height: 4px; border-radius: 2px; }
.mk.k i { background: #efbf04; }
.mk.c i { background: #1f9d55; }
.mk.p i { background: #3b5ba5; }
.mk.f i { background: #c0392b; }
.mkey-note { margin-left: auto; font-size: 12.5px; color: #8a9a91; }
@media (max-width: 760px) { .mkey-note { margin-left: 0; flex-basis: 100%; } }
</style>