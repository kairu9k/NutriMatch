<template>
  <div class="wh">
    <div class="wh-form">
      <div class="wh-row">
        <span class="wh-label">Hours</span>
        <input v-model="start" type="time" class="wh-time" aria-label="Start time" />
        <span class="wh-to">to</span>
        <input v-model="end" type="time" class="wh-time" aria-label="End time" />
      </div>
      <div class="wh-row">
        <span class="wh-label">Days</span>
        <div class="wh-days" role="group" aria-label="Days to add these hours to">
          <button v-for="d in ORDER" :key="d" type="button" class="wh-day" :class="{ on: days.includes(d) }" :aria-pressed="days.includes(d)" @click="toggleDay(d)">{{ NAMES[d].slice(0, 3) }}</button>
        </div>
        <button type="button" class="wh-link" @click="days = [1, 2, 3, 4, 5]">Weekdays</button>
        <button type="button" class="wh-link" @click="days = [...ORDER]">Every day</button>
      </div>
      <div class="wh-actions">
        <button type="button" class="nm-btn-dark nm-btn-sm" :disabled="!days.length" @click="add">
          Add to {{ days.length || 'no' }} day{{ days.length === 1 ? '' : 's' }}
        </button>
      </div>
      <p v-if="problem" class="wh-problem" role="alert">{{ problem }}</p>
    </div>

    <p class="nm-note plain-note wh-hint">
      Taking a lunch break? Add your morning and afternoon as two blocks, for example 8:00 AM to 12:00 PM and 1:00 PM to 5:00 PM.
      For hours that end at midnight, use 12:00 AM. Clients book one-hour sessions from the start of each block.
    </p>

    <ul class="wh-list">
      <li v-for="d in ORDER" :key="d" class="wh-day-row">
        <span class="wh-name">{{ NAMES[d] }}</span>
        <span v-if="!blocksOn(d).length" class="wh-none">No hours</span>
        <span v-for="b in blocksOn(d)" :key="`${b.start_time}-${b.end_time}`" class="wh-pill">
          {{ fmt(b.start_time) }} to {{ fmt(b.end_time) }}
          <button type="button" class="wh-x" :aria-label="`Remove ${NAMES[d]} ${fmt(b.start_time)} to ${fmt(b.end_time)}`" @click="remove(b)"><X :size="13" aria-hidden="true" /></button>
        </span>
      </li>
    </ul>
  </div>
</template>

<script setup>
// Weekly hours kept in memory until the RND finishes onboarding (nothing is
// saved before that). Same rules as the API (profiles/hours.py): each block at
// least an hour, no overlaps on a day, 12:00 AM as an end time means midnight.
import { ref } from 'vue'
import { X } from 'lucide-vue-next'

const model = defineModel({ type: Array, default: () => [] })

const NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
const ORDER = [1, 2, 3, 4, 5, 6, 0]
const start = ref('09:00')
const end = ref('17:00')
const days = ref([1, 2, 3, 4, 5])
const problem = ref('')

const startMin = t => Number(t.slice(0, 2)) * 60 + Number(t.slice(3, 5))
const endMin = t => (t.slice(0, 5) === '00:00' ? 1440 : startMin(t))
function fmt(t) {
  const h = Number(t.slice(0, 2))
  const m = t.slice(3, 5)
  return `${h % 12 || 12}:${m} ${h < 12 ? 'AM' : 'PM'}`
}
const blocksOn = d => model.value.filter(b => b.day_of_week === d).sort((a, b) => startMin(a.start_time) - startMin(b.start_time))
function toggleDay(d) {
  days.value = days.value.includes(d) ? days.value.filter(x => x !== d) : [...days.value, d]
}
function add() {
  problem.value = ''
  if (!start.value || !end.value) { problem.value = 'Choose a start and an end time.'; return }
  if (endMin(end.value) - startMin(start.value) < 60) { problem.value = 'Each block of hours must be at least 1 hour long, because a consultation is one hour.'; return }
  const next = [...model.value]
  const skipped = []
  for (const d of ORDER.filter(x => days.value.includes(x))) {
    const clash = blocksOn(d).some(b => startMin(start.value) < endMin(b.end_time) && startMin(b.start_time) < endMin(end.value))
    if (clash) skipped.push(NAMES[d])
    else next.push({ day_of_week: d, start_time: start.value, end_time: end.value })
  }
  model.value = next
  if (skipped.length) problem.value = `${skipped.join(', ')} already ha${skipped.length === 1 ? 's' : 've'} hours that overlap, so ${skipped.length === 1 ? 'it was' : 'they were'} skipped.`
}
function remove(b) {
  model.value = model.value.filter(x => x !== b)
}
</script>

<style scoped>
.wh { display: flex; flex-direction: column; gap: 14px; }
.wh-form { border: 1px solid #d9e3dc; border-radius: 12px; padding: 14px; display: flex; flex-direction: column; gap: 12px; background: #fff; }
.wh-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.wh-label { width: 44px; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; }
.wh-time { border: 1px solid #d5dad5; border-radius: 8px; padding: 8px 10px; font: inherit; font-size: 0.88rem; color: #1a3a1a; background: #fff; }
.wh-to { font-size: 0.84rem; color: #6a7a6a; }
.wh-days { display: flex; gap: 6px; flex-wrap: wrap; }
.wh-day { min-width: 44px; min-height: 34px; border: 1.5px solid #d9e3dc; border-radius: 999px; background: #fff; color: #4a5a4a; font: inherit; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.wh-day.on { border-color: #0a4a37; background: #e3efe7; color: #0a4a37; }
.wh-link { border: 0; background: none; padding: 4px 6px; font: inherit; font-size: 0.8rem; font-weight: 600; color: #0a4a37; text-decoration: underline; cursor: pointer; }
.wh-actions { display: flex; }
.wh-problem { margin: 0; font-size: 0.82rem; color: #a12525; }
.wh-hint { margin: 0; font-size: 0.84rem; }
.wh-list { list-style: none; margin: 0; padding: 0; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; background: #fff; }
.wh-day-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 10px 14px; border-top: 1px solid #d9e3dc; }
.wh-day-row:first-child { border-top: 0; }
.wh-name { width: 96px; font-size: 0.86rem; font-weight: 600; color: #1a3a1a; }
.wh-none { font-size: 0.82rem; color: #8a9a8a; }
.wh-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 6px 4px 12px; border-radius: 999px; background: #e3efe7; color: #0a4a37; font-size: 0.82rem; font-weight: 600; }
.wh-x { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border: 0; border-radius: 50%; background: transparent; color: #0a4a37; cursor: pointer; }
.wh-x:hover { background: #cfe3d6; }
@media (max-width: 640px) {
  .wh-name { width: 100%; }
}
</style>
