<template>
  <div class="profile-page">
    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <p v-if="isLoading" class="placeholder-text">Loading…</p>

    <template v-else-if="rnd">
      <p class="breadcrumb"><NuxtLink to="/find-rnd">Find an RND</NuxtLink> / RND {{ rnd.user.first_name }} {{ rnd.user.last_name }}</p>

      <div class="profile-banner">
        <div class="big-avatar" :style="{ background: colorForId(rnd.user.id) }">{{ initialsFor(rnd.user) }}</div>
        <div class="banner-info">
          <h1 class="banner-name">RND {{ rnd.user.first_name }} {{ rnd.user.last_name }} <BadgeCheck :size="18" class="verified-icon" /></h1>
          <p class="banner-specialty">{{ rnd.specialization || 'General Practice' }} · PRC License #{{ rnd.prc_license_number }}</p>
          <div class="banner-chips">
            <span v-if="rnd.average_rating" class="chip chip-gold">★ {{ rnd.average_rating.toFixed(1) }} ({{ rnd.review_count }} review{{ rnd.review_count === 1 ? '' : 's' }})</span>
            <span v-if="rnd.languages.length" class="chip"><Languages :size="13" /> {{ rnd.languages.map(l => l.language_name).join(' · ') }}</span>
          </div>
        </div>
        <div class="banner-fee">
          <div class="fee-amount">₱{{ rnd.consultation_fee }}</div>
          <div class="fee-unit">per session</div>
        </div>
      </div>

      <div class="content-grid">
        <div class="main-col">
          <div class="surface">
            <h3 class="surface-title">About</h3>
            <p class="bio-text">{{ rnd.bio || 'This RND has not added a bio yet.' }}</p>
          </div>

          <div class="surface">
            <div class="reviews-header">
              <h3 class="surface-title">Patient Reviews</h3>
              <span v-if="rnd.average_rating" class="chip chip-gold">★ {{ rnd.average_rating.toFixed(1) }} average</span>
            </div>
            <div v-if="isLoadingReviews" class="placeholder-text">Loading reviews…</div>
            <div v-else-if="reviews.length" class="review-list">
              <div v-for="review in reviews" :key="review.id" class="review-row">
                <div class="review-top">
                  <span class="review-name">{{ review.client_name }}</span>
                  <span class="review-stars">{{ '★'.repeat(review.rating) }}{{ '☆'.repeat(5 - review.rating) }}</span>
                </div>
                <p v-if="review.comment" class="review-comment">"{{ review.comment }}"</p>
              </div>
            </div>
            <p v-else class="empty-note">No reviews yet.</p>
          </div>
        </div>

        <div class="sidebar-col">
          <div class="surface sticky-card">
            <h3 class="surface-title">Start Your Care Journey</h3>
            <p class="sidebar-desc">
              {{ relationshipStatus === 'active'
                ? "You're already connected — head to Appointments to book a session."
                : `Send a relationship request to RND ${rnd.user.first_name} ${rnd.user.last_name}. Once accepted, you can book your first appointment.` }}
            </p>

            <NuxtLink v-if="relationshipStatus === 'active'" :to="`/book-appointment?rnd=${rnd.user.id}`" class="primary-btn">Book Appointment</NuxtLink>
            <button v-else class="primary-btn" type="button" :disabled="relationshipStatus === 'pending' || isRequesting" @click="requestRelationship">
              {{ requestButtonLabel }}
            </button>

            <NuxtLink to="/messages" class="outline-btn">Message First</NuxtLink>

            <div class="info-note">
              <Info :size="15" />
              <span>Pre-consultation screening is required before your first appointment can be confirmed.</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { BadgeCheck, Languages, Info } from 'lucide-vue-next'

const route = useRoute()
const { get, post } = useApi()

const isLoading = ref(true)
const isLoadingReviews = ref(true)
const errorMessage = ref('')
const rnd = ref(null)
const reviews = ref([])
const relationshipStatus = ref(null)
const isRequesting = ref(false)

const AVATAR_COLORS = ['#1e4a26', '#3a6b3a', '#D4A017', '#6a8a6a', '#8a6a3a']
function colorForId(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}
function initialsFor(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
}

const requestButtonLabel = computed(() => {
  if (isRequesting.value) return 'Sending…'
  if (relationshipStatus.value === 'pending') return 'Request Sent'
  return 'Request to Connect'
})

async function loadProfile() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const rndId = route.params.id
    const [profile, relationships] = await Promise.all([
      get(`/client/rnds/${rndId}/`),
      get('/client/relationships/').catch(() => []),
    ])
    rnd.value = profile
    const existing = relationships.find(r => r.rnd.id === Number(rndId))
    relationshipStatus.value = existing?.status || null
  } catch {
    errorMessage.value = 'Could not load this RND profile. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

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

async function requestRelationship() {
  isRequesting.value = true
  try {
    await post(`/client/rnds/${route.params.id}/request/`)
    relationshipStatus.value = 'pending'
  } catch (error) {
    errorMessage.value = error?.data?.detail || 'Could not send request. Please try again.'
  } finally {
    isRequesting.value = false
  }
}

onMounted(() => {
  loadProfile()
  loadReviews()
})
</script>

<style scoped>
* { box-sizing: border-box; }

.profile-page { font-family: 'Inter', sans-serif; }

.breadcrumb { font-size: 0.8rem; color: #8a9a8a; margin: 0 0 14px; }
.breadcrumb :deep(a) { color: #3a6b3a; text-decoration: none; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.profile-banner {
  background: #14301a; border-radius: 14px; padding: 28px 32px; color: #fff;
  display: flex; align-items: center; gap: 20px; margin-bottom: 20px; flex-wrap: wrap;
}
.big-avatar {
  width: 76px; height: 76px; border-radius: 50%; color: #fff; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1.4rem;
}
.banner-info { flex: 1; min-width: 200px; }
.banner-name { font-family: 'Playfair Display', serif; font-size: 1.4rem; margin: 0; display: flex; align-items: center; gap: 8px; }
.verified-icon { color: #D4A017; }
.banner-specialty { font-size: 0.85rem; color: #c9d9c9; margin: 6px 0 10px; }
.banner-chips { display: flex; gap: 8px; flex-wrap: wrap; }
.chip {
  font-size: 0.74rem; font-weight: 600; padding: 4px 11px; border-radius: 20px;
  background: rgba(255,255,255,0.12); color: #fff; display: inline-flex; align-items: center; gap: 5px;
}
.chip-gold { background: #D4A017; color: #1a3a1a; }
.banner-fee { text-align: right; }
.fee-amount { font-size: 1.4rem; font-weight: 700; }
.fee-unit { font-size: 0.72rem; color: #a9c0a9; }

.content-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; align-items: start; }
@media (max-width: 900px) { .content-grid { grid-template-columns: 1fr; } }

.main-col { display: flex; flex-direction: column; gap: 16px; }
.surface { background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px 22px; }
.surface-title { font-family: 'Playfair Display', serif; font-size: 1.05rem; color: #1a3a1a; margin: 0 0 12px; }

.bio-text { font-size: 0.87rem; color: #4a5a4a; line-height: 1.6; margin: 0; }

.reviews-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.review-list { margin-top: 8px; }
.review-row { padding: 14px 0; border-bottom: 1px solid #f0f0e6; }
.review-row:last-child { border-bottom: none; }
.review-top { display: flex; justify-content: space-between; margin-bottom: 4px; }
.review-name { font-weight: 700; font-size: 0.87rem; color: #1a3a1a; }
.review-stars { color: #D4A017; font-size: 0.8rem; }
.review-comment { font-size: 0.85rem; color: #6a7a6a; margin: 0; }
.empty-note { font-size: 0.85rem; color: #9aaa9a; margin: 0; }

.sidebar-col { position: sticky; top: 20px; }
.sticky-card { display: flex; flex-direction: column; }
.sidebar-desc { font-size: 0.84rem; color: #6a7a6a; margin: 0 0 16px; line-height: 1.5; }

.primary-btn {
  display: block; width: 100%; text-align: center; text-decoration: none; border: none;
  background: #D4A017; color: #1a3a1a; border-radius: 8px; padding: 12px;
  font-weight: 700; font-size: 0.88rem; cursor: pointer; margin-bottom: 10px;
}
.primary-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.outline-btn {
  display: block; text-align: center; text-decoration: none; border: 1px solid #d5dad5;
  background: #fff; color: #1a3a1a; border-radius: 8px; padding: 12px;
  font-weight: 600; font-size: 0.88rem;
}

.info-note {
  display: flex; align-items: flex-start; gap: 8px; margin-top: 16px;
  background: #e3edf7; color: #2f6fa8; border-radius: 8px; padding: 10px 12px; font-size: 0.78rem;
}
</style>
