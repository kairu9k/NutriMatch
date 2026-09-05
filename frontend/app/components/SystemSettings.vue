<script setup>
import { adminProfile , platformStats } from '~/mock/mockAdminDatabase'

const profile = adminProfile
const stats = platformStats

const form = reactive({
  displayName: profile.value.displayName,
  email: profile.value.email,
  password: ''
})

const toggles = reactive({
  rndVerification: true,
  clientRegistration: true,
  auditNotifications: true,
  maintenanceMode: false
})

const saveMsg = ref('')
function saveAccount() {
  profile.value.displayName = form.displayName
  profile.value.email = form.email
  saveMsg.value = 'Account settings saved.'
  setTimeout(() => (saveMsg.value = ''), 2500)
}

const showMaintenanceConfirm = ref(false)
function enableMaintenance() {
  showMaintenanceConfirm.value = true
}
function confirmMaintenance() {
  toggles.maintenanceMode = true
  showMaintenanceConfirm.value = false
}

const showPurgeConfirm = ref(false)
const purgeMsg = ref('')
function purgeLogs() {
  showPurgeConfirm.value = true
}
function confirmPurge() {
  showPurgeConfirm.value = false
  purgeMsg.value = 'Audit logs purge queued. (Demo only — no data was deleted.)'
  setTimeout(() => (purgeMsg.value = ''), 3000)
}
</script>

<template>
  <div class="grid grid-cols-2 gap-6">
    <div class="space-y-6">
      <div class="animate-in bg-white rounded-2xl p-6">
        <h3 class="font-display text-lg text-forest-dark mb-4">Administrator Account</h3>
        <div class="flex items-center gap-3 bg-cream-soft rounded-xl p-4 mb-4">
          <div class="w-10 h-10 rounded-full bg-gold text-forest-dark flex items-center justify-center font-bold">SA</div>
          <div class="flex-1">
            <p class="font-semibold text-sm">System Administrator</p>
            <p class="text-xs text-forest/50">admin@nutrimatch.ph · Super Admin</p>
          </div>
          <span class="text-xs font-semibold bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full">Full Access</span>
        </div>

        <label class="text-xs text-forest/50">Display name</label>
        <input v-model="form.displayName" type="text" class="w-full border border-forest/15 rounded-lg px-3 py-2 text-sm mb-3 mt-1 bg-cream-soft transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />

        <label class="text-xs text-forest/50">Email address</label>
        <input v-model="form.email" type="email" class="w-full border border-forest/15 rounded-lg px-3 py-2 text-sm mb-3 mt-1 bg-cream-soft transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />

        <label class="text-xs text-forest/50">New password</label>
        <input v-model="form.password" type="password" placeholder="Leave blank to keep current" class="w-full border border-forest/15 rounded-lg px-3 py-2 text-sm mb-4 mt-1 bg-cream-soft transition-shadow focus:outline-none focus:ring-2 focus:ring-forest/20" />

        <button class="btn-press w-full bg-forest text-white rounded-lg py-2.5 text-sm font-medium hover:bg-forest-light hover:scale-[1.01]" @click="saveAccount">
          Save account settings
        </button>
        <Transition name="dropdown">
          <p v-if="saveMsg" class="text-xs text-emerald-700 mt-2">{{ saveMsg }}</p>
        </Transition>
      </div>

      <div class="animate-in stagger-1 bg-white rounded-2xl p-6">
        <h3 class="font-display text-lg text-forest-dark mb-4">Platform Configuration</h3>

        <div class="flex items-center justify-between py-3 border-b border-forest/5">
          <div>
            <p class="text-sm font-medium">RND Verification Mode</p>
            <p class="text-xs text-forest/40">Manual review required before activation</p>
          </div>
          <label class="switch"><input type="checkbox" v-model="toggles.rndVerification" /><span class="track"><span class="thumb" /></span></label>
        </div>

        <div class="flex items-center justify-between py-3 border-b border-forest/5">
          <div>
            <p class="text-sm font-medium">Client Registration</p>
            <p class="text-xs text-forest/40">Allow public client self-registration</p>
          </div>
          <label class="switch"><input type="checkbox" v-model="toggles.clientRegistration" /><span class="track"><span class="thumb" /></span></label>
        </div>

        <div class="flex items-center justify-between py-3 border-b border-forest/5">
          <div>
            <p class="text-sm font-medium">Audit Log Notifications</p>
            <p class="text-xs text-forest/40">Email alerts for security events</p>
          </div>
          <label class="switch"><input type="checkbox" v-model="toggles.auditNotifications" /><span class="track"><span class="thumb" /></span></label>
        </div>

        <div class="flex items-center justify-between py-3">
          <div>
            <p class="text-sm font-medium">Maintenance Mode</p>
            <p class="text-xs text-forest/40">Temporarily disable public access</p>
          </div>
          <label class="switch"><input type="checkbox" v-model="toggles.maintenanceMode" /><span class="track"><span class="thumb" /></span></label>
        </div>
      </div>
    </div>

    <div class="space-y-6">
      <div class="animate-in stagger-1 bg-white rounded-2xl p-6">
        <h3 class="font-display text-lg text-forest-dark">Privacy & Compliance</h3>
        <p class="text-xs text-forest/40 mb-4">Republic Act No. 10173</p>

        <div class="card-hover bg-emerald-50 rounded-lg px-4 py-3 flex justify-between items-center mb-2">
          <div><p class="text-sm font-medium">SSL/TLS Encryption</p><p class="text-xs text-forest/40">Certificate valid until Dec 31, 2026</p></div>
          <span class="text-xs font-semibold bg-emerald-600 text-white px-2.5 py-1 rounded-full">Active</span>
        </div>
        <div class="card-hover bg-emerald-50 rounded-lg px-4 py-3 flex justify-between items-center mb-2">
          <div><p class="text-sm font-medium">Role-Based Access Control</p><p class="text-xs text-forest/40">3 roles: Admin, RND, Client</p></div>
          <span class="text-xs font-semibold bg-emerald-600 text-white px-2.5 py-1 rounded-full">Enforced</span>
        </div>
        <div class="card-hover bg-emerald-50 rounded-lg px-4 py-3 flex justify-between items-center mb-2">
          <div><p class="text-sm font-medium">Audit Logging</p><p class="text-xs text-forest/40">All clinical and admin actions logged</p></div>
          <span class="text-xs font-semibold bg-emerald-600 text-white px-2.5 py-1 rounded-full">Enabled</span>
        </div>
        <div class="card-hover bg-amber-50 rounded-lg px-4 py-3 flex justify-between items-center mb-4">
          <div><p class="text-sm font-medium text-amber-800">Data Retention Schedule</p><p class="text-xs text-amber-700">Automated purge not yet implemented</p></div>
          <span class="text-xs font-semibold bg-amber-400 text-amber-900 px-2.5 py-1 rounded-full">Manual</span>
        </div>

        <button class="btn-press w-full border border-forest/15 rounded-lg py-2.5 text-sm font-medium hover:bg-cream-soft hover:scale-[1.01]">
          Generate compliance report
        </button>
      </div>

      <div class="animate-in stagger-2 bg-red-50 border border-red-200 rounded-2xl p-6">
        <h3 class="font-display text-lg text-red-700 mb-4">Danger zone</h3>
        <button class="btn-press w-full border border-red-300 text-red-600 rounded-lg py-2.5 text-sm font-medium mb-3 hover:bg-red-100 hover:scale-[1.01]" @click="purgeLogs">
          Purge old audit logs
        </button>
        <Transition name="dropdown">
          <p v-if="purgeMsg" class="text-xs text-red-700 mb-3">{{ purgeMsg }}</p>
        </Transition>
        <button class="btn-press w-full bg-red-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-red-700 hover:scale-[1.01]" @click="enableMaintenance">
          Enable maintenance mode
        </button>
      </div>
    </div>

    <!-- confirm dialogs -->
    <Transition name="modal">
      <div v-if="showMaintenanceConfirm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
        <Transition name="modal-pop" appear>
          <div class="bg-white rounded-xl p-6 w-96">
            <p class="font-semibold text-forest-dark mb-2">Enable maintenance mode?</p>
            <p class="text-sm text-forest/60 mb-4">This will disable public access to the platform (demo only).</p>
            <div class="flex gap-3">
              <button class="btn-press flex-1 border border-forest/15 rounded-lg py-2 text-sm hover:bg-cream-soft" @click="showMaintenanceConfirm = false">Cancel</button>
              <button class="btn-press flex-1 bg-red-600 text-white rounded-lg py-2 text-sm hover:bg-red-700" @click="confirmMaintenance">Enable</button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>

    <Transition name="modal">
      <div v-if="showPurgeConfirm" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
        <Transition name="modal-pop" appear>
          <div class="bg-white rounded-xl p-6 w-96">
            <p class="font-semibold text-forest-dark mb-2">Purge old audit logs?</p>
            <p class="text-sm text-forest/60 mb-4">This action is irreversible in production (demo only, nothing is actually deleted).</p>
            <div class="flex gap-3">
              <button class="btn-press flex-1 border border-forest/15 rounded-lg py-2 text-sm hover:bg-cream-soft" @click="showPurgeConfirm = false">Cancel</button>
              <button class="btn-press flex-1 bg-red-600 text-white rounded-lg py-2 text-sm hover:bg-red-700" @click="confirmPurge">Purge</button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </div>
</template>
