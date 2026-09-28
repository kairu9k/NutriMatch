<template>
  <div class="find-rnd-page">
    <!-- FILTER BAR -->
    <div class="filter-bar">
      <div class="filter-row">
        <div class="field">
          <label>Specialization</label>
          <select v-model="specialization">
            <option value="">All Specializations</option>
            <option v-for="s in specializations" :key="s.keyword" :value="s.keyword">{{ s.label }}</option>
          </select>
        </div>
        <div class="field">
          <label>Language</label>
          <select v-model="language">
            <option value="">Any Language</option>
            <option v-for="l in languageOptions" :key="l.code" :value="l.code">{{ l.label }}</option>
          </select>
        </div>
        <div class="field">
          <label>Consultation Mode</label>
          <select v-model="mode">
            <option value="">Any Mode</option>
            <option v-for="m in modeOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>
        <button class="search-btn" type="button" @click="loadRnds"><Search :size="15" /> Search</button>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="isLoading" class="placeholder-text">Loading…</p>

    <template v-else>
      <div class="results-row">
        <p class="results-count">Showing {{ pagedRnds.length }} of {{ rnds.length }} verified RND{{ rnds.length === 1 ? '' : 's' }}</p>
        <select v-model="sortBy" class="sort-select">
          <option value="rating">Sort: Highest Rated</option>
          <option value="reviews">Sort: Most Reviews</option>
          <option value="fee_low">Sort: Lowest Fee</option>
        </select>
      </div>

      <div v-if="pagedRnds.length" class="rnd-grid">
        <div v-for="rnd in pagedRnds" :key="rnd.id" class="rnd-card">
          <div class="rnd-card-top">
            <div class="rnd-avatar" :style="avatarStyle(rnd.user.id)">{{ initialsFor(rnd.user) }}</div>
            <div>
              <p class="rnd-name">RND {{ rnd.user.first_name }} {{ rnd.user.last_name }} <BadgeCheck :size="13" class="verified-icon" /></p>
              <p class="rnd-specialty">{{ rnd.specialization || 'General Practice' }}</p>
              <p v-if="rnd.review_count" class="rnd-rating">★ {{ Number(rnd.average_rating).toFixed(1) }} <span class="rnd-review-count">({{ rnd.review_count }} review{{ rnd.review_count === 1 ? '' : 's' }})</span></p>
              <p v-else class="rnd-rating no-reviews">No reviews yet</p>
            </div>
          </div>

          <p class="rnd-desc">{{ rnd.bio || 'No bio provided yet.' }}</p>

          <div class="rnd-tags">
            <span v-for="lang in rnd.languages" :key="lang.id" class="lang-chip">{{ lang.language_name }}</span>
            <span v-for="m in rnd.consultation_modes" :key="m" class="mode-pill"><component :is="modeMeta(m).icon" :size="12" /> {{ modeMeta(m).label }}</span>
          </div>

          <div class="rnd-footer">
            <span class="rnd-price">₱{{ formatFee(rnd.consultation_fee) }}<span class="rnd-price-unit">/session</span></span>
            <NuxtLink :to="`/rnd-profile-view/${rnd.user.id}`" class="outline-btn">View Profile</NuxtLink>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon"><SearchX :size="28" /></div>
        <p class="empty-title">No RNDs match your filters</p>
        <p class="empty-desc">Try another specialization, language, or consultation mode.</p>
      </div>

      <div v-if="pageCount > 1" class="pagination-row">
        <button class="page-btn" :disabled="page === 1" @click="page--"><ChevronLeft :size="14" /> Prev</button>
        <span class="page-current">Page {{ page }} of {{ pageCount }}</span>
        <button class="page-btn page-btn-primary" :disabled="page === pageCount" @click="page++">Next <ChevronRight :size="14" /></button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { Search, SearchX, BadgeCheck, Video, MessageCircle, Users, ChevronLeft, ChevronRight } from 'lucide-vue-next'

const { get } = useApi()

const PAGE_SIZE = 6

// RndProfile.specialization is free text; each option filters by keyword
// (the backend's `specialty` param is a case-insensitive contains match).
const specializations = [
  { label: 'Diabetes Management', keyword: 'Diabetes' },
  { label: 'Renal Nutrition', keyword: 'Renal' },
  { label: 'Hypertension & Cardiac Care', keyword: 'Hypertension' },
  { label: 'Weight Management', keyword: 'Weight' },
  { label: 'Pediatric Nutrition', keyword: 'Pediatric' },
]

// Same set used on the RND-side Languages tab — there's no fixed language
// enum in the backend, just free-text codes per RndLanguage.
const languageOptions = [
  { code: 'tl', label: 'Filipino (Tagalog)' },
  { code: 'ceb', label: 'Bisaya (Cebuano)' },
  { code: 'ilo', label: 'Ilocano' },
  { code: 'en', label: 'English' },
]

const modeOptions = [
  { value: 'video', label: 'Video', icon: Video },
  { value: 'chat', label: 'Chat', icon: MessageCircle },
  { value: 'in_person', label: 'In-Person', icon: Users },
]
function modeMeta(value) {
  return modeOptions.find(m => m.value === value) || { label: value, icon: Video }
}

const specialization = ref('')
const language = ref('')
const mode = ref('')
const sortBy = ref('rating')
const page = ref(1)

const isLoading = ref(true)
const errorMessage = ref('')
const rnds = ref([])

const AVATAR_COLORS = [
  { bg: '#1e4a26', fg: '#fff' }, { bg: '#D4A017', fg: '#1a3a1a' }, { bg: '#7aa87a', fg: '#fff' },
  { bg: '#3a6b3a', fg: '#fff' }, { bg: '#f0dca8', fg: '#1a3a1a' }, { bg: '#00382a', fg: '#fff' },
]
function avatarStyle(id) {
  const c = AVATAR_COLORS[id % AVATAR_COLORS.length]
  return { background: c.bg, color: c.fg }
}
function initialsFor(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
}
function formatFee(fee) {
  return Number(fee).toLocaleString('en-PH', { maximumFractionDigits: 2 })
}

const sortedRnds = computed(() => {
  const list = [...rnds.value]
  if (sortBy.value === 'rating') return list.sort((a, b) => (b.average_rating || 0) - (a.average_rating || 0))
  if (sortBy.value === 'reviews') return list.sort((a, b) => (b.review_count || 0) - (a.review_count || 0))
  if (sortBy.value === 'fee_low') return list.sort((a, b) => a.consultation_fee - b.consultation_fee)
  return list
})

const pageCount = computed(() => Math.max(1, Math.ceil(sortedRnds.value.length / PAGE_SIZE)))
const pagedRnds = computed(() => sortedRnds.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))
watch(sortBy, () => { page.value = 1 })

async function loadRnds() {
  isLoading.value = true
  errorMessage.value = ''
  page.value = 1
  try {
    const params = new URLSearchParams()
    if (specialization.value) params.set('specialty', specialization.value)
    if (language.value) params.set('language', language.value)
    if (mode.value) params.set('mode', mode.value)
    const query = params.toString()
    rnds.value = await get(`/client/rnds/${query ? `?${query}` : ''}`)
  } catch {
    errorMessage.value = 'Could not load RNDs. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadRnds)
</script>

<style scoped>
* { box-sizing: border-box; }
.find-rnd-page { font-family: 'Inter', sans-serif; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

/* FILTER BAR */
.filter-bar { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 20px; margin-bottom: 20px; }
.filter-row { display: grid; grid-template-columns: 1.3fr 1fr 1fr auto; gap: 16px; align-items: end; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.78rem; font-weight: 600; color: #4a5a4a; }
.field select { border: 1px solid #d5dad5; border-radius: 8px; padding: 11px 12px; font-size: 0.85rem; font-family: inherit; color: #2a2a2a; background: #fff; cursor: pointer; }
.field select:focus { outline: none; border-color: #D4A017; }
.search-btn {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  background: #14301a; color: #fff; border: none; border-radius: 8px;
  padding: 11px 20px; font-weight: 700; font-size: 0.85rem; cursor: pointer; white-space: nowrap;
}

/* RESULTS ROW */
.results-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; gap: 12px; }
.results-count { font-size: 0.85rem; color: #6a7a6a; margin: 0; }
.sort-select { border: 1px solid #d5dad5; border-radius: 8px; padding: 9px 12px; font-size: 0.83rem; color: #2a2a2a; background: #fff; cursor: pointer; }

/* RND GRID */
.rnd-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.rnd-card {
  background: #fff; border-radius: 14px; border: 1.5px solid #eceeec; padding: 22px;
  display: flex; flex-direction: column; transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.rnd-card:hover { border-color: #1f8f5c; box-shadow: 0 4px 14px rgba(31,143,92,0.1); }

.rnd-card-top { display: flex; gap: 14px; margin-bottom: 14px; }
.rnd-avatar { width: 56px; height: 56px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; flex-shrink: 0; }
.rnd-name { display: flex; align-items: center; gap: 5px; font-weight: 700; color: #1a3a1a; margin: 0; font-size: 0.92rem; }
.verified-icon { color: #D4A017; }
.rnd-specialty { font-size: 0.78rem; color: #8a9a8a; margin: 3px 0 0; }
.rnd-rating { font-size: 0.78rem; font-weight: 700; color: #b8860b; margin: 3px 0 0; }
.rnd-rating.no-reviews { font-weight: 400; color: #9aaa9a; }
.rnd-review-count { font-weight: 400; color: #9aaa9a; }

.rnd-desc { font-size: 0.83rem; color: #6a7a6a; line-height: 1.5; margin: 0 0 14px; flex: 1; }

.rnd-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.lang-chip { font-size: 0.7rem; background: #eef3ec; color: #1a5a2a; padding: 3px 10px; border-radius: 20px; font-weight: 600; }
.mode-pill { display: flex; align-items: center; gap: 4px; font-size: 0.7rem; background: #e3ecf7; color: #2a5a8a; padding: 3px 10px; border-radius: 20px; font-weight: 600; }

.rnd-footer { display: flex; align-items: center; justify-content: space-between; padding-top: 14px; border-top: 1px solid #f0f2f0; }
.rnd-price { font-weight: 700; color: #1a3a1a; font-size: 0.92rem; }
.rnd-price-unit { font-size: 0.72rem; font-weight: 400; color: #9aaa9a; }
.outline-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 8px 16px; font-weight: 600; font-size: 0.82rem; cursor: pointer; white-space: nowrap; text-decoration: none; }
.outline-btn:hover { background: #f7f9f7; }

/* PAGINATION */
.pagination-row { display: flex; align-items: center; justify-content: center; gap: 14px; margin-top: 22px; }
.page-btn { display: flex; align-items: center; gap: 4px; border: 1px solid #d5dad5; background: #fff; color: #4a5a4a; border-radius: 8px; padding: 9px 16px; font-size: 0.83rem; font-weight: 600; cursor: pointer; }
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-btn-primary { background: #14301a; color: #fff; border-color: #14301a; }
.page-current { font-size: 0.85rem; color: #4a5a4a; font-weight: 600; }

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

@media (max-width: 1150px) {
  .rnd-grid { grid-template-columns: repeat(2, 1fr); }
  .filter-row { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 700px) {
  .rnd-grid { grid-template-columns: 1fr; }
  .filter-row { grid-template-columns: 1fr; }
}
</style>
