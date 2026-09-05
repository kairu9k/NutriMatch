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
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    relationship = models.ForeignKey(
        RndClientRelationship, on_delete=models.CASCADE, related_name="meal_plans"
    )
    name = models.CharField(max_length=255)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.GENERAL)
    target_kcal = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)
    total_vegetable = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_fruit = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_milk = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_rice = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_meat = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_fat = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    total_sugar = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
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

    meal_plan = models.ForeignKey(MealPlan, on_delete=models.CASCADE, related_name="meals")
    meal_time = models.CharField(max_length=20, choices=MealTime.choices)
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

    class Meta:
        db_table = "meal_plan_food_items"

    def __str__(self):
        return self.food_name
