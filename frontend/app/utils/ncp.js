// NCP form helpers.

// Common nutrition diagnosis terms for the PES "Problem", grouped the way the
// Academy of Nutrition and Dietetics' NCP terminology groups them (Intake /
// Clinical / Behavioral-Environmental). The RND can still type their own.
export const PES_TERMS = [
  {
    group: 'Intake',
    terms: [
      'Excessive energy intake', 'Inadequate energy intake', 'Excessive oral intake', 'Inadequate oral intake',
      'Excessive carbohydrate intake', 'Inadequate carbohydrate intake', 'Inconsistent carbohydrate intake',
      'Excessive fat intake', 'Excessive saturated fat intake', 'Inadequate protein intake', 'Excessive protein intake',
      'Inadequate fiber intake', 'Excessive sodium intake', 'Excessive sugar intake', 'Inadequate fluid intake',
      'Excessive alcohol intake', 'Inadequate vitamin intake', 'Inadequate mineral intake (e.g. iron, calcium)',
      'Predicted suboptimal nutrient intake',
    ],
  },
  {
    group: 'Clinical',
    terms: [
      'Overweight/obesity', 'Underweight', 'Unintended weight loss', 'Unintended weight gain', 'Malnutrition',
      'Altered nutrition-related laboratory values', 'Impaired nutrient utilization', 'Altered GI function',
      'Swallowing difficulty', 'Food–medication interaction',
    ],
  },
  {
    group: 'Behavioral / environmental',
    terms: [
      'Food- and nutrition-related knowledge deficit', 'Not ready for diet/lifestyle change',
      'Undesirable food choices', 'Disordered eating pattern', 'Limited adherence to nutrition-related recommendations',
      'Physical inactivity', 'Excessive physical activity', 'Self-monitoring deficit', 'Limited access to food',
      'Intake of unsafe food',
    ],
  },
]

// WHO Asia-Pacific BMI — same formula and cut-offs as clinical/services.py.
export function bmiOf(weightKg, heightCm) {
  const w = Number(weightKg)
  const h = Number(heightCm) / 100
  if (!w || !h) return null
  return Math.round((w / (h * h)) * 100) / 100
}
export function bmiClass(bmi) {
  if (bmi == null) return ''
  if (bmi < 18.5) return 'Underweight'
  if (bmi < 23) return 'Normal'
  if (bmi < 25) return 'Overweight (At Risk)'
  if (bmi < 30) return 'Obese I'
  return 'Obese II'
}

// Blood pressure category, WHO / ESH-style grading (user's call, 2026-10-16 —
// common in the Philippines) plus a Low band (< 90/60). When the two numbers
// fall in different grades the higher grade wins (135/92 → Grade 1); Low only
// applies when neither number is high (150/55 is Grade 1). A warning only —
// `level` is ok / warn / danger for colouring. Returns null for an incomplete
// reading. Accepts (systolic, diastolic) or a "120/80" string.
const BP_GRADES = [
  { sys: 180, dia: 110, label: 'Grade 3 hypertension', level: 'danger' },
  { sys: 160, dia: 100, label: 'Grade 2 hypertension', level: 'danger' },
  { sys: 140, dia: 90, label: 'Grade 1 hypertension', level: 'warn' },
  { sys: 130, dia: 85, label: 'High-normal blood pressure', level: 'warn' },
  { sys: 120, dia: 80, label: 'Normal', level: 'ok' },
]
export function bpCategory(systolic, diastolic) {
  if (diastolic === undefined && typeof systolic === 'string') [systolic, diastolic] = systolic.split('/')
  const s = Number(systolic), d = Number(diastolic)
  if (!String(systolic ?? '').trim() || !String(diastolic ?? '').trim() || !s || !d) return null
  const grade = BP_GRADES.find(g => s >= g.sys || d >= g.dia)
  if (grade) return { label: grade.label, level: grade.level }
  if (s < 90 || d < 60) return { label: 'Low blood pressure', level: 'warn' }
  return { label: 'Optimal', level: 'ok' }
}
export const bpLabel = bp => (bp ? `${bp} mmHg${bpCategory(bp) ? `, ${bpCategory(bp).label}` : ''}` : '')

// Fasting blood glucose (mg/dL) and HbA1c (%) categories (ADA cutoffs,
// user's call 2026-10-16). Warnings only, same { label, level } shape.
const filledNum = v => (v == null || String(v).trim() === '' ? null : Number(v))
export function glucoseCategory(mgdl) {
  const g = filledNum(mgdl)
  if (g == null || Number.isNaN(g)) return null
  if (g < 70) return { label: 'Low (hypoglycemia)', level: 'warn' }
  if (g < 100) return { label: 'Normal', level: 'ok' }
  if (g < 126) return { label: 'Prediabetes', level: 'warn' }
  return { label: 'Diabetes', level: 'danger' }
}
export function hba1cCategory(pct) {
  const h = filledNum(pct)
  if (h == null || Number.isNaN(h)) return null
  if (h < 5.7) return { label: 'Normal', level: 'ok' }
  if (h < 6.5) return { label: 'Prediabetes', level: 'warn' }
  return { label: 'Diabetes', level: 'danger' }
}

// Macros → kcal (4 / 4 / 9 kcal per gram).
export const KCAL_PER_G = { carb: 4, protein: 4, fat: 9 }
export function macroKcal({ carb, protein, fat }) {
  return (Number(carb) || 0) * 4 + (Number(protein) || 0) * 4 + (Number(fat) || 0) * 9
}
// A starting split for the RND to adjust: 50% carbs, 20% protein, 30% fat.
export function suggestMacros(kcal) {
  const k = Number(kcal)
  if (!k) return null
  return { carb: Math.round((k * 0.5) / 4), protein: Math.round((k * 0.2) / 4), fat: Math.round((k * 0.3) / 9) }
}

// Field limits — mirror clinical/serializers.py NcpRecordSerializer.RANGES /
// max lengths and core/validators.py validate_blood_pressure.
export const NCP_LIMITS = {
  height_cm: { min: 100, max: 250, unit: 'cm' },
  weight_kg: { min: 25, max: 300, unit: 'kg' },
  bp_systolic: { min: 60, max: 260, unit: 'mmHg' },
  bp_diastolic: { min: 30, max: 160, unit: 'mmHg' },
  blood_glucose: { min: 20, max: 600, unit: 'mg/dL' },
  hba1c: { min: 3, max: 20, unit: '%' },
  target_kcal: { min: 800, max: 5000, unit: 'kcal' },
  target_carb_g: { min: 0, max: 1000, unit: 'g' },
  target_protein_g: { min: 0, max: 500, unit: 'g' },
  target_fat_g: { min: 0, max: 300, unit: 'g' },
}
export const NCP_TEXT_MAX = {
  lab_notes: 2000, assessment_notes: 3000, pes_problem: 200, pes_etiology: 1000, pes_signs: 1000,
  diet_prescription: 3000, intervention_notes: 3000, monitoring_notes: 3000,
}
export function rangeError(field, value) {
  const lim = NCP_LIMITS[field]
  if (!lim || String(value ?? '').trim() === '') return ''
  const n = Number(value)
  if (Number.isNaN(n)) return 'Enter a number.'
  if (n < lim.min || n > lim.max) return `Must be ${lim.min}–${lim.max} ${lim.unit}.`
  return ''
}

// "Other measurements": a number + a unit made of letters (plus % and /).
export const EXTRA_VALUE_RE = /^\d{1,6}(\.\d{1,3})?$/
export const EXTRA_UNIT_RE = /^[A-Za-zµ%/. ²³]*$/
export const cleanUnit = v => String(v ?? '').replace(/[^A-Za-zµ%/. ²³]/g, '').slice(0, 30)
export function extraRowErrors(row) {
  const label = String(row.label ?? '').trim()
  const value = String(row.value ?? '').trim()
  const unit = String(row.unit ?? '').trim()
  if (!label && !value && !unit) return {}
  const e = {}
  if (!label) e.label = 'Name it'
  if (!value) e.value = 'Enter a value'
  else if (!EXTRA_VALUE_RE.test(value)) e.value = 'Numbers only'
  if (unit && !EXTRA_UNIT_RE.test(unit)) e.unit = 'Letters only'
  return e
}

// Common measurements an RND adds, with their usual unit — picked like the
// PES problem; the RND can still type any name and unit.
export const MEASURE_TEMPLATES = {
  assessment: [
    { group: 'Body', items: [['Waist circumference', 'cm'], ['Hip circumference', 'cm'], ['Waist-to-hip ratio', ''], ['Mid-upper arm circumference', 'cm'], ['Body fat', '%'], ['Triceps skinfold', 'mm'], ['Calf circumference', 'cm']] },
    { group: 'Labs', items: [['Total cholesterol', 'mg/dL'], ['LDL cholesterol', 'mg/dL'], ['HDL cholesterol', 'mg/dL'], ['Triglycerides', 'mg/dL'], ['Postprandial glucose', 'mg/dL'], ['Creatinine', 'mg/dL'], ['eGFR', 'mL/min'], ['Uric acid', 'mg/dL'], ['Hemoglobin', 'g/dL'], ['Albumin', 'g/dL'], ['Sodium', 'mmol/L'], ['Potassium', 'mmol/L']] },
  ],
  // Daily targets, named and united as in the Philippine Dietary Reference
  // Intakes (PDRI 2015). Protein / carbohydrate / fat have their own fields.
  // Also the Meal Planning page's "Other Targets" list.
  intervention: [
    { group: 'Nutrients', items: [['Sodium', 'mg/day'], ['Fiber', 'g/day'], ['Saturated fat', 'g/day'], ['Trans fat', 'g/day'], ['Omega-3', 'g/day'], ['Added sugar', 'g/day'], ['Cholesterol', 'mg/day']] },
    { group: 'Minerals', items: [['Potassium', 'mg/day'], ['Phosphorus', 'mg/day'], ['Calcium', 'mg/day'], ['Magnesium', 'mg/day'], ['Iron', 'mg/day'], ['Zinc', 'mg/day'], ['Copper', 'mg/day'], ['Manganese', 'mg/day'], ['Chloride', 'mg/day'], ['Fluoride', 'mg/day'], ['Iodine', 'mcg/day'], ['Selenium', 'mcg/day']] },
    { group: 'Vitamins', items: [['Vitamin A', 'mcg/day'], ['Vitamin D', 'mcg/day'], ['Vitamin E', 'mg/day'], ['Vitamin K', 'mcg/day'], ['Vitamin C', 'mg/day'], ['Thiamin (B1)', 'mg/day'], ['Riboflavin (B2)', 'mg/day'], ['Niacin (B3)', 'mg/day'], ['Pantothenic acid (B5)', 'mg/day'], ['Vitamin B6', 'mg/day'], ['Biotin (B7)', 'mcg/day'], ['Folate (B9)', 'mcg/day'], ['Vitamin B12', 'mcg/day'], ['Choline', 'mg/day']] },
    { group: 'Goals', items: [['Water intake', 'L/day'], ['Fluid limit', 'mL/day'], ['Rice per meal', 'cups'], ['Physical activity', 'min/day'], ['Steps per day', 'steps'], ['Meals per day', 'meals'], ['Target weight', 'kg']] },
  ],
}

/* ---------- dietary intake tools (mirrors backend clinical/dietary.py) ---------- */
export const RECALL_MEALS = [
  { value: 'breakfast', label: 'Breakfast' }, { value: 'am_snack', label: 'AM snack' }, { value: 'lunch', label: 'Lunch' },
  { value: 'pm_snack', label: 'PM snack' }, { value: 'dinner', label: 'Dinner' }, { value: 'bedtime_snack', label: 'Late-night snack' },
]
export const RECALL_MAX_ROWS = 80
export const FFQ_GROUPS = [
  { value: 'rice_bread', label: 'Rice, bread, noodles, corn' },
  { value: 'root_crops', label: 'Root crops (kamote, gabi, cassava)' },
  { value: 'green_yellow_veg', label: 'Green leafy & yellow vegetables' },
  { value: 'other_veg', label: 'Other vegetables' },
  { value: 'fruits', label: 'Fruits' },
  { value: 'fish', label: 'Fish & seafood' },
  { value: 'meat_poultry', label: 'Meat & poultry' },
  { value: 'processed_meat', label: 'Processed meat (hotdog, longganisa, tocino, canned)' },
  { value: 'eggs', label: 'Eggs' },
  { value: 'legumes', label: 'Legumes & nuts (monggo, peanuts, tokwa)' },
  { value: 'milk', label: 'Milk & dairy' },
  { value: 'sweet_drinks', label: 'Sweetened drinks (soft drinks, juice, 3-in-1 coffee)' },
  { value: 'sweets', label: 'Sweets & desserts (kakanin, cakes, candy)' },
  { value: 'fried', label: 'Fried & fast food' },
  { value: 'salty_snacks', label: 'Instant noodles, chips & salty snacks' },
  { value: 'alcohol', label: 'Alcoholic drinks' },
]
export const FFQ_FREQS = [
  { value: 'never', label: 'Never' }, { value: 'monthly', label: '1–3× a month' }, { value: 'weekly', label: '1–2× a week' },
  { value: 'often', label: '3–6× a week' }, { value: 'daily', label: 'Once a day' }, { value: 'multi', label: '2+ times a day' },
]
// FAO's 9-group Individual Dietary Diversity Score (FAO 2011).
export const IDDS_GROUPS = [
  { value: 'starchy', label: 'Starchy staples', eg: 'rice, bread, corn, kamote' },
  { value: 'dark_green', label: 'Dark green leafy vegetables', eg: 'malunggay, kangkong, pechay' },
  { value: 'vit_a', label: 'Other vitamin A-rich fruits & vegetables', eg: 'kalabasa, carrot, ripe mango, papaya' },
  { value: 'other_fv', label: 'Other fruits & vegetables', eg: 'talong, sitaw, banana' },
  { value: 'organ', label: 'Organ meat', eg: 'liver, gizzard, dinuguan' },
  { value: 'meat_fish', label: 'Meat & fish', eg: 'chicken, pork, bangus, tilapia' },
  { value: 'eggs', label: 'Eggs', eg: 'itlog, balut' },
  { value: 'legumes', label: 'Legumes, nuts & seeds', eg: 'monggo, tokwa, peanuts' },
  { value: 'milk', label: 'Milk & milk products', eg: 'milk, cheese, yogurt' },
]
// Commonly used cut-offs for the 9-group score.
export function iddsLevel(score) {
  if (score == null) return null
  return score <= 3 ? { key: 'low', label: 'Low diversity' } : score <= 5 ? { key: 'medium', label: 'Medium diversity' } : { key: 'high', label: 'High diversity' }
}
// Calorie count of a 24-hour recall from the FNRI exchange values per group.
export function recallTotals(rows, values = []) {
  const by = Object.fromEntries(values.map(v => [v.code, v]))
  const t = { kcal: 0, carbs_g: 0, protein_g: 0, fat_g: 0, counted: 0, foods: 0 }
  for (const r of rows) {
    if (!String(r.food_name || '').trim()) continue
    t.foods++
    const v = by[r.group]
    const x = Number(r.exchanges)
    if (!v || r.exchanges === '' || r.exchanges == null || !Number.isFinite(x)) continue
    t.kcal += x * (v.kcal || 0); t.carbs_g += x * (v.carbs_g || 0); t.protein_g += x * (v.protein_g || 0); t.fat_g += x * (v.fat_g || 0)
    t.counted++
  }
  for (const k of ['kcal', 'carbs_g', 'protein_g', 'fat_g']) t[k] = Math.round(t[k])
  return t
}
export function recallRowErrors(row) {
  const e = {}
  const name = String(row.food_name || '').trim()
  const x = String(row.exchanges ?? '').trim()
  if (!name && (String(row.amount || '').trim() || x)) e.food_name = 'Add the food'
  if (x && (!/^\d{1,2}(\.\d)?$/.test(x) || Number(x) > 20)) e.exchanges = '0–20, e.g. 1.5'
  return e
}
// Suggest the IDDS groups a recall covers (the RND confirms them).
const has = (s, words) => words.some(w => s.includes(w))
export function iddsFromRecall(rows) {
  const out = new Set()
  for (const r of rows) {
    const s = String(r.food_name || '').toLowerCase()
    if (!s.trim()) continue
    const g = r.group || ''
    if (has(s, ['liver', 'atay', 'gizzard', 'balunbalunan', 'dinuguan', 'isaw', 'bopis', 'kidney'])) out.add('organ')
    else if (has(s, ['egg', 'itlog', 'balut'])) out.add('eggs')
    else if (has(s, ['tokwa', 'tofu', 'monggo', 'mongo', 'munggo', 'beans', 'peanut', 'mani', 'nuts', 'seeds', 'toge'])) out.add('legumes')
    else if (g.startsWith('milk') || has(s, ['milk', 'gatas', 'cheese', 'keso', 'yogurt'])) out.add('milk')
    else if (g.startsWith('rice') || has(s, ['rice', 'kanin', 'bread', 'pandesal', 'pan de sal', 'noodle', 'pancit', 'pasta', 'corn', 'mais', 'kamote', 'cassava', 'potato', 'gabi', 'oat'])) out.add('starchy')
    else if (has(s, ['malunggay', 'kangkong', 'pechay', 'petsay', 'alugbati', 'saluyot', 'talbos', 'camote tops', 'spinach', 'mustasa', 'leaves', 'dahon'])) out.add('dark_green')
    else if (has(s, ['kalabasa', 'squash', 'carrot', 'mango', 'mangga', 'papaya'])) out.add('vit_a')
    else if (g === 'vegetable' || g === 'fruit') out.add('other_fv')
    else if (g.startsWith('meat') || has(s, ['chicken', 'manok', 'pork', 'baboy', 'beef', 'baka', 'fish', 'isda', 'bangus', 'tilapia', 'tuna', 'galunggong', 'shrimp', 'hipon', 'squid', 'pusit', 'sardines', 'hotdog', 'longganisa', 'tocino'])) out.add('meat_fish')
  }
  return IDDS_GROUPS.map(x => x.value).filter(v => out.has(v))
}
