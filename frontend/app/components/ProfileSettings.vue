<template>
  <div class="profile-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Profile Settings</h1>
        <p class="page-sub">Manage your professional profile, credentials, and preferences.</p>
      </div>
      <span v-if="personalInfo.prcVerified" class="verified-pill">
        <BadgeCheck :size="14" />
        PRC Verified
      </span>
    </div>

    <div class="profile-layout">
      <!-- TABS -->
      <div class="tab-card">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-item"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          <component :is="tab.icon" :size="17" />
          {{ tab.label }}
        </button>
      </div>

      <!-- PANEL -->
      <div class="panel-card">
        <!-- ============ PERSONAL INFO ============ -->
        <template v-if="activeTab === 'personal'">
          <div class="avatar-row">
            <div class="avatar-circle" :style="{ background: personalInfo.avatarColor }">
              {{ personalInfo.initials }}
            </div>
            <div>
              <button class="change-photo-btn" type="button">Change Photo</button>
              <p class="avatar-hint">JPG or PNG, max 2MB</p>
            </div>
          </div>

          <div class="form-grid">
            <div class="field">
              <label class="field-label">First Name</label>
              <input v-model="personalInfo.firstName" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Last Name</label>
              <input v-model="personalInfo.lastName" type="text" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Email Address</label>
              <input v-model="personalInfo.email" type="email" class="field-input" />
            </div>
            <div class="field">
              <label class="field-label">Phone Number</label>
              <input v-model="personalInfo.phone" type="tel" class="field-input" />
            </div>
          </div>

          <button class="save-btn" type="button" @click="saveChanges">Save Changes</button>
        </template>

        <!-- ============ EARNINGS ============ -->
        <template v-else-if="activeTab === 'earnings'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Earnings</h3>
              <p class="tab-panel-sub">Track your revenue, commission, and payout history.</p>
            </div>
            <div class="period-select">
              <select v-model="period">
                <option>This Month</option>
                <option>Last Month</option>
                <option>Last 3 Months</option>
                <option>This Year</option>
              </select>
              <ChevronDown :size="15" class="select-caret" />
            </div>
          </div>

          <div class="stat-grid-4">
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Landmark :size="17" /></div>
              <p class="mini-stat-value">₱{{ earningsSummary.gross.toLocaleString() }}</p>
              <p class="mini-stat-label">Gross Revenue</p>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Percent :size="17" /></div>
              <p class="mini-stat-value">₱{{ earningsSummary.commission.toLocaleString() }}</p>
              <p class="mini-stat-label">Platform Commission (15%)</p>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Wallet :size="17" /></div>
              <p class="mini-stat-value">₱{{ earningsSummary.net.toLocaleString() }}</p>
              <p class="mini-stat-label">Net Earnings</p>
              <p v-if="earningsSummary.net" class="mini-stat-delta">↑ 12% vs last month</p>
            </div>
            <div class="mini-stat-card">
              <div class="mini-stat-icon"><Hourglass :size="17" /></div>
              <p class="mini-stat-value">₱{{ earningsSummary.pending.toLocaleString() }}</p>
              <p class="mini-stat-label">Pending Payment</p>
            </div>
          </div>

          <div class="sub-panel">
            <h4 class="sub-panel-title">Earnings Trend (Last 6 Months)</h4>
            <div v-if="earningsTrend.length" class="chart-wrap">
              <div class="chart-y-axis">
                <span v-for="tick in yTicks" :key="tick">{{ tick.toLocaleString() }}</span>
              </div>
              <div class="chart-bars">
                <div v-for="point in earningsTrend" :key="point.month" class="chart-col">
                  <div class="chart-bar" :style="{ height: barHeight(point.amount) + '%' }"></div>
                  <span class="chart-label">{{ point.month }}</span>
                </div>
              </div>
            </div>
            <p v-else class="empty-note">No earnings data yet.</p>
          </div>

          <div class="sub-panel" v-if="invoices.length">
            <table class="invoice-table">
              <thead>
                <tr>
                  <th>INVOICE</th><th>PATIENT</th><th>DATE</th><th>GROSS</th><th>COMMISSION</th><th>NET EARNED</th><th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="inv in invoices" :key="inv.id">
                  <td class="invoice-id">{{ inv.id }}</td>
                  <td>{{ inv.patient }}</td>
                  <td class="invoice-date">{{ inv.date }}</td>
                  <td>₱{{ inv.gross.toFixed(2) }}</td>
                  <td class="invoice-commission">₱{{ inv.commission.toFixed(2) }}</td>
                  <td class="invoice-net">₱{{ inv.net.toFixed(2) }}</td>
                  <td><span class="status-pill" :class="inv.status === 'Paid' ? 'status-paid' : 'status-pending'">{{ inv.status === 'Paid' ? 'Paid Out' : 'Pending' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- ============ REVIEWS ============ -->
        <template v-else-if="activeTab === 'reviews'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Reviews</h3>
              <p class="tab-panel-sub">See what your patients are saying about their care.</p>
            </div>
          </div>

          <div v-if="reviews.length" class="summary-row">
            <div class="score-card">
              <p class="score-number">{{ reviewsSummary.average.toFixed(1) }}</p>
              <div class="stars-row">
                <Star
                  v-for="n in 5" :key="n" :size="17"
                  :fill="n <= Math.round(reviewsSummary.average) ? '#D4A017' : 'none'"
                  :color="n <= Math.round(reviewsSummary.average) ? '#D4A017' : '#d5dad5'"
                  :stroke-width="1.5"
                />
              </div>
              <p class="score-caption">Based on {{ reviewsSummary.total }} reviews</p>
            </div>

            <div class="breakdown-card">
              <div v-for="row in ratingBreakdown" :key="row.stars" class="breakdown-row">
                <span class="breakdown-label">{{ row.stars }} star{{ row.stars !== 1 ? 's' : '' }}</span>
                <div class="breakdown-track">
                  <div class="breakdown-fill" :style="{ width: maxCount ? `${(row.count / maxCount) * 100}%` : '0%' }" />
                </div>
                <span class="breakdown-count">{{ row.count }}</span>
              </div>
            </div>
          </div>

          <div v-if="reviews.length" class="review-list">
            <div v-for="review in reviews" :key="review.id" class="review-card">
              <div class="review-top">
                <div class="review-who">
                  <div class="review-avatar" :style="{ background: review.avatarColor }">{{ review.initials }}</div>
                  <div>
                    <p class="review-name">{{ review.name }}</p>
                    <div class="stars-row stars-row-sm">
                      <Star
                        v-for="n in 5" :key="n" :size="13"
                        :fill="n <= review.rating ? '#D4A017' : 'none'"
                        :color="n <= review.rating ? '#D4A017' : '#d5dad5'"
                        :stroke-width="1.5"
                      />
                    </div>
                  </div>
                </div>
                <span class="review-time">{{ review.postedAt }}</span>
              </div>
              <p class="review-comment">"{{ review.comment }}"</p>
            </div>
          </div>
          <p v-else class="empty-note">No reviews yet.</p>
        </template>

        <!-- ============ AVAILABILITY ============ -->
        <template v-else-if="activeTab === 'availability'">
          <div class="tab-panel-header">
            <div>
              <h3 class="tab-panel-title">Availability</h3>
              <p class="tab-panel-sub">Set the hours clients can book consultations with you.</p>
            </div>
            <button class="save-btn" type="button" @click="addSlot(week[0].day)"><Plus :size="15" /> Add Time Slot</button>
          </div>

          <div class="day-list">
            <div v-for="day in week" :key="day.day" class="day-row" :class="{ 'day-row-blocked': day.blocked }">
              <span class="day-name" :class="{ 'day-name-blocked': day.blocked }">{{ day.day }}</span>

              <div class="day-content">
                <template v-if="day.blocked">
                  <span class="blocked-pill">Blocked — No Availability</span>
                </template>
                <template v-else>
                  <span v-for="slot in day.slots" :key="slot.id" class="slot-pill">
                    {{ slot.start }} – {{ slot.end }}
                    <button class="pill-icon-btn" @click="removeSlot(day, slot)"><X :size="13" /></button>
                  </span>
                </template>
              </div>

              <button v-if="day.blocked" class="day-action-link" @click="unblockDay(day)">Unblock Day</button>
              <button v-else class="day-action-link" @click="addSlot(day.day)">+ Add Slot</button>
            </div>
          </div>

          <div class="sub-panel block-panel">
            <div class="block-header">
              <CalendarOff :size="18" class="block-icon" />
              <div>
                <h4 class="sub-panel-title">Block a Day Off</h4>
                <p class="block-desc">Quickly mark a specific date range as unavailable — useful for holidays, leave, or emergencies.</p>
              </div>
            </div>

            <div class="block-form">
              <div class="field">
                <label class="field-label">From</label>
                <input v-model="newBlock.from" type="date" class="field-input" />
              </div>
              <div class="field">
                <label class="field-label">To <span class="optional">(optional)</span></label>
                <input v-model="newBlock.to" type="date" class="field-input" />
              </div>
              <div class="field field-wide">
                <label class="field-label">Reason <span class="optional">(optional)</span></label>
                <input v-model="newBlock.reason" type="text" class="field-input" placeholder="e.g. Annual leave" />
              </div>
              <button class="save-btn block-btn" :disabled="!newBlock.from" @click="submitBlock">Block</button>
            </div>

            <div v-if="blocks.length" class="blocked-list">
              <div v-for="b in blocks" :key="b.id" class="blocked-item">
                <span class="blocked-dates">{{ formatDate(b.from) }}<template v-if="b.to"> – {{ formatDate(b.to) }}</template></span>
                <span v-if="b.reason" class="blocked-reason">{{ b.reason }}</span>
                <button class="remove-block-btn" @click="removeBlock(b)"><X :size="14" /></button>
              </div>
            </div>
            <p v-else class="empty-note">No blocked dates yet.</p>
          </div>
        </template>

        <!-- ============ OTHER TABS (still placeholder) ============ -->
        <template v-else>
          <p class="placeholder-text">{{ activeTabLabel }} settings go here.</p>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import {
  User, Briefcase, Languages, ShieldCheck, BadgeCheck,
  Landmark, Percent, Wallet, Hourglass, ChevronDown,
  Star, CalendarClock, Plus, X, CalendarOff
} from 'lucide-vue-next'
import { db } from '~/mock/mockDatabase'

definePageMeta({ layout: 'dashboard', title: 'Profile Settings' })

const tabs = [
  { key: 'personal', label: 'Personal Info', icon: User },
  { key: 'professional', label: 'Professional Profile', icon: Briefcase },
  { key: 'languages', label: 'Languages', icon: Languages },
  { key: 'earnings', label: 'Earnings', icon: Wallet },
  { key: 'reviews', label: 'Reviews', icon: Star },
  { key: 'availability', label: 'Availability', icon: CalendarClock },
  { key: 'security', label: 'Security', icon: ShieldCheck }
]

const activeTab = ref('personal')
const activeTabLabel = computed(() => tabs.find(t => t.key === activeTab.value)?.label)

/* ---------- PERSONAL INFO ---------- */
const personalInfo = ref({ ...db.personalInfo })

function saveChanges() {
  // Wire this up to your real update-profile API call
  personalInfo.value.initials = `${personalInfo.value.firstName?.[0] ?? ''}${personalInfo.value.lastName?.[0] ?? ''}`.toUpperCase()
}

/* ---------- EARNINGS ---------- */
const period = ref('This Month')
const earningsSummary = computed(() => db.earningsSummary)
const earningsTrend = computed(() => db.earningsTrend)
const invoices = computed(() => db.invoices)

const maxAmount = computed(() => Math.max(...earningsTrend.value.map(p => p.amount), 20000))
const yTicks = computed(() => {
  const step = Math.ceil(maxAmount.value / 5 / 2000) * 2000
  return [0, step, step * 2, step * 3, step * 4, step * 5].reverse()
})
function barHeight(amount) {
  const topTick = yTicks.value[0] || 20000
  return Math.min(100, Math.round((amount / topTick) * 100))
}

/* ---------- REVIEWS ---------- */
const reviewsSummary = ref(db.reviewsSummary)
const ratingBreakdown = ref(db.ratingBreakdown)
const reviews = ref(db.reviews)
const maxCount = computed(() => Math.max(0, ...ratingBreakdown.value.map(r => r.count)))

/* ---------- AVAILABILITY ---------- */
// Deep-copy so edits here don't mutate the shared mock db directly
const week = reactive(structuredClone(db.weeklyAvailabilityFull))
const blocks = reactive(structuredClone(db.blockedDaysOff))

function addSlot(dayName) {
  const day = week.find(d => d.day === dayName)
  if (!day || day.blocked) return
  day.slots.push({ id: 's' + Date.now(), start: '9:00 AM', end: '5:00 PM' })
}
function removeSlot(day, slot) {
  day.slots = day.slots.filter(s => s.id !== slot.id)
}
function unblockDay(day) {
  day.blocked = false
}

const newBlock = ref({ from: '', to: '', reason: '' })
function submitBlock() {
  if (!newBlock.value.from) return
  blocks.push({ id: 'off-' + Date.now(), from: newBlock.value.from, to: newBlock.value.to, reason: newBlock.value.reason })
  newBlock.value = { from: '', to: '', reason: '' }
}
function removeBlock(b) {
  const idx = blocks.findIndex(x => x.id === b.id)
  if (idx > -1) blocks.splice(idx, 1)
}
function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
</script>

<style scoped>
* { box-sizing: border-box; }

.profile-page { font-family: 'Inter', sans-serif; }

.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.verified-pill {
  display: inline-flex; align-items: center; gap: 6px;
  background: #e6efe0; color: #3a6b3a; font-size: 0.78rem; font-weight: 700;
  padding: 7px 14px; border-radius: 20px; white-space: nowrap;
}

/* LAYOUT */
.profile-layout { display: grid; grid-template-columns: 280px 1fr; gap: 20px; align-items: start; }

.tab-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 10px; display: flex; flex-direction: column; gap: 2px;
}
.tab-item {
  display: flex; align-items: center; gap: 10px; text-align: left;
  border: none; background: none; border-radius: 8px; padding: 12px 14px;
  font-size: 0.88rem; font-weight: 600; color: #4a5a4a; cursor: pointer;
}
.tab-item.active { background: #eef3ec; color: #1a3a1a; }

.panel-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 28px;
}

/* AVATAR */
.avatar-row { display: flex; align-items: center; gap: 18px; margin-bottom: 26px; }
.avatar-circle {
  width: 56px; height: 56px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 1.05rem; font-weight: 700; flex-shrink: 0;
}
.change-photo-btn {
  border: 1px solid #d5dad5; background: #fff; color: #1a3a1a;
  border-radius: 8px; padding: 9px 16px; font-size: 0.84rem; font-weight: 600; cursor: pointer;
}
.avatar-hint { font-size: 0.76rem; color: #9aaa9a; margin: 6px 0 0; }

/* FORM */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px 24px; margin-bottom: 24px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { display: block; font-size: 0.82rem; font-weight: 600; color: #1a3a1a; margin: 0 0 8px; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 12px 14px;
  font-size: 0.88rem; color: #2a2a2a; font-family: inherit;
}
.field-input:focus { outline: none; border-color: #D4A017; }

.save-btn {
  display: flex; align-items: center; gap: 6px;
  background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 12px 22px; font-weight: 700; font-size: 0.88rem; cursor: pointer; white-space: nowrap;
}
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

/* SHARED TAB PANEL HEADER */
.tab-panel-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 22px; gap: 16px; }
.tab-panel-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; color: #1a3a1a; margin: 0 0 4px; }
.tab-panel-sub { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
.sub-panel { border-top: 1px solid #f0f2f0; padding-top: 20px; margin-top: 20px; }
.sub-panel-title { font-family: 'Playfair Display', serif; font-size: 1rem; color: #1a3a1a; margin: 0 0 16px; }
.empty-note { font-size: 0.85rem; color: #9aaa9a; text-align: center; padding: 30px 0; }

/* EARNINGS TAB */
.period-select { position: relative; flex-shrink: 0; }
.period-select select {
  appearance: none; border: 1px solid #dde3dd; background: #fff;
  padding: 9px 32px 9px 14px; border-radius: 8px; font-size: 0.85rem; color: #1a3a1a; cursor: pointer;
}
.select-caret { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); color: #9aaa9a; pointer-events: none; }

.stat-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.mini-stat-card { background: #fafbfa; border-radius: 10px; padding: 16px 18px; border: 1px solid #f0f2f0; }
.mini-stat-icon {
  width: 30px; height: 30px; border-radius: 8px; background: #eef1ee;
  display: flex; align-items: center; justify-content: center; color: #4a5a4a; margin-bottom: 10px;
}
.mini-stat-value { font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.mini-stat-label { font-size: 0.75rem; color: #8a9a8a; margin: 3px 0 0; }
.mini-stat-delta { font-size: 0.7rem; font-weight: 600; color: #2e9e52; margin: 5px 0 0; }

.chart-wrap { display: flex; gap: 12px; }
.chart-y-axis { display: flex; flex-direction: column; justify-content: space-between; font-size: 0.7rem; color: #9aaa9a; padding-bottom: 24px; text-align: right; min-width: 44px; }
.chart-bars { flex: 1; display: flex; align-items: flex-end; gap: 16px; height: 200px; border-left: 1px solid #eceeec; padding-left: 16px; }
.chart-col { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.chart-bar { width: 60%; background: #163a1c; border-radius: 4px 4px 0 0; min-height: 2px; }
.chart-label { font-size: 0.76rem; color: #8a9a8a; margin-top: 8px; }

.invoice-table { width: 100%; border-collapse: collapse; }
.invoice-table th { text-align: left; font-size: 0.66rem; letter-spacing: 0.05em; color: #9aaa9a; padding-bottom: 12px; }
.invoice-table td { padding: 12px 10px 12px 0; border-top: 1px solid #f2f4f2; font-size: 0.83rem; color: #3a4a3a; }
.invoice-id { font-weight: 700; color: #1a3a1a; }
.invoice-date { color: #3b6fd6; }
.invoice-commission { color: #9aaa9a; }
.invoice-net { font-weight: 700; color: #1a3a1a; }
.status-pill { font-size: 0.7rem; font-weight: 600; padding: 4px 10px; border-radius: 20px; }
.status-paid { background: #e6f4e6; color: #2e7d32; }
.status-pending { background: #fdf1d6; color: #b8860b; }

/* REVIEWS TAB */
.summary-row { display: grid; grid-template-columns: 220px 1fr; gap: 14px; margin-bottom: 20px; }
.score-card { background: #fafbfa; border-radius: 10px; border: 1px solid #f0f2f0; padding: 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.score-number { font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stars-row { display: flex; gap: 3px; margin-top: 6px; }
.stars-row-sm { margin-top: 2px; }
.score-caption { font-size: 0.78rem; color: #8a9a8a; margin: 8px 0 0; }
.breakdown-card { background: #fafbfa; border-radius: 10px; border: 1px solid #f0f2f0; padding: 18px 22px; display: flex; flex-direction: column; justify-content: center; gap: 9px; }
.breakdown-row { display: flex; align-items: center; gap: 10px; }
.breakdown-label { width: 46px; font-size: 0.78rem; color: #4a5a4a; }
.breakdown-track { flex: 1; height: 7px; border-radius: 999px; background: #eceeec; overflow: hidden; }
.breakdown-fill { height: 100%; background: #D4A017; border-radius: 999px; }
.breakdown-count { width: 20px; text-align: right; font-size: 0.78rem; color: #8a9a8a; }

.review-list { display: flex; flex-direction: column; gap: 14px; }
.review-card { background: #fafbfa; border-radius: 10px; border: 1px solid #f0f2f0; padding: 16px 20px; }
.review-top { display: flex; align-items: flex-start; justify-content: space-between; }
.review-who { display: flex; align-items: flex-start; gap: 12px; }
.review-avatar { width: 34px; height: 34px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; }
.review-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.review-time { font-size: 0.76rem; color: #9aaa9a; white-space: nowrap; }
.review-comment { font-size: 0.84rem; color: #4a5a4a; line-height: 1.55; margin: 10px 0 0 46px; }

/* AVAILABILITY TAB */
.day-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px; }
.day-row { background: #fafbfa; border-radius: 10px; border: 1px solid #f0f2f0; padding: 14px 18px; display: flex; align-items: center; gap: 16px; }
.day-row-blocked { background: #fafafa; }
.day-name { font-size: 0.88rem; font-weight: 700; color: #1a3a1a; width: 100px; flex-shrink: 0; }
.day-name-blocked { color: #9aaa9a; font-weight: 600; }
.day-content { flex: 1; display: flex; flex-wrap: wrap; gap: 8px; }
.slot-pill { display: flex; align-items: center; gap: 6px; background: #e6f4e6; color: #1a5a2a; font-size: 0.8rem; font-weight: 600; padding: 6px 10px 6px 14px; border-radius: 20px; }
.pill-icon-btn { background: none; border: none; color: #4a8a5a; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 2px; }
.pill-icon-btn:hover { color: #1a5a2a; }
.blocked-pill { background: #fbe1de; color: #c0483a; font-size: 0.78rem; font-weight: 700; padding: 6px 14px; border-radius: 20px; }
.day-action-link { background: none; border: none; color: #1a6a2a; font-size: 0.8rem; font-weight: 600; cursor: pointer; white-space: nowrap; flex-shrink: 0; }
.day-row-blocked .day-action-link { color: #9aaa9a; }
.day-action-link:hover { text-decoration: underline; }

.block-panel { background: #eef3ee; border-radius: 10px; padding: 20px; border-top: none; margin-top: 20px; }
.block-header { display: flex; gap: 12px; margin-bottom: 18px; }
.block-icon { color: #1a3a1a; flex-shrink: 0; margin-top: 2px; }
.block-desc { font-size: 0.8rem; color: #6a7a6a; line-height: 1.5; margin: 0; max-width: 640px; }
.block-form { display: grid; grid-template-columns: 1fr 1fr 1.4fr auto; gap: 12px; align-items: end; margin-bottom: 14px; }
.field-wide { grid-column: auto; }
.block-btn { padding: 12px 20px; }
.blocked-list { display: flex; flex-direction: column; gap: 8px; }
.blocked-item { display: flex; align-items: center; gap: 12px; background: #fff; border-radius: 8px; padding: 10px 14px; font-size: 0.8rem; }
.blocked-dates { font-weight: 700; color: #1a3a1a; }
.blocked-reason { color: #7a8a7a; flex: 1; }
.remove-block-btn { background: none; border: none; color: #9aaa9a; cursor: pointer; display: flex; }
.remove-block-btn:hover { color: #c0483a; }

@media (max-width: 1100px) {
  .stat-grid-4 { grid-template-columns: repeat(2, 1fr); }
  .summary-row { grid-template-columns: 1fr; }
  .block-form { grid-template-columns: 1fr; }
}
</style>