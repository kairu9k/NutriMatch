from django.conf import settings
from django.db import models

from scheduling.models import Appointment, RndClientRelationship


class PreConsultationScreening(models.Model):
    class ActivityLevel(models.TextChoices):
        SEDENTARY = "sedentary", "Sedentary"
        LIGHTLY_ACTIVE = "lightly_active", "Lightly Active"
        MODERATELY_ACTIVE = "moderately_active", "Moderately Active"
        VERY_ACTIVE = "very_active", "Very Active"
        EXTRA_ACTIVE = "extra_active", "Extra Active"

    class NrsRisk(models.TextChoices):
        NO_RISK = "no_risk", "No Risk"
        AT_RISK = "at_risk", "At Risk"
        HIGH_RISK = "high_risk", "High Risk"

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="screenings"
    )
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="screenings"
    )
    height_cm = models.DecimalField(max_digits=5, decimal_places=2)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi_category = models.CharField(max_length=50, null=True, blank=True)
    bmr_kcal = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    tdee_kcal = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    activity_level = models.CharField(
        max_length=20, choices=ActivityLevel.choices, default=ActivityLevel.SEDENTARY
    )
    nrs_score = models.SmallIntegerField(null=True, blank=True)
    nrs_risk = models.CharField(max_length=20, choices=NrsRisk.choices, null=True, blank=True)
    symptoms = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pre_consultation_screenings"

    def __str__(self):
        return f"Screening for {self.client.full_name} ({self.created_at:%Y-%m-%d})"


class NcpRecord(models.Model):
    """Longitudinal record spanning all 4 NCP phases (Assessment, Diagnosis,
    Intervention, Monitoring) — one row per encounter, not one table per phase."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        COMPLETED = "completed", "Completed"

    class GoalStatus(models.TextChoices):
        MET = "met", "Met"
        PARTIALLY_MET = "partially_met", "Partially Met"
        NOT_MET = "not_met", "Not Met"
        ONGOING = "ongoing", "Ongoing"

    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="ncp_records"
    )
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="ncp_records"
    )
    encounter_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Phase 1 — Assessment
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_pressure = models.CharField(max_length=20, null=True, blank=True)
    blood_glucose = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hba1c = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    lab_notes = models.TextField(null=True, blank=True)
    assessment_notes = models.TextField(null=True, blank=True)

    # Phase 2 — Diagnosis (PES statement)
    pes_problem = models.CharField(max_length=500, null=True, blank=True)
    pes_etiology = models.TextField(null=True, blank=True)
    pes_signs = models.TextField(null=True, blank=True)

    # Phase 3 — Intervention
    diet_prescription = models.TextField(null=True, blank=True)
    target_kcal = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    target_protein_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    target_carb_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    target_fat_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    intervention_notes = models.TextField(null=True, blank=True)

    # Phase 4 — Monitoring & Evaluation
    monitoring_notes = models.TextField(null=True, blank=True)
    goal_status = models.CharField(
        max_length=20, choices=GoalStatus.choices, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ncp_records"

    def __str__(self):
        return f"NCP Record #{self.id} — {self.encounter_date} ({self.status})"


class ProgressRecord(models.Model):
    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="progress_records"
    )
    record_date = models.DateField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    blood_pressure = models.CharField(max_length=20, null=True, blank=True)
    blood_glucose = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    hba1c = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    adherence_pct = models.SmallIntegerField(null=True, blank=True)
    client_notes = models.TextField(null=True, blank=True)
    rnd_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "progress_records"

    def __str__(self):
        return f"Progress Record — {self.record_date}"
