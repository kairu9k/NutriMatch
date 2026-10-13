// Pre-consultation screening symptoms (2026-10-14, user's call): the checkboxes
// follow the client's condition (ClientHealthProfile.medical_conditions) instead
// of one fixed list. Saved as plain text, comma-separated, in
// PreConsultationScreening.symptoms — so labels must not contain commas.
//
// Only the "For everyone" group feeds the NRS-2002 score (poor appetite →
// reduced intake; elevated blood glucose or recent hospitalization → disease
// severity, clinical/services.py). The condition symptoms are recorded for the
// RND and don't change the score.

export const GENERAL_SYMPTOMS = [
  'Unintended weight loss',
  'Poor appetite',
  'Elevated blood glucose',
  'Recent hospitalization',
]

const CONDITION_GROUPS = [
  { key: 'obesity', title: 'Obesity Management', match: /obes|weight/i, items: [
    'Short of breath when walking or climbing stairs', 'Joint or back pain', 'Snoring or poor sleep',
    'Always tired', 'Heartburn or acid reflux', 'Overeating or late-night eating',
  ] },
  { key: 'diabetes', title: 'Type 2 Diabetes', match: /diabet/i, items: [
    'Always thirsty', 'Frequent urination', 'Always tired', 'Blurred vision',
    'Slow-healing wounds', 'Numbness or tingling in hands or feet',
  ] },
  { key: 'hypertension', title: 'Hypertension', match: /hypertens|blood pressure/i, items: [
    'Frequent headaches', 'Dizziness', 'Blurred vision', 'Chest pain or tightness',
    'Short of breath', 'Swelling in ankles or feet',
  ] },
  { key: 'renal', title: 'Renal Nutrition', match: /renal|kidney|ckd/i, items: [
    'Swelling in the legs or face', 'Less or foamy urine', 'Itchy skin', 'Nausea or vomiting',
    'Muscle cramps', 'Always tired',
  ] },
]
const OTHER_GROUP = { key: 'other', title: '', items: ['Always tired', 'Bloating or constipation', 'Heartburn', 'Frequent headaches', 'Poor sleep'] }

/** The groups of symptom checkboxes for a client: one per known condition (a
 *  symptom already shown in an earlier group isn't repeated), or a general
 *  list when the condition isn't one we know, then "For everyone". Symptoms in
 *  `saved` that no group lists (older screenings) get their own group so a
 *  read-only view still shows them. */
export function symptomGroups(conditions = [], saved = []) {
  const groups = []
  const seen = new Set()
  const add = (title, items, key) => {
    const fresh = items.filter(i => !seen.has(i))
    fresh.forEach(i => seen.add(i))
    if (fresh.length) groups.push({ key, title, items: fresh })
  }
  const matched = CONDITION_GROUPS.filter(g => (conditions || []).some(c => g.match.test(String(c))))
  if (matched.length) matched.forEach(g => add(`Symptoms related to ${g.title}`, g.items, g.key))
  else add('Common symptoms', OTHER_GROUP.items, OTHER_GROUP.key)
  add('For everyone', GENERAL_SYMPTOMS, 'general')
  const extra = (saved || []).filter(s => s && !seen.has(s))
  if (extra.length) groups.push({ key: 'saved', title: 'Other symptoms you reported', items: extra })
  return groups
}

export function parseSymptoms(text) {
  return String(text || '').split(',').map(s => s.trim()).filter(Boolean)
}
