<template>
  <div class="nm-page">
    <p class="nm-page-sub">Everyone you care for, where they are in the care process, and who needs you next.</p>

    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <div v-if="loading" class="nm-panel"><p class="nm-muted">Loading your patients…</p></div>

    <div v-else-if="!patients.length" class="nm-panel">
      <div class="nm-empty">
        <Users :size="28" />
        <p><strong>No patients yet</strong></p>
        <p>When a client books you, they show up here. Confirming their booking makes them your patient.</p>
      </div>
    </div>

    <template v-else>
      <div class="nm-toolbar">
        <div class="nm-tabs" role="tablist" aria-label="Filter patients">
          <button v-for="f in filters" :key="f.key" class="nm-tab" :class="{ active: filter === f.key }" role="tab"
                  :aria-selected="filter === f.key" @click="filter = f.key">
            <AlertTriangle v-if="f.key === 'attention' && f.count" :size="13" />
            {{ f.label }} <span class="nm-count">{{ f.count }}</span>
          </button>
        </div>
      </div>
      <div class="nm-toolbar">
        <label class="nm-search">
          <Search :size="16" />
          <input v-model="search" type="search" placeholder="Search by name or condition" aria-label="Search patients" />
        </label>
        <label class="sort">
          <span>Sort</span>
          <select v-model="sort" class="nm-select">
            <option value="attention">Needs attention first</option>
            <option value="next">Next appointment</option>
            <option value="adherence">Lowest adherence</option>
            <option value="name">Name (A–Z)</option>
          </select>
        </label>
      </div>

      <div class="nm-panel list-panel">
        <p v-if="!shown.length" class="nm-muted empty-filter">No patients match this filter.</p>

        <!-- desktop: table -->
        <div v-if="shown.length" class="nm-table-wrap desktop">
          <table class="nm-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Care stage</th>
                <th>Adherence · 7 days</th>
                <th>Progress</th>
                <th>Next appointment</th>
                <th><span class="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in shown" :key="p.id" :class="{ muted: p.status === 'discharged' }">
                <td class="who">
                  <PatientIdentity :p="p" />
                </td>
                <td><CareStage :p="p" /></td>
                <td><AdherenceCell :p="p" /></td>
                <td><ProgressCell :p="p" /></td>
                <td><NextCell :p="p" /></td>
                <td class="actions"><RowActions :p="p" /></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- phone: cards -->
        <div v-if="shown.length" class="cards">
          <article v-for="p in shown" :key="p.id" class="card" :class="{ muted: p.status === 'discharged' }">
            <PatientIdentity :p="p" />
            <div class="card-grid">
              <div><p class="k">Care stage</p><CareStage :p="p" /></div>
              <div><p class="k">Adherence · 7 days</p><AdherenceCell :p="p" /></div>
              <div><p class="k">Progress</p><ProgressCell :p="p" /></div>
              <div><p class="k">Next appointment</p><NextCell :p="p" /></div>
            </div>
            <div class="card-actions"><RowActions :p="p" /></div>
          </article>
        </div>
      </div>
      <p class="nm-hint">Adherence is the share of planned meals followed in the last 7 days (partly followed counts half, unlogged counts as missed). Weight change is from their screening to the latest progress record.</p>
    </template>
  </div>
</template>

<script setup>
import { AlertTriangle, FlaskConical, Info, MessageSquare, OctagonAlert, Search, Users } from 'lucide-vue-next'

const { get } = useApi()

const patients = ref([])
const loading = ref(true)
const error = ref('')
const route = useRoute()
const search = ref('')
const filter = ref(['active', 'pending', 'attention', 'no_plan', 'discharged', 'all'].includes(route.query.filter) ? route.query.filter : 'active')
const sort = ref('attention')

async function load() {
  error.value = ''
  try {
    patients.value = await get('/rnd/patients/')
  } catch {
    error.value = 'Could not load your patients.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

const needsPlan = p => p.status === 'active' && p.stage.meal_plan !== 'active'
const RULES = {
  active: p => p.status === 'active',
  pending: p => p.status === 'pending',
  attention: p => p.alerts.length > 0,
  no_plan: needsPlan,
  discharged: p => p.status === 'discharged',
  all: () => true,
}
const filters = computed(() => [
  { key: 'active', label: 'Active' },
  { key: 'pending', label: 'New bookings' },
  { key: 'attention', label: 'Needs attention' },
  { key: 'no_plan', label: 'No meal plan' },
  { key: 'discharged', label: 'Discharged' },
  { key: 'all', label: 'All' },
].map(f => ({ ...f, count: patients.value.filter(RULES[f.key]).length })))

const LEVEL = { critical: 0, warning: 1, info: 2 }
const STATUS = { pending: 0, active: 1, discharged: 2 }
const time = p => (p.next_appointment ? new Date(p.next_appointment.scheduled_at).getTime() : Infinity)
const SORTS = {
  attention: (a, b) => (STATUS[a.status] - STATUS[b.status])
    || ((a.alerts[0] ? LEVEL[a.alerts[0].level] : 9) - (b.alerts[0] ? LEVEL[b.alerts[0].level] : 9))
    || (time(a) - time(b)) || a.client.name.localeCompare(b.client.name),
  next: (a, b) => (time(a) - time(b)) || a.client.name.localeCompare(b.client.name),
  adherence: (a, b) => (a.adherence?.pct ?? 101) - (b.adherence?.pct ?? 101) || a.client.name.localeCompare(b.client.name),
  name: (a, b) => a.client.name.localeCompare(b.client.name),
}
const shown = computed(() => {
  const q = search.value.trim().toLowerCase()
  return patients.value
    .filter(RULES[filter.value])
    .filter(p => !q || p.client.name.toLowerCase().includes(q) || (p.condition || '').toLowerCase().includes(q))
    .sort(SORTS[sort.value])
})

/* ---------- small cells, shared by the table and the phone cards ---------- */
const PH = { timeZone: 'Asia/Manila' }
const phDate = v => new Date(v).toLocaleDateString('en-CA', PH)
function when(v) {
  const day = phDate(v)
  const t = new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
  if (day === phDate(Date.now())) return `Today, ${t}`
  if (day === phDate(Date.now() + 86400000)) return `Tomorrow, ${t}`
  return `${new Date(v).toLocaleDateString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric' })}, ${t}`
}
const SEX = { male: 'Male', female: 'Female' }

const PatientIdentity = defineComponent({
  props: { p: Object },
  setup(props) {
    return () => {
      const p = props.p
      const c = p.client
      const meta = [c.age != null ? `${c.age} y/o` : null, SEX[c.sex], p.condition ? p.condition + (p.other_conditions ? ` +${p.other_conditions}` : '') : null]
        .filter(Boolean).join(' · ')
      const alert = p.alerts[0]
      const AlertIcon = alert ? { critical: OctagonAlert, warning: AlertTriangle, info: Info }[alert.level] : null
      return h('div', { class: 'identity' }, [
        c.profile_photo ? h('img', { src: c.profile_photo, class: 'nm-avatar', alt: '' }) : h('span', { class: 'nm-avatar' }, userInitials(c.first_name, c.last_name)),
        h('div', { class: 'id-main' }, [
          h('p', { class: 'id-name' }, [
            h(resolveComponent('NuxtLink'), { to: `/client-detail/${p.id}`, class: 'name-link' }, () => c.name),
            p.status === 'pending' ? h('span', { class: 'nm-pill gold' }, 'New booking') : null,
            p.status === 'discharged' ? h('span', { class: 'nm-pill muted' }, 'Discharged') : null,
          ]),
          meta ? h('p', { class: 'nm-row-sub' }, meta) : null,
          p.allergies.length ? h('p', { class: 'allergy' }, `Allergy: ${p.allergies.join(', ')}`) : null,
          alert ? h('p', { class: ['flag', alert.level] }, [h(AlertIcon, { size: 13 }), h('span', alert.title + (p.alerts.length > 1 ? ` (+${p.alerts.length - 1} more)` : ''))]) : null,
          p.status === 'discharged' && p.ended_at ? h('p', { class: 'nm-row-sub' }, `Discharged ${shortDate(p.ended_at)}`) : null,
        ]),
      ])
    }
  },
})

const STEPS = ['Screening', 'NCP', 'Meal plan', 'Follow-up']
function stepStates(s) {
  return [
    s.screening ? 'done' : 'todo',
    s.ncp === 'done' ? 'done' : (s.ncp_draft ? 'current' : 'todo'),
    s.meal_plan === 'active' ? 'done' : (s.meal_plan === 'draft' ? 'current' : 'todo'),
    s.follow_up ? 'done' : (s.ncp === 'done' && s.ncp_draft ? 'current' : 'todo'),
  ]
}
function stageCaption(p) {
  const s = p.stage
  if (p.status === 'pending') return 'Booking not confirmed yet'
  if (!s.screening) return 'Waiting for their screening'
  if (s.ncp === 'none') return 'No NCP record yet'
  if (s.ncp === 'draft') return 'Initial NCP in progress'
  if (s.ncp_draft) return 'Follow-up NCP in progress'
  if (s.meal_plan === 'none') return 'No meal plan yet'
  if (s.meal_plan === 'draft') return 'Meal plan not sent yet'
  return s.follow_up ? `On plan · ${s.ncp_count} NCP records` : 'On plan · awaiting follow-up'
}
const CareStage = defineComponent({
  props: { p: Object },
  setup(props) {
    return () => {
      const states = stepStates(props.p.stage)
      const label = STEPS.map((n, i) => `${n}: ${{ done: 'done', current: 'in progress', todo: 'not yet' }[states[i]]}`).join(', ')
      return h('div', { class: 'stage' }, [
        h('div', { class: 'steps', role: 'img', 'aria-label': label },
          STEPS.map((n, i) => h('span', { class: ['step', states[i]], title: `${n} — ${{ done: 'done', current: 'in progress', todo: 'not yet' }[states[i]]}` }))),
        h('p', { class: 'nm-row-sub' }, stageCaption(props.p)),
      ])
    }
  },
})

const AdherenceCell = defineComponent({
  props: { p: Object },
  setup(props) {
    return () => {
      const a = props.p.adherence
      if (!a) return h('span', { class: 'nm-muted' }, 'No active plan')
      if (a.pct == null) return h('span', { class: 'nm-muted' }, 'Nothing due yet')
      const tone = a.pct >= 80 ? 'good' : a.pct >= 50 ? 'mid' : 'low'
      return h('div', { class: 'adh' }, [
        h('div', { class: 'adh-line' }, [
          h('strong', `${a.pct}%`),
          h('span', { class: 'adh-track', 'aria-hidden': 'true' }, [h('span', { class: ['adh-fill', tone], style: { width: `${Math.max(a.pct, 2)}%` } })]),
        ]),
        h('p', { class: 'nm-row-sub' }, `${a.logged} of ${a.planned} meals logged`),
      ])
    }
  },
})

const ProgressCell = defineComponent({
  props: { p: Object },
  setup(props) {
    return () => {
      const g = props.p.progress
      const ch = g.weight_change_kg
      const change = ch == null ? null : `${Number(ch) > 0 ? '+' : Number(ch) < 0 ? '−' : ''}${Math.abs(Number(ch)).toFixed(1)} kg`
      if (g.latest_weight_kg == null && g.bmi == null) return h('span', { class: 'nm-muted' }, 'No measurements yet')
      return h('div', [
        h('p', { class: 'cell-main' }, change ?? `${Number(g.latest_weight_kg).toFixed(1)} kg`),
        h('p', { class: 'nm-row-sub' }, [g.bmi != null ? `BMI ${Number(g.bmi).toFixed(1)}` : null, g.bmi_class].filter(Boolean).join(' · ')
          + (change ? '' : ' · at screening')),
      ])
    }
  },
})

const NextCell = defineComponent({
  props: { p: Object },
  setup(props) {
    return () => {
      const n = props.p.next_appointment
      const last = props.p.last_visit ? `Last visit ${shortDate(props.p.last_visit)}` : 'No visits yet'
      if (!n) return h('div', [h('p', { class: 'nm-muted' }, 'None booked'), h('p', { class: 'nm-row-sub' }, last)])
      return h('div', [
        h('p', { class: 'cell-main' }, when(n.scheduled_at)),
        h('p', { class: 'nm-row-sub next-sub' }, [
          n.type_label,
          n.status === 'pending' ? h('span', { class: 'nm-pill gold' }, 'To confirm')
            : n.payment === 'paid' ? h('span', { class: 'nm-pill green' }, 'Paid') : h('span', { class: 'nm-pill muted' }, 'Not paid yet'),
        ]),
      ])
    }
  },
})

const PRIMARY = ['review_booking', 'video_call', 'finish_ncp', 'start_ncp', 'create_plan', 'send_plan']
const RowActions = defineComponent({
  props: { p: Object },
  setup(props) {
    return () => {
      const p = props.p
      const step = p.stage.next_step
      const NuxtLink = resolveComponent('NuxtLink')
      return h('div', { class: 'row-actions' }, [
        h(NuxtLink, { to: step.link, class: [PRIMARY.includes(step.key) ? 'nm-btn-dark' : 'nm-btn-outline', 'nm-btn-sm'] }, () => step.label),
        p.status === 'active' && PRIMARY.includes(step.key)
          ? h(NuxtLink, { to: `/client-detail/${p.id}`, class: 'nm-btn-outline nm-btn-sm' }, () => 'Chart') : null,
        p.status !== 'pending'
          ? h(NuxtLink, { to: `/messages?relationship=${p.id}`, class: 'icon-btn', 'aria-label': `Message ${p.client.name}`, title: 'Message' }, () => [
            h(MessageSquare, { size: 15 }),
            p.unread_messages ? h('span', { class: 'badge' }, p.unread_messages) : null,
          ]) : null,
        p.new_lab_results
          ? h(NuxtLink, { to: `/client-detail/${p.id}?tab=labs`, class: 'icon-btn', 'aria-label': `${p.new_lab_results} new lab results`, title: 'New lab results' }, () => [
            h(FlaskConical, { size: 15 }),
            h('span', { class: 'badge' }, p.new_lab_results),
          ]) : null,
      ])
    }
  },
})
</script>

<style scoped>
.nm-page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0 0 18px; }
.sort { display: inline-flex; align-items: center; gap: 8px; font-size: 0.8rem; color: #6a7a6a; }
.list-panel { padding-top: 14px; }
.empty-filter { padding: 12px 0; margin: 0; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

.nm-table td { vertical-align: top; }
.nm-table tr.muted td { color: #8a9a8a; }
.who { min-width: 240px; }
.actions { text-align: right; white-space: nowrap; }

:deep(.identity) { display: flex; gap: 12px; align-items: flex-start; }
:deep(.id-main) { min-width: 0; }
:deep(.id-name) { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 0; font-weight: 700; color: #1a3a1a; font-size: 0.9rem; }
:deep(.name-link) { color: inherit; text-decoration: none; }
:deep(.name-link:hover) { text-decoration: underline; }
:deep(.allergy) { display: inline-block; margin: 4px 0 0; font-size: 0.72rem; font-weight: 600; color: #8a5a00; background: #fdf1d6; padding: 2px 8px; border-radius: 10px; }
:deep(.flag) { display: flex; align-items: center; gap: 5px; margin: 5px 0 0; font-size: 0.76rem; font-weight: 600; }
:deep(.flag.critical) { color: #a12525; }
:deep(.flag.warning) { color: #9a6a00; }
:deep(.flag.info) { color: #4a6a8a; }

:deep(.stage) { min-width: 150px; }
:deep(.steps) { display: flex; gap: 3px; margin: 4px 0 6px; }
:deep(.step) { height: 6px; width: 30px; border-radius: 3px; background: #e3e8e3; }
:deep(.step.done) { background: #1f8f5c; }
:deep(.step.current) { background: #D4A017; }

:deep(.adh) { min-width: 130px; }
:deep(.adh-line) { display: flex; align-items: center; gap: 8px; }
:deep(.adh-line strong) { font-variant-numeric: tabular-nums; color: #1a3a1a; width: 38px; }
:deep(.adh-track) { flex: 1; max-width: 90px; height: 6px; border-radius: 3px; background: #eef1ee; overflow: hidden; }
:deep(.adh-fill) { display: block; height: 100%; border-radius: 3px; }
:deep(.adh-fill.good) { background: #1f8f5c; }
:deep(.adh-fill.mid) { background: #D4A017; }
:deep(.adh-fill.low) { background: #c0392b; }

:deep(.cell-main) { margin: 0; font-weight: 600; color: #1a3a1a; font-variant-numeric: tabular-nums; }
:deep(.next-sub) { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
:deep(.nm-muted) { margin: 0; }

:deep(.row-actions) { display: inline-flex; gap: 6px; align-items: center; justify-content: flex-end; flex-wrap: wrap; }
:deep(.icon-btn) { position: relative; width: 32px; height: 32px; border-radius: 8px; border: 1px solid #d5dad5; display: inline-flex; align-items: center; justify-content: center; color: #1a3a1a; background: #fff; }
:deep(.icon-btn:hover) { background: #f7f9f7; }
:deep(.badge) { position: absolute; top: -6px; right: -6px; min-width: 17px; height: 17px; padding: 0 4px; border-radius: 9px; background: #c0392b; color: #fff; font-size: 0.64rem; font-weight: 700; display: flex; align-items: center; justify-content: center; }

.cards { display: none; }
.card { border-top: 1px solid #f0f2f0; padding: 14px 0; }
.card:first-child { border-top: none; padding-top: 4px; }
.card.muted { opacity: 0.8; }
.card-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; margin: 12px 0; }
.k { font-size: 0.66rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: #8a9a8a; margin: 0 0 4px; }
.card-actions :deep(.row-actions) { justify-content: flex-start; }

@media (max-width: 900px) {
  .desktop { display: none; }
  .cards { display: block; }
}
@media (max-width: 420px) {
  .card-grid { grid-template-columns: minmax(0, 1fr); }
  .sort { width: 100%; }
  .sort select { flex: 1; }
}
</style>
