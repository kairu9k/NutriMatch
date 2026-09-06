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


class RndInvoiceListSerializer(serializers.ModelSerializer):
    """RND-facing invoice list — nests the client's name (via relationship)
    and appointment date instead of the client-side appointment/RND nesting
    InvoiceListSerializer uses. net is amount - commission_amt, computed
    here since it isn't stored (commission_amt already freezes at creation)."""

    client_name = serializers.SerializerMethodField()
    appointment_date = serializers.DateTimeField(source="appointment.scheduled_at", read_only=True)
    net = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "client_name", "appointment_date", "amount", "commission_amt",
            "net", "status", "paid_at", "created_at",
        ]

    def get_client_name(self, obj):
        client = obj.relationship.client
        return f"{client.first_name} {client.last_name}"

    def get_net(self, obj):
        return obj.amount - obj.commission_amt


class AdminInvoiceListSerializer(serializers.ModelSerializer):
    """Platform-wide invoice list for BillingCommission.vue — both client
    and RND names, net computed the same way as RndInvoiceListSerializer."""

    client_name = serializers.SerializerMethodField()
    rnd_name = serializers.SerializerMethodField()
    net = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "client_name", "rnd_name", "amount", "commission_amt",
            "net", "status", "payment_method", "paid_at", "created_at",
        ]

    def get_client_name(self, obj):
        client = obj.relationship.client
        return f"{client.first_name} {client.last_name}"

    def get_rnd_name(self, obj):
        rnd = obj.relationship.rnd
        return f"{rnd.first_name} {rnd.last_name}"

    def get_net(self, obj):
        return obj.amount - obj.commission_amt


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ["id", "invoice", "transaction_type", "amount", "status", "processed_at", "created_at"]
