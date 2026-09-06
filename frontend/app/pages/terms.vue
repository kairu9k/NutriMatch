<template>
  <div>
    <MarketingNavbar />

    <div class="legal-shell">
      <p class="eyebrow">LEGAL</p>
      <h1 class="legal-title">Terms &amp; Conditions</h1>
      <p class="legal-meta">Last updated: June 2026</p>

      <h2>1. Acceptance of Terms</h2>
      <p>By creating an account on NutriMatch, you agree to be bound by these Terms &amp; Conditions. NutriMatch is a web-based clinical nutrition consultation management system connecting clients with licensed Registered Nutritionist-Dietitians (RNDs) in the Philippines.</p>

      <h2>2. Eligibility &amp; Roles</h2>
      <p>NutriMatch operates under three roles: Client, RND, and Administrator. RND accounts require a valid, unexpired PRC (Professional Regulation Commission) license number, which is manually verified by an administrator before clinical features become accessible. Clinical features — including the Nutrition Care Process, meal planning, and progress monitoring — are only accessible within a formally established, active RND-client relationship.</p>

      <h2>3. Nature of the Service</h2>
      <p>NutriMatch provides tools to support, not replace, professional clinical judgment. Automated computations including BMI, BMR, TDEE, and NRS-2002 nutritional risk scoring are intended as decision-support aids. Final clinical decisions remain the responsibility of the supervising RND. NutriMatch is not a substitute for emergency medical care.</p>

      <h2>4. Payments &amp; Billing</h2>
      <p>Consultation fees are set independently by each RND and displayed on their profile prior to booking. Payments are processed through PayMongo, a third-party payment provider. NutriMatch retains a platform commission on completed transactions, frozen at the rate in effect at the time of the transaction.</p>

      <h2>5. User Conduct</h2>
      <ul>
        <li>You agree to provide accurate registration and clinical information</li>
        <li>RNDs agree to maintain valid professional credentials for the duration of platform use</li>
        <li>You agree not to misuse messaging, video, or resource-sharing features for purposes unrelated to nutrition care</li>
        <li>You agree not to attempt to access clinical records outside an established care relationship</li>
      </ul>

      <h2>6. Service Availability</h2>
      <p>NutriMatch requires a stable internet connection; no offline mode is available. Video conferencing, payment processing, and SMS notifications depend on third-party providers and are subject to their respective uptime and service terms.</p>

      <h2>7. Limitation of Liability</h2>
      <p>NutriMatch is provided as an academic capstone project. While built to professional standards, it is not formally registered as a Data Processing System with the National Privacy Commission. Institutions or individuals deploying NutriMatch for live clinical use assume responsibility for regulatory compliance appropriate to their context.</p>

      <h2>8. Changes to These Terms</h2>
      <p>We may update these Terms from time to time. Continued use of NutriMatch after changes take effect constitutes acceptance of the revised Terms.</p>

      <h2>9. Contact</h2>
      <p>Questions about these Terms can be directed to <strong>support@nutrimatch.ph</strong> or via our <NuxtLink to="/contact">Contact page</NuxtLink>.</p>
    </div>

    <SiteFooter />
  </div>
</template>

<style scoped>
* { box-sizing: border-box; }
div { font-family: 'Inter', sans-serif; }

.legal-shell { max-width: 780px; margin: 0 auto; padding: 56px 24px 80px; }
.eyebrow { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; color: #8a9a8a; margin: 0 0 10px; }
.legal-title { font-family: 'Playfair Display', serif; font-size: 2rem; color: #1a3a1a; margin: 0; }
.legal-meta { font-size: 0.85rem; color: #8a9a8a; margin: 10px 0 28px; }

h2 { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 32px 0 12px; }
p, li { font-size: 0.9rem; color: #4a5a4a; line-height: 1.75; }
strong { color: #1a3a1a; }
:deep(a) { color: #1e4a26; font-weight: 600; }
</style>
