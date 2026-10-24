"""Admin > Appointments: list/filter, summary, cancel on a user's behalf."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from communication.models import NotificationLog
from core.models import AuditLog
from core.test_utils import approve_rnd, onboard_client

from .models import Appointment, RndClientRelationship


class AdminAppointmentTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@x.ph", password="x", role="admin", first_name="Ad", last_name="Min")
        self.api = APIClient()
        self.api.force_authenticate(self.admin)
        self.rnd = approve_rnd(User.objects.create_user(email="rnd@x.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.client_user = onboard_client(User.objects.create_user(email="ana@x.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        now = timezone.now()
        self.upcoming = self._appt("confirmed", now + timedelta(days=2), invoice="paid")
        self.request = self._appt("pending", now + timedelta(days=3))
        Appointment.objects.filter(pk=self.request.pk).update(created_at=now - timedelta(hours=30))
        self.done = self._appt("completed", now - timedelta(days=2), invoice="paid")
        self.gone = self._appt("cancelled", now - timedelta(days=1))

    def _appt(self, status, when, invoice=None):
        appt = Appointment.objects.create(relationship=self.rel, type="video", status=status, scheduled_at=when, duration_minutes=60)
        if invoice:
            Invoice.objects.create(relationship=self.rel, appointment=appt, amount=Decimal("800"), status=invoice,
                                   paid_at=timezone.now() if invoice == "paid" else None)
        return appt

    def _ids(self, url):
        return [r["id"] for r in self.api.get(url).data["results"]]

    def test_views(self):
        self.assertEqual(self._ids("/api/admin/appointments/"), [self.upcoming.id, self.request.id])
        self.assertEqual(self._ids("/api/admin/appointments/?view=requests"), [self.request.id])
        self.assertEqual(self._ids("/api/admin/appointments/?view=past"), [self.done.id])
        self.assertEqual(self._ids("/api/admin/appointments/?view=cancelled"), [self.gone.id])
        self.assertEqual(len(self._ids("/api/admin/appointments/?view=all")), 4)

    def test_row_shape_has_people_and_payment_but_no_room_link(self):
        row = self.api.get("/api/admin/appointments/").data["results"][0]
        self.assertEqual(row["client"]["name"], "Ana Cruz")
        self.assertEqual(row["rnd"]["name"], "Maria Santos")
        self.assertEqual(row["payment"]["status"], "paid")
        self.assertNotIn("video_session_url", row)

    def test_filters(self):
        self.assertEqual(len(self._ids("/api/admin/appointments/?view=all&search=santos")), 4)
        self.assertEqual(self._ids("/api/admin/appointments/?view=all&search=nobody"), [])
        self.assertEqual(self._ids(f"/api/admin/appointments/?view=all&search={self.done.id}"), [self.done.id])
        self.assertEqual(self._ids("/api/admin/appointments/?view=all&payment=paid"), [self.upcoming.id, self.done.id])

    def test_expired_request_is_cancelled(self):
        old = self._appt("pending", timezone.now() - timedelta(days=1))
        self.assertNotIn(old.id, self._ids("/api/admin/appointments/?view=requests"))
        self.assertIn(old.id, self._ids("/api/admin/appointments/?view=cancelled"))
        # an unanswered request whose time passed expires (2026-10-25): cancelled, nothing left pending
        old.refresh_from_db()
        self.assertEqual((old.status, old.cancellation_reason), ("cancelled", "The RND didn't respond before the requested time."))
        data = self.api.get("/api/admin/appointments/summary/").data
        self.assertEqual((data["requests"], data["expired_requests"]), (1, 0))

    def test_summary(self):
        data = self.api.get("/api/admin/appointments/summary/").data
        self.assertEqual((data["upcoming"], data["requests"], data["stale_requests"]), (2, 1, 1))

    def test_cancel_paid_appointment_goes_to_refund_and_notifies_both(self):
        url = f"/api/admin/appointments/{self.upcoming.id}/cancel/"
        self.assertEqual(self.api.post(url, {"reason": "short"}, format="json").status_code, 400)
        resp = self.api.post(url, {"reason": "The RND has a family emergency this week."}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "cancelled")
        self.assertEqual(resp.data["payment"]["status"], "refund_pending")
        self.assertIn("Cancelled by NutriMatch", resp.data["cancellation_reason"])
        recipients = set(NotificationLog.objects.filter(notifiable_type="appointment", notifiable_id=self.upcoming.id).values_list("recipient_id", flat=True))
        self.assertEqual(recipients, {self.client_user.id, self.rnd.id})
        log = AuditLog.objects.get(action="appointment.cancelled")
        self.assertEqual((log.user, log.new_values["invoice_status"]), (self.admin, "refund_pending"))

    def test_cannot_cancel_finished_or_cancelled(self):
        for appt in (self.done, self.gone):
            resp = self.api.post(f"/api/admin/appointments/{appt.id}/cancel/", {"reason": "Testing a finished one."}, format="json")
            self.assertEqual(resp.status_code, 400)

    def test_admin_only(self):
        other = APIClient()
        other.force_authenticate(self.client_user)
        self.assertEqual(other.get("/api/admin/appointments/").status_code, 403)
        self.assertEqual(other.post(f"/api/admin/appointments/{self.upcoming.id}/cancel/", {"reason": "x" * 20}).status_code, 403)
