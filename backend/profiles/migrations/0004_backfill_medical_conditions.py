from django.db import migrations


def copy_signup_concern_to_conditions(apps, schema_editor):
    """Registration used to store the client's primary health concern only in
    health_goals, so medical_conditions (what the RND's patient list reads)
    was always empty. Copy it over for existing clients who have no
    conditions yet. "Other" is skipped — it carries no clinical meaning."""
    ClientHealthProfile = apps.get_model("profiles", "ClientHealthProfile")
    for hp in ClientHealthProfile.objects.filter(medical_conditions__isnull=True):
        goals = hp.health_goals or []
        concern = goals[0].strip() if goals and isinstance(goals[0], str) else ""
        if concern and concern.lower() != "other":
            hp.medical_conditions = [concern]
            hp.save(update_fields=["medical_conditions"])


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0003_rndprofile_prc_license_image_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_signup_concern_to_conditions, migrations.RunPython.noop),
    ]
