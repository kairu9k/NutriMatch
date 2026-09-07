from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from scheduling.models import RndClientRelationship

from .models import RndAvailabilitySchedule, RndProfile


def _make_rnd(email="rnd@t.ph", fee="500.00"):
    user = User.objects.create_user(email=email, password="x", role="rnd", first_name="R", last_name="D")
    RndProfile.objects.create(
        user=user, prc_license_number=f"PRC-{email}", consultation_fee=Decimal(fee),
        is_verified=True, available_for_new_clients=True,
    )
    return user


def _make_client(email="client@t.ph"):
    return User.objects.create_user(email=email, password="x", role="client", first_name="C", last_name="L")


class RndSearchRelationshipStatusTests(TestCase):
    """GET /client/rnds/ must reflect real relationship state — Find an RND
    previously never checked this at all, always showing "Request" even
    for RNDs the client already had a pending/active relationship with."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.client_api.force_authenticate(self.client_user)

    def test_no_relationship_returns_null_status(self):
        resp = self.client_api.get("/api/client/rnds/")

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data[0]["relationship_status"])

    def test_pending_relationship_status_is_real(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="pending")
        resp = self.client_api.get("/api/client/rnds/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]["relationship_status"], "pending")

    def test_active_relationship_status_is_real(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        resp = self.client_api.get("/api/client/rnds/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]["relationship_status"], "active")

    def test_status_scoped_to_requesting_client_only(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        other_client = _make_client(email="other@t.ph")
        self.client_api.force_authenticate(other_client)

        resp = self.client_api.get("/api/client/rnds/")

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data[0]["relationship_status"])

    def test_rnd_viewing_public_profile_gets_null_status_not_error(self):
        other_rnd = _make_rnd(email="other-rnd@t.ph")
        self.client_api.force_authenticate(other_rnd)

        resp = self.client_api.get(f"/api/client/rnds/{self.rnd.id}/")

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data["relationship_status"])


class RndAvailabilityCustomTimesTests(TestCase):
    """The Availability page previously hardcoded every new slot to
    9 AM-5 PM regardless of what the RND actually wanted — the model and
    endpoints already supported arbitrary times, only the frontend didn't
    expose it. These tests cover the validation added alongside the fix."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_api.force_authenticate(self.rnd)

    def test_create_slot_with_custom_times(self):
        resp = self.client_api.post("/api/rnd/availability/", {
            "day_of_week": 3, "start_time": "13:00:00", "end_time": "16:30:00",
            "is_available": True, "effective_from": timezone.now().date().isoformat(),
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["start_time"], "13:00:00")
        self.assertEqual(resp.data["end_time"], "16:30:00")

    def test_create_rejects_end_before_start(self):
        resp = self.client_api.post("/api/rnd/availability/", {
            "day_of_week": 3, "start_time": "16:00:00", "end_time": "09:00:00",
            "is_available": True, "effective_from": timezone.now().date().isoformat(),
        })
        self.assertEqual(resp.status_code, 400)

    def test_create_rejects_equal_start_and_end(self):
        resp = self.client_api.post("/api/rnd/availability/", {
            "day_of_week": 3, "start_time": "09:00:00", "end_time": "09:00:00",
            "is_available": True, "effective_from": timezone.now().date().isoformat(),
        })
        self.assertEqual(resp.status_code, 400)

    def test_patch_can_edit_existing_slot_times(self):
        slot = RndAvailabilitySchedule.objects.create(
            rnd=self.rnd, day_of_week=1, start_time="09:00:00", end_time="17:00:00",
            effective_from=timezone.now().date(),
        )
        resp = self.client_api.patch(f"/api/rnd/availability/{slot.id}/", {
            "start_time": "10:00:00", "end_time": "14:00:00",
        })

        self.assertEqual(resp.status_code, 200, resp.data)
        slot.refresh_from_db()
        self.assertEqual(str(slot.start_time), "10:00:00")
        self.assertEqual(str(slot.end_time), "14:00:00")

    def test_patch_rejects_end_before_start_using_existing_value(self):
        slot = RndAvailabilitySchedule.objects.create(
            rnd=self.rnd, day_of_week=1, start_time="09:00:00", end_time="17:00:00",
            effective_from=timezone.now().date(),
        )
        # only patching start_time past the existing end_time (17:00) should
        # still be caught, not bypassed just because end_time wasn't in this request
        resp = self.client_api.patch(f"/api/rnd/availability/{slot.id}/", {"start_time": "18:00:00"})
        self.assertEqual(resp.status_code, 400)
