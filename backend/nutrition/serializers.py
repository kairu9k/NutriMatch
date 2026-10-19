from decimal import Decimal

from rest_framework import serializers

from core.validators import NonNegativeNumbersMixin

from .models import (
    FoodExchangeCategory,
    FoodExchangeItem,
    MealLog,
    MealPlan,
    MealPlanFoodItem,
    MealPlanMeal,
)


class FoodExchangeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodExchangeCategory
        fields = [
            "id", "code", "name", "description", "kcal_per_exchange",
            "carbs_g", "protein_g", "fat_g", "color", "sort_order",
        ]


class FoodExchangeItemSerializer(serializers.ModelSerializer):
    category = FoodExchangeCategorySerializer(read_only=True)

    class Meta:
        model = FoodExchangeItem
        fields = [
            "id", "category", "name", "local_name", "subcategory",
            "ep_grams", "household_measure",
            "is_high_sodium", "is_high_potassium", "is_high_phosphorus",
            "is_high_fiber", "is_low_gi",
            "ok_for_diabetes", "ok_for_hypertension", "ok_for_renal",
            "is_free_food", "notes",
        ]


class MealPlanFoodItemSerializer(NonNegativeNumbersMixin, serializers.ModelSerializer):
    class Meta:
        model = MealPlanFoodItem
        fields = [
            "id", "meal_plan_meal", "food_item", "food_name", "source_type",
            "external_food_id", "exchanges", "household_measure", "notes",
            "kcal", "carbs_g", "protein_g", "fat_g", "grams",
        ]
        read_only_fields = ["meal_plan_meal"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # USDA foods: kcal/macros are computed live, never stored (RA 10173).
        if instance.source_type == MealPlanFoodItem.SourceType.USDA:
            from .usda import item_nutrients

            per_100g, values = item_nutrients(instance)
            data.update(values)
            data["usda_per_100g"] = per_100g
        return data


class MealPlanMealSerializer(NonNegativeNumbersMixin, serializers.ModelSerializer):
    """Exchange totals (vegetable_exchanges etc.) are derived from this
    meal's food_items — see MealPlanMeal.recompute_exchanges — not
    editable directly, so they're read-only here."""

    food_items = MealPlanFoodItemSerializer(many=True, read_only=True)

    class Meta:
        model = MealPlanMeal
        fields = [
            "id", "meal_plan", "day_of_week", "meal_time", "scheduled_time",
            "vegetable_exchanges", "fruit_exchanges",
            "milk_exchanges", "rice_exchanges", "meat_exchanges", "fat_exchanges",
            "sugar_exchanges", "meal_notes", "food_items",
        ]
        read_only_fields = [
            "meal_plan", "vegetable_exchanges", "fruit_exchanges", "milk_exchanges",
            "rice_exchanges", "meat_exchanges", "fat_exchanges", "sugar_exchanges",
        ]


class NutrientTargetSerializer(serializers.Serializer):
    """One Measured Variable / Value / Unit row of a meal plan's targets.
    Blank-label rows are accepted and dropped in MealPlanSerializer.validate
    (an empty "+ Add Field" row the RND never filled in)."""

    label = serializers.CharField(max_length=100, allow_blank=True)
    value = serializers.CharField(max_length=100, allow_blank=True)
    unit = serializers.CharField(max_length=30, allow_blank=True, required=False, default="")


# Which row labels feed which macro column — matched case-insensitively,
# and only when the unit is grams (a % or mg value isn't a gram target).
_MACRO_LABELS = {
    "target_protein_g": {"protein", "proteins"},
    "target_carb_g": {"carb", "carbs", "carbohydrate", "carbohydrates"},
    "target_fat_g": {"fat", "fats", "total fat"},
}
_GRAM_UNITS = {"g", "g/day", "gram", "grams", "g per day", "grams/day"}


class MealPlanSerializer(NonNegativeNumbersMixin, serializers.ModelSerializer):
    meals = MealPlanMealSerializer(many=True, read_only=True)
    nutrient_targets = NutrientTargetSerializer(many=True, required=False)

    class Meta:
        model = MealPlan
        fields = [
            "id", "relationship", "name", "condition", "target_kcal",
            "target_protein_g", "target_carb_g", "target_fat_g", "nutrient_targets",
            "total_vegetable", "total_fruit", "total_milk", "total_rice",
            "total_meat", "total_fat", "total_sugar", "notes", "allergies_restrictions",
            "status", "sent_at", "meals", "created_at", "updated_at",
        ]
        # Status only changes through "Send to Patient" (RndMealPlanSendView),
        # which also archives the previous plan and notifies the client.
        # The macro columns are derived from nutrient_targets (see validate).
        read_only_fields = ["status", "sent_at", "target_protein_g", "target_carb_g", "target_fat_g"]

    def validate_relationship(self, value):
        request = self.context["request"]
        if value.rnd_id != request.user.id:
            raise serializers.ValidationError("You can only create meal plans for your own clients.")
        return value

    def validate_nutrient_targets(self, rows):
        from decimal import Decimal, InvalidOperation

        cleaned = []
        for row in rows:
            label = row["label"].strip()
            if not label:
                continue
            value = row["value"].strip()
            try:
                if value and Decimal(value) < 0:
                    raise serializers.ValidationError(f"{label} can't be negative.")
            except InvalidOperation:
                pass  # free text (e.g. "as tolerated") is allowed, like the NCP rows
            cleaned.append({"label": label, "value": value, "unit": (row.get("unit") or "").strip()})
        if len(cleaned) > 30:
            raise serializers.ValidationError("You can add up to 30 targets.")
        return cleaned

    def validate(self, attrs):
        # Keep the protein/carb/fat columns in step with the rows.
        if "nutrient_targets" in attrs:
            from decimal import Decimal, InvalidOperation

            for column, labels in _MACRO_LABELS.items():
                attrs[column] = None
                for row in attrs["nutrient_targets"]:
                    if row["label"].lower() in labels and row["unit"].lower() in _GRAM_UNITS:
                        try:
                            attrs[column] = Decimal(row["value"])
                        except InvalidOperation:
                            pass
                        break
        return attrs


class WeekFoodItemSerializer(serializers.Serializer):
    food_item = serializers.PrimaryKeyRelatedField(queryset=FoodExchangeItem.objects.all(), required=False, allow_null=True)
    food_name = serializers.CharField(max_length=255)
    # USDA foods: source_type "usda" + the FDC id + grams; kcal/macros sent
    # for them are ignored (computed live, see nutrition/usda.py).
    source_type = serializers.ChoiceField(choices=["fel", "custom", "usda"], required=False)
    external_food_id = serializers.RegexField(r"^\d{1,12}$", required=False, allow_null=True, allow_blank=True)
    grams = serializers.DecimalField(max_digits=6, decimal_places=1, required=False, allow_null=True)
    household_measure = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    exchanges = serializers.DecimalField(max_digits=4, decimal_places=1, required=False, min_value=0)
    kcal = serializers.DecimalField(max_digits=7, decimal_places=1, required=False, allow_null=True, min_value=0)
    carbs_g = serializers.DecimalField(max_digits=6, decimal_places=1, required=False, allow_null=True, min_value=0)
    protein_g = serializers.DecimalField(max_digits=6, decimal_places=1, required=False, allow_null=True, min_value=0)
    fat_g = serializers.DecimalField(max_digits=6, decimal_places=1, required=False, allow_null=True, min_value=0)

    def validate(self, attrs):
        if attrs.get("source_type") == "usda":
            from .usda import MAX_GRAMS

            if not attrs.get("external_food_id"):
                raise serializers.ValidationError({"external_food_id": "A USDA food needs its FoodData Central id."})
            grams = attrs.get("grams")
            if grams is None or not Decimal("1") <= grams <= MAX_GRAMS:
                raise serializers.ValidationError({"grams": f"Enter the portion in grams (1–{MAX_GRAMS:.0f})."})
            attrs.update(food_item=None, kcal=None, carbs_g=None, protein_g=None, fat_g=None)
        else:
            attrs.update(external_food_id=None, grams=None)
        return attrs


class WeekMealSerializer(serializers.Serializer):
    day_of_week = serializers.ChoiceField(choices=MealPlanMeal.DayOfWeek.choices)
    meal_time = serializers.ChoiceField(choices=MealPlanMeal.MealTime.choices)
    scheduled_time = serializers.TimeField(required=False, allow_null=True)
    items = WeekFoodItemSerializer(many=True)


class MealPlanWeekSerializer(serializers.Serializer):
    """The whole weekly grid (day × meal slot → food rows) saved in one go."""

    meals = WeekMealSerializer(many=True)

    def validate_meals(self, value):
        keys = [(m["day_of_week"], m["meal_time"]) for m in value]
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError("Each day can have each meal slot only once.")
        return value


class RndMealLogSerializer(serializers.ModelSerializer):
    """One client meal log as the RND sees it — what was planned for that
    meal next to what the client logged (photo, time, status, reason). Used
    by GET /api/rnd/meal-logs/<id>/ and attached to "Meal log update"
    notifications so the RND sees the log right in the notification."""

    status_label = serializers.CharField(read_only=True)
    can_review = serializers.SerializerMethodField()
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    relationship_id = serializers.IntegerField(source="meal_plan_meal.meal_plan.relationship_id", read_only=True)
    plan_name = serializers.CharField(source="meal_plan_meal.meal_plan.name", read_only=True)
    meal_label = serializers.CharField(source="meal_plan_meal.get_meal_time_display", read_only=True)
    scheduled_time = serializers.TimeField(source="meal_plan_meal.scheduled_time", read_only=True)
    planned_items = serializers.SerializerMethodField()
    # A link that expires (private photo) — see nutrition/photos.py.
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = MealLog
        fields = [
            "id", "log_date", "status", "status_label", "reviewed_at", "can_review", "time_logged", "reason_notes", "photo_url",
            "client_name", "relationship_id", "plan_name", "meal_label", "scheduled_time", "planned_items",
            "updated_at",
        ]
        read_only_fields = fields

    def get_can_review(self, obj):
        return obj.meal_plan_meal.meal_plan.relationship.status == "active"

    def get_photo_url(self, obj):
        from .photos import meal_photo_link

        return meal_photo_link(obj)

    def get_planned_items(self, obj):
        return [
            {"food_name": i.food_name, "household_measure": i.household_measure, "kcal": i.kcal}
            for i in obj.meal_plan_meal.food_items.all()
        ]


class MealLogSerializer(serializers.ModelSerializer):
    # A link that expires (private photo) — see nutrition/photos.py.
    photo_url = serializers.SerializerMethodField()

    def get_photo_url(self, obj):
        from .photos import meal_photo_link

        return meal_photo_link(obj)

    class Meta:
        model = MealLog
        fields = [
            "id", "meal_plan_meal", "log_date", "status", "status_label", "reviewed_at",
            "time_logged", "reason_notes", "photo_url", "created_at", "updated_at",
        ]
        # The client only sends a note (+ photo); the RND rates it and the
        # server stamps the time.
        read_only_fields = ["meal_plan_meal", "log_date", "photo_url", "status", "reviewed_at", "time_logged"]
        extra_kwargs = {"reason_notes": {"max_length": 1000, "allow_blank": True, "required": False}}

    status_label = serializers.CharField(read_only=True)
