"""Find an RND / RND profile page: public data only, open slots, filters,
clinic address."""

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import Appointment, Review, RndClientRelationship

from .models import RndAvailabilitySchedule, RndProfile
from .public import next_open_slots


class PublicRndTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(
            email="maria@p.ph", password="x", role="rnd", first_name="Maria", last_name="Santos", phone="09170000000"))
        RndProfile.objects.filter(user=self.rnd).update(
            consultation_fee=Decimal("800"), consultation_modes=["video", "in_person"],
            clinic_address="Unit 2, Bajada Medical Bldg, J.P. Laurel Ave, Davao City", prc_license_number="0123456")
        self.client_user = onboard_client(User.objects.create_user(email="ana@p.ph", password="x", role="client", first_name="Ana", last_name="Cruz"))
        self.api = APIClient()
        self.api.force_authenticate(self.client_user)

    def test_no_private_fields(self):
        row = self.api.get("/api/client/rnds/").data[0]
        self.assertEqual(set(row["user"]), {"id", "first_name", "last_name", "profile_photo"})
        text = str(row)
        self.assertNotIn("maria@p.ph", text)
        self.assertNotIn("09170000000", text)
        self.assertEqual(row["prc_license_number"], "0123456")  # public PRC registry info
        self.assertIn("Davao City", row["clinic_address"])
        detail = self.api.get(f"/api/client/rnds/{self.rnd.id}/").data
        self.assertNotIn("maria@p.ph", str(detail))
        self.assertEqual(set(detail["rating_breakdown"]), {"5", "4", "3", "2", "1"})

    def test_stats_and_my_rnd(self):
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        appt = Appointment.objects.create(relationship=rel, type="video", status="completed", scheduled_at=timezone.now() - timedelta(days=3))
        Review.objects.create(appointment=appt, client=self.client_user, rnd=self.rnd, rating=5, comment="Great")
        d = self.api.get(f"/api/client/rnds/{self.rnd.id}/").data
        self.assertEqual((d["consultations_completed"], d["active_patients"], d["review_count"], d["average_rating"]), (1, 1, 1, 5.0))
        self.assertEqual(d["rating_breakdown"]["5"], 1)
        self.assertTrue(d["is_my_rnd"])

    def test_next_open_slots_skip_booked_and_past(self):
        from scheduling.serializers import PH_TZ

        RndAvailabilitySchedule.objects.filter(rnd=self.rnd).delete()
        now = datetime(2026, 10, 12, 9, 30, tzinfo=PH_TZ)  # a Monday, 9:30 AM
        RndAvailabilitySchedule.objects.create(rnd=self.rnd, day_of_week=1, start_time=time(9), end_time=time(12),
                                               effective_from=now.date() - timedelta(days=30))
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        Appointment.objects.create(relationship=rel, type="video", status="confirmed", duration_minutes=60,
                                   scheduled_at=datetime(2026, 10, 12, 10, 0, tzinfo=PH_TZ))
        slots = next_open_slots(self.rnd.id, count=3, now=now)
        # 15-minute steps: 9:00–9:30 have passed, 9:45–10:45 overlap the 10:00
        # booking → 11:00 today, then next Monday 9:00 and 9:15
        self.assertEqual([datetime.fromisoformat(s).astimezone(PH_TZ).strftime("%m-%d %H:%M") for s in slots],
                         ["10-12 11:00", "10-19 09:00", "10-19 09:15"])
        # A start less than 10 minutes away isn't offered (8:55 → 9:00 skipped).
        early = next_open_slots(self.rnd.id, count=1, now=datetime(2026, 10, 19, 8, 55, tzinfo=PH_TZ))
        self.assertEqual(datetime.fromisoformat(early[0]).astimezone(PH_TZ).strftime("%H:%M"), "09:15")

    def test_search_by_name_and_max_fee(self):
        other = approve_rnd(User.objects.create_user(email="jose@p.ph", password="x", role="rnd", first_name="Jose", last_name="Reyes"))
        RndProfile.objects.filter(user=other).update(consultation_fee=Decimal("1500"))
        names = lambda q: sorted(r["user"]["first_name"] for r in self.api.get(f"/api/client/rnds/{q}").data)
        self.assertEqual(names("?search=santos"), ["Maria"])
        self.assertEqual(names("?max_fee=1000"), ["Maria"])
        self.assertEqual(names(""), ["Jose", "Maria"])

    def test_options_only_list_what_findable_rnds_have(self):
        from profiles.models import RndLanguage

        RndProfile.objects.filter(user=self.rnd).update(specialization="Diabetes Management")
        RndLanguage.objects.create(rnd=self.rnd, language_code="ceb", language_name="Cebuano")
        hidden = approve_rnd(User.objects.create_user(email="h@p.ph", password="x", role="rnd", first_name="H", last_name="D"))
        RndProfile.objects.filter(user=hidden).update(specialization="Sports Nutrition", available_for_new_clients=False, consultation_modes=["chat"])
        RndLanguage.objects.create(rnd=hidden, language_code="ilo", language_name="Ilocano")

        data = self.api.get("/api/client/rnds/options/").data
        self.assertEqual(data["specializations"], ["Diabetes Management"])
        self.assertEqual([lang["code"] for lang in data["languages"]], ["ceb"])
        self.assertEqual([m["value"] for m in data["modes"]], ["video", "in_person"])


class ClinicAddressTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@a.ph", password="x", role="rnd", first_name="R", last_name="D"))
        RndProfile.objects.filter(user=self.rnd).update(consultation_modes=["video"], clinic_address=None)
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)

    def test_in_person_needs_an_address(self):
        resp = self.api.patch("/api/rnd/profile/", {"consultation_modes": ["video", "in_person"]}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("clinic_address", resp.data)
        self.assertEqual(self.api.patch("/api/rnd/profile/", {"consultation_modes": ["video", "in_person"], "clinic_address": "Davao"}, format="json").status_code, 400)
        ok = self.api.patch("/api/rnd/profile/", {"consultation_modes": ["video", "in_person"],
                                                  "clinic_address": "2F Bajada Bldg, J.P. Laurel Ave, Davao City"}, format="json")
        self.assertEqual(ok.status_code, 200, ok.data)
        self.assertIn("Bajada", ok.data["clinic_address"])

    def test_unrelated_edit_isnt_blocked(self):
        RndProfile.objects.filter(user=self.rnd).update(consultation_modes=["video", "in_person"])
        self.assertEqual(self.api.patch("/api/rnd/profile/", {"languages": ["en"]}, format="json").status_code, 200)

    def test_in_person_booking_needs_address(self):
        RndProfile.objects.filter(user=self.rnd).update(consultation_modes=["video", "in_person"])
        client = onboard_client(User.objects.create_user(email="c@a.ph", password="x", role="client", first_name="C", last_name="L"))
        from clinical.models import PreConsultationScreening

        PreConsultationScreening.objects.create(client=client, height_cm=Decimal("160"), weight_kg=Decimal("60"))
        api = APIClient()
        api.force_authenticate(client)
        slot = next_open_slots(self.rnd.id, count=1)[0]
        resp = api.post("/api/client/appointments/", {"rnd_id": self.rnd.id, "scheduled_at": slot, "type": "in_person",
                                                      "duration_minutes": 60}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("clinic address", str(resp.data))
