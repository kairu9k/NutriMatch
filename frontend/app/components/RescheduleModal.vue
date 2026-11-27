<template>
  <!-- Reschedule pop-up (2026-11-23), the booking pop-up's frame (RndProfileView.vue): a header, a
       scrolling body with the open times, and a footer that always shows what's picked + Send.
       Client: ask for a later time, paid or not; the RND confirms it (or, for a request still
       waiting for the RND, the time just changes). RND: offer a new time with a reason; the
       client accepts, picks another or {takes a refund / cancels}. Only later times are listed. -->
  <div class="nm-modal-overlay mv-overlay" @click.self="close">
    <div class="mv-box" role="dialog" aria-modal="true" aria-labelledby="move-title">
      <header class="mv-head">
        <span class="mv-badge" aria-hidden="true"><CalendarClock :size="28" /></span>
        <div class="mv-head-text">
          <h2 id="move-title" class="mv-title">Reschedule with {{ otherFirstName }}</h2>
          <p class="mv-sub">
            <template v-if="counter">Pick a different time. {{ otherFirstName }} accepts it or answers with another.</template>
            <template v-else-if="role === 'rnd' && status === 'pending'">
              Suggest another time for {{ otherFirstName }}'s request. If they accept it, the consultation is confirmed at that time.
              If they keep theirs or don't answer, the request stays and you can still confirm or decline it.
            </template>
            <template v-else-if="role === 'rnd'">
              {{ otherFirstName }} accepts the new time, picks another, or {{ paid ? 'takes a full refund' : 'cancels' }}.
              <template v-if="paid">They don't pay again.</template>
            </template>
            <template v-else-if="status === 'pending'">{{ otherFirstName }} hasn't confirmed this request yet, so its time simply changes and they confirm it as usual.</template>
            <template v-else>{{ otherFirstName }} has to agree to the new time. Until then, and if they decline, it stays as booked.<template v-if="paid"> You don't pay again.</template></template>
            Times are Philippine time.
          </p>
        </div>
        <button class="mv-x" type="button" aria-label="Close" @click="close"><X :size="24" /></button>
      </header>

      <div class="mv-body">
        <RescheduleSlotPicker v-model="pick" :appointment-id="appointmentId"
                              :empty-hint="role === 'rnd' ? 'No later times are open. Add hours in Availability, or cancel the consultation.' : 'No later times are open. You can keep this time, or cancel it.'">
          <template #left-top>
            <p class="mv-now"><CalendarDays :size="18" aria-hidden="true" /><span>{{ status === 'pending' ? 'Requested' : 'Now booked' }}</span> {{ typeLabel }}, {{ bookedLabel }}</p>
          </template>

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
              <FileText :size="18" aria-hidden="true" />
              {{ noteRequired ? (late && category !== 'other' ? 'Note to the client' : 'Reason, sent to the client') : role === 'rnd' ? 'Note to the client' : 'Note for your RND' }}
              <span v-if="!noteRequired || (late && category !== 'other')" class="optional">(optional)</span>
            </label>
            <textarea id="move-note" v-model="note" class="mv-input" rows="2" maxlength="500" data-allow-emoji
                      :placeholder="role === 'rnd' ? 'For example, I have a hospital shift that morning.' : 'For example, work came up that day.'"></textarea>
            <p v-if="noteRequired && (!late || category === 'other')" class="mv-hint">At least 10 characters.</p>
          </section>
        </RescheduleSlotPicker>
      </div>

      <footer class="mv-foot">
        <div class="mv-sumbox">
          <span class="mv-sum-ico" :class="{ ready: pick }" aria-hidden="true"><CalendarCheck v-if="pick" :size="22" /><Info v-else :size="22" /></span>
          <div class="mv-summary" aria-live="polite">
            <p v-if="pick" class="mv-pick">{{ typeLabel }}, {{ pickLabel }}</p>
            <p v-else class="mv-pick muted">Pick a time.</p>
            <p v-if="error" class="mv-error" role="alert">{{ error }}</p>
            <p v-else class="mv-after">Only later times are open, up to 14 days after it was first booked.</p>
          </div>
        </div>
        <button class="nm-btn-dark mv-send" type="button" :disabled="!ready || busy" @click="send">
          <CalendarCheck :size="18" aria-hidden="true" />
          {{ busy ? 'Sending…' : role === 'client' && status === 'pending' ? 'Change time' : 'Send to ' + otherFirstName }}
        </button>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { CalendarCheck, CalendarClock, CalendarDays, FileText, Info, X } from 'lucide-vue-next'
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
// (a time suggested on a request the RND hasn't confirmed only needs an optional note)
const noteRequired = computed(() => props.role === 'rnd' && !props.counter && props.status !== 'pending')
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
      toast.success(props.status === 'pending'
        ? `Time suggested. ${name} was told; if they accept, it's confirmed.`
        : `New time sent. ${name} was told and can answer in My Appointments.`, { id: `move-${props.appointmentId}` })
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
/* the redesigned booking pop-up's frame (RndProfileView.vue .booking-modal-box / .bk-head / .bk-foot), kept in step with it */
.mv-box {
  position: relative; width: 100%; max-width: 980px; max-height: 94vh; max-height: 94dvh; display: flex; flex-direction: column; overflow: hidden;
  border-radius: 24px; background: #FFFFFF; box-shadow: 0 40px 90px -30px rgba(0, 0, 0, 0.6); font-family: 'DM Sans', Arial, sans-serif; color: #10231B;
}
.mv-head { display: flex; align-items: center; gap: 22px; padding: 20px 30px; color: #FFFFFF; background: #0B5640; }
.mv-badge { flex-shrink: 0; width: 66px; height: 66px; border-radius: 50%; background: #E3EFE7; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; border: 3px solid #FFFFFF; box-shadow: 0 8px 18px -10px rgba(0, 0, 0, 0.5); }
.mv-head-text { flex: 1; min-width: 0; }
.mv-title { margin: 0 0 6px; font-family: 'Playfair Display', Georgia, serif; font-size: 26px; font-weight: 700; line-height: 1.2; color: #FFFFFF; }
.mv-sub { margin: 0; font-size: 14px; line-height: 1.5; color: rgba(255, 255, 255, 0.88); }
/* the shared [role=dialog] Close style is dark; on the green band it is white, like the booking pop-up */
.mv-box .mv-x { flex-shrink: 0; align-self: flex-start; width: 40px; height: 40px; border: none; border-radius: 50%; background: transparent; color: #FFFFFF; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background-color .15s; }
.mv-box .mv-x:hover { background: rgba(255, 255, 255, 0.14); color: #FFFFFF; }
.mv-box .mv-x:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.mv-body { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; }
.mv-now { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 0 0 16px; padding: 12px 18px; border-radius: 999px; background: #E3F0E7; font-size: 15px; color: #0E3A2C; }
.mv-now :deep(svg) { color: #1F5C45; }
.mv-now span { font-weight: 700; }
.mv-section { margin-bottom: 16px; }
.mv-section:last-child { margin-bottom: 0; }
.mv-section .nm-note { margin: 0 0 12px; }
.mv-h { display: flex; align-items: center; gap: 10px; margin: 0 0 10px; font-size: 16px; font-weight: 700; color: #0E3A2C; }
.mv-h :deep(svg) { color: #1F5C45; }
.mv-h .optional { font-size: 13.5px; font-weight: 500; color: #6B7D73; }
.mv-input { width: 100%; min-height: 74px; padding: 14px 18px; border: 1px solid #D5E2D9; border-radius: 14px; background: #FFFFFF; font-family: inherit; font-size: 14px; color: #14261E; resize: vertical; }
.mv-input::placeholder { color: #8A9A91; }
.mv-input:focus { outline: none; border-color: #0B5640; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.mv-hint { margin: 6px 0 0; font-size: 12.5px; color: #6B7D73; }
.mv-foot { display: flex; align-items: center; gap: 14px 22px; padding: 18px 24px; border-top: 1px solid #E3ECE6; background: #FFFFFF; }
.mv-sumbox { flex: 1; min-width: 0; display: flex; align-items: center; gap: 18px; padding: 12px 18px 12px 0; border-radius: 16px; background: linear-gradient(90deg, #EEF5F0 0, #EEF5F0 70px, rgba(238, 245, 240, 0) 70px); }
.mv-sum-ico { flex-shrink: 0; width: 70px; display: inline-flex; align-items: center; justify-content: center; color: #1F5C45; }
.mv-sum-ico :deep(svg) { width: 36px; height: 36px; padding: 6px; border-radius: 50%; border: 2px solid currentColor; }
.mv-sum-ico.ready { color: #0B5640; }
.mv-summary { flex: 1; min-width: 0; }
.mv-pick { margin: 0; font-size: 17px; font-weight: 700; color: #0E3A2C; }
.mv-pick.muted { font-weight: 600; color: #3E5046; }
.mv-after { margin: 4px 0 0; font-size: 12.5px; line-height: 1.5; color: #3E5046; }
.mv-error { margin: 4px 0 0; font-size: 13px; font-weight: 600; color: #B42318; }
.mv-box .mv-send { flex-shrink: 0; gap: 12px; height: 56px; padding: 0 32px; border-radius: 16px; background: #0B5640; font-size: 15.5px; font-weight: 600; }
.mv-box .mv-send:hover:not(:disabled) { background: #136047; }
.mv-box .mv-send:disabled { background: #C9D6CE; color: #FFFFFF; opacity: 1; }
@media (max-width: 640px) {
  .mv-overlay { padding: 0; align-items: stretch; }
  .mv-box { max-width: none; max-height: none; height: 100%; border-radius: 0; }
  .mv-head { gap: 12px; padding: 16px; padding-top: calc(16px + env(safe-area-inset-top)); }
  .mv-badge { width: 48px; height: 48px; }
  .mv-title { font-size: 19px; }
  .mv-sub { font-size: 12.5px; }
  .mv-now { border-radius: 14px; font-size: 14px; padding: 10px 14px; }
  .mv-foot { flex-direction: column; align-items: stretch; gap: 10px; padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); }
  .mv-sumbox { padding: 10px 14px 10px 0; background: linear-gradient(90deg, #EEF5F0 0, #EEF5F0 56px, rgba(238, 245, 240, 0) 56px); gap: 12px; }
  .mv-sum-ico { width: 56px; }
  .mv-box .mv-send { width: 100%; justify-content: center; height: 50px; }
}
</style>
