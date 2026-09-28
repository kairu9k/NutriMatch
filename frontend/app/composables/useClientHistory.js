// TODO: mock/local only — no client-activity-history endpoint exists yet
// (screenings, appointments, and meal logs are each their own real API
// resource, but there's no unified timeline). Once one exists, replace
// addHistoryEvent()'s internals with a real POST/GET and hydrate
// `historyLog` from the API on app load instead of starting empty.
//
// Shared reactive state lives at module scope (outside the exported
// function) so every component that calls useClientHistory() reads and
// writes the SAME ref — this is what lets the Dashboard's "Recent Activity"
// panel and the History page agree without a page reload in between.

import { ref } from 'vue'

const historyLog = ref([])
let nextId = 1

export function useClientHistory() {
  function addHistoryEvent({ type, title, detail }) {
    historyLog.value.unshift({
      id: nextId++,
      type, // 'screening' | 'appointment' | 'mealLog'
      title,
      detail,
      timestamp: new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }),
    })
  }

  return { historyLog, addHistoryEvent }
}
