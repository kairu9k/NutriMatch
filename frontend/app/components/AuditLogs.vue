<script setup>
const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const logs = ref([])
const search = ref('')
const eventType = ref('All Event Types')

async function loadLogs() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    logs.value = await get('/admin/audit-logs/')
  } catch {
    errorMessage.value = 'Could not load audit logs. Please try again later.'
  } finally {
    isLoading.value = false
  }
}
onMounted(loadLogs)

const eventTypes = computed(() => ['All Event Types', ...new Set(logs.value.map(l => l.action))])

const filtered = computed(() =>
  logs.value.filter(l => {
    const matchesSearch = !search.value ||
      l.action.toLowerCase().includes(search.value.toLowerCase()) ||
      (l.ip_address || '').includes(search.value) ||
      (l.user ? `${l.user.first_name} ${l.user.last_name}`.toLowerCase().includes(search.value.toLowerCase()) : false)
    const matchesType = eventType.value === 'All Event Types' || l.action === eventType.value
    return matchesSearch && matchesType
  })
)

function fmtDateTime(iso) {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}

function detailFor(log) {
  const parts = []
  if (log.user) parts.push(`${log.user.first_name} ${log.user.last_name}`)
  if (log.table_name) parts.push(`Table: ${log.table_name}`)
  if (log.record_id) parts.push(`Record #${log.record_id}`)
  return parts.join(' · ') || '—'
}
</script>

<template>
  <div class="grid grid-cols-4 gap-6">
    <div class="col-span-3">
      <p v-if="errorMessage" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">{{ errorMessage }}</p>

      <div class="grid grid-cols-2 gap-3 mb-5">
        <div class="relative">
          <NavIcon name="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-forest/40" />
          <input v-model="search" type="text" placeholder="Search by action, IP, or user..."
            class="w-full border border-forest/25 rounded-lg pl-9 pr-3 py-2.5 text-sm bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />
        </div>
        <select v-model="eventType" class="border border-forest/15 rounded-lg px-3 py-2.5 text-sm bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20">
          <option v-for="t in eventTypes" :key="t">{{ t }}</option>
        </select>
      </div>

      <div v-if="isLoading" class="text-sm text-forest/50 py-10 text-center bg-white rounded-2xl">Loading…</div>
      <div v-else class="animate-in bg-white rounded-2xl p-2">
        <TransitionGroup name="list" tag="div" class="relative">
          <div
            v-for="log in filtered"
            :key="log.id"
            class="flex items-center justify-between gap-4 border-l-4 border-forest/20 rounded-lg px-4 py-3 mb-1 transition-colors duration-200 hover:bg-cream-soft"
          >
            <div>
              <p class="text-sm font-semibold text-forest-dark">{{ log.action }}</p>
              <p class="text-xs text-forest/50">{{ detailFor(log) }}</p>
              <p class="text-xs text-forest/35">{{ fmtDateTime(log.created_at) }}{{ log.ip_address ? ' · IP: ' + log.ip_address : '' }}</p>
            </div>
          </div>
        </TransitionGroup>
        <div v-if="filtered.length === 0" class="text-center text-sm text-forest/40 py-10 animate-in">
          {{ logs.length === 0 ? 'No audit events recorded yet.' : 'No matching audit events.' }}
        </div>
      </div>
    </div>

    <div class="space-y-4">
      <div class="animate-in bg-white border border-forest/15 rounded-2xl p-5">
        <h3 class="font-display text-lg text-forest-dark mb-3">Activity Snapshot</h3>
        <div class="flex justify-between text-sm py-2 border-b border-forest/5">
          <span class="text-forest/50">Total events</span><span class="font-semibold">{{ logs.length }}</span>
        </div>
        <div class="flex justify-between text-sm py-2">
          <span class="text-forest/50">Event types</span><span class="font-semibold">{{ eventTypes.length - 1 }}</span>
        </div>
      </div>
      <div class="animate-in stagger-1 bg-white rounded-2xl p-5 flex gap-3">
        <span class="text-forest text-lg leading-none">🔒</span>
        <div>
          <p class="text-sm font-semibold text-forest-dark">Immutable by design</p>
          <p class="text-sm text-forest/50">Audit rows are never updated or deleted, fulfilling the RA 10173 audit-logging mandate.</p>
        </div>
      </div>
    </div>
  </div>
</template>
