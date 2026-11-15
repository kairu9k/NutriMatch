<template>
  <div class="spec-picker">
    <p class="spec-hint">Pick up to {{ MAX }}. If you practise in more areas, choose {{ GENERAL }}.</p>
    <div class="chip-grid" role="group" :aria-label="label">
      <label v-for="sp in SPECIALIZATIONS" :key="sp" class="choice-chip" :class="{ checked: listed.includes(sp), locked: locked(sp) }">
        <input type="checkbox" :checked="listed.includes(sp)" :disabled="locked(sp)" @change="toggle(sp)" />
        {{ sp }}
      </label>
      <label class="choice-chip" :class="{ checked: otherOn, locked: otherLocked }">
        <input type="checkbox" :checked="otherOn" :disabled="otherLocked" @change="toggleOther" />
        Other
      </label>
    </div>

    <div v-if="otherOn" class="spec-other">
      <label :for="otherId" class="spec-other-label">Your specialization</label>
      <input :id="otherId" v-model="otherText" type="text" maxlength="60" autocomplete="off" placeholder="For example, Pediatric Nutrition" @blur="touched = true"
             :class="{ invalid: showError }" :aria-invalid="showError ? 'true' : 'false'" />
      <span v-if="showError" class="spec-error">{{ error }}</span>
      <span v-else class="spec-hint">Letters only, up to 60 characters.</span>
    </div>

    <p v-if="atMax && !listed.includes(GENERAL)" class="nm-note plain-note spec-note">
      <span>You've picked {{ MAX }}. Practise in more areas?</span>
      <button type="button" class="nm-btn-soft nm-btn-sm" @click="useGeneral">Use {{ GENERAL }}</button>
    </p>
    <p v-else-if="listed.includes(GENERAL)" class="nm-note plain-note spec-note">
      <span>{{ GENERAL }} covers every area, so it stands alone. Untick it to pick specific ones.</span>
    </p>
  </div>
</template>

<script setup>
// Up to 3 specializations from the list, one of them may be typed (Other).
// General / Clinical Nutrition is for an RND who covers more areas and stands
// alone. Same rules as the API (profiles/specializations.py).
import { computed, ref, watch } from 'vue'

const GENERAL = 'General / Clinical Nutrition'
const SPECIALIZATIONS = [
  'Diabetes Management',
  'Weight Management',
  'Renal Nutrition',
  'Hypertension & Cardiac Care',
  'Sports Nutrition',
  GENERAL,
]
const MAX = 3

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: { type: String, default: 'Specializations' },
})
// v-model: the picks, typed one included. v-model:error: why they aren't valid yet ('' = fine).
const emit = defineEmits(['update:modelValue', 'update:error'])

const otherId = `spec-other-${Math.random().toString(36).slice(2, 8)}`
const typedFromProps = props.modelValue.find(v => !SPECIALIZATIONS.some(sp => sp.toLowerCase() === v.toLowerCase()))
const listed = ref(props.modelValue.filter(v => SPECIALIZATIONS.includes(v)))
const otherOn = ref(!!typedFromProps)
const otherText = ref(typedFromProps || '')

// the error waits until they've typed something or left the box
const touched = ref(false)
// Typing keeps only letters (and space . ' & / -) and capitalizes each word, like names do.
const tidy = v => v.replace(/[^A-Za-zÀ-ÿÑñ .'&/-]/g, '').replace(/\s{2,}/g, ' ').replace(/(^|[ \/-])([a-zà-ÿñ])/g, (_, a, b) => a + b.toUpperCase())
watch(otherText, v => { const t = tidy(v); if (t !== v) otherText.value = t })
const typed = computed(() => otherText.value.replace(/\s+/g, ' ').trim())
const count = computed(() => listed.value.length + (otherOn.value ? 1 : 0))
const atMax = computed(() => count.value >= MAX)
const otherLocked = computed(() => !otherOn.value && (atMax.value || listed.value.includes(GENERAL)))
function locked(name) {
  if (listed.value.includes(name) || name === GENERAL) return false // General replaces the others
  return atMax.value || listed.value.includes(GENERAL)
}
function toggle(name) {
  const i = listed.value.indexOf(name)
  if (i >= 0) { listed.value.splice(i, 1); return }
  if (name === GENERAL) { useGeneral(); return }
  if (!atMax.value) listed.value.push(name)
}
function toggleOther() {
  if (otherOn.value) { otherOn.value = false; otherText.value = ''; touched.value = false; return }
  if (!otherLocked.value) otherOn.value = true
}
function useGeneral() {
  listed.value = [GENERAL]
  otherOn.value = false
  otherText.value = ''
}

const error = computed(() => {
  if (!otherOn.value) return ''
  const t = typed.value
  if (!t) return 'Type your specialization, or untick Other.'
  if (t.length < 3 || !/^[A-Za-zÀ-ÿÑñ][A-Za-zÀ-ÿÑñ .'&/-]*$/.test(t)) return 'Use letters only, 3 to 60 characters.'
  if (SPECIALIZATIONS.some(sp => sp.toLowerCase() === t.toLowerCase())) return 'That one is already in the list. Tick it above.'
  return ''
})
const showError = computed(() => !!error.value && (touched.value || !!typed.value))
const picks = computed(() => [...listed.value, ...(otherOn.value && typed.value ? [typed.value] : [])])
watch(picks, v => emit('update:modelValue', v), { immediate: true })
watch(error, e => emit('update:error', e), { immediate: true })
</script>

<style scoped>
.spec-picker { display: flex; flex-direction: column; gap: 8px; }
.spec-hint { margin: 0; font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; }
.chip-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.choice-chip {
  display: inline-flex; align-items: center; gap: 6px; min-height: 36px; padding: 0 13px; border: 1.5px solid #d9e3dc; border-radius: 999px;
  background: #fff; color: #4a5a4a; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.choice-chip input { width: 16px; height: 16px; flex-shrink: 0; accent-color: #0a4a37; margin: 0; }
.choice-chip.checked { border-color: #0a4a37; background: #e3efe7; color: #0a4a37; }
.choice-chip.locked { opacity: 0.5; cursor: not-allowed; }
.choice-chip.locked input { cursor: not-allowed; }
.spec-other { display: flex; flex-direction: column; gap: 6px; }
.spec-other-label { font-size: 0.82rem; font-weight: 600; color: #1a3a1a; }
.spec-other input { width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 13px; font-size: 0.9rem; font-family: inherit; color: #1a3a1a; background: #fff; }
.spec-other input:focus { outline: none; border-color: #1a3a1a; }
.spec-other input.invalid { border-color: #c0392b; }
.spec-error { font-size: 0.78rem; color: #c0392b; }
.spec-note { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin: 2px 0 0; padding: 10px 12px; font-size: 0.84rem; }
</style>
