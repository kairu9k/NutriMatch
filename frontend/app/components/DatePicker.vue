<template>
  <!-- The app's one date picker (2026-11-03, user's call — replaces every
       native <input type="date">). A date box; clicking it opens a month
       calendar in a pop-over (a sheet from the bottom on phones).
         single: v-model = 'YYYY-MM-DD' ('' = none); one click picks and closes.
         range:  v-model:from / v-model:to; first click = start, a later click
                 = end and closes. Closing after only a start = that one day
                 (from = to). Values are emitted only when a pick is finished,
                 so pages watching them don't reload halfway through a range.
       year-select adds month/year drop-downs (dates of birth). -->
  <div class="dp" :class="[`dp-${size}`, { 'dp-block': block }]">
    <button
      :id="id"
      ref="trigger"
      type="button"
      class="dp-trigger"
      :class="{ invalid, empty: !display, open }"
      :disabled="disabled"
      :aria-label="ariaLabel ? `${ariaLabel}${display ? `: ${display}` : ''}` : undefined"
      aria-haspopup="dialog"
      :aria-expanded="open"
      @click="toggle"
    >
      <CalendarDays :size="16" class="dp-icon" aria-hidden="true" />
      <span class="dp-text">{{ display || placeholderText }}</span>
    </button>

    <Teleport to="body">
      <div v-if="open && sheet" class="dp-backdrop" @click="close()" />
      <div
        v-if="open"
        ref="pop"
        class="dp-pop"
        :class="{ sheet }"
        :style="sheet ? null : popStyle"
        role="dialog"
        :aria-label="range ? 'Pick dates' : 'Pick a date'"
      >
        <div class="dp-head">
          <button type="button" class="dp-nav" aria-label="Previous month" :disabled="!canGoBack" @click="shiftMonth(-1)"><ChevronLeft :size="18" /></button>
          <div v-if="yearSelect" class="dp-selects">
            <select class="nm-select dp-select" aria-label="Month" :value="viewMonth.slice(5, 7)" @change="setMonth(viewMonth.slice(0, 4), $event.target.value)">
              <option v-for="m in monthOptions" :key="m.value" :value="m.value" :disabled="m.disabled">{{ m.label }}</option>
            </select>
            <select class="nm-select dp-select" aria-label="Year" :value="viewMonth.slice(0, 4)" @change="setMonth($event.target.value, viewMonth.slice(5, 7))">
              <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
            </select>
          </div>
          <p v-else class="dp-month" aria-live="polite">{{ monthLabel }}</p>
          <button type="button" class="dp-nav" aria-label="Next month" :disabled="!canGoForward" @click="shiftMonth(1)"><ChevronRight :size="18" /></button>
        </div>

        <div class="dp-grid" role="grid" :aria-label="monthLabel" @keydown="onKey" @mouseleave="hoverIso = ''">
          <span v-for="d in WEEKDAYS" :key="d" class="dp-wd" aria-hidden="true">{{ d }}</span>
          <template v-for="cell in cells" :key="cell.key">
            <span v-if="!cell.iso" class="dp-cell empty" aria-hidden="true" />
            <button
              v-else
              :ref="el => setCellRef(cell.iso, el)"
              type="button"
              class="dp-cell"
              :class="cell.classes"
              :disabled="cell.blocked"
              :tabindex="cell.iso === focusIso ? 0 : -1"
              :aria-label="cell.label"
              :aria-pressed="cell.isStart || cell.isEnd"
              @click="pick(cell.iso)"
              @mouseenter="hoverIso = cell.iso"
              @focus="focusIso = cell.iso"
            >
              <span class="dp-num">{{ cell.day }}</span>
              <span v-if="cell.note" class="dp-note">{{ cell.note }}</span>
            </button>
          </template>
        </div>

        <div class="dp-foot">
          <p class="dp-summary">{{ summary }}</p>
          <div class="dp-actions">
            <button v-if="hasValue" type="button" class="nm-btn-soft nm-btn-sm" @click="clear">Clear</button>
            <button v-if="sheet" type="button" class="nm-btn-dark nm-btn-sm" @click="close()">Done</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { CalendarDays, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { phIso } from '~/utils/phTime'

const props = defineProps({
  modelValue: { type: String, default: '' },
  from: { type: String, default: '' },
  to: { type: String, default: '' },
  range: { type: Boolean, default: false },
  min: { type: String, default: '' },
  max: { type: String, default: '' },
  // Longest range in days (inclusive); 0 = no limit.
  maxDays: { type: Number, default: 0 },
  // iso -> true when there are working hours that day (Block time off only).
  isWorkingDay: { type: Function, default: null },
  // Existing time off to mark: [{ start_date, end_date, whole_day }]
  blocks: { type: Array, default: () => [] },
  yearSelect: { type: Boolean, default: false },
  // Month to show when nothing is picked yet (defaults to today, kept inside min/max).
  openAt: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  invalid: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
  id: { type: String, default: undefined },
  ariaLabel: { type: String, default: '' },
  size: { type: String, default: 'md' }, // sm (filters) | md | lg (sign-up forms)
  block: { type: Boolean, default: true }, // full width
})
const emit = defineEmits(['update:modelValue', 'update:from', 'update:to'])

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

// Plain calendar dates, computed in UTC so no time zone can shift a day.
const parse = iso => { const [y, m, d] = iso.split('-').map(Number); return new Date(Date.UTC(y, m - 1, d)) }
const fmt = dt => dt.toISOString().slice(0, 10)
const addDays = (iso, n) => { const dt = parse(iso); dt.setUTCDate(dt.getUTCDate() + n); return fmt(dt) }
const daysBetween = (a, b) => Math.round((parse(b) - parse(a)) / 86400000)
const nice = (iso, opts) => parse(iso).toLocaleDateString('en-US', { timeZone: 'UTC', ...opts })
const monthOf = iso => iso.slice(0, 7) + '-01'
const lastDayOf = iso => { const dt = parse(monthOf(iso)); dt.setUTCMonth(dt.getUTCMonth() + 1, 0); return fmt(dt) }

const today = phIso()
const outside = iso => (props.min && iso < props.min) || (props.max && iso > props.max)
const clampIso = iso => (props.min && iso < props.min ? props.min : props.max && iso > props.max ? props.max : iso)

/* ---------- the box ---------- */
const placeholderText = computed(() => props.placeholder || (props.range ? 'Pick dates' : 'Pick a date'))
const display = computed(() => {
  const full = { month: 'short', day: 'numeric', year: 'numeric' }
  if (!props.range) return props.modelValue ? nice(props.modelValue, full) : ''
  const { from, to } = props
  if (!from && !to) return ''
  if (from && (!to || to === from)) return nice(from, full) + (to ? '' : ' onwards')
  if (!from) return `Until ${nice(to, full)}`
  return from.slice(0, 4) === to.slice(0, 4)
    ? `${nice(from, { month: 'short', day: 'numeric' })} to ${nice(to, full)}`
    : `${nice(from, full)} to ${nice(to, full)}`
})
const hasValue = computed(() => (props.range ? !!(props.from || props.to || draftFrom.value) : !!props.modelValue))

/* ---------- open / close ---------- */
const open = ref(false)
const trigger = ref(null)
const pop = ref(null)
const popStyle = ref({})
const sheet = ref(false)
const draftFrom = ref('')
const draftTo = ref('')
const touched = ref(false)
const viewMonth = ref(monthOf(today))
const focusIso = ref(today)
const hoverIso = ref('')

function toggle() { open.value ? close() : show() }
async function show() {
  if (props.disabled) return
  draftFrom.value = props.range ? props.from : ''
  draftTo.value = props.range ? props.to : ''
  touched.value = false
  const start = (props.range ? props.from || props.to : props.modelValue) || props.openAt || today
  focusIso.value = clampIso(start)
  viewMonth.value = monthOf(focusIso.value)
  sheet.value = window.matchMedia('(max-width: 640px)').matches
  open.value = true
  await nextTick()
  place()
  cellRefs.get(focusIso.value)?.focus({ preventScroll: true })
}
function close(refocus = true) {
  if (!open.value) return
  // A range with only its first day picked = that one day.
  if (props.range && touched.value && draftFrom.value && !draftTo.value) commitRange(draftFrom.value, draftFrom.value)
  open.value = false
  hoverIso.value = ''
  if (refocus) trigger.value?.focus({ preventScroll: true })
}
function commitRange(from, to) {
  emit('update:from', from)
  emit('update:to', to)
}

// Pop-over sits under the box (above it when there's no room below), kept on screen.
function place() {
  if (sheet.value || !trigger.value || !pop.value) return
  const r = trigger.value.getBoundingClientRect()
  const w = pop.value.offsetWidth
  const h = pop.value.offsetHeight
  const below = window.innerHeight - r.bottom
  const top = below >= h + 12 || below >= r.top ? r.bottom + 6 : r.top - h - 6
  const left = Math.max(8, Math.min(r.left, window.innerWidth - w - 8))
  popStyle.value = { top: `${Math.max(8, top)}px`, left: `${left}px` }
}
function onOutside(e) {
  if (!open.value) return
  if (pop.value?.contains(e.target) || trigger.value?.contains(e.target)) return
  close(false)
}
function onEsc(e) {
  if (open.value && e.key === 'Escape') {
    // Don't let the pop-up underneath close too.
    e.stopPropagation()
    e.preventDefault()
    close()
  }
}
function onViewport() {
  if (sheet.value) return
  if (window.matchMedia('(max-width: 640px)').matches) { close(false); return }
  place()
}
watch(open, (isOpen) => {
  const fn = isOpen ? 'addEventListener' : 'removeEventListener'
  document[fn]('pointerdown', onOutside, true)
  window[fn]('keydown', onEsc, true)
  window[fn]('resize', onViewport)
  window[fn]('scroll', onViewport, true)
})
onBeforeUnmount(() => { open.value = false })

/* ---------- month navigation ---------- */
const canGoBack = computed(() => !props.min || viewMonth.value > monthOf(props.min))
const canGoForward = computed(() => !props.max || viewMonth.value < monthOf(props.max))
const monthLabel = computed(() => nice(viewMonth.value, { month: 'long', year: 'numeric' }))
async function shiftMonth(n) {
  const dt = parse(viewMonth.value)
  dt.setUTCMonth(dt.getUTCMonth() + n)
  const next = fmt(dt)
  if ((n < 0 && !canGoBack.value) || (n > 0 && !canGoForward.value)) return
  viewMonth.value = next
  focusIso.value = clampIso(next)
  await nextTick(); place()
}
function setMonth(y, m) {
  let next = `${y}-${m}-01`
  if (props.min && next < monthOf(props.min)) next = monthOf(props.min)
  if (props.max && next > monthOf(props.max)) next = monthOf(props.max)
  viewMonth.value = next
  focusIso.value = clampIso(next)
}
const yearOptions = computed(() => {
  const hi = Number((props.max || addDays(today, 3650)).slice(0, 4))
  const lo = Number((props.min || '1900-01-01').slice(0, 4))
  return Array.from({ length: hi - lo + 1 }, (_, i) => String(hi - i))
})
const monthOptions = computed(() => MONTHS.map((label, i) => {
  const value = String(i + 1).padStart(2, '0')
  const first = `${viewMonth.value.slice(0, 4)}-${value}-01`
  return { value, label, disabled: (props.max && first > props.max) || (props.min && lastDayOf(first) < props.min) }
}))

/* ---------- days ---------- */
function blockOn(iso) {
  let part = false
  for (const b of props.blocks) {
    if (b.start_date <= iso && iso <= (b.end_date || b.start_date)) {
      if (b.whole_day) return 'off'
      part = true
    }
  }
  return part ? 'part' : ''
}
const tooLong = iso => props.maxDays > 0 && draftFrom.value && daysBetween(draftFrom.value, iso) >= props.maxDays
// While choosing the end of a range, the range follows the pointer.
const rangeEnd = computed(() => {
  if (!props.range) return ''
  if (draftTo.value) return draftTo.value
  if (draftFrom.value && hoverIso.value > draftFrom.value && !tooLong(hoverIso.value)) return hoverIso.value
  return ''
})
const cells = computed(() => {
  const lead = parse(viewMonth.value).getUTCDay()
  const count = Number(lastDayOf(viewMonth.value).slice(8))
  const out = Array.from({ length: lead }, (_, i) => ({ key: `e${i}` }))
  for (let day = 1; day <= count; day++) {
    const iso = viewMonth.value.slice(0, 8) + String(day).padStart(2, '0')
    const blocked = !!outside(iso)
    const isStart = props.range ? iso === draftFrom.value : iso === props.modelValue
    const isEnd = props.range && !!rangeEnd.value && iso === rangeEnd.value
    const between = props.range && !!draftFrom.value && !!rangeEnd.value && iso > draftFrom.value && iso < rangeEnd.value
    const off = blocked ? '' : blockOn(iso)
    const idle = !blocked && !off && props.isWorkingDay && !props.isWorkingDay(iso)
    const note = off === 'off' ? 'Day off' : off === 'part' ? 'Part off' : idle ? 'No hours' : ''
    out.push({
      key: iso, iso, day, blocked, isStart, isEnd, note,
      classes: {
        blocked, today: iso === today, start: isStart, end: isEnd, between,
        preview: props.range && !draftTo.value && (isEnd || between), off: off === 'off', part: off === 'part', idle,
      },
      label: `${nice(iso, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}${note ? `, ${note.toLowerCase()}` : ''}${isStart ? (props.range ? ', first day' : ', selected') : ''}${isEnd && draftTo.value ? ', last day' : ''}`,
    })
  }
  return out
})

function pick(iso) {
  if (outside(iso)) return
  focusIso.value = iso
  if (!props.range) {
    emit('update:modelValue', iso)
    close()
    return
  }
  touched.value = true
  if (!draftFrom.value || draftTo.value || iso < draftFrom.value || tooLong(iso)) {
    draftFrom.value = iso
    draftTo.value = ''
    return
  }
  draftTo.value = iso
  commitRange(draftFrom.value, iso)
  close()
}
function clear() {
  if (props.range) {
    draftFrom.value = ''
    draftTo.value = ''
    touched.value = false
    commitRange('', '')
  } else {
    emit('update:modelValue', '')
  }
  close()
}

const summary = computed(() => {
  const short = { weekday: 'short', month: 'short', day: 'numeric' }
  if (!props.range) {
    if (props.modelValue) return nice(props.modelValue, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
    return 'Pick a day.'
  }
  if (!draftFrom.value) return 'Pick the first day, then the last day.'
  if (!draftTo.value) return `${nice(draftFrom.value, short)}. Pick the last day, or the same day again for just this one.`
  if (draftTo.value === draftFrom.value) return `${nice(draftFrom.value, short)} (1 day)`
  return `${nice(draftFrom.value, short)} to ${nice(draftTo.value, short)} (${daysBetween(draftFrom.value, draftTo.value) + 1} days)`
})

/* ---------- keyboard: arrows a day / a week, Page Up/Down a month, Enter/Space picks ---------- */
const cellRefs = new Map()
function setCellRef(iso, el) { if (el) cellRefs.set(iso, el); else cellRefs.delete(iso) }
async function onKey(e) {
  const moves = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }
  let next = ''
  if (e.key in moves) next = addDays(focusIso.value, moves[e.key])
  else if (e.key === 'PageUp' || e.key === 'PageDown') {
    const dt = parse(focusIso.value); dt.setUTCMonth(dt.getUTCMonth() + (e.key === 'PageUp' ? -1 : 1)); next = fmt(dt)
  } else return
  e.preventDefault()
  next = clampIso(next)
  focusIso.value = next
  if (monthOf(next) !== viewMonth.value) viewMonth.value = monthOf(next)
  await nextTick()
  cellRefs.get(next)?.focus()
}
</script>

<style scoped>
.dp { position: relative; display: inline-block; min-width: 0; }
.dp-block { display: block; width: 100%; }

.dp-trigger {
  width: 100%; display: flex; align-items: center; gap: 8px; text-align: left; cursor: pointer;
  border: 1px solid #d5dad5; border-radius: 8px; background: #fff; color: #1a3a1a;
  font-family: inherit; font-size: 0.86rem; padding: 10px 12px; min-height: 42px;
}
.dp-sm .dp-trigger { padding: 7px 10px; min-height: 36px; font-size: 0.82rem; }
.dp-lg .dp-trigger { padding: 11px 14px; min-height: 46px; font-size: 0.95rem; }
.dp-trigger:hover:not(:disabled) { border-color: #3f9a6b; }
.dp-trigger:focus-visible, .dp-trigger.open { outline: none; border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.15); }
.dp-trigger.invalid { border-color: #c0392b; background: #fff8f7; }
.dp-trigger:disabled { background: #f4f5f3; color: #8a9a8a; cursor: not-allowed; }
.dp-trigger.empty .dp-text { color: #8a9a8a; }
.dp-icon { flex: none; color: #3f9a6b; }
.dp-text { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-variant-numeric: lining-nums tabular-nums; }

/* pop-over (teleported to body so pop-ups' scrolling middles don't clip it) */
.dp-pop {
  position: fixed; z-index: 1200; width: 332px; max-width: calc(100vw - 16px);
  background: #fff; border-radius: 14px; padding: 12px;
  box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
  font-family: 'Inter', sans-serif; color: #1a3a1a;
}
.dp-backdrop { position: fixed; inset: 0; z-index: 1199; background: rgba(20, 30, 20, 0.55); }
.dp-pop.sheet {
  left: 0; right: 0; bottom: 0; top: auto; width: auto; max-width: none;
  border-radius: 18px 18px 0 0; padding: 16px 16px calc(16px + env(safe-area-inset-bottom));
}

.dp-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px; }
.dp-month { margin: 0; font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1rem; }
.dp-selects { display: flex; gap: 6px; flex: 1; justify-content: center; min-width: 0; }
.dp-select { min-width: 0; }
.dp-nav {
  flex: none; width: 32px; height: 32px; border-radius: 8px; border: none; background: #e3efe7; color: #0a4a37;
  display: flex; align-items: center; justify-content: center; cursor: pointer;
}
.dp-nav:hover:not(:disabled) { background: #d3e6d9; }
.dp-nav:disabled { opacity: 0.4; cursor: not-allowed; }
.dp-nav:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.dp-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 3px; }
.dp-wd { text-align: center; font-size: 0.72rem; font-weight: 600; color: #6a7a6a; padding-bottom: 2px; }
.dp-cell {
  min-height: 40px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
  border: 1px solid transparent; border-radius: 8px; background: #f7faf8; color: #1a3a1a;
  font-family: inherit; padding: 2px; cursor: pointer;
}
.dp-cell.empty { background: none; cursor: default; }
.dp-cell:hover:not(:disabled):not(.start):not(.end) { border-color: #3f9a6b; }
.dp-cell:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.dp-num { font-size: 0.86rem; font-weight: 600; font-variant-numeric: lining-nums tabular-nums; }
.dp-note { font-size: 0.56rem; font-weight: 600; white-space: nowrap; color: #6a7a6a; }
.dp-cell.today .dp-num { text-decoration: underline; text-underline-offset: 3px; }
.dp-cell.blocked { background: none; color: #c0c9c0; cursor: not-allowed; }
.dp-cell.idle { background: none; color: #8a9a8a; }
.dp-cell.off { background: repeating-linear-gradient(135deg, #f3f5f3, #f3f5f3 4px, #e8ebe8 4px, #e8ebe8 8px); color: #8a9a8a; }
.dp-cell.part { background: linear-gradient(180deg, #f7faf8 50%, #e8ebe8 50%); }
.dp-cell.between { background: #e3efe7; border-color: #cfe3d6; color: #1a3a1a; }
.dp-cell.between .dp-note { color: #1f6f46; }
.dp-cell.preview.between { background: #eef5f0; border-style: dashed; border-color: #3f9a6b; }
.dp-cell.start, .dp-cell.end { background: #0a4a37; border-color: #0a4a37; color: #fff; }
.dp-cell.start .dp-note, .dp-cell.end .dp-note { color: #9fd0b4; }
.dp-cell.preview.end { background: #3f9a6b; border-color: #3f9a6b; }

.dp-foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #d9e3dc; }
.dp-summary { margin: 0; font-size: 0.78rem; color: #4a5a4a; line-height: 1.45; }
.dp-actions { display: flex; gap: 6px; flex: none; }

@media (max-width: 640px) {
  .dp-cell { min-height: 44px; }
  .dp-note { font-size: 0.54rem; }
}
</style>
