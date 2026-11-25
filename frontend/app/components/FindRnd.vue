<template>
  <div class="nm-page fr-page">
    <!-- HERO: salad photo on the right, green fade from the left -->
    <section class="fr-hero">
      <div class="fr-hero-text">
        <p class="fr-eyebrow"><span aria-hidden="true"></span>Care team</p>
        <h2 class="fr-title">Find an RND who <em>fits you.</em></h2>
        <p class="fr-hero-sub"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg>Every RND here is PRC-licensed and verified by the NutriMatch team.</p>
      </div>

      <div class="fr-searchbar" :class="{ open: showFilters }">
        <label class="fr-search">
          <span class="fr-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg></span>
          <span class="fr-fld">
            <input v-model="search" type="search" placeholder="Search an RND..." aria-label="Search RNDs by name" />
          </span>
        </label>
        <button class="fr-filter-btn" type="button" :aria-expanded="showFilters" aria-label="Filters" @click="showFilters = !showFilters">
          <svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12" /><circle cx="16" cy="6" r="2" /><circle cx="10" cy="12" r="2" /><circle cx="18" cy="18" r="2" /></svg><span v-if="activeFilterCount" class="fr-filter-count">{{ activeFilterCount }}</span>
        </button>
        <div class="fr-fields">
          <label class="fr-select">
            <span class="fr-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path fill="currentColor" d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg></span>
            <span class="fr-fld">
              <small>Specialization</small>
              <select v-model="specialization">
                <option value="">Any specialization</option>
                <option v-for="s in options.specializations" :key="s" :value="s">{{ s }}</option>
              </select>
            </span>
            <svg class="ic fr-caret" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
          </label>
          <label class="fr-select">
            <span class="fr-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9s-1.3 6.3-3.8 9c-2.5-2.7-3.8-5.7-3.8-9S9.5 5.7 12 3z" /></svg></span>
            <span class="fr-fld">
              <small>Language</small>
              <select v-model="language">
                <option value="">Any language</option>
                <option v-for="l in options.languages" :key="l.code" :value="l.code">{{ l.label }}</option>
              </select>
            </span>
            <svg class="ic fr-caret" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
          </label>
          <label class="fr-select">
            <span class="fr-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg></span>
            <span class="fr-fld">
              <small>Format</small>
              <select v-model="mode">
                <option value="">Any format</option>
                <option v-for="m in options.modes" :key="m.value" :value="m.value">{{ m.label }}</option>
              </select>
            </span>
            <svg class="ic fr-caret" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 9l6 6 6-6" /></svg>
          </label>
        </div>
      </div>
    </section>

    <!-- One RND at a time (until the current RND discharges the client). -->
    <div v-if="blockedBy" class="one-rnd">
      <span class="one-rnd-icon"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 8h.01M11 12h1v5h1" /></svg></span>
      <p>{{ blockedBy.status === 'active'
        ? `You're under RND ${blockedBy.name}'s care, so you can book a different RND once they discharge you. To switch, ask to end your care in Profile Settings, Care team.`
        : `You have a booking waiting for RND ${blockedBy.name}. Cancel it first to book someone else.` }}</p>
      <NuxtLink :to="`/rnd-profile-view/${blockedBy.rnd_id}`" class="fr-btn-soft sm">Go to RND {{ blockedBy.name }}</NuxtLink>
    </div>

    <div class="results-row">
      <p class="fr-count">
        <template v-if="loading">Finding RNDs…</template>
        <template v-else><span class="fr-live" aria-hidden="true"></span><strong>{{ rnds.length }} RND{{ rnds.length === 1 ? '' : 's' }}</strong> Available</template>
      </p>
      <div class="results-right">
        <button v-if="activeFilterCount || search" class="fr-clear" type="button" @click="clearFilters">Clear filters</button>
        <span class="fr-sort">Sort by: <strong>Soonest open time</strong></span>
      </div>
    </div>

    <p v-if="error" class="nm-error fr-error">{{ error }} <button class="fr-btn-soft sm" @click="load">Try again</button></p>

    <!-- skeletons -->
    <div v-if="loading" class="rnd-grid">
      <div v-for="n in 3" :key="n" class="card skeleton">
        <div class="sk-row"><span class="sk sk-avatar" /><span style="flex: 1"><span class="sk sk-line w60" /><span class="sk sk-line w40" /></span></div>
        <span class="sk sk-line" /><span class="sk sk-line w80" />
        <span class="sk sk-box" />
      </div>
    </div>

    <div v-else-if="!rnds.length && !error" class="fr-empty">
      <span class="fr-empty-icon"><SearchX :size="26" /></span>
      <p class="fr-empty-title">No RNDs match these filters.</p>
      <p class="fr-empty-sub">Try another specialization, language or format.</p>
      <button class="fr-btn-soft" type="button" @click="clearFilters">Clear filters</button>
    </div>

    <!-- RND CARDS (new design) -->
    <div v-else class="rnd-grid">
      <article v-for="rnd in paged" :key="rnd.id" class="card" :class="{ mine: rnd.is_my_rnd }">
        <div class="card-top">
          <span class="card-avatar">
            <img v-if="rnd.user.profile_photo" :src="rnd.user.profile_photo" alt="" />
            <template v-else>{{ userInitials(rnd.user.first_name, rnd.user.last_name) }}</template>
            <i title="PRC verified"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></i>
          </span>
          <div class="card-id">
            <span v-if="rnd.is_my_rnd" class="my-rnd">★ Your RND</span>
            <h2 class="card-name">{{ rnd.user.first_name }} {{ rnd.user.last_name }} <BadgeCheck :size="20" class="verified" aria-label="PRC verified" /></h2>
            <p class="card-spec">{{ rnd.specialization || 'General and clinical nutrition' }}</p>
            <p class="card-meta">
              <span v-if="rnd.review_count" class="stars"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="#EFBF04" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg><strong>{{ rnd.average_rating.toFixed(1) }}</strong><span class="muted">({{ rnd.review_count }})</span></span>
              <span v-else class="new-pill"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg>New on NutriMatch</span>
              <template v-if="rnd.consultations_completed"><span class="dot" aria-hidden="true"></span><span class="muted">{{ rnd.consultations_completed }} consultation{{ rnd.consultations_completed === 1 ? '' : 's' }}</span></template>
            </p>
          </div>
        </div>

        <p v-if="rnd.bio" class="card-bio">{{ rnd.bio }}</p>

        <div v-if="rnd.languages.length" class="chips">
          <span v-for="l in rnd.languages" :key="l.language_name" class="chip">{{ l.language_name.replace(/ \(.*\)/, '') }}</span>
        </div>

        <div class="card-row">
          <div class="card-facts">
            <span v-for="m in rnd.consultation_modes" :key="m" class="fact"><component :is="MODE_ICONS[m]" :size="17" aria-hidden="true" /> {{ MODE_LABELS[m] }}</span>
          </div>
          <!-- Shows only if the API sends a fee. Rename session_fee to your real field name. -->
          <span v-if="rnd.session_fee != null" class="price">₱{{ Number(rnd.session_fee).toLocaleString('en-PH') }} <small>per 60-min session</small></span>
        </div>
        <p v-if="rnd.clinic_address" class="fact where"><MapPin :size="17" aria-hidden="true" /> {{ rnd.clinic_address }}</p>

        <div class="slots-box">
          <template v-if="rnd.next_open_slots.length">
            <p class="side-label"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>Next open: <b>{{ slotDay(rnd.next_open_slots[0]) }}</b></p>
            <div class="slots">
              <span v-for="(t, i) in sameDaySlots(rnd.next_open_slots)" :key="t" class="slot" :class="{ first: i === 0 }">{{ slotTime(t) }}</span>
            </div>
          </template>
          <template v-else>
            <p class="side-label"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>Next open</p>
            <p class="no-slots">No open times in the next 4 weeks</p>
          </template>
        </div>

        <div class="card-actions">
          <NuxtLink :to="`/rnd-profile-view/${rnd.user.id}`" class="fr-btn-soft">View profile</NuxtLink>
          <NuxtLink v-if="rnd.next_open_slots.length && !rnd.booking_blocked_by" :to="`/rnd-profile-view/${rnd.user.id}?book=1`" class="fr-btn-dark"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>Book</NuxtLink>
        </div>
      </article>
    </div>

    <div v-if="!loading && pageCount > 1" class="pagination">
      <button class="fr-btn-soft sm" :disabled="page === 1" @click="page--"><ChevronLeft :size="14" /> Previous</button>
      <span class="fr-count muted">Page {{ page }} of {{ pageCount }}</span>
      <button class="fr-btn-soft sm" :disabled="page === pageCount" @click="page++">Next <ChevronRight :size="14" /></button>
    </div>
  </div>
</template>

<script setup>
import {
  BadgeCheck, CalendarClock, ChevronLeft, ChevronRight, MapPin, Search, SearchX, SlidersHorizontal, Users, Video,
} from 'lucide-vue-next'

const { get } = useApi()

const PAGE_SIZE = 6
const MODE_ICONS = { video: Video, in_person: Users }
const MODE_LABELS = { video: 'Video call', in_person: 'In person' }

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

let requestId = 0
async function load({ quiet = false } = {}) {
  const id = ++requestId
  if (!quiet) {
    loading.value = true
    error.value = ''
    page.value = 1
  }
  const query = {}
  if (search.value.trim()) query.search = search.value.trim()
  if (specialization.value) query.specialty = specialization.value // one whole name; an RND may list up to 3
  if (language.value) query.language = language.value
  if (mode.value) query.mode = mode.value
  try {
    const r = await get('/client/rnds/', { query })
    if (id === requestId) rnds.value = r
  } catch {
    if (id === requestId && !quiet) error.value = 'Could not load the RNDs.'
  } finally {
    if (id === requestId) loading.value = false
  }
}
// open times and "one RND at a time" stay current; keeps the page you're on
useAutoRefresh(() => load({ quiet: true }))

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
  if (day === today) return `today, ${time}`
  if (day === tomorrow) return `tomorrow, ${time}`
  return `${d.toLocaleDateString('en-PH', { ...ph, weekday: 'short', month: 'short', day: 'numeric' })}, ${time}`
}

/* ---------- UI only: the "Next open" times on each card ---------- */
const PH = { timeZone: 'Asia/Manila' }
function slotDay(iso) {
  const d = new Date(iso)
  const day = d.toLocaleDateString('en-CA', PH)
  if (day === new Date().toLocaleDateString('en-CA', PH)) return 'Today'
  if (day === new Date(Date.now() + 86400000).toLocaleDateString('en-CA', PH)) return 'Tomorrow'
  return d.toLocaleDateString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric' })
}
function slotTime(iso) {
  return new Date(iso).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
}
// up to three times on the same day as the first open time
function sameDaySlots(slots) {
  const first = new Date(slots[0]).toLocaleDateString('en-CA', PH)
  return slots.filter(s => new Date(s).toLocaleDateString('en-CA', PH) === first).slice(0, 3)
}
</script>

<style scoped>
/* =========================================================
   Find an RND: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings), DM Sans (body)
   ========================================================= */
.fr-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; gap: 18px; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }

/* ---------- HERO (salad photo, green fade from the left) ---------- */
.fr-hero {
  position: relative;
  padding: 34px 36px 26px;
  border-radius: 24px;
  color: #FFFFFF;
  background-color: #0B5640;
  background-image:
    linear-gradient(90deg, #0B5640 0%, #0B5640 40%, rgba(11, 86, 64, 0.85) 54%, rgba(11, 86, 64, 0.2) 74%, rgba(11, 86, 64, 0) 90%),
    url('/landing/find-rnd-hero.webp');
  background-repeat: no-repeat;
  background-size: auto, cover;
  background-position: 0 0, right center;
  box-shadow: 0 10px 30px -18px rgba(0, 77, 58, 0.5);
}
.fr-hero-text { position: relative; z-index: 1; max-width: 560px; }
.fr-eyebrow { margin: 0; display: flex; align-items: center; gap: 10px; font-size: 12.5px; font-weight: 800; color: #EFBF04; }
.fr-eyebrow span { width: 26px; height: 2px; border-radius: 2px; background: #EFBF04; }
.fr-title { margin: 10px 0 12px; font-family: 'Playfair Display', Georgia, serif; font-size: 46px; font-weight: 700; line-height: 1.1; letter-spacing: -0.3px; color: #FFFFFF; }
.fr-title em { font-style: italic; color: #EFBF04; }
.fr-hero-sub { margin: 0; display: flex; align-items: center; gap: 10px; font-size: 15px; line-height: 1.5; color: rgba(255, 255, 255, 0.88); }
.fr-hero-sub .ic { color: #8FD4A8; }

/* ---------- SEARCH BAR ---------- */
.fr-searchbar {
  position: relative;
  z-index: 1;
  margin-top: 24px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 7px 7px 7px 10px;
  border-radius: 999px;
  background: #FFFFFF;
  box-shadow: 0 18px 40px -18px rgba(0, 0, 0, 0.45);
}
.fr-search,
.fr-select {
  position: relative;
  flex: 1 1 0;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  height: 56px;
  padding: 0 14px 0 8px;
  border-radius: 999px;
  cursor: pointer;
  transition: background-color .15s;
}
.fr-search { flex: 1.25 1 0; cursor: text; }
.fr-search:hover,
.fr-select:hover { background: #F6F9F7; }
.fr-select + .fr-select::before,
.fr-fields > .fr-select:first-child::before {
  content: '';
  position: absolute;
  left: -2px;
  top: 12px;
  bottom: 12px;
  width: 1px;
  background: #E3E9E5;
}
.fr-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 50%; background: #EEF5F0; display: inline-flex; align-items: center; justify-content: center; color: #004D3A; }
.fr-fld { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.fr-fld small { font-size: 12.5px; font-weight: 600; color: #1F7A55; }
.fr-fld input,
.fr-fld select {
  width: 100%;
  min-width: 0;
  padding: 0;
  border: none;
  outline: none;
  background: transparent;
  font-family: inherit;
  font-size: 14.5px;
  color: #22362C;
  -webkit-appearance: none;
  appearance: none;
  text-overflow: ellipsis;
  cursor: inherit;
}
.fr-fld input { font-size: 15px; }
.fr-fld input::placeholder { color: #5E6E66; }
.fr-fld input::-webkit-search-cancel-button { cursor: pointer; }
.fr-caret { color: #6B7D73; pointer-events: none; }
.fr-fields { flex: 3.4 1 0; min-width: 0; display: flex; align-items: center; gap: 4px; }
.fr-filter-btn:focus-visible { outline: 3px solid #EFBF04; outline-offset: 2px; }
.fr-search:focus-within,
.fr-select:focus-within { background: #F1F6F2; }
.fr-filter-btn {
  display: none;
  position: relative;
  flex-shrink: 0;
  width: 46px;
  height: 46px;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 12px;
  background: #F1F6F2;
  color: #004D3A;
  cursor: pointer;
}
.fr-filter-count {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: #EFBF04;
  color: #10231B;
  font-size: 11px;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* ---------- notice, count ---------- */
.one-rnd {
  display: flex;
  align-items: center;
  gap: 12px 14px;
  flex-wrap: wrap;
  padding: 14px 16px;
  border-radius: 16px;
  background: #FBF8EC;
  border: 1px solid #F1E2A6;
}
.one-rnd-icon { flex-shrink: 0; width: 34px; height: 34px; border-radius: 50%; background: #FFFFFF; color: #9A7300; display: inline-flex; align-items: center; justify-content: center; }
.one-rnd p { flex: 1; min-width: 220px; margin: 0; font-size: 14px; line-height: 1.55; color: #4A3E10; }
.results-row { display: flex; align-items: center; justify-content: space-between; gap: 10px 16px; flex-wrap: wrap; margin: 6px 2px 0; }
.results-right { display: flex; align-items: center; gap: 12px; }
.fr-count { margin: 0; display: inline-flex; align-items: center; gap: 10px; font-size: 16px; color: #3E5046; }
.fr-count strong { color: #10231B; font-weight: 800; }
.fr-count.muted { font-size: 13px; color: #6B7D73; }
.fr-live { width: 10px; height: 10px; border-radius: 50%; background: #1F9D55; box-shadow: 0 0 0 4px rgba(31, 157, 85, 0.15); }
.fr-sort { display: inline-flex; align-items: center; gap: 6px; height: 40px; padding: 0 16px; border-radius: 12px; background: #FFFFFF; border: 1px solid #E1E7E3; font-size: 13.5px; color: #6B7D73; white-space: nowrap; }
.fr-sort strong { color: #10231B; font-weight: 700; }
.fr-clear { border: none; background: none; padding: 0; font-family: inherit; font-size: 13.5px; font-weight: 700; color: #004D3A; cursor: pointer; }
.fr-clear:hover { text-decoration: underline; text-underline-offset: 3px; }
.fr-error { display: flex; align-items: center; gap: 12px; margin: 0; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; }

/* ---------- buttons ---------- */
.fr-btn-soft,
.fr-btn-dark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 46px;
  padding: 0 22px;
  border: none;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14.5px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color .15s;
}
.fr-btn-soft { background: #F1F6F2; color: #004D3A; }
.fr-btn-soft:hover:not(:disabled) { background: #E3EFE7; }
.fr-btn-soft:disabled { opacity: .5; cursor: not-allowed; }
.fr-btn-soft.sm { height: 36px; padding: 0 14px; font-size: 13px; }
.fr-btn-dark { background: #004D3A; color: #FFFFFF; }
.fr-btn-dark:hover { background: #0A5C46; }

/* ---------- RND cards (new design) ---------- */
.rnd-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 22px; }
.card {
  position: relative;
  display: flex;
  flex-direction: column;
  padding: 22px;
  border-radius: 22px;
  background: #FFFFFF;
  border: 1px solid #EDF1EE;
  box-shadow: 0 2px 6px rgba(16, 35, 27, 0.04), 0 14px 30px -20px rgba(16, 35, 27, 0.22);
  transition: box-shadow .2s;
}
.card:hover { box-shadow: 0 2px 6px rgba(16, 35, 27, 0.05), 0 20px 38px -20px rgba(16, 35, 27, 0.3); }
.card.mine { border-color: #EFBF04; }

.card-top { display: flex; align-items: center; gap: 16px; }
.card-avatar {
  position: relative;
  flex-shrink: 0;
  width: 76px;
  height: 76px;
  border-radius: 50%;
  background: linear-gradient(135deg, #F5CF4A, #DCA812);
  color: #0A3A2B;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 26px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.card-avatar img { width: 100%; height: 100%; object-fit: cover; border-radius: 50%; }
.card-avatar i {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #0B6B47;
  color: #FFFFFF;
  border: 3px solid #FFFFFF;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.card-id { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: flex-start; }
.my-rnd { margin-bottom: 6px; padding: 3px 10px; border-radius: 999px; background: #FDF6DA; color: #8A6700; font-size: 12px; font-weight: 800; }
.card-name { margin: 0; display: flex; align-items: center; gap: 6px; font-size: 22px; font-weight: 700; line-height: 1.2; color: #0E3A2C; }
.verified { flex-shrink: 0; color: #FFFFFF; fill: #0B6B47; }
.card-spec { margin: 3px 0 8px; font-size: 14.5px; font-weight: 700; color: #1F7A4D; }
.card-meta { margin: 0; display: flex; flex-wrap: wrap; align-items: center; gap: 6px 8px; font-size: 13px; }
.stars { display: inline-flex; align-items: center; gap: 4px; color: #10231B; }
.muted { color: #6B7D73; }
.new-pill { display: inline-flex; align-items: center; gap: 6px; height: 26px; padding: 0 11px; border-radius: 999px; background: #F6EAB8; border: 1px solid #ECD98A; color: #6A5200; font-size: 12.5px; font-weight: 600; }
.new-pill .ic { color: #8A6700; }
.dot { width: 3px; height: 3px; border-radius: 50%; background: #B8C9BE; }

.card-bio {
  margin: 16px 0 12px;
  font-size: 14.5px;
  line-height: 1.55;
  color: #5D6F68;
  overflow-wrap: anywhere;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.chips { display: flex; flex-wrap: wrap; gap: 8px; }
.chip { padding: 6px 14px; border-radius: 999px; background: #EEF2EE; font-size: 13px; font-weight: 600; color: #22362C; }

.card-row { display: flex; align-items: center; justify-content: space-between; gap: 10px 14px; flex-wrap: wrap; margin: 16px 0 6px; }
.card-facts { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 16px; }
.fact { display: inline-flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 500; color: #0E5A40; line-height: 1.3; }
.fact svg,
.fact .ic { flex-shrink: 0; }
.fact.where { margin: 4px 0 0; color: #22362C; }
.price { font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #10231B; }
.price small { font-family: 'DM Sans', 'Inter', Arial, sans-serif; font-size: 13px; font-weight: 400; color: #6B7D73; }

.slots-box { margin-top: 14px; padding: 14px; border-radius: 16px; background: #E4EEE8; }
.side-label { margin: 0 0 10px; display: flex; align-items: center; gap: 8px; font-size: 14px; color: #22362C; }
.side-label .ic { color: #0E5A40; }
.side-label b { color: #0E3A2C; }
.slots { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.slot { height: 38px; display: inline-flex; align-items: center; justify-content: center; border-radius: 10px; background: #FFFFFF; border: 1px solid #DFE7E2; font-size: 13px; font-weight: 600; color: #14261E; }
.slot.first { background: #0E4D38; border-color: #0E4D38; color: #FFFFFF; }
.no-slots { margin: 0; font-size: 13.5px; color: #6B7D73; }

.card-actions { margin-top: auto; padding-top: 18px; display: grid; grid-template-columns: 1fr 1.15fr; gap: 12px; }
.card-actions > :only-child { grid-column: 1 / -1; }
.card-actions .fr-btn-soft,
.card-actions .fr-btn-dark { height: 48px; border-radius: 14px; }
.card-actions .fr-btn-soft { background: #E4EEE8; color: #14261E; }
.card-actions .fr-btn-soft:hover { background: #D6E6DC; }
.card-actions .fr-btn-dark { background: #0E4D38; box-shadow: 0 8px 18px -8px rgba(14, 77, 56, 0.55); }
.card-actions .fr-btn-dark:hover { background: #136047; }

/* empty + pages */
.fr-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px 20px;
  border-radius: 20px;
  background: #FFFFFF;
  border: 1px solid #E1E7E3;
  text-align: center;
}
.fr-empty-icon { width: 56px; height: 56px; border-radius: 18px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.fr-empty-title { margin: 6px 0 0; font-size: 16px; font-weight: 700; color: #10231B; }
.fr-empty-sub { margin: 0 0 8px; font-size: 13.5px; color: #6B7D73; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 14px; margin-top: 4px; }

/* skeleton */
.skeleton { pointer-events: none; gap: 6px; }
.sk-row { display: flex; gap: 14px; align-items: center; margin-bottom: 8px; }
.sk { display: block; background: linear-gradient(90deg, #F0F2F0 25%, #E6EAE6 50%, #F0F2F0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 8px; }
.sk-avatar { width: 76px; height: 76px; border-radius: 50%; flex-shrink: 0; }
.sk-line { height: 12px; margin: 6px 0; width: 100%; }
.sk-box { height: 96px; margin-top: 8px; border-radius: 16px; }
.w80 { width: 80%; } .w60 { width: 60%; } .w50 { width: 50%; } .w40 { width: 40%; }
@keyframes shimmer { to { background-position: -200% 0; } }

/* ---------- SMALLER SCREENS ---------- */
@media (max-width: 1100px) {
  /* search on its own row, filters + button below */
  .fr-searchbar { flex-wrap: wrap; }
  .fr-search { flex: 1 1 100%; }
  .fr-searchbar { border-radius: 30px; }
  .fr-fields { flex: 1 1 100%; border-top: 1px solid #EEF2EF; padding-top: 4px; }
  .fr-fields > .fr-select:first-child::before { display: none; }
  .fr-title { font-size: 40px; }
}
@media (max-width: 900px) {
  /* filters collapse behind the filter button */
  .fr-hero { padding: 28px 22px 22px; background-position: 0 0, 70% center; background-image:
      linear-gradient(180deg, rgba(0, 77, 58, 0.55) 0%, rgba(0, 77, 58, 0.92) 45%, #004D3A 100%),
      url('/landing/find-rnd-hero.webp'); }
  .fr-searchbar { flex-wrap: wrap; margin-top: 22px; padding: 6px; gap: 6px; border-radius: 30px; }
  .fr-filter-btn { border-radius: 50%; }
  .fr-search { flex: 1 1 0; height: 52px; padding: 0 12px; }
  .fr-filter-btn { display: inline-flex; }
  .fr-fields { display: none; flex: 1 1 100%; flex-direction: column; align-items: stretch; gap: 2px; padding-top: 6px; }
  .fr-searchbar.open .fr-fields { display: flex; }
  .fr-select { height: 54px; flex: none; }
  .fr-select + .fr-select::before { left: 12px; right: 12px; top: -1px; bottom: auto; width: auto; height: 1px; }
}
@media (max-width: 640px) {
  .fr-title { font-size: 32px; margin: 10px 0 12px; }
  .fr-hero-sub { font-size: 13.5px; align-items: flex-start; }
  .fr-hero-sub .ic { margin-top: 1px; }
  .results-row { align-items: flex-start; flex-direction: column; }
  .results-right { width: 100%; justify-content: space-between; }
  .fr-sort { height: 36px; padding: 0 12px; font-size: 12.5px; }
  .rnd-grid { grid-template-columns: 1fr; gap: 16px; }
  .card { padding: 18px; }
  .pagination { gap: 8px; }
}
@media (prefers-reduced-motion: reduce) {
  .card, .sk { transition: none; animation: none; }
}
</style>