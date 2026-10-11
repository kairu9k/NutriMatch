from rest_framework import serializers

from scheduling.serializers import AppointmentSerializer

from .models import Invoice, PaymentTransaction, Payout, RndPayoutAccount


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
    """The client's Billing page: each invoice with the consultation it's
    for, the pay-by deadline, a receipt summary once paid and refund dates.
    No commission split — that's between the RND and NutriMatch."""

    consultation = serializers.SerializerMethodField()
    pay_by = serializers.SerializerMethodField()
    receipt = serializers.SerializerMethodField()
    refund = serializers.SerializerMethodField()
    payment_method_label = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "amount", "status", "payment_method", "payment_method_label", "paid_at", "created_at",
            "consultation", "pay_by", "receipt", "refund",
        ]

    def _txns(self, obj):
        return list(obj.transactions.all())

    def get_consultation(self, obj):
        a = obj.appointment
        rnd = obj.relationship.rnd
        return {
            "id": a.id if a else None, "scheduled_at": a.scheduled_at if a else None,
            "type": a.type if a else None, "type_label": a.get_type_display() if a else None,
            "status": a.status if a else None, "duration_minutes": a.duration_minutes if a else None,
            "cancellation_reason": a.cancellation_reason if a else None,
            "rnd": {"id": rnd.id, "name": rnd.full_name, "profile_photo": rnd.profile_photo},
        }

    def get_pay_by(self, obj):
        a = obj.appointment
        return a.scheduled_at if obj.status == Invoice.Status.UNPAID and a and a.status == "confirmed" else None

    def get_payment_method_label(self, obj):
        return obj.get_payment_method_display() if obj.payment_method else None

    def get_receipt(self, obj):
        from .services import payment_receipt

        if obj.status not in (Invoice.Status.PAID, Invoice.Status.REFUND_PENDING, Invoice.Status.REFUNDED):
            return None
        pay = next((t for t in self._txns(obj) if t.transaction_type == "payment"), None)
        details = payment_receipt(pay.gateway_payload) if pay and pay.gateway_payload else {}
        return {
            "number": f"INV-{obj.id:04d}",
            "paid_at": obj.paid_at,
            "method": self.get_payment_method_label(obj),
            "card_brand": details.get("card_brand"),
            "card_last4": details.get("card_last4"),
            "reference": details.get("payment_id") or obj.gateway_reference_id,
        }

    def get_refund(self, obj):
        if obj.status not in (Invoice.Status.REFUND_PENDING, Invoice.Status.REFUNDED):
            return None
        refund = next((t for t in self._txns(obj) if t.transaction_type == "refund"), None)
        a = obj.appointment
        return {
            "status": obj.status,
            "cancelled_at": a.updated_at if a and a.status == "cancelled" else None,
            "refunded_at": refund.processed_at if refund else None,
        }


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
            "id", "client_name", "rnd_name", "amount", "commission_pct", "commission_amt",
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


class AdminInvoiceDetailSerializer(AdminInvoiceListSerializer):
    """One invoice for the Billing & Commission detail overlay: the parties,
    the consultation it bills, and every transaction with its receipt
    details (picked from the PayMongo payload, never the raw payload)."""

    client = serializers.SerializerMethodField()
    rnd = serializers.SerializerMethodField()
    appointment = serializers.SerializerMethodField()
    transactions = serializers.SerializerMethodField()

    class Meta(AdminInvoiceListSerializer.Meta):
        fields = AdminInvoiceListSerializer.Meta.fields + [
            "client", "rnd", "appointment", "payment_gateway", "gateway_reference_id",
            "notes", "payout", "transactions",
        ]

    @staticmethod
    def _person(user):
        return {"id": user.id, "name": user.full_name, "email": user.email}

    def get_client(self, obj):
        return self._person(obj.relationship.client)

    def get_rnd(self, obj):
        return self._person(obj.relationship.rnd)

    def get_appointment(self, obj):
        appt = obj.appointment
        if appt is None:
            return None
        return {
            "id": appt.id, "scheduled_at": appt.scheduled_at, "duration_minutes": appt.duration_minutes,
            "type": appt.type, "status": appt.status, "cancellation_reason": appt.cancellation_reason,
            "completed_at": appt.completed_at,
        }

    def get_transactions(self, obj):
        from .services import payment_receipt

        rows = []
        for t in obj.transactions.order_by("created_at"):
            payload = t.gateway_payload if isinstance(t.gateway_payload, dict) else {}
            rows.append({
                "id": t.id, "transaction_type": t.transaction_type, "amount": t.amount, "status": t.status,
                "processed_at": t.processed_at, "created_at": t.created_at,
                # Where it was recorded from: webhook / status check / admin / seed_demo.
                "source": payload.get("source") or ("paymongo" if payload else None),
                "reference": payload.get("reference"),
                "receipt": payment_receipt(payload) if t.transaction_type == "payment" else {},
            })
        return rows


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ["id", "invoice", "transaction_type", "amount", "status", "processed_at", "created_at"]



class RndPayoutAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = RndPayoutAccount
        fields = ["method", "account_name", "account_number", "bank_name", "updated_at"]
        read_only_fields = ["updated_at"]

    def validate_account_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Enter the account holder's full name.")
        return value

    def validate(self, attrs):
        import re

        method = attrs.get("method", getattr(self.instance, "method", None))
        number = (attrs.get("account_number", getattr(self.instance, "account_number", "")) or "").replace(" ", "")
        if method == "gcash":
            if not re.fullmatch(r"09\d{9}", number):
                raise serializers.ValidationError({"account_number": ["Enter the 11-digit GCash number, e.g. 09171234567."]})
            attrs["bank_name"] = None
        elif method == "bank":
            if not re.fullmatch(r"\d{6,20}", number):
                raise serializers.ValidationError({"account_number": ["Enter the bank account number (digits only)."]})
            if not (attrs.get("bank_name", getattr(self.instance, "bank_name", "")) or "").strip():
                raise serializers.ValidationError({"bank_name": ["Enter the bank name, e.g. BDO or BPI."]})
        attrs["account_number"] = number
        return attrs


class PayoutSerializer(serializers.ModelSerializer):
    rnd_name = serializers.CharField(source="rnd.full_name", read_only=True)
    released_by_name = serializers.SerializerMethodField()
    invoice_count = serializers.SerializerMethodField()

    class Meta:
        model = Payout
        fields = [
            "id", "rnd", "rnd_name", "amount", "payout_date", "method", "account_name", "account_number", "bank_name",
            "reference", "notes", "released_by_name", "released_at", "invoice_count",
        ]

    def get_released_by_name(self, obj):
        return obj.released_by.full_name if obj.released_by else None

    def get_invoice_count(self, obj):
        return obj.invoices.count()
