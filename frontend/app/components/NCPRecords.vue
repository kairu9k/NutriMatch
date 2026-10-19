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
            <p class="nm-panel-sub">{{ groups.length }} patient{{ groups.length === 1 ? '' : 's' }} · {{ shown.length }} record{{ shown.length === 1 ? '' : 's' }}{{ shown.length !== data.records.length ? ` (of ${data.records.length})` : '' }}</p>
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
        <div v-if="groups.length" class="plist" role="list">
          <div class="phead" aria-hidden="true">
            <span /><span>Patient</span><span>Latest diagnosis</span><span>Records</span><span>Last record</span><span>Goal status</span>
          </div>
          <div v-for="g in pagedGroups" :key="g.relationship_id" class="pgroup" :class="{ open: expanded.has(g.relationship_id) }" role="listitem">
            <button type="button" class="prow" :aria-expanded="expanded.has(g.relationship_id)" @click="toggle(g.relationship_id)">
              <ChevronRight :size="16" class="chev" />
              <span class="pwho">
                <Avatar :p="g.patient" />
                <span class="pname">
                  <span class="nm-row-title">{{ g.patient.name }}</span>
                  <span v-if="g.relationship_status !== 'active'" class="nm-row-sub">{{ g.relationship_status === 'discharged' ? 'Discharged' : 'Not yet confirmed' }}</span>
                </span>
              </span>
              <span class="pdx" :class="{ empty: !g.latest.pes_problem }">{{ g.latest.pes_problem || 'No diagnosis yet' }}</span>
              <span class="pcount">
                {{ g.records.length }}
                <span v-if="g.drafts" class="nm-pill gold">{{ g.drafts }} draft</span>
              </span>
              <span class="pdate">{{ shortDate(g.records[0].encounter_date) }}</span>
              <span class="pgoal" :class="{ muted: !g.goal }">{{ g.goal || (g.latest.status === 'completed' ? 'At first follow-up' : '—') }}</span>
            </button>
            <div v-if="expanded.has(g.relationship_id)" class="timeline">
              <button v-for="rec in g.records" :key="rec.id" type="button" class="trow" @click="open = rec">
                <span class="tdot" :class="rec.status" aria-hidden="true" />
                <span class="tdate">{{ shortDate(rec.encounter_date) }}</span>
                <span class="tkind">{{ rec.is_follow_up ? `Follow-up #${rec.follow_up_no}` : 'Initial' }}</span>
                <span class="tdx">{{ rec.pes_problem || 'No diagnosis yet' }}</span>
                <span class="tkcal">{{ rec.target_kcal ? `${Math.round(rec.target_kcal).toLocaleString('en-PH')} kcal` : '—' }}</span>
                <!-- goal status is only rated at a follow-up (Monitoring step) -->
                <span class="tgoal" :class="{ muted: !rec.goal_status_label && rec.status !== 'draft' }">{{ rec.goal_status_label || (rec.status === 'draft' ? `Draft · ${rec.missing.length} missing` : (rec.is_follow_up ? '—' : 'Set at follow-up')) }}</span>
                <span class="tview">View <ChevronRight :size="14" /></span>
              </button>
              <NuxtLink :to="`/client-detail/${g.relationship_id}?tab=ncp`" class="nm-panel-link chart-link">Open patient chart →</NuxtLink>
            </div>
          </div>
        </div>
        <div v-if="pageCount > 1" class="pager">
          <span class="nm-muted">Showing {{ (page - 1) * PAGE + 1 }}–{{ Math.min(page * PAGE, groups.length) }} of {{ groups.length }} patients</span>
          <div class="pager-btns">
            <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="page === 1" @click="page--">Previous</button>
            <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="page === pageCount" @click="page++">Next</button>
          </div>
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
import { CheckCircle2, ChevronRight, ClipboardList, Search } from 'lucide-vue-next'

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
  if (!data.value) return []
  return data.value.records.filter(r =>
    (!status.value || r.status === status.value)
    && (!kind.value || (kind.value === 'follow') === r.is_follow_up)
    && (!goal.value || r.goal_status === goal.value)
    && (!q || r.patient.name.toLowerCase().includes(q) || (r.pes_problem || '').toLowerCase().includes(q)))
})

// One row per patient (newest activity first); expanding shows that
// patient's records as a timeline. Filters apply to records — a patient is
// listed when any of their records match. 20 patients per page.
const PAGE = 20
const page = ref(1)
const expanded = ref(new Set())
function toggle(id) {
  const next = new Set(expanded.value)
  next.has(id) ? next.delete(id) : next.add(id)
  expanded.value = next
}
const groups = computed(() => {
  const map = new Map()
  for (const rec of shown.value) {
    if (!map.has(rec.relationship_id)) {
      map.set(rec.relationship_id, { relationship_id: rec.relationship_id, relationship_status: rec.relationship_status, patient: rec.patient, records: [] })
    }
    map.get(rec.relationship_id).records.push(rec)
  }
  return [...map.values()].map((g) => {
    const finals = g.records.filter(x => x.status === 'completed')
    const latest = finals[0] || g.records[0]
    const lastGoal = finals.find(x => x.goal_status_label)
    return { ...g, latest, drafts: g.records.length - finals.length, goal: lastGoal?.goal_status_label || null,
      sortKey: g.records[0].updated_at }
  }).sort((x, y) => String(y.sortKey).localeCompare(String(x.sortKey)))
})
const pageCount = computed(() => Math.max(1, Math.ceil(groups.value.length / PAGE)))
const pagedGroups = computed(() => groups.value.slice((page.value - 1) * PAGE, page.value * PAGE))
watch([search, status, kind, goal], () => { page.value = 1 })
watch(pageCount, (n) => { if (page.value > n) page.value = n })

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
.plist { border-top: 1px solid #f0f2f0; }
.phead, .prow { display: grid; grid-template-columns: 22px minmax(0, 1.3fr) minmax(0, 1.6fr) 110px 110px 120px; gap: 12px; align-items: center; }
.phead { padding: 10px 8px; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; }
.pgroup { border-bottom: 1px solid #f0f2f0; }
.prow { width: 100%; padding: 10px 8px; background: none; border: none; font-family: inherit; text-align: left; cursor: pointer; border-radius: 8px; color: #1a3a1a; }
.prow:hover, .prow:focus-visible { background: #fafbfa; outline: none; }
.pgroup.open > .prow { background: #f6f9f6; }
.chev { color: #8a9a8a; transition: transform 0.15s; }
.pgroup.open .chev { transform: rotate(90deg); }
.pwho { display: flex; align-items: center; gap: 10px; min-width: 0; }
.pname { display: flex; flex-direction: column; min-width: 0; }
.pname .nm-row-title { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pdx { font-size: 0.86rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pdx.empty { color: #9aaa9a; font-style: italic; }
.pcount { display: flex; align-items: center; gap: 6px; font-size: 0.86rem; font-variant-numeric: tabular-nums; }
.pdate, .pgoal { font-size: 0.84rem; color: #4a5a4a; }

.timeline { padding: 4px 8px 12px 42px; }
.trow { width: 100%; display: grid; grid-template-columns: 10px 96px 104px minmax(0, 1fr) 90px 150px 54px; gap: 10px; align-items: center; padding: 9px 10px; border: none; background: none; font-family: inherit; text-align: left; cursor: pointer; border-radius: 8px; font-size: 0.82rem; color: #2a3a2a; }
.trow:hover, .trow:focus-visible { background: #eef3ec; outline: none; }
.tdot { width: 8px; height: 8px; border-radius: 50%; background: #1f8f5c; }
.tdot.draft { background: #D4A017; }
.tkind { font-weight: 600; }
.tdx { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tkcal { font-variant-numeric: tabular-nums; color: #4a5a4a; }
.tgoal { color: #4a5a4a; }
.pgoal.muted, .tgoal.muted { color: #8a968a; font-style: italic; }
.tview { display: inline-flex; align-items: center; justify-content: flex-end; color: #1f6f46; font-weight: 600; }
.chart-link { display: inline-block; margin: 6px 0 0 10px; }
.pager { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 14px; font-size: 0.82rem; }
.pager-btns { display: flex; gap: 8px; }

@media (max-width: 860px) {
  .phead { display: none; }
  .prow { grid-template-columns: 22px minmax(0, 1fr) auto; grid-template-areas: "c who count" "c dx dx" "c meta meta"; row-gap: 4px; }
  .chev { grid-area: c; align-self: start; margin-top: 8px; }
  .pwho { grid-area: who; }
  .pcount { grid-area: count; }
  .pdx { grid-area: dx; white-space: normal; }
  .pdate { grid-area: meta; }
  .pgoal { display: none; }
  .timeline { padding-left: 16px; }
  .trow { grid-template-columns: 10px minmax(0, 1fr) auto; grid-template-areas: "d kind view" "d dx dx" "d meta meta"; row-gap: 2px; }
  .tdot { grid-area: d; align-self: start; margin-top: 5px; }
  .tkind { grid-area: kind; }
  .tdate { display: none; }
  .tdx { grid-area: dx; white-space: normal; }
  .tkcal { grid-area: meta; }
  .tgoal { display: none; }
  .tview { grid-area: view; }
}
@media (max-width: 760px) {
  .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .filters, .filters select { width: 100%; }
  .filters select { flex: 1; min-width: 0; }
  .wl-row .nm-btn-sm { margin-left: 50px; }
}
</style>
