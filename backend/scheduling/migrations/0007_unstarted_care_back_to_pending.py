"""Active care where no consultation was completed and nothing is booked
(the first booking was confirmed, then cancelled) goes back to pending, so
the client leaves the RND's My Patients list (2026-10-23)."""

from django.db import migrations


def forwards(apps, schema_editor):
    Rel = apps.get_model("scheduling", "RndClientRelationship")
    for rel in Rel.objects.filter(status="active"):
        statuses = set(rel.appointments.values_list("status", flat=True))
        if statuses and not statuses & {"pending", "confirmed", "completed"}:
            rel.status = "pending"
            rel.started_at = None
            rel.save(update_fields=["status", "started_at"])


class Migration(migrations.Migration):
    dependencies = [("scheduling", "0006_discharge_requests")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
