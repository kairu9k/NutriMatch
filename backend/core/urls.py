from django.urls import path

from .views import (
    AdminAuditLogListView,
    AdminPlatformStatsView,
    AdminSystemSettingListView,
    AdminSystemSettingUpdateView,
)

urlpatterns = [
    path("admin/platform-stats/", AdminPlatformStatsView.as_view(), name="admin_platform_stats"),
    path("admin/audit-logs/", AdminAuditLogListView.as_view(), name="admin_audit_logs"),
    path("admin/settings/", AdminSystemSettingListView.as_view(), name="admin_settings_list"),
    path("admin/settings/<str:key>/", AdminSystemSettingUpdateView.as_view(), name="admin_settings_update"),
]
