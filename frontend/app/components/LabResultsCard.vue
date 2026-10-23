<template>
  <!-- Client dashboard: Upload Lab Results (between My tasks and Recent
       Activity). Hidden until the client has an RND — uploads go to them. -->
  <div v-if="data?.has_rnd" class="panel lab-card" :class="{ requested: openRequests.length }">
    <div class="panel-header-row">
      <h3 class="panel-title flush">Upload Lab Results</h3>
      <NuxtLink to="/lab-results" class="nm-btn-soft nm-btn-sm">All lab results</NuxtLink>
    </div>

    <div v-for="r in openRequests" :key="r.id" class="lab-request">
      <p class="lab-request-title"><FlaskConical :size="15" /> Your RND requested: {{ r.test_names.join(', ') }}</p>
      <p class="lab-request-due">{{ neededBefore(r) }}</p>
      <p v-if="r.note" class="lab-request-note">“{{ r.note }}”</p>
    </div>
    <p v-if="!openRequests.length" class="lab-intro">Have lab results? Upload them for RND {{ data.rnd_name }}.</p>

    <label class="lab-drop">
      <input type="file" :accept="LAB_ACCEPT" multiple class="sr-only" @change="onPick" />
      <CloudUpload :size="28" class="lab-drop-icon" />
      <span class="lab-drop-text"><span class="desk">Browse files</span><span class="phone">Choose a file or take a photo</span></span>
      <span class="lab-drop-hint">PDF, JPG or PNG, up to {{ LAB_MAX_MB }} MB</span>
    </label>
    <p v-if="pickError" class="nm-field-error" role="alert">{{ pickError }}</p>
    <p v-if="done" class="lab-done" role="status"><CheckCircle2 :size="14" /> Uploaded. Your RND can see it now.</p>

    <ul v-if="recent.length" class="lab-recent">
      <li v-for="r in recent" :key="r.id">
        <FileText :size="14" />
        <span class="lab-recent-name">{{ r.test_names.join(', ') }}, {{ labDate(r.taken_on) }}</span>
        <span class="nm-pill" :class="r.reviewed_at ? 'green' : 'gold'">{{ r.reviewed_at ? 'Reviewed' : 'Waiting for your RND' }}</span>
      </li>
    </ul>

    <LabUploadModal
      v-if="picked.length" :tests="data.tests" :requests="openRequests" :initial-files="picked"
      @close="picked = []" @uploaded="onUploaded"
    />
  </div>
</template>

<script setup>
import { CheckCircle2, CloudUpload, FileText, FlaskConical } from 'lucide-vue-next'
import { LAB_ACCEPT, LAB_MAX_MB, labDate, neededBefore, splitLabFiles } from '~/utils/labs'

const emit = defineEmits(['uploaded'])
const { get } = useApi()

const data = ref(null)
const picked = ref([])
const pickError = ref('')
const done = ref(false)

const openRequests = computed(() => (data.value?.requests || []).filter(r => r.status === 'open'))
const recent = computed(() => (data.value?.results || []).slice(0, 2))

async function load() {
  try { data.value = await get('/client/labs/') } catch { data.value = null }
}
onMounted(load)

async function onPick(e) {
  const files = Array.from(e.target.files || [])
  e.target.value = ''
  done.value = false
  const { ok, error } = await splitLabFiles(files)
  pickError.value = error
  if (ok.length) picked.value = ok
}

async function onUploaded() {
  picked.value = []
  done.value = true
  await load()
  emit('uploaded')
}
</script>

<style scoped>
.panel { background: #fff; border-radius: 14px; border: 1px solid #d9e3dc; padding: 22px; box-shadow: 0 0 1px rgba(0, 77, 58, 0.06), 0 0 14px rgba(0, 77, 58, 0.09); }
.panel-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0; }
.panel-link { font-size: 0.78rem; color: #1f8f5c; font-weight: 600; text-decoration: none; white-space: nowrap; }
.panel-link:hover { text-decoration: underline; }


.lab-request { background: #fff; border: 1.5px dashed #3f9a6b; border-radius: 10px; padding: 10px 12px; margin-bottom: 10px; }
.lab-request-title { display: flex; align-items: flex-start; gap: 6px; font-size: 0.84rem; font-weight: 700; color: #6b4e00; margin: 0; }
.lab-request-title svg { flex-shrink: 0; margin-top: 2px; }
.lab-request-due { font-size: 0.78rem; color: #8a6a10; margin: 3px 0 0 21px; font-weight: 600; }
.lab-request-note { font-size: 0.76rem; color: #6a5a3a; margin: 4px 0 0 21px; font-style: italic; overflow-wrap: anywhere; }
.lab-intro { font-size: 0.82rem; color: #6a7a6a; margin: 0 0 10px; }

.lab-drop { display: flex; flex-direction: column; align-items: center; gap: 4px; text-align: center; padding: 20px 12px; border: 2px dashed #b7cbbd; border-radius: 12px; background: #f2f7f3; cursor: pointer; transition: background 0.15s, border-color 0.15s; }
.lab-drop:hover { background: #e9f2ec; border-color: #8fb19b; }
.lab-drop:focus-within { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.lab-drop-icon { color: #2f6b4f; }
.lab-drop-text { font-size: 0.86rem; font-weight: 700; color: #00382a; }
.lab-drop-text .phone { display: none; }
.lab-drop-hint { font-size: 0.72rem; color: #8a9a8a; }
.lab-done { display: flex; align-items: center; gap: 6px; font-size: 0.8rem; font-weight: 600; color: #1f8f5c; margin: 10px 0 0; }
.nm-field-error { margin-top: 6px; }

.lab-recent { list-style: none; margin: 12px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.lab-recent li { display: flex; align-items: center; gap: 8px; font-size: 0.8rem; color: #2a3a2a; }
.lab-recent li svg { color: #6a7a6a; flex-shrink: 0; }
.lab-recent-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0; }
@media (max-width: 700px) {
  .lab-drop-text .desk { display: none; }
  .lab-drop-text .phone { display: inline; }
}
</style>
