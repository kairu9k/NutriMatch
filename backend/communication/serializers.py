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
