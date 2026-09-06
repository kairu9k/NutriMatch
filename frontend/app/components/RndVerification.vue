<script setup>
const { get, patch } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const rnds = ref([])
const search = ref('')
const statusFilter = ref('All Status')
const busyId = ref(null)

async function loadRnds() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    rnds.value = await get('/admin/rnds/')
  } catch {
    errorMessage.value = 'Could not load RND applications. Please try again later.'
  } finally {
    isLoading.value = false
  }
}
onMounted(loadRnds)

function statusOf(r) {
  if (!r.is_active) return 'suspended'
  return r.is_verified ? 'verified' : 'pending'
}

const filtered = computed(() => {
  return rnds.value.filter(r => {
    const name = `${r.first_name} ${r.last_name}`.toLowerCase()
    const matchesSearch =
      !search.value ||
      name.includes(search.value.toLowerCase()) ||
      (r.prc_license_number || '').toLowerCase().includes(search.value.toLowerCase())
    const matchesStatus =
      statusFilter.value === 'All Status' || statusOf(r) === statusFilter.value.toLowerCase()
    return matchesSearch && matchesStatus
  })
})

const verifiedCount = computed(() => rnds.value.filter(r => statusOf(r) === 'verified').length)
const pendingCount = computed(() => rnds.value.filter(r => statusOf(r) === 'pending').length)

async function approve(id) {
  busyId.value = id
  try {
    await patch(`/admin/users/${id}/verify-rnd/`)
    const rnd = rnds.value.find(r => r.id === id)
    if (rnd) { rnd.is_verified = true; rnd.verified_at = new Date().toISOString() }
  } catch {
    errorMessage.value = 'Could not approve this RND. Please try again.'
  } finally {
    busyId.value = null
  }
}

async function reject(id) {
  // No dedicated "rejected" state exists in the schema — deactivating the
  // account is the real mechanism behind this, same as Suspend below.
  busyId.value = id
  try {
    await patch(`/admin/users/${id}/toggle-active/`)
    const rnd = rnds.value.find(r => r.id === id)
    if (rnd) rnd.is_active = false
  } catch {
    errorMessage.value = 'Could not reject this RND. Please try again.'
  } finally {
    busyId.value = null
  }
}

async function suspend(id) {
  busyId.value = id
  try {
    await patch(`/admin/users/${id}/toggle-active/`)
    const rnd = rnds.value.find(r => r.id === id)
    if (rnd) rnd.is_active = false
  } catch {
    errorMessage.value = 'Could not suspend this RND. Please try again.'
  } finally {
    busyId.value = null
  }
}

async function reinstate(id) {
  busyId.value = id
  try {
    await patch(`/admin/users/${id}/toggle-active/`)
    const rnd = rnds.value.find(r => r.id === id)
    if (rnd) rnd.is_active = true
  } catch {
    errorMessage.value = 'Could not reinstate this RND. Please try again.'
  } finally {
    busyId.value = null
  }
}

const AVATAR_COLORS = ['bg-emerald-800', 'bg-amber-400', 'bg-indigo-700', 'bg-red-600']
function colorFor(id) { return AVATAR_COLORS[id % AVATAR_COLORS.length] }
function initialsFor(first, last) { return `${(first || '?')[0] ?? ''}${(last || '')[0] ?? ''}`.toUpperCase() }

const statusBadge = (status) => ({
  pending: 'bg-amber-100 text-amber-700',
  verified: 'bg-emerald-100 text-emerald-700',
  suspended: 'bg-red-100 text-red-700'
}[status])

const peso = (n) => `₱${Number(n).toLocaleString()}`
function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<template>
  <div>
    <p v-if="errorMessage" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">{{ errorMessage }}</p>

    <div class="flex items-center justify-between mb-10">
      <div>
        <p class="text-sm text-forest/50">{{ verifiedCount }} verified · {{ pendingCount }} pending</p>
      </div>
      <select v-model="statusFilter" class="border border-forest/15 rounded-lg px-3 py-2 text-sm bg-white">
        <option>All Status</option>
        <option>pending</option>
        <option>verified</option>
        <option>suspended</option>
      </select>
    </div>

    <div class="flex gap-3 mb-6">
      <div class="relative flex-1">
        <NavIcon name="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-forest/40" />
        <input
          v-model="search"
          type="text"
          placeholder="Search RND by name or PRC license..."
          class="w-full border border-forest/25 rounded-lg pl-9 pr-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-forest/20"
        />
      </div>
    </div>

    <div v-if="isLoading" class="text-sm text-forest/50 py-8 text-center">Loading…</div>
    <div v-else-if="!rnds.length" class="text-sm text-forest/50 py-8 text-center">No RND applications yet.</div>
    <div v-else class="space-y-4">
      <p v-if="!filtered.length" class="text-sm text-forest/40 py-8 text-center">No RNDs match your search/filter.</p>
      <TransitionGroup name="list" tag="div" class="relative space-y-4">
        <div
          v-for="rnd in filtered"
          :key="rnd.id"
          class="card-hover rounded-xl border p-5 transition-colors duration-300"
          :class="{
            'bg-amber-50 border-amber-200': statusOf(rnd) === 'pending',
            'bg-white border-forest/10': statusOf(rnd) === 'verified',
            'bg-red-50 border-red-200': statusOf(rnd) === 'suspended'
          }"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <div :class="['w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white', colorFor(rnd.id)]">
                {{ initialsFor(rnd.first_name, rnd.last_name) }}
              </div>
              <div>
                <p class="font-semibold text-forest-dark">{{ rnd.first_name }} {{ rnd.last_name }}</p>
                <p class="text-xs text-forest/50">PRC {{ rnd.prc_license_number }} · {{ rnd.specialization || 'No specialization listed' }}</p>
              </div>
            </div>
            <span :class="['text-xs font-semibold px-3 py-1 rounded-full uppercase transition-colors', statusBadge(statusOf(rnd))]">{{ statusOf(rnd) }}</span>
          </div>

          <Transition name="dropdown" mode="out-in">
            <div v-if="statusOf(rnd) === 'pending'" key="pending" class="grid grid-cols-2 gap-4 text-sm mb-4">
              <div><p class="text-xs text-forest/40 uppercase">Submitted</p><p class="font-medium">{{ fmtDate(rnd.submitted_at) }}</p></div>
              <div><p class="text-xs text-forest/40 uppercase">Specialization</p><p class="font-medium">{{ rnd.specialization || '—' }}</p></div>
            </div>

            <div v-else-if="statusOf(rnd) === 'verified'" key="verified" class="grid grid-cols-3 gap-4 text-sm mb-4">
              <div><p class="text-xs text-forest/40 uppercase">Verified On</p><p class="font-medium">{{ fmtDate(rnd.verified_at) }}</p></div>
              <div><p class="text-xs text-forest/40 uppercase">Patients</p><p class="font-medium">{{ rnd.patients }}</p></div>
              <div><p class="text-xs text-forest/40 uppercase">Rating</p><p class="font-medium">{{ rnd.average_rating ? `★ ${rnd.average_rating}` : '—' }}</p></div>
            </div>

            <div v-else key="suspended" class="bg-red-100 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">
              Account deactivated{{ rnd.is_verified ? ' — was previously verified' : ' — application was rejected' }}.
            </div>
          </Transition>

          <div class="flex gap-3">
            <template v-if="statusOf(rnd) === 'pending'">
              <button class="btn-press flex-1 bg-forest text-white rounded-lg py-2 text-sm font-medium hover:bg-forest-light hover:scale-[1.02]" :disabled="busyId === rnd.id" @click="approve(rnd.id)">Approve</button>
              <button class="btn-press flex-1 border border-red-300 text-red-600 rounded-lg py-2 text-sm font-medium hover:bg-red-50 hover:scale-[1.02]" :disabled="busyId === rnd.id" @click="reject(rnd.id)">Reject</button>
            </template>
            <template v-else-if="statusOf(rnd) === 'verified'">
              <button class="btn-press flex-1 border border-amber-300 text-amber-700 rounded-lg py-2 text-sm font-medium hover:bg-amber-50 hover:scale-[1.02]" :disabled="busyId === rnd.id" @click="suspend(rnd.id)">Suspend</button>
            </template>
            <template v-else>
              <button class="btn-press flex-1 bg-forest text-white rounded-lg py-2 text-sm font-medium hover:bg-forest-light hover:scale-[1.02]" :disabled="busyId === rnd.id" @click="reinstate(rnd.id)">Reinstate</button>
            </template>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>
