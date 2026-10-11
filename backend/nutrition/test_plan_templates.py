"""Disease-specific diet templates (objective 3)."""

from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from clinical.models import NcpRecord, PreConsultationScreening
from core.test_utils import approve_rnd, onboard_client
from profiles.models import ClientHealthProfile
from scheduling.models import RndClientRelationship

from .models import MealPlan, MealPlanFoodItem
from .plan_templates import TEMPLATES, daily_exchanges


class DietTemplateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed", verbosity=0)  # FNRI exchange lists

    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@t.ph", password="x", role="rnd", first_name="M", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@t.ph", password="x", role="client", first_name="A", last_name="C"))
        ClientHealthProfile.objects.update_or_create(user=self.c, defaults={"allergies": ["Shrimp"]})
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        PreConsultationScreening.objects.create(client=self.c, height_cm=Decimal("160"), weight_kg=Decimal("70"), tdee_kcal=Decimal("2100"))
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)
        self.url = f"/api/rnd/relationships/{self.rel.id}/meal-plans/from-template/"

    def _day_kcal(self, plan, day=1):
        items = MealPlanFoodItem.objects.filter(meal_plan_meal__meal_plan=plan, meal_plan_meal__day_of_week=day)
        return sum(i.kcal for i in items)

    def test_every_template_hits_its_kcal_target(self):
        for key in TEMPLATES:
            resp = self.api.post(self.url, {"template": key, "target_kcal": 1600}, format="json")
            self.assertEqual(resp.status_code, 201, resp.data)
            plan = MealPlan.objects.get(pk=resp.data["id"])
            self.assertEqual((plan.status, plan.condition), ("draft", TEMPLATES[key]["condition"]))
            self.assertEqual(plan.meals.count(), 35)  # 7 days × 5 meals
            self.assertAlmostEqual(float(self._day_kcal(plan)), 1600, delta=1600 * 0.08)

    def test_condition_rules_and_allergies(self):
        renal = MealPlan.objects.get(pk=self.api.post(self.url, {"template": "renal", "target_kcal": 1500}, format="json").data["id"])
        foods = MealPlanFoodItem.objects.filter(meal_plan_meal__meal_plan=renal).select_related("food_item__category")
        meats = [f for f in foods if f.food_item.category.code.startswith("meat")]
        self.assertTrue(meats)  # still some high-quality protein, just limited
        self.assertTrue(all(f.food_item.ok_for_renal for f in foods if not f.food_item.category.code.startswith("meat")))
        self.assertFalse(any(f.food_item.is_high_potassium or f.food_item.is_high_phosphorus for f in meats))
        self.assertFalse(any(f.food_item.category.code.startswith("milk") for f in foods))
        self.assertFalse(foods.filter(food_name__icontains="shrimp").exists())
        protein = sum(f.protein_g for f in foods.filter(meal_plan_meal__day_of_week=1))
        self.assertLess(protein, 50)  # protein-restricted

    def test_kcal_suggestion(self):
        data = self.api.get(f"/api/rnd/relationships/{self.rel.id}/meal-plan-templates/").data
        self.assertEqual(len(data["templates"]), 4)
        self.assertEqual(data["suggested_kcal"]["value"], 2100)  # screening TDEE
        self.assertEqual(data["allergies"], ["Shrimp"])
        NcpRecord.objects.create(relationship=self.rel, status="completed", encounter_date="2026-10-01", target_kcal=Decimal("1500"))
        self.assertEqual(self.api.get(f"/api/rnd/relationships/{self.rel.id}/meal-plan-templates/").data["suggested_kcal"]["value"], 1500)
        resp = self.api.post(self.url, {"template": "diabetes"}, format="json")
        self.assertEqual(MealPlan.objects.get(pk=resp.data["id"]).target_kcal, Decimal("1500"))

    def test_weight_management_default_deficit(self):
        resp = self.api.post(self.url, {"template": "weight_management"}, format="json")
        self.assertEqual(MealPlan.objects.get(pk=resp.data["id"]).target_kcal, Decimal("1600"))  # 2100 − 500

    def test_guards(self):
        self.assertEqual(self.api.post(self.url, {"template": "keto"}, format="json").status_code, 400)
        self.assertEqual(self.api.post(self.url, {"template": "diabetes", "target_kcal": 300}, format="json").status_code, 400)
        other = approve_rnd(User.objects.create_user(email="o@t.ph", password="x", role="rnd", first_name="O", last_name="R"))
        self.api.force_authenticate(other)
        self.assertEqual(self.api.post(self.url, {"template": "diabetes"}, format="json").status_code, 404)
        self.api.force_authenticate(self.rnd)
        self.rel.status = "discharged"
        self.rel.save()
        self.assertEqual(self.api.post(self.url, {"template": "diabetes"}, format="json").status_code, 403)

    def test_exchange_math(self):
        d = daily_exchanges(TEMPLATES["diabetes"], 1500)
        self.assertEqual((d["veg"], d["fruit"], d["milk"], d["sugar"]), (4, 3, 1, 0))
        self.assertTrue(all(v % Decimal("0.5") == 0 for v in d.values()))
