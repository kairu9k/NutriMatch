<template>
  <div class="sw" :class="{ hidden: covered && !open }">
    <!-- PANEL -->
    <Transition name="sw-pop">
      <section v-if="open" ref="panel" class="sw-panel" role="dialog" aria-modal="false" aria-labelledby="sw-title" @keydown.esc="close">
        <header class="sw-head">
          <button v-if="view === 'thread' || view === 'sent'" type="button" class="sw-icon" aria-label="Back" @click="backToList"><ArrowLeft :size="17" /></button>
          <div class="sw-head-text">
            <h2 id="sw-title">{{ view === 'thread' && ticket ? ticket.subject : 'Help & Support' }}</h2>
            <p>{{ view === 'thread' && ticket ? `${ticket.reference}, ${ticket.category_label.toLowerCase()}` : 'We usually reply within 24 hours.' }}</p>
          </div>
          <button type="button" class="sw-icon" aria-label="Close help" @click="close"><X :size="18" /></button>
        </header>

        <nav v-if="view === 'home'" class="sw-tabs" role="tablist">
          <button v-for="t in TABS" :key="t.key" type="button" role="tab" class="sw-tab" :class="{ on: tab === t.key }" :aria-selected="tab === t.key" @click="tab = t.key">
            {{ t.label }}<span v-if="t.key === 'requests' && unread" class="sw-count">{{ unread }}</span>
          </button>
        </nav>

        <div class="sw-body">
          <!-- QUICK ANSWERS -->
          <template v-if="view === 'home' && tab === 'help'">
            <div class="sw-search">
              <Search :size="14" aria-hidden="true" />
              <input v-model="faqQuery" class="nm-input" type="search" placeholder="Search quick answers" aria-label="Search quick answers" />
            </div>
            <div v-for="(f, n) in faqShown" :key="f.q" class="faq" :class="{ on: faqOpen === n }">
              <button type="button" class="faq-q" :aria-expanded="faqOpen === n" @click="faqOpen = faqOpen === n ? null : n">
                <span>{{ f.q }}</span><ChevronDown :size="15" />
              </button>
              <div v-if="faqOpen === n" class="faq-a">
                <p>{{ f.a }}</p>
                <NuxtLink v-if="f.link" :to="f.link.to" class="nm-panel-link" @click="close">{{ f.link.label }}</NuxtLink>
              </div>
            </div>
            <p v-if="!faqShown.length" class="nm-muted">No quick answer matches that.</p>
            <div class="sw-cta">
              <p>Still need help?</p>
              <button type="button" class="nm-btn-dark nm-btn-sm" @click="tab = 'contact'"><MessageSquarePlus :size="14" /> Contact support</button>
            </div>
          </template>

          <!-- CONTACT SUPPORT -->
          <form v-else-if="view === 'home' && tab === 'contact'" class="sw-form" @submit.prevent="submit">
            <label class="sw-field">
              <span>What's it about?</span>
              <select v-model="form.category" class="nm-select block" required>
                <option value="" disabled>Choose a topic</option>
                <option v-for="c in SUPPORT_CATEGORIES" :key="c.value" :value="c.value">{{ c.label }}</option>
              </select>
            </label>
            <label v-if="links.appointments.length && ['appointment', 'payment', 'report'].includes(form.category)" class="sw-field">
              <span>Related appointment <em>(optional)</em></span>
              <select v-model="form.appointment" class="nm-select block">
                <option :value="null">None</option>
                <option v-for="a in links.appointments" :key="a.id" :value="a.id">{{ a.label }}</option>
              </select>
            </label>
            <label v-if="links.invoices.length && form.category === 'payment'" class="sw-field">
              <span>Related invoice <em>(optional)</em></span>
              <select v-model="form.invoice" class="nm-select block">
                <option :value="null">None</option>
                <option v-for="i in links.invoices" :key="i.id" :value="i.id">{{ i.label }}</option>
              </select>
            </label>
            <label class="sw-field">
              <span>Subject</span>
              <input v-model="form.subject" class="nm-input" maxlength="150" placeholder="e.g. I was charged twice" required />
            </label>
            <label class="sw-field">
              <span>Message</span>
              <textarea v-model="form.message" data-allow-emoji class="nm-input" rows="5" maxlength="3000" placeholder="Tell us what happened, with dates or reference numbers if you have them." required></textarea>
              <small class="sw-count-text">{{ form.message.length }}/3000</small>
            </label>
            <p v-if="formError" class="nm-error">{{ formError }}</p>
            <button type="submit" class="nm-btn-dark sw-submit" :disabled="sending || !canSubmit"><Send :size="14" /> {{ sending ? 'Sending…' : 'Send to NutriMatch Support' }}</button>
            <p class="nm-hint">Don't include passwords or card numbers. We reply here and by email.</p>
          </form>

          <!-- MY REQUESTS -->
          <template v-else-if="view === 'home' && tab === 'requests'">
            <p v-if="loadingList" class="nm-muted">Loading…</p>
            <div v-else-if="!tickets.length" class="sw-empty">
              <Inbox :size="26" />
              <p>No requests yet.</p>
              <button type="button" class="nm-btn-outline nm-btn-sm" @click="tab = 'contact'">Contact support</button>
            </div>
            <button v-for="t in tickets" :key="t.id" type="button" class="req" :class="{ unread: t.unread }" @click="openTicket(t.id)">
              <span class="req-top">
                <span class="req-subject">{{ t.subject }}</span>
                <span class="nm-pill" :class="STATUS_PILL[t.status]">{{ t.status_label }}</span>
              </span>
              <span class="req-preview">{{ t.last_message ? `${t.last_message.from_support ? 'Support: ' : 'You: '}${t.last_message.body}` : '' }}</span>
              <span class="req-meta">{{ t.reference }}, {{ ago(t.last_activity_at) }}<span v-if="t.unread" class="req-dot">New reply</span></span>
            </button>
          </template>

          <!-- SENT -->
          <div v-else-if="view === 'sent'" class="sw-sent">
            <CheckCircle2 :size="34" />
            <h3>Request sent</h3>
            <p>Your reference is <strong>{{ ticket?.reference }}</strong>. We'll reply here and email you at {{ auth.user?.email }}.</p>
            <button type="button" class="nm-btn-outline nm-btn-sm" @click="view = 'thread'">View request</button>
          </div>

          <!-- THREAD -->
          <template v-else-if="view === 'thread'">
            <p v-if="!ticket" class="nm-muted">Loading…</p>
            <template v-else>
              <div class="thread-info">
                <span class="nm-pill" :class="STATUS_PILL[ticket.status]">{{ ticket.status_label }}</span>
                <span v-if="ticket.appointment" class="thread-link"><CalendarCheck :size="13" /> {{ ticket.appointment.label }}</span>
                <span v-if="ticket.invoice" class="thread-link"><Receipt :size="13" /> {{ ticket.invoice.label }}</span>
              </div>
              <div ref="threadBox" class="thread">
                <div v-for="m in ticket.messages" :key="m.id" class="msg" :class="{ support: m.from_support }">
                  <p class="msg-who">{{ m.from_support ? m.sender_name : 'You' }}, {{ when(m.created_at) }}</p>
                  <p class="msg-body">{{ m.body }}</p>
                </div>
              </div>
              <p v-if="ticket.status === 'closed'" class="nm-hint">This request is closed. Replying reopens it.</p>
              <form class="reply" @submit.prevent="sendReply">
                <textarea v-model="reply" data-allow-emoji class="nm-input" rows="2" maxlength="3000" :placeholder="ticket.status === 'closed' ? 'Reply to reopen…' : 'Write a reply…'" aria-label="Reply"></textarea>
                <button type="submit" class="nm-btn-dark" :disabled="sending || reply.trim().length < 2" aria-label="Send reply"><Send :size="15" /></button>
              </form>
              <p v-if="formError" class="nm-error">{{ formError }}</p>
              <button v-if="ticket.status !== 'closed'" type="button" class="nm-panel-link sw-close-req" @click="closeTicket">Mark as resolved</button>
            </template>
          </template>
        </div>
      </section>
    </Transition>

    <!-- FLOATING BUTTON -->
    <button type="button" class="sw-fab" :class="{ on: open }" :aria-label="open ? 'Close help' : 'Help & Support'" :aria-expanded="open" @click="toggle">
      <X v-if="open" :size="22" />
      <Headset v-else :size="24" />
      <span v-if="unread && !open" class="sw-dot" aria-hidden="true"></span>
    </button>
  </div>
</template>

<script setup>
// Floating Help & Support button (bottom right) for clients and RNDs:
// Quick answers · Contact support · My requests, with the reply thread.
// Talks to /api/support/* (communication/support.py). Hides while another
// pop-up is open so it never covers its buttons; ?support=<id> opens a request.
import { ArrowLeft, CalendarCheck, CheckCircle2, ChevronDown, Headset, Inbox, MessageSquarePlus, Receipt, Search, Send, X } from 'lucide-vue-next'
import { SUPPORT_CATEGORIES, SUPPORT_FAQ } from '~/utils/supportFaq'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const { get, post } = useApi()

const TABS = [{ key: 'help', label: 'Quick answers' }, { key: 'contact', label: 'Contact support' }, { key: 'requests', label: 'My requests' }]
const STATUS_PILL = { open: 'gold', answered: 'green', closed: 'muted' }

const open = ref(false)
const view = ref('home') // home | thread | sent
const tab = ref('help')
const unread = ref(0)

/* ---------- quick answers ---------- */
const faqQuery = ref('')
const faqOpen = ref(null)
const faqShown = computed(() => {
  const list = SUPPORT_FAQ[auth.user?.role === 'rnd' ? 'rnd' : 'client']
  const q = faqQuery.value.trim().toLowerCase()
  return q ? list.filter(f => `${f.q} ${f.a}`.toLowerCase().includes(q)) : list
})
watch(faqQuery, () => { faqOpen.value = null })

/* ---------- contact ---------- */
const emptyForm = () => ({ category: '', subject: '', message: '', appointment: null, invoice: null })
const form = reactive(emptyForm())
const links = ref({ appointments: [], invoices: [] })
const sending = ref(false)
const formError = ref('')
const canSubmit = computed(() => form.category && form.subject.trim().length >= 5 && form.message.trim().length >= 10)
let linksLoaded = false
watch(tab, async (t) => {
  formError.value = ''
  if (t === 'contact' && !linksLoaded) {
    linksLoaded = true
    try { links.value = await get('/support/links/') } catch { /* optional */ }
  }
  if (t === 'requests') loadTickets()
})
async function submit() {
  if (!canSubmit.value) {
    formError.value = 'Add a subject (5+ characters) and a message (10+ characters).'
    return
  }
  sending.value = true
  formError.value = ''
  try {
    ticket.value = await post('/support/tickets/', { ...form, subject: form.subject.trim(), message: form.message.trim() })
    Object.assign(form, emptyForm())
    view.value = 'sent'
  } catch (e) {
    formError.value = apiMessage(e, 'Could not send your request. Please try again.')
  } finally {
    sending.value = false
  }
}

/* ---------- my requests ---------- */
const tickets = ref([])
const loadingList = ref(false)
async function loadTickets() {
  loadingList.value = !tickets.value.length
  try { tickets.value = await get('/support/tickets/') } catch { /* keep what we have */ } finally { loadingList.value = false }
}
const ticket = ref(null)
const reply = ref('')
const threadBox = ref(null)
async function openTicket(id) {
  view.value = 'thread'
  ticket.value = null
  reply.value = ''
  formError.value = ''
  try {
    ticket.value = await get(`/support/tickets/${id}/`)
    refreshUnread()
    scrollThread()
  } catch {
    formError.value = 'Could not open this request.'
  }
}
async function sendReply() {
  sending.value = true
  formError.value = ''
  try {
    ticket.value = await post(`/support/tickets/${ticket.value.id}/messages/`, { body: reply.value.trim() })
    reply.value = ''
    scrollThread()
  } catch (e) {
    formError.value = apiMessage(e, 'Could not send your reply.')
  } finally {
    sending.value = false
  }
}
async function closeTicket() {
  try { ticket.value = await post(`/support/tickets/${ticket.value.id}/close/`) } catch { formError.value = 'Could not close this request.' }
}
function scrollThread() {
  nextTick(() => { if (threadBox.value) threadBox.value.scrollTop = threadBox.value.scrollHeight })
}
function backToList() {
  view.value = 'home'
  tab.value = 'requests'
  loadTickets()
}

/* ---------- open / close / unread ---------- */
function toggle() { open.value ? close() : (open.value = true) }
function close() {
  open.value = false
  if (view.value === 'sent') view.value = 'home'
}
async function refreshUnread() {
  try { unread.value = (await get('/support/unread/')).count } catch { /* dot is optional */ }
}
let timer = null
onMounted(() => {
  refreshUnread()
  timer = setInterval(refreshUnread, 60000)
})
onBeforeUnmount(() => clearInterval(timer))
watch(() => route.path, refreshUnread)
// ?support=<id> (email link, notification) opens that request.
watch(() => route.query.support, (id) => {
  if (!id) return
  open.value = true
  openTicket(id)
  const { support, ...rest } = route.query
  router.replace({ query: rest })
}, { immediate: true })
defineExpose({ openTicket: (id) => { open.value = true; openTicket(id) } })

/* ---------- stay out of the way of other pop-ups ---------- */
const covered = ref(false)
let observer = null
onMounted(() => {
  const check = () => {
    covered.value = !!document.querySelector('.nm-modal-overlay, .modal-overlay, .welcome-overlay, .ml-overlay, .ncp-overlay, [aria-modal="true"]:not(.sw-panel)')
  }
  observer = new MutationObserver(check)
  observer.observe(document.body, { childList: true, subtree: true })
  check()
})
onBeforeUnmount(() => observer?.disconnect())

/* ---------- helpers ---------- */
function apiMessage(e, fallback) {
  const d = e?.data
  if (!d) return fallback
  if (typeof d.detail === 'string') return d.detail
  const first = Object.values(d).flat()[0]
  return typeof first === 'string' ? first : fallback
}
function ago(iso) {
  const s = Math.floor((Date.now() - new Date(iso)) / 1000)
  for (const [label, secs] of [['d', 86400], ['h', 3600], ['m', 60]]) {
    const v = Math.floor(s / secs)
    if (v >= 1) return `${v}${label} ago`
  }
  return 'just now'
}
function when(iso) {
  return new Date(iso).toLocaleString('en-PH', { timeZone: 'Asia/Manila', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}
</script>

<style scoped>
.sw { position: fixed; right: 22px; bottom: 22px; z-index: 250; display: flex; flex-direction: column; align-items: flex-end; gap: 12px; font-family: 'Inter', sans-serif; }
.sw.hidden { display: none; }
.sw-fab { position: relative; width: 56px; height: 56px; border-radius: 50%; border: none; background: linear-gradient(135deg, #00382a 0%, #005a42 100%); color: #fff; display: flex; align-items: center; justify-content: center; cursor: pointer; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22); transition: transform 0.15s ease; }
.sw-fab:hover { transform: translateY(-2px); }
.sw-fab:focus-visible { outline: 3px solid #1f8f5c; outline-offset: 2px; }
.sw-fab.on { background: #0a4a37; }
/* unread reply: the same yellow dot as the bell and Messages */
.sw-dot { position: absolute; top: 4px; right: 4px; width: 13px; height: 13px; border-radius: 50%; background: #D4A017; border: 2px solid #fff; }

.sw-panel { width: 380px; max-height: min(620px, calc(100vh - 110px)); background: #fff; border-radius: 16px; box-shadow: 0 0 2px rgba(0, 77, 58, 0.08), 0 0 24px rgba(0, 77, 58, 0.22); display: flex; flex-direction: column; overflow: hidden; color: #1a3a1a; }
.sw-head { display: flex; align-items: flex-start; gap: 8px; background: linear-gradient(135deg, #00382a 0%, #005a42 100%); color: #fff; padding: 16px 16px 14px; }
.sw-head-text { flex: 1; min-width: 0; }
.sw-head h2 { font-family: 'Playfair Display', serif; font-size: 1.08rem; margin: 0; overflow-wrap: anywhere; }
.sw-head p { font-size: 0.78rem; color: #cfe3d6; margin: 3px 0 0; }
.sw-icon { border: none; background: rgba(255, 255, 255, 0.12); color: #fff; width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; }
.sw-icon:hover { background: rgba(255, 255, 255, 0.22); }
.sw-icon:focus-visible { outline: 2px solid #fff; outline-offset: 1px; }
.sw-tabs { display: flex; border-bottom: 1px solid #d9e3dc; padding: 0 8px; }
.sw-tab { flex: 1; border: none; background: none; font-family: inherit; font-size: 0.78rem; font-weight: 600; color: #6a7a6a; padding: 11px 4px; border-bottom: 2px solid transparent; margin-bottom: -1px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 5px; }
.sw-tab.on { color: #0a4a37; border-bottom-color: #0a4a37; }
.sw-tab:focus-visible { outline: 2px solid #1f8f5c; outline-offset: -2px; }
.sw-count { font-size: 0.68rem; font-weight: 700; background: #D4A017; color: #1a3a1a; border-radius: 10px; padding: 1px 6px; }
.sw-body { padding: 14px 16px 16px; overflow-y: auto; flex: 1; }

.sw-search { position: relative; margin-bottom: 10px; }
.sw-search svg { position: absolute; left: 11px; top: 50%; transform: translateY(-50%); color: #8a9a8a; }
.sw-search .nm-input { padding-left: 32px; }
.faq { border: 1px solid #d9e3dc; border-radius: 10px; margin-bottom: 6px; }
.faq.on { border-color: #9ec4ad; }
.faq-q { display: flex; justify-content: space-between; align-items: center; gap: 8px; width: 100%; border: none; background: none; text-align: left; padding: 10px 12px; font-family: inherit; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; cursor: pointer; }
.faq-q svg { flex-shrink: 0; color: #6a7a6a; transition: transform 0.15s ease; }
.faq.on .faq-q svg { transform: rotate(180deg); }
.faq-a { padding: 0 12px 10px; }
.faq-a p { font-size: 0.8rem; color: #4a5a4a; line-height: 1.55; margin: 0 0 6px; }
.sw-cta { display: flex; align-items: center; justify-content: space-between; gap: 10px; border-top: 1px solid #d9e3dc; padding: 12px 0 0; margin-top: 12px; }
.sw-cta p { font-size: 0.8rem; font-weight: 600; margin: 0; }

.sw-form { display: flex; flex-direction: column; gap: 10px; }
.sw-field { display: flex; flex-direction: column; gap: 5px; font-size: 0.78rem; font-weight: 600; color: #1a3a1a; }
.sw-field em { font-style: normal; font-weight: 400; color: #8a9a8a; }
.sw-field textarea { resize: vertical; }
.sw-field input.nm-input { min-height: 42px; }
.sw-count-text { font-size: 0.7rem; font-weight: 400; color: #6a7a6a; text-align: right; }
.sw-submit { width: 100%; justify-content: center; }
.sw-form .nm-error { margin: 0; }

.sw-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; color: #6a7a6a; padding: 26px 0; font-size: 0.84rem; }
.sw-empty svg { color: #9ec4ad; }
.sw-empty p { margin: 0; }
.req { display: flex; flex-direction: column; gap: 3px; width: 100%; text-align: left; border: 1px solid #d9e3dc; background: #fff; border-radius: 10px; padding: 10px 12px; margin-bottom: 8px; cursor: pointer; font-family: inherit; }
.req:hover { border-color: #9ec4ad; background: #f7faf8; }
.req:focus-visible { outline: 2px solid #1f8f5c; outline-offset: 1px; }
.req.unread { border-color: #9ec4ad; background: #f2f8f4; }
.req-top { display: flex; justify-content: space-between; gap: 8px; align-items: flex-start; }
.req-subject { font-size: 0.84rem; font-weight: 600; color: #1a3a1a; overflow-wrap: anywhere; }
.req-preview { font-size: 0.76rem; color: #6a7a6a; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.req-meta { font-size: 0.72rem; color: #6a7a6a; display: flex; gap: 8px; align-items: center; }
.req-dot { color: #0a4a37; font-weight: 700; display: inline-flex; align-items: center; gap: 4px; }
.req-dot::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: #D4A017; }

.sw-sent { display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px; padding: 20px 6px; color: #1f8f5c; }
.sw-sent h3 { font-family: 'Playfair Display', serif; color: #1a3a1a; margin: 0; }
.sw-sent p { font-size: 0.82rem; color: #4a5a4a; line-height: 1.5; margin: 0 0 6px; }

.thread-info { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; margin-bottom: 10px; }
.thread-link { display: inline-flex; align-items: center; gap: 4px; font-size: 0.72rem; color: #5a6a5a; }
.thread { display: flex; flex-direction: column; gap: 8px; max-height: 300px; overflow-y: auto; padding-right: 2px; margin-bottom: 10px; }
/* same bubbles as Messages: yours dark green, support's light with a border */
.msg { align-self: flex-end; max-width: 88%; background: #0a4a37; color: #fff; border-radius: 12px 12px 4px 12px; padding: 8px 11px; }
.msg.support { align-self: flex-start; background: #f2f6f3; color: #1a3a1a; border: 1px solid #d9e3dc; border-radius: 12px 12px 12px 4px; }
.msg-who { font-size: 0.7rem; font-weight: 600; color: #cfe3d6; margin: 0 0 3px; }
.msg.support .msg-who { color: #4a5a4a; }
.msg-body { font-size: 0.82rem; color: inherit; line-height: 1.5; margin: 0; white-space: pre-line; overflow-wrap: anywhere; }
.reply { display: flex; gap: 8px; align-items: flex-end; }
.reply textarea { resize: none; flex: 1; }
.reply .nm-btn-dark { height: 40px; width: 44px; padding: 0; justify-content: center; }
.sw-close-req { display: block; margin: 10px auto 0; }

.sw-pop-enter-active, .sw-pop-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; transform-origin: bottom right; }
.sw-pop-enter-from, .sw-pop-leave-to { opacity: 0; transform: scale(0.96) translateY(6px); }
@media (prefers-reduced-motion: reduce) {
  .sw-fab, .sw-pop-enter-active, .sw-pop-leave-active, .faq-q svg { transition: none; }
  .sw-fab:hover { transform: none; }
}

@media (max-width: 560px) {
  .sw { right: 14px; bottom: 14px; }
  .sw-fab { width: 50px; height: 50px; }
  .sw-panel { position: fixed; inset: 0; width: auto; max-height: none; border-radius: 0; }
  .sw:has(.sw-panel) .sw-fab { display: none; }
  .thread { max-height: none; }
}
@media print { .sw { display: none; } }
</style>
