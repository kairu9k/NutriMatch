<template>
  <div class="reviews-page">
    <div class="page-header">
      <h1 class="page-title">My Reviews</h1>
      <p class="page-sub">Feedback you've left for your RNDs after completed consultations.</p>
    </div>

    <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
    <div v-if="isLoading" class="placeholder-text">Loading…</div>

    <div v-else-if="reviews.length" class="review-list">
      <div v-for="review in reviews" :key="review.id" class="review-card">
        <div class="review-top">
          <div class="review-who">
            <div class="review-avatar" :style="{ background: colorFor(review.rnd.id) }">{{ initialsFor(review.rnd) }}</div>
            <div>
              <p class="review-name">RND {{ review.rnd.first_name }} {{ review.rnd.last_name }}</p>
              <div class="stars-row">
                <Star
                  v-for="n in 5"
                  :key="n"
                  :size="13"
                  :fill="n <= review.rating ? '#D4A017' : 'none'"
                  :color="n <= review.rating ? '#D4A017' : '#d5dad5'"
                  :stroke-width="1.5"
                />
              </div>
            </div>
          </div>
          <span class="review-time">{{ formatDate(review.created_at) }}</span>
        </div>
        <p v-if="review.comment" class="review-comment">"{{ review.comment }}"</p>
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon"><Star :size="28" /></div>
      <p class="empty-title">No reviews yet</p>
      <p class="empty-desc">After a completed consultation, you can rate your RND from the Appointments page — your reviews will show up here.</p>
    </div>
  </div>
</template>

<script setup>
import { Star } from 'lucide-vue-next'

definePageMeta({ layout: 'dashboard', title: 'Reviews' })

const { get } = useApi()

const isLoading = ref(true)
const errorMessage = ref('')
const reviews = ref([])

const AVATAR_COLORS = ['#1a3a1a', '#D4A017', '#3a6b3a', '#8a5a2a', '#5a3a8a']
function colorFor(id) {
  return AVATAR_COLORS[id % AVATAR_COLORS.length]
}
function initialsFor(user) {
  return `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase()
}
function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function loadReviews() {
  isLoading.value = true
  errorMessage.value = ''
  try {
    reviews.value = await get('/client/reviews/')
  } catch {
    errorMessage.value = 'Could not load your reviews. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadReviews)
</script>

<style scoped>
* { box-sizing: border-box; }

.reviews-page { font-family: 'Inter', sans-serif; }

.page-header { margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}
.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.review-list { display: flex; flex-direction: column; gap: 16px; }
.review-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 18px 22px;
}
.review-top { display: flex; align-items: flex-start; justify-content: space-between; }
.review-who { display: flex; align-items: flex-start; gap: 12px; }
.review-avatar {
  width: 36px; height: 36px; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700; flex-shrink: 0;
}
.review-name { font-size: 0.92rem; font-weight: 700; color: #1a3a1a; margin: 0 0 4px; }
.stars-row { display: flex; gap: 3px; }
.review-time { font-size: 0.78rem; color: #9aaa9a; white-space: nowrap; }
.review-comment { font-size: 0.85rem; color: #4a5a4a; line-height: 1.55; margin: 12px 0 0 48px; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; max-width: 400px; margin-left: auto; margin-right: auto; }
</style>
