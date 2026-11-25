<template>
  <!-- The client's screening on file, read-only, over the current page
       ("View Screening" on the dashboard and Profile Settings). It's taken
       once and then can't be changed — see PreConsultationScreening.vue. -->
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="emit('close')">
      <div class="nm-modal scr-box" role="dialog" aria-modal="true" aria-labelledby="scr-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="emit('close')"><X :size="18" aria-hidden="true" /></button>
        <header class="scr-head">
          <span class="scr-ico" aria-hidden="true"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6M9 18h4" /></svg></span>
          <div>
            <p class="scr-k">Pre-consultation</p>
            <h2 id="scr-title" class="nm-modal-title">Your screening</h2>
          </div>
        </header>
        <div class="scr-body">
          <PreConsultationScreening embedded />
        </div>
        <div class="nm-modal-actions scr-foot">
          <button type="button" class="nm-btn-soft" @click="emit('close')">Close</button>
          <NuxtLink to="/progress-tracker" class="scr-go" @click="emit('close')">
            <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h4l3-8 4 16 3-8h4" /></svg>
            Open Progress Tracker
            <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
          </NuxtLink>
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
.scr-box { position: relative; max-width: 640px; padding: 0 !important; display: flex; flex-direction: column; border-radius: 24px; overflow: hidden; }
/* the pop-up's header already says it */
.scr-box :deep(.screening-title) { display: none; }
.scr-box .nm-modal-x { position: absolute !important; top: 18px !important; right: 18px !important; left: auto !important; margin: 0 !important; z-index: 2; width: 38px; height: 38px; display: inline-flex; align-items: center; justify-content: center; border: none; border-radius: 50%; background: #F1F5F2; color: #22362C; }
.scr-head { display: flex; align-items: center; gap: 14px; padding: 24px 64px 18px 26px; background: linear-gradient(180deg, #F1F7F3, #FFFFFF); }
.scr-ico { width: 50px; height: 50px; flex-shrink: 0; border-radius: 50%; background: #004D3A; color: #EFBF04; display: inline-flex; align-items: center; justify-content: center; }
.scr-k { margin: 0; font-size: 11.5px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; color: #9A7300; }
.scr-head .nm-modal-title { margin: 2px 0 0; font-family: 'Playfair Display', Georgia, serif; font-size: 24px; color: #0E3A2C; }
.scr-body { padding: 4px 26px 22px; overflow: auto; }
.scr-body :deep(.panel) { padding: 0; border: none; }
.scr-foot { display: flex; justify-content: flex-end; gap: 10px; margin: 0; padding: 16px 26px; border-top: 1px solid #EEF2EF; background: #FAFCFB; }
.scr-foot .nm-btn-soft { height: 44px; padding: 0 18px; border-radius: 12px; font-weight: 800; }
.scr-go { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 44px; padding: 0 18px; border-radius: 12px; background: #004D3A; color: #FFFFFF; font-size: 14px; font-weight: 800; text-decoration: none; }
.scr-go svg { color: #EFBF04; }
.scr-go:hover { background: #00684E; }
.scr-go:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
@media (max-width: 640px) {
  .nm-modal-overlay { padding: 0; }
  .scr-box { max-width: none; max-height: none; height: 100vh; height: 100dvh; border-radius: 0; }
  .scr-head { padding: 20px 56px 16px 18px; }
  .scr-body { flex: 1; padding: 4px 18px 18px; }
  .scr-foot { flex-direction: column-reverse; padding: 12px 18px; }
  .scr-foot > * { flex: none; width: 100%; }
}
</style>