import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from accounts.models import User
from profiles.models import RndProfile
from scheduling.models import Appointment, RndClientRelationship
from scheduling.services import DailyCoVideoService, VideoSessionError

from .models import Invoice
from .services import InvalidWebhookSignatureError, PayMongoService, PaymentGatewayError


TEST_PAYMONGO = {
    "SECRET_KEY": "sk_test_fake",
    "WEBHOOK_SECRET": "whsec_fake",
    "BASE_URL": "https://api.paymongo.com/v1",
    "TIMEOUT": 30,
}

TEST_DAILY_CO = {
    "API_KEY": "fake_daily_key",
    "BASE_URL": "https://api.daily.co/v1",
    "TIMEOUT": 15,
}


def _mock_response(json_data, error=False):
    resp = MagicMock()
    resp.is_error = error
    resp.json.return_value = json_data
    return resp


@override_settings(PAYMONGO=TEST_PAYMONGO)
class PayMongoServiceTests(TestCase):
    def setUp(self):
        rnd = User.objects.create_user(email="rnd@t.ph", password="x", role="rnd", first_name="R", last_name="D")
        client = User.objects.create_user(email="client@t.ph", password="x", role="client", first_name="C", last_name="L")
        rel = RndClientRelationship.objects.create(rnd=rnd, client=client, status="active")
        self.invoice = Invoice.objects.create(relationship=rel, amount=Decimal("800.00"))

    def test_missing_secret_key_raises(self):
        with override_settings(PAYMONGO={**TEST_PAYMONGO, "SECRET_KEY": ""}):
            with self.assertRaises(PaymentGatewayError):
                PayMongoService().create_payment_link(self.invoice)

    @patch("billing.services.httpx.Client")
    def test_create_payment_link_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = _mock_response({
            "data": {"id": "link_123", "attributes": {"checkout_url": "https://pm.link/abc"}}
        })
        mock_client_cls.return_value = mock_client

        result = PayMongoService().create_payment_link(self.invoice)

        self.assertEqual(result["payment_url"], "https://pm.link/abc")
        self.assertEqual(result["gateway_reference_id"], "link_123")
        # amount converted to centavos correctly
        sent_kwargs = mock_client.post.call_args.kwargs
        self.assertEqual(sent_kwargs["json"]["data"]["attributes"]["amount"], 80000)

    @patch("billing.services.httpx.Client")
    def test_create_payment_link_gateway_error(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = _mock_response({}, error=True)
        mock_client_cls.return_value = mock_client

        with self.assertRaises(PaymentGatewayError):
            PayMongoService().create_payment_link(self.invoice)

    def test_webhook_valid_signature(self):
        payload = json.dumps({
            "data": {"attributes": {"type": "payment.paid", "data": {"id": "pi_123"}}}
        }).encode()
        sig = hmac.new(b"whsec_fake", payload, hashlib.sha256).hexdigest()

        event = PayMongoService().handle_webhook(payload, sig)

        self.assertEqual(event["status"], "success")
        self.assertEqual(event["gateway_reference_id"], "pi_123")

    def test_webhook_invalid_signature_rejected(self):
        payload = json.dumps({"data": {"attributes": {"type": "payment.paid"}}}).encode()
        with self.assertRaises(InvalidWebhookSignatureError):
            PayMongoService().handle_webhook(payload, "wrong-signature")

    @patch("billing.services.httpx.Client")
    def test_get_payment_status_maps_succeeded(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = _mock_response({
            "data": {"attributes": {"status": "succeeded"}}
        })
        mock_client_cls.return_value = mock_client

        status = PayMongoService().get_payment_status("pi_123")
        self.assertEqual(status, "success")


@override_settings(DAILY_CO=TEST_DAILY_CO)
class DailyCoVideoServiceTests(TestCase):
    def setUp(self):
        rnd = User.objects.create_user(email="rnd2@t.ph", password="x", role="rnd", first_name="R", last_name="D")
        client = User.objects.create_user(email="client2@t.ph", password="x", role="client", first_name="C", last_name="L")
        rel = RndClientRelationship.objects.create(rnd=rnd, client=client, status="active")
        from django.utils import timezone
        self.appointment = Appointment.objects.create(
            relationship=rel, scheduled_at=timezone.now(), type="video", duration_minutes=30
        )

    def test_missing_api_key_raises(self):
        with override_settings(DAILY_CO={**TEST_DAILY_CO, "API_KEY": ""}):
            with self.assertRaises(VideoSessionError):
                DailyCoVideoService().create_room(self.appointment)

    @patch("scheduling.services.httpx.Client")
    def test_create_room_success(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.side_effect = [
            _mock_response({"url": "https://nutrimatch.daily.co/nm-appt-1-abc"}),  # room creation
            _mock_response({"token": "fake-host-token"}),  # host token
        ]
        mock_client_cls.return_value = mock_client

        result = DailyCoVideoService().create_room(self.appointment)

        self.assertIn("participant_url", result)
        self.assertEqual(result["participant_url"], "https://nutrimatch.daily.co/nm-appt-1-abc")
        self.assertIn("fake-host-token", result["host_url"])
        self.assertTrue(result["external_session_id"].startswith(f"nm-appt-{self.appointment.id}-"))

    @patch("scheduling.services.httpx.Client")
    def test_create_room_failure_raises(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = _mock_response({}, error=True)
        mock_client_cls.return_value = mock_client

        with self.assertRaises(VideoSessionError):
            DailyCoVideoService().create_room(self.appointment)
