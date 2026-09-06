<script setup>
const { get, patch } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const invoices = ref([])

const commissionRate = ref('')
const settingsLoaded = ref(false)
const saveMsg = ref('')
const isSaving = ref(false)

async function loadInvoices() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    invoices.value = await get('/admin/invoices/')
  } catch {
    errorMessage.value = 'Could not load billing data. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

async function loadSettings() {
  try {
    const settings = await get('/admin/settings/')
    const setting = settings.find(s => s.key === 'platform_commission_pct')
    commissionRate.value = setting ? setting.value : '10.00'
  } catch {
    commissionRate.value = '10.00'
  } finally {
    settingsLoaded.value = true
  }
}

onMounted(() => {
  loadInvoices()
  loadSettings()
})

async function saveSettings() {
  isSaving.value = true
  saveMsg.value = ''
  try {
    await patch(`/admin/settings/platform_commission_pct/`, { value: commissionRate.value })
    saveMsg.value = `Saved — new invoices will use ${commissionRate.value}% commission. Already-created invoices are unaffected (commission freezes at creation).`
  } catch {
    saveMsg.value = 'Could not save. Please try again.'
  } finally {
    isSaving.value = false
    setTimeout(() => (saveMsg.value = ''), 4000)
  }
}

const grossRevenue = computed(() => invoices.value.filter(i => i.status === 'paid').reduce((sum, i) => sum + Number(i.amount), 0))
const totalCommission = computed(() => invoices.value.filter(i => i.status === 'paid').reduce((sum, i) => sum + Number(i.commission_amt), 0))
const totalNet = computed(() => invoices.value.filter(i => i.status === 'paid').reduce((sum, i) => sum + Number(i.net), 0))

const payouts = computed(() => {
  const byRnd = {}
  for (const inv of invoices.value) {
    if (inv.status !== 'paid') continue
    if (!byRnd[inv.rnd_name]) byRnd[inv.rnd_name] = { rnd: inv.rnd_name, gross: 0, commission: 0, net: 0 }
    byRnd[inv.rnd_name].gross += Number(inv.amount)
    byRnd[inv.rnd_name].commission += Number(inv.commission_amt)
    byRnd[inv.rnd_name].net += Number(inv.net)
  }
  return Object.values(byRnd).sort((a, b) => b.net - a.net)
})

const statusColor = (status) => ({
  paid: 'bg-emerald-100 text-emerald-700',
  unpaid: 'bg-amber-100 text-amber-700',
  refunded: 'bg-red-100 text-red-700',
  cancelled: 'bg-forest/10 text-forest/50',
}[status] || 'bg-forest/10 text-forest/50')

const statusLabel = (status) => ({ paid: 'Paid', unpaid: 'Pending', refunded: 'Refunded', cancelled: 'Cancelled' }[status] || status)

const peso = (n) => `₱${Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
</script>

<template>
  <div>
    <p v-if="errorMessage" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">{{ errorMessage }}</p>

    <div class="animate-in bg-gradient-to-br from-forest to-forest-dark text-white rounded-2xl p-8 mb-6">
      <p class="text-xs tracking-widest text-gold">PLATFORM REVENUE — ALL TIME (PAID INVOICES)</p>
      <p class="font-display text-4xl mt-1 animate-pop">{{ peso(grossRevenue) }}</p>
      <p class="text-sm text-cream/60 mb-5">Gross · {{ invoices.filter(i => i.status === 'paid').length }} consultations paid</p>
      <div class="grid grid-cols-2 gap-4">
        <div class="animate-in stagger-1 card-hover bg-white/10 rounded-xl p-4">
          <p class="text-2xl font-display">{{ peso(totalCommission) }}</p>
          <p class="text-xs text-cream/60">Total Commission</p>
        </div>
        <div class="animate-in stagger-2 card-hover bg-white/10 rounded-xl p-4">
          <p class="text-2xl font-display">{{ peso(totalNet) }}</p>
          <p class="text-xs text-cream/60">RND Payouts (net)</p>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-6">
      <div class="animate-in stagger-1 border border-forest/15 col-span-2 bg-white rounded-2xl p-6">
        <h3 class="font-display text-lg text-forest-dark mb-4">Invoice Log</h3>
        <div v-if="isLoading" class="text-sm text-forest/50 py-8 text-center">Loading…</div>
        <div v-else-if="!invoices.length" class="text-sm text-forest/50 py-8 text-center">No invoices yet.</div>
        <TransitionGroup v-else name="list" tag="div" class="relative">
          <div v-for="inv in invoices" :key="inv.id" class="flex items-center justify-between py-3 border-b border-forest/5 last:border-0 hover:bg-cream-soft/40 transition-colors rounded-lg px-2">
            <div>
              <p class="text-sm font-semibold text-forest-dark">{{ inv.client_name }} → {{ inv.rnd_name }}</p>
              <p class="text-xs text-forest/40">{{ new Date(inv.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) }}{{ inv.payment_method ? ' · ' + inv.payment_method : '' }}</p>
            </div>
            <div class="text-right">
              <p class="text-sm font-semibold">{{ peso(inv.amount) }}</p>
              <span :class="['text-xs font-semibold px-2 py-0.5 rounded-full transition-colors', statusColor(inv.status)]">{{ statusLabel(inv.status) }}</span>
            </div>
          </div>
        </TransitionGroup>
      </div>

      <div class="animate-in stagger-2 space-y-4">
        <div class="bg-white rounded-2xl border border-forest/15 p-6">
          <h3 class="font-display text-lg text-forest-dark mb-4">Commission Settings</h3>
          <label class="text-xs text-forest/50">Platform commission rate (%)</label>
          <input v-model="commissionRate" type="number" step="0.01" :disabled="!settingsLoaded" class="w-full border border-forest/15 rounded-lg px-3 py-2 text-sm mb-3 mt-1 bg-white transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />
          <button class="btn-press w-full bg-gold text-forest-dark font-semibold rounded-lg py-2.5 text-sm hover:brightness-95 hover:scale-[1.01] disabled:opacity-60" :disabled="isSaving || !settingsLoaded" @click="saveSettings">
            {{ isSaving ? 'Saving…' : 'Save settings' }}
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
      <div v-if="!payouts.length" class="text-sm text-forest/50 py-4 text-center">No paid invoices yet.</div>
      <table v-else class="w-full text-sm">
        <thead>
          <tr class="text-xs text-forest/40 uppercase text-left border-b border-forest/10">
            <th class="pb-2">RND</th><th>Gross</th><th>Commission</th><th>Net Payout</th>
          </tr>
        </thead>
        <TransitionGroup name="list" tag="tbody">
          <tr v-for="p in payouts" :key="p.rnd" class="border-b border-forest/5 last:border-0 hover:bg-cream-soft/40 transition-colors">
            <td class="py-3 font-medium">{{ p.rnd }}</td>
            <td>{{ peso(p.gross) }}</td>
            <td>{{ peso(p.commission) }}</td>
            <td class="font-semibold text-forest-dark">{{ peso(p.net) }}</td>
          </tr>
        </TransitionGroup>
      </table>
    </div>
  </div>
</template>
