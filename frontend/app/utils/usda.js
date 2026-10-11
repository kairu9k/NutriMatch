// USDA FoodData Central foods (backend nutrition/usda.py): per-100 g values
// scaled to a portion in grams. Mirrors usda.portion() on the API.
export function usdaPortion(per100, grams) {
  const g = Number(grams)
  const scale = v => (v == null || !Number.isFinite(g) ? null : Math.round(v * g / 100 * 10) / 10)
  return { kcal: scale(per100?.kcal), carbs_g: scale(per100?.carbs_g), protein_g: scale(per100?.protein_g), fat_g: scale(per100?.fat_g) }
}
