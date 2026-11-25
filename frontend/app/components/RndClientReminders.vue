<template>
  <div>
    <div class="head">
      <div>
        <p class="rx-k"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10 21a2 2 0 0 0 4 0" /></svg>Tasks &amp; reminders</p>
        <h3 class="nm-panel-title">Reminders for {{ clientFirstName }}</h3>
        <p class="nm-panel-sub">Medication and habit reminders. {{ clientFirstName }} gets each one as a notification and ticks it off in My tasks. Only you can change them.</p>
      </div>
      <button v-if="canEdit" class="nm-btn-dark rx-add" type="button" @click="openForm()"><Plus :size="16" /> Add reminder</button>
    </div>
    <div v-if="!loading && reminders.length" class="rx-key">
      <span><i class="med" />Medication</span><span><i class="hab" />Habit</span>
      <span class="rx-count">{{ active.length }} active reminder{{ active.length === 1 ? '' : 's' }}</span>
    </div>

    <p v-if="error" class="nm-error" style="margin-top: 14px">{{ error }}</p>
    <p v-if="loading" class="nm-muted" style="margin-top: 14px">Loading reminders…</p>

    <!-- empty: say what's automatic; Add reminder is top right -->
    <div v-else-if="!reminders.length" class="empty">
      <p class="empty-title">No reminders yet</p>
      <p class="empty-text">Consultation, payment and meal-logging reminders already go out on their own. Add medication or habit reminders here.</p>
    </div>

    <!-- an agenda: one line per reminder, in time-of-day order -->
    <template v-else>
      <ol v-if="active.length" class="agenda">
        <li v-for="r in active" :key="r.id" class="ag-row">
          <span class="rx-ico" :class="['tone-' + reminderIcon(r).tone]" :title="reminderIcon(r).label"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="reminderIcon(r).svg" /></span>
          <div class="ag-main">
            <p class="ag-time"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ clock(r.time_of_day) }}</p>
            <p class="ag-title">{{ r.title }}<span class="rx-kind" :class="r.type === 'medication' ? 'med' : 'hab'">{{ kindLabel(r) }}</span></p>
            <p class="ag-sub"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12a8 8 0 0 1 14-5.3L20 9M20 4v5h-5M20 12a8 8 0 0 1-14 5.3L4 15M4 20v-5h5" /></svg>{{ r.repeat_label }}<template v-if="!r.done"><i aria-hidden="true" />Next {{ dayLabel(r.next_at) }}</template></p>
            <p v-if="r.message" class="ag-msg"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 4h16v12H8l-4 4z" /></svg><span>{{ r.message }}</span></p>
          </div>
          <div class="rx-side">
          <span class="ag-status" :class="{ done: r.done_today }">
            <template v-if="r.done_today"><Check :size="14" /> Done today</template>
            <template v-else-if="r.done">Finished</template>
            <template v-else>Not done yet today</template>
          </span>
          <div v-if="canEdit" class="ag-actions">
            <button class="rx-btn" :aria-label="`Edit ${r.title}`" title="Edit" @click="openForm(r)"><Pencil :size="15" /></button>
            <button v-if="!r.done" class="rx-btn" :disabled="busyId === r.id" :aria-label="`Pause ${r.title}`" title="Pause" @click="toggle(r)"><Pause :size="15" /></button>
            <button class="icon-del" :disabled="busyId === r.id" :aria-label="`Delete ${r.title}`" title="Delete" @click="confirmDelete = r"><Trash2 :size="15" /></button>
          </div>
          </div>
        </li>
      </ol>

      <section v-if="paused.length" class="paused">
        <h4 class="paused-title"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M10 9v6M14 9v6" /></svg>Paused</h4>
        <p class="paused-sub">{{ clientFirstName }} doesn't get these until you resume them.</p>
        <ol class="agenda">
          <li v-for="r in paused" :key="r.id" class="ag-row off">
            <span class="rx-ico off" :title="reminderIcon(r).label"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="reminderIcon(r).svg" /></span>
            <div class="ag-main">
              <p class="ag-time"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ clock(r.time_of_day) }}</p>
              <p class="ag-title">{{ r.title }}<span class="rx-kind off">{{ kindLabel(r) }}</span></p>
              <p class="ag-sub"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 12a8 8 0 0 1 14-5.3L20 9M20 4v5h-5M20 12a8 8 0 0 1-14 5.3L4 15M4 20v-5h5" /></svg>{{ r.repeat_label }}</p>
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
      <div class="nm-modal rf" role="dialog" aria-modal="true" aria-labelledby="rem-form-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="saving ? null : (form = null)"><X :size="18" aria-hidden="true" /></button>
        <header class="rf-h">
          <span class="rf-hi" :class="['tone-' + reminderIcon(form).tone]"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="reminderIcon(form).svg" /></span>
          <div class="rf-ht">
            <h3 id="rem-form-title" class="nm-modal-title">{{ form.id ? 'Edit reminder' : `New reminder for ${clientFirstName}` }}</h3>
            <p>{{ clientFirstName }} gets it as a notification at the time you set.</p>
          </div>
        </header>
        <div class="rf-b">
          <template v-if="!form.id">
            <p class="rf-lab">Quick start</p>
            <div class="templates">
              <button v-for="t in TEMPLATES" :key="t.title" type="button" class="template" :class="{ on: form.title === t.title }" @click="useTemplate(t)"><span class="tq" :class="['tone-' + reminderIcon(t).tone]"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="reminderIcon(t).svg" /></span>{{ t.title }}</button>
            </div>
          </template>
          <p class="rf-sec"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg>What to remind</p>
          <label class="nm-label" for="rem-title">Title</label>
          <input id="rem-title" v-model="form.title" class="nm-input" maxlength="255" autocomplete="off" placeholder="e.g. Take metformin" />
          <label class="nm-label" for="rem-msg">Message <span class="nm-muted">(optional)</span></label>
          <textarea id="rem-msg" v-model="form.message" class="nm-input" rows="2" maxlength="500" placeholder="e.g. 500 mg after breakfast, with water." />
          <p class="rf-sec"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>Schedule</p>
          <div class="form-grid">
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
              <label class="nm-label" for="rem-type">Type</label>
              <select id="rem-type" v-model="form.type" class="nm-select full">
                <option value="medication">Medication</option>
                <option value="general">Habit or general</option>
              </select>
            </div>
            <div>
              <label class="nm-label" for="rem-date">{{ form.repeat === 'once' ? 'Date' : 'Starting' }}</label>
              <DateField id="rem-date" v-model="form.date" :min="todayIso" placeholder="Select date" />
            </div>
            <div>
              <label class="nm-label" for="rem-time">Time</label>
              <input id="rem-time" v-model="form.time" type="time" class="nm-input" />
            </div>
          </div>
          <p class="nm-hint rf-hint"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" /></svg><span>Philippine time.<template v-if="form.repeat === 'weekly'"> Repeats on the same weekday as the start date.</template></span></p>
          <p v-if="formError" class="nm-field-error">{{ formError }}</p>
        </div>
        <div class="nm-modal-actions rf-f">
          <p v-if="form.time" class="rf-sum"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10 21a2 2 0 0 0 4 0" /></svg><span>{{ RF_REPEAT[form.repeat] || 'Once' }} at <b>{{ clock(form.time) }}</b></span></p>
          <button class="nm-btn-outline" :disabled="saving" @click="form = null">Cancel</button>
          <button class="nm-btn-dark" :disabled="saving" @click="save">{{ saving ? 'Saving…' : form.id ? 'Save changes' : 'Add reminder' }}</button>
        </div>
      </div>
    </div>

    <!-- delete -->
    <div v-if="confirmDelete" class="nm-modal-overlay" @click.self="confirmDelete = null">
      <div class="nm-modal" role="alertdialog" aria-modal="true" aria-label="Delete reminder">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="confirmDelete = null"><X :size="18" aria-hidden="true" /></button>
        <h3 class="nm-modal-title">Delete "{{ confirmDelete.title }}"?</h3>
        <p class="nm-modal-text">{{ clientFirstName }} won't get it any more. To stop it for a while instead, use Pause.</p>
        <div class="nm-modal-actions">
          <button class="nm-btn-outline" @click="confirmDelete = null">Cancel</button>
          <button class="nm-btn-danger solid" :disabled="busyId === confirmDelete.id" @click="remove(confirmDelete)">Delete reminder</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import { Check, CheckCircle2, Pause, Pencil, Play, Plus, Trash2, X } from 'lucide-vue-next'

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
const toast = useToast() // the app's toast (2026-11-03)
const form = ref(null)
const formError = ref('')
const saving = ref(false)
const confirmDelete = ref(null)

// active (and finished one-offs) by time of day; paused ones in their own list
const byTime = list => [...list].sort((x, y) => String(x.time_of_day).localeCompare(String(y.time_of_day)))
const active = computed(() => byTime(reminders.value.filter(r => r.is_active || r.done)))
const paused = computed(() => byTime(reminders.value.filter(r => !r.is_active && !r.done)))
const kindLabel = r => (r.type === 'medication' ? 'Medication' : 'Habit')

async function load({ quiet = false } = {}) {
  try {
    reminders.value = await get(`/rnd/relationships/${props.relationshipId}/reminders/`)
  } catch {
    if (!quiet) error.value = 'Could not load reminders. Please refresh.'
  } finally {
    loading.value = false
  }
}
onMounted(load)
// "Done today" ticks from the client show without a reload
useAutoRefresh(() => load({ quiet: true }))

function flash(text, opts) {
  toast.success(text, opts)
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
    toast.error(apiError(e, 'Could not update this reminder. Please try again.'))
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
    toast.error(apiError(e, 'Could not delete this reminder. Please try again.'))
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

// ---- UI helper only: pick an icon that matches what the reminder is about ----
const RX_ICONS = [
  { key: 'water', label: 'Water', tone: 'water', words: ['water', 'tubig', 'drink', 'hydrat', 'inom', 'glass'], svg: '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" /><path d="M9 14.5a3 3 0 0 0 3 3" />' },
  { key: 'sugar', label: 'Blood sugar', tone: 'blood', words: ['sugar', 'glucose', 'blood', 'cbg', 'fbs'], svg: '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z" /><path d="M12 11v6M9 14h6" />' },
  { key: 'bp', label: 'Blood pressure', tone: 'blood', words: ['pressure', ' bp', 'heart', 'pulse'], svg: '<path d="M20.8 5.6a5 5 0 0 0-7.1 0L12 7.3l-1.7-1.7a5 5 0 0 0-7.1 7.1L12 21.5l8.8-8.8a5 5 0 0 0 0-7.1z" /><path d="M3.5 12h4l2-3 3 6 2-3h6" />' },
  { key: 'insulin', label: 'Insulin', tone: 'med', words: ['insulin', 'inject', 'shot', 'syringe'], svg: '<path d="M18 2l4 4M17 7l3-3M19 9l-9.5 9.5H5.5v-4L15 5zM14 10l-3-3M11 13l-3-3M5.5 18.5 2 22" />' },
  { key: 'meal', label: 'Meal', tone: 'meal', words: ['meal', 'breakfast', 'lunch', 'dinner', 'snack', 'eat', 'kaon', 'pamahaw', 'paniudto', 'panihapon', 'food'], svg: '<path d="M4 3v8a2 2 0 0 0 2 2h1v8M8 3v6M6 3v6M16 21V3c-2 1-3 4-3 8h3" />' },
  { key: 'fruit', label: 'Fruits & vegetables', tone: 'hab', words: ['fruit', 'veg', 'gulay', 'prutas', 'salad', 'fiber'], svg: '<path d="M12 7c-3-2-8-1-8 5 0 5 3 9 6 9 1 0 1.4-.5 2-.5s1 .5 2 .5c3 0 6-4 6-9 0-6-5-7-8-5z" /><path d="M12 7c0-2 1-4 3-4" />' },
  { key: 'sleep', label: 'Sleep', tone: 'sleep', words: ['sleep', 'tulog', 'bed', 'rest', 'nap'], svg: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z" />' },
  { key: 'weight', label: 'Weight', tone: 'hab', words: ['weigh', 'timbang', 'scale', 'bmi'], svg: '<rect x="3" y="3" width="18" height="18" rx="4" /><path d="M8.5 9a5 5 0 0 1 7 0l-2.5 3" />' },
  { key: 'run', label: 'Exercise', tone: 'hab', words: ['exercise', 'workout', 'gym', 'run', 'jog', 'ehersisyo', 'stretch', 'yoga', 'bike', 'swim'], svg: '<path d="M6.5 6.5v11M17.5 6.5v11M3 9.5v5M21 9.5v5M6.5 12h11" />' },
  { key: 'walk', label: 'Walk', tone: 'hab', words: ['walk', 'lakaw', 'steps', 'stroll'], svg: '<circle cx="13" cy="4" r="2" /><path d="M7 22l3-7 3 2v6M10 9l4-2 2 4 3 1M9 15l-3-1 2-5 3-1" />' },
  { key: 'pill', label: 'Medicine', tone: 'med', words: ['medicine', 'tambal', 'pill', 'tablet', 'capsule', 'vitamin', 'metformin', 'take your', 'dose'], svg: '<path d="M10.5 20.5a5 5 0 0 1-7-7l6-6a5 5 0 0 1 7 7z" /><path d="M8.5 8.5l7 7" />' },
  { key: 'log', label: 'Log', tone: 'hab', words: ['log', 'record', 'journal', 'track', 'photo'], svg: '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" />' },
]
const RX_DEFAULT = {
  medication: { label: 'Medicine', tone: 'med', svg: '<path d="M10.5 20.5a5 5 0 0 1-7-7l6-6a5 5 0 0 1 7 7z" /><path d="M8.5 8.5l7 7" />' },
  habit: { label: 'Habit', tone: 'hab', svg: '<path d="M20 6 9 17l-5-5" />' },
}
function reminderIcon(r) {
  // title first, then the note, so "30-minute walk ... helps your blood sugar" stays a walk
  const find = t => RX_ICONS.find(i => i.words.some(w => ` ${t || ''}`.toLowerCase().includes(w)))
  return find(r?.title) || find(r?.message) || (r?.type === 'medication' ? RX_DEFAULT.medication : RX_DEFAULT.habit)
}

// ---- UI helper only: summary line in the reminder form ----
const RF_REPEAT = { once: 'Once', daily: 'Every day', weekdays: 'Weekdays', weekly: 'Every week' }
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
.templates { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 14px; }
/* quick starts: small filled light green buttons; the one in use turns green */
.template { display: inline-flex; align-items: center; min-height: 32px; padding: 0 12px; border: none; border-radius: 8px; background: #e3efe7; color: #0a4a37; font-size: 0.78rem; font-weight: 600; cursor: pointer; font-family: inherit; }
.template:hover { background: #d3e7da; }
.template.on { background: #0a4a37; color: #fff; }
.template:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
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

/* =========================================================
   UI refresh: timeline (icon + line), brand colours
   ========================================================= */
.ic { flex-shrink: 0; display: inline-block; }
.rx-k { display: flex; align-items: center; gap: 8px; margin: 0 0 4px; font-size: 12px; font-weight: 800; color: #9a7300; }
.head .nm-panel-title { font-size: 22px; }
.rx-add { display: inline-flex; align-items: center; gap: 8px; height: 44px; padding: 0 20px; border-radius: 12px; font-weight: 800; }
.rx-add :deep(svg) { color: #efbf04; }
.rx-key { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 16px; margin: 14px 0 4px; font-size: 13px; font-weight: 700; color: #3e5046; }
.rx-key span { display: inline-flex; align-items: center; gap: 6px; }
.rx-key i { width: 10px; height: 10px; border-radius: 50%; }
.rx-key i.med { background: #efbf04; } .rx-key i.hab { background: #1f7a4d; }
.rx-count { margin-left: auto; padding: 4px 12px; border-radius: 999px; background: #e3efe7; color: #004d3a; font-weight: 800; }
.agenda { margin: 10px 0 0; display: flex; flex-direction: column; gap: 4px; }
.ag-row { position: relative; display: grid; grid-template-columns: 44px minmax(0, 1fr) auto; align-items: start; gap: 16px; padding: 14px 14px 14px 0; border-top: none; border-radius: 16px; flex-wrap: nowrap; }
.ag-row:hover { background: #f7faf8; }
.ag-row:not(:last-child)::after { content: ''; position: absolute; left: 21px; top: 58px; bottom: -18px; width: 2px; background: #d3e0d8; }
.rx-ico { position: relative; z-index: 1; width: 44px; height: 44px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; border: 3px solid #fff; }
.rx-ico.med { background: #fbf3d2; color: #9a7300; }
.rx-ico.hab { background: #ddefe4; color: #1f7a4d; }
.rx-ico.off { background: #eef2ef; color: #8a9a91; }
.ag-main { min-width: 0; }
.ag-time { width: auto; display: inline-flex; align-items: center; gap: 5px; margin: 0 0 3px; padding: 0; font-family: inherit; font-size: 13px; font-weight: 800; color: #9a7300; }
.ag-title { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; font-size: 16px; font-weight: 800; color: #0e3a2c; }
.rx-kind { padding: 2px 9px; border-radius: 999px; font-size: 11.5px; font-weight: 800; }
.rx-kind.med { background: #fbf3d2; color: #8a6400; }
.rx-kind.hab { background: #e3f4ea; color: #1f7a4d; }
.rx-kind.off { background: #eef2ef; color: #6b7d73; }
.ag-sub { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin: 5px 0 0; font-size: 13px; font-weight: 600; color: #4a5a52; }
.ag-sub .ic { color: #1f7a4d; }
.ag-sub i { width: 4px; height: 4px; margin: 0 4px; border-radius: 50%; background: #b5c2ba; }
.ag-msg { display: flex; gap: 6px; margin: 8px 0 0; padding: 8px 12px; border-left: none; border-radius: 10px; background: #f3f7f4; font-size: 13px; color: #22362c; }
.ag-msg .ic { margin-top: 2px; color: #9a7300; }
.rx-side { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; align-self: center; }
.ag-status { padding: 3px 10px; border-radius: 999px; background: #fff; border: 1.5px dashed #c6d3cb; font-size: 12px; font-weight: 700; color: #4a5a52; }
.ag-status.done { border: none; background: #e3f4ea; color: #1f7a4d; }
.ag-actions { gap: 6px; align-self: center; }
.rx-btn { width: 36px; height: 36px; display: inline-flex; align-items: center; justify-content: center; border: 1.5px solid #d3e0d8; border-radius: 10px; background: #fff; color: #004d3a; cursor: pointer; }
.rx-btn:hover:not(:disabled) { background: #f1f8f4; border-color: #004d3a; }
.rx-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.rx-btn:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.icon-del { width: 36px; height: 36px; border: 1.5px solid #ebc2be; border-radius: 10px; color: #b4384a; }
.ag-row.off .ag-title { color: #6b7d73; }
.paused { margin-top: 20px; padding-top: 16px; border-top: 1.5px solid #eef2ef; }
.paused-title { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 800; color: #4a5a52; }
.paused-title .ic { color: #8a9a91; }
.paused-sub { margin-top: 4px; font-size: 13px; color: #6b7d73; }
.paused .ag-actions .nm-btn-sm { display: inline-flex; align-items: center; gap: 5px; height: 36px; border-radius: 10px; }
.empty { margin-top: 18px; padding: 26px; border: 1.5px dashed #c6d9cd; border-radius: 16px; text-align: center; }
.empty-title { font-size: 19px; color: #0e3a2c; }
.empty-text { margin: 0 auto; font-size: 14px; color: #4a5a52; }
.template { min-height: 34px; border-radius: 999px; font-size: 13px; font-weight: 700; }
.template.on { background: #004d3a; }
@media (max-width: 900px) {
  .ag-row { grid-template-columns: 44px minmax(0, 1fr); }
  .rx-side, .paused .ag-actions { grid-column: 2; flex-direction: row; align-items: center; justify-content: space-between; width: auto; }
}
@media (max-width: 640px) {
  .ag-row { gap: 12px; }
  .ag-status { width: auto; }
  .ag-actions { width: auto; }
  .rx-count { margin-left: 0; }
  .rx-add { width: 100%; justify-content: center; }
}

/* matching icon tones */
.rx-ico.tone-med { background: #fbf3d2; color: #9a7300; }
.rx-ico.tone-hab { background: #ddefe4; color: #1f7a4d; }
.rx-ico.tone-water { background: #dff0fb; color: #1f6fa8; }
.rx-ico.tone-blood { background: #fbe4e6; color: #b4384a; }
.rx-ico.tone-meal { background: #fdebd9; color: #b8621b; }
.rx-ico.tone-sleep { background: #e8e6f8; color: #5a4fa8; }

/* ===== New / edit reminder modal ===== */
.nm-modal.rf { width: min(560px, calc(100vw - 32px)); max-width: none; max-height: calc(100vh - 40px); padding: 0; display: flex; flex-direction: column; border-radius: 22px; overflow: hidden; }
.nm-modal.rf { position: relative; }
.nm-modal-overlay .nm-modal.rf .nm-modal-x { position: absolute !important; top: 20px !important; right: 20px !important; left: auto !important; margin: 0 !important; z-index: 2; width: 38px; height: 38px; display: inline-flex; align-items: center; justify-content: center; border: none; border-radius: 50%; background: #f1f5f2; color: #22362c; }
.nm-modal-overlay .nm-modal.rf .nm-modal-x:hover { background: #e3efe7; }
.rf-h { display: flex; align-items: flex-start; gap: 14px; padding: 24px 60px 18px 26px; border-bottom: 1px solid #eef2ef; background: linear-gradient(180deg, #f6faf7, #fff); }
.rf-hi { width: 46px; height: 46px; flex-shrink: 0; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 0 0 5px #f4f8f5; }
.rf-ht { min-width: 0; }
.rf-ht .nm-modal-title { margin: 2px 0 0; font-size: 23px; }
.rf-ht p { margin: 4px 0 0; font-size: 13.5px; color: #4a5a52; }
.rf-b { padding: 18px 26px 20px; overflow: auto; }
.rf-lab { margin: 0 0 8px; font-size: 12px; font-weight: 700; color: #6b7d73; }
.rf .templates { gap: 8px; margin: 0; }
.rf .template { gap: 7px; height: 34px; min-height: 34px; padding: 0 13px 0 5px; border: 1.5px solid #e1eae4; border-radius: 999px; background: #fff; color: #22362c; font-size: 13px; font-weight: 700; }
.rf .template:hover { border-color: #9cc3ae; background: #fff; }
.rf .template.on { border-color: #004d3a; background: #004d3a; color: #fff; }
.tq { width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; }
.rf-hi.tone-med, .tq.tone-med { background: #fbf3d2; color: #9a7300; }
.rf-hi.tone-hab, .tq.tone-hab { background: #ddefe4; color: #1f7a4d; }
.rf-hi.tone-water, .tq.tone-water { background: #dff0fb; color: #1f6fa8; }
.rf-hi.tone-blood, .tq.tone-blood { background: #fbe4e6; color: #b4384a; }
.rf-hi.tone-meal, .tq.tone-meal { background: #fdebd9; color: #b8621b; }
.rf-hi.tone-sleep, .tq.tone-sleep { background: #e8e6f8; color: #5a4fa8; }
.rf-sec { display: flex; align-items: center; gap: 8px; margin: 22px 0 2px; font-size: 11.5px; font-weight: 800; color: #9a7300; }
.rf-sec::after { content: ''; flex: 1; height: 1px; background: #eef2ef; }
.rf .nm-label { display: block; margin: 14px 0 6px; font-size: 13px; font-weight: 700; color: #22362c; }
.rf .nm-input, .rf .nm-select { min-height: 46px; border: 1.5px solid #dce5df; border-radius: 12px; font-size: 15px; color: #0e3a2c; }
.rf textarea.nm-input { min-height: 64px; font-size: 14px; }
.rf .nm-input:focus, .rf .nm-select:focus { border-color: #004d3a; box-shadow: 0 0 0 3px rgba(0, 77, 58, 0.1); outline: none; }
.rf .form-grid { margin-top: 0; column-gap: 12px; row-gap: 0; }
.rf-hint { display: flex; align-items: center; gap: 6px; margin-top: 10px; font-size: 12.5px; color: #6b7d73; }
.rf .nm-field-error { margin-top: 10px; }
.nm-modal-actions.rf-f { display: flex; align-items: center; gap: 10px; margin: 0; padding: 16px 26px; border-top: 1px solid #eef2ef; background: #fafcfb; }
.rf-sum { display: flex; align-items: center; gap: 8px; margin: 0 auto 0 0; font-size: 13.5px; color: #4a5a52; }
.rf-sum .ic { color: #9a7300; }
.rf-sum b { color: #0e3a2c; }
.rf-f .nm-btn-outline, .rf-f .nm-btn-dark { height: 44px; padding: 0 22px; border-radius: 12px; font-weight: 700; }
.rf-f .nm-btn-outline { border: none; background: #f1f5f2; color: #22362c; }
@media (max-width: 640px) {
  .nm-modal.rf { max-height: calc(100dvh - 20px); }
  .rf-h { padding: 18px 54px 14px 18px; }
  .rf-hi { width: 40px; height: 40px; }
  .rf-b { padding: 14px 18px 18px; }
  .nm-modal-actions.rf-f { flex-wrap: wrap; padding: 12px 18px; }
  .rf-sum { flex-basis: 100%; margin: 0 0 4px; }
  .rf-f .nm-btn-outline, .rf-f .nm-btn-dark { flex: 1; }
}
</style>