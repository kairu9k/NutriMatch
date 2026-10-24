"""Payment receipt emails (client + NutriMatch inbox)."""

from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from core.models import SystemSetting
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, RndClientRelationship

from .models import Invoice
from .services import record_successful_payment

PAYLOAD = {"data": {"attributes": {"data": {"id": "pay_abc123", "attributes": {
    "amount": 80000, "fee": 1840, "status": "paid", "currency": "PHP", "paid_at": 1791600000,
    "source": {"type": "card", "brand": "visa", "last4": "4242"}, "billing": {"name": "Ana Cruz", "email": "ana@r.ph"}}}}}}


class ReceiptEmailTests(TestCase):
    def setUp(self):
        mail.outbox = []
        SystemSetting.objects.update_or_create(key="support_email", defaults={"value": "team@nutrimatch.test"})
        self.rnd = approve_rnd(User.objects.create_user(email="rnd@r.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.client_user = onboard_client(User.objects.create_user(email="ana@r.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        appt = Appointment.objects.create(relationship=rel, type="video", status="confirmed", scheduled_at=timezone.now() + timedelta(days=2))
        self.invoice = Invoice.objects.create(relationship=rel, appointment=appt, amount=Decimal("800"))

    def _pay(self):
        with self.captureOnCommitCallbacks(execute=True):
            return record_successful_payment(self.invoice, "link_1", PAYLOAD, source="webhook", payment_method="card")

    def test_client_and_inbox_get_receipts(self):
        self.assertTrue(self._pay())
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ["ana@r.ph", "team@nutrimatch.test"])
        client_mail = next(m for m in mail.outbox if m.to == ["ana@r.ph"])
        self.assertIn(f"INV-{self.invoice.id:04d}", client_mail.subject)
        self.assertIn("₱800.00", client_mail.subject)
        html = client_mail.alternatives[0][0]
        for text in ("Payment received", "RND Maria Santos", "Visa •••• 4242", "pay_abc123", "Total paid"):
            self.assertIn(text, html)
        admin_mail = next(m for m in mail.outbox if m.to == ["team@nutrimatch.test"])
        self.assertIn("Ana Cruz", admin_mail.subject)

    def test_paying_twice_sends_nothing_more(self):
        self._pay()
        mail.outbox = []
        with self.captureOnCommitCallbacks(execute=True):
            self.assertFalse(record_successful_payment(self.invoice, "link_1", PAYLOAD, source="sync"))
        self.assertEqual(mail.outbox, [])

    def test_email_failure_never_breaks_the_payment(self):
        with mock.patch("accounts.emails.EmailMultiAlternatives.send", side_effect=OSError("SMTP down")):
            self.assertTrue(self._pay())
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, "paid")

    def test_late_payment_on_cancelled_appointment_says_refund(self):
        Appointment.objects.filter(pk=self.invoice.appointment_id).update(status="cancelled")
        self._pay()
        admin_mail = next(m for m in mail.outbox if m.to == ["team@nutrimatch.test"])
        self.assertIn("refund needed", admin_mail.alternatives[0][0])


class RndPaidNotificationTests(ReceiptEmailTests):
    """The RND is told when a consultation is paid (2026-10-25)."""

    def test_rnd_notified_once(self):
        from communication.models import NotificationLog

        self._pay()
        notes = NotificationLog.objects.filter(recipient=self.rnd)
        self.assertEqual(notes.count(), 1)
        n = notes.get()
        self.assertEqual((n.subject, n.notifiable_type, n.notifiable_id), ("Consultation paid", "appointment", self.invoice.appointment_id))
        self.assertIn("Ana Cruz paid ₱800.00", n.content)
        with self.captureOnCommitCallbacks(execute=True):
            record_successful_payment(self.invoice, "link_1", PAYLOAD, source="sync")
        self.assertEqual(notes.count(), 1)

    def test_late_payment_on_cancelled_consultation_not_announced(self):
        from communication.models import NotificationLog

        Appointment.objects.filter(pk=self.invoice.appointment_id).update(status="cancelled")
        self._pay()
        self.assertFalse(NotificationLog.objects.filter(recipient=self.rnd).exists())
