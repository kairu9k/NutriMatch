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


def _make_rnd(email="rnd@t.ph", fee="500.00"):
    user = User.objects.create_user(email=email, password="x", role="rnd", first_name="R", last_name="D")
    RndProfile.objects.create(user=user, prc_license_number=f"PRC-{email}", consultation_fee=Decimal(fee))
    return user


def _make_client(email="client@t.ph"):
    return User.objects.create_user(email=email, password="x", role="client", first_name="C", last_name="L")


class RelationshipLifecycleTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()

    def test_client_can_request_relationship(self):
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.post(f"/api/client/rnds/{self.rnd.id}/request/")

        self.assertEqual(resp.status_code, 201, resp.data)
        rel = RndClientRelationship.objects.get(rnd=self.rnd, client=self.client_user)
        self.assertEqual(rel.status, "pending")

    def test_requesting_twice_is_idempotent(self):
        self.client_api.force_authenticate(self.client_user)
        self.client_api.post(f"/api/client/rnds/{self.rnd.id}/request/")
        resp = self.client_api.post(f"/api/client/rnds/{self.rnd.id}/request/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(RndClientRelationship.objects.filter(rnd=self.rnd, client=self.client_user).count(), 1)

    def test_rnd_can_accept_pending_request(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="pending")
        self.client_api.force_authenticate(self.rnd)

        resp = self.client_api.patch(f"/api/rnd/relationships/{rel.id}/accept/")

        self.assertEqual(resp.status_code, 200)
        rel.refresh_from_db()
        self.assertEqual(rel.status, "active")
        self.assertIsNotNone(rel.started_at)

    def test_rnd_can_decline_pending_request(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="pending")
        self.client_api.force_authenticate(self.rnd)

        resp = self.client_api.patch(f"/api/rnd/relationships/{rel.id}/decline/")

        self.assertEqual(resp.status_code, 200)
        rel.refresh_from_db()
        self.assertEqual(rel.status, "discharged")

    def test_other_rnd_cannot_accept_someone_elses_request(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="pending")
        other_rnd = _make_rnd(email="other-rnd@t.ph")
        self.client_api.force_authenticate(other_rnd)

        resp = self.client_api.patch(f"/api/rnd/relationships/{rel.id}/accept/")
        self.assertEqual(resp.status_code, 404)


class AppointmentBookingTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()

    def test_booking_requires_active_relationship(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="pending")
        self.client_api.force_authenticate(self.client_user)

        resp = self.client_api.post("/api/client/appointments/", {
            "rnd_id": self.rnd.id,
            "scheduled_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "type": "video", "duration_minutes": 30,
        })
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(Appointment.objects.exists())

    def test_booking_succeeds_with_active_relationship(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.client_api.force_authenticate(self.client_user)

        resp = self.client_api.post("/api/client/appointments/", {
            "rnd_id": self.rnd.id,
            "scheduled_at": (timezone.now() + timedelta(days=1)).isoformat(),
            "type": "chat", "duration_minutes": 30,
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["status"], "pending")
        self.assertTrue(Appointment.objects.filter(relationship__rnd=self.rnd, relationship__client=self.client_user).exists())

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
