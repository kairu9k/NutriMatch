from datetime import timedelta

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.public_stats import CACHE_KEY
from core.test_utils import approve_rnd
from profiles.models import RndProfile
from scheduling.models import Appointment, RndClientRelationship


class PublicLandingStatsTests(TestCase):
    def setUp(self):
        cache.delete(CACHE_KEY)
        self.addCleanup(cache.delete, CACHE_KEY)
        self.rnd = approve_rnd(User.objects.create_user(email="r1@t.ph", password="x", role="rnd", first_name="R", last_name="One"))
        self.client_a = User.objects.create_user(email="a@t.ph", password="x", role="client", first_name="A", last_name="C")
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_a, status="active")

    def _book(self, status, relationship=None):
        return Appointment.objects.create(
            relationship=relationship or self.rel, scheduled_at=timezone.now() - timedelta(days=2),
            duration_minutes=60, type="video", status=status,
        )

    def _stats(self):
        cache.delete(CACHE_KEY)
        resp = APIClient().get("/api/public/stats/")
        self.assertEqual(resp.status_code, 200)
        return resp.data

    def test_only_two_totals_and_no_sign_in_needed(self):
        self.assertEqual(set(self._stats()), {"verified_rnds", "clients_served"})

    def test_an_expired_token_does_not_break_it(self):
        api = APIClient(HTTP_AUTHORIZATION="Bearer not-a-real-token")
        self.assertEqual(api.get("/api/public/stats/").status_code, 200)

    def test_verified_rnds_counts_only_approved_active_accounts(self):
        self.assertEqual(self._stats()["verified_rnds"], 1)
        pending = User.objects.create_user(email="r2@t.ph", password="x", role="rnd", first_name="R", last_name="Two")
        RndProfile.objects.create(user=pending, prc_license_number="P2")
        self.assertEqual(self._stats()["verified_rnds"], 1)
        User.objects.filter(pk=self.rnd.pk).update(is_active=False)
        self.assertEqual(self._stats()["verified_rnds"], 0)

    def test_clients_served_needs_a_completed_consultation_and_counts_people(self):
        self.assertEqual(self._stats()["clients_served"], 0)
        self._book(Appointment.Status.CONFIRMED)
        self._book(Appointment.Status.NO_SHOW)
        self.assertEqual(self._stats()["clients_served"], 0)
        self._book(Appointment.Status.COMPLETED)
        self._book(Appointment.Status.COMPLETED)  # same person twice
        self.assertEqual(self._stats()["clients_served"], 1)
