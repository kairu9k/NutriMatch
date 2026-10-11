"""USDA FoodData Central — the second food source beside FNRI (proposal: meal
plans "drawing from both the FNRI Food Exchange Lists and USDA FoodData
Central"). FNRI stays the default for Filipino foods; USDA fills the gaps.

RA 10173 data minimization: nothing from USDA is copied into domain tables.
A meal-plan food from USDA stores only its name, the FDC id and the grams
(MealPlanFoodItem); its kcal/macros are worked out live from the per-100 g
values, which are kept only in the transient core.ApiCache (TTL CACHE_DAYS).

Endpoints (RND): GET /api/usda/foods/?q=  and  GET /api/usda/foods/<fdc_id>/."""

from datetime import timedelta
from decimal import Decimal

import httpx
from django.conf import settings
from django.utils import timezone

BASE_URL = "https://api.nal.usda.gov/fdc/v1"
# Generic foods only — branded products are label data, often per serving.
DATA_TYPES = ["Foundation", "SR Legacy", "Survey (FNDDS)"]
CACHE_DAYS = 30
TIMEOUT = 15
MAX_GRAMS = Decimal("2000")

# FDC nutrient numbers → our keys (all per 100 g).
NUTRIENTS = {
    "208": "kcal", "205": "carbs_g", "203": "protein_g", "204": "fat_g",
    "291": "fiber_g", "269": "sugars_g", "307": "sodium_mg", "306": "potassium_mg", "305": "phosphorus_mg",
}
# Some Foundation foods report energy only as Atwater factors.
ENERGY_FALLBACKS = ("958", "957")


class UsdaNotConfigured(Exception):
    pass


class UsdaUnavailable(Exception):
    pass


def _api_key():
    key = getattr(settings, "USDA_FDC_API_KEY", "")
    if not key:
        raise UsdaNotConfigured("USDA food search isn't set up yet (USDA_FDC_API_KEY is blank).")
    return key


def _request(method, path, params=None, **kwargs):
    try:
        resp = httpx.request(method, f"{BASE_URL}{path}", params={**(params or {}), "api_key": _api_key()}, timeout=TIMEOUT, **kwargs)
    except httpx.HTTPError as exc:
        raise UsdaUnavailable("Couldn't reach USDA FoodData Central. Try again in a moment.") from exc
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise UsdaUnavailable(f"USDA FoodData Central answered {resp.status_code}. Try again in a moment.")
    return resp.json()


def _cached(key, fetch):
    from core.models import ApiCache

    now = timezone.now()
    hit = ApiCache.objects.filter(cache_key=key, expires_at__gt=now).first()
    if hit:
        return hit.response_body
    body = fetch()
    if body is not None:
        ApiCache.objects.update_or_create(cache_key=key, defaults={"response_body": body, "expires_at": now + timedelta(days=CACHE_DAYS)})
    return body


def _per_100g(food_nutrients):
    """Search results use nutrientNumber/value, food details number/amount."""
    raw = {}
    for n in food_nutrients or []:
        num = str(n.get("nutrientNumber") or n.get("number") or (n.get("nutrient") or {}).get("number") or "")
        val = n.get("value", n.get("amount"))
        if num and val is not None and (n.get("unitName") or "").upper() != "KJ":
            raw[num] = val
    out = {key: round(float(raw[num]), 2) if num in raw else None for num, key in NUTRIENTS.items()}
    if out["kcal"] is None:
        out["kcal"] = next((round(float(raw[n]), 2) for n in ENERGY_FALLBACKS if n in raw), None)
    return out


def _food(f):
    return {
        "fdc_id": f.get("fdcId"),
        "name": (f.get("description") or "").strip(),
        "data_type": f.get("dataType"),
        "per_100g": _per_100g(f.get("foodNutrients")),
    }


def search(query, page_size=20):
    q = " ".join(str(query or "").split())[:100]
    if len(q) < 2:
        return []
    key = f"usda:search:{q.lower()}:{page_size}"
    body = _cached(key, lambda: _request("POST", "/foods/search", json={"query": q, "pageSize": page_size, "dataType": DATA_TYPES}))
    return [_food(f) for f in (body or {}).get("foods", [])]


def food(fdc_id):
    """One food with its per-100 g values, or None if USDA doesn't have it."""
    fdc_id = int(fdc_id)
    body = _cached(f"usda:food:{fdc_id}", lambda: _request("GET", f"/food/{fdc_id}", params={"format": "abridged"}))
    return _food(body) if body else None


def portion(per_100g, grams):
    """kcal/macros for `grams` of a food, from its per-100 g values."""
    if not per_100g or grams in (None, ""):
        return {"kcal": None, "carbs_g": None, "protein_g": None, "fat_g": None}
    g = Decimal(str(grams))
    scale = lambda v: None if v is None else round(float(Decimal(str(v)) * g / 100), 1)  # noqa: E731
    return {k: scale(per_100g.get(k)) for k in ("kcal", "carbs_g", "protein_g", "fat_g")}


def item_nutrients(item):
    """Live kcal/macros for a USDA meal-plan food (None values if USDA can't
    be reached) — never stored on the item."""
    try:
        f = food(item.external_food_id) if item.external_food_id else None
    except (UsdaNotConfigured, UsdaUnavailable, ValueError):
        f = None
    return (f or {}).get("per_100g"), portion((f or {}).get("per_100g"), item.grams)


# ---- API views --------------------------------------------------------------

from rest_framework.response import Response  # noqa: E402
from rest_framework.views import APIView  # noqa: E402

from accounts.permissions import IsRnd  # noqa: E402


def _unavailable(exc, status):
    return Response({"detail": str(exc)}, status=status)


class UsdaFoodSearchView(APIView):
    permission_classes = [IsRnd]

    def get(self, request):
        try:
            return Response({"results": search(request.query_params.get("q", ""))})
        except UsdaNotConfigured as exc:
            return _unavailable(exc, 503)
        except UsdaUnavailable as exc:
            return _unavailable(exc, 502)


class UsdaFoodDetailView(APIView):
    permission_classes = [IsRnd]

    def get(self, request, fdc_id):
        try:
            f = food(fdc_id)
        except UsdaNotConfigured as exc:
            return _unavailable(exc, 503)
        except UsdaUnavailable as exc:
            return _unavailable(exc, 502)
        if not f:
            return Response({"detail": "USDA has no food with that id."}, status=404)
        return Response(f)
