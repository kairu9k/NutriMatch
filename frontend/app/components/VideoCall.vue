<template>
  <div class="call">
    <!-- the other person, large -->
    <video v-show="showRemoteVideo" ref="remoteEl" class="remote" autoplay playsinline />
    <div v-if="!showRemoteVideo" class="placeholder">
      <img v-if="otherPhoto" :src="otherPhoto" class="ph-avatar" alt="" />
      <span v-else class="ph-avatar">{{ initials }}</span>
      <p class="ph-name">{{ otherName }}</p>
      <p class="ph-state" role="status">{{ stateText }}</p>
      <p v-if="stateHint" class="ph-hint">{{ stateHint }}</p>
      <button v-if="call.status.value === 'blocked' || call.status.value === 'replaced'" type="button" class="ph-btn" @click="call.start()">
        {{ call.status.value === 'replaced' ? 'Use the call here' : 'Try again' }}
      </button>
    </div>

    <!-- a short notice over the video: reconnecting, they muted -->
    <p v-if="showRemoteVideo && notice" class="notice" role="status">{{ notice }}</p>

    <!-- you, small -->
    <div v-if="call.localStream.value" class="self" :class="{ off: !call.camOn.value }">
      <video v-show="call.camOn.value" ref="localEl" class="self-video" autoplay playsinline muted />
      <span v-if="!call.camOn.value" class="self-off"><VideoOff :size="16" aria-hidden="true" /> Camera off</span>
      <span class="self-label">You</span>
    </div>

    <!-- controls -->
    <div v-if="inCall" class="controls" role="toolbar" aria-label="Call controls">
      <button type="button" class="ctl" :class="{ off: !call.micOn.value }" :aria-label="call.micOn.value ? 'Mute' : 'Unmute'" @click="call.toggleMic">
        <component :is="call.micOn.value ? Mic : MicOff" :size="18" aria-hidden="true" />
        <span>{{ call.micOn.value ? 'Mute' : 'Unmute' }}</span>
      </button>
      <button type="button" class="ctl" :class="{ off: !call.camOn.value }" :disabled="!call.hasCamera.value" :aria-label="!call.hasCamera.value ? 'No camera' : call.camOn.value ? 'Stop video' : 'Start video'" @click="call.toggleCam">
        <component :is="call.camOn.value ? Video : VideoOff" :size="18" aria-hidden="true" />
        <span>{{ !call.hasCamera.value ? 'No camera' : call.camOn.value ? 'Stop video' : 'Start video' }}</span>
      </button>
      <button v-if="call.canSwitchCamera.value" type="button" class="ctl" aria-label="Switch camera" @click="call.switchCamera">
        <SwitchCamera :size="18" aria-hidden="true" /><span>Switch camera</span>
      </button>
      <button type="button" class="ctl end" :aria-label="isRnd ? 'End the call' : 'Leave the call'" @click="hangUp">
        <PhoneOff :size="18" aria-hidden="true" /><span>{{ isRnd ? 'End' : 'Leave' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
// The video call inside the consultation room (composables/useWebRtcCall.js).
// Ending: the client just leaves; for the RND the room opens Finish
// consultation (the `hangup` event), and the call starts again if they stay.
import { Mic, MicOff, PhoneOff, SwitchCamera, Video, VideoOff } from 'lucide-vue-next'

const props = defineProps({
  appointmentId: { type: [Number, String], required: true },
  otherName: { type: String, default: '' },
  otherPhoto: { type: String, default: null },
  isRnd: { type: Boolean, default: false },
})
const emit = defineEmits(['hangup'])

const call = useWebRtcCall(props.appointmentId)
const remoteEl = ref(null)
const localEl = ref(null)
const firstName = computed(() => props.otherName.split(' ')[0] || (props.isRnd ? 'Your patient' : 'Your RND'))
const initials = computed(() => props.otherName.split(' ').filter(Boolean).map(w => w[0]).slice(0, 2).join('').toUpperCase())

const inCall = computed(() => ['waiting', 'connecting', 'connected', 'reconnecting'].includes(call.status.value))
const showRemoteVideo = computed(() => call.status.value === 'connected' && call.peerMedia.value.video && !!call.remoteStream.value)

const stateText = computed(() => {
  const st = call.status.value
  if (st === 'waiting') return call.peerLeft.value ? `${firstName.value} left the call` : `Waiting for ${firstName.value} to join`
  if (st === 'connecting') return call.peer.value ? `Connecting to ${firstName.value}…` : 'Getting your camera and microphone ready…'
  if (st === 'reconnecting') return 'Reconnecting…'
  if (st === 'connected') return `${firstName.value} turned off their camera`
  if (st === 'blocked') return 'NutriMatch can\'t use your camera or microphone'
  if (st === 'replaced') return 'You opened this call in another tab'
  if (st === 'denied') return call.message.value || 'You can\'t join this call right now'
  if (st === 'error') return call.message.value || 'The call stopped working'
  if (st === 'ended') return 'You left the call'
  return 'Starting the call…'
})
const stateHint = computed(() => {
  const st = call.status.value
  if (st === 'waiting') return call.peerLeft.value ? 'They can join again from the same page.' : 'Keep this page open. The call starts when they join.'
  if (st === 'reconnecting') return 'The internet connection dropped. Stay on this page; the call comes back on its own.'
  if (st === 'blocked') return 'Allow the camera and microphone for this site (the camera icon in the address bar, or your phone\'s settings), then try again.'
  if (st === 'replaced') return 'The call moved to the newer tab.'
  return ''
})
const notice = computed(() => {
  if (call.status.value === 'reconnecting') return 'Reconnecting…'
  if (!call.peerMedia.value.audio) return `${firstName.value} is muted`
  return ''
})

// show the streams in the video elements
watch([call.remoteStream, remoteEl], ([stream, el]) => { if (el) el.srcObject = stream || null })
watch([call.localStream, localEl], ([stream, el]) => { if (el) el.srcObject = stream || null })

// The room asks first (the RND: how to finish; the client: leave the call?),
// and the call stays connected meanwhile; leaving the room ends it.
function hangUp() {
  emit('hangup')
}

onMounted(() => call.start())
defineExpose({ leave: call.leave, start: call.start })
</script>

<style scoped>
.call { position: relative; width: 100%; height: 100%; background: #0b1914; overflow: hidden; display: flex; align-items: center; justify-content: center; }
.remote { width: 100%; height: 100%; object-fit: contain; background: #0b1914; }

.placeholder { display: flex; flex-direction: column; align-items: center; gap: 8px; max-width: 360px; padding: 20px; text-align: center; color: #a9c2b0; }
.ph-avatar {
  width: 96px; height: 96px; border-radius: 50%; object-fit: cover; background: #1f3a2e; color: #e3efe7;
  display: flex; align-items: center; justify-content: center; font-size: 1.8rem; font-weight: 700; margin-bottom: 6px;
}
.ph-name { margin: 0; font-family: 'Playfair Display', serif; font-size: 1.3rem; font-weight: 700; color: #fff; }
.ph-state { margin: 0; font-size: 0.92rem; color: #e3efe7; }
.ph-hint { margin: 0; font-size: 0.8rem; line-height: 1.5; }
.ph-btn {
  margin-top: 6px; min-height: 36px; padding: 0 16px; border-radius: 8px; border: none; cursor: pointer;
  background: #e3efe7; color: #0a4a37; font-family: inherit; font-weight: 700; font-size: 0.85rem;
}

.notice {
  position: absolute; top: 14px; left: 50%; transform: translateX(-50%); margin: 0; padding: 6px 12px; border-radius: 999px;
  background: rgba(11, 25, 20, 0.78); color: #fff; font-size: 0.8rem; font-weight: 600;
}

.self {
  position: absolute; right: 14px; bottom: 82px; width: 180px; aspect-ratio: 4 / 3; border-radius: 12px; overflow: hidden;
  background: #1f3a2e; box-shadow: 0 0 2px rgba(0, 0, 0, 0.3), 0 0 18px rgba(0, 0, 0, 0.35); border: 1px solid rgba(255, 255, 255, 0.12);
}
.self-video { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); }
.self-off { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; gap: 6px; color: #a9c2b0; font-size: 0.78rem; }
.self-label { position: absolute; left: 8px; bottom: 6px; font-size: 0.72rem; font-weight: 700; color: #fff; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6); }

.controls {
  position: absolute; left: 50%; bottom: 16px; transform: translateX(-50%); display: flex; gap: 8px; padding: 8px;
  border-radius: 14px; background: rgba(11, 25, 20, 0.82); border: 1px solid rgba(255, 255, 255, 0.1);
}
.ctl {
  display: inline-flex; align-items: center; gap: 6px; height: 40px; padding: 0 14px; border-radius: 10px; border: none; cursor: pointer;
  background: #e3efe7; color: #0a4a37; font-family: inherit; font-size: 0.82rem; font-weight: 700; white-space: nowrap;
}
.ctl:hover:not(:disabled) { background: #d3e7da; }
.ctl.off { background: #3a4a40; color: #fff; }
.ctl:disabled { opacity: 0.55; cursor: not-allowed; }
.ctl.end { background: #c0392b; color: #fff; }
.ctl.end:hover { background: #a93226; }
.ctl:focus-visible { outline: 2px solid #D4A017; outline-offset: 2px; }

@media (max-width: 640px) {
  .self { width: 104px; bottom: 78px; right: 10px; }
  .controls { left: 10px; right: 10px; transform: none; justify-content: center; bottom: 10px; }
  .ctl { padding: 0 12px; }
  .ctl span { display: none; } /* icons only on phones; each button keeps its aria-label */
}
</style>
