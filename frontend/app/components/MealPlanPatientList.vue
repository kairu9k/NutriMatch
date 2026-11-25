<template>
  <div class="mpl">
    <section class="mpl-head">
      <img class="mpl-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="mpl-fade" aria-hidden="true"></span>
      <div class="mpl-head-txt">
        <p class="mpl-eyebrow"><span aria-hidden="true"></span>Meal planning</p>
        <h2 class="mpl-title">Weekly meal plans</h2>
        <p class="mpl-intro">Pick a patient to build or update their weekly meal plan. Patients waiting on you come first.</p>
      </div>
    </section>

    <!-- search sits under the hero, on its own row -->
    <div class="mpl-bar">
      <label class="nm-search mpl-search">
        <Search :size="17" />
        <input v-model="search" type="search" placeholder="Search patients by name or condition" aria-label="Search patients" />
      </label>
    </div>

    <p v-if="loading" class="nm-muted mpl-state"><span class="mpl-spin" aria-hidden="true"></span> Loading patients…</p>
    <p v-else-if="error" class="nm-error">{{ error }}</p>
    <div v-else-if="!active.length" class="nm-panel mpl-empty">
      <h2 class="mpl-empty-title">No active patients yet</h2>
      <p class="mpl-empty-text">A meal plan can be made once a patient's first consultation is confirmed and their NCP Intervention is done.</p>
    </div>
    <p v-else-if="!groups.some(g => g.items.length)" class="nm-muted mpl-state">No patients match "{{ search }}".</p>

    <!-- one worklist table; each group is a heading row saying why those patients are in it -->
    <div v-else class="nm-panel mpl-table-wrap">
      <table class="mpl-table">
        <thead>
          <tr><th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg> Patient</th><th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" /></svg> Meal plan</th><th class="num"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8" /><path d="M14 7h7v7" /></svg> 7-day adherence</th><th><span class="sr-only">Action</span></th></tr>
        </thead>
        <template v-for="g in groups" :key="g.key">
          <tbody v-if="g.items.length" :class="'tone-' + g.tone">
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
async function load({ quiet = false } = {}) {
  try {
    rows.value = await get('/rnd/patients/')
  } catch {
    if (!quiet) error.value = 'Could not load your patients.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
useAutoRefresh(() => load({ quiet: true }))

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
    why: 'A plan needs the NCP Intervention (diet prescription and TER), written at or after their consultation.' },
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
</script>
<style scoped>
.mpl {
  --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22);
  font-family: 'DM Sans', sans-serif; color: #22362c;
}
.ic { flex-shrink: 0; }

/* ---------- hero ---------- */
.mpl-head {
  position: relative; overflow: hidden; display: flex; align-items: flex-end; justify-content: space-between; gap: 18px 24px; flex-wrap: wrap;
  margin-bottom: 18px; padding: 26px 30px; border-radius: 24px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.mpl-head > *:not(.mpl-plate):not(.mpl-fade) { position: relative; z-index: 1; }
.mpl-plate { position: absolute; right: -60px; top: 50%; width: 320px; height: 320px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.mpl-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 55%, rgba(0, 77, 58, 0.82) 70%, rgba(0, 77, 58, 0.55) 100%); }
.mpl-head-txt { flex: 1 1 360px; min-width: 0; max-width: 600px; }
.mpl-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.mpl-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.mpl-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.mpl-intro { margin: 0; max-width: 62ch; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }
.mpl-search { display: flex; align-items: center; gap: 10px; width: 320px; max-width: 100%; height: 46px; margin: 0; padding: 0 16px; border-radius: 999px; background: #fff; border: none; color: #8a9a91; box-sizing: border-box; box-shadow: 0 10px 22px -12px rgba(0, 0, 0, 0.5); }
.mpl-search:focus-within { box-shadow: 0 0 0 4px rgba(239, 191, 4, 0.45); }
.mpl-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.mpl-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }

/* ---------- states ---------- */
.mpl-state { display: flex; align-items: center; justify-content: center; gap: 10px; margin: 0; padding: 36px 20px; border-radius: 22px; background: #fff; box-shadow: var(--sh); font-weight: 600; }
.mpl-spin { width: 20px; height: 20px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: mpl-spin 0.8s linear infinite; }
@keyframes mpl-spin { to { transform: rotate(360deg); } }
.mpl-empty { padding: 40px 28px; border: none; border-radius: 22px; text-align: center; box-shadow: var(--sh); }
.mpl-empty-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.mpl-empty-text { margin: 0 auto; max-width: 56ch; font-size: 13.5px; line-height: 1.55; color: #6b7d73; }

/* ---------- table ---------- */
.mpl-table-wrap { padding: 0; border: none; border-radius: 24px; overflow: hidden; box-shadow: var(--sh); }
.mpl-table { width: 100%; border-collapse: collapse; font-size: 14px; }
.mpl-table thead th {
  padding: 14px 18px; text-align: left; background: #eaf3ed; border-bottom: 1px solid #dcebe1;
  font-size: 13px; font-weight: 700; color: #1f5c45; white-space: nowrap;
}
.mpl-table thead th .ic { margin-right: 6px; vertical-align: -2px; color: #1f7a4d; }
.mpl-table thead th:first-child, .prow td:first-child, .grp-row th { padding-left: 24px; }
.mpl-table thead th:last-child, .prow td:last-child { padding-right: 24px; }
.mpl-table .num { text-align: left; }

/* group heading rows */
.grp-row th { text-align: left; font-weight: 400; padding-top: 11px; padding-bottom: 11px; background: #fafcfb; border-bottom: 1px solid #f0f3f1; border-top: 1px solid #f0f3f1; }
tbody:first-of-type .grp-row th { border-top: none; }
.dot { display: inline-block; width: 8px; height: 8px; margin-right: 10px; border-radius: 50%; background: #c9d3cd; vertical-align: 1px; box-shadow: 0 0 0 3px #eef2ef; }
.dot.gold { background: #efbf04; box-shadow: 0 0 0 3px #fff4d6; }
.dot.red { background: #c0392b; box-shadow: 0 0 0 3px #fdecea; }
.dot.green { background: #1f9d55; box-shadow: 0 0 0 3px #e3f4ea; }
.grp-name { font-size: 14px; font-weight: 700; color: #0e3a2c; }
.grp-count { margin-left: 8px; font-size: 12.5px; font-weight: 700; color: #8a9a91; font-variant-numeric: tabular-nums; }
.grp-why { margin-left: 10px; font-size: 13px; color: #6b7d73; }

/* patient rows */
.prow td { position: relative; padding: 18px; border-bottom: 1px solid #f0f3f1; vertical-align: middle; transition: background 0.15s; }
.prow:hover td { background: #fafcfb; }
tbody:last-of-type .prow:last-child td { border-bottom: none; }
.prow td:first-child::before { content: ''; position: absolute; left: 0; top: 18px; bottom: 18px; width: 4px; border-radius: 0 4px 4px 0; background: #c9d3cd; }
.tone-green .prow td:first-child::before { background: #1f9d55; }
.tone-gold .prow td:first-child::before { background: #efbf04; }
.tone-red .prow td:first-child::before { background: #c0392b; }
.who { display: flex; align-items: center; gap: 12px; }
.who .nm-avatar {
  flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%; object-fit: cover; box-sizing: border-box;
  display: inline-flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800;
  background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; border: 2px solid #fff; box-shadow: 0 0 0 2.5px #1f9d55;
}
.tone-gold .who .nm-avatar { box-shadow: 0 0 0 2.5px #efbf04; }
.tone-red .who .nm-avatar { box-shadow: 0 0 0 2.5px #c0392b; }
.tone-muted .who .nm-avatar { box-shadow: 0 0 0 2.5px #c9d3cd; }
.who-text { display: flex; flex-direction: column; min-width: 0; }
.plan > * { display: block; }
.name, .plan-name { font-size: 14.5px; font-weight: 700; color: #0e3a2c; }
.sub { margin-top: 2px; font-size: 13px; color: #6b7d73; }
.adh strong { font-size: 15px; font-weight: 800; font-variant-numeric: tabular-nums; color: #0e3a2c; }
.adh strong.good { color: #1f7a4d; }
.adh strong.low { color: #b42318; }
.adh strong.muted, .adh .sub { display: inline-flex; padding: 4px 11px; border-radius: 999px; background: #f3f6f4; font-size: 12.5px; font-weight: 600; color: #6b7d73; }
.act { text-align: right; white-space: nowrap; }
.act .nm-btn-sm { display: inline-flex; align-items: center; gap: 7px; min-height: 40px; padding: 0 18px; border-radius: 12px; font-size: 13.5px; font-weight: 800; text-decoration: none; transition: background 0.15s, transform 0.15s; }
.act button.nm-btn-sm { background: #004d3a; border: 1px solid #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); cursor: pointer; }
.act button.nm-btn-sm:hover { background: #00382a; transform: translateY(-1px); }
.act button.nm-btn-sm::after {
  content: ''; width: 15px; height: 15px; background: currentColor;
  -webkit-mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14M13 6l6 6-6 6'/%3E%3C/svg%3E") center / contain no-repeat;
          mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2.4' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12h14M13 6l6 6-6 6'/%3E%3C/svg%3E") center / contain no-repeat;
}
.act a.nm-btn-sm { background: #f1f6f2; border: 1px solid #dce8e0; color: #004d3a; }
.act a.nm-btn-sm:hover { background: #e3efe7; }
.act button.nm-btn-sm:focus-visible, .act a.nm-btn-sm:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }

/* phones: each patient becomes a small card */
@media (max-width: 760px) {
  .mpl-head { padding: 20px 18px; border-radius: 22px; }
  .mpl-title { font-size: 24px; }
  .mpl-plate { width: 200px; height: 200px; right: -70px; top: 40px; transform: none; }
  .mpl-head .mpl-search { flex: 1 1 100%; width: 100%; min-width: 0; }
  .mpl-table thead { display: none; }
  .mpl-table, .mpl-table tbody, .grp-row, .grp-row th, .prow, .prow td { display: block; width: 100%; box-sizing: border-box; }
  .grp-row th { padding: 12px 16px; }
  .grp-why { display: block; margin: 4px 0 0 18px; }
  .prow { position: relative; padding: 14px 16px; border-bottom: 1px solid #f0f3f1; }
  .prow td { border: none; padding: 0 !important; background: none !important; }
  .prow td:first-child::before { top: 14px; bottom: 14px; left: -16px; }
  .prow .plan { margin: 10px 0 0 56px; width: auto; }
  .prow .adh { text-align: left; margin: 8px 0 0 56px; width: auto; }
  .prow .act { text-align: left; margin-top: 12px; }
  .prow .act > * { width: 100%; justify-content: center; text-align: center; }
}

/* search row under the hero */
.mpl-bar { display: flex; align-items: center; gap: 12px; margin: 28px 0 22px; }
.mpl-bar .mpl-search { flex: 0 1 380px !important; width: 380px !important; max-width: 100% !important; height: 42px !important; padding: 0 14px !important; border: 1px solid #d9e0dc !important; border-radius: 10px !important; background: #fff !important; color: #8a9a91; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.04) !important; box-sizing: border-box; }
.mpl-bar .mpl-search:hover { border-color: #c2ccc6 !important; }
.mpl-bar .mpl-search:focus-within { border-color: #004d3a !important; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.1) !important; color: #1f7a4d; }
.mpl-bar .mpl-search input { font-size: 14px; color: #14261e !important; }
.mpl-bar .mpl-search input::placeholder { color: #8a9a91; }
.mpl .ic { display: inline-block; flex-shrink: 0; }
.mpl-table thead th { white-space: nowrap; }
@media (max-width: 760px) { .mpl-bar .mpl-search { flex: 1 1 100% !important; width: 100% !important; } }
</style>