"""Admins correct user details: validation, audit row with old → new, emails."""

from django.core import mail
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import AuditLog
from core.test_utils import approve_rnd, onboard_client

from .models import User


class AdminUserEditTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="a@e.ph", password="x", role="admin", first_name="Ada", last_name="Min")
        self.client_user = onboard_client(User.objects.create_user(email="c@e.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.rnd = approve_rnd(User.objects.create_user(email="r@e.ph", password="x", role="rnd", first_name="Maria", last_name="Santos"))
        self.api = APIClient()
        self.api.force_authenticate(self.admin)

    def edit(self, user, **data):
        return self.api.patch(f"/api/admin/users/{user.pk}/edit/", {"reason": "Typo reported by the user", **data}, format="json")

    def test_edit_name_and_email_is_audited_and_emailed(self):
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.edit(self.client_user, first_name="ana marie", email="Ana.New@E.ph", phone="0917 123 4567")
        self.assertEqual(resp.status_code, 200, resp.data)
        u = User.objects.get(pk=self.client_user.pk)
        self.assertEqual((u.first_name, u.email, u.phone), ("Ana Marie", "ana.new@e.ph", "+639171234567"))
        log = AuditLog.objects.get(action="user.updated", record_id=u.pk)
        self.assertEqual(log.old_values["email"], "c@e.ph")
        self.assertEqual(log.new_values["email"], "ana.new@e.ph")
        self.assertEqual(log.new_values["reason"], "Typo reported by the user")
        self.assertNotIn("last_name", log.new_values)  # only what changed
        # Both the new and the old address are told.
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ["ana.new@e.ph", "c@e.ph"])

    def test_rnd_license_and_specialization(self):
        from profiles.models import RND_SPECIALIZATIONS

        resp = self.edit(self.rnd, prc_license_number="1234567", specialization=RND_SPECIALIZATIONS[0])
        self.assertEqual(resp.status_code, 200, resp.data)
        self.rnd.rnd_profile.refresh_from_db()
        self.assertEqual(self.rnd.rnd_profile.prc_license_number, "1234567")
        self.assertEqual(self.edit(self.rnd, prc_license_number="12345").status_code, 400)
        self.assertEqual(self.edit(self.rnd, specialization="Astrology").status_code, 400)
        self.assertEqual(self.edit(self.client_user, prc_license_number="7654321").status_code, 400)

    def test_rules(self):
        self.assertEqual(self.edit(self.client_user, email="r@e.ph").status_code, 400)  # taken
        self.assertEqual(self.edit(self.client_user, first_name="Ana2").status_code, 400)
        self.assertEqual(self.edit(self.client_user, phone="call me").status_code, 400)
        self.assertEqual(self.api.patch(f"/api/admin/users/{self.client_user.pk}/edit/", {"first_name": "Anna", "reason": "short"}, format="json").status_code, 400)
        self.assertEqual(self.edit(self.client_user, first_name="Ana").data["detail"], "Nothing changed.")
        self.assertEqual(self.edit(self.admin, first_name="Adah").status_code, 400)  # not themselves
        other = APIClient()
        other.force_authenticate(self.client_user)
        self.assertEqual(other.patch(f"/api/admin/users/{self.rnd.pk}/edit/", {"first_name": "X", "reason": "x" * 12}, format="json").status_code, 403)
