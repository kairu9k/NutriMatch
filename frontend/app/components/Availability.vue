<template>
  <div>
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Weekly Availability</h1>
        <p class="page-subtitle">Set the hours clients can book consultations with you.</p>
      </div>
      <button class="add-slot-btn" @click="addSlot(week[0].dayIndex)"><Plus :size="16" /> Add Time Slot</button>
    </div>

    <!-- WEEKLY DAY ROWS -->
    <div v-if="loading" class="empty-note">Loading…</div>
    <div v-else class="day-list">
      <div v-for="day in week" :key="day.dayIndex" class="day-row">
        <span class="day-name">{{ day.day }}</span>

        <div class="day-content">
          <template v-if="day.slots.length">
            <span v-for="slot in day.slots" :key="slot.id" class="slot-pill">
              {{ formatTime(slot.start_time) }} – {{ formatTime(slot.end_time) }}
              <button class="pill-icon-btn" @click="removeSlot(slot)"><X :size="13" /></button>
            </span>
          </template>
          <span v-else class="empty-note-inline">No hours set</span>
        </div>

        <button class="day-action-link" @click="addSlot(day.dayIndex)">+ Add Slot</button>
      </div>
    </div>

    <p v-if="saveError" class="save-error">{{ saveError }}</p>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Plus, X } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Availability' })

const { get, post, del } = useApi()

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

const slots = ref([])
const loading = ref(true)
const saveError = ref('')

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

async function addSlot(dayIndex) {
  saveError.value = ''
  try {
    const today = new Date().toISOString().slice(0, 10)
    const created = await post('/rnd/availability/', {
      day_of_week: dayIndex,
      start_time: '09:00:00',
      end_time: '17:00:00',
      is_available: true,
      effective_from: today,
    })
    slots.value.push(created)
  } catch {
    saveError.value = 'Could not add slot. Please try again.'
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

.day-name { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; width: 100px; flex-shrink: 0; }

.day-content { flex: 1; display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }

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

.empty-note-inline { font-size: 0.82rem; color: #9aaa9a; }

.day-action-link {
  background: none; border: none; color: #1a6a2a;
  font-size: 0.82rem; font-weight: 600; cursor: pointer; white-space: nowrap; flex-shrink: 0;
}
.day-action-link:hover { text-decoration: underline; }

.empty-note { font-size: 0.82rem; color: #8a9a8a; margin: 0; }
.save-error { font-size: 0.82rem; color: #c0483a; margin: 12px 0 0; }

@media (max-width: 900px) {
  .day-row { flex-wrap: wrap; }
}
</style>