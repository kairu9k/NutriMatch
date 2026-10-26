"""Care-relationship helpers for scheduling. (Video calls are NutriMatch's own
WebRTC call since 2026-10-26: scheduling/video_call.py + consumers.py.)"""


def current_rnd_relationship(client, exclude_rnd_id=None):
    """One RND at a time (user's rule, 2026-10-12): the client's care
    relationship that blocks booking a *different* RND, or None.

    Blocks: an active relationship (until that RND discharges them), or a
    pending one that still has a booking waiting or coming up (a first
    booking the RND hasn't confirmed yet). A pending relationship whose
    booking was declined, cancelled or expired doesn't block."""
    from django.utils import timezone

    from .discharge_requests import process_due_discharge_requests
    from .models import Appointment, RndClientRelationship

    process_due_discharge_requests(client=client)  # a request's 3 days may be up
    qs = RndClientRelationship.objects.filter(client=client).select_related("rnd")
    if exclude_rnd_id is not None:
        qs = qs.exclude(rnd_id=exclude_rnd_id)
    active = qs.filter(status=RndClientRelationship.Status.ACTIVE).first()
    if active:
        return active
    return qs.filter(
        status=RndClientRelationship.Status.PENDING,
        appointments__status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
        appointments__scheduled_at__gte=timezone.now(),
    ).distinct().first()


def close_reopened_care_if_idle(relationship):
    """Run after a booking is cancelled, declined or expired, once nothing
    else is waiting:

    - a discharged client who booked again goes back to discharged, so chat
      stays closed (2026-10-15);
    - care where no consultation was ever completed goes back to *pending*
      (2026-10-23) — the client isn't the RND's patient: they leave My
      Patients, the chart is read-only and they can book another RND."""
    from django.utils import timezone

    from .models import Appointment, RndClientRelationship

    relationship.refresh_from_db()
    appts = relationship.appointments
    if appts.filter(status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]).exists():
        return
    if relationship.status == RndClientRelationship.Status.PENDING and relationship.discharge_reason:
        relationship.status = RndClientRelationship.Status.DISCHARGED
        relationship.ended_at = timezone.now()
        relationship.save(update_fields=["status", "ended_at", "updated_at"])
    elif (relationship.status == RndClientRelationship.Status.ACTIVE
          and not appts.filter(status=Appointment.Status.COMPLETED).exists()):
        relationship.status = RndClientRelationship.Status.PENDING
        relationship.started_at = None
        relationship.save(update_fields=["status", "started_at", "updated_at"])
