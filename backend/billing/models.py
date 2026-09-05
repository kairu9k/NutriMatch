from decimal import Decimal

from django.db import models

from scheduling.models import Appointment, RndClientRelationship


class Invoice(models.Model):
    class Status(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        CANCELLED = "cancelled", "Cancelled"
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
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        CASH = "cash", "Cash"
        OTHER = "other", "Other"

    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="invoices"
    )
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
