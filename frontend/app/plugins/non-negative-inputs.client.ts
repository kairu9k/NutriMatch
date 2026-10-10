// A number input's `min` only limits its spinner arrows — the user can
// still type or paste a lower value (e.g. "-5"). For number inputs with a
// `min` of 0 or more, app-wide:
//  - the "-" key (and "+"/"e", which number inputs also accept) is blocked,
//    so a negative can't be typed in the first place. (Snapping "-" to 0
//    mid-typing turned "-1500" into "500".)
//  - a negative that still gets in — e.g. pasted — is raised to 0. This
//    runs in the capture phase, before Vue's own v-model listener, so
//    v-model receives the corrected value. Only negatives are touched: a
//    value that's merely below a higher `min` (height min 100) is left for
//    the form to flag, because snapping it to `min` while typing made the
//    field impossible to edit — backspacing "162" to "16" jumped to the min.
//  - scrolling the mouse wheel over a focused number input no longer changes
//    its value (it used to turn a blank height into the min while the user
//    was just scrolling the page); the page scrolls instead.
// The API rejects negatives too (core/validators.py) — this just keeps the
// form from showing them.
function nonNegativeNumberInput(target: EventTarget | null): HTMLInputElement | null {
  if (!(target instanceof HTMLInputElement) || target.type !== 'number' || target.min === '') return null
  return Number(target.min) >= 0 ? target : null
}

export default defineNuxtPlugin(() => {
  document.addEventListener('keydown', (event) => {
    if (nonNegativeNumberInput(event.target) && ['-', '+', 'e', 'E'].includes(event.key)) event.preventDefault()
  }, true)

  document.addEventListener('input', (event) => {
    const input = nonNegativeNumberInput(event.target)
    if (input && input.value !== '' && Number(input.value) < 0) input.value = '0'
  }, true)

  document.addEventListener('wheel', (event) => {
    const target = event.target
    if (target instanceof HTMLInputElement && target.type === 'number' && target === document.activeElement) target.blur()
  }, { capture: true, passive: true })
})
