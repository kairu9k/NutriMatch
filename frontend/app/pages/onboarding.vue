<template>
  <ClientOnboarding />
</template>

<script setup>
// Client onboarding has its own minimal layout (no sidebar) — the rest of the
// app opens once it's finished (middleware/auth.global.ts).
definePageMeta({ layout: false, title: 'Set up your account' })
</script>
