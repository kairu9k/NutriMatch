"""Client side of the consultation room: only public / own data."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from clinical.models import NcpRecord, ProgressRecord
from core.test_utils import approve_rnd, onboard_client
from nutrition.models import MealPlan

from .models import Appointment, ConsultationSession, RndClientRelationship


class ClientRoomInfoTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@room.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@room.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        self.appt = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=timezone.now() + timedelta(minutes=5))
        ConsultationSession.objects.create(appointment=self.appt, host_url="https://meet.jit.si/secret-host", participant_url="https://meet.jit.si/room")
        MealPlan.objects.create(relationship=self.rel, name="Low-GI plan", status="active", sent_at=timezone.now(), target_kcal=Decimal("1500"))
        NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date(), assessment_notes="PRIVATE-NCP-NOTE")
        ProgressRecord.objects.create(relationship=self.rel, record_date=timezone.now().date(), weight_kg=Decimal("60"), rnd_notes="PRIVATE-RND-NOTE")
        self.api = APIClient()
        self.api.force_authenticate(self.c)

    def test_room_info_is_public_and_own_only(self):
        resp = self.api.get(f"/api/client/appointments/{self.appt.id}/room-info/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["rnd"]["name"], "Maria S")
        self.assertEqual(resp.data["meal_plan"]["target_kcal"], 1500.0)
        body = str(resp.content)
        for secret in ("secret-host", "PRIVATE-NCP-NOTE", "PRIVATE-RND-NOTE", "r@room.ph"):
            self.assertNotIn(secret, body)

    def test_other_clients_cannot_read_it(self):
        other = onboard_client(User.objects.create_user(email="o@room.ph", password="x", role="client", first_name="O", last_name="C"))
        self.api.force_authenticate(other)
        self.assertEqual(self.api.get(f"/api/client/appointments/{self.appt.id}/room-info/").status_code, 404)
