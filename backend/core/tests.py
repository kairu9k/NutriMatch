from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User

from .models import AuditLog, SystemSetting


def _make_admin(email="admin@t.ph"):
    return User.objects.create_user(email=email, password="x", role="admin", first_name="Ad", last_name="Min")


class AdminAuditLogListViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.admin = _make_admin()
        self.client_api.force_authenticate(self.admin)

    def test_non_admin_cannot_access(self):
        client = User.objects.create_user(email="c@t.ph", password="x", role="client", first_name="C", last_name="L")
        self.client_api.force_authenticate(client)
        resp = self.client_api.get("/api/admin/audit-logs/")
        self.assertEqual(resp.status_code, 403)

    def test_lists_real_rows_newest_first(self):
        AuditLog.objects.create(action="invoice.paid", table_name="invoices", record_id=1)
        AuditLog.objects.create(action="user.deactivated", table_name="users", record_id=2)

        resp = self.client_api.get("/api/admin/audit-logs/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)
        self.assertEqual(resp.data[0]["action"], "user.deactivated")

    def test_search_filters_by_action(self):
        AuditLog.objects.create(action="invoice.paid")
        AuditLog.objects.create(action="login.failed")

        resp = self.client_api.get("/api/admin/audit-logs/?search=invoice")
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["action"], "invoice.paid")

    def test_no_write_or_delete_endpoint_exists(self):
        # AuditLog is append-only by design (RA 10173) — there is no
        # PATCH/DELETE route to try; POST to the list endpoint should
        # 405 since it's ListAPIView only.
        resp = self.client_api.post("/api/admin/audit-logs/", {"action": "fake"})
        self.assertEqual(resp.status_code, 405)


class AdminSystemSettingViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.admin = _make_admin()
        self.client_api.force_authenticate(self.admin)
        self.setting = SystemSetting.objects.create(
            key="platform_commission_pct", value="10.00", description="Commission %"
        )

    def test_list_returns_real_settings(self):
        resp = self.client_api.get("/api/admin/settings/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]["key"], "platform_commission_pct")

    def test_update_by_key_changes_value_and_tracks_updated_by(self):
        resp = self.client_api.patch("/api/admin/settings/platform_commission_pct/", {"value": "15.00"})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.value, "15.00")
        self.assertEqual(self.setting.updated_by, self.admin)

    def test_update_unknown_key_404s(self):
        resp = self.client_api.patch("/api/admin/settings/does_not_exist/", {"value": "x"})
        self.assertEqual(resp.status_code, 404)

    def test_key_itself_is_not_editable(self):
        resp = self.client_api.patch("/api/admin/settings/platform_commission_pct/", {
            "value": "15.00", "key": "renamed_key",
        })
        self.assertEqual(resp.status_code, 200)
        self.setting.refresh_from_db()
        self.assertEqual(self.setting.key, "platform_commission_pct")
