from rest_framework import serializers

from .models import NcpRecord, PreConsultationScreening, ProgressRecord


class PreConsultationScreeningSerializer(serializers.ModelSerializer):
    """reduced_intake/has_chronic_illness are write-only NRS-2002 inputs —
    not stored on the model (same pattern as activity_level feeding TDEE
    without being a "result" field itself). Weight-loss-percent isn't an
    input at all: it's computed server-side from the client's own screening
    history, not self-reported."""

    reduced_intake = serializers.BooleanField(write_only=True, required=False, default=False)
    has_chronic_illness = serializers.BooleanField(write_only=True, required=False, default=False)
    # Optional Mifflin-St Jeor inputs; when omitted, ScreeningCreateView falls
    # back to the client's profile (date_of_birth / sex). Not stored here.
    age = serializers.IntegerField(write_only=True, required=False, min_value=1, max_value=120)
    sex = serializers.ChoiceField(write_only=True, required=False, choices=["male", "female"])

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

    class Meta:
        model = NcpRecord
        fields = [
            "id", "relationship_id", "client_name", "status", "updated_at",
            "weight_kg", "height_cm", "pes_problem", "diet_prescription", "goal_status",
        ]

    def get_client_name(self, obj):
        client = obj.relationship.client
        return f"{client.first_name} {client.last_name}"


class NcpRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NcpRecord
        fields = [
            "id", "relationship", "appointment", "encounter_date", "status",
            # Phase 1 — Assessment
            "weight_kg", "height_cm", "bmi", "blood_pressure", "blood_glucose",
            "hba1c", "lab_notes", "assessment_notes",
            # Phase 2 — Diagnosis
            "pes_problem", "pes_etiology", "pes_signs",
            # Phase 3 — Intervention
            "diet_prescription", "target_kcal", "target_protein_g", "target_carb_g",
            "target_fat_g", "intervention_notes",
            # Phase 4 — Monitoring
            "monitoring_notes", "goal_status",
            "created_at", "updated_at",
        ]
        read_only_fields = ["bmi"]

    def validate(self, attrs):
        # bmi is always derived server-side from weight/height (or the
        # existing record's values on a partial update), same
        # calculate_bmi/classify_bmi_asia_pacific used by the screening flow —
        # never trust a client-supplied BMI.
        from .services import calculate_bmi

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


class ProgressRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressRecord
        fields = [
            "id", "relationship", "record_date", "weight_kg", "bmi", "blood_pressure",
            "blood_glucose", "hba1c", "adherence_pct", "client_notes", "rnd_notes", "created_at",
        ]
        read_only_fields = ["bmi"]

    def validate_relationship(self, value):
        request = self.context["request"]
        if value.rnd_id != request.user.id:
            raise serializers.ValidationError("You can only log progress for your own clients.")
        return value
