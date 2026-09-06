<template>
  <div class="screening-page">
    <div class="page-header">
      <p class="eyebrow">BEFORE YOUR FIRST APPOINTMENT</p>
      <h1 class="page-title">Pre-Consultation Screening</h1>
      <p class="page-sub">A few quick biometrics so your RND can prepare for your session.</p>
    </div>

    <div v-if="!result" class="surface">
      <h3 class="surface-title">Biometrics</h3>
      <div class="field-row">
        <div class="field">
          <label class="field-label">Height (cm)</label>
          <input v-model.number="form.height_cm" type="number" step="0.1" class="field-input" placeholder="e.g. 165" />
        </div>
        <div class="field">
          <label class="field-label">Weight (kg)</label>
          <input v-model.number="form.weight_kg" type="number" step="0.1" class="field-input" placeholder="e.g. 60" />
        </div>
      </div>

      <label class="field-label">Activity Level</label>
      <select v-model="form.activity_level" class="field-input">
        <option value="sedentary">Sedentary (little to no exercise)</option>
        <option value="lightly_active">Lightly active (1–3 days/week)</option>
        <option value="moderately_active">Moderately active (3–5 days/week)</option>
        <option value="very_active">Very active (6–7 days/week)</option>
        <option value="extra_active">Extra active (physical job or 2x/day training)</option>
      </select>

      <label class="field-label">Current Symptoms <span class="optional">(optional)</span></label>
      <textarea v-model="form.symptoms" class="field-input" rows="3" placeholder="e.g. frequent thirst, fatigue, swelling in ankles..."></textarea>

      <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>

      <button class="submit-btn" type="button" :disabled="!canSubmit || isSubmitting" @click="submitScreening">
        {{ isSubmitting ? 'Submitting…' : 'Submit Screening' }}
      </button>
    </div>

    <div v-else class="surface">
      <div class="result-header"><Cpu :size="18" /><h3 class="surface-title">Computed Clinical Values</h3></div>
      <div class="result-grid">
        <div class="result-box">
          <div class="result-num">{{ result.bmi }}</div>
          <div class="result-label">BMI</div>
          <span class="badge-pill" :class="bmiBadgeClass">{{ result.bmi_category }}</span>
        </div>
        <div class="result-box">
          <div class="result-num">{{ result.bmr_kcal ? Math.round(result.bmr_kcal) : '—' }}</div>
          <div class="result-label">BMR (kcal)</div>
        </div>
        <div class="result-box">
          <div class="result-num">{{ result.tdee_kcal ? Math.round(result.tdee_kcal) : '—' }}</div>
          <div class="result-label">TDEE (kcal)</div>
        </div>
      </div>
      <p v-if="!result.bmr_kcal" class="bmr-note">
        BMR/TDEE need your date of birth and sex on file — add these in
        <NuxtLink to="/profile-settings">Profile Settings</NuxtLink> to see them next time.
      </p>
      <div class="success-note">Screening submitted. Your RND will see this before your appointment.</div>
      <NuxtLink to="/appointments" class="submit-btn continue-btn">Continue to Appointments</NuxtLink>
    </div>
  </div>
</template>

<script setup>
import { Cpu } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Pre-Consultation Screening' })

const { post } = useApi()

const form = reactive({
  height_cm: null,
  weight_kg: null,
  activity_level: 'sedentary',
  symptoms: '',
})

const isSubmitting = ref(false)
const errorMessage = ref('')
const result = ref(null)

const canSubmit = computed(() => form.height_cm > 0 && form.weight_kg > 0)

const bmiBadgeClass = computed(() => {
  const cat = (result.value?.bmi_category || '').toLowerCase()
  if (cat.includes('normal')) return 'badge-success'
  if (cat.includes('underweight')) return 'badge-info'
  return 'badge-warning'
})

async function submitScreening() {
  isSubmitting.value = true
  errorMessage.value = ''
  try {
    result.value = await post('/client/screening/', {
      height_cm: form.height_cm,
      weight_kg: form.weight_kg,
      activity_level: form.activity_level,
      symptoms: form.symptoms || undefined,
    })
  } catch (error) {
    errorMessage.value = error?.data?.detail || 'Could not submit your screening. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
* { box-sizing: border-box; }

.screening-page { font-family: 'Inter', sans-serif; max-width: 640px; }

.page-header { margin-bottom: 20px; }
.eyebrow { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; color: #8a9a8a; margin: 0 0 8px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 22px; }
.surface-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0; }

.field-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 4px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { display: block; font-size: 0.85rem; font-weight: 600; color: #1a3a1a; margin: 16px 0 8px; }
.field-label:first-child { margin-top: 0; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px;
  font-size: 0.88rem; color: #2a2a2a; font-family: inherit; background: #fff;
}
.field-input:focus { outline: none; border-color: #D4A017; }
textarea.field-input { resize: vertical; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 16px 0 0;
}

.submit-btn {
  display: block; width: 100%; text-align: center; text-decoration: none;
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 14px; font-weight: 700; font-size: 0.95rem; cursor: pointer; margin-top: 20px;
}
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.result-header { display: flex; align-items: center; gap: 8px; color: #1e4a26; margin-bottom: 18px; }
.result-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.result-box { background: #f6f7f2; border-radius: 10px; padding: 16px; text-align: center; }
.result-num { font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: 700; color: #1a3a1a; }
.result-label { font-size: 0.74rem; color: #8a9a8a; margin-top: 4px; }
.badge-pill {
  display: inline-block; font-size: 0.68rem; font-weight: 700; padding: 2px 9px;
  border-radius: 12px; margin-top: 8px;
}
.badge-success { background: #e6efe0; color: #3a6b3a; }
.badge-warning { background: #faead0; color: #b8860b; }
.badge-info { background: #e3edf7; color: #2f6fa8; }

.bmr-note { font-size: 0.8rem; color: #8a9a8a; margin: 14px 0 0; }
.bmr-note :deep(a) { color: #3a6b3a; font-weight: 600; }

.success-note {
  background: #e6efe0; border: 1px solid #b8d5b8; color: #3a6b3a;
  border-radius: 8px; padding: 12px 14px; font-size: 0.85rem; margin-top: 20px;
}
.continue-btn { margin-top: 14px; }
</style>
