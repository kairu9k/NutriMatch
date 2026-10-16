"""Live updates to a signed-in user's browser (ws/notifications/,
NotificationConsumer): every new bell notification, and a "message" event
when someone chats them (the yellow dot on the Messages icon).

Best effort — a missed push is caught by the page's fallback refresh."""

import json
import threading

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction


def user_group(user_id):
    return f"user_{user_id}"


def group_send(group, event):
    """Send to a channel-layer group, never raising. With Redis it runs in a
    background thread (an unreachable Redis takes seconds to fail and the
    request mustn't wait); the in-memory layer is sent inline, because it
    only works on the server's own event loop, which async_to_sync reaches
    from a request thread but not from a new thread."""
    def send():
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            layer = get_channel_layer()
            if layer is not None:
                async_to_sync(layer.group_send)(group, event)
        except Exception:  # noqa: BLE001 — live push is best effort
            pass

    if getattr(settings, "REDIS_URL", ""):
        threading.Thread(target=send, daemon=True).start()
    else:
        send()


def push_to_user(user_id, kind, payload):
    """Push {kind, ...payload} to the user's open pages once the current
    transaction commits (nothing is pushed for a rolled-back change)."""
    # Plain JSON types only (what Redis' msgpack and the browser can take).
    data = json.loads(json.dumps({"kind": kind, **payload}, cls=DjangoJSONEncoder))
    event = {"type": "live.event", "data": data}
    transaction.on_commit(lambda: group_send(user_group(user_id), event))


def push_notification(notification):
    from .serializers import NotificationLogSerializer

    push_to_user(notification.recipient_id, "notification", {"notification": NotificationLogSerializer(notification).data})


def push_new_message(recipient_id, message_data):
    push_to_user(recipient_id, "message", {
        "relationship_id": message_data["relationship"], "message": message_data,
    })
