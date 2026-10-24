"""RND dashboard: real adherence, alerts, to-dos."""

from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from clinical.models import PreConsultationScreening, ProgressRecord
from core.test_utils import approve_rnd, onboard_client
from nutrition.models import MealLog, MealPlan, MealPlanMeal

from .models import Appointment, Review, RndClientRelationship
from .rnd_dashboard import build_dashboard

PH = ZoneInfo("Asia/Manila")


class RndDashboardTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@d.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@d.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        self.now = datetime(2026, 10, 14, 20, 0, tzinfo=PH)  # Wednesday evening
        self.plan = MealPlan.objects.create(relationship=self.rel, name="P", status="active", sent_at=self.now - timedelta(days=20))
        # created_at=None: the meal is part of the plan from its start.
        self.meal = MealPlanMeal.objects.create(meal_plan=self.plan, day_of_week=None, meal_time="breakfast", scheduled_time=time(7), created_at=None)

    def _log(self, days_ago, status="followed"):
        MealLog.objects.create(meal_plan_meal=self.meal, client=self.c, log_date=(self.now - timedelta(days=days_ago)).date(), status=status)

    def test_rating_averages_public_reviews_only(self):
        self.assertEqual(build_dashboard(self.rnd, self.now)["rating"], {"average": None, "count": 0})
        for i, (stars, public) in enumerate([(5, True), (4, True), (1, False)]):
            appt = Appointment.objects.create(relationship=self.rel, scheduled_at=self.now - timedelta(days=i + 1),
                                              duration_minutes=60, type="video", status="completed")
            Review.objects.create(appointment=appt, client=self.c, rnd=self.rnd, rating=stars, is_public=public)
        self.assertEqual(build_dashboard(self.rnd, self.now)["rating"], {"average": 4.5, "count": 2})

    def test_adherence_counts_planned_meals(self):
        self._log(0)
        self._log(1, "partially_followed")
        d = build_dashboard(self.rnd, self.now)
        days = d["adherence"]["days"]
        self.assertEqual(len(days), 7)
        self.assertEqual((days[-1]["planned"], days[-1]["followed_pct"]), (1, 100))
        self.assertEqual(days[-2]["followed_pct"], 50)
        self.assertEqual(d["adherence"]["pct"], round(1.5 / 7 * 100))

    def test_unrated_logs_wait_outside_adherence(self):
        self._log(0, None)  # logged today, the RND hasn't rated it yet
        self._log(1)
        d = build_dashboard(self.rnd, self.now)
        # 7 planned, 1 waiting: 1 followed out of the 6 that count
        self.assertEqual(d["adherence"]["waiting"], 1)
        self.assertEqual(d["adherence"]["pct"], round(1 / 6 * 100))
        self.assertIsNone(d["adherence"]["days"][-1]["followed_pct"])
        self.assertEqual((d["todo"]["meal_logs_to_review"], d["todo"]["meal_logs_to_review_first"]), (1, self.rel.id))

    def test_resending_an_edited_plan_keeps_adherence_history(self):
        for i in range(7):
            self._log(i)
        self.plan.first_sent_at = self.now - timedelta(days=20)
        self.plan.sent_at = self.now - timedelta(hours=1)  # re-sent today after an edit
        self.plan.save()
        d = build_dashboard(self.rnd, self.now)
        self.assertEqual(d["adherence"]["pct"], 100)
        self.assertEqual(sum(day["planned"] for day in d["adherence"]["days"]), 7)

    def test_slot_added_later_counts_only_from_its_day(self):
        for i in range(7):
            self._log(i)
        MealPlanMeal.objects.create(meal_plan=self.plan, day_of_week=None, meal_time="lunch", scheduled_time=time(12),
                                    created_at=self.now - timedelta(days=1))
        d = build_dashboard(self.rnd, self.now)
        # 7 breakfasts + lunch only yesterday and today (both unlogged)
        self.assertEqual(sum(day["planned"] for day in d["adherence"]["days"]), 9)
        self.assertEqual(d["adherence"]["pct"], round(7 / 9 * 100))

    def test_no_logs_alert(self):
        self._log(5)
        alerts = build_dashboard(self.rnd, self.now)["alerts"]
        self.assertEqual([a["kind"] for a in alerts], ["no_logs"])
        self.assertIn("5 days", alerts[0]["title"])

    def test_nrs_and_weight_alerts(self):
        for i in range(3):
            self._log(i)
        PreConsultationScreening.objects.create(client=self.c, height_cm=Decimal("160"), weight_kg=Decimal("45"), nrs_score=3)
        ProgressRecord.objects.create(relationship=self.rel, record_date=self.now.date() - timedelta(days=14), weight_kg=Decimal("70"))
        ProgressRecord.objects.create(relationship=self.rel, record_date=self.now.date(), weight_kg=Decimal("67.5"))
        kinds = [a["kind"] for a in build_dashboard(self.rnd, self.now)["alerts"]]
        self.assertEqual(kinds[0], "nrs")  # critical first
        self.assertIn("weight", kinds)

    def test_todo_and_next_up(self):
        Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=self.now + timedelta(hours=2))
        Appointment.objects.create(relationship=self.rel, type="video", status="pending", scheduled_at=self.now + timedelta(days=2))
        Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=self.now - timedelta(days=1))
        d = build_dashboard(self.rnd, self.now)
        self.assertEqual((d["todo"]["requests"], d["todo"]["to_complete"]), (1, 1))
        self.assertEqual(d["next_up"]["status"], "confirmed")

    def test_endpoint_rnd_only(self):
        api = APIClient()
        api.force_authenticate(self.rnd)
        self.assertEqual(api.get("/api/rnd/dashboard/").status_code, 200)
        api.force_authenticate(self.c)
        self.assertEqual(api.get("/api/rnd/dashboard/").status_code, 403)

    def test_earnings_this_month_vs_last(self):
        from billing.models import Invoice

        def done(when, amount, status="paid"):
            a = Appointment.objects.create(relationship=self.rel, scheduled_at=when, duration_minutes=60, type="video",
                                           status="completed", completed_at=when)
            Invoice.objects.create(relationship=self.rel, appointment=a, amount=Decimal(amount), commission_amt=Decimal(amount) / 10,
                                   status=status, paid_at=when - timedelta(hours=1))

        done(datetime(2026, 10, 3, 10, tzinfo=PH), "1000")                     # this month: share 900
        done(datetime(2026, 10, 10, 10, tzinfo=PH), "500", "refund_pending")    # refunded money isn't earned
        done(datetime(2026, 9, 5, 10, tzinfo=PH), "600")                       # last month, inside Sep 1-14: 540
        done(datetime(2026, 9, 20, 10, tzinfo=PH), "800")                      # after Sep 14: not compared
        c = build_dashboard(self.rnd, self.now)["earnings_compare"]
        m = {x["key"]: x for x in c["metrics"]}
        self.assertEqual((m["earned"]["now"], m["earned"]["before"], m["earned"]["change_pct"]), (900.0, 540.0, 67))
        self.assertEqual((m["consultations"]["now"], m["consultations"]["before"]), (2, 1))
        self.assertEqual(c["label"], "October 1–14 vs September 1–14")
