from django.urls import path

from .views import (
    MessageDeleteView,
    MessageListCreateView,
    NotificationListView,
    NotificationMarkAllReadView,
    NotificationMarkReadView,
)

urlpatterns = [
    path("relationships/<int:relationship_id>/messages/", MessageListCreateView.as_view(), name="messages"),
    path("relationships/<int:relationship_id>/messages/<int:pk>/", MessageDeleteView.as_view(), name="message_delete"),

    path("notifications/", NotificationListView.as_view(), name="notification_list"),
    path("notifications/mark-all-read/", NotificationMarkAllReadView.as_view(), name="notification_mark_all_read"),
    path("notifications/<int:pk>/read/", NotificationMarkReadView.as_view(), name="notification_mark_read"),
]
