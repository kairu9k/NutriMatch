<template>
  <div class="mpl">
    <div class="mpl-head">
      <div>
        <h2 class="nm-panel-title">Choose a patient</h2>
        <p class="nm-panel-sub">Patients waiting on you are listed first.</p>
      </div>
      <label class="nm-search">
        <Search :size="16" />
        <input v-model="search" type="search" placeholder="Search patients" aria-label="Search patients" />
      </label>
    </div>

    <p v-if="loading" class="nm-muted">Loading patients…</p>
    <p v-else-if="error" class="nm-error">{{ error }}</p>
    <div v-else-if="!active.length" class="nm-empty"><Users :size="26" /><p>No active patients yet. Meal plans can be made once a patient's first consultation is confirmed.</p></div>
    <p v-else-if="!groups.some(g => g.items.length)" class="nm-muted">No patients match “{{ search }}”.</p>

    <template v-for="g in groups" :key="g.key">
      <section v-if="g.items.length" class="grp">
        <p class="grp-label"><span class="dot" :class="g.tone" /> {{ g.label }} <span class="count">{{ g.items.length }}</span></p>
        <div v-for="p in g.items" :key="p.id" class="row">
          <img v-if="p.client.profile_photo" :src="p.client.profile_photo" class="nm-avatar" alt="" />
          <span v-else class="nm-avatar">{{ userInitials(p.client.first_name, p.client.last_name) }}</span>
          <div class="main">
            <p class="nm-row-title">{{ p.client.name }}<span v-if="p.condition" class="cond"> · {{ p.condition }}</span></p>
            <p class="nm-row-sub">{{ g.detail(p) }}</p>
          </div>
          <div v-if="g.key === 'on_plan' || g.key === 'needs_update'" class="adh">
            <strong>{{ p.adherence?.pct != null ? `${p.adherence.pct}%` : '—' }}</strong>
            <span>adherence · 7 days</span>
          </div>
          <NuxtLink v-if="g.key === 'not_ready'" :to="`/client-detail/${p.id}?tab=ncp`" class="nm-btn-outline nm-btn-sm">Open NCP</NuxtLink>
          <button v-else type="button" class="nm-btn-sm" :class="g.primary ? 'nm-btn-dark' : 'nm-btn-outline'" @click="emit('pick', p.id)">{{ g.action }}</button>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
// Meal Planning's start screen: the RND picks a patient instead of the page
// opening the first patient's plan. Grouped by what each patient needs.
import { Search, Users } from 'lucide-vue-next'

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
const kcal = v => (v ? `${Math.round(v).toLocaleString('en-PH')} kcal/day` : 'no kcal target')
function bucket(p) {
  const mp = p.meal_plan
  if (mp.plan?.status === 'draft') return 'draft'
  if (mp.plan && mp.outdated) return 'needs_update'
  if (mp.plan) return 'on_plan'
  return mp.ready ? 'needs_plan' : 'not_ready'
}
const DEFS = [
  { key: 'needs_plan', label: 'Needs a meal plan', tone: 'gold', action: 'Create plan', primary: true,
    detail: () => 'NCP Intervention is done — ready for a plan' },
  { key: 'draft', label: 'Draft not sent', tone: 'gold', action: 'Continue', primary: true,
    detail: p => `“${p.meal_plan.plan.name}” · last edited ${shortDate(p.meal_plan.plan.updated_at)} · not sent to the patient yet` },
  { key: 'needs_update', label: 'Needs an update', tone: 'red', action: 'Update plan', primary: true,
    detail: p => `“${p.meal_plan.plan.name}” sent ${shortDate(p.meal_plan.plan.sent_at)} · a newer NCP record was finalized since` },
  { key: 'on_plan', label: 'On a plan', tone: 'green', action: 'Open',
    detail: p => `“${p.meal_plan.plan.name}” · ${kcal(p.meal_plan.plan.target_kcal)} · sent ${shortDate(p.meal_plan.plan.sent_at)}` },
  { key: 'not_ready', label: 'Not ready yet', tone: 'muted',
    detail: () => 'Finish the NCP Intervention (diet prescription and target kcal) first' },
]
const groups = computed(() => {
  const q = search.value.trim().toLowerCase()
  const list = active.value.filter(p => !q || p.client.name.toLowerCase().includes(q) || (p.condition || '').toLowerCase().includes(q))
  return DEFS.map(d => ({ ...d, items: list.filter(p => bucket(p) === d.key).sort((a, b) => a.client.name.localeCompare(b.client.name)) }))
})
</script>

<style scoped>
.mpl { background: #fff; border: 1px solid #eceeec; border-radius: 14px; padding: 22px; font-family: 'Inter', sans-serif; }
.mpl-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
.mpl-head > div { flex: 1 1 220px; }
.grp { margin-top: 16px; }
.grp-label { display: flex; align-items: center; gap: 8px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #6a7a6a; margin: 0 0 2px; }
.grp-label .count { color: #b0bab0; }
.dot { width: 8px; height: 8px; border-radius: 50%; background: #d5dad5; }
.dot.gold { background: #D4A017; }
.dot.red { background: #c0392b; }
.dot.green { background: #1f8f5c; }
.row { display: flex; align-items: center; gap: 12px; padding: 11px 0; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.grp-label + .row { border-top: none; }
.main { flex: 1; min-width: 200px; }
.cond { font-weight: 500; color: #6a7a6a; }
.adh { display: flex; flex-direction: column; align-items: flex-end; min-width: 92px; }
.adh strong { font-size: 1rem; color: #1a3a1a; font-variant-numeric: tabular-nums; }
.adh span { font-size: 0.68rem; color: #8a9a8a; }
@media (max-width: 560px) {
  .mpl { padding: 16px; }
  .adh { align-items: flex-start; }
  .row > .nm-btn-sm { width: 100%; text-align: center; justify-content: center; }
}
</style>
