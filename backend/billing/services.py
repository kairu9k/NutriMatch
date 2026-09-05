"""PayMongo payment gateway integration for the Philippine market.

Security notes:
 - Secret key is read from settings.PAYMONGO (sourced from .env) only —
   never hardcoded.
 - Webhook signatures are always validated before processing.
 - Full gateway responses are stored in PaymentTransaction.gateway_payload
   for audit, but payment_url is returned to the caller and never logged.
"""

import hashlib
import hmac
import json

import httpx
from django.conf import settings


class PaymentGatewayError(Exception):
    pass


class InvalidWebhookSignatureError(Exception):
    pass


class PayMongoService:
    def __init__(self):
        cfg = settings.PAYMONGO
        self.secret_key = cfg["SECRET_KEY"]
        self.webhook_secret = cfg["WEBHOOK_SECRET"]
        self.base_url = cfg["BASE_URL"]
        self.timeout = cfg["TIMEOUT"]

    def _client(self):
        if not self.secret_key:
            raise PaymentGatewayError("PAYMONGO_SECRET_KEY is not configured.")
        return httpx.Client(auth=(self.secret_key, ""), timeout=self.timeout)

    def create_payment_link(self, invoice) -> dict:
        """Create a PayMongo payment link for an invoice.
        Returns {'payment_url': ..., 'gateway_reference_id': ...}.
        """
        amount_centavos = int(round(invoice.amount * 100))

        with self._client() as client:
            response = client.post(
                f"{self.base_url}/links",
                json={
                    "data": {
                        "attributes": {
                            "amount": amount_centavos,
                            "description": f"NutriMatch Consultation Invoice #{invoice.id}",
                            "currency": "PHP",
                        }
                    }
                },
            )

        if response.is_error:
            # NOTE: never log secret_key or the full response body
            raise PaymentGatewayError("Payment gateway error. Please try again later.")

        data = response.json()["data"]
        return {
            "payment_url": data["attributes"]["checkout_url"],
            "gateway_reference_id": data["id"],
        }

    def handle_webhook(self, payload: bytes, signature: str) -> dict:
        """Validate a PayMongo webhook signature and return normalized event data.

        PayMongo signs the raw request body (bytes), not the parsed JSON —
        `payload` must be the exact bytes received, not a re-serialized dict.
        """
        if not self._validate_signature(payload, signature):
            raise InvalidWebhookSignatureError("Webhook signature validation failed.")

        event = json.loads(payload)
        event_type = event.get("data", {}).get("attributes", {}).get("type", "")

        return {
            "event_type": event_type,
            "gateway_reference_id": event.get("data", {}).get("attributes", {}).get("data", {}).get("id"),
            "status": self._map_event_to_status(event_type),
            "raw": event,
        }

    def get_payment_status(self, gateway_reference_id: str) -> str:
        with self._client() as client:
            response = client.get(f"{self.base_url}/payment_intents/{gateway_reference_id}")

        if response.is_error:
            return "pending"

        status = response.json().get("data", {}).get("attributes", {}).get("status", "pending")
        return self._map_paymongo_status(status)

    def _validate_signature(self, payload: bytes, signature: str) -> bool:
        if not self.webhook_secret:
            raise PaymentGatewayError("PAYMONGO_WEBHOOK_SECRET is not configured.")
        computed = hmac.new(self.webhook_secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, signature)

    @staticmethod
    def _map_event_to_status(event_type: str) -> str:
        return {
            "payment.paid": "success",
            "payment.failed": "failed",
            "payment.refunded": "refunded",
        }.get(event_type, "pending")

    @staticmethod
    def _map_paymongo_status(status: str) -> str:
        if status == "succeeded":
            return "success"
        if status in ("awaiting_payment_method", "processing"):
            return "pending"
        if status == "failed":
            return "failed"
        return "pending"
