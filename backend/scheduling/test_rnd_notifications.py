"""Notifications added 2026-10-25: RND reminders (request waiting, consultation
in the hour), unanswered requests expiring, new reviews."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from communication.models import NotificationLog
from communication.reminders import run_rnd_reminders
from core.test_utils import approve_rnd, onboard_client

from .models import Appointment, RndClientRelationship


class RndNotificationTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@n.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.c = onboard_client(User.objects.create_user(email="c@n.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        self.now = timezone.now()

    def notes(self, user, subject):
        return NotificationLog.objects.filter(recipient=user, subject=subject)

    def test_request_waiting_reminder_once(self):
        far = Appointment.objects.create(relationship=self.rel, type="video", status="pending", scheduled_at=self.now + timedelta(days=3))
        near = Appointment.objects.create(relationship=self.rel, type="video", status="pending", scheduled_at=self.now + timedelta(hours=5))
        self.assertEqual(run_rnd_reminders(self.now), 1)
        self.assertEqual(run_rnd_reminders(self.now), 0)
        n = self.notes(self.rnd, "Booking request waiting").get()
        self.assertEqual(n.notifiable_id, near.id)
        self.assertIn("Ana Cruz's request", n.content)
        self.assertNotEqual(n.notifiable_id, far.id)

    def test_consultation_soon_reminder_mentions_unpaid(self):
        appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=self.now + timedelta(minutes=40))
        Invoice.objects.create(relationship=self.rel, appointment=appt, amount=Decimal("800"))
        self.assertEqual(run_rnd_reminders(self.now), 1)
        self.assertEqual(run_rnd_reminders(self.now), 0)
        self.assertIn("isn't paid yet", self.notes(self.rnd, "Your consultation starts soon").get().content)

    def test_unanswered_request_expires(self):
        from billing.services import expire_unpaid_appointments

        appt = Appointment.objects.create(relationship=self.rel, type="video", status="pending", scheduled_at=self.now - timedelta(minutes=5))
        expire_unpaid_appointments(relationship__rnd=self.rnd)
        appt.refresh_from_db()
        self.assertEqual(appt.status, "cancelled")
        self.assertIn("book another time", self.notes(self.c, "Booking request expired").get().content)
        self.assertTrue(self.notes(self.rnd, "Booking request expired").exists())

    def test_new_review_notifies_the_rnd(self):
        appt = Appointment.objects.create(relationship=self.rel, type="video", status="completed",
                                          scheduled_at=self.now - timedelta(days=1), completed_at=self.now - timedelta(days=1))
        api = APIClient()
        api.force_authenticate(self.c)
        resp = api.post("/api/client/reviews/", {"appointment": appt.id, "rating": 5, "comment": "Very helpful"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(self.notes(self.rnd, "New review").get().content, 'Ana C. left a 5-star review ★★★★★: "Very helpful"')

    def test_rnd_notifications_page_runs_the_reminders(self):
        Appointment.objects.create(relationship=self.rel, type="video", status="pending", scheduled_at=self.now + timedelta(hours=3))
        api = APIClient()
        api.force_authenticate(self.rnd)
        subjects = [n["subject"] for n in api.get("/api/notifications/").data]
        self.assertIn("Booking request waiting", subjects)
