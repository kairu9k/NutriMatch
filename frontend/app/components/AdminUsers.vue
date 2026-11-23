<template>
  <div class="nm-page">

    <!-- add admin (POST /api/admin/admins/, accounts/admin_accounts.py) -->
    <div v-if="showAdd" class="nm-modal-overlay" @click.self="showAdd = false">
      <form class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="add-admin-title" @submit.prevent="addAdmin">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="showAdd = false"><X :size="18" aria-hidden="true" /></button>
        <h3 id="add-admin-title" class="nm-modal-title">Add an admin</h3>
        <p class="nm-modal-text">They get full admin access. We email them an invite to set their own password with a 6-digit code. No password is ever sent by email.</p>
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
          <textarea v-model="addForm.reason" class="nm-input" rows="2" maxlength="500" placeholder="For example: a second admin to cover support on weekends." />
          <small v-if="addErrors.reason" class="nm-field-error">{{ addErrors.reason }}</small>
          <small v-else class="nm-hint">At least 10 characters. It's saved in the audit log.</small></label>
        <p v-if="addErrors.detail" class="nm-error">{{ addErrors.detail }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="showAdd = false">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="adding">{{ adding ? 'Adding…' : 'Add admin and send invite' }}</button>
        </div>
      </form>
    </div>

    <section class="us-hero">
      <img class="us-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="us-fade" aria-hidden="true"></span>
      <div class="us-hero-txt">
        <p class="us-eyebrow"><span aria-hidden="true"></span>Users</p>
        <h2 class="us-title">Everyone on NutriMatch</h2>
        <p class="us-sub">Clients, RNDs and admins. Open anyone to see their details and account.</p>
      </div>
      <button type="button" class="nm-btn-dark us-add" @click="openAddAdmin"><UserPlus :size="16" aria-hidden="true" /> Add admin</button>
    </section>

    <p v-if="error" class="nm-error">{{ error }}</p>

    <div class="nm-toolbar us-toolbar">
      <div class="nm-tabs us-tabs">
        <button v-for="t in tabs" :key="t.key" class="nm-tab" :class="{ active: tab === t.key }" @click="tab = t.key">
          <svg v-if="t.key === 'clients'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1-1.1a5.5 5.5 0 0 0-7.8 7.8l1 1.1L12 21l7.8-7.5 1-1.1a5.5 5.5 0 0 0 0-7.8z" /></svg><svg v-else-if="t.key === 'rnds'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3v6a5 5 0 0 0 10 0V3" /><path d="M10 14v2a5 5 0 0 0 10 0v-2" /><circle cx="20" cy="12" r="2" /></svg><svg v-else class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
          {{ t.label }} <span class="nm-count">{{ lists[t.key].length }}</span>
        </button>
      </div>
      <div class="users-tools">
        <label class="us-sel">
          <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h18l-7 8v6l-4 2v-8z" /></svg>
          <select v-model="status" class="nm-select" aria-label="Account status">
            <option v-for="s in statusFilters" :key="s.key" :value="s.key">{{ s.label }}</option>
          </select>
        </label>
        <div class="nm-search us-search">
          <Search :size="17" />
          <input v-model="query" type="search" placeholder="Search name or email" />
        </div>
      </div>
    </div>

    <div class="nm-panel us-card">
      <header class="us-head">
        <div>
          <h3 class="us-h">{{ tabs.find(t => t.key === tab).label }}</h3>
          <p class="us-hsub">{{ TAB_SUB[tab] }}</p>
        </div>
        <span v-if="!loading && rows.length" class="us-count">{{ rows.length }} {{ tabs.find(t => t.key === tab).label.toLowerCase() }}</span>
      </header>
      <p v-if="loading" class="nm-muted us-state"><span class="us-spin" aria-hidden="true"></span> Loading accounts…</p>
      <div v-else-if="!rows.length" class="nm-empty">
        <span class="us-empty-ico"><Users :size="26" /></span>
        <p>{{ query || status !== 'all' ? `No ${tabs.find(t => t.key === tab).label.toLowerCase()} match these filters.` : `No ${tabs.find(t => t.key === tab).label.toLowerCase()} yet.` }}</p>
      </div>
      <div v-else class="nm-table-wrap">
        <table class="nm-table stack us-table" :class="'tab-' + tab">
          <thead>
            <tr>
              <th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg> Name</th>
              <th v-if="tab === 'clients'"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h4l3-8 4 16 3-8h4" /></svg> Condition</th>
              <th v-if="tab === 'clients'"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3v6a5 5 0 0 0 10 0V3" /><path d="M10 14v2a5 5 0 0 0 10 0v-2" /><circle cx="20" cy="12" r="2" /></svg> RND</th>
              <th v-if="tab === 'rnds'"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.6 13.4l-7.2 7.2a2 2 0 0 1-2.8 0L3 13V3h10l7.6 7.6a2 2 0 0 1 0 2.8z" /><circle cx="7.5" cy="7.5" r="1.5" /></svg> Specialization</th>
              <th v-if="tab === 'rnds'"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2l2.4 3.2 4-.6.6 4L22 11l-3 2.6.6 4-4-.6L12 20l-2.4-3.2-4 .6-.6-4L2 11l3-2.4-.6-4 4 .6z" /><path d="M9 11l2 2 4-4" /></svg> Application</th>
              <th v-if="tab !== 'admins'" class="nm-num"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="6" width="14" height="12" rx="2" /><path d="M16 10l6-3v10l-6-3z" /></svg> Consultations</th>
              <th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg> Joined</th>
              <th><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21V4M4 4h12l-2 4 2 4H4" /></svg> Status</th>
              <th class="us-go-h"><span class="sr-only">Open</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in pagedRows" :key="u.id" class="clickable" :class="u.is_active ? 'tone-green' : 'tone-muted'" @click="open(u)">
              <td>
                <div class="u-who">
                  <img v-if="u.profile_photo" :src="u.profile_photo" class="nm-avatar" alt="" />
                  <span v-else class="nm-avatar">{{ userInitials(u.first_name, u.last_name) }}</span>
                  <div class="u-who-txt">
                    <p class="nm-row-title">{{ u.first_name }} {{ u.last_name }}</p>
                    <p class="nm-row-sub">{{ u.email }}</p>
                  </div>
                </div>
              </td>
              <td v-if="tab === 'clients'" data-label="Condition"><span v-if="u.condition" class="u-cond">{{ u.condition }}</span><span v-else class="u-none">—</span></td>
              <td v-if="tab === 'clients'" data-label="RND"><span v-if="u.matched_rnd" class="u-rnd"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 3v6a5 5 0 0 0 10 0V3" /><path d="M10 14v2a5 5 0 0 0 10 0v-2" /><circle cx="20" cy="12" r="2" /></svg> {{ u.matched_rnd }}</span><span v-else class="u-none">—</span></td>
              <td v-if="tab === 'rnds'" data-label="Specialization"><span v-if="u.specialization" class="u-cond green">{{ u.specialization }}</span><span v-else class="u-none">—</span></td>
              <td v-if="tab === 'rnds'" data-label="Application">
                <span class="nm-pill" :class="reviewPill(u.review_status)">{{ reviewLabel(u.review_status) }}</span>
              </td>
              <td v-if="tab !== 'admins'" data-label="Consultations" class="nm-num"><span class="u-num" :class="{ on: u.consultations }">{{ u.consultations ?? 0 }}</span></td>
              <td data-label="Joined"><span class="u-date"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg> {{ shortDate(u.created_at) }}</span></td>
              <td data-label="Status">
                <span class="nm-pill" :class="u.is_active ? 'green' : 'muted'">{{ u.is_active ? 'Active' : 'Deactivated' }}</span>
              </td>
              <td class="u-go" aria-hidden="true"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg></td>
            </tr>
          </tbody>
        </table>
      </div>
      <ListPager v-model:page="page" :pages="pages" />
    </div>
  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import { CheckCircle2, Search, UserPlus, Users, X } from 'lucide-vue-next'

const { get, post } = useApi()

/* ---------- add admin ---------- */
const showAdd = ref(false)
const adding = ref(false)
const addForm = reactive({ first_name: '', last_name: '', email: '', reason: '' })
const addErrors = ref({})
const toast = useToast() // the app's toast (2026-11-03)
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
    toast.success(`Invite sent to ${created.email}.`)
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
  { key: 'all', label: 'Any status' },
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

useAutoRefresh(() => loadAll({ quiet: true }))
onMounted(loadAll)
async function loadAll({ quiet = false } = {}) {
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
    if (!quiet) error.value = 'Could not load the accounts. Please refresh the page.'
  } finally {
    loading.value = false
  }
}

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

// 10 per page; back to page 1 when the tab, status or search changes
const { page, pages, paged: pagedRows } = usePager(rows, { perPage: 10, resetOn: () => [tab.value, status.value, query.value] })

function open(u) {
  navigateTo(`/users/${u.id}`)
}
function reviewLabel(s) {
  return { pending: 'Under review', approved: 'Approved', rejected: 'Rejected' }[s] || '—'
}
function reviewPill(s) {
  return { pending: 'gold', approved: 'green', rejected: 'muted' }[s] || 'muted'
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
const TAB_SUB = {
  clients: 'Everyone who signed up to find an RND',
  rnds: 'Registered nutritionist-dietitians and their applications',
  admins: 'People with full admin access',
}
</script>
<style scoped>
.nm-page { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; display: inline-block; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }

/* ---------- hero ---------- */
.us-hero { position: relative; overflow: hidden; display: flex; align-items: center; justify-content: space-between; gap: 18px 24px; flex-wrap: wrap; margin-bottom: 18px; padding: 26px 30px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.us-hero > *:not(.us-plate):not(.us-fade) { position: relative; z-index: 1; }
.us-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.us-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 52%, rgba(0, 77, 58, 0.85) 72%, rgba(0, 77, 58, 0.6) 100%); }
.us-hero-txt { flex: 1 1 360px; min-width: 0; max-width: 620px; }
.us-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.us-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.us-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.us-sub { margin: 0; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }
.us-hero .nm-btn-dark.us-add { display: inline-flex; align-items: center; gap: 8px; height: 44px; margin-right: 120px; padding: 0 18px; border: none; border-radius: 12px; background: #efbf04; color: #004d3a; font-family: inherit; font-size: 14px; font-weight: 800; cursor: pointer; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); transition: background 0.15s, transform 0.15s; }
.us-hero .nm-btn-dark.us-add:hover { background: #f5cb1c; transform: translateY(-1px); }
.us-add:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }

/* ---------- tabs, status, search ---------- */
.us-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin: 0 0 16px; }
.us-tabs { display: inline-flex; gap: 4px; max-width: 100%; padding: 5px; border: none; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); overflow-x: auto; scrollbar-width: none; }
.us-tabs::-webkit-scrollbar { display: none; }
.us-tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 36px; margin: 0; padding: 0 15px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.us-tabs .nm-tab .ic { color: #8a9a91; }
.us-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; }
.us-tabs .nm-count { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 700; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.us-tabs .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.us-tabs .nm-tab.active .ic { color: #efbf04; }
.us-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }
.us-tabs .nm-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.users-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.us-sel { position: relative; display: flex; align-items: center; gap: 8px; height: 46px; padding: 0 6px 0 16px; border-radius: 999px; background: #fff; color: #1f7a4d; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); cursor: pointer; }
.us-sel:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.us-sel .nm-select { width: auto; min-width: 130px; height: 100%; margin: 0; padding: 0 28px 0 0; border: none !important; background-color: transparent !important; box-shadow: none !important; font-family: inherit; font-size: 14px; color: #22362c; cursor: pointer; outline: none; }
.us-search { position: relative; display: flex; align-items: center; gap: 10px; width: 300px; max-width: 100%; height: 46px; margin: 0; padding: 0 16px; border: none; border-radius: 999px; background: #fff; color: #8a9a91; box-sizing: border-box; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); }
.us-search:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.us-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.us-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }

/* ---------- table card ---------- */
.nm-panel.us-card { padding: 0; border: none; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: hidden; }
.us-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; padding: 24px 32px 20px; }
.us-h { margin: 0 0 4px; font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 700; color: #0e3a2c; }
.us-hsub { margin: 0; font-size: 13.5px; color: #6b7d73; }
.us-count { flex-shrink: 0; padding: 5px 12px; border-radius: 999px; background: #e3f4ea; font-size: 12.5px; font-weight: 700; color: #1f7a4d; white-space: nowrap; }
.us-state { display: flex; align-items: center; justify-content: center; gap: 10px; margin: 0; padding: 36px 20px; font-weight: 600; }
.us-spin { width: 20px; height: 20px; border-radius: 50%; border: 3px solid #e3efe7; border-top-color: #004d3a; animation: us-spin 0.8s linear infinite; }
@keyframes us-spin { to { transform: rotate(360deg); } }
.us-card :deep(.nm-empty) { display: flex; flex-direction: column; align-items: center; gap: 10px; margin: 0 32px 28px; padding: 32px 20px; border-radius: 18px; border: 1.5px dashed #cfddd4; text-align: center; }
.us-card :deep(.nm-empty p) { margin: 0; font-size: 14px; font-weight: 600; color: #4a5a52; }
.us-empty-ico { width: 52px; height: 52px; border-radius: 16px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }
.us-card .nm-table-wrap { margin: 0; border: none; border-radius: 0; overflow-x: auto; }
.us-table { width: 100% !important; border-collapse: collapse; font-size: 14px; }
.us-table thead th { padding: 15px 16px; background: #eaf3ed; border-top: 1px solid #dcebe1; border-bottom: 1px solid #dcebe1; text-align: left !important; font-size: 13px; font-weight: 700; color: #1f5c45; white-space: nowrap; text-transform: none; letter-spacing: 0; }
.us-table thead th .ic { margin-right: 6px; vertical-align: -2px; color: #1f7a4d; }
.us-table td.nm-num { text-align: left !important; }
.us-table th:first-child, .us-table td:first-child { padding-left: 32px; }
.us-table tbody td { position: relative; padding: 18px 16px; border-bottom: 1px solid #f0f3f1; vertical-align: middle; }
.us-table tbody tr:last-child td { border-bottom: none; }
.us-table tbody tr.clickable { cursor: pointer; transition: background 0.15s; }
.us-table tbody tr.clickable:hover td { background: #fafcfb; }
.us-go-h { width: 56px; }
.u-who { display: flex; align-items: center; gap: 14px; min-width: 0; }
.u-who .nm-avatar { flex-shrink: 0; width: 42px; height: 42px; border-radius: 50%; object-fit: cover; box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #efbf04, #c49102); color: #004d3a; font-size: 13.5px; font-weight: 800; border: 2px solid #fff; box-shadow: 0 0 0 2.5px #1f9d55; }
.tone-muted .u-who .nm-avatar { box-shadow: 0 0 0 2.5px #c9d3cd; }
.u-who-txt { min-width: 0; }
.u-who .nm-row-title { margin: 0; font-size: 14.5px; font-weight: 700; color: #0e3a2c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.u-who .nm-row-sub { margin: 2px 0 0; font-size: 13px; color: #6b7d73; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.u-cond { display: inline-flex; padding: 4px 11px; border-radius: 999px; background: #eef1fa; font-size: 12.5px; font-weight: 700; color: #2e4a86; }
.u-cond.green { background: #e3f4ea; color: #1f5c45; }
.u-rnd { display: inline-flex; align-items: center; gap: 6px; font-weight: 600; color: #0e3a2c; }
.u-rnd .ic { color: #1f7a4d; }
.u-none { font-weight: 700; color: #b5c3ba; }
.u-num { display: inline-flex; align-items: center; justify-content: center; min-width: 30px; height: 30px; padding: 0 8px; border-radius: 10px; background: #f3f6f4; font-weight: 800; color: #8a9a91; font-variant-numeric: tabular-nums; box-sizing: border-box; }
.u-num.on { background: #e3f4ea; color: #1f7a4d; }
.u-date { display: inline-flex; align-items: center; gap: 7px; color: #22362c; white-space: nowrap; }
.u-date .ic { color: #1f7a4d; }
.us-table .nm-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 11px; border-radius: 999px; font-size: 12.5px; font-weight: 700; }
.us-table .nm-pill::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.us-table .nm-pill.green { background: #e3f4ea; color: #1f7a4d; }
.us-table .nm-pill.gold { background: #fff4d6; color: #8a6500; }
.us-table .nm-pill.muted { background: #f3f6f4; color: #6b7d73; }
.u-go { width: 56px; text-align: right; padding-right: 24px !important; }
.u-go .ic { width: 28px; height: 28px; padding: 6px; box-sizing: border-box; border-radius: 50%; background: #f1f6f2; color: #1f7a4d; }
@media (min-width: 761px) {
  .us-table tbody td:first-child::before { content: ''; position: absolute; left: 0; top: 18px; bottom: 18px; width: 4px; border-radius: 0 4px 4px 0; background: #c9d3cd; }
  .us-table tbody tr.tone-green td:first-child::before { background: #1f9d55; }
}
.us-card :deep(.nm-pager) { margin: 0; padding: 14px 32px; border-top: 1px solid #f0f3f1; }

/* ---------- add admin pop-up ---------- */
.add-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.add-field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; min-width: 0; }
.add-field .nm-label { margin: 0; font-size: 13px; font-weight: 700; color: #22362c; }
.add-field .nm-input { border: 1.5px solid #c9d8cf; border-radius: 12px; font-family: inherit; }
.add-field .nm-input:focus { border-color: #004d3a; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); outline: none; }
.add-field input.nm-input { min-height: 44px; }

/* ---------- smaller screens ---------- */
@media (max-width: 960px) {
  .us-hero { padding: 20px 18px; border-radius: 22px; }
  .us-title { font-size: 24px; }
  .us-plate { width: 180px; height: 180px; right: -60px; top: 20px; transform: none; }
  .us-hero .nm-btn-dark.us-add { width: 100%; margin-right: 0; justify-content: center; }
  .us-tabs { display: flex; width: 100%; border-radius: 16px; }
  .users-tools { width: 100%; }
  .us-sel { flex: 1; }
  .us-search { flex: 1 1 100%; width: auto; order: -1; }
  .us-head { padding: 18px 16px 12px; }
}
@media (max-width: 760px) {
  .nm-page { padding-bottom: 110px; }
  .us-table tbody tr { position: relative; border-left: 4px solid #c9d3cd; }
  .us-table tbody tr.tone-green { border-left-color: #1f9d55; }
  .u-go { position: absolute; top: 18px; right: 12px; width: auto; padding: 0 !important; }
  .us-card :deep(.nm-pager) { padding: 12px 16px; }
}
@media (max-width: 560px) { .add-grid { grid-template-columns: minmax(0, 1fr); gap: 0; } }
</style>