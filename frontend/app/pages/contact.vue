<template>
  <div>
    <MarketingNavbar />

    <section class="page-hero">
      <p class="eyebrow">GET IN TOUCH</p>
      <h1 class="hero-title">We'd Love to Hear From You</h1>
      <p class="hero-sub">Questions about NutriMatch, partnership inquiries, or feedback on the platform — reach out below.</p>
    </section>

    <section class="page-content">
      <div class="contact-grid">
        <div class="email-card">
          <h3 class="card-title">Send Us a Message</h3>
          <p class="card-text">Click below to open your email client with our support address pre-filled. We aim to respond within 1–2 business days.</p>
          <a href="mailto:support@nutrimatch.ph?subject=NutriMatch%20Inquiry" class="email-btn">
            <Mail :size="16" /> Email Us
          </a>
        </div>

        <div class="info-card">
          <h3 class="card-title info-title">Contact Information</h3>
          <div class="info-row">
            <div class="info-icon"><Mail :size="16" /></div>
            <div><div class="info-label">Email</div><div class="info-value">support@nutrimatch.ph</div></div>
          </div>
          <div class="info-row">
            <div class="info-icon"><Phone :size="16" /></div>
            <div><div class="info-label">Phone</div><div class="info-value">(082) 123-4567</div></div>
          </div>
          <div class="info-row">
            <div class="info-icon"><MapPin :size="16" /></div>
            <div><div class="info-label">Institution</div><div class="info-value">STI College Davao, Davao City, Philippines</div></div>
          </div>
          <div class="info-row">
            <div class="info-icon"><Clock :size="16" /></div>
            <div><div class="info-label">Support Hours</div><div class="info-value">Mon–Fri, 9:00 AM – 6:00 PM PHT</div></div>
          </div>
          <div class="ra-badge-wrap"><span class="ra-badge">RA 10173 COMPLIANT</span></div>
        </div>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>

<script setup>
import { Mail, Phone, MapPin, Clock } from 'lucide-vue-next'
</script>

<style scoped>
* { box-sizing: border-box; }
div { font-family: 'Inter', sans-serif; }

.page-hero { background: #14301a; padding: 72px 48px; text-align: center; }
.eyebrow { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; color: #D4A017; margin: 0 0 12px; }
.hero-title { font-family: 'Playfair Display', serif; font-style: italic; color: #fff; font-size: 2.2rem; margin: 0; }
.hero-sub { color: #c9d9c9; max-width: 560px; margin: 16px auto 0; font-size: 0.95rem; }

.page-content { max-width: 1100px; margin: 0 auto; padding: 56px 24px; }
.contact-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 24px; }
@media (max-width: 800px) { .contact-grid { grid-template-columns: 1fr; } }

.email-card { background: #fff; border-radius: 14px; padding: 36px; border: 1px solid #eceeec; }
.card-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0 0 12px; }
.card-text { font-size: 0.88rem; color: #6a7a6a; line-height: 1.6; margin: 0 0 24px; }
.email-btn {
  display: inline-flex; align-items: center; gap: 8px; text-decoration: none;
  background: #D4A017; color: #1a3a1a; border-radius: 8px; padding: 12px 24px;
  font-weight: 700; font-size: 0.9rem;
}

.info-card { background: #14301a; border-radius: 14px; padding: 32px; color: #fff; }
.info-title { color: #fff; }
.info-row {
  display: flex; gap: 14px; align-items: flex-start; padding: 14px 0;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.info-row:last-of-type { border-bottom: none; }
.info-icon {
  width: 34px; height: 34px; border-radius: 8px; background: rgba(212,160,23,0.18); color: #D4A017;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.info-label { font-size: 0.74rem; color: #a9c0a9; }
.info-value { font-weight: 600; font-size: 0.88rem; margin-top: 2px; }

.ra-badge-wrap { margin-top: 18px; padding-top: 14px; border-top: 1px solid rgba(255,255,255,0.08); }
.ra-badge {
  display: inline-block; border: 1px solid rgba(122,170,122,0.5); color: #7aaa7a;
  font-size: 0.62rem; letter-spacing: 0.08em; padding: 4px 12px; border-radius: 4px;
}
</style>
