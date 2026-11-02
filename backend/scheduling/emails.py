"""Consultation emails (2026-11-02, user's call): the events with money or a
deadline also go by email, whatever the reminder settings, because an in-app
notification alone is easy to miss:

- the client was marked as not attending (3 days to dispute)
- the RND confirmed the booking (pay by the deadline or it's cancelled)
- the RND cancelled (emergency, the call didn't work, or a normal cancel)
- the RND is told they missed a consultation (the client reported it)

Sent after the database commit, best effort: a failed email never breaks the
action. No health details and never the RND's private notes (RA 10173); free
text reasons stay in the app."""

import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


def _send(user, **kwargs):
    from accounts.emails import send_notice_email

    def go():
        try:
            send_notice_email(user, **kwargs)
        except Exception:  # noqa: BLE001 — best effort
            logger.exception("Consultation email to user %s failed", user.pk)

    transaction.on_commit(go)


def _when(dt):
    from .views import format_ph_datetime

    return format_ph_datetime(dt)


def _link(path):
    return f"{settings.FRONTEND_URL}{path}"


def email_no_show(appointment):
    from .serializers import DISPUTE_DAYS

    client, rnd = appointment.relationship.client, appointment.relationship.rnd
    until = _when(appointment.completed_at + timedelta(days=DISPUTE_DAYS)) if appointment.completed_at else None
    _send(
        client,
        subject=f"You were marked as not attending your consultation on {_when(appointment.scheduled_at)}",
        heading="You were marked as not attending",
        paragraphs=[
            f"RND {rnd.full_name} marked your consultation on {_when(appointment.scheduled_at)} as not attended, "
            "so the payment isn't refunded.",
            "If you were there or something went wrong, you can dispute it. NutriMatch reviews it with the video "
            "call's attendance record (only who joined and when) and either refunds you or keeps the no-show.",
        ],
        highlight=f"Dispute by {until} from My Appointments, History." if until else "",
        button_label="Open My Appointments",
        button_url=_link("/appointments"),
        preheader=f"No refund unless you dispute it{f' by {until}' if until else ''}.",
    )


def email_confirmed(appointment, invoice):
    from .serializers import deadlines
    from .views import format_ph_short

    client, rnd = appointment.relationship.client, appointment.relationship.rnd
    d = deadlines(appointment)
    pay_by = format_ph_short(d["pay_by"])
    _send(
        client,
        subject=f"Your consultation on {_when(appointment.scheduled_at)} is confirmed. Pay before {pay_by}",
        heading="Your consultation is confirmed",
        paragraphs=[
            f"RND {rnd.full_name} confirmed your {appointment.get_type_display().lower()} consultation on "
            f"{_when(appointment.scheduled_at)}.",
            f"You can pay ₱{invoice.amount:,.2f} (INV-{invoice.id:04d}) any time now. The last moment is {pay_by}, "
            "15 minutes before the start. If it isn't paid by then, the booking is cancelled and the time is released.",
            f"Once paid, you can cancel for a full refund until {format_ph_short(d['cancel_by'])}, 30 minutes before the start. "
            "If you don't attend, there's no refund.",
        ],
        highlight=f"Pay ₱{invoice.amount:,.2f} any time before {pay_by}",
        button_label="Pay now",
        button_url=_link("/invoices-billing"),
        preheader=f"Pay ₱{invoice.amount:,.2f} any time before {pay_by} to keep your booking.",
    )


def email_cancelled_by_rnd(appointment, *, kind, paid_amount=None):
    """kind: emergency | technical | other (a last-minute cancel), call_failed, or normal."""
    client, rnd = appointment.relationship.client, appointment.relationship.rnd
    when = _when(appointment.scheduled_at)
    opening = {
        "emergency": f"RND {rnd.full_name} had to cancel your consultation on {when} because of an emergency.",
        "technical": f"RND {rnd.full_name} had to cancel your consultation on {when} because of a technical problem.",
        "other": f"RND {rnd.full_name} had to cancel your consultation on {when}.",
        "call_failed": f"Your consultation on {when} with RND {rnd.full_name} was ended because the video call didn't work.",
    }.get(kind, f"RND {rnd.full_name} cancelled your consultation on {when}.")
    paragraphs = [opening]
    if paid_amount:
        paragraphs.append(f"You get your full ₱{paid_amount:,.2f} back within 5–7 business days.")
    paragraphs.append("You can see the details in NutriMatch and book a new time whenever you're ready.")
    _send(
        client,
        subject=f"Your consultation on {when} was cancelled",
        heading="Your consultation was cancelled",
        paragraphs=paragraphs,
        button_label="Open My Appointments",
        button_url=_link("/appointments"),
        preheader=opening,
    )


def email_rnd_missed(appointment):
    client, rnd = appointment.relationship.client, appointment.relationship.rnd
    _send(
        rnd,
        subject=f"You missed a consultation on {_when(appointment.scheduled_at)}",
        heading="You missed a consultation",
        paragraphs=[
            f"{client.full_name} waited in the video call for your consultation on {_when(appointment.scheduled_at)} "
            "and you didn't join, so it was cancelled and their payment is refunded.",
            "Missed consultations and last-minute cancels are noted for NutriMatch. "
            "If this is wrong, contact NutriMatch support from Help & Support.",
        ],
        button_label="Open Appointments",
        button_url=_link("/appointments?tab=history"),
        preheader=f"{client.full_name}'s consultation was cancelled and refunded.",
    )
