from django.db import migrations
from django.db.models import F


def backfill(apps, schema_editor):
    """Appointments completed before completed_at existed: use their last
    update (when the RND marked them complete) for the payout hold."""
    Appointment = apps.get_model("scheduling", "Appointment")
    Appointment.objects.filter(status="completed", completed_at__isnull=True).update(completed_at=F("updated_at"))


class Migration(migrations.Migration):
    dependencies = [("scheduling", "0003_appointment_completed_at")]

    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
