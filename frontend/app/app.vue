<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup>
const auth = useAuthStore()
auth.hydrate()
</script>