from django.contrib import admin

from .models import ApiCache, AuditLog, SystemSetting

admin.site.register(SystemSetting)
admin.site.register(ApiCache)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "user", "table_name", "record_id", "created_at"]
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
