"""Dietary intake tools on the NCP record: 24-hour recall (calorie count from
FNRI exchanges), food frequency, IDDS, and the food diary in the form context."""

from datetime import time
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd, onboard_client
from nutrition.models import FoodExchangeCategory, FoodExchangeItem, MealLog, MealPlan, MealPlanFoodItem, MealPlanMeal
from scheduling.models import Appointment, RndClientRelationship

from .dietary import idds_level, recall_totals
from .models import NcpRecord


class DietaryIntakeTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@n.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@n.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        self.rice = FoodExchangeCategory.objects.create(code="rice_b", name="Rice B", kcal_per_exchange=Decimal("100"),
                                                        carbs_g=Decimal("23"), protein_g=Decimal("2"), fat_g=Decimal("0"))
        FoodExchangeCategory.objects.create(code="meat_medium", name="Meat (Medium Fat)", kcal_per_exchange=Decimal("86"),
                                            carbs_g=Decimal("0"), protein_g=Decimal("8"), fat_g=Decimal("6"))
        FoodExchangeItem.objects.create(category=self.rice, name="Rice, boiled", household_measure="1/2 cup")
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)
        self.url = f"/api/rnd/relationships/{self.rel.id}/ncp/"
        self.today = str(timezone.now().date())

    def post(self, **fields):
        return self.api.post(self.url, {"relationship": self.rel.id, "encounter_date": self.today, **fields}, format="json")

    RECALL = [
        {"meal": "breakfast", "food_name": "Rice, boiled", "amount": "1 cup", "group": "rice_b", "exchanges": "2"},
        {"meal": "lunch", "food_name": "Pork adobo", "amount": "2 pcs", "group": "meat_medium", "exchanges": 1.5},
        {"meal": "pm_snack", "food_name": "Banana cue", "amount": "1 stick", "group": "", "exchanges": None},
        {"meal": "dinner", "food_name": "", "amount": "", "group": "", "exchanges": ""},  # blank row, dropped
    ]

    def test_recall_saves_names_and_portions_and_counts_calories(self):
        resp = self.post(diet_recall=self.RECALL, diet_ffq={"sweet_drinks": "daily", "fruits": ""}, idds_groups=["meat_fish", "starchy", "starchy"])
        self.assertEqual(resp.status_code, 201, resp.data)
        rec = NcpRecord.objects.get(pk=resp.data["id"])
        self.assertEqual(len(rec.diet_recall), 3)
        # Only the food name and portion are stored — no nutrient values.
        self.assertEqual(set(rec.diet_recall[0]), {"meal", "food_name", "amount", "group", "exchanges"})
        self.assertEqual(rec.diet_ffq, {"sweet_drinks": "daily"})
        self.assertEqual(rec.idds_groups, ["starchy", "meat_fish"])
        totals = resp.data["dietary"]["recall"]
        # 2 × rice B (100 kcal) + 1.5 × medium-fat meat (86 kcal) = 329 kcal
        self.assertEqual(totals["kcal"], 329)
        self.assertEqual((totals["carbs_g"], totals["protein_g"], totals["fat_g"]), (46, 16, 9))
        self.assertEqual((totals["foods"], totals["counted"]), (3, 2))
        self.assertEqual(resp.data["dietary"]["idds_score"], 2)
        self.assertEqual(resp.data["dietary"]["idds_level"], "low")
        self.assertEqual(resp.data["dietary"]["ffq"], [{"group": "Sweetened drinks (soft drinks, juice, 3-in-1 coffee)", "frequency": "Once a day"}])

    def test_invalid_input_is_refused(self):
        bad = [
            {"diet_recall": [{"meal": "brunch", "food_name": "Rice", "group": "rice_b", "exchanges": 1}]},
            {"diet_recall": [{"meal": "lunch", "food_name": "Rice", "group": "unknown", "exchanges": 1}]},
            {"diet_recall": [{"meal": "lunch", "food_name": "Rice", "group": "rice_b", "exchanges": 25}]},
            {"diet_recall": [{"meal": "lunch", "food_name": "Rice", "group": "rice_b", "exchanges": "two"}]},
            {"diet_recall": [{"meal": "lunch", "food_name": "", "amount": "1 cup"}]},
            {"diet_recall": [{"meal": "lunch", "food_name": "x" * 121}]},
            {"diet_recall": [{"meal": "lunch", "food_name": "Rice"}] * 81},
            {"diet_ffq": {"sweet_drinks": "hourly"}},
            {"diet_ffq": {"pizza": "daily"}},
            {"idds_groups": ["starchy", "junk_food"]},
        ]
        for fields in bad:
            with self.subTest(fields=str(fields)[:60]):
                self.assertEqual(self.post(**fields).status_code, 400)

    def test_dietary_is_optional_for_finalize(self):
        rec = NcpRecord.objects.create(relationship=self.rel, encounter_date=timezone.now().date(), weight_kg=Decimal("70"),
                                       height_cm=Decimal("160"), pes_problem="P", pes_etiology="E", pes_signs="S",
                                       diet_prescription="1500 kcal", target_kcal=Decimal("1500"))
        self.assertEqual(self.api.patch(f"/api/rnd/ncp/{rec.id}/finalize/").status_code, 200)
        self.assertIsNone(self.api.get(f"/api/rnd/ncp/{rec.id}/").data["dietary"])

    def test_idds_levels(self):
        self.assertEqual([idds_level(n) for n in (0, 3, 4, 5, 6, 9)], ["low", "low", "medium", "medium", "high", "high"])
        self.assertIsNone(recall_totals([]))

    def test_context_has_foods_exchange_values_and_food_diary(self):
        plan = MealPlan.objects.create(relationship=self.rel, name="Plan", status="active")
        meal = MealPlanMeal.objects.create(meal_plan=plan, meal_time="breakfast", scheduled_time=time(7, 0))
        MealPlanFoodItem.objects.create(meal_plan_meal=meal, food_name="Rice, boiled")
        MealLog.objects.create(meal_plan_meal=meal, client=self.c, log_date=timezone.localdate(), status="partially_followed", reason_notes="Ate half")
        d = self.api.get(f"{self.url}context/").data
        self.assertEqual(d["exchange_values"][0]["code"], "rice_b")
        self.assertEqual(d["fnri_foods"], [{"name": "Rice, boiled", "local_name": None, "group": "rice_b", "measure": "1/2 cup"}])
        self.assertEqual(len(d["food_diary"]), 1)
        self.assertEqual(d["food_diary"][0]["planned"], ["Rice, boiled"])
        self.assertEqual(d["food_diary"][0]["notes"], "Ate half")

    def test_rnd_summary_shows_dietary_but_client_summary_does_not(self):
        appt = Appointment.objects.create(relationship=self.rel, type="video", status="completed", scheduled_at=timezone.now(), completed_at=timezone.now())
        NcpRecord.objects.create(relationship=self.rel, appointment=appt, encounter_date=timezone.now().date(), status="completed",
                                 diet_recall=[{"meal": "lunch", "food_name": "Rice", "amount": "", "group": "rice_b", "exchanges": 1}],
                                 idds_groups=["starchy"])
        rnd = self.api.get(f"/api/rnd/appointments/{appt.id}/summary/").data
        self.assertEqual(rnd["care_plan"]["dietary"]["recall"]["kcal"], 100)
        client = APIClient()
        client.force_authenticate(self.c)
        data = client.get(f"/api/client/appointments/{appt.id}/summary/").data
        self.assertNotIn("dietary", data.get("care_plan") or {})
