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
