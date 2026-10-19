<template>
  <div>
    <div class="head">
      <div>
        <h3 class="nm-panel-title">Tasks & reminders for {{ clientFirstName }}</h3>
        <p class="nm-panel-sub">Medication cues and habit prompts. {{ clientFirstName }} gets each one as a notification (and by email if they turned that on). It shows on their My tasks list to tick off; only you can change or delete it.</p>
      </div>
      <button v-if="canEdit" class="nm-btn-dark" type="button" @click="openForm()"><Plus :size="15" /> Add reminder</button>
    </div>

    <p v-if="error" class="nm-error" style="margin-top: 14px">{{ error }}</p>
    <p v-if="loading" class="nm-muted" style="margin-top: 14px">Loading reminders…</p>
    <div v-else-if="!reminders.length" class="nm-empty">
      <AlarmClock :size="28" />
      <p>No reminders yet.</p>
      <p v-if="canEdit" class="nm-hint" style="margin-top: 4px">Consultation, payment and meal-logging reminders are already automatic — add medication or habit reminders here.</p>
    </div>
    <div v-else class="list">
      <div v-for="r in reminders" :key="r.id" class="rem" :class="{ off: !r.is_active || r.done }">
        <span class="rem-icon" :class="r.type"><component :is="r.type === 'medication' ? Pill : AlarmClock" :size="16" /></span>
        <div class="rem-main">
          <p class="rem-title">{{ r.title }}</p>
          <p class="rem-sub">
            {{ r.repeat_label }} at {{ clock(r.time_of_day) }}
            <template v-if="r.done"> · done</template>
            <template v-else-if="r.is_active"> · next {{ dayLabel(r.next_at) }}</template>
          </p>
          <p v-if="r.message" class="rem-msg">{{ r.message }}</p>
          <div class="rem-pills">
            <span class="nm-pill" :class="r.type === 'medication' ? 'gold' : 'muted'">{{ r.type_label }}</span>
            <span v-if="r.done" class="nm-pill muted">Finished</span>
            <span v-else-if="!r.is_active" class="nm-pill muted">Paused</span>
            <span v-if="r.done_today" class="nm-pill green">✓ Done today</span>
            <span v-if="r.last_sent_at" class="nm-pill blue">Last sent {{ dayLabel(r.last_sent_at) }}</span>
          </div>
        </div>
        <div v-if="canEdit" class="rem-actions">
          <button v-if="!r.done" class="nm-btn-outline nm-btn-sm" :disabled="busyId === r.id" @click="toggle(r)">
            <component :is="r.is_active ? Pause : Play" :size="13" /> {{ r.is_active ? 'Pause' : 'Resume' }}
          </button>
          <button class="nm-btn-outline nm-btn-sm" @click="openForm(r)"><Pencil :size="13" /> Edit</button>
          <button class="nm-btn-danger nm-btn-sm" :disabled="busyId === r.id" @click="confirmDelete = r"><Trash2 :size="13" /></button>
        </div>
      </div>
    </div>

    <!-- add / edit -->
    <div v-if="form" class="nm-modal-overlay" @click.self="saving ? null : (form = null)">
      <div class="nm-modal">
        <h3 class="nm-modal-title">{{ form.id ? 'Edit reminder' : `New reminder for ${clientFirstName}` }}</h3>
        <div v-if="!form.id" class="templates">
          <button v-for="t in TEMPLATES" :key="t.title" type="button" class="template" @click="useTemplate(t)">{{ t.title }}</button>
        </div>
        <label class="nm-label" for="rem-title">Title</label>
        <input id="rem-title" v-model="form.title" class="nm-input" maxlength="255" placeholder="e.g. Take metformin" />
        <label class="nm-label" for="rem-msg" style="margin-top: 12px">Message <span class="nm-muted">(optional)</span></label>
        <textarea id="rem-msg" v-model="form.message" class="nm-input" rows="2" maxlength="500" placeholder="e.g. 500 mg after breakfast, with water." />
        <div class="form-grid">
          <div>
            <label class="nm-label" for="rem-type">Kind</label>
            <select id="rem-type" v-model="form.type" class="nm-select full">
              <option value="medication">Medication</option>
              <option value="general">Habit / general</option>
            </select>
          </div>
          <div>
            <label class="nm-label" for="rem-repeat">Repeats</label>
            <select id="rem-repeat" v-model="form.repeat" class="nm-select full">
              <option value="once">Once</option>
              <option value="daily">Every day</option>
              <option value="weekdays">Weekdays (Mon–Fri)</option>
              <option value="weekly">Every week</option>
            </select>
          </div>
          <div>
            <label class="nm-label" for="rem-date">{{ form.repeat === 'once' ? 'Date' : 'Starting' }}</label>
            <input id="rem-date" v-model="form.date" type="date" class="nm-input" :min="todayIso" />
          </div>
          <div>
            <label class="nm-label" for="rem-time">Time</label>
            <input id="rem-time" v-model="form.time" type="time" class="nm-input" />
          </div>
        </div>
        <p class="nm-hint">Philippine time.<template v-if="form.repeat === 'weekly'"> Repeats on the same weekday as the start date.</template></p>
        <p v-if="formError" class="nm-field-error">{{ formError }}</p>
        <div class="nm-modal-actions">
          <button class="nm-btn-outline" :disabled="saving" @click="form = null">Cancel</button>
          <button class="nm-btn-dark" :disabled="saving" @click="save">{{ saving ? 'Saving…' : form.id ? 'Save changes' : 'Add reminder' }}</button>
        </div>
      </div>
    </div>

    <!-- delete -->
    <div v-if="confirmDelete" class="nm-modal-overlay" @click.self="confirmDelete = null">
      <div class="nm-modal">
        <h3 class="nm-modal-title">Delete "{{ confirmDelete.title }}"?</h3>
        <p class="nm-modal-text">{{ clientFirstName }} won't get it any more. To stop it for a while instead, use Pause.</p>
        <div class="nm-modal-actions">
          <button class="nm-btn-outline" @click="confirmDelete = null">Cancel</button>
          <button class="nm-btn-danger solid" :disabled="busyId === confirmDelete.id" @click="remove(confirmDelete)">Delete reminder</button>
        </div>
      </div>
    </div>

    <div v-if="toast" class="nm-toast"><CheckCircle2 :size="16" /> {{ toast }}</div>
  </div>
</template>

<script setup>
import { AlarmClock, CheckCircle2, Pause, Pencil, Pill, Play, Plus, Trash2 } from 'lucide-vue-next'

const props = defineProps({
  relationshipId: { type: [String, Number], required: true },
  clientName: { type: String, default: 'your client' },
  canEdit: { type: Boolean, default: true },
})

const { get, post, patch, del } = useApi()

const TEMPLATES = [
  { title: 'Take your medicine', type: 'medication', repeat: 'daily', time: '08:00', message: '' },
  { title: 'Drink a glass of water', type: 'general', repeat: 'daily', time: '10:00', message: 'Aim for 8 glasses today.' },
  { title: '30-minute walk', type: 'general', repeat: 'weekdays', time: '18:00', message: 'A brisk walk after dinner helps your blood sugar.' },
  { title: 'Check your blood sugar', type: 'medication', repeat: 'daily', time: '06:30', message: 'Before breakfast — note the result for your next consultation.' },
]

const clientFirstName = computed(() => (props.clientName || '').split(' ')[0] || 'your client')
const ph = d => new Date(d).toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' })
const todayIso = ph(new Date())

const reminders = ref([])
const loading = ref(true)
const error = ref('')
const busyId = ref(null)
const toast = ref('')
const form = ref(null)
const formError = ref('')
const saving = ref(false)
const confirmDelete = ref(null)

async function load() {
  try {
    reminders.value = await get(`/rnd/relationships/${props.relationshipId}/reminders/`)
  } catch {
    error.value = 'Could not load reminders. Please refresh.'
  } finally {
    loading.value = false
  }
}
onMounted(load)

function flash(text) {
  toast.value = text
  setTimeout(() => { toast.value = '' }, 3000)
}

function openForm(r = null) {
  formError.value = ''
  form.value = r
    ? { id: r.id, title: r.title, message: r.message || '', type: r.type, repeat: r.repeat, date: ph(r.next_at), time: r.time_of_day }
    : { title: '', message: '', type: 'medication', repeat: 'daily', date: todayIso, time: '08:00' }
}
function useTemplate(t) {
  Object.assign(form.value, { title: t.title, type: t.type, repeat: t.repeat, time: t.time, message: t.message })
}

async function save() {
  const f = form.value
  formError.value = ''
  if ((f.title || '').trim().length < 3) {
    formError.value = 'Give the reminder a short title.'
    return
  }
  if (!f.date || !f.time) {
    formError.value = 'Pick a date and time.'
    return
  }
  saving.value = true
  const body = { title: f.title.trim(), message: f.message.trim(), type: f.type, repeat: f.repeat, date: f.date, time: f.time }
  try {
    if (f.id) await patch(`/rnd/reminders/${f.id}/`, body)
    else await post(`/rnd/relationships/${props.relationshipId}/reminders/`, body)
    form.value = null
    await load()
    flash(f.id ? 'Reminder updated.' : `Reminder added — ${clientFirstName.value} was notified.`)
  } catch (e) {
    formError.value = apiError(e, 'Could not save this reminder. Please try again.')
  } finally {
    saving.value = false
  }
}

async function toggle(r) {
  busyId.value = r.id
  try {
    Object.assign(r, await patch(`/rnd/reminders/${r.id}/`, { is_active: !r.is_active }))
    flash(r.is_active ? 'Reminder resumed.' : 'Reminder paused.')
  } catch (e) {
    error.value = apiError(e, 'Could not update this reminder.')
  } finally {
    busyId.value = null
  }
}

async function remove(r) {
  busyId.value = r.id
  try {
    await del(`/rnd/reminders/${r.id}/`)
    reminders.value = reminders.value.filter(x => x.id !== r.id)
    confirmDelete.value = null
    flash('Reminder deleted.')
  } catch (e) {
    error.value = apiError(e, 'Could not delete this reminder.')
  } finally {
    busyId.value = null
  }
}

function clock(hhmm) {
  const [h, m] = String(hhmm || '00:00').split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}
function dayLabel(iso) {
  return iso ? new Date(iso).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'short', month: 'short', day: 'numeric' }) : ''
}
</script>

<style scoped>
.head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.head > div { flex: 1; min-width: 240px; }
.list { margin-top: 16px; display: flex; flex-direction: column; gap: 10px; }
.rem { display: flex; gap: 12px; align-items: flex-start; border: 1px solid #eceeec; border-radius: 12px; padding: 14px; flex-wrap: wrap; }
.rem.off { background: #fafbfa; }
.rem.off .rem-title { color: #6a7a6a; }
.rem-icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; background: #eef3ec; color: #1e4a26; }
.rem-icon.medication { background: #fdf1d6; color: #b8860b; }
.rem-main { flex: 1; min-width: 200px; }
.rem-title { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.rem-sub { font-size: 0.78rem; color: #6a7a6a; margin: 2px 0 0; }
.rem-msg { font-size: 0.82rem; color: #4a5a4a; margin: 6px 0 0; line-height: 1.45; overflow-wrap: anywhere; }
.rem-pills { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.rem-actions { display: flex; gap: 6px; align-items: center; }
.templates { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 14px; }
.template { background: #f7f9f7; border: 1px solid #e3e8e3; border-radius: 16px; padding: 6px 12px; font-size: 0.78rem; color: #2a3a2a; cursor: pointer; font-family: inherit; }
.template:hover { border-color: #1f8f5c; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
.full { width: 100%; }
@media (max-width: 640px) {
  .form-grid { grid-template-columns: 1fr; }
  .rem-actions { width: 100%; }
  .rem-actions > * { flex: 1; }
}
</style>
