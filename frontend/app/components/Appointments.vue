<template>
  <!-- /appointments: RNDs get their work board, clients their own bookings. -->
  <RndAppointments v-if="isRnd" />
  <ClientAppointments v-else />
</template>

<script setup>
const auth = useAuthStore()
const isRnd = computed(() => auth.user?.role === 'rnd')
</script>
