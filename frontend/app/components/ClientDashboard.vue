<template>
  <!-- Client home — one page, real data only. The "next step" banner follows
       where the client is in their journey (screen → find an RND → booking
       → consultation → meal plan). Sections with nothing to show explain
       what fills them, instead of showing placeholder data. -->
  <div class="client-dashboard">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-else-if="isLoading" class="placeholder-text">Loading…</p>

    <template v-else>
      <!-- BANNER (same design as the RND dashboard, nm-hero in portal.css):
           greeting + the next step on the left; the next consultation, or the
           next step when there isn't one, in the "Up next" card on the right. -->
      <section class="cd-hero">
        <img class="cd-hero-plate" src="/landing/login-plate.webp" alt="" aria-hidden="true" />
        <span class="cd-hero-fade" aria-hidden="true"></span>
        <div class="nm-hero-greet">
          <p class="nm-hero-date">{{ longToday }}</p>
          <h1 class="nm-hero-title">Hi {{ auth.user?.first_name }}<template v-if="auth.user?.welcome_seen_at">, welcome <em>back.</em></template><template v-else>.</template></h1>
          <p class="nm-hero-sub">{{ nextStep.text }}</p>
        </div>
        <!-- UP NEXT: the time is the one big thing; the RND under a thin line;
             the status is a dot and a word. A button shows only when there's
             something to do right here (join, view a waiting booking). -->
        <div class="nm-upnext up" :class="{ 'ub-card': upNext }">
          <template v-if="upNext">
            <div class="ub">
              <div class="ub-db">
                <small>{{ ubMonth(upNext.startsAt) }}</small>
                <b>{{ ubDay(upNext.startsAt) }}</b>
                <span>{{ ['Today', 'Tomorrow'].includes(upNext.day) ? upNext.day : ubWeek(upNext.startsAt) }}</span>
              </div>
              <div class="ub-m">
                <p class="ub-k">Up next · <b>{{ upNext.time }}</b></p>
                <div class="ub-who">
                  <img v-if="upNext.photo" :src="upNext.photo" alt="" class="ub-av" />
                  <span v-else class="ub-av ub-ini">{{ upNext.initials }}</span>
                  <div class="ub-name">
                    <strong>RND {{ upNext.name }}</strong>
                    <small><Video :size="13" aria-hidden="true" /> {{ upNext.format }}</small>
                  </div>
                  <span class="ub-pill" :class="upNext.state"><template v-if="upNext.state === 'paid'"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></template>{{ upNext.pill }}</span>
                </div>
                <div class="ub-acts">
                  <span v-if="whenLine" class="ub-btn soft"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg>{{ whenLine }}</span>
                  <NuxtLink v-if="nextStep.action" :to="nextStep.to" class="ub-btn" :class="/Join/.test(nextStep.action) ? 'gold' : 'dark'">
                    <Video v-if="/Join/.test(nextStep.action)" :size="15" aria-hidden="true" />{{ nextStep.action }}<template v-if="!/Join/.test(nextStep.action)"><svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></template>
                  </NuxtLink>
                </div>
              </div>
            </div>
          </template>
          <!-- nothing booked: headline on the left, the one button top right -->
          <template v-else>
            <div class="up-empty">
              <div class="up-empty-text">
                <span class="nm-upnext-label">{{ nextStep.eyebrow }}</span>
                <p class="up-time small">{{ emptyCard.headline }}</p>
                <p class="up-when">{{ emptyCard.sub }}</p>
              </div>
              <NuxtLink :to="nextStep.to" class="nm-hero-btn primary up-empty-btn">{{ nextStep.action }}<svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
            </div>
          </template>
        </div>
      </section>

      <!-- NEEDS ATTENTION: the shared strip (same on the RND and admin dashboards);
           its pop-up lists everything waiting on the client. Red = it goes wrong soon
           if left (payment due within a day, labs for a consultation within 2 days);
           dashed green = still to do. -->
      <NeedsAttention class="needs-strip" :groups="needGroups" clear-text="All caught up. Nothing is waiting on you." />

      <!-- PHONE: quick access to the main pages -->
      <section class="qa" aria-label="Quick access">
        <h2 class="m-title">Quick access</h2>
        <div class="qa-grid">
          <NuxtLink to="/appointments" class="qa-tile "><span class="qa-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span><span>Appointments</span></NuxtLink>
          <NuxtLink to="/meal-plan-view" class="qa-tile gold"><span class="qa-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4" /></svg></span><span>My Meal Plan</span></NuxtLink>
          <NuxtLink to="/progress-tracker" class="qa-tile "><span class="qa-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 17l6-6 4 4 8-8" /><path d="M15 7h6v6" /></svg></span><span>Progress</span></NuxtLink>
          <NuxtLink to="/lab-results" class="qa-tile gold"><span class="qa-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3" /></svg></span><span>Lab Results</span></NuxtLink>
          <NuxtLink to="/find-rnd" class="qa-tile dark"><span class="qa-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.3-4.3" /></svg></span><span>Find an RND</span></NuxtLink>
          <button v-if="screening" type="button" class="qa-tile" @click="screeningOpen = true"><span class="qa-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4h6v3H9zM9 11h6M9 15h4" /></svg></span><span>Screening</span></button>
          <NuxtLink v-else to="/pre-consultation-screening" class="qa-tile"><span class="qa-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4h6v3H9zM9 11h6M9 15h4" /></svg></span><span>Screening</span></NuxtLink>
          <NuxtLink to="/resource-library" class="qa-tile gold"><span class="qa-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" /><path d="M14 3v5h5M9 13h6M9 17h4" /></svg></span><span>Resources</span></NuxtLink>
          <NuxtLink to="/invoices-billing" class="qa-tile "><span class="qa-icon"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="M3 10h18M7 15h3" /></svg></span><span>Billing</span></NuxtLink>
        </div>
      </section>

      <div class="m-head">
        <h2 class="m-title">Your numbers</h2>
        <NuxtLink to="/progress-tracker" class="m-more">Details<svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6l6 6-6 6" /></svg></NuxtLink>
      </div>
      <!-- HEALTH SNAPSHOT -->
      <section class="stat-grid" aria-label="Your health at a glance">
        <div class="stat-card">
          <div class="stat-top">
            <span class="stat-icon" aria-hidden="true"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v18M5 7h14M7 7l-3 7a3 3 0 0 0 6 0zM17 7l-3 7a3 3 0 0 0 6 0z" /></svg></span>
            <span class="stat-pill" :class="currentBmi ? bmiTone : 'neutral'">{{ currentBmi?.label ?? 'Not yet screened' }}</span>
          </div>
          <div>
            <p class="stat-value">{{ currentBmi ? currentBmi.value.toFixed(1) : '—' }}</p>
            <p class="stat-label">BMI</p>
          </div>
          <!-- where the BMI sits: under 18.5 / normal / overweight / obese -->
          <div v-if="currentBmi" class="bmi-gauge" aria-hidden="true">
            <span class="bmi-pin" :style="{ left: `${Math.min(97, Math.max(3, ((currentBmi.value - 14) / (36 - 14)) * 100))}%` }"></span>
          </div>
          <p v-else class="stat-delta neutral">Not yet screened</p>
        </div>
        <div class="stat-card">
          <div class="stat-top">
            <span class="stat-icon gold" aria-hidden="true"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3c3 4 6 6.5 6 10a6 6 0 0 1-12 0c0-2 1-3.5 2-4.5 0 2 1 3 2 3 0-3 1-5.5 2-8.5z" /></svg></span>
            <span v-if="calorieTarget.value" class="stat-pill neutral">{{ calorieTarget.label.startsWith('Estimated') ? 'Estimate' : 'Target' }}</span>
          </div>
          <div>
            <p class="stat-value">
              {{ calorieTarget.value ? calorieTarget.value.toLocaleString() : '—' }}
              <span v-if="calorieTarget.value" class="unit">kcal</span>
            </p>
            <p class="stat-label">{{ calorieTarget.label }}</p>
          </div>
          <p class="stat-delta neutral">{{ calorieTarget.note }}</p>
        </div>
        <div class="stat-card">
          <div class="stat-top">
            <span class="stat-icon" aria-hidden="true"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v5c0 4.6-3 8.4-7 10-4-1.6-7-5.4-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></svg></span>
            <span class="stat-pill" :class="screening ? nrsTone : 'neutral'">{{ screening ? nrsRiskLabel : 'Pending screening' }}</span>
          </div>
          <div>
            <p class="stat-value">{{ screening?.nrs_score ?? '—' }}</p>
            <p class="stat-label">NRS-2002 score</p>
          </div>
          <p class="stat-delta neutral">Nutrition risk from your screening.</p>
        </div>
        <div class="stat-card">
          <div class="stat-top">
            <span class="stat-icon" aria-hidden="true"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></svg></span>
            <span class="stat-pill" :class="nextAppointment ? (nextAppointment.status === 'pending' ? 'warn' : 'good') : 'warn'">{{ nextAppointment ? (nextAppointment.status === 'pending' ? 'Waiting' : 'Booked') : 'Not booked' }}</span>
          </div>
          <div>
            <p class="stat-value" :class="{ muted: !nextAppointment }">{{ nextAppointment ? formatShortDate(nextAppointment.scheduled_at) : '—' }}</p>
            <p class="stat-label">Next consultation</p>
          </div>
          <p v-if="nextAppointment" class="stat-delta" :class="nextAppointment.status === 'pending' ? 'warn' : 'neutral'">
            {{ formatTime(nextAppointment.scheduled_at) }}, {{ (APPT_TYPES[nextAppointment.type] || nextAppointment.type).toLowerCase() }}{{ nextAppointment.status === 'pending' ? ', waiting for your RND to confirm' : '' }}
          </p>
          <NuxtLink v-else :to="careRnd ? `/rnd-profile-view/${careRnd.id}?book=1` : '/find-rnd'" class="cd-link">{{ careRnd ? 'Book a consultation' : 'Book your first one' }}<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
        </div>
      </section>

      <section class="dash-grid">
        <div class="dash-col">
          <!-- TODAY'S MEAL PLAN -->
          <div class="panel">
            <div class="panel-header-row">
              <div>
                <p v-if="activePlan" class="mt-k">Today · {{ weekdayLabel }}</p>
                <h3 class="panel-title flush">Today's meal plan</h3>
                <p v-if="activePlan" class="panel-sub">{{ activePlan.name || 'Your meal plan' }}. Snap a photo of each meal so your RND can rate it.</p>
              </div>
              <NuxtLink v-if="activePlan" to="/meal-plan-view" class="mt-log"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" /><circle cx="12" cy="13.5" r="3.5" /></svg>Log a meal</NuxtLink>
              <NuxtLink v-else to="/meal-plan-view" class="cd-link">Open meal plan<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
            </div>

            <template v-if="activePlan">
              <div v-if="planMacros" class="macro-strip">
                <span><strong>{{ planMacros.kcal }}</strong> kcal</span>
                <span v-if="planMacros.carbs"><strong>{{ planMacros.carbs }}g</strong> carbs</span>
                <span v-if="planMacros.protein"><strong>{{ planMacros.protein }}g</strong> protein</span>
                <span v-if="planMacros.fat"><strong>{{ planMacros.fat }}g</strong> fat</span>
                <span class="macro-source">daily targets from your RND</span>
              </div>

              <template v-if="todaysMeals.length">
                <div class="mt-lh">
                  <p><b>{{ mtShowAll ? 'All meals' : 'Up next' }}</b> · {{ mtShowAll ? `${todaysMeals.length} meals today` : `showing ${mtVisible.length} of ${todaysMeals.length} meals` }}</p>
                  <button v-if="todaysMeals.length > MT_FIRST" type="button" class="mt-all" :aria-expanded="mtShowAll" @click="mtShowAll = !mtShowAll">{{ mtShowAll ? 'Show less' : `See all ${todaysMeals.length}` }}<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></button>
                </div>
                <ul class="meal-list mt-tl">
                  <li v-for="meal in mtVisible" :key="meal.id" class="mt-row" :class="mtState(meal)">
                    <div class="mt-ic"><component :is="MEAL_ICONS[meal.meal_time] || Sun" :size="17" /></div>
                    <div class="mt-m">
                      <p class="mt-t">
                        <span v-if="meal.scheduled_time">{{ formatClock(meal.scheduled_time) }}</span>
                        <span v-if="mtState(meal) === 'logged'" class="mt-st" :class="logPillClass(meal)"><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>{{ logLabel(meal) }}</span>
                        <span v-else-if="mtState(meal) === 'now'" class="mt-st now">● Log it now</span>
                        <span v-else class="mt-st later">Later today</span>
                      </p>
                      <p class="mt-n">{{ MEAL_LABELS[meal.meal_time] || meal.meal_time }}</p>
                      <div class="mt-f">
                        <span v-for="f in mtFoods(meal)" :key="f">{{ f }}</span>
                        <span v-if="!mtFoods(meal).length" class="none">No foods listed</span>
                      </div>
                    </div>
                    <div v-if="mtState(meal) === 'logged'" class="mt-ph done">
                      <img v-if="todaysLogsByMeal[meal.id]?.photo_url" :src="todaysLogsByMeal[meal.id].photo_url" alt="" />
                      <span v-else class="mt-nophoto"><svg class="ic" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" /><circle cx="12" cy="13.5" r="3.5" /></svg></span>
                      <i><svg class="ic" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></i>
                    </div>
                    <NuxtLink v-else to="/meal-plan-view" class="mt-ph add" :class="{ now: mtState(meal) === 'now' }" :aria-label="`Add a photo of your ${(MEAL_LABELS[meal.meal_time] || 'meal').toLowerCase()}`"><svg class="ic" width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" /><circle cx="12" cy="13.5" r="3.5" /></svg><b>Add photo</b></NuxtLink>
                  </li>
                </ul>
              </template>
              <p v-if="!todaysMeals.length" class="empty-note">No meals are scheduled for today in your plan.</p>

              <div class="adherence-row">
                <div class="adherence-item">
                  <p class="adherence-label mt-pg"><b>{{ todayLoggedCount }} of {{ todaysMeals.length }}</b> meals logged today</p>
                  <div class="mt-bar" aria-hidden="true"><i :style="{ width: `${todaysMeals.length ? Math.round((todayLoggedCount / todaysMeals.length) * 100) : 0}%` }" /></div>
                </div>
                <div class="adherence-item">
                  <p class="adherence-value">{{ weekAdherence.logged ? `${weekAdherence.followedPct}%` : '—' }}</p>
                  <p class="adherence-label">
                    {{ weekAdherence.logged ? `followed in the last 7 days (${weekAdherence.followed} followed${weekAdherence.partly ? `, ${weekAdherence.partly} partly` : ''}, of ${weekAdherence.logged} meals your RND rated; partly counts as half)` : 'no rated meals in the last 7 days' }}
                  </p>
                </div>
              </div>
            </template>
            <div v-else class="empty-plate">
              <div class="plate-ring" aria-hidden="true"><span><UtensilsCrossed :size="26" /></span></div>
              <div class="empty-plate-text">
                <p class="empty-plate-title">{{ pastRnd ? 'Your meal plan ended with your care.' : 'No meal plan yet.' }}</p>
                <p class="empty-sub">{{ pastRnd ? 'When you start care with an RND again, your new plan shows up here.' : 'Your RND prepares your meal plan after your consultation. It will show up here, meal by meal.' }}</p>
                <div class="plate-chips"><span class="c-veg">½ Vegetables</span><span class="c-grain">¼ Whole grains</span><span class="c-prot">¼ Protein</span></div>
              </div>
            </div>
          </div>

          <!-- WEIGHT PROGRESS -->
          <div class="panel">
            <div class="panel-header-row">
              <h3 class="panel-title flush">Weight progress <span class="title-unit">(kg)</span></h3>
              <div class="range-toggle" role="group" aria-label="Time range">
                <button v-for="d in [30, 90]" :key="d" type="button" :class="{ on: weightDays === d }" :aria-pressed="weightDays === d" @click="weightDays = d">{{ d }} days</button>
              </div>
            </div>
            <template v-if="rangeChart">
              <div class="weight-now">
                <span class="weight-now-value">{{ rangePoints[rangePoints.length - 1].weight }}</span>
                <span class="weight-now-unit">kg now</span>
                <span class="stat-pill neutral">{{ rangeDelta }}</span>
              </div>
              <svg class="weight-svg" viewBox="0 0 600 205" width="100%" role="img" :aria-label="`Weight over the last ${weightDays} days, latest ${rangePoints[rangePoints.length - 1].weight} kg`">
                <defs><linearGradient id="wGrad2" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#004D3A" stop-opacity=".14" /><stop offset="100%" stop-color="#004D3A" stop-opacity="0" /></linearGradient></defs>
                <g v-for="g in rangeChart.grid" :key="g.y">
                  <line x1="40" :y1="g.y" x2="600" :y2="g.y" stroke="#EEF2EF" stroke-width="1" />
                  <text x="0" :y="g.y + 4" font-size="11" fill="#9AA9A1" font-family="DM Sans, Arial, sans-serif">{{ g.label }}</text>
                </g>
                <path v-if="rangeChart.single" :d="`M${rangeChart.points[0].x} ${rangeChart.points[0].y} L580 ${rangeChart.points[0].y}`" stroke="#C9D6CE" stroke-width="2" stroke-dasharray="6 6" fill="none" />
                <template v-else>
                  <polygon :points="rangeChart.fill" fill="url(#wGrad2)" />
                  <polyline :points="rangeChart.line" stroke="#004D3A" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round" />
                </template>
                <g v-for="(p, i) in rangeChart.points" :key="i">
                  <circle v-if="i === rangeChart.points.length - 1" :cx="p.x" :cy="p.y" r="9" fill="rgba(239,191,4,.25)" />
                  <circle :cx="p.x" :cy="p.y" :r="i === rangeChart.points.length - 1 ? 5 : 4" :fill="i === rangeChart.points.length - 1 ? '#EFBF04' : '#004D3A'" :stroke="i === rangeChart.points.length - 1 ? '#004D3A' : '#FFFFFF'" stroke-width="2" />
                  <text v-if="rangeChart.points.length > 1" :x="p.x" y="198" text-anchor="middle" font-size="11" :fill="i === rangeChart.points.length - 1 ? '#C49102' : '#9AA9A1'" :font-weight="i === rangeChart.points.length - 1 ? 700 : 400" font-family="DM Sans, Arial, sans-serif">{{ p.label }}</text>
                </g>
              </svg>
            </template>
            <p v-else class="empty-note">No weight history yet. It starts from your screening and fills in after each consultation.</p>
            <div class="weight-foot">
              <span>Log your weight each week to see your progress line.</span>
              <NuxtLink to="/progress-tracker" class="nm-btn-soft nm-btn-sm"><Plus :size="14" aria-hidden="true" /> Log weight</NuxtLink>
            </div>
          </div>

          <!-- LATEST SCREENING -->
          <div class="panel scr-card sx">
            <div class="sx-h">
              <div>
                <p class="sx-k"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="4" width="12" height="17" rx="2" /><path d="M9 4V3h6v1M9 10h6M9 14h6M9 18h4" /></svg>Pre-consultation</p>
                <h3 class="panel-title flush">Your screening</h3>
                <p class="panel-sub">{{ screening ? `Recorded ${formatLongDate(screening.created_at)}` : 'Not done yet' }}</p>
              </div>
              <span v-if="screening" class="stat-pill good"><Check :size="13" aria-hidden="true" /> Done</span>
              <span v-else class="stat-pill warn">To do</span>
            </div>
            <template v-if="screening">
              <div class="sx-figs">
                <div class="sx-f"><span class="sx-i"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 20 20 4M7 17l2 2M10 14l2 2M13 11l2 2M16 8l2 2" /></svg></span><div><small>Height</small><b>{{ Number(screening.height_cm) }}<em> cm</em></b></div></div>
                <div class="sx-f"><span class="sx-i"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 21h14a1 1 0 0 0 1-1l-1.5-13a1 1 0 0 0-1-1h-11a1 1 0 0 0-1 1L4 20a1 1 0 0 0 1 1z" /><path d="M12 6V3M9.5 12a2.5 2.5 0 0 1 5 0M12 12l1.5-2" /></svg></span><div><small>Weight</small><b>{{ Number(screening.weight_kg) }}<em> kg</em></b></div></div>
                <div class="sx-f"><span class="sx-i"><svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="4.5" r="2" /><path d="M8 9h8M12 9v12M9 21l3-6 3 6" /></svg></span><div><small>BMI</small><b>{{ screening.bmi != null ? Number(screening.bmi).toFixed(1) : '—' }}<span v-if="screening.bmi != null" class="sx-pill">{{ bmiClass(Number(screening.bmi)) }}</span></b></div></div>
              </div>
              <div class="sx-foot">
                <p>Your RND uses this to plan your care.</p>
                <button type="button" class="sx-btn" @click="screeningOpen = true">View screening<svg class="ic" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></button>
              </div>
            </template>
            <template v-else>
              <p class="screening-summary-text">Your RND needs this before your first consultation. It takes about a minute.</p>
              <NuxtLink to="/pre-consultation-screening" class="nm-btn-dark block-wide">Complete screening</NuxtLink>
            </template>
          </div>
        </div>


        <div class="dash-col">
          <!-- YOUR RND (compact, top of the column) -->
          <div class="panel rnd-compact" :class="{ empty: !careRnd }">
            <template v-if="careRnd">
              <div class="yr-av">
                <img v-if="careRnd.photo" :src="careRnd.photo" alt="" />
                <span v-else>{{ careRnd.initials }}</span>
                <i v-if="!careRnd.pending"><svg class="ic" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg></i>
              </div>
              <div class="rnd-text yr-m">
                <p class="yr-k"><svg class="ic" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 19c0-8 6-14 14-14 0 8-6 14-14 14zM5 19l8-8" /></svg>Your RND</p>
                <p class="yr-name">{{ careRnd.name }}, RND</p>
                <p class="yr-s">
                  <span class="yr-spec">{{ careRnd.specialization || 'Registered Nutritionist-Dietitian' }}</span>
                  <span v-if="careRnd.reviewCount" class="yr-rate"><svg width="14" height="14" viewBox="0 0 24 24" fill="#EFBF04" aria-hidden="true"><path d="M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z" /></svg><b>{{ careRnd.rating }}</b> · {{ careRnd.reviewCount }} review{{ careRnd.reviewCount === 1 ? '' : 's' }}</span>
                </p>
                <p v-if="careRnd.pending" class="rnd-pending">Waiting to confirm your first booking</p>
              </div>
              <div class="yr-a">
                <NuxtLink v-if="!careRnd.pending" to="/messages" class="yr-btn dark"><MessageSquare :size="15" aria-hidden="true" />Message</NuxtLink>
                <NuxtLink :to="`/rnd-profile-view/${careRnd.id}`" class="yr-btn soft"><UserRound :size="15" aria-hidden="true" />Profile</NuxtLink>
              </div>
            </template>
            <template v-else>
              <div class="rnd-empty">
                <p class="rnd-eyebrow">Your RND</p>
                <div class="rnd-empty-row">
                  <span class="rnd-avatar dashed" aria-hidden="true"><UserRound :size="22" /></span>
                  <div class="rnd-text">
                    <p class="rnd-name">{{ pastRnd ? 'Care ended' : 'Not connected yet' }}</p>
                    <p class="rnd-specialty">{{ pastRnd ? `Your care with RND ${pastRndName} has ended.` : 'You\'re not connected with an RND yet.' }}</p>
                  </div>
                </div>
                <NuxtLink to="/find-rnd" class="nm-btn-dark block-wide">Find an RND</NuxtLink>
              </div>
            </template>
          </div>

          <!-- MY TASKS (today) — tasks from the RND or the client are checkboxes;
               meals tick themselves once logged; consultations link out. -->
          <div class="panel">
            <div class="panel-header-row">
              <div>
                <div class="tk-head">
                  <div v-if="taskCount" class="tk-ring" :style="{ '--p': Math.round((doneCount / taskCount) * 100) }" aria-hidden="true"><b>{{ doneCount }}<small>/{{ taskCount }}</small></b></div>
                  <div>
                    <p class="tk-k"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01" /></svg>Today</p>
                    <h3 class="panel-title flush">My tasks</h3>
                    <p v-if="taskCount" class="panel-sub">{{ doneCount }} of {{ taskCount }} done<template v-if="tkNext"> · next: {{ tkNext.title.toLowerCase() }}<template v-if="tkNext.at && tkNext.kind !== 'lab'"> at {{ phClock(tkNext.at) }}</template></template></p>
                  </div>
                </div>
              </div>
              <button type="button" class="tk-add" @click="addOpen = !addOpen"><Plus :size="15" aria-hidden="true" /> Add a task</button>
            </div>

            <form v-if="addOpen" class="add-task" @submit.prevent="addTask">
              <input v-model="newTask.title" class="nm-input" maxlength="120" autocomplete="off" placeholder="e.g. Walk for 20 minutes" aria-label="Task" />
              <div class="add-task-row">
                <input v-model="newTask.time" type="time" class="nm-input" aria-label="Time" />
                <select v-model="newTask.repeat" class="nm-select" aria-label="Repeat">
                  <option value="once">Today only</option>
                  <option value="daily">Every day</option>
                  <option value="weekdays">Weekdays</option>
                </select>
                <button type="submit" class="nm-btn-dark nm-btn-sm" :disabled="adding || newTask.title.trim().length < 3">{{ adding ? 'Adding…' : 'Add' }}</button>
              </div>
              <p v-if="addError" class="add-error">{{ addError }}</p>
            </form>

            <div v-if="todayItems.length > TK_FIRST" class="tk-lh">
              <p><b>{{ tkShowAll ? 'All tasks' : 'Up next' }}</b> · {{ tkShowAll ? `${todayItems.length} today` : `showing ${tkVisible.length} of ${todayItems.length}` }}</p>
              <button type="button" class="tk-all" :aria-expanded="tkShowAll" @click="tkShowAll = !tkShowAll">{{ tkShowAll ? 'Show less' : `See all ${todayItems.length}` }}<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></button>
            </div>
            <div class="tk-list">
            <template v-for="(item, i) in tkVisible" :key="item.id ? `${item.kind}${item.id}` : i">
              <label v-if="item.kind === 'task'" class="today-row task tk-row" :class="{ done: item.done }">
                <span class="tk-time">{{ phClock(item.at) }}</span>
                <input type="checkbox" class="task-check tk-cb" :checked="item.done" :disabled="taskBusy === item.id" @change="toggleTask(item, $event.target.checked)" />
                <span class="today-main tk-m">
                  <span class="today-title">{{ item.title }}</span>
                  <span class="tk-s"><span class="tk-kd" :class="item.own ? 'own' : 'rem'">{{ item.own ? 'Your task' : 'Reminder' }}</span><span v-if="item.detail" class="today-detail">{{ item.detail }}</span></span>
                  <span v-if="item.note" class="today-note tk-note">“{{ item.note }}”</span>
                </span>
                <button v-if="item.own" type="button" class="task-x" aria-label="Delete task" :disabled="taskBusy === item.id" @click.prevent="removeTask(item)"><X :size="13" /></button>
              </label>
              <NuxtLink v-else :to="item.link" class="today-row tk-row" :class="[{ done: item.done }, 'k-' + item.kind]">
                <span class="tk-time">{{ item.kind !== 'lab' ? phClock(item.at) : 'Today' }}</span>
                <span v-if="item.kind === 'meal' || item.kind === 'lab'" class="task-check meal tk-cb" :class="{ on: item.done }" aria-hidden="true"><Check v-if="item.done" :size="13" /></span>
                <span v-else class="today-icon tk-cb tk-ico" :class="'k-' + item.kind"><component :is="TODAY_ICONS[item.kind]" :size="15" /></span>
                <span class="today-main tk-m">
                  <span class="today-title">{{ item.title }}</span>
                  <span class="tk-s"><span class="tk-kd" :class="item.kind">{{ TK_KIND[item.kind] || item.kind }}</span><span v-if="item.detail" class="today-detail">{{ item.detail }}</span></span>
                </span>
              </NuxtLink>
            </template>
            </div>
            <div v-if="todayLoaded && !todayItems.length" class="tasks-empty">
              <span class="tasks-empty-icon" aria-hidden="true"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 11l3 3 8-8" /><path d="M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9" /></svg></span>
              <p class="tasks-empty-title">No tasks for today</p>
              <p class="empty-note">Tasks from your RND, meals to log and your own tasks show up here.</p>
            </div>
          </div>

          <!-- RECENT ACTIVITY (real notifications) -->
          <div class="panel">
            <div class="panel-header-row">
              <div>
                <p class="ra-k"><svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12h4l3-8 4 16 3-8h4" /></svg>Activity</p>
                <h3 class="panel-title flush">Recent activity</h3>
              </div>
              <NuxtLink v-if="notifications.length" to="/notifications" class="ra-all">View all<svg class="ic" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" /></svg></NuxtLink>
            </div>
            <template v-for="g in raDays" :key="g.label">
              <p class="ra-day">{{ g.label }}<span v-if="g.unread">{{ g.unread }} new</span></p>
              <div class="ra-list">
                <NuxtLink v-for="r in g.rows" :key="r.id" to="/notifications" class="ra-row">
                  <span class="ra-ic" :class="raKind(r.subject).tone"><svg class="ic" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" v-html="raKind(r.subject).svg" /></span>
                  <span class="ra-m">
                    <span class="ra-t">{{ r.subject }}<span v-if="r.count > 1" class="ra-cnt">×{{ r.count }}</span></span>
                    <span v-if="r.detail" class="ra-s">{{ r.detail }}</span>
                    <span class="ra-g">{{ timeAgo(r.created_at) }}</span>
                  </span>
                  <i v-if="r.unread" class="ra-dot" aria-label="Unread" />
                  <span class="ra-go"><svg class="ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m9 6 6 6-6 6" /></svg></span>
                </NuxtLink>
              </div>
            </template>
            <div v-if="!recentActivity.length" class="tasks-empty">
              <span class="tasks-empty-icon gold" aria-hidden="true"><svg class="ic" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg></span>
              <p class="tasks-empty-title">Nothing yet</p>
              <p class="empty-note">Updates about your bookings, meal plans and payments show up here.</p>
            </div>
          </div>

          

          <!-- UPLOAD LAB RESULTS (only once the client has an RND) -->
          <LabResultsCard @uploaded="loadToday" />
        </div>
      </section>

    </template>

    <ScreeningModal v-if="screeningOpen" @close="screeningOpen = false" />
  </div>
</template>

<script setup>
import { useToast } from '~/composables/useToast'
import { phIso } from '~/utils/phTime'
import { bmiClass } from '~/utils/ncp'
import { computed, onMounted, reactive, ref } from 'vue'
import {
  UtensilsCrossed, Sunrise, Sun, Moon, Coffee, AlarmClock, CalendarCheck, Check, Plus, X, MessageSquare, UserRound, Video,
} from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Dashboard' })

const auth = useAuthStore()
const { get, post, del } = useApi()

const isLoading = ref(true)
const screeningOpen = ref(false) // View Screening pop-up
const errorMessage = ref('')
const appointments = ref([])
const relationships = ref([])
const rndProfile = ref(null)
const screening = ref(null)
const mealPlans = ref([])
const mealLogs = ref([])
const invoices = ref([])
const notifications = ref([])
const labs = ref(null) // GET /client/labs/: open requests from the RND

const APPT_TYPES = { video: 'Video', chat: 'Chat', in_person: 'In person' }
const MEAL_ORDER = ['breakfast', 'am_snack', 'lunch', 'pm_snack', 'dinner', 'bedtime_snack']
const MEAL_LABELS = { breakfast: 'Breakfast', am_snack: 'Morning snack', lunch: 'Lunch', pm_snack: 'Afternoon snack', dinner: 'Dinner', bedtime_snack: 'Bedtime snack' }
const MEAL_ICONS = { breakfast: Sunrise, am_snack: Coffee, lunch: Sun, pm_snack: Coffee, dinner: Moon, bedtime_snack: Moon }
const LOG_LABELS = { followed: 'Followed', partially_followed: 'Partly followed', not_followed: 'Not followed' }

// Philippine dates on the server's clock.
const now = new Date()
const localIso = phIso
const todayIso = localIso(now)
const weekdayLabel = now.toLocaleDateString('en-US', { weekday: 'long' })

function formatShortDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
function formatLongDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
}
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
}
function formatClock(t) {
  const [h, m] = t.split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}
function timeAgo(iso) {
  const mins = Math.round((Date.now() - new Date(iso)) / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs} hr${hrs === 1 ? '' : 's'} ago`
  const days = Math.round(hrs / 24)
  if (days < 7) return `${days} day${days === 1 ? '' : 's'} ago`
  return formatLongDate(iso)
}

/* ---------- Appointments & RND ---------- */
const activeRelationship = computed(() => relationships.value[0] || null)

// Upcoming = not cancelled/completed and not over yet (an in-progress call still counts).
const nextAppointment = computed(() => {
  const upcoming = appointments.value
    .filter(a => ['pending', 'confirmed'].includes(a.status))
    .filter(a => new Date(a.scheduled_at).getTime() + (a.duration_minutes || 60) * 60000 > Date.now())
    .sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at))
  return upcoming[0] || null
})

// Most recent still-"pending" request whose time has already passed.
const expiredRequest = computed(() =>
  appointments.value
    .filter(a => a.status === 'pending' && new Date(a.scheduled_at) <= new Date())
    .sort((a, b) => new Date(b.scheduled_at) - new Date(a.scheduled_at))[0] || null
)

// The RND to show: the active care relationship, or the RND of a first
// booking that hasn't been confirmed yet.
const careRnd = computed(() => {
  const rnd = activeRelationship.value?.rnd || nextAppointment.value?.relationship?.rnd
  if (!rnd) return null
  const profile = rndProfile.value
  return {
    id: rnd.id,
    name: `${rnd.first_name} ${rnd.last_name}`,
    initials: `${rnd.first_name?.[0] || ''}${rnd.last_name?.[0] || ''}`.toUpperCase(),
    photo: profile?.user?.profile_photo || '',
    specialization: profile?.specialization || '',
    rating: profile?.average_rating ? Number(profile.average_rating).toFixed(1) : '',
    reviewCount: profile?.review_count || 0,
    pending: !activeRelationship.value,
  }
})

/* ---------- Billing ---------- */
const unpaidInvoices = computed(() => invoices.value.filter(i => i.status === 'unpaid'))

/* ---------- Needs you ---------- */
const HOUR = 3600000
const peso = v => `₱${Number(v).toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
function whenShort(iso) {
  const d = new Date(iso)
  const day = d.toDateString() === new Date().toDateString() ? 'today'
    : d.toDateString() === new Date(Date.now() + 24 * HOUR).toDateString() ? 'tomorrow'
      : d.toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'short', month: 'short', day: 'numeric' })
  return `${day} at ${formatTime(iso)}`
}
const openLabRequests = computed(() => (labs.value?.requests || []).filter(r => r.status === 'open'))
function labsLeft(r) {
  const done = new Set(r.uploaded_tests || [])
  const names = r.test_names || []
  return (r.tests || []).length ? names.filter((_, i) => !done.has(r.tests[i])) : names
}
// The pop-up (NeedsAttention.vue, same design as the admin and RND dashboards):
// one "Your to-do" list; what goes wrong soon if left turns the strip red.
const needGroups = computed(() => [{
  title: 'Your to-do',
  items: [
    ...needsUrgent.value.map(n => ({ key: n.key, title: n.title, detail: n.detail, to: n.to, action: n.action, tone: 'todo', critical: true })),
    ...needsTodo.value.map(n => ({ key: n.key, title: n.title, detail: n.detail, to: n.to, action: n.action, tone: 'todo' })),
  ],
}])
const needsUrgent = computed(() => {
  const out = []
  for (const inv of unpaidInvoices.value) {
    if (!inv.pay_by || new Date(inv.pay_by) - Date.now() > 24 * HOUR) continue
    out.push({
      key: `pay${inv.id}`, title: `Pay ${peso(inv.amount)} by ${whenShort(inv.pay_by)}.`,
      detail: "If it's still unpaid then, your consultation is cancelled.", action: 'Pay now', to: '/invoices-billing',
    })
  }
  for (const r of openLabRequests.value) {
    if (!r.needed_before || new Date(r.needed_before) - Date.now() > 48 * HOUR) continue
    out.push({
      key: `lab${r.id}`, title: `Lab results needed before your consultation ${whenShort(r.needed_before)}.`,
      detail: `Still to upload: ${labsLeft(r).join(', ')}.`, action: 'Upload', to: '/lab-results',
    })
  }
  return out
})
const needsTodo = computed(() => {
  const out = []
  const urgent = new Set(needsUrgent.value.map(n => n.key))
  if (!screening.value) {
    out.push({ key: 'screening', title: 'Complete your health screening.', detail: 'Your RND needs it before your first consultation. It takes about a minute.', action: 'Start screening', to: '/pre-consultation-screening' })
  }
  for (const inv of unpaidInvoices.value) {
    if (urgent.has(`pay${inv.id}`)) continue
    out.push({
      key: `pay${inv.id}`, title: `Pay ${peso(inv.amount)} for your consultation.`,
      detail: inv.pay_by ? `Pay before ${whenShort(inv.pay_by)}.` : 'Pay before it starts.', action: 'Pay', to: '/invoices-billing',
    })
  }
  for (const r of openLabRequests.value) {
    if (urgent.has(`lab${r.id}`)) continue
    out.push({
      key: `lab${r.id}`, title: `${r.requested_by ? `RND ${r.requested_by}` : 'Your RND'} asked for lab results.`,
      detail: `${labsLeft(r).join(', ')}${r.needed_before ? `, before ${whenShort(r.needed_before)}` : ''}.`, action: 'Upload', to: '/lab-results',
    })
  }
  if (!activeRelationship.value && expiredRequest.value && !nextAppointment.value) {
    const rnd = expiredRequest.value.relationship?.rnd
    out.push({
      key: 'expired', title: 'Your booking request wasn\'t confirmed in time.',
      detail: `The ${formatLongDate(expiredRequest.value.scheduled_at)} request${rnd ? ` with RND ${rnd.first_name} ${rnd.last_name}` : ''} has passed. Pick a new time.`,
      action: 'Book again', to: rnd ? `/rnd-profile-view/${rnd.id}?book=1` : '/find-rnd',
    })
  }
  return out
})

/* ---------- Banner "Up next" card: the next consultation, if any ---------- */
const longToday = new Date().toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'long', month: 'long', day: 'numeric' })
const upNext = computed(() => {
  const a = nextAppointment.value
  if (!a) return null
  const rnd = a.relationship?.rnd || {}
  const name = `${rnd.first_name || ''} ${rnd.last_name || ''}`.trim()
  const sameDay = new Date(a.scheduled_at).toDateString() === new Date().toDateString()
  const day = sameDay ? '' : `${new Date(a.scheduled_at).toLocaleDateString('en-PH', { weekday: 'short', month: 'short', day: 'numeric' })}, `
  const d = new Date(a.scheduled_at)
  const dayWord = sameDay ? 'Today'
    : d.toDateString() === new Date(Date.now() + 86400000).toDateString() ? 'Tomorrow'
      : d.toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'long', month: 'short', day: 'numeric' })
  const state = a.status === 'pending' ? 'waiting' : a.payment?.status === 'paid' ? 'paid' : 'unpaid'
  return {
    when: `${day}${formatTime(a.scheduled_at)}`,
    time: formatTime(a.scheduled_at),
    day: dayWord,
    startsAt: d.getTime(),
    state,
    pill: { waiting: 'Waiting for your RND', paid: 'Paid', unpaid: 'Not paid yet' }[state],
    name,
    initials: `${rnd.first_name?.[0] || ''}${rnd.last_name?.[0] || ''}`.toUpperCase(),
    photo: rnd.profile_photo || (careRnd.value?.id === rnd.id ? careRnd.value.photo : ''),
    format: `${APPT_TYPES[a.type] || ''} consultation, ${a.duration_minutes || 60} min`.trim(),
  }
})

// Under the time: a countdown only on the day itself ("Today, in 5 hours",
// "Starts in 12 min"); other days just say the day. Ticks every 30 s.
const tick = useNow()
const whenLine = computed(() => {
  const u = upNext.value
  if (!u) return ''
  const mins = Math.round((u.startsAt - tick.value) / 60000)
  if (mins <= 0) return 'Starting now'
  if (mins < 60) return `Starts in ${mins} min`
  if (u.day !== 'Today') return u.day
  const hrs = Math.round(mins / 60)
  return `Today, in ${hrs} hour${hrs === 1 ? '' : 's'}`
})

// The card when nothing is booked: one short headline, one line of context.
const lastVisit = computed(() => appointments.value
  .filter(a => a.status === 'completed')
  .sort((a, b) => new Date(b.scheduled_at) - new Date(a.scheduled_at))[0] || null)
// Care that ended (discharged): no active RND, but past consultations. Used so
// the dashboard doesn't talk as if the client never had an RND (2026-11-02 fix).
const pastRnd = computed(() => (activeRelationship.value ? null : lastVisit.value?.relationship?.rnd || null))
const pastRndName = computed(() => (pastRnd.value ? `${pastRnd.value.first_name} ${pastRnd.value.last_name}` : ''))
const emptyCard = computed(() => {
  if (!screening.value) return { headline: 'Health screening', sub: 'About a minute. Your RND needs it before you meet.' }
  if (!activeRelationship.value && expiredRequest.value) return { headline: 'Booking expired', sub: 'Your last request passed before it was confirmed.' }
  if (activeRelationship.value) {
    const v = lastVisit.value
    if (!v) return { headline: 'Nothing booked', sub: 'Book your next consultation when you\'re ready.' }
    const days = Math.max(0, Math.round((Date.now() - new Date(v.scheduled_at)) / 86400000))
    const ago = days === 0 ? 'today' : days === 1 ? 'yesterday' : `${days} days ago`
    return { headline: 'Nothing booked', sub: `Your last consultation was ${formatShortDate(v.scheduled_at)}, ${ago}.` }
  }
  if (pastRnd.value) return { headline: 'Your care has ended', sub: `Book RND ${pastRndName.value} again, or find another RND.` }
  return { headline: 'Find your RND', sub: 'Pick a licensed RND and book your first consultation.' }
})

/* ---------- Next step (banner) ---------- */
const nextStep = computed(() => {
  const appt = nextAppointment.value
  const rndName = careRnd.value ? `RND ${careRnd.value.name}` : 'your RND'
  if (!screening.value) {
    return {
      eyebrow: 'Your next step',
      text: 'Complete your health screening. It takes about a minute and gives your RND your BMI, calorie needs and nutrition risk before you meet.',
      short: 'Your health screening. It takes about a minute.',
      action: 'Start screening', to: '/pre-consultation-screening',
    }
  }
  // Pay before the consultation (unpaid ones are cancelled 15 minutes before the start).
  if (appt?.status === 'confirmed' && appt.payment?.status === 'unpaid') {
    const amount = Number(appt.payment.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })
    return {
      eyebrow: 'Payment due',
      text: `${rndName} confirmed your ${formatLongDate(appt.scheduled_at)} ${formatTime(appt.scheduled_at)} consultation. Pay ₱${amount} any time before ${formatTime(new Date(new Date(appt.scheduled_at).getTime() - 15 * 60000))} on that day. Unpaid bookings are cancelled 15 minutes before the start.`,
      action: null, to: '/appointments', // no button here: paying lives in Needs you, the status pill says it
    }
  }
  if (appt?.status === 'confirmed') {
    const when = `${formatLongDate(appt.scheduled_at)} at ${formatTime(appt.scheduled_at)}`
    // Paid and inside the join window (15 min before to 15 min after)
    const canJoin = ['video', 'chat'].includes(appt.type) && appt.payment?.status === 'paid'
      && Date.now() >= new Date(appt.join_opens_at) && Date.now() <= new Date(appt.join_closes_at)
    return {
      eyebrow: 'Upcoming consultation',
      text: `${APPT_TYPES[appt.type] || ''} consultation with ${rndName} on ${when}.`,
      action: canJoin ? (appt.type === 'chat' ? 'Join chat' : 'Join video call') : 'View appointment',
      to: canJoin ? `/consultation-room/${appt.id}` : '/appointments',
    }
  }
  if (appt?.status === 'pending') {
    return {
      eyebrow: 'Waiting for your RND',
      text: `Your ${formatLongDate(appt.scheduled_at)} ${formatTime(appt.scheduled_at)} booking is waiting for ${rndName} to confirm. We'll notify you as soon as they do.`,
      action: 'View booking', to: '/appointments',
    }
  }
  // A booking request whose time passed before the RND confirmed it.
  if (!activeRelationship.value && expiredRequest.value) {
    const rnd = expiredRequest.value.relationship?.rnd
    return {
      eyebrow: 'Booking not confirmed',
      text: `Your ${formatLongDate(expiredRequest.value.scheduled_at)} booking request${rnd ? ` with RND ${rnd.first_name} ${rnd.last_name}` : ''} wasn't confirmed before its time passed. Pick a new time, or choose another RND.`,
      short: 'Your last booking request expired. Pick a new time.',
      action: 'Book a new time', to: rnd ? `/rnd-profile-view/${rnd.id}?book=1` : '/find-rnd',
    }
  }
  if (activeRelationship.value) {
    return {
      eyebrow: 'Stay on track',
      text: activePlan.value
        ? `You don't have an upcoming consultation with ${rndName}. Keep logging your meals, and book a follow-up when you're ready.`
        : `You don't have an upcoming consultation with ${rndName}. Book one to continue your care.`,
      short: `No consultation booked with ${rndName}.`,
      action: 'Book a consultation', to: `/rnd-profile-view/${activeRelationship.value.rnd.id}?book=1`,
    }
  }
  if (pastRnd.value) {
    return {
      eyebrow: 'Your next step',
      text: `Your care with RND ${pastRndName.value} has ended. You can book them again any time, or find another RND.`,
      short: `Your care with RND ${pastRndName.value} has ended.`,
      action: 'Book again', to: `/rnd-profile-view/${pastRnd.value.id}?book=1`,
    }
  }
  return {
    eyebrow: 'Your next step',
    text: 'Your screening is done. Find a licensed RND who fits your needs and book your first consultation.',
    short: 'Find an RND and book your first consultation.',
    action: 'Find an RND', to: '/find-rnd',
  }
})

/* ---------- Screening badges ---------- */
const nrsRiskLabel = computed(() => ({ no_risk: 'No risk', at_risk: 'At risk', high_risk: 'High risk' }[screening.value?.nrs_risk] || ''))
const nrsTone = computed(() => ({ no_risk: 'good', at_risk: 'warn', high_risk: 'bad' }[screening.value?.nrs_risk] || 'neutral'))
// The latest BMI: the newest progress record with one (from the RND's finalized
// NCP), else the screening, so it matches the weight chart (2026-11-02 fix).
const progressRows = ref([])
const currentBmi = computed(() => {
  const latest = [...progressRows.value].filter(r => r.bmi != null)
    .sort((a, b) => String(b.record_date).localeCompare(String(a.record_date)))[0]
  if (latest) return { value: Number(latest.bmi), label: bmiClass(Number(latest.bmi)) }
  if (screening.value?.bmi != null) return { value: Number(screening.value.bmi), label: screening.value.bmi_category }
  return null
})
const bmiTone = computed(() => ((currentBmi.value?.label || '').toLowerCase().includes('normal') ? 'good' : 'warn'))

/* ---------- Meal plan ---------- */
// Only the plan the RND has sent (drafts never reach the client).
const activePlan = computed(() => mealPlans.value.find(p => p.status === 'active') || null)

// The RND's target when there's a plan; otherwise the screening's estimate.
const calorieTarget = computed(() => {
  if (activePlan.value?.target_kcal) {
    return { value: Math.round(Number(activePlan.value.target_kcal)), label: 'Daily calorie target', note: 'Set by your RND in your meal plan' }
  }
  // no plan yet, but the RND has set a target in a finalized NCP record (newer than the screening)
  const upd = screening.value?.rnd_update
  if (upd?.target_kcal) {
    const when = new Date(`${upd.date}T00:00:00`).toLocaleDateString('en-PH', { month: 'short', day: 'numeric' })
    return { value: Math.round(Number(upd.target_kcal)), label: 'Daily calorie target', note: `Set by your RND on ${when}` }
  }
  if (screening.value?.tdee_kcal) {
    return { value: Math.round(Number(screening.value.tdee_kcal)), label: 'Estimated daily needs (TER)', note: 'Your RND sets your actual target' }
  }
  return { value: null, label: 'Daily calorie target', note: 'Complete your screening first' }
})
const planMacros = computed(() => {
  const p = activePlan.value
  if (!p?.target_kcal) return null
  const g = (v) => (v ? Math.round(Number(v)) : null)
  return { kcal: Math.round(Number(p.target_kcal)).toLocaleString(), carbs: g(p.target_carb_g), protein: g(p.target_protein_g), fat: g(p.target_fat_g) }
})

// Plans are per weekday (Sunday = 0); meals with no day (older plans) apply every day.
const todaysMeals = computed(() =>
  (activePlan.value?.meals || [])
    .filter(m => m.day_of_week === now.getDay() || m.day_of_week === null)
    .sort((a, b) => MEAL_ORDER.indexOf(a.meal_time) - MEAL_ORDER.indexOf(b.meal_time))
)
function mealFoodsLabel(meal) {
  const names = (meal.food_items || []).map(f => f.food_name).filter(Boolean)
  if (!names.length) return 'No foods listed'
  return names.length > 3 ? `${names.slice(0, 3).join(', ')} +${names.length - 3} more` : names.join(', ')
}

const todaysLogsByMeal = computed(() => {
  const map = {}
  for (const log of mealLogs.value) if (log.log_date === todayIso) map[log.meal_plan_meal] = log
  return map
})
function logLabel(meal) {
  const log = todaysLogsByMeal.value[meal.id]
  return log ? LOG_LABELS[log.status] || 'Waiting for your RND to rate it' : 'Not logged'
}
function logPillClass(meal) {
  const status = todaysLogsByMeal.value[meal.id]?.status
  if (todaysLogsByMeal.value[meal.id] && !status) return 'pill-gold'
  return { followed: 'pill-green', partially_followed: 'pill-gold', not_followed: 'badge-danger' }[status] || 'pill-muted'
}
const todayLoggedCount = computed(() => todaysMeals.value.filter(m => todaysLogsByMeal.value[m.id]).length)

// Last 7 days including today, from the client's own meal logs.
const weekAdherence = computed(() => {
  const start = new Date(now)
  start.setDate(start.getDate() - 6)
  const startIso = localIso(start)
  // Only meals the RND has rated count; the rest are waiting for their rating.
  const logs = mealLogs.value.filter(l => l.log_date >= startIso && l.log_date <= todayIso && l.status)
  const followed = logs.filter(l => l.status === 'followed').length
  const partly = logs.filter(l => l.status === 'partially_followed').length
  // partly followed counts as half, the same as the RND's adherence (patient_insights.adherence_pct)
  return { logged: logs.length, followed, partly, followedPct: logs.length ? Math.round(((followed + partly / 2) / logs.length) * 100) : 0 }
})

/* ---------- Weight chart (oldest → newest) ----------
   Starts from the screening — the baseline the RND measures progress from —
   then the latest progress readings, so the change matches the RND's view. */
const weightHistory = ref([])
function toWeightHistory(records, baseline) {
  const points = records
    .filter(r => r.weight_kg != null)
    .slice(0, baseline ? 7 : 8)
    .reverse()
    .map(r => ({
      weight: Number(r.weight_kg),
      label: new Date(r.record_date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    }))
  if (baseline?.weight_kg != null) points.unshift({ weight: Number(baseline.weight_kg), label: 'Screening' })
  return points
}
const weightDeltaLabel = computed(() => {
  if (weightHistory.value.length < 2) return ''
  const delta = weightHistory.value[weightHistory.value.length - 1].weight - weightHistory.value[0].weight
  if (Math.abs(delta) < 0.05) return 'No change'
  return `${delta < 0 ? '↓' : '↑'} ${Math.abs(delta).toFixed(1)} kg ${weightHistory.value[0].label === 'Screening' ? 'since your screening' : 'overall'}`
})
const chartCoords = computed(() => {
  if (!weightHistory.value.length) return []
  const weights = weightHistory.value.map(w => w.weight)
  const minW = Math.min(...weights)
  const maxW = Math.max(...weights)
  const range = maxW - minW || 1
  const n = weightHistory.value.length
  return weightHistory.value.map((w, i) => ({
    label: w.label,
    weight: w.weight,
    x: n > 1 ? (i / (n - 1)) * 400 : 200,
    y: 80 - ((w.weight - minW) / range) * 56,
  }))
})
const chartPoints = computed(() => chartCoords.value.map(p => `${p.x},${p.y}`).join(' '))
const chartFillPoints = computed(() => {
  const c = chartCoords.value
  if (!c.length) return ''
  return `${chartPoints.value} ${c[c.length - 1].x},90 ${c[0].x},90`
})

/* ---------- Recent activity ---------- */
const recentActivity = computed(() => notifications.value.slice(0, 5))

async function loadDashboard({ quiet = false } = {}) {
  if (!quiet) {
    isLoading.value = true
    errorMessage.value = ''
  }
  try {
    const [appts, rels, latestScreening, progress, plans, logs, invs, notes, labData] = await Promise.all([
      get('/client/appointments/'),
      get('/client/relationships/'),
      get('/client/screening/latest/').catch(() => null),
      get('/client/progress/').catch(() => []),
      get('/client/meal-plans/').catch(() => []),
      get('/client/meal-logs/').catch(() => []),
      get('/client/invoices/').catch(() => []),
      get('/notifications/').catch(() => []),
      get('/client/labs/').catch(() => null),
    ])
    labs.value = labData
    appointments.value = appts
    relationships.value = rels
    screening.value = latestScreening
    weightHistory.value = toWeightHistory(progress, latestScreening)
    progressRows.value = Array.isArray(progress) ? progress : progress?.results || []
    mealPlans.value = plans
    mealLogs.value = logs
    invoices.value = invs
    notifications.value = Array.isArray(notes) ? notes : notes?.results || []

    const rndId = careRnd.value?.id
    if (rndId) rndProfile.value = await get(`/client/rnds/${rndId}/`).catch(() => null)
  } catch {
    if (!quiet) errorMessage.value = 'Could not load your dashboard. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadDashboard)
// stays current without a reload (composables/useAutoRefresh.js)
useAutoRefresh(() => Promise.all([loadDashboard({ quiet: true }), loadToday()]))

/* Coming up today — consultations, meals to log and RND reminders (also
   sends any reminder that's due right now). */
const TODAY_ICONS = { appointment: CalendarCheck, meal: UtensilsCrossed, reminder: AlarmClock }
const todayItems = ref([])
const todayLoaded = ref(false)
async function loadToday() {
  try {
    todayItems.value = await get('/client/today/')
  } catch {
    todayItems.value = []
  } finally {
    todayLoaded.value = true
  }
}
onMounted(loadToday)

// My tasks: tick off tasks (POST /client/reminders/<id>/check/), add your own.
const checkable = computed(() => todayItems.value.filter(i => ['task', 'meal', 'lab'].includes(i.kind)))
const taskCount = computed(() => checkable.value.length)
const doneCount = computed(() => checkable.value.filter(i => i.done).length)
// One request per task at a time (2026-11-03): quick ticks could arrive out of order.
const taskBusy = ref(null)
const toast = useToast()
async function toggleTask(item, done) {
  if (taskBusy.value === item.id) return
  taskBusy.value = item.id
  item.done = done
  try {
    item.done = (await post(`/client/reminders/${item.id}/check/`, { done })).done
  } catch {
    item.done = !done
    toast.error('Could not update this task. Please try again.', { id: 'task' })
  } finally {
    taskBusy.value = null
  }
}
const addOpen = ref(false)
const adding = ref(false)
const addError = ref('')
function defaultTime() {
  const d = new Date(Date.now() + 30 * 60000)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
const newTask = reactive({ title: '', time: defaultTime(), repeat: 'once' })
async function addTask() {
  adding.value = true
  addError.value = ''
  try {
    const today = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' })
    await post('/client/reminders/', { title: newTask.title.trim(), date: today, time: newTask.time, repeat: newTask.repeat })
    Object.assign(newTask, { title: '', time: defaultTime(), repeat: 'once' })
    addOpen.value = false
    await loadToday()
  } catch (e) {
    const d = e?.data || {}
    addError.value = d.time?.[0] || d.title?.[0] || d.detail || 'Could not add the task.'
  } finally {
    adding.value = false
  }
}
async function removeTask(item) {
  if (taskBusy.value === item.id) return
  taskBusy.value = item.id
  try {
    await del(`/client/reminders/${item.id}/`)
    todayItems.value = todayItems.value.filter(i => i !== item)
  } catch {
    toast.error('Could not delete this task. Please try again.', { id: 'task' })
  } finally {
    taskBusy.value = null
  }
}
function phClock(iso) {
  return new Date(iso).toLocaleTimeString('en-PH', { timeZone: 'Asia/Manila', hour: 'numeric', minute: '2-digit' })
}

/* ---------- UI only: weight chart with a 30 / 90 day range ----------
   Reads the same progress records and screening the page already loads. */
const weightDays = ref(30)
const rangePoints = computed(() => {
  const cutoff = Date.now() - weightDays.value * 86400000
  const pts = []
  const s = screening.value
  if (s?.weight_kg != null && s.created_at) {
    const t = new Date(s.created_at).getTime()
    if (t >= cutoff) pts.push({ weight: Number(s.weight_kg), label: 'Screening', t })
  }
  for (const r of progressRows.value) {
    if (r.weight_kg == null || !r.record_date) continue
    const t = new Date(`${r.record_date}T00:00:00`).getTime()
    if (t >= cutoff) pts.push({ weight: Number(r.weight_kg), label: new Date(t).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }), t })
  }
  pts.sort((a, b) => a.t - b.t)
  if (!pts.length && weightHistory.value.length) return [{ ...weightHistory.value[weightHistory.value.length - 1], old: true }]
  return pts.slice(-10)
})
const rangeChart = computed(() => {
  const pts = rangePoints.value
  if (!pts.length) return null
  const ws = pts.map(p => p.weight)
  const lo = Math.floor(Math.min(...ws)) - 1
  const hi = Math.max(Math.ceil(Math.max(...ws)) + 1, lo + 3)
  const step = (hi - lo) / 3
  const Y = w => 170 - ((w - lo) / (hi - lo)) * 150
  const grid = [0, 1, 2, 3].map(i => {
    const v = hi - i * step
    return { y: Y(v), label: Number.isInteger(v) ? v : v.toFixed(1) }
  })
  const n = pts.length
  const points = pts.map((p, i) => ({ ...p, x: n > 1 ? 60 + (i / (n - 1)) * 520 : 60, y: Y(p.weight) }))
  const line = points.map(p => `${p.x},${p.y}`).join(' ')
  return { grid, points, line, fill: n > 1 ? `${line} ${points[n - 1].x},170 ${points[0].x},170` : '', single: n === 1 }
})
const rangeDelta = computed(() => {
  const p = rangePoints.value
  if (p.length === 1) return p[0].old ? `Latest reading, before the last ${weightDays.value} days` : 'First entry'
  const d = p[p.length - 1].weight - p[0].weight
  if (Math.abs(d) < 0.05) return 'No change'
  return `${d < 0 ? '↓' : '↑'} ${Math.abs(d).toFixed(1)} kg in ${weightDays.value} days`
})

// ---- UI helpers only: date block in the Up next card ----
const ubMonth = t => new Date(t).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', month: 'short' }).toUpperCase()
const ubDay = t => new Date(t).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', day: 'numeric' })
const ubWeek = t => new Date(t).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'short' })

// ---- UI helpers only: today's meal plan as a photo log (first 3, then See all) ----
const MT_FIRST = 3
const mtShowAll = ref(false)
function mtState(meal) {
  if (todaysLogsByMeal.value[meal.id]) return 'logged'
  const firstOpen = todaysMeals.value.find(m => !todaysLogsByMeal.value[m.id])
  return firstOpen && firstOpen.id === meal.id ? 'now' : 'later'
}
const mtVisible = computed(() => {
  const list = todaysMeals.value
  if (mtShowAll.value || list.length <= MT_FIRST) return list
  const open = list.findIndex(m => !todaysLogsByMeal.value[m.id])
  const start = open === -1 ? list.length - MT_FIRST : Math.max(0, Math.min(open - 1, list.length - MT_FIRST))
  return list.slice(start, start + MT_FIRST)
})
function mtFoods(meal) {
  const names = (meal.food_items || []).map(f => f.food_name).filter(Boolean)
  return names.length > 3 ? [...names.slice(0, 3), `+${names.length - 3} more`] : names
}

// ---- UI helpers only: Recent activity, grouped by day, repeats combined ----
const RA_KINDS = [
  { words: ['consult', 'appointment', 'booking', 'starts soon', 'video'], tone: 'gold', svg: '<circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" />' },
  { words: ['reminder', 'task'], tone: 'green', svg: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10 21a2 2 0 0 0 4 0" />' },
  { words: ['meal', 'plan', 'rated', 'log'], tone: 'orange', svg: '<path d="M4 3v8a2 2 0 0 0 2 2h1v8M8 3v6M6 3v6M16 21V3c-2 1-3 4-3 8h3" />' },
  { words: ['payment', 'paid', 'invoice', 'receipt', 'refund'], tone: 'blue', svg: '<rect x="3" y="5" width="18" height="14" rx="3" /><path d="M3 10h18M7 15h4" />' },
  { words: ['message', 'chat'], tone: 'green', svg: '<path d="M4 5h16v11H8l-4 4z" />' },
  { words: ['lab', 'result', 'screening', 'ncp', 'record'], tone: 'purple', svg: '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6M8 13h8M8 17h5" />' },
]
const RA_DEFAULT = { tone: 'green', svg: '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10 21a2 2 0 0 0 4 0" />' }
function raKind(subject) {
  const t = String(subject || '').toLowerCase()
  return RA_KINDS.find(k => k.words.some(w => t.includes(w))) || RA_DEFAULT
}
function raDayLabel(v) {
  const d = new Date(v).toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' })
  if (d === todayIso) return 'Today'
  if (d === new Date(Date.now() - 86400000).toLocaleDateString('en-CA', { timeZone: 'Asia/Manila' })) return 'Yesterday'
  return new Date(v).toLocaleDateString('en-PH', { timeZone: 'Asia/Manila', weekday: 'long', month: 'short', day: 'numeric' })
}
const raDays = computed(() => {
  const rows = []
  for (const n of recentActivity.value) {
    const last = rows[rows.length - 1]
    if (last && last.subject === n.subject && raDayLabel(last.created_at) === raDayLabel(n.created_at)) {
      last.count += 1
      if (!n.is_read) last.unread = true
      if (n.content && !last.details.includes(n.content)) last.details.push(n.content)
    } else {
      rows.push({ id: n.id, subject: n.subject, created_at: n.created_at, count: 1, unread: !n.is_read, details: n.content ? [n.content] : [] })
    }
  }
  const days = []
  for (const r of rows) {
    r.detail = r.details.join(', ')
    const label = raDayLabel(r.created_at)
    let g = days.find(x => x.label === label)
    if (!g) days.push(g = { label, rows: [], unread: 0 })
    g.rows.push(r)
    if (r.unread) g.unread += 1
  }
  return days
})

// ---- UI helpers only: My tasks as a timeline (first 4, then See all) ----
const TK_FIRST = 4
const TK_KIND = { meal: 'Meal', lab: 'Lab', appointment: 'Consultation', reminder: 'Reminder' }
const tkShowAll = ref(false)
const tkNext = computed(() => todayItems.value.find(i => !i.done) || null)
const tkVisible = computed(() => {
  const list = todayItems.value
  if (tkShowAll.value || list.length <= TK_FIRST) return list
  const open = list.findIndex(i => !i.done)
  const start = open === -1 ? list.length - TK_FIRST : Math.max(0, Math.min(open - 1, list.length - TK_FIRST))
  return list.slice(start, start + TK_FIRST)
})
</script>

<style scoped>
/* =========================================================
   Client dashboard: brand #004D3A / #EFBF04 / white
   Fonts: Playfair Display (headings, numbers), DM Sans (body)
   ========================================================= */
* { box-sizing: border-box; }

.client-dashboard {
  font-family: 'DM Sans', 'Inter', Arial, sans-serif;
  color: #14261E;
  display: flex;
  flex-direction: column;
  gap: 22px;
}
.unit { font-family: 'DM Sans', Arial, sans-serif; font-size: 14px; font-weight: 600; color: #6B7D73; }

.form-error {
  margin: 0;
  padding: 12px 16px;
  border-radius: 14px;
  background: #FEF3F2;
  border: 1px solid #FECDCA;
  color: #B42318;
  font-size: 14px;
}
.placeholder-text { margin: 0; font-size: 14px; color: #6B7D73; }
.empty-note { margin: 0; font-size: 13.5px; line-height: 1.6; color: #6B7D73; }
.empty-note.spaced { margin-bottom: 16px; }

/* ---------- BANNER ---------- */
.client-dashboard .cd-hero {
  position: relative;
  overflow: hidden;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 360px);
  align-items: center;
  gap: 28px;
  margin: 0;
  padding: 32px 34px;
  border: none;
  border-radius: 24px;
  color: #FFFFFF;
  background:
    radial-gradient(70% 140% at 0% 0%, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0) 60%),
    linear-gradient(120deg, #005A43 0%, #004D3A 55%, #00402F 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 24px 50px -18px rgba(0, 77, 58, 0.55);
}
.cd-hero-plate {
  position: absolute;
  right: -80px;
  top: 50%;
  width: 520px;
  height: 520px;
  transform: translateY(-50%);
  object-fit: cover;
  border-radius: 50%;
  opacity: 0.55;
  pointer-events: none;
}
.cd-hero-fade {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(0, 70, 52, 0) 46%, rgba(0, 68, 51, 0.86) 63%, rgba(0, 64, 47, 0.35) 100%);
  pointer-events: none;
}
.cd-hero > *:not(.cd-hero-plate):not(.cd-hero-fade) { position: relative; z-index: 2; }
/* no overlay from the shared banner styles may cover the photo */
.client-dashboard .cd-hero::before,
.client-dashboard .cd-hero::after { display: none !important; content: none !important; }
.client-dashboard .cd-hero .cd-hero-plate { z-index: 0; display: block; max-width: none; opacity: 0.55; filter: none; }
.client-dashboard .cd-hero .cd-hero-fade { z-index: 1; }
.client-dashboard .nm-hero-title em { font-style: italic; color: #EFBF04; background: none; padding: 0; }
.client-dashboard .nm-hero-greet { min-width: 0; }
.client-dashboard .nm-hero-date {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #EFBF04;
}
.client-dashboard .nm-hero-date::before { content: ''; width: 24px; height: 2px; border-radius: 2px; background: #EFBF04; }
.client-dashboard .nm-hero-title {
  margin: 10px 0 10px;
  padding: 0;
  background: none;
  font-family: 'Playfair Display', Georgia, serif;
  font-size: 38px;
  line-height: 1.1;
  font-weight: 700;
  color: #FFFFFF;
}
.client-dashboard .nm-hero-sub { margin: 0; max-width: 560px; font-size: 15px; line-height: 1.65; color: rgba(255, 255, 255, 0.85); }

/* UP NEXT card: frosted glass, the time is the big thing */
.client-dashboard .nm-upnext {
  display: flex;
  flex-direction: column;
  padding: 20px 22px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  color: #FFFFFF;
  box-shadow: none;
}
.client-dashboard .nm-upnext-label { font-size: 11.5px; font-weight: 800; letter-spacing: 1.6px; text-transform: uppercase; color: #EFBF04; }
.up { gap: 0; }
.up-top { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.up-status { display: inline-flex; align-items: center; gap: 7px; height: 26px; padding: 0 10px; border-radius: 999px; background: rgba(255, 255, 255, 0.12); font-size: 12.5px; font-weight: 700; white-space: nowrap; }
.up-dot { width: 8px; height: 8px; border-radius: 50%; background: #FFFFFF; flex-shrink: 0; }
.up-status.unpaid { color: #EFBF04; background: rgba(239, 191, 4, 0.16); }
.up-status.unpaid .up-dot { background: #EFBF04; box-shadow: 0 0 0 3px rgba(239, 191, 4, 0.25); }
.up-status.paid { color: #9BE3BD; }
.up-status.paid .up-dot { background: #4ADE80; }
.up-status.waiting { color: #FFFFFF; }
.up-time { margin: 12px 0 2px; font-family: 'Playfair Display', Georgia, serif; font-size: 38px; font-weight: 700; line-height: 1.05; color: #FFFFFF; font-variant-numeric: lining-nums; }
.up-time.small { margin: 8px 0 6px; font-size: 24px; }
.up-when { margin: 0; font-size: 14px; color: rgba(255, 255, 255, 0.82); }
.up-with { margin: 4px 0 0; font-size: 13px; color: rgba(255, 255, 255, 0.7); overflow-wrap: anywhere; }
.up-empty { display: flex; flex-direction: column; align-items: stretch; gap: 16px; }
.up-top + .up-empty { margin-top: 2px; }
.up-empty-text { min-width: 0; }
.up-empty-btn { flex-shrink: 0; }
.client-dashboard .nm-upnext .nm-hero-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 44px;
  padding: 0 18px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: transparent;
  color: #FFFFFF;
  font-family: inherit;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color .15s, transform .15s;
}
.client-dashboard .nm-upnext .nm-hero-btn:hover { background: rgba(255, 255, 255, 0.12); }
.client-dashboard .nm-upnext .nm-hero-btn.primary {
  border-color: #EFBF04;
  background: #EFBF04;
  color: #004D3A;
  box-shadow: 0 10px 20px -10px rgba(196, 145, 2, 0.9);
}
.client-dashboard .nm-upnext .nm-hero-btn.primary:hover { background: #F5CB1F; transform: translateY(-1px); }

/* NEEDS ATTENTION strip (NeedsAttention.vue) */
.needs-strip { margin: 0; }
/* the shared strip, given this page's look (only its outer box) */
.client-dashboard .needs-strip {
  border-radius: 14px !important;
  background: #EAF4EE !important;
  border: 1px solid #CFE5D7 !important;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05), 0 10px 22px -12px rgba(0, 77, 58, 0.25) !important;
  color: #004D3A;
  font-weight: 600;
}
.notice-text { flex: 1; font-size: 14px; }
.notice-text strong { color: #10231B; }

/* ---------- HEALTH FIGURES: four cards ---------- */
.stat-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.stat-card,
.panel {
  background: #FFFFFF;
  border: 1px solid #E1E7E3;
  border-radius: 20px;
  box-shadow:
    0 0 0 1px rgba(0, 0, 0, 0.02),
    0 2px 6px rgba(0, 0, 0, 0.06),
    0 12px 28px -6px rgba(0, 0, 0, 0.12),
    0 24px 48px -18px rgba(0, 77, 58, 0.22);
}
.stat-card {
  position: relative;
  min-width: 0;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  transition: transform .15s, box-shadow .15s;
}
.stat-card:hover { transform: translateY(-3px); box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.02), 0 4px 10px rgba(0, 0, 0, 0.08), 0 20px 40px -10px rgba(0, 0, 0, 0.18), 0 30px 60px -20px rgba(0, 77, 58, 0.3); }
.stat-card { gap: 12px; }
.stat-top { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.stat-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #EEF4F0;
  color: #004D3A;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.stat-icon.gold { background: #FBF6E4; color: #9A7300; }
.stat-pill { height: 26px; padding: 0 10px; display: inline-flex; align-items: center; border-radius: 999px; font-size: 12px; font-weight: 700; white-space: nowrap; }
.stat-pill.good { background: #EAF4EE; color: #004D3A; }
.stat-pill.warn { background: #FBF6E4; color: #7A5A00; }
.stat-pill.bad { background: #FEF3F2; color: #B42318; }
.stat-pill.neutral { background: #F3F5F4; color: #5D7065; }
.stat-value { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 34px; font-weight: 700; line-height: 1.1; color: #10231B; font-variant-numeric: lining-nums; }
.stat-value.muted { color: #C3CEC8; }
.stat-label { margin: 2px 0 0; font-size: 13.5px; font-weight: 700; color: #22362C; }
.stat-delta { margin: 0; font-size: 12.5px; line-height: 1.5; }
.stat-delta.neutral { color: #6B7D73; }
.stat-delta.good { color: #1F7A4C; font-weight: 600; }
.stat-delta.warn { color: #8A6500; font-weight: 600; }
.stat-delta.bad { color: #B42318; font-weight: 600; }
.bmi-gauge { position: relative; height: 6px; margin-top: 4px; border-radius: 99px; background: linear-gradient(90deg, #EFBF04 0 21%, #2E9E64 21% 50%, #F29B38 50% 73%, #D9534F 73%); }
.bmi-pin { position: absolute; top: -4px; width: 14px; height: 14px; margin-left: -7px; border-radius: 50%; background: #FFFFFF; border: 3px solid #004D3A; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2); }

/* ---------- GRID + PANELS ---------- */
.dash-grid { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 22px; align-items: start; }
.dash-col { display: flex; flex-direction: column; gap: 22px; min-width: 0; }
.panel { padding: 22px 24px; }
.panel-title { margin: 0 0 14px; font-family: 'Playfair Display', Georgia, serif; font-size: 20px; font-weight: 700; color: #10231B; }
.panel-title.flush { margin: 0; }
.panel-sub { margin: 4px 0 0; font-size: 13px; color: #6B7D73; }
.panel-header-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 18px; }
.panel-link { font-size: 13px; font-weight: 700; color: #004D3A; text-decoration: none; white-space: nowrap; }
.panel-link:hover { text-decoration: underline; }
.panel-meta { height: 26px; padding: 0 10px; display: inline-flex; align-items: center; border-radius: 999px; background: #EEF4F0; font-size: 12.5px; font-weight: 700; color: #004D3A; white-space: nowrap; }

/* soft / dark buttons used on this page (shared nm-btn-* classes, given the page look) */
.client-dashboard .nm-btn-soft,
.client-dashboard .nm-btn-dark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 40px;
  padding: 0 16px;
  border-radius: 12px;
  border: none;
  font-family: inherit;
  font-size: 13.5px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
  cursor: pointer;
  transition: background-color .15s;
}
.client-dashboard .nm-btn-soft { background: #F1F6F2; color: #004D3A; }
.client-dashboard .nm-btn-soft:hover { background: #E3EFE7; }
.client-dashboard .nm-btn-dark { background: #004D3A; color: #FFFFFF; box-shadow: 0 10px 20px -12px rgba(0, 77, 58, 0.8); }
.client-dashboard .nm-btn-dark:hover:not(:disabled) { background: #0A5C46; }
.client-dashboard .nm-btn-dark:disabled { opacity: .5; cursor: not-allowed; box-shadow: none; }
.client-dashboard .nm-btn-sm { height: 36px; padding: 0 14px; font-size: 13px; }
.block-wide { width: 100%; height: 46px !important; }

/* PILLS (meal log status) */
.status-pill { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; white-space: nowrap; }
.pill-green { background: #E3F3EA; color: #1F7A4C; }
.pill-gold { background: #FBF3D2; color: #8A6500; }
.pill-muted { background: #F1F4F2; color: #5D7065; }
.badge-danger { background: #FEF3F2; color: #B42318; }

/* old outlined block button (kept for any page that still uses it) */
.block-btn {
  display: block; width: 100%; text-align: center; background: #FFFFFF; border: 1.5px solid #004D3A; color: #004D3A;
  border-radius: 12px; padding: 11px; font-weight: 700; font-size: 14px; font-family: inherit; cursor: pointer; text-decoration: none;
}
.block-btn:hover { background: #F1F6F2; }
.btn-row { display: flex; gap: 10px; }

/* ---------- TODAY'S MEAL PLAN ---------- */
.macro-strip {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 18px;
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: 14px;
  background: linear-gradient(90deg, #EEF4F0, #F8F4E4);
  font-size: 13.5px;
  color: #3E5046;
}
.macro-strip strong { font-family: 'Playfair Display', Georgia, serif; font-size: 16px; color: #10231B; }
.macro-source { margin-left: auto; font-size: 12px; color: #6B7D73; }
.meal-list { list-style: none; margin: 0; padding: 0; }
.meal-row { display: flex; align-items: center; gap: 14px; padding: 12px 0; border-top: 1px solid #EEF2EF; }
.meal-row:first-child { border-top: none; padding-top: 0; }
.meal-icon { width: 40px; height: 40px; flex-shrink: 0; border-radius: 12px; background: #EEF4F0; color: #004D3A; display: flex; align-items: center; justify-content: center; }
.meal-info { flex: 1; min-width: 0; }
.meal-name { margin: 0; font-size: 14.5px; font-weight: 700; color: #10231B; }
.meal-detail { margin: 2px 0 0; font-size: 13px; color: #6B7D73; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.adherence-row { display: grid; grid-template-columns: auto 1fr; gap: 12px; margin-top: 14px; padding-top: 16px; border-top: 1px solid #EEF2EF; }
.adherence-item { display: flex; align-items: baseline; gap: 10px; min-width: 0; padding: 12px 14px; border-radius: 14px; background: #F7FAF8; }
.adherence-value { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #004D3A; }
.adherence-label { margin: 0; font-size: 12.5px; line-height: 1.5; color: #5D7065; }
.empty-state { padding: 26px 16px; border-radius: 16px; background: #F7FAF8; text-align: center; font-size: 14px; color: #3E5046; }
.empty-state p { margin: 0; font-weight: 700; }
.empty-icon { margin-bottom: 10px; padding: 10px; width: 44px; height: 44px; border-radius: 14px; background: #FFFFFF; color: #004D3A; box-shadow: 0 6px 14px -10px rgba(0, 77, 58, 0.6); }
.empty-sub { margin-top: 6px !important; font-size: 13px; font-weight: 400 !important; line-height: 1.55; color: #6B7D73; }

/* ---------- WEIGHT CHART ---------- */
.weight-chart { padding: 12px 0 4px; }

/* ---------- YOUR RND ---------- */
.rnd-row { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.rnd-avatar { width: 52px; height: 52px; flex-shrink: 0; border-radius: 16px; background: #EFBF04; color: #004D3A; display: flex; align-items: center; justify-content: center; font-weight: 800; }
.rnd-avatar-img { object-fit: cover; background: #00382A; }
.rnd-text { min-width: 0; }
.rnd-name { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 17px; font-weight: 700; color: #10231B; }
.rnd-specialty { margin: 2px 0 0; font-size: 13px; color: #5D7065; }
.rnd-rating { margin: 2px 0 0; font-size: 12.5px; font-weight: 700; color: #9A7300; }
.rnd-pending { display: inline-flex; margin: 6px 0 0; padding: 2px 10px; border-radius: 999px; background: #FBF3D2; font-size: 12px; font-weight: 700; color: #8A6500; }
.rnd-compact {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  background: linear-gradient(90deg, #FFFFFF 0%, #F7FAF8 100%);
}
.rnd-compact .rnd-text { flex: 1; min-width: 0; }
.rnd-compact .rnd-name { overflow-wrap: anywhere; }
.rnd-eyebrow { margin: 0 0 2px; font-size: 11.5px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; color: #C49102; }
.rnd-actions { display: flex; gap: 8px; flex-shrink: 0; }
.icon-action { width: 40px; height: 40px; border-radius: 12px; background: #EEF4F0; display: flex; align-items: center; justify-content: center; color: #004D3A; text-decoration: none; transition: background-color .15s; }
.icon-action:hover { background: #004D3A; color: #EFBF04; }
.icon-action:focus-visible { outline: 2px solid #EFBF04; outline-offset: 2px; }

/* ---------- MY TASKS ---------- */
.today-row { display: flex; align-items: center; gap: 12px; padding: 12px 0; border-top: 1px solid #EEF2EF; text-decoration: none; color: inherit; }
.panel-header-row + .today-row { margin-top: 0; border-top: none; }
.today-row.done { opacity: 0.55; }
.today-row.done .today-title { text-decoration: line-through; }
.today-icon { width: 34px; height: 34px; flex-shrink: 0; border-radius: 10px; display: flex; align-items: center; justify-content: center; background: #EEF4F0; color: #004D3A; }
.today-icon.k-reminder { background: #FBF3D2; color: #9A7300; }
.today-icon.k-appointment { background: #004D3A; color: #EFBF04; }
.today-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; }
.today-title { font-size: 14px; font-weight: 700; color: #10231B; overflow-wrap: anywhere; }
.today-detail { font-size: 12.5px; color: #6B7D73; }
.today-time { height: 24px; padding: 0 9px; display: inline-flex; align-items: center; border-radius: 999px; background: #F1F4F2; font-size: 12px; font-weight: 700; color: #3E5046; white-space: nowrap; }
.today-row.task { cursor: pointer; }
.task-check { width: 22px; height: 22px; margin: 0 6px; flex-shrink: 0; accent-color: #004D3A; cursor: pointer; }
.task-check.meal { display: inline-flex; align-items: center; justify-content: center; border: 2px solid #B8C9BE; border-radius: 7px; color: #FFFFFF; }
.task-check.meal.on { background: #004D3A; border-color: #004D3A; }
.today-note { display: block; margin: 2px 0; padding: 6px 10px; border-left: 3px solid #EFBF04; border-radius: 0 8px 8px 0; background: #FBF8EC; font-size: 13px; line-height: 1.45; color: #3E5046; white-space: pre-line; overflow-wrap: anywhere; }
.task-x { display: flex; padding: 6px; border: none; border-radius: 8px; background: none; color: #9AA9A1; cursor: pointer; }
.task-x:hover { background: #FEF3F2; color: #B42318; }
.as-btn { background: none; border: none; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 3px; padding: 0; }
.add-task { display: flex; flex-direction: column; gap: 10px; margin-bottom: 10px; padding: 14px; border-radius: 16px; background: #F7FAF8; border: 1px solid #E3EAE5; }
.add-task .nm-input,
.add-task .nm-select {
  min-height: 44px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1.5px solid #DCE5DF;
  background: #FFFFFF;
  font-family: inherit;
  font-size: 14px;
  color: #14261E;
}
.add-task .nm-input:focus,
.add-task .nm-select:focus { outline: none; border-color: #004D3A; box-shadow: 0 0 0 4px rgba(0, 77, 58, 0.1); }
.add-task-row { display: flex; gap: 8px; }
.add-task-row .nm-input,
.add-task-row .nm-select { flex: 1; min-width: 0; }
.add-error { margin: 0; font-size: 12.5px; font-weight: 600; color: #B42318; }

/* ---------- SCREENING ---------- */
.screening-summary-text { margin: 0 0 16px; font-size: 14px; line-height: 1.6; color: #5D7065; }

/* ---------- RECENT ACTIVITY ---------- */
.activity-row { display: flex; align-items: flex-start; gap: 12px; padding: 12px 0; border-top: 1px solid #EEF2EF; }
.activity-row:first-of-type { border-top: none; padding-top: 0; }
.activity-dot { width: 9px; height: 9px; flex-shrink: 0; margin-top: 6px; border-radius: 50%; background: #D3DCD6; }
.activity-dot.unread { background: #EFBF04; box-shadow: 0 0 0 4px rgba(239, 191, 4, 0.2); }
.activity-text { min-width: 0; }
.activity-title { margin: 0; font-size: 14px; font-weight: 700; color: #10231B; overflow-wrap: anywhere; }
.activity-time { margin: 2px 0 0; font-size: 12.5px; color: #6B7D73; }


/* link with an arrow (Open meal plan) */
.ic { flex-shrink: 0; display: inline-block; vertical-align: middle; }
.cd-link { display: inline-flex; align-items: center; gap: 6px; font-size: 13.5px; font-weight: 700; color: #004D3A; text-decoration: none; white-space: nowrap; }
.cd-link:hover { text-decoration: underline; text-underline-offset: 3px; }
.title-unit { font-family: 'DM Sans', Arial, sans-serif; font-size: 14px; font-weight: 600; color: #6B7D73; }

/* no meal plan yet: a Pinggang Pinoy plate */
.empty-plate { display: flex; align-items: center; gap: 22px; }
.plate-ring {
  position: relative;
  flex-shrink: 0;
  width: 112px;
  height: 112px;
  border-radius: 50%;
  background: conic-gradient(#DDEBE2 0 50%, #F6E7B4 50% 75%, #F0D9C8 75% 100%);
  box-shadow: inset 0 0 0 10px #FFFFFF, 0 0 0 1px #E6ECE8, 0 14px 26px -18px rgba(0, 77, 58, 0.5);
}
.plate-ring span { position: absolute; inset: 30px; border-radius: 50%; background: #FFFFFF; display: flex; align-items: center; justify-content: center; color: #004D3A; }
.empty-plate-text { flex: 1; min-width: 0; }
.empty-plate-title { margin: 0 0 6px; font-size: 16px; font-weight: 700; color: #10231B; }
.empty-plate .empty-sub { margin: 0 0 14px !important; font-size: 14px; line-height: 1.6; color: #5D7065; }
.plate-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.plate-chips span { height: 26px; padding: 0 10px; display: inline-flex; align-items: center; border-radius: 999px; font-size: 12px; font-weight: 700; }
.c-veg { background: #EAF4EE; color: #004D3A; }
.c-grain { background: #FBF6E4; color: #7A5A00; }
.c-prot { background: #F8ECE4; color: #8A4B2A; }

/* your RND, not connected yet */
.rnd-compact.empty { display: block; padding: 20px 22px; background: #FFFFFF; }
.rnd-empty-row { display: flex; align-items: center; gap: 14px; margin: 12px 0 16px; }
.rnd-avatar.dashed { border: 2px dashed #C9D6CE; background: #F7FAF8; color: #9AA9A1; }
.rnd-empty .rnd-name { font-family: 'DM Sans', Arial, sans-serif; font-size: 15px; }
.rnd-empty .nm-btn-dark { height: 48px !important; }

/* no tasks today */
.tasks-empty { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 12px 12px 6px; text-align: center; }
.tasks-empty-icon { width: 48px; height: 48px; border-radius: 14px; background: #EAF4EE; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.tasks-empty-title { margin: 0; font-size: 15px; font-weight: 700; color: #10231B; }


/* weight */
.weight-now { display: flex; align-items: baseline; flex-wrap: wrap; gap: 10px; margin-bottom: 4px; }
.weight-now-value { font-family: 'Playfair Display', Georgia, serif; font-size: 30px; font-weight: 700; color: #10231B; }
.weight-now-unit { font-size: 14px; font-weight: 700; color: #6B7D73; }
.weight-foot { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-top: 12px; padding: 12px 14px; border-radius: 12px; background: #F7FAF8; font-size: 13.5px; color: #4A5A52; }


/* 30 / 90 days */
.range-toggle { display: inline-flex; gap: 4px; padding: 4px; border-radius: 999px; background: #F1F6F2; }
.range-toggle button { height: 28px; padding: 0 12px; border: none; border-radius: 999px; background: transparent; color: #004D3A; font-family: inherit; font-size: 12.5px; font-weight: 700; cursor: pointer; transition: background-color .15s, color .15s; }
.range-toggle button.on { background: #004D3A; color: #FFFFFF; }
.weight-svg { display: block; height: auto; max-height: 220px; margin-top: 8px; overflow: visible; }

/* screening + lab results row */
.cd-pair { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 22px; align-items: stretch; }
.cd-pair > * { min-width: 0; }
.scr-card { display: flex; flex-direction: column; }
.scr-head { display: flex; align-items: center; gap: 14px; margin-bottom: 18px; }
.scr-head-text { flex: 1; min-width: 0; }
.scr-icon { flex-shrink: 0; width: 48px; height: 48px; border-radius: 14px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; }
.scr-head .stat-pill { gap: 5px; }
.scr-tiles { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-bottom: 18px; }
.scr-tiles div { padding: 12px 14px; border-radius: 14px; border: 1px solid #E8EDEA; background: #FBFCFB; }
.scr-tiles small { display: block; font-size: 11px; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; color: #6B7D73; }
.scr-tiles strong { display: block; margin-top: 4px; font-size: 20px; font-weight: 700; color: #10231B; }
.scr-tiles strong span { font-size: 13px; font-weight: 600; color: #6B7D73; }
.scr-card .block-wide { margin-top: auto; }
.tasks-empty-icon.gold { background: #FBF6E4; color: #9A7300; }


/* ---------- PHONE ONLY BITS (quick access, section titles) ---------- */
.qa,
.m-head { display: none; }
.m-title { margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 700; color: #10231B; }
.m-head { align-items: center; justify-content: space-between; margin-bottom: -4px; }
.m-more { display: inline-flex; align-items: center; gap: 2px; font-size: 13.5px; font-weight: 700; color: #004D3A; text-decoration: none; }
.qa-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px 6px; margin-top: 14px; }
.qa-tile { display: flex; flex-direction: column; align-items: center; gap: 7px; padding: 0; border: none; background: none; font-family: inherit; font-size: 12px; font-weight: 600; color: #22362C; text-align: center; text-decoration: none; cursor: pointer; }
.qa-icon { width: 54px; height: 54px; border-radius: 16px; background: #EEF4F0; color: #004D3A; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 6px 14px -10px rgba(0, 77, 58, 0.5); transition: transform .15s; }
.qa-tile.gold .qa-icon { background: #FBF6E4; color: #9A7300; }
.qa-tile.dark .qa-icon { background: #004D3A; color: #EFBF04; }
.qa-tile:active .qa-icon { transform: scale(.95); }

/* ---------- SMALLER SCREENS ---------- */
@media (max-width: 1100px) {
  .client-dashboard .cd-hero { grid-template-columns: 1fr; }
  .cd-hero-plate { opacity: .25; }
  .stat-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .dash-grid { grid-template-columns: 1fr; }
  .cd-pair { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .client-dashboard { gap: 16px; }
  .client-dashboard .cd-hero { padding: 22px 18px; border-radius: 22px; gap: 18px; }
  .cd-hero-plate, .cd-hero-fade { display: none; }
  .client-dashboard .nm-hero-title { font-size: 26px; }
  .client-dashboard .nm-hero-sub { font-size: 14px; }
  .client-dashboard .nm-upnext { padding: 16px; }
  .up-time { font-size: 32px; }
  .up-time.small { font-size: 22px; }
  .up-empty { flex-direction: column; align-items: stretch; }
  /* the shared `.nm-hero-btn { flex: 1 }` (portal.css, <= 900px) would squash the button; keep it full width */
  .client-dashboard .nm-upnext .up-empty-btn { flex: none; width: 100%; }
  .stat-grid { gap: 10px; }
  .stat-card { padding: 14px; border-radius: 18px; }
  .stat-icon { width: 34px; height: 34px; margin-bottom: 10px; }
  .stat-value { font-size: 26px; }
  .stat-pill { height: 22px; padding: 0 8px; font-size: 11px; }
  .empty-plate { flex-direction: column; align-items: flex-start; }
  .plate-ring { width: 88px; height: 88px; }
  .plate-ring span { inset: 24px; }
  .panel { padding: 18px 16px; border-radius: 18px; }
  .panel-title { font-size: 18px; }
  .adherence-row { grid-template-columns: 1fr; gap: 8px; }
  .macro-source { margin-left: 0; width: 100%; }
  .add-task-row { flex-wrap: wrap; }
  .scr-tiles { gap: 8px; }
  .scr-tiles div { padding: 10px; }
  .scr-tiles strong { font-size: 17px; }
  .add-task .nm-input,
  .add-task .nm-select { font-size: 16px; } /* stops iPhone zoom on tap */
}

/* ---------- PHONE: app layout ---------- */
@media (max-width: 640px) {
  .qa { display: block; }
  .m-head { display: flex; }

  /* the header above already says hi: the banner is the next step only */
  .client-dashboard .cd-hero { display: block; min-height: 190px; padding: 22px 18px; }
  .client-dashboard .nm-hero-greet { display: none; }
  .client-dashboard .cd-hero .cd-hero-plate {
    display: block;
    top: 50%;
    right: -46px;
    width: 190px;
    height: 190px;
    opacity: 1;
    box-shadow: 0 0 0 6px rgba(255, 255, 255, 0.08);
  }
  .client-dashboard .cd-hero .cd-hero-fade { display: none; }
  .client-dashboard .nm-upnext { max-width: 62%; padding: 0; background: none; border: none; -webkit-backdrop-filter: none; backdrop-filter: none; }
  .client-dashboard .nm-upnext .up-time.small { margin: 8px 0 6px; font-size: 26px; line-height: 1.1; }
  .client-dashboard .nm-upnext .up-when { font-size: 13.5px; }
  .client-dashboard .nm-upnext .up-empty { gap: 14px; }
  .client-dashboard .nm-upnext .up-empty-btn { width: auto; align-self: flex-start; height: 42px; padding: 0 18px; border-radius: 999px; }
  .client-dashboard .nm-upnext .up-empty-btn .ic { display: none; }

  /* numbers: label, value, status */
  .stat-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
  .stat-card { gap: 6px; padding: 14px 14px 12px; }
  .stat-card:hover { transform: none; }
  .stat-top,
  .stat-card > div:not(.stat-top):not(.bmi-gauge) { display: contents; }
  .stat-icon,
  .bmi-gauge,
  .stat-card .stat-delta,
  .stat-card .cd-link { display: none; }
  .stat-label { order: 1; margin: 0; font-size: 12.5px; font-weight: 600; color: #5D7065; }
  .stat-value { order: 2; font-size: 26px; }
  .stat-pill { order: 3; align-self: flex-start; height: 24px; font-size: 11.5px; }
}

/* ===== Up next: white card + date block (option B) ===== */
.client-dashboard .nm-upnext.ub-card { padding: 16px !important; max-width: none !important; border: none !important; border-radius: 22px !important; background: #FFFFFF !important; color: #0E3A2C; -webkit-backdrop-filter: none !important; backdrop-filter: none !important; box-shadow: 0 20px 40px -20px rgba(0, 0, 0, 0.5) !important; }
.ub { display: flex; gap: 16px; }
.ub-db { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 72px; flex-shrink: 0; border-radius: 16px; background: #004D3A; color: #FFFFFF; }
.ub-db small { font-size: 11px; font-weight: 800; letter-spacing: 1px; color: #EFBF04; }
.ub-db b { font-family: 'Playfair Display', Georgia, serif; font-size: 30px; line-height: 1; }
.ub-db span { font-size: 11.5px; font-weight: 700; color: #CFE3D8; }
.ub-m { flex: 1; min-width: 0; }
.ub-k { margin: 0 0 8px; font-size: 11.5px; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase; color: #9A7300; }
.ub-k b { color: #0E3A2C; }
.ub-who { display: flex; align-items: center; gap: 10px; }
.ub-av { width: 40px; height: 40px; flex-shrink: 0; border-radius: 50%; object-fit: cover; }
.ub-ini { display: inline-flex; align-items: center; justify-content: center; background: #E3EFE7; color: #004D3A; font-size: 14px; font-weight: 800; }
.ub-name { min-width: 0; flex: 1; }
.ub-name strong { display: block; font-size: 15.5px; color: #0E3A2C; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ub-name small { display: inline-flex; align-items: center; gap: 5px; font-size: 12.5px; color: #4A5A52; }
.ub-name small svg { color: #1F7A4D; }
.ub-pill { display: inline-flex; align-items: center; gap: 4px; flex-shrink: 0; padding: 3px 10px; border-radius: 999px; background: #E3F4EA; color: #1F7A4D; font-size: 12px; font-weight: 800; white-space: nowrap; }
.ub-pill.unpaid, .ub-pill.waiting { background: #FBF3D2; color: #8A6400; }
.ub-acts { display: flex; gap: 8px; margin-top: 12px; }
.ub-btn { display: inline-flex; align-items: center; justify-content: center; gap: 6px; flex: 1; height: 40px; padding: 0 12px; border-radius: 12px; font-size: 13px; font-weight: 800; text-decoration: none; white-space: nowrap; }
.ub-btn.soft { background: #F1F5F2; color: #4A5A52; font-weight: 700; }
.ub-btn.soft svg { color: #9A7300; }
.ub-btn.dark { background: #004D3A; color: #FFFFFF; }
.ub-btn.dark svg { color: #EFBF04; }
.ub-btn.gold { background: #EFBF04; color: #004D3A; }
.ub-btn:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
@media (max-width: 640px) {
  .ub { gap: 12px; }
  .ub-db { width: 60px; }
  .ub-db b { font-size: 24px; }
  .ub-acts { flex-direction: column; }
}

/* Up next card: give it room, keep each line on one row */
.client-dashboard .cd-hero:has(.ub-card) { grid-template-columns: minmax(0, 1fr) minmax(0, 460px); }
.client-dashboard .nm-upnext.ub-card { width: 100%; box-sizing: border-box; }
.ub-name small { display: flex; max-width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ub-name small svg { flex-shrink: 0; }
.ub-btn { min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.ub-btn.soft { flex: 0 1 auto; }
.ub-btn:not(.soft) { flex: 1 1 auto; }
@media (max-width: 1100px) {
  .client-dashboard .cd-hero:has(.ub-card) { grid-template-columns: 1fr; }
}

/* ===== Today's meal plan: photo log timeline ===== */
.mt-k { margin: 0 0 4px; font-size: 12px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; color: #9A7300; }
.mt-log { display: inline-flex; align-items: center; gap: 8px; flex-shrink: 0; height: 42px; padding: 0 16px; border-radius: 12px; background: #004D3A; color: #FFFFFF; font-size: 13.5px; font-weight: 800; text-decoration: none; }
.mt-log svg { color: #EFBF04; }
.mt-log:hover { background: #00684E; }
.panel:has(.mt-tl) .macro-strip { padding: 0 0 16px; border-radius: 0; background: none; border-bottom: 1px solid #EEF2EF; }
.mt-lh { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 14px 0 0; }
.mt-lh p { margin: 0; font-size: 13px; color: #6B7D73; }
.mt-lh b { font-weight: 800; color: #0E3A2C; }
.mt-all { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 14px; border: none; border-radius: 10px; background: #E3EFE7; color: #004D3A; font-family: inherit; font-size: 13px; font-weight: 800; cursor: pointer; }
.mt-all:hover { background: #D3E7DA; }
.mt-all[aria-expanded="true"] svg { transform: rotate(-90deg); }
.mt-all:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
.meal-list.mt-tl { display: flex; flex-direction: column; margin: 0; padding: 0; list-style: none; }
.mt-row { position: relative; display: grid; grid-template-columns: 42px minmax(0, 1fr) 84px; gap: 14px; align-items: center; padding: 14px 0; border: none; }
.mt-row:not(:last-child)::after { content: ''; position: absolute; left: 20px; top: 58px; bottom: -14px; width: 2px; background: #E1EAE4; }
.mt-row.logged:not(:last-child)::after { background: #9CC9AE; }
.mt-ic { position: relative; z-index: 1; align-self: start; margin-top: 2px; width: 42px; height: 42px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: #F1F5F2; color: #6B7D73; border: 3px solid #FFFFFF; box-sizing: border-box; }
.mt-row.logged .mt-ic { background: #1F7A4D; color: #FFFFFF; }
.mt-row.now .mt-ic { background: #EFBF04; color: #004D3A; box-shadow: 0 0 0 4px rgba(239, 191, 4, 0.2); }
.mt-m { min-width: 0; }
.mt-t { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 0; font-size: 12.5px; font-weight: 800; color: #9A7300; }
.mt-st { display: inline-flex; align-items: center; gap: 4px; padding: 2px 9px; border-radius: 999px; font-size: 11.5px; font-weight: 800; }
.mt-st.pill-green { background: #E3F4EA; color: #1F7A4D; }
.mt-st.pill-gold { background: #FBF3D2; color: #8A6400; }
.mt-st.badge-danger { background: #FDECEC; color: #B4384A; }
.mt-st.pill-muted { background: #F1F5F2; color: #6B7D73; }
.mt-st.now { background: #004D3A; color: #EFBF04; }
.mt-st.later { background: #F1F5F2; color: #6B7D73; }
.mt-n { margin: 3px 0 6px; font-size: 16px; font-weight: 800; color: #0E3A2C; }
.mt-f { display: flex; flex-wrap: wrap; gap: 6px; }
.mt-f span { padding: 3px 10px; border-radius: 999px; background: #F4F7F5; font-size: 12.5px; color: #3E5046; }
.mt-f span.none { background: none; padding: 0; color: #8A9A91; }
.mt-ph { position: relative; width: 84px; height: 84px; border-radius: 16px; overflow: hidden; box-sizing: border-box; }
.mt-ph.done img { width: 100%; height: 100%; object-fit: cover; display: block; }
.mt-nophoto { width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #E3F4EA; color: #1F7A4D; }
.mt-ph.done i { position: absolute; right: 6px; bottom: 6px; width: 22px; height: 22px; border-radius: 50%; background: #1F7A4D; color: #FFFFFF; border: 2px solid #FFFFFF; display: inline-flex; align-items: center; justify-content: center; }
.mt-ph.add { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; border: 1.5px dashed #C6D3CB; background: #FAFCFB; color: #6B7D73; font-size: 11.5px; text-decoration: none; }
.mt-ph.add b { font-weight: 800; }
.mt-ph.add:hover { border-color: #004D3A; color: #004D3A; }
.mt-ph.add.now { border: 2px dashed #EFBF04; background: #FDF9E8; color: #8A6400; }
.mt-ph.add:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
.mt-pg { margin: 0 0 8px; font-size: 13.5px; color: #4A5A52; }
.mt-pg b { color: #0E3A2C; }
.mt-bar { height: 8px; border-radius: 999px; background: #EEF2EF; overflow: hidden; }
.mt-bar i { display: block; height: 100%; border-radius: 999px; background: #1F7A4D; }
@media (max-width: 640px) {
  .mt-log { width: 100%; justify-content: center; }
  .mt-row { grid-template-columns: 38px minmax(0, 1fr) 68px; gap: 10px; }
  .mt-ic { width: 38px; height: 38px; }
  .mt-row:not(:last-child)::after { left: 18px; }
  .mt-ph { width: 68px; height: 68px; }
}

/* ===== Recent activity: timeline, grouped by day ===== */
.ra-k { display: flex; align-items: center; gap: 7px; margin: 0 0 4px; font-size: 12px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; color: #9A7300; }
.ra-all { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 14px; border-radius: 10px; background: #E3EFE7; color: #004D3A; font-size: 13px; font-weight: 800; text-decoration: none; }
.ra-all:hover { background: #D3E7DA; }
.ra-day { display: flex; align-items: center; gap: 8px; margin: 16px 0 4px; font-size: 13px; font-weight: 800; color: #0E3A2C; }
.ra-day span { padding: 2px 9px; border-radius: 999px; background: #FBF3D2; color: #8A6400; font-size: 11.5px; }
.ra-list { display: flex; flex-direction: column; }
.ra-row { position: relative; display: grid; grid-template-columns: 42px minmax(0, 1fr) auto 20px; gap: 14px; align-items: center; padding: 12px 10px 12px 0; border-radius: 14px; text-decoration: none; color: inherit; }
.ra-row:hover { background: #F7FAF8; }
.ra-row:not(:last-child)::after { content: ''; position: absolute; left: 20px; top: 56px; bottom: -12px; width: 2px; background: #E1EAE4; }
.ra-ic { position: relative; z-index: 1; width: 42px; height: 42px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; border: 3px solid #FFFFFF; box-sizing: border-box; }
.ra-ic.gold { background: #FBF3D2; color: #9A7300; }
.ra-ic.green { background: #DDEFE4; color: #1F7A4D; }
.ra-ic.orange { background: #FDEBD9; color: #B8621B; }
.ra-ic.blue { background: #E6ECF8; color: #3B5BA5; }
.ra-ic.purple { background: #ECE8F8; color: #5A4FA8; }
.ra-m { display: flex; flex-direction: column; min-width: 0; }
.ra-t { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 800; color: #0E3A2C; }
.ra-cnt { padding: 1px 8px; border-radius: 999px; background: #E3EFE7; color: #004D3A; font-size: 11.5px; font-weight: 800; }
.ra-s { margin-top: 2px; font-size: 13px; color: #4A5A52; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ra-g { margin-top: 2px; font-size: 12px; color: #8A9A91; }
.ra-dot { width: 9px; height: 9px; border-radius: 50%; background: #EFBF04; box-shadow: 0 0 0 3px rgba(239, 191, 4, 0.2); }
.ra-go { color: #9AAAA1; display: inline-flex; }
.ra-row:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
@media (max-width: 640px) {
  .ra-row { grid-template-columns: 38px minmax(0, 1fr) auto; gap: 10px; }
  .ra-ic { width: 38px; height: 38px; }
  .ra-row:not(:last-child)::after { left: 18px; }
  .ra-go { display: none; }
}

/* ===== Your RND card ===== */
.panel.rnd-compact:not(.empty) { display: flex; align-items: center; gap: 16px; padding: 18px 20px; }
.yr-av { position: relative; flex-shrink: 0; width: 58px; height: 58px; border-radius: 50%; padding: 3px; background: #FFFFFF; box-shadow: 0 0 0 2.5px #EFBF04; box-sizing: border-box; }
.yr-av img, .yr-av span { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; display: flex; align-items: center; justify-content: center; }
.yr-av span { background: #004D3A; color: #EFBF04; font-size: 18px; font-weight: 800; }
.yr-av i { position: absolute; right: -2px; bottom: -2px; width: 20px; height: 20px; border-radius: 50%; background: #1F7A4D; color: #FFFFFF; border: 2px solid #FFFFFF; display: inline-flex; align-items: center; justify-content: center; box-sizing: border-box; }
.yr-m { flex: 1; min-width: 0; }
.yr-k { display: flex; align-items: center; gap: 6px; margin: 0; font-size: 11.5px; font-weight: 800; letter-spacing: 1.3px; text-transform: uppercase; color: #9A7300; }
.yr-name { margin: 2px 0 6px; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; font-weight: 700; color: #0E3A2C; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.yr-s { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin: 0; }
.yr-spec { padding: 3px 10px; border-radius: 999px; background: #E3EFE7; color: #004D3A; font-size: 12.5px; font-weight: 700; }
.yr-rate { display: inline-flex; align-items: center; gap: 4px; font-size: 12.5px; color: #4A5A52; }
.yr-rate b { color: #0E3A2C; }
.yr-a { display: flex; gap: 8px; flex-shrink: 0; }
.yr-btn { display: inline-flex; align-items: center; gap: 7px; height: 40px; padding: 0 14px; border-radius: 12px; font-size: 13px; font-weight: 800; text-decoration: none; }
.yr-btn.dark { background: #004D3A; color: #FFFFFF; }
.yr-btn.dark svg { color: #EFBF04; }
.yr-btn.soft { background: #E3EFE7; color: #004D3A; }
.yr-btn:hover { filter: brightness(1.05); }
.yr-btn:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
@media (max-width: 640px) {
  .panel.rnd-compact:not(.empty) { flex-wrap: wrap; padding: 16px; }
  .yr-a { width: 100%; }
  .yr-btn { flex: 1; justify-content: center; }
}

/* ===== My tasks: progress ring + timeline ===== */
.tk-head { display: flex; align-items: center; gap: 16px; }
.tk-ring { --p: 0; position: relative; width: 62px; height: 62px; flex-shrink: 0; border-radius: 50%; background: conic-gradient(#1F7A4D calc(var(--p) * 1%), #EEF2EF 0); display: flex; align-items: center; justify-content: center; }
.tk-ring::before { content: ''; position: absolute; inset: 7px; border-radius: 50%; background: #FFFFFF; }
.tk-ring b { position: relative; font-family: 'Playfair Display', Georgia, serif; font-size: 21px; color: #0E3A2C; }
.tk-ring small { font-family: inherit; font-size: 12px; font-weight: 700; color: #6B7D73; }
.tk-k { display: flex; align-items: center; gap: 7px; margin: 0 0 2px; font-size: 12px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; color: #9A7300; }
.tk-add { display: inline-flex; align-items: center; gap: 7px; flex-shrink: 0; height: 40px; padding: 0 14px; border: none; border-radius: 12px; background: #004D3A; color: #FFFFFF; font-family: inherit; font-size: 13px; font-weight: 800; cursor: pointer; }
.tk-add svg { color: #EFBF04; }
.tk-add:focus-visible, .tk-all:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
.tk-lh { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin: 16px 0 4px; padding-top: 14px; border-top: 1px solid #EEF2EF; }
.tk-lh p { margin: 0; font-size: 13px; color: #6B7D73; }
.tk-lh b { font-weight: 800; color: #0E3A2C; }
.tk-all { display: inline-flex; align-items: center; gap: 6px; height: 36px; padding: 0 14px; border: none; border-radius: 10px; background: #E3EFE7; color: #004D3A; font-family: inherit; font-size: 13px; font-weight: 800; cursor: pointer; }
.tk-all[aria-expanded="true"] svg { transform: rotate(-90deg); }
.tk-list { display: flex; flex-direction: column; }
.today-row.tk-row { position: relative; display: grid; grid-template-columns: 70px 34px minmax(0, 1fr) auto; gap: 12px; align-items: start; padding: 12px 0; border: none; background: none; }
.tk-row:not(:last-child)::after { content: ''; position: absolute; left: 98px; top: 46px; bottom: -12px; width: 2px; background: #E1EAE4; }
.tk-row.done:not(:last-child)::after { background: #9CC9AE; }
.tk-time { padding-top: 7px; text-align: right; font-size: 13px; font-weight: 800; color: #9A7300; white-space: nowrap; }
.tk-row.done .tk-time { color: #A9B6AE; }
.tk-cb { position: relative; z-index: 1; width: 34px !important; height: 34px !important; margin: 0 !important; border-radius: 50% !important; box-sizing: border-box; }
input.tk-cb { appearance: none; -webkit-appearance: none; border: 2px solid #C6D3CB; background: #FFFFFF; cursor: pointer; }
input.tk-cb:checked { border: none; background: #1F7A4D url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 12.5l4.5 4.5L19 7.5'/%3E%3C/svg%3E") center / 15px no-repeat; }
input.tk-cb:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
span.tk-cb.meal { display: inline-flex; align-items: center; justify-content: center; border: 2px solid #C6D3CB; background: #FFFFFF; }
span.tk-cb.meal.on { border: none; background: #1F7A4D; color: #FFFFFF; }
.tk-ico { display: inline-flex; align-items: center; justify-content: center; border: none; background: #004D3A; color: #EFBF04; box-shadow: 0 0 0 4px rgba(239, 191, 4, 0.25); }
.tk-m { display: flex; flex-direction: column; min-width: 0; padding-top: 2px; }
.tk-row .today-title { font-size: 15.5px; font-weight: 800; color: #0E3A2C; }
.tk-row.done .today-title { color: #8A9A91; text-decoration: line-through; }
.tk-s { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
.tk-s .today-detail { font-size: 12.5px; color: #6B7D73; }
.tk-kd { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px; font-size: 11.5px; font-weight: 800; background: #F1F5F2; color: #4A5A52; }
.tk-kd.meal { background: #FDEBD9; color: #B8621B; }
.tk-kd.appointment { background: #FBF3D2; color: #8A6400; }
.tk-kd.rem, .tk-kd.reminder { background: #DFF0FB; color: #1F6FA8; }
.tk-kd.own { background: #E3EFE7; color: #004D3A; }
.tk-kd.lab { background: #ECE8F8; color: #5A4FA8; }
.tk-note { display: block; margin-top: 8px; padding: 8px 12px; border: none !important; border-radius: 10px; background: #F4F8F5 !important; font-size: 13px; font-style: italic; color: #22362C; }
@media (max-width: 640px) {
  .tk-head { flex-wrap: wrap; }
  .tk-add { width: 100%; justify-content: center; }
  .today-row.tk-row { grid-template-columns: 34px minmax(0, 1fr) auto; }
  .tk-time { grid-column: 2; grid-row: 1; text-align: left; padding: 0; }
  .tk-cb { grid-column: 1; grid-row: 1 / 3; }
  .tk-m { grid-column: 2; }
  .tk-row:not(:last-child)::after { left: 16px; }
}

/* ===== Your screening: no tiles, round icons ===== */
.sx-h { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.sx-k { display: flex; align-items: center; gap: 7px; margin: 0 0 4px; font-size: 12px; font-weight: 800; letter-spacing: 1.4px; text-transform: uppercase; color: #9A7300; }
.sx-figs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 22px; }
.sx-f { display: flex; align-items: center; gap: 12px; min-width: 0; }
.sx-i { width: 46px; height: 46px; flex-shrink: 0; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; background: #E3EFE7; color: #004D3A; }
.sx-f small { display: block; font-size: 12.5px; font-weight: 700; color: #6B7D73; }
.sx-f b { display: inline-flex; align-items: baseline; flex-wrap: wrap; font-family: 'Playfair Display', Georgia, serif; font-size: 28px; line-height: 1.1; color: #0E3A2C; }
.sx-f em { margin-left: 3px; font-family: inherit; font-style: normal; font-size: 13px; font-weight: 700; color: #6B7D73; }
.sx-pill { align-self: center; margin-left: 8px; padding: 2px 9px; border-radius: 999px; background: #F1F5F2; color: #3E5046; font-family: 'DM Sans', sans-serif; font-size: 11.5px; font-weight: 800; }
.sx-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 22px; padding-top: 16px; border-top: 1px solid #EEF2EF; }
.sx-foot p { margin: 0; font-size: 13px; color: #6B7D73; }
.sx-btn { display: inline-flex; align-items: center; gap: 7px; flex-shrink: 0; height: 42px; padding: 0 18px; border: none; border-radius: 12px; background: #004D3A; color: #FFFFFF; font-family: inherit; font-size: 13.5px; font-weight: 800; cursor: pointer; }
.sx-btn svg { color: #EFBF04; }
.sx-btn:hover { background: #00684E; }
.sx-btn:focus-visible { outline: 2px solid #1F8F5C; outline-offset: 2px; }
@media (max-width: 640px) {
  .sx-figs { grid-template-columns: 1fr; gap: 14px; }
  .sx-foot { flex-direction: column; align-items: stretch; }
  .sx-btn { justify-content: center; }
}

/* Screening card lines up with the Weight progress card above (same columns as .dash-grid) */
.cd-pair { grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 22px; }
@media (max-width: 1100px) { .cd-pair { grid-template-columns: 1fr; } }

/* ===== Mobile fixes for the redesigned cards ===== */
@media (max-width: 640px) {
  /* My tasks: ring + title side by side, button full width under them */
  .panel-header-row:has(.tk-add) { flex-direction: column; align-items: stretch; gap: 14px; }
  .panel-header-row:has(.tk-add) > div { min-width: 0; }
  .tk-head { flex-wrap: nowrap !important; align-items: center; gap: 14px; }
  .tk-head > div:last-child { flex: 1; min-width: 0; }
  .tk-ring { width: 54px; height: 54px; }
  .tk-ring b { font-size: 18px; }
  .tk-add { width: 100%; justify-content: center; }
  .tk-lh { flex-wrap: wrap; }
  /* Today's meal plan / Recent activity headers: button under the title */
  .panel-header-row:has(.mt-log) { flex-direction: column; align-items: stretch; gap: 12px; }
  .mt-log { width: 100%; justify-content: center; }
  .mt-lh { flex-wrap: wrap; }
  .panel-header-row:has(.ra-all) { align-items: center; }
  /* Your RND: avatar + name on one row, buttons under */
  .panel.rnd-compact:not(.empty) .yr-m { flex: 1 1 calc(100% - 74px); }
  .yr-name { font-size: 19px; white-space: normal; }
  /* Up next card: full width, smaller date block */
  .client-dashboard .nm-upnext.ub-card { padding: 14px !important; }
  .ub-name strong { white-space: normal; }
  /* Screening figures: two per row on phones */
  .sx-figs { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .sx-f b { font-size: 24px; }
}

/* date block: compact square, not stretched to the card height */
.ub-db { align-self: flex-start; width: 64px !important; height: 68px; padding: 0; border-radius: 14px; }
.ub-db b { font-size: 24px !important; }
.ub-db small, .ub-db span { font-size: 10.5px !important; }
@media (max-width: 640px) { .ub-db { width: 56px !important; height: 60px; } .ub-db b { font-size: 21px !important; } }

/* Phone: no big green date block; the date is already in the line under the name */
@media (max-width: 640px) {
  .client-dashboard .ub-db { display: none !important; }
  .client-dashboard .ub-name small { white-space: normal; }
  .client-dashboard .ub-acts { flex-direction: column; }
}

/* Phone: full-width card, proper button height (flex:1 squashed them in a column) */
@media (max-width: 640px) {
  .client-dashboard .nm-upnext.ub-card { width: 100% !important; max-width: none !important; box-sizing: border-box; }
  .ub-acts { gap: 8px; }
  .ub-acts .ub-btn { flex: 0 0 auto !important; width: 100%; height: 46px !important; min-height: 46px; font-size: 14px; }
}

/* screening + lab results now sit in the two columns (no tall empty card, no big gap) */
.dash-col > .scr-card { margin-top: 0; }
</style>