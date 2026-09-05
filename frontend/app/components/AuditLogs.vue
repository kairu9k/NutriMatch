<script setup>
import { auditLogs } from '~/mock/mockAdminDatabase'

const logs = auditLogs
const search = ref('')
const eventType = ref('All Event Types')
const dateFilter = ref('')

const eventTypes = computed(() => ['All Event Types', ...new Set(logs.value.map(l => l.tag))])

const filtered = computed(() =>
  logs.value.filter(l => {
    const matchesSearch = !search.value || l.detail.toLowerCase().includes(search.value.toLowerCase()) || l.ip.includes(search.value)
    const matchesType = eventType.value === 'All Event Types' || l.tag === eventType.value
    return matchesSearch && matchesType
  })
)

const tagColor = (tag) => ({
  Clinical: 'bg-emerald-100 text-emerald-700',
  Payment: 'bg-amber-100 text-amber-700',
  Verification: 'bg-amber-100 text-amber-700',
  Security: 'bg-red-100 text-red-700',
  Auth: 'bg-blue-100 text-blue-700',
  'Data Access': 'bg-purple-100 text-purple-700'
}[tag] || 'bg-forest/10 text-forest')
</script>

<template>
  <div class="grid grid-cols-4 gap-6">
    <div class="col-span-3">
      <div class="flex justify-end mb-4">
        <button class="btn-press bg-forest text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-forest-light hover:scale-105"> Export Log</button>
      </div>
      <div class="grid grid-cols-4 gap-3 mb-5">
        <div class="relative col-span-2">
          <NavIcon name="search" class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-forest/40" />
          <input v-model="search" type="text" placeholder="Search by IP or user..."
            class="w-full border border-forest/25 rounded-lg pl-9 pr-3 py-2.5 text-sm bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />
        </div>
        <input v-model="dateFilter" type="date" class="border border-forest/15 rounded-lg px-3 py-2.5 text-sm bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />
        <select v-model="eventType" class="border border-forest/15 rounded-lg px-3 py-2.5 text-sm bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20">
          <option v-for="t in eventTypes" :key="t">{{ t }}</option>
        </select>
      </div>

      <div class="animate-in bg-white rounded-2xl p-2">
        <TransitionGroup name="list" tag="div" class="relative">
          <div
            v-for="log in filtered"
            :key="log.id"
            class="flex items-center justify-between gap-4 border-l-4 rounded-lg px-4 py-3 mb-1 transition-colors duration-200"
            :class="[log.color, log.highlight ? 'bg-red-50' : 'hover:bg-cream-soft']"
          >
            <div>
              <p class="text-sm font-semibold text-forest-dark">{{ log.title }}</p>
              <p class="text-xs text-forest/50">{{ log.detail }}</p>
              <p class="text-xs text-forest/35">{{ log.date }} · IP: {{ log.ip }}</p>
            </div>
            <span :class="['text-xs font-semibold px-2.5 py-1 rounded-full shrink-0', tagColor(log.tag)]">{{ log.tag }}</span>
          </div>
        </TransitionGroup>
        <div v-if="filtered.length === 0" class="text-center text-sm text-forest/40 py-10 animate-in">No matching audit events.</div>
      </div>

      <div class="flex items-center justify-between mt-4">
        <button class="btn-press border border-forest/15 rounded-lg px-4 py-2 text-sm hover:bg-cream-soft">‹ Previous</button>
        <span class="text-sm text-forest/50">Page 1 of 18</span>
        <button class="btn-press border border-forest/15 rounded-lg px-4 py-2 text-sm hover:bg-cream-soft">Next ›</button>
      </div>
    </div>

    <div class="space-y-4">
      <div class="animate-in bg-white border border-forest/15 rounded-2xl p-5">
        <h3 class="font-display text-lg text-forest-dark mb-3">Activity Snapshot</h3>
        <div class="flex justify-between text-sm py-2 border-b border-forest/5">
          <span class="text-forest/50">Events today</span><span class="font-semibold animate-pop">12</span>
        </div>
        <div class="flex justify-between text-sm py-2 border-b border-forest/5">
          <span class="text-forest/50">Events this week</span><span class="font-semibold animate-pop">84</span>
        </div>
        <div class="flex justify-between text-sm py-2">
          <span class="text-red-600">Security alerts</span><span class="font-semibold text-red-600 animate-pulse">1</span>
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
