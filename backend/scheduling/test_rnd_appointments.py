"""RND Appointments board and the decline/cancel reason."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from clinical.models import PreConsultationScreening
from core.test_utils import approve_rnd, onboard_client

from .models import Appointment, RndClientRelationship


class RndAppointmentBoardTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@b.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@b.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        PreConsultationScreening.objects.create(client=self.c, height_cm=Decimal("160"), weight_kg=Decimal("60"), nrs_score=3)
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)
        now = timezone.now()
        mk = lambda status, delta: Appointment.objects.create(relationship=self.rel, type="video", status=status, scheduled_at=now + delta)  # noqa: E731
        self.req = mk("pending", timedelta(days=2))
        self.up = mk("confirmed", timedelta(days=1))
        self.ended = mk("confirmed", -timedelta(hours=3))
        self.done = mk("completed", -timedelta(days=5))

    def test_buckets(self):
        d = self.api.get("/api/rnd/appointments/board/").data
        self.assertEqual([r["id"] for r in d["requests"]], [self.req.id])
        self.assertEqual([r["id"] for r in d["upcoming"]], [self.up.id])
        self.assertEqual([r["id"] for r in d["to_complete"]], [self.ended.id])
        self.assertEqual([r["id"] for r in d["history"]], [self.done.id])
        req = d["requests"][0]
        self.assertTrue(req["screening"]["submitted"])
        self.assertEqual(req["screening"]["nrs_score"], 3)
        self.assertTrue(req["returning"])
        self.assertEqual(d["summary"]["requests"], 1)

    def test_decline_and_cancel_need_a_reason(self):
        url = f"/api/rnd/appointments/{self.req.id}/cancel/"
        self.assertEqual(self.api.patch(url, {"reason": "no"}, format="json").status_code, 400)
        self.assertEqual(Appointment.objects.get(pk=self.req.id).status, "pending")
        resp = self.api.patch(url, {"reason": "  Fully booked that day, please pick another time.  "}, format="json")
        self.assertEqual(resp.status_code, 200)
        appt = Appointment.objects.get(pk=self.req.id)
        self.assertEqual((appt.status, appt.cancellation_reason), ("cancelled", "Fully booked that day, please pick another time."))

    def test_board_is_rnd_only(self):
        self.api.force_authenticate(self.c)
        self.assertEqual(self.api.get("/api/rnd/appointments/board/").status_code, 403)
