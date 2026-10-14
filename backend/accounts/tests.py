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


# The rest of an RND application (onboarding, 2026-10-10) — list fields are
# JSON strings, the way the multipart registration form sends them.
RND_APPLICATION = {
    "bio": "Registered Nutritionist-Dietitian helping adults manage diabetes with practical Filipino meals.",
    "consultation_fee": "800.00",
    "consultation_modes": '["video", "chat"]',
    "languages": '["en", "tl"]',
    "availability": '[{"day_of_week": 1, "start_time": "09:00", "end_time": "12:00"}]',
}


class RegisterViewTests(TestCase):
    def setUp(self):
        # The register endpoint is rate-limited; its counter lives in the
        # cache and would otherwise carry over between these tests.
        cache.clear()
        self.client_api = APIClient()

    def test_register_client_creates_user_and_profiles(self):
        resp = self.client_api.post("/api/auth/register/client/", {
            "first_name": "Ana", "last_name": "Reyes", "email": "ana@t.ph", "password": "StrongPass123!",
            "accept_terms": True, "data_privacy_consent": True,
            "date_of_birth": "1995-05-01", "sex": "female", "primary_health_concern": "Weight management",
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        user = User.objects.get(email="ana@t.ph")
        self.assertEqual(user.role, "client")
        profile = ClientProfile.objects.get(user=user)
        self.assertEqual(str(profile.date_of_birth), "1995-05-01")
        self.assertIsNone(user.health_profile.health_goals)  # goals are picked in onboarding
        self.assertEqual(user.health_profile.medical_conditions, ["Weight management"])
        # registering sends a verification code and leaves the account
        # unverified — login should be refused until it's used
        self.assertIsNone(user.email_verified_at)
        self.assertTrue(EmailVerificationCode.objects.filter(user=user).exists())

    def test_register_client_other_concern_is_not_stored_as_condition(self):
        resp = self.client_api.post("/api/auth/register/client/", {
            "first_name": "Ana", "last_name": "Reyes", "email": "other@t.ph", "password": "StrongPass123!",
            "accept_terms": True, "data_privacy_consent": True,
            "date_of_birth": "1995-05-01", "primary_health_concern": "Other",
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertIsNone(User.objects.get(email="other@t.ph").health_profile.medical_conditions)

    def test_register_client_duplicate_email_rejected(self):
        User.objects.create_user(email="dupe@t.ph", password="x", role="client", first_name="A", last_name="B")
        resp = self.client_api.post("/api/auth/register/client/", {
            "first_name": "Ana", "last_name": "Reyes", "email": "dupe@t.ph", "password": "StrongPass123!",
            "accept_terms": True, "data_privacy_consent": True,
        })
        self.assertEqual(resp.status_code, 400)

    def _rnd_payload(self, email="ivy@t.ph", image=None):
        return {
            "first_name": "Ivy", "last_name": "Alba", "email": email, "password": "StrongPass123!",
            "accept_terms": True, "data_privacy_consent": True,
            "date_of_birth": "1990-01-15", "specialization": "Diabetes Management", "prc_license_number": "0123456",
            "prc_license_image": image or SimpleUploadedFile("license.jpg", b"fake-jpeg-bytes", content_type="image/jpeg"),
            **RND_APPLICATION,
        }

    @patch("accounts.serializers.upload_prc_license_image", return_value="prc-licenses/abc123")
    def test_register_rnd_uploads_license_photo_and_creates_unverified_profile(self, mock_upload):
        resp = self.client_api.post("/api/auth/register/rnd/", self._rnd_payload(), format="multipart")

        self.assertEqual(resp.status_code, 201, resp.data)
        mock_upload.assert_called_once()
        profile = RndProfile.objects.get(user__email="ivy@t.ph")
        self.assertFalse(profile.is_verified)
        self.assertEqual(profile.prc_license_image, "prc-licenses/abc123")
        self.assertEqual(profile.prc_license_number, "0123456")

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
            email="unverified@t.ph", password="StrongPass123!", role="client", first_name="Un", last_name="Verified"
        )

    def test_login_blocked_before_verification(self):
        resp = self.client_api.post("/api/auth/login/", {"email": "unverified@t.ph", "password": "StrongPass123!"})
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

        login_resp = self.client_api.post("/api/auth/login/", {"email": "unverified@t.ph", "password": "StrongPass123!"})
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
            email="unverified2@t.ph", password="StrongPass123!", role="client", first_name="U2", last_name="V"
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
            "email": "reset@t.ph", "code": "123456", "new_password": "BrandNewPass123!",
        })

        self.assertEqual(resp.status_code, 200, resp.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPass123!"))
        reset.refresh_from_db()
        self.assertIsNotNone(reset.used_at)

        login_resp = self.client_api.post("/api/auth/login/", {"email": "reset@t.ph", "password": "BrandNewPass123!"})
        self.assertEqual(login_resp.status_code, 200)

    def test_confirm_with_wrong_code_rejected(self):
        PasswordResetCode.objects.create(
            user=self.user, code="123456", expires_at=timezone.now() + timedelta(minutes=15)
        )
        resp = self.client_api.post("/api/auth/password-reset/confirm/", {
            "email": "reset@t.ph", "code": "000000", "new_password": "BrandNewPass123!",
        })
        self.assertEqual(resp.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123"))

    def test_confirm_with_expired_code_rejected(self):
        PasswordResetCode.objects.create(
            user=self.user, code="123456", expires_at=timezone.now() - timedelta(minutes=1)
        )
        resp = self.client_api.post("/api/auth/password-reset/confirm/", {
            "email": "reset@t.ph", "code": "123456", "new_password": "BrandNewPass123!",
        })
        self.assertEqual(resp.status_code, 400)

    def test_confirm_code_cannot_be_reused(self):
        PasswordResetCode.objects.create(
            user=self.user, code="123456", expires_at=timezone.now() + timedelta(minutes=15)
        )
        first = self.client_api.post("/api/auth/password-reset/confirm/", {
            "email": "reset@t.ph", "code": "123456", "new_password": "FirstNewPass123!",
        })
        self.assertEqual(first.status_code, 200)

        second = self.client_api.post("/api/auth/password-reset/confirm/", {
            "email": "reset@t.ph", "code": "123456", "new_password": "SecondNewPass123!",
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


class RegistrationValidationTests(TestCase):
    """Names are letters only, dates of birth can't be in the future, and
    passwords need upper + lower + number + special character."""

    def setUp(self):
        cache.clear()
        self.client_api = APIClient()

    def _register(self, **overrides):
        payload = {
            "first_name": "Ana", "last_name": "Reyes", "email": "valid@t.ph", "password": "StrongPass123!",
            "accept_terms": True, "data_privacy_consent": True,
            "date_of_birth": "1995-05-01", "sex": "female",
        }
        payload.update(overrides)
        return self.client_api.post("/api/auth/register/client/", payload)

    def test_names_with_numbers_are_rejected(self):
        resp = self._register(first_name="Ana2", last_name="Reyes 3")

        self.assertEqual(resp.status_code, 400)
        self.assertIn("first_name", resp.data)
        self.assertIn("last_name", resp.data)
        self.assertFalse(User.objects.filter(email="valid@t.ph").exists())

    def test_real_names_with_spaces_and_punctuation_are_accepted(self):
        resp = self._register(first_name="Ma.  Theresa", last_name="Dela Cruz-O'Niño")

        self.assertEqual(resp.status_code, 201, resp.data)
        user = User.objects.get(email="valid@t.ph")
        self.assertEqual(user.first_name, "Ma. Theresa")  # extra spaces collapsed
        self.assertEqual(user.last_name, "Dela Cruz-O'Niño")

    def test_names_are_capitalized(self):
        resp = self._register(first_name="juan miguel", last_name="dela cruz-o'neil")

        self.assertEqual(resp.status_code, 201, resp.data)
        user = User.objects.get(email="valid@t.ph")
        self.assertEqual(user.first_name, "Juan Miguel")
        self.assertEqual(user.last_name, "Dela Cruz-O'Neil")

    def test_clients_must_be_18(self):
        from datetime import date

        today = date.today()
        five = today.replace(year=today.year - 5)
        resp = self._register(date_of_birth=str(five))
        self.assertEqual(resp.status_code, 400)
        self.assertIn("at least 18", str(resp.data["date_of_birth"]))

        eighteen = today.replace(year=today.year - 18)
        self.assertEqual(self._register(email="adult@t.ph", date_of_birth=str(eighteen)).status_code, 201)

    def test_date_of_birth_is_required_for_clients(self):
        resp = self._register(date_of_birth="")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("date_of_birth", resp.data)

    @patch("accounts.serializers.upload_prc_license_image", return_value="prc-licenses/x")
    def test_rnds_must_be_21_and_their_birth_date_is_saved(self, mock_upload):
        from datetime import date

        today = date.today()

        def rnd(email, dob):
            return self.client_api.post("/api/auth/register/rnd/", {
                "first_name": "Ivy", "last_name": "Alba", "email": email, "password": "StrongPass123!",
            "accept_terms": True, "data_privacy_consent": True,
                "date_of_birth": dob, "specialization": "Sports Nutrition",
                "prc_license_number": str(abs(hash(email)) % 10_000_000).zfill(7),
                "prc_license_image": SimpleUploadedFile("license.jpg", b"fake", content_type="image/jpeg"),
                **RND_APPLICATION,
            }, format="multipart")

        too_young = rnd("young@t.ph", str(today.replace(year=today.year - 20)))
        self.assertEqual(too_young.status_code, 400)
        self.assertIn("at least 21", str(too_young.data["date_of_birth"]))
        self.assertEqual(rnd("nodob@t.ph", "").status_code, 400)

        ok = rnd("rnd21@t.ph", "1990-01-15")
        self.assertEqual(ok.status_code, 201, ok.data)
        self.assertEqual(str(RndProfile.objects.get(user__email="rnd21@t.ph").date_of_birth), "1990-01-15")

    def test_future_date_of_birth_is_rejected(self):
        from datetime import date, timedelta

        resp = self._register(date_of_birth=str(date.today() + timedelta(days=1)))

        self.assertEqual(resp.status_code, 400)
        self.assertIn("date_of_birth", resp.data)

    def test_weak_passwords_are_rejected(self):
        for weak, missing in [
            ("alllowercase1!", "uppercase"),
            ("ALLUPPERCASE1!", "lowercase"),
            ("NoNumbersHere!", "number"),
            ("NoSpecial123", "special character"),
        ]:
            resp = self._register(email=f"{missing.split()[0]}@t.ph", password=weak)
            self.assertEqual(resp.status_code, 400, weak)
            self.assertIn(missing, str(resp.data["password"]), weak)

    def test_profile_name_edit_also_rejects_numbers(self):
        user = User.objects.create_user(email="edit@t.ph", password="x", role="client", first_name="Ana", last_name="Reyes")
        self.client_api.force_authenticate(user)

        resp = self.client_api.patch("/api/auth/me/", {"first_name": "Ana99"}, format="json")

        self.assertEqual(resp.status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Ana")


class RegistrationConsentTests(TestCase):
    """RA 10173 informed consent: registration needs both checkboxes, and
    the consent is stored on the account and in the audit log."""

    def setUp(self):
        cache.clear()
        self.client_api = APIClient()

    def _register(self, **overrides):
        payload = {
            "first_name": "Ana", "last_name": "Reyes", "email": "consent@t.ph", "password": "StrongPass123!",
            "date_of_birth": "1995-05-01", "accept_terms": True, "data_privacy_consent": True,
        }
        payload.update(overrides)
        return self.client_api.post("/api/auth/register/client/", payload, format="json")

    def test_registration_without_consent_is_refused(self):
        for missing in ["accept_terms", "data_privacy_consent"]:
            resp = self._register(**{missing: False})
            self.assertEqual(resp.status_code, 400, missing)
            self.assertIn(missing, resp.data)
        payload_without = {"first_name": "Ana", "last_name": "Reyes", "email": "none@t.ph",
                           "password": "StrongPass123!", "date_of_birth": "1995-05-01"}
        self.assertEqual(self.client_api.post("/api/auth/register/client/", payload_without, format="json").status_code, 400)
        self.assertFalse(User.objects.filter(email__in=["consent@t.ph", "none@t.ph"]).exists())

    def test_consent_is_recorded_and_audited(self):
        from core.models import AuditLog

        resp = self._register()

        self.assertEqual(resp.status_code, 201, resp.data)
        user = User.objects.get(email="consent@t.ph")
        self.assertIsNotNone(user.terms_accepted_at)
        self.assertIsNotNone(user.data_consent_at)
        log = AuditLog.objects.get(action="consent.given", record_id=user.id)
        self.assertEqual(log.user, user)
        self.assertTrue(log.new_values["data_processing_consent"])



class RegistrationEmailAndRndFieldTests(TestCase):
    """Unverified signups can be redone; RNDs give a 7-digit PRC number and
    pick a specialization from the list."""

    def setUp(self):
        cache.clear()
        self.client_api = APIClient()

    def _client(self, **overrides):
        cache.clear()  # registration is rate-limited (5/min)
        payload = {
            "first_name": "Ana", "last_name": "Reyes", "email": "redo@t.ph", "password": "StrongPass123!",
            "date_of_birth": "1995-05-01", "accept_terms": True, "data_privacy_consent": True,
        }
        payload.update(overrides)
        return self.client_api.post("/api/auth/register/client/", payload, format="json")

    def _rnd(self, **overrides):
        cache.clear()  # registration is rate-limited (5/min)
        payload = {
            "first_name": "Ivy", "last_name": "Alba", "email": "rnd-redo@t.ph", "password": "StrongPass123!",
            "date_of_birth": "1990-01-15", "prc_license_number": "0123456", "specialization": "Renal Nutrition",
            "accept_terms": True, "data_privacy_consent": True,
            "prc_license_image": SimpleUploadedFile("license.jpg", b"fake", content_type="image/jpeg"),
            **RND_APPLICATION,
        }
        payload.update(overrides)
        return self.client_api.post("/api/auth/register/rnd/", payload, format="multipart")

    def test_unverified_signup_can_register_again(self):
        self.assertEqual(self._client().status_code, 201)
        first_id = User.objects.get(email="redo@t.ph").id

        resp = self._client(first_name="Anna")

        self.assertEqual(resp.status_code, 201, resp.data)
        users = User.objects.filter(email="redo@t.ph")
        self.assertEqual(users.count(), 1)
        self.assertNotEqual(users.first().id, first_id)
        self.assertEqual(users.first().first_name, "Anna")

    def test_verified_email_is_still_taken(self):
        self.assertEqual(self._client().status_code, 201)
        User.objects.filter(email="redo@t.ph").update(email_verified_at=timezone.now())

        resp = self._client()

        self.assertEqual(resp.status_code, 400)
        self.assertIn("already exists", str(resp.data["email"]))

    @patch("accounts.serializers.upload_prc_license_image", return_value="prc-licenses/x")
    def test_rnd_prc_number_and_specialization(self, mock_upload):
        for bad in ["12345", "12345678", "01234ab", ""]:
            self.assertEqual(self._rnd(prc_license_number=bad).status_code, 400, bad)
        self.assertEqual(self._rnd(specialization="Astrology").status_code, 400)

        ok = self._rnd()
        self.assertEqual(ok.status_code, 201, ok.data)
        profile = RndProfile.objects.get(user__email="rnd-redo@t.ph")
        self.assertEqual(profile.prc_license_number, "0123456")
        self.assertEqual(profile.specialization, "Renal Nutrition")

        # someone else (verified) already holds that number
        User.objects.filter(email="rnd-redo@t.ph").update(email_verified_at=timezone.now())
        dupe = self._rnd(email="other-rnd@t.ph")
        self.assertEqual(dupe.status_code, 400)
        self.assertIn("already registered", str(dupe.data["prc_license_number"]))

    @patch("accounts.serializers.upload_prc_license_image", return_value="prc-licenses/x")
    def test_unverified_rnd_can_redo_with_the_same_prc_number(self, mock_upload):
        self.assertEqual(self._rnd().status_code, 201)

        again = self._rnd(first_name="Ivana")

        self.assertEqual(again.status_code, 201, again.data)
        self.assertEqual(RndProfile.objects.filter(prc_license_number="0123456").count(), 1)


PHOTO_URL = "https://res.cloudinary.com/demo/image/upload/c_fill,g_face,h_400,w_400/v1/profile-photos/{}.jpg"


@patch("profiles.services._configure")
class ProfilePhotoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="photo@t.ph", password="x", role="client", first_name="Pia", last_name="Cruz",
        )
        self.api = APIClient()
        self.api.force_authenticate(self.user)

    def _image(self, name="me.jpg", content_type="image/jpeg", size=1024):
        return SimpleUploadedFile(name, b"\xff\xd8" + b"0" * size, content_type=content_type)

    @patch("cloudinary.uploader.destroy")
    @patch("cloudinary.uploader.upload")
    def test_upload_sets_photo_and_replacing_deletes_the_old_one(self, upload, destroy, _cfg):
        upload.return_value = {"secure_url": PHOTO_URL.format("first")}
        resp = self.api.post("/api/auth/me/photo/", {"photo": self._image()}, format="multipart")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["profile_photo"], PHOTO_URL.format("first"))
        # cropped to a small square avatar on upload
        self.assertEqual(upload.call_args.kwargs["transformation"][0]["width"], 400)
        destroy.assert_not_called()

        upload.return_value = {"secure_url": PHOTO_URL.format("second")}
        self.api.post("/api/auth/me/photo/", {"photo": self._image()}, format="multipart")
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile_photo, PHOTO_URL.format("second"))
        destroy.assert_called_once()
        self.assertEqual(destroy.call_args.args[0], "profile-photos/first")

    @patch("cloudinary.uploader.upload")
    def test_rejects_wrong_type_too_big_and_missing(self, upload, _cfg):
        cases = [
            {"photo": self._image("doc.pdf", "application/pdf")},
            {"photo": self._image(size=2 * 1024 * 1024 + 1)},
            {},
        ]
        for payload in cases:
            resp = self.api.post("/api/auth/me/photo/", payload, format="multipart")
            self.assertEqual(resp.status_code, 400)
            self.assertIn("photo", resp.data)
        upload.assert_not_called()

    @patch("cloudinary.uploader.destroy")
    def test_delete_removes_photo(self, destroy, _cfg):
        self.user.profile_photo = PHOTO_URL.format("gone")
        self.user.save()
        resp = self.api.delete("/api/auth/me/photo/")
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data["profile_photo"])
        self.assertEqual(destroy.call_args.args[0], "profile-photos/gone")

    def test_requires_login(self, _cfg):
        resp = APIClient().post("/api/auth/me/photo/", {"photo": self._image()}, format="multipart")
        self.assertEqual(resp.status_code, 401)


class BrandedEmailTests(TestCase):
    """Code emails are branded HTML (with a plain-text version) and embed the logo inline."""

    def setUp(self):
        from django.core import mail

        mail.outbox = []
        self.user = User.objects.create_user(email="mail@t.ph", password="x", role="client", first_name="Mara", last_name="Cruz")

    def _check(self, subject_part, heading):
        from django.core import mail

        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertIn(subject_part, msg.subject)
        html = msg.alternatives[0].content if hasattr(msg.alternatives[0], "content") else msg.alternatives[0][0]
        code = EmailVerificationCode.objects.filter(user=self.user).first() or PasswordResetCode.objects.filter(user=self.user).first()
        self.assertIn(code.code, html)
        self.assertIn(code.code, msg.body)  # plain-text version too
        self.assertIn(heading, html)
        self.assertIn("cid:nutrimatch-logo", html)
        cids = [p.get("Content-ID") for p in msg.message().walk() if p.get_content_type() == "image/png"]
        self.assertEqual(cids, ["<nutrimatch-logo>"])

    def test_verification_email(self):
        from .services import send_verification_code

        send_verification_code(self.user)
        self._check("Verify your NutriMatch email", "Confirm your email address")

    def test_password_reset_email(self):
        from .services import request_password_reset

        request_password_reset(self.user)
        self._check("password reset code", "Reset your password")
