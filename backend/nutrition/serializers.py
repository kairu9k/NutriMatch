from rest_framework import serializers

from .models import FoodExchangeCategory, FoodExchangeItem


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
