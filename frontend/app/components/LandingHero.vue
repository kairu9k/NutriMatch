<template>
  <div class="landing">
    <!-- HERO -->
    <section id="home" class="hero">
      <div class="dots dots-top" aria-hidden="true"></div>
      <div class="dots dots-bottom" aria-hidden="true"></div>
      <!-- soft leaves drifting at the screen edges -->
     

      <div class="hero-inner">
        <div class="hero-content">
          <h1 class="hero-heading">
            Nourish Your Body.<br />
            Transform Your<br />
            <em class="highlight">Life.<svg class="swoosh" viewBox="0 0 220 24" preserveAspectRatio="none" aria-hidden="true"><path d="M4 16 C 50 6, 120 4, 216 10 C 150 12, 90 16, 40 20" fill="none" stroke="#EFBF04" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" /></svg></em>
          </h1>

         
          <div class="hero-cta">
            <button class="btn-primary" @click="navigateTo('/register?role=client')">Find a dietitian</button>
            <button class="btn-secondary" @click="navigateTo('/register?role=rnd')">I'm an RND</button>
          </div>

          <div class="plate-guide">
            <span class="plate-guide-title">A BALANCED PLATE</span>
            <div class="plate-guide-items">
              <div v-for="p in plateParts" :key="p.label" class="plate-part">
                <img :src="p.img" :alt="p.label" class="plate-part-img" />
                <span class="plate-part-text">
                  <strong>{{ p.label }}</strong>
                  <span>{{ p.share }} of the plate</span>
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="hero-art">
          <div class="plate-box">
            <div class="plate-backdrop" aria-hidden="true"></div>
            <div class="plate-ring" aria-hidden="true"></div>
            <img
              :src="IMG.plate"
              alt="A balanced plate: half vegetables, a quarter whole grains and a quarter protein"
              class="plate-img"
            />

            <img
              v-for="(d, i) in decor"
              :key="i"
              :src="d.src"
              alt=""
              aria-hidden="true"
              class="decor"
              :class="d.kind"
              :style="d.style"
            />

            <div class="plate-badge badge-fnri">
              <span class="badge-icon" aria-hidden="true">
                <Check :size="16" :stroke-width="2.8" />
              </span>
              FNRI-based meal plans
            </div>

            <div class="plate-badge badge-balance">
              <span class="badge-icon badge-icon-lg" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a9 9 0 1 0 9 9h-9z" /><path d="M15 3.5A9 9 0 0 1 20.5 9H15z" /></svg>
              </span>
              <span class="badge-text">
                <strong>Balanced plate</strong>
                <span>½ veg · ¼ grains · ¼ protein</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- STANDARDS STRIP -->
    <section class="standards" aria-label="Standards">
      <span v-for="item in standards" :key="item">{{ item }}</span>
    </section>
  </div>
</template>

<script setup>
import { Check } from 'lucide-vue-next'

// Gold strip under the hero
const standards = [
  'FNRI Food Exchange Lists',
  'USDA FoodData Central',
  'Nutrition Care Process',
  'RA 10173 · RA 10862',
]

// Images live in frontend/public/landing/ (bound with :src so a missing file
// shows as a broken image instead of stopping the whole page)
const IMG = {
  plate: '/landing/plate.webp',
  leaf: '/landing/leaf.webp',
}

// The three parts of the plate shown under the buttons
const plateParts = [
  { img: '/landing/thumb-veg.webp', label: 'Vegetables', share: '½' },
  { img: '/landing/thumb-grains.webp', label: 'Whole grains', share: '¼' },
  { img: '/landing/thumb-protein.webp', label: 'Protein', share: '¼' },
]

// Leaves and tomatoes around the plate (positions are % of the plate box)
const LEAF = '/landing/leaf.webp'
const T1 = '/landing/tomato-1.webp'
const T2 = '/landing/tomato-2.webp'
const place = (pos, w, rot, flip = false) =>
  `${pos}; width: ${w}; transform: rotate(${rot}deg)${flip ? ' scaleY(-1)' : ''}`
const decor = [
  { src: LEAF, kind: 'leaf', style: place('left: -16%; top: 10%', '26%', -55) },
  { src: LEAF, kind: 'leaf', style: place('right: -4%; top: -3%', '17%', 35, true) },
  { src: LEAF, kind: 'leaf', style: place('right: -15%; top: 46%', '21%', 100) },
  { src: LEAF, kind: 'leaf', style: place('left: -15%; bottom: 40%', '19%', 200, true) },
  { src: LEAF, kind: 'leaf', style: place('right: 6%; bottom: -5%', '19%', 145) },
  { src: LEAF, kind: 'leaf', style: place('left: 30%; bottom: -9%', '15%', -165, true) },
  { src: LEAF, kind: 'leaf', style: place('left: 13%; top: 8%', '14%', -25) },
  { src: T1, kind: 'tomato', style: place('left: 12%; top: -5%', '12%', 10) },
  { src: T2, kind: 'tomato', style: place('right: -8%; top: 31%', '12%', -15) },
  { src: T1, kind: 'tomato', style: place('left: -9%; bottom: 30%', '11%', -30) },
  { src: T2, kind: 'tomato', style: place('right: 18%; bottom: -6%', '10%', 20) },
]

</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

:global(html),
:global(body) {
  margin: 0;
  padding: 0;
  width: 100%;
  /* clip, not hidden: this global rule stays loaded after leaving the landing
     page, and overflow-x: hidden would turn body into a scroll container and
     break the dashboard's sticky sidebar and top bar. */
  overflow-x: clip;
}

:global(#app) {
  margin: 0;
  padding: 0;
  width: 100%;
  max-width: 100%;
}

.landing {
  font-family: 'DM Sans', Arial, sans-serif;
  background: #FFFFFF;
  color: #1F2D27;
  width: 100%;
  -webkit-font-smoothing: antialiased;
}
.landing *, .landing *::before, .landing *::after { box-sizing: border-box; }

/* ---------- HERO ---------- */
.hero {
  position: relative;
  overflow: hidden;
  /* light green-to-cream shade; pinned to the screen (fixed) so it lines up
     exactly with the navbar, which uses the same background */
  background:
    radial-gradient(circle at 76% 48%, rgba(239, 191, 4, 0.30), rgba(239, 191, 4, 0) 48%),
    radial-gradient(circle at 6% 10%, rgba(6, 60, 42, 0.16), rgba(6, 60, 42, 0) 42%),
    linear-gradient(135deg, #DFECE3 0%, #EAF2E8 40%, #FBEFC8 100%);
  background-attachment: fixed;
}

/* Dot texture */
.dots {
  position: absolute;
  width: 220px;
  height: 220px;
  background-image: radial-gradient(#063C2A 1.4px, transparent 1.6px);
  background-size: 18px 18px;
  opacity: 0.12;
  pointer-events: none;
}
.dots-top { top: 120px; left: 24px; -webkit-mask-image: radial-gradient(circle, #000 40%, transparent 72%); mask-image: radial-gradient(circle, #000 40%, transparent 72%); }
.dots-bottom { bottom: 40px; right: 32px; -webkit-mask-image: radial-gradient(circle, #000 40%, transparent 72%); mask-image: radial-gradient(circle, #000 40%, transparent 72%); }

.hero-inner {
  position: relative;
  max-width: 1360px;
  /* fill the whole first screen, so the gold strip only shows after scrolling */
  min-height: 100vh;
  min-height: 100svh;
  margin: 0 auto;
  /* 90px clears the fixed navbar; the bottom space keeps the gold strip
     clear of the leaves under the plate */
  padding: calc(90px + 56px) clamp(20px, 3vw, 40px) 100px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 40px;
}

.hero-content {
  position: relative;
  z-index: 2;
  /* nudged a little to the left on wide screens (mirrors the plate on the right) */
  margin-left: clamp(-150px, -9vw, 0px);
  flex: 0 1 640px;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.hero-heading {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-style: italic;
  font-size: clamp(46px, 6vw, 82px);
  line-height: 1.08;
  font-weight: 700;
  letter-spacing: 1.2px;
  color: #10231B;
}
.highlight { position: relative; display: inline-block; font-style: italic; color: #063C2A; }

/* Gold brush stroke under "Life." */
.swoosh {
  position: absolute;
  left: 2%;
  bottom: -0.12em;
  width: 100%;
  height: 0.28em;
  z-index: -1;
  overflow: visible;
}

/* Heading moved down a little on its own (buttons and plate row stay where they are) */
.hero-heading { position: relative; top: 8px; }

.hero-subtext {
  margin: 0;
  max-width: 460px;
  font-size: 15px;
  line-height: 1.75;
  color: #4E5F57;
  text-align: justify;
}

.hero-cta { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 10px; }

/* Buttons + balanced plate move down together; the heading stays put.
   (position/top shifts them without changing the layout around them) */
.hero-cta, .plate-guide { position: relative; top: 64px; }

.btn-primary, .btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 56px;
  min-width: 210px;   /* both buttons the same, wider width */
  padding: 0 36px;
  border-radius: 999px;
  font-family: inherit;
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s, transform 0.15s;
}
.btn-primary {
  background: #063C2A;
  border: 1.5px solid #063C2A;
  color: #FFFFFF;
  box-shadow: 0 12px 24px -12px rgba(6, 60, 42, 0.8);
}
.btn-primary:hover { background: #0B5A3F; }
/* "I'm an RND": no green border, soft shadow instead */
.btn-secondary {
  background: #FFFFFF;
  border: 1.5px solid transparent;
  color: #063C2A;
  box-shadow: 0 12px 26px -12px rgba(6, 60, 42, 0.35), 0 2px 6px rgba(6, 60, 42, 0.06);
}
.btn-secondary:hover {
  background: #FFFFFF;
  transform: translateY(-2px);
  box-shadow: 0 16px 30px -12px rgba(6, 60, 42, 0.45), 0 2px 6px rgba(6, 60, 42, 0.08);
}
.btn-primary:active, .btn-secondary:active { transform: scale(0.98); }
.btn-primary:focus-visible, .btn-secondary:focus-visible { outline: 3px solid #EFBF04; outline-offset: 3px; }

/* Balanced plate thumbnails */
.plate-guide {
  margin-top: 20px;
  padding-top: 10px;
  border-top: 1px solid #EEF2EF;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.plate-guide-title { font-size: 12px; font-weight: 600; letter-spacing: 2px; color: #6E877B; }
.plate-guide-items { display: flex; flex-wrap: wrap; gap: 14px 26px; }
.plate-part { display: flex; align-items: center; gap: 12px; }
.plate-part-img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #FFFFFF;
  box-shadow: 0 10px 20px -10px rgba(6, 60, 42, 0.55);
}
.plate-part-text { display: flex; flex-direction: column; line-height: 1.3; }
.plate-part-text strong { font-size: 14px; font-weight: 700; color: #063C2A; }
.plate-part-text span { font-size: 12px; color: #4E5F57; }

/* Plate + decoration */
.hero-art {
  position: relative;
  flex: 1 1 460px;
  min-width: 0;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-right: clamp(-130px, -8vw, 0px);
}
.plate-box { position: relative; width: 100%; max-width: 740px; aspect-ratio: 1 / 1; }
/* Soft circle + dotted ring behind the plate */
.plate-backdrop {
  position: absolute;
  inset: -5%;
  border-radius: 50%;
  background: radial-gradient(circle at 50% 50%, #EEF4EF 0%, #EEF4EF 62%, rgba(238, 244, 239, 0) 72%);
  z-index: 0;
}
.plate-ring {
  position: absolute;
  inset: -9%;
  border-radius: 50%;
  border: 2px dashed rgba(6, 60, 42, 0.18);
  z-index: 0;
}
.plate-img {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  border: 14px solid #FFFFFF;
  box-shadow: 0 40px 70px -28px rgba(2, 26, 18, 0.65);
}
.decor { position: absolute; height: auto; z-index: 2; pointer-events: none; }
.decor.leaf { filter: drop-shadow(0 14px 12px rgba(20, 50, 20, 0.28)); }
.decor.tomato { filter: drop-shadow(0 12px 12px rgba(80, 20, 10, 0.25)); }

.edge-leaf { position: absolute; height: auto; opacity: 0.95; pointer-events: none; }
.edge-left { top: 36%; left: -70px; width: 160px; transform: rotate(-62deg); filter: blur(2.5px); }
.edge-right { top: 56%; right: -60px; width: 170px; transform: rotate(72deg); filter: blur(3px); }

.plate-badge {
  position: absolute;
  z-index: 3;
  display: flex;
  align-items: center;
  gap: 10px;
  border-radius: 999px;
  box-shadow: 0 14px 28px -14px rgba(2, 26, 18, 0.6);
}
.badge-fnri {
  right: -3%;
  top: 13%;
  padding: 10px 18px 10px 10px;
  background: #EFBF04;
  color: #063C2A;
  font-size: 14px;
  font-weight: 700;
}
.badge-balance {
  left: -2%;
  bottom: 9%;
  padding: 8px 18px 8px 8px;
  background: #FFFFFF;
}
.badge-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #063C2A;
  color: #EFBF04;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.badge-icon-lg { width: 36px; height: 36px; }
.badge-text { display: flex; flex-direction: column; line-height: 1.3; }
.badge-text strong { font-size: 14px; color: #063C2A; }
.badge-text span { font-size: 12px; color: #4E5F57; }

/* Gentle entrance + float (off for reduced motion) */
@media (prefers-reduced-motion: no-preference) {
  .hero-heading, .hero-subtext, .hero-cta, .plate-guide {
    animation: fadeUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
  }
  .hero-subtext { animation-delay: 0.08s; }
  .hero-cta { animation-delay: 0.16s; }
  .plate-guide { animation-delay: 0.24s; }
  .plate-badge { animation: float 5s ease-in-out infinite; }
  .plate-ring { animation: spin 60s linear infinite; }
  .swoosh path { stroke-dasharray: 260; stroke-dashoffset: 260; animation: draw 0.9s 0.5s ease-out forwards; }
  .badge-balance { animation-delay: 0.6s; }
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: none; }
}
@keyframes spin { to { transform: rotate(360deg); } }
@keyframes draw { to { stroke-dashoffset: 0; } }
@keyframes float {
  0%, 100% { translate: 0 0; }
  50% { translate: 0 -8px; }
}

/* ---------- STANDARDS STRIP (gold) ---------- */
.standards {
  background: #EFBF04;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 20px 40px;
  padding: 22px 24px;
  width: 100%;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.4px;
  color: #063C2A;
}

/* ---------- Tablet ---------- */
@media (max-width: 960px) {
  .hero-inner { min-height: 0; padding-top: calc(90px + 40px); padding-bottom: 88px; gap: 56px; }
  .hero-art { margin-right: 0; justify-content: center; padding: 0 6%; }
  .hero-content { margin-left: 0; }
}

/* ---------- Phone (navbar is 64px here) ---------- */
@media (max-width: 600px) {
  .hero-inner { padding: calc(64px + 28px) 20px 64px; gap: 44px; }
  .hero-heading { font-size: 44px; line-height: 1.08; letter-spacing: 0.6px; }
  .hero-cta, .plate-guide { top: 24px; }
  .hero-heading { top: 0; }
  .hero-cta .btn-primary, .hero-cta .btn-secondary { flex: 1 1 100%; }
  .hero-art { padding: 0 9%; }
  .edge-leaf { display: none; }
  .dots { width: 140px; height: 140px; }
  .dots-bottom { display: none; }
  .plate-badge { scale: 0.82; }
  .badge-fnri { right: -10%; top: 6%; transform-origin: right center; }
  .badge-balance { left: -10%; bottom: 4%; transform-origin: left center; }
  .standards { gap: 10px 24px; padding: 18px 16px; }
}
</style>