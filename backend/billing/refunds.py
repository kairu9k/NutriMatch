"""Refunds through PayMongo (2026-10-19, user's call — the adviser wants the
money trail in PayMongo, not just a status in NutriMatch).

An invoice is only marked Refunded once PayMongo shows a *succeeded* refund
for its payment (PayMongo keeps the payment's own status "paid"; the refund
entries carry the outcome). GCash / Maya / card refunds go back to the same
wallet or card and succeed in the sandbox; QR Ph refunds are claimed by the
client through a PayMongo transfer link (live mode only — the sandbox fails
them). Invoices that weren't paid through PayMongo (demo data) keep the
manual "Mark as refunded".
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Invoice, PaymentTransaction
from .services import PaymentGatewayError, PayMongoService, payment_receipt

# A refund PayMongo is still working on (the QR Ph claim link is open, or a
# wallet/card refund hasn't settled) — never start a second one meanwhile.
IN_PROGRESS = {"pending", "processing", "refunding"}


class RefundError(Exception):
    pass


def invoice_payment_id(invoice):
    """The PayMongo payment id (pay_...) of the invoice's recorded payment,
    or None (not paid through PayMongo, e.g. demo data)."""
    for t in invoice.transactions.filter(
        transaction_type=PaymentTransaction.TransactionType.PAYMENT, status="success",
    ).order_by("-created_at"):
        pid = payment_receipt(t.gateway_payload).get("payment_id")
        if pid:
            return pid
    return None


def _pesos(centavos):
    return str(Decimal(centavos) / 100) if isinstance(centavos, int) else None


def _refund_row(r):
    a = r.get("attributes") or {}
    return {
        "id": r.get("id"), "status": a.get("status"), "amount": _pesos(a.get("amount")),
        "reason": a.get("reason"), "notes": a.get("notes"), "transfer_link": a.get("transfer_link"),
        "created_at": a.get("created_at"), "refunded_at": a.get("refunded_at"),
    }


def paymongo_status(invoice, service=None):
    """What PayMongo says about the invoice's payment and its refunds."""
    pid = invoice_payment_id(invoice)
    if not pid:
        return {"available": False}
    payment = (service or PayMongoService()).get_payment(pid)
    attrs = payment.get("attributes") or {}
    refunds = [_refund_row(r) for r in attrs.get("refunds") or []]
    succeeded = sum(Decimal(r["amount"] or 0) for r in refunds if r["status"] == "succeeded")
    paid = Decimal(_pesos(attrs.get("amount")) or 0)
    return {
        "available": True,
        "payment_id": pid,
        "payment_status": attrs.get("status"),
        "amount": _pesos(attrs.get("amount")),
        "source_type": (attrs.get("source") or {}).get("type"),
        "livemode": attrs.get("livemode"),
        "refunds": refunds,
        "refunded_amount": str(succeeded),
        "refunded": paid > 0 and succeeded >= paid,
        "in_progress": any(r["status"] in IN_PROGRESS for r in refunds),
    }


def apply_confirmed_refund(invoice, state, user=None) -> bool:
    """Mark a refund-pending invoice Refunded when PayMongo confirms it —
    saves the refund ids, audit row and tells the client. Idempotent."""
    from communication.services import notify
    from core.models import AuditLog

    if not state.get("refunded"):
        return False
    with transaction.atomic():
        invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
        if invoice.status != Invoice.Status.REFUND_PENDING:
            return False
        done = [r for r in state["refunds"] if r["status"] == "succeeded"]
        invoice.status = Invoice.Status.REFUNDED
        invoice.save(update_fields=["status"])
        PaymentTransaction.objects.create(
            invoice=invoice,
            transaction_type=PaymentTransaction.TransactionType.REFUND,
            amount=invoice.amount,
            status="success",
            gateway_payload={"source": "paymongo", "reference": ", ".join(r["id"] for r in done),
                             "payment_id": state["payment_id"], "refunds": done},
            processed_at=timezone.now(),
        )
        AuditLog.objects.create(
            user=user, action="invoice.refunded", table_name="invoices", record_id=invoice.id,
            new_values={"status": "refunded", "reference": [r["id"] for r in done], "confirmed_by": "paymongo"},
        )
        notify(
            recipient=invoice.relationship.client, notifiable_type="invoice", notifiable_id=invoice.id,
            subject="Refund completed",
            content=f"Your ₱{invoice.amount:,.2f} refund for INV-{invoice.id:04d} has been sent back to you through PayMongo.",
        )
    return True


def refund_through_paymongo(invoice, user):
    """Admin: send the refund to PayMongo (once), then read back PayMongo's
    answer. Returns (state, refund_created_or_None)."""
    from communication.services import notify
    from core.models import AuditLog

    if invoice.status != Invoice.Status.REFUND_PENDING:
        raise RefundError("Only refund-pending invoices can be refunded.")
    service = PayMongoService()
    try:
        state = paymongo_status(invoice, service)
    except PaymentGatewayError as exc:
        raise RefundError(str(exc)) from exc
    if not state["available"]:
        raise RefundError("This invoice wasn't paid through PayMongo, so there's nothing to refund there. "
                          "Return the money another way, then use Mark as refunded.")
    if state["refunded"]:
        apply_confirmed_refund(invoice, state, user)
        return state, None
    if state["in_progress"]:
        # PayMongo is already handling one — don't send the money twice.
        return state, None

    try:
        refund = service.create_refund(
            state["payment_id"], int(round(Decimal(state["amount"]) * 100)), state["source_type"],
            notes=f"NutriMatch INV-{invoice.id:04d}, consultation cancelled",
        )
    except PaymentGatewayError as exc:
        AuditLog.objects.create(user=user, action="invoice.refund_requested", table_name="invoices",
                                record_id=invoice.id, new_values={"error": str(exc)[:300]})
        raise RefundError(f"PayMongo refused the refund: {exc}") from exc
    row = _refund_row(refund)
    AuditLog.objects.create(user=user, action="invoice.refund_requested", table_name="invoices",
                            record_id=invoice.id, new_values={"refund_id": row["id"], "status": row["status"]})
    if row["transfer_link"] and row["status"] != "failed":
        # QR Ph: the client chooses where the money goes through this link.
        notify(
            recipient=invoice.relationship.client, notifiable_type="invoice", notifiable_id=invoice.id,
            subject="Claim your refund",
            content=(f"Your ₱{invoice.amount:,.2f} refund for INV-{invoice.id:04d} is ready. Open this PayMongo link "
                     f"within 3 days to send it to your bank or e-wallet: {row['transfer_link']}"),
        )
    try:
        state = paymongo_status(invoice, service)
    except PaymentGatewayError:
        state = {**state, "refunds": state["refunds"] + [row]}
    apply_confirmed_refund(invoice, state, user)
    return state, row


def sync_refunds_for(invoices):
    """Refund-pending invoices whose PayMongo refund has since succeeded
    become Refunded (the client's Billing page and the admin list call
    this). Errors are skipped — it's a best-effort refresh."""
    updated = []
    service = None
    for invoice in invoices:
        if not invoice_payment_id(invoice):
            continue
        service = service or PayMongoService()
        try:
            state = paymongo_status(invoice, service)
        except PaymentGatewayError:
            continue
        if apply_confirmed_refund(invoice, state):
            updated.append(invoice.id)
    return updated
