<script setup>
import { platformStats } from '~/mock/mockAdminDatabase'

const stats = platformStats

const conditions = ref([
  { name: 'Diabetes Mellitus', pct: 42, color: 'bg-emerald-700' },
  { name: 'Weight Management', pct: 25, color: 'bg-blue-600' },
  { name: 'Renal Disease', pct: 12, color: 'bg-purple-600' },
  { name: 'Hypertension', pct: 28, color: 'bg-amber-400' }
])

const rndPerformance = ref([
  { rnd: 'RND Reyes', patients: 12, consults: 47, revenue: 15800, rating: 4.8, status: 'Active' },
  { rnd: 'RND Alba', patients: 8, consults: 31, revenue: 9400, rating: 4.5, status: 'Active' },
  { rnd: 'RND Felizarta', patients: 8, consults: 31, revenue: 9400, rating: 4.5, status: 'Active' },
  { rnd: 'RND Espantaleon', patients: 8, consults: 31, revenue: 9400, rating: 4.5, status: 'Active' },
  { rnd: 'RND Libunax', patients: 8, consults: 31, revenue: 9400, rating: 4.5, status: 'Active' },
  { rnd: 'RND Aiai', patients: 8, consults: 31, revenue: 9400, rating: 4.5, status: 'Active' },
  { rnd: 'RND Garcia', patients: 0, consults: 0, revenue: null, rating: null, status: 'Suspended' }
])

const reportTypes = ['Platform Summary', 'RND Performance', 'Client Outcomes', 'Financial Report', 'Audit Export']
const selectedReport = ref('Platform Summary')
const dateRange = ref('Last 30 days')
const format = ref('PDF')
const generating = ref(false)
const generatedMsg = ref('')

function generateReport() {
  generating.value = true
  generatedMsg.value = ''
  setTimeout(() => {
    generating.value = false
    generatedMsg.value = `${selectedReport.value} report generated (${format.value}, ${dateRange.value}). This is a frontend-only demo — no file is produced.`
  }, 900)
}

const peso = (n) => (n == null ? '—' : `₱${Number(n).toLocaleString()}`)
</script>

<template>
  <div>
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="animate-in stagger- border border-forest/15 card-hover bg-white rounded-2xl p-5">
        <p class="text-xs text-forest/50">Total Consultations</p>
        <p class="text-2xl font-display text-forest-dark animate-pop">{{ stats.totalConsultations }}</p>
        <p class="text-xs text-emerald-700">↑ 28 from April</p>
        <div class="h-1.5 bg-cream-soft rounded-full mt-2 overflow-hidden"><div class="h-1.5 bg-forest rounded-full transition-all duration-700 ease-out" style="width:70%" /></div>
      </div>
      <div class="animate-in stagger-2 border border-forest/15 card-hover bg-white rounded-2xl p-5">
        <p class="text-xs text-forest/50">Platform Revenue</p>
        <p class="text-2xl font-display text-forest-dark animate-pop">{{ peso(stats.grossRevenue) }}</p>
        <div class="h-1.5 bg-cream-soft rounded-full mt-2 overflow-hidden"><div class="h-1.5 bg-forest rounded-full transition-all duration-700 ease-out" style="width:80%" /></div>
      </div>
      <div class="animate-in stagger-3 border border-forest/15 card-hover bg-white rounded-2xl p-5">
        <p class="text-xs text-forest/50">Avg. Client Retention</p>
        <p class="text-2xl font-display text-forest-dark animate-pop">86%</p>
        <p class="text-xs text-forest/40">Platform-wide</p>
        <div class="h-1.5 bg-cream-soft rounded-full mt-2 overflow-hidden"><div class="h-1.5 bg-gold rounded-full transition-all duration-700 ease-out" style="width:86%" /></div>
      </div>
      <div class="animate-in stagger-4 border border-forest/15 card-hover bg-white rounded-2xl p-5">
        <p class="text-xs text-forest/50">Avg. RND Rating</p>
        <p class="text-2xl font-display text-forest-dark animate-pop">4.7/5</p>
        <p class="text-xs text-forest/40">★★★★★ across 24 RNDs</p>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-6">
      <div class="col-span-2 space-y-6">
        <div class="animate-in stagger-2 bg-white rounded-2xl p-6">
          <h3 class="font-display text-lg text-forest-dark mb-4">Client Condition Distribution</h3>
          <div v-for="(c, i) in conditions" :key="c.name" class="mb-4 last:mb-0">
            <div class="flex justify-between text-sm mb-1">
              <span class="font-medium">{{ c.name }}</span><span class="font-semibold">{{ c.pct }}%</span>
            </div>
            <div class="h-2.5 bg-cream-soft rounded-full overflow-hidden">
              <div
                :class="['h-2.5 rounded-full transition-all ease-out', c.color]"
                :style="{ width: c.pct + '%', transitionDuration: '800ms', transitionDelay: (i * 80) + 'ms' }"
              />
            </div>
          </div>
        </div>

        <div class="animate-in stagger-3 bg-white rounded-2xl p-6">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h3 class="font-display text-lg text-forest-dark">RND Performance Overview</h3>
              <p class="text-xs text-forest/40">Consultation volume, revenue, and ratings by practitioner</p>
            </div>
            <button class="text-sm text-forest hover:underline transition-colors"> Export</button>
          </div>
          <table class="w-full text-sm">
            <thead>
              <tr class="text-xs text-forest/40 uppercase text-left border-b border-forest/10">
                <th class="pb-2">RND</th><th>Patients</th><th>Consults</th><th>Revenue</th><th>Rating</th><th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="r in rndPerformance" :key="r.rnd" class="border-b border-forest/5 last:border-0 hover:bg-cream-soft/40 transition-colors" :class="r.status === 'Suspended' ? 'text-forest/30' : ''">
                <td class="py-3 font-medium">{{ r.rnd }}</td>
                <td>{{ r.patients }}</td>
                <td>{{ r.consults }}</td>
                <td>{{ peso(r.revenue) }}</td>
                <td>{{ r.rating ? `★ ${r.rating}` : '—' }}</td>
                <td>
                  <span :class="['text-xs font-semibold px-2 py-0.5 rounded-full', r.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-600']">{{ r.status }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="animate-in stagger-4 bg-white rounded-2xl p-6 h-fit">
        <h3 class="font-display text-lg text-forest-dark mb-1">Generate Custom Report</h3>
        <p class="text-xs text-forest/40 mb-4">Choose a report type and export range</p>

        <p class="text-xs text-forest/50 uppercase mb-2">Report Type</p>
        <div class="space-y-1 mb-4">
          <label v-for="t in reportTypes" :key="t" class="flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer text-sm transition-colors duration-150"
            :class="selectedReport === t ? 'bg-forest text-white' : 'hover:bg-cream-soft'">
            <input type="radio" class="accent-gold" :value="t" v-model="selectedReport" />
            {{ t }}
          </label>
        </div>

        <label class="text-xs text-forest/50 uppercase">Date Range</label>
        <select v-model="dateRange" class="w-full border border-forest/15 rounded-lg px-3 py-2 text-sm mb-3 mt-1 bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20">
          <option>Last 7 days</option>
          <option>Last 30 days</option>
          <option>This quarter</option>
          <option>Custom range</option>
        </select>

        <label class="text-xs text-forest/50 uppercase">Format</label>
        <select v-model="format" class="w-full border border-forest/15 rounded-lg px-3 py-2 text-sm mb-4 mt-1 bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20">
          <option>PDF</option>
          <option>CSV</option>
          <option>XLSX</option>
        </select>

        <button class="btn-press w-full bg-forest text-white rounded-lg py-2.5 text-sm font-medium hover:bg-forest-light hover:scale-[1.01] disabled:opacity-60 disabled:hover:scale-100 flex items-center justify-center gap-2" :disabled="generating" @click="generateReport">
          <svg v-if="generating" class="spin w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="9" stroke-opacity=".25" /><path d="M21 12a9 9 0 0 0-9-9" stroke-linecap="round" /></svg>
          {{ generating ? 'Generating…' : ' Generate Report' }}
        </button>
        <Transition name="dropdown">
          <p v-if="generatedMsg" class="text-xs text-emerald-700 mt-3">{{ generatedMsg }}</p>
        </Transition>
      </div>
    </div>
  </div>
</template>
