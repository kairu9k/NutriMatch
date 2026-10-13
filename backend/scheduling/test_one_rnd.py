"""One RND at a time: a client can book a different RND only after their
current RND discharges them."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, booking_slot, onboard_client

from .models import Appointment, RndClientRelationship
from .services import current_rnd_relationship


class OneRndAtATimeTests(TestCase):
    def setUp(self):
        self.a = approve_rnd(User.objects.create_user(email="a@o.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.b = approve_rnd(User.objects.create_user(email="b@o.ph", password="x", role="rnd", first_name="Jose", last_name="Reyes"))
        self.c = onboard_client(User.objects.create_user(email="c@o.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.api = APIClient()
        self.api.force_authenticate(self.c)

    def test_active_rnd_blocks_another_until_discharged(self):
        rel = RndClientRelationship.objects.create(rnd=self.a, client=self.c, status="active")
        self.assertEqual(current_rnd_relationship(self.c, exclude_rnd_id=self.b.id), rel)
        detail = self.api.get(f"/api/client/rnds/{self.b.id}/").data
        self.assertEqual(detail["booking_blocked_by"]["name"], "Maria Santos")
        self.assertIsNone(self.api.get(f"/api/client/rnds/{self.a.id}/").data["booking_blocked_by"])  # own RND is fine
        rel.status = "discharged"
        rel.save()
        self.assertIsNone(current_rnd_relationship(self.c, exclude_rnd_id=self.b.id))
        self.assertIsNone(self.api.get(f"/api/client/rnds/{self.b.id}/").data["booking_blocked_by"])

    def test_waiting_first_booking_blocks_but_a_declined_one_does_not(self):
        rel = RndClientRelationship.objects.create(rnd=self.a, client=self.c, status="pending")
        appt = Appointment.objects.create(relationship=rel, type="video", status="pending", scheduled_at=timezone.now() + timedelta(days=1))
        self.assertEqual(current_rnd_relationship(self.c, exclude_rnd_id=self.b.id), rel)
        appt.status = "cancelled"
        appt.save()
        self.assertIsNone(current_rnd_relationship(self.c, exclude_rnd_id=self.b.id))

    def test_booking_api_refuses_a_second_rnd(self):
        RndClientRelationship.objects.create(rnd=self.a, client=self.c, status="active")
        resp = self.api.post("/api/client/appointments/", {
            "rnd_id": self.b.id, "type": "video", "duration_minutes": 60,
            "scheduled_at": booking_slot(2).isoformat(),
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("discharges you", str(resp.data))
