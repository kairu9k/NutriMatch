// Where a clinical figure came from and when (patient summary
// progress.weight_origin / bmi_origin, 2026-10-26): measured at a consultation,
// typed in by the client, or their screening. The RND judges a number by it.
const PH = { timeZone: 'Asia/Manila' }
const day = v => new Date(typeof v === 'string' && v.length === 10 ? `${v}T00:00:00+08:00` : v)
  .toLocaleDateString('en-PH', { ...PH, month: 'short', day: 'numeric' })

export function figureSource(origin) {
  if (!origin) return ''
  if (origin.from === 'consultation') return `${day(origin.on)}, at consultation`
  if (origin.from === 'self-reported') return `${day(origin.on)}, self-reported`
  return `${day(origin.on)}, self-reported at screening`
}

export function screeningSource(screening) {
  return screening?.date ? `from the screening on ${day(screening.date)}` : ''
}
