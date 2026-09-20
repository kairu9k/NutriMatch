<template>
  <div>
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Weekly Availability</h1>
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
                <span class="time-sep">–</span>
                <input v-model="editForm.end_time" type="time" class="time-input" />
                <button class="form-btn save" @click="saveEdit(slot)">Save</button>
                <button class="form-btn cancel" @click="cancelEdit">Cancel</button>
              </div>
              <button v-else class="slot-pill" type="button" @click="startEdit(slot)">
                {{ formatTime(slot.start_time) }} – {{ formatTime(slot.end_time) }}
                <span class="pill-icon-btn" @click.stop="removeSlot(slot)"><X :size="13" /></span>
              </button>
            </template>
          </template>
          <span v-else class="empty-note-inline">No hours set</span>

          <div v-if="addingDay === day.dayIndex" class="slot-edit-form">
            <input v-model="addForm.start_time" type="time" class="time-input" />
            <span class="time-sep">–</span>
            <input v-model="addForm.end_time" type="time" class="time-input" />
            <button class="form-btn save" @click="confirmAddSlot(day.dayIndex)">Add</button>
            <button class="form-btn cancel" @click="addingDay = null">Cancel</button>
          </div>
        </div>

        <button v-if="addingDay !== day.dayIndex" class="day-action-link" @click="startAddSlot(day.dayIndex)">+ Add Slot</button>
      </div>
    </div>

    <p v-if="saveError" class="save-error">{{ saveError }}</p>

    <!-- BLOCK A DAY OFF — mock/local only, no backend model for date-range
         blocks yet (see RndAvailabilitySchedule in vault/database.txt). -->
    <div class="block-panel">
      <div class="block-header">
        <CalendarOff :size="18" class="block-icon" />
        <div>
          <h3 class="block-title">Block a Day Off</h3>
          <p class="block-desc">Quickly mark a specific date range as unavailable — useful for holidays, leave, or emergencies. Existing bookings within the range are not auto-cancelled.</p>
        </div>
      </div>

      <div class="block-form">
        <div class="field">
          <label>From</label>
          <input v-model="newBlock.from" type="date" />
        </div>
        <div class="field">
          <label>To <span class="optional">(optional)</span></label>
          <input v-model="newBlock.to" type="date" />
        </div>
        <div class="field field-wide">
          <label>Reason <span class="optional">(optional)</span></label>
          <input v-model="newBlock.reason" type="text" placeholder="e.g. Annual leave" />
        </div>
        <button class="block-btn" :disabled="!newBlock.from" @click="submitBlock">Block</button>
      </div>

      <div v-if="blocks.length" class="blocked-list">
        <div v-for="b in blocks" :key="b.id" class="blocked-item">
          <span class="blocked-dates">{{ formatBlockDate(b.from) }}<template v-if="b.to"> – {{ formatBlockDate(b.to) }}</template></span>
          <span v-if="b.reason" class="blocked-reason">{{ b.reason }}</span>
          <button class="remove-block-btn" @click="removeBlock(b)"><X :size="14" /></button>
        </div>
      </div>
      <p v-else class="empty-note">No blocked dates yet.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { X, CalendarOff } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Availability' })

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
    slots.value = await get('/rnd/availability/')
  } finally {
    loading.value = false
  }
})

const week = computed(() =>
  DAY_NAMES.map((day, dayIndex) => ({
    day,
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
    const today = new Date().toISOString().slice(0, 10)
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

/* ---------- BLOCK A DAY OFF — local-only state, no backend model yet ---------- */
const blocks = reactive([])
const newBlock = ref({ from: '', to: '', reason: '' })

function submitBlock() {
  if (!newBlock.value.from) return
  blocks.push({
    id: 'off-' + Date.now(),
    from: newBlock.value.from,
    to: newBlock.value.to,
    reason: newBlock.value.reason,
  })
  newBlock.value = { from: '', to: '', reason: '' }
}
function removeBlock(b) {
  const idx = blocks.findIndex(x => x.id === b.id)
  if (idx > -1) blocks.splice(idx, 1)
}
function formatBlockDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #1a3a1a; margin: 0 0 4px; }
.page-subtitle { font-size: 0.88rem; color: #8a9a8a; margin: 0; }

.day-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }

.day-row {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 16px 20px; display: flex; align-items: center; gap: 16px;
}

.day-name { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; width: 100px; flex-shrink: 0; }

.day-content { flex: 1; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }

.slot-pill {
  display: flex; align-items: center; gap: 6px;
  background: #e6f4e6; color: #1a5a2a; font-size: 0.82rem; font-weight: 600;
  padding: 6px 10px 6px 14px; border-radius: 20px; border: none; cursor: pointer;
}
.slot-pill:hover { background: #d5ecd5; }
.pill-icon-btn {
  background: none; border: none; color: #4a8a5a; cursor: pointer;
  display: flex; align-items: center; justify-content: center; padding: 2px;
}
.pill-icon-btn:hover { color: #1a5a2a; }

.slot-edit-form { display: flex; align-items: center; gap: 8px; background: #f6f8f4; border-radius: 10px; padding: 6px 10px; }
.time-input {
  border: 1px solid #d5dad5; border-radius: 6px; padding: 5px 8px;
  font-size: 0.82rem; color: #1a3a1a; background: #fff;
}
.time-sep { color: #8a9a8a; font-size: 0.82rem; }
.form-btn {
  border: none; border-radius: 6px; padding: 5px 12px; font-size: 0.8rem; font-weight: 700; cursor: pointer;
}
.form-btn.save { background: #D4A017; color: #1a3a1a; }
.form-btn.save:hover { background: #c4920f; }
.form-btn.cancel { background: none; color: #8a9a8a; }
.form-btn.cancel:hover { color: #4a5a4a; }

.empty-note-inline { font-size: 0.82rem; color: #9aaa9a; }

.day-action-link {
  background: none; border: none; color: #1a6a2a;
  font-size: 0.82rem; font-weight: 600; cursor: pointer; white-space: nowrap; flex-shrink: 0;
}
.day-action-link:hover { text-decoration: underline; }

.empty-note { font-size: 0.82rem; color: #8a9a8a; margin: 0; }
.save-error { font-size: 0.82rem; color: #c0483a; margin: 12px 0 0; }

/* BLOCK A DAY OFF */
.block-panel { background: #eef3ee; border-radius: 12px; padding: 22px; margin-top: 20px; }
.block-header { display: flex; gap: 12px; margin-bottom: 20px; }
.block-icon { color: #1a3a1a; flex-shrink: 0; margin-top: 2px; }
.block-title { font-size: 0.98rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.block-desc { font-size: 0.82rem; color: #6a7a6a; line-height: 1.5; margin: 0; max-width: 640px; }

.block-form { display: grid; grid-template-columns: 1fr 1fr 1.4fr auto; gap: 14px; align-items: end; margin-bottom: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.78rem; font-weight: 600; color: #4a5a4a; }
.optional { font-weight: 400; color: #9aaa9a; }
.field input {
  border: 1px solid #dde3dd; border-radius: 8px; padding: 10px 12px;
  font-size: 0.85rem; font-family: inherit; background: #fff; color: #1a3a1a;
}

.block-btn {
  background: #fff; border: 1px solid #1a3a1a; color: #1a3a1a;
  padding: 10px 24px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer; white-space: nowrap;
}
.block-btn:hover:not(:disabled) { background: #1a3a1a; color: #fff; }
.block-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.blocked-list { display: flex; flex-direction: column; gap: 8px; }
.blocked-item {
  display: flex; align-items: center; gap: 12px;
  background: #fff; border-radius: 8px; padding: 10px 14px; font-size: 0.82rem;
}
.blocked-dates { font-weight: 700; color: #1a3a1a; }
.blocked-reason { color: #7a8a7a; flex: 1; }
.remove-block-btn { background: none; border: none; color: #9aaa9a; cursor: pointer; display: flex; }
.remove-block-btn:hover { color: #c0483a; }

@media (max-width: 900px) {
  .day-row { flex-wrap: wrap; }
  .block-form { grid-template-columns: 1fr; }
}
</style>
