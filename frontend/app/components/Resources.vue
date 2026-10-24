<template>
  <div class="resources-page">
    <header class="page-head">
      <p class="page-intro">Handouts, guides and videos for your patients. Uploading sends nothing; you choose who receives each one.</p>
      <button class="nm-btn-dark" type="button" @click="openUploadModal"><Upload :size="15" aria-hidden="true" /> Upload resource</button>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <!-- TOOLBAR -->
    <div v-if="resources.length" class="nm-toolbar">
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

    <div v-else-if="!resources.length" class="nm-panel empty-state">
      <h2 class="empty-title">No resources yet</h2>
      <p class="empty-text">Upload a PDF, article, video or link. It stays private until you share it with a patient.</p>
    </div>

    <!-- one list: what it is, who has it, Share (Healthie-style library, 2026-10-24) -->
    <div v-else class="nm-panel lib">
      <p v-if="!filteredResources.length" class="lib-empty">{{ search ? 'No resources match that search.' : 'Nothing here.' }}</p>
      <ul v-else class="lib-list">
        <li v-for="r in pagedResources" :key="r.id" class="lib-row" :class="{ 'is-hidden': !r.is_active }">
          <span class="type-icon"><component :is="iconFor(r.type)" :size="17" aria-hidden="true" /></span>
          <div class="lib-main">
            <button type="button" class="lib-title" @click="openPreview(r)">{{ r.title }}</button>
            <p class="lib-sub">{{ r.type }}, uploaded {{ shortDate(r.created_at) }}</p>
          </div>
          <div class="lib-who">
            <span v-if="!r.is_active" class="nm-pill muted">Hidden from clients</span>
            <template v-else-if="r.shared_with?.length">
              <span class="faces" aria-hidden="true">
                <template v-for="c in r.shared_with.slice(0, 3)" :key="c.relationship_id">
                  <img v-if="c.photo" :src="c.photo" alt="" class="face" />
                  <span v-else class="face">{{ nameInitials(c.name) }}</span>
                </template>
                <span v-if="r.shared_with.length > 3" class="face more">+{{ r.shared_with.length - 3 }}</span>
              </span>
              <span class="who-text" :title="r.shared_with.map(c => c.name).join(', ')">{{ whoText(r) }}</span>
            </template>
            <span v-else class="not-shared">Not shared yet</span>
          </div>
          <div class="lib-actions">
            <button type="button" class="nm-btn-soft nm-btn-sm" @click="openShare(r)"><Send :size="13" aria-hidden="true" /> Share</button>
            <div class="more-wrap">
              <button
                type="button" class="more-btn" aria-label="More actions" aria-haspopup="menu" :aria-expanded="menuId === r.id"
                @click.stop="menuId = menuId === r.id ? null : r.id"
              ><MoreHorizontal :size="16" aria-hidden="true" /></button>
              <div v-if="menuId === r.id" class="more-menu" role="menu" @click.stop>
                <button type="button" role="menuitem" @click="openPreview(r)"><Eye :size="14" aria-hidden="true" /> Preview</button>
                <a v-if="r.file_path || r.url" role="menuitem" :href="r.file_path || r.url" target="_blank" rel="noopener" @click="menuId = null"><ExternalLink :size="14" aria-hidden="true" /> Open in new tab</a>
                <a v-if="r.download_url" role="menuitem" :href="r.download_url" @click="menuId = null"><Download :size="14" aria-hidden="true" /> Download</a>
                <button type="button" role="menuitem" :disabled="busyId === r.id" @click="toggleActive(r)">
                  <template v-if="r.is_active"><EyeOff :size="14" aria-hidden="true" /> Hide from clients</template>
                  <template v-else><Eye :size="14" aria-hidden="true" /> Show to clients again</template>
                </button>
              </div>
            </div>
          </div>
        </li>
      </ul>
      <ListPager v-model:page="resourcePage" :pages="resourcePages" />
    </div>

    <!-- PREVIEW -->
    <div v-if="previewR" class="nm-modal-overlay" @click.self="previewId = null">
      <div class="nm-modal preview-modal" role="dialog" aria-modal="true" :aria-label="previewR.title">
        <div class="pv-head nm-modal-head">
          <span class="type-icon"><component :is="iconFor(previewR.type)" :size="18" aria-hidden="true" /></span>
          <div class="pv-head-text">
            <h2 class="nm-modal-title">{{ previewR.title }}</h2>
            <p class="nm-modal-text">{{ previewR.type }}, uploaded {{ shortDate(previewR.created_at) }}, {{ previewR.is_active ? (previewR.shared_with?.length ? `shared with ${whoText(previewR)}` : 'not shared yet') : 'hidden from clients' }}</p>
          </div>
          <button type="button" aria-label="Close" @click="previewId = null"><X :size="18" aria-hidden="true" /></button>
        </div>
        <div class="preview">
          <iframe v-if="previewKind === 'pdf'" :src="previewR.file_path" :title="previewR.title" class="preview-frame" />
          <video v-else-if="previewKind === 'video'" :src="previewR.file_path" controls preload="metadata" class="preview-video" />
          <a v-else-if="previewKind === 'link'" :href="previewR.url" target="_blank" rel="noopener" class="preview-link">
            <LinkIcon :size="18" aria-hidden="true" />
            <span><strong>Open link</strong><span class="preview-url">{{ previewR.url }}</span></span>
            <ExternalLink :size="15" aria-hidden="true" />
          </a>
          <div v-else class="preview-none">
            <FileText :size="22" aria-hidden="true" />
            <p>This file type can't be previewed here. Download it or open it in a new tab.</p>
          </div>
        </div>
        <p v-if="previewR.description" class="detail-desc">{{ previewR.description }}</p>
        <div class="nm-modal-actions">
          <a v-if="previewR.download_url" :href="previewR.download_url" class="nm-btn-soft"><Download :size="14" aria-hidden="true" /> Download</a>
          <a v-if="previewR.file_path" :href="previewR.file_path" target="_blank" rel="noopener" class="nm-btn-soft"><ExternalLink :size="14" aria-hidden="true" /> Open in new tab</a>
          <button type="button" class="nm-btn-dark" @click="openShare(previewR)"><Send :size="14" aria-hidden="true" /> Share</button>
        </div>
      </div>
    </div>

    <!-- SHARE -->
    <div v-if="shareR" class="nm-modal-overlay" @click.self="closeShare">
      <div class="nm-modal share-modal" role="dialog" aria-modal="true" aria-labelledby="share-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="closeShare"><X :size="18" aria-hidden="true" /></button>
        <h2 id="share-title" class="nm-modal-title">Share "{{ shareR.title }}"</h2>
        <p class="nm-modal-text">Patients you tick see it in their Resource Library and get a notification. Untick someone to take it back.</p>
        <p v-if="!shareR.is_active" class="nm-note plain-note share-note">It's hidden, so patients can't see it even if it's shared. Show it again from the ⋯ menu to give them access.</p>
        <p v-if="shareLoading" class="nm-muted">Loading your patients…</p>
        <p v-else-if="shareError && !shareRows.length" class="nm-error">{{ shareError }}</p>
        <p v-else-if="!shareRows.length" class="nm-muted">You don't have any active patients yet. Once you confirm an appointment, you can share resources with them.</p>
        <template v-else>
          <div class="share-tools">
            <div v-if="shareRows.length > 6" class="nm-search share-search">
              <Search :size="15" />
              <input v-model="shareSearch" type="search" placeholder="Search your patients" />
            </div>
            <button v-if="shareRows.length > 1" type="button" class="nm-panel-link" @click="toggleAllClients">{{ allSelected ? 'Clear all' : 'Select all' }}</button>
          </div>
          <p v-if="!shownShareRows.length" class="nm-muted">No patient matches that name.</p>
          <div class="client-grid">
            <label v-for="row in shownShareRows" :key="row.relationship_id" class="client-check" :class="{ on: chosen.includes(row.relationship_id) }">
              <input v-model="chosen" type="checkbox" :value="row.relationship_id" />
              <img v-if="row.client.profile_photo" :src="row.client.profile_photo" class="mini-avatar" alt="" />
              <span v-else class="mini-avatar">{{ nameInitials(row.client.full_name) }}</span>
              <span class="client-name">{{ row.client.full_name }}</span>
            </label>
          </div>
          <p v-if="shareError" class="nm-error">{{ shareError }}</p>
        </template>
        <div class="nm-modal-actions share-actions">
          <span class="share-summary">{{ shareRows.length ? shareSummary : '' }}</span>
          <button type="button" class="nm-btn-soft" @click="closeShare">Cancel</button>
          <button type="button" class="nm-btn-dark" :disabled="!shareChanged || shareSaving" @click="saveSharing">{{ shareSaving ? 'Saving…' : 'Save sharing' }}</button>
        </div>
      </div>
    </div>

    <!-- ================= UPLOAD NEW RESOURCE MODAL ================= -->
    <div v-if="showUploadModal" class="nm-modal-overlay" @click.self="closeUploadModal">
      <div class="nm-modal upload-modal" role="dialog" aria-modal="true" aria-labelledby="upload-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="closeUploadModal"><X :size="18" aria-hidden="true" /></button>
        <h2 id="upload-title" class="nm-modal-title">Upload a resource</h2>

        <p class="field-label">Type</p>
        <div class="type-selector" role="radiogroup" aria-label="Type">
          <button
            v-for="t in resourceTypeOptions"
            :key="t.value"
            type="button"
            role="radio"
            :aria-checked="newUpload.type === t.value"
            class="type-option"
            :class="{ active: newUpload.type === t.value }"
            @click="newUpload.type = t.value"
          >
            <component :is="t.icon" :size="15" />
            {{ t.label }}
          </button>
        </div>


        <label class="field-label">Title</label>
        <input v-model="newUpload.title" type="text" class="field-input" autocomplete="off" placeholder="e.g. Understanding Glycemic Index" />

        <label class="field-label">Description <span class="optional">(optional)</span></label>
        <textarea v-model="newUpload.description" class="field-textarea" rows="3" placeholder="What it covers, in a sentence or two"></textarea>

        <template v-if="newUpload.type === 'Link'">
          <label class="field-label">URL</label>
          <input v-model="newUpload.url" type="url" class="field-input" placeholder="https://..." />
        </template>
        <template v-else>
          <p class="field-label">File</p>
          <label class="file-pick">
            <input type="file" class="file-input" :accept="fileRule.accept" @change="onFileSelected" />
            <span class="file-btn">{{ newUpload.fileName ? 'Change file' : 'Choose a file' }}</span>
            <span class="file-name" :class="{ 'is-empty': !newUpload.fileName }">{{ newUpload.fileName || 'No file chosen' }}</span>
          </label>
          <p class="file-hint">{{ fileRule.hint }}</p>
        </template>

        <p v-if="uploadError" class="form-error">{{ uploadError }}</p>

        <p class="upload-note">Uploading doesn't send it to anyone. Next, you pick the patients who should receive it.</p>

        <div class="nm-modal-actions">
          <button class="nm-btn-soft" type="button" @click="closeUploadModal">Cancel</button>
          <button
            class="nm-btn-dark"
            :disabled="!canSubmit || isSubmitting"
            @click="submitUpload"
          >{{ isSubmitting ? 'Uploading…' : 'Upload' }}</button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  CheckCircle2, Download, ExternalLink, Eye, EyeOff, FileEdit, FileText,
  Link as LinkIcon, MoreHorizontal, PlayCircle, Search, Send, Upload, X,
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

/* ---------- LIST ---------- */
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
const { page: resourcePage, pages: resourcePages, paged: pagedResources } = usePager(filteredResources, { resetOn: () => [tab.value, search.value] })

// Every type gets a green icon; the icon itself says which type it is.
function iconFor(type) {
  if (type === 'PDF') return FileText
  if (type === 'Video') return PlayCircle
  if (type === 'Article') return FileEdit
  if (type === 'Link') return LinkIcon
  return FileText
}
// "Mia Santos", or "5 patients"
function whoText(r) {
  const n = r.shared_with?.length || 0
  return n === 1 ? r.shared_with[0].name : `${n} patients`
}

// the ⋯ menu on a row
const menuId = ref(null)
function closeMenus() { menuId.value = null }

// Reload quietly after a change (and in the background, useAutoRefresh), so
// the row's faces and counts follow.
useAutoRefresh(() => refreshList())
async function refreshList() {
  try {
    const data = await get('/rnd/resources/')
    resources.value = data.map(r => ({ ...r, type: toDisplayType(r.type) }))
  } catch {
    // the list just keeps what it had
  }
}

/* ---------- PREVIEW ---------- */
const previewId = ref(null)
const previewR = computed(() => resources.value.find(r => r.id === previewId.value) || null)
function openPreview(r) {
  menuId.value = null
  previewId.value = r.id
}
// PDF / video play in the page; Word documents can't, so they get a link.
const previewKind = computed(() => {
  const r = previewR.value
  if (!r) return null
  if (r.type === 'Link') return r.url ? 'link' : null
  const path = (r.file_path || '').toLowerCase().split('?')[0]
  if (r.type === 'Video' || /\.(mp4|webm|mov)$/.test(path)) return 'video'
  if (path.endsWith('.pdf') || r.type === 'PDF') return 'pdf'
  return null
})

/* ---------- SHARE: GET who's shared, POST to add, DELETE to remove ---------- */
const shareId = ref(null)
const shareR = computed(() => resources.value.find(r => r.id === shareId.value) || null)
const shareRows = ref([])
const chosen = ref([])
const shareSearch = ref('')
const shareLoading = ref(false)
const shareSaving = ref(false)
const shareError = ref('')
const shownShareRows = computed(() => {
  const q = shareSearch.value.trim().toLowerCase()
  return q ? shareRows.value.filter(r => r.client.full_name.toLowerCase().includes(q)) : shareRows.value
})
const originallyShared = computed(() => shareRows.value.filter(r => r.shared).map(r => r.relationship_id))
const toAdd = computed(() => chosen.value.filter(id => !originallyShared.value.includes(id)))
const toRemove = computed(() => originallyShared.value.filter(id => !chosen.value.includes(id)))
const shareChanged = computed(() => toAdd.value.length > 0 || toRemove.value.length > 0)
const allSelected = computed(() => shareRows.value.length > 0 && shareRows.value.every(r => chosen.value.includes(r.relationship_id)))
const shareSummary = computed(() => {
  const parts = [chosen.value.length ? `${chosen.value.length} selected` : 'Nobody selected']
  if (toAdd.value.length) parts.push(`${toAdd.value.length} will be notified`)
  if (toRemove.value.length) parts.push(`${toRemove.value.length} will lose access`)
  return parts.join(', ')
})
function toggleAllClients() {
  chosen.value = allSelected.value ? [] : shareRows.value.map(r => r.relationship_id)
}
function openShare(r) {
  menuId.value = null
  previewId.value = null
  shareSearch.value = ''
  shareId.value = r.id
}
function closeShare() {
  if (!shareSaving.value) shareId.value = null
}
async function loadSharing(id) {
  shareLoading.value = true
  shareError.value = ''
  shareRows.value = []
  chosen.value = []
  try {
    const rows = await get(`/rnd/resources/${id}/share/`)
    if (shareId.value !== id) return
    shareRows.value = rows
    chosen.value = rows.filter(r => r.shared).map(r => r.relationship_id)
  } catch {
    shareError.value = 'Could not load your patients. Please try again.'
  } finally {
    shareLoading.value = false
  }
}
watch(shareId, (id) => { if (id) loadSharing(id) })

async function saveSharing() {
  const r = shareR.value
  shareSaving.value = true
  shareError.value = ''
  const added = toAdd.value.length
  const removed = toRemove.value.length
  try {
    if (added) await post(`/rnd/resources/${r.id}/share/`, { relationship_ids: toAdd.value })
    for (const id of toRemove.value) await del(`/rnd/resources/${r.id}/share/${id}/`)
    await refreshList()
    shareSaving.value = false
    shareId.value = null
    const parts = []
    if (added) parts.push(`Shared with ${added} patient${added > 1 ? 's' : ''}. They were notified`)
    if (removed) parts.push(`${added ? 'removed' : 'Removed'} from ${removed}`)
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
  menuId.value = null
  busyId.value = r.id
  try {
    await patch(`/rnd/resources/${r.id}/`, { is_active: !r.is_active })
    r.is_active = !r.is_active
    showToast(r.is_active ? 'Patients you shared it with can see it again.' : 'Hidden. Patients can no longer see it.')
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

// Esc closes the ⋯ menu first, then a pop-up; a click anywhere closes the menu.
function onKey(e) {
  if (e.key !== 'Escape') return
  if (menuId.value) menuId.value = null
  else if (shareId.value) closeShare()
  else if (previewId.value) previewId.value = null
}
onMounted(() => {
  document.addEventListener('click', closeMenus)
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', closeMenus)
  window.removeEventListener('keydown', onKey)
})

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
  return { ...rule, accept: rule.exts.join(','), hint: `${rule.exts.join(', ')}, up to ${rule.maxMb} MB` }
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
    if (created?.id) openShare(created)
    showToast('Uploaded. Now choose who receives it.')
  } catch (error) {
    uploadError.value = error?.data?.non_field_errors?.[0] || error?.data?.url?.[0] || error?.data?.file?.[0] || error?.data?.title?.[0] || 'Could not add this resource. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}


onMounted(loadResources)

</script>

<style scoped>
* { box-sizing: border-box; }

.resources-page { font-family: 'Inter', sans-serif; }

/* PAGE HEAD: one line of context and the one action */
.page-head { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin: 0 0 22px; }
.page-intro { font-size: 0.9rem; color: #4a5a4a; line-height: 1.55; margin: 0; max-width: 60ch; }
.page-head .nm-btn-dark { flex-shrink: 0; }

.empty-state { padding: 40px 32px; }
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.15rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-text { font-size: 0.88rem; color: #5a6a5a; line-height: 1.55; margin: 0; max-width: 52ch; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 20px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

/* type icon: green for every type, the icon says which */
.type-icon { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #e3efe7; color: #0a4a37; }

/* THE LIBRARY: one divided list */
.lib { padding: 0; }
.lib-empty { margin: 0; padding: 22px; font-size: 0.86rem; color: #6a7a6a; }
.lib-list { list-style: none; margin: 0; padding: 0; }
.lib-row {
  display: grid; grid-template-columns: 36px minmax(0, 1fr) minmax(150px, 220px) auto; align-items: center; gap: 14px;
  padding: 14px 20px; border-top: 1px solid #d9e3dc;
}
.lib-row:first-child { border-top: none; }
.lib-row.is-hidden .lib-title, .lib-row.is-hidden .type-icon { opacity: 0.6; }
.lib-main { min-width: 0; }
.lib-title {
  display: block; max-width: 100%; border: none; background: none; padding: 0; font-family: inherit; text-align: left; cursor: pointer;
  font-size: 0.9rem; font-weight: 600; color: #1a3a1a; line-height: 1.35; overflow-wrap: anywhere;
}
.lib-title:hover { color: #0a4a37; text-decoration: underline; }
.lib-title:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; border-radius: 4px; }
.lib-sub { margin: 2px 0 0; font-size: 0.78rem; color: #6a7a6a; }

/* who has it: up to three faces, then +n */
.lib-who { display: flex; align-items: center; gap: 8px; min-width: 0; }
.faces { display: flex; flex-shrink: 0; }
.face {
  width: 28px; height: 28px; border-radius: 50%; border: 2px solid #fff; margin-left: -8px; object-fit: cover;
  display: flex; align-items: center; justify-content: center; background: #0a4a37; color: #fff; font-size: 0.64rem; font-weight: 700;
}
.face:first-child { margin-left: 0; }
.face.more { background: #e3efe7; color: #0a4a37; }
.who-text { font-size: 0.8rem; color: #4a5a4a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
/* something still to do: dashed green */
.not-shared { font-size: 0.78rem; font-weight: 600; color: #1f4a30; border: 1.5px dashed #3f9a6b; border-radius: 999px; padding: 3px 10px; white-space: nowrap; }

.lib-actions { display: flex; align-items: center; gap: 8px; }
.more-wrap { position: relative; }
.more-btn { width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: none; border-radius: 8px; background: #e3efe7; color: #0a4a37; cursor: pointer; }
.more-btn:hover { background: #d3e7da; }
.more-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.more-menu {
  position: absolute; right: 0; top: calc(100% + 6px); z-index: 20; min-width: 210px; padding: 6px; background: #fff;
  border: 1px solid #d9e3dc; border-radius: 12px; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09);
}
.more-menu > * {
  display: flex; align-items: center; gap: 8px; width: 100%; min-height: 36px; padding: 0 10px; border: none; border-radius: 8px;
  background: none; font-family: inherit; font-size: 0.84rem; font-weight: 500; color: #1a3a1a; text-decoration: none; cursor: pointer; text-align: left;
}
.more-menu > *:hover:not(:disabled) { background: #f2f7f3; }
.more-menu > *:disabled { opacity: 0.5; cursor: not-allowed; }
.more-menu > *:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.lib .nm-pager { margin: 0; padding: 12px 20px; }

/* PREVIEW pop-up */
.preview-modal { max-width: 820px; }
.pv-head { display: flex; align-items: flex-start; gap: 12px; }
.pv-head-text { flex: 1; min-width: 0; }
.pv-head .nm-modal-title { overflow-wrap: anywhere; }
.preview { border: 1px solid #d9e3dc; border-radius: 12px; overflow: hidden; background: #f7f9f7; }
.preview-frame { display: block; width: 100%; height: 60vh; border: 0; background: #fff; }
.preview-video { display: block; width: 100%; max-height: 60vh; background: #000; }
.preview-link { display: flex; align-items: center; gap: 12px; padding: 18px; text-decoration: none; color: #1a3a1a; }
.preview-link > span { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; font-size: 0.88rem; }
.preview-url { font-size: 0.78rem; color: #1f6f46; overflow-wrap: anywhere; }
.preview-none { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 30px 16px; color: #6a7a6a; font-size: 0.84rem; text-align: center; }
.preview-none p { margin: 0; }
.detail-desc { font-size: 0.86rem; color: #4a5a4a; line-height: 1.6; margin: 14px 0 0; white-space: pre-line; overflow-wrap: anywhere; }

/* SHARE pop-up */
.share-modal { max-width: 560px; }
.share-note { margin: 0 0 12px; }
.share-tools { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin: 0 0 10px; }
.share-search { flex: 1; }
.share-tools .nm-panel-link { margin-left: auto; }
.client-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.client-check { display: flex; align-items: center; gap: 10px; background: #fff; border: 1px solid #d9e3dc; border-radius: 10px; padding: 8px 10px; cursor: pointer; min-width: 0; }
.client-check.on { border-color: #1f8f5c; background: #f2f9f4; }
.client-check input { width: 16px; height: 16px; accent-color: #0a4a37; flex-shrink: 0; }
.mini-avatar { width: 28px; height: 28px; border-radius: 50%; background: #0a4a37; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; object-fit: cover; flex-shrink: 0; }
.client-name { font-size: 0.84rem; font-weight: 600; color: #1a3a1a; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.share-actions { align-items: center; }
.share-summary { margin-right: auto; font-size: 0.8rem; color: #4a5a4a; }

@media (max-width: 640px) {
  .page-head { flex-direction: column; align-items: stretch; }
}
/* phones: each row becomes a card, the who-line and buttons under the title */
@media (max-width: 760px) {
  .lib-row { grid-template-columns: 36px minmax(0, 1fr); gap: 8px 12px; padding: 14px 16px; }
  .lib-who { grid-column: 2; }
  .lib-actions { grid-column: 2; }
  .lib-actions .nm-btn-soft { flex: 1; justify-content: center; }
  .lib .nm-pager { padding: 12px 16px; }
  .preview-frame { height: 55vh; }
  .share-summary { flex-basis: 100%; }
}

/* ============ UPLOAD NEW RESOURCE MODAL ============ */
.upload-modal { max-width: 500px; }


.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #2a2a2a; margin: 0 0 8px; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input, .field-textarea {
  width: 100%; border: 1px solid #e5e8e5; border-radius: 8px; padding: 11px 14px;
  font-size: 0.86rem; color: #2a2a2a; background: #fff; font-family: inherit; margin-bottom: 18px;
}
.field-textarea { resize: vertical; }

.type-selector { display: inline-flex; gap: 2px; padding: 3px; background: #f1f3f0; border-radius: 9px; margin-bottom: 18px; }
.type-option {
  display: inline-flex; align-items: center; gap: 6px;
  border: none; background: none; color: #5a6a5a; border-radius: 7px;
  padding: 7px 12px; font-size: 0.82rem; font-weight: 600; cursor: pointer; font-family: inherit;
}
.type-option:hover { color: #1a3a1a; }
.type-option.active { background: #fff; color: #1a3a1a; box-shadow: 0 1px 2px rgba(20,40,20,0.12); }
.type-option:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }

.file-pick { position: relative; display: flex; align-items: center; gap: 12px; border: 1px solid #e5e8e5; border-radius: 8px; padding: 6px; cursor: pointer; }
.file-pick:focus-within { border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31,143,92,0.15); }
.file-input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.file-btn { flex-shrink: 0; background: #f1f3f0; color: #1a3a1a; border-radius: 6px; padding: 7px 12px; font-size: 0.82rem; font-weight: 600; }
.file-pick:hover .file-btn { background: #e7ebe6; }
.file-name { font-size: 0.84rem; color: #2a2a2a; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-name.is-empty { color: #9aaa9a; }
.file-hint { font-size: 0.76rem; color: #8a9a8a; margin: 6px 0 18px; }

.upload-note { font-size: 0.8rem; color: #4a5a4a; line-height: 1.5; background: #f4f6f4; border: 1px solid #d9e3dc; border-radius: 8px; padding: 10px 12px; margin: 0 0 20px; }


@media (max-width: 640px) {
  .client-grid { grid-template-columns: minmax(0, 1fr); }
  .type-selector { display: flex; }
  .type-option { flex: 1; justify-content: center; padding: 7px 6px; }
}
</style>
