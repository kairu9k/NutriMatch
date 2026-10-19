"""The client asks to end care; the RND has 3 days, then it ends on its own.
Deactivating an RND ends their patients' care (2026-10-19)."""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from billing.models import Invoice
from communication.models import NotificationLog
from core.test_utils import approve_rnd, booking_slot, onboard_client

from .discharge_requests import DISCHARGE_REQUEST_DAYS
from .models import Appointment, RndClientRelationship
from .services import current_rnd_relationship


class DischargeRequestTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@dr.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.other = approve_rnd(User.objects.create_user(email="o@dr.ph", password="x", role="rnd", first_name="Jose", last_name="Reyes"))
        self.c = onboard_client(User.objects.create_user(email="c@dr.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active", started_at=timezone.now())
        self.api = APIClient()
        self.api.force_authenticate(self.c)
        self.url = f"/api/client/relationships/{self.rel.id}/discharge-request/"

    def test_request_tells_the_rnd_and_shows_the_deadline(self):
        resp = self.api.post(self.url, {"reason": "different_rnd"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        info = resp.data["discharge_request"]
        self.assertEqual(info["reason_label"], "I want a different RND")
        self.assertAlmostEqual((info["ends_at"] - info["requested_at"]).days, DISCHARGE_REQUEST_DAYS)
        self.assertTrue(NotificationLog.objects.filter(recipient=self.rnd, subject="Discharge requested").exists())
        # visible on the client's care list and the RND's patient summary
        self.assertIsNotNone(self.api.get("/api/client/relationships/").data[0]["discharge_request"])
        self.api.force_authenticate(self.rnd)
        self.assertIsNotNone(self.api.get(f"/api/rnd/relationships/{self.rel.id}/summary/").data["discharge_request"])
        # still blocks another RND while waiting
        self.assertEqual(current_rnd_relationship(self.c, exclude_rnd_id=self.other.id), self.rel)

    def test_rules(self):
        self.assertEqual(self.api.post(self.url, {"reason": "other"}, format="json").status_code, 400)  # needs a note
        self.assertEqual(self.api.post(self.url, {"reason": "bored"}, format="json").status_code, 400)
        Appointment.objects.create(relationship=self.rel, type="video", status="confirmed", scheduled_at=timezone.now() + timedelta(days=1))
        resp = self.api.post(self.url, {"reason": "moved"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Cancel your upcoming consultation", resp.data["detail"])
        other_client = onboard_client(User.objects.create_user(email="x@dr.ph", password="x", role="client"))
        self.api.force_authenticate(other_client)
        self.assertEqual(self.api.post(self.url, {"reason": "moved"}, format="json").status_code, 404)

    def test_withdraw(self):
        self.api.post(self.url, {"reason": "cost"}, format="json")
        self.assertEqual(self.api.delete(self.url).status_code, 200)
        self.rel.refresh_from_db()
        self.assertIsNone(self.rel.discharge_requested_at)
        self.assertTrue(NotificationLog.objects.filter(recipient=self.rnd, subject="Discharge request withdrawn").exists())

    def test_ends_automatically_after_three_days(self):
        self.api.post(self.url, {"reason": "goal_reached"}, format="json")
        RndClientRelationship.objects.filter(pk=self.rel.pk).update(
            discharge_requested_at=timezone.now() - timedelta(days=DISCHARGE_REQUEST_DAYS, minutes=1))
        # any care check runs it — here: is the client free to book Jose?
        self.assertIsNone(current_rnd_relationship(self.c, exclude_rnd_id=self.other.id))
        self.rel.refresh_from_db()
        self.assertEqual((self.rel.status, self.rel.ended_by), ("discharged", "auto"))
        self.assertIn("Ended automatically", self.rel.discharge_reason)
        self.assertTrue(NotificationLog.objects.filter(recipient=self.c, subject="Your care plan has ended").exists())
        self.assertTrue(NotificationLog.objects.filter(recipient=self.rnd, subject="Patient's care ended").exists())
        resp = self.api.post("/api/client/appointments/", {"rnd_id": self.other.id, "type": "video", "duration_minutes": 60,
                                                            "scheduled_at": booking_slot(2).isoformat()}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_not_before_three_days(self):
        self.api.post(self.url, {"reason": "goal_reached"}, format="json")
        RndClientRelationship.objects.filter(pk=self.rel.pk).update(
            discharge_requested_at=timezone.now() - timedelta(days=DISCHARGE_REQUEST_DAYS - 1))
        self.api.get("/api/client/relationships/")
        self.rel.refresh_from_db()
        self.assertEqual(self.rel.status, "active")

    def test_rnd_discharge_closes_the_request(self):
        self.api.post(self.url, {"reason": "different_rnd"}, format="json")
        self.api.force_authenticate(self.rnd)
        resp = self.api.post(f"/api/rnd/relationships/{self.rel.id}/discharge/", {"reason": "Care completed, all the best!"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.rel.refresh_from_db()
        self.assertEqual((self.rel.status, self.rel.ended_by, self.rel.discharge_requested_at), ("discharged", "rnd", None))

    def test_booking_the_same_rnd_again_withdraws_it(self):
        self.api.post(self.url, {"reason": "schedule"}, format="json")
        resp = self.api.post("/api/client/appointments/", {"rnd_id": self.rnd.id, "type": "video", "duration_minutes": 60,
                                                            "scheduled_at": booking_slot(2).isoformat()}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        self.rel.refresh_from_db()
        self.assertIsNone(self.rel.discharge_requested_at)


class DeactivatedRndTests(TestCase):
    def test_deactivating_an_rnd_ends_their_patients_care(self):
        rnd = approve_rnd(User.objects.create_user(email="r2@dr.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        c = onboard_client(User.objects.create_user(email="c2@dr.ph", password="x", role="client", first_name="Ana", last_name="C"))
        admin = User.objects.create_user(email="a2@dr.ph", password="x", role="admin")
        rel = RndClientRelationship.objects.create(rnd=rnd, client=c, status="active", started_at=timezone.now())
        appt = Appointment.objects.create(relationship=rel, type="video", status="confirmed", scheduled_at=timezone.now() + timedelta(days=2))
        inv = Invoice.objects.create(relationship=rel, appointment=appt, amount=Decimal("800"), status="paid", paid_at=timezone.now())
        api = APIClient()
        api.force_authenticate(admin)
        resp = api.post(f"/api/admin/users/{rnd.id}/deactivate/", {"reason": "PRC license expired."}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        rel.refresh_from_db()
        appt.refresh_from_db()
        inv.refresh_from_db()
        self.assertEqual((rel.status, rel.ended_by), ("discharged", "admin"))
        self.assertEqual(appt.status, "cancelled")
        self.assertEqual(inv.status, "refund_pending")  # paid -> refunded
        self.assertIsNone(current_rnd_relationship(c))
        self.assertEqual((resp.data["consultations_cancelled"], resp.data["care_ended"]), (1, 1))
        from communication.models import NotificationLog
        self.assertTrue(NotificationLog.objects.filter(recipient=c, notifiable_type="appointment", notifiable_id=appt.id).exists())
