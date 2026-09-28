<template>
  <!-- Auth state lives in localStorage, so the role is unknown during SSR —
       rendering the branch server-side would hydrate the wrong component. -->
  <ClientOnly>
    <ClientProfileSettings v-if="auth.user?.role === 'client'" />
    <ProfileSettings v-else />
  </ClientOnly>
</template>

<script setup>
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'dashboard', title: 'Profile Settings' })

const auth = useAuthStore()
</script>
