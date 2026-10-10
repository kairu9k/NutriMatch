from django.conf import settings
from decimal import Decimal

from django.db import models

from scheduling.models import Appointment, RndClientRelationship


class Invoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
        # A paid appointment was cancelled; an admin refunds it in PayMongo
        # and then marks it refunded (refunds aren't automated).
        REFUND_PENDING = "refund_pending", "Refund pending"
        REFUNDED = "refunded", "Refunded"

    class PaymentGateway(models.TextChoices):
        PAYMONGO = "paymongo", "PayMongo"
        STRIPE = "stripe", "Stripe"
        XENDIT = "xendit", "Xendit"
        PAYPAL = "paypal", "PayPal"
        CASH = "cash", "Cash"
        MANUAL = "manual", "Manual"

    class PaymentMethod(models.TextChoices):
        CARD = "card", "Card"
        GCASH = "gcash", "GCash"
        MAYA = "maya", "Maya"
        QRPH = "qrph", "QR Ph"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CASH = "cash", "Cash"
        OTHER = "other", "Other"

    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="invoices"
    )
    # The monthly payout that paid the RND's share of this invoice (once).
    payout = models.ForeignKey("Payout", on_delete=models.PROTECT, null=True, blank=True, related_name="invoices")
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("10.00"))
    commission_amt = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Frozen at creation — do not recompute from commission_pct after the fact.",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID)
    payment_gateway = models.CharField(
        max_length=20, choices=PaymentGateway.choices, null=True, blank=True
    )
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices, null=True, blank=True
    )
    gateway_reference_id = models.CharField(max_length=255, null=True, blank=True)
    payment_url = models.CharField(max_length=1000, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "invoices"

    def __str__(self):
        return f"Invoice #{self.id} — {self.amount} ({self.status})"

    def save(self, *args, **kwargs):
        if self._state.adding and not self.commission_amt:
            self.commission_amt = (self.amount * self.commission_pct / 100).quantize(
                self.amount
            )
        super().save(*args, **kwargs)


class PaymentTransaction(models.Model):
    class TransactionType(models.TextChoices):
        PAYMENT = "payment", "Payment"
        PAYOUT = "payout", "Payout"
        REFUND = "refund", "Refund"
        ADJUSTMENT = "adjustment", "Adjustment"

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(
        max_length=20, choices=TransactionType.choices, default=TransactionType.PAYMENT
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)
    gateway_payload = models.JSONField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment_transactions"

    def __str__(self):
        return f"{self.transaction_type} — {self.amount} ({self.status})"



class RndPayoutAccount(models.Model):
    """Where an RND gets paid (GCash or bank). Visible to admins, who send the
    monthly payout outside the app and record its reference."""

    class Method(models.TextChoices):
        GCASH = "gcash", "GCash"
        BANK = "bank", "Bank transfer"

    rnd = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payout_account")
    method = models.CharField(max_length=20, choices=Method.choices)
    account_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "rnd_payout_accounts"

    def __str__(self):
        return f"{self.rnd} — {self.get_method_display()} {self.account_number}"


class Payout(models.Model):
    """One monthly payout sent to an RND (Roblox-style: earnings go Pending →
    Posted → Paid out; payout day is the 5th). The account details are
    snapshotted so history stays accurate if the RND changes them later."""

    rnd = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="payouts")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payout_date = models.DateField(help_text="The payout day (the 5th) this payout belongs to")
    method = models.CharField(max_length=20)
    account_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    reference = models.CharField(max_length=100)
    notes = models.TextField(null=True, blank=True)
    released_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    released_at = models.DateTimeField()

    class Meta:
        db_table = "payouts"
        ordering = ["-released_at"]

    def __str__(self):
        return f"Payout {self.id} — {self.rnd} ₱{self.amount}"
