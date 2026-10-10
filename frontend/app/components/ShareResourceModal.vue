<template>
  <!-- RND picks which of their confirmed clients get a resource. Uploading
       shares it with nobody; clients only see what's shared here. Ticking
       adds a client (they get a notification), unticking stops sharing. -->
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="emit('close')">
      <div class="nm-modal sr-box" role="dialog" aria-modal="true" :aria-label="`Share ${resource.title}`">
        <h3 class="nm-modal-title">Share Resource</h3>
        <p class="nm-modal-text">Choose which of your clients receive <strong>{{ resource.title }}</strong>. They'll be notified and can view or download it from their Resources page.</p>

        <p v-if="loading" class="nm-muted">Loading your clients…</p>
        <p v-else-if="loadError" class="nm-field-error">{{ loadError }}</p>

        <div v-else-if="!rows.length" class="nm-empty">
          <Users :size="26" />
          <p>You don't have any confirmed clients yet.</p>
          <p class="nm-hint">Clients appear here once you confirm their first booking.</p>
        </div>

        <template v-else>
          <div class="sr-tools">
            <div class="nm-search sr-search">
              <Search :size="15" />
              <input v-model="search" type="text" placeholder="Search clients…" />
            </div>
            <button type="button" class="sr-link" @click="toggleAll">{{ allVisibleSelected ? 'Clear all' : 'Select all' }}</button>
          </div>

          <ul class="sr-list">
            <li v-for="row in visibleRows" :key="row.relationship_id">
              <label class="sr-row">
                <input v-model="selected" type="checkbox" :value="row.relationship_id" />
                <img v-if="row.client.profile_photo" :src="row.client.profile_photo" alt="" class="nm-avatar sr-avatar" />
                <span v-else class="nm-avatar sr-avatar">{{ initials(row.client.full_name) }}</span>
                <span class="sr-name">
                  {{ row.client.full_name }}
                  <span class="sr-email">{{ row.client.email }}</span>
                </span>
                <span v-if="row.shared" class="nm-pill green">Shared</span>
              </label>
            </li>
            <li v-if="!visibleRows.length" class="nm-muted sr-none">No clients match "{{ search }}".</li>
          </ul>

          <p class="nm-hint">{{ summary }}</p>
        </template>

        <p v-if="saveError" class="nm-field-error">{{ saveError }}</p>

        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="emit('close')">Cancel</button>
          <button
            v-if="rows.length"
            type="button"
            class="nm-btn-dark"
            :disabled="saving || !hasChanges"
            @click="save"
          ><Share2 :size="14" /> {{ saving ? 'Saving…' : 'Save' }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { Search, Share2, Users } from 'lucide-vue-next'

const props = defineProps({ resource: { type: Object, required: true } })
const emit = defineEmits(['close', 'saved'])

const { get, post, del } = useApi()

const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const saveError = ref('')
const rows = ref([])
const selected = ref([])
const search = ref('')

const originallyShared = computed(() => rows.value.filter(r => r.shared).map(r => r.relationship_id))
const toAdd = computed(() => selected.value.filter(id => !originallyShared.value.includes(id)))
const toRemove = computed(() => originallyShared.value.filter(id => !selected.value.includes(id)))
const hasChanges = computed(() => toAdd.value.length > 0 || toRemove.value.length > 0)

const visibleRows = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return rows.value
  return rows.value.filter(r => r.client.full_name.toLowerCase().includes(q) || r.client.email.toLowerCase().includes(q))
})
const allVisibleSelected = computed(() =>
  visibleRows.value.length > 0 && visibleRows.value.every(r => selected.value.includes(r.relationship_id))
)

const summary = computed(() => {
  const n = selected.value.length
  const parts = [n ? `${n} client${n > 1 ? 's' : ''} selected` : 'No clients selected']
  if (toAdd.value.length) parts.push(`${toAdd.value.length} will be notified`)
  if (toRemove.value.length) parts.push(`${toRemove.value.length} will lose access`)
  return parts.join(' · ')
})

function initials(name) {
  return (name || '?').split(' ').filter(Boolean).slice(0, 2).map(w => w[0].toUpperCase()).join('')
}

function toggleAll() {
  const ids = visibleRows.value.map(r => r.relationship_id)
  selected.value = allVisibleSelected.value
    ? selected.value.filter(id => !ids.includes(id))
    : [...new Set([...selected.value, ...ids])]
}

async function save() {
  saving.value = true
  saveError.value = ''
  try {
    if (toAdd.value.length) {
      await post(`/rnd/resources/${props.resource.id}/share/`, { relationship_ids: toAdd.value })
    }
    for (const id of toRemove.value) {
      await del(`/rnd/resources/${props.resource.id}/share/${id}/`)
    }
    emit('saved', { sharedCount: selected.value.length, added: toAdd.value.length, removed: toRemove.value.length })
  } catch (error) {
    saveError.value = error?.data?.relationship_ids?.[0] || error?.data?.detail || 'Could not update sharing. Please try again.'
  } finally {
    saving.value = false
  }
}

function onKey(e) { if (e.key === 'Escape') emit('close') }

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  try {
    rows.value = await get(`/rnd/resources/${props.resource.id}/share/`)
    selected.value = rows.value.filter(r => r.shared).map(r => r.relationship_id)
  } catch {
    loadError.value = 'Could not load your clients. Please try again.'
  } finally {
    loading.value = false
  }
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.sr-box { max-width: 500px; }
.sr-tools { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }
.sr-search { max-width: none; min-width: 0; }
.sr-link { background: none; border: none; color: #1a3a1a; font-size: 0.8rem; font-weight: 600; cursor: pointer; text-decoration: underline; white-space: nowrap; font-family: inherit; padding: 0; }

.sr-list { list-style: none; margin: 0 0 10px; padding: 0; border: 1px solid #eceeec; border-radius: 10px; max-height: 300px; overflow-y: auto; }
.sr-list li + li { border-top: 1px solid #f2f4f2; }
.sr-row { display: flex; align-items: center; gap: 12px; padding: 10px 14px; cursor: pointer; }
.sr-row:hover { background: #f7f9f7; }
.sr-row input { width: 16px; height: 16px; accent-color: #163a1c; flex-shrink: 0; cursor: pointer; }
.sr-avatar { width: 32px; height: 32px; font-size: 0.72rem; }
.sr-name { flex: 1; min-width: 0; font-size: 0.86rem; font-weight: 600; color: #1a3a1a; overflow-wrap: anywhere; }
.sr-email { display: block; font-size: 0.74rem; font-weight: 400; color: #8a9a8a; }
.sr-none { padding: 14px; }

@media (max-width: 640px) {
  .nm-modal-actions > * { flex: 1; }
}
</style>
