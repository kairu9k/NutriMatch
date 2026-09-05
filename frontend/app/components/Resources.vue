<template>
  <div>
    <!-- PAGE HEADER -->
    <div class="page-header">
      <div>
        <h1 class="page-title">Resources</h1>
        <p class="page-subtitle">Upload nutrition education materials for your patients.</p>
      </div>
      <button class="upload-btn" @click="uploadResource"><Plus :size="16" /> Upload Resource</button>
    </div>

    <!-- RESOURCE TABLE -->
    <div class="table-wrap" v-if="resources.length">
      <table class="resource-table">
        <thead>
          <tr>
            <th>TITLE</th>
            <th>TYPE</th>
            <th>STATUS</th>
            <th>UPLOADED</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in resources" :key="r.id">
            <td class="title-cell">
              <div class="resource-icon" :class="'icon-' + r.type.toLowerCase()">
                <component :is="iconFor(r.type)" :size="16" />
              </div>
              <div>
                <p class="resource-title">{{ r.title }}</p>
                <p class="resource-desc">{{ r.description }}</p>
              </div>
            </td>
            <td><span class="type-pill" :class="'type-' + r.type.toLowerCase()">{{ r.type }}</span></td>
            <td><span class="status-pill" :class="r.status === 'Active' ? 'status-active' : 'status-inactive'">{{ r.status }}</span></td>
            <td class="uploaded-cell">{{ r.uploadedAt }}</td>
            <td class="menu-cell">
              <button class="menu-btn" @click="toggleMenu(r.id)"><MoreHorizontal :size="18" /></button>
              <div v-if="openMenuId === r.id" class="menu-dropdown">
                <button @click="editResource(r)">Edit</button>
                <button @click="toggleStatus(r)">{{ r.status === 'Active' ? 'Mark Inactive' : 'Mark Active' }}</button>
                <button class="menu-danger" @click="deleteResource(r)">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="empty-state">
      <BookOpen :size="28" class="empty-icon" />
      <p class="empty-title">No resources uploaded yet</p>
      <p class="empty-desc">Click "Upload Resource" to share your first guide, video, or article with patients.</p>
    </div>
  </div>
</template>

<script setup>
import { Plus, MoreHorizontal, BookOpen, FileText, PlayCircle, FileEdit, Link as LinkIcon } from 'lucide-vue-next'
import { db } from '~/mock/mockDatabase'

definePageMeta({ layout: 'dashboard', title: 'Resources' })

// Deep-copy so local edits (status toggle, delete) don't mutate the shared mock db
const resources = reactive(JSON.parse(JSON.stringify(db.resources)))

const openMenuId = ref(null)
function toggleMenu(id) {
  openMenuId.value = openMenuId.value === id ? null : id
}

function iconFor(type) {
  if (type === 'PDF') return FileText
  if (type === 'Video') return PlayCircle
  if (type === 'Article') return FileEdit
  if (type === 'Link') return LinkIcon
  return FileText
}

function uploadResource() {
  // TODO: wire up to a real file picker / upload flow
  console.log('Upload resource clicked')
}
function editResource(r) {
  console.log('Edit', r)
  openMenuId.value = null
}
function toggleStatus(r) {
  r.status = r.status === 'Active' ? 'Inactive' : 'Active'
  openMenuId.value = null
}
function deleteResource(r) {
  const idx = resources.findIndex(x => x.id === r.id)
  if (idx > -1) resources.splice(idx, 1)
  openMenuId.value = null
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #1a3a1a; margin: 0 0 4px; }
.page-subtitle { font-size: 0.88rem; color: #8a9a8a; margin: 0; }

.upload-btn {
  display: flex; align-items: center; gap: 6px;
  background: #D4A017; border: none; color: #1a3a1a;
  padding: 11px 20px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; cursor: pointer; white-space: nowrap;
}
.upload-btn:hover { background: #c4920f; }

.table-wrap { background: #fff; border-radius: 12px; border: 1px solid #eceeec; overflow: hidden; }

.resource-table { width: 100%; border-collapse: collapse; }
.resource-table th {
  text-align: left; font-size: 0.68rem; letter-spacing: 0.05em; color: #9aaa9a;
  background: #f5f7f4; padding: 14px 20px;
}
.resource-table td { padding: 16px 20px; border-top: 1px solid #f2f4f2; font-size: 0.85rem; vertical-align: middle; }

.title-cell { display: flex; align-items: center; gap: 12px; }
.resource-icon {
  width: 34px; height: 34px; border-radius: 8px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
}
.icon-pdf { background: #fbe1de; color: #c0483a; }
.icon-video { background: #e3edfc; color: #3b6fd6; }
.icon-article { background: #e6f4e6; color: #2e7d32; }
.icon-link { background: #fdf1d6; color: #b8860b; }

.resource-title { font-weight: 700; color: #1a3a1a; margin: 0; }
.resource-desc { font-size: 0.78rem; color: #9aaa9a; margin: 2px 0 0; }

.type-pill { font-size: 0.7rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; white-space: nowrap; }
.type-pdf { background: #fbe1de; color: #c0483a; }
.type-video { background: #e3edfc; color: #3b6fd6; }
.type-article { background: #eef0ee; color: #4a5a4a; }
.type-link { background: #fdf1d6; color: #b8860b; }

.status-pill { font-size: 0.7rem; font-weight: 700; padding: 3px 10px; border-radius: 20px; white-space: nowrap; }
.status-active { background: #e6f4e6; color: #2e7d32; }
.status-inactive { background: #eef0ee; color: #8a9a8a; }

.uploaded-cell { color: #9aaa9a; white-space: nowrap; }

.menu-cell { position: relative; text-align: right; width: 40px; }
.menu-btn {
  background: none; border: none; color: #9aaa9a; cursor: pointer;
  display: flex; align-items: center; justify-content: center; padding: 4px; margin-left: auto;
}
.menu-btn:hover { color: #4a5a4a; }

.menu-dropdown {
  position: absolute; right: 20px; top: 100%; z-index: 10;
  background: #fff; border: 1px solid #eceeec; border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08); display: flex; flex-direction: column; min-width: 140px; overflow: hidden;
}
.menu-dropdown button {
  background: none; border: none; text-align: left; padding: 10px 14px;
  font-size: 0.82rem; color: #3a4a3a; cursor: pointer;
}
.menu-dropdown button:hover { background: #f4f6f4; }
.menu-danger { color: #c0483a !important; }

.empty-state {
  text-align: center; padding: 56px 24px; background: #fff; border-radius: 12px; border: 1px solid #eceeec;
}
.empty-icon { color: #c8d0c8; margin-bottom: 12px; }
.empty-title { font-size: 0.95rem; font-weight: 700; color: #4a5a4a; margin: 0 0 6px; }
.empty-desc { font-size: 0.82rem; color: #9aaa9a; margin: 0; }
</style>