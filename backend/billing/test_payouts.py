"""Monthly RND payouts: Pending → Posted (3-day hold) → Paid out, ₱500
minimum, payout details required, each invoice paid once."""

from datetime import date, timedelta
from decimal import Decimal

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.models import AuditLog
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship

from .models import Invoice, PaymentTransaction, Payout, RndPayoutAccount
from .payouts import next_payout_date


class PayoutTests(TestCase):
    def setUp(self):
        mail.outbox = []
        self.rnd = approve_rnd(User.objects.create_user(email="rnd@p.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.client_user = onboard_client(User.objects.create_user(email="c@p.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.admin = User.objects.create_user(email="admin@p.ph", password="x", role="admin", first_name="A", last_name="D")
        self.rnd_api = APIClient()
        self.rnd_api.force_authenticate(self.rnd)
        self.admin_api = APIClient()
        self.admin_api.force_authenticate(self.admin)

    def _consult(self, amount="800.00", completed_days_ago=5, status="completed", paid=True):
        appt = Appointment.objects.create(
            relationship=self.rel, type="video", status=status,
            scheduled_at=timezone.now() - timedelta(days=completed_days_ago or 0, hours=1),
            completed_at=(timezone.now() - timedelta(days=completed_days_ago)) if status == "completed" else None,
        )
        return Invoice.objects.create(
            relationship=self.rel, appointment=appt, amount=Decimal(amount), commission_pct=Decimal("10.00"),
            status="paid" if paid else "unpaid", paid_at=timezone.now() if paid else None,
        )

    def _add_gcash(self):
        return self.rnd_api.put("/api/rnd/payout-account/", {
            "method": "gcash", "account_name": "Maria Santos", "account_number": "0917 123 4567",
        }, format="json")

    def test_next_payout_date_is_the_5th(self):
        self.assertEqual(next_payout_date(date(2026, 10, 3)), date(2026, 10, 5))
        self.assertEqual(next_payout_date(date(2026, 10, 5)), date(2026, 10, 5))
        self.assertEqual(next_payout_date(date(2026, 10, 6)), date(2026, 11, 5))
        self.assertEqual(next_payout_date(date(2026, 12, 20)), date(2027, 1, 5))

    def test_pending_posted_and_ignored(self):
        self._consult(completed_days_ago=5)            # posted: 720
        self._consult(completed_days_ago=1)            # pending: still on hold
        self._consult(status="confirmed", completed_days_ago=None)  # pending: paid, not completed
        self._consult(paid=False)                      # not counted
        data = self.rnd_api.get("/api/rnd/earnings/").data
        self.assertEqual(data["posted"], Decimal("720.00"))
        self.assertEqual(data["pending"], Decimal("1440.00"))
        self.assertEqual(data["paid_out"], Decimal("0.00"))
        self.assertFalse(data["has_payout_account"])
        self.assertTrue(any(i["posts_on"] for i in data["items"] if i["state"] == "pending"))

    def test_payout_account_validation(self):
        bad = self.rnd_api.put("/api/rnd/payout-account/", {"method": "gcash", "account_name": "M", "account_number": "123"}, format="json")
        self.assertEqual(bad.status_code, 400)
        no_bank = self.rnd_api.put("/api/rnd/payout-account/", {"method": "bank", "account_name": "Maria", "account_number": "001234567"}, format="json")
        self.assertIn("bank_name", no_bank.data)
        ok = self._add_gcash()
        self.assertEqual(ok.status_code, 200, ok.data)
        self.assertEqual(ok.data["account_number"], "09171234567")

    def test_release_rules_and_paid_once(self):
        first = self._consult(completed_days_ago=10)
        self._consult(completed_days_ago=8)  # posted total 1,440
        url = f"/api/admin/payouts/release/{self.rnd.id}/"
        self.assertIn("payout details", self.admin_api.post(url, {"reference": "GC-1"}, format="json").data["detail"])
        self._add_gcash()
        self.assertEqual(self.admin_api.post(url, {"reference": ""}, format="json").status_code, 400)
        run = self.admin_api.get("/api/admin/payouts/run/").data
        row = next(r for r in run["rows"] if r["rnd_id"] == self.rnd.id)
        self.assertTrue(row["eligible"])
        self.assertEqual(row["payout_account"]["account_number"], "09171234567")

        resp = self.admin_api.post(url, {"reference": "GC-2026-11-05"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(Decimal(resp.data["amount"]), Decimal("1440.00"))
        first.refresh_from_db()
        self.assertIsNotNone(first.payout_id)
        self.assertEqual(PaymentTransaction.objects.filter(transaction_type="payout").count(), 2)
        self.assertTrue(AuditLog.objects.filter(action="payout.released", user=self.admin).exists())
        self.assertIn("₱1,440.00", mail.outbox[-1].subject)
        # nothing left to pay — the same invoices are never paid twice
        again = self.admin_api.post(url, {"reference": "GC-again"}, format="json")
        self.assertEqual(again.status_code, 400)
        self.assertEqual(Payout.objects.count(), 1)
        data = self.rnd_api.get("/api/rnd/earnings/").data
        self.assertEqual((data["posted"], data["paid_out"]), (Decimal("0.00"), Decimal("1440.00")))
        self.assertEqual(len(data["payouts"]), 1)

    def test_minimum_payout_carries_over(self):
        self._add_gcash()
        self._consult(amount="300.00", completed_days_ago=6)  # 270 posted < 500
        resp = self.admin_api.post(f"/api/admin/payouts/release/{self.rnd.id}/", {"reference": "GC-3"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("minimum", resp.data["detail"])
        row = next(r for r in self.admin_api.get("/api/admin/payouts/run/").data["rows"] if r["rnd_id"] == self.rnd.id)
        self.assertFalse(row["eligible"])
        self.assertIn("minimum", row["reason"])

    def test_refund_pending_invoice_is_never_paid_out(self):
        self._add_gcash()
        inv = self._consult(completed_days_ago=6)
        Invoice.objects.filter(pk=inv.pk).update(status="refund_pending")
        self._consult(completed_days_ago=6)
        resp = self.admin_api.post(f"/api/admin/payouts/release/{self.rnd.id}/", {"reference": "GC-4"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(Decimal(resp.data["amount"]), Decimal("720.00"))

    def test_completing_starts_the_hold(self):
        appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=timezone.now() - timedelta(hours=2))
        Invoice.objects.create(relationship=self.rel, appointment=appt, amount=Decimal("800"), status="paid", paid_at=timezone.now())
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{appt.id}/complete/").status_code, 200)
        appt.refresh_from_db()
        self.assertIsNotNone(appt.completed_at)
        self.assertEqual(self.rnd_api.get("/api/rnd/earnings/").data["items"][0]["state"], "pending")

    def test_only_admins_and_the_owner(self):
        client_api = APIClient()
        client_api.force_authenticate(self.client_user)
        self.assertEqual(client_api.get("/api/admin/payouts/run/").status_code, 403)
        self.assertEqual(self.rnd_api.post(f"/api/admin/payouts/release/{self.rnd.id}/", {"reference": "x"}).status_code, 403)
        self.assertEqual(client_api.get("/api/rnd/earnings/").status_code, 403)
        self.assertFalse(RndPayoutAccount.objects.exists())
