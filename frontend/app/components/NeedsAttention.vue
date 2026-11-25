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
        <span class="na-bell" :class="tone"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.7 21a2 2 0 0 1-3.4 0" /></svg></span>
        <span class="na-text">
          <span class="na-tag" :class="tone">{{ urgent ? 'Urgent' : 'To do' }}</span>
          <strong>{{ count }} thing{{ count === 1 ? '' : 's' }} need{{ count === 1 ? 's' : '' }} your attention</strong>
          <small class="na-sum">{{ summaryText }}</small>
        </span>
        <div class="na-cards">
          <NuxtLink v-for="a in cardItems" :key="a.key" :to="a.to" class="na-card" :class="a.tone || 'todo'">
            <span class="na-card-ico"><component :is="ICONS[a.tone || 'todo']" :size="17" aria-hidden="true" /></span>
            <span class="na-card-txt"><b v-if="splitTitle(a.title).n">{{ splitTitle(a.title).n }}</b>{{ splitTitle(a.title).rest }}</span>
            <span class="na-card-go">{{ a.action || 'Open' }} <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></span>
          </NuxtLink>
          <button type="button" class="nm-btn-dark nm-btn-sm na-open" aria-haspopup="dialog" @click="open = true">Needs attention ({{ count }})</button>
        </div>
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

/* ---------- UI only ---------- */
// the strip shows the first two to-dos as cards (urgent first; "for information" ones stay in the pop-up)
const cardItems = computed(() => [...items.value.filter(isUrgent), ...items.value.filter(a => !isUrgent(a) && a.tone !== 'info')].slice(0, 2))
// "4 refunds to send" → big "4", then "refunds to send"
function splitTitle(title) {
  const m = noDot(title).match(/^(\d+)\s+(.*)$/)
  return m ? { n: m[1], rest: m[2].charAt(0).toUpperCase() + m[2].slice(1) } : { n: '', rest: noDot(title) }
}
</script>
<style scoped>
.na { font-family: 'DM Sans', sans-serif; }
.na-strip { border-radius: 20px; overflow: hidden; background: #fffbea; border: 1.5px solid #f0d774; box-shadow: 0 10px 24px -18px rgba(196, 145, 2, 0.6); }
.na-clear { display: flex; align-items: center; gap: 10px; margin: 0; padding: 16px 20px; background: #fff; font-size: 14px; font-weight: 700; color: #1f6f46; }
.na-row { display: flex; align-items: center; flex-wrap: wrap; gap: 14px 16px; padding: 16px; line-height: 1.45; }
.na-row.risk { background: #fef3f2; }
.na-strip:has(.na-row.risk) { border-color: #eba79f; }
.na-bell { flex-shrink: 0; width: 46px; height: 46px; border-radius: 14px; background: #efbf04; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px -12px rgba(239, 191, 4, 0.9); }
.na-bell.risk { background: #c0392b; color: #fff; box-shadow: 0 10px 20px -12px rgba(192, 57, 43, 0.9); }
.na-text { flex: 1 1 260px; min-width: 0; display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
.na-tag { padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase; }
.na-tag.todo { background: #fff; color: #8a6500; box-shadow: 0 0 0 1px #f3e2a0; }
.na-tag.risk { background: #fde4e1; color: #b42318; }
.na-text strong { font-size: 15.5px; font-weight: 800; color: #3d3005; }
.na-row.risk .na-text strong { color: #8c1d2c; }
.na-sum { font-size: 13px; color: #6b5a1e; overflow-wrap: anywhere; }
.na-row.risk .na-sum { color: #8c1d2c; }

/* the first two to-dos, each with its button */
.na-cards { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; }
.na-card { display: flex; align-items: center; gap: 12px; padding: 8px 8px 8px 10px; border-radius: 16px; border: 1px solid #f3e2a0; background: #fff; text-decoration: none; box-shadow: 0 8px 18px -14px rgba(196, 145, 2, 0.7); transition: transform 0.15s; }
.na-card:hover { transform: translateY(-1px); }
.na-card:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.na-card-ico { flex-shrink: 0; width: 38px; height: 38px; border-radius: 12px; background: #fff4d6; color: #8a6500; display: inline-flex; align-items: center; justify-content: center; }
.na-card.urgent { border-color: #f6cfcb; }
.na-card.urgent .na-card-ico { background: #fdecea; color: #b42318; }
.na-card-txt { display: flex; flex-direction: column; min-width: 0; max-width: 200px; font-size: 12.5px; line-height: 1.3; color: #6b5a1e; }
.na-card-txt b { font-family: 'Playfair Display', serif; font-size: 20px; line-height: 1.1; color: #3d3005; font-variant-numeric: lining-nums; }
.na-card.urgent .na-card-txt b { color: #b42318; }
.na-card-go { flex-shrink: 0; display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 14px; border-radius: 11px; background: #004d3a; color: #fff; font-size: 13px; font-weight: 800; white-space: nowrap; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.na-open { display: inline-flex; align-items: center; height: 36px; padding: 0 14px; border: 1px solid #e7c65a; border-radius: 11px; background: transparent; color: #6b5a1e; font-family: inherit; font-size: 12.5px; font-weight: 800; white-space: nowrap; cursor: pointer; box-shadow: none; }
.na-open:hover { background: #fff4d6; }
.na-open:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

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

.na-modal { border-radius: 22px; }
.na-h { font-size: 15px; font-weight: 800; color: #0e3a2c; }
.na-item { align-items: center; padding: 12px; border: 1px solid #e3ebe6; border-radius: 14px; margin-bottom: 8px; }
.na-item:first-child { border-top: 1px solid #e3ebe6; padding-top: 12px; }
.na-item.urgent { background: #fef3f2; border-color: #f6cfcb; }
.na-item.todo { background: #fffbea; border-color: #f3e2a0; }
.na-item.todo .na-icon { color: #c49102; }
.na-main strong { font-size: 14px; color: #0e3a2c; }
.na-main small { font-size: 12.5px; color: #6b7d73; }

/* the strip glows three times when it appears */
@media (prefers-reduced-motion: no-preference) {
  .na-row.risk { animation: na-risk 1s ease-in-out 0.45s 3; }
  .na-row.todo { animation: na-todo 1s ease-in-out 0.45s 3; }
}
@keyframes na-risk { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(192, 57, 43, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(192, 57, 43, 0.45), inset 0 0 18px rgba(192, 57, 43, 0.22); } }
@keyframes na-todo { 0%, 100% { box-shadow: inset 0 0 0 0 rgba(239, 191, 4, 0); } 50% { box-shadow: inset 0 0 0 2px rgba(239, 191, 4, 0.5), inset 0 0 18px rgba(239, 191, 4, 0.22); } }

@media (max-width: 760px) {
  .na-strip { background: #fff; }
  .na-row { padding: 14px; gap: 12px; }
  .na-bell { width: 44px; height: 44px; }
  .na-text { flex-basis: calc(100% - 60px); }
  .na-cards { flex-direction: column; align-items: stretch; width: 100%; gap: 8px; }
  .na-card { background: #fffbea; }
  .na-card-txt { flex: 1; max-width: none; }
  .na-card-go { height: 34px; padding: 0 12px; }
  .na-open { justify-content: center; }
  .na-item { flex-wrap: wrap; }
  .na-item > a { margin-left: 26px; }
}
</style>