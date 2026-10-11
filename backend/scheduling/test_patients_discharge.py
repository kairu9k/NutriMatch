"""My Patients rows and discharging a patient."""

from datetime import time, timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from clinical.models import NcpRecord, PreConsultationScreening
from communication.models import Reminder
from core.models import AuditLog
from core.test_utils import approve_rnd, onboard_client
from nutrition.models import MealPlan, MealPlanMeal

from .models import Appointment, RndClientRelationship


class PatientsAndDischargeTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@p.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@p.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active", started_at=timezone.now())
        PreConsultationScreening.objects.create(client=self.c, height_cm=Decimal("160"), weight_kg=Decimal("60"))
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)

    def _row(self):
        return self.api.get("/api/rnd/patients/").data[0]

    def test_stage_and_next_step_follow_the_care_process(self):
        self.assertEqual(self._row()["stage"]["next_step"]["key"], "start_ncp")
        rec = NcpRecord.objects.create(relationship=self.rel, status="draft", encounter_date=timezone.now().date())
        self.assertEqual(self._row()["stage"]["next_step"]["key"], "finish_ncp")
        rec.status, rec.diet_prescription = "completed", "1500 kcal"
        rec.save()
        self.assertEqual(self._row()["stage"]["next_step"]["key"], "create_plan")
        plan = MealPlan.objects.create(relationship=self.rel, name="P", status="active", sent_at=timezone.now())
        MealPlanMeal.objects.create(meal_plan=plan, meal_time="breakfast", scheduled_time=time(0, 1))
        row = self._row()
        self.assertEqual((row["stage"]["meal_plan"], row["stage"]["next_step"]["key"]), ("active", "open"))
        self.assertIsNotNone(row["adherence"])

    def test_discharge_blocked_by_upcoming_consultation_and_draft(self):
        Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=timezone.now() + timedelta(days=1))
        NcpRecord.objects.create(relationship=self.rel, status="draft", encounter_date=timezone.now().date())
        check = self.api.get(f"/api/rnd/relationships/{self.rel.id}/discharge/").data
        self.assertFalse(check["can_discharge"])
        self.assertEqual(len(check["blockers"]), 2)
        resp = self.api.post(f"/api/rnd/relationships/{self.rel.id}/discharge/", {"reason": "Goals reached, care done."}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_discharge_ends_care_and_locks_the_record(self):
        plan = MealPlan.objects.create(relationship=self.rel, name="P", status="active", sent_at=timezone.now())
        reminder = Reminder.objects.create(client=self.c, relationship=self.rel, created_by=self.rnd, title="Water",
                                           send_at=timezone.now() + timedelta(hours=1), repeat="daily")
        short = self.api.post(f"/api/rnd/relationships/{self.rel.id}/discharge/", {"reason": "done"}, format="json")
        self.assertEqual(short.status_code, 400)

        with self.captureOnCommitCallbacks(execute=True):
            resp = self.api.post(f"/api/rnd/relationships/{self.rel.id}/discharge/", {"reason": "Reached her target weight."}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.rel.refresh_from_db()
        plan.refresh_from_db()
        reminder.refresh_from_db()
        self.assertEqual((self.rel.status, plan.status, reminder.is_active), ("discharged", "archived", False))
        self.assertEqual(self.rel.discharge_reason, "Reached her target weight.")
        self.assertTrue(AuditLog.objects.filter(action="relationship.discharged", record_id=self.rel.id).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self._row()["stage"]["next_step"]["key"], "view")

        # read-only afterwards
        self.assertEqual(self.api.post(f"/api/rnd/relationships/{self.rel.id}/ncp/", {"relationship": self.rel.id, "encounter_date": str(timezone.now().date())}, format="json").status_code, 403)
        self.assertEqual(self.api.post(f"/api/relationships/{self.rel.id}/messages/", {"message": "hi"}, format="json").status_code, 403)
        self.assertEqual(self.api.post(f"/api/rnd/meal-plans/{plan.id}/send/").status_code, 403)

    def test_only_own_active_patients(self):
        other = approve_rnd(User.objects.create_user(email="o@p.ph", password="x", role="rnd", first_name="O", last_name="R"))
        self.api.force_authenticate(other)
        self.assertEqual(self.api.post(f"/api/rnd/relationships/{self.rel.id}/discharge/", {"reason": "Not my patient at all."}, format="json").status_code, 404)
        self.rel.status = "pending"
        self.rel.save()
        self.api.force_authenticate(self.rnd)
        self.assertEqual(self.api.post(f"/api/rnd/relationships/{self.rel.id}/discharge/", {"reason": "Not active yet here."}, format="json").status_code, 400)
