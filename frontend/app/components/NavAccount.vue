<template>
  <!-- The right side of the public navbars (home, about, contact, terms,
       privacy). Signed out: Sign in + Create account. Signed in: Go to my
       dashboard + the account (photo and name) with Sign out underneath.
       The session lives in the browser, so this only shows after mounting
       (no flash of the wrong buttons). -->
  <div class="nav-actions" :class="`is-${variant}`">
    <template v-if="!ready" />
    <template v-else-if="user">
      <NuxtLink :to="dashboardPath" class="btn-get-started">
        <span class="full">Go to my dashboard</span><span class="short">Dashboard</span>
      </NuxtLink>
      <div class="acct">
        <button
          type="button" class="acct-btn" aria-haspopup="menu" :aria-expanded="menuOpen"
          :aria-label="`Account menu for ${fullName}`" @click.stop="menuOpen = !menuOpen"
        >
          <img v-if="user.profile_photo" :src="user.profile_photo" alt="" class="acct-avatar" />
          <span v-else class="acct-avatar">{{ initials }}</span>
          <span class="acct-name">{{ user.first_name }}</span>
          <ChevronDown :size="14" aria-hidden="true" class="acct-chev" :class="{ open: menuOpen }" />
        </button>
        <div v-if="menuOpen" class="acct-menu" role="menu" @click.stop>
          <div class="acct-who">
            <strong>{{ fullName }}</strong>
            <span>{{ user.email }}</span>
          </div>
          <button type="button" role="menuitem" class="acct-item" @click="signOut">
            <LogOut :size="15" aria-hidden="true" /> Sign out
          </button>
        </div>
      </div>
    </template>
    <template v-else>
      <NuxtLink to="/login" class="btn-login">Log in</NuxtLink>
      <NuxtLink to="/register" class="btn-get-started">Create account</NuxtLink>
    </template>
  </div>
</template>

<script setup>
import { ChevronDown, LogOut } from 'lucide-vue-next'

// variant="dark"  (default): for the green navbars (about, contact, terms, privacy)
// variant="light": for the white landing navbar
defineProps({
  variant: { type: String, default: 'dark' },
})

const auth = useAuthStore()
const ready = ref(false)
const menuOpen = ref(false)

const user = computed(() => (auth.isAuthenticated ? auth.user : null))
const fullName = computed(() => [user.value?.first_name, user.value?.last_name].filter(Boolean).join(' '))
const initials = computed(() => userInitials(user.value?.first_name, user.value?.last_name))
const DASHBOARDS = { client: '/client-dashboard', rnd: '/rnd-dashboard', admin: '/admin-dashboard' }
const dashboardPath = computed(() => DASHBOARDS[user.value?.role] || '/')

// Signing out here keeps them on the page they were reading.
function signOut() {
  menuOpen.value = false
  auth.logout()
}

function close() { menuOpen.value = false }
function onKey(e) { if (e.key === 'Escape') menuOpen.value = false }
onMounted(() => {
  ready.value = true
  document.addEventListener('click', close)
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', close)
  window.removeEventListener('keydown', onKey)
})
</script>

<style scoped>
.nav-actions { display: flex; gap: 12px; align-items: center; min-height: 34px; }

.btn-login, .btn-get-started {
  display: inline-flex; align-items: center; justify-content: center; min-height: 34px; padding: 0 22px; border-radius: 24px;
  font-family: 'Inter', sans-serif; font-size: 0.78rem; font-weight: 700; text-decoration: none; white-space: nowrap; cursor: pointer;
  transition: background 0.2s;
}
/* filled, on the dark bar */
.btn-login { background: rgba(255, 255, 255, 0.14); color: #fff; padding: 0 28px; }
.btn-login:hover { background: rgba(255, 255, 255, 0.22); }
.btn-get-started { background: #EFBF04; color: #063C2A; }
.btn-get-started:hover { background: #e0b204; }
.btn-login:focus-visible, .btn-get-started:focus-visible, .acct-btn:focus-visible { outline: 2px solid #f3d27a; outline-offset: 2px; }
.short { display: none; }

/* the account: photo, first name, menu */
.acct { position: relative; }
.acct-btn {
  display: inline-flex; align-items: center; gap: 8px; min-height: 34px; padding: 0 10px 0 3px; border: none; border-radius: 24px;
  background: rgba(255, 255, 255, 0.14); color: #fff; font-family: 'Inter', sans-serif; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.acct-btn:hover { background: rgba(255, 255, 255, 0.22); }
.acct-avatar {
  width: 28px; height: 28px; border-radius: 50%; object-fit: cover; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; background: #D4A017; color: #063C2A; font-size: 0.7rem; font-weight: 700;
}
.acct-name { max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.acct-chev { transition: transform 0.15s; }
.acct-chev.open { transform: rotate(180deg); }
@media (prefers-reduced-motion: reduce) { .acct-chev { transition: none; } }

.acct-menu {
  position: absolute; right: 0; top: calc(100% + 8px); z-index: 1100; min-width: 230px; padding: 6px; background: #fff; border-radius: 12px;
  border: 1px solid #d9e3dc; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22); font-family: 'Inter', sans-serif;
}
.acct-who { display: flex; flex-direction: column; gap: 2px; padding: 10px 10px 12px; border-bottom: 1px solid #d9e3dc; margin-bottom: 6px; }
.acct-who strong { font-size: 0.88rem; color: #1a3a1a; }
.acct-who span { font-size: 0.78rem; color: #6a7a6a; overflow-wrap: anywhere; }
.acct-item {
  display: flex; align-items: center; gap: 8px; width: 100%; min-height: 36px; padding: 0 10px; border: none; border-radius: 8px;
  background: none; color: #a12525; font-family: inherit; font-size: 0.86rem; font-weight: 600; text-align: left; cursor: pointer;
}
.acct-item:hover { background: #fdf1ef; }
.acct-item:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }


/* ---------- light variant: white landing navbar ---------- */
.is-light .btn-login, .is-light .btn-get-started {
  min-height: 44px; font-family: 'DM Sans', Arial, sans-serif; font-size: 15px; border-radius: 999px;
  transition: background 0.2s, box-shadow 0.2s;
}
/* Sign in: no border, same soft shadow as the hero's "I'm an RND" button */
.is-light .btn-login {
  background: #fff; color: #063C2A; border: 1.5px solid transparent; padding: 0 22px;
  box-shadow: 0 12px 26px -12px rgba(6, 60, 42, 0.35), 0 2px 6px rgba(6, 60, 42, 0.06);
  transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
}
.is-light .btn-login:hover {
  background: #fff;
  transform: translateY(-2px);
  box-shadow: 0 16px 30px -12px rgba(6, 60, 42, 0.45), 0 2px 6px rgba(6, 60, 42, 0.08);
}
.is-light .btn-get-started { background: #EFBF04; color: #063C2A; border: 1.5px solid #EFBF04; padding: 0 22px; box-shadow: 0 8px 18px -10px rgba(6, 60, 42, 0.6); }
.is-light .btn-get-started:hover { background: #e0b204; }
.is-light .btn-login:focus-visible, .is-light .btn-get-started:focus-visible, .is-light .acct-btn:focus-visible { outline: 3px solid #EFBF04; outline-offset: 3px; }
.is-light .acct-btn { min-height: 44px; background: #F1F5F2; color: #063C2A; font-family: 'DM Sans', Arial, sans-serif; font-size: 14px; padding: 0 12px 0 4px; }
.is-light .acct-btn:hover { background: #E4EDE7; }
.is-light .acct-avatar { width: 34px; height: 34px; background: #063C2A; color: #EFBF04; }
.is-light .acct-menu { font-family: 'DM Sans', Arial, sans-serif; }

/* phones: shorter dashboard label, photo only */
@media (max-width: 600px) {
  .nav-actions { gap: 8px; }
  .btn-login, .btn-get-started { padding: 0 14px; }
  .is-light .btn-login, .is-light .btn-get-started { padding: 0 18px; }
  .full, .acct-name { display: none; }
  .short { display: inline; }
  .acct-btn { padding: 0 6px 0 3px; gap: 4px; }
}
</style>