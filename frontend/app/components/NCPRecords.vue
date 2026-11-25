<template>
  <div class="nm-page">
    <!-- HERO (the summary figures double as filters) -->
    <section class="nr-hero">
      <img class="nr-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="nr-hero-fade" aria-hidden="true"></span>
      <div class="nr-hero-txt">
        <p class="nr-eyebrow"><span aria-hidden="true"></span>NCP records</p>
        <h2 class="nr-title">Every record, in one place</h2>
        <p class="nm-page-sub">Every NCP record across your patients. Records are written during consultations, in the consultation room. This page is for reviewing and printing them.</p>
      </div>
    </section>

    <!-- the summary figures, under the hero; each one filters the list -->
    <div v-if="data" class="summary kfs" role="group" aria-label="Filter by">
      <button v-for="s in SUMMARY" :key="s.key" type="button" class="sum-item kf" :class="[SUM_TONE[s.key], { attn: s.attn && data.summary[s.key], on: focus === s.key }]" :aria-pressed="focus === s.key" @click="toggleFocus(s.key)">
        <span class="kf-ico"><template v-if="s.key === 'drafts'"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="M13.5 6.5l4 4" /></svg></template><template v-else-if="s.key === 'no_record'"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M12 11v6M9 14h6" /></svg></template><template v-else-if="s.key === 'follow_up_due'"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg></template><template v-else><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 18 0a9 9 0 1 0 -18 0" /><path d="M8.5 12.5l2.5 2.5 4.5-5" /></svg></template></span>
        <span class="kf-t">
          <span class="sum-label">{{ s.label }}</span>
          <strong>{{ data.summary[s.key] }}</strong>
          <em>{{ SUM_NOTE[s.key] }}</em>
        </span>
        <span class="kf-go"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></span>
      </button>
    </div>

    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <div v-if="loading" class="nm-panel nr-loading"><span class="nr-spin" aria-hidden="true"></span><p class="nm-muted">Loading NCP records…</p></div>

    <template v-else-if="data">

      <!-- NEEDS YOUR ATTENTION -->
      <section v-if="worklistCount" class="nm-panel nr-card wl-card">
        <div class="nm-panel-head nr-card-h">
          <span class="nr-hico gold"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3L2 20h20z" /><path d="M12 10v4M12 17h.01" /></svg></span>
          <div class="nr-card-txt">
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
                  <span v-if="(w.nrs_score ?? 0) >= 3" class="nm-pill red">At risk, NRS-2002 {{ w.nrs_score }}</span>
                </p>
                <p class="nm-row-sub">{{ grp.detail(w) }}</p>
              </div>
              <NuxtLink :to="grp.link(w)" class="nm-btn-sm" :class="grp.key === 'drafts' ? 'nm-btn-dark' : 'nm-btn-outline'">{{ grp.action }}</NuxtLink>
            </div>
          </div>
        </template>
      </section>
      <p v-else class="all-clear"><span class="all-clear-ico"><CheckCircle2 :size="16" /></span> Every active patient's NCP is up to date.</p>

      <!-- ALL RECORDS -->
      <section class="nm-panel nr-card">
        <div class="nm-panel-head nr-card-h">
          <span class="nr-hico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6M9 17.5h3" /></svg></span>
          <div class="nr-card-txt">
            <h2 class="nm-panel-title">All records</h2>
            <p class="nm-panel-sub nr-count">{{ groups.length }} patient{{ groups.length === 1 ? '' : 's' }}, {{ shown.length }} record{{ shown.length === 1 ? '' : 's' }}{{ shown.length !== data.records.length ? ` of ${data.records.length}` : '' }}</p>
          </div>
        </div>
        <div class="nm-toolbar nr-tools">
          <label class="nm-search nr-search">
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

        <p v-if="!data.records.length" class="nm-muted empty-line nr-empty">No NCP records yet. They're written during consultations, in the consultation room's NCP tab.</p>
        <p v-else-if="!shown.length" class="nm-muted nr-empty">No records match these filters.</p>
        <div v-if="groups.length" class="plist" role="list">
          <div class="phead" aria-hidden="true">
            <span /><span>Patient</span><span>Latest diagnosis</span><span>Records</span><span>Last record</span><span>Goal status</span>
          </div>
          <div v-for="g in pagedGroups" :key="g.relationship_id" class="pgroup" :class="{ open: expanded.has(g.relationship_id) }" role="listitem">
            <button type="button" class="prow" :aria-expanded="expanded.has(g.relationship_id)" @click="toggle(g.relationship_id)">
              <span class="chev-wrap" aria-hidden="true"><ChevronRight :size="16" class="chev" /></span>
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
              <div class="tbox">
              <div class="thead" aria-hidden="true"><span /><span>Date</span><span>Type</span><span>Diagnosis</span><span>TER</span><span>Goal</span><span /></div>
              <button v-for="rec in g.records" :key="rec.id" type="button" class="trow" @click="open = rec">
                <span class="tdot" :class="rec.status" aria-hidden="true" />
                <span class="tdate">{{ shortDate(rec.encounter_date) }}</span>
                <span class="tkind"><em :class="{ follow: rec.is_follow_up }">{{ rec.is_follow_up ? `Follow-up #${rec.follow_up_no}` : 'Initial' }}</em></span>
                <span class="tdx">{{ rec.pes_problem || 'No diagnosis yet' }}</span>
                <span class="tkcal">{{ rec.target_kcal ? `${Math.round(rec.target_kcal).toLocaleString('en-PH')} kcal` : '—' }}</span>
                <!-- goal status is only rated at a follow-up (Monitoring step) -->
                <span class="tgoal" :class="{ muted: !rec.goal_status_label && rec.status !== 'draft' }">{{ rec.goal_status_label || (rec.status === 'draft' ? `Draft, ${rec.missing.length} missing` : (rec.is_follow_up ? '—' : 'Set at follow-up')) }}</span>
                <span class="tview">View <ChevronRight :size="14" /></span>
              </button>
              </div>
              <NuxtLink :to="`/client-detail/${g.relationship_id}?tab=ncp`" class="nm-panel-link chart-link">Open patient chart <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
            </div>
          </div>
        </div>
        <div v-if="pageCount > 1" class="pager">
          <span class="nm-muted">Showing {{ (page - 1) * PAGE + 1 }}–{{ Math.min(page * PAGE, groups.length) }} of {{ groups.length }} patients</span>
          <div class="pager-btns">
            <button type="button" class="nm-btn-outline nm-btn-sm" :disabled="page === 1" @click="page--">Previous</button>
            <span class="pager-num">Page {{ page }} of {{ pageCount }}</span>
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
import { CheckCircle2, ChevronRight, Search } from 'lucide-vue-next'

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

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    data.value = await get('/rnd/ncp/overview/')
  } catch {
    if (!quiet) error.value = 'Could not load your NCP records.'
  } finally {
    loading.value = false
  }
}
useAutoRefresh(() => load({ quiet: true }))
onMounted(() => {
  if (route.query.relationship) {
    navigateTo(`/client-detail/${route.query.relationship}?tab=ncp`, { replace: true })
    return
  }
  load()
})

const SUMMARY = [
  { key: 'drafts', label: 'Drafts in progress', attn: true },
  { key: 'no_record', label: 'Need an initial record', attn: true },
  { key: 'follow_up_due', label: 'Follow-ups due', attn: true },
  { key: 'finalized_this_month', label: 'Finalized this month' },
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
      detail: x => `${x.is_follow_up ? `Follow-up #${x.follow_up_no}` : 'Initial record'}, edited ${dateTime(x.updated_at)}. ${x.missing.length ? `Missing: ${x.missing.join(', ')}.` : 'Ready to finalize.'}` },
    { key: 'no_record', label: 'Consultation done, no NCP record yet', items: w.no_record, action: 'Write record', link: x => chart(x.relationship_id),
      detail: x => `Consultation on ${shortDate(x.visit_date)}${x.nrs_risk ? `, screened ${x.nrs_risk.toLowerCase()}` : ''}.` },
    { key: 'follow_up_due', label: 'Follow-up due', items: w.follow_up_due, action: 'Open chart', link: x => chart(x.relationship_id),
      detail: x => `${x.reason}. Last record ${shortDate(x.last_record_date)}.` },
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const SUM_TONE = { drafts: 'gold', no_record: 'blue', follow_up_due: 'green', finalized_this_month: 'dark' }
const SUM_NOTE = { drafts: 'Continue them in the chart', no_record: 'First record not written yet', follow_up_due: 'A reassessment is due', finalized_this_month: 'Signed and locked' }
</script>
<style scoped>
.nm-page { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); }
.ic { flex-shrink: 0; }

/* ---------- hero + summary figures ---------- */
.nr-hero {
  position: relative; overflow: hidden; display: flex; align-items: flex-end; justify-content: space-between; gap: 18px 24px; flex-wrap: wrap;
  margin-bottom: 16px; padding: 26px 30px; border-radius: 24px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.nr-hero-plate { position: absolute; right: -70px; top: 50%; width: 340px; height: 340px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); opacity: 0.85; pointer-events: none; }
.nr-hero-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 48%, rgba(0, 77, 58, 0.8) 72%, rgba(0, 77, 58, 0.3) 100%); }
.nr-hero-txt { position: relative; z-index: 1; flex: 1 1 360px; min-width: 0; max-width: 620px; }
.nr-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.nr-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.nr-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.nr-hero .nm-page-sub { margin: 0; font-size: 14px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }
.summary { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(4, auto); gap: 8px; }
.sum-item {
  display: flex; flex-direction: column; gap: 2px; min-width: 118px; padding: 10px 14px; border-radius: 14px; cursor: pointer; text-align: left;
  background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.18); color: #fff; font-family: inherit; backdrop-filter: blur(6px); transition: background 0.15s, transform 0.15s;
}
.sum-item:hover { background: rgba(255, 255, 255, 0.18); transform: translateY(-1px); }
.sum-item:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }
.sum-label { font-size: 11px; font-weight: 700; color: rgba(255, 255, 255, 0.75); white-space: nowrap; }
.sum-item strong { font-family: 'Playfair Display', serif; font-size: 26px; line-height: 1.2; color: #fff; font-variant-numeric: tabular-nums lining-nums; }
.sum-item.on { background: #fff; border-color: #fff; }
.sum-item.on .sum-label { color: #6b7d73; }
.sum-item.on strong { color: #004d3a; }

.nr-loading { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px 20px; border-radius: 22px; box-shadow: var(--sh); }
.nr-loading .nm-muted { margin: 0; }
.nr-spin { width: 22px; height: 22px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: nr-spin 0.8s linear infinite; }
@keyframes nr-spin { to { transform: rotate(360deg); } }

.all-clear { display: inline-flex; align-items: center; gap: 10px; margin: 0 0 16px; padding: 7px 16px 7px 7px; border-radius: 999px; background: #e3f4ea; font-size: 13.5px; font-weight: 800; color: #1f5c45; }
.all-clear-ico { width: 28px; height: 28px; border-radius: 50%; background: #1f9d55; color: #fff; display: inline-flex; align-items: center; justify-content: center; }

/* ---------- cards ---------- */
.nm-page > .nm-panel, .nr-card { margin-bottom: 16px; }
.nr-card { padding: 0; border: none; border-radius: 24px; overflow: hidden; box-shadow: var(--sh); }
.nr-card-h { display: flex; align-items: center; gap: 14px; margin: 0; padding: 20px 24px 0; }
.nr-card-txt { flex: 1; min-width: 0; }
.nr-hico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.nr-hico.gold { background: #fbf3d2; color: #9a7300; }
.nr-card .nm-panel-title { margin: 0; font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 700; letter-spacing: 0.01em; color: #0e3a2c; }
.nr-card .nm-panel-sub { margin: 3px 0 0; font-size: 13px; line-height: 1.5; color: #6b7d73; }
.nr-count { display: inline-flex; padding: 3px 11px; border-radius: 999px; background: #e3efe7; font-weight: 800; color: #004d3a !important; }

/* needs attention */
.wl-card { padding-bottom: 12px; }
.wl-group { margin: 16px 24px 0; border: 1px solid #eef2ef; border-radius: 18px; overflow: hidden; }
.wl-group + .wl-group { margin-top: 12px; }
.wl-label { display: flex; align-items: center; gap: 8px; margin: 0; padding: 10px 16px; background: #f7faf8; border-bottom: 1px solid #eef2ef; font-size: 13.5px; font-weight: 800; color: #0e3a2c; }
.wl-label span { min-width: 20px; height: 20px; padding: 0 6px; margin-left: 0; border-radius: 999px; background: #fff4d6; font-size: 11.5px; font-weight: 800; color: #8a6500; display: inline-flex; align-items: center; justify-content: center; }
.wl-row { position: relative; display: flex; align-items: center; gap: 14px; padding: 14px 16px 14px 20px; border-top: 1px solid #f0f3f1; flex-wrap: wrap; }
.wl-row::before { content: ''; position: absolute; left: 0; top: 14px; bottom: 14px; width: 4px; border-radius: 0 4px 4px 0; background: #efbf04; }
.wl-label + .wl-row { border-top: none; }
.wl-main { flex: 1; min-width: 180px; }
.wl-main .nm-row-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 0; font-family: inherit; font-size: 14.5px; font-weight: 700; color: #0e3a2c; }
.wl-main .nm-row-sub { margin: 3px 0 0; font-size: 13px; color: #6b7d73; }
.wl-main .nm-pill.red { padding: 2px 9px; border-radius: 999px; background: #fdecea; font-size: 11.5px; font-weight: 800; color: #b42318; }
.wl-row .nm-btn-sm { display: inline-flex; align-items: center; min-height: 40px; padding: 0 16px; border-radius: 12px; font-size: 13.5px; font-weight: 800; text-decoration: none; }
.wl-row .nm-btn-dark { background: #004d3a; border: 1px solid #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.wl-row .nm-btn-outline { background: #f1f6f2; border: 1px solid #dce8e0; color: #004d3a; }

/* avatar (render function) */
:deep(.nm-avatar) {
  flex-shrink: 0; width: 42px; height: 42px; border-radius: 50%; object-fit: cover; box-sizing: border-box;
  display: inline-flex; align-items: center; justify-content: center; font-family: 'Playfair Display', serif; font-size: 15px; font-weight: 700;
  background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; border: 2px solid #fff; box-shadow: 0 0 0 2.5px #1f9d55;
}

/* ---------- toolbar ---------- */
.nr-tools { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin: 0; padding: 18px 24px; }
.nr-search { position: relative; display: flex; align-items: center; gap: 10px; flex: 0 1 340px; height: 46px; padding: 0 16px; margin: 0; border-radius: 999px; background: #fff; border: 1.5px solid #d3dfd8; color: #8a9a91; box-sizing: border-box; }
.nr-search:focus-within { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.nr-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.nr-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }
.filters { display: flex; gap: 8px; flex-wrap: wrap; }
.filters .nm-select { min-height: 42px; height: 42px; padding-left: 14px; border-radius: 999px; border: 1.5px solid #d3dfd8; background-color: #f7faf8; font-family: inherit; font-size: 14px; font-weight: 400; color: #22362c; cursor: pointer; }
.filters .nm-select:focus { outline: none; border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.nr-empty, .empty-line { margin: 0 24px 20px; padding: 20px; border-radius: 16px; border: 1.5px dashed #cfddd4; text-align: center; font-weight: 600; }

/* ---------- patient list ---------- */
.plist { border-top: none; }
.phead, .prow { display: grid; grid-template-columns: 32px minmax(0, 1.3fr) minmax(0, 1.6fr) 110px 130px 150px; gap: 14px; align-items: center; }
.phead { padding: 13px 24px; background: #f7faf8; border-top: 1px solid #eef2ef; border-bottom: 1px solid #eef2ef; font-size: 12.5px; font-weight: 500; color: #7a8a80; }
.pgroup { position: relative; border-bottom: 1px solid #f0f3f1; }
.pgroup:last-child { border-bottom: none; }
.prow { width: 100%; padding: 16px 24px; background: none; border: none; border-radius: 0; font-family: inherit; text-align: left; cursor: pointer; color: #22362c; transition: background 0.15s; }
.prow:hover { background: #fafcfb; }
.prow:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.pgroup.open { background: #f4f9f6; box-shadow: inset 4px 0 0 #1f9d55; }
.pgroup.open > .prow { background: transparent; }
.chev-wrap { width: 28px; height: 28px; border-radius: 50%; border: 1.5px solid #d3dfd8; display: inline-flex; align-items: center; justify-content: center; color: #6b7d73; transition: background 0.15s, border-color 0.15s; }
.chev { color: inherit; transition: transform 0.2s; }
.pgroup.open .chev-wrap { background: #e3efe7; border-color: #e3efe7; color: #004d3a; }
.pgroup.open .chev { transform: rotate(90deg); }
.pwho { display: flex; align-items: center; gap: 12px; min-width: 0; }
.pname { display: flex; flex-direction: column; min-width: 0; }
.pname .nm-row-title { margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-family: inherit; font-size: 14.5px; font-weight: 700; color: #0e3a2c; }
.pname .nm-row-sub { margin: 1px 0 0; font-size: 12px; color: #8a9a91; }
.pdx { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 14px; font-weight: 400; color: #22362c; }
.pdx.empty { color: #8a9a91; font-weight: 500; font-style: italic; }
.pcount { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 400; color: #22362c; font-variant-numeric: tabular-nums; }
.pcount .nm-pill { padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; }
.pcount .nm-pill.gold { background: #fff4d6; color: #8a6500; }
.pdate { font-size: 14px; color: #3e5046; white-space: nowrap; }
.pgoal { font-size: 14px; font-weight: 400; color: #22362c; }
.pgoal.muted { color: #6b7d73; font-weight: 500; font-style: italic; }

/* expanded: a small table of the patient's records */
.timeline { padding: 0 24px 18px 70px; }
.tbox { border-radius: 14px; background: #fff; border: 1px solid #e3ebe6; overflow: hidden; }
.thead, .trow { display: grid; grid-template-columns: 10px 110px 120px minmax(0, 1fr) 100px 160px 60px; gap: 12px; align-items: center; }
.thead { padding: 10px 16px; border-bottom: 1px solid #eef2ef; font-size: 12px; font-weight: 500; color: #7a8a80; }
.trow { width: 100%; padding: 12px 16px; border: none; border-top: 1px solid #f3f6f4; background: none; font-family: inherit; text-align: left; cursor: pointer; font-size: 13.5px; color: #22362c; transition: background 0.15s; }
.thead + .trow { border-top: none; }
.trow:hover { background: #f7faf8; }
.trow:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.tdot { width: 8px; height: 8px; border-radius: 50%; background: #1f9d55; box-shadow: 0 0 0 3px #e3f4ea; }
.tdot.draft { background: #efbf04; box-shadow: 0 0 0 3px #fff4d6; }
.tdate { font-weight: 500; color: #22362c; white-space: nowrap; }
.tkind em { display: inline-flex; padding: 2px 9px; border-radius: 999px; background: #e3efe7; font-style: normal; font-size: 11.5px; font-weight: 800; color: #004d3a; white-space: nowrap; }
.tkind em.follow { background: #fbf3d2; color: #9a7300; }
.tdx { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tkcal { font-weight: 400; color: #22362c; font-variant-numeric: tabular-nums; white-space: nowrap; }
.tgoal { color: #3e5046; }
.pgoal.muted, .tgoal.muted { color: #6b7d73; font-style: italic; }
.tview { display: inline-flex; align-items: center; justify-content: flex-end; gap: 2px; font-weight: 800; color: #004d3a; }
.chart-link { display: inline-flex; align-items: center; gap: 6px; height: 36px; margin: 10px 0 0; padding: 0 14px; border-radius: 12px; background: #fff; border: 1px solid #dce8e0; font-size: 13px; font-weight: 800; color: #004d3a; text-decoration: none; }
.chart-link:hover { background: #f1f6f2; }

/* pager */
.pager { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin: 0; padding: 14px 24px; border-top: 1px solid #eef2ef; font-size: 13px; }
.pager-btns { display: flex; gap: 10px; align-items: center; }
.pager-num { align-self: center; font-size: 13px; font-weight: 700; color: #3e5046; font-variant-numeric: tabular-nums; }
.pager .nm-btn-outline { min-height: 38px; padding: 0 14px; border-radius: 12px; background: #f1f6f2; border: 1px solid #dce8e0; color: #004d3a; font-weight: 800; }

/* ---------- responsive ---------- */
@media (max-width: 1200px) {
  .summary { flex-basis: 100%; grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .sum-item { min-width: 0; }
}
@media (max-width: 960px) {
  .nr-hero { padding: 20px 18px; border-radius: 22px; }
  .nr-title { font-size: 24px; }
  .nr-hero-plate { width: 220px; height: 220px; right: -80px; top: 40px; transform: none; opacity: 0.5; }
  .summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .all-clear { border-radius: 16px; }
  .nr-card-h { padding: 16px 16px 0; }
  .nr-tools { padding: 14px 16px; }
  .nr-search { flex: 1 1 100%; }
  .wl-group { margin: 14px 16px 0; }
}
@media (max-width: 860px) {
  .phead { display: none; }
  .prow { grid-template-columns: 32px minmax(0, 1fr) auto; grid-template-areas: "c who count" "c dx dx" "c meta meta"; row-gap: 6px; padding: 14px 16px; }
  .chev-wrap { grid-area: c; align-self: start; margin-top: 6px; }
  .pwho { grid-area: who; }
  .pcount { grid-area: count; }
  .pdx { grid-area: dx; white-space: normal; }
  .pdate { grid-area: meta; }
  .pgoal { display: none; }
  .timeline { padding: 0 16px 16px; }
  .thead { display: none; }
  .trow { grid-template-columns: 10px minmax(0, 1fr) auto; grid-template-areas: "d kind view" "d dx dx" "d meta meta"; row-gap: 4px; }
  .tdot { grid-area: d; align-self: start; margin-top: 6px; }
  .tkind { grid-area: kind; }
  .tdate { display: none; }
  .tdx { grid-area: dx; white-space: normal; }
  .tkcal { grid-area: meta; }
  .tgoal { display: none; }
  .tview { grid-area: view; }
}
@media (max-width: 760px) {
  .nm-page { padding-bottom: 110px; }
  .sum-item strong { font-size: 22px; }
  .filters { width: 100%; flex-wrap: nowrap; overflow-x: auto; }
  .filters .nm-select { flex: 1 0 auto; }
  .wl-row .nm-btn-sm { width: 100%; justify-content: center; }
}

/* ---------- summary figures, under the hero ---------- */
.kfs { display: grid !important; grid-template-columns: repeat(4, minmax(0, 1fr)) !important; gap: 14px !important; margin: 0 0 18px !important; padding: 0 !important; background: none !important; border: none !important; box-shadow: none !important; }
.kf { position: relative; display: flex !important; flex-direction: row !important; align-items: center; gap: 14px; min-width: 0; margin: 0 !important; padding: 16px 18px !important; border: 1.5px solid #c9d8cf !important; border-radius: 18px !important; background: #fff !important; font-family: inherit; text-align: left; color: #0e3a2c !important; cursor: pointer; box-shadow: 0 10px 24px -18px rgba(0, 77, 58, 0.35) !important; transition: transform 0.15s, border-color 0.15s; }
.kf:hover { transform: translateY(-2px); border-color: #9ec4ad !important; }
.kf:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.kf-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; }
.kf.gold .kf-ico { background: #fff4d6; color: #8a6500; }
.kf.blue .kf-ico { background: #eef1fa; color: #2e4a86; }
.kf.green .kf-ico { background: #e3f4ea; color: #1f7a4d; }
.kf.dark .kf-ico { background: #004d3a; color: #efbf04; }
.kf-t { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.kf .sum-label { font-size: 12.5px !important; font-weight: 700; color: #4a5a52 !important; letter-spacing: 0 !important; text-transform: none !important; }
.kf strong { font-family: 'DM Sans', sans-serif !important; font-size: 26px !important; font-weight: 800; line-height: 1.1; color: #0e3a2c !important; font-variant-numeric: lining-nums tabular-nums; }
.kf em { font-style: normal; font-size: 12px; color: #8a9a91; }
.kf-go { flex-shrink: 0; color: #c9d3cd; }
.kf:hover .kf-go { color: #1f7a4d; }
.kf.attn { border-color: #efbf04 !important; background: linear-gradient(180deg, #fffbea, #fff) !important; }
.kf.attn strong { color: #8a6500 !important; }
.kf.on { border-color: #004d3a !important; background: linear-gradient(180deg, #f1f8f4, #fff) !important; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.1) !important; }
.kf.on strong { color: #004d3a !important; }
.kf.on em { font-weight: 700; color: #1f7a4d; }
@media (max-width: 1100px) { .kfs { grid-template-columns: repeat(2, minmax(0, 1fr)) !important; } }
@media (max-width: 760px) { .kfs { gap: 10px !important; } .kf { padding: 14px !important; } .kf-go { display: none; } }

/* search + filters: 10px corners like the other pages */
.nr-tools .nm-search,
.nr-search,
.nr-tools .nm-select,
.filters .nm-select,
.filters select.nm-select { border-radius: 10px !important; }
</style>