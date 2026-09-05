from django.contrib import admin

from .models import FoodExchangeCategory, FoodExchangeItem, MealPlan, MealPlanFoodItem, MealPlanMeal

admin.site.register(FoodExchangeCategory)
admin.site.register(FoodExchangeItem)
admin.site.register(MealPlan)
admin.site.register(MealPlanMeal)
admin.site.register(MealPlanFoodItem)
