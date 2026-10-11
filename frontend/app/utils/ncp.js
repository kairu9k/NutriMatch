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
