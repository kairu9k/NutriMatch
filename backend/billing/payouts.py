"""Monthly RND payouts (2026-10-10, user's rules, Roblox-style).

An RND's share of a consultation (invoice amount minus its frozen
commission) moves through:
  Pending   — paid, but not completed yet, or completed < HOLD_DAYS ago
              (time for a refund if the client reports a problem)
  Posted    — cleared, waiting for the next payout day
  Paid out  — included in a Payout the admin released
Payout day is the 5th of every month. A payout needs at least
MIN_PAYOUT posted and the RND's payout details (GCash/bank) on file;
smaller balances carry over. Money moves outside the app — the admin sends
it and records the reference here."""

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

HOLD_DAYS = 3
MIN_PAYOUT = Decimal("500.00")
PAYOUT_DAY = 5


def rnd_share(invoice):
    return (invoice.amount or Decimal("0")) - (invoice.commission_amt or Decimal("0"))


def next_payout_date(today=None):
    today = today or timezone.localdate()
    if today.day <= PAYOUT_DAY:
        return today.replace(day=PAYOUT_DAY)
    month = today.month % 12 + 1
    year = today.year + (1 if today.month == 12 else 0)
    return date(year, month, PAYOUT_DAY)


def invoice_state(invoice, now=None):
    """'pending' | 'posted' | 'paid_out' | None (doesn't count: unpaid,
    cancelled, refunded…)."""
    from .models import Invoice

    if invoice.status != Invoice.Status.PAID:
        return None
    if invoice.payout_id:
        return "paid_out"
    appt = invoice.appointment
    if appt is None:
        return "posted"  # an invoice without an appointment (legacy/manual)
    if appt.status != "completed" or appt.completed_at is None:
        return "pending"
    now = now or timezone.now()
    return "posted" if appt.completed_at + timedelta(days=HOLD_DAYS) <= now else "pending"


def posted_until(invoice):
    appt = invoice.appointment
    if appt is not None and appt.completed_at:
        return appt.completed_at + timedelta(days=HOLD_DAYS)
    return None


def rnd_earnings(rnd, now=None):
    """Balances + per-invoice rows for one RND."""
    from .models import Invoice

    now = now or timezone.now()
    invoices = (
        Invoice.objects.filter(relationship__rnd=rnd, status=Invoice.Status.PAID)
        .select_related("appointment", "relationship__client")
        .order_by("-paid_at")
    )
    totals = {"pending": Decimal("0"), "posted": Decimal("0"), "paid_out": Decimal("0")}
    rows = []
    for inv in invoices:
        state = invoice_state(inv, now)
        if state is None:
            continue
        share = rnd_share(inv)
        totals[state] += share
        rows.append({
            "invoice_id": inv.id,
            "client_name": inv.relationship.client.full_name,
            "appointment_date": inv.appointment.scheduled_at if inv.appointment else None,
            "amount": inv.amount,
            "commission": inv.commission_amt,
            "share": share,
            "state": state,
            "posts_on": posted_until(inv) if state == "pending" else None,
            "payout_id": inv.payout_id,
        })
    account = getattr(rnd, "payout_account", None)
    return {
        **{k: v.quantize(Decimal("0.01")) for k, v in totals.items()},
        "next_payout_date": next_payout_date(timezone.localdate(now)),
        "minimum_payout": MIN_PAYOUT,
        "hold_days": HOLD_DAYS,
        "has_payout_account": account is not None,
        "eligible": account is not None and totals["posted"] >= MIN_PAYOUT,
        "items": rows,
    }


class PayoutError(Exception):
    pass


def release_payout(rnd, *, reference, released_by, notes=""):
    """Pay out everything the RND has Posted (admin sent the money already)."""
    from communication.services import notify
    from core.models import AuditLog

    from .models import Invoice, PaymentTransaction, Payout

    reference = (reference or "").strip()
    if not reference:
        raise PayoutError("Enter the GCash/bank transfer reference number.")
    account = getattr(rnd, "payout_account", None)
    if account is None:
        raise PayoutError("This RND hasn't added their payout details yet.")
    now = timezone.now()
    with transaction.atomic():
        candidates = list(
            Invoice.objects.select_for_update()
            .filter(relationship__rnd=rnd, status=Invoice.Status.PAID, payout__isnull=True)
            .select_related("appointment")
        )
        posted = [inv for inv in candidates if invoice_state(inv, now) == "posted"]
        amount = sum((rnd_share(inv) for inv in posted), Decimal("0")).quantize(Decimal("0.01"))
        if amount < MIN_PAYOUT:
            raise PayoutError(f"Posted balance is ₱{amount:,.2f} — the minimum payout is ₱{MIN_PAYOUT:,.0f}. It carries over.")
        payout = Payout.objects.create(
            # The month's payout run it belongs to (the 5th), even if released a little early/late.
            rnd=rnd, amount=amount, payout_date=timezone.localdate(now).replace(day=PAYOUT_DAY),
            method=account.method, account_name=account.account_name, account_number=account.account_number,
            bank_name=account.bank_name, reference=reference[:100], notes=(notes or "").strip()[:1000] or None,
            released_by=released_by, released_at=now,
        )
        Invoice.objects.filter(id__in=[inv.id for inv in posted]).update(payout=payout)
        PaymentTransaction.objects.bulk_create([
            PaymentTransaction(
                invoice=inv, transaction_type=PaymentTransaction.TransactionType.PAYOUT, amount=rnd_share(inv),
                status="success", gateway_payload={"payout_id": payout.id, "reference": payout.reference}, processed_at=now,
            )
            for inv in posted
        ])
        AuditLog.objects.create(
            user=released_by, action="payout.released", table_name="payouts", record_id=payout.id,
            new_values={"rnd_id": rnd.id, "amount": str(amount), "invoices": [inv.id for inv in posted], "reference": payout.reference},
        )
    method = account.get_method_display()
    notify(
        recipient=rnd, notifiable_type="payout", notifiable_id=payout.id,
        subject="Payout sent",
        content=f"Your ₱{amount:,.2f} payout was sent to your {method} account ({account.account_number}). Reference: {payout.reference}.",
    )
    try:
        send_payout_email(payout)
    except Exception:
        pass  # the payout is recorded either way; the in-app notification still goes out
    return payout


def send_payout_email(payout):
    """The "payout sent" email (also used by the RND's Resend button).
    Uses the payout's own snapshot of the account it went to."""
    from accounts.emails import send_notice_email

    count = payout.invoices.count()
    method = "GCash" if payout.method == "gcash" else (payout.bank_name or "Bank transfer")
    send_notice_email(
        payout.rnd,
        subject=f"Your NutriMatch payout of ₱{payout.amount:,.2f} was sent",
        heading="Your payout is on its way 💸",
        paragraphs=[
            f"We've sent your earnings for {count} consultation{'s' if count != 1 else ''} to your {method} account.",
            "Salamat for caring for your clients on NutriMatch!",
        ],
        highlight=f"Amount: ₱{payout.amount:,.2f} · {method} {payout.account_number} · Reference: {payout.reference}",
        button_label="View my earnings", button_url=f"{_frontend()}/earnings",
        preheader=f"₱{payout.amount:,.2f} sent to your {method} account.",
    )


def _frontend():
    from django.conf import settings

    return settings.FRONTEND_URL


# Every invoice for an RND's patients, for the Earnings page — not just the
# ones that count toward a payout (those are rnd_earnings above).
STATEMENT_STATES = {
    "unpaid": "awaiting_payment", "refund_pending": "refund_pending", "refunded": "refunded", "cancelled": "voided",
}


def rnd_statement(rnd, now=None):
    from .models import Invoice

    now = now or timezone.now()
    rows = []
    invoices = (Invoice.objects.filter(relationship__rnd=rnd)
                .select_related("appointment", "relationship__client", "payout").order_by("-created_at"))
    for inv in invoices:
        state = invoice_state(inv, now) or STATEMENT_STATES.get(inv.status, inv.status)
        appt = inv.appointment
        rows.append({
            "invoice_id": inv.id,
            "client_name": inv.relationship.client.full_name,
            "consultation_at": appt.scheduled_at if appt else None,
            "consultation_type": appt.get_type_display() if appt else None,
            "amount": inv.amount,
            "commission_pct": inv.commission_pct,
            "commission": inv.commission_amt,
            "share": rnd_share(inv),
            "state": state,
            "posts_on": posted_until(inv) if state == "pending" else None,
            "paid_at": inv.paid_at,
            "payment_method": inv.get_payment_method_display() if inv.payment_method else None,
            "issued_at": inv.created_at,
            "payout": {"id": inv.payout.id, "released_at": inv.payout.released_at, "reference": inv.payout.reference} if inv.payout_id else None,
        })
    return rows
