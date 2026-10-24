from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import User
from core.test_utils import approve_rnd
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
        rnd = approve_rnd(User.objects.create_user(email="rnd@nt.ph", password="x", role="rnd", first_name="R", last_name="D"))
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
        self.rnd = approve_rnd(User.objects.create_user(email="rnd2@nt.ph", password="x", role="rnd", first_name="R", last_name="D"))
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
        self.rnd = approve_rnd(User.objects.create_user(email="rnd3@nt.ph", password="x", role="rnd", first_name="R", last_name="D"))
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
        other = approve_rnd(User.objects.create_user(email="rnd4@nt.ph", password="x", role="rnd", first_name="O", last_name="R"))
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


class NonNegativeMealPlanTests(TestCase):
    setUp = WeeklyMealPlanTests.setUp  # same RND / client / plan fixture

    def test_negative_plan_target_rejected(self):
        resp = self.client_api.patch(f"/api/rnd/meal-plans/{self.plan.id}/", {"target_kcal": "-100"}, format="json")

        self.assertEqual(resp.status_code, 400)
        self.assertIn("target_kcal", resp.data)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.target_kcal, Decimal("1800"))

    def test_negative_food_macro_in_week_rejected(self):
        resp = self.client_api.put(f"/api/rnd/meal-plans/{self.plan.id}/week/", {"meals": [{
            "day_of_week": 1, "meal_time": "breakfast", "items": [{"food_name": "Rice", "kcal": "-5"}],
        }]}, format="json")

        self.assertEqual(resp.status_code, 400)


class MealPlanNutrientTargetTests(TestCase):
    """Plan targets beyond calories are Measured Variable / Value / Unit rows;
    gram rows for protein/carbs/fat also fill the macro columns."""

    setUp = WeeklyMealPlanTests.setUp

    def _patch(self, rows):
        return self.client_api.patch(f"/api/rnd/meal-plans/{self.plan.id}/", {"nutrient_targets": rows}, format="json")

    def test_rows_saved_and_macro_columns_synced(self):
        resp = self._patch([
            {"label": "Protein", "value": "70", "unit": "g/day"},
            {"label": "carbohydrate", "value": "210", "unit": "g"},
            {"label": "Fat", "value": "30", "unit": "% of kcal"},  # not grams → no fat column
            {"label": "Fiber", "value": "25", "unit": "g/day"},
            {"label": "  ", "value": "", "unit": ""},  # empty row dropped
        ])

        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual([r["label"] for r in resp.data["nutrient_targets"]], ["Protein", "carbohydrate", "Fat", "Fiber"])
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.target_protein_g, Decimal("70"))
        self.assertEqual(self.plan.target_carb_g, Decimal("210"))
        self.assertIsNone(self.plan.target_fat_g)

    def test_negative_value_rejected(self):
        resp = self._patch([{"label": "Protein", "value": "-5", "unit": "g/day"}])

        self.assertEqual(resp.status_code, 400)

    def test_macro_columns_are_not_directly_writable(self):
        self._patch([{"label": "Protein", "value": "70", "unit": "g/day"}])
        resp = self.client_api.patch(f"/api/rnd/meal-plans/{self.plan.id}/", {"target_protein_g": "999"}, format="json")

        self.assertEqual(resp.status_code, 200)
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.target_protein_g, Decimal("70"))

    def test_plan_saved_with_only_columns_gets_rows(self):
        plan = MealPlan.objects.create(
            relationship=self.rel, name="Seeded", target_protein_g=Decimal("80.00"), target_fat_g=Decimal("55.5"),
        )
        self.assertEqual(plan.nutrient_targets, [
            {"label": "Protein", "value": "80", "unit": "g/day"},
            {"label": "Fat", "value": "55.5", "unit": "g/day"},
        ])


class RndMealLogNotificationTests(TestCase):
    """When a client logs a meal, the RND's notification carries the log
    (meal, status, photo, what was planned) and the RND can open it."""

    def setUp(self):
        self.client_api = APIClient()
        self.rnd = approve_rnd(User.objects.create_user(email="rnd9@nt.ph", password="x", role="rnd", first_name="Maria", last_name="S"))
        self.client_user = User.objects.create_user(email="client9@nt.ph", password="x", role="client", first_name="Ana", last_name="C")
        rel = RndClientRelationship.objects.create(rnd=self.rnd, client=self.client_user, status="active")
        plan = MealPlan.objects.create(relationship=rel, name="Plan", status="active")
        # day_of_week None = every day, so it can be logged whatever today is.
        self.meal = MealPlanMeal.objects.create(meal_plan=plan, day_of_week=None, meal_time="breakfast")
        self.plan = plan
        MealPlanFoodItem.objects.create(meal_plan_meal=self.meal, food_name="Rice, boiled", household_measure="1/2 cup", kcal=Decimal("100"))

        self.client_api.force_authenticate(self.client_user)
        # A status or time sent by the client is ignored: the RND rates it, the server stamps the time.
        resp = self.client_api.post(f"/api/client/meals/{self.meal.id}/log/", {
            "status": "followed", "time_logged": "03:00", "reason_notes": "Only half the rice",
        }, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertIsNone(resp.data["status"])
        self.assertNotEqual(resp.data["time_logged"], "03:00:00")
        self.log_id = resp.data["id"]

    def test_editing_a_waiting_log_does_not_notify_again(self):
        from communication.models import NotificationLog

        resp = self.client_api.post(f"/api/client/meals/{self.meal.id}/log/", {"reason_notes": "All the rice after all"}, format="json")
        self.assertEqual(resp.status_code, 200, resp.data)
        self.assertEqual(NotificationLog.objects.filter(recipient=self.rnd, notifiable_type="meal_log").count(), 1)

    def test_rnd_notification_includes_the_meal_log(self):
        self.client_api.force_authenticate(self.rnd)
        notifications = self.client_api.get("/api/notifications/").data
        meal_note = next(n for n in notifications if n["notifiable_type"] == "meal_log")

        log = meal_note["meal_log"]
        self.assertEqual(log["id"], self.log_id)
        self.assertEqual(log["meal_label"], "Breakfast")
        self.assertEqual(log["status_label"], "Waiting for review")
        self.assertEqual(log["reason_notes"], "Only half the rice")
        self.assertEqual(log["client_name"], "Ana C")
        self.assertEqual(log["planned_items"][0]["food_name"], "Rice, boiled")

    def test_rnd_can_open_the_log_but_others_cannot(self):
        self.client_api.force_authenticate(self.rnd)
        self.assertEqual(self.client_api.get(f"/api/rnd/meal-logs/{self.log_id}/").status_code, 200)

        other = approve_rnd(User.objects.create_user(email="rnd10@nt.ph", password="x", role="rnd", first_name="O", last_name="R"))
        self.client_api.force_authenticate(other)
        self.assertEqual(self.client_api.get(f"/api/rnd/meal-logs/{self.log_id}/").status_code, 404)

        self.client_api.force_authenticate(self.client_user)
        self.assertEqual(self.client_api.get(f"/api/rnd/meal-logs/{self.log_id}/").status_code, 403)

    def test_other_notification_types_have_no_meal_log(self):
        self.client_api.force_authenticate(self.client_user)
        for n in self.client_api.get("/api/notifications/").data:
            self.assertIsNone(n["meal_log"])

    def test_a_log_needs_a_photo_or_note(self):
        self.client_api.force_authenticate(self.client_user)
        resp = self.client_api.post(f"/api/client/meals/{self.meal.id}/log/", {"reason_notes": "  "}, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_only_the_rnd_rates_and_a_rated_log_is_final(self):
        from .models import MealLog

        self.client_api.force_authenticate(self.rnd)
        bad = self.client_api.patch(f"/api/rnd/meal-logs/{self.log_id}/review/", {"status": "great"}, format="json")
        self.assertEqual(bad.status_code, 400)
        ok = self.client_api.patch(f"/api/rnd/meal-logs/{self.log_id}/review/", {"status": "partially_followed"}, format="json")
        self.assertEqual(ok.status_code, 200, ok.data)
        self.assertEqual(ok.data["status_label"], "Partially Followed")

        other = approve_rnd(User.objects.create_user(email="rnd11@nt.ph", password="x", role="rnd", first_name="O", last_name="R"))
        self.client_api.force_authenticate(other)
        self.assertEqual(self.client_api.patch(f"/api/rnd/meal-logs/{self.log_id}/review/", {"status": "followed"}, format="json").status_code, 404)

        # Once rated, the client can't change it (and the rating stays).
        self.client_api.force_authenticate(self.client_user)
        log = MealLog.objects.get(pk=self.log_id)
        resp = self.client_api.post(f"/api/client/meals/{self.meal.id}/log/", {"log_date": str(log.log_date), "reason_notes": "Actually all of it"}, format="json")
        self.assertEqual(resp.status_code, 400)
        log.refresh_from_db()
        self.assertEqual((log.status, log.reason_notes == "Actually all of it"), ("partially_followed", False))

    def test_the_day_comes_from_the_server_not_the_phone(self):
        # A phone set to another date can't log meals for other days.
        from core.ph_time import ph_today

        from .models import MealLog

        self.client_api.force_authenticate(self.client_user)
        self.assertEqual(MealLog.objects.get(pk=self.log_id).log_date, ph_today())
        past = self.client_api.post(f"/api/client/meals/{self.meal.id}/log/", {"log_date": "2026-01-05", "reason_notes": "Backdated"}, format="json")
        self.assertEqual(past.status_code, 400)
        self.assertEqual(MealLog.objects.filter(meal_plan_meal=self.meal).count(), 1)
        # A meal planned for another weekday isn't on today's plan.
        other_day = (ph_today().weekday() + 2) % 7
        meal = MealPlanMeal.objects.create(meal_plan=self.plan, day_of_week=other_day, meal_time="lunch")
        resp = self.client_api.post(f"/api/client/meals/{meal.id}/log/", {"reason_notes": "Lunch"}, format="json")
        self.assertEqual(resp.status_code, 400)
