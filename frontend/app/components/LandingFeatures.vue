<template>
  <section id="features" class="features">
    <div class="features-inner">
      <div class="features-header">
        <span class="eyebrow">
          <span class="eyebrow-line" aria-hidden="true"></span>
          FEATURES
          <span class="eyebrow-line" aria-hidden="true"></span>
        </span>
        <h2>Everything in <em>one place</em></h2>
        <p>Eight modules that replace paper charts, printed exchange lists, spreadsheets and scattered chats.</p>
      </div>

      <div class="features-grid">
        <div v-for="feature in features" :key="feature.title" class="feature-card">
          <svg
            class="feature-icon"
            width="30" height="30" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" stroke-width="1.5"
            stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"
          >
            <path :d="feature.icon" />
          </svg>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.desc }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
// The eight NutriMatch modules (icons are simple line drawings)
const features = [
  {
    title: 'RND-client matching',
    desc: 'Search by specialty, language and video or in-person consultation, with ratings and reviews.',
    icon: 'M9 4a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM2 21c0-4 3-6 7-6s7 2 7 6M16 11l2 2 4-4',
  },
  {
    title: 'Pre-consultation screening',
    desc: 'Clients complete a screening form ahead of time, summarized for the RND.',
    icon: 'M9 3h6v4H9zM6 5h12v16H6zM9 12h6M9 16h4',
  },
  {
    title: 'Digital Nutrition Care Process',
    desc: 'Assessment, diagnosis, intervention and monitoring in one record.',
    icon: 'M4 4h16v16H4zM4 9h16M9 9v11M12 13h5M12 16h4',
  },
  {
    title: 'Disease-specific meal plans',
    desc: 'Templates built on FNRI exchange lists and USDA data, for diabetes, hypertension, kidney disease and weight management.',
    icon: 'M3 12h18a9 9 0 0 1-18 0zM8 8c0-2 2-2 2-4M13 8c0-2 2-2 2-4',
  },
  {
    title: 'Progress monitoring',
    desc: 'Weight, BMI, blood pressure, glucose, lipids and adherence over time.',
    icon: 'M4 20h16M4 14l5-4 4 3 7-7M16 6h4v4',
  },
  {
    title: 'Resource repository',
    desc: 'Nutrition and physical activity materials shared by your RND.',
    icon: 'M4 5h7v15H4zM13 5h7v15h-7zM6.5 9h2M15.5 9h2',
  },
  {
    title: 'Automated reminders',
    desc: 'Notifications for appointments, payments, meal logging and tasks.',
    icon: 'M6 16v-5a6 6 0 0 1 12 0v5l2 2H4zM10 21h4',
  },
  {
    title: 'Billing & payments',
    desc: 'Consultation fees for clients and RNDs, with admin oversight.',
    icon: 'M3 6h18v12H3zM3 10h18M7 15h4',
  },
]
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

.features {
  /* exactly the same shade as the navbar and hero; pinned to the screen
     (fixed) so all three line up */
  background:
    radial-gradient(circle at 76% 48%, rgba(239, 191, 4, 0.30), rgba(239, 191, 4, 0) 48%),
    radial-gradient(circle at 6% 10%, rgba(6, 60, 42, 0.16), rgba(6, 60, 42, 0) 42%),
    linear-gradient(135deg, #DFECE3 0%, #EAF2E8 40%, #FBEFC8 100%);
  background-attachment: fixed;
  font-family: 'DM Sans', Arial, sans-serif;
}
.features *, .features *::before, .features *::after { box-sizing: border-box; }

.features-inner {
  max-width: 1180px;
  margin: 0 auto;
  padding: 96px 24px;
  display: flex;
  flex-direction: column;
  gap: 48px;
}

/* Header */
.features-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 16px;
}
.eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 2px;
  color: #063C2A;
}
.eyebrow-line {
  display: inline-block;
  width: 32px;
  height: 3px;
  border-radius: 2px;
  background: #EFBF04;
}
.features-header h2 {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: clamp(28px, 3.4vw, 42px);
  line-height: 1.15;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: #1F2D27;
}
.features-header h2 em { font-style: italic; font-weight: 700; color: #063C2A; }
.features-header p {
  margin: 0;
  max-width: 560px;
  font-size: 16px;
  line-height: 1.7;
  color: #4E5F57;
}

/* Cards */
.features-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 24px;
}
.feature-card {
  background: #FFFFFF;
  border: 1px solid #E3EBE5;
  border-radius: 16px;
  padding: 30px 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  /* soft shadow so the white cards stand out on the shaded background */
  box-shadow: 0 10px 24px -18px rgba(6, 60, 42, 0.35);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.feature-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 32px -22px rgba(6, 60, 42, 0.45);
  border-color: #C7D6CD;
}
.feature-icon { color: #063C2A; flex-shrink: 0; }
.feature-card h3 {
  margin: 4px 0 0;
  font-size: 17px;
  line-height: 1.35;
  font-weight: 700;
  color: #063C2A;
}
.feature-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: #4E5F57;
}

/* Tablet: 2 per row */
@media (max-width: 960px) {
  .features-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .features-inner { padding: 72px 24px; }
}

/* Phone: 1 per row */
@media (max-width: 600px) {
  .features-grid { grid-template-columns: 1fr; }
  .features-inner { padding: 56px 20px; gap: 36px; }
}

@media (prefers-reduced-motion: reduce) {
  .feature-card { transition: none; }
  .feature-card:hover { transform: none; }
}
</style>