from django.urls import re_path

from .consumers import MessageConsumer, NotificationConsumer

websocket_urlpatterns = [
    re_path(r"^ws/relationships/(?P<relationship_id>\d+)/messages/$", MessageConsumer.as_asgi()),
    re_path(r"^ws/notifications/$", NotificationConsumer.as_asgi()),
]
