<script setup>
import { clients } from '~/mock/mockAdminDatabase'

const search = ref('')
const selectedClient = ref('')

const activeCount = computed(() => clients.value.filter(c => c.status === 'Active').length)
const inactiveCount = computed(() => clients.value.filter(c => c.status === 'Inactive').length)
const flaggedCount = computed(() => clients.value.filter(c => c.status === 'Flagged').length)

const filtered = computed(() =>
  clients.value.filter(c =>
    !search.value ||
    c.name.toLowerCase().includes(search.value.toLowerCase()) ||
    c.email.toLowerCase().includes(search.value.toLowerCase())
  )
)

const statusBadge = (status) => ({
  Active: 'bg-emerald-100 text-emerald-700',
  Inactive: 'bg-amber-100 text-amber-700',
  Flagged: 'bg-red-100 text-red-700'
}[status])

const actionMsg = ref('')
function deactivate() {
  if (!selectedClient.value) { actionMsg.value = 'Select a client first.'; return }
  const c = clients.value.find(c => String(c.id) === selectedClient.value)
  if (c) c.status = 'Inactive'
  actionMsg.value = `${c?.name || ''} has been deactivated.`
}
function unlockFlagged() {
  if (!selectedClient.value) { actionMsg.value = 'Select a client first.'; return }
  const c = clients.value.find(c => String(c.id) === selectedClient.value)
  if (c) { c.status = 'Active'; c.flagNote = null }
  actionMsg.value = `${c?.name || ''}'s account has been unlocked.`
}
</script>

<template>
  <div class="grid grid-cols-3 gap-6">
    <div class="col-span-2">
      <div class="flex items-center justify-between mb-10">
        <div>
          <p class="text-sm text-forest/50">{{ clients.length }} registered clients</p>
        </div>
        <select class="border border-forest/15 rounded-lg px-3 py-2 text-sm bg-white">
          <option>All Status</option>
        </select>
      </div>

      <div class="flex gap-3 mb-6">
        <div class="relative flex-1">
          <NavIcon name="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-forest/40" />
          <input v-model="search" type="text" placeholder="Search client by name or email..."
            class="w-full border border-forest/25 rounded-lg pl-9 pr-3 py-2.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-forest/20" />
        </div>
        <select class="border border-forest/15 rounded-lg px-3 text-sm bg-white">
          <option>All Conditions</option>
        </select>
      </div>

      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="animate-in stagger-1 border border-forest/15 card-hover bg-emerald-50 rounded-xl p-4 text-center">
          <p class="text-2xl font-display text-emerald-700 animate-pop">{{ activeCount }}</p>
          <p class="text-xs text-forest/50">Active</p>
        </div>
        <div class="animate-in stagger-2 border border-forest/15 card-hover bg-amber-50 rounded-xl p-4 text-center">
          <p class="text-2xl font-display text-amber-600 animate-pop">{{ inactiveCount }}</p>
          <p class="text-xs text-forest/50">Inactive</p>
        </div>
        <div class="animate-in stagger-3 border border-forest/15 card-hover bg-red-50 rounded-xl p-4 text-center">
          <p class="text-2xl font-display text-red-600 animate-pop">{{ flaggedCount }}</p>
          <p class="text-xs text-forest/50">Flagged</p>
        </div>
      </div>

      <TransitionGroup name="list" tag="div" class="relative space-y-3">
        <div
          v-for="c in filtered"
          :key="c.id"
          class="card-hover rounded-xl border p-4 transition-colors duration-300"
          :class="c.status === 'Flagged' ? 'bg-red-50 border-red-200' : 'bg-white border-forest/10'"
        >
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-3">
              <div :class="['w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white', c.color]">
                {{ c.initials }}
              </div>
              <div>
                <p class="font-semibold text-forest-dark text-sm">{{ c.name }}</p>
                <p class="text-xs text-forest/50">{{ c.email }} · {{ c.condition }}</p>
              </div>
            </div>
            <div class="text-right">
              <span :class="['text-xs font-semibold px-3 py-1 rounded-full transition-colors', statusBadge(c.status)]">{{ c.status }}</span>
              <p class="text-xs text-forest/40 mt-1">Matched: {{ c.matched }}</p>
            </div>
          </div>
          <div v-if="c.status !== 'Flagged'" class="grid grid-cols-3 text-xs text-forest/50 mt-2">
            <div><span class="uppercase text-forest/40">Joined</span><br /><span class="font-medium text-forest-dark">{{ c.joined }}</span></div>
            <div><span class="uppercase text-forest/40">Consultations</span><br /><span class="font-medium text-forest-dark">{{ c.consultations }}</span></div>
            <div><span class="uppercase text-forest/40">Last Active</span><br /><span class="font-medium text-forest-dark">{{ c.lastActive }}</span></div>
          </div>
          <div v-else class="bg-red-100 text-red-700 text-sm rounded-lg px-3 py-2 mt-2 animate-slide-down">
            {{ c.flagNote }}
          </div>
        </div>
      </TransitionGroup>
    </div>

    <div>
      <div class="animate-in bg-white rounded-2xl p-5 mb-4">
        <h3 class="font-display text-normal text-forest-dark mb-3">Account Actions</h3>
        <select v-model="selectedClient" class="w-full border border-forest/25 rounded-lg px-3 py-2.5 text-sm mb-3 bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20">
          <option value="">Select client...</option>
          <option v-for="c in clients" :key="c.id" :value="String(c.id)">{{ c.name }}</option>
        </select>
        <button class="btn-press w-full border border-red-300 text-red-600 rounded-lg py-2.5 text-sm font-medium mb-2 hover:bg-red-50 hover:scale-[1.01]" @click="deactivate">
          Deactivate account
        </button>
        <button class="btn-press w-full border border-forest/15 rounded-lg py-2.5 text-sm font-medium hover:bg-cream-soft hover:scale-[1.01]" @click="unlockFlagged">
          Unlock flagged account
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
