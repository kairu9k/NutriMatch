<template>
  <section class="testimonials" id="testimonials">
    <div class="testimonials-header">
      <div class="eyebrow"><span class="eyebrow-line"></span> TESTIMONIALS</div>
      <h2>Trusted by Clients &amp; Dietitians</h2>
      <p>Real stories from people whose lives have changed through expert nutrition guidance.</p>
    </div>

    <div class="cards">
      <div class="card" v-for="t in testimonials" :key="t.name">
        <div class="card-img-wrap">
          <img :src="t.img" :alt="t.name" class="card-img" />
        </div>
        <div class="stars">★★★★★</div>
        <p class="quote">{{ t.quote }}</p>
        <div class="reviewer">
          <div class="avatar">{{ t.initials }}</div>
          <div>
            <div class="reviewer-name">{{ t.name }}</div>
            <div class="reviewer-role">{{ t.role }}</div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
const testimonials = [
  {
    name: 'Julia Niel Bulalaque',
    initials: 'JB',
    role: 'Client — Diabetic Management',
    quote: 'NutriMatch helped me find an RND who speaks Cebuano and truly understands my diabetes. I feel heard for the first time.',
    img: 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=600&q=80',
  },
  {
    name: 'RND Ivy Hope Alba',
    initials: 'IA',
    role: 'Registered Nutritionist-Dietitian',
    quote: 'The digital NCP workflow is a complete game-changer. PES statements, lab tracking, and meal plans — all in one place.',
    img: 'https://images.unsplash.com/photo-1543362906-acfc16c67564?w=600&q=80',
  },
  {
    name: 'Kent Leabres',
    initials: 'KB',
    role: 'Client — Weight Management',
    quote: 'Lost 8 kilos in 3 months following my personalized FNRI meal plan. My RND adjusted recipes based on my actual labs.',
    img: 'https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=600&q=80',
  },
]
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600&display=swap');

.testimonials {
  background: #FDFBD4;
  padding: 100px 90px;
  font-family: 'Inter', sans-serif;
}

.testimonials-header {
  text-align: center;
  margin-bottom: 64px;
}

.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  color: #1a3a1a;
  margin-bottom: 1px;
}

.eyebrow-line {
  display: inline-block;
  width: 28px;
  height: 3px;
  background: #D4A017;
}

.testimonials-header h2 {
  font-family: 'Playfair Display', serif;
  font-size: 2.4rem;
  font-weight: 700;
  font-style: italic;
  color: #1a3a1a;
  margin-bottom: 12px;
}

.testimonials-header p {
  font-size: 0.95rem;
  color: #6a8a6a;
  max-width: 460px;
  margin: 0 auto;
  font-size: 0.75rem;
  line-height: 1.7;
}

.cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(250px, 1fr));
  justify-content: center;
  gap: 24px;
  width: 70%;
  margin: 0 auto;
}
.card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  cursor: pointer;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1),
 box-shadow 0.35s cubic-bezier(0.22, 1, 0.36, 1);
}

.card:hover {
  transform: translateY(-10px);
  box-shadow: 0 24px 40px rgba(26, 58, 26, 0.16),
   0 8px 16px rgba(26, 58, 26, 0.08);
}

.card-img-wrap {
  height: 180px;
  overflow: hidden;
}
.card-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  transition: transform 0.4s ease;
}

.card:hover .card-img {
  transform: scale(1.06);
}

.stars {
  color: #D4A017;
  font-size: 1rem;
  padding: 20px 24px 8px;
  letter-spacing: 2px;
}

.quote {
  font-size: 0.88rem;
  color: #2a4a2a;
  line-height: 1.7;
  padding: 0 24px 20px;
  font-size:0.75rem;
  font-style: italic;
}

.reviewer {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #f0f0e0;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #2a5a2a;
  color: #EFBF04;
  font-size: 0.72rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.reviewer-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1a3a1a;
}

.reviewer-role {
  font-size: 0.75rem;
  color: #8aaa8a;
  margin-top: 2px;
}

@media (max-width: 900px) {
  .cards { grid-template-columns: 1fr; }
  .testimonials { padding: 60px 24px; }
}
</style>