<template>
  <!-- Client Lab Results page (/lab-results): what the RND requested, and
       every uploaded result. GET/POST /api/client/labs/. -->
  <div class="nm-page">
    <header class="nm-page-header">
      <div>
        <p class="nm-page-sub">Lab tests your RND asks for, and the results you've uploaded. Only you and your RND can open them.</p>
      </div>
      <label v-if="data?.has_rnd" class="nm-btn-dark nm-btn-sm upload-btn">
        <input type="file" :accept="LAB_ACCEPT" multiple class="sr-only" @change="e => pick(e, null)" />
        <Upload :size="14" aria-hidden="true" /> Upload a result
      </label>
    </header>

    <p v-if="error" class="nm-error">{{ error }} <button class="nm-btn-soft nm-btn-sm" @click="load">Try again</button></p>
    <p v-if="pickError" class="nm-error" role="alert">{{ pickError }}</p>
    <div v-if="loading" class="nm-panel"><p class="nm-muted">Loading…</p></div>

    <template v-else-if="data">
      <div v-if="!data.has_rnd && !data.results.length" class="nm-panel nm-empty">
        <FlaskConical :size="28" />
        <p><strong>No lab results yet.</strong></p>
        <p class="nm-muted">Once you have an RND, they can request lab tests and you can upload the results here.</p>
        <NuxtLink to="/find-rnd" class="nm-btn-dark nm-btn-sm">Find an RND</NuxtLink>
      </div>

      <!-- REQUESTED -->
      <section v-if="openRequests.length" class="nm-panel">
        <h2 class="nm-panel-title">Requested by your RND</h2>
        <div v-for="r in openRequests" :key="r.id" class="req">
          <div class="req-main">
            <p class="req-title"><FlaskConical :size="15" aria-hidden="true" /> {{ r.test_names.join(', ') }}</p>
            <p class="req-due">{{ neededBefore(r) }}</p>
            <p class="req-meta">Requested by RND {{ r.requested_by }} on {{ labDay(r.created_at) }}<template v-if="r.uploaded_tests.length">, {{ r.uploaded_tests.length }} of {{ r.tests.length }} uploaded</template></p>
            <p v-if="r.note" class="req-note">“{{ r.note }}”</p>
          </div>
          <label class="nm-btn-dark nm-btn-sm upload-btn">
            <input type="file" :accept="LAB_ACCEPT" multiple class="sr-only" @change="e => pick(e, r.id)" />
            <Upload :size="14" aria-hidden="true" /> Upload result
          </label>
        </div>
      </section>

      <!-- RESULTS -->
      <section v-if="data.has_rnd || data.results.length" class="nm-panel">
        <h2 class="nm-panel-title">My lab results</h2>
        <p v-if="!data.results.length" class="nm-muted">Nothing uploaded yet. Use <strong>Upload a result</strong> to send your RND lab results you already have.</p>
        <div v-for="r in data.results" :key="r.id" class="res">
          <span class="res-icon"><FileText :size="17" /></span>
          <div class="res-main">
            <p class="res-title">{{ r.test_names.join(', ') }}</p>
            <p class="res-meta">
              Taken {{ labDate(r.taken_on) }}<template v-if="FASTED_LABEL[r.fasted]">, <span :class="{ 'not-fasting': notFastingGlucose(r) }">{{ FASTED_LABEL[r.fasted] }}</span></template>,
              {{ r.file_name }} ({{ fileSize(r.file_size) }})
            </p>
            <p v-if="notFastingGlucose(r)" class="res-warn"><AlertTriangle :size="13" aria-hidden="true" /> Glucose taken while not fasting reads high. Your RND may ask you to repeat it after 8 hours without food.</p>
          </div>
          <span class="nm-pill" :class="r.reviewed_at ? 'green' : 'gold'">{{ r.reviewed_at ? 'Reviewed' : 'Waiting for your RND' }}</span>
          <div class="res-actions">
            <button type="button" class="nm-btn-soft nm-btn-sm" @click="view(r)"><Eye :size="13" aria-hidden="true" /> View</button>
            <template v-if="!r.reviewed_at">
              <button type="button" class="nm-btn-soft nm-btn-sm" @click="replacing = r"><RefreshCw :size="13" aria-hidden="true" /> Replace</button>
              <button type="button" class="nm-btn-danger solid nm-btn-sm" :disabled="deleting === r.id" @click="remove(r)"><Trash2 :size="13" aria-hidden="true" /> Delete</button>
            </template>
          </div>
        </div>
        <p v-if="data.results.some(r => r.reviewed_at)" class="nm-hint">Results your RND has reviewed are part of your record and can't be changed.</p>
      </section>
    </template>

    <LabUploadModal
      v-if="picked.length && data" :tests="data.tests" :requests="openRequests" :initial-files="picked" :preset-request-id="pickedFor"
      @close="picked = []" @uploaded="afterUpload"
    />
    <LabUploadModal
      v-if="replacing && data" :tests="data.tests" :replace="replacing"
      @close="replacing = null" @uploaded="afterUpload"
    />
    <div v-if="toast" class="nm-toast" role="status">{{ toast }}</div>
  </div>
</template>

<script setup>
import { AlertTriangle, Eye, FileText, FlaskConical, RefreshCw, Trash2, Upload } from 'lucide-vue-next'
import { FASTED_LABEL, LAB_ACCEPT, fileSize, labDate, labDay, neededBefore, openLabFile, splitLabFiles } from '~/utils/labs'

const { get, del } = useApi()
const data = ref(null)
const loading = ref(true)
const error = ref('')
const pickError = ref('')
const picked = ref([])
const pickedFor = ref(null)
const replacing = ref(null)
const deleting = ref(null)
const toast = ref('')

const openRequests = computed(() => (data.value?.requests || []).filter(r => r.status === 'open'))
// a fasting blood glucose test taken while not fasting: flagged red
const notFastingGlucose = r => r.fasted === 'no' && (r.tests || []).includes('fbs')

async function load() {
  error.value = ''
  try {
    data.value = await get('/client/labs/')
  } catch {
    error.value = 'Could not load your lab results.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

function flash(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3000)
}

async function pick(e, requestId) {
  const files = Array.from(e.target.files || [])
  e.target.value = ''
  const { ok, error } = await splitLabFiles(files)
  pickError.value = error
  if (!ok.length) return
  pickedFor.value = requestId
  picked.value = ok
}

async function afterUpload() {
  picked.value = []
  replacing.value = null
  flash('Uploaded. Your RND can see it now.')
  await load()
}

async function view(r) {
  if (!(await openLabFile(get, `/client/lab-results/${r.id}/file/`))) flash('Could not open the file. Please try again.')
}

async function remove(r) {
  deleting.value = r.id
  try {
    await del(`/client/lab-results/${r.id}/`)
    flash('Lab result deleted.')
    await load()
  } catch (e) {
    flash(e?.data?.detail || 'Could not delete it.')
  } finally {
    deleting.value = null
  }
}
</script>

<style scoped>
.nm-page-header { align-items: center; }
.upload-btn { display: inline-flex; align-items: center; gap: 6px; cursor: pointer; white-space: nowrap; }
.upload-btn:focus-within { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.nm-empty { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 6px; color: #2f6b4f; }
.nm-empty p { margin: 0; color: #1a3a1a; }

/* a request is something still to do: dashed green */
.req { display: flex; align-items: flex-start; gap: 14px; padding: 14px; border: 1.5px dashed #3f9a6b; background: #fff; border-radius: 12px; margin-top: 10px; }
.req-main { flex: 1; min-width: 0; }
.req-title { display: flex; align-items: flex-start; gap: 6px; font-weight: 700; font-size: 0.9rem; color: #1a3a1a; margin: 0; }
.req-title svg { flex-shrink: 0; margin-top: 3px; color: #3f9a6b; }
.req-due { font-size: 0.82rem; font-weight: 600; color: #8a6a10; margin: 4px 0 0; }
.req-meta { font-size: 0.8rem; color: #6a7a6a; margin: 3px 0 0; }
.req-note { font-size: 0.84rem; color: #1a3a1a; margin: 8px 0 0; padding: 8px 10px; background: #f2f6f3; border-radius: 8px; overflow-wrap: anywhere; }

.res { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-top: 1px solid #d9e3dc; flex-wrap: wrap; }
.res:first-of-type { border-top: none; }
.res-icon { width: 36px; height: 36px; border-radius: 10px; background: #e3efe7; color: #1e4a26; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.res-main { flex: 1; min-width: 180px; }
.res-title { font-weight: 600; font-size: 0.88rem; color: #1a3a1a; margin: 0; }
.res-meta { font-size: 0.8rem; color: #6a7a6a; margin: 2px 0 0; overflow-wrap: anywhere; }
.not-fasting { color: #a12525; font-weight: 600; }
.res-warn { display: flex; gap: 6px; align-items: flex-start; font-size: 0.8rem; color: #8a1f14; background: #fdf1ef; border-radius: 8px; padding: 6px 10px; margin: 6px 0 0; line-height: 1.4; }
.res-warn svg { flex-shrink: 0; margin-top: 2px; color: #c0392b; }
.res-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.res-actions button { display: inline-flex; align-items: center; gap: 5px; }

.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0; }
@media (max-width: 600px) {
  .nm-page-header { flex-direction: column; align-items: stretch; gap: 10px; }
  .req { flex-direction: column; }
  .req .upload-btn, .nm-page-header .upload-btn { justify-content: center; }
  .res-actions { width: 100%; }
  .res-actions button { flex: 1; justify-content: center; }
}
</style>
