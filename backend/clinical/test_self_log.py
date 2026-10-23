"""Client self-monitoring: home readings ("self-reported") and weekly adherence."""

from datetime import time
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client
from nutrition.models import MealLog, MealPlan, MealPlanMeal
from scheduling.models import RndClientRelationship
from scheduling.patient_insights import ph_tz

from .models import PreConsultationScreening, ProgressRecord


class SelfLogTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@s.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@s.ph", password="x", role="client", first_name="Ana", last_name="C"))
        PreConsultationScreening.objects.create(client=self.c, height_cm=Decimal("160"), weight_kg=Decimal("70"))
        self.api = APIClient()
        self.api.force_authenticate(self.c)
        self.today = timezone.now().astimezone(ph_tz()).date().isoformat()

    def test_needs_an_active_rnd(self):
        resp = self.api.post("/api/client/progress/", {"record_date": self.today, "weight_kg": "68"}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_log_view_delete_and_rnd_sees_it(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        resp = self.api.post("/api/client/progress/", {"record_date": self.today, "weight_kg": "68", "blood_pressure": "130/85",
                                                        "client_notes": "Morning, after walking"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        rec = ProgressRecord.objects.get(pk=resp.data["id"])
        self.assertEqual((rec.source, rec.relationship_id, rec.client_notes), ("client", rel.id, "Morning, after walking"))
        self.assertEqual(float(rec.bmi), 26.56)  # from the screening height
        # Same limits as the RND's records.
        self.assertEqual(self.api.post("/api/client/progress/", {"record_date": self.today, "weight_kg": "900"}, format="json").status_code, 400)
        self.assertEqual(self.api.post("/api/client/progress/", {"record_date": self.today}, format="json").status_code, 400)
        # The RND sees it, marked self-reported, with the client's note.
        rnd = APIClient()
        rnd.force_authenticate(self.rnd)
        row = rnd.get(f"/api/rnd/relationships/{rel.id}/summary/").data["progress"][0]
        self.assertEqual((row["source"], row["client_notes"]), ("client", "Morning, after walking"))
        # Clients can delete their own readings, never the RND's.
        rnd_rec = ProgressRecord.objects.create(relationship=rel, record_date=self.today, weight_kg=Decimal("69"))
        self.assertEqual(self.api.delete(f"/api/client/progress/{rnd_rec.id}/").status_code, 404)
        self.assertEqual(self.api.delete(f"/api/client/progress/{rec.id}/").status_code, 204)

    def test_weekly_adherence(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        plan = MealPlan.objects.create(relationship=rel, name="P", status="active",
                                       sent_at=timezone.now() - timezone.timedelta(days=30), first_sent_at=timezone.now() - timezone.timedelta(days=30))
        meal = MealPlanMeal.objects.create(meal_plan=plan, meal_time="breakfast", scheduled_time=time(0, 1), created_at=None)
        MealLog.objects.create(meal_plan_meal=meal, client=self.c, log_date=timezone.now().astimezone(ph_tz()).date(), status="followed")
        weeks = self.api.get("/api/client/adherence/").data["weeks"]
        self.assertEqual(len(weeks), 8)
        self.assertEqual(weeks[-1]["logged"], 1)
        self.assertEqual(weeks[-1]["planned"], 7)

    def test_older_weeks_count_their_logs(self):
        # a log four weeks back still counts (the chart covers 8 weeks)
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        plan = MealPlan.objects.create(relationship=rel, name="P", status="active",
                                       sent_at=timezone.now() - timezone.timedelta(days=50), first_sent_at=timezone.now() - timezone.timedelta(days=50))
        meal = MealPlanMeal.objects.create(meal_plan=plan, meal_time="breakfast", scheduled_time=time(0, 1), created_at=None)
        old_day = timezone.now().astimezone(ph_tz()).date() - timezone.timedelta(days=30)
        MealLog.objects.create(meal_plan_meal=meal, client=self.c, log_date=old_day, status="followed")
        weeks = self.api.get("/api/client/adherence/").data["weeks"]
        self.assertEqual(sum(w["logged"] for w in weeks), 1)
        self.assertTrue(any(w["pct"] for w in weeks[:-2]))
