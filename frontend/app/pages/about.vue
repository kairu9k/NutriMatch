<template>
  <div>
    <MarketingNavbar />

    <section class="page-hero">
      <p class="eyebrow">ABOUT NUTRIMATCH</p>
      <h1 class="hero-title">Modernizing Medical<br>Nutrition Therapy in the Philippines</h1>
      <p class="hero-sub">A capstone project by BSIT Group 12, STI College Davao — built to close the gap between Filipino RNDs and the patients who need structured nutrition care.</p>
    </section>

    <section class="page-content">
      <div class="mission-grid">
        <div class="mission-card">
          <div class="mission-icon"><Target :size="22" /></div>
          <h3 class="mission-title">Our Mission</h3>
          <p class="mission-text">To give every licensed RND in the Philippines a digital practice — one that replaces paper charting with structured, auditable, FNRI-grounded clinical workflows, so Medical Nutrition Therapy can reach more Filipinos managing diabetes, hypertension, renal disease, and obesity.</p>
        </div>
        <div class="mission-card">
          <div class="mission-icon"><HeartPulse :size="22" /></div>
          <h3 class="mission-title">Why It Matters</h3>
          <p class="mission-text">Noncommunicable diseases account for roughly 3 in 4 deaths worldwide, and the Philippines faces a dual burden of malnutrition — persistent stunting alongside rising obesity. NutriMatch operationalizes the WHO-recommended Nutrition Care Process to make evidence-based dietary care more accessible.</p>
        </div>
      </div>

      <div class="section-header">
        <p class="eyebrow">THE TEAM</p>
        <h2 class="section-title">BSIT Group 12</h2>
      </div>
      <div class="team-grid">
        <div v-for="member in team" :key="member.name" class="team-card">
          <div class="team-avatar">{{ member.initials }}</div>
          <div class="team-name">{{ member.name }}</div>
          <div class="team-role">{{ member.role }}</div>
        </div>
      </div>

      <div class="adviser-card">
        <GraduationCap :size="26" />
        <p>Developed under the guidance of Capstone Project Adviser <strong>Elvi Lito Ubas</strong>, STI College Davao, in partial fulfillment of the requirements for the degree of Bachelor of Science in Information Technology.</p>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>

<script setup>
import { Target, HeartPulse, GraduationCap } from 'lucide-vue-next'

const team = [
  { initials: 'KC', name: 'King Chiu', role: 'Backend Developer' },
  { initials: 'IA', name: 'Ivy Hope Alba', role: 'Project Member' },
  { initials: 'JB', name: 'Julia Niel Bulalaque', role: 'Project Member' },
  { initials: 'KL', name: 'Kent Leabres', role: 'Project Member' },
]
</script>

<style scoped>
* { box-sizing: border-box; }
div { font-family: 'Inter', sans-serif; }

.page-hero {
  background: #14301a; padding: 72px 48px; text-align: center;
}
.eyebrow { font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; color: #D4A017; margin: 0 0 12px; }
.hero-title {
  font-family: 'Playfair Display', serif; font-style: italic; color: #fff;
  font-size: 2.4rem; line-height: 1.3; margin: 0;
}
.hero-sub { color: #c9d9c9; max-width: 600px; margin: 16px auto 0; font-size: 0.95rem; }

.page-content { max-width: 1100px; margin: 0 auto; padding: 56px 24px; }

.mission-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 64px; }
@media (max-width: 800px) { .mission-grid { grid-template-columns: 1fr; } }
.mission-card { background: #fff; border-radius: 14px; padding: 32px; border: 1px solid #eceeec; }
.mission-icon {
  width: 44px; height: 44px; border-radius: 10px; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin-bottom: 16px;
}
.mission-title { font-family: 'Playfair Display', serif; font-size: 1.25rem; color: #1a3a1a; margin: 0 0 10px; }
.mission-text { font-size: 0.9rem; color: #6a7a6a; line-height: 1.65; margin: 0; }

.section-header { text-align: center; margin-bottom: 32px; }
.section-header .eyebrow { justify-content: center; }
.section-title { font-family: 'Playfair Display', serif; font-size: 1.8rem; color: #1a3a1a; margin: 0; }

.team-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 56px; }
@media (max-width: 700px) { .team-grid { grid-template-columns: 1fr 1fr; } }
.team-card { background: #fff; border-radius: 14px; padding: 28px 18px; text-align: center; border: 1px solid #eceeec; }
.team-avatar {
  width: 68px; height: 68px; border-radius: 50%; background: #1e4a26; color: #fff;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.1rem;
  margin: 0 auto 14px;
}
.team-name { font-weight: 700; font-size: 0.9rem; color: #1a3a1a; }
.team-role { font-size: 0.76rem; color: #8a9a8a; margin-top: 3px; }

.adviser-card {
  background: #eef3ec; border-radius: 14px; padding: 28px 32px; text-align: center;
  color: #1e4a26; display: flex; flex-direction: column; align-items: center; gap: 14px;
}
.adviser-card p { font-size: 0.9rem; color: #4a5a4a; margin: 0; max-width: 640px; line-height: 1.6; }
.adviser-card strong { color: #1a3a1a; }
</style>
