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

    <!-- STAT CARDS — real numbers only -->
    <section class="nm-stat-grid">
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><Library :size="17" /></div>
        <p class="nm-stat-value">{{ stats.total }}</p>
        <p class="nm-stat-label">My resources</p>
        <p class="nm-stat-note">{{ stats.active }} active</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon"><Share2 :size="17" /></div>
        <p class="nm-stat-value">{{ stats.shared }}</p>
        <p class="nm-stat-label">Shared with clients</p>
        <p class="nm-stat-note">Resources at least one client can see</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon gold"><Users :size="17" /></div>
        <p class="nm-stat-value">{{ stats.shares }}</p>
        <p class="nm-stat-label">Client shares</p>
        <p class="nm-stat-note">Total across all resources</p>
      </div>
      <div class="nm-stat-card">
        <div class="nm-stat-icon gold"><EyeOff :size="17" /></div>
        <p class="nm-stat-value">{{ stats.notShared }}</p>
        <p class="nm-stat-label">Not shared yet</p>
        <p class="nm-stat-note" :class="{ warn: stats.notShared }">{{ stats.notShared ? 'Choose clients in the panel' : 'Everything is shared' }}</p>
      </div>
    </section>

    <!-- TOOLBAR -->
    <div class="nm-toolbar">
      <div class="nm-tabs">
        <button v-for="t in TABS" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" @click="tab = t.key">
          {{ t.label }} <span class="nm-count">{{ countOf(t.key) }}</span>
        </button>
      </div>
      <div class="nm-search">
        <Search :size="15" />
        <input v-model="search" type="search" placeholder="Search your resources" />
      </div>
    </div>

    <div v-if="isLoading" class="nm-panel"><p class="nm-muted">Loading your resources…</p></div>

    <div v-else-if="!resources.length" class="nm-panel nm-empty">
      <BookOpen :size="28" />
      <p>No resources uploaded yet.</p>
      <p class="nm-hint" style="margin-top: 4px">Upload a guide, video or link, then choose which clients receive it.</p>
      <button class="nm-btn-gold" style="margin-top: 14px" @click="openUploadModal"><Upload :size="15" /> Upload resource</button>
    </div>

    <div v-else class="review-layout">
      <!-- list -->
      <div class="nm-panel queue">
        <p v-if="!filteredResources.length" class="nm-muted" style="padding: 10px">Nothing here.</p>
        <button v-for="r in filteredResources" :key="r.id" class="queue-item" :class="{ active: selected?.id === r.id }" @click="select(r.id)">
          <span class="type-icon" :class="'t-' + r.type.toLowerCase()"><component :is="iconFor(r.type)" :size="17" /></span>
          <span class="queue-main">
            <span class="queue-name">{{ r.title }}</span>
            <span class="queue-sub">{{ r.type }} · {{ shortDate(r.created_at) }}</span>
          </span>
          <span class="queue-end">
            <span v-if="!r.is_active" class="nm-pill muted">Hidden</span>
            <span v-else-if="r.shared_count" class="nm-pill green">{{ r.shared_count }} client{{ r.shared_count === 1 ? '' : 's' }}</span>
            <span v-else class="nm-pill gold">Not shared</span>
          </span>
          <ChevronRight :size="16" class="queue-chevron" />
        </button>
      </div>

      <!-- panel (a full-screen sheet on phones) -->
      <div v-if="selected" ref="panelWrap" class="panel-wrap">
        <div class="nm-panel detail">
          <button class="back-btn" @click="selectedId = null"><ArrowLeft :size="15" /> All resources</button>

          <div class="detail-head">
            <span class="type-icon lg" :class="'t-' + selected.type.toLowerCase()"><component :is="iconFor(selected.type)" :size="20" /></span>
            <div style="flex: 1; min-width: 0">
              <h2 class="nm-panel-title detail-title">{{ selected.title }}</h2>
              <p class="nm-panel-sub">{{ selected.type }} · Uploaded {{ shortDate(selected.created_at) }}</p>
            </div>
            <span v-if="!selected.is_active" class="nm-pill muted">Hidden from clients</span>
          </div>

          <!-- preview -->
          <div class="preview">
            <iframe v-if="previewKind === 'pdf'" :src="selected.file_path" :title="selected.title" class="preview-frame" />
            <video v-else-if="previewKind === 'video'" :src="selected.file_path" controls preload="metadata" class="preview-video" />
            <a v-else-if="previewKind === 'link'" :href="selected.url" target="_blank" rel="noopener" class="preview-link">
              <LinkIcon :size="18" />
              <span><strong>Open link</strong><span class="preview-url">{{ selected.url }}</span></span>
              <ExternalLink :size="15" />
            </a>
            <div v-else class="preview-none">
              <FileText :size="22" />
              <p>This file type can't be previewed here.</p>
            </div>
          </div>
          <div v-if="selected.file_path" class="preview-actions">
            <a :href="selected.file_path" target="_blank" rel="noopener" class="nm-panel-link"><ExternalLink :size="13" /> Open in new tab</a>
            <a v-if="selected.download_url" :href="selected.download_url" class="nm-panel-link"><Download :size="13" /> Download</a>
          </div>

          <p v-if="selected.description" class="detail-desc">{{ selected.description }}</p>

          <!-- sharing -->
          <div class="share-box">
            <div class="share-head">
              <p class="share-title">Shared with</p>
              <button v-if="shareRows.length > 1" class="nm-panel-link" @click="toggleAllClients">{{ allSelected ? 'Clear all' : 'Select all' }}</button>
            </div>
            <p v-if="!selected.is_active" class="nm-note" style="margin: 0 0 10px">It's hidden, so clients can't see it even if it's shared. Show it again to give them access.</p>
            <p v-if="shareLoading" class="nm-muted">Loading your clients…</p>
            <p v-else-if="shareError" class="nm-error">{{ shareError }}</p>
            <p v-else-if="!shareRows.length" class="nm-muted">You don't have any active clients yet — once an appointment is confirmed you can share resources with them.</p>
            <div v-else class="client-grid">
              <label v-for="row in shareRows" :key="row.relationship_id" class="client-check" :class="{ on: chosen.includes(row.relationship_id) }">
                <input v-model="chosen" type="checkbox" :value="row.relationship_id" />
                <img v-if="row.client.profile_photo" :src="row.client.profile_photo" class="mini-avatar" alt="" />
                <span v-else class="mini-avatar">{{ nameInitials(row.client.full_name) }}</span>
                <span class="client-name">{{ row.client.full_name }}</span>
              </label>
            </div>
            <div v-if="shareRows.length" class="share-foot">
              <span class="nm-hint" style="margin: 0">{{ shareSummary }}</span>
              <button class="nm-btn-dark nm-btn-sm" :disabled="!shareChanged || shareSaving" @click="saveSharing">
                {{ shareSaving ? 'Saving…' : 'Save sharing' }}
              </button>
            </div>
          </div>

          <div class="detail-actions">
            <button v-if="selected.is_active" class="nm-btn-outline" :disabled="busyId === selected.id" @click="toggleActive(selected)">
              <EyeOff :size="14" /> Hide from clients
            </button>
            <button v-else class="nm-btn-dark" :disabled="busyId === selected.id" @click="toggleActive(selected)">
              <Eye :size="14" /> Show to clients again
            </button>
          </div>
        </div>
      </div>
      <div v-else class="nm-panel panel-placeholder">
        <BookOpen :size="28" />
        <p>Select a resource to preview and share it.</p>
      </div>
    </div>

    <!-- YOUR TOOLS — links to the app's own clinical tools -->
    <section class="resource-section">
      <div class="section-header">
        <h3 class="section-title">Your tools</h3>
      </div>
      <div class="tools-grid">
        <NuxtLink v-for="t in TOOLS" :key="t.to" :to="t.to" class="nm-panel tool-card">
          <span class="nm-stat-icon" :class="t.gold ? 'gold' : ''"><component :is="t.icon" :size="17" /></span>
          <span class="tool-main">
            <span class="tool-title">{{ t.title }}</span>
            <span class="tool-desc">{{ t.desc }}</span>
          </span>
          <ChevronRight :size="16" class="tool-arrow" />
        </NuxtLink>
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
            <input type="file" class="dropzone-input" :accept="fileRule.accept" @change="onFileSelected" />
            <UploadCloud :size="26" class="dropzone-icon" />
            <span class="dropzone-text">
              <template v-if="newUpload.fileName">{{ newUpload.fileName }}</template>
              <template v-else>Drag file here or <strong>browse</strong></template>
            </span>
            <span class="dropzone-hint">{{ fileRule.hint }}</span>
          </label>
        </template>

        <p v-if="uploadError" class="form-error">{{ uploadError }}</p>

        <p class="upload-note">Uploading doesn't send it to anyone yet — after it uploads, tick the clients who should receive it.</p>

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

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import {
  Upload, Search, Library, Eye, ArrowLeft, Download, ExternalLink,
  BookOpen, FileText, PlayCircle, FileEdit, Link as LinkIcon, Share2,
  Table2, ClipboardList, HeartPulse, Leaf,
  UploadCloud, CheckCircle2, EyeOff, Users, ChevronRight
} from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Resources' })

const { get, post, patch, del } = useApi()

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
// Only what the app actually records (views/downloads aren't tracked).
const stats = computed(() => {
  const list = resources.value
  return {
    total: list.length,
    active: list.filter(r => r.is_active).length,
    shared: list.filter(r => r.shared_count).length,
    shares: list.reduce((n, r) => n + (r.shared_count || 0), 0),
    notShared: list.filter(r => !r.shared_count).length,
  }
})

/* ---------- LIST + PANEL ---------- */
const TABS = [
  { key: 'all', label: 'All' },
  { key: 'shared', label: 'Shared' },
  { key: 'not_shared', label: 'Not shared' },
  { key: 'hidden', label: 'Hidden' },
]
const tab = ref('all')
const search = ref('')
function inTab(r, key) {
  if (key === 'shared') return r.is_active && r.shared_count > 0
  if (key === 'not_shared') return r.is_active && !r.shared_count
  if (key === 'hidden') return !r.is_active
  return true
}
const countOf = key => resources.value.filter(r => inTab(r, key)).length
const filteredResources = computed(() => {
  const q = search.value.trim().toLowerCase()
  return resources.value.filter(r => inTab(r, tab.value)
    && (!q || `${r.title} ${r.description || ''}`.toLowerCase().includes(q)))
})

function iconFor(type) {
  if (type === 'PDF') return FileText
  if (type === 'Video') return PlayCircle
  if (type === 'Article') return FileEdit
  if (type === 'Link') return LinkIcon
  return FileText
}

const selectedId = ref(null)
const selected = computed(() => resources.value.find(r => r.id === selectedId.value) || null)
const panelWrap = ref(null)
const isWide = () => import.meta.client && window.matchMedia('(min-width: 1000px)').matches
function select(id) {
  selectedId.value = id
  nextTick(() => { if (panelWrap.value) panelWrap.value.scrollTop = 0 })
}
// On desktop a resource is always open while the list has any.
watch(filteredResources, (list) => {
  if (selectedId.value && !list.some(r => r.id === selectedId.value)) selectedId.value = null
  if (!selectedId.value && isWide() && list.length) select(list[0].id)
})

// PDF / video play in the page; Word documents can't, so they get a link.
const previewKind = computed(() => {
  const r = selected.value
  if (!r) return null
  if (r.type === 'Link') return r.url ? 'link' : null
  const path = (r.file_path || '').toLowerCase().split('?')[0]
  if (r.type === 'Video' || /\.(mp4|webm|mov)$/.test(path)) return 'video'
  if (path.endsWith('.pdf') || r.type === 'PDF') return 'pdf'
  return null
})

/* sharing — same API as before: GET who's shared, POST to add, DELETE to remove */
const shareRows = ref([])
const chosen = ref([])
const shareLoading = ref(false)
const shareSaving = ref(false)
const shareError = ref('')
const originallyShared = computed(() => shareRows.value.filter(r => r.shared).map(r => r.relationship_id))
const toAdd = computed(() => chosen.value.filter(id => !originallyShared.value.includes(id)))
const toRemove = computed(() => originallyShared.value.filter(id => !chosen.value.includes(id)))
const shareChanged = computed(() => toAdd.value.length > 0 || toRemove.value.length > 0)
const allSelected = computed(() => shareRows.value.length > 0 && shareRows.value.every(r => chosen.value.includes(r.relationship_id)))
const shareSummary = computed(() => {
  const parts = [chosen.value.length ? `${chosen.value.length} selected` : 'Nobody selected']
  if (toAdd.value.length) parts.push(`${toAdd.value.length} will be notified`)
  if (toRemove.value.length) parts.push(`${toRemove.value.length} will lose access`)
  return parts.join(' · ')
})
function toggleAllClients() {
  chosen.value = allSelected.value ? [] : shareRows.value.map(r => r.relationship_id)
}
async function loadSharing(id) {
  shareLoading.value = true
  shareError.value = ''
  shareRows.value = []
  chosen.value = []
  try {
    const rows = await get(`/rnd/resources/${id}/share/`)
    if (selectedId.value !== id) return
    shareRows.value = rows
    chosen.value = rows.filter(r => r.shared).map(r => r.relationship_id)
  } catch {
    shareError.value = 'Could not load your clients. Please try again.'
  } finally {
    shareLoading.value = false
  }
}
watch(selectedId, (id) => { if (id) loadSharing(id) })

async function saveSharing() {
  const r = selected.value
  shareSaving.value = true
  shareError.value = ''
  const added = toAdd.value.length
  const removed = toRemove.value.length
  try {
    if (added) await post(`/rnd/resources/${r.id}/share/`, { relationship_ids: toAdd.value })
    for (const id of toRemove.value) await del(`/rnd/resources/${r.id}/share/${id}/`)
    r.shared_count = chosen.value.length
    await loadSharing(r.id)
    const parts = []
    if (added) parts.push(`Shared with ${added} client${added > 1 ? 's' : ''} — they were notified`)
    if (removed) parts.push(`removed from ${removed}`)
    showToast(parts.join(', ') + '.')
  } catch (e) {
    shareError.value = e?.data?.relationship_ids?.[0] || e?.data?.detail || 'Could not update sharing. Please try again.'
  } finally {
    shareSaving.value = false
  }
}

const toast = ref('')
let toastTimer = null
function showToast(text) {
  toast.value = text
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 3500)
}

async function toggleActive(r) {
  busyId.value = r.id
  try {
    await patch(`/rnd/resources/${r.id}/`, { is_active: !r.is_active })
    r.is_active = !r.is_active
    showToast(r.is_active ? 'Clients you shared it with can see it again.' : 'Hidden — clients can no longer see it.')
  } catch {
    errorMessage.value = 'Could not update this resource. Please try again.'
  } finally {
    busyId.value = null
  }
}

function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}

/* ---------- UPLOAD NEW RESOURCE MODAL ---------- */
const showUploadModal = ref(false)

const resourceTypeOptions = [
  { value: 'PDF', label: 'PDF', icon: FileText },
  { value: 'Video', label: 'Video', icon: PlayCircle },
  { value: 'Article', label: 'Article', icon: FileEdit },
  { value: 'Link', label: 'Link', icon: LinkIcon }
]

const newUpload = ref({ type: 'PDF', title: '', description: '', url: '', file: null, fileName: '' })

const canSubmit = computed(() => {
  if (!newUpload.value.title.trim()) return false
  return newUpload.value.type === 'Link' ? !!newUpload.value.url.trim() : !!newUpload.value.file
})

// Same lists/limits as RESOURCE_FILE_RULES in communication/serializers.py
// (the API enforces them; this keeps the picker and the message in step).
const FILE_RULES = {
  PDF: { exts: ['.pdf'], maxMb: 10 },
  Article: { exts: ['.pdf', '.doc', '.docx'], maxMb: 10 },
  Video: { exts: ['.mp4', '.webm', '.mov'], maxMb: 100 },
}
const fileRule = computed(() => {
  const rule = FILE_RULES[newUpload.value.type] || FILE_RULES.PDF
  return { ...rule, accept: rule.exts.join(','), hint: `${rule.exts.join(', ')} · up to ${rule.maxMb} MB` }
})
const uploadError = ref('')

function openUploadModal() {
  newUpload.value = { type: 'PDF', title: '', description: '', url: '', file: null, fileName: '' }
  uploadError.value = ''
  showUploadModal.value = true
}
function closeUploadModal() {
  showUploadModal.value = false
}
function onFileSelected(e) {
  const file = e.target.files?.[0]
  if (!file) return
  uploadError.value = ''
  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  const rule = fileRule.value
  if (!rule.exts.includes(ext)) {
    uploadError.value = `This file type isn't allowed for a ${newUpload.value.type} resource. Use ${rule.exts.join(', ')}.`
  } else if (file.size > rule.maxMb * 1024 * 1024) {
    uploadError.value = `The file is too large. The limit is ${rule.maxMb} MB.`
  }
  if (uploadError.value) {
    e.target.value = ''
    newUpload.value.file = null
    newUpload.value.fileName = ''
    return
  }
  newUpload.value.file = file
  newUpload.value.fileName = file.name
}
// A file picked for one type may not fit another — pick again after switching.
watch(() => newUpload.value.type, () => {
  newUpload.value.file = null
  newUpload.value.fileName = ''
  uploadError.value = ''
})
async function submitUpload() {
  if (!canSubmit.value) return
  isSubmitting.value = true
  errorMessage.value = ''
  uploadError.value = ''
  try {
    const isLink = newUpload.value.type === 'Link'
    const form = new FormData()
    form.append('title', newUpload.value.title)
    if (newUpload.value.description) form.append('description', newUpload.value.description)
    form.append('type', toApiType(newUpload.value.type))
    if (isLink) {
      form.append('url', newUpload.value.url)
    } else {
      form.append('file', newUpload.value.file)
    }
    const created = await post('/rnd/resources/', form)
    showUploadModal.value = false
    tab.value = 'all'
    await loadResources()
    if (created?.id) select(created.id)
    showToast('Uploaded — now tick the clients who should receive it.')
  } catch (error) {
    uploadError.value = error?.data?.non_field_errors?.[0] || error?.data?.url?.[0] || error?.data?.file?.[0] || error?.data?.title?.[0] || 'Could not add this resource. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}


onMounted(loadResources)


/* ---------- YOUR TOOLS ---------- */
const TOOLS = [
  { title: 'Food Exchange Search', desc: 'FNRI Food Exchange Lists — exchanges, portions and macros.', to: '/food-exchange-search', icon: Table2 },
  { title: 'Meal Planning', desc: 'Build and send weekly meal plans to your patients.', to: '/meal-planning', icon: Leaf, gold: true },
  { title: 'NCP Records', desc: 'Assessment, diagnosis, intervention and monitoring notes.', to: '/ncp-records', icon: ClipboardList },
  { title: 'My Patients', desc: 'Screenings, progress and plans for each patient.', to: '/my-patients', icon: HeartPulse, gold: true },
]
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

/* SECTIONS */
.resource-section { margin: 28px 0 0; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.section-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; font-weight: 700; margin: 0; }
.tools-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.tool-card { display: flex; align-items: center; gap: 14px; text-decoration: none; padding: 16px 18px; }
.tool-card:hover { border-color: #c7d6ca; background: #fafbfa; }
.tool-card .nm-stat-icon { margin: 0; flex-shrink: 0; }
.tool-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.tool-title { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; }
.tool-desc { font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; }
.tool-arrow { color: #b0bab0; flex-shrink: 0; }

/* type icon colors (shared by list + panel) */
.type-icon { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #eef3ec; color: #1e4a26; }
.type-icon.lg { width: 46px; height: 46px; border-radius: 11px; }
.type-icon.t-pdf { background: #fdecec; color: #a13a2f; }
.type-icon.t-video { background: #e3edf7; color: #2f6fa8; }
.type-icon.t-link { background: #fdf1d6; color: #b8860b; }

/* LIST + PANEL (same layout as RND Applications) */
.review-layout { display: grid; grid-template-columns: minmax(280px, 360px) minmax(0, 1fr); gap: 20px; align-items: start; }
.queue { padding: 10px; position: sticky; top: 84px; max-height: calc(100vh - 140px); overflow-y: auto; }
.queue-item { display: flex; align-items: center; gap: 10px; width: 100%; text-align: left; background: none; border: 1px solid transparent; border-radius: 10px; padding: 10px; cursor: pointer; font-family: inherit; color: inherit; }
.queue-item + .queue-item { margin-top: 2px; }
.queue-item:hover { background: #f7f9f7; }
.queue-item.active { background: #eef3ec; border-color: #d3e2d6; }
.queue-main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.queue-name { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.queue-sub { font-size: 0.74rem; color: #8a9a8a; }
.queue-end { flex-shrink: 0; }
.queue-chevron { color: #c5d0c5; flex-shrink: 0; display: none; }

.detail { min-width: 0; }
.detail-head { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.detail-title { font-size: 1.2rem; overflow-wrap: anywhere; }
.back-btn { display: none; align-items: center; gap: 6px; background: none; border: none; color: #1f8f5c; font-weight: 600; font-size: 0.84rem; padding: 0; margin-bottom: 14px; cursor: pointer; font-family: inherit; }
.preview { margin-top: 16px; border: 1px solid #eceeec; border-radius: 12px; overflow: hidden; background: #f7f9f7; }
.preview-frame { display: block; width: 100%; height: 420px; border: 0; background: #fff; }
.preview-video { display: block; width: 100%; max-height: 420px; background: #000; }
.preview-link { display: flex; align-items: center; gap: 12px; padding: 18px; text-decoration: none; color: #1a3a1a; }
.preview-link > span { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; font-size: 0.88rem; }
.preview-url { font-size: 0.78rem; color: #1f8f5c; overflow-wrap: anywhere; }
.preview-none { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 30px 16px; color: #8a9a8a; font-size: 0.84rem; }
.preview-none p { margin: 0; }
.preview-actions { display: flex; gap: 16px; flex-wrap: wrap; margin-top: 10px; }
.preview-actions .nm-panel-link { display: inline-flex; align-items: center; gap: 5px; }
.detail-desc { font-size: 0.86rem; color: #4a5a4a; line-height: 1.6; margin: 14px 0 0; white-space: pre-line; overflow-wrap: anywhere; }

.share-box { margin-top: 18px; background: #fafbfa; border: 1px solid #eceeec; border-radius: 12px; padding: 14px 16px; }
.share-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.share-title { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.client-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.client-check { display: flex; align-items: center; gap: 10px; background: #fff; border: 1px solid #e3e8e3; border-radius: 10px; padding: 8px 10px; cursor: pointer; min-width: 0; }
.client-check.on { border-color: #1f8f5c; background: #f2f9f4; }
.client-check input { width: 16px; height: 16px; accent-color: #163a1c; flex-shrink: 0; }
.mini-avatar { width: 28px; height: 28px; border-radius: 50%; background: #00382a; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; object-fit: cover; flex-shrink: 0; }
.client-name { font-size: 0.84rem; font-weight: 600; color: #1a3a1a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.share-foot { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
.detail-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; padding-top: 14px; border-top: 1px solid #f0f2f0; }
.panel-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; color: #9aaa9a; min-height: 300px; font-size: 0.86rem; }
.panel-placeholder p { margin: 0; }

@media (max-width: 1100px) {
  .hero-banner { flex-direction: column; align-items: flex-start; }
}
/* below 1000px: just the list; a resource opens as a full-screen sheet */
@media (max-width: 999px) {
  .review-layout { grid-template-columns: minmax(0, 1fr); }
  .queue { position: static; max-height: none; }
  .queue-chevron { display: block; }
  .queue-item.active { background: none; border-color: transparent; }
  .panel-placeholder { display: none; }
  .panel-wrap { position: fixed; inset: 0; z-index: 250; background: #f4f5f3; overflow-y: auto; padding: 16px; }
  .back-btn { display: inline-flex; }
  .preview-frame { height: 60vh; }
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
.dropzone-hint { font-size: 0.74rem; color: #8a9a8a; }

.upload-note { font-size: 0.8rem; color: #6a7a6a; line-height: 1.5; background: #fdf8ee; border: 1px solid #f1e3bd; border-radius: 8px; padding: 10px 12px; margin: 0 0 20px; }

.modal-actions { display: flex; align-items: center; justify-content: flex-end; gap: 12px; }
.modal-cancel-btn { background: none; border: none; color: #4a5a4a; font-size: 0.85rem; font-weight: 600; cursor: pointer; padding: 11px 16px; }
.modal-upload-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 11px 24px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}
.modal-upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }

@media (max-width: 640px) {
  .tools-grid, .client-grid { grid-template-columns: minmax(0, 1fr); }
  .detail-actions > * { flex: 1; }
  .type-selector { grid-template-columns: repeat(2, 1fr); }
  .modal-box { padding: 22px 18px; }
}
</style>
