<template>
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="!saving && emit('close')">
      <form class="nm-modal lu-modal" role="dialog" aria-modal="true" aria-labelledby="lu-title" @submit.prevent="submit">
        <div class="lu-head">
          <h3 id="lu-title" class="nm-modal-title">{{ replace ? 'Replace lab result' : 'Upload lab results' }}</h3>
          <button type="button" class="lu-x" aria-label="Close" :disabled="saving" @click="emit('close')"><X :size="18" /></button>
        </div>
        <p class="nm-modal-text">Your RND sees it as soon as it's uploaded. Only you and your RND can open it.</p>

        <!-- files -->
        <p class="nm-label">File{{ files.length > 1 ? 's' : '' }}</p>
        <ul v-if="files.length" class="lu-files">
          <li v-for="(f, i) in files" :key="i">
            <FileText :size="15" />
            <span class="lu-name">{{ f.name }}</span>
            <span class="lu-size">{{ fileSize(f.size) }}</span>
            <button type="button" class="lu-remove" :aria-label="`Remove ${f.name}`" @click="files.splice(i, 1)"><X :size="14" /></button>
          </li>
        </ul>
        <label v-if="!replace && files.length < LAB_MAX_FILES" class="lu-add">
          <input type="file" :accept="LAB_ACCEPT" multiple class="sr-only" @change="addFiles" />
          <Plus :size="14" /> {{ files.length ? 'Add another file' : 'Browse files' }}
        </label>
        <label v-else-if="replace && !files.length" class="lu-add">
          <input type="file" :accept="LAB_ACCEPT" class="sr-only" @change="addFiles" />
          <Plus :size="14" /> Browse files
        </label>
        <p class="nm-hint">PDF · JPG · PNG — up to {{ LAB_MAX_MB }} MB each{{ replace ? '' : `, ${LAB_MAX_FILES} files at a time` }}.</p>

        <!-- request -->
        <template v-if="requests.length && !replace">
          <label class="nm-label" for="lu-req">Which request is this for?</label>
          <select id="lu-req" v-model="requestId" class="nm-select block">
            <option v-for="r in requests" :key="r.id" :value="r.id">{{ r.test_names.join(', ') }} · requested {{ labDay(r.created_at) }}</option>
            <option :value="null">Not for a request (results I already have)</option>
          </select>
        </template>

        <!-- tests -->
        <fieldset class="lu-fieldset">
          <legend class="nm-label">Which tests are in {{ files.length > 1 ? 'these files' : 'this file' }}?</legend>
          <div class="lu-tests">
            <label v-for="t in tests" :key="t.code" class="lu-check">
              <input v-model="picked" type="checkbox" :value="t.code" /> {{ t.name }}
            </label>
          </div>
          <input v-if="picked.includes('other')" v-model="other" class="nm-input" maxlength="200" placeholder="Name of the other test" aria-label="Other test" />
          <p v-if="errors.tests" class="nm-field-error">{{ errors.tests }}</p>
        </fieldset>

        <!-- date + fasting -->
        <label class="nm-label" for="lu-date">Date the test was taken</label>
        <input id="lu-date" v-model="takenOn" type="date" class="nm-input" :max="today" required />
        <p v-if="errors.taken_on" class="nm-field-error">{{ errors.taken_on }}</p>

        <fieldset v-if="picked.includes('fbs')" class="lu-fieldset">
          <legend class="nm-label">Did you fast for 8+ hours before the glucose test?</legend>
          <div class="lu-radios">
            <label class="lu-check"><input v-model="fasted" type="radio" value="yes" /> Yes</label>
            <label class="lu-check"><input v-model="fasted" type="radio" value="no" /> No</label>
          </div>
          <p v-if="errors.fasted" class="nm-field-error">{{ errors.fasted }}</p>
        </fieldset>

        <p v-if="error" class="nm-error" role="alert">{{ error }}</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-outline" :disabled="saving" @click="emit('close')">Cancel</button>
          <button type="submit" class="nm-btn-dark" :disabled="saving">{{ saving ? 'Uploading…' : 'Upload' }}</button>
        </div>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { FileText, Plus, X } from 'lucide-vue-next'
import { LAB_ACCEPT, LAB_MAX_FILES, LAB_MAX_MB, fileSize, labDay, labFilesError, splitLabFiles } from '~/utils/labs'

// Upload pop-up (POST /api/client/labs/, multipart). Opened from the
// dashboard card or the Lab Results page with the file(s) already chosen.
// `replace`: an unreviewed result to delete once the new one is uploaded.
const props = defineProps({
  tests: { type: Array, required: true },
  requests: { type: Array, default: () => [] },
  initialFiles: { type: Array, default: () => [] },
  presetRequestId: { type: Number, default: null },
  replace: { type: Object, default: null },
})
const emit = defineEmits(['close', 'uploaded'])
const { post, del } = useApi()

const today = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' })
const files = ref([...props.initialFiles])
const requestId = ref(props.replace ? props.replace.request_id : (props.presetRequestId ?? props.requests[0]?.id ?? null))
const picked = ref([])
const other = ref('')
const takenOn = ref(props.replace?.taken_on || today)
const fasted = ref(props.replace?.fasted && props.replace.fasted !== 'na' ? props.replace.fasted : '')
const errors = ref({})
const error = ref('')
const saving = ref(false)

// Pre-tick the tests from the request (the ones not uploaded yet), or the replaced result's.
function pickFromRequest() {
  if (props.replace) {
    picked.value = [...props.replace.tests]
    other.value = props.replace.other_tests || ''
    return
  }
  const r = props.requests.find(x => x.id === requestId.value)
  if (!r) return
  const left = r.tests.filter(t => !r.uploaded_tests.includes(t))
  picked.value = left.length ? left : [...r.tests]
  other.value = r.other_tests || ''
}
pickFromRequest()
watch(requestId, pickFromRequest)

async function addFiles(e) {
  const chosen = Array.from(e.target.files || [])
  e.target.value = ''
  const room = props.replace ? 1 - files.value.length : LAB_MAX_FILES - files.value.length
  const { ok, error: left } = await splitLabFiles(chosen, room)
  files.value.push(...ok)
  error.value = left
}

async function submit() {
  errors.value = {}
  error.value = labFilesError(files.value)
  if (!picked.value.length) errors.value.tests = 'Tick at least one test.'
  else if (picked.value.includes('other') && !other.value.trim()) errors.value.tests = 'Type the other test\'s name.'
  if (!takenOn.value) errors.value.taken_on = 'Enter the date the test was taken.'
  else if (takenOn.value > today) errors.value.taken_on = 'The test date can\'t be in the future.'
  if (picked.value.includes('fbs') && !fasted.value) errors.value.fasted = 'Choose yes or no.'
  if (error.value || Object.keys(errors.value).length) return

  const fd = new FormData()
  files.value.forEach(f => fd.append('files', f))
  fd.append('tests', JSON.stringify(picked.value))
  fd.append('other_tests', picked.value.includes('other') ? other.value.trim() : '')
  fd.append('taken_on', takenOn.value)
  fd.append('fasted', picked.value.includes('fbs') ? fasted.value : 'na')
  if (requestId.value) fd.append('request_id', requestId.value)

  saving.value = true
  try {
    const res = await post('/client/labs/', fd)
    if (props.replace) await del(`/client/lab-results/${props.replace.id}/`).catch(() => {})
    emit('uploaded', res.results)
  } catch (e) {
    const d = e?.data || {}
    for (const k of ['tests', 'other_tests', 'taken_on', 'fasted']) {
      if (d[k]) errors.value[k === 'other_tests' ? 'tests' : k] = [].concat(d[k])[0]
    }
    const general = d.files || d.request_id || d.detail
    error.value = general ? [].concat(general)[0] : (Object.keys(errors.value).length ? '' : 'Could not upload. Please try again.')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.lu-modal { max-width: 520px; }
.lu-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.lu-x { border: none; background: none; color: #8a9a8a; cursor: pointer; padding: 2px; display: flex; }
.lu-x:hover { color: #1a3a1a; }
.lu-files { list-style: none; margin: 0 0 8px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.lu-files li { display: flex; align-items: center; gap: 8px; padding: 8px 10px; border: 1px solid #e3e8e3; border-radius: 8px; font-size: 0.84rem; color: #1a3a1a; }
.lu-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.lu-size { font-size: 0.74rem; color: #8a9a8a; }
.lu-remove { border: none; background: none; color: #9aaa9a; cursor: pointer; display: flex; padding: 2px; }
.lu-remove:hover { color: #c0392b; }
.lu-add { display: inline-flex; align-items: center; gap: 6px; font-size: 0.82rem; font-weight: 600; color: #00382a; border: 1px dashed #9fb8a8; border-radius: 8px; padding: 8px 12px; cursor: pointer; background: #f4f8f5; }
.lu-add:hover { background: #eaf2ec; }
.lu-add:focus-within { outline: 2px solid #D4A017; outline-offset: 2px; }
.nm-hint { margin: 6px 0 14px; }
.nm-select.block { margin-bottom: 14px; }
.lu-fieldset { border: none; padding: 0; margin: 0 0 14px; }
.lu-tests { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 12px; margin-bottom: 8px; }
.lu-radios { display: flex; gap: 18px; }
.lu-check { display: flex; align-items: center; gap: 8px; font-size: 0.84rem; color: #2a3a2a; cursor: pointer; }
.lu-check input { accent-color: #00382a; width: 16px; height: 16px; }
#lu-date { margin-bottom: 14px; }
.nm-field-error { margin-top: 4px; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); border: 0; }
@media (max-width: 480px) { .lu-tests { grid-template-columns: minmax(0, 1fr); } }
</style>
