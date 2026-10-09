<template>
  <div class="ncp-page">
    <div v-if="loadError" class="form-error">{{ loadError }}</div>

    <div class="toolbar">
      <div class="search-box-wide">
        <Search :size="16" class="search-icon" />
        <input v-model="search" type="text" placeholder="Search by patient name....." />
      </div>
      <select v-model="statusFilter" class="filter-select">
        <option value="All Status">All Status</option>
        <option>Finalized</option>
        <option>In Progress</option>
      </select>
      <button class="new-record-btn" @click="openPatientPicker">
        <Plus :size="15" /> New NCP Record
      </button>
    </div>

    <div class="history-section">
      <h3 class="history-title">NCP Records</h3>
      <div class="table-wrap">
        <table class="history-table">
          <thead>
            <tr>
              <th>PATIENT</th>
              <th>RECORD</th>
              <th>PHASE</th>
              <th>CREATED</th>
              <th>STATUS</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="h in filteredRecords" :key="h.id" class="clickable-row" @click="openRecord(h)">
              <td class="patient-cell">
                <div class="history-avatar">{{ h.initials }}</div>
                <p class="history-name">{{ h.client_name }}</p>
              </td>
              <td>{{ h.is_follow_up ? 'Follow-up' : 'Initial' }}</td>
              <td>{{ h.phaseLabel }}</td>
              <td>{{ formatDateTime(h.created_at) }}</td>
              <td><span class="status-pill" :class="h.status === 'completed' ? 'pill-green' : 'pill-gold'">{{ h.displayStatus }}</span></td>
            </tr>
          </tbody>
        </table>
        <p v-if="isLoading" class="empty-note table-empty">Loading…</p>
        <p v-else-if="!filteredRecords.length" class="empty-note table-empty">No NCP records match your filters yet.</p>
      </div>
    </div>

    <!-- PATIENT PICKER for "New NCP Record" -->
    <div v-if="showPicker" class="modal-overlay" @click.self="showPicker = false">
      <div class="picker-box">
        <h2 class="picker-title">New NCP Record</h2>
        <p class="picker-sub">Choose the patient this record is for.</p>
        <p v-if="!patients.length" class="empty-note">You have no active patients yet.</p>
        <button v-for="p in patients" :key="p.id" class="picker-row" @click="startRecord(p)">
          <span class="history-avatar">{{ initialsFor(p.name) }}</span>
          <span class="picker-name">{{ p.name }}</span>
          <span v-if="draftByRelationship[p.id]" class="status-pill pill-gold">Continue unfinished</span>
        </button>
        <button class="picker-cancel" @click="showPicker = false">Cancel</button>
      </div>
    </div>

    <!-- The record form (shared with Client Detail's NCP Records tab) -->
    <NcpRecordModal
      v-if="modal"
      :key="`${modal.mode}-${modal.relationshipId}-${modal.recordId}`"
      :relationship-id="modal.relationshipId"
      :patient-name="modal.patientName"
      :mode="modal.mode"
      :record-id="modal.recordId"
      @close="modal = null"
      @changed="loadRecords"
      @continue="modal = { ...modal, mode: 'edit', recordId: null }"
    />
  </div>
</template>

<script setup>
// NCP Records (sidebar): every NCP record across the RND's patients.
// Clicking a record opens it read-only; new records are started here (pick
// a patient) or from that patient's Client Detail → NCP Records tab. The
// per-patient view lives on Client Detail now — old ?relationship= links
// are forwarded there.
import { computed, onMounted, ref } from 'vue'
import { Plus, Search } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'NCP Records' })

const route = useRoute()
const { get } = useApi()

const records = ref([])
const isLoading = ref(true)
const loadError = ref('')
const search = ref('')
const statusFilter = ref('All Status')
const modal = ref(null) // { relationshipId, recordId, patientName, mode }

const PHASES = ['Assessment', 'Diagnosis', 'Intervention', 'Monitoring']
function phaseLabelFor(r) {
  if (r.status === 'completed') return r.is_follow_up ? 'Monitoring' : 'Intervention'
  const done = [!!(r.weight_kg && r.height_cm), !!r.pes_problem, !!r.diet_prescription]
  const next = done.findIndex(d => !d)
  return next === -1 ? (r.is_follow_up ? 'Monitoring' : 'Intervention') : PHASES[next]
}
function initialsFor(name) {
  return (name || '').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()
}
function formatDateTime(iso) {
  return iso ? new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }) : ''
}

const filteredRecords = computed(() => {
  const q = search.value.trim().toLowerCase()
  return records.value
    .map(r => ({
      ...r,
      initials: initialsFor(r.client_name),
      phaseLabel: phaseLabelFor(r),
      displayStatus: r.status === 'completed' ? 'Finalized' : 'In Progress',
    }))
    .filter(r => (!q || r.client_name.toLowerCase().includes(q))
      && (statusFilter.value === 'All Status' || r.displayStatus === statusFilter.value))
})
const draftByRelationship = computed(() =>
  Object.fromEntries(records.value.filter(r => r.status === 'draft').map(r => [r.relationship_id, r]))
)

async function loadRecords() {
  loadError.value = ''
  try {
    records.value = await get('/rnd/ncp/drafts/?status=all')
  } catch {
    loadError.value = 'Could not load your NCP records. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

function openRecord(r) {
  modal.value = { relationshipId: r.relationship_id, recordId: r.id, patientName: r.client_name, mode: 'view' }
}

/* ---------- New NCP Record: pick a patient ---------- */
const showPicker = ref(false)
const patients = ref([])
async function openPatientPicker() {
  showPicker.value = true
  try {
    const rels = await get('/rnd/relationships/active/')
    patients.value = rels.map(r => ({ id: r.id, name: `${r.client.first_name} ${r.client.last_name}` }))
  } catch {
    patients.value = []
  }
}
function startRecord(p) {
  showPicker.value = false
  modal.value = { relationshipId: p.id, recordId: null, patientName: p.name, mode: 'edit' }
}

onMounted(() => {
  // Old per-patient links (/ncp-records?relationship=<id>) → Client Detail.
  if (route.query.relationship) {
    navigateTo(`/client-detail/${route.query.relationship}?tab=ncp`, { replace: true })
    return
  }
  loadRecords()
})
</script>

<style scoped>
* { box-sizing: border-box; }

.ncp-page { font-family: 'Inter', sans-serif; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.empty-note { font-size: 0.85rem; color: #9aaa9a; }

.toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.search-box-wide {
  flex: 1; min-width: 220px; display: flex; align-items: center; gap: 10px; background: #fff;
  border: 1.0px solid #a8b3a8; border-radius: 10px; padding: 11px 16px;
}
.search-box-wide input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; color: #4a5a4a; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }
.filter-select { border: 1px solid #e5e8e5; border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; color: #4a5a4a; background: #fff; cursor: pointer; }
.new-record-btn {
  display: flex; align-items: center; gap: 6px; background: #14301a; color: #fff; border: none;
  border-radius: 8px; padding: 11px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; white-space: nowrap;
}

.history-section { margin-top: 8px; }
.history-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 14px; }
.table-wrap { background: #fff; border-radius: 14px; border: 1px solid #eceeec; overflow-x: auto; }
.history-table { width: 100%; border-collapse: collapse; }
.history-table th { text-align: left; font-size: 0.7rem; letter-spacing: 0.05em; color: #9aaa9a; font-weight: 700; padding: 14px 16px 10px; border-bottom: 1px solid #eceeec; }
.history-table td { padding: 14px 16px; border-bottom: 1px solid #f2f4f2; font-size: 0.86rem; color: #2a2a2a; }
.history-table tr:last-child td { border-bottom: none; }
.clickable-row { cursor: pointer; transition: background 0.1s ease; }
.clickable-row:hover { background: #f7f9f7; }
.patient-cell { display: flex; align-items: center; gap: 10px; }
.history-avatar {
  width: 30px; height: 30px; border-radius: 50%; background: #eceeec; color: #4a5a4a; display: flex;
  align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; flex-shrink: 0;
}
.history-name { font-weight: 700; color: #1a3a1a; margin: 0; }
.status-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-gold { background: #fdf1d6; color: #b8860b; }
.table-empty { padding: 40px 16px; text-align: center; margin: 0; }

.modal-overlay {
  position: fixed; inset: 0; background: rgba(20,30,20,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 100; padding: 20px;
}
.picker-box { background: #fff; border-radius: 16px; width: 100%; max-width: 420px; max-height: 80vh; overflow-y: auto; padding: 24px; }
.picker-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0 0 4px; }
.picker-sub { font-size: 0.82rem; color: #8a9a8a; margin: 0 0 16px; }
.picker-row {
  display: flex; align-items: center; gap: 10px; width: 100%; background: #fff; border: 1px solid #eceeec;
  border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; cursor: pointer; text-align: left;
}
.picker-row:hover { background: #f7f9f7; border-color: #d5dad5; }
.picker-name { flex: 1; font-weight: 600; color: #1a3a1a; font-size: 0.88rem; }
.picker-cancel {
  width: 100%; margin-top: 8px; border: 1px solid #d5dad5; background: #fff; color: #4a5a4a;
  border-radius: 8px; padding: 10px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
</style>
