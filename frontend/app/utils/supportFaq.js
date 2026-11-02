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
      a: 'Pay any time after your RND confirms, at least 15 minutes before the start, on Billing & Invoice or from My Appointments. GCash, Maya, cards and QR Ph work through PayMongo. A consultation that is still unpaid 15 minutes before the start is cancelled automatically.',
      link: { label: 'Billing & Invoice', to: '/invoices-billing' },
    },
    {
      q: 'How do I join my video consultation?',
      a: 'The Join button appears on My Appointments 15 minutes before the start, once the consultation is paid. Allow your camera and microphone when the browser asks. The room stays open until 15 minutes after the scheduled end.',
      link: { label: 'My Appointments', to: '/appointments' },
    },
    {
      q: 'Can I cancel, and will I get a refund?',
      a: 'From My Appointments you can withdraw a booking request until your RND confirms it, cancel an unpaid consultation at no cost, and cancel a paid one up to 30 minutes before the start for the full amount back within 5–7 business days. After that it can’t be cancelled. Paid with GCash, Maya or a card? It goes back to the same account. Paid with QR Ph? We send you a PayMongo link to claim it to your bank or e-wallet. The link works for 3 days.',
    },
    {
      q: 'What if I miss my consultation, or my RND does?',
      a: 'If you don’t attend a paid consultation, your RND can mark it as a no-show and it isn’t refunded. If that’s wrong, press Dispute on it in My Appointments, History, within 3 days: NutriMatch checks the video call’s attendance record (only who joined and when) and refunds you or keeps the no-show. If you joined the video call and your RND still hasn’t 15 minutes after the start, you can report it from the call and get a full refund. If your RND has an emergency and cancels, you also get the full amount back.',
      link: { label: 'My Appointments', to: '/appointments' },
    },
    {
      q: 'Where do I find my meal plan and log my meals?',
      a: 'My Meal Plan shows the plan your RND sent. Log each meal there with a photo, a note or both. Your RND looks at each log and marks how closely it followed the plan. You can change a log until your RND rates it; after that it’s final.',
      link: { label: 'My Meal Plan', to: '/meal-plan-view' },
    },
    {
      q: 'How do I upload my lab results?',
      a: 'When your RND requests lab tests, it shows on your dashboard and in Lab Results, needed before your next consultation. Choose the file (PDF, JPG or PNG, up to 10 MB) or take a photo, then say which tests it has, the date taken and whether you fasted. Your RND sees it right away and accepts it or sends it back with a reason, so you can upload a clearer one. You can replace or delete a result until it’s accepted. You can also upload results you already have. Only you and your RND can open them.',
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
      a: 'New bookings are on the Requests tab of Appointments, with the patient’s screening summary. Confirm at least 30 minutes before the start, or the request expires. Confirming issues the invoice, which the patient pays at least 15 minutes before the start. Declining needs a short reason, which the patient sees.',
      link: { label: 'Appointments', to: '/appointments?tab=requests' },
    },
    {
      q: 'When do I get paid?',
      a: 'Your share (fee minus the platform commission) is on hold until 3 days after the consultation is completed, then it clears. On the 5th of each month NutriMatch pays everything that cleared by that day, once it reaches ₱500, to the GCash or bank account in your payout details. Money that clears after the 5th waits for the next month. Payouts are never sent early.',
      link: { label: 'Earnings', to: '/earnings' },
    },
    {
      q: 'What if my patient doesn’t come, or I have to cancel?',
      a: 'Once the consultation has started, Finish consultation lets you mark a patient who never joined as a no-show: there’s no refund and you’re paid as usual, unless they dispute it within 3 days and NutriMatch approves the dispute. You can’t mark a no-show if they joined the video call. If the call itself doesn’t work, end it as a call that didn’t work and they get a full refund. You can still cancel in the last 30 minutes for an emergency: pick the reason, the patient gets a full refund, and NutriMatch notices if it happens 3 times in 30 days.',
    },
    {
      q: 'Why can’t I mark a consultation complete?',
      a: 'A consultation can only be completed after the patient has paid and the scheduled time has started. If it’s unpaid, the patient sees a reminder to pay before the start time.',
    },
    {
      q: 'How do I write and finalize an NCP record?',
      a: 'Start it in the consultation room, on the NCP tab. Save a draft any time and continue it later from the patient’s chart. Finalize is on the Review step once the required fields are in. A finalized record can’t be edited.',
      link: { label: 'My Patients', to: '/my-patients' },
    },
    {
      q: 'How do I request lab tests?',
      a: 'In the patient’s chart, press Request lab tests, tick the tests and add a note. They’re needed before the patient’s next consultation. Uploads appear in the chart’s Lab results tab (and in the consultation room) as soon as the patient sends them. Open one to read it, then Accept it or Decline it with a reason the patient sees (they’re asked to upload it again). Type the values into the NCP record yourself.',
      link: { label: 'My Patients', to: '/my-patients' },
    },
    {
      q: 'How do I send a meal plan?',
      a: 'Open Meal Planning and pick the patient. Start from a diet template or build the week yourself (FNRI foods, or USDA foods by grams), then send it to the patient.',
      link: { label: 'Meal Planning', to: '/meal-planning' },
    },
    {
      q: 'How do I change my availability or fee?',
      a: 'In Profile Settings, change your fee under Professional profile (press Edit profile) and your hours under Availability. Patients only see open times inside your weekly hours.',
      link: { label: 'Profile Settings', to: '/profile-settings' },
    },
  ],
}
