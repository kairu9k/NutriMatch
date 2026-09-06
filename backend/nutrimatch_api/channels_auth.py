"""JWT authentication for Django Channels' ASGI stack.

channels.auth.AuthMiddlewareStack only understands Django sessions —
this app is entirely JWT/SimpleJWT (see accounts.serializers), so
WebSocket connections need their own auth path. Browsers can't set custom
headers on a WebSocket handshake, so the access token is passed as a
query param instead: ws://host/ws/relationships/<id>/messages/?token=<jwt>
"""

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs


@database_sync_to_async
def _get_user_from_token(token):
    from accounts.models import User

    try:
        validated = AccessToken(token)
        user = User.objects.get(id=validated["user_id"], deleted_at__isnull=True)
    except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()
    if not user.is_active:
        return AnonymousUser()
    return user


class JwtAuthMiddleware:
    """Reads ?token=<access-token> from the WebSocket connection's query
    string and sets scope['user'] accordingly, same contract as Channels'
    own session-based AuthMiddleware."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        scope["user"] = await _get_user_from_token(token) if token else AnonymousUser()
        return await self.inner(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    """JWT auth first (sets scope['user'] from the token), then Channels'
    own AuthMiddlewareStack as a fallback for anything session-based —
    matches the pattern Channels' docs show for custom auth."""
    return JwtAuthMiddleware(AuthMiddlewareStack(inner))
