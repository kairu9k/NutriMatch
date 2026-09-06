from django.urls import path

from .views import (
    ClientMealPlanListView,
    FoodExchangeCategoryListView,
    FoodExchangeItemListView,
    RndMealPlanFoodItemCreateView,
    RndMealPlanListCreateView,
    RndMealPlanMealCreateView,
)

urlpatterns = [
    path("food-exchange/categories/", FoodExchangeCategoryListView.as_view(), name="food_exchange_categories"),
    path("food-exchange/items/", FoodExchangeItemListView.as_view(), name="food_exchange_items"),

    path("rnd/relationships/<int:relationship_id>/meal-plans/", RndMealPlanListCreateView.as_view(), name="rnd_meal_plan_list_create"),
    path("rnd/meal-plans/<int:meal_plan_id>/meals/", RndMealPlanMealCreateView.as_view(), name="rnd_meal_plan_meal_create"),
    path("rnd/meals/<int:meal_id>/food-items/", RndMealPlanFoodItemCreateView.as_view(), name="rnd_meal_food_item_create"),
    path("client/meal-plans/", ClientMealPlanListView.as_view(), name="client_meal_plan_list"),
]
