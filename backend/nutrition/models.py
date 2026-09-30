from decimal import Decimal

from django.db import models

from scheduling.models import RndClientRelationship


class FoodExchangeCategory(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    kcal_per_exchange = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    carbs_g = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    protein_g = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fat_g = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    color = models.CharField(max_length=7, null=True, blank=True)
    sort_order = models.SmallIntegerField(default=0)

    class Meta:
        db_table = "food_exchange_categories"
        ordering = ["sort_order"]
        verbose_name_plural = "food exchange categories"

    def __str__(self):
        return self.name


class FoodExchangeItem(models.Model):
    category = models.ForeignKey(
        FoodExchangeCategory, on_delete=models.CASCADE, related_name="items"
    )
    name = models.CharField(max_length=255)
    local_name = models.CharField(max_length=255, null=True, blank=True)
    subcategory = models.CharField(max_length=50, null=True, blank=True)
    ep_grams = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    household_measure = models.CharField(max_length=100, null=True, blank=True)
    is_high_sodium = models.BooleanField(default=False)
    is_high_potassium = models.BooleanField(default=False)
    is_high_phosphorus = models.BooleanField(default=False)
    is_high_fiber = models.BooleanField(default=False)
    is_low_gi = models.BooleanField(default=False)
    ok_for_diabetes = models.BooleanField(default=True)
    ok_for_hypertension = models.BooleanField(default=True)
    ok_for_renal = models.BooleanField(default=True)
    is_free_food = models.BooleanField(default=False)
    notes = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        db_table = "food_exchange_items"

    def __str__(self):
        return self.name


class MealPlan(models.Model):
    class Condition(models.TextChoices):
        DIABETES = "diabetes", "Diabetes"
        HYPERTENSION = "hypertension", "Hypertension"
        RENAL = "renal", "Renal"
        WEIGHT_LOSS = "weight_loss", "Weight Loss"
        WEIGHT_GAIN = "weight_gain", "Weight Gain"
        GENERAL = "general", "General"

    class Status(models.TextChoices):
        # Drafts are the RND's work in progress — not visible to the client
        # until "Send to Patient" makes the plan active.
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="meal_plans"
    )
    name = models.CharField(max_length=255)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GENERAL)
    target_kcal = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    target_protein_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    target_carb_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    target_fat_g = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    total_vegetable = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_fruit = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_milk = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_rice = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_meat = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_fat = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_sugar = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    notes = models.TextField(null=True, blank=True)
    allergies_restrictions = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "meal_plans"

    def __str__(self):
        return f"{self.name} ({self.get_condition_display()})"


class MealPlanMeal(models.Model):
    class MealTime(models.TextChoices):
        BREAKFAST = "breakfast", "Breakfast"
        AM_SNACK = "am_snack", "AM Snack"
        LUNCH = "lunch", "Lunch"
        PM_SNACK = "pm_snack", "PM Snack"
        DINNER = "dinner", "Dinner"
        BEDTIME_SNACK = "bedtime_snack", "Bedtime Snack"

    class DayOfWeek(models.IntegerChoices):
        # Sunday=0, same convention as RndAvailabilitySchedule and JS Date#getDay.
        SUNDAY = 0, "Sunday"
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"

    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name="meals")
    # Null = applies every day (plans made before per-day planning).
    day_of_week = models.SmallIntegerField(choices=DayOfWeek.choices, null=True, blank=True)
    meal_time = models.CharField(max_length=20, choices=MealTime.choices)
    scheduled_time = models.TimeField(null=True, blank=True)
    vegetable_exchanges = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    fruit_exchanges = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    milk_exchanges = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    rice_exchanges = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    meat_exchanges = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    fat_exchanges = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    sugar_exchanges = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    meal_notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "meal_plan_meals"

    def __str__(self):
        return f"{self.meal_plan.name} — {self.get_meal_time_display()}"

    # Category code prefix -> exchange field. Rice A/B/C and the three milk
    # types all collapse into one total each; vegetable/fruit/fat/sugar map
    # 1:1. A food item with no linked food_item (free-text/custom) has no
    # known category and is deliberately excluded — we don't know what it
    # is, so it can't count toward a specific exchange total.
    _CATEGORY_PREFIX_TO_FIELD = {
        "vegetable": "vegetable_exchanges",
        "fruit": "fruit_exchanges",
        "milk": "milk_exchanges",
        "rice": "rice_exchanges",
        "meat": "meat_exchanges",
        "fat": "fat_exchanges",
        "sugar": "sugar_exchanges",
    }

    def recompute_exchanges(self):
        """Sums this meal's food items by category and writes the totals
        into the *_exchanges fields, replacing whatever manual values were
        there. Call after any food item is added/removed."""
        from decimal import Decimal

        totals = {field: Decimal("0") for field in self._CATEGORY_PREFIX_TO_FIELD.values()}
        for item in self.food_items.select_related("food_item__category"):
            if not item.food_item_id:
                continue
            code = item.food_item.category.code
            prefix = code.split("_")[0]
            field = self._CATEGORY_PREFIX_TO_FIELD.get(prefix)
            if field:
                totals[field] += item.exchanges

        for field, value in totals.items():
            setattr(self, field, value)
        self.save(update_fields=list(totals.keys()))


class MealPlanFoodItem(models.Model):
    """Actual foods matching individual meal components.

    RA 10173 data minimization: only plain-text `food_name` is persisted for
    externally sourced items (fnri_fct / usda). No nutrient payload from those
    APIs is ever written here — `external_food_id` is kept only as a reference
    for re-querying the source API, not for storing its response.
    """

    class SourceType(models.TextChoices):
        FEL = "fel", "FNRI Food Exchange List"
        FNRI_FCT = "fnri_fct", "FNRI Food Composition Table"
        USDA = "usda", "USDA FoodData Central"
        CUSTOM = "custom", "Custom"

    meal_plan_meal = models.ForeignKey(
        MealPlanMeal, on_delete=models.CASCADE, related_name="food_items"
    )
    food_item = models.ForeignKey(
        FoodExchangeItem, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    food_name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.FEL)
    external_food_id = models.CharField(max_length=100, null=True, blank=True)
    exchanges = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal("1.0"))
    household_measure = models.CharField(max_length=100, null=True, blank=True)
    notes = models.CharField(max_length=500, null=True, blank=True)
    # The RND's planned values for this portion (typed, or pre-filled from the
    # local FNRI exchange list). Not an external lookup payload, so RA 10173's
    # "food_name only" rule for external sources doesn't apply.
    kcal = models.DecimalField(max_digits=7, decimal_places=1, null=True, blank=True)
    carbs_g = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    protein_g = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    fat_g = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)

    class Meta:
        db_table = "meal_plan_food_items"

    def __str__(self):
        return self.food_name


class MealLog(models.Model):
    """Client-reported adherence for one prescribed meal on one date —
    the 'Actual Food Intake' side of a meal plan, as distinct from
    MealPlanMeal/MealPlanFoodItem which describe what was *prescribed*.

    One row per (meal_plan_meal, log_date). Not in the original DBML
    schema (vault/database.txt has no per-meal adherence table, only
    progress_records.adherence_pct as an RND-authored per-date summary)
    — added because the capstone's adherence-tracking requirement needs
    client-side, per-meal logging that progress_records doesn't cover.
    """

    class MealStatus(models.TextChoices):
        FOLLOWED = "followed", "Followed Plan"
        PARTIALLY_FOLLOWED = "partially_followed", "Partially Followed"
        NOT_FOLLOWED = "not_followed", "Did Not Follow"

    meal_plan_meal = models.ForeignKey(
        MealPlanMeal, on_delete=models.CASCADE, related_name="logs"
    )
    client = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="meal_logs"
    )
    log_date = models.DateField()
    status = models.CharField(max_length=20, choices=MealStatus.choices)
    time_logged = models.TimeField(null=True, blank=True)
    reason_notes = models.TextField(null=True, blank=True)
    photo_url = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "meal_logs"
        constraints = [
            models.UniqueConstraint(
                fields=["meal_plan_meal", "log_date"], name="unique_meal_log_per_day"
            )
        ]

    def __str__(self):
        return f"{self.meal_plan_meal} — {self.log_date} ({self.status})"
