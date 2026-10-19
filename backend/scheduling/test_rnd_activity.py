"""RND Profile Settings -> History (GET /api/rnd/activity/, 2026-10-19)."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client

from .models import Appointment, Review, RndClientRelationship


class RndActivityTests(TestCase):
    def test_own_activity_newest_first_and_private(self):
        rnd = approve_rnd(User.objects.create_user(email="r@ha.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        other = approve_rnd(User.objects.create_user(email="o@ha.ph", password="x", role="rnd", first_name="Jose", last_name="Reyes"))
        c = onboard_client(User.objects.create_user(email="c@ha.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        rel = RndClientRelationship.objects.create(rnd=rnd, client=c, status="active", started_at=timezone.now() - timedelta(days=5))
        appt = Appointment.objects.create(relationship=rel, type="video", status="completed",
                                          scheduled_at=timezone.now() - timedelta(days=1), completed_at=timezone.now() - timedelta(hours=20))
        Review.objects.create(appointment=appt, client=c, rnd=rnd, rating=5, comment="Very helpful")
        from billing.models import Payout

        Payout.objects.create(rnd=rnd, amount=Decimal("900"), payout_date=timezone.localdate(), method="gcash",
                              account_name="Maria Santos", account_number="09171234567", reference="GC-1",
                              released_at=timezone.now() - timedelta(hours=1))
        api = APIClient()
        api.force_authenticate(rnd)
        items = api.get("/api/rnd/activity/").data
        titles = [i["title"] for i in items]
        self.assertIn("Ana Cruz left a 5-star review", titles)
        self.assertIn("Completed a video consultation with Ana Cruz", titles)
        self.assertIn("Ana Cruz became your patient", titles)
        self.assertIn("Payout of ₱900.00 sent to your GCash", titles)
        self.assertEqual(titles[-1], "Ana Cruz became your patient")  # oldest last
        self.assertEqual({i["type"] for i in items}, {"review", "consultation", "patient", "payout"})
        # another RND sees none of it; clients can't call it
        api.force_authenticate(other)
        self.assertEqual(api.get("/api/rnd/activity/").data, [])
        api.force_authenticate(c)
        self.assertEqual(api.get("/api/rnd/activity/").status_code, 403)
