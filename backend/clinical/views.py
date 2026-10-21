from decimal import Decimal

from datetime import date

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from scheduling.discharge import ensure_open
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd

from .models import NcpRecord, PreConsultationScreening, ProgressRecord
from .serializers import (
    NcpDraftListSerializer,
    NcpRecordSerializer,
    PreConsultationScreeningSerializer,
    ClientProgressRecordSerializer,
    ClientSelfLogSerializer,
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
    from core.ph_time import ph_today

    today = ph_today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


class ScreeningCreateView(generics.ListCreateAPIView):
    serializer_class = PreConsultationScreeningSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return PreConsultationScreening.objects.filter(client=self.request.user).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        # The screening is the baseline that weight/BMI change is measured
        # against, so it's taken once and then read-only (user's rule,
        # 2026-10-13); new readings go in the Progress Tracker.
        if PreConsultationScreening.objects.filter(client=request.user).exists():
            return Response(
                {"detail": "Your screening is already on file and can't be changed. "
                           "Log new readings in the Progress Tracker."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        weight_kg = serializer.validated_data["weight_kg"]
        height_cm = serializer.validated_data["height_cm"]
        bmi = calculate_bmi(weight_kg, height_cm)
        bmi_category = classify_bmi_asia_pacific(bmi)

        # Age and sex always come from the profile when it has them (given at
        # registration; the form shows them read-only and they're changed in
        # Profile Settings). A typed value is only the fallback — older
        # accounts without a DOB, or "Prefer not to say" at registration —
        # and a typed sex is then saved to the profile.
        client_profile = getattr(request.user, "client_profile", None)
        age = serializer.validated_data.pop("age", None)
        sex = serializer.validated_data.pop("sex", None)
        if client_profile and client_profile.date_of_birth:
            age = _age_from_dob(client_profile.date_of_birth)
        if client_profile and client_profile.sex:
            sex = client_profile.sex
        elif sex and client_profile:
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


class RndAppointmentScreeningView(generics.GenericAPIView):
    """What the RND reviews before accepting a booking (the Appointments
    page's "View Screening" popup): the client's latest pre-consultation
    screening plus their basic health profile.

    Screenings aren't tied to a specific appointment — a client screens
    once, before booking — so this returns the client's most recent one,
    the same rule RndAppointmentConfirmView uses for its screening gate.
    `screening` is null when the client hasn't submitted one yet."""

    permission_classes = [IsRnd]

    def get(self, request, appointment_id):
        from scheduling.models import Appointment

        appointment = Appointment.objects.select_related(
            "relationship__client__client_profile", "relationship__client__health_profile"
        ).filter(pk=appointment_id, relationship__rnd=request.user).first()
        if appointment is None:
            raise NotFound("Appointment not found.")

        client = appointment.relationship.client
        profile = getattr(client, "client_profile", None)
        health = getattr(client, "health_profile", None)
        screening = PreConsultationScreening.objects.filter(client=client).order_by("-created_at").first()

        return Response({
            "appointment": {
                "id": appointment.id,
                "status": appointment.status,
                "type": appointment.type,
                "scheduled_at": appointment.scheduled_at,
                "notes": appointment.notes,
            },
            "client": {
                "name": client.full_name,
                "age": _age_from_dob(profile.date_of_birth) if profile and profile.date_of_birth else None,
                "sex": profile.sex if profile else None,
                "medical_conditions": (health.medical_conditions if health else None) or [],
                "allergies": (health.allergies if health else None) or [],
                "dietary_restrictions": (health.dietary_restrictions if health else None) or [],
                "health_goals": (health.health_goals if health else None) or [],
            },
            "screening": PreConsultationScreeningSerializer(screening).data if screening else None,
        })


class NcpRecordListCreateView(generics.ListCreateAPIView):
    serializer_class = NcpRecordSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return NcpRecord.objects.filter(
            relationship_id=self.kwargs["relationship_id"], relationship__rnd=self.request.user
        ).order_by("-encounter_date", "-created_at")

    def perform_create(self, serializer):
        # One open draft per client at a time: the form resumes it rather
        # than starting another (also guards against a double autosave POST).
        relationship = serializer.validated_data["relationship"]
        ensure_open(relationship)
        if NcpRecord.objects.filter(relationship=relationship, status=NcpRecord.Status.DRAFT).exists():
            raise ValidationError("This client already has an unfinished NCP record — continue that one instead.")
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
        ensure_open(serializer.validated_data["relationship"])
        _set_bmi(serializer.save(source="rnd"))


def _set_bmi(record):
    """BMI from the weight and the height in the client's latest screening
    (height isn't stored on its own; same lookup ScreeningCreateView uses)."""
    if record.weight_kg is None:
        return
    latest_screening = PreConsultationScreening.objects.filter(
        client=record.relationship.client_id
    ).order_by("-created_at").first()
    if latest_screening and latest_screening.height_cm:
        record.bmi = calculate_bmi(record.weight_kg, latest_screening.height_cm)
        record.save(update_fields=["bmi"])


class ClientProgressRecordListView(generics.ListCreateAPIView):
    """Client's own progress history, across all relationships (no RND notes).
    POST logs a home reading ("self-reported") on their current RND's record —
    the proposal's client self-monitoring between sessions."""

    permission_classes = [IsClient]

    def get_serializer_class(self):
        return ClientSelfLogSerializer if self.request.method == "POST" else ClientProgressRecordSerializer

    def get_queryset(self):
        return ProgressRecord.objects.filter(
            relationship__client=self.request.user
        ).order_by("-record_date", "-created_at")

    def perform_create(self, serializer):
        from rest_framework.exceptions import ValidationError

        from scheduling.models import RndClientRelationship

        rel = RndClientRelationship.objects.filter(client=self.request.user, status=RndClientRelationship.Status.ACTIVE).first()
        if rel is None:
            raise ValidationError({"detail": "You can log readings once an RND is caring for you — they'll see them on your chart."})
        _set_bmi(serializer.save(relationship=rel, source="client"))


class ClientProgressRecordDetailView(generics.DestroyAPIView):
    """A client deletes one of their own self-reported readings (never the RND's)."""

    permission_classes = [IsClient]

    def get_queryset(self):
        return ProgressRecord.objects.filter(relationship__client=self.request.user, source="client")


class ClientAdherenceView(APIView):
    """Meal-plan adherence per week for the client's Progress Tracker
    (same rules as the RND dashboard: followed 1, partly 0.5, unlogged 0)."""

    permission_classes = [IsClient]

    def get(self, request):
        from datetime import timedelta

        from scheduling.models import RndClientRelationship
        from scheduling.patient_insights import CareData, adherence_pct

        rels = list(RndClientRelationship.objects.filter(client=request.user, status=RndClientRelationship.Status.ACTIVE))
        if not rels:
            return Response({"weeks": []})
        care = CareData(rels)
        weeks = []
        for k in range(7, -1, -1):  # oldest first
            planned, logged, score, waiting = care.window(7 * k)
            end = care.today - timedelta(days=7 * k)
            weeks.append({"start": end - timedelta(days=6), "end": end, "planned": planned, "logged": logged,
                          "waiting": waiting, "pct": adherence_pct(planned, score, waiting)})
        return Response({"weeks": weeks})


class NcpRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NcpRecordSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return NcpRecord.objects.filter(relationship__rnd=self.request.user)

    def perform_update(self, serializer):
        # A finalized record is permanent — the UI locks it, but the API
        # must refuse edits too.
        if serializer.instance.status == NcpRecord.Status.COMPLETED:
            raise PermissionDenied("This NCP record is finalized and can no longer be edited.")
        ensure_open(serializer.instance.relationship)
        serializer.save()

    def perform_destroy(self, instance):
        # Only an unfinished draft can be discarded; a finalized record is
        # part of the patient's clinical history and stays.
        from core.models import AuditLog

        if instance.status == NcpRecord.Status.COMPLETED:
            raise PermissionDenied("This NCP record is finalized and can't be deleted.")
        AuditLog.objects.create(
            user=self.request.user, action="ncp_record.deleted", table_name="ncp_records", record_id=instance.id,
            old_values={"status": instance.status, "relationship_id": instance.relationship_id},
        )
        instance.delete()


class NcpRecordFinalizeView(generics.UpdateAPIView):
    serializer_class = NcpRecordSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return NcpRecord.objects.filter(relationship__rnd=self.request.user)

    def patch(self, request, *args, **kwargs):
        record = self.get_object()
        ensure_open(record.relationship)
        # The clinical minimum; the form itself requires every non-optional
        # field before it auto-finalizes (NcpRecordModal.vue).
        missing = record.finalize_missing()
        if missing:
            return Response(
                {"detail": "Can't finalize yet — missing " + ", ".join(missing) + "."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        record.status = NcpRecord.Status.COMPLETED
        record.save(update_fields=["status", "updated_at"])
        return Response(NcpRecordSerializer(record).data)
