<script setup>
const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const stats = ref({
  active_rnds: 0, clients: 0, new_registrations: 0,
  total_consultations: 0, gross_revenue: 0,
})
const rnds = ref([])

async function loadData() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [platformStats, rndList] = await Promise.all([
      get('/admin/platform-stats/'),
      get('/admin/rnds/'),
    ])
    stats.value = platformStats
    rnds.value = rndList.filter(r => r.is_verified)
  } catch {
    errorMessage.value = 'Could not load report data. Please try again later.'
  } finally {
    isLoading.value = false
  }
}
onMounted(loadData)

const rndPerformance = computed(() =>
  [...rnds.value].sort((a, b) => b.consultations - a.consultations)
)

const peso = (n) => (n == null ? '—' : `₱${Number(n).toLocaleString()}`)
</script>

<template>
  <div>
    <p v-if="errorMessage" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">{{ errorMessage }}</p>

    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="animate-in stagger-1 border border-forest/15 card-hover bg-white rounded-2xl p-5">
        <p class="text-xs text-forest/50">Total Consultations</p>
        <p class="text-2xl font-display text-forest-dark animate-pop">{{ stats.total_consultations }}</p>
        <p class="text-xs text-forest/40">All-time completed</p>
      </div>
      <div class="animate-in stagger-2 border border-forest/15 card-hover bg-white rounded-2xl p-5">
        <p class="text-xs text-forest/50">Platform Revenue</p>
        <p class="text-2xl font-display text-forest-dark animate-pop">{{ peso(stats.gross_revenue) }}</p>
        <p class="text-xs text-forest/40">This month, paid invoices</p>
      </div>
      <div class="animate-in stagger-3 border border-forest/15 card-hover bg-white rounded-2xl p-5">
        <p class="text-xs text-forest/50">Active RNDs / Clients</p>
        <p class="text-2xl font-display text-forest-dark animate-pop">{{ stats.active_rnds }} / {{ stats.clients }}</p>
        <p class="text-xs text-forest/40">{{ stats.new_registrations }} new registrations (30d)</p>
      </div>
    </div>

    <div class="bg-white rounded-2xl p-6">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="font-display text-lg text-forest-dark">RND Performance Overview</h3>
          <p class="text-xs text-forest/40">Consultation volume, revenue, and ratings by practitioner</p>
        </div>
      </div>

      <div v-if="isLoading" class="text-sm text-forest/50 py-8 text-center">Loading…</div>
      <div v-else-if="!rndPerformance.length" class="text-sm text-forest/50 py-8 text-center">No verified RNDs yet.</div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="text-xs text-forest/40 uppercase text-left border-b border-forest/10">
            <th class="pb-2">RND</th><th>Patients</th><th>Consults</th><th>Revenue</th><th>Rating</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rndPerformance" :key="r.id" class="border-b border-forest/5 last:border-0 hover:bg-cream-soft/40 transition-colors">
            <td class="py-3 font-medium">{{ r.first_name }} {{ r.last_name }}</td>
            <td>{{ r.patients }}</td>
            <td>{{ r.consultations }}</td>
            <td>{{ peso(r.revenue) }}</td>
            <td>{{ r.average_rating ? `★ ${r.average_rating}` : '—' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
