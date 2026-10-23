<template>
  <!-- Profile Settings → Notifications (client and RND): the chime for new
       notifications and messages, saved on this device only. -->
  <div class="snd">
    <div class="snd-text">
      <p class="snd-label">Play a sound for new notifications and messages</p>
      <p class="snd-detail">A short chime while NutriMatch is open. Saved on this device only, so you can mute a shared computer and keep it on your phone.</p>
      <button type="button" class="snd-test" @click="test"><Volume2 :size="14" /> Play test sound</button>
    </div>
    <label class="snd-toggle">
      <input type="checkbox" :checked="enabled" aria-label="Play a sound for new notifications and messages" @change="setEnabled($event.target.checked)" />
      <span class="snd-track"><span class="snd-thumb" /></span>
    </label>
  </div>
</template>

<script setup>
import { Volume2 } from 'lucide-vue-next'

const { enabled, test, setEnabled } = useNotificationSound()
</script>

<style scoped>
.snd { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; padding: 14px 0; border-bottom: 1px solid #f0f2f0; }
.snd-text { min-width: 0; }
.snd-label { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.snd-detail { font-size: 0.8rem; color: #7a8a7a; margin: 3px 0 0; line-height: 1.5; max-width: 60ch; }
.snd-test { display: inline-flex; align-items: center; gap: 6px; margin-top: 8px; background: none; border: none; padding: 0; font-family: inherit; font-size: 0.82rem; font-weight: 600; color: #1f6f46; cursor: pointer; }
.snd-test:hover { text-decoration: underline; }
.snd-test:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; border-radius: 4px; }
.snd-toggle { position: relative; flex-shrink: 0; width: 42px; height: 24px; cursor: pointer; }
.snd-toggle input { position: absolute; opacity: 0; width: 100%; height: 100%; margin: 0; cursor: pointer; }
.snd-track { position: absolute; inset: 0; border-radius: 999px; background: #d5dad5; transition: background 0.2s; }
.snd-thumb { position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: #fff; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2); transition: transform 0.2s; }
.snd-toggle input:checked + .snd-track { background: #1f8f5c; }
.snd-toggle input:checked + .snd-track .snd-thumb { transform: translateX(18px); }
.snd-toggle input:focus-visible + .snd-track { outline: 2px solid #1f8f5c; outline-offset: 2px; }
</style>
