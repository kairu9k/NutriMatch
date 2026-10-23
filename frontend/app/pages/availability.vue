<template>
  <div></div>
</template>

<script setup>
// Weekly hours and time off live in Profile Settings → Availability now.
definePageMeta({ layout: 'dashboard' })
navigateTo({ path: '/profile-settings', query: { tab: 'availability' } }, { replace: true })
</script>
