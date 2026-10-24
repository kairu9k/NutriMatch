<template>
  <nav v-if="pages > 1" class="nm-pager" aria-label="Pages">
    <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="page <= 1" @click="emit('update:page', page - 1)">Previous</button>
    <span class="nm-pager-num">Page {{ page }} of {{ pages }}</span>
    <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="page >= pages" @click="emit('update:page', page + 1)">Next</button>
  </nav>
</template>

<script setup>
// Previous / Page X of Y / Next under a list paged with usePager().
defineProps({ page: { type: Number, required: true }, pages: { type: Number, required: true } })
const emit = defineEmits(['update:page'])
</script>
