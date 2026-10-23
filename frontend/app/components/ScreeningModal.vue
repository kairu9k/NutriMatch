<template>
  <!-- The client's screening on file, read-only, over the current page
       ("View Screening" on the dashboard and Profile Settings). It's taken
       once and then can't be changed — see PreConsultationScreening.vue. -->
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="emit('close')">
      <div class="scr-box" role="dialog" aria-modal="true" aria-label="Your pre-consultation screening">
        <button type="button" class="scr-x" aria-label="Close" @click="emit('close')"><X :size="18" /></button>
        <PreConsultationScreening embedded />
        <div class="scr-foot">
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
.scr-box { position: relative; background: #fff; border-radius: 16px; width: 100%; max-width: 820px; max-height: calc(100vh - 32px); overflow-y: auto; padding: 28px 30px 20px; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2); }
.scr-x { position: sticky; top: -14px; float: right; z-index: 3; margin: -14px -16px 0 8px; border: 0; background: #fff; color: #6a7a6a; cursor: pointer; padding: 6px; border-radius: 8px; display: flex; }
.scr-x:hover { background: #f1f3f1; color: #1a3a1a; }
.scr-foot { display: flex; justify-content: flex-end; position: sticky; bottom: -20px; z-index: 2; margin: 18px -30px -20px; padding: 14px 30px 16px; border-top: 1px solid #d9e3dc; background: #fff; }
@media (max-width: 560px) {
  .nm-modal-overlay { padding: 0; }
  .scr-box { max-width: none; max-height: 100vh; height: 100vh; height: 100dvh; border-radius: 0; padding: 20px 16px; }
  .scr-foot { margin: 18px -16px -20px; padding: 12px 16px 14px; }
  .scr-foot > * { flex: 1; }
}
</style>
