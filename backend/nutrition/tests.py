from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from scheduling.models import RndClientRelationship

from .models import (
    FoodExchangeCategory,
    FoodExchangeItem,
    MealPlan,
    MealPlanFoodItem,
    MealPlanMeal,
)


class MealPlanExchangeRecomputeTests(TestCase):
    """Exchange totals at the top of a meal are derived from its food
    items, not manually entered — see MealPlanMeal.recompute_exchanges."""

    def setUp(self):
        rnd = User.objects.create_user(email="rnd@nt.ph", password="x", role="rnd", first_name="R", last_name="D")
        client = User.objects.create_user(email="client@nt.ph", password="x", role="client", first_name="C", last_name="L")
        rel = RndClientRelationship.objects.create(rnd=rnd, client=client, status="active")
        plan = MealPlan.objects.create(relationship=rel, name="Test Plan")
        self.meal = MealPlanMeal.objects.create(meal_plan=plan, meal_time="breakfast")

        self.rice_b = FoodExchangeCategory.objects.create(code="rice_b", name="Rice B")
        self.rice_c = FoodExchangeCategory.objects.create(code="rice_c", name="Rice C")
        self.vegetable = FoodExchangeCategory.objects.create(code="vegetable", name="Vegetable")

        self.rice_item = FoodExchangeItem.objects.create(category=self.rice_b, name="Rice, boiled")
        self.rice_item_2 = FoodExchangeItem.objects.create(category=self.rice_c, name="Rice, fried")
        self.veg_item = FoodExchangeItem.objects.create(category=self.vegetable, name="Kangkong")

    def test_recompute_sums_by_category_prefix(self):
        # Two different rice subcategories (rice_b, rice_c) should both
        # collapse into the single rice_exchanges total.
        MealPlanFoodItem.objects.create(
            meal_plan_meal=self.meal, food_item=self.rice_item, food_name="Rice, boiled",
            source_type="fel", exchanges=Decimal("1.0"),
        )
        MealPlanFoodItem.objects.create(
            meal_plan_meal=self.meal, food_item=self.rice_item_2, food_name="Rice, fried",
            source_type="fel", exchanges=Decimal("0.5"),
        )
        MealPlanFoodItem.objects.create(
            meal_plan_meal=self.meal, food_item=self.veg_item, food_name="Kangkong",
            source_type="fel", exchanges=Decimal("2.0"),
        )

        self.meal.recompute_exchanges()
        self.meal.refresh_from_db()

        self.assertEqual(self.meal.rice_exchanges, Decimal("1.5"))
        self.assertEqual(self.meal.vegetable_exchanges, Decimal("2.0"))
        self.assertEqual(self.meal.meat_exchanges, Decimal("0.0"))

    def test_free_text_items_excluded_from_totals(self):
        # A custom/free-text item has no food_item FK, so its category is
        # unknown — it must not silently count toward any exchange total.
        MealPlanFoodItem.objects.create(
            meal_plan_meal=self.meal, food_item=None, food_name="Homemade lumpia",
            source_type="custom", exchanges=Decimal("3.0"),
        )

        self.meal.recompute_exchanges()
        self.meal.refresh_from_db()

        self.assertEqual(self.meal.rice_exchanges, Decimal("0.0"))
        self.assertEqual(self.meal.vegetable_exchanges, Decimal("0.0"))

    def test_removing_last_item_resets_total_to_zero(self):
        item = MealPlanFoodItem.objects.create(
            meal_plan_meal=self.meal, food_item=self.rice_item, food_name="Rice, boiled",
            source_type="fel", exchanges=Decimal("1.5"),
        )
        self.meal.recompute_exchanges()
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.rice_exchanges, Decimal("1.5"))

        item.delete()
        self.meal.recompute_exchanges()
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.rice_exchanges, Decimal("0.0"))


class MealPlanFoodItemViewTests(TestCase):
    """Adding/removing a food item via the real API recomputes the meal's
    exchange totals — not just the model method in isolation."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = User.objects.create_user(email="rnd2@nt.ph", password="x", role="rnd", first_name="R", last_name="D")
        client = User.objects.create_user(email="client2@nt.ph", password="x", role="client", first_name="C", last_name="L")
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=client, status="active")
        plan = MealPlan.objects.create(relationship=rel, name="Test Plan")
        self.meal = MealPlanMeal.objects.create(meal_plan=plan, meal_time="breakfast")

        category = FoodExchangeCategory.objects.create(code="meat_low", name="Meat (Low Fat)")
        self.food_item = FoodExchangeItem.objects.create(category=category, name="Chicken breast")

        self.client_api.force_authenticate(self.rnd)

    def test_create_food_item_recomputes_meal_totals(self):
        resp = self.client_api.post(f"/api/rnd/meals/{self.meal.id}/food-items/", {
            "food_item": self.food_item.id, "food_name": "Chicken breast",
            "source_type": "fel", "exchanges": "2.0",
        })
        self.assertEqual(resp.status_code, 201, resp.data)

        self.meal.refresh_from_db()
        self.assertEqual(self.meal.meat_exchanges, Decimal("2.0"))

    def test_delete_food_item_recomputes_meal_totals(self):
        item = MealPlanFoodItem.objects.create(
            meal_plan_meal=self.meal, food_item=self.food_item, food_name="Chicken breast",
            source_type="fel", exchanges=Decimal("2.0"),
        )
        self.meal.recompute_exchanges()
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.meat_exchanges, Decimal("2.0"))

        resp = self.client_api.delete(f"/api/rnd/food-items/{item.id}/")
        self.assertEqual(resp.status_code, 204)

        self.meal.refresh_from_db()
        self.assertEqual(self.meal.meat_exchanges, Decimal("0.0"))

    def test_exchange_fields_not_editable_via_meal_patch(self):
        resp = self.client_api.patch(f"/api/rnd/meals/{self.meal.id}/", {"rice_exchanges": "9.9"})
        self.assertEqual(resp.status_code, 200, resp.data)

        self.meal.refresh_from_db()
        self.assertEqual(self.meal.rice_exchanges, Decimal("0.0"))
