<template>
  <!-- The platform's day, on the admin banner (2026-10-25): every consultation
       today on one line, sized to its length, with a gold "Now" mark. Faint =
       done, white = paid, gold = not paid yet, dashed = waiting for the RND.
       Pointing at a block shows it in the line underneath, which otherwise
       names the next consultation. -->
  <div class="day">
    <p class="day-head">
      <template v-if="rows.length"><strong>{{ rows.length }}</strong> consultation{{ rows.length === 1 ? '' : 's' }} today<template v-if="toCome">, {{ toCome }} still to come</template></template>
      <template v-else>No consultations today</template>
    </p>

    <div class="track" :style="{ height: `${trackHeight}px` }">
      <span v-for="t in ticks" :key="t.h" class="tick" :class="{ hushed: nowPct != null && Math.abs(t.pct - nowPct) < 9 }" :style="{ left: `${t.pct}%` }" aria-hidden="true">{{ t.label }}</span>
      <span class="rail" :style="{ top: `${railTop}px` }" aria-hidden="true" />
      <ul class="slots" aria-label="Today's consultations">
        <li v-for="b in blocks" :key="b.id" :style="{ left: `${b.left}%`, width: `${b.width}%`, top: `${b.top}px` }">
          <NuxtLink
            :to="`/admin-appointments?view=all&search=${b.id}`" class="slot" :class="b.state" :aria-label="b.text"
            @mouseenter="focused = b" @mouseleave="focused = null" @focus="focused = b" @blur="focused = null"
          />
        </li>
      </ul>
      <span v-if="nowPct != null" class="now" :style="{ left: `${nowPct}%` }" aria-hidden="true"><i>Now</i></span>
    </div>

    <p class="day-detail" aria-live="polite">{{ focused ? focused.text : nextText }}</p>
    <ul v-if="rows.length" class="key" aria-hidden="true">
      <li><span class="sw done" />Done</li>
      <li><span class="sw paid" />Paid</li>
      <li><span class="sw unpaid" />Not paid yet</li>
      <li><span class="sw waiting" />Waiting for the RND</li>
    </ul>
  </div>
</template>

<script setup>
import { phHour, phIso } from '~/utils/phTime'

const props = defineProps({
  rows: { type: Array, default: () => [] }, // GET /admin/dashboard/ schedule.today
  next: { type: Object, default: null }, // schedule.next
  now: { type: Number, default: () => Date.now() },
})

const LANE = 12 // px per row of blocks; overlapping consultations stack
const GAP = 4
const focused = ref(null)

// minutes since midnight, Philippine time
const minuteOf = d => phHour(d) * 60 + d.getMinutes()
const clock = d => d.toLocaleTimeString('en-PH', { hour: 'numeric', minute: '2-digit' })

// 7 AM to 9 PM, widened to fit anything earlier or later
const range = computed(() => {
  let lo = 7 * 60
  let hi = 21 * 60
  for (const r of props.rows) {
    const s = minuteOf(new Date(r.scheduled_at))
    lo = Math.min(lo, Math.floor(s / 60) * 60)
    hi = Math.max(hi, Math.ceil((s + r.duration_minutes) / 60) * 60)
  }
  return { lo, hi: Math.min(hi, 24 * 60) }
})
const pct = m => ((m - range.value.lo) / (range.value.hi - range.value.lo)) * 100

const ticks = computed(() => {
  const out = []
  for (let h = range.value.lo / 60; h <= range.value.hi / 60; h += 3) {
    out.push({ h, pct: pct(h * 60), label: `${h % 12 || 12} ${h < 12 || h === 24 ? 'AM' : 'PM'}` })
  }
  return out
})

const WORD = { done: 'completed', paid: 'paid', unpaid: 'not paid yet', waiting: 'waiting for the RND to confirm' }
function describe(r, withDay = false) {
  const d = new Date(r.scheduled_at)
  const when = withDay && phIso(d) !== phIso(new Date(props.now))
    ? `${d.toLocaleDateString('en-PH', { weekday: 'short', month: 'short', day: 'numeric' })} at ${clock(d)}`
    : clock(d)
  return { when, rest: `${r.client} with RND ${r.rnd}, ${r.type.toLowerCase()}` }
}
function stateOf(r) {
  const end = new Date(r.scheduled_at).getTime() + r.duration_minutes * 60000
  if (r.status === 'completed' || end < props.now) return 'done'
  if (r.status === 'pending') return 'waiting'
  return r.paid ? 'paid' : 'unpaid'
}

// blocks, each in the first row (lane) where it doesn't overlap another
const blocks = computed(() => {
  const laneEnds = []
  return props.rows.map((r) => {
    const s = minuteOf(new Date(r.scheduled_at))
    const e = s + r.duration_minutes
    let lane = laneEnds.findIndex(end => end <= s)
    if (lane === -1) { lane = laneEnds.length; laneEnds.push(e) } else laneEnds[lane] = e
    const state = stateOf(r)
    const { when, rest } = describe(r)
    return {
      id: r.id, state, top: 20 + lane * (LANE + GAP),
      left: pct(s), width: Math.max(pct(e) - pct(s), 1.2),
      text: `${when}: ${rest}, ${WORD[state]}`,
    }
  })
})
const lanes = computed(() => Math.max(1, ...blocks.value.map(b => (b.top - 20) / (LANE + GAP) + 1)))
const trackHeight = computed(() => 20 + lanes.value * (LANE + GAP) + 2)
const railTop = computed(() => 20 + (lanes.value * (LANE + GAP) - GAP) / 2)

const nowPct = computed(() => {
  const m = minuteOf(new Date(props.now))
  return m >= range.value.lo && m <= range.value.hi ? pct(m) : null
})
const toCome = computed(() => props.rows.filter(r => new Date(r.scheduled_at).getTime() > props.now).length)
const nextText = computed(() => {
  if (!props.next) return props.rows.length ? 'Nothing else booked for now.' : 'Nothing booked in the next 30 days.'
  const { when, rest } = describe(props.next, true)
  const state = props.next.status === 'pending' ? 'waiting for the RND to confirm' : props.next.paid ? 'paid' : 'not paid yet'
  return `Next ${when.includes(' at ') ? 'on' : 'at'} ${when}: ${rest}, ${state}`
})
</script>

<style scoped>
.day { display: flex; flex-direction: column; gap: 10px; min-width: 0; color: #cfe0d5; }
.day-head { margin: 0; font-size: 14px; color: #e6efe9; }
.day-head strong { font-family: 'Playfair Display', serif; font-size: 22px; color: #fff; margin-right: 4px; font-variant-numeric: lining-nums; }

.track { position: relative; margin: 2px 6px 0; }
.tick { position: absolute; top: 0; transform: translateX(-50%); font-size: 11px; color: #9fbcab; white-space: nowrap; }
.tick::after { content: ''; position: absolute; left: 50%; top: 16px; width: 1px; height: 6px; background: rgba(255, 255, 255, 0.22); }
.tick.hushed { color: transparent; } /* the "Now" label sits there */
.rail { position: absolute; left: 0; right: 0; height: 2px; margin-top: -1px; background: rgba(255, 255, 255, 0.16); border-radius: 2px; }
.slots { list-style: none; margin: 0; padding: 0; }
.slots li { position: absolute; height: 12px; }
.slot { display: block; width: 100%; height: 100%; border-radius: 4px; outline: none; transition: transform 0.12s ease, box-shadow 0.12s ease; }
.slot:hover, .slot:focus-visible { transform: scaleY(1.35); box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.55); }
.slot.done, .sw.done { background: rgba(255, 255, 255, 0.32); }
.slot.paid, .sw.paid { background: #fff; }
.slot.unpaid, .sw.unpaid { background: #d4a017; }
/* dashed = still to do (design rule): the RND hasn't confirmed it yet */
.slot.waiting, .sw.waiting { background: transparent; border: 1.5px dashed #cfe0d5; box-sizing: border-box; }
.now { position: absolute; top: 14px; bottom: -4px; width: 2px; margin-left: -1px; background: #e2c25e; border-radius: 2px; pointer-events: none; }
.now i { position: absolute; bottom: 100%; left: 50%; transform: translate(-50%, -1px); font-style: normal; font-size: 10px; font-weight: 700; color: #e2c25e; background: #003f2f; padding: 0 3px; border-radius: 3px; }

.day-detail { margin: 2px 0 0; font-size: 13px; color: #fff; min-height: 1.5em; line-height: 1.5; overflow-wrap: anywhere; }
.key { display: flex; flex-wrap: wrap; gap: 4px 14px; list-style: none; margin: 0; padding: 0; font-size: 11px; color: #9fbcab; }
.key li { display: inline-flex; align-items: center; gap: 6px; }
.sw { display: inline-block; width: 14px; height: 8px; border-radius: 3px; }
.sw.waiting { border-width: 1px; }
@media (prefers-reduced-motion: reduce) { .slot { transition: none; } }
</style>
