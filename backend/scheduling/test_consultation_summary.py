"""Consultation summary after a completed visit."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from clinical.models import NcpRecord, PreConsultationScreening, ProgressRecord
from communication.models import NotificationLog
from core.test_utils import approve_rnd, onboard_client

from .models import Appointment, RndClientRelationship
from .serializers import PH_TZ


class ConsultationSummaryTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@cs.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@cs.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        PreConsultationScreening.objects.create(client=self.c, height_cm=Decimal("160"), weight_kg=Decimal("72"))
        self.visit = Appointment.objects.create(relationship=self.rel, type="video", status="completed",
                                                scheduled_at=timezone.now() - timedelta(days=1))
        visit_day = self.visit.scheduled_at.astimezone(PH_TZ).date()  # the app works in Philippine time
        self.ncp = NcpRecord.objects.create(
            relationship=self.rel, appointment=self.visit, encounter_date=visit_day,
            weight_kg=Decimal("70"), height_cm=Decimal("160"), bmi=Decimal("27.34"), blood_pressure="130/85",
            pes_problem="Excessive energy intake", pes_etiology="large portions", pes_signs="BMI 27.3",
            diet_prescription="1500 kcal balanced diet", target_kcal=Decimal("1500"),
            intervention_notes="Use the plate method.", assessment_notes="PRIVATE-ASSESSMENT", monitoring_notes="PRIVATE-MONITOR",
        )
        ProgressRecord.objects.create(relationship=self.rel, record_date=visit_day,
                                      weight_kg=Decimal("70"), rnd_notes="PRIVATE-PROGRESS")
        self.api = APIClient()

    def _get(self, user, role):
        self.api.force_authenticate(user)
        return self.api.get(f"/api/{role}/appointments/{self.visit.id}/summary/")

    def test_client_sees_only_finalized_care_plan_and_no_private_notes(self):
        data = self._get(self.c, "client").data
        self.assertTrue(data["ncp_pending"])
        self.assertIsNone(data["care_plan"])
        self.ncp.status = "completed"
        self.ncp.save()
        resp = self._get(self.c, "client")
        self.assertEqual(resp.data["care_plan"]["pes_problem"], "Excessive energy intake")
        self.assertEqual(resp.data["care_plan"]["advice"], "Use the plate method.")
        self.assertEqual(resp.data["weight_change"]["kg"], -2.0)  # vs screening
        body = str(resp.content)
        for secret in ("PRIVATE-ASSESSMENT", "PRIVATE-MONITOR", "PRIVATE-PROGRESS"):
            self.assertNotIn(secret, body)

    def test_rnd_sees_drafts_and_clinical_notes(self):
        data = self._get(self.rnd, "rnd").data
        self.assertEqual(data["care_plan"]["status"], "draft")
        self.assertEqual(data["care_plan"]["assessment_notes"], "PRIVATE-ASSESSMENT")
        self.assertEqual(data["measurements"]["blood_pressure"], "130/85")

    def test_only_completed_and_own(self):
        self.visit.status = "confirmed"
        self.visit.save()
        self.assertEqual(self._get(self.c, "client").status_code, 400)
        self.visit.status = "completed"
        self.visit.save()
        other = onboard_client(User.objects.create_user(email="o@cs.ph", password="x", role="client", first_name="O", last_name="C"))
        self.assertEqual(self._get(other, "client").status_code, 404)

    def test_completing_notifies_the_client(self):
        appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed",
                                          scheduled_at=timezone.now() - timedelta(hours=2))
        self.api.force_authenticate(self.rnd)
        self.assertEqual(self.api.patch(f"/api/rnd/appointments/{appt.id}/complete/").status_code, 200)
        self.assertTrue(NotificationLog.objects.filter(recipient=self.c, subject="Your consultation summary is ready").exists())
