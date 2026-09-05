import { ref } from 'vue'

// Frontend rani

//hide ra nako ang sulod na data temporary pwede siya e flase para makita ang data sa frontend
const HIDE_DATA = true

const rawRnds = [
  {
    id: 1,
    name: 'Dr. Mika Lim',
    initials: 'ML',
    color: 'bg-amber-400',
    license: 'PRC Lic. No. 0072341',
    specialty: 'Diabetes & Obesity',
    submitted: 'May 1, 2026',
    consultType: 'Video, Chat',
    status: 'pending'
  },
  {
    id: 2,
    name: 'Dr. Ivy Hope Alba',
    initials: 'IA',
    color: 'bg-amber-400',
    license: 'PRC Lic. No. 0072341',
    specialty: 'Weight Management',
    submitted: 'Today',
    consultType: 'Video, In-Person',
    status: 'pending'
  },
  {
    id: 3,
    name: 'Jhon Llyod Cruz, RND',
    initials: 'JC',
    color: 'bg-emerald-800',
    license: 'PRC Lic. No. 0081234',
    specialty: 'General Nutrition',
    submitted: 'Apr 30',
    consultType: 'Chat',
    status: 'pending'
  },
  {
    id: 4,
    name: 'Fridei Aguilar, RND',
    initials: 'RA',
    color: 'bg-indigo-700',
    license: 'PRC Lic. No. 0063201',
    specialty: 'Renal Nutrition',
    submitted: 'Apr 28',
    consultType: 'Video',
    status: 'pending'
  },
  {
    id: 5,
    name: 'RND Ivy Reyes',
    initials: 'AR',
    color: 'bg-emerald-800',
    license: 'PRC Lic. No. 0056789',
    specialty: 'Diabetes & Renal',
    verifiedOn: 'Mar 14, 2026',
    patients: 12,
    rating: 4.8,
    revenue: 15800,
    status: 'verified'
  },
  {
    id: 6,
    name: 'RND Ben Torres',
    initials: 'BT',
    color: 'bg-indigo-700',
    license: 'PRC Lic. No. 0049012',
    specialty: 'Hypertension & CVD',
    verifiedOn: 'Jan 8, 2026',
    patients: 8,
    rating: 4.5,
    revenue: 9400,
    status: 'verified'
  },
  {
    id: 7,
    name: 'RND Ivy Garcia',
    initials: 'PG',
    color: 'bg-red-600',
    license: 'PRC Lic. No. 0031872',
    specialty: 'Weight Management',
    status: 'suspended',
    suspendReason: 'Unresolved client complaint — Apr 10, 2026'
  }
]

const rawClients = [
  {
    id: 1,
    name: 'Kent Leabres',
    initials: 'KL',
    color: 'bg-emerald-800',
    email: 'kent.leabres@email.com',
    condition: 'Diabetes',
    status: 'Active',
    joined: 'Jan 14, 2026',
    consultations: 8,
    lastActive: 'Today',
    matched: 'RND Alba'
  },
  {
    id: 2,
    name: 'King Piolo Chui',
    initials: 'KP',
    color: 'bg-amber-400',
    email: 'king.chui@email.com',
    condition: 'Hypertension',
    status: 'Active',
    joined: 'Apr 15, 2026',
    consultations: 1,
    lastActive: 'Today',
    matched: 'RND Espantaleon'
  },
  {
    id: 3,
    name: 'Julia Niel Bulalaque',
    initials: 'JB',
    color: 'bg-amber-400',
    email: 'julia.bulalaque@email.com',
    condition: 'Hypertension',
    status: 'Active',
    joined: 'Apr 15, 2026',
    consultations: 1,
    lastActive: 'Today',
    matched: 'Felizarta'
  },
  {
    id: 4,
    name: 'Kim Taeyeon',
    initials: 'KT',
    color: 'bg-red-600',
    email: 'kim.taeyeon@email.com',
    condition: 'Unmatched',
    status: 'Flagged',
    matched: 'Multiple disputes',
    flagNote: 'Flagged: 3 unresolved payment disputes · Review needed'
  }
]

const rawTransactions = [
  { id: 1, from: 'Judy Santos', to: 'RND Reyes', date: 'May 1, 2026', mode: 'Video Consult · GCash', amount: 500, status: 'Settled' },
  { id: 2, from: 'Trisha Reyes', to: 'RND Alba', date: 'Apr 30, 2026', mode: 'In-Person · Cash', amount: 600, status: 'Settled' },
  { id: 3, from: 'Juan dela Cruz', to: 'RND Alba', date: 'Scheduled: May 1, 2026', mode: 'Chat', amount: 500, status: 'Pending' },
  { id: 4, from: 'Roberto Pascual', to: 'RND Alba', date: 'Apr 28, 2026', mode: 'Chat', amount: 400, status: 'Disputed' }
]

const rawAuditLogs = [
  { id: 1, title: 'NCP Record Submitted', detail: 'RND Ivy Reyes → Patient: Julia Niel Bulalaque · NCP ID: NCP-2026-0481', date: 'May 1, 2026 · 10:45 AM', ip: '175.45.12.88', tag: 'Clinical', color: 'border-emerald-700' },
  { id: 2, title: 'Payment Processed', detail: 'Julia Niel Bulalaque · ₱500 · GCash · TXN-2026-09913', date: 'May 1, 2026 · 9:30 AM', ip: '175.45.12.88', tag: 'Payment', color: 'border-amber-400' },
  { id: 3, title: 'RND Verification Request', detail: 'Dr. Mika Lim uploaded credentials · PRC Lic. 0072341', date: 'May 1, 2026 · 8:00 AM', ip: '122.54.89.10', tag: 'Verification', color: 'border-amber-400' },
  { id: 4, title: 'Failed Login Attempt (×3)', detail: 'Account: p.pascual@email.com · Brute force detected', date: 'Apr 30, 2026 · 11:22 PM', ip: '103.12.48.2', tag: 'Security', color: 'border-red-600', highlight: true },
  { id: 5, title: 'Admin Login', detail: 'System Administrator · Session started', date: 'Apr 30, 2026 · 8:05 AM', ip: '175.45.12.01', tag: 'Auth', color: 'border-blue-600' },
  { id: 6, title: 'Client Data Accessed', detail: 'RND Torres accessed NCP record of Ana Reyes', date: 'Apr 30, 2026 · 2:10 PM', ip: '120.88.41.19', tag: 'Data Access', color: 'border-purple-600' }
]

const rawNotifications = [
  { id: 1, initials: 'KM', color: 'bg-emerald-800', text: 'KM A. Murcia sent you a message', time: '9:12 AM today', unread: true },
  { id: 2, initials: 'CM', color: 'bg-amber-400', text: 'CJ R. Masudog requested a reschedule', time: '8:44 AM today', unread: true },
  { id: 3, initials: 'AD', color: 'bg-emerald-800', text: 'AiAi C. Dela sent you a message', time: 'Yesterday · 4:30 PM', unread: true },
  { id: 4, initials: 'AM', color: 'bg-indigo-700', text: "Anne P. Morales logged today's meal", time: 'Yesterday · 1:15 PM', unread: false },
  { id: 5, initials: 'LO', color: 'bg-amber-400', text: 'Luisa C. Onyok completed her weekly check-in', time: '2 days ago', unread: false }
]

const rawPlatformStats = {
  activeRnds: 24,
  clients: 187,
  pendingVerif: 3,
  commissions: 6820,
  newRegistrations: 14,
  totalConsultations: 312,
  grossRevenue: 68200,
  platformUptime: 99.8
}

const emptyPlatformStats = {
  activeRnds: 0,
  clients: 0,
  pendingVerif: 0,
  commissions: 0,
  newRegistrations: 0,
  totalConsultations: 0,
  grossRevenue: 0,
  platformUptime: 0
}

export const rnds = ref(HIDE_DATA ? [] : rawRnds)
export const clients = ref(HIDE_DATA ? [] : rawClients)
export const transactions = ref(HIDE_DATA ? [] : rawTransactions)
export const auditLogs = ref(HIDE_DATA ? [] : rawAuditLogs)
export const notifications = ref(HIDE_DATA ? [] : rawNotifications)
export const platformStats = ref(HIDE_DATA ? emptyPlatformStats : rawPlatformStats)

export const adminProfile = ref({
  displayName: 'System Administrator',
  email: 'admin@nutrimatch.ph',
  footerName: 'Elvi Lito Ubas',
  footerRole: 'System Ad'
})

// Mock admin credentials for frontend-only login.
// TODO (backend integration): replace this with a real API call
// (e.g. POST /api/admin/login) that verifies email + password
// and returns a session token instead of checking this object.
export const adminCredentials = ref({
  email: 'admin@nutrimatch.ph',
  password: 'Admin123!'
})