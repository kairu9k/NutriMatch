<template>
  <!-- The RND rates a client's meal log (PATCH /api/rnd/meal-logs/<id>/review/).
       Clients only log what they ate; the rating is the RND's call and can be changed. -->
  <div class="rate" role="group" :aria-label="`Rate ${label || 'this meal log'}`">
    <button v-for="o in OPTIONS" :key="o.value" type="button" class="rate-btn" :class="[o.value, { on: current === o.value }]"
            :aria-pressed="current === o.value" :disabled="saving" @click="rate(o.value)">
      {{ compact ? o.short : o.label }}
    </button>
    <span v-if="error" class="rate-err" role="alert">{{ error }}</span>
  </div>
</template>

<script setup>
const props = defineProps({
  logId: { type: Number, required: true },
  status: { type: String, default: null },
  label: { type: String, default: '' }, // e.g. "Carla's lunch", for screen readers
  compact: { type: Boolean, default: false },
})
const emit = defineEmits(['rated'])
const { patch } = useApi()

const OPTIONS = [
  { value: 'followed', label: 'Followed', short: 'Followed' },
  { value: 'partially_followed', label: 'Partly followed', short: 'Partly' },
  { value: 'not_followed', label: 'Not followed', short: 'Not followed' },
]
const current = ref(props.status)
watch(() => props.status, (v) => { current.value = v })
const saving = ref(false)
const error = ref('')

async function rate(value) {
  if (value === current.value) return
  saving.value = true
  error.value = ''
  try {
    const log = await patch(`/rnd/meal-logs/${props.logId}/review/`, { status: value })
    current.value = log.status
    emit('rated', log)
  } catch (e) {
    error.value = apiError(e, 'Could not save the rating.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.rate { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.rate-btn { border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 16px; padding: 5px 12px; font-family: inherit; font-size: 0.76rem; font-weight: 600; cursor: pointer; }
.rate-btn:hover:not(:disabled) { border-color: #1a3a1a; }
.rate-btn:disabled { opacity: 0.6; cursor: wait; }
.rate-btn.followed.on { background: #e3f3ea; border-color: #1f8f5c; color: #1f8f5c; }
.rate-btn.partially_followed.on { background: #fdf1d6; border-color: #b8860b; color: #8a6508; }
.rate-btn.not_followed.on { background: #fbe1de; border-color: #c0483a; color: #c0483a; }
.rate-err { font-size: 0.74rem; color: #c0392b; flex-basis: 100%; }
</style>
