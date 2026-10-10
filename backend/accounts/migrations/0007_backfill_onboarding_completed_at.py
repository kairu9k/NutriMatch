from django.db import migrations
from django.utils import timezone


def mark_existing_onboarded(apps, schema_editor):
    """Accounts that existed before onboarding was added keep working as
    before (user's decision, 2026-10-10). RNDs only if already verified —
    a pending RND still has to be approved first."""
    User = apps.get_model("accounts", "User")
    RndProfile = apps.get_model("profiles", "RndProfile")
    now = timezone.now()
    User.objects.exclude(role="rnd").filter(onboarding_completed_at__isnull=True).update(onboarding_completed_at=now)
    verified_rnd_ids = RndProfile.objects.filter(is_verified=True).values_list("user_id", flat=True)
    User.objects.filter(id__in=list(verified_rnd_ids), onboarding_completed_at__isnull=True).update(onboarding_completed_at=now)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_user_onboarding_completed_at"),
        ("profiles", "0006_rndprofile_review_status"),
    ]

    operations = [migrations.RunPython(mark_existing_onboarded, migrations.RunPython.noop)]
