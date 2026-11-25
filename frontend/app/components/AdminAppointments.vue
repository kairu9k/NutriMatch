<template>
  <div class="nm-page">
    <section class="ap-hero">
      <img class="ap-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="ap-fade" aria-hidden="true"></span>
      <div class="ap-hero-txt">
        <p class="ap-eyebrow"><span aria-hidden="true"></span>Appointments</p>
        <h2 class="ap-title">Every consultation on NutriMatch</h2>
        <p class="ap-sub">Bookings across all clients and RNDs. All times are Philippine time.</p>
      </div>
    </section>

    <p v-if="error" class="nm-error">{{ error }}</p>

    <!-- AT A GLANCE: one divided panel; each figure opens the list it counts -->
    <div class="nm-panel glance">
      <button type="button" class="fig" @click="jump('upcoming')">
        <span class="fig-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg></span>
        <strong>{{ summary.today ?? '—' }}</strong>
        <span class="fig-label">Consultations today</span>
        <span class="fig-note">{{ summary.next_7_days ?? 0 }} in the next 7 days</span>
      </button>
      <button type="button" class="fig" @click="jump('requests')">
        <span class="fig-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2h12M6 22h12M7 2v4l5 6-5 6v4M17 2v4l-5 6 5 6v4" /></svg></span>
        <strong>{{ summary.requests ?? '—' }}</strong>
        <span class="fig-label">Waiting for the RND</span>
        <span class="fig-note" :class="{ warn: summary.stale_requests }">
          {{ summary.stale_requests ? `${summary.stale_requests} waiting over ${summary.stale_request_hours} hours` : 'None waiting too long' }}
        </span>
      </button>
      <button type="button" class="fig" @click="jump('upcoming', 'unpaid')">
        <span class="fig-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /></svg></span>
        <strong :class="{ warn: summary.unpaid_soon }">{{ summary.unpaid_soon ?? '—' }}</strong>
        <span class="fig-label">Unpaid, starting within 24 hours</span>
        <span class="fig-note">Cancelled on its own if still unpaid 15 minutes before the start</span>
      </button>
      <button type="button" class="fig" @click="jump('past')">
        <span class="fig-ico"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M8.5 12.5l2.5 2.5 4.5-5" /></svg></span>
        <strong>{{ summary.completed_7_days ?? '—' }}</strong>
        <span class="fig-label">Completed in 7 days</span>
        <span class="fig-note">{{ summary.cancelled_7_days ?? 0 }} cancelled in 7 days</span>
      </button>
    </div>

    <div class="nm-toolbar ap-toolbar">
      <div class="nm-tabs ap-tabs">
        <button v-for="t in VIEWS" :key="t.key" type="button" class="nm-tab" :class="{ active: view === t.key }" @click="view = t.key">
          <svg v-if="t.key === 'upcoming'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M16 3v4M8 3v4M3 10h18" /></svg><svg v-else-if="t.key === 'requests'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2h12M6 22h12M7 2v4l5 6-5 6v4M17 2v4l-5 6 5 6v4" /></svg><svg v-else-if="t.key === 'past'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg><svg v-else-if="t.key === 'cancelled'" class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M15 9l-6 6M9 9l6 6" /></svg><svg v-else class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></svg>
          {{ t.label }}<span v-if="t.count && summary[t.count]" class="nm-count"> {{ summary[t.count] }}</span>
        </button>
      </div>
      <div class="appt-tools">
        <label class="ap-sel">
        <svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 5h18l-7 8v6l-4 2v-8z" /></svg>
        <select v-model="payment" class="nm-select" aria-label="Filter by payment">
          <option value="">Any payment</option>
          <option value="unpaid">Awaiting payment</option>
          <option value="paid">Paid</option>
          <option value="refund_pending">Refund pending</option>
          <option value="refunded">Refunded</option>
        </select>
        </label>
        <div class="nm-search ap-search">
          <Search :size="17" aria-hidden="true" />
          <input v-model="search" type="search" placeholder="Search client, RND or appointment no." />
        </div>
      </div>
    </div>

    <p v-if="personFilter" class="nm-note plain-note person-filter">
      Showing only {{ personFilter.label }}.
      <button type="button" class="nm-btn-soft nm-btn-sm" @click="clearPerson">Show everyone</button>
    </p>

    <!-- THE AGENDA: grouped by Philippine day, time on the left -->
    <div ref="listTop" class="nm-panel agenda-panel">
      <div class="agenda-head">
        <div class="dates">
          <span class="dates-k">Date range</span>
          <label class="date-field">From <DateField v-model="dateFrom" compact clearable hint="Pick the first day." placeholder="Any date" aria-label="From" /></label>
          <label class="date-field">To <DateField v-model="dateTo" :min="dateFrom" compact clearable hint="Pick the last day." placeholder="Any date" aria-label="To" /></label>
          <button v-if="dateFrom || dateTo" type="button" class="nm-btn-soft nm-btn-sm" @click="dateFrom = ''; dateTo = ''">Clear dates</button>
        </div>
        <span class="nm-muted count ap-count">{{ loading ? 'Loading…' : `${count} appointment${count === 1 ? '' : 's'}` }}</span>
      </div>

      <div v-if="!loading && !rows.length" class="nm-empty">
        <span class="ap-eico"><CalendarX :size="28" aria-hidden="true" /></span>
        <p>{{ emptyText }}</p>
      </div>

      <div v-if="rows.length" class="agenda-cols" aria-hidden="true">
        <span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg> Time</span><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg> Client and RND</span><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 21V4M4 4h12l-2 4 2 4H4" /></svg> Status</span><span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /></svg> Payment</span><span></span>
      </div>

      <section v-for="d in days" :key="d.key" class="day">
        <h3 class="day-title">
          <span class="day-date" aria-hidden="true"><b>{{ dayParts(d.key).d }}</b><small>{{ dayParts(d.key).m }}</small></span>
          <span class="day-label">{{ d.label }}</span>
          <span class="day-count">{{ d.items.length }} appointment{{ d.items.length === 1 ? '' : 's' }}</span>
        </h3>
        <button v-for="a in d.items" :key="a.id" type="button" class="appt" :class="[{ attention: attentionOf(a) }, 'tone-' + rowTone(a)]" @click="selected = a">
          <span class="appt-time">
            <strong>{{ timeText(a.scheduled_at) }}</strong>
            <small><component :is="a.type === 'in_person' ? MapPin : Video" :size="13" aria-hidden="true" /> {{ a.type === 'in_person' ? 'In person' : a.type === 'chat' ? 'Chat' : 'Video' }} · {{ a.duration_minutes || 60 }} min</small>
          </span>
          <span class="appt-people">
            <img v-if="a.client.profile_photo" :src="a.client.profile_photo" class="nm-avatar sm" alt="" />
            <span v-else class="nm-avatar sm">{{ nameInitials(a.client.name) }}</span>
            <span class="appt-names">
              <span class="appt-client">{{ a.client.name }}</span>
              <span class="appt-rnd">with RND {{ a.rnd.name }}</span>
            </span>
          </span>
          <span class="appt-state">
            <span class="nm-pill" :class="statusOf(a).pill">{{ statusOf(a).label }}</span>
            <span v-if="attendanceOf(a)" class="appt-att" :class="attendanceOf(a).pill">{{ attendanceOf(a).label }}</span>
            <span v-if="attentionOf(a)" class="appt-flag">{{ attentionOf(a) }}</span>
          </span>
          <span class="appt-pay">
            <span v-if="a.payment" class="pay" :class="PAY[a.payment.status]?.pill || 'muted'">{{ PAY[a.payment.status]?.label || a.payment.status }}</span>
            <span v-else class="pay-none">—</span>
          </span>
          <span class="appt-go" aria-hidden="true"><ChevronRight :size="16" /></span>
        </button>
      </section>

      <ListPager v-model:page="page" :pages="pages" />
    </div>

    <!-- DETAILS -->
    <div v-if="selected" class="nm-modal-overlay" @click.self="selected = null">
      <div class="nm-modal detail" role="dialog" aria-modal="true" aria-labelledby="appt-title">
        <header class="am-head">
          <img class="am-plate" :src="plateImg" alt="" aria-hidden="true" />
          <span class="am-fade" aria-hidden="true"></span>
          <span class="am-date" aria-hidden="true"><b>{{ dayParts(dayKey(selected.scheduled_at)).d }}</b><small>{{ dayParts(dayKey(selected.scheduled_at)).m }}</small></span>
          <div class="am-ht">
            <p class="am-kind">Appointment #{{ selected.id }}</p>
            <h3 id="appt-title" class="nm-modal-title">{{ dayText(selected.scheduled_at, true) }}</h3>
            <p class="detail-sub am-meta">
              <span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg> {{ timeText(selected.scheduled_at) }}</span>
              <span><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2h12M6 22h12M7 2v4l5 6-5 6v4M17 2v4l-5 6 5 6v4" /></svg> {{ selected.duration_minutes || 60 }} min</span>
              <span><component :is="selected.type === 'in_person' ? MapPin : Video" :size="14" aria-hidden="true" /> {{ selected.type === 'in_person' ? 'In person' : selected.type === 'chat' ? 'Chat' : 'Video call' }}</span>
            </p>
          </div>
          <span class="nm-pill am-st" :class="statusOf(selected).pill">{{ statusOf(selected).label }}</span>
          <button type="button" class="nm-modal-x am-x" aria-label="Close" @click="selected = null"><X :size="18" aria-hidden="true" /></button>
        </header>

        <div class="am-body">
        <div class="people">
          <NuxtLink v-for="p in [{ role: 'Client', ...selected.client }, { role: 'RND', ...selected.rnd }]" :key="p.role" :to="`/users/${p.id}`" class="person">
            <img v-if="p.profile_photo" :src="p.profile_photo" class="nm-avatar" alt="" />
            <span v-else class="nm-avatar">{{ nameInitials(p.name) }}</span>
            <span class="person-text">
              <i class="role" :class="p.role === 'RND' ? 'rnd' : 'client'">{{ p.role }}</i>
              <span class="nm-row-title">{{ p.name }}</span>
              <span class="nm-row-sub"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="4" width="20" height="16" rx="2" /><path d="M22 6l-10 7L2 6" /></svg> {{ p.email }}</span>
            </span>
            <span class="person-go" aria-hidden="true"><ChevronRight :size="15" /></span>
          </NuxtLink>
        </div>

        <!-- what has happened so far: a real sequence -->
        <p class="am-h">What happened</p>
        <ol class="track">
          <li v-for="s in steps" :key="s.key" :class="s.state">
            <span class="dot" aria-hidden="true"><Check v-if="s.state === 'done'" :size="12" /><X v-else-if="s.state === 'stopped'" :size="12" /></span>
            <span class="step-text">
              <strong>{{ s.label }}</strong>
              <span>{{ s.detail }}</span>
            </span>
          </li>
        </ol>

        <p v-if="selected.cancellation_reason" class="nm-note plain-note reason"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg><span>{{ selected.cancellation_reason }}</span></p>
        <p v-if="selected.attendance" class="nm-note reason" :class="selected.attendance.state === 'both' ? 'plain-note' : 'attend-warn'">
          <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l10 18H2z" /><path d="M12 10v4M12 17h.01" /></svg><span><strong>Attendance:</strong> {{ selected.attendance.line }}</span>
        </p>
        <p v-if="selected.cancelled_late" class="nm-note attend-warn reason">
          <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l10 18H2z" /><path d="M12 10v4M12 17h.01" /></svg><span>A last-minute cancel by the RND{{ selected.cancel_category ? ` (${CATEGORY[selected.cancel_category] || selected.cancel_category})` : '' }}.</span>
        </p>
        <div v-if="selected.reschedule" class="nm-note plain-note reason">
          <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" /></svg><div><strong>New times proposed</strong> (booked for {{ dateTime(selected.reschedule.original_at) }}):
          <ul class="rs-history">
            <li v-for="p in selected.reschedule.history" :key="p.id">
              {{ p.proposed_by === 'rnd' ? 'RND' : 'Client' }} proposed {{ dateTime(p.scheduled_at) }}, {{ p.status_label.toLowerCase() }}<template v-if="p.note">. Note: {{ p.note }}</template>
            </li>
          </ul></div>
        </div>
        <p v-if="selected.dispute?.opened_at" class="nm-note reason" :class="selected.dispute.resolved_at ? 'plain-note' : 'attend-warn'">
          <svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 11v5M12 8h.01" /></svg><span><strong>Dispute:</strong>
          <template v-if="selected.dispute.resolved_at"> {{ selected.dispute.outcome === 'refunded' ? 'approved, refunded' : 'rejected' }}. {{ selected.dispute.note }}</template>
          <template v-else> waiting for a decision. <NuxtLink to="/admin-support" class="nm-text-link">Decide on the Support page</NuxtLink>.</template></span>
        </p>

        <dl class="nm-dl facts">
          <div>
            <span class="af-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg></span>
            <dt>Invoice</dt>
            <dd v-if="selected.payment">
              <NuxtLink to="/billing-commission" class="nm-text-link">INV-{{ String(selected.payment.invoice_id).padStart(4, '0') }}</NuxtLink>,
              {{ peso(selected.payment.amount) }}
            </dd>
            <dd v-else class="muted">{{ selected.status === 'pending' ? 'Issued when the RND confirms' : 'None' }}</dd>
          </div>
          <div>
            <span class="af-ico" :class="selected.payment ? PAY[selected.payment.status]?.pill : ''"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20" /></svg></span>
            <dt>Payment</dt>
            <dd v-if="selected.payment"><span class="pay" :class="PAY[selected.payment.status]?.pill || 'muted'">{{ PAY[selected.payment.status]?.label || selected.payment.status }}</span></dd>
            <dd v-else class="muted">None yet</dd>
          </div>
          <div v-if="selected.notes" class="wide"><span class="af-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg></span><dt>Client's note</dt><dd>{{ selected.notes }}</dd></div>
        </dl>

        <p v-if="startedOpen(selected)" class="nm-hint started">This consultation has started, so it can't be cancelled here. The RND closes it from the consultation room.</p>
        </div>

        <div class="nm-modal-actions am-foot">
          <button type="button" class="nm-btn-soft" @click="selected = null">Close</button>
          <button v-if="canCancel(selected)" type="button" class="nm-btn-danger solid" @click="openCancel"><Ban :size="14" aria-hidden="true" /> Cancel appointment</button>
        </div>
      </div>
    </div>

    <!-- CANCEL: a last resort, the button waits 3 seconds -->
    <div v-if="cancelling" class="nm-modal-overlay" style="z-index: 310" @click.self="busy ? null : closeCancel()">
      <div class="nm-modal" role="dialog" aria-modal="true" aria-labelledby="cancel-title">
        <button type="button" class="nm-modal-x" aria-label="Close" @click="busy ? null : closeCancel()"><X :size="18" aria-hidden="true" /></button>
        <h3 id="cancel-title" class="nm-modal-title">Cancel this appointment?</h3>
        <p class="nm-modal-text">
          Only cancel when the client or the RND can't do it themselves, for example after a support request.
          {{ selected.client.name }} and RND {{ selected.rnd.name }} will both be notified with your reason.
        </p>
        <p v-if="selected.payment?.status === 'paid'" class="nm-note">
          <strong>The client paid {{ peso(selected.payment.amount) }}.</strong> It will be marked for refund and listed under Refunds in Billing and commission.
        </p>
        <p v-else-if="selected.payment?.status === 'unpaid'" class="nm-note plain-note">The unpaid invoice will be voided.</p>
        <label class="nm-label" for="cancel-reason">Reason</label>
        <textarea id="cancel-reason" v-model="reason" class="nm-input" rows="3" maxlength="500"
          placeholder="For example: the RND has a family emergency and can't attend." />
        <p v-if="cancelError" class="nm-field-error">{{ cancelError }}</p>
        <p v-else class="nm-hint">At least 10 characters. Both people will see this.</p>
        <div class="nm-modal-actions">
          <button type="button" class="nm-btn-soft" :disabled="busy" @click="closeCancel">Keep it</button>
          <button type="button" class="nm-btn-danger solid" :disabled="busy || lockLeft > 0" @click="confirmCancel">
            {{ busy ? 'Cancelling…' : lockLeft > 0 ? `Cancel appointment (${lockLeft})` : 'Cancel appointment' }}
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import { Ban, CalendarX, Check, CheckCircle2, ChevronRight, MapPin, Search, Video, X } from 'lucide-vue-next'

const { get, post } = useApi()
const route = useRoute()

const PER_PAGE = 20
const VIEWS = [
  { key: 'upcoming', label: 'Upcoming', count: 'upcoming' },
  { key: 'requests', label: 'Waiting for RND', count: 'requests' },
  { key: 'past', label: 'Past' },
  { key: 'cancelled', label: 'Cancelled' },
  { key: 'all', label: 'All' },
]
// states in green/grey, things an admin may need to act on in gold
const PAY = {
  unpaid: { label: 'Awaiting payment', pill: 'gold' },
  paid: { label: 'Paid', pill: 'green' },
  refund_pending: { label: 'Refund pending', pill: 'gold' },
  refunded: { label: 'Refunded', pill: 'muted' },
  cancelled: { label: 'Voided', pill: 'muted' },
}

const view = ref(VIEWS.some(v => v.key === route.query.view) ? route.query.view : 'upcoming')
const search = ref('')
const payment = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const person = ref({ client: route.query.client || '', rnd: route.query.rnd || '' })
const page = ref(1)

const summary = ref({})
const rows = ref([])
const count = ref(0)
const pages = computed(() => Math.max(1, Math.ceil(count.value / PER_PAGE)))
const loading = ref(true)
const error = ref('')
const toast = useToast() // the app's toast (2026-11-03)
const selected = ref(null)
const listTop = ref(null)

const personFilter = computed(() => {
  if (!person.value.client && !person.value.rnd) return null
  const first = rows.value[0]
  if (person.value.client) return { label: first ? `${first.client.name}'s appointments` : "this client's appointments" }
  return { label: first ? `RND ${first.rnd.name}'s appointments` : "this RND's appointments" }
})
function clearPerson() {
  person.value = { client: '', rnd: '' }
  navigateTo({ query: { view: view.value } }, { replace: true })
}
function jump(v, pay = '') {
  view.value = v
  payment.value = pay
}

const emptyText = computed(() => {
  if (search.value.trim() || payment.value || dateFrom.value || dateTo.value) return 'No appointments match these filters.'
  return {
    upcoming: 'No upcoming appointments.',
    requests: 'No booking requests waiting for an RND.',
    past: 'No past appointments.',
    cancelled: 'No cancelled appointments.',
  }[view.value] || 'No appointments yet.'
})

function params() {
  const q = { view: view.value, page: page.value, page_size: PER_PAGE }
  if (search.value.trim()) q.search = search.value.trim()
  if (payment.value) q.payment = payment.value
  if (dateFrom.value) q.date_from = dateFrom.value
  if (dateTo.value) q.date_to = dateTo.value
  if (person.value.client) q.client = person.value.client
  if (person.value.rnd) q.rnd = person.value.rnd
  return q
}

let requestId = 0
async function load({ quiet = false } = {}) {
  const id = ++requestId
  if (!quiet) {
    loading.value = true
    error.value = ''
  }
  try {
    const r = await get('/admin/appointments/', { query: params() })
    if (id !== requestId) return
    rows.value = r.results
    count.value = r.count
    // a quiet refresh can leave the page past the end (rows cancelled meanwhile)
    if (page.value > pages.value) page.value = pages.value
  } catch {
    if (id === requestId && !quiet) error.value = 'Could not load appointments. Refresh the page to try again.'
  } finally {
    if (id === requestId) loading.value = false
  }
}
async function loadSummary() {
  try {
    summary.value = await get('/admin/appointments/summary/')
  } catch {
    summary.value = {}
  }
}
useAutoRefresh(() => Promise.all([loadSummary(), load({ quiet: true })]))

let searchTimer
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value === 1 ? load() : (page.value = 1) }, 350)
})
// a new filter starts again at page 1 (the page watcher then loads)
watch([view, payment, dateFrom, dateTo, person], () => { page.value === 1 ? load() : (page.value = 1) }, { deep: true })
watch(page, () => {
  load()
  listTop.value?.scrollIntoView({ block: 'start', behavior: 'smooth' })
})
watch(view, v => navigateTo({ query: { ...route.query, view: v } }, { replace: true }))
onMounted(() => {
  load()
  loadSummary()
})

/* display */
const PH = { timeZone: 'Asia/Manila' }
const dayKey = v => new Date(v).toLocaleDateString('en-CA', PH)
function dayLabel(v) {
  const key = dayKey(v)
  const today = dayKey(Date.now())
  const md = new Date(v).toLocaleDateString('en-PH', { ...PH, month: 'long', day: 'numeric' })
  if (key === today) return `Today, ${md}`
  if (key === dayKey(Date.now() + 86400000)) return `Tomorrow, ${md}`
  if (key === dayKey(Date.now() - 86400000)) return `Yesterday, ${md}`
  return dayText(v, true, key.slice(0, 4) !== today.slice(0, 4))
}
// rows arrive sorted by the server; group neighbours that share a day
const days = computed(() => {
  const out = []
  for (const a of rows.value) {
    const key = dayKey(a.scheduled_at)
    const last = out[out.length - 1]
    if (last && last.key === key) last.items.push(a)
    else out.push({ key, label: dayLabel(a.scheduled_at), items: [a] })
  }
  return out
})

function statusOf(a) {
  const past = new Date(a.scheduled_at) < new Date()
  if (a.status === 'pending') return past ? { label: 'Expired', pill: 'muted' } : { label: 'Waiting for RND', pill: 'gold' }
  if (a.status === 'confirmed') {
    if (!past) return { label: 'Confirmed', pill: 'green' }
    const end = new Date(a.scheduled_at).getTime() + (a.duration_minutes || 60) * 60000
    return Date.now() < end ? { label: 'In progress', pill: 'green' } : { label: 'Not marked complete', pill: 'gold' }
  }
  if (a.status === 'completed') return { label: 'Completed', pill: 'muted' }
  if (a.status === 'no_show') return { label: 'No-show', pill: 'red' }
  if (a.status === 'rescheduling') return { label: 'Rescheduling', pill: 'gold' }
  return { label: 'Cancelled', pill: 'muted' }
}
const CATEGORY = { emergency: 'emergency', technical: 'technical problem', other: 'other' }
// Who joined the video call (green: both; red: only one or neither). Only for
// calls that were due, so a future booking shows nothing.
function attendanceOf(a) {
  const at = a.attendance
  if (!at || a.status === 'pending' || new Date(a.scheduled_at) > new Date()) return null
  if (at.state === 'both') return { label: `Both attended, ${at.together_minutes} min`, pill: 'green' }
  if (at.state === 'rnd_only') return { label: 'Only the RND joined', pill: 'red' }
  if (at.state === 'client_only') return { label: 'Only the client joined', pill: 'red' }
  return a.status === 'cancelled' ? null : { label: 'Neither joined', pill: 'red' }
}
// one short gold line when a row needs a look
function attentionOf(a) {
  const now = Date.now()
  const start = new Date(a.scheduled_at).getTime()
  if (a.status === 'pending' && start > now && now - new Date(a.created_at) > (summary.value.stale_request_hours || 24) * 3600000) {
    return `Waiting ${ageText(a.created_at)} for the RND`
  }
  if (a.status === 'confirmed' && a.payment?.status === 'unpaid' && start > now && start - now < 86400000) {
    return `Unpaid, starts in ${untilText(start - now)}`
  }
  return ''
}
function ageText(v) {
  const h = Math.floor((Date.now() - new Date(v)) / 3600000)
  return h >= 48 ? `${Math.floor(h / 24)} days` : `${h} hours`
}
function untilText(ms) {
  const m = Math.max(1, Math.round(ms / 60000))
  return m < 60 ? `${m} min` : `${Math.round(m / 60)} h`
}
function dayText(v, long = false, withYear = true) {
  return new Date(v).toLocaleDateString('en-PH', {
    ...PH, weekday: long ? 'long' : 'short', month: long ? 'long' : 'short', day: 'numeric', ...(withYear ? { year: 'numeric' } : {}),
  })
}
function timeText(v) {
  return new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
}
function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}
function canCancel(a) {
  return a.status === 'rescheduling' || (['pending', 'confirmed'].includes(a.status) && new Date(a.scheduled_at) > new Date())
}
function startedOpen(a) {
  return a.status === 'confirmed' && new Date(a.scheduled_at) <= new Date()
}

// Booked, confirmed, paid, then completed or cancelled
const steps = computed(() => {
  const a = selected.value
  if (!a) return []
  const pay = a.payment
  const cancelled = a.status === 'cancelled' || a.status === 'no_show'
  const out = [{ key: 'booked', label: 'Booked by the client', detail: dateTime(a.created_at), state: 'done' }]
  const confirmed = !!pay?.issued_at && a.status !== 'pending'
  out.push({
    key: 'confirmed', label: 'Confirmed by the RND',
    detail: confirmed ? dateTime(pay.issued_at) : cancelled ? 'Never confirmed' : 'Not yet',
    state: confirmed ? 'done' : cancelled ? 'stopped' : 'todo',
  })
  if (confirmed || !cancelled) {
    const paid = !!pay?.paid_at
    out.push({
      key: 'paid', label: 'Paid',
      detail: paid ? dateTime(pay.paid_at) : cancelled ? 'Never paid' : 'Due before the start',
      state: paid ? 'done' : cancelled ? 'stopped' : 'todo',
    })
  }
  if (a.status === 'no_show') out.push({ key: 'end', label: 'Marked as a no-show', detail: a.completed_at ? dateTime(a.completed_at) : '', state: 'stopped' })
  else if (cancelled) out.push({ key: 'end', label: 'Cancelled', detail: dateTime(a.updated_at), state: 'stopped' })
  else out.push({ key: 'end', label: 'Completed', detail: a.completed_at ? dateTime(a.completed_at) : 'Not yet', state: a.completed_at ? 'done' : 'todo' })
  return out
})

/* cancel */
const cancelling = ref(false)
const reason = ref('')
const cancelError = ref('')
const busy = ref(false)
const lockLeft = ref(0)
let lockTimer
function openCancel() {
  reason.value = ''
  cancelError.value = ''
  cancelling.value = true
  lockLeft.value = 3
  clearInterval(lockTimer)
  lockTimer = setInterval(() => {
    lockLeft.value -= 1
    if (lockLeft.value <= 0) clearInterval(lockTimer)
  }, 1000)
}
function closeCancel() {
  clearInterval(lockTimer)
  cancelling.value = false
}
onBeforeUnmount(() => clearInterval(lockTimer))
async function confirmCancel() {
  cancelError.value = ''
  if (reason.value.trim().length < 10) {
    cancelError.value = 'Explain why in at least 10 characters. Both people will see this.'
    return
  }
  busy.value = true
  try {
    const updated = await post(`/admin/appointments/${selected.value.id}/cancel/`, { reason: reason.value.trim() })
    closeCancel()
    selected.value = null
    toast.success(updated.payment?.status === 'refund_pending'
      ? 'Appointment cancelled. The payment is now under Refunds in Billing and commission.'
      : 'Appointment cancelled. Both people were notified.')
    load()
    loadSummary()
  } catch (e) {
    cancelError.value = apiError(e, 'Could not cancel this appointment. Try again.')
  } finally {
    busy.value = false
  }
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// "2026-11-30" → { d: '30', m: 'Nov' } for the small date block
const dayParts = key => {
  const dt = new Date(`${key}T12:00:00+08:00`)
  return { d: dt.toLocaleDateString('en-PH', { ...PH, day: 'numeric' }), m: dt.toLocaleDateString('en-PH', { ...PH, month: 'short' }) }
}
// accent colour of a row: gold = needs a look, red = a problem, grey = cancelled
function rowTone(a) {
  if (attentionOf(a) || a.payment?.status === 'refund_pending' || statusOf(a).pill === 'gold') return 'gold'
  const at = attendanceOf(a)
  if (statusOf(a).pill === 'red' || at?.pill === 'red') return 'red'
  if (a.status === 'cancelled') return 'muted'
  return 'green'
}
</script>
<style scoped>
.nm-page { --sh: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); font-family: 'DM Sans', sans-serif; color: #22362c; }
.ic { flex-shrink: 0; display: inline-block; }

/* ---------- hero ---------- */
.ap-hero { position: relative; overflow: hidden; margin-bottom: 26px; padding: 26px 30px; border-radius: 24px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 50%, #004635 100%); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55); }
.ap-plate { position: absolute; right: -70px; top: 50%; width: 300px; height: 300px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.ap-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 52%, rgba(0, 77, 58, 0.85) 72%, rgba(0, 77, 58, 0.6) 100%); }
.ap-hero-txt { position: relative; z-index: 1; max-width: 620px; }
.ap-eyebrow { display: flex; align-items: center; gap: 10px; margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 2.4px; text-transform: uppercase; color: #efbf04; }
.ap-eyebrow span { width: 22px; height: 2px; border-radius: 2px; background: #efbf04; }
.ap-title { margin: 0 0 6px; font-family: 'Playfair Display', serif; font-size: 30px; font-weight: 700; line-height: 1.2; letter-spacing: 0.01em; color: #fff; }
.ap-sub { margin: 0; font-size: 14.5px; line-height: 1.55; color: rgba(255, 255, 255, 0.85); }

/* ---------- at a glance: four cards ---------- */
.glance { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; margin-bottom: 24px; padding: 0; border: none; background: none; box-shadow: none; overflow: visible; }
.fig { display: grid; grid-template-columns: 42px minmax(0, 1fr); grid-auto-rows: auto; column-gap: 14px; align-items: start; min-width: 0; padding: 18px; border: 1.5px solid #c9d8cf; border-radius: 20px; background: #fff; box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.08); font-family: inherit; color: #0e3a2c; text-align: left; cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
.fig:hover { transform: translateY(-1px); box-shadow: 0 14px 24px -16px rgba(0, 77, 58, 0.5); }
.fig:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.fig-ico { grid-row: 1 / 4; width: 42px; height: 42px; border-radius: 13px; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.fig strong { font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 700; line-height: 1.05; color: #0e3a2c; font-variant-numeric: lining-nums; }
.fig strong.warn { color: #8a6500; }
.fig-label { margin-top: 4px; font-size: 14px; font-weight: 700; color: #0e3a2c; }
.fig-note { margin-top: 2px; font-size: 12.5px; line-height: 1.4; color: #6b7d73; }
.fig-note.warn { color: #8a6500; font-weight: 700; }

/* ---------- tabs + filters ---------- */
.ap-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin: 0 0 16px; }
.ap-tabs { display: inline-flex; gap: 4px; max-width: 100%; padding: 5px; border: none; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); overflow-x: auto; scrollbar-width: none; }
.ap-tabs::-webkit-scrollbar { display: none; }
.ap-tabs .nm-tab { flex-shrink: 0; display: inline-flex; align-items: center; gap: 7px; height: 36px; margin: 0; padding: 0 15px; border: none; border-radius: 999px; background: transparent; font-family: inherit; font-size: 13.5px; font-weight: 400; color: #4a5a52; white-space: nowrap; cursor: pointer; }
.ap-tabs .nm-tab .ic { color: #8a9a91; }
.ap-tabs .nm-tab:hover:not(.active) { background: #f1f6f2; }
.ap-tabs .nm-count { min-width: 20px; height: 20px; margin-left: 2px; padding: 0 6px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 700; color: #4a5a52; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.ap-tabs .nm-tab.active { background: #004d3a; color: #fff; font-weight: 600; }
.ap-tabs .nm-tab.active .ic { color: #efbf04; }
.ap-tabs .nm-tab.active .nm-count { background: #efbf04; color: #004d3a; }
.ap-tabs .nm-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 2px; }
.appt-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.ap-sel { display: flex; align-items: center; gap: 8px; height: 46px; padding: 0 6px 0 16px; border-radius: 999px; background: #fff; color: #1f7a4d; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); cursor: pointer; }
.ap-sel:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.ap-sel .nm-select { width: auto; min-width: 150px; height: 100%; margin: 0; padding: 0 28px 0 0; border: none !important; background-color: transparent !important; box-shadow: none !important; font-family: inherit; font-size: 14px; color: #22362c; outline: none; cursor: pointer; }
.ap-search { position: relative; display: flex; align-items: center; gap: 10px; width: 320px; max-width: 100%; height: 46px; margin: 0; padding: 0 16px; border: none; border-radius: 999px; background: #fff; color: #8a9a91; box-sizing: border-box; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.03), 0 4px 14px -6px rgba(0, 0, 0, 0.12); }
.ap-search:focus-within { box-shadow: 0 0 0 2px #004d3a, 0 0 0 6px rgba(0, 77, 58, 0.1); }
.ap-search svg { position: static !important; transform: none !important; flex-shrink: 0; }
.ap-search input { flex: 1; min-width: 0; height: 100%; padding: 0 !important; border: none !important; outline: none; background: transparent !important; font-family: inherit; font-size: 14px; color: #14261e; box-shadow: none; }
.person-filter { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; border-radius: 14px; }

/* ---------- the agenda ---------- */
.agenda-panel { scroll-margin-top: 16px; padding: 0; border: none; border-radius: 24px; background: #fff; box-shadow: var(--sh); overflow: hidden; }
.agenda-head { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; justify-content: space-between; padding: 16px 24px; background: #f1f8f4; border-bottom: 1px solid #e3efe7; }
.dates { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.dates-k { font-size: 13px; font-weight: 800; color: #0e3a2c; }
.date-field { display: inline-flex; align-items: center; gap: 8px; padding-left: 12px; border-radius: 12px; background: #fff; border: 1.5px solid #c9d8cf; font-size: 12px; font-weight: 800; color: #1f5c45; }
.date-field :deep(.df-trigger) { border: none !important; box-shadow: none !important; background: transparent !important; }
.ap-count { padding: 5px 12px; border-radius: 999px; background: #fff; box-shadow: 0 0 0 1px #dce8e0; font-size: 12.5px; font-weight: 700; color: #1f5c45; }
.agenda-panel :deep(.nm-empty) { display: flex; flex-direction: column; align-items: center; gap: 10px; margin: 24px; padding: 40px 20px; border-radius: 18px; border: 1.5px dashed #cfddd4; text-align: center; }
.agenda-panel :deep(.nm-empty p) { margin: 0; font-size: 15px; font-weight: 700; color: #0e3a2c; }
.ap-eico { width: 60px; height: 60px; border-radius: 18px; background: #e3efe7; color: #004d3a; display: inline-flex; align-items: center; justify-content: center; }

/* columns: the header row and every appointment share one grid */
.agenda-cols, .appt { display: grid; grid-template-columns: 160px minmax(0, 1.7fr) minmax(0, 1.1fr) minmax(0, 0.8fr) 40px; gap: 16px; align-items: center; }
.agenda-cols { padding: 13px 24px; background: #eaf3ed; border-bottom: 1px solid #dcebe1; font-size: 13px; font-weight: 700; color: #1f5c45; }
.agenda-cols span { display: inline-flex; align-items: center; gap: 6px; }
.agenda-cols .ic { color: #1f7a4d; }

.day + .day { margin-top: 0; }
.day-title { display: flex; align-items: center; gap: 12px; margin: 0; padding: 12px 24px; background: #f7faf8; border-bottom: 1px solid #f0f3f1; font-family: inherit; font-size: 16px; font-weight: 800; color: #0e3a2c; }
.day-date { flex-shrink: 0; width: 54px; height: 58px; border-radius: 14px; display: inline-flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; background: linear-gradient(160deg, #035a45, #004d3a); color: #fff; border-bottom: 2px solid #efbf04; box-shadow: 0 8px 16px -10px rgba(0, 77, 58, 0.8); }
.day-date b { font-family: 'Playfair Display', serif; font-size: 23px; line-height: 1; font-variant-numeric: lining-nums; }
.day-date small { font-size: 10.5px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #efbf04; }
.day-count { padding: 2px 9px; border-radius: 999px; background: #eef2ef; font-size: 11.5px; font-weight: 700; color: #6b7d73; }

.appt { position: relative; width: 100%; margin: 0; padding: 18px 24px; background: #fff; border: 0; border-bottom: 1px solid #f0f3f1; font-family: inherit; color: #0e3a2c; text-align: left; cursor: pointer; transition: background 0.15s; }
.appt:hover { background: #fafcfb; }
.appt:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.appt::before { content: ''; position: absolute; left: 0; top: 18px; bottom: 18px; width: 4px; border-radius: 0 4px 4px 0; background: #1f9d55; }
.appt.tone-gold::before { background: #efbf04; }
.appt.tone-red::before { background: #c0392b; }
.appt.tone-muted::before { background: #c9d3cd; }
.appt-time { display: flex; flex-direction: column; border: none; padding: 0; }
.appt-time strong { font-size: 15px; font-weight: 800; color: #004d3a; font-variant-numeric: tabular-nums; white-space: nowrap; }
.appt-time small { display: inline-flex; align-items: center; gap: 6px; margin-top: 2px; font-size: 12.5px; color: #8a9a91; white-space: nowrap; }
.appt-time small svg { color: #1f7a4d; }
.appt-people { display: flex; align-items: center; gap: 12px; min-width: 0; }
.nm-avatar.sm { flex-shrink: 0; width: 40px; height: 40px; border-radius: 50%; object-fit: cover; box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; background: #e3efe7; color: #004d3a; font-size: 13px; font-weight: 800; border: 2px solid #fff; box-shadow: 0 0 0 1.5px #c9d8cf; }
.appt-names { display: flex; flex-direction: column; min-width: 0; }
.appt-client { font-size: 14.5px; font-weight: 700; color: #0e3a2c; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.appt-rnd { margin-top: 2px; font-size: 13px; color: #6b7d73; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.appt-state { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; min-width: 0; }
.appt-state .nm-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 800; }
.appt-state .nm-pill::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.nm-pill.green { background: #e3f4ea; color: #1f7a4d; }
.nm-pill.gold { background: #fff4d6; color: #8a6500; }
.nm-pill.red { background: #fdecea; color: #b42318; }
.nm-pill.muted { background: #f3f6f4; color: #6b7d73; }
.appt-att { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; font-weight: 600; }
.appt-att::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.appt-att.green { color: #1f7a4d; }
.appt-att.red { color: #b42318; }
.appt-flag { font-size: 12px; font-weight: 700; color: #8a6500; }
.pay { display: inline-flex; align-items: center; gap: 7px; padding: 5px 12px; border-radius: 10px; background: #f7faf8; border: 1px solid #e3ebe6; font-size: 13px; font-weight: 700; white-space: nowrap; }
.pay::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.pay.green { color: #1f7a4d; }
.pay.gold { color: #8a6500; background: #fffbea; border-color: #f3e2a0; }
.pay.muted { color: #8a9a91; }
.pay-none { font-weight: 700; color: #b5c3ba; }
.appt-go { justify-self: end; width: 30px; height: 30px; border-radius: 50%; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; transition: background 0.15s, color 0.15s; }
.appt:hover .appt-go { background: #004d3a; color: #fff; }
.agenda-panel :deep(.nm-pager) { margin: 0; padding: 14px 24px; border-top: 1px solid #f0f3f1; }

/* ---------- details pop-up ---------- */
.nm-modal.detail { position: relative; display: flex; flex-direction: column; width: min(760px, 100%); max-width: 760px; max-height: calc(100vh - 48px); padding: 0; border-radius: 24px; overflow: hidden; background: #fff; box-shadow: 0 40px 90px -30px rgba(0, 0, 0, 0.55); }
.am-head { position: relative; overflow: hidden; flex-shrink: 0; display: flex; align-items: center; gap: 18px; padding: 26px 30px; color: #fff; background: radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%), linear-gradient(115deg, #035a45 0%, #004d3a 55%, #004635 100%); }
.am-head > *:not(.am-plate):not(.am-fade) { position: relative; z-index: 1; }
.am-plate { position: absolute; right: -50px; top: 50%; width: 210px; height: 210px; object-fit: cover; border-radius: 50%; transform: translateY(-50%); pointer-events: none; }
.am-fade { position: absolute; inset: 0; pointer-events: none; background: linear-gradient(90deg, #004d3a 0%, #004d3a 55%, rgba(0, 77, 58, 0.88) 72%, rgba(0, 77, 58, 0.7) 100%); }
.am-date { flex-shrink: 0; width: 66px; height: 72px; border-radius: 15px; background: #fff; color: #004d3a; display: inline-flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; border-bottom: 3px solid #efbf04; box-shadow: 0 10px 20px -12px rgba(0, 0, 0, 0.5); }
.am-date b { font-family: 'Playfair Display', serif; font-size: 29px; line-height: 1; font-variant-numeric: lining-nums; }
.am-date small { font-size: 10.5px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #c49102; }
.am-ht { flex: 1; min-width: 0; }
.am-kind { margin: 0 0 3px; font-size: 11.5px; font-weight: 800; letter-spacing: 1.6px; text-transform: uppercase; color: #efbf04; }
.detail .am-head .nm-modal-title { margin: 0; padding: 0; font-family: 'Playfair Display', serif; font-size: 26px; font-weight: 700; line-height: 1.2; color: #fff; }
.am-meta { display: flex; flex-wrap: wrap; gap: 6px; margin: 8px 0 0; }
.am-meta span { display: inline-flex; align-items: center; gap: 6px; padding: 5px 11px; border-radius: 999px; background: rgba(255, 255, 255, 0.12); font-size: 13px; font-weight: 700; color: #fff; }
.am-meta .ic, .am-meta svg { color: #efbf04; }
.am-st { align-self: flex-start; display: inline-flex; align-items: center; gap: 6px; padding: 5px 11px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.am-st::before { content: ''; width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.am-st.muted { background: #f3f6f4; color: #4a5a52; }
.detail .nm-modal-x.am-x { position: relative; inset: auto; flex-shrink: 0; align-self: flex-start; width: 36px; height: 36px; margin: 0; border-radius: 11px; border: 1px solid rgba(255, 255, 255, 0.4); background: rgba(0, 56, 42, 0.85); color: #fff; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; backdrop-filter: blur(6px); }
.am-x:focus-visible { outline: 2px solid #efbf04; outline-offset: 2px; }
.am-body { flex: 1; min-height: 0; overflow-y: auto; padding: 26px 30px 28px; }
.people { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.person { display: flex; gap: 14px; align-items: center; min-width: 0; padding: 16px; border: 1.5px solid #e3ebe6; border-radius: 16px; text-decoration: none; transition: border-color 0.15s; }
.person:hover { border-color: #9dc3ae; background: #fff; }
.person .nm-avatar { flex-shrink: 0; width: 52px; height: 52px; border-radius: 50%; object-fit: cover; box-sizing: border-box; display: inline-flex; align-items: center; justify-content: center; background: #004d3a; color: #efbf04; font-size: 14px; font-weight: 800; border: 2px solid #fff; box-shadow: 0 0 0 1.5px #c9d8cf; }
.person-text { flex: 1; min-width: 0; display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
.role { padding: 1px 8px; border-radius: 999px; font-style: normal; font-size: 10.5px; font-weight: 800; letter-spacing: 0.4px; text-transform: uppercase; }
.role.client { background: #fff4d6; color: #8a6500; }
.role.rnd { background: #e3f4ea; color: #1f7a4d; }
.person .nm-row-title { max-width: 100%; font-size: 16px; font-weight: 700; color: #0e3a2c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.person .nm-row-sub { display: flex; align-items: center; gap: 5px; max-width: 100%; margin: 0; font-size: 13px; color: #6b7d73; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.person .nm-row-sub .ic { color: #1f7a4d; }
.person-go { flex-shrink: 0; width: 28px; height: 28px; border-radius: 50%; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.am-h { margin: 26px 0 16px; font-size: 16px; font-weight: 800; color: #0e3a2c; }

/* the steps, left to right */
.track { position: relative; display: grid; grid-template-columns: repeat(auto-fit, minmax(0, 1fr)); list-style: none; margin: 0; padding: 0; }
.track li { position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 0 4px; text-align: center; }
.track li:not(:last-child)::after { content: ''; position: absolute; top: 15px; left: calc(50% + 16px); right: calc(-50% + 16px); height: 3px; border-radius: 3px; background: #dce8e0; }
.track li.done:not(:last-child)::after { background: #1f9d55; }
.dot { position: relative; z-index: 1; width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; border: 2px solid #c9d8cf; background: #fff; color: #fff; box-sizing: border-box; }
.track li.done .dot { background: #1f9d55; border-color: #1f9d55; box-shadow: 0 0 0 4px #e3f4ea; }
.track li.stopped .dot { background: #8a9a91; border-color: #8a9a91; box-shadow: 0 0 0 4px #f1f4f2; }
.track li.todo .dot { box-shadow: 0 0 0 4px #f7faf8; }
.step-text { display: flex; flex-direction: column; gap: 2px; }
.step-text strong { font-size: 14px; color: #0e3a2c; }
.step-text span { font-size: 12.5px; font-weight: 600; color: #8a9a91; }
.track li.todo .step-text strong { color: #6b7d73; font-weight: 600; }

/* notes */
.reason { display: flex; gap: 12px; margin: 22px 0 0; padding: 14px 16px; border-radius: 14px; font-size: 14.5px; line-height: 1.5; }
.reason + .reason { margin-top: 10px; }
.reason > .ic { margin-top: 1px; }
.plain-note.reason { background: #f7faf8; border: 1px solid #e3ebe6; color: #4a5a52; }
.plain-note.reason > .ic { color: #1f7a4d; }
.attend-warn { background: #fef3f2; border: 1px solid #f6cfcb; border-left: 1px solid #f6cfcb; border-radius: 14px; color: #8c1d2c; }
.attend-warn > .ic { color: #b42318; }

/* invoice + payment */
.facts { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin: 22px 0 0; }
.facts > div { display: grid; grid-template-columns: 44px minmax(0, 1fr); grid-template-rows: auto auto; column-gap: 14px; align-items: center; min-width: 0; padding: 16px 18px; border: 1.5px solid #c9d8cf; border-radius: 16px; }
.facts .wide { grid-column: 1 / -1; }
.af-ico { grid-row: 1 / 3; width: 44px; height: 44px; border-radius: 12px; background: #f1f6f2; color: #1f7a4d; display: inline-flex; align-items: center; justify-content: center; }
.af-ico.gold { background: #fff4d6; color: #8a6500; }
.af-ico.muted { background: #f3f6f4; color: #8a9a91; }
.facts dt { margin: 0; font-size: 13px; color: #8a9a91; }
.facts dd { margin: 0; font-size: 16px; font-weight: 700; color: #0e3a2c; overflow-wrap: anywhere; }
.facts dd.muted { font-weight: 500; color: #8a9a91; }
.facts .nm-text-link { color: #1f7a4d; }
.started { margin: 14px 0 0; }
.detail .am-foot { flex-shrink: 0; display: flex; justify-content: flex-end; gap: 10px; margin: 0; padding: 18px 30px; border-top: 1px solid #eef2ef; background: #f7faf8; }
.am-foot > button { display: inline-flex; align-items: center; justify-content: center; gap: 7px; height: 48px; padding: 0 26px; border-radius: 12px; font-family: inherit; font-size: 14px; font-weight: 800; cursor: pointer; }
.am-foot .nm-btn-soft { background: #004d3a; border: 1px solid #004d3a; color: #fff; }
.am-foot .nm-btn-danger { background: #fff; border: 1px solid #f2c4be; color: #b42318; box-shadow: none; }
.am-foot .nm-btn-danger:hover { background: #fdecea; }
.detail.nm-modal, .detail { border-radius: 24px; }

@media (max-width: 1100px) {
  .glance { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 900px) {
  .ap-hero { padding: 20px 18px; border-radius: 22px; }
  .ap-title { font-size: 24px; }
  .ap-plate { width: 180px; height: 180px; right: -60px; top: 20px; transform: none; }
  .ap-hero-txt { max-width: 72%; }
  .glance { gap: 10px; }
  .fig { grid-template-columns: 1fr; padding: 14px; }
  .fig-ico { grid-row: auto; width: 34px; height: 34px; margin-bottom: 8px; }
  .fig strong { font-size: 24px; }
  .fig-label { font-size: 13px; }
  .fig-note { font-size: 11.5px; }
  .ap-tabs { display: flex; width: 100%; border-radius: 16px; }
  .agenda-cols { display: none; }
  .agenda-head { padding: 14px 16px; }
  .day-title { padding: 10px 16px; }
  .appt { grid-template-columns: minmax(0, 1fr) 30px; gap: 8px 12px; padding: 14px 16px; }
  .appt::before { top: 14px; bottom: 14px; }
  .appt-time { grid-column: 1; }
  .appt-people, .appt-state, .appt-pay { grid-column: 1; }
  .appt-state { flex-direction: row; flex-wrap: wrap; align-items: center; }
  .appt-go { grid-column: 2; grid-row: 1; }
}
@media (max-width: 760px) {
  .nm-page { padding-bottom: 110px; }
}
@media (max-width: 640px) {
  .appt-tools { width: 100%; }
  .appt-tools .ap-search { flex: 1 1 100%; width: auto; order: -1; }
  .ap-sel { flex: 1; }
  .dates { width: 100%; }
  .date-field { flex: 1; }
  .date-field :deep(.df-trigger) { flex: 1; min-width: 0; }
  .people, .facts { grid-template-columns: 1fr; }
  .nm-modal.detail { max-height: calc(100dvh - 24px); border-radius: 22px; }
  .am-head { flex-wrap: wrap; padding: 18px; }
  .detail .am-head .nm-modal-title { font-size: 19px; }
  .am-plate { width: 150px; height: 150px; right: -50px; }
  .am-st { order: 5; }
  .am-body { padding: 16px 18px; }
  .track { grid-template-columns: 1fr; gap: 12px; }
  .track li { flex-direction: row; align-items: flex-start; gap: 10px; padding: 0; text-align: left; }
  .track li:not(:last-child)::after { top: 30px; left: 13px; right: auto; bottom: -12px; width: 3px; height: auto; }
  .detail .am-foot { padding: 12px 18px 16px; }
  .am-foot > button { flex: 1; }
}
.rs-history { margin: 6px 0 0; padding-left: 18px; }
.rs-history li { margin: 2px 0; overflow-wrap: anywhere; }
</style>