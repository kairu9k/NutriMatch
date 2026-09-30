from decimal import Decimal

from datetime import date

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from accounts.permissions import IsClient, IsRnd

from .models import NcpRecord, PreConsultationScreening, ProgressRecord
from .serializers import (
    NcpDraftListSerializer,
    NcpRecordSerializer,
    PreConsultationScreeningSerializer,
    ProgressRecordSerializer,
)
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


class ScreeningCreateView(generics.ListCreateAPIView):
    serializer_class = PreConsultationScreeningSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return PreConsultationScreening.objects.filter(client=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        weight_kg = serializer.validated_data["weight_kg"]
        height_cm = serializer.validated_data["height_cm"]
        bmi = calculate_bmi(weight_kg, height_cm)
        bmi_category = classify_bmi_asia_pacific(bmi)

        # Age/sex come from the form when given (it pre-fills them from the
        # profile), otherwise from the profile itself.
        client_profile = getattr(request.user, "client_profile", None)
        age = serializer.validated_data.pop("age", None)
        sex = serializer.validated_data.pop("sex", None)
        if age is None and client_profile and client_profile.date_of_birth:
            age = _age_from_dob(client_profile.date_of_birth)
        if sex is None and client_profile:
            sex = client_profile.sex
        elif sex and client_profile and not client_profile.sex:
            client_profile.sex = sex
            client_profile.save(update_fields=["sex", "updated_at"])

        bmr_kcal = tdee_kcal = None
        if age and sex:
            bmr_kcal = calculate_bmr_mifflin_st_jeor(weight_kg, height_cm, age, sex)
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


class RndNcpDraftListView(generics.ListAPIView):
    """RND's NCP records across all patients — cross-patient, unlike
    NcpRecordListCreateView which is scoped to one relationship. Defaults to
    drafts only (the dashboard's 'resume a draft' panel); pass ?status=all
    to also include finalized records (the NCP Records page's cross-patient
    history table, reached when no specific patient is in context)."""

    serializer_class = NcpDraftListSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        qs = NcpRecord.objects.filter(
            relationship__rnd=self.request.user
        ).select_related("relationship__client")
        if self.request.query_params.get("status") != "all":
            qs = qs.filter(status=NcpRecord.Status.DRAFT)
        return qs.order_by("-updated_at")


class RndProgressRecordListCreateView(generics.ListCreateAPIView):
    """RND logs progress for a specific client relationship."""

    serializer_class = ProgressRecordSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return ProgressRecord.objects.filter(
            relationship_id=self.kwargs["relationship_id"], relationship__rnd=self.request.user
        ).order_by("-record_date")

    def perform_create(self, serializer):
        record = serializer.save()
        weight_kg = record.weight_kg
        if weight_kg is not None:
            # Height isn't stored as a standalone client field — sourced from
            # their most recent screening, same lookup ScreeningCreateView
            # uses for the weight-loss-% baseline.
            latest_screening = PreConsultationScreening.objects.filter(
                client=record.relationship.client_id
            ).order_by("-created_at").first()
            if latest_screening and latest_screening.height_cm:
                record.bmi = calculate_bmi(weight_kg, latest_screening.height_cm)
                record.save(update_fields=["bmi"])


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

    def perform_update(self, serializer):
        # A finalized record is permanent — the UI locks it, but the API
        # must refuse edits too.
        if serializer.instance.status == NcpRecord.Status.COMPLETED:
            raise PermissionDenied("This NCP record is finalized and can no longer be edited.")
        serializer.save()


class NcpRecordFinalizeView(generics.UpdateAPIView):
    serializer_class = NcpRecordSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return NcpRecord.objects.filter(relationship__rnd=self.request.user)

    def patch(self, request, *args, **kwargs):
        record = self.get_object()
        # Same checklist the Finalize panel shows in NCPRecords.vue.
        missing = []
        if not (record.weight_kg and record.height_cm):
            missing.append("weight and height (Assessment)")
        if not record.pes_problem:
            missing.append("PES problem (Diagnosis)")
        if not record.diet_prescription:
            missing.append("diet prescription (Intervention)")
        if missing:
            return Response(
                {"detail": "Can't finalize yet — missing " + ", ".join(missing) + "."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        record.status = NcpRecord.Status.COMPLETED
        record.save(update_fields=["status", "updated_at"])
        return Response(NcpRecordSerializer(record).data)
