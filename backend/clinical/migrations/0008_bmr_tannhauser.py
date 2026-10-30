from decimal import Decimal

from django.db import migrations

# BMR switched from Mifflin-St Jeor to Tannhauser's method (2026-10-31, asked
# for by the RND resource person). Recompute every saved screening so old and
# new patients use the same method. Same formula as clinical.services
# (copied here: a migration mustn't import code that can change later).
FACTOR = {"male": Decimal("1.0"), "female": Decimal("0.9")}
ACTIVITY = {
    "sedentary": Decimal("1.2"), "lightly_active": Decimal("1.375"), "moderately_active": Decimal("1.55"),
    "very_active": Decimal("1.725"), "extra_active": Decimal("1.9"),
}


def recompute(apps, schema_editor):
    Screening = apps.get_model("clinical", "PreConsultationScreening")
    ClientProfile = apps.get_model("profiles", "ClientProfile")
    sex_by_user = dict(ClientProfile.objects.values_list("user_id", "sex"))
    for s in Screening.objects.all():
        factor = FACTOR.get(sex_by_user.get(s.client_id))
        if factor is None or s.height_cm is None:
            continue
        base = s.height_cm - Decimal("100")
        dbw = (base - base * Decimal("0.10")).quantize(Decimal("0.01"))
        s.bmr_kcal = (dbw * factor * Decimal("24")).quantize(Decimal("0.01"))
        s.tdee_kcal = (s.bmr_kcal * ACTIVITY.get(s.activity_level, ACTIVITY["sedentary"])).quantize(Decimal("0.01"))
        s.save(update_fields=["bmr_kcal", "tdee_kcal"])


class Migration(migrations.Migration):

    dependencies = [
        ("clinical", "0007_lab_result_decline"),
        ("profiles", "0010_remove_chat_consultation_mode"),
    ]

    operations = [
        migrations.RunPython(recompute, migrations.RunPython.noop),
    ]
