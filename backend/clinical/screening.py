"""Working out a pre-consultation screening: one place for the numbers, used by
the "calculate only" preview (onboarding's Work out my results), the screening
page's save, and Finish setup, which saves it together with completing onboarding."""

from decimal import Decimal

from .models import PreConsultationScreening
from .services import (
    calculate_bmi,
    calculate_bmr,
    calculate_nrs2002,
    calculate_ter_tannhauser,
    classify_bmi_asia_pacific,
)


def work_out_screening(user, data):
    """The result fields for validated screening input. Removes the write-only
    inputs from `data`, so what's left can build the record. Saves nothing.
    Returns (result fields, the sex that was used)."""
    weight_kg = data["weight_kg"]
    height_cm = data["height_cm"]
    bmi = calculate_bmi(weight_kg, height_cm)
    bmi_category = classify_bmi_asia_pacific(bmi)

    # Sex always comes from the profile when it has it (given at registration;
    # the form shows it read-only and it's changed in Profile Settings). A
    # typed value is only the fallback for "Prefer not to say" at registration.
    # A typed age is accepted but not stored: the BMR doesn't use age.
    client_profile = getattr(user, "client_profile", None)
    data.pop("age", None)
    sex = data.pop("sex", None)
    if client_profile and client_profile.sex:
        sex = client_profile.sex

    # The BMR needs only height and sex (DBW by the BMI method; no age, no actual weight).
    bmr_kcal = tdee_kcal = None
    if sex:
        bmr_kcal = calculate_bmr(height_cm, sex)
    if bmr_kcal is not None:
        activity_level = data.get("activity_level", "sedentary")
        tdee_kcal = calculate_ter_tannhauser(bmr_kcal, activity_level)  # the column holds TER

    # Weight-loss % is derived from the client's own screening history, never
    # self-reported: the most recent prior screening's weight is the baseline.
    # A first-ever screening has no prior data (contributes 0).
    weight_loss_pct = None
    previous = PreConsultationScreening.objects.filter(client=user).order_by("-created_at").first()
    if previous and previous.weight_kg and previous.weight_kg > weight_kg:
        weight_loss_pct = ((previous.weight_kg - weight_kg) / previous.weight_kg * Decimal("100")).quantize(Decimal("0.01"))

    nrs_score, nrs_risk = calculate_nrs2002(
        bmi=bmi,
        weight_loss_pct=weight_loss_pct,
        reduced_intake=data.pop("reduced_intake", False),
        severity_of_disease_points=1 if data.pop("has_chronic_illness", False) else 0,
        reported_weight_loss=data.pop("reported_weight_loss", False),
    )
    fields = {
        "bmi": bmi, "bmi_category": bmi_category, "bmr_kcal": bmr_kcal, "tdee_kcal": tdee_kcal,
        "nrs_score": nrs_score, "nrs_risk": nrs_risk,
    }
    return fields, sex


def save_screening(user, serializer):
    """Save a validated PreConsultationScreeningSerializer as this client's screening."""
    fields, sex = work_out_screening(user, serializer.validated_data)
    client_profile = getattr(user, "client_profile", None)
    if sex and client_profile and not client_profile.sex:  # the typed fallback is kept on the profile
        client_profile.sex = sex
        client_profile.save(update_fields=["sex", "updated_at"])
    return serializer.save(client=user, **fields)
