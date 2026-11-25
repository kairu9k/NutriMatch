<template>
  <section id="faqs" class="nm-faq">
    <div class="nm-faq-inner">
      <div class="nm-faq-header">
        <span class="nm-faq-eyebrow">
          <span class="nm-faq-line" aria-hidden="true"></span>
          FAQ
          <span class="nm-faq-line" aria-hidden="true"></span>
        </span>
        <h2>Questions, <em>answered</em></h2>
      </div>

      <div class="nm-faq-list">
        <div
          v-for="(item, i) in faqs"
          :key="i"
          class="nm-faq-item"
          :class="{ open: openIndex === i }"
        >
          <button
            type="button"
            class="nm-faq-question"
            :aria-expanded="openIndex === i"
            :aria-controls="`faq-answer-${i}`"
            @click="toggle(i)"
          >
            <span>{{ item.q }}</span>
            <span class="nm-faq-icon" aria-hidden="true">+</span>
          </button>
          <div v-show="openIndex === i" :id="`faq-answer-${i}`" class="nm-faq-answer">
            {{ item.a }}
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

// First question starts open so visitors see how the list works
const openIndex = ref(0)
const toggle = (i) => { openIndex.value = openIndex.value === i ? null : i }

const faqs = [
  { q: 'Is NutriMatch free to use?', a: 'Creating an account is free. Each RND sets their own consultation fee, shown on their profile. You pay it once your RND confirms the booking, any time before the consultation starts.' },
  { q: 'How are RNDs verified on the platform?', a: 'All RNDs upload a photo of their PRC license and a selfie holding it during registration. Our admin team checks both against PRC records before their profile goes live.' },
  { q: 'Is my health data kept private?', a: 'Yes. NutriMatch follows the Data Privacy Act of 2012 (RA 10173). Only you and your RND see your health records, your data travels over an encrypted connection, and every time someone opens your records it is logged.' },
  { q: 'Which conditions does NutriMatch support?', a: 'NutriMatch supports diabetes, hypertension, renal disease, obesity, malnutrition, and other conditions requiring Medical Nutrition Therapy.' },
  { q: 'What consultation types are available?', a: 'A video call or an in-person visit at your RND\'s clinic, depending on what your RND offers.' },
  { q: 'How do I pay?', a: 'Through PayMongo with GCash, Maya, a card or QR Ph. Your consultation opens once it is paid.' },
  { q: 'What if a consultation is cancelled?', a: 'If you cancel a paid consultation at least 30 minutes before the start, or your RND cancels, you get a full refund within 5 to 7 business days, back to the same wallet or card. If you don\'t attend, there\'s no refund, but you can dispute it within 3 days.' },
  { q: 'Can I see more than one RND?', a: 'You work with one RND at a time, so your care stays in one place. You can ask to end your care with them in Profile Settings, then book someone else.' },
]
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,700&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

.nm-faq {
  /* same light shade as the navbar and other sections */
  background:
    radial-gradient(circle at 76% 48%, rgba(239, 191, 4, 0.30), rgba(239, 191, 4, 0) 48%),
    radial-gradient(circle at 6% 10%, rgba(6, 60, 42, 0.16), rgba(6, 60, 42, 0) 42%),
    linear-gradient(135deg, #DFECE3 0%, #EAF2E8 40%, #FBEFC8 100%);
  background-attachment: fixed;
  font-family: 'DM Sans', Arial, sans-serif;
}
.nm-faq *, .nm-faq *::before, .nm-faq *::after { box-sizing: border-box; }

.nm-faq-inner {
  max-width: 820px;
  margin: 0 auto;
  padding: 96px 24px 88px;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

/* Header */
.nm-faq-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 16px;
}
.nm-faq-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  font-weight: 600;
  color: #063C2A;
}
.nm-faq-line {
  display: inline-block;
  width: 32px;
  height: 3px;
  border-radius: 2px;
  background: #EFBF04;
}
.nm-faq-header h2 {
  margin: 0;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: clamp(28px, 3.4vw, 42px);
  line-height: 1.15;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: #1F2D27;
}
.nm-faq-header h2 em { font-style: italic; font-weight: 700; color: #063C2A; }

/* Accordion */
.nm-faq-list { display: flex; flex-direction: column; gap: 12px; }

.nm-faq-item {
  background: #FFFFFF;
  border: 1px solid #E3EBE5;
  border-radius: 12px;
  overflow: hidden;
  /* soft shadow so the white cards stand out on the shaded background */
  box-shadow: 0 10px 24px -18px rgba(6, 60, 42, 0.35);
  transition: border-color 0.2s;
}
.nm-faq-item.open { border-color: #063C2A; }

.nm-faq-question {
  width: 100%;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 22px;
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  font-size: 16px;
  font-weight: 600;
  color: #063C2A;
}
.nm-faq-question:focus-visible { outline: 3px solid #EFBF04; outline-offset: -3px; }

.nm-faq-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 400;
  line-height: 1;
  background: #EEF4F0;
  color: #063C2A;
  transition: transform 0.2s, background-color 0.2s;
}
.nm-faq-item.open .nm-faq-icon { background: #EFBF04; transform: rotate(45deg); }

.nm-faq-answer {
  padding: 0 22px 22px;
  font-size: 14px;
  line-height: 1.75;
  color: #4E5F57;
}

/* Tablet */
@media (max-width: 960px) {
  .nm-faq-inner { padding: 72px 24px; }
}

/* Phone */
@media (max-width: 600px) {
  .nm-faq-inner { padding: 56px 20px; gap: 32px; }
  .nm-faq-question { font-size: 15px; padding: 16px 18px; }
  .nm-faq-answer { padding: 0 18px 18px; }
}

@media (prefers-reduced-motion: reduce) {
  .nm-faq-item, .nm-faq-icon { transition: none; }
}
</style>