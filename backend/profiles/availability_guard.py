"""An RND can't take away weekly hours that an upcoming booking sits in
(2026-10-26, user's rule): removing or shrinking a block is refused while a
pending or confirmed consultation inside it is still ahead. Bookings that
already sat outside the RND's hours (booked before a change) don't block
unrelated edits; only the ones this change would leave uncovered do."""

from datetime import timedelta
from types import SimpleNamespace

from django.utils import timezone

from .models import RndAvailabilitySchedule


def _covered(appt, blocks, tz):
    start = appt.scheduled_at.astimezone(tz)
    end = (appt.scheduled_at + timedelta(minutes=appt.duration_minutes or 60)).astimezone(tz)
    day = start.date()
    weekday = (day.weekday() + 1) % 7  # Python Monday=0 -> model Sunday=0
    for b in blocks:
        if b.day_of_week != weekday:
            continue
        if getattr(b, "effective_from", None) and b.effective_from > day:
            continue
        if getattr(b, "effective_to", None) and b.effective_to < day:
            continue
        if b.start_time <= start.time() and end.time() <= b.end_time:
            return True
    return False


def bookings_left_outside(rnd, *, remove_id, replacement=None):
    """Upcoming bookings the RND's hours cover now but wouldn't after removing
    block `remove_id` (and adding `replacement`, for an edit)."""
    from scheduling.models import Appointment
    from scheduling.serializers import PH_TZ

    before = list(RndAvailabilitySchedule.objects.filter(rnd=rnd, is_available=True))
    after = [b for b in before if b.id != remove_id]
    if replacement is not None:
        after.append(SimpleNamespace(**replacement))
    upcoming = (Appointment.objects.filter(relationship__rnd=rnd, status__in=["pending", "confirmed"], scheduled_at__gte=timezone.now())
                .select_related("relationship__client").order_by("scheduled_at"))
    return [a for a in upcoming if _covered(a, before, PH_TZ) and not _covered(a, after, PH_TZ)]


def refusal(bookings):
    from scheduling.views import format_ph_datetime

    first = bookings[0]
    more = f" and {len(bookings) - 1} more" if len(bookings) > 1 else ""
    return {
        "detail": (f"You have a booking in these hours: {first.relationship.client.full_name} on "
                   f"{format_ph_datetime(first.scheduled_at)}{more}. Keep these hours until it's done, "
                   "or reschedule or cancel the booking first."),
        "bookings": [{"id": a.id, "client": a.relationship.client.full_name, "scheduled_at": a.scheduled_at} for a in bookings],
    }
