<template>
  <div class="profile-page nm-page">
    <p v-if="errorMessage" class="nm-error">{{ errorMessage }}</p>

    <div v-if="isLoading" class="loading-hero"><span class="sk sk-avatar" /><span style="flex: 1"><span class="sk sk-line w40" /><span class="sk sk-line w60" /></span></div>

    <template v-else-if="rnd">
      <p class="breadcrumb"><NuxtLink to="/find-rnd"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 6l-6 6 6 6" /></svg>Find an RND</NuxtLink><span aria-hidden="true">/</span><span class="bc-here">{{ fullName }}</span></p>

      <!-- hero: green banner with the plate, who they are + fee, then the four figures -->
      <section class="hero">
        <div class="hero-banner">
          <span class="hero-kicker">NUTRITIONIST PROFILE</span>
          <img :src="plateImg" class="hero-plate" alt="" />
        </div>

        <div class="hero-body">
          <span class="hero-avatar-wrap">
            <img v-if="rnd.user.profile_photo" :src="rnd.user.profile_photo" class="hero-avatar" alt="" />
            <span v-else class="hero-avatar initials">{{ userInitials(rnd.user.first_name, rnd.user.last_name) }}</span>
            <i aria-hidden="true"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></i>
          </span>

          <div class="hero-main">
            <span v-if="rnd.is_my_rnd" class="hero-tag">★ Your RND</span>
            <h1 class="hero-name">
              {{ fullName }}
              <span class="verified" :title="verifiedTitle" tabindex="0" :aria-label="verifiedTitle"><BadgeCheck :size="22" aria-hidden="true" /></span>
            </h1>
            <p class="hero-spec">{{ rnd.specialization || 'General and clinical nutrition' }}</p>
            <div class="hero-chips">
              <p class="hero-line prc" :title="verifiedTitle">
                <svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6z" /></svg>
                PRC verified
              </p>
              <p v-if="rnd.languages?.length" class="hero-line">
                <Languages :size="15" aria-hidden="true" />
                <span>{{ languagesText }}<button
                  v-if="languageNames.length > 3" type="button" class="lang-more" :aria-expanded="showAllLanguages"
                  @click="showAllLanguages = !showAllLanguages"
                >{{ showAllLanguages ? 'Show less' : `and ${languageNames.length - 3} more` }}</button></span>
              </p>
              <p v-if="offeredFormats.length" class="hero-line"><component :is="offeredFormats[0].icon" :size="15" aria-hidden="true" /> {{ formatsText }}</p>
            </div>
          </div>

          <div class="hero-fee">
            <p class="fee-amount">₱{{ formatFee(rnd.consultation_fee) }}</p>
            <p class="fee-unit">per {{ SESSION_MINUTES }}-minute session</p>
          </div>
        </div>

        <div class="hero-figs">
          <div class="hfig">
            <span class="hfig-ico" aria-hidden="true"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg></span>
            <div class="hfig-text">
              <template v-if="rnd.review_count">
                <p class="hfig-val"><Star :size="15" class="gold" aria-hidden="true" />{{ rnd.average_rating.toFixed(1) }}</p>
                <p class="hfig-label">{{ rnd.review_count }} review{{ rnd.review_count === 1 ? '' : 's' }}</p>
              </template>
              <template v-else>
                <p class="hfig-val">No reviews yet</p>
                <p class="hfig-label">Be the first to review</p>
              </template>
            </div>
          </div>
          <div class="hfig">
            <span class="hfig-ico" aria-hidden="true"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4M9 15l2 2 4-4" /></svg></span>
            <div class="hfig-text">
              <p class="hfig-val">{{ rnd.consultations_completed }}</p>
              <p class="hfig-label">Consultation{{ rnd.consultations_completed === 1 ? '' : 's' }} done</p>
            </div>
          </div>
          <div class="hfig">
            <span class="hfig-ico" aria-hidden="true"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20c.6-3.6 3.2-6 6.5-6s5.9 2.4 6.5 6" /><path d="M16 4.6a3.5 3.5 0 0 1 0 6.8M18 14.4c2 .8 3.2 2.8 3.5 5.6" /></svg></span>
            <div class="hfig-text">
              <p class="hfig-val">{{ rnd.active_patients }}</p>
              <p class="hfig-label">Active patient{{ rnd.active_patients === 1 ? '' : 's' }}</p>
            </div>
          </div>
          <div class="hfig">
            <span class="hfig-ico" aria-hidden="true"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>
            <div class="hfig-text">
              <p class="hfig-val">{{ monthYear(rnd.member_since) }}</p>
              <p class="hfig-label">On NutriMatch since</p>
            </div>
          </div>
        </div>
      </section>

      <div class="nm-grid">
        <div class="nm-col">
          <div class="nm-panel">
            <div class="pn-head">
              <span class="pn-ico"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 21V11" /><path d="M12 13C12 8 9 5 4 5c0 5 3 8 8 8z" /><path d="M12 11c0-4 2.5-6.5 7-6.5 0 4.5-2.5 7-7 7" /></svg></span>
              <div class="pn-text">
                <h2 class="nm-panel-title">About {{ rnd.user.first_name }}</h2>
                <p class="bio-text">{{ rnd.bio || 'This RND has not added a bio yet.' }}</p>
              </div>
            </div>
          </div>

          <div class="nm-panel">
            <div class="pn-head">
              <span class="pn-ico plain"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20s-7.5-4.6-9.2-9.3C1.7 7.4 3.8 4.5 7 4.5c2 0 3.3 1.1 5 3 1.7-1.9 3-3 5-3 3.2 0 5.3 2.9 4.2 6.2C19.5 15.4 12 20 12 20z" /></svg></span>
              <div class="pn-text">
                <h2 class="nm-panel-title">How your care works</h2>
                <p class="nm-panel-sub">NutriMatch follows the Nutrition Care Process used by RNDs.</p>
              </div>
            </div>
            <ol class="steps">
              <li v-for="(st, i) in CARE_STEPS" :key="st.title">
                <span class="step-ico"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="STEP_ICONS[i % STEP_ICONS.length]" /></span>
                <strong>{{ i + 1 }}. {{ st.title }}</strong>
                <span class="step-text">{{ st.text }}</span>
              </li>
            </ol>
          </div>

          <div class="nm-panel meet-panel">
            <svg class="meet-art" width="150" height="96" viewBox="0 0 150 96" fill="none" aria-hidden="true">
              <path d="M18 92c-4-22 4-38 22-46 2 20-6 36-22 46z" fill="#D7EADF" /><path d="M10 92C2 80 2 66 10 56c10 12 10 26 0 36z" fill="#E5F1E9" />
              <path d="M132 92c4-20-2-34-18-42-3 18 4 32 18 42z" fill="#D7EADF" /><path d="M140 92c8-10 9-22 2-32-9 9-10 21-2 32z" fill="#E5F1E9" />
              <rect x="42" y="22" width="66" height="44" rx="5" fill="#FFFFFF" stroke="#2F5A49" stroke-width="2.2" />
              <rect x="47" y="27" width="56" height="34" rx="2" fill="#E8F2EC" />
              <circle cx="75" cy="40" r="6" fill="#2F5A49" /><path d="M64 61c1.5-7 5.5-10.5 11-10.5S84.5 54 86 61z" fill="#3E8E6A" />
              <path d="M34 70h82l-6 6H40z" fill="#2F5A49" />
              <rect x="88" y="76" width="10" height="16" rx="2" fill="#EAF2ED" /><path d="M93 76c-3-6-1-12 4-14 1 6-1 10-4 14z" fill="#3E8E6A" />
            </svg>
            <div class="pn-head">
              <span class="pn-ico plain"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="6" width="13" height="12" rx="2" /><path d="M15.5 10.5l6-3.5v10l-6-3.5" /></svg></span>
              <div class="pn-text">
                <h2 class="nm-panel-title">Where and how you'll meet</h2>
              </div>
            </div>
            <div v-for="f in offeredFormats" :key="f.key" class="nm-row how-row">
              <span class="nm-stat-icon" style="margin: 0"><component :is="f.icon" :size="18" /></span>
              <div class="nm-row-main">
                <p class="nm-row-title">{{ f.label }}</p>
                <p class="nm-row-sub">{{ f.how }}</p>
                <template v-if="f.key === 'in_person'">
                  <p class="address"><MapPin :size="13" /> {{ rnd.clinic_address }}</p>
                  <a :href="mapUrl" target="_blank" rel="noopener" class="nm-btn-soft nm-btn-sm map-link">Open in Google Maps <ExternalLink :size="12" aria-hidden="true" /></a>
                </template>
              </div>
            </div>
            <p v-if="inPersonWithoutAddress" class="nm-note plain-note" style="margin: 12px 0 0">
              {{ rnd.user.first_name }} hasn't added a clinic address yet, so in-person consultations can't be booked for now.
            </p>
          </div>

          <div class="nm-panel">
            <div class="pn-head">
              <span class="pn-ico plain"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg></span>
              <div class="pn-text">
                <h2 class="nm-panel-title">Weekly hours</h2>
                <p class="nm-panel-sub">Philippine time</p>
              </div>
            </div>
            <div v-if="isLoadingAvailability" class="nm-muted" style="margin-top: 12px">Loading…</div>
            <div v-else-if="availabilityByDay.some(d => d.slots.length)" class="avail-grid">
              <div v-for="d in availabilityWeekMonFirst" :key="d.day" class="avail-box" :class="{ muted: !d.slots.length }">
                <p class="avail-day">{{ d.short }}</p>
                <p class="avail-hours">{{ d.slots.length ? d.slots.map(s => compactHours(s.start_time, s.end_time)).join(', ') : '—' }}</p>
              </div>
            </div>
            <p v-else class="nm-muted" style="margin-top: 12px">This RND hasn't set their hours yet.</p>
          </div>

          <div class="nm-panel">
            <div class="pn-head">
              <span class="pn-ico plain"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z" /></svg></span>
              <div class="pn-text"><h2 class="nm-panel-title">Patient reviews</h2></div>
            </div>
            <div v-if="rnd.review_count" class="rating-summary">
              <div class="rating-big">
                <p class="rating-num">{{ rnd.average_rating.toFixed(1) }}</p>
                <p class="rating-stars">{{ starText(Math.round(rnd.average_rating)) }}</p>
                <p class="nm-muted">{{ rnd.review_count }} review{{ rnd.review_count === 1 ? '' : 's' }}</p>
              </div>
              <div class="bars">
                <div v-for="star in [5, 4, 3, 2, 1]" :key="star" class="bar-row">
                  <span>{{ star }}★</span>
                  <span class="bar"><span :style="{ width: `${barPct(star)}%` }" /></span>
                  <span class="bar-n">{{ rnd.rating_breakdown?.[star] || 0 }}</span>
                </div>
              </div>
            </div>
            <div v-if="isLoadingReviews" class="nm-muted" style="margin-top: 12px">Loading reviews…</div>
            <div v-else-if="reviews.length">
              <div v-for="review in reviews" :key="review.id" class="nm-row review-row">
                <div class="nm-row-main">
                  <p class="review-top"><span class="nm-row-title">{{ review.client_name }}</span><span class="rating-stars small">{{ starText(review.rating) }}</span></p>
                  <p v-if="review.comment" class="review-comment">"{{ review.comment }}"</p>
                  <p class="nm-row-sub">{{ shortDate(review.created_at) }}</p>
                </div>
              </div>
            </div>
            <p v-else class="nm-muted" style="margin-top: 12px">No reviews yet. You could be one of {{ rnd.user.first_name }}'s first patients.</p>
          </div>
        </div>

        <!-- booking card -->
        <div class="nm-col side">
          <div class="nm-panel book-card">
            <svg class="book-leaf" width="120" height="120" viewBox="0 0 120 120" fill="currentColor" aria-hidden="true"><path d="M70 120c-4-40 12-74 50-92 6 44-12 78-50 92z" /><path d="M58 120C38 100 34 72 50 46c26 22 30 52 8 74z" opacity=".7" /></svg>
            <template v-if="rnd.is_my_rnd">
              <div class="yours">
                <span class="yours-ico"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg></span>
                <div>
                  <span class="nm-pill green">Your RND</span>
                  <p class="book-text">You're already seeing {{ rnd.user.first_name }}. Your appointments and messages are in one place.</p>
                </div>
              </div>
              <div class="book-links">
                <NuxtLink to="/appointments" class="nm-btn-soft"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg>My appointments</NuxtLink>
                <NuxtLink to="/messages" class="nm-btn-soft"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>Messages</NuxtLink>
              </div>
              <div class="divider" />
            </template>

            <p class="book-fee"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4M8 14h.01M12 14h.01M16 14h.01" /></svg>₱{{ formatFee(rnd.consultation_fee) }} <span>/ {{ SESSION_MINUTES }}-min session</span></p>
            <!-- One RND at a time: booking someone else waits until the current RND discharges them. -->
            <div v-if="rnd.booking_blocked_by" class="one-rnd">
              <p v-if="rnd.booking_blocked_by.status === 'active'">
                You're under <strong>RND {{ rnd.booking_blocked_by.name }}</strong>'s care. You can book a different RND once RND {{ rnd.booking_blocked_by.name }} discharges you. To switch, ask to end your care in Profile Settings, Care team.
              </p>
              <p v-else>
                You have a booking waiting for <strong>RND {{ rnd.booking_blocked_by.name }}</strong>. Cancel it first if you'd like a different RND.
              </p>
              <NuxtLink :to="`/rnd-profile-view/${rnd.booking_blocked_by.rnd_id}`" class="nm-btn-soft nm-btn-sm">Go to RND {{ rnd.booking_blocked_by.name }}</NuxtLink>
            </div>
            <template v-else>
            <p class="nm-section-title" style="margin-top: 14px">Next open times</p>
            <div v-if="rnd.next_open_slots.length" class="slot-grid">
              <button v-for="slot in rnd.next_open_slots" :key="slot" type="button" class="slot" @click="bookSlot(slot)">
                <span class="slot-day">{{ slotDay(slot) }}</span>
                <span class="slot-time">{{ slotTime(slot) }}</span>
              </button>
            </div>
            <p v-else class="nm-muted">No open times in the next 4 weeks.</p>

            <button class="nm-btn-dark book-btn" type="button" :disabled="!offeredFormats.length || !rnd.next_open_slots.length" @click="openBookingModal()">
              <CalendarPlus :size="15" aria-hidden="true" /> {{ rnd.next_open_slots.length ? 'See all times and book' : 'No times available' }}
            </button>
            </template>

            <ul class="policy">
              <li><Clock :size="13" aria-hidden="true" /> Your booking is a request until {{ rnd.user.first_name }} confirms it.</li>
              <li><CreditCard :size="13" aria-hidden="true" /> Pay after {{ rnd.user.first_name }} confirms, at least 15 minutes before the start.</li>
              <li><RotateCcw :size="13" aria-hidden="true" /> Once paid, cancel at least 30 minutes before the start for a full refund.</li>
              <li><UserX :size="13" aria-hidden="true" /> If you don't attend, there's no refund. You can dispute it within 3 days.</li>
            </ul>

            <!-- Only for clients who haven't screened yet — the RND can't
                 confirm a first appointment without it. -->
            <div v-if="hasScreening === false" class="info-note">
              <p>Complete your health screening first. Your RND needs it before they can confirm your first consultation.</p>
              <NuxtLink to="/pre-consultation-screening" class="nm-btn-dark nm-btn-sm">Start screening</NuxtLink>
            </div>
          </div>
        </div>
      </div>

      <!-- PHONE: price and Book stay at the bottom -->
      <div v-if="!rnd.booking_blocked_by && offeredFormats.length && rnd.next_open_slots.length" class="m-bookbar">
        <div><strong>₱{{ formatFee(rnd.consultation_fee) }}</strong><span>{{ SESSION_MINUTES }}-min session</span></div>
        <button type="button" class="hero-book" @click="openBookingModal()"><CalendarPlus :size="16" aria-hidden="true" /> Book</button>
      </div>
    </template>

    <!-- BOOK APPOINTMENT MODAL: header, a scrolling body (format, open days,
         times, notes) and a footer that always shows what's picked + Send. -->
    <div v-if="bookingModalOpen" class="modal-overlay" @click.self="closeBookingModal">
      <div class="booking-modal-box" role="dialog" aria-modal="true" aria-labelledby="bk-title">
        <header class="bk-head">
          <img v-if="rnd.user.profile_photo" :src="rnd.user.profile_photo" class="bk-avatar" alt="" />
          <span v-else class="bk-avatar">{{ userInitials(rnd.user.first_name, rnd.user.last_name) }}</span>
          <div class="bk-head-text">
            <h2 id="bk-title" class="booking-title">Book a consultation with {{ rnd.user.first_name }}</h2>
            <p class="booking-sub">{{ rnd.user.first_name }} confirms your request, then you pay before it starts. Times are Philippine time.</p>
          </div>
          <button class="bk-x" type="button" aria-label="Close" @click="closeBookingModal"><X :size="18" /></button>
        </header>

        <div class="bk-body">
          <div class="bk-grid">
          <div class="bk-left">
          <div class="bk-format">
            <div class="seg" role="radiogroup" aria-label="Format">
              <button
                v-for="f in offeredFormats" :key="f.key"
                type="button" role="radio" :aria-checked="bookingType === f.key"
                class="seg-btn" :class="{ active: bookingType === f.key }"
                @click="bookingType = f.key"
              ><component :is="f.icon" :size="15" aria-hidden="true" /> {{ f.label }}</button>
            </div>
            <p class="bk-fee"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg><strong>₱{{ formatFee(rnd.consultation_fee) }}</strong> · {{ SESSION_MINUTES }} minutes</p>
          </div>
          <p v-if="bookingType === 'in_person'" class="address booking-address"><MapPin :size="13" aria-hidden="true" /> {{ rnd.clinic_address }}</p>

          <section class="bk-section bk-calcard" aria-labelledby="bk-day-h">
            <div class="bk-row-head">
              <h3 id="bk-day-h" class="section-h"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4M9 15l2 2 4-4" /></svg>{{ viewMonthLabel }}</h3>
              <div class="strip-nav">
                <button type="button" aria-label="Previous month" :disabled="!canGoBack" @click="shiftMonth(-1)"><ChevronLeft :size="15" /></button>
                <button type="button" aria-label="Next month" @click="shiftMonth(1)"><ChevronRight :size="15" /></button>
              </div>
            </div>
            <div class="cal">
              <span v-for="d in dayHeaders" :key="d" class="cal-wd" aria-hidden="true">{{ d }}</span>
              <template v-for="cell in calendarCells" :key="cell.iso">
                <span v-if="!cell.inMonth" class="cal-cell out" aria-hidden="true" />
                <button
                  v-else type="button" class="cal-cell"
                  :class="{ open: cell.open, selected: cell.iso === selectedDateISO, today: cell.iso === todayISO, off: cell.dayOff, full: cell.full }"
                  :disabled="!cell.open" :aria-pressed="cell.iso === selectedDateISO" :aria-label="cell.aria"
                  @click="pickDay(cell.iso)"
                >
                  <span class="cal-num">{{ cell.day }}</span>
                  <span v-if="cell.open" class="cal-note">{{ cell.open }} open</span>
                  <span v-else-if="cell.dayOff" class="cal-note">Day off</span>
                  <span v-else-if="cell.full" class="cal-note">Full</span>
                </button>
              </template>
            </div>
            <p v-if="!calendarCells.some(c => c.open)" class="nm-note plain-note cal-empty">No open times in {{ viewMonthLabel }}. Try the next month.</p>
            <p class="cal-legend"><span><i class="lg-open"></i>Open</span><span><i class="lg-sel"></i>Picked</span><span><i class="lg-off"></i>Day off</span></p>
          </section>
          </div>
          <div class="bk-right">

          <div v-if="!selectedDateISO" class="bk-pickday">
            <span class="bk-pickday-ico"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>
            <p>Pick a green day to see the open times.</p>
          </div>
          <section v-if="selectedDateISO" class="bk-section" aria-labelledby="bk-time-h">
            <p class="bk-k"><svg class="ic" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>Open Times</p>
            <h3 id="bk-time-h" class="section-h">{{ selectedDayLabel }}</h3>
            <div v-for="g in timeGroups" :key="g.label" class="tg">
              <span class="tg-label">{{ g.label }}</span>
              <div class="tg-times">
                <template v-for="item in g.items" :key="item.value">
                  <span v-if="item.away" class="t-away">Away {{ item.label }}</span>
                  <span v-else-if="item.taken" class="t-booked" title="Already booked by another client">{{ item.label }}, booked</span>
                  <button
                    v-else type="button" class="t-btn" :class="{ selected: selectedTime === item.value }"
                    :aria-pressed="selectedTime === item.value" @click="selectedTime = item.value"
                  >{{ item.label }}</button>
                </template>
              </div>
            </div>
          </section>

          <section class="bk-section">
            <label for="bk-notes" class="section-h bk-notes-h"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg>Notes for your RND <span class="optional">(optional)</span></label>
            <textarea id="bk-notes" v-model="bookingNotes" data-allow-emoji rows="2" placeholder="Anything you'd like your RND to know before the session..."></textarea>
          </section>
          </div>
          </div>
        </div>

        <footer class="bk-foot">
          <div class="bk-sumbox">
          <span class="bk-sum-ico" :class="{ ready: bookingSummary }"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 7v6M12 16.5h.01" /></svg></span>
          <div class="bk-summary" aria-live="polite">
            <p v-if="bookingSummary" class="bk-pick">{{ bookingSummary }}</p>
            <p v-else class="bk-pick muted">{{ bookingHint }}</p>
            <p v-if="bookingError" class="form-error" role="alert">{{ bookingError }}</p>
            <p v-else class="bk-after">You get an invoice once {{ rnd.user.first_name }} confirms. Pay at least 15 minutes before the start. Once paid, cancel at least 30 minutes before. No refund if you don't attend.</p>
          </div>
          </div>
          <button class="nm-btn-dark bk-send" type="button" :disabled="!canConfirmBooking || isBooking" @click="confirmBooking">
            <svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4M9 15l2 2 4-4" /></svg>{{ isBooking ? 'Sending…' : 'Send booking request' }}
          </button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
const toast = useToast() // the app's toast (2026-11-03)
import {
  BadgeCheck, CalendarPlus, ChevronLeft, ChevronRight, Clock, CreditCard, ExternalLink, Languages,
  MapPin, RotateCcw, Star, UserX, Video, X,
} from 'lucide-vue-next'

const route = useRoute()
const { get, post } = useApi()

const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

const isLoading = ref(true)
const isLoadingReviews = ref(true)
const isLoadingAvailability = ref(true)
const errorMessage = ref('')
const rnd = ref(null)
const reviews = ref([])
const availability = ref([])

const availabilityByDay = computed(() =>
  DAY_NAMES.map((day, dayIndex) => ({
    day,
    slots: availability.value
      .filter(s => s.day_of_week === dayIndex)
      .sort((a, b) => a.start_time.localeCompare(b.start_time)),
  }))
)

// Reference design's Weekly Availability grid runs Mon→Sun, not
// availabilityByDay's Sun-first order (DAY_NAMES/day_of_week both key off
// JS's Sunday=0 convention, which is right for the calendar grid but wrong
// for this display) — reorder without touching the underlying data shape.
const DAY_SHORT = { Sunday: 'Sun', Monday: 'Mon', Tuesday: 'Tue', Wednesday: 'Wed', Thursday: 'Thu', Friday: 'Fri', Saturday: 'Sat' }
const availabilityWeekMonFirst = computed(() => {
  const days = availabilityByDay.value
  return [...days.slice(1), days[0]].map(d => ({ ...d, short: DAY_SHORT[d.day] }))
})

// Short form for the small grid boxes, e.g. "9–5", "1:30–7" (keeps minutes).
function shortTime(t) {
  const [h, m] = t.split(':').map(Number)
  return `${h % 12 || 12}${m ? `:${String(m).padStart(2, '0')}` : ''}`
}
function compactHours(start, end) {
  return `${shortTime(start)}–${shortTime(end)}`
}
function formatFee(fee) {
  return Number(fee).toLocaleString('en-PH', { maximumFractionDigits: 2 })
}

const fullName = computed(() => (rnd.value ? `${rnd.value.user.first_name} ${rnd.value.user.last_name}` : ''))
// Hero sentences: languages ("Speaks English, Filipino, Bisaya and 3 more"),
// formats + city ("Video call or in person, Davao City"), PRC details on the check.
const languageNames = computed(() => (rnd.value?.languages || []).map(l => l.language_name.replace(/ \(.*\)/, '')))
// More than three: the first three, then an "and 3 more" button that opens the rest.
const showAllLanguages = ref(false)
const languagesText = computed(() => {
  const n = languageNames.value
  const list = (xs) => (xs.length > 1 ? `${xs.slice(0, -1).join(', ')} and ${xs.at(-1)}` : xs[0])
  if (n.length <= 3 || showAllLanguages.value) return `Speaks ${list(n)}`
  return `Speaks ${n.slice(0, 3).join(', ')}`
})
const formatsText = computed(() => {
  const labels = offeredFormats.value.map((f, i) => (i ? f.label.toLowerCase() : f.label))
  const city = offeredFormats.value.some(f => f.key === 'in_person') ? (rnd.value?.clinic_address || '').split(',').pop().trim() : ''
  return `${labels.join(' or ')}${city ? `, ${city}` : ''}`
})
const verifiedTitle = computed(() => {
  const r = rnd.value
  if (!r) return ''
  return `PRC verified${r.verified_at ? ` since ${monthYear(r.verified_at)}` : ''}${r.prc_license_number ? `, license no. ${r.prc_license_number}` : ''}`
})
const mapUrl = computed(() => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(rnd.value?.clinic_address || '')}`)
const CARE_STEPS = [
  { title: 'Health screening', text: 'A short form about your height, weight and health so your RND comes prepared.' },
  { title: 'First consultation', text: 'Your RND assesses your diet and health and agrees on goals with you.' },
  { title: 'Your meal plan', text: 'A weekly plan built from Filipino foods, which you can follow and log in the app.' },
  { title: 'Follow-ups', text: 'Regular check-ins to track your progress and adjust the plan.' },
]
const PH = { timeZone: 'Asia/Manila' }
function monthYear(v) {
  return v ? new Date(v).toLocaleDateString('en-PH', { ...PH, month: 'short', year: 'numeric' }) : ''
}
function slotDay(iso) {
  const day = new Date(iso).toLocaleDateString('en-CA', PH)
  if (day === new Date().toLocaleDateString('en-CA', PH)) return 'Today'
  if (day === new Date(Date.now() + 86400000).toLocaleDateString('en-CA', PH)) return 'Tomorrow'
  return new Date(iso).toLocaleDateString('en-PH', { ...PH, weekday: 'short', month: 'short', day: 'numeric' })
}
function slotTime(iso) {
  return new Date(iso).toLocaleTimeString('en-PH', { ...PH, hour: 'numeric', minute: '2-digit' })
}
function starText(n) {
  return '★'.repeat(n) + '☆'.repeat(5 - n)
}
function barPct(star) {
  const n = rnd.value?.rating_breakdown?.[star] || 0
  return rnd.value?.review_count ? Math.round((n / rnd.value.review_count) * 100) : 0
}

async function loadProfile({ quiet = false } = {}) {
  if (!quiet) {
    isLoading.value = true
    errorMessage.value = ''
  }
  try {
    rnd.value = await get(`/client/rnds/${route.params.id}/`)
  } catch {
    if (!quiet) errorMessage.value = 'Could not load this RND profile. Please try again later.'
  } finally {
    isLoading.value = false
  }
}
// open times stay current (the booking pop-up pauses it while open)
useAutoRefresh(() => loadProfile({ quiet: true }))

async function loadReviews() {
  isLoadingReviews.value = true
  try {
    reviews.value = await get(`/client/rnds/${route.params.id}/reviews/`)
  } catch {
    reviews.value = []
  } finally {
    isLoadingReviews.value = false
  }
}

async function loadAvailability() {
  isLoadingAvailability.value = true
  try {
    availability.value = await get(`/client/rnds/${route.params.id}/availability/`)
  } catch {
    availability.value = []
  } finally {
    isLoadingAvailability.value = false
  }
}

// null until known, so the note doesn't flash for clients who have screened.
const hasScreening = ref(null)
async function loadScreeningStatus() {
  try {
    await get('/client/screening/latest/')
    hasScreening.value = true
  } catch (error) {
    hasScreening.value = (error?.response?.status ?? error?.status) === 404 ? false : null
  }
}

onMounted(async () => {
  loadReviews()
  loadAvailability()
  loadScreeningStatus()
  await loadProfile()
  // ?book=1 (e.g. the client dashboard's "Book a Consultation") opens the
  // booking modal straight away.
  if (route.query.book === '1' && offeredFormats.value.length && !rnd.value?.booking_blocked_by) openBookingModal()
})

/* ---------- BOOK APPOINTMENT MODAL ---------- */
const bookingModalOpen = ref(false)
const formats = [
  { key: 'video', label: 'Video call', short: 'Video call', icon: Video, how: 'Right in your browser, no app to install. The Join button appears in My Appointments 15 minutes before the start, once you\'ve paid.' },
  { key: 'in_person', label: 'In person', short: 'In person', icon: MapPin, how: 'Visit the clinic at your booked time.' },
]
// In-person needs a clinic address on file (the API refuses it otherwise).
const offeredFormats = computed(() => formats.filter(f => rnd.value?.consultation_modes?.includes(f.key)
  && (f.key !== 'in_person' || rnd.value?.clinic_address)))
const inPersonWithoutAddress = computed(() => rnd.value?.consultation_modes?.includes('in_person') && !rnd.value?.clinic_address)
const bookingType = ref('video')
const selectedDateISO = ref('')
const selectedTime = ref('')
const bookingNotes = ref('')
const isBooking = ref(false)
const bookingError = ref('')

// Local-calendar-date formatting — Date#toISOString() converts to UTC first,
// which shifts a local midnight back a day in any UTC+ timezone (e.g. PHT,
// UTC+8) and silently mis-gates "today" by one day.
function toISO(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
const todayISO = toISO(new Date())

// Gated by the RND's real RndAvailabilitySchedule rows (already loaded via
// loadAvailability), not mock data — a day is bookable only if it has at
// least one is_available slot.
function scheduleForDate(date) {
  return availability.value.filter(s => s.day_of_week === date.getDay())
}
// A day is only highlighted if it still has at least one bookable time —
// otherwise picking it would show no times and Confirm could never enable
// (e.g. today after the RND's last slot, or hours shorter than a session).
// The month calendar. A day is green with its count while it still has an open
// time; past days and days without hours are faint; a day the RND blocked off
// is striped "Day off", a day with every time taken says "Full".
const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const viewMonth = ref(new Date(new Date().getFullYear(), new Date().getMonth(), 1))
const viewMonthLabel = computed(() => viewMonth.value.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }))
const canGoBack = computed(() => {
  const now = new Date()
  return viewMonth.value > new Date(now.getFullYear(), now.getMonth(), 1)
})
function shiftMonth(delta) {
  viewMonth.value = new Date(viewMonth.value.getFullYear(), viewMonth.value.getMonth() + delta, 1)
}
const calendarCells = computed(() => {
  const year = viewMonth.value.getFullYear()
  const month = viewMonth.value.getMonth()
  const gridStart = new Date(year, month, 1 - new Date(year, month, 1).getDay())
  const weeks = Math.ceil((new Date(year, month, 1).getDay() + new Date(year, month + 1, 0).getDate()) / 7)
  const cells = []
  for (let i = 0; i < weeks * 7; i++) {
    const d = new Date(gridStart.getFullYear(), gridStart.getMonth(), gridStart.getDate() + i)
    const iso = toISO(d)
    const inMonth = d.getMonth() === month
    const future = iso >= todayISO
    const slots = inMonth && future ? slotsForDate(iso) : []
    const open = slots.filter(t => !t.taken).length
    const dayOff = !open && slots.length > 0 && slots.every(t => t.off)
    const full = !open && !dayOff && slots.length > 0
    const long = d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
    cells.push({
      iso, inMonth, open, dayOff, full, day: d.getDate(),
      aria: open ? `${long}, ${open} open` : dayOff ? `${long}, day off` : full ? `${long}, fully booked` : long,
    })
  }
  return cells
})
function pickDay(iso) {
  if (iso === selectedDateISO.value) return
  selectedDateISO.value = iso
  selectedTime.value = ''
}
// The first day with an open time, looking up to 60 days ahead.
function firstOpenDay() {
  const now = new Date()
  for (let i = 0; i < 60; i++) {
    const iso = toISO(new Date(now.getFullYear(), now.getMonth(), now.getDate() + i))
    if (slotsForDate(iso).some(t => !t.taken)) return iso
  }
  return ''
}
const selectedDayLabel = computed(() => (selectedDateISO.value
  ? new Date(selectedDateISO.value + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
  : ''))
// Times split into morning / afternoon / evening. Booked times stay visible
// (greyed); a run of blocked-off hours shows as one "Away 9:00 AM to 12:00 PM".
const timeGroups = computed(() => {
  const groups = [
    { label: 'Morning', test: h => h < 12, items: [] },
    { label: 'Afternoon', test: h => h >= 12 && h < 17, items: [] },
    { label: 'Evening', test: h => h >= 17, items: [] },
  ]
  // A run of blocked hours stays one item, filed under the part of day it starts in.
  let run = null
  for (const slot of timeSlots.value) {
    if (slot.off) {
      const endLabel = clockLabel(minutesOf(slot.value) + SESSION_MINUTES)
      if (run) { run.label = `${run.from} to ${endLabel}`; continue }
      run = { value: slot.value, away: true, from: slot.label, label: `${slot.label} to ${endLabel}` }
      groups.find(g => g.test(Number(slot.value.slice(0, 2)))).items.push(run)
    } else {
      run = null
      groups.find(g => g.test(Number(slot.value.slice(0, 2)))).items.push(slot)
    }
  }
  return groups.filter(g => g.items.length)
})
function minutesOf(t) { const [h, m] = t.split(':').map(Number); return h * 60 + m }
function clockLabel(min) {
  const h = Math.floor(min / 60) % 24
  const m = min % 60
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}
const bookingSummary = computed(() => {
  if (!selectedDateISO.value || !selectedTime.value) return ''
  const fmt = offeredFormats.value.find(f => f.key === bookingType.value)?.label || ''
  const day = new Date(selectedDateISO.value + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  return `${fmt}, ${day}, ${clockLabel(minutesOf(selectedTime.value))}`
})

// Bookings are 60 minutes. Start times step every hour from the RND's start
// time while a full session still fits before their end time (e.g.
// 1:30 PM–7:00 PM → 1:30, 2:30 … 5:30 PM) — same grid the server enforces
// (scheduling/serializers.py SLOT_STEP_MINUTES). Today, a time must be at
// least MIN_LEAD_MINUTES away.
const SESSION_MINUTES = 60
const SLOT_STEP_MINUTES = 60
const MIN_LEAD_MINUTES = 45 // MIN_BOOKING_LEAD_MINUTES: 30 for the RND to confirm + 15 for you to pay
const timeSlots = computed(() => (selectedDateISO.value ? slotsForDate(selectedDateISO.value) : []))

function slotsForDate(iso) {
  const date = new Date(iso + 'T00:00:00')
  const isToday = iso === todayISO
  const now = new Date()
  const nowMinutes = now.getHours() * 60 + now.getMinutes()
  const toMinutes = (t) => { const [h, m] = t.split(':').map(Number); return h * 60 + m }
  const seen = new Set()
  const slots = []
  for (const s of scheduleForDate(date)) {
    const end = s.end_time.slice(0, 5) === '00:00' ? 24 * 60 : toMinutes(s.end_time) // 12:00 AM = end of the day
    for (let start = toMinutes(s.start_time); start + SESSION_MINUTES <= end; start += SLOT_STEP_MINUTES) {
      if (isToday && start < nowMinutes + MIN_LEAD_MINUTES) continue
      const h = Math.floor(start / 60)
      const m = start % 60
      const value = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`
      if (seen.has(value)) continue
      seen.add(value)
      // Times already booked, or blocked off by the RND, stay visible but can't be picked.
      const taken = isSlotTaken(iso, start)
      slots.push({ value, label: `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`, taken: !!taken, off: taken === 'time_off' })
    }
  }
  return slots.sort((a, b) => a.value.localeCompare(b.value))
}

const bookingHint = computed(() => {
  if (!selectedDateISO.value) return 'Pick a green day to see the open times.'
  if (!selectedTime.value) return 'Pick a time.'
  return ''
})

const canConfirmBooking = computed(() => selectedDateISO.value !== '' && selectedTime.value !== ''
  && !timeSlots.value.find(s => s.value === selectedTime.value)?.taken)
// A time picked (e.g. from "Next available") that turns out to be booked is cleared.
watch(timeSlots, (slots) => {
  if (selectedTime.value && slots.find(s => s.value === selectedTime.value)?.taken) selectedTime.value = ''
})

// Times this RND is already booked or has blocked off (start/end/kind only), so they aren't offered.
const bookedSlots = ref([])
async function loadBookedSlots() {
  try {
    const rows = await get(`/client/rnds/${route.params.id}/booked-slots/`)
    bookedSlots.value = rows.map(r => ({ start: new Date(r.start).getTime(), end: new Date(r.end).getTime(), kind: r.kind || 'booked' }))
  } catch {
    bookedSlots.value = []
  }
}
function slotHits(iso, minutes) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  const start = new Date(`${iso}T${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`).getTime()
  const end = start + SESSION_MINUTES * 60000
  return bookedSlots.value.filter(b => b.start < end && start < b.end)
}
// 'booked' (another booking), 'time_off' (the RND blocked it) or null (open).
function isSlotTaken(iso, minutes) {
  const hits = slotHits(iso, minutes)
  if (!hits.length) return null
  return hits.some(b => b.kind === 'booked') ? 'booked' : 'time_off'
}
async function openBookingModal(slotIso = null) {
  bookingType.value = offeredFormats.value[0]?.key || 'video'
  selectedDateISO.value = ''
  selectedTime.value = ''
  bookingNotes.value = ''
  bookingError.value = ''
  if (slotIso) {
    // The strip works in the browser's local time, like the slot list.
    const d = new Date(slotIso)
    selectedDateISO.value = toISO(d)
    selectedTime.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  }
  bookingModalOpen.value = true
  await loadBookedSlots()
  // Nothing picked yet (or that day is now full): start on the first open day.
  if (!selectedDateISO.value || !slotsForDate(selectedDateISO.value).some(t => !t.taken)) {
    selectedDateISO.value = firstOpenDay()
    selectedTime.value = ''
  }
  const shown = selectedDateISO.value ? new Date(selectedDateISO.value + 'T00:00:00') : new Date()
  viewMonth.value = new Date(shown.getFullYear(), shown.getMonth(), 1)
}
function bookSlot(iso) {
  openBookingModal(iso)
}
function closeBookingModal() {
  bookingModalOpen.value = false
}
function onBookingKey(e) { if (e.key === 'Escape' && bookingModalOpen.value) closeBookingModal() }
onMounted(() => window.addEventListener('keydown', onBookingKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onBookingKey))

async function confirmBooking() {
  if (!canConfirmBooking.value) return
  isBooking.value = true
  bookingError.value = ''
  try {
    await post('/client/appointments/', {
      rnd_id: rnd.value.user.id,
      scheduled_at: new Date(`${selectedDateISO.value}T${selectedTime.value}`).toISOString(),
      type: bookingType.value,
      duration_minutes: SESSION_MINUTES,
      notes: bookingNotes.value || undefined,
    })
    const rndName = rnd.value.user.first_name
    closeBookingModal()
    await navigateTo('/appointments')
    toast.success(`Booking request sent. We'll tell you when RND ${rndName} confirms it.`, { duration: 6000 })
  } catch (error) {
    const data = error?.data || {}
    bookingError.value = data.detail || data.non_field_errors?.[0] || data.scheduled_at?.[0] || data.type?.[0]
      || data.duration_minutes?.[0] || data.rnd_id?.[0] || 'Could not book this appointment. Please try again.'
    // The slot may have just been taken — refresh what's open.
    if (data.scheduled_at) {
      selectedTime.value = ''
      await loadBookedSlots()
    }
  } finally {
    isBooking.value = false
  }
}

/* ---------- UI only ---------- */
const plateImg = '/landing/login-plate.webp'
// icons for the four care steps (screening, consultation, meal plan, follow-ups)
const STEP_ICONS = [
  '<rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6M9 17.5h3" />',
  '<path d="M6 3v5a4 4 0 0 0 8 0V3" /><path d="M10 12v2a5 5 0 0 0 10 0v-2" /><circle cx="20" cy="10" r="2" />',
  '<path d="M3 12h18a9 9 0 0 1-18 0z" /><path d="M8 12c0-3 1.5-5 4-6M12 12c0-2.5 1.5-4 4-4.5M7.5 8.5C9 7 10 5.5 10 4" />',
  '<path d="M4 20h16" /><path d="M7 16v-3M11 16v-6M15 16v-4M19 16V7" /><path d="M5 11l5-4 4 3 5-5" />',
]
</script>

<style scoped>
/* =========================================================
   RND profile: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings, numbers), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }
.profile-page { font-family: 'DM Sans', 'Inter', Arial, sans-serif; color: #14261E; display: flex; flex-direction: column; gap: 20px; }
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }
.profile-page .nm-error { margin: 0; padding: 12px 16px; border-radius: 14px; background: #FEF3F2; border: 1px solid #FECDCA; color: #B42318; font-size: 14px; }
.profile-page .nm-muted { color: #6B7D73; font-size: 14px; }

/* breadcrumb */
.breadcrumb { margin: 0; display: flex; align-items: center; gap: 8px; font-size: 13.5px; color: #6B7D73; }
.breadcrumb :deep(a) { display: inline-flex; align-items: center; gap: 4px; color: #004D3A; font-weight: 700; text-decoration: none; }
.breadcrumb :deep(a:hover) { text-decoration: underline; text-underline-offset: 3px; }
.bc-here { font-weight: 600; color: #22362C; }

/* ---------- HERO ---------- */
.hero {
  position: relative;
  overflow: hidden;
  margin: 0;
  border-radius: 22px;
  background: #FFFFFF;
  color: #10231B;
  border: 1px solid #E3EDE5;
  box-shadow: 0 1px 2px rgba(16, 35, 27, 0.06), 0 6px 14px -4px rgba(16, 35, 27, 0.1), 0 22px 40px -18px rgba(16, 35, 27, 0.28);
}
.hero-banner { position: relative; height: 140px; background: #00503E; overflow: hidden; }
.hero-kicker { position: absolute; left: 36px; top: 28px; display: flex; align-items: center; gap: 10px; font-size: 12px; font-weight: 700; letter-spacing: .18em; color: #F2C230; }
.hero-kicker::before { content: ''; width: 26px; height: 2px; background: #F2C230; }
.hero-plate { position: absolute; right: 0; top: 0; width: 340px; height: 100%; object-fit: cover; object-position: right center; opacity: .6; }
.hero-banner::after { content: ''; position: absolute; right: 0; top: 0; width: 340px; height: 100%; background: linear-gradient(90deg, #00503E 0%, rgba(0, 80, 62, .55) 45%, rgba(0, 80, 62, 0) 100%); }

.hero-body { position: relative; display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; min-height: 112px; padding: 0 36px 20px 186px; }
.hero-avatar-wrap { position: absolute; left: 36px; top: -62px; width: 124px; height: 124px; }
.hero-avatar { display: block; width: 124px; height: 124px; border-radius: 50%; object-fit: cover; border: 5px solid #FFFFFF; box-shadow: 0 6px 18px rgba(0, 60, 45, .22); }
.hero-avatar.initials { display: flex; align-items: center; justify-content: center; background: linear-gradient(145deg, #F6CF3F 0%, #D9A716 100%); color: #00503E; font-family: 'Playfair Display', Georgia, serif; font-size: 44px; font-weight: 700; }
.hero-avatar-wrap i { position: absolute; right: 2px; bottom: 6px; width: 34px; height: 34px; border-radius: 50%; background: #00503E; color: #F2C230; border: 3px solid #FFFFFF; display: inline-flex; align-items: center; justify-content: center; }
.hero-main { flex: 1; min-width: 0; padding-top: 18px; }
.hero-tag { display: inline-flex; align-items: center; height: 24px; margin-bottom: 8px; padding: 0 10px; border-radius: 999px; background: #FDF6DA; color: #8A6700; font-size: 11.5px; font-weight: 800; letter-spacing: .4px; }
.hero-name { margin: 0; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-family: 'Playfair Display', Georgia, serif; font-size: 34px; line-height: 1.1; font-weight: 700; color: #00402F; }
.verified { display: inline-flex; color: #FFFFFF; cursor: help; border-radius: 50%; }
.verified :deep(svg) { fill: #00503E; }
.verified:focus-visible { outline: 2px solid #004D3A; outline-offset: 2px; }
.hero-spec { margin: 2px 0 12px; font-size: 15px; font-weight: 600; color: #00673F; }
.hero-chips { display: flex; flex-wrap: wrap; gap: 8px 10px; }
.hero-line { display: inline-flex; align-items: center; gap: 8px; min-height: 32px; margin: 0; padding: 4px 14px; border-radius: 16px; background: #EEF3EF; font-size: 13px; font-weight: 500; color: #2C3D36; }
.hero-line svg { flex-shrink: 0; color: #1F7A4D; }
.hero-line.prc { background: #FDF3D2; color: #6D5200; font-weight: 600; }
.hero-line.prc svg { color: #6D5200; }
.lang-more { margin-left: 6px; min-height: 22px; padding: 0 10px; border: none; border-radius: 999px; background: #E3EFE7; color: #004D3A; font-family: inherit; font-size: 12px; font-weight: 700; cursor: pointer; vertical-align: middle; }
.lang-more:hover { background: #D3E6DA; }
.gold { color: #EFBF04; fill: #EFBF04; }
.hero-fee { flex-shrink: 0; padding-top: 18px; text-align: right; }
.fee-amount { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 34px; font-weight: 700; line-height: 1.1; color: #00402F; }
.fee-unit { margin: 4px 0 0; font-size: 13px; color: #4A5C54; }

/* the four figures */
.hero-figs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; padding: 18px 36px 20px; border-top: 1px solid #E3EAE6; }
.hfig { min-width: 0; display: flex; align-items: center; gap: 14px; }
.hfig-ico { flex-shrink: 0; width: 44px; height: 44px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; background: #E3F1EA; color: #00503E; }
.hfig:nth-child(1) .hfig-ico { background: #EEF1FB; color: #3A4A9F; }
.hfig:nth-child(3) .hfig-ico { background: #FDF3D2; color: #8A6600; }
.hfig-text { min-width: 0; }
.hfig-val { margin: 0; display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 600; color: #1B2B25; }
.hfig-label { margin: 2px 0 0; font-size: 13px; color: #55665E; }

/* "Book" button: now only used by the phone bar at the bottom */
.hero-book {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  height: 48px;
  padding: 0 30px;
  border: none;
  border-radius: 14px;
  background: #0E4D38;
  color: #FFFFFF;
  font-family: inherit;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 12px 22px -14px rgba(0, 77, 58, 0.9);
  transition: background-color .15s;
}
.hero-book:hover { background: #136047; }
.hero-book:focus-visible { outline: 3px solid #EFBF04; outline-offset: 2px; }

/* ---------- GRID + PANELS ---------- */
.profile-page .nm-grid { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); gap: 22px; align-items: start; }
.profile-page .nm-col { display: flex; flex-direction: column; gap: 18px; min-width: 0; }
.profile-page .nm-panel {
  position: relative;
  padding: 22px 26px;
  border-radius: 20px;
  background: #FFFFFF;
  border: 1px solid #E4EBE6;
  box-shadow: 0 1px 2px rgba(16, 35, 27, 0.06), 0 6px 14px -4px rgba(16, 35, 27, 0.1), 0 20px 36px -18px rgba(16, 35, 27, 0.26);
}
.pn-head { display: flex; align-items: flex-start; gap: 16px; }
.pn-ico { flex-shrink: 0; width: 46px; height: 46px; border-radius: 50%; background: #EEF5F0; color: #1F5C45; display: inline-flex; align-items: center; justify-content: center; }
.pn-ico.plain { width: 30px; height: 30px; background: none; color: #1F5C45; margin-top: 1px; }
.pn-text { flex: 1; min-width: 0; }
.profile-page .nm-panel-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-weight: 700; color: #0E3A2C; }
.profile-page .nm-panel-sub { margin: 4px 0 0; font-size: 13.5px; color: #4A5A52; }
.bio-text { margin: 6px 0 0; font-size: 14.5px; line-height: 1.65; color: #3E5046; white-space: pre-line; }

/* how your care works: four steps in a row with arrows */
.steps { list-style: none; margin: 20px 0 4px; padding: 0; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px 28px; }
.steps li { position: relative; display: flex; flex-direction: column; align-items: center; text-align: center; font-size: 14px; color: #10231B; }
.steps li + li::before { content: '›'; position: absolute; left: -22px; top: 14px; font-size: 22px; line-height: 1; color: #3E5046; }
.step-ico { width: 56px; height: 56px; margin-bottom: 12px; border-radius: 50%; background: #EEF5F0; color: #1F5C45; display: inline-flex; align-items: center; justify-content: center; }
.steps strong { font-weight: 700; color: #0E3A2C; }
.step-text { display: block; margin-top: 6px; font-size: 12.5px; line-height: 1.55; color: #4A5A52; }

/* where you'll meet */
.meet-panel { overflow: hidden; }
.meet-art { position: absolute; right: 20px; bottom: 6px; opacity: .95; pointer-events: none; }
.meet-panel .pn-head,
.meet-panel .nm-row,
.meet-panel .nm-note { position: relative; z-index: 1; }
.meet-panel .nm-row-main { padding-right: 150px; }
.profile-page .nm-row { display: flex; gap: 14px; padding: 14px 0; }
.profile-page .nm-row + .nm-row { border-top: 1px solid #EEF2EF; }
.how-row { align-items: flex-start; }
.how-row:first-of-type { margin-top: 6px; }
.profile-page .nm-stat-icon { flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%; background: #EEF5F0; color: #1F5C45; display: inline-flex; align-items: center; justify-content: center; }
.how-row + .how-row .nm-stat-icon { background: #FBF6E4; color: #9A7300; }
.profile-page .nm-row-main { flex: 1; min-width: 0; }
.profile-page .nm-row-title { margin: 0; font-size: 15px; font-weight: 700; color: #10231B; }
.profile-page .nm-row-sub { margin: 3px 0 0; font-size: 13px; line-height: 1.55; color: #4A5A52; }
.address { display: flex; align-items: flex-start; gap: 6px; margin: 8px 0 10px; font-size: 13px; font-weight: 600; line-height: 1.45; color: #3E5046; }
.address svg { flex-shrink: 0; margin-top: 2px; color: #7A8F84; }
.map-link { display: inline-flex; align-items: center; gap: 6px; }

/* weekly hours */
.avail-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 16px; }
.avail-box { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px 4px; border-radius: 14px; background: #EEF6F0; border: 1px solid #DCEBE1; text-align: center; }
.avail-box.muted { background: #F5F7F6; border-color: transparent; }
.avail-day { margin: 0; font-size: 13px; font-weight: 800; color: #0E3A2C; }
.avail-hours { margin: 0; font-size: 12px; font-weight: 600; color: #1F7A4D; }
.avail-box.muted .avail-day,
.avail-box.muted .avail-hours { color: #9AA9A1; }

/* reviews */
.rating-summary { display: flex; gap: 24px; align-items: center; flex-wrap: wrap; margin: 14px 0 6px; padding: 16px; border-radius: 16px; background: #F3F8F5; }
.rating-big { min-width: 110px; text-align: center; }
.rating-num { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 40px; font-weight: 700; line-height: 1; color: #10231B; }
.rating-stars { margin: 4px 0; color: #EFBF04; letter-spacing: 1px; }
.rating-stars.small { font-size: 13px; }
.bars { flex: 1; min-width: 200px; display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: grid; grid-template-columns: 30px 1fr 24px; gap: 10px; align-items: center; font-size: 12.5px; font-weight: 600; color: #5D7065; }
.bar { height: 8px; border-radius: 99px; background: #E6ECE8; overflow: hidden; }
.bar span { display: block; height: 100%; border-radius: 99px; background: #EFBF04; }
.bar-n { text-align: right; }
.review-row { display: block; }
.review-top { display: flex; justify-content: space-between; gap: 10px; margin: 0 0 4px; }
.review-comment { margin: 0 0 4px; padding: 8px 12px; border-left: 3px solid #EFBF04; border-radius: 0 10px 10px 0; background: #FBF8EC; font-size: 14px; line-height: 1.55; color: #3E5046; }

/* ---------- BOOKING CARD ---------- */
.side { position: sticky; top: 96px; }
.profile-page .book-card { display: flex; flex-direction: column; overflow: hidden; padding: 24px 24px 22px; }
.book-leaf { position: absolute; right: -14px; bottom: -14px; color: #DCEBE1; pointer-events: none; }
.book-card > :not(.book-leaf) { position: relative; z-index: 1; }
.yours { display: flex; gap: 12px; align-items: flex-start; padding: 12px 14px; border-radius: 14px; background: linear-gradient(90deg, #EAF4EE, #F7F3E2); }
.yours-ico { flex-shrink: 0; width: 32px; height: 32px; border-radius: 10px; background: #004D3A; color: #EFBF04; display: inline-flex; align-items: center; justify-content: center; }
.profile-page .nm-pill { display: inline-flex; align-items: center; height: 22px; padding: 0 9px; border-radius: 999px; font-size: 11.5px; font-weight: 800; }
.profile-page .nm-pill.green { background: #004D3A; color: #EFBF04; }
.book-text { margin: 6px 0 0; font-size: 13px; line-height: 1.5; color: #3E5046; }
.book-links { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
.divider { height: 1px; margin: 18px 0 4px; background: #EEF2EF; }
.book-fee { margin: 0; padding-bottom: 16px; border-bottom: 1px solid #EEF2EF; display: flex; align-items: center; gap: 10px; font-family: 'Playfair Display', Georgia, serif; font-size: 26px; font-weight: 700; color: #0E3A2C; }
.book-fee .ic { color: #1F5C45; margin-right: 4px; }
.book-fee span { font-family: 'DM Sans', Arial, sans-serif; font-size: 13.5px; font-weight: 500; color: #4A5A52; }
.profile-page .nm-section-title { margin: 16px 0 12px !important; font-size: 13.5px; font-weight: 700; letter-spacing: 0.6px; text-transform: uppercase; color: #1F7A4D; }
.slot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.slot-grid .slot { display: flex; flex-direction: column; align-items: flex-start; gap: 3px; padding: 10px 14px; border: 1px solid #DDEAE1; border-radius: 12px; background: #F3F8F5; font-family: inherit; text-align: left; cursor: pointer; transition: border-color .15s, background-color .15s, color .15s; }
.slot-grid .slot:hover { border-color: #0E4D38; background: #0E4D38; }
.slot-grid .slot:hover .slot-day,
.slot-grid .slot:hover .slot-time { color: #FFFFFF; }
.slot-grid .slot:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.slot-day { font-size: 11.5px; font-weight: 600; color: #22362C; }
.slot-time { font-size: 15px; font-weight: 700; color: #0E3A2C; }
.profile-page .book-btn { width: 100%; height: 50px !important; margin-top: 16px; border-radius: 14px; background: #0E4D38; }
.policy { list-style: none; margin: 18px 0 0; padding: 0; display: flex; flex-direction: column; gap: 12px; }
.policy li { display: flex; gap: 12px; align-items: flex-start; font-size: 12.5px; line-height: 1.5; color: #22362C; }
.policy svg { flex-shrink: 0; margin-top: 1px; color: #1F5C45; }
/* screening still to do */
.info-note { display: flex; flex-direction: column; align-items: flex-start; gap: 10px; margin-top: 16px; padding: 12px 14px; border-radius: 14px; background: #FBF6E4; border: 1.5px dashed #E2C35A; color: #4A3E10; font-size: 13px; line-height: 1.5; }
.info-note p { margin: 0; }
.one-rnd { margin-top: 14px; padding: 12px 14px; border-radius: 14px; background: #FBF8EC; border: 1px solid #F1E2A6; font-size: 13px; line-height: 1.55; color: #4A3E10; }
.one-rnd p { margin: 0 0 10px; }

/* buttons on this page */
.profile-page .nm-btn-dark,
.profile-page .nm-btn-soft {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  height: 42px;
  padding: 0 16px;
  border: none;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color .15s;
}
.profile-page .nm-btn-sm { height: 36px; padding: 0 14px; font-size: 13px; }
.profile-page .nm-btn-dark { background: #004D3A; color: #FFFFFF; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.profile-page .nm-btn-dark:hover:not(:disabled) { background: #0A5C46; }
.profile-page .nm-btn-dark:disabled { opacity: .5; cursor: not-allowed; box-shadow: none; }
.profile-page .nm-btn-soft { background: #F1F6F2; color: #004D3A; }
.profile-page .nm-btn-soft:hover { background: #E3EFE7; }
.profile-page .nm-note { padding: 12px 14px; border-radius: 12px; background: #F7FAF8; font-size: 13px; line-height: 1.5; color: #4A5A52; }

/* phone: price + Book stay at the bottom */
.m-bookbar { display: none; }

/* loading */
.loading-hero { display: flex; gap: 20px; align-items: center; padding: 28px; border-radius: 24px; background: #FFFFFF; border: 1px solid #E1E7E3; }
.sk { display: block; background: linear-gradient(90deg, #F0F2F0 25%, #E6EAE6 50%, #F0F2F0 75%); background-size: 200% 100%; animation: shimmer 1.2s infinite; border-radius: 8px; }
.sk-avatar { width: 108px; height: 108px; border-radius: 32px; flex-shrink: 0; }
.sk-line { height: 14px; margin: 8px 0; }
.w60 { width: 60%; } .w40 { width: 40%; }
@keyframes shimmer { to { background-position: -200% 0; } }

@media (max-width: 1200px) {
  .profile-page .nm-grid { grid-template-columns: 1fr; }
  .side { position: static; order: -1; }
  .steps { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .steps li:nth-child(3)::before { display: none; }
}

/* phone + tablet */
@media (max-width: 960px) {
  .profile-page { gap: 16px; padding-bottom: 96px; }
  .hero { border-radius: 22px; }
  .hero-banner { height: 104px; }
  .hero-kicker { left: 18px; top: 20px; font-size: 11px; }
  .hero-plate,
  .hero-banner::after { width: 200px; }
  .hero-body { flex-direction: column; min-height: 0; padding: 62px 18px 16px; }
  .hero-avatar-wrap { left: 18px; top: -46px; width: 92px; height: 92px; }
  .hero-avatar { width: 92px; height: 92px; border-width: 4px; }
  .hero-avatar.initials { font-size: 32px; }
  .hero-avatar-wrap i { width: 28px; height: 28px; right: 0; bottom: 2px; }
  .hero-main { padding-top: 0; }
  .hero-name { font-size: 26px; }
  .hero-fee { display: none; }
  .hero-figs { grid-template-columns: 1fr 1fr; gap: 16px 10px; padding: 16px 18px 18px; }
  .hfig { gap: 10px; }
  .hfig-ico { width: 40px; height: 40px; }
  .profile-page .nm-panel { padding: 18px 16px; border-radius: 18px; }
  .profile-page .nm-panel-title { font-size: 19px; }
  .pn-ico { width: 40px; height: 40px; }
  .meet-art { display: none; }
  .meet-panel .nm-row-main { padding-right: 0; }
  .avail-grid { grid-template-columns: repeat(4, 1fr); }
  .m-bookbar {
    position: fixed;
    left: 12px;
    right: 12px;
    bottom: 84px;
    z-index: 25;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 10px 10px 16px;
    border-radius: 18px;
    background: #0B5640;
    color: #FFFFFF;
    box-shadow: 0 16px 30px -12px rgba(0, 0, 0, 0.45);
  }
  .m-bookbar strong { display: block; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; line-height: 1; }
  .m-bookbar span { font-size: 12px; color: rgba(255, 255, 255, 0.8); }
  .m-bookbar .hero-book { background: #FFFFFF; color: #0B5640; height: 44px; padding: 0 22px; }
}
@media (max-width: 520px) {
  .steps { grid-template-columns: 1fr; gap: 16px; }
  .steps li { flex-direction: row; align-items: flex-start; text-align: left; flex-wrap: wrap; column-gap: 14px; }
  .steps li::before { display: none; }
  .step-ico { width: 46px; height: 46px; margin: 0; }
  .steps li { display: grid; grid-template-columns: 46px 1fr; }
  .steps li .step-ico { grid-row: span 2; }
  .steps li .step-text { margin-top: 2px; }
}

/* ---------- BOOK APPOINTMENT MODAL ---------- */
.modal-overlay { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; padding: 24px; background: rgba(4, 30, 21, 0.55); -webkit-backdrop-filter: blur(6px); backdrop-filter: blur(6px); }
.booking-modal-box { position: relative; width: 100%; max-width: 980px; max-height: 94vh; max-height: 94dvh; display: flex; flex-direction: column; overflow: hidden; border-radius: 24px; background: #FFFFFF; box-shadow: 0 40px 90px -30px rgba(0, 0, 0, 0.6); font-family: 'DM Sans', Arial, sans-serif; animation: bk-in .28s cubic-bezier(.2, .7, .2, 1); }
@keyframes bk-in { from { opacity: 0; transform: translateY(14px) scale(.98); } to { opacity: 1; transform: none; } }

/* header: green band with the RND */
.bk-head { position: relative; display: flex; align-items: center; gap: 22px; padding: 20px 30px; color: #FFFFFF; background: #0B5640; }
.bk-avatar { flex-shrink: 0; width: 66px; height: 66px; border-radius: 50%; object-fit: cover; background: #E3EFE7; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; font-size: 21px; font-weight: 800; border: 3px solid #FFFFFF; box-shadow: 0 8px 18px -10px rgba(0, 0, 0, 0.5); }
.bk-head-text { flex: 1; min-width: 0; }
.booking-title { margin: 0 0 6px; font-family: 'Playfair Display', Georgia, serif; font-size: 26px; font-weight: 700; line-height: 1.2; color: #FFFFFF; }
.booking-sub { margin: 0; font-size: 14px; line-height: 1.5; color: rgba(255, 255, 255, 0.88); }
.bk-x { flex-shrink: 0; align-self: flex-start; width: 40px; height: 40px; border: none; border-radius: 50%; background: transparent; color: #FFFFFF; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: background-color .15s; }
.bk-x :deep(svg) { width: 24px; height: 24px; }
.bk-x:hover { background: rgba(255, 255, 255, 0.14); }
.bk-x:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }

/* body: calendar card on the left, the day's times on a light green side */
.bk-body { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; padding: 0; }
.bk-grid { display: grid; grid-template-columns: minmax(0, 1.08fr) minmax(0, 1fr); min-height: 100%; }
.bk-left { min-width: 0; padding: 20px 24px 24px 28px; background: #FFFFFF; }
.bk-right { min-width: 0; padding: 22px 28px 24px; background: #EEF5F0; border-left: 1px solid #E3ECE6; }
.bk-section { margin-bottom: 20px; }
.bk-section:last-child { margin-bottom: 0; }
.bk-k { margin: 0 0 8px; display: flex; align-items: center; gap: 12px; font-size: 17px; font-weight: 700; color: #0E3A2C; }
.bk-k .ic { color: #1F5C45; }
.section-h { display: flex; align-items: center; gap: 12px; margin: 0 0 12px; font-family: 'Playfair Display', Georgia, serif; font-size: 24px; font-weight: 700; color: #0E3A2C; }
.section-h .ic { color: #1F5C45; }
.section-h .optional { font-family: 'DM Sans', Arial, sans-serif; font-size: 13.5px; font-weight: 500; color: #6B7D73; }
.bk-notes-h { font-family: 'DM Sans', Arial, sans-serif; font-size: 16px; font-weight: 700; gap: 10px; }
.bk-notes-h .optional { margin-left: -4px; }

.bk-format { display: flex; align-items: center; justify-content: space-between; gap: 10px 16px; flex-wrap: wrap; margin-bottom: 16px; }
.seg { display: inline-flex; gap: 8px; flex-wrap: wrap; }
.seg-btn { display: inline-flex; align-items: center; gap: 12px; height: 46px; padding: 0 30px; border: 1.5px solid #D5E2D9; border-radius: 999px; background: #FFFFFF; color: #3E5046; font-family: inherit; font-size: 16px; font-weight: 600; cursor: pointer; transition: border-color .15s, color .15s, background-color .15s; }
.seg-btn :deep(svg) { width: 20px; height: 20px; }
.seg-btn:hover:not(.active) { border-color: #1F5C45; color: #0E3A2C; }
.seg-btn.active { border-color: #0B5640; color: #0E3A2C; background: #FFFFFF; box-shadow: 0 0 0 1px #0B5640; }
.seg-btn:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.bk-fee { margin: 0; display: inline-flex; align-items: center; gap: 8px; height: 46px; padding: 0 22px; border-radius: 999px; background: #E3F0E7; font-size: 15.5px; color: #3E5046; }
.bk-fee .ic { color: #1F5C45; margin-right: 4px; }
.bk-fee strong { font-size: 16px; font-weight: 700; color: #0E3A2C; }
.booking-address { margin: -4px 0 16px; padding: 10px 12px; border-radius: 12px; background: #F3F8F5; border: 1px solid #E3EAE5; }

/* the calendar: its own card */
.bk-calcard { padding: 20px 20px 18px; border-radius: 20px; background: #FFFFFF; border: 1px solid #E4EBE6; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05), 0 14px 30px -20px rgba(16, 35, 27, 0.3); }
.bk-row-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 10px; }
.bk-row-head .section-h { margin: 0; font-size: 22px; }
.strip-nav { display: flex; gap: 10px; }
.strip-nav button { width: 40px; height: 40px; border: 1.5px solid #DDE6E0; border-radius: 50%; background: #FFFFFF; color: #0E3A2C; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: border-color .15s, background-color .15s; }
.strip-nav button :deep(svg) { width: 18px; height: 18px; }
.strip-nav button:hover:not(:disabled) { border-color: #0B5640; background: #F1F6F2; }
.strip-nav button:disabled { opacity: .35; cursor: default; }
.strip-nav button:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.cal { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 8px 8px; }
.cal-wd { padding: 6px 0 6px; text-align: center; font-size: 13px; font-weight: 700; letter-spacing: .4px; text-transform: uppercase; color: #1F7A4D; }
.cal-cell { min-height: 56px; padding: 2px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; border: none; border-radius: 14px; background: transparent; color: #3E5046; font-family: inherit; transition: background-color .15s, transform .15s, box-shadow .15s; }
.cal-cell.out { border: none; }
.cal-num { font-size: 16px; font-weight: 500; line-height: 1; font-variant-numeric: lining-nums tabular-nums; }
.cal-note { font-size: 10.5px; font-weight: 600; white-space: nowrap; }
.cal-cell.today .cal-num { text-decoration: underline; text-decoration-color: #EFBF04; text-decoration-thickness: 2px; text-underline-offset: 4px; }
.cal-cell.open { background: #E3F0E7; color: #0E3A2C; cursor: pointer; }
.cal-cell.open .cal-num { font-size: 18px; font-weight: 700; }
.cal-cell.open .cal-note { color: #2E5B49; }
.cal-cell.open:hover:not(.selected) { background: #D4E8DB; transform: translateY(-1px); }
.cal-cell.selected { background: #0B5640; color: #FFFFFF; box-shadow: 0 10px 18px -10px rgba(0, 77, 58, 0.9); }
.cal-cell.selected .cal-note { color: rgba(255, 255, 255, 0.9); }
.cal-cell:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.cal-cell.off { background: repeating-linear-gradient(135deg, #F3F5F3, #F3F5F3 4px, #E8EBE8 4px, #E8EBE8 8px); color: #8A9A91; }
.cal-cell.full { background: #F3F5F3; color: #8A9A91; }
.cal-empty { margin: 10px 0 0; }
.cal-legend { margin: 16px 0 0; display: flex; flex-wrap: wrap; gap: 6px 22px; font-size: 13px; color: #3E5046; }
.cal-legend span { display: inline-flex; align-items: center; gap: 8px; }
.cal-legend i { width: 16px; height: 16px; border-radius: 50%; }
.lg-open { background: #EEF5F0; box-shadow: inset 0 0 0 1.5px #D5E2D9; }
.lg-sel { background: #0B5640; }
.lg-off { background: repeating-linear-gradient(135deg, #F3F5F3, #F3F5F3 2px, #C9D3CC 2px, #C9D3CC 4px); }

/* the day's times */
.bk-pickday { height: 100%; min-height: 220px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px; text-align: center; color: #3E5046; font-size: 14px; }
.bk-pickday p { margin: 0; max-width: 220px; }
.bk-pickday-ico { flex-shrink: 0; width: 56px; height: 56px; border-radius: 50%; background: #FFFFFF; color: #0B5640; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 10px 20px -14px rgba(0, 77, 58, 0.6); }
.bk-right .section-h { font-size: 26px; margin-bottom: 14px; }
.tg { padding: 4px 0 12px; }
.tg-label { display: block; margin-bottom: 10px; font-size: 16px; font-weight: 700; color: #0E3A2C; }
.tg-times { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.t-btn { height: 46px; padding: 0 8px; border: 1px solid #D5E2D9; border-radius: 14px; background: #FFFFFF; color: #10231B; font-family: inherit; font-size: 15px; font-weight: 500; cursor: pointer; font-variant-numeric: tabular-nums; box-shadow: 0 1px 2px rgba(16, 35, 27, 0.05); transition: border-color .15s, background-color .15s, color .15s; }
.t-btn:hover:not(.selected) { border-color: #0B5640; }
.t-btn.selected { background: #0B5640; border-color: #0B5640; color: #FFFFFF; font-weight: 600; box-shadow: 0 10px 18px -12px rgba(0, 77, 58, 0.9); }
.t-btn:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }
.t-booked,
.t-away { display: inline-flex; align-items: center; justify-content: center; height: 46px; padding: 0 8px; border-radius: 14px; background: #E2EAE5; color: #8A9A91; font-size: 12.5px; text-align: center; }
.t-away { grid-column: span 3; }
.t-booked { text-decoration: line-through; text-decoration-color: #B5BFB5; }
.bk-right .bk-section:last-child { margin-top: 14px; padding-top: 20px; border-top: 1px solid #D9E5DD; }
.bk-section textarea { width: 100%; min-height: 74px; padding: 14px 18px; border: 1px solid #D5E2D9; border-radius: 14px; background: #FFFFFF; font-family: inherit; font-size: 14px; color: #14261E; resize: vertical; }
.bk-section textarea::placeholder { color: #8A9A91; }
.bk-section textarea:focus { outline: none; border-color: #0B5640; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }

/* the footer: what's picked, and Send */
.bk-foot { display: flex; align-items: center; gap: 14px 22px; padding: 18px 24px; border-top: 1px solid #E3ECE6; background: #FFFFFF; }
.bk-sumbox { flex: 1; min-width: 0; display: flex; align-items: center; gap: 18px; padding: 12px 18px 12px 0; border-radius: 16px; background: linear-gradient(90deg, #EEF5F0 0, #EEF5F0 70px, rgba(238, 245, 240, 0) 70px); }
.bk-sum-ico { flex-shrink: 0; width: 70px; display: inline-flex; align-items: center; justify-content: center; color: #1F5C45; }
.bk-sum-ico .ic { width: 36px; height: 36px; padding: 6px; border-radius: 50%; border: 2px solid currentColor; }
.bk-sum-ico.ready { color: #0B5640; }
.bk-summary { flex: 1; min-width: 0; }
.bk-pick { margin: 0; font-size: 17px; font-weight: 700; color: #0E3A2C; }
.bk-pick.muted { font-weight: 600; color: #3E5046; }
.bk-after { margin: 4px 0 0; font-size: 12.5px; line-height: 1.5; color: #3E5046; }
.bk-foot .form-error { margin: 4px 0 0; font-size: 13px; font-weight: 600; color: #B42318; }
.profile-page .bk-send { flex-shrink: 0; gap: 12px; height: 56px !important; padding: 0 32px !important; border-radius: 16px !important; background: #0B5640; font-size: 15.5px; font-weight: 600; }
.profile-page .bk-send:hover:not(:disabled) { background: #136047; }
.profile-page .bk-send:disabled { background: #C9D6CE; color: #FFFFFF; opacity: 1; }

@media (max-width: 860px) {
  .bk-grid { grid-template-columns: 1fr; }
  .bk-right { border-left: none; border-top: 1px solid #E3ECE6; }
  .bk-pickday { min-height: 0; padding: 4px 0; flex-direction: row; justify-content: flex-start; text-align: left; }
  .bk-pickday-ico { width: 44px; height: 44px; }
}
@media (max-width: 640px) {
  .modal-overlay { padding: 0; align-items: stretch; }
  .booking-modal-box { max-width: none; max-height: none; height: 100%; border-radius: 0; animation: none; }
  .bk-head { gap: 12px; padding: 16px; padding-top: calc(16px + env(safe-area-inset-top)); }
  .bk-avatar { width: 48px; height: 48px; font-size: 16px; }
  .booking-title { font-size: 19px; }
  .booking-sub { font-size: 12.5px; }
  .bk-left,
  .bk-right { padding: 16px; }
  .bk-format { margin-bottom: 14px; gap: 8px; }
  .seg { width: 100%; }
  .seg-btn { flex: 1; justify-content: center; height: 44px; padding: 0 14px; font-size: 15px; }
  .bk-fee { width: 100%; justify-content: center; height: 42px; font-size: 14.5px; }
  .bk-calcard { padding: 14px 12px; border-radius: 18px; }
  .bk-row-head .section-h { font-size: 19px; gap: 8px; }
  .strip-nav button { width: 36px; height: 36px; }
  .cal { gap: 4px; }
  .cal-wd { font-size: 11px; }
  .cal-cell { min-height: 46px; border-radius: 12px; }
  .cal-num { font-size: 14px; }
  .cal-cell.open .cal-num { font-size: 15px; }
  .cal-note { font-size: 8.5px; }
  .bk-right .section-h { font-size: 21px; }
  .t-btn { height: 44px; font-size: 14px; }
  .bk-section textarea { font-size: 16px; } /* stops iPhone zoom on tap */
  .bk-foot { flex-wrap: wrap; gap: 10px 12px; padding: 12px 16px calc(12px + env(safe-area-inset-bottom)); box-shadow: 0 -10px 24px -16px rgba(0, 0, 0, 0.3); }
  .bk-sumbox { flex: 1 1 100%; padding: 10px 12px 10px 0; background: linear-gradient(90deg, #EEF5F0 0, #EEF5F0 52px, rgba(238, 245, 240, 0) 52px); gap: 12px; }
  .bk-sum-ico { width: 52px; }
  .bk-sum-ico .ic { width: 30px; height: 30px; padding: 5px; }
  .bk-pick { font-size: 15px; }
  .bk-after { display: none; }
  .profile-page .bk-send { width: 100%; height: 52px !important; }
}

@media (prefers-reduced-motion: reduce) {
  .sk { animation: none; }
}
</style>