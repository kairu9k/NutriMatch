<template>
  <section class="for-rnds" id="for-rnds">
    <div class="for-rnds-image">
      <img src="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&q=80" alt="Healthy food" />
    </div>
    <div class="for-rnds-content">
      <div class="eyebrow"><span class="eyebrow-line"></span> FOR REGISTERED NUTRITIONIST-DIETITIANS</div>
      <h2>Modernize Your<br /><em class="highlight">Clinical Practice</em></h2>
      <p>Replace paper records with a fully digital NCP workflow — from NRS-2002 screening to disease-specific meal planning and outcome reports.</p>

      <ul class="features-list">
        <li v-for="item in features" :key="item">
          <span class="check">✓</span> {{ item }}
        </li>
      </ul>

      <div class="ncp-card">
        <div class="ncp-title">NCP Record — Phase Progress</div>
        <div class="ncp-phase" v-for="phase in phases" :key="phase.title" :class="{ active: phase.active }">
          <div class="phase-dot" :class="{ active: phase.active }"></div>
          <div>
            <div class="phase-title">{{ phase.title }}</div>
            <div class="phase-sub">{{ phase.sub }}</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const features = [
  'Auto-generated PES statements',
  'NRS-2002 nutritional risk scoring',
  'WHO Asia-Pacific BMI thresholds',
  'FNRI Food Exchange integration',
  'RA 10173-compliant audit logging',
]

const phases = [
  { title: 'Phase 1 — Nutritional Assessment', sub: 'BMI 23.4 · NRS Score 2 · At Risk', active: true },
  { title: 'Phase 2 — Nutrition Diagnosis', sub: 'Inadequate carb intake r/t poor dietary knowledge', active: true },
  { title: 'Phase 3 — Intervention', sub: '1800 kcal diabetic diet · FNRI Exchange', active: false },
  { title: 'Phase 4 — Monitoring & Evaluation', sub: 'Pending follow-up — May 30, 2026', active: false },
]
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600&display=swap');

.for-rnds {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 600px;
  font-family: 'Inter', sans-serif;
}

.for-rnds-image img {
  width: 100%; height: 100%; object-fit: cover; display: block;
}

.for-rnds-content {
  background: #E8F1ED;
  padding: 72px 56px;
  display: flex; flex-direction: column; justify-content: center; gap: 20px;
}

.eyebrow {
  display: inline-flex; align-items: center; gap: 10px;
  font-size: 0.72rem; font-weight: 600; letter-spacing: 0.2em; color: #004635;
}
.eyebrow-line { display: inline-block; width: 28px; height: 3px; background: #D4A017; }

.for-rnds-content h2 {
  font-family: 'Playfair Display', serif;
  font-size: 2.2rem; font-weight: 700; color: #1a3a1a; line-height: 1.1; letter-spacing: 0.03em; margin-bottom: auto;
}
.highlight { color: #D4A017; font-style: italic; }

.for-rnds-content > p {
  font-size: 0.75rem; color: #4a6a4a; line-height: 1.7; max-width: 480px;
}

.features-list { list-style: none; display: flex; flex-direction: column; gap: 10px; }
.features-list li { display: flex; align-items: center; gap: 10px; font-size: 0.88rem; color: #2a4a2a; font-weight: 500; }
.check {
  width: 22px; height: 22px; border-radius: 50%; background: #2a5a2a;
  color: #EFBF04; font-size: 0.7rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}

.ncp-card {
  background: #ffffff; border-radius: 14px; padding: 24px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08); margin-top: 8px;
}
.ncp-title { font-size: 0.8rem; font-weight: 600; color: #1a3a1a; margin-bottom: 18px; }
.ncp-phase {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 10px 0; border-bottom: 1px solid #f0f0e8;
}
.ncp-phase:last-child { border-bottom: none; }
.phase-dot {
  width: 14px; height: 14px; border-radius: 50%;
  border: 2px solid #cccccc; flex-shrink: 0; margin-top: 2px;
  background: #ffffff;
}
.phase-dot.active { background: #2a5a2a; border-color: #2a5a2a; }
.phase-title { font-size: 0.82rem; font-weight: 600; color: #1a3a1a; }
.phase-sub { font-size: 0.75rem; color: #8aaa8a; margin-top: 2px; }

@media (max-width: 900px) {
  .for-rnds { grid-template-columns: 1fr; }
  .for-rnds-image { height: 300px; }
  .for-rnds-content { padding: 48px 24px; }
}
</style>