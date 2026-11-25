<template>
  <nav class="navbar" :class="{ 'menu-open': menuOpen }">
    <div class="nav-bar">
      <NuxtLink to="/" class="nav-logo" aria-label="NutriMatch home" @click="goHome">
        <img src="/resources/nutrimatchlogo.png" alt="" class="logo-img" />
        <span class="logo-text">
          <span class="logo-nutri">Nutri</span><span class="logo-match">Match</span>
        </span>
      </NuxtLink>

      <ul class="nav-links">
        <li v-for="link in links" :key="link.id">
          <a
            :href="link.id === 'home' ? '/' : `#${link.id}`"
            :class="{ active: activeSection === link.id }"
            :aria-current="activeSection === link.id ? 'true' : undefined"
            @click="handleClick(link.id, $event)"
          >{{ link.label }}</a>
        </li>
      </ul>

      <div class="nav-account">
        <NavAccount variant="light" />
      </div>

      <button
        type="button"
        class="nav-burger"
        :aria-label="menuOpen ? 'Close menu' : 'Open menu'"
        :aria-expanded="menuOpen"
        @click="menuOpen = !menuOpen"
      >
        <svg v-if="!menuOpen" width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18" /></svg>
        <svg v-else width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" /></svg>
      </button>
    </div>

    <!-- Phone / tablet menu -->
    <Transition name="drop">
      <div v-if="menuOpen" class="nav-mobile">
        <a
          v-for="link in links"
          :key="link.id"
          :href="link.id === 'home' ? '/' : `#${link.id}`"
          :class="{ active: activeSection === link.id }"
          @click="handleClick(link.id, $event); menuOpen = false"
        >{{ link.label }}</a>
        <div class="nav-mobile-account">
          <NavAccount variant="light" />
        </div>
      </div>
    </Transition>
  </nav>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const links = [
  { id: 'home', label: 'Home' },
  { id: 'features', label: 'Features' },
  { id: 'how-it-works', label: 'How it works' },
  { id: 'for-rnds', label: 'For RNDs' },
  { id: 'faqs', label: 'FAQs' },
]

const activeSection = ref(links[0].id)
const menuOpen = ref(false)

let manualOverrideTimeout = null
let isManualClick = false

// The logo links to the landing page; already there, it scrolls back to the top.
function goHome(event) {
  menuOpen.value = false
  if (useRoute().path !== '/') return
  event.preventDefault()
  window.scrollTo({ top: 0, behavior: 'smooth' })
  history.pushState(null, '', '/')
  activeSection.value = 'home'
}

// Highlight the link of the section sitting under the navbar.
// A section counts as "current" once its top passes just below the navbar,
// so a tall section (For RNDs + meal plans) stays highlighted all the way down.
function updateActive() {
  if (isManualClick) return
  const line = 140 // px from the top of the window (navbar + a little room)
  let current = 'home'
  for (const link of links) {
    if (link.id === 'home') continue
    const el = document.getElementById(link.id)
    if (el && el.getBoundingClientRect().top <= line) current = link.id
  }
  // At the very bottom of the page, the last section is the current one
  const atBottom = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4
  if (atBottom) current = links[links.length - 1].id
  activeSection.value = current
}

function handleClick(id, event) {
  event.preventDefault()

  // Set active immediately (persists even after cursor leaves)
  activeSection.value = id
  isManualClick = true

  if (id === 'home') {
    window.scrollTo({ top: 0, behavior: 'smooth' })
    history.pushState(null, '', '/')
  } else {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
    // Update the URL hash without an extra jump
    history.pushState(null, '', `#${id}`)
  }

  // Give the smooth scroll time to finish before the scroll position
  // takes back control of the highlight
  clearTimeout(manualOverrideTimeout)
  manualOverrideTimeout = setTimeout(() => {
    isManualClick = false
    updateActive()
  }, 900)
}

onMounted(() => {
  window.addEventListener('scroll', updateActive, { passive: true })
  window.addEventListener('resize', updateActive)
  updateActive()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateActive)
  window.removeEventListener('resize', updateActive)
  clearTimeout(manualOverrideTimeout)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

/* Fixed white bar with a thin bottom border (height unchanged: 90px / 64px on phones,
   so LandingHero.vue's top padding still matches) */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  /* exactly the same shade as the hero; both are pinned to the screen
     (fixed) so the colors line up seamlessly */
  background:
    radial-gradient(circle at 76% 48%, rgba(239, 191, 4, 0.30), rgba(239, 191, 4, 0) 48%),
    radial-gradient(circle at 6% 10%, rgba(6, 60, 42, 0.16), rgba(6, 60, 42, 0) 42%),
    linear-gradient(135deg, #DFECE3 0%, #EAF2E8 40%, #FBEFC8 100%);
  background-attachment: fixed;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: none;
  font-family: 'DM Sans', Arial, sans-serif;
}

.nav-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  height: 90px;
  padding: 0 clamp(16px, 2vw, 32px);
}

/* Logo */
.nav-logo { display: flex; align-items: center; gap: 12px; text-decoration: none; flex-shrink: 0; margin-left: clamp(0px, 2.5vw, 40px); }
.logo-img { width: 55px; height: 50px; object-fit: contain; }
.logo-text {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.2px;
}
.logo-nutri { color: #063C2A; }
.logo-match { color: #C49102; } /* darker gold so it stands out on the light navbar */

/* Links: centered, uppercase, gold underline on the active one */
.nav-links {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 32px;
  list-style: none;
  margin: 0;
  padding: 0;
}
.nav-links a {
  display: inline-block;
  padding: 8px 0;
  color: #1F2D27;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
  transition: color 0.2s, box-shadow 0.2s;
}
.nav-links a:hover {
  color: #063C2A;
  box-shadow: inset 0 -3px 0 #C49102;
}
.nav-links a.active {
  color: #063C2A;
  font-weight: 700;
  box-shadow: inset 0 -3px 0 #C49102;
}
.nav-links a:focus-visible,
.nav-burger:focus-visible,
.nav-mobile a:focus-visible { outline: 3px solid #EFBF04; outline-offset: 3px; }

.nav-account { flex-shrink: 0; display: flex; align-items: center; }

/* Phone menu button: plain icon, no background */
.nav-burger {
  display: none;
  width: 44px;
  height: 44px;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  background: transparent;
  color: #10231B;
  cursor: pointer;
}

/* Dropdown under the bar */
.nav-mobile {
  display: none;
  flex-direction: column;
  padding: 4px 24px 20px;
  background: #F6F9F4;
  border-top: 1px solid #DCE6DF;
}
.nav-mobile > a {
  padding: 14px 12px;
  margin: 0 -12px;
  border-radius: 10px;
  border-bottom: 1px solid #EEF2EF;
  color: #063C2A;
  text-decoration: none;
  font-size: 15px;
  font-weight: 600;
}
.nav-mobile > a.active { background: #FFF6D1; font-weight: 700; }
.nav-mobile-account { margin-top: 16px; display: flex; flex-wrap: wrap; gap: 10px; }

.drop-enter-active, .drop-leave-active { transition: opacity .2s ease, transform .2s ease; }
.drop-enter-from, .drop-leave-to { opacity: 0; transform: translateY(-6px); }

/* Tablet & phone: links and account buttons move into the menu */
@media (max-width: 1100px) {
  .nav-links, .nav-account { display: none; }
  .nav-burger { display: inline-flex; }
  .nav-mobile { display: flex; }
}

/* Phones: slimmer bar (64px) — LandingHero.vue's top padding matches this height */
@media (max-width: 600px) {
  .nav-bar { height: 64px; padding: 0 16px; }
  .logo-img { width: 28px; height: 35px; }
  .logo-text { font-size: 21px; }
  .nav-logo { gap: 8px; margin-left: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .drop-enter-active, .drop-leave-active, .nav-links a { transition: none; }
}
</style>