<template>
  <div>
    <!-- PAGE HEADER (hidden when embedded in Profile Settings, which has its own) -->
    <div v-if="!embedded" class="page-header">
      <div>
        <h1 class="page-title">Weekly availability</h1>
        <p class="page-subtitle">Set the hours clients can book consultations with you.</p>
      </div>
      <button v-if="!weekOpen" class="day-action-link" type="button" @click="openWeekForm"><Plus :size="14" aria-hidden="true" /> Add hours for all week</button>
    </div>

    <!-- ADD HOURS FOR ALL WEEK — the same hours on several days at once.
         Days whose hours already overlap are skipped, not changed. -->
    <div v-if="weekOpen" class="week-form">
      <div class="week-form-row">
        <span class="field-label week-label">Hours</span>
        <input v-model="weekForm.start_time" type="time" class="time-input" aria-label="Start time" />
        <span class="time-sep">to</span>
        <input v-model="weekForm.end_time" type="time" class="time-input" aria-label="End time" />
      </div>
      <div class="week-form-row">
        <span class="field-label week-label">Days</span>
        <div class="day-chips" role="group" aria-label="Days to add these hours to">
          <button v-for="d in DISPLAY_ORDER" :key="d" type="button" class="day-chip" :class="{ on: weekForm.days.includes(d) }" :aria-pressed="weekForm.days.includes(d)" @click="toggleWeekDay(d)">{{ DAY_NAMES[d].slice(0, 3) }}</button>
        </div>
        <button type="button" class="chip-link" @click="weekForm.days = [1, 2, 3, 4, 5]">Weekdays</button>
        <button type="button" class="chip-link" @click="weekForm.days = [...DISPLAY_ORDER]">Every day</button>
      </div>      <div class="week-form-actions">
        <button class="form-btn cancel" type="button" @click="weekOpen = false">Cancel</button>
        <button class="form-btn save" type="button" :disabled="!weekForm.days.length || weekSaving" @click="addWeekHours">
          {{ weekSaving ? 'Adding…' : `Add to ${weekForm.days.length} day${weekForm.days.length === 1 ? '' : 's'}` }}
        </button>
      </div>
      <p v-if="saveError && errorAt === 'week'" class="save-error in-form" role="alert">{{ saveError }}</p>
    </div>

    <!-- the two things people get wrong (Calendly's forum has the same questions) -->
    <!-- quick summary of the week -->
    <div v-if="!loading" class="av-sum">
      <span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg><b>{{ daysOpen }}</b> {{ daysOpen === 1 ? 'day' : 'days' }} open</span>
      <span><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg><b>{{ weekSlots }}</b> one-hour {{ weekSlots === 1 ? 'slot' : 'slots' }} a week</span>
    </div>

    <!-- WEEKLY DAY ROWS -->
    <div v-if="loading" class="empty-note">Loading…</div>
    <div v-else class="day-list">
      <div v-for="day in week" :key="day.dayIndex" class="day-row" :class="{ today: day.dayIndex === todayDow, empty: !day.slots.length }">
        <div class="day-head">
          <span class="day-name">{{ day.day.slice(0, 3) }}<em v-if="day.dayIndex === todayDow" class="today-tag">Today</em></span>
          <small>{{ dayCount(day.slots) }} {{ dayCount(day.slots) === 1 ? 'slot' : 'slots' }}</small>
        </div>

        <div class="day-content">
          <template v-if="day.slots.length">
            <template v-for="slot in day.slots" :key="slot.id">
              <div v-if="editingId === slot.id" class="slot-edit-form">
                <input v-model="editForm.start_time" type="time" class="time-input" />
                <span class="time-sep">to</span>
                <input v-model="editForm.end_time" type="time" class="time-input" />
                <button class="form-btn save" :disabled="!!busyKey" @click="saveEdit(slot)">{{ busyKey === `edit-${slot.id}` ? 'Saving…' : 'Save' }}</button>
                <button class="form-btn cancel" @click="cancelEdit">Cancel</button>
                <p v-if="saveError && errorAt === `edit-${slot.id}`" class="save-error in-form" role="alert">{{ saveError }}</p>
              </div>
              <button v-else class="slot-pill" type="button" :aria-label="`Edit ${formatTime(slot.start_time)} to ${formatTime(slot.end_time)}`" @click="startEdit(slot)">
                <span class="sp-from">{{ formatTime(slot.start_time) }}</span>
                <span class="sp-to">to {{ formatTime(slot.end_time) }}</span>
                <span class="pill-icon-btn" role="button" :aria-disabled="!!busyKey || undefined" :aria-label="`Remove ${formatTime(slot.start_time)} to ${formatTime(slot.end_time)}`" @click.stop="removeSlot(slot)"><X :size="13" /></span>
              </button>
            </template>
          </template>
          <span v-else class="empty-note-inline">Closed</span>

          <div v-if="addingDay === day.dayIndex" class="slot-edit-form">
            <input v-model="addForm.start_time" type="time" class="time-input" />
            <span class="time-sep">to</span>
            <input v-model="addForm.end_time" type="time" class="time-input" />
            <button class="form-btn save" :disabled="!!busyKey" @click="confirmAddSlot(day.dayIndex)">{{ busyKey === `add-${day.dayIndex}` ? 'Adding…' : 'Add' }}</button>
            <button class="form-btn cancel" @click="addingDay = null">Cancel</button>
            <p v-if="saveError && errorAt === `add-${day.dayIndex}`" class="save-error in-form" role="alert">{{ saveError }}</p>
          </div>
          <!-- what clients actually get: 1-hour consultations every hour from each block's start -->
          <p v-if="day.slots.length" class="day-preview">
            <span class="day-book" :title="`Clients can book ${bookableText(day.slots) || 'nothing yet'}.`">Clients can book {{ bookableText(day.slots) || 'nothing yet' }}.</span>
            <span v-for="w in wastedText(day.slots)" :key="w" class="day-waste">{{ w }}</span>
          </p>
        </div>

        <button v-if="addingDay !== day.dayIndex" class="day-action-link day-add" @click="startAddSlot(day.dayIndex)"><Plus :size="14" aria-hidden="true" /> Add</button>
      </div>
    </div>

    <!-- the two things people get wrong (Calendly's forum has the same questions) -->
    <p class="nm-note plain-note avail-hint">
      <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg><span>Taking a lunch break? Add your morning and afternoon as two blocks, for example 8:00 AM to 12:00 PM and 1:00 PM to 5:00 PM.
      For hours that end at midnight, use 12:00 AM. Tap a time to edit it.</span>
    </p>


    <!-- BLOCK TIME OFF — whole days or part of a day on specific dates
         (RndTimeOff, /api/rnd/time-off/). Clients can't book it. -->
    <div v-if="!hideTimeOff" class="block-panel">
      <div class="block-header">
        <span class="block-ico"><CalendarOff :size="19" class="block-icon" aria-hidden="true" /></span>
        <div>
          <h3 class="block-title">Block time off</h3>
          <p class="block-desc">Block whole days or part of a day, like a holiday, leave or a seminar afternoon. Clients can't book that time. Consultations already booked in it stay booked.</p>
        </div>
      </div>

      <div class="block-form">
        <div class="field">
          <label for="off-from">From</label>
          <DateField id="off-from" v-model="newBlock.from" :min="todayIso" :is-working-day="iso => hoursOn(iso).length > 0" :blocks="blocks" hint="Pick the first day." placeholder="Select date" />
        </div>
        <div class="field">
          <label for="off-to">To <span class="optional">(optional)</span></label>
          <DateField id="off-to" v-model="newBlock.to" :min="newBlock.from || todayIso" :is-working-day="iso => hoursOn(iso).length > 0" :blocks="blocks" clearable hint="Pick the last day." placeholder="Same day" />
        </div>
        <div class="field">
          <span class="field-label">Time</span>
          <div class="seg" role="radiogroup" aria-label="Block the whole day or part of it">
            <button type="button" role="radio" :aria-checked="newBlock.wholeDay" :class="{ on: newBlock.wholeDay }" @click="newBlock.wholeDay = true"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>Whole day</button>
            <button type="button" role="radio" :aria-checked="!newBlock.wholeDay" :class="{ on: !newBlock.wholeDay }" @click="newBlock.wholeDay = false"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor" stroke="none" /></svg>Part of the day</button>
          </div>
        </div>
        <template v-if="!newBlock.wholeDay">
          <div class="field">
            <label for="off-start">From time</label>
            <select id="off-start" v-model="newBlock.startTime" class="nm-select block">
              <option v-for="h in HOURS.slice(0, -1)" :key="h.value" :value="h.value">{{ h.label }}</option>
            </select>
          </div>
          <div class="field">
            <label for="off-end">To time</label>
            <select id="off-end" v-model="newBlock.endTime" class="nm-select block">
              <option v-for="h in HOURS.slice(1)" :key="h.value" :value="h.value">{{ h.label }}</option>
            </select>
          </div>
        </template>
        <div v-if="newBlock.from" class="field field-wide">
          <label for="off-reason">Reason <span class="optional">(optional, only you see it)</span></label>
          <input id="off-reason" v-model="newBlock.reason" type="text" maxlength="200" placeholder="e.g. Annual leave" />
        </div>
        <button class="block-btn" :disabled="!newBlock.from || !!blockRuleError || blockSaving" @click="submitBlock">{{ blockSaving ? 'Blocking…' : 'Block time' }}</button>
      </div>
      <p v-if="blockRuleError" class="save-error" role="alert">{{ blockRuleError }}</p>
      <div v-if="conflicts.length" class="conflicts" role="status">
        <p><strong>You already have {{ conflicts.length }} consultation{{ conflicts.length === 1 ? '' : 's' }} in this time.</strong> They weren't cancelled. Cancel or move them from Appointments.</p>
        <ul><li v-for="c in conflicts" :key="c.id">{{ when(c.scheduled_at) }}, {{ c.client_name }}, {{ c.type_label.toLowerCase() }}</li></ul>
        <NuxtLink to="/appointments?tab=upcoming" class="nm-panel-link">Open Appointments</NuxtLink>
      </div>

      <div v-if="blocks.length" class="blocked-list">
        <div v-for="b in blocks" :key="b.id" class="blocked-item">
          <span class="blocked-dates">{{ formatBlockDate(b.start_date) }}<template v-if="b.end_date !== b.start_date"> to {{ formatBlockDate(b.end_date) }}</template></span>
          <span class="blocked-time">{{ b.whole_day ? 'Whole day' : `${formatTime(b.start_time)} to ${formatTime(b.end_time)}` }}</span>
          <span class="blocked-reason">{{ b.reason }}</span>
          <button class="remove-block-btn" :disabled="!!busyKey" :aria-label="`Remove time off on ${formatBlockDate(b.start_date)}`" @click="removeBlock(b)"><X :size="14" /></button>
        </div>
      </div>
      <p v-else class="empty-note block-empty">No time blocked off yet.</p>
    </div>
  </div>
</template>

<script setup>
import { phIso } from '~/utils/phTime'
import { computed, onMounted, reactive, ref } from 'vue'
import { X, CalendarOff, PenLine, Plus } from 'lucide-vue-next'
import { useToast } from '~/composables/useToast'

definePageMeta({ layout: 'dashboard', title: 'Availability' })

// hideTimeOff: the RND onboarding uses this same editor, without the time-off panel
defineProps({ embedded: { type: Boolean, default: false }, hideTimeOff: { type: Boolean, default: false } })

const { get, post, patch, del } = useApi()

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

const slots = ref([])
const loading = ref(true)
// A problem with the hours typed shows inside the form being used (errorAt says
// which one). What an action did, or a failure from the server, goes to the
// toast (2026-11-03) so it shows wherever the page is scrolled.
const saveError = ref('')
const errorAt = ref('')
const toast = useToast()
function formProblem(where, message) { errorAt.value = where; saveError.value = message }
// One hours action at a time (2026-11-03): a double click on Add sent two
// requests at once, and the server's overlap check can miss a simultaneous pair.
const busyKey = ref('')

const addingDay = ref(null)
const addForm = reactive({ start_time: '09:00', end_time: '17:00' })

const editingId = ref(null)
const editForm = reactive({ start_time: '09:00', end_time: '17:00' })

onMounted(async () => {
  try {
    const [schedule, off] = await Promise.all([get('/rnd/availability/'), get('/rnd/time-off/').catch(() => [])])
    slots.value = schedule
    blocks.value = off
  } finally {
    loading.value = false
  }
})

// Displayed Monday-first (matches the public RND profile); day_of_week itself
// keeps the backend's Sunday=0 convention.
const DISPLAY_ORDER = [1, 2, 3, 4, 5, 6, 0]
const week = computed(() =>
  DISPLAY_ORDER.map(dayIndex => ({
    day: DAY_NAMES[dayIndex],
    dayIndex,
    slots: slots.value
      .filter(s => s.day_of_week === dayIndex)
      .sort((a, b) => a.start_time.localeCompare(b.start_time)),
  }))
)

function formatTime(t) {
  const [h, m] = t.split(':').map(Number)
  const period = h >= 12 ? 'PM' : 'AM'
  const hour12 = h % 12 || 12
  return `${hour12}:${String(m).padStart(2, '0')} ${period}`
}

// Every block must be at least 1 hour, like at sign-up.
const MIN_BLOCK_MINUTES = 60
const toMinutes = t => { const [h, m] = t.split(':').map(Number); return h * 60 + m }
// An END time of 12:00 AM means midnight at the end of the day (profiles/hours.py):
// compare it as "24:00" so "10 PM to 12 AM" works.
const endKey = t => (t && t.slice(0, 5) === '00:00' ? '24:00' : (t || '').slice(0, 5))

/* ---------- what clients can book on a day (same grid as profiles/public.py) ---------- */
const SESSION = 60 // minutes, one consultation; starts step every hour from the block's start
const shortClock = (mins) => {
  const h = Math.floor(mins / 60) % 24
  const m = mins % 60
  return { text: `${h % 12 || 12}${m ? `:${String(m).padStart(2, '0')}` : ''}`, period: h < 12 ? 'AM' : 'PM' }
}
const sortedSlots = slots => [...slots].sort((a, b) => a.start_time.localeCompare(b.start_time))
// "8, 9, 10, 11 AM, 1, 2, 3, 4 PM"
function bookableText(daySlots) {
  const starts = []
  for (const s of sortedSlots(daySlots)) {
    const end = toMinutes(endKey(s.end_time))
    for (let t = toMinutes(s.start_time.slice(0, 5)); t + SESSION <= end; t += SESSION) starts.push(t)
  }
  const out = []
  starts.forEach((t, i) => {
    const c = shortClock(t)
    const next = starts[i + 1] != null ? shortClock(starts[i + 1]) : null
    out.push(next && next.period === c.period ? c.text : `${c.text} ${c.period}`)
  })
  return out.join(', ')
}
// "4:30 to 5:00 PM can't be booked: shorter than a 1-hour consultation."
function wastedText(daySlots) {
  return sortedSlots(daySlots).flatMap((s) => {
    const start = toMinutes(s.start_time.slice(0, 5))
    const end = toMinutes(endKey(s.end_time))
    const left = (end - start) % SESSION
    if (!left || end - start < SESSION) return end - start < SESSION ? [`${formatTime(s.start_time)} to ${formatTime(s.end_time)} is too short for a 1-hour consultation.`] : []
    return [`${formatTime(`${String(Math.floor((end - left) / 60) % 24).padStart(2, '0')}:${String((end - left) % 60).padStart(2, '0')}`)} to ${formatTime(s.end_time)} can't be booked: shorter than a 1-hour consultation.`]
  })
}

function rangeError(start, end) {
  if (!start || !end) return 'Pick a start and end time.'
  if (endKey(end) <= start) return 'End time must be after start time.'
  if (toMinutes(endKey(end)) - toMinutes(start) < MIN_BLOCK_MINUTES) return 'Hours must be at least 1 hour long.'
  return ''
}

const overlapsDay = (dayIndex, [a, b], exceptId = null) => slots.value.some(s =>
  s.day_of_week === dayIndex && s.id !== exceptId
  && a < endKey(s.end_time) && endKey(b) > s.start_time.slice(0, 5))

function createSlot(dayIndex, [start, end]) {
  return post('/rnd/availability/', {
    day_of_week: dayIndex,
    start_time: `${start}:00`,
    end_time: `${end}:00`,
    is_available: true,
    effective_from: phIso(),
  })
}

function startAddSlot(dayIndex) {
  editingId.value = null
  addForm.start_time = '09:00'
  addForm.end_time = '17:00'
  addingDay.value = dayIndex
}

async function confirmAddSlot(dayIndex) {
  if (busyKey.value) return
  saveError.value = ''
  const where = `add-${dayIndex}`
  const problem = rangeError(addForm.start_time, addForm.end_time)
  if (problem) return formProblem(where, problem)
  const hours = [addForm.start_time, addForm.end_time]
  if (overlapsDay(dayIndex, hours)) return formProblem(where, `${DAY_NAMES[dayIndex]} already has hours in that time. Edit them instead.`)
  busyKey.value = where
  try {
    slots.value.push(await createSlot(dayIndex, hours))
    addingDay.value = null
    toast.dismiss('availability')
  } catch (e) {
    toast.error(apiError(e, `Could not add hours to ${DAY_NAMES[dayIndex]}. Please try again.`), { id: 'availability' })
  } finally {
    busyKey.value = ''
  }
}

/* ---------- ADD HOURS FOR ALL WEEK ---------- */
const weekOpen = ref(false)
const weekSaving = ref(false)
const weekForm = reactive({ start_time: '09:00', end_time: '17:00', days: [] })

function openWeekForm() {
  addingDay.value = null
  editingId.value = null
  saveError.value = ''
  Object.assign(weekForm, { start_time: '09:00', end_time: '17:00', days: [...DISPLAY_ORDER] })
  weekOpen.value = true
}
defineExpose({ openWeekForm, hasHours: computed(() => slots.value.length > 0) })

function toggleWeekDay(d) {
  weekForm.days = weekForm.days.includes(d) ? weekForm.days.filter(x => x !== d) : [...weekForm.days, d]
}

const dayList = days => days.map(d => DAY_NAMES[d].slice(0, 3)).join(', ')

async function addWeekHours() {
  saveError.value = ''
  const problem = rangeError(weekForm.start_time, weekForm.end_time)
  if (problem) return formProblem('week', problem)
  const hours = [weekForm.start_time, weekForm.end_time]
  const days = DISPLAY_ORDER.filter(d => weekForm.days.includes(d))
  const added = [], skipped = [], failed = []
  weekSaving.value = true
  for (const d of days) {
    if (overlapsDay(d, hours)) { skipped.push(d); continue }
    try {
      slots.value.push(await createSlot(d, hours))
      added.push(d)
    } catch {
      failed.push(d)
    }
  }
  weekSaving.value = false
  const parts = []
  if (added.length) parts.push(`Added ${formatTime(hours[0])} – ${formatTime(hours[1])} to ${dayList(added)}.`)
  if (skipped.length) parts.push(`Skipped ${dayList(skipped)} (already has hours at that time).`)
  if (failed.length) parts.push(`Couldn't save ${dayList(failed)}. Please try again.`)
  if (failed.length) toast.error(parts.join(' '), { id: 'availability' })
  else if (added.length) toast.success(parts.join(' '), { id: 'availability', duration: skipped.length ? 6000 : 4000 })
  else toast.problem(parts.join(' '), { id: 'availability' })
  if (!failed.length) weekOpen.value = false
}

function startEdit(slot) {
  addingDay.value = null
  editForm.start_time = slot.start_time.slice(0, 5)
  editForm.end_time = slot.end_time.slice(0, 5)
  editingId.value = slot.id
}

function cancelEdit() {
  editingId.value = null
}

async function saveEdit(slot) {
  if (busyKey.value) return
  saveError.value = ''
  const where = `edit-${slot.id}`
  const problem = rangeError(editForm.start_time, editForm.end_time)
  if (problem) return formProblem(where, problem)
  if (overlapsDay(slot.day_of_week, [editForm.start_time, editForm.end_time], slot.id)) {
    return formProblem(where, `${DAY_NAMES[slot.day_of_week]} already has hours in that time.`)
  }
  busyKey.value = where
  try {
    const updated = await patch(`/rnd/availability/${slot.id}/`, {
      start_time: `${editForm.start_time}:00`,
      end_time: `${editForm.end_time}:00`,
    })
    const idx = slots.value.findIndex(s => s.id === slot.id)
    if (idx !== -1) slots.value[idx] = updated
    editingId.value = null
    toast.dismiss('availability')
  } catch (e) {
    // e.g. a booking sits in the hours being taken away (the API names it)
    toast.error(apiError(e, 'Could not update these hours. Try again.'), { id: 'availability' })
  } finally {
    busyKey.value = ''
  }
}

async function removeSlot(slot) {
  if (busyKey.value) return
  saveError.value = ''
  busyKey.value = `del-${slot.id}`
  try {
    await del(`/rnd/availability/${slot.id}/`)
    slots.value = slots.value.filter(s => s.id !== slot.id)
    toast.dismiss('availability')
  } catch (e) {
    toast.error(apiError(e, 'Could not remove these hours. Try again.'), { id: 'availability' })
  } finally {
    busyKey.value = ''
  }
}

/* ---------- BLOCK TIME OFF (/api/rnd/time-off/) ---------- */
const PH = { timeZone: 'Asia/Manila' }
const todayIso = new Date().toLocaleDateString('en-CA', PH)
const HOURS = [...Array.from({ length: 24 }, (_, h) => `${String(h).padStart(2, '0')}:00`), '23:59']
  .map(v => ({ value: v, label: formatTime(v) }))
const blocks = ref([])
const blankBlock = () => ({ from: '', to: '', wholeDay: true, startTime: '13:00', endTime: '17:00', reason: '' })
const newBlock = ref(blankBlock())
const blockSaving = ref(false)
const conflicts = ref([])
const when = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })

// A block must cover some of the weekly hours on at least one of its dates —
// a whole day needs a working day, a part-day block must overlap that day's
// hours (partly is fine). Same rule as the API (profiles/time_off.py
// outside_working_hours); Block stays disabled while this has a message.
function hoursOn(iso) {
  const dow = new Date(iso + 'T00:00:00').getDay() // Sunday = 0, like day_of_week
  return slots.value
    .filter(s => s.is_available !== false && s.day_of_week === dow
      && (!s.effective_from || s.effective_from <= iso) && (!s.effective_to || s.effective_to >= iso))
    .sort((a, b) => a.start_time.localeCompare(b.start_time))
}
const blockRuleError = computed(() => {
  const b = newBlock.value
  if (!b.from || loading.value) return ''
  if (!slots.value.length) return 'Add your weekly hours first. There are no hours to block yet.'
  const to = b.to && b.to > b.from ? b.to : b.from
  const covers = iso => {
    const hours = hoursOn(iso)
    return hours.length && (b.wholeDay || hours.some(s => s.start_time.slice(0, 5) < endKey(b.endTime) && endKey(s.end_time) > b.startTime))
  }
  const d = new Date(b.from + 'T00:00:00')
  for (let i = 0; i < 90; i++) {
    const iso = d.toLocaleDateString('en-CA')
    if (iso > to) break
    if (covers(iso)) return ''
    d.setDate(d.getDate() + 1)
  }
  if (to === b.from) {
    const name = DAY_NAMES[new Date(b.from + 'T00:00:00').getDay()]
    const hours = hoursOn(b.from)
    if (!hours.length) return `You have no hours on ${name}s, so there's nothing to block.`
    const list = hours.map(s => `${formatTime(s.start_time)} – ${formatTime(s.end_time)}`).join(', ')
    return `That time is outside your ${name} hours (${list}). Pick a time within them.`
  }
  return b.wholeDay
    ? "None of these dates fall on your working days, so there's nothing to block."
    : 'That time is outside your working hours on every date in this range.'
})

async function submitBlock() {
  const b = newBlock.value
  if (!b.from || blockRuleError.value) return
  blockSaving.value = true
  conflicts.value = []
  try {
    const saved = await post('/rnd/time-off/', {
      start_date: b.from, end_date: b.to || undefined, reason: b.reason.trim(),
      ...(b.wholeDay ? {} : { start_time: b.startTime, end_time: b.endTime }),
    })
    const { conflicts: found, ...block } = saved
    blocks.value = [...blocks.value, block].sort((x, y) => x.start_date.localeCompare(y.start_date) || String(x.start_time).localeCompare(String(y.start_time)))
    conflicts.value = found || []
    newBlock.value = blankBlock()
    toast.success(found?.length ? 'Time off blocked. You already have consultations in it, listed under the form.' : "Time off blocked. Clients can't book it.", { id: 'time-off', duration: found?.length ? 6000 : 4000 })
  } catch (e) {
    toast.error(apiError(e, 'Could not block that time. Please try again.'), { id: 'time-off' })
  } finally {
    blockSaving.value = false
  }
}
async function removeBlock(b) {
  if (busyKey.value) return
  busyKey.value = `off-${b.id}`
  try {
    await del(`/rnd/time-off/${b.id}/`)
    blocks.value = blocks.value.filter(x => x.id !== b.id)
    toast.dismiss('time-off')
  } catch (e) {
    toast.error(apiError(e, 'Could not remove that time off.'), { id: 'time-off' })
  } finally {
    busyKey.value = ''
  }
}
function formatBlockDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/* ---------- UI only ---------- */
// one-hour consultations a day can hold (same count as "Clients can book …")
function dayCount(daySlots) {
  let n = 0
  for (const sl of daySlots) {
    const end = toMinutes(endKey(sl.end_time))
    for (let t = toMinutes(sl.start_time.slice(0, 5)); t + SESSION <= end; t += SESSION) n++
  }
  return n
}
const daysOpen = computed(() => week.value.filter(d => d.slots.length).length)
const weekSlots = computed(() => week.value.reduce((sum, d) => sum + dayCount(d.slots), 0))
const todayDow = new Date(todayIso + 'T00:00:00').getDay()
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #1a3a1a; margin: 0 0 4px; }
.page-subtitle { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

/* the week: one panel, a divider between days */
.day-list {
  display: flex; flex-direction: column; margin-bottom: 24px; background: #fff;
  border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden;
}

.day-row { padding: 14px 18px; display: flex; align-items: center; gap: 16px; border-top: 1px solid #d9e3dc; }
.day-row:first-child { border-top: none; }

.day-name { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; width: 100px; flex-shrink: 0; }

.day-content { flex: 1; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }

.avail-hint { margin: 0 0 12px; }
.day-preview { flex-basis: 100%; display: flex; flex-direction: column; gap: 2px; margin: 4px 0 0; font-size: 0.78rem; color: #6a7a6a; line-height: 1.4; }
.day-waste { color: #8a5a10; }
.pill-edit { color: #3f6b55; flex-shrink: 0; }
.slot-pill {
  display: flex; align-items: center; gap: 6px;
  background: #e3efe7; color: #1e4a26; font-size: 0.82rem; font-weight: 600; font-family: inherit;
  padding: 6px 10px 6px 14px; border-radius: 999px; border: none; cursor: pointer;
}
.slot-pill:hover { background: #d3e7da; }
.slot-pill:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.pill-icon-btn {
  background: none; border: none; color: #3f7a55; cursor: pointer;
  display: flex; align-items: center; justify-content: center; padding: 2px;
}
.pill-icon-btn:hover { color: #1e4a26; }

.slot-edit-form { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; background: #f2f6f3; border-radius: 10px; padding: 6px 10px; }
.time-input {
  border: 1px solid #d9e3dc; border-radius: 6px; padding: 5px 8px; font-family: inherit;
  font-size: 0.82rem; color: #1a3a1a; background: #fff;
}
.time-sep { color: #6a7a6a; font-size: 0.82rem; }
.form-btn {
  display: inline-flex; align-items: center; justify-content: center; border: none; border-radius: 8px; min-height: 32px; padding: 0 12px;
  font-size: 0.78rem; font-weight: 600; cursor: pointer; font-family: inherit;
}
.form-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.form-btn.save { background: #0a4a37; color: #fff; }
.form-btn.save:hover:not(:disabled) { background: #00382a; }
.form-btn:disabled, .remove-block-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.pill-icon-btn[aria-disabled="true"] { opacity: 0.4; cursor: not-allowed; }
.form-btn.cancel { background: #e3efe7; color: #0a4a37; }
.form-btn.cancel:hover { background: #d3e7da; }

.form-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.empty-note-inline { font-size: 0.82rem; color: #8a9a8a; }

/* ADD HOURS FOR ALL WEEK */
.week-form {
  display: flex; flex-direction: column; gap: 12px; background: #f4f8f5;
  border: 1px solid #d9e3dc; border-radius: 12px; padding: 16px 18px; margin-bottom: 14px;
}
.week-form-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.week-label { width: 52px; flex-shrink: 0; }
.day-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.day-chip {
  border: 1px solid #d9e3dc; background: #fff; color: #4a5a4a; border-radius: 999px; min-height: 32px; padding: 0 12px;
  font-family: inherit; font-size: 0.78rem; font-weight: 600; cursor: pointer;
}
.day-chip.on { background: #0a4a37; border-color: #0a4a37; color: #fff; }
.day-chip:focus-visible, .chip-link:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.chip-link { background: none; border: none; color: #0a4a37; font-family: inherit; font-size: 0.78rem; font-weight: 600; cursor: pointer; text-decoration: underline; padding: 4px; }
.week-form-actions { display: flex; justify-content: flex-end; gap: 8px; }

.day-action-link {
  display: inline-flex; align-items: center; gap: 4px; background: #e3efe7; border: none; border-radius: 8px; color: #0a4a37; font-family: inherit;
  font-size: 0.78rem; font-weight: 600; cursor: pointer; white-space: nowrap; flex-shrink: 0; min-height: 32px; padding: 0 12px;
}
.day-action-link:hover { background: #d3e7da; }
.day-action-link:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.empty-note { font-size: 0.82rem; color: #6a7a6a; margin: 0; }
.save-error { font-size: 0.82rem; color: #c0483a; margin: 12px 0 0; }
.save-error.in-form { flex-basis: 100%; margin: 4px 0 2px; }

/* BLOCK A DAY OFF */
.block-panel { background: #f4f8f5; border: 1px solid #d9e3dc; border-radius: 12px; padding: 22px; margin-top: 20px; }
.block-header { display: flex; gap: 12px; margin-bottom: 20px; }
.block-icon { color: #1a3a1a; flex-shrink: 0; margin-top: 2px; }
.block-title { font-size: 0.98rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.block-desc { font-size: 0.82rem; color: #6a7a6a; line-height: 1.5; margin: 0; max-width: 640px; }

.block-form { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; align-items: end; margin-bottom: 16px; }
.field-wide { grid-column: span 2; }
.field-label { font-size: 0.78rem; font-weight: 600; color: #4a5a4a; }
.seg { display: flex; border: 1px solid #d9e3dc; border-radius: 8px; overflow: hidden; background: #fff; }
.seg button { flex: 1; border: 0; background: none; padding: 10px 8px; font-family: inherit; font-size: 0.8rem; color: #4a5a4a; cursor: pointer; white-space: nowrap; }
.seg button.on { background: #0a4a37; color: #fff; font-weight: 600; }
.conflicts { background: #fdf8ec; border-left: 3px solid #D4A017; border-radius: 6px; padding: 10px 14px; font-size: 0.82rem; color: #6a5a2a; margin: 0 0 14px; }
.conflicts p { margin: 0 0 6px; }
.conflicts ul { margin: 0 0 6px; padding-left: 18px; }
.blocked-time { color: #1a3a1a; white-space: nowrap; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.78rem; font-weight: 600; color: #4a5a4a; }
.optional { font-weight: 400; color: #9aaa9a; }
.field input {
  border: 1px solid #d9e3dc; border-radius: 8px; padding: 10px 12px;
  font-size: 0.85rem; font-family: inherit; background: #fff; color: #1a3a1a;
}
.field input:focus { outline: none; border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.15); }

.block-btn {
  background: #0a4a37; border: none; color: #fff; font-family: inherit;
  padding: 11px 24px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; cursor: pointer; white-space: nowrap;
}
.block-btn:hover:not(:disabled) { background: #00382a; }
.block-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.blocked-list { display: flex; flex-direction: column; gap: 8px; }
.blocked-item {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border: 1px solid #d9e3dc; border-radius: 8px; padding: 10px 14px; font-size: 0.82rem;
}
.blocked-dates { font-weight: 700; color: #1a3a1a; }
.blocked-reason { color: #7a8a7a; flex: 1; min-width: 0; overflow-wrap: anywhere; }
.remove-block-btn { background: none; border: none; color: #6a7a6a; cursor: pointer; display: flex; padding: 4px; }
.remove-block-btn:hover { color: #c0483a; }

@media (max-width: 900px) {
  .day-row { flex-wrap: wrap; gap: 8px 16px; }
  .day-content { flex-basis: 100%; order: 3; }
  .block-form { grid-template-columns: 1fr; }
  .field-wide { grid-column: auto; }
  .blocked-item { flex-wrap: wrap; }
}

/* =========================================================
   UI refresh: week grid (brand #004D3A / #EFBF04)
   ========================================================= */
.ic { flex-shrink: 0; display: inline-block; }

/* summary pills */
.av-sum { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 14px; }
.av-sum span { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; border-radius: 999px; background: #f3f6f4; font-size: 13px; color: #3e5046; }
.av-sum .ic { color: #1f7a4d; }
.av-sum b { color: #0e3a2c; }

/* the week: seven columns */
.day-list { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 10px; margin: 0; background: none; border: none; border-radius: 0; overflow: visible; }
.day-row, .day-row:first-child { display: flex; flex-direction: column; align-items: stretch; gap: 8px; min-width: 0; padding: 12px; border: 1px solid #edf2ee; border-radius: 16px; background: #f7faf8; }
.day-row.today { background: #f1f8f4; border-color: #bfdccb; }
.day-head { display: flex; align-items: baseline; justify-content: space-between; gap: 6px; padding: 0 2px 7px; border-bottom: 1px solid #e6eee9; }
.day-name { width: auto; display: inline-flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 800; color: #0e3a2c; }
.day-head small { font-size: 11.5px; color: #8a9a91; white-space: nowrap; }
.today-tag { padding: 2px 7px; border-radius: 999px; background: #efbf04; color: #004d3a; font-style: normal; font-size: 10px; font-weight: 800; letter-spacing: 0.3px; }
.day-content { flex: 1; display: flex; flex-direction: column; flex-wrap: nowrap; align-items: stretch; gap: 8px; }

/* a block of hours */
.slot-pill { position: relative; display: flex; flex-direction: column; align-items: flex-start; gap: 1px; width: 100%; padding: 9px 28px 9px 11px; border: 1px solid #cfe6d7; border-left: 4px solid #1f7a4d; border-radius: 11px; background: #fff; color: #0e3a2c; text-align: left; font-family: inherit; cursor: pointer; transition: border-color 0.15s, box-shadow 0.15s; }
.slot-pill:hover { background: #fff; border-color: #1f7a4d; box-shadow: 0 6px 14px -10px rgba(0, 77, 58, 0.6); }
.slot-pill:focus-visible { outline: 2px solid #004d3a; outline-offset: 2px; }
.sp-from { font-size: 13.5px; font-weight: 800; color: #0e3a2c; white-space: nowrap; }
.sp-to { font-size: 12px; font-weight: 600; color: #6b7d73; white-space: nowrap; }
.slot-pill .pill-icon-btn { position: absolute; top: 6px; right: 6px; width: 20px; height: 20px; padding: 0; border-radius: 50%; color: #8a9a91; }
.slot-pill .pill-icon-btn:hover { background: #fdecec; color: #b4384a; }
.empty-note-inline { padding: 10px 0; text-align: center; font-size: 12.5px; color: #8a9a91; }

/* what clients can book: kept short, full text on hover */
.day-preview { gap: 4px; margin: 0; font-size: 11.5px; line-height: 1.4; color: #6b7d73; }
.day-book { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.day-waste { padding: 6px 8px; border-radius: 8px; background: #fbf3d2; color: #8a6400; }

/* add / edit inside a day */
.day-action-link.day-add { justify-content: center; gap: 5px; min-height: 34px; margin-top: auto; border: 1.5px dashed #c6d9cd; border-radius: 11px; background: transparent; color: #1f7a4d; font-size: 13px; font-weight: 700; }
.day-action-link.day-add:hover { border-color: #004d3a; background: #fff; }
.slot-edit-form { flex-direction: column; flex-wrap: nowrap; align-items: stretch; gap: 6px; min-width: 0; padding: 10px; border: 1px solid #cfe6d7; border-radius: 12px; background: #fff; }
.slot-edit-form .time-input { width: 100%; min-height: 36px; border: 1px solid #d9e0dc; border-radius: 9px; font-size: 13px; }
.slot-edit-form .time-input:focus { outline: none; border-color: #004d3a; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.1); }
.slot-edit-form .time-sep { text-align: center; font-size: 11.5px; }
.slot-edit-form .form-btn { width: 100%; }
.slot-edit-form .save-error.in-form { flex-basis: auto; order: -1; margin: 0 0 2px; padding: 8px 10px; border-radius: 9px; background: #fdecec; color: #b4384a; font-size: 12px; line-height: 1.4; overflow-wrap: anywhere; }
.week-form .save-error.in-form { padding: 8px 12px; border-radius: 10px; background: #fdecec; color: #b4384a; }
.form-btn { min-height: 34px; border-radius: 10px; font-size: 13px; font-weight: 700; }
.form-btn.save { background: #004d3a; }
.form-btn.save:hover:not(:disabled) { background: #035a45; }
.form-btn.cancel { background: #f1f6f2; color: #004d3a; }

/* tip under the week */
.avail-hint.nm-note { display: flex; align-items: flex-start; gap: 8px; margin: 14px 0 0; padding: 0; border: none; background: none; font-size: 12.5px; line-height: 1.5; color: #6b7d73; }
.avail-hint .ic { margin-top: 1px; color: #3b5ba5; }

/* add hours for all week */
.week-form { gap: 14px; margin: 0 0 16px; padding: 18px 20px; border: 1.5px solid #cfe6d7; border-radius: 18px; background: #f1f8f4; }
.week-label { width: 56px; font-size: 12.5px; font-weight: 700; color: #22362c; }
.week-form .time-input { min-height: 40px; padding: 0 10px; border: 1px solid #d9e0dc; border-radius: 10px; font-size: 14px; }
.day-chip { min-height: 36px; padding: 0 14px; border-color: #dce8e0; font-size: 13px; font-weight: 700; }
.day-chip.on { background: #004d3a; border-color: #004d3a; color: #fff; }
.chip-link { color: #004d3a; font-size: 13px; font-weight: 700; }
.week-form-actions .form-btn { min-height: 40px; padding: 0 18px; }
.page-header .day-action-link { min-height: 42px; padding: 0 18px; border-radius: 12px; background: #004d3a; color: #fff; font-size: 14px; font-weight: 800; }

/* block time off */
.block-panel { margin-top: 22px; padding: 22px 24px; border: 1px solid #e4ebe6; border-radius: 20px; background: #fff; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -22px rgba(16, 35, 27, 0.3); }
.block-header { align-items: center; gap: 14px; margin-bottom: 18px; }
.block-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; background: #fbf3d2; color: #9a7300; display: inline-flex; align-items: center; justify-content: center; }
.block-icon { margin: 0; color: #9a7300; }
.block-title { margin: 0 0 2px; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; color: #0e3a2c; }
.block-desc { font-size: 13.5px; color: #6b7d73; }
.block-form { grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-bottom: 14px; }
.field label, .field-label { font-size: 12.5px; font-weight: 700; color: #22362c; }
.optional { font-weight: 500; color: #8a9a91; }
.field input, .nm-select.block { min-height: 44px; border: 1px solid #d9e0dc; border-radius: 10px; font-size: 14px; }
.field input:focus { border-color: #004d3a; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.1); }
.seg { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; height: 44px; padding: 4px; border: none; border-radius: 12px; background: #f1f6f2; }
.seg button { display: inline-flex; align-items: center; justify-content: center; gap: 6px; padding: 0 8px; border-radius: 9px; font-size: 13px; font-weight: 700; color: #3e5046; }
.seg button.on { background: #004d3a; color: #fff; }
.seg button.on .ic { color: #efbf04; }
.block-btn { min-height: 44px; padding: 0 22px; border-radius: 12px; background: #004d3a; font-size: 14px; font-weight: 800; }
.block-btn:hover:not(:disabled) { background: #035a45; }
.block-btn:disabled { opacity: 1; background: #c9d8cf; }
.conflicts { border-radius: 12px; }
.blocked-list { gap: 8px; }
.blocked-item { padding: 12px 14px; border: 1px solid #edf2ee; border-left: 4px solid #efbf04; border-radius: 12px; background: #fffdf6; font-size: 13.5px; }
.blocked-dates { color: #0e3a2c; }
.blocked-time { padding: 3px 10px; border-radius: 999px; background: #fbf3d2; color: #8a6400; font-size: 12.5px; font-weight: 700; }
.remove-block-btn { width: 30px; height: 30px; align-items: center; justify-content: center; border-radius: 50%; }
.remove-block-btn:hover { background: #fdecec; color: #b4384a; }
.block-empty { padding: 12px 14px; border: 1.5px dashed #dce5df; border-radius: 12px; font-size: 13px; color: #8a9a91; }

@media (max-width: 1200px) { .day-list { grid-template-columns: repeat(4, minmax(0, 1fr)); } }
@media (max-width: 900px) {
  .day-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .day-row { flex-wrap: nowrap; }
  .day-content { flex-basis: auto; order: 0; }
}
@media (max-width: 560px) {
  .day-list { grid-template-columns: minmax(0, 1fr); }
  .block-panel { padding: 18px 14px; }
}

/* clearer: open days stand out, closed days step back */
.day-row, .day-row:first-child { background: #fff; border: 1px solid #dfe8e2; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 10px 22px -18px rgba(16, 35, 27, 0.35); }
.day-row:not(.empty) { border-top: 4px solid #1f7a4d; }
.day-row.today { background: #f1f8f4; border-color: #9fcbb1; border-top-color: #efbf04; }
.day-row.empty { background: #f6f8f7; border-style: dashed; border-color: #d6dfda; box-shadow: none; }
.day-row.empty:not(.today) .day-name { color: #8a9a91; }
.day-row.empty .day-head small { display: none; }
.day-name { font-size: 16px; }
.day-head { padding-bottom: 8px; border-bottom-color: #e3ebe6; }
.day-head small { padding: 3px 9px; border-radius: 999px; background: #e3efe7; color: #004d3a; font-size: 12px; font-weight: 800; }
.empty-note-inline { padding: 14px 0; font-size: 13px; font-weight: 700; color: #9aa8a0; letter-spacing: 0.3px; }
.slot-pill { padding: 11px 28px 11px 12px; background: #f1f8f4; border-color: #bfdccb; }
.slot-pill:hover { background: #e9f4ee; }
.sp-from { font-size: 15px; }
.sp-to { font-size: 13px; color: #3e5046; }
.day-preview { font-size: 12.5px; color: #3e5046; }
.day-action-link.day-add { min-height: 36px; font-size: 13.5px; }
.day-row.empty .day-action-link.day-add { border-color: #b7cbbf; background: #fff; }
.av-sum span { height: 36px; padding: 0 14px; background: #fff; border: 1px solid #dfe8e2; font-size: 13.5px; }

/* bigger text + stronger borders */
.day-row, .day-row:first-child { border: 1.5px solid #b9d3c3; }
.day-row:not(.empty) { border-top: 5px solid #1f7a4d; }
.day-row.today { border-color: #8fc0a3; border-top-color: #efbf04; }
.day-row.empty { border: 1.5px dashed #a9bbb1; background: #f3f6f4; }
.day-row.empty:not(.today) .day-name { color: #4a5a52; }
.day-name { font-size: 18px; color: #0e3a2c; }
.today-tag { font-size: 11px; padding: 3px 8px; }
.day-head { border-bottom: 1.5px solid #d3e0d8; }
.day-head small { font-size: 13px; padding: 4px 10px; background: #d6eadd; }
.empty-note-inline { font-size: 14.5px; color: #5f7067; }
.slot-pill { border: 1.5px solid #8fc0a3; border-left: 5px solid #1f7a4d; }
.sp-from { font-size: 17px; }
.sp-to { font-size: 14px; font-weight: 700; color: #22362c; }
.slot-pill .pill-icon-btn { width: 24px; height: 24px; color: #4a5a52; }
.day-preview { font-size: 13.5px; line-height: 1.45; color: #22362c; }
.day-action-link.day-add { min-height: 40px; border: 1.5px dashed #7fae92; font-size: 14.5px; color: #004d3a; }
.day-row.empty .day-action-link.day-add { border-color: #7fae92; }
.av-sum span { height: 38px; border: 1.5px solid #b9d3c3; font-size: 14.5px; color: #22362c; }
.avail-hint.nm-note { font-size: 13.5px; color: #3e5046; }
.block-desc { font-size: 14px; color: #3e5046; }
.field label, .field-label { font-size: 13.5px; }
.field input, .nm-select.block { border: 1.5px solid #b9c9bf; }
.seg button { font-size: 14px; }
.blocked-item { font-size: 14.5px; border: 1.5px solid #d3e0d8; border-left: 5px solid #efbf04; }
.block-empty { border: 1.5px dashed #a9bbb1; font-size: 14px; color: #4a5a52; }
</style>