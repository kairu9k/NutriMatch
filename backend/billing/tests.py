import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from accounts.models import User
from profiles.models import RndProfile
from scheduling.models import Appointment, RndClientRelationship
from scheduling.services import JitsiVideoService

from .models import Invoice
from .services import InvalidWebhookSignatureError, PayMongoService, PaymentGatewayError


TEST_PAYMONGO = {
    "SECRET_KEY": "sk_test_fake",
    "WEBHOOK_SECRET": "whsec_fake",
    "BASE_URL": "https://api.paymongo.com/v1",
    "TIMEOUT": 30,
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
            "data": {"id": "link_123", "attributes": {
                "checkout_url": "https://pm.link/abc", "reference_number": "ref_xyz"
            }}
        })
        mock_client_cls.return_value = mock_client

        result = PayMongoService().create_payment_link(self.invoice)

        self.assertEqual(result["payment_url"], "https://pm.link/abc")
        self.assertEqual(result["gateway_reference_id"], "ref_xyz")
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
            "data": {"attributes": {"type": "payment.paid", "data": {
                "id": "pay_123", "attributes": {"external_reference_number": "ref_abc"}
            }}}
        }).encode()
        # Real Paymongo-Signature shape: 't=<ts>,te=<test-sig>,li=<live-sig>',
        # signing '{timestamp}.{raw_body}' — not a bare hex digest of the
        # payload alone. TEST_PAYMONGO's SECRET_KEY is sk_test_..., so this
        # verifies against 'te'.
        timestamp = "1700000000"
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        te = hmac.new(b"whsec_fake", signed_payload, hashlib.sha256).hexdigest()
        header = f"t={timestamp},te={te},li=irrelevant-for-test-mode"

        event = PayMongoService().handle_webhook(payload, header)

        self.assertEqual(event["status"], "success")
        # gateway_reference_id is external_reference_number (the payment
        # link's reference_number), not data.id (pay_... is a different id
        # namespace than what create_payment_link() stores on the invoice).
        self.assertEqual(event["gateway_reference_id"], "ref_abc")

    def test_webhook_invalid_signature_rejected(self):
        payload = json.dumps({"data": {"attributes": {"type": "payment.paid"}}}).encode()
        with self.assertRaises(InvalidWebhookSignatureError):
            PayMongoService().handle_webhook(payload, "t=1700000000,te=wrong-signature")

    @override_settings(PAYMONGO={**TEST_PAYMONGO, "SECRET_KEY": "sk_live_fake"})
    def test_webhook_live_mode_verifies_against_li(self):
        payload = json.dumps({
            "data": {"attributes": {"type": "payment.paid", "data": {
                "id": "pay_live_1", "attributes": {"external_reference_number": "ref_live_1"}
            }}}
        }).encode()
        timestamp = "1700000000"
        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        li = hmac.new(b"whsec_fake", signed_payload, hashlib.sha256).hexdigest()
        # te is deliberately wrong — a live key must verify against li, not te
        header = f"t={timestamp},te=wrong,li={li}"

        event = PayMongoService().handle_webhook(payload, header)
        self.assertEqual(event["status"], "success")

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


class JitsiVideoServiceTests(TestCase):
    def setUp(self):
        rnd = User.objects.create_user(email="rnd2@t.ph", password="x", role="rnd", first_name="R", last_name="D")
        client = User.objects.create_user(email="client2@t.ph", password="x", role="client", first_name="C", last_name="L")
        rel = RndClientRelationship.objects.create(rnd=rnd, client=client, status="active")
        from django.utils import timezone
        self.appointment = Appointment.objects.create(
            relationship=rel, scheduled_at=timezone.now(), type="video", duration_minutes=30
        )

    def test_create_room_returns_jitsi_url(self):
        result = JitsiVideoService().create_room(self.appointment)

        self.assertTrue(result["participant_url"].startswith("https://meet.jit.si/"))
        # no host/participant distinction on the public server
        self.assertEqual(result["host_url"], result["participant_url"])
        self.assertTrue(result["external_session_id"].startswith(f"nm-appt-{self.appointment.id}-"))
        self.assertIn(result["external_session_id"], result["participant_url"])

    def test_create_room_names_are_unique(self):
        first = JitsiVideoService().create_room(self.appointment)
        second = JitsiVideoService().create_room(self.appointment)

        self.assertNotEqual(first["external_session_id"], second["external_session_id"])
