"""Notifications already sent keep the wording they had, so the old phrases
with a dash or an arrow (2026-10-24 design pass: no " — " inside sentences,
no "→") are rewritten in place to match the new wording."""
from django.db import migrations

REPLACEMENTS = [
    ("subject", "Appointment confirmed — payment due", "Appointment confirmed, payment due"),
    ("content", "Open it in My Appointments → History to see your summary.",
     "Open My Appointments, then History, to see your summary."),
    ("content", "with a closing note — after that it ends automatically.",
     "with a closing note. After that it ends automatically."),
]


def forwards(apps, schema_editor):
    NotificationLog = apps.get_model("communication", "NotificationLog")
    for field, old, new in REPLACEMENTS:
        for n in NotificationLog.objects.filter(**{f"{field}__contains": old}).only("id", field):
            setattr(n, field, getattr(n, field).replace(old, new))
            n.save(update_fields=[field])


class Migration(migrations.Migration):
    dependencies = [("communication", "0008_unmute_reminders")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
