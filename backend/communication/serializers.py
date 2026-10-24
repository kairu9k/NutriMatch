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
    # For a "Meal log update" sent to an RND: the log itself (photo, meal,
    # status, what was planned), so the notification can show it. Only when
    # the log belongs to one of the recipient's own clients; None otherwise.
    meal_log = serializers.SerializerMethodField()

    class Meta:
        model = NotificationLog
        fields = [
            "id", "notifiable_type", "notifiable_id", "subject", "content",
            "is_read", "created_at", "meal_log",
        ]
        read_only_fields = fields

    def get_meal_log(self, obj):
        if obj.notifiable_type != "meal_log" or not obj.notifiable_id:
            return None
        from nutrition.models import MealLog
        from nutrition.serializers import RndMealLogSerializer

        log = (
            MealLog.objects.filter(pk=obj.notifiable_id, meal_plan_meal__meal_plan__relationship__rnd_id=obj.recipient_id)
            .select_related("client", "meal_plan_meal__meal_plan")
            .prefetch_related("meal_plan_meal__food_items")
            .first()
        )
        return RndMealLogSerializer(log).data if log else None


# Which files each resource type accepts, and how big (Cloudinary free tier:
# 10 MB for images/PDFs/documents, 100 MB for videos). The upload page's
# file picker uses the same lists.
RESOURCE_FILE_RULES = {
    Resource.Type.PDF: ({".pdf"}, 10),
    Resource.Type.ARTICLE: ({".pdf", ".doc", ".docx"}, 10),
    Resource.Type.VIDEO: ({".mp4", ".webm", ".mov"}, 100),
}


def resource_download_url(file_path, title):
    """The Cloudinary URL with `fl_attachment` added, so the browser saves
    the file (named after the resource's title) instead of opening it.
    Documents Cloudinary stores as "raw" files already download as-is."""
    from django.utils.text import slugify

    if not file_path:
        return None
    filename = slugify(title or "")[:80] or "resource"
    for marker in ("/image/upload/", "/video/upload/"):
        if marker in file_path:
            return file_path.replace(marker, f"{marker}fl_attachment:{filename}/", 1)
    return file_path


class ResourceSerializer(serializers.ModelSerializer):
    # Write-only — the view uploads this to Cloudinary via
    # CloudinaryResourceUploadService and writes the returned URL into
    # file_path itself; it's never assigned directly from validated_data.
    file = serializers.FileField(write_only=True, required=False)
    download_url = serializers.SerializerMethodField()
    # RND views only: how many active clients it's shared with (the view
    # annotates `_shared_count`; a just-created resource has none yet).
    shared_count = serializers.SerializerMethodField()
    # RND views only: the active clients it's shared with, newest first
    # (prefetched as `_active_shares` by the view).
    shared_with = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            "id", "title", "description", "type", "file", "file_path", "download_url",
            "url", "is_active", "created_at", "shared_count", "shared_with",
        ]
        read_only_fields = ["file_path"]

    def get_download_url(self, obj):
        return resource_download_url(obj.file_path, obj.title)

    def get_shared_count(self, obj):
        return getattr(obj, "_shared_count", 0)

    def get_shared_with(self, obj):
        return [
            {
                "relationship_id": share.relationship_id,
                "name": f"{share.relationship.client.first_name} {share.relationship.client.last_name}".strip(),
                "photo": share.relationship.client.profile_photo,
            }
            for share in getattr(obj, "_active_shares", [])
        ]


    def validate(self, attrs):
        import os

        resource_type = attrs.get("type", getattr(self.instance, "type", None))
        if resource_type == Resource.Type.LINK:
            if not attrs.get("url") and not (self.instance and self.instance.url):
                raise serializers.ValidationError({"url": "A URL is required for link resources."})
        else:
            file = attrs.get("file")
            has_existing_file = self.instance and self.instance.file_path
            if not file and not has_existing_file:
                raise serializers.ValidationError(
                    {"file": "A file is required for PDF/video/article resources."}
                )
            if file and resource_type in RESOURCE_FILE_RULES:
                extensions, max_mb = RESOURCE_FILE_RULES[resource_type]
                ext = os.path.splitext(file.name)[1].lower()
                if ext not in extensions:
                    allowed = ", ".join(sorted(extensions))
                    raise serializers.ValidationError(
                        {"file": f"This file type isn't allowed for a {Resource.Type(resource_type).label} resource. Use {allowed}."}
                    )
                if file.size > max_mb * 1024 * 1024:
                    raise serializers.ValidationError({"file": f"The file is too large. The limit is {max_mb} MB."})
        return attrs


class ClientResourceSerializer(ResourceSerializer):
    """What a client sees: the resource plus which RND shared it and when
    (their own share — the view prefetches it as `_my_shares`)."""

    shared_by = serializers.SerializerMethodField()
    shared_at = serializers.SerializerMethodField()

    class Meta(ResourceSerializer.Meta):
        fields = [f for f in ResourceSerializer.Meta.fields if f not in ("shared_count", "shared_with")] + ["shared_by", "shared_at"]

    def _share(self, obj):
        shares = getattr(obj, "_my_shares", None)
        return shares[0] if shares else None

    def get_shared_by(self, obj):
        u = obj.uploaded_by
        return {"id": u.id, "name": u.full_name, "profile_photo": u.profile_photo}

    def get_shared_at(self, obj):
        share = self._share(obj)
        return share.shared_at if share else None




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

    def _related_relationship(self, pk, user):
        from django.db.models import Q

        from scheduling.models import RndClientRelationship

        rel = RndClientRelationship.objects.filter(Q(client=user) | Q(rnd=user), pk=pk).select_related("client", "rnd").first()
        if rel is None:
            return None
        return {
            "id": rel.id, "relationship_id": rel.id, "with": self._other_party(rel, user),
            "status": rel.status, "discharge_requested_at": rel.discharge_requested_at,
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

    def _related_support(self, pk, user):
        from .models import SupportTicket

        qs = SupportTicket.objects.filter(pk=pk)
        if user.role != "admin":
            qs = qs.filter(user=user)
        t = qs.first()
        if t is None:
            return None
        return {"id": t.id, "reference": f"SR-{t.id:04d}", "subject": t.subject, "status": t.status,
                "status_label": t.get_status_display(), "category_label": t.get_category_display()}

    def _related_reminder(self, pk, user):
        from .models import Reminder

        r = Reminder.objects.filter(pk=pk, client=user).select_related("created_by").first()
        if r is None:
            return None
        return {
            "id": r.id, "title": r.title, "message": r.message, "repeat": r.get_repeat_display(),
            "next_at": None if r.is_sent else r.send_at, "is_muted": r.is_muted,
            "with": {"name": r.created_by.full_name, "role": r.created_by.role} if r.created_by else None,
        }

    def _related_resource(self, pk, user):
        from scheduling.models import RndClientRelationship

        resource = (
            Resource.objects.filter(
                pk=pk, is_active=True,
                shares__relationship__client=user,
                shares__relationship__status=RndClientRelationship.Status.ACTIVE,
            )
            .select_related("uploaded_by")
            .first()
        )
        if resource is None:
            return None
        return {
            "id": resource.id, "title": resource.title, "type": resource.type,
            "with": {"name": resource.uploaded_by.full_name, "role": resource.uploaded_by.role},
        }

    def _related_lab_request(self, pk, user):
        from clinical.labs import request_payload
        from clinical.models import LabRequest

        req = LabRequest.objects.filter(_party_q(user), pk=pk).select_related("relationship__client", "relationship__rnd").first()
        if req is None:
            return None
        return {**request_payload(req), "with": self._other_party(req.relationship, user)}

    def _related_lab_result(self, pk, user):
        from clinical.labs import result_payload
        from clinical.models import LabResult

        res = LabResult.objects.filter(_party_q(user), pk=pk).select_related("relationship__client", "relationship__rnd").first()
        if res is None:
            return None
        return {**result_payload(res), "with": self._other_party(res.relationship, user)}

    def _related_payout(self, pk, user):
        from billing.models import Payout

        payout = Payout.objects.filter(pk=pk, rnd=user).first()
        if payout is None:
            return None
        return {
            "id": payout.id, "amount": payout.amount, "method": payout.method, "bank_name": payout.bank_name, "reference": payout.reference,
            "released_at": payout.released_at,
        }
