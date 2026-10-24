<template>
  <nav class="navbar">
    <NuxtLink to="/" class="nav-logo">
      <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="logo-img" />
      <span class="logo-text"><span class="logo-nutri">Nutri</span><span class="logo-match">Match</span></span>
    </NuxtLink>

    <ul class="nav-links">
      <li><NuxtLink to="/#features">Features</NuxtLink></li>
      <li><NuxtLink to="/about">About</NuxtLink></li>
      <li><NuxtLink to="/contact">Contact</NuxtLink></li>
    </ul>

    <NavAccount />
  </nav>
</template>

<script setup>
</script>

<style scoped>
.navbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 48px; height: 90px; background-color: #063C2A;
  font-family: 'Inter', sans-serif;
}
.nav-logo { display: flex; align-items: center; gap: 10px; text-decoration: none; }
.logo-img { width: 44px; height: 36px; object-fit: contain; }
.logo-text { font-size: 1.2rem; font-weight: 700; font-family: 'Playfair Display', serif; }
.logo-nutri { color: #ffffff; }
.logo-match { color: #D4A017; }

.nav-links { display: flex; list-style: none; gap: 32px; margin: 0; padding: 0; }
.nav-links a { color: #c8d8c8; text-decoration: none; font-size: 0.85rem; font-weight: 500; }
.nav-links a:hover { color: #D4A017; }

@media (max-width: 900px) {
  .navbar { padding: 0 24px; }
  .nav-links { display: none; }
}

/* Phones: same slim bar as the landing page's LandingNavbar.vue. */
@media (max-width: 600px) {
  .navbar { padding: 0 16px; height: 64px; }
  .logo-img { width: 34px; height: 30px; }
  .nav-logo { gap: 6px; }
}
</style>
