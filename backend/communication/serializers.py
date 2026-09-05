from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id", "relationship", "sender", "message", "message_type",
            "attachment_url", "attachment_type", "is_read", "read_at", "created_at",
        ]
        read_only_fields = ["relationship", "sender", "is_read", "read_at"]
