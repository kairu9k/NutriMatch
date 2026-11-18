<template>
  <!-- A consultation being rescheduled (scheduling/reschedule.py): the new
       time waiting for an answer, and what this person can do about it. -->
  <div v-if="r?.waiting" class="rs-box" :class="{ todo: myTurn }">
    <template v-if="mode === 'view'">
      <p class="rs-line">
        <template v-if="myTurn">
          {{ r.waiting.proposed_by === 'rnd' ? `RND ${otherName}` : otherName }}
          {{ firstOffer ? `can't make ${when(r.original_at)} and offered` : 'proposed' }}
          <strong>{{ when(r.waiting.scheduled_at) }}</strong>{{ firstOffer ? ' instead' : '' }}.
        </template>
        <template v-else>You proposed <strong>{{ when(r.waiting.scheduled_at) }}</strong>. Waiting for {{ role === 'client' ? `RND ${otherName}` : otherName }} to answer.</template>
      </p>
      <p v-if="r.waiting.note" class="rs-note">{{ myTurn ? 'Note' : 'Your note' }}: {{ r.waiting.note }}</p>
      <p class="rs-sub">
        {{ myTurn ? 'Answer' : 'They answer' }} by {{ when(r.waiting.expires_at) }}, or it's cancelled with a full refund.
        <template v-if="role === 'client'">You don't pay again for a new time.</template>
      </p>
      <p v-if="myTurn && !r.proposals_left" class="rs-sub">Three times have been proposed, so this is the last one: accept it or {{ role === 'client' ? 'get a full refund' : 'cancel with a full refund' }}.</p>
      <div class="rs-actions">
        <button v-if="myTurn" type="button" class="nm-btn-dark nm-btn-sm" :disabled="!!busy" @click="send('accept')">{{ busy === 'accept' ? 'Accepting…' : 'Accept new time' }}</button>
        <button v-if="myTurn && r.proposals_left" type="button" class="nm-btn-soft nm-btn-sm" :disabled="!!busy" @click="mode = 'propose'">Propose another time</button>
        <button v-if="role === 'client'" type="button" class="nm-btn-danger solid nm-btn-sm" :disabled="!!busy" @click="mode = 'refund'">Get a full refund</button>
        <button v-else type="button" class="nm-btn-danger solid nm-btn-sm" :disabled="!!busy" @click="emit('cancel')">Cancel with full refund</button>
      </div>
    </template>

    <template v-else-if="mode === 'propose'">
      <p class="rs-line">Pick another time from {{ role === 'client' ? `RND ${otherName}'s` : 'your' }} open hours.</p>
      <RescheduleSlotPicker v-model="pick" :appointment-id="appointment.id"
                            :empty-hint="role === 'client' ? 'You can accept the offered time or get a full refund.' : 'Add hours in Availability, or cancel with a full refund.'" />
      <label class="nm-label rs-gap" :for="`rs-note-${appointment.id}`">Note <span class="rs-opt">(optional)</span></label>
      <textarea :id="`rs-note-${appointment.id}`" v-model="note" class="nm-input" rows="2" maxlength="500" data-allow-emoji></textarea>
      <div class="rs-actions">
        <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="!!busy" @click="mode = 'view'">Back</button>
        <button type="button" class="nm-btn-dark nm-btn-sm" :disabled="!pick || !!busy" @click="send('propose')">{{ busy === 'propose' ? 'Sending…' : 'Send this time' }}</button>
      </div>
    </template>

    <template v-else>
      <p class="rs-line">Cancel this consultation and get your full {{ amount ? `₱${amount}` : 'payment' }} back?</p>
      <p class="rs-sub">The refund reaches you within 5–7 business days. You can book again any time.</p>
      <div class="rs-actions">
        <button type="button" class="nm-btn-soft nm-btn-sm" :disabled="!!busy" @click="mode = 'view'">Back</button>
        <button type="button" class="nm-btn-danger solid nm-btn-sm" :disabled="!!busy" @click="send('refund')">{{ busy === 'refund' ? 'Cancelling…' : 'Yes, refund me' }}</button>
      </div>
    </template>
    <p v-if="error" class="nm-field-error">{{ error }}</p>
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
const firstOffer = computed(() => r.value?.history?.length === 1)
const amount = computed(() => props.appointment.payment?.amount ? Number(props.appointment.payment.amount).toLocaleString('en-PH', { minimumFractionDigits: 2 }) : '')
const mode = ref('view')
const pick = ref('')
const note = ref('')
const busy = ref('')
const error = ref('')

const PH = { timeZone: 'Asia/Manila' }
const when = v => new Date(v).toLocaleString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })

const DONE = { accept: 'New time accepted. The consultation is confirmed.', propose: 'Time sent. You\'ll be told when they answer.', refund: 'Consultation cancelled. Your full refund is on its way.' }
async function send(action) {
  busy.value = action
  error.value = ''
  try {
    const body = { action }
    if (action === 'propose') Object.assign(body, { scheduled_at: pick.value, note: note.value.trim() || undefined })
    await post(`/${props.role === 'client' ? 'client' : 'rnd'}/appointments/${props.appointment.id}/reschedule/`, body)
    toast.success(DONE[action], { id: `reschedule-${props.appointment.id}` })
    mode.value = 'view'
    pick.value = ''
    note.value = ''
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
.rs-gap { margin-top: 12px; }
.rs-opt { font-weight: 400; color: #8a9a8a; }
.rs-box :deep(.rs-picker) { margin-top: 8px; }
</style>
