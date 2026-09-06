from datetime import date

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from accounts.permissions import IsClient, IsRnd

from .models import NcpRecord, PreConsultationScreening
from .serializers import NcpRecordSerializer, PreConsultationScreeningSerializer
from .services import (
    calculate_bmi,
    calculate_bmr_mifflin_st_jeor,
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

        screening = serializer.save(
            client=request.user, bmi=bmi, bmi_category=bmi_category,
            bmr_kcal=bmr_kcal, tdee_kcal=tdee_kcal,
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
