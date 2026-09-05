/**
 * MOCK DATABASE — single file, acts as your "database" until the Laravel
 * backend is connected. Import `db` anywhere you need fake data.
 *
 * USAGE:
 *   import { db } from '~/mock/mockDatabase'
 *   const patients = ref(db.patients)
 *
 * EMPTY STATE PREVIEW:
 *   Flip USE_EMPTY_STATE to true below, save, reload — every list becomes
 *   empty and every single-record object becomes null, so you can see what
 *   your layouts look like with zero data (new account, fresh signup, etc.)
 *   without deleting anything.
 *
 * SWITCHING TO THE REAL BACKEND LATER:
 *   Replace `ref(db.patients)` with a real fetch, e.g.
 *     const patients = ref([])
 *     onMounted(async () => {
 *       const { data } = await useFetch('/api/patients')
 *       patients.value = data.value
 *     })
 *   Field names already match what your components expect, so templates
 *   don't need to change — only where the array comes from.
 */

// ---------------------------------------------------------------------------
export const USE_EMPTY_STATE = true
// ---------------------------------------------------------------------------

function list(arr) {
  return USE_EMPTY_STATE ? [] : arr
}
function record(obj) {
  return USE_EMPTY_STATE ? null : obj
}

/* =========================================================================
   USERS (all roles)
========================================================================= */
const rnds = [
  {
    id: 'rnd-001',
    name: 'RND Ivy Hope Alba',
    initials: 'IA',
    role: 'rnd',
    specialty: 'Diabetes & Renal Specialist',
    specialization: 'Diabetes Management',
    prc: '0012345',
    verified: true,
    consultationFee: 800,
    acceptingClients: true,
    email: 'ivy.alba@nutrimatch.ph',
    avatarColor: '#D4A017'
  }
]

const clients = [
  { id: 'client-001', name: 'Juan Dela Cruz', initials: 'JD', role: 'client', email: 'juan.delacruz@email.com', avatarColor: '#1e4a26', assignedRnd: 'rnd-001' },
  { id: 'client-002', name: 'Roberto Manalo', initials: 'RM', role: 'client', email: 'roberto.manalo@email.com', avatarColor: '#3a6b3a', assignedRnd: 'rnd-001' },
  { id: 'client-003', name: 'Anna Lim', initials: 'AL', role: 'client', email: 'anna.lim@email.com', avatarColor: '#D4A017', assignedRnd: 'rnd-001' }
]

const admins = [
  { id: 'admin-001', name: 'Admin User', initials: 'AU', role: 'admin', email: 'admin@nutrimatch.ph', avatarColor: '#4a5a4a' }
]

function getCurrentUser(role = 'rnd') {
  if (USE_EMPTY_STATE) return null
  if (role === 'rnd') return rnds[0]
  if (role === 'client') return clients[0]
  if (role === 'admin') return admins[0]
  return null

}

/* =========================================================================
   RND: PATIENTS
========================================================================= */
const patients = [
  { id: 'client-001', name: 'Juan Dela Cruz', initials: 'JD', avatarColor: '#1e4a26', condition: 'Diabetes Mellitus', status: 'Active', lastVisit: 'Jun 15, 2026', nextAppointment: 'Jul 4, 2026', ncpPhase: 'Phase 3 (draft)', ncpStatus: 'Draft (Phase 3)', alert: null, alertLevel: null },
  { id: 'client-002', name: 'Roberto Manalo', initials: 'RM', avatarColor: '#3a6b3a', condition: 'Renal Disease', status: 'Active', lastVisit: 'Jun 20, 2026', nextAppointment: 'Jun 30, 2026', ncpPhase: 'Phase 4 (draft)', ncpStatus: 'Draft (Phase 4)', alert: null, alertLevel: null },
  { id: 'client-003', name: 'Anna Lim', initials: 'AL', avatarColor: '#D4A017', condition: 'Hypertension', status: 'Pending Screening', lastVisit: null, nextAppointment: 'Jun 30, 2026', ncpPhase: 'Not Started', ncpStatus: 'Not Started', alert: null, alertLevel: null },
  { id: 'client-004', name: 'Maria Santos', initials: 'MS', avatarColor: '#c9998a', condition: 'Diabetes', status: 'Active', lastVisit: 'Jun 1, 2026', nextAppointment: null, ncpPhase: 'Phase 4', ncpStatus: 'Phase 4', alert: 'HbA1c ↑', alertLevel: 'danger' },
  { id: 'client-005', name: 'John Reyes', initials: 'JR', avatarColor: '#D4A017', condition: 'Hypertension', status: 'Active', lastVisit: 'Jun 10, 2026', nextAppointment: null, ncpPhase: 'Phase 3', ncpStatus: 'Phase 3', alert: 'Low Adherence', alertLevel: 'warning' },
  { id: 'client-006', name: 'Kent Leabres', initials: 'KL', avatarColor: '#1e4a26', condition: 'Weight Management', status: 'Active', lastVisit: 'Jun 10, 2026', nextAppointment: 'Jul 10, 2026', ncpPhase: 'Completed', ncpStatus: 'Completed', alert: null, alertLevel: null },
  { id: 'client-007', name: 'Carlo Bautista', initials: 'CB', avatarColor: '#9aaa9a', condition: 'General Practice', status: 'Discharged', lastVisit: 'Apr 2, 2026', nextAppointment: null, ncpPhase: 'Completed', ncpStatus: 'Completed', alert: null, alertLevel: null, discharged: true }
]

const patientRequests = [
  { id: 'req-001', name: 'Maria Torres', initials: 'MT', avatarColor: '#1e4a26', requestedAt: 'Requested 4 hours ago' },
  { id: 'req-002', name: 'Edgar Pascual', initials: 'EP', avatarColor: '#D4A017', requestedAt: 'Requested yesterday' }
]

/* =========================================================================
   RND: APPOINTMENTS
========================================================================= */
const appointments = [
  { id: 1, day: '30', month: 'JUN', patientId: 'client-003', name: 'Anna Lim', initials: 'AL', avatarColor: '#D4A017', statusLabel: 'Awaiting Screening', statusClass: 'awaiting', status: 'Awaiting Screening', detail: 'Today, 4:00 PM – 4:30 PM · Chat', note: "Cannot confirm — client hasn't submitted pre-consultation screening yet." },
  { id: 2, day: '30', month: 'JUN', patientId: 'client-001', name: 'Juan Dela Cruz', initials: 'JD', avatarColor: '#1e4a26', statusLabel: 'Confirmed', statusClass: 'confirmed', status: 'Confirmed', detail: 'Today, 2:00 PM – 3:00 PM · Video', canStart: true, canViewChart: true },
  { id: 3, day: '04', month: 'JUL', patientId: 'client-002', name: 'Roberto Manalo', initials: 'RM', avatarColor: '#3a6b3a', statusLabel: 'Confirmed', statusClass: 'confirmed', status: 'Confirmed', detail: 'Saturday, Jul 4, 2026 · 10:00 AM – 11:00 AM · In-Person', canViewChart: true, canReschedule: true },
  { id: 4, day: '18', month: 'JUL', patientId: 'client-001', name: 'Juan Dela Cruz', initials: 'JD', avatarColor: '#1e4a26', statusLabel: 'Pending Your Confirmation', statusClass: 'pending', status: 'Pending Confirmation', detail: 'Saturday, Jul 18, 2026 · 10:30 AM – 11:00 AM · Chat', canConfirm: true },
  { id: 5, day: '15', month: 'JUN', patientId: 'client-001', name: 'Juan Dela Cruz', initials: 'JD', avatarColor: '#1e4a26', statusLabel: 'Completed', statusClass: 'completed', status: 'Completed', detail: 'Monday, Jun 15, 2026 · 2:00 PM – 3:00 PM · Video', canViewRecord: true }
]

const todaysSchedule = [
  { time: '9:00 AM', name: 'Roberto Manalo', detail: 'In-Person · Renal follow-up' },
  { time: '2:00 PM', name: 'Juan Dela Cruz', detail: 'Video · Diabetes review' },
  { time: '4:00 PM', name: 'Anna Lim', detail: 'Chat · New patient (screening pending)' }
]

/* =========================================================================
   RND: NCP RECORDS
========================================================================= */
const draftRecords = [
  { id: 'ncp-001', patientId: 'client-001', name: 'Juan Dela Cruz', initials: 'JD', avatarColor: '#1e4a26', phase: 'Phase 3', status: 'Intervention incomplete' },
  { id: 'ncp-002', patientId: 'client-002', name: 'Roberto Manalo', initials: 'RM', avatarColor: '#3a6b3a', phase: 'Phase 4', status: 'Monitoring incomplete' }
]

const ncpRecordFull = {
  id: 'ncp-001',
  patientId: 'client-001',
  patientName: 'Juan Dela Cruz',
  encounterDate: 'June 15, 2026',
  status: 'Draft',
  assessment: {
    weight: '68.2', height: '171', bloodPressure: '118/76', bloodGlucose: '112', hba1c: '6.8',
    labNotes: 'HbA1c drawn 6/10/2026 at Davao Medical Center. Lipid panel pending.',
    notes: 'Patient reports inconsistent meal timing, frequent skipping of breakfast. 24-hour recall shows high refined carbohydrate intake. No known food allergies aside from shellfish. Physical activity: light walking 2x/week.'
  },
  diagnosis: {
    problem: 'Inadequate carbohydrate intake management',
    etiology: 'poor dietary knowledge regarding diabetic exchange portions and inconsistent meal timing',
    signs: 'elevated fasting blood glucose (126 mg/dL), HbA1c of 6.8%, and irregular meal pattern reported in 24-hour recall'
  },
  intervention: {
    dietPrescription: '1,800 kcal diabetic exchange diet, low glycemic index focus, consistent carbohydrate distribution across 3 meals + 2 snacks. FNRI Food Exchange List-based meal planning.',
    kcal: '1800', protein: '90', carbs: '225', fat: '60',
    notes: 'Educated patient on FNRI Food Exchange List portion sizes using visual food models. Discussed strategies to avoid skipping breakfast. Set a behavioral goal of logging meals daily via food diary for the next 2 weeks. Linked patient to "Managing Carb Cravings" resource article.',
    linkedPlan: 'Diabetic-Friendly Plan (1,800 kcal)'
  },
  monitoring: {
    goalStatus: 'Partially Met',
    notes: 'Patient has reduced fasting glucose from 126 to 112 mg/dL over 4 weeks, indicating partial progress toward glycemic goals. Food diary adherence improved to 5/7 days. Breakfast skipping has decreased but not fully resolved. Recommend continued reinforcement of meal timing at next follow-up (Jul 4, 2026) and re-check of HbA1c in 3 months.'
  }
}

const healthOutcomes = [
  { label: 'Weight Loss Avg.', value: '-2.8 kg', color: 'olive' },
  { label: 'HbA1c Reduction', value: '-0.6%', color: 'green' },
  { label: 'BP Improvement (mmHg)', value: '-8/-5', color: 'blue' },
  { label: 'Goal Met Rate', value: '78%', color: 'gold' }
]

const clinicalAlerts = [
  { patientId: 'client-004', name: 'Maria Santos', issue: 'HbA1c above target', detail: 'Latest: 8.1% (target <7%). Needs intervention adjustment.', level: 'level-danger', actionLabel: 'Review', link: '/ncp-records' },
  { patientId: 'client-005', name: 'John Reyes', issue: 'Low meal adherence', detail: 'Only 2/5 meal logs this week. Send motivational message.', level: 'level-warning', actionLabel: 'Message', link: '/messages' },
  { patientId: null, name: 'Rosa Fernandez', issue: 'Overdue follow-up', detail: 'Last consultation 4 weeks ago. Schedule Phase 4 monitoring.', level: 'level-warning', actionLabel: 'Schedule', link: '/appointments' }
]

/* =========================================================================
   RND: MEAL PLANS
========================================================================= */
const mealPlans = [
  { id: 'mp-001', patientId: 'client-001', name: 'Juan Dela Cruz', initials: 'JD', avatarColor: '#1e4a26', diet: 'Diabetic-Friendly', kcal: '1,800', status: 'Active' },
  { id: 'mp-002', patientId: 'client-002', name: 'Roberto Manalo', initials: 'RM', avatarColor: '#3a6b3a', diet: 'Renal Diet', kcal: '1,600', status: 'Active' }
]

const emptyDay = () => ({
  Breakfast: { time: '7:00 AM', items: [] },
  'Morning Snack': { time: '10:00 AM', items: [] },
  Lunch: { time: '12:00 PM', items: [] },
  'Afternoon Snack': { time: '3:30 PM', items: [] },
  Dinner: { time: '6:30 PM', items: [] }
})

const mealPlanDetailsFull = [
  {
    patientId: 'client-004', // Maria Santos
    planName: 'Week 1 Low GI',
    dietType: 'Low GI',
    kcalTarget: 1600,
    carbTarget: 200,
    proteinTarget: 80,
    fatTarget: 53,
    allergies: '',
    notes: '',
    week: {
      Mon: {
        Breakfast: { time: '7:00 AM', items: [{ name: 'Egg', portion: '1', kcal: 78, carb: 1, prot: 6, fat: 5 }] },
        'Morning Snack': { time: '10:00 AM', items: [{ name: 'Bread', portion: '5', kcal: 70, carb: 2, prot: 3, fat: 6 }] },
        Lunch: { time: '12:00 PM', items: [{ name: 'Sinigang', portion: '2', kcal: 30, carb: 1, prot: 4, fat: 0 }] },
        'Afternoon Snack': { time: '3:30 PM', items: [] },
        Dinner: { time: '6:30 PM', items: [] }
      },
      Tue: emptyDay(), Wed: emptyDay(), Thu: emptyDay(), Fri: emptyDay(), Sat: emptyDay(), Sun: emptyDay()
    }
  },
  {
    patientId: 'client-001', // Juan Dela Cruz
    planName: 'Diabetic-Friendly Plan',
    dietType: 'Low GI',
    kcalTarget: 1800,
    carbTarget: 225,
    proteinTarget: 90,
    fatTarget: 60,
    allergies: '',
    notes: 'Substitute brown rice with cauliflower rice on days with higher fasting glucose readings.',
    week: {
      Mon: {
        Breakfast: { time: '7:00 AM', items: [
          { name: 'Brown Rice', portion: '1 cup', kcal: 216, carb: 45, prot: 5, fat: 2 },
          { name: 'Fried Egg', portion: 'small', kcal: 90, carb: 0, prot: 6, fat: 7 }
        ] },
        'Morning Snack': { time: '10:00 AM', items: [
          { name: 'Banana (Saba)', portion: 'small', kcal: 90, carb: 23, prot: 1, fat: 0 }
        ] },
        Lunch: { time: '12:00 PM', items: [
          { name: 'Grilled Tilapia', portion: 'medium', kcal: 180, carb: 0, prot: 30, fat: 6 }
        ] },
        'Afternoon Snack': { time: '3:30 PM', items: [] },
        Dinner: { time: '6:30 PM', items: [
          { name: 'Chicken Tinola', portion: '1 piece', kcal: 160, carb: 5, prot: 22, fat: 5 }
        ] }
      },
      Tue: emptyDay(), Wed: emptyDay(), Thu: emptyDay(), Fri: emptyDay(), Sat: emptyDay(), Sun: emptyDay()
    }
  }
]

const mealPlanDetailsEmpty = []

/* =========================================================================
   RND: RESOURCES
========================================================================= */
const resources = [
  { id: 'res-001', title: 'FNRI Food Exchange List Guide', description: 'Complete reference for 4th edition FNRI exchange categories.', type: 'PDF', status: 'Active', uploadedAt: '2 days ago' },
  { id: 'res-002', title: 'Reading Nutrition Labels', description: '6-minute walkthrough video.', type: 'Video', status: 'Active', uploadedAt: '5 days ago' },
  { id: 'res-003', title: 'Managing Carb Cravings', description: 'Practical strategies article.', type: 'Article', status: 'Active', uploadedAt: '1 week ago' },
  { id: 'res-004', title: 'DOH Pinggang Pinoy Guide', description: 'External link to official DOH resource.', type: 'Link', status: 'Inactive', uploadedAt: '3 weeks ago' }
]

const resourcesEmpty = []

/* =========================================================================
   RND: EARNINGS & INVOICES
========================================================================= */
const earningsSummaryFull = {
  thisMonthNet: 18400,
  monthlyGoal: 42000,
  gross: 23200,
  commission: 2320,
  net: 20880,
  pending: 800,
  billableSessionsThisMonth: 18
}

const earningsSummaryEmpty = {
  thisMonthNet: 0, monthlyGoal: 42000, gross: 0, commission: 0, net: 0, pending: 0, billableSessionsThisMonth: 0
}
/* =========================================================================
   RND: EARNINGS TREND (last 6 months, for the bar chart)
========================================================================= */
const earningsTrendFull = [
  { month: 'Feb', amount: 12400 },
  { month: 'Mar', amount: 14100 },
  { month: 'Apr', amount: 13200 },
  { month: 'May', amount: 15600 },
  { month: 'Jun', amount: 15900 },
  { month: 'Jul', amount: 18400 }
]

const earningsTrendEmpty = []

const invoices = [
  { id: 'INV-0231', patientId: 'client-001', patient: 'Juan Dela Cruz', date: 'Jul 4', gross: 800, commission: 80, net: 720, status: 'Pending' },
  { id: 'INV-0214', patientId: 'client-001', patient: 'Juan Dela Cruz', date: 'Jun 15', gross: 800, commission: 80, net: 720, status: 'Paid' },
  { id: 'INV-0209', patientId: 'client-002', patient: 'Roberto Manalo', date: 'Jun 12', gross: 900, commission: 90, net: 810, status: 'Paid' }
]

/* =========================================================================
   RND: SETTINGS
========================================================================= */
const rndSettings = {
  specialization: 'Diabetes Management',
  fee: '800',
  acceptingClients: true
}

const notificationPrefs = [
  { key: 'new_patient_requests', label: 'New patient requests', enabled: true },
  { key: 'appointment_reminders', label: 'Appointment reminders', enabled: true },
  { key: 'new_messages', label: 'New messages', enabled: true }
]

/* =========================================================================
   RND: PROFILE — PERSONAL INFO
========================================================================= */
const personalInfoFull = {
  firstName: 'Ivy Hope',
  lastName: 'Alba',
  email: 'rnd@test.ph',
  phone: '0918 234 5678',
  initials: 'IA',
  avatarColor: '#1e4a26',
  prcVerified: true
}
 
const personalInfoEmpty = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  initials: '',
  avatarColor: '#1e4a26',
  prcVerified: false
}

/* =========================================================================
   CLIENT: MESSAGES
========================================================================= */
// const conversationsFull = [
//   {
//     id: 'conv-001',
//     participantId: 'rnd-001',
//     name: 'RND Ivy Hope Alba',
//     initials: 'IA',
//     avatarColor: '#1e4a26',
//     online: true,
//     lastMessage: "Let's review your glucose readi...",
//     lastMessageAt: '2m',
//     unread: 0
//   },
//   {
//     id: 'conv-002',
//     participantId: null,
//     name: 'NutriMatch Support',
//     initials: 'NM',
//     avatarColor: '#D4A017',
//     online: false,
//     lastMessage: 'Your invoice #INV-0231 is ready.',
//     lastMessageAt: '2d',
//     unread: 0
//   }
// ]
 
// const conversationsEmpty = []
 
// const messagesByConversationFull = {
//   'conv-001': [
//     { id: 'msg-001', sender: 'them', text: 'Hi Juan! I can see your screening results. Your BMI looks great this month.', time: '9:02 AM' },
//     { id: 'msg-002', sender: 'me', text: "Thank you po! I've been following the meal plan closely.", time: '9:05 AM' },
//     { id: 'msg-003', sender: 'them', text: "That's wonderful to hear. Let's review your glucose readings from the past two weeks during our video call on Friday.", time: '9:06 AM' },
//     { id: 'msg-004', sender: 'me', text: "Sounds good! I'll have my logbook ready.", time: '9:08 AM' }
//   ],
//   'conv-002': [
//     { id: 'msg-005', sender: 'them', text: 'Your invoice #INV-0231 is ready. You can view it under Billing.', time: '10:14 AM' }
//   ]
// }
 
// const messagesByConversationEmpty = {}

/* =========================================================================
   CLIENT ROLE (for when you build client-facing pages)
========================================================================= */
const clientProfileFull = {
  id: 'client-001',
  name: 'Juan Dela Cruz',
  initials: 'JD',
  condition: 'Diabetes Mellitus',
  assignedRnd: { id: 'rnd-001', name: 'RND Ivy Hope Alba', specialty: 'Diabetes & Renal Specialist' }
}

const clientAppointments = [
  { id: 2, date: 'Today, Jun 30, 2026', time: '2:00 PM – 3:00 PM', type: 'Video', status: 'Confirmed', withRnd: 'RND Ivy Hope Alba' },
  { id: 4, date: 'Saturday, Jul 18, 2026', time: '10:30 AM – 11:00 AM', type: 'Chat', status: 'Pending Confirmation', withRnd: 'RND Ivy Hope Alba' }
]

const clientMealPlanFull = {
  name: 'Diabetic-Friendly Plan',
  kcal: 1800,
  status: 'Active',
  meals: [
    { name: 'Breakfast', items: ['1 cup brown rice', '1 exchange lean protein', '1 exchange vegetables'] },
    { name: 'Lunch', items: ['1 cup brown rice', '2 exchanges lean protein', '2 exchanges vegetables'] },
    { name: 'Dinner', items: ['1 cup brown rice', '2 exchanges lean protein', '1 exchange vegetables'] },
    { name: 'Snacks (x2)', items: ['1 exchange fruit', '1 exchange milk/dairy'] }
  ]
}

const clientProgress = [
  { date: 'May 20, 2026', weight: 71.0, bloodGlucose: 126, hba1c: null },
  { date: 'Jun 3, 2026', weight: 70.1, bloodGlucose: 118, hba1c: null },
  { date: 'Jun 15, 2026', weight: 68.2, bloodGlucose: 112, hba1c: 6.8 }
]

/* =========================================================================
   RND: REVIEWS
========================================================================= */
const reviewsSummaryFull = {
  average: 4.9,
  total: 38
}
 
const reviewsSummaryEmpty = {
  average: 0,
  total: 0
}
 
// Star breakdown for the bar chart (5 -> 1)
const ratingBreakdownFull = [
  { stars: 5, count: 31 },
  { stars: 4, count: 5 },
  { stars: 3, count: 2 },
  { stars: 2, count: 0 },
  { stars: 1, count: 0 }
]
 
const ratingBreakdownEmpty = [
  { stars: 5, count: 0 },
  { stars: 4, count: 0 },
  { stars: 3, count: 0 },
  { stars: 2, count: 0 },
  { stars: 1, count: 0 }
]
 
const reviews = [
  {
    id: 'rev-001',
    patientId: null,
    name: 'Julia Niel',
    initials: 'JN',
    avatarColor: '#1e4a26',
    rating: 5,
    postedAt: '2 days ago',
    comment: "NutriMatch helped me find an RND who speaks Cebuano and truly understands my diabetes. I feel heard for the first time."
  },
  {
    id: 'rev-002',
    patientId: 'client-002',
    name: 'Roberto Manalo',
    initials: 'RM',
    avatarColor: '#3a6b3a',
    rating: 5,
    postedAt: '1 week ago',
    comment: "Very thorough during my initial screening. Explained my NRS score and BMI in terms I could actually understand."
  },
  {
    id: 'rev-003',
    patientId: 'client-003',
    name: 'Anna Lim',
    initials: 'AL',
    avatarColor: '#D4A017',
    rating: 4,
    postedAt: '3 weeks ago',
    comment: "Great meal plan, very practical for everyday Filipino cooking. Wish video sessions ran a bit longer."
  }
]

/* =========================================================================
   ADMIN ROLE (for when you build admin-facing pages)
========================================================================= */
const adminStatsFull = {
  totalRnds: 24,
  totalClients: 312,
  pendingRndVerifications: 3,
  totalAppointmentsThisMonth: 486,
  platformRevenueThisMonth: 412000
}

const adminStatsEmpty = {
  totalRnds: 0, totalClients: 0, pendingRndVerifications: 0, totalAppointmentsThisMonth: 0, platformRevenueThisMonth: 0
}

const pendingRndVerifications = [
  { id: 'rnd-010', name: 'RND Carla Dizon', prc: '0019456', submittedAt: 'Jul 15, 2026', specialty: 'Pediatric Nutrition' },
  { id: 'rnd-011', name: 'RND Miguel Torres', prc: '0021873', submittedAt: 'Jul 16, 2026', specialty: 'Sports Nutrition' }
]

const reportedIssues = [
  { id: 'issue-001', reporter: 'Juan Dela Cruz', against: 'N/A', type: 'Billing dispute', status: 'Open', submittedAt: 'Jul 14, 2026' }
]

/* =========================================================================
   RND: AVAILABILITY
========================================================================= */
const weeklyAvailabilityFull = [
  { day: 'Monday', blocked: false, slots: [{ id: 's1', start: '9:00 AM', end: '5:00 PM' }] },
  { day: 'Tuesday', blocked: false, slots: [{ id: 's2', start: '9:00 AM', end: '5:00 PM' }] },
  { day: 'Wednesday', blocked: true, slots: [] },
  { day: 'Thursday', blocked: false, slots: [{ id: 's3', start: '1:00 PM', end: '6:00 PM' }] },
  { day: 'Friday', blocked: false, slots: [
    { id: 's4', start: '9:00 AM', end: '12:00 PM' },
    { id: 's5', start: '1:00 PM', end: '5:00 PM' }
  ] },
  { day: 'Saturday', blocked: false, slots: [{ id: 's6', start: '9:00 AM', end: '12:00 PM' }] },
  { day: 'Sunday', blocked: true, slots: [] }
]

// Empty state keeps all 7 days (they're structural, not mock content) but
// with no slots and nothing blocked — a genuinely fresh, unconfigured week.
const weeklyAvailabilityEmpty = [
  { day: 'Monday', blocked: false, slots: [] },
  { day: 'Tuesday', blocked: false, slots: [] },
  { day: 'Wednesday', blocked: false, slots: [] },
  { day: 'Thursday', blocked: false, slots: [] },
  { day: 'Friday', blocked: false, slots: [] },
  { day: 'Saturday', blocked: false, slots: [] },
  { day: 'Sunday', blocked: false, slots: [] }
]

const blockedDaysOff = [
  { id: 'off-001', from: '2026-08-10', to: '2026-08-14', reason: 'Annual leave' }
]


/* =========================================================================
   EXPORTED DATABASE OBJECT
========================================================================= */
export const db = {
  // Users
  rnds: list(rnds),
  clients: list(clients),
  admins: list(admins),
  getCurrentUser,

   // RND: Reviews
  reviewsSummary: USE_EMPTY_STATE ? reviewsSummaryEmpty : reviewsSummaryFull,
  ratingBreakdown: USE_EMPTY_STATE ? ratingBreakdownEmpty : ratingBreakdownFull,
  reviews: list(reviews),

  // RND Weekly Availability
  weeklyAvailabilityFull: list(weeklyAvailabilityFull),
  weeklyAvailabilityEmpty: list(weeklyAvailabilityEmpty),
  blockedDaysOff: list(blockedDaysOff),

  // RND: Patients
  patients: list(patients),
  patientRequests: list(patientRequests),

  // RND: Appointments
  appointments: list(appointments),
  todaysSchedule: list(todaysSchedule),

  // RND: NCP Records
  draftRecords: list(draftRecords),
  ncpRecord: record(ncpRecordFull),
  healthOutcomes: list(healthOutcomes),
  clinicalAlerts: list(clinicalAlerts),

  // RND: Meal Plans
  mealPlans: list(mealPlans),
  // RND: Meal Plans
  mealPlanDetails: USE_EMPTY_STATE ? mealPlanDetailsEmpty : mealPlanDetailsFull,  // full builder data (Meal Plans page)

  // RND: Resources
 resources: USE_EMPTY_STATE ? resourcesEmpty : resources,

  // RND: Earnings
  earningsSummary: USE_EMPTY_STATE ? earningsSummaryEmpty : earningsSummaryFull,
 
    // RND: Earnings
  earningsSummary: USE_EMPTY_STATE ? earningsSummaryEmpty : earningsSummaryFull,
  earningsTrend: USE_EMPTY_STATE ? earningsTrendEmpty : earningsTrendFull,
  invoices: list(invoices),

  // RND: Settings
  rndSettings,
  notificationPrefs: list(notificationPrefs),

   // RND: Profile
  personalInfo: USE_EMPTY_STATE ? personalInfoEmpty : personalInfoFull,

   // Client: Messages
  // conversations: USE_EMPTY_STATE ? conversationsEmpty : conversationsFull,
  // messagesByConversation: USE_EMPTY_STATE ? messagesByConversationEmpty : messagesByConversationFull,

  // Client role
  clientProfile: record(clientProfileFull),
  clientAppointments: list(clientAppointments),
  clientMealPlan: record(clientMealPlanFull),
  clientProgress: list(clientProgress),

  // Admin role
  adminStats: USE_EMPTY_STATE ? adminStatsEmpty : adminStatsFull,
  pendingRndVerifications: list(pendingRndVerifications),
  reportedIssues: list(reportedIssues)
}

export default db