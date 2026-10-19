// What a client is told about a refund (user's call, 2026-10-19). PayMongo
// returns a QR Ph refund through a link the client opens to choose their bank
// or e-wallet (it works for 3 days); GCash / Maya / card refunds go back to
// the same wallet or card. Keep in step with billing/services.py refund_note.
export const REFUND_WINDOW = '5–7 business days'
export const REFUND_CLAIM_NOTE = 'We\'ll send you a PayMongo link to claim it to your bank or e-wallet — claim it within 3 days of getting the link.'
const BACK_TO = { gcash: 'your GCash', maya: 'your Maya account', card: 'the card you paid with' }

export function refundNote (method) {
  if (method === 'qrph') return REFUND_CLAIM_NOTE
  return BACK_TO[method] ? `It goes back to ${BACK_TO[method]}.` : ''
}

export function refundMessage (amount, method) {
  return `Your ₱${amount} payment will be refunded within ${REFUND_WINDOW}. ${refundNote(method)}`.trim()
}
