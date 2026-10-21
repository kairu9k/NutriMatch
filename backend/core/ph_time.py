"""Philippine time for "today" decisions. TIME_ZONE is UTC, so
timezone.localdate() is still yesterday in the Philippines until 8 AM.
Dates the app decides on (meal-log day, payout day, this month) come from
the server's clock in Philippine time — never from the client's device,
which a user can set to any date."""

from zoneinfo import ZoneInfo

from django.utils import timezone

PH_TZ = ZoneInfo("Asia/Manila")


def ph_now():
    return timezone.now().astimezone(PH_TZ)


def ph_today():
    return ph_now().date()


def ph_date(value):
    """The Philippine calendar date of an aware datetime."""
    return timezone.localdate(value, timezone=PH_TZ)
