// One toast for the whole app (2026-11-03, after the adviser check): a result
// the person can't otherwise see shows here, wherever they have scrolled.
// Built on vue-sonner; pages call this, never vue-sonner directly.
//
// Timing (user's decision, "the mix"):
//   success  4 s   the page already shows the result, this only confirms it
//   problem  6 s   a form problem; the fields stay red underneath
//   error    stays until closed or retried; nothing else on screen shows it
// Every toast pauses while hovered or while the tab is hidden (vue-sonner).
//
// One toast per action: pass the same `id` (e.g. 'meal-plan-save') and a
// retry replaces the old toast: "Saving…" then "Plan saved." or the error.
import { toast as sonner } from 'vue-sonner'

export const TOAST_MS = { success: 4000, problem: 6000 }

export function useToast() {
  const success = (message, opts = {}) =>
    sonner.success(message, { duration: TOAST_MS.success, ...opts })

  // A form problem: points at the red fields, so it can go away by itself.
  const problem = (message, opts = {}) =>
    sonner.warning(message, { duration: TOAST_MS.problem, ...opts })

  // A failed action: stays until the person closes it or retries.
  const error = (message, opts = {}) =>
    sonner.error(message, { duration: Infinity, closeButton: true, ...opts })

  // "Saving…" on the action's own toast; finish it with success/error and the same id.
  const working = (message, opts = {}) =>
    sonner.loading(message, { duration: Infinity, ...opts })

  const dismiss = id => sonner.dismiss(id)

  // Runs an action with its own toast: working → success, or → error.
  // Returns the action's result, or undefined when it failed.
  async function run(id, action, { working: busyText, success: doneText, error: failText }) {
    if (busyText) working(busyText, { id })
    try {
      const result = await action()
      if (doneText) success(typeof doneText === 'function' ? doneText(result) : doneText, { id })
      else dismiss(id)
      return result
    } catch (e) {
      error(apiErrorText(e, failText), { id })
      return undefined
    }
  }

  return { success, problem, error, working, dismiss, run }
}

// The server's own words when it gives them (DRF `detail`, or the first field
// error), else the page's fallback. Network failures get a plain sentence.
export function apiErrorText(e, fallback = 'Something went wrong. Please try again.') {
  const data = e?.data
  if (!e?.response && !data && e?.name === 'FetchError') return 'No connection. Check your internet and try again.'
  if (typeof data === 'string' && data.length < 200 && !data.startsWith('<')) return data
  if (data?.detail) return String(data.detail)
  if (data && typeof data === 'object') {
    const first = Object.values(data).flat()[0]
    if (typeof first === 'string') return first
  }
  return fallback
}
