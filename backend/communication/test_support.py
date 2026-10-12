"""Help & Support requests: user → admins and back, ownership, limits, notifications."""

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship

from .models import NotificationLog, SupportTicket


class SupportTests(TestCase):
    def setUp(self):
        self.client_user = onboard_client(User.objects.create_user(email="c@s.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.rnd = approve_rnd(User.objects.create_user(email="r@s.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.admin = User.objects.create_user(email="a@s.ph", password="x", role="admin", first_name="Ada", last_name="Min")
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=timezone.now())
        self.api = APIClient()
        self.api.force_authenticate(self.client_user)

    def open_ticket(self, **extra):
        return self.api.post("/api/support/tickets/", {
            "category": "payment", "subject": "Charged twice", "message": "I was charged twice for my consultation.", **extra,
        }, format="json")

    def test_full_conversation(self):
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.open_ticket(appointment=self.appt.id)
        self.assertEqual(resp.status_code, 201, resp.data)
        tid = resp.data["id"]
        self.assertEqual(resp.data["reference"], f"SR-{tid:04d}")
        self.assertIn("Maria Santos", resp.data["appointment"]["label"])
        # Admins are notified in-app and the support inbox gets an email.
        self.assertTrue(NotificationLog.objects.filter(recipient=self.admin, notifiable_type="support", notifiable_id=tid).exists())
        self.assertEqual(len(mail.outbox), 1)

        admin = APIClient()
        admin.force_authenticate(self.admin)
        listing = admin.get("/api/admin/support/tickets/").data
        self.assertEqual(listing["counts"]["open"], 1)
        self.assertTrue(listing["results"][0]["unread"])
        self.assertEqual(listing["results"][0]["user"]["email"], "c@s.ph")
        self.assertFalse(admin.get(f"/api/admin/support/tickets/{tid}/").data["unread"])  # opening marks it read

        with self.captureOnCommitCallbacks(execute=True):
            reply = admin.post(f"/api/admin/support/tickets/{tid}/messages/", {"body": "Refund is on the way."}, format="json")
        self.assertEqual(reply.data["status"], "answered")
        self.assertTrue(NotificationLog.objects.filter(recipient=self.client_user, notifiable_type="support").exists())
        self.assertEqual(mail.outbox[-1].to, ["c@s.ph"])

        self.assertEqual(self.api.get("/api/support/unread/").data["count"], 1)
        thread = self.api.get(f"/api/support/tickets/{tid}/").data
        self.assertEqual([m["from_support"] for m in thread["messages"]], [False, True])
        self.assertEqual(thread["messages"][1]["sender_name"], "NutriMatch Support")  # admin's name hidden from users
        self.assertEqual(self.api.get("/api/support/unread/").data["count"], 0)

        self.api.post(f"/api/support/tickets/{tid}/close/")
        self.assertEqual(SupportTicket.objects.get(pk=tid).status, "closed")
        back = self.api.post(f"/api/support/tickets/{tid}/messages/", {"body": "It happened again."}, format="json")
        self.assertEqual(back.data["status"], "open")  # replying reopens it

    def test_only_own_records(self):
        other = onboard_client(User.objects.create_user(email="o@s.ph", password="x", role="client", first_name="O", last_name="C"))
        other_rel = RndClientRelationship.objects.create(rnd=self.rnd, client=other, status="active")
        other_appt = Appointment.objects.create(relationship=other_rel, type="video", status="confirmed", scheduled_at=timezone.now())
        self.assertEqual(self.open_ticket(appointment=other_appt.id).status_code, 400)
        tid = self.open_ticket().data["id"]
        stranger = APIClient()
        stranger.force_authenticate(other)
        self.assertEqual(stranger.get(f"/api/support/tickets/{tid}/").status_code, 404)
        self.assertEqual(stranger.get("/api/admin/support/tickets/").status_code, 403)

    def test_rnd_can_use_it_and_admin_cannot_open_one(self):
        rnd_api = APIClient()
        rnd_api.force_authenticate(self.rnd)
        resp = rnd_api.post("/api/support/tickets/", {"category": "account", "subject": "Payout details", "message": "How do I change my GCash number?"}, format="json")
        self.assertEqual(resp.status_code, 201)
        admin = APIClient()
        admin.force_authenticate(self.admin)
        self.assertEqual(admin.get("/api/support/tickets/").status_code, 403)

    def test_validation_and_hourly_limit(self):
        self.assertEqual(self.open_ticket(subject="Hi").status_code, 400)
        self.assertEqual(self.open_ticket(message="short").status_code, 400)
        self.assertEqual(self.open_ticket(category="spam").status_code, 400)
        for _ in range(5):
            self.assertEqual(self.open_ticket().status_code, 201)
        self.assertEqual(self.open_ticket().status_code, 400)

    def test_links_and_notification_detail(self):
        links = self.api.get("/api/support/links/").data
        self.assertEqual(links["appointments"][0]["id"], self.appt.id)
        tid = self.open_ticket().data["id"]
        note = NotificationLog.objects.get(recipient=self.admin, notifiable_id=tid)
        admin = APIClient()
        admin.force_authenticate(self.admin)
        self.assertEqual(admin.get(f"/api/notifications/{note.id}/").data["related"]["reference"], f"SR-{tid:04d}")
