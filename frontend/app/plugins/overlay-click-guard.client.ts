// Pop-ups close when their dark background is clicked (@click.self on the
// overlay). A browser "click" is a press plus a release, and if the press is
// inside the panel (selecting text, dragging) and the release is on the
// background, the click lands on the background and the pop-up closed
// (user's report, 2026-10-23). This guard only lets a background click
// through when the press started on that same background too. It applies to
// pop-up backgrounds only, never to buttons or anything else.
const OVERLAYS = [
  '.nm-modal-overlay',
  '.modal-overlay',
  '.overlay',
  '.inner-overlay',
  '.welcome-overlay',
  '.photo-viewer',
  '.ml-overlay',
  '.legal-overlay',
  '.ncp-overlay',
  '.dr-overlay',
  '.sidebar-overlay',
].join(', ')

export default defineNuxtPlugin(() => {
  let pressedOn: EventTarget | null = null

  document.addEventListener('pointerdown', (e) => { pressedOn = e.target }, true)

  document.addEventListener('click', (e) => {
    const target = e.target as Element | null
    if (target && target.matches?.(OVERLAYS) && pressedOn !== target) {
      // pressed inside the panel, released on the background: not a click outside
      e.stopPropagation()
      e.preventDefault()
    }
    pressedOn = null
  }, true)
})
