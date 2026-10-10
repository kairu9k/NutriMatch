// A `now` timestamp (ms) that ticks every `intervalMs`, so time-based UI —
// e.g. the consultation join window — updates without a page reload.
import { onBeforeUnmount, onMounted, ref } from 'vue'

export function useNow(intervalMs = 30000) {
  const now = ref(Date.now())
  let timer = null
  onMounted(() => { timer = setInterval(() => { now.value = Date.now() }, intervalMs) })
  onBeforeUnmount(() => clearInterval(timer))
  return now
}

// "8:45 AM" today, "tomorrow, 8:45 AM", otherwise "Mon, Oct 12, 8:45 AM".
export function formatJoinTime(date, nowMs = Date.now()) {
  const d = new Date(date)
  const time = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
  const today = new Date(nowMs)
  const tomorrow = new Date(nowMs + 86400000)
  if (d.toDateString() === today.toDateString()) return time
  if (d.toDateString() === tomorrow.toDateString()) return `tomorrow, ${time}`
  return `${d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}, ${time}`
}
