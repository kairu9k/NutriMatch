<template>
  <div>
    <!-- PAGE HEADER (hidden when embedded in Profile Settings, which has its own) -->
    <div v-if="!embedded" class="page-header">
      <div>
        <h1 class="page-title">Weekly availability</h1>
        <p class="page-subtitle">Set the hours clients can book consultations with you.</p>
      </div>
    </div>

    <!-- WEEKLY DAY ROWS -->
    <div v-if="loading" class="empty-note">Loading…</div>
    <div v-else class="day-list">
      <div v-for="day in week" :key="day.dayIndex" class="day-row">
        <span class="day-name">{{ day.day }}</span>

        <div class="day-content">
          <template v-if="day.slots.length">
            <template v-for="slot in day.slots" :key="slot.id">
              <div v-if="editingId === slot.id" class="slot-edit-form">
                <input v-model="editForm.start_time" type="time" class="time-input" />
                <span class="time-sep">to</span>
                <input v-model="editForm.end_time" type="time" class="time-input" />
                <button class="form-btn save" @click="saveEdit(slot)">Save</button>
                <button class="form-btn cancel" @click="cancelEdit">Cancel</button>
              </div>
              <button v-else class="slot-pill" type="button" @click="startEdit(slot)">
                {{ formatTime(slot.start_time) }} – {{ formatTime(slot.end_time) }}
                <span class="pill-icon-btn" role="button" :aria-label="`Remove ${formatTime(slot.start_time)} to ${formatTime(slot.end_time)}`" @click.stop="removeSlot(slot)"><X :size="13" /></span>
              </button>
            </template>
          </template>
          <span v-else class="empty-note-inline">No hours set</span>

          <div v-if="addingDay === day.dayIndex" class="slot-edit-form">
            <input v-model="addForm.start_time" type="time" class="time-input" />
            <span class="time-sep">to</span>
            <input v-model="addForm.end_time" type="time" class="time-input" />
            <button class="form-btn save" @click="confirmAddSlot(day.dayIndex)">Add</button>
            <button class="form-btn cancel" @click="addingDay = null">Cancel</button>
          </div>
        </div>

        <button v-if="addingDay !== day.dayIndex" class="day-action-link" @click="startAddSlot(day.dayIndex)"><Plus :size="14" aria-hidden="true" /> Add hours</button>
      </div>
    </div>

    <p v-if="saveError" class="save-error">{{ saveError }}</p>

    <!-- BLOCK TIME OFF — whole days or part of a day on specific dates
         (RndTimeOff, /api/rnd/time-off/). Clients can't book it. -->
    <div class="block-panel">
      <div class="block-header">
        <CalendarOff :size="18" class="block-icon" aria-hidden="true" />
        <div>
          <h3 class="block-title">Block time off</h3>
          <p class="block-desc">Block whole days or part of a day, like a holiday, leave or a seminar afternoon. Clients can't book that time. Consultations already booked in it stay booked.</p>
        </div>
      </div>

      <div class="block-form">
        <div class="field">
          <label for="off-from">From</label>
          <input id="off-from" v-model="newBlock.from" type="date" :min="todayIso" />
        </div>
        <div class="field">
          <label for="off-to">To <span class="optional">(optional)</span></label>
          <input id="off-to" v-model="newBlock.to" type="date" :min="newBlock.from || todayIso" />
        </div>
        <div class="field">
          <span class="field-label">Time</span>
          <div class="seg" role="radiogroup" aria-label="Block the whole day or part of it">
            <button type="button" role="radio" :aria-checked="newBlock.wholeDay" :class="{ on: newBlock.wholeDay }" @click="newBlock.wholeDay = true">Whole day</button>
            <button type="button" role="radio" :aria-checked="!newBlock.wholeDay" :class="{ on: !newBlock.wholeDay }" @click="newBlock.wholeDay = false">Part of the day</button>
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
        <button class="block-btn" :disabled="!newBlock.from || !!blockRuleError || blockSaving" @click="submitBlock">{{ blockSaving ? 'Blocking…' : 'Block' }}</button>
      </div>
      <p v-if="blockRuleError || blockError" class="save-error" role="alert">{{ blockRuleError || blockError }}</p>
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
          <button class="remove-block-btn" :aria-label="`Remove time off on ${formatBlockDate(b.start_date)}`" @click="removeBlock(b)"><X :size="14" /></button>
        </div>
      </div>
      <p v-else class="empty-note">No time blocked off.</p>
    </div>
  </div>
</template>

<script setup>
import { phIso } from '~/utils/phTime'
import { computed, onMounted, reactive, ref } from 'vue'
import { X, CalendarOff, Plus } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Availability' })

defineProps({ embedded: { type: Boolean, default: false } })

const { get, post, patch, del } = useApi()

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

const slots = ref([])
const loading = ref(true)
const saveError = ref('')

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

function startAddSlot(dayIndex) {
  editingId.value = null
  addForm.start_time = '09:00'
  addForm.end_time = '17:00'
  addingDay.value = dayIndex
}

async function confirmAddSlot(dayIndex) {
  saveError.value = ''
  if (addForm.end_time <= addForm.start_time) {
    saveError.value = 'End time must be after start time.'
    return
  }
  try {
    const today = phIso()
    const created = await post('/rnd/availability/', {
      day_of_week: dayIndex,
      start_time: `${addForm.start_time}:00`,
      end_time: `${addForm.end_time}:00`,
      is_available: true,
      effective_from: today,
    })
    slots.value.push(created)
    addingDay.value = null
  } catch {
    saveError.value = 'Could not add slot. Please try again.'
  }
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
  saveError.value = ''
  if (editForm.end_time <= editForm.start_time) {
    saveError.value = 'End time must be after start time.'
    return
  }
  try {
    const updated = await patch(`/rnd/availability/${slot.id}/`, {
      start_time: `${editForm.start_time}:00`,
      end_time: `${editForm.end_time}:00`,
    })
    const idx = slots.value.findIndex(s => s.id === slot.id)
    if (idx !== -1) slots.value[idx] = updated
    editingId.value = null
  } catch {
    saveError.value = 'Could not update slot. Please try again.'
  }
}

async function removeSlot(slot) {
  saveError.value = ''
  try {
    await del(`/rnd/availability/${slot.id}/`)
    slots.value = slots.value.filter(s => s.id !== slot.id)
  } catch {
    saveError.value = 'Could not remove slot. Please try again.'
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
const blockError = ref('')
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
    return hours.length && (b.wholeDay || hours.some(s => s.start_time.slice(0, 5) < b.endTime && s.end_time.slice(0, 5) > b.startTime))
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
  blockError.value = ''
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
  } catch (e) {
    blockError.value = apiError(e, 'Could not block that time. Please try again.')
  } finally {
    blockSaving.value = false
  }
}
async function removeBlock(b) {
  blockError.value = ''
  try {
    await del(`/rnd/time-off/${b.id}/`)
    blocks.value = blocks.value.filter(x => x.id !== b.id)
  } catch (e) {
    blockError.value = apiError(e, 'Could not remove that time off.')
  }
}
function formatBlockDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
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
.form-btn.save:hover { background: #00382a; }
.form-btn.cancel { background: #e3efe7; color: #0a4a37; }
.form-btn.cancel:hover { background: #d3e7da; }

.empty-note-inline { font-size: 0.82rem; color: #8a9a8a; }

.day-action-link {
  display: inline-flex; align-items: center; gap: 4px; background: #e3efe7; border: none; border-radius: 8px; color: #0a4a37; font-family: inherit;
  font-size: 0.78rem; font-weight: 600; cursor: pointer; white-space: nowrap; flex-shrink: 0; min-height: 32px; padding: 0 12px;
}
.day-action-link:hover { background: #d3e7da; }
.day-action-link:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

.empty-note { font-size: 0.82rem; color: #6a7a6a; margin: 0; }
.save-error { font-size: 0.82rem; color: #c0483a; margin: 12px 0 0; }

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
</style>
