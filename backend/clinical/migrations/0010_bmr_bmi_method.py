from decimal import ROUND_HALF_UP, Decimal

from django.db import migrations

# BMR's desirable body weight switched from Tannhauser's (height − 100) − 10%
# to the BMI method, height (m)² × 22 (2026-11-02, user's call — Tannhauser
# falls apart for short patients). Recompute every saved screening's BMR and,
# since TER is built from it, its TER too (formula unchanged). Same formulas as
# clinical.services calculate_bmr / calculate_ter_tannhauser (copied: a
# migration mustn't import code that can change later).
FACTOR = {"male": Decimal("1.0"), "female": Decimal("0.9")}
ACTIVITY_PCT = {
    "sedentary": Decimal("30"), "lightly_active": Decimal("50"), "moderately_active": Decimal("75"),
    "very_active": Decimal("100"), "extra_active": Decimal("100"),
}


def recompute(apps, schema_editor):
    Screening = apps.get_model("clinical", "PreConsultationScreening")
    ClientProfile = apps.get_model("profiles", "ClientProfile")
    sex_by_user = dict(ClientProfile.objects.values_list("user_id", "sex"))
    for s in Screening.objects.all():
        factor = FACTOR.get(sex_by_user.get(s.client_id))
        if factor is None or s.height_cm is None:
            continue
        height_m = s.height_cm / Decimal("100")
        dbw = (height_m * height_m * Decimal("22")).quantize(Decimal("0.01"))
        s.bmr_kcal = (dbw * factor * Decimal("24")).quantize(Decimal("0.01"))
        pa = s.bmr_kcal * ACTIVITY_PCT.get(s.activity_level, ACTIVITY_PCT["sedentary"]) / 100
        ter = (s.bmr_kcal + pa) * Decimal("1.10")
        s.tdee_kcal = (ter / 50).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * 50
        s.save(update_fields=["bmr_kcal", "tdee_kcal"])


class Migration(migrations.Migration):

    dependencies = [
        ("clinical", "0009_ncp_ter_split"),
        ("profiles", "0010_remove_chat_consultation_mode"),
    ]

    operations = [
        migrations.RunPython(recompute, migrations.RunPython.noop),
    ]
