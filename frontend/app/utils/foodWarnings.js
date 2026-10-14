// Meal planning: warn when an FNRI food isn't a good fit for the patient's
// condition (team testing feedback, 2026-10-14). Only a warning — the RND
// decides; nothing is blocked. Rules come from the FNRI exchange list's own
// flags (high sodium / potassium / phosphorus, renal flag) and food groups
// (sugar, high-fat meat). USDA and typed foods have no FNRI data, so no warning.

// Conditions as written on the client's health profile ("Type 2 Diabetes",
// "Hypertension"…) or picked on the plan ("diabetes", "renal", "weight_loss").
const CONDITION_MATCH = [
  { key: 'diabetes', match: /diabet/i },
  { key: 'hypertension', match: /hypertens|blood pressure/i },
  { key: 'renal', match: /renal|kidney|ckd/i },
  { key: 'weight', match: /obes|weight_loss|weight management|weight loss/i },
]

export function conditionKeys(...sources) {
  const keys = new Set()
  for (const text of sources.flat().filter(Boolean)) {
    for (const c of CONDITION_MATCH) if (c.match.test(String(text))) keys.add(c.key)
  }
  return keys
}

/** Reasons this FNRI item doesn't suit the patient, e.g.
 *  ["High in sodium — limit for hypertension"]. Empty when it's fine. */
export function foodWarnings(item, keys) {
  if (!item || !keys?.size) return []
  const code = item.category?.code || ''
  const out = []
  const add = (text) => { if (!out.includes(text)) out.push(text) }
  if (keys.has('diabetes') && code === 'sugar') add('Added sugar — raises blood sugar (diabetes)')
  if (keys.has('hypertension') && item.is_high_sodium) add('High in sodium — limit for hypertension')
  if (keys.has('hypertension') && code === 'meat_high') add('High-fat meat — limit for hypertension (DASH)')
  if (keys.has('renal')) {
    if (item.is_high_potassium) add('High in potassium — limit for kidney disease')
    if (item.is_high_phosphorus) add('High in phosphorus — limit for kidney disease')
    if (item.is_high_sodium) add('High in sodium — limit for kidney disease')
    // FNRI flags every meat as not renal-friendly; protein is limited by the
    // prescribed exchanges instead, so only other flagged foods are warned.
    if (!item.ok_for_renal && !code.startsWith('meat')) add('Not recommended for kidney disease (FNRI)')
  }
  if (keys.has('weight')) {
    if (code === 'sugar') add('Added sugar — limit for weight management')
    if (code === 'meat_high') add('High-fat meat — limit for weight management')
  }
  return out
}

// Allergies (any food, FNRI, USDA or typed): the food words each onboarding
// allergy choice covers — mirrors nutrition/plan_templates.py ALLERGEN_WORDS.
// Whole words, so "egg" doesn't catch "Eggplant" nor "milk" "Milkfish".
const ALLERGEN_WORDS = {
  'shrimp / shellfish': ['shrimp', 'prawn', 'crab', 'lobster', 'squid', 'clam', 'mussel', 'oyster', 'scallop',
    'shellfish', 'hipon', 'alimango', 'talaba', 'tahong', 'pusit'],
  fish: ['fish', 'milkfish', 'bangus', 'tilapia', 'tuna', 'sardine', 'galunggong', 'mackerel', 'dilis', 'tuyo'],
  peanuts: ['peanut'],
  'tree nuts': ['cashew', 'almond', 'walnut', 'pili', 'pistachio', 'hazelnut', 'macadamia'],
  eggs: ['egg', 'balut', 'leche flan', 'custard'],
  milk: ['milk', 'cheese', 'yogurt', 'leche flan', 'custard'],
  soy: ['soy', 'tofu', 'tokwa', 'taho'],
  'wheat / gluten': ['wheat', 'gluten', 'bread', 'pan de sal', 'pasta', 'noodle', 'flour', 'bun'],
}
const escapeRe = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

/** "Allergy: Shrimp / shellfish" for each of the patient's allergies this food name matches. */
export function allergyWarnings(foodName, allergies) {
  const name = String(foodName || '').toLowerCase()
  if (!name || !allergies?.length) return []
  const out = []
  for (const allergy of allergies) {
    const key = String(allergy).trim().toLowerCase()
    if (!key) continue
    const words = ALLERGEN_WORDS[key] || key.split(/[/,]/).map(w => w.trim()).filter(Boolean)
    const hit = words.some((w) => {
      const stem = w.endsWith('s') && w.length > 3 ? w.slice(0, -1) : w
      return new RegExp(`\\b${escapeRe(stem)}(e?s)?\\b`).test(name)
    })
    if (hit) out.push(`Allergy: ${allergy}`)
  }
  return out
}
