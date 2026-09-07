<template>
  <ClientReviews v-if="auth.user?.role === 'client'" />
  <Reviews v-else />
</template>

<script setup>
definePageMeta({ layout: 'dashboard', title: 'Reviews' })

const auth = useAuthStore()
</script>
