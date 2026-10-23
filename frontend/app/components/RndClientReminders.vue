<template>
  <div>
    <div class="head">
      <div>
        <h3 class="nm-panel-title">Tasks and reminders for {{ clientFirstName }}</h3>
        <p class="nm-panel-sub">Medication and habit reminders. {{ clientFirstName }} gets each one as a notification and ticks it off in My tasks. Only you can change them.</p>
      </div>
      <button v-if="canEdit && reminders.length" class="nm-btn-dark" type="button" @click="openForm()"><Plus :size="15" /> Add reminder</button>
    </div>

    <p v-if="error" class="nm-error" style="margin-top: 14px">{{ error }}</p>
    <p v-if="loading" class="nm-muted" style="margin-top: 14px">Loading reminders…</p>

    <!-- empty: say what's automatic, offer a start -->
    <div v-else-if="!reminders.length" class="empty">
      <p class="empty-title">No reminders yet</p>
      <p class="empty-text">Consultation, payment and meal-logging reminders already go out on their own. Add medication or habit reminders here.</p>
      <div v-if="canEdit" class="starters">
        <button v-for="t in TEMPLATES" :key="t.title" type="button" class="starter" @click="openForm(); useTemplate(t)">{{ t.title }}</button>
        <button type="button" class="nm-btn-dark nm-btn-sm" @click="openForm()"><Plus :size="14" /> Write your own</button>
      </div>
    </div>

    <!-- an agenda: one line per reminder, in time-of-day order -->
    <template v-else>
      <ol v-if="active.length" class="agenda">
        <li v-for="r in active" :key="r.id" class="ag-row">
          <span class="ag-time">{{ clock(r.time_of_day) }}</span>
          <div class="ag-main">
            <p class="ag-title">{{ r.title }}</p>
            <p class="ag-sub">{{ kindLabel(r) }}, {{ r.repeat_label.toLowerCase() }}<template v-if="!r.done">. Next {{ dayLabel(r.next_at) }}</template></p>
            <p v-if="r.message" class="ag-msg">{{ r.message }}</p>
          </div>
          <span class="ag-status" :class="{ done: r.done_today }">
            <template v-if="r.done_today"><Check :size="14" /> Done today</template>
            <template v-else-if="r.done">Finished</template>
            <template v-else>Not done yet today</template>
          </span>
          <div v-if="canEdit" class="ag-actions">
            <button class="nm-btn-outline nm-btn-sm" @click="openForm(r)"><Pencil :size="13" /> Edit</button>
            <button v-if="!r.done" class="nm-btn-outline nm-btn-sm" :disabled="busyId === r.id" @click="toggle(r)"><Pause :size="13" /> Pause</button>
            <button class="icon-del" :disabled="busyId === r.id" :aria-label="`Delete ${r.title}`" @click="confirmDelete = r"><Trash2 :size="14" /></button>
          </div>
        </li>
      </ol>

      <section v-if="paused.length" class="paused">
        <h4 class="paused-title">Paused</h4>
        <p class="paused-sub">{{ clientFirstName }} doesn't get these until you resume them.</p>
        <ol class="agenda">
          <li v-for="r in paused" :key="r.id" class="ag-row off">
            <span class="ag-time">{{ clock(r.time_of_day) }}</span>
            <div class="ag-main">
              <p class="ag-title">{{ r.title }}</p>
              <p class="ag-sub">{{ kindLabel(r) }}, {{ r.repeat_label.toLowerCase() }}</p>
            </div>
            <div v-if="canEdit" class="ag-actions">
              <button class="nm-btn-outline nm-btn-sm" :disabled="busyId === r.id" @click="toggle(r)"><Play :size="13" /> Resume</button>
              <button class="icon-del" :disabled="busyId === r.id" :aria-label="`Delete ${r.title}`" @click="confirmDelete = r"><Trash2 :size="14" /></button>
            </div>
          </li>
        </ol>
      </section>
    </template>

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
            <label class="nm-label" for="rem-type">Type</label>
            <select id="rem-type" v-model="form.type" class="nm-select full">
              <option value="medication">Medication</option>
              <option value="general">Habit or general</option>
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
import { Check, CheckCircle2, Pause, Pencil, Play, Plus, Trash2 } from 'lucide-vue-next'

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
  { title: 'Check your blood sugar', type: 'medication', repeat: 'daily', time: '06:30', message: 'Before breakfast. Note the result for your next consultation.' },
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

// active (and finished one-offs) by time of day; paused ones in their own list
const byTime = list => [...list].sort((x, y) => String(x.time_of_day).localeCompare(String(y.time_of_day)))
const active = computed(() => byTime(reminders.value.filter(r => r.is_active || r.done)))
const paused = computed(() => byTime(reminders.value.filter(r => !r.is_active && !r.done)))
const kindLabel = r => (r.type === 'medication' ? 'Medication' : 'Habit')

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
    flash(f.id ? 'Reminder updated.' : `Reminder added. ${clientFirstName.value} was notified.`)
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
/* agenda */
.agenda { list-style: none; margin: 16px 0 0; padding: 0; }
.ag-row { display: flex; align-items: flex-start; gap: 16px; padding: 14px 0; border-top: 1px solid #f0f2f0; flex-wrap: wrap; }
.ag-row:first-child { border-top: none; }
.ag-time { width: 78px; flex-shrink: 0; font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; color: #1a3a1a; font-variant-numeric: tabular-nums lining-nums; white-space: nowrap; padding-top: 1px; }
.ag-main { flex: 1; min-width: 200px; }
.ag-title { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0; overflow-wrap: anywhere; }
.ag-sub { font-size: 0.8rem; color: #6a7a6a; margin: 2px 0 0; }
.ag-msg { font-size: 0.82rem; color: #4a5a4a; margin: 6px 0 0; padding-left: 10px; border-left: 2px solid #e3e9e4; line-height: 1.45; overflow-wrap: anywhere; }
.ag-status { flex-shrink: 0; display: inline-flex; align-items: center; gap: 4px; font-size: 0.8rem; color: #8a9a8a; padding-top: 2px; white-space: nowrap; }
.ag-status.done { color: #1f7a4d; font-weight: 600; }
.ag-actions { display: flex; gap: 6px; align-items: center; }
.icon-del { width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; border: 1px solid #f0d0cc; border-radius: 8px; background: #fff; color: #b23b2e; cursor: pointer; }
.icon-del:hover { background: #fdf0ee; }
.icon-del:focus-visible { outline: 2px solid #b23b2e; outline-offset: 2px; }
.ag-row.off .ag-time, .ag-row.off .ag-title { color: #7a8a7a; }
.paused { margin-top: 18px; padding-top: 14px; border-top: 1px solid #eef1ee; }
.paused-title { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.paused-sub { font-size: 0.8rem; color: #7a8a7a; margin: 2px 0 0; }
.paused .agenda { margin-top: 6px; }
/* empty */
.empty { margin-top: 18px; }
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.empty-text { font-size: 0.86rem; color: #5a6a5a; margin: 0; max-width: 60ch; line-height: 1.5; }
.starters { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-top: 14px; }
.starter { background: #fff; border: 1px solid #d5dad5; border-radius: 16px; padding: 6px 12px; font-size: 0.8rem; color: #1a3a1a; cursor: pointer; font-family: inherit; }
.starter:hover { border-color: #1f8f5c; }
.templates { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 14px; }
.template { background: #f7f9f7; border: 1px solid #e3e8e3; border-radius: 16px; padding: 6px 12px; font-size: 0.78rem; color: #2a3a2a; cursor: pointer; font-family: inherit; }
.template:hover { border-color: #1f8f5c; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
.full { width: 100%; }
@media (max-width: 640px) {
  .form-grid { grid-template-columns: 1fr; }
  .ag-time { width: auto; }
  .ag-row { gap: 8px 14px; }
  .ag-status { width: 100%; padding-top: 0; }
  .ag-actions { width: 100%; }
  .ag-actions > .nm-btn-sm { flex: 1; justify-content: center; }
}
</style>
