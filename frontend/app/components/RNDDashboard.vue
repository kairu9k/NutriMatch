<template>
  <div class="nm-page rd-page">
    <p v-if="error" class="nm-error">{{ error }} <button class="rd-link" @click="load">Try again</button></p>

    <!-- BANNER: greeting + today's summary on the left, the next consultation on the right -->
    <section class="rd-hero">
      <img class="rd-hero-plate" :src="plateImg" alt="" aria-hidden="true" />
      <span class="rd-hero-fade" aria-hidden="true"></span>
      <div class="rd-hero-text">
        <p class="rd-eyebrow"><span aria-hidden="true"></span>{{ longToday }}</p>
        <h1 class="rd-title">Good {{ partOfDay }}, <em>{{ auth.user?.first_name }}.</em></h1>
        <p v-if="d" class="rd-hero-sub"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ summaryLine }}</p>
      </div>
      <div v-if="d" class="rd-next un-b">
        <template v-if="d.next_up">
          <div class="un-db">
            <small>{{ sdMonth(d.next_up.scheduled_at) }}</small>
            <b>{{ sdDay(d.next_up.scheduled_at) }}</b>
            <span>{{ ['Today', 'Tomorrow'].includes(dayWord(d.next_up.scheduled_at)) ? dayWord(d.next_up.scheduled_at) : sdWeek(d.next_up.scheduled_at) }}</span>
          </div>
          <div class="un-m">
            <p class="un-k">Up next, <span class="un-day">{{ dayWord(d.next_up.scheduled_at).split(',')[0] }}, </span><b>{{ clock(d.next_up.scheduled_at) }}</b></p>
            <div class="un-who">
              <img v-if="d.next_up.client.profile_photo" :src="d.next_up.client.profile_photo" alt="" class="un-av" />
              <span v-else class="un-av un-ini">{{ nameInitials(d.next_up.client.name) }}</span>
              <div class="un-name">
                <strong>{{ d.next_up.client.name }}</strong>
                <small><Video :size="13" aria-hidden="true" /> {{ d.next_up.type_label }} consultation</small>
              </div>
              <span class="un-paid" :class="{ unpaid: d.next_up.payment !== 'paid' }"><template v-if="d.next_up.payment === 'paid'"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></template>{{ d.next_up.payment === 'paid' ? 'Paid' : 'Not paid yet' }}</span>
            </div>
            <div class="un-acts">
              <NuxtLink v-if="canJoin(d.next_up)" :to="`/consultation-room/${d.next_up.id}`" class="un-btn gold"><Video :size="15" /> Join now</NuxtLink>
              <span v-else-if="d.next_up.type !== 'in_person'" class="un-btn soft"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>Join opens {{ dayWord(d.next_up.join_opens_at) === 'Today' ? '' : `${dayWord(d.next_up.join_opens_at).split(',')[0].replace(/^Tomorrow/, 'tomorrow')} ` }}{{ clock(d.next_up.join_opens_at) }}</span>
              <NuxtLink :to="`/client-detail/${d.next_up.relationship_id}`" class="un-btn" :class="canJoin(d.next_up) ? 'soft' : 'dark'">Open patient<svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="un-db un-empty-db"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></div>
          <div class="un-m">
            <p class="un-k">Up next</p>
            <p class="un-empty">No consultations coming up.</p>
            <div class="un-acts"><NuxtLink to="/appointments" class="un-btn dark">View appointments<svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink></div>
          </div>
        </template>
      </div>
    </section>

    <!-- PHONE: quick access to the main pages (UI only, same pages as the sidebar) -->
    <section class="rq" aria-label="Quick access">
      <h2 class="rq-title">Quick access</h2>
      <div class="rq-grid">
        <NuxtLink to="/appointments" class="rq-tile "><span class="rq-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>Appointments</NuxtLink>
        <NuxtLink to="/my-patients" class="rq-tile gold"><span class="rq-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 4.5a3.5 3.5 0 0 1 0 7M18 14a5.5 5.5 0 0 1 3.5 6" /></svg></span>My Patients</NuxtLink>
        <NuxtLink to="/ncp-records" class="rq-tile "><span class="rq-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" /></svg></span>NCP Records</NuxtLink>
        <NuxtLink to="/meal-planning" class="rq-tile gold"><span class="rq-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 3v8a2 2 0 0 0 2 2h1v8M8 3v6M6 3v6M16 21V3c-2 1-3 4-3 8h3" /></svg></span>Meal Plans</NuxtLink>
        <NuxtLink to="/availability" class="rq-tile dark"><span class="rq-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg></span>Availability</NuxtLink>
        <NuxtLink to="/earnings" class="rq-tile "><span class="rq-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="6" width="18" height="13" rx="3" /><path d="M3 10h18M16 15h2" /></svg></span>Earnings</NuxtLink>
        <NuxtLink to="/messages" class="rq-tile gold"><span class="rq-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5h16v11H8l-4 4z" /></svg></span>Messages</NuxtLink>
        <NuxtLink to="/profile-settings" class="rq-tile "><span class="rq-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-2.7 1.1V21a2 2 0 1 1-4 0v-.1A1.6 1.6 0 0 0 8.6 19.4a1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0-1.1-2.7H3a2 2 0 1 1 0-4h.1A1.6 1.6 0 0 0 4.6 8.6a1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z" /></svg></span>Settings</NuxtLink>
      </div>
    </section>

    <!-- NEEDS ATTENTION: the shared strip and pop-up (NeedsAttention.vue) -->
    <NeedsAttention v-if="d" class="needs-strip" :groups="needGroups" clear-text="All caught up. Nothing is waiting on you." />

    <div v-if="loading" class="rd-card"><p class="rd-muted">Loading your dashboard…</p></div>

    <template v-else-if="d">
      <!-- three figures -->
      <div class="rd-stats">
        <NuxtLink to="/appointments?tab=upcoming" class="rd-stat" style="--c: #004D3A; --bg: #E3EFE7">
          <span class="rd-stat-top"><span class="rd-stat-label">Consultations this week</span><span class="rd-stat-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span></span>
          <strong class="rd-stat-val">{{ d.stats.sessions_this_week }}</strong>
          <small class="rd-stat-sub">{{ todayCount }} today</small>
        </NuxtLink>
        <NuxtLink to="/my-patients" class="rd-stat" style="--c: #9A7300; --bg: #FBF3D2">
          <span class="rd-stat-top"><span class="rd-stat-label">Active patients</span><span class="rd-stat-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20c.6-3.6 3.2-6 6.5-6s5.9 2.4 6.5 6" /><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.4c2 .8 3.2 2.8 3.5 5.6" /></svg></span></span>
          <strong class="rd-stat-val">{{ d.stats.active_patients }}</strong>
          <small class="rd-stat-sub">View my patients</small>
        </NuxtLink>
        <NuxtLink to="/meal-planning" class="rd-stat" :class="{ empty: d.adherence.pct == null }" style="--c: #3B5BA5; --bg: #EEF1FA">
          <span class="rd-stat-top"><span class="rd-stat-label">Meal-plan adherence</span><span class="rd-stat-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></svg></span></span>
          <strong class="rd-stat-val">{{ d.adherence.pct == null ? '—' : `${d.adherence.pct}%` }}</strong>
          <small class="rd-stat-sub">{{ deltaText }}</small>
        </NuxtLink>
      </div>

      <div class="rd-grid">
        <div class="rd-col">
          <!-- schedule -->
          <div class="rd-card">
            <div class="rd-head">
              <span class="rd-head-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>
              <div class="rd-head-text">
                <h2 class="rd-h">Today &amp; the next 7 days</h2>
                <p class="rd-sub">{{ confirmedSchedule.length ? `${confirmedSchedule.length} confirmed consultation${confirmedSchedule.length === 1 ? '' : 's'}` : 'Confirmed consultations' }}</p>
              </div>
              <NuxtLink to="/appointments" class="rd-link">All appointments<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
            </div>
            <div v-if="!confirmedSchedule.length" class="rd-empty"><span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span><p>Nothing confirmed for this week.</p></div>
            <div v-for="group in scheduleByDay" :key="group.key" class="sd-dg" :class="{ 'is-today': group.key === todayIso }">
              <div class="sd-db" :aria-label="group.label"><small>{{ sdMonth(group.items[0].scheduled_at) }}</small><b>{{ sdDay(group.items[0].scheduled_at) }}</b><span>{{ group.key === todayIso ? 'Today' : sdWeek(group.items[0].scheduled_at) }}</span></div>
              <div class="sd-dl">
                <div v-for="(a, i) in group.items" :key="a.id" class="sd-ev" :class="{ 'is-now': group.key === todayIso && i === sdFirstUpcoming(group) }">
                  <span class="sd-tm">{{ sdTime(a.scheduled_at) }} <small>{{ sdAmPm(a.scheduled_at) }}</small></span>
                  <img v-if="a.client.profile_photo" :src="a.client.profile_photo" class="sd-av" alt="" />
                  <span v-else class="sd-av sd-ini">{{ nameInitials(a.client.name) }}</span>
                  <span class="sd-evm">
                    <span class="sd-evn"><NuxtLink :to="`/client-detail/${a.relationship_id}`" class="sd-name">{{ a.client.name }}</NuxtLink><span v-if="group.key === todayIso && i === sdFirstUpcoming(group)" class="sd-soon"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ sdSoonText(a.scheduled_at) }}</span></span>
                    <span class="sd-evs"><Video v-if="a.type === 'video'" :size="14" aria-hidden="true" />{{ a.type_label }}, {{ a.duration_minutes }} min<i aria-hidden="true" /><span v-if="a.payment === 'paid'" class="sd-pay">Paid</span><span v-else class="sd-pay muted">Not paid yet</span></span>
                  </span>
                  <NuxtLink v-if="canJoin(a)" :to="`/consultation-room/${a.id}`" class="rd-btn dark sm"><Video :size="14" /> Join</NuxtLink>
                  <NuxtLink v-else :to="`/client-detail/${a.relationship_id}`" class="sd-go" :aria-label="`Open ${a.client.name}`"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg></NuxtLink>
                </div>
              </div>
            </div>
            <NuxtLink v-if="d.requests.length" to="/appointments?tab=requests" class="sd-req">
              <span class="sd-req-i"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z" /></svg></span>
              <span><b>{{ d.requests.length }} booking request{{ d.requests.length === 1 ? '' : 's' }}</b> {{ d.requests.length === 1 ? 'is' : 'are' }} waiting for your answer</span>
              <em>Review<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></em>
            </NuxtLink>
          </div>

          <!-- adherence chart -->
          <div class="rd-card">
            <div class="rd-head">
              <span class="rd-head-ico" style="background: #FBF3D2; color: #9A7300"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" /></svg></span>
              <div class="rd-head-text">
                <h2 class="rd-h">Meal-plan adherence, last 7 days</h2>
                <p class="rd-sub">Share of planned meals your patients followed. Partly followed counts as half, and an unlogged meal counts as missed.</p>
              </div>
              <div v-if="d.adherence.pct != null" class="chart-figure">
                <span class="cf-value">{{ d.adherence.pct }}%</span>
                <span class="cf-sub">{{ d.adherence.logged }} of {{ d.adherence.planned }} meals logged<template v-if="d.adherence.waiting">, {{ d.adherence.waiting }} waiting for your rating</template></span>
              </div>
            </div>
            <div v-if="!d.adherence.planned" class="rd-empty"><span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" /></svg></span><p>No meal plans active yet. Adherence shows up once patients have a sent plan.</p></div>
            <div v-else class="chart" role="img" :aria-label="`Meal-plan adherence by day: ${chartSummary}`">
              <div class="chart-plot">
                <div v-for="t in [100, 50, 0]" :key="t" class="grid" :style="{ bottom: `${t}%` }"><span>{{ t }}%</span></div>
                <div class="goal" :style="{ bottom: `${d.adherence.goal}%` }"><span>Goal {{ d.adherence.goal }}%</span></div>
                <div class="cols">
                  <div v-for="(day, i) in d.adherence.days" :key="day.date" class="col" tabindex="0"
                       :aria-label="colLabel(day, i)" @mouseenter="hover = i" @mouseleave="hover = null" @focus="hover = i" @blur="hover = null">
                    <span v-if="day.followed_pct == null" class="no-data" title="No meals planned">–</span>
                    <span v-else class="bar" :class="{ today: i === 6 }" :style="{ height: `${Math.max(day.followed_pct, 1.5)}%` }" />
                    <div v-if="hover === i" class="tip" :class="{ left: i > 4 }">
                      <strong>{{ tipDay(day.date, i) }}</strong>
                      <span v-if="day.followed_pct == null">No meals planned</span>
                      <template v-else>
                        <span>{{ day.followed_pct }}% followed</span>
                        <span class="tip-muted">{{ day.logged }} of {{ day.planned }} meals logged{{ i === 6 ? ' so far' : '' }}</span>
                      </template>
                    </div>
                  </div>
                </div>
              </div>
              <div class="chart-x">
                <span v-for="(day, i) in d.adherence.days" :key="day.date" :class="{ today: i === 6 }">{{ i === 6 ? 'Today' : weekday(day.date) }}</span>
              </div>
              <table class="sr-only">
                <caption>Meal-plan adherence by day</caption>
                <thead><tr><th>Day</th><th>Followed</th><th>Meals logged</th></tr></thead>
                <tbody><tr v-for="day in d.adherence.days" :key="day.date"><td>{{ day.date }}</td><td>{{ day.followed_pct ?? 'none planned' }}</td><td>{{ day.logged }} / {{ day.planned }}</td></tr></tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="rd-col">
          <!-- requests -->
          <div class="rd-card">
            <div class="rd-head">
              <span class="rd-head-ico" style="background: #FDECEC; color: #B4384A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z" /></svg></span>
              <div class="rd-head-text">
                <h2 class="rd-h">Booking requests <span v-if="d.requests.length" class="rd-count">{{ d.requests.length }}</span></h2>
                <p class="rd-sub">Confirm before the time passes. The client pays after you confirm.</p>
              </div>
            </div>
            <div v-if="!d.requests.length" class="rd-empty"><span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z" /></svg></span><p>No requests waiting.</p></div>
            <div v-for="a in d.requests" :key="a.id" class="req-row">
              <img v-if="a.client.profile_photo" :src="a.client.profile_photo" class="rd-av sm" alt="" />
              <span v-else class="rd-av sm">{{ nameInitials(a.client.name) }}</span>
              <div class="req-main">
                <p class="req-name">{{ a.client.name }}</p>
                <p class="req-sub">{{ a.type_label }}, {{ dayWord(a.scheduled_at) }}, {{ clock(a.scheduled_at) }}</p>
                <p class="req-soon" :class="{ urgent: hoursUntil(a.scheduled_at) < SOON_HOURS }"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ startsIn(a.scheduled_at) }}</p>
              </div>
              <NuxtLink to="/appointments?tab=requests" class="rd-btn dark sm">Review</NuxtLink>
            </div>
          </div>

          <!-- earnings -->
          <div class="rd-card">
            <div class="rd-head">
              <span class="rd-head-ico" style="background: #E3EFE7; color: #004D3A"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-3" /><path d="M21 9h-6a3 3 0 0 0 0 6h6z" /></svg></span>
              <div class="rd-head-text">
                <h2 class="rd-h">Earnings</h2>
                <p v-if="d.earnings_compare" class="rd-sub">{{ d.earnings_compare.label }}</p>
              </div>
              <NuxtLink to="/earnings" class="rd-link">Open Earnings<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
            </div>
            <div class="rd-earn">
              <div v-for="m in d.earnings_compare?.metrics || []" :key="m.key" class="rd-e">
                <small>{{ EARN_LABEL[m.key] }}</small>
                <strong>{{ m.key === 'earned' ? peso(m.now) : m.now }}</strong>
                <span class="rd-e-foot"><ChangeBadge :now="m.now" :before="m.before" :pct="m.change_pct" /><em>was {{ m.key === 'earned' ? peso(m.before) : m.before }}</em></span>
              </div>
              <div class="rd-e gold">
                <small>Waiting to be paid</small>
                <strong>{{ peso(Number(d.earnings.pending) + Number(d.earnings.posted)) }}</strong>
                <span class="rd-e-foot"><em>{{ peso(d.earnings.posted) }} cleared, {{ peso(d.earnings.pending) }} on hold</em></span>
              </div>
              <div class="rd-e">
                <small>Paid out so far</small>
                <strong>{{ peso(d.earnings.paid_out) }}</strong>
              </div>
            </div>
            <p class="rd-note"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg><span>Next payout <strong>{{ shortDate(d.earnings.next_payout_date) }}</strong><template v-if="!d.earnings.eligible">. It needs {{ peso(d.earnings.minimum_payout) }} cleared<template v-if="!d.earnings.has_payout_account"> and your payout details</template></template>.</span></p>
          </div>

          <!-- reviews -->
          <div class="rd-card">
            <div class="rd-head">
              <span class="rd-head-ico" style="background: #FBF3D2; color: #9A7300"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg></span>
              <div class="rd-head-text">
                <h2 class="rd-h">Latest reviews</h2>
              </div>
              <NuxtLink v-if="d.rating?.count" to="/reviews" class="overall" :aria-label="`Average ${d.rating.average} out of 5 from ${d.rating.count} reviews. Open Reviews`">
                <span class="overall-star" aria-hidden="true">★</span>
                <strong>{{ d.rating.average.toFixed(1) }}</strong>
                <span>from {{ d.rating.count }} review{{ d.rating.count === 1 ? '' : 's' }}</span>
              </NuxtLink>
            </div>
            <div v-if="!d.reviews.length" class="rd-empty"><span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg></span><p>No reviews yet.</p></div>
            <div v-for="(r, i) in d.reviews" :key="i" class="review">
              <p class="stars">{{ '★'.repeat(r.rating) }}<span>{{ '★'.repeat(5 - r.rating) }}</span></p>
              <p v-if="r.comment" class="review-text">"{{ r.comment }}"</p>
              <p class="review-by">{{ r.client }}, {{ shortDate(r.created_at) }}</p>
            </div>
          </div>

          <!-- recent activity: the latest notifications (gold = unread) -->
          <div class="rd-card">
            <div class="rd-head">
              <span class="rd-head-ico" style="background: #EEF1FA; color: #3B5BA5"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" /></svg></span>
              <div class="rd-head-text">
                <h2 class="rd-h">Recent activity</h2>
              </div>
              <NuxtLink v-if="recentActivity.length" to="/notifications" class="rd-link">View all<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
            </div>
            <ul v-if="recentActivity.length" class="rd-tl">
              <li v-for="n in recentActivity" :key="n.id" class="activity-row" :class="{ unread: !n.is_read }">
                <span class="rd-tl-ico" :class="actKind(n).tone"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="actKind(n).path" /></span>
                <div class="activity-text">
                  <p class="activity-title">{{ n.subject }}</p>
                  <p class="activity-time">{{ timeAgo(n.created_at) }}</p>
                </div>
                <span v-if="!n.is_read" class="activity-dot" aria-label="Unread"></span>
              </li>
            </ul>
            <div v-else class="rd-empty"><span><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" /></svg></span><p>Nothing yet. Booking requests, payments and patient updates show up here.</p></div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import {
  CalendarDays, ClipboardList, FlaskConical, MessageSquare,
  Target, Users, Utensils, Video, Wallet,
} from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'


const { get } = useApi()
const auth = useAuthStore()
const now = useNow()


const d = ref(null)
const loading = ref(true)
const error = ref('')
const hover = ref(null)
const setupMissing = ref([])

/* recent activity (the bell's notifications, newest first, live) */
const notifications = ref([])
const recentActivity = computed(() => notifications.value.filter(n => n.notifiable_type !== 'message').slice(0, 5))
async function loadActivity() {
  try {
    const notes = await get('/notifications/')
    notifications.value = Array.isArray(notes) ? notes : notes?.results || []
  } catch {
    notifications.value = []
  }
}
const live = useLiveUpdates()
live.onLive('notification', ({ notification }) => {
  if (!notifications.value.some(n => n.id === notification.id)) notifications.value = [notification, ...notifications.value]
})
live.onLive('reconnect', loadActivity)
// "19 min ago", "15 hrs ago", "3 days ago", then the date (as on the client dashboard)
function timeAgo(iso) {
  const mins = Math.round((now.value - new Date(iso)) / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs} hr${hrs === 1 ? '' : 's'} ago`
  const days = Math.round(hrs / 24)
  if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`
  return shortDate(iso)
}

async function load({ quiet = false } = {}) {
  if (!quiet) error.value = ''
  try {
    d.value = await get('/rnd/dashboard/')
  } catch {
    if (!quiet) error.value = 'Could not load your dashboard.'
  } finally {
    loading.value = false
  }
}
async function loadSetup() {
  try {
    setupMissing.value = (await get('/auth/me/onboarding/')).missing || []
  } catch {
    setupMissing.value = []
  }
}
onMounted(() => {
  load()
  loadActivity()
  loadSetup()
})
// requests, schedule, payments and alerts stay current without a reload
useAutoRefresh(() => Promise.all([load({ quiet: true }), loadSetup()]))
// patient alerts, critical first as the API sends them (all of them: the pop-up scrolls)
const shownAlerts = computed(() => d.value?.alerts || [])
const noDot = t => String(t || '').replace(/[.\s]+$/, '')
const riskAlerts = computed(() => shownAlerts.value.filter(a => a.level !== 'info'))
const infoAlerts = computed(() => shownAlerts.value.filter(a => a.level === 'info'))
// The pop-up's sections. Each to-do count gets a line of what to do and a button.
const TODO_TEXT = {
  done: ['Mark each one complete after the call, so the client gets their summary.', 'Mark complete'],
  ncp: ['Finish the records you started.', 'Finish'],
  plan: ['They have a finished NCP record and no meal plan yet.', 'Create plan'],
  logs: ['Rate how well each meal followed the plan.', 'Rate'],
  labs: ['Open each upload, then accept or decline it.', 'Review'],
  msg: ['Reply in Messages.', 'Reply'],
}
const needGroups = computed(() => {
  if (!d.value) return []
  const alert = (a, i, tone) => ({ key: `${tone}-${i}`, title: `${a.client.name}: ${noDot(a.title)}`, detail: a.detail, to: a.link, action: a.action, tone })
  const todo = []
  if (requiredMissing.value.length) {
    todo.push({ key: 'profile', title: 'Finish your profile so clients can book you', tone: 'todo', action: 'Complete profile',
      detail: `Still to do: ${requiredMissing.value.map(m => m.label.toLowerCase()).join('; ')}.`,
      to: requiredMissing.value.length === 1 && requiredMissing.value[0].key === 'availability' ? '/profile-settings?tab=availability' : '/profile-settings' })
  }
  // the bio is optional (clients can find the RND without it), but worth a nudge
  if (needsBio.value) {
    todo.push({ key: 'bio', title: 'Add a bio to your profile', tone: 'todo', action: 'Write bio', to: '/profile-settings',
      detail: 'Clients see it on Find an RND and your profile. It helps them choose you.' })
  }
  if (needsClinicAddress.value) {
    todo.push({ key: 'clinic', title: 'Add your clinic address', tone: 'todo', action: 'Add address', to: '/profile-settings',
      detail: "Clients can't book your in-person consultations until it's added." })
  }
  if (!d.value.earnings.has_payout_account) {
    const waiting = Number(d.value.earnings.pending) + Number(d.value.earnings.posted)
    todo.push({ key: 'payout', title: 'Add your payout details', tone: 'todo', action: 'Add details', to: '/earnings?payout=1',
      detail: `Earnings are sent every 5th to your e-wallet or bank${waiting > 0 ? `, and ${peso(waiting)} is waiting` : ''}.` })
  }
  for (const t of todoItems.value) {
    todo.push({ key: t.key, title: `${t.count} ${t.label}`, detail: TODO_TEXT[t.key]?.[0], action: TODO_TEXT[t.key]?.[1], to: t.to, tone: 'todo' })
  }
  return [
    { title: 'Your patients', sub: "From your patients' records. Open the chart to follow up.",
      items: [...riskAlerts.value.map((a, i) => alert(a, i, 'urgent')), ...infoAlerts.value.map((a, i) => alert(a, i, 'info'))] },
    { title: 'Your to-do', items: todo },
  ]
})
const requiredMissing = computed(() => setupMissing.value.filter(m => !m.optional))
const needsClinicAddress = computed(() => setupMissing.value.some(m => m.key === 'clinic_address'))
const needsBio = computed(() => setupMissing.value.some(m => m.key === 'bio'))

const PH = { timeZone: 'Asia/Manila' }
const phDate = v => new Date(v).toLocaleDateString('en-CA', PH)
const todayIso = phDate(new Date())
const partOfDay = (() => {
  const h = Number(new Date().toLocaleString('en-US', { ...PH, hour: 'numeric', hour12: false }))
  return h < 12 ? 'morning' : h < 18 ? 'afternoon' : 'evening'
})()

const todoItems = computed(() => {
  const t = d.value?.todo
  if (!t) return []
  return [
    { key: 'done', count: t.to_complete, label: `consultation${t.to_complete === 1 ? '' : 's'} to mark complete`, to: '/appointments?tab=to_complete', icon: ClipboardList },
    { key: 'ncp', count: t.ncp_drafts, label: `NCP draft${t.ncp_drafts === 1 ? '' : 's'} to finish`, to: '/ncp-records', icon: ClipboardList },
    { key: 'plan', count: t.need_meal_plan, label: `patient${t.need_meal_plan === 1 ? '' : 's'} ready for a meal plan`,
      to: t.need_meal_plan_first ? `/meal-planning?relationship=${t.need_meal_plan_first}` : '/meal-planning', icon: Target },
    { key: 'logs', count: t.meal_logs_to_review, label: `meal log${t.meal_logs_to_review === 1 ? '' : 's'} to rate`,
      to: t.meal_logs_to_review_first ? `/client-detail/${t.meal_logs_to_review_first}?tab=meal` : '/my-patients', icon: Utensils },
    { key: 'labs', count: t.lab_results_to_review, label: `lab result${t.lab_results_to_review === 1 ? '' : 's'} to review`,
      to: t.lab_results_to_review_first ? `/client-detail/${t.lab_results_to_review_first}?tab=labs` : '/my-patients', icon: FlaskConical },
    { key: 'msg', count: t.unread_messages, label: `unread message${t.unread_messages === 1 ? '' : 's'}`, to: '/messages', icon: MessageSquare },
  ].filter(i => i.count > 0)
})

const todayCount = computed(() => (d.value?.schedule || []).filter(a => phDate(a.scheduled_at) === todayIso).length)

/* ---------- banner ---------- */
const longToday = new Date().toLocaleDateString('en-PH', { ...PH, weekday: 'long', month: 'long', day: 'numeric' })
const todayConfirmed = computed(() => (d.value?.schedule || []).filter(a => a.status === 'confirmed' && phDate(a.scheduled_at) === todayIso))
function untilText(v) {
  const mins = Math.round((new Date(v) - now.value) / 60000)
  if (mins <= 0) return 'now'
  if (mins < 60) return `in ${mins} minute${mins === 1 ? '' : 's'}`
  const h = Math.round(mins / 60)
  return `in about ${h} hour${h === 1 ? '' : 's'}`
}
const summaryLine = computed(() => {
  const next = d.value?.next_up
  const n = todayConfirmed.value.length
  if (n) {
    const count = `You have ${n} consultation${n === 1 ? '' : 's'} today.`
    if (next && phDate(next.scheduled_at) === todayIso) {
      const started = new Date(next.scheduled_at) <= now.value
      return started ? `${count} Your consultation with ${next.client.first_name} is happening now.`
        : `${count} Your ${next.id === todayConfirmed.value[0]?.id ? 'first' : 'next'} one starts ${untilText(next.scheduled_at)}.`
    }
    return `${count} You're done with them for the day.`
  }
  if (next) return `No consultations today. Your next one is ${dayWord(next.scheduled_at, true).replace(/^Tomorrow/, 'tomorrow')} at ${clock(next.scheduled_at)}.`
  return 'No consultations coming up. Your schedule is clear.'
})
// The schedule shows only what's confirmed; requests live in Booking requests.
const confirmedSchedule = computed(() => (d.value?.schedule || []).filter(a => a.status === 'confirmed'))
const scheduleByDay = computed(() => {
  const groups = []
  for (const a of confirmedSchedule.value) {
    const key = phDate(a.scheduled_at)
    let g = groups.find(x => x.key === key)
    if (!g) groups.push(g = { key, label: dayWord(a.scheduled_at, true), items: [] })
    g.items.push(a)
  }
  return groups
})

const deltaText = computed(() => {
  const a = d.value?.adherence
  if (!a || a.pct == null) return 'Last 7 days'
  if (a.previous_pct == null) return 'Last 7 days'
  const diff = a.pct - a.previous_pct
  return diff === 0 ? 'Same as the week before' : `${diff > 0 ? '+' : '−'}${Math.abs(diff)} pts vs the week before`
})
const EARN_LABEL = { earned: 'Earned this month', consultations: 'Consultations completed' }

function canJoin(a) {
  return a.status === 'confirmed' && a.type === 'video' && now.value >= new Date(a.join_opens_at) && now.value <= new Date(a.join_closes_at)
}
function clock(v) {
  return new Date(v).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
}
// Booking requests: how soon each starts. Under SOON_HOURS it turns red,
// because an unconfirmed request lapses once its time passes.
const SOON_HOURS = 6
function hoursUntil(v) {
  return (new Date(v).getTime() - now.value) / 3600000
}
function startsIn(v) {
  const h = hoursUntil(v)
  if (h < 1) return `Starts in ${Math.max(1, Math.round(h * 60))} min`
  if (h < 24) return `Starts in ${Math.round(h)} hour${Math.round(h) === 1 ? '' : 's'}`
  const days = Math.round(h / 24)
  return `Starts in ${days} day${days === 1 ? '' : 's'}`
}
function dayWord(v, long = false) {
  const day = phDate(v)
  if (day === todayIso) return 'Today'
  if (day === phDate(Date.now() + 86400000)) return 'Tomorrow'
  return new Date(v).toLocaleDateString('en-PH', { ...PH, weekday: long ? 'long' : 'short', month: 'short', day: 'numeric' })
}
function weekday(iso) {
  return new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { weekday: 'short' })
}
function tipDay(iso, i) {
  return i === 6 ? 'Today' : new Date(`${iso}T00:00:00`).toLocaleDateString('en-PH', { weekday: 'long', month: 'short', day: 'numeric' })
}
function colLabel(day, i) {
  const name = tipDay(day.date, i)
  return day.followed_pct == null ? `${name}: no meals planned` : `${name}: ${day.followed_pct}% followed, ${day.logged} of ${day.planned} meals logged`
}
const chartSummary = computed(() => (d.value?.adherence.days || []).map((x, i) => `${i === 6 ? 'today' : weekday(x.date)} ${x.followed_pct ?? 'none'}`).join(', '))
function nameInitials(name) {
  const parts = String(name || '').split(' ').filter(Boolean)
  return userInitials(parts[0], parts[parts.length - 1])
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// a small icon + colour for each activity row, read from its subject
const ACT_KINDS = [
  { test: /pay|invoice|refund|payout|earning/i, tone: 'gold', path: '<rect x="2" y="5" width="20" height="14" rx="2" /><path d="M2 10h20M6 15h4" />' },
  { test: /request|booking/i, tone: 'red', path: '<path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.5 5h13L22 12v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z" />' },
  { test: /lab|result/i, tone: 'blue', path: '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3" />' },
  { test: /meal|plan|log/i, tone: 'green', path: '<path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5" />' },
  { test: /review|rating/i, tone: 'gold', path: '<path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" />' },
  { test: /consult|appointment|soon|starts|session/i, tone: 'green', path: '<circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />' },
]
const actKind = n => ACT_KINDS.find(k => k.test.test(n.subject || '')) || { tone: 'muted', path: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0" />' }

// ---- UI helpers only: date block + time in the schedule card ----
const sdMonth = v => new Date(v).toLocaleDateString('en-PH', { ...PH, month: 'short' }).toUpperCase()
const sdDay = v => new Date(v).toLocaleDateString('en-PH', { ...PH, day: 'numeric' })
const sdWeek = v => new Date(v).toLocaleDateString('en-PH', { ...PH, weekday: 'short' })
const sdTime = v => clock(v).replace(/\s?[AP]M$/i, '')
const sdAmPm = v => (clock(v).match(/[AP]M$/i) || [''])[0].toUpperCase()
function sdFirstUpcoming(group) {
  return group.items.findIndex(a => new Date(a.scheduled_at) > now.value)
}
function sdSoonText(v) {
  const t = untilText(v).replace('in about ', 'In ').replace(/^in /, 'In ')
  return t.replace(' hours', ' hrs').replace(' hour', ' hr').replace(' minutes', ' min').replace(' minute', ' min')
}
</script>

<style scoped>
/* =========================================================
   RND dashboard: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings, numbers), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.rd-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; gap: 18px; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }
.rd-page .nm-error { display: flex; align-items: center; gap: 12px; margin: 0; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 14px; }

/* ---------- HERO ---------- */
.rd-hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
  padding: 30px 32px;
  border-radius: 24px;
  color: #FFFFFF;
  background:
    radial-gradient(120% 140% at 12% -20%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 45%),
    linear-gradient(115deg, #035A45 0%, #004D3A 50%, #004635 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.rd-hero-plate { position: absolute; right: -40px; top: 50%; width: 460px; height: 460px; transform: translateY(-50%); object-fit: cover; border-radius: 50%; opacity: 0.6; pointer-events: none; }
.rd-hero-fade { position: absolute; inset: 0; background: linear-gradient(90deg, #004D3A 0%, #004D3A 45%, rgba(0, 77, 58, 0.35) 100%); pointer-events: none; }
.rd-hero-text { position: relative; z-index: 1; max-width: 520px; }
.rd-eyebrow { margin: 0; display: flex; align-items: center; gap: 10px; font-size: 12.5px; font-weight: 800; color: #EFBF04; }
.rd-eyebrow span { width: 26px; height: 2px; border-radius: 2px; background: #EFBF04; }
.rd-title { margin: 10px 0 12px; font-family: 'Playfair Display', Georgia, serif; font-size: 40px; font-weight: 700; line-height: 1.1; color: #FFFFFF; }
.rd-title em { font-style: italic; color: #EFBF04; }
.rd-hero-sub { margin: 0; display: flex; align-items: flex-start; gap: 8px; font-size: 14.5px; line-height: 1.5; color: rgba(255, 255, 255, 0.88); }
.rd-hero-sub .ic { margin-top: 2px; color: #8FD4A8; }

.rd-next { position: relative; z-index: 1; width: 440px; max-width: 100%; padding: 18px; border-radius: 20px; background: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.18); -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px); }
.rd-next-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.rd-next-k { margin: 0; display: inline-flex; align-items: center; gap: 8px; font-size: 11.5px; font-weight: 800; color: #EFBF04; }
.rd-next-k i { width: 8px; height: 8px; border-radius: 50%; background: #EFBF04; box-shadow: 0 0 0 4px rgba(239, 191, 4, 0.25); }
.rd-paid { flex-shrink: 0; display: inline-flex; align-items: center; height: 24px; padding: 0 10px; border-radius: 999px; background: #FFFFFF; color: #1F7A4C; font-size: 11.5px; font-weight: 800; }
.rd-paid.unpaid { background: rgba(239, 191, 4, 0.2); color: #EFBF04; }
.rd-next-who { display: flex; align-items: center; gap: 12px; margin: 14px 0; }
.rd-next-name { min-width: 0; }
.rd-next-name strong { display: block; font-size: 17px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rd-next-name small { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; color: rgba(255, 255, 255, 0.8); }
.rd-next-empty { margin: 10px 0 14px; font-size: 15px; color: #FFFFFF; }
.rd-next-acts { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.rd-next-acts.one { grid-template-columns: 1fr; }
.rd-av { flex-shrink: 0; width: 48px; height: 48px; border-radius: 50%; object-fit: cover; background: linear-gradient(135deg, #F5CB1F, #C49102); color: #004D3A; display: inline-flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 800; border: 3px solid #FFFFFF; }
.rd-av.sm { width: 42px; height: 42px; font-size: 13px; border-width: 2px; }

/* buttons */
.rd-btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; height: 44px; padding: 0 14px; border: 1px solid transparent; border-radius: 12px; font-family: inherit; font-size: 13.5px; font-weight: 800; text-decoration: none; white-space: nowrap; cursor: pointer; transition: background-color .15s, transform .15s; }
.rd-btn.gold { background: #EFBF04; color: #004D3A; box-shadow: 0 10px 22px -12px rgba(239, 191, 4, 0.9); }
.rd-btn.gold:hover { background: #F5CB1F; transform: translateY(-1px); }
.rd-btn.ghost { background: rgba(255, 255, 255, 0.08); border: 1px dashed rgba(239, 191, 4, 0.6); color: #EFBF04; cursor: default; }
.rd-btn.outline { background: transparent; border-color: rgba(255, 255, 255, 0.45); color: #FFFFFF; }
.rd-btn.outline:hover { background: rgba(255, 255, 255, 0.12); }
.rd-btn.dark { background: #004D3A; color: #FFFFFF; }
.rd-btn.dark:hover { background: #0A5C46; }
.rd-btn.sm { height: 36px; padding: 0 14px; font-size: 13px; }
.rd-btn:focus-visible,
.rd-link:focus-visible { outline: 3px solid rgba(239, 191, 4, 0.6); outline-offset: 2px; }
.rd-link { flex-shrink: 0; display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px; border-radius: 10px; background: #F1F6F2; border: 1px solid #DCE8E0; color: #004D3A; font-family: inherit; font-size: 13px; font-weight: 700; text-decoration: none; white-space: nowrap; cursor: pointer; }
.rd-link:hover { background: #E3EFE7; }

.needs-strip { margin: 0; }
.rd-page .needs-strip {
  border-radius: 14px !important;
  background: #EAF4EE !important;
  border: 1px solid #CFE5D7 !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05), 0 10px 22px -12px rgba(0, 77, 58, 0.25) !important;
  color: #004D3A;
  font-weight: 600;
}

/* ---------- STATS ---------- */
.rd-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.rd-stat { position: relative; overflow: hidden; display: flex; flex-direction: column; padding: 20px 22px 18px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E1E7E3; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); color: inherit; text-decoration: none; transition: transform .2s, box-shadow .2s; }
.rd-stat:hover { transform: translateY(-3px); box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 4px 10px rgba(0, 0, 0, 0.08), 0 20px 40px -10px rgba(0, 0, 0, 0.18), 0 30px 60px -20px rgba(0, 77, 58, 0.3); }
.rd-stat:focus-visible { outline: 3px solid rgba(239, 191, 4, 0.6); outline-offset: 2px; }
.rd-stat::after { display: none; }
.rd-stat-top { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.rd-stat-label { font-size: 14px; font-weight: 700; color: #3E5046; }
.rd-stat-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 14px; display: inline-flex; align-items: center; justify-content: center; background: var(--bg); color: var(--c); }
.rd-stat-val { margin: 8px 0 10px; font-family: 'Playfair Display', Georgia, serif; font-size: 38px; font-weight: 700; line-height: 1; color: #0E3A2C; font-variant-numeric: lining-nums tabular-nums; }
.rd-stat.empty .rd-stat-val { color: #B5C2BA; }
.rd-stat-sub { align-self: flex-start; padding: 4px 10px; border-radius: 999px; background: #F3F6F4; font-size: 12px; font-weight: 600; color: #4A5A52; }

/* ---------- CARDS ---------- */
.rd-grid { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr); gap: 18px; align-items: start; }
.rd-col { display: flex; flex-direction: column; gap: 18px; min-width: 0; }
.rd-card { padding: 22px 24px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E1E7E3; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 2px 6px rgba(0, 0, 0, 0.06), 0 12px 28px -6px rgba(0, 0, 0, 0.12), 0 24px 48px -18px rgba(0, 77, 58, 0.22); }
.rd-head { display: flex; align-items: flex-start; gap: 14px; flex-wrap: wrap; margin-bottom: 16px; }
.rd-head-text { flex: 1 1 220px; min-width: 0; }
.rd-head-ico { flex-shrink: 0; width: 42px; height: 42px; border-radius: 13px; display: inline-flex; align-items: center; justify-content: center; }
.rd-h { margin: 0; display: flex; align-items: center; gap: 8px; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #0E3A2C; }
.rd-sub { margin: 4px 0 0; font-size: 13px; line-height: 1.5; color: #6B7D73; }
.rd-count { min-width: 22px; height: 22px; padding: 0 7px; border-radius: 999px; background: #B42318; color: #FFFFFF; font-family: 'DM Sans', Arial, sans-serif; font-size: 12px; font-weight: 800; display: inline-flex; align-items: center; justify-content: center; }
.rd-muted { margin: 0; font-size: 14px; color: #6B7D73; }
.rd-empty { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border-radius: 14px; border: 1.5px dashed #CFDDD4; background: #F8FBF9; }
.rd-empty > span { flex-shrink: 0; width: 42px; height: 42px; border-radius: 50%; background: #FFFFFF; color: #6B7D73; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 6px 14px -10px rgba(0, 77, 58, 0.6); }
.rd-empty p { margin: 0; font-size: 13.5px; line-height: 1.5; color: #4A5A52; }
.rd-pill { display: inline-flex; align-items: center; height: 26px; padding: 0 12px; border-radius: 999px; font-size: 12px; font-weight: 800; white-space: nowrap; }
.rd-pill.green { background: #EAF4EE; color: #1F7A4C; }
.rd-pill.muted { background: #FBF3D2; color: #8A6400; }

/* schedule */
.day-group + .day-group { margin-top: 16px; }
.day-label { display: flex; align-items: center; gap: 12px; margin: 4px 0 12px; }
.day-label span { padding: 4px 12px; border-radius: 999px; background: #004D3A; color: #FFFFFF; font-size: 12px; font-weight: 800; white-space: nowrap; }
.day-label::after { content: ''; flex: 1; border-top: 1px dashed #DCE5DF; }
.sched-row { display: flex; align-items: center; gap: 14px; }
.sched-row + .sched-row { margin-top: 10px; }
.sched-time { flex-shrink: 0; width: 72px; font-family: 'Playfair Display', Georgia, serif; font-size: 17px; font-weight: 700; color: #0E3A2C; text-align: center; font-variant-numeric: tabular-nums; }
.sched-card { flex: 1; min-width: 0; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding: 12px 14px; border-radius: 16px; background: #F7FAF8; border: 1px solid #EDF2EE; border-left: 4px solid #004D3A; }
.sched-main { flex: 1; min-width: 140px; display: flex; flex-direction: column; }
.sched-name { font-size: 15px; font-weight: 700; color: #0E3A2C; text-decoration: none; }
.sched-name:hover { text-decoration: underline; text-underline-offset: 3px; }
.sched-sub { display: inline-flex; align-items: center; gap: 6px; font-size: 12.5px; color: #6B7D73; }
.sched-end { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.req-pointer { display: flex; align-items: center; gap: 8px; margin: 14px 0 0; padding: 10px 12px; border-radius: 12px; background: #FEF5F4; font-size: 13px; color: #8A1F14; }

/* adherence chart */
.chart-figure { flex-shrink: 0; margin-left: auto; text-align: right; white-space: nowrap; }
.cf-value { display: block; font-family: 'Playfair Display', Georgia, serif; font-size: 30px; font-weight: 700; line-height: 1.1; color: #0E3A2C; font-variant-numeric: tabular-nums; }
.cf-sub { font-size: 12px; color: #6B7D73; }
.chart { margin-top: 6px; padding: 14px 14px 10px; border-radius: 16px; background: #F7FAF8; }
.chart-plot { position: relative; height: 180px; margin: 10px 0 0 34px; }
.grid { position: absolute; left: 0; right: 0; border-top: 1px solid #E3EAE5; }
.grid span { position: absolute; left: -34px; top: -8px; width: 28px; text-align: right; font-size: 11px; color: #8A9A91; font-variant-numeric: tabular-nums; }
.goal { position: absolute; left: 0; right: 0; border-top: 2px dashed #EFBF04; }
.goal span { position: absolute; right: 0; top: -22px; padding: 1px 8px; border-radius: 999px; background: #FDF6DA; font-size: 11px; font-weight: 700; color: #9A7300; }
.cols { position: absolute; inset: 0; display: flex; }
.col { position: relative; flex: 1; display: flex; align-items: flex-end; justify-content: center; outline: none; cursor: default; }
.col:hover,
.col:focus-visible { background: rgba(0, 77, 58, 0.05); border-radius: 8px; }
.bar { width: 28px; max-width: 60%; border-radius: 8px 8px 3px 3px; background: #A8D8BF; transition: background .15s; }
.bar.today { background: linear-gradient(180deg, #1F9D55, #004D3A); }
.col:hover .bar:not(.today),
.col:focus-visible .bar:not(.today) { background: #7CC39F; }
.no-data { margin-bottom: 2px; font-size: 13px; color: #B0BAB0; }
.tip { position: absolute; bottom: calc(100% - 8px); left: 50%; z-index: 5; display: flex; flex-direction: column; gap: 2px; padding: 8px 10px; border-radius: 10px; background: #0E3A2C; color: #FFFFFF; font-size: 12px; white-space: nowrap; transform: translateX(-50%); box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15); pointer-events: none; }
.tip.left { left: auto; right: 0; transform: none; }
.tip-muted { color: #B9CDBF; }
.chart-x { display: flex; margin-left: 34px; padding-top: 8px; border-top: 1px solid #DFE5DF; }
.chart-x span { flex: 1; text-align: center; font-size: 12px; color: #8A9A91; }
.chart-x span.today { color: #0E3A2C; font-weight: 800; }
/* display: block: a hidden <table> otherwise keeps its full size */
.sr-only { position: absolute; display: block; width: 1px; height: 1px; margin: -1px; padding: 0; border: 0; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

/* requests */
.req-row { display: flex; align-items: center; gap: 12px; padding: 12px; border-radius: 14px; background: #F7FAF8; border: 1px solid #EDF2EE; }
.req-row + .req-row { margin-top: 8px; }
.req-main { flex: 1; min-width: 0; }
.req-name { margin: 0; font-size: 14.5px; font-weight: 700; color: #0E3A2C; }
.req-sub { margin: 2px 0 0; font-size: 12.5px; color: #6B7D73; }
.req-soon { display: inline-flex; align-items: center; gap: 5px; margin: 6px 0 0; padding: 2px 8px; border-radius: 999px; background: #EAF4EE; font-size: 11.5px; font-weight: 700; color: #1F5C45; }
.req-soon.urgent { background: #FDECEC; color: #B42318; }

/* earnings */
.rd-earn { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.rd-e { display: flex; flex-direction: column; gap: 4px; min-width: 0; padding: 14px; border-radius: 14px; background: #F7FAF8; border: 1px solid #EDF2EE; }
.rd-e small { font-size: 12px; font-weight: 600; color: #6B7D73; }
.rd-e strong { font-family: 'Playfair Display', Georgia, serif; font-size: 24px; line-height: 1.1; color: #0E3A2C; font-variant-numeric: lining-nums tabular-nums; overflow-wrap: anywhere; }
.rd-e-foot { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.rd-e em { font-style: normal; font-size: 11.5px; color: #8A9A91; }
.rd-e.gold { background: #FFFAEB; border-color: #F3E3A8; }
.rd-e.gold strong { color: #8A6400; }
.rd-note { display: flex; align-items: flex-start; gap: 8px; margin: 12px 0 0; padding: 10px 12px; border-radius: 12px; background: #EAF4EE; font-size: 12.5px; line-height: 1.5; color: #1F5C45; }
.rd-note .ic { margin-top: 2px; }
.rd-note strong { color: #0E3A2C; }

/* reviews */
.overall { flex-shrink: 0; display: inline-flex; align-items: baseline; gap: 4px; padding: 6px 12px; border-radius: 999px; background: #FDF6DA; font-size: 12.5px; color: #6A5410; text-decoration: none; white-space: nowrap; }
.overall strong { font-family: 'Playfair Display', Georgia, serif; font-size: 16px; color: #0E3A2C; }
.overall-star { color: #EFBF04; }
.overall:hover span:last-child { text-decoration: underline; }
.review { margin-top: 10px; padding: 14px; border-radius: 14px; background: #F7FAF8; border: 1px solid #EDF2EE; }
.stars { margin: 0; font-size: 15px; letter-spacing: 1px; color: #EFBF04; }
.stars span { color: #E3E6E3; }
.review-text { margin: 6px 0; font-size: 14px; line-height: 1.55; color: #22362C; overflow-wrap: anywhere; }
.review-by { margin: 0; font-size: 12.5px; color: #6B7D73; }

/* recent activity: a timeline */
.rd-tl { position: relative; display: flex; flex-direction: column; gap: 12px; margin: 0; padding: 0; list-style: none; }
.rd-tl::before { content: ''; position: absolute; left: 17px; top: 10px; bottom: 10px; width: 2px; background: #E3EBE6; }
.activity-row { position: relative; display: flex; align-items: center; gap: 12px; }
.rd-tl-ico { position: relative; z-index: 1; flex-shrink: 0; width: 36px; height: 36px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 0 0 4px #FFFFFF; }
.rd-tl-ico.green { background: #E3EFE7; color: #004D3A; }
.rd-tl-ico.gold { background: #FBF3D2; color: #9A7300; }
.rd-tl-ico.red { background: #FDECEC; color: #B42318; }
.rd-tl-ico.blue { background: #EEF1FA; color: #3B5BA5; }
.rd-tl-ico.muted { background: #F1F3F2; color: #4A5A52; }
.activity-text { flex: 1; min-width: 0; }
.activity-title { margin: 0; font-size: 14px; font-weight: 600; color: #22362C; overflow-wrap: anywhere; }
.unread .activity-title { font-weight: 800; color: #0E3A2C; }
.activity-time { margin: 2px 0 0; font-size: 12px; color: #8A9A91; }
.activity-dot { flex-shrink: 0; width: 9px; height: 9px; border-radius: 50%; background: #EFBF04; box-shadow: 0 0 0 3px rgba(239, 191, 4, 0.2); }

/* ---------- SMALLER SCREENS ---------- */
@media (max-width: 1180px) {
  .rd-next { width: 100%; }
  .rd-grid { grid-template-columns: 1fr; }
}
@media (max-width: 960px) {
  .rd-page { gap: 14px; padding-bottom: 96px; }
  .rd-hero { padding: 22px 18px; border-radius: 22px; }
  .rd-hero-plate { display: none; }
  .rd-title { font-size: 28px; }
  .rd-hero-sub { font-size: 13px; }
  .rd-next { padding: 14px; border-radius: 16px; }
  .rd-btn { height: 42px; padding: 0 8px; font-size: 12.5px; }
  .rd-stats { gap: 8px; }
  .rd-stat { padding: 12px; border-radius: 16px; }
  .rd-stat-top { flex-direction: column-reverse; align-items: flex-start; gap: 8px; }
  .rd-stat-ico { width: 32px; height: 32px; border-radius: 11px; }
  .rd-stat-ico .ic { width: 16px; height: 16px; }
  .rd-stat-label { font-size: 11.5px; line-height: 1.3; }
  .rd-stat-val { margin: 6px 0 8px; font-size: 26px; }
  .rd-stat-sub { padding: 2px 7px; font-size: 10.5px; }
  .rd-card { padding: 16px; border-radius: 18px; }
  .rd-h { font-size: 18px; }
  .rd-head-ico { width: 38px; height: 38px; }
  .sched-row { align-items: flex-start; gap: 10px; }
  .sched-time { width: 52px; padding-top: 14px; font-size: 15px; }
  .chart-figure { margin-left: 0; text-align: left; }
}
@media (max-width: 420px) {
  .rd-earn { grid-template-columns: 1fr; }
  .rd-next-acts { grid-template-columns: 1fr; }
}

/* ===== Schedule card: date block per day ===== */
.sd-dg { display: grid; grid-template-columns: 68px minmax(0, 1fr); gap: 18px; padding: 14px 0; border-top: 1px solid #EEF2EF; }
.rd-head + .sd-dg, .rd-empty + .sd-dg { border-top: none; padding-top: 4px; }
.sd-db { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 72px; border-radius: 16px; background: #F1F5F2; color: #0E3A2C; }
.sd-db small { font-size: 11px; font-weight: 800; color: #6B7D73; }
.sd-db b { font-family: 'Playfair Display', Georgia, serif; font-size: 26px; line-height: 1; }
.sd-db span { font-size: 11.5px; font-weight: 700; color: #4A5A52; }
.sd-dg.is-today .sd-db { background: #004D3A; color: #FFFFFF; }
.sd-dg.is-today .sd-db small { color: #EFBF04; }
.sd-dg.is-today .sd-db span { color: #CFE3D8; }
.sd-dl { display: flex; flex-direction: column; gap: 6px; align-self: center; min-width: 0; }
.sd-ev { display: flex; align-items: center; gap: 14px; padding: 10px 12px; border-radius: 14px; }
.sd-ev:hover { background: #F7FAF8; }
.sd-tm { min-width: 82px; font-size: 17px; font-weight: 800; color: #0E3A2C; white-space: nowrap; }
.sd-tm small { font-size: 11.5px; font-weight: 800; color: #9A7300; }
.sd-av { width: 44px; height: 44px; flex-shrink: 0; border-radius: 50%; object-fit: cover; }
.sd-ini { display: inline-flex; align-items: center; justify-content: center; background: #E3EFE7; color: #004D3A; font-size: 14px; font-weight: 800; }
.sd-ev.is-now .sd-av { box-shadow: 0 0 0 2.5px #FFFFFF, 0 0 0 4.5px #EFBF04; }
.sd-evm { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.sd-evn { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.sd-name { font-size: 15.5px; font-weight: 800; color: #0E3A2C; text-decoration: none; }
.sd-name:hover { text-decoration: underline; }
.sd-evs { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-top: 3px; font-size: 13px; color: #4A5A52; }
.sd-evs svg { color: #1F7A4D; }
.sd-evs i { width: 4px; height: 4px; margin: 0 3px; border-radius: 50%; background: #B5C2BA; }
.sd-pay { font-weight: 800; color: #1F7A4D; }
.sd-pay.muted { color: #8A6400; }
.sd-soon { display: inline-flex; align-items: center; gap: 4px; padding: 2px 9px; border-radius: 999px; background: #FBF3D2; color: #8A6400; font-size: 11.5px; font-weight: 800; }
.sd-go { width: 32px; height: 32px; flex-shrink: 0; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: #6B7D73; }
.sd-ev:hover .sd-go { background: #E3EFE7; color: #004D3A; }
.sd-req { display: flex; align-items: center; gap: 12px; margin-top: 10px; padding: 12px 14px; border-radius: 14px; background: #FDF9E8; text-decoration: none; font-size: 14px; color: #22362C; }
.sd-req-i { width: 34px; height: 34px; flex-shrink: 0; border-radius: 50%; background: #FBF0C4; color: #9A7300; display: inline-flex; align-items: center; justify-content: center; }
.sd-req b { color: #0E3A2C; }
.sd-req em { display: inline-flex; align-items: center; gap: 5px; margin-left: auto; font-style: normal; font-weight: 800; color: #004D3A; white-space: nowrap; }
.sd-req:hover { background: #FBF3D2; }
@media (max-width: 640px) {
  .sd-dg { grid-template-columns: 56px minmax(0, 1fr); gap: 10px; }
  .sd-db { height: 64px; }
  .sd-db b { font-size: 22px; }
  .sd-ev { flex-wrap: wrap; gap: 4px 10px; padding: 8px; }
  .sd-tm { min-width: 0; flex-basis: 100%; font-size: 14px; }
  .sd-av { width: 38px; height: 38px; }
  .sd-go { display: none; }
  .sd-req { font-size: 13px; }
}

/* ===== Up next card: white card + date block (option B) ===== */
.rd-next.un-b { display: flex; gap: 16px; width: 460px; max-width: 100%; padding: 16px; border: none; border-radius: 22px; background: #FFFFFF; color: #0E3A2C; -webkit-backdrop-filter: none; backdrop-filter: none; box-shadow: 0 20px 40px -20px rgba(0, 0, 0, 0.5); }
.un-db { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 72px; flex-shrink: 0; border-radius: 16px; background: #004D3A; color: #FFFFFF; }
.un-db small { font-size: 11px; font-weight: 800; color: #EFBF04; }
.un-db b { font-family: 'Playfair Display', Georgia, serif; font-size: 30px; line-height: 1; }
.un-db span { font-size: 11.5px; font-weight: 700; color: #CFE3D8; }
.un-empty-db { color: #EFBF04; }
.un-m { flex: 1; min-width: 0; }
.un-k { margin: 0 0 8px; font-size: 11.5px; font-weight: 800; color: #9A7300; }
.un-k b { color: #0E3A2C; }
.un-who { display: flex; align-items: center; gap: 10px; }
.un-av { width: 40px; height: 40px; flex-shrink: 0; border-radius: 50%; object-fit: cover; }
.un-ini { display: inline-flex; align-items: center; justify-content: center; background: #E3EFE7; color: #004D3A; font-size: 14px; font-weight: 800; }
.un-name { min-width: 0; flex: 1; }
.un-name strong { display: block; font-size: 15.5px; color: #0E3A2C; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.un-name small { display: inline-flex; align-items: center; gap: 5px; font-size: 12.5px; color: #4A5A52; }
.un-name small svg { color: #1F7A4D; }
.un-paid { display: inline-flex; align-items: center; gap: 4px; flex-shrink: 0; padding: 3px 10px; border-radius: 999px; background: #E3F4EA; color: #1F7A4D; font-size: 12px; font-weight: 800; }
.un-paid.unpaid { background: #FBF3D2; color: #8A6400; }
.un-empty { margin: 0; font-size: 15px; font-weight: 700; color: #0E3A2C; }
.un-acts { display: flex; gap: 8px; margin-top: 12px; }
.un-btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex: 1; height: 40px; padding: 0 12px; border-radius: 12px; font-size: 13px; font-weight: 800; text-decoration: none; white-space: nowrap; }
.un-btn.soft { background: #F1F5F2; color: #4A5A52; font-weight: 700; }
.un-btn.soft svg { color: #9A7300; }
a.un-btn.soft { color: #004D3A; font-weight: 800; }
.un-btn.dark { background: #004D3A; color: #FFFFFF; }
.un-btn.dark svg { color: #EFBF04; }
.un-btn.gold { background: #EFBF04; color: #004D3A; }
.un-btn:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
@media (max-width: 640px) {
  .rd-next.un-b { width: auto; gap: 12px; padding: 14px; }
  .un-db { width: 60px; }
  .un-db b { font-size: 24px; }
  .un-acts { flex-direction: column; }
}

/* date block: compact square, not stretched to the card height */
.un-db { align-self: flex-start; width: 64px !important; height: 68px; padding: 0; border-radius: 14px; }
.un-db b { font-size: 24px !important; }
.un-db small, .un-db span { font-size: 10.5px !important; }
@media (max-width: 640px) { .un-db { width: 56px !important; height: 60px; } .un-db b { font-size: 21px !important; } }

/* Phone: no big green date block (same as the patient dashboard) */
@media (max-width: 640px) {
  .rd-next.un-b .un-db { display: none !important; }
  .un-day { display: inline !important; }
  .un-name strong { white-space: normal; }
  .un-name small { white-space: normal; }
  .un-acts { flex-direction: column; }
}
.un-day { display: none; }

/* Phone: full-width card, proper button height (flex:1 squashed them in a column) */
@media (max-width: 640px) {
  .rd-next.un-b { width: 100% !important; max-width: none !important; box-sizing: border-box; }
  .un-acts { gap: 8px; }
  .un-acts .un-btn { flex: 0 0 auto !important; width: 100%; height: 46px !important; min-height: 46px; font-size: 14px; }
}

/* ===== PHONE: app layout like the patient dashboard ===== */
.rq { display: none; }
.rq-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #10231B; }
.rq-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px 6px; margin-top: 14px; }
.rq-tile { display: flex; flex-direction: column; align-items: center; gap: 7px; font-size: 12px; font-weight: 600; color: #22362C; text-align: center; text-decoration: none; }
.rq-icon { width: 54px; height: 54px; border-radius: 16px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 6px 14px -10px rgba(0, 77, 58, 0.5); transition: transform .15s; }
.rq-tile.gold .rq-icon { background: #FBF6E4; color: #9A7300; }
.rq-tile.dark .rq-icon { background: #004D3A; color: #EFBF04; }
.rq-tile:active .rq-icon { transform: scale(.95); }
.rq-tile:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 3px; border-radius: 12px; }
@media (max-width: 640px) {
  .rq { display: block; margin: 4px 0 6px; }
  /* the top bar already says hi: the banner is just the next consultation */
  .rd-hero { display: block !important; min-height: 0; padding: 18px !important; border-radius: 24px !important; }
  .rd-hero-text { display: none !important; }
  .rd-hero .rd-hero-plate { display: block !important; top: 50% !important; right: -46px !important; left: auto !important; width: 190px !important; height: 190px !important; opacity: 1 !important; box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.08); }
  .rd-hero .rd-hero-fade { display: none !important; }
  .rd-next.un-b { position: relative; z-index: 1; width: calc(100% - 26px) !important; margin: 0; }
}
</style>