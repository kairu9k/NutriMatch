from rest_framework import serializers

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


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ["id", "invoice", "transaction_type", "amount", "status", "processed_at", "created_at"]
