"""Demo mode for the defense (scheduling/demo.py, 2026-11-27): instant Pay, no booking lead,
the room opens once confirmed and paid; off by default and every normal rule back when off."""

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from billing.models import Invoice
from billing.services import create_appointment_invoice, expire_unpaid_appointments
from core.models import AuditLog
from profiles.models import RndAvailabilitySchedule

from .demo import DEMO_PAYMENT_NOTE
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

    def test_pay_is_instant_and_marked_as_demo(self):
        a, inv = self.unpaid(10)
        with patch("billing.views.PayMongoService.create_payment_link") as link:
            resp = self.client_api.post(f"/api/client/invoices/{inv.id}/pay/")
        self.assertEqual(resp.status_code, 200, resp.data)
        link.assert_not_called()
        self.assertEqual(resp.data["status"], "paid")
        self.assertIsNone(resp.data["payment_url"])
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.Status.PAID)
        self.assertEqual(inv.payment_gateway, Invoice.PaymentGateway.MANUAL)
        self.assertIn(DEMO_PAYMENT_NOTE, inv.notes)
        self.assertTrue(AuditLog.objects.filter(action="invoice.paid", record_id=inv.id).exists())

    def test_unpaid_isnt_cancelled_before_the_start(self):
        a, _ = self.unpaid(10)
        expire_unpaid_appointments()
        a.refresh_from_db()
        self.assertEqual(a.status, "confirmed")

    def test_room_opens_well_before_the_start(self):
        a, _ = self.unpaid(120)
        opens, _ = join_window(a)
        self.assertLessEqual(opens, timezone.now())


class ClearDemoPaymentsTests(_DemoSetup, TestCase):
    def test_voids_only_demo_payments(self):
        with override_settings(DEMO_MODE=True):
            a, demo_inv = self.unpaid(10)
            self.client_api.post(f"/api/client/invoices/{demo_inv.id}/pay/")
        b = self.appt(300)  # a normal paid one
        normal = Invoice.objects.get(appointment=b)

        out = StringIO()
        call_command("clear_demo_payments", "--dry-run", stdout=out)
        demo_inv.refresh_from_db()
        self.assertEqual(demo_inv.status, Invoice.Status.PAID)
        self.assertIn(f"INV-{demo_inv.id:04d}", out.getvalue())

        call_command("clear_demo_payments", stdout=StringIO())
        demo_inv.refresh_from_db()
        normal.refresh_from_db()
        self.assertEqual(demo_inv.status, Invoice.Status.CANCELLED)
        self.assertEqual(normal.status, Invoice.Status.PAID)
        self.assertTrue(AuditLog.objects.filter(action="invoice.demo_voided", record_id=demo_inv.id).exists())
