<template>
  <!-- The RND recommends a meal plan to a consultation-only patient
       (2026-11-04): the client gets an add-on invoice for the difference
       between the two prices, to pay within 7 days. Used by Meal Planning,
       the patient chart and the consultation room's wrap-up. -->
  <div class="nm-modal-overlay" @click.self="$emit('close')">
    <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="recommend-title">
      <button type="button" class="nm-modal-x" aria-label="Close" @click="$emit('close')"><X :size="18" aria-hidden="true" /></button>
      <h2 id="recommend-title" class="nm-modal-title">Recommend a meal plan to {{ firstName }}?</h2>
      <form @submit.prevent="submit">
        <p class="nm-modal-text">
          {{ firstName }} gets a notification and an email to pay <strong>{{ peso(price) }}</strong> for a 7-day meal plan
          (your meal plan price minus your consultation fee). The offer stays open for 7 days. Once they pay, you're told,
          and you create and send their plan.
        </p>
        <label class="nm-label" for="recommend-note">Note to {{ firstName }} <span class="optional">(optional)</span></label>
        <textarea id="recommend-note" v-model="note" class="nm-input" rows="3" maxlength="500" data-allow-emoji
                  placeholder="e.g. A plan will help you keep your blood sugar steady between visits."></textarea>
        <p v-if="error" class="nm-field-error">{{ error }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="$emit('close')">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="saving">{{ saving ? 'Sending…' : 'Send recommendation' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { X } from 'lucide-vue-next'

const props = defineProps({
  relationshipId: { type: [String, Number], required: true },
  patientName: { type: String, default: '' },
  price: { type: [String, Number], default: 0 },
})
const emit = defineEmits(['close', 'done'])

const { post } = useApi()
const note = ref('')
const saving = ref(false)
const error = ref('')
const firstName = computed(() => (props.patientName || 'the patient').split(' ')[0])
const peso = v => `₱${Number(v || 0).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

async function submit() {
  saving.value = true
  error.value = ''
  try {
    const access = await post(`/rnd/relationships/${props.relationshipId}/meal-plan-offer/`, { note: note.value.trim() })
    emit('done', access)
  } catch (e) {
    error.value = apiError(e, 'Could not send the recommendation. Please try again.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.optional { font-weight: 400; color: #6a7a6a; }
</style>
