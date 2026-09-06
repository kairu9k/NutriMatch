<template>
  <div class="library-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Resources</h1>
        <p class="page-sub">Nutrition education materials shared by your RND.</p>
      </div>
      <div class="search-box">
        <Search :size="16" class="search-icon" />
        <input v-model="search" type="text" placeholder="Search resources..." />
      </div>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div v-if="resources.length" class="filter-chips">
      <button v-for="f in filters" :key="f.value" class="filter-chip" :class="{ active: activeType === f.value }" @click="activeType = f.value">
        <component :is="f.icon" v-if="f.icon" :size="14" /> {{ f.label }}
      </button>
    </div>

    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="resources.length">
      <div v-if="filteredResources.length" class="resource-grid">
        <div v-for="r in filteredResources" :key="r.id" class="resource-card">
          <div class="resource-icon" :class="typeClass(r.type)">
            <component :is="typeIcon(r.type)" :size="20" />
          </div>
          <span class="badge-pill" :class="typeClass(r.type)">{{ typeLabel(r.type) }}</span>
          <h3 class="resource-title">{{ r.title }}</h3>
          <p class="resource-desc">{{ r.description || 'No description provided.' }}</p>
          <div class="resource-footer">
            <span class="resource-date">Added {{ timeAgo(r.created_at) }}</span>
            <a v-if="r.url" :href="r.url" target="_blank" rel="noopener noreferrer" class="open-btn">
              <ExternalLink :size="14" />
            </a>
          </div>
        </div>
      </div>
      <p v-else class="empty-text">No resources match this filter.</p>
    </template>

    <div v-else class="empty-state">
      <div class="empty-icon"><BookOpen :size="28" /></div>
      <p class="empty-title">No resources shared yet</p>
      <p class="empty-desc">Your RND hasn't shared any education materials yet.</p>
    </div>
  </div>
</template>

<script setup>
import { Search, BookOpen, FileText, PlayCircle, FileType, Link2, ExternalLink } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Resources' })

const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const resources = ref([])
const search = ref('')
const activeType = ref('all')

const filters = [
  { value: 'all', label: 'All', icon: null },
  { value: 'pdf', label: 'PDF', icon: FileText },
  { value: 'video', label: 'Video', icon: PlayCircle },
  { value: 'article', label: 'Article', icon: FileType },
  { value: 'link', label: 'Link', icon: Link2 },
]

const TYPE_ICONS = { pdf: FileText, video: PlayCircle, article: FileType, link: Link2 }
const TYPE_LABELS = { pdf: 'PDF', video: 'Video', article: 'Article', link: 'Link' }
const TYPE_CLASSES = { pdf: 'danger', video: 'info', article: 'neutral', link: 'gold' }

function typeIcon(t) { return TYPE_ICONS[t] || FileText }
function typeLabel(t) { return TYPE_LABELS[t] || t }
function typeClass(t) { return TYPE_CLASSES[t] || 'neutral' }

function timeAgo(iso) {
  const seconds = Math.floor((Date.now() - new Date(iso)) / 1000)
  const units = [['year', 31536000], ['month', 2592000], ['day', 86400], ['hour', 3600], ['minute', 60]]
  for (const [label, secs] of units) {
    const value = Math.floor(seconds / secs)
    if (value >= 1) return `${value} ${label}${value > 1 ? 's' : ''} ago`
  }
  return 'just now'
}

const filteredResources = computed(() => {
  return resources.value.filter(r => {
    const matchesType = activeType.value === 'all' || r.type === activeType.value
    const matchesSearch = r.title.toLowerCase().includes(search.value.toLowerCase())
    return matchesType && matchesSearch
  })
})

async function loadResources() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    resources.value = await get('/client/resources/')
  } catch {
    errorMessage.value = 'Could not load resources. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadResources)
</script>

<style scoped>
* { box-sizing: border-box; }

.library-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; flex-wrap: wrap; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.search-box {
  display: flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #e5e8e5;
  border-radius: 8px; padding: 10px 14px; width: 260px; flex-shrink: 0;
}
.search-box input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.filter-chips { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 20px; }
.filter-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 20px; font-size: 0.82rem; font-weight: 600;
  background: #fff; border: 1px solid #eceeec; color: #6a7a6a; cursor: pointer;
}
.filter-chip.active { background: #14301a; color: #fff; border-color: #14301a; }

.resource-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.resource-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px;
  display: flex; flex-direction: column;
}
.resource-icon {
  width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-bottom: 12px;
}
.resource-icon.danger { background: rgba(192,57,43,0.1); color: #c0392b; }
.resource-icon.info { background: rgba(47,111,168,0.1); color: #2f6fa8; }
.resource-icon.gold { background: rgba(212,160,23,0.14); color: #b8860b; }
.resource-icon.neutral { background: #eef3ec; color: #1e4a26; }

.badge-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; width: fit-content; margin-bottom: 10px; }
.badge-pill.danger { background: rgba(192,57,43,0.1); color: #c0392b; }
.badge-pill.info { background: rgba(47,111,168,0.1); color: #2f6fa8; }
.badge-pill.gold { background: rgba(212,160,23,0.14); color: #b8860b; }
.badge-pill.neutral { background: #eef3ec; color: #1e4a26; }

.resource-title { font-family: 'Playfair Display', serif; font-size: 0.95rem; color: #1a3a1a; margin: 0 0 8px; }
.resource-desc { font-size: 0.82rem; color: #8a9a8a; line-height: 1.5; margin: 0; flex-grow: 1; }

.resource-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 14px; }
.resource-date { font-size: 0.74rem; color: #9aaa9a; }
.open-btn {
  width: 30px; height: 30px; border-radius: 6px; border: 1px solid #d5dad5;
  display: flex; align-items: center; justify-content: center; color: #1a3a1a; text-decoration: none;
}

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
.empty-text { font-size: 0.85rem; color: #9aaa9a; padding: 20px; text-align: center; }
</style>
