"""Rescheduling a paid consultation the RND can't make (2026-11-16, the
adviser's idea, agreed with the user) so the client doesn't have to pay again.

Instead of cancelling with a refund, the RND offers a new time from their
open hours with a reason. The appointment goes to ``rescheduling`` and the
client can:

- **accept** — the same appointment moves and is confirmed again, with the
  same paid invoice (fee and commission stay frozen);
- **propose another time** — from the RND's open slots; the RND then accepts,
  proposes another, or cancels with a full refund;
- **get a refund** — any time while it's waiting.

At most MAX_PROPOSALS proposals in all (after the third the client can only
accept or take the refund). Each waits ANSWER_HOURS, or until
ANSWER_BEFORE_MINUTES before the offered time, whichever is first; an
unanswered one ends with a full refund. A waiting proposal holds its slot
(``held_intervals``). Moving a consultation in its last 30 minutes still
counts as a late cancel, like cancelling it. The client can't start a
reschedule (not included)."""

from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd

from .models import Appointment, RescheduleProposal

MAX_PROPOSALS = 3
ANSWER_HOURS = 48
ANSWER_BEFORE_MINUTES = 60
OFFER_WITHIN_DAYS = 14
# The new time must leave the other person at least an hour to answer
# before the ANSWER_BEFORE_MINUTES cut-off, so a proposal never starts expired.
MIN_LEAD_MINUTES = 120
MIN_REASON = 10

By = RescheduleProposal.By
P = RescheduleProposal.Status


# --------------------------------------------------------------- read helpers
def waiting_proposal(appointment):
    return appointment.reschedule_proposals.filter(status=P.WAITING).order_by("-created_at").first()


def held_intervals(rnd_id=None, client_id=None):
    """Times held by waiting proposals: [(start, end)]."""
    from .serializers import DEFAULT_SESSION_MINUTES

    qs = RescheduleProposal.objects.filter(status=P.WAITING, appointment__status=Appointment.Status.RESCHEDULING)
    if rnd_id is not None:
        qs = qs.filter(appointment__relationship__rnd_id=rnd_id)
    if client_id is not None:
        qs = qs.filter(appointment__relationship__client_id=client_id)
    return [(p.scheduled_at, p.scheduled_at + timedelta(minutes=p.appointment.duration_minutes or DEFAULT_SESSION_MINUTES))
            for p in qs.select_related("appointment")]


def _end(appointment, start):
    from .serializers import DEFAULT_SESSION_MINUTES

    return start + timedelta(minutes=appointment.duration_minutes or DEFAULT_SESSION_MINUTES)


def open_slots(appointment, now=None):
    """Every start the RND could move this consultation to (ISO)."""
    from profiles.public import next_open_slots

    from datetime import datetime

    slots = next_open_slots(appointment.relationship.rnd_id, count=500, now=now, lead_minutes=MIN_LEAD_MINUTES,
                            days=OFFER_WITHIN_DAYS, minutes=appointment.duration_minutes or 60)
    return [s for s in slots if datetime.fromisoformat(s) > appointment.scheduled_at]


def check_new_time(appointment, start, now=None):
    """Same rules as booking, inside OFFER_WITHIN_DAYS and at least
    MIN_LEAD_MINUTES ahead and after the current time; this consultation's
    own times don't count."""
    from profiles.services import overlaps_time_off

    from .serializers import fits_rnd_availability, overlapping_appointments

    now = now or timezone.now()
    end = _end(appointment, start)
    rel = appointment.relationship
    if start < now + timedelta(minutes=MIN_LEAD_MINUTES):
        raise ValidationError({"scheduled_at": [f"Pick a time at least {MIN_LEAD_MINUTES // 60} hours from now, so there's time to answer."]})
    if start > now + timedelta(days=OFFER_WITHIN_DAYS):
        raise ValidationError({"scheduled_at": [f"Pick a time within the next {OFFER_WITHIN_DAYS} days."]})
    # Only later times: an earlier one could clash with plans the client
    # made around the original booking.
    if start <= appointment.scheduled_at:
        raise ValidationError({"scheduled_at": ["Pick a time after the consultation's current time."]})
    if not fits_rnd_availability(rel.rnd_id, start, end):
        raise ValidationError({"scheduled_at": ["That time is outside the RND's weekly hours. Pick one of the listed times."]})
    if overlaps_time_off(rel.rnd_id, start, end):
        raise ValidationError({"scheduled_at": ["The RND blocked that time off. Pick another time."]})
    for scope in ({"relationship__rnd_id": rel.rnd_id}, {"relationship__client_id": rel.client_id}):
        if overlapping_appointments(start, end, **scope).exclude(pk=appointment.pk).exists():
            raise ValidationError({"scheduled_at": ["That time was just taken. Pick another one."]})


def payload(appointment, now=None):
    """What both sides see while rescheduling (and the history afterwards)."""
    proposals = list(appointment.reschedule_proposals.all())
    if not proposals:
        return None
    waiting = next((p for p in reversed(proposals) if p.status == P.WAITING), None)
    row = lambda p: {  # noqa: E731
        "id": p.id, "proposed_by": p.proposed_by, "from_at": p.from_at, "scheduled_at": p.scheduled_at,
        "note": p.note, "status": p.status, "status_label": p.get_status_display(),
        "expires_at": p.expires_at, "answered_at": p.answered_at, "created_at": p.created_at,
    }
    return {
        "waiting": row(waiting) if waiting else None,
        # whose answer it waits for
        "turn": (By.CLIENT if waiting.proposed_by == By.RND else By.RND) if waiting else None,
        "proposals_left": max(0, MAX_PROPOSALS - len(proposals)),
        "original_at": proposals[0].from_at,
        "history": [row(p) for p in proposals],
    }


# ------------------------------------------------------------------- actions
def _when(dt):
    from .views import format_ph_datetime

    return format_ph_datetime(dt)


def _audit(user, action, appointment, **values):
    from core.models import AuditLog

    AuditLog.objects.create(user=user, action=action, table_name="appointments", record_id=appointment.id,
                            new_values={k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in values.items()})


def _lock(appointment):
    return Appointment.objects.select_for_update().select_related("relationship__client", "relationship__rnd").get(pk=appointment.pk)


def _create(appointment, by, start, note, now):
    expires = min(now + timedelta(hours=ANSWER_HOURS), start - timedelta(minutes=ANSWER_BEFORE_MINUTES))
    return RescheduleProposal.objects.create(appointment=appointment, proposed_by=by, from_at=appointment.scheduled_at,
                                             scheduled_at=start, note=note, expires_at=expires)


def offer(appointment, user, start, reason, category=None, now=None):
    """The RND can't make a paid, confirmed consultation and offers a new time."""
    from billing.services import is_appointment_paid

    from .serializers import CLIENT_CANCEL_CUTOFF_MINUTES

    now = now or timezone.now()
    reason = (reason or "").strip()[:500]
    with transaction.atomic():
        appt = _lock(appointment)
        if appt.status != Appointment.Status.CONFIRMED or not is_appointment_paid(appt):
            raise ValidationError({"detail": "Only a paid, confirmed consultation can be moved to a new time."})
        late = appt.scheduled_at - timedelta(minutes=CLIENT_CANCEL_CUTOFF_MINUTES) <= now
        if late:
            category = (category or "").strip()
            if category not in Appointment.CancelCategory.values:
                raise ValidationError({"category": "Pick why you can't make it: emergency, technical problem or other."})
            if category == Appointment.CancelCategory.OTHER and len(reason) < MIN_REASON:
                raise ValidationError({"reason": f"Tell the client why, in at least {MIN_REASON} characters."})
        elif len(reason) < MIN_REASON:
            raise ValidationError({"reason": f"Tell the client why, in at least {MIN_REASON} characters."})
        check_new_time(appt, start, now)
        proposal = _create(appt, By.RND, start, reason or Appointment.CancelCategory(category).label, now)
        appt.status = Appointment.Status.RESCHEDULING
        fields = ["status", "updated_at"]
        if late:  # still a last-minute cancel for the admin's count
            appt.cancelled_late, appt.cancel_category, appt.cancelled_at = True, category, now
            fields += ["cancelled_late", "cancel_category", "cancelled_at"]
        appt.save(update_fields=fields)
        _audit(user, "appointment.reschedule_offered", appt, scheduled_at=start, from_at=proposal.from_at, late=late)

    from communication.services import notify
    from communication.sms import text_client

    from .emails import email_new_time_offered

    rnd, client = appt.relationship.rnd, appt.relationship.client
    notify(recipient=client, notifiable_type="appointment", notifiable_id=appt.id, subject="New time offered",
           content=f"RND {rnd.full_name} can't make your consultation on {_when(proposal.from_at)} and offered "
                   f"{_when(start)} instead. Reason: {proposal.note} Accept it, pick another time or get a full refund "
                   f"in My Appointments by {_when(proposal.expires_at)}.")
    email_new_time_offered(appt, proposal)
    from communication.reminders import _when as short_when

    text_client(client, f"RND {rnd.full_name} can't make your consultation on {short_when(proposal.from_at)} and offered a new time. "
                        "Open the app to accept, pick another time or get a refund.")
    return appt


def respond(appointment, user, by, action, start=None, note="", now=None):
    """accept | propose (another time) | refund. `by` is who answers."""
    now = now or timezone.now()
    note = (note or "").strip()[:500]
    expire_due(now=now, pk=appointment.pk)  # an answer after the deadline is too late
    with transaction.atomic():
        appt = _lock(appointment)
        proposal = waiting_proposal(appt)
        if appt.status != Appointment.Status.RESCHEDULING or proposal is None:
            raise ValidationError({"detail": "There's no new time waiting for an answer on this consultation."})
        if action == "refund":
            if by != By.CLIENT:
                raise PermissionDenied("Use Cancel with full refund.")
            return _end_with_refund(appt, proposal, user, P.REFUNDED, chosen_by=By.CLIENT, now=now)
        if proposal.proposed_by == by:
            raise ValidationError({"detail": "This time is waiting for the other person's answer."})
        if action == "accept":
            return _accept(appt, proposal, user, by, now)
        if action != "propose":
            raise ValidationError({"action": "Choose accept, propose or refund."})
        if appt.reschedule_proposals.count() >= MAX_PROPOSALS:
            raise ValidationError({"detail": f"Three times have been proposed already. Accept this one"
                                             f"{' or get a full refund' if by == By.CLIENT else ' or cancel with a full refund'}."})
        if start is None:
            raise ValidationError({"scheduled_at": ["Pick a time."]})
        proposal.status, proposal.answered_at = P.COUNTERED, now
        proposal.save(update_fields=["status", "answered_at"])  # its slot is no longer held
        check_new_time(appt, start, now)
        new = _create(appt, by, start, note, now)
        _audit(user, "appointment.reschedule_proposed", appt, scheduled_at=start, by=by)

    from communication.services import notify

    rel = appt.relationship
    other = rel.client if by == By.RND else rel.rnd
    name = f"RND {rel.rnd.full_name}" if by == By.RND else rel.client.full_name
    notify(recipient=other, notifiable_type="appointment", notifiable_id=appt.id, subject="Another time proposed",
           content=f"{name} proposed {_when(start)} for the consultation instead of {_when(proposal.scheduled_at)}."
                   + (f" Note: {note}" if note else "")
                   + f" Answer by {_when(new.expires_at)}, or it's cancelled with a full refund.")
    return appt


def _accept(appt, proposal, user, by, now):
    from communication.models import Reminder
    from communication.services import notify

    old = appt.scheduled_at
    proposal.status, proposal.answered_at = P.ACCEPTED, now
    proposal.save(update_fields=["status", "answered_at"])
    appt.scheduled_at = proposal.scheduled_at
    appt.status = Appointment.Status.CONFIRMED
    # a fresh start: nobody has been in the new call yet
    for f in ("rnd_joined_at", "client_joined_at", "rnd_left_at", "client_left_at", "together_since", "rnd_in_since", "client_in_since"):
        setattr(appt, f, None)
    appt.together_seconds = appt.rnd_seconds = appt.client_seconds = 0
    appt.save()
    # the 24-hour and 1-hour reminders go out again for the new time
    Reminder.objects.filter(source_key__startswith=f"appt:{appt.id}:").delete()
    _audit(user, "appointment.rescheduled", appt, scheduled_at=appt.scheduled_at, from_at=old, accepted_by=by)

    rel = appt.relationship
    other = rel.rnd if by == By.CLIENT else rel.client
    name = rel.client.full_name if by == By.CLIENT else f"RND {rel.rnd.full_name}"
    notify(recipient=other, notifiable_type="appointment", notifiable_id=appt.id, subject="Consultation moved",
           content=f"{name} accepted the new time. The consultation is now on {_when(appt.scheduled_at)}"
                   + (". It's already paid." if other == rel.client else "."))
    return appt


def _end_with_refund(appt, proposal, user, outcome, chosen_by, now, reason=""):
    """Cancelled with a full refund: the client chose it, the RND cancelled,
    or nobody answered in time. It still counts as the RND's cancel."""
    from billing.services import settle_cancelled_appointment
    from communication.services import notify

    from .services import close_reopened_care_if_idle

    first = appt.reschedule_proposals.order_by("created_at").first()
    if proposal is not None:
        proposal.status, proposal.answered_at = outcome, now
        proposal.save(update_fields=["status", "answered_at"])
    appt.status = Appointment.Status.CANCELLED
    appt.cancelled_by = Appointment.CancelledBy.RND
    appt.cancelled_at = appt.cancelled_at if appt.cancelled_late else now
    appt.cancellation_reason = (reason or (first.note if first else "") or "The RND couldn't make it.")[:500]
    appt.save(update_fields=["status", "cancelled_by", "cancelled_at", "cancellation_reason", "updated_at"])
    invoice = settle_cancelled_appointment(appt)  # refund pending, the client is told
    close_reopened_care_if_idle(appt.relationship)
    _audit(user, "appointment.reschedule_refunded", appt, outcome=outcome, chosen_by=chosen_by,
           invoice_status=invoice.status if invoice else None)

    rel = appt.relationship
    when = _when(first.from_at if first else appt.scheduled_at)
    if chosen_by == By.CLIENT:
        notify(recipient=rel.rnd, notifiable_type="appointment", notifiable_id=appt.id, subject="Consultation cancelled",
               content=f"{rel.client.full_name} chose a full refund instead of a new time for the consultation on {when}.")
    elif chosen_by == By.RND:
        notify(recipient=rel.client, notifiable_type="appointment", notifiable_id=appt.id, subject="Consultation cancelled",
               content=f"RND {rel.rnd.full_name} cancelled the consultation on {when} instead of moving it. "
                       f"Reason: {appt.cancellation_reason} You get a full refund.")
    else:
        for who, text in ((rel.client, "Nobody answered the proposed time in time, so the consultation is cancelled and you get a full refund."),
                          (rel.rnd, f"The proposed time for {rel.client.full_name}'s consultation wasn't answered in time, so it's cancelled with a full refund.")):
            notify(recipient=who, notifiable_type="appointment", notifiable_id=appt.id, subject="Reschedule expired", content=text)
    if chosen_by != By.CLIENT:
        from .emails import email_cancelled_by_rnd

        email_cancelled_by_rnd(appt, kind="normal",
                               paid_amount=invoice.amount if invoice is not None and invoice.status == "refund_pending" else None)
    return appt


def rnd_cancel(appointment, user, reason, now=None):
    """The RND cancels while rescheduling (Cancel with full refund)."""
    now = now or timezone.now()
    reason = (reason or "").strip()[:500]
    if len(reason) < MIN_REASON:
        raise ValidationError({"reason": f"Tell the client why, in at least {MIN_REASON} characters."})
    with transaction.atomic():
        appt = _lock(appointment)
        if appt.status != Appointment.Status.RESCHEDULING:
            raise ValidationError({"detail": "This consultation isn't being rescheduled."})
        return _end_with_refund(appt, waiting_proposal(appt), user, P.REFUNDED, chosen_by=By.RND, now=now, reason=reason)


def end_for_admin(appointment):
    """An admin cancel or a deactivated RND closes the waiting proposal."""
    appointment.reschedule_proposals.filter(status=P.WAITING).update(status=P.REFUNDED, answered_at=timezone.now())


def expire_due(now=None, **scope):
    """Waiting proposals past their answer time end with a full refund.
    Runs with expire_unpaid_appointments (wherever appointments are listed).
    Returns how many."""
    now = now or timezone.now()
    due = (RescheduleProposal.objects.filter(status=P.WAITING, expires_at__lte=now,
                                             appointment__status=Appointment.Status.RESCHEDULING,
                                             **{f"appointment__{k}": v for k, v in scope.items()})
           .values_list("appointment_id", flat=True))
    count = 0
    for appt_id in list(due):
        with transaction.atomic():
            appt = Appointment.objects.select_for_update().select_related("relationship__client", "relationship__rnd").get(pk=appt_id)
            proposal = waiting_proposal(appt)
            if appt.status != Appointment.Status.RESCHEDULING or proposal is None or proposal.expires_at > now:
                continue
            _end_with_refund(appt, proposal, None, P.EXPIRED, chosen_by=None, now=now)
            count += 1
    return count


# --------------------------------------------------------------------- views
def _start(request):
    from rest_framework.fields import DateTimeField

    value = request.data.get("scheduled_at")
    if not value:
        return None
    try:
        return DateTimeField().to_internal_value(value)
    except ValidationError:
        raise ValidationError({"scheduled_at": ["Pick a valid time."]})


def _response(request, appt):
    from .serializers import AppointmentSerializer

    appt.refresh_from_db()
    return Response(AppointmentSerializer(appt, context={"request": request}).data)


class RndRescheduleView(APIView):
    """POST {action: offer | accept | propose, scheduled_at, reason, category}.
    Cancel with full refund while rescheduling is the normal cancel endpoint."""

    permission_classes = [IsRnd]

    def post(self, request, pk):
        appt = get_object_or_404(Appointment.objects.filter(relationship__rnd=request.user), pk=pk)
        action = request.data.get("action")
        if action == "offer":
            start = _start(request)
            if start is None:
                raise ValidationError({"scheduled_at": ["Pick a new time."]})
            offer(appt, request.user, start, request.data.get("reason"), request.data.get("category"))
        else:
            respond(appt, request.user, By.RND, action, _start(request), request.data.get("reason") or request.data.get("note"))
        return _response(request, appt)


class ClientRescheduleView(APIView):
    """POST {action: accept | propose | refund, scheduled_at, note}."""

    permission_classes = [IsClient]

    def post(self, request, pk):
        appt = get_object_or_404(Appointment.objects.filter(relationship__client=request.user), pk=pk)
        respond(appt, request.user, By.CLIENT, request.data.get("action"), _start(request), request.data.get("note"))
        return _response(request, appt)


class RescheduleSlotsView(APIView):
    """GET: the times this consultation can move to (the RND's open slots in
    the next 14 days), for the RND or the client of this appointment."""

    def get(self, request, pk):
        user = request.user
        appt = get_object_or_404(Appointment.objects.select_related("relationship"), pk=pk)
        if user.id not in (appt.relationship.rnd_id, appt.relationship.client_id):
            raise PermissionDenied("Not your consultation.")
        return Response({"slots": open_slots(appt), "duration_minutes": appt.duration_minutes or 60})
