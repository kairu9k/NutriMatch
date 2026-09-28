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


def _make_rnd(email="rnd@t.ph", fee="500.00", **profile_fields):
    user = User.objects.create_user(email=email, password="x", role="rnd", first_name="R", last_name="D")
    profile_fields.setdefault("is_verified", True)
    RndProfile.objects.create(
        user=user, prc_license_number=f"PRC-{email}", consultation_fee=Decimal(fee), **profile_fields
    )
    return user


def _make_client(email="client@t.ph"):
    return User.objects.create_user(email=email, password="x", role="client", first_name="C", last_name="L")


def _booking(rnd, type_="chat"):
    return {
        "rnd_id": rnd.id,
        "scheduled_at": (timezone.now() + timedelta(days=1)).isoformat(),
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
        resp = self.client_api.post("/api/client/appointments/", _booking(self.rnd))

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
