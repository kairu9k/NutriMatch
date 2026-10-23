// A short chime for new notifications and chat messages (2026-10-23, user's
// call). Our own three rising notes made with the Web Audio API, in the spirit
// of a phone's tri-tone: no audio file, nothing copyrighted.
//
// On/off is saved per device in localStorage (a shared clinic computer can be
// muted without touching the RND's phone); on by default. Browsers only allow
// sound after the person has clicked or typed on the page, so the audio
// context is created on the first interaction and the chime stays silent until
// then.
import { ref } from 'vue'

const KEY = 'nm-notification-sound'
const NOTES = [1046.5, 1318.5, 1568] // C6, E6, G6
const GAP = 0.1 // seconds between notes
const QUIET_MS = 1500 // several arrivals at once chime once

function readPref() {
  try {
    return localStorage.getItem(KEY) !== 'off'
  } catch {
    return true
  }
}

const enabled = ref(import.meta.client ? readPref() : true)
let ctx = null
let lastPlayed = 0
let unlockBound = false

function audio() {
  if (!import.meta.client) return null
  if (!ctx) {
    const AC = window.AudioContext || window.webkitAudioContext
    if (!AC) return null
    ctx = new AC()
  }
  if (ctx.state === 'suspended') ctx.resume().catch(() => {})
  return ctx
}

// Browsers block sound until a click/keypress: prepare the audio then.
function bindUnlock() {
  if (unlockBound || !import.meta.client) return
  unlockBound = true
  const unlock = () => {
    audio()
    window.removeEventListener('pointerdown', unlock)
    window.removeEventListener('keydown', unlock)
  }
  window.addEventListener('pointerdown', unlock)
  window.addEventListener('keydown', unlock)
}

function chime() {
  const ac = audio()
  if (!ac || ac.state !== 'running') return
  const start = ac.currentTime + 0.02
  NOTES.forEach((freq, i) => {
    const t = start + i * GAP
    const osc = ac.createOscillator()
    const gain = ac.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(freq, t)
    gain.gain.setValueAtTime(0.0001, t)
    gain.gain.exponentialRampToValueAtTime(0.14, t + 0.012)
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.32)
    osc.connect(gain).connect(ac.destination)
    osc.start(t)
    osc.stop(t + 0.34)
  })
}

export function useNotificationSound() {
  bindUnlock()

  // A new notification or message arrived: chime if it's on (and not just now).
  function play() {
    if (!enabled.value) return
    const now = Date.now()
    if (now - lastPlayed < QUIET_MS) return
    lastPlayed = now
    chime()
  }

  // "Play test sound" in settings: always plays (it's a click, so audio is allowed).
  function test() {
    audio()
    chime()
  }

  function setEnabled(on) {
    enabled.value = !!on
    try {
      localStorage.setItem(KEY, on ? 'on' : 'off')
    } catch {
      // private mode / storage blocked: the setting just won't be remembered
    }
  }

  return { enabled, play, test, setEnabled }
}
