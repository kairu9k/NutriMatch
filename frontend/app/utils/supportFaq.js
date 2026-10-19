// Quick answers in the Help & Support panel (SupportWidget.vue), per role.
// Keep these in step with how the app actually works (see CLAUDE.md).
export const SUPPORT_CATEGORIES = [
  { value: 'payment', label: 'Payment or refund' },
  { value: 'appointment', label: 'Appointment' },
  { value: 'account', label: 'Account' },
  { value: 'report', label: 'Report a user' },
  { value: 'technical', label: 'Technical problem' },
  { value: 'other', label: 'Other' },
]

export const SUPPORT_FAQ = {
  client: [
    {
      q: 'How do I book a consultation?',
      a: 'Open Find an RND, pick a dietitian and press Book. Choose an open time and the format (video call or in person). Your RND confirms the booking, and then you can pay.',
      link: { label: 'Find an RND', to: '/find-rnd' },
    },
    {
      q: 'When and how do I pay?',
      a: 'Pay any time after your RND confirms and before the consultation starts — on Billing & Invoice or from My Appointments. GCash, Maya, cards and QR Ph work through PayMongo. A consultation that is still unpaid when it starts is cancelled automatically.',
      link: { label: 'Billing & Invoice', to: '/invoices-billing' },
    },
    {
      q: 'How do I join my video consultation?',
      a: 'The Join button appears on My Appointments 15 minutes before the start, once the consultation is paid. Allow your camera and microphone when the browser asks. The room stays open until 15 minutes after the scheduled end.',
      link: { label: 'My Appointments', to: '/appointments' },
    },
    {
      q: 'Can I cancel, and will I get a refund?',
      a: 'You can cancel a pending or confirmed consultation from My Appointments. If you already paid, you get the full amount back within 5–7 business days. Paid with GCash, Maya or a card? It goes back to the same account. Paid with QR Ph? We send you a PayMongo link to claim it to your bank or e-wallet — the link works for 3 days.',
    },
    {
      q: 'Where do I find my meal plan and log my meals?',
      a: 'My Meal Plan shows the plan your RND sent. Log each meal there (followed, partly followed or not followed, with an optional photo) — your RND sees your logs.',
      link: { label: 'My Meal Plan', to: '/meal-plan-view' },
    },
    {
      q: 'How do I upload my lab results?',
      a: 'When your RND requests lab tests, it shows on your dashboard and in Lab Results, needed before your next consultation. Choose the file (PDF, JPG or PNG, up to 10 MB) or take a photo, then say which tests it has, the date taken and whether you fasted. Your RND sees it right away. You can also upload results you already have. Only you and your RND can open them.',
      link: { label: 'Lab Results', to: '/lab-results' },
    },
    {
      q: 'Who can see my health information?',
      a: 'Only the RNDs you consult with and authorized NutriMatch admins, under the Data Privacy Act (RA 10173). Admin access to health records is logged.',
      link: { label: 'Privacy Policy', to: '/privacy-policy' },
    },
  ],
  rnd: [
    {
      q: 'How do I confirm or decline a booking?',
      a: 'New bookings are under Appointments → Requests, with the patient’s screening summary. Confirm to issue the invoice; declining needs a short reason, which the patient sees.',
      link: { label: 'Appointments', to: '/appointments?tab=requests' },
    },
    {
      q: 'When do I get paid?',
      a: 'Your share (fee minus the platform commission) is Pending until the consultation is completed, then Posted 3 days later. Posted balances are released on or after the 5th of each month once they reach ₱500, to the GCash or bank account in your payout details.',
      link: { label: 'Earnings', to: '/earnings' },
    },
    {
      q: 'Why can’t I mark a consultation complete?',
      a: 'A consultation can only be completed after the patient has paid and the scheduled time has started. If it’s unpaid, the patient sees a reminder to pay before the start time.',
    },
    {
      q: 'How do I write and finalize an NCP record?',
      a: 'Open the patient’s chart → NCP Records (or the NCP tab in the consultation room). Save a draft any time; Finalize is on the Review step once the required fields are in. A finalized record can’t be edited.',
      link: { label: 'My Patients', to: '/my-patients' },
    },
    {
      q: 'How do I request lab tests?',
      a: 'Open the patient’s chart → Request lab tests, tick the tests and add a note. They’re needed before the patient’s next consultation. Uploads appear in the chart’s Lab results tab (and in the consultation room) as soon as the patient sends them; opening one marks it reviewed. Type the values into the NCP record yourself.',
      link: { label: 'My Patients', to: '/my-patients' },
    },
    {
      q: 'How do I send a meal plan?',
      a: 'Meal Plans → pick the patient → start from a diet template or build the week yourself (FNRI foods, or USDA foods by grams), then Send to patient.',
      link: { label: 'Meal Plans', to: '/meal-planning' },
    },
    {
      q: 'How do I change my availability or fee?',
      a: 'Profile Settings → Professional Profile and Availability. Patients only see open times inside your weekly hours.',
      link: { label: 'Profile Settings', to: '/profile-settings' },
    },
  ],
}
