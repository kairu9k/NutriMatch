<template>
  <div></div>
</template>

<script setup>
// Client Management became the Users page (Clients / RNDs / Admins).
definePageMeta({ layout: 'dashboard', admin: true })
navigateTo('/users', { replace: true })
</script>
