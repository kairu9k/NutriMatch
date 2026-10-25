"""Payouts sent through Xendit (billing/xendit.py, payouts.send_payout_via_xendit).
Xendit itself is mocked: no network calls."""

from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from communication.models import NotificationLog
from core.models import AuditLog
from core.ph_time import ph_today
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship

from . import xendit
from .models import Invoice, Payout, RndPayoutAccount
from .payouts import last_payout_day

XENDIT = override_settings(XENDIT_SECRET_KEY="xnd_development_test", XENDIT_CALLBACK_TOKEN="cb-token")


@XENDIT
class XenditPayoutTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="rnd@x.ph", password="x", role="rnd", first_name="Lara", last_name="M"))
        client = onboard_client(User.objects.create_user(email="c@x.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=client, status="active")
        self.admin = User.objects.create_user(email="admin@x.ph", password="x", role="admin", first_name="A", last_name="D")
        self.api = APIClient()
        self.api.force_authenticate(self.admin)
        RndPayoutAccount.objects.create(rnd=self.rnd, method="gcash", account_name="Lara M", account_number="09181112222")
        days = (ph_today() - last_payout_day()).days + 5  # cleared before the last 5th
        appt = Appointment.objects.create(relationship=self.rel, type="video", status="completed",
                                          scheduled_at=timezone.now() - timedelta(days=days, hours=1),
                                          completed_at=timezone.now() - timedelta(days=days))
        self.invoice = Invoice.objects.create(relationship=self.rel, appointment=appt, amount=Decimal("800"),
                                              commission_pct=Decimal("10"), status="paid", paid_at=timezone.now())

    def _send(self, amount="720.00"):
        return self.api.post(f"/api/admin/payouts/release/{self.rnd.id}/",
                             {"via": "xendit", "expected_amount": amount, "details_confirmed": False}, format="json")

    def _row(self):
        return next(r for r in self.api.get("/api/admin/payouts/run/").data["rows"] if r["rnd_id"] == self.rnd.id)

    def test_sent_and_succeeded_right_away(self):
        with mock.patch.object(xendit, "create_payout", return_value={"id": "disb-123", "status": "SUCCEEDED"}) as create:
            resp = self._send()
        self.assertEqual(resp.status_code, 201, resp.data)
        payout = Payout.objects.get()
        self.assertEqual((payout.status, payout.provider, payout.reference, payout.test_mode), ("paid", "xendit", "disb-123", True))
        kwargs = create.call_args.kwargs
        self.assertEqual((kwargs["channel_code"], kwargs["account_number"], kwargs["amount"]), ("PH_GCASH", "09181112222", Decimal("720.00")))
        self.assertEqual(kwargs["idempotency_key"], f"nutrimatch-payout-{payout.id}")  # a retry can't send twice
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.payout_id, payout.id)
        self.assertTrue(NotificationLog.objects.filter(recipient=self.rnd, notifiable_type="payout").exists())
        self.assertTrue(AuditLog.objects.filter(action="payout.sent").exists())
        self.assertTrue(AuditLog.objects.filter(action="payout.released").exists())

    def test_sending_until_xendit_confirms(self):
        with mock.patch.object(xendit, "create_payout", return_value={"id": "disb-9", "status": "ACCEPTED"}):
            self.assertEqual(self._send().status_code, 201)
        payout = Payout.objects.get()
        self.assertEqual(payout.status, "sending")
        self.assertFalse(NotificationLog.objects.filter(recipient=self.rnd, notifiable_type="payout").exists())
        self.assertEqual(self._send().status_code, 400)  # the same money can't be sent again meanwhile
        with mock.patch.object(xendit, "get_payout", return_value={"id": "disb-9", "status": "SUCCEEDED"}):
            self.api.get("/api/admin/payouts/")  # opening Payouts asks Xendit
        payout.refresh_from_db()
        self.assertEqual(payout.status, "paid")
        self.assertTrue(NotificationLog.objects.filter(recipient=self.rnd, notifiable_type="payout").exists())

    def test_refused_by_xendit_releases_the_money(self):
        with mock.patch.object(xendit, "create_payout", side_effect=xendit.XenditError("Xendit refused the payout: bad account.")):
            resp = self._send()
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Nothing was sent", resp.data["detail"])
        payout = Payout.objects.get()
        self.assertEqual((payout.status, payout.failure_code), ("failed", "NOT_SENT"))
        self.invoice.refresh_from_db()
        self.assertIsNone(self.invoice.payout_id)
        self.assertTrue(self._row()["eligible"])  # ready to try again

    def test_failed_later_releases_the_money(self):
        with mock.patch.object(xendit, "create_payout", return_value={"id": "disb-7", "status": "ACCEPTED"}):
            self._send()
        with mock.patch.object(xendit, "get_payout", return_value={"id": "disb-7", "status": "FAILED", "failure_code": "INVALID_DESTINATION"}):
            resp = self.api.post(f"/api/admin/payouts/{Payout.objects.get().id}/check/")
        self.assertEqual(resp.data["status"], "failed")
        self.assertEqual(resp.data["failure_code"], "INVALID_DESTINATION")
        self.invoice.refresh_from_db()
        self.assertIsNone(self.invoice.payout_id)
        self.assertTrue(AuditLog.objects.filter(action="payout.failed").exists())

    def test_callback_needs_the_token_and_reads_the_status_back(self):
        with mock.patch.object(xendit, "create_payout", return_value={"id": "disb-5", "status": "ACCEPTED"}):
            self._send()
        anon = APIClient()
        self.assertEqual(anon.post("/api/webhooks/xendit/payouts/", {"data": {"id": "disb-5", "status": "SUCCEEDED"}}, format="json").status_code, 401)
        with mock.patch.object(xendit, "get_payout", return_value={"id": "disb-5", "status": "SUCCEEDED"}) as get:
            resp = anon.post("/api/webhooks/xendit/payouts/", {"data": {"id": "disb-5", "status": "SUCCEEDED"}},
                             format="json", HTTP_X_CALLBACK_TOKEN="cb-token")
        self.assertEqual(resp.status_code, 200)
        get.assert_called_once_with("disb-5")
        self.assertEqual(Payout.objects.get().status, "paid")

    def test_unsupported_destination_is_refused(self):
        RndPayoutAccount.objects.filter(rnd=self.rnd).update(method="bank", bank_name="Bank of Nowhere", account_number="001234567890")
        with mock.patch.object(xendit, "channels", return_value=[]):
            resp = self._send()
        self.assertEqual(resp.status_code, 400)
        self.assertIn("record it by hand", resp.data["detail"])
        self.assertFalse(Payout.objects.exists())

    @override_settings(XENDIT_SECRET_KEY="")
    def test_not_set_up(self):
        resp = self._send()
        self.assertIn("isn't set up", resp.data["detail"])
        self.assertFalse(self._row()["xendit_ok"])
