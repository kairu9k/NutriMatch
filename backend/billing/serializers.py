from rest_framework import serializers

from scheduling.serializers import AppointmentSerializer

from .models import Invoice, PaymentTransaction


class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = [
            "id", "relationship", "appointment", "amount", "commission_pct", "commission_amt",
            "status", "payment_gateway", "payment_method", "gateway_reference_id",
            "payment_url", "paid_at", "notes", "created_at",
        ]
        read_only_fields = [
            "commission_amt", "status", "payment_gateway", "gateway_reference_id",
            "payment_url", "paid_at",
        ]


class InvoiceListSerializer(serializers.ModelSerializer):
    """Read-only, nests appointment (with RND/relationship) for client-facing
    invoice list display — InvoiceSerializer stays flat-FK for the pay flow."""

    appointment = AppointmentSerializer(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "appointment", "amount", "status",
            "payment_gateway", "payment_method", "payment_url", "paid_at", "created_at",
        ]


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ["id", "invoice", "transaction_type", "amount", "status", "processed_at", "created_at"]
