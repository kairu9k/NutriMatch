"""Demo mode for the defense (scheduling/demo.py, 2026-11-27): no booking lead, the room opens once
confirmed and paid, Pay still goes through the provider; off by default, every rule back when off."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from billing.models import Invoice
from billing.services import create_appointment_invoice, expire_unpaid_appointments
from profiles.models import RndAvailabilitySchedule

from rest_framework.exceptions import ValidationError

from .models import Appointment
from .serializers import AppointmentCreateSerializer, deadlines
from .test_no_shows import _ConsultationSetup
from .video_call import join_window


class _DemoSetup(_ConsultationSetup):
    def setUp(self):
        super().setUp()
        RndAvailabilitySchedule.objects.filter(rnd=self.rnd).delete()  # any time fits

    def unpaid(self, minutes_from_now):
        a = Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", duration_minutes=60,
                                       scheduled_at=timezone.now() + timedelta(minutes=minutes_from_now))
        inv, _ = create_appointment_invoice(a)
        return a, inv


class DemoModeOffTests(_DemoSetup, TestCase):
    def test_config_says_off(self):
        self.assertEqual(self.client_api.get("/api/public/config/").json(), {"demo_mode": False})

    def test_booking_still_needs_the_lead(self):
        with self.assertRaises(ValidationError) as err:
            AppointmentCreateSerializer().validate_scheduled_at(timezone.now() + timedelta(minutes=10))
        self.assertIn("45 minutes", str(err.exception))

    def test_deadlines_unchanged(self):
        a, _ = self.unpaid(120)
        d = deadlines(a)
        self.assertEqual(d["confirm_by"], a.scheduled_at - timedelta(minutes=30))
        self.assertEqual(d["pay_by"], a.scheduled_at - timedelta(minutes=15))

    @override_settings(PAYMENT_PROVIDER="paymongo")
    def test_pay_still_goes_to_paymongo(self):
        a, inv = self.unpaid(120)
        with patch("billing.views.PayMongoService.create_payment_link",
                   return_value={"payment_url": "https://checkout.example/cs_1", "gateway_reference_id": "cs_1"}) as link:
            resp = self.client_api.post(f"/api/client/invoices/{inv.id}/pay/")
        self.assertEqual(resp.status_code, 200)
        link.assert_called_once()
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.Status.UNPAID)
        self.assertEqual(resp.data["payment_url"], "https://checkout.example/cs_1")

    def test_room_opens_fifteen_minutes_before(self):
        a, _ = self.unpaid(120)
        opens, _ = join_window(a)
        self.assertEqual(opens, a.scheduled_at - timedelta(minutes=15))


@override_settings(DEMO_MODE=True)
class DemoModeOnTests(_DemoSetup, TestCase):
    def test_config_says_on(self):
        self.assertEqual(self.client_api.get("/api/public/config/").json(), {"demo_mode": True})

    def test_booking_a_few_minutes_ahead(self):
        when = timezone.now() + timedelta(minutes=10)
        self.assertEqual(AppointmentCreateSerializer().validate_scheduled_at(when), when)

    def test_booking_a_time_that_started_is_still_refused(self):
        with self.assertRaises(ValidationError):
            AppointmentCreateSerializer().validate_scheduled_at(timezone.now() - timedelta(minutes=10))

    def test_confirm_and_pay_until_the_start(self):
        a, _ = self.unpaid(10)
        d = deadlines(a)
        self.assertEqual(d["confirm_by"], a.scheduled_at)
        self.assertEqual(d["pay_by"], a.scheduled_at)
        self.assertEqual(d["cancel_by"], a.scheduled_at - timedelta(minutes=30))  # unchanged

    def test_pay_still_goes_through_the_provider(self):
        a, inv = self.unpaid(10)
        with patch("billing.xendit.XenditService.create_payment_link",
                   return_value={"payment_url": "https://checkout.xendit.example/inv_1",
                                 "gateway_reference_id": "inv_1"}) as link:
            resp = self.client_api.post(f"/api/client/invoices/{inv.id}/pay/")
        self.assertEqual(resp.status_code, 200, resp.data)
        link.assert_called_once()
        self.assertEqual(link.call_args.kwargs["pay_by"], a.scheduled_at)  # open until the start
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.Status.UNPAID)
        self.assertEqual(inv.payment_gateway, Invoice.PaymentGateway.XENDIT)

    def test_unpaid_isnt_cancelled_before_the_start(self):
        a, _ = self.unpaid(10)
        expire_unpaid_appointments()
        a.refresh_from_db()
        self.assertEqual(a.status, "confirmed")

    def test_room_opens_well_before_the_start(self):
        a, _ = self.unpaid(120)
        opens, _ = join_window(a)
        self.assertLessEqual(opens, timezone.now())


class InPersonRoomOpensOnTheDayTests(_DemoSetup, TestCase):
    """2026-11-27 (user's call): an in-person visit's room opens from the start of its day (PH time),
    so a client who arrives early can be seen; video keeps the 15-minute rule."""

    def _at(self, type_, hour):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        when = datetime(2026, 12, 3, hour, 0, tzinfo=ZoneInfo("Asia/Manila"))
        return Appointment.objects.create(relationship=self.rel, type=type_, status="confirmed", duration_minutes=60,
                                          scheduled_at=when)

    def test_in_person_opens_at_midnight_ph(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        opens, _ = join_window(self._at("in_person", 15))
        self.assertEqual(opens, datetime(2026, 12, 3, 0, 0, tzinfo=ZoneInfo("Asia/Manila")))

    def test_video_still_opens_fifteen_minutes_before(self):
        a = self._at("video", 15)
        opens, _ = join_window(a)
        self.assertEqual(opens, a.scheduled_at - timedelta(minutes=15))

    def test_payload_shows_the_same_time(self):
        a = self._at("in_person", 15)
        Appointment.objects.filter(pk=a.pk).update(status="pending")
        data = self.client_api.get("/api/client/appointments/").json()
        rows = data["results"] if isinstance(data, dict) else data
        row = next(r for r in rows if r["id"] == a.id)
        self.assertEqual(row["join_opens_at"][:19], "2026-12-03T00:00:00", row["join_opens_at"])  # midnight PH


@override_settings(DEMO_MODE=True)
class DemoRescheduleLimitsTests(_DemoSetup, TestCase):
    """Demo mode: rescheduling until 30 minutes before, to a time at least 1 hour ahead."""

    def setUp(self):
        from clinical.models import PreConsultationScreening

        super().setUp()
        PreConsultationScreening.objects.create(client=self.client_user, height_cm=160, weight_kg=60, activity_level="sedentary")

    def _pending(self, minutes):
        return Appointment.objects.create(relationship=self.rel, type="video", status="pending", duration_minutes=60,
                                          scheduled_at=timezone.now() + timedelta(minutes=minutes))

    def _later(self, minutes):
        return (timezone.now() + timedelta(minutes=minutes)).replace(second=0, microsecond=0)

    def test_client_changes_a_request_45_minutes_before(self):
        a = self._pending(45)
        resp = self.client_api.post(f"/api/client/appointments/{a.id}/reschedule/",
                                    {"action": "change", "scheduled_at": self._later(90).isoformat()}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)

    def test_rnd_suggests_45_minutes_before_and_client_accepts(self):
        a = self._pending(45)
        resp = self.rnd_api.post(f"/api/rnd/appointments/{a.id}/reschedule/",
                                 {"action": "offer", "scheduled_at": self._later(90).isoformat()}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(self.client_api.post(f"/api/client/appointments/{a.id}/reschedule/", {"action": "accept"},
                                              format="json").status_code, 200)
        a.refresh_from_db()
        self.assertEqual(a.status, "confirmed")

    def test_still_closed_in_the_last_30_minutes(self):
        a = self._pending(20)
        resp = self.client_api.post(f"/api/client/appointments/{a.id}/reschedule/",
                                    {"action": "change", "scheduled_at": self._later(90).isoformat()}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("30 minutes", str(resp.data))


class DemoCompleteAfterBothJoinTests(_DemoSetup, TestCase):
    """Demo mode: a video consultation can be marked complete once both joined,
    even before its start (2026-11-28); off, the 5 minutes together still apply."""

    def _joined(self, a):
        from .attendance import record_presence

        record_presence(a.id, "rnd", True, ["rnd"])
        record_presence(a.id, "client", True, ["rnd", "client"])

    @override_settings(DEMO_MODE=True)
    def test_demo_completes_once_both_joined_before_the_start(self):
        a = self.appt(600)
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/complete/").status_code, 403)
        self._joined(a)
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/complete/").status_code, 200)
        a.refresh_from_db()
        self.assertEqual(a.status, "completed")

    def test_off_still_needs_five_minutes_together(self):
        a = self.appt(-10)
        self._joined(a)
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/complete/").status_code, 403)
