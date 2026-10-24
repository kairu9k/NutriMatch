"""Admin dashboard: today counts, attention items, month-over-month comparison."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from communication.models import SupportTicket
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, Review, RndClientRelationship

from .admin_dashboard import _pct


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="a@d.ph", password="x", role="admin", first_name="Ada", last_name="Min")
        self.rnd = approve_rnd(User.objects.create_user(email="r@d.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@d.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        self.api = APIClient()
        self.api.force_authenticate(self.admin)

    def test_attention_items(self):
        now = timezone.now()
        appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=now + timedelta(hours=3))
        Invoice.objects.create(relationship=self.rel, appointment=appt, amount=Decimal("800"), commission_amt=Decimal("80"), status="unpaid")
        SupportTicket.objects.create(user=self.c, category="other", subject="Help please")
        done = Appointment.objects.create(relationship=self.rel, type="video", status="completed",
                                          scheduled_at=now - timedelta(days=2), completed_at=now - timedelta(days=2))
        Review.objects.create(appointment=done, client=self.c, rnd=self.rnd, rating=1)
        d = self.api.get("/api/admin/dashboard/").data
        keys = [a["key"] for a in d["attention"]]
        self.assertEqual(keys[0], "unpaid_soon")  # critical first
        self.assertIn("support", keys)
        self.assertIn("low_reviews", keys)
        self.assertEqual(d["today"]["unpaid_soon"], 1)

    def test_compare_and_pct(self):
        self.assertIsNone(_pct(5, 0))
        self.assertEqual(_pct(150, 100), 50)
        self.assertEqual(_pct(50, 100), -50)
        d = self.api.get("/api/admin/dashboard/").data
        self.assertEqual([m["key"] for m in d["compare"]["metrics"]], ["consultations", "payments", "commission", "new_clients"])

    def test_admin_only(self):
        api = APIClient()
        api.force_authenticate(self.rnd)
        self.assertEqual(api.get("/api/admin/dashboard/").status_code, 403)

    def test_overview(self):
        from datetime import time
        from profiles.models import RndAvailabilitySchedule

        now = timezone.now()
        # bookable RND: fee + bio + a 10-hour weekly block (approve_rnd may set some of these)
        p = self.rnd.rnd_profile
        p.consultation_fee = Decimal("800")
        p.bio = "x" * 60
        p.save()
        RndAvailabilitySchedule.objects.filter(rnd=self.rnd).delete()
        RndAvailabilitySchedule.objects.create(rnd=self.rnd, day_of_week=1, start_time=time(8), end_time=time(18), is_available=True,
                                              effective_from=now.date() - timedelta(days=30))
        # one 60-min booking in the next 7 days -> 60 / 600 = 10%
        Appointment.objects.create(relationship=self.rel, type="video", status="confirmed",
                                   scheduled_at=now + timedelta(days=2), duration_minutes=60)
        # last 30 days: 3 completed, 1 cancelled -> 25% cancelled
        for d in (3, 5, 7):
            Appointment.objects.create(relationship=self.rel, type="video", status="completed",
                                       scheduled_at=now - timedelta(days=d), completed_at=now - timedelta(days=d))
        Appointment.objects.create(relationship=self.rel, type="video", status="cancelled", scheduled_at=now - timedelta(days=4))

        o = self.api.get("/api/admin/dashboard/").data["overview"]
        self.assertEqual(o["clients"]["in_care"], 1)
        self.assertEqual(o["clients"]["onboarded_pct"], 100)
        self.assertEqual(len(o["clients"]["trend"]), 6)
        self.assertEqual(o["rnds"]["approved"], 1)
        self.assertEqual(o["rnds"]["active_30_days"], 1)
        self.assertEqual(o["rnds"]["bookable"], 1)
        self.assertEqual(o["rnds"]["calendar_filled_pct"], 10)
        self.assertEqual(o["platform"]["cancelled_pct_30_days"], 25)
        self.assertEqual(len(o["platform"]["trend"]), 6)

    def test_overview_empty_platform(self):
        o = self.api.get("/api/admin/dashboard/").data["overview"]
        self.assertIsNone(o["platform"]["cancelled_pct_30_days"])
        self.assertEqual(o["platform"]["payments_this_month"], 0.0)

    def test_unconfirmed_applicants_not_counted(self):
        from profiles.models import RndProfile

        done = User.objects.create_user(email="app1@d.ph", password="x", role="rnd", first_name="A", last_name="One")
        done.email_verified_at = timezone.now()
        done.save()
        RndProfile.objects.create(user=done, prc_license_number="1111111", review_status="pending")
        unfinished = User.objects.create_user(email="app2@d.ph", password="x", role="rnd", first_name="B", last_name="Two")
        RndProfile.objects.create(user=unfinished, prc_license_number="2222222", review_status="pending")

        apps = [a for a in self.api.get("/api/admin/dashboard/").data["attention"] if a["key"] == "applications"]
        self.assertEqual(apps[0]["count"], 1)
        self.assertEqual(self.api.get("/api/admin/platform-stats/").data["pending_verif"], 1)


class ScheduleTests(TestCase):
    """The banner's day timeline: today's consultations and the next one."""

    def test_today_and_next(self):
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        from core.admin_dashboard import _schedule
        from core.test_utils import approve_rnd, onboard_client
        from scheduling.models import Appointment, RndClientRelationship

        ph = ZoneInfo("Asia/Manila")
        now = datetime(2026, 10, 25, 11, 0, tzinfo=ph)
        rnd = approve_rnd(User.objects.create_user(email="r@s.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        c = onboard_client(User.objects.create_user(email="c@s.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        rel = RndClientRelationship.objects.create(rnd=rnd, client=c, status="active")
        mk = lambda h, status, day=25: Appointment.objects.create(relationship=rel, type="video", status=status,
                                                                  scheduled_at=datetime(2026, 10, day, h, tzinfo=ph))
        done, later = mk(9, "completed"), mk(15, "confirmed")
        mk(13, "cancelled")            # left out
        mk(10, "confirmed", day=26)    # tomorrow: not today
        s = _schedule(now)
        self.assertEqual([r["id"] for r in s["today"]], [done.id, later.id])
        self.assertEqual((s["next"]["id"], s["next"]["client"], s["next"]["paid"]), (later.id, "Ana Cruz", False))
        self.assertEqual(_schedule(now + timedelta(days=40))["next"], None)
