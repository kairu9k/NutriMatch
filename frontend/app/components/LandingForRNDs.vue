<template>
  <!-- "For RNDs" in the navbar covers both parts: the green NCP section
       and the meal plans & privacy section right under it -->
  <div id="for-rnds">
  <section class="rnd-section">
    <!-- slanted top edge, same light shade as the "How it works" section above -->
    <div class="rnd-slant" aria-hidden="true"></div>

    <div class="rnd-inner">
      <div class="rnd-text">
        <span class="rnd-eyebrow">
          <span class="rnd-eyebrow-line" aria-hidden="true"></span>
          FOR DIETITIANS
        </span>
        <h2 class="rnd-title">Less paperwork.<br /><em>More care.</em></h2>
        <p class="rnd-lead">
          NutriMatch runs the full Nutrition Care Process digitally and handles the computation, so you
          can focus on your clients. Automated outputs support, never replace, your clinical judgment.
        </p>
        <NuxtLink to="/register?role=rnd" class="rnd-btn">Apply as an RND</NuxtLink>
      </div>

      <div class="rnd-grid">
        <div v-for="(phase, i) in phases" :key="phase.title" class="rnd-card">
          <span class="rnd-card-label">{{ String(i + 1).padStart(2, '0') }} — {{ phase.title }}</span>
          <p>{{ phase.desc }}</p>
        </div>
      </div>
    </div>
  </section>

  <!-- MEAL PLANS & PRIVACY (part of "For RNDs") -->
  <section class="nm-meal">
    <div class="nm-meal-inner">
      <div class="nm-meal-header">
        <span class="nm-meal-eyebrow">
          <span class="nm-meal-line" aria-hidden="true"></span>
          MEAL PLANS &amp; PRIVACY
          <span class="nm-meal-line" aria-hidden="true"></span>
        </span>
        <h2>Made for <em>Filipino tables</em></h2>
      </div>

      <div class="nm-meal-grid">
        <!-- Diet templates -->
        <div class="nm-meal-card">
          <h3>Disease-specific diet templates</h3>
          <p>
            FNRI Food Exchange Lists for what you actually eat at home, plus USDA FoodData Central
            for nutrient accuracy.
          </p>
          <div class="nm-meal-chips">
            <span v-for="t in templates" :key="t" class="nm-meal-chip">{{ t }}</span>
          </div>
        </div>

        <!-- Privacy -->
        <div class="nm-meal-card nm-meal-card--warm">
          <h3>Your records, handled with care</h3>
          <ul class="nm-meal-checks">
            <li v-for="item in privacy" :key="item">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5L20 7" /></svg>
              <span>{{ item }}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
  </div>
</template>

<script setup>
// The four phases of the Nutrition Care Process
const phases = [
  { title: 'ASSESSMENT', desc: 'Automatic BMI, BMR and NRS-2002 risk with WHO Asia-Pacific BMI thresholds.' },
  { title: 'DIAGNOSIS', desc: 'Structured PES statements from standard terms for clear, consistent nutrition diagnoses.' },
  { title: 'INTERVENTION', desc: 'Total Energy Requirement, macro targets, diet prescription and FNRI exchange-based meal plans.' },
  { title: 'MONITORING', desc: 'Charts for weight, BMI, BP, glucose and lipids, with automated alerts and RA 10173-compliant audit logging.' },
]

// Conditions with ready meal-plan templates
const templates = [
  'Diabetes mellitus',
  'Hypertension',
  'Renal disease',
  'Weight management',
  'Malnutrition',
]

const privacy = [
  'Designed for the Data Privacy Act (RA 10173), with digital informed consent',
  'Encrypted connection and hashed passwords',
  'Role-based access, and every time someone opens your records it is logged',
  "Every RND's PRC license checked by an administrator",
]
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

.rnd-section {
  position: relative;
  overflow: hidden;
  background: #063C2A;
  color: #FFFFFF;
  font-family: 'DM Sans', Arial, sans-serif;
}
.rnd-section *, .rnd-section *::before, .rnd-section *::after { box-sizing: border-box; }

.rnd-slant {
  position: absolute;
  /* starts 2px above the section so no thin green line shows at the seam */
  top: -2px;
  left: 0;
  right: 0;
  height: 66px;
  /* same shade as "How it works" above (fixed, so it lines up exactly) */
  background:
    radial-gradient(circle at 76% 48%, rgba(239, 191, 4, 0.30), rgba(239, 191, 4, 0) 48%),
    radial-gradient(circle at 6% 10%, rgba(6, 60, 42, 0.16), rgba(6, 60, 42, 0) 42%),
    linear-gradient(135deg, #DFECE3 0%, #EAF2E8 40%, #FBEFC8 100%);
  background-attachment: fixed;
  clip-path: polygon(0 0, 100% 0, 100% 0, 0 100%);
}

.rnd-inner {
  position: relative;
  max-width: 1180px;
  margin: 0 auto;
  padding: 128px 24px 96px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 56px;
}

/* Left: text */
.rnd-text {
  flex: 1 1 380px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.rnd-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 2px;
  color: #EFBF04;
}
.rnd-eyebrow-line {
  display: inline-block;
  width: 32px;
  height: 3px;
  border-radius: 2px;
  background: #EFBF04;
}
.rnd-title {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: clamp(28px, 3.4vw, 42px);
  line-height: 1.15;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: #FFFFFF;
}
.rnd-title em { font-style: italic; font-weight: 700; color: #EFBF04; }
.rnd-lead {
  margin: 0;
  max-width: 460px;
  font-size: 16px;
  line-height: 1.75;
  color: #CFE0D7;
  text-align: justify;
}
.rnd-btn {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 52px;
  padding: 0 30px;
  border-radius: 999px;
  background: #EFBF04;
  color: #063C2A;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  transition: background 0.2s, transform 0.15s;
}
.rnd-btn:hover { background: #e0b204; }
.rnd-btn:active { transform: scale(0.98); }
.rnd-btn:focus-visible { outline: 3px solid #FFFFFF; outline-offset: 3px; }

/* Right: NCP phase cards */
.rnd-grid {
  flex: 1 1 520px;
  min-width: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.rnd-card {
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 12px;
  padding: 26px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: background 0.2s, border-color 0.2s;
}
.rnd-card:hover { background: rgba(255, 255, 255, 0.05); border-color: rgba(239, 191, 4, 0.45); }
.rnd-card-label {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 2px;
  color: #EFBF04;
}
.rnd-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #E3EDE7;
}

/* Tablet */
@media (max-width: 960px) {
  .rnd-inner { padding: 104px 24px 72px; }
}

/* Phone: one card per row */
@media (max-width: 600px) {
  .rnd-inner { padding: 88px 20px 56px; gap: 40px; }
  .rnd-slant { height: 42px; }
  .rnd-grid { grid-template-columns: 1fr; }
  .rnd-btn { align-self: stretch; }
}

/* ================= MEAL PLANS & PRIVACY ================= */
.nm-meal {
  /* same light shade as the navbar and other sections */
  background:
    radial-gradient(circle at 76% 48%, rgba(239, 191, 4, 0.30), rgba(239, 191, 4, 0) 48%),
    radial-gradient(circle at 6% 10%, rgba(6, 60, 42, 0.16), rgba(6, 60, 42, 0) 42%),
    linear-gradient(135deg, #DFECE3 0%, #EAF2E8 40%, #FBEFC8 100%);
  background-attachment: fixed;
  font-family: 'DM Sans', Arial, sans-serif;
}
.nm-meal *, .nm-meal *::before, .nm-meal *::after { box-sizing: border-box; }

.nm-meal-inner {
  max-width: 1180px;
  margin: 0 auto;
  padding: 96px 24px;
  display: flex;
  flex-direction: column;
  gap: 48px;
}

/* Header */
.nm-meal-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 16px;
}
.nm-meal-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 2px;
  color: #063C2A;
}
.nm-meal-line {
  display: inline-block;
  width: 32px;
  height: 3px;
  border-radius: 2px;
  background: #EFBF04;
}
.nm-meal-header h2 {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: clamp(28px, 3.4vw, 42px);
  line-height: 1.15;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: #1F2D27;
}
.nm-meal-header h2 em { font-style: italic; font-weight: 700; color: #063C2A; }

/* Two cards */
.nm-meal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
}
.nm-meal-card {
  border: 1px solid #E3EBE5;
  box-shadow: 0 10px 24px -18px rgba(6, 60, 42, 0.35);
  border-radius: 12px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  background: #FFFFFF;
}
.nm-meal-card--warm { background: #FFFBEA; }
.nm-meal-card h3 {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 22px;
  font-weight: 700;
  color: #063C2A;
}
.nm-meal-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.7;
  color: #4E5F57;
}

.nm-meal-chips { display: flex; flex-wrap: wrap; gap: 10px; }
.nm-meal-chip {
  font-size: 13px;
  font-weight: 500;
  padding: 10px 16px;
  border-radius: 6px;
  background: #EEF4F0;
  color: #063C2A;
}

.nm-meal-checks {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.nm-meal-checks li {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 14px;
  line-height: 1.6;
  color: #2F3E37;
}
.nm-meal-checks svg { flex-shrink: 0; margin-top: 1px; color: #063C2A; }

/* Tablet */
@media (max-width: 960px) {
  .nm-meal-inner { padding: 72px 24px; }
}

/* Phone: cards stack */
@media (max-width: 600px) {
  .nm-meal-inner { padding: 56px 20px; gap: 36px; }
  .nm-meal-grid { grid-template-columns: 1fr; }
  .nm-meal-card { padding: 24px; }
}
</style>