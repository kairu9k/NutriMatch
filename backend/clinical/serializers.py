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

    class Meta:
        model = PreConsultationScreening
        fields = [
            "id", "appointment", "height_cm", "weight_kg", "bmi", "bmi_category",
            "bmr_kcal", "tdee_kcal", "activity_level", "nrs_score", "nrs_risk",
            "reduced_intake", "has_chronic_illness", "symptoms", "created_at",
        ]
        read_only_fields = ["bmi", "bmi_category", "bmr_kcal", "tdee_kcal", "nrs_score", "nrs_risk"]


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

    def validate_relationship(self, value):
        request = self.context["request"]
        if value.rnd_id != request.user.id:
            raise serializers.ValidationError("You can only create NCP records for your own clients.")
        return value


class ProgressRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressRecord
        fields = [
            "id", "relationship", "record_date", "weight_kg", "blood_pressure",
            "blood_glucose", "hba1c", "adherence_pct", "client_notes", "rnd_notes", "created_at",
        ]

    def validate_relationship(self, value):
        request = self.context["request"]
        if value.rnd_id != request.user.id:
            raise serializers.ValidationError("You can only log progress for your own clients.")
        return value
