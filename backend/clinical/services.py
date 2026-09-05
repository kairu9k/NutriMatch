"""Nutritional calculation engine.

Implements the exact formulas named in the capstone proposal — do not
substitute generic/global versions of these without checking
vault/C1-NUTRIMATCH-FINALv5.pdf first:

- BMR: Mifflin-St Jeor equation
- TDEE: BMR × activity factor
- BMI classification: WHO Asia-Pacific thresholds (NOT the standard global
  WHO cutoffs — Asia-Pacific uses lower obesity thresholds)
- NRS-2002: adapted nutritional risk screening score
"""

from decimal import Decimal


ACTIVITY_FACTORS = {
    "sedentary": Decimal("1.2"),
    "lightly_active": Decimal("1.375"),
    "moderately_active": Decimal("1.55"),
    "very_active": Decimal("1.725"),
    "extra_active": Decimal("1.9"),
}


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


def calculate_bmr_mifflin_st_jeor(
    weight_kg: Decimal, height_cm: Decimal, age_years: int, sex: str
) -> Decimal:
    """Mifflin-St Jeor equation.

    Male:   BMR = 10*weight + 6.25*height - 5*age + 5
    Female: BMR = 10*weight + 6.25*height - 5*age - 161
    """
    base = (Decimal("10") * weight_kg) + (Decimal("6.25") * height_cm) - (Decimal("5") * age_years)
    bmr = base + Decimal("5") if sex == "male" else base - Decimal("161")
    return bmr.quantize(Decimal("0.01"))


def calculate_tdee(bmr_kcal: Decimal, activity_level: str) -> Decimal:
    factor = ACTIVITY_FACTORS.get(activity_level, ACTIVITY_FACTORS["sedentary"])
    return (bmr_kcal * factor).quantize(Decimal("0.01"))


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
