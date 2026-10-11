"""Dietary intake tools on the NCP record (proposal: "calorie counts, 24-hour
dietary recalls, food diaries, food frequency questionnaires, and Individual
Dietary Diversity Score assessments").

  - 24-hour recall: what the patient ate yesterday, one row per food —
    {meal, food_name, amount, group, exchanges}. Only the food name and the
    portion are stored; energy and macros are counted live from the FNRI
    exchange values (FoodExchangeCategory), never saved with the row.
  - Food frequency questionnaire: how often each Filipino food group is eaten.
  - IDDS: FAO's 9-group Individual Dietary Diversity Score (FAO 2011,
    *Guidelines for measuring household and individual dietary diversity*),
    one point per group eaten in the last 24 hours.
  - Food diary: the patient's own meal logs (nutrition.MealLog), shown read-only.

Mirrored in frontend utils/ncp.js (RECALL_MEALS, FFQ_GROUPS, FFQ_FREQS,
IDDS_GROUPS, iddsLevel)."""

from decimal import Decimal, InvalidOperation

from rest_framework import serializers

RECALL_MEALS = [
    ("breakfast", "Breakfast"), ("am_snack", "AM snack"), ("lunch", "Lunch"),
    ("pm_snack", "PM snack"), ("dinner", "Dinner"), ("bedtime_snack", "Late-night snack"),
]

FFQ_GROUPS = [
    ("rice_bread", "Rice, bread, noodles, corn"),
    ("root_crops", "Root crops (kamote, gabi, cassava)"),
    ("green_yellow_veg", "Green leafy & yellow vegetables"),
    ("other_veg", "Other vegetables"),
    ("fruits", "Fruits"),
    ("fish", "Fish & seafood"),
    ("meat_poultry", "Meat & poultry"),
    ("processed_meat", "Processed meat (hotdog, longganisa, tocino, canned)"),
    ("eggs", "Eggs"),
    ("legumes", "Legumes & nuts (monggo, peanuts, tokwa)"),
    ("milk", "Milk & dairy"),
    ("sweet_drinks", "Sweetened drinks (soft drinks, juice, 3-in-1 coffee)"),
    ("sweets", "Sweets & desserts (kakanin, cakes, candy)"),
    ("fried", "Fried & fast food"),
    ("salty_snacks", "Instant noodles, chips & salty snacks"),
    ("alcohol", "Alcoholic drinks"),
]
FFQ_FREQS = [
    ("never", "Never"), ("monthly", "1–3× a month"), ("weekly", "1–2× a week"),
    ("often", "3–6× a week"), ("daily", "Once a day"), ("multi", "2+ times a day"),
]

IDDS_GROUPS = [
    ("starchy", "Starchy staples"),
    ("dark_green", "Dark green leafy vegetables"),
    ("vit_a", "Other vitamin A-rich fruits & vegetables"),
    ("other_fv", "Other fruits & vegetables"),
    ("organ", "Organ meat"),
    ("meat_fish", "Meat & fish"),
    ("eggs", "Eggs"),
    ("legumes", "Legumes, nuts & seeds"),
    ("milk", "Milk & milk products"),
]

MAX_RECALL_ROWS = 80
MAX_EXCHANGES = Decimal("20")


def idds_level(score):
    """Commonly used cut-offs for the 9-group score: ≤3 low, 4–5 medium, ≥6 high."""
    if score is None:
        return None
    return "low" if score <= 3 else "medium" if score <= 5 else "high"


def _codes(pairs):
    return {k for k, _ in pairs}


def clean_recall(rows):
    from nutrition.models import FoodExchangeCategory

    if not isinstance(rows, list):
        raise serializers.ValidationError("The 24-hour recall must be a list of foods.")
    groups = set(FoodExchangeCategory.objects.values_list("code", flat=True))
    meals = _codes(RECALL_MEALS)
    out = []
    for n, r in enumerate(rows, start=1):
        if not isinstance(r, dict):
            raise serializers.ValidationError(f"Recall row {n} is not valid.")
        name = str(r.get("food_name") or "").strip()
        amount = str(r.get("amount") or "").strip()
        group = str(r.get("group") or "").strip()
        meal = str(r.get("meal") or "").strip()
        raw = str(r.get("exchanges") if r.get("exchanges") is not None else "").strip()
        if not name:
            if amount or raw:
                raise serializers.ValidationError(f"Recall row {n}: add the food.")
            continue  # an empty row is just dropped
        if len(name) > 120 or len(amount) > 60:
            raise serializers.ValidationError(f"Recall row {n}: the food or amount is too long.")
        if meal not in meals:
            raise serializers.ValidationError(f"Recall row {n}: pick the meal.")
        if group and group not in groups:
            raise serializers.ValidationError(f"Recall row {n}: unknown food group.")
        exchanges = None
        if raw:
            try:
                exchanges = Decimal(raw)
            except InvalidOperation:
                raise serializers.ValidationError(f"Recall row {n}: exchanges must be a number.")
            if not Decimal("0") <= exchanges <= MAX_EXCHANGES:
                raise serializers.ValidationError(f"Recall row {n}: exchanges must be between 0 and 20.")
            exchanges = float(exchanges.quantize(Decimal("0.1")))
        out.append({"meal": meal, "food_name": name, "amount": amount, "group": group, "exchanges": exchanges})
    if len(out) > MAX_RECALL_ROWS:
        raise serializers.ValidationError(f"The recall can have up to {MAX_RECALL_ROWS} foods.")
    return out


def clean_ffq(value):
    if not isinstance(value, dict):
        raise serializers.ValidationError("The food frequency answers are not valid.")
    groups, freqs = _codes(FFQ_GROUPS), _codes(FFQ_FREQS)
    out = {}
    for k, v in value.items():
        if not v:
            continue
        if k not in groups or v not in freqs:
            raise serializers.ValidationError("The food frequency answers are not valid.")
        out[k] = v
    return out


def clean_idds(value):
    if not isinstance(value, list):
        raise serializers.ValidationError("The diversity groups are not valid.")
    groups = _codes(IDDS_GROUPS)
    if any(g not in groups for g in value):
        raise serializers.ValidationError("The diversity groups are not valid.")
    return [k for k, _ in IDDS_GROUPS if k in value]  # canonical order, no repeats


def recall_totals(rows, values=None):
    """Calorie count of a recall from the FNRI exchange values (per exchange of
    each group). Rows without a group or exchanges aren't counted."""
    from nutrition.models import FoodExchangeCategory

    if not rows:
        return None
    if values is None:
        values = {c.code: c for c in FoodExchangeCategory.objects.all()}
    kcal = carbs = protein = fat = Decimal("0")
    counted = 0
    for r in rows:
        cat = values.get(r.get("group") or "")
        if not cat or r.get("exchanges") in (None, ""):
            continue
        x = Decimal(str(r["exchanges"]))
        kcal += x * cat.kcal_per_exchange
        carbs += x * (cat.carbs_g or 0)
        protein += x * (cat.protein_g or 0)
        fat += x * (cat.fat_g or 0)
        counted += 1
    return {
        "kcal": round(float(kcal)), "carbs_g": round(float(carbs)), "protein_g": round(float(protein)),
        "fat_g": round(float(fat)), "foods": len(rows), "counted": counted,
    }


def dietary_summary(record):
    """What summaries/printouts show about a record's dietary intake, or None."""
    totals = recall_totals(record.diet_recall)
    score = len(record.idds_groups) if record.idds_groups else None
    labels = dict(FFQ_GROUPS)
    freq_labels = dict(FFQ_FREQS)
    ffq = [{"group": labels[k], "frequency": freq_labels[v]} for k, v in (record.diet_ffq or {}).items() if k in labels and v in freq_labels]
    if not totals and score is None and not ffq:
        return None
    return {
        "recall": totals,
        "idds_score": score,
        "idds_level": idds_level(score),
        "idds_groups": [dict(IDDS_GROUPS)[g] for g in record.idds_groups or []],
        "ffq": ffq,
    }


def food_diary(client, days=7, now=None):
    """The patient's own meal logs for the last `days` days (newest first) —
    the food diary side of dietary assessment."""
    from datetime import timedelta

    from django.utils import timezone

    from nutrition.models import MealLog
    from scheduling.patient_insights import ph_tz

    now = now or timezone.now()
    today = now.astimezone(ph_tz()).date()
    logs = (MealLog.objects.filter(client=client, log_date__gte=today - timedelta(days=days - 1), log_date__lte=today)
            .select_related("meal_plan_meal").prefetch_related("meal_plan_meal__food_items")
            .order_by("-log_date", "meal_plan_meal__scheduled_time"))
    return [{
        "date": log.log_date,
        "meal": log.meal_plan_meal.get_meal_time_display(),
        "planned": [f.food_name for f in log.meal_plan_meal.food_items.all()],
        "status": log.status,
        "status_label": log.get_status_display(),
        "notes": log.reason_notes or "",
        "has_photo": bool(log.photo_url),
    } for log in logs]
