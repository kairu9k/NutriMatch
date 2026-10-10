from django.db import migrations


def approve_verified(apps, schema_editor):
    """Already-verified RNDs are approved; everyone else stays pending."""
    RndProfile = apps.get_model("profiles", "RndProfile")
    RndProfile.objects.filter(is_verified=True).update(review_status="approved")


class Migration(migrations.Migration):
    dependencies = [("profiles", "0006_rndprofile_review_status")]

    operations = [migrations.RunPython(approve_verified, migrations.RunPython.noop)]
