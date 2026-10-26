"""ws/appointments/<id>/call/ — signaling for the WebRTC video call
(scheduling/video_call.py). The server never sees the video: it checks who
may be in the call, tracks who is in it (at most two), and passes the two
browsers' messages (offer, answer, ICE candidates, camera/mic state) to the
other person.

Messages from the browser: {"type": "signal", "data": {...}} and
{"type": "media", "audio": bool, "video": bool}. To the browser:
{"type": "welcome", "role", "peers": [...]}, {"type": "peer-joined", ...},
{"type": "peer-left", ...}, {"type": "signal", "from", "data"},
{"type": "media", "from", ...}, {"type": "replaced"} (opened in another tab).

Who is in a call is kept in the Django cache (one process: the in-memory
cache; several processes need a shared cache such as Redis)."""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache

from .video_call import MAX_PEOPLE, CallDenied, call_access, mark_ended, mark_started

CLOSE_CODES = {"not_signed_in": 4001, "full": 4009}


def _members_key(appointment_id):
    return f"call:{appointment_id}:members"


class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.appointment_id = int(self.scope["url_route"]["kwargs"]["appointment_id"])
        self.group_name = f"call_{self.appointment_id}"
        user = self.scope["user"]
        try:
            _, self.role = await database_sync_to_async(call_access)(user, self.appointment_id)
        except CallDenied as denied:
            await self.accept()
            await self.send(text_data=json.dumps({"type": "denied", "code": denied.code, "message": denied.message}))
            await self.close(code=CLOSE_CODES.get(denied.code, 4003))
            return

        members = cache.get(_members_key(self.appointment_id)) or {}
        # the same person opening the call again (another tab, a refresh) replaces the old one
        old = members.pop(str(user.id), None)
        if old:
            await self.channel_layer.send(old["channel"], {"type": "call.replaced"})
        if len(members) >= MAX_PEOPLE:
            await self.accept()
            await self.send(text_data=json.dumps({"type": "denied", "code": "full", "message": "This call already has two people."}))
            await self.close(code=CLOSE_CODES["full"])
            return
        self.me = {"user_id": user.id, "role": self.role, "name": user.full_name, "channel": self.channel_name}
        members[str(user.id)] = self.me
        cache.set(_members_key(self.appointment_id), members, 6 * 3600)

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        others = [self._public(m) for uid, m in members.items() if uid != str(user.id)]
        await self.send(text_data=json.dumps({"type": "welcome", "role": self.role, "peers": others}))
        await self.channel_layer.group_send(self.group_name, {
            "type": "call.event", "skip": self.channel_name,
            "data": {"type": "peer-joined", **self._public(self.me)},
        })
        if others:
            await database_sync_to_async(mark_started)(self.appointment_id)

    async def disconnect(self, close_code):
        me = getattr(self, "me", None)
        if not me:
            return
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        members = cache.get(_members_key(self.appointment_id)) or {}
        current = members.get(str(me["user_id"]))
        if current and current["channel"] == self.channel_name:  # not already replaced by a newer tab
            members.pop(str(me["user_id"]))
            cache.set(_members_key(self.appointment_id), members, 6 * 3600)
            await self.channel_layer.group_send(self.group_name, {
                "type": "call.event", "skip": self.channel_name,
                "data": {"type": "peer-left", **self._public(me)},
            })
            if not members:
                await database_sync_to_async(mark_ended)(self.appointment_id)

    async def receive(self, text_data=None, bytes_data=None):
        if not getattr(self, "me", None) or not text_data:
            return
        try:
            message = json.loads(text_data)
        except json.JSONDecodeError:
            return
        kind = message.get("type")
        if kind == "signal" and isinstance(message.get("data"), dict):
            data = {"type": "signal", "from": self.role, "data": message["data"]}
        elif kind == "media":
            data = {"type": "media", "from": self.role, "audio": bool(message.get("audio")), "video": bool(message.get("video"))}
        else:
            return
        await self.channel_layer.group_send(self.group_name, {"type": "call.event", "skip": self.channel_name, "data": data})

    async def call_event(self, event):
        if event.get("skip") != self.channel_name:
            await self.send(text_data=json.dumps(event["data"]))

    async def call_replaced(self, event):
        self.me = None  # the newer tab owns the seat now; leave without announcing
        await self.send(text_data=json.dumps({"type": "replaced"}))
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.close(code=4010)

    @staticmethod
    def _public(member):
        return {"role": member["role"], "name": member["name"]}
