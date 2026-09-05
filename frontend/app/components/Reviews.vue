<template>
  <div class="reviews-page">
    <div class="page-header">
      <h1 class="page-title">Patient Reviews</h1>
      <p class="page-sub">See what your patients are saying about their care.</p>
    </div>

    <!-- SUMMARY -->
    <div v-if="reviews.length" class="summary-row">
      <div class="score-card">
        <p class="score-number">{{ summary.average.toFixed(1) }}</p>
        <div class="stars-row">
          <Star
            v-for="n in 5"
            :key="n"
            :size="18"
            :fill="n <= Math.round(summary.average) ? '#D4A017' : 'none'"
            :color="n <= Math.round(summary.average) ? '#D4A017' : '#d5dad5'"
            :stroke-width="1.5"
          />
        </div>
        <p class="score-caption">Based on {{ summary.total }} reviews</p>
      </div>

      <div class="breakdown-card">
        <div v-for="row in ratingBreakdown" :key="row.stars" class="breakdown-row">
          <span class="breakdown-label">{{ row.stars }} star{{ row.stars !== 1 ? 's' : '' }}</span>
          <div class="breakdown-track">
            <div
              class="breakdown-fill"
              :style="{ width: maxCount ? `${(row.count / maxCount) * 100}%` : '0%' }"
            />
          </div>
          <span class="breakdown-count">{{ row.count }}</span>
        </div>
      </div>
    </div>

    <!-- REVIEW LIST -->
    <div v-if="reviews.length" class="review-list">
      <div v-for="review in reviews" :key="review.id" class="review-card">
        <div class="review-top">
          <div class="review-who">
            <div class="review-avatar" :style="{ background: review.avatarColor }">{{ review.initials }}</div>
            <div>
              <p class="review-name">{{ review.name }}</p>
              <div class="stars-row stars-row-sm">
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
          <span class="review-time">{{ review.postedAt }}</span>
        </div>
        <p class="review-comment">"{{ review.comment }}"</p>
      </div>
    </div>

    <!-- EMPTY STATE: no reviews yet -->
    <div v-else class="empty-state">
      <div class="empty-icon"><Star :size="28" /></div>
      <p class="empty-title">No reviews yet</p>
      <p class="empty-desc">Once patients rate their consultations, their feedback will show up here.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Star } from 'lucide-vue-next'
import { db } from '~/mock/mockDatabase'

const summary = ref(db.reviewsSummary)
const ratingBreakdown = ref(db.ratingBreakdown)
const reviews = ref(db.reviews)

const maxCount = computed(() => Math.max(0, ...ratingBreakdown.value.map(r => r.count)))
</script>

<style scoped>
* { box-sizing: border-box; }

.reviews-page { font-family: 'Inter', sans-serif; }

.page-header { margin-bottom: 20px; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

/* SUMMARY */
.summary-row { display: grid; grid-template-columns: 260px 1fr; gap: 16px; margin-bottom: 24px; }

.score-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 24px; display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.score-number { font-family: 'Playfair Display', serif; font-size: 2.4rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.stars-row { display: flex; gap: 3px; margin-top: 6px; }
.stars-row-sm { margin-top: 2px; }
.score-caption { font-size: 0.8rem; color: #8a9a8a; margin: 8px 0 0; }

.breakdown-card {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 22px 26px; display: flex; flex-direction: column; justify-content: center; gap: 10px;
}
.breakdown-row { display: flex; align-items: center; gap: 10px; }
.breakdown-label { width: 46px; font-size: 0.8rem; color: #4a5a4a; }
.breakdown-track { flex: 1; height: 8px; border-radius: 999px; background: #eceeec; overflow: hidden; }
.breakdown-fill { height: 100%; background: #D4A017; border-radius: 999px; }
.breakdown-count { width: 20px; text-align: right; font-size: 0.8rem; color: #8a9a8a; }

/* REVIEW LIST */
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
.review-time { font-size: 0.78rem; color: #9aaa9a; white-space: nowrap; }
.review-comment { font-size: 0.85rem; color: #4a5a4a; line-height: 1.55; margin: 12px 0 0 48px; }

/* EMPTY STATE */
.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-icon {
  width: 56px; height: 56px; border-radius: 50%; background: #eef3ec; color: #1e4a26;
  display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
</style>