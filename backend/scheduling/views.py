from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.permissions import IsClient, IsRnd

from .models import Appointment, ConsultationSession, RndClientRelationship
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    ReviewSerializer,
    RndClientRelationshipSerializer,
)
from .services import DailyCoVideoService, VideoSessionError


class RequestRelationshipView(APIView):
    """Client requests to start a relationship with an RND. Starts as
    'pending' until the RND accepts via RndRelationshipAcceptView."""

    permission_classes = [IsClient]

    def post(self, request, rnd_id):
        try:
            rnd = User.objects.get(id=rnd_id, role=User.Role.RND)
        except User.DoesNotExist:
            raise NotFound("RND not found.")

        relationship, created = RndClientRelationship.objects.get_or_create(
            rnd=rnd, client=request.user,
            defaults={"status": RndClientRelationship.Status.PENDING},
        )
        if not created and relationship.status == RndClientRelationship.Status.DISCHARGED:
            relationship.status = RndClientRelationship.Status.PENDING
            relationship.save(update_fields=["status"])

        return Response(
            RndClientRelationshipSerializer(relationship).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RndRelationshipRequestsView(generics.ListAPIView):
    """RND's incoming pending relationship requests."""

    serializer_class = RndClientRelationshipSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return RndClientRelationship.objects.filter(
            rnd=self.request.user, status=RndClientRelationship.Status.PENDING
        ).select_related("rnd", "client")


class RndRelationshipAcceptView(APIView):
    permission_classes = [IsRnd]

    def patch(self, request, pk):
        relationship = get_object_or_404(
            RndClientRelationship.objects.filter(
                rnd=request.user, status=RndClientRelationship.Status.PENDING
            ),
            pk=pk,
        )
        relationship.status = RndClientRelationship.Status.ACTIVE
        relationship.started_at = timezone.now()
        relationship.save(update_fields=["status", "started_at", "updated_at"])
        return Response(RndClientRelationshipSerializer(relationship).data)


class ClientActiveRelationshipsView(generics.ListAPIView):
    """RNDs the client can book appointments with (active relationship only)."""

    serializer_class = RndClientRelationshipSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return RndClientRelationship.objects.filter(
            client=self.request.user, status=RndClientRelationship.Status.ACTIVE
        ).select_related("rnd", "client")


class ClientAppointmentListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsClient]

    def get_queryset(self):
        return Appointment.objects.filter(
            relationship__client=self.request.user
        ).select_related("relationship").order_by("-scheduled_at")

    def get_serializer_class(self):
        return AppointmentCreateSerializer if self.request.method == "POST" else AppointmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
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
            Appointment.objects.filter(relationship__client=request.user), pk=pk
        )
        appointment.status = Appointment.Status.CANCELLED
        appointment.cancellation_reason = request.data.get("reason", "")
        appointment.save(update_fields=["status", "cancellation_reason", "updated_at"])
        return Response(AppointmentSerializer(appointment).data)


class RndAppointmentListView(generics.ListAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
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
            appointment.cancellation_reason = request.data.get("reason", "")
        appointment.save()
        return Response(AppointmentSerializer(appointment).data)


class RndAppointmentConfirmView(_RndAppointmentTransitionView):
    """Confirming a video appointment also provisions the Daily.co room.
    Confirmation still succeeds even if room creation fails — the RND can
    retry video setup separately; a gateway hiccup shouldn't block the
    appointment from being confirmed."""

    from_statuses = [Appointment.Status.PENDING]
    to_status = Appointment.Status.CONFIRMED

    def patch(self, request, pk):
        response = super().patch(request, pk)
        appointment = get_object_or_404(Appointment, pk=response.data["id"])

        if appointment.type == Appointment.Type.VIDEO:
            try:
                room = DailyCoVideoService().create_room(appointment)
            except VideoSessionError:
                pass
            else:
                ConsultationSession.objects.create(
                    appointment=appointment,
                    video_provider=ConsultationSession.VideoProvider.DAILY_CO,
                    external_session_id=room["external_session_id"],
                    host_url=room["host_url"],
                    participant_url=room["participant_url"],
                )
                appointment.video_session_url = room["participant_url"]
                appointment.meeting_id = room["external_session_id"]
                appointment.save(update_fields=["video_session_url", "meeting_id", "updated_at"])

        return Response(AppointmentSerializer(appointment).data)


class RndAppointmentCompleteView(_RndAppointmentTransitionView):
    from_statuses = [Appointment.Status.CONFIRMED]
    to_status = Appointment.Status.COMPLETED


class RndAppointmentCancelView(_RndAppointmentTransitionView):
    from_statuses = [Appointment.Status.PENDING, Appointment.Status.CONFIRMED]
    to_status = Appointment.Status.CANCELLED


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsClient]
