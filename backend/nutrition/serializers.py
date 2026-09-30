from rest_framework import serializers

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


class MealPlanFoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealPlanFoodItem
        fields = [
            "id", "meal_plan_meal", "food_item", "food_name", "source_type",
            "external_food_id", "exchanges", "household_measure", "notes",
            "kcal", "carbs_g", "protein_g", "fat_g",
        ]
        read_only_fields = ["meal_plan_meal"]


class MealPlanMealSerializer(serializers.ModelSerializer):
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


class MealPlanSerializer(serializers.ModelSerializer):
    meals = MealPlanMealSerializer(many=True, read_only=True)

    class Meta:
        model = MealPlan
        fields = [
            "id", "relationship", "name", "condition", "target_kcal",
            "target_protein_g", "target_carb_g", "target_fat_g",
            "total_vegetable", "total_fruit", "total_milk", "total_rice",
            "total_meat", "total_fat", "total_sugar", "notes", "allergies_restrictions",
            "status", "sent_at", "meals", "created_at", "updated_at",
        ]
        # Status only changes through "Send to Patient" (RndMealPlanSendView),
        # which also archives the previous plan and notifies the client.
        read_only_fields = ["status", "sent_at"]

    def validate_relationship(self, value):
        request = self.context["request"]
        if value.rnd_id != request.user.id:
            raise serializers.ValidationError("You can only create meal plans for your own clients.")
        return value


class WeekFoodItemSerializer(serializers.Serializer):
    food_item = serializers.PrimaryKeyRelatedField(queryset=FoodExchangeItem.objects.all(), required=False, allow_null=True)
    food_name = serializers.CharField(max_length=255)
    household_measure = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    exchanges = serializers.DecimalField(max_digits=4, decimal_places=1, required=False, min_value=0)
    kcal = serializers.DecimalField(max_digits=7, decimal_places=1, required=False, allow_null=True, min_value=0)
    carbs_g = serializers.DecimalField(max_digits=6, decimal_places=1, required=False, allow_null=True, min_value=0)
    protein_g = serializers.DecimalField(max_digits=6, decimal_places=1, required=False, allow_null=True, min_value=0)
    fat_g = serializers.DecimalField(max_digits=6, decimal_places=1, required=False, allow_null=True, min_value=0)


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


class MealLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MealLog
        fields = [
            "id", "meal_plan_meal", "log_date", "status",
            "time_logged", "reason_notes", "photo_url", "created_at", "updated_at",
        ]
        read_only_fields = ["meal_plan_meal", "log_date", "photo_url"]
