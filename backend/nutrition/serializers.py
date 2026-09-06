from rest_framework import serializers

from .models import (
    FoodExchangeCategory,
    FoodExchangeItem,
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
        ]
        read_only_fields = ["meal_plan_meal"]


class MealPlanMealSerializer(serializers.ModelSerializer):
    food_items = MealPlanFoodItemSerializer(many=True, read_only=True)

    class Meta:
        model = MealPlanMeal
        fields = [
            "id", "meal_plan", "meal_time", "vegetable_exchanges", "fruit_exchanges",
            "milk_exchanges", "rice_exchanges", "meat_exchanges", "fat_exchanges",
            "sugar_exchanges", "meal_notes", "food_items",
        ]
        read_only_fields = ["meal_plan"]


class MealPlanSerializer(serializers.ModelSerializer):
    meals = MealPlanMealSerializer(many=True, read_only=True)

    class Meta:
        model = MealPlan
        fields = [
            "id", "relationship", "name", "condition", "target_kcal",
            "total_vegetable", "total_fruit", "total_milk", "total_rice",
            "total_meat", "total_fat", "total_sugar", "notes", "status",
            "meals", "created_at", "updated_at",
        ]

    def validate_relationship(self, value):
        request = self.context["request"]
        if value.rnd_id != request.user.id:
            raise serializers.ValidationError("You can only create meal plans for your own clients.")
        return value
