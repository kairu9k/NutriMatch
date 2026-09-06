import json

from channels.testing import WebsocketCommunicator
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from accounts.models import User
from scheduling.models import RndClientRelationship

from .consumers import MessageConsumer
from .models import Message, NotificationLog


def _make_rnd(email="rnd@t.ph"):
    return User.objects.create_user(email=email, password="x", role="rnd", first_name="R", last_name="D")


def _make_client(email="client@t.ph"):
    return User.objects.create_user(email=email, password="x", role="client", first_name="C", last_name="L")


class MessageViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")

    def test_client_can_send_message_and_it_notifies_the_rnd(self):
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.post(f"/api/relationships/{self.rel.id}/messages/", {"message": "Hi doc!"})

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["sender"]["id"], self.client_user.id)
        self.assertTrue(
            NotificationLog.objects.filter(recipient=self.rnd, notifiable_type="message").exists()
        )

    def test_rnd_can_reply(self):
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.post(f"/api/relationships/{self.rel.id}/messages/", {"message": "Hi there!"})
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_third_party_cannot_read_relationship_messages(self):
        Message.objects.create(relationship=self.rel, sender=self.client_user, message="private")
        outsider = _make_client(email="outsider@t.ph")
        self.client_api.force_authenticate(outsider)

        resp = self.client_api.get(f"/api/relationships/{self.rel.id}/messages/")
        self.assertEqual(resp.status_code, 404)

    def test_messages_ordered_oldest_first(self):
        self.client_api.force_authenticate(self.client_user)
        self.client_api.post(f"/api/relationships/{self.rel.id}/messages/", {"message": "first"})
        self.client_api.post(f"/api/relationships/{self.rel.id}/messages/", {"message": "second"})

        resp = self.client_api.get(f"/api/relationships/{self.rel.id}/messages/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual([m["message"] for m in resp.data], ["first", "second"])

    def test_sender_can_soft_delete_own_message(self):
        msg = Message.objects.create(relationship=self.rel, sender=self.client_user, message="oops")
        self.client_api.force_authenticate(self.client_user)

        resp = self.client_api.delete(f"/api/relationships/{self.rel.id}/messages/{msg.id}/")

        self.assertEqual(resp.status_code, 204)
        msg.refresh_from_db()
        self.assertIsNotNone(msg.deleted_at)

    def test_deleted_message_excluded_from_list(self):
        Message.objects.create(relationship=self.rel, sender=self.client_user, message="visible")
        from django.utils import timezone
        Message.objects.create(
            relationship=self.rel, sender=self.client_user, message="hidden", deleted_at=timezone.now()
        )
        self.client_api.force_authenticate(self.rnd)

        resp = self.client_api.get(f"/api/relationships/{self.rel.id}/messages/")
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["message"], "visible")

    def test_cannot_delete_someone_elses_message(self):
        msg = Message.objects.create(relationship=self.rel, sender=self.client_user, message="mine")
        self.client_api.force_authenticate(self.rnd)

        resp = self.client_api.delete(f"/api/relationships/{self.rel.id}/messages/{msg.id}/")
        self.assertEqual(resp.status_code, 404)


class MessageConsumerTests(TransactionTestCase):
    """Real-time delivery over the actual WebSocket consumer — needs a real
    Redis channel layer (see CHANNEL_LAYERS in settings), same as the app
    itself in dev (docker run -d -p 6379:6379 redis). TransactionTestCase
    because the consumer's DB access happens in a different async context
    than TestCase's wrapping transaction would allow."""

    def setUp(self):
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")

    def _communicator(self, user, relationship_id):
        # WebsocketCommunicator drives the consumer directly, bypassing
        # JwtAuthMiddlewareStack (that's ASGI-app-level, not consumer-level)
        # — so scope['user'] has to be set by hand here, same as the
        # middleware would from the ?token= query param in the real app.
        communicator = WebsocketCommunicator(
            MessageConsumer.as_asgi(),
            f"/ws/relationships/{relationship_id}/messages/",
        )
        communicator.scope["user"] = user
        communicator.scope["url_route"] = {"kwargs": {"relationship_id": str(relationship_id)}}
        return communicator

    async def test_connect_requires_membership_in_the_relationship(self):
        outsider = await self._acreate_outsider()
        communicator = self._communicator(outsider, self.rel.id)
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_connect_succeeds_for_relationship_members(self):
        communicator = self._communicator(self.client_user, self.rel.id)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.disconnect()

    async def test_message_delivered_in_real_time_and_persisted(self):
        rnd_comm = self._communicator(self.rnd, self.rel.id)
        client_comm = self._communicator(self.client_user, self.rel.id)
        await rnd_comm.connect()
        await client_comm.connect()

        await client_comm.send_to(text_data=json.dumps({"message": "hello from client"}))

        # sender gets its own message echoed back (group broadcast includes them)
        own_echo = await client_comm.receive_from()
        self.assertEqual(json.loads(own_echo)["message"], "hello from client")

        # the RND, a separate connection, receives it too — this is the
        # actual real-time delivery the REST API alone can't provide
        received = await rnd_comm.receive_from()
        data = json.loads(received)
        self.assertEqual(data["message"], "hello from client")
        self.assertEqual(data["sender"]["id"], self.client_user.id)

        message_exists = await self._amessage_exists(self.rel.id, "hello from client")
        self.assertTrue(message_exists)

        await rnd_comm.disconnect()
        await client_comm.disconnect()

    async def test_blank_message_is_ignored(self):
        communicator = self._communicator(self.client_user, self.rel.id)
        await communicator.connect()

        await communicator.send_to(text_data=json.dumps({"message": "   "}))
        # nothing should arrive — assertTimeout confirms no message was broadcast
        await communicator.receive_nothing(timeout=1)

        await communicator.disconnect()

    @staticmethod
    async def _acreate_outsider():
        from channels.db import database_sync_to_async
        return await database_sync_to_async(_make_client)(email="ws-outsider@t.ph")

    @staticmethod
    async def _amessage_exists(relationship_id, text):
        from channels.db import database_sync_to_async

        @database_sync_to_async
        def _check():
            return Message.objects.filter(relationship_id=relationship_id, message=text).exists()

        return await _check()


class NotificationViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.user = _make_client()

    def test_list_only_returns_own_in_app_notifications(self):
        NotificationLog.objects.create(
            recipient=self.user, channel=NotificationLog.Channel.IN_APP,
            status=NotificationLog.Status.DELIVERED, subject="Hi",
        )
        other = _make_client(email="other@t.ph")
        NotificationLog.objects.create(
            recipient=other, channel=NotificationLog.Channel.IN_APP,
            status=NotificationLog.Status.DELIVERED, subject="Not yours",
        )

        self.client_api.force_authenticate(self.user)
        resp = self.client_api.get("/api/notifications/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["subject"], "Hi")

    def test_mark_all_read_clears_unread_flag(self):
        NotificationLog.objects.create(
            recipient=self.user, channel=NotificationLog.Channel.IN_APP,
            status=NotificationLog.Status.DELIVERED, is_read=False,
        )
        self.client_api.force_authenticate(self.user)

        resp = self.client_api.patch("/api/notifications/mark-all-read/")

        self.assertEqual(resp.status_code, 204)
        self.assertFalse(NotificationLog.objects.filter(recipient=self.user, is_read=False).exists())
