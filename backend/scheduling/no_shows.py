"""When a consultation doesn't happen (2026-11-02, user's plan).

- The client didn't come: the RND marks a **no-show** (only after the start,
  only if the client never joined the video call). No refund: the RND is paid
  like a completed consultation. The client can **dispute** it for 3 days
  (DISPUTE_DAYS, the same as the payout hold), which opens a support request
  and holds the payout until an admin refunds it or rejects the dispute.
- The RND didn't come: 15 minutes after the start, a client who joined the
  call can report it if the RND isn't in the call and was in it for less
  than 5 minutes in total (a brief join doesn't count). It's cancelled and the payment
  goes to refund pending (the attendance record proves it), and it counts as
  one of the RND's late cancels.
- The call didn't work: the RND ends it as a failed call, the client gets a
  full refund and can book again.

Attendance comes from scheduling/attendance.py."""

from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin, IsClient, IsRnd

from .attendance import attendance_line, dispute_payload, minutes_in_call
from .models import Appointment
from .serializers import RND_ABSENT_AFTER_MINUTES, RND_MIN_PRESENT_MINUTES, AppointmentSerializer
from .views import format_ph_datetime

MIN_DISPUTE_REASON = 20
MIN_DECISION_NOTE = 10
LATE_CANCEL_DAYS = 30  # admin flag: an RND with LATE_CANCEL_FLAG late cancels in this many days
LATE_CANCEL_FLAG = 3


def _audit(user, action, appointment, values):
    from core.models import AuditLog

    AuditLog.objects.create(user=user, action=action, table_name="appointments", record_id=appointment.id, new_values=values)


def _note(request, limit=500):
    return str(request.data.get("note") or request.data.get("reason") or "").strip()[:limit]


def _respond(request, appointment):
    appointment.refresh_from_db()
    return Response(AppointmentSerializer(appointment, context={"request": request}).data)


# ---------------------------------------------------------------- RND side
class RndNoShowView(APIView):
    """POST /api/rnd/appointments/<id>/no-show/ {note?}: the client didn't
    come. Refused once the client joined the video call."""

    permission_classes = [IsRnd]

    def post(self, request, pk):
        from billing.services import appointment_invoice
        from communication.services import notify

        from .services import close_reopened_care_if_idle

        a = get_object_or_404(Appointment.objects.filter(relationship__rnd=request.user)
                              .select_related("relationship__client", "relationship__rnd"), pk=pk)
        now = timezone.now()
        if a.status != Appointment.Status.CONFIRMED:
            raise ValidationError({"detail": "Only a confirmed consultation can be marked as a no-show."})
        if now < a.scheduled_at:
            raise ValidationError({"detail": "You can mark a no-show once the consultation has started."})
        invoice = appointment_invoice(a)
        if invoice is not None and invoice.status != "paid":
            raise ValidationError({"detail": "This consultation isn't paid, so it's cancelled automatically instead."})
        if a.type == Appointment.Type.VIDEO and a.client_joined_at is not None:
            raise ValidationError({"detail": f"{a.relationship.client.first_name} joined the video call, so this isn't a no-show. "
                                             "Mark it complete instead, or end it as a call that didn't work."})
        note = _note(request)
        a.status = Appointment.Status.NO_SHOW
        a.completed_at = now  # starts the payout hold, which is also the dispute window
        a.cancellation_reason = note or "The client didn't attend."
        a.save(update_fields=["status", "completed_at", "cancellation_reason", "updated_at"])
        close_reopened_care_if_idle(a.relationship)
        _audit(request.user, "appointment.no_show", a, {"note": note, "attendance": attendance_line(a, now)})
        notify(recipient=a.relationship.client, notifiable_type="appointment", notifiable_id=a.id,
               subject="Marked as not attending",
               content=(f"RND {request.user.full_name} marked your consultation on {format_ph_datetime(a.scheduled_at)} "
                        "as not attended, so it isn't refunded. If this is wrong, you can dispute it from My Appointments, "
                        "History, within 3 days."))
        from .emails import email_no_show

        email_no_show(a)
        return _respond(request, a)


class RndCallFailedView(APIView):
    """POST /api/rnd/appointments/<id>/call-failed/ {note?}: the video call
    didn't work. Cancelled with a full refund; the client can book again."""

    permission_classes = [IsRnd]

    def post(self, request, pk):
        from billing.services import settle_cancelled_appointment
        from communication.services import notify

        from .services import close_reopened_care_if_idle
        from .video_call import join_window

        a = get_object_or_404(Appointment.objects.filter(relationship__rnd=request.user)
                              .select_related("relationship__client", "relationship__rnd"), pk=pk)
        if a.status != Appointment.Status.CONFIRMED or a.type != Appointment.Type.VIDEO:
            raise ValidationError({"detail": "Only a confirmed video consultation can be ended this way."})
        if timezone.now() < join_window(a)[0]:
            raise ValidationError({"detail": "The call hasn't opened yet."})
        note = _note(request)
        a.status = Appointment.Status.CANCELLED
        a.cancellation_reason = ("The video call didn't work." + (f" {note}" if note else ""))[:500]
        a.cancelled_by, a.cancelled_at = Appointment.CancelledBy.CALL_FAILED, timezone.now()
        a.save(update_fields=["status", "cancellation_reason", "cancelled_by", "cancelled_at", "updated_at"])
        invoice = settle_cancelled_appointment(a)
        close_reopened_care_if_idle(a.relationship)
        _audit(request.user, "appointment.call_failed", a, {"note": note, "attendance": attendance_line(a)})
        from .emails import email_cancelled_by_rnd

        email_cancelled_by_rnd(a, kind="call_failed",
                               paid_amount=invoice.amount if invoice is not None and invoice.status == "refund_pending" else None)
        notify(recipient=a.relationship.client, notifiable_type="appointment", notifiable_id=a.id,
               subject="The video call didn't work",
               content=(f"Your consultation on {format_ph_datetime(a.scheduled_at)} with RND {request.user.full_name} "
                        "was ended because the video call didn't work. If you paid, you get the full amount back. "
                        "You can book a new time any time."))
        return _respond(request, a)


# ---------------------------------------------------------------- client side
class ClientRndAbsentView(APIView):
    """POST /api/client/appointments/<id>/rnd-absent/: the client joined the
    call and the RND never did, 15 minutes after the start."""

    permission_classes = [IsClient]

    def post(self, request, pk):
        from billing.services import is_appointment_paid, settle_cancelled_appointment
        from communication.services import notify
        from accounts.models import User

        from .services import close_reopened_care_if_idle

        a = get_object_or_404(Appointment.objects.filter(relationship__client=request.user)
                              .select_related("relationship__client", "relationship__rnd"), pk=pk)
        now = timezone.now()
        if a.status != Appointment.Status.CONFIRMED or a.type != Appointment.Type.VIDEO or not is_appointment_paid(a):
            raise ValidationError({"detail": "Only a paid, confirmed video consultation can be reported."})
        if now < a.scheduled_at + timedelta(minutes=RND_ABSENT_AFTER_MINUTES):
            raise ValidationError({"detail": f"You can report it {RND_ABSENT_AFTER_MINUTES} minutes after the start."})
        if a.client_joined_at is None:
            raise ValidationError({"detail": "Join the video call first, so NutriMatch can see you were there."})
        # A brief join doesn't count (2026-11-02): the RND must have been in
        # the call at least 5 minutes in total, or be in it right now.
        if a.rnd_in_since is not None:
            raise ValidationError({"detail": "Your RND is in the call now."})
        if minutes_in_call(a, "rnd", now) >= RND_MIN_PRESENT_MINUTES:
            raise ValidationError({"detail": f"Your RND was in the call for {RND_MIN_PRESENT_MINUTES} minutes or more, so this can't be "
                                             "reported as a no-show. If something went wrong, contact NutriMatch support."})
        a.status = Appointment.Status.CANCELLED
        a.cancellation_reason = ("The RND didn't join the video call." if a.rnd_joined_at is None
                                 else "The RND was in the video call for less than 5 minutes.")
        a.cancelled_by, a.cancelled_at, a.cancelled_late = Appointment.CancelledBy.RND_ABSENT, now, True
        a.save(update_fields=["status", "cancellation_reason", "cancelled_by", "cancelled_at", "cancelled_late", "updated_at"])
        settle_cancelled_appointment(a)  # refund pending, the client is told
        close_reopened_care_if_idle(a.relationship)
        line = attendance_line(a, now)
        _audit(request.user, "appointment.rnd_absent", a, {"attendance": line})
        rnd = a.relationship.rnd
        notify(recipient=rnd, notifiable_type="appointment", notifiable_id=a.id, subject="You missed a consultation",
               content=(f"{request.user.full_name} waited in the video call for their consultation on "
                        f"{format_ph_datetime(a.scheduled_at)} and you didn't join, so it was cancelled and refunded. "
                        "If this is wrong, contact NutriMatch support."))
        from .emails import email_rnd_missed

        email_rnd_missed(a)
        for admin in User.objects.filter(role=User.Role.ADMIN, is_active=True):
            notify(recipient=admin, notifiable_type="appointment", notifiable_id=a.id, subject="RND didn't attend",
                   content=f"{request.user.full_name} reported that RND {rnd.full_name} didn't join. {line} The refund is waiting.")
        return _respond(request, a)


class ClientDisputeView(APIView):
    """POST /api/client/appointments/<id>/dispute/ {reason}: the client says
    the no-show is wrong. Opens a support request; the payout waits."""

    permission_classes = [IsClient]

    def post(self, request, pk):
        from billing.services import appointment_invoice
        from communication.models import SupportMessage, SupportTicket
        from communication.services import notify
        from communication.support import _notify_admins

        a = get_object_or_404(Appointment.objects.filter(relationship__client=request.user)
                              .select_related("relationship__client", "relationship__rnd"), pk=pk)
        info = dispute_payload(a)
        if info is None:
            raise ValidationError({"detail": "Only a consultation marked as a no-show can be disputed."})
        if a.dispute_opened_at:
            raise ValidationError({"detail": "You already disputed this. NutriMatch will reply to your support request."})
        if not info["can_open"]:
            raise ValidationError({"detail": "The 3 days to dispute this have passed."})
        reason = str(request.data.get("reason") or "").strip()
        if len(reason) < MIN_DISPUTE_REASON:
            raise ValidationError({"reason": f"Tell us what happened, in at least {MIN_DISPUTE_REASON} characters."})
        reason = reason[:2000]
        now = timezone.now()
        with transaction.atomic():
            a.dispute_opened_at, a.dispute_reason = now, reason
            a.save(update_fields=["dispute_opened_at", "dispute_reason", "updated_at"])
            ticket = SupportTicket.objects.create(
                user=request.user, category=SupportTicket.Category.DISPUTE,
                subject=f"No-show dispute, {format_ph_datetime(a.scheduled_at)}"[:150],
                appointment=a, invoice=appointment_invoice(a))
            SupportMessage.objects.create(ticket=ticket, sender=request.user,
                                          body=f"{reason}\n\nAttendance: {attendance_line(a, now)}")
            _notify_admins(ticket, "No-show dispute",
                           f"{request.user.full_name} disputes being marked as not attending with RND "
                           f"{a.relationship.rnd.full_name}: {reason[:300]}")
            _audit(request.user, "appointment.dispute_opened", a, {"reason": reason[:1000], "ticket": ticket.id})
        notify(recipient=a.relationship.rnd, notifiable_type="appointment", notifiable_id=a.id, subject="No-show disputed",
               content=(f"{request.user.full_name} disputes the no-show for {format_ph_datetime(a.scheduled_at)}. "
                        "The payment waits until NutriMatch decides. You'll be told the outcome."))
        return _respond(request, a)


# ---------------------------------------------------------------- admin side
class AdminDisputeDecisionView(APIView):
    """POST /api/admin/appointments/<id>/dispute/ {decision: refund|reject, note}.
    Refund: the payment goes to refund pending (sent from Billing &
    Commission as usual). Reject: the RND keeps it."""

    permission_classes = [IsAdmin]

    def post(self, request, pk):
        from billing.models import Invoice
        from billing.services import appointment_invoice
        from communication.models import SupportMessage, SupportTicket
        from communication.services import notify

        a = get_object_or_404(Appointment.objects.select_related("relationship__client", "relationship__rnd"), pk=pk)
        if not a.dispute_opened_at or a.dispute_resolved_at:
            raise ValidationError({"detail": "There's no open dispute on this consultation."})
        decision = request.data.get("decision")
        if decision not in ("refund", "reject"):
            raise ValidationError({"decision": "Choose refund or reject."})
        note = str(request.data.get("note") or "").strip()
        if len(note) < MIN_DECISION_NOTE:
            raise ValidationError({"note": f"Explain the decision in at least {MIN_DECISION_NOTE} characters (both people see it)."})
        note = note[:1000]
        client, rnd = a.relationship.client, a.relationship.rnd
        when = format_ph_datetime(a.scheduled_at)
        with transaction.atomic():
            invoice = appointment_invoice(a)
            if decision == "refund":
                if invoice is None or invoice.status != Invoice.Status.PAID or invoice.payout_id:
                    raise PermissionDenied("This payment can't be refunded from here (it isn't paid, or it was already paid out).")
                invoice.status = Invoice.Status.REFUND_PENDING
                invoice.save(update_fields=["status"])
            a.dispute_resolved_at = timezone.now()
            a.dispute_outcome = Appointment.DisputeOutcome.REFUNDED if decision == "refund" else Appointment.DisputeOutcome.REJECTED
            a.dispute_note = note
            a.save(update_fields=["dispute_resolved_at", "dispute_outcome", "dispute_note", "updated_at"])
            ticket = SupportTicket.objects.filter(appointment=a, category=SupportTicket.Category.DISPUTE).order_by("-id").first()
            if ticket:
                outcome = "We'll refund your payment" if decision == "refund" else "We didn't approve a refund"
                SupportMessage.objects.create(ticket=ticket, sender=request.user, is_admin=True, body=f"{outcome}. {note}")
                ticket.status, ticket.closed_at, ticket.user_unread = SupportTicket.Status.CLOSED, timezone.now(), True
                ticket.last_activity_at = timezone.now()
                ticket.save(update_fields=["status", "closed_at", "user_unread", "last_activity_at"])
            _audit(request.user, "appointment.dispute_decided", a, {"decision": decision, "note": note})
        if decision == "refund":
            notify(recipient=client, notifiable_type="appointment", notifiable_id=a.id, subject="Dispute approved",
                   content=f"Your dispute for the consultation on {when} was approved. Your payment will be refunded within 5–7 business days. {note}")
            notify(recipient=rnd, notifiable_type="appointment", notifiable_id=a.id, subject="No-show dispute decided",
                   content=f"NutriMatch approved {client.full_name}'s dispute for {when}, so the payment is refunded. {note}")
        else:
            notify(recipient=client, notifiable_type="appointment", notifiable_id=a.id, subject="Dispute not approved",
                   content=f"Your dispute for the consultation on {when} wasn't approved, so it isn't refunded. {note}")
            notify(recipient=rnd, notifiable_type="appointment", notifiable_id=a.id, subject="No-show dispute decided",
                   content=f"NutriMatch didn't approve {client.full_name}'s dispute for {when}. The payment stays yours. {note}")
        return Response({"ok": True, "outcome": a.dispute_outcome})


def late_cancel_flags(now=None):
    """RNDs with LATE_CANCEL_FLAG or more late cancels (incl. not attending)
    in the last LATE_CANCEL_DAYS days: [(rnd, count)]."""
    from django.db.models import Count

    from accounts.models import User

    since = (now or timezone.now()) - timedelta(days=LATE_CANCEL_DAYS)
    rows = (Appointment.objects.filter(cancelled_late=True, cancelled_at__gte=since)
            .values("relationship__rnd").annotate(n=Count("id")).filter(n__gte=LATE_CANCEL_FLAG))
    users = User.objects.in_bulk([r["relationship__rnd"] for r in rows])
    return [(users[r["relationship__rnd"]], r["n"]) for r in rows if r["relationship__rnd"] in users]
