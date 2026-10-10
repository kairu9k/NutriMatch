from django.urls import path

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
]
