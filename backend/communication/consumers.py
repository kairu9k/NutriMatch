import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .serializers import MessageSerializer
from .services import notify


class MessageConsumer(AsyncWebsocketConsumer):
    """Real-time message delivery for one RndClientRelationship thread.
    Replaces the 5s-poll placeholder Messages.vue shipped with initially —
    same relationship-scoped access rule as the REST endpoints
    (MessageListCreateView), just enforced here at connect time instead of
    per-request."""

    async def connect(self):
        self.relationship_id = self.scope["url_route"]["kwargs"]["relationship_id"]
        self.group_name = f"relationship_{self.relationship_id}"
        user = self.scope["user"]

        if not user.is_authenticated:
            await self.close(code=4001)
            return

        relationship = await self._get_relationship(user, self.relationship_id)
        if relationship is None:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        user = self.scope["user"]
        try:
            data = json.loads(text_data)
            text = data.get("message", "").strip()
        except (json.JSONDecodeError, AttributeError):
            return
        if not text:
            return

        relationship = await self._get_relationship(user, self.relationship_id)
        if relationship is None:
            return

        message_data = await self._create_message(relationship, user, text)
        await self._notify_other_party(relationship, user, text, message_data["id"])

        await self.channel_layer.group_send(
            self.group_name, {"type": "chat.message", "message": message_data}
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def _get_relationship(self, user, relationship_id):
        from django.db.models import Q

        from scheduling.models import RndClientRelationship

        return RndClientRelationship.objects.filter(
            Q(rnd=user) | Q(client=user), id=relationship_id
        ).first()

    @database_sync_to_async
    def _create_message(self, relationship, user, text):
        from .models import Message

        message = Message.objects.create(relationship=relationship, sender=user, message=text)
        return MessageSerializer(message).data

    @database_sync_to_async
    def _notify_other_party(self, relationship, sender, text, message_id):
        recipient = relationship.client if sender.id == relationship.rnd_id else relationship.rnd
        notify(
            recipient=recipient,
            notifiable_type="message",
            notifiable_id=message_id,
            subject="New message",
            content=f"{sender.full_name}: {text[:200]}",
        )
