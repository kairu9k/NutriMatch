"""Weekly hours and time off may end at 12:00 AM: midnight at the end of the day (2026-11-02)."""

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client
from profiles.models import RndAvailabilitySchedule
from scheduling.serializers import fits_rnd_availability

PH = ZoneInfo("Asia/Manila")


class MidnightTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="m@t.ph", password="x", role="rnd", first_name="M", last_name="R"),
                               availability=False)
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)
        self.day = timezone.now().astimezone(PH).date() + timedelta(days=2)
        self.dow = (self.day.weekday() + 1) % 7

    def test_a_block_can_end_at_midnight(self):
        resp = self.api.post("/api/rnd/availability/", {"day_of_week": self.dow, "start_time": "22:00", "end_time": "00:00",
                                                        "effective_from": str(timezone.now().date())}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        # still refused: an end before the start, and a block shorter than nothing
        bad = self.api.post("/api/rnd/availability/", {"day_of_week": self.dow, "start_time": "22:00", "end_time": "21:00",
                                                       "effective_from": str(timezone.now().date())}, format="json")
        self.assertEqual(bad.status_code, 400)

    def test_booking_and_slots_up_to_midnight(self):
        RndAvailabilitySchedule.objects.create(rnd=self.rnd, day_of_week=self.dow, start_time=time(22), end_time=time(0),
                                               effective_from=timezone.now().date())
        at = lambda h: datetime.combine(self.day, time(h), tzinfo=PH)  # noqa: E731
        self.assertTrue(fits_rnd_availability(self.rnd.id, at(23), at(23) + timedelta(hours=1)))  # 11 PM to 12 AM
        self.assertTrue(fits_rnd_availability(self.rnd.id, at(22), at(22) + timedelta(hours=1)))
        self.assertFalse(fits_rnd_availability(self.rnd.id, at(23), at(23) + timedelta(minutes=90)))  # past midnight
        self.assertFalse(fits_rnd_availability(self.rnd.id, at(21), at(22)))

        from profiles.public import next_open_slots

        slots = [s for s in next_open_slots(self.rnd.id) if s.startswith(str(self.day))]
        self.assertEqual([s[11:16] for s in slots], ["22:00", "23:00"])

    def test_time_off_can_end_at_midnight(self):
        RndAvailabilitySchedule.objects.create(rnd=self.rnd, day_of_week=self.dow, start_time=time(20), end_time=time(0),
                                               effective_from=timezone.now().date())
        resp = self.api.post("/api/rnd/time-off/", {"start_date": str(self.day), "start_time": "22:00", "end_time": "00:00"},
                             format="json")
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_overlapping_hours_are_refused_but_a_break_is_fine(self):
        today = str(timezone.now().date())
        post = lambda a, b: self.api.post("/api/rnd/availability/", {"day_of_week": self.dow, "start_time": a, "end_time": b,  # noqa: E731
                                                                     "effective_from": today}, format="json")
        self.assertEqual(post("08:00", "12:00").status_code, 201)
        self.assertEqual(post("13:00", "17:00").status_code, 201)  # lunch break between
        resp = post("11:00", "14:00")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("overlap", str(resp.data))
        self.assertEqual(post("17:00", "00:00").status_code, 201)  # touching is fine, up to midnight
