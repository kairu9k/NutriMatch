import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from profiles.models import ClientProfile, RndProfile
from scheduling.models import RndClientRelationship

from .models import NcpRecord, PreConsultationScreening
from .services import (
    calculate_bmi,
    calculate_bmr_mifflin_st_jeor,
    calculate_nrs2002,
    calculate_tdee,
    classify_bmi_asia_pacific,
)


def _make_rnd(email="rnd@t.ph"):
    user = User.objects.create_user(email=email, password="x", role="rnd", first_name="R", last_name="D")
    RndProfile.objects.create(user=user, prc_license_number=f"PRC-{email}")
    return user


def _make_client(email="client@t.ph", dob=None, sex="male"):
    user = User.objects.create_user(email=email, password="x", role="client", first_name="C", last_name="L")
    ClientProfile.objects.create(user=user, date_of_birth=dob or datetime.date(1995, 6, 15), sex=sex)
    return user


class CalculationEngineTests(TestCase):
    """Hand-checked values against the capstone proposal's named formulas —
    do not loosen these without re-checking vault/C1-NUTRIMATCH-FINALv5.pdf."""

    def test_bmi_calculation(self):
        bmi = calculate_bmi(Decimal("70"), Decimal("170"))
        self.assertEqual(bmi, Decimal("24.22"))

    def test_bmi_classification_asia_pacific_thresholds(self):
        # Asia-Pacific cutoffs are lower than standard global WHO cutoffs —
        # 24.22 must land in "Overweight (At Risk)", not "Normal".
        self.assertEqual(classify_bmi_asia_pacific(Decimal("18.4")), "Underweight")
        self.assertEqual(classify_bmi_asia_pacific(Decimal("22.9")), "Normal")
        self.assertEqual(classify_bmi_asia_pacific(Decimal("24.22")), "Overweight (At Risk)")
        self.assertEqual(classify_bmi_asia_pacific(Decimal("27.0")), "Obese I")
        self.assertEqual(classify_bmi_asia_pacific(Decimal("31.0")), "Obese II")

    def test_bmr_mifflin_st_jeor_male(self):
        bmr = calculate_bmr_mifflin_st_jeor(Decimal("70"), Decimal("170"), 31, "male")
        self.assertEqual(bmr, Decimal("1612.50"))

    def test_bmr_mifflin_st_jeor_female(self):
        # Same inputs, female offset is -161 instead of +5 -> 166 lower.
        bmr = calculate_bmr_mifflin_st_jeor(Decimal("70"), Decimal("170"), 31, "female")
        self.assertEqual(bmr, Decimal("1446.50"))

    def test_tdee_applies_activity_factor(self):
        bmr = Decimal("1612.50")
        self.assertEqual(calculate_tdee(bmr, "moderately_active"), Decimal("2499.38"))
        self.assertEqual(calculate_tdee(bmr, "sedentary"), Decimal("1935.00"))

    def test_nrs2002_no_risk_factors(self):
        score, risk = calculate_nrs2002(bmi=Decimal("22"))
        self.assertEqual((score, risk), (0, "no_risk"))

    def test_nrs2002_underweight_scores_high(self):
        score, risk = calculate_nrs2002(bmi=Decimal("17"))
        self.assertEqual((score, risk), (3, "at_risk"))

    def test_nrs2002_weight_loss_plus_disease_severity_is_high_risk(self):
        score, risk = calculate_nrs2002(bmi=Decimal("22"), weight_loss_pct=Decimal("14.3"), severity_of_disease_points=3)
        self.assertEqual((score, risk), (5, "high_risk"))


class ScreeningViewTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.client_user = _make_client()

    def test_screening_computes_all_derived_fields(self):
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.post("/api/client/screening/", {
            "height_cm": "170", "weight_kg": "70", "activity_level": "moderately_active",
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["bmi"], "24.22")
        self.assertEqual(resp.data["bmi_category"], "Overweight (At Risk)")
        self.assertEqual(resp.data["bmr_kcal"], "1612.50")
        self.assertEqual(resp.data["tdee_kcal"], "2499.38")
        self.assertEqual(resp.data["nrs_score"], 0)
        self.assertEqual(resp.data["nrs_risk"], "no_risk")

    def test_weight_loss_is_derived_from_prior_screening_not_self_reported(self):
        self.client_api.force_authenticate(self.client_user)
        self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "70"})
        resp = self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "60"})

        # 70 -> 60 is a ~14.3% drop, well over the 5% NRS-2002 threshold
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertGreaterEqual(resp.data["nrs_score"], 2)

    def test_screening_without_dob_skips_bmr_tdee(self):
        bare_client = User.objects.create_user(email="bare@t.ph", password="x", role="client", first_name="B", last_name="C")
        self.client_api.force_authenticate(bare_client)
        resp = self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "70"})

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertIsNotNone(resp.data["bmi"])
        self.assertIsNone(resp.data["bmr_kcal"])
        self.assertIsNone(resp.data["tdee_kcal"])

    def test_latest_screening_returns_most_recent(self):
        self.client_api.force_authenticate(self.client_user)
        self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "70"})
        self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "68"})

        resp = self.client_api.get("/api/client/screening/latest/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["weight_kg"], "68.00")

    def test_latest_screening_404_when_none_exist(self):
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.get("/api/client/screening/latest/")
        self.assertEqual(resp.status_code, 404)


class NcpRecordLifecycleTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")

    def test_rnd_can_create_draft_ncp_record(self):
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.post(f"/api/rnd/relationships/{self.rel.id}/ncp/", {
            "relationship": self.rel.id, "encounter_date": str(timezone.now().date()),
            "weight_kg": "70", "height_cm": "170",
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["status"], "draft")
        # bmi is always server-computed, never trusts client input
        self.assertEqual(resp.data["bmi"], "24.22")

    def test_other_rnd_cannot_create_ncp_for_relationship_not_theirs(self):
        other_rnd = _make_rnd(email="other@t.ph")
        self.client_api.force_authenticate(other_rnd)
        resp = self.client_api.post(f"/api/rnd/relationships/{self.rel.id}/ncp/", {
            "relationship": self.rel.id, "encounter_date": str(timezone.now().date()),
        })
        self.assertEqual(resp.status_code, 400)

    def test_bmi_recomputed_on_update_when_weight_changes(self):
        record = NcpRecord.objects.create(
            relationship=self.rel, encounter_date=timezone.now().date(),
            weight_kg=Decimal("70"), height_cm=Decimal("170"), bmi=Decimal("24.22"),
        )
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.patch(f"/api/rnd/ncp/{record.id}/", {"weight_kg": "80"})

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["bmi"], "27.68")

    def test_finalize_requires_the_owning_rnd(self):
        record = NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date())
        other_rnd = _make_rnd(email="other2@t.ph")
        self.client_api.force_authenticate(other_rnd)

        resp = self.client_api.patch(f"/api/rnd/ncp/{record.id}/finalize/")
        self.assertEqual(resp.status_code, 404)

    def test_finalize_sets_status_completed(self):
        record = NcpRecord.objects.create(
            relationship=self.rel, encounter_date=timezone.now().date(),
            weight_kg=Decimal("70"), height_cm=Decimal("170"),
            pes_problem="Inadequate intake", diet_prescription="1800 kcal exchange diet",
        )
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.patch(f"/api/rnd/ncp/{record.id}/finalize/")

        self.assertEqual(resp.status_code, 200, resp.data)
        record.refresh_from_db()
        self.assertEqual(record.status, "completed")

    def test_list_is_scoped_to_relationship_and_ordered_newest_first(self):
        NcpRecord.objects.create(relationship=self.rel, encounter_date="2026-01-01")
        newer = NcpRecord.objects.create(relationship=self.rel, encounter_date="2026-06-01")
        other_rel = RndClientRelationship.objects.create(
            rnd=self.rnd, client=_make_client(email="other-client@t.ph"), status="active"
        )
        NcpRecord.objects.create(relationship=other_rel, encounter_date="2026-06-01")

        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.get(f"/api/rnd/relationships/{self.rel.id}/ncp/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)
        self.assertEqual(resp.data[0]["id"], newer.id)


class NcpDraftListViewTests(TestCase):
    """Cross-patient draft list for the RND dashboard's Overview tab."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()

    def test_only_returns_this_rnds_drafts(self):
        client_a = _make_client(email="a@t.ph")
        client_b = _make_client(email="b@t.ph")
        rel_a = RndClientRelationship.objects.create(rnd=self.rnd, client=client_a, status="active")
        rel_b = RndClientRelationship.objects.create(rnd=self.rnd, client=client_b, status="active")

        other_rnd = _make_rnd(email="other@t.ph")
        other_rel = RndClientRelationship.objects.create(rnd=other_rnd, client=_make_client(email="c@t.ph"), status="active")

        NcpRecord.objects.create(relationship=rel_a, encounter_date=timezone.now().date(), status="draft")
        NcpRecord.objects.create(relationship=rel_b, encounter_date=timezone.now().date(), status="completed")
        NcpRecord.objects.create(relationship=other_rel, encounter_date=timezone.now().date(), status="draft")

        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.get("/api/rnd/ncp/drafts/")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]["client_name"], "C L")
