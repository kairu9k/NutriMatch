// No emoji in text fields (user's rule, 2026-10-15). Every text input and
// textarea app-wide silently drops emoji as they're typed or pasted (no
// message — the emoji just never appears) — except notes and messages, which opt in with `data-allow-emoji`
// (chat, support messages/replies, booking notes, meal-log note, reading
// note, RND private / NCP notes, payout notes).
//
// Runs in the capture phase, before Vue's own v-model listener, so v-model
// only ever receives the cleaned text.

// Pictographs (😀 ❤ ✅ …), regional-indicator flags, skin tones, and the
// joiner / variation selector / keycap marks emoji are built from. Digits,
// letters and normal punctuation are untouched.
const EMOJI = /[\p{Extended_Pictographic}\u{1F1E6}-\u{1F1FF}\u{1F3FB}-\u{1F3FF}‍️⃣]/gu
const TEXT_TYPES = new Set(['text', 'search', 'email', 'tel', 'url', 'password', ''])

function emojiFreeField(target: EventTarget | null): HTMLInputElement | HTMLTextAreaElement | null {
  if (target instanceof HTMLTextAreaElement) return target.hasAttribute('data-allow-emoji') ? null : target
  if (target instanceof HTMLInputElement && TEXT_TYPES.has(target.type)) {
    return target.hasAttribute('data-allow-emoji') ? null : target
  }
  return null
}

export default defineNuxtPlugin(() => {
  document.addEventListener('input', (event) => {
    if ((event as InputEvent).isComposing) return // wait until the IME finishes
    const field = emojiFreeField(event.target)
    if (!field) return
    EMOJI.lastIndex = 0
    if (!EMOJI.test(field.value)) return
    const caret = field.selectionStart ?? field.value.length
    const before = field.value.slice(0, caret).replace(EMOJI, '')
    field.value = field.value.replace(EMOJI, '')
    try {
      field.setSelectionRange(before.length, before.length) // keep the cursor where it was
    } catch {
      // email inputs don't support selection ranges
    }
  }, true)
})
