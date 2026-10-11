<template>
  <div ref="root" class="diet">
    <div class="diet-head">
      <span class="field-label">Dietary intake</span>
      <span class="field-hint">Optional · collected during the assessment and used to plan the intervention</span>
    </div>

    <div class="diet-tabs" role="tablist" aria-label="Dietary intake tools">
      <button v-for="t in TABS" :key="t.key" type="button" role="tab" class="diet-tab" :class="{ on: tab === t.key }" :aria-selected="tab === t.key" @click="tab = t.key">
        {{ t.label }}<span v-if="badge(t.key)" class="tab-badge">{{ badge(t.key) }}</span>
      </button>
    </div>

    <!-- 24-HOUR RECALL -->
    <div v-if="tab === 'recall'" class="pane">
      <p class="pane-hint">Ask what they ate and drank <strong>yesterday</strong>, from waking up to bedtime. Pick FNRI foods to count calories by exchange, or type any food.</p>
      <div v-if="totals.foods" class="totals">
        <div><span class="k">Calorie count</span><strong>{{ fmt(totals.kcal) }} kcal</strong></div>
        <div><span class="k">Carbs</span><strong>{{ totals.carbs_g }} g</strong></div>
        <div><span class="k">Protein</span><strong>{{ totals.protein_g }} g</strong></div>
        <div><span class="k">Fat</span><strong>{{ totals.fat_g }} g</strong></div>
        <p class="c-sub">
          {{ totals.foods }} food{{ totals.foods === 1 ? '' : 's' }}<template v-if="totals.foods > totals.counted"> · {{ totals.foods - totals.counted }} not counted (no group or exchanges)</template><template v-if="tdee && totals.kcal"> · {{ Math.round(totals.kcal / tdee * 100) }}% of their TDEE ({{ fmt(Math.round(tdee)) }} kcal)</template>
        </p>
      </div>

      <div v-for="meal in mealsShown" :key="meal.value" class="meal">
        <div class="meal-head">
          <span>{{ meal.label }}</span>
          <button v-if="!readOnly && recall.length < RECALL_MAX_ROWS" type="button" class="nm-panel-link add" @click="addRow(meal.value)"><Plus :size="13" /> Add food</button>
        </div>
        <p v-if="!rowsOf(meal.value).length" class="empty">{{ readOnly ? '—' : 'Nothing yet' }}</p>
        <div v-else class="cols" aria-hidden="true"><span>Food</span><span>Amount</span><span>Exchange group</span><span>Exch.</span><span>kcal</span><span /></div>
        <div v-for="row in rowsOf(meal.value)" :key="row._k" class="row-wrap">
          <div class="row">
            <div class="combo f-food">
              <input :value="row.food_name" :data-k="row._k" class="nm-input" :class="{ bad: rowErr(row).food_name }" placeholder="Search FNRI or type" maxlength="120" :disabled="readOnly"
                     aria-label="Food" autocomplete="off" role="combobox" :aria-expanded="openKey === row._k"
                     @focus="openKey = row._k" @blur="closeSoon(row._k)" @input="row.food_name = $event.target.value; openKey = row._k" @keydown.esc="openKey = null" />
              <div v-if="openKey === row._k && !readOnly && matches(row.food_name).length" class="combo-list" role="listbox">
                <template v-for="g in matches(row.food_name)" :key="g.group">
                  <p class="combo-group">{{ g.name }}</p>
                  <button v-for="f in g.items" :key="f.name" type="button" role="option" class="combo-opt" @mousedown.prevent="pick(row, f)">
                    <span>{{ f.name }}</span><span class="opt-unit">{{ f.measure }}</span>
                  </button>
                </template>
              </div>
            </div>
            <input v-model="row.amount" class="nm-input f-amt" placeholder="e.g. 1 cup" maxlength="60" :disabled="readOnly" aria-label="Amount" />
            <select v-model="row.group" class="nm-select f-grp" :disabled="readOnly" aria-label="Exchange group">
              <option value="">Not counted</option>
              <option v-for="v in values" :key="v.code" :value="v.code">{{ v.name }}</option>
            </select>
            <input v-model="row.exchanges" class="nm-input f-exch" :class="{ bad: rowErr(row).exchanges }" inputmode="decimal" placeholder="1" maxlength="4" :disabled="readOnly" aria-label="Exchanges" />
            <span class="kcal">{{ rowKcal(row) }}</span>
            <button v-if="!readOnly" type="button" class="row-x" aria-label="Remove food" @click="removeRow(row)"><X :size="14" /></button>
          </div>
          <p v-if="rowErr(row).food_name || rowErr(row).exchanges" class="row-err">{{ [rowErr(row).food_name, rowErr(row).exchanges].filter(Boolean).join(' · ') }}</p>
        </div>
      </div>
      <p v-if="readOnly && !recall.length" class="empty">No 24-hour recall recorded.</p>
    </div>

    <!-- FOOD FREQUENCY -->
    <div v-else-if="tab === 'ffq'" class="pane">
      <p class="pane-hint">How often do they usually eat each of these? Answers that may need attention are highlighted.</p>
      <div class="ffq">
        <label v-for="g in FFQ_GROUPS" :key="g.value" class="ffq-row" :class="{ flag: ffqFlag(g.value) }">
          <span>{{ g.label }}</span>
          <select :value="ffq[g.value] || ''" class="nm-select" :disabled="readOnly" @change="ffq[g.value] = $event.target.value">
            <option value="">—</option>
            <option v-for="f in FFQ_FREQS" :key="f.value" :value="f.value">{{ f.label }}</option>
          </select>
        </label>
      </div>
    </div>

    <!-- IDDS -->
    <div v-else-if="tab === 'idds'" class="pane">
      <p class="pane-hint">Individual Dietary Diversity Score (FAO): one point for each food group eaten in the last 24 hours.</p>
      <div class="idds-score">
        <strong>{{ idds.length }} / 9</strong>
        <span class="lvl" :class="level?.key">{{ level?.label }}</span>
        <button v-if="!readOnly && suggested.length" type="button" class="nm-btn-outline nm-btn-sm" @click="useRecall">Fill from the 24-hour recall</button>
      </div>
      <div class="idds">
        <label v-for="g in IDDS_GROUPS" :key="g.value" class="idds-row" :class="{ on: idds.includes(g.value) }">
          <input type="checkbox" :checked="idds.includes(g.value)" :disabled="readOnly" @change="toggle(g.value)" />
          <span class="idds-text"><strong>{{ g.label }}</strong><small>{{ g.eg }}</small></span>
          <span v-if="!readOnly && suggested.includes(g.value)" class="in-recall">in recall</span>
        </label>
      </div>
      <p class="c-sub">Cut-offs: 3 or fewer = low, 4–5 = medium, 6 or more = high diversity.</p>
    </div>

    <!-- FOOD DIARY -->
    <div v-else class="pane">
      <p class="pane-hint">The patient's own meal logs for the last 7 days (read-only).</p>
      <p v-if="!diary.length" class="empty">No meal logs in the last 7 days. Patients log meals from their meal plan.</p>
      <div v-for="day in diaryDays" :key="day.date" class="diary-day">
        <p class="diary-date">{{ day.label }}</p>
        <div v-for="(e, n) in day.entries" :key="n" class="diary-row">
          <span class="diary-meal">{{ e.meal }}</span>
          <span class="diary-food">{{ e.planned.join(', ') || 'Planned meal' }}<small v-if="e.notes">“{{ e.notes }}”</small></span>
          <span class="status" :class="e.status">{{ e.status_label }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Dietary intake tools on the NCP Assessment step: 24-hour recall with an FNRI
// exchange calorie count, food frequency questionnaire, IDDS, and the patient's
// food diary (their meal logs). Edits the parent's arrays/object in place, so
// the form's unsaved-changes check sees them. Mirrors backend clinical/dietary.py.
import { Plus, X } from 'lucide-vue-next'
import { FFQ_FREQS, FFQ_GROUPS, IDDS_GROUPS, RECALL_MAX_ROWS, RECALL_MEALS, iddsFromRecall, iddsLevel, recallRowErrors, recallTotals } from '~/utils/ncp'

const props = defineProps({
  recall: { type: Array, required: true },
  ffq: { type: Object, required: true },
  idds: { type: Array, required: true },
  values: { type: Array, default: () => [] }, // FNRI exchange values per group
  foods: { type: Array, default: () => [] }, // FNRI foods
  diary: { type: Array, default: () => [] },
  tdee: { type: Number, default: null },
  readOnly: { type: Boolean, default: false },
})

const TABS = [
  { key: 'recall', label: '24-hour recall' }, { key: 'ffq', label: 'Food frequency' },
  { key: 'idds', label: 'Diversity (IDDS)' }, { key: 'diary', label: 'Food diary' },
]
const tab = ref('recall')
const openKey = ref(null)
const root = ref(null)

let seq = Date.now() // unique across remounts
// Stable v-for keys, non-enumerable so they never reach the saved JSON or the
// form's unsaved-changes snapshot.
function keyOf(row) {
  if (row._k == null) Object.defineProperty(row, '_k', { value: ++seq, enumerable: false })
  return row._k
}
props.recall.forEach(keyOf)

const totals = computed(() => recallTotals(props.recall, props.values))
const mealsShown = computed(() => (props.readOnly ? RECALL_MEALS.filter(m => rowsOf(m.value).length) : RECALL_MEALS))
const rowsOf = meal => props.recall.filter(r => r.meal === meal).map(r => (keyOf(r), r))
const rowErr = row => recallRowErrors(row)
const byCode = computed(() => Object.fromEntries(props.values.map(v => [v.code, v])))
function rowKcal(row) {
  const v = byCode.value[row.group]
  const x = Number(row.exchanges)
  return v && String(row.exchanges ?? '').trim() !== '' && Number.isFinite(x) ? fmt(Math.round(x * v.kcal)) : '—'
}
function badge(key) {
  if (key === 'recall') return totals.value.foods || ''
  if (key === 'ffq') return Object.values(props.ffq).filter(Boolean).length || ''
  if (key === 'idds') return props.idds.length ? `${props.idds.length}/9` : ''
  return props.diary.length || ''
}

function addRow(meal) {
  const row = { meal, food_name: '', amount: '', group: '', exchanges: '' }
  keyOf(row)
  props.recall.push(row)
  openKey.value = row._k
  nextTick(() => root.value?.querySelector(`input[data-k="${row._k}"]`)?.focus())
}
function removeRow(row) {
  const n = props.recall.indexOf(row)
  if (n !== -1) props.recall.splice(n, 1)
}
function matches(q) {
  const s = String(q || '').trim().toLowerCase()
  const hits = props.foods.filter(f => !s || f.name.toLowerCase().includes(s) || (f.local_name || '').toLowerCase().includes(s))
  if (hits.length === 1 && hits[0].name.toLowerCase() === s) return []
  return props.values
    .map(v => ({ group: v.code, name: v.name, items: hits.filter(f => f.group === v.code) }))
    .filter(g => g.items.length)
}
function pick(row, f) {
  row.food_name = f.name
  row.group = f.group
  if (!String(row.amount || '').trim()) row.amount = f.measure || ''
  if (String(row.exchanges ?? '').trim() === '') row.exchanges = '1'
  openKey.value = null
}
function closeSoon(k) { setTimeout(() => { if (openKey.value === k) openKey.value = null }, 120) }

// FFQ answers worth a second look.
const TOO_OFTEN = ['sweet_drinks', 'sweets', 'fried', 'salty_snacks', 'processed_meat', 'alcohol']
const TOO_RARE = ['green_yellow_veg', 'other_veg', 'fruits']
function ffqFlag(group) {
  const v = props.ffq[group]
  return (TOO_OFTEN.includes(group) && ['daily', 'multi'].includes(v)) || (TOO_RARE.includes(group) && ['never', 'monthly'].includes(v))
}

const level = computed(() => iddsLevel(props.idds.length))
const suggested = computed(() => iddsFromRecall(props.recall))
function toggle(g) {
  const n = props.idds.indexOf(g)
  if (n === -1) props.idds.push(g)
  else props.idds.splice(n, 1)
  sortIdds()
}
function useRecall() {
  for (const g of suggested.value) if (!props.idds.includes(g)) props.idds.push(g)
  sortIdds()
}
function sortIdds() {
  const order = IDDS_GROUPS.map(x => x.value)
  props.idds.sort((a, b) => order.indexOf(a) - order.indexOf(b))
}

const diaryDays = computed(() => {
  const days = []
  for (const e of props.diary) {
    let d = days.find(x => x.date === e.date)
    if (!d) {
      d = { date: e.date, label: new Date(`${e.date}T00:00:00`).toLocaleDateString('en-PH', { weekday: 'short', month: 'short', day: 'numeric' }), entries: [] }
      days.push(d)
    }
    d.entries.push(e)
  }
  return days
})

function fmt(n) { return Number(n || 0).toLocaleString('en-PH') }
</script>

<style scoped>
.diet { border-top: 1px dashed #e3e8e3; padding-top: 12px; margin: 4px 0 14px; }
.diet-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; margin-bottom: 8px; }
.field-label { font-size: 0.8rem; font-weight: 600; color: #1a3a1a; }
.field-hint, .c-sub { font-size: 0.72rem; color: #8a9a8a; margin: 0; }
.diet-tabs { display: flex; gap: 4px; flex-wrap: wrap; border-bottom: 1px solid #e8ece8; margin-bottom: 12px; }
.diet-tab { border: none; background: none; font-family: inherit; font-size: 0.82rem; font-weight: 600; color: #6a7a6a; padding: 8px 10px; border-bottom: 2px solid transparent; margin-bottom: -1px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
.diet-tab.on { color: #1a3a1a; border-bottom-color: #1a3a1a; }
.tab-badge { font-size: 0.68rem; background: #eef3ec; color: #1a5a2a; border-radius: 10px; padding: 1px 7px; }
.pane-hint { font-size: 0.78rem; color: #5a6a5a; margin: 0 0 10px; line-height: 1.5; }
.empty { font-size: 0.78rem; color: #9aaa9a; margin: 2px 0 6px; }

.totals { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; background: #f7f9f7; border: 1px solid #e8ece8; border-radius: 10px; padding: 10px 12px; margin-bottom: 12px; }
.totals .k { display: block; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; color: #8a9a8a; }
.totals strong { font-size: 0.95rem; color: #1a3a1a; }
.totals .c-sub { grid-column: 1 / -1; }

.meal { margin-bottom: 12px; }
.meal-head { display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; font-weight: 700; color: #1a3a1a; padding: 6px 0; border-bottom: 1px solid #f0f2f0; margin-bottom: 6px; }
.add { display: inline-flex; align-items: center; gap: 3px; font-weight: 600; }
.cols, .row { display: grid; grid-template-columns: minmax(0, 1.7fr) minmax(0, 0.9fr) minmax(0, 1.2fr) 58px 44px 24px; gap: 6px; align-items: center; }
.cols span { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #9aaa9a; }
.row-wrap { margin-top: 6px; }
.row .nm-select { width: 100%; padding-left: 10px; padding-right: 30px; background-position: right 8px center; }
.kcal { font-size: 0.8rem; color: #4a5a4a; text-align: right; }
.nm-input.bad { border-color: #e0a3a3; background: #fffafa; }
.row-err { font-size: 0.72rem; color: #c0392b; margin: 3px 0 0; }
.row-x { border: none; background: none; color: #8a9a8a; cursor: pointer; padding: 0; }
.combo { position: relative; }
.combo-list { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; width: max(100%, 300px); max-height: 260px; overflow-y: auto; background: #fff; border: 1px solid #d5dad5; border-radius: 10px; box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12); padding: 6px; }
.combo-group { font-size: 0.64rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; margin: 6px 8px 2px; }
.combo-opt { display: flex; justify-content: space-between; gap: 10px; width: 100%; text-align: left; border: none; background: none; padding: 7px 8px; border-radius: 6px; font-family: inherit; font-size: 0.84rem; color: #1a3a1a; cursor: pointer; }
.combo-opt:hover { background: #eef3ec; }
.opt-unit { color: #8a9a8a; font-size: 0.74rem; white-space: nowrap; }

.ffq { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 14px; }
.ffq-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; font-size: 0.8rem; color: #2a3a2a; padding: 4px 6px; border-radius: 8px; }
.ffq-row.flag { background: #fff6e0; }
.ffq-row .nm-select { flex: 0 0 150px; }

.idds-score { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 10px; }
.idds-score strong { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a3a1a; }
.lvl { font-size: 0.74rem; font-weight: 700; padding: 3px 9px; border-radius: 10px; background: #eef1ee; color: #5a6a5a; }
.lvl.low { background: #fdecec; color: #a12525; }
.lvl.medium { background: #fff3d6; color: #8a5a00; }
.lvl.high { background: #e3f4e6; color: #1a6a2a; }
.idds-score .nm-btn-outline { margin-left: auto; }
.idds { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; margin-bottom: 8px; }
.idds-row { display: flex; align-items: flex-start; gap: 8px; border: 1px solid #e8ece8; border-radius: 10px; padding: 8px 10px; cursor: pointer; }
.idds-row.on { border-color: #9ccaa6; background: #f3faf4; }
.idds-row input { margin-top: 3px; accent-color: #1a5a2a; }
.idds-text { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.idds-text strong { font-size: 0.8rem; color: #1a3a1a; font-weight: 600; }
.idds-text small { font-size: 0.72rem; color: #8a9a8a; }
.in-recall { font-size: 0.64rem; font-weight: 700; color: #1a5a2a; background: #e3f4e6; border-radius: 8px; padding: 2px 6px; white-space: nowrap; }

.diary-day { margin-bottom: 10px; }
.diary-date { font-size: 0.74rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.diary-row { display: grid; grid-template-columns: 90px minmax(0, 1fr) auto; gap: 10px; align-items: start; font-size: 0.8rem; padding: 6px 0; border-bottom: 1px solid #f3f5f3; }
.diary-meal { color: #6a7a6a; }
.diary-food { color: #2a3a2a; }
.diary-food small { display: block; color: #8a9a8a; font-style: italic; }
.status { font-size: 0.7rem; font-weight: 700; border-radius: 8px; padding: 2px 8px; white-space: nowrap; }
.status.followed { background: #e3f4e6; color: #1a6a2a; }
.status.partially_followed { background: #fff3d6; color: #8a5a00; }
.status.not_followed { background: #fdecec; color: #a12525; }

@media (max-width: 640px) {
  .totals { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .cols { display: none; }
  .row { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 24px; }
  .row .f-food { grid-area: 1 / 1 / 2 / 3; }
  .row .row-x { grid-area: 1 / 3; }
  .row .f-amt { grid-area: 2 / 1; }
  .row .f-grp { grid-area: 2 / 2 / 3 / 4; }
  .row .f-exch { grid-area: 3 / 1; }
  .row .kcal { grid-area: 3 / 2 / 4 / 4; text-align: left; }
  .ffq, .idds { grid-template-columns: minmax(0, 1fr); }
  .ffq-row .nm-select { flex-basis: 140px; }
  .diary-row { grid-template-columns: minmax(0, 1fr) auto; }
  .diary-meal { grid-column: 1 / -1; font-weight: 600; }
}
</style>
