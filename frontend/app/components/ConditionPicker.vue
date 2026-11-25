<template>
  <div class="cond-picker">
    <div class="chip-grid" role="group" :aria-label="label">
      <label v-for="c in CONDITIONS" :key="c" class="choice-chip" :class="{ checked: listed.includes(c) }">
        <input type="checkbox" :checked="listed.includes(c)" @change="toggle(c)" />
        {{ c }}
      </label>
      <label class="choice-chip" :class="{ checked: otherOn }">
        <input type="checkbox" :checked="otherOn" @change="toggleOther" />
        Other
      </label>
      <label class="choice-chip" :class="{ checked: none }">
        <input type="checkbox" :checked="none" @change="toggleNone" />
        None / not sure
      </label>
    </div>

    <div v-if="otherOn" class="cond-other">
      <label :for="otherId" class="cond-other-label">Your other conditions</label>
      <input :id="otherId" v-model="otherText" type="text" maxlength="200" autocomplete="off" placeholder="For example, High cholesterol, Gout" @blur="touched = true"
             :class="{ invalid: showError }" :aria-invalid="showError ? 'true' : 'false'" />
      <span v-if="showError" class="cond-error">{{ error }}</span>
      <span v-else class="cond-hint">Separate more than one with commas.</span>
    </div>
    <p v-if="none" class="cond-hint">Your RND can add a condition later if one is found.</p>
  </div>
</template>

<script setup>
// A client's health conditions (2026-11-23, adviser: more than one is allowed).
// Pick any of the list, type others under Other (comma separated), or None / not
// sure, which stands alone. v-model: the conditions; v-model:none: "None" ticked
// (so a form can tell "answered none" from "not answered"); v-model:error: why the
// typed ones aren't valid yet ('' = fine). Same rules as the API (profiles/conditions.py).
import { computed, ref, watch } from 'vue'

const CONDITIONS = ['Hypertension', 'Type 2 Diabetes', 'Obesity management', 'Renal nutrition']

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  none: { type: Boolean, default: false },
  label: { type: String, default: 'Health conditions' },
})
const emit = defineEmits(['update:modelValue', 'update:none', 'update:error'])

const otherId = `cond-other-${Math.random().toString(36).slice(2, 8)}`
const known = v => CONDITIONS.find(c => c.toLowerCase() === String(v || '').trim().toLowerCase())
const listed = ref(props.modelValue.map(known).filter(Boolean))
const typedStart = props.modelValue.filter(v => !known(v))
const otherOn = ref(typedStart.length > 0)
const otherText = ref(typedStart.join(', '))
const none = ref(props.none && !props.modelValue.length)
const touched = ref(false)

function toggle(c) {
  const i = listed.value.indexOf(c)
  if (i >= 0) listed.value.splice(i, 1)
  else { listed.value.push(c); none.value = false }
}
function toggleOther() {
  if (otherOn.value) { otherOn.value = false; otherText.value = ''; touched.value = false }
  else { otherOn.value = true; none.value = false }
}
function toggleNone() {
  none.value = !none.value
  if (none.value) { listed.value = []; otherOn.value = false; otherText.value = ''; touched.value = false }
}

const typed = computed(() => otherText.value.split(',').map(s => s.replace(/\s+/g, ' ').trim()).filter(Boolean))
const error = computed(() => {
  if (!otherOn.value) return ''
  if (!typed.value.length) return 'Type your condition, or untick Other.'
  const bad = typed.value.find(t => t.length < 2 || t.length > 100 || !/^[A-Za-zÀ-ÿÑñ0-9][A-Za-zÀ-ÿÑñ0-9 .'&/()+-]*$/.test(t))
  if (bad) return `"${bad.slice(0, 40)}" isn't a condition we can save. Use letters and numbers.`
  return ''
})
const showError = computed(() => !!error.value && (touched.value || typed.value.length > 0))
const picks = computed(() => {
  const out = [...listed.value]
  for (const t of otherOn.value ? typed.value : []) {
    const k = known(t) || t
    if (!out.some(o => o.toLowerCase() === k.toLowerCase())) out.push(k)
  }
  return out
})
watch(picks, v => emit('update:modelValue', v), { immediate: true })
watch(none, v => emit('update:none', v), { immediate: true })
watch(error, e => emit('update:error', e), { immediate: true })
</script>

<style scoped>
.cond-picker { display: flex; flex-direction: column; gap: 8px; }
.cond-hint { margin: 0; font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; }
.chip-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.choice-chip {
  display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 0 13px; border: 1.5px solid #d9e3dc; border-radius: 999px;
  background: #fff; color: #4a5a4a; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.choice-chip input { width: 16px; height: 16px; flex-shrink: 0; accent-color: #0a4a37; margin: 0; }
.choice-chip.checked { border-color: #0a4a37; background: #e3efe7; color: #0a4a37; }
.cond-other { display: flex; flex-direction: column; gap: 6px; }
.cond-other-label { font-size: 0.82rem; font-weight: 600; color: #1a3a1a; }
.cond-other input { width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 13px; font-size: 0.9rem; font-family: inherit; color: #1a3a1a; background: #fff; }
.cond-other input:focus { outline: none; border-color: #1a3a1a; }
.cond-other input.invalid { border-color: #c0392b; }
.cond-error { font-size: 0.78rem; color: #c0392b; }
</style>
