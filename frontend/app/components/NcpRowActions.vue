<template>
  <div class="ncp-actions">
    <button type="button" class="act-btn" title="View record" @click="emit('view')">
      <Eye :size="14" /> <span>View</span>
    </button>
    <button
      type="button" class="act-btn" :disabled="!canEdit"
      :title="editHint" @click="emit('edit')"
    >
      <Pencil :size="14" /> <span>Edit</span>
    </button>
    <button
      type="button" class="act-btn danger" :disabled="isFinalized"
      :title="isFinalized ? 'Finalized records are part of the patient\'s history and can\'t be deleted' : 'Delete this draft'"
      @click="confirming = true"
    >
      <Trash2 :size="14" /> <span>Delete</span>
    </button>

    <Teleport to="body">
      <div v-if="confirming" class="nm-modal-overlay" @click.self="busy ? null : (confirming = false)">
        <div class="nm-modal" role="dialog" aria-modal="true" aria-label="Delete NCP record">
          <h3 class="nm-modal-title">Delete this NCP record?</h3>
          <p class="nm-modal-text">
            The unfinished {{ record.is_follow_up ? 'follow-up' : 'initial' }} record<template v-if="patientName"> for <strong>{{ patientName }}</strong></template>
            and everything typed into it will be removed. This can't be undone.
          </p>
          <p v-if="error" class="nm-field-error">{{ error }}</p>
          <div class="nm-modal-actions">
            <button class="nm-btn-outline" :disabled="busy" @click="confirming = false">Keep it</button>
            <button class="nm-btn-danger" :disabled="busy" @click="remove">{{ busy ? 'Deleting…' : 'Delete record' }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { Eye, Pencil, Trash2 } from 'lucide-vue-next'

// Row actions for an NCP record list (NCP Records page + Client Detail tab).
// Only an in-progress draft can be edited or deleted — a finalized record is
// permanent (the API refuses both too).
const props = defineProps({
  record: { type: Object, required: true },
  patientName: { type: String, default: '' },
  // false when the relationship isn't active (Client Detail) — drafts stay viewable
  editable: { type: Boolean, default: true },
})
const emit = defineEmits(['view', 'edit', 'deleted'])

const { del } = useApi()
const isFinalized = computed(() => props.record.status === 'completed')
const canEdit = computed(() => !isFinalized.value && props.editable)
const editHint = computed(() => {
  if (isFinalized.value) return 'Finalized records are locked and can no longer be edited'
  if (!props.editable) return 'This patient is no longer active'
  return 'Continue editing this draft'
})

const confirming = ref(false)
const busy = ref(false)
const error = ref('')
async function remove() {
  busy.value = true
  error.value = ''
  try {
    await del(`/rnd/ncp/${props.record.id}/`)
    confirming.value = false
    emit('deleted', props.record)
  } catch (e) {
    error.value = apiError(e, 'Could not delete this record. Please try again.')
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
.ncp-actions { display: flex; gap: 6px; justify-content: flex-end; white-space: nowrap; }
.act-btn {
  display: inline-flex; align-items: center; gap: 5px; border: 1px solid #d5dad5; background: #fff; color: #1a3a1a;
  border-radius: 7px; padding: 6px 10px; font-size: 0.76rem; font-weight: 600; font-family: inherit; cursor: pointer;
}
.act-btn:hover:not(:disabled) { background: #f4f7f4; border-color: #c7d6ca; }
.act-btn.danger { color: #c0392b; border-color: #f0c9c4; }
.act-btn.danger:hover:not(:disabled) { background: #fdf0ee; }
.act-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
