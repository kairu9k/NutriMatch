<template>
  <!-- A consultation being rescheduled (scheduling/reschedule.py): the new
       time waiting for an answer, and what this person can do about it. -->
  <div v-if="r?.waiting" class="rs-box" :class="{ todo: myTurn }">
    <!-- a booking request the RND hasn't confirmed: the RND suggested another time (2026-11-27) -->
    <template v-if="onRequest">
      <p class="rs-line">
        <template v-if="role === 'client'">RND {{ otherName }} can't do {{ when(appointment.scheduled_at) }} and suggested <strong>{{ when(r.waiting.scheduled_at) }}</strong> instead.</template>
        <template v-else>You suggested <strong>{{ when(r.waiting.scheduled_at) }}</strong>. Waiting for {{ otherName }} to answer.</template>
      </p>
      <p v-if="r.waiting.note" class="rs-note">{{ role === 'client' ? 'Note' : 'Your note' }}: {{ r.waiting.note }}</p>
      <p class="rs-sub">
        <template v-if="role === 'client'">Accept it and your consultation is confirmed. Answer by {{ when(r.waiting.expires_at) }}; otherwise your request stays on {{ when(appointment.scheduled_at) }}.</template>
        <template v-else>If they accept, it's confirmed at that time. If they keep theirs or don't answer by {{ when(r.waiting.expires_at) }}, the request stays on {{ when(appointment.scheduled_at) }} and you can still confirm or decline it.</template>
      </p>
      <div v-if="role === 'client'" class="rs-actions">
        <button type="button" class="nm-btn-dark nm-btn-sm" :disabled="!!busy" @click="send('accept')">{{ busy === 'accept' ? 'Accepting…' : 'Accept new time' }}</button>
        <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="!!busy" @click="send('keep')">{{ busy === 'keep' ? 'Keeping…' : 'Keep my requested time' }}</button>
      </div>
    </template>
    <template v-else-if="mode === 'view'">
      <p class="rs-line">
        <template v-if="myTurn && clientsRequest && firstOffer">
          {{ otherName }} asked to move the consultation on {{ when(appointment.scheduled_at) }} to <strong>{{ when(r.waiting.scheduled_at) }}</strong>.
        </template>
        <template v-else-if="myTurn">
          {{ r.waiting.proposed_by === 'rnd' ? `RND ${otherName}` : otherName }}
          {{ firstOffer ? `can't make ${when(r.original_at)} and offered` : 'proposed' }}
          <strong>{{ when(r.waiting.scheduled_at) }}</strong>{{ firstOffer ? ' instead' : '' }}.
        </template>
        <template v-else-if="clientsRequest && firstOffer">You asked to move it to <strong>{{ when(r.waiting.scheduled_at) }}</strong>. Waiting for RND {{ otherName }} to answer.</template>
        <template v-else>You proposed <strong>{{ when(r.waiting.scheduled_at) }}</strong>. Waiting for {{ role === 'client' ? `RND ${otherName}` : otherName }} to answer.</template>
      </p>
      <p v-if="r.waiting.note" class="rs-note">{{ myTurn ? 'Note' : 'Your note' }}: {{ r.waiting.note }}</p>
      <p class="rs-sub">
        <template v-if="clientsRequest">
          {{ myTurn ? 'Answer' : 'They answer' }} by {{ when(r.waiting.expires_at) }}. Otherwise it stays on {{ when(appointment.scheduled_at) }}.
        </template>
        <template v-else>
          {{ myTurn ? 'Answer' : 'They answer' }} by {{ when(r.waiting.expires_at) }}, or it's cancelled{{ paid ? ' with a full refund' : '' }}.
          <template v-if="role === 'client' && paid">You don't pay again for a new time.</template>
        </template>
      </p>
      <div class="rs-actions">
        <button v-if="myTurn" type="button" class="nm-btn-dark nm-btn-sm" :disabled="!!busy" @click="send('accept')">{{ busy === 'accept' ? 'Accepting…' : 'Accept new time' }}</button>
        <button v-if="myTurn" type="button" class="nm-btn-soft nm-btn-sm" :disabled="!!busy" @click="picking = true">Reschedule</button>
        <!-- the client's own request: nothing is refunded, the booking just stays (2026-11-23) -->
        <template v-if="clientsRequest">
          <button v-if="role === 'client'" type="button" class="nm-btn-soft nm-btn-sm" :disabled="!!busy" @click="send('keep')">{{ busy === 'keep' ? 'Keeping…' : 'Keep my current time' }}</button>
          <button v-else-if="myTurn" type="button" class="nm-btn-danger solid nm-btn-sm" :disabled="!!busy" @click="send('decline')">{{ busy === 'decline' ? 'Declining…' : 'Decline' }}</button>
        </template>
        <template v-else>
          <button v-if="role === 'client'" type="button" class="nm-btn-danger solid nm-btn-sm" :disabled="!!busy" @click="mode = 'refund'">{{ paid ? 'Get a full refund' : 'Cancel consultation' }}</button>
          <button v-else type="button" class="nm-btn-danger solid nm-btn-sm" :disabled="!!busy" @click="emit('cancel')">{{ paid ? 'Cancel with full refund' : 'Cancel consultation' }}</button>
        </template>
      </div>
    </template>

    <template v-else>
      <p class="rs-line">{{ paid ? `Cancel this consultation and get your full ${amount ? `₱${amount}` : 'payment'} back?` : 'Cancel this consultation? You haven\'t paid, so nothing is charged.' }}</p>
      <p class="rs-sub">{{ paid ? 'The refund reaches you within 5–7 business days. You can book again any time.' : 'You can book again any time.' }}</p>
      <div class="rs-actions">
        <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="!!busy" @click="mode = 'view'">Back</button>
        <button type="button" class="nm-btn-danger solid nm-btn-sm" :disabled="!!busy" @click="send('refund')">{{ busy === 'refund' ? 'Cancelling…' : paid ? 'Yes, refund me' : 'Yes, cancel it' }}</button>
      </div>
    </template>
    <p v-if="error" class="nm-field-error">{{ error }}</p>

    <!-- Reschedule: answer this time with another one, in the same pop-up as everywhere else -->
    <Teleport to="body">
      <RescheduleModal
        v-if="picking" counter :role="role" :appointment-id="appointment.id" :other-first-name="otherName.split(' ')[0]"
        :paid="paid" :type-label="appointment.typeLabel || appointment.type_label || 'Video call'"
        :booked-label="when(appointment.scheduled_at)" @close="picking = false" @done="onCounter"
      />
    </Teleport>
  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'

const props = defineProps({
  appointment: { type: Object, required: true }, // needs id, reschedule, payment
  role: { type: String, required: true }, // client | rnd
  otherName: { type: String, required: true },
})
const emit = defineEmits(['changed', 'cancel'])
const toast = useToast()
const { post } = useApi()

const r = computed(() => props.appointment.reschedule)
const myTurn = computed(() => r.value?.turn === props.role)
// the first proposal of this round (an earlier, finished reschedule may be in the history too)
const firstOffer = computed(() => r.value?.waiting && r.value.history?.filter(p => p.created_at >= roundStart.value).length === 1)
const roundStart = computed(() => {
  const h = r.value?.history || []
  let start = h.length ? h[0].created_at : ''
  h.forEach((p, i) => { if (['accepted', 'refunded', 'expired', 'declined', 'withdrawn'].includes(p.status) && h[i + 1]) start = h[i + 1].created_at })
  return start
})
// the client asked for this new time (2026-11-23): the RND declines rather than refunds,
// and if it ends without a move the booking simply stays
const clientsRequest = computed(() => r.value?.started_by === 'client')
// the RND's suggested time on a request they haven't confirmed yet
const onRequest = computed(() => props.appointment.status === 'pending')
const amount = computed(() => props.appointment.payment?.amount ? Number(props.appointment.payment.amount).toLocaleString('en-PH', { minimumFractionDigits: 2 }) : '')
const paid = computed(() => props.appointment.payment?.status === 'paid')
const mode = ref('view')
const picking = ref(false)
const busy = ref('')
const error = ref('')

const PH = { timeZone: 'Asia/Manila' }
const when = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })

function onCounter() {
  picking.value = false
  emit('changed')
}

const DONE = {
  accept: 'New time accepted. The consultation is confirmed.',
  refund: props.appointment.payment?.status === 'paid' ? 'Consultation cancelled. Your full refund is on its way.' : 'Consultation cancelled.',
  keep: props.appointment.status === 'pending' ? 'Your requested time is kept.' : 'Your current time is kept.',
  decline: 'Request declined. The consultation stays at its current time.',
}
async function send(action) {
  busy.value = action
  error.value = ''
  try {
    await post(`/${props.role === 'client' ? 'client' : 'rnd'}/appointments/${props.appointment.id}/reschedule/`, { action })
    toast.success(DONE[action], { id: `reschedule-${props.appointment.id}` })
    mode.value = 'view'
    emit('changed')
  } catch (e) {
    error.value = apiError(e, 'Could not send this. Please try again.')
  } finally {
    busy.value = ''
  }
}
</script>

<style scoped>
.rs-box { margin-top: 10px; padding: 12px 14px; border-radius: 10px; background: #f4f6f4; border: 1px solid #d9e3dc; }
.rs-box.todo { background: #fff; border: 1.5px dashed #3f9a6b; }
.rs-line { margin: 0 0 4px; font-size: 0.86rem; color: #1a3a1a; line-height: 1.45; }
.rs-note { margin: 4px 0; font-size: 0.82rem; color: #4a5a4a; overflow-wrap: anywhere; }
.rs-sub { margin: 4px 0 0; font-size: 0.78rem; color: #6a7a6a; line-height: 1.45; }
.rs-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
</style>
