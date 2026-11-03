<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
  <AppToaster />
</template>

<script setup>
const auth = useAuthStore()
auth.hydrate()
</script>