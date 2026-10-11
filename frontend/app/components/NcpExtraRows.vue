<template>
  <div class="extra">
    <div class="extra-head">
      <span class="field-label">Other measurements</span>
      <button v-if="!readOnly && rows.length < 30" type="button" class="nm-panel-link add" @click="add"><Plus :size="13" /> Add</button>
    </div>
    <p v-if="!rows.length" class="field-hint">{{ readOnly ? 'None recorded.' : empty }}</p>
    <div v-if="rows.length" class="extra-cols" aria-hidden="true"><span>Measurement</span><span>Value</span><span>Unit</span><span /></div>
    <div v-for="(row, idx) in rows" :key="idx" class="extra-row-wrap">
      <div class="extra-row">
        <div class="combo">
          <input :value="row.label" class="nm-input" :class="{ bad: errs[idx].label }" placeholder="Search or type" maxlength="100" :disabled="readOnly"
                 :aria-label="`Measurement ${idx + 1} name`" autocomplete="off" role="combobox" :aria-expanded="openIdx === idx"
                 @focus="openIdx = idx" @blur="closeSoon" @input="row.label = $event.target.value; openIdx = idx"
                 @keydown.esc="openIdx = null" />
          <div v-if="openIdx === idx && !readOnly && matches(row.label).length" class="combo-list" role="listbox">
            <template v-for="g in matches(row.label)" :key="g.group">
              <p class="combo-group">{{ g.group }}</p>
              <button v-for="[name, unit] in g.items" :key="name" type="button" role="option" class="combo-opt" @mousedown.prevent="pick(row, name, unit)">
                {{ name }}<span v-if="unit" class="opt-unit">{{ unit }}</span>
              </button>
            </template>
          </div>
        </div>
        <input :value="row.value" class="nm-input" :class="{ bad: errs[idx].value }" inputmode="decimal" placeholder="0" maxlength="10" :disabled="readOnly"
               :aria-label="`Measurement ${idx + 1} value`" @input="onValue(row, $event)" />
        <input :value="row.unit" class="nm-input" :class="{ bad: errs[idx].unit }" placeholder="cm" maxlength="30" :disabled="readOnly"
               :aria-label="`Measurement ${idx + 1} unit`" @input="onUnit(row, $event)" />
        <button v-if="!readOnly" type="button" class="row-x" :aria-label="`Remove measurement ${idx + 1}`" @click="rows.splice(idx, 1)"><X :size="14" /></button>
      </div>
      <p v-if="errs[idx].label || errs[idx].value || errs[idx].unit" class="row-err">
        {{ [errs[idx].label, errs[idx].value, errs[idx].unit].filter(Boolean).join(' · ') }}
      </p>
    </div>
  </div>
</template>

<script setup>
// "Other measurements" rows on the NCP form: a name (picked from common
// measurements like the PES problem, or typed), a number and a unit
// (letters, % and / only). Rows are edited in place on the parent's array.
import { Plus, X } from 'lucide-vue-next'
import { cleanUnit, extraRowErrors } from '~/utils/ncp'

const props = defineProps({
  rows: { type: Array, required: true },
  templates: { type: Array, default: () => [] },
  readOnly: { type: Boolean, default: false },
  empty: { type: String, default: '' },
})

const openIdx = ref(null)
const errs = computed(() => props.rows.map(extraRowErrors))

function add() {
  props.rows.push({ label: '', value: '', unit: '' })
  openIdx.value = props.rows.length - 1
}
function matches(q) {
  const s = String(q || '').trim().toLowerCase()
  return props.templates
    .map(g => ({ group: g.group, items: g.items.filter(([n]) => !s || n.toLowerCase().includes(s)) }))
    .filter(g => g.items.length && !(g.items.length === 1 && g.items[0][0].toLowerCase() === s))
}
function pick(row, name, unit) {
  row.label = name
  if (!row.unit) row.unit = unit
  openIdx.value = null
}
function closeSoon() { setTimeout(() => { openIdx.value = null }, 120) }
// Keep only digits and one decimal point as they type (never change the number itself).
function onValue(row, e) {
  let v = e.target.value.replace(/[^\d.]/g, '')
  const dot = v.indexOf('.')
  if (dot !== -1) v = v.slice(0, dot + 1) + v.slice(dot + 1).replace(/\./g, '')
  row.value = v
  if (e.target.value !== v) e.target.value = v
}
function onUnit(row, e) {
  const v = cleanUnit(e.target.value)
  row.unit = v
  if (e.target.value !== v) e.target.value = v
}
</script>

<style scoped>
.extra { border-top: 1px dashed #e3e8e3; padding-top: 12px; margin-top: 4px; }
.extra-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.field-label { font-size: 0.8rem; font-weight: 600; color: #1a3a1a; }
.field-hint { font-size: 0.72rem; color: #8a9a8a; margin: 0; }
.add { display: inline-flex; align-items: center; gap: 3px; }
.extra-cols, .extra-row { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 0.7fr) minmax(0, 0.7fr) 28px; gap: 6px; }
.extra-cols span { font-size: 0.64rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #9aaa9a; }
.extra-row-wrap { margin-top: 6px; }
.nm-input.bad { border-color: #e0a3a3; background: #fffafa; }
.row-err { font-size: 0.72rem; color: #c0392b; margin: 3px 0 0; }
.row-x { border: none; background: none; color: #8a9a8a; cursor: pointer; }
.combo { position: relative; }
.combo-list { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; width: max(100%, 280px); max-height: 240px; overflow-y: auto; background: #fff; border: 1px solid #d5dad5; border-radius: 10px; box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12); padding: 6px; }
.combo-group { font-size: 0.64rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; margin: 6px 8px 2px; }
.combo-opt { display: flex; justify-content: space-between; gap: 10px; width: 100%; text-align: left; border: none; background: none; padding: 7px 8px; border-radius: 6px; font-family: inherit; font-size: 0.84rem; color: #1a3a1a; cursor: pointer; }
.combo-opt:hover { background: #eef3ec; }
.opt-unit { color: #8a9a8a; font-size: 0.76rem; }
@media (max-width: 560px) {
  .extra-cols { display: none; }
  .extra-row { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 28px; }
  .extra-row .combo { grid-column: 1 / -1; }
}
</style>
