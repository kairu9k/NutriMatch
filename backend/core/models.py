from django.conf import settings
from django.db import models


class SystemSetting(models.Model):
    key = models.CharField(max_length=50, unique=True)
    value = models.TextField(null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_settings",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_settings"

    def __str__(self):
        return self.key


class ApiCache(models.Model):
    """Transient cache for external API responses (USDA FoodData Central, etc.).

    This is the one deliberate exception to the platform's data-minimization
    rule — it exists to reduce redundant external calls, has a TTL via
    `expires_at`, and is not a source of truth. Persistent domain data (e.g.
    MealPlanFoodItem) must NOT copy nutrient payloads out of this cache.
    """

    cache_key = models.CharField(max_length=255, unique=True)
    response_body = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_cache"

    def __str__(self):
        return self.cache_key


class AuditLog(models.Model):
    """Immutable compliance activity trail (RA 10173). Rows are append-only —
    application code must never update or delete an existing AuditLog row."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=255)
    table_name = models.CharField(max_length=100, null=True, blank=True)
    record_id = models.IntegerField(null=True, blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"

    def __str__(self):
        return f"{self.action} — {self.created_at:%Y-%m-%d %H:%M}"
