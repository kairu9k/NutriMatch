<template>
  <svg :viewBox="`0 0 ${width} ${height}`" class="trend-svg" preserveAspectRatio="none">
    <path :d="areaPath" :fill="color" fill-opacity="0.08" stroke="none" />
    <path :d="linePath" :stroke="color" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    <circle v-for="(p, i) in coords" :key="i" :cx="p.x" :cy="p.y" r="3.5" :fill="i === coords.length - 1 ? goldColor : color" />
  </svg>
  <div class="trend-labels">
    <span v-for="p in points" :key="p.label">{{ p.label }}</span>
  </div>
</template>

<script setup>
const props = defineProps({
  points: { type: Array, required: true }, // [{ label, value }]
  color: { type: String, default: '#1a3a1a' },
})

const width = 400
const height = 120
const padding = 12
const goldColor = '#D4A017'

const values = computed(() => props.points.map(p => p.value))
const minVal = computed(() => Math.min(...values.value))
const maxVal = computed(() => Math.max(...values.value))
const range = computed(() => (maxVal.value - minVal.value) || 1)

const coords = computed(() => {
  const n = props.points.length
  return props.points.map((p, i) => {
    const x = n === 1 ? width / 2 : padding + (i / (n - 1)) * (width - padding * 2)
    const y = height - padding - ((p.value - minVal.value) / range.value) * (height - padding * 2)
    return { x, y }
  })
})

const linePath = computed(() =>
  coords.value.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.x},${c.y}`).join(' ')
)

const areaPath = computed(() => {
  if (!coords.value.length) return ''
  const first = coords.value[0]
  const last = coords.value.at(-1)
  return `M${first.x},${height - padding} ${linePath.value.replace('M', 'L')} L${last.x},${height - padding} Z`
})
</script>

<style scoped>
.trend-svg { width: 100%; height: 120px; display: block; }
.trend-labels {
  display: flex; justify-content: space-between; font-size: 0.68rem; color: #9aaa9a; margin-top: 6px;
}
</style>
