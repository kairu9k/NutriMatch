from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from scheduling.models import RndClientRelationship

from .models import RndProfile


def _make_rnd(email="rnd@t.ph", fee="500.00"):
    user = User.objects.create_user(email=email, password="x", role="rnd", first_name="R", last_name="D")
    RndProfile.objects.create(
        user=user, prc_license_number=f"PRC-{email}", consultation_fee=Decimal(fee),
        is_verified=True, available_for_new_clients=True,
    )
    return user


def _make_client(email="client@t.ph"):
    return User.objects.create_user(email=email, password="x", role="client", first_name="C", last_name="L")


class RndSearchRelationshipStatusTests(TestCase):
    """GET /client/rnds/ must reflect real relationship state — Find an RND
    previously never checked this at all, always showing "Request" even
    for RNDs the client already had a pending/active relationship with."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.client_api.force_authenticate(self.client_user)

    def test_no_relationship_returns_null_status(self):
        resp = self.client_api.get("/api/client/rnds/")

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data[0]["relationship_status"])

    def test_pending_relationship_status_is_real(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="pending")
        resp = self.client_api.get("/api/client/rnds/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]["relationship_status"], "pending")

    def test_active_relationship_status_is_real(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        resp = self.client_api.get("/api/client/rnds/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data[0]["relationship_status"], "active")

    def test_status_scoped_to_requesting_client_only(self):
        RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        other_client = _make_client(email="other@t.ph")
        self.client_api.force_authenticate(other_client)

        resp = self.client_api.get("/api/client/rnds/")

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data[0]["relationship_status"])

    def test_rnd_viewing_public_profile_gets_null_status_not_error(self):
        other_rnd = _make_rnd(email="other-rnd@t.ph")
        self.client_api.force_authenticate(other_rnd)

        resp = self.client_api.get(f"/api/client/rnds/{self.rnd.id}/")

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data["relationship_status"])
