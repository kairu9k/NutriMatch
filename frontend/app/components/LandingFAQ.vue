<template>
  <section class="faq" id="faqs">
    <div class="faq-header">
      <div class="eyebrow">FAQ</div>
      <h2>Common questions</h2>
    </div>

    <div class="faq-list">
      <div class="faq-item" v-for="(item, i) in faqs" :key="i">
        <button class="faq-question" @click="toggle(i)">
          <span>{{ item.q }}</span>
          <span class="faq-icon">{{ openIndex === i ? '×' : '+' }}</span>
        </button>
        <div class="faq-answer" v-show="openIndex === i">
          {{ item.a }}
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from 'vue'

const openIndex = ref(null)
const toggle = (i) => { openIndex.value = openIndex.value === i ? null : i }

const faqs = [
  { q: 'Is NutriMatch free to use?', a: 'Creating an account is free. Each RND sets their own consultation fee, shown on their profile. You pay it once your RND confirms the booking, any time before the consultation starts.' },
  { q: 'How are RNDs verified on the platform?', a: 'All RNDs upload a photo of their PRC license during registration, which our admin team verifies against PRC records before their profile goes live.' },
  { q: 'Is my health data kept private?', a: 'Yes. NutriMatch follows the Data Privacy Act of 2012 (RA 10173). Only you and your RND see your health records, your data travels over an encrypted connection, and every time someone opens your records it is logged.' },
  { q: 'Which conditions does NutriMatch support?', a: 'NutriMatch supports diabetes, hypertension, renal disease, obesity, malnutrition, and other conditions requiring Medical Nutrition Therapy.' },
  { q: 'What consultation types are available?', a: 'A video call or an in-person visit at your RND\'s clinic, depending on what your RND offers.' },
  { q: 'How do I pay?', a: 'Through PayMongo with GCash, Maya, a card or QR Ph. Your consultation opens once it is paid.' },
  { q: 'What if a consultation is cancelled?', a: 'If you already paid, you get a full refund within 5 to 7 business days, back to the same wallet or card.' },
  { q: 'Can I see more than one RND?', a: 'You work with one RND at a time, so your care stays in one place. You can ask to end your care with them in Profile Settings, then book someone else.' },
]
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&family=Inter:wght@400;500;600&display=swap');

.faq {
  background: #ffffff;
  padding: 100px 200px;
  font-family: 'Inter', sans-serif;
}

.faq-header { text-align: center; margin-bottom: 48px; }

.eyebrow {
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.12em;
  color: #8aaa8a; margin-bottom: 12px;
}

.faq-header h2 {
  font-family: 'Playfair Display', serif;
  font-size: 2.4rem; font-weight: 700; font-style: italic; color: #1a3a1a;
}

.faq-list { display: flex; flex-direction: column; }

.faq-item { border-bottom: 1px solid #e8e8e0; }

.faq-question {
  width: 100%; display: flex; justify-content: space-between; align-items: center;
  padding: 20px 0; background: none; border: none; cursor: pointer;
  font-size: 0.95rem; font-weight: 500; color: #1a3a1a; text-align: left;
  font-family: 'Inter', sans-serif;
}

.faq-icon { color: #D4A017; font-size: 1.4rem; font-weight: 300; flex-shrink: 0; }

.faq-answer {
  padding: 0 0 20px; font-size: 0.88rem; color: #6a8a6a; line-height: 1.7;
}

@media (max-width: 900px) {
  .faq { padding: 60px 24px; }
}
</style>