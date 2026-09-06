from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from accounts.permissions import IsClient, IsRnd

from .models import FoodExchangeCategory, FoodExchangeItem, MealPlan, MealPlanFoodItem, MealPlanMeal
from .serializers import (
    FoodExchangeCategorySerializer,
    FoodExchangeItemSerializer,
    MealPlanFoodItemSerializer,
    MealPlanMealSerializer,
    MealPlanSerializer,
)


class FoodExchangeCategoryListView(generics.ListAPIView):
    """FNRI Food Exchange List categories. PH food data only — no USDA
    integration (deferred, see project scope notes)."""

    serializer_class = FoodExchangeCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = FoodExchangeCategory.objects.all()


class FoodExchangeItemListView(generics.ListAPIView):
    serializer_class = FoodExchangeItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = FoodExchangeItem.objects.select_related("category")

        category_id = self.request.query_params.get("category")
        if category_id:
            qs = qs.filter(category_id=category_id)

        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(name__icontains=search)

        for flag in ("ok_for_diabetes", "ok_for_hypertension", "ok_for_renal"):
            value = self.request.query_params.get(flag)
            if value is not None:
                qs = qs.filter(**{flag: value.lower() in ("1", "true", "yes")})

        return qs


class RndMealPlanListCreateView(generics.ListCreateAPIView):
    """RND creates/lists meal plans for a specific client relationship."""

    serializer_class = MealPlanSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return MealPlan.objects.filter(
            relationship_id=self.kwargs["relationship_id"], relationship__rnd=self.request.user
        ).prefetch_related("meals__food_items").order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save()


class RndMealPlanDetailView(generics.RetrieveUpdateAPIView):
    """RND editing one of their own meal plans (name/condition/targets/notes/status)."""

    serializer_class = MealPlanSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return MealPlan.objects.filter(relationship__rnd=self.request.user).prefetch_related("meals__food_items")


class RndMealPlanMealCreateView(generics.CreateAPIView):
    """RND adds a meal (breakfast/lunch/etc.) to one of their meal plans."""

    serializer_class = MealPlanMealSerializer
    permission_classes = [IsRnd]

    def perform_create(self, serializer):
        meal_plan = get_object_or_404(
            MealPlan.objects.filter(relationship__rnd=self.request.user),
            pk=self.kwargs["meal_plan_id"],
        )
        serializer.save(meal_plan=meal_plan)


class RndMealPlanMealDetailView(generics.RetrieveUpdateDestroyAPIView):
    """RND editing or removing one meal (and its food items, via cascade)."""

    serializer_class = MealPlanMealSerializer
    permission_classes = [IsRnd]

    def get_queryset(self):
        return MealPlanMeal.objects.filter(meal_plan__relationship__rnd=self.request.user)


class RndMealPlanFoodItemCreateView(generics.CreateAPIView):
    """RND adds a food item to one meal within a meal plan."""

    serializer_class = MealPlanFoodItemSerializer
    permission_classes = [IsRnd]

    def perform_create(self, serializer):
        meal = get_object_or_404(
            MealPlanMeal.objects.filter(meal_plan__relationship__rnd=self.request.user),
            pk=self.kwargs["meal_id"],
        )
        serializer.save(meal_plan_meal=meal)


class RndMealPlanFoodItemDeleteView(generics.DestroyAPIView):
    """RND removing a food item from a meal."""

    permission_classes = [IsRnd]

    def get_queryset(self):
        return MealPlanFoodItem.objects.filter(meal_plan_meal__meal_plan__relationship__rnd=self.request.user)


class ClientMealPlanListView(generics.ListAPIView):
    """Client's own meal plans, most recent first."""

    serializer_class = MealPlanSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return MealPlan.objects.filter(
            relationship__client=self.request.user
        ).prefetch_related("meals__food_items").order_by("-created_at")
