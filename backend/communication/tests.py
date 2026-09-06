from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from scheduling.models import RndClientRelationship

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
