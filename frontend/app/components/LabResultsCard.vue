<template>
  <!-- Client dashboard: Upload Lab Results (between My tasks and Recent
       Activity). Hidden until the client has an RND — uploads go to them. -->
  <div v-if="data?.has_rnd" class="panel lab-card" :class="{ requested: openRequests.length }">
    <div class="panel-header-row">
      <div>
        <p class="lx-k"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6M10 3v6L4.5 18.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-2.5L14 9V3" /><path d="M7 15h10" /></svg>Lab results</p>
        <h3 class="panel-title flush">Upload lab results</h3>
        <p v-if="!openRequests.length" class="lab-intro">Have lab results? Upload them for RND {{ data.rnd_name }}.</p>
      </div>
      <NuxtLink to="/lab-results" class="lx-all">All labs<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
    </div>

    <div v-for="r in openRequests" :key="r.id" class="lab-request">
      <p class="lab-request-title"><FlaskConical :size="15" /> Your RND requested: {{ r.test_names.join(', ') }}</p>
      <p class="lab-request-due">{{ neededBefore(r) }}</p>
      <p v-if="r.note" class="lab-request-note">“{{ r.note }}”</p>
    </div>

    <label class="lab-drop">
      <input type="file" :accept="LAB_ACCEPT" multiple class="sr-only" @change="onPick" />
      <span class="lx-ico"><CloudUpload :size="26" class="lab-drop-icon" /></span>
      <span class="lx-title">Upload a lab result</span>
      <span class="lx-or desk">Drag a file here, or</span>
      <span class="lab-drop-text lx-btn"><span class="desk">Browse files</span><span class="phone">Choose a file or take a photo</span></span>
      <span class="lab-drop-hint">PDF, JPG or PNG, up to {{ LAB_MAX_MB }} MB</span>
    </label>
    <p v-if="pickError" class="nm-field-error" role="alert">{{ pickError }}</p>
    <p v-if="done" class="lab-done" role="status"><CheckCircle2 :size="14" /> Uploaded. Your RND can see it now.</p>

    <ul v-if="recent.length" class="lab-recent">
      <li v-for="r in recent" :key="r.id">
        <span class="lx-fi"><FileText :size="15" /></span>
        <span class="lab-recent-name">{{ r.test_names.join(', ') }}</span>
        <span class="lx-date">{{ labDate(r.taken_on) }}</span>
        <i class="lx-dot" :class="lxState(r)" :title="LX_LABEL[lxState(r)]" :aria-label="LX_LABEL[lxState(r)]" />
      </li>
    </ul>
    <p v-if="recent.length" class="lx-key">
      <span v-for="s in lxKeys" :key="s"><i class="lx-dot" :class="s" aria-hidden="true" />{{ LX_LABEL[s] }}</span>
    </p>

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
useAutoRefresh(load)

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

// ---- UI helpers only: a coloured dot per upload, with a small key ----
const LX_LABEL = { ok: 'Accepted', again: 'Upload again', wait: 'Waiting for your RND' }
const lxState = r => (r.reviewed_at ? 'ok' : r.declined_at ? 'again' : 'wait')
const lxKeys = computed(() => ['wait', 'ok', 'again'].filter(k => recent.value.some(r => lxState(r) === k)))
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

/* ===== Redesign: eyebrow, big centred upload, compact list with dots ===== */
.panel.lab-card { padding: 24px 26px; border-radius: 22px; border: 1.5px solid #E1EAE4; box-shadow: none; font-family: 'DM Sans', sans-serif; }
.lab-card .panel-header-row { margin-bottom: 16px; }
.lx-k { display: flex; align-items: center; gap: 7px; margin: 0 0 4px; font-size: 12px; font-weight: 800; color: #9A7300; }
.lab-card .panel-title { font-size: 22px; color: #0E3A2C; }
.lab-card .lab-intro { margin: 3px 0 0; font-size: 13.5px; color: #4A5A52; }
.lx-all { display: inline-flex; align-items: center; gap: 6px; flex-shrink: 0; height: 36px; padding: 0 14px; border-radius: 10px; background: #E3EFE7; color: #004D3A; font-size: 13px; font-weight: 800; text-decoration: none; white-space: nowrap; }
.lx-all:hover { background: #D3E7DA; }
.lab-request { border-radius: 14px; background: #FDF9E8; border: 1.5px dashed #E6CF7A; }
.lab-drop { gap: 0; padding: 26px 18px 22px; border: 1.5px dashed #B9CFC1; border-radius: 18px; background: radial-gradient(120% 100% at 50% 0%, #EAF4EE, #F7FBF8 70%); }
.lab-drop:hover { background: radial-gradient(120% 100% at 50% 0%, #E1EFE6, #F4F9F6 70%); border-color: #004D3A; }
.lx-ico { width: 58px; height: 58px; border-radius: 50%; background: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 0 0 7px rgba(0, 77, 58, 0.08); }
.lab-drop .lab-drop-icon { color: #EFBF04; }
.lx-title { margin-top: 12px; font-family: 'Playfair Display', Georgia, serif; font-size: 18px; font-weight: 700; color: #0E3A2C; }
.lx-or { margin-top: 2px; font-size: 13px; color: #4A5A52; }
.lab-drop-text.lx-btn { margin-top: 10px; display: inline-flex; align-items: center; height: 40px; padding: 0 18px; border-radius: 12px; background: #004D3A; color: #FFFFFF; font-size: 13px; font-weight: 800; }
.lab-drop .lab-drop-hint { margin-top: 10px; font-size: 12px; color: #8A9A91; }
.lab-recent { gap: 0; margin-top: 14px; }
.lab-recent li { gap: 10px; padding: 10px 4px; border-top: 1px solid #EEF2EF; font-size: 14px; }
.lab-recent li:first-child { border-top: none; }
.lx-fi { width: 32px; height: 32px; flex-shrink: 0; border-radius: 50%; background: #F1F5F2; display: inline-flex; align-items: center; justify-content: center; }
.lab-recent li .lx-fi svg { color: #004D3A; }
.lab-recent-name { font-weight: 700; color: #0E3A2C; }
.lx-date { flex-shrink: 0; font-size: 12.5px; color: #6B7D73; }
.lx-dot { display: inline-block; flex-shrink: 0; width: 9px; height: 9px; border-radius: 50%; }
.lx-dot.wait { background: #EFBF04; }
.lx-dot.ok { background: #1F7A4D; }
.lx-dot.again { background: #C0392B; }
.lx-key { display: flex; flex-wrap: wrap; gap: 6px 14px; margin: 8px 0 0; font-size: 11.5px; color: #6B7D73; }
.lx-key span { display: inline-flex; align-items: center; gap: 5px; }
.lx-or.desk { display: inline; }
@media (max-width: 700px) {
  .panel.lab-card { padding: 18px 14px; }
  .lx-or.desk { display: none; }
}
</style>