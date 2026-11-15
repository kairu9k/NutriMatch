"""RND onboarding after approval (2026-11-16, panel feedback): sign-up asks only
what approval needs; fee, formats, languages, hours and payout are set after
approval, in one all-or-nothing request."""
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from billing.models import RndPayoutAccount
from core.test_utils import approve_rnd, onboard_client
from profiles.models import RndLanguage, RndProfile
from profiles.services import bookable_rnd_profiles

from .models import User

URL = "/api/auth/me/onboarding/complete/"
HOURS = [{"day_of_week": d, "start_time": "09:00", "end_time": "17:00"} for d in range(1, 6)]


def saved(block):
    """A block the way the weekly hours editor posts it."""
    return {**block, "effective_from": "2026-01-01"}


def valid(**over):
    body = {
        "profile": {"bio": "", "languages": ["en", "tl"], "consultation_fee": "600", "consultation_modes": ["video"]},
        "availability": HOURS,
    }
    body.update(over)
    return body


class RndOnboardingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.rnd = approve_rnd(User.objects.create_user(email="r@t.ph", password="x", role="rnd", first_name="R", last_name="D"))
        # approved, but nothing set up yet (what a fresh approval leaves)
        User.objects.filter(pk=self.rnd.pk).update(onboarding_completed_at=None)
        RndProfile.objects.filter(user=self.rnd).update(consultation_fee=Decimal("0"), bio=None)
        self.rnd.availability_schedules.all().delete()
        self.rnd.refresh_from_db()
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)

    def test_not_findable_until_onboarded(self):
        self.assertFalse(bookable_rnd_profiles().filter(user=self.rnd).exists())
        # even with a fee and hours already on file (e.g. an applicant from before this change)
        RndProfile.objects.filter(user=self.rnd).update(consultation_fee=Decimal("500"))
        self.assertEqual(self.api.post("/api/rnd/availability/", saved(HOURS[0]), format="json").status_code, 201)
        self.assertFalse(bookable_rnd_profiles().filter(user=self.rnd).exists())

    def test_finish_saves_everything_and_makes_them_findable(self):
        resp = self.api.post(URL, valid(payout={"method": "gcash", "account_name": "R D", "account_number": "09171234567"}), format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data["complete"])
        self.rnd.refresh_from_db()
        self.assertIsNotNone(self.rnd.onboarding_completed_at)
        profile = self.rnd.rnd_profile
        self.assertEqual((profile.consultation_fee, profile.consultation_modes), (Decimal("600.00"), ["video"]))
        self.assertEqual(sorted(RndLanguage.objects.filter(rnd=self.rnd).values_list("language_code", flat=True)), ["en", "tl"])
        self.assertEqual(self.rnd.availability_schedules.count(), 5)
        self.assertEqual(RndPayoutAccount.objects.get(rnd=self.rnd).account_number, "09171234567")
        self.assertTrue(bookable_rnd_profiles().filter(user=self.rnd).exists())

    def test_hours_already_saved_by_the_editor_are_used(self):
        for block in HOURS[:2]:
            self.assertEqual(self.api.post("/api/rnd/availability/", saved(block), format="json").status_code, 201)
        body = valid()
        del body["availability"]
        self.assertEqual(self.api.post(URL, body, format="json").status_code, 200)
        self.assertEqual(self.rnd.availability_schedules.count(), 2)  # kept, not replaced

    def test_no_hours_at_all_is_refused(self):
        body = valid()
        del body["availability"]
        resp = self.api.post(URL, body, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("availability", resp.data)

    def test_payout_can_be_skipped(self):
        self.assertEqual(self.api.post(URL, valid(), format="json").status_code, 200)
        self.assertFalse(RndPayoutAccount.objects.filter(rnd=self.rnd).exists())

    def test_required_things_are_checked_and_nothing_is_kept(self):
        for label, body, field in [
            ("no hours", valid(availability=[]), "availability"),
            ("hours under an hour", valid(availability=[{"day_of_week": 1, "start_time": "09:00", "end_time": "09:30"}]), "availability"),
            ("overlapping hours", valid(availability=[HOURS[0], {"day_of_week": 1, "start_time": "12:00", "end_time": "18:00"}]), "availability"),
            ("fee too low", valid(profile={"languages": ["en"], "consultation_fee": "50", "consultation_modes": ["video"]}), "consultation_fee"),
            ("no fee", valid(profile={"languages": ["en"], "consultation_modes": ["video"]}), "consultation_fee"),
            ("no languages", valid(profile={"languages": [], "consultation_fee": "600", "consultation_modes": ["video"]}), "languages"),
            ("no formats", valid(profile={"languages": ["en"], "consultation_fee": "600", "consultation_modes": []}), "consultation_modes"),
            ("in person without an address", valid(profile={"languages": ["en"], "consultation_fee": "600", "consultation_modes": ["video", "in_person"]}), "clinic_address"),
            ("short bio", valid(profile={"bio": "Too short", "languages": ["en"], "consultation_fee": "600", "consultation_modes": ["video"]}), "bio"),
            ("bad payout", valid(payout={"method": "gcash", "account_name": "R D", "account_number": "123"}), "payout"),
        ]:
            resp = self.api.post(URL, body, format="json")
            self.assertEqual(resp.status_code, 400, label)
            self.assertIn(field, resp.data, label)
        # the last two failed after the profile fields were valid: still nothing is kept
        self.rnd.refresh_from_db()
        self.assertIsNone(self.rnd.onboarding_completed_at)
        self.assertEqual(self.rnd.rnd_profile.consultation_fee, Decimal("0"))
        self.assertEqual(self.rnd.availability_schedules.count(), 0)
        self.assertFalse(RndLanguage.objects.filter(rnd=self.rnd).exists())

    def test_in_person_with_an_address_and_a_bio(self):
        body = valid(profile={
            "bio": "Registered Nutritionist-Dietitian with years of practice helping clients with diabetes.",
            "languages": ["en"], "consultation_fee": "700", "consultation_modes": ["video", "in_person"],
            "clinic_address": "Unit 4, Sample Building, Juan Luna Street, Davao City",
        })
        self.assertEqual(self.api.post(URL, body, format="json").status_code, 200)
        profile = RndProfile.objects.get(user=self.rnd)
        self.assertIn("Davao", profile.clinic_address)
        self.assertTrue(profile.bio.startswith("Registered"))

    def test_finishing_twice_changes_nothing(self):
        self.api.post(URL, valid(), format="json")
        again = self.api.post(URL, valid(profile={"languages": ["en"], "consultation_fee": "9999", "consultation_modes": ["video"]}), format="json")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(RndProfile.objects.get(user=self.rnd).consultation_fee, Decimal("600.00"))

    def test_an_unapproved_rnd_cannot_finish(self):
        RndProfile.objects.filter(user=self.rnd).update(is_verified=False, review_status="pending")
        self.rnd.refresh_from_db()
        self.assertEqual(self.api.post(URL, valid(), format="json").status_code, 403)

    def test_clients_and_admins(self):
        client = onboard_client(User.objects.create_user(email="c@t.ph", password="x", role="client", first_name="C", last_name="L"))
        User.objects.filter(pk=client.pk).update(onboarding_completed_at=None)
        client.refresh_from_db()
        self.api.force_authenticate(client)
        # the client's own flow is unchanged: it still asks for the required steps
        self.assertEqual(self.api.post(URL, {}, format="json").status_code, 400)
        admin = User.objects.create_user(email="a@t.ph", password="x", role="admin", first_name="A", last_name="D")
        self.api.force_authenticate(admin)
        self.assertEqual(self.api.post(URL, valid(), format="json").status_code, 403)


class ShorterRegistrationTests(TestCase):
    """Sign-up no longer asks for fee, formats or languages."""

    def test_register_without_them(self):
        from unittest.mock import patch

        from django.core.files.uploadedfile import SimpleUploadedFile

        cache.clear()
        payload = {
            "first_name": "Ivy", "last_name": "Cruz", "email": "short@t.ph", "password": "Str0ng!Pass1", "phone": "+639171234567",
            "date_of_birth": "1990-01-15", "specializations": '["Sports Nutrition"]', "prc_license_number": "2468013",
            "accept_terms": "true", "data_privacy_consent": "true",
            "prc_license_image": SimpleUploadedFile("license.jpg", b"fake", content_type="image/jpeg"),
            "prc_selfie_image": SimpleUploadedFile("selfie.jpg", b"fake", content_type="image/jpeg"),
        }
        with patch("accounts.serializers.upload_prc_license_image", return_value="prc/x"):
            resp = APIClient().post("/api/auth/register/rnd/", payload, format="multipart")
        self.assertEqual(resp.status_code, 201, resp.data)
        profile = RndProfile.objects.get(user__email="short@t.ph")
        self.assertEqual(profile.consultation_fee, 0)
        self.assertFalse(RndLanguage.objects.filter(rnd=profile.user).exists())
        self.assertIsNone(profile.user.onboarding_completed_at)

    def test_approval_leaves_onboarding_for_the_rnd(self):
        from django.utils import timezone

        rnd = User.objects.create_user(email="p@t.ph", password="x", role="rnd", first_name="P", last_name="R")
        User.objects.filter(pk=rnd.pk).update(email_verified_at=timezone.now())
        RndProfile.objects.create(user=rnd, prc_license_number="1111111")
        admin = User.objects.create_user(email="ad@t.ph", password="x", role="admin", first_name="A", last_name="D")
        api = APIClient()
        api.force_authenticate(admin)
        self.assertEqual(api.patch(f"/api/admin/users/{rnd.pk}/verify-rnd/").status_code, 200)
        rnd.refresh_from_db()
        self.assertTrue(rnd.rnd_profile.is_verified)
        self.assertIsNone(rnd.onboarding_completed_at)
