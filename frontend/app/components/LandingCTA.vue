<template>
  <div>
    <!-- CTA SECTION -->
    <section class="nm-cta">
      <div class="nm-cta-card">
        <!-- soft diagonal and gold glow in the background -->
        <div class="nm-cta-diagonal" aria-hidden="true"></div>
        <div class="nm-cta-glow" aria-hidden="true"></div>

        <div class="nm-cta-text">
          <span class="nm-cta-eyebrow">
            <span class="nm-cta-line" aria-hidden="true"></span>
            GET STARTED
          </span>
          <h2>Start your <em>nutrition journey</em> today</h2>
          <p>
            Create a free account and get matched with a dietitian who understands your needs,
            your language and your food.
          </p>
          <div class="nm-cta-buttons">
            <button type="button" class="nm-cta-btn nm-cta-btn--gold" @click="navigateTo('/register?role=client')">Create account</button>
            <button type="button" class="nm-cta-btn nm-cta-btn--glass" @click="navigateTo('/register?role=rnd')">Join as RND</button>
          </div>
          <ul class="nm-cta-checks">
            <li v-for="item in checks" :key="item">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5L20 7" /></svg>
              {{ item }}
            </li>
          </ul>
        </div>

        <div class="nm-cta-art">
          <img :src="plateImg" alt="" class="nm-cta-plate" />
        </div>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>

<script setup>
// Plate photo from frontend/public/landing/
const plateImg = '/landing/plate.webp'

const checks = ['Free to sign up', 'PRC-verified RNDs', 'RA 10173 compliant']
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

/* Same light shade as the FAQ above and the navbar, so it all reads as one area */
.nm-cta {
  background:
    radial-gradient(circle at 76% 48%, rgba(239, 191, 4, 0.30), rgba(239, 191, 4, 0) 48%),
    radial-gradient(circle at 6% 10%, rgba(6, 60, 42, 0.16), rgba(6, 60, 42, 0) 42%),
    linear-gradient(135deg, #DFECE3 0%, #EAF2E8 40%, #FBEFC8 100%);
  background-attachment: fixed;
  padding: 0 clamp(16px, 2vw, 32px) 80px;
  font-family: 'DM Sans', Arial, sans-serif;
}
.nm-cta *, .nm-cta *::before, .nm-cta *::after { box-sizing: border-box; }

.nm-cta-card {
  position: relative;
  max-width: 1760px;
  margin: 0 auto;
  border-radius: 28px;
  background: #063C2A;
  overflow: hidden;
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
}
.nm-cta-diagonal {
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.05);
  clip-path: polygon(42% 100%, 78% 0, 100% 0, 100% 100%);
}
.nm-cta-glow {
  position: absolute;
  width: 520px;
  height: 520px;
  left: -220px;
  top: -260px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(239, 191, 4, 0.22), rgba(239, 191, 4, 0) 65%);
  pointer-events: none;
}

/* Left: text */
.nm-cta-text {
  position: relative;
  flex: 1 1 520px;
  min-width: 0;
  padding: clamp(36px, 5vw, 64px);
  display: flex;
  flex-direction: column;
  gap: 20px;
  color: #FFFFFF;
}
.nm-cta-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 2px;
  color: #EFBF04;
}
.nm-cta-line {
  display: inline-block;
  width: 32px;
  height: 3px;
  border-radius: 2px;
  background: #EFBF04;
}
.nm-cta-text h2 {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: clamp(30px, 3.8vw, 48px);
  line-height: 1.1;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: #FFFFFF;
}
.nm-cta-text h2 em { font-style: italic; font-weight: 700; color: #EFBF04; }
.nm-cta-text p {
  margin: 0;
  max-width: 460px;
  font-size: 16px;
  line-height: 1.7;
  color: #CFE0D7;
}

.nm-cta-buttons { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 6px; }
.nm-cta-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 52px;
  padding: 0 28px;
  border: none;
  border-radius: 999px;
  font-family: inherit;
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition: background 0.2s, transform 0.15s;
}
.nm-cta-btn--gold { background: #EFBF04; color: #063C2A; }
.nm-cta-btn--gold:hover { background: #e0b204; }
.nm-cta-btn--glass { background: rgba(255, 255, 255, 0.14); color: #FFFFFF; }
.nm-cta-btn--glass:hover { background: rgba(255, 255, 255, 0.22); }
.nm-cta-btn:active { transform: scale(0.98); }
.nm-cta-btn:focus-visible { outline: 3px solid #FFFFFF; outline-offset: 3px; }

.nm-cta-checks {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  font-size: 13px;
  color: #CFE0D7;
}
.nm-cta-checks li { display: inline-flex; align-items: center; gap: 8px; }
.nm-cta-checks svg { color: #EFBF04; flex-shrink: 0; }

/* Right: plate peeking out of the card edge */
.nm-cta-art {
  position: relative;
  flex: 1 1 340px;
  min-height: 320px;
}
.nm-cta-plate {
  position: absolute;
  width: 460px;
  height: 460px;
  right: -70px;
  top: 50%;
  margin-top: -230px;
  border-radius: 50%;
  border: 10px solid rgba(255, 255, 255, 0.9);
  object-fit: cover;
  box-shadow: 0 30px 60px -20px rgba(0, 0, 0, 0.6);
}

/* Tablet */
@media (max-width: 960px) {
  .nm-cta { padding-bottom: 64px; }
}

/* Phone: buttons full width, plate peeks up from the bottom */
@media (max-width: 600px) {
  .nm-cta { padding-bottom: 56px; }
  .nm-cta-buttons { flex-direction: column; align-items: stretch; }
  .nm-cta-art { min-height: 200px; }
  .nm-cta-plate {
    width: 300px;
    height: 300px;
    right: 50%;
    margin-right: -150px;
    top: auto;
    bottom: -130px;
    margin-top: 0;
  }
}
</style>