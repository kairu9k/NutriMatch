from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import AuditLog, SystemSetting


class AuditLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id", "user", "action", "table_name", "record_id",
            "old_values", "new_values", "ip_address", "user_agent", "created_at",
        ]
        read_only_fields = fields


class SystemSettingSerializer(serializers.ModelSerializer):
    updated_by = UserSerializer(read_only=True)

    class Meta:
        model = SystemSetting
        fields = ["id", "key", "value", "description", "updated_by", "updated_at"]
        read_only_fields = ["id", "key", "updated_by", "updated_at"]
