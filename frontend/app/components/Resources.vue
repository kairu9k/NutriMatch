<template>
  <div class="resources-page">
    <header class="page-head">
      <img class="rs-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="rs-fade" aria-hidden="true"></span>
      <div class="rs-hero-txt">
        <p class="rs-eyebrow"><span aria-hidden="true"></span>Resources</p>
        <h2 class="rs-title">Your resource library</h2>
        <p class="page-intro">Handouts, guides and videos for your patients. Uploading sends nothing; you choose who receives each one.</p>
        <button class="nm-btn-dark rs-up" type="button" @click="openUploadModal"><Upload :size="16" aria-hidden="true" /> Upload resource</button>
      </div>
    </header>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <!-- TOOLBAR -->
    <div v-if="resources.length" class="nm-toolbar rs-toolbar">
      <div class="nm-tabs rs-tabs">
        <button v-for="t in TABS" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" @click="tab = t.key">
          <svg v-if="t.key === 'all'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z" /><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5" /></svg><svg v-else-if="t.key === 'shared'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" /></svg><svg v-else-if="t.key === 'not_shared'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg><svg v-else class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.9 17.9A10 10 0 0 1 12 20c-7 0-10-8-10-8a18 18 0 0 1 5.1-5.9M9.9 4.2A9 9 0 0 1 12 4c7 0 10 8 10 8a18 18 0 0 1-2.2 3.2M1 1l22 22" /></svg>
          {{ t.label }} <span class="nm-count">{{ countOf(t.key) }}</span>
        </button>
      </div>
      <div class="nm-search rs-search">
        <Search :size="17" />
        <input v-model="search" type="search" placeholder="Search your resources" />
      </div>
    </div>

    <div v-if="isLoading" class="nm-panel rs-loading"><span class="rs-spin" aria-hidden="true"></span><p class="nm-muted">Loading your resources…</p></div>

    <div v-else-if="!resources.length" class="nm-panel empty-state">
      <span class="empty-ico"><svg class="ic" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z" /><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5" /></svg></span>
      <h2 class="empty-title">No resources yet</h2>
      <p class="empty-text">Upload a PDF, article, video or link. It stays private until you share it with a patient.</p>
    </div>

    <!-- one list: what it is, who has it, Share (Healthie-style library, 2026-10-24) -->
    <div v-else class="nm-panel lib">
      <div v-if="filteredResources.length" class="lib-thead" aria-hidden="true"><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg> Resource</span><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" /></svg> Shared with</span><span></span></div>
      <p v-if="!filteredResources.length" class="lib-empty">{{ search ? 'No resources match that search.' : 'Nothing here.' }}</p>
      <ul v-else class="lib-list">
        <li v-for="r in pagedResources" :key="r.id" class="lib-row" :class="[{ 'is-hidden': !r.is_active }, 'tone-' + rowTone(r)]">
          <span class="type-icon file-tile"><component :is="iconFor(r.type)" :size="20" aria-hidden="true" /><b>{{ r.type }}</b></span>
          <div class="lib-main">
            <button type="button" class="lib-title" @click="openPreview(r)">{{ r.title }}</button>
            <p class="lib-sub"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg> Uploaded {{ shortDate(r.created_at) }}</p>
          </div>
          <div class="lib-who">
            <span v-if="!r.is_active" class="nm-pill muted"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.9 17.9A10 10 0 0 1 12 20c-7 0-10-8-10-8a18 18 0 0 1 5.1-5.9M9.9 4.2A9 9 0 0 1 12 4c7 0 10 8 10 8a18 18 0 0 1-2.2 3.2M1 1l22 22" /></svg> Hidden from clients</span>
            <template v-else-if="r.shared_with?.length">
              <span class="faces" aria-hidden="true">
                <template v-for="c in r.shared_with.slice(0, 3)" :key="c.relationship_id">
                  <img v-if="c.photo" :src="c.photo" alt="" class="face" />
                  <span v-else class="face">{{ nameInitials(c.name) }}</span>
                </template>
                <span v-if="r.shared_with.length > 3" class="face more">+{{ r.shared_with.length - 3 }}</span>
              </span>
              <span class="who-wrap">
                <span class="who-text" :title="r.shared_with.map(c => c.name).join(', ')">{{ whoText(r) }}</span>
                <small class="who-state"><i aria-hidden="true"></i>Shared</small>
              </span>
            </template>
            <span v-else class="not-shared"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg> Not shared yet</span>
          </div>
          <div class="lib-actions">
            <button type="button" class="nm-btn-soft nm-btn-sm share-btn" @click="openShare(r)"><Send :size="15" aria-hidden="true" /> Share</button>
            <div class="more-wrap">
              <button
                type="button" class="more-btn" aria-label="More actions" aria-haspopup="menu" :aria-expanded="menuId === r.id"
                @click.stop="menuId = menuId === r.id ? null : r.id"
              ><MoreHorizontal :size="18" aria-hidden="true" /></button>
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
        <header class="um-head">
          <img class="um-plate" :src="plateImg" alt="" aria-hidden="true" />
          <span class="um-fade" aria-hidden="true"></span>
          <span class="um-hico" aria-hidden="true"><Upload :size="22" /></span>
          <div class="um-head-txt">
            <p class="um-kind">Resource library</p>
            <h2 id="upload-title" class="nm-modal-title">Upload a resource</h2>
            <p class="um-sub">Add a handout, guide, video or link.</p>
          </div>
          <button type="button" class="nm-modal-x um-x" aria-label="Close" @click="closeUploadModal"><X :size="18" aria-hidden="true" /></button>
        </header>

        <div class="um-body">
          <p class="field-label um-step-label"><span aria-hidden="true">1</span>Type</p>
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
              <span class="ut-ico"><component :is="t.icon" :size="18" /></span>
              <strong>{{ t.label }}</strong>
              <small>{{ typeHint(t.value) }}</small>
              <i v-if="newUpload.type === t.value" class="ut-chk" aria-hidden="true"><svg class="ic" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></i>
            </button>
          </div>

          <p class="field-label um-step-label"><span aria-hidden="true">2</span>Details</p>
          <label class="field-label">Title</label>
          <input v-model="newUpload.title" type="text" class="field-input" autocomplete="off" placeholder="e.g. Understanding Glycemic Index" />

          <label class="field-label">Description <span class="optional">(optional)</span></label>
          <textarea v-model="newUpload.description" class="field-textarea" rows="3" placeholder="What it covers, in a sentence or two"></textarea>

          <template v-if="newUpload.type === 'Link'">
            <p class="field-label um-step-label"><span aria-hidden="true">3</span>Link</p>
            <label class="field-label">URL</label>
            <input v-model="newUpload.url" type="url" class="field-input" placeholder="https://..." />
          </template>
          <template v-else>
            <p class="field-label um-step-label"><span aria-hidden="true">3</span>File</p>
            <label class="file-pick" :class="{ picked: newUpload.fileName }">
              <input type="file" class="file-input" :accept="fileRule.accept" @change="onFileSelected" />
              <span class="um-dico" aria-hidden="true"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M16 16l-4-4-4 4M12 12v9" /><path d="M20.4 18.4A5 5 0 0 0 18 9h-1.3A8 8 0 1 0 3 16.3" /></svg></span>
              <span class="file-btn">{{ newUpload.fileName ? 'Change file' : 'Choose a file' }}</span>
              <span class="file-name" :class="{ 'is-empty': !newUpload.fileName }">{{ newUpload.fileName || 'No file chosen' }}</span>
              <span class="file-hint">{{ fileRule.hint }}</span>
            </label>
          </template>

          <p v-if="uploadError" class="form-error">{{ uploadError }}</p>

          <div class="upload-note">
            <span class="um-flow on"><Upload :size="13" aria-hidden="true" /> Upload</span>
            <span class="um-arrow" aria-hidden="true"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></span>
            <span class="um-flow"><Send :size="13" aria-hidden="true" /> Pick patients</span>
            <p>Uploading doesn't send it to anyone. Next, you pick the patients who should receive it.</p>
          </div>
        </div>

        <div class="nm-modal-actions um-foot">
          <button class="nm-btn-soft" type="button" @click="closeUploadModal">Cancel</button>
          <button
            class="nm-btn-dark"
            :disabled="!canSubmit || isSubmitting"
            @click="submitUpload"
          ><Upload :size="15" aria-hidden="true" /> {{ isSubmitting ? 'Uploading…' : 'Upload' }}</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
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

const toast = useToast() // the app's toast (2026-11-03)
function showToast(text, opts) {
  toast.success(text, opts)
}

async function toggleActive(r) {
  menuId.value = null
  busyId.value = r.id
  try {
    await patch(`/rnd/resources/${r.id}/`, { is_active: !r.is_active })
    r.is_active = !r.is_active
    showToast(r.is_active ? 'Patients you shared it with can see it again.' : 'Hidden. Patients can no longer see it.')
  } catch {
    toast.error('Could not update this resource. Please try again.')
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

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// upload modal: the limit under each type card
const typeHint = v => (v === 'Link' ? 'A web address' : `Up to ${(FILE_RULES[v] || FILE_RULES.PDF).maxMb} MB`)
// accent colour of a row: shared green, not shared gold, hidden grey
const rowTone = r => (!r.is_active ? 'muted' : r.shared_with?.length ? 'green' : 'gold')

</script>
<style scoped>
* { box-sizing: border-box; }
.resources-page { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; }

/* ---------- hero ---------- */
.page-head {
  position: relative; overflow: hidden; display: flex; align-items: center; gap: 18px 24px; margin: 0 0 18px; padding: 26px 30px; border-radius: 24px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.rs-plate { position: absolute; right: -70px; top: 50%; width: 340px; height: 340px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.rs-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 48%, rgba(0, 77, 58, 0.85) 70%, rgba(0, 77, 58, 0.6) 100%); }
.rs-hero-txt { position: relative; z-index: 1; flex: 1 1 360px; min-width: 0; max-width: 620px; }
.rs-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.rs-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.rs-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.page-intro { margin: 0 0 16px; max-width: 62ch; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }
.page-head .nm-btn-dark.rs-up { display: inline-flex; align-items: center; gap: 8px; height: 42px; padding: 0 18px; border: none; border-radius: 12px; background: #efbf04; color: #004d3a; font-family: inherit; font-size: 13.5px; font-weight: 800; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); cursor: pointer; transition: background 0.15s, transform 0.15s; }
.page-head .nm-btn-dark.rs-up:hover { background: #f5cb1c; transform: translateY(-1px); }
.page-head .rs-up:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }

.form-error { margin: 0 0 18px; padding: 11px 14px; border-radius: 14px; background: #fdecea; border: 1px solid #f6c9c3; color: #b42318; font-size: 13.5px; }

/* ---------- tabs + search ---------- */
.rs-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin: 0 0 16px; }
.rs-tabs { display: inline-flex; gap: 4px; max-width: 100%; padding: 5px; border: none; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); overflow-x: auto; scrollbar-width: none; }
.rs-tabs::-webkit-scrollbar { display: none; }
.rs-tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 36px; margin: 0; padding: 0 15px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.rs-tabs .nm-tab .ic { display: inline-block; color: #8a9a91; }
.rs-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; }
.rs-tabs .nm-count { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 700; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; }
.rs-tabs .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.rs-tabs .nm-tab.active .ic { color: #efbf04; }
.rs-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }
.rs-tabs .nm-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.rs-search { position: relative; display: flex; align-items: center; gap: 10px; flex: 0 1 320px; height: 46px; margin: 0; padding: 0 16px; border: none; border-radius: 999px; background: #fff; color: #8a9a91; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); }
.rs-search:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.rs-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.rs-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }

/* ---------- loading + empty ---------- */
.rs-loading { display: flex; flex-direction: column; align-items: center; gap: 10px; padding: 40px 20px; border: none; border-radius: 24px; box-shadow: var(--sh); }
.rs-loading .nm-muted { margin: 0; }
.rs-spin { width: 22px; height: 22px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: rs-spin 0.8s linear infinite; }
@keyframes rs-spin { to { transform: rotate(360deg); } }
.empty-state { display: flex; flex-direction: column; align-items: center; padding: 44px 28px; border: none; border-radius: 24px; text-align: center; box-shadow: var(--sh); }
.empty-ico { width: 60px; height: 60px; margin-bottom: 14px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.empty-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.empty-text { margin: 0; max-width: 52ch; font-size: 13.5px; line-height: 1.55; color: #6b7d73; }

/* ---------- the library ---------- */
.lib { padding: 0; border: none; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: visible; }
.lib-thead, .lib-row { display: grid; grid-template-columns: 52px minmax(0, 1.6fr) minmax(0, 1fr) 200px; gap: 16px 32px; align-items: center; padding: 0 32px; }
.lib-thead { padding-top: 15px; padding-bottom: 15px; border-radius: 24px 24px 0 0; background: #eaf3ed; border-bottom: 1px solid #dcebe1; font-size: 13px; font-weight: 700; color: #1f5c45; }
.lib-thead span { display: inline-flex; align-items: center; gap: 7px; }
.lib-thead span:first-child { grid-column: 1 / 3; }
.lib-thead .ic { color: #1f7a4d; }
.lib-empty { margin: 0; padding: 26px 32px; font-size: 14px; color: #6b7d73; }
.lib-list { list-style: none; margin: 0; padding: 0; }
.lib-row { position: relative; padding-top: 20px; padding-bottom: 20px; border-top: 1px solid #f0f3f1; transition: background 0.15s; }
.lib-row:first-child { border-top: none; }
.lib-row:hover { background: #fafcfb; }
.lib-row:last-child { border-radius: 0 0 24px 24px; }
.lib-row::before { content: ''; position: absolute; left: 0; top: 20px; bottom: 20px; width: 4px; border-radius: 0 4px 4px 0; background: #c9d3cd; }
.lib-row.tone-green::before { background: #1f9d55; }
.lib-row.tone-gold::before { background: #efbf04; }

/* file tile: dark green with the type on a gold tag */
.type-icon.file-tile { position: relative; width: 52px; height: 58px; padding-bottom: 10px; border-radius: 14px; background: linear-gradient(160deg, #035a45, #004d3a); color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.85); }
.file-tile b { position: absolute; left: 50%; bottom: 6px; transform: translateX(-50%); max-width: 46px; padding: 1px 5px; border-radius: 5px; background: #efbf04; color: #004d3a; font-size: 9px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.lib-row.is-hidden .file-tile { background: #e3e9e5; color: #6b7d73; box-shadow: none; }
.lib-row.is-hidden .file-tile b { background: #fff; color: #6b7d73; }
.lib-row.is-hidden .lib-title { opacity: 0.65; }
.lib-main { min-width: 0; }
.lib-title { display: block; max-width: 100%; padding: 0; border: none; background: none; font-family: inherit; text-align: left; cursor: pointer; font-size: 15px; font-weight: 700; line-height: 1.35; color: #0e3a2c; overflow-wrap: anywhere; }
.lib-title:hover { color: #004d3a; text-decoration: underline; text-underline-offset: 3px; }
.lib-title:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; border-radius: 4px; }
.lib-sub { display: flex; align-items: center; gap: 7px; margin: 5px 0 0; font-size: 13px; color: #6b7d73; }
.lib-sub .ic { display: inline-block; color: #1f7a4d; }

/* who has it */
.lib-who { display: flex; align-items: center; gap: 12px; min-width: 0; }
.faces { display: flex; flex-shrink: 0; }
.face { width: 42px; height: 42px; margin-left: -12px; border-radius: 50%; border: 2px solid #fff; object-fit: cover; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-size: 13px; font-weight: 800; box-shadow: 0 0 0 2.5px #1f9d55; }
.face:first-child { margin-left: 0; }
.face.more { background: #e3f4ea; color: #1f7a4d; }
.who-wrap { display: flex; flex-direction: column; min-width: 0; }
.who-text { font-size: 14.5px; font-weight: 700; color: #0e3a2c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.who-state { display: flex; align-items: center; gap: 6px; margin-top: 3px; font-size: 12.5px; font-weight: 600; color: #1f7a4d; }
.who-state i { width: 7px; height: 7px; border-radius: 50%; background: #1f9d55; box-shadow: 0 0 0 3px #e3f4ea; }
.not-shared { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 999px; background: #fff4d6; font-size: 12.5px; font-weight: 700; color: #8a6500; white-space: nowrap; }
.lib-who .nm-pill.muted { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border-radius: 999px; background: #f3f6f4; font-size: 12.5px; font-weight: 700; color: #6b7d73; }
.lib-who .ic { display: inline-block; }

/* actions */
.lib-actions { display: flex; align-items: center; justify-content: flex-end; gap: 8px; }
.lib-actions .nm-btn-soft.share-btn { display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 40px; padding: 0 18px; border: 1px solid #004d3a; border-radius: 12px; background: #004d3a; color: #fff; font-size: 13.5px; font-weight: 800; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.lib-actions .nm-btn-soft.share-btn:hover { background: #00382a; }
.lib-actions .share-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.more-wrap { position: relative; }
.more-btn { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border: 1px solid #dce8e0; border-radius: 12px; background: #f1f6f2; color: #004d3a; cursor: pointer; }
.more-btn:hover { background: #e3efe7; }
.more-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.more-menu { position: absolute; right: 0; top: calc(100% + 8px); z-index: 20; min-width: 220px; padding: 6px; border: 1px solid #e3ebe6; border-radius: 14px; background: #fff; box-shadow: 0 18px 40px -16px rgba(0, 0, 0, 0.3); }
.more-menu > * { display: flex; align-items: center; gap: 9px; width: 100%; min-height: 38px; padding: 0 12px; border: none; border-radius: 10px; background: none; font-family: inherit; font-size: 13.5px; font-weight: 500; color: #0e3a2c; text-decoration: none; text-align: left; cursor: pointer; }
.more-menu > * svg { color: #1f7a4d; }
.more-menu > *:hover:not(:disabled) { background: #f1f6f2; }
.more-menu > *:disabled { opacity: 0.5; cursor: not-allowed; }
.more-menu > *:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.lib .nm-pager { margin: 0; padding: 14px 32px; border-top: 1px solid #f0f3f1; }

/* type icon in the preview header */
.type-icon { width: 40px; height: 40px; border-radius: 12px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #e3efe7; color: #004d3a; }

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

.preview { border-color: #e3ebe6; border-radius: 16px; }
.client-check { border-radius: 12px; padding: 10px 12px; }
.client-check.on { border-color: #1f9d55; background: #f1f8f4; }
.mini-avatar { background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; }

/* ---------- responsive ---------- */
@media (max-width: 960px) {
  .page-head { padding: 20px 18px; border-radius: 22px; }
  .rs-title { font-size: 24px; }
  .rs-plate { width: 200px; height: 200px; right: -80px; top: 40px; transform: none; }
  .page-head .rs-up { width: 100%; justify-content: center; }
  .rs-search { flex: 1 1 100%; }
  .rs-tabs { display: flex; width: 100%; border-radius: 16px; }
}
@media (max-width: 760px) {
  .resources-page { padding-bottom: 110px; }
  .lib-thead { display: none; }
  .lib-row { grid-template-columns: 52px minmax(0, 1fr); gap: 12px 14px; padding: 16px; }
  .lib-row::before { top: 16px; bottom: 16px; }
  .lib-row:first-child { border-radius: 24px 24px 0 0; }
  .lib-who { grid-column: 1 / -1; padding: 10px 12px; border-radius: 14px; background: #f7faf8; }
  .lib-actions { grid-column: 1 / -1; }
  .lib-actions .share-btn { flex: 1; }
  .lib .nm-pager { padding: 12px 16px; }
  .preview-frame { height: 55vh; }
  .share-summary { flex-basis: 100%; }
}

/* ============ UPLOAD NEW RESOURCE MODAL ============ */
.nm-modal.upload-modal { position: relative; display: flex; flex-direction: column; width: min(560px, 100%); max-width: 560px; max-height: calc(100vh - 48px); padding: 0; border-radius: 24px; overflow: hidden; background: #fff; box-shadow: 0 40px 90px -30px rgba(0, 0, 0, 0.55); }
.um-head {
  position: relative; overflow: hidden; flex-shrink: 0; display: flex; align-items: center; gap: 14px; padding: 22px 24px; color: #fff;
  background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 55%, #004635 100%);
}
.um-head > *:not(.um-plate):not(.um-fade) { position: relative; z-index: 1; }
.um-plate { position: absolute; right: -40px; top: 50%; width: 200px; height: 200px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.um-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 50%, rgba(0, 77, 58, 0.85) 68%, rgba(0, 77, 58, 0.65) 100%); }
.um-hico { flex-shrink: 0; width: 50px; height: 50px; border-radius: 15px; background: #efbf04; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
.um-head-txt { flex: 1; min-width: 0; }
.um-kind { margin: 0 0 3px; font-size: 11.5px; font-weight: 800; color: #efbf04; }
.upload-modal .um-head .nm-modal-title { margin: 0; padding: 0; font-family: 'Playfair Display', serif; font-size: 24px; font-weight: 700; line-height: 1.2; letter-spacing: 0.015em; color: #fff; }
.um-sub { margin: 3px 0 0; font-size: 13.5px; color: rgba(255, 255, 255, 0.85); }
.upload-modal .nm-modal-x.um-x { position: relative; inset: auto; flex-shrink: 0; width: 38px; height: 38px; margin: 0; border-radius: 11px; border: 1px solid rgba(255, 255, 255, 0.3); background: rgba(0, 56, 42, 0.55); color: #fff; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; backdrop-filter: blur(6px); }
.upload-modal .um-x:hover { background: rgba(0, 56, 42, 0.8); }
.upload-modal .um-x:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }
.um-body { flex: 1; min-height: 0; overflow-y: auto; padding: 20px 24px 22px; }

.field-label { display: block; margin: 0 0 6px; font-size: 13px; font-weight: 700; color: #22362c; }
.optional { font-weight: 500; color: #8a9a91; }
.field-label.um-step-label { display: flex; align-items: center; gap: 9px; margin: 20px 0 10px; font-size: 14px; font-weight: 800; color: #0e3a2c; }
.um-body > .um-step-label:first-child { margin-top: 0; }
.um-step-label span { width: 22px; height: 22px; border-radius: 7px; background: #004d3a; color: #efbf04; display: inline-flex; align-items: center; justify-content: center; font-size: 12px; }
.field-input, .field-textarea { width: 100%; margin-bottom: 12px; padding: 12px 14px; border: 1.5px solid #c9d8cf; border-radius: 12px; background: #fff; font-family: inherit; font-size: 14px; color: #14261e; outline: none; }
.field-input:focus, .field-textarea:focus { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.field-input::placeholder, .field-textarea::placeholder { color: #9aaaa1; }
.field-textarea { resize: vertical; }

/* type cards */
.type-selector { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 0; padding: 0; background: none; border-radius: 0; }
.type-option { position: relative; display: flex; flex-direction: column; align-items: flex-start; gap: 3px; padding: 12px; border: 1.5px solid #dce8e0; border-radius: 14px; background: #fff; font-family: inherit; text-align: left; color: #0e3a2c; cursor: pointer; transition: border-color 0.15s, background 0.15s; }
.type-option:hover { border-color: #9dc3ae; }
.ut-ico { width: 34px; height: 34px; margin-bottom: 6px; border-radius: 10px; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.type-option strong { font-size: 14px; color: #0e3a2c; }
.type-option small { font-size: 11.5px; line-height: 1.35; color: #7a8a80; }
.type-option.active { border-color: #004d3a; background: #f1f8f4; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.08); }
.type-option.active .ut-ico { background: #004d3a; color: #efbf04; }
.ut-chk { position: absolute; top: 10px; right: 10px; width: 18px; height: 18px; border-radius: 50%; background: #004d3a; color: #fff; display: inline-flex; align-items: center; justify-content: center; }
.ut-chk .ic { display: block; }
.type-option:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }

/* file dropzone */
.file-pick { position: relative; display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 22px 16px; border: 1.5px dashed #9dc3ae; border-radius: 16px; background: #f7faf8; text-align: center; cursor: pointer; transition: background 0.15s, border-color 0.15s; }
.file-pick:hover { background: #f1f8f4; border-color: #1f9d55; }
.file-pick:focus-within { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.file-pick.picked { border-style: solid; border-color: #1f9d55; background: #f1f8f4; }
.file-input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.um-dico { width: 48px; height: 48px; margin-bottom: 8px; border-radius: 14px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.um-dico .ic { display: block; }
.file-btn { padding: 0; background: none; font-size: 14.5px; font-weight: 800; color: #004d3a; }
.file-name { max-width: 100%; font-size: 13px; color: #0e3a2c; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-name.is-empty { color: #6b7d73; font-weight: 400; }
.file-hint { margin-top: 8px; padding: 3px 10px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px #e3ece6; font-size: 12px; font-weight: 600; color: #4a5a52; }
.upload-modal .form-error { margin: 14px 0 0; }

/* note */
.upload-note { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 18px 0 0; padding: 12px 14px; border-radius: 14px; background: #fffbea; border: 1px solid #f3e2a0; }
.um-flow { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; background: #fff; font-size: 12px; font-weight: 800; color: #8a6500; }
.um-flow.on { background: #004d3a; color: #fff; }
.um-arrow { display: inline-flex; color: #c49102; }
.um-arrow .ic { display: block; }
.upload-note p { flex-basis: 100%; margin: 2px 0 0; font-size: 13px; line-height: 1.5; color: #6b5a1e; }

/* footer */
.upload-modal .um-foot { flex-shrink: 0; display: flex; justify-content: flex-end; gap: 10px; margin: 0; padding: 14px 24px; border-top: 1px solid #eef2ef; background: #f7faf8; }
.um-foot .nm-btn-soft, .um-foot .nm-btn-dark { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 44px; padding: 0 20px; border-radius: 12px; font-family: inherit; font-size: 14px; font-weight: 800; cursor: pointer; }
.um-foot .nm-btn-soft { background: #fff; border: 1px solid #dce8e0; color: #004d3a; }
.um-foot .nm-btn-dark { background: #004d3a; border: 1px solid #004d3a; color: #fff; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.um-foot .nm-btn-dark:hover:not(:disabled) { background: #00382a; }
.um-foot .nm-btn-dark:disabled { opacity: 0.45; cursor: not-allowed; box-shadow: none; }

@media (max-width: 640px) {
  .client-grid { grid-template-columns: minmax(0, 1fr); }
  .nm-modal.upload-modal { max-height: calc(100dvh - 24px); border-radius: 22px; }
  .um-head { padding: 18px; }
  .um-hico { width: 42px; height: 42px; }
  .upload-modal .um-head .nm-modal-title { font-size: 21px; }
  .um-plate { width: 150px; height: 150px; right: -50px; }
  .um-body { padding: 16px 18px; }
  .type-selector { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .upload-modal .um-foot { padding: 12px 18px 16px; }
  .um-foot > button { flex: 1; }
}

/* search: 10px corners like the other pages */
.nm-search.rs-search, .rs-search, .rs-search input { border-radius: 10px !important; }
</style>