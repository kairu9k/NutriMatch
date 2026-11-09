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
      <div v-if="open && sheet" class="df-backdrop" aria-hidden="true" />
      <PopoverContent class="df-pop" :class="{ sheet }" side="bottom" align="start" :side-offset="6" :collision-padding="12">
        <CalendarRoot
          v-slot="{ grid, weekDays }"
          v-model:placeholder="view"
          :model-value="value"
          :min-value="minDate"
          :max-value="maxDate"
          locale="en-US"
          weekday-format="short"
          class="df-cal"
          @update:model-value="pick"
        >
          <CalendarHeader class="df-head" :class="{ 'df-head-years': yearsOpen }">
            <CalendarPrev class="df-nav" aria-label="Previous month"><ChevronLeft :size="16" aria-hidden="true" /></CalendarPrev>
            <!-- year-select (dates of birth, decades back): the title opens a list of years -->
            <button
              v-if="yearSelect" type="button" class="df-month df-month-btn" :aria-expanded="yearsOpen"
              :aria-label="`${monthLabel}. Choose a year`" @click="toggleYears"
            >
              {{ monthLabel }}
              <ChevronDown :size="14" class="df-month-chev" :class="{ open: yearsOpen }" aria-hidden="true" />
            </button>
            <p v-else class="df-month" aria-live="polite">{{ monthLabel }}</p>
            <CalendarNext class="df-nav" aria-label="Next month"><ChevronRight :size="16" aria-hidden="true" /></CalendarNext>
          </CalendarHeader>
          <CalendarGrid v-for="month in grid" v-show="!yearsOpen" :key="month.value.toString()" class="df-grid">
            <CalendarGridHead>
              <CalendarGridRow class="df-row">
                <CalendarHeadCell v-for="d in weekDays" :key="d" class="df-wd">{{ d }}</CalendarHeadCell>
              </CalendarGridRow>
            </CalendarGridHead>
            <CalendarGridBody>
              <CalendarGridRow v-for="(week, wi) in month.rows" :key="wi" class="df-row">
                <CalendarCell v-for="d in week" :key="d.toString()" :date="d" class="df-cell">
                  <CalendarCellTrigger :day="d" :month="month.value" class="df-day" :class="mark(d).cls">
                    <span class="df-num">{{ d.day }}</span>
                    <span v-if="mark(d).note" class="df-note">{{ mark(d).note }}</span>
                  </CalendarCellTrigger>
                </CalendarCell>
              </CalendarGridRow>
            </CalendarGridBody>
          </CalendarGrid>
          <div v-if="yearsOpen" ref="yearList" class="df-years" role="group" aria-label="Year">
            <button
              v-for="y in years" :key="y" type="button" class="df-year" :class="{ on: y === view.year }"
              :aria-pressed="y === view.year" @click="pickYear(y)"
            >{{ y }}</button>
          </div>
        </CalendarRoot>
        <div class="df-foot">
          <p class="df-summary">{{ summary }}</p>
          <!-- optional dates (filters, an end date) can be emptied again -->
          <div class="df-actions">
            <button v-if="clearable && value" type="button" class="nm-btn-soft nm-btn-sm" @click="clear">Clear</button>
            <button v-if="sheet" type="button" class="nm-btn-dark nm-btn-sm" @click="open = false">Done</button>
          </div>
        </div>
      </PopoverContent>
    </PopoverPortal>
  </PopoverRoot>
</template>

<script setup>
import { parseDate, today } from '@internationalized/date'
import { CalendarDays, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-vue-next'
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
  clearable: { type: Boolean, default: false }, // shows "Clear" in the pop-up
  yearSelect: { type: Boolean, default: false }, // the title opens a list of years (dates of birth)
  hint: { type: String, default: '' }, // the line under the calendar before a day is picked
  // Block time off only: iso -> true when there are working hours that day
  isWorkingDay: { type: Function, default: null },
  // Block time off only: existing time off [{ start_date, end_date, whole_day }]
  blocks: { type: Array, default: () => [] },
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
  // a date of birth is decades back: start nearer to it than the newest allowed date
  if (props.yearSelect) return clampView(todayPh.subtract({ years: 30 }))
  if (maxDate.value && maxDate.value.compare(todayPh) < 0) return maxDate.value
  if (minDate.value && minDate.value.compare(todayPh) > 0) return minDate.value
  return todayPh
}
const view = ref(startView())
const open = ref(false)
// Phones get a sheet from the bottom of the screen instead of a pop-over.
const sheet = ref(false)
watch(open, (o) => {
  if (!o) return
  yearsOpen.value = false
  view.value = startView()
  sheet.value = window.matchMedia('(max-width: 640px)').matches
})

function pick(d) {
  if (!d) { open.value = false; return } // the day already picked: keep it and close
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
function clampView(d) {
  if (minDate.value && d.compare(minDate.value) < 0) return minDate.value.set({ day: 1 })
  if (maxDate.value && d.compare(maxDate.value) > 0) return maxDate.value.set({ day: 1 })
  return d
}

// The list of years opens at the year on show, inside its own scroll area.
const yearsOpen = ref(false)
const yearList = ref(null)
async function toggleYears() {
  yearsOpen.value = !yearsOpen.value
  if (!yearsOpen.value) return
  await nextTick()
  const box = yearList.value
  const current = box?.querySelector('[aria-pressed="true"]')
  if (!current) return
  box.scrollTop = current.offsetTop - box.clientHeight / 2 + current.offsetHeight / 2
  current.focus({ preventScroll: true })
}
function pickYear(y) {
  view.value = clampView(view.value.set({ year: y, day: 1 }))
  yearsOpen.value = false
}

const monthLabel = computed(() => `${MONTHS[view.value.month - 1]} ${view.value.year}`)

// A label under the day number (Block time off): existing time off, or no hours.
const NO_MARK = { note: '', cls: '' }
function mark(d) {
  const iso = d.toString()
  if ((props.min && iso < props.min) || (props.max && iso > props.max)) return NO_MARK
  const hits = props.blocks.filter(b => b.start_date <= iso && iso <= (b.end_date || b.start_date))
  if (hits.some(b => b.whole_day)) return { note: 'Day off', cls: 'off' }
  if (hits.length) return { note: 'Part off', cls: 'part' }
  if (props.isWorkingDay && !props.isWorkingDay(iso)) return { note: 'No hours', cls: 'idle' }
  return NO_MARK
}

// The line under the calendar: "Monday, November 9, 2026", or what to do.
const summary = computed(() => {
  if (yearsOpen.value) return 'Pick a year.'
  const d = value.value
  if (!d) return props.hint || 'Pick a day.'
  return new Date(Date.UTC(d.year, d.month - 1, d.day))
    .toLocaleDateString('en-US', { timeZone: 'UTC', weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
})

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

/* the pop-up: the calendar look the team picked (2026-11-09) */
.df-pop {
  z-index: 1200; width: 332px; max-width: calc(100vw - 24px); padding: 12px; background: #fff; border-radius: 14px;
  color: #1a3a1a; font-family: 'Inter', sans-serif;
  box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
}
.df-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
.df-month { margin: 0; font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1rem; }
.df-month-btn {
  display: inline-flex; align-items: center; gap: 4px; padding: 5px 8px; border: none; border-radius: 8px;
  background: none; color: inherit; cursor: pointer;
}
.df-month-btn:hover, .df-month-btn[aria-expanded="true"] { background: #e3efe7; }
.df-month-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.df-month-chev { color: #3f6b55; }
.df-month-chev.open { transform: rotate(180deg); }
.df-head-years .df-nav { visibility: hidden; }
.df-nav {
  display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; flex-shrink: 0;
  border: none; border-radius: 8px; background: #e3efe7; color: #0a4a37; cursor: pointer;
}
.df-nav:hover:not([data-disabled]) { background: #d3e6d9; }
.df-nav[data-disabled] { opacity: 0.4; cursor: not-allowed; }
.df-nav:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.df-grid, .df-grid thead, .df-grid tbody { display: block; width: 100%; }
.df-row { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 3px; margin-bottom: 3px; }
.df-wd { padding: 0 0 2px; font-size: 0.72rem; font-weight: 600; color: #6a7a6a; text-align: center; }
.df-cell { display: block; min-width: 0; padding: 0; }
.df-day {
  box-sizing: border-box; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
  width: 100%; min-height: 40px; padding: 2px; border: 1px solid transparent; border-radius: 8px;
  background: #f7faf8; color: #1a3a1a; cursor: pointer; user-select: none;
}
.df-num { font-size: 0.86rem; font-weight: 600; font-variant-numeric: lining-nums tabular-nums; }
.df-note { font-size: 0.56rem; font-weight: 600; white-space: nowrap; color: #6a7a6a; }
.df-day:hover:not([data-disabled]):not([data-selected]) { border-color: #3f9a6b; }
.df-day:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.df-day[data-today] .df-num { text-decoration: underline; text-underline-offset: 3px; }
.df-day[data-outside-view] { visibility: hidden; }
.df-day[data-disabled], .df-day[data-unavailable] { background: none; color: #c0c9c0; cursor: not-allowed; }
.df-day.idle { background: none; color: #8a9a8a; }
.df-day.off { background: repeating-linear-gradient(135deg, #f3f5f3, #f3f5f3 4px, #e8ebe8 4px, #e8ebe8 8px); color: #8a9a8a; }
.df-day.part { background: linear-gradient(180deg, #f7faf8 50%, #e8ebe8 50%); }
.df-day[data-selected] { background: #0a4a37; border-color: #0a4a37; color: #fff; }
.df-day[data-selected] .df-note { color: #9fd0b4; }

.df-years {
  position: relative; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 3px;
  height: 252px; overflow-y: auto; align-content: start;
}
.df-year {
  min-height: 40px; border: 1px solid transparent; border-radius: 8px; background: #f7faf8; color: #1a3a1a;
  font: inherit; font-size: 0.86rem; font-weight: 600; font-variant-numeric: lining-nums tabular-nums; cursor: pointer;
}
.df-year:hover:not(.on) { border-color: #3f9a6b; }
.df-year:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.df-year.on { background: #0a4a37; border-color: #0a4a37; color: #fff; }

.df-foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: 7px; padding-top: 10px; border-top: 1px solid #d9e3dc; }
.df-summary { margin: 0; font-size: 0.78rem; color: #4a5a4a; line-height: 1.45; }
.df-actions { display: flex; gap: 6px; flex: none; }
@media (max-width: 640px) { .df-day { min-height: 44px; } .df-note { font-size: 0.54rem; } }

/* phones: a sheet from the bottom. Reka positions a wrapper around the pop-up, so that is what moves. */
.df-backdrop { position: fixed; inset: 0; z-index: 1199; background: rgba(20, 30, 20, 0.55); }
[data-reka-popper-content-wrapper]:has(> .df-pop.sheet) {
  position: fixed !important; top: auto !important; right: 0 !important; bottom: 0 !important; left: 0 !important;
  transform: none !important; min-width: 0 !important; width: 100% !important;
}
.df-pop.sheet {
  box-sizing: border-box; width: 100%; max-width: none; border-radius: 18px 18px 0 0;
  padding: 16px 16px calc(16px + env(safe-area-inset-bottom));
}
@media (prefers-reduced-motion: no-preference) {
  .df-pop.sheet { animation: df-sheet-up 0.2s ease-out; }
}
@keyframes df-sheet-up { from { transform: translateY(24px); opacity: 0.6; } }
</style>
