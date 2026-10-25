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
from .payouts import last_payout_day, next_payout_date


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

    def _before_run(self, days=5):
        """How many days ago a consultation must have been completed so its
        share posted `days` days before the last payout day (in this run)."""
        from core.ph_time import ph_today

        return (ph_today() - last_payout_day()).days + days

    def _release(self, amount, reference="1023 456 789012", confirmed=True):
        """Record a payout the way the page does: the amount the admin saw,
        the receipt reference, and the confirmation for new details."""
        return self.admin_api.post(f"/api/admin/payouts/release/{self.rnd.id}/", {
            "reference": reference, "expected_amount": str(amount), "details_confirmed": confirmed,
        }, format="json")

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

    def test_payout_account_wallets_and_banks(self):
        put = lambda body: self.rnd_api.put("/api/rnd/payout-account/", {"account_name": "Maria Santos", **body}, format="json")
        maya = put({"method": "maya", "account_number": "0918 765 4321"})
        self.assertEqual(maya.status_code, 200, maya.data)
        self.assertEqual((maya.data["account_number"], maya.data["bank_name"]), ("09187654321", None))
        self.assertIn("Maya", str(put({"method": "maya", "account_number": "12345"}).data["account_number"]))
        gotyme = put({"method": "gotyme", "account_number": "012345678901"})
        self.assertEqual(gotyme.status_code, 200, gotyme.data)
        self.assertEqual(put({"method": "maribank", "account_number": "abc"}).status_code, 400)
        bank = put({"method": "bank", "account_number": "001234567890", "bank_name": "BDO Unibank"})
        self.assertEqual((bank.status_code, bank.data["bank_name"]), (200, "BDO Unibank"))
        self.assertEqual(put({"method": "paypal", "account_number": "09171234567"}).status_code, 400)

    def test_payout_destination_labels(self):
        from billing.models import payout_destination
        self.assertEqual(payout_destination("maya"), "Maya")
        self.assertEqual(payout_destination("gotyme"), "GoTyme")
        self.assertEqual(payout_destination("bank", "BPI"), "BPI")
        self.assertEqual(payout_destination("bank"), "Bank transfer")

    def test_last_payout_day(self):
        self.assertEqual(last_payout_day(date(2026, 10, 26)), date(2026, 10, 5))
        self.assertEqual(last_payout_day(date(2026, 10, 5)), date(2026, 10, 5))
        self.assertEqual(last_payout_day(date(2026, 10, 4)), date(2026, 9, 5))
        self.assertEqual(last_payout_day(date(2027, 1, 2)), date(2026, 12, 5))

    def test_release_rules_and_paid_once(self):
        first = self._consult(completed_days_ago=self._before_run(10))
        self._consult(completed_days_ago=self._before_run(8))  # posted total 1,440
        self.assertIn("payout details", self._release("1440.00").data["detail"])
        self._add_gcash()
        self.assertEqual(self._release("1440.00", reference="").status_code, 400)
        run = self.admin_api.get("/api/admin/payouts/run/").data
        row = next(r for r in run["rows"] if r["rnd_id"] == self.rnd.id)
        self.assertTrue(row["eligible"])
        self.assertEqual(row["payout_account"]["account_number"], "09171234567")

        resp = self._release("1440.00")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(Decimal(resp.data["amount"]), Decimal("1440.00"))
        self.assertEqual(Payout.objects.get().payout_date, last_payout_day())  # dated to its run
        first.refresh_from_db()
        self.assertIsNotNone(first.payout_id)
        self.assertEqual(PaymentTransaction.objects.filter(transaction_type="payout").count(), 2)
        self.assertTrue(AuditLog.objects.filter(action="payout.released", user=self.admin).exists())
        self.assertIn("₱1,440.00", mail.outbox[-1].subject)
        # nothing left to pay — the same invoices are never paid twice
        again = self._release("1440.00", reference="9988 776 655443")
        self.assertEqual(again.status_code, 400)
        self.assertEqual(Payout.objects.count(), 1)
        data = self.rnd_api.get("/api/rnd/earnings/").data
        self.assertEqual((data["posted"], data["paid_out"]), (Decimal("0.00"), Decimal("1440.00")))
        self.assertEqual(len(data["payouts"]), 1)

    def test_minimum_payout_carries_over(self):
        self._add_gcash()
        self._consult(amount="300.00", completed_days_ago=self._before_run())  # 270 posted < 500
        resp = self._release("270.00")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("minimum", resp.data["detail"])
        row = next(r for r in self.admin_api.get("/api/admin/payouts/run/").data["rows"] if r["rnd_id"] == self.rnd.id)
        self.assertFalse(row["eligible"])
        self.assertIn("minimum", row["reason"])

    def test_refund_pending_invoice_is_never_paid_out(self):
        self._add_gcash()
        inv = self._consult(completed_days_ago=self._before_run())
        Invoice.objects.filter(pk=inv.pk).update(status="refund_pending")
        self._consult(completed_days_ago=self._before_run())
        resp = self._release("720.00")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(Decimal(resp.data["amount"]), Decimal("720.00"))

    def test_money_posted_after_the_payout_day_waits_for_the_next_run(self):
        """No early payouts (user's rule, 2026-10-26): on Oct 26 only what
        posted by Oct 5 is paid; what posted after waits for Nov 5."""
        from datetime import datetime, timezone as dt_tz
        from unittest import mock

        fixed = datetime(2026, 10, 26, 4, 0, tzinfo=dt_tz.utc)  # noon in the Philippines
        with mock.patch("django.utils.timezone.now", return_value=fixed):
            self._add_gcash()
            in_run = self._consult(completed_days_ago=28)                 # posted Oct 1
            later = self._consult(amount="2000.00", completed_days_ago=11)  # posted Oct 18
            row = next(r for r in self.admin_api.get("/api/admin/payouts/run/").data["rows"] if r["rnd_id"] == self.rnd.id)
            self.assertEqual((Decimal(row["posted"]), Decimal(row["payable"])), (Decimal("2520.00"), Decimal("720.00")))
            resp = self._release("720.00")
            self.assertEqual(resp.status_code, 201, resp.data)
            self.assertEqual(Decimal(resp.data["amount"]), Decimal("720.00"))
            self.assertEqual(Payout.objects.get().payout_date, date(2026, 10, 5))
            later.refresh_from_db()
            self.assertIsNone(later.payout_id)
            again = self._release("720.00", reference="5566 778 899001")
            self.assertEqual(again.status_code, 400)
            self.assertIn("paid on November 5", again.data["detail"])
            row = next(r for r in self.admin_api.get("/api/admin/payouts/run/").data["rows"] if r["rnd_id"] == self.rnd.id)
            self.assertFalse(row["eligible"])
            self.assertEqual(row["reason"], "Cleared after Oct 5, paid on Nov 5")
        in_run.refresh_from_db()
        self.assertIsNotNone(in_run.payout_id)

    def test_admin_payout_slip(self):
        self._add_gcash()
        inv = self._consult(completed_days_ago=self._before_run())
        payout_id = self._release("720.00").data["id"]
        slip = self.admin_api.get(f"/api/admin/payouts/{payout_id}/").data
        self.assertEqual((slip["reference"], slip["invoices"][0]["invoice_id"]), ("1023 456 789012", inv.id))
        self.assertEqual(Decimal(slip["invoices"][0]["share"]), Decimal("720.00"))
        self.assertEqual(self.rnd_api.get(f"/api/admin/payouts/{payout_id}/").status_code, 403)

    def test_amount_must_match_what_the_admin_saw(self):
        self._add_gcash()
        self._consult(completed_days_ago=self._before_run())  # 720
        resp = self._release("1440.00")  # the page showed an older amount
        self.assertEqual(resp.status_code, 400)
        self.assertIn("amount changed to ₱720.00", resp.data["detail"])
        self.assertIn("Nothing was recorded", resp.data["detail"])
        no_amount = self.admin_api.post(f"/api/admin/payouts/release/{self.rnd.id}/",
                                        {"reference": "1023 456 789012", "details_confirmed": True}, format="json")
        self.assertEqual(no_amount.status_code, 400)
        self.assertFalse(Payout.objects.exists())
        self.assertEqual(self._release("720.00").status_code, 201)

    def test_reference_must_be_a_real_receipt_number(self):
        self._add_gcash()
        self._consult(completed_days_ago=self._before_run())
        short = self._release("720.00", reference="GC-1")
        self.assertIn("too short", short.data["detail"])
        number = self._release("720.00", reference="0917 123 4567")  # the RND's own GCash number
        self.assertIn("account number", number.data["detail"])
        self.assertFalse(Payout.objects.exists())
        self.assertEqual(self._release("720.00", reference="1023 456 789012").status_code, 201)

    def test_recently_changed_details_need_confirming(self):
        self._consult(completed_days_ago=self._before_run())
        self._add_gcash()  # new details: changed just now
        row = next(r for r in self.admin_api.get("/api/admin/payouts/run/").data["rows"] if r["rnd_id"] == self.rnd.id)
        self.assertTrue(row["payout_account"]["recently_changed"])
        resp = self._release("720.00", confirmed=False)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("changed in the last 7 days", resp.data["detail"])
        # saving the same details again is not a change; a week later the warning is gone
        account = RndPayoutAccount.objects.get(rnd=self.rnd)
        RndPayoutAccount.objects.filter(pk=account.pk).update(details_changed_at=timezone.now() - timedelta(days=8))
        self._add_gcash()
        account.refresh_from_db()
        self.assertLess(account.details_changed_at, timezone.now() - timedelta(days=7))
        self.assertEqual(self._release("720.00", confirmed=False).status_code, 201)

    def test_changing_the_number_stamps_the_change(self):
        self._add_gcash()
        RndPayoutAccount.objects.filter(rnd=self.rnd).update(details_changed_at=timezone.now() - timedelta(days=30))
        self.rnd_api.put("/api/rnd/payout-account/", {
            "method": "gcash", "account_name": "Maria Santos", "account_number": "0918 000 1111",
        }, format="json")
        account = RndPayoutAccount.objects.get(rnd=self.rnd)
        self.assertGreater(account.details_changed_at, timezone.now() - timedelta(minutes=1))
        self.assertTrue(AuditLog.objects.filter(action="payout_account.updated", new_values__details_changed=True).exists())

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
