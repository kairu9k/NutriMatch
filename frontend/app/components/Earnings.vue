<template>
  <div>
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Earnings</h1>
        <p class="page-subtitle">Track your revenue, commission, and payout history.</p>
      </div>
      <div class="period-select">
        <select v-model="period">
          <option>This Month</option>
          <option>Last Month</option>
          <option>Last 3 Months</option>
          <option>This Year</option>
        </select>
        <ChevronDown :size="15" class="select-caret" />
      </div>
    </div>

    <!-- STAT CARDS -->
    <section class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon"><Landmark :size="18" /></div>
        <p class="stat-value">₱{{ summary.gross.toLocaleString() }}</p>
        <p class="stat-label">Gross Revenue</p>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><Percent :size="18" /></div>
        <p class="stat-value">₱{{ summary.commission.toLocaleString() }}</p>
        <p class="stat-label">Platform Commission</p>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><Wallet :size="18" /></div>
        <p class="stat-value">₱{{ summary.net.toLocaleString() }}</p>
        <p class="stat-label">Net Earnings</p>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><Hourglass :size="18" /></div>
        <p class="stat-value">₱{{ summary.pending.toLocaleString() }}</p>
        <p class="stat-label">Pending Payment</p>
      </div>
    </section>

    <!-- EARNINGS TREND CHART -->
    <div class="panel chart-panel">
      <h3 class="panel-title">Earnings Trend (Last 6 Months)</h3>

      <div v-if="trend.length" class="chart-wrap">
        <div class="chart-y-axis">
          <span v-for="tick in yTicks" :key="tick">{{ tick.toLocaleString() }}</span>
        </div>
        <div class="chart-bars">
          <div v-for="point in trend" :key="point.month" class="chart-col">
            <div class="chart-bar" :style="{ height: barHeight(point.amount) + '%' }"></div>
            <span class="chart-label">{{ point.month }}</span>
          </div>
        </div>
      </div>
      <p v-else class="empty-note">No earnings data yet — your trend will appear here once you complete billable sessions.</p>
    </div>

    <!-- INVOICE TABLE -->
    <div class="panel table-panel" v-if="invoices.length">
      <table class="invoice-table">
        <thead>
          <tr>
            <th>INVOICE</th>
            <th>PATIENT</th>
            <th>DATE</th>
            <th>GROSS</th>
            <th>COMMISSION</th>
            <th>NET EARNED</th>
            <th>STATUS</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="inv in invoices" :key="inv.id">
            <td class="invoice-id">{{ inv.id }}</td>
            <td>{{ inv.patient }}</td>
            <td class="invoice-date">{{ inv.date }}</td>
            <td>₱{{ inv.gross.toFixed(2) }}</td>
            <td class="invoice-commission">₱{{ inv.commission.toFixed(2) }}</td>
            <td class="invoice-net">₱{{ inv.net.toFixed(2) }}</td>
            <td><span class="status-pill" :class="inv.status === 'Paid' ? 'status-paid' : 'status-pending'">{{ inv.status === 'Paid' ? 'Paid Out' : 'Pending' }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="!loading" class="empty-state">
      <Receipt :size="28" class="empty-icon" />
      <p class="empty-title">No invoices yet</p>
      <p class="empty-desc">Completed billable sessions will appear here.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { Landmark, Percent, Wallet, Hourglass, Receipt, ChevronDown } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Earnings' })

const { get } = useApi()

const rawInvoices = ref([])
const loading = ref(true)
const period = ref('This Month')

onMounted(async () => {
  try {
    rawInvoices.value = await get('/rnd/invoices/')
  } finally {
    loading.value = false
  }
})

function periodStart(label) {
  const now = new Date()
  if (label === 'This Month') return new Date(now.getFullYear(), now.getMonth(), 1)
  if (label === 'Last Month') return new Date(now.getFullYear(), now.getMonth() - 1, 1)
  if (label === 'Last 3 Months') return new Date(now.getFullYear(), now.getMonth() - 2, 1)
  if (label === 'This Year') return new Date(now.getFullYear(), 0, 1)
  return null
}
function periodEnd(label) {
  const now = new Date()
  if (label === 'Last Month') return new Date(now.getFullYear(), now.getMonth(), 1)
  return null
}

const periodInvoices = computed(() => {
  const start = periodStart(period.value)
  const end = periodEnd(period.value)
  return rawInvoices.value.filter(inv => {
    const created = new Date(inv.created_at)
    if (start && created < start) return false
    if (end && created >= end) return false
    return true
  })
})

const invoices = computed(() => periodInvoices.value.map(inv => ({
  id: `INV-${String(inv.id).padStart(4, '0')}`,
  patient: inv.client_name,
  date: new Date(inv.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
  gross: Number(inv.amount),
  commission: Number(inv.commission_amt),
  net: Number(inv.net),
  status: inv.status === 'paid' ? 'Paid' : 'Pending',
})))

const summary = computed(() => {
  const gross = periodInvoices.value.reduce((sum, i) => sum + Number(i.amount), 0)
  const commission = periodInvoices.value.reduce((sum, i) => sum + Number(i.commission_amt), 0)
  const net = periodInvoices.value.reduce((sum, i) => sum + Number(i.net), 0)
  const pending = periodInvoices.value
    .filter(i => i.status === 'unpaid')
    .reduce((sum, i) => sum + Number(i.amount), 0)
  return { gross, commission, net, pending }
})

const trend = computed(() => {
  const now = new Date()
  const months = []
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    months.push({ key: `${d.getFullYear()}-${d.getMonth()}`, month: d.toLocaleDateString('en-US', { month: 'short' }), amount: 0 })
  }
  for (const inv of rawInvoices.value) {
    if (inv.status !== 'paid') continue
    const d = new Date(inv.created_at)
    const key = `${d.getFullYear()}-${d.getMonth()}`
    const bucket = months.find(m => m.key === key)
    if (bucket) bucket.amount += Number(inv.net)
  }
  return months.some(m => m.amount > 0) ? months : []
})

const maxAmount = computed(() => Math.max(...trend.value.map(p => p.amount), 20000))
const yTicks = computed(() => {
  const step = Math.ceil(maxAmount.value / 5 / 2000) * 2000
  return [0, step, step * 2, step * 3, step * 4, step * 5].reverse()
})
function barHeight(amount) {
  const topTick = yTicks.value[0] || 20000
  return Math.min(100, Math.round((amount / topTick) * 100))
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #1a3a1a; margin: 0 0 4px; }
.page-subtitle { font-size: 0.88rem; color: #8a9a8a; margin: 0; }

.period-select { position: relative; }
.period-select select {
  appearance: none; border: 1px solid #dde3dd; background: #fff;
  padding: 9px 32px 9px 14px; border-radius: 8px; font-size: 0.85rem; color: #1a3a1a; cursor: pointer;
}
.select-caret { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #9aaa9a; pointer-events: none; }

.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 12px; padding: 18px 20px; border: 1px solid #eceeec; }
.stat-icon {
  width: 34px; height: 34px; border-radius: 8px; background: #f4f6f4;
  display: flex; align-items: center; justify-content: center; color: #4a5a4a; margin-bottom: 14px;
}
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stat-label { font-size: 0.8rem; color: #8a9a8a; margin: 4px 0 0; }
.stat-delta { font-size: 0.75rem; font-weight: 600; margin: 6px 0 0; }
.stat-delta.up { color: #2e9e52; }

.panel { background: #fff; border-radius: 12px; padding: 22px; border: 1px solid #eceeec; margin-bottom: 16px; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 20px; }

.chart-wrap { display: flex; gap: 12px; }
.chart-y-axis {
  display: flex; flex-direction: column; justify-content: space-between;
  font-size: 0.72rem; color: #9aaa9a; padding-bottom: 24px; text-align: right; min-width: 44px;
}
.chart-bars { flex: 1; display: flex; align-items: flex-end; gap: 20px; height: 260px; border-left: 1px solid #eceeec; padding-left: 16px; }
.chart-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.chart-bar { width: 60%; background: #163a1c; border-radius: 4px 4px 0 0; min-height: 2px; }
.chart-label { font-size: 0.78rem; color: #8a9a8a; margin-top: 8px; }

.invoice-table { width: 100%; border-collapse: collapse; }
.invoice-table th {
  text-align: left; font-size: 0.68rem; letter-spacing: 0.05em; color: #9aaa9a; padding-bottom: 14px;
}
.invoice-table td { padding: 14px 10px 14px 0; border-top: 1px solid #f2f4f2; font-size: 0.85rem; color: #3a4a3a; }
.invoice-id { font-weight: 700; color: #1a3a1a; }
.invoice-date { color: #3b6fd6; }
.invoice-commission { color: #9aaa9a; }
.invoice-net { font-weight: 700; color: #1a3a1a; }

.status-pill { font-size: 0.72rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; }
.status-paid { background: #e6f4e6; color: #2e7d32; }
.status-pending { background: #fdf1d6; color: #b8860b; }

.empty-note { font-size: 0.85rem; color: #9aaa9a; text-align: center; padding: 40px 0; }

.empty-state { text-align: center; padding: 56px 24px; background: #fff; border-radius: 12px; border: 1px solid #eceeec; }
.empty-icon { color: #c8d0c8; margin-bottom: 12px; }
.empty-title { font-size: 0.95rem; font-weight: 700; color: #4a5a4a; margin: 0 0 6px; }
.empty-desc { font-size: 0.82rem; color: #9aaa9a; margin: 0; }

@media (max-width: 900px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .invoice-table { display: block; overflow-x: auto; }
}
</style>