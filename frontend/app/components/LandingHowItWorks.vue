<template>
  <section id="how-it-works" class="hiw">
    <div class="hiw-inner">
      <div class="hiw-header">
        <span class="eyebrow">
          <span class="eyebrow-line" aria-hidden="true"></span>
          HOW IT WORKS
          <span class="eyebrow-line" aria-hidden="true"></span>
        </span>
        <h2>Four steps to <em>steady progress</em></h2>

        <div class="hiw-switch" role="group" aria-label="Choose your role">
          <button
            type="button"
            :class="{ active: audience === 'client' }"
            :aria-pressed="audience === 'client'"
            @click="audience = 'client'"
          >For clients</button>
          <button
            type="button"
            :class="{ active: audience === 'rnd' }"
            :aria-pressed="audience === 'rnd'"
            @click="audience = 'rnd'"
          >For RNDs</button>
        </div>
      </div>

      <ol class="steps">
        <li v-for="(step, i) in steps[audience]" :key="audience + i" class="step">
          <span class="step-number">{{ String(i + 1).padStart(2, '0') }}</span>
          <span class="step-line" aria-hidden="true"></span>
          <h3>{{ step.title }}</h3>
          <p>{{ step.desc }}</p>
        </li>
      </ol>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

// Which set of steps is showing
const audience = ref('client')

const steps = {
  client: [
    { title: 'Create your account', desc: 'Sign up in minutes, answer a short health screening and give your digital informed consent.' },
    { title: 'Find your RND', desc: 'Browse verified RNDs by specialty and language, then book a video call or an in-person visit.' },
    { title: 'Pre-consultation screening', desc: 'Share your health history before your session so your RND arrives prepared.' },
    { title: 'Follow your plan', desc: 'Get a personal FNRI meal plan, log your meals and see your progress from your dashboard.' },
  ],
  rnd: [
    { title: 'Register and get verified', desc: 'Send your PRC license; our team checks it before you go live.' },
    { title: 'Receive matched clients', desc: 'Clients find you by specialty, language and consultation type.' },
    { title: 'Run the NCP digitally', desc: 'Assess, diagnose, intervene and monitor with automated calculations.' },
    { title: 'Track, remind and bill', desc: 'Share resources, set reminders and manage consultation fees.' },
  ],
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

.hiw {
  /* exactly the same shade as the navbar, hero and features; pinned to the
     screen (fixed) so they all line up */
  background:
    radial-gradient(circle at 76% 48%, rgba(239, 191, 4, 0.30), rgba(239, 191, 4, 0) 48%),
    radial-gradient(circle at 6% 10%, rgba(6, 60, 42, 0.16), rgba(6, 60, 42, 0) 42%),
    linear-gradient(135deg, #DFECE3 0%, #EAF2E8 40%, #FBEFC8 100%);
  background-attachment: fixed;
  font-family: 'DM Sans', Arial, sans-serif;
}
.hiw *, .hiw *::before, .hiw *::after { box-sizing: border-box; }

.hiw-inner {
  max-width: 1180px;
  margin: 0 auto;
  padding: 96px 24px;
  display: flex;
  flex-direction: column;
  gap: 44px;
}

/* Header */
.hiw-header {
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
.hiw-header h2 {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: clamp(28px, 3.4vw, 42px);
  line-height: 1.15;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: #1F2D27;
}
.hiw-header h2 em { font-style: italic; font-weight: 700; color: #063C2A; }

/* For clients / For RNDs switch */
.hiw-switch {
  position: static;
  width: auto;
  height: auto;
  display: inline-flex;
  align-items: center;
  margin-top: 8px;
  padding: 5px;
  gap: 4px;
  background: #FFFFFF;
  border: 1px solid #DCE5E0;
  border-radius: 999px;
}
.hiw-switch button {
  min-height: 44px;
  padding: 0 22px;
  border: none;
  border-radius: 999px;
  background: #FFFFFF;
  color: #063C2A;
  font-family: inherit;
  font-size: 15px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}
.hiw-switch button.active { background: #063C2A; color: #FFFFFF; }
.hiw-switch button:focus-visible { outline: 3px solid #EFBF04; outline-offset: 2px; }

/* Step cards */
.steps {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 24px;
}
.step {
  background: #FFFFFF;
  border: 1px solid #E3EBE5;
  border-radius: 16px;
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  /* soft shadow so the white cards stand out on the shaded background */
  box-shadow: 0 10px 24px -18px rgba(6, 60, 42, 0.35);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  animation: fadeUp 0.35s ease both;
}
.step:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 32px -22px rgba(6, 60, 42, 0.45);
  border-color: #C7D6CD;
}
.step-number {
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 44px;
  line-height: 1;
  font-weight: 700;
  font-style: italic;
  color: #063C2A;
}
.step-line {
  display: block;
  width: 32px;
  height: 3px;
  border-radius: 2px;
  background: #EFBF04;
}
.step h3 {
  margin: 0;
  font-size: 17px;
  line-height: 1.35;
  font-weight: 700;
  color: #063C2A;
}
.step p {
  margin: 0;
  font-size: 14px;
  line-height: 1.65;
  color: #4E5F57;
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}

/* Tablet: 2 per row */
@media (max-width: 960px) {
  .steps { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hiw-inner { padding: 72px 24px; }
}

/* Phone: 1 per row, full-width switch */
@media (max-width: 600px) {
  .steps { grid-template-columns: 1fr; }
  .hiw-inner { padding: 56px 20px; gap: 36px; }
  .hiw-switch { width: 100%; }
  .hiw-switch button { flex: 1; padding: 0 12px; }
}

@media (prefers-reduced-motion: reduce) {
  .step { animation: none; transition: none; }
  .step:hover { transform: none; }
}
</style>