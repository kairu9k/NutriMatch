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

    <!-- FOOTER -->
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
          <a href="#features">Features</a>
          <a href="#how-it-works">How It Works</a>
          <a href="#testimonials">Reviews</a>
          <a href="#faqs">FAQ</a>
        </div>

        <div class="footer-col">
          <div class="footer-col-title">FOR USERS</div>
          <a href="#">Sign Up as Patient</a>
          <a href="#">Register as RND</a>
          <a href="#">Log In</a>
        </div>

        <div class="footer-col">
          <div class="footer-col-title">LEGAL</div>
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
          <a href="#">RA 10173 Compliance</a>
          <a href="#">NPC Advisory</a>
        </div>
      </div>

      <div class="footer-bottom">
        <span>© 2026 NutriMatch · BSIT Group 12 · STI College Davao · Timtim · Alba · Bulalaque · Leabres</span>
        <div class="footer-links">
          <a href="#">Privacy</a>
          <a href="#">Terms</a>
          <a href="#">Contact</a>
        </div>
      </div>
    </footer>
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

.footer-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 48px;
  margin-bottom: 55px;
}

.footer-logo-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.logo-img {width: 36px; height : 36px; object-fit: contain;}
.footer-logo {
  font-size: 1.2rem; font-weight: 700; font-family: 'Playfair Display', serif; letter-spacing: 0.02em;
}
.logo-nutri { color: #004635; }
.logo-match { color: #EFBF04; }




.footer-brand p {
  font-size: 0.75rem; color: #6a8a6a; line-height: 1.7; margin-bottom: 16px; max-width: 280px;
}

.ra-badge {
  display: inline-block; border: 1px solid #3a6a3a; color: #7aaa7a;
  font-size: 0.55rem; letter-spacing: 0.08em; padding: 4px 12px; border-radius: 4px;
}

.footer-col { display: flex; flex-direction: column; gap: 12px; }

.footer-col-title {
  font-size: 0.75rem; letter-spacing: 0.12em; font-weight: 600; color: #6a8a6a; margin-bottom: 4px;
}

.footer-col a {
  font-size: 0.75rem; color: #c8d8c8; text-decoration: none; transition: color 0.2s;
}
.footer-col a:hover { color: #ffffff; }

.footer-bottom {
  border-top: 1px solid #1a4a1a;
  padding-top: 24px;
  display: flex; justify-content: space-between; align-items: center;
  font-size: 0.75rem; color: #4a6a4a;
}

.footer-links { display: flex; gap: 20px; }
.footer-links a { color: #4a6a4a; text-decoration: none; }
.footer-links a:hover { color: #c8d8c8; }

@media (max-width: 900px) {
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .footer { padding: 48px 24px 24px; }
  .cta { padding: 72px 24px; }
}
</style>