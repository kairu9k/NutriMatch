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

    def test_record_progress_computes_bmi(self):
        resp = self.api.post(self.url, {"relationship": self.rel.id, "record_date": str(timezone.now().date()),
                                        "weight_kg": "68.5", "rnd_notes": "Private"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(ProgressRecord.objects.get().bmi, Decimal("26.76"))
        summary = self.api.get(f"/api/rnd/relationships/{self.rel.id}/summary/").data
        self.assertEqual(summary["patient"]["progress"]["weight_change_kg"], Decimal("-1.5"))

    def test_progress_validation(self):
        tomorrow = str(timezone.now().date() + timedelta(days=2))
        today = str(timezone.now().date())
        self.assertIn("record_date", self.api.post(self.url, {"relationship": self.rel.id, "record_date": tomorrow, "weight_kg": "60"}, format="json").data)
        self.assertIn("weight_kg", self.api.post(self.url, {"relationship": self.rel.id, "record_date": today, "weight_kg": "650"}, format="json").data)
        self.assertEqual(self.api.post(self.url, {"relationship": self.rel.id, "record_date": today}, format="json").status_code, 400)

    def test_client_never_sees_private_note(self):
        ProgressRecord.objects.create(relationship=self.rel, record_date=timezone.now().date(), weight_kg=Decimal("69"), rnd_notes="Private")
        self.api.force_authenticate(self.c)
        rows = self.api.get("/api/client/progress/").data
        rows = rows.get("results", rows) if isinstance(rows, dict) else rows
        self.assertNotIn("rnd_notes", rows[0])
