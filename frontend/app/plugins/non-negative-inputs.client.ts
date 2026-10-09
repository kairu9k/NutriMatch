// A number input's `min` only limits its spinner arrows — the user can
// still type or paste a lower value (e.g. "-5"). For number inputs with a
// `min` of 0 or more, app-wide:
//  - the "-" key (and "+"/"e", which number inputs also accept) is blocked,
//    so a negative can't be typed in the first place. (Snapping "-" to 0
//    mid-typing turned "-1500" into "500".)
//  - anything still below `min` — e.g. pasted — is raised to `min` as it's
//    entered. This runs in the capture phase, before Vue's own v-model
//    listener, so v-model receives the corrected value.
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
    if (input && input.value !== '' && Number(input.value) < Number(input.min)) input.value = input.min
  }, true)
})
