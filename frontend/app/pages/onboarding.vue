<template>
  <RndOnboarding v-if="isRnd" />
  <ClientOnboarding v-else />
</template>

<script setup>
import { useAuthStore } from '~/stores/auth'

// Onboarding has its own minimal layout (no sidebar): the rest of the app opens
// once it's finished (middleware/auth.global.ts). RNDs set up their profile,
// fee, hours and payout after approval; clients do their health screening.
definePageMeta({ layout: false, title: 'Set up your account' })
const isRnd = useAuthStore().user?.role === 'rnd'
</script>
