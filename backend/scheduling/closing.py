"""How a consultation closes (2026-11-16, user's plan: the call's attendance
record decides, so nobody has to press Mark complete, and money never sits in
limbo).

Video consultations, decided from scheduling/attendance.py when the room closes:

- Both in the call together for MIN_TOGETHER_MINUTES or more: **completed by
  itself** when the room closes at the scheduled end. The RND never presses
  Mark complete for a video call, and can't unless this holds (the server
  refuses).
- The RND waited (RND_MIN_PRESENT_MINUTES) and the client never joined, from
  NO_SHOW_AFTER_MINUTES after the start (so the client has time to arrive, and
  joining the room early doesn't count as waiting): the RND may mark a
  **no-show** (the client can dispute it, as before).
- Anything else (the RND was absent or there under 5 minutes, or they were
  together too briefly): only **a full refund** (the RND's "call didn't work").
- All of this happens when the room closes (2026-11-16, user's call: nothing
  should wait for a button the record already answers). The RND's own choices
  (a no-show once 15 minutes have passed, "the call didn't work") are made in
  the room while the call is on.

In-person consultations have no call record, so the RND's word stands: they
mark it complete or a no-show, and the client may dispute either for
DISPUTE_DAYS. If it is still open AUTO_CLOSE_DAYS after the end, it goes to
the admin's Needs attention list (nothing closes it by itself).

Run lazily wherever expire_unpaid_appointments runs."""

from datetime import timedelta

from django.utils import timezone

from .attendance import minutes_in_call
from .demo import call_counts_as_held
from .models import Appointment
from .serializers import AUTO_CLOSE_DAYS, NO_SHOW_AFTER_MINUTES, RND_MIN_PRESENT_MINUTES
from .video_call import end_of


def no_show_opens_at(a):
    """A no-show can be marked from here: NO_SHOW_AFTER_MINUTES after the start,
    so the client has time to arrive (the same wait a client gives an absent RND)."""
    return a.scheduled_at + timedelta(minutes=NO_SHOW_AFTER_MINUTES)


def close_options(a, now=None):
    """What can close this consultation: {"complete", "no_show", "refund"}.
    Refunding ("the call didn't work") is always possible."""
    now = now or timezone.now()
    waited_long_enough = now >= no_show_opens_at(a)
    if a.type != Appointment.Type.VIDEO:
        return {"complete": True, "no_show": waited_long_enough, "refund": True}
    return {
        "complete": call_counts_as_held(a, now),
        "no_show": waited_long_enough and minutes_in_call(a, "rnd", now) >= RND_MIN_PRESENT_MINUTES and a.client_joined_at is None,
        "refund": True,
    }


def rnd_absent(a, now=None):
    """The client was in the call and the RND wasn't there long enough: a
    late cancel by the RND (it counts toward the admin's late-cancel flag)."""
    return (a.type == Appointment.Type.VIDEO and a.client_joined_at is not None
            and minutes_in_call(a, "rnd", now or timezone.now()) < RND_MIN_PRESENT_MINUTES)


# ----------------------------------------------------------------- closings
def _audit(action, a, values):
    from core.models import AuditLog

    AuditLog.objects.create(user=None, action=action, table_name="appointments", record_id=a.id, new_values=values)


def _complete(a, now):
    from communication.services import notify

    from .attendance import attendance_line
    from .views import format_ph_datetime

    a.status = Appointment.Status.COMPLETED
    a.completed_at = now  # starts the payout hold
    a.save(update_fields=["status", "completed_at", "updated_at"])
    _audit("appointment.auto_completed", a, {"attendance": attendance_line(a, now)})
    when = format_ph_datetime(a.scheduled_at)
    rel = a.relationship
    notify(recipient=rel.client, notifiable_type="appointment", notifiable_id=a.id, subject="Your consultation summary is ready",
           content=f"Your consultation on {when} is complete. Open My Appointments, then History, to see your summary.")
    notify(recipient=rel.rnd, notifiable_type="appointment", notifiable_id=a.id, subject="Consultation completed",
           content=f"Your consultation with {rel.client.full_name} on {when} was completed automatically. "
                   "Write or finish the NCP record from their chart.")


def _no_show(a, now):
    from communication.services import notify

    from .attendance import attendance_line
    from .emails import email_no_show
    from .services import close_reopened_care_if_idle
    from .views import format_ph_datetime

    a.status = Appointment.Status.NO_SHOW
    a.completed_at = now  # the payout hold, which is also the dispute window
    a.cancellation_reason = "The client didn't attend."
    a.save(update_fields=["status", "completed_at", "cancellation_reason", "updated_at"])
    close_reopened_care_if_idle(a.relationship)
    _audit("appointment.auto_no_show", a, {"attendance": attendance_line(a, now)})
    when = format_ph_datetime(a.scheduled_at)
    notify(recipient=a.relationship.client, notifiable_type="appointment", notifiable_id=a.id, subject="Marked as not attending",
           content=(f"Your consultation on {when} was marked as not attended, because you didn't join the video call, "
                    "so it isn't refunded. If this is wrong, you can dispute it within 3 days from Help & Support (bottom right), Dispute a consultation."))
    email_no_show(a)


def _refund(a, now):
    from billing.services import settle_cancelled_appointment
    from communication.services import notify

    from .attendance import attendance_line
    from .services import close_reopened_care_if_idle
    from .views import format_ph_datetime

    late = rnd_absent(a, now)
    a.status = Appointment.Status.CANCELLED
    a.cancellation_reason = "The consultation didn't take place in the video call, so it was cancelled and refunded."
    a.cancelled_by, a.cancelled_at = (Appointment.CancelledBy.RND_ABSENT if late else Appointment.CancelledBy.SYSTEM), now
    a.cancelled_late = late
    a.save(update_fields=["status", "cancellation_reason", "cancelled_by", "cancelled_at", "cancelled_late", "updated_at"])
    settle_cancelled_appointment(a)  # refund pending, the client is told
    close_reopened_care_if_idle(a.relationship)
    _audit("appointment.auto_refunded", a, {"attendance": attendance_line(a, now)})
    when = format_ph_datetime(a.scheduled_at)
    notify(recipient=a.relationship.rnd, notifiable_type="appointment", notifiable_id=a.id, subject="Consultation cancelled",
           content=(f"Your consultation with {a.relationship.client.full_name} on {when} wasn't closed and the video call "
                    "doesn't show it took place, so it was cancelled and refunded."))


def auto_close_due(now=None, **scope):
    """Close every ended video consultation from its call record: completed,
    a no-show, or a full refund. Returns how many were closed."""
    from billing.services import is_appointment_paid

    now = now or timezone.now()
    due = (Appointment.objects.filter(status=Appointment.Status.CONFIRMED, type=Appointment.Type.VIDEO,
                                      scheduled_at__lte=now, **scope)
           .select_related("relationship__client", "relationship__rnd"))
    closed = 0
    for a in due:
        end = end_of(a)
        if end > now or not is_appointment_paid(a):  # unpaid ones are cancelled by the pay deadline
            continue
        options = close_options(a, now)
        if options["complete"]:
            _complete(a, now)
        elif options["no_show"]:
            _no_show(a, now)
        else:
            _refund(a, now)
        closed += 1
    return closed


def open_too_long(now=None):
    """In-person consultations still confirmed AUTO_CLOSE_DAYS after their end
    (nobody closed them): for the admin's Needs attention list."""
    now = now or timezone.now()
    rows = (Appointment.objects.filter(status=Appointment.Status.CONFIRMED, type=Appointment.Type.IN_PERSON,
                                       scheduled_at__lte=now - timedelta(days=AUTO_CLOSE_DAYS))
            .select_related("relationship__client", "relationship__rnd"))
    return [a for a in rows if end_of(a) + timedelta(days=AUTO_CLOSE_DAYS) <= now]
