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


class WeeklyMealPlanTests(TestCase):
    """The Meal Planning page saves a Mon–Sun grid in one request and
    publishes it with "Send to Patient"."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = User.objects.create_user(email="rnd3@nt.ph", password="x", role="rnd", first_name="R", last_name="D")
        self.client_user = User.objects.create_user(email="client3@nt.ph", password="x", role="client", first_name="C", last_name="L")
        self.rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        self.plan = MealPlan.objects.create(relationship=self.rel, name="Week Plan", target_kcal=Decimal("1800"))
        category = FoodExchangeCategory.objects.create(code="rice_a", name="Rice A")
        self.rice = FoodExchangeItem.objects.create(category=category, name="Rice, boiled")
        self.client_api.force_authenticate(self.rnd)

    def _week(self, items_monday_breakfast, extra=None):
        meals = [{
            "day_of_week": 1, "meal_time": "breakfast", "scheduled_time": "07:00",
            "items": items_monday_breakfast,
        }]
        return {"meals": meals + (extra or [])}

    def _save(self, payload):
        return self.client_api.put(f"/api/rnd/meal-plans/{self.plan.id}/week/", payload, format="json")

    def test_new_plan_starts_as_draft(self):
        self.assertEqual(self.plan.status, MealPlan.Status.DRAFT)

    def test_save_week_creates_meals_items_and_totals(self):
        resp = self._save(self._week(
            [{"food_item": self.rice.id, "food_name": "Rice, boiled", "household_measure": "1/2 cup",
              "exchanges": "2", "kcal": "200", "carbs_g": "46", "protein_g": "4", "fat_g": "0"}],
            extra=[{"day_of_week": 3, "meal_time": "dinner", "items": [{"food_name": "Tinola", "kcal": "250"}]}],
        ))

        self.assertEqual(resp.status_code, 200, resp.data)
        monday = self.plan.meals.get(day_of_week=1, meal_time="breakfast")
        self.assertEqual(str(monday.scheduled_time), "07:00:00")
        self.assertEqual(monday.rice_exchanges, Decimal("2.0"))
        item = monday.food_items.get()
        self.assertEqual((item.kcal, item.source_type), (Decimal("200.0"), "fel"))
        self.assertEqual(self.plan.meals.get(day_of_week=3).food_items.get().source_type, "custom")

    def test_resave_keeps_same_meal_and_replaces_items(self):
        self._save(self._week([{"food_name": "Oatmeal", "kcal": "150"}]))
        meal_id = self.plan.meals.get(day_of_week=1).id

        self._save(self._week([{"food_name": "Pandesal", "kcal": "120"}, {"food_name": "Egg", "kcal": "70"}]))

        meal = self.plan.meals.get(day_of_week=1)
        self.assertEqual(meal.id, meal_id)
        self.assertEqual(sorted(meal.food_items.values_list("food_name", flat=True)), ["Egg", "Pandesal"])

    def test_emptied_slot_is_kept_when_client_logged_it(self):
        from .models import MealLog

        self._save(self._week([{"food_name": "Oatmeal"}]))
        meal = self.plan.meals.get(day_of_week=1)
        MealLog.objects.create(meal_plan_meal=meal, client=self.client_user, log_date="2026-09-28", status="followed")

        self._save({"meals": []})

        self.assertTrue(MealPlanMeal.objects.filter(pk=meal.pk).exists())
        self.assertEqual(MealLog.objects.count(), 1)

    def test_emptied_slot_without_logs_is_removed(self):
        self._save(self._week([{"food_name": "Oatmeal"}]))
        self._save(self._week([]))
        self.assertFalse(self.plan.meals.exists())

    def test_duplicate_slots_rejected(self):
        slot = {"day_of_week": 1, "meal_time": "lunch", "items": []}
        resp = self._save({"meals": [slot, slot]})
        self.assertEqual(resp.status_code, 400)

    def test_other_rnd_cannot_save_week(self):
        other = User.objects.create_user(email="rnd4@nt.ph", password="x", role="rnd", first_name="O", last_name="R")
        self.client_api.force_authenticate(other)
        self.assertEqual(self._save(self._week([{"food_name": "Oatmeal"}])).status_code, 404)

    def test_send_requires_food(self):
        resp = self.client_api.post(f"/api/rnd/meal-plans/{self.plan.id}/send/")
        self.assertEqual(resp.status_code, 400)

    def test_send_activates_archives_previous_and_notifies(self):
        from communication.models import NotificationLog

        old = MealPlan.objects.create(relationship=self.rel, name="Old", status=MealPlan.Status.ACTIVE)
        self._save(self._week([{"food_name": "Oatmeal"}]))

        resp = self.client_api.post(f"/api/rnd/meal-plans/{self.plan.id}/send/")

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(resp.data["status"], "active")
        old.refresh_from_db()
        self.assertEqual(old.status, MealPlan.Status.ARCHIVED)
        self.assertTrue(NotificationLog.objects.filter(recipient=self.client_user, notifiable_type="meal_plan").exists())

    def test_client_does_not_see_drafts(self):
        self.client_api.force_authenticate(self.client_user)
        self.assertEqual(self.client_api.get("/api/client/meal-plans/").data, [])

        self.client_api.force_authenticate(self.rnd)
        self._save(self._week([{"food_name": "Oatmeal"}]))
        self.client_api.post(f"/api/rnd/meal-plans/{self.plan.id}/send/")

        self.client_api.force_authenticate(self.client_user)
        self.assertEqual([p["id"] for p in self.client_api.get("/api/client/meal-plans/").data], [self.plan.id])

    def test_status_cannot_be_patched_directly(self):
        self.client_api.patch(f"/api/rnd/meal-plans/{self.plan.id}/", {"status": "active"}, format="json")
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.status, MealPlan.Status.DRAFT)
