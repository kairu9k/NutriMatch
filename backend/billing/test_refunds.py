"""Checkout Sessions + refunds through PayMongo (2026-10-19). PayMongo is
mocked — no network calls. A refund-pending invoice only turns Refunded when
PayMongo reports a succeeded refund."""

import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from communication.models import NotificationLog
from core.models import AuditLog
from scheduling.models import RndClientRelationship

from .models import Invoice, PaymentTransaction
from .services import PaymentGatewayError

TEST_PAYMONGO = {
    "SECRET_KEY": "sk_test_fake", "WEBHOOK_SECRET": "whsec_fake",
    "BASE_URL": "https://api.paymongo.com/v1", "TIMEOUT": 30,
}


def _session(cs_id="cs_1", paid=True, source="gcash"):
    payments = [{"id": "pay_1", "type": "payment", "attributes": {
        "status": "paid", "amount": 80000, "source": {"type": source}, "livemode": False,
    }}] if paid else []
    return {"id": cs_id, "type": "checkout_session", "attributes": {"payments": payments}}


def _payment(refunds=(), source="gcash"):
    return {"id": "pay_1", "attributes": {
        "status": "paid", "amount": 80000, "livemode": False, "source": {"type": source},
        "refunds": [{"id": rid, "attributes": {"status": st, "amount": 80000, "created_at": 1792367103,
                                               "refunded_at": 1792367110 if st == "succeeded" else None,
                                               "transfer_link": None}} for rid, st in refunds],
    }}


def _resp(data, error=False):
    r = MagicMock()
    r.is_error = error
    r.json.return_value = data
    return r


@override_settings(PAYMONGO=TEST_PAYMONGO)
class CheckoutAndRefundTests(TestCase):
    def setUp(self):
        self.rnd = User.objects.create_user(email="r@ref.ph", password="x", role="rnd", first_name="R", last_name="D")
        self.client_user = User.objects.create_user(email="c@ref.ph", password="x", role="client", first_name="C", last_name="L")
        self.admin = User.objects.create_user(email="a@ref.ph", password="x", role="admin", first_name="A", last_name="D")
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.invoice = Invoice.objects.create(relationship=self.rel, amount=Decimal("800.00"),
                                              payment_gateway="paymongo", gateway_reference_id="cs_1")
        self.api = APIClient()

    def _paid_refund_pending(self, source="gcash"):
        PaymentTransaction.objects.create(invoice=self.invoice, transaction_type="payment", amount=Decimal("800"),
                                          status="success", gateway_payload=_session(source=source))
        Invoice.objects.filter(pk=self.invoice.pk).update(status="refund_pending", payment_method=source)

    # --- paying through a checkout session -------------------------------
    @patch("billing.services.httpx.Client")
    def test_sync_marks_a_paid_checkout_session(self, mock_cls):
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = _resp({"data": _session()})
        mock_cls.return_value = client
        self.api.force_authenticate(self.client_user)
        self.assertEqual(self.api.post("/api/client/invoices/sync/").data["updated"], [self.invoice.id])
        client.get.assert_called_with("https://api.paymongo.com/v1/checkout_sessions/cs_1")
        self.invoice.refresh_from_db()
        self.assertEqual((self.invoice.status, self.invoice.payment_method), ("paid", "gcash"))

    @patch("billing.services.httpx.Client")
    def test_sync_leaves_an_unpaid_session(self, mock_cls):
        client = MagicMock()
        client.__enter__.return_value = client
        client.get.return_value = _resp({"data": _session(paid=False)})
        mock_cls.return_value = client
        self.api.force_authenticate(self.client_user)
        self.assertEqual(self.api.post("/api/client/invoices/sync/").data["updated"], [])
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "unpaid")

    def test_checkout_session_webhook_marks_paid_with_receipt(self):
        payload = json.dumps({"data": {"attributes": {"type": "checkout_session.payment.paid", "data": _session()}}}).encode()
        ts = "1700000000"
        te = hmac.new(b"whsec_fake", f"{ts}.{payload.decode()}".encode(), hashlib.sha256).hexdigest()
        resp = self.api.post("/api/webhooks/paymongo/", data=payload, content_type="application/json",
                             HTTP_PAYMONGO_SIGNATURE=f"t={ts},te={te},li=x")
        self.assertEqual(resp.status_code, 200)
        self.invoice.refresh_from_db()
        self.assertEqual((self.invoice.status, self.invoice.payment_method), ("paid", "gcash"))
        self.api.force_authenticate(self.admin)
        detail = self.api.get(f"/api/admin/invoices/{self.invoice.id}/").data
        self.assertEqual(detail["transactions"][0]["receipt"]["payment_id"], "pay_1")
        self.assertEqual(detail["paymongo_payment_id"], "pay_1")

    # --- refunding through PayMongo ---------------------------------------
    @patch("billing.refunds.PayMongoService")
    def test_gcash_refund_succeeds_then_invoice_is_refunded(self, svc_cls):
        self._paid_refund_pending()
        svc = svc_cls.return_value
        svc.get_payment.side_effect = [_payment(), _payment([("ref_1", "succeeded")])]
        svc.create_refund.return_value = {"id": "ref_1", "attributes": {"status": "pending", "amount": 80000}}
        self.api.force_authenticate(self.admin)
        resp = self.api.post(f"/api/admin/invoices/{self.invoice.id}/refund/")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["invoice_status"], "refunded")
        svc.create_refund.assert_called_once_with("pay_1", 80000, "gcash", notes=f"NutriMatch INV-{self.invoice.id:04d}, consultation cancelled")
        refund_txn = PaymentTransaction.objects.get(invoice=self.invoice, transaction_type="refund")
        self.assertEqual(refund_txn.gateway_payload["reference"], "ref_1")
        self.assertTrue(AuditLog.objects.filter(action="invoice.refunded", record_id=self.invoice.id).exists())
        self.assertTrue(NotificationLog.objects.filter(recipient=self.client_user, subject="Refund completed").exists())

    @patch("billing.refunds.PayMongoService")
    def test_failed_refund_keeps_it_pending(self, svc_cls):
        self._paid_refund_pending(source="qrph")
        svc = svc_cls.return_value
        svc.get_payment.side_effect = [_payment(source="qrph"), _payment([("ref_q", "failed")], source="qrph")]
        svc.create_refund.return_value = {"id": "ref_q", "attributes": {"status": "failed", "amount": 80000}}
        self.api.force_authenticate(self.admin)
        resp = self.api.post(f"/api/admin/invoices/{self.invoice.id}/refund/")
        self.assertEqual(resp.data["invoice_status"], "refund_pending")
        self.assertEqual(resp.data["refunds"][0]["status"], "failed")
        self.assertFalse(PaymentTransaction.objects.filter(invoice=self.invoice, transaction_type="refund").exists())

    @patch("billing.refunds.PayMongoService")
    def test_no_second_refund_while_one_is_in_progress(self, svc_cls):
        self._paid_refund_pending()
        svc = svc_cls.return_value
        svc.get_payment.return_value = _payment([("ref_1", "pending")])
        self.api.force_authenticate(self.admin)
        resp = self.api.post(f"/api/admin/invoices/{self.invoice.id}/refund/")
        self.assertEqual(resp.data["invoice_status"], "refund_pending")
        svc.create_refund.assert_not_called()

    @patch("billing.refunds.PayMongoService")
    def test_paymongo_refusing_is_reported(self, svc_cls):
        self._paid_refund_pending()
        svc = svc_cls.return_value
        svc.get_payment.return_value = _payment()
        svc.create_refund.side_effect = PaymentGatewayError("Refunds are not allowed for payments with source type qrph.")
        self.api.force_authenticate(self.admin)
        resp = self.api.post(f"/api/admin/invoices/{self.invoice.id}/refund/")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("not allowed", resp.data["detail"])

    def test_refund_needs_a_paymongo_payment_and_admin(self):
        Invoice.objects.filter(pk=self.invoice.pk).update(status="refund_pending")
        self.api.force_authenticate(self.client_user)
        self.assertEqual(self.api.post(f"/api/admin/invoices/{self.invoice.id}/refund/").status_code, 403)
        self.api.force_authenticate(self.admin)
        resp = self.api.post(f"/api/admin/invoices/{self.invoice.id}/refund/")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("wasn't paid through PayMongo", resp.data["detail"])

    # --- "Mark as refunded" no longer trusts a click for PayMongo invoices --
    @patch("billing.refunds.PayMongoService")
    def test_mark_refunded_needs_paymongos_confirmation(self, svc_cls):
        self._paid_refund_pending()
        svc_cls.return_value.get_payment.return_value = _payment([("ref_x", "failed")])
        self.api.force_authenticate(self.admin)
        resp = self.api.post(f"/api/admin/invoices/{self.invoice.id}/mark-refunded/", {"reference": "trust me"}, format="json")
        self.assertEqual(resp.status_code, 409)
        self.assertIn("ref_x", resp.data["detail"])
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "refund_pending")

        svc_cls.return_value.get_payment.return_value = _payment([("ref_x", "failed"), ("ref_y", "succeeded")])
        self.assertEqual(self.api.post(f"/api/admin/invoices/{self.invoice.id}/mark-refunded/").status_code, 200)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "refunded")

    @patch("billing.refunds.PayMongoService")
    def test_check_with_paymongo_and_client_sync_pick_up_a_finished_refund(self, svc_cls):
        self._paid_refund_pending()
        svc_cls.return_value.get_payment.return_value = _payment([("ref_1", "pending")])
        self.api.force_authenticate(self.admin)
        state = self.api.get(f"/api/admin/invoices/{self.invoice.id}/paymongo/").data
        self.assertEqual((state["invoice_status"], state["in_progress"]), ("refund_pending", True))

        svc_cls.return_value.get_payment.return_value = _payment([("ref_1", "succeeded")])
        self.api.force_authenticate(self.client_user)
        self.assertIn(self.invoice.id, self.api.post("/api/client/invoices/sync/").data["updated"])
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "refunded")
