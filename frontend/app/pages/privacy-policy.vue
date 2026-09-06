<template>
  <div>
    <MarketingNavbar />

    <div class="legal-shell">
      <p class="eyebrow">LEGAL</p>
      <h1 class="legal-title">Privacy Policy</h1>
      <p class="legal-meta">Last updated: June 2026 · Compliant with Republic Act No. 10173 (Data Privacy Act of 2012)</p>

      <div class="toc-card">
        <div class="toc-title">ON THIS PAGE</div>
        <a href="#collection">1. Information We Collect</a>
        <a href="#use">2. How We Use Your Information</a>
        <a href="#sharing">3. Data Sharing &amp; Third Parties</a>
        <a href="#security">4. Security Measures</a>
        <a href="#rights">5. Your Rights Under RA 10173</a>
        <a href="#retention">6. Data Retention</a>
        <a href="#contact-dpo">7. Contact Our Data Protection Officer</a>
      </div>

      <p>NutriMatch ("we," "our," "the platform") is committed to protecting the privacy of Registered Nutritionist-Dietitians (RNDs), clients, and administrators who use our clinical nutrition consultation management system. This policy explains what personal and health-related data we collect, how it is used, and the rights you hold under Philippine law.</p>

      <h2 id="collection">1. Information We Collect</h2>
      <p>We collect identity information (name, email, phone), demographic data (date of birth, sex), and clinical data necessary for Medical Nutrition Therapy, including pre-consultation screening results (weight, height, BMI, NRS-2002 risk score), Nutrition Care Process records (assessment, diagnosis, intervention, monitoring notes), meal plans, and progress records (blood pressure, blood glucose, lipid profiles). RNDs additionally provide PRC license numbers and professional credentials for verification.</p>

      <h2 id="use">2. How We Use Your Information</h2>
      <ul>
        <li>To facilitate RND-client matching based on specialty, language, and consultation modality</li>
        <li>To support clinical documentation throughout the four-phase Nutrition Care Process</li>
        <li>To generate disease-specific meal plans using FNRI Food Exchange List data</li>
        <li>To process consultation payments and generate invoices</li>
        <li>To send appointment reminders and platform notifications</li>
        <li>To maintain immutable audit logs of significant account and clinical actions, as required for compliance</li>
      </ul>

      <h2 id="sharing">3. Data Sharing &amp; Third Parties</h2>
      <p>Clinical data is only accessible within an established, active RND-client relationship. We share limited data with third-party service providers strictly to deliver platform functionality: video conferencing providers for telehealth sessions, PayMongo for payment processing, and SMS gateways for appointment reminders. These providers are bound by their own data protection obligations and do not receive more data than necessary to perform their function.</p>

      <h2 id="security">4. Security Measures</h2>
      <p>NutriMatch implements SSL/TLS encryption for all data in transit, bcrypt password hashing, role-based access controls, and automated audit logging of significant data mutations. Communications are protected at the transport layer via HTTPS; please note this is not end-to-end encryption at the application layer.</p>

      <h2 id="rights">5. Your Rights Under RA 10173</h2>
      <p>As a data subject under the Data Privacy Act of 2012, you have the right to be informed, the right to access your personal data, the right to object to processing, the right to data portability, and the right to file a complaint with the National Privacy Commission. To exercise these rights, contact us using the information below.</p>

      <h2 id="retention">6. Data Retention</h2>
      <p>As a capstone academic system, NutriMatch does not currently implement an automated data retention schedule or granular consent revocation. Organizations deploying NutriMatch for clinical use are responsible for establishing retention policies appropriate to their practice and applicable regulations.</p>

      <h2 id="contact-dpo">7. Contact Our Data Protection Officer</h2>
      <p>For questions about this policy or to exercise your data subject rights, contact us at <strong>privacy@nutrimatch.ph</strong> or through our <NuxtLink to="/contact">Contact page</NuxtLink>.</p>

      <div class="info-note">
        <Info :size="16" />
        <p>As an academic capstone system, NutriMatch does not maintain formal Data Processing System registration with the National Privacy Commission. Institutions deploying this system for live clinical use are responsible for independent NPC registration.</p>
      </div>
    </div>

    <SiteFooter />
  </div>
</template>

<script setup>
import { Info } from 'lucide-vue-next'
</script>

<style scoped>
* { box-sizing: border-box; }
div { font-family: 'Inter', sans-serif; }

.legal-shell { max-width: 780px; margin: 0 auto; padding: 56px 24px 80px; }
.eyebrow { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; color: #8a9a8a; margin: 0 0 10px; }
.legal-title { font-family: 'Playfair Display', serif; font-size: 2rem; color: #1a3a1a; margin: 0; }
.legal-meta { font-size: 0.85rem; color: #8a9a8a; margin: 10px 0 28px; }

.toc-card { background: #eef3ec; border-radius: 12px; padding: 20px 24px; margin-bottom: 32px; }
.toc-title { font-size: 0.7rem; letter-spacing: 0.08em; font-weight: 700; color: #1e4a26; margin-bottom: 8px; }
.toc-card a { display: block; padding: 4px 0; font-size: 0.85rem; color: #1e4a26; text-decoration: none; font-weight: 500; }
.toc-card a:hover { text-decoration: underline; }

h2 { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 32px 0 12px; }
p, li { font-size: 0.9rem; color: #4a5a4a; line-height: 1.75; }
strong { color: #1a3a1a; }
:deep(a) { color: #1e4a26; font-weight: 600; }

.info-note {
  display: flex; gap: 10px; align-items: flex-start;
  background: #e3edf7; color: #2f6fa8; border-radius: 10px; padding: 14px 16px; margin-top: 28px;
}
.info-note p { color: #2f6fa8; font-size: 0.84rem; margin: 0; line-height: 1.6; }
</style>
