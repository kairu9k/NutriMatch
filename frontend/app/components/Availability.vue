<template>
  <div>
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Weekly Availability</h1>
        <p class="page-subtitle">Set the hours clients can book consultations with you.</p>
      </div>
      <button class="add-slot-btn" @click="addSlot(week[0].day)"><Plus :size="16" /> Add Time Slot</button>
    </div>

    <!-- WEEKLY DAY ROWS -->
    <div class="day-list">
      <div v-for="day in week" :key="day.day" class="day-row" :class="{ 'day-row-blocked': day.blocked }">
        <span class="day-name" :class="{ 'day-name-blocked': day.blocked }">{{ day.day }}</span>

        <div class="day-content">
          <template v-if="day.blocked">
            <span class="blocked-pill">Blocked — No Availability</span>
          </template>
          <template v-else>
            <span v-for="slot in day.slots" :key="slot.id" class="slot-pill">
              {{ slot.start }} – {{ slot.end }}
              <button class="pill-icon-btn" @click="editSlot(day, slot)"><Pencil :size="12" /></button>
              <button class="pill-icon-btn" @click="removeSlot(day, slot)"><X :size="13" /></button>
            </span>
          </template>
        </div>

        <button v-if="day.blocked" class="day-action-link" @click="unblockDay(day)">Unblock Day</button>
        <button v-else class="day-action-link" @click="addSlot(day.day)">+ Add Slot</button>
      </div>
    </div>

    <!-- BLOCK A DAY OFF -->
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
          <span class="blocked-dates">{{ formatDate(b.from) }}<template v-if="b.to"> – {{ formatDate(b.to) }}</template></span>
          <span v-if="b.reason" class="blocked-reason">{{ b.reason }}</span>
          <button class="remove-block-btn" @click="removeBlock(b)"><X :size="14" /></button>
        </div>
      </div>
      <p v-else class="empty-note">No blocked dates yet.</p>
    </div>
  </div>
</template>

<script setup>
import { Plus, Pencil, X, CalendarOff } from 'lucide-vue-next'
import { db } from '~/mock/mockDatabase'

definePageMeta({ layout: 'dashboard', title: 'Availability' })

// Deep-copy so edits here don't mutate the shared mock db directly
const week = reactive(structuredClone(db.weeklyAvailabilityFull))
const blocks = reactive(structuredClone(db.blockedDaysOff)
)

function addSlot(dayName) {
  const day = week.find(d => d.day === dayName)
  if (!day || day.blocked) return
  day.slots.push({ id: 's' + Date.now(), start: '9:00 AM', end: '5:00 PM' })
}
function removeSlot(day, slot) {
  day.slots = day.slots.filter(s => s.id !== slot.id)
}
function editSlot(day, slot) {
  // TODO: replace with a real time picker — for now this is a stub
  console.log('Edit slot', day.day, slot)
}
function unblockDay(day) {
  day.blocked = false
}

const newBlock = ref({ from: '', to: '', reason: '' })

function submitBlock() {
  if (!newBlock.value.from) return
  blocks.push({
    id: 'off-' + Date.now(),
    from: newBlock.value.from,
    to: newBlock.value.to,
    reason: newBlock.value.reason
  })
  newBlock.value = { from: '', to: '', reason: '' }
}
function removeBlock(b) {
  const idx = blocks.findIndex(x => x.id === b.id)
  if (idx > -1) blocks.splice(idx, 1)
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #1a3a1a; margin: 0 0 4px; }
.page-subtitle { font-size: 0.88rem; color: #8a9a8a; margin: 0; }

.add-slot-btn {
  display: flex; align-items: center; gap: 6px;
  background: #D4A017; border: none; color: #1a3a1a;
  padding: 11px 20px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer; white-space: nowrap;
}
.add-slot-btn:hover { background: #c4920f; }

.day-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px; }

.day-row {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 16px 20px; display: flex; align-items: center; gap: 16px;
}
.day-row-blocked { background: #fafafa; }

.day-name { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; width: 100px; flex-shrink: 0; }
.day-name-blocked { color: #9aaa9a; font-weight: 600; }

.day-content { flex: 1; display: flex; flex-wrap: wrap; gap: 10px; }

.slot-pill {
  display: flex; align-items: center; gap: 6px;
  background: #e6f4e6; color: #1a5a2a; font-size: 0.82rem; font-weight: 600;
  padding: 6px 10px 6px 14px; border-radius: 20px;
}
.pill-icon-btn {
  background: none; border: none; color: #4a8a5a; cursor: pointer;
  display: flex; align-items: center; justify-content: center; padding: 2px;
}
.pill-icon-btn:hover { color: #1a5a2a; }

.blocked-pill {
  background: #fbe1de; color: #c0483a; font-size: 0.8rem; font-weight: 700;
  padding: 6px 14px; border-radius: 20px;
}

.day-action-link {
  background: none; border: none; color: #1a6a2a;
  font-size: 0.82rem; font-weight: 600; cursor: pointer; white-space: nowrap; flex-shrink: 0;
}
.day-row-blocked .day-action-link { color: #9aaa9a; }
.day-action-link:hover { text-decoration: underline; }

/* BLOCK A DAY OFF */
.block-panel { background: #eef3ee; border-radius: 12px; padding: 22px; }
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

.empty-note { font-size: 0.82rem; color: #8a9a8a; margin: 0; }

@media (max-width: 900px) {
  .block-form { grid-template-columns: 1fr; }
  .day-row { flex-wrap: wrap; }
}
</style>