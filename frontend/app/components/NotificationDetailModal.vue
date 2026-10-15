<template>
  <Teleport to="body">
    <div class="nm-modal-overlay" @click.self="emit('close')">
      <div class="nm-modal nd-box" role="dialog" aria-modal="true" :aria-label="note.subject || 'Notification'">
        <div class="nd-head">
          <div class="nd-icon" :class="tone"><component :is="icon" :size="18" /></div>
          <div class="nd-head-text">
            <p class="nm-section-title" style="margin: 0 0 2px">{{ TYPE_LABELS[note.notifiable_type] || 'Notification' }}</p>
            <h3 class="nm-modal-title" style="margin: 0">{{ note.subject || 'Notification' }}</h3>
            <p class="nd-time">{{ dateTime(note.created_at) }} · {{ timeAgo(note.created_at) }}</p>
          </div>
          <button class="nd-close" aria-label="Close" @click="emit('close')"><X :size="18" /></button>
        </div>

        <p v-if="note.content" class="nd-content">{{ note.content }}</p>

        <p v-if="loading" class="nm-muted">Loading details…</p>
        <p v-else-if="error" class="nm-field-error">{{ error }}</p>
 
        <template v-else-if="related">
          <p class="nm-section-title">Details</p>

          <!-- the full message -->
          <div v-if="type === 'message'" class="nd-quote">
            <p class="nd-quote-from">{{ related.sender }} · {{ dateTime(related.created_at) }}</p>
            <p class="nd-quote-text">{{ related.message }}</p>
          </div>

          <dl v-else class="nd-rows">
            <template v-if="type === 'appointment'">
              <div><dt>{{ withLabel }}</dt><dd>{{ related.with.name }}</dd></div>
              <div><dt>Date &amp; time</dt><dd>{{ dateTime(related.scheduled_at) }}</dd></div>
              <div><dt>Length</dt><dd>{{ related.duration_minutes || 60 }} min · {{ MODE_LABELS[related.type] || related.type }}</dd></div>
              <div><dt>Status</dt><dd><span class="nm-pill" :class="APPT_PILLS[related.status] || 'muted'">{{ APPT_LABELS[related.status] || related.status }}</span></dd></div>
              <div v-if="related.cancellation_reason"><dt>Reason</dt><dd>{{ related.cancellation_reason }}</dd></div>
              <div v-if="related.invoice"><dt>Payment</dt><dd>{{ peso(related.invoice.amount) }} · {{ INVOICE_LABELS[related.invoice.status] || related.invoice.status }}</dd></div>
            </template>

            <template v-else-if="type === 'invoice'">
              <div><dt>Invoice</dt><dd class="mono">INV-{{ String(related.id).padStart(4, '0') }}</dd></div>
              <div><dt>{{ withLabel }}</dt><dd>{{ related.with.name }}</dd></div>
              <div><dt>Amount</dt><dd><strong>{{ peso(related.amount) }}</strong></dd></div>
              <div><dt>Status</dt><dd><span class="nm-pill" :class="INVOICE_PILLS[related.status] || 'muted'">{{ INVOICE_LABELS[related.status] || related.status }}</span></dd></div>
              <div v-if="related.paid_at"><dt>Paid</dt><dd>{{ dateTime(related.paid_at) }}<template v-if="related.payment_method"> · {{ METHOD_LABELS[related.payment_method] || related.payment_method }}</template></dd></div>
              <div v-if="related.appointment"><dt>Consultation</dt><dd>{{ dateTime(related.appointment.scheduled_at) }}</dd></div>
            </template>

            <template v-else-if="type === 'lab_request'">
              <div><dt>Tests</dt><dd>{{ related.test_names.join(', ') }}</dd></div>
              <div><dt>{{ withLabel }}</dt><dd>{{ related.with.name }}</dd></div>
              <div v-if="related.status === 'open'"><dt>Needed before</dt><dd>{{ related.needed_before ? dateTime(related.needed_before) : 'Your next consultation' }}</dd></div>
              <div><dt>Status</dt><dd>{{ { open: 'Waiting for upload', completed: 'Uploaded', cancelled: 'Cancelled' }[related.status] }}</dd></div>
              <div v-if="related.note"><dt>Note</dt><dd>{{ related.note }}</dd></div>
            </template>

            <template v-else-if="type === 'lab_result'">
              <div><dt>Tests</dt><dd>{{ related.test_names.join(', ') }}</dd></div>
              <div><dt>{{ withLabel }}</dt><dd>{{ related.with.name }}</dd></div>
              <div><dt>Taken</dt><dd>{{ new Date(`${related.taken_on}T00:00:00`).toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' }) }}</dd></div>
              <div><dt>Status</dt><dd>{{ related.reviewed_at ? 'Reviewed' : 'Not opened yet' }}</dd></div>
            </template>

            <template v-else-if="type === 'meal_plan'">
              <div><dt>Plan</dt><dd>{{ related.name }}</dd></div>
              <div><dt>{{ withLabel }}</dt><dd>{{ related.with.name }}</dd></div>
              <div v-if="related.target_kcal"><dt>Daily target</dt><dd>{{ Math.round(Number(related.target_kcal)).toLocaleString() }} kcal</dd></div>
              <div><dt>Status</dt><dd>{{ PLAN_LABELS[related.status] || related.status }}</dd></div>
              <div v-if="related.sent_at"><dt>Sent</dt><dd>{{ dateTime(related.sent_at) }}</dd></div>
            </template>

            <template v-else-if="type === 'reminder'">
              <div><dt>Reminder</dt><dd>{{ related.title }}</dd></div>
              <div v-if="related.with"><dt>Set by</dt><dd>RND {{ related.with.name }}</dd></div>
              <div><dt>Repeats</dt><dd>{{ related.repeat }}</dd></div>
              <div v-if="related.next_at"><dt>Next</dt><dd>{{ new Date(related.next_at).toLocaleString('en-PH', { timeZone: 'Asia/Manila', weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }) }}</dd></div>
            </template>

            <template v-else-if="type === 'resource'">
              <div><dt>Resource</dt><dd>{{ related.title }}</dd></div>
              <div><dt>{{ withLabel }}</dt><dd>{{ related.with.name }}</dd></div>
              <div><dt>Type</dt><dd>{{ RESOURCE_LABELS[related.type] || related.type }}</dd></div>
            </template>

            <template v-else-if="type === 'payout'">
              <div><dt>Amount</dt><dd><strong>{{ peso(related.amount) }}</strong></dd></div>
              <div><dt>Sent via</dt><dd>{{ related.method === 'gcash' ? 'GCash' : 'Bank transfer' }}</dd></div>
              <div><dt>Reference</dt><dd class="mono">{{ related.reference }}</dd></div>
              <div><dt>Released</dt><dd>{{ dateTime(related.released_at) }}</dd></div>
            </template>
          </dl>
        </template>

        <p v-else-if="note.notifiable_type && !['meal_log', 'relationship'].includes(note.notifiable_type)" class="nm-hint">
          The {{ (TYPE_LABELS[note.notifiable_type] || 'item').toLowerCase() }} this notification was about is no longer available.
        </p>

        <div class="nm-modal-actions">
          <button class="nm-btn-outline" @click="emit('close')">Close</button>
          <button v-if="link" class="nm-btn-dark" @click="go">{{ link.label }} <ArrowRight :size="14" /></button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { AlarmClock, ArrowRight, Bell, BookOpen, CalendarCheck, FlaskConical, MessageSquare, Receipt, Utensils, Wallet, X, HeartHandshake, Headset } from 'lucide-vue-next'

// Full detail of one notification + a button to the page it's about.
// `notification` is the list row (shown right away); the related record is
// fetched from GET /notifications/<id>/ (only returned when it's the user's).
const props = defineProps({ notification: { type: Object, required: true } })
const emit = defineEmits(['close'])

const { get } = useApi()
const auth = useAuthStore()
const route = useRoute()

const note = computed(() => props.notification)
const type = computed(() => note.value.notifiable_type)
const related = ref(null)
const loading = ref(false)
const error = ref('')

const TYPE_LABELS = { appointment: 'Appointment', invoice: 'Invoice', message: 'Message', meal_plan: 'Meal plan', meal_log: 'Meal log', payout: 'Payout', resource: 'Resource', reminder: 'Reminder', relationship: 'Care plan', support: 'Support request', lab_request: 'Lab request', lab_result: 'Lab result' }
const ICONS = { appointment: CalendarCheck, invoice: Receipt, message: MessageSquare, meal_plan: Utensils, meal_log: Utensils, payout: Wallet, resource: BookOpen, reminder: AlarmClock, relationship: HeartHandshake, support: Headset, lab_request: FlaskConical, lab_result: FlaskConical }
const TONES = { appointment: 'gold', invoice: 'warn', message: 'info', payout: 'good', reminder: 'gold', lab_request: 'gold', lab_result: 'gold' }
const APPT_LABELS = { pending: 'Awaiting confirmation', confirmed: 'Confirmed', completed: 'Completed', cancelled: 'Cancelled' }
const APPT_PILLS = { pending: 'gold', confirmed: 'green', completed: 'blue', cancelled: 'muted' }
const INVOICE_LABELS = { unpaid: 'Awaiting payment', paid: 'Paid', refund_pending: 'Refund pending', refunded: 'Refunded', cancelled: 'Voided' }
const INVOICE_PILLS = { unpaid: 'gold', paid: 'green', refund_pending: 'red', refunded: 'blue', cancelled: 'muted' }
const METHOD_LABELS = { card: 'Card', gcash: 'GCash', maya: 'Maya', qrph: 'QR Ph', bank_transfer: 'Bank transfer', cash: 'Cash', other: 'Other' }
const PLAN_LABELS = { draft: 'Draft', active: 'Active', archived: 'Archived' }
const RESOURCE_LABELS = { pdf: 'PDF', video: 'Video', article: 'Article', link: 'Link' }

const icon = computed(() => ICONS[type.value] || Bell)
const tone = computed(() => TONES[type.value] || '')
const role = computed(() => auth.user?.role)
const withLabel = computed(() => (related.value?.with?.role === 'rnd' ? 'Dietitian' : 'Client'))

// Where "Go to …" leads, per role.
const link = computed(() => {
  const r = related.value
  const t = type.value
  // Support replies open the request: the Support page for admins, the
  // help panel (?support=<id>, SupportWidget.vue) for clients and RNDs.
  if (t === 'support' && r) {
    return role.value === 'admin'
      ? { label: 'Open request', to: { path: '/admin-support', query: { ticket: r.id } } }
      : { label: 'Open my request', to: { path: route.path, query: { ...route.query, support: r.id } } }
  }
  if (role.value === 'admin') {
    return {
      invoice: { label: 'Open Billing & Commission', to: '/billing-commission' },
      appointment: { label: 'Open Appointments', to: '/admin-appointments' },
      payout: { label: 'Open Payouts', to: '/payouts' },
    }[t] || null
  }
  if (t === 'relationship' && role.value === 'client') return { label: 'Find an RND', to: '/find-rnd' }
  if (!r) return null
  const messages = { label: 'Open conversation', to: { path: '/messages', query: r?.relationship_id ? { relationship: r.relationship_id } : {} } }
  if (role.value === 'rnd') {
    return {
      appointment: { label: 'Open Appointments', to: '/appointments' },
      invoice: { label: 'View earnings', to: '/earnings' },
      payout: { label: 'View earnings', to: '/earnings' },
      message: messages,
      meal_plan: { label: 'Open Meal Plans', to: '/meal-planning' },
      lab_result: { label: 'Open lab results', to: `/client-detail/${r.relationship_id}?tab=labs` },
    }[t] || null
  }
  return {
    appointment: { label: 'Go to My Appointments', to: '/appointments' },
    invoice: { label: r?.status === 'unpaid' ? 'Go to Billing to pay' : 'Go to Billing', to: '/invoices-billing' },
    message: messages,
    meal_plan: { label: 'View my meal plan', to: '/meal-plan-view' },
    resource: { label: 'Open Resources', to: '/resource-library' },
    lab_request: { label: r?.status === 'open' ? 'Upload lab results' : 'Open Lab Results', to: '/lab-results' },
    reminder: { label: 'My reminder settings', to: { path: '/profile-settings', query: { tab: 'notifications' } } },
  }[t] || null
})

function go() {
  const to = link.value?.to
  emit('close')
  if (to) navigateTo(to)
}

function timeAgo(iso) {
  const seconds = Math.floor((Date.now() - new Date(iso)) / 1000)
  for (const [label, secs] of [['year', 31536000], ['month', 2592000], ['day', 86400], ['hour', 3600], ['minute', 60]]) {
    const value = Math.floor(seconds / secs)
    if (value >= 1) return `${value} ${label}${value > 1 ? 's' : ''} ago`
  }
  return 'just now'
}

function onKey(e) { if (e.key === 'Escape') emit('close') }

onMounted(async () => {
  window.addEventListener('keydown', onKey)
  if (!note.value.notifiable_type || !note.value.notifiable_id) return
  loading.value = true
  try {
    related.value = (await get(`/notifications/${note.value.id}/`)).related
  } catch {
    error.value = 'Could not load the details. Please try again.'
  } finally {
    loading.value = false
  }
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<style scoped>
.nd-box { max-width: 480px; }
.nd-head { display: flex; gap: 12px; align-items: flex-start; }
.nd-head-text { flex: 1; min-width: 0; }
.nd-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: #eef3ee; color: #1a3a1a; flex-shrink: 0; }
.nd-icon.gold { background: #fbf3dc; color: #a37a0b; }
.nd-icon.warn { background: #fdf0e6; color: #b5651d; }
.nd-icon.info { background: #e8f0fb; color: #2c5c9a; }
.nd-icon.good { background: #e6f4ea; color: #2e7d32; }
.nd-time { font-size: 0.76rem; color: #8a9a8a; margin: 4px 0 0; }
.nd-close { background: none; border: none; color: #8a9a8a; cursor: pointer; padding: 4px; }
.nd-content { font-size: 0.88rem; color: #2a3a2a; line-height: 1.55; margin: 16px 0 0; white-space: pre-line; overflow-wrap: anywhere; }
.nd-rows { margin: 0; border: 1px solid #eceeec; border-radius: 10px; padding: 2px 14px; }
.nd-rows > div { display: flex; justify-content: space-between; gap: 16px; padding: 9px 0; font-size: 0.84rem; }
.nd-rows > div + div { border-top: 1px solid #f0f2f0; }
.nd-rows dt { color: #8a9a8a; font-weight: 500; flex-shrink: 0; }
.nd-rows dd { margin: 0; color: #1a3a1a; text-align: right; overflow-wrap: anywhere; }
.nd-quote { border-left: 3px solid #c7d6ca; background: #fafcfa; border-radius: 0 10px 10px 0; padding: 10px 14px; }
.nd-quote-from { font-size: 0.74rem; font-weight: 600; color: #8a9a8a; margin: 0 0 6px; }
.nd-quote-text { font-size: 0.88rem; color: #1a3a1a; line-height: 1.55; margin: 0; white-space: pre-line; overflow-wrap: anywhere; }
.mono { font-variant-numeric: tabular-nums; }
.nm-btn-dark { display: inline-flex; align-items: center; gap: 6px; }
</style>
