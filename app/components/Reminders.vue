<template>
  <div class="reminders-page">
    <div class="panel">
      <div class="panel-header-row">
        <div class="panel-heading">
          <div class="panel-icon icon-gold"><AlarmClock :size="16" /></div>
          <div>
            <h3 class="panel-title">Active Reminders</h3>
            <p class="panel-sub">Stay on track with your care plan</p>
          </div>
        </div>
        <button class="primary-btn small" @click="openAddModal"><Plus :size="14" /> Add Reminder</button>
      </div>

      <div class="reminder-full-list">
        <div v-if="!activeReminders.length" class="empty-state">
          <AlarmClock :size="26" class="empty-icon" />
          <p>No reminders yet. Add one to get started.</p>
        </div>
        <div v-for="(r, i) in activeReminders" :key="r.label" class="reminder-full-item" :class="r.status === 'Active' ? 'accent-green' : 'accent-blue'">
          <div class="reminder-full-icon" :class="r.status === 'Active' ? 'icon-green' : 'icon-blue'"><AlarmClock :size="16" /></div>
          <div class="reminder-full-info">
            <p class="reminder-full-label">{{ r.label }}</p>
            <p class="reminder-full-schedule">{{ r.schedule }}</p>
          </div>
          <span class="status-pill" :class="r.status === 'Active' ? 'pill-green' : 'pill-blue'">{{ r.status }}</span>
          <button class="remove-btn" title="Remove reminder" @click="removeReminder(i)"><X :size="14" /></button>
        </div>
      </div>
    </div>

    <!-- ADD REMINDER MODAL -->
    <div v-if="modalOpen" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal-box">
        <div class="modal-title-row">
          <h3 class="modal-title">Add Reminder</h3>
          <button class="modal-close-btn" @click="closeAddModal"><X :size="18" /></button>
        </div>

        <label class="field-label">Reminder Label</label>
        <input v-model="form.label" type="text" placeholder="e.g. Meal Logging" class="modal-input" />

        <label class="field-label">Frequency</label>
        <div class="freq-row">
          <button
            v-for="f in frequencies" :key="f"
            class="freq-btn" :class="{ active: form.frequency === f }"
            @click="form.frequency = f"
          >{{ f }}</button>
        </div>

        <div class="modal-row-2">
          <div>
            <label class="field-label">Time</label>
            <input v-model="form.time" type="time" class="modal-input" />
          </div>
          <div v-if="form.frequency === 'One-time'">
            <label class="field-label">Date</label>
            <input v-model="form.date" type="date" class="modal-input" />
          </div>
        </div>

        <label class="field-label">Note <span class="optional">(optional)</span></label>
        <textarea v-model="form.note" rows="2" placeholder="Any extra detail for this reminder..."></textarea>

        <div class="modal-actions">
          <button class="ghost-btn" @click="closeAddModal">Cancel</button>
          <button class="primary-btn" :disabled="!canSave" @click="saveReminder">Save Reminder</button>
        </div>
      </div>
    </div>

    <!-- SAVE TOAST -->
    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle2 :size="16" /> {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { AlarmClock, Plus, X, CheckCircle2 } from 'lucide-vue-next'

// TODO: local mock data — move into the shared mock db (db.reminders)
// once the client-side data model is defined, and swap in a real API call.
const activeReminders = ref([
  { label: 'Meal Logging', schedule: 'Daily at 7:00 AM, 12:00 PM, 7:00 PM', status: 'Active' },
  { label: 'Fasting Blood Sugar Check', schedule: 'Daily at 6:30 AM', status: 'Active' },
  { label: 'Appointment Reminder — Jul 4', schedule: 'Jul 3 at 5:00 PM', status: 'Upcoming' }
])
function removeReminder(index) {
  // TODO: wire up to a real delete-reminder API call
  activeReminders.value.splice(index, 1)
}

const frequencies = ['Daily', 'Weekdays', 'Weekly', 'One-time']
const modalOpen = ref(false)
const form = reactive({ label: '', frequency: 'Daily', time: '', date: '', note: '' })

function openAddModal() {
  form.label = ''
  form.frequency = 'Daily'
  form.time = ''
  form.date = ''
  form.note = ''
  modalOpen.value = true
}
function closeAddModal() {
  modalOpen.value = false
}

const canSave = computed(() =>
  form.label.trim() !== '' && form.time !== '' && (form.frequency !== 'One-time' || form.date !== '')
)

function formatTime(t) {
  const [h, m] = t.split(':').map(Number)
  const period = h >= 12 ? 'PM' : 'AM'
  const hour12 = h % 12 === 0 ? 12 : h % 12
  return `${hour12}:${String(m).padStart(2, '0')} ${period}`
}

const toastVisible = ref(false)
const toastMessage = ref('')
let toastTimer = null
function fireToast(msg) {
  toastMessage.value = msg
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 3500)
}

function saveReminder() {
  if (!canSave.value) return
  const timeLabel = formatTime(form.time)
  let schedule = ''
  let status = 'Active'
  if (form.frequency === 'One-time') {
    const dateLabel = new Date(form.date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    schedule = `${dateLabel} at ${timeLabel}`
    status = 'Upcoming'
  } else {
    schedule = `${form.frequency} at ${timeLabel}`
  }
  if (form.note.trim()) schedule += ` — ${form.note.trim()}`

  // TODO: wire up to a real add-reminder API call
  activeReminders.value.unshift({ label: form.label.trim(), schedule, status })

  closeAddModal()
  fireToast('Reminder added!')
}
</script>

<style scoped>
* { box-sizing: border-box; }
.reminders-page { font-family: 'Inter', sans-serif; }

.panel { background: #fff; border-radius: 14px; border: 1px solid #eceeec; padding: 22px; }
.panel-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 30px; }
.panel-heading { display: flex; align-items: center; gap: 12px; }
.panel-icon { width: 34px; height: 34px; border-radius: 9px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.icon-green { background: #e3f3ea; color: #1f8f5c; }
.icon-gold { background: #fdf1d6; color: #b8860b; }
.icon-blue { background: #e3ecf7; color: #2a5a8a; }
.panel-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0; }
.panel-sub { font-size: 0.78rem; color: #9aaa9a; margin: 2px 0 0; }

.primary-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 11px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }
.primary-btn.small { display: inline-flex; align-items: center; gap: 6px; padding: 8px 14px; font-size: 0.8rem; flex-shrink: 0; }
.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.empty-state { padding: 30px; text-align: center; color: #9aaa9a; font-size: 0.85rem; }
.empty-icon { color: #d5dad5; margin-bottom: 8px; }

.reminder-full-list { display: flex; flex-direction: column; gap: 25px; }
.reminder-full-item {
  display: flex; align-items: center; gap: 15px; padding: 14px 16px; border-radius: 10px;
  border-left: 3px solid #D4A017; background: #f7f9f7; transition: background 0.15s;
}
.reminder-full-item:hover { background: #f0f2f0; }
.reminder-full-item.accent-blue { border-left-color: #2a5a8a; }
.reminder-full-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.reminder-full-info { flex: 1; }
.reminder-full-label { font-size: 0.86rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.reminder-full-schedule { font-size: 0.76rem; color: #9aaa9a; margin: 2px 0 0; }
.remove-btn { border: none; background: none; color: #b5bdb5; cursor: pointer; padding: 4px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.remove-btn:hover { color: #c0392b; }

.status-pill { font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; white-space: nowrap; flex-shrink: 0; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }
.pill-gold { background: #fdf1d6; color: #b8860b; }
.pill-blue { background: #e3ecf7; color: #2a5a8a; }

/* ADD REMINDER MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(20,30,20,0.45); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 16px; }
.modal-box { background: #fff; border-radius: 14px; padding: 26px; width: 100%; max-width: 420px; }
.modal-title-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 18px; }
.modal-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0; }
.modal-close-btn { border: none; background: none; color: #9aaa9a; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 2px; flex-shrink: 0; }

.field-label { display: block; font-size: 0.78rem; font-weight: 700; color: #4a5a4a; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.04em; }
.optional { font-weight: 400; text-transform: none; color: #9aaa9a; }
.modal-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #2a2a2a; margin-bottom: 16px;
}
.modal-box textarea {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #2a2a2a; resize: vertical; margin-bottom: 20px;
}

.freq-row { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.freq-btn { flex: 1; border: 1.5px solid #d5dad5; background: #fff; color: #6a7a6a; border-radius: 8px; padding: 9px 8px; font-size: 0.78rem; font-weight: 600; cursor: pointer; white-space: nowrap; }
.freq-btn.active { border-color: #14301a; background: #14301a; color: #fff; }

.modal-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }
.ghost-btn { background: none; border: 1px solid #d5dad5; color: #4a5a4a; font-weight: 600; font-size: 0.85rem; cursor: pointer; padding: 10px 18px; border-radius: 8px; }

/* TOAST */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }
</style>