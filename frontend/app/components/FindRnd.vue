<template>
  <div class="nm-page">
    <p class="nm-page-sub intro">Every RND here is PRC-licensed and verified by the NutriMatch team. Pick one that fits your needs and book a consultation.</p>

    <!-- filters -->
    <div class="nm-panel filters">
      <div class="filter-top">
        <div class="nm-search name-search">
          <Search :size="15" />
          <input v-model="search" type="search" placeholder="Search by name" />
        </div>
        <button class="nm-btn-outline filters-toggle" type="button" @click="showFilters = !showFilters">
          <SlidersHorizontal :size="15" /> Filters<span v-if="activeFilterCount"> ({{ activeFilterCount }})</span>
        </button>
      </div>
      <div class="filter-grid" :class="{ open: showFilters }">
        <label class="filter-field">
          <span>Specialization</span>
          <select v-model="specialization" class="nm-select">
            <option value="">Any specialization</option>
            <option v-for="s in options.specializations" :key="s" :value="s">{{ s }}</option>
          </select>
        </label>
        <label class="filter-field">
          <span>Language</span>
          <select v-model="language" class="nm-select">
            <option value="">Any language</option>
            <option v-for="l in options.languages" :key="l.code" :value="l.code">{{ l.label }}</option>
          </select>
        </label>
        <label class="filter-field">
          <span>Format</span>
          <select v-model="mode" class="nm-select">
            <option value="">Any format</option>
            <option v-for="m in options.modes" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </label>
      </div>
    </div>

    <!-- One RND at a time (until the current RND discharges the client). -->
    <p v-if="blockedBy" class="one-rnd">
      {{ blockedBy.status === 'active' ? `You're under RND ${blockedBy.name}'s care — you can book a different RND once they discharge you.` : `You have a booking waiting for RND ${blockedBy.name} — cancel it first to book someone else.` }}
      <NuxtLink :to="`/rnd-profile-view/${blockedBy.rnd_id}`">Go to RND {{ blockedBy.name }} →</NuxtLink>
    </p>
    <div class="results-row">
      <p class="nm-muted">
        <template v-if="loading">Finding RNDs…</template>
        <template v-else>{{ rnds.length }} RND{{ rnds.length === 1 ? '' : 's' }} available</template>
        <template v-if="activeFilterCount || search"> · <button class="nm-panel-link" @click="clearFilters">Clear filters</button></template>
      </p>
    </div>

    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>

    <!-- skeletons -->
    <div v-if="loading" class="rnd-grid">
      <div v-for="n in 4" :key="n" class="nm-panel card skeleton">
        <div class="sk-row"><span class="sk sk-avatar" /><span style="flex: 1"><span class="sk sk-line w60" /><span class="sk sk-line w40" /></span></div>
        <span class="sk sk-line" /><span class="sk sk-line w80" /><span class="sk sk-line w50" />
      </div>
    </div>

    <div v-else-if="!rnds.length && !error" class="nm-panel nm-empty">
      <SearchX :size="28" />
      <p>No RNDs match these filters.</p>
      <button class="nm-btn-outline" style="margin-top: 12px" @click="clearFilters">Clear filters</button>
    </div>

    <div v-else class="rnd-grid">
      <article v-for="rnd in paged" :key="rnd.id" class="nm-panel card">
        <div class="card-head">
          <img v-if="rnd.user.profile_photo" :src="rnd.user.profile_photo" class="nm-avatar lg" alt="" />
          <span v-else class="nm-avatar lg">{{ userInitials(rnd.user.first_name, rnd.user.last_name) }}</span>
          <div class="card-id">
            <h2 class="card-name">{{ rnd.user.first_name }} {{ rnd.user.last_name }} <BadgeCheck :size="16" class="verified" aria-label="PRC-verified" /></h2>
            <p class="card-spec">{{ rnd.specialization || 'General / Clinical Nutrition' }}</p>
            <p class="card-meta">
              <span v-if="rnd.review_count" class="stars">★ {{ rnd.average_rating.toFixed(1) }}</span>
              <span v-if="rnd.review_count" class="nm-muted">({{ rnd.review_count }})</span>
              <span v-else class="nm-muted">New on NutriMatch</span>
              <span v-if="rnd.consultations_completed" class="nm-muted">· {{ rnd.consultations_completed }} consultation{{ rnd.consultations_completed === 1 ? '' : 's' }}</span>
            </p>
          </div>
          <span v-if="rnd.is_my_rnd" class="nm-pill green my-rnd">Your RND</span>
        </div>

        <p class="card-bio">{{ rnd.bio }}</p>

        <div class="chips">
          <span v-for="l in rnd.languages" :key="l.code" class="chip">{{ l.language_name.replace(/ \(.*\)/, '') }}</span>
        </div>
        <div class="formats">
          <span v-for="m in rnd.consultation_modes" :key="m" class="format"><component :is="MODE_ICONS[m]" :size="13" /> {{ MODE_LABELS[m] }}</span>
        </div>
        <p v-if="rnd.clinic_address" class="where"><MapPin :size="13" /> {{ rnd.clinic_address }}</p>

        <div class="next" :class="{ none: !rnd.next_open_slots.length }">
          <CalendarClock :size="14" />
          <span v-if="rnd.next_open_slots.length">Next available: <strong>{{ slotText(rnd.next_open_slots[0]) }}</strong></span>
          <span v-else>No open times in the next 4 weeks</span>
        </div>

        <div class="card-foot">
          <div class="card-actions">
            <NuxtLink :to="`/rnd-profile-view/${rnd.user.id}`" class="nm-btn-outline">View profile</NuxtLink>
            <NuxtLink v-if="rnd.next_open_slots.length && !rnd.booking_blocked_by" :to="`/rnd-profile-view/${rnd.user.id}?book=1`" class="nm-btn-dark">Book</NuxtLink>
          </div>
        </div>
      </article>
    </div>

    <div v-if="!loading && pageCount > 1" class="pagination">
      <button class="nm-btn-outline nm-btn-sm" :disabled="page === 1" @click="page--"><ChevronLeft :size="14" /> Previous</button>
      <span class="nm-muted">Page {{ page }} of {{ pageCount }}</span>
      <button class="nm-btn-outline nm-btn-sm" :disabled="page === pageCount" @click="page++">Next <ChevronRight :size="14" /></button>
    </div>
  </div>
</template>

<script setup>
import {
  BadgeCheck, CalendarClock, ChevronLeft, ChevronRight, MapPin, MessageCircle, Search, SearchX, SlidersHorizontal, Users, Video,
} from 'lucide-vue-next'

const { get } = useApi()

const PAGE_SIZE = 6
const MODE_ICONS = { video: Video, chat: MessageCircle, in_person: Users }
const MODE_LABELS = { video: 'Video', chat: 'Chat', in_person: 'In-person' }

const options = ref({ specializations: [], languages: [], modes: [] })
const search = ref('')
const specialization = ref('')
const language = ref('')
const mode = ref('')
const showFilters = ref(false)
const page = ref(1)

const rnds = ref([])
// The client's current RND when it's someone else (same for every row).
const blockedBy = computed(() => rnds.value.find(r => r.booking_blocked_by)?.booking_blocked_by || null)
const loading = ref(true)
const error = ref('')

const activeFilterCount = computed(() => [specialization.value, language.value, mode.value].filter(Boolean).length)
function clearFilters() {
  search.value = ''
  specialization.value = ''
  language.value = ''
  mode.value = ''
}

// RND specializations are free text for older accounts (e.g. "Diabetes &
// Weight Management"), so filter by the option's first word.
const specialtyKeyword = s => s.split(/[ /&]/)[0]

let requestId = 0
async function load() {
  const id = ++requestId
  loading.value = true
  error.value = ''
  page.value = 1
  const query = {}
  if (search.value.trim()) query.search = search.value.trim()
  if (specialization.value) query.specialty = specialtyKeyword(specialization.value)
  if (language.value) query.language = language.value
  if (mode.value) query.mode = mode.value
  try {
    const r = await get('/client/rnds/', { query })
    if (id === requestId) rnds.value = r
  } catch {
    if (id === requestId) error.value = 'Could not load RNDs.'
  } finally {
    if (id === requestId) loading.value = false
  }
}

let searchTimer
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(load, 350)
})
watch([specialization, language, mode], load)

onMounted(async () => {
  load()
  try {
    options.value = await get('/client/rnds/options/')
  } catch {
    // filters just stay empty
  }
})

// Always soonest available first (no sort menu, user's call 2026-10-13).
const sorted = computed(() => {
  const firstSlot = r => (r.next_open_slots[0] ? new Date(r.next_open_slots[0]).getTime() : Infinity)
  return [...rnds.value].sort((a, b) => firstSlot(a) - firstSlot(b))
})
const pageCount = computed(() => Math.max(1, Math.ceil(sorted.value.length / PAGE_SIZE)))
const paged = computed(() => sorted.value.slice((page.value - 1) * PAGE_SIZE, page.value * PAGE_SIZE))

function slotText(iso) {
  const d = new Date(iso)
  const ph = { timeZone: 'Asia/Manila' }
  const day = d.toLocaleDateString('en-CA', ph)
  const today = new Date().toLocaleDateString('en-CA', ph)
  const tomorrow = new Date(Date.now() + 86400000).toLocaleDateString('en-CA', ph)
  const time = d.toLocaleTimeString('en-PH', { ...ph, hour: 'numeric', minute: '2-digit' })
  if (day === today) return `Today · ${time}`
  if (day === tomorrow) return `Tomorrow · ${time}`
  return `${d.toLocaleDateString('en-PH', { ...ph, weekday: 'short', month: 'short', day: 'numeric' })} · ${time}`
}
</script>

<style scoped>
.intro { margin: 0 0 16px; }
.filters { margin-bottom: 14px; }
.filter-top { display: flex; gap: 10px; }
.name-search { max-width: none; flex: 1; }
.filters-toggle { display: none; }
.filter-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 14px; }
.filter-field { display: flex; flex-direction: column; gap: 6px; min-width: 0; }
.filter-field > span { font-size: 0.74rem; font-weight: 600; color: #6a7a6a; }
.filter-field .nm-select { width: 100%; }
.results-row { margin: 0 0 14px; }

/* minmax(0, 1fr) + overflow-wrap: long unbroken text can't widen a card past the screen */
.rnd-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.card { display: flex; flex-direction: column; gap: 12px; min-width: 0; overflow-wrap: anywhere; }
.card-head { display: flex; gap: 14px; align-items: flex-start; }
.card-id { flex: 1; min-width: 0; }
.card-name { font-family: 'Playfair Display', serif; font-size: 1.12rem; color: #1a3a1a; margin: 0; display: flex; align-items: center; gap: 6px; }
.verified { color: #1f8f5c; flex-shrink: 0; }
.card-spec { font-size: 0.82rem; color: #4a5a4a; margin: 3px 0 0; }
.card-meta { display: flex; flex-wrap: wrap; gap: 4px; font-size: 0.78rem; margin: 5px 0 0; }
.stars { color: #b8860b; font-weight: 700; }
.my-rnd { flex-shrink: 0; }
.card-bio { font-size: 0.85rem; color: #4a5a4a; line-height: 1.55; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { font-size: 0.72rem; font-weight: 600; background: #f3f5f2; color: #4a5a4a; border-radius: 12px; padding: 3px 10px; }
.formats { display: flex; flex-wrap: wrap; gap: 12px; }
.format { display: inline-flex; align-items: center; gap: 5px; font-size: 0.78rem; color: #2a3a2a; font-weight: 500; }
.where { display: flex; align-items: flex-start; gap: 6px; font-size: 0.78rem; color: #6a7a6a; margin: 0; line-height: 1.4; }
.where svg { flex-shrink: 0; margin-top: 2px; }
.next { display: flex; align-items: center; gap: 8px; background: #eef6f0; color: #1f6f46; border-radius: 8px; padding: 9px 12px; font-size: 0.8rem; }
.next.none { background: #f4f5f3; color: #8a9a8a; }
.card-foot { display: flex; align-items: center; justify-content: flex-end; gap: 12px; margin-top: auto; padding-top: 12px; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.card-actions { display: flex; gap: 8px; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 14px; margin-top: 20px; }

.skeleton { pointer-events: none; }
.sk-row { display: flex; gap: 14px; align-items: center; }
.sk { display: block; background: linear-gradient(90deg, #f0f2f0 25%, #e6eae6 50%, #f0f2f0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 6px; }
.sk-avatar { width: 64px; height: 64px; border-radius: 50%; flex-shrink: 0; }
.sk-line { height: 12px; margin: 6px 0; width: 100%; }
.w80 { width: 80%; } .w60 { width: 60%; } .w50 { width: 50%; } .w40 { width: 40%; }
@keyframes shimmer { to { background-position: -200% 0; } }

@media (max-width: 1150px) {
  .filter-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 860px) {
  .rnd-grid { grid-template-columns: minmax(0, 1fr); }
}
@media (max-width: 640px) {
  .filters-toggle { display: inline-flex; }
  .filter-grid { display: none; grid-template-columns: 1fr 1fr; }
  .filter-grid.open { display: grid; }
  .card-foot { flex-direction: column; align-items: stretch; }
  .card-actions > * { flex: 1; }
}
.one-rnd { background: #fff8e8; border: 1px solid #f1dca3; border-radius: 10px; padding: 10px 14px; font-size: 0.84rem; color: #5a4a1a; line-height: 1.5; margin: 0 0 12px; }
.one-rnd a { color: #1f6f46; font-weight: 600; margin-left: 4px; white-space: nowrap; }
</style>
