<template>
  <!-- One strip under a dashboard banner: a label (Urgent / To do), how many things
       need attention, the first two, and a button that opens the full list in a
       pop-up. The client, RND and admin dashboards all use it (2026-10-25), and
       the pop-up is one design for all three: sections ("Your to-do", ...), each
       item an icon, its title, a line of detail and its button on the right.
       Icons: red triangle = urgent (pay soon, a patient at risk), gold dot = to
       do, grey "i" = for information. -->
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
        <template v-for="g in shownGroups" :key="g.title">
          <h3 class="na-h">{{ g.title }}</h3>
          <p v-if="g.sub" class="na-sub">{{ g.sub }}</p>
          <p v-if="!g.items.length" class="na-none">{{ g.empty || 'Nothing here right now.' }}</p>
          <ul v-else class="na-list">
            <li v-for="a in g.items" :key="a.key" class="na-item" :class="a.tone || 'todo'">
              <component :is="ICONS[a.tone || 'todo']" :size="16" class="na-icon" aria-hidden="true" />
              <span class="na-main">
                <strong>{{ noDot(a.title) }}</strong>
                <small v-if="a.detail">{{ a.detail }}</small>
                <small v-if="a.extra" class="na-extra">{{ a.extra }}</small>
              </span>
              <NuxtLink :to="a.to" :class="a.tone === 'info' ? 'nm-btn-soft nm-btn-sm' : 'nm-btn-dark nm-btn-sm'" @click="close">{{ a.action || 'Open' }}</NuxtLink>
            </li>
          </ul>
        </template>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="open = false">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { AlertTriangle, CheckCircle2, CircleDot, Info, X } from 'lucide-vue-next'

const props = defineProps({
  // [{ title, sub?, empty?, always?, items: [{ key, title, detail?, extra?, to, action?, tone: 'urgent' | 'todo' | 'info', critical? }] }]
  // tone sets the icon; `critical` (or tone urgent) turns the strip red "Urgent".
  // A section with no items is left out unless `always` (then it says `empty`).
  groups: { type: Array, required: true },
  clearText: { type: String, default: 'All caught up. Nothing needs you right now.' },
})

const ICONS = { urgent: AlertTriangle, todo: CircleDot, info: Info }
const open = ref(false)
const close = () => { open.value = false }
const noDot = t => String(t || '').replace(/[.\s]+$/, '')

const shownGroups = computed(() => props.groups.filter(g => g.items.length || g.always))
const items = computed(() => props.groups.flatMap(g => g.items))
const count = computed(() => items.value.length)
const isUrgent = a => a.tone === 'urgent' || a.critical
const urgent = computed(() => items.value.some(isUrgent))
const tone = computed(() => (urgent.value ? 'risk' : 'todo'))
// "2 unpaid consultations starting within 24 h, 1 RND application to review, and 2 more."
// urgent ones first, whatever section they're in
const summaryText = computed(() => {
  const ordered = [...items.value.filter(isUrgent), ...items.value.filter(a => !isUrgent(a))]
  const t = ordered.map(a => noDot(a.title)).filter(Boolean)
  if (!t.length) return ''
  const shown = t.slice(0, 2).join(', ')
  return t.length > 2 ? `${shown}, and ${t.length - 2} more.` : `${shown}.`
})
function onKey(e) {
  if (e.key === 'Escape') close()
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
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

/* the pop-up list (the admin dashboard's design, 2026-10-25) */
.na-modal { max-width: 560px; }
.na-h { font-size: 0.92rem; font-weight: 700; margin: 4px 0 8px; color: #1a3a1a; }
.na-sub { font-size: 0.8rem; color: #6a7a6a; margin: -4px 0 10px; }
.na-none { margin: 0 0 18px; font-size: 0.84rem; color: #6a7a6a; }
.na-list { list-style: none; margin: 0 0 18px; padding: 0; }
.na-item { display: flex; align-items: flex-start; gap: 10px; padding: 12px 0; border-top: 1px solid #d9e3dc; }
.na-item:first-child { border-top: none; padding-top: 0; }
.na-icon { flex-shrink: 0; margin-top: 2px; }
.na-item.todo .na-icon { color: #a37a0b; }
.na-item.info .na-icon { color: #6a7a6a; }
.na-item.urgent .na-icon { color: #c0392b; }
.na-item.urgent strong { color: #a12525; }
.na-main { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.na-main strong { font-size: 0.86rem; color: #1a3a1a; overflow-wrap: anywhere; }
.na-main small { font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; overflow-wrap: anywhere; }
.na-main .na-extra { color: #4a5a4a; }
.na-item > a { flex-shrink: 0; white-space: nowrap; }

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
  .na-item { flex-wrap: wrap; }
  .na-item > a { margin-left: 26px; }
}
</style>
