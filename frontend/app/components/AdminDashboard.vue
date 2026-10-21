<template>
  <div class="nm-page">
    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-banner">
      <span class="nm-banner-badge">{{ today }}</span>
      <h1 class="nm-banner-title">Good {{ partOfDay }}, {{ auth.user?.first_name }}</h1>
      <p class="nm-banner-sub">
        {{ todoCount ? `You have ${todoCount} thing${todoCount === 1 ? '' : 's'} to take care of.` : 'Everything is up to date — nothing needs your attention right now.' }}
      </p>
      <div class="nm-todo">
        <NuxtLink to="/rnd-verification" class="nm-todo-item" :class="{ done: !stats.pending_verif }">
          <strong>{{ stats.pending_verif }}</strong> RND application{{ stats.pending_verif === 1 ? '' : 's' }} to review
        </NuxtLink>
        <NuxtLink to="/billing-commission?tab=refunds" class="nm-todo-item" :class="{ done: !stats.refunds_pending }">
          <strong>{{ stats.refunds_pending }}</strong> refund{{ stats.refunds_pending === 1 ? '' : 's' }} to send
        </NuxtLink>
        <NuxtLink to="/payouts" class="nm-todo-item" :class="{ done: !stats.payouts_due_count }">
          <strong>{{ peso(stats.payouts_due_total) }}</strong> in payouts due {{ shortDate(stats.next_payout_date) }}
        </NuxtLink>
      </div>
    </div>

    <!-- TODAY -->
    <div v-if="dash" class="today" aria-label="Today">
      <NuxtLink v-for="t in todayTiles" :key="t.label" :to="t.link" class="tile" :class="t.tone">
        <strong>{{ t.value }}</strong><span>{{ t.label }}</span>
      </NuxtLink>
    </div>

    <div v-if="dash" class="nm-grid">
      <!-- NEEDS ATTENTION -->
      <div class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">Needs attention</h2>
            <p class="nm-panel-sub">Most urgent first</p>
          </div>
        </div>
        <div v-if="!dash.attention.length" class="nm-empty"><CheckCircle2 :size="28" /><p>Nothing needs you right now.</p></div>
        <NuxtLink v-for="a in dash.attention" :key="a.key" :to="a.link" class="attn" :class="a.level">
          <component :is="LEVEL_ICON[a.level]" :size="16" class="attn-icon" />
          <span class="attn-main">
            <strong>{{ a.title }}</strong>
            <small>{{ a.detail }}</small>
            <small v-if="a.people.length" class="attn-people">{{ a.people.slice(0, 4).map(p => p.name).join(', ') }}{{ a.people.length > 4 ? ` +${a.people.length - 4} more` : '' }}</small>
          </span>
          <ChevronRight :size="15" class="attn-go" />
        </NuxtLink>
      </div>

      <!-- MONTH VS LAST MONTH -->
      <div class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">This month vs last month</h2>
            <p class="nm-panel-sub">{{ dash.compare.label }} — same number of days</p>
          </div>
          <NuxtLink to="/platform-reports" class="nm-panel-link">Reports →</NuxtLink>
        </div>
        <div v-for="m in dash.compare.metrics" :key="m.key" class="cmp">
          <span class="cmp-label">{{ METRIC_LABEL[m.key] }}</span>
          <span class="cmp-now">{{ m.key === 'payments' || m.key === 'commission' ? peso(m.now) : m.now }}</span>
          <span class="cmp-delta" :class="m.change_pct == null ? 'flat' : m.change_pct >= 0 ? 'up' : 'down'">
            <template v-if="m.change_pct == null">new</template>
            <template v-else><component :is="m.change_pct >= 0 ? TrendingUp : TrendingDown" :size="13" /> {{ m.change_pct >= 0 ? '+' : '' }}{{ m.change_pct }}%</template>
          </span>
          <span class="cmp-before">was {{ m.key === 'payments' || m.key === 'commission' ? peso(m.before) : m.before }}</span>
        </div>
      </div>
    </div>

    <div class="nm-stat-grid">
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><Stethoscope :size="17" /></div>
        <p class="nm-stat-value">{{ stats.active_rnds }}</p>
        <p class="nm-stat-label">Active RNDs</p>
        <p class="nm-stat-note">Verified and signed up</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><Users :size="17" /></div>
        <p class="nm-stat-value">{{ stats.clients }}</p>
        <p class="nm-stat-label">Clients</p>
        <p class="nm-stat-note" :class="{ good: stats.new_registrations }">{{ stats.new_registrations }} new sign-ups in 30 days</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><CalendarCheck :size="17" /></div>
        <p class="nm-stat-value">{{ stats.total_consultations }}</p>
        <p class="nm-stat-label">Consultations completed</p>
        <p class="nm-stat-note">All time</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon gold"><Coins :size="17" /></div>
        <p class="nm-stat-value">{{ peso(stats.commissions) }}</p>
        <p class="nm-stat-label">Commission this month</p>
        <p class="nm-stat-note">From {{ peso(stats.gross_revenue) }} in payments</p>
      </div>
    </div>

    <div class="nm-grid">
      <div class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">RND applications</h2>
            <p class="nm-panel-sub">Check each PRC license before approving</p>
          </div>
          <NuxtLink to="/rnd-verification" class="nm-panel-link">View all →</NuxtLink>
        </div>
        <p v-if="loading" class="nm-muted">Loading…</p>
        <div v-else-if="!pendingRnds.length" class="nm-empty">
          <ShieldCheck :size="28" />
          <p>No applications waiting.</p>
        </div>
        <div v-for="r in pendingRnds.slice(0, 5)" :key="r.id" class="nm-row">
          <img v-if="r.profile_photo" :src="r.profile_photo" class="nm-avatar" alt="" />
          <span v-else class="nm-avatar">{{ userInitials(r.first_name, r.last_name) }}</span>
          <div class="nm-row-main">
            <p class="nm-row-title">{{ r.first_name }} {{ r.last_name }}</p>
            <p class="nm-row-sub">{{ r.specialization }}<template v-if="r.prc_license_number"> · PRC {{ r.prc_license_number }}</template> · {{ shortDate(r.submitted_at) }}</p>
          </div>
          <div class="nm-row-end">
            <span v-if="!r.email_verified_at" class="nm-pill muted">Email not verified</span>
            <NuxtLink :to="`/rnd-verification?open=${r.id}`" class="nm-btn-dark nm-btn-sm">Review</NuxtLink>
          </div>
        </div>
      </div>

      <div class="nm-panel">
        <div class="nm-panel-head">
          <div>
            <h2 class="nm-panel-title">Recent admin activity</h2>
            <p class="nm-panel-sub">Approvals, account changes, refunds, payouts and settings</p>
          </div>
          <NuxtLink to="/audit-logs?scope=admin" class="nm-panel-link">Audit logs →</NuxtLink>
        </div>
        <p v-if="loading" class="nm-muted">Loading…</p>
        <div v-else-if="!activity.length" class="nm-empty"><p>Nothing recorded yet.</p></div>
        <div v-for="a in activity" :key="a.id" class="nm-row">
          <div class="nm-row-main">
            <p class="nm-row-title">{{ auditLabel(a.action) }}</p>
            <p class="nm-row-sub">{{ a.user ? `${a.user.first_name} ${a.user.last_name}` : 'System' }} · {{ dateTime(a.created_at) }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { phHour } from '~/utils/phTime'
import { AlertOctagon, AlertTriangle, CalendarCheck, CheckCircle2, ChevronRight, Coins, Info, ShieldCheck, Stethoscope, TrendingDown, TrendingUp, Users } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

const { get } = useApi()
const auth = useAuthStore()

const loading = ref(true)
const error = ref('')
const stats = ref({
  active_rnds: 0, clients: 0, pending_verif: 0, commissions: 0, gross_revenue: 0, new_registrations: 0,
  total_consultations: 0, refunds_pending: 0, payouts_due_count: 0, payouts_due_total: 0, next_payout_date: null,
})
const pendingRnds = ref([])
// GET /api/admin/dashboard/ (core/admin_dashboard.py): today, attention, compare.
const dash = ref(null)
const LEVEL_ICON = { critical: AlertOctagon, warning: AlertTriangle, info: Info }
const METRIC_LABEL = { consultations: 'Consultations completed', payments: 'Payments received', commission: 'Commission', new_clients: 'New clients' }
const todayTiles = computed(() => {
  const t = dash.value?.today || {}
  return [
    { label: 'Consultations today', value: t.today ?? 0, link: '/admin-appointments' },
    { label: 'Next 7 days', value: t.next_7_days ?? 0, link: '/admin-appointments' },
    { label: 'Waiting for the RND', value: t.requests ?? 0, link: '/admin-appointments', tone: t.requests ? 'gold' : '' },
    { label: 'Unpaid, starting < 24 h', value: t.unpaid_soon ?? 0, link: '/admin-appointments', tone: t.unpaid_soon ? 'red' : '' },
    { label: 'Completed · 7 days', value: t.completed_7_days ?? 0, link: '/admin-appointments' },
    { label: 'Cancelled · 7 days', value: t.cancelled_7_days ?? 0, link: '/admin-appointments' },
  ]
})
const activity = ref([])

const today = new Date().toLocaleDateString('en-PH', { weekday: 'long', month: 'long', day: 'numeric' }).toUpperCase()
const partOfDay = (() => {
  const h = phHour()
  return h < 12 ? 'morning' : h < 18 ? 'afternoon' : 'evening'
})()
const todoCount = computed(() => (stats.value.pending_verif || 0) + (stats.value.refunds_pending || 0) + (stats.value.payouts_due_count || 0))

onMounted(async () => {
  try {
    const [s, rnds, logs, d] = await Promise.all([
      get('/admin/platform-stats/'), get('/admin/rnds/'), get('/admin/audit-logs/', { query: { scope: 'admin', page_size: 6 } }),
      get('/admin/dashboard/').catch(() => null),
    ])
    stats.value = s
    dash.value = d
    pendingRnds.value = rnds.filter(r => r.is_active && r.review_status === 'pending')
      .sort((a, b) => new Date(a.submitted_at) - new Date(b.submitted_at))
    activity.value = (Array.isArray(logs) ? logs : logs?.results || []).slice(0, 6)
  } catch {
    error.value = 'Could not load the dashboard. Please refresh the page.'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.today { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; margin: 0 0 16px; }
.tile { display: flex; flex-direction: column; gap: 2px; background: #fff; border: 1px solid #eceeec; border-radius: 12px; padding: 12px 14px; text-decoration: none; color: #1a3a1a; min-width: 0; }
.tile:hover { border-color: #b9d3be; }
.tile strong { font-family: 'Playfair Display', serif; font-size: 1.4rem; }
.tile span { font-size: 0.74rem; color: #6a7a6a; }
.tile.gold { background: #fffaf0; border-color: #f1dca3; }
.tile.red { background: #fff6f5; border-color: #f0c2bc; }
.tile.red strong { color: #a12525; }
.attn { display: flex; align-items: flex-start; gap: 10px; padding: 10px 12px; border-radius: 10px; text-decoration: none; color: #1a3a1a; border: 1px solid transparent; }
.attn + .attn { margin-top: 6px; }
.attn:hover { background: #f7f9f7; border-color: #eceeec; }
.attn-icon { flex-shrink: 0; margin-top: 2px; }
.attn.critical .attn-icon { color: #c0392b; }
.attn.warning .attn-icon { color: #b8860b; }
.attn.info .attn-icon { color: #2f6fa8; }
.attn-main { display: flex; flex-direction: column; gap: 2px; flex: 1; min-width: 0; }
.attn-main strong { font-size: 0.85rem; }
.attn-main small { font-size: 0.75rem; color: #6a7a6a; }
.attn-people { color: #4a5a4a !important; }
.attn-go { color: #9aaa9a; flex-shrink: 0; margin-top: 2px; }
.cmp { display: grid; grid-template-columns: minmax(0, 1fr) auto auto; grid-template-areas: "label now delta" "label before before"; gap: 0 12px; align-items: center; padding: 9px 0; border-bottom: 1px solid #f0f2f0; }
.cmp-label { grid-area: label; font-size: 0.84rem; color: #4a5a4a; }
.cmp-now { grid-area: now; font-weight: 700; font-size: 0.95rem; text-align: right; }
.cmp-delta { grid-area: delta; display: inline-flex; align-items: center; gap: 3px; font-size: 0.74rem; font-weight: 700; border-radius: 10px; padding: 2px 8px; justify-self: end; }
.cmp-delta.up { background: #e3f3ea; color: #1f8f5c; }
.cmp-delta.down { background: #fdecec; color: #a12525; }
.cmp-delta.flat { background: #eceeec; color: #6a7a6a; }
.cmp-before { grid-area: before; font-size: 0.72rem; color: #9aaa9a; text-align: right; }
@media (max-width: 1100px) { .today { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 560px) { .today { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
