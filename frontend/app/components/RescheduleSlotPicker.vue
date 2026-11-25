<template>
  <!-- The open times a consultation can move to (scheduling/reschedule.py open_slots), shown like
       the booking pop-up (RndProfileView.vue): a month calendar with the open days in green and
       their count, then the day's times grouped Morning / Afternoon / Evening (2026-11-23, user's call). -->
  <div class="rs-picker">
    <p v-if="loading" class="rs-muted">Loading open times…</p>
    <p v-else-if="error" class="nm-field-error">{{ error }}</p>
    <p v-else-if="!slots.length" class="nm-note plain-note">{{ emptyHint || 'No open times to move to.' }}</p>
    <template v-else>
      <section class="rs-section" aria-label="Pick a day">
        <div class="rs-row-head">
          <h4 class="rs-h">{{ monthLabel }}</h4>
          <div class="rs-nav">
            <button type="button" aria-label="Previous month" :disabled="!canBack" @click="shift(-1)"><ChevronLeft :size="15" /></button>
            <button type="button" aria-label="Next month" :disabled="!canForward" @click="shift(1)"><ChevronRight :size="15" /></button>
          </div>
        </div>
        <div class="cal">
          <span v-for="d in DAY_HEADERS" :key="d" class="cal-wd" aria-hidden="true">{{ d }}</span>
          <template v-for="cell in cells" :key="cell.key">
            <span v-if="!cell.inMonth" class="cal-cell out" aria-hidden="true" />
            <button
              v-else type="button" class="cal-cell"
              :class="{ open: cell.open, selected: cell.key === day, today: cell.key === todayKey }"
              :disabled="!cell.open" :aria-pressed="cell.key === day" :aria-label="cell.aria"
              @click="pickDay(cell.key)"
            >
              <span class="cal-num">{{ cell.day }}</span>
              <span v-if="cell.open" class="cal-note">{{ cell.open }} open</span>
            </button>
          </template>
        </div>
        <p v-if="!cells.some(c => c.open)" class="nm-note plain-note cal-empty">No open times in {{ monthLabel }}. Try the {{ canForward ? 'next' : 'previous' }} month.</p>
      </section>

      <section v-if="day" class="rs-section" aria-label="Pick a time">
        <h4 class="rs-h">{{ dayLabel }}</h4>
        <div v-for="g in groups" :key="g.label" class="tg">
          <span class="tg-label">{{ g.label }}</span>
          <div class="tg-times">
            <button
              v-for="t in g.items" :key="t.iso" type="button" class="t-btn" :class="{ selected: modelValue === t.iso }"
              :aria-pressed="modelValue === t.iso" @click="emit('update:modelValue', t.iso)"
            >{{ t.label }}</button>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  appointmentId: { type: [Number, String], required: true },
  modelValue: { type: String, default: '' },
  emptyHint: { type: String, default: '' },
})
const emit = defineEmits(['update:modelValue'])
const { get } = useApi()

const PH = { timeZone: 'Asia/Manila' }
const DAY_HEADERS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const slots = ref([])
const loading = ref(true)
const error = ref('')
const day = ref('')
const month = ref('') // 'YYYY-MM' shown

// PH calendar date and hour of a time, whatever the device's time zone
const keyOf = iso => new Date(iso).toLocaleDateString('en-CA', PH)
const hourOf = iso => Number(new Date(iso).toLocaleString('en-US', { ...PH, hour: 'numeric', hourCycle: 'h23' }))
const todayKey = new Date().toLocaleDateString('en-CA', PH)

onMounted(async () => {
  try {
    slots.value = (await get(`/appointments/${props.appointmentId}/reschedule/slots/`)).slots || []
    if (slots.value.length) {
      day.value = keyOf(slots.value[0])
      month.value = day.value.slice(0, 7)
    }
  } catch (e) {
    error.value = apiError(e, 'Could not load the open times.')
  } finally {
    loading.value = false
  }
})

const openByDay = computed(() => {
  const out = {}
  for (const iso of slots.value) (out[keyOf(iso)] ||= []).push(iso)
  return out
})
const months = computed(() => [...new Set(slots.value.map(iso => keyOf(iso).slice(0, 7)))])
const canBack = computed(() => months.value.indexOf(month.value) > 0)
const canForward = computed(() => months.value.indexOf(month.value) < months.value.length - 1)
function shift(delta) {
  const i = months.value.indexOf(month.value) + delta
  if (i < 0 || i >= months.value.length) return
  month.value = months.value[i]
  const first = Object.keys(openByDay.value).sort().find(k => k.startsWith(month.value))
  if (first && !day.value.startsWith(month.value)) pickDay(first)
}
const monthLabel = computed(() => {
  if (!month.value) return ''
  const [y, m] = month.value.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})
const cells = computed(() => {
  if (!month.value) return []
  const [y, m] = month.value.split('-').map(Number)
  const first = new Date(y, m - 1, 1)
  const daysIn = new Date(y, m, 0).getDate()
  const weeks = Math.ceil((first.getDay() + daysIn) / 7)
  const out = []
  for (let i = 0; i < weeks * 7; i++) {
    const d = new Date(y, m - 1, 1 - first.getDay() + i)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
    const open = (openByDay.value[key] || []).length
    const long = d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
    out.push({ key, inMonth: d.getMonth() === m - 1, day: d.getDate(), open, aria: open ? `${long}, ${open} open` : long })
  }
  return out
})
function pickDay(key) {
  if (key === day.value) return
  day.value = key
  if (props.modelValue && keyOf(props.modelValue) !== key) emit('update:modelValue', '')
}
const dayLabel = computed(() => (day.value
  ? new Date(`${day.value}T00:00:00`).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
  : ''))
const groups = computed(() => {
  const g = [
    { label: 'Morning', test: h => h < 12, items: [] },
    { label: 'Afternoon', test: h => h >= 12 && h < 17, items: [] },
    { label: 'Evening', test: h => h >= 17, items: [] },
  ]
  for (const iso of openByDay.value[day.value] || []) {
    g.find(x => x.test(hourOf(iso))).items.push({ iso, label: new Date(iso).toLocaleTimeString('en-US', { ...PH, hour: 'numeric', minute: '2-digit' }) })
  }
  return g.filter(x => x.items.length)
})
</script>

<style scoped>
/* the booking pop-up's calendar (RndProfileView.vue), kept in step with it */
.rs-picker { display: flex; flex-direction: column; }
.rs-muted { margin: 0; font-size: 0.84rem; color: #6a7a6a; }
.rs-section { margin-bottom: 18px; }
.rs-section:last-child { margin-bottom: 4px; }
.rs-h { font-family: 'Playfair Display', serif; font-size: 1rem; font-weight: 700; color: #1a3a1a; margin: 0 0 10px; }
.rs-row-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.rs-nav { display: flex; gap: 5px; margin-bottom: 10px; }
.rs-nav button { width: 30px; height: 30px; border-radius: 8px; border: none; background: #e3efe7; color: #0a4a37; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.rs-nav button:hover:not(:disabled) { background: #d3e6d9; }
.rs-nav button:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.rs-nav button:disabled { opacity: 0.4; cursor: default; }
.cal { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 5px; }
.cal-wd { text-align: center; font-size: 0.76rem; font-weight: 600; color: #6a7a6a; padding-bottom: 2px; }
.cal-cell {
  min-height: 52px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
  border: 1px solid transparent; border-radius: 9px; background: transparent; color: #b5bfb5; font-family: inherit; padding: 4px 2px;
}
.cal-cell.out { border: none; }
.cal-num { font-size: 0.9rem; font-weight: 600; font-variant-numeric: lining-nums tabular-nums; }
.cal-note { font-size: 0.66rem; font-weight: 600; white-space: nowrap; }
.cal-cell.today .cal-num { text-decoration: underline; text-underline-offset: 3px; }
.cal-cell.open { background: #e3efe7; border-color: #cfe3d6; color: #1a3a1a; cursor: pointer; }
.cal-cell.open .cal-note { color: #1f6f46; }
.cal-cell.open:hover:not(.selected) { background: #d3e6d9; border-color: #3f9a6b; }
.cal-cell.selected { background: #0a4a37; border-color: #0a4a37; color: #fff; }
.cal-cell.selected .cal-note { color: #9fd0b4; }
.cal-cell:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.cal-empty { margin: 10px 0 0; }
.tg { display: grid; grid-template-columns: 84px 1fr; gap: 8px 12px; align-items: start; padding: 10px 0; border-top: 1px solid #d9e3dc; }
.tg:first-of-type { border-top: none; padding-top: 0; }
.tg-label { font-size: 0.82rem; font-weight: 600; color: #4a5a4a; padding-top: 9px; }
.tg-times { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.t-btn {
  min-height: 36px; padding: 0 16px; border-radius: 8px; border: 1px solid #b9d4c2; background: #fff; color: #1a3a1a;
  font-family: inherit; font-size: 0.85rem; font-weight: 600; cursor: pointer; font-variant-numeric: tabular-nums;
}
.t-btn:hover:not(.selected) { border-color: #3f9a6b; background: #f2f7f3; }
.t-btn.selected { background: #0a4a37; border-color: #0a4a37; color: #fff; }
.t-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
@media (max-width: 640px) {
  .cal { gap: 3px; }
  .cal-cell { min-height: 46px; }
  .cal-note { font-size: 0.6rem; }
  .tg { grid-template-columns: 1fr; gap: 6px; }
  .tg-label { padding-top: 0; }
}
</style>
