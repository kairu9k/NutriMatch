import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd
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
    return approve_rnd(user)


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

    def test_screening_is_taken_once_then_read_only(self):
        # It's the baseline for weight/BMI change; new readings go in the Progress Tracker.
        self.client_api.force_authenticate(self.client_user)
        first = self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "70"})
        again = self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "60"})

        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(again.status_code, 400)
        self.assertIn("Progress Tracker", again.data["detail"])
        self.assertEqual(PreConsultationScreening.objects.filter(client=self.client_user).count(), 1)

    def test_screening_without_dob_skips_bmr_tdee(self):
        bare_client = User.objects.create_user(email="bare@t.ph", password="x", role="client", first_name="B", last_name="C")
        self.client_api.force_authenticate(bare_client)
        resp = self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "70"})

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertIsNotNone(resp.data["bmi"])
        self.assertIsNone(resp.data["bmr_kcal"])
        self.assertIsNone(resp.data["tdee_kcal"])

    def test_submitted_age_and_sex_used_when_profile_lacks_them(self):
        bare_client = User.objects.create_user(email="bare2@t.ph", password="x", role="client", first_name="B", last_name="C")
        ClientProfile.objects.create(user=bare_client)
        self.client_api.force_authenticate(bare_client)

        # Hand-checked: 10*90 + 6.25*172 - 5*31 + 5 = 1825; x1.375 = 2509.375
        resp = self.client_api.post("/api/client/screening/", {
            "height_cm": "172", "weight_kg": "90", "age": 31, "sex": "male", "activity_level": "lightly_active",
        })

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["bmr_kcal"], "1825.00")
        self.assertEqual(resp.data["tdee_kcal"], "2509.38")
        self.assertEqual(resp.data["bmi_category"], "Obese II")
        self.assertNotIn("age", resp.data)
        bare_client.client_profile.refresh_from_db()
        self.assertEqual(bare_client.client_profile.sex, "male")

    def test_profile_dob_wins_over_submitted_age(self):
        self.client_api.force_authenticate(self.client_user)
        from_dob = self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "70", "sex": "male"})
        PreConsultationScreening.objects.filter(client=self.client_user).delete()  # one screening per client
        typed = self.client_api.post("/api/client/screening/", {
            "height_cm": "170", "weight_kg": "70", "age": 40, "sex": "male",
        })

        # The age field is read-only in the form when a DOB is on file; a
        # tampered request can't change the BMR either.
        self.assertEqual(typed.status_code, 201, typed.data)
        self.assertEqual(typed.data["bmr_kcal"], from_dob.data["bmr_kcal"])

    def test_profile_sex_wins_over_submitted_sex(self):
        self.client_api.force_authenticate(self.client_user)
        profile = self.client_user.client_profile
        on_file = profile.sex
        other = "female" if on_file == "male" else "male"
        from_profile = self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "70"})
        PreConsultationScreening.objects.filter(client=self.client_user).delete()  # one screening per client
        typed = self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "70", "sex": other})

        self.assertEqual(typed.status_code, 201, typed.data)
        self.assertEqual(typed.data["bmr_kcal"], from_profile.data["bmr_kcal"])
        profile.refresh_from_db()
        self.assertEqual(profile.sex, on_file)

    def test_screening_rejects_unrealistic_measurements(self):
        self.client_api.force_authenticate(self.client_user)
        cases = [
            ({"height_cm": "99", "weight_kg": "70"}, "height_cm"),
            ({"height_cm": "509999", "weight_kg": "70"}, "height_cm"),
            ({"height_cm": "abc", "weight_kg": "70"}, "height_cm"),
            ({"height_cm": "251", "weight_kg": "70"}, "height_cm"),
            ({"height_cm": "170", "weight_kg": "24"}, "weight_kg"),
            ({"height_cm": "170", "weight_kg": "301"}, "weight_kg"),
            ({"height_cm": "170.255", "weight_kg": "70"}, "height_cm"),
        ]
        for payload, field in cases:
            resp = self.client_api.post("/api/client/screening/", payload, format="json")
            self.assertEqual(resp.status_code, 400, payload)
            self.assertIn(field, resp.data, payload)
        ok = self.client_api.post("/api/client/screening/", {"height_cm": "250", "weight_kg": "25"}, format="json")
        self.assertEqual(ok.status_code, 201, ok.data)

    def test_typed_age_limits_when_no_dob(self):
        bare_client = User.objects.create_user(email="bare3@t.ph", password="x", role="client", first_name="B", last_name="C")
        ClientProfile.objects.create(user=bare_client)
        self.client_api.force_authenticate(bare_client)
        for age in (5, 17, 500):
            resp = self.client_api.post("/api/client/screening/", {"height_cm": "170", "weight_kg": "70", "age": age, "sex": "male"})
            self.assertEqual(resp.status_code, 400, age)
            self.assertIn("age", resp.data)

    def test_latest_screening_returns_most_recent(self):
        self.client_api.force_authenticate(self.client_user)
        # Accounts from before screenings became one-time can have several.
        PreConsultationScreening.objects.create(client=self.client_user, height_cm=170, weight_kg=70)
        PreConsultationScreening.objects.create(client=self.client_user, height_cm=170, weight_kg=68)

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

    def test_extra_fields_saved_cleaned_and_returned(self):
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.post(f"/api/rnd/relationships/{self.rel.id}/ncp/", {
            "relationship": self.rel.id, "encounter_date": str(timezone.now().date()),
            "assessment_extra": [
                {"label": " Waist circumference ", "value": " 92 ", "unit": "cm"},
                {"label": "   ", "value": "", "unit": ""},  # an empty row is dropped
            ],
            "intervention_extra": [{"label": "Fluid restriction", "value": "1.5", "unit": "L/day"}],
        }, format="json")

        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["assessment_extra"], [{"label": "Waist circumference", "value": "92", "unit": "cm"}])
        record = NcpRecord.objects.get(pk=resp.data["id"])
        self.assertEqual(record.intervention_extra[0]["unit"], "L/day")

        resp = self.client_api.patch(f"/api/rnd/ncp/{record.id}/", {"assessment_notes": "Updated"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        record.refresh_from_db()
        self.assertEqual(len(record.assessment_extra), 1)

    def test_no_ncp_record_can_be_deleted(self):
        # Drafts come from a consultation, so neither a draft nor a finalized
        # record can be deleted (no DELETE on the endpoint).
        draft = NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date())
        final = NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date(), status="completed")
        self.client_api.force_authenticate(self.rnd)
        for record in (draft, final):
            self.assertEqual(self.client_api.delete(f"/api/rnd/ncp/{record.id}/").status_code, 405)
            self.assertTrue(NcpRecord.objects.filter(pk=record.id).exists())

    def test_extra_fields_are_capped(self):
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.post(f"/api/rnd/relationships/{self.rel.id}/ncp/", {
            "relationship": self.rel.id, "encounter_date": str(timezone.now().date()),
            "assessment_extra": [{"label": f"Item {i}", "value": "1"} for i in range(31)],
        }, format="json")
        self.assertEqual(resp.status_code, 400)

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
            pes_problem="Inadequate intake", pes_etiology="skipped meals", pes_signs="weight loss of 3 kg",
            diet_prescription="1800 kcal exchange diet", target_kcal=Decimal("1800"),
        )
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.patch(f"/api/rnd/ncp/{record.id}/finalize/")

        self.assertEqual(resp.status_code, 200, resp.data)
        record.refresh_from_db()
        self.assertEqual(record.status, "completed")

    def test_finalize_refused_when_required_fields_missing(self):
        record = NcpRecord.objects.create(
            relationship=self.rel, encounter_date=timezone.now().date(), weight_kg=Decimal("70"),
        )
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.patch(f"/api/rnd/ncp/{record.id}/finalize/")

        self.assertEqual(resp.status_code, 400)
        self.assertIn("PES problem", resp.data["detail"])
        record.refresh_from_db()
        self.assertEqual(record.status, "draft")

    def test_finalized_record_cannot_be_edited(self):
        record = NcpRecord.objects.create(
            relationship=self.rel, encounter_date=timezone.now().date(),
            status="completed", assessment_notes="original",
        )
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.patch(f"/api/rnd/ncp/{record.id}/", {"assessment_notes": "changed"}, format="json")

        self.assertEqual(resp.status_code, 403)
        record.refresh_from_db()
        self.assertEqual(record.assessment_notes, "original")

    def test_status_cannot_be_changed_through_plain_update(self):
        record = NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date())
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.patch(f"/api/rnd/ncp/{record.id}/", {"status": "completed"}, format="json")

        self.assertEqual(resp.status_code, 200)
        record.refresh_from_db()
        self.assertEqual(record.status, "draft")

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


class RndAppointmentScreeningViewTests(TestCase):
    """The Appointments page's "View Screening" popup."""

    def setUp(self):
        from profiles.models import ClientHealthProfile
        from scheduling.models import Appointment

        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client(sex="female")
        ClientHealthProfile.objects.create(user=self.client_user, medical_conditions=["Type 2 Diabetes"], allergies=["Shrimp"])
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="pending")
        self.appt = Appointment.objects.create(
            relationship=self.rel, scheduled_at=timezone.now() + datetime.timedelta(days=2),
            status="pending", notes="First visit",
        )

    def _screen(self, weight):
        return PreConsultationScreening.objects.create(
            client=self.client_user, height_cm=Decimal("160"), weight_kg=Decimal(weight),
            bmi=calculate_bmi(Decimal(weight), Decimal("160")), bmi_category="Overweight",
        )

    def test_owning_rnd_gets_latest_screening_and_health_profile(self):
        self._screen("70")
        latest = self._screen("68")
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.get(f"/api/rnd/appointments/{self.appt.id}/screening/")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["screening"]["id"], latest.id)
        self.assertEqual(resp.data["client"]["medical_conditions"], ["Type 2 Diabetes"])
        self.assertEqual(resp.data["client"]["allergies"], ["Shrimp"])
        self.assertEqual(resp.data["client"]["sex"], "female")
        self.assertEqual(resp.data["appointment"]["notes"], "First visit")

    def test_no_screening_returns_null(self):
        self.client_api.force_authenticate(self.rnd)
        resp = self.client_api.get(f"/api/rnd/appointments/{self.appt.id}/screening/")

        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.data["screening"])

    def test_other_rnd_cannot_see_it(self):
        self._screen("68")
        self.client_api.force_authenticate(_make_rnd(email="other@t.ph"))
        resp = self.client_api.get(f"/api/rnd/appointments/{self.appt.id}/screening/")

        self.assertEqual(resp.status_code, 404)

    def test_client_cannot_use_rnd_endpoint(self):
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.get(f"/api/rnd/appointments/{self.appt.id}/screening/")

        self.assertEqual(resp.status_code, 403)


class NonNegativeAndBloodPressureTests(TestCase):
    """Measurements are never negative, and blood pressure must be
    number/number — enforced by the API, not just the form."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.record = NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date())

    def _patch_ncp(self, data):
        self.client_api.force_authenticate(self.rnd)
        return self.client_api.patch(f"/api/rnd/ncp/{self.record.id}/", data, format="json")

    def test_negative_ncp_values_rejected(self):
        resp = self._patch_ncp({"weight_kg": "-70", "target_kcal": "-1"})

        self.assertEqual(resp.status_code, 400)
        self.assertIn("weight_kg", resp.data)
        self.assertIn("target_kcal", resp.data)

    def test_zero_is_allowed(self):
        resp = self._patch_ncp({"target_fat_g": "0"})

        self.assertEqual(resp.status_code, 200, resp.data)

    def test_blood_pressure_must_be_number_slash_number(self):
        for bad in ["120", "abc/80", "120/eighty", "120-80", "1200/80"]:
            self.assertEqual(self._patch_ncp({"blood_pressure": bad}).status_code, 400, bad)

        resp = self._patch_ncp({"blood_pressure": "120 / 80"})
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["blood_pressure"], "120/80")

        self.assertEqual(self._patch_ncp({"blood_pressure": ""}).status_code, 200)

    def test_negative_screening_rejected(self):
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.post("/api/client/screening/", {"height_cm": "-160", "weight_kg": "60"}, format="json")

        self.assertEqual(resp.status_code, 400)
        self.assertIn("height_cm", resp.data)

    def test_progress_record_validated(self):
        self.client_api.force_authenticate(self.rnd)
        url = f"/api/rnd/relationships/{self.rel.id}/progress/"
        base = {"relationship": self.rel.id, "record_date": str(timezone.now().date())}

        # The RND no longer types progress in (it comes from finalized NCP records).
        self.assertEqual(self.client_api.post(url, {**base, "weight_kg": "70", "blood_pressure": "118/76"}, format="json").status_code, 405)


class NcpFollowUpRecordTests(TestCase):
    """First record ends at Intervention; follow-ups (client already has a
    finalized record) also need Monitoring before they can be finalized."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = _make_rnd()
        self.client_user = _make_client()
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.client_api.force_authenticate(self.rnd)
        self.complete = dict(
            weight_kg=Decimal("70"), height_cm=Decimal("165"),
            pes_problem="Excessive carbohydrate intake", pes_etiology="large rice servings", pes_signs="FBS 148 mg/dL",
            diet_prescription="1500 kcal low-GI diet", target_kcal=Decimal("1500"),
        )

    def _record(self, **extra):
        return NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date(), **{**self.complete, **extra})

    def test_first_record_finalizes_without_monitoring(self):
        first = self._record()
        resp = self.client_api.patch(f"/api/rnd/ncp/{first.id}/finalize/")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertFalse(resp.data["is_follow_up"])

    def test_follow_up_needs_goal_status(self):
        self._record(status="completed")
        follow_up = self._record()

        resp = self.client_api.patch(f"/api/rnd/ncp/{follow_up.id}/finalize/")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("goal status", resp.data["detail"])

        follow_up.goal_status = "partially_met"
        follow_up.save()
        resp = self.client_api.patch(f"/api/rnd/ncp/{follow_up.id}/finalize/")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertTrue(resp.data["is_follow_up"])

    def test_only_one_open_draft_per_client(self):
        url = f"/api/rnd/relationships/{self.rel.id}/ncp/"
        body = {"relationship": self.rel.id, "encounter_date": str(timezone.now().date())}

        self.assertEqual(self.client_api.post(url, body, format="json").status_code, 201)
        resp = self.client_api.post(url, body, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(NcpRecord.objects.filter(relationship=self.rel).count(), 1)
