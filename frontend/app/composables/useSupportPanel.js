// The Help & Support panel (SupportWidget.vue) is the one place to dispute a
// consultation (2026-11-16). When it sends a dispute it says so here, so My
// Appointments shows "You disputed this" at once.
export function useSupportPanel() {
  const sent = useState('support-dispute-sent', () => 0)
  return {
    sent,
    markDisputeSent() {
      sent.value = Date.now()
    },
  }
}
