<template>
  <section class="features" id="features" style="background-color: #F9F8F0;">
    <div class="features-header">
      <div class="eyebrow" style="color:#004635;"font-size: 0.75rem;><span class="eyebrow-line"></span> BUILT FOR FILIPINO HEALTHCARE</div>
      <h2>Everything for Clinical Nutrition Care</h2>
      <p style="font-family: 'Inter', sans-serif; font-size: 1rem; color: #5a7a5a; max-width: 600px; margin: 0 auto; line-height: 1.7;">
        From Client-RND matching to FNRI-compliant meal plans, every step of your care journey is covered.
      </p>
    </div>

    <div class="features-grid">
      <div class="feature-card" v-for="feature in features" :key="feature.title">
        <div class="feature-img-wrap">
          <img :src="feature.img" :alt="feature.title" class="feature-img" />
        </div>
        <h3>{{ feature.title }}</h3>
        <p>{{ feature.desc }}</p>
      </div>
    </div>

    <div class="features-cta">
      <button class="btn-gold">Start Your Nutrition Journey →</button>
    </div>
  </section>
</template>

<script setup>
const features = [
  {
    title: 'Filipino-First Meal Plans',
    desc: 'FNRI Food Exchange Lists, disease-specific templates for diabetes, hypertension & renal conditions.',
    img: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&q=80',
  },
  {
    title: 'Client-RND Matching',
    desc: 'Filter by specialty, language (Tagalog, Cebuano, Ilocano), and consultation mode — video, chat, in-person.',
    img: 'https://images.unsplash.com/photo-1543362906-acfc16c67564?w=400&q=80',
  },
  {
    title: 'Digital NCP Module',
    desc: 'Complete 4-phase Nutrition Care Process — Assessment, PES Diagnosis, Intervention, and Monitoring.',
    img: 'https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=400&q=80',
  },
  {
    title: 'Outcome Monitoring',
    desc: 'Track BMI, HbA1c, blood pressure & glucose with automated dashboards and longitudinal reports.',
    img: 'https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=400&q=80',
  },
]
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600&display=swap');

.features {
  background: #f5f5e8;
  padding: 100px 72px;
  font-family: 'Inter', sans-serif;
}

.features-header {
  text-align: center;
  margin-bottom: 56px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: #D4A017;
  margin-bottom: 16px;
}

.eyebrow-line {
  display: inline-block;
  width: 28px;
  height: 2px;
  background: #D4A017;
}

.features-header h2 {
  font-family: 'Playfair Display', serif;
  font-size: 2.4rem;
  font-weight: 700;
  color: #1a3a1a;
  margin-bottom: 16px;
}

.features-header p {
  font-size: 0.95rem;
  color: #5a7a5a;
  max-width: 480px;
  margin: 0 auto;
  line-height: 1.7;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 48px;
}

.feature-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 32px 24px;
  text-align: center;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
 
.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 24px 40px rgba(26, 58, 26, 0.16),
              0 8px 16px rgba(26, 58, 26, 0.08);
}

.feature-img-wrap {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 auto 24px;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
              box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}
 
.feature-card:hover .feature-img-wrap {
  transform: scale(1.08);
  box-shadow: 0 0 0 4px rgba(212, 160, 23, 0.25);
}


.feature-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}
 
.feature-card:hover .feature-img {
  transform: scale(1.1);
}

.feature-card h3 {
  font-family: 'Playfair Display', serif;
  font-size: 1.05rem;
  font-weight: 700;
  color: #1a3a1a;
  margin-bottom: 12px;
  transition: color 0.3s ease;
}
 
.feature-card:hover h3 {
  color: #00674F;
}

.feature-card p {
  font-size: 0.85rem;
  color: #6a8a6a;
  line-height: 1.65;
}
 
.features-cta {
  text-align: center;
}
 
.btn-gold {
  background: #EFBF04;
  border: none;
  color: #1a3a1a;
  padding: 16px 36px;
  border-radius: 32px;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}
 
.btn-gold:hover {
  background: #c4920f;
  transform: translateY(-2px);
}
 
@media (max-width: 900px) {
  .features-grid { grid-template-columns: repeat(2, 1fr); }
  .features { padding: 60px 24px; }
}
</style>
 



