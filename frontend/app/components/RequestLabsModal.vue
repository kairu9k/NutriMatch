<template>
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="!saving && emit('close')">
      <form class="nm-modal rl-modal" role="dialog" aria-modal="true" aria-labelledby="rl-title" @submit.prevent="submit">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="!saving && emit('close')"><X :size="18" aria-hidden="true" /></button>
        <h3 id="rl-title" class="nm-modal-title">Request lab tests</h3>
        <p class="nm-modal-text">
          {{ patientName }} is notified and uploads the results from their dashboard.
          <strong>{{ dueLine }}</strong>
        </p>

        <fieldset class="rl-fieldset">
          <legend class="nm-label">Tests</legend>
          <div class="rl-tests">
            <label v-for="t in tests" :key="t.code" class="rl-check">
              <input v-model="picked" type="checkbox" :value="t.code" /> {{ t.name }}
            </label>
          </div>
          <input v-if="picked.includes('other')" v-model="other" class="nm-input" maxlength="200" placeholder="Name of the other test" aria-label="Other test" />
          <p v-if="errors.tests" class="nm-field-error">{{ errors.tests }}</p>
        </fieldset>

        <label class="nm-label" for="rl-note">Note for the patient <span class="opt">(optional)</span></label>
        <textarea id="rl-note" v-model="note" class="nm-input" rows="3" maxlength="500" placeholder="e.g. Fast for 8–10 hours before the blood test (water is okay)."></textarea>
        <p class="nm-hint">{{ note.length }}/500</p>

        <p v-if="error" class="nm-error" role="alert">{{ error }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" :disabled="saving" @click="emit('close')">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="saving">{{ saving ? 'Sending…' : 'Send request' }}</button>
        </div>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { X } from 'lucide-vue-next'
import { labDayTime } from '~/utils/labs'

// RND: POST /api/rnd/relationships/<id>/labs/. "Needed before" isn't picked —
// it's always the patient's next booked consultation.
const props = defineProps({
  relationshipId: { type: [String, Number], required: true },
  patientName: { type: String, default: 'The patient' },
  tests: { type: Array, required: true },
  nextConsultation: { type: String, default: null },
})
const emit = defineEmits(['close', 'sent'])
const { post } = useApi()

const picked = ref([])
const other = ref('')
const note = ref('')
const errors = ref({})
const error = ref('')
const saving = ref(false)

const dueLine = computed(() => (props.nextConsultation
  ? `Needed before ${labDayTime(props.nextConsultation)} (their next consultation).`
  : 'Needed before their next consultation (none booked yet).'))

async function submit() {
  errors.value = {}
  error.value = ''
  if (!picked.value.length) errors.value.tests = 'Tick at least one test.'
  else if (picked.value.includes('other') && !other.value.trim()) errors.value.tests = 'Type the other test\'s name.'
  if (errors.value.tests) return
  saving.value = true
  try {
    await post(`/rnd/relationships/${props.relationshipId}/labs/`, {
      tests: picked.value, other_tests: other.value.trim(), note: note.value.trim(),
    })
    emit('sent')
  } catch (e) {
    const d = e?.data || {}
    error.value = [].concat(d.tests || d.other_tests || d.note || d.detail || 'Could not send the request.')[0]
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.rl-modal { max-width: 520px; }
.rl-fieldset { border: none; padding: 0; margin: 0 0 14px; }
.rl-tests { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 12px; margin-bottom: 8px; }
.rl-check { display: flex; align-items: center; gap: 8px; font-size: 0.84rem; color: #2a3a2a; cursor: pointer; }
.rl-check input { accent-color: #00382a; width: 16px; height: 16px; }
.opt { font-weight: 400; color: #8a9a8a; }
.nm-hint { text-align: right; margin: 4px 0 0; }
@media (max-width: 480px) { .rl-tests { grid-template-columns: minmax(0, 1fr); } }
</style>
