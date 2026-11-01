from django.db import migrations
from django.utils import timezone


def cancel(apps, schema_editor):
    """Open lab requests left on care that already ended (discharge didn't close them before)."""
    LabRequest = apps.get_model("clinical", "LabRequest")
    LabRequest.objects.filter(status="open").filter(relationship__status="discharged").update(
        status="cancelled", cancelled_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [
        ("clinical", "0009_ncp_ter_split"),
        ("scheduling", "0007_unstarted_care_back_to_pending"),
    ]

    operations = [migrations.RunPython(cancel, migrations.RunPython.noop)]
