from decimal import Decimal

from datetime import date

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from accounts.permissions import IsClient, IsRnd

from .models import NcpRecord, PreConsultationScreening, ProgressRecord
from .serializers import NcpRecordSerializer, PreConsultationScreeningSerializer, ProgressRecordSerializer
from .services import (
    calculate_bmi,
    calculate_bmr_mifflin_st_jeor,
    calculate_nrs2002,
    calculate_tdee,
    classify_bmi_asia_pacific,
)


def _age_from_dob(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class ScreeningCreateView(generics.CreateAPIView):
    serializer_class = PreConsultationScreeningSerializer
    permission_classes = [IsClient]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        weight_kg = serializer.validated_data["weight_kg"]
        height_cm = serializer.validated_data["height_cm"]
        bmi = calculate_bmi(weight_kg, height_cm)
        bmi_category = classify_bmi_asia_pacific(bmi)

        bmr_kcal = tdee_kcal = None
        client_profile = getattr(request.user, "client_profile", None)
        if client_profile and client_profile.date_of_birth and client_profile.sex:
            age = _age_from_dob(client_profile.date_of_birth)
            bmr_kcal = calculate_bmr_mifflin_st_jeor(weight_kg, height_cm, age, client_profile.sex)
            activity_level = serializer.validated_data.get("activity_level", "sedentary")
            tdee_kcal = calculate_tdee(bmr_kcal, activity_level)

        # Weight-loss % is derived from the client's own screening history,
        # never self-reported — the most recent prior screening's weight is
        # the baseline. A first-ever screening has no prior data (contributes 0).
        weight_loss_pct = None
        previous = PreConsultationScreening.objects.filter(
            client=request.user
        ).order_by("-created_at").first()
        if previous and previous.weight_kg and previous.weight_kg > weight_kg:
            weight_loss_pct = ((previous.weight_kg - weight_kg) / previous.weight_kg * Decimal("100")).quantize(Decimal("0.01"))

        nrs_score, nrs_risk = calculate_nrs2002(
            bmi=bmi,
            weight_loss_pct=weight_loss_pct,
            reduced_intake=serializer.validated_data.pop("reduced_intake", False),
            severity_of_disease_points=1 if serializer.validated_data.pop("has_chronic_illness", False) else 0,
        )

        screening = serializer.save(
            client=request.user, bmi=bmi, bmi_category=bmi_category,
            bmr_kcal=bmr_kcal, tdee_kcal=tdee_kcal,
            nrs_score=nrs_score, nrs_risk=nrs_risk,
        )
        return Response(
            PreConsultationScreeningSerializer(screening).data, status=status.HTTP_201_CREATED
        )


class LatestScreeningView(generics.RetrieveAPIView):
    """The client's own most recent screening, for dashboard display."""

    serializer_class = PreConsultationScreeningSerializer
    permission_classes = [IsClient]

    def get_object(self):
        obj = PreConsultationScreening.objects.filter(
            client=self.request.user
        ).order_by("-created_at").first()
        if obj is None:
            raise NotFound("No screening on file yet.")
        return obj


class ScreeningDetailView(generics.RetrieveAPIView):
    serializer_class = PreConsultationScreeningSerializer

    def get_queryset(self):
        return PreConsultationScreening.objects.filter(appointment_id=self.kwargs["appointment_id"])

    def get_object(self):
        obj = self.get_queryset().first()
        if obj is None:
            raise NotFound("No screening found for this appointment.")
        user = self.request.user
        if obj.client_id != user.id and obj.appointment.relationship.rnd_id != user.id:
            raise PermissionDenied("Not your screening record.")
        return obj


class NcpRecordListCreateView(generics.ListCreateAPIView):
    serializer_class = NcpRecordSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return NcpRecord.objects.filter(
            relationship_id=self.kwargs["relationship_id"], relationship__rnd=self.request.user
        ).order_by("-encounter_date")

    def perform_create(self, serializer):
        serializer.save()


class RndProgressRecordListCreateView(generics.ListCreateAPIView):
    """RND logs progress for a specific client relationship."""

    serializer_class = ProgressRecordSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return ProgressRecord.objects.filter(
            relationship_id=self.kwargs["relationship_id"], relationship__rnd=self.request.user
        ).order_by("-record_date")

    def perform_create(self, serializer):
        serializer.save()


class ClientProgressRecordListView(generics.ListAPIView):
    """Client's own progress history, across all relationships."""

    serializer_class = ProgressRecordSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return ProgressRecord.objects.filter(
            relationship__client=self.request.user
        ).order_by("-record_date")


class NcpRecordDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = NcpRecordSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return NcpRecord.objects.filter(relationship__rnd=self.request.user)


class NcpRecordFinalizeView(generics.UpdateAPIView):
    serializer_class = NcpRecordSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return NcpRecord.objects.filter(relationship__rnd=self.request.user)

    def patch(self, request, *args, **kwargs):
        record = self.get_object()
        record.status = NcpRecord.Status.COMPLETED
        record.save(update_fields=["status", "updated_at"])
        return Response(NcpRecordSerializer(record).data)
