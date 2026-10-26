// NutriMatch's own 1-on-1 video call (WebRTC, 2026-10-26). The two browsers
// connect directly and encrypt the call between them; the server only
// introduces them (backend scheduling/video_call.py + consumers.py):
//   GET /api/appointments/<id>/call-config/  STUN + TURN (Cloudflare) servers
//   ws  /ws/appointments/<id>/call/           offer / answer / ICE candidates
// "Perfect negotiation" (MDN): the client is the polite side, so when both
// start an offer at once the RND's wins. A dropped network is retried with an
// ICE restart; a dropped socket reconnects and renegotiates. Not recorded.
import { useAuthStore } from '~/stores/auth'

const RECONNECT_GRACE_MS = 4000 // "disconnected" often recovers by itself

export function useWebRtcCall(appointmentId) {
  const { get } = useApi()
  const auth = useAuthStore()
  const config = useRuntimeConfig()

  // waiting | connecting | connected | reconnecting | blocked | denied | replaced | ended | error
  const status = ref('idle')
  const message = ref('') // a reason, for denied / blocked / error
  const localStream = shallowRef(null)
  const remoteStream = shallowRef(null)
  const micOn = ref(true)
  const camOn = ref(true)
  const hasCamera = ref(true)
  const canSwitchCamera = ref(false)
  const peer = ref(null) // { name, role } while the other person is in the call
  const peerMedia = ref({ audio: true, video: true })
  const peerLeft = ref(false) // they were here and left

  let role = null
  let iceServers = []
  let socket = null
  let pc = null
  let makingOffer = false
  let ignoreOffer = false
  let wanted = false
  let retryTimer = null
  let retryDelay = 1000
  let graceTimer = null
  let facing = 'user'

  const polite = () => role === 'client'

  function socketUrl() {
    const base = config.public.apiBase.replace(/\/api\/?$/, '').replace(/^http/, 'ws')
    return `${base}/ws/appointments/${appointmentId}/call/?token=${auth.accessToken}`
  }
  function tokenExpiresSoon() {
    try {
      const { exp } = JSON.parse(atob(auth.accessToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
      return exp * 1000 < Date.now() + 30000
    } catch { return true }
  }
  function send(data) {
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify(data))
  }

  /* ---------- camera and microphone ---------- */
  async function openMedia() {
    try {
      localStream.value = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        video: { facingMode: facing, width: { ideal: 1280 }, height: { ideal: 720 } },
      })
    } catch (err) {
      if (err?.name === 'NotAllowedError' || err?.name === 'SecurityError') throw err
      // no camera (or it's busy): join with sound only
      localStream.value = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }, video: false })
      hasCamera.value = false
      camOn.value = false
    }
    try {
      const cams = (await navigator.mediaDevices.enumerateDevices()).filter(d => d.kind === 'videoinput')
      canSwitchCamera.value = hasCamera.value && cams.length > 1
    } catch { canSwitchCamera.value = false }
  }

  /* ---------- the peer connection ---------- */
  function newPeerConnection() {
    closePeerConnection()
    const conn = new RTCPeerConnection({ iceServers })
    pc = conn
    remoteStream.value = new MediaStream()
    localStream.value?.getTracks().forEach(t => conn.addTrack(t, localStream.value))
    conn.ontrack = ({ track }) => {
      const stream = remoteStream.value || new MediaStream()
      if (!stream.getTracks().includes(track)) stream.addTrack(track)
      remoteStream.value = new MediaStream(stream.getTracks()) // new object so the view updates
    }
    conn.onicecandidate = ({ candidate }) => { if (candidate) send({ type: 'signal', data: { candidate } }) }
    conn.onnegotiationneeded = async () => {
      try {
        makingOffer = true
        await conn.setLocalDescription()
        send({ type: 'signal', data: { description: conn.localDescription } })
      } catch { /* the other side's offer wins; handled in onSignal */ } finally {
        makingOffer = false
      }
    }
    conn.onconnectionstatechange = () => {
      if (pc !== conn) return
      const st = conn.connectionState
      clearTimeout(graceTimer)
      if (st === 'connected') status.value = 'connected'
      else if (st === 'connecting' || st === 'new') { if (status.value !== 'reconnecting') status.value = 'connecting' }
      else if (st === 'disconnected') {
        status.value = 'reconnecting'
        graceTimer = setTimeout(() => { if (pc === conn && conn.connectionState !== 'connected') conn.restartIce() }, RECONNECT_GRACE_MS)
      } else if (st === 'failed') {
        status.value = 'reconnecting'
        conn.restartIce()
      }
    }
    status.value = 'connecting'
    send({ type: 'media', audio: micOn.value, video: camOn.value })
  }
  function closePeerConnection() {
    clearTimeout(graceTimer)
    if (pc) {
      pc.ontrack = pc.onicecandidate = pc.onnegotiationneeded = pc.onconnectionstatechange = null
      pc.close()
      pc = null
    }
    remoteStream.value = null
  }

  async function onSignal({ description, candidate }) {
    if (!pc) newPeerConnection()
    const conn = pc
    try {
      if (description) {
        const collision = description.type === 'offer' && (makingOffer || conn.signalingState !== 'stable')
        ignoreOffer = !polite() && collision
        if (ignoreOffer) return
        await conn.setRemoteDescription(description)
        if (description.type === 'offer') {
          await conn.setLocalDescription()
          send({ type: 'signal', data: { description: conn.localDescription } })
        }
      } else if (candidate) {
        try { await conn.addIceCandidate(candidate) } catch (err) { if (!ignoreOffer) throw err }
      }
    } catch { /* a stale message from an earlier connection: ignore */ }
  }

  /* ---------- the signaling socket ---------- */
  async function openSocket() {
    if (!wanted || socket) return
    if (tokenExpiresSoon() && !(await auth.refreshAccessToken())) {
      status.value = 'error'
      message.value = 'Your sign-in expired. Sign in again to join the call.'
      return
    }
    const ws = new WebSocket(socketUrl())
    socket = ws
    ws.onopen = () => { retryDelay = 1000 }
    ws.onmessage = (e) => {
      let data
      try { data = JSON.parse(e.data) } catch { return }
      if (data.type === 'welcome') {
        role = data.role
        const other = data.peers[0]
        if (other) { peer.value = other; peerLeft.value = false; newPeerConnection() } else if (status.value !== 'reconnecting') status.value = 'waiting'
      } else if (data.type === 'peer-joined') {
        peer.value = data
        peerLeft.value = false
        newPeerConnection()
      } else if (data.type === 'peer-left') {
        closePeerConnection()
        peer.value = null
        peerLeft.value = true
        peerMedia.value = { audio: true, video: true }
        status.value = 'waiting'
      } else if (data.type === 'signal') {
        onSignal(data.data || {})
      } else if (data.type === 'media') {
        peerMedia.value = { audio: data.audio, video: data.video }
      } else if (data.type === 'denied') {
        wanted = false
        status.value = 'denied'
        message.value = data.message
      } else if (data.type === 'replaced') {
        wanted = false
        status.value = 'replaced'
        stopMedia()
      }
    }
    ws.onclose = () => {
      if (socket === ws) socket = null
      if (!wanted) return
      // the call itself may keep going peer to peer; just get the socket back
      if (status.value !== 'connected') status.value = 'reconnecting'
      clearTimeout(retryTimer)
      retryTimer = setTimeout(openSocket, retryDelay)
      retryDelay = Math.min(retryDelay * 2, 15000)
    }
  }

  /* ---------- public ---------- */
  async function start() {
    if (wanted) return
    wanted = true
    status.value = 'connecting'
    message.value = ''
    try {
      const cfg = await get(`/appointments/${appointmentId}/call-config/`)
      role = cfg.role
      iceServers = cfg.ice_servers || []
    } catch (e) {
      wanted = false
      status.value = 'denied'
      message.value = e?.data?.detail || 'You can\'t join this call right now.'
      return
    }
    try {
      await openMedia()
    } catch {
      wanted = false
      status.value = 'blocked'
      return
    }
    openSocket()
  }

  function toggleMic() {
    micOn.value = !micOn.value
    localStream.value?.getAudioTracks().forEach((t) => { t.enabled = micOn.value })
    send({ type: 'media', audio: micOn.value, video: camOn.value })
  }
  function toggleCam() {
    if (!hasCamera.value) return
    camOn.value = !camOn.value
    localStream.value?.getVideoTracks().forEach((t) => { t.enabled = camOn.value })
    send({ type: 'media', audio: micOn.value, video: camOn.value })
  }
  async function switchCamera() {
    if (!canSwitchCamera.value || !localStream.value) return
    const next = facing === 'user' ? 'environment' : 'user'
    try {
      const fresh = await navigator.mediaDevices.getUserMedia({ video: { facingMode: next } })
      const track = fresh.getVideoTracks()[0]
      track.enabled = camOn.value
      const sender = pc?.getSenders().find(s => s.track?.kind === 'video')
      if (sender) await sender.replaceTrack(track)
      const old = localStream.value.getVideoTracks()[0]
      if (old) { localStream.value.removeTrack(old); old.stop() }
      localStream.value.addTrack(track)
      localStream.value = new MediaStream(localStream.value.getTracks())
      facing = next
    } catch { /* keep the current camera */ }
  }

  function stopMedia() {
    localStream.value?.getTracks().forEach(t => t.stop())
    localStream.value = null
  }
  // Leave the call (the room page decides what happens next).
  function leave() {
    wanted = false
    clearTimeout(retryTimer)
    closePeerConnection()
    if (socket) { socket.onclose = null; socket.close(); socket = null }
    stopMedia()
    peer.value = null
    status.value = 'ended'
  }
  onBeforeUnmount(leave)

  return {
    status, message, localStream, remoteStream, micOn, camOn, hasCamera, canSwitchCamera, peer, peerMedia, peerLeft,
    start, leave, toggleMic, toggleCam, switchCamera,
  }
}
