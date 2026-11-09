<template>
  <!-- A patient's meal photo shown on the page, never in a new tab: the photo is
       private and its link is signed (nutrition/photos.py), so it stays out of
       the browser's address bar and history. -->
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="emit('close')">
      <div class="nm-modal mp-modal" role="dialog" aria-modal="true" aria-labelledby="mp-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="emit('close')"><X :size="18" /></button>
        <h3 id="mp-title" class="nm-modal-title">{{ title }}</h3>
        <p v-if="failed" class="nm-note plain-note mp-failed">This photo couldn't be loaded. The link only lasts 10 minutes, so refresh the page and open it again.</p>
        <template v-else>
          <p v-if="!loaded" class="nm-muted mp-loading">Loading photo…</p>
          <img v-show="loaded" :src="url" :alt="`Photo the patient logged for ${title}`" class="mp-img" @load="loaded = true" @error="failed = true" />
        </template>
        <p v-if="note" class="mp-note">{{ note }}</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { X } from 'lucide-vue-next'

defineProps({
  url: { type: String, required: true },
  title: { type: String, required: true },
  note: { type: String, default: '' },
})
const emit = defineEmits(['close'])

const loaded = ref(false)
const failed = ref(false)

function onKey(e) { if (e.key === 'Escape') emit('close') }
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.mp-modal { max-width: 560px; }
.mp-img { display: block; width: 100%; max-height: 65vh; object-fit: contain; border-radius: 10px; background: #f7faf8; }
.mp-loading { padding: 48px 0; text-align: center; }
.mp-failed { margin: 0; }
.mp-note { margin: 12px 0 0; font-size: 0.86rem; line-height: 1.5; color: #4a5a4a; overflow-wrap: anywhere; }
</style>
