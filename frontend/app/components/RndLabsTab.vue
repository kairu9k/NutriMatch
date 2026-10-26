<template>
  <!-- Client Detail → Lab results tab (?tab=labs). GET /api/rnd/relationships/<id>/labs/.
       Opening a file marks it reviewed (and is audit-logged on the API). -->
  <div class="nm-panel">
    <div class="nm-panel-head">
      <div>
        <h2 class="nm-panel-title">Lab results</h2>
        <p class="nm-panel-sub">Opening a result marks it reviewed. Copy the values into the NCP record's Assessment step.</p>
      </div>
      <button v-if="data?.can_request" type="button" class="nm-btn-dark nm-btn-sm" @click="requestOpen = true"><FlaskConical :size="14" /> Request lab tests</button>
    </div>

    <p v-if="error" class="nm-error">{{ error }}</p>
    <p v-if="loading" class="nm-muted">Loading…</p>

    <template v-else-if="data">
      <!-- open requests -->
      <div v-for="r in openRequests" :key="r.id" class="lr-req">
        <div class="lr-req-main">
          <p class="lr-req-title">{{ r.test_names.join(', ') }}</p>
          <p class="lr-req-meta">
            Requested {{ labDay(r.created_at) }},
            {{ r.needed_before ? `needed before ${labDayTime(r.needed_before)}` : 'needed before their next consultation' }}
            <template v-if="r.uploaded_tests.length">, {{ r.uploaded_tests.length }} of {{ r.tests.length }} uploaded</template>
          </p>
          <p v-if="r.note" class="lr-req-note">{{ r.note }}</p>
        </div>
        <span class="nm-pill gold">Waiting for patient</span>
        <button v-if="canEdit" type="button" class="nm-btn-danger solid nm-btn-sm" :disabled="cancelling === r.id" @click="cancel(r)">Cancel request</button>
      </div>

      <p v-if="!validResults.length && !openRequests.length" class="nm-muted">
        No lab results yet.<template v-if="data.can_request"> Use <strong>Request lab tests</strong> to ask {{ patientFirstName }} for them.</template>
      </p>

      <!-- results: only the ones that count (to review or accepted) -->
      <div v-for="r in validResults" :key="r.id" class="lr-res" :class="{ new: !r.reviewed_at }">
        <span class="lr-icon"><FileText :size="17" /></span>
        <div class="lr-res-main">
          <p class="lr-res-title">{{ r.test_names.join(', ') }}</p>
          <p class="lr-res-meta">
            Taken {{ labDate(r.taken_on) }}<template v-if="FASTED_LABEL[r.fasted]">, {{ FASTED_LABEL[r.fasted].toLowerCase() }}</template><template v-if="consultGap(r)">, {{ consultGap(r) }}</template>. Uploaded {{ labDay(r.uploaded_at) }}.
          </p>
          <p v-if="r.flags.old || r.flags.not_fasting" class="lr-flags">
            <span v-if="r.flags.old"><AlertTriangle :size="12" /> Older than 30 days. Consider repeating it.</span>
            <span v-if="r.flags.not_fasting"><AlertTriangle :size="12" /> Not a fasting sample. Don't compare it with the fasting glucose cut-offs.</span>
          </p>
        </div>
        <span class="nm-pill" :class="r.reviewed_at ? 'green' : 'gold'">{{ r.reviewed_at ? 'Accepted' : 'To review' }}</span>
        <button type="button" class="nm-btn-soft nm-btn-sm" @click="view(r)"><Eye :size="13" aria-hidden="true" /> {{ !r.reviewed_at ? 'Open to review' : 'View' }}</button>
      </div>

      <!-- declined uploads: kept for the record (what was sent and why it was
           declined), out of the way and greyed -->
      <details v-if="declinedResults.length" class="lr-declined-box">
        <summary>Declined uploads ({{ declinedResults.length }})</summary>
        <p class="lr-declined-note">These don't count as results. They're kept so you can see what {{ patientFirstName }} sent and why it was declined.</p>
        <div v-for="r in declinedResults" :key="r.id" class="lr-res declined">
          <span class="lr-icon"><FileText :size="17" /></span>
          <div class="lr-res-main">
            <p class="lr-res-title">{{ r.test_names.join(', ') }}</p>
            <p class="lr-res-meta">Taken {{ labDate(r.taken_on) }}. Uploaded {{ labDay(r.uploaded_at) }}, declined {{ labDay(r.declined_at) }}.</p>
            <p class="lr-declined">Reason: {{ r.decline_reason }}</p>
          </div>
          <span class="nm-pill muted">Declined</span>
          <button type="button" class="nm-btn-soft nm-btn-sm" @click="view(r)"><Eye :size="13" aria-hidden="true" /> View</button>
        </div>
      </details>
    </template>

    <RequestLabsModal
      v-if="requestOpen && data" :relationship-id="relationshipId" :patient-name="patientFirstName" :tests="data.tests"
      :next-consultation="data.next_consultation" @close="requestOpen = false" @sent="onSent"
    />
    <div v-if="toast" class="nm-toast" role="status">{{ toast }}</div>
      <LabFileModal
      v-if="viewing" :path="viewing.path" :title="viewing.title" :sub="viewing.sub" :file-name="viewing.fileName" :review-path="viewing.reviewPath"
      @close="viewing = null" @opened="onViewed" @reviewed="onReviewed"
    />
  </div>
</template>

<script setup>
import { AlertTriangle, Eye, FileText, FlaskConical } from 'lucide-vue-next'
import { FASTED_LABEL, consultGap, labDate, labDay, labDayTime } from '~/utils/labs'

const props = defineProps({
  relationshipId: { type: [String, Number], required: true },
  patientFirstName: { type: String, default: 'the patient' },
  canEdit: { type: Boolean, default: false },
  openRequest: { type: Boolean, default: false }, // open the request pop-up right away (header button)
})
const emit = defineEmits(['changed', 'autoOpened'])
const { get, del } = useApi()

const data = ref(null)
const loading = ref(true)
const error = ref('')
const requestOpen = ref(false)
const cancelling = ref(null)
const toast = ref('')

const validResults = computed(() => (data.value?.results || []).filter(r => !r.declined_at))
const declinedResults = computed(() => (data.value?.results || []).filter(r => r.declined_at))
const openRequests = computed(() => (data.value?.requests || []).filter(r => r.status === 'open'))

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    data.value = await get(`/rnd/relationships/${props.relationshipId}/labs/`)
    if (props.openRequest && !quiet) {
      if (data.value.can_request) requestOpen.value = true
      emit('autoOpened')
    }
  } catch {
    if (!quiet) error.value = 'Could not load lab results.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
useAutoRefresh(() => load({ quiet: true }))

function flash(msg) {
  toast.value = msg
  setTimeout(() => { toast.value = '' }, 3000)
}

async function onSent() {
  requestOpen.value = false
  flash('Lab request sent to the patient.')
  await load()
  emit('changed')
}

async function cancel(r) {
  cancelling.value = r.id
  try {
    await del(`/rnd/lab-requests/${r.id}/`)
    await load()
    emit('changed')
  } catch (e) {
    flash(e?.data?.detail || 'Could not cancel it.')
  } finally {
    cancelling.value = null
  }
}

// opens in a pop-up on the page; opening marks it reviewed, so refresh after
const viewing = ref(null)
function view(r) {
  const open = !r.reviewed_at && !r.declined_at
  viewing.value = { path: `/rnd/lab-results/${r.id}/file/`, title: r.test_names.join(', '), sub: `Taken ${labDate(r.taken_on)}, ${r.file_name}`, fileName: r.file_name,
                    reviewPath: open ? `/rnd/lab-results/${r.id}/review/` : '' }
}
function onViewed() {}
async function onReviewed(res) {
  flash(res.reviewed_at ? 'Accepted. It\'s now part of the record.' : 'Declined. The patient was asked to upload it again.')
  await load()
  emit('changed')
}

defineExpose({ openRequestForm: () => { requestOpen.value = true } })
</script>

<style scoped>
.nm-panel-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.nm-panel-head button { display: inline-flex; align-items: center; gap: 6px; }

/* open request = unfinished (same as an NCP draft): white card, dashed green border */
.lr-req { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border: 1.5px dashed #3f9a6b; background: #fff; border-radius: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.lr-req-main { flex: 1; min-width: 200px; }
.lr-req-title { font-weight: 700; font-size: 0.88rem; color: #1a3a1a; margin: 0; }
.lr-req-meta { font-size: 0.78rem; color: #6a7a6a; margin: 3px 0 0; }
.lr-req-note { font-size: 0.8rem; color: #4a5a4a; margin: 6px 0 0; padding-left: 10px; border-left: 2px solid #e3e9e4; overflow-wrap: anywhere; }

.lr-res { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.lr-icon { width: 36px; height: 36px; border-radius: 10px; background: #eef3ee; color: #2f6b4f; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.lr-res.new .lr-icon { background: #fdf1d6; color: #a37a0b; }
.lr-res-main { flex: 1; min-width: 200px; }
.lr-res-title { font-weight: 600; font-size: 0.88rem; color: #1a3a1a; margin: 0; }
.lr-res-meta { font-size: 0.76rem; color: #7a8a7a; margin: 2px 0 0; }
.lr-flags { display: flex; flex-direction: column; gap: 2px; margin: 5px 0 0; }
.lr-flags span { display: inline-flex; align-items: center; gap: 5px; font-size: 0.76rem; font-weight: 600; color: #a12525; }
.lr-res button { display: inline-flex; align-items: center; gap: 5px; }
@media (max-width: 600px) {
  .lr-res button, .lr-req button { flex: 1; justify-content: center; }
}
.lr-declined { font-size: 0.8rem; color: #6a7a6a; margin: 4px 0 0; overflow-wrap: anywhere; }
.lr-declined-box { margin-top: 14px; border-top: 1px solid #d9e3dc; padding-top: 10px; }
.lr-declined-box summary { cursor: pointer; font-size: 0.84rem; font-weight: 600; color: #4a5a4a; padding: 4px 0; }
.lr-declined-box summary:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.lr-declined-note { margin: 4px 0 6px; font-size: 0.78rem; color: #8a9a8a; }
.lr-res.declined { opacity: 0.75; }
</style>
