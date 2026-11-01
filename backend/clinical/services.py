"""Nutritional calculation engine.

Implements the exact formulas named in the capstone proposal — do not
substitute generic/global versions of these without checking
vault/C1-NUTRIMATCH-FINALv5.pdf first:

- BMR: Tannhauser's method — DBW from height, then BMR from DBW (2026-10-31,
  asked for by the project's RND resource person; replaces the proposal's
  Mifflin-St Jeor equation)
- TER (Total Energy Requirement): Tannhauser's factorial method — BMR +
  physical activity (% of BMR) + TEF (10% of the two), rounded to the nearest
  50 kcal (2026-11-01, the RND resource person's method; replaces BMR ×
  activity factor). Stored in the screening's `tdee_kcal` column.
- Macro distribution: TER × % ÷ 4 (carbs, protein) or ÷ 9 (fat), rounded to
  the nearest 5 g; default 55 / 20 / 25
- BMI classification: WHO Asia-Pacific thresholds (NOT the standard global
  WHO cutoffs — Asia-Pacific uses lower obesity thresholds)
- NRS-2002: adapted nutritional risk screening score
"""

from decimal import ROUND_HALF_UP, Decimal


# Tannhauser physical activity, as a % of BMR (mirrored in utils/ncp.js TER_ACTIVITY).
TER_ACTIVITY_PCT = {
    "bed_rest": Decimal("10"),
    "sedentary": Decimal("30"),
    "light": Decimal("50"),
    "moderate": Decimal("75"),
    "heavy": Decimal("100"),
}
# The screening's activity answers on the Tannhauser scale (very and extra
# active are both "heavy", the top of the scale).
SCREENING_TO_TER_ACTIVITY = {
    "sedentary": "sedentary",
    "lightly_active": "light",
    "moderately_active": "moderate",
    "very_active": "heavy",
    "extra_active": "heavy",
}
TEF_PCT = Decimal("10")
DEFAULT_MACRO_PCT = {"carb": 55, "protein": 20, "fat": 25}
KCAL_PER_G = {"carb": Decimal("4"), "protein": Decimal("4"), "fat": Decimal("9")}


def round_to(value: Decimal, step: int) -> Decimal:
    """Nearest multiple of `step`, halves up (1,825 → 1,850)."""
    return (value / step).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * step


def calculate_bmi(weight_kg: Decimal, height_cm: Decimal) -> Decimal:
    height_m = height_cm / Decimal("100")
    bmi = weight_kg / (height_m * height_m)
    return bmi.quantize(Decimal("0.01"))


def classify_bmi_asia_pacific(bmi: Decimal) -> str:
    """WHO Asia-Pacific BMI classification (WHO, 2000, reaffirmed 2023)."""
    if bmi < Decimal("18.5"):
        return "Underweight"
    if bmi < Decimal("23"):
        return "Normal"
    if bmi < Decimal("25"):
        return "Overweight (At Risk)"
    if bmi < Decimal("30"):
        return "Obese I"
    return "Obese II"


# kcal per kg of DBW per hour, Tannhauser BMR (values given by the RND resource person).
BMR_KCAL_PER_KG_HOUR = {"male": Decimal("1.0"), "female": Decimal("0.9")}


def calculate_dbw_tannhauser(height_cm: Decimal) -> Decimal:
    """Desirable body weight, Tannhauser's method:
    DBW = (height cm - 100) - 10% of (height cm - 100)."""
    base = height_cm - Decimal("100")
    return (base - base * Decimal("0.10")).quantize(Decimal("0.01"))


def calculate_bmr_tannhauser(height_cm: Decimal, sex: str) -> Decimal | None:
    """BMR from the Tannhauser DBW — it uses the desirable weight, not the
    actual weight, and no age:

    Male:   BMR = DBW × 1.0 kcal/kg/hour × 24
    Female: BMR = DBW × 0.9 kcal/kg/hour × 24

    None when sex isn't male/female.
    """
    factor = BMR_KCAL_PER_KG_HOUR.get(sex)
    if factor is None:
        return None
    return (calculate_dbw_tannhauser(height_cm) * factor * Decimal("24")).quantize(Decimal("0.01"))


def calculate_ter_tannhauser(bmr_kcal: Decimal, activity: str) -> Decimal:
    """Total Energy Requirement, Tannhauser's factorial method:

    Physical activity = BMR × activity % (bed rest 10, sedentary 30, light 50,
                        moderate 75, heavy 100)
    TEF               = 10% of (BMR + physical activity)
    TER               = BMR + physical activity + TEF, to the nearest 50 kcal

    `activity` is a Tannhauser key or a screening answer (lightly_active…).
    """
    key = SCREENING_TO_TER_ACTIVITY.get(activity, activity)
    pa = bmr_kcal * TER_ACTIVITY_PCT.get(key, TER_ACTIVITY_PCT["sedentary"]) / 100
    tef = (bmr_kcal + pa) * TEF_PCT / 100
    return round_to(bmr_kcal + pa + tef, 50)


def macro_grams(ter_kcal: Decimal, pct: dict | None = None) -> dict:
    """Grams per day for a TER and a % split (default 55 / 20 / 25), each to
    the nearest 5 g: carbs and protein 4 kcal/g, fat 9 kcal/g."""
    pct = pct or DEFAULT_MACRO_PCT
    return {k: round_to(Decimal(ter_kcal) * Decimal(pct[k]) / 100 / KCAL_PER_G[k], 5) for k in ("carb", "protein", "fat")}


def calculate_nrs2002(bmi: Decimal, weight_loss_pct: Decimal | None = None, reduced_intake: bool = False,
                        severity_of_disease_points: int = 0) -> tuple[int, str]:
    """Adapted NRS-2002 nutritional risk score.

    Simplified scoring against the fields this system actually captures:
    impaired nutritional status (0-3, from BMI + weight loss + intake) +
    severity of disease (0-3, clinician-supplied). Score >= 3 = at risk.
    """
    nutritional_score = 0
    if bmi < Decimal("18.5"):
        nutritional_score = 3
    elif weight_loss_pct is not None and weight_loss_pct >= Decimal("5"):
        nutritional_score = 2
    elif reduced_intake:
        nutritional_score = 1

    total = nutritional_score + severity_of_disease_points

    if total >= 3:
        risk = "high_risk" if total >= 5 else "at_risk"
    else:
        risk = "no_risk"

    return total, risk


def run_screening_calculations(screening) -> None:
    """Populates the derived fields (bmi, bmi_category, bmr_kcal, tdee_kcal)
    on a PreConsultationScreening instance in place. Does not save."""
    screening.bmi = calculate_bmi(screening.weight_kg, screening.height_cm)
    screening.bmi_category = classify_bmi_asia_pacific(screening.bmi)
