from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from profiles.models import ClientProfile, RndProfile

from .models import PasswordResetCode, User


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()

    def test_register_client_creates_user_and_profiles(self):
        resp = self.client_api.post("/api/auth/register/client/", {
            "first_name": "Ana", "last_name": "Reyes", "email": "ana@t.ph", "password": "StrongPass123",
            "date_of_birth": "1995-05-01", "sex": "female", "primary_health_concern": "Weight management",
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        user = User.objects.get(email="ana@t.ph")
        self.assertEqual(user.role, "client")
        profile = ClientProfile.objects.get(user=user)
        self.assertEqual(str(profile.date_of_birth), "1995-05-01")
        self.assertEqual(user.health_profile.health_goals, ["Weight management"])

    def test_register_client_duplicate_email_rejected(self):
        User.objects.create_user(email="dupe@t.ph", password="x", role="client", first_name="A", last_name="B")
        resp = self.client_api.post("/api/auth/register/client/", {
            "first_name": "Ana", "last_name": "Reyes", "email": "dupe@t.ph", "password": "StrongPass123",
        })
        self.assertEqual(resp.status_code, 400)

    def test_register_rnd_creates_unverified_profile(self):
        resp = self.client_api.post("/api/auth/register/rnd/", {
            "first_name": "Ivy", "last_name": "Alba", "email": "ivy@t.ph", "password": "StrongPass123",
            "prc_license_number": "PRC-0099", "specialization": "Diabetes",
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        user = User.objects.get(email="ivy@t.ph")
        profile = RndProfile.objects.get(user=user)
        self.assertFalse(profile.is_verified)

    def test_register_rnd_duplicate_prc_license_rejected(self):
        existing = User.objects.create_user(email="rnd1@t.ph", password="x", role="rnd", first_name="A", last_name="B")
        RndProfile.objects.create(user=existing, prc_license_number="PRC-DUPE")

        resp = self.client_api.post("/api/auth/register/rnd/", {
            "first_name": "Ivy", "last_name": "Alba", "email": "ivy2@t.ph", "password": "StrongPass123",
            "prc_license_number": "PRC-DUPE",
        })
        self.assertEqual(resp.status_code, 400)


class LoginAndMeViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            email="login@t.ph", password="CorrectPass123", role="client", first_name="Lo", last_name="Gin"
        )

    def test_login_success_returns_tokens_and_claims(self):
        resp = self.client_api.post("/api/auth/login/", {"email": "login@t.ph", "password": "CorrectPass123"})

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)
        self.assertEqual(resp.data["user"]["email"], "login@t.ph")

    def test_login_wrong_password_rejected(self):
        resp = self.client_api.post("/api/auth/login/", {"email": "login@t.ph", "password": "WrongPass"})
        self.assertEqual(resp.status_code, 401)

    def test_me_requires_authentication(self):
        resp = self.client_api.get("/api/auth/me/")
        self.assertEqual(resp.status_code, 401)

    def test_me_returns_current_user(self):
        self.client_api.force_authenticate(self.user)
        resp = self.client_api.get("/api/auth/me/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["email"], "login@t.ph")


class PasswordResetTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            email="reset@t.ph", password="OldPass123", role="client", first_name="Re", last_name="Set"
        )

    def test_request_reset_creates_code_for_existing_user(self):
        resp = self.client_api.post("/api/auth/password-reset/request/", {"email": "reset@t.ph"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(PasswordResetCode.objects.filter(user=self.user).exists())

    def test_request_reset_unknown_email_returns_same_generic_response(self):
        resp = self.client_api.post("/api/auth/password-reset/request/", {"email": "nobody@t.ph"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["detail"], "If that email is registered, a reset code has been sent.")

    def test_confirm_with_correct_code_resets_password(self):
        reset = PasswordResetCode.objects.create(
            user=self.user, code="123456", expires_at=timezone.now() + timedelta(minutes=15)
        )

        resp = self.client_api.post("/api/auth/password-reset/confirm/", {
            "email": "reset@t.ph", "code": "123456", "new_password": "BrandNewPass123",
        })

        self.assertEqual(resp.status_code, 200, resp.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPass123"))
        reset.refresh_from_db()
        self.assertIsNotNone(reset.used_at)

        login_resp = self.client_api.post("/api/auth/login/", {"email": "reset@t.ph", "password": "BrandNewPass123"})
        self.assertEqual(login_resp.status_code, 200)

    def test_confirm_with_wrong_code_rejected(self):
        PasswordResetCode.objects.create(
            user=self.user, code="123456", expires_at=timezone.now() + timedelta(minutes=15)
        )
        resp = self.client_api.post("/api/auth/password-reset/confirm/", {
            "email": "reset@t.ph", "code": "000000", "new_password": "BrandNewPass123",
        })
        self.assertEqual(resp.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123"))

    def test_confirm_with_expired_code_rejected(self):
        PasswordResetCode.objects.create(
            user=self.user, code="123456", expires_at=timezone.now() - timedelta(minutes=1)
        )
        resp = self.client_api.post("/api/auth/password-reset/confirm/", {
            "email": "reset@t.ph", "code": "123456", "new_password": "BrandNewPass123",
        })
        self.assertEqual(resp.status_code, 400)

    def test_confirm_code_cannot_be_reused(self):
        PasswordResetCode.objects.create(
            user=self.user, code="123456", expires_at=timezone.now() + timedelta(minutes=15)
        )
        first = self.client_api.post("/api/auth/password-reset/confirm/", {
            "email": "reset@t.ph", "code": "123456", "new_password": "FirstNewPass123",
        })
        self.assertEqual(first.status_code, 200)

        second = self.client_api.post("/api/auth/password-reset/confirm/", {
            "email": "reset@t.ph", "code": "123456", "new_password": "SecondNewPass123",
        })
        self.assertEqual(second.status_code, 400)
