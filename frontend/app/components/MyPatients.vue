<template>
  <div class="my-patients-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">My Patients</h1>
        <p class="page-sub">Manage your active and pending client relationships.</p>
      </div>
      <div class="search-box-wide">
        <Search :size="16" class="search-icon" />
        <input v-model="search" type="text" placeholder="Search patients..." />
      </div>
    </div>

    <!-- FILTER TABS -->
    <div v-if="patients.length" class="filter-tabs">
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

    <!-- PATIENT TABLE -->
    <div v-if="patients.length" class="patient-table-wrap">
      <table v-if="filteredPatients.length" class="patient-table">
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
          <tr v-for="p in filteredPatients" :key="p.name">
            <td class="patient-cell">
              <div class="patient-avatar" :class="{ 'avatar-muted': p.discharged }" :style="!p.discharged ? { background: p.avatarColor } : {}">
                {{ p.initials }}
              </div>
              <span class="patient-name" :class="{ 'name-muted': p.discharged }">{{ p.name }}</span>
            </td>
            <td :class="{ 'text-muted': p.discharged }">{{ p.condition }}</td>
            <td><span class="status-pill" :class="statusClass(p.status)">{{ p.status }}</span></td>
            <td :class="{ 'text-muted': p.discharged }">{{ p.lastVisit || '—' }}</td>
            <td :class="{ 'text-muted': p.discharged }">{{ p.nextAppointment || '—' }}</td>
            <td><span class="ncp-pill" :class="ncpClass(p.ncpStatus)">{{ p.ncpStatus }}</span></td>
            <td class="action-cell">
              <template v-if="p.status === 'Pending Request'">
                <button class="accept-btn" @click="acceptPatient(p)">Accept</button>
                <button class="decline-btn" @click="declinePatient(p)">Decline</button>
              </template>
              <button v-else class="chart-btn" @click="navigateTo(`/ncp-records?patient=${p.name}`)">View Chart</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty-text">No patients match your search or filter.</p>
    </div>

    <!-- EMPTY STATE: no patients at all -->
    <div v-else class="empty-state">
      <div class="empty-icon"><Users :size="28" /></div>
      <p class="empty-title">No patients yet</p>
      <p class="empty-desc">Once clients request to work with you, they'll show up here.</p>
    </div>
  </div>
</template>

<script setup>
import { Search, Users } from 'lucide-vue-next'
import { db } from '~/mock/mockDatabase'

definePageMeta({ layout: 'dashboard', title: 'My Patients' })

const search = ref('')
const activeFilter = ref('All')

const patients = ref(db.patients)

const filters = computed(() => [
  { label: 'All', count: patients.value.length },
  { label: 'Active', count: patients.value.filter(p => p.status === 'Active').length },
  { label: 'Pending', count: patients.value.filter(p => p.status.includes('Pending')).length },
  { label: 'Discharged', count: patients.value.filter(p => p.status === 'Discharged').length }
])

const filteredPatients = computed(() => {
  return patients.value.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.value.toLowerCase())
    const matchesFilter =
      activeFilter.value === 'All' ||
      (activeFilter.value === 'Pending' && p.status.includes('Pending')) ||
      p.status === activeFilter.value
    return matchesSearch && matchesFilter
  })
})

function statusClass(status) {
  if (status === 'Active') return 'status-active'
  if (status.includes('Pending')) return 'status-pending'
  if (status === 'Discharged') return 'status-discharged'
  return ''
}

function ncpClass(ncpStatus) {
  if (ncpStatus.includes('Draft')) return 'ncp-draft'
  if (ncpStatus === 'Not Started') return 'ncp-not-started'
  if (ncpStatus === 'Completed') return 'ncp-completed'
  return ''
}

function acceptPatient(patient) {
  // Wire this up to your real accept-patient API call
  patient.status = 'Active'
}

function declinePatient(patient) {
  // Wire this up to your real decline-patient API call
  patients.value = patients.value.filter(p => p.name !== patient.name)
}
</script>

<style scoped>
* { box-sizing: border-box; }

.my-patients-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.search-box-wide {
  display: flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #e5e8e5;
  border-radius: 8px; padding: 10px 14px; width: 260px; flex-shrink: 0;
}
.search-box-wide input { border: none; background: none; outline: none; font-size: 0.85rem; width: 100%; }
.search-icon { color: #9aaa9a; flex-shrink: 0; }

/* FILTER TABS */
.filter-tabs { display: flex; gap: 10px; margin-bottom: 20px; }
.filter-tab {
  border: 1px solid #e5e8e5; background: #fff; color: #4a5a4a;
  border-radius: 20px; padding: 9px 18px; font-size: 0.85rem; font-weight: 600; cursor: pointer;
}
.filter-tab.active { background: #14301a; color: #fff; border-color: #14301a; }

/* TABLE */
.patient-table-wrap { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 8px 22px; overflow-x: auto; }
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
.status-pill.status-active { background: #e6efe0; color: #3a6b3a; }
.status-pill.status-pending { background: #faead0; color: #b8860b; }
.status-pill.status-discharged { background: #f9e0dd; color: #c0392b; }

.ncp-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; }
.ncp-pill.ncp-draft { background: #faead0; color: #b8860b; }
.ncp-pill.ncp-not-started { background: #eceeec; color: #7a8a7a; }
.ncp-pill.ncp-completed { background: #e6efe0; color: #3a6b3a; }

.action-cell { display: flex; align-items: center; gap: 10px; white-space: nowrap; }
.chart-btn {
  border: 1px solid #d5dad5; background: #fff; color: #2a2a2a;
  border-radius: 6px; padding: 7px 16px; font-size: 0.8rem; font-weight: 600; cursor: pointer;
}
.accept-btn {
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 6px;
  padding: 7px 16px; font-size: 0.8rem; font-weight: 700; cursor: pointer;
}
.decline-btn {
  background: none; border: none; color: #8a9a8a; font-size: 0.8rem; font-weight: 600; cursor: pointer;
}

/* EMPTY STATE */
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