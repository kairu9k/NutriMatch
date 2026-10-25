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
it and records the reference here.

No early payouts, no exceptions (user's rule, 2026-10-26): each run (the 5th)
pays only shares that were Posted on or before that 5th, Philippine date.
A run can be released late (on the 6th, the 20th...), but money that posted
after its 5th always waits for the next run."""

from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from core.ph_time import ph_date

HOLD_DAYS = 3
MIN_PAYOUT = Decimal("500.00")
PAYOUT_DAY = 5
# payout details changed this recently need the RND's confirmation first
RECENT_CHANGE_DAYS = 7
# a GCash or bank receipt reference has at least this many letters/digits
MIN_REFERENCE_CHARS = 6


def rnd_share(invoice):
    return (invoice.amount or Decimal("0")) - (invoice.commission_amt or Decimal("0"))


def next_payout_date(today=None):
    from core.ph_time import ph_today

    today = today or ph_today()
    if today.day <= PAYOUT_DAY:
        return today.replace(day=PAYOUT_DAY)
    month = today.month % 12 + 1
    year = today.year + (1 if today.month == 12 else 0)
    return date(year, month, PAYOUT_DAY)


def details_recently_changed(account, now=None):
    changed = getattr(account, "details_changed_at", None)
    return bool(changed and changed >= (now or timezone.now()) - timedelta(days=RECENT_CHANGE_DAYS))


def check_reference(reference, account):
    """A real receipt reference: long enough, and not the account number typed
    into the wrong box. Returns the cleaned reference."""
    import re

    reference = (reference or "").strip()
    if not reference:
        raise PayoutError("Enter the GCash or bank reference number from the receipt.")
    if len(re.sub(r"[^0-9A-Za-z]", "", reference)) < MIN_REFERENCE_CHARS:
        raise PayoutError(f"That reference is too short. Copy the full reference number from the receipt (at least {MIN_REFERENCE_CHARS} letters or digits).")
    digits = re.sub(r"\D", "", reference)
    account_digits = re.sub(r"\D", "", account.account_number or "")
    if account_digits and digits.endswith(account_digits[-10:]) and len(digits) <= len(account_digits) + 2:
        raise PayoutError("That's the RND's account number, not the receipt's reference number. Copy the reference from the GCash or bank receipt.")
    return reference


def last_payout_day(today=None):
    """The most recent payout day (the run whose money can be paid now)."""
    from core.ph_time import ph_today

    today = today or ph_today()
    if today.day >= PAYOUT_DAY:
        return today.replace(day=PAYOUT_DAY)
    if today.month == 1:
        return date(today.year - 1, 12, PAYOUT_DAY)
    return date(today.year, today.month - 1, PAYOUT_DAY)


def in_run(invoice, run_day):
    """A Posted share belongs to the run of `run_day` if it posted on or
    before that day (an invoice with no completed appointment counts)."""
    until = posted_until(invoice)
    return until is None or ph_date(until) <= run_day


def invoice_state(invoice, now=None):
    """'pending' | 'posted' | 'sending' | 'paid_out' | None (doesn't count:
    unpaid, cancelled, refunded…). 'sending' = in a Xendit payout that hasn't
    succeeded yet."""
    from .models import Invoice

    if invoice.status != Invoice.Status.PAID:
        return None
    if invoice.payout_id:
        return "paid_out" if invoice.payout.status == "paid" else "sending"
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
        .select_related("appointment", "relationship__client", "payout")
        .order_by("-paid_at")
    )
    totals = {"pending": Decimal("0"), "posted": Decimal("0"), "sending": Decimal("0"), "paid_out": Decimal("0"), "payable": Decimal("0")}
    run_day = last_payout_day(ph_date(now))
    rows = []
    for inv in invoices:
        state = invoice_state(inv, now)
        if state is None:
            continue
        share = rnd_share(inv)
        totals[state] += share
        payable = state == "posted" and in_run(inv, run_day)
        if payable:
            totals["payable"] += share
        rows.append({
            "invoice_id": inv.id,
            "client_name": inv.relationship.client.full_name,
            "appointment_date": inv.appointment.scheduled_at if inv.appointment else None,
            "amount": inv.amount,
            "commission": inv.commission_amt,
            "share": share,
            "state": state,
            "posts_on": posted_until(inv) if state == "pending" else None,
            "payable": payable,
            "payout_id": inv.payout_id,
        })
    account = getattr(rnd, "payout_account", None)
    return {
        **{k: v.quantize(Decimal("0.01")) for k, v in totals.items()},
        "next_payout_date": next_payout_date(ph_date(now)),
        "run_date": run_day,
        "minimum_payout": MIN_PAYOUT,
        "hold_days": HOLD_DAYS,
        "has_payout_account": account is not None,
        # only what posted by the last 5th can be paid now
        "eligible": account is not None and totals["payable"] >= MIN_PAYOUT,
        "items": rows,
    }


class PayoutError(Exception):
    pass


def _reserve(rnd, account, now, expected_amount, details_confirmed):
    """The checks every payout needs, then the invoices it covers, locked
    (call inside transaction.atomic()). Returns (run_day, invoices, amount)."""
    from .models import Invoice

    if details_recently_changed(account, now) and not details_confirmed:
        raise PayoutError(f"These payout details changed in the last {RECENT_CHANGE_DAYS} days. "
                          "Confirm the number with the RND before sending, then tick the confirmation.")
    try:
        expected = Decimal(str(expected_amount)).quantize(Decimal("0.01"))
    except Exception:  # noqa: BLE001 - missing or not a number
        raise PayoutError("Reload the page and try again: the amount you saw wasn't sent with the request.")
    candidates = list(
        Invoice.objects.select_for_update()
        .filter(relationship__rnd=account.rnd, status=Invoice.Status.PAID, payout__isnull=True)
        .select_related("appointment")
    )
    run_day = last_payout_day(ph_date(now))
    posted = [inv for inv in candidates if invoice_state(inv, now) == "posted" and in_run(inv, run_day)]
    amount = sum((rnd_share(inv) for inv in posted), Decimal("0")).quantize(Decimal("0.01"))
    if amount < MIN_PAYOUT:
        later = [inv for inv in candidates if invoice_state(inv, now) == "posted" and not in_run(inv, run_day)]
        if later and not posted:
            nxt = next_payout_date(ph_date(now))
            raise PayoutError(f"Nothing from the {run_day:%B} {run_day.day} run is left to pay. "
                              f"Money that cleared after that is paid on {nxt:%B} {nxt.day}.")
        raise PayoutError(f"The balance for the {run_day:%B} {run_day.day} run is ₱{amount:,.2f}. "
                          f"The minimum payout is ₱{MIN_PAYOUT:,.0f}, so it carries over.")
    if amount != expected:
        # a refund or a newly cleared consultation landed after the page was opened
        raise PayoutError(f"The amount changed to ₱{amount:,.2f} since you opened this (you saw ₱{expected:,.2f}). "
                          "Nothing was sent or recorded. Reload the page and check the new amount.")
    return run_day, posted, amount


def _new_payout(rnd, account, run_day, amount, *, reference, released_by, notes, now, **extra):
    from .models import Payout

    return Payout.objects.create(
        # the run it belongs to: the last 5th (released on it or later, never earlier)
        rnd=rnd, amount=amount, payout_date=run_day,
        method=account.method, account_name=account.account_name, account_number=account.account_number,
        bank_name=account.bank_name, reference=reference[:100], notes=(notes or "").strip()[:1000] or None,
        released_by=released_by, released_at=now, **extra,
    )


def _book_paid(payout, invoices, now):
    """Payout transactions + the payout.released audit row, once it is paid."""
    from core.models import AuditLog

    from .models import PaymentTransaction

    PaymentTransaction.objects.bulk_create([
        PaymentTransaction(
            invoice=inv, transaction_type=PaymentTransaction.TransactionType.PAYOUT, amount=rnd_share(inv),
            status="success", gateway_payload={"payout_id": payout.id, "reference": payout.reference,
                                               "provider": payout.provider}, processed_at=now,
        )
        for inv in invoices
    ])
    AuditLog.objects.create(
        user=payout.released_by, action="payout.released", table_name="payouts", record_id=payout.id,
        new_values={"rnd_id": payout.rnd_id, "amount": str(payout.amount), "invoices": [inv.id for inv in invoices],
                    "reference": payout.reference, "provider": payout.provider, "test_mode": payout.test_mode},
    )


def _announce(payout):
    """Tell the RND (notification + email) once the money is really out."""
    from communication.services import notify

    from .models import payout_destination

    method = payout_destination(payout.method, payout.bank_name)
    notify(
        recipient=payout.rnd, notifiable_type="payout", notifiable_id=payout.id,
        subject="Payout sent",
        content=f"Your ₱{payout.amount:,.2f} payout was sent to your {method} account ({payout.account_number}). Reference: {payout.reference}.",
    )
    try:
        send_payout_email(payout)
    except Exception:
        pass  # the payout is recorded either way; the in-app notification still goes out


def release_payout(rnd, *, reference, released_by, notes="", expected_amount=None, details_confirmed=False):
    """Record a payout the admin already sent by hand (the fallback)."""
    from .models import Invoice

    account = getattr(rnd, "payout_account", None)
    if account is None:
        raise PayoutError("This RND hasn't added their payout details yet.")
    reference = check_reference(reference, account)
    now = timezone.now()
    with transaction.atomic():
        run_day, posted, amount = _reserve(rnd, account, now, expected_amount, details_confirmed)
        payout = _new_payout(rnd, account, run_day, amount, reference=reference, released_by=released_by, notes=notes, now=now,
                             settled_at=now)
        Invoice.objects.filter(id__in=[inv.id for inv in posted]).update(payout=payout)
        _book_paid(payout, posted, now)
    _announce(payout)
    return payout


def send_payout_via_xendit(rnd, *, released_by, notes="", expected_amount=None, details_confirmed=False):
    """NutriMatch sends the payout through Xendit (billing/xendit.py).

    The invoices are reserved for the payout first (status "sending"), so a
    second click can't send them again; Xendit's payout id becomes the
    reference; it turns Paid out only when Xendit reports SUCCEEDED, and a
    refused or failed transfer releases the invoices again."""
    from core.models import AuditLog

    from . import xendit
    from .models import Invoice, Payout

    if not xendit.configured():
        raise PayoutError("Xendit isn't set up on this server. Record the payout by hand instead.")
    account = getattr(rnd, "payout_account", None)
    if account is None:
        raise PayoutError("This RND hasn't added their payout details yet.")
    channel = xendit.channel_for(account)
    if channel is None:
        raise PayoutError(f"Xendit can't send to {account.bank_name or account.get_method_display()}. "
                          "Send it yourself and record it by hand.")
    now = timezone.now()
    with transaction.atomic():
        run_day, posted, amount = _reserve(rnd, account, now, expected_amount, details_confirmed)
        payout = _new_payout(rnd, account, run_day, amount, reference="Waiting for Xendit", released_by=released_by,
                             notes=notes, now=now, provider=Payout.Provider.XENDIT, status=Payout.Status.SENDING,
                             test_mode=xendit.is_test_mode())
        Invoice.objects.filter(id__in=[inv.id for inv in posted]).update(payout=payout)
        AuditLog.objects.create(
            user=released_by, action="payout.sent", table_name="payouts", record_id=payout.id,
            new_values={"rnd_id": rnd.id, "amount": str(amount), "invoices": [inv.id for inv in posted],
                        "provider": "xendit", "channel": channel, "test_mode": payout.test_mode},
        )
    try:
        result = xendit.create_payout(
            idempotency_key=f"nutrimatch-payout-{payout.id}", reference_id=f"PO-{payout.id:04d}", channel_code=channel,
            account_name=account.account_name, account_number=account.account_number, amount=amount,
            description=f"NutriMatch payout PO-{payout.id:04d} for the {run_day:%B} {run_day.day} run",
        )
    except xendit.XenditError as exc:
        mark_payout_failed(payout, "NOT_SENT", str(exc))
        raise PayoutError(f"{exc} Nothing was sent, and the balance is ready again.") from exc
    Payout.objects.filter(pk=payout.pk).update(provider_payout_id=result.get("id"), reference=(result.get("id") or "")[:100])
    payout.refresh_from_db()
    apply_xendit_status(payout, result)
    payout.refresh_from_db()
    return payout


def apply_xendit_status(payout, result):
    """Act on what Xendit says about a payout we sent."""
    from . import xendit

    status = (result.get("status") or "").upper()
    if status in xendit.SUCCEEDED:
        mark_payout_paid(payout)
    elif status in xendit.FAILED:
        mark_payout_failed(payout, result.get("failure_code") or status, None)


def mark_payout_paid(payout):
    from .models import Payout

    now = timezone.now()
    with transaction.atomic():
        locked = Payout.objects.select_for_update().get(pk=payout.pk)
        if locked.status != Payout.Status.SENDING:
            return  # already settled (a callback and a status check can both arrive)
        locked.status = Payout.Status.PAID
        locked.settled_at = now
        locked.save(update_fields=["status", "settled_at"])
        _book_paid(locked, list(locked.invoices.all()), now)
    _announce(locked)


def mark_payout_failed(payout, code, message):
    """The transfer didn't happen: release the invoices so they can be paid again."""
    from core.models import AuditLog

    from .models import Invoice, Payout

    with transaction.atomic():
        locked = Payout.objects.select_for_update().get(pk=payout.pk)
        if locked.status != Payout.Status.SENDING:
            return
        invoice_ids = list(locked.invoices.values_list("id", flat=True))
        Invoice.objects.filter(id__in=invoice_ids).update(payout=None)
        locked.status = Payout.Status.FAILED
        locked.failure_code = (code or "FAILED")[:100]
        locked.save(update_fields=["status", "failure_code"])
        AuditLog.objects.create(
            user=None, action="payout.failed", table_name="payouts", record_id=locked.id,
            new_values={"rnd_id": locked.rnd_id, "amount": str(locked.amount), "invoices": invoice_ids,
                        "failure_code": locked.failure_code, "message": (message or "")[:300]},
        )


def sync_sending_payouts(limit=20):
    """Ask Xendit about payouts still sending (works without a callback, e.g.
    on a laptop). Called when the admin opens Payouts. Best effort."""
    from . import xendit
    from .models import Payout

    if not xendit.configured():
        return
    for payout in Payout.objects.filter(status=Payout.Status.SENDING, provider=Payout.Provider.XENDIT,
                                        provider_payout_id__isnull=False)[:limit]:
        try:
            apply_xendit_status(payout, xendit.get_payout(payout.provider_payout_id))
        except xendit.XenditError:
            continue


def send_payout_email(payout):
    """The "payout sent" email (also used by the RND's Resend button).
    Uses the payout's own snapshot of the account it went to."""
    from accounts.emails import send_notice_email

    count = payout.invoices.count()
    from .models import payout_destination

    method = payout_destination(payout.method, payout.bank_name)
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
    run_day = last_payout_day(ph_date(now))
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
            # cleared in time for the last payout day's run (else it waits for the next)
            "payable": state == "posted" and in_run(inv, run_day),
            "paid_at": inv.paid_at,
            "payment_method": inv.get_payment_method_display() if inv.payment_method else None,
            "issued_at": inv.created_at,
            "payout": {"id": inv.payout.id, "released_at": inv.payout.released_at, "reference": inv.payout.reference} if inv.payout_id else None,
        })
    return rows
