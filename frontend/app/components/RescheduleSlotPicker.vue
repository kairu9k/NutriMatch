<template>
  <!-- The open times a consultation can move to (scheduling/reschedule.py open_slots), laid out like
       the booking pop-up (RndProfileView.vue, redesigned on feature/NewUI): the month calendar in its
       own card on the left (open days green with their count), the picked day's times grouped
       Morning / Afternoon / Evening on the light green right side. Slots: `left-top` sits above the
       calendar card, the default slot below the times (the note box). -->
  <div class="rs-grid">
    <div class="rs-left">
      <slot name="left-top" />
      <section class="rs-calcard" aria-label="Pick a day">
        <p v-if="loading" class="rs-muted">Loading open times…</p>
        <p v-else-if="error" class="nm-field-error">{{ error }}</p>
        <p v-else-if="!slots.length" class="nm-note plain-note">{{ emptyHint || 'No open times to move to.' }}</p>
        <template v-else>
          <div class="rs-row-head">
            <h3 class="rs-month"><CalendarCheck :size="20" aria-hidden="true" /> {{ monthLabel }}</h3>
            <div class="rs-nav">
              <button type="button" aria-label="Previous month" :disabled="!canBack" @click="shift(-1)"><ChevronLeft :size="18" /></button>
              <button type="button" aria-label="Next month" :disabled="!canForward" @click="shift(1)"><ChevronRight :size="18" /></button>
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
          <p class="cal-legend" aria-hidden="true"><span><i class="lg-open" />Open</span><span><i class="lg-sel" />Picked</span></p>
        </template>
      </section>
    </div>

    <div class="rs-right">
      <section v-if="day" class="rs-section" aria-label="Pick a time">
        <p class="rs-k"><Clock :size="18" aria-hidden="true" /> Open times</p>
        <h3 class="rs-day">{{ dayLabel }}</h3>
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
      <div v-else-if="!loading && slots.length" class="rs-pickday">
        <span class="rs-pickday-ico"><CalendarCheck :size="24" aria-hidden="true" /></span>
        <p>Pick a green day to see its times.</p>
      </div>
      <div v-if="$slots.default" class="rs-extra"><slot /></div>
    </div>
  </div>
</template>

<script setup>
import { CalendarCheck, ChevronLeft, ChevronRight, Clock } from 'lucide-vue-next'

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
/* the redesigned booking pop-up's body (RndProfileView.vue .bk-grid / .bk-calcard / .t-btn), kept in step with it */
.rs-grid { display: grid; grid-template-columns: minmax(0, 1.08fr) minmax(0, 1fr); min-height: 100%; }
.rs-left { min-width: 0; padding: 20px 24px 24px 28px; background: #FFFFFF; }
.rs-right { min-width: 0; padding: 22px 28px 24px; background: #EEF5F0; border-left: 1px solid #E3ECE6; }
.rs-muted { margin: 0; font-size: 14px; color: #6B7D73; }

.rs-calcard { padding: 20px 20px 18px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.rs-row-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.rs-month { display: flex; align-items: center; gap: 12px; margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #0E3A2C; }
.rs-month :deep(svg) { color: #1F5C45; }
.rs-nav { display: flex; gap: 10px; }
.rs-nav button { width: 40px; height: 40px; border: 1.5px solid #DDE6E0; border-radius: 50%; background: #FFFFFF; color: #0E3A2C; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: border-color .15s, background-color .15s; }
.rs-nav button:hover:not(:disabled) { border-color: #0B5640; background: #F1F6F2; }
.rs-nav button:disabled { opacity: .35; cursor: default; }
.rs-nav button:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }

.cal { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 8px; }
.cal-wd { padding: 6px 0; text-align: center; font-size: 13px; font-weight: 700; color: #1F7A4D; }
.cal-cell { min-height: 56px; padding: 2px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; border: none; border-radius: 14px; background: transparent; color: #8A9A91; font-family: inherit; transition: background-color .15s, transform .15s, box-shadow .15s; }
.cal-cell.out { border: none; }
.cal-num { font-size: 16px; font-weight: 500; line-height: 1; font-variant-numeric: lining-nums tabular-nums; }
.cal-note { font-size: 10.5px; font-weight: 600; white-space: nowrap; }
.cal-cell.today .cal-num { text-decoration: underline; text-decoration-color: #EFBF04; text-decoration-thickness: 2px; text-underline-offset: 4px; }
.cal-cell.open { background: #E3F0E7; color: #0E3A2C; cursor: pointer; }
.cal-cell.open .cal-num { font-size: 18px; font-weight: 700; }
.cal-cell.open .cal-note { color: #2E5B49; }
.cal-cell.open:hover:not(.selected) { background: #D4E8DB; transform: translateY(-1px); }
.cal-cell.selected { background: #0B5640; color: #FFFFFF; box-shadow: 0 10px 18px -10px rgba(0, 77, 58, 0.9); }
.cal-cell.selected .cal-note { color: rgba(255, 255, 255, 0.9); }
.cal-cell:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.cal-empty { margin: 10px 0 0; }
.cal-legend { margin: 16px 0 0; display: flex; flex-wrap: wrap; gap: 6px 22px; font-size: 13px; color: #3E5046; }
.cal-legend span { display: inline-flex; align-items: center; gap: 8px; }
.cal-legend i { width: 16px; height: 16px; border-radius: 50%; }
.lg-open { background: #EEF5F0; box-shadow: inset 0 0 0 1.5px #D5E2D9; }
.lg-sel { background: #0B5640; }

.rs-k { margin: 0 0 8px; display: flex; align-items: center; gap: 12px; font-size: 17px; font-weight: 700; color: #0E3A2C; }
.rs-k :deep(svg) { color: #1F5C45; }
.rs-day { margin: 0 0 14px; font-family: 'Playfair Display', Georgia, serif; font-size: 26px; font-weight: 700; color: #0E3A2C; }
.tg { padding: 4px 0 12px; }
.tg-label { display: block; margin-bottom: 10px; font-size: 16px; font-weight: 700; color: #0E3A2C; }
.tg-times { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.t-btn { height: 46px; padding: 0 8px; border: 1px solid #D5E2D9; border-radius: 14px; background: #FFFFFF; color: #10231B; font-family: inherit; font-size: 15px; font-weight: 500; cursor: pointer; font-variant-numeric: tabular-nums; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05); transition: border-color .15s, background-color .15s; }
.t-btn:hover:not(.selected) { border-color: #0B5640; }
.t-btn.selected { background: #0B5640; border-color: #0B5640; color: #FFFFFF; font-weight: 600; box-shadow: 0 10px 18px -12px rgba(0, 77, 58, 0.9); }
.t-btn:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.rs-pickday { min-height: 220px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; text-align: center; color: #3E5046; font-size: 14px; }
.rs-pickday p { margin: 0; max-width: 220px; }
.rs-pickday-ico { width: 56px; height: 56px; border-radius: 50%; background: #FFFFFF; color: #0B5640; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px -14px rgba(0, 77, 58, 0.6); }
.rs-extra { margin-top: 14px; padding-top: 20px; border-top: 1px solid #D9E5DD; }
.rs-section + .rs-extra { margin-top: 2px; }
.rs-extra:empty { display: none; } /* every section inside is v-if'd off (a pending request has no note) */

@media (prefers-reduced-motion: reduce) {
  .cal-cell, .t-btn, .rs-nav button { transition: none; }
  .cal-cell.open:hover:not(.selected) { transform: none; }
}
@media (max-width: 860px) {
  .rs-grid { grid-template-columns: 1fr; }
  .rs-right { border-left: none; border-top: 1px solid #E3ECE6; }
  .rs-pickday { min-height: 0; padding: 4px 0; flex-direction: row; justify-content: flex-start; text-align: left; }
  .rs-pickday-ico { width: 44px; height: 44px; }
}
@media (max-width: 640px) {
  .rs-left, .rs-right { padding: 16px; }
  .rs-calcard { padding: 14px 12px; border-radius: 18px; }
  .rs-month { font-size: 19px; }
  .cal { gap: 4px; }
  .cal-cell { min-height: 46px; border-radius: 12px; }
  .cal-note { font-size: 9.5px; }
  .rs-day { font-size: 21px; }
  .t-btn { height: 44px; font-size: 14px; }
}
</style>
