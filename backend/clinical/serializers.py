from rest_framework import serializers

from .models import NcpRecord, PreConsultationScreening


class PreConsultationScreeningSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreConsultationScreening
        fields = [
            "id", "appointment", "height_cm", "weight_kg", "bmi", "bmi_category",
            "bmr_kcal", "tdee_kcal", "activity_level", "nrs_score", "nrs_risk",
            "symptoms", "created_at",
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
