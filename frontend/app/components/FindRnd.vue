<template>
  <div class="find-rnd-page">
    <div class="page-header">
      <h1 class="page-title">Find Your RND</h1>
      <p class="page-sub">Browse PRC-verified Registered Nutritionist-Dietitians by specialty and language.</p>
    </div>

    <!-- FILTER BAR -->
    <div class="filter-bar">
      <div class="field">
        <label class="field-label">Specialization</label>
        <input v-model="specialty" type="text" class="field-input" placeholder="e.g. Diabetes, Renal Nutrition" @keyup.enter="loadRnds" />
      </div>
      <div class="field">
        <label class="field-label">Language</label>
        <select v-model="language" class="field-input">
          <option value="">Any Language</option>
          <option value="tl">Tagalog</option>
          <option value="ceb">Cebuano</option>
          <option value="ilo">Ilocano</option>
          <option value="en">English</option>
        </select>
      </div>
      <button class="search-btn" type="button" @click="loadRnds">
        <Search :size="16" /> Search
      </button>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="actionMessage" class="form-success">{{ actionMessage }}</p>

    <!-- LOADING -->
    <p v-if="isLoading" class="placeholder-text">Loading…</p>

    <!-- RESULTS -->
    <template v-else>
      <p class="results-count">{{ rnds.length }} verified RND{{ rnds.length === 1 ? '' : 's' }} found</p>

      <div v-if="rnds.length" class="rnd-grid">
        <div v-for="rnd in rnds" :key="rnd.id" class="rnd-card">
          <NuxtLink :to="`/rnd-profile-view/${rnd.user.id}`" class="rnd-card-top">
            <div class="rnd-avatar" :style="{ background: colorForId(rnd.user.id) }">{{ initialsFor(rnd.user) }}</div>
            <div>
              <p class="rnd-name">
                RND {{ rnd.user.first_name }} {{ rnd.user.last_name }}
                <BadgeCheck :size="14" class="verified-icon" />
              </p>
              <p class="rnd-specialty">{{ rnd.specialization || 'General Practice' }}</p>
            </div>
          </NuxtLink>

          <p class="rnd-bio">{{ rnd.bio || 'No bio provided yet.' }}</p>

          <div class="rnd-chips">
            <span v-for="lang in rnd.languages" :key="lang.id" class="lang-chip">{{ lang.language_name }}</span>
          </div>

          <div class="rnd-card-bottom">
            <span class="rnd-fee">₱{{ rnd.consultation_fee }}<span class="fee-unit">/session</span></span>
            <button
              class="request-btn"
              type="button"
              :disabled="requestedIds.has(rnd.user.id) || busyId === rnd.user.id"
              @click="requestRelationship(rnd)"
            >
              {{ requestButtonLabel(rnd) }}
            </button>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon"><SearchX :size="28" /></div>
        <p class="empty-title">No RNDs match your filters</p>
        <p class="empty-desc">Try a broader specialization or clear the language filter.</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Search, SearchX, BadgeCheck } from 'lucide-vue-next'

const { get, post } = useApi()

const specialty = ref('')
const language = ref('')
const isLoading = ref(true)
const errorMessage = ref('')
const actionMessage = ref('')
const busyId = ref(null)
const requestedIds = ref(new Set())

const rnds = ref([])

const AVATAR_COLORS = ['#1e4a26', '#3a6b3a', '#D4A017', '#6a8a6a', '#8a6a3a']

function colorForId(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}

function initialsFor(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
}

function requestButtonLabel(rnd) {
  if (busyId.value === rnd.user.id) return 'Sending…'
  if (requestedIds.value.has(rnd.user.id)) return 'Requested'
  return 'Request'
}

async function loadRnds() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const params = new URLSearchParams()
    if (specialty.value) params.set('specialty', specialty.value)
    if (language.value) params.set('language', language.value)
    const query = params.toString()
    rnds.value = await get(`/client/rnds/${query ? `?${query}` : ''}`)
  } catch {
    errorMessage.value = 'Could not load RNDs. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

async function requestRelationship(rnd) {
  busyId.value = rnd.user.id
  errorMessage.value = ''
  actionMessage.value = ''
  try {
    await post(`/client/rnds/${rnd.user.id}/request/`)
    requestedIds.value.add(rnd.user.id)
    actionMessage.value = `Request sent to RND ${rnd.user.first_name} ${rnd.user.last_name}.`
  } catch (error) {
    errorMessage.value = error?.data?.detail || 'Could not send request. Please try again.'
  } finally {
    busyId.value = null
  }
}

onMounted(loadRnds)
</script>

<style scoped>
* { box-sizing: border-box; }

.find-rnd-page { font-family: 'Inter', sans-serif; }

.page-header { margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.filter-bar {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 18px 20px; display: flex; gap: 16px; align-items: flex-end; margin-bottom: 20px; flex-wrap: wrap;
}
.field { display: flex; flex-direction: column; gap: 6px; flex: 1; min-width: 180px; }
.field-label { font-size: 0.78rem; font-weight: 600; color: #1a3a1a; }
.field-input {
  border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px;
  font-size: 0.88rem; color: #2a2a2a; font-family: inherit; background: #fff;
}
.field-input:focus { outline: none; border-color: #D4A017; }

.search-btn {
  background: #14301a; color: #fff; border: none; border-radius: 8px;
  padding: 10px 20px; font-weight: 600; font-size: 0.88rem; cursor: pointer;
  display: flex; align-items: center; gap: 8px; white-space: nowrap;
}

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.form-success {
  background: #e6efe0; border: 1px solid #b8d5b8; color: #3a6b3a;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}

.results-count { font-size: 0.85rem; color: #6a7a6a; margin: 0 0 14px; }

.rnd-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.rnd-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px;
  display: flex; flex-direction: column;
}
.rnd-card-top { display: flex; gap: 14px; margin-bottom: 12px; text-decoration: none; }
.rnd-avatar {
  width: 52px; height: 52px; border-radius: 50%; color: #fff; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.9rem;
}
.rnd-name { font-weight: 700; color: #1a3a1a; margin: 0 0 2px; display: flex; align-items: center; gap: 6px; font-size: 0.92rem; }
.verified-icon { color: #D4A017; }
.rnd-specialty { font-size: 0.78rem; color: #6a7a6a; margin: 0; }

.rnd-bio { font-size: 0.83rem; color: #4a5a4a; flex-grow: 1; margin: 0 0 12px; line-height: 1.5; }

.rnd-chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
.lang-chip {
  font-size: 0.7rem; background: #eef3ec; color: #1e4a26;
  padding: 3px 10px; border-radius: 20px; font-weight: 600;
}

.rnd-card-bottom { display: flex; align-items: center; justify-content: space-between; margin-top: auto; }
.rnd-fee { font-weight: 700; color: #1a3a1a; font-size: 0.95rem; }
.fee-unit { font-size: 0.72rem; font-weight: 400; color: #8a9a8a; }

.request-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 8px 16px; font-weight: 700; font-size: 0.82rem; cursor: pointer; white-space: nowrap;
}
.request-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
</style>
