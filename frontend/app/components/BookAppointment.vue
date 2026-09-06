<template>
  <div class="book-page">
    <div class="page-header">
      <p class="breadcrumb"><NuxtLink to="/appointments">Appointments</NuxtLink> / Book Appointment</p>
      <h1 class="page-title">Book an Appointment</h1>
      <p class="page-sub">Schedule a consultation with an RND you're actively working with.</p>
    </div>

    <p v-if="loadError" class="form-error">{{ loadError }}</p>

    <p v-if="isLoading" class="placeholder-text">Loading…</p>

    <template v-else-if="!relationships.length">
      <div class="empty-state">
        <p class="empty-title">No active RND relationship yet</p>
        <p class="empty-desc">
          You need an RND to accept your request before you can book a session.
          <NuxtLink to="/find-rnd">Find an RND</NuxtLink> to get started.
        </p>
      </div>
    </template>

    <template v-else>
      <div class="surface mb-3">
        <label class="field-label">Select RND</label>
        <select v-model="selectedRndId" class="field-input">
          <option v-for="rel in relationships" :key="rel.id" :value="rel.rnd.id">
            RND {{ rel.rnd.first_name }} {{ rel.rnd.last_name }}
          </option>
        </select>
      </div>

      <div class="surface mb-3">
        <div class="eyebrow">CONSULTATION TYPE</div>
        <div class="modality-row">
          <button
            v-for="opt in typeOptions"
            :key="opt.value"
            type="button"
            class="modality-option"
            :class="{ selected: type === opt.value }"
            @click="type = opt.value"
          >
            <component :is="opt.icon" :size="20" />
            <span>{{ opt.label }}</span>
          </button>
        </div>

        <div class="eyebrow">DATE & TIME</div>
        <input v-model="scheduledAt" type="datetime-local" class="field-input" :min="minDateTime" />

        <div class="eyebrow">DURATION</div>
        <select v-model.number="durationMinutes" class="field-input duration-select">
          <option :value="30">30 minutes</option>
          <option :value="60">60 minutes</option>
          <option :value="90">90 minutes</option>
        </select>

        <label class="field-label">Notes for your RND <span class="optional">(optional)</span></label>
        <textarea v-model="notes" class="field-input" rows="3" placeholder="Anything you'd like your RND to know before the session..."></textarea>
      </div>

      <p v-if="submitError" class="form-error">{{ submitError }}</p>

      <button class="submit-btn" type="button" :disabled="!canSubmit || isSubmitting" @click="submitBooking">
        {{ isSubmitting ? 'Booking…' : 'Confirm Booking' }}
      </button>
      <p class="submit-note">You'll be asked to pay after your RND confirms the appointment.</p>
    </template>
  </div>
</template>

<script setup>
import { Video, MessageSquare, MapPin } from 'lucide-vue-next'

const { get, post } = useApi()
const route = useRoute()

const isLoading = ref(true)
const loadError = ref('')
const relationships = ref([])

const selectedRndId = ref(null)
const type = ref('video')
const scheduledAt = ref('')
const durationMinutes = ref(60)
const notes = ref('')

const isSubmitting = ref(false)
const submitError = ref('')

const typeOptions = [
  { value: 'video', label: 'Video', icon: Video },
  { value: 'chat', label: 'Chat', icon: MessageSquare },
  { value: 'in_person', label: 'In-Person', icon: MapPin },
]

const minDateTime = computed(() => {
  const now = new Date(Date.now() - new Date().getTimezoneOffset() * 60000)
  return now.toISOString().slice(0, 16)
})

const canSubmit = computed(() => selectedRndId.value && scheduledAt.value)

async function loadRelationships() {
  isLoading.value = true
  loadError.value = ''
  try {
    relationships.value = await get('/client/relationships/')
    const preselect = Number(route.query.rnd)
    if (preselect && relationships.value.some(r => r.rnd.id === preselect)) {
      selectedRndId.value = preselect
    } else if (relationships.value.length) {
      selectedRndId.value = relationships.value[0].rnd.id
    }
  } catch {
    loadError.value = 'Could not load your RNDs. Please try again later.'
  } finally {
    isLoading.value = false
  }
}

async function submitBooking() {
  isSubmitting.value = true
  submitError.value = ''
  try {
    await post('/client/appointments/', {
      rnd_id: selectedRndId.value,
      scheduled_at: new Date(scheduledAt.value).toISOString(),
      type: type.value,
      duration_minutes: durationMinutes.value,
      notes: notes.value,
    })
    await navigateTo('/appointments')
  } catch (error) {
    submitError.value = error?.data?.detail || error?.data?.rnd_id?.[0] || 'Could not book this appointment. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

onMounted(loadRelationships)
</script>

<style scoped>
* { box-sizing: border-box; }

.book-page { font-family: 'Inter', sans-serif; max-width: 640px; }

.page-header { margin-bottom: 20px; }
.breadcrumb { font-size: 0.8rem; color: #8a9a8a; margin: 0 0 8px; }
.breadcrumb :deep(a) { color: #3a6b3a; text-decoration: none; }
.page-title { font-family: 'Playfair Display', serif; font-size: 1.7rem; color: #1a3a1a; margin: 0 0 4px; }
.page-sub { font-size: 0.88rem; color: #6a7a6a; margin: 0; }

.surface {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec; padding: 20px 22px;
}
.mb-3 { margin-bottom: 16px; }

.eyebrow {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; color: #8a9a8a;
  margin: 18px 0 10px;
}
.eyebrow:first-child { margin-top: 0; }

.field-label { display: block; font-size: 0.85rem; font-weight: 600; color: #1a3a1a; margin: 0 0 8px; }
.optional { font-weight: 400; color: #9aaa9a; }
.field-input {
  width: 100%; border: 1px solid #d5dad5; border-radius: 8px; padding: 10px 12px;
  font-size: 0.88rem; color: #2a2a2a; font-family: inherit; background: #fff;
}
.field-input:focus { outline: none; border-color: #D4A017; }
.duration-select { max-width: 220px; }
textarea.field-input { resize: vertical; margin-top: 4px; }

.modality-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.modality-option {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  border: 1.5px solid #e0e6dc; border-radius: 10px; padding: 16px 10px;
  background: #fff; color: #3a6b3a; font-size: 0.82rem; font-weight: 600; cursor: pointer;
}
.modality-option.selected { border-color: #D4A017; background: rgba(212,160,23,0.08); color: #1a3a1a; }

.form-error {
  background: #fdecec; border: 1px solid #f3b8b8; color: #a12525;
  border-radius: 8px; padding: 10px 14px; font-size: 0.85rem; margin: 0 0 16px;
}

.submit-btn {
  width: 100%; background: #D4A017; color: #1a3a1a; border: none; border-radius: 8px;
  padding: 14px; font-weight: 700; font-size: 0.95rem; cursor: pointer;
}
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.submit-note { text-align: center; font-size: 0.78rem; color: #9aaa9a; margin: 10px 0 0; }

.placeholder-text { font-size: 0.85rem; color: #9aaa9a; }

.empty-state {
  background: #fff; border-radius: 12px; border: 1px solid #eceeec;
  padding: 60px 20px; text-align: center;
}
.empty-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a3a1a; margin: 0 0 6px; }
.empty-desc { font-size: 0.85rem; color: #8a9a8a; margin: 0; }
.empty-desc :deep(a) { color: #3a6b3a; font-weight: 600; }
</style>
