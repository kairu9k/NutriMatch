"""USDA FoodData Central: search, cache, meal-plan foods stored without nutrients
(RA 10173) and computed live. httpx is mocked — no real network calls."""

from decimal import Decimal
from unittest import mock

import httpx
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from accounts.models import User
from core.models import ApiCache
from core.test_utils import approve_rnd, onboard_client
from scheduling.models import RndClientRelationship

from . import usda
from .models import MealPlan, MealPlanFoodItem

APPLE = {
    "fdcId": 2709215, "description": "Apple, raw", "dataType": "Survey (FNDDS)",
    "foodNutrients": [
        {"nutrientNumber": "208", "value": 61, "unitName": "KCAL"},
        {"nutrientNumber": "205", "value": 14.8, "unitName": "G"},
        {"nutrientNumber": "203", "value": 0.17, "unitName": "G"},
        {"nutrientNumber": "204", "value": 0.15, "unitName": "G"},
        {"nutrientNumber": "268", "value": 255, "unitName": "KJ"},
    ],
}
APPLE_DETAIL = {
    "fdcId": 2709215, "description": "Apple, raw", "dataType": "Survey (FNDDS)",
    "foodNutrients": [
        {"number": "208", "amount": 61, "unitName": "KCAL"}, {"number": "205", "amount": 14.8, "unitName": "G"},
        {"number": "203", "amount": 0.17, "unitName": "G"}, {"number": "204", "amount": 0.15, "unitName": "G"},
    ],
}


def fake_response(body, status=200):
    return httpx.Response(status, json=body, request=httpx.Request("GET", "https://api.nal.usda.gov"))


@override_settings(USDA_FDC_API_KEY="test-key")
class UsdaTests(TestCase):
    def setUp(self):
        self.rnd = approve_rnd(User.objects.create_user(email="r@n.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.c = onboard_client(User.objects.create_user(email="c@n.ph", password="x", role="client", first_name="Ana", last_name="C"))
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.c, status="active")
        self.api = APIClient()
        self.api.force_authenticate(self.rnd)

    @mock.patch("nutrition.usda.httpx.request")
    def test_search_normalizes_and_caches(self, req):
        req.return_value = fake_response({"foods": [APPLE]})
        resp = self.api.get("/api/usda/foods/", {"q": "apple"})
        self.assertEqual(resp.status_code, 200)
        food = resp.data["results"][0]
        self.assertEqual((food["fdc_id"], food["name"]), (2709215, "Apple, raw"))
        self.assertEqual(food["per_100g"]["kcal"], 61)
        self.assertEqual(food["per_100g"]["carbs_g"], 14.8)
        # Generic foods only, key sent as a query parameter.
        kwargs = req.call_args.kwargs
        self.assertEqual(kwargs["json"]["dataType"], usda.DATA_TYPES)
        self.assertEqual(kwargs["params"]["api_key"], "test-key")
        # Same search again comes from the cache.
        self.api.get("/api/usda/foods/", {"q": "Apple"})
        self.assertEqual(req.call_count, 1)
        self.assertTrue(ApiCache.objects.filter(cache_key__startswith="usda:search:").exists())

    @override_settings(USDA_FDC_API_KEY="")
    def test_not_configured_and_unavailable(self):
        self.assertEqual(self.api.get("/api/usda/foods/", {"q": "apple"}).status_code, 503)
        with override_settings(USDA_FDC_API_KEY="k"), mock.patch("nutrition.usda.httpx.request", side_effect=httpx.ConnectError("down")):
            self.assertEqual(self.api.get("/api/usda/foods/", {"q": "apple"}).status_code, 502)

    def test_rnd_only(self):
        client = APIClient()
        client.force_authenticate(self.c)
        self.assertEqual(client.get("/api/usda/foods/", {"q": "apple"}).status_code, 403)

    def test_energy_fallback_and_portion(self):
        per = usda._per_100g([{"nutrientNumber": "958", "value": 52.0, "unitName": "KCAL"}])
        self.assertEqual(per["kcal"], 52.0)
        self.assertEqual(usda.portion({"kcal": 61, "carbs_g": 14.8, "protein_g": 0.17, "fat_g": 0.15}, Decimal("150")),
                         {"kcal": 91.5, "carbs_g": 22.2, "protein_g": 0.3, "fat_g": 0.2})

    @mock.patch("nutrition.usda.httpx.request")
    def test_meal_plan_stores_name_id_grams_only_and_computes_live(self, req):
        req.return_value = fake_response(APPLE_DETAIL)
        plan = MealPlan.objects.create(relationship=self.rel, name="Plan")
        week = {"meals": [{"day_of_week": 1, "meal_time": "pm_snack", "items": [
            {"food_name": "Apple, raw", "source_type": "usda", "external_food_id": "2709215", "grams": "150",
             "kcal": "999", "carbs_g": "999"},  # sent nutrients are ignored
            {"food_name": "Banana cue", "kcal": "120"},
        ]}]}
        resp = self.api.put(f"/api/rnd/meal-plans/{plan.id}/week/", week, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        item = MealPlanFoodItem.objects.get(food_name="Apple, raw")
        self.assertEqual((item.source_type, item.external_food_id, item.grams), ("usda", "2709215", Decimal("150.0")))
        self.assertIsNone(item.kcal)
        self.assertIsNone(item.carbs_g)
        self.assertEqual(MealPlanFoodItem.objects.get(food_name="Banana cue").source_type, "custom")
        out = resp.data["meals"][0]["food_items"]
        apple = next(i for i in out if i["food_name"] == "Apple, raw")
        self.assertEqual(apple["kcal"], 91.5)
        self.assertEqual(apple["usda_per_100g"]["kcal"], 61)

    def test_usda_item_needs_id_and_grams(self):
        plan = MealPlan.objects.create(relationship=self.rel, name="Plan")
        for item in ({"food_name": "Apple", "source_type": "usda", "grams": "100"},
                     {"food_name": "Apple", "source_type": "usda", "external_food_id": "1", "grams": "0"},
                     {"food_name": "Apple", "source_type": "usda", "external_food_id": "abc", "grams": "100"}):
            week = {"meals": [{"day_of_week": 1, "meal_time": "lunch", "items": [item]}]}
            self.assertEqual(self.api.put(f"/api/rnd/meal-plans/{plan.id}/week/", week, format="json").status_code, 400)
