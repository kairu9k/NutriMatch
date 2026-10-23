from datetime import timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from clinical.models import PreConsultationScreening

from .models import Appointment, ConsultationSession, Review, RndClientRelationship
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    ClientReviewListSerializer,
    ReviewSerializer,
    RndClientRelationshipSerializer,
)
from .services import JitsiVideoService, VideoSessionError


PH_TZ = ZoneInfo("Asia/Manila")


def format_ph_datetime(value):
    """Appointment times are stored in UTC; messages to users show Philippine
    time (e.g. "September 28, 2026 at 9:00 AM")."""
    local = value.astimezone(PH_TZ)
    return f"{local:%B} {local.day}, {local.year} at {local.hour % 12 or 12}:{local:%M} {local:%p}"


class RndActiveRelationshipsView(generics.ListAPIView):
    """RND's own active clients — for patient pickers (meal plans, NCP, etc.)."""

    serializer_class = RndClientRelationshipSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        # ?include=ended also lists discharged patients and care waiting for
        # you to confirm a booking (Messages shows them read-only); pickers
        # keep the default, active only.
        qs = RndClientRelationship.objects.filter(rnd=self.request.user)
        if self.request.query_params.get("include") == "ended":
            return _with_ended(qs).select_related("rnd", "client")
        return qs.filter(status=RndClientRelationship.Status.ACTIVE).select_related("rnd", "client")


def _with_ended(qs):
    """Active + discharged care, plus pending care that has a booking waiting
    for the RND (a pending one whose booking was declined is left out)."""
    from django.db.models import Exists, OuterRef, Q

    waiting = Appointment.objects.filter(relationship=OuterRef("pk"), status=Appointment.Status.PENDING)
    return qs.annotate(has_waiting=Exists(waiting)).filter(
        Q(status__in=[RndClientRelationship.Status.ACTIVE, RndClientRelationship.Status.DISCHARGED])
        | Q(status=RndClientRelationship.Status.PENDING, has_waiting=True)
    )


class ClientActiveRelationshipsView(generics.ListAPIView):
    """RNDs the client can book appointments with (active relationship only)."""

    serializer_class = RndClientRelationshipSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        # ?include=ended also lists discharged care and care waiting for the
        # RND to confirm a booking (read-only chat history).
        from .discharge_requests import process_due_discharge_requests

        process_due_discharge_requests(client=self.request.user)
        qs = RndClientRelationship.objects.filter(client=self.request.user)
        if self.request.query_params.get("include") == "ended":
            return _with_ended(qs).select_related("rnd", "client")
        return qs.filter(status=RndClientRelationship.Status.ACTIVE).select_related("rnd", "client")


class ClientAppointmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsClient]

    def get_queryset(self):
        from billing.services import expire_unpaid_appointments

        expire_unpaid_appointments(relationship__client=self.request.user)
        return Appointment.objects.filter(
            relationship__client=self.request.user
        ).select_related("relationship").order_by("-scheduled_at")

    def get_serializer_class(self):
        return AppointmentCreateSerializer if self.request.method == "POST" else AppointmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()

        from communication.services import notify

        notify(
            recipient=appointment.relationship.rnd,
            notifiable_type="appointment",
            notifiable_id=appointment.id,
            subject="New booking request",
            content=(
                f"{request.user.full_name} requested a {appointment.get_type_display().lower()} consultation "
                f"for {format_ph_datetime(appointment.scheduled_at)}. Review it in Appointments."
            ),
        )
        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)


class ClientAppointmentDetailView(generics.RetrieveAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return Appointment.objects.filter(relationship__client=self.request.user)


class ClientAppointmentCancelView(APIView):
    permission_classes = [IsClient]

    def patch(self, request, pk):
        appointment = get_object_or_404(
            Appointment.objects.filter(relationship__client=request.user).select_related("relationship"), pk=pk
        )
        # Same rule as the RND's cancel: only an upcoming (pending/confirmed)
        # appointment can be cancelled — never a completed one (it already has
        # an invoice) or one that's already cancelled.
        if appointment.status not in (Appointment.Status.PENDING, Appointment.Status.CONFIRMED):
            return Response(
                {"detail": f"This appointment is already {appointment.get_status_display().lower()} and can't be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Once a confirmed consultation has started the client can't cancel it
        # (it's paid — cancelling would ask for a refund for a session that may
        # have happened). The RND or an admin can still cancel a no-show.
        if appointment.status == Appointment.Status.CONFIRMED and appointment.scheduled_at <= timezone.now():
            return Response(
                {"detail": "This consultation has already started, so it can't be cancelled. "
                           "If it didn't take place, message your RND or contact NutriMatch support."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reason = (request.data.get("reason") or "").strip()[:500]
        appointment.status = Appointment.Status.CANCELLED
        appointment.cancellation_reason = reason
        appointment.save(update_fields=["status", "cancellation_reason", "updated_at"])

        from billing.services import settle_cancelled_appointment

        from .services import close_reopened_care_if_idle

        settle_cancelled_appointment(appointment)
        close_reopened_care_if_idle(appointment.relationship)

        from communication.services import notify

        notify(
            recipient=appointment.relationship.rnd,
            notifiable_type="appointment",
            notifiable_id=appointment.id,
            subject="Appointment cancelled",
            content=(
                f"{appointment.relationship.client.full_name} cancelled their {appointment.get_type_display().lower()} "
                f"consultation for {format_ph_datetime(appointment.scheduled_at)}."
                + (f" Reason: {reason}" if reason else "")
            ),
        )
        return Response(AppointmentSerializer(appointment, context={"request": request}).data)


class RndAppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        from billing.services import expire_unpaid_appointments

        expire_unpaid_appointments(relationship__rnd=self.request.user)
        return Appointment.objects.filter(
            relationship__rnd=self.request.user
        ).select_related("relationship").order_by("-scheduled_at")


class RndAppointmentDetailView(generics.RetrieveAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return Appointment.objects.filter(relationship__rnd=self.request.user)


class _RndAppointmentTransitionView(APIView):
    permission_classes = [IsRnd]
    from_statuses = []
    to_status = None

    def patch(self, request, pk):
        appointment = get_object_or_404(
            Appointment.objects.filter(relationship__rnd=request.user), pk=pk
        )
        if self.from_statuses and appointment.status not in self.from_statuses:
            raise PermissionDenied(
                f"Cannot transition appointment from '{appointment.status}' to '{self.to_status}'."
            )
        appointment.status = self.to_status
        if self.to_status == Appointment.Status.CANCELLED:
            appointment.cancellation_reason = self.cancel_reason(request)
        appointment.save()
        return Response(AppointmentSerializer(appointment, context={"request": request}).data)

    def cancel_reason(self, request):
        return request.data.get("reason", "")


class RndAppointmentConfirmView(_RndAppointmentTransitionView):
    """Confirming a video appointment also provisions the Daily.co room.
    Confirmation still succeeds even if room creation fails — the RND can
    retry video setup separately; a gateway hiccup shouldn't block the
    appointment from being confirmed.

    Also enforces the proposal's screening-before-consultation requirement.
    PreConsultationScreening isn't tied to a specific appointment in the
    current frontend (no appointment picker on that form), so this checks
    "has the client ever submitted any screening" rather than "did they
    screen for this exact appointment" — looser than the original mockup's
    intent, but real and honest given what the data actually supports."""

    from_statuses = [Appointment.Status.PENDING]
    to_status = Appointment.Status.CONFIRMED

    def patch(self, request, pk):
        appointment = get_object_or_404(
            Appointment.objects.filter(relationship__rnd=request.user), pk=pk
        )
        if appointment.status == Appointment.Status.PENDING and appointment.scheduled_at <= timezone.now():
            raise PermissionDenied("This request's time has already passed, so it can't be confirmed.")
        has_screening = PreConsultationScreening.objects.filter(
            client_id=appointment.relationship.client_id
        ).exists()
        if not has_screening:
            raise PermissionDenied(
                "Cannot confirm — this client hasn't submitted a pre-consultation screening yet."
            )
        response = super().patch(request, pk)
        appointment = get_object_or_404(Appointment, pk=response.data["id"])

        # Clients book directly (no request/accept step), so confirming their
        # appointment is what starts the care relationship.
        relationship = appointment.relationship
        if relationship.status != RndClientRelationship.Status.ACTIVE:
            relationship.status = RndClientRelationship.Status.ACTIVE
            relationship.started_at = timezone.now()
            relationship.ended_at = None
            relationship.discharge_reason = None
            relationship.save(update_fields=["status", "started_at", "ended_at", "discharge_reason", "updated_at"])

        if appointment.type == Appointment.Type.VIDEO:
            try:
                room = JitsiVideoService().create_room(appointment)
            except VideoSessionError:
                pass
            else:
                ConsultationSession.objects.create(
                    appointment=appointment,
                    video_provider=ConsultationSession.VideoProvider.JITSI,
                    external_session_id=room["external_session_id"],
                    host_url=room["host_url"],
                    participant_url=room["participant_url"],
                )
                appointment.video_session_url = room["participant_url"]
                appointment.meeting_id = room["external_session_id"]
                appointment.save(update_fields=["video_session_url", "meeting_id", "updated_at"])

        from billing.services import create_appointment_invoice
        from communication.services import notify

        # Pay before the consultation: the invoice is issued on confirmation.
        invoice, _ = create_appointment_invoice(appointment)
        scheduled_str = format_ph_datetime(appointment.scheduled_at)
        notify(
            recipient=appointment.relationship.client,
            notifiable_type="invoice",
            notifiable_id=invoice.id,
            subject="Appointment confirmed, payment due",
            content=(
                f"RND {appointment.relationship.rnd.full_name} confirmed your "
                f"{appointment.get_type_display().lower()} consultation for {scheduled_str}. "
                f"Please pay ₱{invoice.amount:,.2f} (INV-{invoice.id:04d}) before then to start your consultation."
            ),
        )
        from communication.reminders import _when
        from communication.sms import text_client

        text_client(appointment.relationship.client,
                    f"RND {appointment.relationship.rnd.full_name} confirmed your consultation on {_when(appointment.scheduled_at)}. "
                    f"Please pay P{invoice.amount:,.2f} in the app before it starts.")

        return Response(AppointmentSerializer(appointment, context={"request": request}).data)


class RndAppointmentCompleteView(_RndAppointmentTransitionView):
    """Completing requires the consultation to be paid (the invoice is issued
    at confirmation). Appointments confirmed before pay-first existed have no
    invoice: those still get one issued now, as before (pay after)."""

    from_statuses = [Appointment.Status.CONFIRMED]
    to_status = Appointment.Status.COMPLETED

    def patch(self, request, pk):
        from billing.services import appointment_invoice, create_appointment_invoice
        from communication.services import notify

        appointment = get_object_or_404(
            Appointment.objects.filter(relationship__rnd=request.user), pk=pk
        )
        invoice = appointment_invoice(appointment)
        if invoice is not None and invoice.status != "paid":
            raise PermissionDenied("This consultation hasn't been paid yet, so it can't be completed.")

        response = super().patch(request, pk)
        Appointment.objects.filter(pk=appointment.pk).update(completed_at=timezone.now())  # starts the payout hold
        if invoice is None:  # legacy: confirmed before pay-first
            appointment.refresh_from_db()
            invoice, created = create_appointment_invoice(appointment)
            if created:
                notify(
                    recipient=appointment.relationship.client,
                    notifiable_type="invoice",
                    notifiable_id=invoice.id,
                    subject="Invoice ready",
                    content=f"INV-{invoice.id:04d} for ₱{invoice.amount:.2f} is ready for payment.",
                )
        notify(
            recipient=appointment.relationship.client,
            notifiable_type="appointment",
            notifiable_id=appointment.id,
            subject="Your consultation summary is ready",
            content=(
                f"{request.user.full_name} marked your consultation on {format_ph_datetime(appointment.scheduled_at)} "
                "as complete. Open My Appointments, then History, to see your summary."
            ),
        )
        return response


class RndAppointmentCancelView(_RndAppointmentTransitionView):
    """Declining a request or cancelling a confirmed consultation — the RND
    must say why (the client is told the reason)."""

    from_statuses = [Appointment.Status.PENDING, Appointment.Status.CONFIRMED]
    to_status = Appointment.Status.CANCELLED
    MIN_REASON = 10

    def cancel_reason(self, request):
        return str(request.data.get("reason") or "").strip()[:500]

    def patch(self, request, pk):
        from billing.services import settle_cancelled_appointment
        from communication.services import notify

        if len(self.cancel_reason(request)) < self.MIN_REASON:
            raise ValidationError({"reason": f"Tell the client why, in at least {self.MIN_REASON} characters."})
        response = super().patch(request, pk)
        appointment = Appointment.objects.select_related("relationship__client", "relationship__rnd").get(pk=pk)
        settle_cancelled_appointment(appointment)
        from .services import close_reopened_care_if_idle

        close_reopened_care_if_idle(appointment.relationship)
        reason = (appointment.cancellation_reason or "").strip()
        notify(
            recipient=appointment.relationship.client,
            notifiable_type="appointment",
            notifiable_id=appointment.id,
            subject="Appointment cancelled",
            content=(
                f"RND {appointment.relationship.rnd.full_name} cancelled your "
                f"{appointment.get_type_display().lower()} consultation for {format_ph_datetime(appointment.scheduled_at)}."
                + (f" Reason: {reason}" if reason else "")
            ),
        )
        # By SMS too, so nobody waits in the room or travels for nothing.
        # The reason stays in the app (it can mention health details).
        from communication.reminders import _when
        from communication.sms import text_client

        text_client(appointment.relationship.client,
                    f"RND {appointment.relationship.rnd.full_name} cancelled your consultation on {_when(appointment.scheduled_at)}. "
                    "Open the app for details.")
        return response

class ClientReviewListCreateView(generics.ListCreateAPIView):
    """Reviews the logged-in client has left (GET, newest first) and
    creating a new one (POST) — same path as before (client/reviews/),
    now also listable. Previously the client-facing Reviews page wrongly
    rendered the RND's "Patient Reviews" component, 403ing against the
    RND-only /rnd/reviews/ endpoint since no client-facing list existed."""

    permission_classes = [IsClient]

    def get_queryset(self):
        return Review.objects.filter(
            client=self.request.user
        ).select_related("rnd").order_by("-created_at")

    def get_serializer_class(self):
        return ReviewSerializer if self.request.method == "POST" else ClientReviewListSerializer


class RndReviewListView(generics.ListAPIView):
    """Reviews received by the logged-in RND, newest first."""

    serializer_class = ReviewSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return Review.objects.filter(
            rnd=self.request.user, is_public=True
        ).select_related("client").order_by("-created_at")


class RndBookedSlotsView(APIView):
    """Times an RND is already booked (pending/confirmed, upcoming) or has
    blocked off, so the client booking modal can grey them out. Only
    start/end/kind are returned, never who booked them or why."""

    permission_classes = [IsClient]

    def get(self, request, rnd_id):
        from .serializers import DEFAULT_SESSION_MINUTES

        upcoming = Appointment.objects.filter(
            relationship__rnd_id=rnd_id,
            status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED],
            scheduled_at__gte=timezone.now() - timedelta(hours=3),
        ).order_by("scheduled_at")
        from profiles.services import time_off_intervals

        now = timezone.now()
        taken = [
            {
                "start": a.scheduled_at,
                "end": a.scheduled_at + timedelta(minutes=a.duration_minutes or DEFAULT_SESSION_MINUTES),
                "kind": "booked",
            }
            for a in upcoming
        ]
        # Time the RND blocked off (never the reason): the modal shows it as
        # "Unavailable", and a fully blocked day as "Day off".
        taken += [{"start": lo, "end": hi, "kind": "time_off"}
                  for lo, hi in time_off_intervals(rnd_id, now, now + timedelta(days=60))]
        return Response(taken)
