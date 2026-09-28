from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from profiles.models import ClientHealthProfile, ClientProfile, RndProfile
from profiles.services import LicenseImageUploadError

from .models import EmailVerificationCode, PasswordResetCode, User


class RegisterViewTests(TestCase):
    def setUp(self):
        # The register endpoint is rate-limited; its counter lives in the
        # cache and would otherwise carry over between these tests.
        cache.clear()
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
        self.assertEqual(user.health_profile.medical_conditions, ["Weight management"])
        # registering sends a verification code and leaves the account
        # unverified — login should be refused until it's used
        self.assertIsNone(user.email_verified_at)
        self.assertTrue(EmailVerificationCode.objects.filter(user=user).exists())

    def test_register_client_other_concern_is_not_stored_as_condition(self):
        resp = self.client_api.post("/api/auth/register/client/", {
            "first_name": "Ana", "last_name": "Reyes", "email": "other@t.ph", "password": "StrongPass123",
            "primary_health_concern": "Other",
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertIsNone(User.objects.get(email="other@t.ph").health_profile.medical_conditions)

    def test_register_client_duplicate_email_rejected(self):
        User.objects.create_user(email="dupe@t.ph", password="x", role="client", first_name="A", last_name="B")
        resp = self.client_api.post("/api/auth/register/client/", {
            "first_name": "Ana", "last_name": "Reyes", "email": "dupe@t.ph", "password": "StrongPass123",
        })
        self.assertEqual(resp.status_code, 400)

    def _rnd_payload(self, email="ivy@t.ph", image=None):
        return {
            "first_name": "Ivy", "last_name": "Alba", "email": email, "password": "StrongPass123",
            "specialization": "Diabetes",
            "prc_license_image": image or SimpleUploadedFile("license.jpg", b"fake-jpeg-bytes", content_type="image/jpeg"),
        }

    @patch("accounts.serializers.upload_prc_license_image", return_value="prc-licenses/abc123")
    def test_register_rnd_uploads_license_photo_and_creates_unverified_profile(self, mock_upload):
        resp = self.client_api.post("/api/auth/register/rnd/", self._rnd_payload(), format="multipart")

        self.assertEqual(resp.status_code, 201, resp.data)
        mock_upload.assert_called_once()
        profile = RndProfile.objects.get(user__email="ivy@t.ph")
        self.assertFalse(profile.is_verified)
        self.assertEqual(profile.prc_license_image, "prc-licenses/abc123")
        self.assertIsNone(profile.prc_license_number)

    @patch("accounts.serializers.upload_prc_license_image")
    def test_register_rnd_requires_license_photo(self, mock_upload):
        payload = self._rnd_payload()
        del payload["prc_license_image"]

        resp = self.client_api.post("/api/auth/register/rnd/", payload, format="multipart")

        self.assertEqual(resp.status_code, 400)
        self.assertIn("prc_license_image", resp.data)
        mock_upload.assert_not_called()
        self.assertFalse(User.objects.filter(email="ivy@t.ph").exists())

    @patch("accounts.serializers.upload_prc_license_image")
    def test_register_rnd_rejects_non_image_file(self, mock_upload):
        pdf = SimpleUploadedFile("license.pdf", b"%PDF-1.4", content_type="application/pdf")

        resp = self.client_api.post("/api/auth/register/rnd/", self._rnd_payload(image=pdf), format="multipart")

        self.assertEqual(resp.status_code, 400)
        self.assertIn("prc_license_image", resp.data)
        mock_upload.assert_not_called()

    @patch("accounts.serializers.upload_prc_license_image", side_effect=LicenseImageUploadError("upload failed"))
    def test_failed_upload_creates_no_account(self, mock_upload):
        resp = self.client_api.post("/api/auth/register/rnd/", self._rnd_payload(), format="multipart")

        self.assertEqual(resp.status_code, 400)
        self.assertFalse(User.objects.filter(email="ivy@t.ph").exists())


class EmailVerificationTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            email="unverified@t.ph", password="StrongPass123", role="client", first_name="Un", last_name="Verified"
        )

    def test_login_blocked_before_verification(self):
        resp = self.client_api.post("/api/auth/login/", {"email": "unverified@t.ph", "password": "StrongPass123"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("verify your email", resp.data["detail"])

    def test_verify_with_correct_code_allows_login(self):
        EmailVerificationCode.objects.create(
            user=self.user, code="654321", expires_at=timezone.now() + timedelta(minutes=15)
        )

        resp = self.client_api.post("/api/auth/verify-email/", {"email": "unverified@t.ph", "code": "654321"})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.email_verified_at)

        login_resp = self.client_api.post("/api/auth/login/", {"email": "unverified@t.ph", "password": "StrongPass123"})
        self.assertEqual(login_resp.status_code, 200)

    def test_verify_with_wrong_code_rejected(self):
        EmailVerificationCode.objects.create(
            user=self.user, code="654321", expires_at=timezone.now() + timedelta(minutes=15)
        )
        resp = self.client_api.post("/api/auth/verify-email/", {"email": "unverified@t.ph", "code": "000000"})
        self.assertEqual(resp.status_code, 400)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.email_verified_at)

    def test_verify_with_expired_code_rejected(self):
        EmailVerificationCode.objects.create(
            user=self.user, code="654321", expires_at=timezone.now() - timedelta(minutes=1)
        )
        resp = self.client_api.post("/api/auth/verify-email/", {"email": "unverified@t.ph", "code": "654321"})
        self.assertEqual(resp.status_code, 400)

    def test_verify_code_cannot_be_reused(self):
        EmailVerificationCode.objects.create(
            user=self.user, code="654321", expires_at=timezone.now() + timedelta(minutes=15)
        )
        first = self.client_api.post("/api/auth/verify-email/", {"email": "unverified@t.ph", "code": "654321"})
        self.assertEqual(first.status_code, 200)

        second_user = User.objects.create_user(
            email="unverified2@t.ph", password="StrongPass123", role="client", first_name="U2", last_name="V"
        )
        # reusing the same code value for a different user's (nonexistent)
        # verification should still fail — the code was tied to the first user
        second = self.client_api.post("/api/auth/verify-email/", {"email": "unverified2@t.ph", "code": "654321"})
        self.assertEqual(second.status_code, 400)
        second_user.refresh_from_db()
        self.assertIsNone(second_user.email_verified_at)

    def test_resend_creates_new_code_for_unverified_user(self):
        resp = self.client_api.post("/api/auth/verify-email/resend/", {"email": "unverified@t.ph"})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(EmailVerificationCode.objects.filter(user=self.user).exists())

    def test_resend_unknown_email_returns_same_generic_response(self):
        resp = self.client_api.post("/api/auth/verify-email/resend/", {"email": "nobody@t.ph"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["detail"], "If that email needs verification, a new code has been sent.")

    def test_resend_does_not_send_for_already_verified_user(self):
        self.user.email_verified_at = timezone.now()
        self.user.save(update_fields=["email_verified_at"])

        resp = self.client_api.post("/api/auth/verify-email/resend/", {"email": "unverified@t.ph"})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(EmailVerificationCode.objects.filter(user=self.user).exists())


class LoginAndMeViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.user = User.objects.create_user(
            email="login@t.ph", password="CorrectPass123", role="client", first_name="Lo", last_name="Gin"
        )
        self.user.email_verified_at = timezone.now()
        self.user.save(update_fields=["email_verified_at"])

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
        self.user.email_verified_at = timezone.now()
        self.user.save(update_fields=["email_verified_at"])

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


class AdminRndAndClientListTests(TestCase):
    """The new admin-facing user list endpoints (RndVerification.vue /
    ClientManagement.vue) — real prefetch-derived stats, not fabricated."""

    def setUp(self):
        self.client_api = APIClient()
        self.admin = User.objects.create_user(
            email="admin2@t.ph", password="x", role="admin", first_name="Ad", last_name="Min"
        )
        self.client_api.force_authenticate(self.admin)

    def test_non_admin_cannot_access_admin_rnd_list(self):
        rnd = User.objects.create_user(email="notadmin@t.ph", password="x", role="rnd", first_name="R", last_name="D")
        self.client_api.force_authenticate(rnd)
        resp = self.client_api.get("/api/admin/rnds/")
        self.assertEqual(resp.status_code, 403)

    def test_rnd_list_includes_pending_and_verified(self):
        pending = User.objects.create_user(email="pending@t.ph", password="x", role="rnd", first_name="P", last_name="D")
        RndProfile.objects.create(user=pending, prc_license_number="PRC-P1", is_verified=False)

        verified = User.objects.create_user(email="verified@t.ph", password="x", role="rnd", first_name="V", last_name="D")
        RndProfile.objects.create(user=verified, prc_license_number="PRC-V1", is_verified=True)

        resp = self.client_api.get("/api/admin/rnds/")
        self.assertEqual(resp.status_code, 200)
        emails = {r["email"] for r in resp.data}
        self.assertEqual(emails, {"pending@t.ph", "verified@t.ph"})

    def test_rnd_list_patient_count_and_revenue_are_real(self):
        from decimal import Decimal as D

        from billing.models import Invoice
        from scheduling.models import Appointment, RndClientRelationship

        rnd = User.objects.create_user(email="withpatients@t.ph", password="x", role="rnd", first_name="W", last_name="P")
        RndProfile.objects.create(user=rnd, prc_license_number="PRC-WP1", is_verified=True)
        client = User.objects.create_user(email="theirclient@t.ph", password="x", role="client", first_name="T", last_name="C")
        rel = RndClientRelationship.objects.create(rnd=rnd, client=client, status="active")
        appt = Appointment.objects.create(relationship=rel, scheduled_at=timezone.now(), type="chat", status="completed")
        Invoice.objects.create(relationship=rel, appointment=appt, amount=D("500.00"), status=Invoice.Status.PAID)

        resp = self.client_api.get("/api/admin/rnds/")
        row = next(r for r in resp.data if r["email"] == "withpatients@t.ph")
        self.assertEqual(row["patients"], 1)
        self.assertEqual(Decimal(row["revenue"]), D("500.00"))

    def test_client_list_shows_condition_and_matched_rnd(self):
        rnd = User.objects.create_user(email="matchedrnd@t.ph", password="x", role="rnd", first_name="M", last_name="R")
        client = User.objects.create_user(email="matchedclient@t.ph", password="x", role="client", first_name="M", last_name="C")
        ClientHealthProfile.objects.create(user=client, medical_conditions=["Type 2 Diabetes"])
        from scheduling.models import RndClientRelationship
        RndClientRelationship.objects.create(rnd=rnd, client=client, status="active")

        resp = self.client_api.get("/api/admin/clients/")
        row = next(r for r in resp.data if r["email"] == "matchedclient@t.ph")
        self.assertEqual(row["condition"], "Type 2 Diabetes")
        self.assertEqual(row["matched_rnd"], "M R")


class AdminPlatformStatsTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.admin = User.objects.create_user(
            email="admin3@t.ph", password="x", role="admin", first_name="Ad", last_name="Min"
        )
        self.client_api.force_authenticate(self.admin)

    def test_stats_reflect_real_counts(self):
        from scheduling.models import RndClientRelationship

        rnd = User.objects.create_user(email="statsrnd@t.ph", password="x", role="rnd", first_name="S", last_name="R")
        RndProfile.objects.create(user=rnd, prc_license_number="PRC-STATS1", is_verified=True)
        client = User.objects.create_user(email="statsclient@t.ph", password="x", role="client", first_name="S", last_name="C")
        RndClientRelationship.objects.create(rnd=rnd, client=client, status="active")

        resp = self.client_api.get("/api/admin/platform-stats/")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.data["active_rnds"], 1)
        self.assertGreaterEqual(resp.data["clients"], 1)
