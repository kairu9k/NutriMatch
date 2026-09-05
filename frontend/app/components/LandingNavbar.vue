<template>
  <nav class="navbar">
    <div class="nav-logo">
      <div class="nav-logo">
        <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="logo-img" />
      </div>
      <span class="logo-text">
        <span class="logo-nutri" style="font-family: 'DM Serif Display', serif; font-weight: 700;font-size:medium;">Nutri</span><span class="logo-match" style="font-family: 'DM Serif Display', serif; font-weight: 700; font-size: medium;">Match</span>
      </span>
    </div>

    <ul class="nav-links">
      <li v-for="link in links" :key="link.id">
        <a
          :href="`#${link.id}`"
          :class="{ active: activeSection === link.id }"
          @click="handleClick(link.id, $event)"
        >{{ link.label }}</a>
      </li>
    </ul>

    <div class="nav-actions">
      <button class="btn-login" @click="navigateTo('/login')">Log In</button>
      <button class="btn-get-started" @click="navigateTo('/register')">Get Started</button>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const links = [
  { id: 'features', label: 'Features' },
  { id: 'how-it-works', label: 'How It Works' },
  { id: 'testimonials', label: 'Testimonials' },
  { id: 'for-rnds', label: 'For RNDs' },
  { id: 'faqs', label: 'FAQs' },
]

const activeSection = ref(links[0].id)

let observer = null
let manualOverrideTimeout = null
let isManualClick = false

function handleClick(id, event) {
  event.preventDefault()

  // Set active immediately (persists even after cursor leaves)
  activeSection.value = id
  isManualClick = true

  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  // Update the URL hash without an extra jump
  history.pushState(null, '', `#${id}`)

  // Give the smooth scroll time to finish before letting the
  // IntersectionObserver take back control of activeSection
  clearTimeout(manualOverrideTimeout)
  manualOverrideTimeout = setTimeout(() => {
    isManualClick = false
  }, 900)
}

onMounted(() => {
  const sections = links
    .map(link => document.getElementById(link.id))
    .filter(Boolean)

  observer = new IntersectionObserver(
    (entries) => {
      if (isManualClick) return // don't fight the click-triggered scroll

      // Pick the entry that is most visible / closest to the top band
      const visible = entries
        .filter(e => e.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)

      if (visible.length > 0) {
        activeSection.value = visible[0].target.id
      }
    },
    {
      // Treat the top ~30% of the viewport as the "trigger band"
      rootMargin: '-90px 0px -60% 0px',
      threshold: [0, 0.25, 0.5, 0.75, 1],
    }
  )

  sections.forEach(section => observer.observe(section))
})

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
  clearTimeout(manualOverrideTimeout)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  height: 90px;
  background-color: #063C2A;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  font-family: 'DM Sans', sans-serif;
  font-size: 0.75rem; font-weight: 100; color: #c8d8c8;
}

.nav-logo { display: flex; align-items: center; gap: 10px; }
.logo-text { font-size: 1.2rem; font-weight: 500; }
.logo-nutri { color: #ffffff; }
.logo-match { color: #D4A017; }

.logo-img {
  width: 55px;
  height: 45px;
  object-fit: contain;
}

.nav-links { display: flex; list-style: none; gap: 32px; }
.nav-links a {
  position: relative;
  color: #c8d8c8; text-decoration: none;
  font-size: 0.85rem; font-weight: 100; transition: color 0.2s;
  padding-bottom: 4px;
}
.nav-links a:hover {
  color: #D4A017;
  text-decoration: underline;
  text-underline-offset: 6px;
}

/* Persistent active state (stays highlighted after click, and follows scroll) */
.nav-links a.active {
  color: #D4A017;
  text-decoration: underline;
  text-underline-offset: 6px;
  font-weight: 500;
}

.nav-actions { display: flex; gap: 12px; align-items: center; }

.btn-login {
  background: transparent; border: 0.5px solid #ffffff; color: #ffffff;
  padding: 8px 35px; border-radius: 24px; font-size: 0.70rem;
  font-weight: 500; cursor: pointer; transition: background 0.2s;
}
.btn-login:hover {  border-color: #D4A017; color: #D4A017; }

.btn-get-started {
  background: #EFBF04; border: none; color: #063C2A;
  padding: 8px 22px; border-radius: 24px; font-size: 0.70rem;
  font-weight: 700; cursor: pointer; transition: background 0.2s;
}
.btn-get-started:hover {background: #EFBF04; box-shadow: 0 4px 12px rgb(255, 230, 2);}

@media (max-width: 900px) {
  .navbar { padding: 0 24px; }
  .nav-links { display: none; }
}
</style>