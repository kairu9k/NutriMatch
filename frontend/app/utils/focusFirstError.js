// After a Save that found problems: bring the first red field into view and put
// the cursor in it (2026-11-03, adviser check: errors under a field that is
// scrolled off screen were missed). scrollIntoView also scrolls a pop-up's own
// scroll area, so this works inside nm-modal too.
//
// Fields count as red when they carry aria-invalid="true" or the class
// `invalid` (DateField, PhoneInput and the forms already use one of these).
// Returns how many red fields there are, for "Check N fields" toasts.
import { nextTick } from 'vue'

const SELECTOR = '[aria-invalid="true"], .invalid'

export async function focusFirstError(root) {
  await nextTick()
  const scope = root?.$el || root || document
  const shown = [...scope.querySelectorAll(SELECTOR)].filter(el => el.offsetParent !== null || el.getClientRects().length)
  // one field can be marked twice (a red wrapper around a red input): count it once
  const all = shown.filter(el => !shown.some(other => other !== el && other.contains(el)))
  const first = all[0]
  if (!first) return 0
  const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  first.scrollIntoView({ block: 'center', behavior: reduce ? 'auto' : 'smooth' })
  // the first control that can take the cursor (a disabled one can't: the
  // RND phone box starts with a country picker fixed to the Philippines)
  const FOCUSABLE = 'input:not([disabled]):not([type=hidden]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])'
  const target = first.matches(FOCUSABLE) ? first : first.querySelector(FOCUSABLE)
  target?.focus({ preventScroll: true })
  return all.length
}

// "Check 2 fields before saving." / "Check the field marked in red."
export function fieldsProblemText(count, verb = 'saving') {
  return count > 1 ? `Check ${count} fields before ${verb}.` : `Check the field marked in red before ${verb}.`
}
