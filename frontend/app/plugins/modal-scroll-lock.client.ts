// While any pop-up (or the phone menu) is open, the page behind it doesn't
// scroll — otherwise, on phones, reaching the end of a pop-up starts
// scrolling the page underneath (user's report, 2026-10-22). One place for
// every pop-up: new ones are covered as long as they use one of these
// overlay classes or aria-modal="true".
const OPEN_POPUP = [
  '[aria-modal="true"]',
  '.nm-modal-overlay',
  '.modal-overlay',
  '.welcome-overlay',
  '.legal-overlay',
  '.ncp-overlay',
  '.ml-overlay',
  '.dr-overlay',
  '.sidebar-overlay',
].join(', ')

export default defineNuxtPlugin(() => {
  let locked = false
  let queued = false

  const apply = () => {
    queued = false
    const open = !!document.querySelector(OPEN_POPUP)
    if (open === locked) return
    locked = open
    document.documentElement.style.overflow = open ? 'hidden' : ''
    document.body.style.overflow = open ? 'hidden' : ''
  }

  new MutationObserver(() => {
    if (!queued) {
      queued = true
      requestAnimationFrame(apply)
    }
  }).observe(document.body, { childList: true, subtree: true })
  apply()
})
