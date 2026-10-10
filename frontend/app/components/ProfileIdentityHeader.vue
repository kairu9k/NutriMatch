<template>
  <!-- Avatar + name header shared by the client (ClientProfileSettings.vue)
       and RND (ProfileSettings.vue) settings pages, so the two stay the same.
       The photo uploads/removes immediately via POST/DELETE /auth/me/photo/;
       the page's own buttons (Edit Profile / Cancel / Save) go in #actions. -->
  <div class="identity-row">
    <div class="avatar-wrap">
      <img v-if="photoUrl" :src="photoUrl" alt="Your profile photo" class="avatar-circle avatar-img" />
      <div v-else class="avatar-circle">{{ initials }}</div>
      <button
        class="avatar-camera" type="button" :disabled="isUploading"
        :aria-label="photoUrl ? 'Change photo' : 'Upload photo'" @click="photoInput?.click()"
      >
        <Loader2 v-if="isUploading" :size="14" class="spin" />
        <Camera v-else :size="14" />
      </button>
      <input ref="photoInput" type="file" accept="image/jpeg,image/png,image/webp" class="visually-hidden" @change="onPhotoSelected" />
    </div>

    <div class="identity-text">
      <p class="identity-name">{{ name }}</p>
      <p class="identity-sub">{{ subtitle }}</p>
      <p class="photo-links">
        <button class="photo-link" type="button" :disabled="isUploading" @click="photoInput?.click()">
          {{ isUploading ? 'Uploading…' : photoUrl ? 'Change photo' : 'Upload photo' }}
        </button>
        <template v-if="photoUrl && !isUploading">
          <span class="dot">·</span>
          <button class="photo-link danger" type="button" @click="removePhoto">Remove</button>
        </template>
        <span class="photo-hint">JPG, PNG or WEBP · max 2 MB</span>
      </p>
      <p v-if="photoError" class="photo-error">{{ photoError }}</p>
    </div>

    <div class="identity-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Camera, Loader2 } from 'lucide-vue-next'
import { useAuthStore } from '~/stores/auth'

defineProps({
  name: { type: String, default: '' },
  subtitle: { type: String, default: '' },
})
const emit = defineEmits(['photo-changed'])

const auth = useAuthStore()
const { post, del } = useApi()

const photoInput = ref(null)
const isUploading = ref(false)
const photoError = ref('')
const photoUrl = computed(() => auth.user?.profile_photo || '')
const initials = computed(() => `${auth.user?.first_name?.[0] || ''}${auth.user?.last_name?.[0] || ''}`.toUpperCase())

// Same limits the API enforces (accounts/views.py MePhotoView).
const PHOTO_TYPES = ['image/jpeg', 'image/png', 'image/webp']
const MAX_PHOTO_BYTES = 2 * 1024 * 1024

async function onPhotoSelected(event) {
  const file = event.target.files?.[0]
  event.target.value = '' // so picking the same file again still fires
  if (!file) return
  photoError.value = ''
  if (!PHOTO_TYPES.includes(file.type)) {
    photoError.value = 'Use a JPG, PNG, or WEBP image.'
    return
  }
  if (file.size > MAX_PHOTO_BYTES) {
    photoError.value = 'The photo must be 2 MB or smaller.'
    return
  }
  isUploading.value = true
  try {
    const body = new FormData()
    body.append('photo', file)
    await post('/auth/me/photo/', body)
    await auth.fetchMe()
    emit('photo-changed', 'Photo updated!')
  } catch (error) {
    const data = error?.data || {}
    photoError.value = (Array.isArray(data.photo) ? data.photo[0] : data.photo) || data.detail || 'Could not upload the photo. Please try again.'
  } finally {
    isUploading.value = false
  }
}

async function removePhoto() {
  photoError.value = ''
  isUploading.value = true
  try {
    await del('/auth/me/photo/')
    await auth.fetchMe()
    emit('photo-changed', 'Photo removed.')
  } catch {
    photoError.value = 'Could not remove the photo. Please try again.'
  } finally {
    isUploading.value = false
  }
}
</script>

<style scoped>
.identity-row { display: flex; align-items: center; gap: 18px; margin-bottom: 26px; }
.avatar-wrap { position: relative; flex-shrink: 0; }
.avatar-circle {
  width: 56px; height: 56px; border-radius: 50%; background: #D4A017; color: #1a3a1a;
  display: flex; align-items: center; justify-content: center; font-size: 1.05rem; font-weight: 700;
}
.avatar-img { object-fit: cover; display: block; background: #eef1ee; }
.avatar-camera {
  position: absolute; right: -4px; bottom: -4px; width: 26px; height: 26px; border-radius: 50%;
  border: 2px solid #fff; background: #163a1c; color: #fff; cursor: pointer;
  display: flex; align-items: center; justify-content: center; padding: 0;
}
.avatar-camera:disabled { opacity: 0.7; cursor: wait; }
.visually-hidden { position: absolute; width: 1px; height: 1px; opacity: 0; pointer-events: none; }

.identity-text { flex: 1; min-width: 0; }
.identity-name { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #1a3a1a; margin: 0; }
.identity-sub { font-size: 0.78rem; color: #9aaa9a; margin: 4px 0 0; overflow-wrap: anywhere; }
.photo-links { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin: 6px 0 0; font-size: 0.78rem; }
.photo-link { background: none; border: none; padding: 0; font: inherit; font-weight: 600; color: #1f8f5c; cursor: pointer; }
.photo-link:hover { text-decoration: underline; }
.photo-link:disabled { color: #9aaa9a; cursor: wait; }
.photo-link.danger { color: #c0392b; }
.dot { color: #c5cec5; }
.photo-hint { color: #aab5aa; margin-left: 4px; }
.photo-error { font-size: 0.76rem; color: #c0392b; margin: 4px 0 0; }
.identity-actions { display: flex; gap: 10px; align-items: center; flex-shrink: 0; margin-left: auto; }
.identity-actions:empty { display: none; }
.spin { animation: spin 0.9s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 640px) {
  .identity-row { flex-wrap: wrap; }
  .identity-actions { width: 100%; margin-left: 0; }
  .identity-actions > :deep(*) { flex: 1; }
}
</style>
