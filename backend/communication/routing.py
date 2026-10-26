from django.urls import re_path

from scheduling.consumers import CallConsumer

from .consumers import MessageConsumer, NotificationConsumer

websocket_urlpatterns = [
    re_path(r"^ws/relationships/(?P<relationship_id>\d+)/messages/$", MessageConsumer.as_asgi()),
    re_path(r"^ws/notifications/$", NotificationConsumer.as_asgi()),
    # the WebRTC video call's signaling (scheduling/video_call.py)
    re_path(r"^ws/appointments/(?P<appointment_id>\d+)/call/$", CallConsumer.as_asgi()),
]
