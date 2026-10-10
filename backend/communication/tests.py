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


class NotificationDetailTests(TestCase):
    """The notification overlay: full detail + what it's about, own records only."""

    def setUp(self):
        from datetime import timedelta
        from decimal import Decimal

        from django.utils import timezone

        from billing.models import Invoice
        from scheduling.models import Appointment

        from .services import notify

        self.api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.appt = Appointment.objects.create(relationship=self.rel, scheduled_at=timezone.now() + timedelta(days=2), type="video", duration_minutes=60, status="confirmed")
        self.invoice = Invoice.objects.create(relationship=self.rel, appointment=self.appt, amount=Decimal("800.00"))
        self.msg = Message.objects.create(relationship=self.rel, sender=self.rnd, message="See you on Friday! " * 20)
        self.n_appt = notify(self.client_user, "appointment", self.appt.id, "Appointment confirmed", "Confirmed.")
        self.n_inv = notify(self.client_user, "invoice", self.invoice.id, "Invoice issued", "Please pay.")
        self.n_msg = notify(self.client_user, "message", self.msg.id, "New message", "R D: See you…")

    def _get(self, n, user=None):
        self.api.force_authenticate(user or self.client_user)
        return self.api.get(f"/api/notifications/{n.id}/")

    def test_appointment_detail(self):
        resp = self._get(self.n_appt)
        self.assertEqual(resp.status_code, 200, resp.data)
        rel = resp.data["related"]
        self.assertEqual(rel["with"]["name"], "R D")
        self.assertEqual(rel["status"], "confirmed")
        self.assertEqual(rel["invoice"]["id"], self.invoice.id)

    def test_invoice_detail(self):
        rel = self._get(self.n_inv).data["related"]
        self.assertEqual(str(rel["amount"]), "800.00")
        self.assertEqual(rel["status"], "unpaid")
        self.assertEqual(rel["appointment"]["id"], self.appt.id)

    def test_message_detail_has_full_text_and_relationship(self):
        rel = self._get(self.n_msg).data["related"]
        self.assertEqual(rel["message"], self.msg.message)
        self.assertEqual(rel["relationship_id"], self.rel.id)

    def test_other_users_cannot_open_it(self):
        other = _make_client("other@t.ph")
        self.assertEqual(self._get(self.n_appt, other).status_code, 404)

    def test_related_is_hidden_when_record_is_not_the_recipients(self):
        from .services import notify

        other = _make_client("other2@t.ph")
        n = notify(other, "appointment", self.appt.id, "x", "y")  # points at someone else's appointment
        self.assertIsNone(self._get(n, other).data["related"])


class ResourceSharingTests(TestCase):
    """RND uploads a resource, picks which confirmed clients get it; those
    clients can view + download it."""

    FILE_URL = "https://res.cloudinary.com/demo/image/upload/v1/resources/abc.pdf"

    def setUp(self):
        from core.test_utils import approve_rnd

        self.api = APIClient()
        self.rnd = _make_rnd()
        approve_rnd(self.rnd)
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")

    def _resource(self, share_with=(), **fields):
        from .models import Resource, ResourceShare

        defaults = {"uploaded_by": self.rnd, "title": "Healthy Plate Guide", "type": "pdf", "file_path": self.FILE_URL}
        defaults.update(fields)
        resource = Resource.objects.create(**defaults)
        for rel in share_with:
            ResourceShare.objects.create(resource=resource, relationship=rel)
        return resource

    def _client_titles(self, user):
        self.api.force_authenticate(user)
        return [r["title"] for r in self.api.get("/api/client/resources/").data]

    def test_active_client_gets_view_and_download_links(self):
        self._resource(share_with=[self.rel])
        self.api.force_authenticate(self.client_user)
        resp = self.api.get("/api/client/resources/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["file_path"], self.FILE_URL)
        self.assertEqual(
            resp.data[0]["download_url"],
            "https://res.cloudinary.com/demo/image/upload/fl_attachment:healthy-plate-guide/v1/resources/abc.pdf",
        )

    def test_video_and_raw_download_urls(self):
        from .serializers import resource_download_url

        self.assertEqual(
            resource_download_url("https://res.cloudinary.com/d/video/upload/v1/r/a.mp4", "Meal Prep 101"),
            "https://res.cloudinary.com/d/video/upload/fl_attachment:meal-prep-101/v1/r/a.mp4",
        )
        raw = "https://res.cloudinary.com/d/raw/upload/v1/r/a.docx"
        self.assertEqual(resource_download_url(raw, "Doc"), raw)
        self.assertIsNone(resource_download_url(None, "Link"))

    def test_link_resource_has_no_download_url(self):
        self._resource(share_with=[self.rel], type="link", file_path=None, url="https://fnri.dost.gov.ph")
        self.api.force_authenticate(self.client_user)
        resp = self.api.get("/api/client/resources/")

        self.assertIsNone(resp.data[0]["download_url"])
        self.assertEqual(resp.data[0]["url"], "https://fnri.dost.gov.ph")

    def test_client_sees_who_shared_it_and_when(self):
        self._resource(share_with=[self.rel])
        self.api.force_authenticate(self.client_user)
        row = self.api.get("/api/client/resources/").data[0]
        self.assertEqual(row["shared_by"]["name"], self.rnd.full_name)
        self.assertIsNotNone(row["shared_at"])
        self.assertNotIn("shared_count", row)  # how many others got it is the RND's business

    def test_uploading_alone_shares_with_nobody(self):
        self._resource()
        self.assertEqual(self._client_titles(self.client_user), [])

    def test_only_clients_it_was_shared_with_see_it(self):
        second = _make_client("second@t.ph")
        second_rel = RndClientRelationship.objects.create(rnd=self.rnd, client=second, status="active")
        self._resource(share_with=[second_rel], title="Only for second")
        self._resource(share_with=[self.rel], is_active=False, title="Hidden by RND")

        self.assertEqual(self._client_titles(self.client_user), [])
        self.assertEqual(self._client_titles(second), ["Only for second"])

    def test_share_list_shows_only_the_rnds_confirmed_clients(self):
        pending = _make_client("pending@t.ph")
        RndClientRelationship.objects.create(rnd=self.rnd, client=pending, status="pending")
        other_rnd = _make_rnd("other@t.ph")
        their_client = _make_client("theirs@t.ph")
        RndClientRelationship.objects.create(rnd=other_rnd, client=their_client, status="active")
        resource = self._resource(share_with=[self.rel])

        self.api.force_authenticate(self.rnd)
        resp = self.api.get(f"/api/rnd/resources/{resource.id}/share/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([r["client"]["email"] for r in resp.data], ["client@t.ph"])
        self.assertTrue(resp.data[0]["shared"])

    def test_share_notifies_new_recipients_once(self):
        resource = self._resource()
        self.api.force_authenticate(self.rnd)
        url = f"/api/rnd/resources/{resource.id}/share/"

        resp = self.api.post(url, {"relationship_ids": [self.rel.id]}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data[0]["shared"])
        self.assertEqual(self._client_titles(self.client_user), ["Healthy Plate Guide"])

        self.api.force_authenticate(self.rnd)
        self.api.post(url, {"relationship_ids": [self.rel.id]}, format="json")
        notes = NotificationLog.objects.filter(recipient=self.client_user, notifiable_type="resource")
        self.assertEqual(notes.count(), 1)
        self.assertEqual(resource.shares.count(), 1)

        self.api.force_authenticate(self.client_user)
        detail = self.api.get(f"/api/notifications/{notes.first().id}/").data
        self.assertEqual(detail["related"]["title"], "Healthy Plate Guide")

        self.api.force_authenticate(self.rnd)
        listed = self.api.get("/api/rnd/resources/").data
        self.assertEqual(listed[0]["shared_count"], 1)

    def test_cannot_share_with_unconfirmed_or_other_rnds_clients(self):
        resource = self._resource()
        pending = _make_client("pending@t.ph")
        pending_rel = RndClientRelationship.objects.create(rnd=self.rnd, client=pending, status="pending")
        other_rnd = _make_rnd("other@t.ph")
        theirs = RndClientRelationship.objects.create(rnd=other_rnd, client=_make_client("theirs@t.ph"), status="active")

        self.api.force_authenticate(self.rnd)
        url = f"/api/rnd/resources/{resource.id}/share/"
        for ids in ([pending_rel.id], [theirs.id], [self.rel.id, theirs.id], [], "x", [True]):
            resp = self.api.post(url, {"relationship_ids": ids}, format="json")
            self.assertEqual(resp.status_code, 400, ids)
        self.assertEqual(resource.shares.count(), 0)

    def test_other_rnd_cannot_touch_my_resource(self):
        from core.test_utils import approve_rnd

        resource = self._resource(share_with=[self.rel])
        other_rnd = _make_rnd("other@t.ph")
        approve_rnd(other_rnd)
        self.api.force_authenticate(other_rnd)

        self.assertEqual(self.api.get(f"/api/rnd/resources/{resource.id}/share/").status_code, 404)
        self.assertEqual(self.api.delete(f"/api/rnd/resources/{resource.id}/share/{self.rel.id}/").status_code, 404)
        self.assertEqual(resource.shares.count(), 1)

    def test_unshare_and_discharge_remove_access(self):
        resource = self._resource(share_with=[self.rel])
        self.api.force_authenticate(self.rnd)
        resp = self.api.delete(f"/api/rnd/resources/{resource.id}/share/{self.rel.id}/")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(self._client_titles(self.client_user), [])

        self._resource(share_with=[self.rel], title="Second")
        self.assertEqual(self._client_titles(self.client_user), ["Second"])
        self.rel.status = "discharged"
        self.rel.save(update_fields=["status"])
        self.assertEqual(self._client_titles(self.client_user), [])

    def test_upload_rejects_wrong_file_type_and_oversized_files(self):
        from unittest.mock import patch

        from django.core.files.uploadedfile import SimpleUploadedFile

        self.api.force_authenticate(self.rnd)
        with patch("communication.views.CloudinaryResourceUploadService.upload") as upload:
            wrong = SimpleUploadedFile("notes.exe", b"x", content_type="application/octet-stream")
            resp = self.api.post("/api/rnd/resources/", {"title": "T", "type": "pdf", "file": wrong}, format="multipart")
            self.assertEqual(resp.status_code, 400)
            self.assertIn("file", resp.data)

            big = SimpleUploadedFile("guide.pdf", b"x" * (10 * 1024 * 1024 + 1), content_type="application/pdf")
            resp = self.api.post("/api/rnd/resources/", {"title": "T", "type": "pdf", "file": big}, format="multipart")
            self.assertEqual(resp.status_code, 400)
            self.assertIn("10 MB", str(resp.data["file"]))
            upload.assert_not_called()

            upload.return_value = self.FILE_URL
            ok = SimpleUploadedFile("Guide.PDF", b"%PDF-1.4", content_type="application/pdf")
            resp = self.api.post("/api/rnd/resources/", {"title": "Guide", "type": "pdf", "file": ok}, format="multipart")
            self.assertEqual(resp.status_code, 201, resp.data)
            self.assertEqual(resp.data["file_path"], self.FILE_URL)
            self.assertIn("fl_attachment:guide/", resp.data["download_url"])

    def test_new_upload_is_active_and_visible_once_shared(self):
        """The upload form sends no is_active; that must not hide the file."""
        from unittest.mock import patch

        from django.core.files.uploadedfile import SimpleUploadedFile

        self.api.force_authenticate(self.rnd)
        with patch("communication.views.CloudinaryResourceUploadService.upload", return_value=self.FILE_URL):
            pdf = SimpleUploadedFile("plate.pdf", b"%PDF-1.4", content_type="application/pdf")
            resp = self.api.post("/api/rnd/resources/", {"title": "Plate", "type": "pdf", "file": pdf}, format="multipart")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertTrue(resp.data["is_active"])

        self.api.post(f"/api/rnd/resources/{resp.data['id']}/share/", {"relationship_ids": [self.rel.id]}, format="json")
        self.assertEqual(self._client_titles(self.client_user), ["Plate"])

        note = NotificationLog.objects.get(recipient=self.client_user, notifiable_type="resource")
        detail = self.api.get(f"/api/notifications/{note.id}/").data
        self.assertEqual(detail["related"]["title"], "Plate")
