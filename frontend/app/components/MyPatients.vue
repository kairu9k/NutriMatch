<template>
  <div class="my-patients-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Patients</h1>
        <p class="page-sub">Manage your active and pending client relationships.</p>
      </div>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <template v-else>
      <!-- TOOLBAR: SEARCH + FILTER TABS -->
      <div v-if="patients.length" class="toolbar">
        <div class="search-box-wide">
          <Search :size="16" class="search-icon" />
          <input v-model="search" type="text" placeholder="Search patients..." />
        </div>
        <div class="filter-tabs">
          <button
            v-for="f in filters"
            :key="f.label"
            class="filter-tab"
            :class="{ active: activeFilter === f.label }"
            @click="activeFilter = f.label"
          >
            {{ f.label }} ({{ f.count }})
          </button>
        </div>
      </div>

      <div v-if="patients.length" class="patient-table-wrap">
        <table v-if="pagedPatients.length" class="patient-table">
          <thead>
            <tr>
              <th>PATIENT</th>
              <th>CONDITION</th>
              <th>STATUS</th>
              <th>LAST VISIT</th>
              <th>NEXT APPOINTMENT</th>
              <th>NCP STATUS</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in pagedPatients" :key="p.id">
              <td class="patient-cell">
                <div class="patient-avatar" :class="{ 'avatar-muted': p.status === 'discharged' }" :style="p.status !== 'discharged' ? { background: colorForId(p.client.id) } : {}">
                  {{ initialsFor(p.client) }}
                </div>
                <span class="patient-name" :class="{ 'name-muted': p.status === 'discharged' }">{{ p.client.first_name }} {{ p.client.last_name }}</span>
              </td>
              <td :class="{ 'text-muted': p.status === 'discharged' }">{{ p.condition || '—' }}</td>
              <td><span class="status-pill" :class="statusClass(p.status)">{{ statusLabel(p.status) }}</span></td>
              <td :class="{ 'text-muted': p.status === 'discharged' }">{{ formatDate(p.last_visit) }}</td>
              <td :class="{ 'text-muted': p.status === 'discharged' }">{{ formatDate(p.next_appointment) }}</td>
              <td><span class="ncp-pill" :class="ncpClass(p.ncp_status)">{{ ncpLabel(p.ncp_status) }}</span></td>
              <td class="action-cell">
                <NuxtLink v-if="p.status === 'pending'" to="/appointments" class="accept-btn">Review Booking</NuxtLink>
                <NuxtLink v-else :to="`/client-detail/${p.id}`" class="chart-btn">View Chart</NuxtLink>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty-text">No patients match your search or filter.</p>
      </div>

      <!-- PAGINATION -->
      <div v-if="filteredPatients.length" class="pagination-row">
        <span class="pagination-label">Showing {{ pagedPatients.length }} of {{ filteredPatients.length }} patients</span>
        <div class="pagination-controls">
          <button class="page-btn" :disabled="page === 1" @click="page--"><ChevronLeft :size="14" /> Prev</button>
          <button class="page-btn page-btn-primary" :disabled="page >= totalPages" @click="page++">Next <ChevronRight :size="14" /></button>
        </div>
      </div>

      <div v-else-if="!patients.length" class="empty-state">
        <div class="empty-icon"><Users :size="28" /></div>
        <p class="empty-title">No patients yet</p>
        <p class="empty-desc">Once clients request to work with you, they'll show up here.</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Search, Users, ChevronLeft, ChevronRight } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'My Patients' })

const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const patients = ref([])
const search = ref('')
const activeFilter = ref('All')
const page = ref(1)
const pageSize = 6

const AVATAR_COLORS = ['#1e4a26', '#3a6b3a', '#D4A017', '#6a8a6a', '#8a6a3a']
function colorForId(id) { return AVATAR_COLORS[id % AVATAR_COLORS.length] }
function initialsFor(user) { return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase() }

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const filters = computed(() => [
  { label: 'All', count: patients.value.length },
  { label: 'Active', count: patients.value.filter(p => p.status === 'active').length },
  { label: 'Pending', count: patients.value.filter(p => p.status === 'pending').length },
  { label: 'Discharged', count: patients.value.filter(p => p.status === 'discharged').length },
])

const filteredPatients = computed(() => {
  return patients.value.filter(p => {
    const name = `${p.client.first_name} ${p.client.last_name}`.toLowerCase()
    const matchesSearch = name.includes(search.value.toLowerCase())
    const matchesFilter = activeFilter.value === 'All' || p.status === activeFilter.value.toLowerCase()
    return matchesSearch && matchesFilter
  })
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredPatients.value.length / pageSize)))

const pagedPatients = computed(() => {
  const start = (page.value - 1) * pageSize
  return filteredPatients.value.slice(start, start + pageSize)
})

watch([search, activeFilter], () => { page.value = 1 })

function statusLabel(status) {
  return { active: 'Active', pending: 'New Booking', discharged: 'Discharged' }[status] || status
}
function statusClass(status) {
  return { active: 'status-active', pending: 'status-pending', discharged: 'status-discharged' }[status] || ''
}
function ncpLabel(status) {
  return { draft: 'Draft', completed: 'Completed', not_started: 'Not Started' }[status] || status
}
function ncpClass(status) {
  return { draft: 'ncp-draft', completed: 'ncp-completed', not_started: 'ncp-not-started' }[status] || ''
}

async function loadPatients() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    patients.value = await get('/rnd/patients/')
  } catch {
    errorMessage.value = 'Could not load your patients. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadPatients)
</script>

<style scoped>
* { box-sizing: border-box; }

.my-patients-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

/* TOOLBAR */
.toolbar { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }
.search-box-wide {
  display: flex; align-items: center; gap: 10px; background: #fff; border: 1.5px solid #a8b3a8;
  border-radius: 24px; padding: 12px 18px; width: 100%; max-width: 420px;
}
.search-box-wide input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; color: #4a5a4a; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }

.filter-tabs { display: flex; gap: 10px; flex-wrap: wrap; }
.filter-tab {
  border: 1px solid #e5e8e5; background: #fff; color: #4a5a4a;
  border-radius: 20px; padding: 9px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.filter-tab.active { background: #14301a; color: #fff; border-color: #14301a; }

.patient-table-wrap { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 8px 22px; overflow-x: auto; }
.patient-table { width: 100%; border-collapse: collapse; }
.patient-table th {
  text-align: left; font-size: 0.7rem; letter-spacing: 0.05em; color: #9aaa9a;
  font-weight: 700; padding: 16px 12px 12px; border-bottom: 1px solid #eceeec;
}
.patient-table td { padding: 16px 12px; border-bottom: 1px solid #f2f4f2; font-size: 0.86rem; color: #2a2a2a; }
.patient-table tr:last-child td { border-bottom: none; }

.patient-cell { display: flex; align-items: center; gap: 10px; }
.patient-avatar {
  width: 32px; height: 32px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 0.72rem; font-weight: 700; flex-shrink: 0;
}
.patient-avatar.avatar-muted { background: #d5dad5; color: #fff; }
.patient-name { font-weight: 700; color: #1a3a1a; }
.patient-name.name-muted { color: #9aaa9a; font-weight: 600; }
.text-muted { color: #b0b8b0; }

.status-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.status-pill.status-active { background: #e3f3ea; color: #1f8f5c; }
.status-pill.status-pending { background: #fdf1d6; color: #b8860b; }
.status-pill.status-discharged { background: #fbe0e0; color: #c0392b; }

.ncp-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.ncp-pill.ncp-draft { background: #fdf1d6; color: #b8860b; }
.ncp-pill.ncp-not-started { background: #eceeec; color: #7a8a7a; }
.ncp-pill.ncp-completed { background: #e3f3ea; color: #1f8f5c; }

.action-cell { display: flex; align-items: center; gap: 10px; white-space: nowrap; }
.chart-btn {
  border: 1px solid #d5dad5; background: #fff; color: #2a2a2a;
  border-radius: 6px; padding: 7px 16px; font-size: 0.8rem; font-weight: 600; cursor: pointer; text-decoration: none;
}
.accept-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 6px;
  padding: 7px 16px; font-size: 0.8rem; font-weight: 700; cursor: pointer; text-decoration: none;
}

.empty-state {
  background: #fff; border-radius: 14px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
.empty-text { font-size: 0.85rem; color: #9aaa9a; padding: 20px; text-align: center; }

/* PAGINATION */
.pagination-row { display: flex; align-items: center; justify-content: space-between; margin-top: 16px; }
.pagination-label { font-size: 0.8rem; color: #8a9a8a; }
.pagination-controls { display: flex; gap: 8px; }
.page-btn {
  display: flex; align-items: center; gap: 4px;
  border: 1px solid #d5dad5; background: #fff; color: #4a5a4a;
  border-radius: 8px; padding: 8px 14px; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.page-btn-primary { background: #14301a; color: #fff; border-color: #14301a; }
.page-btn-primary:disabled { background: #14301a; opacity: 0.4; }

</style>
