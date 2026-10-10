<template>
  <div class="nm-page">
    <p class="nm-page-sub intro">Guides, videos and links your RND shared with you, to help you follow your plan.</p>
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-panel-link" @click="load">Try again</button></p>

    <div v-if="resources.length" class="nm-toolbar">
      <div class="nm-tabs">
        <button v-for="f in FILTERS" :key="f.value" class="nm-tab" :class="{ active: activeType === f.value }" @click="activeType = f.value">
          {{ f.label }}<span v-if="countOf(f.value)" class="nm-count"> {{ countOf(f.value) }}</span>
        </button>
      </div>
      <div class="nm-search">
        <Search :size="15" />
        <input v-model="search" type="search" placeholder="Search resources" />
      </div>
    </div>

    <div v-if="loading" class="library-grid">
      <div v-for="n in 3" :key="n" class="nm-panel card skeleton"><span class="sk sk-icon" /><span class="sk sk-line w80" /><span class="sk sk-line w50" /></div>
    </div>

    <div v-else-if="!resources.length && !error" class="nm-panel nm-empty">
      <BookOpen :size="28" />
      <p>No resources shared yet.</p>
      <p class="nm-hint" style="margin-top: 4px">Your RND usually shares guides and materials after your consultation. They'll appear here.</p>
    </div>

    <template v-else>
      <div v-if="filtered.length" class="library-grid">
        <button v-for="r in filtered" :key="r.id" type="button" class="nm-panel card" @click="open(r)">
          <span class="card-top">
            <span class="type-icon" :class="'t-' + r.type"><component :is="TYPE_ICONS[r.type] || FileText" :size="18" /></span>
            <span class="nm-pill muted">{{ TYPE_LABELS[r.type] || r.type }}</span>
            <span v-if="isNew(r)" class="nm-pill gold new">New</span>
          </span>
          <span class="card-title">{{ r.title }}</span>
          <span v-if="r.description" class="card-desc">{{ r.description }}</span>
          <span class="card-from">
            <img v-if="r.shared_by?.profile_photo" :src="r.shared_by.profile_photo" class="mini-avatar" alt="" />
            <span v-else class="mini-avatar">{{ nameInitials(r.shared_by?.name) }}</span>
            <span>From RND {{ r.shared_by?.name }} · shared {{ shortDate(r.shared_at || r.created_at) }}</span>
          </span>
        </button>
      </div>
      <div v-else class="nm-panel nm-empty">
        <SearchX :size="28" />
        <p>No resources match.</p>
      </div>
    </template>

    <!-- preview -->
    <div v-if="current" class="nm-modal-overlay" @click.self="current = null">
      <div class="nm-modal preview-modal" role="dialog" aria-modal="true" :aria-label="current.title">
        <div class="pm-head">
          <span class="type-icon" :class="'t-' + current.type"><component :is="TYPE_ICONS[current.type] || FileText" :size="18" /></span>
          <div style="flex: 1; min-width: 0">
            <h3 class="nm-modal-title" style="margin: 0">{{ current.title }}</h3>
            <p class="nm-panel-sub">From RND {{ current.shared_by?.name }} · shared {{ shortDate(current.shared_at || current.created_at) }}</p>
          </div>
          <button class="close-btn" aria-label="Close" @click="current = null"><X :size="18" /></button>
        </div>

        <div class="preview">
          <iframe v-if="previewKind === 'pdf'" :src="current.file_path" :title="current.title" class="preview-frame" />
          <video v-else-if="previewKind === 'video'" :src="current.file_path" controls preload="metadata" class="preview-video" />
          <div v-else-if="previewKind === 'link'" class="preview-none">
            <Link2 :size="22" />
            <p>This resource is a link to another website.</p>
            <p class="preview-url">{{ current.url }}</p>
          </div>
          <div v-else class="preview-none">
            <FileText :size="22" />
            <p>This file can't be previewed here — download it to open it.</p>
          </div>
        </div>
        <p v-if="current.description" class="pm-desc">{{ current.description }}</p>

        <div class="nm-modal-actions">
          <template v-if="current.file_path">
            <a :href="current.file_path" target="_blank" rel="noopener noreferrer" class="nm-btn-outline"><ExternalLink :size="14" /> Open in new tab</a>
            <a :href="current.download_url || current.file_path" class="nm-btn-dark"><Download :size="14" /> Download</a>
          </template>
          <a v-else-if="current.url" :href="current.url" target="_blank" rel="noopener noreferrer" class="nm-btn-dark"><ExternalLink :size="14" /> Open link</a>
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

async function load() {
  loading.value = true
  error.value = ''
  try {
    resources.value = await get('/client/resources/')
  } catch {
    error.value = 'Could not load your resources.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

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

function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}
</script>

<style scoped>
.intro { margin: 0 0 16px; }
.library-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.card { display: flex; flex-direction: column; gap: 10px; text-align: left; cursor: pointer; font-family: inherit; color: inherit; min-width: 0; overflow-wrap: anywhere; }
.card:hover { border-color: #c7d6ca; box-shadow: 0 4px 14px rgba(31, 143, 92, 0.08); }
.card-top { display: flex; align-items: center; gap: 8px; }
.new { margin-left: auto; }
.card-title { font-family: 'Playfair Display', serif; font-size: 1.02rem; font-weight: 700; color: #1a3a1a; line-height: 1.35; }
.card-desc { font-size: 0.82rem; color: #6a7a6a; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-from { display: flex; align-items: center; gap: 8px; font-size: 0.75rem; color: #8a9a8a; margin-top: auto; padding-top: 10px; border-top: 1px solid #f0f2f0; }
.type-icon { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #eef3ec; color: #1e4a26; }
.type-icon.t-pdf { background: #fdecec; color: #a13a2f; }
.type-icon.t-video { background: #e3edf7; color: #2f6fa8; }
.type-icon.t-link { background: #fdf1d6; color: #b8860b; }
.mini-avatar { width: 22px; height: 22px; border-radius: 50%; background: #00382a; color: #fff; display: inline-flex; align-items: center; justify-content: center; font-size: 0.6rem; font-weight: 700; object-fit: cover; flex-shrink: 0; }

.preview-modal { max-width: 760px; }
.pm-head { display: flex; gap: 12px; align-items: flex-start; }
.close-btn { background: none; border: none; color: #8a9a8a; cursor: pointer; padding: 4px; }
.preview { margin-top: 16px; border: 1px solid #eceeec; border-radius: 12px; overflow: hidden; background: #f7f9f7; }
.preview-frame { display: block; width: 100%; height: 60vh; border: 0; background: #fff; }
.preview-video { display: block; width: 100%; max-height: 60vh; background: #000; }
.preview-none { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 30px 16px; color: #8a9a8a; font-size: 0.84rem; text-align: center; }
.preview-none p { margin: 0; }
.preview-url { color: #1f8f5c; overflow-wrap: anywhere; }
.pm-desc { font-size: 0.86rem; color: #4a5a4a; line-height: 1.6; margin: 14px 0 0; white-space: pre-line; overflow-wrap: anywhere; }

.skeleton { pointer-events: none; }
.sk { display: block; background: linear-gradient(90deg, #f0f2f0 25%, #e6eae6 50%, #f0f2f0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 6px; }
.sk-icon { width: 36px; height: 36px; border-radius: 9px; }
.sk-line { height: 12px; margin: 4px 0; }
.w80 { width: 80%; } .w50 { width: 50%; }
@keyframes shimmer { to { background-position: -200% 0; } }

@media (max-width: 1100px) {
  .library-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 640px) {
  .library-grid { grid-template-columns: minmax(0, 1fr); }
  /* the preview opens as a full-screen sheet */
  .preview-modal { max-width: none; height: 100%; max-height: none; border-radius: 0; display: flex; flex-direction: column; }
  .preview-frame { height: auto; flex: 1; min-height: 50vh; }
}
</style>
