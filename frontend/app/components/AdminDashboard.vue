<script setup>
import { rnds, platformStats } from '~/mock/mockAdminDatabase'

const stats = platformStats

const pending = computed(() => rnds.value.filter(r => r.status === 'pending'))
const carousel = ref(0)

const activity = ref([
  { id: 1, text: 'RND Ivy Reyes completed NCP for Maria Santos', time: 'Today · 10:45 AM', color: 'bg-emerald-700' },
  { id: 2, text: 'Payment of ₱500 received — Julia Niel Bulalaque', time: 'Today · 9:30 AM', color: 'bg-amber-400' },
  { id: 3, text: 'New RND verification submitted: Dr. Mika Lim', time: 'Today · 8:00 AM', color: 'bg-amber-400' },
  { id: 4, text: 'New client registered: Maine Mendoza', time: 'Yesterday · 3:00 PM', color: 'bg-blue-600' },
  { id: 5, text: 'Failed login attempt detected · IP 103.12.48.2', time: 'Yesterday · 11:22 PM', color: 'bg-red-600' }
])

function approve(id) {
  const rnd = rnds.value.find(r => r.id === id)
  if (!rnd) return
  rnd.status = 'verified'
  rnd.verifiedOn = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  rnd.patients = 0
  rnd.rating = null
  rnd.revenue = 0
  stats.value.activeRnds++
  stats.value.pendingVerif = Math.max(0, stats.value.pendingVerif - 1)
  activity.value.unshift({ id: Date.now(), text: `${rnd.name} was approved as a verified RND`, time: 'Just now', color: 'bg-emerald-700' })
}

function reject(id) {
  const rnd = rnds.value.find(r => r.id === id)
  if (!rnd) return
  rnds.value = rnds.value.filter(r => r.id !== id)
  stats.value.pendingVerif = Math.max(0, stats.value.pendingVerif - 1)
  activity.value.unshift({ id: Date.now(), text: `${rnd.name}'s application was rejected`, time: 'Just now', color: 'bg-red-600' })
}

const peso = (n) => `₱${Number(n).toLocaleString()}`
</script>

<template>
  <div>
    <!-- Hero banner -->
    <div class="animate-in relative overflow-hidden rounded-2xl bg-gradient-to-br from-forest to-forest-dark text-white p-6 mb-6">
      <span class="hero-circle hero-circle-1"></span>
      <span class="hero-circle hero-circle-2"></span>
      <span class="hero-circle hero-circle-3"></span>

      <span class="relative z-10 inline-flex items-center gap-1.5 text-[11px] font-semibold text-gold border border-gold/40 rounded-full px-2.5 py-1">
        <span class="w-1.5 h-1.5 rounded-full bg-gold animate-pulse"></span>
        {{ new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }).toUpperCase() }}
      </span>
      <h2 class="font-display text-3xl mt-3 relative z-10">System Administrator</h2>
      <p class="text-cream/60 text-sm mb-6 relative z-10">NutriMatch Platform · Admin Control Center</p>

      <div class="grid grid-cols-4 gap-4 relative z-10">
        <div class="animate-in stagger-1 hero-stat bg-white/10 rounded-xl p-4">
          <p class="text-3xl font-display animate-pop">{{ stats.activeRnds }}</p>
          <p class="text-xs text-cream/60 mt-1">Active RNDs</p>
        </div>
        <div class="animate-in stagger-2 hero-stat bg-white/10 rounded-xl p-4">
          <p class="text-3xl font-display animate-pop">{{ stats.clients }}</p>
          <p class="text-xs text-cream/60 mt-1">Clients</p>
        </div>
        <div class="animate-in stagger-3 hero-stat bg-white/10 rounded-xl p-4">
          <p class="text-3xl font-display animate-pop">{{ stats.pendingVerif }}</p>
          <p class="text-xs text-cream/60 mt-1">Pending Verif.</p>
        </div>
        <div class="animate-in stagger-4 hero-stat bg-white/10 rounded-xl p-4">
          <p class="text-3xl font-display animate-pop">{{ peso(stats.commissions) }}</p>
          <p class="text-xs text-cream/60 mt-1">Commissions</p>
        </div>
      </div>

      <div class="flex gap-1.5 mt-5 relative z-10">
        <button v-for="i in 3" :key="i" class="h-1.5 rounded-full transition-all duration-300" :class="carousel === i-1 ? 'w-6 bg-gold' : 'w-1.5 bg-white/30 hover:bg-white/50'" @click="carousel = i-1" />
      </div>
    </div>

    <!-- Secondary stat cards -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="animate-in stagger-1 card-hover bg-cream-card border border-forest/15 rounded-xl p-5">
        <div class="w-8 h-8 rounded-lg bg-forest/5 flex items-center justify-center mb-3">
          <NavIcon name="users" class="w-4 h-4 text-forest" />
        </div>
        <p class="text-xs  text-forest/50 mb-1">New Registrations</p>
        <p class="text-2xl font-display text-forest-dark">{{ stats.newRegistrations }}</p>
        <p class="text-xs text-emerald-700 mt-1">↑ This month</p>
      </div>
      <div class="animate-in stagger-2 border border-forest/15 card-hover bg-cream-card rounded-xl p-5">
        <div class="w-8 h-8 rounded-lg bg-forest/5 flex items-center justify-center mb-3">
          <NavIcon name="trending" class="w-4 h-4 text-forest" />
        </div>
        <p class="text-xs text-forest/50 mb-1">Total Consultations</p>
        <p class="text-2xl font-display text-forest-dark">{{ stats.totalConsultations }}</p>
        <p class="text-xs text-emerald-700 mt-1">↑ 28 from last month</p>
      </div>
      <div class="animate-in stagger-3 border border-forest/15 card-hover bg-cream-card rounded-xl p-5">
        <div class="w-8 h-8 rounded-lg bg-forest/5 flex items-center justify-center mb-3">
          <NavIcon name="card" class="w-4 h-4 text-forest" />
        </div>
        <p class="text-xs text-forest/50 mb-1">Gross Revenue</p>
        <p class="text-2xl font-display text-forest-dark">{{ peso(stats.grossRevenue) }}</p>
        <p class="text-xs text-forest/40 mt-1">Platform-wide · May</p>
      </div>
      <div class="animate-in stagger-4 border border-forest/15 card-hover bg-cream-card rounded-xl p-5">
        <div class="w-8 h-8 rounded-lg bg-forest/5 flex items-center justify-center mb-3">
          <NavIcon name="shield" class="w-4 h-4 text-forest" />
        </div>
        <p class="text-xs text-forest/50 mb-1">Platform Uptime</p>
        <p class="text-2xl font-display text-forest-dark">{{ stats.platformUptime }}%</p>
        <p class="text-xs text-forest/40 mt-1">Last 30 days</p>
      </div>
    </div>

    <div class="grid grid-cols-3 gap-6">
      <!-- Pending verifications -->
      <div class="animate-in stagger-2 border border-forest/15 col-span-2 bg-white rounded-2xl p-6">
        <div class="flex items-center justify-between mb-1">
          <h3 class="font-display text-normal text-forest-dark">Pending RND Verifications</h3>
          <NuxtLink to="/rnd-verification" class="text-sm text-forest hover:underline transition-colors">View all</NuxtLink>
        </div>
        <p class="text-xs text-forest/50 mb-4">Credential review required</p>

        <div v-if="pending.length === 0" class="text-sm text-forest/50 py-8 text-center animate-in">
          No pending verifications right now.
        </div>
        <TransitionGroup name="list" tag="div" class="relative">
          <div
            v-for="rnd in pending"
            :key="rnd.id"
            class="flex items-center justify-between gap-4 bg-cream-soft rounded-xl px-4 py-3 mb-2"
          >
            <div class="flex items-center gap-3 min-w-0">
              <div :class="['w-9 h-9 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0', rnd.color]">
                {{ rnd.initials }}
              </div>
              <div class="min-w-0">
                <p class="text-sm font-semibold text-forest-dark truncate">{{ rnd.name }}</p>
                <p class="text-xs text-forest/50 truncate">{{ rnd.license }} · Submitted: {{ rnd.submitted }}</p>
              </div>
            </div>
            <div class="flex gap-2 shrink-0">
              <button class="btn-press bg-forest text-white text-sm font-medium px-4 py-1.5 rounded-lg hover:bg-forest-light hover:scale-105" @click="approve(rnd.id)">Approve</button>
              <button class="btn-press border border-red-300 text-red-600 text-sm font-medium px-4 py-1.5 rounded-lg hover:bg-red-50 hover:scale-105" @click="reject(rnd.id)">Reject</button>
            </div>
          </div>
        </TransitionGroup>
      </div>

      <!-- Recent activity -->
      <div class="animate-in border border-forest/15 stagger-3 bg-white rounded-2xl p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-display text-normal text-forest-dark">Recent System Activity</h3>
          <button class="text-sm text-forest hover:underline transition-colors">Full log</button>
        </div>
        <TransitionGroup name="list" tag="div" class="relative">
          <div v-for="a in activity.slice(0,5)" :key="a.id" class="flex items-start gap-2.5 mb-4 last:mb-0">
            <span :class="['w-2 h-2 rounded-full mt-1.5 shrink-0', a.color]" />
            <div>
              <p class="text-sm text-forest-dark">{{ a.text }}</p>
              <p class="text-xs text-forest/40">{{ a.time }}</p>
            </div>
          </div>
        </TransitionGroup>
      </div>
    </div>

    <div class="animate-slide-down bg-amber-50 border border-amber-200 rounded-xl p-4 mt-6 flex items-start gap-3">
      <span class="text-amber-500 text-lg leading-none">⚠</span>
      <div>
        <p class="text-sm font-semibold text-amber-800">Platform alert</p>
        <p class="text-sm text-amber-700">{{ stats.pendingVerif }} RND verification requests have been pending for more than 48 hours. Review to maintain onboarding SLA.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Hover for the 4 stat pills inside the dark green hero card.
   The generic .card-hover box-shadow is dark-on-dark here and invisible,
   so this gives a hover that's actually visible against the forest background. */
.hero-stat {
  transition: background-color .2s ease, transform .2s ease, box-shadow .2s ease, border-color .2s ease;
  border: 1px solid transparent;
  cursor: pointer;
}
.hero-stat:hover {
  background-color: rgba(255, 255, 255, 0.16);
  border-color: rgba(212, 175, 55, 0.35); /* gold-tinted border */
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
}

/* Decorative background circles for the hero card */
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