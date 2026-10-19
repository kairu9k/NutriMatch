"""The per-task mute was removed (2026-10-19, user's call): the client's
"Reminders from your RND" switch is the only control, and tasks always show
on My tasks. Clears existing mutes so hidden tasks come back."""

from django.db import migrations


def unmute(apps, schema_editor):
    apps.get_model("communication", "Reminder").objects.filter(is_muted=True).update(is_muted=False)


class Migration(migrations.Migration):
    dependencies = [("communication", "0007_reminder_sms")]

    operations = [migrations.RunPython(unmute, migrations.RunPython.noop)]
