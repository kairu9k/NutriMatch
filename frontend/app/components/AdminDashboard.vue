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
import { CalendarCheck, Coins, ShieldCheck, Stethoscope, Users } from 'lucide-vue-next'
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
const activity = ref([])

const today = new Date().toLocaleDateString('en-PH', { weekday: 'long', month: 'long', day: 'numeric' }).toUpperCase()
const partOfDay = (() => {
  const h = new Date().getHours()
  return h < 12 ? 'morning' : h < 18 ? 'afternoon' : 'evening'
})()
const todoCount = computed(() => (stats.value.pending_verif || 0) + (stats.value.refunds_pending || 0) + (stats.value.payouts_due_count || 0))

onMounted(async () => {
  try {
    const [s, rnds, logs] = await Promise.all([get('/admin/platform-stats/'), get('/admin/rnds/'), get('/admin/audit-logs/', { query: { scope: 'admin', page_size: 6 } })])
    stats.value = s
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
