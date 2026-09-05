from django.urls import path

from .views import FoodExchangeCategoryListView, FoodExchangeItemListView

urlpatterns = [
    path("food-exchange/categories/", FoodExchangeCategoryListView.as_view(), name="food_exchange_categories"),
    path("food-exchange/items/", FoodExchangeItemListView.as_view(), name="food_exchange_items"),
]
