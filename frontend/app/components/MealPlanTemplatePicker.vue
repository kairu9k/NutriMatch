<template>
  <div class="panel tpl">
    <div class="tpl-head">
      <div>
        <h4 class="tpl-title"><Sparkles :size="16" /> Start from a diet template</h4>
        <p class="tpl-sub">Builds a full week from the FNRI Food Exchange Lists for the condition and calorie target. It's saved as a draft — review and adjust every day before sending.</p>
      </div>
    </div>

    <p v-if="loading" class="tpl-sub">Loading templates…</p>
    <p v-else-if="error" class="tpl-error">{{ error }}</p>
    <template v-else-if="data">
      <div class="tpl-grid" role="radiogroup" aria-label="Diet template">
        <button v-for="t in data.templates" :key="t.key" type="button" role="radio" :aria-checked="picked === t.key"
                class="tpl-card" :class="{ on: picked === t.key }" @click="picked = t.key">
          <span class="tpl-name">{{ t.label }}</span>
          <span class="tpl-desc">{{ t.description }}</span>
          <span class="tpl-split">Carbs {{ t.split.carbs }}% · Protein {{ t.split.protein }}% · Fat {{ t.split.fat }}%</span>
        </button>
      </div>

      <div class="tpl-row">
        <label class="tpl-kcal">
          <span>Calories per day</span>
          <input v-model.number="kcal" type="number" :min="data.min_kcal" :max="data.max_kcal" step="50" />
          <small v-if="kcalError" class="tpl-error">{{ kcalError }}</small>
          <small v-else-if="kcalSource">{{ kcalSource }}</small>
        </label>
        <p v-if="data.allergies.length" class="tpl-allergy"><AlertTriangle :size="14" /> Leaves out foods matching their allergies: {{ data.allergies.join(', ') }}</p>
      </div>

      <div class="tpl-actions">
        <button type="button" class="tpl-btn" :disabled="!picked || !!kcalError || busy" @click="generate">
          {{ busy ? 'Building the week…' : 'Generate draft plan' }}
        </button>
        <span class="tpl-or">or fill in the plan yourself below</span>
      </div>
    </template>
  </div>
</template>

<script setup>
// Meal Plans → new plan: pick a disease-specific template (diabetes,
// hypertension, renal, weight management) and a kcal target; the API builds
// a draft week from the FNRI exchange lists (nutrition/plan_templates.py).
import { AlertTriangle, Sparkles } from 'lucide-vue-next'

const props = defineProps({ relationshipId: { type: [String, Number], required: true } })
const emit = defineEmits(['created'])
const { get, post } = useApi()

const data = ref(null)
const loading = ref(true)
const error = ref('')
const picked = ref(null)
const kcal = ref(null)
const busy = ref(false)


async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await get(`/rnd/relationships/${props.relationshipId}/meal-plan-templates/`)
    kcal.value = data.value.suggested_kcal.value
  } catch {
    error.value = 'Could not load the diet templates.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
watch(() => props.relationshipId, () => { picked.value = null; load() })

const kcalSource = computed(() => {
  const s = data.value?.suggested_kcal
  return s && Number(kcal.value) === s.value ? `From the ${s.source}` : ''
})
const kcalError = computed(() => {
  const k = Number(kcal.value)
  if (!k) return 'Enter a calorie target.'
  if (k < data.value.min_kcal || k > data.value.max_kcal) return `Must be ${data.value.min_kcal}–${data.value.max_kcal} kcal.`
  return ''
})

async function generate() {
  busy.value = true
  error.value = ''
  try {
    const plan = await post(`/rnd/relationships/${props.relationshipId}/meal-plans/from-template/`, { template: picked.value, target_kcal: Number(kcal.value) })
    const label = data.value.templates.find(t => t.key === picked.value)?.label
    emit('created', plan, label)
  } catch (e) {
    error.value = apiError(e, 'Could not build the plan.')
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.tpl { margin-bottom: 16px; }
.tpl-title { display: flex; align-items: center; gap: 6px; font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 4px; }
.tpl-sub { font-size: 0.82rem; color: #6a7a6a; margin: 0 0 12px; line-height: 1.5; }
.tpl-error { color: #c0392b; font-size: 0.78rem; }
.tpl-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.tpl-card { text-align: left; display: flex; flex-direction: column; gap: 6px; background: #fff; border: 1.5px solid #e3e8e3; border-radius: 12px; padding: 12px; font-family: inherit; cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; }
.tpl-card:hover { border-color: #b9cdbf; }
.tpl-card.on { border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.12); background: #f6fbf7; }
.tpl-name { font-weight: 700; font-size: 0.9rem; color: #1a3a1a; }
.tpl-desc { font-size: 0.76rem; color: #5a6a5a; line-height: 1.45; flex: 1; }
.tpl-split { font-size: 0.68rem; font-weight: 700; color: #8a9a8a; letter-spacing: 0.02em; }
.tpl-row { display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap; margin-top: 14px; }
.tpl-kcal { display: flex; flex-direction: column; gap: 4px; font-size: 0.8rem; font-weight: 600; color: #1a3a1a; }
.tpl-kcal input { width: 160px; border: 1px solid #d5dad5; border-radius: 8px; padding: 9px 12px; font-family: inherit; font-size: 0.88rem; }
.tpl-kcal small { font-weight: 500; color: #8a9a8a; font-size: 0.72rem; }
.tpl-allergy { display: flex; align-items: center; gap: 6px; margin: 0; font-size: 0.78rem; font-weight: 600; color: #a12525; background: #fdecec; border-radius: 8px; padding: 8px 10px; }
.tpl-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-top: 14px; }
.tpl-or { font-size: 0.78rem; color: #8a9a8a; }
.tpl-btn { background: #14301a; color: #fff; border: none; border-radius: 8px; padding: 10px 18px; font-family: inherit; font-size: 0.85rem; font-weight: 700; cursor: pointer; }
.tpl-btn:disabled { opacity: 0.45; cursor: not-allowed; }
@media (max-width: 900px) { .tpl-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 480px) {
  .tpl-grid { grid-template-columns: minmax(0, 1fr); }
  .tpl-kcal, .tpl-kcal input { width: 100%; }
}
</style>
