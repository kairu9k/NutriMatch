<template>
  <!-- The client's screening on file, read-only, over the current page
       ("View Screening" on the dashboard and Profile Settings). It's taken
       once and then can't be changed — see PreConsultationScreening.vue. -->
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="emit('close')">
      <div class="nm-modal scr-box" role="dialog" aria-modal="true" aria-labelledby="scr-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="emit('close')"><X :size="18" aria-hidden="true" /></button>
        <h2 id="scr-title" class="nm-modal-title">Your screening</h2>
        <PreConsultationScreening embedded />
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" @click="emit('close')">Close</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { X } from 'lucide-vue-next'

const emit = defineEmits(['close'])
function onKey(e) { if (e.key === 'Escape') emit('close') }
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.scr-box { max-width: 640px; }
/* the pop-up's header already says it */
.scr-box :deep(.screening-title) { display: none; }
@media (max-width: 640px) {
  .nm-modal-overlay { padding: 0; }
  .scr-box { max-width: none; max-height: none; height: 100vh; height: 100dvh; border-radius: 0; }
  .scr-box .nm-modal-actions > * { flex: 1; }
}
</style>
