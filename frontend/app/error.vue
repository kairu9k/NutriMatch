<template>
  <div class="error-shell">
    <div class="error-circle"></div>
    <div class="error-content">
      <div class="error-code">{{ error?.statusCode || 500 }}</div>
      <h1 class="error-title">{{ isNotFound ? 'This Page Took a Wrong Turn' : 'Something Went Wrong on Our End' }}</h1>
      <p class="error-desc">
        {{ isNotFound
          ? "The page you're looking for doesn't exist or may have been moved. Let's get you back to a meal plan that actually works."
          : "We're already looking into it. Your data is safe — please try again in a few minutes." }}
      </p>
      <div class="error-actions">
        <button class="btn-gold" @click="handleClearError">Back to Home</button>
        <NuxtLink to="/contact" class="btn-outline">Contact Support</NuxtLink>
      </div>
      <p v-if="!isNotFound" class="error-ref">Error reference: {{ errorRef }}</p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  error: Object,
})

const isNotFound = computed(() => props.error?.statusCode === 404)

const errorRef = computed(() => {
  const id = Math.random().toString(16).slice(2, 8).toUpperCase()
  return `NM-${props.error?.statusCode || 500}-${id}`
})

function handleClearError() {
  clearError({ redirect: '/' })
}
</script>

<style scoped>
* { box-sizing: border-box; }

.error-shell {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: #14301a; position: relative; overflow: hidden; padding: 24px;
  font-family: 'Inter', sans-serif;
}
.error-circle {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%);
  width: 620px; height: 620px; border-radius: 50%; background: rgba(255,255,255,0.03);
}
.error-content { position: relative; z-index: 1; text-align: center; max-width: 480px; }
.error-code {
  font-family: 'Playfair Display', serif; font-style: italic; font-weight: 700;
  font-size: 6rem; color: #D4A017; line-height: 1;
}
.error-title { font-family: 'Playfair Display', serif; color: #fff; font-size: 1.6rem; margin: 16px 0 0; }
.error-desc { color: #c9d9c9; margin: 16px 0 28px; font-size: 0.92rem; line-height: 1.6; }
.error-actions { display: flex; gap: 14px; justify-content: center; flex-wrap: wrap; }
.btn-gold {
  background: #D4A017; border: none; color: #1a3a1a; border-radius: 24px;
  padding: 12px 26px; font-weight: 700; font-size: 0.88rem; cursor: pointer;
}
.btn-outline {
  background: transparent; border: 1.5px solid rgba(255,255,255,0.6); color: #fff;
  border-radius: 24px; padding: 12px 26px; font-weight: 600; font-size: 0.88rem; text-decoration: none;
}
.error-ref { margin-top: 24px; font-size: 0.72rem; color: #7a9a7a; }
</style>
