<template>
  <!-- The "↗ +60%" badge beside a this-month figure (admin and RND dashboards).
       Up is green, a drop or no change is plain grey (not a warning). When last
       month was zero there is no percentage, so it shows the difference instead
       ("↗ +₱1,440.00", "↗ +2"). -->
  <span class="change" :class="up ? 'up' : 'flat'">
    <component :is="icon" :size="13" aria-hidden="true" /> {{ text }}
  </span>
</template>

<script setup>
import { Minus, TrendingDown, TrendingUp } from 'lucide-vue-next'

const props = defineProps({
  now: { type: Number, default: 0 },
  before: { type: Number, default: 0 },
  pct: { type: Number, default: null }, // the API's change_pct (null when before is 0)
  money: { type: Boolean, default: false },
})

const diff = computed(() => (Number(props.now) || 0) - (Number(props.before) || 0))
const up = computed(() => diff.value > 0)
const icon = computed(() => (diff.value > 0 ? TrendingUp : diff.value < 0 ? TrendingDown : Minus))
const text = computed(() => {
  if (!diff.value) return 'No change'
  if (props.pct != null) return `${props.pct > 0 ? '+' : ''}${props.pct}%`
  const amount = props.money ? peso(Math.abs(diff.value)) : Math.abs(diff.value)
  return `${diff.value > 0 ? '+' : '−'}${amount}`
})
</script>

<style scoped>
.change { grid-area: delta; display: inline-flex; align-items: center; gap: 3px; font-size: 0.74rem; font-weight: 700; border-radius: 10px; padding: 2px 8px; justify-self: end; white-space: nowrap; }
.change.up { background: #e3efe7; color: #0a4a37; }
.change.flat { background: #eef1ee; color: #4a5a4a; }
</style>
