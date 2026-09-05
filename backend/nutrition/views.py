from rest_framework import generics, permissions

from .models import FoodExchangeCategory, FoodExchangeItem
from .serializers import FoodExchangeCategorySerializer, FoodExchangeItemSerializer


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
