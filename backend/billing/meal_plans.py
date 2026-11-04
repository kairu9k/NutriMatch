"""Paid meal plans (2026-11-04, user's call).

A client books "Consultation only" or "Consultation + meal plan" (the
package). A consultation-only patient can still get a plan later: the RND
recommends one and the client pays an add-on invoice for the difference
(meal_plan_fee - consultation_fee, frozen when offered).

A paid package or add-on invoice is a meal-plan credit. Sending a plan to the
client uses one credit (MealPlan.invoice) and the sent plan is then locked: an
RND edits a plan only while it is a draft. A new or updated plan needs a new
credit.

Add-on invoices have no appointment (much of billing assumes one invoice per
appointment); the RND's share posts HOLD_DAYS after the plan is sent
(billing/payouts.py)."""

from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

OFFER_DAYS = 7           # an unpaid add-on offer expires after this
NOT_SENT_ALERT_DAYS = 7  # admin attention: paid but no plan sent after this
OFFER_NOTE_MAX = 500


def commission_kwargs():
    """Commission % frozen on a new invoice (SystemSetting or the model default)."""
    from core.models import SystemSetting

    setting = SystemSetting.objects.filter(key="platform_commission_pct").first()
    if setting and setting.value:
        try:
            return {"commission_pct": Decimal(setting.value)}
        except (InvalidOperation, TypeError):
            pass
    return {}


def offers_meal_plans(profile):
    return bool(profile and profile.meal_plan_fee and profile.meal_plan_fee > (profile.consultation_fee or 0))


def addon_price(profile):
    """What a consultation-only patient pays for a plan afterwards."""
    if not offers_meal_plans(profile):
        return None
    return (profile.meal_plan_fee - profile.consultation_fee).quantize(Decimal("0.01"))


def _credit_kinds():
    from .models import Invoice

    return [Invoice.Kind.PACKAGE, Invoice.Kind.MEAL_PLAN_ADDON]


def unused_credit(relationship):
    """The oldest paid package / add-on invoice no sent plan has used yet."""
    from .models import Invoice

    return (Invoice.objects.filter(relationship=relationship, kind__in=_credit_kinds(), status=Invoice.Status.PAID)
            .exclude(meal_plans__first_sent_at__isnull=False)
            .order_by("paid_at", "id").first())


def offer_expires_at(invoice):
    return invoice.created_at + timedelta(days=OFFER_DAYS)


def open_offer(relationship):
    from .models import Invoice

    return (Invoice.objects.filter(relationship=relationship, kind=Invoice.Kind.MEAL_PLAN_ADDON,
                                   status=Invoice.Status.UNPAID,
                                   created_at__gt=timezone.now() - timedelta(days=OFFER_DAYS))
            .order_by("-created_at").first())


def offer_payload(invoice):
    if invoice is None:
        return None
    return {"invoice_id": invoice.id, "amount": invoice.amount, "note": invoice.offer_note or "",
            "created_at": invoice.created_at, "expires_at": offer_expires_at(invoice)}


def meal_plan_access(relationship):
    """What the screens need: can a plan be sent, is one on offer, prices."""
    profile = getattr(relationship.rnd, "rnd_profile", None)
    credit = unused_credit(relationship)
    offer = open_offer(relationship)
    return {
        "offered": offers_meal_plans(profile),
        "consultation_fee": profile.consultation_fee if profile else None,
        "meal_plan_fee": profile.meal_plan_fee if offers_meal_plans(profile) else None,
        "addon_price": addon_price(profile),
        "credit": {"invoice_id": credit.id, "kind": credit.kind, "paid_at": credit.paid_at} if credit else None,
        "offer": offer_payload(offer),
        "can_send": credit is not None,
        "can_offer": (relationship.status == "active" and credit is None and offer is None and offers_meal_plans(profile)),
    }


NO_CREDIT_MESSAGE = ("This patient hasn't paid for a meal plan. Recommend one to them, or they can book "
                     "\"Consultation + meal plan\".")
LOCKED_MESSAGE = "A sent meal plan can't be changed. Start a new plan from it instead."


def ensure_editable(plan):
    """Only drafts can be edited (2026-11-04): a sent plan is final."""
    from rest_framework.exceptions import PermissionDenied

    if plan.first_sent_at:
        raise PermissionDenied(LOCKED_MESSAGE)


# ---------------------------------------------------------------------------
# Add-on offers
# ---------------------------------------------------------------------------

def _frontend(path):
    return f"{settings.FRONTEND_URL.rstrip('/')}{path}"


def create_offer(relationship, rnd, note=""):
    """The RND recommends a meal plan: an unpaid add-on invoice for the
    difference, frozen now with its commission. The client is told."""
    from communication.services import notify
    from core.models import AuditLog

    from .models import Invoice

    if relationship.status != "active":
        raise serializers.ValidationError({"detail": "You can recommend a meal plan only to an active patient."})
    profile = getattr(rnd, "rnd_profile", None)
    price = addon_price(profile)
    if price is None:
        raise serializers.ValidationError({"detail": "Set your meal plan price in Profile Settings first."})
    if unused_credit(relationship):
        raise serializers.ValidationError({"detail": "This patient has already paid for a meal plan. Create and send it."})
    if open_offer(relationship):
        raise serializers.ValidationError({"detail": "You already recommended a meal plan. It's waiting for the patient's payment."})
    note = (note or "").strip()[:OFFER_NOTE_MAX]
    with transaction.atomic():
        invoice = Invoice.objects.create(relationship=relationship, kind=Invoice.Kind.MEAL_PLAN_ADDON,
                                         amount=price, offer_note=note or None, **commission_kwargs())
        AuditLog.objects.create(user=rnd, action="meal_plan.offered", table_name="invoices", record_id=invoice.id,
                                new_values={"relationship_id": relationship.id, "amount": str(price)})
        client = relationship.client
        notify(recipient=client, notifiable_type="invoice", notifiable_id=invoice.id,
               subject="Your RND recommends a meal plan",
               content=(f"RND {rnd.full_name} recommends a 7-day meal plan made for you, ₱{price:,.2f}. "
                        f"Pay in Billing within {OFFER_DAYS} days and they'll start your plan." + (f" Note: {note}" if note else "")))

        def _email():
            from accounts.emails import send_notice_email

            try:
                send_notice_email(
                    client, subject=f"RND {rnd.full_name} recommends a meal plan for you",
                    heading="Your RND recommends a meal plan",
                    paragraphs=[
                        f"After your consultation, RND {rnd.full_name} recommends a 7-day meal plan made for you: "
                        "your meals, portions and targets, with meal logging so they can follow your progress.",
                        f"Pay ₱{price:,.2f} in the app within {OFFER_DAYS} days and your RND will start your plan. "
                        "If you'd rather not, you can say Not now.",
                    ],
                    highlight=f"Note from your RND: {note}" if note else "",
                    button_label="Open Billing", button_url=_frontend("/invoices-billing"),
                    preheader=f"A meal plan from RND {rnd.full_name}, ₱{price:,.2f}.",
                )
            except Exception:  # best effort
                pass

        transaction.on_commit(_email)
    return invoice


def decline_offer(invoice, client):
    """The client says Not now: the offer is cancelled and the RND told."""
    from communication.services import notify

    from .models import Invoice

    if invoice.kind != Invoice.Kind.MEAL_PLAN_ADDON or invoice.status != Invoice.Status.UNPAID:
        raise serializers.ValidationError({"detail": "This offer can't be declined anymore."})
    invoice.status = Invoice.Status.CANCELLED
    invoice.save(update_fields=["status"])
    rel = invoice.relationship
    notify(recipient=rel.rnd, notifiable_type="relationship", notifiable_id=rel.id,
           subject="Meal plan declined",
           content=f"{client.full_name} said not now to the meal plan you recommended. You can recommend one again later.")
    return invoice


def expire_offers(**scope):
    """Unpaid add-on offers older than OFFER_DAYS are cancelled (run lazily
    with expire_unpaid_appointments). Returns how many."""
    from communication.services import notify

    from .models import Invoice

    cutoff = timezone.now() - timedelta(days=OFFER_DAYS)
    due = (Invoice.objects.filter(kind=Invoice.Kind.MEAL_PLAN_ADDON, status=Invoice.Status.UNPAID,
                                  created_at__lte=cutoff, **scope)
           .select_related("relationship__client", "relationship__rnd"))
    count = 0
    for inv in due:
        inv.status = Invoice.Status.CANCELLED
        inv.save(update_fields=["status"])
        rel = inv.relationship
        notify(recipient=rel.client, notifiable_type="invoice", notifiable_id=inv.id, subject="Meal plan offer expired",
               content=f"The meal plan RND {rel.rnd.full_name} recommended wasn't paid within {OFFER_DAYS} days, so the offer ended. "
                       "Ask your RND if you'd still like one.")
        notify(recipient=rel.rnd, notifiable_type="relationship", notifiable_id=rel.id, subject="Meal plan offer expired",
               content=f"{rel.client.full_name} didn't pay for the meal plan you recommended within {OFFER_DAYS} days. You can recommend one again.")
        count += 1
    return count


def notify_rnd_plan_paid(invoice_id):
    from communication.services import notify

    from .models import Invoice

    inv = Invoice.objects.select_related("relationship__client", "relationship__rnd").get(pk=invoice_id)
    rel = inv.relationship
    notify(recipient=rel.rnd, notifiable_type="relationship", notifiable_id=rel.id, subject="Meal plan paid",
           content=f"{rel.client.full_name} paid ₱{inv.amount:,.2f} for the meal plan you recommended. Create and send their plan.")


# ---------------------------------------------------------------------------
# When care ends
# ---------------------------------------------------------------------------

def settle_on_discharge(relationship):
    """Care ended: an open offer is cancelled; a paid add-on whose plan was
    never sent is refunded (refund pending, the client told). A package
    whose plan was never sent shows on the admin's Needs attention list
    instead (only part of it is owed back; PayMongo refunds are whole)."""
    from communication.services import notify

    from .models import Invoice
    from .services import REFUND_WINDOW, refund_note

    Invoice.objects.filter(relationship=relationship, kind=Invoice.Kind.MEAL_PLAN_ADDON,
                           status=Invoice.Status.UNPAID).update(status=Invoice.Status.CANCELLED)
    unused = (Invoice.objects.filter(relationship=relationship, kind=Invoice.Kind.MEAL_PLAN_ADDON,
                                     status=Invoice.Status.PAID)
              .exclude(meal_plans__first_sent_at__isnull=False))
    for inv in unused:
        inv.status = Invoice.Status.REFUND_PENDING
        inv.save(update_fields=["status"])
        notify(recipient=relationship.client, notifiable_type="invoice", notifiable_id=inv.id,
               subject="Refund being processed",
               content=(f"Your care ended before your meal plan was sent, so your ₱{inv.amount:,.2f} payment for "
                        f"INV-{inv.id:04d} will be refunded within {REFUND_WINDOW}. {refund_note(inv.payment_method)}").strip())


def undelivered_plans(now=None):
    """Paid meal plans not sent after NOT_SENT_ALERT_DAYS (admin attention):
    add-ons paid that long ago, and packages whose consultation was completed
    that long ago."""
    from django.db.models import Q

    from .models import Invoice

    cutoff = (now or timezone.now()) - timedelta(days=NOT_SENT_ALERT_DAYS)
    return (Invoice.objects.filter(kind__in=_credit_kinds(), status=Invoice.Status.PAID)
            .filter(Q(kind=Invoice.Kind.MEAL_PLAN_ADDON, paid_at__lte=cutoff)
                    | Q(kind=Invoice.Kind.PACKAGE, appointment__completed_at__lte=cutoff))
            .exclude(meal_plans__first_sent_at__isnull=False)
            .select_related("relationship__client", "relationship__rnd"))
