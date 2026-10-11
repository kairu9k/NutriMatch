<template>
  <div class="nm-page">
    <p class="nm-page-sub">Every NCP record across your patients. Records are written and edited on each patient's chart; this page is for reviewing and printing.</p>
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <div v-if="loading" class="nm-panel"><p class="nm-muted">Loading NCP records…</p></div>

    <template v-else-if="data">
      <!-- SUMMARY (click to filter the worklist / list) -->
      <div class="summary">
        <button v-for="s in SUMMARY" :key="s.key" type="button" class="sum-item" :class="{ attn: s.attn && data.summary[s.key], on: focus === s.key }" @click="toggleFocus(s.key)">
          <strong>{{ data.summary[s.key] }}</strong><span>{{ s.label }}</span>
        </button>
      </div>

      <!-- NEEDS YOUR ATTENTION -->
      <section v-if="worklistCount" class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">Needs your attention</h2>
            <p class="nm-panel-sub">Patients at nutritional risk (NRS-2002 ≥ 3) are listed first. A follow-up is due {{ data.follow_up_days }} days after the last finalized record, or after a consultation with no record.</p>
          </div>
        </div>
        <template v-for="grp in worklistGroups" :key="grp.key">
          <div v-if="grp.items.length && (!focus || focus === grp.key || focus === 'finalized_this_month')" class="wl-group">
            <p class="wl-label">{{ grp.label }} <span>{{ grp.items.length }}</span></p>
            <div v-for="w in grp.items" :key="`${grp.key}-${w.relationship_id}`" class="wl-row">
              <Avatar :p="w.patient" />
              <div class="wl-main">
                <p class="nm-row-title">
                  {{ w.patient.name }}
                  <span v-if="(w.nrs_score ?? 0) >= 3" class="nm-pill red">NRS-2002 {{ w.nrs_score }} · at risk</span>
                </p>
                <p class="nm-row-sub">{{ grp.detail(w) }}</p>
              </div>
              <NuxtLink :to="grp.link(w)" class="nm-btn-sm" :class="grp.key === 'drafts' ? 'nm-btn-dark' : 'nm-btn-outline'">{{ grp.action }}</NuxtLink>
            </div>
          </div>
        </template>
      </section>
      <section v-else class="nm-panel all-clear"><CheckCircle2 :size="16" /> Every active patient's NCP is up to date.</section>

      <!-- ALL RECORDS -->
      <section class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">All records</h2>
            <p class="nm-panel-sub">{{ shown.length }} of {{ data.records.length }}</p>
          </div>
        </div>
        <div class="nm-toolbar">
          <label class="nm-search">
            <Search :size="16" />
            <input v-model="search" type="search" placeholder="Search patient or diagnosis" aria-label="Search records" />
          </label>
          <div class="filters">
            <select v-model="status" class="nm-select" aria-label="Status">
              <option value="">All statuses</option><option value="completed">Finalized</option><option value="draft">Drafts</option>
            </select>
            <select v-model="kind" class="nm-select" aria-label="Record type">
              <option value="">Initial &amp; follow-up</option><option value="initial">Initial</option><option value="follow">Follow-up</option>
            </select>
            <select v-model="goal" class="nm-select" aria-label="Goal status">
              <option value="">Any goal status</option>
              <option v-for="(l, v) in GOALS" :key="v" :value="v">{{ l }}</option>
            </select>
          </div>
        </div>

        <div v-if="!data.records.length" class="nm-empty"><ClipboardList :size="26" /><p>No NCP records yet. Start one from a patient's chart.</p></div>
        <p v-else-if="!shown.length" class="nm-muted">No records match these filters.</p>
        <div class="cards">
          <button v-for="r in shown" :key="r.id" type="button" class="card" :class="r.status" @click="open = r">
            <div class="card-top">
              <Avatar :p="r.patient" />
              <div class="card-who">
                <p class="nm-row-title">{{ r.patient.name }}</p>
                <p class="nm-row-sub">{{ r.is_follow_up ? `Follow-up #${r.follow_up_no}` : 'Initial record' }} · {{ shortDate(r.encounter_date) }}</p>
              </div>
              <span class="nm-pill" :class="r.status === 'completed' ? 'green' : 'gold'">{{ r.status === 'completed' ? 'Finalized' : 'Draft' }}</span>
            </div>
            <p class="dx" :class="{ empty: !r.pes_problem }">{{ r.pes_problem || 'No diagnosis yet' }}</p>
            <div class="card-meta">
              <span v-if="r.target_kcal"><Flame :size="13" /> {{ Math.round(r.target_kcal).toLocaleString('en-PH') }} kcal/day</span>
              <span v-if="r.goal_status_label"><Target :size="13" /> Goals: {{ r.goal_status_label }}</span>
              <span v-if="r.status === 'draft' && r.missing.length" class="miss">Missing {{ r.missing.length }}</span>
            </div>
          </button>
        </div>
      </section>
    </template>

    <NcpRecordSummary v-if="open" :row="open" :rnd="data?.rnd" @close="open = null" />
  </div>
</template>

<script setup>
// NCP Records (sidebar) — view only. A worklist of who needs an NCP record
// (drafts, patients with none, follow-ups due) linking to the patient chart,
// and every record as a card; clicking one opens a read-only summary that
// can be printed. Writing/editing happens on Client Detail (and the room).
// Old per-patient links (?relationship=) are forwarded to the chart.
import { CheckCircle2, ClipboardList, Flame, Search, Target } from 'lucide-vue-next'

const route = useRoute()
const { get } = useApi()

const data = ref(null)
const loading = ref(true)
const error = ref('')
const open = ref(null)
const search = ref('')
const status = ref('')
const kind = ref('')
const goal = ref('')
const focus = ref(null)

async function load() {
  error.value = ''
  try {
    data.value = await get('/rnd/ncp/overview/')
  } catch {
    error.value = 'Could not load your NCP records.'
  } finally {
    loading.value = false
  }
}
onMounted(() => {
  if (route.query.relationship) {
    navigateTo(`/client-detail/${route.query.relationship}?tab=ncp`, { replace: true })
    return
  }
  load()
})

const SUMMARY = [
  { key: 'drafts', label: 'drafts in progress', attn: true },
  { key: 'no_record', label: 'need an initial record', attn: true },
  { key: 'follow_up_due', label: 'follow-ups due', attn: true },
  { key: 'finalized_this_month', label: 'finalized this month' },
]
function toggleFocus(k) {
  focus.value = focus.value === k ? null : k
  if (k === 'finalized_this_month') { status.value = focus.value ? 'completed' : '' }
}
const GOALS = { met: 'Met', partially_met: 'Partially met', not_met: 'Not met', ongoing: 'Ongoing' }
const chart = (id, extra = '') => `/client-detail/${id}?tab=ncp${extra}`
const worklistGroups = computed(() => {
  const w = data.value.worklist
  return [
    { key: 'drafts', label: 'Drafts in progress', items: w.drafts, action: 'Continue in chart', link: x => chart(x.relationship_id, '&open=draft'),
      detail: x => `${x.is_follow_up ? `Follow-up #${x.follow_up_no}` : 'Initial record'} · edited ${dateTime(x.updated_at)}${x.missing.length ? ` · missing ${x.missing.join(', ')}` : ' · ready to finalize'}` },
    { key: 'no_record', label: 'No NCP record yet', items: w.no_record, action: 'Open chart', link: x => chart(x.relationship_id),
      detail: x => `Screening ${x.screening_date ? shortDate(x.screening_date) : '—'}${x.nrs_risk ? ` · ${x.nrs_risk}` : ''}` },
    { key: 'follow_up_due', label: 'Follow-up due', items: w.follow_up_due, action: 'Open chart', link: x => chart(x.relationship_id),
      detail: x => `${x.reason} · last record ${shortDate(x.last_record_date)}` },
  ]
})
const worklistCount = computed(() => worklistGroups.value.reduce((n, g) => n + g.items.length, 0))

const shown = computed(() => {
  const q = search.value.trim().toLowerCase()
  return data.value.records.filter(r =>
    (!status.value || r.status === status.value)
    && (!kind.value || (kind.value === 'follow') === r.is_follow_up)
    && (!goal.value || r.goal_status === goal.value)
    && (!q || r.patient.name.toLowerCase().includes(q) || (r.pes_problem || '').toLowerCase().includes(q)))
})

const Avatar = defineComponent({
  props: { p: Object },
  setup(props) {
    return () => props.p.profile_photo
      ? h('img', { src: props.p.profile_photo, class: 'nm-avatar', alt: '' })
      : h('span', { class: 'nm-avatar' }, (props.p.name || '').split(' ').filter(Boolean).map(n => n[0]).slice(0, 2).join('').toUpperCase())
  },
})
</script>

<style scoped>
.nm-page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0 0 16px; }
.nm-page > .nm-panel { margin-bottom: 16px; }
.summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-bottom: 16px; }
.sum-item { background: #fff; border: 1px solid #eceeec; border-radius: 12px; padding: 12px 14px; display: flex; align-items: baseline; gap: 8px; min-width: 0; cursor: pointer; font-family: inherit; text-align: left; }
.sum-item strong { font-size: 1.35rem; color: #1a3a1a; font-variant-numeric: tabular-nums; }
.sum-item span { font-size: 0.8rem; color: #6a7a6a; }
.sum-item.attn { border-color: #f0dca0; background: #fffaf0; }
.sum-item.attn strong { color: #8a6a00; }
.sum-item.on { box-shadow: 0 0 0 2px #14301a; }
.all-clear { display: flex; align-items: center; gap: 8px; color: #1f6f46; font-weight: 600; font-size: 0.88rem; }

.wl-group + .wl-group { margin-top: 14px; }
.wl-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #8a9a8a; margin: 0 0 2px; }
.wl-label span { color: #b0bab0; margin-left: 4px; }
.wl-row { display: flex; align-items: center; gap: 12px; padding: 10px 0; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.wl-label + .wl-row { border-top: none; }
.wl-main { flex: 1; min-width: 180px; }
.wl-main .nm-row-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.filters { display: flex; gap: 8px; flex-wrap: wrap; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
.card { text-align: left; font-family: inherit; background: #fff; border: 1px solid #eceeec; border-radius: 12px; padding: 14px; cursor: pointer; display: flex; flex-direction: column; gap: 10px; transition: border-color 0.15s, box-shadow 0.15s; }
.card:hover, .card:focus-visible { border-color: #c7d6ca; box-shadow: 0 4px 14px rgba(20, 48, 26, 0.06); outline: none; }
.card.draft { border-left: 3px solid #D4A017; }
.card.completed { border-left: 3px solid #1f8f5c; }
.card-top { display: flex; align-items: center; gap: 10px; }
.card-who { flex: 1; min-width: 0; }
.dx { margin: 0; font-size: 0.88rem; font-weight: 600; color: #1a3a1a; line-height: 1.4; }
.dx.empty { color: #9aaa9a; font-weight: 500; font-style: italic; }
.card-meta { display: flex; gap: 12px; flex-wrap: wrap; font-size: 0.76rem; color: #6a7a6a; }
.card-meta span { display: inline-flex; align-items: center; gap: 4px; }
.card-meta .miss { color: #9a6a00; font-weight: 600; }

@media (max-width: 760px) {
  .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .filters, .filters select { width: 100%; }
  .filters select { flex: 1; min-width: 0; }
  .wl-row .nm-btn-sm { margin-left: 50px; }
}
</style>
