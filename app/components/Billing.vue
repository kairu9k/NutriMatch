<template>
  <div class="billing-page">
    <!-- PENDING PAYMENT -->
    <div v-if="pendingInvoice" class="pending-card">
      <span class="pending-eyebrow">Pending Payment</span>
      <div class="pending-row">
        <div>
          <p class="pending-title">{{ pendingInvoice.type }} — {{ pendingInvoice.date }}</p>
          <p class="pending-sub">{{ rndName }} · Invoice #{{ pendingInvoice.invoiceNo }}</p>
        </div>
        <p class="pending-amount">₱{{ pendingInvoice.amount.toLocaleString() }}</p>
      </div>
      <div class="pending-actions">
        <button class="pay-btn" @click="openPaymentModal"><Wallet :size="15" /> Pay Now</button>
        <button class="outline-btn" @click="downloadInvoice(pendingInvoice)"><Download :size="14" /> Download Invoice</button>
      </div>
    </div>

    <!-- PAYMENT HISTORY -->
    <h3 class="section-title">Payment History</h3>
    <div class="history-list">
      <div v-for="(item, i) in paymentHistory" :key="i" class="history-row">
        <div class="history-icon"><span>₱</span></div>
        <div class="history-info">
          <p class="history-title">{{ item.type }}</p>
          <p class="history-sub">{{ item.date }} · {{ item.method }}</p>
        </div>
        <div class="history-right">
          <p class="history-amount">₱{{ item.amount.toLocaleString() }}</p>
          <span class="status-pill pill-green">Paid</span>
        </div>
      </div>
    </div>

    <p class="total-paid-note">Total paid to {{ rndName }}: <strong>₱{{ totalPaid.toLocaleString() }}</strong></p>

    <!-- PAYMENT MODAL -->
    <div v-if="paymentModalOpen" class="modal-overlay" @click.self="closePaymentModal">
      <div class="modal-box">
        <div class="modal-title-row">
          <h3 class="modal-title">
            {{ paymentStep === 'invoice' ? 'Payment Details' : paymentStep === 'summary' ? 'Confirm Payment' : 'Pay Invoice' }}
          </h3>
          <button class="modal-close-btn" @click="closePaymentModal"><X :size="18" /></button>
        </div>

        <!-- STEP 0: INVOICE DETAILS -->
        <template v-if="paymentStep === 'invoice' && pendingInvoice">
          <div class="invoice-detail-block">
            <div class="invoice-detail-row"><span>Service</span><strong>{{ pendingInvoice.type }}</strong></div>
            <div class="invoice-detail-row"><span>Billed to</span><strong>{{ rndName }}</strong></div>
            <div class="invoice-detail-row"><span>Session Date</span><strong>{{ pendingInvoice.date }}</strong></div>
            <div class="invoice-detail-row"><span>Invoice #</span><strong>{{ pendingInvoice.invoiceNo }}</strong></div>
          </div>
          <div class="due-row">
            <span>Amount Due</span>
            <strong>₱{{ pendingInvoice.amount.toLocaleString() }}</strong>
          </div>
          <button class="pay-now-btn" @click="paymentStep = 'method'">Continue to Payment</button>
          <button class="ghost-btn full-width" @click="closePaymentModal">Cancel</button>
        </template>

        <!-- STEP 1: PAYMENT METHOD -->
        <template v-if="paymentStep === 'method'">
        <p class="modal-sub" v-if="pendingInvoice">{{ pendingInvoice.type }} — {{ rndName }}</p>

        <div class="method-list">
          <!-- CARD OPTION -->
          <div class="method-option" :class="{ open: selectedMethod === 'card' }">
            <button class="method-option-head" @click="selectedMethod = selectedMethod === 'card' ? '' : 'card'">
              <span class="radio-dot" :class="{ checked: selectedMethod === 'card' }"></span>
              <span class="method-option-label">Credit or Debit Card</span>
              <span class="card-network-icons">
                <span class="network-chip visa">VISA</span>
                <span class="network-chip mc">Mastercard</span>
                <span class="network-chip amex">Amex</span>
              </span>
            </button>

            <div v-if="selectedMethod === 'card'" class="method-option-body">
              <div class="card-preview" :class="{ filled: cardForm.number }">
                <div class="card-preview-top">
                  <span class="card-chip"></span>
                  <component :is="CreditCard" :size="20" style="opacity: 0.85;" />
                </div>
                <p class="card-preview-number">{{ cardForm.number || '•••• •••• •••• ••••' }}</p>
                <div class="card-preview-bottom">
                  <div>
                    <span class="card-preview-label">Card Holder</span>
                    <p class="card-preview-value">{{ cardForm.name || 'YOUR NAME' }}</p>
                  </div>
                  <div>
                    <span class="card-preview-label">Expires</span>
                    <p class="card-preview-value">{{ cardForm.expiry || 'MM/YY' }}</p>
                  </div>
                </div>
              </div>

              <label class="field-label">Cardholder Name</label>
              <input v-model="cardForm.name" type="text" placeholder="Juan Dela Cruz" class="modal-input" />
              <label class="field-label">Card Number</label>
              <input :value="cardForm.number" @input="onCardNumberInput" type="text" inputmode="numeric" placeholder="1234 1234 1234 1234" maxlength="19" class="modal-input" />
              <div class="modal-row-2">
                <div>
                  <label class="field-label">Expiration Date</label>
                  <input :value="cardForm.expiry" @input="onExpiryInput" type="text" inputmode="numeric" placeholder="MM/YY" maxlength="5" class="modal-input" />
                </div>
                <div>
                  <label class="field-label">Security Code</label>
                  <input v-model="cardForm.cvv" type="password" inputmode="numeric" placeholder="CVC" maxlength="4" class="modal-input" />
                </div>
              </div>
            </div>
          </div>

          <!-- GCASH OPTION -->
          <div class="method-option" :class="{ open: selectedMethod === 'gcash' }">
            <button class="method-option-head" @click="selectedMethod = selectedMethod === 'gcash' ? '' : 'gcash'">
              <span class="radio-dot" :class="{ checked: selectedMethod === 'gcash' }" :style="selectedMethod === 'gcash' ? { borderColor: '#0072E3' } : {}"></span>
              <span class="method-option-label">GCash</span>
              <span class="wallet-badge gcash-badge">GCash</span>
            </button>
            <div v-if="selectedMethod === 'gcash'" class="method-option-body">
              <div class="wallet-mode-tabs">
                <button class="wallet-mode-tab" :class="{ active: walletMode === 'number' }" @click="walletMode = 'number'">Enter Number</button>
                <button class="wallet-mode-tab" :class="{ active: walletMode === 'qr' }" @click="walletMode = 'qr'">Scan QR</button>
              </div>
              <template v-if="walletMode === 'number'">
                <label class="field-label">GCash Mobile Number</label>
                <div class="phone-input-wrap">
                  <span class="phone-prefix">+63</span>
                  <input v-model="walletForm.mobile" type="tel" inputmode="numeric" placeholder="9XX XXX XXXX" maxlength="10" class="modal-input phone-input" />
                </div>
                <p class="wallet-note">You'll confirm this payment in the GCash app.</p>
              </template>
              <template v-else>
                <div class="qr-box"><QrCode :size="90" /></div>
                <p class="wallet-note qr-note">Open your GCash app and scan this code to pay ₱{{ pendingInvoice ? pendingInvoice.amount.toLocaleString() : 0 }}.</p>
              </template>
            </div>
          </div>

          <!-- MAYA OPTION -->
          <div class="method-option" :class="{ open: selectedMethod === 'maya' }">
            <button class="method-option-head" @click="selectedMethod = selectedMethod === 'maya' ? '' : 'maya'">
              <span class="radio-dot" :class="{ checked: selectedMethod === 'maya' }" :style="selectedMethod === 'maya' ? { borderColor: '#00A868' } : {}"></span>
              <span class="method-option-label">Maya</span>
              <span class="wallet-badge maya-badge">maya</span>
            </button>
            <div v-if="selectedMethod === 'maya'" class="method-option-body">
              <div class="wallet-mode-tabs">
                <button class="wallet-mode-tab" :class="{ active: walletMode === 'number' }" @click="walletMode = 'number'">Enter Number</button>
                <button class="wallet-mode-tab" :class="{ active: walletMode === 'qr' }" @click="walletMode = 'qr'">Scan QR</button>
              </div>
              <template v-if="walletMode === 'number'">
                <label class="field-label">Maya Mobile Number</label>
                <div class="phone-input-wrap">
                  <span class="phone-prefix">+63</span>
                  <input v-model="walletForm.mobile" type="tel" inputmode="numeric" placeholder="9XX XXX XXXX" maxlength="10" class="modal-input phone-input" />
                </div>
                <p class="wallet-note">You'll confirm this payment in the Maya app.</p>
              </template>
              <template v-else>
                <div class="qr-box"><QrCode :size="90" /></div>
                <p class="wallet-note qr-note">Open your Maya app and scan this code to pay ₱{{ pendingInvoice ? pendingInvoice.amount.toLocaleString() : 0 }}.</p>
              </template>
            </div>
          </div>

          <!-- ONLINE BANKING OPTION -->
          <div class="method-option" :class="{ open: selectedMethod === 'bank' }">
            <button class="method-option-head" @click="selectedMethod = selectedMethod === 'bank' ? '' : 'bank'">
              <span class="radio-dot" :class="{ checked: selectedMethod === 'bank' }"></span>
              <span class="method-option-label">Online Banking</span>
              <span class="bank-hint">BDO · BPI · Landbank +more</span>
            </button>
            <div v-if="selectedMethod === 'bank'" class="method-option-body">
              <label class="field-label">Select Your Bank</label>
              <div class="bank-grid">
                <button
                  v-for="b in banks" :key="b.key"
                  class="bank-tile" :class="{ active: bankForm.bank === b.key }"
                  :style="bankForm.bank === b.key ? { borderColor: b.color } : {}"
                  @click="bankForm.bank = b.key"
                >
                  <span class="bank-tile-accent" :style="{ background: b.color }"></span>
                  <span class="bank-tile-name">{{ b.label }}</span>
                </button>
              </div>
              <p v-if="bankForm.bank" class="wallet-note">You'll be redirected to {{ banks.find(b => b.key === bankForm.bank)?.label }}'s online banking to complete this payment.</p>
            </div>
          </div>
        </div>

        <div class="due-row">
          <span>Due Today</span>
          <strong>₱{{ pendingInvoice ? pendingInvoice.amount.toLocaleString() : 0 }}</strong>
        </div>

        <button class="pay-now-btn" :disabled="!canConfirmPayment" @click="paymentStep = 'summary'">
          Review Payment
        </button>
        <button class="ghost-btn full-width" @click="closePaymentModal">Cancel</button>
        </template>

        <!-- STEP 2: SUMMARY -->
        <template v-else-if="paymentStep === 'summary' && pendingInvoice">
          <div class="summary-block">
            <div class="summary-row"><span>Billed to</span><strong>{{ rndName }}</strong></div>
            <div class="summary-row"><span>Service</span><strong>{{ pendingInvoice.type }}</strong></div>
            <div class="summary-row"><span>Date</span><strong>{{ pendingInvoice.date }}</strong></div>
            <div class="summary-row"><span>Invoice #</span><strong>{{ pendingInvoice.invoiceNo }}</strong></div>
            <div class="summary-divider"></div>
            <div class="summary-row">
              <span>Payment Method</span>
              <strong class="summary-method"><span class="summary-method-dot" :style="{ background: activeMethod.color }"></span>{{ paymentMethodDetail }}</strong>
            </div>
            <div class="summary-divider"></div>
            <div class="summary-row total"><span>Amount</span><span>₱{{ pendingInvoice.amount.toLocaleString() }}</span></div>
          </div>

          <div class="modal-actions">
            <button class="ghost-btn" @click="paymentStep = 'method'">Back</button>
            <button class="primary-btn" @click="confirmPayment" :style="{ background: '#1f8f5c', color: '#fff' }">
              Confirm &amp; Pay ₱{{ pendingInvoice.amount.toLocaleString() }}
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- TOAST -->
    <Transition name="toast-fade">
      <div v-if="toastVisible" class="toast">
        <CheckCircle2 :size="16" /> {{ toastMessage }}
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { Wallet, Download, CheckCircle2, X, CreditCard, Smartphone, QrCode } from 'lucide-vue-next'

// TODO: pull from the client's actual assigned RND once that endpoint exists.
const rndName = 'RND Ivy Hope Alba'

// TODO: local mock data — move into the shared mock db (db.billing)
// once the client-side data model is defined, and swap in a real API call.
const pendingInvoice = ref({ type: 'Video Consultation', date: 'Jul 4, 2026', invoiceNo: 'INV-0231', amount: 800 })

const paymentHistory = ref([
  { type: 'Video Consultation', date: 'Jun 15, 2026', method: 'GCash', amount: 800 },
  { type: 'Chat Consultation', date: 'May 20, 2026', method: 'GCash', amount: 800 }
])

const totalPaid = computed(() => paymentHistory.value.reduce((sum, p) => sum + p.amount, 0))

/* ---------- PAYMENT MODAL ---------- */
const paymentModalOpen = ref(false)
const methods = [
  { key: 'card', label: 'Card', icon: CreditCard, color: '#1a3a1a', tint: '#eef3ee' },
  { key: 'gcash', label: 'GCash', icon: Smartphone, color: '#0072E3', tint: '#e6f1fd' },
  { key: 'maya', label: 'Maya', icon: Smartphone, color: '#00A868', tint: '#e3f6ec' },
  { key: 'bank', label: 'Online Banking', icon: Wallet, color: '#003DA5', tint: '#e6ecf7' }
]
const selectedMethod = ref('')
const paymentStep = ref('details')
const activeMethod = computed(() => methods.find(m => m.key === selectedMethod.value) || {})
const cardForm = reactive({ name: '', number: '', expiry: '', cvv: '' })
const walletForm = reactive({ mobile: '' })
const walletMode = ref('number')

const banks = [
  { key: 'bdo', label: 'BDO', short: 'BDO', color: '#003DA5', tint: '#e6ecf7' },
  { key: 'bpi', label: 'BPI', short: 'BPI', color: '#9E1B32', tint: '#f7e9eb' },
  { key: 'landbank', label: 'Landbank', short: 'LBP', color: '#00693E', tint: '#e3f0e9' },
  { key: 'metrobank', label: 'Metrobank', short: 'MB', color: '#003876', tint: '#e6ecf5' },
  { key: 'unionbank', label: 'UnionBank', short: 'UB', color: '#F7941D', tint: '#fdf1e0' },
  { key: 'securitybank', label: 'Security Bank', short: 'SB', color: '#0072BC', tint: '#e6f1fa' }
]
const bankForm = reactive({ bank: '' })

const paymentMethodDetail = computed(() => {
  if (selectedMethod.value === 'card') {
    const last4 = cardForm.number.replace(/\s/g, '').slice(-4)
    return `Card ending in ${last4}`
  }
  if (selectedMethod.value === 'gcash' || selectedMethod.value === 'maya') {
    if (walletMode.value === 'qr') return `${activeMethod.value.label} — QR Code`
    const m = walletForm.mobile
    return `${activeMethod.value.label} — +63 ${m.slice(0, 3)} ${m.slice(3)}`
  }
  if (selectedMethod.value === 'bank') {
    return banks.find(b => b.key === bankForm.bank)?.label || ''
  }
  return ''
})

function onCardNumberInput(e) {
  const digits = e.target.value.replace(/\D/g, '').slice(0, 16)
  cardForm.number = digits.replace(/(.{4})/g, '$1 ').trim()
}
function onExpiryInput(e) {
  let digits = e.target.value.replace(/\D/g, '').slice(0, 4)
  if (digits.length >= 3) digits = digits.slice(0, 2) + '/' + digits.slice(2)
  cardForm.expiry = digits
}

function openPaymentModal() {
  selectedMethod.value = ''
  paymentStep.value = 'invoice'
  walletMode.value = 'number'
  cardForm.name = ''; cardForm.number = ''; cardForm.expiry = ''; cardForm.cvv = ''
  walletForm.mobile = ''
  bankForm.bank = ''
  paymentModalOpen.value = true
}
function closePaymentModal() {
  paymentModalOpen.value = false
}

const canConfirmPayment = computed(() => {
  if (selectedMethod.value === 'card') {
    return cardForm.name.trim() !== '' && cardForm.number.replace(/\s/g, '').length === 16 && cardForm.expiry.length === 5 && cardForm.cvv.trim().length >= 3
  }
  if (selectedMethod.value === 'gcash' || selectedMethod.value === 'maya') {
    if (walletMode.value === 'qr') return true
    return walletForm.mobile.trim().length === 10
  }
  if (selectedMethod.value === 'bank') {
    return bankForm.bank !== ''
  }
  return false
})

const toastVisible = ref(false)
const toastMessage = ref('')
let toastTimer = null
function fireToast(msg) {
  toastMessage.value = msg
  toastVisible.value = true
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastVisible.value = false }, 3500)
}

function confirmPayment() {
  if (!canConfirmPayment.value || !pendingInvoice.value) return
  const methodLabel = selectedMethod.value === 'bank'
    ? (banks.find(b => b.key === bankForm.bank)?.label || 'Online Banking')
    : (activeMethod.value.label || selectedMethod.value)
  // TODO: wire up to a real payment gateway (card processor / GCash / Maya API / bank redirect)
  paymentHistory.value.unshift({
    type: pendingInvoice.value.type, date: pendingInvoice.value.date, method: methodLabel, amount: pendingInvoice.value.amount
  })
  fireToast(`${pendingInvoice.value.invoiceNo} paid via ${methodLabel}!`)
  pendingInvoice.value = null
  closePaymentModal()
}

function downloadInvoice(inv) {
  // TODO: wire up to a real invoice PDF download
  console.log('Download invoice', inv.invoiceNo)
}
</script>

<style scoped>
* { box-sizing: border-box; }
.billing-page { font-family: 'Inter', sans-serif; }

/* PENDING PAYMENT */
.pending-card { background: #fdf1d6; border-left: 4px solid #D4A017; border-radius: 14px; padding: 22px 24px; margin-bottom: 24px; }
.pending-eyebrow { display: block; font-size: 0.76rem; font-weight: 700; color: #b8860b; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 10px; }
.pending-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 18px; }
.pending-title { font-size: 1rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.pending-sub { font-size: 0.82rem; color: #8a9a8a; margin: 4px 0 0; }
.pending-amount { font-family: 'Playfair Display', serif; font-size: 1.6rem; font-weight: 700; color: #1f8f5c; margin: 0; white-space: nowrap; }
.pending-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.pay-btn { display: inline-flex; align-items: center; gap: 8px; background: #1f8f5c; color: #fff; border: none; border-radius: 999px; padding: 12px 24px; font-weight: 700; font-size: 0.87rem; cursor: pointer; }
.pay-btn:hover { background: #197a4d; }
.outline-btn { display: inline-flex; align-items: center; gap: 7px; background: #fff; color: #1a3a1a; border: 1px solid #e5d7ae; border-radius: 999px; padding: 12px 22px; font-weight: 600; font-size: 0.87rem; cursor: pointer; }

/* PAYMENT HISTORY */
.section-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 14px; }
.history-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; }
.history-row { display: flex; align-items: center; gap: 14px; background: #f7f9f7; border-radius: 12px; padding: 16px 18px; }
.history-icon { width: 36px; height: 36px; border-radius: 9px; background: #e3f3ea; color: #1f8f5c; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.history-info { flex: 1; }
.history-title { font-size: 0.9rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.history-sub { font-size: 0.78rem; color: #9aaa9a; margin: 3px 0 0; }
.history-right { text-align: right; }
.history-amount { font-weight: 700; color: #1f8f5c; margin: 0; }
.status-pill { display: inline-block; font-size: 0.72rem; font-weight: 700; padding: 3px 10px; border-radius: 12px; margin-top: 3px; }
.pill-green { background: #e3f3ea; color: #1f8f5c; }

.total-paid-note { text-align: center; font-size: 0.87rem; color: #8a9a8a; }
.total-paid-note strong { color: #1a3a1a; }

/* PAYMENT MODAL */
.modal-overlay { position: fixed; inset: 0; background: rgba(20,30,20,0.45); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 16px; }
.modal-box { background: #fff; border-radius: 18px; padding: 26px 30px; width: 100%; max-width: 560px; max-height: 90vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.25); }
.modal-title-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 4px; }
.modal-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0; }
.modal-close-btn { border: none; background: none; color: #9aaa9a; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 2px; flex-shrink: 0; }
.modal-sub { font-size: 0.85rem; color: #8a9a8a; margin: 0 0 18px; }

/* INVOICE DETAILS STEP */
.invoice-detail-block { background: #f7f9f7; border-radius: 12px; padding: 18px 20px; margin-bottom: 16px; }
.invoice-detail-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 0.85rem; padding: 9px 0; color: #6a7a6a; border-top: 1px solid #eceeec; }
.invoice-detail-row:first-child { border-top: none; padding-top: 0; }
.invoice-detail-row:last-child { padding-bottom: 0; }
.invoice-detail-row strong { color: #1a3a1a; font-weight: 700; }

.field-label { display: block; font-size: 0.76rem; font-weight: 700; color: #6a7a6a; margin: 0 0 8px; text-transform: uppercase; letter-spacing: 0.05em; }

/* RADIO ACCORDION LIST */
.method-list { border: 1px solid #eceeec; border-radius: 12px; overflow: hidden; margin-bottom: 18px; }
.method-option { border-bottom: 1px solid #eceeec; }
.method-option:last-child { border-bottom: none; }
.method-option-head {
  width: 100%; display: flex; align-items: center; gap: 12px; border: none; background: #fff; cursor: pointer;
  padding: 16px; text-align: left; transition: background 0.15s;
}
.method-option-head:hover { background: #fafbfa; }
.method-option.open .method-option-head { background: #f7f9f7; }
.radio-dot { width: 20px; height: 20px; border-radius: 50%; border: 2px solid #d5dad5; flex-shrink: 0; position: relative; transition: border-color 0.15s; }
.radio-dot.checked { border-color: #1f8f5c; }
.radio-dot.checked::after { content: ''; position: absolute; inset: 4px; border-radius: 50%; background: #1f8f5c; }
.method-option-label { flex: 1; font-size: 0.88rem; font-weight: 700; color: #1a3a1a; }
.card-network-icons { display: flex; gap: 6px; }
.network-chip { font-size: 0.65rem; font-weight: 800; border-radius: 5px; padding: 4px 8px; letter-spacing: 0.01em; }
.network-chip.visa { color: #1434CB; background: #eef0fb; }
.network-chip.mc { color: #eb001b; background: #fdeaec; }
.network-chip.amex { color: #016fd0; background: #e6f2fb; }
.wallet-badge {
  padding: 5px 12px; border-radius: 999px; color: #fff; font-size: 0.82rem; font-weight: 800; display: flex; align-items: center;
  justify-content: center; flex-shrink: 0; letter-spacing: -0.01em;
}
.gcash-badge { background: #0072E3; font-style: normal; }
.maya-badge { background: #000; color: #00CD7E; text-transform: lowercase; font-weight: 900; }
.bank-hint { font-size: 0.72rem; color: #9aaa9a; font-weight: 600; }

/* BANK GRID */
.bank-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-bottom: 10px; }
.bank-tile {
  display: flex; flex-direction: column; align-items: center; gap: 8px; border: 1.5px solid #e5e8e5; background: #fff;
  border-radius: 10px; padding: 12px 4px 10px; cursor: pointer;
}
.bank-tile:hover { border-color: #d5dad5; }
.bank-tile-accent { width: 20px; height: 3px; border-radius: 2px; }
.bank-tile-name { font-size: 0.68rem; font-weight: 700; color: #4a5a4a; text-align: center; line-height: 1.2; }
.method-option-body { padding: 4px 16px 16px; }

/* CARD PREVIEW */
.card-preview {
  background: linear-gradient(135deg, #1a3a1a 0%, #00382a 100%); border-radius: 14px; padding: 16px 20px; margin-bottom: 16px; color: #fff;
  box-shadow: 0 8px 20px rgba(0,0,0,0.15);
}
.card-preview-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px; }
.card-chip { width: 32px; height: 22px; border-radius: 5px; background: linear-gradient(135deg, #D4A017, #f0c94a); display: inline-block; }
.card-preview-number { font-size: 1.1rem; letter-spacing: 2px; font-family: 'Courier New', monospace; margin: 0 0 18px; opacity: 0.95; }
.card-preview-bottom { display: flex; align-items: flex-end; justify-content: space-between; }
.card-preview-label { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.06em; color: #cfe0d5; }
.card-preview-value { font-size: 0.82rem; font-weight: 700; margin: 2px 0 0; text-transform: uppercase; letter-spacing: 0.5px; }

.wallet-note { font-size: 0.78rem; color: #9aaa9a; margin: 8px 0 0; }
.phone-input-wrap { display: flex; align-items: center; gap: 8px; }
.phone-prefix { font-size: 0.85rem; font-weight: 700; color: #4a5a4a; background: #f2f4f2; border-radius: 8px; padding: 10px 12px; }
.phone-input { flex: 1; margin-bottom: 0 !important; }

.wallet-mode-tabs { display: flex; gap: 6px; background: #f2f4f2; border-radius: 8px; padding: 4px; margin-bottom: 14px; }
.wallet-mode-tab { flex: 1; border: none; background: none; padding: 8px; border-radius: 6px; font-size: 0.78rem; font-weight: 700; color: #6a7a6a; cursor: pointer; }
.wallet-mode-tab.active { background: #fff; color: #1a3a1a; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
.qr-box {
  width: 140px; height: 140px; margin: 4px auto 12px; background: #fff; border: 1.5px solid #e5e8e5; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; color: #1a3a1a;
}
.qr-note { text-align: center; }

/* DUE ROW + PAY BUTTON */
.due-row { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; margin-bottom: 16px; background: #f7f9f7; border-radius: 10px; font-size: 0.85rem; color: #6a7a6a; font-weight: 600; }
.due-row strong { font-family: 'Playfair Display', serif; font-size: 1.25rem; color: #1a3a1a; }
.pay-now-btn { width: 100%; background: #14301a; color: #fff; border: none; border-radius: 10px; padding: 14px; font-weight: 700; font-size: 0.9rem; cursor: pointer; margin-bottom: 10px; transition: background 0.15s; }
.pay-now-btn:hover:not(:disabled) { background: #1c421f; }
.pay-now-btn:disabled { background: #e5e8e5; color: #9aaa9a; cursor: not-allowed; }
.ghost-btn.full-width { width: 100%; text-align: center; border: none; background: none; color: #8a9a8a; padding: 8px; margin-top: -2px; }
.ghost-btn.full-width:hover { color: #4a5a4a; }

.modal-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px; font-size: 0.85rem; font-family: inherit; color: #2a2a2a; margin-bottom: 16px;
}
.modal-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 6px; }
.ghost-btn { background: none; border: 1px solid #d5dad5; color: #4a5a4a; font-weight: 600; font-size: 0.85rem; cursor: pointer; padding: 10px 18px; border-radius: 8px; }
.primary-btn { background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 700; font-size: 0.85rem; cursor: pointer; }
.primary-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* SUMMARY STEP */
.summary-block { background: #f7f9f7; border-radius: 12px; padding: 18px 20px; margin: 18px 0 4px; }
.summary-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 0.85rem; padding: 8px 0; color: #6a7a6a; }
.summary-row strong { color: #1a3a1a; font-weight: 700; text-align: right; }
.summary-row.total { font-size: 1rem; padding-top: 10px; }
.summary-row.total span:last-child { font-family: 'Playfair Display', serif; font-weight: 700; color: #1f8f5c; font-size: 1.15rem; }
.summary-divider { border-top: 1px solid #e5e8e5; margin: 4px 0; }
.summary-method { display: flex; align-items: center; gap: 7px; }
.summary-method-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }

/* TOAST */
.toast {
  position: fixed; bottom: 28px; left: 50%; transform: translateX(-50%); z-index: 200;
  display: flex; align-items: center; gap: 8px; background: #00382a; color: #fff;
  padding: 13px 22px; border-radius: 10px; font-size: 0.86rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.18);
  white-space: nowrap;
}
.toast-fade-enter-active, .toast-fade-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(8px); }

@media (max-width: 640px) {
  .pending-row { flex-direction: column; }
  .history-right { text-align: left; }
}
</style>