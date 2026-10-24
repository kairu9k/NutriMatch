<template>
  <div class="nm-page">
    <p class="nm-page-sub intro">Guides, videos and links your RND shared with you, to help you follow your plan.</p>
    <p v-if="error" class="nm-error">{{ error }} <button class="nm-btn-soft nm-btn-sm" @click="load">Try again</button></p>

    <div v-if="resources.length" class="nm-toolbar">
      <div class="nm-tabs">
        <button v-for="f in FILTERS.filter(x => x.value === 'all' || countOf(x.value))" :key="f.value" class="nm-tab" :class="{ active: activeType === f.value }" @click="activeType = f.value">
          {{ f.label }}<span v-if="countOf(f.value)" class="nm-count"> {{ countOf(f.value) }}</span>
        </button>
      </div>
      <div class="nm-search">
        <Search :size="15" aria-hidden="true" />
        <input v-model="search" type="search" placeholder="Search resources" aria-label="Search resources" />
      </div>
    </div>

    <div v-if="loading" class="nm-panel shelf">
      <div v-for="n in 3" :key="n" class="row skeleton"><span class="sk sk-icon" /><span class="row-main"><span class="sk sk-line w80" /><span class="sk sk-line w50" /></span></div>
    </div>

    <div v-else-if="!resources.length && !error" class="nm-panel nm-empty">
      <BookOpen :size="28" aria-hidden="true" />
      <p>No resources shared yet.</p>
      <p class="nm-hint" style="margin-top: 4px">Your RND usually shares guides after a consultation. They show up here when they do.</p>
    </div>

    <template v-else>
      <div v-if="filtered.length" class="nm-panel shelf">
        <article v-for="r in filtered" :key="r.id" class="row">
          <span class="type-icon"><component :is="TYPE_ICONS[r.type] || FileText" :size="18" aria-hidden="true" /></span>
          <div class="row-main">
            <p class="row-top">
              <button type="button" class="row-title" @click="open(r)">{{ r.title }}</button>
              <span v-if="isNew(r)" class="nm-pill gold">New</span>
            </p>
            <p v-if="r.description" class="row-desc">{{ r.description }}</p>
            <p class="row-meta">{{ TYPE_LABELS[r.type] || r.type }}, shared {{ shortDate(r.shared_at || r.created_at) }} by RND {{ r.shared_by?.name }}</p>
          </div>
          <div class="row-actions">
            <button type="button" class="nm-btn-soft nm-btn-sm" @click="open(r)">{{ r.type === 'video' ? 'Watch' : 'View' }}</button>
            <a v-if="r.file_path" :href="r.download_url || r.file_path" class="nm-btn-dark nm-btn-sm"><Download :size="14" aria-hidden="true" /> Download</a>
            <a v-else-if="r.url" :href="r.url" target="_blank" rel="noopener noreferrer" class="nm-btn-dark nm-btn-sm"><ExternalLink :size="14" aria-hidden="true" /> Open link</a>
          </div>
        </article>
      </div>
      <div v-else class="nm-panel nm-empty">
        <SearchX :size="28" aria-hidden="true" />
        <p>No resources match your search.</p>
      </div>
    </template>

    <!-- preview -->
    <div v-if="current" class="nm-modal-overlay" @click.self="current = null">
      <div class="nm-modal preview-modal" role="dialog" aria-modal="true" :aria-label="current.title">
        <div class="pm-head nm-modal-head">
          <span class="type-icon"><component :is="TYPE_ICONS[current.type] || FileText" :size="18" aria-hidden="true" /></span>
          <div style="flex: 1; min-width: 0">
            <h3 class="nm-modal-title" style="margin: 0">{{ current.title }}</h3>
            <p class="nm-panel-sub">Shared {{ shortDate(current.shared_at || current.created_at) }} by RND {{ current.shared_by?.name }}</p>
          </div>
          <button class="close-btn" aria-label="Close" @click="current = null"><X :size="18" /></button>
        </div>

        <div class="preview">
          <iframe v-if="previewKind === 'pdf'" :src="current.file_path" :title="current.title" class="preview-frame" />
          <video v-else-if="previewKind === 'video'" :src="current.file_path" controls preload="metadata" class="preview-video" />
          <div v-else-if="previewKind === 'link'" class="preview-none">
            <Link2 :size="22" aria-hidden="true" />
            <p>This resource is a link to another website.</p>
            <p class="preview-url">{{ current.url }}</p>
          </div>
          <div v-else class="preview-none">
            <FileText :size="22" aria-hidden="true" />
            <p>This file can't be shown here. Download it to open it.</p>
          </div>
        </div>
        <p v-if="current.description" class="pm-desc">{{ current.description }}</p>

        <div class="nm-modal-actions">
          <template v-if="current.file_path">
            <a :href="current.file_path" target="_blank" rel="noopener noreferrer" class="nm-btn-soft"><ExternalLink :size="14" aria-hidden="true" /> Open in new tab</a>
            <a :href="current.download_url || current.file_path" class="nm-btn-dark"><Download :size="14" aria-hidden="true" /> Download</a>
          </template>
          <a v-else-if="current.url" :href="current.url" target="_blank" rel="noopener noreferrer" class="nm-btn-dark"><ExternalLink :size="14" aria-hidden="true" /> Open link</a>
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

</script>

<style scoped>
.intro { margin: 0 0 16px; }
.shelf { padding: 0; overflow: hidden; border-color: #d9e3dc; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.row { display: flex; align-items: center; gap: 14px; padding: 16px 20px; border-top: 1px solid #d9e3dc; min-width: 0; }
.row:first-child { border-top: none; }
.type-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #e3efe7; color: #0a4a37; }
.row-main { flex: 1; min-width: 0; overflow-wrap: anywhere; }
.row-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin: 0; }
.row-title {
  border: none; background: none; padding: 0; text-align: left; cursor: pointer; font-family: 'Playfair Display', serif;
  font-size: 1.02rem; font-weight: 700; color: #1a3a1a; line-height: 1.35;
}
.row-title:hover { color: #0a4a37; text-decoration: underline; text-underline-offset: 3px; }
.row-title:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; border-radius: 4px; }
.row-desc { font-size: 0.84rem; color: #4a5a4a; line-height: 1.5; margin: 3px 0 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.row-meta { font-size: 0.78rem; color: #6a7a6a; margin: 4px 0 0; }
.row-actions { display: flex; gap: 8px; flex-shrink: 0; }

.preview-modal { max-width: 760px; }
.pm-head { display: flex; gap: 12px; align-items: flex-start; }
.close-btn { background: none; border: none; color: #6a7a6a; cursor: pointer; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.close-btn:hover { background: #f2f5f2; color: #1a3a1a; }
.close-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.preview { margin-top: 16px; border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; background: #f7f9f7; }
.preview-frame { display: block; width: 100%; height: 60vh; border: 0; background: #fff; }
.preview-video { display: block; width: 100%; max-height: 60vh; background: #000; }
.preview-none { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 30px 16px; color: #4a5a4a; font-size: 0.84rem; text-align: center; }
.preview-none p { margin: 0; }
.preview-url { color: #1f8f5c; overflow-wrap: anywhere; }
.pm-desc { font-size: 0.86rem; color: #4a5a4a; line-height: 1.6; margin: 14px 0 0; white-space: pre-line; overflow-wrap: anywhere; }

.skeleton { pointer-events: none; }
.skeleton .row-main { display: block; }
.sk { display: block; background: linear-gradient(90deg, #f0f2f0 25%, #e6eae6 50%, #f0f2f0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 6px; }
.sk-icon { width: 36px; height: 36px; border-radius: 9px; }
.sk-line { height: 12px; margin: 4px 0; }
.w80 { width: 80%; } .w50 { width: 50%; }
@keyframes shimmer { to { background-position: -200% 0; } }

@media (max-width: 640px) {
  .row { flex-wrap: wrap; align-items: flex-start; padding: 14px 16px; }
  .row-main { flex-basis: calc(100% - 52px); }
  .row-actions { width: 100%; padding-left: 52px; }
  .row-actions > * { flex: 1; justify-content: center; }
  /* the preview opens as a full-screen sheet */
  .preview-modal { max-width: none; height: 100%; max-height: none; border-radius: 0; display: flex; flex-direction: column; }
  .preview-frame { height: auto; flex: 1; min-height: 50vh; }
}
</style>
