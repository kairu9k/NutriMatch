<template>
  <div class="resources-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Resources</h1>
        <p class="page-sub">Share nutrition education materials with your patients.</p>
      </div>
      <button class="add-btn" type="button" @click="showForm = !showForm">
        <Plus :size="15" /> Add Resource
      </button>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

    <div v-if="showForm" class="surface form-card">
      <h3 class="surface-title">Add a Resource Link</h3>
      <p class="form-note">
        Only external link resources can be added right now — PDF/video file upload isn't available yet
        (no file storage has been set up for this project).
      </p>

      <label class="field-label">Title</label>
      <input v-model="form.title" type="text" class="field-input" placeholder="e.g. DOH Pinggang Pinoy Guide" />

      <label class="field-label">Description <span class="optional">(optional)</span></label>
      <textarea v-model="form.description" class="field-input" rows="2" placeholder="Brief summary for your patients..."></textarea>

      <label class="field-label">URL</label>
      <input v-model="form.url" type="url" class="field-input" placeholder="https://..." />

      <label class="checkbox-row">
        <input v-model="form.is_active" type="checkbox" />
        Make visible to patients immediately
      </label>

      <div class="form-actions">
        <button class="ghost-btn" type="button" @click="showForm = false">Cancel</button>
        <button class="submit-btn" type="button" :disabled="!canSubmit || isSubmitting" @click="submitResource">
          {{ isSubmitting ? 'Adding…' : 'Add Resource' }}
        </button>
      </div>
    </div>

    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else-if="resources.length">
      <div class="surface list-surface">
        <div class="resource-row header-row">
          <span class="col-icon"></span>
          <span class="col-title">Title</span>
          <span class="col-type">Type</span>
          <span class="col-status">Status</span>
          <span class="col-date">Added</span>
          <span class="col-action"></span>
        </div>
        <div v-for="resource in resources" :key="resource.id" class="resource-row">
          <div class="resource-icon" :class="typeClass(resource.type)">
            <component :is="typeIcon(resource.type)" :size="16" />
          </div>
          <div class="col-title">
            <p class="resource-title">{{ resource.title }}</p>
            <p v-if="resource.description" class="resource-desc">{{ resource.description }}</p>
          </div>
          <div class="col-type"><span class="badge-pill" :class="typeClass(resource.type)">{{ typeLabel(resource.type) }}</span></div>
          <div class="col-status"><span class="badge-pill" :class="resource.is_active ? 'success' : 'neutral'">{{ resource.is_active ? 'Active' : 'Inactive' }}</span></div>
          <div class="col-date">{{ timeAgo(resource.created_at) }}</div>
          <div class="col-action">
            <button class="toggle-btn" type="button" :disabled="busyId === resource.id" @click="toggleActive(resource)">
              {{ resource.is_active ? 'Deactivate' : 'Activate' }}
            </button>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="empty-state">
      <div class="empty-icon"><FileText :size="28" /></div>
      <p class="empty-title">No resources yet</p>
      <p class="empty-desc">Add a link to nutrition education material for your patients.</p>
    </div>
  </div>
</template>

<script setup>
import { Plus, FileText, PlayCircle, Link2, FileType } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Resources' })

const { get, post, patch } = useApi()

const isLoading = ref(true)
const isSubmitting = ref(false)
const errorMessage = ref('')
const resources = ref([])
const showForm = ref(false)
const busyId = ref(null)

const form = reactive({ title: '', description: '', url: '', is_active: true })
const canSubmit = computed(() => form.title.trim() && form.url.trim())

const TYPE_ICONS = { pdf: FileText, video: PlayCircle, article: FileType, link: Link2 }
const TYPE_LABELS = { pdf: 'PDF', video: 'Video', article: 'Article', link: 'Link' }
const TYPE_CLASSES = { pdf: 'danger', video: 'info', article: 'neutral', link: 'gold' }

function typeIcon(type) { return TYPE_ICONS[type] || FileText }
function typeLabel(type) { return TYPE_LABELS[type] || type }
function typeClass(type) { return TYPE_CLASSES[type] || 'neutral' }

function timeAgo(iso) {
  const seconds = Math.floor((Date.now() - new Date(iso)) / 1000)
  const units = [['year', 31536000], ['month', 2592000], ['day', 86400], ['hour', 3600], ['minute', 60]]
  for (const [label, secs] of units) {
    const value = Math.floor(seconds / secs)
    if (value >= 1) return `${value} ${label}${value > 1 ? 's' : ''} ago`
  }
  return 'just now'
}

async function loadResources() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    resources.value = await get('/rnd/resources/')
  } catch {
    errorMessage.value = 'Could not load your resources. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

async function submitResource() {
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    await post('/rnd/resources/', { title: form.title, description: form.description || undefined, type: 'link', url: form.url, is_active: form.is_active })
    form.title = ''; form.description = ''; form.url = ''; form.is_active = true
    showForm.value = false
    await loadResources()
  } catch (error) {
    errorMessage.value = error?.data?.non_field_errors?.[0] || error?.data?.url?.[0] || 'Could not add this resource. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

async function toggleActive(resource) {
  busyId.value = resource.id
  try {
    await patch(`/rnd/resources/${resource.id}/`, { is_active: !resource.is_active })
    resource.is_active = !resource.is_active
  } catch {
    errorMessage.value = 'Could not update this resource. Please try again.'
  } finally {
    busyId.value = null
  }
}

onMounted(loadResources)
</script>

<style scoped>
* { box-sizing: border-box; }

.resources-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.add-btn {
  display: flex; align-items: center; gap: 6px; background: #D4A017; color: #1a3a1a;
  border: none; border-radius: 8px; padding: 10px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; white-space: nowrap;
}

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; }
.form-card { padding: 22px; margin-bottom: 20px; }
.surface-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 8px; }
.form-note { font-size: 0.82rem; color: #8a9a8a; margin: 0 0 16px; line-height: 1.5; }

.field-label { display: block; font-size: 0.85rem; font-weight: 600; color: #1a3a1a; margin: 14px 0 8px; }
.field-label:first-of-type { margin-top: 0; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px;
  font-size: 0.88rem; color: #2a2a2a; font-family: inherit;
}
.field-input:focus { outline: none; border-color: #D4A017; }

.checkbox-row { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: #4a5a4a; margin-top: 16px; }

.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.ghost-btn { background: none; border: none; color: #8a9a8a; font-size: 0.85rem; font-weight: 600; cursor: pointer; padding: 10px 14px; }
.submit-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 10px 20px; font-weight: 700; font-size: 0.85rem; cursor: pointer;
}
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.list-surface { overflow: hidden; overflow-x: auto; }
.resource-row {
  display: flex; align-items: center; gap: 14px; padding: 14px 18px; border-bottom: 1px solid #f0f0e6; min-width: 640px;
}
.resource-row:last-child { border-bottom: none; }
.header-row {
  background: #eef3ec; font-size: 0.7rem; font-weight: 700; color: #8a9a8a; text-transform: uppercase; letter-spacing: 0.04em;
}
.col-icon { width: 38px; flex-shrink: 0; }
.col-title { flex: 1; min-width: 180px; }
.col-type { width: 90px; flex-shrink: 0; }
.col-status { width: 90px; flex-shrink: 0; }
.col-date { width: 110px; flex-shrink: 0; font-size: 0.8rem; color: #8a9a8a; }
.col-action { width: 100px; flex-shrink: 0; text-align: right; }

.resource-icon {
  width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.resource-icon.danger { background: rgba(192,57,43,0.1); color: #c0392b; }
.resource-icon.info { background: rgba(47,111,168,0.1); color: #2f6fa8; }
.resource-icon.gold { background: rgba(212,160,23,0.14); color: #b8860b; }
.resource-icon.neutral { background: #eef3ec; color: #1e4a26; }

.resource-title { font-weight: 600; color: #1a3a1a; font-size: 0.88rem; margin: 0; }
.resource-desc { font-size: 0.76rem; color: #8a9a8a; margin: 2px 0 0; }

.badge-pill { font-size: 0.7rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.badge-pill.danger { background: #fdecec; color: #a12525; }
.badge-pill.info { background: #e3edf7; color: #2f6fa8; }
.badge-pill.gold { background: #faead0; color: #b8860b; }
.badge-pill.neutral { background: #eceeec; color: #7a8a7a; }
.badge-pill.success { background: #e6efe0; color: #3a6b3a; }

.toggle-btn { background: none; border: none; color: #6a7a6a; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
.toggle-btn:disabled { opacity: 0.6; cursor: not-allowed; }

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
</style>
