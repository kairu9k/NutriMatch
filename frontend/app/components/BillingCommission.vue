<script setup>
import { transactions, platformStats } from '~/mock/mockAdminDatabase'

const stats = platformStats

const commissionRate = ref(10)
const paymentGateway = ref('GCash / Maya')
const saveMsg = ref('')

function saveSettings() {
  saveMsg.value = `Saved — commission rate set to ${commissionRate.value}%.`
  setTimeout(() => (saveMsg.value = ''), 2500)
}

const payouts = ref([
  { rnd: 'RND Reyes', gross: 15800, commission: 1580, net: 14220, status: 'Released' },
  { rnd: 'RND Alba', gross: 9400, commission: 940, net: 8460, status: 'Pending' }
])

function releaseAll() {
  payouts.value = payouts.value.map(p => ({ ...p, status: 'Released' }))
}

const statusColor = (status) => ({
  Settled: 'bg-emerald-100 text-emerald-700',
  Pending: 'bg-amber-100 text-amber-700',
  Disputed: 'bg-red-100 text-red-700',
  Released: 'bg-emerald-100 text-emerald-700'
}[status])

const peso = (n) => `₱${Number(n).toLocaleString()}`
</script>

<template>
  <div>
    <div class="animate-in bg-gradient-to-br from-forest to-forest-dark text-white rounded-2xl p-8 mb-6">
      <p class="text-xs tracking-widest text-gold">PLATFORM REVENUE — MAY 2026</p>
      <p class="font-display text-4xl mt-1 animate-pop">{{ peso(stats.grossRevenue) }}</p>
      <p class="text-sm text-cream/60 mb-5">Gross · {{ stats.totalConsultations }} consultations completed</p>
      <div class="grid grid-cols-3 gap-4">
        <div class="animate-in stagger-1 card-hover bg-white/10 rounded-xl p-4">
          <p class="text-2xl font-display">{{ peso(stats.commissions) }}</p>
          <p class="text-xs text-cream/60">Commission (10%)</p>
        </div>
        <div class="animate-in stagger-2 card-hover bg-white/10 rounded-xl p-4">
          <p class="text-2xl font-display">{{ peso(stats.grossRevenue - stats.commissions) }}</p>
          <p class="text-xs text-cream/60">RND payouts</p>
        </div>
        <div class="animate-in stagger-3 card-hover bg-white/10 rounded-xl p-4">
          <p class="text-2xl font-display">{{ stats.activeRnds }}</p>
          <p class="text-xs text-cream/60">Active RNDs</p>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-6">
      <div class="animate-in stagger-1 border border-forest/15 col-span-2 bg-white rounded-2xl p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-display text-lg text-forest-dark">Transaction Log</h3>
          <button class="text-sm text-forest hover:underline transition-colors"> Export CSV</button>
        </div>
        <TransitionGroup name="list" tag="div" class="relative">
          <div v-for="t in transactions" :key="t.id" class="flex items-center justify-between py-3 border-b border-forest/5 last:border-0 hover:bg-cream-soft/40 transition-colors rounded-lg px-2">
            <div>
              <p class="text-sm font-semibold text-forest-dark">{{ t.from }} → {{ t.to }}</p>
              <p class="text-xs text-forest/40">{{ t.date }} · {{ t.mode }}</p>
            </div>
            <div class="text-right">
              <p class="text-sm font-semibold">{{ peso(t.amount) }}</p>
              <span :class="['text-xs font-semibold px-2 py-0.5 rounded-full transition-colors', statusColor(t.status)]">{{ t.status }}</span>
            </div>
          </div>
        </TransitionGroup>
      </div>

      <div class="animate-in stagger-2 space-y-4">
        <div class="bg-white rounded-2xl border border-forest/15 p-6">
          <h3 class="font-display text-lg text-forest-dark mb-4">Commission Settings</h3>
          <label class="text-xs text-forest/50">Platform commission rate (%)</label>
          <input v-model="commissionRate" type="number" class="w-full border border-forest/15 rounded-lg px-3 py-2 text-sm mb-3 mt-1 bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />
          <label class="text-xs text-forest/50">Payment gateway</label>
          <input v-model="paymentGateway" type="text" class="w-full border border-forest/15 rounded-lg px-3 py-2 text-sm mb-3 mt-1 bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />
          <button class="btn-press w-full bg-gold text-forest-dark font-semibold rounded-lg py-2.5 text-sm hover:brightness-95 hover:scale-[1.01]" @click="saveSettings">
            Save settings
          </button>
          <Transition name="dropdown">
            <p v-if="saveMsg" class="text-xs text-emerald-700 mt-2">{{ saveMsg }}</p>
          </Transition>
        </div>
        <div class="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
          <p class="text-sm font-semibold text-indigo-800">Commission is frozen at invoice creation</p>
          <p class="text-sm text-indigo-700">Rate changes only apply to new invoices, protecting RND payouts from retroactive adjustment.</p>
        </div>
      </div>
    </div>

    <div class="animate-in stagger-3 border border-forest/15 bg-white rounded-2xl p-6 mt-6">
      <h3 class="font-display text-lg text-forest-dark mb-4">RND Payout Summary</h3>
      <table class="w-full text-sm">
        <thead>
          <tr class="text-xs text-forest/40 uppercase text-left border-b border-forest/10">
            <th class="pb-2">RND</th><th>Gross</th><th>Commission</th><th>Net Payout</th><th>Status</th>
          </tr>
        </thead>
        <TransitionGroup name="list" tag="tbody">
          <tr v-for="p in payouts" :key="p.rnd" class="border-b border-forest/5 last:border-0 hover:bg-cream-soft/40 transition-colors">
            <td class="py-3 font-medium">{{ p.rnd }}</td>
            <td>{{ peso(p.gross) }}</td>
            <td>{{ peso(p.commission) }}</td>
            <td class="font-semibold text-forest-dark">{{ peso(p.net) }}</td>
            <td><span :class="['text-xs font-semibold px-2 py-0.5 rounded-full transition-colors', statusColor(p.status)]">{{ p.status }}</span></td>
          </tr>
        </TransitionGroup>
      </table>
      <button class="btn-press w-full bg-forest text-white rounded-lg py-2.5 text-sm font-medium mt-4 hover:bg-forest-light hover:scale-[1.01]" @click="releaseAll">
        Release all pending payouts
      </button>
    </div>
  </div>
</template>
