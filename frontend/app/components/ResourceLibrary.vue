<template>
  <div class="nm-page rs-page">
    <!-- HERO -->
    <section class="rs-hero">
      <img class="rs-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="rs-hero-fade" aria-hidden="true"></span>
      <div class="rs-hero-text">
        <p class="rs-eyebrow"><span aria-hidden="true"></span>Resources</p>
        <h2 class="rs-heading">Learn more, <em>eat better.</em></h2>
        <p class="nm-page-sub intro"><BookOpen :size="17" aria-hidden="true" />Guides, videos and links your RND shared with you, to help you follow your plan.</p>
      </div>
    </section>

    <p v-if="error" class="nm-error">{{ error }} <button class="rs-btn soft sm" @click="load">Try again</button></p>

    <div v-if="resources.length" class="rs-bar">
      <div class="rs-seg" role="tablist" aria-label="Resource type">
        <button v-for="f in FILTERS.filter(x => x.value === 'all' || countOf(x.value))" :key="f.value" type="button" class="rs-seg-btn" :class="{ active: activeType === f.value }" @click="activeType = f.value">
          {{ f.label }}<span v-if="countOf(f.value)" class="rs-seg-count">{{ countOf(f.value) }}</span>
        </button>
      </div>
      <label class="rs-search">
        <Search :size="18" aria-hidden="true" />
        <input v-model="search" type="search" placeholder="Search resources" aria-label="Search resources" />
      </label>
    </div>

    <div v-if="loading" class="rs-grid">
      <div v-for="n in 3" :key="n" class="rs-card skeleton">
        <span class="sk sk-cover" />
        <span class="rs-body"><span class="sk sk-line w80" /><span class="sk sk-line w50" /><span class="sk sk-line w80" style="margin-top: 14px" /></span>
      </div>
    </div>

    <div v-else-if="!resources.length && !error" class="rs-empty">
      <span class="rs-empty-ico"><BookOpen :size="28" aria-hidden="true" /></span>
      <p class="rs-empty-title">No resources shared yet.</p>
      <p class="rs-empty-sub">Your RND usually shares guides after a consultation. They show up here when they do.</p>
    </div>

    <template v-else>
      <div v-if="filtered.length" class="rs-grid">
        <article v-for="r in filtered" :key="r.id" class="rs-card" :style="toneOf(r.type)">
          <!-- cover: the kind of resource, big and clear -->
          <button type="button" class="rs-cover" :aria-label="`Open ${r.title}`" @click="open(r)">
            <span class="rs-type">{{ TYPE_LABELS[r.type] || r.type }}</span>
            <span v-if="isNew(r)" class="rs-new">New</span>
            <span class="rs-ico"><component :is="TYPE_ICONS[r.type] || FileText" :size="30" aria-hidden="true" /></span>
            <span class="rs-cover-hint"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></svg>{{ r.type === 'video' ? 'Watch' : 'Preview' }}</span>
          </button>

          <div class="rs-body">
            <button type="button" class="rs-title" @click="open(r)">{{ r.title }}</button>
            <p v-if="r.description" class="rs-desc">{{ r.description }}</p>
            <p class="rs-meta">
              <span class="rs-by-ico" aria-hidden="true"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4" /><path d="M4 21c1-4 4-6 8-6s7 2 8 6" /></svg></span>
              <span class="rs-meta-txt"><strong>RND {{ r.shared_by?.name }}</strong><small>Shared {{ shortDate(r.shared_at || r.created_at) }}</small></span>
            </p>
          </div>

          <div class="rs-acts">
            <button type="button" class="rs-btn soft" @click="open(r)">
              <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></svg>{{ r.type === 'video' ? 'Watch' : 'View' }}
            </button>
            <a v-if="r.file_path" :href="r.download_url || r.file_path" class="rs-btn dark"><Download :size="16" aria-hidden="true" /> Download</a>
            <a v-else-if="r.url" :href="r.url" target="_blank" rel="noopener noreferrer" class="rs-btn dark"><ExternalLink :size="16" aria-hidden="true" /> Open link</a>
          </div>
        </article>
      </div>
      <div v-else class="rs-empty">
        <span class="rs-empty-ico"><SearchX :size="28" aria-hidden="true" /></span>
        <p class="rs-empty-title">No resources match your search.</p>
      </div>
    </template>

    <!-- preview -->
    <div v-if="current" class="nm-modal-overlay pm-overlay" @click.self="current = null">
      <div class="nm-modal preview-modal" role="dialog" aria-modal="true" :aria-label="current.title">
        <div class="pm-head">
          <span class="pm-ico"><component :is="TYPE_ICONS[current.type] || FileText" :size="20" aria-hidden="true" /></span>
          <div style="flex: 1; min-width: 0">
            <h3 class="pm-title">{{ current.title }}</h3>
            <p class="pm-sub">Shared {{ shortDate(current.shared_at || current.created_at) }} by RND {{ current.shared_by?.name }}</p>
          </div>
          <button class="close-btn" aria-label="Close" @click="current = null"><X :size="20" /></button>
        </div>

        <div class="pm-body">
          <div class="preview">
            <iframe v-if="previewKind === 'pdf'" :src="current.file_path" :title="current.title" class="preview-frame" />
            <video v-else-if="previewKind === 'video'" :src="current.file_path" controls preload="metadata" class="preview-video" />
            <div v-else-if="previewKind === 'link'" class="preview-none">
              <span class="preview-ico"><Link2 :size="24" aria-hidden="true" /></span>
              <p>This resource is a link to another website.</p>
              <p class="preview-url">{{ current.url }}</p>
            </div>
            <div v-else class="preview-none">
              <span class="preview-ico"><FileText :size="24" aria-hidden="true" /></span>
              <p>This file can't be shown here. Download it to open it.</p>
            </div>
          </div>
          <p v-if="current.description" class="pm-desc">{{ current.description }}</p>
        </div>

        <div class="pm-actions">
          <template v-if="current.file_path">
            <a :href="current.file_path" target="_blank" rel="noopener noreferrer" class="rs-btn soft"><ExternalLink :size="15" aria-hidden="true" /> Open in new tab</a>
            <a :href="current.download_url || current.file_path" class="rs-btn dark"><Download :size="15" aria-hidden="true" /> Download</a>
          </template>
          <a v-else-if="current.url" :href="current.url" target="_blank" rel="noopener noreferrer" class="rs-btn dark"><ExternalLink :size="15" aria-hidden="true" /> Open link</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { BookOpen, Download, ExternalLink, FileText, FileType, Link2, PlayCircle, Search, SearchX, X } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Resources' })

const { get } = useApi()

const FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'pdf', label: 'PDF' },
  { value: 'video', label: 'Video' },
  { value: 'article', label: 'Article' },
  { value: 'link', label: 'Link' },
]
const TYPE_ICONS = { pdf: FileText, video: PlayCircle, article: FileType, link: Link2 }
const TYPE_LABELS = { pdf: 'PDF', video: 'Video', article: 'Article', link: 'Link' }
const NEW_DAYS = 7

const loading = ref(true)
const error = ref('')
const resources = ref([])
const search = ref('')
const activeType = ref('all')
const current = ref(null)

async function load({ quiet = false } = {}) {
  if (!quiet) {
    loading.value = true
    error.value = ''
  }
  try {
    resources.value = await get('/client/resources/')
  } catch {
    if (!quiet) error.value = 'Could not load your resources.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
useAutoRefresh(() => load({ quiet: true }))

const countOf = type => (type === 'all' ? resources.value.length : resources.value.filter(r => r.type === type).length)
// Newest shares first.
const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  return resources.value
    .filter(r => (activeType.value === 'all' || r.type === activeType.value)
      && (!q || `${r.title} ${r.description || ''} ${r.shared_by?.name || ''}`.toLowerCase().includes(q)))
    .sort((a, b) => new Date(b.shared_at || b.created_at) - new Date(a.shared_at || a.created_at))
})

function isNew(r) {
  const at = r.shared_at || r.created_at
  return at && Date.now() - new Date(at) < NEW_DAYS * 86400000
}
function open(r) {
  current.value = r
}
// PDF / video play in the page; Word documents can't, so they're downloaded.
const previewKind = computed(() => {
  const r = current.value
  if (!r) return null
  if (r.type === 'link') return 'link'
  const path = (r.file_path || '').toLowerCase().split('?')[0]
  if (r.type === 'video' || /\.(mp4|webm|mov)$/.test(path)) return 'video'
  if (path.endsWith('.pdf') || r.type === 'pdf') return 'pdf'
  return null
})
function onKey(e) {
  if (e.key === 'Escape') current.value = null
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// a colour for each kind of resource
const TYPE_TONES = {
  pdf: { '--c': '#B4384A', '--bg': '#FDECEC' },
  video: { '--c': '#3B5BA5', '--bg': '#EEF1FA' },
  article: { '--c': '#9A7300', '--bg': '#FBF3D2' },
  link: { '--c': '#004D3A', '--bg': '#E3EFE7' },
}
const toneOf = type => TYPE_TONES[type] || TYPE_TONES.link
</script>

<style scoped>
/* =========================================================
   Resources: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.rs-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; gap: 18px; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }
.rs-page .nm-error { display: flex; align-items: center; gap: 12px; margin: 0; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 14px; }

/* ---------- HERO ---------- */
.rs-hero {
  position: relative;
  overflow: hidden;
  padding: 32px 34px;
  border-radius: 24px;
  color: #FFFFFF;
  background:
    radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%),
    linear-gradient(115deg, #035A45 0%, #004D3A 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -24px rgba(0, 77, 58, 0.55);
}
.rs-hero-plate { position: absolute; right: -70px; top: 50%; width: 400px; height: 400px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.55; pointer-events: none; }
.rs-hero-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004D3A 0%, #004D3A 45%, rgba(0, 77, 58, 0.75) 62%, rgba(0, 70, 52, 0.15) 100%); pointer-events: none; }
.rs-hero-text { position: relative; z-index: 1; max-width: 620px; }
.rs-eyebrow { margin: 0; display: flex; align-items: center; gap: 10px; font-size: 12.5px; font-weight: 800; color: #EFBF04; }
.rs-eyebrow span { width: 26px; height: 2px; border-radius: 2px; background: #EFBF04; }
.rs-heading { margin: 10px 0 12px; font-family: 'Playfair Display', Georgia, serif; font-size: 40px; font-weight: 700; line-height: 1.12; color: #FFFFFF; }
.rs-heading em { font-style: italic; color: #EFBF04; }
.rs-page .intro { margin: 0; display: flex; align-items: flex-start; gap: 10px; font-size: 15.0px; line-height: 1.55; color: rgba(255, 255, 255, 0.88); }
.intro svg { flex-shrink: 0; margin-top: 5px; color: #8FD4A8; }

/* ---------- TABS + SEARCH ---------- */
.rs-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.rs-seg { display: inline-flex; gap: 4px; padding: 5px; border-radius: 999px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 6px 16px -12px rgba(16, 35, 27, 0.3); }
.rs-seg-btn { display: inline-flex; align-items: center; gap: 8px; height: 38px; padding: 0 18px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 14px; font-weight: 700; color: #3E5046; white-space: nowrap; cursor: pointer; transition: background-color .15s, color .15s; }
.rs-seg-btn:hover:not(.active) { color: #004D3A; }
.rs-seg-count { min-width: 22px; height: 22px; padding: 0 6px; border-radius: 999px; background: #EEF4F0; color: #004D3A; font-size: 12px; display: inline-flex; align-items: center; justify-content: center; }
.rs-seg-btn.active { background: #004D3A; color: #FFFFFF; }
.rs-seg-btn.active .rs-seg-count { background: rgba(255, 255, 255, 0.18); color: #FFFFFF; }
.rs-seg-btn:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.rs-search { display: flex; align-items: center; gap: 10px; width: 380px; max-width: 100%; height: 48px; padding: 0 18px; border-radius: 999px; background: #FFFFFF; border: 1px solid #E4EBE6; color: #6B7D73; box-shadow: 0 6px 16px -12px rgba(16, 35, 27, 0.3); cursor: text; }
.rs-search:focus-within { border-color: #004D3A; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.rs-search input { flex: 1; min-width: 0; border: none; outline: none; background: transparent; font-family: inherit; font-size: 14px; color: #14261E; }

/* ---------- CARDS ---------- */
.rs-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 18px; align-items: stretch; }
.rs-card {
  --c: #004D3A;
  --bg: #E3EFE7;
  position: relative;
  overflow: hidden;
  min-width: 0;
  display: flex;
  flex-direction: column;
  padding: 10px;
  border-radius: 22px;
  background: #FFFFFF;
  border: 1px solid #E4EBE6;
  box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3);
  transition: box-shadow .2s, transform .2s;
}
.rs-card:not(.skeleton):hover { transform: translateY(-3px); box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 24px 40px -22px rgba(16, 35, 27, 0.4); }

/* cover */
.rs-cover {
  position: relative;
  height: 150px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: none;
  border-radius: 16px;
  background:
    radial-gradient(circle at 85% 20%, rgba(255, 255, 255, 0.7) 0 22%, transparent 23%),
    radial-gradient(circle at 10% 110%, rgba(255, 255, 255, 0.55) 0 30%, transparent 31%),
    var(--bg);
  font-family: inherit;
  cursor: pointer;
}
.rs-cover:focus-visible { outline: 3px solid rgba(239, 191, 4, 0.6); outline-offset: 2px; }
.rs-ico { width: 72px; height: 72px; border-radius: 22px; background: #FFFFFF; color: var(--c); display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 16px 28px -16px rgba(16, 35, 27, 0.45); transition: transform .2s; }
.rs-card:hover .rs-ico { transform: scale(1.05); }
.rs-type,
.rs-new { position: absolute; top: 12px; height: 26px; padding: 0 12px; border-radius: 999px; font-size: 12px; font-weight: 800; display: inline-flex; align-items: center; }
.rs-type { left: 12px; background: #FFFFFF; color: var(--c); }
.rs-new { right: 12px; background: #EFBF04; color: #004D3A; }
.rs-cover-hint { position: absolute; left: 50%; bottom: 12px; display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 12px; border-radius: 999px; background: rgba(255, 255, 255, 0.92); color: #0E3A2C; font-size: 12px; font-weight: 700; opacity: 0; transform: translate(-50%, 6px); transition: opacity .2s, transform .2s; }
.rs-cover:hover .rs-cover-hint,
.rs-cover:focus-visible .rs-cover-hint { opacity: 1; transform: translate(-50%, 0); }

/* body */
.rs-body { flex: 1; display: flex; flex-direction: column; padding: 16px 10px 4px; }
.rs-title { margin: 0; padding: 0; border: none; background: none; text-align: left; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; line-height: 1.25; color: #0E3A2C; cursor: pointer; overflow-wrap: anywhere; }
.rs-title:hover { color: var(--c); }
.rs-title:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; border-radius: 4px; }
.rs-desc { margin: 6px 0 0; font-size: 13.5px; line-height: 1.55; color: #4A5A52; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; overflow-wrap: anywhere; }
.rs-meta { margin: auto 0 0; padding-top: 16px; display: flex; align-items: center; gap: 10px; }
.rs-by-ico { flex-shrink: 0; width: 32px; height: 32px; border-radius: 50%; background: #EEF4F0; color: #1F7A4D; display: inline-flex; align-items: center; justify-content: center; }
.rs-meta-txt { display: flex; flex-direction: column; min-width: 0; line-height: 1.3; }
.rs-meta-txt strong { font-size: 13px; font-weight: 700; color: #22362C; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rs-meta-txt small { font-size: 12px; color: #6B7D73; }
.rs-acts { display: grid; grid-template-columns: 1fr 1.3fr; gap: 8px; margin-top: 14px; padding: 0 0 2px; }
.rs-acts > :only-child { grid-column: 1 / -1; }

/* buttons */
.rs-btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 44px; padding: 0 16px; border-radius: 12px; font-family: inherit; font-size: 14px; font-weight: 700; text-decoration: none; white-space: nowrap; cursor: pointer; transition: background-color .15s; }
.rs-btn.soft { background: #F1F6F2; color: #004D3A; border: 1px solid #DCE8E0; }
.rs-btn.soft:hover { background: #E3EFE7; }
.rs-btn.dark { background: #004D3A; color: #FFFFFF; border: none; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.rs-btn.dark:hover { background: #0A5C46; }
.rs-btn.sm { height: 36px; padding: 0 14px; font-size: 13px; }
.rs-btn:focus-visible { outline: 3px solid rgba(239, 191, 4, 0.6); outline-offset: 2px; }

/* empty */
.rs-empty { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 48px 20px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; text-align: center; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.rs-empty-ico { width: 60px; height: 60px; margin-bottom: 10px; border-radius: 18px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.rs-empty-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 19px; font-weight: 700; color: #0E3A2C; }
.rs-empty-sub { max-width: 420px; margin: 4px 0 0; font-size: 14px; line-height: 1.55; color: #6B7D73; }

/* skeleton */
.skeleton { pointer-events: none; }
.sk { display: block; background: linear-gradient(90deg, #F0F2F0 25%, #E6EAE6 50%, #F0F2F0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 8px; }
.sk-cover { height: 150px; border-radius: 16px; }
.sk-line { height: 12px; margin: 4px 0; }
.w80 { width: 80%; } .w50 { width: 50%; }
@keyframes shimmer { to { background-position: -200% 0; } }

/* ---------- PREVIEW MODAL ---------- */
.pm-overlay { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 24px; background: rgba(4, 30, 21, 0.55); -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px); }
.preview-modal { width: 100%; max-width: 780px; max-height: 92vh; max-height: 92dvh; display: flex; flex-direction: column; overflow: hidden; padding: 0 !important; border-radius: 24px !important; background: #FFFFFF; box-shadow: 0 40px 90px -30px rgba(0, 0, 0, 0.6); font-family: 'DM Sans', Arial, sans-serif; }
.pm-head { display: flex; align-items: center; gap: 14px; padding: 18px 22px; background: #0B5640; color: #FFFFFF; }
.pm-ico { flex-shrink: 0; width: 46px; height: 46px; border-radius: 50%; background: rgba(255, 255, 255, 0.14); color: #EFBF04; display: inline-flex; align-items: center; justify-content: center; }
.pm-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; line-height: 1.25; color: #FFFFFF; overflow-wrap: anywhere; }
.pm-sub { margin: 4px 0 0; font-size: 13px; color: rgba(255, 255, 255, 0.82); }
.close-btn { flex-shrink: 0; width: 40px; height: 40px; border: none; border-radius: 50%; background: transparent; color: #FFFFFF; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.close-btn:hover { background: rgba(255, 255, 255, 0.14); }
.close-btn:focus-visible { outline: 2px solid #EFBF04; outline-offset: 1px; }
.pm-body { flex: 1; min-height: 0; overflow-y: auto; padding: 20px 22px 4px; }
.preview { overflow: hidden; border-radius: 16px; border: 1px solid #E4EBE6; background: #F6FAF7; }
.preview-frame { display: block; width: 100%; height: 60vh; border: 0; background: #FFFFFF; }
.preview-video { display: block; width: 100%; max-height: 60vh; background: #000; }
.preview-none { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 36px 16px; text-align: center; font-size: 14px; color: #3E5046; }
.preview-none p { margin: 0; }
.preview-ico { width: 56px; height: 56px; margin-bottom: 4px; border-radius: 50%; background: #FFFFFF; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px -14px rgba(0, 77, 58, 0.6); }
.preview-url { max-width: 100%; padding: 6px 12px; border-radius: 999px; background: #FFFFFF; border: 1px solid #E4EBE6; color: #1F7A4D; font-size: 13px; font-weight: 600; overflow-wrap: anywhere; }
.pm-desc { margin: 14px 0 0; font-size: 14px; line-height: 1.6; color: #3E5046; white-space: pre-line; overflow-wrap: anywhere; }
.pm-actions { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 22px 20px; }
.pm-actions:empty { display: none; }

/* ---------- SMALLER SCREENS ---------- */
@media (max-width: 960px) {
  .rs-page { gap: 14px; padding-bottom: 96px; }
  .rs-hero { padding: 22px 18px 20px; border-radius: 22px; }
  .rs-hero-plate { width: 170px; height: 170px; right: -50px; top: 18px; transform: none; opacity: .9; }
  .rs-hero-fade { background: linear-gradient(90deg, #004D3A 40%, rgba(0, 77, 58, 0.5) 75%, rgba(0, 77, 58, 0.2)); }
  .rs-hero-text { max-width: 74%; }
  .rs-heading { font-size: 28px; }
  .rs-page .intro { font-size: 13px; }
  .intro svg { display: none; }
  .rs-bar { flex-direction: column; align-items: stretch; gap: 10px; }
  .rs-seg { align-self: flex-start; max-width: 100%; overflow-x: auto; }
  .rs-search { width: 100%; height: 46px; }
  .rs-grid { grid-template-columns: 1fr; gap: 12px; }
  .rs-card { padding: 8px; border-radius: 20px; }
  .rs-cover { height: 120px; border-radius: 14px; }
  .rs-ico { width: 60px; height: 60px; border-radius: 18px; }
  .rs-cover-hint { display: none; }
  .rs-body { padding: 14px 8px 2px; }
  .rs-title { font-size: 18px; }
  .rs-acts { padding: 0; }
}
@media (max-width: 640px) {
  /* the preview opens as a full-screen sheet */
  .pm-overlay { padding: 0; align-items: stretch; }
  .preview-modal { max-width: none; height: 100%; max-height: none; border-radius: 0 !important; }
  .pm-head { padding: 16px; padding-top: calc(16px + env(safe-area-inset-top)); }
  .pm-title { font-size: 19px; }
  .pm-body { display: flex; flex-direction: column; padding: 14px 16px 4px; }
  .preview-frame { height: auto; flex: 1; min-height: 50vh; }
  .pm-actions { padding: 12px 16px calc(14px + env(safe-area-inset-bottom)); box-shadow: 0 -10px 24px -16px rgba(0, 0, 0, 0.3); }
  .pm-actions > * { flex: 1; }
}
</style>