<template>
  <!-- A lab result file shown on the page (client Lab Results, the RND's Lab
       results tab and the consultation room). The file is private, so it's
       fetched through the API as a blob (it can take a few seconds) and shown
       in a pop-up: a PDF in the browser's viewer, a photo as an image. -->
  <Teleport to="body">
    <div class="nm-modal-overlay lf-overlay" @click.self="emit('close')">
      <div class="lf" role="dialog" aria-modal="true" aria-labelledby="lf-title">
        <header class="lf-head">
          <div class="lf-head-text">
            <h3 id="lf-title" class="lf-title">{{ title }}</h3>
            <p v-if="sub" class="lf-sub">{{ sub }}</p>
          </div>
          <button type="button" class="lf-x" aria-label="Close" @click="emit('close')"><X :size="18" /></button>
        </header>

        <div class="lf-body">
          <div v-if="state === 'loading'" class="lf-msg" role="status">
            <Loader2 :size="22" class="lf-spin" aria-hidden="true" />
            <p>Opening your lab result. This can take a few seconds.</p>
          </div>
          <div v-else-if="state === 'error'" class="lf-msg" role="alert">
            <p>This file could not be opened. Close this and try again, or upload it again if the problem stays.</p>
          </div>
          <img v-else-if="isImage" :src="url" :alt="title" class="lf-img" />
          <iframe v-else :src="url" :title="title" class="lf-frame" />
        </div>

        <!-- RND: decline needs a reason the patient will see -->
        <div v-if="declining" class="lf-decline">
          <label for="lf-reason" class="lf-label">Why are you sending it back?</label>
          <textarea id="lf-reason" v-model="reason" data-allow-emoji rows="2" maxlength="500" class="lf-input"
                    placeholder="e.g. The photo is too blurry to read. Please upload a clearer one." />
          <p v-if="reviewError" class="lf-error" role="alert">{{ reviewError }}</p>
        </div>
        <p v-else-if="reviewError" class="lf-error lf-error-row" role="alert">{{ reviewError }}</p>

        <footer class="lf-foot">
          <template v-if="canReview && declining">
            <button type="button" class="nm-btn-soft" :disabled="saving" @click="declining = false">Back</button>
            <button type="button" class="nm-btn-danger solid" :disabled="saving || reason.trim().length < 10" @click="review('decline')">{{ saving ? 'Sending…' : 'Decline and ask again' }}</button>
          </template>
          <template v-else>
            <!-- reviewing: the header's × closes, so no second Close button -->
            <button v-if="!canReview" type="button" class="nm-btn-soft" @click="emit('close')">Close</button>
            <a v-if="state === 'ready'" :href="url" :download="fileName || 'lab-result'" class="nm-btn-soft"><Download :size="14" aria-hidden="true" /> Download</a>
            <template v-if="canReview">
              <button type="button" class="nm-btn-danger solid" :disabled="saving || state !== 'ready'" @click="declining = true">Decline</button>
              <button type="button" class="nm-btn-dark" :disabled="saving || state !== 'ready'" @click="review('accept')">{{ saving ? 'Saving…' : 'Accept' }}</button>
            </template>
          </template>
        </footer>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { Download, Loader2, X } from 'lucide-vue-next'

const props = defineProps({
  path: { type: String, required: true }, // e.g. /client/lab-results/4/file/
  title: { type: String, default: 'Lab result' },
  sub: { type: String, default: '' },
  fileName: { type: String, default: '' },
  // RND only: POST here to accept or decline (null = view only)
  reviewPath: { type: String, default: '' },
})
// `opened` once the file loaded; `reviewed` with the updated result after Accept / Decline
const emit = defineEmits(['close', 'opened', 'reviewed'])
const { get, post } = useApi()

const canReview = computed(() => Boolean(props.reviewPath))
const declining = ref(false)
const reason = ref('')
const saving = ref(false)
const reviewError = ref('')
async function review(action) {
  saving.value = true
  reviewError.value = ''
  try {
    const res = await post(props.reviewPath, action === 'decline' ? { action, reason: reason.value.trim() } : { action })
    emit('reviewed', res)
    emit('close')
  } catch (e) {
    reviewError.value = e?.data?.reason?.[0] || e?.data?.reason || e?.data?.detail || 'Could not save. Please try again.'
  } finally {
    saving.value = false
  }
}

const state = ref('loading')
const url = ref('')
const isImage = ref(false)

onMounted(async () => {
  try {
    const blob = await get(props.path, { responseType: 'blob' })
    isImage.value = (blob.type || '').startsWith('image/')
    url.value = URL.createObjectURL(blob)
    state.value = 'ready'
    emit('opened')
  } catch {
    state.value = 'error'
  }
})
function onKey(e) { if (e.key === 'Escape') emit('close') }
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  if (url.value) URL.revokeObjectURL(url.value)
})
</script>

<style scoped>
.lf-overlay { z-index: 400; }
.lf {
  background: #fff; border-radius: 16px; width: 100%; max-width: 900px; height: min(88vh, 900px);
  display: flex; flex-direction: column; overflow: hidden; font-family: 'Inter', sans-serif; color: #1a3a1a;
  box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
}
.lf-head { display: flex; align-items: flex-start; gap: 12px; padding: 16px 20px; border-bottom: 1px solid #d9e3dc; }
.lf-head-text { flex: 1; min-width: 0; }
.lf-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; margin: 0; overflow-wrap: anywhere; }
.lf-sub { font-size: 0.82rem; color: #6a7a6a; margin: 3px 0 0; overflow-wrap: anywhere; }
.lf-x { border: none; background: none; color: #6a7a6a; cursor: pointer; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.lf-x:hover { background: #f2f5f2; color: #1a3a1a; }
.lf-x:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.lf-body { flex: 1; min-height: 0; background: #f2f6f3; display: flex; align-items: center; justify-content: center; }
.lf-frame { width: 100%; height: 100%; border: none; background: #fff; }
.lf-img { max-width: 100%; max-height: 100%; object-fit: contain; display: block; }
.lf-msg { display: flex; flex-direction: column; align-items: center; gap: 10px; text-align: center; max-width: 380px; padding: 20px; }
.lf-msg p { margin: 0; font-size: 0.88rem; line-height: 1.5; color: #4a5a4a; }
.lf-spin { color: #3f9a6b; animation: lf-spin 0.9s linear infinite; }
@keyframes lf-spin { to { transform: rotate(360deg); } }
@media (prefers-reduced-motion: reduce) { .lf-spin { animation: none; } }
.lf-foot { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: 10px; padding: 12px 20px; border-top: 1px solid #d9e3dc; }
.lf-decline { padding: 12px 20px 0; border-top: 1px solid #d9e3dc; }
.lf-label { display: block; font-size: 0.84rem; font-weight: 600; margin: 0 0 6px; }
.lf-input { width: 100%; border: 1px solid #d9e3dc; border-radius: 8px; padding: 9px 12px; font-family: inherit; font-size: 0.86rem; color: #1a3a1a; resize: vertical; box-sizing: border-box; }
.lf-input:focus { outline: none; border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.15); }
.lf-error { font-size: 0.8rem; color: #a12525; margin: 6px 0 0; }
.lf-error-row { padding: 0 20px; }
@media (max-width: 640px) {
  .lf-overlay { padding: 0; }
  .lf { max-width: none; height: 100%; border-radius: 0; }
  .lf-foot > * { flex: 1; }
}
</style>
