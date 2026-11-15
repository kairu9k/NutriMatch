// What an RND sets up after approval (RndOnboarding.vue). Same lists and limits
// the API enforces (profiles/models.py LANGUAGES, CONSULTATION_MODES,
// MIN_CONSULTATION_FEE).
export const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'tl', name: 'Filipino (Tagalog)' },
  { code: 'ceb', name: 'Bisaya (Cebuano)' },
  { code: 'ilo', name: 'Ilocano' },
  { code: 'hil', name: 'Hiligaynon (Ilonggo)' },
  { code: 'war', name: 'Waray' },
  { code: 'pam', name: 'Kapampangan' },
  { code: 'bcl', name: 'Bicolano' },
]
export const MODE_LABELS = { video: 'Video call', in_person: 'In-person' }
export const MIN_FEE = 100
export const MAX_FEE = 100000

export function bioProblem(bio) {
  const len = (bio || '').trim().length
  return len > 0 && len < 50 ? `Write at least 50 characters (${50 - len} more), or leave it empty for now.` : ''
}
export function feeProblem(fee) {
  if (fee === '' || fee === null || fee === undefined) return ''
  if (!Number.isFinite(Number(fee)) || Number(fee) < MIN_FEE) return `The fee must be at least ₱${MIN_FEE}.`
  if (Number(fee) > MAX_FEE) return 'Enter a realistic fee.'
  return ''
}
export function addressProblem(modes, address) {
  if (!modes.includes('in_person')) return ''
  const v = (address || '').trim()
  if (!v) return 'Add your clinic address, so clients know where to go.'
  return v.length < 10 ? 'Enter the full address: building, street, barangay and city.' : ''
}
