<template>
  <div></div>
</template>

<script setup>
// The old booking page. Clients book from an RND's profile (Find an RND) now.
import { useAuthStore } from '~/stores/auth'

definePageMeta({ layout: 'dashboard' })
const auth = useAuthStore()
navigateTo(auth.user?.role === 'client' ? '/find-rnd' : auth.user?.role === 'admin' ? '/admin-dashboard' : '/rnd-dashboard', { replace: true })
</script>
