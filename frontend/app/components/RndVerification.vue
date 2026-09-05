<script setup>
import { rnds, platformStats } from '~/mock/mockAdminDatabase'

const stats = platformStats

const search = ref('')
const statusFilter = ref('All Status')

const filtered = computed(() => {
  return rnds.value.filter(r => {
    const matchesSearch =
      !search.value ||
      r.name.toLowerCase().includes(search.value.toLowerCase()) ||
      r.license.toLowerCase().includes(search.value.toLowerCase())
    const matchesStatus =
      statusFilter.value === 'All Status' || r.status === statusFilter.value.toLowerCase()
    return matchesSearch && matchesStatus
  })
})

const verifiedCount = computed(() => rnds.value.filter(r => r.status === 'verified').length)
const pendingCount = computed(() => rnds.value.filter(r => r.status === 'pending').length)

function approve(id) {
  const rnd = rnds.value.find(r => r.id === id)
  rnd.status = 'verified'
  rnd.verifiedOn = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  rnd.patients = 0
  rnd.rating = null
  rnd.revenue = 0
  stats.value.activeRnds++
  stats.value.pendingVerif = Math.max(0, stats.value.pendingVerif - 1)
}
function reject(id) {
  rnds.value = rnds.value.filter(r => r.id !== id)
  stats.value.pendingVerif = Math.max(0, stats.value.pendingVerif - 1)
}
function suspend(id) {
  const rnd = rnds.value.find(r => r.id === id)
  rnd.status = 'suspended'
  rnd.suspendReason = `Suspended by admin — ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  stats.value.activeRnds = Math.max(0, stats.value.activeRnds - 1)
}
function reinstate(id) {
  const rnd = rnds.value.find(r => r.id === id)
  rnd.status = 'verified'
  stats.value.activeRnds++
}

const statusBadge = (status) => ({
  pending: 'bg-amber-100 text-amber-700',
  verified: 'bg-emerald-100 text-emerald-700',
  suspended: 'bg-red-100 text-red-700'
}[status])

const peso = (n) => `₱${Number(n).toLocaleString()}`
</script>

<template>
  <div>
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
      <button class="bg-forest text-white px-5 rounded-lg text-sm font-medium">Search</button>
    </div>

    <div class="space-y-4">
      <TransitionGroup name="list" tag="div" class="relative space-y-4">
        <div
          v-for="rnd in filtered"
          :key="rnd.id"
          class="card-hover rounded-xl border p-5 transition-colors duration-300"
          :class="{
            'bg-amber-50 border-amber-200': rnd.status === 'pending',
            'bg-white border-forest/10': rnd.status === 'verified',
            'bg-red-50 border-red-200': rnd.status === 'suspended'
          }"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-3">
              <div :class="['w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white', rnd.color]">
                {{ rnd.initials }}
              </div>
              <div>
                <p class="font-semibold text-forest-dark">{{ rnd.name }}</p>
                <p class="text-xs text-forest/50">{{ rnd.license }} · {{ rnd.specialty }}</p>
              </div>
            </div>
            <span :class="['text-xs font-semibold px-3 py-1 rounded-full uppercase transition-colors', statusBadge(rnd.status)]">{{ rnd.status }}</span>
          </div>

          <Transition name="dropdown" mode="out-in">
            <div v-if="rnd.status === 'pending'" key="pending" class="grid grid-cols-3 gap-4 text-sm mb-4">
              <div><p class="text-xs text-forest/40 uppercase">Submitted</p><p class="font-medium">{{ rnd.submitted }}</p></div>
              <div><p class="text-xs text-forest/40 uppercase">Specialization</p><p class="font-medium">{{ rnd.specialty }}</p></div>
              <div><p class="text-xs text-forest/40 uppercase">Consult Type</p><p class="font-medium">{{ rnd.consultType }}</p></div>
            </div>

            <div v-else-if="rnd.status === 'verified'" key="verified" class="grid grid-cols-4 gap-4 text-sm mb-4">
              <div><p class="text-xs text-forest/40 uppercase">Verified On</p><p class="font-medium">{{ rnd.verifiedOn }}</p></div>
              <div><p class="text-xs text-forest/40 uppercase">Patients</p><p class="font-medium">{{ rnd.patients }}</p></div>
              <div><p class="text-xs text-forest/40 uppercase">Rating</p><p class="font-medium">★ {{ rnd.rating ?? '—' }}</p></div>
              <div><p class="text-xs text-forest/40 uppercase">Revenue</p><p class="font-medium">{{ peso(rnd.revenue ?? 0) }}</p></div>
            </div>

            <div v-else key="suspended" class="bg-red-100 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">
              {{ rnd.suspendReason }}
            </div>
          </Transition>

          <div class="flex gap-3">
            <template v-if="rnd.status === 'pending'">
              <button class="btn-press flex-1 border border-forest/15 rounded-lg py-2 text-sm font-medium hover:bg-cream-soft">View Credentials</button>
              <button class="btn-press flex-1 bg-forest text-white rounded-lg py-2 text-sm font-medium hover:bg-forest-light hover:scale-[1.02]" @click="approve(rnd.id)">Approve</button>
              <button class="btn-press flex-1 border border-red-300 text-red-600 rounded-lg py-2 text-sm font-medium hover:bg-red-50 hover:scale-[1.02]" @click="reject(rnd.id)">Reject</button>
            </template>
            <template v-else-if="rnd.status === 'verified'">
              <button class="btn-press flex-1 border border-forest/15 rounded-lg py-2 text-sm font-medium hover:bg-cream-soft">View Profile</button>
              <button class="btn-press flex-1 border border-amber-300 text-amber-700 rounded-lg py-2 text-sm font-medium hover:bg-amber-50 hover:scale-[1.02]" @click="suspend(rnd.id)">Suspend</button>
            </template>
            <template v-else>
              <button class="btn-press flex-1 border border-forest/15 rounded-lg py-2 text-sm font-medium hover:bg-cream-soft">View Profile</button>
              <button class="btn-press flex-1 bg-forest text-white rounded-lg py-2 text-sm font-medium hover:bg-forest-light hover:scale-[1.02]" @click="reinstate(rnd.id)">Reinstate</button>
            </template>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>
