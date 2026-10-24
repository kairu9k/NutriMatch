<template>
  <!-- One strip under a dashboard banner: a label (Urgent / To do), how many things
       need attention, the first two, and a button that opens the full list in a
       pop-up. The list itself is the page's own (default slot), so each dashboard
       keeps its rows. Used by the client, RND and admin dashboards. -->
  <div class="na">
  <section class="na-strip" aria-label="Needs attention">
    <p v-if="!count" class="na-clear"><CheckCircle2 :size="16" aria-hidden="true" /> {{ clearText }}</p>
    <div v-else class="na-row" :class="tone">
      <span class="na-tag" :class="tone">{{ urgent ? 'Urgent' : 'To do' }}</span>
      <span class="na-text"><strong>{{ count }} thing{{ count === 1 ? '' : 's' }} need{{ count === 1 ? 's' : '' }} your attention.</strong> {{ summaryText }}</span>
      <button type="button" class="nm-btn-dark nm-btn-sm na-open" aria-haspopup="dialog" @click="open = true">Needs attention ({{ count }})</button>
    </div>
  </section>

  <div v-if="open" class="nm-modal-overlay" @click.self="open = false">
    <div class="nm-modal na-modal" role="dialog" aria-modal="true" aria-labelledby="na-title">
      <button type="button" class="nm-modal-x" aria-label="Close" @click="open = false"><X :size="18" aria-hidden="true" /></button>
      <h2 id="na-title" class="nm-modal-title">Needs attention</h2>
      <!-- a click on any link inside closes the pop-up -->
      <div class="na-body" @click="onBodyClick"><slot :close="close" /></div>
      <div class="nm-modal-actions">
        <button type="button" class="nm-btn-soft" @click="open = false">Close</button>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup>
import { CheckCircle2, X } from 'lucide-vue-next'

const props = defineProps({
  count: { type: Number, required: true },
  urgent: { type: Boolean, default: false }, // something critical: red strip, "Urgent"
  titles: { type: Array, default: () => [] }, // every item's short title, most important first
  clearText: { type: String, default: 'All caught up. Nothing needs you right now.' },
})

const open = ref(false)
const close = () => { open.value = false }
const tone = computed(() => (props.urgent ? 'risk' : 'todo'))
// "2 unpaid consultations starting within 24 h, 1 RND application to review, and 2 more."
const summaryText = computed(() => {
  const t = props.titles.map(x => String(x).replace(/[.\s]+$/, '')).filter(Boolean)
  if (!t.length) return ''
  const shown = t.slice(0, 2).join(', ')
  return t.length > 2 ? `${shown}, and ${t.length - 2} more.` : `${shown}.`
})
function onBodyClick(e) {
  if (e.target.closest('a')) close()
}
function onKey(e) {
  if (e.key === 'Escape') close()
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
defineExpose({ close })
</script>

<style scoped>
.na-strip { background: #fff; border: 1px solid #d9e3dc; border-radius: 14px; overflow: hidden; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.na-clear { display: flex; align-items: center; gap: 8px; margin: 0; padding: 14px 20px; font-size: 0.86rem; font-weight: 600; color: #1f6f46; }
.na-row { display: flex; align-items: center; gap: 12px; padding: 12px 20px; font-size: 0.86rem; color: #3a4a3a; line-height: 1.45; }
.na-row.risk { background: #fdf3f2; }
.na-row strong { color: #1a3a1a; }
.na-row.risk strong { color: #a12525; }
.na-text { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.na-tag { flex-shrink: 0; padding: 2px 9px; border-radius: 999px; font-size: 0.74rem; font-weight: 700; line-height: 1.5; }
.na-tag.risk { background: #f6d9d6; color: #a12525; }
.na-tag.todo { background: #e3efe7; color: #0a4a37; }
.na-open { flex-shrink: 0; white-space: nowrap; font-family: inherit; cursor: pointer; }
.na-modal { max-width: 620px; }
/* the strip glows three times when it appears, red or green */
@media (prefers-reduced-motion: no-preference) {
  .na-row.risk { animation: na-risk 1s ease-in-out 0.45s 3; }
  .na-row.todo { animation: na-todo 1s ease-in-out 0.45s 3; }
}
@keyframes na-risk { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(192, 57, 43, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(192, 57, 43, 0.45), inset 0 0 18px rgba(192, 57, 43, 0.22); } }
@keyframes na-todo { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(63, 154, 107, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(63, 154, 107, 0.45), inset 0 0 18px rgba(63, 154, 107, 0.2); } }
@media (max-width: 560px) {
  .na-row { flex-wrap: wrap; padding: 12px 16px; }
  .na-text { flex-basis: 100%; }
}
</style>
