"""RND time off (whole or part days) and hourly booking starts."""

from datetime import datetime, time, timedelta

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, booking_slot, onboard_client
from scheduling.models import Appointment, RndClientRelationship
from scheduling.serializers import PH_TZ

from .models import RndAvailabilitySchedule, RndTimeOff
from .public import next_open_slots


class TimeOffTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@t.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.client_user = onboard_client(User.objects.create_user(email="c@t.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.rnd_api, self.api = APIClient(), APIClient()
        self.rnd_api.force_authenticate(self.rnd)
        self.api.force_authenticate(self.client_user)
        self.day = booking_slot(3).date()

    def _book(self, when, duration=60):
        return self.api.post("/api/client/appointments/", {
            "rnd_id": self.rnd.id, "type": "video", "duration_minutes": duration, "scheduled_at": when.isoformat(),
        }, format="json")

    def _at(self, hour, minute=0, day=None):
        return datetime.combine(day or self.day, time(hour, minute), tzinfo=PH_TZ)

    def test_rules(self):
        post = lambda body: self.rnd_api.post("/api/rnd/time-off/", body, format="json")
        today = booking_slot(0).date()
        self.assertEqual(post({"start_date": str(today - timedelta(days=1))}).status_code, 400)  # past
        self.assertEqual(post({"start_date": str(self.day), "end_date": str(self.day - timedelta(days=1))}).status_code, 400)
        self.assertEqual(post({"start_date": str(self.day), "end_date": str(self.day + timedelta(days=90))}).status_code, 400)
        self.assertEqual(post({"start_date": str(self.day), "start_time": "13:00"}).status_code, 400)  # half a range
        self.assertEqual(post({"start_date": str(self.day), "start_time": "13:00", "end_time": "13:30"}).status_code, 400)
        ok = post({"start_date": str(self.day), "reason": "Holiday"})
        self.assertEqual(ok.status_code, 201, ok.data)
        self.assertTrue(ok.data["whole_day"])
        self.assertEqual(ok.data["end_date"], str(self.day))  # one day when no end date
        self.assertEqual(len(self.rnd_api.get("/api/rnd/time-off/").data), 1)
        self.assertEqual(self.rnd_api.delete(f"/api/rnd/time-off/{ok.data['id']}/").status_code, 204)

    def test_whole_day_blocks_booking_and_next_available(self):
        RndTimeOff.objects.create(rnd=self.rnd, start_date=self.day, end_date=self.day)
        resp = self._book(self._at(10))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("isn't available", str(resp.data))
        self.assertEqual(self._book(self._at(10, day=self.day + timedelta(days=1))).status_code, 201)

        start_of_day = self._at(0)
        slots = next_open_slots(self.rnd.id, count=30, now=start_of_day - timedelta(hours=1))
        self.assertFalse(any(datetime.fromisoformat(s).astimezone(PH_TZ).date() == self.day for s in slots))

    def test_part_day_blocks_only_those_hours_on_each_date(self):
        RndTimeOff.objects.create(rnd=self.rnd, start_date=self.day, end_date=self.day + timedelta(days=1),
                                  start_time=time(13), end_time=time(17))
        self.assertEqual(self._book(self._at(13)).status_code, 400)
        self.assertEqual(self._book(self._at(12, day=self.day + timedelta(days=1)), duration=90).status_code, 400)  # runs into 13:00
        self.assertEqual(self._book(self._at(12)).status_code, 201)  # 12-13 ends right at the block
        self.assertEqual(self._book(self._at(17, day=self.day + timedelta(days=1))).status_code, 201)

        slots = self.api.get(f"/api/client/rnds/{self.rnd.id}/booked-slots/").data
        blocked = [s for s in slots if s["kind"] == "time_off"]
        self.assertEqual(len(blocked), 2)
        self.assertNotIn("reason", blocked[0])

    def test_new_block_lists_existing_bookings_it_covers(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        Appointment.objects.create(relationship=rel, type="video", status="confirmed", duration_minutes=60, scheduled_at=self._at(14))
        resp = self.rnd_api.post("/api/rnd/time-off/", {"start_date": str(self.day), "start_time": "13:00", "end_time": "17:00"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual([c["client_name"] for c in resp.data["conflicts"]], ["Ana Cruz"])
        self.assertEqual(Appointment.objects.get().status, "confirmed")  # not auto-cancelled

    def test_starts_are_hourly_from_the_block_start(self):
        RndAvailabilitySchedule.objects.filter(rnd=self.rnd).delete()
        dow = (self.day.weekday() + 1) % 7
        RndAvailabilitySchedule.objects.create(rnd=self.rnd, day_of_week=dow, start_time=time(8, 30), end_time=time(12, 30),
                                               effective_from=self.day - timedelta(days=7))
        self.assertEqual(self._book(self._at(9)).status_code, 400)   # not on the 8:30 grid
        self.assertEqual(self._book(self._at(9, 30)).status_code, 201)

    def test_block_must_cover_working_hours(self):
        # Mondays and Thursdays 9:00 AM - 5:00 PM only.
        RndAvailabilitySchedule.objects.filter(rnd=self.rnd).delete()
        start = booking_slot(0).date()
        for dow in (1, 4):
            RndAvailabilitySchedule.objects.create(rnd=self.rnd, day_of_week=dow, start_time=time(9), end_time=time(17),
                                                   effective_from=start - timedelta(days=7))
        upcoming = lambda py_weekday: next(start + timedelta(days=i) for i in range(1, 8)
                                           if (start + timedelta(days=i)).weekday() == py_weekday)
        tue, thu = upcoming(1), upcoming(3)
        post = lambda body: self.rnd_api.post("/api/rnd/time-off/", body, format="json")

        resp = post({"start_date": str(tue)})  # whole day with no hours set
        self.assertEqual(resp.status_code, 400)
        self.assertIn("no hours on Tuesdays", str(resp.data))
        resp = post({"start_date": str(thu), "start_time": "03:00", "end_time": "04:00"})  # outside 9-5
        self.assertEqual(resp.status_code, 400)
        self.assertIn("outside your Thursday hours (9:00 AM – 5:00 PM)", str(resp.data))
        self.assertEqual(post({"start_date": str(thu), "start_time": "17:00", "end_time": "18:00"}).status_code, 400)  # touches only

        self.assertEqual(post({"start_date": str(thu), "start_time": "08:00", "end_time": "10:00"}).status_code, 201)  # partly inside
        self.assertEqual(post({"start_date": str(thu), "start_time": "13:00", "end_time": "15:00"}).status_code, 201)
        self.assertEqual(post({"start_date": str(tue), "end_date": str(tue + timedelta(days=6))}).status_code, 201)  # a week of leave
        self.assertEqual(RndTimeOff.objects.count(), 3)

        RndAvailabilitySchedule.objects.filter(rnd=self.rnd).delete()
        resp = post({"start_date": str(thu)})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Add your weekly availability first", str(resp.data))
