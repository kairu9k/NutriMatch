from decimal import Decimal

from rest_framework import serializers

from core.validators import NonNegativeNumbersMixin, validate_blood_pressure

from .models import NcpRecord, PreConsultationScreening, ProgressRecord


class PreConsultationScreeningSerializer(NonNegativeNumbersMixin, serializers.ModelSerializer):
    """reduced_intake/has_chronic_illness are write-only NRS-2002 inputs —
    not stored on the model (same pattern as activity_level feeding TDEE
    without being a "result" field itself). Weight-loss-percent isn't an
    input at all: it's computed server-side from the client's own screening
    history, not self-reported."""

    reduced_intake = serializers.BooleanField(write_only=True, required=False, default=False)
    has_chronic_illness = serializers.BooleanField(write_only=True, required=False, default=False)
    # Optional Mifflin-St Jeor inputs; when omitted, ScreeningCreateView falls
    # back to the client's profile (date_of_birth / sex). Not stored here.
    # Only used when the profile has no date of birth — otherwise the age
    # comes from the DOB (clients must be 18+, accounts.validators).
    age = serializers.IntegerField(
        write_only=True, required=False, min_value=18, max_value=120,
        error_messages={"min_value": "Age must be between 18 and 120 years.", "max_value": "Age must be between 18 and 120 years."},
    )
    sex = serializers.ChoiceField(write_only=True, required=False, choices=["male", "female"])
    # Realistic adult ranges, so a typo like 1700 cm or 7 kg can't produce a
    # nonsense BMI/BMR. Mirrored in PreConsultationScreening.vue.
    height_cm = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("100"), max_value=Decimal("250"),
        error_messages={
            "min_value": "Height must be between 100 and 250 cm.",
            "max_value": "Height must be between 100 and 250 cm.",
            "max_digits": "Height must be between 100 and 250 cm.",
            "max_decimal_places": "Use at most 2 decimal places.",
            "invalid": "Enter a number.",
        },
    )
    weight_kg = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("25"), max_value=Decimal("300"),
        error_messages={
            "min_value": "Weight must be between 25 and 300 kg.",
            "max_value": "Weight must be between 25 and 300 kg.",
            "max_digits": "Weight must be between 25 and 300 kg.",
            "max_decimal_places": "Use at most 2 decimal places.",
            "invalid": "Enter a number.",
        },
    )

    class Meta:
        model = PreConsultationScreening
        fields = [
            "id", "appointment", "height_cm", "weight_kg", "bmi", "bmi_category",
            "bmr_kcal", "tdee_kcal", "activity_level", "nrs_score", "nrs_risk",
            "reduced_intake", "has_chronic_illness", "age", "sex", "symptoms", "created_at",
        ]
        read_only_fields = ["bmi", "bmi_category", "bmr_kcal", "tdee_kcal", "nrs_score", "nrs_risk"]


class NcpDraftListSerializer(serializers.ModelSerializer):
    """Lightweight cross-patient NCP record list — for the dashboard's
    'resume a draft' panel (drafts only) and the NCP Records page's
    cross-patient history table (all records). Includes just enough of each
    phase's key field for the frontend to derive "which phase looks
    unfinished" the same way the single-record page does, without shipping
    every clinical field cross-patient."""

    client_name = serializers.SerializerMethodField()
    is_follow_up = serializers.SerializerMethodField()

    class Meta:
        model = NcpRecord
        fields = [
            "id", "relationship_id", "client_name", "status", "is_follow_up", "created_at", "updated_at",
            "weight_kg", "height_cm", "pes_problem", "diet_prescription", "goal_status",
        ]

    def get_is_follow_up(self, obj):
        return obj.is_follow_up()

    def get_client_name(self, obj):
        client = obj.relationship.client
        return f"{client.first_name} {client.last_name}"


class NcpExtraFieldSerializer(serializers.Serializer):
    """One RND-added row on the Assessment or Intervention form."""

    # Blank labels are accepted here and dropped in NcpRecordSerializer.validate
    # (an empty "+ Add Field" row the RND never filled in).
    label = serializers.CharField(max_length=100, allow_blank=True)
    value = serializers.CharField(max_length=500, allow_blank=True)
    unit = serializers.CharField(max_length=30, allow_blank=True, required=False, default="")


class NcpRecordSerializer(NonNegativeNumbersMixin, serializers.ModelSerializer):
    assessment_extra = NcpExtraFieldSerializer(many=True, required=False)
    intervention_extra = NcpExtraFieldSerializer(many=True, required=False)
    is_follow_up = serializers.SerializerMethodField()

    class Meta:
        model = NcpRecord
        fields = [
            "id", "relationship", "appointment", "encounter_date", "status",
            # Phase 1 — Assessment
            "weight_kg", "height_cm", "bmi", "blood_pressure", "blood_glucose",
            "hba1c", "lab_notes", "assessment_notes", "assessment_extra",
            # Phase 2 — Diagnosis
            "pes_problem", "pes_etiology", "pes_signs",
            # Phase 3 — Intervention
            "diet_prescription", "target_kcal", "target_protein_g", "target_carb_g",
            "target_fat_g", "intervention_notes", "intervention_extra",
            # Phase 4 — Monitoring
            "monitoring_notes", "goal_status",
            "is_follow_up", "created_at", "updated_at",
        ]
        # status only changes through NcpRecordFinalizeView — never via a
        # plain PATCH, or a finalized record could be flipped back to draft.
        read_only_fields = ["bmi", "status"]

    def get_is_follow_up(self, obj):
        return obj.is_follow_up()

    def validate(self, attrs):
        # bmi is always derived server-side from weight/height (or the
        # existing record's values on a partial update), same
        # calculate_bmi/classify_bmi_asia_pacific used by the screening flow —
        # never trust a client-supplied BMI.
        from .services import calculate_bmi

        # Extra rows: trim, drop rows with no label, cap how many can be added.
        for key in ("assessment_extra", "intervention_extra"):
            if key in attrs:
                rows = [
                    {"label": r["label"].strip(), "value": r["value"].strip(), "unit": (r.get("unit") or "").strip()}
                    for r in attrs[key] if r["label"].strip()
                ]
                if len(rows) > 30:
                    raise serializers.ValidationError({key: ["You can add up to 30 extra fields."]})
                attrs[key] = rows

        weight_kg = attrs.get("weight_kg", getattr(self.instance, "weight_kg", None))
        height_cm = attrs.get("height_cm", getattr(self.instance, "height_cm", None))
        if weight_kg and height_cm:
            attrs["bmi"] = calculate_bmi(weight_kg, height_cm)
        return attrs

    def validate_relationship(self, value):
        request = self.context["request"]
        if value.rnd_id != request.user.id:
            raise serializers.ValidationError("You can only create NCP records for your own clients.")
        return value

    def validate_blood_pressure(self, value):
        return validate_blood_pressure(value)


class ProgressRecordSerializer(NonNegativeNumbersMixin, serializers.ModelSerializer):
    class Meta:
        model = ProgressRecord
        fields = [
            "id", "relationship", "record_date", "weight_kg", "bmi", "blood_pressure",
            "blood_glucose", "hba1c", "adherence_pct", "client_notes", "rnd_notes", "created_at",
        ]
        read_only_fields = ["bmi"]

    # Sensible adult ranges — catches typos (e.g. 650 kg) before they skew charts and alerts.
    RANGES = {
        "weight_kg": (Decimal("25"), Decimal("300"), "Weight must be between 25 and 300 kg."),
        "blood_glucose": (Decimal("20"), Decimal("600"), "Fasting glucose must be between 20 and 600 mg/dL."),
        "hba1c": (Decimal("3"), Decimal("20"), "HbA1c must be between 3 and 20%."),
    }

    def validate_relationship(self, value):
        request = self.context["request"]
        if value.rnd_id != request.user.id:
            raise serializers.ValidationError("You can only log progress for your own clients.")
        return value

    def validate_record_date(self, value):
        from scheduling.serializers import PH_TZ
        from django.utils import timezone

        if value > timezone.now().astimezone(PH_TZ).date():
            raise serializers.ValidationError("The date can't be in the future.")
        return value

    def validate_blood_pressure(self, value):
        return validate_blood_pressure(value)

    def validate_adherence_pct(self, value):
        if value is not None and not 0 <= value <= 100:
            raise serializers.ValidationError("Adherence must be between 0 and 100%.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        errors = {}
        for field, (low, high, msg) in self.RANGES.items():
            v = attrs.get(field)
            if v is not None and not low <= v <= high:
                errors[field] = msg
        if errors:
            raise serializers.ValidationError(errors)
        if not any(attrs.get(f) not in (None, "") for f in ("weight_kg", "blood_pressure", "blood_glucose", "hba1c")):
            raise serializers.ValidationError({"detail": "Enter at least one measurement."})
        return attrs


class ClientProgressRecordSerializer(serializers.ModelSerializer):
    """What a client sees of their progress — the RND's private note is left out."""

    class Meta:
        model = ProgressRecord
        fields = ["id", "record_date", "weight_kg", "bmi", "blood_pressure", "blood_glucose", "hba1c", "adherence_pct", "created_at"]
