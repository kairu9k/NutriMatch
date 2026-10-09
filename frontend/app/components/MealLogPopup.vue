<template>
  <Teleport to="body">
    <div class="ml-overlay" @click.self="emit('close')">
      <div class="ml-box">
        <div class="ml-header">
          <div>
            <h2 class="ml-title">Meal Log</h2>
            <p class="ml-sub">{{ log ? `${log.meal_label} · ${formatDate(log.log_date)}` : 'Loading…' }}</p>
          </div>
          <div v-if="log" class="ml-chip">
            <span class="ml-avatar">{{ initials(log.client_name) }}</span>
            {{ log.client_name }}
          </div>
        </div>

        <p v-if="error" class="ml-error">{{ error }}</p>

        <template v-else-if="log">
          <div class="ml-status-row">
            <span class="ml-status" :class="`ml-status-${log.status}`">{{ log.status_label }}</span>
            <span class="ml-meta">Logged at {{ formatTime(log.time_logged) || '—' }}{{ log.scheduled_time ? ` · scheduled ${formatTime(log.scheduled_time)}` : '' }}</span>
          </div>

          <span class="ml-eyebrow">WHAT THE CLIENT ATE</span>
          <a v-if="log.photo_url" :href="log.photo_url" target="_blank" rel="noopener" class="ml-photo-link" title="Open full size">
            <img :src="log.photo_url" :alt="`${log.client_name}'s ${log.meal_label.toLowerCase()}`" class="ml-photo" />
          </a>
          <p v-else class="ml-no-photo"><ImageOff :size="16" /> No photo was uploaded for this meal.</p>

          <template v-if="log.reason_notes">
            <label class="ml-label">Client's note</label>
            <p class="ml-note">{{ log.reason_notes }}</p>
          </template>

          <span class="ml-eyebrow">WHAT WAS PLANNED · {{ log.plan_name }}</span>
          <ul v-if="log.planned_items.length" class="ml-planned">
            <li v-for="(item, i) in log.planned_items" :key="i">
              <span>{{ item.food_name }}<span v-if="item.household_measure" class="ml-measure"> · {{ item.household_measure }}</span></span>
              <span v-if="item.kcal" class="ml-kcal">{{ Math.round(item.kcal) }} kcal</span>
            </li>
          </ul>
          <p v-else class="ml-no-photo">No foods were planned for this meal.</p>

          <div class="ml-actions">
            <button class="ml-secondary-btn" type="button" @click="emit('close')">Close</button>
            <button class="ml-primary-btn" type="button" @click="openChart">Open Patient Chart</button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
// One client meal log, opened from an RND's "Meal log update" notification:
// the photo and status the client logged next to what was planned. Shows the
// copy that came with the notification right away, then refreshes it from
// GET /api/rnd/meal-logs/<id>/ (the client may have edited the log since).
import { onMounted, ref } from 'vue'
import { ImageOff } from 'lucide-vue-next'

const props = defineProps({
  mealLogId: { type: Number, required: true },
  initial: { type: Object, default: null },
})
const emit = defineEmits(['close'])

const { get } = useApi()
const log = ref(props.initial)
const error = ref('')

onMounted(async () => {
  try {
    log.value = await get(`/rnd/meal-logs/${props.mealLogId}/`)
  } catch {
    if (!log.value) error.value = 'Could not load this meal log. It may have been removed.'
  }
})

function openChart() {
  emit('close')
  navigateTo(`/client-detail/${log.value.relationship_id}`)
}
function initials(name) {
  return (name || '').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}
function formatDate(iso) {
  return iso ? new Date(`${iso}T00:00:00`).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' }) : ''
}
function formatTime(t) {
  if (!t) return ''
  const [h, m] = t.split(':').map(Number)
  return new Date(2000, 0, 1, h, m).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}
</script>

<style scoped>
* { box-sizing: border-box; }

.ml-overlay {
  position: fixed; inset: 0; background: rgba(20,30,20,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 200; padding: 20px;
}
.ml-box {
  background: #fff; border-radius: 16px; width: 100%; max-width: 520px; max-height: 90vh; overflow-y: auto;
  padding: 28px; font-family: 'Inter', sans-serif;
}
.ml-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px solid #eceeec; }
.ml-title { font-family: 'Playfair Display', serif; font-size: 1.3rem; color: #1a3a1a; margin: 0 0 4px; }
.ml-sub { font-size: 0.82rem; color: #8a9a8a; margin: 0; }
.ml-chip {
  display: flex; align-items: center; gap: 8px; border: 1px solid #e5e8e5; border-radius: 20px;
  padding: 6px 14px 6px 6px; font-size: 0.82rem; font-weight: 700; color: #1a3a1a; white-space: nowrap;
}
.ml-avatar {
  width: 26px; height: 26px; border-radius: 50%; background: #14301a; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700;
}
.ml-error { background: #fdecec; border: 1px solid #f3b8b8; color: #a12525; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; }

.ml-status-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 18px; }
.ml-status { font-size: 0.74rem; font-weight: 700; padding: 4px 12px; border-radius: 14px; }
.ml-status-followed { background: #e3f3ea; color: #1f8f5c; }
.ml-status-partially_followed { background: #fdf1d6; color: #b8860b; }
.ml-status-not_followed { background: #fbe1de; color: #c0483a; }
.ml-meta { font-size: 0.8rem; color: #6a7a6a; }

.ml-eyebrow { display: block; font-size: 0.68rem; letter-spacing: 0.08em; color: #b8860b; font-weight: 700; margin: 4px 0 10px; }
.ml-photo-link { display: block; margin-bottom: 16px; }
.ml-photo { width: 100%; max-height: 300px; object-fit: cover; border-radius: 12px; border: 1px solid #eceeec; display: block; }
.ml-no-photo { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; color: #8a9a8a; background: #f7f8f7; border-radius: 10px; padding: 14px 16px; margin: 0 0 16px; }
.ml-label { display: block; font-size: 0.82rem; font-weight: 600; color: #2a2a2a; margin: 0 0 6px; }
.ml-note { font-size: 0.85rem; color: #4a5a4a; background: #f4f6f4; border-radius: 8px; padding: 11px 14px; margin: 0 0 18px; }

.ml-planned { list-style: none; padding: 0; margin: 0 0 20px; border: 1px solid #eceeec; border-radius: 10px; }
.ml-planned li { display: flex; justify-content: space-between; gap: 12px; padding: 10px 14px; font-size: 0.85rem; color: #1a3a1a; border-bottom: 1px solid #f2f4f2; }
.ml-planned li:last-child { border-bottom: none; }
.ml-measure { color: #8a9a8a; }
.ml-kcal { color: #8a9a8a; white-space: nowrap; }

.ml-actions { display: flex; gap: 12px; }
.ml-secondary-btn {
  border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 8px;
  padding: 11px 20px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.ml-primary-btn {
  flex: 1; background: #14301a; color: #fff; border: none; border-radius: 8px;
  padding: 12px 20px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}
@media (max-width: 600px) { .ml-header { flex-direction: column; } }
</style>
