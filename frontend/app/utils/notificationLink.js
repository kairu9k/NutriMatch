// Where a notification leads (2026-11-03, user's call: clicking a
// notification goes straight to that page, no detail pop-up).
// `related` is GET /api/notifications/<id>/ → related: a summary of the record
// it's about, or null when the record is gone or not the viewer's. With no
// record the click still lands on the main page for that kind of
// notification; null = nowhere to go (the row already shows the full text).

// Which RND Appointments tab a booking notification opens on.
const RND_APPT_TAB = { pending: 'requests', confirmed: 'upcoming', completed: 'history', cancelled: 'history' }

export function notificationLink(n, related, role, route) {
  const t = n.notifiable_type
  const r = related || null

  // Support: admins open the Support page, clients/RNDs the help panel
  // (?support=<id>, SupportWidget.vue) on the page they're on.
  if (t === 'support') {
    if (role === 'admin') return r ? { path: '/admin-support', query: { ticket: r.id } } : '/admin-support'
    return r ? { path: route.path, query: { ...route.query, support: r.id } } : null
  }

  if (role === 'admin') {
    return { invoice: '/billing-commission', appointment: '/admin-appointments', payout: '/payouts' }[t] || null
  }

  const chart = (tab) => (r?.relationship_id
    ? { path: `/client-detail/${r.relationship_id}`, query: tab ? { tab } : {} }
    : '/my-patients')
  const messages = { path: '/messages', query: r?.relationship_id ? { relationship: r.relationship_id } : {} }

  if (role === 'rnd') {
    if (t === 'appointment' && n.subject === 'New review') return '/reviews'
    switch (t) {
      case 'appointment': return { path: '/appointments', query: { tab: RND_APPT_TAB[r?.status] || 'upcoming' } }
      case 'invoice':
      case 'payout': return '/earnings'
      case 'message': return messages
      case 'meal_plan': return { path: '/meal-planning', query: r?.relationship_id ? { relationship: r.relationship_id } : {} }
      case 'meal_log': return r ? { path: `/client-detail/${r.relationship_id}`, query: { tab: 'meal', log: r.id } } : '/my-patients'
      case 'relationship': return chart()
      case 'lab_result':
      case 'lab_request': return chart('labs')
      default: return null
    }
  }

  // client
  switch (t) {
    case 'appointment': return '/appointments'
    case 'invoice': return '/invoices-billing'
    case 'message': return messages
    case 'meal_plan': return '/meal-plan-view'
    case 'resource': return '/resource-library'
    case 'lab_request':
    case 'lab_result': return '/lab-results'
    case 'reminder': return '/client-dashboard'
    case 'relationship': return !r || r.status === 'discharged' ? '/find-rnd' : '/client-dashboard'
    default: return null
  }
}
