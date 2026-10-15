"""Chat consultations were removed (adviser's call, 2026-10-15): consultations
are video or in-person only. Strip "chat" from every RND's offered formats;
an RND left with nothing offers video. Past chat appointments stay as history.
"""

from django.db import migrations


def strip_chat(apps, schema_editor):
    RndProfile = apps.get_model("profiles", "RndProfile")
    for profile in RndProfile.objects.all():
        modes = list(profile.consultation_modes or [])
        if "chat" in modes:
            modes = [m for m in modes if m != "chat"] or ["video"]
            profile.consultation_modes = modes
            profile.save(update_fields=["consultation_modes"])


class Migration(migrations.Migration):
    dependencies = [("profiles", "0009_rnd_time_off")]

    operations = [migrations.RunPython(strip_chat, migrations.RunPython.noop)]
