<template>
  <!-- Reschedule pop-up (2026-11-23), the booking pop-up's frame (RndProfileView.vue): a header, a
       scrolling body with the open times, and a footer that always shows what's picked + Send.
       Client: ask for a later time, paid or not; the RND confirms it (or, for a request still
       waiting for the RND, the time just changes). RND: offer a new time with a reason; the
       client accepts, picks another or {takes a refund / cancels}. Only later times are listed. -->
  <div class="nm-modal-overlay mv-overlay" @click.self="close">
    <div class="mv-box" role="dialog" aria-modal="true" aria-labelledby="move-title">
      <header class="mv-head">
        <div class="mv-head-text">
          <h2 id="move-title" class="mv-title">Reschedule with {{ otherFirstName }}</h2>
          <p class="mv-sub">
            <template v-if="counter">Pick a different time. {{ otherFirstName }} accepts it or answers with another.</template>
            <template v-else-if="role === 'rnd'">
              {{ otherFirstName }} accepts the new time, picks another, or {{ paid ? 'takes a full refund' : 'cancels' }}.
              <template v-if="paid">They don't pay again.</template>
            </template>
            <template v-else-if="status === 'pending'">{{ otherFirstName }} hasn't confirmed this request yet, so its time simply changes and they confirm it as usual.</template>
            <template v-else>{{ otherFirstName }} has to agree to the new time. Until then, and if they decline, it stays as booked.<template v-if="paid"> You don't pay again.</template></template>
            Times are Philippine time.
          </p>
        </div>
        <button class="mv-x" type="button" aria-label="Close" @click="close"><X :size="18" /></button>
      </header>

      <div class="mv-body">
        <p class="mv-now"><span>Now booked</span> {{ typeLabel }}, {{ bookedLabel }}</p>
        <RescheduleSlotPicker v-model="pick" :appointment-id="appointmentId"
                              :empty-hint="role === 'rnd' ? 'No later times are open. Add hours in Availability, or cancel the consultation.' : 'No later times are open. You can keep this time, or cancel it.'" />

        <section v-if="role === 'rnd' && late && !counter" class="mv-section">
          <p class="nm-note plain-note">It starts in under 30 minutes, so this counts as a last-minute cancel even if you move it. Pick why; you don't have to give details.</p>
          <label class="mv-h" for="move-cat">Why you can't make it</label>
          <select id="move-cat" v-model="category" class="nm-select block">
            <option value="" disabled>Choose a reason</option>
            <option value="emergency">Emergency (family or health)</option>
            <option value="technical">Technical problem</option>
            <option value="other">Other</option>
          </select>
        </section>
        <section v-if="role === 'rnd' || status !== 'pending'" class="mv-section">
          <label for="move-note" class="mv-h">
            {{ noteRequired ? (late && category !== 'other' ? 'Note to the client' : 'Reason, sent to the client') : role === 'rnd' ? 'Note to the client' : 'Note for your RND' }}
            <span v-if="!noteRequired || (late && category !== 'other')" class="optional">(optional)</span>
          </label>
          <textarea id="move-note" v-model="note" class="field-input" rows="2" maxlength="500" data-allow-emoji
                    :placeholder="role === 'rnd' ? 'For example, I have a hospital shift that morning.' : 'For example, work came up that day.'"></textarea>
          <p v-if="noteRequired && (!late || category === 'other')" class="mv-hint">At least 10 characters.</p>
        </section>
      </div>

      <footer class="mv-foot">
        <div class="mv-summary" aria-live="polite">
          <p v-if="pick" class="mv-pick">{{ typeLabel }}, {{ pickLabel }}</p>
          <p v-else class="mv-pick muted">Pick a green day, then a time.</p>
          <p v-if="error" class="mv-error" role="alert">{{ error }}</p>
          <p v-else class="mv-after">Only later times are open, up to 14 days after it was first booked.</p>
        </div>
        <button class="nm-btn-dark mv-send" type="button" :disabled="!ready || busy" @click="send">
          {{ busy ? 'Sending…' : role === 'client' && status === 'pending' ? 'Change time' : 'Send to ' + otherFirstName }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { X } from 'lucide-vue-next'
import { useToast } from '~/composables/useToast'

const props = defineProps({
  appointmentId: { type: [Number, String], required: true },
  role: { type: String, required: true }, // client | rnd
  otherFirstName: { type: String, required: true },
  status: { type: String, default: 'confirmed' }, // pending | confirmed (a pending request only changes its time)
  paid: { type: Boolean, default: false },
  late: { type: Boolean, default: false }, // RND: starts in under 30 minutes, so a category is needed
  counter: { type: Boolean, default: false }, // answering a time that is waiting with another one (action: propose)
  typeLabel: { type: String, default: 'Video call' },
  bookedLabel: { type: String, default: '' },
})
const emit = defineEmits(['close', 'done'])
const toast = useToast()
const { post } = useApi()

const pick = ref('')
const note = ref('')
const category = ref('')
const busy = ref(false)
const error = ref('')

const pickLabel = computed(() => (pick.value
  ? new Date(pick.value).toLocaleString('en-US', { timeZone: 'Asia/Manila', weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
  : ''))
// the RND gives a reason when they start the move (a category is enough in a last-minute one);
// the client's note, and any note on a counter-proposal, is optional
const noteRequired = computed(() => props.role === 'rnd' && !props.counter)
const ready = computed(() => {
  if (!pick.value) return false
  if (!noteRequired.value) return true
  if (props.late) return !!category.value && (category.value !== 'other' || note.value.trim().length >= 10)
  return note.value.trim().length >= 10
})

function close() {
  if (!busy.value) emit('close')
}
async function send() {
  busy.value = true
  error.value = ''
  const name = props.otherFirstName
  try {
    if (props.counter) {
      await post(`/${props.role === 'rnd' ? 'rnd' : 'client'}/appointments/${props.appointmentId}/reschedule/`, {
        action: 'propose', scheduled_at: pick.value, note: note.value.trim() || undefined,
      })
      toast.success('Time sent. You\'ll be told when they answer.', { id: `move-${props.appointmentId}` })
    } else if (props.role === 'rnd') {
      await post(`/rnd/appointments/${props.appointmentId}/reschedule/`, {
        action: 'offer', scheduled_at: pick.value, reason: note.value.trim(), category: props.late ? category.value : undefined,
      })
      toast.success(`New time sent. ${name} was told and can answer in My Appointments.`, { id: `move-${props.appointmentId}` })
    } else {
      const pending = props.status === 'pending'
      await post(`/client/appointments/${props.appointmentId}/reschedule/`, {
        action: pending ? 'change' : 'request', scheduled_at: pick.value, note: note.value.trim() || undefined,
      })
      toast.success(pending ? 'Time changed. Your RND confirms it as usual.' : `Request sent. RND ${name} confirms the new time.`, { id: `move-${props.appointmentId}` })
    }
    emit('done')
  } catch (e) {
    error.value = apiError(e, 'Could not send this. Please try again.')
  } finally {
    busy.value = false
  }
}
</script>

<style scoped>
/* the booking pop-up's frame (RndProfileView.vue .booking-modal-box), kept in step with it */
.mv-box {
  position: relative; background: #fff; border-radius: 18px; width: 100%; max-width: 620px; max-height: 92vh; max-height: 92dvh;
  display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22);
  font-family: 'Inter', sans-serif; color: #1a3a1a;
}
.mv-head { display: flex; align-items: flex-start; gap: 12px; padding: 24px 26px 16px; border-bottom: 1px solid #d9e3dc; }
.mv-head-text { flex: 1; min-width: 0; }
.mv-title { font-family: 'Playfair Display', serif; font-size: 1.35rem; font-weight: 700; color: #1a3a1a; margin: 0 0 6px; line-height: 1.2; }
.mv-sub { margin: 0; font-size: 0.84rem; color: #4a5a4a; line-height: 1.5; }
.mv-x { border: none; background: none; color: #6a7a6a; cursor: pointer; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.mv-x:hover { background: #f2f5f2; color: #1a3a1a; }
.mv-x:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.mv-body { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 18px 26px 6px; }
.mv-now { margin: 0 0 18px; padding: 10px 12px; border-radius: 10px; background: #f4f6f4; border: 1px solid #d9e3dc; font-size: 0.86rem; color: #1a3a1a; }
.mv-now span { font-weight: 600; color: #4a5a4a; margin-right: 6px; }
.mv-section { margin: 4px 0 18px; }
.mv-h { display: block; font-family: 'Playfair Display', serif; font-size: 1rem; font-weight: 700; color: #1a3a1a; margin: 0 0 10px; }
.mv-h .optional { font-family: 'Inter', sans-serif; font-weight: 400; font-size: 0.82rem; color: #6a7a6a; }
.mv-hint { margin: 4px 0 0; font-size: 0.78rem; color: #6a7a6a; }
.field-input { width: 100%; border: 1px solid #d9e3dc; border-radius: 8px; padding: 10px 12px; font-size: 0.86rem; font-family: inherit; color: #1a3a1a; resize: vertical; }
.field-input:focus { outline: none; border-color: #1f8f5c; box-shadow: 0 0 0 3px rgba(31, 143, 92, 0.15); }
.mv-foot { display: flex; align-items: center; gap: 12px 18px; padding: 14px 26px; border-top: 1px solid #d9e3dc; background: #f7faf8; }
.mv-summary { flex: 1; min-width: 0; }
.mv-pick { margin: 0; font-size: 0.92rem; font-weight: 700; color: #1a3a1a; }
.mv-pick.muted { font-weight: 600; color: #4a5a4a; }
.mv-after { margin: 2px 0 0; font-size: 0.78rem; color: #6a7a6a; }
.mv-error { margin: 4px 0 0; font-size: 0.8rem; color: #a12525; }
.mv-send { flex-shrink: 0; min-height: 40px; padding: 0 20px; }
@media (max-width: 640px) {
  .mv-overlay { padding: 0; align-items: stretch; }
  .mv-box { max-width: none; max-height: none; height: 100%; border-radius: 0; }
  .mv-head { padding: 18px 16px 14px; }
  .mv-body { padding: 16px 16px 4px; }
  .mv-foot { flex-direction: column; align-items: stretch; padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); }
  .mv-send { width: 100%; }
}
</style>
