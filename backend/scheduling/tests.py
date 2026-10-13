from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from clinical.models import PreConsultationScreening
from profiles.models import RndProfile

from .models import Appointment, RndClientRelationship
from core.test_utils import approve_rnd, booking_slot, onboard_client


def _make_rnd(email="rnd@t.ph", fee="500.00", availability=True, **profile_fields):
    user = User.objects.create_user(email=email, password="x", role="rnd", first_name="R", last_name="D")
    profile_fields.setdefault("is_verified", True)
    RndProfile.objects.create(
        user=user, prc_license_number=f"PRC-{email}", consultation_fee=Decimal(fee), **profile_fields
    )
    if profile_fields["is_verified"]:
        approve_rnd(user, availability=availability)  # approved + bookable
    return user


def _make_client(email="client@t.ph"):
    return onboard_client(User.objects.create_user(email=email, password="x", role="client", first_name="C", last_name="L"))


def _booking(rnd, type_="chat"):
    return {
        "rnd_id": rnd.id,
        "scheduled_at": booking_slot(1).isoformat(),
        "type": type_, "duration_minutes": 30,
    }


class AppointmentBookingTests(TestCase):
    """Clients book directly — no separate request/accept step."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.client_api.force_authenticate(self.client_user)

    def test_first_booking_creates_pending_relationship(self):
        resp = self.client_api.post("/api/client/appointments/", _booking(self.rnd))

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["status"], "pending")
        rel = RndClientRelationship.objects.get(rnd=self.rnd, client=self.client_user)
        self.assertEqual(rel.status, "pending")

    def test_repeat_booking_reuses_relationship(self):
        self.client_api.post("/api/client/appointments/", _booking(self.rnd))
        later = {**_booking(self.rnd), "scheduled_at": booking_slot(2).isoformat()}
        resp = self.client_api.post("/api/client/appointments/", later)

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(RndClientRelationship.objects.filter(rnd=self.rnd, client=self.client_user).count(), 1)
        self.assertEqual(Appointment.objects.count(), 2)

    def test_booking_succeeds_with_active_relationship(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")

        resp = self.client_api.post("/api/client/appointments/", _booking(self.rnd))

        self.assertEqual(resp.status_code, 201, resp.data)
        rel = RndClientRelationship.objects.get(rnd=self.rnd, client=self.client_user)
        self.assertEqual(rel.status, "active")

    def test_booking_reopens_discharged_relationship(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="discharged")

        resp = self.client_api.post("/api/client/appointments/", _booking(self.rnd))

        self.assertEqual(resp.status_code, 201, resp.data)
        rel = RndClientRelationship.objects.get(rnd=self.rnd, client=self.client_user)
        self.assertEqual(rel.status, "pending")

    def test_cannot_book_unverified_rnd(self):
        unverified = _make_rnd(email="unverified@t.ph", is_verified=False)

        resp = self.client_api.post("/api/client/appointments/", _booking(unverified))

        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Appointment.objects.exists())
        self.assertFalse(RndClientRelationship.objects.exists())

    def test_cannot_book_mode_rnd_does_not_offer(self):
        video_only = _make_rnd(email="video-only@t.ph", consultation_modes=["video"])

        resp = self.client_api.post("/api/client/appointments/", _booking(video_only, type_="in_person"))

        self.assertEqual(resp.status_code, 400)
        self.assertIn("type", resp.data)
        self.assertFalse(Appointment.objects.exists())

    def test_new_client_cannot_book_rnd_not_accepting(self):
        closed = _make_rnd(email="closed@t.ph", available_for_new_clients=False)

        resp = self.client_api.post("/api/client/appointments/", _booking(closed))
        self.assertEqual(resp.status_code, 400)

    def test_existing_client_can_still_book_rnd_not_accepting_new(self):
        closed = _make_rnd(email="closed@t.ph", available_for_new_clients=False)
        RndClientRelationship.objects.create(rnd=closed, client=self.client_user, status="active")

        resp = self.client_api.post("/api/client/appointments/", _booking(closed))
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_client_can_cancel_own_appointment(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        appt = Appointment.objects.create(relationship=rel, scheduled_at=timezone.now() + timedelta(days=1), type="chat")
        self.client_api.force_authenticate(self.client_user)

        resp = self.client_api.patch(f"/api/client/appointments/{appt.id}/cancel/", {"reason": "Can't make it"})

        self.assertEqual(resp.status_code, 200)
        appt.refresh_from_db()
        self.assertEqual(appt.status, "cancelled")
        self.assertEqual(appt.cancellation_reason, "Can't make it")


class AppointmentConfirmScreeningGateTests(TestCase):
    """RndAppointmentConfirmView must block confirmation until the client
    has at least one PreConsultationScreening on file — this is the real
    clinical gate added alongside the Appointments.vue rewiring."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.appt = Appointment.objects.create(
            relationship=self.rel, scheduled_at=timezone.now() + timedelta(days=1), type="chat"
        )
        self.client_api.force_authenticate(self.rnd)

    def test_confirm_blocked_without_screening(self):
        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/confirm/")

        self.assertEqual(resp.status_code, 403)
        self.appt.refresh_from_db()
        self.assertEqual(self.appt.status, "pending")

    def test_confirm_succeeds_once_client_has_any_screening(self):
        PreConsultationScreening.objects.create(
            client=self.client_user, height_cm=Decimal("170.00"), weight_kg=Decimal("65.00")
        )

        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/confirm/")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.appt.refresh_from_db()
        self.assertEqual(self.appt.status, "confirmed")

    def test_confirming_first_appointment_activates_relationship(self):
        self.rel.status = RndClientRelationship.Status.PENDING
        self.rel.save(update_fields=["status"])
        PreConsultationScreening.objects.create(
            client=self.client_user, height_cm=Decimal("170.00"), weight_kg=Decimal("65.00")
        )

        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/confirm/")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.rel.refresh_from_db()
        self.assertEqual(self.rel.status, "active")
        self.assertIsNotNone(self.rel.started_at)

    def test_blocked_confirm_leaves_relationship_pending(self):
        self.rel.status = RndClientRelationship.Status.PENDING
        self.rel.save(update_fields=["status"])

        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/confirm/")

        self.assertEqual(resp.status_code, 403)
        self.rel.refresh_from_db()
        self.assertEqual(self.rel.status, "pending")

    def test_confirm_wrong_status_transition_rejected(self):
        PreConsultationScreening.objects.create(
            client=self.client_user, height_cm=Decimal("170.00"), weight_kg=Decimal("65.00")
        )
        self.appt.status = Appointment.Status.CANCELLED
        self.appt.save(update_fields=["status"])

        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/confirm/")
        self.assertEqual(resp.status_code, 403)


class AppointmentCompleteInvoiceTests(TestCase):
    """Completing an appointment auto-generates its invoice, idempotently."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd(fee="750.00")
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.appt = Appointment.objects.create(
            relationship=self.rel, scheduled_at=timezone.now() - timedelta(hours=1),
            type="chat", status=Appointment.Status.CONFIRMED,
        )
        self.client_api.force_authenticate(self.rnd)

    def test_complete_creates_invoice_with_rnd_fee(self):
        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/complete/")

        self.assertEqual(resp.status_code, 200, resp.data)
        invoice = Invoice.objects.get(appointment=self.appt)
        self.assertEqual(invoice.amount, Decimal("750.00"))
        self.assertEqual(invoice.relationship, self.rel)

    def test_complete_is_idempotent_on_invoice_creation(self):
        self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/complete/")
        # second complete call is a no-op transition-wise (already completed),
        # so it should be rejected as an invalid transition, not double-invoice
        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/complete/")

        self.assertEqual(resp.status_code, 403)
        self.assertEqual(Invoice.objects.filter(appointment=self.appt).count(), 1)

    def test_complete_uses_admin_configured_commission_rate(self):
        from core.models import SystemSetting

        SystemSetting.objects.create(key="platform_commission_pct", value="15.00")

        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/complete/")

        self.assertEqual(resp.status_code, 200, resp.data)
        invoice = Invoice.objects.get(appointment=self.appt)
        self.assertEqual(invoice.commission_pct, Decimal("15.00"))
        self.assertEqual(invoice.commission_amt, Decimal("112.50"))  # 750 * 15%

    def test_complete_falls_back_to_default_when_no_setting(self):
        resp = self.client_api.patch(f"/api/rnd/appointments/{self.appt.id}/complete/")

        self.assertEqual(resp.status_code, 200, resp.data)
        invoice = Invoice.objects.get(appointment=self.appt)
        self.assertEqual(invoice.commission_pct, Decimal("10.00"))


class ReviewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.appt = Appointment.objects.create(
            relationship=self.rel, scheduled_at=timezone.now() - timedelta(days=1),
            type="chat", status=Appointment.Status.COMPLETED,
        )

    def test_client_can_review_completed_appointment(self):
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.post("/api/client/reviews/", {
            "appointment": self.appt.id, "rating": 5, "comment": "Great session!",
        })
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_cannot_review_same_appointment_twice(self):
        self.client_api.force_authenticate(self.client_user)
        self.client_api.post("/api/client/reviews/", {"appointment": self.appt.id, "rating": 5})
        resp = self.client_api.post("/api/client/reviews/", {"appointment": self.appt.id, "rating": 3})
        self.assertEqual(resp.status_code, 400)

    def test_cannot_review_non_completed_appointment(self):
        pending_appt = Appointment.objects.create(
            relationship=self.rel, scheduled_at=timezone.now() + timedelta(days=1), type="chat"
        )
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.post("/api/client/reviews/", {"appointment": pending_appt.id, "rating": 5})
        self.assertEqual(resp.status_code, 400)

    def test_rnd_sees_own_reviews(self):
        from .models import Review

        Review.objects.create(appointment=self.appt, client=self.client_user, rnd=self.rnd, rating=4, comment="Good")
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.get("/api/rnd/reviews/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["rating"], 4)

    def test_client_sees_own_submitted_reviews(self):
        from .models import Review

        Review.objects.create(appointment=self.appt, client=self.client_user, rnd=self.rnd, rating=5, comment="Great!")
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.get("/api/client/reviews/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["rating"], 5)
        self.assertEqual(resp.data[0]["rnd"]["id"], self.rnd.id)

    def test_client_cannot_see_other_clients_reviews(self):
        from .models import Review

        Review.objects.create(appointment=self.appt, client=self.client_user, rnd=self.rnd, rating=5)
        other_client = _make_client(email="other-client@t.ph")
        self.client_api.force_authenticate(other_client)
        resp = self.client_api.get("/api/client/reviews/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 0)

    def test_rnd_cannot_access_client_review_list(self):
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.get("/api/client/reviews/")
        self.assertEqual(resp.status_code, 403)


class ClientCancelTests(TestCase):
    def setUp(self):
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.api = APIClient()
        self.api.force_authenticate(self.client_user)

    def _appt(self, status, when=None):
        return Appointment.objects.create(
            relationship=self.rel, type="video", status=status,
            scheduled_at=when or timezone.now() + timedelta(days=2),
        )

    def test_cancel_upcoming_notifies_rnd_with_reason(self):
        from communication.models import NotificationLog

        appt = self._appt("confirmed")
        resp = self.api.patch(f"/api/client/appointments/{appt.id}/cancel/", {"reason": "  Out of town  "}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        appt.refresh_from_db()
        self.assertEqual((appt.status, appt.cancellation_reason), ("cancelled", "Out of town"))
        note = NotificationLog.objects.get(recipient=self.rnd, subject="Appointment cancelled")
        self.assertIn("Reason: Out of town", note.content)

    def test_completed_or_cancelled_cannot_be_cancelled(self):
        for st in ("completed", "cancelled"):
            appt = self._appt(st, when=timezone.now() - timedelta(days=1))
            resp = self.api.patch(f"/api/client/appointments/{appt.id}/cancel/", {}, format="json")
            self.assertEqual(resp.status_code, 400, st)
            appt.refresh_from_db()
            self.assertEqual(appt.status, st)

    def test_cannot_cancel_someone_elses_appointment(self):
        other = _make_client("other@t.ph")
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=other, status="active")
        appt = Appointment.objects.create(relationship=rel, type="chat", status="pending", scheduled_at=timezone.now() + timedelta(days=1))
        resp = self.api.patch(f"/api/client/appointments/{appt.id}/cancel/", {}, format="json")
        self.assertEqual(resp.status_code, 404)


class PhTimeFormatTests(TestCase):
    def test_messages_show_philippine_time(self):
        from datetime import datetime, timezone as dt_tz

        from .views import format_ph_datetime

        # 01:00 UTC is 9:00 AM in Manila (UTC+8)
        self.assertEqual(format_ph_datetime(datetime(2026, 9, 28, 1, 0, tzinfo=dt_tz.utc)), "September 28, 2026 at 9:00 AM")
        self.assertEqual(format_ph_datetime(datetime(2026, 9, 28, 5, 30, tzinfo=dt_tz.utc)), "September 28, 2026 at 1:30 PM")


class ReviewValidationTests(TestCase):
    def setUp(self):
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.appt = Appointment.objects.create(
            relationship=rel, type="video", status="completed", scheduled_at=timezone.now() - timedelta(days=1),
        )
        self.api = APIClient()
        self.api.force_authenticate(self.client_user)

    def test_rating_outside_1_to_5_is_a_400_not_a_crash(self):
        for rating in (0, 6, -1):
            resp = self.api.post("/api/client/reviews/", {"appointment": self.appt.id, "rating": rating}, format="json")
            self.assertEqual(resp.status_code, 400, rating)
            self.assertIn("rating", resp.data)

    def test_comment_length_limit(self):
        resp = self.api.post("/api/client/reviews/", {"appointment": self.appt.id, "rating": 5, "comment": "x" * 1001}, format="json")
        self.assertEqual(resp.status_code, 400)
        ok = self.api.post("/api/client/reviews/", {"appointment": self.appt.id, "rating": 5, "comment": "Great"}, format="json")
        self.assertEqual(ok.status_code, 201, ok.data)


class BookingRuleTests(TestCase):
    """The booking modal only shows open slots; the API enforces the same rules."""

    def setUp(self):
        from profiles.models import RndAvailabilitySchedule

        self.rnd = _make_rnd(consultation_modes=["video", "chat"], availability=False)
        self.client_user = _make_client()
        self.api = APIClient()
        self.api.force_authenticate(self.client_user)
        # Next Monday, 9:00-12:00 Philippine time (01:00-04:00 UTC).
        today = timezone.now().date()
        self.monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
        RndAvailabilitySchedule.objects.create(
            rnd=self.rnd, day_of_week=1, start_time="09:00", end_time="12:00", effective_from=today,
        )

    def _at(self, hour_utc, minute=0, day=None):
        from datetime import datetime, timezone as dt_tz

        d = day or self.monday
        return datetime(d.year, d.month, d.day, hour_utc, minute, tzinfo=dt_tz.utc).isoformat()

    def _book(self, when, duration=60, type_="video", api=None):
        return (api or self.api).post("/api/client/appointments/", {
            "rnd_id": self.rnd.id, "scheduled_at": when, "type": type_, "duration_minutes": duration,
        }, format="json")

    def test_valid_booking_notifies_the_rnd(self):
        from communication.models import NotificationLog

        resp = self._book(self._at(1))  # 9:00 AM PHT
        self.assertEqual(resp.status_code, 201, resp.data)
        note = NotificationLog.objects.get(recipient=self.rnd, subject="New booking request")
        self.assertIn("9:00 AM", note.content)

    def test_past_time_rejected(self):
        resp = self._book((timezone.now() - timedelta(hours=2)).isoformat())
        self.assertEqual(resp.status_code, 400)
        self.assertIn("scheduled_at", resp.data)

    def test_outside_available_hours_rejected(self):
        for when in (self._at(0), self._at(3, 30), self._at(6)):  # 8:00 AM, 11:30 AM (runs past 12), 2:00 PM
            resp = self._book(when)
            self.assertEqual(resp.status_code, 400, when)
            self.assertIn("scheduled_at", resp.data)

    def test_same_or_overlapping_slot_cannot_be_double_booked(self):
        self.assertEqual(self._book(self._at(1)).status_code, 201)
        other = _make_client("other@t.ph")
        other_api = APIClient()
        other_api.force_authenticate(other)
        for when in (self._at(1), self._at(1, 30)):
            resp = self._book(when, type_="chat", api=other_api)
            self.assertEqual(resp.status_code, 400, when)
        # back-to-back is fine
        self.assertEqual(self._book(self._at(2), api=other_api).status_code, 201)

    def test_cancelled_slot_can_be_rebooked(self):
        first = self._book(self._at(1))
        Appointment.objects.filter(id=first.data["id"]).update(status="cancelled")
        self.assertEqual(self._book(self._at(1)).status_code, 201)

    def test_duration_limits(self):
        self.assertEqual(self._book(self._at(1), duration=5).status_code, 400)
        self.assertEqual(self._book(self._at(1), duration=600).status_code, 400)

    def test_booked_slots_endpoint_hides_who_booked(self):
        self._book(self._at(1))
        resp = self.api.get(f"/api/client/rnds/{self.rnd.id}/booked-slots/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(set(resp.data[0]), {"start", "end", "kind"})
        self.assertEqual(resp.data[0]["kind"], "booked")


class PayBeforeConsultationTests(TestCase):
    """Invoice on confirm -> client pays before the start -> consultation opens."""

    def setUp(self):
        self.rnd = _make_rnd(fee="800.00", consultation_modes=["video", "chat"])
        self.client_user = _make_client()
        PreConsultationScreening.objects.create(client=self.client_user, height_cm=Decimal("160"), weight_kg=Decimal("60"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.appt = Appointment.objects.create(
            relationship=self.rel, type="video", status="pending", scheduled_at=timezone.now() + timedelta(days=1),
        )
        self.rnd_api = APIClient()
        self.rnd_api.force_authenticate(self.rnd)
        self.client_api = APIClient()
        self.client_api.force_authenticate(self.client_user)

    def _confirm(self, appt=None):
        appt = appt or self.appt
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{appt.id}/confirm/")
        self.assertEqual(resp.status_code, 200, resp.data)
        return Invoice.objects.get(appointment=appt)

    def _pay(self, invoice):
        from billing.services import record_successful_payment

        record_successful_payment(invoice, "ref-test", {}, source="test")
        invoice.refresh_from_db()

    def _client_view(self):
        return next(a for a in self.client_api.get("/api/client/appointments/").data if a["id"] == self.appt.id)

    def test_confirm_issues_unpaid_invoice_and_asks_for_payment(self):
        from communication.models import NotificationLog

        invoice = self._confirm()
        self.assertEqual((invoice.status, invoice.amount), ("unpaid", Decimal("800.00")))
        note = NotificationLog.objects.get(recipient=self.client_user, subject__startswith="Appointment confirmed")
        self.assertIn("Please pay ₱800.00", note.content)

    def test_video_link_hidden_from_client_until_paid(self):
        invoice = self._confirm()
        unpaid = self._client_view()
        self.assertIsNone(unpaid["video_session_url"])
        self.assertIsNone(unpaid["meeting_id"])
        self.assertEqual(unpaid["payment"]["status"], "unpaid")
        detail = self.client_api.get(f"/api/client/appointments/{self.appt.id}/").data
        self.assertIsNone(detail["video_session_url"])
        # the RND always sees the room
        rnd_row = next(a for a in self.rnd_api.get("/api/rnd/appointments/").data if a["id"] == self.appt.id)
        self.assertTrue(rnd_row["video_session_url"])

        self._pay(invoice)
        # paid, but tomorrow: still outside the join window
        early = self._client_view()
        self.assertIsNone(early["video_session_url"])
        self.assertEqual(early["payment"]["status"], "paid")
        # 10 minutes before the start: inside the window (opens 15 min early)
        Appointment.objects.filter(pk=self.appt.pk).update(scheduled_at=timezone.now() + timedelta(minutes=10))
        paid = self._client_view()
        self.assertTrue(paid["video_session_url"].startswith("https://meet.jit.si/"))

    def test_join_window_closes_after_the_session(self):
        invoice = self._confirm()
        self._pay(invoice)
        # 60-min session that started 90 min ago: ended 30 min ago, window closed 15 min ago
        Appointment.objects.filter(pk=self.appt.pk).update(scheduled_at=timezone.now() - timedelta(minutes=90))
        row = self._client_view()
        self.assertIsNone(row["video_session_url"])
        self.assertIn("join_opens_at", row)
        self.assertIn("join_closes_at", row)

    def test_cannot_complete_until_paid(self):
        invoice = self._confirm()
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{self.appt.id}/complete/")
        self.assertEqual(resp.status_code, 403)
        self._pay(invoice)
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{self.appt.id}/complete/")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(Invoice.objects.filter(appointment=self.appt).count(), 1)

    def test_legacy_confirmed_without_invoice_can_still_complete(self):
        Appointment.objects.filter(pk=self.appt.pk).update(status="confirmed")
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{self.appt.id}/complete/")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(Invoice.objects.get(appointment=self.appt).status, "unpaid")

    def test_client_cancel_paid_marks_refund_pending_unpaid_voids(self):
        from communication.models import NotificationLog

        invoice = self._confirm()
        self._pay(invoice)
        self.client_api.patch(f"/api/client/appointments/{self.appt.id}/cancel/", {}, format="json")
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "refund_pending")
        self.assertTrue(NotificationLog.objects.filter(recipient=self.client_user, subject="Refund being processed").exists())

        other = Appointment.objects.create(relationship=self.rel, type="chat", status="pending", scheduled_at=timezone.now() + timedelta(days=3))
        self._confirm(other)
        self.client_api.patch(f"/api/client/appointments/{other.id}/cancel/", {}, format="json")
        self.assertEqual(Invoice.objects.get(appointment=other).status, "cancelled")

    def test_rnd_cancel_paid_marks_refund_pending_and_tells_client(self):
        from communication.models import NotificationLog

        invoice = self._confirm()
        self._pay(invoice)
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{self.appt.id}/cancel/", {"reason": "Sick today, sorry."}, format="json")
        self.assertEqual(resp.status_code, 200)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "refund_pending")
        note = NotificationLog.objects.get(recipient=self.client_user, subject="Appointment cancelled")
        self.assertIn("Reason: Sick", note.content)

    def test_unpaid_at_start_time_is_cancelled_and_slot_released(self):
        invoice = self._confirm()
        Appointment.objects.filter(pk=self.appt.pk).update(scheduled_at=timezone.now() - timedelta(minutes=5))
        row = self._client_view()  # listing runs the expiry
        self.assertEqual(row["status"], "cancelled")
        self.assertIn("Not paid", row["cancellation_reason"])
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "cancelled")
        # and it can no longer be paid
        resp = self.client_api.post(f"/api/client/invoices/{invoice.id}/pay/")
        self.assertEqual(resp.status_code, 404)

    def test_paid_appointment_is_not_expired(self):
        invoice = self._confirm()
        self._pay(invoice)
        Appointment.objects.filter(pk=self.appt.pk).update(scheduled_at=timezone.now() - timedelta(minutes=5))
        self.assertEqual(self._client_view()["status"], "confirmed")

    def test_late_payment_on_cancelled_appointment_flags_refund(self):
        invoice = self._confirm()
        Appointment.objects.filter(pk=self.appt.pk).update(status="cancelled")
        self._pay(invoice)
        self.assertEqual(invoice.status, "refund_pending")

    def test_cannot_confirm_a_request_whose_time_passed(self):
        Appointment.objects.filter(pk=self.appt.pk).update(scheduled_at=timezone.now() - timedelta(hours=1))
        resp = self.rnd_api.patch(f"/api/rnd/appointments/{self.appt.id}/confirm/")
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(Invoice.objects.filter(appointment=self.appt).exists())

    def test_admin_marks_refund_done(self):
        from billing.models import PaymentTransaction

        invoice = self._confirm()
        self._pay(invoice)
        self.client_api.patch(f"/api/client/appointments/{self.appt.id}/cancel/", {}, format="json")
        admin = User.objects.create_user(email="admin@t.ph", password="x", role="admin", first_name="A", last_name="D")
        admin_api = APIClient()
        admin_api.force_authenticate(admin)
        self.assertEqual(self.client_api.post(f"/api/admin/invoices/{invoice.id}/mark-refunded/").status_code, 403)
        resp = admin_api.post(f"/api/admin/invoices/{invoice.id}/mark-refunded/", {"reference": "PM-REF-1"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, "refunded")
        self.assertTrue(PaymentTransaction.objects.filter(invoice=invoice, transaction_type="refund").exists())
        again = admin_api.post(f"/api/admin/invoices/{invoice.id}/mark-refunded/")
        self.assertEqual(again.status_code, 400)
