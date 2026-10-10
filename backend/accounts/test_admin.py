"""Admin powers (2026-10-10): see everything except passwords, deactivate
with a reason / reactivate / send a password reset, all audit-logged."""

from decimal import Decimal

from django.core import mail
from django.test import TestCase
from rest_framework.test import APIClient

from clinical.models import PreConsultationScreening
from core.models import AuditLog, SystemSetting
from core.test_utils import approve_rnd, onboard_client
from profiles.models import ClientHealthProfile, ClientProfile

from .models import PasswordResetCode, User


class AdminUserTests(TestCase):
    def setUp(self):
        mail.outbox = []
        self.admin = User.objects.create_user(email="admin@a.ph", password="x", role="admin", first_name="Ad", last_name="Min")
        self.api = APIClient()
        self.api.force_authenticate(self.admin)
        self.client_user = onboard_client(User.objects.create_user(email="c@a.ph", password="Secret123!", role="client", first_name="Ana", last_name="Cruz"))
        ClientProfile.objects.create(user=self.client_user, sex="female")
        ClientHealthProfile.objects.create(user=self.client_user, allergies=["Shrimp"], medical_conditions=["Hypertension"])
        PreConsultationScreening.objects.create(client=self.client_user, height_cm=Decimal("160"), weight_kg=Decimal("60"), bmi=Decimal("23.4"))

    def test_client_overview_shows_health_and_is_audit_logged(self):
        resp = self.api.get(f"/api/admin/users/{self.client_user.id}/overview/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["client"]["health"]["allergies"], ["Shrimp"])
        self.assertEqual(resp.data["client"]["latest_screening"]["bmi"], Decimal("23.40"))
        self.assertNotIn("password", str(resp.data).lower())
        self.assertTrue(AuditLog.objects.filter(action="client.record_viewed", user=self.admin, record_id=self.client_user.id).exists())

    def test_rnd_overview(self):
        rnd = approve_rnd(User.objects.create_user(email="r@a.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        data = self.api.get(f"/api/admin/users/{rnd.id}/overview/").data["rnd"]
        self.assertEqual(data["profile"]["review_status"], "approved")
        self.assertIsNone(data["payout_account"])
        self.assertIn("posted", data["earnings"])

    def test_deactivate_with_reason_then_reactivate(self):
        url = f"/api/admin/users/{self.client_user.id}"
        self.assertEqual(self.api.post(f"{url}/deactivate/", {"reason": "spam"}, format="json").status_code, 400)
        resp = self.api.post(f"{url}/deactivate/", {"reason": "Repeated no-shows and abusive messages."}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.client_user.refresh_from_db()
        self.assertFalse(self.client_user.is_active)
        self.assertIn("abusive", mail.outbox[-1].body)
        self.assertTrue(AuditLog.objects.filter(action="user.deactivated", new_values__reason__icontains="no-shows").exists())
        login = APIClient().post("/api/auth/login/", {"email": "c@a.ph", "password": "Secret123!"}, format="json")
        self.assertEqual(login.status_code, 401)

        self.assertEqual(self.api.post(f"{url}/reactivate/").status_code, 200)
        self.client_user.refresh_from_db()
        self.assertTrue(self.client_user.is_active)
        self.assertTrue(AuditLog.objects.filter(action="user.reactivated").exists())

    def test_deactivated_login_says_why_only_with_the_right_password(self):
        SystemSetting.objects.update_or_create(key="support_email", defaults={"value": "help@nutrimatch.test"})
        self.api.post(f"/api/admin/users/{self.client_user.id}/deactivate/", {"reason": "Repeated no-shows."}, format="json")
        self.assertIn("help@nutrimatch.test", mail.outbox[-1].body)

        login = APIClient().post("/api/auth/login/", {"email": "C@A.ph", "password": "Secret123!"}, format="json")
        self.assertEqual(login.status_code, 401)
        self.assertEqual(login.data["code"], "account_deactivated")
        self.assertIn("deactivated by the NutriMatch admin", login.data["detail"])
        self.assertEqual(login.data["support_email"], "help@nutrimatch.test")

        wrong = APIClient().post("/api/auth/login/", {"email": "c@a.ph", "password": "Wrong123!"}, format="json")
        self.assertEqual(wrong.status_code, 401)
        self.assertEqual(str(wrong.data["detail"]), "Incorrect email or password.")
        self.assertNotIn("support_email", wrong.data)

    def test_cannot_deactivate_yourself(self):
        resp = self.api.post(f"/api/admin/users/{self.admin.id}/deactivate/", {"reason": "Testing self-deactivation."}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(self.api.patch(f"/api/admin/users/{self.admin.id}/toggle-active/").status_code, 400)

    def test_send_password_reset(self):
        resp = self.api.post(f"/api/admin/users/{self.client_user.id}/send-password-reset/")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(PasswordResetCode.objects.filter(user=self.client_user).exists())
        self.assertIn("password reset", mail.outbox[-1].subject.lower())
        self.assertTrue(AuditLog.objects.filter(action="user.password_reset_sent").exists())

    def test_non_admins_are_refused(self):
        other = APIClient()
        other.force_authenticate(self.client_user)
        self.assertEqual(other.get(f"/api/admin/users/{self.client_user.id}/overview/").status_code, 403)
        self.assertEqual(other.post(f"/api/admin/users/{self.admin.id}/deactivate/", {"reason": "x" * 20}).status_code, 403)

    def test_commission_setting_is_validated_and_logged(self):
        SystemSetting.objects.update_or_create(key="platform_commission_pct", defaults={"value": "10.00"})
        url = "/api/admin/settings/platform_commission_pct/"
        self.assertEqual(self.api.patch(url, {"value": "abc"}, format="json").status_code, 400)
        self.assertEqual(self.api.patch(url, {"value": "80"}, format="json").status_code, 400)
        ok = self.api.patch(url, {"value": "12.5"}, format="json")
        self.assertEqual(ok.status_code, 200, ok.data)
        log = AuditLog.objects.get(action="setting.updated")
        self.assertEqual((log.old_values, log.new_values), ({"platform_commission_pct": "10.00"}, {"platform_commission_pct": "12.50"}))
