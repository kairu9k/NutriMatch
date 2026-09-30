from django.urls import path

from .views import (
    ClientMealLogListView,
    ClientMealLogSaveView,
    ClientMealPlanListView,
    FoodExchangeCategoryListView,
    FoodExchangeItemListView,
    RndMealPlanDetailView,
    RndMealPlanFoodItemCreateView,
    RndMealPlanFoodItemDeleteView,
    RndMealPlanListCreateView,
    RndMealPlanMealCreateView,
    RndMealPlanMealDetailView,
    RndMealPlanSendView,
    RndMealPlanWeekView,
)

urlpatterns = [
    path("food-exchange/categories/", FoodExchangeCategoryListView.as_view(), name="food_exchange_categories"),
    path("food-exchange/items/", FoodExchangeItemListView.as_view(), name="food_exchange_items"),

    path("rnd/relationships/<int:relationship_id>/meal-plans/", RndMealPlanListCreateView.as_view(), name="rnd_meal_plan_list_create"),
    path("rnd/meal-plans/<int:pk>/", RndMealPlanDetailView.as_view(), name="rnd_meal_plan_detail"),
    path("rnd/meal-plans/<int:pk>/week/", RndMealPlanWeekView.as_view(), name="rnd_meal_plan_week"),
    path("rnd/meal-plans/<int:pk>/send/", RndMealPlanSendView.as_view(), name="rnd_meal_plan_send"),
    path("rnd/meal-plans/<int:meal_plan_id>/meals/", RndMealPlanMealCreateView.as_view(), name="rnd_meal_plan_meal_create"),
    path("rnd/meals/<int:pk>/", RndMealPlanMealDetailView.as_view(), name="rnd_meal_plan_meal_detail"),
    path("rnd/meals/<int:meal_id>/food-items/", RndMealPlanFoodItemCreateView.as_view(), name="rnd_meal_food_item_create"),
    path("rnd/food-items/<int:pk>/", RndMealPlanFoodItemDeleteView.as_view(), name="rnd_meal_food_item_delete"),
    path("client/meal-plans/", ClientMealPlanListView.as_view(), name="client_meal_plan_list"),
    path("client/meal-logs/", ClientMealLogListView.as_view(), name="client_meal_log_list"),
    path("client/meals/<int:meal_id>/log/", ClientMealLogSaveView.as_view(), name="client_meal_log_save"),
]
