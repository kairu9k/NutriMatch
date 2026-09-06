<template>
  <ForgotPassword />
</template>

<script setup>
// This app uses a one-page OTP flow (request code -> enter code + new
// password) rather than a separate emailed-link route, so /reset-password
// just renders the same ForgotPassword component — kept as its own route
// since some places (and habit) link to "reset-password" by name.
</script>
