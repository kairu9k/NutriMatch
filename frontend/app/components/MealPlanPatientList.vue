<template>
  <div class="mpl">
    <div class="mpl-head">
      <p class="mpl-intro">Pick a patient to build or update their weekly meal plan. Patients waiting on you come first.</p>
      <label class="nm-search">
        <Search :size="16" />
        <input v-model="search" type="search" placeholder="Search patients" aria-label="Search patients" />
      </label>
    </div>

    <p v-if="loading" class="nm-muted">Loading patients…</p>
    <p v-else-if="error" class="nm-error">{{ error }}</p>
    <div v-else-if="!active.length" class="nm-panel mpl-empty">
      <h2 class="mpl-empty-title">No active patients yet</h2>
      <p class="mpl-empty-text">A meal plan can be made once a patient's first consultation is confirmed and their NCP Intervention is done.</p>
    </div>
    <p v-else-if="!groups.some(g => g.items.length)" class="nm-muted">No patients match "{{ search }}".</p>

    <!-- one worklist table; each group is a heading row saying why those patients are in it -->
    <div v-else class="nm-panel mpl-table-wrap">
      <table class="mpl-table">
        <thead>
          <tr><th>Patient</th><th>Meal plan</th><th class="num">7-day adherence</th><th><span class="sr-only">Action</span></th></tr>
        </thead>
        <template v-for="g in groups" :key="g.key">
          <tbody v-if="g.items.length">
            <tr class="grp-row">
              <th colspan="4" scope="colgroup">
                <span class="dot" :class="g.tone" aria-hidden="true" />
                <span class="grp-name">{{ g.label }}</span>
                <span class="grp-count">{{ g.items.length }}</span>
                <span class="grp-why">{{ g.why }}</span>
              </th>
            </tr>
            <tr v-for="p in g.items" :key="p.id" class="prow">
              <td>
                <div class="who">
                  <img v-if="p.client.profile_photo" :src="p.client.profile_photo" class="nm-avatar" alt="" />
                  <span v-else class="nm-avatar">{{ userInitials(p.client.first_name, p.client.last_name) }}</span>
                  <span class="who-text">
                    <span class="name">{{ p.client.name }}</span>
                    <span class="sub">{{ p.condition || 'No condition recorded' }}</span>
                  </span>
                </div>
              </td>
              <td class="plan">
                <template v-if="p.meal_plan.plan">
                  <span class="plan-name">{{ p.meal_plan.plan.name }}</span>
                  <span class="sub">{{ planLine(p) }}</span>
                </template>
                <span v-else class="sub">No plan yet</span>
              </td>
              <td class="num adh">
                <strong v-if="p.meal_plan.plan?.status === 'active'" :class="adhTone(p)">{{ p.adherence?.pct != null ? `${p.adherence.pct}%` : 'No logs' }}</strong>
                <span v-else class="sub">Not on a plan</span>
              </td>
              <td class="act">
                <!-- consultation still ahead: the NCP (and then the plan) comes after it -->
                <NuxtLink v-if="g.key === 'not_ready' && p.stage?.next_step?.key === 'video_call'" :to="p.stage.next_step.link" class="nm-btn-outline nm-btn-sm">{{ p.stage.next_step.label }}</NuxtLink>
                <NuxtLink v-else-if="g.key === 'not_ready'" :to="`/client-detail/${p.id}?tab=ncp`" class="nm-btn-outline nm-btn-sm">Open NCP</NuxtLink>
                <button v-else type="button" class="nm-btn-sm" :class="g.primary ? 'nm-btn-dark' : 'nm-btn-outline'" @click="emit('pick', p.id)">{{ g.action }}</button>
              </td>
            </tr>
          </tbody>
        </template>
      </table>
    </div>
  </div>
</template>

<script setup>
// Meal Planning's start screen: the RND picks a patient instead of the page
// opening the first patient's plan. Grouped by what each patient needs.
import { Search } from 'lucide-vue-next'

const emit = defineEmits(['pick'])
const { get } = useApi()

const rows = ref([])
const loading = ref(true)
const error = ref('')
const search = ref('')
onMounted(async () => {
  try {
    rows.value = await get('/rnd/patients/')
  } catch {
    error.value = 'Could not load your patients.'
  } finally {
    loading.value = false
  }
})

const active = computed(() => rows.value.filter(p => p.status === 'active'))
function bucket(p) {
  const mp = p.meal_plan
  if (mp.plan?.status === 'draft') return 'draft'
  if (mp.plan && mp.outdated) return 'needs_update'
  if (mp.plan) return 'on_plan'
  return mp.ready ? 'needs_plan' : 'not_ready'
}
const DEFS = [
  { key: 'needs_plan', label: 'Needs a meal plan', tone: 'gold', action: 'Create plan', primary: true,
    why: 'Their NCP Intervention is done.' },
  { key: 'draft', label: 'Draft not sent', tone: 'gold', action: 'Continue', primary: true,
    why: "The patient can't see a draft until you send it." },
  { key: 'needs_update', label: 'Needs an update', tone: 'red', action: 'Update plan', primary: true,
    why: 'A newer NCP record was finalized after the plan was sent.' },
  { key: 'on_plan', label: 'On a plan', tone: 'green', action: 'Open',
    why: 'The patient is following a sent plan.' },
  { key: 'not_ready', label: 'Not ready yet', tone: 'muted',
    why: 'A plan needs the NCP Intervention (diet prescription and target kcal), written at or after their consultation.' },
]
function planLine(p) {
  const plan = p.meal_plan.plan
  const kcal = plan.target_kcal ? `${Math.round(plan.target_kcal).toLocaleString('en-PH')} kcal/day, ` : ''
  return plan.status === 'draft' ? `${kcal}last edited ${shortDate(plan.updated_at)}` : `${kcal}sent ${shortDate(plan.sent_at)}`
}
// same 80% goal and 50% alert line as the RND dashboard
function adhTone(p) {
  const v = p.adherence?.pct
  if (v == null) return 'muted'
  return v >= 80 ? 'good' : v < 50 ? 'low' : ''
}
const groups = computed(() => {
  const q = search.value.trim().toLowerCase()
  const list = active.value.filter(p => !q || p.client.name.toLowerCase().includes(q) || (p.condition || '').toLowerCase().includes(q))
  return DEFS.map(d => ({ ...d, items: list.filter(p => bucket(p) === d.key).sort((a, b) => a.client.name.localeCompare(b.client.name)) }))
})
</script>

<style scoped>
.mpl { font-family: 'Inter', sans-serif; }
.mpl-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 18px; }
.mpl-intro { font-size: 0.9rem; color: #4a5a4a; line-height: 1.55; margin: 0; flex: 1 1 320px; max-width: 62ch; }
.mpl-empty { padding: 36px 28px; }
.mpl-empty-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0 0 6px; }
.mpl-empty-text { font-size: 0.88rem; color: #5a6a5a; line-height: 1.55; margin: 0; max-width: 56ch; }

.mpl-table-wrap { padding: 6px 20px 10px; }
.mpl-table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
.mpl-table thead th { text-align: left; font-size: 0.76rem; font-weight: 500; color: #8a9a8a; padding: 12px 12px 8px 0; border-bottom: 1px solid #eef1ee; }
.mpl-table .num { text-align: right; }
.grp-row th { text-align: left; font-weight: 400; padding: 18px 0 8px; border-bottom: 1px solid #eef1ee; }
.grp-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.grp-count { margin-left: 6px; font-size: 0.8rem; color: #8a9a8a; font-variant-numeric: tabular-nums; }
.grp-why { margin-left: 12px; font-size: 0.8rem; color: #7a8a7a; }
.dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #d5dad5; margin-right: 8px; vertical-align: 1px; }
.dot.gold { background: #D4A017; }
.dot.red { background: #c0392b; }
.dot.green { background: #1f8f5c; }
.prow td { padding: 12px 12px 12px 0; border-bottom: 1px solid #f3f5f3; vertical-align: middle; }
.prow:last-child td { border-bottom: none; }
.who { display: flex; align-items: center; gap: 12px; }
.who .nm-avatar { flex-shrink: 0; }
.who-text { display: flex; flex-direction: column; min-width: 0; }
.plan > * { display: block; }
.name, .plan-name { font-weight: 600; color: #1a3a1a; }
.sub { font-size: 0.78rem; color: #7a8a7a; }
.adh strong { font-size: 0.95rem; font-variant-numeric: tabular-nums; color: #1a3a1a; }
.adh strong.good { color: #1f7a4d; }
.adh strong.low { color: #b23b2e; }
.adh strong.muted { color: #8a9a8a; font-weight: 500; font-size: 0.84rem; }
.act { text-align: right; padding-right: 0 !important; white-space: nowrap; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }

/* phones: each patient becomes a small card */
@media (max-width: 760px) {
  .mpl-head .nm-search { flex: 1 1 100%; width: 100%; min-width: 0; }
  .mpl-table-wrap { padding: 4px 16px 10px; }
  .mpl-table thead { display: none; }
  .mpl-table, .mpl-table tbody, .grp-row, .grp-row th, .prow, .prow td { display: block; width: 100%; }
  .grp-why { display: block; margin: 4px 0 0; }
  .prow { padding: 12px 0; border-bottom: 1px solid #f3f5f3; }
  .prow td { border: none; padding: 0; }
  .prow .plan { margin: 8px 0 0 48px; width: auto; }
  .prow .adh { text-align: left; margin: 4px 0 0 48px; width: auto; }
  .prow .act { text-align: left; margin-top: 10px; }
  .prow .act > * { width: 100%; justify-content: center; text-align: center; }
}
</style>
