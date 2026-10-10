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

        gateway_reference_id is the link's reference_number, not its `id`
        (link_...) — the payment.paid webhook payload never echoes the link
        id back, only external_reference_number/metadata.pm_reference_number,
        which equals reference_number. Matching on the link id would never
        find the invoice.
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
            "gateway_reference_id": data["attributes"]["reference_number"],
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
        payment_data = event.get("data", {}).get("attributes", {}).get("data", {})
        payment_attrs = payment_data.get("attributes", {})

        return {
            "event_type": event_type,
            # external_reference_number is the payment link's reference_number
            # echoed back — payment_data["id"] (pay_...) is a different id
            # namespace than what create_payment_link() stores on the invoice.
            "gateway_reference_id": payment_attrs.get("external_reference_number"),
            "status": self._map_event_to_status(event_type),
            "payment_method": payment_method_from_source(payment_attrs.get("source")),
            "raw": event,
        }

    def get_link_status(self, reference_number: str) -> dict:
        """Ask PayMongo directly whether a payment link has been paid — the
        fallback for when the payment.paid webhook never arrived (webhook
        disabled, tunnel down). PayMongo accepts the link's reference_number
        in place of its id on GET /links/{id}. Returns
        {'status': 'success'|'pending', 'raw': <link resource>}."""
        with self._client() as client:
            response = client.get(f"{self.base_url}/links/{reference_number}")

        if response.is_error:
            raise PaymentGatewayError("Could not check the payment status. Please try again later.")

        link = response.json()["data"]
        paid = link.get("attributes", {}).get("status") == "paid"
        method = None
        if paid:
            # The link resource doesn't say how the client paid — the payment
            # resource does (attributes.source.type). Best-effort: a failed
            # lookup still records the payment, just without the method.
            payments = link.get("attributes", {}).get("payments") or []
            payment_id = payments[0].get("id") if payments else None
            if payment_id:
                try:
                    with self._client() as client:
                        payment = client.get(f"{self.base_url}/payments/{payment_id}")
                    if not payment.is_error:
                        method = payment_method_from_source(
                            payment.json()["data"].get("attributes", {}).get("source")
                        )
                except (httpx.HTTPError, KeyError, ValueError):
                    method = None
        return {"status": "success" if paid else "pending", "payment_method": method, "raw": link}

    def _validate_signature(self, payload: bytes, signature: str) -> bool:
        """PayMongo's Paymongo-Signature header is a comma-separated string
        like 't=1234567890,te=<test-sig>,li=<live-sig>' — not a bare hex
        digest — and the signed value is '{timestamp}.{raw_body}', not the
        raw body alone. Test-mode keys (sk_test_...) are verified against
        `te`; live keys against `li`. See PayMongo's webhook docs."""
        if not self.webhook_secret:
            raise PaymentGatewayError("PAYMONGO_WEBHOOK_SECRET is not configured.")

        parts = dict(p.split("=", 1) for p in signature.split(",") if "=" in p)
        timestamp = parts.get("t")
        is_live = self.secret_key.startswith("sk_live_")
        provided = parts.get("li") if is_live else parts.get("te")
        if not timestamp or not provided:
            return False

        signed_payload = f"{timestamp}.{payload.decode()}".encode()
        computed = hmac.new(self.webhook_secret.encode(), signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, provided)

    @staticmethod
    def _map_event_to_status(event_type: str) -> str:
        return {
            "payment.paid": "success",
            "payment.failed": "failed",
            "payment.refunded": "refunded",
        }.get(event_type, "pending")



# PayMongo payment source types → Invoice.PaymentMethod.
_SOURCE_TO_METHOD = {
    "card": "card",
    "gcash": "gcash",
    "paymaya": "maya",
    "maya": "maya",
    "qrph": "qrph",
    "dob": "bank_transfer",
    "dob_ubp": "bank_transfer",
    "brankas_bdo": "bank_transfer",
    "brankas_landbank": "bank_transfer",
    "brankas_metrobank": "bank_transfer",
}


def payment_method_from_source(source) -> str | None:
    """Map a PayMongo payment's `source` ({"type": "qrph", ...}) to an
    Invoice.PaymentMethod value; unknown types → "other", no source → None."""
    source_type = (source or {}).get("type") if isinstance(source, dict) else None
    if not source_type:
        return None
    return _SOURCE_TO_METHOD.get(source_type, "other")


def record_successful_payment(invoice, reference_id: str, payload: dict, source: str, payment_method: str | None = None) -> bool:
    """Record a confirmed payment and mark the invoice paid — shared by the
    webhook and the direct status check so both behave identically.
    Idempotent: returns False (and records nothing) if already paid.
    `payment_method` (e.g. "qrph", "gcash") is saved on the invoice when known."""
    from django.db import transaction
    from django.utils import timezone

    from core.models import AuditLog

    from .models import Invoice, PaymentTransaction

    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        if invoice.status == Invoice.Status.PAID:
            return False
        PaymentTransaction.objects.create(
            invoice=invoice,
            transaction_type=PaymentTransaction.TransactionType.PAYMENT,
            amount=invoice.amount,
            status="success",
            gateway_payload=payload,
            processed_at=timezone.now(),
        )
        invoice.status = Invoice.Status.PAID
        invoice.paid_at = timezone.now()
        update_fields = ["status", "paid_at"]
        if payment_method:
            invoice.payment_method = payment_method
            update_fields.append("payment_method")
        # Paid after the appointment was already cancelled/expired (e.g. the
        # webhook arrived late) — keep the money on record, flag a refund.
        appt = invoice.appointment
        if appt is not None and appt.status == appt.Status.CANCELLED:
            invoice.status = Invoice.Status.REFUND_PENDING
        invoice.save(update_fields=update_fields)
        AuditLog.objects.create(
            action="invoice.paid",
            table_name="invoices",
            record_id=invoice.id,
            new_values={"status": "paid", "gateway_reference_id": reference_id, "source": source},
        )
    return True



# ---------------------------------------------------------------------------
# Pay before the consultation (2026-10-10): the invoice is created when the
# RND confirms; the client pays before the scheduled start; the consultation
# (video link, chat, "Complete") only opens once it's paid.
# ---------------------------------------------------------------------------

NOT_PAID_REASON = "Not paid before the scheduled start time."


def appointment_invoice(appointment):
    """The appointment's current invoice (newest), or None."""
    return appointment.invoices.order_by("-created_at").first()


def is_appointment_paid(appointment) -> bool:
    from .models import Invoice

    return appointment.invoices.filter(status=Invoice.Status.PAID).exists()


def create_appointment_invoice(appointment):
    """Create the invoice for an appointment (once). Amount is the RND's
    consultation fee now; commission % is frozen at creation (proposal
    rule) from SystemSetting `platform_commission_pct` or the model default."""
    from decimal import Decimal, InvalidOperation

    from core.models import SystemSetting

    from .models import Invoice

    existing = appointment.invoices.exclude(status=Invoice.Status.CANCELLED).first()
    if existing:
        return existing, False
    rnd_profile = getattr(appointment.relationship.rnd, "rnd_profile", None)
    kwargs = {
        "relationship": appointment.relationship,
        "appointment": appointment,
        "amount": rnd_profile.consultation_fee if rnd_profile else 0,
    }
    setting = SystemSetting.objects.filter(key="platform_commission_pct").first()
    if setting and setting.value:
        try:
            kwargs["commission_pct"] = Decimal(setting.value)
        except (InvalidOperation, TypeError):
            pass
    return Invoice.objects.create(**kwargs), True


def settle_cancelled_appointment(appointment):
    """After an appointment is cancelled: a paid invoice becomes
    refund-pending (client told), an unpaid one is voided. Returns the
    invoice touched, if any."""
    from communication.services import notify

    from .models import Invoice

    invoice = appointment_invoice(appointment)
    if invoice is None:
        return None
    if invoice.status == Invoice.Status.PAID:
        invoice.status = Invoice.Status.REFUND_PENDING
        invoice.save(update_fields=["status"])
        notify(
            recipient=appointment.relationship.client,
            notifiable_type="invoice",
            notifiable_id=invoice.id,
            subject="Refund being processed",
            content=(
                f"Your appointment was cancelled, so your ₱{invoice.amount:,.2f} payment for "
                f"INV-{invoice.id:04d} will be refunded. The NutriMatch team will process it."
            ),
        )
    elif invoice.status == Invoice.Status.UNPAID:
        invoice.status = Invoice.Status.CANCELLED
        invoice.save(update_fields=["status"])
    return invoice


def expire_unpaid_appointments(**scope):
    """Confirmed appointments whose start time passed while their invoice was
    still unpaid are cancelled ("not paid") and the invoice voided, so the
    slot is released and it can't be paid late. Run lazily wherever
    appointments/invoices are listed. Returns how many were expired."""
    from django.utils import timezone

    from communication.services import notify
    from scheduling.models import Appointment

    from .models import Invoice

    due = Appointment.objects.filter(
        status=Appointment.Status.CONFIRMED,
        scheduled_at__lte=timezone.now(),
        invoices__status=Invoice.Status.UNPAID,
        **scope,
    ).exclude(invoices__status=Invoice.Status.PAID).select_related("relationship__client", "relationship__rnd").distinct()
    count = 0
    for appt in due:
        appt.status = Appointment.Status.CANCELLED
        appt.cancellation_reason = NOT_PAID_REASON
        appt.save(update_fields=["status", "cancellation_reason", "updated_at"])
        appt.invoices.filter(status=Invoice.Status.UNPAID).update(status=Invoice.Status.CANCELLED)
        for recipient, text in (
            (appt.relationship.client, "Your consultation was cancelled because it wasn't paid before the start time. You can book a new time."),
            (appt.relationship.rnd, f"{appt.relationship.client.full_name}'s consultation was cancelled because it wasn't paid before the start time. The slot is open again."),
        ):
            notify(recipient=recipient, notifiable_type="appointment", notifiable_id=appt.id,
                   subject="Consultation not paid", content=text)
        count += 1
    return count
