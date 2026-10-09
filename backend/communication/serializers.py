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
