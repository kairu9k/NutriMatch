"""Where users are told to write for help (appeals, account questions)."""

from django.conf import settings


def support_email():
    """The `support_email` system setting (editable in Admin > System
    Settings), falling back to settings.SUPPORT_EMAIL."""
    from .models import SystemSetting

    value = SystemSetting.objects.filter(key="support_email").values_list("value", flat=True).first()
    return (value or "").strip() or settings.SUPPORT_EMAIL
