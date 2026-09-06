<script setup>
const { get, patch } = useApi()
const auth = useAuthStore()

const isLoading = ref(true)
const errorMessage = ref('')
const stats = ref({
  active_rnds: 0, clients: 0, pending_verif: 0, commissions: 0,
  new_registrations: 0, total_consultations: 0, gross_revenue: 0,
})
const pendingRnds = ref([])
const busyId = ref(null)

const AVATAR_COLORS = ['bg-emerald-800', 'bg-amber-400', 'bg-indigo-700', 'bg-red-600']
function colorFor(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}
function initialsFor(first, last) {
  return `${(first || '?')[0] ?? ''}${(last || '')[0] ?? ''}`.toUpperCase()
}

async function loadData() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const [platformStats, rnds] = await Promise.all([
      get('/admin/platform-stats/'),
      get('/admin/rnds/'),
    ])
    stats.value = platformStats
    pendingRnds.value = rnds.filter(r => !r.is_verified)
  } catch {
    errorMessage.value = 'Could not load dashboard data. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

async function approve(id) {
  busyId.value = id
  try {
    await patch(`/admin/users/${id}/verify-rnd/`)
    pendingRnds.value = pendingRnds.value.filter(r => r.id !== id)
    stats.value.pending_verif = Math.max(0, stats.value.pending_verif - 1)
    stats.value.active_rnds++
  } finally {
    busyId.value = null
  }
}

onMounted(loadData)

const peso = (n) => `₱${Number(n).toLocaleString()}`
</script>

<template>
  <div>
    <p v-if="errorMessage" class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-4">{{ errorMessage }}</p>

    <!-- Hero banner -->
    <div class="animate-in relative overflow-hidden rounded-2xl bg-gradient-to-br from-forest to-forest-dark text-white p-6 mb-6">
      <span class="hero-circle hero-circle-1"></span>
      <span class="hero-circle hero-circle-2"></span>
      <span class="hero-circle hero-circle-3"></span>

      <span class="relative z-10 inline-flex items-center gap-1.5 text-[11px] font-semibold text-gold border border-gold/40 rounded-full px-2.5 py-1">
        <span class="w-1.5 h-1.5 rounded-full bg-gold animate-pulse"></span>
        {{ new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).toUpperCase() }}
      </span>
      <h2 class="font-display text-3xl mt-3 relative z-10">{{ auth.user?.first_name }} {{ auth.user?.last_name }}</h2>
      <p class="text-cream/60 text-sm mb-6 relative z-10">NutriMatch Platform · Admin Control Center</p>

      <div class="grid grid-cols-4 gap-4 relative z-10">
        <div class="animate-in stagger-1 hero-stat bg-white/10 rounded-xl p-4">
          <p class="text-3xl font-display animate-pop">{{ stats.active_rnds }}</p>
          <p class="text-xs text-cream/60 mt-1">Active RNDs</p>
        </div>
        <div class="animate-in stagger-2 hero-stat bg-white/10 rounded-xl p-4">
          <p class="text-3xl font-display animate-pop">{{ stats.clients }}</p>
          <p class="text-xs text-cream/60 mt-1">Clients</p>
        </div>
        <div class="animate-in stagger-3 hero-stat bg-white/10 rounded-xl p-4">
          <p class="text-3xl font-display animate-pop">{{ stats.pending_verif }}</p>
          <p class="text-xs text-cream/60 mt-1">Pending Verif.</p>
        </div>
        <div class="animate-in stagger-4 hero-stat bg-white/10 rounded-xl p-4">
          <p class="text-3xl font-display animate-pop">{{ peso(stats.commissions) }}</p>
          <p class="text-xs text-cream/60 mt-1">Commissions (This Month)</p>
        </div>
      </div>
    </div>

    <!-- Secondary stat cards -->
    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="animate-in stagger-1 card-hover bg-cream-card border border-forest/15 rounded-xl p-5">
        <div class="w-8 h-8 rounded-lg bg-forest/5 flex items-center justify-center mb-3">
          <NavIcon name="users" class="w-4 h-4 text-forest" />
        </div>
        <p class="text-xs text-forest/50 mb-1">New Registrations</p>
        <p class="text-2xl font-display text-forest-dark">{{ stats.new_registrations }}</p>
        <p class="text-xs text-forest/40 mt-1">Last 30 days</p>
      </div>
      <div class="animate-in stagger-2 border border-forest/15 card-hover bg-cream-card rounded-xl p-5">
        <div class="w-8 h-8 rounded-lg bg-forest/5 flex items-center justify-center mb-3">
          <NavIcon name="trending" class="w-4 h-4 text-forest" />
        </div>
        <p class="text-xs text-forest/50 mb-1">Total Consultations</p>
        <p class="text-2xl font-display text-forest-dark">{{ stats.total_consultations }}</p>
        <p class="text-xs text-forest/40 mt-1">All-time completed</p>
      </div>
      <div class="animate-in stagger-3 border border-forest/15 card-hover bg-cream-card rounded-xl p-5">
        <div class="w-8 h-8 rounded-lg bg-forest/5 flex items-center justify-center mb-3">
          <NavIcon name="card" class="w-4 h-4 text-forest" />
        </div>
        <p class="text-xs text-forest/50 mb-1">Gross Revenue</p>
        <p class="text-2xl font-display text-forest-dark">{{ peso(stats.gross_revenue) }}</p>
        <p class="text-xs text-forest/40 mt-1">This month</p>
      </div>
    </div>

    <!-- Pending verifications -->
    <div class="animate-in stagger-2 border border-forest/15 bg-white rounded-2xl p-6">
      <div class="flex items-center justify-between mb-1">
        <h3 class="font-display text-normal text-forest-dark">Pending RND Verifications</h3>
        <NuxtLink to="/rnd-verification" class="text-sm text-forest hover:underline transition-colors">View all</NuxtLink>
      </div>
      <p class="text-xs text-forest/50 mb-4">Credential review required</p>

      <div v-if="isLoading" class="text-sm text-forest/50 py-8 text-center">Loading…</div>
      <div v-else-if="pendingRnds.length === 0" class="text-sm text-forest/50 py-8 text-center animate-in">
        No pending verifications right now.
      </div>
      <TransitionGroup v-else name="list" tag="div" class="relative">
        <div
          v-for="rnd in pendingRnds"
          :key="rnd.id"
          class="flex items-center justify-between gap-4 bg-cream-soft rounded-xl px-4 py-3 mb-2"
        >
          <div class="flex items-center gap-3 min-w-0">
            <div :class="['w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0', colorFor(rnd.id)]">
              {{ initialsFor(rnd.first_name, rnd.last_name) }}
            </div>
            <div class="min-w-0">
              <p class="text-sm font-semibold text-forest-dark truncate">{{ rnd.first_name }} {{ rnd.last_name }}</p>
              <p class="text-xs text-forest/50 truncate">PRC {{ rnd.prc_license_number }} · Submitted {{ new Date(rnd.submitted_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) }}</p>
            </div>
          </div>
          <div class="flex gap-2 shrink-0">
            <NuxtLink to="/rnd-verification" class="btn-press bg-forest text-white text-sm font-medium px-4 py-1.5 rounded-lg hover:bg-forest-light hover:scale-105">Review</NuxtLink>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.hero-stat {
  transition: background-color .2s ease, transform .2s ease, box-shadow .2s ease, border-color .2s ease;
  border: 1px solid transparent;
  cursor: pointer;
}
.hero-stat:hover {
  background-color: rgba(255, 255, 255, 0.16);
  border-color: rgba(212, 175, 55, 0.35);
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
}

.hero-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.06);
  pointer-events: none;
  z-index: 0;
}
.hero-circle-1 { width: 420px; height: 420px; top: -140px; right: -100px; }
.hero-circle-2 { width: 300px; height: 300px; bottom: -160px; right: 12%; background: rgba(212, 175, 55, 0.08); }
.hero-circle-3 { width: 220px; height: 220px; top: 40%; left: -80px; background: rgba(255, 255, 255, 0.04); }
</style>
