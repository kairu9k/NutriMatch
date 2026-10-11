<template>
  <div class="nm-modal-overlay" @click.self="emit('close')">
    <div class="nm-modal usda" role="dialog" aria-modal="true" aria-labelledby="usda-title">
      <div class="head">
        <div>
          <h3 id="usda-title" class="nm-modal-title">Add a USDA food</h3>
          <p class="nm-modal-text">USDA FoodData Central, for foods the FNRI list doesn't have. Values are per 100 g.<template v-if="mealLabel"> Adding to <strong>{{ mealLabel }}</strong>.</template></p>
        </div>
        <button type="button" class="icon-x" aria-label="Close" @click="emit('close')"><X :size="18" /></button>
      </div>

      <template v-if="!picked">
        <div class="search">
          <Search :size="15" class="search-icon" />
          <input ref="box" v-model="q" class="nm-input" type="search" placeholder="e.g. oatmeal, salmon, quinoa" maxlength="100" aria-label="Search USDA foods" @input="onType" />
        </div>
        <p v-if="error" class="nm-error">{{ error }}</p>
        <p v-else-if="loading" class="nm-muted">Searching USDA…</p>
        <p v-else-if="q.trim().length >= 2 && searched && !results.length" class="nm-muted">No USDA foods match "{{ q.trim() }}".</p>
        <ul v-if="results.length" class="results">
          <li v-for="f in results" :key="f.fdc_id">
            <button type="button" class="result" @click="pick(f)">
              <span class="r-name">{{ f.name }}</span>
              <span class="r-meta">
                <span class="tag">{{ TYPE_LABEL[f.data_type] || f.data_type }}</span>
                {{ val(f.per_100g.kcal) }} kcal · C {{ val(f.per_100g.carbs_g) }} g · P {{ val(f.per_100g.protein_g) }} g · F {{ val(f.per_100g.fat_g) }} g
              </span>
            </button>
          </li>
        </ul>
      </template>

      <template v-else>
        <div class="picked">
          <p class="r-name">{{ picked.name }}</p>
          <p class="r-meta">Per 100 g: {{ val(picked.per_100g.kcal) }} kcal · C {{ val(picked.per_100g.carbs_g) }} g · P {{ val(picked.per_100g.protein_g) }} g · F {{ val(picked.per_100g.fat_g) }} g</p>
          <label class="grams">
            <span>Portion (grams)</span>
            <input v-model="grams" class="nm-input" type="number" min="1" max="2000" step="1" />
          </label>
          <p v-if="gramsError" class="nm-error">{{ gramsError }}</p>
          <div v-else class="portion">
            <div><span class="k">kcal</span><strong>{{ val(portion.kcal) }}</strong></div>
            <div><span class="k">Carbs</span><strong>{{ val(portion.carbs_g) }} g</strong></div>
            <div><span class="k">Protein</span><strong>{{ val(portion.protein_g) }} g</strong></div>
            <div><span class="k">Fat</span><strong>{{ val(portion.fat_g) }} g</strong></div>
          </div>
          <p class="nm-hint">Only the food name, its USDA id and the grams are saved with the plan; the numbers are worked out from USDA each time.</p>
        </div>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="picked = null">Back to results</button>
          <button type="button" class="nm-btn-dark" :disabled="!!gramsError" @click="add">Add food</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
// Search USDA FoodData Central (GET /api/usda/foods/?q=) and add a food by
// grams. Emits `pick` with { fdcId, name, grams, per100 } — the caller keeps
// per100 only in memory to show the portion's numbers.
import { Search, X } from 'lucide-vue-next'
import { usdaPortion } from '~/utils/usda'

defineProps({ mealLabel: { type: String, default: '' } })
const emit = defineEmits(['close', 'pick'])
const { get } = useApi()

const TYPE_LABEL = { 'Foundation': 'Foundation', 'SR Legacy': 'SR Legacy', 'Survey (FNDDS)': 'FNDDS' }
const q = ref('')
const results = ref([])
const loading = ref(false)
const searched = ref(false)
const error = ref('')
const picked = ref(null)
const grams = ref(100)
const box = ref(null)
onMounted(() => box.value?.focus())

let timer = null
let seq = 0
function onType() {
  clearTimeout(timer)
  error.value = ''
  const term = q.value.trim()
  if (term.length < 2) { results.value = []; searched.value = false; return }
  timer = setTimeout(async () => {
    const mine = ++seq
    loading.value = true
    try {
      const data = await get(`/usda/foods/?q=${encodeURIComponent(term)}`)
      if (mine === seq) results.value = data.results
    } catch (e) {
      if (mine === seq) { results.value = []; error.value = e?.data?.detail || 'USDA search is unavailable right now.' }
    } finally {
      if (mine === seq) { loading.value = false; searched.value = true }
    }
  }, 400)
}

function pick(f) {
  picked.value = f
  grams.value = 100
}
const gramsError = computed(() => {
  const g = Number(grams.value)
  return !Number.isFinite(g) || g < 1 || g > 2000 ? 'Enter 1 to 2,000 grams.' : ''
})
const portion = computed(() => usdaPortion(picked.value?.per_100g, grams.value))
function add() {
  emit('pick', { fdcId: picked.value.fdc_id, name: picked.value.name, grams: Number(grams.value), per100: picked.value.per_100g })
}
function val(v) { return v == null ? '—' : Math.round(v * 10) / 10 }
</script>

<style scoped>
.usda { max-width: 560px; }
.head { display: flex; justify-content: space-between; gap: 12px; }
.icon-x { border: none; background: none; color: #6a7a6a; cursor: pointer; align-self: flex-start; }
.search { position: relative; margin-bottom: 10px; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #8a9a8a; }
.search .nm-input { padding-left: 34px; width: 100%; }
.results { list-style: none; margin: 0; padding: 0; max-height: 360px; overflow-y: auto; border: 1px solid #e8ece8; border-radius: 10px; }
.results li + li { border-top: 1px solid #f0f2f0; }
.result { display: flex; flex-direction: column; gap: 3px; width: 100%; text-align: left; border: none; background: none; padding: 10px 12px; cursor: pointer; font-family: inherit; }
.result:hover { background: #f4f8f4; }
.r-name { font-size: 0.86rem; font-weight: 600; color: #1a3a1a; margin: 0; }
.r-meta { font-size: 0.74rem; color: #6a7a6a; margin: 0; }
.tag { display: inline-block; font-size: 0.64rem; font-weight: 700; background: #eef1f8; color: #34508a; border-radius: 6px; padding: 1px 6px; margin-right: 6px; }
.picked { display: flex; flex-direction: column; gap: 8px; }
.grams { display: flex; flex-direction: column; gap: 4px; font-size: 0.8rem; font-weight: 600; color: #1a3a1a; max-width: 200px; margin-top: 6px; }
.portion { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; background: #f7f9f7; border: 1px solid #e8ece8; border-radius: 10px; padding: 10px 12px; }
.portion .k { display: block; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #8a9a8a; }
.portion strong { font-size: 0.95rem; }
@media (max-width: 520px) {
  .portion { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .nm-modal-actions { flex-direction: column-reverse; }
}
</style>
