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


# What the client can pay with on PayMongo's checkout page (2026-10-19, user's
# call). Payment Links on this account only offered QR Ph, and the sandbox
# can't complete a QR Ph refund; GCash / Maya / card refunds go back to the
# same wallet or card and complete in test mode too.
CHECKOUT_PAYMENT_METHODS = ["qrph", "gcash", "paymaya", "card"]
# QR Ph refunds have their own API (the client claims them through a link);
# every other method uses the standard POST /v1/refunds.
QRPH_REFUNDS_URL = "https://refunds-api.paymongo.com/v1/refunds"


def is_checkout_session(reference: str | None) -> bool:
    """Invoices paid since 2026-10-19 store the checkout session id (cs_...);
    older ones store a payment link's reference_number."""
    return bool(reference) and str(reference).startswith("cs_")


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
        """Create a PayMongo Checkout Session for an invoice (QR Ph, GCash,
        Maya or card — CHECKOUT_PAYMENT_METHODS).
        Returns {'payment_url': ..., 'gateway_reference_id': <cs_... id>}.

        The session id is what the checkout_session.payment.paid webhook and
        GET /checkout_sessions/{id} identify it by; our own INV-0000 number
        goes in reference_number/metadata for the PayMongo dashboard.
        """
        amount_centavos = int(round(invoice.amount * 100))
        frontend = getattr(settings, "FRONTEND_URL", "").rstrip("/")
        attributes = {
            "line_items": [{
                "name": f"NutriMatch consultation (INV-{invoice.id:04d})",
                "amount": amount_centavos, "currency": "PHP", "quantity": 1,
            }],
            "payment_method_types": CHECKOUT_PAYMENT_METHODS,
            "description": f"NutriMatch Consultation Invoice #{invoice.id}",
            "reference_number": f"INV-{invoice.id:04d}",
            "metadata": {"invoice_id": str(invoice.id)},
            # NutriMatch emails its own receipt (billing/receipts.py).
            "send_email_receipt": False,
            "show_description": True,
            "show_line_items": True,
        }
        if frontend:
            attributes["success_url"] = f"{frontend}/invoices-billing"
            attributes["cancel_url"] = f"{frontend}/invoices-billing"

        with self._client() as client:
            response = client.post(f"{self.base_url}/checkout_sessions", json={"data": {"attributes": attributes}})

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
        payment_data = event.get("data", {}).get("attributes", {}).get("data", {})
        payment_attrs = payment_data.get("attributes", {})

        if event_type == "checkout_session.payment.paid":
            # The event carries the checkout session itself (cs_...), the id
            # create_payment_link() stored on the invoice.
            paid = paid_payment_of(payment_data)
            return {
                "event_type": event_type,
                "gateway_reference_id": payment_data.get("id"),
                "status": "success" if paid else "pending",
                "payment_method": payment_method_from_source((paid or {}).get("attributes", {}).get("source")),
                "raw": event,
            }

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

    def get_payment_status(self, reference: str) -> dict:
        """Has this invoice's checkout been paid? Works for checkout sessions
        (cs_...) and the payment links used before 2026-10-19.
        Returns {'status': 'success'|'pending', 'payment_method', 'raw'}."""
        if not is_checkout_session(reference):
            return self.get_link_status(reference)
        with self._client() as client:
            response = client.get(f"{self.base_url}/checkout_sessions/{reference}")
        if response.is_error:
            raise PaymentGatewayError("Could not check the payment status. Please try again later.")
        session = response.json()["data"]
        paid = paid_payment_of(session)
        return {
            "status": "success" if paid else "pending",
            "payment_method": payment_method_from_source((paid or {}).get("attributes", {}).get("source")),
            "raw": session,
        }

    def get_payment(self, payment_id: str) -> dict:
        """The PayMongo payment resource (with its `refunds`)."""
        with self._client() as client:
            response = client.get(f"{self.base_url}/payments/{payment_id}")
        if response.is_error:
            raise PaymentGatewayError("Could not reach PayMongo. Please try again later.")
        return response.json()["data"]

    def create_refund(self, payment_id: str, amount_centavos: int, source_type: str | None, notes: str = "") -> dict:
        """Refund a payment in full. QR Ph goes through PayMongo's QR Ph
        refunds API (the client claims it through a transfer link); every
        other method through POST /v1/refunds, back to the same card/wallet.
        Returns the refund resource — its status can already be "failed"
        (PayMongo answers 422 with the refund in that case)."""
        url = QRPH_REFUNDS_URL if source_type == "qrph" else f"{self.base_url}/refunds"
        body = {"data": {"attributes": {
            "payment_id": payment_id, "amount": amount_centavos,
            "reason": "requested_by_customer", "notes": notes[:255],
        }}}
        with self._client() as client:
            response = client.post(url, json=body)
        try:
            data = response.json()
        except ValueError:
            data = {}
        refund = data.get("data") if isinstance(data, dict) else None
        if isinstance(refund, dict) and str(refund.get("id", "")).startswith("ref_"):
            return refund
        errors = (data or {}).get("errors") or [{}]
        raise PaymentGatewayError(errors[0].get("detail") or "PayMongo refused the refund. Please try again later.")

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


def paid_payment_of(session) -> dict | None:
    """The paid payment ({"id": "pay_...", "attributes": {...}}) listed on a
    checkout session resource, or None while nothing is paid."""
    for p in ((session or {}).get("attributes") or {}).get("payments") or []:
        p = p.get("data", p) if isinstance(p, dict) else None
        if isinstance(p, dict) and (p.get("attributes") or {}).get("status") == "paid":
            return p
    return None


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
        # Receipt to the client + a copy to the NutriMatch inbox, once the
        # payment is saved. Looked up at call time (tests patch it).
        from . import receipts

        invoice_id = invoice.pk
        transaction.on_commit(lambda: receipts.send_payment_receipts(invoice_id))
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


# What the client is told about a refund (user's call, 2026-10-19). QR Ph
# refunds are claimed through a PayMongo link that works for 3 days; GCash /
# Maya / card refunds go back to the same wallet or card.
# Mirrored in frontend/app/utils/refund.js.
REFUND_WINDOW = "5–7 business days"
REFUND_CLAIM_NOTE = "We'll send you a PayMongo link to claim it to your bank or e-wallet — claim it within 3 days of getting the link."
_REFUND_BACK_TO = {"gcash": "your GCash", "maya": "your Maya account", "card": "the card you paid with"}


def refund_note(payment_method):
    """How the money comes back, by how the client paid."""
    if payment_method == "qrph":
        return REFUND_CLAIM_NOTE
    if payment_method in _REFUND_BACK_TO:
        return f"It goes back to {_REFUND_BACK_TO[payment_method]}."
    return ""


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
                f"INV-{invoice.id:04d} will be refunded within {REFUND_WINDOW}. {refund_note(invoice.payment_method)}".strip()
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


# ---------------------------------------------------------------------------
# Payment receipts (admin invoice detail)
# ---------------------------------------------------------------------------

def _find_payment_resource(payload):
    """The PayMongo payment resource ({"id": "pay_...", "attributes": {...}})
    inside a stored gateway_payload — a payment.paid webhook event nests it at
    data.attributes.data; a GET /links status check lists it under
    attributes.payments (sometimes wrapped in its own {"data": ...})."""
    if not isinstance(payload, dict):
        return None
    event_data = (payload.get("data") or {}).get("attributes", {}).get("data")
    if isinstance(event_data, dict) and str(event_data.get("id", "")).startswith("pay_"):
        return event_data
    if isinstance(event_data, dict) and str(event_data.get("id", "")).startswith("cs_"):
        return paid_payment_of(event_data)
    for p in (payload.get("attributes") or {}).get("payments") or []:
        p = p.get("data", p) if isinstance(p, dict) else None
        if isinstance(p, dict) and str(p.get("id", "")).startswith("pay_"):
            return p
    return None


def payment_receipt(payload) -> dict:
    """The receipt details of a payment, picked out of its stored PayMongo
    payload — only what a receipt shows (no raw payload is sent to the
    browser). PayMongo amounts are in centavos. Empty dict when the payment
    wasn't made through PayMongo (e.g. demo data)."""
    from datetime import datetime, timezone as dt_timezone
    from decimal import Decimal

    payment = _find_payment_resource(payload)
    if not payment:
        return {}
    attrs = payment.get("attributes") or {}
    source = attrs.get("source") or {}
    billing = attrs.get("billing") or {}

    def pesos(centavos):
        return str(Decimal(centavos) / 100) if isinstance(centavos, int) else None

    paid_at = attrs.get("paid_at")
    return {
        "payment_id": payment.get("id"),
        "status": attrs.get("status"),
        "description": attrs.get("description"),
        "reference_number": attrs.get("external_reference_number"),
        "currency": attrs.get("currency") or "PHP",
        "amount": pesos(attrs.get("amount")),
        "fee": pesos(attrs.get("fee")),
        "net_amount": pesos(attrs.get("net_amount")),
        "paid_at": datetime.fromtimestamp(paid_at, dt_timezone.utc).isoformat() if isinstance(paid_at, int) else None,
        "source_type": source.get("type"),
        "card_brand": source.get("brand"),
        "card_last4": source.get("last4"),
        "payer_name": billing.get("name"),
        "payer_email": billing.get("email"),
        "payer_phone": billing.get("phone"),
        "livemode": attrs.get("livemode"),
    }
