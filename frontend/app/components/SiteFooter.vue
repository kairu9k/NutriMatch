<template>
  <footer class="footer">
    <div class="footer-grid">
      <div class="footer-brand">
        <div class="footer-logo-row">
          <img src="/resources/nutrimatchlogo.png" alt="NutriMatch Logo" class="logo-img" />
          <div class="footer-logo"><span class="logo-nutri">Nutri</span><span class="logo-match">Match</span></div>
        </div>
        <p>A web-based clinical nutrition consultation management system for Filipino RNDs and patients. Built for Philippine healthcare.</p>
        <span class="ra-badge">RA 10173 COMPLIANT</span>
      </div>

      <div class="footer-col">
        <div class="footer-col-title">PLATFORM</div>
        <NuxtLink to="/#features">Features</NuxtLink>
        <NuxtLink to="/#how-it-works">How It Works</NuxtLink>
        <NuxtLink to="/#testimonials">Reviews</NuxtLink>
        <NuxtLink to="/#faqs">FAQ</NuxtLink>
      </div>

      <div class="footer-col">
        <div class="footer-col-title">FOR USERS</div>
        <NuxtLink to="/register">Sign Up as Patient</NuxtLink>
        <NuxtLink to="/register">Register as RND</NuxtLink>
        <NuxtLink to="/login">Log In</NuxtLink>
      </div>

      <div class="footer-col">
        <div class="footer-col-title">LEGAL</div>
        <NuxtLink to="/privacy-policy">Privacy Policy</NuxtLink>
        <NuxtLink to="/terms">Terms of Service</NuxtLink>
        <NuxtLink to="/contact">Contact Us</NuxtLink>
      </div>
    </div>

    <div class="footer-bottom">
      <span>© 2026 NutriMatch · BSIT Group 12 · STI College Davao · Timtim · Alba · Bulalaque · Leabres</span>
      <div class="footer-links">
        <NuxtLink to="/privacy-policy">Privacy</NuxtLink>
        <NuxtLink to="/terms">Terms</NuxtLink>
        <NuxtLink to="/contact">Contact</NuxtLink>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  background: #0D1F18;
  padding: 56px 72px 32px;
  font-family: 'Inter', sans-serif;
}

.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 48px;
  margin-bottom: 55px;
}

.footer-logo-row { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.logo-img { width: 36px; height: 36px; object-fit: contain; }
.footer-logo { font-size: 1.2rem; font-weight: 700; font-family: 'Playfair Display', serif; letter-spacing: 0.02em; }
.logo-nutri { color: #004635; }
.logo-match { color: #EFBF04; }

.footer-brand p { font-size: 0.75rem; color: #6a8a6a; line-height: 1.7; margin-bottom: 16px; max-width: 280px; }

.ra-badge {
  display: inline-block; border: 1px solid #3a6a3a; color: #7aaa7a;
  font-size: 0.55rem; letter-spacing: 0.08em; padding: 4px 12px; border-radius: 4px;
}

.footer-col { display: flex; flex-direction: column; gap: 12px; }
.footer-col-title { font-size: 0.75rem; letter-spacing: 0.12em; font-weight: 600; color: #6a8a6a; margin-bottom: 4px; }
.footer-col a { font-size: 0.75rem; color: #c8d8c8; text-decoration: none; }
.footer-col a:hover { color: #ffffff; }

.footer-bottom {
  border-top: 1px solid #1a4a1a;
  padding-top: 24px;
  display: flex; justify-content: space-between; align-items: center;
  font-size: 0.75rem; color: #4a6a4a; flex-wrap: wrap; gap: 12px;
}
.footer-links { display: flex; gap: 20px; }
.footer-links a { color: #4a6a4a; text-decoration: none; }
.footer-links a:hover { color: #c8d8c8; }

@media (max-width: 900px) {
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .footer { padding: 48px 24px 24px; }
}
</style>
