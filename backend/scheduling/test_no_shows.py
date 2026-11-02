"""Time rules, attendance, no-shows, disputes, late RND cancels (2026-11-02)."""

from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from billing.payouts import invoice_state
from billing.services import create_appointment_invoice, expire_unpaid_appointments
from communication.models import NotificationLog, SupportTicket

from .attendance import attendance_payload, record_presence
from .models import Appointment, RndClientRelationship
from .tests import _make_client, _make_rnd


class _ConsultationSetup:
    def setUp(self):
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.admin = User.objects.create_user(email="admin@t.ph", password="x", role="admin", first_name="A", last_name="D")
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active",
                                                        started_at=timezone.now())
        self.rnd_api, self.client_api, self.admin_api = APIClient(), APIClient(), APIClient()
        self.rnd_api.force_authenticate(self.rnd)
        self.client_api.force_authenticate(self.client_user)
        self.admin_api.force_authenticate(self.admin)

    def appt(self, minutes_from_now, status="confirmed", paid=True, type_="video"):
        a = Appointment.objects.create(relationship=self.rel, type=type_, status=status, duration_minutes=60,
                                       scheduled_at=timezone.now() + timedelta(minutes=minutes_from_now))
        if status == "confirmed":
            inv, _ = create_appointment_invoice(a)
            if paid:
                inv.status, inv.paid_at = Invoice.Status.PAID, timezone.now()
                inv.save()
        return a



class NoShowRulesTests(_ConsultationSetup, TestCase):
    # ---- time rules
    def test_confirm_closes_30_minutes_before(self):
        from clinical.models import PreConsultationScreening

        PreConsultationScreening.objects.create(client=self.client_user, height_cm=160, weight_kg=60, activity_level="sedentary")
        late = self.appt(25, status="pending")
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{late.id}/confirm/")
        self.assertEqual(resp.status_code, 403)
        self.assertIn("30 minutes", str(resp.data))
        ok = self.appt(40, status="pending")
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{ok.id}/confirm/").status_code, 200)

    def test_unanswered_request_expires_30_minutes_before(self):
        a = self.appt(25, status="pending")
        expire_unpaid_appointments(relationship=self.rel)
        a.refresh_from_db()
        self.assertEqual((a.status, a.cancelled_by), ("cancelled", "system"))

    def test_unpaid_cancelled_15_minutes_before(self):
        keep = self.appt(20, paid=False)
        gone = self.appt(10, paid=False)
        expire_unpaid_appointments(relationship=self.rel)
        keep.refresh_from_db()
        gone.refresh_from_db()
        self.assertEqual(keep.status, "confirmed")
        self.assertEqual(gone.status, "cancelled")

    def test_paid_cancel_closes_30_minutes_before_unpaid_does_not(self):
        paid = self.appt(25)
        resp = self.client_api.patch(f"/api/client/appointments/{paid.id}/cancel/", {}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("30 minutes", resp.data["detail"])
        unpaid = self.appt(20, paid=False)
        self.assertEqual(self.client_api.patch(f"/api/client/appointments/{unpaid.id}/cancel/", {}, format="json").status_code, 200)
        early = self.appt(40)
        self.assertEqual(self.client_api.patch(f"/api/client/appointments/{early.id}/cancel/", {}, format="json").status_code, 200)

    def test_payload_has_deadlines(self):
        a = self.appt(120)
        data = self.client_api.get(f"/api/client/appointments/{a.id}/").data
        start = a.scheduled_at
        for key, mins in (("confirm_by", 30), ("cancel_by", 30), ("pay_by", 15)):
            self.assertEqual(data[key], (start - timedelta(minutes=mins)).isoformat())
        self.assertEqual(data["attendance"]["state"], "none")

    # ---- attendance
    def test_attendance_records_join_leave_and_time_together(self):
        a = self.appt(-5)
        t0 = timezone.now()
        record_presence(a.id, "rnd", True, ["rnd"], now=t0)
        record_presence(a.id, "client", True, ["rnd", "client"], now=t0 + timedelta(minutes=2))
        record_presence(a.id, "client", False, ["rnd"], now=t0 + timedelta(minutes=32))
        a.refresh_from_db()
        info = attendance_payload(a)
        self.assertEqual(info["state"], "both")
        self.assertEqual(info["together_minutes"], 30)
        self.assertIn("together 30 min", info["line"])

    # ---- client no-show
    def test_no_show_refused_once_client_joined(self):
        a = self.appt(-5)
        record_presence(a.id, "client", True, ["client"])
        resp = self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {}, format="json")
        self.assertEqual(resp.status_code, 400)
        a.refresh_from_db()
        self.assertEqual(a.status, "confirmed")

    def test_no_show_refused_before_the_start(self):
        a = self.appt(10)
        self.assertEqual(self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {}, format="json").status_code, 400)

    def test_no_show_pays_the_rnd_and_dispute_holds_then_refunds(self):
        a = self.appt(-5)
        record_presence(a.id, "rnd", True, ["rnd"])
        resp = self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {"note": "Waited 15 minutes"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        inv = Invoice.objects.get(appointment=a)
        self.assertEqual((a.status, inv.status), ("no_show", "paid"))
        self.assertEqual(invoice_state(inv), "pending")
        self.assertEqual(invoice_state(inv, timezone.now() + timedelta(days=4)), "posted")  # paid out like a completed one
        self.assertTrue(NotificationLog.objects.filter(recipient=self.client_user, subject="Marked as not attending").exists())

        # the client disputes: a support request, the payout waits
        self.assertEqual(self.client_api.post(f"/api/client/appointments/{a.id}/dispute/", {"reason": "short"}, format="json").status_code, 400)
        resp = self.client_api.post(f"/api/client/appointments/{a.id}/dispute/",
                                    {"reason": "I was in the waiting room but the call never loaded."}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        ticket = SupportTicket.objects.get(appointment=a, category="dispute")
        self.assertIn("Attendance:", ticket.messages.first().body)
        inv.refresh_from_db()
        self.assertEqual(invoice_state(inv, timezone.now() + timedelta(days=10)), "pending")
        self.assertEqual(self.client_api.post(f"/api/client/appointments/{a.id}/dispute/",
                                              {"reason": "Again, again, again, again."}, format="json").status_code, 400)
        # the form can't open a dispute
        self.assertEqual(self.client_api.post("/api/support/tickets/", {"category": "dispute", "subject": "Hello there",
                                                                         "message": "A long enough message."}, format="json").status_code, 400)

        # the admin refunds it
        resp = self.admin_api.post(f"/api/admin/appointments/{a.id}/dispute/", {"decision": "refund", "note": "The call log shows a problem."}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        inv.refresh_from_db()
        a.refresh_from_db()
        ticket.refresh_from_db()
        self.assertEqual((inv.status, a.dispute_outcome, ticket.status), ("refund_pending", "refunded", "closed"))
        self.assertTrue(NotificationLog.objects.filter(recipient=self.client_user, subject="Dispute approved").exists())

    def test_rejected_dispute_pays_the_rnd(self):
        a = self.appt(-5)
        self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {}, format="json")
        self.client_api.post(f"/api/client/appointments/{a.id}/dispute/", {"reason": "I really did try to join it."}, format="json")
        resp = self.admin_api.post(f"/api/admin/appointments/{a.id}/dispute/", {"decision": "reject", "note": "You never joined the call."}, format="json")
        self.assertEqual(resp.status_code, 200)
        inv = Invoice.objects.get(appointment=a)
        self.assertEqual(inv.status, "paid")
        self.assertEqual(invoice_state(inv, timezone.now() + timedelta(days=4)), "posted")

    def test_dispute_window_is_three_days(self):
        a = self.appt(-5)
        self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {}, format="json")
        Appointment.objects.filter(pk=a.pk).update(completed_at=timezone.now() - timedelta(days=3, minutes=1))
        resp = self.client_api.post(f"/api/client/appointments/{a.id}/dispute/", {"reason": "I really did try to join it."}, format="json")
        self.assertEqual(resp.status_code, 400)

    # ---- RND didn't come
    def test_client_reports_rnd_absent(self):
        a = self.appt(-16)
        self.assertEqual(self.client_api.post(f"/api/client/appointments/{a.id}/rnd-absent/").status_code, 400)  # never joined
        record_presence(a.id, "client", True, ["client"])
        resp = self.client_api.post(f"/api/client/appointments/{a.id}/rnd-absent/")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        self.assertEqual((a.status, a.cancelled_by, a.cancelled_late), ("cancelled", "rnd_absent", True))
        self.assertEqual(Invoice.objects.get(appointment=a).status, "refund_pending")

    def test_rnd_absent_needs_15_minutes_and_an_absent_rnd(self):
        a = self.appt(-10)
        record_presence(a.id, "client", True, ["client"])
        self.assertEqual(self.client_api.post(f"/api/client/appointments/{a.id}/rnd-absent/").status_code, 400)
        b = self.appt(-20)
        record_presence(b.id, "client", True, ["client"])
        record_presence(b.id, "rnd", True, ["client", "rnd"])
        self.assertEqual(self.client_api.post(f"/api/client/appointments/{b.id}/rnd-absent/").status_code, 400)

    def test_a_brief_rnd_join_does_not_count(self):
        t0 = timezone.now() - timedelta(minutes=20)
        brief = self.appt(-20)
        record_presence(brief.id, "client", True, ["client"], now=t0)
        record_presence(brief.id, "rnd", True, ["client", "rnd"], now=t0 + timedelta(minutes=1))
        record_presence(brief.id, "rnd", False, ["client"], now=t0 + timedelta(minutes=3))  # 2 min, then left
        resp = self.client_api.post(f"/api/client/appointments/{brief.id}/rnd-absent/")
        self.assertEqual(resp.status_code, 200, resp.data)
        brief.refresh_from_db()
        self.assertIn("less than 5 minutes", brief.cancellation_reason)

        stayed = self.appt(-25)
        t1 = timezone.now() - timedelta(minutes=25)
        record_presence(stayed.id, "client", True, ["client"], now=t1)
        record_presence(stayed.id, "rnd", True, ["client", "rnd"], now=t1)
        record_presence(stayed.id, "rnd", False, ["client"], now=t1 + timedelta(minutes=4))
        record_presence(stayed.id, "rnd", True, ["client", "rnd"], now=t1 + timedelta(minutes=6))
        record_presence(stayed.id, "rnd", False, ["client"], now=t1 + timedelta(minutes=8))  # 4 + 2 = 6 min in total
        stayed.refresh_from_db()
        self.assertEqual(attendance_payload(stayed)["rnd_minutes"], 6)
        self.assertEqual(self.client_api.post(f"/api/client/appointments/{stayed.id}/rnd-absent/").status_code, 400)

    # ---- call didn't work
    def test_call_failed_refunds(self):
        a = self.appt(-5)
        resp = self.rnd_api.post(f"/api/rnd/appointments/{a.id}/call-failed/", {"note": "No audio either side"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        self.assertEqual((a.status, a.cancelled_by, a.cancelled_late), ("cancelled", "call_failed", False))
        self.assertEqual(Invoice.objects.get(appointment=a).status, "refund_pending")

    # ---- RND late cancel
    def test_late_rnd_cancel_needs_a_category_and_is_flagged(self):
        from core.admin_dashboard import _attention
        from .no_shows import late_cancel_flags

        a = self.appt(20)
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/cancel/", {}, format="json").status_code, 400)
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/cancel/", {"category": "emergency"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        a.refresh_from_db()
        self.assertEqual((a.cancelled_late, a.cancel_category), (True, "emergency"))
        note = NotificationLog.objects.filter(recipient=self.client_user, subject="Appointment cancelled").latest("id")
        self.assertIn("because of an emergency", note.content)
        self.assertEqual(Invoice.objects.get(appointment=a).status, "refund_pending")
        # "Other" needs a note; an early cancel still needs a reason and isn't late
        b = self.appt(20)
        self.assertEqual(self.rnd_api.patch(f"/api/rnd/appointments/{b.id}/cancel/", {"category": "other"}, format="json").status_code, 400)
        early = self.appt(120)
        self.rnd_api.patch(f"/api/rnd/appointments/{early.id}/cancel/", {"reason": "Clinic is closed that day"}, format="json")
        early.refresh_from_db()
        self.assertFalse(early.cancelled_late)
        self.assertEqual(late_cancel_flags(), [])
        for _ in range(2):
            c = self.appt(20)
            self.rnd_api.patch(f"/api/rnd/appointments/{c.id}/cancel/", {"category": "technical"}, format="json")
        self.assertEqual(late_cancel_flags(), [(self.rnd, 3)])
        self.assertIn("late_cancels", [i["key"] for i in _attention(timezone.now(), {"unpaid_soon": 0, "stale_requests": 0, "stale_request_hours": 24})])


class ConsultationEmailTests(_ConsultationSetup, TestCase):
    """The four consultation events that also go by email (2026-11-02)."""

    def subjects(self):
        from django.core import mail

        return [m.subject for m in mail.outbox]

    def test_no_show_emails_the_client_with_the_dispute_deadline(self):
        from django.core import mail

        a = self.appt(-5)
        with self.captureOnCommitCallbacks(execute=True):
            self.rnd_api.post(f"/api/rnd/appointments/{a.id}/no-show/", {"note": "Waited 15 minutes"}, format="json")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.client_user.email])
        self.assertIn("not attending", mail.outbox[0].subject)
        self.assertIn("Dispute by", mail.outbox[0].body)
        self.assertNotIn("Waited 15 minutes", mail.outbox[0].body)  # the RND's note stays in the app

    def test_confirm_emails_the_pay_by_time(self):
        from django.core import mail

        from clinical.models import PreConsultationScreening

        PreConsultationScreening.objects.create(client=self.client_user, height_cm=160, weight_kg=60, activity_level="sedentary")
        a = self.appt(120, status="pending")
        with self.captureOnCommitCallbacks(execute=True):
            self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/confirm/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Pay by", mail.outbox[0].subject)
        self.assertIn("15 minutes before the start", mail.outbox[0].body)

    def test_rnd_cancel_and_failed_call_email_the_client(self):
        from django.core import mail

        a = self.appt(20)
        with self.captureOnCommitCallbacks(execute=True):
            self.rnd_api.patch(f"/api/rnd/appointments/{a.id}/cancel/", {"category": "emergency", "reason": "private family matter"}, format="json")
        b = self.appt(-5)
        with self.captureOnCommitCallbacks(execute=True):
            self.rnd_api.post(f"/api/rnd/appointments/{b.id}/call-failed/", {}, format="json")
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("because of an emergency", mail.outbox[0].body)
        self.assertNotIn("private family matter", mail.outbox[0].body)
        self.assertIn("full", mail.outbox[0].body)
        self.assertIn("video call didn't work", mail.outbox[1].body)
        # declining a request that was never confirmed doesn't email
        c = self.appt(200, status="pending")
        with self.captureOnCommitCallbacks(execute=True):
            self.rnd_api.patch(f"/api/rnd/appointments/{c.id}/cancel/", {"reason": "Fully booked that day"}, format="json")
        self.assertEqual(len(mail.outbox), 2)

    def test_rnd_absent_emails_the_rnd(self):
        from django.core import mail

        a = self.appt(-16)
        record_presence(a.id, "client", True, ["client"])
        with self.captureOnCommitCallbacks(execute=True):
            self.client_api.post(f"/api/client/appointments/{a.id}/rnd-absent/")
        self.assertEqual([m.to for m in mail.outbox], [[self.rnd.email]])
        self.assertIn("You missed a consultation", mail.outbox[0].subject)
