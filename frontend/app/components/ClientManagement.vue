<script setup>
const { get, patch } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const clients = ref([])
const search = ref('')
const selectedClient = ref('')
const busyId = ref(null)

async function loadClients() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    clients.value = await get('/admin/clients/')
  } catch {
    errorMessage.value = 'Could not load clients. Please try again later.'
  } finally {
    isLoading.value = false
  }
}
onMounted(loadClients)

const activeCount = computed(() => clients.value.filter(c => c.is_active).length)
const inactiveCount = computed(() => clients.value.filter(c => !c.is_active).length)

const filtered = computed(() =>
  clients.value.filter(c => {
    const name = `${c.first_name} ${c.last_name}`.toLowerCase()
    return !search.value || name.includes(search.value.toLowerCase()) || c.email.toLowerCase().includes(search.value.toLowerCase())
  })
)

const AVATAR_COLORS = ['bg-emerald-800', 'bg-amber-400', 'bg-indigo-700', 'bg-red-600']
function colorFor(id) { return AVATAR_COLORS[id % AVATAR_COLORS.length] }
function initialsFor(first, last) { return `${(first || '?')[0] ?? ''}${(last || '')[0] ?? ''}`.toUpperCase() }
function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const actionMsg = ref('')
async function deactivate() {
  if (!selectedClient.value) { actionMsg.value = 'Select a client first.'; return }
  const c = clients.value.find(c => String(c.id) === selectedClient.value)
  if (!c) return
  busyId.value = c.id
  try {
    await patch(`/admin/users/${c.id}/toggle-active/`)
    c.is_active = false
    actionMsg.value = `${c.first_name} ${c.last_name} has been deactivated.`
  } catch {
    actionMsg.value = 'Could not deactivate this account. Please try again.'
  } finally {
    busyId.value = null
  }
}
async function reactivate() {
  if (!selectedClient.value) { actionMsg.value = 'Select a client first.'; return }
  const c = clients.value.find(c => String(c.id) === selectedClient.value)
  if (!c) return
  busyId.value = c.id
  try {
    await patch(`/admin/users/${c.id}/toggle-active/`)
    c.is_active = true
    actionMsg.value = `${c.first_name} ${c.last_name}'s account has been reactivated.`
  } catch {
    actionMsg.value = 'Could not reactivate this account. Please try again.'
  } finally {
    busyId.value = null
  }
}
</script>

<template>
  <div class="grid grid-cols-3 gap-6">
    <div class="col-span-2">
      <p v-if="errorMessage" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">{{ errorMessage }}</p>

      <div class="flex items-center justify-between mb-10">
        <p class="text-sm text-forest/50">{{ clients.length }} registered clients</p>
      </div>

      <div class="flex gap-3 mb-6">
        <div class="relative flex-1">
          <NavIcon name="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-forest/40" />
          <input v-model="search" type="text" placeholder="Search client by name or email..."
            class="w-full border border-forest/25 rounded-lg pl-9 pr-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-forest/20" />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4 mb-6">
        <div class="animate-in stagger-1 border border-forest/15 card-hover bg-emerald-50 rounded-xl p-4 text-center">
          <p class="text-2xl font-display text-emerald-700 animate-pop">{{ activeCount }}</p>
          <p class="text-xs text-forest/50">Active</p>
        </div>
        <div class="animate-in stagger-2 border border-forest/15 card-hover bg-amber-50 rounded-xl p-4 text-center">
          <p class="text-2xl font-display text-amber-600 animate-pop">{{ inactiveCount }}</p>
          <p class="text-xs text-forest/50">Inactive</p>
        </div>
      </div>

      <div v-if="isLoading" class="text-sm text-forest/50 py-8 text-center">Loading…</div>
      <div v-else-if="!clients.length" class="text-sm text-forest/50 py-8 text-center">No clients registered yet.</div>
      <template v-else>
        <p v-if="!filtered.length" class="text-sm text-forest/40 py-8 text-center">No clients match your search.</p>
        <TransitionGroup name="list" tag="div" class="relative space-y-3">
          <div
            v-for="c in filtered"
            :key="c.id"
            class="card-hover rounded-xl border p-4 transition-colors duration-300"
            :class="c.is_active ? 'bg-white border-forest/10' : 'bg-amber-50 border-amber-200'"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-3">
                <div :class="['w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white', colorFor(c.id)]">
                  {{ initialsFor(c.first_name, c.last_name) }}
                </div>
                <div>
                  <p class="font-semibold text-forest-dark text-sm">{{ c.first_name }} {{ c.last_name }}</p>
                  <p class="text-xs text-forest/50">{{ c.email }}{{ c.condition ? ' · ' + c.condition : '' }}</p>
                </div>
              </div>
              <div class="text-right">
                <span :class="['text-xs font-semibold px-3 py-1 rounded-full transition-colors', c.is_active ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700']">
                  {{ c.is_active ? 'Active' : 'Inactive' }}
                </span>
                <p class="text-xs text-forest/40 mt-1">{{ c.matched_rnd ? `Matched: ${c.matched_rnd}` : 'Unmatched' }}</p>
              </div>
            </div>
            <div class="grid grid-cols-3 text-xs text-forest/50 mt-2">
              <div><span class="uppercase text-forest/40">Joined</span><br /><span class="font-medium text-forest-dark">{{ fmtDate(c.created_at) }}</span></div>
              <div><span class="uppercase text-forest/40">Consultations</span><br /><span class="font-medium text-forest-dark">{{ c.consultations }}</span></div>
              <div><span class="uppercase text-forest/40">Last Active</span><br /><span class="font-medium text-forest-dark">{{ c.last_active ? fmtDate(c.last_active) : '—' }}</span></div>
            </div>
          </div>
        </TransitionGroup>
      </template>
    </div>

    <div>
      <div class="animate-in bg-white rounded-2xl p-5 mb-4">
        <h3 class="font-display text-normal text-forest-dark mb-3">Account Actions</h3>
        <select v-model="selectedClient" class="w-full border border-forest/25 rounded-lg px-3 py-2.5 text-sm mb-3 bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20">
          <option value="">Select client...</option>
          <option v-for="c in clients" :key="c.id" :value="String(c.id)">{{ c.first_name }} {{ c.last_name }}</option>
        </select>
        <button class="btn-press w-full border border-red-300 text-red-600 rounded-lg py-2.5 text-sm font-medium mb-2 hover:bg-red-50 hover:scale-[1.01]" :disabled="busyId !== null" @click="deactivate">
          Deactivate account
        </button>
        <button class="btn-press w-full border border-forest/15 rounded-lg py-2.5 text-sm font-medium hover:bg-cream-soft hover:scale-[1.01]" :disabled="busyId !== null" @click="reactivate">
          Reactivate account
        </button>
        <Transition name="dropdown">
          <p v-if="actionMsg" class="text-xs text-forest/60 mt-3">{{ actionMsg }}</p>
        </Transition>
      </div>

      <div class="animate-in stagger-1 bg-indigo-50 border border-indigo-100 rounded-xl p-4 flex gap-3">
        <span class="text-indigo-500 text-lg leading-none">🛡</span>
        <div>
          <p class="text-sm font-semibold text-indigo-800">Data privacy reminder</p>
          <p class="text-sm text-indigo-700">Client records are RA 10173-protected. Access is limited to resolving disputes and account issues.</p>
        </div>
      </div>
    </div>
  </div>
</template>
