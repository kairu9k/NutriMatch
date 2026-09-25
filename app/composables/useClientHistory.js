// composables/useClientHistory.js
//
// TODO: this is a mock, in-memory store. It resets on page refresh.
// Once the Django API exists, replace addHistoryEvent()'s internals with
// a real POST call and hydrate `historyLog` from the API on app load.
//
// Single shared timeline that useClientScreening, useAppointments, and
// useMealLogs all feed into — this is the ONE place to check that
// something was actually saved, instead of hunting across three pages.

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
      timestamp: new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
    })
  }

  return { historyLog, addHistoryEvent }
}