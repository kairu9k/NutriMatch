<template>
  <ClientReviews v-if="auth.hydrated && auth.user?.role === 'client'" />
  <Reviews v-else-if="auth.hydrated" />
</template>

<script setup>
definePageMeta({ layout: 'dashboard', title: 'Reviews' })

// Gated on auth.hydrated, same reasoning as layouts/dashboard.vue's sidebar
// fix: auth.user is null during SSR (JWT lives in localStorage), so an
// unguarded role check here always renders <Reviews /> (the RND component)
// server-side regardless of who's actually logged in — a client's first
// paint would show "Patient Reviews" and fire the RND-only /rnd/reviews/
// endpoint (403) before self-correcting on hydration.
const auth = useAuthStore()
</script>
