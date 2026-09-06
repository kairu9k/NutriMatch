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

    <div class="nav-actions">
      <button class="btn-login" @click="navigateTo('/login')">Log In</button>
      <button class="btn-get-started" @click="navigateTo('/register')">Get Started</button>
    </div>
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

.nav-actions { display: flex; gap: 12px; align-items: center; }
.btn-login {
  background: transparent; border: 0.5px solid #ffffff; color: #ffffff;
  padding: 8px 28px; border-radius: 24px; font-size: 0.78rem; font-weight: 600; cursor: pointer;
}
.btn-login:hover { border-color: #D4A017; color: #D4A017; }
.btn-get-started {
  background: #D4A017; border: none; color: #063C2A;
  padding: 8px 22px; border-radius: 24px; font-size: 0.78rem; font-weight: 700; cursor: pointer;
}
.btn-get-started:hover { background: #c4920f; }

@media (max-width: 900px) {
  .navbar { padding: 0 24px; }
  .nav-links { display: none; }
}
</style>
