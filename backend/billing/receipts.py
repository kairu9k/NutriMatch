"""Payment receipt emails: one to the client, one to the NutriMatch inbox
(the `support_email` system setting) for the admin team. Sent after a
payment is recorded (record_successful_payment) — best effort, a failed
email never affects the payment."""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _peso(value):
    return f"₱{value:,.2f}"


def receipt_rows(invoice):
    from scheduling.views import format_ph_datetime

    from .services import payment_receipt

    rel = invoice.relationship
    rows = [{"label": "Receipt no.", "value": f"INV-{invoice.id:04d}"}]
    appt = invoice.appointment
    if appt is not None:
        rows.append({"label": "Consultation", "value": f"{appt.get_type_display()} with RND {rel.rnd.full_name}"})
        rows.append({"label": "Scheduled", "value": format_ph_datetime(appt.scheduled_at)})
    else:
        rows.append({"label": "RND", "value": rel.rnd.full_name})
    if invoice.paid_at:
        rows.append({"label": "Paid on", "value": format_ph_datetime(invoice.paid_at)})
    if invoice.payment_method:
        rows.append({"label": "Paid via", "value": invoice.get_payment_method_display()})
    txn = invoice.transactions.filter(transaction_type="payment").order_by("-processed_at").first()
    details = payment_receipt(txn.gateway_payload) if txn and txn.gateway_payload else {}
    if details.get("card_last4"):
        rows.append({"label": "Card", "value": f"{(details.get('card_brand') or 'Card').title()} •••• {details['card_last4']}"})
    reference = details.get("payment_id") or invoice.gateway_reference_id
    if reference:
        rows.append({"label": "Payment reference", "value": reference})
    return rows


def send_payment_receipts(invoice_id):
    from accounts.emails import send_branded_email
    from core.support import support_email

    from .models import Invoice

    try:
        invoice = Invoice.objects.select_related("relationship__client", "relationship__rnd", "appointment").get(pk=invoice_id)
    except Invoice.DoesNotExist:
        return
    client = invoice.relationship.client
    rows = receipt_rows(invoice)
    refund = invoice.status == Invoice.Status.REFUND_PENDING
    total = _peso(invoice.amount)
    ref = f"INV-{invoice.id:04d}"

    client_note = (
        "This appointment had already been cancelled when the payment arrived, so it will be refunded."
        if refund else
        "Keep this email as your receipt. Join from My Appointments starting 15 minutes before the start. "
        "If you cancel before the session starts, your payment is refunded."
    )
    lines = [f"Hi {client.first_name},", "", f"We received your payment of {total} for {ref}.", ""]
    lines += [f"{r['label']}: {r['value']}" for r in rows] + ["", client_note, "", "Salamat,", "The NutriMatch Team"]
    try:
        send_branded_email(
            to=client.email,
            subject=f"Your NutriMatch receipt — {ref} ({total})",
            template="emails/receipt.html",
            context={
                "first_name": client.first_name,
                "heading": "Payment received — salamat!",
                "intro": f"We received your payment of {total}. Here's your receipt.",
                "rows": rows, "total_label": "Total paid", "total": total, "note": client_note,
                "button_label": "View my appointments", "button_url": f"{settings.FRONTEND_URL}/appointments",
            },
            text="\n".join(lines),
            preheader=f"Receipt {ref} · {total} paid",
        )
    except Exception:
        logger.exception("Could not email the receipt for invoice %s to the client", invoice_id)

    admin_rows = [{"label": "Client", "value": f"{client.full_name} ({client.email})"}] + rows
    admin_note = "This appointment was already cancelled — refund it in PayMongo, then mark it refunded in Billing & Commission." if refund else ""
    try:
        send_branded_email(
            to=support_email(),
            subject=f"Payment received — {ref} ({total}) from {client.full_name}",
            template="emails/receipt.html",
            context={
                "first_name": "NutriMatch team",
                "heading": "Payment received" if not refund else "Payment received — refund needed",
                "intro": f"{client.full_name} paid {total} for {ref}.",
                "rows": admin_rows, "total_label": "Amount", "total": total, "note": admin_note,
                "button_label": "Open Billing & Commission", "button_url": f"{settings.FRONTEND_URL}/billing-commission",
            },
            text="\n".join([f"{client.full_name} paid {total} for {ref}.", ""] + [f"{r['label']}: {r['value']}" for r in admin_rows]
                           + ([ "", admin_note] if admin_note else [])),
            preheader=f"{client.full_name} paid {total} ({ref})",
        )
    except Exception:
        logger.exception("Could not email the admin copy of the receipt for invoice %s", invoice_id)
