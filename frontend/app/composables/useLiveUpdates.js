// One live connection per signed-in tab (ws/notifications/, backend
// communication/live.py): new bell notifications and "someone messaged you"
// arrive the moment they happen. The dashboard layout starts it; components
// listen with onLive(kind, handler). If the socket is down, `connected` is
// false and listeners fall back to a slow refresh.
import { useAuthStore } from '~/stores/auth'

let socket = null
let retryTimer = null
let retryDelay = 1000
let wanted = false
let startedFor = null
let signOutWatch = null
const listeners = { notification: new Set(), message: new Set(), reconnect: new Set() }

export function useLiveUpdates() {
  const connected = useState('live-connected', () => false)
  const auth = useAuthStore()
  const config = useRuntimeConfig()

  function url() {
    const base = config.public.apiBase.replace(/\/api\/?$/, '').replace(/^http/, 'ws')
    return `${base}/ws/notifications/?token=${auth.accessToken}`
  }

  // The server turns away an expired token before the socket opens (the
  // browser only sees a failed connection), so refresh it first.
  function tokenExpiresSoon() {
    try {
      const { exp } = JSON.parse(atob(auth.accessToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
      return exp * 1000 < Date.now() + 30000
    } catch { return true }
  }

  async function open(isRetry = false) {
    if (!wanted || !auth.accessToken || socket) return
    if (tokenExpiresSoon() && !(await auth.refreshAccessToken())) return
    if (!wanted || socket) return
    const ws = new WebSocket(url())
    socket = ws
    ws.onopen = () => {
      connected.value = true
      retryDelay = 1000
      // Anything sent while we were disconnected: let pages re-sync.
      if (isRetry) listeners.reconnect.forEach(fn => fn())
    }
    ws.onmessage = (e) => {
      let data
      try { data = JSON.parse(e.data) } catch { return }
      listeners[data.kind]?.forEach(fn => fn(data))
    }
    ws.onclose = () => {
      if (socket === ws) socket = null
      connected.value = false
      if (!wanted) return
      clearTimeout(retryTimer)
      retryTimer = setTimeout(() => open(true), retryDelay)
      retryDelay = Math.min(retryDelay * 2, 30000)
    }
  }

  // Follows the signed-in user: signing out closes it (the login page has
  // no dashboard layout to do that), another account gets its own socket.
  function start() {
    if (wanted && startedFor === auth.user?.id) return
    stop()
    wanted = true
    startedFor = auth.user?.id
    if (!signOutWatch) signOutWatch = watch(() => auth.accessToken, (token) => { if (!token) stop() })
    open()
  }

  function stop() {
    wanted = false
    startedFor = null
    clearTimeout(retryTimer)
    if (socket) {
      socket.onclose = null
      socket.close()
      socket = null
    }
    connected.value = false
  }

  // Registers a listener for this component's lifetime.
  function onLive(kind, fn) {
    listeners[kind].add(fn)
    onUnmounted(() => listeners[kind].delete(fn))
  }

  return { connected, start, stop, onLive }
}
