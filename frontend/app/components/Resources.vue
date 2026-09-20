<template>
  <div class="resources-page">
    <!-- HERO BANNER -->
    <section class="hero-banner">
      <div class="hero-blob"></div>
      <div class="hero-content">
        <h1 class="hero-title"><Library :size="22" class="hero-icon" /> Educational Resource Center</h1>
        <p class="hero-desc">
          Upload handouts, guides, meal plan templates, and clinical references for your patients.
          All files are stored securely under your RND account.
        </p>
      </div>
      <div class="hero-actions">
        <button class="upload-btn" @click="openUploadModal"><Upload :size="15" /> Upload Resource</button>
      </div>
    </section>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <!-- STAT CARDS -->
    <section class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon icon-purple"><Copy :size="17" /></div>
        <div>
          <p class="stat-value">{{ stats.total }}</p>
          <p class="stat-label">Total Resources</p>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon icon-blue"><Upload :size="17" /></div>
        <div>
          <p class="stat-value">{{ stats.myUploads }}</p>
          <p class="stat-label">My Uploads</p>
        </div>
      </div>
      <div class="stat-card">
        <!-- TODO: patient views isn't tracked by the backend yet -->
        <div class="stat-icon icon-red"><Eye :size="17" /></div>
        <div>
          <p class="stat-value">{{ stats.patientViews }}</p>
          <p class="stat-label">Patient Views</p>
        </div>
      </div>
      <div class="stat-card">
        <!-- TODO: download counts aren't tracked by the backend yet -->
        <div class="stat-icon icon-gold"><Download :size="17" /></div>
        <div>
          <p class="stat-value">{{ stats.downloads }}</p>
          <p class="stat-label">Downloads</p>
        </div>
      </div>
    </section>

    <!-- TOOLBAR -->
    <div class="toolbar">
      <div class="search-box-wide">
        <Search :size="16" class="search-icon" />
        <input v-model="search" type="text" placeholder="Search resources..." />
      </div>
      <select v-model="typeFilter" class="filter-select">
        <option value="All Types">All Types</option>
        <option v-for="t in types" :key="t" :value="t">{{ t }}</option>
      </select>
      <div class="view-toggle">
        <button class="view-btn" :class="{ active: view === 'grid' }" @click="view = 'grid'"><LayoutGrid :size="14" /> Grid</button>
        <button class="view-btn" :class="{ active: view === 'list' }" @click="view = 'list'"><List :size="14" /> List</button>
      </div>
    </div>

    <!-- MY UPLOADED RESOURCES -->
    <section class="resource-section">
      <div class="section-header">
        <h3 class="section-title"><Upload :size="15" /> MY UPLOADED RESOURCES</h3>
        <span class="section-count">{{ filteredResources.length }} files</span>
      </div>

      <div v-if="isLoading" class="placeholder-text">Loading…</div>

      <template v-else>
        <div v-if="filteredResources.length" class="resource-grid" :class="{ 'resource-list-view': view === 'list' }">
          <div v-for="r in filteredResources" :key="r.id" class="resource-card">
            <button class="card-remove-btn" :disabled="busyId === r.id" @click="toggleActive(r)"><X :size="14" /></button>
            <div class="resource-icon" :class="'icon-' + r.type.toLowerCase()">
              <component :is="iconFor(r.type)" :size="18" />
            </div>
            <p class="resource-title">{{ r.title }}</p>
            <p class="resource-desc">{{ r.description }}</p>
            <div class="resource-tags">
              <span class="type-pill" :class="'type-' + r.type.toLowerCase()">{{ r.type }}</span>
              <span class="category-pill" :class="r.is_active ? 'status-active' : 'status-inactive'">{{ r.is_active ? 'Active' : 'Inactive' }}</span>
            </div>
            <p class="resource-meta">{{ timeAgo(r.created_at) }}</p>
            <button class="share-btn" @click="shareResource(r)"><Share2 :size="14" /> Share Resource</button>
          </div>
        </div>
        <div v-else class="empty-state">
          <BookOpen :size="28" class="empty-icon" />
          <p class="empty-title">No resources uploaded yet</p>
          <p class="empty-desc">Click "Upload Resource" to share your first guide, video, or article with patients.</p>
        </div>
      </template>
    </section>

    <!-- PINNED CLINICAL REFERENCES -->
    <!-- Static app-level reference content, not tied to a per-RND data source -->
    <section class="resource-section">
      <div class="section-header">
        <h3 class="section-title"><Pin :size="15" /> PINNED CLINICAL REFERENCES</h3>
      </div>
      <div class="resource-grid">
        <div v-for="p in pinnedReferences" :key="p.title" class="resource-card reference-card">
          <div class="resource-icon" :class="'icon-' + p.iconType">
            <component :is="p.icon" :size="18" />
          </div>
          <p class="resource-title">{{ p.title }}</p>
          <p class="resource-desc">{{ p.description }}</p>
          <div class="resource-tags">
            <span class="type-pill" :class="'type-' + p.type.toLowerCase()">{{ p.type }}</span>
            <span class="category-pill">{{ p.tag }}</span>
          </div>
          <button class="share-btn" @click="shareResource(p)"><Share2 :size="14" /> Share Resource</button>
        </div>
      </div>
    </section>

    <!-- PATIENT EDUCATION MATERIALS -->
    <!-- Static app-level reference content, not tied to a per-RND data source -->
    <section class="resource-section">
      <div class="section-header">
        <h3 class="section-title"><GraduationCap :size="15" /> PATIENT EDUCATION MATERIALS</h3>
      </div>
      <div class="resource-grid">
        <div v-for="e in patientEducationMaterials" :key="e.title" class="resource-card reference-card">
          <div class="resource-icon" :class="'icon-' + e.iconType">
            <component :is="e.icon" :size="18" />
          </div>
          <p class="resource-title">{{ e.title }}</p>
          <p class="resource-desc">{{ e.description }}</p>
          <div class="resource-tags">
            <span class="type-pill" :class="'type-' + e.type.toLowerCase()">{{ e.type }}</span>
            <span class="category-pill">{{ e.tag }}</span>
          </div>
          <button class="share-btn" @click="shareResource(e)"><Share2 :size="14" /> Share Resource</button>
        </div>
      </div>
    </section>

    <!-- ================= UPLOAD NEW RESOURCE MODAL ================= -->
    <div v-if="showUploadModal" class="modal-overlay" @click.self="closeUploadModal">
      <div class="modal-box">
        <h2 class="modal-title">Upload New Resource</h2>

        <label class="field-label">Resource Type</label>
        <div class="type-selector">
          <button
            v-for="t in resourceTypeOptions"
            :key="t.value"
            class="type-option"
            :class="{ active: newUpload.type === t.value }"
            @click="newUpload.type = t.value"
          >
            <component :is="t.icon" :size="20" />
            {{ t.label }}
          </button>
        </div>


        <label class="field-label">Title</label>
        <input v-model="newUpload.title" type="text" class="field-input" placeholder="e.g. Understanding Glycemic Index" />

        <label class="field-label">Description <span class="optional">(optional)</span></label>
        <textarea v-model="newUpload.description" class="field-textarea" rows="3" placeholder="Brief summary for your patients..."></textarea>

        <template v-if="newUpload.type === 'Link'">
          <label class="field-label">URL</label>
          <input v-model="newUpload.url" type="url" class="field-input" placeholder="https://..." />
        </template>
        <template v-else>
          <label class="field-label">Upload File</label>
          <label class="dropzone">
            <input type="file" class="dropzone-input" @change="onFileSelected" />
            <UploadCloud :size="26" class="dropzone-icon" />
            <span class="dropzone-text">
              <template v-if="newUpload.fileName">{{ newUpload.fileName }}</template>
              <template v-else>Drag file here or <strong>browse</strong></template>
            </span>
          </label>
        </template>

        <label class="checkbox-row">
          <input type="checkbox" v-model="newUpload.visible" />
          Make visible to patients immediately
        </label>

        <div class="modal-actions">
          <button class="modal-cancel-btn" @click="closeUploadModal">Cancel</button>
          <button
            class="modal-upload-btn"
            :disabled="!canSubmit || isSubmitting"
            @click="submitUpload"
          >{{ isSubmitting ? 'Uploading…' : 'Upload Resource' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  Upload, Search, LayoutGrid, List, Library, Copy, Eye, Download,
  BookOpen, FileText, PlayCircle, FileEdit, Link as LinkIcon, Share2, X, Pin,
  Table2, Calculator, ClipboardList, HeartPulse, GraduationCap, Leaf, Cookie, Link2, ShieldCheck,
  UploadCloud
} from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Resources' })

const { get, post, patch } = useApi()

const isLoading = ref(true)
const isSubmitting = ref(false)
const errorMessage = ref('')
const resources = ref([])
const busyId = ref(null)

const TYPE_LABELS = { article: 'Article', pdf: 'PDF', video: 'Video', link: 'Link' }
function toDisplayType(type) { return TYPE_LABELS[type] || type }
function toApiType(label) { return label.toLowerCase() }

async function loadResources() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const data = await get('/rnd/resources/')
    resources.value = data.map(r => ({ ...r, type: toDisplayType(r.type) }))
  } catch {
    errorMessage.value = 'Could not load your resources. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

/* ---------- STATS ---------- */
// TODO: patientViews and downloads aren't tracked by the backend yet —
// wire these up to real analytics once available.
const stats = computed(() => ({
  total: resources.value.length,
  myUploads: resources.value.length,
  patientViews: 0,
  downloads: 0
}))

/* ---------- TOOLBAR ---------- */
const search = ref('')
const typeFilter = ref('All Types')
const view = ref('grid')

const types = computed(() => [...new Set(resources.value.map(r => r.type).filter(Boolean))])

const filteredResources = computed(() => {
  return resources.value.filter(r => {
    const matchesSearch = r.title.toLowerCase().includes(search.value.toLowerCase())
    const matchesType = typeFilter.value === 'All Types' || r.type === typeFilter.value
    return matchesSearch && matchesType
  })
})

function iconFor(type) {
  if (type === 'PDF') return FileText
  if (type === 'Video') return PlayCircle
  if (type === 'Article') return FileEdit
  if (type === 'Link') return LinkIcon
  return FileText
}

function shareResource(r) {
  // TODO: wire up to a real share flow (link/copy)
  console.log('Share resource', r)
}

async function toggleActive(r) {
  busyId.value = r.id
  try {
    await patch(`/rnd/resources/${r.id}/`, { is_active: !r.is_active })
    r.is_active = !r.is_active
  } catch {
    errorMessage.value = 'Could not update this resource. Please try again.'
  } finally {
    busyId.value = null
  }
}

/* ---------- UPLOAD NEW RESOURCE MODAL ---------- */
const showUploadModal = ref(false)

const resourceTypeOptions = [
  { value: 'PDF', label: 'PDF', icon: FileText },
  { value: 'Video', label: 'Video', icon: PlayCircle },
  { value: 'Article', label: 'Article', icon: FileEdit },
  { value: 'Link', label: 'Link', icon: LinkIcon }
]

const newUpload = ref({ type: 'PDF', title: '', description: '', url: '', file: null, fileName: '', visible: true })

const canSubmit = computed(() => {
  if (!newUpload.value.title.trim()) return false
  return newUpload.value.type === 'Link' ? !!newUpload.value.url.trim() : !!newUpload.value.file
})

function openUploadModal() {
  newUpload.value = { type: 'PDF', title: '', description: '', url: '', file: null, fileName: '', visible: true }
  showUploadModal.value = true
}
function closeUploadModal() {
  showUploadModal.value = false
}
function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  newUpload.value.file = file
  newUpload.value.fileName = file.name
}
async function submitUpload() {
  if (!canSubmit.value) return
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    const isLink = newUpload.value.type === 'Link'
    const form = new FormData()
    form.append('title', newUpload.value.title)
    if (newUpload.value.description) form.append('description', newUpload.value.description)
    form.append('type', toApiType(newUpload.value.type))
    form.append('is_active', String(newUpload.value.visible))
    if (isLink) {
      form.append('url', newUpload.value.url)
    } else {
      form.append('file', newUpload.value.file)
    }
    await post('/rnd/resources/', form)
    showUploadModal.value = false
    await loadResources()
  } catch (error) {
    errorMessage.value = error?.data?.non_field_errors?.[0] || error?.data?.url?.[0] || error?.data?.file?.[0] || 'Could not add this resource. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

function timeAgo(iso) {
  if (!iso) return ''
  const seconds = Math.floor((Date.now() - new Date(iso)) / 1000)
  const units = [['year', 31536000], ['month', 2592000], ['day', 86400], ['hour', 3600], ['minute', 60]]
  for (const [label, secs] of units) {
    const value = Math.floor(seconds / secs)
    if (value >= 1) return `${value} ${label}${value > 1 ? 's' : ''} ago`
  }
  return 'just now'
}

onMounted(loadResources)

/* ---------- PINNED CLINICAL REFERENCES (static, app-level content) ---------- */
const pinnedReferences = ref([
  { title: 'FNRI Food Exchange Lists 4th Ed.', description: 'Philippine-specific food exchange reference for MNT planning.', icon: Table2, iconType: 'article', type: 'PDF', tag: 'Official' },
  { title: 'BMI & IBW Calculator', description: 'Auto-calculate BMI, IBW, and calorie needs using patient data.', icon: Calculator, iconType: 'pdf', type: 'Tool', tag: 'Interactive' },
  { title: 'NCP Documentation Template', description: '4-phase NCP template pre-formatted for RA 10173 compliance.', icon: ClipboardList, iconType: 'video', type: 'DOCX', tag: 'Compliance' },
  { title: 'T2DM MNT Protocol 2024', description: 'Evidence-based MNT protocol for Type 2 Diabetes management.', icon: HeartPulse, iconType: 'link', type: 'PDF', tag: 'Clinical' }
])

const patientEducationMaterials = ref([
  { title: 'Healthy Filipino Eating Guide', description: 'Patient-friendly visual guide to balanced Filipino meals.', icon: Leaf, iconType: 'article', type: 'Handout', tag: 'Patient' },
  { title: 'Low-GI Filipino Foods List', description: 'Glycemic index reference for common Philippine foods.', icon: Cookie, iconType: 'pdf', type: 'PDF', tag: 'Patient' },
  { title: 'DASH Diet for Filipinos', description: 'Localized DASH diet guide using accessible Filipino ingredients.', icon: Link2, iconType: 'link', type: 'PDF', tag: 'Patient' },
  { title: 'CKD Dietary Restrictions', description: 'Potassium, phosphorus, and sodium restriction guide for CKD.', icon: ShieldCheck, iconType: 'video', type: 'PDF', tag: 'Patient' }
])
</script>

<style scoped>
* { box-sizing: border-box; }

.resources-page { font-family: 'Inter', sans-serif; }

/* HERO BANNER */
.hero-banner {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%);
  border-radius: 16px; padding: 28px 32px;
  display: flex; align-items: center; justify-content: space-between; gap: 20px;
  margin-bottom: 45px; color: #fff;
}
.hero-blob { position: absolute; width: 220px; height: 220px; border-radius: 50%; background: rgba(255,255,255,0.05); top: -60px; right: 200px; }
.hero-content { position: relative; z-index: 1; flex: 1; }
.hero-title { display: flex; align-items: center; gap: 10px; font-family: 'Playfair Display', serif; font-size: 1.3rem; margin: 0 0 8px; }
.hero-icon { color: #D4A017; }
.hero-desc { font-size: 0.85rem; color: #cfe0d5; margin: 0; max-width: 560px; line-height: 1.5; }
.hero-actions { position: relative; z-index: 1; display: flex; gap: 10px; flex-shrink: 0; }
.upload-btn {
  display: flex; align-items: center; gap: 6px; background: #D4A017; color: #1a3a1a; border: none;
  border-radius: 8px; padding: 11px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; white-space: nowrap;
}

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 20px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

/* STAT CARDS */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 35px; }
.stat-card { background: #fff; border-radius: 14px; padding: 14px 18px; border: 1px solid #CBD5E1; display: flex; align-items: center; gap: 14px; }
.stat-icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.stat-icon.icon-purple { background: #ece3f7; color: #6a3aa0; }
.stat-icon.icon-blue { background: #e3ecf7; color: #2a5a8a; }
.stat-icon.icon-red { background: #fbe0e0; color: #c0392b; }
.stat-icon.icon-gold { background: #fdf1d6; color: #b8860b; }
.stat-value { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stat-label { font-size: 0.8rem; color: #6a7a6a; margin: 4px 0 0; }

/* TOOLBAR */
.toolbar { display: flex; align-items: center; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }
.search-box-wide {
  width: 100%; max-width: 420px; display: flex; align-items: center; gap: 10px; background: #fff;
 border: 1px solid #CBD5E1; border-radius: 10px; padding: 11px 16px;
}
.search-box-wide input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; color: #4a5a4a; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }
.filter-select { border: 1px solid #CBD5E1; border-radius: 10px; padding: 11px 16px; font-size: 0.85rem; color: #4a5a4a; background: #fff; cursor: pointer; }
.view-toggle { display: flex; border: 1px solid #CBD5E1; border-radius: 8px; overflow: hidden; margin-left: auto; }
.view-btn { display: flex; align-items: center; gap: 5px; border: none; background: #fff; color: #4a5a4a; padding: 10px 14px; font-size: 0.82rem; font-weight: 600; cursor: pointer; }
.view-btn.active { background: #14301a; color: #fff; }

/* SECTIONS */
.resource-section { margin-bottom: 32px; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.section-title { display: flex; align-items: center; gap: 8px; font-size: 0.72rem; letter-spacing: 0.08em; color: #6a7a6a; font-weight: 700; margin: 0; }
.section-count { background: #fdf1d6; color: #b8860b; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }

/* RESOURCE GRID */
.resource-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.resource-list-view { grid-template-columns: 1fr; }
.resource-card {
  position: relative; background: #fff; border-radius: 14px; border: 1.5px solid #eceeec;
  padding: 18px; display: flex; flex-direction: column; gap: 8px;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.resource-card:hover {
  border-color: #1f8f5c;
  box-shadow: 0 4px 14px rgba(31,143,92,0.12);
}
.card-remove-btn {
  position: absolute; top: 12px; right: 12px; background: none; border: none; color: #b0b8b0;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.card-remove-btn:hover { color: #c0392b; }
.card-remove-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.resource-icon { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; margin-bottom: 4px; }
.icon-pdf { background: #fbe1de; color: #c0483a; }
.icon-video { background: #e3edfc; color: #3b6fd6; }
.icon-article { background: #e6f4e6; color: #2e7d32; }
.icon-link { background: #fdf1d6; color: #b8860b; }

.resource-title { font-weight: 700; color: #1f8f5c; font-size: 0.92rem; margin: 0; }
.resource-desc { font-size: 0.8rem; color: #6a7a6a; margin: 0; line-height: 1.45; flex: 1; }

.resource-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.type-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 9px; border-radius: 12px; white-space: nowrap; }
.type-pdf { background: #fbe1de; color: #c0483a; }
.type-video { background: #e3edfc; color: #3b6fd6; }
.type-article { background: #eef0ee; color: #4a5a4a; }
.type-link { background: #fdf1d6; color: #b8860b; }
.type-tool { background: #fdf1d6; color: #b8860b; }
.type-handout { background: #e6f4e6; color: #2e7d32; }
.category-pill { font-size: 0.68rem; font-weight: 700; padding: 3px 9px; border-radius: 12px; background: #f0e9f7; color: #6a3aa0; white-space: nowrap; }
.category-pill.status-active { background: #e6efe0; color: #3a6b3a; }
.category-pill.status-inactive { background: #eceeec; color: #7a8a7a; }

.resource-meta { font-size: 0.72rem; color: #9aaa9a; margin: 2px 0 6px; border-top: 1px solid #f2f4f2; padding-top: 10px; }

.share-btn {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  background: #14301a; color: #fff; border: none; border-radius: 8px;
  padding: 10px; font-size: 0.82rem; font-weight: 700; cursor: pointer;
  margin-top: 4px;
  visibility: hidden; opacity: 0;
  transition: opacity 0.15s ease;
}
.resource-card:hover .share-btn {
  visibility: visible; opacity: 1;
}
.share-btn:hover { background: #0d2312; }

.reference-card { padding-bottom: 18px; }

/* EMPTY STATE */
.empty-state {
  text-align: center; padding: 56px 24px; background: #fff; border-radius: 14px; border: 1px solid #eceeec;
}
.empty-icon { color: #c8d0c8; margin-bottom: 12px; }
.empty-title { font-size: 0.95rem; font-weight: 700; color: #4a5a4a; margin: 0 0 6px; }
.empty-desc { font-size: 0.82rem; color: #9aaa9a; margin: 0; }

@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .resource-grid { grid-template-columns: repeat(2, 1fr); }
  .hero-banner { flex-direction: column; align-items: flex-start; }
}

/* ============ UPLOAD NEW RESOURCE MODAL ============ */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(20,30,20,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100; padding: 20px;
}
.modal-box {
  background: #fff; border-radius: 16px; width: 100%; max-width: 500px;
  max-height: 90vh; overflow-y: auto; padding: 28px;
}
.modal-title { font-family: 'Playfair Display', serif; font-size: 1.3rem; color: #1a3a1a; margin: 0 0 20px; }


.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #2a2a2a; margin: 0 0 8px; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input, .field-textarea {
  width: 100%; border: 1px solid #e5e8e5; border-radius: 8px; padding: 11px 14px;
  font-size: 0.86rem; color: #2a2a2a; background: #fff; font-family: inherit; margin-bottom: 18px;
}
.field-textarea { resize: vertical; }

.type-selector { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 18px; }
.type-option {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  border: 1.5px solid #e5e8e5; background: #fff; color: #6a7a6a; border-radius: 10px;
  padding: 14px 8px; font-size: 0.8rem; font-weight: 600; cursor: pointer;
}
.type-option.active { border-color: #D4A017; color: #1a3a1a; background: #fdf8ee; }

.dropzone {
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  background: #eef3ee; border: 1.5px dashed #b8c8b8; border-radius: 10px;
  padding: 28px 16px; margin-bottom: 18px; cursor: pointer; text-align: center;
}
.dropzone-input { display: none; }
.dropzone-icon { color: #1a5a2a; }
.dropzone-text { font-size: 0.85rem; color: #4a5a4a; }
.dropzone-text strong { color: #1a5a2a; text-decoration: underline; }

.checkbox-row { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: #3a4a3a; margin-bottom: 22px; cursor: pointer; }
.checkbox-row input { width: 16px; height: 16px; accent-color: #14301a; cursor: pointer; }

.modal-actions { display: flex; align-items: center; justify-content: flex-end; gap: 12px; }
.modal-cancel-btn { background: none; border: none; color: #4a5a4a; font-size: 0.85rem; font-weight: 600; cursor: pointer; padding: 11px 16px; }
.modal-upload-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 11px 24px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}
.modal-upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
