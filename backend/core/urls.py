from django.urls import path

from .views import (
    AdminAuditLogActionsView,
    AdminAuditLogExportView,
    AdminAuditLogListView,
    AdminPlatformStatsView,
    AdminSystemSettingListView,
    AdminSystemSettingUpdateView,
)

urlpatterns = [
    path("admin/platform-stats/", AdminPlatformStatsView.as_view(), name="admin_platform_stats"),
    path("admin/audit-logs/", AdminAuditLogListView.as_view(), name="admin_audit_logs"),
    path("admin/audit-logs/actions/", AdminAuditLogActionsView.as_view(), name="admin_audit_log_actions"),
    path("admin/audit-logs/export/", AdminAuditLogExportView.as_view(), name="admin_audit_log_export"),
    path("admin/settings/", AdminSystemSettingListView.as_view(), name="admin_settings_list"),
    path("admin/settings/<str:key>/", AdminSystemSettingUpdateView.as_view(), name="admin_settings_update"),
]
