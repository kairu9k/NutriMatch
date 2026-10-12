<template>
  <div class="nm-page">
    <div class="users-head">
      <p class="nm-page-sub">Every client, RND and admin account. Open one to see their full record.</p>
      <button type="button" class="nm-btn-dark nm-btn-sm" @click="openAddAdmin"><UserPlus :size="14" /> Add admin</button>
    </div>

    <!-- add admin (POST /api/admin/admins/, accounts/admin_accounts.py) -->
    <div v-if="showAdd" class="nm-modal-overlay" @click.self="showAdd = false">
      <form class="nm-modal" @submit.prevent="addAdmin">
        <h3 class="nm-modal-title">Add an admin</h3>
        <p class="nm-modal-text">They get full admin access. We email them an invite to set their own password with a 6-digit code — no password is sent by email.</p>
        <div class="add-grid">
          <label class="add-field"><span class="nm-label">First name</span>
            <input v-model="addForm.first_name" class="nm-input" maxlength="150" required />
            <small v-if="addErrors.first_name" class="nm-field-error">{{ addErrors.first_name }}</small></label>
          <label class="add-field"><span class="nm-label">Last name</span>
            <input v-model="addForm.last_name" class="nm-input" maxlength="150" required />
            <small v-if="addErrors.last_name" class="nm-field-error">{{ addErrors.last_name }}</small></label>
        </div>
        <label class="add-field"><span class="nm-label">Email</span>
          <input v-model="addForm.email" type="email" class="nm-input" maxlength="254" required />
          <small v-if="addErrors.email" class="nm-field-error">{{ addErrors.email }}</small></label>
        <label class="add-field"><span class="nm-label">Reason</span>
          <textarea v-model="addForm.reason" class="nm-input" rows="2" maxlength="500" placeholder="e.g. Second admin to cover support on weekends." />
          <small v-if="addErrors.reason" class="nm-field-error">{{ addErrors.reason }}</small>
          <small v-else class="nm-hint">At least 10 characters — saved in the audit log.</small></label>
        <p v-if="addErrors.detail" class="nm-error">{{ addErrors.detail }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" @click="showAdd = false">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="adding">{{ adding ? 'Adding…' : 'Add admin & send invite' }}</button>
        </div>
      </form>
    </div>
    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>

    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-toolbar">
      <div class="nm-tabs">
        <button v-for="t in tabs" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" @click="tab = t.key">
          {{ t.label }} <span class="nm-count">{{ lists[t.key].length }}</span>
        </button>
      </div>
      <div class="nm-search">
        <Search :size="15" />
        <input v-model="query" type="search" placeholder="Search name or email" />
      </div>
    </div>

    <div class="nm-toolbar" style="margin-bottom: 12px">
      <div class="nm-tabs">
        <button v-for="s in statusFilters" :key="s.key" class="nm-tab" :class="{ active: status === s.key }" @click="status = s.key">
          {{ s.label }}
        </button>
      </div>
    </div>

    <div class="nm-panel">
      <p v-if="loading" class="nm-muted">Loading accounts…</p>
      <div v-else-if="!rows.length" class="nm-empty">
        <Users :size="28" />
        <p>No {{ tab }} match these filters.</p>
      </div>
      <div v-else class="nm-table-wrap">
        <table class="nm-table stack">
          <thead>
            <tr>
              <th>Name</th>
              <th v-if="tab === 'clients'">Condition</th>
              <th v-if="tab === 'clients'">RND</th>
              <th v-if="tab === 'rnds'">Specialization</th>
              <th v-if="tab === 'rnds'">Application</th>
              <th v-if="tab !== 'admins'" class="nm-num">Consultations</th>
              <th>Joined</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in rows" :key="u.id" class="clickable" @click="open(u)">
              <td>
                <div style="display: flex; align-items: center; gap: 10px; min-width: 0">
                  <img v-if="u.profile_photo" :src="u.profile_photo" class="nm-avatar" alt="" />
                  <span v-else class="nm-avatar">{{ userInitials(u.first_name, u.last_name) }}</span>
                  <div style="min-width: 0">
                    <p class="nm-row-title">{{ u.first_name }} {{ u.last_name }}</p>
                    <p class="nm-row-sub">{{ u.email }}</p>
                  </div>
                </div>
              </td>
              <td v-if="tab === 'clients'" data-label="Condition">{{ u.condition || '—' }}</td>
              <td v-if="tab === 'clients'" data-label="RND">{{ u.matched_rnd || '—' }}</td>
              <td v-if="tab === 'rnds'" data-label="Specialization">{{ u.specialization || '—' }}</td>
              <td v-if="tab === 'rnds'" data-label="Application">
                <span class="nm-pill" :class="reviewPill(u.review_status)">{{ reviewLabel(u.review_status) }}</span>
              </td>
              <td v-if="tab !== 'admins'" data-label="Consultations" class="nm-num">{{ u.consultations ?? 0 }}</td>
              <td data-label="Joined">{{ shortDate(u.created_at) }}</td>
              <td data-label="Status">
                <span class="nm-pill" :class="u.is_active ? 'green' : 'red'">{{ u.is_active ? 'Active' : 'Deactivated' }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { CheckCircle2, Search, UserPlus, Users } from 'lucide-vue-next'

const { get, post } = useApi()

/* ---------- add admin ---------- */
const showAdd = ref(false)
const adding = ref(false)
const addForm = reactive({ first_name: '', last_name: '', email: '', reason: '' })
const addErrors = ref({})
const toast = ref('')
function openAddAdmin() {
  Object.assign(addForm, { first_name: '', last_name: '', email: '', reason: '' })
  addErrors.value = {}
  showAdd.value = true
}
async function addAdmin() {
  addErrors.value = {}
  if (addForm.reason.trim().length < 10) {
    addErrors.value = { reason: 'Say why in at least 10 characters.' }
    return
  }
  adding.value = true
  try {
    const created = await post('/admin/admins/', { ...addForm })
    lists.admins.unshift(created)
    showAdd.value = false
    tab.value = 'admins'
    toast.value = `Invite sent to ${created.email}.`
    setTimeout(() => { toast.value = '' }, 3500)
  } catch (e) {
    const d = e?.data || {}
    addErrors.value = Object.fromEntries(Object.entries(d).map(([k, v]) => [k, Array.isArray(v) ? v[0] : v]))
    if (!Object.keys(addErrors.value).length) addErrors.value = { detail: apiError(e) }
  } finally {
    adding.value = false
  }
}
const route = useRoute()

const tabs = [
  { key: 'clients', label: 'Clients' },
  { key: 'rnds', label: 'RNDs' },
  { key: 'admins', label: 'Admins' },
]
const statusFilters = [
  { key: 'all', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'inactive', label: 'Deactivated' },
]

const tab = ref(tabs.some(t => t.key === route.query.tab) ? route.query.tab : 'clients')
const status = ref('all')
const query = ref('')
const loading = ref(true)
const error = ref('')
const lists = reactive({ clients: [], rnds: [], admins: [] })

const asList = r => (Array.isArray(r) ? r : r?.results || [])

onMounted(async () => {
  try {
    const [clients, rnds, admins] = await Promise.all([
      get('/admin/clients/'),
      get('/admin/rnds/'),
      get('/admin/users/', { query: { role: 'admin' } }),
    ])
    lists.clients = asList(clients)
    lists.rnds = asList(rnds)
    lists.admins = asList(admins)
  } catch {
    error.value = 'Could not load the accounts. Please refresh the page.'
  } finally {
    loading.value = false
  }
})

watch(tab, t => navigateTo({ query: { ...route.query, tab: t } }, { replace: true }))

const rows = computed(() => {
  const q = query.value.trim().toLowerCase()
  return lists[tab.value].filter((u) => {
    if (status.value === 'active' && !u.is_active) return false
    if (status.value === 'inactive' && u.is_active) return false
    if (!q) return true
    return `${u.first_name} ${u.last_name} ${u.email}`.toLowerCase().includes(q)
  })
})

function open(u) {
  navigateTo(`/users/${u.id}`)
}
function reviewLabel(s) {
  return { pending: 'Under review', approved: 'Approved', rejected: 'Rejected' }[s] || '—'
}
function reviewPill(s) {
  return { pending: 'gold', approved: 'green', rejected: 'red' }[s] || 'muted'
}
</script>

<style scoped>
.users-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.users-head .nm-page-sub { margin: 0; }
.add-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.add-field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; min-width: 0; }
.add-field .nm-label { margin: 0; }
.add-field input.nm-input { min-height: 42px; }
@media (max-width: 560px) { .add-grid { grid-template-columns: minmax(0, 1fr); gap: 0; } }
</style>
