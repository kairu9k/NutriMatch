<template>
  <div class="trend">
    <ul v-if="series.length > 1" class="legend" aria-label="Legend">
      <li v-for="(s, i) in series" :key="s.key"><span class="swatch" :style="{ background: colorOf(i) }" />{{ s.label }}</li>
    </ul>
    <div class="plot" @mouseleave="hover = null">
      <svg :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none" class="svg" role="img" :aria-label="ariaLabel">
        <line v-for="t in scale.ticks" :key="t" x1="0" :x2="W" :y1="y(t)" :y2="y(t)" class="grid" />
        <line v-for="r in refLines" :key="`r${r.value}`" x1="0" :x2="W" :y1="y(r.value)" :y2="y(r.value)" class="ref" />
        <polyline v-for="(s, i) in series" :key="s.key" :points="s.points.map(p => `${x(p.date)},${y(p.value)}`).join(' ')"
                  class="line" :style="{ stroke: colorOf(i) }" />
      </svg>
      <span v-for="t in scale.ticks" :key="`t${t}`" class="tick" :style="{ top: `${(y(t) / H) * 100}%` }">{{ fmtTick(t) }}</span>
      <span v-for="r in refLines" :key="`rl${r.value}`" class="ref-label" :style="{ top: `${(y(r.value) / H) * 100}%` }">{{ r.label }}</span>
      <template v-for="(s, i) in series" :key="`d${s.key}`">
        <button v-for="(p, j) in s.points" :key="j" type="button" class="dot"
                :class="{ on: hover && hover.s === i && hover.p === j }"
                :style="{ left: `${(x(p.date) / W) * 100}%`, top: `${(y(p.value) / H) * 100}%`, borderColor: colorOf(i), '--c': colorOf(i) }"
                :aria-label="`${s.label}, ${dateLabel(p.date)}: ${fmt(p.value)} ${unit}${p.note ? ` (${p.note})` : ''}`"
                @mouseenter="hover = { s: i, p: j }" @focus="hover = { s: i, p: j }" @blur="hover = null" />
      </template>
      <div v-if="hoverPoint" class="tip" :class="{ flip: x(hoverPoint.date) > W * 0.6 }"
           :style="{ left: `${(x(hoverPoint.date) / W) * 100}%`, top: `${(y(hoverPoint.value) / H) * 100}%` }">
        <strong>{{ fmt(hoverPoint.value) }} {{ unit }}</strong>
        <span>{{ series.length > 1 ? `${series[hover.s].label} · ` : '' }}{{ dateLabel(hoverPoint.date) }}{{ hoverPoint.note ? ` · ${hoverPoint.note}` : '' }}</span>
      </div>
    </div>
    <div class="xaxis"><span>{{ dateLabel(span.first) }}</span><span>{{ dateLabel(span.last) }}</span></div>
    <table class="sr-only">
      <caption>{{ ariaLabel }}</caption>
      <thead><tr><th>Date</th><th v-for="s in series" :key="s.key">{{ s.label }} ({{ unit }})</th></tr></thead>
      <tbody><tr v-for="d in allDates" :key="d"><td>{{ dateLabel(d) }}</td><td v-for="s in series" :key="s.key">{{ s.points.find(p => p.date === d)?.value ?? '—' }}</td></tr></tbody>
    </table>
  </div>
</template>

<script setup>
// Line chart for progress trends: one or more series of { date: 'YYYY-MM-DD',
// value, note? } on a shared time axis. One series = one green line, no
// legend; several (BP, lipids) get a legend and fixed colors in order.
// Hover/focus a point for its value; a hidden table carries the data for
// screen readers.
const props = defineProps({
  series: { type: Array, required: true }, // [{ key, label, points: [{date, value, note}] }]
  unit: { type: String, default: '' },
  decimals: { type: Number, default: 1 },
  refLines: { type: Array, default: () => [] }, // [{ value, label }] e.g. a goal or cut-off
  title: { type: String, default: 'Trend' },
})

const W = 600
const H = 180
const PAD = 14
const COLORS = ['#1f8f5c', '#b8730b', '#2f6fa8', '#a33e7a'] // fixed order — never by rank
const colorOf = i => COLORS[i % COLORS.length]
const hover = ref(null)

const allPoints = computed(() => props.series.flatMap(s => s.points))
const allDates = computed(() => [...new Set(allPoints.value.map(p => p.date))].sort())
const span = computed(() => ({ first: allDates.value[0], last: allDates.value[allDates.value.length - 1] }))
const tOf = d => new Date(`${d}T00:00:00`).getTime()
function x(date) {
  const t0 = tOf(span.value.first)
  const t1 = tOf(span.value.last)
  return PAD + (t1 === t0 ? 0.5 : (tOf(date) - t0) / (t1 - t0)) * (W - PAD * 2)
}
const scale = computed(() => {
  const vals = [...allPoints.value.map(p => p.value), ...props.refLines.map(r => r.value)]
  let lo = Math.min(...vals)
  let hi = Math.max(...vals)
  const pad = Math.max((hi - lo) * 0.12, Math.abs(hi) * 0.02, 0.5)
  lo -= pad
  hi += pad
  const step = niceStep((hi - lo) / 3)
  lo = Math.floor(lo / step) * step
  hi = Math.ceil(hi / step) * step
  const ticks = []
  for (let v = lo; v <= hi + step / 2; v += step) ticks.push(Number(v.toFixed(4)))
  return { lo, hi, ticks }
})
function niceStep(raw) {
  const p = 10 ** Math.floor(Math.log10(raw || 1))
  const n = raw / p
  return (n <= 1 ? 1 : n <= 2 ? 2 : n <= 2.5 ? 2.5 : n <= 5 ? 5 : 10) * p
}
const y = v => PAD + (1 - (v - scale.value.lo) / (scale.value.hi - scale.value.lo || 1)) * (H - PAD * 2)

const hoverPoint = computed(() => (hover.value ? props.series[hover.value.s]?.points[hover.value.p] : null))
const fmt = v => Number(v).toFixed(props.decimals).replace(/\.0+$/, '')
const fmtTick = v => (Math.abs(v) >= 100 ? Math.round(v) : Number(v.toFixed(1)))
const dateLabel = d => (d ? new Date(`${d}T00:00:00`).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }) : '')
const ariaLabel = computed(() => `${props.title}: ${props.series.map(s => `${s.label} from ${fmt(s.points[0].value)} to ${fmt(s.points[s.points.length - 1].value)} ${props.unit}`).join('; ')}`)
</script>

<style scoped>
.legend { display: flex; gap: 14px; flex-wrap: wrap; list-style: none; margin: 0 0 8px; padding: 0; font-size: 0.76rem; color: #3a4a3a; }
.legend li { display: inline-flex; align-items: center; gap: 6px; }
.swatch { width: 14px; height: 3px; border-radius: 2px; }
.plot { position: relative; height: 180px; margin-left: 38px; }
.svg { width: 100%; height: 100%; display: block; overflow: visible; }
.grid { stroke: #eef1ee; stroke-width: 1; vector-effect: non-scaling-stroke; }
.ref { stroke: #8a9a8a; stroke-width: 1; stroke-dasharray: 4 3; vector-effect: non-scaling-stroke; }
.line { fill: none; stroke-width: 2; vector-effect: non-scaling-stroke; stroke-linejoin: round; stroke-linecap: round; }
.tick { position: absolute; left: -38px; width: 32px; text-align: right; transform: translateY(-50%); font-size: 0.68rem; color: #9aaa9a; font-variant-numeric: tabular-nums; }
.ref-label { position: absolute; right: 0; transform: translateY(-120%); font-size: 0.66rem; font-weight: 600; color: #6a7a6a; background: #fff; padding: 0 4px; }
.dot { position: absolute; width: 10px; height: 10px; margin: -5px 0 0 -5px; border-radius: 50%; background: #fff; border: 2px solid; padding: 0; cursor: default; }
.dot::after { content: ''; position: absolute; inset: -8px; }
.dot.on { background: var(--c); box-shadow: 0 0 0 2px #fff; }
.tip { position: absolute; transform: translate(12px, -50%); background: #1a3a1a; color: #fff; border-radius: 8px; padding: 7px 10px; font-size: 0.74rem; white-space: nowrap; display: flex; flex-direction: column; gap: 2px; z-index: 5; pointer-events: none; box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15); }
.tip span { color: #b9cdbf; }
.tip.flip { transform: translate(calc(-100% - 12px), -50%); }
.xaxis { display: flex; justify-content: space-between; margin-left: 38px; border-top: 1px solid #dfe5df; padding-top: 6px; font-size: 0.7rem; color: #8a9a8a; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
</style>
