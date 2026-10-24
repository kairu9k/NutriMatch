<template>
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="emit('close')">
      <div class="nm-modal ml-box" role="dialog" aria-modal="true" :aria-label="log ? title : 'Meal log'">
        <div class="ml-header nm-modal-head">
          <div class="ml-head-text">
            <h2 class="ml-title">{{ log ? title : 'Meal log' }}</h2>
            <p class="ml-sub">{{ log ? subLine : 'Loading…' }}</p>
            <span v-if="log" class="ml-status" :class="`ml-status-${log.status || 'waiting'}`">{{ log.status_label }}</span>
          </div>
          <button type="button" aria-label="Close" @click="emit('close')"><X :size="18" aria-hidden="true" /></button>
        </div>

        <p v-if="error" class="ml-error">{{ error }}</p>

        <template v-else-if="log">
          <section class="ml-sec">
            <h3 class="ml-h">What they ate</h3>
            <a v-if="log.photo_url" :href="log.photo_url" target="_blank" rel="noopener" class="ml-photo-link" title="Open full size">
              <img :src="log.photo_url" :alt="`${log.client_name}'s ${log.meal_label.toLowerCase()}`" class="ml-photo" />
            </a>
            <p v-else class="ml-empty"><ImageOff :size="16" /> No photo was uploaded for this meal.</p>
            <p v-if="log.reason_notes" class="ml-note">{{ log.reason_notes }}</p>
          </section>

          <section class="ml-sec">
            <h3 class="ml-h">What was planned</h3>
            <p class="ml-hsub">{{ log.plan_name }}</p>
            <ul v-if="log.planned_items.length" class="ml-planned">
              <li v-for="(item, i) in log.planned_items" :key="i">
                <span>{{ item.food_name }}<span v-if="item.household_measure" class="ml-measure">, {{ item.household_measure }}</span></span>
                <span v-if="item.kcal" class="ml-kcal">{{ Math.round(item.kcal) }} kcal</span>
              </li>
            </ul>
            <p v-else class="ml-empty">No foods were planned for this meal.</p>
          </section>

          <section v-if="log.can_review !== false" class="ml-sec">
            <h3 class="ml-h">Your rating</h3>
            <p class="ml-hsub">How well did this meal follow the plan? It counts toward their adherence once rated.</p>
            <MealLogRating :log-id="log.id" :status="log.status" :label="`${log.client_name}'s ${log.meal_label.toLowerCase()}`" @rated="onRated" />
          </section>

          <div class="nm-modal-actions ml-actions">
            <button class="ml-primary-btn" type="button" @click="openChart">Open patient chart</button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
// One client meal log, opened from an RND's "Meal log to review" notification:
// the photo and note the client logged next to what was planned, and the
// RND's rating (Followed / Partly / Not followed). Shows the
// copy that came with the notification right away, then refreshes it from
// GET /api/rnd/meal-logs/<id>/ (the client may have edited the log since).
import { computed, onMounted, ref } from 'vue'
import { ImageOff, X } from 'lucide-vue-next'

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

// "Ana Cruz's breakfast" / "Friday, October 23, logged 8:05 AM, planned for 7:00 AM"
const title = computed(() => `${log.value.client_name}'s ${log.value.meal_label.toLowerCase()}`)
const subLine = computed(() => {
  const l = log.value
  const parts = [formatDate(l.log_date)]
  if (l.time_logged) parts.push(`logged ${formatTime(l.time_logged)}`)
  if (l.scheduled_time) parts.push(`planned for ${formatTime(l.scheduled_time)}`)
  return parts.join(', ')
})

function onRated(updated) {
  log.value = { ...log.value, ...updated }
}
function openChart() {
  emit('close')
  navigateTo(`/client-detail/${log.value.relationship_id}`)
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

.ml-box { max-width: 520px; }
.ml-header { display: flex; align-items: flex-start; gap: 12px; }
.ml-head-text { flex: 1; min-width: 0; }
.ml-title { font-family: 'Playfair Display', serif; font-size: 1.35rem; font-weight: 700; line-height: 1.2; color: #1a3a1a; margin: 0 0 4px; }
.ml-sub { font-size: 0.84rem; color: #6a7a6a; margin: 0 0 10px; }
.ml-error { background: #fdecec; border: 1px solid #f3b8b8; color: #a12525; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin-top: 16px; }

.ml-status { display: inline-block; font-size: 0.74rem; font-weight: 700; padding: 3px 11px; border-radius: 14px; }
.ml-status-followed { background: #e3f3ea; color: #1f8f5c; }
.ml-status-partially_followed { background: #fdf1d6; color: #8a6508; }
.ml-status-not_followed { background: #fbe1de; color: #b23b2e; }
.ml-status-waiting { background: #eceeec; color: #5a6a5a; }

.ml-sec { padding: 18px 0 0; }
.ml-sec + .ml-sec { margin-top: 18px; border-top: 1px solid #eef1ee; }
.ml-h { font-size: 0.95rem; font-weight: 700; color: #1a3a1a; margin: 0 0 8px; }
.ml-hsub { font-size: 0.82rem; color: #6a7a6a; margin: -4px 0 10px; }
.ml-photo-link { display: block; }
.ml-photo { width: 100%; max-height: 300px; object-fit: cover; border-radius: 12px; border: 1px solid #eceeec; display: block; }
.ml-empty { display: flex; align-items: center; gap: 8px; font-size: 0.84rem; color: #7a8a7a; background: #f7f9f7; border-radius: 10px; padding: 14px 16px; margin: 0; }
.ml-note { font-size: 0.86rem; color: #3a4a3a; margin: 12px 0 0; padding-left: 10px; border-left: 2px solid #d9e3dc; line-height: 1.5; white-space: pre-line; overflow-wrap: anywhere; }

.ml-planned { list-style: none; padding: 0; margin: 0; border: 1px solid #d9e3dc; border-radius: 10px; }
.ml-planned li { display: flex; justify-content: space-between; gap: 12px; padding: 10px 14px; font-size: 0.86rem; color: #1a3a1a; border-bottom: 1px solid #eef1ee; }
.ml-planned li:last-child { border-bottom: none; }
.ml-measure { color: #7a8a7a; }
.ml-kcal { color: #7a8a7a; white-space: nowrap; font-variant-numeric: tabular-nums; }

.ml-actions { flex-wrap: nowrap; }
.ml-primary-btn {
  flex: 1; background: #0a4a37; color: #fff; border: none; border-radius: 8px;
  min-height: 40px; padding: 0 20px; font-weight: 600; font-size: 0.86rem; cursor: pointer; font-family: inherit;
}
.ml-primary-btn:hover { background: #00382a; }
.ml-primary-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
</style>
