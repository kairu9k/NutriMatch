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
  intervention: [
    { group: 'Limits', items: [['Sodium limit', 'mg/day'], ['Fluid limit', 'mL/day'], ['Added sugar limit', 'g/day'], ['Saturated fat limit', 'g/day'], ['Rice per meal', 'cups']] },
    { group: 'Goals', items: [['Fiber goal', 'g/day'], ['Water intake', 'L/day'], ['Physical activity', 'min/day'], ['Steps per day', 'steps'], ['Meals per day', 'meals'], ['Target weight', 'kg']] },
  ],
}
