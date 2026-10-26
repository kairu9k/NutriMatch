"""An RND can't remove or shrink weekly hours that an upcoming booking sits in."""

from datetime import date, datetime, time, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship
from scheduling.serializers import PH_TZ

from .models import RndAvailabilitySchedule


class AvailabilityGuardTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@g.ph", password="x", role="rnd", first_name="Lena", last_name="T"), availability=False)
        client = onboard_client(User.objects.create_user(email="c@g.ph", password="x", role="client", first_name="Ana", last_name="C"))
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=client, status="active")
        # a booking next week, 10:00 to 11:00 Philippine time
        day = (timezone.now().astimezone(PH_TZ) + timedelta(days=7)).date()
        self.weekday = (day.weekday() + 1) % 7
        start = datetime.combine(day, time(10), tzinfo=PH_TZ)
        self.block = RndAvailabilitySchedule.objects.create(rnd=self.rnd, day_of_week=self.weekday, start_time=time(9), end_time=time(12), effective_from=date(2026, 1, 1))
        self.other_day = RndAvailabilitySchedule.objects.create(rnd=self.rnd, day_of_week=(self.weekday + 1) % 7, start_time=time(9), end_time=time(12), effective_from=date(2026, 1, 1))
        self.appt = Appointment.objects.create(relationship=rel, type="video", status="confirmed", scheduled_at=start, duration_minutes=60)
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)

    def test_cannot_remove_hours_with_a_booking(self):
        resp = self.api.delete(f"/api/rnd/availability/{self.block.id}/")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Ana C", resp.data["detail"])
        self.assertTrue(RndAvailabilitySchedule.objects.filter(pk=self.block.pk).exists())

    def test_cannot_shrink_them_past_the_booking(self):
        resp = self.api.patch(f"/api/rnd/availability/{self.block.id}/", {"start_time": "10:30:00"}, format="json")
        self.assertEqual(resp.status_code, 400)
        ok = self.api.patch(f"/api/rnd/availability/{self.block.id}/", {"end_time": "11:00:00"}, format="json")
        self.assertEqual(ok.status_code, 200, ok.data)  # still covers 10:00 to 11:00

    def test_other_days_and_finished_bookings_are_free_to_change(self):
        self.assertEqual(self.api.delete(f"/api/rnd/availability/{self.other_day.id}/").status_code, 204)
        Appointment.objects.filter(pk=self.appt.pk).update(status="cancelled")
        self.assertEqual(self.api.delete(f"/api/rnd/availability/{self.block.id}/").status_code, 204)
