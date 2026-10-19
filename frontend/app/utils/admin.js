// Formatting helpers shared by the admin pages (auto-imported by Nuxt).

export function peso(v) {
  const n = Number(v || 0)
  return `₱${n.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export function shortDate(v) {
  if (!v) return '—'
  const d = /^\d{4}-\d{2}-\d{2}$/.test(v) ? new Date(`${v}T00:00:00`) : new Date(v)
  return d.toLocaleDateString('en-PH', { month: 'short', day: 'numeric', year: 'numeric' })
}

export function dateTime(v) {
  if (!v) return '—'
  return new Date(v).toLocaleString('en-PH', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' })
}

export function userInitials(first, last) {
  return `${first?.[0] || ''}${last?.[0] || ''}`.toUpperCase() || '?'
}

export function ageFrom(dob) {
  if (!dob) return null
  const d = new Date(`${dob}T00:00:00`)
  const now = new Date()
  let age = now.getFullYear() - d.getFullYear()
  if (now.getMonth() < d.getMonth() || (now.getMonth() === d.getMonth() && now.getDate() < d.getDate())) age--
  return age
}

// Audit-log action codes → plain words.
export const AUDIT_ACTIONS = {
  'consent.given': 'Gave data-privacy consent',
  'login.failed': 'Failed sign-in',
  'invoice.paid': 'Invoice paid',
  'invoice.refunded': 'Invoice refunded',
  'payout.released': 'Payout released',
  'payout_account.updated': 'Payout details updated',
  'rnd.approved': 'RND application approved',
  'rnd.rejected': 'RND application rejected',
  'setting.updated': 'System setting changed',
  'user.deactivated': 'Account deactivated',
  'user.reactivated': 'Account reactivated',
  'user.password_reset_sent': 'Password reset sent',
  'user.removed': 'Account removed',
  'client.record_viewed': 'Client health record viewed',
  'audit_log.exported': 'Audit log exported',
  'appointment.cancelled': 'Appointment cancelled by admin',
  'lab_request.created': 'Lab tests requested',
  'lab_request.cancelled': 'Lab request cancelled',
  'lab_result.uploaded': 'Lab result uploaded',
  'lab_result.viewed': 'Lab result viewed by RND',
  'lab_result.deleted': 'Lab result deleted',
  'audit_log.reset': 'Audit log reset (test data removed)',
  'admin.created': 'Admin account added',
  'user.updated': 'Account details edited',
  'password.changed': 'Password changed',
  'invoice.refund_requested': 'Refund sent to PayMongo',
  'relationship.discharged': 'Client discharged',
  'relationship.discharge_requested': 'Client asked to be discharged',
  'ncp_record.deleted': 'NCP draft deleted',
  'meal_plan.deleted': 'Meal plan draft deleted',
}

export function auditLabel(action) {
  if (AUDIT_ACTIONS[action]) return AUDIT_ACTIONS[action]
  const text = String(action || '').replace(/[._]/g, ' ')
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export const DAY_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
export const MODE_LABELS = { video: 'Video call', in_person: 'In-person' }

export function clock12(t) {
  const [h, m] = String(t).split(':').map(Number)
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`
}

// [{day_of_week, start_time, end_time}] → ["Monday: 9:00 AM – 5:00 PM", …], Monday first.
export function availabilityLines(blocks) {
  const byDay = {}
  for (const b of blocks || []) (byDay[b.day_of_week] ||= []).push(`${clock12(b.start_time)} – ${clock12(b.end_time)}`)
  return [1, 2, 3, 4, 5, 6, 0].filter(d => byDay[d]).map(d => `${DAY_NAMES[d]}: ${byDay[d].join(', ')}`)
}

export function apiError(e, fallback = 'Something went wrong. Please try again.') {
  const data = e?.data || e?.response?._data
  if (!data) return fallback
  if (typeof data === 'string') return fallback
  if (data.detail) return data.detail
  const first = Object.values(data)[0]
  return Array.isArray(first) ? first[0] : (typeof first === 'string' ? first : fallback)
}
