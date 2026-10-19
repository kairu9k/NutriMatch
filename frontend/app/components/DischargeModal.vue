<template>
  <div class="nm-modal-overlay" @click.self="$emit('close')">
    <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="discharge-title">
      <h2 id="discharge-title" class="nm-modal-title">Discharge {{ patientName }}?</h2>
      <p v-if="checking" class="nm-modal-text">Checking…</p>
      <template v-else-if="blockers.length">
        <p class="nm-modal-text">Before you can end their care:</p>
        <ul class="blockers">
          <li v-for="b in blockers" :key="b">{{ b }}</li>
        </ul>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-dark" @click="$emit('close')">OK</button>
        </div>
      </template>
      <form v-else @submit.prevent="submit">
        <p class="nm-modal-text">
          This ends their care with you. Their active meal plan is archived and your reminders stop. Their records stay
          readable but can't be changed. {{ firstName }} gets a notification and an email with your note, and can book you again later.
        </p>
        <label class="nm-label" for="discharge-reason">Reason / note to the patient</label>
        <textarea id="discharge-reason" v-model="reason" class="nm-input" rows="4" maxlength="1000"
                  placeholder="e.g. Reached the target weight and is maintaining it well."></textarea>
        <p v-if="error" class="nm-field-error">{{ error }}</p>
        <p v-else class="nm-hint">At least 10 characters.</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="$emit('close')">Cancel</button>
          <button type="submit" class="nm-btn-danger solid" :disabled="saving || reason.trim().length < 10">
            {{ saving ? 'Discharging…' : 'Discharge patient' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  relationshipId: { type: [String, Number], required: true },
  patientName: { type: String, default: 'this patient' },
  // Pre-filled when the client asked to end care (the RND adds a closing note).
  initialReason: { type: String, default: '' },
})
const emit = defineEmits(['close', 'discharged'])
const { get, post } = useApi()

const firstName = computed(() => props.patientName.split(' ')[0])
const checking = ref(true)
const blockers = ref([])
const reason = ref(props.initialReason)
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    blockers.value = (await get(`/rnd/relationships/${props.relationshipId}/discharge/`)).blockers || []
  } catch (e) {
    blockers.value = [apiError(e, 'Could not check this patient right now.')]
  } finally {
    checking.value = false
  }
})

async function submit() {
  saving.value = true
  error.value = ''
  try {
    const res = await post(`/rnd/relationships/${props.relationshipId}/discharge/`, { reason: reason.value.trim() })
    emit('discharged', res)
  } catch (e) {
    error.value = apiError(e, 'Could not discharge this patient.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.blockers { margin: 0 0 4px; padding-left: 18px; font-size: 0.86rem; color: #1a3a1a; line-height: 1.7; }
</style>
