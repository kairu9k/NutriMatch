<template>
  <div class="phone-field">
    <div class="phone-box" :class="{ invalid: !!shownError, disabled }">
      <!-- The flag is the visible part; a transparent native select sits on
           top of it, so the country list is the browser's own (keyboard,
           type-to-find, phone pickers) like every other dropdown in the app. -->
      <div class="phone-country" :title="`${countryName(country)} (+${dial})`">
        <span :class="['fi', `fi-${country.toLowerCase()}`, 'phone-flag']" aria-hidden="true" />
        <ChevronsUpDown :size="14" class="phone-chevron" aria-hidden="true" />
        <select
          v-model="country"
          class="phone-country-select"
          :disabled="disabled || rnd"
          :aria-label="`Country for ${label}`"
          @change="onCountry"
        >
          <option v-for="c in PHONE_COUNTRIES" :key="c.code" :value="c.code">{{ c.name }} (+{{ c.dial }})</option>
        </select>
      </div>
      <span v-if="!pending" class="phone-dial" aria-hidden="true">+{{ dial }}</span>
      <input
        :id="id"
        ref="inputEl"
        :value="shown"
        type="tel"
        inputmode="tel"
        autocomplete="tel-national"
        class="phone-number"
        :placeholder="placeholder"
        :disabled="disabled"
        :aria-label="`${label}, country code +${dial}`"
        :aria-invalid="!!shownError"
        :aria-describedby="shownError ? `${id}-error` : undefined"
        maxlength="24"
        @input="onInput"
        @blur="touched = true"
      />
    </div>
    <p v-if="shownError" :id="`${id}-error`" class="nm-field-error">{{ shownError }}</p>
  </div>
</template>

<script setup>
// A mobile number from any country, shown the international way:
// [flag ▴▾] +63 917 123 4567. Pick the country from the flag, type the rest
// (a leading 0 is dropped, a pasted +65… switches the country). v-model is
// E.164 (+639171234567), '' when left blank — the field is optional. Typing
// stops at the country's longest mobile number; the rest of the check (valid
// prefix, mobile not a landline) shows once the box loses focus. Parents also
// run phoneError() before saving and can pass a server message via `error`.
import { computed, nextTick, ref, watch } from 'vue'
import { ChevronsUpDown } from 'lucide-vue-next'
import { AsYouType, getCountryCallingCode } from 'libphonenumber-js/max'
import 'flag-icons/css/flag-icons.min.css'
import {
  PHONE_COUNTRIES, countryForCode, countryName, exampleLocal, formatLocal, maxMobileDigits, nationalPrefix, phoneError, rndPhoneError, splitPhone, toE164,
} from '~/utils/phone'

const props = defineProps({
  modelValue: { type: String, default: '' },
  id: { type: String, required: true },
  label: { type: String, default: 'phone number' },
  error: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  // RNDs: Philippine numbers only and required (the country is fixed to PH).
  rnd: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const inputEl = ref(null)
const country = ref('PH')
const digits = ref('') // the number after the country code, digits only
const pending = ref('') // a "+…" being typed whose country code isn't complete yet
const touched = ref(false)
let lastEmitted = null

function fill(value) {
  const parts = splitPhone(value)
  country.value = parts.country
  digits.value = parts.digits
  pending.value = ''
}
fill(props.modelValue)
watch(() => props.modelValue, (value) => {
  if (value !== lastEmitted) { fill(value); touched.value = false }
})

// A message from the parent (its own check on Save, or the API) belongs to
// the number it was about — once the number is edited, the live check takes over.
const errorFor = ref(null)
watch(() => props.error, (message) => {
  errorFor.value = message ? props.modelValue : null
  if (message) touched.value = true
}, { immediate: true })

const dial = computed(() => getCountryCallingCode(country.value))
const shown = computed(() => pending.value || formatLocal(digits.value, country.value))
const placeholder = computed(() => exampleLocal(country.value))
const shownError = computed(() => {
  if (props.error && props.modelValue === errorFor.value) return props.error
  return touched.value ? (props.rnd ? rndPhoneError : phoneError)(props.modelValue) : ''
})

function send() {
  lastEmitted = toE164(digits.value, country.value)
  emit('update:modelValue', lastEmitted)
}

// Puts the caret back after the same number of digits once the text is
// regrouped, so editing in the middle doesn't jump to the end.
function placeCaret(el, digitsBefore) {
  const text = el.value
  let pos = 0
  for (let seen = 0; pos < text.length && seen < digitsBefore; pos++) if (/\d/.test(text[pos])) seen++
  el.setSelectionRange(pos, pos)
}

function onInput(event) {
  const el = event.target
  const raw = el.value
  let next
  let caretDigits = raw.slice(0, el.selectionStart ?? raw.length).replace(/\D/g, '').length
  if (raw.trim().startsWith('+')) {
    // A number typed or pasted with its country code: follow that country.
    const typed = new AsYouType()
    typed.input(raw)
    const code = typed.getCallingCode()
    if (!code) {
      // Still typing the code (+6 on the way to +65): leave it as typed.
      pending.value = `+${raw.replace(/\D/g, '')}`
      el.value = pending.value
      lastEmitted = pending.value.length > 1 ? pending.value : ''
      emit('update:modelValue', lastEmitted)
      return
    }
    if (props.rnd && code !== '63') {
      // RNDs: the country stays the Philippines. Keep the foreign number as
      // typed so the "Use a Philippine mobile number" error explains why.
      pending.value = `+${raw.replace(/\D/g, '')}`
      el.value = pending.value
      lastEmitted = pending.value
      emit('update:modelValue', lastEmitted)
      return
    }
    country.value = typed.getCountry() || (dial.value === code ? country.value : countryForCode(code))
    next = typed.getNationalNumber() || ''
    caretDigits = next.length
  } else {
    next = raw.replace(/\D/g, '')
    const prefix = nationalPrefix(country.value)
    if (prefix && next.startsWith(prefix)) {
      next = next.slice(prefix.length)
      caretDigits = Math.max(0, caretDigits - prefix.length)
    }
  }
  if (next.length > maxMobileDigits(country.value)) {
    // Past this country's longest mobile number: keep what was there.
    el.value = shown.value
    return
  }
  digits.value = next
  pending.value = ''
  el.value = shown.value
  placeCaret(el, caretDigits)
  send()
}

function onCountry() {
  pending.value = ''
  send()
  nextTick(() => inputEl.value?.focus())
}
</script>

<style scoped>
.phone-field { min-width: 0; }
.phone-box {
  display: flex; align-items: center; min-height: 42px;
  border: 1px solid #d5dad5; border-radius: 8px; background: #fff;
  font-size: 0.86rem; color: #2a2a2a;
}
.phone-box:focus-within { border-color: #1a3a1a; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.14); }
.phone-box.invalid { border-color: #c0392b; background: #fffafa; }
.phone-box.disabled { background: #f4f6f4; color: #8a9a8a; }

.phone-country {
  position: relative; display: flex; align-items: center; gap: 6px; align-self: stretch;
  padding: 0 10px 0 12px; border-right: 1px solid #e4e8e4; flex-shrink: 0;
}
.phone-flag { width: 22px; height: 16px; border-radius: 3px; background-size: cover; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.08); }
.phone-chevron { color: #6a7a6a; }
.phone-country-select {
  position: absolute; inset: 0; width: 100%; opacity: 0; cursor: pointer;
  font-size: 0.86rem; /* the open list's text size */
}
.phone-country-select:disabled { cursor: not-allowed; }
.phone-country:has(.phone-country-select:focus-visible) { outline: 2px solid #1a3a1a; outline-offset: -2px; border-radius: 7px 0 0 7px; }

.phone-dial { padding-left: 12px; color: #2a2a2a; font-variant-numeric: tabular-nums; flex-shrink: 0; }
.phone-number {
  flex: 1; min-width: 0; border: none; background: transparent; outline: none;
  padding: 10px 12px 10px 5px; font: inherit; color: inherit; font-variant-numeric: tabular-nums;
}
.phone-number::placeholder { color: #a9b4a9; }
</style>
