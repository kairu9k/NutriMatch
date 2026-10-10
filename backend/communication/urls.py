from django.urls import path

from .reminder_views import (
    ClientReminderListView,
    ClientReminderMuteView,
    ClientReminderSettingsView,
    ClientTodayView,
    RndClientReminderListCreateView,
    RndReminderDetailView,
)
from .views import (
    ClientResourceListView,
    MessageDeleteView,
    MessageListCreateView,
    NotificationDetailView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
    RndResourceListCreateView,
    RndResourceShareView,
    RndResourceUnshareView,
    RndResourceUpdateView,
)

urlpatterns = [
    path("relationships/<int:relationship_id>/messages/", MessageListCreateView.as_view(), name="messages"),
    path("relationships/<int:relationship_id>/messages/<int:pk>/", MessageDeleteView.as_view(), name="message_delete"),

    path("notifications/", NotificationListView.as_view(), name="notification_list"),
    path("notifications/mark-all-read/", NotificationMarkAllReadView.as_view(), name="notification_mark_all_read"),
    path("notifications/<int:pk>/", NotificationDetailView.as_view(), name="notification_detail"),
    path("notifications/<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification_mark_read"),

    path("rnd/resources/", RndResourceListCreateView.as_view(), name="rnd_resource_list_create"),
    path("rnd/resources/<int:pk>/", RndResourceUpdateView.as_view(), name="rnd_resource_update"),
    path("rnd/resources/<int:pk>/share/", RndResourceShareView.as_view(), name="rnd_resource_share"),
    path(
        "rnd/resources/<int:pk>/share/<int:relationship_id>/",
        RndResourceUnshareView.as_view(),
        name="rnd_resource_unshare",
    ),
    path("client/resources/", ClientResourceListView.as_view(), name="client_resource_list"),

    path("client/reminder-settings/", ClientReminderSettingsView.as_view(), name="client_reminder_settings"),
    path("client/reminders/", ClientReminderListView.as_view(), name="client_reminders"),
    path("client/reminders/<int:pk>/", ClientReminderMuteView.as_view(), name="client_reminder_mute"),
    path("client/today/", ClientTodayView.as_view(), name="client_today"),
    path("rnd/relationships/<int:relationship_id>/reminders/", RndClientReminderListCreateView.as_view(), name="rnd_client_reminders"),
    path("rnd/reminders/<int:pk>/", RndReminderDetailView.as_view(), name="rnd_reminder_detail"),
]
