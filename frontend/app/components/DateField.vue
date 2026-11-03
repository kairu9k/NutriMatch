<template>
  <!-- A date picker on Reka UI's Calendar (2026-11-03, user's call): replaces the
       browser's own <input type="date">, which looks different in every browser.
       v-model is an ISO date string ("1995-03-14"), the same as the native input. -->
  <PopoverRoot v-model:open="open">
    <PopoverTrigger as-child>
      <button
        :id="id" type="button" class="df-trigger" :class="{ invalid, empty: !value, compact }"
        :disabled="disabled" :aria-invalid="invalid || undefined" :aria-label="ariaLabel || undefined"
      >
        <span class="df-text">{{ display || placeholder }}</span>
        <CalendarDays :size="17" class="df-icon" aria-hidden="true" />
      </button>
    </PopoverTrigger>
    <PopoverPortal>
      <PopoverContent class="df-pop" side="bottom" align="start" :side-offset="6" :collision-padding="12">
        <CalendarRoot
          v-slot="{ grid, weekDays }"
          v-model:placeholder="view"
          :model-value="value"
          :min-value="minDate"
          :max-value="maxDate"
          locale="en-US"
          weekday-format="short"
          fixed-weeks
          class="df-cal"
          @update:model-value="pick"
        >
          <CalendarHeader class="df-head">
            <CalendarPrev class="df-nav" aria-label="Previous month"><ChevronLeft :size="16" aria-hidden="true" /></CalendarPrev>
            <!-- month and year jump straight there (a date of birth is decades back) -->
            <div class="df-selects">
              <select class="nm-select df-sel" :value="view.month" aria-label="Month" @change="setMonth(Number($event.target.value))">
                <option v-for="(m, i) in MONTHS" :key="m" :value="i + 1" :disabled="monthOff(view.year, i + 1)">{{ m.slice(0, 3) }}</option>
              </select>
              <select class="nm-select df-sel" :value="view.year" aria-label="Year" @change="setYear(Number($event.target.value))">
                <option v-for="y in years" :key="y" :value="y">{{ y }}</option>
              </select>
            </div>
            <CalendarNext class="df-nav" aria-label="Next month"><ChevronRight :size="16" aria-hidden="true" /></CalendarNext>
          </CalendarHeader>
          <CalendarGrid v-for="month in grid" :key="month.value.toString()" class="df-grid">
            <CalendarGridHead>
              <CalendarGridRow class="df-row">
                <CalendarHeadCell v-for="d in weekDays" :key="d" class="df-wd">{{ d.slice(0, 2) }}</CalendarHeadCell>
              </CalendarGridRow>
            </CalendarGridHead>
            <CalendarGridBody>
              <CalendarGridRow v-for="(week, wi) in month.rows" :key="wi" class="df-row">
                <CalendarCell v-for="d in week" :key="d.toString()" :date="d" class="df-cell">
                  <CalendarCellTrigger :day="d" :month="month.value" class="df-day" />
                </CalendarCell>
              </CalendarGridRow>
            </CalendarGridBody>
          </CalendarGrid>
        </CalendarRoot>
        <!-- optional dates (filters, an end date) can be emptied again -->
        <div v-if="clearable && value" class="df-foot">
          <button type="button" class="df-clear" @click="clear">Clear date</button>
        </div>
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<script setup>
import { parseDate, today } from '@internationalized/date'
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import {
  CalendarCell, CalendarCellTrigger, CalendarGrid, CalendarGridBody, CalendarGridHead, CalendarGridRow,
  CalendarHeadCell, CalendarHeader, CalendarNext, CalendarPrev, CalendarRoot,
  PopoverContent, PopoverPortal, PopoverRoot, PopoverTrigger,
} from 'reka-ui'

const props = defineProps({
  modelValue: { type: String, default: '' },
  min: { type: String, default: '' }, // ISO date, like the native input's min
  max: { type: String, default: '' },
  placeholder: { type: String, default: 'Pick a date' },
  invalid: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  id: { type: String, default: undefined },
  ariaLabel: { type: String, default: '' },
  compact: { type: Boolean, default: false }, // smaller, for filter bars
  clearable: { type: Boolean, default: false }, // shows "Clear date" in the pop-up
})
const emit = defineEmits(['update:modelValue'])

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
const toDate = (s) => { try { return s ? parseDate(String(s).slice(0, 10)) : undefined } catch { return undefined } }
const value = computed(() => toDate(props.modelValue))
const minDate = computed(() => toDate(props.min))
const maxDate = computed(() => toDate(props.max))
const todayPh = today('Asia/Manila')

// The month shown when it opens: the chosen date, else today, kept inside min/max.
function startView() {
  if (value.value) return value.value
  if (maxDate.value && maxDate.value.compare(todayPh) < 0) return maxDate.value
  if (minDate.value && minDate.value.compare(todayPh) > 0) return minDate.value
  return todayPh
}
const view = ref(startView())
const open = ref(false)
watch(open, (o) => { if (o) view.value = startView() })

function pick(d) {
  if (!d) return
  emit('update:modelValue', d.toString())
  open.value = false
}

function clear() {
  emit('update:modelValue', '')
  open.value = false
}

// Year list: newest first, within min/max (default 100 years back to 10 ahead).
const years = computed(() => {
  const hi = maxDate.value ? maxDate.value.year : todayPh.year + 10
  const lo = minDate.value ? minDate.value.year : todayPh.year - 100
  const out = []
  for (let y = hi; y >= lo; y--) out.push(y)
  return out
})
function monthOff(year, month) {
  if (minDate.value && (year < minDate.value.year || (year === minDate.value.year && month < minDate.value.month))) return true
  if (maxDate.value && (year > maxDate.value.year || (year === maxDate.value.year && month > maxDate.value.month))) return true
  return false
}
function clampView(d) {
  if (minDate.value && d.compare(minDate.value) < 0) return minDate.value.set({ day: 1 })
  if (maxDate.value && d.compare(maxDate.value) > 0) return maxDate.value.set({ day: 1 })
  return d
}
function setMonth(m) { view.value = clampView(view.value.set({ month: m, day: 1 })) }
function setYear(y) { view.value = clampView(view.value.set({ year: y, day: 1 })) }

// "March 14, 1995"
const display = computed(() => {
  const d = value.value
  if (!d) return ''
  return `${MONTHS[d.month - 1]} ${d.day}, ${d.year}`
})
</script>

<!-- Not scoped: Reka renders the pop-up at the end of <body> (a portal), where
     scoped styles do not reach. Every class here starts with df-. -->
<style>
/* the field: same size and border as the other inputs */
.df-trigger {
  display: flex; align-items: center; justify-content: space-between; gap: 10px; width: 100%; min-height: 46px;
  padding: 11px 14px; border: 1px solid #d5dad5; border-radius: 8px; background: #fff; color: #1a3a1a;
  font: inherit; font-size: 0.95rem; text-align: left; cursor: pointer;
}
.df-trigger:hover:not(:disabled) { border-color: #b9c8bd; }
.df-trigger:focus-visible, .df-trigger[data-state="open"] { outline: none; border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.15); }
.df-trigger.empty .df-text { color: #8a9a8a; }
.df-trigger.invalid { border-color: #e2a39b; background: #fff8f7; }
.df-trigger:disabled { background: #f4f6f4; color: #6a7a6a; cursor: not-allowed; }
.df-icon { color: #3f6b55; flex-shrink: 0; }
.df-trigger.compact { width: auto; min-width: 158px; min-height: 36px; padding: 6px 10px; font-size: 0.85rem; }
.df-text { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* the pop-up: the booking calendar's look */
.df-pop {
  z-index: 1000; width: 316px; max-width: calc(100vw - 24px); padding: 12px; background: #fff; border-radius: 14px;
  border: 1px solid #d9e3dc; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
}
.df-head { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
.df-selects { display: flex; gap: 6px; flex: 1; min-width: 0; }
.df-sel { flex: 1.3; min-width: 0; min-height: 34px; padding-top: 4px; padding-bottom: 4px; font-size: 0.86rem; }
.df-nav {
  display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; flex-shrink: 0;
  border: none; border-radius: 8px; background: #e3efe7; color: #0a4a37; cursor: pointer;
}
.df-nav:hover:not([data-disabled]) { background: #d3e7da; }
.df-nav[data-disabled] { opacity: 0.4; cursor: not-allowed; }
.df-nav:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.df-grid { width: 100%; border-collapse: collapse; }
.df-row { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 2px; }
.df-wd { padding: 4px 0 6px; font-size: 0.74rem; font-weight: 600; color: #6a7a6a; text-align: center; }
.df-cell { display: flex; justify-content: center; }
.df-day {
  display: flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 9px;
  font-size: 0.86rem; color: #1a3a1a; cursor: pointer; user-select: none;
}
.df-day:hover:not([data-disabled]):not([data-selected]) { background: #e3efe7; }
.df-day[data-today]:not([data-selected]) { box-shadow: inset 0 0 0 1.5px #3f9a6b; font-weight: 700; }
.df-day[data-selected] { background: #0a4a37; color: #fff; font-weight: 700; }
.df-day[data-outside-view] { color: #b5c0b8; }
.df-day[data-disabled], .df-day[data-unavailable] { color: #cdd5cf; cursor: not-allowed; }
.df-day[data-highlighted]:not([data-selected]), .df-day:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.df-foot { display: flex; justify-content: flex-end; margin-top: 8px; padding-top: 8px; border-top: 1px solid #d9e3dc; }
.df-clear {
  min-height: 32px; padding: 0 12px; border: none; border-radius: 8px; background: #e3efe7; color: #0a4a37;
  font: inherit; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.df-clear:hover { background: #d3e7da; }
@media (max-width: 380px) { .df-day { width: 32px; height: 32px; } }
</style>
