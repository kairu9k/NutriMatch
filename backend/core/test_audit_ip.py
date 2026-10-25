"""Every audit row made during a request records the client's IP and browser
(core/request_context.py), even when the code writing it didn't pass them."""

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from core.models import AuditLog
from core.test_utils import onboard_client


class AuditIpTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@a.ph", password="x", role="admin", first_name="A", last_name="D")
        self.client_user = onboard_client(User.objects.create_user(email="c@a.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.api = APIClient()
        self.api.force_authenticate(self.admin)

    def _reset(self, **meta):
        # writes user.password_reset_sent, which used to be saved without an IP
        resp = self.api.post(f"/api/admin/users/{self.client_user.id}/send-password-reset/", **meta)
        self.assertLess(resp.status_code, 300, resp.data)
        return AuditLog.objects.filter(action="user.password_reset_sent").latest("id")

    def test_ip_and_browser_are_recorded(self):
        log = self._reset(REMOTE_ADDR="203.0.113.7", HTTP_USER_AGENT="TestBrowser/1.0")
        self.assertEqual((log.ip_address, log.user_agent), ("203.0.113.7", "TestBrowser/1.0"))

    def test_behind_a_proxy_the_forwarded_client_ip_is_kept(self):
        log = self._reset(REMOTE_ADDR="10.0.0.5", HTTP_X_FORWARDED_FOR="198.51.100.20, 10.0.0.5")
        self.assertEqual(log.ip_address, "198.51.100.20")

    def test_rows_made_outside_a_request_stay_empty(self):
        log = AuditLog.objects.create(action="audit_log.reset")
        self.assertIsNone(log.ip_address)
