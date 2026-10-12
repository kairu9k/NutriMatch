"""Adding admins (invite, no emailed password) and changing your own password."""

from django.core import mail
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import AuditLog
from core.test_utils import onboard_client

from .models import User

GOOD = "NewPass#2026"


class AdminAccountTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="a@x.ph", password="OldPass#2026", role="admin", first_name="Ada", last_name="Min")
        self.api = APIClient()
        self.api.force_authenticate(self.admin)

    def test_add_admin_sends_invite_without_password(self):
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.api.post("/api/admin/admins/", {"first_name": "bea", "last_name": "reyes", "email": "Bea@X.ph",
                                                        "reason": "Second admin for the weekend shift"}, format="json")
        self.assertEqual(resp.status_code, 201, resp.data)
        new = User.objects.get(email="bea@x.ph")
        self.assertEqual((new.role, new.first_name), ("admin", "Bea"))
        self.assertIsNotNone(new.email_verified_at)
        self.assertFalse(new.has_usable_password())
        self.assertTrue(AuditLog.objects.filter(action="admin.created", record_id=new.pk).exists())
        self.assertEqual(mail.outbox[0].to, ["bea@x.ph"])
        self.assertIn("forgot-password", mail.outbox[0].body)
        # Can't sign in until a password is set.
        self.assertEqual(APIClient().post("/api/auth/login/", {"email": "bea@x.ph", "password": ""}, format="json").status_code // 100, 4)

    def test_add_admin_rules(self):
        self.assertEqual(self.api.post("/api/admin/admins/", {"first_name": "Bea", "last_name": "Reyes", "email": "a@x.ph", "reason": "x" * 12}, format="json").status_code, 400)
        self.assertEqual(self.api.post("/api/admin/admins/", {"first_name": "Bea", "last_name": "Reyes", "email": "b@x.ph", "reason": "short"}, format="json").status_code, 400)
        client = APIClient()
        client.force_authenticate(onboard_client(User.objects.create_user(email="c@x.ph", password="x", role="client", first_name="C", last_name="C")))
        self.assertEqual(client.post("/api/admin/admins/", {"first_name": "Bea", "last_name": "Reyes", "email": "b@x.ph", "reason": "x" * 12}, format="json").status_code, 403)

    def test_change_password(self):
        bad = self.api.post("/api/auth/me/password/", {"current_password": "wrong", "new_password": GOOD}, format="json")
        self.assertIn("current_password", bad.data)
        weak = self.api.post("/api/auth/me/password/", {"current_password": "OldPass#2026", "new_password": "password"}, format="json")
        self.assertIn("new_password", weak.data)
        ok = self.api.post("/api/auth/me/password/", {"current_password": "OldPass#2026", "new_password": GOOD}, format="json")
        self.assertEqual(ok.status_code, 200, ok.data)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password(GOOD))
        self.assertTrue(AuditLog.objects.filter(action="password.changed", record_id=self.admin.pk).exists())
        self.assertEqual(mail.outbox[-1].to, ["a@x.ph"])
