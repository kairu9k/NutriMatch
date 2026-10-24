<template>
  <div class="nm-modal-overlay" @click.self="emit('close')">
    <div class="nm-modal usda" role="dialog" aria-modal="true" aria-labelledby="usda-title">
      <div class="head nm-modal-head">
        <div>
          <h3 id="usda-title" class="nm-modal-title">Add a USDA food</h3>
          <p class="nm-modal-text">USDA FoodData Central, for foods the FNRI list doesn't have. Values are per 100 g.<template v-if="mealLabel"> Adding to <strong>{{ mealLabel }}</strong>.</template></p>
        </div>
        <button type="button" class="icon-x" aria-label="Close" @click="emit('close')"><X :size="18" /></button>
      </div>

      <template v-if="!picked">
        <div class="search">
          <Search :size="15" class="search-icon" aria-hidden="true" />
          <input ref="box" v-model="q" class="nm-input" type="search" placeholder="e.g. oatmeal, salmon, quinoa" maxlength="100" aria-label="Search USDA foods" @input="onType" />
        </div>
        <p v-if="error" class="nm-error">{{ error }}</p>
        <p v-else-if="loading" class="nm-muted">Searching USDA…</p>
        <p v-else-if="q.trim().length >= 2 && searched && !results.length" class="nm-muted">No USDA foods match "{{ q.trim() }}".</p>
        <ul v-if="results.length" class="results">
          <li v-for="f in results" :key="f.fdc_id">
            <button type="button" class="result" :class="{ allergen: hits(f).length }" @click="pick(f)">
              <span class="r-top">
                <span class="r-name">{{ f.name }}</span>
                <span v-for="w in hits(f)" :key="w" class="allergy-tag"><AlertTriangle :size="12" aria-hidden="true" /> {{ w }}</span>
              </span>
              <span class="r-meta">
                <span class="tag">{{ TYPE_LABEL[f.data_type] || f.data_type }}</span>
                {{ macros(f.per_100g) }}
              </span>
            </button>
          </li>
        </ul>
      </template>

      <template v-else>
        <div class="picked">
          <p class="r-name">{{ picked.name }}</p>
          <div v-if="hits(picked).length" class="allergy-box" role="alert">
            <AlertTriangle :size="16" aria-hidden="true" />
            <p><strong>{{ (patientName || 'This patient').replace(/^./, c => c.toUpperCase()) }} has an allergy this food may match: {{ hits(picked).map(w => w.replace('Allergy: ', '')).join(', ') }}.</strong> Check the food before you add it. It stays flagged in red in the plan.</p>
          </div>
          <p class="r-meta">Per 100 g: {{ macros(picked.per_100g) }}</p>
          <label class="grams">
            <span>Portion (grams)</span>
            <input v-model="grams" class="nm-input" type="number" min="1" max="2000" step="1" />
          </label>
          <p v-if="gramsError" class="nm-error">{{ gramsError }}</p>
          <div v-else class="portion">
            <div><span class="k">Calories</span><strong>{{ val(portion.kcal) }}</strong></div>
            <div><span class="k">Carbs</span><strong>{{ val(portion.carbs_g) }} g</strong></div>
            <div><span class="k">Protein</span><strong>{{ val(portion.protein_g) }} g</strong></div>
            <div><span class="k">Fat</span><strong>{{ val(portion.fat_g) }} g</strong></div>
          </div>
          <p class="nm-hint">Only the food name, its USDA id and the grams are saved with the plan; the numbers are worked out from USDA each time.</p>
        </div>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="picked = null">Back to results</button>
          <button type="button" class="nm-btn-dark" :class="{ 'add-danger': hits(picked).length }" :disabled="!!gramsError" @click="add">{{ hits(picked).length ? 'Add it anyway' : 'Add food' }}</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
// Search USDA FoodData Central (GET /api/usda/foods/?q=) and add a food by
// grams. Emits `pick` with { fdcId, name, grams, per100 } — the caller keeps
// per100 only in memory to show the portion's numbers.
import { AlertTriangle, Search, X } from 'lucide-vue-next'
import { allergyWarnings } from '~/utils/foodWarnings'
import { usdaPortion } from '~/utils/usda'

const props = defineProps({
  mealLabel: { type: String, default: '' },
  // the patient's allergies: matching foods get a red "Allergy: …" tag (same words as the editor)
  allergies: { type: Array, default: () => [] },
  patientName: { type: String, default: '' },
})
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
function val(v) { return v == null ? 'n/a' : Math.round(v * 10) / 10 }
function macros(p) {
  return `${val(p.kcal)} kcal, carbs ${val(p.carbs_g)} g, protein ${val(p.protein_g)} g, fat ${val(p.fat_g)} g`
}
function hits(f) { return f ? allergyWarnings(f.name, props.allergies) : [] }
</script>

<style scoped>
.usda { max-width: 560px; }
.head { display: flex; justify-content: space-between; gap: 12px; }
.icon-x { border: none; background: none; color: #6a7a6a; cursor: pointer; align-self: flex-start; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.icon-x:hover { background: #f2f5f2; }
.search { position: relative; margin-bottom: 10px; }
.search-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); color: #8a9a8a; }
.search .nm-input { padding-left: 34px; width: 100%; }
.results { list-style: none; margin: 0; padding: 0; max-height: 360px; overflow-y: auto; border: 1px solid #d9e3dc; border-radius: 10px; }
.results li + li { border-top: 1px solid #d9e3dc; }
.result { display: flex; flex-direction: column; gap: 3px; width: 100%; text-align: left; border: none; background: none; padding: 10px 12px; cursor: pointer; font-family: inherit; }
.result:hover { background: #f4f7f5; }
.result:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
/* a food that matches the patient's allergy: red, never quiet */
.result.allergen { background: #fdf1ef; box-shadow: inset 3px 0 0 #c0392b; }
.result.allergen:hover { background: #fbe6e2; }
.r-top { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 8px; }
.allergy-tag { display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; font-weight: 700; color: #fff; background: #c0392b; border-radius: 999px; padding: 2px 8px; }
.r-name { font-size: 0.86rem; font-weight: 600; color: #1a3a1a; margin: 0; }
.r-meta { font-size: 0.76rem; color: #4a5a4a; margin: 0; }
.tag { display: inline-block; font-size: 0.7rem; font-weight: 600; background: #e3efe7; color: #1e4a26; border-radius: 6px; padding: 1px 6px; margin-right: 6px; }
.allergy-box { display: flex; gap: 8px; align-items: flex-start; background: #fdf1ef; border: 1.5px solid #c0392b; border-radius: 10px; padding: 10px 12px; color: #8a1f14; }
.allergy-box svg { flex-shrink: 0; margin-top: 2px; color: #c0392b; }
.allergy-box p { margin: 0; font-size: 0.82rem; line-height: 1.45; }
.add-danger { background: #c0392b !important; }
.add-danger:hover { background: #a12f23 !important; }
.picked { display: flex; flex-direction: column; gap: 8px; }
.grams { display: flex; flex-direction: column; gap: 4px; font-size: 0.8rem; font-weight: 600; color: #1a3a1a; max-width: 200px; margin-top: 6px; }
/* this portion's figures: one divided panel */
.portion { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; }
.portion > div { padding: 9px 12px; border-left: 1px solid #d9e3dc; min-width: 0; }
.portion > div:first-child { border-left: none; }
.portion .k { display: block; font-size: 0.74rem; font-weight: 600; color: #4a5a4a; }
.portion strong { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-variant-numeric: tabular-nums lining-nums; }
@media (max-width: 520px) {
  .portion { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .portion > div:nth-child(3) { border-left: none; }
  .portion > div:nth-child(n+3) { border-top: 1px solid #d9e3dc; }
  .nm-modal-actions { flex-direction: column-reverse; }
}
</style>
