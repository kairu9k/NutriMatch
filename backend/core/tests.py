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
        self.assertEqual(resp.data["count"], 2)
        self.assertEqual(resp.data["results"][0]["action"], "user.deactivated")

    def test_search_filters_by_action(self):
        AuditLog.objects.create(action="invoice.paid")
        AuditLog.objects.create(action="login.failed")

        resp = self.client_api.get("/api/admin/audit-logs/?search=invoice")
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["action"], "invoice.paid")

    def test_search_by_person_and_paging(self):
        other = User.objects.create_user(email="maria@t.ph", password="x", role="rnd", first_name="Maria", last_name="Santos")
        for _ in range(55):
            AuditLog.objects.create(user=other, action="payout_account.updated")
        AuditLog.objects.create(user=self.admin, action="setting.updated")
        first = self.client_api.get("/api/admin/audit-logs/?search=maria santos").data
        self.assertEqual((first["count"], len(first["results"])), (55, 50))
        self.assertIsNotNone(first["next"])
        self.assertEqual(len(self.client_api.get("/api/admin/audit-logs/?search=maria&page=2").data["results"]), 5)
        self.assertEqual(self.client_api.get(f"/api/admin/audit-logs/?user={self.admin.id}").data["count"], 1)

    def test_date_range_uses_philippine_days(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo

        ph = ZoneInfo("Asia/Manila")
        early = AuditLog.objects.create(action="invoice.paid")
        late = AuditLog.objects.create(action="invoice.refunded")
        # 11:30 PM Oct 9 and 12:30 AM Oct 10, Philippine time
        AuditLog.objects.filter(pk=early.pk).update(created_at=datetime(2026, 10, 9, 23, 30, tzinfo=ph))
        AuditLog.objects.filter(pk=late.pk).update(created_at=datetime(2026, 10, 10, 0, 30, tzinfo=ph))
        day = self.client_api.get("/api/admin/audit-logs/?date_from=2026-10-10&date_to=2026-10-10").data
        self.assertEqual([r["action"] for r in day["results"]], ["invoice.refunded"])
        both = self.client_api.get("/api/admin/audit-logs/?date_from=2026-10-09&date_to=2026-10-10").data
        self.assertEqual(both["count"], 2)

    def test_admin_scope_hides_routine_rows(self):
        client = User.objects.create_user(email="c2@t.ph", password="x", role="client", first_name="C", last_name="L")
        AuditLog.objects.create(user=client, action="consent.given")
        AuditLog.objects.create(user=self.admin, action="client.record_viewed")
        AuditLog.objects.create(user=client, action="payout_account.updated")
        AuditLog.objects.create(user=self.admin, action="rnd.approved")
        rows = self.client_api.get("/api/admin/audit-logs/?scope=admin").data["results"]
        self.assertEqual([r["action"] for r in rows], ["rnd.approved"])

    def test_actions_facet(self):
        AuditLog.objects.create(action="invoice.paid")
        AuditLog.objects.create(action="invoice.paid")
        AuditLog.objects.create(action="login.failed")
        data = self.client_api.get("/api/admin/audit-logs/actions/").data
        self.assertEqual({r["action"]: r["count"] for r in data}, {"invoice.paid": 2, "login.failed": 1})

    def test_csv_export_is_filtered_and_audit_logged(self):
        AuditLog.objects.create(user=self.admin, action="setting.updated", new_values={"platform_commission_pct": "12.00"})
        AuditLog.objects.create(action="login.failed")
        resp = self.client_api.get("/api/admin/audit-logs/export/?action=setting.updated")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp["Content-Type"])
        self.assertIn("attachment;", resp["Content-Disposition"])
        body = resp.content.decode("utf-8-sig")
        lines = body.strip().splitlines()
        self.assertEqual(len(lines), 2)  # header + 1 row
        self.assertIn("System setting changed", lines[1])
        self.assertNotIn("Failed sign-in", body)
        log = AuditLog.objects.get(action="audit_log.exported")
        self.assertEqual((log.user, log.new_values["rows"], log.new_values["action"]), (self.admin, 1, "setting.updated"))

    def test_csv_export_admin_only(self):
        client = User.objects.create_user(email="c3@t.ph", password="x", role="client", first_name="C", last_name="L")
        self.client_api.force_authenticate(client)
        self.assertEqual(self.client_api.get("/api/admin/audit-logs/export/").status_code, 403)

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
