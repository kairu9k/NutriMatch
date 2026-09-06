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
    class Meta:
        model = Resource
        fields = ["id", "title", "description", "type", "file_path", "url", "is_active", "created_at"]
        read_only_fields = ["file_path"]

    def validate(self, attrs):
        resource_type = attrs.get("type", getattr(self.instance, "type", None))
        if resource_type != Resource.Type.LINK:
            raise serializers.ValidationError(
                "Only 'link' resources can be created right now — file upload "
                "(PDF/video) isn't wired up yet."
            )
        if not attrs.get("url") and not (self.instance and self.instance.url):
            raise serializers.ValidationError({"url": "A URL is required for link resources."})
        return attrs
