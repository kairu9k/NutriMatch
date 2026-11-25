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
        <template v-if="asTable"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18" /><path d="M7 15v3M12 10v8M17 6v12" /></svg></template><template v-else><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M3 10h18M9 10v10" /></svg></template>{{ asTable ? 'View as chart' : 'View as table' }}
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
          <span v-if="total(r) > 0" class="col-total" :style="{ bottom: `calc(${(total(r) / top) * 100}% + 6px)` }" aria-hidden="true">{{ format(total(r)) }}</span>
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
.bar-chart { margin: 0; font-family: 'DM Sans', sans-serif; }
.ic { flex-shrink: 0; display: inline-block; }
.bc-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.legend { display: flex; gap: 8px; flex-wrap: wrap; list-style: none; margin: 0; padding: 0; }
.legend li { display: inline-flex; align-items: center; gap: 7px; padding: 4px 11px; border-radius: 999px; background: #f7faf8; font-size: 12.5px; font-weight: 700; color: #4a5a52; }
.swatch { display: inline-block; width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.table-toggle { display: inline-flex !important; align-items: center; gap: 6px; height: 36px; margin-left: auto; padding: 0 13px !important; border: 1px solid #dce8e0 !important; border-radius: 999px !important; background: #fff !important; font-family: inherit; font-size: 12.5px !important; font-weight: 800; color: #004d3a !important; cursor: pointer; white-space: nowrap; }
.table-toggle .ic { color: #1f7a4d; }
.table-toggle:hover { background: #f1f6f2 !important; }

.plot { position: relative; padding: 24px 0 26px 44px; box-sizing: border-box; }
.grid { position: absolute; inset: 24px 0 26px 44px; }
.gridline { position: absolute; left: 0; right: 0; border-top: 1px dashed #e3ebe6; }
.gridline:first-child { border-top: 1.5px solid #c9d8cf; }
.tick { position: absolute; left: -44px; width: 36px; transform: translateY(-50%); text-align: right; font-size: 11px; font-weight: 700; color: #a9b6ae; font-variant-numeric: tabular-nums; }
.cols { position: relative; display: flex; align-items: stretch; height: 100%; gap: 8px; }
.col { position: relative; flex: 1; display: flex; flex-direction: column; justify-content: flex-end; align-items: center; min-width: 0; border-radius: 10px; outline: none; cursor: default; }
.col:hover, .col:focus-visible { background: rgba(0, 77, 58, 0.04); }
.col:focus-visible { box-shadow: inset 0 0 0 2px #1f8f5c; }
.stack { display: flex; flex-direction: column-reverse; justify-content: flex-start; align-items: center; width: 100%; height: 100%; }
/* wider, rounder columns with a light sheen on top of the series colour */
.seg { width: min(64px, 60%); flex-shrink: 0; background-image: linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0)) !important; transition: filter 0.15s; }
.seg:first-child { border-radius: 0 0 6px 6px; }
.seg + .seg { margin-bottom: 2px; }
.seg.top { border-radius: 10px 10px 0 0; }
.seg.top:first-child { border-radius: 10px 10px 6px 6px; }
.col:hover .seg, .col:focus-visible .seg { filter: brightness(1.06); }
.col-total { position: absolute; left: 0; right: 0; z-index: 2; text-align: center; font-size: 12.5px; font-weight: 800; color: #0e3a2c; font-variant-numeric: tabular-nums; white-space: nowrap; pointer-events: none; }
.col-label { position: absolute; bottom: -24px; font-size: 12.5px; font-weight: 800; color: #4a5a52; white-space: nowrap; }
.tip {
  position: absolute; left: 50%; z-index: 5; display: flex; flex-direction: column; gap: 4px; min-width: 170px;
  padding: 12px 14px; border-radius: 14px; background: #004d3a; color: #fff; font-size: 12.5px; pointer-events: none; white-space: nowrap;
  box-shadow: 0 18px 36px -14px rgba(0, 0, 0, 0.45);
}
.tip.left { left: auto; right: 50%; }
.tip strong { margin-bottom: 4px; font-family: 'Playfair Display', serif; font-size: 15px; color: #efbf04; }
.tip span { display: inline-flex; align-items: center; gap: 7px; }
.tip .swatch { width: 9px; height: 9px; box-shadow: 0 0 0 1.5px rgba(255, 255, 255, 0.6); }
.tip-total { margin-top: 4px; padding-top: 6px; border-top: 1px solid rgba(255, 255, 255, 0.22); font-weight: 800; }

/* table view */
.nm-table-wrap { margin: 0; border: 1.5px solid #c9d8cf; border-radius: 16px; overflow: hidden; overflow-x: auto; }
.nm-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.nm-table thead th { padding: 12px 16px; background: #004d3a; border: none; text-align: left !important; font-size: 12.5px; font-weight: 700; color: #fff; text-transform: none; letter-spacing: 0; white-space: nowrap; }
.nm-table tbody td { padding: 12px 16px; border-bottom: 1px solid #eef2ef; text-align: left !important; color: #22362c; font-variant-numeric: tabular-nums; }
.nm-table tbody tr:last-child td { border-bottom: none; }
.nm-table tbody td:first-child { font-weight: 800; color: #0e3a2c; }
.nm-table tbody td:last-child { font-weight: 700; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

@media (max-width: 640px) {
  .seg { width: min(44px, 70%); }
  .col-total { font-size: 11px; }
  .table-toggle { margin-left: 0; }
}
</style>