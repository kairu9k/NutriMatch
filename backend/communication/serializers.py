from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Message, NotificationLog, Resource


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id", "relationship", "sender", "message", "message_type",
            "attachment_url", "attachment_type", "is_read", "read_at", "created_at",
        ]
        read_only_fields = ["relationship", "sender", "is_read", "read_at"]


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = [
            "id", "notifiable_type", "notifiable_id", "subject", "content",
            "is_read", "created_at",
        ]
        read_only_fields = fields


class ResourceSerializer(serializers.ModelSerializer):
    # Write-only — the view uploads this to Cloudinary via
    # CloudinaryResourceUploadService and writes the returned URL into
    # file_path itself; it's never assigned directly from validated_data.
    file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Resource
        fields = ["id", "title", "description", "type", "file", "file_path", "url", "is_active", "created_at"]
        read_only_fields = ["file_path"]

    def validate(self, attrs):
        resource_type = attrs.get("type", getattr(self.instance, "type", None))
        if resource_type == Resource.Type.LINK:
            if not attrs.get("url") and not (self.instance and self.instance.url):
                raise serializers.ValidationError({"url": "A URL is required for link resources."})
        else:
            has_existing_file = self.instance and self.instance.file_path
            if not attrs.get("file") and not has_existing_file:
                raise serializers.ValidationError(
                    {"file": "A file is required for PDF/video/article resources."}
                )
        return attrs


def _party_q(user):
    """Relationships the user belongs to (as the client or the RND)."""
    from django.db.models import Q

    return Q(relationship__client=user) | Q(relationship__rnd=user)


class NotificationDetailSerializer(NotificationLogSerializer):
    """One notification for the detail overlay, plus `related`: a summary of
    what it's about (the appointment, invoice, message or meal plan) so the
    overlay can show the full picture and link to it. Only filled in when that
    record belongs to the recipient; None if it's gone or not theirs."""

    related = serializers.SerializerMethodField()

    class Meta(NotificationLogSerializer.Meta):
        fields = NotificationLogSerializer.Meta.fields + ["related"]
        read_only_fields = fields

    def get_related(self, obj):
        getter = getattr(self, f"_related_{obj.notifiable_type}", None)
        if getter is None or not obj.notifiable_id:
            return None
        return getter(obj.notifiable_id, obj.recipient)

    @staticmethod
    def _other_party(relationship, user):
        other = relationship.rnd if relationship.client_id == user.id else relationship.client
        return {"name": other.full_name, "role": other.role}

    @staticmethod
    def _invoice_summary(invoice):
        if invoice is None:
            return None
        return {"id": invoice.id, "amount": invoice.amount, "status": invoice.status, "paid_at": invoice.paid_at}

    def _related_appointment(self, pk, user):
        from billing.services import appointment_invoice
        from scheduling.models import Appointment

        appt = Appointment.objects.filter(_party_q(user), pk=pk).select_related("relationship__client", "relationship__rnd").first()
        if appt is None:
            return None
        return {
            "id": appt.id, "relationship_id": appt.relationship_id, "with": self._other_party(appt.relationship, user),
            "scheduled_at": appt.scheduled_at, "duration_minutes": appt.duration_minutes, "type": appt.type,
            "status": appt.status, "cancellation_reason": appt.cancellation_reason,
            "invoice": self._invoice_summary(appointment_invoice(appt)),
        }

    def _related_invoice(self, pk, user):
        from billing.models import Invoice

        inv = Invoice.objects.filter(_party_q(user), pk=pk).select_related(
            "relationship__client", "relationship__rnd", "appointment"
        ).first()
        if inv is None:
            return None
        appt = inv.appointment
        return {
            **self._invoice_summary(inv), "relationship_id": inv.relationship_id,
            "with": self._other_party(inv.relationship, user), "payment_method": inv.payment_method,
            "appointment": {"id": appt.id, "scheduled_at": appt.scheduled_at, "status": appt.status} if appt else None,
        }

    def _related_message(self, pk, user):
        msg = Message.objects.filter(_party_q(user), pk=pk).select_related("sender").first()
        if msg is None:
            return None
        return {
            "id": msg.id, "relationship_id": msg.relationship_id, "sender": msg.sender.full_name,
            "message": msg.message, "message_type": msg.message_type, "created_at": msg.created_at,
        }

    def _related_meal_plan(self, pk, user):
        from nutrition.models import MealPlan

        plan = MealPlan.objects.filter(pk=pk, relationship__client=user).exclude(status="draft").select_related(
            "relationship__rnd"
        ).first() or MealPlan.objects.filter(pk=pk, relationship__rnd=user).select_related("relationship__client").first()
        if plan is None:
            return None
        return {
            "id": plan.id, "relationship_id": plan.relationship_id, "with": self._other_party(plan.relationship, user),
            "name": plan.name, "status": plan.status, "target_kcal": plan.target_kcal, "sent_at": plan.sent_at,
        }

    def _related_payout(self, pk, user):
        from billing.models import Payout

        payout = Payout.objects.filter(pk=pk, rnd=user).first()
        if payout is None:
            return None
        return {
            "id": payout.id, "amount": payout.amount, "method": payout.method, "reference": payout.reference,
            "released_at": payout.released_at,
        }
