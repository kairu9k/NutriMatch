<template>
  <!-- A small trend line (one series, so no legend: the heading above names it).
       Hover or focus shows the month's value; screen readers get the table. -->
  <div class="spark" @mouseleave="hover = null">
    <svg :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none" class="spark-svg" role="img" :aria-label="summary">
      <line :x1="0" :x2="W" :y1="H - PAD" :y2="H - PAD" class="base" />
      <polyline :points="line" class="trend" />
      <circle v-if="pts.length" :cx="pts[pts.length - 1].x" :cy="pts[pts.length - 1].y" r="3.5" class="last" />
      <circle v-if="hover !== null" :cx="pts[hover].x" :cy="pts[hover].y" r="4" class="hover-dot" />
      <!-- hit areas, wider than the marks -->
      <rect
        v-for="(p, i) in pts" :key="i" :x="p.x - step / 2" y="0" :width="step" :height="H" class="hit"
        tabindex="0" :aria-label="`${points[i].month}: ${format(points[i].value)}`"
        @mouseenter="hover = i" @focus="hover = i" @blur="hover = null"
      />
    </svg>
    <div class="spark-axis"><span>{{ points[0]?.month }}</span><span>{{ points[points.length - 1]?.month }}</span></div>
    <div v-if="hover !== null" class="tip" :style="{ left: `${(pts[hover].x / W) * 100}%` }">
      <strong>{{ format(points[hover].value) }}</strong> {{ points[hover].month }}
    </div>
    <table class="sr-only">
      <caption>{{ label }}</caption>
      <tr v-for="p in points" :key="p.month"><th scope="row">{{ p.month }}</th><td>{{ format(p.value) }}</td></tr>
    </table>
  </div>
</template>

<script setup>
const props = defineProps({
  points: { type: Array, required: true }, // [{ month, value }]
  label: { type: String, required: true },
  format: { type: Function, default: v => String(v) },
})
const W = 200
const H = 48
const PAD = 6
const hover = ref(null)
const step = computed(() => (props.points.length > 1 ? W / (props.points.length - 1) : W))
const pts = computed(() => {
  const vals = props.points.map(p => Number(p.value) || 0)
  const max = Math.max(...vals, 1)
  return vals.map((v, i) => ({
    x: props.points.length > 1 ? (i / (props.points.length - 1)) * (W - 8) + 4 : W / 2,
    y: H - PAD - (v / max) * (H - PAD * 2 - 4),
  }))
})
const line = computed(() => pts.value.map(p => `${p.x},${p.y}`).join(' '))
const summary = computed(() => `${props.label}: ${props.points.map(p => `${p.month} ${props.format(p.value)}`).join(', ')}`)
</script>

<style scoped>
.spark { position: relative; }
.spark-svg { display: block; width: 100%; height: 48px; overflow: visible; }
.base { stroke: #d9e3dc; stroke-width: 1; }
.trend { fill: none; stroke: #1f8f5c; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; vector-effect: non-scaling-stroke; }
.last { fill: #0a4a37; stroke: #fff; stroke-width: 2; vector-effect: non-scaling-stroke; }
.hover-dot { fill: #fff; stroke: #0a4a37; stroke-width: 2; vector-effect: non-scaling-stroke; }
.hit { fill: transparent; cursor: default; outline: none; }
.spark-axis { display: flex; justify-content: space-between; font-size: 0.7rem; color: #6a7a6a; margin-top: 2px; }
.tip {
  position: absolute; bottom: calc(100% - 4px); transform: translateX(-50%); white-space: nowrap; pointer-events: none;
  background: #1a3a1a; color: #fff; font-size: 0.72rem; border-radius: 6px; padding: 4px 8px;
}
.tip strong { font-weight: 700; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
</style>
