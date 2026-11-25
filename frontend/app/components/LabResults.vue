<template>
  <!-- Client Lab Results page (/lab-results): what the RND requested, and
       every uploaded result. GET/POST /api/client/labs/. -->
  <div class="nm-page lb-page">
    <!-- HERO -->
    <header class="nm-page-header lb-hero">
      <img class="lb-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="lb-hero-fade" aria-hidden="true"></span>
      <div class="lb-hero-text">
        <p class="lb-eyebrow"><span aria-hidden="true"></span>Lab results</p>
        <h2 class="lb-heading">Your lab tests, <em>safe and shared.</em></h2>
        <p class="nm-page-sub"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>Lab tests your RND asks for, and the results you've uploaded. Only you and your RND can open them.</p>
      </div>
      <!-- one upload button at a time: with an open request, use the request's
           own button (its pop-up still offers "Not for a request") -->
      <label v-if="data?.has_rnd && !openRequests.length" class="lb-btn gold upload-btn">
        <input type="file" :accept="LAB_ACCEPT" multiple class="sr-only" @change="e => pick(e, null)" />
        <Upload :size="17" aria-hidden="true" /> Upload a result
      </label>
    </header>

    <p v-if="error" class="nm-error">{{ error }} <button class="lb-btn soft sm" @click="load">Try again</button></p>
    <p v-if="pickError" class="nm-error" role="alert">{{ pickError }}</p>
    <div v-if="loading" class="lb-panel">
      <div v-for="n in 2" :key="n" class="lb-sk"><span class="sk sk-icon" /><span style="flex: 1"><span class="sk sk-line w60" /><span class="sk sk-line w40" /></span></div>
    </div>

    <template v-else-if="data">
      <div v-if="!data.has_rnd && !data.results.length" class="lb-panel lb-empty">
        <span class="lb-empty-ico"><FlaskConical :size="28" /></span>
        <p class="lb-empty-title">No lab results yet.</p>
        <p class="lb-muted">Once you have an RND, they can request lab tests and you can upload the results here.</p>
        <NuxtLink to="/find-rnd" class="lb-btn dark">Find an RND</NuxtLink>
      </div>

      <!-- REQUESTED -->
      <section v-if="openRequests.length" class="lb-req-panel lx-block">
        <div class="lb-head lx-bh">
          <div>
            <p class="lx-k gold"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6M10 3v6L4.5 18.5A2 2 0 0 0 6.2 21h11.6a2 2 0 0 0 1.7-2.5L14 9V3" /><path d="M7 15h10" /></svg>To do</p>
            <h2 class="lb-title">Requested by your RND</h2>
            <p class="lb-sub">Upload the results here so your RND can review them.</p>
          </div>
          <span class="lx-cnt gold">{{ openRequests.length }} request{{ openRequests.length === 1 ? '' : 's' }}</span>
        </div>
        <div class="lx-list">
          <div v-for="r in openRequests" :key="r.id" class="req lx-row">
            <span class="lx-ic gold"><FlaskConical :size="19" aria-hidden="true" /></span>
            <div class="req-main">
              <p class="req-title">{{ r.test_names.join(', ') }}</p>
              <p class="lx-meta">
                <span class="req-due lx-due"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ neededBefore(r) }}</span>
                <span class="req-meta">Requested by RND {{ r.requested_by }} on {{ labDay(r.created_at) }}<template v-if="r.uploaded_tests.length">, {{ r.uploaded_tests.length }} of {{ r.tests.length }} uploaded</template></span>
              </p>
              <p v-if="r.note" class="req-note">“{{ r.note }}”</p>
            </div>
            <label class="lb-btn dark upload-btn">
              <input type="file" :accept="LAB_ACCEPT" multiple class="sr-only" @change="e => pick(e, r.id)" />
              <Upload :size="16" aria-hidden="true" /> Upload result
            </label>
          </div>
        </div>
      </section>

      <!-- RESULTS -->
      <section v-if="data.has_rnd || data.results.length" class="lb-panel lx-block">
        <div class="lb-head lx-bh">
          <div class="lb-head-text">
            <p class="lx-k"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6" /></svg>History</p>
            <h2 class="lb-title">My lab results</h2>
            <p class="lb-sub">Every result you've sent your RND.</p>
          </div>
          <span v-if="data.results.length" class="lb-count lx-cnt">{{ data.results.length }} file{{ data.results.length === 1 ? '' : 's' }}</span>
        </div>

        <div v-if="!data.results.length" class="lb-none">
          <span class="lb-none-ico"><Upload :size="24" aria-hidden="true" /></span>
          <p class="lb-none-title">Nothing uploaded yet</p>
          <p class="lb-muted">Use <strong>Upload a result</strong> to send your RND lab results you already have.</p>
        </div>

        <div class="lx-list">
          <div v-for="r in data.results" :key="r.id" class="res lx-row">
            <span class="lx-ic" :class="r.reviewed_at ? 'green' : r.declined_at && !replaced(r) ? 'red' : r.declined_at ? 'muted' : 'gold'"><FileText :size="18" /></span>
            <div class="res-main">
              <p class="res-title">{{ r.test_names.join(', ') }}<span v-if="notFastingGlucose(r)" class="lx-tag">{{ FASTED_LABEL[r.fasted] }}</span></p>
              <p class="lx-meta lx-file">
                <span class="lx-mi"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>Taken {{ labDate(r.taken_on) }}<template v-if="FASTED_LABEL[r.fasted] && !notFastingGlucose(r)">, {{ FASTED_LABEL[r.fasted] }}</template></span>
                <i aria-hidden="true" />
                <span class="lx-mi lx-fn"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.5 12.5 21a5 5 0 0 1-7-7L14 5.5a3.5 3.5 0 0 1 5 5L10.5 19a2 2 0 0 1-3-3L15 8.5" /></svg><span>{{ r.file_name }}</span></span>
                <em>{{ fileSize(r.file_size) }}</em>
              </p>
              <p v-if="r.declined_at && replaced(r)" class="res-meta">Your RND sent this back: {{ r.decline_reason }} You've uploaded a new one since.</p>
              <p v-else-if="r.declined_at" class="res-warn"><AlertTriangle :size="14" aria-hidden="true" /> Your RND sent this back: {{ r.decline_reason }} Use Replace to upload it again.</p>
              <p v-if="notFastingGlucose(r)" class="res-warn"><AlertTriangle :size="14" aria-hidden="true" /> Glucose taken while not fasting reads high. Your RND may ask you to repeat it after 8 hours without food.</p>
            </div>
            <span v-if="r.declined_at && replaced(r)" class="nm-pill lb-pill muted"><i aria-hidden="true"></i>Replaced</span>
            <span v-else class="nm-pill lb-pill" :class="r.reviewed_at ? 'green' : r.declined_at ? 'red' : 'gold'"><i aria-hidden="true"></i>{{ r.reviewed_at ? 'Accepted' : r.declined_at ? 'Upload again' : 'Waiting for your RND' }}</span>
            <div class="res-actions lx-acts">
              <button type="button" class="lx-ib" title="View" aria-label="View" @click="view(r)"><Eye :size="16" aria-hidden="true" /></button>
              <template v-if="!r.reviewed_at">
                <button v-if="!(r.declined_at && replaced(r))" type="button" class="lx-ib" title="Replace" aria-label="Replace" @click="replacing = r"><RefreshCw :size="16" aria-hidden="true" /></button>
                <button type="button" class="lx-ib del" title="Delete" aria-label="Delete" :disabled="deleting === r.id" @click="remove(r)"><Trash2 :size="16" aria-hidden="true" /></button>
              </template>
            </div>
          </div>
        </div>
        <p v-if="data.results.some(r => r.reviewed_at)" class="nm-hint lb-hint"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg>Results your RND accepted are part of your record and can't be changed.</p>
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
    <LabFileModal
      v-if="viewing" :path="viewing.path" :title="viewing.title" :sub="viewing.sub" :file-name="viewing.fileName"
      @close="viewing = null" 
    />
  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import { AlertTriangle, Eye, FileText, FlaskConical, RefreshCw, Trash2, Upload } from 'lucide-vue-next'
import { FASTED_LABEL, LAB_ACCEPT, fileSize, labDate, labDay, neededBefore, splitLabFiles } from '~/utils/labs'

const { get, del } = useApi()
const data = ref(null)
const loading = ref(true)
const error = ref('')
const pickError = ref('')
const picked = ref([])
const pickedFor = ref(null)
const replacing = ref(null)
const deleting = ref(null)
const toast = useToast() // the app's toast (2026-11-03)

const openRequests = computed(() => (data.value?.requests || []).filter(r => r.status === 'open'))
// a fasting blood glucose test taken while not fasting: flagged red
// A declined upload whose tests were all uploaded again later: nothing left to do.
const replaced = r => (r.tests || []).every(t => (data.value?.results || []).some(o =>
  o.id !== r.id && !o.declined_at && (o.tests || []).includes(t) && new Date(o.uploaded_at) > new Date(r.uploaded_at)))
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
useAutoRefresh(load)

function flash(msg, opts) {
  toast.success(msg, opts)
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

// opens in a pop-up on the page (LabFileModal), not a new tab
const viewing = ref(null)
function view(r) {
  viewing.value = { path: `/client/lab-results/${r.id}/file/`, title: r.test_names.join(', '), sub: `Taken ${labDate(r.taken_on)}, ${r.file_name}`, fileName: r.file_name }
}

async function remove(r) {
  deleting.value = r.id
  try {
    await del(`/client/lab-results/${r.id}/`)
    flash('Lab result deleted.')
    await load()
  } catch (e) {
    toast.error(e?.data?.detail || 'Could not delete this lab result. Please try again.')
  } finally {
    deleting.value = null
  }
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
</script>

<style scoped>
/* =========================================================
   Lab results: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.lb-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; gap: 18px; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }
.lb-page .nm-error { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 0; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 14px; }

/* ---------- HERO ---------- */
.lb-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: flex-end !important;
  justify-content: space-between;
  gap: 20px 28px;
  flex-wrap: wrap;
  margin: 0;
  padding: 32px 34px;
  border-radius: 24px;
  color: #FFFFFF;
  background:
    radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%),
    linear-gradient(115deg, #035A45 0%, #004D3A 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -24px rgba(0, 77, 58, 0.55);
}
.lb-hero-plate { position: absolute; right: -70px; top: 50%; width: 400px; height: 400px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.55; pointer-events: none; }
.lb-hero-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004D3A 0%, #004D3A 45%, rgba(0, 77, 58, 0.75) 62%, rgba(0, 70, 52, 0.15) 100%); pointer-events: none; }
.lb-hero-text { position: relative; z-index: 1; max-width: 620px; }
.lb-eyebrow { margin: 0; display: flex; align-items: center; gap: 10px; font-size: 12.5px; font-weight: 800; color: #EFBF04; }
.lb-eyebrow span { width: 26px; height: 2px; border-radius: 2px; background: #EFBF04; }
.lb-heading { margin: 10px 0 12px; font-family: 'Playfair Display', Georgia, serif; font-size: 40px; font-weight: 700; line-height: 1.12; color: #FFFFFF; }
.lb-heading em { font-style: italic; color: #EFBF04; }
.lb-hero .nm-page-sub { margin: 0; display: flex; align-items: flex-start; gap: 10px; font-size: 15.0px; line-height: 1.55; color: rgba(255, 255, 255, 0.88); }
.lb-hero .nm-page-sub .ic { margin-top: 5px; color: #8FD4A8; }
.lb-hero .upload-btn { position: relative; z-index: 1; }

/* ---------- BUTTONS ---------- */
.lb-btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 46px; padding: 0 20px; border: none; border-radius: 12px; font-family: inherit; font-size: 14px; font-weight: 700; text-decoration: none; white-space: nowrap; cursor: pointer; transition: background-color .15s; }
.lb-btn.gold { background: #EFBF04; color: #004D3A; font-weight: 800; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
.lb-btn.gold:hover { background: #F5CB1F; }
.lb-btn.dark { background: #004D3A; color: #FFFFFF; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.lb-btn.dark:hover { background: #0A5C46; }
.lb-btn.soft { background: #F1F6F2; color: #004D3A; border: 1px solid #DCE8E0; }
.lb-btn.soft:hover { background: #E3EFE7; }
.lb-btn.danger { background: #FDECEC; color: #B42318; border: 1px solid #F6CFCB; }
.lb-btn.danger:hover:not(:disabled) { background: #FAD9D6; }
.lb-btn:disabled { opacity: .55; cursor: not-allowed; }
.lb-btn.sm { height: 38px; padding: 0 14px; font-size: 13px; }
.upload-btn:focus-within,
.lb-btn:focus-visible { outline: 3px solid rgba(239, 191, 4, 0.6); outline-offset: 2px; }

/* ---------- PANELS ---------- */
.lb-panel,
.lb-req-panel { padding: 22px 24px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.lb-req-panel { background: linear-gradient(180deg, #FFFBEA 0%, #FFFFFF 70%); border: 1.5px solid #F1DE97; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(154, 115, 0, 0.35); }
.lb-head { display: flex; align-items: flex-start; gap: 14px; }
.lb-head-text { flex: 1; min-width: 0; }
.lb-head-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 14px; background: #E3EFE7; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.lb-head-ico.gold { background: #EFBF04; color: #004D3A; }
.lb-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-weight: 700; color: #0E3A2C; }
.lb-sub { margin: 4px 0 0; font-size: 13.5px; color: #6B7D73; }
.lb-req-panel .lb-sub { color: #6B5A1F; }
.lb-count { flex-shrink: 0; align-self: center; padding: 6px 12px; border-radius: 999px; background: #EAF4EE; color: #004D3A; font-size: 13px; font-weight: 700; }
.lb-muted { margin: 0; font-size: 14px; line-height: 1.55; color: #6B7D73; }

/* empty states */
.lb-empty { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 44px 20px; text-align: center; }
.lb-empty .lb-muted { max-width: 420px; margin-bottom: 10px; }
.lb-empty-ico { width: 60px; height: 60px; margin-bottom: 8px; border-radius: 18px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.lb-empty-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #0E3A2C; }
.lb-none { display: flex; flex-direction: column; align-items: center; gap: 4px; margin-top: 18px; padding: 30px 20px; border-radius: 16px; border: 1.5px dashed #CFDDD4; background: #F8FBF9; text-align: center; }
.lb-none-ico { width: 52px; height: 52px; margin-bottom: 6px; border-radius: 50%; background: #FFFFFF; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px -14px rgba(0, 77, 58, 0.6); }
.lb-none-title { margin: 0; font-size: 15.5px; font-weight: 700; color: #0E3A2C; }
.lb-none .lb-muted { max-width: 420px; }

/* a request: still to do */
.req { display: flex; align-items: center; gap: 16px; margin-top: 14px; padding: 16px 18px; border-radius: 16px; background: #FFFFFF; border: 1px solid #F1E6BD; }
.req-main { flex: 1; min-width: 0; }
.req-title { margin: 0; font-size: 15.5px; font-weight: 700; color: #0E3A2C; overflow-wrap: anywhere; }
.req-due { display: inline-flex; align-items: center; gap: 6px; margin: 8px 0 0; padding: 4px 10px; border-radius: 999px; background: #FBF3D2; font-size: 12.5px; font-weight: 700; color: #8A6400; }
.req-meta { margin: 6px 0 0; font-size: 13px; color: #6B7D73; }
.req-note { margin: 10px 0 0; padding: 10px 12px; border-left: 3px solid #EFBF04; border-radius: 0 10px 10px 0; background: #FBF8EC; font-size: 13.5px; line-height: 1.5; color: #3E5046; overflow-wrap: anywhere; }

/* results */
.res { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; margin-top: 14px; padding: 16px 18px; border-radius: 16px; border: 1px solid #E7EDE9; background: #FFFFFF; transition: background-color .15s; }
.res:hover { background: #FAFCFA; }
.res-icon { flex-shrink: 0; width: 46px; height: 46px; border-radius: 14px; background: #FBF3D2; color: #9A7300; display: inline-flex; align-items: center; justify-content: center; }
.res-icon.ok { background: #E3EFE7; color: #004D3A; }
.res-icon.bad { background: #FDECEC; color: #B42318; }
.res-main { flex: 1; min-width: 200px; }
.res-title { margin: 0; font-size: 15px; font-weight: 700; color: #0E3A2C; }
.res-meta { margin: 4px 0 0; font-size: 13px; color: #6B7D73; overflow-wrap: anywhere; }
.not-fasting { color: #B42318; font-weight: 700; }
.res-warn { display: flex; gap: 8px; align-items: flex-start; margin: 8px 0 0; padding: 8px 12px; border-radius: 10px; background: #FEF3F2; font-size: 13px; line-height: 1.45; color: #8A1F14; }
.res-warn svg { flex-shrink: 0; margin-top: 1px; color: #C0392B; }
.lb-pill { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 12px; border-radius: 999px; font-size: 12.5px; font-weight: 800; white-space: nowrap; background: #F1F3F2; color: #6B7D73; }
.lb-pill i { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.lb-pill.green { background: #EAF4EE; color: #1F7A4C; }
.lb-pill.gold { background: #FBF3D2; color: #8A6400; }
.lb-pill.red { background: #FDECEC; color: #B42318; }
.res-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.lb-hint { display: flex; align-items: center; gap: 8px; margin: 16px 0 0; font-size: 13px; color: #6B7D73; }
.lb-hint .ic { color: #1F7A4D; }

/* skeleton */
.lb-sk { display: flex; align-items: center; gap: 14px; padding: 10px 0; }
.sk { display: block; background: linear-gradient(90deg, #F0F2F0 25%, #E6EAE6 50%, #F0F2F0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 8px; }
.sk-icon { width: 46px; height: 46px; border-radius: 14px; flex-shrink: 0; }
.sk-line { height: 12px; margin: 6px 0; }
.w60 { width: 60%; } .w40 { width: 40%; }
@keyframes shimmer { to { background-position: -200% 0; } }

.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0; }

/* ---------- SMALLER SCREENS ---------- */
@media (max-width: 960px) {
  .lb-page { gap: 14px; padding-bottom: 96px; }
  .lb-hero { flex-direction: column; align-items: stretch !important; padding: 22px 18px 20px; border-radius: 22px; }
  .lb-hero-plate { width: 170px; height: 170px; right: -50px; top: 18px; transform: none; opacity: .9; }
  .lb-hero-fade { background: linear-gradient(90deg, #004D3A 40%, rgba(0, 77, 58, 0.5) 75%, rgba(0, 77, 58, 0.2)); }
  .lb-hero-text { max-width: 74%; }
  .lb-heading { font-size: 28px; }
  .lb-hero .nm-page-sub { font-size: 13px; }
  .lb-hero .nm-page-sub .ic { display: none; }
  .lb-hero .upload-btn { width: 100%; }
  .lb-panel,
  .lb-req-panel { padding: 16px; border-radius: 18px; }
  .lb-head-ico { width: 40px; height: 40px; }
  .lb-title { font-size: 19px; }
  .req { flex-direction: column; align-items: stretch; padding: 14px; }
  .req .upload-btn { width: 100%; }
  .res { padding: 14px; gap: 12px; }
  .res-main { flex-basis: calc(100% - 60px); min-width: 0; }
  .res-actions { width: 100%; }
  .res-actions > * { flex: 1; }
}

/* ===== Redesign: white blocks, round icons on a timeline, icon actions ===== */
.lx-block { padding: 24px 26px !important; border-radius: 22px !important; background: #FFFFFF !important; border: 1.5px solid #E1EAE4 !important; box-shadow: none !important; }
.lb-head.lx-bh { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 4px; }
.lx-bh .lb-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; color: #0E3A2C; }
.lx-bh .lb-sub { margin: 3px 0 0; font-size: 13.5px; color: #4A5A52; }
.lx-k { display: flex; align-items: center; gap: 7px; margin: 0 0 4px; font-size: 12px; font-weight: 800; color: #1F7A4D; }
.lx-k.gold { color: #9A7300; }
.lx-cnt { flex-shrink: 0; white-space: nowrap; padding: 4px 12px; border-radius: 999px; background: #E3EFE7; color: #004D3A; font-size: 12.5px; font-weight: 800; }
.lx-cnt.gold { background: #FBF3D2; color: #8A6400; }
.lx-list { display: flex; flex-direction: column; margin-top: 10px; }
.lx-row { position: relative; display: grid !important; grid-template-columns: 46px minmax(0, 1fr) auto auto; gap: 14px; align-items: center; margin: 0 !important; padding: 18px 0 !important; border: none !important; border-radius: 0 !important; background: none !important; box-shadow: none !important; }
.req.lx-row { grid-template-columns: 46px minmax(0, 1fr) auto; }
.lx-row:not(:last-child)::after { content: ''; position: absolute; left: 22px; top: 66px; bottom: -18px; width: 2px; background: #E1EAE4; }
.lx-ic { position: relative; z-index: 1; align-self: start; width: 46px; height: 46px; border-radius: 50%; border: 3px solid #FFFFFF; box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; }
.lx-ic.gold { background: #FBF3D2; color: #9A7300; }
.lx-ic.green { background: #DDEFE4; color: #1F7A4D; }
.lx-ic.red { background: #FDECEC; color: #B4384A; }
.lx-ic.muted { background: #EEF2EF; color: #6B7D73; }
.lx-row .req-title, .lx-row .res-title { display: flex; align-items: center; gap: 8px; margin: 0; font-size: 16px; font-weight: 800; color: #0E3A2C; }
.lx-meta { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 12px; margin: 5px 0 0; font-size: 13px; color: #6B7D73; }
.lx-due { display: inline-flex !important; align-items: center; gap: 5px; margin: 0 !important; padding: 3px 10px; border-radius: 999px; background: #FBF3D2; color: #8A6400 !important; font-size: 12px !important; font-weight: 800; }
.lx-meta .req-meta { margin: 0; font-size: 13px; color: #6B7D73; }
.lx-tag { padding: 2px 9px; border-radius: 999px; background: #FDECEC; color: #B4384A; font-size: 11.5px; font-weight: 800; }
.lx-file { flex-wrap: nowrap; gap: 6px; min-width: 0; }
.lx-mi { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
.lx-mi svg { flex-shrink: 0; color: #1F7A4D; }
.lx-fn { min-width: 0; overflow: hidden; }
.lx-fn > span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lx-file > i { width: 4px; height: 4px; flex-shrink: 0; margin: 0 4px; border-radius: 50%; background: #B5C2BA; }
.lx-file em { flex-shrink: 0; font-style: normal; color: #8A9A91; }
.lx-row .res-warn { display: flex; align-items: flex-start; gap: 6px; margin: 8px 0 0; padding: 0; border: none; background: none; font-size: 13px; color: #B4384A; }
.lx-acts { display: flex; gap: 6px; }
.lx-ib { width: 38px; height: 38px; border: 1.5px solid #D3E0D8; border-radius: 10px; background: #FFFFFF; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; }
.lx-ib:hover:not(:disabled) { background: #F1F8F4; border-color: #004D3A; }
.lx-ib.del { border-color: #EBC2BE; color: #B4384A; }
.lx-ib.del:hover:not(:disabled) { background: #FDF0EE; border-color: #B4384A; }
.lx-ib:disabled { opacity: 0.5; cursor: not-allowed; }
.lx-ib:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
.lx-row .upload-btn { height: 44px; border-radius: 12px; }
@media (max-width: 760px) {
  .lx-block { padding: 18px 14px !important; }
  .lx-row, .req.lx-row { grid-template-columns: 42px minmax(0, 1fr); gap: 10px 12px; }
  .lx-ic { width: 42px; height: 42px; }
  .lx-row:not(:last-child)::after { left: 20px; top: 60px; }
  .lx-row .lb-pill, .lx-acts { grid-column: 2; justify-self: start; }
  .lx-row .upload-btn { grid-column: 1 / -1; width: 100%; justify-content: center; }
  .lx-file { flex-wrap: wrap; }
  .lx-fn { flex-basis: 100%; order: 3; }
  .lx-file > i { display: none; }
}
</style>