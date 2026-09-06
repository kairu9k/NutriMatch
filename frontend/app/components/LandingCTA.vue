<template>
  <div>
    <!-- CTA SECTION -->
    <section class="cta">
      <div class="cta-circle"></div>
      <div class="cta-content">
        <h2>Start Your<br /><em class="highlight">Nutrition Journey</em><br />Today.</h2>
        <p>Join Filipino patients and RNDs already using NutriMatch. Free to sign up. No commitment required.</p>
        <div class="cta-buttons">
          <button class="btn-gold">I'm a Patient →</button>
          <button class="btn-outline">I'm an RND →</button>
        </div>
        <div class="cta-badges">
          Free to join · PRC-verified RNDs only · RA 10173 compliant
        </div>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>


<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600&display=swap');

/* CTA */
.cta {
  background: #004635;
  padding: 150px 60px;
  text-align: center;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', sans-serif;
}

.cta-circle {
  position: absolute;
  top: 15%; left: 50%;
  transform: translate(-50%, -50%);
  width: 520px; height: 520px;
  border-radius: 50%;
  background: rgba(255,255,255,0.04);
  pointer-events: none;
}

.cta-content { position: relative; z-index: 1; max-width: 560px; margin: 0 auto; }

.cta-content h2 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 700; font-style: italic;
  color: #ffffff; line-height: 1.3; margin-bottom: 50px;
}

.highlight { color: #D4A017; font-style: italic; }

.cta-content p {
  font-size: 0.75rem; color: #a8c4a8; line-height: 1.7; margin-bottom: 30px;

}

.cta-buttons { display: flex; gap: 16px; justify-content: center; margin-bottom: 50px; }

.btn-gold {
  background: #D4A017; border: none; color: #1a3a1a;
  padding: 14px 28px; border-radius: 32px; font-size: 0.95rem; font-weight: 500; cursor: pointer;
}
.btn-gold:hover { background: #c4920f; }

.btn-outline {
  background: transparent; border: 1.5px solid #ffffff; color: #ffffff;
  padding: 14px 28px; border-radius: 32px; font-size: 0.95rem; font-weight: 500; cursor: pointer;
}
.btn-outline:hover { background: rgba(255,255,255,0.08); }

.cta-badges { font-size: 0.78rem; color: #7aaa7a; }

/* FOOTER */
.footer {
  background: #0D1F18;
  padding: 56px 72px 32px;
  font-family: 'Inter', sans-serif;
}

@media (max-width: 900px) {
  .cta { padding: 72px 24px; }
}
</style>