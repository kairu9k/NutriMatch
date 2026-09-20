<template>
  <div class="landing">
    <!-- HERO -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-badge">
          <span class="badge-dot"></span>
          DESIGNED FOR PHILIPPINE RNDS · RA 10173 COMPLIANT
        </div>

        <h1 class="hero-heading">
          Nourish Your Body.<br />
          <em class="highlight">Transform</em> Your Life.
        </h1>

        <p class="hero-subtext">
          NutriMatch connects patients with PRC-licensed Registered Nutritionist-Dietitians
          for structured Medical Nutrition Therapy, powered by FNRI food data and the
          full NCP framework.
        </p>

        <div class="hero-cta">
          <button class="btn-primary">Find an RND →</button>
          <button class="btn-secondary">Join as Dietitian</button>
        </div>

        <div class="hero-tags">
          <span class="tag"><Check class="tag-icon" :size="14" :stroke-width="2.5" /> PRC Verified RNDs</span>
          <span class="tag"><ShieldCheck class="tag-icon" :size="14" :stroke-width="2.5" /> RA 10173 Compliant</span>
          <span class="tag"><FileText class="tag-icon" :size="14" :stroke-width="2.5" /> FNRI Food Database</span>
          <span class="tag"><Activity class="tag-icon" :size="14" :stroke-width="2.5" /> Full NCP Framework</span>
        </div>
      </div>

      <div class="hero-image-wrap">
        <div class="hero-image-card">
          <div
            class="carousel-track"
            :style="{ transform: `translateX(-${currentSlide * 100}%)` }"
          >
            <img
              v-for="(img, i) in heroImages"
              :key="i"
              :src="img"
              alt="Healthy meal bowls prepared for patient nutrition consultations"
              class="hero-img"
            />
          </div>
          <div class="image-scrim"></div>

          <div class="carousel-dots">
            <button
              v-for="(img, i) in heroImages"
              :key="i"
              type="button"
              class="dot"
              :class="{ active: i === currentSlide }"
              :aria-label="`Show slide ${i + 1}`"
              @click="goToSlide(i)"
            ></button>
          </div>
        </div>

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
    <div class="stats-bar">
      <div class="stat-item" v-for="stat in stats" :key="stat.label">
        <div class="stats-number">{{ stat.number }}</div>
        <div class="stats-label">{{ stat.label }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Check, ShieldCheck, FileText, Activity } from 'lucide-vue-next'

const stats = [
  { number: '200+', label: 'Verified RNDs' },
  { number: '5,000+', label: 'Patients Served' },
  { number: '8', label: 'Core Modules' },
  { number: 'RA 10173', label: 'Compliant' },
]

const heroImages = [
  'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=900&q=80',
  'https://images.unsplash.com/photo-1490645935967-10de6ba17061?w=900&q=80',
  'https://images.unsplash.com/photo-1543352634-a1c51d9f1fa7?w=900&q=80',
]

const currentSlide = ref(0)
let carouselTimer = null

function goToSlide(i) {
  currentSlide.value = i
}

onMounted(() => {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (!prefersReducedMotion) {
    carouselTimer = setInterval(() => {
      currentSlide.value = (currentSlide.value + 1) % heroImages.length
    }, 4500)
  }
})

onUnmounted(() => {
  if (carouselTimer) clearInterval(carouselTimer)
})
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
  background-color: #F7F9F6;
  color: #123524;
  width: 100%;
  min-height: 100vh;
  overflow-x: hidden;
}

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
  padding: 80px 64px 80px 88px; gap: 22px;
}

.hero-badge {
  display: inline-flex; align-items: center; gap: 10px;
  border: 1.5px solid #1F5C3C; color: #1F5C3C; border-radius: 999px;
  padding: 7px 16px; font-size: 0.68rem; font-weight: 600; letter-spacing: 0.08em; width: fit-content;
}

.badge-dot { width: 6px; height: 6px; border-radius: 50%; background: #1F5C3C; flex-shrink: 0; }

.hero-heading {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2.6rem, 4.5vw, 3.8rem);
  font-weight: 700;
  line-height: 1.15;
  color: #123524;
}

.highlight { color: #1F5C3C; font-style: italic; }

.hero-subtext {
  font-size: 0.95rem;
  font-weight: 400;
  color: #55655C;
  line-height: 1.7;
  max-width: 460px;
  margin-bottom: 4px;
}

.hero-cta { display: flex; gap: 20px; align-items: center; }

.btn-primary {
  background: #123524; border: none; color: #ffffff;
  padding: 14px 28px; border-radius: 10px; font-size: 0.85rem; font-weight: 700; cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
}
.btn-primary:hover { background: #1F5C3C; box-shadow: 0 6px 18px rgba(18,53,36,0.25); }
.btn-primary:active { transform: scale(0.98); }

.btn-secondary {
  background: #ffffff; border: 1.5px solid #123524; color: #123524;
  padding: 14px 28px; border-radius: 10px; font-size: 0.85rem; font-weight: 700; cursor: pointer;
  transition: background 0.2s, transform 0.15s;
}
.btn-secondary:hover { background: rgba(18,53,36,0.06); }
.btn-secondary:active { transform: scale(0.98); }

.hero-tags {
  display: flex;
  flex-wrap: wrap;
  column-gap: 26px;
  row-gap: 10px;
}

.tag {
  display: inline-flex; align-items: center; gap: 8px;
  color: #4B5A50; font-size: 0.8rem; font-weight: 500;
  white-space: nowrap;
}

.tag-icon { color: #1F5C3C; flex-shrink: 0; }

/* HERO IMAGE */
.hero-image-wrap {
  position: relative; display: flex; align-items: center; justify-content: center;
  padding: 56px 56px 56px 24px;
}

.hero-image-card {
  position: relative; width: 100%; max-width: 560px; aspect-ratio: 4 / 5;
  border-radius: 28px; overflow: hidden;
  box-shadow: 0 30px 70px rgba(18,53,36,0.16), 0 8px 20px rgba(18,53,36,0.10);
}

.carousel-track {
  display: flex;
  width: 100%;
  height: 100%;
  transition: transform 0.9s cubic-bezier(0.65, 0, 0.35, 1);
}

.hero-img { width: 100%; height: 100%; object-fit: cover; display: block; flex-shrink: 0; }

.image-scrim {
  position: absolute; inset: auto 0 0 0; height: 35%;
  background: linear-gradient(to top, rgba(0,0,0,0.4), transparent);
  pointer-events: none;
}

.carousel-dots {
  position: absolute; bottom: 18px; left: 50%; transform: translateX(-50%);
  display: flex; gap: 8px; z-index: 5;
}

.dot {
  width: 8px; height: 8px; padding: 0; border: none; border-radius: 50%;
  background: rgba(255,255,255,0.5); cursor: pointer;
  transition: background 0.3s, width 0.3s;
}

.dot.active { background: #ffffff; width: 22px; border-radius: 4px; }

.stat-card {
  position: absolute; background: #ffffff; color: #123524;
  border-radius: 14px; padding: 14px 20px; box-shadow: 0 8px 32px rgba(18,53,36,0.18); min-width: 140px;
}

.stat-top { top: 150px; right: 150px; }
.stat-bottom { bottom: 150px; right: 100px; }
.stat-number { font-size: 1.1rem; font-weight: 800; color: #123524; font-family: 'Playfair Display', serif; }
.stat-label { font-size: 0.7rem; color: #5a7a5a; margin-top: 2px; font-weight: 500; font-family: 'Inter', sans-serif; }

.screening-card {
  position: absolute; left: -16px; bottom: 200px;
  background: #001E14; border: 1px solid rgba(255,255,255,0.12);
  border-radius: 14px; padding: 16px 20px; min-width: 250px; max-width: 270px;
  box-shadow: 0 16px 40px rgba(18,53,36,0.28);
}

.screening-title { font-size: 0.60rem; letter-spacing: 0.1em; color: #7aaa7a; font-weight: 600; margin-bottom: 20px; }
.screening-row { display: flex; align-items: center; gap: 5px; margin-bottom: 8px; }
.screening-key { font-size: 0.8rem; color: #c8d8c8; flex: 1; }
.screening-value { font-size: 0.65rem; font-weight: 700; color: #ffffff; min-width: 32px; text-align: right; }
.screening-badge { font-size: 0.65rem; font-weight: 500; border-radius: 999px; padding: 2px 10px; }
.screening-badge.normal { background: rgba(74,185,74,0.2); color: #6fda6f; }
.screening-badge.risk { background: rgba(220,150,40,0.2); color: #f0b04a; }
.screening-rnd { display: flex; align-items: center; gap: 10px; margin-top: 14px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); }
.rnd-avatar { width: 34px; height: 34px; border-radius: 50%; background: #3a7a3a; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 600; color: #ffffff; flex-shrink: 0; }
.rnd-info { flex: 1; }
.rnd-name { font-size: 0.65rem; font-weight: 500; color: #ffffff; }
.rnd-spec { font-size: 0.65rem; color: #7aaa7a; margin-top: 2px; }
.rnd-rating { font-size: 0.65rem; font-weight: 700; color: #f0b04a; }

/* Floating card motion: motivated by the "live monitoring" feel of the product, not decoration */
@media (prefers-reduced-motion: no-preference) {
  .stat-card, .screening-card { animation: float 5s ease-in-out infinite; }
  .stat-bottom { animation-delay: 0.4s; }
  .screening-card { animation-duration: 6s; animation-delay: 0.2s; }

  .hero-badge, .hero-heading, .hero-subtext, .hero-cta, .hero-tags {
    animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
  }
  .hero-badge { animation-delay: 0s; }
  .hero-heading { animation-delay: 0.06s; }
  .hero-subtext { animation-delay: 0.12s; }
  .hero-cta { animation-delay: 0.18s; }
  .hero-tags { animation-delay: 0.24s; }
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: none; }
}

/* STATS BAR */
.stats-bar {
  background: #E9F2EB;
  display: flex;
  justify-content: center;
  gap: 80px;
  padding: 28px 48px;
  width: 100%;
}
.stat-item { text-align: center; }
.stats-number { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 700; color: #123524; }
.stats-label { font-size: 0.82rem; color: #55655C; margin-top: 2px; font-weight: 500; }

@media (max-width: 900px) {
  .hero { grid-template-columns: 1fr; }
  .hero-content { padding: 48px 24px; }
  .hero-image-wrap { padding: 32px 24px 88px; }
  .hero-image-card { max-width: 100%; }
  .stats-bar { gap: 32px; flex-wrap: wrap; }

  .stat-card { padding: 10px 14px; min-width: unset; }
  .stat-top { top: 16px; right: 16px; }
  .stat-bottom { bottom: 56px; right: 16px; }
  .screening-card { left: 16px; right: 16px; bottom: 0; max-width: unset; padding: 12px 14px; }
  .screening-title { margin-bottom: 12px; }
  .screening-rnd { margin-top: 10px; padding-top: 8px; }
}
</style>
