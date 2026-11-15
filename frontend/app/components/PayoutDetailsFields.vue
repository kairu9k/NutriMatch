<template>
  <div>
    <div class="pd-methods" role="radiogroup" aria-label="Send my earnings by">
      <label class="pd-method" :class="{ on: form.kind === 'ewallet' }"><input v-model="form.kind" type="radio" value="ewallet" /> E-wallet</label>
      <label class="pd-method" :class="{ on: form.kind === 'bank' }"><input v-model="form.kind" type="radio" value="bank" /> Bank transfer</label>
    </div>
    <div class="pd-fields">
      <div v-if="form.kind === 'ewallet'">
        <label class="nm-label" :for="`${uid}-wallet`">E-wallet</label>
        <select :id="`${uid}-wallet`" v-model="form.wallet" class="nm-select block">
          <option v-for="w in WALLETS" :key="w.value" :value="w.value">{{ w.label }}</option>
        </select>
      </div>
      <div v-else>
        <label class="nm-label" :for="`${uid}-bank`">Bank</label>
        <select :id="`${uid}-bank`" v-model="form.bankChoice" class="nm-select block" :class="{ invalid: formErrors.bank_name }">
          <option value="" disabled>Choose your bank</option>
          <option v-for="b in BANKS" :key="b" :value="b">{{ b }}</option>
          <option value="__other">Other bank</option>
        </select>
        <input v-if="form.bankChoice === '__other'" v-model="form.otherBank" class="nm-input pd-other" maxlength="100" placeholder="Name of your bank" aria-label="Name of your bank" />
        <p v-if="formErrors.bank_name" class="nm-field-error">{{ formErrors.bank_name }}</p>
      </div>
      <div>
        <label class="nm-label" :for="`${uid}-name`">Account name</label>
        <input :id="`${uid}-name`" v-model="form.account_name" class="nm-input" maxlength="150" placeholder="Name on the account" />
        <p v-if="formErrors.account_name" class="nm-field-error">{{ formErrors.account_name }}</p>
      </div>
      <div>
        <label class="nm-label" :for="`${uid}-number`">{{ numberLabel }}</label>
        <input :id="`${uid}-number`" :value="form.account_number" class="nm-input" :class="{ invalid: numberMessage }" inputmode="numeric" autocomplete="off"
               :maxlength="numberMax" :placeholder="isMobileWallet(formMethod) ? '09171234567' : 'Digits only'"
               :aria-invalid="!!numberMessage" :aria-describedby="`${uid}-help`" @input="onNumberInput" @blur="numberTouched = true" />
        <p v-if="numberMessage" :id="`${uid}-help`" class="nm-field-error">{{ numberMessage }}</p>
        <p v-else :id="`${uid}-help`" class="nm-hint pd-count">{{ isMobileWallet(formMethod) ? `${form.account_number.length} of 11 digits` : '6 to 20 digits' }}</p>
      </div>
    </div>
    <p v-if="formErrors.detail" class="nm-field-error">{{ formErrors.detail }}</p>
  </div>
</template>

<script setup>
// An RND's payout details: an e-wallet (GCash, Maya, GoTyme, MariBank) or a bank
// from the list / typed in. Same rules as the API: GCash and Maya 09XXXXXXXXX,
// everything else 6 to 20 digits. Used by Earnings and the RND onboarding;
// the parent calls validate(), payload() and setErrors() through the ref.
import { computed, reactive, ref, watch } from 'vue'
import { BANKS, WALLETS, isMobileWallet, payoutVia } from '~/utils/payout'

const props = defineProps({ account: { type: Object, default: null } })
const uid = `pd-${Math.random().toString(36).slice(2, 8)}`

const a = props.account
const isBank = a?.method === 'bank'
const form = reactive({
  kind: isBank ? 'bank' : 'ewallet',
  wallet: !a || isBank ? 'gcash' : a.method,
  bankChoice: isBank ? (BANKS.includes(a.bank_name) ? a.bank_name : '__other') : '',
  otherBank: isBank && !BANKS.includes(a.bank_name) ? a.bank_name || '' : '',
  account_name: a?.account_name || '',
  account_number: a?.account_number || '',
})
const formErrors = reactive({})
const formMethod = computed(() => (form.kind === 'bank' ? 'bank' : form.wallet))
const formBank = computed(() => (form.bankChoice === '__other' ? form.otherBank.trim() : form.bankChoice))

// account number: digits only, capped per method, checked while typing
const numberTouched = ref(false)
const numberMax = computed(() => (isMobileWallet(formMethod.value) ? 11 : 20))
function onNumberInput(ev) {
  const digits = ev.target.value.replace(/\D/g, '').slice(0, numberMax.value)
  form.account_number = digits
  if (ev.target.value !== digits) ev.target.value = digits
  delete formErrors.account_number
}
watch(numberMax, (max) => { form.account_number = form.account_number.slice(0, max) })
const numberError = computed(() => {
  const v = form.account_number
  const name = payoutVia(formMethod.value)
  if (isMobileWallet(formMethod.value)) {
    if (v.length >= 2 && !v.startsWith('09')) return `${name} numbers start with 09.`
    if (numberTouched.value && v.length !== 11) return v ? `Enter the 11-digit ${name} number, e.g. 09171234567.` : `Enter your ${name} number.`
  } else if (numberTouched.value && v.length < 6) {
    return v ? 'Account numbers are 6 to 20 digits.' : 'Enter your account number.'
  }
  return ''
})
const numberMessage = computed(() => formErrors.account_number || numberError.value)
const numberLabel = computed(() => (isMobileWallet(formMethod.value) ? `${payoutVia(formMethod.value)} number` : 'Account number'))

/** True when everything is filled in correctly; otherwise shows what's wrong. */
function validate() {
  for (const k of Object.keys(formErrors)) delete formErrors[k]
  if (!form.account_name.trim()) formErrors.account_name = 'Enter the name on the account.'
  numberTouched.value = true
  if (numberError.value) formErrors.account_number = numberError.value
  if (form.kind === 'bank' && !formBank.value) formErrors.bank_name = form.bankChoice === '__other' ? 'Type the name of your bank.' : 'Choose your bank.'
  return Object.keys(formErrors).length === 0
}
/** Nothing typed at all, for a form that may be left empty (onboarding's "Add later"). */
const isEmpty = () => !form.account_name.trim() && !form.account_number && !formBank.value
const payload = () => ({
  method: formMethod.value, account_name: form.account_name.trim(), account_number: form.account_number.trim(),
  bank_name: form.kind === 'bank' ? formBank.value : '',
})
/** Shows an API error object ({account_name: [...], ...}) next to its fields. */
function setErrors(data, fallback) {
  for (const k of Object.keys(formErrors)) delete formErrors[k]
  for (const k of ['account_name', 'account_number', 'bank_name']) if (data?.[k]) formErrors[k] = Array.isArray(data[k]) ? data[k][0] : data[k]
  if (!Object.keys(formErrors).length && fallback) formErrors.detail = fallback
}
defineExpose({ validate, payload, setErrors, isEmpty })
</script>

<style scoped>
.pd-fields { display: flex; flex-direction: column; gap: 12px; }
.pd-other { margin-top: 8px; }
.pd-count { margin: 4px 0 0; font-variant-numeric: tabular-nums; }
.pd-methods { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.pd-method { display: inline-flex; align-items: center; gap: 8px; border: 1px solid #d5dad5; border-radius: 10px; padding: 9px 14px; font-size: 0.85rem; font-weight: 600; cursor: pointer; }
.pd-method.on { border-color: #1f8f5c; background: #f2f9f4; }
.pd-method input { accent-color: #163a1c; }
</style>
