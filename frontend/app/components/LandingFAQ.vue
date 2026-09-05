<template>
  <section class="faq" id="faqs">
    <div class="faq-header">
      <div class="eyebrow">FAQ</div>
      <h2>Common Questions</h2>
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
  { q: 'Is NutriMatch free to use?', a: 'Yes, creating a patient account is completely free. RNDs may have consultation fees set independently on their profiles.' },
  { q: 'How are RNDs verified on the platform?', a: 'All RNDs submit their PRC license number and credentials during registration, which are verified against PRC records before their profile goes live.' },
  { q: 'Is my health data kept private?', a: 'Absolutely. NutriMatch is fully RA 10173 (Data Privacy Act) compliant. Your health data is encrypted and never shared without your consent.' },
  { q: 'Which conditions does NutriMatch support?', a: 'NutriMatch supports diabetes, hypertension, renal disease, obesity, malnutrition, and other conditions requiring Medical Nutrition Therapy.' },
  { q: 'What consultation types are available?', a: 'You can choose from video call, chat-based, or in-person consultations depending on your RND\'s availability and your preference.' },
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