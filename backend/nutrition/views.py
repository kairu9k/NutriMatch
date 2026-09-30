from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsClient, IsRnd
from communication.services import CloudinaryResourceUploadService, ResourceUploadError, notify

from .models import FoodExchangeCategory, FoodExchangeItem, MealLog, MealPlan, MealPlanFoodItem, MealPlanMeal
from .serializers import (
    FoodExchangeCategorySerializer,
    FoodExchangeItemSerializer,
    MealLogSerializer,
    MealPlanFoodItemSerializer,
    MealPlanMealSerializer,
    MealPlanSerializer,
    MealPlanWeekSerializer,
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
    """RND adds a food item to one meal within a meal plan. The meal's
    exchange totals are recomputed from its food items afterward — see
    MealPlanMeal.recompute_exchanges."""

    serializer_class = MealPlanFoodItemSerializer
    permission_classes = [IsRnd]

    def perform_create(self, serializer):
        meal = get_object_or_404(
            MealPlanMeal.objects.filter(meal_plan__relationship__rnd=self.request.user),
            pk=self.kwargs["meal_id"],
        )
        serializer.save(meal_plan_meal=meal)
        meal.recompute_exchanges()


class RndMealPlanFoodItemDeleteView(generics.DestroyAPIView):
    """RND removing a food item from a meal. Recomputes the meal's exchange
    totals afterward — see MealPlanMeal.recompute_exchanges."""

    permission_classes = [IsRnd]

    def get_queryset(self):
        return MealPlanFoodItem.objects.filter(meal_plan_meal__meal_plan__relationship__rnd=self.request.user)

    def perform_destroy(self, instance):
        meal = instance.meal_plan_meal
        instance.delete()
        meal.recompute_exchanges()


class RndMealPlanWeekView(APIView):
    """Saves the whole weekly grid (Mon–Sun × meal slots) in one request.

    Meals are matched by (day_of_week, meal_time) and updated in place rather
    than deleted and recreated — the client's MealLog rows point at these
    meals, so recreating them would wipe the client's adherence history.
    A slot left empty is removed only if nothing has been logged against it.
    Food rows carry no logs, so they're simply replaced."""

    permission_classes = [IsRnd]

    def put(self, request, pk):
        plan = get_object_or_404(MealPlan.objects.filter(relationship__rnd=request.user), pk=pk)
        serializer = MealPlanWeekSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            existing = {
                (m.day_of_week, m.meal_time): m
                for m in plan.meals.filter(day_of_week__isnull=False)
            }
            for slot in serializer.validated_data["meals"]:
                key = (slot["day_of_week"], slot["meal_time"])
                items = [i for i in slot["items"] if i["food_name"].strip()]
                meal = existing.pop(key, None)

                if not items:
                    if meal and not meal.logs.exists():
                        meal.delete()
                    elif meal:
                        meal.food_items.all().delete()
                        meal.scheduled_time = slot.get("scheduled_time")
                        meal.save(update_fields=["scheduled_time"])
                        meal.recompute_exchanges()
                    continue

                if meal is None:
                    meal = MealPlanMeal.objects.create(
                        meal_plan=plan, day_of_week=key[0], meal_time=key[1],
                        scheduled_time=slot.get("scheduled_time"),
                    )
                else:
                    meal.scheduled_time = slot.get("scheduled_time")
                    meal.save(update_fields=["scheduled_time"])
                    meal.food_items.all().delete()

                MealPlanFoodItem.objects.bulk_create([
                    MealPlanFoodItem(
                        meal_plan_meal=meal,
                        food_item=item.get("food_item"),
                        food_name=item["food_name"].strip(),
                        source_type=(
                            MealPlanFoodItem.SourceType.FEL if item.get("food_item")
                            else MealPlanFoodItem.SourceType.CUSTOM
                        ),
                        household_measure=item.get("household_measure") or None,
                        exchanges=item.get("exchanges") or Decimal("1.0"),
                        kcal=item.get("kcal"),
                        carbs_g=item.get("carbs_g"),
                        protein_g=item.get("protein_g"),
                        fat_g=item.get("fat_g"),
                    )
                    for item in items
                ])
                meal.recompute_exchanges()

            # Slots the RND didn't send at all — same rule as emptied slots.
            for meal in existing.values():
                if not meal.logs.exists():
                    meal.delete()

            plan.save(update_fields=["updated_at"])

        plan = MealPlan.objects.prefetch_related("meals__food_items").get(pk=plan.pk)
        return Response(MealPlanSerializer(plan, context={"request": request}).data)


class RndMealPlanSendView(APIView):
    """"Send to Patient": makes the plan the client's active plan (archiving
    any other active plan for that client) and notifies them. Re-sending an
    already-active plan after edits just notifies them of the update."""

    permission_classes = [IsRnd]

    def post(self, request, pk):
        plan = get_object_or_404(
            MealPlan.objects.select_related("relationship__client").filter(relationship__rnd=request.user), pk=pk,
        )
        if not plan.meals.filter(food_items__isnull=False).exists():
            raise serializers.ValidationError({"detail": "Add at least one food item before sending the plan."})

        was_active = plan.status == MealPlan.Status.ACTIVE
        with transaction.atomic():
            MealPlan.objects.filter(
                relationship=plan.relationship, status=MealPlan.Status.ACTIVE
            ).exclude(pk=plan.pk).update(status=MealPlan.Status.ARCHIVED)
            plan.status = MealPlan.Status.ACTIVE
            plan.sent_at = timezone.now()
            plan.save(update_fields=["status", "sent_at", "updated_at"])

        notify(
            recipient=plan.relationship.client,
            notifiable_type="meal_plan",
            notifiable_id=plan.id,
            subject="Meal plan updated" if was_active else "New meal plan",
            content=(
                f"{request.user.full_name} "
                f"{'updated your meal plan' if was_active else 'sent you a new meal plan'}: {plan.name}."
            ),
        )

        plan = MealPlan.objects.prefetch_related("meals__food_items").get(pk=plan.pk)
        return Response(MealPlanSerializer(plan, context={"request": request}).data)


class ClientMealPlanListView(generics.ListAPIView):
    """Client's own meal plans, most recent first. Drafts are the RND's work
    in progress and stay hidden until sent."""

    serializer_class = MealPlanSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        return MealPlan.objects.filter(
            relationship__client=self.request.user
        ).exclude(status=MealPlan.Status.DRAFT).prefetch_related("meals__food_items").order_by("-created_at")


class ClientMealLogListView(generics.ListAPIView):
    """Client's own adherence logs, optionally filtered to one date via
    ?date=YYYY-MM-DD (defaults to every log they've ever saved)."""

    serializer_class = MealLogSerializer
    permission_classes = [IsClient]

    def get_queryset(self):
        qs = MealLog.objects.filter(client=self.request.user)
        log_date = self.request.query_params.get("date")
        if log_date:
            qs = qs.filter(log_date=log_date)
        return qs.order_by("-log_date")


class ClientMealLogSaveView(APIView):
    """Client logs (or updates) their actual intake for one prescribed meal
    on one date. Upserts on (meal_plan_meal, log_date) — re-saving the same
    meal/day edits that day's entry rather than creating duplicates.
    Notifies the meal plan's RND on every save, matching the design's
    'saved & sent to RND' confirmation."""

    permission_classes = [IsClient]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, meal_id):
        meal = get_object_or_404(
            MealPlanMeal.objects.select_related("meal_plan__relationship__rnd"),
            pk=meal_id,
            meal_plan__relationship__client=request.user,
        )

        log_date = request.data.get("log_date") or timezone.localdate().isoformat()
        instance = MealLog.objects.filter(meal_plan_meal=meal, log_date=log_date).first()

        serializer = MealLogSerializer(instance, data=request.data, partial=instance is not None)
        serializer.is_valid(raise_exception=True)

        photo = request.data.get("photo")
        photo_url = instance.photo_url if instance else None
        if photo is not None:
            try:
                photo_url = CloudinaryResourceUploadService().upload(photo, folder="meal-logs")
            except ResourceUploadError as exc:
                raise serializers.ValidationError({"photo": [str(exc)]})

        meal_log = serializer.save(
            meal_plan_meal=meal, client=request.user, log_date=log_date, photo_url=photo_url
        )

        rnd = meal.meal_plan.relationship.rnd
        notify(
            recipient=rnd,
            notifiable_type="meal_log",
            notifiable_id=meal_log.id,
            subject="Meal log update",
            content=(
                f"{request.user.full_name} logged {meal.get_meal_time_display()} "
                f"as \"{meal_log.get_status_display()}\" for {log_date}."
            ),
        )

        return Response(MealLogSerializer(meal_log).data, status=status.HTTP_200_OK)
