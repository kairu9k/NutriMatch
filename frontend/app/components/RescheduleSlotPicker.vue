<template>
  <!-- The RND's open times this consultation can move to (next 14 days,
       at least 2 hours ahead), from GET /appointments/<id>/reschedule/slots/. -->
  <div class="rs-picker">
    <p v-if="loading" class="nm-muted">Loading open times…</p>
    <p v-else-if="error" class="nm-field-error">{{ error }}</p>
    <p v-else-if="!days.length" class="nm-note plain-note">No open times in the next 14 days. {{ emptyHint }}</p>
    <template v-else>
      <p class="rs-k">Day</p>
      <div class="rs-days" role="listbox" aria-label="Day">
        <button v-for="d in days" :key="d.key" type="button" class="rs-day" :class="{ on: day === d.key }"
                role="option" :aria-selected="day === d.key" @click="day = d.key">
          <span class="rs-wd">{{ d.weekday }}</span><span class="rs-dt">{{ d.date }}</span>
        </button>
      </div>
      <p class="rs-k">Time</p>
      <div class="rs-times" role="listbox" aria-label="Time">
        <button v-for="t in timesOfDay" :key="t.iso" type="button" class="rs-time" :class="{ on: modelValue === t.iso }"
                role="option" :aria-selected="modelValue === t.iso" @click="emit('update:modelValue', t.iso)">
          {{ t.label }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
const props = defineProps({
  appointmentId: { type: [Number, String], required: true },
  modelValue: { type: String, default: '' },
  emptyHint: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])
const { get } = useApi()

const PH = { timeZone: 'Asia/Manila' }
const slots = ref([])
const loading = ref(true)
const error = ref('')
const day = ref('')

onMounted(async () => {
  try {
    slots.value = (await get(`/appointments/${props.appointmentId}/reschedule/slots/`)).slots || []
    day.value = days.value[0]?.key || ''
  } catch (e) {
    error.value = apiError(e, 'Could not load the open times.')
  } finally {
    loading.value = false
  }
})

const days = computed(() => {
  const out = []
  for (const iso of slots.value) {
    const key = new Date(iso).toLocaleDateString('en-CA', PH)
    if (!out.some(d => d.key === key)) {
      out.push({
        key,
        weekday: new Date(iso).toLocaleDateString('en-PH', { ...PH, weekday: 'short' }),
        date: new Date(iso).toLocaleDateString('en-PH', { ...PH, month: 'short', day: 'numeric' }),
      })
    }
  }
  return out
})
const timesOfDay = computed(() => slots.value
  .filter(iso => new Date(iso).toLocaleDateString('en-CA', PH) === day.value)
  .map(iso => ({ iso, label: new Date(iso).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' }) })))
</script>

<style scoped>
.rs-k { font-size: 0.8rem; font-weight: 600; color: #1a3a1a; margin: 12px 0 6px; }
.rs-k:first-child { margin-top: 0; }
.rs-days { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 4px; }
.rs-day { flex: 0 0 auto; display: flex; flex-direction: column; align-items: center; min-width: 58px; padding: 7px 8px; border-radius: 10px;
  border: 1px solid #d9e3dc; background: #fff; color: #1a3a1a; font-family: inherit; cursor: pointer; }
.rs-wd { font-size: 0.7rem; color: #6a7a6a; }
.rs-dt { font-size: 0.84rem; font-weight: 700; }
.rs-times { display: flex; flex-wrap: wrap; gap: 6px; }
.rs-time { height: 36px; padding: 0 12px; border-radius: 8px; border: 1px solid #d9e3dc; background: #fff; color: #1a3a1a;
  font-family: inherit; font-size: 0.84rem; font-weight: 600; cursor: pointer; font-variant-numeric: tabular-nums; }
.rs-day.on, .rs-time.on { background: #0a4a37; border-color: #0a4a37; color: #fff; }
.rs-day.on .rs-wd { color: #cfe3d8; }
.rs-day:focus-visible, .rs-time:focus-visible { outline: 2px solid #0a4a37; outline-offset: 2px; }
</style>
