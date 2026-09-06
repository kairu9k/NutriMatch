import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from clinical.models import PreConsultationScreening
from scheduling.models import Appointment, RndClientRelationship

from .models import Invoice, PaymentTransaction

TEST_PAYMONGO = {
    "SECRET_KEY": "sk_test_fake", "WEBHOOK_SECRET": "whsec_fake",
    "BASE_URL": "https://api.paymongo.com/v1", "TIMEOUT": 30,
}
TEST_DAILY_CO = {
    "API_KEY": "fake_daily_key", "BASE_URL": "https://api.daily.co/v1", "TIMEOUT": 15,
}


@override_settings(PAYMONGO=TEST_PAYMONGO, DAILY_CO=TEST_DAILY_CO)
class BillingAndVideoViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.rnd = User.objects.create_user(email="rnd@v.ph", password="x", role="rnd", first_name="R", last_name="D")
        self.client_user = User.objects.create_user(email="client@v.ph", password="x", role="client", first_name="C", last_name="L")
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.invoice = Invoice.objects.create(relationship=self.rel, amount=Decimal("800.00"))
        self.appointment = Appointment.objects.create(
            relationship=self.rel, scheduled_at=timezone.now(), type="video", duration_minutes=30
        )

    def _mock_resp(self, data, error=False):
        r = MagicMock()
        r.is_error = error
        r.json.return_value = data
        return r

    @patch("billing.services.httpx.Client")
    def test_initiate_payment_view(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = self._mock_resp({
            "data": {"id": "link_abc", "attributes": {"checkout_url": "https://pm.link/xyz"}}
        })
        mock_client_cls.return_value = mock_client

        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.post(f"/api/client/invoices/{self.invoice.id}/pay/")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["payment_url"], "https://pm.link/xyz")
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.gateway_reference_id, "link_abc")

    def test_webhook_marks_invoice_paid(self):
        self.invoice.gateway_reference_id = "pi_999"
        self.invoice.save(update_fields=["gateway_reference_id"])

        payload = json.dumps({
            "data": {"attributes": {"type": "payment.paid", "data": {"id": "pi_999"}}}
        }).encode()
        sig = hmac.new(b"whsec_fake", payload, hashlib.sha256).hexdigest()

        resp = self.client_api.post(
            "/api/webhooks/paymongo/", data=payload, content_type="application/json",
            HTTP_PAYMONGO_SIGNATURE=sig,
        )

        self.assertEqual(resp.status_code, 200)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "paid")
        self.assertIsNotNone(self.invoice.paid_at)
        self.assertEqual(PaymentTransaction.objects.filter(invoice=self.invoice).count(), 1)

    def test_webhook_rejects_bad_signature(self):
        payload = json.dumps({"data": {"attributes": {"type": "payment.paid"}}}).encode()
        resp = self.client_api.post(
            "/api/webhooks/paymongo/", data=payload, content_type="application/json",
            HTTP_PAYMONGO_SIGNATURE="tampered",
        )
        self.assertEqual(resp.status_code, 401)

    @patch("scheduling.services.httpx.Client")
    def test_confirm_video_appointment_creates_session(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = [
            self._mock_resp({"url": "https://nutrimatch.daily.co/room-1"}),
            self._mock_resp({"token": "host-tok"}),
        ]
        mock_client_cls.return_value = mock_client

        PreConsultationScreening.objects.create(
            client=self.client_user, height_cm=Decimal("170.00"), weight_kg=Decimal("70.00"),
        )

        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appointment.id}/confirm/")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "confirmed")
        self.assertEqual(resp.data["video_session_url"], "https://nutrimatch.daily.co/room-1")
        self.assertEqual(len(resp.data["consultation_sessions"]), 1)
        # host_url must never appear in the client-facing serialized session
        self.assertNotIn("host_url", resp.data["consultation_sessions"][0])
