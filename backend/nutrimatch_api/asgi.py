"""
ASGI config for nutrimatch_api project.

Serves both regular HTTP (DRF) and WebSocket (Django Channels, real-time
messaging) traffic from the same app. See communication/consumers.py and
communication/routing.py for the WebSocket side.
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nutrimatch_api.settings')

# get_asgi_application() must run before importing anything that touches
# Django models (routing -> consumers -> models), so app registry setup
# happens first.
django_asgi_app = get_asgi_application()

from communication.routing import websocket_urlpatterns  # noqa: E402
from .channels_auth import JwtAuthMiddlewareStack  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JwtAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
