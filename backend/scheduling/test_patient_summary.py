"""Client Detail summary and recording progress."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from clinical.models import PreConsultationScreening, ProgressRecord
from core.test_utils import approve_rnd, onboard_client

from .models import RndClientRelationship


class PatientSummaryTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@s.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@s.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        PreConsultationScreening.objects.create(client=self.c, height_cm=Decimal("160"), weight_kg=Decimal("70"), nrs_score=1)
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)
        self.url = f"/api/rnd/relationships/{self.rel.id}/progress/"

    def test_summary_for_own_patient_only(self):
        resp = self.api.get(f"/api/rnd/relationships/{self.rel.id}/summary/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["screening"]["weight_kg"], 70.0)
        self.assertEqual(len(resp.data["adherence_days"]), 14)
        other = approve_rnd(User.objects.create_user(email="o@s.ph", password="x", role="rnd", first_name="O", last_name="R"))
        self.api.force_authenticate(other)
        self.assertEqual(self.api.get(f"/api/rnd/relationships/{self.rel.id}/summary/").status_code, 404)

    def test_rnd_cannot_type_progress_directly(self):
        # Progress comes from finalized NCP records only (2026-10-23).
        resp = self.api.post(self.url, {"relationship": self.rel.id, "record_date": str(timezone.now().date()),
                                        "weight_kg": "68.5"}, format="json")
        self.assertEqual(resp.status_code, 405)
        self.assertEqual(self.api.get(self.url).status_code, 200)

    def test_finalized_ncp_becomes_progress(self):
        from clinical.models import NcpRecord

        today = timezone.now().date()
        ncp = NcpRecord.objects.create(
            relationship=self.rel, encounter_date=today, weight_kg=Decimal("68.5"), height_cm=Decimal("160"),
            bmi=Decimal("26.76"), blood_pressure="128/84", blood_glucose=Decimal("104"),
            assessment_notes="Private assessment", pes_problem="Excessive energy intake", pes_etiology="large servings",
            pes_signs="BMI 26.8", diet_prescription="1500 kcal", target_kcal=Decimal("1500"),
        )
        self.assertFalse(ProgressRecord.objects.exists())  # a draft isn't progress yet
        self.assertEqual(self.api.patch(f"/api/rnd/ncp/{ncp.id}/finalize/").status_code, 200)
        p = ProgressRecord.objects.get()
        self.assertEqual((p.record_date, p.weight_kg, p.bmi, p.blood_pressure, p.blood_glucose, p.source),
                         (today, Decimal("68.5"), Decimal("26.76"), "128/84", Decimal("104"), "rnd"))
        self.assertIsNone(p.rnd_notes)
        summary = self.api.get(f"/api/rnd/relationships/{self.rel.id}/summary/").data
        self.assertEqual(summary["patient"]["progress"]["weight_change_kg"], Decimal("-1.5"))
        # The client sees the measurements on their Progress Tracker.
        self.api.force_authenticate(self.c)
        rows = self.api.get("/api/client/progress/").data
        rows = rows.get("results", rows) if isinstance(rows, dict) else rows
        self.assertEqual([r["weight_kg"] for r in rows], ["68.50"])

    def test_same_day_progress_is_updated_not_duplicated(self):
        from clinical.views import progress_from_ncp
        from clinical.models import NcpRecord

        today = timezone.now().date()
        ProgressRecord.objects.create(relationship=self.rel, record_date=today, weight_kg=Decimal("70"), hba1c=Decimal("6.1"))
        progress_from_ncp(NcpRecord(relationship=self.rel, encounter_date=today, weight_kg=Decimal("69")))
        p = ProgressRecord.objects.get()
        self.assertEqual((p.weight_kg, p.hba1c), (Decimal("69"), Decimal("6.1")))

    def test_client_never_sees_private_note(self):
        ProgressRecord.objects.create(relationship=self.rel, record_date=timezone.now().date(), weight_kg=Decimal("69"), rnd_notes="Private")
        self.api.force_authenticate(self.c)
        rows = self.api.get("/api/client/progress/").data
        rows = rows.get("results", rows) if isinstance(rows, dict) else rows
        self.assertNotIn("rnd_notes", rows[0])
