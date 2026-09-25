<template>
  <div class="client-profile-page">
    <!-- HEADER BANNER -->
    <div class="profile-banner">
      <div class="banner-blob"></div>
      <div class="banner-left">
        <div class="banner-avatar">{{ userInitials }}</div>
        <div>
          <p class="banner-name">{{ form.fullName }}</p>
          <p class="banner-sub">{{ form.email }}</p>
          <div class="banner-chips">
            <span class="chip">Patient</span>
            <span class="chip">Member since {{ memberSince }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-layout">
      <!-- SETTINGS NAV -->
      <nav class="settings-nav">
        <button
          v-for="tab in tabs" :key="tab.key"
          class="settings-nav-item" :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <component :is="tab.icon" :size="16" />
          {{ tab.label }}
        </button>
      </nav>

      <!-- MAIN CONTENT -->
      <div class="settings-main">
        <!-- PERSONAL INFO -->
        <div class="panel" v-if="activeTab === 'personal'">
          <h3 class="panel-title">Personal Information</h3>
          <div class="form-row-2">
            <div class="field">
              <label>Full Name</label>
              <input v-model="form.fullName" type="text" />
            </div>
            <div class="field">
              <label>Email Address</label>
              <input v-model="form.email" type="email" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="field">
              <label>Phone Number</label>
              <input v-model="form.phone" type="tel" placeholder="e.g. 0917 123 4567" />
            </div>
            <div class="field">
              <label>Date of Birth</label>
              <input v-model="form.birthdate" type="date" />
            </div>
          </div>
          <div class="form-row-2">
            <div class="field">
              <label>Sex</label>
              <select v-model="form.sex">
                <option>Female</option>
                <option>Male</option>
              </select>
            </div>
            <div class="field">
              <label>Preferred Language</label>
              <select v-model="form.language">
                <option>Cebuano</option>
                <option>Tagalog</option>
                <option>English</option>
                <option>Ilocano</option>
              </select>
            </div>
          </div>
          <button class="primary-btn" @click="saveProfile">Save Changes</button>
        </div>

        <!-- HEALTH PROFILE -->
        <div class="panel" v-if="activeTab === 'health'">
          <h3 class="panel-title">Health Profile</h3>
          <p class="tab-desc">Your latest screening results and target diet on file.</p>
          <div v-if="hasLatestScreening" class="health-grid">
            <div class="health-box"><p class="health-label">BMI</p><p class="health-value">{{ screening.bmi }}</p></div>
            <div class="health-box"><p class="health-label">TDEE</p><p class="health-value">{{ screening.tdee }} <span>kcal</span></p></div>
            <div class="health-box"><p class="health-label">NRS-2002</p><p class="health-value">{{ screening.nrs }}</p></div>
          </div>
          <p v-else class="tab-desc">No screening on file yet.</p>
          <button class="outline-btn" @click="navigateTo('/pre-consultation-screening')">Update Screening</button>
        </div>

        <!-- SECURITY -->
        <div class="panel" v-if="activeTab === 'security'">
          <h3 class="panel-title">Security</h3>
          <div class="account-row">
            <div>
              <p class="account-label">Password</p>
              <p class="account-detail">Last changed {{ passwordLastChanged }}</p>
            </div>
            <button class="outline-btn small" @click="openChangePassword">Change Password</button>
          </div>
        </div>

        <!-- NOTIFICATIONS -->
        <div class="panel" v-if="activeTab === 'notifications'">
          <h3 class="panel-title">Notifications</h3>
          <div class="account-row">
            <div>
              <p class="account-label">Appointment, meal plan, and reminder alerts</p>
              <p class="account-detail">Receive push and email notifications</p>
            </div>
            <label class="toggle">
              <input type="checkbox" v-model="notificationsEnabled" />
              <span class="toggle-track"><span class="toggle-thumb"></span></span>
            </label>
          </div>
        </div>

        <!-- PRIVACY & DATA -->
        <div class="panel" v-if="activeTab === 'privacy'">
          <h3 class="panel-title">Privacy &amp; Data</h3>
          <p class="tab-desc">Your health data is only shared with your assigned RND under RA 10173 (Data Privacy Act of 2012).</p>
          <button class="outline-btn">Download My Data</button>
        </div>

        <!-- HISTORY -->
        <History v-if="activeTab === 'history'" />
      </div>

      <!-- SIDE -->
      <div class="settings-side">
        <div class="panel">
          <h3 class="panel-title">Care Team</h3>
          <div class="rnd-row">
            <div class="rnd-avatar">{{ rnd.initials }}</div>
            <div>
              <p class="rnd-name">{{ rnd.name }}</p>
              <p class="rnd-specialty">{{ rnd.specialty }}</p>
              <p class="rnd-rating">★ {{ rnd.rating }} ({{ rnd.reviews }} reviews)</p>
            </div>
          </div>
          <button class="outline-btn full-width" @click="navigateTo('/messages')">Send a Message</button>
        </div>

        <div class="panel danger-panel">
          <h3 class="panel-title">Sign Out</h3>
          <p class="danger-text">Sign out of NutriMatch on this device.</p>
          <button class="danger-outline-btn full-width" @click="handleLogout">Sign Out</button>
        </div>
      </div>
    </div>

    <!-- SAVE TOAST -->
    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle2 :size="16" /> Profile updated!
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { User, HeartPulse, Shield, Bell, FileText, History as HistoryIcon, CheckCircle2 } from 'lucide-vue-next'
import { useClientScreening } from '~/composables/useClientScreening'

const tabs = [
  { key: 'personal', label: 'Personal Info', icon: User },
  { key: 'health', label: 'Health Profile', icon: HeartPulse },
  { key: 'security', label: 'Security', icon: Shield },
  { key: 'notifications', label: 'Notifications', icon: Bell },
  { key: 'privacy', label: 'Privacy & Data', icon: FileText },
  { key: 'history', label: 'History', icon: HistoryIcon }
]
const activeTab = ref('personal')

// TODO: pull from the real client profile once that endpoint exists.
const userInitials = 'JD'
const memberSince = 'May 2026'
const passwordLastChanged = 'Apr 2, 2026'
const notificationsEnabled = ref(true)

const form = reactive({
  fullName: 'Juan Dela Cruz',
  email: 'juan.delacruz@email.com',
  phone: '0917 123 4567',
  birthdate: '1995-03-12',
  sex: 'Male',
  language: 'Cebuano'
})

const { hasLatestScreening, screening } = useClientScreening()

// TODO: pull from the client's actual assigned RND once that endpoint exists.
const rnd = {
  name: 'RND Ivy Hope Alba',
  initials: 'IA',
  specialty: 'Diabetes · Renal Nutrition',
  rating: 4.9,
  reviews: 38
}

const toastVisible = ref(false)
let toastTimer = null
function saveProfile() {
  // TODO: wire up to a real update-profile API call
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 3500)
}

function openChangePassword() {
  // TODO: wire up to a real change-password flow
  console.log('Change password clicked')
}

function handleLogout() {
  navigateTo('/login')
}
</script>

<style scoped>
* { box-sizing: border-box; }
.client-profile-page { font-family: 'Inter', sans-serif; }

/* BANNER */
.profile-banner {
  position: relative; overflow: hidden;
  background: linear-gradient(135deg, #00382a 0%, #005a42 100%);
  border-radius: 16px; padding: 28px 32px; margin-bottom: 20px; color: #fff;
}
.banner-blob { position: absolute; width: 220px; height: 220px; border-radius: 50%; background: rgba(255,255,255,0.05); top: -70px; right: -50px; z-index: 0; }
.banner-left { display: flex; align-items: center; gap: 18px; position: relative; z-index: 1; }
.banner-avatar { width: 64px; height: 64px; border-radius: 50%; background: #D4A017; color: #1a3a1a; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.3rem; flex-shrink: 0; }
.banner-name { font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; margin: 0; }
.banner-sub { font-size: 0.87rem; color: #cfe0d5; margin: 4px 0 10px; }
.banner-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip { font-size: 0.75rem; font-weight: 600; background: rgba(255,255,255,0.1); color: #fff; padding: 4px 12px; border-radius: 999px; }

/* LAYOUT */
.settings-layout { display: grid; grid-template-columns: 210px 1.6fr 1fr; gap: 20px; align-items: start; }

.settings-nav { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 10px; display: flex; flex-direction: column; gap: 2px; }
.settings-nav-item {
  display: flex; align-items: center; gap: 10px; border: none; background: none; text-align: left;
  padding: 11px 12px; border-radius: 10px; font-size: 0.85rem; font-weight: 600; color: #6a7a6a; cursor: pointer;
}
.settings-nav-item:hover { background: #f7f9f7; }
.settings-nav-item.active { background: #eef3ee; color: #1a3a1a; }

.settings-main { display: flex; flex-direction: column; gap: 16px; }
.settings-side { display: flex; flex-direction: column; gap: 16px; }

.panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px 24px; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 16px; }
.tab-desc { font-size: 0.85rem; color: #6a7a6a; margin: 0 0 16px; line-height: 1.5; }

.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field label { font-size: 0.8rem; font-weight: 600; color: #4a5a4a; }
.field input, .field select {
  border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px; font-size: 0.87rem; font-family: inherit; color: #1a3a1a; width: 100%; background: #fff;
}

.health-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 18px; }
.health-box { background: #f7f9f7; border-radius: 10px; padding: 14px; text-align: center; }
.health-label { font-size: 0.72rem; color: #9aaa9a; font-weight: 700; margin: 0 0 4px; }
.health-value { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.health-value span { font-size: 0.7rem; font-weight: 400; color: #9aaa9a; }

.primary-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 11px 20px; font-weight: 700; font-size: 0.87rem; cursor: pointer; }
.outline-btn { border: 1px solid #d5dad5; background: #fff; color: #1a3a1a; border-radius: 8px; padding: 10px 16px; font-weight: 600; font-size: 0.85rem; cursor: pointer; }
.outline-btn.small { padding: 8px 14px; font-size: 0.8rem; }
.outline-btn.full-width { width: 100%; }
.danger-outline-btn { border: 1px solid #c0392b; background: #fff; color: #c0392b; border-radius: 8px; padding: 10px 16px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }
.danger-outline-btn.full-width { width: 100%; }

.account-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
.account-label { font-size: 0.87rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.account-detail { font-size: 0.78rem; color: #9aaa9a; margin: 2px 0 0; }

.toggle { position: relative; display: inline-block; cursor: pointer; flex-shrink: 0; }
.toggle input { display: none; }
.toggle-track { display: block; width: 40px; height: 22px; background: #e5e8e5; border-radius: 999px; position: relative; transition: background 0.2s; }
.toggle input:checked + .toggle-track { background: #1f8f5c; }
.toggle-thumb { position: absolute; top: 2px; left: 2px; width: 18px; height: 18px; background: #fff; border-radius: 50%; transition: transform 0.2s; }
.toggle input:checked + .toggle-track .toggle-thumb { transform: translateX(18px); }

/* CARE TEAM */
.rnd-row { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.rnd-avatar { width: 48px; height: 48px; border-radius: 50%; background: #00382a; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.rnd-name { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.rnd-specialty { font-size: 0.78rem; color: #8a9a8a; margin: 2px 0 0; }
.rnd-rating { font-size: 0.78rem; color: #b8860b; font-weight: 600; margin: 2px 0 0; }

/* DANGER ZONE */
.danger-panel { border-color: #f5d5cf; }
.danger-text { font-size: 0.83rem; color: #6a7a6a; margin: 0 0 14px; }

/* TOAST */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

@media (max-width: 1100px) {
  .settings-layout { grid-template-columns: 1fr; }
  .settings-nav { flex-direction: row; overflow-x: auto; }
}
@media (max-width: 640px) {
  .form-row-2, .health-grid { grid-template-columns: 1fr; }
}
</style>