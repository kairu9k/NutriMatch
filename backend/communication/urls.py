from django.urls import path

from .support import (
    AdminSupportCloseView,
    AdminSupportReopenView,
    AdminSupportReplyView,
    AdminSupportTicketDetailView,
    AdminSupportTicketListView,
    SupportLinksView,
    SupportTicketCloseView,
    SupportTicketDetailView,
    SupportTicketListCreateView,
    SupportTicketReplyView,
    SupportUnreadView,
)

from .reminder_views import (
    ClientReminderListView,
    ClientReminderMuteView,
    ClientTaskCheckView,
    ClientReminderSettingsView,
    ClientTodayView,
    RndClientReminderListCreateView,
    RndReminderDetailView,
)
from .views import (
    MessageMarkReadView,
    MessageUnreadView,
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
    path("relationships/<int:relationship_id>/messages/read/", MessageMarkReadView.as_view(), name="messages_mark_read"),
    path("messages/unread/", MessageUnreadView.as_view(), name="messages_unread"),

    path("notifications/", NotificationListView.as_view(), name="notification_list"),
    path("support/tickets/", SupportTicketListCreateView.as_view(), name="support_tickets"),
    path("support/tickets/<int:pk>/", SupportTicketDetailView.as_view(), name="support_ticket"),
    path("support/tickets/<int:pk>/messages/", SupportTicketReplyView.as_view(), name="support_ticket_reply"),
    path("support/tickets/<int:pk>/close/", SupportTicketCloseView.as_view(), name="support_ticket_close"),
    path("support/links/", SupportLinksView.as_view(), name="support_links"),
    path("support/unread/", SupportUnreadView.as_view(), name="support_unread"),
    path("admin/support/tickets/", AdminSupportTicketListView.as_view(), name="admin_support_tickets"),
    path("admin/support/tickets/<int:pk>/", AdminSupportTicketDetailView.as_view(), name="admin_support_ticket"),
    path("admin/support/tickets/<int:pk>/messages/", AdminSupportReplyView.as_view(), name="admin_support_reply"),
    path("admin/support/tickets/<int:pk>/close/", AdminSupportCloseView.as_view(), name="admin_support_close"),
    path("admin/support/tickets/<int:pk>/reopen/", AdminSupportReopenView.as_view(), name="admin_support_reopen"),
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
    path("client/reminders/<int:pk>/check/", ClientTaskCheckView.as_view(), name="client_task_check"),
    path("client/today/", ClientTodayView.as_view(), name="client_today"),
    path("rnd/relationships/<int:relationship_id>/reminders/", RndClientReminderListCreateView.as_view(), name="rnd_client_reminders"),
    path("rnd/reminders/<int:pk>/", RndReminderDetailView.as_view(), name="rnd_reminder_detail"),
]
