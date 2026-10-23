// Where an RND's earnings are sent (2026-10-23, user's call): an e-wallet or a
// bank. Same methods as billing.models.RndPayoutAccount.Method on the API.
// GCash and Maya are paid to an 09 mobile number; GoTyme and MariBank are
// digital banks with an account number.
export const WALLETS = [
  { value: 'gcash', label: 'GCash', mobile: true },
  { value: 'maya', label: 'Maya', mobile: true },
  { value: 'gotyme', label: 'GoTyme', mobile: false },
  { value: 'maribank', label: 'MariBank', mobile: false },
]

// The banks most RNDs in the Philippines use; anything else is typed in.
export const BANKS = [
  'BDO Unibank', 'BPI', 'Metrobank', 'Land Bank of the Philippines', 'PNB', 'Security Bank',
  'UnionBank', 'RCBC', 'China Bank', 'EastWest Bank', 'PSBank', 'AUB', 'Maybank Philippines', 'CIMB Bank',
]

const LABEL = Object.fromEntries(WALLETS.map(w => [w.value, w.label]))

// "GCash", "Maya", "BDO Unibank"… (a bank shows its own name)
export function payoutVia(method, bankName) {
  if (method === 'bank') return bankName || 'Bank transfer'
  return LABEL[method] || method || ''
}

export const isMobileWallet = method => WALLETS.some(w => w.value === method && w.mobile)
