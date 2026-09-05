<template>
  <div class="landing">
    <!-- NAVBAR -->
    <!-- <nav class="navbar">
      <div class="nav-logo">
        <div class="logo-icon">
          <svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="18" cy="10" r="5" fill="#D4A017" opacity="0.9"/>
            <circle cx="10" cy="22" r="5" fill="#4CAF50" opacity="0.85"/>
            <circle cx="26" cy="22" r="5" fill="#D4A017" opacity="0.7"/>
            <circle cx="18" cy="18" r="4" fill="#2E5E2E" opacity="0.6"/>
          </svg>
        </div>
        <span class="logo-text"><span class="logo-nutri">Nutri</span><span class="logo-match">Match</span></span>
      </div>

      <ul class="nav-links">
        <li><a href="#features">Features</a></li>
        <li><a href="#how-it-works">How It Works</a></li>
        <li><a href="#testimonials">Testimonials</a></li>
        <li><a href="#for-rnds">For RNDs</a></li>
        <li><a href="#faqs">FAQs</a></li>
      </ul>

      <div class="nav-actions">
        <button class="btn-login">Log In</button>
        <button class="btn-get-started">Get Started</button>
      </div>
    </nav> -->

    <!-- HERO -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-badge"style="position: relative; left: 50px; top: 0;">
          <span class="badge-dot"></span>
          DESIGNED FOR PHILIPPINE RNDS · RA 10173 COMPLIANT
        </div>

        <h1 class="hero-heading" style="position: relative; left: 50px; top: 0; font-size:4cap;">
          Nourish Your Body.<br />
          <em class="highlight">Transform</em> Your<br />
          Life.
        </h1>

        <p class="hero-subtext"">
          NutriMatch connects patients with licensed Registered Nutritionist-Dietitians
          for structured Medical Nutrition Therapy — powered by FNRI food data, the
          full NCP framework, and secure clinical tools built for the Philippines.
        </p>

        <div class="hero-cta"style="position: relative; left: 50px; top: 0;">
          <button class="btn-primary">Find an RND →</button>
          <button class="btn-secondary">Join as Dietitian</button>
        </div>

        <div class="hero-tags" style="position: relative; left: 50px; top: 0;">
          <span class="tag"><span class="tag-icon">✓</span> PRC Verified RNDs</span>
          <span class="tag"><span class="tag-icon">🛡</span> RA 10173 Compliant</span>
          <span class="tag"><span class="tag-icon">📄</span> FNRI Food Database</span>
          <span class="tag"><span class="tag-icon">〜</span> Full NCP Framework</span>
        </div>
      </div>

      <div class="hero-image-wrap">
        <img
          src="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=900&q=80"
          alt="Healthy meal bowls"
          class="hero-img"
        />
        <div class="overlay-gradient"></div>

        <div class="stat-card stat-top">
          <div class="stat-number">200+</div>
          <div class="stat-label">Verified RNDs</div>
        </div>

        <div class="stat-card stat-bottom">
          <div class="stat-number">5,000+</div>
          <div class="stat-label">Patients Served</div>
        </div>

        <div class="screening-card">
          <div class="screening-title">PRE-CONSULTATION SCREENING</div>
          <div class="screening-row">
            <span class="screening-key">BMI</span>
            <span class="screening-value">23.4</span>
            <span class="screening-badge normal">Normal</span>
          </div>
          <div class="screening-row">
            <span class="screening-key">NRS-2002</span>
            <span class="screening-value">2</span>
            <span class="screening-badge risk">At Risk</span>
          </div>
          <div class="screening-rnd">
            <div class="rnd-avatar">IA</div>
            <div class="rnd-info">
              <div class="rnd-name">RND Ivy Hope Alba</div>
              <div class="rnd-spec">Diabetes · Renal Nutrition</div>
            </div>
            <div class="rnd-rating">★ 4.9</div>
          </div>
        </div>
      </div>
    </section>

    <!-- STATS BAR -->
    <div class="stats-bar" style="background-color: #EFBF04;">
      <div class="stat-item" v-for="stat in stats" :key="stat.label">
        <div class="stats-number">{{ stat.number }}</div>
        <div class="stats-label">{{ stat.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
const stats = [
  { number: '200+', label: 'Verified RNDs' },
  { number: '5,000+', label: 'Patients Served' },
  { number: '8', label: 'Core Modules' },
  { number: 'RA 10173', label: 'Compliant' },
]
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }


:global(html),
:global(body) {
  margin: 0;
  padding: 0;
  width: 100%;
  overflow-x: hidden;
}

:global(#app) {
  margin: 0;
  padding: 0;
  width: 100%;
  max-width: 100%;
}

.landing {
  font-family: 'Inter', sans-serif;
  background-color: #1a3a1a;
  color: #ffffff;
  width: 100%;
  min-height: 100vh;
  overflow-x: hidden;
}

/* NAVBAR */
.navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 48px;
  height: 68px;
  background-color: #162e16;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-logo { display: flex; align-items: center; gap: 10px; }
.logo-text { font-size: 1.3rem; font-weight: 700; }
.logo-nutri { color: #ffffff; }
.logo-match { color: #D4A017; }

.nav-links { display: flex; list-style: none; gap: 32px; }
.nav-links a { color: #c8d8c8; text-decoration: none; font-size: 0.9rem; font-weight: 500; transition: color 0.2s; }
.nav-links a:hover { color: #ffffff; }

.nav-actions { display: flex; gap: 12px; align-items: center; }

.btn-login {
  background: transparent; border: 1.5px solid #ffffff; color: #ffffff;
  padding: 8px 22px; border-radius: 24px; font-size: 0.88rem; font-weight: 500; cursor: pointer;
}
.btn-login:hover { background: rgba(255,255,255,0.08); }

.btn-get-started {
  background: #D4A017; border: none; color: #1a3a1a;
  padding: 8px 22px; border-radius: 24px; font-size: 0.88rem; font-weight: 700; cursor: pointer;
}
.btn-get-started:hover { background: #c4920f; }

/* HERO */
.hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  width: 100%;
  min-height: 100vh;
  overflow: hidden;
}

.hero-content {
  display: flex; flex-direction: column; justify-content: center;
  padding: 64px 64px 64px 130px; background: #063C2A; gap: 23px;
}

.hero-badge {
  display: inline-flex; align-items: center; gap: 10px;
  border: 1.5px solid #D4A017; color: #D4A017; border-radius: 24px;
  padding: 6px 16px; font-size: 0.60rem; font-weight: 100; letter-spacing: 0.08em; width: fit-content;
}

.badge-dot { width: 6px; height: 6px; border-radius: 50%; background: #D4A017; flex-shrink: 0; }

.hero-heading {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2.6rem, 4.5vw, 3.8rem);
  font-weight: 900;
  font-style: italic;
  line-height: 1.12;
  color: #ffffff;
}

.highlight { color: #D4A017; font-style: italic; }

.hero-subtext {
  font-size: 0.75rem;
  font-weight: 100;
  color: #a8c4a8;
  line-height: 1.7;
  position:relative; left: 50px; top: 0; line-height: 1.; word-spacing: 0.25em; max-width: 1010px; text-align: left; font-family:sans-serif;
  margin-bottom: 24px;
}

       



.hero-cta { display: flex; gap: 20px; align-items: center; }

.btn-primary {
  background: #EFBF04; border: none; color: #063C2A;
  padding: 14px 28px; border-radius: 8px; font-size: 0.75rem; font-weight: 700; cursor: pointer;
}
.btn-primary:hover { background: #c4920f; background: #EFBF04; box-shadow: 0 4px 10px rgb(255, 230, 2); }

.btn-secondary {
  background: transparent; border: 1.5px solid #6a9a6a; color: #c8e0c8;
  padding: 14px 28px; border-radius: 8px; font-size: 0.75rem; font-weight: 700; cursor: pointer;
}
.btn-secondary:hover { border-color: #ffffff; color: #ffffff; }

.hero-tags {
  display: flex;
  flex-wrap: nowrap;
  gap: 10px;
  overflow-x: auto;
}

.tag {
  display: inline-flex; align-items: center; gap: 10px;
  background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.15);
  color: #c8d8c8; border-radius: 20px; padding: 6px 14px; font-size: 0.70rem; font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

/* HERO IMAGE */
.hero-image-wrap { position: relative; overflow: hidden; }
.hero-img { width: 100%; height: 100%; object-fit: cover; display: block; }
.overlay-gradient {
  position: absolute; inset: 0;
  background: linear-gradient(to right, #063C2A 0%, transparent 150%);
  pointer-events: none;
}

.stat-card {
  position: absolute; background: #ffffff; color: #1a3a1a;
  border-radius: 12px; padding: 14px 20px; box-shadow: 0 8px 32px rgba(0,0,0,0.25); min-width: 140px;
  animation: float 4s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.stat-top { top: 250px; right: 50px; }
.stat-bottom { bottom: 200px; right: 32px; }
.stat-number { font-size: 1.1rem; font-weight: 800; color: #1a3a1a; font-family: 'Playfair Display', serif; }
.stat-label { font-size: 0.7rem; color: #5a7a5a; margin-top: 2px; font-weight: 200; font-family:Arial, Helvetica, sans-serif; }

.screening-card {
  position: absolute; bottom: 120px; right: 580px;
  background: #001E14; border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px; padding: 16px 20px; min-width: 260px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  animation: float 5s ease-in-out infinite;
}







.screening-title { font-size: 0.60rem; letter-spacing: 0.1em; color: #7aaa7a; font-weight: 100; margin-bottom: 35px; }
.screening-row { display: flex; align-items: center; gap: 5px; margin-bottom: 8px; }
.screening-key { font-size: 0.8rem; color: #c8d8c8; flex: 1; }
.screening-value { font-size: 0.65rem; font-weight: 700; color: #ffffff; min-width: 32px; text-align: right; }
.screening-badge { font-size: 0.65rem; font-weight: 300; border-radius: 12px; padding: 2px 10px; }
.screening-badge.normal { background: rgba(74,185,74,0.2); color: #6fda6f; }
.screening-badge.risk { background: rgba(220,150,40,0.2); color: #f0b04a; }
.screening-rnd { display: flex; align-items: center; gap: 10px; margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); }
.rnd-avatar { width: 34px; height: 34px; border-radius: 50%; background: #3a7a3a; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 300; color: #ffffff; flex-shrink: 0; }
.rnd-info { flex: 1; }
.rnd-name { font-size: 0.65rem; font-weight: 300; color: #ffffff; }
.rnd-spec { font-size: 0.65rem; color: #7aaa7a; margin-top: 2px; }
.rnd-rating { font-size: 0.65rem; font-weight: 700; color: #D4A017; }

/* STATS BAR */
.stats-bar {
  background: #D4A017;
  display: flex;
  justify-content: center;
  gap: 80px;
  padding: 28px 48px;
  width: 100%;
}
.stat-item { text-align: center; }
.stats-number { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 700; color: #1a3a1a; }
.stats-label { font-size: 0.82rem; color: #1a3a1a; margin-top: 2px; font-weight: 500; }

@media (max-width: 900px) {
  .hero { grid-template-columns: 1fr; }
  .hero-image-wrap { height: 400px; }
  .hero-content { padding: 48px 32px; }
  .navbar { padding: 0 24px; }
  .nav-links { display: none; }
  .stats-bar { gap: 32px; flex-wrap: wrap; }
}
</style>