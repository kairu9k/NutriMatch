<template>
  <!-- The "↗ +60%" badge beside a this-month figure (admin and RND dashboards).
       Up is green, a drop or no change is plain grey (not a warning). Shown only
       when last month has something to compare with (user's call, 2026-10-25):
       with nothing last month there's no percentage, so no badge. -->
  <span v-if="Number(before)" class="change" :class="up ? 'up' : 'flat'">
    <component :is="icon" :size="13" aria-hidden="true" /> {{ text }}
  </span>
</template>

<script setup>
import { Minus, TrendingDown, TrendingUp } from 'lucide-vue-next'

const props = defineProps({
  now: { type: Number, default: 0 },
  before: { type: Number, default: 0 },
  pct: { type: Number, default: null }, // the API's change_pct (null when before is 0)
})

const diff = computed(() => (Number(props.now) || 0) - (Number(props.before) || 0))
const up = computed(() => diff.value > 0)
const icon = computed(() => (diff.value > 0 ? TrendingUp : diff.value < 0 ? TrendingDown : Minus))
const text = computed(() => (diff.value ? `${props.pct > 0 ? '+' : ''}${props.pct}%` : 'No change'))
</script>

<style scoped>
.change { grid-area: delta; display: inline-flex; align-items: center; gap: 3px; font-size: 0.74rem; font-weight: 700; border-radius: 10px; padding: 2px 8px; justify-self: end; white-space: nowrap; }
.change.up { background: #e3efe7; color: #0a4a37; }
.change.flat { background: #eef1ee; color: #4a5a4a; }
</style>
