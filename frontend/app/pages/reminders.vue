<template>
  <div></div>
</template>

<script setup>
// Reminders are automatic now; their settings live in Profile Settings.
definePageMeta({ layout: 'dashboard' })
navigateTo({ path: '/profile-settings', query: { tab: 'notifications' } }, { replace: true })
</script>
