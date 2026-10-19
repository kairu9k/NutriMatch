"""The client asks to end care (2026-10-19, user's call — one RND at a time,
so a client must never be stuck with an RND who doesn't discharge them).

Profile Settings -> Care Team -> Request discharge (reason from a list).
The RND is told and has DISCHARGE_REQUEST_DAYS to discharge them properly
(Client Detail -> Discharge, pre-filled); if they don't, care ends on its
own. The record stays (read-only), like any discharge. Deactivating an RND
ends their patients' care straight away (end_care_of_deactivated_rnd).

The due check runs lazily — whenever a client/RND loads their care, books,
or reminders run — so no scheduler is needed.
"""

from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient

from .models import Appointment, RndClientRelationship

DISCHARGE_REQUEST_DAYS = 3
NOTE_MAX = 500


def request_payload(rel):
    """What both sides see about a pending request, or None."""
    if not rel.discharge_requested_at or rel.status != RndClientRelationship.Status.ACTIVE:
        return None
    return {
        "requested_at": rel.discharge_requested_at,
        "ends_at": rel.discharge_requested_at + timedelta(days=DISCHARGE_REQUEST_DAYS),
        "reason": rel.discharge_request_reason,
        "reason_label": rel.get_discharge_request_reason_display() if rel.discharge_request_reason else None,
        "note": rel.discharge_request_note or "",
    }


def _ph_date(dt):
    from communication.reminders import ph_tz

    local = dt.astimezone(ph_tz())
    return f"{local:%b} {local.day}, {local.year}"


def process_due_discharge_requests(**scope):
    """End care whose discharge request is older than DISCHARGE_REQUEST_DAYS.
    `scope` narrows it (client=..., rnd=...). Returns how many ended."""
    from .discharge import discharge

    cutoff = timezone.now() - timedelta(days=DISCHARGE_REQUEST_DAYS)
    due = RndClientRelationship.objects.filter(
        status=RndClientRelationship.Status.ACTIVE, discharge_requested_at__lte=cutoff, **scope,
    ).select_related("client", "rnd")
    ended = 0
    for rel in due:
        with transaction.atomic():
            rel = RndClientRelationship.objects.select_for_update().get(pk=rel.pk)
            if rel.status != RndClientRelationship.Status.ACTIVE or not rel.discharge_requested_at:
                continue
            why = rel.get_discharge_request_reason_display() if rel.discharge_request_reason else "no reason given"
            reason = (f"Ended automatically: the client asked to end care on {_ph_date(rel.discharge_requested_at)} "
                      f"({why}) and it wasn't closed within {DISCHARGE_REQUEST_DAYS} days.")
            discharge(rel, None, reason, ended_by=RndClientRelationship.EndedBy.AUTO)
        ended += 1
    return ended


def end_care_of_deactivated_rnd(rnd, admin):
    """An RND was deactivated: their upcoming consultations are cancelled
    (paid ones become refund-pending) and every open care ends, so their
    clients can choose another RND. Each client is notified (and texted, if
    they turned SMS on). Returns (consultations cancelled, care ended)."""
    from billing.services import settle_cancelled_appointment
    from communication.reminders import _when
    from communication.services import notify
    from communication.sms import text_client

    from .discharge import discharge
    from .views import format_ph_datetime

    now = timezone.now()
    reason = "Your RND's NutriMatch account was deactivated, so you can choose a new RND."
    cancelled = 0
    for appt in Appointment.objects.filter(
        relationship__rnd=rnd, status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED], scheduled_at__gt=now,
    ).select_related("relationship__client"):
        appt.status = Appointment.Status.CANCELLED
        appt.cancellation_reason = "Cancelled by NutriMatch: the RND's account was deactivated."
        appt.save(update_fields=["status", "cancellation_reason", "updated_at"])
        settle_cancelled_appointment(appt)
        client = appt.relationship.client
        notify(recipient=client, notifiable_type="appointment", notifiable_id=appt.id, subject="Appointment cancelled",
               content=f"Your {appt.get_type_display().lower()} consultation with RND {rnd.full_name} for "
                       f"{format_ph_datetime(appt.scheduled_at)} was cancelled because the RND's account was deactivated. "
                       "You can book another RND on Find an RND.")
        text_client(client, f"NutriMatch cancelled your consultation with RND {rnd.full_name} on {_when(appt.scheduled_at)}. "
                            "Open the app for details.")
        cancelled += 1
    ended = 0
    for rel in RndClientRelationship.objects.filter(
        rnd=rnd, status__in=[RndClientRelationship.Status.ACTIVE, RndClientRelationship.Status.PENDING],
    ).select_related("client", "rnd"):
        if rel.status == RndClientRelationship.Status.ACTIVE:
            discharge(rel, admin, reason, ended_by=RndClientRelationship.EndedBy.ADMIN)
        else:  # never started (first booking not confirmed) — just close it
            rel.status = RndClientRelationship.Status.DISCHARGED
            rel.ended_at = now
            rel.ended_by = RndClientRelationship.EndedBy.ADMIN
            rel.discharge_reason = reason
            rel.save(update_fields=["status", "ended_at", "ended_by", "discharge_reason", "updated_at"])
        ended += 1
    return cancelled, ended


class DischargeRequestSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=RndClientRelationship.RequestReason.choices, error_messages={
        "required": "Pick a reason.", "invalid_choice": "Pick a reason from the list."})
    note = serializers.CharField(max_length=NOTE_MAX, required=False, allow_blank=True, trim_whitespace=True)

    def validate(self, attrs):
        if attrs["reason"] == RndClientRelationship.RequestReason.OTHER and not attrs.get("note"):
            raise serializers.ValidationError({"note": ["Tell us a little more."]})
        return attrs


class ClientDischargeRequestView(APIView):
    """POST {reason, note?} -> ask to end care; DELETE -> take the request back."""

    permission_classes = [IsClient]

    def _rel(self, request, pk):
        return get_object_or_404(RndClientRelationship.objects.select_related("rnd", "client"), pk=pk, client=request.user)

    def post(self, request, pk):
        from communication.services import notify
        from core.models import AuditLog

        rel = self._rel(request, pk)
        if rel.status != RndClientRelationship.Status.ACTIVE:
            return Response({"detail": "You can only end care that's active."}, status=status.HTTP_400_BAD_REQUEST)
        if rel.discharge_requested_at:
            return Response({"detail": "You've already asked to end this care."}, status=status.HTTP_400_BAD_REQUEST)
        if rel.appointments.filter(status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
                                   scheduled_at__gt=timezone.now()).exists():
            return Response({"detail": "Cancel your upcoming consultation first (My Appointments), then ask to end care."},
                            status=status.HTTP_400_BAD_REQUEST)
        data = DischargeRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        rel.discharge_requested_at = timezone.now()
        rel.discharge_request_reason = data.validated_data["reason"]
        rel.discharge_request_note = data.validated_data.get("note") or None
        rel.save(update_fields=["discharge_requested_at", "discharge_request_reason", "discharge_request_note", "updated_at"])
        info = request_payload(rel)
        AuditLog.objects.create(user=request.user, action="relationship.discharge_requested",
                                table_name="rnd_client_relationships", record_id=rel.id,
                                new_values={"reason": rel.discharge_request_reason})
        notify(recipient=rel.rnd, notifiable_type="relationship", notifiable_id=rel.id,
               subject="Discharge requested",
               content=(f"{request.user.full_name} asked to end their care ({info['reason_label']}). "
                        f"Discharge them by {_ph_date(info['ends_at'])} with a closing note — after that it ends automatically."))
        return Response({"discharge_request": info}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        from communication.services import notify

        rel = self._rel(request, pk)
        if not rel.discharge_requested_at or rel.status != RndClientRelationship.Status.ACTIVE:
            return Response({"detail": "There's no request to cancel."}, status=status.HTTP_400_BAD_REQUEST)
        rel.discharge_requested_at = None
        rel.discharge_request_reason = None
        rel.discharge_request_note = None
        rel.save(update_fields=["discharge_requested_at", "discharge_request_reason", "discharge_request_note", "updated_at"])
        notify(recipient=rel.rnd, notifiable_type="relationship", notifiable_id=rel.id,
               subject="Discharge request withdrawn",
               content=f"{request.user.full_name} decided to continue their care with you.")
        return Response({"discharge_request": None})
