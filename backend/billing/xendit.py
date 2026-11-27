"""Client payments and refunds through Xendit (2026-11-27, user's call: PayMongo deactivated
the account, the adviser doesn't allow skipping payment, and Xendit's test mode works
without business verification). Xendit is the default provider (settings.PAYMENT_PROVIDER);
the PayMongo code in services.py stays for invoices paid through it and to switch back.

Pay creates a Xendit Invoice (its hosted checkout page) and stores the Xendit invoice id in
Invoice.gateway_reference_id. It counts as paid only once Xendit's own API says PAID/SETTLED:
the callback (webhook) is only a hint, its body is never trusted, the invoice is read back.
Refunds go back to the same GCash / Maya wallet or card through POST /refunds.

Settings: XENDIT_SECRET_KEY (xnd_development_... in test mode; Money-in write) and
XENDIT_CALLBACK_TOKEN (Xendit dashboard, Settings > Webhooks; sent as x-callback-token).
"""

import hmac
from datetime import datetime
from decimal import Decimal

import httpx
from django.conf import settings

from .services import PaymentGatewayError

BASE_URL = "https://api.xendit.co"
TIMEOUT = 20

# What the client can pay with on Xendit's page. QR Ph is left out: Xendit can't refund it
# through the API, and every refund here must go back the way the client paid. Card shows
# only once cards are switched on for the account.
PAYMENT_METHODS = ["GCASH", "PAYMAYA", "CREDIT_CARD"]
PAID = {"PAID", "SETTLED"}

# Xendit's payment_channel / payment_method -> Invoice.PaymentMethod
_CHANNEL_TO_METHOD = {"GCASH": "gcash", "PAYMAYA": "maya", "QRPH": "qrph"}
_METHOD_TO_METHOD = {"CREDIT_CARD": "card", "BANK_TRANSFER": "bank_transfer", "DIRECT_DEBIT": "bank_transfer"}


def payment_method_of(xinv) -> str | None:
    channel = (xinv.get("payment_channel") or "").upper()
    method = (xinv.get("payment_method") or "").upper()
    if not channel and not method:
        return None
    return _CHANNEL_TO_METHOD.get(channel) or _METHOD_TO_METHOD.get(method) or "other"


def is_paid(xinv) -> bool:
    return (xinv.get("status") or "").upper() in PAID


def stored_payload(xinv) -> dict:
    """What a PaymentTransaction keeps of a paid Xendit invoice (billing.services.payment_receipt
    reads it): the invoice resource, marked as Xendit's."""
    return {"provider": "xendit", "invoice": xinv}


def receipt_of(xinv) -> dict:
    """The receipt fields of a paid Xendit invoice, in the shape payment_receipt() returns."""

    def pesos(value):
        return str(Decimal(str(value))) if isinstance(value, (int, float)) else None

    fee = xinv.get("fees_paid_amount")
    paid = xinv.get("paid_amount", xinv.get("amount"))
    net = xinv.get("adjusted_received_amount")
    channel = xinv.get("payment_channel")
    return {
        "provider": "xendit",
        "payment_id": xinv.get("id"),
        "status": (xinv.get("status") or "").lower() or None,
        "description": xinv.get("description"),
        "reference_number": xinv.get("external_id"),
        "currency": xinv.get("currency") or "PHP",
        "amount": pesos(paid),
        "fee": pesos(fee) if fee else None,
        "net_amount": pesos(net),
        "paid_at": xinv.get("paid_at"),
        "source_type": (channel or xinv.get("payment_method") or "").lower() or None,
        "card_brand": None,
        "card_last4": None,
        "payer_name": None,
        "payer_email": xinv.get("payer_email"),
        "payer_phone": None,
        "livemode": not settings.XENDIT_SECRET_KEY.startswith("xnd_development_"),
    }


def _refund_row(r) -> dict:
    """A Xendit refund in the shape billing.refunds uses for PayMongo's (lower-case status)."""
    status = (r.get("status") or "").lower()
    amount = r.get("amount")
    return {
        "id": r.get("id"),
        "status": {"succeeded": "succeeded", "failed": "failed"}.get(status, "pending" if status else None),
        "amount": str(Decimal(str(amount))) if isinstance(amount, (int, float)) else None,
        "reason": r.get("reason"),
        "notes": r.get("failure_code"),
        "transfer_link": None,
        "created_at": r.get("created"),
        "refunded_at": r.get("updated") if status == "succeeded" else None,
    }


class XenditService:
    provider = "xendit"

    def __init__(self):
        self.secret_key = settings.XENDIT_SECRET_KEY
        self.callback_token = settings.XENDIT_CALLBACK_TOKEN

    def _client(self):
        if not self.secret_key:
            raise PaymentGatewayError("XENDIT_SECRET_KEY is not configured.")
        return httpx.Client(base_url=BASE_URL, auth=(self.secret_key, ""), timeout=TIMEOUT)

    def _call(self, method, path, **kwargs):
        try:
            with self._client() as client:
                response = client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise PaymentGatewayError("Could not reach Xendit. Please try again later.") from exc
        try:
            data = response.json()
        except ValueError:
            data = {}
        if response.is_error:
            # Never log the key or the whole body; Xendit's message is safe to show an admin.
            message = data.get("message") if isinstance(data, dict) else None
            raise PaymentGatewayError(message or "Xendit refused the request. Please try again later.")
        return data

    def create_payment_link(self, invoice, pay_by: datetime | None = None) -> dict:
        """A Xendit Invoice for this NutriMatch invoice. It expires at the pay-by time, so a page
        left open can't take money for a consultation that was already cancelled.
        Returns {'payment_url', 'gateway_reference_id'} like PayMongoService."""
        from django.utils import timezone

        frontend = getattr(settings, "FRONTEND_URL", "").rstrip("/")
        body = {
            "external_id": f"INV-{invoice.id:04d}",
            "amount": float(invoice.amount),
            "currency": "PHP",
            "description": f"NutriMatch consultation (INV-{invoice.id:04d})",
            "payment_methods": PAYMENT_METHODS,
            "items": [{"name": "NutriMatch consultation", "quantity": 1, "price": float(invoice.amount)}],
            # NutriMatch emails its own receipt (billing/receipts.py).
            "should_send_email": False,
        }
        if pay_by is not None:
            body["invoice_duration"] = max(60, int((pay_by - timezone.now()).total_seconds()))
        if frontend:
            body["success_redirect_url"] = f"{frontend}/invoices-billing"
            body["failure_redirect_url"] = f"{frontend}/invoices-billing"
        data = self._call("POST", "/v2/invoices", json=body)
        return {"payment_url": data["invoice_url"], "gateway_reference_id": data["id"]}

    def get_invoice(self, xendit_invoice_id: str) -> dict:
        return self._call("GET", f"/v2/invoices/{xendit_invoice_id}")

    def get_payment_status(self, reference: str) -> dict:
        """Same shape as PayMongoService.get_payment_status: {'status', 'payment_method', 'raw'}."""
        xinv = self.get_invoice(reference)
        return {
            "status": "success" if is_paid(xinv) else "pending",
            "payment_method": payment_method_of(xinv),
            "raw": stored_payload(xinv),
        }

    def callback_token_ok(self, token: str) -> bool:
        if not self.callback_token:
            raise PaymentGatewayError("XENDIT_CALLBACK_TOKEN is not configured.")
        return hmac.compare_digest(self.callback_token.encode(), (token or "").encode())

    # ---- refunds (billing/refunds.py)

    def payment_state(self, xendit_invoice_id: str) -> dict:
        """What Xendit says about the payment and its refunds, in billing.refunds' shape."""
        xinv = self.get_invoice(xendit_invoice_id)
        listed = self._call("GET", "/refunds", params={"invoice_id": xendit_invoice_id})
        refunds = [_refund_row(r) for r in (listed.get("data") or [])]
        paid = Decimal(str(xinv.get("paid_amount", xinv.get("amount")) or 0))
        succeeded = sum(Decimal(r["amount"] or 0) for r in refunds if r["status"] == "succeeded")
        return {
            "available": True,
            "provider": self.provider,
            "payment_id": xendit_invoice_id,
            "payment_status": (xinv.get("status") or "").lower(),
            "amount": str(paid),
            "source_type": (xinv.get("payment_channel") or xinv.get("payment_method") or "").lower() or None,
            "livemode": not self.secret_key.startswith("xnd_development_"),
            "refunds": refunds,
            "refunded_amount": str(succeeded),
            "refunded": paid > 0 and succeeded >= paid,
            "in_progress": any(r["status"] == "pending" for r in refunds),
        }

    def create_refund(self, xendit_invoice_id: str, amount: Decimal, notes: str = "") -> dict:
        body = {"invoice_id": xendit_invoice_id, "amount": float(amount), "currency": "PHP", "reason": "CANCELLATION"}
        if notes:
            body["metadata"] = {"note": notes[:250]}
        return _refund_row(self._call("POST", "/refunds", json=body))
