<template>
  <!-- Column chart, stacked when there are several series (one value axis, never
       two). Legend for 2+ series, a tooltip per column (hover or keyboard), and a
       table view. Colours: CHART_COLORS below, checked with the dataviz palette
       validator (green #278f60 + gold #c48a12: colour-blind safe; the gold is
       under 3:1 on white, so the legend, tooltip and table carry the values too). -->
  <figure class="bar-chart">
    <div class="bc-top">
      <ul v-if="series.length > 1" class="legend" aria-label="Legend">
        <li v-for="(s, i) in series" :key="s.key"><span class="swatch" :style="{ background: colorOf(i) }" />{{ s.label }}</li>
      </ul>
      <button type="button" class="nm-btn-soft nm-btn-sm table-toggle" :aria-pressed="asTable" @click="asTable = !asTable">
        {{ asTable ? 'View as chart' : 'View as table' }}
      </button>
    </div>

    <div v-if="!asTable" class="plot" :style="{ height: `${height}px` }" @mouseleave="hover = null">
      <div class="grid" aria-hidden="true">
        <div v-for="t in ticks" :key="t" class="gridline" :style="{ bottom: `${(t / top) * 100}%` }">
          <span class="tick">{{ compact(t) }}</span>
        </div>
      </div>
      <div class="cols">
        <div
          v-for="(r, ri) in rows" :key="r.label" class="col" tabindex="0" role="img"
          :aria-label="`${r.label}: ${series.map(s => `${s.label} ${format(r.values[s.key] || 0)}`).join(', ')}`"
          @mouseenter="hover = ri" @focus="hover = ri" @blur="hover = null"
        >
          <div class="stack">
            <template v-for="(s, si) in series" :key="s.key">
              <div
                v-if="(r.values[s.key] || 0) > 0" class="seg" :class="{ top: si === topIndex(r) }"
                :style="{ height: `${((r.values[s.key] || 0) / top) * 100}%`, background: colorOf(si) }"
              />
            </template>
          </div>
          <span class="col-label">{{ r.short || r.label }}</span>
          <div v-if="hover === ri" class="tip" :class="{ left: ri > rows.length / 2 }" :style="{ bottom: `calc(${Math.min((total(r) / top) * 100, 70)}% + 8px)` }">
            <strong>{{ r.label }}</strong>
            <span v-for="(s, si) in series" :key="s.key"><i class="swatch" :style="{ background: colorOf(si) }" />{{ s.label }}: {{ format(r.values[s.key] || 0) }}</span>
            <span v-if="series.length > 1" class="tip-total">Total: {{ format(total(r)) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="nm-table-wrap">
      <table class="nm-table">
        <caption class="sr-only">{{ label }}</caption>
        <thead><tr><th>Month</th><th v-for="s in series" :key="s.key" class="nm-num">{{ s.label }}</th><th v-if="series.length > 1" class="nm-num">Total</th></tr></thead>
        <tbody>
          <tr v-for="r in rows" :key="r.label">
            <td>{{ r.label }}</td>
            <td v-for="s in series" :key="s.key" class="nm-num">{{ format(r.values[s.key] || 0) }}</td>
            <td v-if="series.length > 1" class="nm-num">{{ format(total(r)) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <figcaption class="sr-only">{{ label }}</figcaption>
  </figure>
</template>

<script setup>
const props = defineProps({
  rows: { type: Array, required: true }, // [{ label, short?, values: { key: number } }]
  series: { type: Array, required: true }, // [{ key, label }] in fixed order
  label: { type: String, required: true },
  format: { type: Function, default: v => Number(v).toLocaleString('en-PH') },
  height: { type: Number, default: 200 },
})
const CHART_COLORS = ['#278f60', '#c48a12']
const colorOf = i => CHART_COLORS[i] || CHART_COLORS[0]
const asTable = ref(false)
const hover = ref(null)

const total = r => props.series.reduce((sum, s) => sum + (Number(r.values[s.key]) || 0), 0)
// the topmost non-zero segment gets the rounded end
const topIndex = r => props.series.reduce((last, s, i) => ((Number(r.values[s.key]) || 0) > 0 ? i : last), -1)

// a clean top for the axis: 1, 2, 2.5 or 5 x 10^n
const top = computed(() => {
  const max = Math.max(...props.rows.map(total), 0)
  if (!max) return 1
  const mag = 10 ** Math.floor(Math.log10(max))
  return [1, 2, 2.5, 5, 10].map(m => m * mag).find(v => v >= max)
})
const ticks = computed(() => [0, top.value / 2, top.value])
const compact = v => (v >= 1000 ? `${+(v / 1000).toFixed(1)}K` : String(+v.toFixed(1)))
</script>

<style scoped>
.bar-chart { margin: 0; }
.bc-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.legend { display: flex; gap: 16px; flex-wrap: wrap; list-style: none; margin: 0; padding: 0; font-size: 0.8rem; color: #4a5a4a; }
.legend li { display: inline-flex; align-items: center; gap: 6px; }
.swatch { display: inline-block; width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.table-toggle { margin-left: auto; }

.plot { position: relative; padding: 0 0 22px 34px; }
.grid { position: absolute; inset: 0 0 22px 34px; }
.gridline { position: absolute; left: 0; right: 0; border-top: 1px solid #e6ece8; }
.gridline:first-child { border-top-color: #c9d6cd; }
.tick { position: absolute; left: -34px; width: 28px; transform: translateY(-50%); text-align: right; font-size: 0.7rem; color: #6a7a6a; font-variant-numeric: tabular-nums; }
.cols { position: relative; display: flex; align-items: stretch; height: 100%; gap: 4px; }
.col { position: relative; flex: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; min-width: 0; outline: none; }
.col:hover .stack, .col:focus-visible .stack { opacity: 0.85; }
.col:focus-visible { box-shadow: inset 0 0 0 2px #1f8f5c; border-radius: 6px; }
.stack { display: flex; flex-direction: column-reverse; justify-content: flex-start; align-items: center; width: 100%; height: 100%; }
/* thin columns (max 24px), 2px surface gap between stacked parts, 4px rounded end */
.seg { width: min(24px, 70%); flex-shrink: 0; }
.seg + .seg { margin-bottom: 2px; }
.seg.top { border-radius: 4px 4px 0 0; }
.col-label { position: absolute; bottom: -20px; font-size: 0.7rem; color: #6a7a6a; white-space: nowrap; }
.tip {
  position: absolute; left: 50%; z-index: 5; display: flex; flex-direction: column; gap: 2px; min-width: 150px;
  padding: 8px 10px; border-radius: 8px; background: #1a3a1a; color: #fff; font-size: 0.74rem; pointer-events: none; white-space: nowrap;
}
.tip.left { left: auto; right: 50%; }
.tip strong { font-size: 0.78rem; margin-bottom: 2px; }
.tip span { display: inline-flex; align-items: center; gap: 6px; }
.tip .swatch { width: 8px; height: 8px; }
.tip-total { margin-top: 2px; padding-top: 4px; border-top: 1px solid rgba(255, 255, 255, 0.25); }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
</style>
