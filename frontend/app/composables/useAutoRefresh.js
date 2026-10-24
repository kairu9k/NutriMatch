// Keeps a page's data current without a browser reload (2026-10-25).
//
//   useAutoRefresh(() => load({ quiet: true }))
//
// The refresh runs:
// - when a live notification arrives (ws/notifications/, clients and RNDs):
//   nearly every change someone else makes (booking, payment, cancellation,
//   meal log, lab upload...) sends one; `messages: true` also listens for chat;
// - when the live connection comes back, and when the tab is shown again
//   after being hidden for a while;
// - on a timer: every `interval` (60 s) while there's no live connection
//   (admins never have one), and every `liveInterval` (2 min) as a safety net
//   for the few changes that send the viewer no notification.
//
// It never refreshes over someone's work: while a pop-up is open, a text field
// is focused, or `paused()` says so (unsaved edits), it waits and tries again.
// The page's load function should not show its loading state on these runs.

const DEBOUNCE_MS = 700
const TICK_MS = 5000 // how often a waiting refresh is retried and the timer checked
const STALE_MS = 15000

export function useAutoRefresh(refresh, { interval = 60000, liveInterval = 120000, messages = false, paused = () => false } = {}) {
  if (import.meta.server) return { refreshNow: () => {} }
  const live = useLiveUpdates()
  let lastRun = Date.now()
  let debounce = null
  let pending = false // a refresh is owed (it was busy or hidden)
  let timer = null
  let running = false
  let again = false

  function busy() {
    if (paused()) return true
    if (document.querySelector('[aria-modal="true"]')) return true
    const el = document.activeElement
    return !!el && (el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable ||
      (el.tagName === 'INPUT' && !['checkbox', 'radio', 'button', 'submit'].includes(el.type)))
  }

  async function run() {
    if (document.visibilityState !== 'visible' || busy()) { pending = true; return } // retried on the next tick
    if (running) { again = true; return }
    pending = false
    running = true
    try {
      await refresh()
    } catch {
      // a failed background refresh keeps what's on screen
    } finally {
      lastRun = Date.now()
      running = false
      if (again) { again = false; schedule() }
    }
  }

  function schedule() {
    clearTimeout(debounce)
    debounce = setTimeout(run, DEBOUNCE_MS)
  }

  function onVisible() {
    if (document.visibilityState === 'visible' && Date.now() - lastRun > STALE_MS) schedule()
  }

  live.onLive('notification', schedule)
  live.onLive('reconnect', schedule)
  if (messages) live.onLive('message', schedule)

  onMounted(() => {
    document.addEventListener('visibilitychange', onVisible)
    timer = setInterval(() => {
      const every = live.connected.value ? liveInterval : interval
      if (pending || Date.now() - lastRun >= every) run()
    }, TICK_MS)
  })
  onBeforeUnmount(() => {
    document.removeEventListener('visibilitychange', onVisible)
    clearInterval(timer)
    clearTimeout(debounce)
  })

  return { refreshNow: schedule }
}
