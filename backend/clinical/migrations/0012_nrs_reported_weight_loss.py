from decimal import Decimal

from django.db import migrations


def recount(apps, schema_editor):
    """Screenings where the client ticked "Unintended weight loss" get it
    counted in NRS-2002 (grade 1, 2026-11-02; the box used to change nothing).
    Rebuilt from the saved symptom text and BMI; a score is only ever raised."""
    Screening = apps.get_model("clinical", "PreConsultationScreening")
    for s in Screening.objects.filter(symptoms__icontains="Unintended weight loss"):
        syms = s.symptoms or ""
        nutritional = 3 if s.bmi is not None and s.bmi < Decimal("18.5") else 1
        severity = 1 if ("Elevated blood glucose" in syms or "Recent hospitalization" in syms) else 0
        total = nutritional + severity
        if s.nrs_score is None or total > s.nrs_score:
            s.nrs_score = total
            s.nrs_risk = "high_risk" if total >= 5 else "at_risk" if total >= 3 else "no_risk"
            s.save(update_fields=["nrs_score", "nrs_risk"])


class Migration(migrations.Migration):
    dependencies = [("clinical", "0011_merge_20261102_1157")]
    operations = [migrations.RunPython(recount, migrations.RunPython.noop)]
