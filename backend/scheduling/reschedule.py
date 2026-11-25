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
counts as a late cancel, like cancelling it.

The client can ask too (2026-11-23, the adviser): ``request`` on a confirmed
consultation, paid or not, until REQUEST_CUTOFF_MINUTES before it; only the
RND confirms it (accept, propose another time, or decline). Declined,
withdrawn or unanswered, the original booking stays: no refund and nothing
cancelled, and the request expires an hour before the booked time so the
original consultation can still happen. A booking still waiting for the RND
just changes its requested time (``change_pending``).

Every new time is later than the current one (never earlier), at least
MIN_LEAD_MINUTES ahead, and at most OFFER_WITHIN_DAYS after the time first
booked, so a consultation can't keep drifting later (user's calls,
2026-11-23). MAX_PROPOSALS counts per round (one reschedule, start to end)."""

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
# the client can ask for a new time until this long before the consultation
REQUEST_CUTOFF_MINUTES = 120

By = RescheduleProposal.By
P = RescheduleProposal.Status


# --------------------------------------------------------------- read helpers
ENDED = (P.ACCEPTED, P.REFUNDED, P.EXPIRED, P.DECLINED, P.WITHDRAWN)


def waiting_proposal(appointment):
    return appointment.reschedule_proposals.filter(status=P.WAITING).order_by("-created_at").first()


def _current_round(proposals):
    """The proposals since the last finished reschedule (oldest first)."""
    start = 0
    for i, p in enumerate(proposals):
        if p.status in ENDED:
            start = i + 1
    return proposals[start:]


def current_round(appointment):
    return _current_round(list(appointment.reschedule_proposals.all()))


def started_by(appointment):
    """Who started the reschedule under way: By.RND, By.CLIENT or None."""
    rows = current_round(appointment)
    return rows[0].proposed_by if rows else None


def first_booked_at(appointment):
    """The time this consultation was first booked for, before any move."""
    first = appointment.reschedule_proposals.order_by("created_at", "id").first()
    return first.from_at if first else appointment.scheduled_at


def latest_allowed(appointment):
    return first_booked_at(appointment) + timedelta(days=OFFER_WITHIN_DAYS)


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

    now = now or timezone.now()
    limit = latest_allowed(appointment)
    days = max(1, (limit - now).days + 2)  # the lookahead counts from today
    slots = next_open_slots(appointment.relationship.rnd_id, count=1000, now=now, lead_minutes=MIN_LEAD_MINUTES,
                            days=days, minutes=appointment.duration_minutes or 60)
    return [s for s in slots if appointment.scheduled_at < datetime.fromisoformat(s) <= limit]


def check_new_time(appointment, start, now=None):
    """Same rules as booking, at least MIN_LEAD_MINUTES ahead, after the
    current time and at most OFFER_WITHIN_DAYS after the time first booked;
    this consultation's own times don't count."""
    from profiles.services import overlaps_time_off

    from .serializers import fits_rnd_availability, overlapping_appointments

    now = now or timezone.now()
    end = _end(appointment, start)
    rel = appointment.relationship
    if start < now + timedelta(minutes=MIN_LEAD_MINUTES):
        raise ValidationError({"scheduled_at": [f"Pick a time at least {MIN_LEAD_MINUTES // 60} hours from now, so there's time to answer."]})
    if start > latest_allowed(appointment):
        raise ValidationError({"scheduled_at": [f"Pick a time by {_when(latest_allowed(appointment))}, "
                                                f"{OFFER_WITHIN_DAYS} days after it was first booked."]})
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
    this_round = _current_round(proposals)
    row = lambda p: {  # noqa: E731
        "id": p.id, "proposed_by": p.proposed_by, "from_at": p.from_at, "scheduled_at": p.scheduled_at,
        "note": p.note, "status": p.status, "status_label": p.get_status_display(),
        "expires_at": p.expires_at, "answered_at": p.answered_at, "created_at": p.created_at,
    }
    return {
        "waiting": row(waiting) if waiting else None,
        # whose answer it waits for
        "turn": (By.CLIENT if waiting.proposed_by == By.RND else By.RND) if waiting else None,
        "proposals_left": max(0, MAX_PROPOSALS - len(this_round)),
        # who started this reschedule: the RND's ends in a refund, the client's keeps the original
        "started_by": this_round[0].proposed_by if this_round else None,
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


def _create(appointment, by, start, note, now, keeps_original=False):
    expires = min(now + timedelta(hours=ANSWER_HOURS), start - timedelta(minutes=ANSWER_BEFORE_MINUTES))
    if keeps_original:  # the client's request: settled an hour before the booked time, so that can still happen
        expires = min(expires, appointment.scheduled_at - timedelta(minutes=ANSWER_BEFORE_MINUTES))
    return RescheduleProposal.objects.create(appointment=appointment, proposed_by=by, from_at=appointment.scheduled_at,
                                             scheduled_at=start, note=note, expires_at=expires)


def offer(appointment, user, start, reason, category=None, now=None):
    """The RND can't make a confirmed consultation, paid or not (2026-11-23), and offers a new time."""
    from billing.services import is_appointment_paid

    from .serializers import CLIENT_CANCEL_CUTOFF_MINUTES

    now = now or timezone.now()
    reason = (reason or "").strip()[:500]
    with transaction.atomic():
        appt = _lock(appointment)
        if appt.status != Appointment.Status.CONFIRMED:
            raise ValidationError({"detail": "Only a confirmed consultation can be moved to a new time. Decline a request instead."})
        paid = is_appointment_paid(appt)
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
                   f"{_when(start)} instead. Reason: {proposal.note} Accept it, pick another time or "
                   f"{'get a full refund' if paid else 'cancel it'} in My Appointments by {_when(proposal.expires_at)}.")
    email_new_time_offered(appt, proposal)
    from communication.reminders import _when as short_when

    text_client(client, f"RND {rnd.full_name} can't make your consultation on {short_when(proposal.from_at)} and offered a new time. "
                        f"Open the app to accept, pick another time or {'get a refund' if paid else 'cancel it'}.")
    return appt


def request_new_time(appointment, user, start, note="", now=None):
    """The client asks to move a confirmed consultation, paid or not
    (2026-11-23). Only the RND confirms it; declined, withdrawn or unanswered,
    the booking stays where it is."""
    now = now or timezone.now()
    note = (note or "").strip()[:500]
    with transaction.atomic():
        appt = _lock(appointment)
        if appt.status == Appointment.Status.RESCHEDULING:
            raise ValidationError({"detail": "A new time is already waiting for an answer on this consultation."})
        if appt.status != Appointment.Status.CONFIRMED:
            raise ValidationError({"detail": "Only a confirmed consultation can be moved."})
        if appt.scheduled_at - timedelta(minutes=REQUEST_CUTOFF_MINUTES) <= now:
            raise ValidationError({"detail": f"You can ask for a new time until {REQUEST_CUTOFF_MINUTES // 60} hours before the consultation."})
        check_new_time(appt, start, now)
        proposal = _create(appt, By.CLIENT, start, note, now, keeps_original=True)
        appt.status = Appointment.Status.RESCHEDULING
        appt.save(update_fields=["status", "updated_at"])
        _audit(user, "appointment.reschedule_requested", appt, scheduled_at=start, from_at=proposal.from_at)

    from communication.services import notify

    rel = appt.relationship
    notify(recipient=rel.rnd, notifiable_type="appointment", notifiable_id=appt.id, subject="New time requested",
           content=f"{rel.client.full_name} asked to move the consultation on {_when(proposal.from_at)} to {_when(start)}."
                   + (f" Note: {note}" if note else "")
                   + f" Accept it, suggest another time or decline by {_when(proposal.expires_at)}."
                   f" If you don't answer, it stays on {_when(proposal.from_at)}.")
    return appt


def change_pending(appointment, user, start, now=None):
    """A booking still waiting for the RND: the client changes the requested
    time directly (2026-11-23). The RND confirms it as usual."""
    now = now or timezone.now()
    with transaction.atomic():
        appt = _lock(appointment)
        if appt.status != Appointment.Status.PENDING:
            raise ValidationError({"detail": "Only a booking still waiting for the RND can change its time this way."})
        if appt.scheduled_at - timedelta(minutes=REQUEST_CUTOFF_MINUTES) <= now:
            raise ValidationError({"detail": f"You can change the time until {REQUEST_CUTOFF_MINUTES // 60} hours before it."})
        check_new_time(appt, start, now)
        old = appt.scheduled_at
        appt.scheduled_at = start
        appt.save(update_fields=["scheduled_at", "updated_at"])
        _audit(user, "appointment.request_moved", appt, scheduled_at=start, from_at=old)

    from communication.services import notify

    rel = appt.relationship
    notify(recipient=rel.rnd, notifiable_type="appointment", notifiable_id=appt.id, subject="Booking request moved",
           content=f"{rel.client.full_name} changed their booking request from {_when(old)} to {_when(start)}. Confirm it in Appointments.")
    return appt


def respond(appointment, user, by, action, start=None, note="", now=None):
    """accept | propose (another time) | refund (the RND's reschedule) |
    decline (RND) / keep (client): the client's request. `by` is who answers."""
    now = now or timezone.now()
    note = (note or "").strip()[:500]
    expire_due(now=now, pk=appointment.pk)  # an answer after the deadline is too late
    with transaction.atomic():
        appt = _lock(appointment)
        proposal = waiting_proposal(appt)
        if appt.status != Appointment.Status.RESCHEDULING or proposal is None:
            raise ValidationError({"detail": "There's no new time waiting for an answer on this consultation."})
        this_round = current_round(appt)
        clients_request = this_round[0].proposed_by == By.CLIENT
        if action == "refund":
            if by != By.CLIENT:
                raise PermissionDenied("Use Cancel with full refund.")
            if clients_request:
                raise ValidationError({"detail": "This is your own request. Keep your current time instead, or cancel the consultation."})
            return _end_with_refund(appt, proposal, user, P.REFUNDED, chosen_by=By.CLIENT, now=now)
        if action in ("keep", "decline"):
            # the client's request only: the RND declines it, or the client withdraws it
            if not clients_request:
                raise ValidationError({"detail": "The RND can't make the current time, so it can't be kept."
                                       if by == By.CLIENT else "Use Cancel with full refund."})
            if by == By.RND and proposal.proposed_by == By.RND:
                raise ValidationError({"detail": "This time is waiting for the client's answer."})
            return _keep_original(appt, proposal, user, P.DECLINED if by == By.RND else P.WITHDRAWN, by, now)
        if proposal.proposed_by == by:
            raise ValidationError({"detail": "This time is waiting for the other person's answer."})
        if action == "accept":
            return _accept(appt, proposal, user, by, now)
        if action != "propose":
            raise ValidationError({"action": "Choose accept, propose, decline or keep."})
        if len(this_round) >= MAX_PROPOSALS:
            raise ValidationError({"detail": f"Three times have been proposed already. Accept this one"
                                             f"{' or get a full refund' if by == By.CLIENT else ' or cancel with a full refund'}."})
        if start is None:
            raise ValidationError({"scheduled_at": ["Pick a time."]})
        proposal.status, proposal.answered_at = P.COUNTERED, now
        proposal.save(update_fields=["status", "answered_at"])  # its slot is no longer held
        check_new_time(appt, start, now)
        new = _create(appt, by, start, note, now, keeps_original=clients_request)
        _audit(user, "appointment.reschedule_proposed", appt, scheduled_at=start, by=by)

    from communication.services import notify

    rel = appt.relationship
    other = rel.client if by == By.RND else rel.rnd
    name = f"RND {rel.rnd.full_name}" if by == By.RND else rel.client.full_name
    notify(recipient=other, notifiable_type="appointment", notifiable_id=appt.id, subject="Another time proposed",
           content=f"{name} proposed {_when(start)} for the consultation instead of {_when(proposal.scheduled_at)}."
                   + (f" Note: {note}" if note else "")
                   + f" Answer by {_when(new.expires_at)}, or "
           + (f"it stays on {_when(appt.scheduled_at)}." if clients_request else "it's cancelled with a full refund."))
    return appt


def _accept(appt, proposal, user, by, now):
    from billing.services import is_appointment_paid
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
                   + (". It's already paid." if other == rel.client and is_appointment_paid(appt) else "."))
    return appt


def _keep_original(appt, proposal, user, outcome, by, now):
    """The client's request ends without a move: the RND declined it, the
    client withdrew it, or nobody answered. The booking stays as it was."""
    from communication.services import notify

    proposal.status, proposal.answered_at = outcome, now
    proposal.save(update_fields=["status", "answered_at"])
    appt.status = Appointment.Status.CONFIRMED
    appt.save(update_fields=["status", "updated_at"])
    _audit(user, "appointment.reschedule_kept", appt, outcome=outcome, by=by)

    rel = appt.relationship
    when = _when(appt.scheduled_at)
    if by == By.RND:
        notify(recipient=rel.client, notifiable_type="appointment", notifiable_id=appt.id, subject="New time declined",
               content=f"RND {rel.rnd.full_name} can't do {_when(proposal.scheduled_at)}. Your consultation stays on {when}.")
    elif by == By.CLIENT:
        notify(recipient=rel.rnd, notifiable_type="appointment", notifiable_id=appt.id, subject="Original time kept",
               content=f"{rel.client.full_name} kept the original time. The consultation stays on {when}.")
    else:
        for who in (rel.client, rel.rnd):
            notify(recipient=who, notifiable_type="appointment", notifiable_id=appt.id, subject="Reschedule expired",
                   content=f"The new time wasn't answered in time, so the consultation stays on {when}.")
    return appt


def _end_with_refund(appt, proposal, user, outcome, chosen_by, now, reason=""):
    """Cancelled with a full refund: the client chose it, the RND cancelled,
    or nobody answered in time. It still counts as the RND's cancel."""
    from billing.services import is_appointment_paid, settle_cancelled_appointment
    from communication.services import notify

    from .services import close_reopened_care_if_idle

    paid = is_appointment_paid(appt)  # read before the invoice is settled

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
               content=f"{rel.client.full_name} chose {'a full refund' if paid else 'to cancel'} instead of a new time for the consultation on {when}.")
    elif chosen_by == By.RND:
        notify(recipient=rel.client, notifiable_type="appointment", notifiable_id=appt.id, subject="Consultation cancelled",
               content=f"RND {rel.rnd.full_name} cancelled the consultation on {when} instead of moving it. "
                       f"Reason: {appt.cancellation_reason}" + (" You get a full refund." if paid else ""))
    else:
        for who, text in ((rel.client, "Nobody answered the proposed time in time, so the consultation is cancelled"
                                       + (" and you get a full refund." if paid else ".")),
                          (rel.rnd, f"The proposed time for {rel.client.full_name}'s consultation wasn't answered in time, so it's cancelled"
                                    + (" with a full refund." if paid else "."))):
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
    """Waiting proposals past their answer time: the RND's reschedule ends
    with a full refund, the client's request keeps the original time. Runs
    with expire_unpaid_appointments (wherever appointments are listed).
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
            if started_by(appt) == By.CLIENT:
                _keep_original(appt, proposal, None, P.EXPIRED, None, now)
            else:
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
    """POST {action: offer | accept | propose | decline (the client's request), scheduled_at, reason, category}.
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
    """POST {action: request (ask for a new time) | change (a booking still
    waiting for the RND) | accept | propose | refund | keep, scheduled_at, note}."""

    permission_classes = [IsClient]

    def post(self, request, pk):
        appt = get_object_or_404(Appointment.objects.filter(relationship__client=request.user), pk=pk)
        action = request.data.get("action")
        if action in ("request", "change"):
            start = _start(request)
            if start is None:
                raise ValidationError({"scheduled_at": ["Pick a new time."]})
            if action == "request":
                request_new_time(appt, request.user, start, request.data.get("note"))
            else:
                change_pending(appt, request.user, start)
        else:
            respond(appt, request.user, By.CLIENT, action, _start(request), request.data.get("note"))
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
