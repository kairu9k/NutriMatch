"""Onboarding (2026-10-10): RND application → admin review → approved →
sign in; strict client onboarding before booking; listing/booking rules."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.test_utils import approve_rnd, onboard_client
from profiles.models import ClientHealthProfile, ClientProfile, RndAvailabilitySchedule, RndLanguage, RndProfile

from .models import User
from .tests import RND_APPLICATION


def _apply(api, **overrides):
    cache.clear()  # registration is rate-limited
    payload = {
        "first_name": "Rhea", "last_name": "Santos", "email": "rhea@t.ph", "password": "StrongPass123!",
        "accept_terms": True, "data_privacy_consent": True, "date_of_birth": "1990-03-01",
        "specialization": "Diabetes Management", "prc_license_number": "1234567",
        "prc_license_image": SimpleUploadedFile("license.jpg", b"fake", content_type="image/jpeg"),
        **RND_APPLICATION,
    }
    payload.update(overrides)
    return api.post("/api/auth/register/rnd/", payload, format="multipart")


def _verify_email(email):
    user = User.objects.get(email=email)
    user.email_verified_at = timezone.now()
    user.save(update_fields=["email_verified_at"])
    return user


@patch("accounts.serializers.upload_prc_license_image", return_value="prc-licenses/test")
class RndApplicationTests(TestCase):
    def setUp(self):
        self.api = APIClient()
        mail.outbox = []

    def test_application_saves_profile_languages_and_availability(self, _upload):
        resp = _apply(self.api)
        self.assertEqual(resp.status_code, 201, resp.data)
        user = User.objects.get(email="rhea@t.ph")
        profile = user.rnd_profile
        self.assertEqual(profile.review_status, "pending")
        self.assertFalse(profile.is_verified)
        self.assertEqual(profile.consultation_fee, Decimal("800.00"))
        self.assertEqual(profile.consultation_modes, ["video", "chat"])
        self.assertIn("diabetes", profile.bio)
        self.assertEqual(sorted(RndLanguage.objects.filter(rnd=user).values_list("language_code", flat=True)), ["en", "tl"])
        block = RndAvailabilitySchedule.objects.get(rnd=user)
        self.assertEqual((block.day_of_week, block.start_time.hour, block.end_time.hour), (1, 9, 12))
        self.assertIsNone(user.onboarding_completed_at)

    def test_invalid_application_fields(self, _upload):
        cases = {
            "consultation_fee": "99.00",
            "bio": "Too short.",
            "availability": "[]",
            "languages": '["xx"]',
            "consultation_modes": "[]",
        }
        for field, value in cases.items():
            resp = _apply(self.api, **{field: value})
            self.assertEqual(resp.status_code, 400, field)
            self.assertIn(field, resp.data, field)
        overlapping = '[{"day_of_week": 1, "start_time": "09:00", "end_time": "12:00"}, {"day_of_week": 1, "start_time": "11:00", "end_time": "13:00"}]'
        self.assertIn("availability", _apply(self.api, availability=overlapping).data)
        too_short = '[{"day_of_week": 2, "start_time": "09:00", "end_time": "09:30"}]'
        self.assertIn("availability", _apply(self.api, availability=too_short).data)

    def test_pending_and_rejected_rnds_cannot_sign_in(self, _upload):
        _apply(self.api)
        _verify_email("rhea@t.ph")
        resp = self.api.post("/api/auth/login/", {"email": "rhea@t.ph", "password": "StrongPass123!"}, format="json")
        self.assertEqual(resp.status_code, 401)
        self.assertIn("under review", str(resp.data["detail"]))
        RndProfile.objects.filter(user__email="rhea@t.ph").update(review_status="rejected")
        resp = self.api.post("/api/auth/login/", {"email": "rhea@t.ph", "password": "StrongPass123!"}, format="json")
        self.assertEqual(resp.status_code, 401)
        self.assertIn("wasn't approved", str(resp.data["detail"]))

    def test_unapproved_rnd_is_blocked_from_rnd_apis(self, _upload):
        _apply(self.api)
        user = _verify_email("rhea@t.ph")
        self.api.force_authenticate(user)
        self.assertEqual(self.api.get("/api/rnd/profile/").status_code, 403)
        self.assertEqual(self.api.get("/api/rnd/appointments/").status_code, 403)

    def test_admin_approves_then_rnd_signs_in(self, _upload):
        _apply(self.api)
        user = _verify_email("rhea@t.ph")
        admin = User.objects.create_user(email="admin@t.ph", password="x", role="admin", first_name="A", last_name="D")
        admin_api = APIClient()
        admin_api.force_authenticate(admin)
        listing = next(r for r in admin_api.get("/api/admin/rnds/").data if r["id"] == user.id)
        self.assertEqual(listing["review_status"], "pending")
        self.assertEqual(listing["availability"][0]["start_time"], "09:00")
        self.assertEqual(listing["languages"], ["English", "Filipino (Tagalog)"])

        resp = admin_api.patch(f"/api/admin/users/{user.id}/verify-rnd/")
        self.assertEqual(resp.status_code, 200, resp.data)
        user.refresh_from_db()
        self.assertEqual(user.rnd_profile.review_status, "approved")
        self.assertIsNotNone(user.onboarding_completed_at)
        self.assertEqual(len(mail.outbox), 2)  # verification code + approval
        approval = mail.outbox[-1]
        self.assertIn("approved", approval.subject)
        self.assertIn("/login", approval.body)
        login = self.api.post("/api/auth/login/", {"email": "rhea@t.ph", "password": "StrongPass123!"}, format="json")
        self.assertEqual(login.status_code, 200, login.data)

    def test_cannot_approve_before_email_is_verified(self, _upload):
        _apply(self.api)
        user = User.objects.get(email="rhea@t.ph")
        admin = User.objects.create_user(email="admin@t.ph", password="x", role="admin", first_name="A", last_name="D")
        admin_api = APIClient()
        admin_api.force_authenticate(admin)
        self.assertEqual(admin_api.patch(f"/api/admin/users/{user.id}/verify-rnd/").status_code, 400)

    def test_reject_with_reason_then_reapply_with_same_email(self, _upload):
        _apply(self.api)
        user = _verify_email("rhea@t.ph")
        admin = User.objects.create_user(email="admin@t.ph", password="x", role="admin", first_name="A", last_name="D")
        admin_api = APIClient()
        admin_api.force_authenticate(admin)
        self.assertEqual(admin_api.patch(f"/api/admin/users/{user.id}/reject-rnd/", {"reason": "short"}, format="json").status_code, 400)
        resp = admin_api.patch(
            f"/api/admin/users/{user.id}/reject-rnd/", {"reason": "The PRC license photo is blurry — please upload a clearer one."}, format="json",
        )
        self.assertEqual(resp.status_code, 200, resp.data)
        rejection = mail.outbox[-1]
        self.assertIn("blurry", rejection.body)
        self.assertIn("/register", rejection.body)

        again = _apply(self.api, prc_license_number="1234567")  # same email + same PRC number
        self.assertEqual(again.status_code, 201, again.data)
        self.assertEqual(User.objects.filter(email="rhea@t.ph").count(), 1)
        self.assertEqual(User.objects.get(email="rhea@t.ph").rnd_profile.review_status, "pending")

    def test_approved_rnd_email_cannot_be_reused(self, _upload):
        _apply(self.api)
        user = _verify_email("rhea@t.ph")
        approve_rnd(user)
        self.assertIn("email", _apply(self.api).data)


class RndListingRuleTests(TestCase):
    def setUp(self):
        self.client_user = onboard_client(User.objects.create_user(email="c@t.ph", password="x", role="client", first_name="C", last_name="L"))
        self.api = APIClient()
        self.api.force_authenticate(self.client_user)

    def _rnd(self, email, **fields):
        user = User.objects.create_user(email=email, password="x", role="rnd", first_name="R", last_name="D")
        RndProfile.objects.create(user=user, prc_license_number=f"P-{email}", consultation_modes=["video"])
        approve_rnd(user)
        RndProfile.objects.filter(user=user).update(**fields)
        return user

    def test_only_fully_set_up_rnds_are_listed_and_bookable(self):
        ready = self._rnd("ready@t.ph")
        cheap = self._rnd("cheap@t.ph", consultation_fee=Decimal("0"))
        no_bio = self._rnd("nobio@t.ph", bio="")
        no_hours = self._rnd("nohours@t.ph")
        RndAvailabilitySchedule.objects.filter(rnd=no_hours).delete()
        listed = {r["user"]["id"] for r in self.api.get("/api/client/rnds/").data}
        self.assertEqual(listed, {ready.id})
        when = (timezone.now() + timedelta(days=1)).isoformat()
        for rnd in (cheap, no_bio, no_hours):
            resp = self.api.post("/api/client/appointments/", {"rnd_id": rnd.id, "scheduled_at": when, "type": "video"}, format="json")
            self.assertEqual(resp.status_code, 400)
            self.assertIn("isn't taking bookings", str(resp.data))

    def test_client_must_finish_onboarding_before_booking(self):
        rnd = self._rnd("ready@t.ph")
        newbie = User.objects.create_user(email="new@t.ph", password="x", role="client", first_name="N", last_name="C")
        api = APIClient()
        api.force_authenticate(newbie)
        when = (timezone.now() + timedelta(days=1)).isoformat()
        resp = api.post("/api/client/appointments/", {"rnd_id": rnd.id, "scheduled_at": when, "type": "video"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Finish setting up", str(resp.data))

    def test_rnd_fee_minimum_and_languages_on_profile_update(self):
        rnd = self._rnd("ready@t.ph")
        api = APIClient()
        api.force_authenticate(rnd)
        self.assertEqual(api.patch("/api/rnd/profile/", {"consultation_fee": "50.00"}, format="json").status_code, 400)
        resp = api.patch("/api/rnd/profile/", {"languages": ["ceb", "en"]}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(sorted(RndLanguage.objects.filter(rnd=rnd).values_list("language_code", flat=True)), ["ceb", "en"])


class ClientOnboardingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="new@t.ph", password="x", role="client", first_name="N", last_name="C")
        ClientProfile.objects.create(user=self.user, date_of_birth=date(1995, 1, 1))
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def _steps(self):
        data = self.api.get("/api/auth/me/onboarding/").data
        return data, {s["key"]: s["done"] for s in data["steps"]}

    def test_steps_and_completion(self):
        data, steps = self._steps()
        self.assertFalse(data["complete"])
        self.assertEqual(steps, {"welcome": True, "about": False, "health": False, "screening": False})
        refused = self.api.post("/api/auth/me/onboarding/complete/")
        self.assertEqual(refused.status_code, 400)

        self.api.patch("/api/client/profile/", {"sex": "female", "allergies": [], "dietary_restrictions": ["Halal"]}, format="json")
        health = ClientHealthProfile.objects.get(user=self.user)
        self.assertEqual(health.allergies, [])  # answered: none
        self.assertEqual(health.dietary_restrictions, ["Halal"])
        _, steps = self._steps()
        self.assertTrue(steps["about"] and steps["health"])
        self.assertFalse(steps["screening"])

        self.api.post("/api/client/screening/", {"height_cm": "160", "weight_kg": "60"}, format="json")
        done = self.api.post("/api/auth/me/onboarding/complete/")
        self.assertEqual(done.status_code, 200, done.data)
        self.assertTrue(done.data["complete"])
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.onboarding_completed_at)
        self.assertIsNotNone(self.api.get("/api/auth/me/").data["onboarding_completed_at"])

    def test_rnd_onboarding_status_lists_missing_setup(self):
        rnd = User.objects.create_user(email="old@t.ph", password="x", role="rnd", first_name="O", last_name="R")
        RndProfile.objects.create(user=rnd, prc_license_number="P-old")
        approve_rnd(rnd, availability=False)
        RndProfile.objects.filter(user=rnd).update(consultation_fee=Decimal("0"))
        api = APIClient()
        api.force_authenticate(rnd)
        keys = {m["key"] for m in api.get("/api/auth/me/onboarding/").data["missing"]}
        self.assertEqual(keys, {"fee", "availability", "languages"})


class WelcomeMessageTests(TestCase):
    def test_welcome_seen_is_recorded_once(self):
        user = User.objects.create_user(email="w@t.ph", password="x", role="client", first_name="W", last_name="C")
        api = APIClient()
        api.force_authenticate(user)
        self.assertIsNone(api.get("/api/auth/me/").data["welcome_seen_at"])
        first = api.post("/api/auth/me/welcome-seen/").data["welcome_seen_at"]
        self.assertIsNotNone(first)
        self.assertEqual(api.post("/api/auth/me/welcome-seen/").data["welcome_seen_at"], first)
        self.assertEqual(APIClient().post("/api/auth/me/welcome-seen/").status_code, 401)
