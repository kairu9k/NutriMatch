<template>
  <div class="nm-page mp-page">
    <!-- HERO -->
    <section class="mp-hero">
      <img class="mp-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="mp-hero-fade" aria-hidden="true"></span>
      <div class="mp-hero-txt">
        <p class="mp-eyebrow"><span aria-hidden="true"></span>My patients</p>
        <h2 class="mp-title">Everyone you care for</h2>
        <p class="nm-page-sub">Where each patient is in the care process, and who needs you next.</p>
      </div>
    </section>

    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>
    <div v-if="loading" class="nm-panel mp-state"><span class="mp-spin" aria-hidden="true"></span><p class="nm-muted">Loading your patients…</p></div>

    <div v-else-if="!patients.length" class="nm-panel mp-state">
      <span class="mp-state-ico"><svg class="ic" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="TAB_ICONS.active" /></span>
      <h2 class="empty-title">No patients yet</h2>
      <p class="empty-text">When a client books you, they show up here. Confirming their booking makes them your patient.</p>
    </div>

    <template v-else>
      <div class="nm-toolbar mp-bar">
        <div class="nm-tabs mp-tabs" role="tablist" aria-label="Filter patients">
          <button v-for="f in filters" :key="f.key" class="nm-tab" :class="{ active: filter === f.key, warn: f.key === 'attention' && f.count }" role="tab"
                  :aria-selected="filter === f.key" @click="filter = f.key">
            <AlertTriangle v-if="f.key === 'attention' && f.count" :size="15" />
            <svg v-else-if="TAB_ICONS[f.key]" class="ic tab-ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="TAB_ICONS[f.key]" />
            {{ f.label }} <span class="nm-count">{{ f.count }}</span>
          </button>
        </div>
      </div>
      <div class="nm-toolbar mp-tools">
        <label class="nm-search">
          <Search :size="17" />
          <input v-model="search" type="search" placeholder="Search by name or condition" aria-label="Search patients" />
        </label>
        <label class="sort">
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M6 12h12M10 18h4" /></svg>
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
        <div v-if="!shown.length" class="empty-filter">
          <span class="mp-state-ico sm"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="TAB_ICONS[filter] || TAB_ICONS.all" /></span>
          <p class="nm-muted">No patients match this filter.</p>
        </div>

        <!-- desktop: table -->
        <div v-if="shown.length" class="nm-table-wrap desktop">
          <table class="nm-table mp-table">
            <thead>
              <tr>
                <th class="col-who">Patient</th>
                <th class="col-stage">Care stage</th>
                <th class="col-adh">7-day adherence</th>
                <th class="col-prog">Progress</th>
                <th class="col-next">Next appointment</th>
                <th class="col-act">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in pagedShown" :key="p.id" :class="rowTone(p)">
                <td class="who col-who">
                  <PatientIdentity :p="p" />
                </td>
                <td class="col-stage"><CareStage :p="p" /></td>
                <td class="col-adh"><AdherenceCell :p="p" /></td>
                <td class="col-prog"><ProgressCell :p="p" /></td>
                <td class="col-next"><NextCell :p="p" /></td>
                <td class="actions col-act"><RowActions :p="p" /></td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- phone: cards -->
        <div v-if="shown.length" class="cards">
          <article v-for="p in pagedShown" :key="p.id" class="card" :class="rowTone(p)">
            <PatientIdentity :p="p" />
            <div class="card-grid">
              <div class="col-stage cg-wide"><p class="k">Care stage</p><CareStage :p="p" /></div>
              <div class="col-adh"><p class="k">7-day adherence</p><AdherenceCell :p="p" /></div>
              <div class="col-prog"><p class="k">Progress</p><ProgressCell :p="p" /></div>
              <div class="col-next cg-wide"><p class="k">Next appointment</p><NextCell :p="p" /></div>
            </div>
            <div class="card-actions"><RowActions :p="p" /></div>
          </article>
        </div>
        <ListPager v-model:page="page" :pages="pages" />
      </div>
      <p class="nm-hint mp-note">
        <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg>
        <span>Adherence is the share of planned meals followed in the last 7 days (partly followed counts half, unlogged counts as missed). Weight change is from their screening to the latest progress record.</span>
      </p>
    </template>
  </div>
</template>
<script setup>
import { AlertTriangle, FlaskConical, Info, MessageSquare, OctagonAlert, Search } from 'lucide-vue-next'

const { get } = useApi()

const patients = ref([])
const loading = ref(true)
const error = ref('')
const route = useRoute()
const search = ref('')
const filter = ref(['active', 'pending', 'attention', 'no_plan', 'discharged', 'all'].includes(route.query.filter) ? route.query.filter : 'active')
const sort = ref('attention')

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    patients.value = await get('/rnd/patients/')
  } catch {
    if (!quiet) error.value = 'Could not load your patients.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
// unread chat counts come with the list, so chat refreshes it too
useAutoRefresh(() => load({ quiet: true }), { messages: true })

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
    .filter(p => !q || p.client.name.toLowerCase().includes(q) || (p.conditions || [p.condition]).join(' ').toLowerCase().includes(q))
    .sort(SORTS[sort.value])
})
const { page, pages, paged: pagedShown } = usePager(shown, { resetOn: () => [filter.value, search.value, sort.value] })

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
      const meta = [c.age != null ? `${c.age} y/o` : null, SEX[c.sex], (p.conditions?.length ? p.conditions.join(', ') : p.condition) || null]
        .filter(Boolean).join(', ')
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
  return s.follow_up ? `On a plan, ${s.ncp_count} NCP records` : 'On a plan, follow-up next'
}
const CareStage = defineComponent({
  props: { p: Object },
  setup(props) {
    return () => {
      const states = stepStates(props.p.stage)
      const label = STEPS.map((n, i) => `${n}: ${{ done: 'done', current: 'in progress', todo: 'not yet' }[states[i]]}`).join(', ')
      return h('div', { class: 'stage' }, [
        h('div', { class: 'steps', role: 'img', 'aria-label': label },
          STEPS.map((n, i) => h('span', { class: ['step', states[i]], title: `${n}: ${{ done: 'done', current: 'in progress', todo: 'not yet' }[states[i]]}` }))),
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
        h('p', { class: 'nm-row-sub' }, [g.bmi != null ? `BMI ${Number(g.bmi).toFixed(1)}` : null, g.bmi_class, change ? null : 'at screening'].filter(Boolean).join(', ')),
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// the hero figures double as quick filters
const HERO_FIGS = ['active', 'pending', 'attention', 'no_plan']
const countOf = key => filters.value.find(f => f.key === key)?.count ?? 0
const filterLabel = key => filters.value.find(f => f.key === key)?.label || key
const TAB_ICONS = {
  active: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" />',
  pending: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M19 8v6M22 11h-6" />',
  attention: '<path d="M12 3L2 20h20z" /><path d="M12 10v4M12 17h.01" />',
  no_plan: '<path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" />',
  discharged: '<path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="9" />',
  all: '<rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" />',
}
// row colour: the accent bar on the left follows the patient's state
const rowTone = p => ({
  muted: p.status === 'discharged',
  pending: p.status === 'pending',
  alert: p.status !== 'discharged' && p.alerts.length > 0,
  [`lvl-${p.alerts[0]?.level}`]: p.alerts.length > 0,
})
</script>
<style scoped>
.mp-page {
  --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22);
}
.ic { flex-shrink: 0; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

/* ---------- hero ---------- */
.mp-hero {
  position: relative; overflow: hidden; display: flex; align-items: flex-end; justify-content: space-between; gap: 18px 24px; flex-wrap: wrap;
  margin-bottom: 20px; padding: 26px 30px; border-radius: 24px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.mp-hero-plate { position: absolute; right: -70px; top: 50%; width: 340px; height: 340px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); opacity: 0.85; pointer-events: none; }
.mp-hero-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 48%, rgba(0, 77, 58, 0.8) 72%, rgba(0, 77, 58, 0.3) 100%); }
.mp-hero-txt { position: relative; z-index: 1; flex: 1 1 320px; min-width: 0; }
.mp-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.mp-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.mp-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.mp-hero .nm-page-sub { margin: 0; font-size: 14.5px; color: rgba(255, 255, 255, 0.85); }
.mp-figs { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(4, auto); gap: 8px; }
.mp-fig {
  display: flex; flex-direction: column; align-items: flex-start; min-width: 108px; padding: 10px 14px; border-radius: 14px; cursor: pointer; text-align: left;
  background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.18); color: #fff; font-family: inherit; backdrop-filter: blur(6px); transition: background 0.15s, transform 0.15s;
}
.mp-fig:hover { background: rgba(255, 255, 255, 0.18); transform: translateY(-1px); }
.mp-fig:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }
.mp-fig small { font-size: 11px; font-weight: 700; color: rgba(255, 255, 255, 0.75); white-space: nowrap; }
.mp-fig strong { font-family: 'Playfair Display', serif; font-size: 26px; line-height: 1.2; font-variant-numeric: lining-nums; }
/* the selected figure is white, the rest glass */
.mp-fig.on { background: #fff; border-color: #fff; color: #004d3a; }
.mp-fig.on small { color: #6b7d73; }


/* ---------- states ---------- */
.mp-state { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 48px 20px; text-align: center; border-radius: 22px; box-shadow: var(--sh); }
.mp-state .nm-muted { margin: 0; }
.mp-spin { width: 22px; height: 22px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: mp-spin 0.8s linear infinite; }
@keyframes mp-spin { to { transform: rotate(360deg); } }
.mp-state-ico { width: 56px; height: 56px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.mp-state-ico.sm { width: 46px; height: 46px; border-radius: 14px; }
.empty-title { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; margin: 0; }
.empty-text { font-size: 13.5px; color: #6b7d73; line-height: 1.55; margin: 0; max-width: 56ch; }

/* ---------- tabs, search, sort ---------- */
.mp-bar { margin-bottom: 12px; }
.mp-tabs { display: flex; gap: 4px; padding: 5px; border-radius: 999px; background: #fff; border: none; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05), 0 8px 20px -14px rgba(0, 77, 58, 0.4); overflow-x: auto; max-width: 100%; scrollbar-width: none; }
.mp-tabs::-webkit-scrollbar { display: none; }
.mp-tabs .nm-tab {
  flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 38px; padding: 0 14px; margin: 0; border: none; border-radius: 999px;
  background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 700; color: #4a5a52; cursor: pointer; white-space: nowrap; transition: background 0.15s;
}
.mp-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; color: #004d3a; }
.mp-tabs .nm-tab .tab-ic { color: #8a9a91; }
.mp-tabs .nm-tab.warn svg { color: #c49102; }
.mp-tabs .nm-count { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 800; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; }
.mp-tabs .nm-tab.warn .nm-count { background: #fff4d6; color: #8a6500; }
.mp-tabs .nm-tab.active { background: #004d3a; color: #fff; box-shadow: 0 8px 16px -10px rgba(0, 77, 58, 0.9); }
.mp-tabs .nm-tab.active svg { color: #efbf04; }
.mp-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }
.mp-tabs .nm-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.mp-tools { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }
.mp-tools .nm-search { position: relative; display: flex; align-items: center; gap: 10px; flex: 0 1 360px; width: auto; max-width: 100%; margin: 0; height: 46px; padding: 0 16px; border-radius: 999px; background: #fff; border: 1.5px solid #d3dfd8; color: #8a9a91; box-sizing: border-box; }
.mp-tools .nm-search:focus-within { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.mp-tools .nm-search svg { position: static !important; flex-shrink: 0; transform: none !important; margin: 0; }
.mp-tools .nm-search input { flex: 1; min-width: 0; width: auto; height: 100%; border: none !important; outline: none; background: transparent !important; padding: 0 !important; margin: 0; border-radius: 0; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }
.sort { display: inline-flex; align-items: center; gap: 8px; height: 46px; padding: 0 6px 0 16px; border-radius: 999px; background: #fff; border: 1.5px solid #d3dfd8; font-size: 13px; color: #6b7d73; box-sizing: border-box; }
.sort .nm-select { height: 38px; min-height: 0; border: none; background-color: transparent; font-family: inherit; font-size: 13.5px; font-weight: 800; color: #0e3a2c; box-shadow: none; cursor: pointer; }
.sort:focus-within { border-color: #004d3a; }

/* ---------- list panel + table ---------- */
.list-panel { padding: 0; border-radius: 24px; border: none; overflow: hidden; box-shadow: var(--sh); }
.empty-filter { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px 20px; margin: 0; text-align: center; }
.empty-filter .nm-muted { margin: 0; font-weight: 600; }
.mp-table { width: 100%; border-collapse: collapse; table-layout: auto; }
/* roomy columns: the table lines the headers up with the cells, so no fixed widths */
.mp-table td.col-who { min-width: 260px; }
.mp-table td.col-stage { min-width: 210px; }
.mp-table td.col-adh { min-width: 160px; }
.mp-table td.col-prog { min-width: 130px; }
.mp-table td.col-next { min-width: 170px; }
.mp-table .col-act { width: 1%; white-space: nowrap; }
/* the lab-results shortcut is hidden here; new results still show in the chart */
:deep(.row-actions .icon-btn[title='New lab results']) { display: none; }
.mp-table th {
  padding: 16px 22px; text-align: left; background: #f7faf8; border-bottom: 1px solid #eef2ef;
  font-size: 11px; font-weight: 800; color: #6b7d73; white-space: nowrap;
}
.mp-table th:first-child { padding-left: 30px; }
.mp-table th.col-act { text-align: right; padding-right: 26px; }
.mp-table td { position: relative; padding: 22px 22px; vertical-align: top; border-bottom: 1px solid #f0f3f1; color: #22362c; }
.mp-table td:first-child { padding-left: 30px; }
.mp-table td.actions { padding-right: 26px; text-align: right; white-space: nowrap; }
.mp-table tbody tr { transition: background 0.15s; }
.mp-table tbody tr:hover td { background: #fafcfb; }
.mp-table tbody tr:last-child td { border-bottom: none; }
/* accent bar: green active, gold new booking, red/amber needs attention, grey discharged */
.mp-table td:first-child::before { content: ''; position: absolute; left: 0; top: 22px; bottom: 22px; width: 4px; border-radius: 0 4px 4px 0; background: #1f9d55; }
.mp-table tr.pending td:first-child::before, .card.pending::before { background: #efbf04; }
.mp-table tr.alert.lvl-warning td:first-child::before, .card.alert.lvl-warning::before { background: #e0a100; }
.mp-table tr.alert.lvl-critical td:first-child::before, .card.alert.lvl-critical::before { background: #c0392b; }
.mp-table tr.alert.lvl-info td:first-child::before, .card.alert.lvl-info::before { background: #3b5ba5; }
.mp-table tr.muted td:first-child::before, .card.muted::before { background: #c9d3cd; }
.mp-table tr.muted td { color: #8a9a91; }
.mp-table tr.muted :deep(.nm-avatar) { filter: grayscale(0.6); opacity: 0.8; }

/* ---------- identity ---------- */
:deep(.identity) { display: flex; gap: 16px; align-items: flex-start; min-width: 0; }
:deep(.identity .nm-avatar) {
  flex-shrink: 0; width: 50px; height: 50px; border-radius: 50%; object-fit: cover; box-sizing: border-box;
  display: inline-flex; align-items: center; justify-content: center; font-family: 'Playfair Display', serif; font-size: 17px; font-weight: 700;
  background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a;
  border: 2px solid #fff; box-shadow: 0 0 0 2.5px #1f9d55, 0 6px 14px -6px rgba(0, 77, 58, 0.5);
}
.pending :deep(.identity .nm-avatar) { box-shadow: 0 0 0 2.5px #efbf04, 0 6px 14px -6px rgba(0, 77, 58, 0.5); }
.muted :deep(.identity .nm-avatar) { box-shadow: 0 0 0 2.5px #c9d3cd; }
:deep(.id-main) { min-width: 0; }
:deep(.id-name) { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 0; }
:deep(.name-link) { font-family: 'Playfair Display', serif; font-size: 17.5px; font-weight: 700; letter-spacing: 0.01em; color: #0e3a2c; text-decoration: none; }
:deep(.name-link:hover) { color: #004d3a; text-decoration: underline; text-underline-offset: 3px; }
.muted :deep(.name-link) { color: #6b7d73; }
:deep(.id-name .nm-pill) { padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; }
:deep(.id-name .nm-pill.gold) { background: #fff4d6; color: #8a6500; }
:deep(.id-name .nm-pill.muted) { background: #eef2ef; color: #6b7d73; }
:deep(.nm-row-sub) { margin: 3px 0 0; font-size: 12.5px; color: #6b7d73; }
:deep(.allergy) { display: inline-block; max-width: 100%; box-sizing: border-box; margin: 6px 0 0; padding: 3px 10px; border-radius: 999px; background: #fef3f2; border: 1px solid #f6cfcb; font-size: 11.5px; font-weight: 800; color: #b42318; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
:deep(.flag) { display: inline-flex; align-items: center; gap: 5px; max-width: 100%; box-sizing: border-box; margin: 6px 0 0; padding: 3px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 800; }
:deep(.flag svg) { flex-shrink: 0; }
:deep(.flag span) { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
:deep(.flag.critical) { background: #fdecea; color: #b42318; }
:deep(.flag.warning) { background: #fff4d6; color: #8a6500; }
:deep(.flag.info) { background: #eef1fa; color: #3b5ba5; }

/* ---------- care stage: four labelled segments ---------- */
:deep(.stage) { min-width: 0; }
:deep(.steps) { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 4px; margin: 2px 0 22px; }
:deep(.step) { position: relative; width: auto; height: 6px; border-radius: 999px; background: #e3ebe6; }
:deep(.step.done) { background: #1f9d55; }
:deep(.step.current) { background: repeating-linear-gradient(90deg, #efbf04 0 6px, #fbeaa6 6px 10px); }
:deep(.step::after) { position: absolute; left: 0; right: 0; top: 10px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 10px; font-weight: 700; color: #a3b1a9; }
:deep(.step:nth-child(1)::after) { content: 'Screening'; }
:deep(.step:nth-child(2)::after) { content: 'NCP'; }
:deep(.step:nth-child(3)::after) { content: 'Meal plan'; }
:deep(.step:nth-child(4)::after) { content: 'Follow-up'; }
:deep(.step.done::after) { color: #1f7a4d; }
:deep(.step.current::after) { color: #8a6500; }
:deep(.stage .nm-row-sub) { margin: 0; font-weight: 600; color: #3e5046; }
.muted :deep(.step.done) { background: #a9bdb1; }

/* ---------- adherence ---------- */
:deep(.adh) { min-width: 0; }
:deep(.adh-line) { display: flex; align-items: center; gap: 10px; }
:deep(.adh-line strong) { width: auto; font-family: 'Playfair Display', serif; font-size: 19px; font-variant-numeric: lining-nums tabular-nums; color: #0e3a2c; }
:deep(.adh-track) { flex: 1; max-width: 100px; height: 8px; border-radius: 999px; background: #eef2ef; overflow: hidden; }
:deep(.adh-fill) { display: block; height: 100%; border-radius: 999px; }
:deep(.adh-fill.good) { background: #1f9d55; }
:deep(.adh-fill.mid) { background: #efbf04; }
:deep(.adh-fill.low) { background: #c0392b; }
.col-adh > :deep(.nm-muted) { display: inline-flex; align-items: center; padding: 4px 11px; border-radius: 999px; background: #f3f6f4; font-size: 12.5px; font-weight: 700; color: #6b7d73; }

/* ---------- progress ---------- */
.col-prog :deep(.cell-main) { margin: 0; font-family: 'Playfair Display', serif; font-size: 19px; font-weight: 700; color: #0e3a2c; font-variant-numeric: lining-nums tabular-nums; }
.col-prog > :deep(.nm-muted) { display: inline-flex; padding: 4px 11px; border-radius: 999px; background: #f3f6f4; font-size: 12.5px; font-weight: 700; color: #6b7d73; }

/* ---------- next appointment ---------- */
.col-next :deep(.cell-main) {
  display: inline-flex; align-items: center; gap: 9px; margin: 0; padding: 5px 12px 5px 5px; border: 1.5px solid #cfe6d7; border-radius: 12px;
  background: #f1f8f4; color: #0e3a2c; font-size: 13.5px; font-weight: 800; white-space: nowrap; font-variant-numeric: tabular-nums;
}
.col-next :deep(.cell-main)::before {
  content: ''; flex-shrink: 0; width: 28px; height: 28px; border-radius: 9px;
  background: #004d3a url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23EFBF04' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='5' width='18' height='16' rx='2'/%3E%3Cpath d='M16 3v4M8 3v4M3 10h18'/%3E%3C/svg%3E") center / 15px no-repeat;
}
.muted .col-next :deep(.cell-main) { border-color: #e3ebe6; background: #f7faf8; color: #4a5a52; }
.muted .col-next :deep(.cell-main)::before { background-color: #a9b6ae; }
:deep(.next-sub) { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-top: 8px; }
:deep(.next-sub .nm-pill) { padding: 2px 9px; border-radius: 999px; font-size: 11px; font-weight: 800; }
:deep(.next-sub .nm-pill.green) { background: #e3f4ea; color: #1f7a4d; }
:deep(.next-sub .nm-pill.gold) { background: #fff4d6; color: #8a6500; }
:deep(.next-sub .nm-pill.muted) { background: #eef2ef; color: #6b7d73; }
.col-next :deep(div > .nm-muted) { display: inline-flex; padding: 4px 11px; border-radius: 999px; background: #f3f6f4; font-size: 12.5px; font-weight: 700; color: #6b7d73; }
:deep(.nm-muted) { margin: 0; }

/* ---------- actions ---------- */
:deep(.row-actions) { display: inline-flex; gap: 8px; align-items: center; justify-content: flex-end; flex-wrap: nowrap; }
/* the main step button ends with an arrow, like "Open chart →" */
:deep(.row-actions > a:first-child)::after {
  content: ''; flex-shrink: 0; width: 15px; height: 15px; background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14M13 6l6 6-6 6'/%3E%3C/svg%3E") center / contain no-repeat;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14M13 6l6 6-6 6'/%3E%3C/svg%3E") center / contain no-repeat;
}
:deep(.row-actions .nm-btn-dark), :deep(.row-actions .nm-btn-outline) {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px; min-height: 42px; padding: 0 18px; border-radius: 12px;
  font-size: 13px; font-weight: 800; text-decoration: none; white-space: nowrap; transition: transform 0.15s, background 0.15s;
}
:deep(.row-actions .nm-btn-dark) { background: #004d3a; border: 1px solid #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
:deep(.row-actions .nm-btn-dark:hover) { background: #00382a; transform: translateY(-1px); }
:deep(.row-actions .nm-btn-outline) { background: #f1f6f2; border: 1px solid #dce8e0; color: #004d3a; }
:deep(.row-actions .nm-btn-outline:hover) { background: #e3efe7; }
:deep(.row-actions > a:first-child) { background: #004d3a; border-color: #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
:deep(.row-actions > a:first-child:hover) { background: #00382a; transform: translateY(-1px); }
.pending :deep(.row-actions > a:first-child),
.pending :deep(.row-actions .nm-btn-dark) { background: #efbf04; border-color: #efbf04; color: #004d3a; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
:deep(.icon-btn) { position: relative; flex-shrink: 0; width: 42px; height: 42px; border-radius: 12px; border: 1px solid #dce8e0; display: inline-flex; align-items: center; justify-content: center; color: #004d3a; background: #f1f6f2; transition: background 0.15s; }
:deep(.icon-btn:hover) { background: #e3efe7; }
:deep(.badge) { position: absolute; top: -6px; right: -6px; min-width: 18px; height: 18px; padding: 0 5px; border-radius: 999px; background: #c0392b; border: 2px solid #fff; color: #fff; font-size: 10.5px; font-weight: 800; display: flex; align-items: center; justify-content: center; }

/* ---------- note ---------- */
.mp-note { display: flex; align-items: flex-start; gap: 10px; margin: 16px 0 0; padding: 12px 14px; border-radius: 14px; background: #fff; border-left: 3px solid #1f9d55; font-size: 12.5px; line-height: 1.5; color: #4a5a52; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04); }
.mp-note svg { margin-top: 1px; color: #004d3a; }

/* ---------- phone cards ---------- */
.cards { display: none; }
.card { position: relative; margin: 0; padding: 16px; border-radius: 20px; background: #fff; border: none; box-shadow: var(--sh); }
.card::before { content: ''; position: absolute; left: 0; top: 18px; bottom: 18px; width: 4px; border-radius: 0 4px 4px 0; background: #1f9d55; }
.card + .card { margin-top: 12px; }
.card.muted { opacity: 0.85; }
.card-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 16px; margin: 14px 0; padding-top: 14px; border-top: 1px solid #f0f3f1; }
.cg-wide { grid-column: 1 / -1; }
.k { margin: 0 0 6px; font-size: 10.5px; font-weight: 800; color: #8a9a91; }
.card-actions :deep(.row-actions) { display: flex; justify-content: flex-start; flex-wrap: nowrap; }
.card-actions :deep(.row-actions > a:first-child) { flex: 1; }

@media (max-width: 1200px) {
  .mp-figs { flex-basis: 100%; grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
@media (max-width: 900px) {
  .desktop { display: none; }
  .cards { display: block; }
  .list-panel { padding: 0; overflow: visible; background: transparent; box-shadow: none; }
  .empty-filter { border-radius: 20px; background: #fff; box-shadow: var(--sh); }
  .mp-hero { padding: 20px 18px; border-radius: 22px; }
  .mp-hero-plate { width: 220px; height: 220px; right: -80px; top: 60px; transform: none; opacity: 0.5; }
  .mp-title { font-size: 24px; }
  .mp-figs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .mp-fig { min-width: 0; }
  .mp-tabs { border-radius: 16px; }
  .mp-tools .nm-search { flex: 1; width: auto; }
}
@media (max-width: 760px) {
  .mp-page { padding-bottom: 110px; }
}
@media (max-width: 420px) {
  .card-grid { grid-template-columns: minmax(0, 1fr); }
  .sort { width: 100%; }
  .sort select { flex: 1; }
}

/* search + sort: soft corners like the food search */
.mp-tools .nm-search,
.mp-tools .sort,
.mp-tools label.sort { border-radius: 10px !important; }

/* next appointment: no box, round calendar icon + plain text */
.col-next :deep(.cell-main) { gap: 10px; padding: 0; border: none; border-radius: 0; background: none; font-size: 14.5px; }
.col-next :deep(.cell-main)::before {
  width: 32px; height: 32px; border-radius: 50%;
  background: #e3efe7 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23004D3A' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='3' y='5' width='18' height='16' rx='3'/%3E%3Cpath d='M16 3v4M8 3v4M3 10h18'/%3E%3C/svg%3E") center / 15px no-repeat;
}
.muted .col-next :deep(.cell-main) { background: none; }
.muted .col-next :deep(.cell-main)::before { background-color: #eef2ef; }
.col-next :deep(.next-sub) { margin-top: 4px; padding-left: 42px; }

/* ===== Same look on every tab (Active, New bookings, Needs attention, No meal plan, Discharged, All) ===== */
/* no coloured strip on the left of a row; the pills already say the status */
.mp-table tr td:first-child::before, .card::before { display: none !important; }
/* discharged rows: same colours, not greyed out */
.mp-table tr.muted td { color: inherit; }
.mp-table tr.muted :deep(.nm-avatar), .card.muted :deep(.nm-avatar) { filter: none; opacity: 1; }
.card.muted { opacity: 1; }
.muted :deep(.name-link) { color: inherit; }
.muted :deep(.step.done) { background: #1f8f5c; }
/* every avatar gets the same ring */
.pending :deep(.identity .nm-avatar), .muted :deep(.identity .nm-avatar) { box-shadow: 0 0 0 2.5px #1f8f5c, 0 6px 14px -6px rgba(0, 77, 58, 0.5); }
/* same green "Open chart" button on every row */
.pending :deep(.row-actions > a:first-child),
.pending :deep(.row-actions .nm-btn-dark) { background: #004d3a; border-color: #004d3a; color: #fff; box-shadow: 0 10px 22px -12px rgba(0, 77, 58, 0.7); }
/* empty tab: the same white card as the table */
.empty-filter { border-radius: 20px; background: #fff; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
</style>