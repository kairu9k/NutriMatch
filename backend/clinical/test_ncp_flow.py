"""NCP form flow: partial drafts, the finalize minimum, linking a consultation, and the form context."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship

from .models import NcpRecord, PreConsultationScreening, ProgressRecord


class NcpFlowTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@n.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@n.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        PreConsultationScreening.objects.create(client=self.c, height_cm=Decimal("160"), weight_kg=Decimal("70"), tdee_kcal=Decimal("1900"))
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)
        self.url = f"/api/rnd/relationships/{self.rel.id}/ncp/"
        self.today = str(timezone.now().date())

    def test_partial_draft_saves(self):
        resp = self.api.post(self.url, {"relationship": self.rel.id, "encounter_date": self.today, "weight_kg": "69"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["status"], "draft")

    def test_finalize_needs_full_pes_and_kcal(self):
        rec = NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date(), weight_kg=Decimal("70"),
                                       height_cm=Decimal("160"), pes_problem="Excessive energy intake", diet_prescription="1500 kcal")
        resp = self.api.patch(f"/api/rnd/ncp/{rec.id}/finalize/")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("etiology", resp.data["detail"])
        self.assertIn("target kcal", resp.data["detail"])
        rec.pes_etiology, rec.pes_signs, rec.target_kcal = "large portions", "BMI 27", Decimal("1500")
        rec.save()
        self.assertEqual(self.api.patch(f"/api/rnd/ncp/{rec.id}/finalize/").status_code, 200)

    def test_appointment_must_be_same_patient(self):
        other_client = onboard_client(User.objects.create_user(email="o@n.ph", password="x", role="client", first_name="O", last_name="C"))
        other_rel = RndClientRelationship.objects.create(rnd=self.rnd, client=other_client, status="active")
        appt = Appointment.objects.create(relationship=other_rel, type="video", status="confirmed", scheduled_at=timezone.now())
        resp = self.api.post(self.url, {"relationship": self.rel.id, "encounter_date": self.today, "appointment": appt.id}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("appointment", resp.data)

    def test_context_prefill_and_previous(self):
        ProgressRecord.objects.create(relationship=self.rel, record_date=timezone.now().date(), weight_kg=Decimal("68"), blood_pressure="120/80")
        NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date() - timedelta(days=30), status="completed",
                                 weight_kg=Decimal("70"), height_cm=Decimal("160"), pes_problem="Excessive energy intake", target_kcal=Decimal("1500"))
        appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=timezone.now() + timedelta(minutes=5))
        d = self.api.get(f"{self.url}context/").data
        self.assertTrue(d["is_follow_up"])
        self.assertEqual(d["prefill"]["weight_kg"]["value"], 68.0)
        self.assertEqual(d["prefill"]["weight_kg"]["source"], "progress record")
        self.assertEqual(d["prefill"]["blood_pressure"]["value"], "120/80")
        self.assertEqual(d["previous"]["pes_problem"], "Excessive energy intake")
        self.assertEqual(d["previous"]["weight_change_kg"], -2.0)
        self.assertEqual(d["appointment_id"], appt.id)

    def test_context_is_own_patients_only(self):
        other = approve_rnd(User.objects.create_user(email="x@n.ph", password="x", role="rnd", first_name="X", last_name="R"))
        self.api.force_authenticate(other)
        self.assertEqual(self.api.get(f"{self.url}context/").status_code, 404)
