"""Platform report: period bounds and the figures for a period."""

from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship

from .reports import build_report, period_bounds

PH = ZoneInfo("Asia/Manila")


class ReportTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="a@r.ph", password="x", role="admin", first_name="Ada", last_name="Min")
        self.rnd = approve_rnd(User.objects.create_user(email="r@r.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        c = onboard_client(User.objects.create_user(email="c@r.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=c, status="active")

    def at(self, y, m, d):
        return datetime.combine(date(y, m, d), time(10), tzinfo=PH)

    def test_period_bounds(self):
        today = date(2026, 3, 15)
        self.assertEqual(period_bounds({"period": "this_month"}, today)[:2], (date(2026, 3, 1), today))
        self.assertEqual(period_bounds({"period": "last_month"}, today)[:2], (date(2026, 2, 1), date(2026, 2, 28)))
        self.assertEqual(period_bounds({"period": "last_3_months"}, today)[:2], (date(2026, 1, 1), today))
        self.assertEqual(period_bounds({"period": "this_year"}, date(2026, 1, 5))[:2], (date(2026, 1, 1), date(2026, 1, 5)))
        self.assertEqual(period_bounds({"from": "2026-02-10", "to": "2026-02-01"}, today)[:2], (date(2026, 2, 1), date(2026, 2, 10)))

    def test_figures_for_a_period(self):
        done = Appointment.objects.create(relationship=self.rel, type="video", status="completed",
                                          scheduled_at=self.at(2026, 2, 10), completed_at=self.at(2026, 2, 10))
        Appointment.objects.create(relationship=self.rel, type="chat", status="cancelled", scheduled_at=self.at(2026, 2, 12))
        Appointment.objects.create(relationship=self.rel, type="video", status="completed",
                                   scheduled_at=self.at(2026, 1, 5), completed_at=self.at(2026, 1, 5))  # outside
        Invoice.objects.create(relationship=self.rel, appointment=done, amount=Decimal("1000"), commission_amt=Decimal("100"),
                               status="paid", paid_at=self.at(2026, 2, 9))
        Invoice.objects.create(relationship=self.rel, amount=Decimal("800"), commission_amt=Decimal("80"),
                               status="refund_pending", paid_at=self.at(2026, 2, 11))
        r = build_report({"from": "2026-02-01", "to": "2026-02-28"})
        self.assertEqual((r["consultations"]["completed"], r["consultations"]["cancelled"]), (1, 1))
        self.assertEqual(r["consultations"]["by_format"], {"Video": 1})
        self.assertEqual((r["money"]["payments"], r["money"]["gross"], r["money"]["commission"], r["money"]["rnd_share"]), (2, 1800.0, 100.0, 900.0))  # the refund-pending 800 earns no commission or share
        self.assertEqual(r["money"]["refund_pending"], {"count": 1, "amount": 800.0})
        self.assertEqual(r["monthly"], [{"month": "2026-02", "completed": 1, "cancelled": 1, "payments": 2, "gross": 1800.0,
                                         "commission": 100.0, "rnd_share": 900.0, "new_clients": 0, "applications": 0}])
        self.assertEqual(r["rnds"][0]["consultations"], 1)
        self.assertEqual(r["rnds"][0]["rnd_share"], 900.0)

    def test_endpoint_admin_only(self):
        api = APIClient()
        api.force_authenticate(self.admin)
        self.assertEqual(api.get("/api/admin/reports/", {"period": "all"}).status_code, 200)
        self.assertEqual(api.get("/api/admin/reports/", {"from": "nope", "to": "2026-01-01"}).status_code, 400)
        api.force_authenticate(self.rnd)
        self.assertEqual(api.get("/api/admin/reports/").status_code, 403)


class ReportTabTests(TestCase):
    """The Clients / RNDs / Consultations / Money tab figures."""

    def setUp(self):
        from django.utils import timezone

        self.now = timezone.now()
        self.rnd = approve_rnd(User.objects.create_user(email="r2@r.ph", password="x", role="rnd", first_name="Lara", last_name="M"))
        self.c1 = onboard_client(User.objects.create_user(email="c1@r.ph", password="x", role="client", first_name="A", last_name="One"))
        self.c2 = onboard_client(User.objects.create_user(email="c2@r.ph", password="x", role="client", first_name="B", last_name="Two"))
        self.r1 = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c1, status="active")
        self.r2 = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c2, status="active")

    def done(self, rel, days_ago):
        from datetime import timedelta

        when = self.now - timedelta(days=days_ago)
        return Appointment.objects.create(relationship=rel, type="video", status="completed", scheduled_at=when, completed_at=when)

    def test_clients_and_reasons(self):
        from datetime import timedelta

        from billing.services import NOT_PAID_REASON

        # c1 signed up 10 days ago and has had two consultations, c2 one
        User.objects.filter(pk=self.c1.pk).update(created_at=self.now - timedelta(days=10))
        User.objects.filter(pk=self.c2.pk).update(created_at=self.now - timedelta(days=4))
        self.done(self.r1, 6)
        self.done(self.r1, 2)
        self.done(self.r2, 2)
        for why in ("No-show: never joined", NOT_PAID_REASON, "Something came up"):
            Appointment.objects.create(relationship=self.r2, type="video", status="cancelled",
                                       scheduled_at=self.now - timedelta(days=1), cancellation_reason=why)
        r = build_report({"period": "this_year"})
        c = r["clients"]
        self.assertEqual(c["consulted"], 2)
        self.assertEqual(c["repeat_pct"], 50)              # 1 of 2 came back
        self.assertEqual(c["days_to_first_median"], 3)      # median of 4 days (c1) and 2 days (c2)
        self.assertEqual(c["in_care_now"], 2)
        self.assertEqual(r["consultations"]["cancelled_reasons"], {"no_show": 1, "not_paid": 1, "other": 1})
        self.assertEqual(r["rnd_stats"]["active"], 1)
        self.assertEqual(r["rnd_stats"]["patients_per_rnd"], 2.0)

    def test_every_month_listed(self):
        r = build_report({"from": "2026-01-01", "to": "2026-04-30"})
        self.assertEqual([m["month"] for m in r["monthly"]], ["2026-01", "2026-02", "2026-03", "2026-04"])
