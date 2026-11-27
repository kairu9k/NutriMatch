"""Client payments and refunds through Xendit (billing/xendit.py, 2026-11-27). Xendit is mocked:
no network calls. An invoice is paid only when Xendit's API says so (the callback body is never
trusted), and refunded only when Xendit reports a succeeded refund."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from scheduling.models import Appointment, RndClientRelationship

from .models import Invoice, PaymentTransaction

XENDIT = {"XENDIT_SECRET_KEY": "xnd_development_fake", "XENDIT_CALLBACK_TOKEN": "cb_token_fake",
          "PAYMENT_PROVIDER": "xendit", "FRONTEND_URL": "https://app.example"}


def _xinv(status="PAID", channel="GCASH", method="EWALLET"):
    return {"id": "xinv_1", "external_id": "INV-0001", "status": status, "amount": 800, "paid_amount": 800,
            "currency": "PHP", "payment_method": method, "payment_channel": channel,
            "paid_at": "2026-11-27T05:00:00.000Z", "payer_email": "c@x.ph", "fees_paid_amount": 18,
            "adjusted_received_amount": 782, "invoice_url": "https://checkout-staging.xendit.co/web/xinv_1"}


def _resp(data, error=False):
    r = MagicMock()
    r.is_error = error
    r.json.return_value = data
    return r


class _Xendit:
    """A fake Xendit: answers by method + path, records what was sent."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        answer = self.routes[(method, path)]
        return answer.pop(0) if isinstance(answer, list) else answer


def _install(mock_cls, routes):
    fake = _Xendit(routes)
    client = MagicMock()
    client.__enter__.return_value = client
    client.request.side_effect = fake.request
    mock_cls.return_value = client
    return fake


@override_settings(**XENDIT)
class XenditPaymentTests(TestCase):
    def setUp(self):
        self.rnd = User.objects.create_user(email="r@xen.ph", password="x", role="rnd", first_name="R", last_name="D")
        self.client_user = User.objects.create_user(email="c@xen.ph", password="x", role="client", first_name="C", last_name="L")
        self.admin = User.objects.create_user(email="a@xen.ph", password="x", role="admin", first_name="A", last_name="D")
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", duration_minutes=60,
                                               scheduled_at=timezone.now() + timezone.timedelta(hours=3))
        self.invoice = Invoice.objects.create(relationship=self.rel, appointment=self.appt, amount=Decimal("800.00"))
        self.api = APIClient()

    def _started(self):
        Invoice.objects.filter(pk=self.invoice.pk).update(payment_gateway="xendit", gateway_reference_id="xinv_1")

    @patch("billing.xendit.httpx.Client")
    def test_pay_opens_a_xendit_invoice_until_the_pay_by_time(self, mock_cls):
        fake = _install(mock_cls, {("POST", "/v2/invoices"): _resp({"id": "xinv_1", "invoice_url": "https://pay/xinv_1"})})
        self.api.force_authenticate(self.client_user)
        resp = self.api.post(f"/api/client/invoices/{self.invoice.id}/pay/")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["payment_url"], "https://pay/xinv_1")
        body = fake.calls[0][2]["json"]
        self.assertEqual((body["external_id"], body["amount"], body["currency"]), (f"INV-{self.invoice.id:04d}", 800.0, "PHP"))
        self.assertNotIn("QRPH", body["payment_methods"])  # Xendit can't refund QR Ph
        # Expires at the pay-by time (15 min before the 3-hour-away start), not later.
        self.assertLessEqual(body["invoice_duration"], 3 * 3600 - 15 * 60)
        self.assertGreater(body["invoice_duration"], 3 * 3600 - 16 * 60)
        self.invoice.refresh_from_db()
        self.assertEqual((self.invoice.payment_gateway, self.invoice.gateway_reference_id), ("xendit", "xinv_1"))
        self.assertEqual(self.invoice.status, "unpaid")

    @patch("billing.xendit.httpx.Client")
    def test_xendit_down_is_a_502_and_nothing_changes(self, mock_cls):
        _install(mock_cls, {("POST", "/v2/invoices"): _resp({"message": "Something broke"}, error=True)})
        self.api.force_authenticate(self.client_user)
        resp = self.api.post(f"/api/client/invoices/{self.invoice.id}/pay/")
        self.assertEqual(resp.status_code, 502)
        self.invoice.refresh_from_db()
        self.assertIsNone(self.invoice.gateway_reference_id)

    @patch("billing.xendit.httpx.Client")
    def test_sync_marks_paid_with_the_method_and_receipt(self, mock_cls):
        self._started()
        _install(mock_cls, {("GET", "/v2/invoices/xinv_1"): _resp(_xinv())})
        self.api.force_authenticate(self.client_user)
        self.assertEqual(self.api.post("/api/client/invoices/sync/").data["updated"], [self.invoice.id])
        self.invoice.refresh_from_db()
        self.assertEqual((self.invoice.status, self.invoice.payment_method), ("paid", "gcash"))

        self.api.force_authenticate(self.admin)
        detail = self.api.get(f"/api/admin/invoices/{self.invoice.id}/").data
        self.assertEqual(detail["gateway_payment_id"], "xinv_1")
        receipt = detail["transactions"][0]["receipt"]
        self.assertEqual((receipt["amount"], receipt["fee"], receipt["source_type"], receipt["livemode"]),
                         ("800", "18", "gcash", False))

    @patch("billing.xendit.httpx.Client")
    def test_sync_leaves_a_pending_invoice(self, mock_cls):
        self._started()
        _install(mock_cls, {("GET", "/v2/invoices/xinv_1"): _resp(_xinv(status="PENDING", channel=None, method=None))})
        self.api.force_authenticate(self.client_user)
        self.assertEqual(self.api.post("/api/client/invoices/sync/").data["updated"], [])
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "unpaid")

    @patch("billing.xendit.httpx.Client")
    def test_callback_needs_the_token_and_is_checked_with_xendit(self, mock_cls):
        self._started()
        _install(mock_cls, {("GET", "/v2/invoices/xinv_1"): [_resp(_xinv(status="PENDING")), _resp(_xinv())]})
        url = "/api/webhooks/xendit/"
        self.assertEqual(self.api.post(url, {"id": "xinv_1", "status": "PAID"}, format="json").status_code, 401)
        self.assertEqual(self.api.post(url, {"id": "xinv_1", "status": "PAID"}, format="json",
                                       HTTP_X_CALLBACK_TOKEN="wrong").status_code, 401)
        # The body says PAID but Xendit's API says PENDING: nothing is recorded.
        self.assertEqual(self.api.post(url, {"id": "xinv_1", "status": "PAID"}, format="json",
                                       HTTP_X_CALLBACK_TOKEN="cb_token_fake").status_code, 200)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "unpaid")
        # Now Xendit's API says PAID.
        self.api.post(url, {"id": "xinv_1", "status": "PAID"}, format="json", HTTP_X_CALLBACK_TOKEN="cb_token_fake")
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "paid")
        self.assertEqual(PaymentTransaction.objects.filter(invoice=self.invoice, transaction_type="payment").count(), 1)

    def test_callback_for_an_unknown_invoice_is_acknowledged(self):
        resp = self.api.post("/api/webhooks/xendit/", {"id": "nope"}, format="json", HTTP_X_CALLBACK_TOKEN="cb_token_fake")
        self.assertEqual(resp.status_code, 200)

    # --- refunds -----------------------------------------------------------
    def _paid_refund_pending(self):
        from .xendit import stored_payload

        self._started()
        PaymentTransaction.objects.create(invoice=self.invoice, transaction_type="payment", amount=Decimal("800"),
                                          status="success", gateway_payload=stored_payload(_xinv()))
        Invoice.objects.filter(pk=self.invoice.pk).update(status="refund_pending", payment_method="gcash")

    @patch("billing.xendit.httpx.Client")
    def test_refund_goes_back_through_xendit(self, mock_cls):
        self._paid_refund_pending()
        done = {"id": "rfd_1", "status": "SUCCEEDED", "amount": 800, "created": "2026-11-27T06:00:00Z"}
        fake = _install(mock_cls, {
            ("GET", "/v2/invoices/xinv_1"): _resp(_xinv()),
            ("GET", "/refunds"): [_resp({"data": []}), _resp({"data": [done]})],
            ("POST", "/refunds"): _resp(done),
        })
        self.api.force_authenticate(self.admin)
        resp = self.api.post(f"/api/admin/invoices/{self.invoice.id}/refund/")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["invoice_status"], "refunded")
        self.assertEqual(resp.data["provider"], "xendit")
        sent = [c for c in fake.calls if c[0] == "POST"][0][2]["json"]
        self.assertEqual((sent["invoice_id"], sent["amount"]), ("xinv_1", 800.0))
        refund = PaymentTransaction.objects.get(invoice=self.invoice, transaction_type="refund")
        self.assertEqual(refund.gateway_payload["source"], "xendit")

    @patch("billing.xendit.httpx.Client")
    def test_no_second_refund_while_one_is_pending(self, mock_cls):
        self._paid_refund_pending()
        fake = _install(mock_cls, {
            ("GET", "/v2/invoices/xinv_1"): _resp(_xinv()),
            ("GET", "/refunds"): _resp({"data": [{"id": "rfd_1", "status": "PENDING", "amount": 800}]}),
        })
        self.api.force_authenticate(self.admin)
        resp = self.api.post(f"/api/admin/invoices/{self.invoice.id}/refund/")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["invoice_status"], "refund_pending")
        self.assertFalse([c for c in fake.calls if c[0] == "POST"])

    @patch("billing.xendit.httpx.Client")
    def test_xendit_refusing_a_refund_is_reported(self, mock_cls):
        self._paid_refund_pending()
        _install(mock_cls, {
            ("GET", "/v2/invoices/xinv_1"): _resp(_xinv()),
            ("GET", "/refunds"): _resp({"data": []}),
            ("POST", "/refunds"): _resp({"message": "Refund is not supported for this channel"}, error=True),
        })
        self.api.force_authenticate(self.admin)
        resp = self.api.post(f"/api/admin/invoices/{self.invoice.id}/refund/")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Xendit refused the refund", resp.data["detail"])
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "refund_pending")
