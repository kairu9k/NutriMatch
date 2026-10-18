<template>
  <div class="combo">
    <input :value="row.label" class="nm-input" :class="[inputClass, { bad }]" placeholder="Search or type" maxlength="100" :disabled="disabled"
           :aria-label="ariaLabel" autocomplete="off" role="combobox" :aria-expanded="open"
           @focus="open = true" @blur="closeSoon" @input="onLabel($event.target.value); open = true"
           @keydown.esc="open = false" />
    <div v-if="open && !disabled && matches.length" class="combo-list" role="listbox">
      <template v-for="g in matches" :key="g.group">
        <p class="combo-group">{{ g.group }}</p>
        <button v-for="[name, unit] in g.items" :key="name" type="button" role="option" class="combo-opt" @mousedown.prevent="pick(name, unit)">
          {{ name }}<span v-if="unit" class="opt-unit">{{ unit }}</span>
        </button>
      </template>
    </div>
  </div>
</template>

<script setup>
// The name box of an "Other measurements" / "Other targets" row: pick a
// common measurement (grouped, with its usual unit) like the PES problem, or
// type any name. Edits row.label / row.unit in place on the parent's row.
const props = defineProps({
  row: { type: Object, required: true },
  templates: { type: Array, default: () => [] },
  disabled: { type: Boolean, default: false },
  bad: { type: Boolean, default: false },
  ariaLabel: { type: String, default: 'Name' },
  inputClass: { type: String, default: '' },
})

const open = ref(false)
const matches = computed(() => {
  const s = String(props.row.label || '').trim().toLowerCase()
  return props.templates
    .map(g => ({ group: g.group, items: g.items.filter(([n]) => !s || n.toLowerCase().includes(s)) }))
    .filter(g => g.items.length && !(g.items.length === 1 && g.items[0][0].toLowerCase() === s))
})
// The unit follows the measurement picked (Hemoglobin → g/dL), replacing a
// unit that was filled in automatically; a unit the RND typed themselves
// (not the usual unit of any listed measurement) is left alone.
const knownUnits = computed(() => new Set(props.templates.flatMap(g => g.items.map(([, u]) => u)).filter(Boolean)))
function applyUnit(unit) {
  if (!props.row.unit || knownUnits.value.has(props.row.unit)) props.row.unit = unit || ''
}
function pick(name, unit) {
  props.row.label = name
  applyUnit(unit)
  open.value = false
}
// Typing a listed name in full (any capitalization) counts as picking it.
function onLabel(value) {
  props.row.label = value
  const s = value.trim().toLowerCase()
  for (const g of props.templates) {
    const hit = g.items.find(([n]) => n.toLowerCase() === s)
    if (hit) {
      props.row.label = hit[0]
      applyUnit(hit[1])
      return
    }
  }
}
function closeSoon() { setTimeout(() => { open.value = false }, 120) }
</script>

<style scoped>
.combo { position: relative; min-width: 0; }
.combo input { width: 100%; }
.nm-input.bad { border-color: #e0a3a3; background: #fffafa; }
.combo-list { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; width: max(100%, 280px); max-height: 240px; overflow-y: auto; background: #fff; border: 1px solid #d5dad5; border-radius: 10px; box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12); padding: 6px; }
.combo-group { font-size: 0.64rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; margin: 6px 8px 2px; }
.combo-opt { display: flex; justify-content: space-between; gap: 10px; width: 100%; text-align: left; border: none; background: none; padding: 7px 8px; border-radius: 6px; font-family: inherit; font-size: 0.84rem; color: #1a3a1a; cursor: pointer; }
.combo-opt:hover { background: #eef3ec; }
.opt-unit { color: #8a9a8a; font-size: 0.76rem; }
</style>
