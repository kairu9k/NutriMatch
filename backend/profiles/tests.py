from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from scheduling.models import RndClientRelationship

from .models import ClientHealthProfile, ClientProfile, RndAvailabilitySchedule, RndProfile
from core.test_utils import approve_rnd


def _make_rnd(email="rnd@t.ph", fee="500.00"):
    user = User.objects.create_user(email=email, password="x", role="rnd", first_name="R", last_name="D")
    RndProfile.objects.create(
        user=user, prc_license_number=f"PRC-{email}", consultation_fee=Decimal(fee),
        is_verified=True, available_for_new_clients=True,
    )
    return approve_rnd(user)


def _make_client(email="client@t.ph"):
    return User.objects.create_user(email=email, password="x", role="client", first_name="C", last_name="L")


class ClientConditionTests(TestCase):
    """The client's primary condition (ClientHealthProfile.medical_conditions[0])
    is editable in Profile Settings and is what the RND's patient list shows."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        ClientProfile.objects.create(user=self.client_user)

    def test_client_can_set_conditions_without_existing_health_profile(self):
        self.client_api.force_authenticate(self.client_user)

        resp = self.client_api.patch("/api/client/profile/", {"medical_conditions": ["  Hypertension ", "hypertension", ""]}, format="json")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["health_profile"]["medical_conditions"], ["Hypertension"])

    def test_clearing_conditions_stores_null(self):
        ClientHealthProfile.objects.create(user=self.client_user, medical_conditions=["Type 2 Diabetes"])
        self.client_api.force_authenticate(self.client_user)

        resp = self.client_api.patch("/api/client/profile/", {"medical_conditions": []}, format="json")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIsNone(ClientHealthProfile.objects.get(user=self.client_user).medical_conditions)

    def test_updating_other_fields_leaves_conditions_alone(self):
        ClientHealthProfile.objects.create(user=self.client_user, medical_conditions=["Type 2 Diabetes"])
        self.client_api.force_authenticate(self.client_user)

        self.client_api.patch("/api/client/profile/", {"language_code": "ceb"}, format="json")

        self.assertEqual(ClientHealthProfile.objects.get(user=self.client_user).medical_conditions, ["Type 2 Diabetes"])

    def test_rnd_patient_list_shows_primary_condition(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.client_api.force_authenticate(self.client_user)
        self.client_api.patch("/api/client/profile/", {"medical_conditions": ["Renal Nutrition", "Hypertension"]}, format="json")

        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.get("/api/rnd/patients/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]["condition"], "Renal Nutrition")


class RndConsultationModeTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()

    def test_new_rnd_offers_all_modes_by_default(self):
        self.assertEqual(RndProfile.objects.get(user=self.rnd).consultation_modes, ["video", "chat", "in_person"])

    def test_search_filters_by_mode(self):
        video_only = _make_rnd(email="video@t.ph")
        RndProfile.objects.filter(user=video_only).update(consultation_modes=["video"])
        self.client_api.force_authenticate(self.client_user)

        resp = self.client_api.get("/api/client/rnds/?mode=in_person")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual([r["user"]["id"] for r in resp.data], [self.rnd.id])

    def test_rnd_can_update_own_modes(self):
        self.client_api.force_authenticate(self.rnd)

        resp = self.client_api.patch("/api/rnd/profile/", {"consultation_modes": ["chat", "video", "chat"]}, format="json")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["consultation_modes"], ["video", "chat"])

    def test_rnd_can_update_consultation_fee(self):
        self.client_api.force_authenticate(self.rnd)

        resp = self.client_api.patch("/api/rnd/profile/", {"consultation_fee": "850.00"}, format="json")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["consultation_fee"], "850.00")
        self.assertEqual(RndProfile.objects.get(user=self.rnd).consultation_fee, Decimal("850.00"))

    def test_consultation_fee_cannot_be_negative(self):
        self.client_api.force_authenticate(self.rnd)

        resp = self.client_api.patch("/api/rnd/profile/", {"consultation_fee": "-1.00"}, format="json")

        self.assertEqual(resp.status_code, 400)
        self.assertIn("consultation_fee", resp.data)

    def test_modes_cannot_be_empty_or_unknown(self):
        self.client_api.force_authenticate(self.rnd)

        empty = self.client_api.patch("/api/rnd/profile/", {"consultation_modes": []}, format="json")
        unknown = self.client_api.patch("/api/rnd/profile/", {"consultation_modes": ["phone"]}, format="json")

        self.assertEqual(empty.status_code, 400)
        self.assertEqual(unknown.status_code, 400)


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


class RndPrcReadOnlyTests(TestCase):
    """Profile Settings shows the PRC license read-only: the RND can see it
    (including a signed link to their own license photo) but not change it,
    and clients never get the photo link."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        RndProfile.objects.filter(user=self.rnd).update(prc_license_image="prc-licenses/abc123")

    def test_rnd_cannot_change_prc_details(self):
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.patch("/api/rnd/profile/", {
            "prc_license_number": "CHANGED", "prc_expiry_date": "2099-01-01",
            "prc_license_image": "prc-licenses/other", "is_verified": False, "bio": "Updated bio — helping clients manage diabetes with Filipino meals.",
        }, format="json")

        self.assertEqual(resp.status_code, 200, resp.data)
        profile = RndProfile.objects.get(user=self.rnd)
        self.assertEqual(profile.prc_license_number, "PRC-rnd@t.ph")
        self.assertIsNone(profile.prc_expiry_date)
        self.assertEqual(profile.prc_license_image, "prc-licenses/abc123")
        self.assertTrue(profile.is_verified)
        self.assertEqual(profile.bio, "Updated bio — helping clients manage diabetes with Filipino meals.")  # the editable fields still save

    def test_own_profile_includes_signed_license_photo_link(self):
        from unittest.mock import patch

        self.client_api.force_authenticate(self.rnd)
        with patch("profiles.services.prc_license_image_url", return_value="https://signed.example/abc123") as signer:
            resp = self.client_api.get("/api/rnd/profile/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["prc_license_image_url"], "https://signed.example/abc123")
        signer.assert_called_once_with("prc-licenses/abc123")
        self.assertEqual(resp.data["prc_license_number"], "PRC-rnd@t.ph")

    def test_clients_never_get_the_license_photo_link(self):
        self.client_api.force_authenticate(_make_client())
        resp = self.client_api.get(f"/api/client/rnds/{self.rnd.id}/")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertNotIn("prc_license_image_url", resp.data)
        self.assertNotIn("prc_license_image", resp.data)
