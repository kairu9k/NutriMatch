// composables/useAppointments.js
//
// TODO: this is a mock, in-memory store. It resets on page refresh.
// Once the Django API exists, replace addAppointment()'s internals with a
// real POST call and hydrate `appointments` from the API on app load.
//
// Shared reactive state lives at module scope so RndProfile.vue (booking)
// and Appointments.vue (the list/history view) read and write the SAME
// array — booking a session from an RND's profile immediately shows up
// as a "Pending" row on the Appointments page, no reload needed.

import { ref } from 'vue'
import { useClientHistory } from './useClientHistory'

let nextId = 5

const appointments = ref([
  { id: 1, day: '04', month: 'Jul', rnd: 'RND Ivy Hope Alba', status: 'confirmed', dateLabel: 'Friday, July 4, 2026', timeLabel: '2:00 PM – 3:00 PM', modality: 'video' },
  { id: 2, day: '18', month: 'Jul', rnd: 'RND Ivy Hope Alba', status: 'pending', dateLabel: 'Saturday, July 18, 2026', timeLabel: '10:30 AM – 11:00 AM', modality: 'chat' },
  { id: 3, day: '15', month: 'Jun', rnd: 'RND Ivy Hope Alba', status: 'completed', dateLabel: 'Monday, June 15, 2026', timeLabel: '2:00 PM – 3:00 PM', modality: 'video' },
  { id: 4, day: '02', month: 'Jun', rnd: 'RND Ivy Hope Alba', status: 'cancelled', dateLabel: 'Tuesday, June 2, 2026', timeLabel: 'Cancelled by client', modality: 'chat' }
])

export function useAppointments() {
  // Called when a client sends a booking request from an RND's profile page.
  // Adds a new "pending" appointment at the top of the list.
  function addAppointment({ rndName, consultType, preferredDateTime, reason }) {
    let day = '--', month = '---', dateLabel = 'Date to be confirmed', timeLabel = 'Awaiting RND confirmation'
    if (preferredDateTime) {
      const d = new Date(preferredDateTime)
      day = String(d.getDate()).padStart(2, '0')
      month = d.toLocaleDateString('en-US', { month: 'short' })
      dateLabel = d.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
      timeLabel = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    }
    const modality = consultType === 'Video' ? 'video' : 'chat'

    appointments.value.unshift({
      id: nextId++,
      day, month,
      rnd: rndName,
      status: 'pending',
      dateLabel,
      timeLabel,
      modality,
      reason: reason || ''
    })

    const { addHistoryEvent } = useClientHistory()
    addHistoryEvent({
      type: 'appointment',
      title: `Appointment requested with ${rndName}`,
      detail: `${consultType} consultation · ${dateLabel}`
    })
  }

  return { appointments, addAppointment }
}